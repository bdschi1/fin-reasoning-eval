"""Tests for CI mode in runners/run_evaluation.py."""
from __future__ import annotations

import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure repo root is on path
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestCIFlagLimitsProblems(unittest.TestCase):
    """test_ci_flag_limits_scenarios: --ci evaluates at most 10 problems."""

    def test_ci_flag_limits_scenarios(self):
        """CI mode limits evaluation to _CI_LIMIT (5) problems from validation split."""
        from runners.run_evaluation import _CI_LIMIT

        # Build a mock dataset with more than CI_LIMIT examples
        mock_examples = []
        for i in range(20):
            ex = MagicMock()
            ex.id = f"problem_{i}"
            ex.category = "dcf_sanity"
            ex.difficulty = "easy"
            ex.question = f"Question {i}"
            ex.context = None
            ex.options = None
            ex.correct_answer = "A"
            ex.answer_type = "multiple_choice"
            mock_examples.append(ex)

        mock_dataset = MagicMock()
        mock_dataset._examples = mock_examples
        mock_dataset.__iter__ = lambda self: iter(self._examples)
        mock_dataset.__len__ = lambda self: len(self._examples)

        mock_response = MagicMock()
        mock_response.answer = "A"
        mock_response.reasoning = "test"
        mock_response.full_response = "test"
        mock_response.latency_ms = 10
        mock_response.tokens_used = 50
        mock_response.success = True
        mock_response.error = None

        mock_runner = MagicMock()
        mock_runner.model_identifier = "claude-haiku-4-5-20251001"
        mock_runner.config.model_name = "claude-haiku-4-5-20251001"
        mock_runner.format_prompt.return_value = "prompt"
        mock_runner.generate.return_value = mock_response

        mock_metrics_result = MagicMock()
        mock_metrics_result.to_dict.return_value = {"overall_accuracy": 0.80}
        mock_metrics = MagicMock()
        mock_metrics.compute.return_value = mock_metrics_result

        evaluated_ids: list[str] = []

        def track_add_prediction(**kwargs):
            evaluated_ids.append(kwargs["problem_id"])

        mock_metrics.add_prediction.side_effect = track_add_prediction

        args = MagicMock()
        args.data_dir = None
        args.api_key = None

        with (
            patch("runners.run_evaluation.load_benchmark", return_value=mock_dataset),
            patch("runners.run_evaluation.get_runner", return_value=mock_runner),
            patch("runners.run_evaluation.FinancialReasoningMetrics", return_value=mock_metrics),
            patch("sys.exit"),
        ):
            from runners.run_evaluation import _run_ci_mode
            _run_ci_mode(args)

        self.assertLessEqual(len(evaluated_ids), 10)
        self.assertLessEqual(len(mock_dataset._examples), _CI_LIMIT)


