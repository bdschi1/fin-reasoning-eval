"""Tests for vendor assessment framework."""
from __future__ import annotations

import pytest

from vendor_assessment.scorecard import (
    AssessmentDimension,
    DimensionScore,
    ScoreLevel,
    VendorScorecard,
    ComparisonReport,
)
from vendor_assessment.dimensions import (
    DEFAULT_WEIGHTS,
    score_to_level,
    score_accuracy,
    score_latency,
    score_cost_efficiency,
    score_safety,
    score_domain_expertise,
    score_consistency,
)
from vendor_assessment.framework import VendorAssessmentFramework
from vendor_assessment.comparator import VendorComparator


class TestScoreLevel:
    def test_excellent(self):
        assert score_to_level(95) == ScoreLevel.EXCELLENT

    def test_strong(self):
        assert score_to_level(80) == ScoreLevel.STRONG

    def test_adequate(self):
        assert score_to_level(65) == ScoreLevel.ADEQUATE

    def test_below(self):
        assert score_to_level(45) == ScoreLevel.BELOW_EXPECTATIONS

    def test_poor(self):
        assert score_to_level(20) == ScoreLevel.POOR

    def test_boundary_90(self):
        assert score_to_level(90) == ScoreLevel.EXCELLENT

    def test_boundary_75(self):
        assert score_to_level(75) == ScoreLevel.STRONG


class TestDimensionScoring:
    def test_accuracy_perfect(self):
        ds = score_accuracy(1.0)
        assert ds.score == 100.0
        assert ds.dimension == AssessmentDimension.ACCURACY

    def test_accuracy_with_categories(self):
        ds = score_accuracy(0.85, {"dcf": 0.90, "comps": 0.80})
        assert ds.score == 85.0
        assert len(ds.evidence) == 3

    def test_latency_fast(self):
        ds = score_latency(200)
        assert ds.score == 100.0

    def test_latency_slow(self):
        ds = score_latency(6000)
        assert ds.score == 0.0

    def test_latency_mid(self):
        ds = score_latency(2750)
        assert 40 < ds.score < 60

    def test_cost_cheap(self):
        ds = score_cost_efficiency(cost_per_1k_tokens=0.10)
        assert ds.score == 100.0

    def test_cost_expensive(self):
        ds = score_cost_efficiency(cost_per_1k_tokens=35.0)
        assert ds.score == 0.0

    def test_cost_unknown(self):
        ds = score_cost_efficiency()
        assert ds.score == 50.0

    def test_safety_robust(self):
        ds = score_safety(adversarial_accuracy=0.95)
        assert ds.score == 95.0

    def test_safety_combined(self):
        ds = score_safety(
            adversarial_accuracy=0.90, hallucination_rate=0.05,
        )
        assert ds.score == pytest.approx(92.5)  # avg(90, 95)

    def test_domain_expertise(self):
        ds = score_domain_expertise(hard_accuracy=0.80)
        assert ds.score == 80.0

    def test_consistency_stable(self):
        ds = score_consistency(score_variance=0.0, n_runs=5)
        assert ds.score == 100.0

    def test_consistency_single_run(self):
        ds = score_consistency(n_runs=1)
        assert ds.score == 50.0


class TestWeights:
    def test_weights_sum_to_one(self):
        assert abs(sum(DEFAULT_WEIGHTS.values()) - 1.0) < 0.001

    def test_all_dimensions_have_weights(self):
        for dim in AssessmentDimension:
            assert dim in DEFAULT_WEIGHTS


