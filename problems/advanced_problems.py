"""
Curated Finance Reasoning Problems - Advanced Concepts

30 in-depth problems covering:
- Alpha/beta separation
- Factor models
- Sizing and risk decomposition
- Hedging and leverage
- Performance attribution

These problems require deeper reasoning about portfolio construction,
factor exposure, and the separation of idiosyncratic vs. systematic returns.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from problems.schema import (
    Problem,
    ProblemCategory,
    Difficulty,
    AnswerType,
    FinancialContext,
    AnswerOption,
)


def generate_advanced_problems() -> list[Problem]:
    """Generate 30 curated advanced concept problems."""
    problems = []

    # =========================================================================
    # I. EARNINGS SURPRISES (5 problems)
    # =========================================================================

    # 1. Earnings Beat with Negative Alpha
    problems.append(Problem(
        id="adv_es_001",
        category=ProblemCategory.EARNINGS_SURPRISE,
        difficulty=Difficulty.HARD,
        question="""A company reports EPS 8% above consensus. The stock gaps up 6% on the day. Over the next 10 trading days, the stock underperforms its industry benchmark by 4%.

Decompose the initial reaction vs. subsequent performance using alpha/beta logic. Was the earnings beat evidence of positive alpha?""",
        context=FinancialContext(
            company_name="Alpha Analytics Corp",
            ticker="AALC",
            sector="Technology",
            eps={"Actual": 2.16, "Consensus": 2.00},
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="No - the initial reaction reflected beta/market sentiment, and subsequent underperformance indicates no lasting idiosyncratic alpha",
        answer_options=[
            AnswerOption(id="A", text="Yes - the 8% EPS beat proves positive alpha generation", is_correct=False),
            AnswerOption(id="B", text="Yes - the 6% gap-up captured the alpha, subsequent moves are noise", is_correct=False),
            AnswerOption(id="C", text="No - the initial reaction reflected beta/market sentiment, and subsequent underperformance indicates no lasting idiosyncratic alpha", is_correct=True),
            AnswerOption(id="D", text="Inconclusive - need factor attribution data", is_correct=False),
        ],
        explanation="The initial 6% gap represents market reaction (potentially beta-driven if the market rallied). The 4% subsequent underperformance relative to the benchmark suggests the 'beat' was already priced in or that idiosyncratic factors turned negative. True alpha would persist or accumulate post-announcement.",
        reasoning_steps=[
            "Separate initial price reaction from subsequent drift",
            "Compare to benchmark to isolate idiosyncratic component",
            "Recognize that earnings beats don't guarantee alpha if expectations were already embedded",
            "Net result: +6% initial, -4% relative drift = modest net outperformance that may be within noise"
        ],
        tags=["alpha-beta", "earnings-drift", "factor-separation", "advanced-concepts"],
    ))

    # 2. Guidance vs. Earnings Signal Conflict
    problems.append(Problem(
        id="adv_es_002",
        category=ProblemCategory.EARNINGS_SURPRISE,
        difficulty=Difficulty.EXPERT,
        question="""A company beats EPS by 5% but lowers full-year revenue guidance by 3%. The stock sells off 4%.

Under what conditions is the market reaction rational? Identify which component (short-term alpha vs. long-term cash flow expectations) dominates.""",
        context=FinancialContext(
            company_name="Guidance Dynamics Inc",
            ticker="GDYN",
            sector="Industrials",
            eps={"Q3 Actual": 1.05, "Q3 Consensus": 1.00},
            guidance="Full-year revenue guidance lowered from $4.2B to $4.07B (-3%)",
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Long-term cash flow expectations dominate - markets discount future earnings, so lowered guidance impacts terminal value more than a single quarter beat",
        answer_options=[
            AnswerOption(id="A", text="Irrational - a 5% beat should outweigh 3% guidance cut", is_correct=False),
            AnswerOption(id="B", text="Long-term cash flow expectations dominate - markets discount future earnings, so lowered guidance impacts terminal value more than a single quarter beat", is_correct=True),
            AnswerOption(id="C", text="Short-term alpha dominates - market overreacting to guidance", is_correct=False),
            AnswerOption(id="D", text="The reaction reflects increased beta exposure, not fundamentals", is_correct=False),
        ],
        explanation="In a DCF framework, terminal value often comprises 60-80% of enterprise value. A 3% revenue guidance cut, if persistent, compounds into significantly lower terminal value. A single quarter's 5% EPS beat adds minimal incremental value. The market correctly prices the longer-duration negative signal.",
        reasoning_steps=[
            "Compare one-time EPS beat impact vs. perpetual guidance reduction",
            "Apply DCF logic: terminal value dominates intrinsic value",
            "Recognize guidance as forward-looking vs. earnings as backward-looking",
            "Market's -4% reaction is rational if guidance cut implies structural issues"
        ],
        tags=["guidance", "dcf-logic", "signal-conflict", "advanced-concepts"],
    ))

    # 3. Earnings Surprise in a High-Beta Name
    problems.append(Problem(
        id="adv_es_003",
        category=ProblemCategory.EARNINGS_SURPRISE,
        difficulty=Difficulty.HARD,
        question="""Two companies both beat earnings by 10%. Company A has beta 0.6; Company B has beta 1.8. During the earnings window, the market rallies 3%.

How should you adjust the observed returns to assess which company delivered more idiosyncratic alpha?""",
        context=FinancialContext(
            company_name="Comparison Analysis",
            ticker="N/A",
            sector="Multiple",
            model_assumptions={
                "Company A beta": 0.6,
                "Company B beta": 1.8,
                "Market return": "3%",
                "EPS beat (both)": "10%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Subtract beta-adjusted market contribution: A's expected beta return = 1.8% (0.6 x 3%), B's = 5.4% (1.8 x 3%). Alpha = actual return minus these amounts.",
        answer_options=[
            AnswerOption(id="A", text="No adjustment needed - both beat by 10% so both generated equal alpha", is_correct=False),
            AnswerOption(id="B", text="Subtract beta-adjusted market contribution: A's expected beta return = 1.8% (0.6 x 3%), B's = 5.4% (1.8 x 3%). Alpha = actual return minus these amounts.", is_correct=True),
            AnswerOption(id="C", text="Divide returns by beta to normalize", is_correct=False),
            AnswerOption(id="D", text="High-beta names always generate more alpha during rallies", is_correct=False),
        ],
        explanation="Using CAPM: Expected return = beta x market return. Company A's beta contribution = 0.6 x 3% = 1.8%. Company B's = 1.8 x 3% = 5.4%. If both stocks rose 12% on earnings, A generated 10.2% alpha (12% - 1.8%) while B generated only 6.6% alpha (12% - 5.4%). The earnings beat's alpha component differs significantly.",
        reasoning_steps=[
            "Calculate expected return from market exposure: beta x market return",
            "Subtract market contribution from total return to isolate alpha",
            "Compare idiosyncratic returns between the two companies",
            "Lower-beta stocks with same total return delivered more alpha"
        ],
        tags=["beta-adjustment", "capm", "alpha-isolation", "advanced-concepts"],
    ))

    # 4. Earnings Drift vs. Factor Exposure
    problems.append(Problem(
        id="adv_es_004",
        category=ProblemCategory.EARNINGS_SURPRISE,
        difficulty=Difficulty.EXPERT,
        question="""Post-earnings, a stock exhibits positive drift for 30 days. Factor analysis shows increasing momentum and volatility exposure during the same period.

How do you distinguish earnings-driven alpha from factor-driven returns?""",
        context=FinancialContext(
            company_name="Drift Analytics Corp",
            ticker="DRFT",
            sector="Technology",
            recent_news=[
                "Stock up 15% over 30 days post-earnings",
                "Momentum factor up 8% same period",
                "Volatility factor up 4% same period",
                "Company beat earnings by 12%"
            ]
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Run multi-factor regression to decompose returns into factor contributions and residual. True earnings alpha is the unexplained residual after controlling for momentum, volatility, and other factors.",
        answer_options=[
            AnswerOption(id="A", text="All 30-day drift is earnings alpha since it started at the announcement", is_correct=False),
            AnswerOption(id="B", text="Run multi-factor regression to decompose returns into factor contributions and residual. True earnings alpha is the unexplained residual after controlling for momentum, volatility, and other factors.", is_correct=True),
            AnswerOption(id="C", text="Factor exposures are irrelevant for earnings-driven stocks", is_correct=False),
            AnswerOption(id="D", text="Compare to sector benchmark only - factors don't apply to single stocks", is_correct=False),
        ],
        explanation="Post-earnings drift can coincide with the stock loading onto momentum (as winners attract momentum investors) and volatility factors. A proper attribution requires regressing returns on factor returns: R = alpha + beta_mkt*MKT + beta_mom*MOM + beta_vol*VOL + epsilon. The alpha term represents true idiosyncratic earnings effect.",
        reasoning_steps=[
            "Recognize that drift timing doesn't prove causation",
            "Factor loadings can change post-event as the stock attracts different investors",
            "Multi-factor regression isolates idiosyncratic component",
            "Residual after factor adjustment = true earnings-driven alpha"
        ],
        tags=["factor-attribution", "momentum", "volatility-factor", "regression", "advanced-concepts"],
    ))

    # 5. Consensus Compression Before Earnings
    problems.append(Problem(
        id="adv_es_005",
        category=ProblemCategory.EARNINGS_SURPRISE,
        difficulty=Difficulty.HARD,
        question="""Short interest declines sharply in the month leading up to earnings, and sell-side dispersion narrows. Earnings are in-line. The stock drops 5%.

