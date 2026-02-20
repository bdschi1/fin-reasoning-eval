from __future__ import annotations

import logging
from datetime import date

from .scorecard import (
    VendorScorecard,
    ComparisonReport,
    DimensionScore,
)
from .dimensions import (
    DEFAULT_WEIGHTS,
    score_accuracy,
    score_latency,
    score_cost_efficiency,
    score_safety,
    score_domain_expertise,
    score_consistency,
)

logger = logging.getLogger(__name__)


class VendorAssessmentFramework:
    """Assess and compare AI model vendors for financial use cases."""

    def __init__(
        self, weights: dict[str, float] | None = None,
    ) -> None:
        self._weights = weights or dict(DEFAULT_WEIGHTS)

    def assess_vendor(
        self,
        vendor_name: str,
        model_name: str,
        overall_accuracy: float = 0.0,
        category_accuracies: dict[str, float] | None = None,
        avg_latency_ms: float = 1000.0,
        p95_latency_ms: float | None = None,
        cost_per_1k_tokens: float | None = None,
        cost_per_correct: float | None = None,
        adversarial_accuracy: float | None = None,
        hallucination_rate: float | None = None,
        hard_accuracy: float | None = None,
        expert_accuracy: float | None = None,
        score_variance: float | None = None,
        n_runs: int = 1,
        context_window: int | None = None,
        model_version: str = "",
    ) -> VendorScorecard:
        """Create a vendor scorecard from raw metrics."""
        dimensions = [
            score_accuracy(overall_accuracy, category_accuracies),
            score_latency(avg_latency_ms, p95_latency_ms),
            score_cost_efficiency(
                cost_per_correct, cost_per_1k_tokens,
            ),
            score_safety(adversarial_accuracy, hallucination_rate),
            score_domain_expertise(
                hard_accuracy, expert_accuracy, category_accuracies,
            ),
            score_consistency(score_variance, n_runs),
        ]

        # Apply custom weights
        for dim in dimensions:
            if dim.dimension in self._weights:
                dim.weight = self._weights[dim.dimension]

        overall = sum(d.score * d.weight for d in dimensions)

        strengths = [
            d.dimension.value for d in dimensions if d.score >= 75
        ]
        weaknesses = [
            d.dimension.value for d in dimensions if d.score < 60
        ]

        # Use case fit
        use_case_fit = self._assess_use_case_fit(dimensions)

        return VendorScorecard(
            vendor_name=vendor_name,
            model_name=model_name,
            model_version=model_version,
            assessment_date=str(date.today()),
            dimension_scores=dimensions,
            overall_score=round(overall, 1),
            strengths=strengths,
            weaknesses=weaknesses,
            use_case_fit=use_case_fit,
            cost_per_1k_input_tokens=cost_per_1k_tokens,
            context_window=context_window,
        )

    def compare_vendors(
        self, scorecards: list[VendorScorecard],
    ) -> ComparisonReport:
        """Compare multiple vendor scorecards."""
        dimension_winners: dict[str, str] = {}
        dim_names = [
            "accuracy", "latency", "cost_efficiency",
            "safety_robustness", "domain_expertise", "consistency",
        ]
        for dim_name in dim_names:
            best_score = -1.0
            best_vendor = ""
            for sc in scorecards:
                for ds in sc.dimension_scores:
                    if (
                        ds.dimension.value == dim_name
                        and ds.score > best_score
                    ):
                        best_score = ds.score
                        best_vendor = sc.vendor_name
            if best_vendor:
                dimension_winners[dim_name] = best_vendor

        overall_winner = (
            max(scorecards, key=lambda s: s.overall_score).vendor_name
            if scorecards
            else ""
        )

        return ComparisonReport(
            title="AI Vendor Assessment — Financial Use Cases",
            assessment_date=str(date.today()),
            scorecards=scorecards,
            dimension_winners=dimension_winners,
            overall_winner=overall_winner,
        )

    @staticmethod
    def _assess_use_case_fit(
        dimensions: list[DimensionScore],
    ) -> dict[str, str]:
        """Map dimension scores to use-case fitness."""
        dim_map = {
            d.dimension.value: d.score for d in dimensions
        }
        fits: dict[str, str] = {}

        # Financial analysis: needs accuracy + domain expertise
        analysis_score = (
            dim_map.get("accuracy", 50) * 0.5
            + dim_map.get("domain_expertise", 50) * 0.5
        )
        fits["financial_analysis"] = (
            "strong" if analysis_score >= 75
            else "adequate" if analysis_score >= 60
            else "weak"
        )

        # Real-time trading: needs latency + consistency
        trading_score = (
            dim_map.get("latency", 50) * 0.5
            + dim_map.get("consistency", 50) * 0.5
        )
        fits["real_time_trading"] = (
            "strong" if trading_score >= 75
            else "adequate" if trading_score >= 60
            else "weak"
        )

        # Document processing: needs accuracy + cost efficiency
        doc_score = (
            dim_map.get("accuracy", 50) * 0.4
            + dim_map.get("cost_efficiency", 50) * 0.6
        )
        fits["document_processing"] = (
            "strong" if doc_score >= 75
            else "adequate" if doc_score >= 60
            else "weak"
        )

        # Compliance/risk: needs safety + accuracy
        compliance_score = (
            dim_map.get("safety_robustness", 50) * 0.6
            + dim_map.get("accuracy", 50) * 0.4
        )
        fits["compliance_risk"] = (
            "strong" if compliance_score >= 75
            else "adequate" if compliance_score >= 60
            else "weak"
        )

        return fits

    @staticmethod
    def recommend_for_use_case(
        use_case: str, scorecards: list[VendorScorecard],
    ) -> str:
        """Recommend a vendor for a specific use case."""
        if not scorecards:
            return "No vendors assessed."

        best: VendorScorecard | None = None
        best_fit = "weak"
        for sc in scorecards:
            fit = sc.use_case_fit.get(use_case, "weak")
            if fit == "strong" and best_fit != "strong":
                best = sc
                best_fit = fit
            elif fit == "adequate" and best_fit == "weak":
                best = sc
                best_fit = fit
            elif (
                fit == best_fit
                and best is not None
                and sc.overall_score > best.overall_score
            ):
                best = sc

        if best is None:
            best = max(
                scorecards, key=lambda s: s.overall_score,
            )

        return (
            f"Recommended: {best.model_name} ({best.vendor_name}) "
            f"for {use_case} — overall score "
            f"{best.overall_score:.0f}/100, "
            f"fit: {best.use_case_fit.get(use_case, 'unknown')}"
        )
