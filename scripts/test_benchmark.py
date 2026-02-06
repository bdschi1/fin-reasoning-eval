#!/usr/bin/env python3
"""
Test script for the Financial Reasoning Eval Benchmark

Verifies that all components work correctly.
"""

import sys
from pathlib import Path

# Add repo root for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_problem_generation():
    """Test that problem generators work correctly."""
    print("Testing problem generation...")

    from problems import Problem, ProblemSet, Difficulty
    from generators import (
        EarningsSurpriseGenerator,
        DCFSanityGenerator,
        AccountingRedFlagGenerator,
        CatalystIdentificationGenerator,
        FormulaAuditGenerator,
        FinancialStatementGenerator,
    )

    generators = [
        EarningsSurpriseGenerator(seed=42),
        DCFSanityGenerator(seed=42),
        AccountingRedFlagGenerator(seed=42),
        CatalystIdentificationGenerator(seed=42),
        FormulaAuditGenerator(seed=42),
        FinancialStatementGenerator(seed=42),
    ]

    for generator in generators:
        # Generate one problem at each difficulty
        for difficulty in Difficulty:
            problem = generator.generate_one(difficulty)
            assert problem.id, f"Problem ID should not be empty"
            assert problem.question, f"Question should not be empty"
            assert problem.correct_answer, f"Correct answer should not be empty"
            print(f"  ✓ {generator.category.value} - {difficulty.value}")

    print("  All problem generators working!\n")


def test_batch_generation():
    """Test batch problem generation."""
    print("Testing batch generation...")

    from generators import EarningsSurpriseGenerator

    generator = EarningsSurpriseGenerator(seed=42)
    problems = generator.generate_batch(10)

    assert len(problems) == 10, f"Expected 10 problems, got {len(problems)}"
    print(f"  ✓ Generated {len(problems)} problems")

    # Check difficulty distribution
    difficulties = [p.difficulty.value for p in problems]
    print(f"  Difficulty distribution: {difficulties}")
    print("  Batch generation working!\n")


def test_problem_set():
    """Test ProblemSet creation and serialization."""
    print("Testing ProblemSet...")

    from problems import ProblemSet, Problem, ProblemCategory, Difficulty, AnswerType, FinancialContext

    # Create a simple problem
    problem = Problem(
        id="test123",
        category=ProblemCategory.EARNINGS_SURPRISE,
        difficulty=Difficulty.MEDIUM,
        question="Test question?",
        context=FinancialContext(company_name="Test Corp"),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Test answer",
    )

    # Create problem set
    ps = ProblemSet(
        name="TestSet",
        description="Test problem set",
        problems=[problem]
    )

    assert ps.total_problems == 1
    print(f"  ✓ Created ProblemSet with {ps.total_problems} problem")

    # Test serialization
    data = ps.to_dict()
    assert 'problems' in data
    print("  ✓ Serialization working!")
    print("  ProblemSet working!\n")


def test_metrics():
    """Test evaluation metrics."""
    print("Testing metrics...")

    from evaluation import FinancialReasoningMetrics, compute_accuracy

    metrics = FinancialReasoningMetrics()

    # Add some predictions
    metrics.add_prediction(
        problem_id="1",
        predicted="A",
        reference="A",
        category="earnings_surprise",
        difficulty="easy"
    )
    metrics.add_prediction(
        problem_id="2",
        predicted="B",
        reference="A",
        category="earnings_surprise",
        difficulty="medium"
    )
    metrics.add_prediction(
        problem_id="3",
        predicted="C",
        reference="C",
        category="dcf_sanity",
        difficulty="hard"
    )

    results = metrics.compute()

    assert results.total_examples == 3
    assert results.overall_accuracy == 2/3
    print(f"  ✓ Overall accuracy: {results.overall_accuracy:.1%}")
    print(f"  ✓ Category accuracy: {results.category_accuracy}")
    print(f"  ✓ Difficulty accuracy: {results.difficulty_accuracy}")

    # Test simple accuracy function
    simple_acc = compute_accuracy(["A", "B", "C"], ["A", "A", "C"])
    assert simple_acc == 2/3
    print(f"  ✓ Simple accuracy: {simple_acc:.1%}")
    print("  Metrics working!\n")


def test_leaderboard():
    """Test leaderboard functionality."""
    print("Testing leaderboard...")

    from leaderboard import Leaderboard, LeaderboardEntry

    # Create temporary leaderboard
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        lb_path = os.path.join(tmpdir, "test_leaderboard.json")
        leaderboard = Leaderboard(storage_path=lb_path)

        # Add entries
        entry1 = LeaderboardEntry(
            model_name="TestModel1",
            overall_accuracy=0.85,
            total_examples=100,
            category_accuracy={"earnings": 0.90, "dcf": 0.80},
            difficulty_accuracy={"easy": 0.95, "hard": 0.75}
        )
        entry2 = LeaderboardEntry(
            model_name="TestModel2",
            overall_accuracy=0.80,
            total_examples=100,
        )

        leaderboard.add_entry(entry1)
        leaderboard.add_entry(entry2)

        assert len(leaderboard.entries) == 2
        assert leaderboard.entries[0].model_name == "TestModel1"  # Higher accuracy
        print(f"  ✓ Added {len(leaderboard.entries)} entries")
        print(f"  ✓ Top model: {leaderboard.entries[0].model_name}")

        # Test markdown output
        md = leaderboard.to_markdown_table()
        assert "TestModel1" in md
        print("  ✓ Markdown table generation working!")

    print("  Leaderboard working!\n")


def test_runner_config():
    """Test runner configuration."""
    print("Testing runner configuration...")

    from runners import RunnerConfig

    config = RunnerConfig(
        model_name="test-model",
        temperature=0.0,
        max_tokens=1024,
        system_prompt="You are a financial analyst."
    )

    assert config.model_name == "test-model"
    assert config.temperature == 0.0
    print("  ✓ RunnerConfig created successfully")
    print("  Runner configuration working!\n")


def test_full_pipeline():
    """Test the full pipeline from generation to evaluation."""
    print("Testing full pipeline...")

    from generators import EarningsSurpriseGenerator
    from evaluation import FinancialReasoningMetrics

    # Generate problems
    generator = EarningsSurpriseGenerator(seed=42)
    problems = generator.generate_batch(5)
    print(f"  ✓ Generated {len(problems)} problems")

    # Simulate model responses (correct answers)
    metrics = FinancialReasoningMetrics()
    for problem in problems:
        metrics.add_prediction(
            problem_id=problem.id,
            predicted=problem.correct_answer,  # Simulate perfect model
            reference=problem.correct_answer,
            category=problem.category.value,
            difficulty=problem.difficulty.value,
        )

    results = metrics.compute()
    assert results.overall_accuracy == 1.0, "Perfect model should have 100% accuracy"
    print(f"  ✓ Simulated evaluation: {results.overall_accuracy:.0%} accuracy")
    print("  Full pipeline working!\n")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Financial Reasoning Eval Benchmark - Test Suite")
    print("=" * 60 + "\n")

    tests = [
        test_problem_generation,
        test_batch_generation,
        test_problem_set,
        test_metrics,
        test_leaderboard,
        test_runner_config,
        test_full_pipeline,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ✗ FAILED: {e}\n")
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
