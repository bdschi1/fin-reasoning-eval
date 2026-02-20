"""
Earnings Surprise Problem Generator

Generates problems testing ability to:
- Calculate earnings beats/misses
- Assess magnitude of surprises
- Identify drivers of variance
- Evaluate market reaction implications
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


class EarningsSurpriseGenerator(BaseGenerator):
    """Generator for earnings surprise analysis problems."""

    @property
    def category(self) -> ProblemCategory:
        return ProblemCategory.EARNINGS_SURPRISE

    def generate_one(self, difficulty: Difficulty) -> Problem:
        """Generate a single earnings surprise problem."""
        problem_type = random.choice([
            'beat_miss_calculation',
            'surprise_magnitude',
            'driver_identification',
            'guidance_comparison',
            'sequential_analysis',
            'margin_variance'
        ])

        generator_map = {
            'beat_miss_calculation': self._generate_beat_miss_problem,
            'surprise_magnitude': self._generate_magnitude_problem,
            'driver_identification': self._generate_driver_problem,
            'guidance_comparison': self._generate_guidance_problem,
            'sequential_analysis': self._generate_sequential_problem,
            'margin_variance': self._generate_margin_variance_problem,
        }

        return generator_map[problem_type](difficulty)

    def _generate_beat_miss_problem(self, difficulty: Difficulty) -> Problem:
        """Generate a basic earnings beat/miss calculation problem."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate consensus and actual EPS
        consensus_eps = round(random.uniform(1.0, 5.0), 2)

        if difficulty == Difficulty.EASY:
            # Clear beat or miss
            variance = random.choice([-0.15, 0.15, -0.20, 0.20])
            actual_eps = round(consensus_eps * (1 + variance), 2)
        elif difficulty == Difficulty.MEDIUM:
            # Smaller variance
            variance = random.choice([-0.05, 0.05, -0.08, 0.08])
            actual_eps = round(consensus_eps * (1 + variance), 2)
        elif difficulty == Difficulty.HARD:
            # Very small variance, need precise calculation
            variance = random.choice([-0.02, 0.02, -0.03, 0.03])
            actual_eps = round(consensus_eps * (1 + variance), 2)
        else:  # EXPERT
            # Include one-time items
            variance = random.uniform(-0.10, 0.10)
            actual_eps = round(consensus_eps * (1 + variance), 2)

        # Calculate correct answer
        surprise_pct = ((actual_eps - consensus_eps) / consensus_eps) * 100
        surprise_pct = round(surprise_pct, 1)

        if surprise_pct > 0:
            correct_answer = f"Beat by {abs(surprise_pct)}%"
            result_type = "beat"
        else:
            correct_answer = f"Miss by {abs(surprise_pct)}%"
            result_type = "miss"

        # Create distractors
        distractors = [
            f"{'Beat' if result_type == 'miss' else 'Miss'} by {abs(surprise_pct)}%",
            f"{'Beat' if result_type == 'beat' else 'Miss'} by {abs(surprise_pct * 2):.1f}%",
            f"In-line with consensus (within 1%)"
        ]

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            consensus_estimates={"EPS": consensus_eps},
            eps={"Q3 2024 Actual": actual_eps, "Q3 2024 Consensus": consensus_eps}
        )

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} ({ticker}) reported Q3 2024 EPS of ${actual_eps:.2f}. "
                     f"The consensus estimate was ${consensus_eps:.2f}. "
                     f"Did the company beat or miss consensus, and by what percentage?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct_answer,
            answer_options=self._create_answer_options(correct_answer, distractors),
            explanation=f"The earnings surprise is calculated as (Actual - Consensus) / Consensus. "
                       f"(${actual_eps:.2f} - ${consensus_eps:.2f}) / ${consensus_eps:.2f} = {surprise_pct:.1f}%",
            reasoning_steps=[
                f"Identify actual EPS: ${actual_eps:.2f}",
                f"Identify consensus EPS: ${consensus_eps:.2f}",
                f"Calculate difference: ${actual_eps:.2f} - ${consensus_eps:.2f} = ${actual_eps - consensus_eps:.2f}",
                f"Calculate percentage: ${actual_eps - consensus_eps:.2f} / ${consensus_eps:.2f} = {surprise_pct:.1f}%",
                f"Result: {'Beat' if surprise_pct > 0 else 'Miss'} by {abs(surprise_pct):.1f}%"
            ],
            common_mistakes=[
                "Using consensus as denominator incorrectly",
                "Confusing beat/miss direction",
                "Rounding errors"
            ],
            tags=["earnings", "beat-miss", "calculation", "eps"]
        )

    def _generate_magnitude_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about classifying earnings surprise magnitude."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate data based on difficulty
        if difficulty == Difficulty.EASY:
            surprise_pct = random.choice([15.0, -12.0, 8.0, -9.0])
            correct_magnitude = "Significant" if abs(surprise_pct) >= 10 else "Moderate"
        elif difficulty == Difficulty.MEDIUM:
            surprise_pct = random.choice([5.5, -4.8, 3.2, -6.1])
            correct_magnitude = "Moderate" if abs(surprise_pct) >= 5 else "Minor"
        elif difficulty == Difficulty.HARD:
            surprise_pct = random.choice([2.1, -1.8, 4.9, -5.1])
            correct_magnitude = "Minor" if abs(surprise_pct) < 3 else "Moderate"
        else:
            surprise_pct = random.uniform(-2, 2)
            correct_magnitude = "Within normal variance" if abs(surprise_pct) < 2 else "Minor"

        consensus_eps = round(random.uniform(2.0, 4.0), 2)
        actual_eps = round(consensus_eps * (1 + surprise_pct / 100), 2)

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            eps={"Actual": actual_eps, "Consensus": consensus_eps}
        )

        distractors = [m for m in ["Significant", "Moderate", "Minor", "Within normal variance"]
                       if m != correct_magnitude][:3]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} reported EPS of ${actual_eps:.2f} versus consensus of ${consensus_eps:.2f}. "
                     f"Using standard thresholds (>10% significant, 5-10% moderate, 2-5% minor, <2% normal), "
                     f"how would you classify this earnings surprise?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct_magnitude,
            answer_options=self._create_answer_options(correct_magnitude, distractors),
            explanation=f"The surprise is {surprise_pct:.1f}%, which falls into the '{correct_magnitude}' category.",
            reasoning_steps=[
                f"Calculate surprise: ({actual_eps} - {consensus_eps}) / {consensus_eps} = {surprise_pct:.1f}%",
                "Apply classification thresholds",
                f"Result: {correct_magnitude}"
            ],
            tags=["earnings", "magnitude", "classification"]
        )

    def _generate_driver_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about identifying earnings variance drivers."""
        sector = random.choice(["Technology", "Healthcare", "Consumer Discretionary"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate revenue and margin data
        rev_consensus = round(random.uniform(800, 1200), 0)
        margin_consensus = round(random.uniform(0.18, 0.25), 3)

        if difficulty == Difficulty.EASY:
            # Clear single driver
            rev_actual = round(rev_consensus * 1.08, 0)  # 8% revenue beat
            margin_actual = margin_consensus  # Flat margin
            primary_driver = "Revenue beat"
        elif difficulty == Difficulty.MEDIUM:
            # Two factors
            rev_actual = round(rev_consensus * 1.03, 0)
            margin_actual = round(margin_consensus + 0.02, 3)
            primary_driver = "Margin expansion"
        elif difficulty == Difficulty.HARD:
            # Offsetting factors
            rev_actual = round(rev_consensus * 0.97, 0)  # Revenue miss
            margin_actual = round(margin_consensus + 0.04, 3)  # Big margin beat
            primary_driver = "Margin expansion offset revenue shortfall"
        else:
            # Multiple complex factors
            rev_actual = round(rev_consensus * 1.02, 0)
            margin_actual = round(margin_consensus + 0.015, 3)
            primary_driver = "Combination of modest revenue growth and margin expansion"

        eps_consensus = round(rev_consensus * margin_consensus / 100, 2)
        eps_actual = round(rev_actual * margin_actual / 100, 2)

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"Actual": rev_actual, "Consensus": rev_consensus},
            eps={"Actual": eps_actual, "Consensus": eps_consensus},
            model_assumptions={
                "Margin Consensus": f"{margin_consensus * 100:.1f}%",
                "Margin Actual": f"{margin_actual * 100:.1f}%"
            }
        )

        distractors = [
            "Revenue miss offset by share buybacks",
            "One-time tax benefit",
            "Currency tailwind" if primary_driver != "Revenue beat" else "Margin compression"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} reported revenue of ${rev_actual:.0f}M (consensus: ${rev_consensus:.0f}M) "
                     f"with operating margin of {margin_actual * 100:.1f}% (consensus: {margin_consensus * 100:.1f}%). "
                     f"EPS came in at ${eps_actual:.2f} vs ${eps_consensus:.2f} consensus. "
                     f"What was the primary driver of the EPS variance?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=primary_driver,
            answer_options=self._create_answer_options(primary_driver, distractors),
            explanation=f"Revenue variance: {((rev_actual / rev_consensus) - 1) * 100:.1f}%, "
                       f"Margin variance: {(margin_actual - margin_consensus) * 100:.1f}pp. "
                       f"The primary driver is: {primary_driver}",
            tags=["earnings", "drivers", "variance-analysis"]
        )

    def _generate_guidance_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem comparing results to prior guidance."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate guidance range and actual
        guidance_low = round(random.uniform(2.0, 3.0), 2)
        guidance_high = round(guidance_low + random.uniform(0.20, 0.40), 2)
        midpoint = (guidance_low + guidance_high) / 2

        if difficulty == Difficulty.EASY:
            # Clear above/below range
            actual = round(guidance_high + 0.15, 2) if random.random() > 0.5 else round(guidance_low - 0.10, 2)
            if actual > guidance_high:
                correct = "Above guidance range"
            else:
                correct = "Below guidance range"
        elif difficulty == Difficulty.MEDIUM:
            # At edges of range
            actual = guidance_high if random.random() > 0.5 else guidance_low
            correct = "At top of guidance range" if actual == guidance_high else "At bottom of guidance range"
        else:
            # Within range - need to assess vs midpoint
            actual = round(midpoint + random.uniform(-0.08, 0.08), 2)
            correct = "Above midpoint of guidance" if actual > midpoint else "Below midpoint of guidance"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            eps={"Actual": actual},
            guidance=f"Full-year EPS guidance: ${guidance_low:.2f} - ${guidance_high:.2f}"
        )

        if difficulty in [Difficulty.EASY, Difficulty.MEDIUM]:
            distractors = [
                "Within guidance range",
                "Above guidance range" if "Below" in correct else "Below guidance range",
                "At midpoint of guidance"
            ]
        else:
            distractors = [
                "Above guidance range",
                "Below guidance range",
                "Below midpoint of guidance" if "Above" in correct else "Above midpoint of guidance"
            ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} provided full-year EPS guidance of ${guidance_low:.2f} - ${guidance_high:.2f}. "
                     f"The company reported actual EPS of ${actual:.2f}. "
                     f"How does the result compare to the guidance range?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors[:3]),
            explanation=f"Guidance range: ${guidance_low:.2f} - ${guidance_high:.2f}, "
                       f"Midpoint: ${midpoint:.2f}, Actual: ${actual:.2f}. Result: {correct}",
            tags=["earnings", "guidance", "range-analysis"]
        )

    def _generate_sequential_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about quarter-over-quarter EPS trends."""
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        # Generate quarterly EPS data
        q1_eps = round(random.uniform(1.0, 2.0), 2)
        growth_rates = {
            Difficulty.EASY: [0.08, 0.10, 0.12],
            Difficulty.MEDIUM: [0.05, 0.03, 0.07],
            Difficulty.HARD: [0.02, -0.03, 0.08],
            Difficulty.EXPERT: [-0.02, 0.04, -0.01]
        }

        rates = growth_rates[difficulty]
        q2_eps = round(q1_eps * (1 + rates[0]), 2)
        q3_eps = round(q2_eps * (1 + rates[1]), 2)
        q4_eps = round(q3_eps * (1 + rates[2]), 2)

        # Calculate trend
        total_growth = (q4_eps / q1_eps - 1) * 100
        if total_growth > 15:
            correct = "Consistent acceleration"
        elif total_growth > 5:
            correct = "Moderate sequential growth"
        elif total_growth > -5:
            correct = "Flat sequential performance"
        else:
            correct = "Sequential deceleration"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            eps={
                "Q1 2024": q1_eps,
                "Q2 2024": q2_eps,
                "Q3 2024": q3_eps,
                "Q4 2024": q4_eps
            }
        )

        distractors = [t for t in ["Consistent acceleration", "Moderate sequential growth",
                                    "Flat sequential performance", "Sequential deceleration"]
                       if t != correct][:3]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Review {company}'s quarterly EPS progression: "
                     f"Q1: ${q1_eps:.2f}, Q2: ${q2_eps:.2f}, Q3: ${q3_eps:.2f}, Q4: ${q4_eps:.2f}. "
                     f"How would you characterize the sequential earnings trend?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Q1→Q2: {rates[0]*100:.1f}%, Q2→Q3: {rates[1]*100:.1f}%, Q3→Q4: {rates[2]*100:.1f}%. "
                       f"Total growth: {total_growth:.1f}%. Trend: {correct}",
            tags=["earnings", "sequential", "trend-analysis"]
        )

    def _generate_margin_variance_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about margin-driven earnings variance."""
        sector = random.choice(["Technology", "Healthcare", "Industrials"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        revenue = round(random.uniform(500, 1500), 0)

        if difficulty == Difficulty.EASY:
            margin_expected = 0.20
            margin_actual = 0.25
            margin_impact = "significant positive"
        elif difficulty == Difficulty.MEDIUM:
            margin_expected = 0.22
            margin_actual = 0.24
            margin_impact = "modest positive"
        elif difficulty == Difficulty.HARD:
            margin_expected = 0.23
            margin_actual = 0.21
            margin_impact = "modest negative"
        else:
            margin_expected = 0.215
            margin_actual = 0.205
            margin_impact = "slight negative"

        eps_impact = (margin_actual - margin_expected) * revenue / 100  # Simplified
        shares = 100  # million shares

        correct = f"Margin variance contributed ${abs(eps_impact):.2f} per share ({margin_impact} impact)"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            revenue={"Actual": revenue},
            model_assumptions={
                "Expected Operating Margin": f"{margin_expected * 100:.1f}%",
                "Actual Operating Margin": f"{margin_actual * 100:.1f}%",
                "Shares Outstanding": f"{shares}M"
            }
        )

        distractors = [
            f"Margin variance contributed ${abs(eps_impact * 2):.2f} per share",
            f"Margin variance had no material impact",
            f"Margin variance contributed ${abs(eps_impact / 2):.2f} per share"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} reported revenue of ${revenue:.0f}M with operating margin of "
                     f"{margin_actual * 100:.1f}% versus expected {margin_expected * 100:.1f}%. "
                     f"With {shares}M shares outstanding, what was the EPS impact of the margin variance?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Margin variance: {(margin_actual - margin_expected) * 100:.1f}pp. "
                       f"Impact on operating income: ${(margin_actual - margin_expected) * revenue:.1f}M. "
                       f"Per share: ${eps_impact:.2f}",
            tags=["earnings", "margin", "variance-analysis", "eps-impact"]
        )
