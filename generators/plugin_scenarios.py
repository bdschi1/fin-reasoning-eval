"""Plugin-derived free-text scenario generator.

Converts a parsed `SkillSpec` into a `Problem` with `answer_type=free_text`.
Maps each pilot skill to an existing ProblemCategory, injects synthetic
financial context, and records the skill provenance in tags and source.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Optional

from problems import (
    AnswerType,
    Difficulty,
    FinancialContext,
    Problem,
    ProblemCategory,
)

from .base import BaseGenerator
from .plugin_reader import SkillSpec, load_skill


# Map pilot skill slugs to existing ProblemCategory values.
SKILL_CATEGORY_MAP: dict[str, ProblemCategory] = {
    "dcf-model": ProblemCategory.DCF_SANITY,
    "comps-analysis": ProblemCategory.VALUATION,
    "lbo-model": ProblemCategory.VALUATION,
    "ic-memo": ProblemCategory.FINANCIAL_STATEMENT,
    "earnings-preview": ProblemCategory.EARNINGS_SURPRISE,
}


# Per-skill question templates. Each phrased as a free-text deliverable.
SKILL_QUESTION_TEMPLATES: dict[str, str] = {
    "dcf-model": (
        "Build a DCF valuation for {company} following the conventions of the "
        "`dcf-model` skill. Produce the five-year FCF projection, WACC "
        "derivation, terminal value (Gordon growth), enterprise-value bridge "
        "to equity value per share, and a 5x5 sensitivity table (WACC vs "
        "terminal growth) with a highlighted center cell matching the base "
        "case. State each assumption with a source note; use probabilistic "
        "language for directional conclusions."
    ),
    "comps-analysis": (
        "Produce a trading comparables analysis for {company} following the "
        "conventions of the `comps-analysis` skill. Select a defensible peer "
        "set (state inclusion criteria), compute current and next-twelve-"
        "month EV/EBITDA, EV/Revenue, and P/E multiples, surface median and "
        "mean, and apply the resulting multiples to {company}'s financials "
        "to produce an implied-value range. Flag outliers and state why each "
        "peer is comparable; use probabilistic language for valuation "
        "conclusions."
    ),
    "lbo-model": (
        "Construct an LBO analysis for {company} following the conventions "
        "of the `lbo-model` skill. Specify sources & uses, debt schedule "
        "(term loan + revolver), five-year operating projection, exit "
        "multiple assumption, and sponsor IRR and MOIC. Include a "
        "sensitivity on entry multiple vs exit multiple. State each "
        "assumption with its source; use probabilistic language for return "
        "conclusions."
    ),
    "ic-memo": (
        "Draft an investment-committee memo for a potential {company} "
        "investment, following the conventions of the `ic-memo` skill. "
        "Cover: deal summary, investment thesis, management assessment, "
        "market and competitive position, financial summary, valuation and "
        "returns, key risks and mitigants, and a recommendation. Use "
        "probabilistic language for the thesis and return outlook — no "
        "'guaranteed', 'definitely', or '100%' phrasing."
    ),
    "earnings-preview": (
        "Write an earnings preview for {company} following the conventions "
        "of the `earnings-preview` skill. Include: consensus expectations "
        "(revenue, EPS, key KPIs), buyside-vs-sellside setup, three things "
        "to watch, scenario analysis (beat / in-line / miss) with estimated "
        "stock reactions, and risk factors. Use probabilistic language for "
        "outcome likelihoods."
    ),
}


@dataclass
class PluginScenarioConfig:
    """Optional overrides for plugin-scenario generation."""

    seed: Optional[int] = None
    difficulty: Difficulty = Difficulty.HARD


class PluginScenarioGenerator(BaseGenerator):
    """Generator that emits free-text Problems derived from plugin skills."""

    def __init__(self, config: Optional[PluginScenarioConfig] = None):
        cfg = config or PluginScenarioConfig()
        super().__init__(seed=cfg.seed)
        self._config = cfg
        self._current_category: ProblemCategory = ProblemCategory.VALUATION

    @property
    def category(self) -> ProblemCategory:
        return self._current_category

    def generate_one(self, difficulty: Difficulty) -> Problem:
        """generate_one is not meaningful without a skill; use generate_from_skill."""
        raise NotImplementedError(
            "PluginScenarioGenerator requires a skill slug. "
            "Use generate_from_skill(slug) or generate_from_spec(spec)."
        )

    def generate_from_skill(self, slug: str) -> Problem:
        """Load the named skill and generate a scenario from it."""
        spec = load_skill(slug)
        return self.generate_from_spec(spec)

    def generate_from_spec(self, spec: SkillSpec) -> Problem:
        """Generate a Problem from an already-parsed SkillSpec."""
        category = SKILL_CATEGORY_MAP.get(spec.slug, ProblemCategory.VALUATION)
        self._current_category = category

        template = SKILL_QUESTION_TEMPLATES.get(
            spec.slug,
            (
                "Produce the deliverable described by the `{slug}` skill for "
                "{company}. Follow the skill's stated conventions and output "
                "schema, and use probabilistic language for conclusions."
            ),
        )

        context = self._synthetic_context(category)
        question = template.format(company=context.company_name, slug=spec.slug)

        reasoning_steps = self._reasoning_from_spec(spec)
        explanation = self._explanation_from_spec(spec)

        return Problem(
            id="",
            category=category,
            difficulty=self._config.difficulty,
            question=question,
            context=context,
            answer_type=AnswerType.FREE_TEXT,
            correct_answer="",
            answer_options=None,
            explanation=explanation,
            reasoning_steps=reasoning_steps,
            tags=[
                "plugin-derived",
                f"skill:{spec.slug}",
                f"plugin:{spec.plugin}",
            ],
            source=spec.source_ref,
            max_points=5,
            partial_credit=True,
        )

    def _synthetic_context(self, category: ProblemCategory) -> FinancialContext:
        sector = random.choice(self.SECTORS)
        company = self._generate_company_name(sector)
        ticker = self._generate_ticker(company)
        base_revenue = random.uniform(500.0, 5000.0)
        revenue = self._generate_revenue_series(base_revenue)
        ebitda = {
            year: round(value * random.uniform(0.18, 0.28), 1)
            for year, value in revenue.items()
        }
        eps = self._generate_eps_series(random.uniform(1.50, 6.00))
        fcf = {
            year: round(value * random.uniform(0.10, 0.18), 1)
            for year, value in revenue.items()
        }

        assumptions = self._generate_dcf_assumptions(self._config.difficulty)
        wacc = assumptions.get("wacc")
        tgr = assumptions.get("terminal_growth")

        guidance = (
            "Management reiterated the full-year revenue range and noted "
            "margin pressure from input costs offset by mix. Full-year EPS "
            "guidance left unchanged."
        )

        return FinancialContext(
            company_name=company,
            ticker=ticker,
            sector=sector,
            market_cap=f"${round(random.uniform(5.0, 50.0), 1)}B",
            fiscal_year="2024",
            revenue=revenue,
            ebitda=ebitda,
            eps=eps,
            free_cash_flow=fcf,
            wacc=wacc,
            terminal_growth=tgr,
            guidance=guidance,
            model_assumptions=assumptions,
        )

    def _reasoning_from_spec(self, spec: SkillSpec) -> list[str]:
        steps: list[str] = []
        if spec.output_schema:
            for line in spec.output_schema.splitlines():
                stripped = line.lstrip("-* \t").strip()
                if stripped and len(stripped) < 240:
                    steps.append(stripped)
                if len(steps) >= 8:
                    break
        if not steps and spec.conventions:
            steps = [c for c in spec.conventions[:6] if len(c) < 240]
        return steps

    def _explanation_from_spec(self, spec: SkillSpec) -> str:
        header = f"Skill: {spec.name} ({spec.source_ref})."
        if spec.description:
            header = f"{header} {spec.description}"
        if spec.conventions:
            joined = "; ".join(spec.conventions[:6])
            return f"{header}\n\nKey conventions: {joined}"
        return header
