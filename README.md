# Financial Reasoning Eval Benchmark

A comprehensive benchmark for evaluating LLM performance on financial reasoning tasks. Designed to test domain expertise in finance, accounting, investment analysis, and quantitative concepts.

## Overview

This benchmark contains **306 curated finance reasoning problems** across seven categories, emphasizing challenging problems that require deep financial knowledge and analytical reasoning.

| Category | Count | Description | Example Tasks |
|----------|-------|-------------|---------------|
| **Earnings Surprises** | 49 | Analyzing quarterly earnings | Beat/miss calculations, guidance analysis, earnings drift |
| **DCF Sanity Checks** | 49 | Validating valuation models | Terminal growth, WACC consistency, scenario analysis |
| **Accounting Red Flags** | 47 | Detecting accounting issues | Revenue recognition, accrual anomalies, cash flow divergence |
| **Catalyst Identification** | 54 | Identifying stock catalysts | Event timing, risk isolation, crowding analysis |
| **Formula Audit** | 46 | Finding model errors | Beta neutrality pitfalls, factor exposure, estimation error |
| **Financial Statement** | 51 | Analyzing financials | Ratio analysis, margin trends, working capital |
| **Risk Assessment** | 10 | Evaluating portfolio risk | Liquidity risk, volatility clustering, tail risk |

### Difficulty Distribution

| Difficulty | Count | Percentage | Description |
|------------|-------|------------|-------------|
| **Hard** | 141 | 46% | Subtle issues requiring careful analysis |
| **Medium** | 111 | 36% | Requires solid financial knowledge |
| **Expert** | 44 | 14% | Complex, multi-factor problems |
| **Easy** | 10 | 3% | Baseline problems for sanity checks |

### Advanced Problem Types

The benchmark includes 60 curated advanced problems covering:
- **Alpha/Beta Separation** - Distinguishing idiosyncratic vs. systematic returns
- **Factor Models** - Multi-factor attribution, momentum, volatility factors
- **Position Sizing** - Risk budgeting, conviction-based sizing
- **Risk Decomposition** - Tracking error, beta-neutrality pitfalls
- **Portfolio Construction** - Mean-variance optimization, constraints, capacity
- **Performance Attribution** - Drawdown analysis, process vs. outcome evaluation

## Quick Start

### Using `run.sh` (recommended)

```bash
chmod +x run.sh

./run.sh setup                            # Create venv & install deps
./run.sh test                             # Verify everything works
./run.sh eval claude-sonnet-4 test 50     # Evaluate a model
```

| Command | What It Does |
|---------|-------------|
| `./run.sh` | Full pipeline: setup → tests → model evaluation |
| `./run.sh setup` | Creates venv, installs deps, checks `.env` config |
| `./run.sh test` | Runs all 7 test suites (generators, metrics, leaderboard, pipeline) |
| `./run.sh generate [N]` | Regenerates N problems + merges advanced curated problems + HuggingFace export |
| `./run.sh eval MODEL [SPLIT] [LIMIT]` | Evaluates any supported model against the benchmark |
| `./run.sh leaderboard` | Launches the Gradio web UI |
| `./run.sh help` | Shows usage, examples, and all supported models |

### Manual Installation

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Evaluation

```bash
# Evaluate Claude Sonnet 4
python3 runners/run_evaluation.py --model claude-sonnet-4 --limit 50

# Evaluate with full test set
python3 runners/run_evaluation.py --model claude-sonnet-4

# Evaluate OpenAI models
python3 runners/run_evaluation.py --model gpt-4.1 --split test
python3 runners/run_evaluation.py --model o3 --split test --limit 50

# Filter by category or difficulty
python3 runners/run_evaluation.py --model claude-sonnet-4 --difficulties hard expert --limit 10
    --categories dcf_sanity_check accounting_red_flag \
    --difficulties hard expert
```

### Python API

```python
from evaluation import load_benchmark
from runners.anthropic_runner import create_anthropic_runner

# Load the benchmark
dataset = load_benchmark(split="test")
print(f"Loaded {len(dataset)} problems")

# Filter by category
dcf_problems = load_benchmark(
    split="test",
    categories=["dcf_sanity_check"]
)

# Create a runner and evaluate
runner = create_anthropic_runner(model="claude-sonnet-4")
```

