"""Tests for calibration scoring module."""
import math
import pytest

from evaluation.calibration import (
    CalibrationReport,
    brier_score,
    expected_calibration_error,
    generate_calibration_report,
    log_loss_score,
    parse_confidence_from_response,
)


# ---------------------------------------------------------------------------
# brier_score
# ---------------------------------------------------------------------------

class TestBrierScore:
    """Tests for brier_score()."""

    def test_perfect_prediction_outcome_1(self):
        assert brier_score(1.0, 1) == 0.0

    def test_perfect_prediction_outcome_0(self):
        assert brier_score(0.0, 0) == 0.0

    def test_worst_prediction_outcome_1(self):
        assert brier_score(0.0, 1) == 1.0

    def test_worst_prediction_outcome_0(self):
        assert brier_score(1.0, 0) == 1.0

    def test_midpoint(self):
        assert brier_score(0.5, 1) == pytest.approx(0.25)
        assert brier_score(0.5, 0) == pytest.approx(0.25)

    def test_typical_prediction(self):
        assert brier_score(0.8, 1) == pytest.approx(0.04)
        assert brier_score(0.2, 0) == pytest.approx(0.04)

    def test_invalid_prob_too_high(self):
        with pytest.raises(ValueError, match="predicted_prob must be in"):
            brier_score(1.5, 1)

    def test_invalid_prob_negative(self):
        with pytest.raises(ValueError, match="predicted_prob must be in"):
            brier_score(-0.1, 0)

    def test_invalid_outcome(self):
        with pytest.raises(ValueError, match="actual_outcome must be 0 or 1"):
            brier_score(0.5, 2)


# ---------------------------------------------------------------------------
# log_loss_score
# ---------------------------------------------------------------------------

class TestLogLossScore:
    """Tests for log_loss_score()."""

    def test_perfect_prediction_outcome_1(self):
        # log(1.0) = 0 — near-perfect
        assert log_loss_score(1.0, 1) == pytest.approx(0.0, abs=1e-10)

    def test_perfect_prediction_outcome_0(self):
        assert log_loss_score(0.0, 0) == pytest.approx(0.0, abs=1e-10)

    def test_midpoint(self):
        expected = -math.log(0.5)
        assert log_loss_score(0.5, 1) == pytest.approx(expected)
        assert log_loss_score(0.5, 0) == pytest.approx(expected)

    def test_confident_correct(self):
        # -log(0.9) ~ 0.1054
        assert log_loss_score(0.9, 1) == pytest.approx(-math.log(0.9))

    def test_confident_wrong(self):
        # -log(1 - 0.9) = -log(0.1) ~ 2.3026
        assert log_loss_score(0.9, 0) == pytest.approx(-math.log(0.1))

    def test_eps_prevents_infinity(self):
        # With eps, log(0) is avoided
        result = log_loss_score(0.0, 1)
        assert math.isfinite(result)
        assert result > 30  # Very large but finite

    def test_invalid_prob(self):
        with pytest.raises(ValueError):
            log_loss_score(1.5, 1)

    def test_invalid_outcome(self):
        with pytest.raises(ValueError):
            log_loss_score(0.5, -1)


# ---------------------------------------------------------------------------
# expected_calibration_error
# ---------------------------------------------------------------------------

class TestExpectedCalibrationError:
    """Tests for expected_calibration_error()."""

    def test_empty_inputs(self):
        ece, bins = expected_calibration_error([], [])
        assert ece == 0.0
        assert bins == []

    def test_perfect_calibration(self):
        # All predictions at 1.0 and all correct
        probs = [1.0, 1.0, 1.0]
        outcomes = [1, 1, 1]
        ece, bins = expected_calibration_error(probs, outcomes)
        assert ece == pytest.approx(0.0, abs=0.001)

    def test_worst_calibration(self):
        # All predictions at 1.0 but all wrong
        probs = [1.0, 1.0, 1.0]
        outcomes = [0, 0, 0]
        ece, bins = expected_calibration_error(probs, outcomes)
        assert ece == pytest.approx(1.0, abs=0.001)

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            expected_calibration_error([0.5], [1, 0])

    def test_returns_per_bin_stats(self):
        probs = [0.1, 0.3, 0.5, 0.7, 0.9]
        outcomes = [0, 0, 1, 1, 1]
        ece, bins = expected_calibration_error(probs, outcomes, n_bins=5)

        assert len(bins) == 5
        for b in bins:
            assert "bin_range" in b
            assert "count" in b
            assert "avg_confidence" in b
            assert "avg_accuracy" in b
            assert "gap" in b

    def test_nonempty_bins_have_positive_count(self):
        probs = [0.15, 0.85]
        outcomes = [0, 1]
        _, bins = expected_calibration_error(probs, outcomes, n_bins=10)
        nonempty = [b for b in bins if b["count"] > 0]
        assert len(nonempty) == 2

    def test_ece_range(self):
        # ECE should be in [0, 1]
        probs = [0.2, 0.4, 0.6, 0.8]
        outcomes = [1, 0, 1, 0]
        ece, _ = expected_calibration_error(probs, outcomes)
        assert 0.0 <= ece <= 1.0


# ---------------------------------------------------------------------------
# parse_confidence_from_response
# ---------------------------------------------------------------------------

