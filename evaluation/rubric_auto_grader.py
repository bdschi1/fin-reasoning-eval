"""Automated rubric grading for fin-reasoning-eval.

Uses FinancialReasoningJudge to automatically produce the judgments dict
required by RubricGrader.score(). Reduces manual effort for rubric evaluation
while maintaining traceability through confidence scores and reasoning.

# module_version: 1.0.0
# date: 2026-04-04
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Optional

from .ai_judge import FinancialReasoningJudge, JudgeResult
from .rubric_scoring import DEFAULT_CRITERIA, RubricCriterion, RubricGrader, RubricResult

logger = logging.getLogger(__name__)


@dataclass
class AutoRubricResult:
    """Result from automated rubric grading."""

    rubric_result: RubricResult
    """Final scores produced by RubricGrader.score()."""

    judgments: dict[str, bool]
    """criterion_id -> True (met) / False (not met)."""

    confidences: dict[str, str]
    """criterion_id -> 'high' | 'medium' | 'low' | 'unclear'."""

    low_confidence_criteria: list[str]
    """IDs of criteria where confidence is 'low' or 'unclear'."""

    fallback_used: bool = False
    """True when the AI judge failed all retries and heuristic fallback was used."""

    needs_human_review: bool = False
    """True when at least one criterion has low or unclear confidence."""


class RubricAutoGrader:
    """Automates rubric judgment production using FinancialReasoningJudge.

    Workflow:
    1. Accept rubric criteria (default or caller-supplied).
    2. Call FinancialReasoningJudge.grade() with the question, context,
       correct answer, model response, and criteria list.
    3. Extract a judgments dict (criterion_id -> bool) and a confidences dict
       (criterion_id -> str) from the returned JudgeResult.
    4. Pass judgments to RubricGrader.score() to produce a RubricResult.
    5. Flag low-confidence criteria for human review.

    The judge is instantiated once at construction time and reused across
    multiple .grade() calls to avoid repeated API client setup.
    """

    LOW_CONFIDENCE_VALUES: frozenset[str] = frozenset({"low", "unclear"})

    def __init__(
        self,
        judge: Optional[FinancialReasoningJudge] = None,
        model: str = "claude-opus-4-20250514",
        api_key: Optional[str] = None,
    ) -> None:
        """Initialise the auto-grader.

        Args:
            judge: Pre-constructed FinancialReasoningJudge instance. When None,
                   a new judge is created using `model` and `api_key`.
            model: Anthropic model name used when creating a new judge.
            api_key: Optional API key override passed to the new judge.
        """
        self._judge: FinancialReasoningJudge = judge or FinancialReasoningJudge(
            model=model, api_key=api_key
        )
        self._grader = RubricGrader()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def grade(
        self,
        question: str,
        context: str,
        correct_answer: str,
        model_response: str,
        criteria: Optional[list[RubricCriterion]] = None,
        problem_category: str = "",
    ) -> AutoRubricResult:
        """Auto-grade a model response against rubric criteria.

        Args:
            question: The problem question posed to the model.
            context: Problem context / financial data.
            correct_answer: The expected correct answer.
            model_response: The AI model response to evaluate.
            criteria: Rubric criteria to evaluate against. When None, uses
                      DEFAULT_CRITERIA (the full 27-criterion PRBench set).
            problem_category: Optional category label for judge context.

        Returns:
            AutoRubricResult containing rubric scores, per-criterion judgments,
            confidence ratings, and human-review flags.
        """
        effective_criteria: list[RubricCriterion] = criteria if criteria is not None else DEFAULT_CRITERIA

        # If a custom criteria list is provided, build a grader scoped to those
        # criteria; otherwise reuse the default-criteria grader.
        grader = (
            self._grader
            if effective_criteria is DEFAULT_CRITERIA
            else RubricGrader(effective_criteria)
        )

        judge_result: JudgeResult = self._judge.grade(
            question=question,
            context=context,
            correct_answer=correct_answer,
            model_response=model_response,
            criteria=effective_criteria,
            problem_category=problem_category,
        )

        if judge_result.fallback_used:
            logger.warning(
                "RubricAutoGrader: AI judge returned fallback result "
                "(validation failed after all retries). "
                "Rubric scores will reflect conservative all-not-met judgments. "
                "Consider human review of this response."
            )
            judgments, confidences = self._build_fallback_judgments(effective_criteria)
            rubric_result = grader.score(judgments)
            low_conf = list(judgments.keys())  # all are unclear in fallback
            return AutoRubricResult(
                rubric_result=rubric_result,
                judgments=judgments,
                confidences=confidences,
                low_confidence_criteria=low_conf,
                fallback_used=True,
                needs_human_review=True,
            )

        judgments, confidences = self._extract_judgments(judge_result, effective_criteria)
        rubric_result = grader.score(judgments)

        low_conf = [
            cid
            for cid, conf in confidences.items()
            if conf in self.LOW_CONFIDENCE_VALUES
        ]

        if low_conf:
            logger.info(
                "RubricAutoGrader: %d criterion/criteria flagged for human review "
                "(low or unclear confidence): %s",
                len(low_conf),
                low_conf,
            )

        return AutoRubricResult(
            rubric_result=rubric_result,
            judgments=judgments,
            confidences=confidences,
            low_confidence_criteria=low_conf,
            fallback_used=False,
            needs_human_review=bool(low_conf),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _extract_judgments(
        self,
        judge_result: JudgeResult,
        criteria: list[RubricCriterion],
    ) -> tuple[dict[str, bool], dict[str, str]]:
        """Extract judgments and confidences from a JudgeResult.

        Criteria that are present in the supplied list but absent from the
        judge's criterion_judgments are conservatively defaulted to
        met=False / confidence='unclear'.

        Args:
            judge_result: The result returned by FinancialReasoningJudge.grade().
            criteria: The criteria list that was passed to the judge.

        Returns:
            Tuple of (judgments dict, confidences dict).
        """
        # Index judge output by criterion_id for O(1) lookup.
        judge_index: dict[str, tuple[bool, str]] = {}
        for cj in judge_result.criterion_judgments:
            judge_index[cj.criterion_id] = (cj.met, cj.confidence)

        judgments: dict[str, bool] = {}
        confidences: dict[str, str] = {}

        for c in criteria:
            if c.id in judge_index:
                met, confidence = judge_index[c.id]
                judgments[c.id] = met
                confidences[c.id] = confidence
            else:
                # Conservative default for any criterion the judge omitted.
                logger.debug(
                    "RubricAutoGrader: criterion '%s' not found in judge output; "
                    "defaulting to met=False, confidence='unclear'.",
                    c.id,
                )
                judgments[c.id] = False
                confidences[c.id] = "unclear"

        return judgments, confidences

    def _build_fallback_judgments(
        self,
        criteria: list[RubricCriterion],
    ) -> tuple[dict[str, bool], dict[str, str]]:
        """Conservative fallback: all criteria not met, all confidence 'unclear'.

        Used when the AI judge fails all retries (JudgeResult.fallback_used=True).
        Preserves the conservative stance from the judge's own fallback logic.

        Args:
            criteria: The criteria list to build fallback judgments for.

        Returns:
            Tuple of (judgments dict, confidences dict).
        """
        judgments: dict[str, bool] = {c.id: False for c in criteria}
        confidences: dict[str, str] = {c.id: "unclear" for c in criteria}
        return judgments, confidences
