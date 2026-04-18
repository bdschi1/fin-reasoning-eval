"""Tests for evaluation/contamination.py — benchmark contamination defense."""

from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

# Ensure repo root is importable regardless of working directory.
sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.contamination import (
    VERBATIM_THRESHOLD_CHARS,
    ContaminationChecker,
    ContaminationResult,
    _extract_problem_text,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@dataclass
class _FakeProblem:
    """Minimal stand-in for FinancialReasoningExample."""

    id: str
    question: str
    context: str


def _make_problems(n: int = 5) -> list[_FakeProblem]:
    return [
        _FakeProblem(
            id=f"prob_{i:03d}",
            question=f"What is the DCF value if WACC is {10 + i}% and FCF is ${100 * i}M?",
            context=f"Company: Acme Corp {i}. Sector: Technology. Revenue: ${500 * i}M.",
        )
        for i in range(1, n + 1)
    ]


# ---------------------------------------------------------------------------
# Test 1: Hash index built from problems
# ---------------------------------------------------------------------------


def test_hash_index_built_from_problems():
    """build_hash_index returns correct SHA-256 for each problem."""
    problems = _make_problems(5)
    checker = ContaminationChecker()
    index = checker.build_hash_index(problems)

    assert len(index) == 5, "Index should contain one entry per problem."

    for p in problems:
        assert p.id in index, f"Problem {p.id} missing from index."
        expected_text = _extract_problem_text(p.question, p.context)
        expected_hash = hashlib.sha256(expected_text.encode("utf-8")).hexdigest()
        assert index[p.id] == expected_hash, (
            f"Hash mismatch for {p.id}: got {index[p.id]}, expected {expected_hash}"
        )


# ---------------------------------------------------------------------------
# Test 2: Verbatim detection flags copied text
# ---------------------------------------------------------------------------


def test_verbatim_detection_flags_copied_text():
    """Response containing a 60-char verbatim fragment from problem text is flagged."""
    problem_text = (
        "What is the DCF value if WACC is 12% and FCF is $200M for Acme Corp? "
        "Context: Revenue $1B, EBITDA margin 25%, terminal growth 2.5%."
    )
    # Take a 60-char slice from the middle of the problem text.
    fragment = problem_text[10:70]
    assert len(fragment) == 60

    response = (
        f"My analysis shows the fair value is approximately $45 per share. "
        f"Reproducing for clarity: {fragment} — end of excerpt."
    )

    checker = ContaminationChecker()
    result = checker.check_response(
        problem_id="test_verbatim_001",
        problem_text=problem_text,
        model_response=response,
    )

    assert result.is_flagged, "Should be flagged for verbatim copy."
    assert result.detection_method == "verbatim"
    assert result.matched_fragment != ""
    assert len(result.matched_fragment) >= VERBATIM_THRESHOLD_CHARS


# ---------------------------------------------------------------------------
# Test 3: Short overlap does NOT trigger a flag
# ---------------------------------------------------------------------------


def test_verbatim_detection_no_flag_on_short_match():
    """A 20-char overlap (below threshold) should NOT be flagged."""
    problem_text = (
        "DCF valuation: WACC 10%, FCF $150M, terminal growth 3%. "
        "Estimate intrinsic value per share."
    )
    # 20 chars from the start — well below VERBATIM_THRESHOLD_CHARS (50).
    short_fragment = problem_text[:20]
    assert len(short_fragment) == 20

    response = (
        f"Based on the provided inputs — {short_fragment} — "
        "the implied value is roughly $38 per share using a standard two-stage DCF."
    )

    checker = ContaminationChecker()
    result = checker.check_response(
        problem_id="test_short_match_002",
        problem_text=problem_text,
        model_response=response,
    )

    assert not result.is_flagged, (
        "Short overlap below threshold should not be flagged."
    )
    assert result.detection_method == "none"


# ---------------------------------------------------------------------------
# Test 4: No false positives on a clean correct answer
# ---------------------------------------------------------------------------


def test_no_false_positives_on_correct_answer():
    """Response containing only the correct answer (no problem text) is clean."""
    problem_text = (
        "Quantum Solutions reported net income of $259.0M and cash from "
        "operations of $181.0M. The accrual ratio (NI - CFO)/NI is 30.1%. "
        "What does this indicate about earnings quality? "
        "Options: A) Valid B) Warning - 30% accrual ratio warrants working "
        "capital review C) No concern D) Normal"
    )
    # Correct answer phrasing — no verbatim copy of the question.
    response = (
        "B\n\nThe answer is B. A 30% accrual ratio indicates potential earnings "
        "quality concerns. CFO/NI of 0.70x signals weak cash conversion. High "
        "accrual ratios (>25-30%) have historically preceded earnings "
        "disappointments and warrant a working capital review."
    )

    checker = ContaminationChecker()
    result = checker.check_response(
        problem_id="test_clean_answer_003",
        problem_text=problem_text,
        model_response=response,
    )

    assert not result.is_flagged, "Clean correct answer should not be flagged."
    assert result.detection_method == "none"


# ---------------------------------------------------------------------------
# Test 5: Batch report summary with known flagged count
# ---------------------------------------------------------------------------


def test_batch_report_summary():
    """Batch of 10 responses with 3 verbatim contaminations produces correct report."""
    checker = ContaminationChecker()

    base_question = (
        "Analyze the balance sheet: total assets $500M, total liabilities $300M, "
        "equity $200M. Debt-to-equity ratio is 1.5x. What is the leverage risk? "
        "Options: A) Low B) Moderate C) High D) Extreme leverage risk detected."
    )

    clean_response = (
        "The answer is B. A D/E of 1.5x is moderate. Sector context matters; "
        "for industrials this is within acceptable range."
    )

    # Build 10 (problem_id, problem_text, response) tuples.
    # Problems 0, 3, 7 are contaminated (verbatim copy of 60+ chars).
    contaminated_indices = {0, 3, 7}
    batch = []
    for i in range(10):
        pid = f"batch_prob_{i:02d}"
        # Each problem has a unique-enough question.
        q = f"[Problem {i}] {base_question}"
        if i in contaminated_indices:
            # Plant a 60-char verbatim fragment in the response.
            fragment = q[5:65]
            assert len(fragment) == 60
            resp = f"The answer is C. Note: {fragment} — end verbatim."
        else:
            resp = clean_response
        batch.append((pid, q, resp))

    results = checker.check_batch(batch)
    report = checker.generate_report(results)

    assert report["total_checked"] == 10
    assert report["flagged_count"] == 3
    assert abs(report["flagged_rate"] - 0.3) < 1e-9
    flagged_ids = set(report["flagged_problem_ids"])
    assert flagged_ids == {"batch_prob_00", "batch_prob_03", "batch_prob_07"}
    assert report["detection_methods"]["verbatim"] == 3
    assert report["detection_methods"]["semantic"] == 0
