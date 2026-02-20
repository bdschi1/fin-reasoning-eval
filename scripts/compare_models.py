#!/usr/bin/env python3
"""
Compare multiple models on the Financial Reasoning Eval Benchmark.

Runs each model on the same problem set and outputs a side-by-side comparison.

Usage:
    python compare_models.py --models claude-sonnet-4 gpt-4.1 ollama:llama3.2 --limit 20
    python compare_models.py --models claude-sonnet-4 ollama:mistral --split test
"""

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from runners.run_evaluation import evaluate_model


def compare_models(
    models: list[str],
    split: str = "test",
    limit: int | None = None,
    output_dir: str = "./results",
) -> dict:
    """Run evaluation for each model and produce a comparison."""
    all_results = {}

    for model in models:
        print(f"\n{'='*60}")
        print(f"  Evaluating: {model}")
        print(f"{'='*60}\n")

        try:
            result = evaluate_model(
                model=model,
                split=split,
                output_dir=output_dir,
                limit=limit,
            )
            all_results[model] = result
        except Exception as e:
            print(f"\n  ERROR evaluating {model}: {e}\n")
            all_results[model] = {"error": str(e)}

    # Build comparison table
    print("\n")
    print("=" * 80)
    print("  MODEL COMPARISON")
    print("=" * 80)

    # Header
    header = f"{'Metric':<35}"
    for model in models:
        short = model[:18]
        header += f" {short:>18}"
    print(header)
    print("-" * 80)

    # Overall accuracy
    row = f"{'Overall Accuracy':<35}"
    for model in models:
        r = all_results.get(model, {})
        if "error" in r:
            row += f" {'ERROR':>18}"
        else:
            acc = r.get("metrics", {}).get("overall_accuracy", 0)
            row += f" {acc:>17.1%}"
    print(row)

    # Reasoning quality
    row = f"{'Reasoning Quality (0-5)':<35}"
    for model in models:
        r = all_results.get(model, {})
        if "error" in r:
            row += f" {'ERROR':>18}"
        else:
            rq = r.get("metrics", {}).get("reasoning_quality")
            row += f" {rq:>17.2f}" if rq is not None else f" {'N/A':>18}"
    print(row)

    # Category accuracy
    all_categories = set()
    for r in all_results.values():
        if "error" not in r:
            all_categories.update(r.get("metrics", {}).get("category_accuracy", {}).keys())

    if all_categories:
        print(f"\n{'Category Accuracy':<35}")
        print("-" * 80)
        for cat in sorted(all_categories):
            row = f"  {cat:<33}"
            for model in models:
                r = all_results.get(model, {})
                if "error" in r:
                    row += f" {'ERROR':>18}"
                else:
                    acc = r.get("metrics", {}).get("category_accuracy", {}).get(cat, 0)
                    row += f" {acc:>17.1%}"
            print(row)

    # Difficulty accuracy
    all_diffs = set()
    for r in all_results.values():
        if "error" not in r:
            all_diffs.update(r.get("metrics", {}).get("difficulty_accuracy", {}).keys())

    if all_diffs:
        diff_order = ["easy", "medium", "hard", "expert"]
        sorted_diffs = sorted(all_diffs, key=lambda d: diff_order.index(d) if d in diff_order else 99)
        print(f"\n{'Difficulty Accuracy':<35}")
        print("-" * 80)
        for diff in sorted_diffs:
            row = f"  {diff:<33}"
            for model in models:
                r = all_results.get(model, {})
                if "error" in r:
                    row += f" {'ERROR':>18}"
                else:
                    acc = r.get("metrics", {}).get("difficulty_accuracy", {}).get(diff, 0)
                    row += f" {acc:>17.1%}"
            print(row)

    print("\n" + "=" * 80)

    # Save comparison
    comparison = {
        "models": models,
        "split": split,
        "limit": limit,
        "results": {},
    }
    for model in models:
        r = all_results.get(model, {})
        if "error" in r:
            comparison["results"][model] = {"error": r["error"]}
        else:
            comparison["results"][model] = r.get("metrics", {})

    comparison_path = os.path.join(output_dir, "comparison.json")
    with open(comparison_path, "w") as f:
        json.dump(comparison, f, indent=2)
    print(f"\nComparison saved to: {comparison_path}")

    return comparison


def main():
    parser = argparse.ArgumentParser(
        description="Compare multiple models on the Financial Reasoning Eval Benchmark"
    )
    parser.add_argument(
        "--models",
        type=str,
        nargs="+",
        required=True,
        help="Models to compare (e.g., claude-sonnet-4 gpt-4.1 ollama:llama3.2)",
    )
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["test", "validation"],
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of examples per model",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./results",
    )

    args = parser.parse_args()
    compare_models(
        models=args.models,
        split=args.split,
        limit=args.limit,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
