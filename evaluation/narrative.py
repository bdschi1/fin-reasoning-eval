"""
Narrative Summary Generator for Financial Reasoning Eval Benchmark

Generates a human-readable .txt summary of evaluation results.
Two modes:
  - Template-based (default): Pure Python, zero cost, always works
  - LLM-generated (opt-in): Uses the evaluated model for a richer narrative
"""

from collections import defaultdict
from typing import Optional

from .metrics import FinancialReasoningMetrics


# ---------------------------------------------------------------------------
# Correctness helper (reuses the metrics module's matching logic)
# ---------------------------------------------------------------------------

def _is_correct(predicted: str, correct_answer: str) -> bool:
    """Determine if a prediction is correct, reusing metrics logic."""
    m = FinancialReasoningMetrics()
    return m._check_text(predicted, correct_answer)


# ---------------------------------------------------------------------------
# Analysis helper
# ---------------------------------------------------------------------------

def _analyze_predictions(predictions: list[dict]) -> dict:
    """
    Analyze predictions and extract patterns for narrative generation.

    Returns a dict with keys:
        correct, incorrect, errors, by_category, by_difficulty,
        avg_latency_ms, total_tokens, strongest_categories,
        weakest_categories
    """
    correct = []
    incorrect = []
    api_errors = []

    for p in predictions:
        if not p.get("success", True):
            api_errors.append(p)
            continue
        if _is_correct(p.get("predicted", ""), p.get("correct_answer", "")):
            correct.append(p)
        else:
            incorrect.append(p)

    # Per-category stats
    by_category: dict[str, dict] = defaultdict(lambda: {
        "total": 0, "correct": 0, "incorrect": 0, "missed": [],
    })
    for p in predictions:
        if not p.get("success", True):
            continue
        cat = p.get("category", "unknown")
        by_category[cat]["total"] += 1
        if _is_correct(p.get("predicted", ""), p.get("correct_answer", "")):
            by_category[cat]["correct"] += 1
        else:
            by_category[cat]["incorrect"] += 1
            by_category[cat]["missed"].append(p)

    for cat, stats in by_category.items():
        stats["accuracy"] = (
            stats["correct"] / stats["total"] if stats["total"] else 0.0
        )

    # Per-difficulty stats
    by_difficulty: dict[str, dict] = defaultdict(lambda: {
        "total": 0, "correct": 0, "incorrect": 0,
    })
    for p in predictions:
        if not p.get("success", True):
            continue
        diff = p.get("difficulty", "unknown")
        by_difficulty[diff]["total"] += 1
        if _is_correct(p.get("predicted", ""), p.get("correct_answer", "")):
            by_difficulty[diff]["correct"] += 1
        else:
            by_difficulty[diff]["incorrect"] += 1

    for diff, stats in by_difficulty.items():
        stats["accuracy"] = (
            stats["correct"] / stats["total"] if stats["total"] else 0.0
        )

    # Latency / tokens
    latencies = [p.get("latency_ms", 0) for p in predictions if p.get("success", True)]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
    total_tokens = sum(p.get("tokens_used", 0) for p in predictions)

    # Strongest / weakest categories (sorted)
    cats_sorted = sorted(by_category.items(), key=lambda x: x[1]["accuracy"], reverse=True)
    strongest = [(c, s) for c, s in cats_sorted if s["accuracy"] >= 0.9]
    weakest = [(c, s) for c, s in cats_sorted if s["accuracy"] < 0.9]

    return {
        "correct": correct,
        "incorrect": incorrect,
        "api_errors": api_errors,
        "by_category": dict(by_category),
        "by_difficulty": dict(by_difficulty),
        "avg_latency_ms": avg_latency,
        "total_tokens": total_tokens,
        "strongest_categories": strongest,
        "weakest_categories": weakest,
    }


# ---------------------------------------------------------------------------
# Template-based narrative
# ---------------------------------------------------------------------------

_SEP = "=" * 60

