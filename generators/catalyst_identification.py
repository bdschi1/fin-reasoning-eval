"""
Catalyst Identification Problem Generator

Generates problems testing ability to:
- Identify potential stock catalysts
- Assess catalyst timing and probability
- Evaluate catalyst materiality
- Understand catalyst dependencies
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


class CatalystIdentificationGenerator(BaseGenerator):
    """Generator for catalyst identification problems."""

    @property
    def category(self) -> ProblemCategory:
        return ProblemCategory.CATALYST_ID

    # Catalyst templates by sector
    SECTOR_CATALYSTS = {
        "Technology": [
            "Product launch", "Customer win", "Margin expansion",
            "M&A announcement", "AI integration", "Cloud migration",
            "Subscription transition", "Geographic expansion"
        ],
        "Healthcare": [
            "FDA approval", "Clinical trial results", "Patent extension",
            "Drug pricing resolution", "Partnership announcement",
            "Pipeline advancement", "Regulatory clearance"
        ],
        "Financials": [
            "Interest rate decision", "Capital return program",
            "Asset quality improvement", "Loan growth acceleration",
            "Cost restructuring", "Regulatory approval"
        ],
        "Consumer Discretionary": [
            "Same-store sales acceleration", "E-commerce growth",
            "New store openings", "Brand partnership", "Pricing power",
            "International expansion", "Market share gain"
        ],
        "Energy": [
            "Production growth", "Cost reduction", "Asset sale",
            "Commodity price movement", "Drilling results",
            "Infrastructure project", "Regulatory approval"
        ],
        "Industrials": [
            "Order book growth", "Backlog conversion",
            "Margin improvement", "Restructuring completion",
            "Infrastructure spending", "Supply chain normalization"
        ]
    }

    def generate_one(self, difficulty: Difficulty) -> Problem:
        """Generate a single catalyst identification problem."""
        problem_type = random.choice([
            'identify_catalyst',
            'catalyst_timing',
            'catalyst_magnitude',
            'catalyst_probability',
            'catalyst_hierarchy',
            'negative_catalyst'
        ])

        generator_map = {
            'identify_catalyst': self._generate_identify_problem,
            'catalyst_timing': self._generate_timing_problem,
            'catalyst_magnitude': self._generate_magnitude_problem,
            'catalyst_probability': self._generate_probability_problem,
            'catalyst_hierarchy': self._generate_hierarchy_problem,
            'negative_catalyst': self._generate_negative_catalyst_problem,
        }

        return generator_map[problem_type](difficulty)

    def _generate_identify_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about identifying the most likely catalyst."""
        sector = random.choice(list(self.SECTOR_CATALYSTS.keys()))
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        catalysts = self.SECTOR_CATALYSTS[sector]

        if difficulty == Difficulty.EASY:
            # Clear primary catalyst
            primary_catalyst = random.choice(catalysts[:3])
            context_clue = f"Management has highlighted {primary_catalyst.lower()} as the key focus for the year."
            correct = f"{primary_catalyst} - directly cited by management"
        elif difficulty == Difficulty.MEDIUM:
            # Need to infer from data
            primary_catalyst = random.choice(catalysts[:4])
            context_clue = f"R&D spending increased 40% with focus on next-generation products."
            correct = f"{primary_catalyst} - implied by investment priorities"
        elif difficulty == Difficulty.HARD:
            # Multiple plausible catalysts
            primary_catalyst = catalysts[0]
            context_clue = f"Company pursuing multiple strategic initiatives simultaneously."
            correct = f"{primary_catalyst} - highest probability based on timeline and execution history"
        else:
            # Need to weigh complex factors
            primary_catalyst = random.choice(catalysts[:2])
            context_clue = f"Regulatory and operational milestones both expected in H2."
            correct = f"{primary_catalyst} - best risk-adjusted return profile among competing catalysts"

        # Generate distractor catalysts
        other_catalysts = [c for c in catalysts if c != primary_catalyst][:3]

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            recent_news=[context_clue],
            model_assumptions={
                "Sector": sector,
                "Potential Catalysts": ", ".join(catalysts[:4])
            }
        )

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"Given the following context for {company} ({sector}): '{context_clue}' "
                     f"What is the most likely near-term catalyst?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(
                correct,
                [f"{c} - potential catalyst" for c in other_catalysts]
            ),
            explanation=f"In {sector}, {primary_catalyst.lower()} is often the most impactful catalyst. "
                       f"The context clue '{context_clue}' points to this as the primary focus.",
            tags=["catalyst", "identification", sector.lower()]
        )

    def _generate_timing_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about catalyst timing assessment."""
        sector = random.choice(list(self.SECTOR_CATALYSTS.keys()))
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            catalyst = "Earnings announcement"
            timing = "Q1 2025"
            correct = f"Near-term (1-3 months) - {catalyst} in {timing}"
        elif difficulty == Difficulty.MEDIUM:
            catalyst = "FDA approval decision"
            timing = "PDUFA date August 2025"
            correct = f"Medium-term (6-9 months) - {catalyst} has defined regulatory timeline"
        elif difficulty == Difficulty.HARD:
            catalyst = "New product launch"
            timing = "management guided to H2 2025"
            correct = f"Medium-term with uncertainty - product launches often delayed 1-2 quarters"
        else:
            catalyst = "Strategic review outcome"
            timing = "ongoing"
            correct = f"Unknown timing - strategic processes can take 6-18 months with no defined endpoint"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            recent_news=[f"{catalyst}: {timing}"],
            model_assumptions={
                "Catalyst": catalyst,
                "Stated Timeline": timing
            }
        )

        distractors = [
            f"Near-term (1-3 months) - imminent resolution",
            f"Long-term (12+ months) - extended process",
            f"Timing uncertain but likely Q2 2025"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} has a pending {catalyst.lower()} with {timing}. "
                     f"How would you characterize the catalyst timing?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Catalyst timing assessment requires understanding both stated timelines "
                       f"and historical execution. {catalyst} with {timing} implies {correct.split(' - ')[0]}.",
            tags=["catalyst", "timing", "assessment"]
        )

    def _generate_magnitude_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about catalyst impact magnitude."""
        sector = random.choice(list(self.SECTOR_CATALYSTS.keys()))
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        stock_price = round(random.uniform(30, 100), 0)
        market_cap = round(random.uniform(5, 50), 1)  # billions

        if difficulty == Difficulty.EASY:
            catalyst = "Major product FDA approval"
            revenue_impact = 500  # millions
            margin_impact = 5  # percentage points
            correct = f"Material - ${revenue_impact}M revenue opportunity (~{revenue_impact/market_cap/10:.0f}% of market cap)"
        elif difficulty == Difficulty.MEDIUM:
            catalyst = "Customer contract win"
            revenue_impact = 80
            margin_impact = 1
            correct = f"Modest - ${revenue_impact}M contract is meaningful but not transformational"
        elif difficulty == Difficulty.HARD:
            catalyst = "Operational efficiency program"
            revenue_impact = 0
            margin_impact = 2
            correct = f"Moderate - {margin_impact}pp margin expansion could add ${market_cap * 10 * margin_impact / 100:.0f}B to value"
        else:
            catalyst = "Strategic partnership announcement"
            revenue_impact = 150
            margin_impact = -1
            correct = f"Mixed - ${revenue_impact}M revenue but margin dilutive, net impact modest"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            market_cap=f"${market_cap}B",
            model_assumptions={
                "Current Stock Price": f"${stock_price}",
                "Market Cap": f"${market_cap}B",
                "Catalyst": catalyst,
                "Revenue Impact": f"${revenue_impact}M",
                "Margin Impact": f"{margin_impact:+.0f}pp"
            }
        )

        distractors = [
            f"Transformational - could double the stock",
            f"Immaterial - less than 1% of value",
            f"Negative - will destroy shareholder value"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} (market cap: ${market_cap}B) has a potential {catalyst.lower()} "
                     f"with estimated revenue impact of ${revenue_impact}M and margin impact of {margin_impact:+.0f}pp. "
                     f"How material is this catalyst?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Catalyst materiality is assessed relative to market cap. "
                       f"${revenue_impact}M revenue for a ${market_cap}B company represents "
                       f"{revenue_impact/market_cap/10:.1f}% of market cap.",
            tags=["catalyst", "magnitude", "materiality"]
        )

    def _generate_probability_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about catalyst probability assessment."""
        sector = random.choice(["Healthcare", "Technology", "Energy"])
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        if difficulty == Difficulty.EASY:
            catalyst = "Phase 3 trial results"
            data_points = ["Phase 2 showed 95% efficacy", "Competitor failed Phase 3", "Large patient population"]
            correct = f"Moderate probability (40-60%) - strong Phase 2 but competitor failure raises bar"
        elif difficulty == Difficulty.MEDIUM:
            catalyst = "Acquisition closing"
            data_points = ["Deal announced", "Regulatory review pending", "Financing committed"]
            correct = f"High probability (70-85%) - definitive agreement but regulatory risk remains"
        elif difficulty == Difficulty.HARD:
            catalyst = "New product adoption"
            data_points = ["Product launched", "Early reviews positive", "Competitive response unknown"]
            correct = f"Moderate probability (50-65%) - execution risk and competitive response uncertain"
        else:
            catalyst = "Strategic alternatives process"
            data_points = ["Review initiated", "Activist involved", "Market conditions volatile"]
            correct = f"Low-moderate probability (25-45%) - many possible outcomes, deal not assured"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            recent_news=data_points,
            model_assumptions={
                "Catalyst": catalyst,
                "Key Data Points": "; ".join(data_points)
            }
        )

        distractors = [
            "Very high probability (>90%) - essentially certain",
            "Low probability (<20%) - unlikely to occur",
            "Equal probability across all outcomes"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} is awaiting {catalyst.lower()}. Key data points: {'; '.join(data_points)}. "
                     f"What probability would you assign to a positive outcome?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Catalyst probability assessment requires weighing multiple factors. "
                       f"For {catalyst}, the data points suggest {correct.split(' - ')[0].lower()}.",
            tags=["catalyst", "probability", "assessment"]
        )

    def _generate_hierarchy_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about prioritizing multiple catalysts."""
        sector = random.choice(list(self.SECTOR_CATALYSTS.keys()))
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        catalysts = self.SECTOR_CATALYSTS[sector][:4]

        if difficulty == Difficulty.EASY:
            catalyst_data = [
                {"name": catalysts[0], "probability": 0.8, "impact": "High", "timing": "Q1"},
                {"name": catalysts[1], "probability": 0.3, "impact": "Medium", "timing": "Q2"},
                {"name": catalysts[2], "probability": 0.5, "impact": "Low", "timing": "Q3"},
            ]
            correct = f"1. {catalysts[0]} - highest probability × impact combination"
        elif difficulty == Difficulty.MEDIUM:
            catalyst_data = [
                {"name": catalysts[0], "probability": 0.4, "impact": "Very High", "timing": "Q2"},
                {"name": catalysts[1], "probability": 0.7, "impact": "Medium", "timing": "Q1"},
                {"name": catalysts[2], "probability": 0.5, "impact": "High", "timing": "Q2"},
            ]
            correct = f"1. {catalysts[0]} - expected value highest despite lower probability"
        elif difficulty == Difficulty.HARD:
            catalyst_data = [
                {"name": catalysts[0], "probability": 0.5, "impact": "High", "timing": "Q1"},
                {"name": catalysts[1], "probability": 0.5, "impact": "High", "timing": "Q2"},
                {"name": catalysts[2], "probability": 0.6, "impact": "Medium", "timing": "Q1"},
            ]
            correct = f"1. {catalysts[0]} - equal expected value but earlier timing breaks tie"
        else:
            catalyst_data = [
                {"name": catalysts[0], "probability": 0.6, "impact": "High", "timing": "Q2"},
                {"name": catalysts[1], "probability": 0.8, "impact": "Medium", "timing": "Q1"},
                {"name": catalysts[2], "probability": 0.4, "impact": "Very High", "timing": "Q3"},
                {"name": catalysts[3], "probability": 0.9, "impact": "Low", "timing": "Q1"},
            ]
            correct = f"1. {catalysts[2]} - highest risk-adjusted return despite lower probability"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            model_assumptions={
                "Catalyst Analysis": str(catalyst_data)
            }
        )

        # Use safe indexing for distractors
        distractor_cats = [c for c in catalysts if c != catalysts[0]][:2]
        distractors = [
            f"1. {distractor_cats[0] if distractor_cats else 'Alternative'} - should prioritize near-term catalysts",
            f"1. {distractor_cats[1] if len(distractor_cats) > 1 else 'Other option'} - highest probability most important",
            f"All equally weighted - cannot prioritize"
        ]

        catalyst_summary = "; ".join([
            f"{c['name']} ({c['probability']*100:.0f}% prob, {c['impact']} impact, {c['timing']})"
            for c in catalyst_data
        ])

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"{company} has multiple potential catalysts: {catalyst_summary}. "
                     f"How should these be prioritized?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"Catalyst prioritization uses expected value (probability × impact) "
                       f"with timing as tiebreaker. {correct.split(' - ')[1]}",
            tags=["catalyst", "prioritization", "hierarchy"]
        )

    def _generate_negative_catalyst_problem(self, difficulty: Difficulty) -> Problem:
        """Generate problem about identifying negative catalysts/risks."""
        sector = random.choice(list(self.SECTOR_CATALYSTS.keys()))
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)

        negative_catalysts = {
            "Technology": ["Customer churn", "Product delay", "Competitive entry", "Margin pressure"],
            "Healthcare": ["Clinical trial failure", "Patent cliff", "Pricing pressure", "Regulatory rejection"],
            "Financials": ["Credit deterioration", "Regulatory fine", "Rate compression", "Trading loss"],
            "Consumer Discretionary": ["Same-store sales decline", "Inventory write-off", "Store closures"],
            "Energy": ["Production decline", "Commodity price drop", "Asset impairment", "Environmental liability"]
        }

        sector_risks = negative_catalysts.get(sector, ["Earnings miss", "Guidance cut", "Management departure"])

        if difficulty == Difficulty.EASY:
            risk = sector_risks[0]
            signals = [f"Recent {risk.lower()} warning signs evident"]
            correct = f"Primary risk: {risk} - clear warning signals present"
        elif difficulty == Difficulty.MEDIUM:
            risk = sector_risks[1]
            signals = [f"Industry facing headwinds in {risk.lower().replace('_', ' ')}"]
            correct = f"Elevated risk: {risk} - sector-wide pressures"
        elif difficulty == Difficulty.HARD:
            risk = sector_risks[0]
            signals = ["Multiple risk factors present but mitigants in place"]
            correct = f"Moderate risk: {risk} - monitoring required despite mitigants"
        else:
            risk = sector_risks[2]
            signals = ["Complex risk environment with unclear probability"]
            correct = f"Uncertain risk: {risk} - limited visibility on timing and magnitude"

        context = FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            recent_news=signals,
            model_assumptions={
                "Sector": sector,
                "Identified Risks": ", ".join(sector_risks[:3])
            }
        )

        # Use safe indexing for alternative risk
        alt_risk = sector_risks[3] if len(sector_risks) > 3 else "Other risk factors"
        distractors = [
            f"Low risk - company well-positioned",
            f"Minimal risk - strong balance sheet provides buffer",
            f"{alt_risk} is the primary concern"
        ]

        return Problem(
            id="",
            category=self.category,
            difficulty=difficulty,
            question=f"For {company} ({sector}), with context '{signals[0]}', "
                     f"what is the primary downside catalyst to monitor?",
            context=context,
            answer_type=AnswerType.MULTIPLE_CHOICE,
            correct_answer=correct,
            answer_options=self._create_answer_options(correct, distractors),
            explanation=f"In {sector}, {risk.lower()} is a common downside catalyst. "
                       f"The signals suggest {correct.split(' - ')[1].lower()}.",
            tags=["catalyst", "risk", "downside", "negative"]
        )
