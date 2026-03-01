"""Calibration scoring for financial reasoning evaluation.

Implements proper scoring rules for evaluating probability/confidence estimates
from LLM predictions. Ported from judgment-under-uncertainty-eval's calibration
module and adapted for the fin-reasoning-eval context.

Metrics:
    - Brier score: quadratic scoring rule (0 = perfect, 1 = worst)
    - Log loss: logarithmic scoring rule (cross-entropy)
    - ECE: Expected Calibration Error (binned calibration metric)
    - Confidence parsing: extract confidence levels from free-text responses

Scoring methodology draws on proper scoring rules as described in Prophet Arena
(Xu et al., UChicago DSI / SIGMA Lab, 2025).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


def brier_score(predicted_prob: float, actual_outcome: int) -> float:
    """Compute Brier score for a single prediction.

    Brier score = (predicted_probability - actual_outcome)^2
    Range: 0 (perfect) to 1 (worst).

    Args:
        predicted_prob: Model's predicted probability in [0, 1].
        actual_outcome: Actual binary outcome (0 or 1).

    Returns:
        Brier score (lower is better).

    Raises:
        ValueError: If predicted_prob is not in [0, 1] or outcome not in {0, 1}.
    """
    if not 0.0 <= predicted_prob <= 1.0:
        raise ValueError(f"predicted_prob must be in [0, 1], got {predicted_prob}")
    if actual_outcome not in (0, 1):
        raise ValueError(f"actual_outcome must be 0 or 1, got {actual_outcome}")
    return (predicted_prob - actual_outcome) ** 2


def log_loss_score(
    predicted_prob: float, actual_outcome: int, eps: float = 1e-15
) -> float:
    """Compute log loss (cross-entropy) for a single prediction.

    Args:
        predicted_prob: Model's predicted probability in [0, 1].
        actual_outcome: Actual binary outcome (0 or 1).
        eps: Small value to avoid log(0).

    Returns:
        Log loss (lower is better). Range: 0 to ~34.5.

    Raises:
        ValueError: If predicted_prob is not in [0, 1] or outcome not in {0, 1}.
    """
    if not 0.0 <= predicted_prob <= 1.0:
        raise ValueError(f"predicted_prob must be in [0, 1], got {predicted_prob}")
    if actual_outcome not in (0, 1):
        raise ValueError(f"actual_outcome must be 0 or 1, got {actual_outcome}")
    p = max(eps, min(1 - eps, predicted_prob))
    if actual_outcome == 1:
        return -math.log(p)
    return -math.log(1 - p)


def expected_calibration_error(
    predicted_probs: List[float],
    actual_outcomes: List[int],
    n_bins: int = 10,
) -> Tuple[float, List[Dict]]:
    """Compute Expected Calibration Error (ECE) across multiple predictions.

    ECE = sum(|bin_accuracy - bin_confidence| * bin_weight)

    Returns per-bin statistics including count, average confidence, average
    accuracy, and the gap between them. This is the richer version that
    provides transparency into where calibration breaks down.

    Args:
        predicted_probs: List of predicted probabilities in [0, 1].
        actual_outcomes: List of actual binary outcomes (0 or 1).
        n_bins: Number of calibration bins.

    Returns:
        Tuple of (ECE value, list of per-bin statistics dicts).

    Raises:
        ValueError: If inputs have different lengths.
    """
    if len(predicted_probs) != len(actual_outcomes):
        raise ValueError("predicted_probs and actual_outcomes must have same length")
    if not predicted_probs:
        return 0.0, []

    bin_edges = [i / n_bins for i in range(n_bins + 1)]
    bins_data: List[Dict] = []
    total = len(predicted_probs)
    ece = 0.0

    for b in range(n_bins):
        low, high = bin_edges[b], bin_edges[b + 1]
        indices = [
            i
            for i, p in enumerate(predicted_probs)
            if (low <= p < high) or (b == n_bins - 1 and p == high)
        ]

        if not indices:
            bins_data.append({
                "bin_range": (low, high),
                "count": 0,
                "avg_confidence": 0.0,
                "avg_accuracy": 0.0,
                "gap": 0.0,
            })
            continue

        bin_probs = [predicted_probs[i] for i in indices]
        bin_outcomes = [actual_outcomes[i] for i in indices]
        avg_confidence = sum(bin_probs) / len(bin_probs)
        avg_accuracy = sum(bin_outcomes) / len(bin_outcomes)
        gap = abs(avg_accuracy - avg_confidence)
        weight = len(indices) / total
        ece += gap * weight

        bins_data.append({
            "bin_range": (low, high),
            "count": len(indices),
            "avg_confidence": round(avg_confidence, 4),
            "avg_accuracy": round(avg_accuracy, 4),
            "gap": round(gap, 4),
        })

    return round(ece, 4), bins_data


def parse_confidence_from_response(text: str) -> Optional[float]:
    """Extract a confidence level from a model's free-text response.

    Adapted from judgment-under-uncertainty-eval's parse_probability_from_response,
    but tuned for confidence expressions commonly found in financial reasoning
    outputs (e.g., "I'm 80% confident", "confidence: high", "likely correct").

    Args:
        text: Model response text.

    Returns:
        Confidence as a float in [0, 1], or None if no confidence found.
    """
    text_lower = text.lower()

    # Pattern 1: Explicit confidence percentage
    # "I'm 80% confident", "confidence: 85%", "80% confidence"
    conf_pct_pattern = (
        r'(?:confidence|confident)\s*[:=]?\s*(\d{1,3})\s*(?:%|percent)'
        r'|(\d{1,3})\s*(?:%|percent)\s*(?:confidence|confident)'
    )
    conf_match = re.search(conf_pct_pattern, text_lower)
    if conf_match:
        val_str = conf_match.group(1) or conf_match.group(2)
        val = float(val_str)
        if 1 <= val <= 100:
            return val / 100

    # Pattern 2: Generic percentage in probability/likelihood context
    # "75% probability", "probability of 75%", "70% likely"
    prob_pct_pattern = (
        r'(?:probability|likelihood|chance|likely)\s*(?:of|:)?\s*(\d{1,3})\s*(?:%|percent)'
        r'|(\d{1,3})\s*(?:%|percent)\s*(?:probability|likelihood|chance|likely)'
    )
    prob_match = re.search(prob_pct_pattern, text_lower)
    if prob_match:
        val_str = prob_match.group(1) or prob_match.group(2)
        val = float(val_str)
        if 1 <= val <= 100:
            return val / 100

    # Pattern 3: Decimal confidence
    # "confidence of 0.85", "probability: 0.75"
    dec_pattern = r'(?:confidence|probability|likelihood|chance)\s*(?:of|:)?\s*(0\.\d{1,4})'
    dec_match = re.search(dec_pattern, text_lower)
    if dec_match:
        val = float(dec_match.group(1))
        if 0 < val < 1:
            return val

    # Pattern 4: Qualitative confidence levels
    # Map common qualitative descriptors to numeric values
    qual_mappings = [
        (r'\b(?:very high|extremely) confidence\b', 0.95),
        (r'\bhigh(?:ly)? confident\b', 0.85),
        (r'\bhigh confidence\b', 0.85),
        (r'\bmoderately confident\b', 0.65),
        (r'\bmoderate confidence\b', 0.65),
        (r'\bfairly confident\b', 0.70),
        (r'\breasonably confident\b', 0.75),
        (r'\bsomewhat confident\b', 0.55),
        (r'\blow confidence\b', 0.30),
        (r'\bnot (?:very )?confident\b', 0.25),
        (r'\bvery low confidence\b', 0.15),
    ]
    for pattern, mapped_val in qual_mappings:
        if re.search(pattern, text_lower):
            return mapped_val

    return None


@dataclass
class CalibrationReport:
    """Aggregated calibration metrics for a set of predictions.

    Attributes:
        brier: Average Brier score across all predictions.
        log_loss: Average log loss across all predictions.
        ece: Expected Calibration Error.
        n_predictions: Number of predictions scored.
        per_bin_stats: Per-bin calibration statistics from ECE computation.
    """
    brier: float
    log_loss: float
    ece: float
    n_predictions: int
    per_bin_stats: List[Dict] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "brier_score": self.brier,
            "log_loss": self.log_loss,
            "ece": self.ece,
            "n_predictions": self.n_predictions,
            "per_bin_stats": self.per_bin_stats,
        }


def generate_calibration_report(
    predicted_probs: List[float],
    actual_outcomes: List[int],
    n_bins: int = 10,
) -> CalibrationReport:
    """Generate a full calibration report from predictions and outcomes.

    Computes Brier score, log loss, and ECE in one pass.

    Args:
        predicted_probs: List of predicted probabilities in [0, 1].
        actual_outcomes: List of actual binary outcomes (0 or 1).
        n_bins: Number of bins for ECE computation.

    Returns:
        CalibrationReport with all metrics populated.

    Raises:
        ValueError: If inputs have different lengths or are empty.
    """
    if len(predicted_probs) != len(actual_outcomes):
        raise ValueError("predicted_probs and actual_outcomes must have same length")
    if not predicted_probs:
        return CalibrationReport(
            brier=0.0, log_loss=0.0, ece=0.0, n_predictions=0, per_bin_stats=[]
        )

    # Compute individual scores
    brier_scores = [
        brier_score(p, a) for p, a in zip(predicted_probs, actual_outcomes)
    ]
    log_loss_scores = [
        log_loss_score(p, a) for p, a in zip(predicted_probs, actual_outcomes)
    ]

    avg_brier = sum(brier_scores) / len(brier_scores)
    avg_log_loss = sum(log_loss_scores) / len(log_loss_scores)

    ece_val, bin_stats = expected_calibration_error(
        predicted_probs, actual_outcomes, n_bins
    )

    return CalibrationReport(
        brier=round(avg_brier, 4),
        log_loss=round(avg_log_loss, 4),
        ece=ece_val,
        n_predictions=len(predicted_probs),
        per_bin_stats=bin_stats,
    )
