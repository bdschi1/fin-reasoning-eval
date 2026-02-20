from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class AssessmentDimension(StrEnum):
    ACCURACY = "accuracy"
    LATENCY = "latency"
    COST_EFFICIENCY = "cost_efficiency"
    SAFETY_ROBUSTNESS = "safety_robustness"
    DOMAIN_EXPERTISE = "domain_expertise"
    CONSISTENCY = "consistency"


class ScoreLevel(StrEnum):
    EXCELLENT = "excellent"           # 90-100
    STRONG = "strong"                 # 75-89
    ADEQUATE = "adequate"             # 60-74
    BELOW_EXPECTATIONS = "below_expectations"  # 40-59
    POOR = "poor"                     # 0-39


class DimensionScore(BaseModel):
    dimension: AssessmentDimension
    score: float = Field(ge=0, le=100)
    weight: float = Field(ge=0, le=1)
    level: ScoreLevel
    evidence: list[str] = Field(default_factory=list)
    benchmark_percentile: float | None = None


class VendorScorecard(BaseModel):
    vendor_name: str
    model_name: str
    model_version: str = ""
    assessment_date: str
    dimension_scores: list[DimensionScore]
    overall_score: float = Field(ge=0, le=100)
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    recommendation: str = ""
    use_case_fit: dict[str, str] = Field(
        default_factory=dict,
    )  # use_case -> "strong"/"adequate"/"weak"
    cost_per_1k_input_tokens: float | None = None
    cost_per_1k_output_tokens: float | None = None
    context_window: int | None = None


class ComparisonReport(BaseModel):
    title: str
    assessment_date: str
    scorecards: list[VendorScorecard]
    dimension_winners: dict[str, str] = Field(
        default_factory=dict,
    )  # dimension -> vendor_name
    overall_winner: str = ""
    summary: str = ""
