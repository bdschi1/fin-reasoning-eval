"""Tests for compute_cost_metrics — the score-only cost-aware eval axis."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.metrics import compute_cost_metrics  # noqa: E402


def _pred(is_correct: bool, output_tokens: int, predicted: str = "A", success: bool = True) -> dict:
    return {
        "is_correct": is_correct,
        "output_tokens": output_tokens,
        "predicted": predicted,
        "success": success,
    }


class TestPassRateAtBudget(unittest.TestCase):
    def test_over_budget_correct_answer_counts_as_fail(self):
        preds = [
            _pred(True, 200),   # correct, within all budgets
            _pred(True, 3000),  # correct, but over 256/512/1024/2048
            _pred(False, 100),  # wrong
        ]
        result = compute_cost_metrics(preds)
        rates = result["pass_rate_at_budget"]
        # Rates are rounded to 4 places for clean JSON serialization.
        self.assertAlmostEqual(rates["256"], 1 / 3, places=4)
        self.assertAlmostEqual(rates["1024"], 1 / 3, places=4)
        self.assertAlmostEqual(rates["4096"], 2 / 3, places=4)

    def test_custom_budgets(self):
        preds = [_pred(True, 500)]
        result = compute_cost_metrics(preds, budgets=(400, 600))
        self.assertEqual(result["pass_rate_at_budget"], {"400": 0.0, "600": 1.0})

    def test_denominator_is_all_predictions(self):
        preds = [_pred(True, 100), _pred(False, 100, predicted="", success=False)]
        result = compute_cost_metrics(preds)
        self.assertAlmostEqual(result["pass_rate_at_budget"]["1024"], 0.5)


class TestQualityPerToken(unittest.TestCase):
    def test_quality_per_1m_output_tokens(self):
        preds = [_pred(True, 400), _pred(False, 600)]
        result = compute_cost_metrics(preds)
        # 1 correct / 1000 tokens * 1e6 = 1000.0
        self.assertAlmostEqual(result["quality_per_1m_output_tokens"], 1000.0)

    def test_none_when_no_tokens_recorded(self):
        preds = [_pred(True, 0)]
        result = compute_cost_metrics(preds)
        self.assertIsNone(result["quality_per_1m_output_tokens"])


class TestTokensToCorrectAnswer(unittest.TestCase):
    def test_charges_wasted_tokens_on_wrong_answers(self):
        preds = [_pred(True, 400), _pred(False, 600)]
        result = compute_cost_metrics(preds)
        # All 1000 output tokens / 1 correct answer.
        self.assertAlmostEqual(result["tokens_to_correct_answer"], 1000.0)

    def test_none_when_nothing_correct(self):
        preds = [_pred(False, 500)]
        result = compute_cost_metrics(preds)
        self.assertIsNone(result["tokens_to_correct_answer"])


class TestWastedTokenFailures(unittest.TestCase):
    def test_counts_burned_budget_with_no_answer(self):
        preds = [
            _pred(False, 800, predicted=""),            # burned, no answer
            _pred(False, 800, predicted="  "),          # whitespace only
            _pred(False, 500, success=False),           # errored after burning
            _pred(False, 300, predicted="B"),           # wrong but parseable
            _pred(False, 0, predicted="", success=False),  # no tokens burned
        ]
        result = compute_cost_metrics(preds)
        self.assertEqual(result["wasted_token_failures"], 3)


class TestEmptyInput(unittest.TestCase):
    def test_empty_predictions(self):
        result = compute_cost_metrics([])
        self.assertEqual(result["wasted_token_failures"], 0)
        self.assertIsNone(result["quality_per_1m_output_tokens"])
        self.assertIsNone(result["tokens_to_correct_answer"])
        self.assertTrue(all(v == 0.0 for v in result["pass_rate_at_budget"].values()))

    def test_missing_fields_are_tolerated(self):
        # Old prediction records may lack token fields entirely.
        result = compute_cost_metrics([{"is_correct": True}])
        self.assertAlmostEqual(result["pass_rate_at_budget"]["256"], 1.0)
        self.assertIsNone(result["quality_per_1m_output_tokens"])


if __name__ == "__main__":
    unittest.main()
