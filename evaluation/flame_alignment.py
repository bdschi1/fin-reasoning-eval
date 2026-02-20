"""
FLaME taxonomy alignment for financial reasoning evaluation.

Maps fin-reasoning-eval problem categories to the FLaME taxonomy
(Financial Language Model Evaluation, 2025) which defines 6 core NLP
task categories across 20 datasets.  This alignment enables cross-
benchmark comparability.

FLaME Categories:
    1. Question Answering (QA)
    2. Information Retrieval (IR)
    3. Summarization
    4. Sentiment Analysis
    5. Causal Reasoning
    6. Classification

References:
    FLaME: Financial Language Model Evaluation (2025)
    Fin-RATE: Financial Analytics Tracking Eval Benchmark (Feb 2026)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


# ---------------------------------------------------------------------------
# FLaME taxonomy categories
# ---------------------------------------------------------------------------

FLAME_CATEGORIES = [
    "question_answering",
    "information_retrieval",
    "summarization",
    "sentiment_analysis",
    "causal_reasoning",
    "classification",
]


# ---------------------------------------------------------------------------
# Fin-RATE QA pathway types
# ---------------------------------------------------------------------------

FINRATE_QA_PATHWAYS = {
    "detail_oriented_qa": "DR-QA: Detail-oriented reasoning from single documents",
    "cross_entity_qa": "EC-QA: Cross-entity comparison and relative analysis",
    "longitudinal_qa": "LT-QA: Longitudinal tracking and trend analysis over time",
}


# ---------------------------------------------------------------------------
# Category → FLaME mapping
# ---------------------------------------------------------------------------

# Maps fin-reasoning-eval problem categories to FLaME task categories.
# A single problem can map to multiple FLaME categories.
CATEGORY_TO_FLAME: Dict[str, List[str]] = {
    # Primary QA categories
    "earnings_surprise": ["question_answering", "classification"],
    "dcf_sanity_check": ["question_answering", "causal_reasoning"],
    "accounting_red_flag": ["classification", "information_retrieval"],
    "catalyst_identification": ["information_retrieval", "causal_reasoning"],
    "formula_audit": ["question_answering"],
    "financial_statement_analysis": ["question_answering", "information_retrieval"],
    "valuation_analysis": ["question_answering", "causal_reasoning"],
    "risk_assessment": ["causal_reasoning", "classification"],

    # New Fin-RATE aligned categories
    "cross_entity_qa": ["question_answering", "information_retrieval", "classification"],
    "longitudinal_qa": ["question_answering", "causal_reasoning", "summarization"],
}

# Reverse mapping: FLaME category → fin-reasoning-eval categories
FLAME_TO_CATEGORIES: Dict[str, List[str]] = {}
for _cat, _flame_cats in CATEGORY_TO_FLAME.items():
    for _fc in _flame_cats:
        FLAME_TO_CATEGORIES.setdefault(_fc, []).append(_cat)


# ---------------------------------------------------------------------------
# Fin-RATE QA pathway mapping
# ---------------------------------------------------------------------------

# Maps problem categories to Fin-RATE QA pathways
CATEGORY_TO_FINRATE: Dict[str, str] = {
    "earnings_surprise": "detail_oriented_qa",
    "dcf_sanity_check": "detail_oriented_qa",
    "accounting_red_flag": "detail_oriented_qa",
    "catalyst_identification": "detail_oriented_qa",
    "formula_audit": "detail_oriented_qa",
    "financial_statement_analysis": "detail_oriented_qa",
    "valuation_analysis": "detail_oriented_qa",
    "risk_assessment": "detail_oriented_qa",
    "cross_entity_qa": "cross_entity_qa",
    "longitudinal_qa": "longitudinal_qa",
}


# ---------------------------------------------------------------------------
# Analysis functions
# ---------------------------------------------------------------------------

@dataclass
class TaxonomyCoverage:
    """Coverage analysis result."""

    flame_coverage: Dict[str, int] = field(default_factory=dict)
    finrate_coverage: Dict[str, int] = field(default_factory=dict)
    total_problems: int = 0
    unmapped: int = 0

    def to_dict(self) -> dict:
        return {
            "total_problems": self.total_problems,
            "flame_coverage": self.flame_coverage,
            "finrate_coverage": self.finrate_coverage,
            "unmapped": self.unmapped,
        }


def analyze_coverage(problem_categories: List[str]) -> TaxonomyCoverage:
    """Analyze FLaME and Fin-RATE coverage for a list of problem categories.

    Args:
        problem_categories: List of category strings (one per problem).

    Returns:
        TaxonomyCoverage with counts per FLaME and Fin-RATE category.
    """
    result = TaxonomyCoverage(
        flame_coverage={fc: 0 for fc in FLAME_CATEGORIES},
        finrate_coverage={fp: 0 for fp in FINRATE_QA_PATHWAYS},
        total_problems=len(problem_categories),
    )

    for cat in problem_categories:
        flame_cats = CATEGORY_TO_FLAME.get(cat, [])
        if not flame_cats:
            result.unmapped += 1
            continue

        for fc in flame_cats:
            result.flame_coverage[fc] += 1

        finrate_path = CATEGORY_TO_FINRATE.get(cat)
        if finrate_path:
            result.finrate_coverage[finrate_path] += 1

    return result


def get_flame_categories(problem_category: str) -> List[str]:
    """Return FLaME categories for a given problem category."""
    return CATEGORY_TO_FLAME.get(problem_category, [])


def get_finrate_pathway(problem_category: str) -> str:
    """Return Fin-RATE QA pathway for a given problem category."""
    return CATEGORY_TO_FINRATE.get(problem_category, "detail_oriented_qa")