## Dataset Format

### Problem Schema

```json
{
  "id": "qc_market_001",
  "category": "formula_audit",
  "difficulty": "hard",
  "question": "A return predictor has strong out-of-sample accuracy but trades in securities with large bid-ask spreads...",
  "context": {
    "company_name": "Signal Analysis",
    "sector": "Quantitative",
    "model_assumptions": {...}
  },
  "answer_type": "multiple_choice",
  "correct_answer": "Transaction costs can exceed expected returns...",
  "answer_options": [
    {"id": "A", "text": "...", "is_correct": false},
    {"id": "B", "text": "...", "is_correct": true},
    ...
  ],
  "explanation": "Expected gross return from signal = IC * volatility...",
  "reasoning_steps": ["Step 1...", "Step 2...", ...],
  "tags": ["transaction-costs", "market-microstructure", "quant-concepts"]
}
```

### HuggingFace Dataset

```python
from datasets import load_dataset

# Load from local files
dataset = load_dataset(
    'json',
    data_files={'test': 'data/huggingface/test.jsonl'}
)

# Or load from Hub (after publishing)
dataset = load_dataset('your-org/financial-reasoning-eval')
```

## Evaluation Metrics

### Primary Metrics

- **Overall Accuracy** - Percentage of correct answers
- **Category Accuracy** - Breakdown by problem category
- **Difficulty Accuracy** - Breakdown by difficulty level

### Additional Metrics

- **Reasoning Quality** - Assessment of step-by-step reasoning
- **Latency** - Response time per problem
- **Token Usage** - Tokens consumed per evaluation

## Sample Results

### Claude 3 Haiku (50 problems)

| Metric | Score |
|--------|-------|
| Overall Accuracy | 64.0% |
| Earnings Surprise | 100.0% |
| Financial Statement | 75.0% |
| Catalyst Identification | 66.7% |
| DCF Sanity Check | 60.0% |
| Formula Audit | 53.8% |
| Accounting Red Flag | 44.4% |

## Project Structure

```
fin-reasoning-eval/
├── README.md
├── requirements.txt
├── .env                    # API keys (not in git)
├── .gitignore
├── LICENSE
│
├── problems/               # Problem definitions
│   ├── schema.py           # Problem dataclasses
│   ├── advanced_problems.py    # 30 advanced concept problems
│   └── quant_concepts_problems.py  # 30 quant concept problems
│
├── generators/             # Problem generators
│   ├── base.py
│   ├── earnings_surprise.py
│   ├── dcf_sanity.py
│   ├── accounting_red_flags.py
│   ├── catalyst_identification.py
│   ├── formula_audit.py
│   └── financial_statement.py
│
├── evaluation/             # Evaluation framework
│   ├── dataset.py          # Dataset loader
│   ├── metrics.py          # Evaluation metrics
│   └── __init__.py
│
├── runners/                # LLM runners
│   ├── base.py             # Base runner class
│   ├── openai_runner.py    # GPT-4o, GPT-4
│   ├── anthropic_runner.py # Claude models
│   ├── huggingface_runner.py
│   └── run_evaluation.py   # Main evaluation script
│
├── leaderboard/            # Leaderboard system
│   ├── leaderboard.py
│   └── submission.py
│
├── spaces/                 # HuggingFace Spaces
│   └── app.py              # Gradio app
│
├── scripts/                # Utility scripts
│   ├── generate_dataset.py
│   ├── test_benchmark.py
│   └── update_benchmark.py
│
├── data/                   # Generated data
│   ├── financial_reasoning_benchmark.json  # Full benchmark (v1.3.0)
│   ├── benchmark_train.json    # 214 problems
│   ├── benchmark_validation.json  # 46 problems
│   ├── benchmark_test.json     # 46 problems
│   └── huggingface/
│       └── dataset_info.json
│
└── results/                # Evaluation results
    └── *.json
```

## Configuration

### Environment Variables

