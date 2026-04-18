---
license: mit
language:
- en
pretty_name: Financial Reasoning Eval Benchmark
size_categories:
- n<1K
task_categories:
- question-answering
- multiple-choice
tags:
- finance
- reasoning
- evaluation
- benchmark
- valuation
- accounting
- risk
- llm-eval
configs:
- config_name: default
  data_files:
  - split: train
    path: train.jsonl
  - split: validation
    path: validation.jsonl
  - split: test
    path: test.jsonl
---

# Financial Reasoning Eval Benchmark — Dataset Card

**Version:** 1.2.0
**Total examples:** 360
**Splits:** train 251 / validation 55 / test 54
**License:** MIT

A curated benchmark for evaluating how large language models perform on
finance reasoning problems. Problems emphasize judgment over recall —
valuation sanity checks, accounting anomalies, DCF framework errors,
formula audits, and portfolio-risk interpretation.

## At a glance

| Category | Count | What it tests |
|---|---|---|
| `earnings_surprise` | 61 | Beat/miss arithmetic, guidance parsing, EPS drift |
| `dcf_sanity_check` | 59 | Terminal growth, WACC sign, scenario coherence |
| `accounting_red_flag` | 59 | Revenue recognition, accrual anomalies, cash-flow divergence |
| `catalyst_identification` | 53 | Event timing, risk isolation, crowding |
| `formula_audit` | 63 | Model-cell errors, sign/unit mistakes, boundary conditions |
| `financial_statement_analysis` | 60 | Ratio interpretation, margin trend, working capital |
| `risk_assessment` | 5 | Portfolio drawdown, vol-of-vol, stress correlation *(small — see Known Gaps)* |

Difficulty mix: easy 76 / medium 116 / hard 128 / expert 40.
All 360 problems are `multiple_choice` with four options in v1.2.0.
Long-form memo problems are a planned v1.3.x addition.

## Known gaps

- **`risk_assessment` is under-filled** at 5 problems. Treat category-level
  scores for risk as indicative, not decisive, until expanded. A larger
  (~40-problem) risk set is planned for a future version.
- **All answers are multiple-choice.** Open-ended memo grading is a
  planned extension, not part of v1.2.0.

## Schema

```json
{
  "id": "string",
  "category": "string",
  "difficulty": "easy|medium|hard|expert",
  "question": "string",
  "context": "string",
  "answer_type": "multiple_choice",
  "correct_answer": "string",
  "options": [{"id": "A", "text": "..."}, ...],
  "explanation": "string",
  "reasoning_steps": ["string", ...],
  "tags": ["string", ...]
}
```

## Usage

```python
from datasets import load_dataset

ds = load_dataset("bdschi1/financial-reasoning-eval")
print(ds)
# DatasetDict({
#     train: Dataset(num_rows=251),
#     validation: Dataset(num_rows=55),
#     test: Dataset(num_rows=54),
# })
```

The repository at <https://github.com/bdschi1/fin-reasoning-eval> provides
multi-provider runners, an AI judge, calibration metrics, and a Gradio
leaderboard.

## Intended use

- Comparing LLMs on finance-specific reasoning rather than general QA.
- Probing where a model degrades by difficulty or category.
- Exercising AI-judge pipelines against an objectively graded MC set.

## Limitations

- Static dataset — no live market data; reproducibility trades against
  recency.
- Categories skew toward public-equity analysis; fixed income, derivatives,
  and credit get lighter coverage.
- Author/authoring-style bias may be present; rubric audits and judge
  agreement checks are in progress.

## Citation

```
@misc{financial-reasoning-eval,
  title  = {Financial Reasoning Eval Benchmark},
  year   = {2026},
  note   = {v1.2.0}
}
```