class TestParseConfidenceFromResponse:
    """Tests for parse_confidence_from_response()."""

    def test_explicit_confidence_percent(self):
        assert parse_confidence_from_response("I'm 80% confident") == pytest.approx(0.8)

    def test_confidence_with_colon(self):
        assert parse_confidence_from_response("Confidence: 85%") == pytest.approx(0.85)

    def test_confidence_word_percent(self):
        result = parse_confidence_from_response("confidence: 75 percent")
        assert result == pytest.approx(0.75)

    def test_probability_percent(self):
        result = parse_confidence_from_response("There is a 60% probability")
        assert result == pytest.approx(0.6)

    def test_decimal_confidence(self):
        result = parse_confidence_from_response("confidence of 0.85")
        assert result == pytest.approx(0.85)

    def test_decimal_probability(self):
        result = parse_confidence_from_response("probability: 0.72")
        assert result == pytest.approx(0.72)

    def test_high_confidence_qualitative(self):
        result = parse_confidence_from_response("I have high confidence in this")
        assert result == pytest.approx(0.85)

    def test_moderate_confidence_qualitative(self):
        result = parse_confidence_from_response("moderate confidence in the outcome")
        assert result == pytest.approx(0.65)

    def test_low_confidence_qualitative(self):
        result = parse_confidence_from_response("I have low confidence here")
        assert result == pytest.approx(0.30)

    def test_reasonably_confident(self):
        result = parse_confidence_from_response("I'm reasonably confident this is correct")
        assert result == pytest.approx(0.75)

    def test_no_confidence_found(self):
        result = parse_confidence_from_response("The answer is B.")
        assert result is None

    def test_empty_string(self):
        assert parse_confidence_from_response("") is None

    def test_returns_float_in_range(self):
        result = parse_confidence_from_response("90% confident")
        assert result is not None
        assert 0.0 <= result <= 1.0


# ---------------------------------------------------------------------------
# CalibrationReport dataclass
# ---------------------------------------------------------------------------

class TestCalibrationReport:
    """Tests for CalibrationReport dataclass."""

    def test_to_dict(self):
        report = CalibrationReport(
            brier=0.15,
            log_loss=0.45,
            ece=0.08,
            n_predictions=100,
            per_bin_stats=[],
        )
        d = report.to_dict()
        assert d["brier_score"] == 0.15
        assert d["log_loss"] == 0.45
        assert d["ece"] == 0.08
        assert d["n_predictions"] == 100

    def test_default_per_bin_stats(self):
        report = CalibrationReport(brier=0.1, log_loss=0.3, ece=0.05, n_predictions=10)
        assert report.per_bin_stats == []


# ---------------------------------------------------------------------------
# generate_calibration_report
# ---------------------------------------------------------------------------

class TestGenerateCalibrationReport:
    """Tests for generate_calibration_report()."""

    def test_empty_input(self):
        report = generate_calibration_report([], [])
        assert report.n_predictions == 0
        assert report.brier == 0.0
        assert report.log_loss == 0.0
        assert report.ece == 0.0

    def test_well_calibrated(self):
        probs = [0.9, 0.9, 0.9, 0.1, 0.1, 0.1]
        outcomes = [1, 1, 1, 0, 0, 0]
        report = generate_calibration_report(probs, outcomes)
        assert report.n_predictions == 6
        # Well-calibrated: Brier should be low
        assert report.brier < 0.1
        assert report.ece < 0.15

    def test_poorly_calibrated(self):
        probs = [0.9, 0.9, 0.9]
        outcomes = [0, 0, 0]
        report = generate_calibration_report(probs, outcomes)
        assert report.brier > 0.5
        assert report.ece > 0.5

    def test_mismatched_lengths(self):
        with pytest.raises(ValueError):
            generate_calibration_report([0.5, 0.5], [1])

    def test_report_has_per_bin_stats(self):
        probs = [0.1, 0.5, 0.9]
        outcomes = [0, 1, 1]
        report = generate_calibration_report(probs, outcomes)
        assert len(report.per_bin_stats) == 10  # default n_bins

    def test_custom_bins(self):
        probs = [0.2, 0.8]
        outcomes = [0, 1]
        report = generate_calibration_report(probs, outcomes, n_bins=5)
        assert len(report.per_bin_stats) == 5


# ---------------------------------------------------------------------------
# Integration: metrics.py uses calibration module
# ---------------------------------------------------------------------------

class TestMetricsCalibrationIntegration:
    """Verify FinancialReasoningMetrics correctly uses calibration module."""

    def test_compute_returns_brier_and_log_loss(self):
        from evaluation.metrics import FinancialReasoningMetrics

        metrics = FinancialReasoningMetrics()
        # Add predictions with confidence scores
        metrics.add_prediction(
            problem_id="p1", predicted="A", reference="A",
            category="test", difficulty="easy", confidence=0.9,
        )
        metrics.add_prediction(
            problem_id="p2", predicted="B", reference="A",
            category="test", difficulty="easy", confidence=0.3,
        )
        metrics.add_prediction(
            problem_id="p3", predicted="C", reference="C",
            category="test", difficulty="easy", confidence=0.8,
        )

        results = metrics.compute()
        assert results.calibration_error is not None
        assert results.brier_score_avg is not None
        assert results.log_loss_avg is not None
        assert results.calibration_per_bin is not None
        assert len(results.calibration_per_bin) == 10

    def test_compute_without_confidence_has_none(self):
        from evaluation.metrics import FinancialReasoningMetrics

        metrics = FinancialReasoningMetrics()
        metrics.add_prediction(
            problem_id="p1", predicted="A", reference="A",
            category="test", difficulty="easy",
        )

        results = metrics.compute()
        assert results.calibration_error is None
        assert results.brier_score_avg is None
        assert results.log_loss_avg is None
        assert results.calibration_per_bin is None

    def test_to_dict_includes_new_fields(self):
        from evaluation.metrics import FinancialReasoningMetrics

        metrics = FinancialReasoningMetrics()
        metrics.add_prediction(
            problem_id="p1", predicted="A", reference="A",
            category="test", difficulty="easy", confidence=0.9,
        )
        results = metrics.compute()
        d = results.to_dict()
        assert "brier_score_avg" in d
        assert "log_loss_avg" in d
