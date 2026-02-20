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
) -> tuple[dict, list[dict]]:
    """
    Run the benchmark evaluation.

    Args:
        runner: LLM runner instance
        dataset: Benchmark dataset
        output_dir: Directory for output files
        save_predictions: Save individual predictions
        show_progress: Show progress during evaluation

    Returns:
        Tuple of (output dict, predictions list)
    """
    os.makedirs(output_dir, exist_ok=True)

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
            "success": response.success,
            "error": response.error,
        }
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
        choices=["test", "validation"],
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

    args = parser.parse_args()

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
    )

    print("\nEvaluation complete!")
    print(f"Overall Accuracy: {results['metrics']['overall_accuracy']:.1%}")


if __name__ == "__main__":
    main()
