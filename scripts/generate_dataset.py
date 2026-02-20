#!/usr/bin/env python3
"""
Generate the Financial Reasoning Eval Benchmark Dataset

This script generates 200-500 finance reasoning problems across categories:
- Earnings surprises
- DCF sanity checks
- Accounting red flags
- Catalyst identification
- Formula audit
- Financial statement analysis

Usage:
    python generate_dataset.py --output-dir ./data --num-problems 300
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from problems import ProblemSet, Difficulty
from generators import (
    EarningsSurpriseGenerator,
    DCFSanityGenerator,
    AccountingRedFlagGenerator,
    CatalystIdentificationGenerator,
    FormulaAuditGenerator,
    FinancialStatementGenerator,
)


def generate_benchmark_dataset(
    num_problems: int = 300,
    seed: int = 42,
    output_dir: str = "./data"
) -> ProblemSet:
    """
    Generate a complete benchmark dataset with specified number of problems.

    Args:
        num_problems: Total number of problems to generate
        seed: Random seed for reproducibility
        output_dir: Directory to save the dataset

    Returns:
        ProblemSet containing all generated problems
    """
    print(f"Generating {num_problems} financial reasoning problems...")

    # Distribution of problems by category (roughly equal)
    category_distribution = {
        "earnings_surprise": 0.18,
        "dcf_sanity": 0.17,
        "accounting_red_flag": 0.18,
        "catalyst_id": 0.15,
        "formula_audit": 0.15,
        "financial_statement": 0.17,
    }

    # Difficulty distribution
    difficulty_distribution = {
        Difficulty.EASY: 0.25,
        Difficulty.MEDIUM: 0.35,
        Difficulty.HARD: 0.30,
        Difficulty.EXPERT: 0.10
    }

    # Initialize generators
    generators = {
        "earnings_surprise": EarningsSurpriseGenerator(seed=seed),
        "dcf_sanity": DCFSanityGenerator(seed=seed + 1),
        "accounting_red_flag": AccountingRedFlagGenerator(seed=seed + 2),
        "catalyst_id": CatalystIdentificationGenerator(seed=seed + 3),
        "formula_audit": FormulaAuditGenerator(seed=seed + 4),
        "financial_statement": FinancialStatementGenerator(seed=seed + 5),
    }

    all_problems = []

    for category, weight in category_distribution.items():
        count = int(num_problems * weight)
        print(f"  Generating {count} {category} problems...")

        generator = generators[category]
        problems = generator.generate_batch(count, difficulty_distribution)
        all_problems.extend(problems)

        print(f"    Generated {len(problems)} problems")

    # Create problem set
    problem_set = ProblemSet(
        name="FinancialReasoningEval",
        description="A benchmark for evaluating LLM financial reasoning capabilities. "
                   "Covers earnings analysis, DCF valuation, accounting quality, "
                   "catalyst identification, formula auditing, and financial statement analysis.",
        problems=all_problems,
        version="1.0.0"
    )

    print(f"\nTotal problems generated: {problem_set.total_problems}")
    print(f"Category distribution: {problem_set.category_distribution}")
    print(f"Difficulty distribution: {problem_set.difficulty_distribution}")

    # Save to file
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "financial_reasoning_benchmark.json")
    problem_set.to_json(output_path)
    print(f"\nDataset saved to: {output_path}")

    return problem_set


def split_dataset(
    problem_set: ProblemSet,
    output_dir: str,
    train_ratio: float = 0.0,  # No training split for eval benchmark
    val_ratio: float = 0.2,
    test_ratio: float = 0.8
) -> dict:
    """
    Split dataset into train/val/test splits.

    For an evaluation benchmark, we primarily need test data,
    but include a small validation set for development.
    """
    import random

    problems = problem_set.problems.copy()
    random.shuffle(problems)

    total = len(problems)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    splits = {
        "train": problems[:train_end] if train_ratio > 0 else [],
        "validation": problems[train_end:val_end],
        "test": problems[val_end:]
    }

    # Save each split
    for split_name, split_problems in splits.items():
        if not split_problems:
            continue

        split_set = ProblemSet(
            name=f"{problem_set.name}_{split_name}",
            description=f"{split_name} split of {problem_set.name}",
            problems=split_problems,
            version=problem_set.version
        )
        output_path = os.path.join(output_dir, f"benchmark_{split_name}.json")
        split_set.to_json(output_path)
        print(f"Saved {split_name} split ({len(split_problems)} problems) to: {output_path}")

    return splits


def export_to_huggingface_format(problem_set: ProblemSet, output_dir: str):
    """
    Export dataset in HuggingFace datasets format.

    Creates JSONL files and a dataset_info.json for easy loading.
    """
    import random

    os.makedirs(output_dir, exist_ok=True)

    # Create HuggingFace-compatible records
    records = []
    for i, problem in enumerate(problem_set.problems):
        record = {
            "id": problem.id,
            "category": problem.category.value,
            "difficulty": problem.difficulty.value,
            "question": problem.question,
            "context": problem.format_prompt(include_options=False),
            "answer_type": problem.answer_type.value,
            "correct_answer": problem.correct_answer,
            "options": [
                {"id": opt.id, "text": opt.text}
                for opt in (problem.answer_options or [])
            ],
            "explanation": problem.explanation,
            "reasoning_steps": problem.reasoning_steps,
            "tags": problem.tags,
        }
        records.append(record)

    # Shuffle and split
    random.seed(42)
    random.shuffle(records)

    val_size = int(len(records) * 0.2)
    val_records = records[:val_size]
    test_records = records[val_size:]

    # Save as JSONL
    for split_name, split_records in [("validation", val_records), ("test", test_records)]:
        output_path = os.path.join(output_dir, f"{split_name}.jsonl")
        with open(output_path, 'w') as f:
            for record in split_records:
                f.write(json.dumps(record) + '\n')
        print(f"Exported {split_name} ({len(split_records)} records) to: {output_path}")

    # Create dataset info
    dataset_info = {
        "dataset_name": "financial-reasoning-eval",
        "description": problem_set.description,
        "version": problem_set.version,
        "created_at": datetime.utcnow().isoformat(),
        "total_examples": len(records),
        "splits": {
            "validation": len(val_records),
            "test": len(test_records)
        },
        "features": {
            "id": "string",
            "category": "string",
            "difficulty": "string",
            "question": "string",
            "context": "string",
            "answer_type": "string",
            "correct_answer": "string",
            "options": "list",
            "explanation": "string",
            "reasoning_steps": "list",
            "tags": "list"
        },
        "categories": list(problem_set.category_distribution.keys()),
        "difficulties": list(problem_set.difficulty_distribution.keys()),
        "license": "MIT",
        "citation": """@misc{financial-reasoning-eval,
  title={Financial Reasoning Eval Benchmark},
  year={2024},
  publisher={HuggingFace}
}"""
    }

    info_path = os.path.join(output_dir, "dataset_info.json")
    with open(info_path, 'w') as f:
        json.dump(dataset_info, f, indent=2)
    print(f"Dataset info saved to: {info_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate Financial Reasoning Eval Benchmark Dataset"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./benchmark/data",
        help="Directory to save the dataset"
    )
    parser.add_argument(
        "--num-problems",
        type=int,
        default=300,
        help="Number of problems to generate (200-500 recommended)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--huggingface-format",
        action="store_true",
        help="Also export in HuggingFace datasets format"
    )

    args = parser.parse_args()

    # Generate the dataset
    problem_set = generate_benchmark_dataset(
        num_problems=args.num_problems,
        seed=args.seed,
        output_dir=args.output_dir
    )

    # Split into train/val/test
    split_dataset(problem_set, args.output_dir)

    # Export to HuggingFace format if requested
    if args.huggingface_format:
        hf_output_dir = os.path.join(args.output_dir, "huggingface")
        export_to_huggingface_format(problem_set, hf_output_dir)

    print("\nDataset generation complete!")


if __name__ == "__main__":
    main()