Explain the result using crowding and expectation formation.""",
        context=FinancialContext(
            company_name="Crowded Trade Inc",
            ticker="CRWD",
            sector="Consumer Discretionary",
            recent_news=[
                "Short interest declined from 15% to 5% of float",
                "Analyst estimate range narrowed from $1.20-$1.80 to $1.45-$1.55",
                "Actual EPS: $1.50 (exactly at consensus midpoint)",
                "Stock declined 5% post-announcement"
            ]
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Declining shorts + narrowing dispersion = crowded long positioning with elevated expectations. In-line results disappointed the embedded bullish consensus, triggering de-crowding.",
        answer_options=[
            AnswerOption(id="A", text="Market is irrational - in-line results shouldn't cause a decline", is_correct=False),
            AnswerOption(id="B", text="Declining shorts + narrowing dispersion = crowded long positioning with elevated expectations. In-line results disappointed the embedded bullish consensus, triggering de-crowding.", is_correct=True),
            AnswerOption(id="C", text="The decline is pure factor rotation unrelated to earnings", is_correct=False),
            AnswerOption(id="D", text="Short covering always leads to post-earnings declines", is_correct=False),
        ],
        explanation="When short interest falls dramatically and analyst estimates converge, it signals that bearish views have been squeezed out and expectations have risen. The 'true' expectation is higher than the published consensus. In-line results then represent a disappointment vs. the crowded positioning, causing longs to exit.",
        reasoning_steps=[
            "Short interest decline = bears capitulating, removing downside protection",
            "Estimate dispersion narrowing = consensus forming around optimistic view",
            "Published consensus understates true market expectation",
            "In-line results disappoint the elevated actual expectation",
            "Crowded longs exit, causing the 5% decline"
        ],
        tags=["crowding", "expectation-formation", "short-interest", "dispersion", "advanced-concepts"],
    ))

    # =========================================================================
    # II. DCF SANITY CHECKS (5 problems)
    # =========================================================================

    # 6. Terminal Growth vs. Market Beta
    problems.append(Problem(
        id="adv_dcf_001",
        category=ProblemCategory.DCF_SANITY,
        difficulty=Difficulty.HARD,
        question="""A DCF assumes terminal growth of 4% for a company with beta 1.7 operating in a mature industry.

Why is this internally inconsistent? What implicit macro assumptions are being made?""",
        context=FinancialContext(
            company_name="High Beta Mature Co",
            ticker="HBMC",
            sector="Industrials",
            wacc=12.0,
            terminal_growth=4.0,
            model_assumptions={
                "Beta": 1.7,
                "Industry growth": "2% (mature)",
                "Risk-free rate": "4%",
                "Equity risk premium": "5%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="High beta implies cyclicality and economic sensitivity. Terminal growth of 4% (above GDP) with beta 1.7 implies the company grows faster than the economy while being more volatile - inconsistent for a mature industry.",
        answer_options=[
            AnswerOption(id="A", text="No inconsistency - beta and growth rate are independent", is_correct=False),
            AnswerOption(id="B", text="High beta implies cyclicality and economic sensitivity. Terminal growth of 4% (above GDP) with beta 1.7 implies the company grows faster than the economy while being more volatile - inconsistent for a mature industry.", is_correct=True),
            AnswerOption(id="C", text="Terminal growth should always equal risk-free rate", is_correct=False),
            AnswerOption(id="D", text="Beta only affects WACC, not terminal growth assumptions", is_correct=False),
        ],
        explanation="A beta of 1.7 signals high economic sensitivity - the company amplifies market moves. In a mature industry, this typically means cyclical swings around a low-growth trend. Assuming 4% perpetual growth (above typical 2-3% nominal GDP) while also assuming high beta creates a contradiction: the company would need to consistently outgrow the economy it's supposedly tethered to.",
        reasoning_steps=[
            "High beta = high sensitivity to economic cycles",
            "Mature industry = limited structural growth opportunity",
            "Terminal growth > GDP implies perpetual market share gains",
            "Combining high cyclicality with above-GDP growth is logically inconsistent",
            "Model implicitly assumes the company decouples from its beta exposure"
        ],
        tags=["dcf", "terminal-growth", "beta-consistency", "macro-assumptions", "advanced-concepts"],
    ))

    # 7. WACC Inconsistency Across Scenarios
    problems.append(Problem(
        id="adv_dcf_002",
        category=ProblemCategory.DCF_SANITY,
        difficulty=Difficulty.EXPERT,
        question="""A base-case DCF uses WACC = 9%. In the downside scenario, revenues fall 15%, but WACC remains unchanged.

Identify the conceptual flaw and describe how factor risk should affect discount rates.""",
        context=FinancialContext(
            company_name="Scenario Analysis Corp",
            ticker="SCEN",
            sector="Consumer Cyclical",
            wacc=9.0,
            model_assumptions={
                "Base case revenue": "$1.0B",
                "Downside revenue": "$850M (-15%)",
                "Base case WACC": "9%",
                "Downside WACC": "9% (unchanged)"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="WACC should increase in downside scenarios. Revenue declines typically coincide with higher beta (operating leverage), increased credit spreads (debt risk), and elevated equity risk premiums. Keeping WACC constant understates downside risk.",
        answer_options=[
            AnswerOption(id="A", text="WACC is a company characteristic and shouldn't change across scenarios", is_correct=False),
            AnswerOption(id="B", text="WACC should increase in downside scenarios. Revenue declines typically coincide with higher beta (operating leverage), increased credit spreads (debt risk), and elevated equity risk premiums. Keeping WACC constant understates downside risk.", is_correct=True),
            AnswerOption(id="C", text="WACC should decrease in downside scenarios due to lower growth", is_correct=False),
            AnswerOption(id="D", text="Only the cash flows matter in scenarios, not the discount rate", is_correct=False),
        ],
        explanation="In downside scenarios: (1) Operating leverage increases effective beta as fixed costs magnify revenue declines, (2) Credit spreads widen as debt becomes riskier, (3) Equity risk premium may rise in stressed environments. A proper scenario analysis should adjust WACC upward by 100-300 bps in downside cases, or probability-weight scenarios correctly.",
        reasoning_steps=[
            "Operating leverage: fixed costs / variable revenue = higher beta in downturns",
            "Credit risk: lower revenue coverage = wider spreads, higher cost of debt",
            "Equity risk: distressed companies face higher required returns",
            "Keeping WACC constant double-counts optimism in the discount rate",
            "Probability weighting doesn't fix this - each scenario needs appropriate WACC"
        ],
        tags=["wacc", "scenario-analysis", "operating-leverage", "credit-risk", "advanced-concepts"],
    ))

    # 8. DCF vs. Factor-Implied Valuation
    problems.append(Problem(
        id="adv_dcf_003",
        category=ProblemCategory.DCF_SANITY,
        difficulty=Difficulty.HARD,
        question="""A stock screens as cheap on EV/EBITDA but has strong negative exposure to volatility and beta factors.

Why might a DCF overstate intrinsic value relative to realized returns?""",
        context=FinancialContext(
            company_name="Factor Trap Corp",
            ticker="FTRP",
            sector="Energy",
            ev_ebitda=5.5,
            model_assumptions={
                "Sector median EV/EBITDA": 8.0,
                "Volatility factor loading": -0.8,
                "Beta factor loading": -0.6,
                "DCF implied upside": "45%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Negative volatility/beta factor loadings mean the stock underperforms when these factors rally. A DCF ignores systematic factor risk - realized returns will trail intrinsic value if factors move against the position.",
        answer_options=[
            AnswerOption(id="A", text="DCF is always more accurate than factor models", is_correct=False),
            AnswerOption(id="B", text="Factor exposures don't affect fundamental value", is_correct=False),
            AnswerOption(id="C", text="Negative volatility/beta factor loadings mean the stock underperforms when these factors rally. A DCF ignores systematic factor risk - realized returns will trail intrinsic value if factors move against the position.", is_correct=True),
            AnswerOption(id="D", text="Low EV/EBITDA always means undervaluation", is_correct=False),
        ],
        explanation="Cheap valuation metrics may reflect persistent factor headwinds. A stock with -0.8 volatility loading will lose ~0.8% for every 1% the volatility factor rallies. Over time, these systematic drags erode returns even if the DCF thesis is correct. Realized returns = alpha + factor returns; negative factor loadings can overwhelm positive alpha.",
        reasoning_steps=[
            "DCF captures company-specific value but ignores systematic factor exposure",
            "Negative factor loadings create persistent headwinds",
            "Cheap multiples may be 'value traps' with structural factor drag",
            "Realized returns = alpha + sum(beta_i * factor_i)",
            "Factor headwinds can prevent convergence to DCF fair value"
        ],
        tags=["dcf", "factor-exposure", "value-trap", "volatility-factor", "advanced-concepts"],
    ))

    # 9. Cash Flow Growth Exceeds Industry Capacity
    problems.append(Problem(
        id="adv_dcf_004",
        category=ProblemCategory.DCF_SANITY,
        difficulty=Difficulty.HARD,
        question="""A company projects 12% FCF growth for 10 years in an industry growing at 3%.