def _generate_template_narrative(output: dict, analysis: dict) -> str:
    """Generate a narrative summary using pure Python templates."""
    metrics = output.get("metrics", {})
    config = output.get("config", {})
    model = output.get("model", "unknown")
    timestamp = output.get("timestamp", "")
    dataset_size = output.get("dataset_size", 0)

    overall_acc = metrics.get("overall_accuracy", 0.0)
    correct_count = metrics.get("correct_count", 0)
    total = metrics.get("total_examples", dataset_size)
    cat_acc = metrics.get("category_accuracy", {})
    diff_acc = metrics.get("difficulty_accuracy", {})

    incorrect = analysis["incorrect"]
    api_errors = analysis["api_errors"]
    by_cat = analysis["by_category"]
    by_diff = analysis["by_difficulty"]

    lines: list[str] = []

    # ── Header ────────────────────────────────────────────────
    lines.append(_SEP)
    lines.append("FINANCIAL REASONING EVAL - NARRATIVE SUMMARY")
    lines.append(_SEP)
    lines.append(f"Model:     {model}")
    lines.append(f"Date:      {timestamp}")
    lines.append(f"Dataset:   {total} examples")
    lines.append(f"Config:    temperature={config.get('temperature', 0.0)}, "
                 f"max_tokens={config.get('max_tokens', 1024)}")
    lines.append("")

    # ── Headline ──────────────────────────────────────────────
    lines.append(_SEP)
    lines.append("HEADLINE")
    lines.append(_SEP)

    perfect_cats = [c for c, s in by_cat.items() if s["accuracy"] == 1.0]
    weak_cats = sorted(
        [(c, s) for c, s in by_cat.items() if s["accuracy"] < 1.0],
        key=lambda x: x[1]["accuracy"],
    )

    headline = f"{model} scored {overall_acc:.1%} overall ({correct_count}/{total})"
    if perfect_cats:
        headline += f", with perfect marks in {', '.join(perfect_cats)}"
    headline += "."

    if weak_cats:
        worst_cat, worst_stats = weak_cats[0]
        headline += (
            f" Notable weakness in {worst_cat} "
            f"({worst_stats['accuracy']:.0%})."
        )

    lines.append(headline)
    lines.append("")

    # ── Strengths ─────────────────────────────────────────────
    lines.append(_SEP)
    lines.append("WHAT THE MODEL GOT RIGHT")
    lines.append(_SEP)

    if analysis["correct"]:
        strong = analysis["strongest_categories"]
        if strong:
            lines.append(
                f"The model demonstrated strong performance (>=90%) in "
                f"{len(strong)} of {len(by_cat)} categories:"
            )
            for cat, stats in strong:
                lines.append(
                    f"  - {cat}: {stats['accuracy']:.0%} "
                    f"({stats['correct']}/{stats['total']})"
                )
        else:
            lines.append("No category reached 90% accuracy.")

        # Highlight hardest correct answers
        hard_correct = [
            p for p in analysis["correct"]
            if p.get("difficulty") in ("hard", "expert")
        ]
        if hard_correct:
            lines.append("")
            lines.append(
                f"The model correctly answered {len(hard_correct)} "
                f"hard/expert-level questions."
            )
    else:
        lines.append("The model did not answer any questions correctly.")

    lines.append("")

    # ── Misses ────────────────────────────────────────────────
    lines.append(_SEP)
    lines.append("WHAT THE MODEL MISSED")
    lines.append(_SEP)

    if not incorrect:
        lines.append(
            "The model answered all questions correctly. "
            "No errors to analyze."
        )
    else:
        lines.append(
            f"The model answered {len(incorrect)} question(s) incorrectly "
            f"out of {total}."
        )
        lines.append("")

        for p in incorrect:
            pid = p.get("id", "?")[:16]
            cat = p.get("category", "?")
            diff = p.get("difficulty", "?")
            question_snippet = (p.get("question", "")[:150] + "...") if len(p.get("question", "")) > 150 else p.get("question", "")
            predicted_snippet = (p.get("predicted", "")[:120] + "...") if len(p.get("predicted", "")) > 120 else p.get("predicted", "")
            correct_snippet = (p.get("correct_answer", "")[:120] + "...") if len(p.get("correct_answer", "")) > 120 else p.get("correct_answer", "")

            lines.append(f"  [{pid}] {cat} ({diff})")
            lines.append(f"    Q: {question_snippet}")
            lines.append(f"    Model answered: {predicted_snippet}")
            lines.append(f"    Correct answer: {correct_snippet}")
            lines.append("")

    lines.append("")

    # ── Error patterns ────────────────────────────────────────
    lines.append(_SEP)
    lines.append("ERROR PATTERNS")
    lines.append(_SEP)

    if not incorrect:
        lines.append("No errors detected.")
    else:
        # Category concentration
        cats_with_misses = [
            (c, s) for c, s in by_cat.items() if s["incorrect"] > 0
        ]
        cats_with_misses.sort(key=lambda x: x[1]["incorrect"], reverse=True)

        lines.append("Category concentration:")
        for cat, stats in cats_with_misses:
            miss_rate = stats["incorrect"] / stats["total"] * 100 if stats["total"] else 0
            lines.append(
                f"  - {cat}: {stats['incorrect']} of {stats['total']} "
                f"missed ({miss_rate:.0f}%)"
            )

        lines.append("")
        lines.append("Difficulty distribution of errors:")
        for diff in ("easy", "medium", "hard", "expert"):
            if diff in by_diff:
                lines.append(
                    f"  - {diff}: {by_diff[diff]['incorrect']} missed"
                )

        # Pattern description
        if cats_with_misses:
            top_miss_cat, top_miss_stats = cats_with_misses[0]
            if top_miss_stats["incorrect"] >= 2:
                lines.append("")
                lines.append(
                    f"Most errors concentrated in {top_miss_cat} "
                    f"({top_miss_stats['incorrect']} misses), suggesting "
                    f"the model may struggle with this problem type."
                )

    lines.append("")

    # ── Performance details ───────────────────────────────────
    lines.append(_SEP)
    lines.append("PERFORMANCE DETAILS")
    lines.append(_SEP)

    lines.append("Category Breakdown:")
    max_cat_len = max((len(c) for c in cat_acc), default=0)
    for cat in sorted(cat_acc.keys()):
        acc = cat_acc[cat]
        cat_stats = by_cat.get(cat, {})
        c = cat_stats.get("correct", 0)
        t = cat_stats.get("total", 0)
        lines.append(f"  {cat:<{max_cat_len}}  {acc:.0%}  ({c}/{t})")

    lines.append("")
    lines.append("Difficulty Breakdown:")
    for diff in ("easy", "medium", "hard", "expert"):
        if diff in diff_acc:
            ds = by_diff.get(diff, {})
            c = ds.get("correct", 0)
            t = ds.get("total", 0)
            lines.append(f"  {diff:<8}  {diff_acc[diff]:.0%}  ({c}/{t})")

    lines.append("")
    lines.append(f"Average latency: {analysis['avg_latency_ms']:.0f}ms per question")
    lines.append(f"Total tokens:    {analysis['total_tokens']}")
    lines.append("")

    # ── API errors ────────────────────────────────────────────
    lines.append(_SEP)
    lines.append("API ERRORS")
    lines.append(_SEP)

    if not api_errors:
        lines.append("No API errors encountered.")
    else:
        lines.append(f"{len(api_errors)} question(s) failed with API errors:")
        for p in api_errors:
            pid = p.get("id", "?")[:16]
            err = (p.get("error", "unknown")[:100] + "...") if len(p.get("error", "")) > 100 else p.get("error", "unknown")
            lines.append(f"  - [{pid}] {err}")

    lines.append("")
    lines.append(_SEP)
    lines.append("Generated by fin-reasoning-eval (template mode)")
    lines.append(_SEP)

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# LLM-based narrative
# ---------------------------------------------------------------------------

