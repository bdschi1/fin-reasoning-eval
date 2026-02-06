"""
Base Generator for Financial Reasoning Problems

Provides common utilities and structure for all problem generators.
"""

from abc import ABC, abstractmethod
import random
from typing import Optional

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    np = None

from problems import (
    Problem,
    ProblemSet,
    ProblemCategory,
    Difficulty,
    AnswerType,
    FinancialContext,
    AnswerOption,
)


class BaseGenerator(ABC):
    """Abstract base class for problem generators."""

    # Common company data for generating realistic problems
    SECTORS = [
        "Technology", "Healthcare", "Financials", "Consumer Discretionary",
        "Consumer Staples", "Energy", "Materials", "Industrials",
        "Real Estate", "Utilities", "Communication Services"
    ]

    COMPANY_PREFIXES = [
        "Apex", "Nexus", "Pinnacle", "Summit", "Vertex", "Zenith",
        "Atlas", "Beacon", "Catalyst", "Dynamic", "Eclipse", "Frontier",
        "Global", "Horizon", "Ionic", "Jupiter", "Kinetic", "Lunar",
        "Meridian", "Nova", "Omega", "Prism", "Quantum", "Radiant",
        "Stellar", "Titan", "Ultra", "Vector", "Wavelength", "Xenon"
    ]

    COMPANY_SUFFIXES = {
        "Technology": ["Tech", "Systems", "Solutions", "Digital", "Software", "AI"],
        "Healthcare": ["Therapeutics", "Pharma", "BioSciences", "Medical", "Health"],
        "Financials": ["Capital", "Financial", "Holdings", "Investments", "Bank"],
        "Consumer Discretionary": ["Brands", "Retail", "Lifestyle", "Consumer"],
        "Consumer Staples": ["Foods", "Consumer Products", "Essentials"],
        "Energy": ["Energy", "Power", "Resources", "Oil & Gas"],
        "Materials": ["Materials", "Chemicals", "Mining", "Resources"],
        "Industrials": ["Industries", "Manufacturing", "Engineering"],
        "Real Estate": ["Properties", "REIT", "Real Estate", "Development"],
        "Utilities": ["Utilities", "Power", "Electric", "Gas"],
        "Communication Services": ["Media", "Communications", "Entertainment"]
    }

    def __init__(self, seed: Optional[int] = None):
        """Initialize generator with optional random seed."""
        self.seed = seed
        if seed is not None:
            random.seed(seed)
            if NUMPY_AVAILABLE:
                np.random.seed(seed)

    @property
    @abstractmethod
    def category(self) -> ProblemCategory:
        """Return the problem category this generator produces."""
        pass

    @abstractmethod
    def generate_one(self, difficulty: Difficulty) -> Problem:
        """Generate a single problem of specified difficulty."""
        pass

    def generate_batch(
        self,
        count: int,
        difficulty_distribution: Optional[dict[Difficulty, float]] = None
    ) -> list[Problem]:
        """
        Generate a batch of problems with specified difficulty distribution.

        Args:
            count: Number of problems to generate
            difficulty_distribution: Dict mapping Difficulty to probability
                                    (defaults to uniform distribution)

        Returns:
            List of generated problems
        """
        if difficulty_distribution is None:
            difficulty_distribution = {
                Difficulty.EASY: 0.25,
                Difficulty.MEDIUM: 0.35,
                Difficulty.HARD: 0.30,
                Difficulty.EXPERT: 0.10
            }

        # Normalize probabilities
        total = sum(difficulty_distribution.values())
        probs = [difficulty_distribution.get(d, 0) / total for d in Difficulty]

        problems = []
        for _ in range(count):
            difficulty = random.choices(list(Difficulty), weights=probs)[0]
            problem = self.generate_one(difficulty)
            problems.append(problem)

        return problems

    def generate_problem_set(
        self,
        name: str,
        count: int,
        description: Optional[str] = None
    ) -> ProblemSet:
        """Generate a complete problem set."""
        problems = self.generate_batch(count)
        return ProblemSet(
            name=name,
            description=description or f"Generated {self.category.value} problems",
            problems=problems
        )

    # Utility methods for generating realistic financial data

    def _generate_company_name(self, sector: Optional[str] = None) -> str:
        """Generate a realistic company name."""
        sector = sector or random.choice(self.SECTORS)
        prefix = random.choice(self.COMPANY_PREFIXES)
        suffix = random.choice(self.COMPANY_SUFFIXES.get(sector, ["Corp"]))
        return f"{prefix} {suffix}"

    def _generate_ticker(self, company_name: str) -> str:
        """Generate a ticker symbol from company name."""
        words = company_name.split()
        if len(words) >= 2:
            ticker = words[0][:2].upper() + words[1][:2].upper()
        else:
            ticker = company_name[:4].upper()
        return ticker

    def _generate_revenue_series(
        self,
        base_revenue: float,
        years: int = 5,
        growth_rate: float = 0.10,
        volatility: float = 0.05
    ) -> dict[str, float]:
        """Generate a realistic revenue time series."""
        revenues = {}
        current = base_revenue

        # Historical years
        for i in range(years - 2, 0, -1):
            year = 2024 - i
            revenues[str(year)] = round(current, 1)
            growth = growth_rate + random.gauss(0, volatility)
            current = current * (1 + growth)

        # Current year
        revenues["2024"] = round(current, 1)

        # Projected years
        for i in range(1, 3):
            year = 2024 + i
            growth = growth_rate + random.gauss(0, volatility)
            current = current * (1 + growth)
            revenues[f"{year}E"] = round(current, 1)

        return revenues

    def _generate_margin_series(
        self,
        base_margin: float,
        years: int = 5,
        trend: float = 0.01,
        volatility: float = 0.02
    ) -> dict[str, float]:
        """Generate a realistic margin time series."""
        margins = {}
        current = base_margin

        for i in range(years - 2, 0, -1):
            year = 2024 - i
            margins[str(year)] = round(current * 100, 1)
            change = trend + random.gauss(0, volatility)
            current = max(0.01, min(0.50, current + change))

        margins["2024"] = round(current * 100, 1)

        for i in range(1, 3):
            year = 2024 + i
            change = trend + random.gauss(0, volatility)
            current = max(0.01, min(0.50, current + change))
            margins[f"{year}E"] = round(current * 100, 1)

        return margins

    def _generate_eps_series(
        self,
        base_eps: float,
        years: int = 5,
        growth_rate: float = 0.12,
        volatility: float = 0.08
    ) -> dict[str, float]:
        """Generate a realistic EPS time series."""
        eps_data = {}
        current = base_eps

        for i in range(years - 2, 0, -1):
            year = 2024 - i
            eps_data[str(year)] = round(current, 2)
            growth = growth_rate + random.gauss(0, volatility)
            current = current * (1 + growth)

        eps_data["2024"] = round(current, 2)

        for i in range(1, 3):
            year = 2024 + i
            growth = growth_rate + random.gauss(0, volatility)
            current = current * (1 + growth)
            eps_data[f"{year}E"] = round(current, 2)

        return eps_data

    def _generate_dcf_assumptions(
        self,
        difficulty: Difficulty
    ) -> dict:
        """Generate DCF model assumptions based on difficulty."""
        base_wacc = random.uniform(0.08, 0.12)
        base_tgr = random.uniform(0.02, 0.03)

        if difficulty == Difficulty.EASY:
            # Clear, reasonable assumptions
            return {
                'wacc': round(base_wacc, 3),
                'terminal_growth': round(base_tgr, 3),
                'projection_years': 5,
                'tax_rate': 0.25
            }
        elif difficulty == Difficulty.MEDIUM:
            # Some slightly off assumptions
            return {
                'wacc': round(base_wacc, 3),
                'terminal_growth': round(base_tgr + 0.01, 3),
                'projection_years': 7,
                'tax_rate': 0.21
            }
        elif difficulty == Difficulty.HARD:
            # Subtle errors to catch
            return {
                'wacc': round(base_wacc - 0.02, 3),  # Low WACC
                'terminal_growth': round(base_tgr + 0.02, 3),  # High TGR
                'projection_years': 10,
                'tax_rate': 0.15
            }
        else:  # EXPERT
            # Multiple subtle issues
            return {
                'wacc': round(base_wacc - 0.03, 3),  # Very low WACC
                'terminal_growth': round(base_tgr + 0.025, 3),  # TGR > GDP
                'projection_years': 15,  # Too long
                'tax_rate': 0.10,  # Unrealistic
                'terminal_multiple': 20  # Added complexity
            }

    def _create_answer_options(
        self,
        correct: str,
        distractors: list[str],
        shuffle: bool = True
    ) -> list[AnswerOption]:
        """Create answer options with correct answer and distractors."""
        options = [
            AnswerOption(id="A", text=correct, is_correct=True)
        ] + [
            AnswerOption(id=chr(66 + i), text=d, is_correct=False)
            for i, d in enumerate(distractors)
        ]

        if shuffle:
            random.shuffle(options)
            # Reassign IDs after shuffle
            for i, opt in enumerate(options):
                opt.id = chr(65 + i)

        return options

    def _format_currency(self, value: float, unit: str = "M") -> str:
        """Format a currency value."""
        if unit == "M":
            return f"${value:,.1f}M"
        elif unit == "B":
            return f"${value / 1000:,.2f}B"
        else:
            return f"${value:,.2f}"

    def _calculate_implied_growth(self, values: dict) -> float:
        """Calculate implied CAGR from a series of values."""
        sorted_years = sorted([k for k in values.keys() if not k.endswith('E')])
        if len(sorted_years) < 2:
            return 0

        start_year = sorted_years[0]
        end_year = sorted_years[-1]
        start_val = values[start_year]
        end_val = values[end_year]
        years = int(end_year) - int(start_year)

        if years > 0 and start_val > 0:
            return (end_val / start_val) ** (1 / years) - 1
        return 0
