<!-- METHODOLOGY.md | fin-reasoning-eval | Problem design + rubric methodology -->

# Methodology

This document explains the design principles behind the benchmark and points to the files that carry the full specifications. For a single worked problem (prompt, gold answer, rubric, anchor responses), see [`SAMPLE_TASK.md`](SAMPLE_TASK.md).

**Scope:** 360 problems across 7 categories and 4 difficulty levels, delivered as fixed train/validation/test splits (251 / 55 / 54). Every problem follows a uniform schema; scoring uses a multiple-choice primary answer with a PRBench-style weighted-binary rubric layered on top.

---

## 1. Design philosophy

Many finance-adjacent LLM benchmarks test recall of definitions or the ability to plug numbers into a canonical formula. This benchmark is built for a narrower question: does the model reason through finance problems the way a practitioner would — catching the perpetuity-growth violation, flagging the revenue-recognition anomaly, sizing by risk rather than conviction — or does it pattern-match to fluent-sounding distractors?

Three consequences shape every design choice:

1. **Problems are adversarial by construction.** Each multiple-choice stem is written so that at least one distractor reflects a real, recurring failure mode — sector-average framing, historical-growth framing, beta-matching as alpha, narrative as thesis. Fluent prose is not enough to land on the correct answer.
2. **Difficulty skews hard.** Easy problems (21%) exist only as sanity checks; the bulk sits at medium / hard / expert (32% / 36% / 11%). Easy-weighted benchmarks do not differentiate frontier models on financial reasoning.
3. **Categories are diagnostic, not decorative.** The seven categories are chosen so that per-category accuracy points to specific capability gaps (valuation, accounting, portfolio math, catalyst identification) rather than a single headline number.

---

## 2. Category taxonomy

