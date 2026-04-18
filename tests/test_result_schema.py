"""Tests for the extended result schema (cost, tokens, wall-time).

Phase 1 deliverable — the leaderboard UI reads these fields.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestModelResponseHasCostFields(unittest.TestCase):
    """ModelResponse exposes input_tokens, output_tokens, wall_time_s, cost_usd."""

    def test_modelresponse_default_fields(self):
        from runners.base import ModelResponse

        resp = ModelResponse(answer="A")
        self.assertEqual(resp.input_tokens, 0)
        self.assertEqual(resp.output_tokens, 0)
        self.assertEqual(resp.wall_time_s, 0.0)
        self.assertIsNone(resp.cost_usd)


class TestPricingTableAndCostEstimator(unittest.TestCase):
    """Per-provider pricing table drives cost estimates."""

    def test_pricing_table_exposes_core_models(self):
        from runners.base import PRICING_PER_1M_USD

        self.assertIn("claude-sonnet-4-20250514", PRICING_PER_1M_USD)
        self.assertIn("gpt-4.1", PRICING_PER_1M_USD)
        self.assertIn("o3", PRICING_PER_1M_USD)
        for entry in PRICING_PER_1M_USD.values():
            self.assertIn("input", entry)
            self.assertIn("output", entry)

    def test_cost_estimator_matches_table(self):
        from runners.base import estimate_cost_usd

        # 1M input tokens at $3/M + 1M output tokens at $15/M = $18.
        cost = estimate_cost_usd(
            "claude-sonnet-4-20250514", 1_000_000, 1_000_000
        )
        self.assertAlmostEqual(cost, 18.0, places=4)

    def test_cost_estimator_zero_on_unknown_model(self):
        from runners.base import estimate_cost_usd

        self.assertIsNone(estimate_cost_usd("unknown-model-xyz", 100, 100))


class TestResultOutputContainsCostFields(unittest.TestCase):
    """run_benchmark serializes cost_usd / tokens / wall_time at both the
    per-prediction and totals level."""

    def test_run_benchmark_emits_extended_schema(self):
        from runners.run_evaluation import run_benchmark

        # Minimal mock example.
        ex = MagicMock()
        ex.id = "prob_001"
        ex.category = "earnings_surprise"
        ex.difficulty = "easy"
        ex.question = "Q1"
        ex.context = "ctx"
        ex.options = None
        ex.correct_answer = "A"
        ex.answer_type = "multiple_choice"

        mock_dataset = MagicMock()
        mock_dataset._examples = [ex]
        mock_dataset.__iter__ = lambda self: iter(self._examples)
        mock_dataset.__len__ = lambda self: 1

        # Response with fully populated accounting.
        from runners.base import ModelResponse

        mock_response = ModelResponse(
            answer="A",
            reasoning="r",
            full_response="Reasoning: r\nAnswer: A",
            model="claude-sonnet-4-20250514",
            latency_ms=1234.5,
            tokens_used=400,
            input_tokens=300,
            output_tokens=100,
            wall_time_s=1.2345,
            cost_usd=0.00345,
            success=True,
        )

        mock_runner = MagicMock()
        mock_runner.model_identifier = "claude-sonnet-4-20250514"
        mock_runner.config.model_name = "claude-sonnet-4-20250514"
        mock_runner.config.temperature = 0.0
        mock_runner.config.max_tokens = 1024
        mock_runner.format_prompt.return_value = "prompt"
        mock_runner.generate.return_value = mock_response

        mock_metrics_result = MagicMock()
        mock_metrics_result.summary.return_value = ""
        mock_metrics_result.to_dict.return_value = {"overall_accuracy": 1.0}
        mock_metrics = MagicMock()
        mock_metrics.compute.return_value = mock_metrics_result

        with tempfile.TemporaryDirectory() as out_dir, patch(
            "runners.run_evaluation.FinancialReasoningMetrics", return_value=mock_metrics
        ):
            output, predictions = run_benchmark(
                runner=mock_runner,
                dataset=mock_dataset,
                output_dir=out_dir,
                save_predictions=False,
                show_progress=False,
            )

        self.assertEqual(len(predictions), 1)
        pred = predictions[0]
        for field in ("input_tokens", "output_tokens", "wall_time_s", "cost_usd"):
            self.assertIn(field, pred, f"prediction missing {field}")

        self.assertIn("judge_model", output)
        self.assertIn("prompt_version", output)
        self.assertIn("totals", output)
        totals = output["totals"]
        self.assertEqual(totals["input_tokens"], 300)
        self.assertEqual(totals["output_tokens"], 100)
        self.assertAlmostEqual(totals["wall_time_s"], 1.23, places=2)
        self.assertAlmostEqual(totals["cost_usd"], 0.00345, places=3)


if __name__ == "__main__":
    unittest.main()