class TestCIOutputIsValidJSON(unittest.TestCase):
    """test_ci_output_is_valid_json: stdout must be valid JSON."""

    def test_ci_output_is_valid_json(self):
        """Capture stdout from _run_ci_mode and verify json.loads() succeeds."""
        import io

        mock_examples = []
        for i in range(3):
            ex = MagicMock()
            ex.id = f"p_{i}"
            ex.category = "dcf_sanity"
            ex.difficulty = "easy"
            ex.question = f"Q{i}"
            ex.context = None
            ex.options = None
            ex.correct_answer = "A"
            ex.answer_type = "multiple_choice"
            mock_examples.append(ex)

        mock_dataset = MagicMock()
        mock_dataset._examples = mock_examples
        mock_dataset.__iter__ = lambda self: iter(self._examples)
        mock_dataset.__len__ = lambda self: len(self._examples)

        mock_response = MagicMock()
        mock_response.answer = "A"
        mock_response.reasoning = ""
        mock_response.full_response = ""
        mock_response.latency_ms = 5
        mock_response.tokens_used = 20
        mock_response.success = True
        mock_response.error = None

        mock_runner = MagicMock()
        mock_runner.model_identifier = "claude-haiku-4-5-20251001"
        mock_runner.config.model_name = "claude-haiku-4-5-20251001"
        mock_runner.format_prompt.return_value = "prompt"
        mock_runner.generate.return_value = mock_response

        mock_metrics_result = MagicMock()
        mock_metrics_result.to_dict.return_value = {"overall_accuracy": 0.67}
        mock_metrics = MagicMock()
        mock_metrics.compute.return_value = mock_metrics_result

        args = MagicMock()
        args.data_dir = None
        args.api_key = None

        captured = io.StringIO()

        with (
            patch("runners.run_evaluation.load_benchmark", return_value=mock_dataset),
            patch("runners.run_evaluation.get_runner", return_value=mock_runner),
            patch("runners.run_evaluation.FinancialReasoningMetrics", return_value=mock_metrics),
            patch("sys.exit"),
            patch("sys.stdout", captured),
        ):
            from runners.run_evaluation import _run_ci_mode
            _run_ci_mode(args)

        output_text = captured.getvalue().strip()
        self.assertTrue(output_text, "stdout should not be empty")
        parsed = json.loads(output_text)
        self.assertIn("ci_mode", parsed)
        self.assertTrue(parsed["ci_mode"])
        self.assertIn("overall_accuracy", parsed)
        self.assertIn("pass", parsed)
        self.assertIn("summary", parsed)


class TestCIExits1OnThresholdFailure(unittest.TestCase):
    """test_ci_exits_1_on_threshold_failure: sys.exit(1) when accuracy < threshold."""

    def test_ci_exits_1_on_threshold_failure(self):
        """When accuracy is below CI threshold, sys.exit(1) must be called."""
        mock_examples = [MagicMock() for _ in range(2)]
        for i, ex in enumerate(mock_examples):
            ex.id = f"p_{i}"
            ex.category = "earnings"
            ex.difficulty = "medium"
            ex.question = f"Q{i}"
            ex.context = None
            ex.options = None
            ex.correct_answer = "A"
            ex.answer_type = "multiple_choice"

        mock_dataset = MagicMock()
        mock_dataset._examples = mock_examples
        mock_dataset.__iter__ = lambda self: iter(self._examples)
        mock_dataset.__len__ = lambda self: len(self._examples)

        mock_response = MagicMock()
        mock_response.answer = "B"  # wrong answer
        mock_response.reasoning = ""
        mock_response.full_response = ""
        mock_response.latency_ms = 5
        mock_response.tokens_used = 10
        mock_response.success = True
        mock_response.error = None

        mock_runner = MagicMock()
        mock_runner.model_identifier = "claude-haiku-4-5-20251001"
        mock_runner.config.model_name = "claude-haiku-4-5-20251001"
        mock_runner.format_prompt.return_value = "prompt"
        mock_runner.generate.return_value = mock_response

        # Return accuracy BELOW threshold (0.50)
        mock_metrics_result = MagicMock()
        mock_metrics_result.to_dict.return_value = {"overall_accuracy": 0.10}
        mock_metrics = MagicMock()
        mock_metrics.compute.return_value = mock_metrics_result

        args = MagicMock()
        args.data_dir = None
        args.api_key = None

        exit_calls: list[int] = []

        def mock_exit(code=0):
            exit_calls.append(code)

        with (
            patch("runners.run_evaluation.load_benchmark", return_value=mock_dataset),
            patch("runners.run_evaluation.get_runner", return_value=mock_runner),
            patch("runners.run_evaluation.FinancialReasoningMetrics", return_value=mock_metrics),
            patch("sys.exit", side_effect=mock_exit),
        ):
            from runners.run_evaluation import _run_ci_mode
            try:
                _run_ci_mode(args)
            except SystemExit:
                pass

        self.assertTrue(exit_calls, "sys.exit should have been called")
        self.assertEqual(exit_calls[-1], 1, "sys.exit(1) expected for failing threshold")


if __name__ == "__main__":
    unittest.main()