Source of truth: `data/financial_reasoning_benchmark.json` → `category_distribution`. Per-category counts live in [`README.md`](README.md#how-it-works).

| # | Category | What it tests | Representative failure mode |
|---|---|---|---|
| 1 | Earnings Surprises | Beat/miss attribution, guidance vs. consensus, post-earnings drift, quality-of-earnings signals | Treating the headline beat as the signal when the guide-down is the signal |
| 2 | DCF Sanity Checks | Terminal growth discipline, WACC consistency, TV/EV split, sensitivity asymmetry | Perpetuity growth above long-run GDP; accepting narrative as justification |
| 3 | Accounting Red Flags | Revenue recognition, accrual vs. cash divergence, inventory / receivables behavior, non-GAAP adjustments | Missing a DSO / DSI trend because the headline income statement looks clean |
| 4 | Catalyst Identification | Event timing, crowding, idiosyncratic vs. macro, expected-value framing | Mistaking a priced-in catalyst for an edge |
| 5 | Formula Audit | Beta-neutrality pitfalls, factor exposure arithmetic, Kelly sizing, tracking-error decomposition | Treating beta exposure as alpha; misapplying CAPM to private assets |
| 6 | Financial Statement Analysis | Margin trend attribution, working-capital dynamics, ratio interplay, segment contribution | Conflating revenue mix shift with margin expansion |
| 7 | Risk Assessment | Drawdown probability, volatility regimes, correlation stress, liquidity / crowding, position-level metrics (VaR, ES, Kelly) | Using unconditional correlations during a regime shift |

Sub-areas (especially within Risk Assessment and Formula Audit) are documented in [`README.md`](README.md#how-it-works) and in the per-category files under `generators/`.

---

## 3. Difficulty calibration

Difficulty is a first-class field on every problem. Definitions (from `problems/schema.py`):

| Level | Share | Author's test |
|---|---|---|
| Easy | 21% | Can a first-year analyst answer this from definitions and one-step arithmetic? If yes, mark easy. Used as sanity anchors. |
| Medium | 32% | Needs solid second-year fluency — comfortable with DCF mechanics, accounting linkages, standard ratios — but no multi-factor judgment. |
| Hard | 36% | Requires recognizing and rejecting a named failure mode (e.g., sector-average framing on terminal growth, CAPM-on-private-asset, beta as alpha). Where frontier models diverge. |
| Expert | 11% | Multi-factor or multi-statement reasoning, regime awareness, or asymmetry detection (e.g., asymmetric sensitivity bands on DCF, correlation breakdown under stress, multi-step accounting reconciliation). |

The distribution is deliberate: the interesting signal is in the hard / expert cells where models that are fluent on definitions stop being fluent on reasoning.

---

## 4. Scoring: MC primary + rubric overlay

Every problem has a multiple-choice ground truth (one correct answer, three distractors with distinct failure-mode profiles). That gives a clean, LLM-judge-free accuracy metric at scale. Layered on top is a PRBench-aligned weighted-binary rubric (`evaluation/rubric_scoring.py`) that grades reasoning quality on the model's free-text response, not just the chosen option.

### Rubric structure

Source: `evaluation/rubric_scoring.py:96` (categories) and `:137` (default criteria).

| Category | Criteria | Max weight | What it measures |
|---|---|---|---|
| `numerical_accuracy` | 5 | 10 | Final answer correct within tolerance; intermediate math shown and consistent; units and bases correct |
| `conceptual_understanding` | 4 | 8 | Correct core concept identified; related-but-distinct concepts kept separate; appropriate framework applied |
| `reasoning_chain` | 5 | 10 | Logical sequence; every step justified; conclusion follows from premises; no circularity; alternatives considered |
| `financial_terminology` | 3 | 5 | Terms used correctly; GAAP vs. non-GAAP distinguished; industry-appropriate language |
| `risk_awareness` | 4 | 7 | Key risks identified; quantitative measures referenced where available; systematic vs. idiosyncratic distinguished; tail scenarios considered |
| `assumption_identification` | 3 | 5 | Explicit and implicit assumptions surfaced and tested for reasonableness |
| `completeness` | 3 | 6 | All sub-questions answered; context used; appropriate length |
| `skill_adherence` | 5 (per skill) | — | For plugin-derived scenarios: structure, conventions, inputs, completeness, probabilistic language |

Scores are produced as weighted sums normalized to [0, 100] at both the overall and per-category level (`RubricResult.overall_pct`, `CategoryScore.pct`). Category-level scores are the diagnostically useful signal; a model that scores 85 overall with 30 on `risk_awareness` is telling you where to *not* deploy it.

### Why binary weights, not Likert scales

Binary criteria (met / not met) with integer weights are how the PRBench paper [PRBench (2025)](https://arxiv.org/abs/2511.04478) gets to inter-rater reliability above 0.8 kappa. Likert grading on soft "how well does the reasoning flow" questions disagrees across graders and makes aggregated scores meaningless. The tradeoff is loss of fine-grained signal per criterion; the offset is thousands of criteria that in aggregate recover the resolution.

### Inspiration and lineage

- [PRBench (2025)](https://arxiv.org/abs/2511.04478) — Professional Reasoning Benchmark for Finance. Source of the weighted-binary criterion design and the 7 finance rubric categories above (I add `skill_adherence` on top for plugin-derived scenarios).
- FLaME (2025) — standardized taxonomy for financial NLP evaluation. Source of the category boundaries (earnings, valuation, accounting, risk).

---

## 5. Ground-truth discipline

Every problem in the benchmark is held to five constraints, checked in `tests/test_problem_schema.py` and the generator base class:

1. **Objectively gradable.** The correct answer is either a labeled option or a numerical value with a tolerance. No "it depends" ground truths.
2. **Strict schema.** `id`, `category`, `difficulty`, `question`, `context`, `answer_type`, `correct_answer`, `answer_options`, `explanation`, `reasoning_steps`, `tags`, `common_mistakes`. See `problems/schema.py`.
3. **Explanation required.** Every problem ships with a step-by-step reasoning chain (`reasoning_steps`) that a grader could replicate. Used for rubric anchoring and for failure-mode attribution.
4. **Common-mistake list.** Each problem names the 2–4 specific traps it is designed to surface. Distractors are drawn from this list.
5. **Provider-agnostic.** Problems contain no model-specific formatting or hidden tokens. Any runner implementing `runners/base.py` can serve them.

### Synthetic companies, real reasoning

Tickers and company names are synthetic throughout ("Titan Resources", "Lunar Lifestyle", "Wavelength Chemicals"). The reasoning structures, accounting patterns, and valuation mechanics are not. This keeps the benchmark free of ticker-memorization shortcuts and free of any real-issuer IP, while preserving the financial-reasoning signal the benchmark is measuring.

---

## 6. How gold answers are validated

1. **Deterministic grading for MC primary.** The benchmark-wide accuracy metric does not use an LLM judge — the correct option is labeled in the schema (`answer_options[i].is_correct`). Scores are reproducible across runs.
2. **Rubric overlay via `RubricGrader`.** Free-text reasoning is scored against the binary criteria. For automated pipelines, an LLM judge (`evaluation/ai_judge.py`) produces per-criterion met/not-met verdicts; for gold-standard runs, a human grader does the same with the same schema.
3. **Inter-grader agreement.** When an LLM judge is used, `judge_agreement.py`-style kappa sampling against human-graded pairs is on the roadmap (see `LEADERBOARD_RUN.md` for cost and sampling plan).
4. **Overconfidence screen.** The skill-adherence probabilistic-language criterion (`evaluation/rubric_scoring.py:244`) explicitly penalizes phrases like "guaranteed", "100% correct", "cannot lose", matching the repo-wide [output-language rule](/Users/bdsm4/.claude/CLAUDE.md). Investment reasoning is probabilistic; rubric language enforces that.

---

## 7. Key files

| File | Purpose |
|---|---|
| `problems/schema.py` | Dataclass schema every problem conforms to |
| `data/financial_reasoning_benchmark.json` | The 360-problem dataset (splits + distribution + full problems) |
| `generators/` | Per-category problem generators with a shared base class |
| `evaluation/dataset.py` | Dataset loader with category/difficulty filters |
| `evaluation/metrics.py` | MC accuracy, per-category and per-difficulty breakdowns |
| `evaluation/rubric_scoring.py` | PRBench-style weighted-binary rubric grader |
| `evaluation/ai_judge.py` | LLM-as-judge pipeline for the rubric overlay |
| `runners/base.py` | Provider-agnostic runner interface |
| `runners/{anthropic,openai,huggingface,ollama}_runner.py` | Provider implementations |
| `LEADERBOARD_RUN.md` | Full benchmark recipe with cost and wall-time budgets |
| [`SAMPLE_TASK.md`](SAMPLE_TASK.md) | One worked problem, end-to-end, portable |

---

## 8. Limitations (stated, not papered over)

- The `risk_assessment` category is thin at 5 problems in v1.2.0. Phase 3 expands it to 40 including 10 long-form variants; tracked in `problems/memo_problems.py` scaffold.
- Long-form memo-style problems (`memo_problems.py`) are schema-defined but not yet wired into the runner pipeline.
- Phase-1 leaderboard is scaffolded with explicit cost ceilings; no frontier-model results are committed yet. See `LEADERBOARD_RUN.md` for the exact invocation recipe and per-cell budget envelope.
- Multiple-choice stems have finite distractor creativity. The rubric overlay is what catches fluent-but-wrong reasoning that lands on the correct letter for the wrong reasons.

These limits are deliberate disclosures: a benchmark that understates its gaps is less useful than one that names them.
