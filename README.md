<!-- fin-reasoning-eval/README.md | Last updated: 2026-06-13 -->

# Financial Reasoning Eval Benchmark

![Python](https://img.shields.io/badge/python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![HuggingFace](https://img.shields.io/badge/HuggingFace-FFD21E?style=flat&logo=huggingface&logoColor=black)
![tests](https://img.shields.io/badge/tests-286%20passing-brightgreen?style=flat)

360 rubric-scored financial-reasoning problems across 7 categories (earnings surprises, DCF sanity checks, accounting red flags, catalyst identification, formula audits, financial-statement analysis, risk assessment) and 4 difficulty levels. Every problem has a multiple-choice ground truth plus a PRBench-style weighted-binary rubric that grades reasoning quality, not just the chosen letter.

**Plain English:** A test suite for AI financial reasoning. Problems use synthetic tickers; the accounting patterns, valuation mechanics, and red-flag setups are real. It pinpoints where each model breaks — valuation, accounting, portfolio math, risk, or catalyst identification.

## Install

```
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env       # ANTHROPIC_API_KEY / OPENAI_API_KEY / HF_API_KEY
```

## Usage

```
./run.sh
./run.sh eval claude-opus-4-7 test 50
```

## What it does

- Splits: train 251 / validation 55 / test 54. Categories: earnings_surprise (61), dcf_sanity_check (59), accounting_red_flag (59), catalyst_identification (53), formula_audit (63), financial_statement_analysis (60), risk_assessment (5)
- Runners for Anthropic, OpenAI, HuggingFace, Ollama; add a provider by subclassing `runners/base.py`
- Frontier leaderboard configs in `leaderboard_configs/`; orchestrator `scripts/run_leaderboard.py` is cost-gated and refuses to run without `--yes`
- Available as the HuggingFace dataset `bdschi1/financial-reasoning-eval`
- See `METHODOLOGY.md`, `LEADERBOARD_RUN.md`, `SAMPLE_TASK.md`

## Tests

```
pytest tests/ -v
```
