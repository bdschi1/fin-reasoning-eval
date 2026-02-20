"""
PRBench-style rubric scoring for financial reasoning evaluation.

Implements weighted binary criteria with integer weights, organized
by finance rubric categories.  Each criterion is scored 0 or 1 (binary)
and multiplied by its integer weight.  Category and overall scores are
weighted sums normalized to [0, 100].

Inspired by:
    - PRBench (2025): 19,356 expert-curated binary criteria with
      integer weights across 7 finance rubric categories
    - FLaME (2025): Standardized taxonomy for financial NLP evaluation

References:
    PRBench: Professional Reasoning Benchmark for Finance (Nov 2025)
    FLaME: Financial Language Model Evaluation (2025)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RubricCriterion:
    """A single binary scoring criterion."""

    id: str
    description: str
    weight: int = 1
    category: str = ""
    tags: List[str] = field(default_factory=list)

    def score(self, met: bool) -> int:
        """Return weighted score: weight if met, 0 otherwise."""
        return self.weight if met else 0


@dataclass
class CategoryScore:
    """Score for a single rubric category."""

    category: str
    earned: int
    possible: int
    criteria_results: Dict[str, bool] = field(default_factory=dict)

    @property
    def pct(self) -> float:
        return (self.earned / self.possible * 100) if self.possible > 0 else 0.0


@dataclass
class RubricResult:
    """Complete rubric scoring result."""

    category_scores: Dict[str, CategoryScore]
    overall_earned: int = 0
    overall_possible: int = 0

    @property
    def overall_pct(self) -> float:
        return (self.overall_earned / self.overall_possible * 100) if self.overall_possible > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "overall_score": round(self.overall_pct, 1),
            "overall_earned": self.overall_earned,
            "overall_possible": self.overall_possible,
            "categories": {
                cat: {
                    "score": round(cs.pct, 1),
                    "earned": cs.earned,
                    "possible": cs.possible,
                    "criteria": cs.criteria_results,
                }
                for cat, cs in self.category_scores.items()
            },
        }


# ---------------------------------------------------------------------------
# Rubric definition
# ---------------------------------------------------------------------------

# 7 PRBench-aligned finance rubric categories
RUBRIC_CATEGORIES = [
    "numerical_accuracy",
    "conceptual_understanding",
    "reasoning_chain",
    "financial_terminology",
    "risk_awareness",
    "assumption_identification",
    "completeness",
]


# Default criteria set — a practical starting set aligned with PRBench
# methodology. Production deployments would load from YAML with thousands
# of criteria.
DEFAULT_CRITERIA: List[RubricCriterion] = [
    # Numerical Accuracy (weight: higher = more important)
    RubricCriterion("NA_001", "Final numerical answer is correct within tolerance", 3, "numerical_accuracy"),
    RubricCriterion("NA_002", "Intermediate calculations are shown and correct", 2, "numerical_accuracy"),
    RubricCriterion("NA_003", "Units and magnitudes are consistent", 2, "numerical_accuracy"),
    RubricCriterion("NA_004", "Percentages and ratios are correctly computed", 2, "numerical_accuracy"),
    RubricCriterion("NA_005", "Growth rates computed from correct base periods", 1, "numerical_accuracy"),

    # Conceptual Understanding
    RubricCriterion("CU_001", "Correctly identifies the core financial concept tested", 3, "conceptual_understanding"),
    RubricCriterion("CU_002", "Distinguishes between related but different concepts", 2, "conceptual_understanding"),
    RubricCriterion("CU_003", "Applies appropriate financial framework", 2, "conceptual_understanding"),
    RubricCriterion("CU_004", "Recognizes edge cases or exceptions to general rules", 1, "conceptual_understanding"),

    # Reasoning Chain
    RubricCriterion("RC_001", "Reasoning steps follow logical sequence", 3, "reasoning_chain"),
    RubricCriterion("RC_002", "Each step is justified with evidence or logic", 2, "reasoning_chain"),
    RubricCriterion("RC_003", "Conclusion follows from premises", 2, "reasoning_chain"),
    RubricCriterion("RC_004", "No circular reasoning present", 2, "reasoning_chain"),
    RubricCriterion("RC_005", "Alternative explanations considered", 1, "reasoning_chain"),

    # Financial Terminology
    RubricCriterion("FT_001", "Key financial terms used correctly", 2, "financial_terminology"),
    RubricCriterion("FT_002", "GAAP vs non-GAAP distinction made where relevant", 2, "financial_terminology"),
    RubricCriterion("FT_003", "Industry-specific terminology appropriate", 1, "financial_terminology"),

    # Risk Awareness
    RubricCriterion("RA_001", "Key risks identified and acknowledged", 3, "risk_awareness"),
    RubricCriterion("RA_002", "Quantitative risk measures referenced where available", 2, "risk_awareness"),
    RubricCriterion("RA_003", "Distinguishes systematic from idiosyncratic risk", 1, "risk_awareness"),
    RubricCriterion("RA_004", "Tail risks or extreme scenarios considered", 1, "risk_awareness"),

    # Assumption Identification
    RubricCriterion("AI_001", "Explicit assumptions identified from context", 2, "assumption_identification"),
    RubricCriterion("AI_002", "Hidden or implicit assumptions surfaced", 2, "assumption_identification"),
    RubricCriterion("AI_003", "Assumptions tested for reasonableness", 1, "assumption_identification"),

    # Completeness
    RubricCriterion("CO_001", "All parts of the question addressed", 3, "completeness"),
    RubricCriterion("CO_002", "Relevant context information utilized", 2, "completeness"),
    RubricCriterion("CO_003", "Response is appropriately detailed (not too terse or verbose)", 1, "completeness"),
]


class RubricGrader:
    """Scores responses against a set of weighted binary criteria.

    Supports loading criteria from the built-in default set or from a
    YAML file for custom rubrics.
    """

    def __init__(self, criteria: Optional[List[RubricCriterion]] = None):
        self.criteria = criteria or DEFAULT_CRITERIA
        self._by_category: Dict[str, List[RubricCriterion]] = {}
        for c in self.criteria:
            self._by_category.setdefault(c.category, []).append(c)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "RubricGrader":
        """Load criteria from a YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        criteria = []
        for cat_data in data.get("categories", {}).values():
            for crit in cat_data.get("criteria", []):
                criteria.append(RubricCriterion(
                    id=crit["id"],
                    description=crit["description"],
                    weight=crit.get("weight", 1),
                    category=crit.get("category", ""),
                    tags=crit.get("tags", []),
                ))
        return cls(criteria)

    @property
    def categories(self) -> List[str]:
        return list(self._by_category.keys())

    @property
    def total_possible(self) -> int:
        return sum(c.weight for c in self.criteria)

    def score(self, judgments: Dict[str, bool]) -> RubricResult:
        """Score a response given criterion-level binary judgments.

        Args:
            judgments: Mapping of criterion_id → True/False indicating
                whether each criterion is met.

        Returns:
            RubricResult with category and overall scores.
        """
        cat_scores: Dict[str, CategoryScore] = {}

        for cat, criteria in self._by_category.items():
            earned = 0
            possible = 0
            results = {}
            for c in criteria:
                met = judgments.get(c.id, False)
                earned += c.score(met)
                possible += c.weight
                results[c.id] = met
            cat_scores[cat] = CategoryScore(
                category=cat,
                earned=earned,
                possible=possible,
                criteria_results=results,
            )

        overall_earned = sum(cs.earned for cs in cat_scores.values())
        overall_possible = sum(cs.possible for cs in cat_scores.values())

        return RubricResult(
            category_scores=cat_scores,
            overall_earned=overall_earned,
            overall_possible=overall_possible,
        )
