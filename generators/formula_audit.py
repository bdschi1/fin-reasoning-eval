"""
Formula Audit Problem Generator

Generates problems testing ability to:
- Identify formula errors in financial models
- Spot circular references
- Detect hard-coded values (plugs)
- Recognize incorrect formula logic
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


class FormulaAuditGenerator(BaseGenerator):
    """Generator for formula audit problems."""

    @property
    def category(self) -> ProblemCategory:
        return ProblemCategory.FORMULA_AUDIT

    def generate_one(self, difficulty: Difficulty) -> Problem:
        """Generate a single formula audit problem."""
        problem_type = random.choice([
            'hard_coded_plug',
            'circular_reference',
            'broken_link',
            'incorrect_logic',
            'sign_convention',
            'unit_mismatch',
            'date_reference'
        ])

        generator_map = {
            'hard_coded_plug': self._generate_hardcoded_problem,
            'circular_reference': self._generate_circular_problem,
            'broken_link': self._generate_broken_link_problem,
            'incorrect_logic': self._generate_logic_error_problem,
            'sign_convention': self._generate_sign_problem,
            'unit_mismatch': self._generate_unit_problem,
            'date_reference': self._generate_date_reference_problem,
        }

        return generator_map[problem_type](difficulty)

    def _generate_hardcoded_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about identifying hard-coded values in formulas."""
        company = self._generate_company_name()
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            # Obvious hard-coded number
            formula = "=B10+B11+B12+500"
            cell = "B15 (Total Revenue)"
            correct = "Hard-coded plug - 500 added directly instead of cell reference"
            explanation = "The formula contains a literal number (500) instead of referencing a cell."
        elif difficulty == Difficulty.MEDIUM:
            # Less obvious - growth rate
            formula = "=B14*1.15"
            cell = "C14 (2025E Revenue)"
            correct = "Hard-coded growth rate - 1.15 should reference assumptions"
            explanation = "Growth rate assumptions should be in separate cells for auditability."
        elif difficulty == Difficulty.HARD:
            # Subtle - mixed formula
            formula = "=SUM(B10:B14)+IF(B5>1000,B5*0.02,0)"
            cell = "B20 (Adjusted Revenue)"
            correct = "Hard-coded threshold and rate - 1000 and 0.02 should be cell references"
            explanation = "Both the threshold (1000) and rate (0.02) are embedded in the formula."
        else:
            # Very subtle - negative plug
            formula = "=SUM(B10:B18)-SUM(C10:C18)+(-42.5)"
            cell = "D20 (Reconciliation)"
            correct = "Reconciliation plug - (-42.5) masks an underlying error"
            explanation = "The negative adjustment suggests a plug to force reconciliation."

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            formula_context=f"Cell {cell}\nFormula: {formula}"
        )

        distractors = [
            "Formula is correct - no issues",
            "Missing absolute references - needs $ signs",
            "Circular reference detected"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Review the following formula from a financial model:\n"
                     f"Cell: {cell}\nFormula: {formula}\n\n"
                     f"What issue, if any, is present?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=explanation,
            reasoning_steps=[
                "Examine formula structure",
                "Identify any literal numbers",
                "Check if literals should be cell references",
                f"Finding: {correct}"
            ],
            common_mistakes=[
                "Accepting hard-coded values as 'standard practice'",
                "Not checking assumption linkage",
                "Missing plugs disguised as adjustments"
            ],
            tags=["formula", "audit", "hard-coded", "plug"]
        )

    def _generate_circular_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about circular reference detection."""
        company = self._generate_company_name()
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            # Direct circular reference
            formulas = [
                "A1: =B1*1.1",
                "B1: =A1+100"
            ]
            correct = "Direct circular reference - A1→B1→A1"
            explanation = "A1 references B1, and B1 references A1 creating a direct loop."
        elif difficulty == Difficulty.MEDIUM:
            # Indirect circular
            formulas = [
                "A1: =SUM(B1:B5)",
                "B3: =C3*1.05",
                "C3: =A1*0.2"
            ]
            correct = "Indirect circular reference - A1→B3→C3→A1"
            explanation = "A1 sums B1:B5 (including B3), B3→C3, C3→A1."
        elif difficulty == Difficulty.HARD:
            # Intentional circular with iteration
            formulas = [
                "D5 (Interest): =D20*B2",
                "D20 (Debt): =D15-D5+D18",
                "Iteration: Enabled"
            ]
            correct = "Intentional circular - interest-debt loop requires iteration"
            explanation = "Interest depends on debt, and debt depends on interest. This is common in LBO models."
        else:
            # Hidden circular through named range
            formulas = [
                "A1: =TotalRevenue*1.05",
                "Named Range 'TotalRevenue': =SUM(A1:A12)",
                "Note: A1 is included in TotalRevenue range"
            ]
            correct = "Hidden circular via named range - A1 in TotalRevenue definition"
            explanation = "The named range includes A1, creating a hidden circular reference."

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            formula_context="\n".join(formulas)
        )

        distractors = [
            "No circular reference - formulas are independent",
            "Circular reference but acceptable for this model type",
            "Error in formula syntax, not circularity"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Review the following formulas and determine if there is a circular reference:\n\n"
                     f"{chr(10).join(formulas)}\n\n"
                     f"What is your assessment?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=explanation,
            tags=["formula", "audit", "circular-reference"]
        )

    def _generate_broken_link_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about broken external links."""
        company = self._generate_company_name()
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            # Obvious broken link
            formula = "='[Bloomberg_Data.xlsx]Sheet1'!$C$5"
            cell = "B10 (Stock Price)"
            correct = "Broken external link - Bloomberg_Data.xlsx file not available"
            explanation = "The formula references an external file that may not be present."
        elif difficulty == Difficulty.MEDIUM:
            # #REF! error
            formula = "=Revenue!#REF!*1.05"
            cell = "C15 (Projected Revenue)"
            correct = "Deleted reference - #REF! indicates source cell was deleted"
            explanation = "The #REF! error shows the original referenced cell no longer exists."
        elif difficulty == Difficulty.HARD:
            # Subtle - wrong sheet reference
            formula = "='Assumptions'!B5"
            note = "Assumptions sheet was renamed to 'Model Assumptions'"
            correct = "Invalid sheet reference - 'Assumptions' sheet was renamed"
            explanation = "The formula references a sheet name that no longer exists."
        else:
            # Complex - version mismatch
            formula = "='[Company_Model_v3.xlsx]DCF'!$H$25"
            note = "Current version is v5; v3 has different DCF layout"
            correct = "Version mismatch - referencing outdated model structure"
            explanation = "External link points to an old version with potentially different cell locations."

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            formula_context=f"Cell: {cell if difficulty in [Difficulty.EASY, Difficulty.MEDIUM] else 'F20'}\n"
                           f"Formula: {formula}\n"
                           f"{'Note: ' + note if difficulty in [Difficulty.HARD, Difficulty.EXPERT] else ''}"
        )

        distractors = [
            "Formula is correct - external links are valid",
            "Circular reference issue",
            "Formula syntax error"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Review this formula from a financial model:\n\n"
                     f"Formula: {formula}\n"
                     f"{'Note: ' + note if difficulty in [Difficulty.HARD, Difficulty.EXPERT] else ''}\n\n"
                     f"What issue is present?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=explanation,
            tags=["formula", "audit", "broken-link", "external-reference"]
        )

    def _generate_logic_error_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about formula logic errors."""
        company = self._generate_company_name()
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            # Wrong operator
            formula = "=Revenue+COGS"
            correct_formula = "=Revenue-COGS"
            cell = "Gross Profit"
            correct = "Logic error - should be Revenue MINUS COGS, not plus"
        elif difficulty == Difficulty.MEDIUM:
            # Wrong order of operations
            formula = "=A1+A2*A3"
            intended = "(A1+A2)*A3"
            cell = "Calculation"
            correct = "Order of operations - may need parentheses if sum should be multiplied"
        elif difficulty == Difficulty.HARD:
            # Subtle IF statement logic
            formula = "=IF(A1>100,B1,IF(A1>50,C1,D1))"
            issue = "Missing case: A1=100 goes to B1, but might want C1"
            cell = "Tiered Pricing"
            correct = "Boundary condition - A1=100 falls in first tier, may want >=100 vs >100"
        else:
            # Complex nested logic
            formula = "=SUMIF(A:A,\">0\",B:B)/COUNTIF(A:A,\">0\")"
            issue = "Division by zero risk if no positive values"
            cell = "Average Calculation"
            correct = "Missing error handling - division by zero if COUNTIF returns 0"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            formula_context=f"Cell: {cell}\nFormula: {formula}"
        )

        distractors = [
            "Formula is logically correct",
            "Syntax error in formula",
            "Hard-coded value issue"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Review this formula for logical correctness:\n\n"
                     f"Cell: {cell}\nFormula: {formula}\n\n"
                     f"Is there a logic error?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"The formula has a logic error: {correct}",
            tags=["formula", "audit", "logic-error"]
        )

    def _generate_sign_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about sign convention errors."""
        company = self._generate_company_name()
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            # Cash flow sign
            formula = "=NetIncome+Depreciation-CapEx"
            issue = "CapEx should be negative (use +(-CapEx) or -CapEx if CapEx is positive)"
            cell = "Cash Flow from Operations"
            correct = "Sign error possible - depends on whether CapEx is stored as positive or negative"
        elif difficulty == Difficulty.MEDIUM:
            # Balance sheet
            formula = "=Assets+Liabilities+Equity"
            cell = "Balance Check"
            correct = "Sign convention - should be Assets = Liabilities + Equity, not sum of all"
        elif difficulty == Difficulty.HARD:
            # Debt calculation
            formula = "=BeginningDebt+NewIssuance+Repayments"
            cell = "Ending Debt"
            correct = "Sign error - Repayments should be subtracted (if stored as positive)"
        else:
            # Complex working capital
            formula = "=-(CurrentAssets-CurrentLiabilities)+(PriorCA-PriorCL)"
            cell = "Change in Working Capital"
            correct = "Sign complexity - need to verify if increase in WC is cash use or source"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            formula_context=f"Cell: {cell}\nFormula: {formula}"
        )

        distractors = [
            "Formula signs are correct",
            "Missing absolute reference",
            "Circular reference detected"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Review the sign convention in this formula:\n\n"
                     f"Cell: {cell}\nFormula: {formula}\n\n"
                     f"Is there a sign convention issue?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Sign convention analysis: {correct}",
            tags=["formula", "audit", "sign-convention"]
        )

    def _generate_unit_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about unit mismatch errors."""
        company = self._generate_company_name()
        ticker = self._generate_ticker(company)

        note = ""  # Initialize note for all cases

        if difficulty == Difficulty.EASY:
            # Obvious - millions vs thousands
            formula = "=Revenue_M*SharesOutstanding_K"
            cell = "Revenue Per Share"
            correct = "Unit mismatch - revenue in millions, shares in thousands needs conversion"
        elif difficulty == Difficulty.MEDIUM:
            # Percentage vs decimal
            formula = "=Price*GrowthRate"
            note = "GrowthRate cell shows 15 (meaning 15%)"
            cell = "Projected Price"
            correct = "Format mismatch - if GrowthRate is 15 (not 0.15), need to divide by 100"
        elif difficulty == Difficulty.HARD:
            # Time period mismatch
            formula = "=AnnualRevenue/QuarterlyExpenses"
            note = "Annual revenue compared to quarterly expenses"
            cell = "Coverage Ratio"
            correct = "Period mismatch - comparing annual to quarterly creates 4x distortion"
        else:
            # Currency mismatch
            formula = "=US_Revenue+EU_Revenue"
            note = "US_Revenue in USD, EU_Revenue in EUR (no conversion)"
            cell = "Total Revenue"
            correct = "Currency mismatch - USD and EUR summed without conversion"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            formula_context=f"Cell: {cell}\nFormula: {formula}\n"
                           f"{'Note: ' + note if difficulty != Difficulty.EASY else ''}"
        )

        distractors = [
            "Units are consistent - no issue",
            "Formula syntax error",
            "Circular reference"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Check for unit consistency in this formula:\n\n"
                     f"Cell: {cell}\nFormula: {formula}\n"
                     f"{'Note: ' + note if difficulty != Difficulty.EASY else ''}\n\n"
                     f"Is there a unit mismatch?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Unit analysis: {correct}",
            tags=["formula", "audit", "unit-mismatch"]
        )

    def _generate_date_reference_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about date/period reference errors."""
        company = self._generate_company_name()
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            # Wrong year
            formula = "=C10*(1+$B$5)"
            note = "C10 is 2023 actual, formula is in 2025E column"
            cell = "2025E Revenue"
            correct = "Missing period - formula references 2023, should chain through 2024"
        elif difficulty == Difficulty.MEDIUM:
            # Relative reference should be absolute
            formula = "=B10*B$5"
            note = "Copied across columns but growth rate in B5 is 2024 specific"
            cell = "Projection formula"
            correct = "Year-specific assumption - growth rate should vary by year or be clearly labeled"
        elif difficulty == Difficulty.HARD:
            # Fiscal vs calendar
            formula = "=FiscalQ4_2024+CalendarQ1_2025"
            note = "Company FY ends March 31"
            cell = "H1 Total"
            correct = "Fiscal/calendar mismatch - Q4 fiscal 2024 ends March 2024, not December"
        else:
            # Timing of balance sheet vs income statement
            formula = "=AverageAssets_2024*ROA_2024"
            note = "AverageAssets uses (Beginning+Ending)/2"
            cell = "Check calculation"
            correct = "Timing consideration - verify ROA is annual and assets averaging is appropriate"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            formula_context=f"Cell: {cell}\nFormula: {formula}\nNote: {note}"
        )

        distractors = [
            "Date references are correct",
            "Hard-coded value issue",
            "Sign convention error"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Review the date/period references:\n\n"
                     f"Cell: {cell}\nFormula: {formula}\nNote: {note}\n\n"
                     f"Is there a date reference issue?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Date/period analysis: {correct}",
            tags=["formula", "audit", "date-reference", "period"]
        )
