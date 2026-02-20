"""
Concept-Driven Finance Reasoning Problems

30 framework-agnostic problems testing first-principles understanding of:
- Sources of excess returns & market structure
- Returns, measurement, and estimation error
- Factor models & alpha separation
- Portfolio construction & optimization
- Attribution & learning from outcomes

These problems stress reasoning under constraints (estimation error, liquidity,
funding, turnover) and are model-portable (Axioma, Barra, in-house, academic).
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


def generate_quant_concept_problems() -> list[Problem]:
    """Generate 30 concept-driven quant/finance problems."""
    problems = []

    # =========================================================================
    # I. SOURCES OF EXCESS RETURNS & MARKET STRUCTURE (6 problems)
    # =========================================================================

    # 1. Predictability Without Profitability
    problems.append(Problem(
        id="qc_market_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A return predictor has strong out-of-sample accuracy but trades in securities with large bid-ask spreads and low turnover.

Explain how a signal can be statistically valid yet economically worthless.""",
        context=FinancialContext(
            company_name="Signal Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Signal IC": "0.08 (strong)",
                "Avg bid-ask spread": "2.5%",
                "Daily turnover": "0.3% of float",
                "Signal turnover": "40% monthly"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Transaction costs (spreads + market impact) can exceed expected returns. A signal predicting 1% monthly return is worthless if round-trip costs are 3%. Statistical validity measures prediction accuracy; economic validity requires net-of-cost profitability.",
        answer_options=[
            AnswerOption(id="A", text="Statistical significance always implies economic significance", is_correct=False),
            AnswerOption(id="B", text="Transaction costs (spreads + market impact) can exceed expected returns. A signal predicting 1% monthly return is worthless if round-trip costs are 3%. Statistical validity measures prediction accuracy; economic validity requires net-of-cost profitability.", is_correct=True),
            AnswerOption(id="C", text="Low turnover securities are always unprofitable to trade", is_correct=False),
            AnswerOption(id="D", text="The signal must be wrong if it doesn't make money", is_correct=False),
        ],
        explanation="Expected gross return from signal = IC * volatility * sqrt(breadth). But net return = gross return - transaction costs. With 2.5% spreads and 40% monthly turnover, costs ≈ 2% monthly (0.4 * 2.5% * 2 for round-trip). If signal generates 1.5% gross, net return is negative. The signal correctly predicts direction but can't overcome friction.",
        reasoning_steps=[
            "Distinguish statistical validity (prediction accuracy) from economic validity (profitability)",
            "Calculate transaction cost drag: spread * turnover * 2 (round-trip)",
            "Compare gross expected return to transaction costs",
            "Market impact in illiquid names adds additional costs beyond spread",
            "A valid signal becomes worthless when implementation costs exceed alpha"
        ],
        tags=["transaction-costs", "market-microstructure", "signal-decay", "quant-concepts"],
    ))

    # 2. Flow Anticipation vs. Information Advantage
    problems.append(Problem(
        id="qc_market_002",
        category=ProblemCategory.CATALYST_ID,
        difficulty=Difficulty.EXPERT,
        question="""A strategy profits by buying assets before predictable institutional demand.

Why is this not equivalent to trading on superior information, and what risks does it embed?""",
        context=FinancialContext(
            company_name="Flow Strategy Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Strategy": "Front-run index rebalances",
                "Avg return": "50 bps per event",
                "Frequency": "Quarterly",
                "Crowding metric": "Increasing over time"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Flow anticipation exploits predictable demand, not superior fundamental knowledge. Risks: (1) Crowding erodes returns as more participants front-run, (2) Flow timing uncertainty creates inventory risk, (3) Index methodology changes can eliminate the signal entirely.",
        answer_options=[
            AnswerOption(id="A", text="It is equivalent to information advantage - both predict returns", is_correct=False),
            AnswerOption(id="B", text="Flow anticipation exploits predictable demand, not superior fundamental knowledge. Risks: (1) Crowding erodes returns as more participants front-run, (2) Flow timing uncertainty creates inventory risk, (3) Index methodology changes can eliminate the signal entirely.", is_correct=True),
            AnswerOption(id="C", text="Flow strategies have no risks since flows are predictable", is_correct=False),
            AnswerOption(id="D", text="This strategy is illegal front-running", is_correct=False),
        ],
        explanation="Information advantage implies knowing something about fundamental value others don't. Flow anticipation knows something about future demand, not value. The asset may be overpriced, but demand will temporarily push it higher. Risks: crowding (everyone front-runs, compressing returns), timing (flows may be delayed or cancelled), and structural (index rules change). This is closer to liquidity provision than information trading.",
        reasoning_steps=[
            "Distinguish information about value vs. information about demand",
            "Flow anticipation profits from price impact, not mispricing correction",
            "Crowding risk: more participants = smaller pie",
            "Timing risk: predicted flows may not materialize",
            "Structural risk: the predictable pattern can disappear"
        ],
        tags=["flow-trading", "crowding", "market-structure", "quant-concepts"],
    ))

    # 3. Liquidity as a Risk Factor
    problems.append(Problem(
        id="qc_market_003",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""Two assets have identical volatility and expected returns, but one is harder to trade in stress.

Why should rational investors demand higher compensation for one over the other?""",
        context=FinancialContext(
            company_name="Liquidity Risk Analysis",
            ticker="N/A",
            sector="Multi-asset",
            model_assumptions={
                "Asset A vol": "20%",
                "Asset B vol": "20%",
                "Asset A expected return": "8%",
                "Asset B expected return": "8%",
                "Asset A stress liquidity": "Normal",
                "Asset B stress liquidity": "Severely impaired"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Illiquidity is worst when you most need to trade - during stress when portfolio rebalancing or redemptions force sales. Asset B's liquidity impairment correlates with bad states of the world, creating an additional risk factor beyond volatility. Rational investors demand a liquidity premium.",
        answer_options=[
            AnswerOption(id="A", text="Volatility fully captures risk - liquidity doesn't matter", is_correct=False),
            AnswerOption(id="B", text="Illiquidity is worst when you most need to trade - during stress when portfolio rebalancing or redemptions force sales. Asset B's liquidity impairment correlates with bad states of the world, creating an additional risk factor beyond volatility. Rational investors demand a liquidity premium.", is_correct=True),
            AnswerOption(id="C", text="Investors should avoid illiquid assets entirely", is_correct=False),
            AnswerOption(id="D", text="Expected returns already account for liquidity differences", is_correct=False),
        ],
        explanation="Volatility measures price variation, not tradability. Asset B's liquidity dries up precisely when investors need to exit (margin calls, redemptions, risk reduction). This correlation with bad states makes it riskier than volatility alone suggests. The liquidity premium compensates for: (1) inability to exit at fair value, (2) forced holding during drawdowns, (3) potential fire-sale losses. Empirically, illiquid assets earn 2-4% annual premium.",
        reasoning_steps=[
            "Volatility measures price risk, not transaction risk",
            "Liquidity risk is state-dependent - worst in crises",
            "Correlation of illiquidity with market stress creates systematic risk",
            "Investors rationally demand compensation for this additional risk",
            "Liquidity premium is compensation for holding hard-to-exit assets"
        ],
        tags=["liquidity-risk", "risk-premium", "market-stress", "quant-concepts"],
    ))

    # 4. Funding Constraints and Missed Opportunities
    problems.append(Problem(
        id="qc_market_004",
        category=ProblemCategory.DCF_SANITY,
        difficulty=Difficulty.HARD,
        question="""During a market selloff, a strategy identifies large mispricings but reduces exposure.

Explain why capital constraints can dominate return forecasts.""",
        context=FinancialContext(
            company_name="Funding Constraint Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Identified mispricing": "15% (historically high)",
                "Current drawdown": "-18%",
                "Margin call threshold": "-25%",
                "Leverage": "3x",
                "Client redemption queue": "12% of AUM"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="With 3x leverage and -18% drawdown, the fund is near margin call (-25%). Adding risk increases probability of forced liquidation at worst prices. Redemptions require cash, forcing sales. The opportunity cost of missing the mispricing is less than the expected cost of fund failure.",
        answer_options=[
            AnswerOption(id="A", text="Large mispricings should always be exploited regardless of constraints", is_correct=False),
            AnswerOption(id="B", text="With 3x leverage and -18% drawdown, the fund is near margin call (-25%). Adding risk increases probability of forced liquidation at worst prices. Redemptions require cash, forcing sales. The opportunity cost of missing the mispricing is less than the expected cost of fund failure.", is_correct=True),
            AnswerOption(id="C", text="Capital constraints are never a valid reason to miss opportunities", is_correct=False),
            AnswerOption(id="D", text="The strategy should increase leverage to capture the mispricing", is_correct=False),
        ],
        explanation="Survival dominates optimization. At -18% with 3x leverage and -25% margin call, another 2-3% move forces liquidation. Expected value of adding risk: (probability of mispricing converging) * (profit) - (probability of margin call) * (forced liquidation loss). With redemptions pending, cash needs further constrain action. Rational behavior is to reduce risk and survive, accepting opportunity cost.",
        reasoning_steps=[
            "Calculate distance to margin call: -25% - (-18%) = 7% cushion",
            "With 3x leverage, 2.3% market move triggers margin call",
            "Pending redemptions require cash, forcing additional sales",
            "Survival constraint: probability of fund failure must stay low",
            "Opportunity cost < expected cost of forced liquidation"
        ],
        tags=["funding-constraints", "leverage", "risk-management", "quant-concepts"],
    ))

    # 5. Retail Flow as an Alpha Source
    problems.append(Problem(
        id="qc_market_005",
        category=ProblemCategory.EARNINGS_SURPRISE,
        difficulty=Difficulty.MEDIUM,
        question="""Retail investors are unprofitable on average.

How can their trading behavior still create systematic opportunities?""",
        context=FinancialContext(
            company_name="Retail Flow Analysis",
            ticker="N/A",
            sector="Market Structure",
            model_assumptions={
                "Retail avg return": "-3% vs market",
                "Retail trading volume": "25% of market",
                "Behavior patterns": "Buy winners, sell losers, overreact to news"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Retail losses are someone's gains. Predictable behavior (momentum chasing, disposition effect, news overreaction) creates temporary mispricings. Strategies can: (1) provide liquidity to retail flow, (2) fade retail overreaction, (3) anticipate retail demand patterns. The alpha comes from being the counterparty.",
        answer_options=[
            AnswerOption(id="A", text="Retail losses disappear into bid-ask spreads with no alpha opportunity", is_correct=False),
            AnswerOption(id="B", text="Retail losses are someone's gains. Predictable behavior (momentum chasing, disposition effect, news overreaction) creates temporary mispricings. Strategies can: (1) provide liquidity to retail flow, (2) fade retail overreaction, (3) anticipate retail demand patterns. The alpha comes from being the counterparty.", is_correct=True),
            AnswerOption(id="C", text="Retail investors are too small to create meaningful opportunities", is_correct=False),
            AnswerOption(id="D", text="It's unethical to profit from retail investor mistakes", is_correct=False),
        ],
        explanation="Markets are zero-sum for alpha. Retail's -3% underperformance flows to counterparties. Systematic patterns: (1) Disposition effect (sell winners, hold losers) creates short-term momentum, (2) Attention-driven buying (news, social media) causes overreaction, (3) Predictable timing (market open, meme cycles) enables positioning. Market makers and quantitative strategies capture this through liquidity provision and contrarian positioning.",
        reasoning_steps=[
            "Alpha is zero-sum: one trader's loss is another's gain",
            "Retail behavior is systematic and predictable",
            "Disposition effect: retail sells winners too early, holds losers too long",
            "Attention effects: retail buys stocks in the news",
            "Counterparty strategies capture retail's systematic losses"
        ],
        tags=["retail-flow", "market-structure", "behavioral-finance", "quant-concepts"],
    ))

    # 6. Standardization Trade-offs
    problems.append(Problem(
        id="qc_market_006",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.MEDIUM,
        question="""Highly standardized contracts improve liquidity but reduce expressiveness.

When does reduced customization lower expected returns?""",
        context=FinancialContext(
            company_name="Contract Design Analysis",
            ticker="N/A",
            sector="Derivatives",
            model_assumptions={
                "Standardized future": "High liquidity, fixed specs",
                "Custom OTC swap": "Low liquidity, exact exposure",
                "Hedging need": "Non-standard risk profile"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="When the standardized contract doesn't match your exposure, you either: (1) leave risk unhedged (basis risk), or (2) over/under-hedge, creating new exposures. Basis risk from imperfect hedging can exceed the liquidity benefit. Custom contracts provide exact hedge but at higher transaction costs.",
        answer_options=[
            AnswerOption(id="A", text="Standardization always improves returns through lower costs", is_correct=False),
            AnswerOption(id="B", text="When the standardized contract doesn't match your exposure, you either: (1) leave risk unhedged (basis risk), or (2) over/under-hedge, creating new exposures. Basis risk from imperfect hedging can exceed the liquidity benefit. Custom contracts provide exact hedge but at higher transaction costs.", is_correct=True),
            AnswerOption(id="C", text="Custom contracts always outperform standardized ones", is_correct=False),
            AnswerOption(id="D", text="Basis risk is negligible compared to liquidity benefits", is_correct=False),
        ],
        explanation="Trade-off: standardized (liquid, cheap, imprecise) vs. custom (illiquid, expensive, precise). If your risk profile is non-standard (e.g., specific commodity grade, unusual tenor), standardized hedge leaves basis risk. Example: hedging jet fuel with crude futures leaves crack spread risk. When basis volatility is high relative to hedge cost savings, customization is worth the illiquidity premium.",
        reasoning_steps=[
            "Standardization improves liquidity by concentrating trading",
            "Mismatch between standard contract and actual exposure creates basis risk",
            "Basis risk = volatility of (actual exposure - hedge)",
            "Trade-off: liquidity savings vs. basis risk costs",
            "Custom contracts eliminate basis risk but cost more to trade"
        ],
        tags=["derivatives", "basis-risk", "liquidity", "quant-concepts"],
    ))

    # =========================================================================
    # II. RETURNS, MEASUREMENT, AND ESTIMATION ERROR (6 problems)
    # =========================================================================

    # 7. Log Returns vs. Arithmetic Returns
    problems.append(Problem(
        id="qc_measure_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.MEDIUM,
        question="""A portfolio aggregates daily log returns to estimate long-term performance.

Under what conditions is this approximation invalid, and why does it matter?""",
        context=FinancialContext(
            company_name="Return Calculation Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Return Calculation:
- Daily log returns: r_t = ln(P_t / P_{t-1})
- Monthly aggregation: R_month = sum(r_daily)
- High volatility asset: 5% daily vol
- Leverage: 3x"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Log returns are time-additive but not portfolio-additive. For high volatility or leveraged positions, the log-to-arithmetic return gap grows: E[arithmetic] = E[log] + 0.5*var. A 5% daily vol with 3x leverage means ~22.5% vol, creating ~2.5% annual drag from the volatility tax.",
        answer_options=[
            AnswerOption(id="A", text="Log returns are always equivalent to arithmetic returns", is_correct=False),
            AnswerOption(id="B", text="Log returns are time-additive but not portfolio-additive. For high volatility or leveraged positions, the log-to-arithmetic return gap grows: E[arithmetic] = E[log] + 0.5*var. A 5% daily vol with 3x leverage means ~22.5% vol, creating ~2.5% annual drag from the volatility tax.", is_correct=True),
            AnswerOption(id="C", text="Log returns always overstate performance", is_correct=False),
            AnswerOption(id="D", text="The difference only matters for daily data", is_correct=False),
        ],
        explanation="Log returns sum across time; arithmetic returns compound. The gap: E[arithmetic] ≈ E[log] + σ²/2. With 3x leverage on 5% daily vol: σ_daily = 15%, σ_annual ≈ 15% * √252 ≈ 238%. Volatility drag = 238%²/2 ≈ 283% annual! This extreme example shows why log approximation fails for leveraged/volatile positions. The 'volatility tax' destroys compounded wealth even with zero expected log return.",
        reasoning_steps=[
            "Log returns are additive across time: sum of daily = period return",
            "Arithmetic returns compound: (1+r1)*(1+r2)-1 ≠ r1+r2",
            "Gap between log and arithmetic: approximately σ²/2",
            "High volatility magnifies this gap significantly",
            "Leveraged positions amplify the 'volatility tax'"
        ],
        tags=["return-calculation", "volatility-drag", "leverage", "quant-concepts"],
    ))

    # 8. Price Noise and Return Estimation
    problems.append(Problem(
        id="qc_measure_002",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""Returns are computed from last-trade prices in a wide-spread market.

How does microstructure noise bias volatility estimates?""",
        context=FinancialContext(
            company_name="Microstructure Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Price Data:
- Bid-ask spread: 1%
- Last trade: randomly bid or ask
- True volatility: 2% daily
- Observed volatility from last trades: ?"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Bid-ask bounce adds spurious variance. If prices randomly bounce between bid and ask, observed returns include noise ≈ (spread/2)². With 1% spread, noise variance ≈ 0.25%². This overstates true volatility, especially at high frequencies. Realized volatility estimators must correct for this bias.",
        answer_options=[
            AnswerOption(id="A", text="Microstructure noise doesn't affect volatility estimates", is_correct=False),
            AnswerOption(id="B", text="Bid-ask bounce adds spurious variance. If prices randomly bounce between bid and ask, observed returns include noise ≈ (spread/2)². With 1% spread, noise variance ≈ 0.25%². This overstates true volatility, especially at high frequencies. Realized volatility estimators must correct for this bias.", is_correct=True),
            AnswerOption(id="C", text="Microstructure noise always understates volatility", is_correct=False),
            AnswerOption(id="D", text="Using mid-prices eliminates all microstructure bias", is_correct=False),
        ],
        explanation="Observed price = true price + microstructure noise. Noise from bid-ask bounce creates negative autocorrelation in returns (up then down). Variance of observed returns = true variance + 2*noise variance (for independent noise). At high frequencies, noise dominates signal. Solutions: use mid-prices, subsample, or apply realized volatility corrections (e.g., Zhang et al. two-scale estimator).",
        reasoning_steps=[
            "Last trade price bounces randomly between bid and ask",
            "This creates artificial return volatility from the bounce",
            "Noise variance ≈ (spread/2)² per return observation",
            "Higher frequency = more noise observations = larger bias",
            "Corrections: mid-prices, subsampling, two-scale estimators"
        ],
        tags=["microstructure", "volatility-estimation", "bid-ask-bounce", "quant-concepts"],
    ))

    # 9. Absence of Autocorrelation ≠ Independence
    problems.append(Problem(
        id="qc_measure_003",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""Daily returns show no autocorrelation.

Why does this not imply unpredictability?""",
        context=FinancialContext(
            company_name="Return Predictability Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Return autocorrelation": "~0 at all lags",
                "Squared return autocorrelation": "0.15 at lag 1",
                "Volume-return correlation": "0.08"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Zero autocorrelation means E[r_t * r_{t-1}] = 0, not that r_t is independent of the past. Squared returns (volatility) can be highly predictable. Other variables (volume, sentiment, order flow) can predict returns. Autocorrelation tests only linear dependence in the return series itself.",
        answer_options=[
            AnswerOption(id="A", text="Zero autocorrelation implies returns are completely unpredictable", is_correct=False),
            AnswerOption(id="B", text="Zero autocorrelation means E[r_t * r_{t-1}] = 0, not that r_t is independent of the past. Squared returns (volatility) can be highly predictable. Other variables (volume, sentiment, order flow) can predict returns. Autocorrelation tests only linear dependence in the return series itself.", is_correct=True),
            AnswerOption(id="C", text="Autocorrelation captures all forms of predictability", is_correct=False),
            AnswerOption(id="D", text="Predictable volatility doesn't help with return prediction", is_correct=False),
        ],
        explanation="Autocorrelation measures linear dependence: corr(r_t, r_{t-1}). But: (1) Non-linear dependence exists - squared returns show strong autocorrelation (GARCH), (2) Cross-variable prediction - volume, sentiment, order imbalance predict returns, (3) Conditional prediction - returns may be predictable given other state variables. Markets remove linear predictability but leave other forms.",
        reasoning_steps=[
            "Autocorrelation measures linear time-series dependence",
            "Zero autocorrelation ≠ independence (only linear independence)",
            "Squared returns (volatility) are highly autocorrelated",
            "Other variables can predict returns even if returns don't predict themselves",
            "Markets are more efficient at removing simple linear patterns"
        ],
        tags=["autocorrelation", "predictability", "volatility-clustering", "quant-concepts"],
    ))

    # 10. Heavy Tails and Risk Estimation
    problems.append(Problem(
        id="qc_measure_004",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""Returns exhibit extreme outliers.

Why does this undermine naïve volatility estimation?""",
        context=FinancialContext(
            company_name="Tail Risk Analysis",
            ticker="N/A",
            sector="Risk Management",
            model_assumptions={
                "Return kurtosis": "8 (vs. 3 for normal)",
                "Largest daily return": "-15%",
                "99% VaR (normal assumption)": "-5.2%",
                "Actual 99th percentile": "-8.1%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Heavy tails mean extreme events occur more frequently than normal distribution predicts. Volatility estimation: (1) Sample variance is highly sensitive to outliers, (2) Normal-based VaR understates tail risk, (3) A single outlier can dominate the variance estimate. Use robust estimators or tail-aware models (t-distribution, extreme value theory).",
        answer_options=[
            AnswerOption(id="A", text="Outliers should be removed as data errors", is_correct=False),
            AnswerOption(id="B", text="Heavy tails mean extreme events occur more frequently than normal distribution predicts. Volatility estimation: (1) Sample variance is highly sensitive to outliers, (2) Normal-based VaR understates tail risk, (3) A single outlier can dominate the variance estimate. Use robust estimators or tail-aware models (t-distribution, extreme value theory).", is_correct=True),
            AnswerOption(id="C", text="Heavy tails only matter for very long horizons", is_correct=False),
            AnswerOption(id="D", text="Adding more data always fixes the outlier problem", is_correct=False),
        ],
        explanation="With kurtosis of 8, returns have much fatter tails than normal. Sample variance: a single -15% day contributes 2.25% to variance, potentially more than hundreds of normal days combined. VaR error: normal 99% = 2.33σ, but heavy-tailed 99% can be 3-4σ. Solutions: use median absolute deviation, winsorize outliers, fit t-distribution, or use extreme value theory for tail estimation.",
        reasoning_steps=[
            "Kurtosis > 3 indicates fatter tails than normal",
            "Sample variance: E[(r - mean)²] is dominated by outliers",
            "One extreme day can move variance estimate significantly",
            "Normal VaR understates tail risk by assuming thin tails",
            "Robust estimators (MAD, trimmed variance) reduce outlier sensitivity"
        ],
        tags=["heavy-tails", "kurtosis", "var", "risk-estimation", "quant-concepts"],
    ))

    # 11. Sampling Frequency and Risk
    problems.append(Problem(
        id="qc_measure_005",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.MEDIUM,
        question="""Using higher-frequency data improves variance estimates but worsens return estimates.

Explain the asymmetry.""",
        context=FinancialContext(
            company_name="Sampling Frequency Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Data Comparison:
- Monthly returns: 60 observations over 5 years
- Daily returns: 1,260 observations over 5 years
- 5-minute returns: ~98,000 observations over 5 years"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Variance estimation error ∝ 1/√N, so more observations help. But expected return estimation error depends on total time span, not observation count. 5 years of daily data has the same return precision as 5 years of monthly data. Variance benefits from frequency; return estimation doesn't.",
        answer_options=[
            AnswerOption(id="A", text="More data always improves both return and variance estimates equally", is_correct=False),
            AnswerOption(id="B", text="Variance estimation error ∝ 1/√N, so more observations help. But expected return estimation error depends on total time span, not observation count. 5 years of daily data has the same return precision as 5 years of monthly data. Variance benefits from frequency; return estimation doesn't.", is_correct=True),
            AnswerOption(id="C", text="Higher frequency data is always worse due to noise", is_correct=False),
            AnswerOption(id="D", text="Return estimation improves more than variance estimation with frequency", is_correct=False),
        ],
        explanation="For variance: standard error ≈ σ²/√(2N). More observations = better estimate. For mean return: standard error ≈ σ/√T where T is time span in years. Doubling observations (daily vs. monthly) doesn't help mean estimation because the same total return is just measured more finely. This is why Sharpe ratios are hard to estimate precisely even with high-frequency data.",
        reasoning_steps=[
            "Variance estimation: precision improves with √N observations",
            "Mean return estimation: precision improves with √T time span",
            "Higher frequency = more N for same T",
            "Variance benefits from N; mean return benefits from T",
            "This explains difficulty in estimating expected returns precisely"
        ],
        tags=["sampling-frequency", "estimation-error", "sharpe-ratio", "quant-concepts"],
    ))

    # 12. Volatility Clustering
    problems.append(Problem(
        id="qc_measure_006",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""Large moves tend to cluster in time.

Why does this matter more for portfolio construction than return forecasting?""",
        context=FinancialContext(
            company_name="Volatility Dynamics Analysis",
            ticker="N/A",
            sector="Risk Management",
            model_assumptions={
                "GARCH(1,1) persistence": "0.95",
                "Unconditional vol": "20%",
                "Current vol (after shock)": "35%",
                "Expected vol next month": "32%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Volatility is highly predictable (GARCH persistence ~0.95), but return direction isn't. For portfolio construction: predictable vol enables dynamic sizing (reduce exposure in high-vol regimes). For return forecasting: vol prediction helps with confidence intervals but not point forecasts. Risk management benefits more than alpha generation.",
        answer_options=[
            AnswerOption(id="A", text="Volatility clustering helps predict return direction", is_correct=False),
            AnswerOption(id="B", text="Volatility is highly predictable (GARCH persistence ~0.95), but return direction isn't. For portfolio construction: predictable vol enables dynamic sizing (reduce exposure in high-vol regimes). For return forecasting: vol prediction helps with confidence intervals but not point forecasts. Risk management benefits more than alpha generation.", is_correct=True),
            AnswerOption(id="C", text="Volatility clustering has no practical applications", is_correct=False),
            AnswerOption(id="D", text="High volatility always means negative expected returns", is_correct=False),
        ],
        explanation="GARCH shows vol is ~95% persistent: today's vol strongly predicts tomorrow's. But returns remain nearly unpredictable. Applications: (1) Position sizing: reduce exposure when vol is high to maintain constant risk, (2) Options: predicted vol affects pricing, (3) VaR: dynamic risk limits. The predictability is in the second moment (variance), not first moment (return), making it more useful for risk than alpha.",
        reasoning_steps=[
            "Volatility clusters: high vol today → likely high vol tomorrow",
            "GARCH persistence of 0.95 means strong predictability",
            "Return direction remains essentially unpredictable",
            "Predictable vol enables dynamic position sizing",
            "Risk management benefits more than return forecasting"
        ],
        tags=["volatility-clustering", "garch", "risk-management", "quant-concepts"],
    ))

    # =========================================================================
    # III. FACTOR MODELS & ALPHA SEPARATION (6 problems)
    # =========================================================================

    # 13. Alpha vs. Factor Drift
    problems.append(Problem(
        id="qc_factor_001",
        category=ProblemCategory.EARNINGS_SURPRISE,
        difficulty=Difficulty.HARD,
        question="""A stock outperforms, but its factor exposures change significantly.

How do you determine whether the gain is true alpha?""",
        context=FinancialContext(
            company_name="Alpha Attribution Analysis",
            ticker="OUTPERF",
            sector="Technology",
            model_assumptions={
                "Stock return": "+25%",
                "Benchmark return": "+10%",
                "Factor exposures (start)": "Beta=1.0, Mom=0.2, Size=-0.1",
                "Factor exposures (end)": "Beta=1.4, Mom=0.8, Size=0.3"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Factor drift confounds alpha attribution. If exposures changed, use average exposures or time-varying attribution. The stock may have outperformed because it loaded onto winning factors (momentum), not due to idiosyncratic alpha. True alpha is the residual after accounting for time-varying factor contributions.",
        answer_options=[
            AnswerOption(id="A", text="Any outperformance above benchmark is alpha", is_correct=False),
            AnswerOption(id="B", text="Factor drift confounds alpha attribution. If exposures changed, use average exposures or time-varying attribution. The stock may have outperformed because it loaded onto winning factors (momentum), not due to idiosyncratic alpha. True alpha is the residual after accounting for time-varying factor contributions.", is_correct=True),
            AnswerOption(id="C", text="Factor exposure changes don't affect alpha calculation", is_correct=False),
            AnswerOption(id="D", text="Use end-of-period factor exposures for attribution", is_correct=False),
        ],
        explanation="Static attribution: return = alpha + Σ(beta_i * factor_i). But if betas change, which betas to use? The stock's momentum loading increased from 0.2 to 0.8 - if momentum was +15%, using end-of-period betas overstates factor contribution. Solutions: (1) Average exposures, (2) Rolling attribution with time-varying betas, (3) Regression-based decomposition. True alpha is residual after proper factor adjustment.",
        reasoning_steps=[
            "Standard attribution assumes constant factor exposures",
            "When exposures drift, attribution becomes ambiguous",
            "Stock may have loaded onto winning factors (luck, not skill)",
            "Time-varying attribution accounts for exposure changes",
            "True alpha = residual after accounting for all factor contributions"
        ],
        tags=["alpha-attribution", "factor-drift", "performance-analysis", "quant-concepts"],
    ))

    # 14. Factor Neutral ≠ Risk Neutral (Repeated theme but different angle)
    problems.append(Problem(
        id="qc_factor_002",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A portfolio is beta-neutral but suffers large drawdowns.

What assumptions failed?""",
        context=FinancialContext(
            company_name="Beta Neutral Analysis",
            ticker="N/A",
            sector="Multi-sector",
            formula_context="""Portfolio:
- Long $100M high-growth stocks (beta 1.6)
- Short $160M low-growth stocks (beta 1.0)
- Net beta: 0.0
- Drawdown during selloff: -15%
- Market drawdown: -10%"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Failed assumptions: (1) Constant betas - betas increase in selloffs, (2) Single factor - other factors (value, quality, momentum) created exposure, (3) Linear relationships - convexity effects in stress. Beta-neutrality hedges only linear market exposure under normal conditions.",
        answer_options=[
            AnswerOption(id="A", text="The beta calculation was simply wrong", is_correct=False),
            AnswerOption(id="B", text="Failed assumptions: (1) Constant betas - betas increase in selloffs, (2) Single factor - other factors (value, quality, momentum) created exposure, (3) Linear relationships - convexity effects in stress. Beta-neutrality hedges only linear market exposure under normal conditions.", is_correct=True),
            AnswerOption(id="C", text="Beta-neutral portfolios cannot have drawdowns", is_correct=False),
            AnswerOption(id="D", text="The portfolio just had bad stock selection", is_correct=False),
        ],
        explanation="Beta is estimated from historical data assuming: constant relationship, linear dependence, and market is the only factor. In selloffs: (1) High-beta names become even higher beta (convexity), (2) Correlations spike ('correlation goes to 1'), (3) Other factors move against the portfolio (growth vs. value). The -15% vs -10% market suggests growth underperformed value, and beta estimates were stale.",
        reasoning_steps=[
            "Beta-neutral assumes constant, linear, single-factor relationship",
            "Selloffs violate all three assumptions",
            "Betas increase in stress (beta asymmetry)",
            "Other factor exposures (growth vs. value) create risk",
            "Correlation spikes reduce diversification benefit"
        ],
        tags=["beta-neutral", "factor-model", "stress-testing", "quant-concepts"],
    ))

    # 15. Correlated Alphas
    problems.append(Problem(
        id="qc_factor_003",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""Many signals show positive expected returns but are highly correlated.

Why does this reduce portfolio-level alpha?""",
        context=FinancialContext(
            company_name="Signal Correlation Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Number of signals": 10,
                "Average signal alpha": "2%",
                "Naïve expectation": "20% combined",
                "Signal correlation": "0.6 average",
                "Realized portfolio alpha": "4%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Correlated signals are redundant - they're betting on the same underlying theme. 10 signals at 0.6 correlation ≈ 3-4 independent signals. Effective breadth = N / (1 + (N-1)*ρ) ≈ 2.5. Alpha doesn't scale linearly with signal count when signals overlap. Diversification across truly independent signals is required.",
        answer_options=[
            AnswerOption(id="A", text="Signal alphas always add linearly regardless of correlation", is_correct=False),
            AnswerOption(id="B", text="Correlated signals are redundant - they're betting on the same underlying theme. 10 signals at 0.6 correlation ≈ 3-4 independent signals. Effective breadth = N / (1 + (N-1)*ρ) ≈ 2.5. Alpha doesn't scale linearly with signal count when signals overlap. Diversification across truly independent signals is required.", is_correct=True),
            AnswerOption(id="C", text="Correlation only affects risk, not expected alpha", is_correct=False),
            AnswerOption(id="D", text="More signals always improve performance", is_correct=False),
        ],
        explanation="Fundamental law: IR ≈ IC * √(breadth). But 'breadth' is effective independent bets, not signal count. With 0.6 correlation: 10 signals effectively become ~2.5 independent bets. If each independent bet has 2% alpha, total ≈ 5%, not 20%. The signals likely capture the same underlying factor (momentum, value, quality) from different angles. True diversification requires orthogonal signals.",
        reasoning_steps=[
            "Correlated signals capture similar information",
            "Effective breadth = N / (1 + (N-1)*ρ)",
            "With ρ=0.6, 10 signals ≈ 2.5 independent signals",
            "Alpha scales with √(effective breadth), not N",
            "Need orthogonal signals for true diversification"
        ],
        tags=["signal-correlation", "breadth", "fundamental-law", "quant-concepts"],
    ))

    # 16. Hidden Factor Bets (Similar to earlier but different angle)
    problems.append(Problem(
        id="qc_factor_004",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""An equal-weighted portfolio underperforms during momentum reversals.

Explain how 'neutral' portfolios can embed factor exposure.""",
        context=FinancialContext(
            company_name="Hidden Factor Analysis",
            ticker="N/A",
            sector="Multi-sector",
            formula_context="""Portfolio:
- 50 stocks, equal-weighted (2% each)
- Benchmark: cap-weighted
- Momentum factor: -12% during period
- Portfolio vs. benchmark: -8%"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Equal-weighting vs. cap-weighting tilts toward small caps. Small caps have higher momentum exposure historically. The 'neutral' equal-weight construction embeds a hidden long momentum bet that hurts during reversals. Construction choices create implicit factor bets.",
        answer_options=[
            AnswerOption(id="A", text="Equal-weighting is always factor-neutral", is_correct=False),
            AnswerOption(id="B", text="Equal-weighting vs. cap-weighting tilts toward small caps. Small caps have higher momentum exposure historically. The 'neutral' equal-weight construction embeds a hidden long momentum bet that hurts during reversals. Construction choices create implicit factor bets.", is_correct=True),
            AnswerOption(id="C", text="The underperformance is pure stock selection failure", is_correct=False),
            AnswerOption(id="D", text="Momentum reversals don't affect diversified portfolios", is_correct=False),
        ],
        explanation="Equal-weighting gives a $5B company the same weight as a $500B company, creating: (1) Size tilt - overweight small caps vs. cap-weighted, (2) Indirect momentum tilt - small caps have higher momentum loading, (3) Higher turnover - rebalancing to equal weight creates momentum-like trading. The -8% underperformance during -12% momentum reversal shows the hidden factor bet.",
        reasoning_steps=[
            "Equal-weight vs. cap-weight creates implicit size tilt",
            "Small caps have higher momentum factor loading",
            "Rebalancing to equal weight creates momentum-like trading",
            "These implicit bets created exposure to momentum factor",
            "Momentum reversal exposed the hidden factor bet"
        ],
        tags=["hidden-factors", "equal-weighting", "momentum", "quant-concepts"],
    ))

    # 17. Orthogonalization Costs
    problems.append(Problem(
        id="qc_factor_005",
        category=ProblemCategory.DCF_SANITY,
        difficulty=Difficulty.HARD,
        question="""Removing factor exposure lowers expected returns.

When is this trade-off justified?""",
        context=FinancialContext(
            company_name="Orthogonalization Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Raw signal alpha": "4%",
                "Factor-neutral alpha": "2%",
                "Raw signal volatility": "15%",
                "Factor-neutral volatility": "8%",
                "Raw Sharpe": "0.27",
                "Factor-neutral Sharpe": "0.25"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Orthogonalization removes factor exposure, reducing both return and risk. Justified when: (1) Factor exposure is unintentional and unrewarded, (2) Client mandate requires factor neutrality, (3) Risk-adjusted return (Sharpe) improves, or (4) Regulatory/risk constraints limit factor exposure. Here Sharpe is similar, so decision depends on constraints.",
        answer_options=[
            AnswerOption(id="A", text="Factor orthogonalization always destroys value", is_correct=False),
            AnswerOption(id="B", text="Orthogonalization removes factor exposure, reducing both return and risk. Justified when: (1) Factor exposure is unintentional and unrewarded, (2) Client mandate requires factor neutrality, (3) Risk-adjusted return (Sharpe) improves, or (4) Regulatory/risk constraints limit factor exposure. Here Sharpe is similar, so decision depends on constraints.", is_correct=True),
            AnswerOption(id="C", text="Always maximize expected return regardless of factor exposure", is_correct=False),
            AnswerOption(id="D", text="Factor exposure is always undesirable", is_correct=False),
        ],
        explanation="Raw signal: 4% return, 15% vol, Sharpe 0.27. Factor-neutral: 2% return, 8% vol, Sharpe 0.25. The factor exposure contributed 2% return and 7% vol - was this intentional? If not, removing it clarifies the true alpha. Decision framework: (1) Is factor exposure compensated? (2) Does mandate allow it? (3) Does orthogonalization improve Sharpe? Here Sharpe is similar, so it's a constraint-driven decision.",
        reasoning_steps=[
            "Orthogonalization removes factor exposure from signal",
            "This reduces both expected return and risk",
            "Trade-off depends on whether factor exposure is desired",
            "Sharpe ratio comparison: 0.27 vs 0.25 - similar risk-adjusted",
            "Decision depends on mandate constraints and factor exposure intent"
        ],
        tags=["orthogonalization", "factor-neutrality", "sharpe-ratio", "quant-concepts"],
    ))

    # 18. Time-Varying Betas
    problems.append(Problem(
        id="qc_factor_006",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""Factor loadings shift in stressed markets.

Why is static hedging dangerous?""",
        context=FinancialContext(
            company_name="Dynamic Beta Analysis",
            ticker="N/A",
            sector="Risk Management",
            model_assumptions={
                "Normal period beta": "1.2",
                "Stress period beta": "1.8",
                "Hedge ratio (static)": "1.2",
                "Market selloff": "-20%",
                "Expected hedged loss": "0%",
                "Actual hedged loss": "-12%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Static hedging uses historical beta, but beta increases in stress (convexity, flight-to-quality). With 1.2 hedge and 1.8 actual beta during -20% selloff: hedged position = -20%*1.8 + 20%*1.2 = -12%. The hedge underperformed precisely when needed most. Dynamic hedging or hedge buffers are required.",
        answer_options=[
            AnswerOption(id="A", text="Betas are constant - the hedge must have been wrong", is_correct=False),
            AnswerOption(id="B", text="Static hedging uses historical beta, but beta increases in stress (convexity, flight-to-quality). With 1.2 hedge and 1.8 actual beta during -20% selloff: hedged position = -20%*1.8 + 20%*1.2 = -12%. The hedge underperformed precisely when needed most. Dynamic hedging or hedge buffers are required.", is_correct=True),
            AnswerOption(id="C", text="A -12% loss on a hedged position is acceptable", is_correct=False),
            AnswerOption(id="D", text="Hedges always fail in stress markets", is_correct=False),
        ],
        explanation="Beta asymmetry: betas are higher when markets fall than when they rise. This is due to: (1) Leverage effects - falling prices increase financial leverage, (2) Flight to quality - risky assets become more correlated, (3) Liquidity effects - selling pressure disproportionately hits risky assets. Static 1.2 hedge was short 12% (1.2 * -20%), but position lost 36% (1.8 * -20%), net -12%. Solutions: use stress betas, add hedge buffer, or use options for tail protection.",
        reasoning_steps=[
            "Historical beta estimated from normal periods",
            "Beta increases during stress (leverage, correlation spike)",
            "Static hedge based on historical beta is insufficient",
            "Hedge loss: -20% * (1.8 - 1.2) = -12%",
            "Need dynamic hedging or stress-adjusted hedge ratios"
        ],
        tags=["time-varying-beta", "hedging", "stress-testing", "quant-concepts"],
    ))

    # =========================================================================
    # IV. PORTFOLIO CONSTRUCTION & OPTIMIZATION (6 problems)
    # =========================================================================

    # 19. Mean-Variance Fragility
    problems.append(Problem(
        id="qc_port_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""An optimizer produces extreme weights.

Identify the role of estimation error.""",
        context=FinancialContext(
            company_name="Optimization Analysis",
            ticker="N/A",
            sector="Portfolio Construction",
            model_assumptions={
                "Number of assets": 50,
                "Historical data": "5 years",
                "Optimizer output": "40% in one stock, -30% shorts",
                "Expected return estimates": "±2% estimation error"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Mean-variance optimizers amplify estimation errors. Small errors in expected returns get multiplied by the inverse covariance matrix, producing extreme weights. With 50 assets and 5 years of data, return estimates have large error bars (±2%), but the optimizer treats them as precise. Result: extreme positions in assets with noisy but favorable estimates.",
        answer_options=[
            AnswerOption(id="A", text="Extreme weights indicate high conviction - optimizer is correct", is_correct=False),
            AnswerOption(id="B", text="Mean-variance optimizers amplify estimation errors. Small errors in expected returns get multiplied by the inverse covariance matrix, producing extreme weights. With 50 assets and 5 years of data, return estimates have large error bars (±2%), but the optimizer treats them as precise. Result: extreme positions in assets with noisy but favorable estimates.", is_correct=True),
            AnswerOption(id="C", text="Estimation error doesn't affect optimization", is_correct=False),
            AnswerOption(id="D", text="Use more complex optimization algorithms to fix this", is_correct=False),
        ],
        explanation="MV optimizer: w = Σ⁻¹ * μ / γ. Errors in μ get amplified by Σ⁻¹, especially when assets are correlated (near-singular Σ). With 50 assets and ~1,250 daily observations, we estimate ~1,275 covariance parameters but have limited degrees of freedom. Expected return estimation error ≈ σ/√T is huge. The 40% position reflects estimation error, not true alpha.",
        reasoning_steps=[
            "Mean-variance optimization: w ∝ Σ⁻¹ * μ",
            "Estimation error in μ gets multiplied by inverse covariance",
            "Near-singular covariance matrices amplify errors further",
            "50 assets with 5 years data = massive estimation uncertainty",
            "Extreme weights reflect noise, not signal"
        ],
        tags=["mean-variance", "estimation-error", "optimization", "quant-concepts"],
    ))

    # 20. Constraints as Information
    problems.append(Problem(
        id="qc_port_002",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""Adding constraints improves realized performance.

Why can restricting the optimizer help?""",
        context=FinancialContext(
            company_name="Constrained Optimization Analysis",
            ticker="N/A",
            sector="Portfolio Construction",
            model_assumptions={
                "Unconstrained Sharpe (backtest)": "2.0",
                "Constrained Sharpe (backtest)": "1.2",
                "Unconstrained Sharpe (live)": "0.3",
                "Constrained Sharpe (live)": "0.8"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Constraints reduce overfitting to estimation errors. Unconstrained optimizer exploits noise in historical data (Sharpe 2.0), but noise doesn't persist (live Sharpe 0.3). Constraints (position limits, sector limits) prevent extreme bets on noisy estimates, improving out-of-sample performance despite lower in-sample fit.",
        answer_options=[
            AnswerOption(id="A", text="Constraints always hurt performance by limiting opportunity set", is_correct=False),
            AnswerOption(id="B", text="Constraints reduce overfitting to estimation errors. Unconstrained optimizer exploits noise in historical data (Sharpe 2.0), but noise doesn't persist (live Sharpe 0.3). Constraints (position limits, sector limits) prevent extreme bets on noisy estimates, improving out-of-sample performance despite lower in-sample fit.", is_correct=True),
            AnswerOption(id="C", text="The live period was just bad luck for unconstrained", is_correct=False),
            AnswerOption(id="D", text="Constraints should be removed to maximize returns", is_correct=False),
        ],
        explanation="Bias-variance tradeoff: unconstrained optimizer has low bias (fits data perfectly) but high variance (sensitive to noise). Constraints add bias but reduce variance. In-sample: unconstrained wins. Out-of-sample: constrained wins because it didn't overfit. Constraints act as regularization, shrinking estimates toward prior beliefs (diversification, sector balance).",
        reasoning_steps=[
            "Unconstrained optimizer fits historical data very well (Sharpe 2.0)",
            "But it's fitting noise, not signal",
            "Live performance shows the overfitting (Sharpe 0.3)",
            "Constraints prevent extreme positions on noisy estimates",
            "Bias-variance tradeoff: some bias improves out-of-sample"
        ],
        tags=["constraints", "overfitting", "regularization", "quant-concepts"],
    ))

    # 21. Tracking Error vs. Total Risk
    problems.append(Problem(
        id="qc_port_003",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A manager controls volatility instead of tracking error.

Why does this misalign incentives?""",
        context=FinancialContext(
            company_name="Risk Target Analysis",
            ticker="N/A",
            sector="Asset Management",
            formula_context="""Manager behavior:
- Risk target: 12% total volatility
- Benchmark volatility: 15%
- Manager action: Holds 80% benchmark + 20% cash
- Active return: 0%
- Risk-adjusted return: "Good" by vol measure"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Targeting total volatility incentivizes benchmark-hugging plus cash. Manager hits 12% vol target by diluting exposure (80% benchmark = 12% vol) without active management. Tracking error measures active risk; total vol doesn't distinguish active bets from benchmark exposure. Client pays for alpha but gets cash-diluted beta.",
        answer_options=[
            AnswerOption(id="A", text="Total volatility and tracking error are equivalent measures", is_correct=False),
            AnswerOption(id="B", text="Targeting total volatility incentivizes benchmark-hugging plus cash. Manager hits 12% vol target by diluting exposure (80% benchmark = 12% vol) without active management. Tracking error measures active risk; total vol doesn't distinguish active bets from benchmark exposure. Client pays for alpha but gets cash-diluted beta.", is_correct=True),
            AnswerOption(id="C", text="Cash allocation is always a valid active decision", is_correct=False),
            AnswerOption(id="D", text="Lower total volatility is always better for clients", is_correct=False),
        ],
        explanation="Total vol = √(benchmark_vol² + active_vol² + 2*corr*benchmark_vol*active_vol). At 80% benchmark weight with 0% active: vol = 0.8 * 15% = 12%. Tracking error = 0% (no active positions). Manager meets vol target without taking active risk. Client wanted active management but got leveraged beta with a fee. TE targeting forces manager to deviate from benchmark.",
        reasoning_steps=[
            "Total vol includes benchmark exposure",
            "Tracking error = vol of (portfolio - benchmark)",
            "Manager can reduce total vol by holding cash without active management",
            "This meets vol target while providing zero alpha",
            "Tracking error targets force actual active management"
        ],
        tags=["tracking-error", "total-risk", "incentives", "quant-concepts"],
    ))

    # 22. Diversification vs. Dilution
    problems.append(Problem(
        id="qc_port_004",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.HARD,
        question="""Adding low-conviction positions lowers volatility but Sharpe declines.

Explain why.""",
        context=FinancialContext(
            company_name="Diversification Analysis",
            ticker="N/A",
            sector="Portfolio Construction",
            model_assumptions={
                "High-conviction portfolio (10 positions)": "Sharpe 1.4, vol 18%",
                "Diversified portfolio (50 positions)": "Sharpe 0.9, vol 10%",
                "Added positions conviction": "Low (near-zero expected alpha)"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Sharpe = alpha / volatility. Adding low-alpha positions reduces both numerator and denominator, but alpha drops proportionally more. If new positions have lower Sharpe than existing portfolio, they dilute overall Sharpe even while reducing volatility. Diversification helps risk but hurts risk-adjusted returns when conviction is low.",
        answer_options=[
            AnswerOption(id="A", text="Lower volatility always means higher Sharpe ratio", is_correct=False),
            AnswerOption(id="B", text="Sharpe = alpha / volatility. Adding low-alpha positions reduces both numerator and denominator, but alpha drops proportionally more. If new positions have lower Sharpe than existing portfolio, they dilute overall Sharpe even while reducing volatility. Diversification helps risk but hurts risk-adjusted returns when conviction is low.", is_correct=True),
            AnswerOption(id="C", text="50 positions is always better than 10 positions", is_correct=False),
            AnswerOption(id="D", text="The Sharpe decline is measurement error", is_correct=False),
        ],
        explanation="High-conviction: alpha ≈ 1.4 * 18% = 25.2% (annualized), vol 18%. Diversified: alpha ≈ 0.9 * 10% = 9% (annualized), vol 10%. Adding 40 low-conviction positions reduced vol from 18% to 10% (good) but reduced alpha from 25.2% to 9% (bad). Net: Sharpe fell from 1.4 to 0.9. The marginal positions had Sharpe < 1.4, so they diluted the portfolio.",
        reasoning_steps=[
            "Sharpe ratio = expected excess return / volatility",
            "Diversification reduces volatility through imperfect correlation",
            "But low-conviction positions contribute little to expected return",
            "If new position Sharpe < portfolio Sharpe, it dilutes",
            "Optimal portfolio concentrates in highest-conviction ideas"
        ],
        tags=["diversification", "sharpe-ratio", "conviction", "quant-concepts"],
    ))

    # 23. Capacity and Alpha Decay
    problems.append(Problem(
        id="qc_port_005",
        category=ProblemCategory.CATALYST_ID,
        difficulty=Difficulty.HARD,
        question="""A strategy scales AUM aggressively and performance deteriorates.

Identify the limiting mechanism.""",
        context=FinancialContext(
            company_name="Capacity Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Initial AUM": "$100M",
                "Initial Sharpe": "2.0",
                "Scaled AUM": "$2B",
                "Scaled Sharpe": "0.5",
                "Average daily volume (traded names)": "$50M"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Market impact increases with trade size. At $100M, trades are small vs. $50M daily volume. At $2B, trades move prices significantly, eroding alpha. The strategy's own trading becomes a cost. Additionally, larger positions are slower to build/exit, causing signal decay. Capacity is limited by liquidity of opportunity set.",
        answer_options=[
            AnswerOption(id="A", text="The strategy just stopped working coincidentally", is_correct=False),
            AnswerOption(id="B", text="Market impact increases with trade size. At $100M, trades are small vs. $50M daily volume. At $2B, trades move prices significantly, eroding alpha. The strategy's own trading becomes a cost. Additionally, larger positions are slower to build/exit, causing signal decay. Capacity is limited by liquidity of opportunity set.", is_correct=True),
            AnswerOption(id="C", text="All strategies can scale infinitely", is_correct=False),
            AnswerOption(id="D", text="The market became more efficient, unrelated to AUM", is_correct=False),
        ],
        explanation="At $100M with 20% daily turnover: $20M daily trading vs. $50M volume = 40% of volume, manageable. At $2B: $400M daily trading vs. $50M = 8x daily volume, impossible without massive impact. Market impact ∝ √(trade size / volume). The strategy is now paying its alpha to the market through impact. Solutions: trade slower (signal decay), expand universe (dilute alpha), or cap AUM.",
        reasoning_steps=[
            "Market impact is function of trade size relative to volume",
            "Small fund: trades are invisible to market",
            "Large fund: trades move prices, eating into alpha",
            "Signal decay: slower trading means holding past optimal exit",
            "Capacity = f(alpha, liquidity, signal half-life)"
        ],
        tags=["capacity", "market-impact", "alpha-decay", "quant-concepts"],
    ))

    # 24. Turnover and Signal Half-Life
    problems.append(Problem(
        id="qc_port_006",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A fast-decaying signal is traded slowly.

Why does this destroy expected returns?""",
        context=FinancialContext(
            company_name="Turnover Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Signal half-life": "3 days",
                "Portfolio rebalance frequency": "Monthly",
                "Signal alpha (at generation)": "5%",
                "Signal alpha (at trade)": "~0%"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="With 3-day half-life, alpha decays by 50% every 3 days. After 30 days: alpha = 5% * (0.5)^10 ≈ 0.005%. By the time the monthly rebalance trades, the signal's alpha is essentially zero. Fast signals require fast trading; slow trading wastes the information. Match turnover to signal decay rate.",
        answer_options=[
            AnswerOption(id="A", text="Trading frequency doesn't affect alpha capture", is_correct=False),
            AnswerOption(id="B", text="With 3-day half-life, alpha decays by 50% every 3 days. After 30 days: alpha = 5% * (0.5)^10 ≈ 0.005%. By the time the monthly rebalance trades, the signal's alpha is essentially zero. Fast signals require fast trading; slow trading wastes the information. Match turnover to signal decay rate.", is_correct=True),
            AnswerOption(id="C", text="Lower turnover always improves performance", is_correct=False),
            AnswerOption(id="D", text="Signal half-life is irrelevant for trading decisions", is_correct=False),
        ],
        explanation="Signal decay: alpha_t = alpha_0 * exp(-λt) where λ = ln(2)/half_life. With 3-day half-life and 30-day holding period: alpha_30 = 5% * 2^(-30/3) = 5% * 2^(-10) ≈ 0.005%. The signal predicted a 5% return starting now, but by the time you trade, that information is priced in. This is why high-frequency signals require high-frequency trading, despite transaction costs.",
        reasoning_steps=[
            "Signal alpha decays as information gets priced in",
            "Half-life = time for alpha to decay 50%",
            "3-day half-life: 10 half-lives in 30 days",
            "Remaining alpha after 30 days: 5% * (0.5)^10 ≈ 0",
            "Trading frequency must match signal decay rate"
        ],
        tags=["signal-decay", "turnover", "half-life", "quant-concepts"],
    ))

    # =========================================================================
    # V. AFTER THE TRADE — ATTRIBUTION & LEARNING (6 problems)
    # =========================================================================

    # 25. Performance Attribution Error
    problems.append(Problem(
        id="qc_attr_001",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.HARD,
        question="""Factor attribution explains most losses post-drawdown.

What conclusions should NOT be drawn?""",
        context=FinancialContext(
            company_name="Drawdown Attribution",
            ticker="N/A",
            sector="Multi-sector",
            model_assumptions={
                "Portfolio drawdown": "-15%",
                "Factor attribution": "Market -10%, Value -4%, Residual -1%",
                "Conclusion drawn": "Stock selection is good, just bad factor timing"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="DON'T conclude: (1) 'Stock selection is working' - residual is small but one period is noise, (2) 'Reduce factor exposure now' - that's market timing after the fact, (3) 'Attribution explains causes' - it's decomposition, not causation. DO: assess whether factor exposures were intentional and within mandate.",
        answer_options=[
            AnswerOption(id="A", text="The portfolio manager should be fired for -15% drawdown", is_correct=False),
            AnswerOption(id="B", text="DON'T conclude: (1) 'Stock selection is working' - residual is small but one period is noise, (2) 'Reduce factor exposure now' - that's market timing after the fact, (3) 'Attribution explains causes' - it's decomposition, not causation. DO: assess whether factor exposures were intentional and within mandate.", is_correct=True),
            AnswerOption(id="C", text="Factor losses are always unacceptable", is_correct=False),
            AnswerOption(id="D", text="Attribution fully explains what went wrong", is_correct=False),
        ],
        explanation="Attribution decomposes returns, it doesn't assign blame. Key errors: (1) Small residual could be luck - need multiple periods, (2) Reducing factor exposure after drawdown is timing (selling low), (3) Attribution uses estimated betas which may be wrong, (4) Factor performance is largely uncontrollable. Proper response: was factor exposure intentional? Within mandate? Consistent with process? If yes, accept the outcome.",
        reasoning_steps=[
            "Attribution decomposes returns, doesn't prove causation",
            "Single-period residual is noisy",
            "Reducing exposure after losses is market timing",
            "Factor attribution depends on estimated betas",
            "Focus on process, not outcome attribution"
        ],
        tags=["attribution", "drawdown", "process-review", "quant-concepts"],
    ))

    # 26. Selection vs. Sizing
    problems.append(Problem(
        id="qc_attr_002",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""Correct ideas with wrong sizes underperform.

Why is sizing often the dominant driver of PnL?""",
        context=FinancialContext(
            company_name="Sizing Analysis",
            ticker="N/A",
            sector="Portfolio Construction",
            model_assumptions={
                "Positions with correct direction": "70%",
                "Average win size": "2% of portfolio",
                "Average loss size": "5% of portfolio",
                "Net PnL": "Negative despite 70% hit rate"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="PnL = Σ(size_i * return_i). Even with 70% correct direction, if losses are 2.5x larger than wins, PnL is negative. Common cause: adding to losers (averaging down), cutting winners early, or sizing based on conviction that correlates inversely with actual returns. Sizing skill is distinct from selection skill.",
        answer_options=[
            AnswerOption(id="A", text="High hit rate always leads to positive PnL", is_correct=False),
            AnswerOption(id="B", text="PnL = Σ(size_i * return_i). Even with 70% correct direction, if losses are 2.5x larger than wins, PnL is negative. Common cause: adding to losers (averaging down), cutting winners early, or sizing based on conviction that correlates inversely with actual returns. Sizing skill is distinct from selection skill.", is_correct=True),
            AnswerOption(id="C", text="Sizing is irrelevant if direction is correct", is_correct=False),
            AnswerOption(id="D", text="Always use equal position sizes", is_correct=False),
        ],
        explanation="Expected PnL: 0.7 * 2% - 0.3 * 5% = 1.4% - 1.5% = -0.1%. Despite 70% correct picks, sizing destroys returns. Why does this happen? (1) Behavioral: hold losers, sell winners (disposition effect), (2) Confidence: most confident on worst ideas, (3) Risk management: average down hoping for rebound. Selection and sizing are separate skills - many managers select well but size poorly.",
        reasoning_steps=[
            "PnL is product of position size and return",
            "Selection: which stocks to own",
            "Sizing: how much of each stock",
            "Poor sizing can overwhelm good selection",
            "Common errors: average down, cut winners, overweight bad ideas"
        ],
        tags=["sizing", "selection", "pnl-decomposition", "quant-concepts"],
    ))

    # 27. Alpha Decay vs. Regime Shift
    problems.append(Problem(
        id="qc_attr_003",
        category=ProblemCategory.CATALYST_ID,
        difficulty=Difficulty.EXPERT,
        question="""A signal stops working.

How do you distinguish noise from structural failure?""",
        context=FinancialContext(
            company_name="Signal Failure Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Historical Sharpe (10 years)": "1.2",
                "Recent Sharpe (2 years)": "-0.3",
                "Market regime": "Shifted from value to growth",
                "Signal type": "Value-oriented"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Distinguish by: (1) Statistical significance - is -0.3 Sharpe within confidence interval of 1.2 Sharpe with 2 years data? (2) Regime explanation - does the underperformance coincide with known regime shift? (3) Crowding - did the signal become too popular? (4) Structural change - has the market mechanism changed? 2 years is likely noise; need 5+ years to confirm failure.",
        answer_options=[
            AnswerOption(id="A", text="Two years of underperformance proves the signal failed", is_correct=False),
            AnswerOption(id="B", text="Distinguish by: (1) Statistical significance - is -0.3 Sharpe within confidence interval of 1.2 Sharpe with 2 years data? (2) Regime explanation - does the underperformance coincide with known regime shift? (3) Crowding - did the signal become too popular? (4) Structural change - has the market mechanism changed? 2 years is likely noise; need 5+ years to confirm failure.", is_correct=True),
            AnswerOption(id="C", text="Always abandon signals after 2 years of losses", is_correct=False),
            AnswerOption(id="D", text="Signal performance is completely random", is_correct=False),
        ],
        explanation="Sharpe ratio SE ≈ 1/√T. With Sharpe 1.2 and 2 years: SE ≈ 0.7. The -0.3 Sharpe is 2.1 SEs below 1.2, borderline significant. But: (1) Value-growth regime shift explains underperformance without signal failure, (2) 2 years is short for a 10-year strategy, (3) Crowding could temporarily compress returns. Evidence for structural failure: mechanism changed (e.g., information now faster), signal correlation with others increased, or returns negative across all regimes.",
        reasoning_steps=[
            "Calculate statistical significance of underperformance",
            "2 years vs 10 years: high uncertainty in recent estimate",
            "Look for regime-based explanation (value/growth shift)",
            "Assess crowding: did too many discover the signal?",
            "Look for mechanism change: why did it work, does that still apply?"
        ],
        tags=["signal-decay", "regime-shift", "statistical-significance", "quant-concepts"],
    ))

    # 28. Volatility Targeting Pitfalls
    problems.append(Problem(
        id="qc_attr_004",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""Risk targeting increases leverage after calm periods.

Why is this pro-cyclical?""",
        context=FinancialContext(
            company_name="Vol Targeting Analysis",
            ticker="N/A",
            sector="Risk Management",
            model_assumptions={
                "Vol target": "15%",
                "Realized vol (calm period)": "8%",
                "Leverage applied": "1.88x (15%/8%)",
                "Subsequent vol spike": "30%",
                "Realized vol at max leverage": "56% (1.88 * 30%)"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Vol targeting: leverage = target_vol / realized_vol. Low realized vol → high leverage → maximum exposure just before vol spikes. This is pro-cyclical: increasing risk when risk is about to rise, forced deleveraging when vol spikes. The strategy buys high (levered at low vol) and sells low (delever at high vol).",
        answer_options=[
            AnswerOption(id="A", text="Vol targeting always improves risk-adjusted returns", is_correct=False),
            AnswerOption(id="B", text="Vol targeting: leverage = target_vol / realized_vol. Low realized vol → high leverage → maximum exposure just before vol spikes. This is pro-cyclical: increasing risk when risk is about to rise, forced deleveraging when vol spikes. The strategy buys high (levered at low vol) and sells low (delever at high vol).", is_correct=True),
            AnswerOption(id="C", text="Leverage decisions should ignore realized volatility", is_correct=False),
            AnswerOption(id="D", text="Vol spikes are unpredictable so this is unavoidable", is_correct=False),
        ],
        explanation="Realized vol is backward-looking and mean-reverting. Low vol periods often precede spikes. At 8% vol with 15% target: leverage = 1.88x. When vol spikes to 30%: portfolio vol = 56%, forced to sell at distressed prices to delever. The strategy is maximum long when markets are calm and fragile, then forced to sell during crashes. Solutions: use vol forecasts (not realized), cap leverage, or maintain buffer.",
        reasoning_steps=[
            "Vol targeting adjusts leverage inversely to realized vol",
            "Low realized vol often precedes vol spikes (mean reversion)",
            "Maximum leverage coincides with maximum fragility",
            "Vol spike forces deleveraging at worst prices",
            "Pro-cyclical: buy high exposure, sell low"
        ],
        tags=["vol-targeting", "pro-cyclicality", "leverage", "quant-concepts"],
    ))

    # 29. Backtest Overconfidence
    problems.append(Problem(
        id="qc_attr_005",
        category=ProblemCategory.DCF_SANITY,
        difficulty=Difficulty.HARD,
        question="""A strategy performs well historically but fails live.

Identify three non-obvious causes.""",
        context=FinancialContext(
            company_name="Backtest Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Backtest Sharpe": "2.5",
                "Live Sharpe": "0.2",
                "Data source": "Point-in-time database",
                "Transaction costs": "Included",
                "Look-ahead bias": "Checked"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Non-obvious causes: (1) Survivorship in universe - backtest only includes stocks that existed throughout, missing failures, (2) Crowding - strategy discovery led others to trade it, compressing returns, (3) Regime specificity - strategy fit a past regime (e.g., declining rates) that no longer holds. Standard checks (look-ahead, costs) miss these.",
        answer_options=[
            AnswerOption(id="A", text="The live period was just unlucky - keep trading", is_correct=False),
            AnswerOption(id="B", text="Non-obvious causes: (1) Survivorship in universe - backtest only includes stocks that existed throughout, missing failures, (2) Crowding - strategy discovery led others to trade it, compressing returns, (3) Regime specificity - strategy fit a past regime (e.g., declining rates) that no longer holds. Standard checks (look-ahead, costs) miss these.", is_correct=True),
            AnswerOption(id="C", text="All backtests accurately predict live performance", is_correct=False),
            AnswerOption(id="D", text="Adding more historical data will fix the issue", is_correct=False),
        ],
        explanation="Beyond standard biases: (1) Universe survivorship: backtest universe may exclude delisted stocks, biasing toward survivors, (2) Crowding: if the strategy was 'discovered' by others, returns compress as more capital chases same opportunities, (3) Regime dependence: strategies can fit specific regimes (bull markets, low rates, low vol) without generalizing. These are harder to detect than look-ahead or transaction cost biases.",
        reasoning_steps=[
            "Standard checks: look-ahead bias, transaction costs, data quality",
            "Survivorship: universe construction may exclude failures",
            "Crowding: strategy publication/discovery attracts competition",
            "Regime fit: strategy may only work in specific market conditions",
            "These biases are harder to detect and more damaging"
        ],
        tags=["backtesting", "overfitting", "crowding", "quant-concepts"],
    ))

    # 30. Learning from PnL
    problems.append(Problem(
        id="qc_attr_006",
        category=ProblemCategory.FINANCIAL_STATEMENT,
        difficulty=Difficulty.EXPERT,
        question="""A losing period coincides with correct forecasts.

Why is outcome-based evaluation misleading?""",
        context=FinancialContext(
            company_name="Process Evaluation Analysis",
            ticker="N/A",
            sector="Portfolio Management",
            model_assumptions={
                "Return forecasts": "Directionally correct 65% of time",
                "Period PnL": "-8%",
                "Factor exposure": "Long growth, short value",
                "Growth vs Value": "-15% during period"
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Outcome = skill + luck + factor exposure. The -8% loss came from -15% growth/value underperformance, not forecast error. 65% directional accuracy is good. Outcome-based evaluation conflates uncontrollable factors with skill. Process evaluation: were forecasts reasonable? Was risk appropriate? Was execution good? Outcomes are noisy; process is signal.",
        answer_options=[
            AnswerOption(id="A", text="Negative PnL always means the forecasts were wrong", is_correct=False),
            AnswerOption(id="B", text="Outcome = skill + luck + factor exposure. The -8% loss came from -15% growth/value underperformance, not forecast error. 65% directional accuracy is good. Outcome-based evaluation conflates uncontrollable factors with skill. Process evaluation: were forecasts reasonable? Was risk appropriate? Was execution good? Outcomes are noisy; process is signal.", is_correct=True),
            AnswerOption(id="C", text="Outcomes are the only valid measure of skill", is_correct=False),
            AnswerOption(id="D", text="Factor exposures should never cause losses", is_correct=False),
        ],
        explanation="Decompose: Stock selection alpha (65% correct) + Factor return (growth/value -15%) + Noise = Total return (-8%). The 65% hit rate suggests positive selection skill, but factor exposure dominated. Outcome-based evaluation would penalize the manager for uncontrollable factor performance. Process evaluation asks: was the growth/value tilt intentional? Was it sized appropriately? Were forecasts well-calibrated?",
        reasoning_steps=[
            "Total return = selection alpha + factor returns + noise",
            "Selection alpha was positive (65% directional accuracy)",
            "Factor exposure (growth/value) drove the loss",
            "Outcome conflates skill with uncontrollable factors",
            "Process evaluation separates controllable from uncontrollable"
        ],
        tags=["process-evaluation", "outcome-bias", "attribution", "quant-concepts"],
    ))

    return problems


if __name__ == "__main__":
    # Generate and print summary
    problems = generate_quant_concept_problems()
    print(f"Generated {len(problems)} concept-driven quant problems")

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
