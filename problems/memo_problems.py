"""Phase-2 seed: five long-form memo problems.

Each entry pairs a 150-300 word analyst prompt with a hand-authored
gold-standard solution (400-800 words) and a PRBench-style binary
rubric. Authoring note: gold solutions are written by a practicing
buyside analyst and should be treated as a probabilistic consensus
view, not a single "right" answer — grading is on whether the memo
hits the rubric criteria, not on matching the solution verbatim.

The judge wiring (Phase 2 task) will load these via
``problems.memo_problems.MEMO_PROBLEMS`` and feed each problem's
rubric into ``evaluation.rubric_scoring.RubricGrader``. This module
intentionally uses plain dict records so it is importable without
depending on the full schema machinery and so Phase 2 can switch to
``dataclasses`` if convenient.

Known limitations:
- Only five problems here — one per core MC category except
  risk_assessment. Additional memo problems will land with the
  Phase 2 authoring pass (target 30).
- Gold solutions are single-author. Inter-rater review is planned
  before the external leaderboard includes memo scores.
"""

from __future__ import annotations

from typing import Any


def _criterion(criterion_id: str, text: str, weight: int = 1) -> dict[str, Any]:
    return {"id": criterion_id, "text": text, "weight": weight}


MEMO_PROBLEMS: list[dict[str, Any]] = [
    {
        "id": "memo_earnings_001",
        "category": "earnings_surprise",
        "difficulty": "hard",
        "answer_type": "free_text",
        "tags": ["memo", "earnings-quality", "guidance"],
        "question": (
            "Nordon Industries (NDON, industrials) reported Q3 2025 EPS of "
            "$1.42 vs. consensus $1.35 (a 5.2% beat) but cut full-year "
            "guidance from $5.60 to $5.30. Revenue came in light at "
            "$1.18B vs. $1.21B consensus (-2.5%). Gross margin expanded "
            "180 bps year-over-year, driven by a one-time favourable mix "
            "in the Aftermarket segment; management flagged softening "
            "orders in Europe. Write a 400-word memo to the buyside PM "
            "assessing whether the beat is high- or low-quality, "
            "reconciling it with the guidance cut, and recommending how "
            "to position the next quarter. Be explicit about what you "
            "would monitor."
        ),
        "context": (
            "Company: Nordon Industries (NDON)\n"
            "Sector: Industrials — diversified machinery\n"
            "Q3 2025 results:\n"
            "  Revenue: $1.18B (consensus $1.21B, -2.5%)\n"
            "  GAAP EPS: $1.42 (consensus $1.35, +5.2%)\n"
            "  Gross margin: 34.1% vs. 32.3% YoY; +180 bps driven by\n"
            "    favourable mix (Aftermarket up 9% YoY, OEM down 4%).\n"
            "  Operating expenses flat.\n"
            "Guidance:\n"
            "  FY25 EPS lowered from $5.60 to $5.30 (-5.4%).\n"
            "  Management cited softening European orders and a FX\n"
            "  headwind of $0.15/share.\n"
            "Balance sheet: Net cash positive, no covenant issues.\n"
            "Buyside position: long 150 bps vs. benchmark 80 bps."
        ),
        "gold_solution": (
            "The Q3 beat is low-quality and should not be extrapolated. "
            "EPS topped consensus largely because Aftermarket mix "
            "lifted gross margin by 180 bps, but Aftermarket strength "
            "typically reflects in-service equipment rather than new "
            "orders — it is a slow-moving pool that can persist for a "
            "few quarters and then normalise as OEM shipments catch "
            "up or as customers defer service. The revenue miss is the "
            "more important signal: a 2.5% shortfall on the top line "
            "in an industrials name with operating leverage usually "
            "means forward earnings power is being overstated by the "
            "current margin print. The FY25 guidance cut of -5.4% is "
            "directionally consistent with this read — management is "
            "telling us Q3's margin tailwind will not persist and "
            "Europe is weakening.\n\n"
            "The reconciliation is straightforward: a one-time mix "
            "benefit pushed Q3 EPS above the run-rate implied by "
            "guidance. Stripping out the mix tailwind (180 bps on ~34% "
            "gross margin is roughly $0.12 of EPS) leaves Q3 closer to "
            "consensus than the headline suggests. The new $5.30 FY "
            "number implies Q4 EPS of roughly $1.15 vs. prior buy-side "
            "expectations of ~$1.35 — call it a 15% cut to the "
            "quarterly run-rate. FX is a real but small component at "
            "$0.15 for the year; the rest is demand.\n\n"
            "Position recommendation: trim the overweight from 150 bps "
            "to 80-100 bps into the print-day rally that is likely to "
            "fade over the next few sessions. Do not exit — the "
            "balance sheet is clean, the Aftermarket franchise has "
            "defensive qualities, and the European order trend could "
            "stabilise. But the stock will likely re-rate on the "
            "guidance cut rather than the beat once the mix story is "
            "understood.\n\n"
            "What to monitor next quarter: (1) European order-book "
            "growth; (2) Aftermarket-to-OEM revenue ratio — a rising "
            "ratio without OEM recovery signals customers are "
            "stretching service cycles, which is a late-cycle warning; "
            "(3) gross-margin sustainability ex-mix — the 180 bps is "
            "the variable to watch; (4) free cash flow conversion, as "
            "a weakening order book should show up in working capital "
            "before it shows up in reported earnings. If any two of "
            "those deteriorate, cut to benchmark weight."
        ),
        "rubric": [
            _criterion(
                "MEM-EAR-01",
                "Explicitly labels the beat as low-quality or flags "
                "the mix tailwind as non-recurring.",
                2,
            ),
            _criterion(
                "MEM-EAR-02",
                "Reconciles the EPS beat with the guidance cut rather "
                "than treating them as contradictory.",
                2,
            ),
            _criterion(
                "MEM-EAR-03",
                "Identifies gross-margin mix (Aftermarket vs. OEM) as "
                "the primary driver of the beat.",
                1,
            ),
            _criterion(
                "MEM-EAR-04",
                "References the revenue miss as a leading indicator "
                "rather than the EPS beat.",
                1,
            ),
            _criterion(
                "MEM-EAR-05",
                "Gives a position recommendation that is concrete "
                "(e.g. trim, add, hold with size).",
                2,
            ),
            _criterion(
                "MEM-EAR-06",
                "Names at least two specific metrics to monitor next "
                "quarter (orders, margin, FCF, segment mix).",
                1,
            ),
            _criterion(
                "MEM-EAR-07",
                "Avoids overconfident language (no 'definitely', "
                "'guaranteed', 'certain').",
                1,
            ),
        ],
    },
    {
        "id": "memo_dcf_001",
        "category": "dcf_sanity_check",
        "difficulty": "expert",
        "answer_type": "free_text",
        "tags": ["memo", "dcf", "terminal-value"],
        "question": (
            "A junior analyst hands you a DCF model for ClearCove "
            "Software (CCOV, vertical SaaS). The explicit period is "
            "five years. Year-1 FCF is $80M, growing at 25% in year 1, "
            "20% in year 2, 15% in years 3-4, and 12% in year 5. "
            "Terminal growth rate is 5%. WACC is 8.5%. The model "
            "produces an enterprise value of $7.4B — a 62% premium to "
            "the current market cap. Write a 400-word memo explaining "
            "whether you would stand behind the output and what you "
            "would change before submitting to the PM."
        ),
        "context": (
            "Company: ClearCove Software (CCOV)\n"
            "Sector: Vertical SaaS — logistics vertical\n"
            "Current market cap: $4.6B\n"
            "DCF inputs:\n"
            "  FCF Year 1: $80M\n"
            "  Growth: 25%, 20%, 15%, 15%, 12%\n"
            "  Terminal growth: 5.0%\n"
            "  WACC: 8.5%\n"
            "  EV output: $7.4B (+62% vs. market)\n"
            "Reference: 10-year Treasury 4.3%; long-run US GDP ~4-5% nominal."
        ),
        "gold_solution": (
            "I would not sign off on this output. Two inputs are "
            "individually defensible but jointly implausible, and the "
            "62% premium to market cap is largely an artifact of that "
            "interaction rather than a view on the business.\n\n"
            "First, the terminal growth of 5% is at the absolute top of "
            "the reasonable range. US long-run nominal GDP growth is "
            "roughly 4-5%, and a perpetuity growth rate at the high end "
            "of GDP is saying the company captures a constant share of "
            "the economy forever. For vertical SaaS, where TAM is "
            "finite and competitive structure erodes pricing power over "
            "decades, 2.5-3.5% is more realistic. Dropping the terminal "
            "to 3.0% on an 8.5% WACC reduces the terminal multiple from "
            "1/(0.085-0.05) = 28.6x to 1/(0.085-0.03) = 18.2x — a 36% "
            "cut in terminal value alone. Terminal value is where most "
            "of this DCF's equity value sits, so the sensitivity is "
            "enormous.\n\n"
            "Second, WACC at 8.5% feels low for a software name against "
            "a 4.3% risk-free rate. For a SaaS company with an equity "
            "beta in the 1.2-1.4 range and an equity risk premium of "
            "5-5.5%, cost of equity lands at roughly 11-12%. Unless the "
            "company has meaningful debt (uncommon for SaaS at this "
            "cap), WACC should be closer to 10-11%. Moving WACC to 10% "
            "with terminal at 3% pushes the terminal multiple to ~14x — "
            "roughly half of what the model currently implies.\n\n"
            "Third, the explicit-period growth stack (25% → 12% over "
            "five years) is aggressive but not crazy for vertical SaaS "
            "with a strong land-and-expand motion. That is where I "
            "would push back least. However, the handoff between year "
            "5's 12% and terminal 5% is too abrupt; a fade period of "
            "three to five years stepping down from 12% to 4% is more "
            "defensible.\n\n"
            "Revised view: with terminal 3%, WACC 10%, and a three-year "
            "fade, EV likely lands closer to $4.8-5.2B — a 5-15% "
            "premium to the current market, which is a reasonable place "
            "to sit for a quality SaaS name but not a screaming buy. I "
            "would ask the junior to re-run with a WACC/g tornado and "
            "highlight that the 62% premium in the original model is "
            "mostly a discount-rate story, not a growth story."
        ),
        "rubric": [
            _criterion(
                "MEM-DCF-01",
                "Rejects the output or explicitly flags terminal value "
                "as the dominant driver of the implied premium.",
                2,
            ),
            _criterion(
                "MEM-DCF-02",
                "Argues the 5% terminal growth is too high and "
                "benchmarks against GDP / long-run economy.",
                2,
            ),
            _criterion(
                "MEM-DCF-03",
                "Questions the 8.5% WACC as too low given a risk-free "
                "rate of 4.3% and a SaaS-typical equity beta.",
                2,
            ),
            _criterion(
                "MEM-DCF-04",
                "Identifies the WACC-minus-g spread as the mechanical "
                "lever (terminal multiple math).",
                2,
            ),
            _criterion(
                "MEM-DCF-05",
                "Suggests a fade or step-down between explicit and "
                "terminal growth.",
                1,
            ),
            _criterion(
                "MEM-DCF-06",
                "Produces a revised valuation range rather than a "
                "single number.",
                1,
            ),
            _criterion(
                "MEM-DCF-07",
                "Avoids overconfident language (no claim the model is "
                "definitely wrong — probabilistic framing).",
                1,
            ),
        ],
    },
    {
        "id": "memo_accounting_001",
        "category": "accounting_red_flag",
        "difficulty": "hard",
        "answer_type": "free_text",
        "tags": ["memo", "revenue-recognition", "accruals"],
        "question": (
            "Helion Materials (HELN, specialty chemicals) reports 12% "
            "YoY revenue growth in FY24, up from 4% in FY23. DSO "
            "(days-sales-outstanding) has risen from 58 days to 81 "
            "days over the same period. Inventory turns have declined "
            "from 6.2x to 4.8x. Operating cash flow is roughly flat "
            "year over year despite the reported revenue and EPS "
            "acceleration. The company recently adopted a new "
            "customer-financing program that allows channel partners "
            "to defer payment by up to 120 days. Write a 400-word "
            "memo assessing whether the accounting signals warrant "
            "further investigation and what you would flag to the PM."
        ),
        "context": (
            "Company: Helion Materials (HELN)\n"
            "Sector: Specialty chemicals\n"
            "FY24: Revenue +12% YoY (prior: +4%), EPS +18% YoY.\n"
            "DSO: 58 → 81 days (+40%).\n"
            "Inventory turns: 6.2x → 4.8x.\n"
            "Operating cash flow: essentially flat YoY.\n"
            "New program: channel-partner financing, up to 120-day terms.\n"
            "Ratings: Investment grade; no downgrade actions."
        ),
        "gold_solution": (
            "The pattern is consistent with pull-forward revenue "
            "through channel financing and should be treated as a "
            "yellow-to-red flag pending management follow-up. None of "
            "these signals in isolation proves aggressive accounting, "
            "but their combination is the classic setup analysts see "
            "before a revenue reset.\n\n"
            "DSO moving from 58 to 81 days is a 40% jump and is "
            "materially larger than the 12% revenue growth — in a "
            "mechanical sense, receivables are growing more than three "
            "times faster than sales. The customer-financing program "
            "is the likely explanation and, on its face, is a "
            "legitimate commercial tool. The problem is that extending "
            "credit terms effectively turns a sale into a lending "
            "decision: the company is booking revenue today on "
            "receivables it will collect 120 days later. If the channel "
            "cannot absorb the volume at those terms, returns and "
            "credit losses will appear in FY25 or FY26, and the "
            "growth acceleration reverses.\n\n"
            "Inventory turns dropping from 6.2x to 4.8x is the second "
            "corroborating data point. Faster revenue growth with "
            "slower inventory turns means product is sitting on shelves "
            "longer — either in the company's own warehouses or in "
            "channel-partner hands. Combined with the financing "
            "program, this raises the question of whether sell-in has "
            "run ahead of sell-through. The third data point — flat "
            "operating cash flow against accelerating reported EPS — "
            "closes the loop. Accrual-based earnings are rising while "
            "cash-based earnings are not, which is exactly the "
            "divergence that channel stuffing produces.\n\n"
            "What I would flag to the PM: treat reported revenue and "
            "EPS growth as probably overstated versus sustainable "
            "trend. Request three items from IR before the next print: "
            "(1) a reconciliation of the receivables build between "
            "volume growth, mix, and the new financing program; "
            "(2) channel-inventory data if the company tracks it, or a "
            "sell-in vs. sell-through commentary; (3) specific allowance-"
            "for-doubtful-accounts movements given the 120-day terms. "
            "Sizing: if we own the name, trim 30-50% pending the next "
            "cash-flow print; if we do not own it, this is not the "
            "entry point. The asymmetry is poor — upside is priced in, "
            "downside is a revenue-quality reset."
        ),
        "rubric": [
            _criterion(
                "MEM-ACC-01",
                "Explicitly flags DSO expansion as disproportionate to "
                "revenue growth.",
                2,
            ),
            _criterion(
                "MEM-ACC-02",
                "Connects the customer-financing program to the "
                "receivables build.",
                2,
            ),
            _criterion(
                "MEM-ACC-03",
                "Identifies the reported-earnings vs. operating-cash-"
                "flow divergence as a key signal.",
                2,
            ),
            _criterion(
                "MEM-ACC-04",
                "References inventory-turn deceleration as a "
                "corroborating data point.",
                1,
            ),
            _criterion(
                "MEM-ACC-05",
                "Uses the phrase channel stuffing, pull-forward, or "
                "sell-in vs. sell-through concept.",
                1,
            ),
            _criterion(
                "MEM-ACC-06",
                "Makes a concrete follow-up request (IR questions, "
                "disclosures, additional data).",
                2,
            ),
            _criterion(
                "MEM-ACC-07",
                "Frames conclusion probabilistically (e.g. 'warrants "
                "investigation', 'likely', not 'certainly').",
                1,
            ),
        ],
    },
    {
        "id": "memo_catalyst_001",
        "category": "catalyst_identification",
        "difficulty": "hard",
        "answer_type": "free_text",
        "tags": ["memo", "catalyst", "event-driven"],
        "question": (
            "Aurora Biotech (AURB) has three near-term catalysts: "
            "(a) a Phase-3 readout on its lead oncology asset in six "
            "weeks, with consensus probability of success around 55% "
            "and a market-expected 35-45% stock move; "
            "(b) a Q4 earnings release in four weeks where the "
            "company will guide on 2026 opex for the next wave of "
            "trials; (c) an FDA Advisory Committee meeting on a "
            "secondary indication in ten weeks. Short interest is "
            "14% of float. The stock is up 22% in the last month on "
            "rumour flow around the Phase-3. Write a 400-word memo "
            "ranking these catalysts by risk-adjusted impact and "
            "recommending how to position."
        ),
        "context": (
            "Company: Aurora Biotech (AURB)\n"
            "Sector: Mid-cap biotech, oncology focus\n"
            "Near-term catalysts:\n"
            "  1. Phase-3 oncology readout — ~6 weeks, 55% POS,\n"
            "     expected 35-45% move either way.\n"
            "  2. Q4 earnings + 2026 opex guide — ~4 weeks.\n"
            "  3. FDA AdCom on secondary indication — ~10 weeks.\n"
            "Short interest: 14% of float.\n"
            "Recent trading: stock +22% in last month on unconfirmed\n"
            "  Phase-3 leaks / rumours."
        ),
        "gold_solution": (
            "Ranked by risk-adjusted impact, the Phase-3 readout "
            "dominates but is the most crowded and the most asymmetric-"
            "looking; the AdCom and Q4 earnings are second-order but "
            "drive stock-specific opex optics that matter for next-year "
            "modelling. My recommendation is to trade around the "
            "Phase-3 rather than hold through it, and to use the "
            "AdCom window for a residual position.\n\n"
            "Phase-3 first. A 55% POS with a 35-45% symmetric-looking "
            "move sounds attractive on expected-value math, but three "
            "things erode the edge. One, the 22% run into the print "
            "means a meaningful fraction of the upside is already in "
            "the stock; success cases often underwhelm after heavy "
            "pre-data positioning. Two, 14% short interest suggests "
            "the market disagrees — any leak that the readout is "
            "positive could short-squeeze ahead of the event, further "
            "de-risking the up-scenario. Three, consensus POS numbers "
            "in biotech are notoriously anchored to management "
            "communication; 55% is close to the default-neutral value "
            "and should not be treated as precise. Trading through the "
            "event with size is a coin-flip dressed up as a "
            "probability bet.\n\n"
            "Q4 earnings in four weeks is second-most important because "
            "2026 opex guidance determines cash runway and therefore "
            "the size and timing of a dilutive raise. A higher-than-"
            "expected opex guide alone could erase 10-15% of the "
            "recent rally regardless of the trial outcome. This "
            "catalyst is under-appreciated relative to the binary "
            "readout but affects every downside scenario.\n\n"
            "The AdCom on the secondary indication is a distant third. "
            "Moves on AdComs for secondary indications are typically "
            "10-20% unless the panel is hostile. It is worth monitoring "
            "but not worth pre-positioning for.\n\n"
            "Positioning recommendation: trim roughly half of any "
            "existing position before the Q4 print, not after, to "
            "avoid being forced to react to the opex guide with "
            "Phase-3 risk still in front of us. Keep enough exposure "
            "to participate in an upside readout but not enough to be "
            "crushed by a negative one. If the Phase-3 is positive and "
            "we retain a half-position, re-underwrite into the AdCom "
            "window. If it is negative, exit quickly — secondary-"
            "indication AdComs are rarely enough to rescue a failed "
            "primary asset in mid-cap biotech. Do not add into the "
            "Phase-3; the payoff has been compressed by positioning."
        ),
        "rubric": [
            _criterion(
                "MEM-CAT-01",
                "Ranks the three catalysts by risk-adjusted impact, "
                "not by raw size.",
                2,
            ),
            _criterion(
                "MEM-CAT-02",
                "References crowding, short interest, or recent price "
                "action as reasons the Phase-3 edge is smaller than it "
                "appears.",
                2,
            ),
            _criterion(
                "MEM-CAT-03",
                "Identifies the Q4 opex guide / runway as a distinct "
                "near-term driver, not just earnings noise.",
                2,
            ),
            _criterion(
                "MEM-CAT-04",
                "Acknowledges POS numbers in biotech are approximate "
                "(do not treat 55% as precise).",
                1,
            ),
            _criterion(
                "MEM-CAT-05",
                "Gives a concrete pre-event position change (e.g. trim "
                "before Q4, not after).",
                2,
            ),
            _criterion(
                "MEM-CAT-06",
                "Includes a post-readout contingency (what to do in "
                "success vs. failure cases).",
                1,
            ),
            _criterion(
                "MEM-CAT-07",
                "Avoids overconfident framing — uses probabilistic, "
                "not deterministic language.",
                1,
            ),
        ],
    },
    {
        "id": "memo_fsa_001",
        "category": "financial_statement_analysis",
        "difficulty": "hard",
        "answer_type": "free_text",
        "tags": ["memo", "ratio-analysis", "margin-trend"],
        "question": (
            "Tempest Apparel (TMPA, mid-cap discretionary) shows the "
            "following trailing three-year trend: gross margin 44% → "
            "41% → 39%; operating margin 14% → 11% → 9%; revenue "
            "growth 8% → 5% → 3%; inventory-to-sales ratio 18% → 22% "
            "→ 27%; and capex as a share of sales 5% → 3% → 2%. Free "
            "cash flow has held roughly flat in dollars. Write a "
            "400-word memo diagnosing the underlying story and "
            "recommending what you would price in."
        ),
        "context": (
            "Company: Tempest Apparel (TMPA)\n"
            "Three-year ratio trend (FY22 → FY23 → FY24):\n"
            "  Gross margin: 44% → 41% → 39%\n"
            "  Operating margin: 14% → 11% → 9%\n"
            "  Revenue growth: 8% → 5% → 3%\n"
            "  Inventory/sales: 18% → 22% → 27%\n"
            "  Capex/sales: 5% → 3% → 2%\n"
            "  FCF $: roughly flat\n"
            "Sector: Apparel / discretionary retail"
        ),
        "gold_solution": (
            "The ratio trend reads as a brand in structural decline "
            "being mitigated by cash-flow management rather than by "
            "operating improvement. Three data points anchor that "
            "view: margin compression at both the gross and operating "
            "line, decelerating revenue growth, and rising "
            "inventory-to-sales — a combination that is very hard to "
            "interpret as anything other than weaker pricing power and "
            "excess production.\n\n"
            "Gross margin down 500 bps over three years in apparel is "
            "large. If input costs were the driver, we would expect it "
            "to reverse as cotton and freight normalised. That it has "
            "continued to compress while the industry reset suggests "
            "the issue is pricing power and promotional activity, not "
            "input costs. Operating margin falling 500 bps in step "
            "with gross margin means SG&A has not been cut — fixed "
            "costs are dragging more as volume decelerates. Revenue "
            "growth going from 8% to 3% on a base that is not very "
            "large is not just a maturity story; apparel peers "
            "growing in low-double-digits over the same window would "
            "suggest share loss.\n\n"
            "Inventory-to-sales rising from 18% to 27% is the biggest "
            "flag. That is 50% growth in stockholding relative to "
            "sell-through. Two possibilities: management is betting "
            "the next cycle will turn and is building for it "
            "(low-probability bet in a declining brand), or "
            "sell-through is meaningfully worse than reported revenue "
            "implies because retailers have held orders while "
            "company-owned inventory has built. Either way, an "
            "inventory markdown is highly likely within 12-18 months, "
            "further pressuring gross margin.\n\n"
            "Capex falling from 5% of sales to 2% and FCF holding flat "
            "is the 'managed decline' part of the story. Management "
            "is converting a declining business into a cash-flow story "
            "by under-investing — the stock may look attractive on "
            "FCF yield but the capex line is borrowed from future "
            "competitiveness. Store fleets age; digital infrastructure "
            "falls behind; brand marketing spend tends to follow.\n\n"
            "What I would price in: the stock likely trades at a "
            "melting-ice-cube multiple unless the inventory glut is "
            "cleared without significant gross-margin damage. A "
            "value-investor narrative on 'FCF yield is X%' should be "
            "discounted — the free cash flow is not sustainable at "
            "the current capex level, and the inventory position "
            "implies a one- to two-year earnings reset is still ahead. "
            "I would not own this without a clean inventory print "
            "and evidence of a credible brand-repositioning plan."
        ),
        "rubric": [
            _criterion(
                "MEM-FSA-01",
                "Diagnoses margin compression as structural (pricing "
                "power / mix) rather than input-cost cyclical.",
                2,
            ),
            _criterion(
                "MEM-FSA-02",
                "Flags inventory-to-sales expansion as the most "
                "concerning ratio.",
                2,
            ),
            _criterion(
                "MEM-FSA-03",
                "Notes the capex-decline / FCF-flat combination as "
                "managed decline or under-investment.",
                2,
            ),
            _criterion(
                "MEM-FSA-04",
                "Connects share loss to decelerating revenue vs. peers.",
                1,
            ),
            _criterion(
                "MEM-FSA-05",
                "Forecasts an inventory markdown or gross-margin "
                "reset in the following year.",
                1,
            ),
            _criterion(
                "MEM-FSA-06",
                "Rejects a simple 'FCF yield = value' framing by "
                "pointing to capex sustainability.",
                2,
            ),
            _criterion(
                "MEM-FSA-07",
                "Avoids overconfident language — frames decline as "
                "probable, not guaranteed.",
                1,
            ),
        ],
    },
]


def get_memo_problems() -> list[dict[str, Any]]:
    """Return the list of memo problems.

    Thin wrapper so Phase-2 judge wiring can import a stable function
    name rather than reaching into module state.
    """
    return MEMO_PROBLEMS


def get_memo_problem(problem_id: str) -> dict[str, Any]:
    for p in MEMO_PROBLEMS:
        if p["id"] == problem_id:
            return p
    raise KeyError(problem_id)
