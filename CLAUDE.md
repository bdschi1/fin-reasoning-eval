# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## What This Is

A benchmark for evaluating LLM performance on financial reasoning tasks. Contains 360 curated problems across seven categories (earnings surprises, DCF sanity checks, accounting red flags, catalyst identification, formula audit, financial statement analysis, risk assessment) with difficulty levels from easy to expert. Includes multi-provider evaluation runners, a Gradio leaderboard, and HuggingFace dataset integration.

## Commands

```bash
# Setup
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run (via run.sh)
./run.sh setup          # Create venv & install deps
./run.sh eval claude-sonnet-4 test 50  # Evaluate a model
./run.sh leaderboard    # Launch Gradio leaderboard UI

# Run (manual)
python3 runners/run_evaluation.py --model claude-sonnet-4 --limit 50

# Tests
pytest tests/ -v

# Lint
ruff check .
```

## Architecture

- `problems/` -- Problem schema dataclasses, advanced curated problems, quant concept problems
- `generators/` -- Per-category problem generators (earnings, DCF, accounting, catalyst, formula, financial statement) with shared base class
- `evaluation/` -- Dataset loader (`dataset.py`), scoring metrics (`metrics.py`), rubric scoring (`rubric_scoring.py`), FLaME alignment mapping, narrative evaluation
- `runners/` -- LLM runner base class + provider-specific runners (Anthropic, OpenAI, HuggingFace, Ollama) and main evaluation script
- `leaderboard/` -- Leaderboard system and submission handling
- `vendor_assessment/` -- Comparative framework for evaluating LLM vendors across scoring dimensions
- `spaces/app.py` -- Gradio web UI for HuggingFace Spaces
- `data/` -- Generated benchmark JSON files and HuggingFace export
- `run.sh` -- Orchestrator script for setup, generation, evaluation, and leaderboard

## Key Patterns

- Problems follow a strict schema with `id`, `category`, `difficulty`, `question`, `context`, `answer_type`, `correct_answer`, `answer_options`, `explanation`, `reasoning_steps`, and `tags`
- Runners implement a base class; adding a new LLM provider means subclassing `runners/base.py`
- Dataset splits: train (251), validation (55), test (54); total 360
- Evaluation filters by category and difficulty via CLI flags
- Benchmark versioning tracks problem count changes (v1.0.0 through v1.3.0)

## Testing Conventions

- Tests in `tests/` with smoke test, rubric scoring tests, and vendor assessment tests
- Run with `pytest tests/ -v`
- Also runnable via `./run.sh test`
