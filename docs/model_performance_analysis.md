# Model Performance Analysis

`fin-reasoning-eval/docs/model_performance_analysis.md`
Last updated: 2026-04-16

## Purpose

This document analyzes model performance on the fin-reasoning-eval benchmark, using actual evaluation results to identify where models succeed, where they fail, and what the failure patterns reveal about current LLM limitations in financial reasoning. Results are drawn from evaluation runs against the 360-problem benchmark across multiple models and difficulty levels.

---

## Benchmark Structure

**360 problems** across 7 categories, each testing a distinct financial reasoning capability:

| Category | Count | Tests |
|---|---|---|
| Formula Audit | 63 (17.5%) | Identifying sign errors, circular references, missing adjustments in financial model formulas |
| Earnings Surprise | 61 (16.9%) | Diagnosing the primary driver of EPS variance (revenue vs. margin vs. one-time items) |
| Accounting Red Flag | 59 (16.4%) | Detecting earnings quality issues via accrual ratios, cash flow divergence, unusual patterns |
| DCF Sanity Check | 59 (16.4%) | Evaluating whether DCF assumptions and outputs are reasonable or indicate modeling errors |
| Financial Statement Analysis | 60 (16.7%) | Calculating ratios, growth rates, and proportions from financial statement data |
| Catalyst Identification | 53 (14.7%) | Prioritizing investment catalysts by probability, impact, and timing |
| Risk Assessment | 5 (1.4%) | Evaluating factor risk, hedging limitations, and regime-dependent risk dynamics |

**Difficulty distribution:** Easy 21% / Medium 32% / Hard 36% / Expert 11%. The distribution is deliberately skewed toward harder problems — benchmarks that are mostly easy fail to discriminate between model capabilities.

---

## Evaluation Results

### Cross-Category Performance (Claude 3 Haiku, n=50)

The most informative evaluation run: 50 problems spanning 6 categories, providing cross-category discrimination.

| Category | Accuracy | n | Interpretation |
|---|---|---|---|
| Financial Statement Analysis | 87.5% | 8 | Strongest. Calculation-heavy, formulaic — models excel at arithmetic extraction from structured data. |
| Earnings Surprise | 85.7% | 7 | Strong. Earnings driver identification maps well to pattern recognition: revenue vs. margin vs. one-time items. |
| Accounting Red Flag | 77.8% | 9 | Moderate. Requires threshold-based judgment (e.g., "30% accrual ratio = warning") — models handle well-documented thresholds but struggle with contextual interpretation. |
| Formula Audit | 76.9% | 13 | Moderate. Sign convention and logical consistency checking is pattern-matchable, but multi-step formula chains degrade accuracy. |
| Catalyst Identification | 66.7% | 6 | Weak. Requires weighing probability × impact × timing — a multi-dimensional judgment task where models show lower reliability. |
| DCF Sanity Check | 60.0% | 5 | Weakest. Requires knowing what "reasonable" looks like — terminal value as % of total, implied growth rates, WACC ranges by sector. This is experiential knowledge, not formula application. |

**Key finding:** Model accuracy correlates inversely with the degree of judgment required. Categories that reduce to calculation or pattern-matching (financial statement analysis, earnings surprise) score 85%+. Categories that require contextual reasonableness assessment (DCF sanity check, catalyst identification) score 60-67%. This gradient is consistent with the hypothesis that LLMs are stronger at procedural tasks than at tasks requiring calibrated professional judgment.

### Difficulty Gradient (Claude 3 Haiku, n=50)

| Difficulty | Accuracy | n |
|---|---|---|
| Easy | 90.0% | 10 |
| Medium | 84.2% | 19 |
| Hard | 58.8% | 17 |
| Expert | 75.0% | 4 |

The easy-to-hard gradient (90% → 59%) validates the difficulty calibration: harder problems are actually harder for models. The expert result (75%) appears anomalously high relative to hard (59%), but the sample size (n=4) is too small to draw conclusions — confidence intervals at this sample size span roughly 30-100%.

The steepest accuracy drop occurs between medium (84%) and hard (59%) — a 25pp decline. This suggests the difficulty boundary between "problems models can reliably solve" and "problems that require genuine analytical judgment" falls at the medium/hard boundary in this benchmark.

### Format vs. Reasoning Errors (Claude Sonnet 4, n=20)

A separate evaluation run revealed an important methodological insight. Claude Sonnet 4 scored 85% on 20 financial statement analysis problems, but examination of the "incorrect" responses revealed that most errors were format mismatches, not reasoning failures:

| Model Answer | Expected Answer | Error Type |
|---|---|---|
| 14.5% | 0.14464 | Format: percentage vs. decimal |
| 2.90% | 0.02899 | Format: percentage vs. decimal |
| 22.43% | 0.22429 | Format: percentage vs. decimal |
| $3,298 million | 3297.66667 | Format: labeled vs. raw number |
| $704.25 million | 705.25 | Rounding + format |

Of 14 flagged errors, approximately 11 were format mismatches where the model's reasoning was correct but the answer representation did not match the expected format. Only 2-3 represented genuine calculation errors (e.g., answering 8.61% when the correct value was 6.76%).

**Implication:** Raw accuracy alone overstates model failure rates for calculation tasks. Evaluation pipelines should distinguish between reasoning errors (wrong answer) and representation errors (right answer, wrong format). The current benchmark uses strict matching; a fuzzy-match grading mode that normalizes percentages and decimal representations would likely show Sonnet 4 at 90-95% accuracy on this category rather than 85%.

This finding does NOT apply to judgment tasks (DCF sanity check, catalyst identification) where the answer itself requires qualitative assessment.

### Open-Source Model Performance (Qwen 3.5-122B, n=5)

