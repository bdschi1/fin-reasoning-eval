"""Tests for evaluation/rubric_auto_grader.py — RubricAutoGrader.

All AI judge calls are mocked; no network access required.
"""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from evaluation.ai_judge import CriterionJudgment, JudgeResult
from evaluation.rubric_auto_grader import AutoRubricResult, RubricAutoGrader
from evaluation.rubric_scoring import RubricCriterion, RubricGrader, RubricResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_criteria() -> list[RubricCriterion]:
    """Two-criterion set for deterministic testing."""
    return [
        RubricCriterion("NA_001", "Final answer correct within tolerance", 3, "numerical_accuracy"),
        RubricCriterion("RC_001", "Reasoning steps follow logical sequence", 2, "reasoning_chain"),
    ]


def _make_judge_result(
    judgments: list[tuple[str, bool, str]],
    overall_quality: str = "good",
    fallback_used: bool = False,
) -> JudgeResult:
    """Build a JudgeResult from (criterion_id, met, confidence) tuples."""
    cj_list = [
        CriterionJudgment(
            criterion_id=cid,
            met=met,
            confidence=conf,
            reasoning=f"Auto-generated reasoning for {cid}.",
        )
        for cid, met, conf in judgments
    ]
    return JudgeResult(
        criterion_judgments=cj_list,
        overall_quality=overall_quality,
        critical_issues=[],
        fallback_used=fallback_used,
    )


def _make_auto_grader(judge_result: JudgeResult) -> RubricAutoGrader:
    """Return a RubricAutoGrader whose judge is pre-configured to return judge_result."""
    mock_judge = MagicMock()
    mock_judge.grade.return_value = judge_result
    return RubricAutoGrader(judge=mock_judge)


# ---------------------------------------------------------------------------
# Test 1: grade() returns an AutoRubricResult
# ---------------------------------------------------------------------------

class TestAutoGradeReturnsAutoRubricResult(unittest.TestCase):
    """grade() returns an AutoRubricResult when the judge returns valid judgments."""

    def test_auto_grade_returns_auto_rubric_result(self) -> None:
        criteria = _make_criteria()
        judge_result = _make_judge_result(
            [("NA_001", True, "high"), ("RC_001", True, "high")],
            overall_quality="excellent",
        )
        auto_grader = _make_auto_grader(judge_result)

        result = auto_grader.grade(
            question="What is the EBITDA margin?",
            context="EBITDA=$420M, Revenue=$2,100M",
            correct_answer="20.0%",
            model_response="420 / 2100 = 20.0%",
            criteria=criteria,
        )

        self.assertIsInstance(result, AutoRubricResult)
        self.assertIsInstance(result.rubric_result, RubricResult)
        self.assertIsInstance(result.judgments, dict)
        self.assertIsInstance(result.confidences, dict)
        self.assertIsInstance(result.low_confidence_criteria, list)
        self.assertFalse(result.fallback_used)


# ---------------------------------------------------------------------------
# Test 2: judgments dict feeds into RubricGrader.score()
# ---------------------------------------------------------------------------

class TestJudgmentsFeedIntoRubricGrader(unittest.TestCase):
    """Judgments extracted from the judge are forwarded to RubricGrader.score()."""

    def test_judgments_feed_into_rubric_grader(self) -> None:
        criteria = _make_criteria()
        # NA_001 met=True (weight 3), RC_001 met=False (weight 2) → 3/5 = 60%
        judge_result = _make_judge_result(
            [("NA_001", True, "high"), ("RC_001", False, "high")],
        )
        auto_grader = _make_auto_grader(judge_result)

        result = auto_grader.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=criteria,
        )

        # Verify judgments dict reflects what the judge returned
        self.assertTrue(result.judgments["NA_001"])
        self.assertFalse(result.judgments["RC_001"])

        # Verify RubricResult reflects those judgments: 3 earned, 5 possible
        self.assertEqual(result.rubric_result.overall_earned, 3)
        self.assertEqual(result.rubric_result.overall_possible, 5)
        self.assertAlmostEqual(result.rubric_result.overall_pct, 60.0, places=1)


# ---------------------------------------------------------------------------
# Test 3: low-confidence criteria flagged for review
# ---------------------------------------------------------------------------

