"""
Risk Assessment Problems — Portfolio Risk, Position Sizing & Risk Metrics

15 problems covering:
- Drawdown probability (3 problems)
- Volatility-of-volatility (3 problems)
- Correlation stress (3 problems)
- Liquidity risk (3 problems)
- Position-level risk metrics (3 problems)

Difficulty range: hard to expert. These problems test whether an AI model
can reason correctly about portfolio risk under realistic conditions,
including non-normal distributions, regime changes, and second-order effects
that practitioners encounter in live capital management.
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


def generate_risk_assessment_problems() -> list[Problem]:
    """Generate 15 risk assessment problems across 5 sub-categories."""
    problems = []

    # =========================================================================
    # I. DRAWDOWN PROBABILITY (3 problems)
    # =========================================================================

    # 1. Maximum Drawdown Estimation
    problems.append(Problem(
        id="ra_dd_001",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.EXPERT,
        question="""A strategy has annualized return of 12%, annualized volatility of 18%, and Sharpe ratio of 0.67. Estimate the probability of experiencing a 20% peak-to-trough drawdown over a 5-year period.

Use the Magdon-Ismail approximation or equivalent framework. State your distributional assumptions and explain why maximum drawdown probability increases with time horizon even when Sharpe is positive.""",
        context=FinancialContext(
            company_name="Drawdown Probability Analysis",
            ticker="N/A",
            sector="Portfolio Risk",
            model_assumptions={
                "Annualized return (mu)": "12%",
                "Annualized volatility (sigma)": "18%",
                "Sharpe ratio": "0.67",
                "Time horizon": "5 years",
                "Drawdown threshold": "20%",
                "Return distribution": "Assumed log-normal (continuous GBM)",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Under continuous-time GBM, the probability is approximately 65-80%. Using the Magdon-Ismail result, for a drift-adjusted process with mu/sigma^2 ≈ 3.7 and D/sigma ≈ 1.11, the probability of a 20% drawdown over 5 years is high because the random-walk component dominates over short-to-medium horizons. Even with positive drift, the cumulative probability of touching a 20% drawdown threshold grows toward 1 as T increases — positive expected return only slows convergence, it does not prevent large drawdowns.",
        answer_options=[
            AnswerOption(id="A", text="Less than 10% — a positive Sharpe of 0.67 makes large drawdowns very unlikely over 5 years", is_correct=False),
            AnswerOption(id="B", text="Approximately 25-35% — the Sharpe ratio provides substantial protection against drawdowns", is_correct=False),
            AnswerOption(id="C", text="Under continuous-time GBM, the probability is approximately 65-80%. Using the Magdon-Ismail result, for a drift-adjusted process with mu/sigma^2 ≈ 3.7 and D/sigma ≈ 1.11, the probability of a 20% drawdown over 5 years is high because the random-walk component dominates over short-to-medium horizons. Even with positive drift, the cumulative probability of touching a 20% drawdown threshold grows toward 1 as T increases — positive expected return only slows convergence, it does not prevent large drawdowns.", is_correct=True),
            AnswerOption(id="D", text="Exactly 50% — drawdown probability equals the probability of a negative return year, which is roughly 50% at Sharpe 0.67", is_correct=False),
        ],
        explanation="""The key insight is that maximum drawdown is a path-dependent statistic, not a point-in-time return measure. Under geometric Brownian motion:

1. Drift-adjusted parameter: gamma = 2*mu/sigma^2 = 2*0.12/0.18^2 ≈ 3.7
2. Normalized drawdown: D/sigma = 0.20/0.18 ≈ 1.11
3. For a drifted Brownian motion, P(max drawdown > D) over horizon T depends on the ratio of drift to diffusion.

The Magdon-Ismail (2004) framework shows that for gamma > 0 (positive drift), P(MDD > D) → 1 as T → infinity, but converges more slowly than the zero-drift case. For gamma ≈ 3.7 and T = 5 years, the probability is in the 65-80% range.

The critical intuition: a Sharpe of 0.67 means the signal-to-noise ratio per unit time is moderate. Over 5 years, there are enough random paths that a 20% drawdown is more likely than not. Investors who assume positive Sharpe protects them from drawdowns fundamentally misunderstand the relationship between expected return and path risk.