Create a `.env` file with your API keys:

```bash
ANTHROPIC_API_KEY=***REDACTED***...
OPENAI_API_KEY=sk-...
HF_API_KEY=hf_...
```

### Supported Models

| Provider | Models | Status |
|----------|--------|--------|
| Anthropic | claude-opus-4, claude-sonnet-4, claude-haiku-3.5 | Current |
| Anthropic | claude-3.5-sonnet, claude-3-opus, claude-3-haiku | Legacy |
| OpenAI | gpt-4.1, gpt-4.1-mini, o3, o4-mini | Current |
| OpenAI | gpt-4o, gpt-4-turbo, o1 | Legacy |
| HuggingFace | llama-4-scout, llama-3.3-70b, deepseek-r1, qwen2.5-72b | Via API |

## Use Cases

### Model Evaluation

```python
# Compare models on specific categories
for model in ["claude-sonnet-4", "gpt-4.1", "o3"]:
    results = evaluate_model(
        model,
        categories=["dcf_sanity_check"],
        difficulties=["hard", "expert"]
    )
    print(f"{model}: {results['overall_accuracy']:.1%}")
```

### Research Applications

- Evaluate domain adaptation for financial LLMs
- Analyze which financial concepts are hardest for LLMs
- Compare model performance across difficulty levels
- Study reasoning quality on complex financial problems

## Version History

| Version | Problems | Changes |
|---------|----------|---------|
| 1.3.0 | 306 | Removed 59 easy problems, focus on challenging content |
| 1.2.0 | 365 | Added 60 advanced/quant concept problems |
| 1.1.0 | 330 | Added 30 advanced concept problems |
| 1.0.0 | 300 | Initial release |

## Citation

```bibtex
@misc{financial-reasoning-eval,
  title={Financial Reasoning Eval Benchmark},
  author=bdschi1,
  year={2026},
  publisher={HuggingFace},
  url={https://huggingface.co/datasets/your-org/financial-reasoning-eval}
}
```

## License

MIT License - see LICENSE file for details.

## Contributing

Contributions welcome! Areas for improvement:
- Additional problem categories
- More sophisticated reasoning evaluation
- Integration with additional LLM providers
- Expanded coverage of financial domains

## Related Work

This benchmark is informed by and aligned with recent advances in financial NLP evaluation:

- **PRBench** (Akyurek et al., 2025) — Large-scale expert rubrics for professional reasoning evaluation with 19,356 binary criteria across 7 finance categories. Directly informs our `evaluation/rubric_scoring.py` weighted binary criteria methodology. [arXiv:2511.11562](https://arxiv.org/abs/2511.11562)
- **FLaME** (Matlin et al., 2025) — Holistic financial NLP benchmarking suite defining 6 core task categories across 20 datasets. Our `evaluation/flame_alignment.py` maps problem categories to the FLaME taxonomy for cross-benchmark comparability. [arXiv:2506.15846](https://arxiv.org/abs/2506.15846)
- **Fin-RATE** (Jiang et al., 2026) — Real-world financial analytics benchmark with three QA pathway types (DR-QA, EC-QA, LT-QA). Motivates the `cross_entity_qa` and `longitudinal_qa` problem categories. [Under review]
- **FinanceQA** (Mateega et al., 2025) — Benchmark showing frontier LLMs fail ~60% of realistic analyst tasks. Validates the need for rigorous financial reasoning evaluation with emphasis on accounting conventions and assumption handling. [arXiv:2501.18062](https://arxiv.org/abs/2501.18062)
- **Fin-o1** (Qian et al., 2025) — First open-source financial reasoning models with FinReason benchmark covering structured financial reasoning. Demonstrates that domain-specific training data quality matters more than model scale. [arXiv:2502.08127](https://arxiv.org/abs/2502.08127)

---

![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=flat&logo=python&logoColor=white)

![Gradio](https://img.shields.io/badge/Gradio-F97316?style=flat&logo=gradio&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=flat&logo=huggingface&logoColor=black)
![Anthropic](https://img.shields.io/badge/Anthropic-191919?style=flat&logo=anthropic&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)
