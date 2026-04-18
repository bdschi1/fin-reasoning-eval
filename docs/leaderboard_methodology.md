# Leaderboard Methodology

*Reproducibility notes for any public numbers produced by
`fin-reasoning-eval`. Pin this document's version with the version
string used to produce a leaderboard entry.*

## 1. What the leaderboard measures

For each (model, problem) pair the runner produces:

| Field | Source |
|---|---|
| `predicted` | parsed answer string |
| `correct_answer` | gold label from `data/financial_reasoning_benchmark.json` |
| `latency_ms` | wall clock from prompt submit to response complete |
| `wall_time_s` | `latency_ms / 1000` |
| `input_tokens` / `output_tokens` | provider-reported usage |
| `cost_usd` | `estimate_cost_usd(model, in, out)` using the pricing table in `runners/base.py` |

Aggregated to produce:

- **Overall accuracy** — fraction correct across the test split.
- **Category accuracy** — per-category accuracy.
- **Difficulty accuracy** — per-difficulty accuracy.
- **Brier score** — mean squared error between confidence and 0/1
  outcome (only when the runner emits a confidence estimate).
- **ECE (expected calibration error)** — 10-bin calibration error.
- **Total $ / $/100 correct** — `sum(cost_usd) / correct * 100`.
- **Rubric-by-category** — when `--auto-rubric` is enabled, average
  PRBench-style rubric score per category.

Cost-per-correct is the primary "price of accuracy" metric. The cost
field may be `None` for models without a pricing-table entry — the
leaderboard renders `—` in that case rather than zero, so readers do
not mistake "unknown" for "free".

## 2. Reproducibility recipe

Inputs are pinned on three axes.

**Dataset version.** `data/huggingface/dataset_info.json` carries the
version string (currently `v1.2.0`). A leaderboard entry is only
comparable to another entry generated at the same dataset version.

**Prompt version.** The runner attaches a `prompt_version` field to
the result output. For v1.2.0 runs the default is `v1.2.0`, matching
the dataset. Any change to `runners/base.py::format_prompt`,
`evaluation/ai_judge.py` judge prompt, or rubric criteria requires a
new prompt_version.

**Judge model.** The result output carries `judge_model`. Primary
production judge is Claude Haiku 4.5
(`claude-haiku-4-5-20251001`) because it is cheap enough to run at
scale and close enough to Sonnet on the judge-agreement harness
(`evaluation/judge_agreement.py`) to serve as the primary grader.
Never change the judge mid-leaderboard.

## 3. Prompt configuration

- `temperature`: 0.0 for all leaderboard runs. Non-zero temperature is
  allowed for experimental runs but flagged in result metadata.
- `max_tokens`: 1024 for non-reasoning models, 4096 for reasoning
  models (o-series, extended-thinking Claude). Higher caps are not
  justified for MC answers at v1.2.0.
- `top_p`: 1.0.
- `system_prompt`: canonical string in `runners/run_evaluation.py`
  (~300 chars, cached via Anthropic `cache_control: ephemeral` when
  length passes the caching threshold).
- Retries: 3 attempts per problem with linear back-off. A non-success
  after 3 attempts counts as incorrect and is logged.

Reasoning models (OpenAI o-series, Anthropic extended-thinking) are
billed for hidden thinking tokens. Budget accordingly — see the cost
table below.

## 4. Provider settings

| Provider | Runner | Notes |
|---|---|---|
| Anthropic | `runners/anthropic_runner.py` | System prompts cached; extended thinking available via `generate_with_thinking`. |
| OpenAI | `runners/openai_runner.py` | Reasoning models use `max_completion_tokens` and `developer` role. Temperature is ignored on o-series. |
| HuggingFace | `runners/huggingface_runner.py` | Either HF Inference API or local `transformers` — flag which was used in the result metadata. |
| Ollama | `runners/ollama_runner.py` | Local inference via OpenAI-compatible endpoint; `<think>` blocks are stripped from Qwen-family responses. Cost recorded as $0. |

## 5. Cost envelope (ballpark, per model, 360 problems)

Numbers are order-of-magnitude based on per-problem token counts
observed in Phase-0 runs. Actual spend varies with caching, retries,
and reasoning depth.

| Model | Expected $ | Notes |
|---|---|---|
| Claude Opus 4.7 | ~$40-55 | Generation. Using Haiku-4.5 as judge keeps judge cost ~$5-8. |
| Claude Sonnet 4.5 | ~$15-25 | Primary workhorse. |
| Claude Haiku 4.5 | ~$2-4 | Also usable as judge. |
| GPT-4.1 | ~$15-25 | |
| o3 | ~$60-100 | Reasoning tokens dominate; consider a 150-problem stratified subsample. |
| DeepSeek-v3.1 | ~$3-6 | Very low API cost. |
| Llama-3.3-70b (hosted) | ~$5-10 | Together / HF Inference. |
| Qwen-family local (Ollama) | $0 | Wall time dominates; treat cost cells as N/A. |

Phase 1 full-leaderboard envelope: $250-400, plus ~30% contingency
for retries and prompt-version reruns → budget $500.

## 6. Running a single model

```bash
# Dry run against a 10-problem slice — cheap, validates the pipeline.
python3 runners/run_evaluation.py \
    --model claude-3-haiku \
    --split test \
    --limit 10 \
    --output-dir ./results/dry_run

# Full 360-problem run (reads train/val/test splits).
python3 runners/run_evaluation.py \
    --model claude-sonnet-4 \
    --split test \
    --output-dir ./results/v1.2.0 \
    --auto-rubric \
    --contamination-check
```

Result artifacts written to `output-dir`:

- `<model>_results.json` — aggregated metrics + totals block.
- `<model>_predictions.json` — per-problem predictions with token
  and cost accounting.
- `<model>_narrative.txt` — human-readable summary.
- `<model>_contamination.json` — (when `--contamination-check` is on).

## 7. Running the full leaderboard sweep

The repo does not ship a single "run everything" command intentionally
— each model's run costs real money. The recommended flow is:

1. Commit the current dataset version. Note the git SHA.
2. For each target model, run the full 360 via the single-model
   command above, writing into a per-version folder.
3. After all runs complete, start the Gradio UI and point it at that
   folder:

   ```bash
   python3 spaces/app.py --results-dir ./results/v1.2.0
   ```

4. Post the hero chart (accuracy vs. $/correct scatter) as the
   leaderboard image.

A lightweight wrapper (`LEADERBOARD_RUN.md` at repo root) documents
the exact invocation, expected cost, and wall-clock time for the next
full sweep.

## 8. CI smoke path

Before any public leaderboard push:

```bash
python3 runners/run_evaluation.py --ci
```

5 problems on validation split, Haiku judge, fails if accuracy
< 0.50. Outputs JSON to stdout; exits 1 on failure. This is a
correctness gate, not a performance one — the value is catching a
broken pipeline before it burns hours of compute.

## 9. Known limitations of current numbers

- **`risk_assessment` is thin (5 problems).** Category-level scores
  for risk are indicative, not decisive. Phase 3 target is 40.
- **All multiple-choice.** Pattern-matchers vs. genuine reasoners
  cannot be fully separated at v1.2.0. Phase 2 adds long-form memo
  grading for 30 problems.
- **No adversarial variants yet.** Consistency column is planned for
  Phase 3.
- **Single judge per run.** Inter-judge variance is measured by the
  judge-agreement harness on a held-out set but is not yet a
  per-problem score on the main leaderboard.

## 10. Change log for this document

| Version | Date | Change |
|---|---|---|
| v0.1 | 2026-04-18 | Initial draft covering v1.2.0 dataset. |
