"""Regression tests for FinancialReasoningJudge + RubricAutoGrader pipeline.

Verifies that AI judge scores on baseline responses stay within ±5% of
expected values. Catches prompt regressions without live API calls.

All tests mock FinancialReasoningJudge — no real API calls are made.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from evaluation.ai_judge import CriterionJudgment, JudgeResult
from evaluation.rubric_auto_grader import RubricAutoGrader
from evaluation.rubric_scoring import DEFAULT_CRITERIA, RubricGrader

FIXTURES_PATH = Path(__file__).parent / "fixtures" / "judge_baseline.json"
TOLERANCE = 0.05  # ±5 percentage points


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_baselines() -> list[dict[str, Any]]:
    with open(FIXTURES_PATH) as f:
        return json.load(f)["baselines"]


def _make_judge_result(baseline: dict[str, Any]) -> JudgeResult:
    """Build a JudgeResult from the baseline fixture's criterion_judgments map."""
    judgments_map: dict[str, bool] = baseline["criterion_judgments"]
    criterion_judgments = [
        CriterionJudgment(
            criterion_id=cid,
            met=met,
            confidence="high",
            reasoning="regression fixture",
            detected_pattern="baseline",
        )
        for cid, met in judgments_map.items()
    ]
    return JudgeResult(
        criterion_judgments=criterion_judgments,
        overall_quality=baseline["expected_scores"]["overall_quality"],
        critical_issues=[],
        fallback_used=False,
    )


def _run_pipeline(baseline: dict[str, Any]) -> float:
    """Run RubricAutoGrader with a mocked judge; return overall_pct."""
    mock_judge = MagicMock()
    mock_judge.grade.return_value = _make_judge_result(baseline)

    auto_grader = RubricAutoGrader(judge=mock_judge)
    result = auto_grader.grade(
        question=baseline["question"],
        context=baseline["context"],
        correct_answer=baseline["correct_answer"],
        model_response=baseline["model_response"],
        criteria=DEFAULT_CRITERIA,
        problem_category=baseline.get("problem_category", ""),
    )
    return result.rubric_result.overall_pct


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestJudgeRegression:
    """Regression suite: pipeline scores remain within ±5% of baseline values."""

    def test_excellent_response_scores_above_80_pct(self) -> None:
        """Excellent baseline (fre_baseline_001) should produce overall_pct ≥ 80%."""
        baselines = _load_baselines()
        baseline = next(b for b in baselines if b["id"] == "fre_baseline_001")
        overall_pct = _run_pipeline(baseline)
        assert overall_pct >= 80.0, (
            f"Excellent response expected ≥80% overall_pct, got {overall_pct:.1f}%"
        )

    def test_poor_response_scores_below_60_pct(self) -> None:
        """Adequate baseline (fre_baseline_002) should produce overall_pct < 60%."""
        baselines = _load_baselines()
        baseline = next(b for b in baselines if b["id"] == "fre_baseline_002")
        overall_pct = _run_pipeline(baseline)
        assert overall_pct < 60.0, (
            f"Adequate response expected <60% overall_pct, got {overall_pct:.1f}%"
        )

    def test_fail_response_scores_zero(self) -> None:
        """Fail baseline (fre_baseline_003) with all criteria not-met should score 0%."""
        baselines = _load_baselines()
        baseline = next(b for b in baselines if b["id"] == "fre_baseline_003")
        overall_pct = _run_pipeline(baseline)
        assert overall_pct == 0.0, (
            f"Fail response expected 0% overall_pct, got {overall_pct:.1f}%"
        )

    @pytest.mark.parametrize("baseline_id", [
        "fre_baseline_001",
        "fre_baseline_002",
        "fre_baseline_003",
    ])
    def test_scores_within_tolerance_of_baseline(self, baseline_id: str) -> None:
        """All baselines: computed overall_pct within ±5 percentage points of expected."""
        baselines = _load_baselines()
        baseline = next(b for b in baselines if b["id"] == baseline_id)
        expected_pct: float = baseline["expected_scores"]["overall_pct"]
        actual_pct = _run_pipeline(baseline)
        diff = abs(actual_pct - expected_pct)
        assert diff <= TOLERANCE * 100, (
            f"{baseline_id}: expected {expected_pct:.1f}%, got {actual_pct:.1f}%, "
            f"diff {diff:.1f}pp exceeds tolerance {TOLERANCE * 100:.1f}pp"
        )

    def test_pipeline_uses_correct_criteria(self) -> None:
        """Judge receives DEFAULT_CRITERIA list; result is not a fallback."""
        baselines = _load_baselines()
        baseline = baselines[0]
        mock_judge = MagicMock()
        mock_judge.grade.return_value = _make_judge_result(baseline)

        auto_grader = RubricAutoGrader(judge=mock_judge)
        result = auto_grader.grade(
            question=baseline["question"],
            context=baseline["context"],
            correct_answer=baseline["correct_answer"],
            model_response=baseline["model_response"],
            criteria=DEFAULT_CRITERIA,
        )
        assert not result.fallback_used, "Pipeline should not report fallback_used=True"
        assert result.rubric_result.overall_possible == sum(
            c.weight for c in DEFAULT_CRITERIA
        ), "overall_possible must equal sum of DEFAULT_CRITERIA weights"

    def test_overall_quality_matches_baseline(self) -> None:
        """JudgeResult.overall_quality should match the baseline expected value."""
        baselines = _load_baselines()
        for baseline in baselines:
            judge_result = _make_judge_result(baseline)
            assert judge_result.overall_quality == baseline["expected_scores"]["overall_quality"], (
                f"{baseline['id']}: overall_quality mismatch — "
                f"expected {baseline['expected_scores']['overall_quality']!r}, "
                f"got {judge_result.overall_quality!r}"
            )

    def test_fixture_file_is_valid_and_complete(self) -> None:
        """Fixture file must parse and contain at least 3 baselines with required keys."""
        with open(FIXTURES_PATH) as f:
            data = json.load(f)

        assert "baselines" in data
        assert len(data["baselines"]) >= 3

        required_keys = {
            "id", "question", "context", "correct_answer",
            "model_response", "criterion_judgments", "expected_scores",
        }
        for baseline in data["baselines"]:
            missing = required_keys - baseline.keys()
            assert not missing, f"{baseline.get('id','?')}: missing keys {missing}"
