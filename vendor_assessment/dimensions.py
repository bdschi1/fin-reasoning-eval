from __future__ import annotations

from .scorecard import AssessmentDimension, DimensionScore, ScoreLevel

# Default weights (sum to 1.0)
DEFAULT_WEIGHTS: dict[AssessmentDimension, float] = {
    AssessmentDimension.ACCURACY: 0.30,
    AssessmentDimension.DOMAIN_EXPERTISE: 0.25,
    AssessmentDimension.SAFETY_ROBUSTNESS: 0.15,
    AssessmentDimension.CONSISTENCY: 0.10,
    AssessmentDimension.COST_EFFICIENCY: 0.10,
    AssessmentDimension.LATENCY: 0.10,
}


def score_to_level(score: float) -> ScoreLevel:
    if score >= 90:
        return ScoreLevel.EXCELLENT
    if score >= 75:
        return ScoreLevel.STRONG
    if score >= 60:
        return ScoreLevel.ADEQUATE
    if score >= 40:
        return ScoreLevel.BELOW_EXPECTATIONS
    return ScoreLevel.POOR


def score_accuracy(
    overall_accuracy: float,
    category_accuracies: dict[str, float] | None = None,
) -> DimensionScore:
    """Score accuracy dimension (0-100 scale)."""
    score = overall_accuracy * 100  # Convert from 0-1 to 0-100
    evidence = [f"Overall accuracy: {overall_accuracy:.1%}"]
    if category_accuracies:
        for cat, acc in sorted(category_accuracies.items()):
            evidence.append(f"  {cat}: {acc:.1%}")
    return DimensionScore(
        dimension=AssessmentDimension.ACCURACY,
        score=score,
        weight=DEFAULT_WEIGHTS[AssessmentDimension.ACCURACY],
        level=score_to_level(score),
        evidence=evidence,
    )


def score_latency(
    avg_latency_ms: float,
    p95_latency_ms: float | None = None,
) -> DimensionScore:
    """Score latency (lower is better). <500ms=100, >5000ms=0."""
    if avg_latency_ms <= 500:
        score = 100.0
    elif avg_latency_ms >= 5000:
        score = 0.0
    else:
        score = 100 * (1 - (avg_latency_ms - 500) / 4500)
    evidence = [f"Avg latency: {avg_latency_ms:.0f}ms"]
    if p95_latency_ms:
        evidence.append(f"P95 latency: {p95_latency_ms:.0f}ms")
    return DimensionScore(
        dimension=AssessmentDimension.LATENCY,
        score=score,
        weight=DEFAULT_WEIGHTS[AssessmentDimension.LATENCY],
        level=score_to_level(score),
        evidence=evidence,
    )


def score_cost_efficiency(
    cost_per_correct: float | None = None,
    cost_per_1k_tokens: float | None = None,
) -> DimensionScore:
    """Score cost efficiency. Lower cost per correct answer = higher score."""
    evidence: list[str] = []
    if cost_per_correct is not None:
        # $0.001 per correct = 100, $0.10 per correct = 0
        if cost_per_correct <= 0.001:
            score = 100.0
        elif cost_per_correct >= 0.10:
            score = 0.0
        else:
            score = 100 * (1 - (cost_per_correct - 0.001) / 0.099)
        evidence.append(
            f"Cost per correct answer: ${cost_per_correct:.4f}"
        )
    elif cost_per_1k_tokens is not None:
        # $0.25/1k = 100, $30/1k = 0
        if cost_per_1k_tokens <= 0.25:
            score = 100.0
        elif cost_per_1k_tokens >= 30.0:
            score = 0.0
        else:
            score = 100 * (1 - (cost_per_1k_tokens - 0.25) / 29.75)
        evidence.append(
            f"Cost per 1K tokens: ${cost_per_1k_tokens:.3f}"
        )
    else:
        score = 50.0  # Unknown cost
        evidence.append("Cost data not available")
    return DimensionScore(
        dimension=AssessmentDimension.COST_EFFICIENCY,
        score=score,
        weight=DEFAULT_WEIGHTS[AssessmentDimension.COST_EFFICIENCY],
        level=score_to_level(score),
        evidence=evidence,
    )


def score_safety(
    adversarial_accuracy: float | None = None,
    hallucination_rate: float | None = None,
) -> DimensionScore:
    """Score safety/robustness."""
    evidence: list[str] = []
    scores: list[float] = []
    if adversarial_accuracy is not None:
        scores.append(adversarial_accuracy * 100)
        evidence.append(
            f"Adversarial accuracy: {adversarial_accuracy:.1%}"
        )
    if hallucination_rate is not None:
        scores.append((1 - hallucination_rate) * 100)
        evidence.append(
            f"Hallucination rate: {hallucination_rate:.1%}"
        )
    score = sum(scores) / len(scores) if scores else 50.0
    if not evidence:
        evidence.append("Safety data not available")
    return DimensionScore(
        dimension=AssessmentDimension.SAFETY_ROBUSTNESS,
        score=score,
        weight=DEFAULT_WEIGHTS[AssessmentDimension.SAFETY_ROBUSTNESS],
        level=score_to_level(score),
        evidence=evidence,
    )


def score_domain_expertise(
    hard_accuracy: float | None = None,
    expert_accuracy: float | None = None,
    category_strengths: dict[str, float] | None = None,
) -> DimensionScore:
    """Score domain expertise (performance on hard/expert questions)."""
    evidence: list[str] = []
    scores: list[float] = []
    if hard_accuracy is not None:
        scores.append(hard_accuracy * 100)
        evidence.append(
            f"Hard question accuracy: {hard_accuracy:.1%}"
        )
    if expert_accuracy is not None:
        scores.append(expert_accuracy * 100)
        evidence.append(
            f"Expert question accuracy: {expert_accuracy:.1%}"
        )
    if category_strengths:
        top_cats = sorted(
            category_strengths.items(), key=lambda x: -x[1],
        )[:3]
        for cat, acc in top_cats:
            evidence.append(f"  Top domain: {cat} ({acc:.1%})")
    score = sum(scores) / len(scores) if scores else 50.0
    return DimensionScore(
        dimension=AssessmentDimension.DOMAIN_EXPERTISE,
        score=score,
        weight=DEFAULT_WEIGHTS[AssessmentDimension.DOMAIN_EXPERTISE],
        level=score_to_level(score),
        evidence=evidence,
    )


def score_consistency(
    score_variance: float | None = None,
    n_runs: int = 1,
) -> DimensionScore:
    """Score consistency across multiple runs. Lower variance = higher."""
    if score_variance is not None and n_runs > 1:
        # Variance of 0 = 100, variance of 0.1 = 0
        if score_variance <= 0:
            score = 100.0
        elif score_variance >= 0.1:
            score = 0.0
        else:
            score = 100 * (1 - score_variance / 0.1)
        evidence = [
            f"Score variance: {score_variance:.4f} "
            f"across {n_runs} runs"
        ]
    else:
        score = 50.0  # Single run, can't assess consistency
        evidence = ["Single run — consistency not assessed"]
    return DimensionScore(
        dimension=AssessmentDimension.CONSISTENCY,
        score=score,
        weight=DEFAULT_WEIGHTS[AssessmentDimension.CONSISTENCY],
        level=score_to_level(score),
        evidence=evidence,
    )
