"""
DCF Sanity Check Problem Generator

Generates problems testing ability to:
- Identify unreasonable DCF assumptions
- Validate terminal value calculations
- Check discount rate appropriateness
- Spot projection inconsistencies
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


class DCFSanityGenerator(BaseGenerator):
    """Generator for DCF sanity check problems."""

    @property
    def category(self) -> ProblemCategory:
        return ProblemCategory.DCF_SANITY

    def generate_one(self, difficulty: Difficulty) -> Problem:
        """Generate a single DCF sanity check problem."""
        problem_type = random.choice([
            'terminal_growth_check',
            'wacc_validation',
            'terminal_value_proportion',
            'projection_growth_check',
            'implied_multiple',
            'sensitivity_analysis',
            'fcf_growth_consistency'
        ])

        generator_map = {
            'terminal_growth_check': self._generate_terminal_growth_problem,
            'wacc_validation': self._generate_wacc_problem,
            'terminal_value_proportion': self._generate_tv_proportion_problem,
            'projection_growth_check': self._generate_projection_growth_problem,
            'implied_multiple': self._generate_implied_multiple_problem,
            'sensitivity_analysis': self._generate_sensitivity_problem,
            'fcf_growth_consistency': self._generate_fcf_consistency_problem,
        }

        return generator_map[problem_type](difficulty)

    def _generate_terminal_growth_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about terminal growth rate reasonableness."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate terminal growth rate based on difficulty
        if difficulty == Difficulty.EASY:
            # Obviously wrong terminal growth
            tgr = random.choice([5.0, 6.0, -1.0, 7.5])
            if tgr > 4:
                issue = "Terminal growth rate exceeds long-term GDP growth"
                correct = f"Invalid - {tgr}% exceeds sustainable growth (typically 2-3%)"
            else:
                issue = "Negative terminal growth is rarely appropriate"
                correct = f"Invalid - negative terminal growth of {tgr}%"
        elif difficulty == Difficulty.MEDIUM:
            tgr = random.choice([3.5, 4.0, 1.0])
            if tgr > 3.0:
                correct = f"Questionable - {tgr}% is at the high end of sustainable growth"
            else:
                correct = f"Reasonable - {tgr}% is conservative"
        elif difficulty == Difficulty.HARD:
            # Borderline cases
            tgr = random.choice([2.8, 3.2, 2.5])
            correct = f"Borderline - {tgr}% is {'slightly aggressive' if tgr > 3 else 'within range'}"
        else:
            # Context-dependent
            tgr = 3.0
            inflation = 2.5
            correct = f"Context-dependent - {tgr}% vs {inflation}% inflation implies {tgr - inflation}% real growth perpetuity"

        wacc = round(random.uniform(8, 12), 1)

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            terminal_growth=tgr,
            wacc=wacc,
            model_assumptions={
                "Terminal Growth Rate": f"{tgr}%",
                "WACC": f"{wacc}%",
                "Long-term GDP Growth": "2.5%",
                "Long-term Inflation": "2.0%"
            }
        )

        distractors = [
            f"Valid - {tgr}% is standard for {sector}",
            f"Invalid - growth must equal WACC",
            f"Valid - matches historical growth rate"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"A DCF model for {company} uses a terminal growth rate of {tgr}% "
                     f"with a WACC of {wacc}%. Long-term GDP growth is 2.5% and inflation is 2.0%. "
                     f"Is this terminal growth rate reasonable?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Terminal growth rate should not exceed long-term GDP growth (2-3%) as it implies "
                       f"the company will eventually become larger than the entire economy. "
                       f"A {tgr}% terminal growth rate is {issue if difficulty == Difficulty.EASY else 'borderline'}.",
            reasoning_steps=[
                f"Identify terminal growth rate: {tgr}%",
                f"Compare to long-term GDP growth: 2.5%",
                f"Compare to inflation: 2.0%",
                f"Implied real growth: {tgr - 2.0}%",
                f"Assessment: {correct}"
            ],
            common_mistakes=[
                "Accepting high terminal growth for 'growth companies'",
                "Ignoring the perpetuity implication",
                "Confusing nominal vs real growth"
            ],
            tags=["dcf", "terminal-growth", "sanity-check"]
        )

    def _generate_wacc_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about WACC reasonableness."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Sector-appropriate WACCs
        sector_wacc = {
            "Technology": 10.0,
            "Healthcare": 9.5,
            "Financials": 8.5,
            "Consumer Discretionary": 9.0,
            "Consumer Staples": 7.5,
            "Energy": 10.5,
            "Materials": 9.5,
            "Industrials": 8.5,
            "Real Estate": 7.0,
            "Utilities": 6.5,
            "Communication Services": 8.5
        }

        base_wacc = sector_wacc.get(sector, 9.0)

        if difficulty == Difficulty.EASY:
            # Obviously wrong
            wacc = random.choice([3.0, 4.0, 18.0, 20.0])
            if wacc < 5:
                correct = f"Invalid - {wacc}% is below risk-free rate"
            else:
                correct = f"Invalid - {wacc}% is unrealistically high"
        elif difficulty == Difficulty.MEDIUM:
            # Moderately off
            wacc = round(base_wacc + random.choice([-3.0, 4.0]), 1)
            correct = f"Questionable - {wacc}% is {'low' if wacc < base_wacc else 'high'} for {sector}"
        elif difficulty == Difficulty.HARD:
            # Slightly off
            wacc = round(base_wacc + random.choice([-1.5, 2.0]), 1)
            correct = f"Borderline - {wacc}% may be {'aggressive' if wacc < base_wacc else 'conservative'}"
        else:
            # Need to check components
            wacc = base_wacc
            rf = 4.5
            beta = 1.2
            erp = 5.0
            implied_cost_equity = rf + beta * erp
            correct = f"Valid components - Rf {rf}% + β{beta} × ERP {erp}% = {implied_cost_equity}% cost of equity"

        rf_rate = 4.5
        market_premium = 5.5

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            wacc=wacc,
            model_assumptions={
                "WACC": f"{wacc}%",
                "Risk-Free Rate": f"{rf_rate}%",
                "Market Risk Premium": f"{market_premium}%",
                "Sector": sector,
                "Typical Sector WACC": f"{base_wacc}%"
            }
        )

        distractors = [
            f"Valid - {wacc}% is standard",
            f"Invalid - should equal terminal growth",
            f"Valid - matches company beta"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"A DCF model for {company} ({sector} sector) uses a WACC of {wacc}%. "
                     f"The risk-free rate is {rf_rate}% and the market risk premium is {market_premium}%. "
                     f"Is this WACC reasonable?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"WACC should reflect the company's weighted cost of capital, typically "
                       f"ranging from 6-12% for most companies. {sector} typically has WACC around {base_wacc}%.",
            tags=["dcf", "wacc", "sanity-check", "discount-rate"]
        )

    def _generate_tv_proportion_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about terminal value as proportion of total value."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate PV of FCF and Terminal Value
        pv_fcf = round(random.uniform(300, 600), 0)

        if difficulty == Difficulty.EASY:
            # Obviously problematic proportion
            tv_pct = random.choice([92, 95, 35])
            if tv_pct > 90:
                correct = f"Red flag - Terminal value is {tv_pct}% of total, projection period adds minimal value"
            else:
                correct = f"Unusual - Terminal value only {tv_pct}% suggests aggressive near-term FCF"
        elif difficulty == Difficulty.MEDIUM:
            tv_pct = random.choice([82, 58])
            correct = f"{'High' if tv_pct > 80 else 'Low'} but within range - {tv_pct}% terminal value"
        elif difficulty == Difficulty.HARD:
            tv_pct = random.choice([75, 68])
            correct = f"Reasonable - {tv_pct}% terminal value is typical"
        else:
            tv_pct = 78
            correct = f"Context-dependent - {tv_pct}% TV for {sector} requires assumption review"

        pv_tv = round(pv_fcf * tv_pct / (100 - tv_pct), 0)
        total_value = pv_fcf + pv_tv

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            model_assumptions={
                "PV of Explicit FCF": f"${pv_fcf}M",
                "PV of Terminal Value": f"${pv_tv}M",
                "Total Enterprise Value": f"${total_value}M",
                "TV as % of Total": f"{tv_pct}%",
                "Projection Period": "5 years"
            }
        )

        distractors = [
            f"Valid - terminal value should be 100% of value",
            f"Invalid - terminal value should be under 50%",
            f"Valid - standard {tv_pct}% allocation"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"A DCF model for {company} shows PV of explicit period FCF of ${pv_fcf}M "
                     f"and PV of terminal value of ${pv_tv}M, for total EV of ${total_value}M. "
                     f"Terminal value represents {tv_pct}% of total value. Is this reasonable?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Terminal value typically represents 60-80% of total DCF value. "
                       f"Values above 85% suggest over-reliance on terminal assumptions; "
                       f"values below 50% suggest aggressive near-term projections.",
            tags=["dcf", "terminal-value", "sanity-check"]
        )

    def _generate_projection_growth_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about projection period growth rates."""
        sector = random.choice(["Technology", "Healthcare", "Consumer Discretionary"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate FCF projections
        base_fcf = round(random.uniform(80, 150), 0)

        if difficulty == Difficulty.EASY:
            # Obviously unrealistic growth
            growth_rate = random.choice([35, 40, 50])
            correct = f"Unrealistic - {growth_rate}% annual FCF growth is not sustainable"
        elif difficulty == Difficulty.MEDIUM:
            growth_rate = random.choice([22, 25])
            correct = f"Aggressive - {growth_rate}% growth requires strong justification"
        elif difficulty == Difficulty.HARD:
            growth_rate = random.choice([15, 18])
            correct = f"Plausible but aggressive - {growth_rate}% growth for 5 years"
        else:
            growth_rate = 20
            correct = f"Requires context - {growth_rate}% may be valid for high-growth tech with clear drivers"

        fcf_projections = {}
        current = base_fcf
        for i in range(5):
            year = 2024 + i
            fcf_projections[f"{year}E"] = round(current, 0)
            current = current * (1 + growth_rate / 100)

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            free_cash_flow=fcf_projections,
            model_assumptions={
                "Implied FCF CAGR": f"{growth_rate}%",
                "Starting FCF (2024E)": f"${base_fcf}M",
                "Ending FCF (2028E)": f"${fcf_projections['2028E']}M"
            }
        )

        distractors = [
            f"Conservative - {growth_rate}% is below market growth",
            f"Valid - standard projection assumption",
            f"Invalid - FCF should decline in projections"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"A DCF model for {company} projects FCF growing from ${base_fcf}M in 2024 to "
                     f"${fcf_projections['2028E']}M in 2028, implying a {growth_rate}% CAGR. "
                     f"Is this projection reasonable?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Sustainable FCF growth typically ranges from 5-15% for mature companies, "
                       f"up to 20-25% for high-growth companies. {growth_rate}% is "
                       f"{'clearly unsustainable' if growth_rate > 30 else 'aggressive'}.",
            tags=["dcf", "projections", "growth-rate", "sanity-check"]
        )

    def _generate_implied_multiple_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about DCF implied multiples."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Sector typical multiples
        sector_ev_ebitda = {
            "Technology": 15.0,
            "Healthcare": 12.0,
            "Financials": 8.0,
            "Consumer Discretionary": 10.0,
            "Consumer Staples": 12.0,
            "Energy": 6.0,
            "Materials": 7.0,
            "Industrials": 9.0,
            "Real Estate": 15.0,
            "Utilities": 10.0,
            "Communication Services": 8.0
        }

        base_multiple = sector_ev_ebitda.get(sector, 10.0)
        ebitda = round(random.uniform(200, 500), 0)

        if difficulty == Difficulty.EASY:
            # Way off
            implied_multiple = random.choice([35, 45, 2.5])
            if implied_multiple > 30:
                correct = f"Too high - {implied_multiple}x EV/EBITDA far exceeds sector ({base_multiple}x)"
            else:
                correct = f"Too low - {implied_multiple}x suggests modeling error"
        elif difficulty == Difficulty.MEDIUM:
            implied_multiple = round(base_multiple * random.choice([1.5, 0.6]), 1)
            correct = f"{'Premium' if implied_multiple > base_multiple else 'Discount'} to sector - {implied_multiple}x vs {base_multiple}x"
        elif difficulty == Difficulty.HARD:
            implied_multiple = round(base_multiple * random.choice([1.2, 0.85]), 1)
            correct = f"Within range - {implied_multiple}x is close to sector average of {base_multiple}x"
        else:
            implied_multiple = base_multiple
            peer_low = base_multiple - 2
            peer_high = base_multiple + 3
            correct = f"Reasonable - {implied_multiple}x aligns with peer range of {peer_low}x to {peer_high}x"

        ev = round(ebitda * implied_multiple, 0)

        # Include peer range in context for expert problems so the answer
        # only references information available in the question
        assumptions = {
            "DCF-Implied EV": f"${ev}M",
            "2024E EBITDA": f"${ebitda}M",
            "Implied EV/EBITDA": f"{implied_multiple}x",
            "Sector Average EV/EBITDA": f"{base_multiple}x",
        }
        if difficulty == Difficulty.EXPERT:
            assumptions["Peer Range EV/EBITDA"] = f"{peer_low}x to {peer_high}x"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            ev_ebitda=implied_multiple,
            ebitda={"2024E": ebitda},
            model_assumptions=assumptions,
        )

        distractors = [
            f"Valid - DCF should not match multiples",
            f"Invalid - should match P/E ratio instead",
            f"Too low - {implied_multiple}x suggests conservative assumptions"
        ]

        # Expert question includes peer range; others just use sector average
        if difficulty == Difficulty.EXPERT:
            question_text = (
                f"A DCF model for {company} yields an enterprise value of ${ev}M. "
                f"With 2024E EBITDA of ${ebitda}M, this implies an EV/EBITDA multiple of {implied_multiple}x. "
                f"The {sector} sector average is {base_multiple}x with a peer range of {peer_low}x to {peer_high}x. "
                f"Is this reasonable?"
            )
        else:
            question_text = (
                f"A DCF model for {company} yields an enterprise value of ${ev}M. "
                f"With 2024E EBITDA of ${ebitda}M, this implies an EV/EBITDA multiple of {implied_multiple}x. "
                f"The {sector} sector average is {base_multiple}x. Is this reasonable?"
            )

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=question_text,
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"DCF-implied multiples should be cross-checked against trading comparables. "
                       f"Large deviations (>50%) from sector averages warrant scrutiny.",
            tags=["dcf", "implied-multiple", "sanity-check", "valuation"]
        )

    def _generate_sensitivity_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about DCF sensitivity analysis."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        base_value = round(random.uniform(1000, 2000), 0)
        wacc = 10.0
        tgr = 2.5

        if difficulty == Difficulty.EASY:
            # Clear asymmetry issue
            low_wacc_value = round(base_value * 1.8, 0)
            high_wacc_value = round(base_value * 0.6, 0)
            correct = f"Extreme sensitivity - 2% WACC change causes {((low_wacc_value/base_value)-1)*100:.0f}% value swing"
        elif difficulty == Difficulty.MEDIUM:
            low_wacc_value = round(base_value * 1.3, 0)
            high_wacc_value = round(base_value * 0.75, 0)
            correct = f"Moderate sensitivity - reasonable for terminal-value-heavy DCF"
        elif difficulty == Difficulty.HARD:
            low_wacc_value = round(base_value * 1.15, 0)
            high_wacc_value = round(base_value * 0.88, 0)
            correct = f"Low sensitivity - may indicate near-term FCF dominates value"
        else:
            low_wacc_value = round(base_value * 1.25, 0)
            high_wacc_value = round(base_value * 0.78, 0)
            correct = f"Asymmetric - downside (-{(1-high_wacc_value/base_value)*100:.0f}%) exceeds upside (+{(low_wacc_value/base_value-1)*100:.0f}%)"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            wacc=wacc,
            terminal_growth=tgr,
            model_assumptions={
                "Base Case Value": f"${base_value}M",
                "Base WACC": f"{wacc}%",
                "Value at WACC -1%": f"${low_wacc_value}M",
                "Value at WACC +1%": f"${high_wacc_value}M",
                "Terminal Growth": f"{tgr}%"
            }
        )

        distractors = [
            "Normal - all DCF models have high sensitivity",
            "Invalid - value should not change with WACC",
            "Valid - sensitivity matches theory perfectly"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"A DCF model shows base case value of ${base_value}M at {wacc}% WACC. "
                     f"Sensitivity analysis shows value of ${low_wacc_value}M at {wacc-1}% WACC "
                     f"and ${high_wacc_value}M at {wacc+1}% WACC. What does this indicate?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Sensitivity to WACC reflects terminal value proportion and duration. "
                       f"Upside: +{(low_wacc_value/base_value-1)*100:.0f}%, Downside: -{(1-high_wacc_value/base_value)*100:.0f}%",
            tags=["dcf", "sensitivity", "sanity-check"]
        )

    def _generate_fcf_consistency_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about FCF projection consistency."""
        sector = random.choice(["Technology", "Healthcare", "Industrials"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate inconsistent projections
        revenue_growth = 15
        margin_trend = 2  # percentage points per year

        base_rev = round(random.uniform(500, 1000), 0)
        base_margin = 0.15

        if difficulty == Difficulty.EASY:
            # Clear inconsistency
            fcf_growth = 35  # FCF growing much faster than revenue
            correct = f"Inconsistent - FCF growth ({fcf_growth}%) far exceeds revenue growth ({revenue_growth}%)"
        elif difficulty == Difficulty.MEDIUM:
            fcf_growth = revenue_growth + 8  # Margin expansion explains some
            correct = f"Partially explained - {fcf_growth}% FCF growth vs {revenue_growth}% revenue from margin expansion"
        elif difficulty == Difficulty.HARD:
            fcf_growth = revenue_growth + margin_trend * 100 / base_margin  # Roughly consistent
            correct = f"Consistent - FCF growth {fcf_growth:.0f}% reflects revenue ({revenue_growth}%) + margin expansion"
        else:
            fcf_growth = revenue_growth + 5
            correct = f"Requires verification - check capex and working capital assumptions for {fcf_growth:.0f}% FCF CAGR"

        rev_projections = {}
        fcf_projections = {}
        rev = base_rev
        fcf = base_rev * base_margin

        for i in range(5):
            year = 2024 + i
            rev_projections[f"{year}E"] = round(rev, 0)
            fcf_projections[f"{year}E"] = round(fcf, 0)
            rev = rev * (1 + revenue_growth / 100)
            fcf = fcf * (1 + fcf_growth / 100)

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue=rev_projections,
            free_cash_flow=fcf_projections,
            model_assumptions={
                "Revenue CAGR": f"{revenue_growth}%",
                "FCF CAGR": f"{fcf_growth:.0f}%",
                "Starting FCF Margin": f"{base_margin*100:.0f}%"
            }
        )

        distractors = [
            "Consistent - FCF should grow faster than revenue",
            "Invalid - FCF must equal net income",
            "Valid - standard modeling practice"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"A DCF model for {company} projects revenue growing at {revenue_growth}% CAGR "
                     f"while FCF is projected to grow at {fcf_growth:.0f}% CAGR. "
                     f"Starting FCF margin is {base_margin*100:.0f}%. Is this internally consistent?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"FCF growth exceeding revenue growth must be explained by margin expansion, "
                       f"declining capex intensity, or working capital improvements. "
                       f"Unexplained divergence is a red flag.",
            tags=["dcf", "consistency", "fcf", "sanity-check"]
        )
