"""Tests for evaluation/ai_judge.py — FinancialReasoningJudge.

All Anthropic API calls are mocked; no network access required.
"""

from __future__ import annotations

import json
import unittest
from unittest.mock import MagicMock, patch

from evaluation.ai_judge import (
    CriterionJudgment,
    FinancialReasoningJudge,
    JudgeResult,
)
from evaluation.rubric_scoring import RubricCriterion

# The bd_anthropic wrapper replaces client.messages.create with a plain
# function, which breaks MagicMock call introspection. Force the raw-client
# fallback path for the whole module so mocks are observed directly.
_BD_PATCH = patch("evaluation.ai_judge._bd_make_client", None)


def setUpModule() -> None:
    _BD_PATCH.start()


def tearDownModule() -> None:
    _BD_PATCH.stop()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_criteria() -> list[RubricCriterion]:
    return [
        RubricCriterion("NA_001", "Final numerical answer is correct within tolerance", 3, "numerical_accuracy"),
        RubricCriterion("RC_001", "Reasoning steps follow logical sequence", 2, "reasoning_chain"),
    ]


def make_mock_tool_response(
    criterion_judgments: list[dict],
    overall_quality: str = "good",
) -> MagicMock:
    """Build a mock Anthropic response with tool_use content."""
    tool_input = {
        "criterion_judgments": criterion_judgments,
        "overall_quality": overall_quality,
        "critical_issues": [],
    }
    mock_response = MagicMock()
    mock_response.stop_reason = "tool_use"
    mock_content = MagicMock()
    mock_content.type = "tool_use"
    mock_content.input = tool_input
    mock_response.content = [mock_content]
    return mock_response