What assumptions must hold for this to be plausible, and how would you stress-test them?""",
        context=FinancialContext(
            company_name="Hypergrowth Industries",
            ticker="HYPR",
            sector="Industrials",
            model_assumptions={
                "Company FCF growth": "12% for 10 years",
                "Industry growth": "3%",
                "Current market share": "5%",
                "Implied year-10 market share": "~25%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="The company must gain ~20% market share, implying either industry consolidation, disruptive competitive advantage, or international expansion. Stress test: model competitor response, pricing pressure as share grows, and capital intensity of share gains.",
        answer_options=[
            AnswerOption(id="A", text="Such growth is impossible in a mature industry", is_correct=False),
            AnswerOption(id="B", text="The company must gain ~20% market share, implying either industry consolidation, disruptive competitive advantage, or international expansion. Stress test: model competitor response, pricing pressure as share grows, and capital intensity of share gains.", is_correct=True),
            AnswerOption(id="C", text="Industry growth rate doesn't constrain company growth", is_correct=False),
            AnswerOption(id="D", text="Use lower growth rate automatically", is_correct=False),
        ],
        explanation="At 12% growth vs. 3% industry: (1.12/1.03)^10 = 2.3x relative growth, implying 5% share grows to ~11.5% (or higher if industry grows slower). This requires: sustained competitive advantage, no competitive response, stable pricing, and consistent capital returns. Stress tests should model: margin compression from competitive pricing, capex needed for growth, and what happens when share gains slow.",
        reasoning_steps=[
            "Calculate implied market share trajectory",
            "Identify required competitive dynamics (consolidation, disruption, expansion)",
            "Model competitive response and margin pressure",
            "Assess capital intensity of growth strategy",
            "Build scenarios for share gain deceleration"
        ],
        tags=["dcf", "growth-assumptions", "market-share", "stress-testing", "advanced-concepts"],
    ))

    # 10. Reconciling DCF Alpha with Portfolio Risk
    problems.append(Problem(
        id="adv_dcf_005",
        category=ProblemCategory.DCF_SANITY,
        difficulty=Difficulty.EXPERT,
        question="""Your DCF implies 25% upside, but adding the position increases portfolio volatility by 18%.

How do you translate valuation conviction into position size without violating risk constraints?""",
        context=FinancialContext(
            company_name="Risk Budget Corp",
            ticker="RSKB",
            sector="Technology",
            model_assumptions={
                "DCF upside": "25%",
                "Portfolio vol before": "12%",
                "Portfolio vol with full position": "14.16% (+18%)",
                "Risk budget": "13% max volatility",
                "Position correlation to portfolio": 0.7
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Size to risk contribution, not conviction. If full position adds 2.16% vol but budget allows 1% vol contribution, size at ~46% of desired weight. Alternatively, hedge correlated exposures to reduce marginal vol impact.",
        answer_options=[
            AnswerOption(id="A", text="Take full position - conviction should override risk limits", is_correct=False),
            AnswerOption(id="B", text="Size to risk contribution, not conviction. If full position adds 2.16% vol but budget allows 1% vol contribution, size at ~46% of desired weight. Alternatively, hedge correlated exposures to reduce marginal vol impact.", is_correct=True),
            AnswerOption(id="C", text="Skip the trade - risk constraints are absolute", is_correct=False),
            AnswerOption(id="D", text="Wait for volatility to decline before entering", is_correct=False),
        ],
        explanation="Using marginal contribution to risk: Full position adds 2.16% vol (14.16% - 12%). Risk budget has 1% remaining (13% - 12%). Size position at 1%/2.16% = 46% of conviction weight. Alternatively, if position has 0.7 correlation to portfolio, hedge 30% of beta to reduce correlation to ~0.5, allowing larger position within risk budget.",
        reasoning_steps=[
            "Calculate marginal contribution to portfolio volatility",
            "Compare to available risk budget",
            "Scale position size to fit risk budget",
            "Consider hedging correlated exposures to increase capacity",
            "Balance conviction with portfolio-level risk management"
        ],
        tags=["position-sizing", "risk-budget", "portfolio-construction", "hedging", "advanced-concepts"],
    ))

    # =========================================================================
    # III. ACCOUNTING RED FLAGS (5 problems)
    # =========================================================================

    # 11. Revenue Growth vs. Receivables Expansion
    problems.append(Problem(
        id="adv_arf_001",
        category=ProblemCategory.ACCOUNTING_RED_FLAG,
        difficulty=Difficulty.MEDIUM,
        question="""Revenue grows 10% YoY, but receivables grow 28%.

Under what conditions is this benign? When does it indicate negative alpha risk?""",
        context=FinancialContext(
            company_name="Receivables Risk Corp",
            ticker="RCVR",
            sector="Technology",
            revenue={"2023": 1000, "2024": 1100},
            model_assumptions={
                "Revenue growth": "10%",
                "Receivables growth": "28%",
                "DSO 2023": "45 days",
                "DSO 2024": "52 days"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Benign if: new large customer with longer payment terms, Q4 seasonality, expansion into new geography. Red flag if: same customer mix with extended terms, rising bad debt reserves, or aggressive revenue recognition.",
        answer_options=[
            AnswerOption(id="A", text="Always a red flag - receivables should grow at same rate as revenue", is_correct=False),
            AnswerOption(id="B", text="Never a concern - receivables naturally fluctuate", is_correct=False),
            AnswerOption(id="C", text="Benign if: new large customer with longer payment terms, Q4 seasonality, expansion into new geography. Red flag if: same customer mix with extended terms, rising bad debt reserves, or aggressive revenue recognition.", is_correct=True),
            AnswerOption(id="D", text="Only concerning if receivables grow more than 50% faster than revenue", is_correct=False),
        ],
        explanation="DSO expansion from 45 to 52 days needs explanation. Legitimate causes: enterprise customer wins (90-day terms vs. SMB 30-day), geographic mix shift, or Q4 timing. Red flags: offering extended terms to close deals (quality deterioration), channel stuffing, or recognizing revenue before delivery. Check: customer concentration, allowance for doubtful accounts, and cash conversion cycle trends.",
        reasoning_steps=[
            "Calculate DSO change: from 45 to 52 days (+15%)",
            "Investigate customer mix changes",
            "Check bad debt allowance trends",
            "Compare to cash collections and operating cash flow",
            "Distinguish growth-driven from quality-deterioration causes"
        ],
        tags=["receivables", "revenue-quality", "dso", "red-flag", "advanced-concepts"],
    ))

    # 12. Margin Expansion with Rising Volatility
    problems.append(Problem(
        id="adv_arf_002",
        category=ProblemCategory.ACCOUNTING_RED_FLAG,
        difficulty=Difficulty.HARD,
        question="""Gross margins expand 400 bps, but idiosyncratic volatility doubles.

