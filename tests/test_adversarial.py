"""Tests for the Phase-3 adversarial variant skeleton."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.adversarial import (  # noqa: E402
    Variant,
    compute_consistency_score,
    generate_numeric_noise_variant,
    generate_option_reorder_variant,
    generate_ticker_swap_variant,
    generate_unit_swap_variant,
    generate_year_shift_variant,
)


SOURCE_PROBLEM = {
    "id": "prob_123",
    "category": "earnings_surprise",
    "difficulty": "medium",
    "question": (
        "Atlas Resources (ATRE) reported Q3 2024 EPS of $2.35 against "
        "consensus $2.47 — beat or miss?"
    ),
    "context": (
        "Revenue: 1200 in Q3 2024. Consensus was 1230. Prior year 1100."
    ),
    "answer_type": "multiple_choice",
    "correct_answer": "Miss by 4.9%",
    "options": [
        {"id": "A", "text": "Miss by 4.9%"},
        {"id": "B", "text": "Beat by 4.9%"},
    ],
    "explanation": "Actual below consensus.",
    "reasoning_steps": ["step 1"],
    "tags": ["earnings"],
}


class TestNumericNoiseVariant(unittest.TestCase):
    def test_returns_variant_dataclass(self):
        variant = generate_numeric_noise_variant(SOURCE_PROBLEM, seed=1)
        self.assertIsInstance(variant, Variant)
        self.assertEqual(variant.original_id, "prob_123")
        self.assertEqual(variant.variant_type, "numeric_noise")
        self.assertNotEqual(variant.variant_id, variant.original_id)

    def test_correct_answer_and_metadata_preserved(self):
        variant = generate_numeric_noise_variant(SOURCE_PROBLEM, seed=1)
        self.assertEqual(variant.correct_answer, SOURCE_PROBLEM["correct_answer"])
        self.assertEqual(variant.category, SOURCE_PROBLEM["category"])
        self.assertEqual(variant.difficulty, SOURCE_PROBLEM["difficulty"])
        self.assertEqual(variant.options, SOURCE_PROBLEM["options"])

    def test_protected_tokens_not_perturbed(self):
        variant = generate_numeric_noise_variant(SOURCE_PROBLEM, seed=1)
        # "2024" (year), "Q3", "ATRE" (ticker) must survive unchanged.
        self.assertIn("2024", variant.question)
        self.assertIn("Q3", variant.question)
        self.assertIn("ATRE", variant.question)

    def test_noise_applied_to_at_least_one_number(self):
        variant = generate_numeric_noise_variant(
            SOURCE_PROBLEM, seed=1, noise_pct=0.05
        )
        self.assertGreaterEqual(len(variant.perturbations), 1)

    def test_variant_adds_adversarial_tag(self):
        variant = generate_numeric_noise_variant(SOURCE_PROBLEM, seed=1)
        self.assertIn("adversarial", variant.tags)
        self.assertIn("numeric_noise", variant.tags)

    def test_variant_serializes_to_dict(self):
        variant = generate_numeric_noise_variant(SOURCE_PROBLEM, seed=1)
        d = variant.to_dict()
        self.assertEqual(d["original_id"], "prob_123")
        self.assertEqual(d["variant_type"], "numeric_noise")
        self.assertIn("perturbations", d)


class TestPhase3StubsRaise(unittest.TestCase):
    def test_unit_swap_raises(self):
        with self.assertRaises(NotImplementedError):
            generate_unit_swap_variant(SOURCE_PROBLEM)

    def test_year_shift_raises(self):
        with self.assertRaises(NotImplementedError):
            generate_year_shift_variant(SOURCE_PROBLEM)

    def test_ticker_swap_raises(self):
        with self.assertRaises(NotImplementedError):
            generate_ticker_swap_variant(SOURCE_PROBLEM)

    def test_option_reorder_raises(self):
        with self.assertRaises(NotImplementedError):
            generate_option_reorder_variant(SOURCE_PROBLEM)


class TestConsistencyScore(unittest.TestCase):
    def test_matching_answers_score_one(self):
        self.assertEqual(compute_consistency_score("Miss by 4.9%", "Miss by 4.9%"), 1.0)

    def test_different_answers_score_zero(self):
        self.assertEqual(compute_consistency_score("Miss", "Beat"), 0.0)

    def test_empty_answer_scores_zero(self):
        self.assertEqual(compute_consistency_score("", "Miss"), 0.0)


if __name__ == "__main__":
    unittest.main()
