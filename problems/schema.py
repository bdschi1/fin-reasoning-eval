"""
Financial Reasoning Eval Benchmark - Problem Schema

Defines the structure for finance reasoning problems across categories:
- Earnings surprises
- DCF sanity checks
- Accounting red flags
- Catalyst identification
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Literal
from enum import Enum
import json
import hashlib
from datetime import datetime


class ProblemCategory(str, Enum):
    """Categories of financial reasoning problems."""
    EARNINGS_SURPRISE = "earnings_surprise"
    DCF_SANITY = "dcf_sanity_check"
    ACCOUNTING_RED_FLAG = "accounting_red_flag"
    CATALYST_ID = "catalyst_identification"
    FORMULA_AUDIT = "formula_audit"
    FINANCIAL_STATEMENT = "financial_statement_analysis"
    VALUATION = "valuation_analysis"
    RISK_ASSESSMENT = "risk_assessment"
    CROSS_ENTITY_QA = "cross_entity_qa"
    LONGITUDINAL_QA = "longitudinal_qa"


class Difficulty(str, Enum):
    """Problem difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    EXPERT = "expert"


class AnswerType(str, Enum):
    """Types of expected answers."""
    MULTIPLE_CHOICE = "multiple_choice"
    NUMERIC = "numeric"
    BOOLEAN = "boolean"
    FREE_TEXT = "free_text"
    RANKING = "ranking"
    MULTI_SELECT = "multi_select"


@dataclass
class FinancialContext:
    """Financial context provided with a problem."""
    company_name: str
    ticker: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[str] = None
    fiscal_year: Optional[str] = None

    # Financial data (can include any subset)
    revenue: Optional[dict] = None  # {"2023": 1000, "2024E": 1200}
    ebitda: Optional[dict] = None
    net_income: Optional[dict] = None
    eps: Optional[dict] = None
    free_cash_flow: Optional[dict] = None

    # Balance sheet items
    total_assets: Optional[dict] = None
    total_debt: Optional[dict] = None
    cash: Optional[dict] = None
    equity: Optional[dict] = None

    # Valuation metrics
    pe_ratio: Optional[float] = None
    ev_ebitda: Optional[float] = None
    price_to_book: Optional[float] = None

    # DCF-specific
    wacc: Optional[float] = None
    terminal_growth: Optional[float] = None
    discount_rate: Optional[float] = None

    # Additional context
    guidance: Optional[str] = None
    consensus_estimates: Optional[dict] = None
    recent_news: Optional[list[str]] = None
    model_assumptions: Optional[dict] = None
    formula_context: Optional[str] = None  # For formula audit problems


@dataclass
class AnswerOption:
    """A single answer option for multiple choice problems."""
    id: str
    text: str
    is_correct: bool = False