How do you reconcile improving fundamentals with deteriorating risk characteristics?""",
        context=FinancialContext(
            company_name="Volatile Margins Inc",
            ticker="VMRG",
            sector="Consumer Discretionary",
            model_assumptions={
                "Gross margin 2023": "32%",
                "Gross margin 2024": "36%",
                "Idiosyncratic vol 2023": "25%",
                "Idiosyncratic vol 2024": "50%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Rising idiosyncratic vol suggests the market doubts margin sustainability. Possible causes: one-time benefits (input cost windfalls, unsustainable pricing), operating leverage risk, or pending competitive response. The market is pricing reversion risk.",
        answer_options=[
            AnswerOption(id="A", text="No conflict - margins and volatility are independent", is_correct=False),
            AnswerOption(id="B", text="Rising idiosyncratic vol suggests the market doubts margin sustainability. Possible causes: one-time benefits (input cost windfalls, unsustainable pricing), operating leverage risk, or pending competitive response. The market is pricing reversion risk.", is_correct=True),
            AnswerOption(id="C", text="High volatility always indicates fraud", is_correct=False),
            AnswerOption(id="D", text="Buy the stock - improving margins with high vol means mispricing", is_correct=False),
        ],
        explanation="Margins and vol should move inversely for stable businesses. If margins improve but vol rises, the market sees the improvement as fragile. Check: commodity input exposure (temporary favorable pricing?), customer concentration, competitive dynamics (are competitors about to respond?), and whether margins were achieved through cost cuts (one-time) vs. pricing power (sustainable).",
        reasoning_steps=[
            "Improving fundamentals should reduce uncertainty and volatility",
            "Rising vol signals market skepticism about sustainability",
            "Investigate margin improvement sources",
            "Assess competitive and cost structure risks",
            "Consider whether margin gains will mean-revert"
        ],
        tags=["margin-analysis", "volatility", "sustainability", "market-signals", "advanced-concepts"],
    ))

    # 13. Capitalized Costs and Factor Exposure
    problems.append(Problem(
        id="adv_arf_003",
        category=ProblemCategory.ACCOUNTING_RED_FLAG,
        difficulty=Difficulty.EXPERT,
        question="""A company capitalizes increasing R&D, boosting near-term earnings. Its volatility and beta exposures rise sharply.

Explain the link between accounting choices and factor risk.""",
        context=FinancialContext(
            company_name="Capitalize Everything Corp",
            ticker="CAPE",
            sector="Technology",
            model_assumptions={
                "R&D expense (expensed) 2023": "$100M",
                "R&D capitalized 2024": "$150M (up from $50M)",
                "EPS impact": "+$0.40 from capitalization change",
                "Beta change": "1.2 to 1.6",
                "Idiosyncratic vol change": "+40%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Capitalizing R&D shifts current expenses to future amortization, making earnings more sensitive to future success. This increases operating leverage and defers risk recognition, raising both beta (economic sensitivity) and idiosyncratic vol (uncertainty about R&D success).",
        answer_options=[
            AnswerOption(id="A", text="Accounting choices don't affect factor exposures", is_correct=False),
            AnswerOption(id="B", text="Capitalizing R&D shifts current expenses to future amortization, making earnings more sensitive to future success. This increases operating leverage and defers risk recognition, raising both beta (economic sensitivity) and idiosyncratic vol (uncertainty about R&D success).", is_correct=True),
            AnswerOption(id="C", text="Higher capitalization always indicates fraud", is_correct=False),
            AnswerOption(id="D", text="Beta increases are unrelated to accounting policy", is_correct=False),
        ],
        explanation="Capitalizing R&D: (1) Increases asset base, requiring future returns to justify carrying value, (2) Creates amortization tail that persists in bad times (operating leverage), (3) Defers the 'test' of R&D success, increasing uncertainty. Markets recognize this by demanding higher risk premium (higher beta) and assigning higher idiosyncratic vol to the uncertain outcomes.",
        reasoning_steps=[
            "Capitalization shifts expense timing, not economic reality",
            "Future amortization creates fixed-cost-like behavior (operating leverage)",
            "Uncertainty about R&D success increases idiosyncratic risk",
            "Market adjusts factor exposures to reflect true risk profile",
            "Accounting 'improvement' comes with higher risk compensation"
        ],
        tags=["capitalization", "r&d", "factor-risk", "accounting-policy", "advanced-concepts"],
    ))

    # 14. Cash Flow vs. Earnings Divergence
    problems.append(Problem(
        id="adv_arf_004",
        category=ProblemCategory.ACCOUNTING_RED_FLAG,
        difficulty=Difficulty.MEDIUM,
        question="""Earnings grow steadily, but operating cash flow stagnates.

How does this affect expected alpha vs. realized idiosyncratic returns?""",
        context=FinancialContext(
            company_name="Accrual Heavy Corp",
            ticker="ACRH",
            sector="Industrials",
            net_income={"2022": 100, "2023": 120, "2024": 145},
            free_cash_flow={"2022": 95, "2023": 90, "2024": 88},
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Earnings without cash flow support indicate accrual accumulation. Studies show high-accrual stocks underperform by 5-10% annually. Expected alpha from earnings growth will likely be offset by negative accrual factor exposure.",
        answer_options=[
            AnswerOption(id="A", text="Earnings are more important than cash flow for valuation", is_correct=False),
            AnswerOption(id="B", text="Cash flow timing differences are always temporary", is_correct=False),
            AnswerOption(id="C", text="Earnings without cash flow support indicate accrual accumulation. Studies show high-accrual stocks underperform by 5-10% annually. Expected alpha from earnings growth will likely be offset by negative accrual factor exposure.", is_correct=True),
            AnswerOption(id="D", text="Only look at free cash flow, ignore earnings entirely", is_correct=False),
        ],
        explanation="The accrual anomaly is well-documented: high accruals (earnings >> cash flow) predict poor future returns. Accruals include: receivables growth, inventory build, capitalized costs, and deferred revenue changes. A stock with steadily rising earnings but flat cash flow is accumulating accruals, loading negatively onto the quality/accrual factor, and likely to generate negative idiosyncratic returns.",
        reasoning_steps=[
            "Calculate accrual accumulation: earnings - cash flow",
            "Recognize accrual anomaly research findings",
            "High accruals = negative quality factor loading",
            "Expected return = alpha + factor loadings",
            "Negative accrual factor exposure offsets fundamental 'improvement'"
        ],
        tags=["accruals", "cash-flow", "quality-factor", "earnings-quality", "advanced-concepts"],
    ))

    # 15. Inventory Build in a Defensive Industry
    problems.append(Problem(
        id="adv_arf_005",
        category=ProblemCategory.ACCOUNTING_RED_FLAG,
        difficulty=Difficulty.HARD,
        question="""Inventory days increase 40% in a traditionally low-volatility industry.