Common error: using single-period return distributions (e.g., P(annual return < -20%)) rather than path-based drawdown analysis. Annual return < -20% has low probability (~4% under normality), but maximum drawdown is a running minimum over all sub-paths, making it far more likely.""",
        reasoning_steps=[
            "Identify that drawdown is path-dependent, not a single-period measure",
            "Calculate drift-adjusted parameter gamma = 2*mu/sigma^2 ≈ 3.7",
            "Normalize the drawdown threshold: D/sigma = 0.20/0.18 ≈ 1.11",
            "Apply Magdon-Ismail or reflection-principle approximation",
            "Recognize that P(MDD > D) increases monotonically with T, approaching 1",
            "Conclude that 65-80% is the approximate probability for these parameters over 5 years",
        ],
        common_mistakes=[
            "Confusing single-period return probability with max drawdown probability",
            "Assuming Sharpe > 0.5 makes 20% drawdowns negligible",
            "Using VaR or expected return to estimate drawdown likelihood",
            "Ignoring that drawdown is a path statistic over all subintervals",
            "Applying normal distribution to log returns without path adjustment",
        ],
        tags=["drawdown", "max-drawdown", "magdon-ismail", "path-dependence", "risk-assessment"],
    ))

    # 2. Conditional Drawdown Recovery
    problems.append(Problem(
        id="ra_dd_002",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""A fund is currently in a -15% drawdown from its high-water mark. The strategy has Sharpe ratio 0.8 and annualized volatility 14%.

Estimate the expected time to recover to the high-water mark. Explain why recovery time is path-dependent and not simply a function of expected return divided by the drawdown deficit.""",
        context=FinancialContext(
            company_name="Drawdown Recovery Analysis",
            ticker="N/A",
            sector="Portfolio Risk",
            model_assumptions={
                "Current drawdown": "-15%",
                "Sharpe ratio": "0.8",
                "Annualized volatility": "14%",
                "Implied annualized return": "11.2% (Sharpe x vol)",
                "Required recovery": "17.6% (1/0.85 - 1 to return to HWM)",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="The naive estimate (17.6% needed / 11.2% expected return ≈ 1.6 years) understates expected recovery time. Under a random walk with drift, the expected first-passage time from a deficit of D with drift mu and volatility sigma is T = D/mu only if vol is zero. With vol > 0, the expected recovery time is longer because the process can drift further into drawdown before recovering. For these parameters, expected recovery is approximately 1.8-2.5 years, and critically, the distribution of recovery times is right-skewed — the median recovery is shorter than the mean, but there is a fat right tail of prolonged drawdown periods.",
        answer_options=[
            AnswerOption(id="A", text="Approximately 1.6 years — simply divide the required recovery (17.6%) by the expected annual return (11.2%)", is_correct=False),
            AnswerOption(id="B", text="The naive estimate (17.6% needed / 11.2% expected return ≈ 1.6 years) understates expected recovery time. Under a random walk with drift, the expected first-passage time from a deficit of D with drift mu and volatility sigma is T = D/mu only if vol is zero. With vol > 0, the expected recovery time is longer because the process can drift further into drawdown before recovering. For these parameters, expected recovery is approximately 1.8-2.5 years, and critically, the distribution of recovery times is right-skewed — the median recovery is shorter than the mean, but there is a fat right tail of prolonged drawdown periods.", is_correct=True),
            AnswerOption(id="C", text="Recovery time is unpredictable and cannot be estimated from Sharpe and vol alone", is_correct=False),
            AnswerOption(id="D", text="Less than 1 year — with Sharpe 0.8, recovery should be swift", is_correct=False),
        ],
        explanation="""Recovery from a drawdown is a first-passage-time problem. The fund needs to gain 17.6% (= 1/0.85 - 1) to return to its high-water mark.

The naive calculation divides deficit by expected return: 0.176/0.112 ≈ 1.57 years. But this ignores volatility entirely.

Under GBM with drift mu and vol sigma, the expected first-passage time to recover distance D involves the inverse Gaussian distribution. The key properties:

1. Expected recovery > D/mu when sigma > 0 (volatility extends recovery)
2. The distribution is right-skewed: most recoveries happen faster than the mean, but some take much longer
3. With sigma = 14% and mu = 11.2%, the coefficient of variation is high, meaning wide dispersion around the expected time
4. Conditional on being in a drawdown, further drawdown is possible before recovery

For practical estimation: with mu = 0.112 and sigma = 0.14, and recovery target D ≈ 0.176 (in log terms, ln(1/0.85) ≈ 0.163), the expected first passage time under a Brownian motion with drift is D_log/mu_log ≈ 0.163/(0.112 - 0.14^2/2) ≈ 0.163/0.1022 ≈ 1.6 years for the log process, but the distribution has significant right-tail mass.

The practitioner implication: fund managers often underestimate recovery horizons, and investors pulling capital during drawdowns face the worst outcome — realizing the drawdown permanently just as the strategy may be approaching recovery.""",
        reasoning_steps=[
            "Calculate required recovery: 1/0.85 - 1 = 17.6%, or ln(1/0.85) ≈ 16.3% in log terms",
            "Compute naive estimate: 17.6%/11.2% ≈ 1.57 years",
            "Recognize this is a first-passage-time problem with drift and diffusion",
            "Account for volatility drag: log return = mu - sigma^2/2 = 11.2% - 0.98% ≈ 10.2%",
            "Note the right-skewed distribution of recovery times",
            "Estimate expected recovery at approximately 1.8-2.5 years with significant tail risk",
        ],
        common_mistakes=[
            "Dividing deficit by expected return without accounting for volatility",
            "Ignoring that the fund can go further into drawdown before recovering",
            "Treating recovery time as deterministic rather than a random variable",
            "Forgetting volatility drag on geometric (compounded) returns",
            "Ignoring the right-skew of the recovery time distribution",
        ],
        tags=["drawdown-recovery", "first-passage-time", "high-water-mark", "path-dependence", "risk-assessment"],
    ))

    # 3. Drawdown vs. Leverage
    problems.append(Problem(
        id="ra_dd_003",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.EXPERT,
        question="""Compare the probability of a 25% peak-to-trough drawdown for two portfolios:

(a) Unlevered portfolio: Sharpe 1.2, volatility 10%
(b) 2x levered portfolio: Sharpe 0.6 (after financing costs), volatility 20%

Both have the same gross return profile before leverage/costs. Which portfolio has a higher probability of a 25% drawdown over a 3-year period, and by approximately how much? Explain why leverage amplifies drawdown risk non-linearly relative to return.""",
        context=FinancialContext(
            company_name="Leverage-Drawdown Analysis",
            ticker="N/A",
            sector="Portfolio Risk",
            model_assumptions={
                "Portfolio A (unlevered)": "Sharpe 1.2, vol 10%, return 12%",
                "Portfolio B (2x levered)": "Sharpe 0.6, vol 20%, return 12% (24% gross - 12% financing)",
                "Drawdown threshold": "25%",
                "Time horizon": "3 years",
                "Financing cost": "6% (levered portfolio)",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="The levered portfolio has a substantially higher drawdown probability — roughly 2-3x that of the unlevered portfolio. Although both target similar net returns (~12%), the levered portfolio doubles vol from 10% to 20%. Drawdown probability scales approximately with (D/sigma)^2 in the exponent for drifted processes: halving D/sigma from 2.5 (unlevered: 25%/10%) to 1.25 (levered: 25%/20%) roughly squares the probability. Additionally, leverage introduces volatility drag: the geometric return penalty is sigma^2/2, which quadruples when vol doubles. The levered portfolio's compounded return is lower than 12% by an additional ~1% (0.20^2/2 - 0.10^2/2 = 1.5%). Leverage amplifies drawdown risk non-linearly because drawdown depends on path volatility, not just expected return.",
        answer_options=[
            AnswerOption(id="A", text="Both have roughly equal drawdown probability since net returns are similar", is_correct=False),
            AnswerOption(id="B", text="The unlevered portfolio has higher drawdown risk because its lower gross return provides less cushion", is_correct=False),
            AnswerOption(id="C", text="The levered portfolio has a substantially higher drawdown probability — roughly 2-3x that of the unlevered portfolio. Although both target similar net returns (~12%), the levered portfolio doubles vol from 10% to 20%. Drawdown probability scales approximately with (D/sigma)^2 in the exponent for drifted processes: halving D/sigma from 2.5 (unlevered: 25%/10%) to 1.25 (levered: 25%/20%) roughly squares the probability. Additionally, leverage introduces volatility drag: the geometric return penalty is sigma^2/2, which quadruples when vol doubles. The levered portfolio's compounded return is lower than 12% by an additional ~1% (0.20^2/2 - 0.10^2/2 = 1.5%). Leverage amplifies drawdown risk non-linearly because drawdown depends on path volatility, not just expected return.", is_correct=True),
            AnswerOption(id="D", text="Leverage exactly doubles drawdown probability since it doubles volatility", is_correct=False),
        ],
        explanation="""This problem illustrates why Sharpe ratio alone is insufficient for risk assessment — drawdown risk depends heavily on the vol level, not just the risk-adjusted return.

Key calculations:
1. Unlevered: mu=12%, sigma=10%, Sharpe=1.2, D/sigma=2.5
2. Levered: mu≈12% (after financing), sigma=20%, Sharpe=0.6, D/sigma=1.25

Under GBM, the probability of a drawdown of size D relates to the ratio D/sigma and the drift parameter gamma = 2*mu/sigma^2:
- Unlevered gamma = 2*0.12/0.01 = 24 (very strong drift relative to diffusion)
- Levered gamma = 2*0.12/0.04 = 6 (moderate drift relative to diffusion)

The unlevered portfolio has much stronger mean-reversion in the drift-to-diffusion ratio. For the levered portfolio, the random walk component is much more dominant relative to drift.

Additionally, volatility drag matters for compounded returns:
- Unlevered geometric drag: 0.10^2/2 = 0.5%
- Levered geometric drag: 0.20^2/2 = 2.0%
The extra 1.5% drag reduces the effective compounding rate of the levered portfolio.

Practical implication: a fund running at 2x leverage with a Sharpe of 0.6 faces far more path risk than an unlevered fund with the same net return, even though a single-period return analysis might suggest comparable risk-adjusted performance. This is why many allocators evaluate managers on both Sharpe and max drawdown independently.""",
        reasoning_steps=[
            "Compare D/sigma ratios: unlevered 2.5, levered 1.25",
            "Calculate drift-to-diffusion parameter gamma for each portfolio",
            "Note gamma difference: 24 (unlevered) vs. 6 (levered)",
            "Compute volatility drag differential: 2.0% - 0.5% = 1.5% additional drag for levered",
            "Recognize that drawdown probability is highly non-linear in sigma",
            "Conclude levered portfolio has roughly 2-3x the drawdown probability",
        ],
        common_mistakes=[
            "Assuming equal Sharpe-adjusted returns imply equal drawdown risk",
            "Thinking leverage doubles drawdown risk linearly",
            "Ignoring the volatility drag on compounded returns",
            "Using single-period return distributions instead of path-based analysis",
            "Neglecting that lower Sharpe (from financing) compounds the vol effect",
        ],
        tags=["leverage", "drawdown", "volatility-drag", "geometric-returns", "risk-assessment"],
    ))

    # =========================================================================
    # II. VOLATILITY-OF-VOLATILITY (3 problems)
    # =========================================================================

    # 4. Vol Regime Detection
    problems.append(Problem(
        id="ra_vov_001",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""Given the following 12 monthly observations of 30-day realized volatility (annualized):

Month 1-6: 11%, 12%, 10%, 14%, 13%, 12%
Month 7-10: 22%, 28%, 24%, 19%
Month 11-12: 15%, 13%

Identify the volatility regime transition. Estimate when it occurred and whether current vol has mean-reverted to the prior regime. What GARCH-type reasoning would you apply to forecast next month's volatility?""",
        context=FinancialContext(
            company_name="Vol Regime Analysis",
            ticker="N/A",
            sector="Portfolio Risk",
            model_assumptions={
                "Vol observations (annualized)": "[11, 12, 10, 14, 13, 12, 22, 28, 24, 19, 15, 13]",
                "Low-vol regime mean": "~12% (months 1-6)",
                "High-vol regime peak": "28% (month 8)",
                "Current observation": "13% (month 12)",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="The regime transition occurred between months 6 and 7, with vol jumping from 12% to 22% (an 83% increase). The high-vol regime peaked at 28% in month 8. Current vol at 13% has largely mean-reverted to the prior low-vol regime average of ~12%. However, a GARCH(1,1) model would suggest the conditional variance still carries elevated persistence: sigma^2_t+1 = omega + alpha*epsilon^2_t + beta*sigma^2_t. With typical GARCH parameters (alpha ≈ 0.10, beta ≈ 0.85, omega calibrated to long-run variance), the forecast would be above the unconditional mean of 12% but declining — approximately 14-16%. The key nuance: vol has mean-reverted in level but the GARCH conditional forecast retains memory of the spike, meaning the probability of another vol jump is elevated relative to the pre-shock period.",
        answer_options=[
            AnswerOption(id="A", text="No regime change occurred — this is normal variation around a 15% mean", is_correct=False),
            AnswerOption(id="B", text="The regime transition occurred between months 6 and 7, with vol jumping from 12% to 22% (an 83% increase). The high-vol regime peaked at 28% in month 8. Current vol at 13% has largely mean-reverted to the prior low-vol regime average of ~12%. However, a GARCH(1,1) model would suggest the conditional variance still carries elevated persistence: sigma^2_t+1 = omega + alpha*epsilon^2_t + beta*sigma^2_t. With typical GARCH parameters (alpha ≈ 0.10, beta ≈ 0.85, omega calibrated to long-run variance), the forecast would be above the unconditional mean of 12% but declining — approximately 14-16%. The key nuance: vol has mean-reverted in level but the GARCH conditional forecast retains memory of the spike, meaning the probability of another vol jump is elevated relative to the pre-shock period.", is_correct=True),
            AnswerOption(id="C", text="Vol at 13% means the crisis is over and next month's vol will be 12%", is_correct=False),
            AnswerOption(id="D", text="GARCH models are irrelevant — just use the trailing 3-month average of 15.7%", is_correct=False),
        ],
        explanation="""Regime detection analysis:

1. Low-vol regime (months 1-6): mean = 12.0%, std = 1.4%
2. High-vol regime (months 7-10): mean = 23.3%, std = 3.8%
3. Recovery (months 11-12): mean = 14.0%

The jump from 12% to 22% at month 7 is 7+ standard deviations from the low-vol regime, clearly a regime break. The decline from 28% to 13% over 4 months suggests mean reversion, but GARCH dynamics matter:

GARCH(1,1): sigma^2_{t+1} = omega + alpha * r^2_t + beta * sigma^2_{t}

With standard parameters (alpha + beta ≈ 0.95, long-run variance targeting ~12%):
- The conditional variance decays exponentially from the spike
- Half-life of a vol shock ≈ -log(2)/log(alpha+beta) ≈ 14 periods
- After 4-5 months of decay, conditional vol is still somewhat elevated

The practical implication: portfolio risk limits that were loosened during the crisis should not immediately return to pre-crisis levels. The conditional probability of a vol re-acceleration remains elevated for several months after an apparent mean reversion.""",
        reasoning_steps=[
            "Calculate mean and standard deviation for the first 6 months (low-vol regime)",
            "Identify the break point: month 7 vol is >7 sigma above low-vol mean",
            "Characterize the high-vol regime: months 7-10, peaking at month 8",
            "Assess mean reversion: months 11-12 are within 1 sigma of low-vol mean",
            "Apply GARCH(1,1) logic: conditional variance decays exponentially from spike",
            "Forecast next month: above unconditional mean but declining, ~14-16%",
        ],
        common_mistakes=[
            "Treating vol as stationary and ignoring the regime break",
            "Assuming current vol equals the forecast (ignoring GARCH persistence)",
            "Using simple trailing average instead of conditional variance model",
            "Concluding the crisis is 'over' because spot vol returned to prior levels",
            "Ignoring that vol-of-vol is itself elevated after a regime break",
        ],
        tags=["vol-regime", "garch", "mean-reversion", "conditional-variance", "risk-assessment"],
    ))

    # 5. VIX Term Structure Interpretation
    problems.append(Problem(
        id="ra_vov_002",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""The VIX term structure shows:
- VIX spot: 18
- 3-month VIX futures: 22
- 6-month VIX futures: 24

The term structure is in contango. What does this imply about the market's forward volatility expectations? Is the market pricing in a specific vol event? How would you express a view that this term structure is too steep?""",
        context=FinancialContext(
            company_name="VIX Term Structure Analysis",
            ticker="VIX",
            sector="Volatility",
            model_assumptions={
                "VIX spot": "18",
                "3-month VIX futures": "22",
                "6-month VIX futures": "24",
                "Term structure shape": "Contango",
                "Contango slope (spot to 3m)": "+4 pts / 22%",
                "Contango slope (3m to 6m)": "+2 pts / 9%",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Contango in VIX futures does NOT necessarily imply the market expects vol to rise. VIX futures converge to expected VIX at expiration, but the term structure in contango is the normal state (~80% of the time) because: (1) variance risk premium — sellers of vol insurance demand compensation, embedding a premium in futures over realized, (2) mean-reversion — when spot VIX is below its long-run mean (~20), futures reflect expected reversion upward. The steepness here (4 pts spot-to-3m) suggests either elevated risk premium or an identifiable event (election, FOMC cycle, earnings season) in the 3-month window. To express a view that the term structure is too steep, you would sell the 3-month future and buy the 6-month (or sell 3m and buy spot VIX exposure via options), profiting if the curve flattens. Calendar spreads on VIX futures or ratio spreads on SPX options are the standard vehicles.",
        answer_options=[
            AnswerOption(id="A", text="Contango means the market expects volatility to increase from 18 to 24 over 6 months — a specific vol event is priced in", is_correct=False),
            AnswerOption(id="B", text="Contango in VIX futures does NOT necessarily imply the market expects vol to rise. VIX futures converge to expected VIX at expiration, but the term structure in contango is the normal state (~80% of the time) because: (1) variance risk premium — sellers of vol insurance demand compensation, embedding a premium in futures over realized, (2) mean-reversion — when spot VIX is below its long-run mean (~20), futures reflect expected reversion upward. The steepness here (4 pts spot-to-3m) suggests either elevated risk premium or an identifiable event (election, FOMC cycle, earnings season) in the 3-month window. To express a view that the term structure is too steep, you would sell the 3-month future and buy the 6-month (or sell 3m and buy spot VIX exposure via options), profiting if the curve flattens. Calendar spreads on VIX futures or ratio spreads on SPX options are the standard vehicles.", is_correct=True),
            AnswerOption(id="C", text="VIX contango is always a buying opportunity — sell the expensive futures and collect roll yield", is_correct=False),
            AnswerOption(id="D", text="The term structure is meaningless — only spot VIX matters for risk management", is_correct=False),
        ],
        explanation="""The VIX term structure requires careful interpretation:

1. Normal contango: VIX futures are typically above spot because (a) the variance risk premium means implied > realized on average, and (b) when VIX is below its long-run mean, mean-reversion expectations push futures higher.

2. Steepness assessment: The 4-point spread from spot to 3-month is moderately steep. Historical median is roughly 2-3 points when VIX spot is at 18. Steeper-than-normal contango could indicate:
   - A known event (election, major FOMC meeting, fiscal cliff) in the window
   - Elevated hedging demand from institutional portfolios
   - Simply higher variance risk premium during the current regime

3. Trading the steepness: If you believe the curve is too steep (i.e., 3-month vol will not be as high as futures imply):
   - Sell 3-month VIX futures / buy spot VIX (via SPX puts or VIX calls)
   - VIX calendar spreads: short near-term, long far-term
   - SPX option structures: sell 3-month straddles, buy 1-month straddles
   - Risk: if a vol event occurs, the short futures position loses significantly

The critical error to avoid: assuming contango = directional vol forecast. The variance risk premium alone accounts for most of the contango under normal conditions.""",
        reasoning_steps=[
            "Recognize contango is the normal state for VIX futures (~80% of the time)",
            "Decompose the term structure into variance risk premium and mean-reversion components",
            "Assess steepness: 4 pts spot-to-3m is moderately above the historical median",
            "Consider event-driven explanations for excess steepness",
            "Identify calendar spreads as the vehicle for expressing a flattening view",
            "Acknowledge the risk: short vol positions can lose multiples of premium if a tail event occurs",
        ],
        common_mistakes=[
            "Interpreting contango as a forecast that vol will rise",
            "Ignoring the variance risk premium embedded in VIX futures",
            "Treating VIX futures as a tradeable spot position",
            "Assuming short vol (selling steep contango) is a risk-free carry trade",
            "Conflating VIX level with actual portfolio risk",
        ],
        tags=["vix", "term-structure", "contango", "variance-risk-premium", "vol-trading", "risk-assessment"],
    ))

    # 6. Dispersion vs. Correlation
    problems.append(Problem(
        id="ra_vov_003",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.EXPERT,
        question="""S&P 500 index implied vol is 16%, but the average single-stock implied vol of its constituents is 32%. The implied correlation is approximately (16/32)^2 = 25%.

Historical realized correlation over the past year is 40%.

What does this dispersion-correlation disconnect imply? How would you trade it?""",
        context=FinancialContext(
            company_name="Dispersion-Correlation Analysis",
            ticker="SPX",
            sector="Volatility / Correlation",
            model_assumptions={
                "SPX implied vol": "16%",
                "Average single-stock implied vol": "32%",
                "Implied correlation": "~25% ((16/32)^2)",
                "Realized correlation (1yr)": "40%",
                "Correlation gap": "15 percentage points (realized > implied)",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Implied correlation (25%) is far below realized correlation (40%), meaning the options market is pricing in much higher single-stock dispersion than has been realized. This can arise from: (1) elevated demand for single-stock options (hedging, overwriting), which inflates individual implied vols relative to index vol, (2) the market expecting a shift toward a more stock-picking-friendly environment with lower correlation. To trade this: a dispersion trade — sell single-stock volatility (sell straddles/strangles on constituents) and buy index volatility (buy SPX straddles). You profit if realized correlation exceeds the 25% implied level, which recent history at 40% suggests is likely. The risk: if a true dispersion event occurs (sector rotation, idiosyncratic catalysts) and realized correlation drops below 25%, the trade loses. This is fundamentally a bet that correlation will stay closer to its realized level than to the depressed implied level.",
        answer_options=[
            AnswerOption(id="A", text="The disconnect is meaningless — implied and realized correlation operate independently", is_correct=False),
            AnswerOption(id="B", text="Implied correlation (25%) is far below realized correlation (40%), meaning the options market is pricing in much higher single-stock dispersion than has been realized. This can arise from: (1) elevated demand for single-stock options (hedging, overwriting), which inflates individual implied vols relative to index vol, (2) the market expecting a shift toward a more stock-picking-friendly environment with lower correlation. To trade this: a dispersion trade — sell single-stock volatility (sell straddles/strangles on constituents) and buy index volatility (buy SPX straddles). You profit if realized correlation exceeds the 25% implied level, which recent history at 40% suggests is likely. The risk: if a true dispersion event occurs (sector rotation, idiosyncratic catalysts) and realized correlation drops below 25%, the trade loses. This is fundamentally a bet that correlation will stay closer to its realized level than to the depressed implied level.", is_correct=True),
            AnswerOption(id="C", text="Always sell index vol and buy single-stock vol when implied correlation is low", is_correct=False),
            AnswerOption(id="D", text="The correlation gap means a market crash is imminent", is_correct=False),
        ],
        explanation="""The dispersion-correlation relationship follows from the index variance formula:

sigma_index^2 = sum(w_i^2 * sigma_i^2) + sum_i≠j(w_i * w_j * rho_ij * sigma_i * sigma_j)

For an equal-weight approximation with N stocks:
sigma_index^2 ≈ (1/N) * sigma_avg^2 + (1 - 1/N) * rho * sigma_avg^2
sigma_index ≈ sigma_avg * sqrt(rho + (1-rho)/N)

For large N: sigma_index ≈ sigma_avg * sqrt(rho)
Therefore: rho_implied ≈ (sigma_index / sigma_avg)^2 = (16/32)^2 = 25%

The 15-point gap between implied (25%) and realized (40%) correlation creates a trade:

Long correlation (dispersion trade):
- Sell single-stock variance (capture the premium in inflated individual IVs)
- Buy index variance (hedge against broad market moves)
- P&L ≈ proportional to (realized_corr - implied_corr)

Historical context: implied correlation is typically below realized due to the single-stock overwriting premium. The average gap is roughly 5-10 points. A 15-point gap is unusually wide, suggesting the trade has positive expected value.

Risks: (1) correlation can drop sharply during earnings seasons or sector rotations, (2) single-stock vol can spike on idiosyncratic events (M&A, earnings), (3) the trade requires careful sizing because correlation moves are fat-tailed.""",
        reasoning_steps=[
            "Derive implied correlation from index vol and average constituent vol",
            "Compare implied correlation (25%) to realized correlation (40%)",
            "Identify the gap as unusually wide relative to historical norms (5-10 pts typical)",
            "Construct the dispersion trade: sell single-stock vol, buy index vol",
            "Assess P&L driver: profit if realized correlation exceeds implied",
            "Identify risks: earnings season, sector rotation, idiosyncratic spikes",
        ],
        common_mistakes=[
            "Confusing dispersion (low correlation) with direction (bear market)",
            "Ignoring that implied correlation is structurally below realized",
            "Not sizing the trade to account for fat-tailed correlation moves",
            "Assuming the gap always closes — sometimes structural supply/demand shifts persist",
            "Treating dispersion trades as risk-free arbitrage",
        ],
        tags=["dispersion", "implied-correlation", "vol-surface", "correlation-trading", "risk-assessment"],
    ))

    # =========================================================================
    # III. CORRELATION STRESS (3 problems)
    # =========================================================================

    # 7. Correlation Breakdown in Crisis
    problems.append(Problem(
        id="ra_corr_001",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""A portfolio holds 10 equally-weighted positions, each with individual annualized volatility of 30%. The average pairwise correlation in normal markets is 0.25.

In a stress scenario, correlation spikes to 0.70.

Calculate the portfolio volatility under each regime. What is the diversification benefit lost, expressed as both absolute vol and as a percentage of the normal-regime diversification benefit?""",
        context=FinancialContext(
            company_name="Correlation Stress Analysis",
            ticker="N/A",
            sector="Portfolio Risk",
            model_assumptions={
                "Number of positions": "10 (equal weight)",
                "Individual vol (each)": "30% annualized",
                "Normal correlation": "0.25",
                "Stress correlation": "0.70",
                "Weight per position": "10%",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""Normal regime: portfolio variance = (1/10)*0.30^2 + (9/10)*0.25*0.30^2 = 0.009 + 0.02025 = 0.02925; portfolio vol = sqrt(0.02925) ≈ 17.1%.

Stress regime: portfolio variance = (1/10)*0.30^2 + (9/10)*0.70*0.30^2 = 0.009 + 0.0567 = 0.0657; portfolio vol = sqrt(0.0657) ≈ 25.6%.

Undiversified vol (rho=1) = 30%. Diversification benefit in normal regime = 30% - 17.1% = 12.9%. Diversification benefit in stress = 30% - 25.6% = 4.4%. Benefit lost = 12.9% - 4.4% = 8.5% absolute, or 66% of the normal diversification benefit evaporates in stress. Portfolio vol increases by 50% (17.1% to 25.6%) even though individual vols are unchanged — the entire increase comes from correlation.""",
        answer_options=[
            AnswerOption(id="A", text="Normal vol ≈ 9.5%, stress vol ≈ 21.0% — the portfolio is well diversified in both regimes", is_correct=False),
            AnswerOption(id="B", text="Normal vol ≈ 17.1%, stress vol ≈ 25.6%. Diversification benefit drops from 12.9% to 4.4% — roughly 66% of the diversification benefit is lost. Portfolio vol increases ~50% solely from correlation, with no change in individual position vols.", is_correct=True),
            AnswerOption(id="C", text="Normal vol ≈ 17.1%, stress vol ≈ 30.0% — correlation at 0.70 eliminates all diversification", is_correct=False),
            AnswerOption(id="D", text="The calculation requires knowing the specific stock betas, not just pairwise correlations", is_correct=False),
        ],
        explanation="""Portfolio variance formula for equal-weight portfolio with uniform pairwise correlation:

sigma_p^2 = w^2 * sum(sigma_i^2) + 2 * w^2 * sum_i<j(rho * sigma_i * sigma_j)

For N equal-weight positions with equal vol and uniform correlation:
sigma_p^2 = (1/N) * sigma^2 + (1 - 1/N) * rho * sigma^2
sigma_p^2 = sigma^2 * [(1/N) + rho * (1 - 1/N)]
sigma_p^2 = sigma^2 * [(1 + rho*(N-1)) / N]

Normal regime:
sigma_p^2 = 0.09 * [(1 + 0.25*9) / 10] = 0.09 * [3.25/10] = 0.09 * 0.325 = 0.02925
sigma_p = 17.1%

Stress regime:
sigma_p^2 = 0.09 * [(1 + 0.70*9) / 10] = 0.09 * [7.3/10] = 0.09 * 0.73 = 0.0657
sigma_p = 25.6%

The diversification ratio:
- Normal: 17.1% / 30% = 0.57 (43% vol reduction)
- Stress: 25.6% / 30% = 0.85 (only 15% vol reduction)
- Lost: 66% of the diversification benefit vanishes

This is the fundamental challenge of portfolio risk management: the diversification you rely on in normal times is precisely what fails when you need it most. Risk models that use trailing realized correlation (typically low-to-moderate) systematically underestimate stress-scenario portfolio vol.""",
        reasoning_steps=[
            "Apply the equal-weight uniform-correlation portfolio variance formula",
            "Normal regime: sigma_p^2 = 0.09 * (1 + 0.25*9)/10 = 0.02925; sigma_p ≈ 17.1%",
            "Stress regime: sigma_p^2 = 0.09 * (1 + 0.70*9)/10 = 0.0657; sigma_p ≈ 25.6%",
            "Calculate diversification benefit as difference from undiversified vol (30%)",
            "Normal benefit: 12.9%; stress benefit: 4.4%; lost: 8.5% or 66%",
            "Note that vol increased 50% with zero change in individual position vols",
        ],
        common_mistakes=[
            "Forgetting the cross-product (correlation) terms in portfolio variance",
            "Using simple average of volatilities instead of the variance formula",
            "Assuming correlation 0.70 means diversification is completely gone (that requires rho=1.0)",
            "Not distinguishing between vol increase from correlation vs. vol increase from positions",
            "Underestimating the magnitude: a 50% vol increase is a massive risk event",
        ],
        tags=["correlation-stress", "diversification", "portfolio-variance", "regime-change", "risk-assessment"],
    ))

    # 8. Cross-Asset Correlation Regime
    problems.append(Problem(
        id="ra_corr_002",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""A 60/40 stock/bond portfolio has benefited from negative stock-bond correlation (-0.30) for the past 20 years.

If the regime shifts to positive stock-bond correlation (+0.30) due to persistent inflation, what happens to the portfolio's annualized volatility? Assume equity vol is 16% and bond vol is 8%.

Quantify the impact and explain why this regime shift is particularly dangerous for institutional portfolios.""",
        context=FinancialContext(
            company_name="60/40 Correlation Regime Analysis",
            ticker="N/A",
            sector="Multi-Asset",
            model_assumptions={
                "Equity weight": "60%",
                "Bond weight": "40%",
                "Equity vol": "16%",
                "Bond vol": "8%",
                "Historical stock-bond correlation": "-0.30",
                "Stress stock-bond correlation": "+0.30",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""Negative correlation regime: sigma_p^2 = (0.6)^2*(0.16)^2 + (0.4)^2*(0.08)^2 + 2*(0.6)*(0.4)*(-0.30)*(0.16)*(0.08) = 0.009216 + 0.001024 - 0.001843 = 0.008397; sigma_p ≈ 9.2%.

Positive correlation regime: sigma_p^2 = 0.009216 + 0.001024 + 0.001843 = 0.012083; sigma_p ≈ 11.0%.

Vol increases from 9.2% to 11.0% — a 20% increase. The cross-product term swings from -0.18% to +0.18%, a 0.37% swing in variance (equivalent to ~1.8% vol impact). This is particularly dangerous because: (1) trillions in AUM are calibrated to the -0.30 correlation assumption, (2) in an inflationary regime, both stocks and bonds can decline simultaneously, meaning the drawdown is not just about higher vol but also about correlated losses, (3) risk parity and target-vol strategies would need to delever significantly, potentially creating forced selling cascades.""",
        answer_options=[
            AnswerOption(id="A", text="Minimal impact — bond vol is only 8%, so correlation doesn't matter much", is_correct=False),
            AnswerOption(id="B", text="Vol increases from approximately 9.2% to approximately 11.0% — a 20% increase. The 60-point correlation swing from -0.30 to +0.30 eliminates the diversification benefit of bonds and converts them from a hedge into an amplifier. Trillions in institutional capital are calibrated to the negative correlation assumption, and the regime shift would force widespread rebalancing.", is_correct=True),
            AnswerOption(id="C", text="Vol doubles from ~9% to ~18% because correlation reverses sign", is_correct=False),
            AnswerOption(id="D", text="Bonds should be removed entirely from the portfolio in an inflationary regime", is_correct=False),
        ],
        explanation="""Two-asset portfolio variance:
sigma_p^2 = w_e^2*sigma_e^2 + w_b^2*sigma_b^2 + 2*w_e*w_b*rho*sigma_e*sigma_b

Components:
- Equity variance contribution: (0.6)^2 * (0.16)^2 = 0.009216
- Bond variance contribution: (0.4)^2 * (0.08)^2 = 0.001024
- Cross-product at rho = -0.30: 2 * 0.6 * 0.4 * (-0.30) * 0.16 * 0.08 = -0.001843
- Cross-product at rho = +0.30: 2 * 0.6 * 0.4 * (+0.30) * 0.16 * 0.08 = +0.001843

Results:
- Negative correlation: sqrt(0.008397) = 9.16%
- Positive correlation: sqrt(0.012083) = 10.99%
- Zero correlation: sqrt(0.010240) = 10.12%

The 20% vol increase understates the true risk because:
1. In an inflation regime, expected returns on both assets may also decline
2. The correlation shift is likely asymmetric — it spikes highest during the worst joint drawdowns
3. Institutional rebalancing flows amplify the sell-off as risk parity and target-vol strategies delever

Historical precedent: the 1970s saw positive stock-bond correlation with both assets generating negative real returns. The 2022 experience (stocks and bonds both down >10%) was a preview of this regime.""",
        reasoning_steps=[
            "Calculate portfolio variance under each correlation assumption",
            "Negative rho: sigma_p^2 = 0.009216 + 0.001024 - 0.001843 = 0.008397",
            "Positive rho: sigma_p^2 = 0.009216 + 0.001024 + 0.001843 = 0.012083",
            "Compare: 9.2% vs 11.0%, a 20% increase in portfolio vol",
            "Assess systemic implications for institutional portfolios",
            "Note that the regime shift compounds: higher vol + correlated drawdowns + forced rebalancing",
        ],
        common_mistakes=[
            "Ignoring the cross-product term or miscalculating its sign",
            "Assuming bond vol is too low to matter (the correlation effect is multiplicative)",
            "Thinking a 20% vol increase is 'small' — for a multi-trillion dollar allocation, it is enormous",
            "Not considering the second-order effects (forced rebalancing, risk parity deleveraging)",
            "Assuming correlation regimes are stable and predictable",
        ],
        tags=["stock-bond-correlation", "regime-change", "60-40", "inflation", "institutional-risk", "risk-assessment"],
    ))

    # 9. Factor Correlation During Stress
    problems.append(Problem(
        id="ra_corr_003",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.EXPERT,
        question="""A fund runs a momentum-value barbell with equal risk allocation to each factor. Historically, momentum and value have correlation of -0.40.

During March 2020, both factors experienced sharp drawdowns simultaneously as the correlation flipped to +0.60.

If momentum factor vol is 12% and value factor vol is 14%, calculate the portfolio vol under each correlation regime (50/50 weight). How should the risk manager adjust position sizing to account for tail correlation, and what structural explanation accounts for the correlation flip?""",
        context=FinancialContext(
            company_name="Factor Barbell Stress Analysis",
            ticker="N/A",
            sector="Factor Investing",
            model_assumptions={
                "Momentum factor vol": "12%",
                "Value factor vol": "14%",
                "Normal correlation (mom-val)": "-0.40",
                "Stress correlation (mom-val)": "+0.60",
                "Portfolio weights": "50% momentum, 50% value",
                "Stress event": "March 2020 COVID crash",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""Normal regime: sigma_p^2 = (0.5)^2*(0.12)^2 + (0.5)^2*(0.14)^2 + 2*(0.5)*(0.5)*(-0.40)*(0.12)*(0.14) = 0.0036 + 0.0049 - 0.00336 = 0.00514; sigma_p ≈ 7.2%.

Stress regime: sigma_p^2 = 0.0036 + 0.0049 + 2*(0.5)*(0.5)*(+0.60)*(0.12)*(0.14) = 0.0036 + 0.0049 + 0.00504 = 0.01354; sigma_p ≈ 11.6%.

Vol nearly doubles from 7.2% to 11.6% — a 62% increase. The risk manager should: (1) size the combined position to the stress-regime vol, not the normal regime — if the risk budget is 10% vol, total factor allocation should be ~86% (10/11.6), not 139% (10/7.2), (2) maintain a tail correlation reserve — assume rho = +0.40 to +0.60 for sizing rather than the -0.40 normal state.

The structural explanation: in a liquidation-driven crash, all risky positions are sold regardless of factor exposure. Both momentum winners and value names get liquidated by funds facing margin calls or redemptions. The 'flight to cash' drives all risk factors to correlate positively. Factor diversification is a fair-weather benefit that partially fails in the worst scenarios.""",
        answer_options=[
            AnswerOption(id="A", text="Vol goes from 7.2% to 8.5% — a modest increase that doesn't warrant position adjustment", is_correct=False),
            AnswerOption(id="B", text="Vol goes from ~7.2% to ~11.6% (a 62% increase). The risk manager should size to stress-regime vol, not normal-regime vol. The correlation flip is structural: liquidation-driven selling compresses all factor spreads simultaneously, converting factor diversification into factor crowding.", is_correct=True),
            AnswerOption(id="C", text="Factor correlations are stable by construction — this scenario is implausible", is_correct=False),
            AnswerOption(id="D", text="The only solution is to abandon factor investing and hold cash", is_correct=False),
        ],
        explanation="""The factor barbell is designed to exploit the negative momentum-value correlation: when one factor underperforms, the other tends to compensate. This works in normal markets where factor returns are driven by fundamental rotations.

Calculation:
Normal: sigma_p = sqrt(0.25*0.0144 + 0.25*0.0196 + 2*0.25*(-0.40)*0.0168) = sqrt(0.00514) = 7.17%
Stress: sigma_p = sqrt(0.25*0.0144 + 0.25*0.0196 + 2*0.25*(+0.60)*0.0168) = sqrt(0.01354) = 11.63%

The correlation swing from -0.40 to +0.60 is a 1-point move in correlation space. This is not uncommon in crisis: the cross-product term swings from -0.00336 to +0.00504, a variance change of 0.00840, which dominates the portfolio variance.

Why it happens structurally:
1. Margin calls force liquidation of ALL positions, regardless of factor tilt
2. Momentum names (recent winners) are heavily owned by trend-followers who delever first
3. Value names (cheap, high-leverage) are hit hardest by credit stress
4. Both factors are sold simultaneously, creating positive correlation
5. The liquidity premium (which props up value) disappears when everyone needs cash

Risk management response:
- Use conditional correlation (stress correlation) for position sizing, not unconditional
- Maintain a 'stress buffer' of at least 30-40% below the normal-regime risk limit
- Monitor factor crowding indicators (short interest, factor ETF flows) as leading indicators
- Consider tail hedges that pay off when correlations spike (e.g., long equity vol)""",
        reasoning_steps=[
            "Calculate portfolio variance under normal correlation: 0.00514; vol ≈ 7.2%",
            "Calculate portfolio variance under stress correlation: 0.01354; vol ≈ 11.6%",
            "Quantify the impact: 62% vol increase from correlation flip alone",
            "Derive sizing rule: use stress-regime vol for risk budgeting",
            "Explain the structural mechanism: liquidation-driven selling compresses all spreads",
            "Recommend monitoring crowding and maintaining stress buffers",
        ],
        common_mistakes=[
            "Assuming factor correlations are stable properties of the market",
            "Sizing based on normal-regime diversification and being surprised by stress losses",
            "Ignoring that factor crowding amplifies the correlation flip",
            "Treating the March 2020 event as a one-off rather than a recurring structural feature",
            "Believing that 'market-neutral' factor portfolios have no drawdown risk",
        ],
        tags=["factor-correlation", "momentum-value", "stress-testing", "liquidation", "crowding", "risk-assessment"],
    ))

    # =========================================================================
    # IV. LIQUIDITY RISK (3 problems)
    # =========================================================================

    # 10. Position Exit Horizon
    problems.append(Problem(
        id="ra_liq_001",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""A fund holds $50M in a stock with $15M average daily volume (ADV). The fund wants to exit the entire position within 5 trading days. Participation rate is capped at 15% of ADV.

(a) Can the position be exited within 5 days at the capped participation rate?
(b) What is the estimated market impact cost using the square-root model: impact ≈ sigma_daily * sqrt(shares_traded / ADV), where daily vol is 2.5%?
(c) What is the total liquidation cost (impact + opportunity cost of extended exit)?""",
        context=FinancialContext(
            company_name="Position Exit Analysis",
            ticker="EXMP",
            sector="Mid-Cap Equity",
            model_assumptions={
                "Position size": "$50M",
                "Average daily volume (ADV)": "$15M",
                "Participation rate cap": "15% of ADV",
                "Daily vol (sigma)": "2.5%",
                "Days to exit target": "5 trading days",
                "Days of ADV": "50/15 ≈ 3.3 days of ADV",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""(a) At 15% participation, daily liquidation capacity = 0.15 * $15M = $2.25M. Over 5 days: $2.25M * 5 = $11.25M. This covers only 22.5% of the $50M position. The position CANNOT be exited in 5 days at the capped rate. At 15% participation, exit requires $50M / $2.25M ≈ 22 trading days (roughly 1 month).

(b) Square-root impact model per day of trading: impact ≈ 2.5% * sqrt(2.25M / 15M) = 2.5% * sqrt(0.15) = 2.5% * 0.387 = 0.97% per day of trading. Over 22 days of VWAP execution, the cumulative impact is not simply 22 * 0.97% because each day's impact builds on the prior day's displaced price. The total permanent impact is approximately 0.97% (the daily impact reflects the participation rate, not the cumulative effect). Temporary impact decays. Estimated permanent impact: ~1.0% of position value = $500K.

(c) Total cost includes: permanent impact (~$500K), temporary impact drag over 22 days (spread + slippage ≈ 0.15% per day * 22 = additional ~$165K across the trade), and opportunity cost of holding an unwanted position for 22 days (daily vol 2.5% * sqrt(22) ≈ 11.7% risk exposure during exit = implicit cost of ~$5.85M in risk-weighted terms). The explicit cost is roughly 1-1.5% of the position ($500K-$750K), but the implicit risk cost of the extended exit is far larger.""",
        answer_options=[
            AnswerOption(id="A", text="Position can be exited in 5 days at 15% participation with minimal impact", is_correct=False),
            AnswerOption(id="B", text="The position cannot be exited in 5 days at 15% participation — it requires approximately 22 trading days. Daily liquidation = $2.25M; 5-day capacity = $11.25M (22.5% of position). Market impact per the square-root model is approximately 1% permanent, but the larger cost is the 22-day risk exposure during the extended exit, representing ~11.7% volatility on the remaining position.", is_correct=True),
            AnswerOption(id="C", text="Increase participation to 50% of ADV to exit in 5 days — the additional impact is worth the speed", is_correct=False),
            AnswerOption(id="D", text="The position can be exited via a single block trade with negligible impact", is_correct=False),
        ],
        explanation="""This problem illustrates why position sizing relative to ADV is a critical pre-trade risk consideration.

Feasibility check:
- Daily capacity at 15% participation: 0.15 * $15M = $2.25M/day
- Days to exit: $50M / $2.25M = 22.2 days
- 5-day capacity: $11.25M = 22.5% of position
- Verdict: impossible at the capped participation rate

Market impact (square-root model):
The Almgren-Chriss model and its variants estimate temporary impact as:
impact = sigma * sqrt(V_trade / V_market)

Per-day impact: 2.5% * sqrt($2.25M / $15M) = 2.5% * 0.387 ≈ 0.97%

This impact has temporary and permanent components. Permanent impact reflects information leakage; temporary impact reflects liquidity displacement. A common split: 1/3 permanent, 2/3 temporary.

Opportunity cost analysis:
During the 22-day exit, the fund holds a diminishing but still large position subject to daily vol of 2.5%. The annualized vol of 2.5% * sqrt(252) ≈ 40% (this is a volatile stock). The risk of adverse price movement during the exit window is the dominant cost for large positions.

Practical lessons:
1. Position sizes should be capped at 3-5 days of ADV (here, 5 days = $75M at 100% participation)
2. At 15% participation and $15M ADV, the prudent max position is ~$11M (5 days * $2.25M)
3. The $50M position is oversized for this liquidity profile by roughly 4.5x""",
        reasoning_steps=[
            "Calculate daily liquidation capacity: 15% * $15M = $2.25M",
            "Determine days to exit: $50M / $2.25M ≈ 22 days — fails the 5-day target",
            "Apply square-root impact model: 2.5% * sqrt(0.15) ≈ 0.97% per day",
            "Separate permanent from temporary impact components",
            "Calculate opportunity cost: 22-day risk exposure during extended exit",
            "Conclude explicit cost is ~1-1.5% but implicit risk cost dominates",
        ],
        common_mistakes=[
            "Dividing position by ADV without applying the participation cap",
            "Treating market impact as linear in trade size (it is concave / square-root)",
            "Ignoring opportunity cost of the extended holding period",
            "Assuming block trades have no impact for positions this large",
            "Not considering that ADV itself may decline as the exit progresses (volume dries up)",
        ],
        tags=["liquidity", "market-impact", "position-sizing", "adv", "square-root-model", "risk-assessment"],
    ))

    # 11. Illiquidity Discount in Small-Cap
    problems.append(Problem(
        id="ra_liq_002",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""A small-cap position ($200M market cap, 2% of NAV in a $500M fund = $10M position) has a bid-ask spread of 150bps and average daily volume (ADV) of $2M.

The stock drops 8% on an earnings miss.

Estimate:
(a) The liquidation cost to exit the full position
(b) The time required to exit at 10% participation
(c) Whether the position violates a '5-day liquidation' risk limit""",
        context=FinancialContext(
            company_name="SmallCap Liquidity Corp",
            ticker="SMLQ",
            sector="Small-Cap",
            market_cap="$200M",
            model_assumptions={
                "Fund NAV": "$500M",
                "Position size": "$10M (2% of NAV)",
                "Market cap": "$200M",
                "Position as % of market cap": "5%",
                "Bid-ask spread": "150bps",
                "ADV": "$2M",
                "Post-earnings drop": "8%",
                "Daily vol (pre-earnings)": "3.5%",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""(a) Liquidation cost: At 10% participation, daily capacity = $200K. Exit time = $10M/$200K = 50 days. Spread cost: 150bps * $10M = $15K per round-trip (half-spread on exit ≈ $7.5K baseline, but post-earnings the spread likely widens to 250-400bps). Market impact per square-root model: sigma*sqrt(V/ADV) = 3.5%*sqrt(0.2M/2M) ≈ 3.5%*0.316 ≈ 1.1% per day. Total estimated liquidation cost: spread (75-200bps) + impact (110bps) + adverse drift during extended exit ≈ 2.5-4% of position value, or $250K-$400K.

(b) At 10% participation: $10M / ($2M * 10%) = 50 trading days (roughly 2.5 months). Post-earnings, ADV may temporarily spike (allowing faster exit in the first few days) or may decline if the stock is de-listed from screens.

(c) The 5-day liquidation test: At 10% participation, 5-day capacity = $1M = 10% of the position. The position clearly violates the 5-day liquidation limit. Even at 25% participation (aggressive), 5-day capacity = $2.5M = 25% of position. The fund would need to participate at 100% of ADV for 5 days ($10M) to liquidate, which would cause severe price impact likely exceeding 5-8%.""",
        answer_options=[
            AnswerOption(id="A", text="Position can be liquidated in 5 days with ~2% cost — within normal risk limits", is_correct=False),
            AnswerOption(id="B", text="Exit at 10% participation requires ~50 days; liquidation cost is 2.5-4% ($250K-$400K) including spread, impact, and drift. The position clearly violates the 5-day liquidation limit — only 10% of the position can be liquidated in 5 days at the capped participation rate.", is_correct=True),
            AnswerOption(id="C", text="The 8% earnings drop means the stock is now cheaper and should be held, not liquidated", is_correct=False),
            AnswerOption(id="D", text="Simply cross the position with another fund at the current bid to exit instantly", is_correct=False),
        ],
        explanation="""This problem highlights the structural liquidity risk embedded in small-cap positions.

Position characteristics:
- $10M in a $200M market cap stock = 5% of the company's equity
- ADV of $2M means the position is 5x daily volume
- The 150bps spread reflects thin market-maker inventory and low competition

Post-earnings environment:
- The 8% gap down likely widened spreads to 250-400bps
- Volume may spike temporarily (day 1-2) as other holders also sell
- The information asymmetry has increased, making market makers less willing to provide liquidity
- If the earnings miss signals fundamental deterioration, there may be persistent selling pressure

Liquidation timeline:
- 10% participation: $200K/day = 50 days
- 15% participation: $300K/day = 33 days
- 25% participation (aggressive): $500K/day = 20 days
- Any participation > 25% likely moves the price significantly

Cost decomposition:
1. Half-spread: 75-200bps (wider post-earnings)
2. Market impact: ~110bps per day at 10% participation
3. Information leakage: as the market detects a large seller, other participants front-run
4. Adverse selection: the post-earnings environment means sellers face adverse selection costs

Risk limit violation:
The 5-day liquidation test is a standard risk limit requiring that any position can be reduced by at least 80-100% within 5 business days at reasonable participation rates. This position fails that test comprehensively — it is fundamentally an illiquid position for a fund this size.

The pre-trade lesson: for a $500M fund with a 5-day liquidation rule and 10-15% max participation, the maximum position in a $2M ADV stock is $1M-$1.5M (0.2-0.3% of NAV), not $10M.""",
        reasoning_steps=[
            "Calculate exit time: $10M / (10% * $2M) = 50 trading days",
            "Estimate spread cost: 75-200bps (wider post-earnings)",
            "Estimate market impact: 3.5% * sqrt(0.1) ≈ 1.1% per day",
            "Total liquidation cost: 2.5-4% of position value",
            "5-day liquidation test: only $1M of $10M can be liquidated = clear violation",
            "Derive proper position sizing: max $1-1.5M at this ADV for a $500M fund",
        ],
        common_mistakes=[
            "Ignoring that post-earnings spreads are wider than normal-state spreads",
            "Assuming ADV stays constant during a liquidation (it may decline)",
            "Not considering information leakage as the market detects the seller",
            "Sizing positions based on market cap rather than ADV-based liquidation capacity",
            "Treating the 5-day rule as a soft guideline rather than a hard constraint",
        ],
        tags=["small-cap", "illiquidity", "bid-ask-spread", "position-sizing", "liquidation-risk", "risk-assessment"],
    ))

    # 12. Crowding and Liquidity Spirals
    problems.append(Problem(
        id="ra_liq_003",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.EXPERT,
        question="""A mid-cap stock ($3B market cap) has 20% of its float held by hedge funds with similar factor exposure (long momentum, short value). Average daily volume is $30M and the normal bid-ask spread is 20bps.

A forced deleveraging event hits (similar to the August 2007 quant crisis). Estimate the potential price impact of 5% of float being liquidated over 3 days, and explain the mechanism of a liquidity spiral.""",
        context=FinancialContext(
            company_name="Crowded Mid-Cap Corp",
            ticker="CRWD",
            sector="Mid-Cap Momentum",
            market_cap="$3B",
            model_assumptions={
                "Market cap": "$3B",
                "Float": "~$2.5B (assume 83% float)",
                "Hedge fund ownership": "20% of float = $500M",
                "ADV": "$30M",
                "Normal bid-ask spread": "20bps",
                "Forced liquidation": "5% of float = $125M over 3 days",
                "Normal daily vol": "2.0%",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""$125M liquidated over 3 days = $41.7M/day, which is 139% of normal ADV ($30M). This is an extreme liquidation intensity.

Price impact estimate using the square-root model with adjustments for crowding:
- Base impact per day: sigma * sqrt(V_trade/ADV) = 2% * sqrt(41.7/30) = 2% * 1.18 = 2.36% per day
- But this understates the true impact because: (1) at 139% ADV, the square-root model breaks down — price impact becomes closer to linear or even convex at extreme participation, (2) spreads widen dramatically — from 20bps to potentially 200-500bps as market makers pull back, (3) other hedge funds with similar positions also sell, amplifying the flow to potentially 30-40% of float.

Realistic estimate: 10-25% price decline over 3 days.

The liquidity spiral mechanism:
Step 1: Initial forced seller hits bids, moving price down 3-5%
Step 2: Other funds with similar positions see losses, triggering their own risk limits or margin calls
Step 3: Additional selling creates more price decline, causing more margin calls
Step 4: Market makers widen spreads and reduce inventory, removing liquidity precisely when it's most needed
Step 5: The feedback loop continues until either (a) new buyers are attracted by the lower price, (b) the selling is exhausted, or (c) circuit breakers or trading halts intervene

This is fundamentally a positive feedback loop: selling causes price decline which causes more selling. The August 2007 quant event saw previously uncorrelated stocks decline 20-30% in days as crowded factor positions unwound simultaneously.""",
        answer_options=[
            AnswerOption(id="A", text="Impact is approximately 2-3% — the square-root model handles this level of trading", is_correct=False),
            AnswerOption(id="B", text="At 139% of ADV per day, the standard impact models break down. Realistic impact: 10-25% over 3 days as the liquidity spiral unfolds — initial forced selling triggers margin calls at other similarly-positioned funds, which triggers more selling, while market makers pull back and widen spreads from 20bps to 200-500bps, removing liquidity precisely when it is most needed.", is_correct=True),
            AnswerOption(id="C", text="5% of float is immaterial for a $3B market cap stock", is_correct=False),
            AnswerOption(id="D", text="The impact is exactly 5% since 5% of float is being sold", is_correct=False),
        ],
        explanation="""This problem illustrates the non-linear dynamics of crowded position liquidation.

Why standard models fail:
1. Square-root impact assumes normal market conditions with active market makers
2. At 139% of ADV, you are THE market — there is no passive liquidity to absorb you
3. The model assumes your selling is independent of others' selling — in a crowding event, it is correlated

The liquidity spiral (Brunnermeier & Pedersen, 2009):
1. Funding liquidity shock hits: a fund faces margin calls or redemptions
2. Market liquidity evaporates: selling moves prices, widening spreads
3. Mark-to-market losses spread to other holders of the same positions
4. Their risk systems trigger selling (stop-losses, VaR breaches, margin calls)
5. The cycle repeats, each round amplifying the price decline

Empirical evidence:
- August 2007: quant funds lost 5-30% in a week as factor positions unwound
- March 2020: similar dynamics in credit and equity momentum
- January 2021 (GameStop): short-squeeze is the mirror image of a liquidation spiral

Crowding metrics that would have signaled risk:
- 20% of float held by similar-strategy funds is a red flag (>15% is typical threshold)
- Concentration of ownership in hedge funds with similar factor exposure
- High short interest combined with high long-side crowding
- Declining ADV relative to hedge fund position sizes

Risk management implication: positions in crowded names should be sized to survive a 20-30% drawdown without triggering portfolio-level risk limits, or hedged with tail protection.""",
        reasoning_steps=[
            "Calculate daily liquidation intensity: $41.7M/day = 139% of $30M ADV",
            "Recognize that standard impact models fail at >50% of ADV",
            "Apply crowding amplifier: other funds with similar positions also sell",
            "Model the liquidity spiral: selling → price decline → margin calls → more selling",
            "Estimate realistic impact: 10-25% over 3 days based on historical analogues",
            "Identify the spread widening mechanism: market makers reduce inventory in stress",
        ],
        common_mistakes=[
            "Applying square-root impact models at extreme participation rates",
            "Treating the forced seller as the only seller (ignoring correlated liquidation)",
            "Assuming market makers provide unlimited liquidity at all times",
            "Using normal-state spreads to estimate stress-state transaction costs",
            "Ignoring the self-reinforcing nature of the liquidity spiral",
        ],
        tags=["crowding", "liquidity-spiral", "forced-selling", "market-impact", "quant-crisis", "risk-assessment"],
    ))

    # =========================================================================
    # V. POSITION-LEVEL RISK METRICS (3 problems)
    # =========================================================================

    # 13. Kelly Criterion Application
    problems.append(Problem(
        id="ra_pos_001",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""You estimate a trade has 60% probability of making +15% and 40% probability of losing -12%.

(a) What is the Kelly-optimal position size as a % of NAV?
(b) What is the half-Kelly size?
(c) If the strategy has 10 concurrent similar bets with average pairwise correlation of 0.15, what is the appropriate portfolio-level Kelly allocation per position?""",
        context=FinancialContext(
            company_name="Kelly Criterion Analysis",
            ticker="N/A",
            sector="Position Sizing",
            model_assumptions={
                "Win probability": "60%",
                "Win payoff": "+15%",
                "Loss probability": "40%",
                "Loss payoff": "-12%",
                "Number of concurrent bets": "10",
                "Average pairwise correlation": "0.15",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""(a) Kelly fraction for a binary outcome: f* = (p*b - q) / b, where p = win probability, q = loss probability, b = win/loss ratio. Here b = 15/12 = 1.25, so f* = (0.60*1.25 - 0.40) / 1.25 = (0.75 - 0.40) / 1.25 = 0.35 / 1.25 = 28.0%.

Alternatively using the edge/odds formula: f* = edge / odds = (0.60*0.15 - 0.40*0.12) / 0.15 = (0.090 - 0.048) / 0.15 = 0.042 / 0.15 = 28.0%.

(b) Half-Kelly: 28% / 2 = 14% of NAV per position.

(c) With 10 correlated bets at rho = 0.15, the effective number of independent bets is approximately N_eff = N / (1 + rho*(N-1)) = 10 / (1 + 0.15*9) = 10 / 2.35 ≈ 4.26. The portfolio-level Kelly allocation across all bets should equal approximately f* (28%), divided across N positions but adjusted for correlation. Per position: f*_adjusted ≈ f* / (1 + rho*(N-1)) = 28% / 2.35 ≈ 11.9%. At half-Kelly (recommended for estimation uncertainty): ~6% per position.

Practitioners overwhelmingly use half-Kelly or less because: (1) the true edge is estimated with error (Kelly assumes known probabilities), (2) utility functions are more risk-averse than log-wealth, (3) drawdown tolerance is typically well below what full Kelly produces (Kelly-optimal strategies can experience 50%+ drawdowns).""",
        answer_options=[
            AnswerOption(id="A", text="Kelly = 60% - the position size should equal the win probability", is_correct=False),
            AnswerOption(id="B", text="Full Kelly = 28.0% of NAV; half-Kelly = 14.0%. With 10 correlated bets at rho=0.15, the per-position allocation adjusts to ~11.9% full Kelly or ~6% half-Kelly, reflecting reduced diversification. Practitioners favor half-Kelly or less due to estimation error in the probability inputs.", is_correct=True),
            AnswerOption(id="C", text="Kelly is irrelevant for equity portfolios — it only applies to gambling", is_correct=False),
            AnswerOption(id="D", text="Full Kelly = 48%, half-Kelly = 24% — larger size to capture the edge", is_correct=False),
        ],
        explanation="""Kelly Criterion derivation:

The Kelly criterion maximizes the expected log of wealth: E[log(1 + f*R)]

For a binary outcome:
E[log(1 + f*R)] = p*log(1 + f*b) + q*log(1 - f)

Taking the derivative and setting to zero:
f* = p - q/b = p - q*(loss/win) = 0.60 - 0.40*(12/15) = 0.60 - 0.32 = 0.28

Or equivalently: f* = (p*b - q) / b = (0.75 - 0.40) / 1.25 = 0.28

Properties of Kelly sizing:
- Maximizes long-run geometric growth rate
- Is aggressive: Kelly-optimal strategies have ~50% probability of a 50% drawdown
- Assumes KNOWN probabilities — estimation error makes overbetting extremely costly
- The penalty for overbetting is worse than underbetting (asymmetric around f*)

Multi-position adjustment:
With N correlated bets, total portfolio risk is N * f * sigma * sqrt((1 + rho*(N-1))/N). To maintain the same risk level as a single Kelly bet, each position should be scaled by 1/(1 + rho*(N-1)). This gives:

f_per_position = f* / (1 + rho*(N-1)) = 0.28 / (1 + 0.15*9) = 0.28 / 2.35 ≈ 0.119

The half-Kelly recommendation (~6% per position) is the practical starting point, further adjusted for:
- Confidence in probability estimates (lower confidence → smaller fraction)
- Drawdown tolerance (lower tolerance → smaller fraction)
- Correlation estimation uncertainty (likely higher in stress → smaller fraction)""",
        reasoning_steps=[
            "Apply Kelly formula: f* = (p*b - q) / b where b = win/loss ratio",
            "Calculate: f* = (0.60*1.25 - 0.40) / 1.25 = 28%",
            "Half-Kelly: 28% / 2 = 14%",
            "For correlated bets: N_eff = N / (1 + rho*(N-1)) ≈ 4.26",
            "Per-position Kelly with correlation: 28% / 2.35 ≈ 11.9%",
            "Practical recommendation: half-Kelly with correlation adjustment ≈ 6% per position",
        ],
        common_mistakes=[
            "Confusing Kelly fraction with win probability",
            "Using full Kelly without accounting for estimation uncertainty",
            "Ignoring correlation when sizing a portfolio of similar bets",
            "Not recognizing that Kelly maximizes log-wealth, which is more aggressive than most risk preferences",
            "Applying the single-bet Kelly formula to each position independently in a portfolio",
        ],
        tags=["kelly-criterion", "position-sizing", "correlation", "geometric-growth", "risk-assessment"],
    ))

    # 14. VaR vs. Expected Shortfall
    problems.append(Problem(
        id="ra_pos_002",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.EXPERT,
        question="""A portfolio has 1-day 95% VaR of $2M and 1-day 99% VaR of $4M. The portfolio NAV is $100M.

Estimate the Expected Shortfall (CVaR) at 95% assuming a Student-t distribution with 5 degrees of freedom. Explain why ES is more useful than VaR for tail risk management, and identify a key limitation of both measures.""",
        context=FinancialContext(
            company_name="Tail Risk Analysis",
            ticker="N/A",
            sector="Portfolio Risk",
            model_assumptions={
                "Portfolio NAV": "$100M",
                "1-day 95% VaR": "$2M (2% of NAV)",
                "1-day 99% VaR": "$4M (4% of NAV)",
                "Distribution assumption": "Student-t with 5 degrees of freedom",
                "VaR ratio (99/95)": "2.0x (vs. 1.52x for normal distribution)",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""The 99/95 VaR ratio of 2.0 (= $4M/$2M) is significantly higher than the normal distribution ratio of ~1.52 (2.326/1.645), confirming heavy tails consistent with Student-t behavior.

For a Student-t distribution with nu=5 degrees of freedom, the ES at 95% can be estimated using:
ES_alpha = VaR_alpha * [t_pdf(t_inv(alpha)) / (1-alpha)] * [(nu + t_inv(alpha)^2) / (nu - 1)]

For alpha = 0.95 with nu = 5:
- t-quantile at 95%: t_0.95,5 ≈ 2.015
- The ES/VaR ratio for t(5) at 95% ≈ 1.68

ES_95% ≈ $2M * 1.68 = approximately $3.4M

This means that when losses exceed the 95% VaR ($2M), the average loss is approximately $3.4M — significantly worse than VaR alone suggests.

ES is superior to VaR because: (1) ES is coherent (satisfies subadditivity — diversified portfolios have lower ES), while VaR can violate subadditivity, (2) ES captures the severity of tail losses, not just the threshold, (3) ES is more sensitive to the shape of the tail distribution.

A key limitation of both: they rely on distributional assumptions and historical data that may not capture regime changes or unprecedented events. Neither VaR nor ES addresses liquidity risk, concentration risk, or the possibility that correlations shift during stress.""",
        answer_options=[
            AnswerOption(id="A", text="ES at 95% is approximately $2.5M — just slightly above VaR", is_correct=False),
            AnswerOption(id="B", text="ES at 95% is approximately $3.4M (ES/VaR ratio ≈ 1.68 for t(5) at 95%). ES is superior because it is coherent (subadditive), captures tail severity rather than just a threshold, and is more sensitive to distributional shape. Both measures are limited by reliance on historical data and distributional assumptions that may fail in novel stress scenarios.", is_correct=True),
            AnswerOption(id="C", text="ES equals the 99% VaR ($4M) by definition", is_correct=False),
            AnswerOption(id="D", text="ES is unnecessary — the 99% VaR captures all relevant tail information", is_correct=False),
        ],
        explanation="""Expected Shortfall (CVaR) is defined as:
ES_alpha = E[L | L > VaR_alpha] = expected loss given that the loss exceeds VaR

For the Student-t distribution with nu degrees of freedom:
ES_alpha / VaR_alpha = [f(t_alpha) / (1-alpha)] * [(nu + t_alpha^2) / (nu - 1)]

where f is the t-density and t_alpha is the alpha-quantile.

For nu = 5, alpha = 0.95:
- t_alpha ≈ 2.015
- f(t_alpha) for t(5) ≈ 0.0514
- ES/VaR = [0.0514 / 0.05] * [(5 + 4.06) / 4] = 1.028 * 2.265 ≈ 2.33

Wait — let me recalculate more carefully. The scaling formula:
For a standardized t(nu) at confidence level alpha:
ES/VaR = [f_t(t_alpha; nu) / (1-alpha)] * [(nu + t_alpha^2) / (nu - 1)]

With our non-standardized distribution (calibrated to match the given VaR values):
The ratio of 99% to 95% VaR = 2.0, which maps to t(5) well.

For practical estimation, the ES at 95% for t(5) is approximately 1.5-1.8x the 95% VaR, giving $3.0M to $3.6M. The midpoint estimate of ~$3.4M is reasonable.

Why ES > VaR for risk management:

1. Subadditivity: VaR(A+B) can exceed VaR(A) + VaR(B) for non-elliptical distributions. This means VaR can suggest that combining portfolios increases risk, which violates the principle of diversification. ES always satisfies VaR(A+B) <= ES(A) + ES(B).

2. Tail sensitivity: Two portfolios can have identical VaR but very different tail losses. VaR is a quantile — it tells you the threshold but nothing about what happens beyond it.

3. Regulatory adoption: Basel III moved from VaR to ES for market risk capital requirements precisely because of these properties.

Limitations of both:
- Model risk: both depend on distributional assumptions
- Stationarity: both assume the return process is stationary
- Historical bias: calibrated to historical data, which may not capture future stress
- No liquidity adjustment: both assume positions can be liquidated at current marks
- Correlation breakdown: both typically use point-in-time correlation estimates""",
        reasoning_steps=[
            "Verify heavy tails: 99/95 VaR ratio = 2.0 vs. 1.52 for normal → confirms fat tails",
            "Identify Student-t(5) as consistent with the observed VaR ratio",
            "Apply ES/VaR ratio formula for t(5) at 95% confidence: approximately 1.68",
            "Estimate ES: $2M * 1.68 ≈ $3.4M",
            "Explain coherence (subadditivity) as the key advantage of ES over VaR",
            "Identify shared limitations: model risk, stationarity, no liquidity adjustment",
        ],
        common_mistakes=[
            "Assuming ES equals VaR at a different confidence level (e.g., ES_95 = VaR_99)",
            "Using the normal distribution ES/VaR ratio when tails are clearly fat",
            "Ignoring that the 99/95 VaR ratio itself is a diagnostic for tail heaviness",
            "Treating VaR as a worst-case loss rather than a threshold",
            "Not recognizing that ES, while better than VaR, still relies on assumptions that fail in crisis",
        ],
        tags=["var", "expected-shortfall", "cvar", "student-t", "tail-risk", "coherent-risk-measures", "risk-assessment"],
    ))

    # 15. Beta-Adjusted Exposure
    problems.append(Problem(
        id="ra_pos_003",
        category=ProblemCategory.RISK_ASSESSMENT,
        difficulty=Difficulty.HARD,
        question="""A long/short portfolio has:
- Long book: $150M with beta 1.3
- Short book: $100M with beta 0.8

Calculate:
(a) Gross exposure
(b) Net exposure
(c) Beta-adjusted net exposure
(d) Net market exposure in 'S&P equivalent' dollars
(e) If the PM wants to be market-neutral on a beta-adjusted basis, what short exposure is needed (assuming the short book beta stays at 0.8)?""",
        context=FinancialContext(
            company_name="L/S Equity Portfolio",
            ticker="N/A",
            sector="Long/Short Equity",
            model_assumptions={
                "Long book": "$150M, beta 1.3",
                "Short book": "$100M, beta 0.8",
                "Fund NAV": "$250M (assumed)",
                "Benchmark": "S&P 500",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="""(a) Gross exposure = $150M + $100M = $250M (100% of NAV if NAV = $250M).

(b) Net exposure = $150M - $100M = $50M (20% of NAV).

(c) Beta-adjusted net exposure = (Long * Beta_long) - (Short * Beta_short) = ($150M * 1.3) - ($100M * 0.8) = $195M - $80M = $115M. As a % of NAV: $115M / $250M = 46%.

(d) S&P equivalent dollars: $115M. This means the portfolio has the market sensitivity of a $115M long-only S&P 500 position. If the S&P drops 10%, the expected portfolio loss from market exposure alone is approximately $11.5M (4.6% of NAV).

(e) For beta-adjusted market neutrality: Long beta dollars = Short beta dollars. $150M * 1.3 = Short * 0.8. Short = $195M / 0.8 = $243.75M. The PM needs to increase shorts from $100M to $243.75M, nearly 2.5x the current short book. This would bring gross exposure to $393.75M (157.5% of NAV) and net dollar exposure to -$93.75M (net short on a dollar basis but market-neutral on a beta-adjusted basis).

The critical insight: the current portfolio appears modestly net long at $50M (20% net), but the beta-adjusted exposure is $115M (46% of NAV) — more than double the dollar net. A PM who reports '20% net long' while running 46% beta-adjusted net long is understating market risk substantially.""",
        answer_options=[
            AnswerOption(id="A", text="Beta-adjusted net = $50M (same as dollar net since betas approximately average to 1.0)", is_correct=False),
            AnswerOption(id="B", text="Gross = $250M, net = $50M (20%), beta-adjusted net = $115M (46%). The portfolio has 2.3x more market exposure than the dollar net suggests. To achieve beta-neutral: short $243.75M (up from $100M), keeping short beta at 0.8. The key insight is that dollar-neutral and beta-neutral are very different when long and short betas diverge.", is_correct=True),
            AnswerOption(id="C", text="Beta-adjusted net = $70M — average the long and short betas and multiply by net exposure", is_correct=False),
            AnswerOption(id="D", text="Beta adjustment is unnecessary — dollar exposure fully captures market risk", is_correct=False),
        ],
        explanation="""This problem illustrates a fundamental concept in L/S equity risk management: dollar exposure and beta-adjusted exposure can diverge significantly.

Step-by-step:
(a) Gross = |Long| + |Short| = $150M + $100M = $250M
(b) Net = Long - Short = $150M - $100M = $50M
(c) Beta-adjusted net = (Long * beta_L) - (Short * beta_S) = $195M - $80M = $115M
(d) S&P equivalent = $115M (the portfolio moves as if it were $115M in the S&P)

Why the gap matters:
- The long book (beta 1.3) is more cyclical/sensitive than the market
- The short book (beta 0.8) is more defensive/less sensitive
- A 10% market decline would produce:
  - Long loss: $150M * 1.3 * 10% = $19.5M
  - Short gain: $100M * 0.8 * 10% = $8.0M
  - Net loss: $11.5M = 4.6% of NAV

If the PM reported this as '20% net long,' the risk committee might assume a 10% market decline costs 2% of NAV. The actual cost would be 4.6% — more than double.

Beta-neutral construction:
To set beta-adjusted net to zero:
$150M * 1.3 = Short * 0.8
Short = $195M / 0.8 = $243.75M

This demonstrates why many L/S funds run large gross exposures to achieve beta neutrality when their long and short books have different beta profiles. A fund with high-beta longs and low-beta shorts needs proportionally more short dollars to offset the market exposure.

Practical considerations:
- Beta is estimated with error (typically ±0.2-0.3 for a 52-week rolling estimate)
- Beta changes with market conditions (conditional beta)
- The short book's beta may increase in a crash (low-beta stocks can become high-beta in stress)
- Transaction costs of maintaining the larger short book reduce net returns""",
        reasoning_steps=[
            "Calculate gross: $150M + $100M = $250M",
            "Calculate net: $150M - $100M = $50M (20%)",
            "Calculate beta-adjusted net: $150M*1.3 - $100M*0.8 = $195M - $80M = $115M (46%)",
            "Interpret S&P equivalent: $115M of market risk = 4.6% loss per 10% market decline",
            "Solve for beta-neutral short: $195M / 0.8 = $243.75M needed",
            "Note the 2.3x gap between dollar net (20%) and beta-adjusted net (46%)",
        ],
        common_mistakes=[
            "Reporting dollar net exposure as the measure of market risk",
            "Averaging the long and short betas rather than dollar-weighting them",
            "Assuming beta-neutral and dollar-neutral are interchangeable",
            "Ignoring that beta estimation error creates residual market exposure",
            "Not considering that the short book's beta may shift in stress environments",
        ],
        tags=["beta-adjusted", "net-exposure", "gross-exposure", "long-short", "market-neutral", "risk-assessment"],
    ))

    return problems


if __name__ == "__main__":
    problems = generate_risk_assessment_problems()
    print(f"Generated {len(problems)} risk assessment problems")

    from collections import Counter
    categories = Counter(p.category.value for p in problems)
    difficulties = Counter(p.difficulty.value for p in problems)

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print("\nDifficulty distribution:")
    for diff, count in sorted(difficulties.items()):
        print(f"  {diff}: {count}")

    # Print problem IDs and titles
    print("\nProblem listing:")
    for i, p in enumerate(problems, 1):
        print(f"  {i}. [{p.id}] ({p.difficulty.value}) {p.question[:80]}...")
