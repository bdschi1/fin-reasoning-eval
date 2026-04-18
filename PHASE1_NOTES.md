# Phase 1 — Implementation Notes & Deferred Items

Branch: `phase1-implementation-20260418`.
Window: Phase 1 per `Desktop/progress/upgrade_plan_04_fin_reasoning_eval.md`.

## 1. First-commit queue — status

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | Fix stale HF dataset metadata (v1.1.0 → v1.2.0, 300 → 360, add `risk_assessment`) | Done | commit `3051050` — `data/huggingface/dataset_info.json` now v1.2.0, 360 examples, 7 categories |
| 2 | Extend result schema (tokens, wall time, cost, judge/prompt versions) | Done | commit `47fcdc8` — `runners/run_evaluation.py` writes `totals`, `judge_model`, `prompt_version`; tests in `tests/test_result_schema.py` |
| 3 | Per-provider cost table in `runners/base.py` + `estimate_cost_usd` | Done | commit `47fcdc8` — `PRICING_PER_1M_USD` dict with 18 model SKUs |
| 4 | Re-run Sonnet-4 at full 360 | Deferred (API spend) | See §3 below; stale 20-problem file archived |
| 5 | Run Opus 4.7 and GPT-4.1 at full 360 | Deferred (API spend) | See §3 below |
| 6 | Rewrite `leaderboard/leaderboard.py` with cost/calibration columns | Done | commit `45df889` — `LeaderboardEntry` carries `total_cost_usd`, `cost_per_100_correct`, `brier_score`, `ece`; renderers updated |
| 7 | Author 5 long-form memo problems (Phase 2 seed) | Done | commit `1df9e3e` — `problems/memo_problems.py` with 5 gold-authored memos + rubrics; `tests/test_memo_problems.py` |
| 8 | Add `evaluation/adversarial.py` skeleton + numeric-noise variant | Done | commit `63fe1ae` — module + `tests/test_adversarial.py` |
| 9 | Draft `docs/leaderboard_methodology.md` | Done | commit `68dce74` |
| 10 | Run `/harden` on repo | In progress | This commit — see §4 |

Items 1–3, 6–9 landed on prior commits on this branch before the current
session. This session's work focused on items 4–5 (verification only, no
live run), item 10 (harden), operational docs (`LEADERBOARD_RUN.md`,
`PHASE1_NOTES.md`), the one real bug surfaced by the dry-run (see §2),
and README reconciliation.

## 2. Bug fixes surfaced by the dry-run

### JSONL context dict not flattened

`evaluation/dataset.py::_load_jsonl` passed `context` through as a dict
whereas `BaseRunner.format_prompt` requires a str. The JSON code path
already flattened via `_format_context`; JSONL did not. The symptom was a
`TypeError: sequence item 3: expected str instance, dict found` on the
first Ollama call. Fix: apply the same flattening in `_load_jsonl`.

### Thinking-truncation silent empty responses

`runners/ollama_runner.py` stripped `<think>...</think>` blocks with
`re.sub(r"<think>.*?</think>", "", ...)`. When the model ran out of tokens
inside the think block, no closing tag ever appeared, the regex silently
kept the whole block, and the caller received an empty answer flagged as
`success=True`. Fix: detect unterminated think blocks, drop everything
from the opening tag onward, and return `success=False,
error="thinking_truncated: ..."` when the resulting answer is empty. This
prevents empty-but-successful rows from polluting accuracy stats and
surfaces the root cause to operators.

## 3. What shipped vs deferred

**Shipped in this session:**

- HF dataset metadata reconciliation (live JSON = 360, HF card = 360,
  risk_assessment present).
- Runner smoke test against Ollama `qwen3.5:27b` on 3 then 2 validation
  problems — end-to-end flow confirmed, new schema fields populated.
- Two bug fixes from §2.
- `LEADERBOARD_RUN.md` — reproducible recipe with exact invocations and
  per-model cost/wall-time estimates.
- Stale `results/*.json` (n=20, n=50, n=5 from pre-Phase-1 runs) moved to
  `results/archive/pre_phase1/`.
- README refresh for accurate counts, run instructions, cost table, HF
  link.

**Deferred (explicit scope cut from the session task):**

- **Items 4 & 5 of the first-commit queue** — full 360-problem runs on
  `claude-sonnet-4`, `claude-opus-4`, `gpt-4.1` (~$75 for the three).
  These are **live API spend** and fall outside the local-only session
  scope. Scaffolded at `leaderboard_configs/phase1_items_4_5.yaml`;
  invoke via:
  ```bash
  python3 scripts/run_leaderboard.py \
      --config leaderboard_configs/phase1_items_4_5.yaml --yes
  ```
- **Full six-frontier-model leaderboard run** (~$190–250, budget ceiling
  ~$250 with contingency). Gated on explicit budget approval. Scaffolded
  at `leaderboard_configs/phase1_full_leaderboard.yaml`; o3 is commented
  out by default due to reasoning-token cost variance.
- Re-running the stale Sonnet-4 20-problem result. Same reason.
- Publishing any numbers to the HF Space or dataset repo.
- Running `huggingface-cli upload` for the regenerated `dataset_info.json`
  — house rule: local metadata change only for this pass.

The orchestrator (`scripts/run_leaderboard.py`) refuses to run without
`--yes`, validates API-key env vars, aborts if the per-config hard cost
ceiling is exceeded, and writes `manifest.json` with per-model status.
`--dry-run` walks the whole flow with zero API calls.

## 4. /harden outcome

Run locally:

```bash
pytest tests/ -v         # 231 passed, 0 failed
ruff check .             # needs re-verification post-edit
python3 -c "import fin_reasoning_eval"   # package boots
```

Notes:

- `.env` is gitignored; `.env.example` present.
- `results/` is gitignored; archived stale artifacts preserve history
  locally without committing them.
- `OLD_venv/` is a legacy venv directory — candidate for removal in a
  follow-up cleanup commit.
- `CLAUDE.md` still references **306 problems**; the live JSON is 360.
  Updated via this Phase 1 commit (along with the README).

## 5. Known gaps flagged for Phase 2 / 3

- **risk_assessment = 5 problems.** Thin category named in Phase 3. Phase
  2 adds 10 long-form risk memos; Phase 3 expands MC to 40.
- **All 360 problems are `answer_type == "multiple_choice"`.** Long-form
  memo grading is Phase 2 scope only. 5 memo problems already seeded in
  `problems/memo_problems.py` but not wired into the judge pipeline.
- **MC answer format mismatch.** Gold `correct_answer` stores full
  sentences; models emit option letters. Grading should canonicalise to
  the matching option text at comparison time. Low-effort fix but out of
  Phase 1 scope; flagged in `LEADERBOARD_RUN.md §5`.
- **Judge agreement study** (humans vs judge) — not started; referenced
  in `tests/test_judge_agreement.py` fixture but no empirical numbers yet.
- **Contamination overlap matrix** against public finance benchmarks —
  Phase 3 deliverable.

## 6. Blockers

None during this session. All fixes were tractable within the window.

The single external blocker for Phase 1 completion is **budget approval
for the ~$250 live-leaderboard run**. That decision sits outside the
local-only session scope and is captured in `LEADERBOARD_RUN.md §4` so a
future operator can execute the run in one pass.
