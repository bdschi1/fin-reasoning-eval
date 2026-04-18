"""Judge agreement metrics for fin-reasoning-eval.

Compares FinancialReasoningJudge (AI) vs RubricGrader (heuristic) on the same
responses. Computes Cohen's kappa per rubric category and overall.
Warns when kappa < 0.6 (substantial agreement threshold).

# module_version: 1.0.0
# date: 2026-04-04
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Optional

from .rubric_scoring import RubricCriterion, RubricGrader

logger = logging.getLogger(__name__)

# Minimum number of comparison pairs required before computing kappa.
_MIN_PAIRS = 3


@dataclass
class AgreementResult:
    """Cohen's kappa agreement between AI judge and heuristic grader."""

    overall_kappa: float
    category_kappa: dict[str, float]   # category -> kappa
    n_compared: int
    low_agreement_categories: list[str]  # categories with kappa < 0.6
    warning: str = ""                    # populated if overall_kappa < 0.6


class RubricJudgeAgreement:
    """Computes Cohen's kappa between AI judge and heuristic rubric grader.

    Both raters produce per-criterion binary (met / not-met) judgments on the
    same response. Agreement is measured at the criterion level, then
    aggregated by rubric category and overall.

    Usage — single response::

        from evaluation.judge_agreement import RubricJudgeAgreement

        agreement = RubricJudgeAgreement()
        result = agreement.compare(
            question="...",
            context="...",
            correct_answer="...",
            model_response="...",
            criteria=DEFAULT_CRITERIA,
            ai_judgments={"NA_001": True, "RC_001": False, ...},
            heuristic_judgments={"NA_001": True, "RC_001": True, ...},
        )
        print(result.overall_kappa)

    Usage — batch::

        result = agreement.batch_compare([
            {"ai_judgments": {...}, "heuristic_judgments": {...}, "criteria": [...], ...},
            ...
        ])
    """

    KAPPA_WARN_THRESHOLD = 0.6

    def __init__(
        self,
        grader: Optional[RubricGrader] = None,
    ) -> None:
        self._grader = grader or RubricGrader()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def compare(
        self,
        question: str,
        context: str,
        correct_answer: str,
        model_response: str,
        criteria: list[RubricCriterion],
        ai_judgments: Optional[dict[str, bool]] = None,
        heuristic_judgments: Optional[dict[str, bool]] = None,
    ) -> AgreementResult:
        """Compare AI judge vs heuristic grader on one response.

        At least one of ``ai_judgments`` or ``heuristic_judgments`` must be
        provided. If both are provided, they are used directly. Arguments
        ``question``, ``context``, ``correct_answer``, and ``model_response``
        are accepted for API consistency and future use (e.g., lazy grading)
        but are not consumed when pre-computed judgments are supplied.

        Args:
            question: The question posed to the model (kept for API symmetry).
            context: Problem context text (kept for API symmetry).
            correct_answer: Ground-truth answer (kept for API symmetry).
            model_response: The model's response (kept for API symmetry).
            criteria: Rubric criteria whose IDs define the comparison space.
            ai_judgments: criterion_id -> bool from the AI judge. When None,
                no AI judgments are available and kappa cannot be computed.
            heuristic_judgments: criterion_id -> bool from the heuristic grader.
                When None, no heuristic judgments are available.

        Returns:
            AgreementResult. If fewer than ``_MIN_PAIRS`` criteria can be
            compared, overall_kappa is 0.0 and a warning is set.
        """
        if ai_judgments is None or heuristic_judgments is None:
            return AgreementResult(
                overall_kappa=0.0,
                category_kappa={},
                n_compared=0,
                low_agreement_categories=[],
                warning="Insufficient data: both ai_judgments and heuristic_judgments required.",
            )

        return self._compute_agreement(criteria, ai_judgments, heuristic_judgments)

    def batch_compare(
        self,
        items: list[dict],
    ) -> AgreementResult:
        """Aggregate agreement across multiple responses.

        Each item in ``items`` should be a dict with at minimum:
            - ``criteria``: list[RubricCriterion]
            - ``ai_judgments``: dict[str, bool]
            - ``heuristic_judgments``: dict[str, bool]

        Additional keys (question, context, etc.) are accepted but ignored.

        Returns:
            AgreementResult aggregated across all items. Pairs from all items
            are pooled before computing kappa.
        """
        all_ai: list[bool] = []
        all_heuristic: list[bool] = []
        category_ai: dict[str, list[bool]] = {}
        category_heuristic: dict[str, list[bool]] = {}

        for item in items:
            criteria: list[RubricCriterion] = item.get("criteria", [])
            ai_j: Optional[dict[str, bool]] = item.get("ai_judgments")
            heur_j: Optional[dict[str, bool]] = item.get("heuristic_judgments")

            if not criteria or ai_j is None or heur_j is None:
                continue

            for c in criteria:
                if c.id not in ai_j or c.id not in heur_j:
                    continue
                all_ai.append(ai_j[c.id])
                all_heuristic.append(heur_j[c.id])
                cat = c.category or "uncategorized"
                category_ai.setdefault(cat, []).append(ai_j[c.id])
                category_heuristic.setdefault(cat, []).append(heur_j[c.id])

        n = len(all_ai)
        if n < _MIN_PAIRS:
            return AgreementResult(
                overall_kappa=0.0,
                category_kappa={},
                n_compared=n,
                low_agreement_categories=[],
                warning=(
                    f"Insufficient comparison pairs ({n} < {_MIN_PAIRS}). "
                    "Collect more graded responses before interpreting kappa."
                ),
            )

        overall_kappa = self.cohens_kappa(all_ai, all_heuristic)
        cat_kappa: dict[str, float] = {}
        for cat in category_ai:
            if len(category_ai[cat]) >= _MIN_PAIRS:
                cat_kappa[cat] = self.cohens_kappa(
                    category_ai[cat], category_heuristic[cat]
                )

        low_cats = [c for c, k in cat_kappa.items() if k < self.KAPPA_WARN_THRESHOLD]
        warning = ""
        if overall_kappa < self.KAPPA_WARN_THRESHOLD:
            warning = (
                f"Overall kappa {overall_kappa:.3f} is below the substantial-agreement "
                f"threshold ({self.KAPPA_WARN_THRESHOLD}). Review the judge prompt or "
                "few-shot examples to improve AI/heuristic alignment."
            )
            logger.warning(warning)

        return AgreementResult(
            overall_kappa=overall_kappa,
            category_kappa=cat_kappa,
            n_compared=n,
            low_agreement_categories=low_cats,
            warning=warning,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_agreement(
        self,
        criteria: list[RubricCriterion],
        ai_judgments: dict[str, bool],
        heuristic_judgments: dict[str, bool],
    ) -> AgreementResult:
        """Core agreement computation for a single response."""
        all_ai: list[bool] = []
        all_heuristic: list[bool] = []
        category_ai: dict[str, list[bool]] = {}
        category_heuristic: dict[str, list[bool]] = {}

        for c in criteria:
            if c.id not in ai_judgments or c.id not in heuristic_judgments:
                continue
            all_ai.append(ai_judgments[c.id])
            all_heuristic.append(heuristic_judgments[c.id])
            cat = c.category or "uncategorized"
            category_ai.setdefault(cat, []).append(ai_judgments[c.id])
            category_heuristic.setdefault(cat, []).append(heuristic_judgments[c.id])

        n = len(all_ai)
        if n < _MIN_PAIRS:
            return AgreementResult(
                overall_kappa=0.0,
                category_kappa={},
                n_compared=n,
                low_agreement_categories=[],
                warning=(
                    f"Insufficient comparison pairs ({n} < {_MIN_PAIRS}). "
                    "Collect more graded responses before interpreting kappa."
                ),
            )

        overall_kappa = self.cohens_kappa(all_ai, all_heuristic)
        cat_kappa: dict[str, float] = {}
        for cat in category_ai:
            if len(category_ai[cat]) >= _MIN_PAIRS:
                cat_kappa[cat] = self.cohens_kappa(
                    category_ai[cat], category_heuristic[cat]
                )

        low_cats = [c for c, k in cat_kappa.items() if k < self.KAPPA_WARN_THRESHOLD]
        warning = ""
        if overall_kappa < self.KAPPA_WARN_THRESHOLD:
            warning = (
                f"Overall kappa {overall_kappa:.3f} is below the substantial-agreement "
                f"threshold ({self.KAPPA_WARN_THRESHOLD}). Review the judge prompt or "
                "few-shot examples to improve AI/heuristic alignment."
            )
            logger.warning(warning)

        return AgreementResult(
            overall_kappa=overall_kappa,
            category_kappa=cat_kappa,
            n_compared=n,
            low_agreement_categories=low_cats,
            warning=warning,
        )

    # ------------------------------------------------------------------
    # Static metric
    # ------------------------------------------------------------------

    @staticmethod
    def cohens_kappa(ratings_a: list[bool], ratings_b: list[bool]) -> float:
        """Compute Cohen's kappa for binary ratings.

        Formula: kappa = (p_o - p_e) / (1 - p_e)

        where:
            p_o = observed agreement proportion
            p_e = expected agreement by chance

        Returns 0.0 when p_e == 1.0 (all ratings identical, no disagreement
        possible) or when the input lists are empty.

        Args:
            ratings_a: Binary ratings from rater A (True = positive).
            ratings_b: Binary ratings from rater B (True = positive).

        Returns:
            Cohen's kappa in range [-1, 1]. Values >= 0.6 indicate substantial
            agreement; values < 0.4 indicate poor agreement.

        Raises:
            ValueError: If ratings_a and ratings_b have different lengths.
        """
        if len(ratings_a) != len(ratings_b):
            raise ValueError(
                f"ratings_a and ratings_b must have the same length; "
                f"got {len(ratings_a)} and {len(ratings_b)}"
            )
        n = len(ratings_a)
        if n == 0:
            return 0.0

        # Observed agreement
        agree = sum(1 for a, b in zip(ratings_a, ratings_b) if a == b)
        p_o = agree / n

        # Expected agreement by chance
        # p(A rates positive) * p(B rates positive) + p(A rates negative) * p(B rates negative)
        p_a_pos = sum(ratings_a) / n
        p_b_pos = sum(ratings_b) / n
        p_a_neg = 1.0 - p_a_pos
        p_b_neg = 1.0 - p_b_pos
        p_e = p_a_pos * p_b_pos + p_a_neg * p_b_neg

        if abs(1.0 - p_e) < 1e-12:
            # Perfect expected agreement — no room for improvement; kappa undefined.
            # Return 1.0 if observed agreement is also perfect, else 0.0.
            return 1.0 if abs(p_o - 1.0) < 1e-12 else 0.0

        return (p_o - p_e) / (1.0 - p_e)