@dataclass
class Problem:
    """A single financial reasoning problem."""

    # Core identification
    id: str
    category: ProblemCategory
    difficulty: Difficulty

    # Problem content
    question: str
    context: FinancialContext
    answer_type: AnswerType

    # Answer specification
    correct_answer: str  # The correct answer (text, number, or option id)
    answer_options: Optional[list[AnswerOption]] = None  # For MC/multi-select
    answer_unit: Optional[str] = None  # e.g., "millions USD", "percentage"
    tolerance: Optional[float] = None  # For numeric answers

    # Explanation and reasoning
    explanation: str = ""  # Why this is the correct answer
    reasoning_steps: list[str] = field(default_factory=list)  # Step-by-step reasoning
    common_mistakes: list[str] = field(default_factory=list)  # Typical errors

    # Metadata
    source: Optional[str] = None  # Where the problem came from
    tags: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    version: str = "1.0"

    # Scoring metadata
    max_points: int = 1
    partial_credit: bool = False

    def __post_init__(self):
        """Generate ID if not provided."""
        if not self.id:
            self.id = self._generate_id()

    def _generate_id(self) -> str:
        """Generate a unique problem ID."""
        content = f"{self.category.value}:{self.question[:100]}:{self.correct_answer}"
        return hashlib.sha256(content.encode()).hexdigest()[:12]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        d['category'] = self.category.value
        d['difficulty'] = self.difficulty.value
        d['answer_type'] = self.answer_type.value
        return d

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> 'Problem':
        """Create Problem from dictionary."""
        # Convert enums
        data['category'] = ProblemCategory(data['category'])
        data['difficulty'] = Difficulty(data['difficulty'])
        data['answer_type'] = AnswerType(data['answer_type'])

        # Convert nested objects
        if isinstance(data.get('context'), dict):
            data['context'] = FinancialContext(**data['context'])

        if data.get('answer_options'):
            data['answer_options'] = [
                AnswerOption(**opt) if isinstance(opt, dict) else opt
                for opt in data['answer_options']
            ]

        return cls(**data)

    def format_prompt(self, include_options: bool = True) -> str:
        """Format the problem as a prompt for LLM evaluation."""
        prompt_parts = []

        # Context section
        ctx = self.context
        prompt_parts.append("## Financial Context")
        prompt_parts.append(f"Company: {ctx.company_name}")
        if ctx.ticker:
            prompt_parts.append(f"Ticker: {ctx.ticker}")
        if ctx.sector:
            prompt_parts.append(f"Sector: {ctx.sector}")

        # Add financial data if present
        financial_data = []
        if ctx.revenue:
            financial_data.append(f"Revenue: {ctx.revenue}")
        if ctx.ebitda:
            financial_data.append(f"EBITDA: {ctx.ebitda}")
        if ctx.net_income:
            financial_data.append(f"Net Income: {ctx.net_income}")
        if ctx.eps:
            financial_data.append(f"EPS: {ctx.eps}")
        if ctx.free_cash_flow:
            financial_data.append(f"Free Cash Flow: {ctx.free_cash_flow}")

        if financial_data:
            prompt_parts.append("\n### Financial Data")
            prompt_parts.extend(financial_data)

        # Valuation metrics
        valuation_data = []
        if ctx.pe_ratio:
            valuation_data.append(f"P/E Ratio: {ctx.pe_ratio}")
        if ctx.ev_ebitda:
            valuation_data.append(f"EV/EBITDA: {ctx.ev_ebitda}")
        if ctx.wacc:
            valuation_data.append(f"WACC: {ctx.wacc}%")
        if ctx.terminal_growth:
            valuation_data.append(f"Terminal Growth: {ctx.terminal_growth}%")

        if valuation_data:
            prompt_parts.append("\n### Valuation Metrics")
            prompt_parts.extend(valuation_data)

        # Additional context
        if ctx.guidance:
            prompt_parts.append(f"\n### Company Guidance\n{ctx.guidance}")
        if ctx.recent_news:
            prompt_parts.append("\n### Recent News")
            for news in ctx.recent_news:
                prompt_parts.append(f"- {news}")
        if ctx.formula_context:
            prompt_parts.append(f"\n### Formula/Model Context\n{ctx.formula_context}")

        # Question
        prompt_parts.append(f"\n## Question\n{self.question}")

        # Answer options for MC
        if include_options and self.answer_options:
            prompt_parts.append("\n### Options")
            for opt in self.answer_options:
                prompt_parts.append(f"{opt.id}. {opt.text}")

        return "\n".join(prompt_parts)


@dataclass
class ProblemSet:
    """A collection of problems forming a benchmark dataset."""

    name: str
    description: str
    problems: list[Problem]
    version: str = "1.0"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    # Metadata
    total_problems: int = 0
    category_distribution: dict = field(default_factory=dict)
    difficulty_distribution: dict = field(default_factory=dict)

    def __post_init__(self):
        self.total_problems = len(self.problems)
        self._compute_distributions()

    def _compute_distributions(self):
        """Compute category and difficulty distributions."""
        self.category_distribution = {}
        self.difficulty_distribution = {}

        for problem in self.problems:
            cat = problem.category.value
            diff = problem.difficulty.value

            self.category_distribution[cat] = self.category_distribution.get(cat, 0) + 1
            self.difficulty_distribution[diff] = self.difficulty_distribution.get(diff, 0) + 1

    def filter_by_category(self, category: ProblemCategory) -> 'ProblemSet':
        """Return a new ProblemSet filtered by category."""
        filtered = [p for p in self.problems if p.category == category]
        return ProblemSet(
            name=f"{self.name}_{category.value}",
            description=f"Filtered by {category.value}",
            problems=filtered,
            version=self.version
        )

    def filter_by_difficulty(self, difficulty: Difficulty) -> 'ProblemSet':
        """Return a new ProblemSet filtered by difficulty."""
        filtered = [p for p in self.problems if p.difficulty == difficulty]
        return ProblemSet(
            name=f"{self.name}_{difficulty.value}",
            description=f"Filtered by {difficulty.value}",
            problems=filtered,
            version=self.version
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'created_at': self.created_at,
            'total_problems': self.total_problems,
            'category_distribution': self.category_distribution,
            'difficulty_distribution': self.difficulty_distribution,
            'problems': [p.to_dict() for p in self.problems]
        }

    def to_json(self, filepath: str):
        """Save to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def from_json(cls, filepath: str) -> 'ProblemSet':
        """Load from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        problems = [Problem.from_dict(p) for p in data['problems']]
        return cls(
            name=data['name'],
            description=data['description'],
            problems=problems,
            version=data.get('version', '1.0'),
            created_at=data.get('created_at', datetime.utcnow().isoformat())
        )
