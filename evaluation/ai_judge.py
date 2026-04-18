"""AI-as-judge for financial reasoning evaluation.

# prompt_version: 1.0.0
# prompt_date: 2026-04-04
# description: Anthropic tool_use judge for PRBench-aligned binary rubric grading

Prompt Versioning Convention
-----------------------------
Every time the SYSTEM_PROMPT or GRADE_TOOL schema changes in a way that would
alter grading behavior, bump prompt_version (semver: major = breaking rubric
change, minor = new field/example, patch = wording tweak) and update
prompt_date. This allows eval result sets to be tagged with the prompt version
used to produce them, enabling apples-to-apples comparisons over time.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Optional

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

from .rubric_scoring import RubricCriterion


def _format_system(system: str | None) -> list[dict] | str | None:
    """Wrap system prompts >= 400 chars with cache_control for prompt caching."""
    if not system or len(system) < 400:
        return system
    return [
        {
            "type": "text",
            "text": system,
            "cache_control": {"type": "ephemeral"},
        }
    ]


# ---------------------------------------------------------------------------
# Tool schema
# ---------------------------------------------------------------------------

GRADE_TOOL: dict = {
    "name": "grade_financial_response",
    "description": "Grade a financial reasoning response against rubric criteria",
    "input_schema": {
        "type": "object",
        "properties": {
            "criterion_judgments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "criterion_id": {"type": "string"},
                        "met": {"type": "boolean"},
                        "confidence": {
                            "type": "string",
                            "enum": ["high", "medium", "low", "unclear"],
                        },
                        "reasoning": {"type": "string"},
                        "detected_pattern": {"type": "string"},
                    },
                    "required": ["criterion_id", "met", "confidence", "reasoning"],
                },
            },
            "overall_quality": {
                "type": "string",
                "enum": ["excellent", "good", "adequate", "poor", "fail"],
            },
            "critical_issues": {
                "type": "array",
                "items": {"type": "string"},
            },
        },
        "required": ["criterion_judgments", "overall_quality"],
    },
}


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """\
You are an expert financial analyst evaluating AI-generated financial analysis responses.

Your task is to grade each rubric criterion as met (true) or not met (false) based solely \
on the content of the model response relative to the question and correct answer provided.

IMPORTANT GRADING RULES:
- Grade based on content quality, not response length or presentation style.
- Longer responses are not inherently better. A concise answer addressing all \
criteria scores equally to a longer one.
- Position bias note: do not favor responses that appear first or that are formatted \
in a particular way. Quality of reasoning and correctness of content are the only \
factors that matter.
- Do not give partial credit within a single binary criterion — each is met or not met.
- Use "unclear" confidence only when the criterion genuinely cannot be evaluated from \
the response text.

FEW-SHOT EXAMPLES
-----------------

Example 1 — criterion MET (met=true):
  Criterion: "Final numerical answer is correct within tolerance" (id: NA_001)
  Question: "What is the EBITDA margin if EBITDA is $420M and revenue is $2,100M?"
  Correct answer: "20.0%"
  Model response: "EBITDA margin = EBITDA / Revenue = $420M / $2,100M = 0.20, or 20.0%."
  Judgment:
    met: true
    confidence: high
    reasoning: "The model correctly divides $420M by $2,100M and arrives at 20.0%, \
matching the correct answer exactly."
    detected_pattern: "direct_calculation"

Example 2 — criterion NOT MET (met=false):
  Criterion: "Key risks identified and acknowledged" (id: RA_001)
  Question: "Should an investor be concerned about a company with a 4.5x net debt/EBITDA \
ratio in a cyclical industry?"
  Correct answer: "Yes — leverage above 3-4x in cyclical industries raises refinancing \
and covenant risk, particularly during downturns."
  Model response: "The company has moderate leverage. Debt is manageable given current \
profitability."
  Judgment:
    met: false
    confidence: high
    reasoning: "The model does not identify cyclicality risk, refinancing risk, or \
covenant risk. It describes leverage as 'moderate' without acknowledging the elevated \
4.5x ratio relative to industry norms. No specific risks are named."
    detected_pattern: "risk_omission"

