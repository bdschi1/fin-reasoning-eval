<!-- SAMPLE_TASK.md | fin-reasoning-eval | Portable scenario walkthrough -->

# Sample Task: DCF Terminal Growth Sanity Check

A complete worked problem from this benchmark, presented end-to-end: prompt, correct answer with reasoning, grading rubric, three anchor responses at different quality levels, and metadata. This single file is self-contained and can be shared without the rest of the repo. The canonical source is `data/financial_reasoning_benchmark.json` (id `a90e1db94367`).

- **Category:** DCF Sanity Checks
- **Difficulty:** Hard
- **Answer type:** Multiple choice (1 of 4), weighted-binary rubric layered on top for reasoning quality
- **Target failure modes:** accepting perpetuity growth above long-run GDP, confusing nominal vs. real growth, waving through "growth company" narratives, treating sector-level multiples as terminal-growth validation
- **Estimated time for a human grader:** ~3 minutes

---

## 1. Scenario

### Context

| Field | Value |
|---|---|
| Company | Titan Resources (synthetic) |
| Ticker | TIRE |
| Sector | Materials |
| WACC | 10.9% |
| Terminal growth rate | 3.2% |
| Long-term GDP growth | 2.5% |
| Long-term inflation | 2.0% |

### Prompt

> A DCF model for Titan Resources uses a terminal growth rate of 3.2% with a WACC of 10.9%. Long-term GDP growth is 2.5% and inflation is 2.0%. Is this terminal growth rate reasonable?
>
> A. Borderline — 3.2% is slightly aggressive
> B. Valid — matches historical growth rate
> C. Valid — 3.2% is standard for Materials
> D. Invalid — growth must equal WACC

---

## 2. Gold answer

**Correct choice:** **A — Borderline; 3.2% is slightly aggressive.**

### Reasoning chain (ground truth)

1. Identify the terminal growth rate in the model: 3.2%.
2. Compare to long-term GDP growth (2.5%). A company's perpetuity growth cannot durably exceed the economy it operates in — otherwise it would eventually become larger than the economy itself.
3. Compare to inflation (2.0%). Implied real terminal growth ≈ 1.2%, which is not unreasonable on its own but leaves limited margin above the economy's real trend.
4. Conclude: 3.2% exceeds 2.5% GDP, so the assumption is borderline / slightly aggressive rather than outright invalid. It warrants a sensitivity check or downward bias in the base case, not rejection.

### Why the distractors are wrong

| Option | Why it fails |
|---|---|
| **B.** "Valid — matches historical growth rate" | Historical growth is not the relevant ceiling for perpetuity growth; GDP is. Conflates growth over an explicit forecast period with growth into perpetuity. |
| **C.** "Valid — 3.2% is standard for Materials" | A sector-average multiple or growth norm is not a sanity-check benchmark for terminal growth; the macroeconomic ceiling is. |
| **D.** "Invalid — growth must equal WACC" | Reverses the relationship. If `g = WACC` the Gordon formula blows up (denominator → 0). Terminal growth must be strictly less than WACC, not equal to it. |

---

## 3. Grading rubric

This benchmark layers a PRBench-style weighted binary rubric on top of the multiple-choice answer so the same problem measures both *what* a model answers and *how* it reasons. Full rubric definition at `evaluation/rubric_scoring.py:137`. For this problem the relevant categories and criteria are:

### Numerical accuracy (max 10)

| ID | Criterion | Weight |
|---|---|---|
| NA_001 | Final numerical/categorical answer correct | 3 |
| NA_004 | Percentages and ratios correctly compared (3.2% vs. 2.5% vs. 2.0%) | 2 |
| NA_005 | Growth rate computed relative to the correct base (real vs. nominal) | 1 |

### Conceptual understanding (max 8)

| ID | Criterion | Weight |
|---|---|---|
| CU_001 | Correctly identifies the governing concept: terminal growth ≤ long-run GDP | 3 |
| CU_002 | Distinguishes terminal growth (perpetuity) from explicit-period growth or historical growth | 2 |
| CU_003 | Applies the Gordon growth framework, not a multiples framework | 2 |
| CU_004 | Notes the `g < WACC` requirement (distractor D trap) | 1 |

### Reasoning chain (max 10)

| ID | Criterion | Weight |
|---|---|---|
| RC_001 | Reasoning steps follow a logical sequence | 3 |
| RC_002 | Each step is justified with an explicit comparison | 2 |
| RC_003 | Conclusion follows from the premises, not from the option label | 2 |
| RC_005 | Considers alternative explanations (e.g., inflation-only ceiling) before rejecting | 1 |

