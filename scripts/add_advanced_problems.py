#!/usr/bin/env python3
"""
Add advanced curated problems to the benchmark.

This script:
1. Loads existing benchmark problems
2. Generates 30 advanced concept problems
3. Generates 30 quant concept problems
4. Merges them into the benchmark
5. Regenerates train/validation/test splits
"""

import json
import random
import sys
from pathlib import Path

# Add parent for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from problems.schema import Problem, ProblemSet, ProblemCategory, Difficulty
from problems.advanced_problems import generate_advanced_problems
from problems.quant_concepts_problems import generate_quant_concept_problems


def main():
    data_dir = Path(__file__).parent.parent / "data"
    benchmark_file = data_dir / "financial_reasoning_benchmark.json"

    # Load existing benchmark
    print("Loading existing benchmark...")
    with open(benchmark_file, 'r') as f:
        existing_data = json.load(f)

    existing_problems = [Problem.from_dict(p) for p in existing_data['problems']]
    print(f"Existing problems: {len(existing_problems)}")

    # Generate advanced concept problems
    print("\nGenerating advanced concept problems...")
    advanced_problems = generate_advanced_problems()
    print(f"Advanced problems: {len(advanced_problems)}")

    # Generate quant concept problems
    print("\nGenerating quant concept problems...")
    quant_problems = generate_quant_concept_problems()
    print(f"Quant concept problems: {len(quant_problems)}")

    new_problems = advanced_problems + quant_problems
    print(f"Total new problems: {len(new_problems)}")

    # Check for ID conflicts
    existing_ids = {p.id for p in existing_problems}
    new_ids = {p.id for p in new_problems}
    conflicts = existing_ids & new_ids
    if conflicts:
        print(f"Warning: {len(conflicts)} ID conflicts found, regenerating IDs...")
        for p in new_problems:
            if p.id in existing_ids:
                p.id = p._generate_id() + "_paleo"

    # Merge
    all_problems = existing_problems + new_problems
    print(f"\nTotal problems after merge: {len(all_problems)}")

    # Create new ProblemSet
    merged_set = ProblemSet(
        name="FinancialReasoningEval",
        description="A benchmark for evaluating LLM financial reasoning capabilities. "
                    "Covers earnings analysis, DCF valuation, accounting quality, catalyst identification, "
                    "formula auditing, and financial statement analysis. "
                    "Includes advanced problems on alpha/beta separation, factor models, portfolio construction, "
                    "risk management, and quantitative finance concepts.",
        problems=all_problems,
        version="1.2.0"  # Version bump
    )

    # Print distribution
    print("\nCategory distribution:")
    for cat, count in sorted(merged_set.category_distribution.items()):
        print(f"  {cat}: {count}")

    print("\nDifficulty distribution:")
    for diff, count in sorted(merged_set.difficulty_distribution.items()):
        print(f"  {diff}: {count}")

    # Save main benchmark
    print(f"\nSaving merged benchmark to {benchmark_file}...")
    merged_set.to_json(str(benchmark_file))

    # Regenerate splits
    print("\nRegenerating train/validation/test splits...")
    random.seed(42)
    shuffled = all_problems.copy()
    random.shuffle(shuffled)

    # 70/15/15 split
    n = len(shuffled)
    train_end = int(0.7 * n)
    val_end = int(0.85 * n)

    train_problems = shuffled[:train_end]
    val_problems = shuffled[train_end:val_end]
    test_problems = shuffled[val_end:]

    print(f"  Train: {len(train_problems)} problems")
    print(f"  Validation: {len(val_problems)} problems")
    print(f"  Test: {len(test_problems)} problems")

    # Save splits
    train_set = ProblemSet(
        name="FinancialReasoningEval_train",
        description="Training split",
        problems=train_problems,
        version="1.2.0"
    )
    train_set.to_json(str(data_dir / "benchmark_train.json"))

    val_set = ProblemSet(
        name="FinancialReasoningEval_validation",
        description="Validation split",
        problems=val_problems,
        version="1.2.0"
    )
    val_set.to_json(str(data_dir / "benchmark_validation.json"))

    test_set = ProblemSet(
        name="FinancialReasoningEval_test",
        description="Test split",
        problems=test_problems,
        version="1.2.0"
    )
    test_set.to_json(str(data_dir / "benchmark_test.json"))

    # Update HuggingFace dataset info
    hf_info_file = data_dir / "huggingface" / "dataset_info.json"
    if hf_info_file.exists():
        with open(hf_info_file, 'r') as f:
            hf_info = json.load(f)

        hf_info['dataset_size'] = len(all_problems)
        hf_info['version'] = "1.1.0"
        hf_info['splits'] = {
            'train': len(train_problems),
            'validation': len(val_problems),
            'test': len(test_problems)
        }

        with open(hf_info_file, 'w') as f:
            json.dump(hf_info, f, indent=2)
        print(f"\nUpdated HuggingFace dataset info")

    print("\n" + "=" * 60)
    print("SUCCESS! Benchmark updated with 60 new curated problems")
    print(f"Total problems: {len(all_problems)}")
    print("=" * 60)


if __name__ == "__main__":
    main()
