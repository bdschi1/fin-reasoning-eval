"""
Financial Statement Analysis Problem Generator

Generates problems testing ability to:
- Analyze income statement trends
- Evaluate balance sheet health
- Assess cash flow quality
- Calculate and interpret financial ratios
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


class FinancialStatementGenerator(BaseGenerator):
    """Generator for financial statement analysis problems."""

    @property
    def category(self) -> ProblemCategory:
        return ProblemCategory.FINANCIAL_STATEMENT

    def generate_one(self, difficulty: Difficulty) -> Problem:
        """Generate a single financial statement analysis problem."""
        problem_type = random.choice([
            'margin_analysis',
            'leverage_ratio',
            'liquidity_analysis',
            'return_metrics',
            'cash_conversion',
            'working_capital',
            'coverage_ratio',
            'dupont_analysis'
        ])

        generator_map = {
            'margin_analysis': self._generate_margin_problem,
            'leverage_ratio': self._generate_leverage_problem,
            'liquidity_analysis': self._generate_liquidity_problem,
            'return_metrics': self._generate_return_problem,
            'cash_conversion': self._generate_cash_conversion_problem,
            'working_capital': self._generate_working_capital_problem,
            'coverage_ratio': self._generate_coverage_problem,
            'dupont_analysis': self._generate_dupont_problem,
        }

        return generator_map[problem_type](difficulty)

    def _generate_margin_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about margin analysis."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        revenue = round(random.uniform(500, 2000), 0)
        cogs = round(revenue * random.uniform(0.50, 0.75), 0)
        gross_profit = revenue - cogs
        gross_margin = gross_profit / revenue * 100

        sga = round(revenue * random.uniform(0.15, 0.25), 0)
        rd = round(revenue * random.uniform(0.05, 0.15), 0)
        operating_income = gross_profit - sga - rd
        operating_margin = operating_income / revenue * 100

        if difficulty == Difficulty.EASY:
            # Simple margin calculation
            correct = f"Gross margin: {gross_margin:.1f}%, Operating margin: {operating_margin:.1f}%"
            question_focus = "Calculate the gross and operating margins"
        elif difficulty == Difficulty.MEDIUM:
            # YoY margin change
            prior_gross_margin = gross_margin - random.uniform(1, 3)
            prior_operating_margin = operating_margin - random.uniform(0.5, 2)
            correct = f"Gross margin expanded {gross_margin - prior_gross_margin:.1f}pp, Operating margin expanded {operating_margin - prior_operating_margin:.1f}pp"
            question_focus = f"Compare to prior year (Gross: {prior_gross_margin:.1f}%, Operating: {prior_operating_margin:.1f}%)"
        elif difficulty == Difficulty.HARD:
            # Margin vs peer
            peer_gross_margin = gross_margin + random.uniform(-5, 5)
            peer_operating_margin = operating_margin + random.uniform(-3, 3)
            spread_gross = gross_margin - peer_gross_margin
            spread_op = operating_margin - peer_operating_margin
            if spread_gross > 0 and spread_op < 0:
                correct = f"Higher gross margin (+{spread_gross:.1f}pp) but lower operating margin ({spread_op:.1f}pp) vs peers - SG&A/R&D drag"
            elif spread_gross > 0:
                correct = f"Premium margins: +{spread_gross:.1f}pp gross, +{spread_op:.1f}pp operating vs peers"
            else:
                correct = f"Discount to peers: {spread_gross:.1f}pp gross, {spread_op:.1f}pp operating"
            question_focus = f"Compare to peer average (Gross: {peer_gross_margin:.1f}%, Operating: {peer_operating_margin:.1f}%)"
        else:
            # Incremental margin analysis
            incremental_rev = round(revenue * 0.10, 0)
            incremental_oi = round(incremental_rev * (operating_margin / 100 + 0.05), 0)
            incremental_margin = incremental_oi / incremental_rev * 100
            correct = f"Incremental margin of {incremental_margin:.1f}% exceeds current {operating_margin:.1f}%, indicating operating leverage"
            question_focus = f"With incremental revenue of ${incremental_rev}M and incremental operating income of ${incremental_oi}M"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"2024": revenue},
            model_assumptions={
                "Revenue": f"${revenue}M",
                "COGS": f"${cogs}M",
                "Gross Profit": f"${gross_profit}M",
                "SG&A": f"${sga}M",
                "R&D": f"${rd}M",
                "Operating Income": f"${operating_income}M"
            }
        )

        distractors = [
            f"Gross margin: {gross_margin + 5:.1f}%",
            f"Operating margin: {operating_margin - 3:.1f}%",
            "Margins are declining year-over-year"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Given the following financial data for {company}:\n"
                     f"Revenue: ${revenue}M, COGS: ${cogs}M, SG&A: ${sga}M, R&D: ${rd}M\n\n"
                     f"{question_focus}.",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Gross Margin = (Revenue - COGS) / Revenue = ({revenue} - {cogs}) / {revenue} = {gross_margin:.1f}%\n"
                       f"Operating Margin = Operating Income / Revenue = {operating_income} / {revenue} = {operating_margin:.1f}%",
            tags=["financial-statement", "margin", "profitability"]
        )

    def _generate_leverage_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about leverage ratio analysis."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        total_assets = round(random.uniform(1000, 5000), 0)
        total_debt = round(total_assets * random.uniform(0.20, 0.50), 0)
        cash = round(total_assets * random.uniform(0.05, 0.15), 0)
        equity = round(total_assets * random.uniform(0.30, 0.50), 0)
        ebitda = round(random.uniform(100, 500), 0)

        net_debt = total_debt - cash
        debt_to_equity = total_debt / equity
        net_debt_to_ebitda = net_debt / ebitda

        if difficulty == Difficulty.EASY:
            correct = f"Debt/Equity: {debt_to_equity:.2f}x, Net Debt/EBITDA: {net_debt_to_ebitda:.1f}x"
        elif difficulty == Difficulty.MEDIUM:
            # Assess leverage level
            if net_debt_to_ebitda < 2:
                leverage_assessment = "Conservative leverage"
            elif net_debt_to_ebitda < 4:
                leverage_assessment = "Moderate leverage"
            else:
                leverage_assessment = "High leverage"
            correct = f"{leverage_assessment} - Net Debt/EBITDA of {net_debt_to_ebitda:.1f}x"
        elif difficulty == Difficulty.HARD:
            # Covenant analysis
            covenant_level = 4.0
            headroom = covenant_level - net_debt_to_ebitda
            headroom_pct = headroom / covenant_level * 100
            if headroom > 1:
                correct = f"Comfortable covenant cushion - {headroom:.1f}x headroom ({headroom_pct:.0f}%)"
            else:
                correct = f"Tight covenant cushion - only {headroom:.1f}x headroom ({headroom_pct:.0f}%)"
        else:
            # Pro forma leverage after event
            acquisition_debt = round(total_debt * 0.5, 0)
            acquisition_ebitda = round(ebitda * 0.3, 0)
            pf_debt = total_debt + acquisition_debt
            pf_ebitda = ebitda + acquisition_ebitda
            pf_leverage = (pf_debt - cash) / pf_ebitda
            correct = f"Pro forma leverage {pf_leverage:.1f}x vs current {net_debt_to_ebitda:.1f}x after acquisition"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            total_debt={"Current": total_debt},
            cash={"Current": cash},
            equity={"Current": equity},
            ebitda={"2024": ebitda},
            model_assumptions={
                "Total Debt": f"${total_debt}M",
                "Cash": f"${cash}M",
                "Net Debt": f"${net_debt}M",
                "Equity": f"${equity}M",
                "EBITDA": f"${ebitda}M"
            }
        )

        distractors = [
            f"Debt/Equity: {debt_to_equity + 0.5:.2f}x",
            f"Net Debt/EBITDA: {net_debt_to_ebitda + 1:.1f}x",
            "Company is overleveraged"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Calculate and assess {company}'s leverage:\n"
                     f"Total Debt: ${total_debt}M, Cash: ${cash}M, Equity: ${equity}M, EBITDA: ${ebitda}M",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Debt/Equity = {total_debt}/{equity} = {debt_to_equity:.2f}x\n"
                       f"Net Debt = {total_debt} - {cash} = {net_debt}M\n"
                       f"Net Debt/EBITDA = {net_debt}/{ebitda} = {net_debt_to_ebitda:.1f}x",
            tags=["financial-statement", "leverage", "debt"]
        )

    def _generate_liquidity_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about liquidity analysis."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        current_assets = round(random.uniform(200, 800), 0)
        inventory = round(current_assets * random.uniform(0.20, 0.40), 0)
        receivables = round(current_assets * random.uniform(0.25, 0.40), 0)
        cash = current_assets - inventory - receivables
        current_liabilities = round(random.uniform(150, 500), 0)

        current_ratio = current_assets / current_liabilities
        quick_ratio = (current_assets - inventory) / current_liabilities
        cash_ratio = cash / current_liabilities

        if difficulty == Difficulty.EASY:
            correct = f"Current ratio: {current_ratio:.2f}x, Quick ratio: {quick_ratio:.2f}x"
        elif difficulty == Difficulty.MEDIUM:
            if current_ratio > 2.0:
                assessment = "Strong liquidity but potentially inefficient asset use"
            elif current_ratio > 1.0:
                assessment = "Adequate liquidity position"
            else:
                assessment = "Liquidity concern - current ratio below 1.0x"
            correct = f"{assessment} with current ratio of {current_ratio:.2f}x"
        elif difficulty == Difficulty.HARD:
            # Quality of current assets
            if inventory / current_assets > 0.35:
                correct = f"Liquidity quality concern - {inventory/current_assets*100:.0f}% inventory-dependent"
            else:
                correct = f"High-quality liquidity - {(cash+receivables)/current_assets*100:.0f}% in liquid assets"
        else:
            # Working capital needs
            revenue = round(random.uniform(1000, 3000), 0)
            wc_as_pct_rev = (current_assets - current_liabilities) / revenue * 100
            correct = f"Working capital intensity of {wc_as_pct_rev:.1f}% of revenue"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            model_assumptions={
                "Current Assets": f"${current_assets}M",
                "- Cash": f"${cash}M",
                "- Receivables": f"${receivables}M",
                "- Inventory": f"${inventory}M",
                "Current Liabilities": f"${current_liabilities}M"
            }
        )

        distractors = [
            f"Current ratio: {current_ratio - 0.3:.2f}x",
            "Company has excess liquidity",
            "Quick ratio indicates concern"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Analyze {company}'s liquidity position:\n"
                     f"Current Assets: ${current_assets}M (Cash: ${cash}M, Receivables: ${receivables}M, "
                     f"Inventory: ${inventory}M)\nCurrent Liabilities: ${current_liabilities}M",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Current Ratio = {current_assets}/{current_liabilities} = {current_ratio:.2f}x\n"
                       f"Quick Ratio = ({current_assets}-{inventory})/{current_liabilities} = {quick_ratio:.2f}x\n"
                       f"Cash Ratio = {cash}/{current_liabilities} = {cash_ratio:.2f}x",
            tags=["financial-statement", "liquidity", "working-capital"]
        )

    def _generate_return_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about return metrics (ROE, ROA, ROIC)."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        total_assets = round(random.uniform(2000, 8000), 0)
        equity = round(total_assets * random.uniform(0.35, 0.55), 0)
        net_income = round(random.uniform(100, 500), 0)
        ebit = round(net_income * random.uniform(1.3, 1.6), 0)
        invested_capital = round(total_assets * random.uniform(0.60, 0.80), 0)
        tax_rate = 0.25

        roe = net_income / equity * 100
        roa = net_income / total_assets * 100
        roic = ebit * (1 - tax_rate) / invested_capital * 100

        if difficulty == Difficulty.EASY:
            correct = f"ROE: {roe:.1f}%, ROA: {roa:.1f}%"
        elif difficulty == Difficulty.MEDIUM:
            wacc = 9.0
            spread = roic - wacc
            if spread > 3:
                correct = f"Value creation - ROIC of {roic:.1f}% exceeds WACC of {wacc}% by {spread:.1f}pp"
            elif spread > 0:
                correct = f"Modest value creation - ROIC {roic:.1f}% vs WACC {wacc}% (+{spread:.1f}pp)"
            else:
                correct = f"Value destruction - ROIC {roic:.1f}% below WACC {wacc}% ({spread:.1f}pp)"
        elif difficulty == Difficulty.HARD:
            # ROE vs ROIC comparison
            if roe > roic * 1.5:
                correct = f"Leverage amplifying returns - ROE {roe:.1f}% vs ROIC {roic:.1f}%"
            else:
                correct = f"Balanced returns - ROE {roe:.1f}% similar to ROIC {roic:.1f}%"
        else:
            # Decomposition
            asset_turnover = (net_income / roa * 100) / total_assets
            profit_margin = net_income / (asset_turnover * total_assets) * 100
            leverage_factor = total_assets / equity
            correct = f"ROE driven by: {profit_margin:.1f}% margin × {asset_turnover:.2f}x turns × {leverage_factor:.1f}x leverage"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            total_assets={"Current": total_assets},
            equity={"Current": equity},
            net_income={"2024": net_income},
            model_assumptions={
                "Total Assets": f"${total_assets}M",
                "Equity": f"${equity}M",
                "Net Income": f"${net_income}M",
                "EBIT": f"${ebit}M",
                "Invested Capital": f"${invested_capital}M",
                "Tax Rate": f"{tax_rate*100:.0f}%"
            }
        )

        distractors = [
            f"ROE: {roe - 3:.1f}%",
            f"ROIC: {roic + 4:.1f}%",
            "Returns are below cost of capital"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Analyze {company}'s return metrics:\n"
                     f"Total Assets: ${total_assets}M, Equity: ${equity}M, Net Income: ${net_income}M, "
                     f"EBIT: ${ebit}M, Invested Capital: ${invested_capital}M",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"ROE = NI/Equity = {net_income}/{equity} = {roe:.1f}%\n"
                       f"ROA = NI/Assets = {net_income}/{total_assets} = {roa:.1f}%\n"
                       f"ROIC = EBIT(1-t)/IC = {ebit}×0.75/{invested_capital} = {roic:.1f}%",
            tags=["financial-statement", "return-metrics", "roe", "roic"]
        )

    def _generate_cash_conversion_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about cash conversion cycle."""
        sector = random.choice(["Consumer Discretionary", "Industrials", "Technology"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        revenue = round(random.uniform(800, 2500), 0)
        cogs = round(revenue * random.uniform(0.55, 0.70), 0)
        receivables = round(revenue * random.uniform(0.08, 0.15), 0)
        inventory = round(cogs * random.uniform(0.12, 0.25), 0)
        payables = round(cogs * random.uniform(0.08, 0.18), 0)

        dso = receivables / revenue * 365
        dio = inventory / cogs * 365
        dpo = payables / cogs * 365
        ccc = dso + dio - dpo

        if difficulty == Difficulty.EASY:
            correct = f"DSO: {dso:.0f} days, DIO: {dio:.0f} days, DPO: {dpo:.0f} days, CCC: {ccc:.0f} days"
        elif difficulty == Difficulty.MEDIUM:
            if ccc < 30:
                assessment = "Efficient cash cycle"
            elif ccc < 60:
                assessment = "Average cash cycle"
            else:
                assessment = "Extended cash cycle - potential working capital drag"
            correct = f"{assessment} with CCC of {ccc:.0f} days"
        elif difficulty == Difficulty.HARD:
            # Working capital funding need
            daily_rev = revenue / 365
            wc_funding = ccc * daily_rev
            correct = f"Cash cycle of {ccc:.0f} days requires ${wc_funding:.0f}M working capital funding"
        else:
            # Improvement opportunity
            target_ccc = ccc * 0.8
            improvement_days = ccc - target_ccc
            cash_release = improvement_days * revenue / 365
            correct = f"Reducing CCC by {improvement_days:.0f} days would release ${cash_release:.0f}M in cash"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"2024": revenue},
            model_assumptions={
                "Revenue": f"${revenue}M",
                "COGS": f"${cogs}M",
                "Receivables": f"${receivables}M",
                "Inventory": f"${inventory}M",
                "Payables": f"${payables}M"
            }
        )

        distractors = [
            f"CCC: {ccc + 20:.0f} days",
            f"DSO: {dso - 10:.0f} days",
            "Negative cash conversion cycle"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Calculate {company}'s cash conversion cycle:\n"
                     f"Revenue: ${revenue}M, COGS: ${cogs}M, Receivables: ${receivables}M, "
                     f"Inventory: ${inventory}M, Payables: ${payables}M",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"DSO = (AR/Rev) × 365 = ({receivables}/{revenue}) × 365 = {dso:.0f} days\n"
                       f"DIO = (Inv/COGS) × 365 = ({inventory}/{cogs}) × 365 = {dio:.0f} days\n"
                       f"DPO = (AP/COGS) × 365 = ({payables}/{cogs}) × 365 = {dpo:.0f} days\n"
                       f"CCC = DSO + DIO - DPO = {dso:.0f} + {dio:.0f} - {dpo:.0f} = {ccc:.0f} days",
            tags=["financial-statement", "cash-conversion", "working-capital"]
        )

    def _generate_working_capital_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about working capital analysis."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        revenue_py = round(random.uniform(700, 2000), 0)
        revenue_cy = round(revenue_py * random.uniform(1.05, 1.15), 0)

        ca_py = round(revenue_py * random.uniform(0.18, 0.28), 0)
        cl_py = round(revenue_py * random.uniform(0.12, 0.20), 0)
        ca_cy = round(revenue_cy * random.uniform(0.18, 0.28), 0)
        cl_cy = round(revenue_cy * random.uniform(0.12, 0.20), 0)

        nwc_py = ca_py - cl_py
        nwc_cy = ca_cy - cl_cy
        change_nwc = nwc_cy - nwc_py

        nwc_py_pct = nwc_py / revenue_py * 100
        nwc_cy_pct = nwc_cy / revenue_cy * 100

        if difficulty == Difficulty.EASY:
            # Use consistent sign-then-currency format: +$38M not $+38M
            sign = "+" if change_nwc >= 0 else "-"
            correct = f"Net Working Capital changed by {sign}${abs(change_nwc):.0f}M"
        elif difficulty == Difficulty.MEDIUM:
            if change_nwc > 0:
                correct = f"Working capital build of ${change_nwc:.0f}M - cash use"
            else:
                correct = f"Working capital release of ${abs(change_nwc):.0f}M - cash source"
        elif difficulty == Difficulty.HARD:
            if nwc_cy_pct > nwc_py_pct:
                correct = f"WC intensity increased from {nwc_py_pct:.1f}% to {nwc_cy_pct:.1f}% of revenue"
            else:
                correct = f"WC efficiency improved from {nwc_py_pct:.1f}% to {nwc_cy_pct:.1f}% of revenue"
        else:
            rev_growth = (revenue_cy / revenue_py - 1) * 100
            wc_growth = (nwc_cy / nwc_py - 1) * 100 if nwc_py > 0 else 100
            if wc_growth > rev_growth:
                correct = f"WC growing faster ({wc_growth:.0f}%) than revenue ({rev_growth:.0f}%) - monitor"
            else:
                correct = f"Healthy dynamic - WC growth ({wc_growth:.0f}%) below revenue ({rev_growth:.0f}%)"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"Prior Year": revenue_py, "Current Year": revenue_cy},
            model_assumptions={
                "Prior Year CA": f"${ca_py}M",
                "Prior Year CL": f"${cl_py}M",
                "Prior Year NWC": f"${nwc_py}M",
                "Current Year CA": f"${ca_cy}M",
                "Current Year CL": f"${cl_cy}M",
                "Current Year NWC": f"${nwc_cy}M"
            }
        )

        inv_sign = "-" if change_nwc >= 0 else "+"
        distractors = [
            f"WC change: {inv_sign}${abs(change_nwc):.0f}M",
            "Working capital is adequate",
            "No significant change in working capital"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Analyze working capital changes for {company}:\n"
                     f"Prior Year: CA ${ca_py}M, CL ${cl_py}M, Revenue ${revenue_py}M\n"
                     f"Current Year: CA ${ca_cy}M, CL ${cl_cy}M, Revenue ${revenue_cy}M",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Prior NWC = {ca_py} - {cl_py} = {nwc_py}M ({nwc_py_pct:.1f}% of rev)\n"
                       f"Current NWC = {ca_cy} - {cl_cy} = {nwc_cy}M ({nwc_cy_pct:.1f}% of rev)\n"
                       f"Change = {change_nwc:+.0f}M",
            tags=["financial-statement", "working-capital", "cash-flow"]
        )

    def _generate_coverage_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about debt coverage ratios."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        ebit = round(random.uniform(100, 400), 0)
        ebitda = round(ebit * random.uniform(1.15, 1.35), 0)
        interest_expense = round(random.uniform(20, 80), 0)
        principal_payment = round(random.uniform(30, 100), 0)
        capex = round(ebitda * random.uniform(0.15, 0.30), 0)

        interest_coverage = ebit / interest_expense
        fccr = ebitda / (interest_expense + principal_payment)
        dscr = (ebitda - capex) / (interest_expense + principal_payment)

        if difficulty == Difficulty.EASY:
            correct = f"Interest coverage: {interest_coverage:.1f}x (EBIT/Interest)"
        elif difficulty == Difficulty.MEDIUM:
            if interest_coverage > 4:
                assessment = "Comfortable coverage"
            elif interest_coverage > 2:
                assessment = "Adequate coverage"
            else:
                assessment = "Tight coverage - refinancing risk"
            correct = f"{assessment} with {interest_coverage:.1f}x interest coverage"
        elif difficulty == Difficulty.HARD:
            if dscr > 1.5:
                correct = f"Strong DSCR of {dscr:.2f}x after maintenance capex"
            elif dscr > 1.0:
                correct = f"Marginal DSCR of {dscr:.2f}x - limited cushion after capex"
            else:
                correct = f"DSCR below 1.0x ({dscr:.2f}x) - cash flow insufficient for debt service"
        else:
            # Covenant headroom
            covenant = 3.0
            headroom = interest_coverage - covenant
            headroom_pct = headroom / covenant * 100
            correct = f"Interest coverage {interest_coverage:.1f}x vs covenant {covenant}x - {headroom_pct:.0f}% cushion"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            ebitda={"2024": ebitda},
            model_assumptions={
                "EBIT": f"${ebit}M",
                "EBITDA": f"${ebitda}M",
                "Interest Expense": f"${interest_expense}M",
                "Principal Payment": f"${principal_payment}M",
                "Maintenance CapEx": f"${capex}M"
            }
        )

        distractors = [
            f"Interest coverage: {interest_coverage + 1:.1f}x",
            f"DSCR: {dscr + 0.5:.2f}x",
            "Coverage ratios are concerning"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Evaluate {company}'s debt coverage:\n"
                     f"EBIT: ${ebit}M, EBITDA: ${ebitda}M, Interest: ${interest_expense}M, "
                     f"Principal: ${principal_payment}M, CapEx: ${capex}M",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Interest Coverage = EBIT/Interest = {ebit}/{interest_expense} = {interest_coverage:.1f}x\n"
                       f"FCCR = EBITDA/(Int+Prin) = {ebitda}/({interest_expense}+{principal_payment}) = {fccr:.2f}x\n"
                       f"DSCR = (EBITDA-CapEx)/(Int+Prin) = ({ebitda}-{capex})/({interest_expense}+{principal_payment}) = {dscr:.2f}x",
            tags=["financial-statement", "coverage", "debt-service"]
        )

    def _generate_dupont_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about DuPont analysis."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        revenue = round(random.uniform(1000, 4000), 0)
        net_income = round(revenue * random.uniform(0.05, 0.12), 0)
        total_assets = round(revenue * random.uniform(0.80, 1.40), 0)
        equity = round(total_assets * random.uniform(0.35, 0.55), 0)

        profit_margin = net_income / revenue * 100
        asset_turnover = revenue / total_assets
        equity_multiplier = total_assets / equity
        roe = profit_margin / 100 * asset_turnover * equity_multiplier * 100

        if difficulty == Difficulty.EASY:
            correct = f"ROE = {profit_margin:.1f}% × {asset_turnover:.2f}x × {equity_multiplier:.2f}x = {roe:.1f}%"
        elif difficulty == Difficulty.MEDIUM:
            # Identify primary driver
            if profit_margin > 8:
                driver = "margin-driven"
            elif asset_turnover > 1.0:
                driver = "turnover-driven"
            else:
                driver = "leverage-driven"
            correct = f"ROE of {roe:.1f}% is primarily {driver}"
        elif difficulty == Difficulty.HARD:
            # Year-over-year change attribution
            py_roe = roe * random.uniform(0.85, 0.95)
            margin_contribution = (profit_margin - profit_margin * 0.95) / 100 * asset_turnover * equity_multiplier
            correct = f"ROE improved from {py_roe:.1f}% to {roe:.1f}% primarily from margin expansion"
        else:
            # Peer comparison decomposition
            peer_margin = profit_margin * random.uniform(0.8, 1.2)
            peer_turnover = asset_turnover * random.uniform(0.8, 1.2)
            peer_leverage = equity_multiplier * random.uniform(0.8, 1.2)
            peer_roe = peer_margin / 100 * peer_turnover * peer_leverage * 100
            if roe > peer_roe:
                correct = f"ROE of {roe:.1f}% exceeds peer {peer_roe:.1f}% - {'higher margin' if profit_margin > peer_margin else 'higher leverage'}"
            else:
                correct = f"ROE of {roe:.1f}% trails peer {peer_roe:.1f}% - {'lower margin' if profit_margin < peer_margin else 'lower turnover'}"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"2024": revenue},
            net_income={"2024": net_income},
            total_assets={"2024": total_assets},
            equity={"2024": equity},
            model_assumptions={
                "Profit Margin": f"{profit_margin:.1f}%",
                "Asset Turnover": f"{asset_turnover:.2f}x",
                "Equity Multiplier": f"{equity_multiplier:.2f}x",
                "ROE": f"{roe:.1f}%"
            }
        )

        distractors = [
            f"ROE: {roe - 3:.1f}%",
            "ROE driven by high asset turnover",
            f"Profit margin of {profit_margin + 5:.1f}%"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Perform DuPont analysis for {company}:\n"
                     f"Revenue: ${revenue}M, Net Income: ${net_income}M, "
                     f"Total Assets: ${total_assets}M, Equity: ${equity}M",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"DuPont Identity: ROE = Margin × Turnover × Leverage\n"
                       f"Profit Margin = NI/Rev = {net_income}/{revenue} = {profit_margin:.1f}%\n"
                       f"Asset Turnover = Rev/Assets = {revenue}/{total_assets} = {asset_turnover:.2f}x\n"
                       f"Equity Multiplier = Assets/Equity = {total_assets}/{equity} = {equity_multiplier:.2f}x\n"
                       f"ROE = {profit_margin:.1f}% × {asset_turnover:.2f} × {equity_multiplier:.2f} = {roe:.1f}%",
            tags=["financial-statement", "dupont", "roe", "decomposition"]
        )
