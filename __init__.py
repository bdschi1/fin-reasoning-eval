"""
Financial Reasoning Eval Benchmark

A comprehensive benchmark for evaluating LLM performance on financial reasoning tasks.
Contains 306 challenging problems across 7 categories:

- Earnings surprises analysis
- DCF sanity checks
- Accounting red flag detection
- Catalyst identification
- Formula auditing
- Financial statement analysis
- Risk assessment

Includes 60 advanced problems on alpha/beta separation, factor models,
portfolio construction, and quantitative finance concepts.

Quick Start:
    from evaluation import load_benchmark
    from runners.anthropic_runner import create_anthropic_runner

    # Load the benchmark
    dataset = load_benchmark(split="test")

    # Evaluate a model
    runner = create_anthropic_runner(model="claude-sonnet-4")

For more details, see:
- README.md - Full documentation
- runners/run_evaluation.py - Evaluation runner
- scripts/generate_dataset.py - Dataset generation
"""

__version__ = "1.3.0"

from problems import (
    Problem,
    ProblemSet,
    ProblemCategory,
    Difficulty,
    AnswerType,
    FinancialContext,
)

from evaluation import (
    FinancialReasoningDataset,
    FinancialReasoningMetrics,
    load_benchmark,
    compute_accuracy,
)

from runners import (
    BaseRunner,
    RunnerConfig,
    OpenAIRunner,
    AnthropicRunner,
    HuggingFaceRunner,
    run_benchmark,
    evaluate_model,
)

from leaderboard import (
    Leaderboard,
    LeaderboardEntry,
)

__all__ = [
    # Version
    '__version__',

    # Problems
    'Problem',
    'ProblemSet',
    'ProblemCategory',
    'Difficulty',
    'AnswerType',
    'FinancialContext',

    # Evaluation
    'FinancialReasoningDataset',
    'FinancialReasoningMetrics',
    'load_benchmark',
    'compute_accuracy',

    # Runners
    'BaseRunner',
    'RunnerConfig',
    'OpenAIRunner',
    'AnthropicRunner',
    'HuggingFaceRunner',
    'run_benchmark',
    'evaluate_model',

    # Leaderboard
    'Leaderboard',
    'LeaderboardEntry',
]
