"""Evaluation module for Financial Reasoning Eval Benchmark."""

from .metrics import (
    FinancialReasoningMetrics,
    compute_accuracy,
    compute_category_accuracy,
    compute_difficulty_accuracy,
    compute_reasoning_quality,
)
from .calibration import (
    CalibrationReport,
    brier_score,
    expected_calibration_error,
    generate_calibration_report,
    log_loss_score,
    parse_confidence_from_response,
)
from .dataset import FinancialReasoningDataset, load_benchmark
from .narrative import generate_narrative_summary

__all__ = [
    'FinancialReasoningMetrics',
    'FinancialReasoningDataset',
    'load_benchmark',
    'compute_accuracy',
    'compute_category_accuracy',
    'compute_difficulty_accuracy',
    'compute_reasoning_quality',
    'generate_narrative_summary',
    'CalibrationReport',
    'brier_score',
    'log_loss_score',
    'expected_calibration_error',
    'generate_calibration_report',
    'parse_confidence_from_response',
]
