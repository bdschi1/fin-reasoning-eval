#!/usr/bin/env python3
"""
Run Evaluation Script for Financial Reasoning Eval Benchmark

Evaluates LLMs on the benchmark and generates results.

Usage:
    python run_evaluation.py --model gpt-4.1 --split test
    python run_evaluation.py --model claude-sonnet-4 --split test --categories dcf_sanity
    python run_evaluation.py --model o3 --split test --limit 50
    python run_evaluation.py --model llama-3.1-70b --use-api
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env', override=True)
except ImportError:
    pass  # dotenv not installed, rely on environment variables

from evaluation import (
    FinancialReasoningDataset,
    FinancialReasoningMetrics,
    load_benchmark,
)
from runners.base import BaseRunner, RunnerConfig


def get_runner(
    model: str,
    api_key: Optional[str] = None,
    use_api: bool = True,
    temperature: float = 0.0,
    max_tokens: int = 1024,
) -> BaseRunner:
    """
    Get the appropriate runner for the specified model.

    Args:
        model: Model name
        api_key: Optional API key
        use_api: Use API (for HuggingFace models)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        Configured runner instance
    """
    model_lower = model.lower()

    # System prompt for all models
    system_prompt = (
        "You are a financial analyst with expertise in evaluating financial models, "
        "analyzing earnings, and assessing investment opportunities. "
        "Provide clear, well-reasoned answers to financial questions. "
        "Always show your reasoning step by step before providing your final answer."
    )

    config = RunnerConfig(
        model_name=model,
        api_key=api_key,
        temperature=temperature,
        max_tokens=max_tokens,
        system_prompt=system_prompt,
    )

    # Determine which runner to use
    if model_lower.startswith("ollama:"):
        from runners.ollama_runner import OllamaRunner
        config.model_name = model[len("ollama:"):]
        return OllamaRunner(config)

    if model_lower.startswith("qwen3.5"):
        from runners.ollama_runner import OllamaRunner
        config.max_tokens = max(max_tokens, 8192)
        return OllamaRunner(config)

    if any(prefix in model_lower for prefix in ("gpt", "o1", "o3", "o4")):
        from runners.openai_runner import OpenAIRunner
        return OpenAIRunner(config)

    elif "claude" in model_lower:
        from runners.anthropic_runner import AnthropicRunner
        return AnthropicRunner(config)

    else:
        # Assume HuggingFace model
        from runners.huggingface_runner import HuggingFaceRunner
        return HuggingFaceRunner(config, use_api=use_api)


def run_benchmark(
    runner: BaseRunner,
    dataset: FinancialReasoningDataset,
    output_dir: str,
    save_predictions: bool = True,
    show_progress: bool = True,
    contamination_check: bool = False,
    auto_rubric: bool = False,
) -> tuple[dict, list[dict]]:
    """
    Run the benchmark evaluation.

    Args:
        runner: LLM runner instance
        dataset: Benchmark dataset
        output_dir: Directory for output files
        save_predictions: Save individual predictions
        show_progress: Show progress during evaluation
        contamination_check: Run contamination detection on each response.
            Non-blocking — logs warnings only.
        auto_rubric: When True, run RubricAutoGrader on every model response
            and attach rubric scores to each prediction record. Does not alter
            accuracy or other metrics.

    Returns:
        Tuple of (output dict, predictions list)
    """
    os.makedirs(output_dir, exist_ok=True)

    # Set up auto-rubric grader if requested.
    auto_grader = None
    if auto_rubric:
        from evaluation.rubric_auto_grader import RubricAutoGrader
        auto_grader = RubricAutoGrader()
        logging.getLogger(__name__).info("RubricAutoGrader enabled for this run.")

    # Set up contamination checker if requested.
    checker = None
    contamination_results = []
    if contamination_check:
        from evaluation.contamination import ContaminationChecker, _extract_problem_text
        checker = ContaminationChecker()
        hashes_path = Path(__file__).parent.parent / "data" / "problem_hashes.json"
        if hashes_path.exists():
            checker.load_hash_index(hashes_path)
        else:
            print("Contamination check: building hash index from current dataset...")
            idx = checker.build_hash_index(list(dataset))
            checker.save_hash_index(idx, hashes_path)

    metrics = FinancialReasoningMetrics()
    predictions = []
    total = len(dataset)

    print(f"\nEvaluating {runner.model_identifier} on {total} examples...")
    print("-" * 60)

    for i, example in enumerate(dataset):
        if show_progress:
            print(f"Processing {i + 1}/{total}: {example.category} ({example.difficulty})...", end='\r')

        # Format prompt
        prompt = runner.format_prompt(
            question=example.question,
            context=example.context,
            options=example.options,
        )

        # Generate response
        response = runner.generate(prompt)

        # Contamination check (non-blocking)
        if checker is not None:
            problem_text = _extract_problem_text(example.question, example.context)
            c_result = checker.check_response(
                problem_id=example.id,
                problem_text=problem_text,
                model_response=response.full_response or "",
            )
            contamination_results.append(c_result)

        # Record prediction
        prediction = {
            "id": example.id,
            "category": example.category,
            "difficulty": example.difficulty,
            "question": example.question,
            "predicted": response.answer,
            "correct_answer": example.correct_answer,
            "reasoning": response.reasoning,
            "full_response": response.full_response,
            "latency_ms": response.latency_ms,
            "tokens_used": response.tokens_used,
            "input_tokens": getattr(response, "input_tokens", 0),
            "output_tokens": getattr(response, "output_tokens", 0),
            "wall_time_s": getattr(response, "wall_time_s", response.latency_ms / 1000.0),
            "cost_usd": getattr(response, "cost_usd", None),
            "success": response.success,
            "error": response.error,
        }

        # Auto-rubric scoring (optional, non-blocking)
        if auto_grader is not None:
            try:
                auto_result = auto_grader.grade(
                    question=example.question,
                    context=example.context or "",
                    correct_answer=example.correct_answer or "",
                    model_response=response.full_response or response.answer or "",
                    problem_category=example.category,
                )
                prediction["auto_rubric"] = auto_result.rubric_result.to_dict()
                if auto_result.needs_human_review:
                    logging.getLogger(__name__).warning(
                        "Problem %s flagged for human rubric review "
                        "(low-confidence criteria: %s)",
                        example.id,
                        auto_result.low_confidence_criteria,
                    )
            except Exception as exc:  # noqa: BLE001
                logging.getLogger(__name__).warning(
                    "RubricAutoGrader failed for problem %s: %s", example.id, exc
                )
                prediction["auto_rubric"] = None

        predictions.append(prediction)

        # Add to metrics
        metrics.add_prediction(
            problem_id=example.id,
            predicted=response.answer,
            reference=example.correct_answer,
            category=example.category,
            difficulty=example.difficulty,
            reasoning=response.reasoning,
            latency_ms=response.latency_ms,
            answer_type=example.answer_type,
        )

    print("\n" + "-" * 60)

    # Compute metrics
    results = metrics.compute()
    print("\nResults:")
    print(results.summary())

    # Aggregate cost and token totals
    total_input_tokens = sum(p.get("input_tokens", 0) or 0 for p in predictions)
    total_output_tokens = sum(p.get("output_tokens", 0) or 0 for p in predictions)
    total_wall_time_s = sum(p.get("wall_time_s", 0.0) or 0.0 for p in predictions)
    cost_vals = [p.get("cost_usd") for p in predictions if p.get("cost_usd") is not None]
    total_cost_usd = round(sum(cost_vals), 4) if cost_vals else None

    # Prepare output
    output = {
        "model": runner.model_identifier,
        "timestamp": datetime.utcnow().isoformat(),
        "dataset_size": total,
        "metrics": results.to_dict(),
        "config": {
            "model_name": runner.config.model_name,
            "temperature": runner.config.temperature,
            "max_tokens": runner.config.max_tokens,
        },
        "judge_model": os.environ.get("JUDGE_MODEL", "claude-haiku-4-5-20251001"),
        "prompt_version": os.environ.get("PROMPT_VERSION", "v1.2.0"),
        "totals": {
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "wall_time_s": round(total_wall_time_s, 2),
            "cost_usd": total_cost_usd,
        },
    }

    # Save results
    results_path = os.path.join(output_dir, f"{runner.config.model_name.replace('/', '_')}_results.json")
    with open(results_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {results_path}")

    # Save predictions
    if save_predictions:
        predictions_path = os.path.join(output_dir, f"{runner.config.model_name.replace('/', '_')}_predictions.json")
        with open(predictions_path, 'w') as f:
            json.dump(predictions, f, indent=2)
        print(f"Predictions saved to: {predictions_path}")

    # Contamination report
    if checker is not None and contamination_results:
        report = checker.generate_report(contamination_results)
        flagged = report["flagged_count"]
        total_checked = report["total_checked"]
        rate = report["flagged_rate"]
        print(f"\nContamination check: {flagged}/{total_checked} flagged ({rate:.1%})")
        if flagged:
            print(f"  Flagged IDs: {report['flagged_problem_ids']}")
        contamination_path = os.path.join(
            output_dir,
            f"{runner.config.model_name.replace('/', '_')}_contamination.json",
        )
        with open(contamination_path, "w") as f:
            json.dump(report, f, indent=2)
        print(f"Contamination report saved to: {contamination_path}")
        output["contamination_report"] = report

    return output, predictions


def evaluate_model(
    model: str,
    split: str = "test",
    categories: Optional[list[str]] = None,
    difficulties: Optional[list[str]] = None,
    data_dir: Optional[str] = None,
    output_dir: str = "./results",
    api_key: Optional[str] = None,
    use_api: bool = True,
    temperature: float = 0.0,
    max_tokens: int = 1024,
    limit: Optional[int] = None,
    narrative_llm: bool = False,
    contamination_check: bool = False,
    auto_rubric: bool = False,
) -> dict:
    """
    Evaluate a model on the benchmark.

    Args:
        model: Model name (gpt-4.1, o3, claude-sonnet-4, llama-3.1-70b, etc.)
        split: Dataset split ('test', 'validation')
        categories: Filter to specific categories
        difficulties: Filter to specific difficulties
        data_dir: Custom data directory
        output_dir: Output directory for results
        api_key: Optional API key
        use_api: Use API for HuggingFace models
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate
        limit: Limit number of examples (for testing)
        narrative_llm: Use the evaluated model to generate a richer narrative summary
        contamination_check: Run contamination detection on model responses.
        auto_rubric: When True, run RubricAutoGrader on each response and attach
            rubric scores to every prediction record. Does not alter accuracy
            or other benchmark metrics.

    Returns:
        Evaluation results dictionary
    """
    # Load dataset
    print(f"Loading benchmark ({split} split)...")
    try:
        dataset = load_benchmark(
            split=split,
            data_dir=data_dir,
            categories=categories,
            difficulties=difficulties,
        )
    except FileNotFoundError:
        print("Benchmark data not found. Generating dataset first...")
        from scripts.generate_dataset import generate_benchmark_dataset
        generate_benchmark_dataset(
            num_problems=300,
            output_dir=data_dir or "./benchmark/data",
        )
        dataset = load_benchmark(
            split=split,
            data_dir=data_dir,
            categories=categories,
            difficulties=difficulties,
        )

    # Apply limit if specified
    if limit and limit < len(dataset):
        dataset._examples = dataset._examples[:limit]

    print(f"Loaded {len(dataset)} examples")
    stats = dataset.get_statistics()
    print(f"Categories: {stats['category_distribution']}")
    print(f"Difficulties: {stats['difficulty_distribution']}")

    # Get runner
    print(f"\nInitializing {model}...")
    runner = get_runner(
        model=model,
        api_key=api_key,
        use_api=use_api,
        temperature=temperature,
        max_tokens=max_tokens,
    )

    # Run evaluation
    results, predictions = run_benchmark(
        runner=runner,
        dataset=dataset,
        output_dir=output_dir,
        contamination_check=contamination_check,
        auto_rubric=auto_rubric,
    )

    # Generate narrative summary
    from evaluation.narrative import generate_narrative_summary

    narrative = generate_narrative_summary(
        output=results,
        predictions=predictions,
        runner=runner if narrative_llm else None,
        use_llm=narrative_llm,
    )
    narrative_path = os.path.join(
        output_dir,
        f"{runner.config.model_name.replace('/', '_')}_narrative.txt",
    )
    with open(narrative_path, "w") as f:
        f.write(narrative)
    print(f"Narrative summary saved to: {narrative_path}")

    return results


_CI_MODEL = "claude-haiku-4-5-20251001"
_CI_THRESHOLD = 0.50
_CI_LIMIT = 5


def _run_ci_mode(args) -> None:
    """Run a fast CI quality gate and exit with an appropriate exit code.

    Uses the validation split (not test) to preserve test-set integrity.
    Outputs machine-parseable JSON to stdout; all other logging goes to stderr.
    Exits 0 on pass, 1 on fail.
    """
    import sys

    print("CI mode: loading validation split...", file=sys.stderr)

    try:
        dataset = load_benchmark(
            split="validation",
            data_dir=args.data_dir if hasattr(args, "data_dir") else None,
        )
    except FileNotFoundError:
        print("CI mode: benchmark data not found. Generating dataset...", file=sys.stderr)
        from scripts.generate_dataset import generate_benchmark_dataset
        generate_benchmark_dataset(num_problems=300, output_dir="./benchmark/data")
        dataset = load_benchmark(split="validation")

    # Limit to first CI_LIMIT problems
    if len(dataset) > _CI_LIMIT:
        dataset._examples = dataset._examples[:_CI_LIMIT]

    n = len(dataset)
    print(f"CI mode: evaluating {n} problems with {_CI_MODEL}...", file=sys.stderr)

    runner = get_runner(
        model=_CI_MODEL,
        api_key=args.api_key if hasattr(args, "api_key") else None,
        use_api=True,
        temperature=0.0,
        max_tokens=512,
    )

    metrics = FinancialReasoningMetrics()
    for example in dataset:
        prompt = runner.format_prompt(
            question=example.question,
            context=example.context,
            options=example.options,
        )
        response = runner.generate(prompt)
        metrics.add_prediction(
            problem_id=example.id,
            predicted=response.answer,
            reference=example.correct_answer,
            category=example.category,
            difficulty=example.difficulty,
            reasoning=response.reasoning,
            latency_ms=response.latency_ms,
            answer_type=example.answer_type,
        )

    results = metrics.compute()
    accuracy = results.to_dict().get("overall_accuracy", 0.0)
    passed = accuracy >= _CI_THRESHOLD

    status_str = "CI PASS" if passed else "CI FAIL"
    output = {
        "ci_mode": True,
        "model": _CI_MODEL,
        "problems_evaluated": n,
        "overall_accuracy": round(accuracy, 4),
        "pass": passed,
        "threshold": _CI_THRESHOLD,
        "summary": (
            f"{n}/{n} problems evaluated. "
            f"Accuracy: {accuracy * 100:.1f}%. "
            f"{status_str}."
        ),
    }

    # JSON to stdout; nothing else
    print(json.dumps(output, indent=2))
    sys.exit(0 if passed else 1)


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate LLMs on the Financial Reasoning Eval Benchmark"
    )

    # Model selection
    parser.add_argument(
        "--model",
        type=str,
        required=True,
        help="Model to evaluate (gpt-4.1, o3, claude-sonnet-4, claude-opus-4, llama-3.1-70b, etc.)"
    )

    # Dataset options
    parser.add_argument(
        "--split",
        type=str,
        default="test",
        choices=["test", "validation", "finqa"],
        help="Dataset split to evaluate"
    )
    parser.add_argument(
        "--categories",
        type=str,
        nargs="+",
        help="Filter to specific categories"
    )
    parser.add_argument(
        "--difficulties",
        type=str,
        nargs="+",
        help="Filter to specific difficulties"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        help="Custom data directory"
    )

    # Output options
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./results",
        help="Output directory for results"
    )

    # Model configuration
    parser.add_argument(
        "--api-key",
        type=str,
        help="API key (defaults to environment variable)"
    )
    parser.add_argument(
        "--use-api",
        action="store_true",
        default=True,
        help="Use API for HuggingFace models"
    )
    parser.add_argument(
        "--no-api",
        action="store_true",
        help="Use local inference for HuggingFace models"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Maximum tokens to generate"
    )

    # Testing options
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of examples (for testing)"
    )

    # Narrative options
    parser.add_argument(
        "--narrative-llm",
        action="store_true",
        default=False,
        help="Use the evaluated model to generate a richer narrative summary (costs extra tokens)"
    )

    # Auto-rubric options
    parser.add_argument(
        "--auto-rubric",
        action="store_true",
        default=False,
        help=(
            "Run automated rubric scoring (RubricAutoGrader) on each model response "
            "using the AI judge. Attaches rubric scores to prediction records. "
            "Does not alter accuracy or other metrics. Requires ANTHROPIC_API_KEY."
        ),
    )

    # Contamination detection options
    parser.add_argument(
        "--contamination-check",
        action="store_true",
        default=False,
        help=(
            "Run benchmark contamination detection on model responses. "
            "Non-blocking — logs warnings and saves a contamination report alongside results."
        ),
    )
    parser.add_argument(
        "--build-hash-index",
        action="store_true",
        default=False,
        help=(
            "Build and save a SHA-256 hash index of all benchmark problems to "
            "data/problem_hashes.json, then exit without running evaluation."
        ),
    )

    # CI mode
    parser.add_argument(
        "--ci",
        action="store_true",
        default=False,
        help=(
            "CI mode: limits to 5 validation problems, uses Haiku judge, "
            "outputs JSON to stdout, exits 1 if accuracy < threshold."
        ),
    )

    args = parser.parse_args()

    # --ci: fast quality gate for CI pipelines
    if args.ci:
        _run_ci_mode(args)
        return

    # --build-hash-index: build index and exit without running evaluation.
    if args.build_hash_index:
        from evaluation.contamination import ContaminationChecker
        data_dir = args.data_dir
        print("Building hash index from benchmark problems...")
        dataset = load_benchmark(split=args.split, data_dir=data_dir)
        checker = ContaminationChecker()
        index = checker.build_hash_index(list(dataset))
        hashes_path = Path(__file__).parent.parent / "data" / "problem_hashes.json"
        checker.save_hash_index(index, hashes_path)
        print(f"Hash index saved: {hashes_path} ({len(index)} entries)")
        return

    # Run evaluation
    results = evaluate_model(
        model=args.model,
        split=args.split,
        categories=args.categories,
        difficulties=args.difficulties,
        data_dir=args.data_dir,
        output_dir=args.output_dir,
        api_key=args.api_key,
        use_api=not args.no_api,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        limit=args.limit,
        narrative_llm=args.narrative_llm,
        contamination_check=args.contamination_check,
        auto_rubric=args.auto_rubric,
    )

    print("\nEvaluation complete!")
    print(f"Overall Accuracy: {results['metrics']['overall_accuracy']:.1%}")


if __name__ == "__main__":
    main()