Return ONLY the tool call output. Do not add commentary outside the tool call.
"""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class CriterionJudgment:
    """Judgment for a single rubric criterion."""

    criterion_id: str
    met: bool
    confidence: str  # "high" | "medium" | "low" | "unclear"
    reasoning: str
    detected_pattern: str = ""


@dataclass
class JudgeResult:
    """Complete AI judge result for one model response."""

    criterion_judgments: list[CriterionJudgment]
    overall_quality: str
    critical_issues: list[str] = field(default_factory=list)
    fallback_used: bool = False  # True when all retries exhausted, fell back to heuristic


# ---------------------------------------------------------------------------
# Judge class
# ---------------------------------------------------------------------------

class FinancialReasoningJudge:
    """AI-as-judge for grading financial reasoning responses against rubric criteria.

    Uses Anthropic tool_use with forced tool selection to guarantee structured
    output. On validation failure retries up to max_retries times with the
    specific error appended to the prompt. Falls back to a heuristic (all
    criteria marked not met, low confidence) when all retries are exhausted.
    """

    def __init__(
        self,
        model: str = "claude-opus-4-20250514",
        api_key: Optional[str] = None,
        thinking_budget: Optional[int] = None,
    ) -> None:
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "anthropic package not installed. Install with: pip install anthropic"
            )

        resolved_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not resolved_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY or pass api_key."
            )

        self.model = model
        self.thinking_budget = thinking_budget
        self.client = anthropic.Anthropic(api_key=resolved_key)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def grade(
        self,
        question: str,
        context: str,
        correct_answer: str,
        model_response: str,
        criteria: list[RubricCriterion],
        problem_category: str = "",
    ) -> JudgeResult:
        """Grade a model response against a list of rubric criteria.

        Args:
            question: The original question posed to the model.
            context: Problem context (financial data, scenario text).
            correct_answer: The ground-truth correct answer.
            model_response: The model's response to evaluate.
            criteria: List of RubricCriterion objects to grade against.
            problem_category: Optional category label (e.g., "accounting_red_flag").

        Returns:
            JudgeResult with per-criterion judgments and overall quality rating.
        """
        messages = self._build_messages(
            question=question,
            context=context,
            correct_answer=correct_answer,
            model_response=model_response,
            criteria=criteria,
            problem_category=problem_category,
        )
        return self._call_with_retry(messages, criteria=criteria)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_messages(
        self,
        question: str,
        context: str,
        correct_answer: str,
        model_response: str,
        criteria: list[RubricCriterion],
        problem_category: str = "",
        error_feedback: Optional[str] = None,
    ) -> list[dict]:
        """Construct the messages list for the API call."""
        criteria_block = "\n".join(
            f"  - id: {c.id}\n    description: {c.description}\n    weight: {c.weight}"
            for c in criteria
        )

        category_line = (
            f"\nProblem category: {problem_category}" if problem_category else ""
        )

        user_content = (
            f"Grade the following financial reasoning response against each rubric criterion."
            f"{category_line}\n\n"
            f"## Question\n{question}\n\n"
            f"## Context\n{context}\n\n"
            f"## Correct Answer\n{correct_answer}\n\n"
            f"## Model Response\n{model_response}\n\n"
            f"## Rubric Criteria\n{criteria_block}"
        )

        if error_feedback:
            user_content += (
                f"\n\n## Validation Error from Previous Attempt\n{error_feedback}\n"
                f"Please correct the above error in your tool call output."
            )

        return [{"role": "user", "content": user_content}]

    def _call_with_retry(
        self,
        messages: list[dict],
        criteria: list[RubricCriterion],
        max_retries: int = 2,
    ) -> JudgeResult:
        """Call the Anthropic API with retry-on-validation-failure logic.

        On each attempt, if the response fails validation, append the specific
        error to the messages and retry. Falls back to heuristic judgments when
        max_retries is exhausted.
        """
        last_error: Optional[str] = None

        for attempt in range(max_retries + 1):
            # On retries, rebuild messages with error feedback
            if attempt > 0 and last_error is not None:
                # Extract original user message content and rebuild with error
                orig_content = messages[0]["content"]
                # Strip any previous error feedback block before appending new one
                if "## Validation Error from Previous Attempt" in orig_content:
                    orig_content = orig_content[
                        : orig_content.index("## Validation Error from Previous Attempt")
                    ].rstrip()
                messages = [
                    {
                        "role": "user",
                        "content": orig_content
                        + f"\n\n## Validation Error from Previous Attempt\n{last_error}\n"
                        "Please correct the above error in your tool call output.",
                    }
                ]

            try:
                api_kwargs = {
                    "model": self.model,
                    "max_tokens": 4096,
                    "system": _format_system(SYSTEM_PROMPT),
                    "tools": [GRADE_TOOL],
                    "tool_choice": {"type": "tool", "name": "grade_financial_response"},
                    "messages": messages,
                }
                if self.thinking_budget is not None:
                    api_kwargs["thinking"] = {
                        "type": "enabled",
                        "budget_tokens": self.thinking_budget,
                    }
                    # Ensure max_tokens accommodates thinking budget
                    current_max = api_kwargs.get("max_tokens", 4096)
                    if current_max < self.thinking_budget + 1024:
                        api_kwargs["max_tokens"] = self.thinking_budget + 4096
                response = self.client.messages.create(**api_kwargs)
            except Exception as exc:
                last_error = f"API call failed: {exc}"
                continue

            try:
                result = self._parse_tool_use(response)
            except Exception as exc:
                last_error = f"Failed to parse tool_use response: {exc}"
                continue

            validation_error = self._validate_result(result, criteria)
            if validation_error is None:
                return result

            last_error = validation_error

        # All retries exhausted
        fallback = self._fallback_judgments(criteria)
        fallback.critical_issues = [
            f"judge_validation_failure: {last_error}"
        ]
        return fallback

    def _parse_tool_use(self, response) -> JudgeResult:
        """Extract and deserialize the tool_use content block."""
        tool_block = None
        for block in response.content:
            if getattr(block, "type", None) == "tool_use":
                tool_block = block
                break

        if tool_block is None:
            raise ValueError(
                "No tool_use block found in response. "
                f"stop_reason={getattr(response, 'stop_reason', 'unknown')}"
            )

        raw: dict = tool_block.input

        judgments = []
        for item in raw.get("criterion_judgments", []):
            judgments.append(
                CriterionJudgment(
                    criterion_id=item["criterion_id"],
                    met=bool(item["met"]),
                    confidence=item.get("confidence", "unclear"),
                    reasoning=item.get("reasoning", ""),
                    detected_pattern=item.get("detected_pattern", ""),
                )
            )

        return JudgeResult(
            criterion_judgments=judgments,
            overall_quality=raw.get("overall_quality", "adequate"),
            critical_issues=raw.get("critical_issues", []),
            fallback_used=False,
        )

    def _validate_result(
        self,
        result: JudgeResult,
        criteria: list[RubricCriterion],
    ) -> Optional[str]:
        """Return an error message if the result is invalid, None if valid.

        Checks:
        - criterion_judgments is non-empty
        - every criterion_id in the result matches one of the supplied criteria ids
        - overall_quality is one of the allowed enum values
        - confidence values are valid
        """
        allowed_qualities = {"excellent", "good", "adequate", "poor", "fail"}
        allowed_confidences = {"high", "medium", "low", "unclear"}
        valid_ids = {c.id for c in criteria}

        if not result.criterion_judgments:
            return "criterion_judgments list is empty"

        for j in result.criterion_judgments:
            if j.criterion_id not in valid_ids:
                return (
                    f"Unknown criterion_id '{j.criterion_id}'. "
                    f"Valid ids: {sorted(valid_ids)}"
                )
            if j.confidence not in allowed_confidences:
                return (
                    f"Invalid confidence value '{j.confidence}' for criterion "
                    f"'{j.criterion_id}'. Must be one of: {sorted(allowed_confidences)}"
                )

        if result.overall_quality not in allowed_qualities:
            return (
                f"Invalid overall_quality '{result.overall_quality}'. "
                f"Must be one of: {sorted(allowed_qualities)}"
            )

        return None

    def _fallback_judgments(self, criteria: list[RubricCriterion]) -> JudgeResult:
        """Heuristic fallback when all retries are exhausted.

        Marks every criterion as not met with low confidence and sets
        fallback_used=True so callers can identify and exclude these results
        from aggregate scoring if desired.
        """
        judgments = [
            CriterionJudgment(
                criterion_id=c.id,
                met=False,
                confidence="low",
                reasoning="Fallback judgment — AI judge validation failed after all retries.",
                detected_pattern="judge_validation_failure",
            )
            for c in criteria
        ]
        return JudgeResult(
            criterion_judgments=judgments,
            overall_quality="fail",
            critical_issues=[],
            fallback_used=True,
        )