### Risk awareness (max 3)

| ID | Criterion | Weight |
|---|---|---|
| RA_001 | Flags the borderline nature as a sensitivity driver, not a binary pass/fail | 3 |

### Skill adherence — probabilistic language (max 2)

| ID | Criterion | Weight |
|---|---|---|
| SA_PROBABILISTIC | Avoids overconfident phrasing ("guaranteed", "100% correct", "cannot lose"); uses probabilistic language for the judgment | 2 |

**Max possible on this problem:** 33 points across 5 categories. Overall score is the weighted-binary sum normalized to [0, 100].

---

## 4. Anchor responses

### Strong (≈ 30/33)

> Terminal growth of 3.2% is slightly aggressive relative to the long-run GDP ceiling of 2.5%, so the assumption is borderline rather than invalid. Gordon-model perpetuity growth cannot durably exceed GDP without implying the firm eventually grows larger than its economy. Real implied growth (3.2% − 2.0% inflation ≈ 1.2%) is plausible in isolation, but above the real GDP trend. I would treat 3.2% as an upper-bound case and re-run the DCF at 2.0–2.5% for the base case, keeping 3.2% as a sensitivity. Answer: **A**.

- Correct answer + correct reasoning + borderline framing + sensitivity-driven next step.
- Likely criteria met: NA_001, NA_004, NA_005, CU_001, CU_002, CU_003, RC_001, RC_002, RC_003, RC_005, RA_001, SA_PROBABILISTIC.
- Likely miss: CU_004 (does not explicitly note `g < WACC`).

### Acceptable (≈ 20/33)

> The terminal growth rate of 3.2% is higher than GDP growth of 2.5%, so it is slightly aggressive. Answer: **A**.

- Correct answer but thin reasoning. No distinction between explicit-period and terminal growth, no sensitivity framing, no explicit comparison to inflation, no note on Gordon mechanics.
- Likely criteria met: NA_001, NA_004, CU_001, RC_001, RC_003.
- Likely miss: CU_002, CU_003, CU_004, RC_002, RC_005, RA_001, SA_PROBABILISTIC (too terse to score probabilistic-language criterion).

### Failing (≈ 6/33)

> 3.2% is in line with sector averages for Materials and matches the historical growth rate, so it looks reasonable. Answer: **C**.

- Wrong answer and the two dominant distractor traps (sector-average framing + historical-growth framing). Reasoning is fluent and confident but does not engage the perpetuity concept at all — the class of failure the benchmark is designed to catch.
- Likely criteria met: RC_001 (steps sequenced, even if wrong), CU_003 (acknowledges a framework, even if the wrong one).
- Likely miss: everything else, including NA_001 (wrong final answer).

---

## 5. Common mistakes this problem catches

From `data/financial_reasoning_benchmark.json` (field `common_mistakes`):

1. Accepting high terminal growth for "growth companies" — narrative substitutes for the GDP ceiling.
2. Ignoring the perpetuity implication of the terminal stage.
3. Confusing nominal vs. real growth when comparing to GDP and inflation.

The multiple-choice structure makes two of these directly selectable (distractors B and C), so models that pattern-match to sector/historical framing will be visibly miscategorized rather than hidden under free-text prose.

---

## 6. Metadata

| Field | Value |
|---|---|
| Problem ID | `a90e1db94367` |
| Category | `dcf_sanity_check` |
| Difficulty | `hard` |
| Answer type | `multiple_choice` |
| Partial credit | No |
| Max points (MC) | 1 |
| Max points (rubric overlay) | 33 |
| Source file | `data/financial_reasoning_benchmark.json` |
| Rubric definition | `evaluation/rubric_scoring.py:137` |
| Schema | `problems/schema.py` |

---

## How this scales across the benchmark

This is one of 360 problems across seven categories (earnings surprises, DCF sanity checks, accounting red flags, catalyst identification, formula audit, financial-statement analysis, risk assessment) and four difficulty levels (easy / medium / hard / expert). Each problem is authored to a uniform schema so that the same PRBench-style rubric (`evaluation/rubric_scoring.py`) can be layered on top of any problem, any category, any provider. See [`README.md`](README.md) for the full distribution and [`METHODOLOGY.md`](METHODOLOGY.md) for the design principles behind problem selection, difficulty calibration, and rubric structure.
