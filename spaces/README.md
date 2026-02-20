---
title: Financial Reasoning Eval Benchmark
emoji: 🏦
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 4.0.0
app_file: app.py
pinned: false
license: mit
---

# Financial Reasoning Eval Benchmark

Interactive leaderboard and evaluation interface for the Financial Reasoning Eval Benchmark.

## Features

- 🏆 **Leaderboard** - Compare model performance across categories and difficulties
- 🔍 **Model Details** - Deep dive into individual model performance
- 📤 **Submit Results** - Upload your evaluation results to the leaderboard

## Categories

- Earnings Surprises
- DCF Sanity Checks
- Accounting Red Flags
- Catalyst Identification
- Formula Audit
- Financial Statement Analysis

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Generate benchmark dataset
python benchmark/scripts/generate_dataset.py

# Run evaluation
python benchmark/runners/run_evaluation.py --model gpt-4.1
```

## Citation

```bibtex
@misc{financial-reasoning-eval,
  title={Financial Reasoning Eval Benchmark},
  year={2024},
  publisher={HuggingFace}
}
```