class TestFramework:
    @pytest.fixture
    def framework(self) -> VendorAssessmentFramework:
        return VendorAssessmentFramework()

    def test_assess_vendor_basic(self, framework):
        sc = framework.assess_vendor(
            vendor_name="Anthropic",
            model_name="claude-sonnet-4",
            overall_accuracy=0.92,
            avg_latency_ms=800,
            cost_per_1k_tokens=3.0,
        )
        assert isinstance(sc, VendorScorecard)
        assert sc.vendor_name == "Anthropic"
        assert sc.overall_score > 0
        assert len(sc.dimension_scores) == 6

    def test_assess_vendor_perfect(self, framework):
        sc = framework.assess_vendor(
            vendor_name="Test",
            model_name="perfect-model",
            overall_accuracy=1.0,
            avg_latency_ms=100,
            cost_per_1k_tokens=0.01,
            adversarial_accuracy=1.0,
            hallucination_rate=0.0,
            hard_accuracy=1.0,
            expert_accuracy=1.0,
            score_variance=0.0,
            n_runs=10,
        )
        assert sc.overall_score >= 95.0

    def test_assess_vendor_use_case_fit(self, framework):
        sc = framework.assess_vendor(
            vendor_name="Test",
            model_name="test",
            overall_accuracy=0.95,
            avg_latency_ms=300,
        )
        assert "financial_analysis" in sc.use_case_fit
        assert "real_time_trading" in sc.use_case_fit

    def test_compare_vendors(self, framework):
        sc1 = framework.assess_vendor(
            "Anthropic", "claude-sonnet-4",
            overall_accuracy=0.92, avg_latency_ms=800,
        )
        sc2 = framework.assess_vendor(
            "OpenAI", "gpt-4o",
            overall_accuracy=0.88, avg_latency_ms=600,
        )
        report = framework.compare_vendors([sc1, sc2])
        assert isinstance(report, ComparisonReport)
        assert len(report.scorecards) == 2
        assert report.overall_winner in [
            "Anthropic", "OpenAI",
        ]

    def test_compare_empty(self, framework):
        report = framework.compare_vendors([])
        assert report.overall_winner == ""

    def test_recommend_for_use_case(self, framework):
        sc1 = framework.assess_vendor(
            "A", "model-a",
            overall_accuracy=0.95, avg_latency_ms=2000,
        )
        sc2 = framework.assess_vendor(
            "B", "model-b",
            overall_accuracy=0.80, avg_latency_ms=200,
        )
        rec = framework.recommend_for_use_case(
            "financial_analysis", [sc1, sc2],
        )
        assert "model-a" in rec

    def test_recommend_empty(self, framework):
        rec = framework.recommend_for_use_case("test", [])
        assert "No vendors" in rec

    def test_custom_weights(self):
        custom = {
            "accuracy": 0.50,
            "latency": 0.20,
            "cost_efficiency": 0.10,
            "safety_robustness": 0.10,
            "domain_expertise": 0.05,
            "consistency": 0.05,
        }
        fw = VendorAssessmentFramework(weights=custom)
        sc = fw.assess_vendor(
            "Test", "test",
            overall_accuracy=0.90, avg_latency_ms=500,
        )
        # Accuracy weighted higher
        assert sc.overall_score > 0


class TestComparator:
    def test_to_markdown(self):
        report = ComparisonReport(
            title="Test Report",
            assessment_date="2024-01-01",
            scorecards=[
                VendorScorecard(
                    vendor_name="Anthropic",
                    model_name="claude-sonnet-4",
                    assessment_date="2024-01-01",
                    dimension_scores=[
                        DimensionScore(
                            dimension="accuracy",
                            score=92,
                            weight=0.3,
                            level="excellent",
                        ),
                    ],
                    overall_score=88.5,
                    strengths=["accuracy"],
                ),
            ],
            dimension_winners={"accuracy": "Anthropic"},
            overall_winner="Anthropic",
        )
        md = VendorComparator.to_markdown_table(report)
        assert "# Test Report" in md
        assert "Anthropic" in md

    def test_to_summary(self):
        report = ComparisonReport(
            title="Test",
            assessment_date="2024-01-01",
            scorecards=[
                VendorScorecard(
                    vendor_name="Anthropic",
                    model_name="claude-sonnet-4",
                    assessment_date="2024-01-01",
                    dimension_scores=[],
                    overall_score=88.5,
                ),
            ],
            overall_winner="Anthropic",
        )
        summary = VendorComparator.to_summary(report)
        assert "claude-sonnet-4" in summary
        assert "88" in summary

    def test_summary_empty(self):
        report = ComparisonReport(
            title="Test",
            assessment_date="2024-01-01",
            scorecards=[],
            overall_winner="",
        )
        assert "No vendors" in VendorComparator.to_summary(report)


class TestSchemas:
    def test_dimension_score_bounds(self):
        with pytest.raises(Exception):
            DimensionScore(
                dimension="accuracy",
                score=150,
                weight=0.3,
                level="excellent",
            )

    def test_vendor_scorecard_serialization(self):
        sc = VendorScorecard(
            vendor_name="Test",
            model_name="test",
            assessment_date="2024-01-01",
            dimension_scores=[],
            overall_score=75.0,
        )
        data = sc.model_dump()
        assert data["vendor_name"] == "Test"
        roundtrip = VendorScorecard(**data)
        assert roundtrip.overall_score == 75.0