An evaluation of Qwen 3.5-122B-A10B scored 0% on 5 problems, but with reasoning quality scored at 3.0/5.0. This suggests the model's analytical reasoning may be acceptable while its answer formatting or extraction fails the strict-match grading. The sample is too small for category-level analysis, but the result indicates that answer-extraction reliability is a meaningful axis of model variation, independent of reasoning quality.

---

## Category-Specific Failure Signatures

### DCF Sanity Check (Weakest Category, 60%)

The DCF sanity check category is designed to test whether a model can identify when a DCF's outputs are unreasonable — not whether it can build a DCF. Failure patterns include:

- **Terminal value proportion insensitivity.** A terminal value representing 35% of total enterprise value is unusual for most companies (typical range: 60-80%). Models sometimes accept this without flagging it, or flag it in the wrong direction (calling it "conservative" rather than investigating why near-term FCF is so dominant).
- **Implied growth rate blindness.** When a DCF implies a terminal growth rate above nominal GDP growth, this is a red flag. Models calculate the implied rate correctly but fail to compare it against the reasonable range for the sector.
- **WACC reasonableness.** Models apply WACC formulas correctly but do not catch sector-inappropriate inputs (e.g., an equity risk premium that is too low for a biotech, or a beta that does not reflect the company's actual risk profile).

These failures share a common root: the model lacks a calibrated sense of "normal" for financial parameters. Knowing that a 35% terminal value proportion is unusual requires having seen hundreds of DCFs and knowing the distribution. This is experiential knowledge that text-based training may not adequately capture.

### Catalyst Identification (Second Weakest, 67%)

Catalyst identification requires multi-dimensional ranking: probability × impact × timing, where impact has qualitative components (what kind of event? how does it change the thesis?) and timing interacts with portfolio constraints (a Q4 catalyst matters differently in Q3 than in Q1).

Failure patterns include:

- **Impact miscalibration.** Treating all "high probability" events as equally important regardless of impact magnitude. An 80% probability / low impact catalyst may rank below a 50% probability / high impact catalyst on an expected-value basis, but models inconsistently apply this framework.
- **Timing as afterthought.** Models list catalysts with timing but do not use timing as a ranking input. Two catalysts with identical probability × impact should be ranked differently if one is 2 weeks away and the other is 6 months away — the near-term catalyst has a more defined risk/reward window.

### Formula Audit (77%)

Formula audit tests range from straightforward sign-convention checks (easy) to multi-step formula chain validation (hard/expert). The difficulty gradient within this category is steep:

- **Easy problems (sign errors, missing operations):** Models identify these reliably. "Should repayments be added or subtracted?" is a pattern-matchable check.
- **Hard problems (circular references, multi-step propagation):** Models struggle when an error in one formula propagates through 3-4 dependent cells. Tracing the impact requires maintaining a mental model of the formula dependency graph, which degrades as chain length increases.

---

## Evaluation Methodology

### Grading Architecture

The benchmark uses a two-layer grading system:

1. **Strict accuracy** (primary metric): Exact or tolerance-matched answer comparison. Binary: correct or incorrect. This is the metric reported in all results above.

2. **Rubric scoring** (secondary metric): 27-criterion rubric across 7 categories (Numerical Accuracy, Conceptual Understanding, Reasoning Chain, Financial Terminology, Risk Awareness, Assumption Identification, Completeness). Each criterion is binary (met/not met) with integer weights (1-3). Rubric scoring is applied via an AI judge (FinancialReasoningJudge) that evaluates model responses against criteria with confidence tracking.

The rubric layer adds nuance that strict accuracy misses. A model that gets the wrong answer but shows sound reasoning chains scores differently from a model that guesses the right answer without justification. Both receive the same strict accuracy score; the rubric distinguishes them.

### Confidence-Flagged Human Review

The AI judge assigns confidence levels (high/medium/low/unclear) to each criterion judgment. Criteria judged at "low" or "unclear" confidence are flagged for human review. This hybrid approach ensures that automated grading does not silently propagate uncertain judgments into aggregate scores.

When the AI judge fails validation (malformed output), all criteria default to not-met with confidence=unclear, and the entire result is flagged. This conservative fallback ensures that judge failures reduce reported accuracy rather than inflate it.

---

## Recommendations

### For Model Developers

1. **DCF reasonableness calibration.** Models would benefit from training data that includes examples of reasonable vs. unreasonable DCF parameters — terminal value proportions, implied growth rates, sector-appropriate WACC ranges. This is not formula knowledge; it is distributional knowledge about what real financial models look like.

2. **Multi-dimensional ranking.** Catalyst identification and similar tasks require explicit framework application (probability × impact × timing), not just listing factors. Training data that shows the ranking process — with tradeoffs between dimensions — would likely improve performance on these tasks.

3. **Format normalization.** Models should be evaluated with tolerance for format variation (percentages vs. decimals, labeled vs. raw numbers) unless format precision is the specific skill being tested. Current strict-match grading likely understates model capability on calculation tasks by 5-10pp.

### For Benchmark Users

1. **Minimum sample size.** Category-level accuracy requires at least 15-20 problems per category for stable estimates. Results from smaller samples (like the n=4 expert results above) should be treated as directional, not definitive.

2. **Difficulty weighting.** Overall accuracy is a misleading single metric when difficulty distribution is non-uniform. A model that scores 95% on easy and 40% on hard may report 65% overall — the same as a model that scores 65% uniformly. Reporting accuracy by difficulty tier is more informative than a single number.

3. **Category portfolios.** Different use cases require different category mixes. An evaluation for "can this model assist with financial statement analysis?" should weight financial statement analysis and formula audit heavily. An evaluation for "can this model make investment judgments?" should weight DCF sanity check, catalyst identification, and risk assessment — the categories where models are weakest and where the answer matters most.
