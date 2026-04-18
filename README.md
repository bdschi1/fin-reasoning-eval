<!-- fin-reasoning-eval/README.md | Last updated: 2026-04-16 -->

# Financial Reasoning Eval Benchmark

![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Gradio](https://img.shields.io/badge/Gradio-F97316?style=flat&logo=gradio&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=flat&logo=huggingface&logoColor=black)
![Anthropic](https://img.shields.io/badge/Anthropic-191919?style=flat&logo=anthropic&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)

A test suite for evaluating how well AI models handle finance reasoning problems — valuation, risk, portfolio math, and accounting. You give it a model, it runs 360 graded problems, and returns accuracy scores by category and difficulty level.

This is a continually developed project. Problem categories, evaluation methods, and model coverage expand over time as new financial reasoning challenges are identified.

**Key questions this project answers:**
- *How well does this AI model handle finance reasoning problems?*
- *Which financial concepts are hardest for LLMs, and at what difficulty level do they break down?*

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

## How It Works

### Overview

This benchmark contains **360 curated finance reasoning problems** across seven categories, emphasizing challenging problems that require deep financial knowledge and analytical reasoning.

| Category | Count | Description | Example Tasks |
|----------|-------|-------------|---------------|
| **Earnings Surprises** | 61 | Analyzing quarterly earnings | Beat/miss calculations, guidance analysis, earnings drift |
| **DCF Sanity Checks** | 59 | Validating valuation models | Terminal growth, WACC consistency, scenario analysis |
| **Accounting Red Flags** | 59 | Detecting accounting issues | Revenue recognition, accrual anomalies, cash flow divergence |
| **Catalyst Identification** | 53 | Identifying stock catalysts | Event timing, risk isolation, crowding analysis |
| **Formula Audit** | 63 | Finding model errors | Beta neutrality pitfalls, factor exposure, estimation error |
| **Financial Statement** | 60 | Analyzing financials | Ratio analysis, margin trends, working capital |
| **Risk Assessment** | 5 | Evaluating portfolio risk | Drawdown probability, vol-of-vol, correlation stress, liquidity risk, position-level metrics |

The Risk Assessment category covers five sub-areas: drawdown probability (max drawdown estimation, conditional recovery, leverage amplification), volatility-of-volatility (vol regime detection, VIX term structure, dispersion-correlation disconnect), correlation stress (crisis correlation breakdown, stock-bond regime shift, factor correlation during stress), liquidity risk (position exit horizon, small-cap illiquidity, crowding spirals), and position-level risk metrics (Kelly criterion, VaR vs Expected Shortfall, beta-adjusted exposure).

#### Difficulty Distribution

| Difficulty | Count | Percentage | Description |
|------------|-------|------------|-------------|
| **Hard** | 128 | 36% | Subtle issues requiring careful analysis |
| **Medium** | 116 | 32% | Requires solid financial knowledge |
| **Expert** | 40 | 11% | Complex, multi-factor problems |
| **Easy** | 76 | 21% | Baseline problems for sanity checks |

#### Advanced Problem Types

The benchmark includes 60 curated advanced problems covering:
- **Alpha/Beta Separation** - Distinguishing idiosyncratic vs. systematic returns
- **Factor Models** - Multi-factor attribution, momentum, volatility factors
- **Position Sizing** - Risk budgeting, conviction-based sizing
- **Risk Decomposition** - Tracking error, beta-neutrality pitfalls
- **Portfolio Construction** - Mean-variance optimization, constraints, capacity
- **Performance Attribution** - Drawdown analysis, process vs. outcome evaluation

## Policy

Every problem must be objectively gradable and grounded in real financial reasoning.

1. **Structured schema, no ambiguity.** Each problem follows a strict schema with ID, category, difficulty, question, context, correct answer, explanation, and reasoning steps -- nothing subjective in the ground truth.
2. **Difficulty is a feature, not a bug.** The benchmark skews hard/expert (47% combined) because easy problems do not differentiate models on financial reasoning.
3. **Category isolation for diagnostics.** Seven categories (earnings, DCF, accounting, catalysts, formula audit, financial statements, risk) enable pinpointing exactly where a model breaks down.
4. **Provider-agnostic runners.** Adding a new LLM provider means subclassing one base class -- the benchmark is model-neutral by design.
5. **Curated over generated.** Advanced problems are hand-crafted to cover alpha/beta separation, factor models, position sizing, and risk decomposition -- areas where naive generation produces shallow questions.

The eval exists to measure how well AI models handle real financial reasoning -- not pattern matching, not trivia, but the analytical problems that separate useful tools from toys.

### Dataset Format

Each problem has `id`, `category`, `difficulty`, `question`, `context`, `answer_type`, `correct_answer`, `answer_options`, `explanation`, `reasoning_steps`, and `tags`. Available as local JSON splits (train/val/test) or via HuggingFace Hub (`bdschi1/financial-reasoning-eval`).

### Evaluation Metrics

#### Primary Metrics

- **Overall Accuracy** - Percentage of correct answers
- **Category Accuracy** - Breakdown by problem category
- **Difficulty Accuracy** - Breakdown by difficulty level

#### Additional Metrics

- **Reasoning Quality** - Assessment of step-by-step reasoning
- **Latency** - Response time per problem
- **Token Usage** - Tokens consumed per evaluation

### Sample Results

#### Baseline: Claude 3 Haiku (50 problems)

| Metric | Score |
|--------|-------|
| Overall Accuracy | 64.0% |
| Earnings Surprise | 100.0% |
| Financial Statement | 75.0% |
| Catalyst Identification | 66.7% |
| DCF Sanity Check | 60.0% |
| Formula Audit | 53.8% |
| Accounting Red Flag | 44.4% |

### Configuration

#### Environment Variables

Create a `.env` file with your API keys:

```bash
ANTHROPIC_API_KEY=***REDACTED***...
OPENAI_API_KEY=sk-...
HF_API_KEY=hf_...
```

#### Supported Models

| Provider | Models | Status |
|----------|--------|--------|
| Anthropic | claude-opus-4, claude-sonnet-4, claude-haiku-3.5 | Current |
| Anthropic | claude-3.5-sonnet, claude-3-opus, claude-3-haiku | Legacy |
| OpenAI | gpt-4.1, gpt-4.1-mini, o3, o4-mini | Current |
| OpenAI | gpt-4o, gpt-4-turbo, o1 | Legacy |
| HuggingFace | llama-4-scout, llama-3.3-70b, deepseek-r1, qwen2.5-72b | Via API |

The Anthropic runner's `generate_with_thinking()` uses the native Anthropic thinking API for extended reasoning. The AI judge (`evaluation/ai_judge.py`) supports an optional `thinking_budget` parameter for extended thinking during scoring. System prompts are automatically cached via Anthropic's prompt caching API to reduce token costs on repeated calls.

### Use Cases

#### Model Evaluation

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

#### Research Applications

- Evaluate domain adaptation for financial LLMs
- Analyze which financial concepts are hardest for LLMs
- Compare model performance across difficulty levels
- Study reasoning quality on complex financial problems

## Architecture

```
fin-reasoning-eval/
├── problems/           # Problem schema, advanced/quant/risk assessment curated sets
├── generators/         # Per-category problem generators (earnings, DCF, accounting, etc.)
├── evaluation/         # Dataset loader, scoring metrics, rubric scoring, FLaME alignment
├── runners/            # LLM runner base + provider runners (Anthropic, OpenAI, HuggingFace, Ollama); Anthropic runner supports extended thinking via real API
├── leaderboard/        # Leaderboard system and submission handling
├── spaces/             # Gradio app for HuggingFace Spaces
├── data/               # Generated benchmark JSON + HuggingFace export (train/val/test splits)
└── results/            # Evaluation outputs (gitignored)
```

## Testing

```bash
pytest tests/ -v
```

## Contributing

Under active development. Contributions welcome — areas for improvement include additional problem categories, reasoning evaluation methods, LLM provider integrations, and financial domain coverage.

## License

MIT License - see LICENSE file for details.

---

***Curiosity compounds. Rigor endures.***
