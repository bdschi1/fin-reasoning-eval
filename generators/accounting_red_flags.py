"""
Accounting Red Flags Problem Generator

Generates problems testing ability to:
- Identify accounting irregularities
- Spot aggressive revenue recognition
- Detect earnings management
- Recognize balance sheet manipulation
"""

import random
from typing import Optional

from problems import (
    Problem,
    ProblemCategory,
    Difficulty,
    AnswerType,
    FinancialContext,
    AnswerOption,
)
from .base import BaseGenerator


class AccountingRedFlagGenerator(BaseGenerator):
    """Generator for accounting red flag identification problems."""

    @property
    def category(self) -> ProblemCategory:
        return ProblemCategory.ACCOUNTING_RED_FLAG

    def generate_one(self, difficulty: Difficulty) -> Problem:
        """Generate a single accounting red flag problem."""
        problem_type = random.choice([
            'revenue_recognition',
            'receivables_quality',
            'inventory_buildup',
            'accrual_anomaly',
            'cash_vs_earnings',
            'off_balance_sheet',
            'related_party',
            'reserve_manipulation'
        ])

        generator_map = {
            'revenue_recognition': self._generate_revenue_recognition_problem,
            'receivables_quality': self._generate_receivables_problem,
            'inventory_buildup': self._generate_inventory_problem,
            'accrual_anomaly': self._generate_accrual_problem,
            'cash_vs_earnings': self._generate_cash_earnings_problem,
            'off_balance_sheet': self._generate_off_balance_sheet_problem,
            'related_party': self._generate_related_party_problem,
            'reserve_manipulation': self._generate_reserve_problem,
        }

        return generator_map[problem_type](difficulty)

    def _generate_revenue_recognition_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about suspicious revenue recognition patterns."""
        sector = random.choice(["Technology", "Healthcare", "Industrials"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            # Obvious hockey stick
            q1_rev = 200
            q2_rev = 210
            q3_rev = 220
            q4_rev = 380  # Suspicious spike
            correct = "Red flag - Q4 revenue spike (73% of H2) suggests aggressive recognition"
        elif difficulty == Difficulty.MEDIUM:
            # Moderate imbalance
            q1_rev = 220
            q2_rev = 235
            q3_rev = 245
            q4_rev = 320
            correct = "Warning - Q4 represents 31% of annual revenue, requires scrutiny"
        elif difficulty == Difficulty.HARD:
            # Subtle pattern
            q1_rev = 240
            q2_rev = 255
            q3_rev = 268
            q4_rev = 295
            correct = "Minor concern - sequential acceleration warrants review of deal terms"
        else:
            # Need context
            q1_rev = 230
            q2_rev = 245
            q3_rev = 260
            q4_rev = 305
            correct = "Context-dependent - seasonality normal for sector but verify customer concentration"

        annual_rev = q1_rev + q2_rev + q3_rev + q4_rev
        q4_pct = q4_rev / annual_rev * 100

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={
                "Q1": q1_rev,
                "Q2": q2_rev,
                "Q3": q3_rev,
                "Q4": q4_rev,
                "FY Total": annual_rev
            },
            model_assumptions={
                "Q4 as % of Annual": f"{q4_pct:.1f}%",
                "Q4 vs Q3 Growth": f"{(q4_rev/q3_rev-1)*100:.1f}%"
            }
        )

        distractors = [
            "Normal - Q4 is always strongest quarter",
            "No concern - revenue growth is positive",
            "Valid - matches industry pattern exactly"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} reported quarterly revenue (in $M): Q1: {q1_rev}, Q2: {q2_rev}, "
                     f"Q3: {q3_rev}, Q4: {q4_rev}. Q4 represents {q4_pct:.1f}% of annual revenue. "
                     f"What is the appropriate assessment of this revenue pattern?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Revenue concentration in Q4 (>{30}% of annual) can indicate aggressive "
                       f"recognition timing, channel stuffing, or side agreements. "
                       f"Q4 vs Q3 growth of {(q4_rev/q3_rev-1)*100:.1f}% requires investigation.",
            common_mistakes=[
                "Accepting seasonality without verification",
                "Ignoring sequential acceleration",
                "Not considering industry norms"
            ],
            tags=["accounting", "revenue-recognition", "red-flag"]
        )

    def _generate_receivables_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about receivables quality."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        rev_growth = round(random.uniform(8, 15), 1)
        base_dso = 45

        if difficulty == Difficulty.EASY:
            # Obvious red flag
            ar_growth = rev_growth + 30
            new_dso = base_dso + 25
            correct = f"Red flag - AR growing {ar_growth:.0f}% vs revenue {rev_growth}%, DSO up {new_dso - base_dso} days"
        elif difficulty == Difficulty.MEDIUM:
            ar_growth = rev_growth + 15
            new_dso = base_dso + 12
            correct = f"Warning - AR growth ({ar_growth:.0f}%) exceeds revenue ({rev_growth}%)"
        elif difficulty == Difficulty.HARD:
            ar_growth = rev_growth + 5
            new_dso = base_dso + 5
            correct = f"Monitor - modest DSO increase ({new_dso - base_dso} days) may indicate customer mix shift"
        else:
            ar_growth = rev_growth + 8
            new_dso = base_dso + 8
            correct = f"Investigate - {new_dso - base_dso} day DSO increase could reflect new customer terms or collection issues"

        base_rev = round(random.uniform(400, 800), 0)
        new_rev = round(base_rev * (1 + rev_growth / 100), 0)
        base_ar = round(base_rev * base_dso / 365, 0)
        new_ar = round(new_rev * new_dso / 365, 0)

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"Prior Year": base_rev, "Current Year": new_rev},
            model_assumptions={
                "Revenue Growth": f"{rev_growth}%",
                "AR Growth": f"{ar_growth:.0f}%",
                "Prior DSO": f"{base_dso} days",
                "Current DSO": f"{new_dso} days",
                "Prior AR": f"${base_ar}M",
                "Current AR": f"${new_ar}M"
            }
        )

        distractors = [
            "Normal - AR should grow with revenue",
            "No concern - DSO is within industry range",
            "Positive - indicates strong sales pipeline"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company}'s revenue grew {rev_growth}% year-over-year while accounts receivable "
                     f"increased {ar_growth:.0f}%. Days Sales Outstanding (DSO) went from {base_dso} to {new_dso} days. "
                     f"What does this pattern suggest?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"AR growing faster than revenue typically signals collection problems, "
                       f"aggressive revenue recognition, or customer quality deterioration. "
                       f"DSO increase from {base_dso} to {new_dso} days warrants investigation.",
            tags=["accounting", "receivables", "dso", "red-flag"]
        )

    def _generate_inventory_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about inventory buildup signals."""
        sector = random.choice(["Consumer Discretionary", "Industrials", "Technology"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        cogs_growth = round(random.uniform(5, 12), 1)

        if difficulty == Difficulty.EASY:
            inv_growth = cogs_growth + 35
            dio_change = 30
            correct = f"Red flag - inventory growth ({inv_growth:.0f}%) vastly exceeds COGS ({cogs_growth}%)"
        elif difficulty == Difficulty.MEDIUM:
            inv_growth = cogs_growth + 18
            dio_change = 15
            correct = f"Warning - {dio_change} day DIO increase suggests demand softness or excess build"
        elif difficulty == Difficulty.HARD:
            inv_growth = cogs_growth + 8
            dio_change = 8
            correct = f"Monitor - modest inventory build may reflect strategic stocking or new SKUs"
        else:
            inv_growth = cogs_growth + 12
            dio_change = 12
            correct = f"Context needed - {inv_growth:.0f}% inventory growth requires segment analysis"

        base_cogs = round(random.uniform(300, 600), 0)
        new_cogs = round(base_cogs * (1 + cogs_growth / 100), 0)
        base_dio = 60
        new_dio = base_dio + dio_change

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            model_assumptions={
                "COGS Growth": f"{cogs_growth}%",
                "Inventory Growth": f"{inv_growth:.0f}%",
                "Prior DIO": f"{base_dio} days",
                "Current DIO": f"{new_dio} days"
            }
        )

        distractors = [
            "Positive - company preparing for growth",
            "No concern - inventory is an asset",
            "Normal - follows industry trend"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company}'s cost of goods sold grew {cogs_growth}% while inventory increased {inv_growth:.0f}%. "
                     f"Days Inventory Outstanding (DIO) changed from {base_dio} to {new_dio} days. "
                     f"What does this signal about the business?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Inventory growing faster than COGS often precedes write-offs or indicates "
                       f"demand weakness. The {dio_change} day DIO increase suggests potential obsolescence risk.",
            tags=["accounting", "inventory", "dio", "red-flag"]
        )

    def _generate_accrual_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about accrual anomalies."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        net_income = round(random.uniform(100, 300), 0)

        if difficulty == Difficulty.EASY:
            # Large accrual
            cfo = round(net_income * 0.4, 0)
            accrual_ratio = (net_income - cfo) / net_income
            correct = f"Red flag - {accrual_ratio*100:.0f}% of earnings are accruals, cash conversion weak"
        elif difficulty == Difficulty.MEDIUM:
            cfo = round(net_income * 0.7, 0)
            accrual_ratio = (net_income - cfo) / net_income
            correct = f"Warning - {accrual_ratio*100:.0f}% accrual ratio warrants working capital review"
        elif difficulty == Difficulty.HARD:
            cfo = round(net_income * 0.9, 0)
            accrual_ratio = (net_income - cfo) / net_income
            correct = f"Acceptable - {accrual_ratio*100:.0f}% accrual ratio within normal range"
        else:
            cfo = round(net_income * 1.15, 0)
            accrual_ratio = (net_income - cfo) / net_income
            correct = f"Positive - CFO exceeds net income, negative accruals indicate conservative accounting"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            net_income={"Current Year": net_income},
            free_cash_flow={"CFO": cfo},
            model_assumptions={
                "Net Income": f"${net_income}M",
                "Cash from Operations": f"${cfo}M",
                "Accrual Ratio": f"{accrual_ratio*100:.1f}%"
            }
        )

        distractors = [
            "Normal - accrual accounting is standard",
            "No concern - both numbers are positive",
            "Valid - matches peer companies"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} reported net income of ${net_income}M and cash from operations of ${cfo}M. "
                     f"The accrual ratio (NI - CFO)/NI is {accrual_ratio*100:.1f}%. "
                     f"What does this indicate about earnings quality?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"High accrual ratios (>30%) often precede earnings disappointments. "
                       f"CFO-to-NI ratio of {cfo/net_income:.2f}x indicates "
                       f"{'strong' if cfo > net_income else 'weak'} cash conversion.",
            tags=["accounting", "accruals", "earnings-quality", "red-flag"]
        )

    def _generate_cash_earnings_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about cash flow vs earnings divergence."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        eps_growth_1y = round(random.uniform(12, 25), 1)

        if difficulty == Difficulty.EASY:
            fcf_growth_1y = -15  # FCF declining while EPS growing
            correct = f"Major red flag - EPS +{eps_growth_1y}% while FCF -{abs(fcf_growth_1y)}%"
        elif difficulty == Difficulty.MEDIUM:
            fcf_growth_1y = eps_growth_1y - 20
            correct = f"Warning - FCF growth ({fcf_growth_1y:+.0f}%) lagging EPS ({eps_growth_1y:+.0f}%)"
        elif difficulty == Difficulty.HARD:
            fcf_growth_1y = eps_growth_1y - 8
            correct = f"Monitor - modest FCF/EPS divergence may reflect timing or investment"
        else:
            fcf_growth_1y = eps_growth_1y + 5
            correct = f"Healthy - FCF growth ({fcf_growth_1y:+.0f}%) exceeds EPS ({eps_growth_1y:+.0f}%)"

        base_eps = round(random.uniform(2.0, 4.0), 2)
        current_eps = round(base_eps * (1 + eps_growth_1y / 100), 2)
        base_fcf_per_share = round(base_eps * random.uniform(0.8, 1.1), 2)
        current_fcf_per_share = round(base_fcf_per_share * (1 + fcf_growth_1y / 100), 2)

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            eps={"Prior Year": base_eps, "Current Year": current_eps},
            model_assumptions={
                "EPS Growth": f"{eps_growth_1y:+.1f}%",
                "FCF/Share Growth": f"{fcf_growth_1y:+.1f}%",
                "Prior FCF/Share": f"${base_fcf_per_share:.2f}",
                "Current FCF/Share": f"${current_fcf_per_share:.2f}"
            }
        )

        distractors = [
            "Normal - EPS and FCF often diverge",
            "Positive - EPS growth is what matters",
            "Valid - standard growth pattern"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company}'s EPS grew {eps_growth_1y:+.1f}% year-over-year while free cash flow per share "
                     f"changed by {fcf_growth_1y:+.1f}%. Prior FCF/share was ${base_fcf_per_share:.2f}, "
                     f"now ${current_fcf_per_share:.2f}. What does this divergence indicate?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Sustained EPS-FCF divergence often indicates non-cash earnings (accruals) "
                       f"or aggressive accounting. FCF growing faster than EPS is generally positive.",
            tags=["accounting", "cash-flow", "eps", "divergence", "red-flag"]
        )

    def _generate_off_balance_sheet_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about off-balance sheet items."""
        sector = random.choice(["Consumer Discretionary", "Industrials", "Real Estate"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        reported_debt = round(random.uniform(200, 500), 0)
        equity = round(random.uniform(300, 600), 0)
        reported_leverage = reported_debt / equity

        if difficulty == Difficulty.EASY:
            operating_leases = round(reported_debt * 0.8, 0)
            adj_leverage = (reported_debt + operating_leases) / equity
            correct = f"Material understatement - adjusted leverage {adj_leverage:.1f}x vs reported {reported_leverage:.1f}x"
        elif difficulty == Difficulty.MEDIUM:
            operating_leases = round(reported_debt * 0.4, 0)
            adj_leverage = (reported_debt + operating_leases) / equity
            correct = f"Significant - operating leases add {operating_leases}M, leverage rises to {adj_leverage:.1f}x"
        elif difficulty == Difficulty.HARD:
            operating_leases = round(reported_debt * 0.15, 0)
            adj_leverage = (reported_debt + operating_leases) / equity
            correct = f"Modest impact - lease adjustment increases leverage by {(adj_leverage-reported_leverage):.2f}x"
        else:
            operating_leases = round(reported_debt * 0.25, 0)
            purchase_commitments = round(reported_debt * 0.1, 0)
            adj_leverage = (reported_debt + operating_leases + purchase_commitments) / equity
            correct = f"Multiple items - leases ${operating_leases}M + commitments ${purchase_commitments}M raise leverage to {adj_leverage:.1f}x"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            total_debt={"Reported": reported_debt},
            equity={"Current": equity},
            model_assumptions={
                "Reported Debt/Equity": f"{reported_leverage:.2f}x",
                "Operating Lease Obligations": f"${operating_leases}M",
                "Adjusted Debt/Equity": f"{adj_leverage:.2f}x"
            }
        )

        distractors = [
            "No impact - leases are not debt",
            "Positive - shows conservative accounting",
            "Invalid - off-balance sheet items don't matter"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} reports debt of ${reported_debt}M and equity of ${equity}M "
                     f"(debt/equity: {reported_leverage:.2f}x). Footnotes disclose ${operating_leases}M in "
                     f"operating lease obligations. How does this affect the true leverage picture?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Operating leases represent debt-like obligations that should be capitalized. "
                       f"Adjusted leverage of {adj_leverage:.1f}x vs reported {reported_leverage:.1f}x "
                       f"shows the true debt burden.",
            tags=["accounting", "off-balance-sheet", "leverage", "red-flag"]
        )

    def _generate_related_party_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about related party transactions."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        revenue = round(random.uniform(500, 1000), 0)

        if difficulty == Difficulty.EASY:
            rpt_pct = 35
            correct = f"Major red flag - {rpt_pct}% of revenue from related parties raises independence concerns"
        elif difficulty == Difficulty.MEDIUM:
            rpt_pct = 18
            correct = f"Significant concern - {rpt_pct}% related party revenue requires scrutiny of terms"
        elif difficulty == Difficulty.HARD:
            rpt_pct = 8
            correct = f"Monitor - {rpt_pct}% RPT level manageable but verify arm's length pricing"
        else:
            rpt_pct = 12
            correct = f"Context-dependent - {rpt_pct}% RPT common in certain structures, verify governance"

        rpt_revenue = round(revenue * rpt_pct / 100, 0)

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"Total": revenue, "Related Party": rpt_revenue},
            model_assumptions={
                "Total Revenue": f"${revenue}M",
                "Related Party Revenue": f"${rpt_revenue}M",
                "RPT as % of Revenue": f"{rpt_pct}%"
            }
        )

        distractors = [
            "Normal - all companies have related party transactions",
            "Positive - shows strong business relationships",
            "No concern - properly disclosed"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} disclosed ${rpt_revenue}M in related party revenue out of total revenue "
                     f"of ${revenue}M ({rpt_pct}%). The related parties are entities controlled by "
                     f"board members. What is the appropriate assessment?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Related party transactions above 10-15% of revenue warrant increased scrutiny. "
                       f"Key concerns: pricing fairness, arm's length terms, governance independence.",
            tags=["accounting", "related-party", "governance", "red-flag"]
        )

    def _generate_reserve_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about reserve manipulation."""
        sector = random.choice(["Financials", "Healthcare", "Consumer Discretionary"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        revenue = round(random.uniform(600, 1200), 0)

        if difficulty == Difficulty.EASY:
            prior_reserve = 5.0
            current_reserve = 2.5
            correct = f"Red flag - reserve cut from {prior_reserve}% to {current_reserve}% added {(prior_reserve-current_reserve)*revenue/100:.0f}M to earnings"
        elif difficulty == Difficulty.MEDIUM:
            prior_reserve = 4.5
            current_reserve = 3.2
            correct = f"Warning - {prior_reserve-current_reserve:.1f}pp reserve reduction boosted earnings"
        elif difficulty == Difficulty.HARD:
            prior_reserve = 4.0
            current_reserve = 3.5
            correct = f"Minor concern - modest reserve release may be justified by improved collections"
        else:
            prior_reserve = 4.2
            current_reserve = 4.0
            correct = f"Requires analysis - small reserve change but timing with earnings target is suspect"

        earnings_boost = (prior_reserve - current_reserve) * revenue / 100
        net_income = round(random.uniform(50, 120), 0)
        boost_pct = earnings_boost / net_income * 100

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"Current Year": revenue},
            net_income={"Current Year": net_income},
            model_assumptions={
                "Prior Year Bad Debt Reserve": f"{prior_reserve}%",
                "Current Year Bad Debt Reserve": f"{current_reserve}%",
                "Earnings Impact": f"${earnings_boost:.0f}M ({boost_pct:.0f}% of NI)"
            }
        )

        distractors = [
            "Positive - reflects better credit quality",
            "Normal - reserves fluctuate annually",
            "No concern - auditors approved"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} reduced its bad debt reserve from {prior_reserve}% to {current_reserve}% of revenue. "
                     f"With revenue of ${revenue}M, this added ${earnings_boost:.0f}M to pre-tax earnings "
                     f"({boost_pct:.0f}% of net income). How should this be viewed?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Reserve releases directly boost earnings and can be used to meet targets. "
                       f"The {prior_reserve-current_reserve:.1f}pp reduction adding ${earnings_boost:.0f}M "
                       f"({boost_pct:.0f}% of NI) warrants scrutiny of the underlying justification.",
            tags=["accounting", "reserves", "earnings-management", "red-flag"]
        )