Why might this shift the stock's factor profile even before earnings decline?""",
        context=FinancialContext(
            company_name="Defensive Inventory Corp",
            ticker="DINV",
            sector="Consumer Staples",
            model_assumptions={
                "Inventory days 2023": "45 days",
                "Inventory days 2024": "63 days (+40%)",
                "Industry": "Consumer Staples (defensive)",
                "Historical beta": 0.6,
                "Current beta": 0.9
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Inventory build increases operating leverage (working capital tied up must be recovered through sales). This raises beta even in defensive industries. Markets also see inventory build as demand weakness signal, adding idiosyncratic risk premium before earnings confirm.",
        answer_options=[
            AnswerOption(id="A", text="Inventory changes don't affect factor exposures", is_correct=False),
            AnswerOption(id="B", text="Inventory build increases operating leverage (working capital tied up must be recovered through sales). This raises beta even in defensive industries. Markets also see inventory build as demand weakness signal, adding idiosyncratic risk premium before earnings confirm.", is_correct=True),
            AnswerOption(id="C", text="Defensive stocks cannot have rising beta", is_correct=False),
            AnswerOption(id="D", text="Only manufacturing companies face inventory risk", is_correct=False),
        ],
        explanation="Inventory build: (1) Ties up working capital, creating fixed-cost-like pressure to sell, (2) Increases risk of write-downs if demand weakens, (3) Signals potential channel stuffing or demand miscalculation. Markets recognize these risks by increasing beta (the company is now more cyclically exposed) and idiosyncratic vol (write-down risk). This happens before earnings decline because factor loadings adjust to forward-looking risk.",
        reasoning_steps=[
            "Inventory build increases working capital intensity",
            "Working capital creates operating leverage effect",
            "Defensive industry doesn't protect against company-specific risks",
            "Market beta adjusts to reflect increased economic sensitivity",
            "Factor profile shifts before accounting earnings reflect the issue"
        ],
        tags=["inventory", "operating-leverage", "beta", "defensive-stocks", "advanced-concepts"],
    ))

    # =========================================================================
    # IV. CATALYST IDENTIFICATION (5 problems)
    # =========================================================================

    # 16. Regulatory Catalyst with Market Exposure
    problems.append(Problem(
        id="adv_cat_001",
        category=ProblemCategory.CATALYST_ID,
        difficulty=Difficulty.HARD,
        question="""A biotech stock has a binary FDA decision in 3 months. Beta exposure is 2.1.

How should you structure the position to isolate the catalyst alpha?""",
        context=FinancialContext(
            company_name="Binary Biotech Inc",
            ticker="BBIN",
            sector="Healthcare",
            model_assumptions={
                "FDA decision": "3 months",
                "Beta": 2.1,
                "Approval probability": "60%",
                "Upside on approval": "+80%",
                "Downside on rejection": "-50%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Hedge market exposure by shorting 2.1x notional in sector ETF or index futures. This isolates the idiosyncratic FDA catalyst. Consider sizing to expected value: 0.6 * 80% - 0.4 * 50% = +28% expected alpha, then adjust for asymmetric payoff and vol.",
        answer_options=[
            AnswerOption(id="A", text="Take a full long position - high beta means high returns", is_correct=False),
            AnswerOption(id="B", text="Hedge market exposure by shorting 2.1x notional in sector ETF or index futures. This isolates the idiosyncratic FDA catalyst. Consider sizing to expected value: 0.6 * 80% - 0.4 * 50% = +28% expected alpha, then adjust for asymmetric payoff and vol.", is_correct=True),
            AnswerOption(id="C", text="Avoid all binary events - too risky", is_correct=False),
            AnswerOption(id="D", text="Use options only - never hold equity for binary events", is_correct=False),
        ],
        explanation="With beta 2.1, a 5% market move creates 10.5% return attribution unrelated to the FDA thesis. Hedge by shorting beta-equivalent index exposure. This isolates catalyst alpha. Position sizing: expected value = 60% * 80% - 40% * 50% = +28%. But given binary payoff, size smaller than expected value suggests due to variance drag and potential blow-up risk.",
        reasoning_steps=[
            "Identify beta contamination risk: 2.1 beta amplifies market moves",
            "Hedge with 2.1x notional short in correlated index",
            "Calculate expected value of catalyst: probability-weighted outcomes",
            "Size for expected alpha, adjusted for binary variance",
            "Result: isolated exposure to FDA decision, hedged market risk"
        ],
        tags=["catalyst", "hedging", "beta-neutralization", "binary-events", "advanced-concepts"],
    ))

    # 17. M&A Rumor in a Crowded Trade
    problems.append(Problem(
        id="adv_cat_002",
        category=ProblemCategory.CATALYST_ID,
        difficulty=Difficulty.EXPERT,
        question="""A stock with high AMH (assets under management hedge-fund) exposure rallies on M&A rumors.

Why is the risk asymmetric, and how should sizing differ from a fundamental long?""",
        context=FinancialContext(
            company_name="Crowded Target Corp",
            ticker="CTGT",
            sector="Technology",
            recent_news=[
                "Stock up 15% on M&A speculation",
                "Hedge fund ownership: 35% of float",
                "Short interest: 3% (low)",
                "Options implied vol: 60% (elevated)"
            ]
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="High HF ownership + M&A pop creates crowded long with limited upside (deal priced in) but significant downside (de-crowding if deal fails). Size at 25-50% of normal conviction weight; use options to define max loss.",
        answer_options=[
            AnswerOption(id="A", text="Size larger - M&A provides downside protection", is_correct=False),
            AnswerOption(id="B", text="High HF ownership + M&A pop creates crowded long with limited upside (deal priced in) but significant downside (de-crowding if deal fails). Size at 25-50% of normal conviction weight; use options to define max loss.", is_correct=True),
            AnswerOption(id="C", text="Avoid completely - M&A rumors are never actionable", is_correct=False),
            AnswerOption(id="D", text="Size same as fundamental positions - risk is symmetric", is_correct=False),
        ],
        explanation="After 15% rally on rumors with 35% HF ownership: (1) Much of deal premium is priced in, (2) If deal fails, HFs will rush to exit simultaneously, (3) Low short interest means no covering to cushion decline. The distribution is negatively skewed: small upside if deal closes at rumored price, large downside on deal failure. Size smaller than conviction suggests and use options (buy puts or put spreads) to cap downside.",
        reasoning_steps=[
            "Assess crowding: 35% HF ownership = significant concentration",
            "Post-rally upside limited: deal premium largely priced in",
            "Downside risk amplified: crowded exit on deal failure",
            "Distribution is negatively skewed: size for asymmetry",
            "Options can define maximum loss in asymmetric scenarios"
        ],
        tags=["m&a", "crowding", "asymmetric-risk", "position-sizing", "advanced-concepts"],
    ))

    # 18. Macro Catalyst Contaminating Stock Thesis
    problems.append(Problem(
        id="adv_cat_003",
        category=ProblemCategory.CATALYST_ID,
        difficulty=Difficulty.HARD,
        question="""A cyclical stock has an upcoming product launch, but macro volatility is rising.

How do you separate catalyst-specific returns from environmental risk?""",
        context=FinancialContext(
            company_name="Cyclical Launch Corp",
            ticker="CYCL",
            sector="Consumer Discretionary",
            model_assumptions={
                "Product launch": "6 weeks",
                "Expected launch impact": "+25% if successful",
                "Current macro vol": "VIX at 28 (elevated)",
                "Stock beta": 1.5,
                "Correlation to macro": 0.7
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="In high-vol environments, macro moves dominate idiosyncratic catalysts. Options: (1) Hedge macro exposure and pay the carry, (2) Wait for vol compression, (3) Size smaller to account for macro variance overwhelming catalyst signal.",
        answer_options=[
            AnswerOption(id="A", text="Ignore macro - focus only on the product launch", is_correct=False),
            AnswerOption(id="B", text="In high-vol environments, macro moves dominate idiosyncratic catalysts. Options: (1) Hedge macro exposure and pay the carry, (2) Wait for vol compression, (3) Size smaller to account for macro variance overwhelming catalyst signal.", is_correct=True),
            AnswerOption(id="C", text="Macro volatility doesn't affect individual stock returns", is_correct=False),
            AnswerOption(id="D", text="Double position size to compensate for macro headwinds", is_correct=False),
        ],
        explanation="With VIX at 28 and beta 1.5, expected macro contribution to variance is high. A 5% market move creates 7.5% stock move, easily swamping a 25% launch catalyst. Signal-to-noise ratio is poor. Solutions: (1) Short index futures to hedge, paying theta but isolating catalyst, (2) Wait for VIX to decline to 18-20, improving signal-to-noise, (3) Size position at 50-60% of normal to account for variance drag.",
        reasoning_steps=[
            "Calculate macro variance contribution: beta^2 * market_vol^2",
            "Compare to catalyst magnitude: 25% launch impact",
            "Assess signal-to-noise ratio",
            "Choose mitigation: hedge, wait, or size down",
            "Hedging costs theta; waiting risks missing catalyst; sizing down reduces alpha capture"
        ],
        tags=["macro-risk", "catalyst", "signal-to-noise", "hedging", "advanced-concepts"],
    ))

    # 19. Earnings as a Risk-Reduction Event
    problems.append(Problem(
        id="adv_cat_004",
        category=ProblemCategory.CATALYST_ID,
        difficulty=Difficulty.HARD,
        question="""A stock's idiosyncratic volatility collapses post-earnings despite flat price reaction.

Why can this still be a positive outcome for portfolio construction?""",
        context=FinancialContext(
            company_name="Volatility Collapse Corp",
            ticker="VOLC",
            sector="Technology",
            recent_news=[
                "Earnings in-line with expectations",
                "Stock flat on announcement (+0.2%)",
                "Idiosyncratic vol dropped from 45% to 28%",
                "Options IV crush of 38%"
            ]
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Lower idiosyncratic vol means higher risk-adjusted returns for the same expected alpha. Portfolio can now: (1) Increase position size within same risk budget, (2) Maintain size with lower marginal risk contribution, (3) Reallocate freed risk budget to other opportunities.",
        answer_options=[
            AnswerOption(id="A", text="Flat price reaction means the position added no value", is_correct=False),
            AnswerOption(id="B", text="Lower idiosyncratic vol means higher risk-adjusted returns for the same expected alpha. Portfolio can now: (1) Increase position size within same risk budget, (2) Maintain size with lower marginal risk contribution, (3) Reallocate freed risk budget to other opportunities.", is_correct=True),
            AnswerOption(id="C", text="Vol collapse is always bad - it means no future upside", is_correct=False),
            AnswerOption(id="D", text="Only price return matters for portfolio construction", is_correct=False),
        ],
        explanation="Sharpe ratio = alpha / volatility. If alpha expectation is unchanged but vol drops 38%, risk-adjusted return improves by ~60% (1/0.62). For portfolio construction: same position now uses less risk budget (MCR declines with vol), allowing size increase or reallocation. This is why earnings can be 'wins' even with flat prices - they resolve uncertainty.",
        reasoning_steps=[
            "Risk-adjusted return = expected alpha / volatility",
            "Vol decline improves Sharpe ratio for same alpha",
            "Lower vol reduces marginal contribution to portfolio risk",
            "Freed risk budget can be reallocated",
            "Information events (earnings) have value beyond price impact"
        ],
        tags=["volatility", "risk-adjusted-returns", "portfolio-construction", "information-value", "advanced-concepts"],
    ))

    # 20. Event Timing vs. Transaction Costs
    problems.append(Problem(
        id="adv_cat_005",
        category=ProblemCategory.CATALYST_ID,
        difficulty=Difficulty.HARD,
        question="""A catalyst is expected in 6 weeks. Entering now doubles tracking error due to beta exposure.

When does waiting dominate early positioning?""",
        context=FinancialContext(
            company_name="Timing Trade Corp",
            ticker="TIME",
            sector="Financials",
            model_assumptions={
                "Catalyst timing": "6 weeks",
                "Expected catalyst alpha": "+15%",
                "Current tracking error impact": "2x if entered now",
                "Entry cost (market impact)": "50 bps",
                "Beta exposure during wait": 1.4
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Wait dominates when: (carry cost of tracking error) > (option value of early entry + market impact savings). With 2x TE for 6 weeks, variance drag likely exceeds 50 bps entry cost. Wait for catalyst proximity or hedge the beta exposure.",
        answer_options=[
            AnswerOption(id="A", text="Always enter early to capture the full move", is_correct=False),
            AnswerOption(id="B", text="Wait dominates when: (carry cost of tracking error) > (option value of early entry + market impact savings). With 2x TE for 6 weeks, variance drag likely exceeds 50 bps entry cost. Wait for catalyst proximity or hedge the beta exposure.", is_correct=True),
            AnswerOption(id="C", text="Timing doesn't matter - alpha is alpha", is_correct=False),
            AnswerOption(id="D", text="Always wait until the day before catalyst", is_correct=False),
        ],
        explanation="Tradeoff: early entry captures any pre-catalyst drift but adds tracking error (beta variance) and may face higher exit impact if wrong. Waiting reduces TE cost but risks missing pre-announcement drift and may face higher entry impact near event. With 2x TE for 6 weeks: variance drag ≈ 2 * sqrt(6/52) * annual_TE, likely several percent. This exceeds 50 bps entry cost. Better to wait or hedge beta.",
        reasoning_steps=[
            "Calculate cost of early entry: tracking error drag over 6 weeks",
            "Compare to benefit: capturing potential pre-catalyst drift",
            "Factor in transaction costs: entry now vs. entry later",
            "Consider alternatives: hedging beta to reduce TE while maintaining exposure",
            "Decision rule: minimize total cost (variance drag + transaction costs - drift capture)"
        ],
        tags=["timing", "tracking-error", "transaction-costs", "catalyst-trading", "advanced-concepts"],
    ))

    # =========================================================================
    # V. FORMULA AUDIT (5 problems)
    # =========================================================================

    # 21. Beta-Neutral but Not Risk-Neutral
    problems.append(Problem(
        id="adv_fa_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A portfolio is beta-neutral but experiences large drawdowns during market sell-offs.

Identify which assumptions of the single-factor model failed.""",
        context=FinancialContext(
            company_name="Portfolio Analysis",
            ticker="N/A",
            sector="Multi-sector",
            formula_context="""Portfolio Construction:
- Long: $100M high-beta growth stocks (avg beta 1.5)
- Short: $150M low-beta value stocks (avg beta 1.0)
- Net beta: (100 * 1.5 - 150 * 1.0) / 100 = 0.0
- Recent drawdown: -8% during -5% market move"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Single-factor beta assumes linear, constant market sensitivity. Failed assumptions: (1) Beta increases in sell-offs (beta asymmetry), (2) Additional factors (value, momentum, liquidity) move against position, (3) Correlation spike in stress periods.",
        answer_options=[
            AnswerOption(id="A", text="The calculation is wrong - recompute beta weights", is_correct=False),
            AnswerOption(id="B", text="Single-factor beta assumes linear, constant market sensitivity. Failed assumptions: (1) Beta increases in sell-offs (beta asymmetry), (2) Additional factors (value, momentum, liquidity) move against position, (3) Correlation spike in stress periods.", is_correct=True),
            AnswerOption(id="C", text="Beta-neutral portfolios cannot have drawdowns by definition", is_correct=False),
            AnswerOption(id="D", text="The portfolio needs more positions for diversification", is_correct=False),
        ],
        explanation="Beta-neutrality using average betas assumes: (1) Constant beta (but betas rise in downturns - 'correlation goes to 1'), (2) Single factor captures all systematic risk (but value/momentum/liquidity factors crashed), (3) Linear market sensitivity (but convexity means losses accelerate). The -8% vs -5% market suggests: long high-beta names fell more than beta predicted, short low-beta names fell less, and factor exposures (long growth/short value) hurt.",
        reasoning_steps=[
            "Beta-neutral doesn't mean risk-neutral",
            "Beta asymmetry: betas increase in sell-offs",
            "Multi-factor exposure: growth vs. value factor moved against position",
            "Correlation spike: diversification benefits disappeared",
            "Non-linear effects: convexity in stress environments"
        ],
        tags=["beta-neutrality", "risk-model", "factor-exposure", "stress-testing", "advanced-concepts"],
    ))

    # 22. Hidden Factor Exposure in Equal-Weight Portfolio
    problems.append(Problem(
        id="adv_fa_002",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""An equal-weighted portfolio shows persistent losses during momentum crashes.

Explain how 'neutral' construction can still embed factor bets.""",
        context=FinancialContext(
            company_name="Equal Weight Analysis",
            ticker="N/A",
            sector="Multi-sector",
            formula_context="""Portfolio Construction:
- 50 stocks, equal-weighted (2% each)
- Sector neutral to benchmark
- Market cap range: $5B - $500B
- Recent momentum crash: portfolio -12%, benchmark -5%"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Equal-weighting overweights small caps vs. cap-weighted benchmark, creating implicit size and momentum tilts. Small caps have higher momentum loading. 'Neutral' construction relative to one factor often embeds bets on correlated factors.",
        answer_options=[
            AnswerOption(id="A", text="Equal-weighting is always factor-neutral", is_correct=False),
            AnswerOption(id="B", text="The benchmark is wrong - use equal-weight benchmark", is_correct=False),
            AnswerOption(id="C", text="Equal-weighting overweights small caps vs. cap-weighted benchmark, creating implicit size and momentum tilts. Small caps have higher momentum loading. 'Neutral' construction relative to one factor often embeds bets on correlated factors.", is_correct=True),
            AnswerOption(id="D", text="Momentum crashes don't affect diversified portfolios", is_correct=False),
        ],
        explanation="Equal-weighting gives same weight to a $5B and $500B company. Vs. cap-weighted benchmark, this massively overweights small caps. Small caps historically have: higher momentum exposure, higher idiosyncratic vol, and higher beta in stress. The portfolio wasn't 'neutral' - it had implicit long small cap, long momentum factor bets. Momentum crash exposed these hidden exposures.",
        reasoning_steps=[
            "Compare equal-weight to cap-weight: implicit size tilt",
            "Small caps have higher momentum factor loading historically",
            "Sector neutrality doesn't imply factor neutrality",
            "Hidden factor bets created by weighting scheme",
            "Momentum crash exposed the embedded size/momentum long"
        ],
        tags=["equal-weighting", "factor-exposure", "size-effect", "momentum", "advanced-concepts"],
    ))

    # 23. Incorrect Volatility Scaling
    problems.append(Problem(
        id="adv_fa_003",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.MEDIUM,
        question="""A PM annualizes daily volatility by multiplying by 252 instead of sqrt(252).

Quantify the error and explain its implications for leverage decisions.""",
        context=FinancialContext(
            company_name="Volatility Scaling Analysis",
            ticker="N/A",
            sector="N/A",
            formula_context="""Volatility Calculation:
- Daily volatility: 1.0%
- PM's annualized vol: 1.0% * 252 = 252%
- Correct annualized vol: 1.0% * sqrt(252) = 15.9%
- Risk limit: 20% annualized vol
- PM's conclusion: 'Cannot use any leverage'"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Error factor: 252 / sqrt(252) = sqrt(252) ≈ 15.9x overstatement. True annualized vol is 15.9%, well within 20% limit. The PM could safely use ~1.25x leverage. Incorrect scaling led to severely over-conservative positioning.",
        answer_options=[
            AnswerOption(id="A", text="The error is small and doesn't affect decisions", is_correct=False),
            AnswerOption(id="B", text="Error factor: 252 / sqrt(252) = sqrt(252) ≈ 15.9x overstatement. True annualized vol is 15.9%, well within 20% limit. The PM could safely use ~1.25x leverage. Incorrect scaling led to severely over-conservative positioning.", is_correct=True),
            AnswerOption(id="C", text="Multiplying by 252 is correct for annualizing volatility", is_correct=False),
            AnswerOption(id="D", text="The error only affects Sharpe ratio calculations", is_correct=False),
        ],
        explanation="Variance scales linearly with time; volatility scales with sqrt(time). Daily vol * sqrt(252) = annual vol. Using 252 instead overstates by 15.9x. A 1% daily vol portfolio has ~16% annual vol, not 252%. With 20% risk limit, the PM could add 25% leverage (20/16 = 1.25x). The error caused massive under-utilization of risk budget.",
        reasoning_steps=[
            "Variance (not vol) scales linearly with time",
            "Correct formula: annual_vol = daily_vol * sqrt(252)",
            "Error magnitude: 252 / sqrt(252) = 15.9x overstatement",
            "True annual vol: 1% * 15.87 = 15.9%, not 252%",
            "Risk budget allows 1.25x leverage, not 'no leverage'"
        ],
        tags=["volatility-scaling", "risk-management", "leverage", "formula-error", "advanced-concepts"],
    ))

    # 24. Misinterpreting Tracking Error
    problems.append(Problem(
        id="adv_fa_004",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A PM targets 5% tracking error but uses total volatility instead of active volatility.

Why does this lead to systematic over-hedging?""",
        context=FinancialContext(
            company_name="Tracking Error Analysis",
            ticker="N/A",
            sector="N/A",
            formula_context="""Risk Calculation Error:
- PM's target: 5% 'tracking error'
- PM measures: total portfolio volatility (12%)
- Actual tracking error (vs. benchmark): 4%
- PM hedges to bring 'TE' from 12% to 5%
- Result: Actual TE drops to 1.5%"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Tracking error = volatility of active returns (portfolio - benchmark), not total vol. Using total vol as target causes over-hedging because it penalizes market exposure, which isn't 'active' risk. Result: portfolio hugs benchmark too closely, destroying alpha opportunity.",
        answer_options=[
            AnswerOption(id="A", text="Total vol and tracking error are equivalent measures", is_correct=False),
            AnswerOption(id="B", text="Tracking error = volatility of active returns (portfolio - benchmark), not total vol. Using total vol as target causes over-hedging because it penalizes market exposure, which isn't 'active' risk. Result: portfolio hugs benchmark too closely, destroying alpha opportunity.", is_correct=True),
            AnswerOption(id="C", text="Lower tracking error is always better", is_correct=False),
            AnswerOption(id="D", text="The hedge was correct but sizing was wrong", is_correct=False),
        ],
        explanation="TE = std(R_portfolio - R_benchmark), capturing only active (different from benchmark) risk. Total vol includes benchmark-correlated moves that aren't 'active' bets. By targeting total vol = 5% when benchmark vol = 11%, the PM forced portfolio to have very low beta, creating massive tracking. Information ratio = active return / TE; with TE at 1.5%, even small active returns look good, but total alpha is minimal.",
        reasoning_steps=[
            "Define tracking error correctly: vol of (portfolio - benchmark)",
            "Total vol includes systematic (benchmark) component",
            "Targeting total vol penalizes benchmark exposure",
            "Over-hedging reduces TE below target",
            "Low TE constrains alpha opportunity despite appearing 'efficient'"
        ],
        tags=["tracking-error", "active-risk", "hedging", "benchmark-relative", "advanced-concepts"],
    ))

    # 25. Alpha Aggregation Fallacy
    problems.append(Problem(
        id="adv_fa_005",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""A portfolio aggregates many small positive-alpha ideas but underperforms.

Explain how correlation and factor overlap can destroy expected alpha.""",
        context=FinancialContext(
            company_name="Alpha Aggregation Analysis",
            ticker="N/A",
            sector="Multi-sector",
            formula_context="""Portfolio Construction:
- 100 positions, each with +1% expected alpha
- Naive expectation: 1% portfolio alpha
- Realized alpha: -2%
- Average pairwise correlation: 0.4
- Common factor exposure: long growth, long momentum"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Position alphas aren't additive when correlated. With 0.4 correlation and common factor exposure: (1) Factor reversal creates correlated losses, (2) Diversification benefit is much lower than expected, (3) 'Alpha' may actually be mislabeled factor exposure. Realized alpha depends on factor performance.",
        answer_options=[
            AnswerOption(id="A", text="Alphas always aggregate linearly regardless of correlation", is_correct=False),
            AnswerOption(id="B", text="Position alphas aren't additive when correlated. With 0.4 correlation and common factor exposure: (1) Factor reversal creates correlated losses, (2) Diversification benefit is much lower than expected, (3) 'Alpha' may actually be mislabeled factor exposure. Realized alpha depends on factor performance.", is_correct=True),
            AnswerOption(id="C", text="100 positions should always diversify away risk", is_correct=False),
            AnswerOption(id="D", text="The alpha estimates were simply wrong for each position", is_correct=False),
        ],
        explanation="100 positions with 0.4 average correlation don't diversify like 100 independent bets. Effective N ≈ 100 / (1 + 99*0.4) ≈ 2.4 independent bets. If positions share growth/momentum exposure, their 'alpha' is partly factor returns. When factors reverse, all positions lose together. The -2% realized vs +1% expected reflects: factor performance (-3% from growth/momentum reversal) + true alpha (+1%) = -2%.",
        reasoning_steps=[
            "Calculate effective diversification: N / (1 + (N-1) * avg_corr)",
            "With 0.4 correlation, 100 positions ≈ 2.4 independent bets",
            "Identify common factor exposure across positions",
            "Decompose 'alpha' into true alpha vs. factor returns",
            "Factor reversal explains correlated underperformance"
        ],
        tags=["alpha-aggregation", "correlation", "factor-overlap", "diversification", "advanced-concepts"],
    ))

    # =========================================================================
    # VI. FINANCIAL STATEMENT & PORTFOLIO REASONING (5 problems)
    # =========================================================================

    # 26. Diversification vs. Alpha Dilution
    problems.append(Problem(
        id="adv_fsp_001",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.HARD,
        question="""Adding 20 low-conviction positions reduces volatility but also Sharpe ratio.

When does diversification become counterproductive?""",
        context=FinancialContext(
            company_name="Diversification Analysis",
            ticker="N/A",
            sector="Multi-sector",
            model_assumptions={
                "Original portfolio": "10 high-conviction positions",
                "Original Sharpe": 1.2,
                "Original vol": "18%",
                "New portfolio": "30 positions (added 20 low conviction)",
                "New Sharpe": 0.8,
                "New vol": "12%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Diversification is counterproductive when: marginal alpha of new positions < (portfolio Sharpe) * (marginal vol contribution). Adding zero-alpha positions dilutes Sharpe even while reducing vol. Optimal sizing concentrates in highest conviction ideas.",
        answer_options=[
            AnswerOption(id="A", text="Diversification is never counterproductive - always add positions", is_correct=False),
            AnswerOption(id="B", text="Diversification is counterproductive when: marginal alpha of new positions < (portfolio Sharpe) * (marginal vol contribution). Adding zero-alpha positions dilutes Sharpe even while reducing vol. Optimal sizing concentrates in highest conviction ideas.", is_correct=True),
            AnswerOption(id="C", text="Only volatility matters, not Sharpe ratio", is_correct=False),
            AnswerOption(id="D", text="30 positions is always better than 10 positions", is_correct=False),
        ],
        explanation="Sharpe = alpha / vol. Adding low-conviction (low/zero alpha) positions: reduces vol (good) but also reduces total alpha (bad). If new positions have lower Sharpe than portfolio, they dilute. Math: if portfolio Sharpe = 1.2, new position needs alpha > 1.2 * its vol contribution to be additive. The 20 low-conviction positions dragged portfolio Sharpe from 1.2 to 0.8 despite vol improvement.",
        reasoning_steps=[
            "Sharpe ratio = total alpha / total volatility",
            "Adding positions affects both numerator and denominator",
            "Low-conviction = low alpha contribution",
            "Marginal position must have Sharpe > portfolio Sharpe to be accretive",
            "Concentration in best ideas often beats over-diversification"
        ],
        tags=["diversification", "sharpe-ratio", "position-sizing", "concentration", "advanced-concepts"],
    ))

    # 27. Leverage with Stable Volatility
    problems.append(Problem(
        id="adv_fsp_002",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.EXPERT,
        question="""A portfolio doubles leverage after a period of low realized volatility.

Why is this decision most dangerous precisely when it feels safest?""",
        context=FinancialContext(
            company_name="Leverage Timing Analysis",
            ticker="N/A",
            sector="N/A",
            model_assumptions={
                "6-month realized vol": "8% (low)",
                "Long-term average vol": "16%",
                "Leverage pre-decision": "1.0x",
                "Leverage post-decision": "2.0x",
                "Vol target": "16%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Low realized vol clusters in time and mean-reverts. Doubling leverage after low-vol period: (1) Vol will likely mean-revert higher, (2) Leverage locks in just before vol spike, (3) Position size is maximum when risk is about to increase. This is volatility targeting's worst failure mode.",
        answer_options=[
            AnswerOption(id="A", text="Low vol means low risk - safe to increase leverage", is_correct=False),
            AnswerOption(id="B", text="Low realized vol clusters in time and mean-reverts. Doubling leverage after low-vol period: (1) Vol will likely mean-revert higher, (2) Leverage locks in just before vol spike, (3) Position size is maximum when risk is about to increase. This is volatility targeting's worst failure mode.", is_correct=True),
            AnswerOption(id="C", text="Volatility targeting always works - this is correct implementation", is_correct=False),
            AnswerOption(id="D", text="Past volatility perfectly predicts future volatility", is_correct=False),
        ],
        explanation="Volatility clustering: low vol periods are followed by vol spikes (GARCH effect). By increasing leverage after low vol, you're maximally exposed just before the spike. When vol doubles from 8% to 16%, a 2x levered portfolio experiences 32% vol - double the target. This 'buy high' behavior is pro-cyclical: maximum leverage at minimum vol, forced deleveraging at maximum vol. Solution: use vol forecasts, not realized vol, and maintain leverage buffers.",
        reasoning_steps=[
            "Volatility clusters and mean-reverts",
            "Low realized vol often precedes vol spikes",
            "Increasing leverage after low vol = maximum exposure before spike",
            "When vol normalizes: 2x leverage * 16% vol = 32% realized vol",
            "Pro-cyclical leverage timing destroys returns"
        ],
        tags=["leverage", "volatility-timing", "mean-reversion", "risk-management", "advanced-concepts"],
    ))

    # 28. Factor Rotation Misdiagnosis
    problems.append(Problem(
        id="adv_fsp_003",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.HARD,
        question="""A portfolio underperforms during a market rally despite positive alpha names.

How do you determine whether this is stock selection failure or factor drag?""",
        context=FinancialContext(
            company_name="Attribution Analysis",
            ticker="N/A",
            sector="Multi-sector",
            model_assumptions={
                "Portfolio return": "+5%",
                "Benchmark return": "+12%",
                "Market rally": "+10%",
                "Portfolio beta": 0.7,
                "Stock selection alpha (bottom-up)": "+3%",
                "Factor exposure": "Long quality, short momentum"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Decompose: Expected return = beta*market + factor exposures + stock alpha. With beta 0.7 and +10% market: expected beta contribution = +7%. Quality underperformed, momentum rallied = factor drag ~-5%. True alpha = +3%. Total: 7% - 5% + 3% = 5%. Underperformance is factor drag, not stock selection.",
        answer_options=[
            AnswerOption(id="A", text="Any underperformance means stock selection failed", is_correct=False),
            AnswerOption(id="B", text="Decompose: Expected return = beta*market + factor exposures + stock alpha. With beta 0.7 and +10% market: expected beta contribution = +7%. Quality underperformed, momentum rallied = factor drag ~-5%. True alpha = +3%. Total: 7% - 5% + 3% = 5%. Underperformance is factor drag, not stock selection.", is_correct=True),
            AnswerOption(id="C", text="Factor exposures don't affect portfolio returns", is_correct=False),
            AnswerOption(id="D", text="Compare only to benchmark - factors are irrelevant", is_correct=False),
        ],
        explanation="Multi-factor attribution: R = alpha + beta*MKT + exposures*factors. Portfolio: beta contribution = 0.7 * 10% = 7%, factor contribution = (long quality * quality_return) + (short momentum * -momentum_return) ≈ -5%, stock selection alpha = +3%. Sum = 5%. Benchmark earned 12% with beta ~1.0 (10%) + 2% factor tailwinds. Underperformance (7%) is entirely explained by lower beta (-3%) and factor drag (-5%), not stock picking.",
        reasoning_steps=[
            "Decompose returns into beta, factor, and alpha components",
            "Calculate beta contribution: portfolio_beta * market_return",
            "Identify factor exposures and their period returns",
            "Residual after beta and factors = true stock selection",
            "Diagnose source of underperformance for correct response"
        ],
        tags=["factor-attribution", "performance-analysis", "stock-selection", "factor-rotation", "advanced-concepts"],
    ))

    # 29. Risk Budget vs. Opportunity Cost
    problems.append(Problem(
        id="adv_fsp_004",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.EXPERT,
        question="""A strict volatility cap forces you to exit a position before alpha realization.

How should risk limits adapt to conviction asymmetry?""",
        context=FinancialContext(
            company_name="Risk Limit Analysis",
            ticker="N/A",
            sector="N/A",
            model_assumptions={
                "Position": "Biotech with FDA catalyst",
                "Vol cap": "15% portfolio vol",
                "Position vol contribution": "3% (20% of budget)",
                "Vol spike on news": "Position vol doubles",
                "Forced exit": "Day before FDA decision",
                "FDA approval": "+50% next day"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Static vol caps ignore conviction asymmetry and catalyst timing. Solutions: (1) Use expected-shortfall limits instead of vol (better tail measure), (2) Allow temporary vol exceedance with hard loss limits, (3) Pre-commit to catalyst positions with dedicated risk budget.",
        answer_options=[
            AnswerOption(id="A", text="Risk limits should never flex - discipline is paramount", is_correct=False),
            AnswerOption(id="B", text="Static vol caps ignore conviction asymmetry and catalyst timing. Solutions: (1) Use expected-shortfall limits instead of vol (better tail measure), (2) Allow temporary vol exceedance with hard loss limits, (3) Pre-commit to catalyst positions with dedicated risk budget.", is_correct=True),
            AnswerOption(id="C", text="Ignore risk limits when conviction is high", is_correct=False),
            AnswerOption(id="D", text="Never hold positions into binary events", is_correct=False),
        ],
        explanation="Static vol limits forced exit right before alpha realization. Better approaches: (1) Expected shortfall (CVaR) limits focus on tail loss, not vol fluctuation, (2) 'Soft' vol limits with hard loss stops: allow 18% vol but stop at -5% loss, (3) Dedicated catalyst bucket: allocate 5% of risk budget specifically for binary events with different rules. The goal is risk management, not vol management - these aren't the same.",
        reasoning_steps=[
            "Static vol limits don't distinguish conviction levels",
            "Vol spike before catalyst is information, not necessarily risk",
            "Expected shortfall better captures actual loss risk",
            "Hybrid limits: vol guidance with hard loss stops",
            "Dedicated risk buckets for different alpha sources"
        ],
        tags=["risk-limits", "opportunity-cost", "catalyst-trading", "expected-shortfall", "advanced-concepts"],
    ))

    # 30. Performance Attribution after a Drawdown
    problems.append(Problem(
        id="adv_fsp_005",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.HARD,
        question="""After a 12% drawdown, factor attribution shows -9% from market, -1% from volatility, -2% idiosyncratic.

What conclusions should NOT be drawn, and what actions are justified?""",
        context=FinancialContext(
            company_name="Drawdown Attribution",
            ticker="N/A",
            sector="Multi-sector",
            model_assumptions={
                "Portfolio drawdown": "-12%",
                "Market attribution": "-9%",
                "Volatility factor": "-1%",
                "Idiosyncratic": "-2%",
                "Portfolio beta": 1.1,
                "Market drawdown": "-8%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="DON'T conclude: 'stock picking failed' (only -2% idiosyncratic), 'reduce beta' (market timing is hard). DO: assess if -2% idiosyncratic is within expected range, review vol factor exposure, maintain process unless idiosyncratic losses persist across multiple periods.",
        answer_options=[
            AnswerOption(id="A", text="Fire the PM - 12% drawdown is unacceptable", is_correct=False),
            AnswerOption(id="B", text="Reduce beta immediately to prevent future market losses", is_correct=False),
            AnswerOption(id="C", text="DON'T conclude: 'stock picking failed' (only -2% idiosyncratic), 'reduce beta' (market timing is hard). DO: assess if -2% idiosyncratic is within expected range, review vol factor exposure, maintain process unless idiosyncratic losses persist across multiple periods.", is_correct=True),
            AnswerOption(id="D", text="Attribution is meaningless - only total return matters", is_correct=False),
        ],
        explanation="Attribution shows: (1) Market: -9% with beta 1.1 and market -8% ≈ expected, (2) Vol factor: -1% - small but review if intentional, (3) Idiosyncratic: -2% - is this 1 std dev? 2 std dev? If expected idiosyncratic vol is 3%, then -2% is <1 sigma, completely normal. Knee-jerk beta reduction is market timing. Only idiosyncratic losses warrant stock selection review, and only if persistent.",
        reasoning_steps=[
            "Separate controllable (stock selection) from uncontrollable (market) losses",
            "Assess idiosyncratic loss vs. expected idiosyncratic volatility",
            "Avoid market timing reactions to market-driven losses",
            "Review factor exposures (vol factor) for intentionality",
            "Maintain process unless pattern of idiosyncratic underperformance"
        ],
        tags=["performance-attribution", "drawdown-analysis", "process-review", "factor-decomposition", "advanced-concepts"],
    ))

    return problems


if __name__ == "__main__":
    # Generate and print summary
    problems = generate_advanced-concepts_problems()
    print(f"Generated {len(problems)} advanced concept problems")

    # Category distribution
    from collections import Counter
    categories = Counter(p.category.value for p in problems)
    difficulties = Counter(p.difficulty.value for p in problems)

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print("\nDifficulty distribution:")
    for diff, count in sorted(difficulties.items()):
        print(f"  {diff}: {count}")