class TestLowConfidenceFlaggedForReview(unittest.TestCase):
    """Criteria with confidence='low' or 'unclear' appear in low_confidence_criteria
    and set needs_human_review=True."""

    def test_low_confidence_flagged_for_review(self) -> None:
        criteria = _make_criteria()
        judge_result = _make_judge_result(
            [("NA_001", True, "high"), ("RC_001", False, "low")],
        )
        auto_grader = _make_auto_grader(judge_result)

        result = auto_grader.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=criteria,
        )

        self.assertIn("RC_001", result.low_confidence_criteria)
        self.assertNotIn("NA_001", result.low_confidence_criteria)
        self.assertTrue(result.needs_human_review)

    def test_unclear_confidence_flagged_for_review(self) -> None:
        criteria = _make_criteria()
        judge_result = _make_judge_result(
            [("NA_001", True, "unclear"), ("RC_001", True, "medium")],
        )
        auto_grader = _make_auto_grader(judge_result)

        result = auto_grader.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=criteria,
        )

        self.assertIn("NA_001", result.low_confidence_criteria)
        self.assertTrue(result.needs_human_review)


# ---------------------------------------------------------------------------
# Test 4: high confidence → no review flag
# ---------------------------------------------------------------------------

class TestHighConfidenceNoReviewFlag(unittest.TestCase):
    """When all criteria have confidence='high', needs_human_review=False."""

    def test_high_confidence_no_review_flag(self) -> None:
        criteria = _make_criteria()
        judge_result = _make_judge_result(
            [("NA_001", True, "high"), ("RC_001", True, "high")],
            overall_quality="excellent",
        )
        auto_grader = _make_auto_grader(judge_result)

        result = auto_grader.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=criteria,
        )

        self.assertEqual(result.low_confidence_criteria, [])
        self.assertFalse(result.needs_human_review)
        self.assertFalse(result.fallback_used)

    def test_medium_confidence_not_flagged(self) -> None:
        """'medium' confidence is not in LOW_CONFIDENCE_VALUES — should not trigger review."""
        criteria = _make_criteria()
        judge_result = _make_judge_result(
            [("NA_001", True, "medium"), ("RC_001", False, "medium")],
        )
        auto_grader = _make_auto_grader(judge_result)

        result = auto_grader.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=criteria,
        )

        self.assertEqual(result.low_confidence_criteria, [])
        self.assertFalse(result.needs_human_review)


# ---------------------------------------------------------------------------
# Test 5: fallback when judge returns fallback_used=True
# ---------------------------------------------------------------------------

class TestFallbackOnJudgeFailure(unittest.TestCase):
    """When JudgeResult.fallback_used=True, AutoRubricResult.fallback_used=True
    and conservative (all-False) judgments are used."""

    def test_fallback_on_judge_failure(self) -> None:
        criteria = _make_criteria()
        # Simulate judge exhausting all retries: fallback_used=True,
        # all criteria marked not met with low confidence.
        fallback_judgments = [
            ("NA_001", False, "low"),
            ("RC_001", False, "low"),
        ]
        judge_result = _make_judge_result(
            fallback_judgments,
            overall_quality="fail",
            fallback_used=True,
        )
        auto_grader = _make_auto_grader(judge_result)

        result = auto_grader.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=criteria,
        )

        self.assertTrue(result.fallback_used)
        self.assertTrue(result.needs_human_review)

        # All judgments must be False (conservative fallback)
        for cid, met in result.judgments.items():
            self.assertFalse(met, f"Expected fallback judgment False for {cid}, got True")

        # All confidences must be 'unclear' (conservative fallback)
        for cid, conf in result.confidences.items():
            self.assertEqual(
                conf, "unclear",
                f"Expected fallback confidence 'unclear' for {cid}, got '{conf}'"
            )

        # Score should be 0 (no criteria met)
        self.assertEqual(result.rubric_result.overall_earned, 0)
        self.assertEqual(result.rubric_result.overall_possible, 5)

    def test_fallback_low_confidence_criteria_contains_all_ids(self) -> None:
        """All criterion IDs appear in low_confidence_criteria during fallback."""
        criteria = _make_criteria()
        judge_result = _make_judge_result(
            [("NA_001", False, "low"), ("RC_001", False, "low")],
            overall_quality="fail",
            fallback_used=True,
        )
        auto_grader = _make_auto_grader(judge_result)

        result = auto_grader.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=criteria,
        )

        expected_ids = {c.id for c in criteria}
        self.assertEqual(set(result.low_confidence_criteria), expected_ids)


if __name__ == "__main__":
    unittest.main()
