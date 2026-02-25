"""
Estimation Error & Backtesting Rigor Problems

12 expert/hard problems covering concepts from:
    Paleologo, G. (2024). The Elements of Quantitative Investing.

Topics:
- Sharpe Ratio Efficiency (SRE) and estimation error (Ch 5.3)
- Rademacher complexity bounds for backtesting (Ch 6.3)
- IC/IR confusion and the Fundamental Law (Ch 4.4)
- Alpha estimation error vs. risk estimation error (Ch 5.2)
- Deflated Sharpe Ratio and multiple testing (FAQ 4.2)
- Autocorrelation effects on Sharpe inference (FAQ 4.2)
- Precision matrix and partial correlations (Insight 4.2)
- Robust optimization penalties (Table 5.1)

These problems test whether an LLM can reason about the gap between
backtest performance and real-world deployment — the central challenge
of quantitative investing.
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


def generate_estimation_error_problems() -> list[Problem]:
    """Generate 12 estimation-error and backtesting-rigor problems."""
    problems = []

    # =========================================================================
    # 1. Sharpe Ratio Efficiency (SRE)
    # =========================================================================
    problems.append(Problem(
        id="ee_sre_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""An optimizer uses estimated alphas (α̂) and covariance (Ω̂) to construct a portfolio. The Sharpe Ratio Efficiency (SRE) is defined as:

    SRE = SR(α̂, Ω̂) / SR(α, Ω)

where the numerator uses estimated inputs and the denominator uses true (unknown) inputs.

With 50 assets, 5 years of daily data, and moderate estimation noise, what is a realistic SRE, and what does it imply?""",
        context=FinancialContext(
            company_name="Portfolio Optimization Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Sharpe Ratio Efficiency:
- SRE = SR(estimated) / SR(true)
- N = 50 assets
- T = 1,260 daily observations (5 years)
- T/N ratio = 25.2
- True Sharpe (with perfect inputs): 1.5""",
            model_assumptions={
                "Number of assets": "50",
                "Data history": "5 years daily (1,260 obs)",
                "True Sharpe": "1.5",
                "Alpha estimation noise": "Moderate",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="SRE is typically 0.3-0.6 for realistic T/N ratios around 25. This means estimated-input portfolios capture only 30-60% of the theoretically achievable Sharpe. With 50 assets and 1,260 observations, alpha estimation error dominates — the optimizer amplifies noise in expected returns through Ω⁻¹. A true Sharpe of 1.5 becomes 0.45-0.90 in practice.",
        answer_options=[
            AnswerOption(id="A", text="SRE ≈ 0.95 — estimation error is negligible with 5 years of data", is_correct=False),
            AnswerOption(id="B", text="SRE is typically 0.3-0.6 for realistic T/N ratios around 25. This means estimated-input portfolios capture only 30-60% of the theoretically achievable Sharpe. With 50 assets and 1,260 observations, alpha estimation error dominates — the optimizer amplifies noise in expected returns through Ω⁻¹. A true Sharpe of 1.5 becomes 0.45-0.90 in practice.", is_correct=True),
            AnswerOption(id="C", text="SRE ≈ 0.0 — optimization with estimated inputs is worthless", is_correct=False),
            AnswerOption(id="D", text="SRE depends only on covariance estimation, not alpha estimation", is_correct=False),
        ],
        explanation="Paleologo (2024, Ch 5.3) shows SRE degrades rapidly as N/T increases. The MVO formula w ∝ Ω⁻¹α amplifies alpha errors by the inverse covariance. With N=50 and T=1,260, the covariance matrix is well-estimated (T >> N), but alpha has SE ≈ σ/√T per asset. The optimizer treats noisy alphas as precise, allocating aggressively to assets with favorable noise. Shrinkage or constraints improve SRE by reducing sensitivity to estimation error.",
        reasoning_steps=[
            "SRE measures the fraction of theoretical Sharpe achieved with noisy inputs",
            "MVO weights w ∝ Ω⁻¹α amplify errors in α",
            "Alpha estimation error: SE(α) ≈ σ/√T for each asset",
            "With 50 assets and T/N ≈ 25, SRE is typically 0.3-0.6",
            "Implication: most of the 'optimal' Sharpe is lost to estimation error",
        ],
        source="Paleologo (2024), Ch 5.3: Sharpe Ratio Efficiency",
        tags=["sre", "estimation-error", "optimization", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 2. Rademacher Complexity Bound
    # =========================================================================
    problems.append(Problem(
        id="ee_rademacher_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""A researcher tests 500 alpha signals over 10 years of daily data (T = 2,520). The best signal shows a backtest Sharpe of 1.8. Using the Rademacher complexity framework:

    θ ≥ θ̂ - 2R̂ - 2√(log(2/δ) / T)

If the empirical Rademacher complexity R̂ = 0.03 and δ = 0.05, what is the performance lower bound, and should the researcher trust the backtest?""",
        context=FinancialContext(
            company_name="Backtesting Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Rademacher Bound:
- θ ≥ θ̂ - 2R̂ - 2√(log(2/δ) / T)
- θ̂ = 1.8 (observed Sharpe, annualized ÷ √252 ≈ 0.113 periodic)
- R̂ = 0.03 (empirical Rademacher complexity)
- T = 2,520 trading days
- δ = 0.05 (95% confidence)
- N = 500 strategies tested""",
            model_assumptions={
                "Strategies tested": "500",
                "Data period": "10 years daily",
                "Best backtest Sharpe": "1.8",
                "Rademacher complexity": "0.03",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Data snooping penalty: 2 × 0.03 = 0.06. Estimation error: 2 × √(log(40)/2520) ≈ 2 × 0.038 = 0.076. Using periodic Sharpe ≈ 0.113: lower bound = 0.113 - 0.06 - 0.076 ≈ -0.023. The lower bound is negative — the best signal's performance is statistically indistinguishable from noise after accounting for 500-signal search. The researcher should not trust the backtest.",
        answer_options=[
            AnswerOption(id="A", text="Sharpe 1.8 is highly significant — 500 signals doesn't matter with 10 years of data", is_correct=False),
            AnswerOption(id="B", text="Data snooping penalty: 2 × 0.03 = 0.06. Estimation error: 2 × √(log(40)/2520) ≈ 2 × 0.038 = 0.076. Using periodic Sharpe ≈ 0.113: lower bound = 0.113 - 0.06 - 0.076 ≈ -0.023. The lower bound is negative — the best signal's performance is statistically indistinguishable from noise after accounting for 500-signal search. The researcher should not trust the backtest.", is_correct=True),
            AnswerOption(id="C", text="The Rademacher bound only applies to in-sample, not out-of-sample performance", is_correct=False),
            AnswerOption(id="D", text="With 10 years of data, any Sharpe above 1.0 is reliable", is_correct=False),
        ],
        explanation="Per Paleologo (2024, Ch 6.3), the Rademacher bound decomposes backtest performance into three parts: true signal (θ), data snooping cost (2R̂ — proportional to strategy-set complexity), and estimation noise (2√(log(2/δ)/T)). The key insight: testing 500 signals inflates R̂ because the strategy family can better fit random noise. Even with 10 years of data, the combined penalties wipe out a Sharpe of 1.8. This is why honest accounting of the search process is critical.",
        reasoning_steps=[
            "Convert annualized Sharpe to periodic: 1.8/√252 ≈ 0.113",
            "Data snooping penalty = 2R̂ = 2 × 0.03 = 0.06",
            "Estimation error = 2√(log(2/0.05)/2520) = 2√(3.69/2520) ≈ 0.076",
            "Lower bound = 0.113 - 0.06 - 0.076 = -0.023",
            "Negative bound: cannot reject that performance is pure noise",
        ],
        source="Paleologo (2024), Ch 6.3: Rademacher Complexity",
        tags=["rademacher", "data-snooping", "backtesting", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 3. IC vs IR Confusion
    # =========================================================================
    problems.append(Problem(
        id="ee_ic_ir_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A quant reports their signal has IC = 0.05 and claims this implies an Information Ratio of 1.5 using the Fundamental Law: IR = IC × √(breadth).

Their universe has 500 stocks rebalanced monthly (breadth = 500 × 12 = 6,000).

What is wrong with this calculation?""",
        context=FinancialContext(
            company_name="Fundamental Law Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Fundamental Law of Active Management:
- IR = IC × √(N × T)
- Claimed IC = 0.05
- Universe = 500 stocks
- Rebalance = monthly (12x/year)
- Claimed breadth = 6,000
- Claimed IR = 0.05 × √6000 ≈ 3.87 (not 1.5 as stated, but even 1.5 is suspicious)""",
            model_assumptions={
                "Signal IC": "0.05",
                "Universe size": "500 stocks",
                "Rebalance frequency": "Monthly",
                "Claimed breadth": "6,000",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Multiple errors: (1) Breadth is independent bets, not stock-count × periods. With correlated stocks, effective breadth << 6,000. (2) IC must be measured in idiosyncratic (residual) space, not total return space — factor-driven correlation inflates raw IC. (3) The Fundamental Law assumes uncorrelated signals across time; serial correlation in monthly signals reduces effective T. Realistic IR with IC=0.05 is closer to 0.3-0.5.",
        answer_options=[
            AnswerOption(id="A", text="The calculation is correct — IR = IC × √(breadth) with breadth = N × T", is_correct=False),
            AnswerOption(id="B", text="Multiple errors: (1) Breadth is independent bets, not stock-count × periods. With correlated stocks, effective breadth << 6,000. (2) IC must be measured in idiosyncratic (residual) space, not total return space — factor-driven correlation inflates raw IC. (3) The Fundamental Law assumes uncorrelated signals across time; serial correlation in monthly signals reduces effective T. Realistic IR with IC=0.05 is closer to 0.3-0.5.", is_correct=True),
            AnswerOption(id="C", text="The only error is using 12 months — should use 252 trading days", is_correct=False),
            AnswerOption(id="D", text="IC of 0.05 is too low to generate any meaningful IR", is_correct=False),
        ],
        explanation="Paleologo (2024, Ch 4.4) defines IC as the cross-sectional idiosyncratic-variance-weighted correlation between alphas and returns. Raw cross-sectional correlation overstates IC because common factors drive co-movement. The 'breadth' in the Fundamental Law is the number of truly independent bets. With 500 stocks in 10 sectors, effective breadth might be 50-100 per period. Monthly serial correlation further reduces temporal breadth.",
        reasoning_steps=[
            "Breadth ≠ N × T when positions are correlated",
            "500 stocks may share factor exposures → effective breadth << 500",
            "IC should be computed in idiosyncratic space, not total return",
            "Monthly signals may be autocorrelated → effective T < 12",
            "Realistic IR with IC=0.05: 0.05 × √(50×6) ≈ 0.87 at best",
        ],
        source="Paleologo (2024), Ch 4.4: Information Coefficient",
        tags=["ic", "ir", "fundamental-law", "breadth", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 4. Alpha Error vs Risk Error Asymmetry
    # =========================================================================
    problems.append(Problem(
        id="ee_alpha_risk_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""In MVO, w ∝ Ω⁻¹α. Estimation errors exist in both α (expected returns) and Ω (covariance matrix).

Which estimation error has a larger impact on portfolio performance, and why?""",
        context=FinancialContext(
            company_name="Estimation Error Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Mean-Variance Optimization:
- w* = (1/γ) × Ω⁻¹ × α
- α estimation: SE(α) ≈ σ/√T per asset
- Ω estimation: SE improves with √T
- N = 30 assets, T = 500 days
- True Sharpe = 1.0""",
            model_assumptions={
                "N assets": "30",
                "T observations": "500",
                "Return estimation error": "σ/√T ≈ 0.7% per asset",
                "Covariance estimation quality": "Good (T >> N)",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Alpha estimation error dominates. Expected returns have SE ≈ σ/√T, which is large relative to the signal itself (a 6% expected return has ±3% SE with 5 years of data). Covariance estimation converges at rate √T and is more stable. The Ω⁻¹ multiplication amplifies alpha errors but not covariance errors equally. Improving alpha estimates yields far more Sharpe than improving Ω estimates.",
        answer_options=[
            AnswerOption(id="A", text="Covariance error dominates because Ω has N(N+1)/2 parameters", is_correct=False),
            AnswerOption(id="B", text="Alpha estimation error dominates. Expected returns have SE ≈ σ/√T, which is large relative to the signal itself (a 6% expected return has ±3% SE with 5 years of data). Covariance estimation converges at rate √T and is more stable. The Ω⁻¹ multiplication amplifies alpha errors but not covariance errors equally. Improving alpha estimates yields far more Sharpe than improving Ω estimates.", is_correct=True),
            AnswerOption(id="C", text="Both errors contribute equally to performance loss", is_correct=False),
            AnswerOption(id="D", text="With T >> N, neither estimation error matters", is_correct=False),
        ],
        explanation="Per Paleologo (2024, Ch 5.2), the signal-to-noise ratio for expected returns is fundamentally low: annual return of 6% with 20% vol gives SR = 0.3, but the estimation SE is σ/√T ≈ 20%/√5 ≈ 9% annually — larger than the signal. Covariance estimation is much better: correlations are estimated with SE ≈ 1/√T ≈ 0.04 with 5 years, plenty precise. The optimizer treats all α estimates as truth, so noisy α → extreme positions. This is why shrinkage estimators for α matter more than Ledoit-Wolf for Ω.",
        reasoning_steps=[
            "α estimation: SE(α) ≈ σ/√T, often larger than the signal itself",
            "Ω estimation: converges faster, more parameters but more data points per estimate",
            "w ∝ Ω⁻¹α: errors in α get multiplied by Ω⁻¹",
            "Small α errors → large weight errors when Ω has near-singular structure",
            "Improving α estimates (shrinkage, priors) dominates improving Ω",
        ],
        source="Paleologo (2024), Ch 5.2: Alpha vs Risk Estimation Error",
        tags=["estimation-error", "alpha", "covariance", "mvo", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 5. Autocorrelation and Sharpe Inflation
    # =========================================================================
    problems.append(Problem(
        id="ee_sharpe_autocorr_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A strategy's daily returns have first-order autocorrelation ρ = 0.15. The naïve annualized Sharpe ratio is 1.2.

What is the autocorrelation-adjusted Sharpe ratio, and why does the adjustment matter?""",
        context=FinancialContext(
            company_name="Sharpe Adjustment Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Autocorrelation adjustment (Paleologo FAQ 4.2):
- SR_adj = SR × √((1-ρ)/(1+ρ))
- Naïve SR = 1.2
- ρ = 0.15 (daily return autocorrelation)
- Standard √252 annualization assumes iid returns"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="SR_adj = 1.2 × √((1-0.15)/(1+0.15)) = 1.2 × √(0.739) = 1.2 × 0.860 = 1.03. The 14% reduction reflects that positive autocorrelation inflates the naïve Sharpe: √252 annualization assumes returns are independent, but autocorrelation means variance grows faster than √T, so the 'true' annualized vol is higher and Sharpe is lower.",
        answer_options=[
            AnswerOption(id="A", text="Autocorrelation doesn't affect the Sharpe ratio", is_correct=False),
            AnswerOption(id="B", text="SR_adj = 1.2 × √((1-0.15)/(1+0.15)) = 1.2 × √(0.739) = 1.2 × 0.860 = 1.03. The 14% reduction reflects that positive autocorrelation inflates the naïve Sharpe: √252 annualization assumes returns are independent, but autocorrelation means variance grows faster than √T, so the 'true' annualized vol is higher and Sharpe is lower.", is_correct=True),
            AnswerOption(id="C", text="The adjustment should increase the Sharpe because autocorrelation indicates momentum", is_correct=False),
            AnswerOption(id="D", text="SR_adj = 1.2 × (1-0.15) = 1.02 — subtract the autocorrelation directly", is_correct=False),
        ],
        explanation="Per Paleologo (2024, FAQ 4.2), the standard √T annualization of Sharpe assumes iid returns. With positive autocorrelation ρ > 0, annualized variance = daily_var × T × (1 + 2ρ/(1-ρ)) approximately, not daily_var × T. The adjustment factor √((1-ρ)/(1+ρ)) corrects for this. Sources of autocorrelation: stale prices, illiquidity, bid-ask bounce patterns, or genuine momentum. Always report the adjusted Sharpe.",
        reasoning_steps=[
            "Naïve annualization assumes iid: σ_annual = σ_daily × √252",
            "With ρ > 0, true annualized vol is higher (returns trend)",
            "Adjustment factor = √((1-ρ)/(1+ρ))",
            "SR_adj = 1.2 × √(0.85/1.15) = 1.2 × 0.860 ≈ 1.03",
            "14% inflation from ignoring autocorrelation",
        ],
        source="Paleologo (2024), FAQ 4.2: Sharpe Ratio Confidence Intervals",
        tags=["sharpe-ratio", "autocorrelation", "annualization", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 6. Sharpe CI Width
    # =========================================================================
    problems.append(Problem(
        id="ee_sharpe_ci_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A strategy has an observed Sharpe ratio of 0.8 computed from 3 years of daily data (T = 756).

Using SE(SR) = √((1 + SR²/2) / T), compute the 95% confidence interval. Is Sharpe 0.8 statistically distinguishable from zero?""",
        context=FinancialContext(
            company_name="Sharpe Inference Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Sharpe CI (Paleologo FAQ 4.2):
- SE(SR) = √((1 + SR²/2) / T)
- SR = 0.8 (annualized)
- Periodic SR = 0.8/√252 ≈ 0.0504
- T = 756 daily observations
- 95% CI: SR ± 1.96 × SE"""
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Periodic SR = 0.0504. SE = √((1 + 0.0504²/2) / 756) = √(1.00127 / 756) ≈ 0.0364. Annualized SE = 0.0364 × √252 ≈ 0.578. 95% CI: 0.8 ± 1.96 × 0.578 = [-0.33, 1.93]. The CI includes zero — a Sharpe of 0.8 is NOT statistically distinguishable from zero with only 3 years of data. This illustrates why Sharpe ratios require decades to estimate precisely.",
        answer_options=[
            AnswerOption(id="A", text="95% CI is [0.6, 1.0] — Sharpe 0.8 is clearly significant", is_correct=False),
            AnswerOption(id="B", text="Periodic SR = 0.0504. SE = √((1 + 0.0504²/2) / 756) = √(1.00127 / 756) ≈ 0.0364. Annualized SE = 0.0364 × √252 ≈ 0.578. 95% CI: 0.8 ± 1.96 × 0.578 = [-0.33, 1.93]. The CI includes zero — a Sharpe of 0.8 is NOT statistically distinguishable from zero with only 3 years of data. This illustrates why Sharpe ratios require decades to estimate precisely.", is_correct=True),
            AnswerOption(id="C", text="Statistical significance doesn't matter for Sharpe ratios", is_correct=False),
            AnswerOption(id="D", text="Use monthly data instead — fewer observations but wider CI", is_correct=False),
        ],
        explanation="Per Paleologo (2024, FAQ 4.2), SE(SR) ≈ 1/√T for small Sharpe ratios. With T=756, SE ≈ 0.036 in periodic terms, or ≈ 0.58 annualized. This wide CI reflects a fundamental problem: expected return estimation requires long time spans (SE(μ) depends on total duration, not frequency). Even a 'good' Sharpe of 0.8 needs ~15 years of data to reject SR=0 at 95% confidence: T needed ≈ (1.96/SR)² × 252 ≈ 1,512 for SR=0.8.",
        reasoning_steps=[
            "Convert annualized to periodic SR: 0.8/√252 ≈ 0.0504",
            "SE(SR) = √((1 + SR²/2) / T) = √(1.001/756) ≈ 0.0364",
            "Annualize SE: 0.0364 × √252 ≈ 0.578",
            "95% CI: [0.8 - 1.13, 0.8 + 1.13] = [-0.33, 1.93]",
            "CI includes 0: cannot reject null of zero Sharpe",
        ],
        source="Paleologo (2024), FAQ 4.2: SE(SR) Formula",
        tags=["sharpe-ratio", "confidence-interval", "statistical-inference", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 7. Precision Matrix / Partial Correlations
    # =========================================================================
    problems.append(Problem(
        id="ee_precision_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""Two tech stocks (AAPL, MSFT) show 0.85 pairwise correlation but only 0.15 partial correlation after controlling for SPY and QQQ.

What does this reveal about portfolio construction, and how does the precision matrix help?""",
        context=FinancialContext(
            company_name="Partial Correlation Analysis",
            ticker="N/A",
            sector="Technology",
            formula_context="""Partial Correlation (Paleologo Insight 4.2):
- ρ_partial(i,j) = -Ω⁻¹_{i,j} / √(Ω⁻¹_{i,i} × Ω⁻¹_{j,j})
- Ω⁻¹ = precision matrix (inverse covariance)
- Pairwise corr(AAPL, MSFT) = 0.85
- Partial corr(AAPL, MSFT | SPY, QQQ) = 0.15
- MVO weights: w ∝ Ω⁻¹α""",
            model_assumptions={
                "AAPL-MSFT correlation": "0.85",
                "AAPL-MSFT partial correlation": "0.15",
                "Controlling for": "SPY, QQQ (market and tech factors)",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="The 0.85 correlation is mostly driven by shared factor exposure (market and tech), not direct co-movement. After controlling for factors, only 0.15 remains — meaning AAPL and MSFT provide substantial independent (idiosyncratic) diversification. The precision matrix Ω⁻¹ automatically captures this: MVO weights w ∝ Ω⁻¹α use partial relationships, so both stocks can receive meaningful weight without over-concentrating in tech.",
        answer_options=[
            AnswerOption(id="A", text="0.85 correlation means AAPL and MSFT are redundant — drop one", is_correct=False),
            AnswerOption(id="B", text="The 0.85 correlation is mostly driven by shared factor exposure (market and tech), not direct co-movement. After controlling for factors, only 0.15 remains — meaning AAPL and MSFT provide substantial independent (idiosyncratic) diversification. The precision matrix Ω⁻¹ automatically captures this: MVO weights w ∝ Ω⁻¹α use partial relationships, so both stocks can receive meaningful weight without over-concentrating in tech.", is_correct=True),
            AnswerOption(id="C", text="Partial correlation is always lower than pairwise — this is uninformative", is_correct=False),
            AnswerOption(id="D", text="The pairwise correlation is the correct metric for portfolio construction", is_correct=False),
        ],
        explanation="Paleologo (2024, Insight 4.2) shows that MVO naturally operates in 'partial correlation space' because w ∝ Ω⁻¹α, and precision matrix entries represent partial correlations (scaled). High pairwise correlation might cause a naïve PM to treat AAPL/MSFT as substitutes. But 0.15 partial correlation reveals they carry mostly independent idiosyncratic risk. The precision matrix view shows that owning both improves risk-adjusted returns — their 0.85 correlation is 'hedged away' by the factor exposure in SPY/QQQ.",
        reasoning_steps=[
            "Pairwise correlation includes both factor and idiosyncratic components",
            "Partial correlation isolates the direct (idiosyncratic) relationship",
            "0.85 → 0.15 shows most co-movement is factor-driven",
            "MVO weights use Ω⁻¹, which reflects partial correlations",
            "Both stocks can have meaningful weight despite high pairwise corr",
        ],
        source="Paleologo (2024), Insight 4.2: Precision Matrix",
        tags=["partial-correlation", "precision-matrix", "diversification", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 8. Robust Optimization Penalty
    # =========================================================================
    problems.append(Problem(
        id="ee_robust_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""Three robust optimization approaches add different penalties to the MVO objective:

1. Uncertain Alpha: max w'α - γw'Ωw - τ²‖w‖²
2. Robust Alpha: max w'α - γw'Ωw - d‖w‖
3. Robust Covariance: max w'α - γw'Ωw - λd²‖w‖²

Which approach is most appropriate when you trust the covariance matrix but distrust alphas?""",
        context=FinancialContext(
            company_name="Robust Optimization Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Robust MVO penalties (Paleologo Table 5.1):
- Uncertain Alpha: L2 penalty τ²‖w‖² (like Ridge regression)
- Robust Alpha: L1/L2 penalty d‖w‖ (like constrained norm)
- Robust Covariance: scaled L2 d²‖w‖²
- All reduce sensitivity to estimation error
- τ, d, λ are uncertainty parameters""",
            model_assumptions={
                "Alpha confidence": "Low (noisy estimates)",
                "Covariance confidence": "High (long history, factor model)",
                "Universe": "100 stocks",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Uncertain Alpha (τ²‖w‖²) is most appropriate. It adds an L2 penalty that shrinks weights toward zero, equivalent to adding τ² to the diagonal of Ω. This is identical to Bayesian shrinkage of alphas toward zero under Gaussian uncertainty. It specifically targets alpha estimation error without modifying the trusted covariance. The L1 variant (Robust Alpha) would additionally promote sparsity, which may or may not be desired.",
        answer_options=[
            AnswerOption(id="A", text="Robust Covariance — always address the harder estimation problem first", is_correct=False),
            AnswerOption(id="B", text="Uncertain Alpha (τ²‖w‖²) is most appropriate. It adds an L2 penalty that shrinks weights toward zero, equivalent to adding τ² to the diagonal of Ω. This is identical to Bayesian shrinkage of alphas toward zero under Gaussian uncertainty. It specifically targets alpha estimation error without modifying the trusted covariance. The L1 variant (Robust Alpha) would additionally promote sparsity, which may or may not be desired.", is_correct=True),
            AnswerOption(id="C", text="Use all three simultaneously for maximum robustness", is_correct=False),
            AnswerOption(id="D", text="No penalty is needed — just use constraints instead", is_correct=False),
        ],
        explanation="Paleologo (2024, Table 5.1) catalogues five penalty approaches. The Uncertain Alpha penalty τ²‖w‖² is equivalent to replacing Ω with Ω + τ²I in the objective, which shrinks extreme weights. This directly addresses the 'Ω⁻¹ amplifies α errors' problem: larger τ reduces sensitivity to noisy alphas. It's the continuous analog of position-size constraints. The τ parameter can be calibrated from bootstrap or cross-validation.",
        reasoning_steps=[
            "The problem is alpha estimation error, not covariance error",
            "Uncertain Alpha: τ²‖w‖² = L2 regularization on weights",
            "Equivalent to Ω → Ω + τ²I: reduces inverse amplification",
            "This is Bayesian shrinkage of α toward zero",
            "Robust Covariance would modify the trusted Ω unnecessarily",
        ],
        source="Paleologo (2024), Table 5.1: Robust Optimization Penalties",
        tags=["robust-optimization", "regularization", "shrinkage", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 9. Deflated Sharpe and Multiple Testing
    # =========================================================================
    problems.append(Problem(
        id="ee_deflated_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A team tested 200 parameter combinations and selected the one with the highest backtest Sharpe of 2.1 over 5 years of daily data.

Using the expected maximum Sharpe under the null E[max] ≈ √(2·ln(N)) and the Sharpe SE formula, is this result significant?""",
        context=FinancialContext(
            company_name="Multiple Testing Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Deflated Sharpe (Bailey & Lopez de Prado, 2014):
- E[max(SR)] ≈ √(2·ln(N)) for N iid trials under null
- N = 200 parameter combos
- Observed max SR = 2.1 (annualized)
- T = 1,260 (5 years daily)
- SE(SR) ≈ √((1 + SR²/2) / T)
- Deflated SR = (observed - E[max]) / SE""",
            model_assumptions={
                "Parameters tested": "200",
                "Best Sharpe": "2.1",
                "Data period": "5 years daily",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="E[max] = √(2·ln(200)) = √(10.6) ≈ 3.26 annualized. Periodic SR = 2.1/√252 ≈ 0.132. E[max] periodic ≈ 3.26/√252 ≈ 0.205. SE ≈ √(1.009/1260) ≈ 0.0283. Deflated = (0.132 - 0.205)/0.0283 ≈ -2.58. The deflated Sharpe is deeply negative — the observed 2.1 is BELOW what you'd expect from pure noise with 200 trials. This is strong evidence of overfitting.",
        answer_options=[
            AnswerOption(id="A", text="Sharpe 2.1 is excellent — far above the usual 0.5 threshold", is_correct=False),
            AnswerOption(id="B", text="E[max] = √(2·ln(200)) = √(10.6) ≈ 3.26 annualized. Periodic SR = 2.1/√252 ≈ 0.132. E[max] periodic ≈ 3.26/√252 ≈ 0.205. SE ≈ √(1.009/1260) ≈ 0.0283. Deflated = (0.132 - 0.205)/0.0283 ≈ -2.58. The deflated Sharpe is deeply negative — the observed 2.1 is BELOW what you'd expect from pure noise with 200 trials. This is strong evidence of overfitting.", is_correct=True),
            AnswerOption(id="C", text="200 parameter combinations is a small number — no adjustment needed", is_correct=False),
            AnswerOption(id="D", text="The deflated Sharpe test only works for more than 1,000 trials", is_correct=False),
        ],
        explanation="Per Paleologo (2024, FAQ 4.2) and Bailey & Lopez de Prado (2014), when you test N strategies, the best Sharpe ratio has E[max] ≈ √(2·ln(N)) even if all strategies are pure noise. With N=200: E[max] ≈ 3.26 annualized — meaning a Sharpe of 2.1 is actually below what noise alone would produce! This reveals that either (1) the parameters aren't all independent (effective N < 200), or (2) the backtest has other flaws. Either way, the result doesn't survive multiple-testing adjustment.",
        reasoning_steps=[
            "Under null (all noise): E[max SR] = √(2·ln(N))",
            "With N=200: E[max] = √(2·ln(200)) ≈ 3.26",
            "Observed 2.1 < expected 3.26 from noise — suspicious",
            "Deflated SR = (observed - E[max]) / SE = negative",
            "Cannot reject null: performance is noise from parameter search",
        ],
        source="Paleologo (2024), FAQ 4.2; Bailey & Lopez de Prado (2014)",
        tags=["deflated-sharpe", "multiple-testing", "overfitting", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 10. Walk-Forward vs. Single Split
    # =========================================================================
    problems.append(Problem(
        id="ee_walkforward_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.HARD,
        question="""A backtest uses a single 70/30 train/test split and reports a Sharpe of 1.4 out-of-sample.

Why is a single split insufficient, and how does walk-forward validation address this?""",
        context=FinancialContext(
            company_name="Validation Method Analysis",
            ticker="N/A",
            sector="Quantitative",
            model_assumptions={
                "Split method": "Single 70/30 (train: 2015-2021, test: 2021-2024)",
                "OOS Sharpe": "1.4",
                "Market regime (train)": "Low rates, low vol",
                "Market regime (test)": "Rising rates, high vol",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="A single split has three problems: (1) Results depend on the specific split point — different cutoffs give different Sharpe ratios, (2) Only one regime is tested OOS — the 2021-2024 period may favor or penalize the strategy by chance, (3) No assessment of stability — you can't tell if performance is consistent or lucky. Walk-forward generates multiple train/test folds across regimes, providing a distribution of OOS results rather than a point estimate.",
        answer_options=[
            AnswerOption(id="A", text="A single 70/30 split is sufficient if the test period is long enough", is_correct=False),
            AnswerOption(id="B", text="A single split has three problems: (1) Results depend on the specific split point — different cutoffs give different Sharpe ratios, (2) Only one regime is tested OOS — the 2021-2024 period may favor or penalize the strategy by chance, (3) No assessment of stability — you can't tell if performance is consistent or lucky. Walk-forward generates multiple train/test folds across regimes, providing a distribution of OOS results rather than a point estimate.", is_correct=True),
            AnswerOption(id="C", text="Walk-forward just uses less data per fold — single split is more powerful", is_correct=False),
            AnswerOption(id="D", text="Any OOS test is valid as long as there's no look-ahead bias", is_correct=False),
        ],
        explanation="Paleologo (2024, Ch 6) emphasizes that backtesting rigor requires testing across multiple regimes. Walk-forward: train on [0,T], test on [T,T+s], slide forward, repeat. This gives K folds with K different market conditions. You can then assess: (1) Average OOS Sharpe across folds, (2) Sharpe decay (IS vs OOS) per fold, (3) What percentage of folds are profitable, (4) Whether performance depends on the regime. A strategy with Sharpe 1.4 in one period but -0.5 in another is less trustworthy than one with consistent 0.7.",
        reasoning_steps=[
            "Single split: one point estimate, no assessment of stability",
            "The specific split date determines which regime is OOS",
            "Walk-forward: multiple folds across different regimes",
            "Provides distribution of OOS results, not just one number",
            "Can assess consistency, Sharpe decay, and regime dependence",
        ],
        source="Paleologo (2024), Ch 6: Evaluating Alpha",
        tags=["walk-forward", "validation", "backtesting", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 11. Data Snooping vs Estimation Error Decomposition
    # =========================================================================
    problems.append(Problem(
        id="ee_decomp_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""The Rademacher bound decomposes backtest-to-reality gap into two terms:

    Gap = 2R̂ (data snooping) + 2√(log(2/δ)/T) (estimation error)

For a universe of 50 strategies tested over 5 years:
- 2R̂ ≈ 0.04 (data snooping)
- 2√(log(2/δ)/T) ≈ 0.076 (estimation error)

Which term dominates and what does this suggest about the research process?""",
        context=FinancialContext(
            company_name="Penalty Decomposition",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""Rademacher decomposition:
- Data snooping (2R̂): penalty for searching over strategies
- Estimation error: penalty for finite sample
- 50 strategies, T=1,260 days, δ=0.05""",
            model_assumptions={
                "Strategies tested": "50",
                "Data snooping penalty": "0.04",
                "Estimation error penalty": "0.076",
                "Total penalty": "0.116",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Estimation error (0.076) dominates data snooping (0.04). With only 50 strategies, the search isn't the main problem — 5 years simply isn't enough data for precise inference. This suggests: (1) Getting more data (longer history) would help more than testing fewer strategies, (2) The 50-strategy search is relatively modest, (3) More data improves both terms but estimation error drops faster (∝ 1/√T). If the team had tested 5,000 strategies, data snooping would dominate instead.",
        answer_options=[
            AnswerOption(id="A", text="Data snooping always dominates — focus on testing fewer strategies", is_correct=False),
            AnswerOption(id="B", text="Estimation error (0.076) dominates data snooping (0.04). With only 50 strategies, the search isn't the main problem — 5 years simply isn't enough data for precise inference. This suggests: (1) Getting more data (longer history) would help more than testing fewer strategies, (2) The 50-strategy search is relatively modest, (3) More data improves both terms but estimation error drops faster (∝ 1/√T). If the team had tested 5,000 strategies, data snooping would dominate instead.", is_correct=True),
            AnswerOption(id="C", text="Both terms are negligible — the backtest is reliable", is_correct=False),
            AnswerOption(id="D", text="The decomposition is theoretical — these terms cancel in practice", is_correct=False),
        ],
        explanation="Per Paleologo (2024, Ch 6.3), the two penalty terms respond differently to research choices. Data snooping (2R̂) grows with strategy-set complexity (roughly √(log N)). Estimation error (2√(log(2/δ)/T)) shrinks with more data. For a disciplined team testing 50 signals over 5 years, finite-sample noise is the binding constraint. Recommendation: extend the backtest period, use international data, or apply synthetic data augmentation. If they tested 5,000+ strategies, data snooping would dominate, suggesting they need pre-registration or out-of-sample holdout.",
        reasoning_steps=[
            "Compare penalties: 0.076 (estimation) > 0.04 (data snooping)",
            "Estimation error dominates with modest strategy count",
            "Data snooping penalty scales with strategy complexity",
            "Estimation error scales with 1/√T — more data helps most",
            "Advice: extend history or test on additional markets",
        ],
        source="Paleologo (2024), Ch 6.3: Rademacher Bound Decomposition",
        tags=["rademacher", "data-snooping", "estimation-error", "paleologo", "quant-concepts"],
    ))

    # =========================================================================
    # 12. Information Coefficient in Idiosyncratic Space
    # =========================================================================
    problems.append(Problem(
        id="ee_ic_idio_001",
        category=ProblemCategory.FORMULA_AUDIT,
        difficulty=Difficulty.EXPERT,
        question="""A researcher measures IC two ways:
1. Raw IC: cross-sectional correlation of signal with total returns = 0.08
2. Idiosyncratic IC: correlation of signal with factor-residual returns = 0.03

Which IC should be used for portfolio construction, and why is the raw IC misleading?""",
        context=FinancialContext(
            company_name="IC Measurement Analysis",
            ticker="N/A",
            sector="Quantitative",
            formula_context="""IC measurement (Paleologo Ch 4.4):
- Raw IC = corr(signal, total_return) = 0.08
- Idiosyncratic IC = corr(signal, residual_return) = 0.03
- Factor model: r = Bf + ε (total = factor + idio)
- Signal also correlates with factor returns (β_signal ≈ 0.3 on momentum)""",
            model_assumptions={
                "Raw IC": "0.08",
                "Idiosyncratic IC": "0.03",
                "Signal factor loading": "0.3 on momentum",
                "Momentum factor return": "Positive in sample period",
            }
        ),
        answer_type=AnswerType.MULTIPLE_CHOICE,
        correct_answer="Use idiosyncratic IC (0.03). The raw IC of 0.08 is inflated because the signal correlates with momentum factor returns — it's partly a momentum signal in disguise. The factor component is unreliable alpha: (1) it can be replicated cheaply via factor ETFs, (2) it will reverse when momentum reverses, (3) it doesn't represent unique information. True alpha is in the residual. The Fundamental Law should use idiosyncratic IC for honest IR estimation.",
        answer_options=[
            AnswerOption(id="A", text="Use raw IC of 0.08 — total return is what investors earn", is_correct=False),
            AnswerOption(id="B", text="Use idiosyncratic IC (0.03). The raw IC of 0.08 is inflated because the signal correlates with momentum factor returns — it's partly a momentum signal in disguise. The factor component is unreliable alpha: (1) it can be replicated cheaply via factor ETFs, (2) it will reverse when momentum reverses, (3) it doesn't represent unique information. True alpha is in the residual. The Fundamental Law should use idiosyncratic IC for honest IR estimation.", is_correct=True),
            AnswerOption(id="C", text="Average the two ICs for a balanced estimate", is_correct=False),
            AnswerOption(id="D", text="IC is IC — the distinction between raw and idiosyncratic is academic", is_correct=False),
        ],
        explanation="Paleologo (2024, Ch 4.4) defines the 'correct' IC as the cross-sectional, idiosyncratic-variance-weighted correlation between signal and residual returns. Raw IC conflates factor prediction (which is beta, not alpha) with idiosyncratic prediction (true alpha). A signal with 0.3 momentum loading will show high raw IC when momentum performs well, but this isn't stock-picking skill — it's factor timing disguised as selection. Stripping factors reveals the actual 0.03 idiosyncratic IC, which is the input for IR calculation.",
        reasoning_steps=[
            "Raw IC includes both factor and idiosyncratic prediction",
            "Signal has 0.3 momentum loading → captures factor return",
            "Factor prediction ≠ alpha (can be replicated cheaply)",
            "Idiosyncratic IC isolates genuine stock-picking signal",
            "Use idiosyncratic IC in Fundamental Law for honest IR",
        ],
        source="Paleologo (2024), Ch 4.4: Information Coefficient",
        tags=["ic", "idiosyncratic", "factor-model", "alpha", "paleologo", "quant-concepts"],
    ))

    return problems


if __name__ == "__main__":
    problems = generate_estimation_error_problems()
    print(f"Generated {len(problems)} estimation-error problems")

    from collections import Counter
    categories = Counter(p.category.value for p in problems)
    difficulties = Counter(p.difficulty.value for p in problems)

    print("\nCategory distribution:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print("\nDifficulty distribution:")
    for diff, count in sorted(difficulties.items()):
        print(f"  {diff}: {count}")

    print("\nProblem IDs:")
    for p in problems:
        print(f"  {p.id}: {p.difficulty.value} — {p.question[:60]}...")
