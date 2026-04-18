# Leaderboard Run Playbook — Phase 1

Operational notes for producing the first public leaderboard. **Not executed
yet** — this document is the reproducible recipe. Phase 1 deliverables in
this repo stop at "runner works end-to-end on one model against a small
sample"; the full 360 × 6-model run is explicit downstream work with a
separate budget approval gate.

## TL;DR — run via the orchestrator

Two YAML configs are checked in. Use them instead of hand-invoking each
model:

```bash
# Preview (no API calls)
python3 scripts/run_leaderboard.py --config leaderboard_configs/phase1_items_4_5.yaml --dry-run

# Items 4 & 5 only: Sonnet 4 + Opus 4 + GPT-4.1 (~$75)
python3 scripts/run_leaderboard.py --config leaderboard_configs/phase1_items_4_5.yaml --yes

# Full six-model leaderboard (~$190–250, ceiling $250)
python3 scripts/run_leaderboard.py --config leaderboard_configs/phase1_full_leaderboard.yaml --yes
```

The orchestrator prints a cost preview, validates required env vars
(`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, etc.), refuses to run without
`--yes`, and writes a `manifest.json` with per-model status into the
config's `output_dir`. Models with existing result files are skipped
unless `--force` is passed. See §§1–5 below for the underlying
methodology.

Pin the following before any public push:

- `prompt_version = v1.2.0` (matches `data/huggingface/dataset_info.json`).
- `judge_model = claude-haiku-4-5-20251001` (Sonnet as a regression-sanity
  cross-check judge, one pass only).
- Benchmark commit SHA (record the repo HEAD at run time in each result file).

## 1. Dataset prerequisite

```bash
# Verify 360 / 7-category live JSON matches the HF export metadata.
python3 -c "import json; d=json.load(open('data/financial_reasoning_benchmark.json')); \
print(d['total_problems'], d['category_distribution'])"

# Expect: 360  {'earnings_surprise': 61, ...}
python3 -c "import json; d=json.load(open('data/huggingface/dataset_info.json')); \
print(d['version'], d['total_examples'])"

# Expect: 1.2.0 360
```

If either mismatches, regenerate the HF export before running the
leaderboard:

```bash
python3 scripts/rebuild_hf_export.py  # wrapped around the existing export logic
```

## 2. Smoke check on one model (runner validation)

```bash
# Local Ollama dry-run (free, ~2 min per problem at 4096 max_tokens on M-series).
python3 runners/run_evaluation.py \
    --model ollama:qwen3.5:27b \
    --split validation \
    --limit 5 \
    --max-tokens 4096

# Managed-API dry-run on Claude Haiku — cheapest paid verification.
# Rough cost at 5 problems: ~$0.02.
python3 runners/run_evaluation.py \
    --model claude-haiku-3.5 \
    --split validation \
    --limit 5 \
    --max-tokens 2048
```

Inspect the resulting `results/{model}_results.json` for:

- `dataset_size == 5`
- `totals.input_tokens`, `totals.output_tokens`, `totals.wall_time_s`,
  `totals.cost_usd` populated
- `judge_model`, `prompt_version` set
- At least one prediction has a non-empty `predicted` (reasoning models
  emit `<think>` blocks that may eat the token budget — see §5).

## 3. Full run per model (360 problems)

```bash
# Anthropic
python3 runners/run_evaluation.py --model claude-opus-4       --split test --max-tokens 4096 --auto-rubric
python3 runners/run_evaluation.py --model claude-sonnet-4     --split test --max-tokens 4096 --auto-rubric
python3 runners/run_evaluation.py --model claude-haiku-3.5    --split test --max-tokens 2048

# OpenAI
python3 runners/run_evaluation.py --model gpt-4.1             --split test --max-tokens 4096 --auto-rubric
python3 runners/run_evaluation.py --model o3                  --split test --max-tokens 8192 --auto-rubric

# HuggingFace / Together (set HF_API_KEY)
python3 runners/run_evaluation.py --model llama-3.3-70b       --split test --max-tokens 4096
python3 runners/run_evaluation.py --model deepseek-v3.1       --split test --max-tokens 4096
```

`--split test` restricts to the 54-problem test split so generation cost is
tractable. For a full 360-problem run, omit `--split` (defaults to `test`
in this repo; to force all-splits use the export path below).

To run all 360 in one pass (merges the 3 splits):

```bash
python3 runners/run_evaluation.py \
    --model <MODEL> \
    --data-dir data \
    --split test \
    --max-tokens 4096
# note: --data-dir data loads the full benchmark JSON (360 problems) when
# split=test is the fallback path.
```

## 4. Cost and wall-time envelope

Figures are planning estimates (probabilistic, not guarantees) based on the
per-1M pricing table in `runners/base.py` and an assumption of ~3k input /
~1.5k output tokens per problem before the judge pass.

| Model | Provider | Tokens in/out (est) | 360-problem cost | 360-problem wall time |
|---|---|---|---|---|
| claude-opus-4 | Anthropic | 1.08M / 0.54M | ~$57 | ~90 min |
| claude-sonnet-4 | Anthropic | 1.08M / 0.54M | ~$12 | ~60 min |
| claude-haiku-3.5 | Anthropic | 1.08M / 0.54M | ~$3 | ~30 min |
| gpt-4.1 | OpenAI | 1.08M / 0.54M | ~$6.5 | ~45 min |
| o3 | OpenAI | 1.08M / 1.80M (+thinking) | ~$85 | ~3 hr |
| llama-3.3-70b | HF Inference | 1.08M / 0.54M | ~$1.5 | ~90 min |
| deepseek-v3.1 | DeepSeek | 1.08M / 0.54M | ~$1 | ~60 min |
| qwen3.5:27b | Ollama (local) | n/a | $0 | ~6–10 hr |

Plus a Haiku-4.5 judge pass at ~$3 per model × 7 models ≈ $21. Total
planning envelope: **~$190** for the six-frontier-model set (Opus + Sonnet +
Haiku + GPT-4.1 + o3 + Llama-3.3 + DeepSeek), with 30% contingency pushing
the budget ceiling to **~$250**.

The upgrade plan's $500 budget covers one full-set run plus a retry / a
re-run with a bug-fix prompt version.

## 5. Known runner caveats

- **Reasoning models (`o3`, Qwen3.5 thinking, DeepSeek-R1) need
  `--max-tokens 4096` or higher.** At 1024 tokens the model can spend its
  entire budget inside a `<think>` block and emit an empty final answer.
  The Ollama runner flags this as `error="thinking_truncated: ..."` and
  `success=False`, which filters the result from accuracy metrics.
- **Judge drift:** pin `JUDGE_MODEL` and `PROMPT_VERSION` env vars for the
  whole leaderboard run. They are written into every result file so a
  future audit can detect version mixing.
- **Rate limits:** HF Inference throttles at ~5 req/s. Add a 0.2 s sleep
  between calls or batch in 50-problem chunks with retry.
- **o3 cost ceiling:** reasoning tokens can triple output. If the dry-run
  averages >3k output tokens/problem, subsample to 150 stratified problems
  and extrapolate with confidence intervals rather than run all 360.
- **MC grading mismatch:** the current gold answers store full sentences
  ("High leverage - Net Debt/EBITDA of 4.7x") while models typically
  output option letters ("C"). Phase 1 scoring should use
  `evaluation/metrics.py`'s option-letter-aware matching when the answer
  type is `multiple_choice`. If accuracy looks near-zero on a known-good
  model, inspect `predictions.json` before assuming a model regression.

## 6. Post-run checklist

1. Regenerate leaderboard markdown/HTML from the result files
   (`python3 -c "from leaderboard.leaderboard import *; ..."`).
2. Tag the repo (`git tag -a leaderboard-v1.2.0`).
3. Bundle the per-model JSON as `results/leaderboard_v1.tar.gz`.
4. Update `docs/leaderboard_methodology.md` with the exact commit SHA and
   any deviation from the recipe above.
5. Run `/harden` and `pytest` once more before pushing the leaderboard
   Space.

See `docs/leaderboard_methodology.md` for the definition of each metric
column and the calibration / cost columns.