def _valid_judgments() -> list[dict]:
    return [
        {
            "criterion_id": "NA_001",
            "met": True,
            "confidence": "high",
            "reasoning": "The model computed 20.0% correctly.",
            "detected_pattern": "direct_calculation",
        },
        {
            "criterion_id": "RC_001",
            "met": False,
            "confidence": "medium",
            "reasoning": "No explicit reasoning steps were shown.",
            "detected_pattern": "missing_steps",
        },
    ]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGradeReturnsJudgmentList(unittest.TestCase):
    """Judge returns a properly populated CriterionJudgment list."""

    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_grade_returns_judgment_list(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = make_mock_tool_response(
            _valid_judgments(), overall_quality="good"
        )

        judge = FinancialReasoningJudge(api_key="test-key")
        result = judge.grade(
            question="What is the EBITDA margin?",
            context="EBITDA=$420M, Revenue=$2,100M",
            correct_answer="20.0%",
            model_response="420/2100 = 20.0%",
            criteria=_make_criteria(),
        )

        self.assertIsInstance(result, JudgeResult)
        self.assertEqual(len(result.criterion_judgments), 2)
        self.assertIsInstance(result.criterion_judgments[0], CriterionJudgment)
        self.assertFalse(result.fallback_used)


class TestGradeValidToolUseStructure(unittest.TestCase):
    """Tool use response is correctly parsed into JudgeResult fields."""

    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_grade_valid_tool_use_structure(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = make_mock_tool_response(
            _valid_judgments(), overall_quality="excellent"
        )

        judge = FinancialReasoningJudge(api_key="test-key")
        result = judge.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=_make_criteria(),
        )

        self.assertEqual(result.overall_quality, "excellent")
        self.assertIsInstance(result.critical_issues, list)

        na001 = next(j for j in result.criterion_judgments if j.criterion_id == "NA_001")
        self.assertTrue(na001.met)
        self.assertEqual(na001.confidence, "high")
        self.assertIn("20.0%", na001.reasoning)

        rc001 = next(j for j in result.criterion_judgments if j.criterion_id == "RC_001")
        self.assertFalse(rc001.met)
        self.assertEqual(rc001.confidence, "medium")


class TestRetryOnValidationFailure(unittest.TestCase):
    """Judge retries when first response fails validation, succeeds on second."""

    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_retry_on_validation_failure(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # First call: bad criterion_id triggers validation failure
        bad_response = make_mock_tool_response(
            [
                {
                    "criterion_id": "UNKNOWN_999",
                    "met": True,
                    "confidence": "high",
                    "reasoning": "bad id",
                }
            ],
            overall_quality="good",
        )
        # Second call: valid response
        good_response = make_mock_tool_response(
            _valid_judgments(), overall_quality="good"
        )

        mock_client.messages.create.side_effect = [bad_response, good_response]

        judge = FinancialReasoningJudge(api_key="test-key")
        result = judge.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=_make_criteria(),
        )

        # Should have retried — create called twice
        self.assertEqual(mock_client.messages.create.call_count, 2)
        self.assertFalse(result.fallback_used)
        self.assertEqual(len(result.criterion_judgments), 2)


class TestFallbackOnAllRetriesExhausted(unittest.TestCase):
    """When every attempt fails validation, fallback_used=True is returned."""

    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_fallback_on_all_retries_exhausted(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        # Always return an invalid criterion_id so every attempt fails validation
        bad_response = make_mock_tool_response(
            [
                {
                    "criterion_id": "INVALID",
                    "met": False,
                    "confidence": "low",
                    "reasoning": "always bad",
                }
            ],
            overall_quality="poor",
        )
        # 3 calls = initial attempt + 2 retries
        mock_client.messages.create.return_value = bad_response

        judge = FinancialReasoningJudge(api_key="test-key")
        result = judge.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=_make_criteria(),
        )

        self.assertTrue(result.fallback_used)
        # All criteria in fallback should be marked not met with low confidence
        for j in result.criterion_judgments:
            self.assertFalse(j.met)
            self.assertEqual(j.confidence, "low")
            self.assertEqual(j.detected_pattern, "judge_validation_failure")
        # critical_issues must reference the failure
        self.assertTrue(
            any("judge_validation_failure" in issue for issue in result.critical_issues)
        )


class TestMetTrueHighConfidence(unittest.TestCase):
    """met=True with high confidence is faithfully round-tripped."""

    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_met_true_high_confidence(self, mock_anthropic_cls: MagicMock) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        mock_client.messages.create.return_value = make_mock_tool_response(
            [
                {
                    "criterion_id": "NA_001",
                    "met": True,
                    "confidence": "high",
                    "reasoning": "Answer exactly matches 20.0%.",
                    "detected_pattern": "exact_match",
                },
                {
                    "criterion_id": "RC_001",
                    "met": True,
                    "confidence": "high",
                    "reasoning": "Response shows step-by-step logic.",
                    "detected_pattern": "explicit_steps",
                },
            ],
            overall_quality="excellent",
        )

        judge = FinancialReasoningJudge(api_key="test-key")
        result = judge.grade(
            question="What is the EBITDA margin?",
            context="EBITDA=$420M, Revenue=$2,100M",
            correct_answer="20.0%",
            model_response="Step 1: 420/2100 = 0.20. Step 2: 0.20 * 100 = 20.0%",
            criteria=_make_criteria(),
        )

        self.assertFalse(result.fallback_used)
        for j in result.criterion_judgments:
            self.assertTrue(j.met)
            self.assertEqual(j.confidence, "high")

        self.assertEqual(result.overall_quality, "excellent")
        na001 = next(j for j in result.criterion_judgments if j.criterion_id == "NA_001")
        self.assertEqual(na001.detected_pattern, "exact_match")


class TestPromptPrefixCaching(unittest.TestCase):
    """Prompt layout supports prefix caching: rubric in system, stable retries."""

    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_rubric_lives_in_system_not_user_message(
        self, mock_anthropic_cls: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = make_mock_tool_response(
            _valid_judgments()
        )

        judge = FinancialReasoningJudge(api_key="test-key")
        judge.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=_make_criteria(),
            skill_conventions="Use the standard output schema.",
        )

        kwargs = mock_client.messages.create.call_args.kwargs
        system = kwargs["system"]
        self.assertIsInstance(system, list)
        self.assertEqual(len(system), 2)
        rubric_block = system[1]["text"]
        self.assertIn("## Rubric Criteria", rubric_block)
        self.assertIn("NA_001", rubric_block)
        self.assertIn("RC_001", rubric_block)
        self.assertIn("## Skill Conventions", rubric_block)

        user_content = kwargs["messages"][0]["content"]
        self.assertNotIn("## Rubric Criteria", user_content)
        self.assertNotIn("NA_001", user_content)

    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_retry_appends_turns_and_preserves_prefix(
        self, mock_anthropic_cls: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client

        bad_response = make_mock_tool_response(
            [
                {
                    "criterion_id": "UNKNOWN_999",
                    "met": True,
                    "confidence": "high",
                    "reasoning": "bad id",
                }
            ]
        )
        good_response = make_mock_tool_response(_valid_judgments())
        mock_client.messages.create.side_effect = [bad_response, good_response]

        judge = FinancialReasoningJudge(api_key="test-key")
        judge.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=_make_criteria(),
        )

        calls = mock_client.messages.create.call_args_list
        self.assertEqual(len(calls), 2)
        first_msgs = calls[0].kwargs["messages"]
        second_msgs = calls[1].kwargs["messages"]

        # Retry appends assistant + user turns; the original user message is
        # byte-identical so the cached prefix survives the retry. Compare
        # against freshly built content — the recorded messages share dict
        # references across calls, so first==second alone would not catch
        # in-place mutation.
        expected_first = judge._build_messages(
            question="Q", context="ctx", correct_answer="A", model_response="R"
        )[0]
        self.assertEqual(len(first_msgs), 1)
        self.assertEqual(len(second_msgs), 3)
        self.assertEqual(first_msgs[0], expected_first)
        self.assertEqual(second_msgs[0], expected_first)
        self.assertEqual(second_msgs[1]["role"], "assistant")
        self.assertEqual(second_msgs[2]["role"], "user")
        self.assertIn("Validation Error", second_msgs[2]["content"])

        # System blocks are identical across attempts.
        self.assertEqual(calls[0].kwargs["system"], calls[1].kwargs["system"])


class TestCacheInjectionSuppression(unittest.TestCase):
    """bd_cache=False when the stable prefix can't clear the model's cache
    minimum (the wrapper's only effective breakpoint would be a per-call
    cache write on the trailing user message that is never read back)."""

    def _grade_call_kwargs(self, model: str) -> dict:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = make_mock_tool_response(
            _valid_judgments()
        )
        # Deterministic fakes so the test doesn't depend on bd_anthropic
        # being installed: prefix estimates to 1400 tokens.
        with patch(
            "evaluation.ai_judge._bd_make_client", lambda **kw: mock_client
        ), patch(
            "evaluation.ai_judge._bd_min_cache_tokens",
            lambda m: 4096 if "haiku" in m else 512,
        ), patch(
            "evaluation.ai_judge._bd_estimate_tokens", lambda payload: 700
        ):
            judge = FinancialReasoningJudge(model=model, api_key="test-key")
            judge.grade(
                question="Q",
                context="ctx",
                correct_answer="A",
                model_response="R",
                criteria=_make_criteria(),
            )
        return mock_client.messages.create.call_args.kwargs

    def test_bd_cache_disabled_below_threshold(self):
        kwargs = self._grade_call_kwargs("claude-haiku-4-5-20251001")
        self.assertIs(kwargs.get("bd_cache"), False)

    def test_bd_cache_left_on_when_prefix_clears_threshold(self):
        kwargs = self._grade_call_kwargs("claude-fable-5")
        self.assertNotIn("bd_cache", kwargs)


class TestApiErrorRetrySemantics(unittest.TestCase):
    """API failures retry with unchanged messages; refusals are terminal."""

    @patch("evaluation.ai_judge.time.sleep")
    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_api_error_retries_with_unchanged_messages(
        self, mock_anthropic_cls: MagicMock, mock_sleep: MagicMock
    ) -> None:
        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = [
            RuntimeError("overloaded_error"),
            make_mock_tool_response(_valid_judgments()),
        ]

        judge = FinancialReasoningJudge(api_key="test-key")
        result = judge.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=_make_criteria(),
        )

        self.assertFalse(result.fallback_used)
        calls = mock_client.messages.create.call_args_list
        self.assertEqual(len(calls), 2)
        # No fabricated validation-error turns for an API failure — the model
        # never saw the first request.
        self.assertEqual(calls[0].kwargs["messages"], calls[1].kwargs["messages"])
        self.assertEqual(len(calls[1].kwargs["messages"]), 1)
        mock_sleep.assert_called_once()

    @patch("evaluation.ai_judge.time.sleep")
    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_refusal_exception_is_terminal(
        self, mock_anthropic_cls: MagicMock, mock_sleep: MagicMock
    ) -> None:
        # bd_anthropic raises RefusalError on stop_reason == "refusal";
        # matched by class name, so mirror that here.
        RefusalError = type("RefusalError", (Exception,), {})

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.side_effect = RefusalError("refused")

        judge = FinancialReasoningJudge(api_key="test-key")
        result = judge.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=_make_criteria(),
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(mock_client.messages.create.call_count, 1)
        mock_sleep.assert_not_called()

    @patch("evaluation.ai_judge.time.sleep")
    @patch("evaluation.ai_judge.anthropic.Anthropic")
    def test_refusal_stop_reason_is_terminal_on_raw_client(
        self, mock_anthropic_cls: MagicMock, mock_sleep: MagicMock
    ) -> None:
        refusal_response = MagicMock()
        refusal_response.stop_reason = "refusal"
        refusal_response.content = []

        mock_client = MagicMock()
        mock_anthropic_cls.return_value = mock_client
        mock_client.messages.create.return_value = refusal_response

        judge = FinancialReasoningJudge(api_key="test-key")
        result = judge.grade(
            question="Q",
            context="ctx",
            correct_answer="A",
            model_response="R",
            criteria=_make_criteria(),
        )

        self.assertTrue(result.fallback_used)
        self.assertEqual(mock_client.messages.create.call_count, 1)
        mock_sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()