def _build_llm_prompt(output: dict, analysis: dict) -> str:
    """Build the prompt for LLM-based narrative generation."""
    metrics = output.get("metrics", {})
    model = output.get("model", "unknown")
    cat_acc = metrics.get("category_accuracy", {})
    diff_acc = metrics.get("difficulty_accuracy", {})

    parts = []
    parts.append(
        "You are a financial evaluation analyst. You have just completed an "
        "evaluation of an LLM on the Financial Reasoning Eval Benchmark. "
        "Write a clear, readable narrative summary of the results suitable "
        "for a technical audience."
    )
    parts.append("")

    parts.append("## Evaluation Summary")
    parts.append(f"- Model: {model}")
    parts.append(f"- Dataset: {metrics.get('total_examples', 0)} examples")
    parts.append(
        f"- Overall Accuracy: {metrics.get('overall_accuracy', 0):.1%} "
        f"({metrics.get('correct_count', 0)}/{metrics.get('total_examples', 0)})"
    )
    parts.append("")

    parts.append("## Accuracy by Category")
    for cat in sorted(cat_acc.keys()):
        parts.append(f"- {cat}: {cat_acc[cat]:.1%}")
    parts.append("")

    parts.append("## Accuracy by Difficulty")
    for diff in ("easy", "medium", "hard", "expert"):
        if diff in diff_acc:
            parts.append(f"- {diff}: {diff_acc[diff]:.1%}")
    parts.append("")

    # Include incorrect predictions (capped at 20, truncated)
    incorrect = analysis["incorrect"]
    parts.append(f"## Incorrect Predictions ({len(incorrect)} total)")
    for p in incorrect[:20]:
        pid = p.get("id", "?")[:16]
        cat = p.get("category", "?")
        diff = p.get("difficulty", "?")
        q = p.get("question", "")[:200]
        pred = p.get("predicted", "")[:150]
        corr = p.get("correct_answer", "")[:150]
        parts.append(f"- ID {pid} ({cat}, {diff}):")
        parts.append(f"  Question: {q}")
        parts.append(f"  Model answered: {pred}")
        parts.append(f"  Correct answer: {corr}")
    if len(incorrect) > 20:
        parts.append(f"  ... and {len(incorrect) - 20} more")
    parts.append("")

    api_errors = analysis["api_errors"]
    parts.append(f"## API Errors: {'None' if not api_errors else len(api_errors)}")
    parts.append("")

    parts.append("## Instructions")
    parts.append("Write a narrative summary with these sections:")
    parts.append("1. HEADLINE - A 2-3 sentence overview of performance")
    parts.append("2. STRENGTHS - What the model did well, citing specific categories and examples")
    parts.append("3. WEAKNESSES - What the model missed and why, citing specific questions")
    parts.append("4. ERROR PATTERNS - Any patterns in the mistakes (category clusters, difficulty trends)")
    parts.append("5. RECOMMENDATIONS - What types of training data or problems would help improve this model")
    parts.append("")
    parts.append("Keep the tone professional and analytical. Be specific with numbers and examples.")
    parts.append("Do not use markdown formatting — write in plain text suitable for a .txt file.")

    prompt = "\n".join(parts)
    # Cap prompt length for models with small context windows
    if len(prompt) > 6000:
        prompt = prompt[:6000] + "\n\n[Truncated for context length]"
    return prompt


