"""Tests for evaluation/judge_agreement.py — RubricJudgeAgreement.

No network access required; all computations are pure Python.
"""

from __future__ import annotations

import unittest

from evaluation.judge_agreement import AgreementResult, RubricJudgeAgreement
from evaluation.rubric_scoring import RubricCriterion


def _make_criteria() -> list[RubricCriterion]:
    return [
        RubricCriterion("NA_001", "Final numerical answer correct", 3, "numerical_accuracy"),
        RubricCriterion("NA_002", "Intermediate calcs shown", 2, "numerical_accuracy"),
        RubricCriterion("RC_001", "Reasoning steps logical", 3, "reasoning_chain"),
        RubricCriterion("RC_002", "Each step justified", 2, "reasoning_chain"),
        RubricCriterion("CU_001", "Identifies core concept", 3, "conceptual_understanding"),
    ]


class TestAgreementResultFields(unittest.TestCase):
    """Test 1: AgreementResult has all required fields."""

    def test_agreement_result_has_required_fields(self) -> None:
        result = AgreementResult(
            overall_kappa=0.75,
            category_kappa={"numerical_accuracy": 0.8},
            n_compared=10,
            low_agreement_categories=[],
            warning="",
        )
        self.assertIsInstance(result.overall_kappa, float)
        self.assertIsInstance(result.category_kappa, dict)
        self.assertIsInstance(result.n_compared, int)
        self.assertIsInstance(result.low_agreement_categories, list)
        self.assertIsInstance(result.warning, str)
        self.assertEqual(result.overall_kappa, 0.75)
        self.assertEqual(result.n_compared, 10)


class TestKappaComputation(unittest.TestCase):
    """Test 2: cohens_kappa produces correct value for known inputs."""

    def test_kappa_perfect_agreement(self) -> None:
        """Perfect agreement => kappa = 1.0."""
        kappa = RubricJudgeAgreement.cohens_kappa(
            [True, False, True, True, False],
            [True, False, True, True, False],
        )
        self.assertAlmostEqual(kappa, 1.0, places=6)

    def test_kappa_chance_level_agreement(self) -> None:
        """50/50 split, agreement equal to chance => kappa ~ 0."""
        # Both raters always say True => p_e = 1.0 => kappa degenerates.
        kappa = RubricJudgeAgreement.cohens_kappa(
            [True, True, True],
            [True, True, True],
        )
        # All positive — p_o=1.0, p_e=1.0 => defined as 1.0 (perfect agreement).
        self.assertAlmostEqual(kappa, 1.0, places=6)

    def test_kappa_known_value(self) -> None:
        """Compute kappa for a known configuration and verify formula."""
        # a = [T, T, F, F, T], b = [T, F, F, T, T]
        # Agreements at positions 0,2,4 => p_o = 3/5 = 0.6
        # p_a_pos = 3/5, p_b_pos = 3/5
        # p_e = (3/5)(3/5) + (2/5)(2/5) = 9/25 + 4/25 = 13/25 = 0.52
        # kappa = (0.6 - 0.52) / (1 - 0.52) = 0.08/0.48 ≈ 0.1667
        a = [True, True, False, False, True]
        b = [True, False, False, True, True]
        kappa = RubricJudgeAgreement.cohens_kappa(a, b)
        self.assertAlmostEqual(kappa, 0.08 / 0.48, places=4)

    def test_kappa_raises_on_length_mismatch(self) -> None:
        with self.assertRaises(ValueError):
            RubricJudgeAgreement.cohens_kappa([True, False], [True])


class TestWarningTriggered(unittest.TestCase):
    """Test 3: warning is populated when overall kappa < 0.6."""

    def test_warning_triggered_below_threshold(self) -> None:
        criteria = _make_criteria()
        agreement = RubricJudgeAgreement()

        # Craft ratings that produce kappa ≈ 0.4 (below threshold).
        # Rater A: all True; Rater B: alternating True/False
        # With 5 criteria: A=[T,T,T,T,T], B=[T,F,T,F,T]
        # Agreements: 0,2,4 => p_o=3/5=0.6
        # p_a_pos=1.0, p_b_pos=3/5
        # p_e = 1.0*0.6 + 0.0*0.4 = 0.6
        # kappa = (0.6 - 0.6) / (1 - 0.6) = 0.0
        ai_j = {c.id: True for c in criteria}
        heur_j = {
            criteria[0].id: True,
            criteria[1].id: False,
            criteria[2].id: True,
            criteria[3].id: False,
            criteria[4].id: True,
        }

        result = agreement.compare(
            question="q", context="c", correct_answer="a", model_response="r",
            criteria=criteria,
            ai_judgments=ai_j,
            heuristic_judgments=heur_j,
        )
        # kappa should be 0.0 which is below 0.6 threshold
        self.assertLess(result.overall_kappa, 0.6)
        self.assertNotEqual(result.warning, "")
        self.assertIn("threshold", result.warning.lower())

    def test_no_warning_above_threshold(self) -> None:
        criteria = _make_criteria()
        agreement = RubricJudgeAgreement()

        # Perfect agreement => kappa = 1.0 => no warning
        j = {c.id: True for c in criteria}
        result = agreement.compare(
            question="q", context="c", correct_answer="a", model_response="r",
            criteria=criteria,
            ai_judgments=j,
            heuristic_judgments=j,
        )
        self.assertGreaterEqual(result.overall_kappa, 0.6)
        self.assertEqual(result.warning, "")

    def test_insufficient_data_warning(self) -> None:
        agreement = RubricJudgeAgreement()
        result = agreement.compare(
            question="q", context="c", correct_answer="a", model_response="r",
            criteria=[],
            ai_judgments={},
            heuristic_judgments={},
        )
        self.assertEqual(result.overall_kappa, 0.0)
        self.assertNotEqual(result.warning, "")


if __name__ == "__main__":
    unittest.main()