def _generate_llm_narrative(
    output: dict,
    analysis: dict,
    runner,
) -> str:
    """Generate a narrative summary using the LLM runner."""
    prompt = _build_llm_prompt(output, analysis)

    # Temporarily increase max_tokens for narrative generation
    original_max_tokens = runner.config.max_tokens
    runner.config.max_tokens = max(2048, original_max_tokens)

    try:
        response = runner.generate(prompt)
    finally:
        runner.config.max_tokens = original_max_tokens

    if not response.success or not response.full_response.strip():
        raise RuntimeError(response.error or "Empty response from LLM")

    model = output.get("model", "unknown")
    header = (
        f"{_SEP}\n"
        f"FINANCIAL REASONING EVAL - NARRATIVE SUMMARY\n"
        f"{_SEP}\n"
        f"Model: {model}\n"
        f"Date:  {output.get('timestamp', '')}\n"
        f"\n"
    )
    footer = (
        f"\n\n{_SEP}\n"
        f"Generated by fin-reasoning-eval (LLM mode)\n"
        f"{_SEP}"
    )

    return header + response.full_response.strip() + footer


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate_narrative_summary(
    output: dict,
    predictions: list[dict],
    runner=None,
    use_llm: bool = False,
) -> str:
    """
    Generate a narrative summary of evaluation results.

    Args:
        output: The output dict from run_benchmark() containing
                model, timestamp, dataset_size, metrics, config.
        predictions: List of prediction dicts from the evaluation.
        runner: Optional BaseRunner instance. Required when use_llm=True.
        use_llm: If True, use the LLM for a richer narrative.
                 If False (default), use template-based generation.

    Returns:
        The narrative summary as a plain-text string.
    """
    if not predictions:
        return (
            f"{_SEP}\n"
            f"FINANCIAL REASONING EVAL - NARRATIVE SUMMARY\n"
            f"{_SEP}\n"
            f"Model: {output.get('model', 'unknown')}\n\n"
            f"Evaluation produced no predictions. No analysis available.\n"
            f"{_SEP}"
        )

    analysis = _analyze_predictions(predictions)

    if use_llm:
        if runner is None:
            raise ValueError("runner is required when use_llm=True")
        try:
            return _generate_llm_narrative(output, analysis, runner)
        except Exception as e:
            # Fall back to template mode
            narrative = _generate_template_narrative(output, analysis)
            narrative += (
                f"\n\nNote: LLM narrative generation failed ({e}). "
                f"This summary was generated using the template fallback."
            )
            return narrative

    return _generate_template_narrative(output, analysis)
