"""Adversarial variant generator — Phase 3 preparation.

Goal: produce equivalence-preserving perturbations of existing benchmark
problems so we can measure a model's consistency under light noise. This
module ships the skeleton plus a single variant type (numeric noise on
numbers embedded in the question/context). Additional variant types
(unit swap, ticker swap, year shift, option reorder) are scaffolded but
not implemented — Phase 3 lands the remaining types.

Design constraint: a variant must not flip the correct answer. Numeric
noise applies a small relative perturbation to raw numbers, chosen small
enough that a multiple-choice problem's bucketed answer remains valid
(we check this at consistency-score time, not at generation time).

Usage::

    from evaluation.adversarial import generate_numeric_noise_variant
    variant = generate_numeric_noise_variant(problem, seed=42, noise_pct=0.01)
"""

from __future__ import annotations

import copy
import random
import re
from dataclasses import dataclass, field
from typing import Any, Optional

# Numbers that appear inside tickers or dates should never be perturbed.
_PROTECTED_PATTERNS = [
    re.compile(r"\b20\d\d\b"),          # years 2000..2099
    re.compile(r"\b19\d\d\b"),          # years 1900..1999
    re.compile(r"\bQ[1-4]\b"),          # quarters
    re.compile(r"\b[A-Z]{1,5}\d*\b"),   # ticker-like tokens
]

_NUMBER_RE = re.compile(
    r"(?<![A-Za-z_])-?\d+(?:\.\d+)?(?![A-Za-z_])"
)


@dataclass
class Variant:
    """One adversarial variant of a source problem."""

    original_id: str
    variant_id: str
    variant_type: str
    question: str
    context: str
    options: list[dict] = field(default_factory=list)
    # Fields copied unchanged from the source problem.
    category: str = ""
    difficulty: str = ""
    answer_type: str = "multiple_choice"
    correct_answer: str = ""
    explanation: str = ""
    reasoning_steps: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    # Provenance: how we perturbed the source.
    perturbations: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.variant_id,
            "original_id": self.original_id,
            "variant_type": self.variant_type,
            "category": self.category,
            "difficulty": self.difficulty,
            "question": self.question,
            "context": self.context,
            "answer_type": self.answer_type,
            "correct_answer": self.correct_answer,
            "options": self.options,
            "explanation": self.explanation,
            "reasoning_steps": self.reasoning_steps,
            "tags": self.tags,
            "perturbations": self.perturbations,
        }


def _token_is_protected(text: str, start: int, end: int) -> bool:
    """Return True when the substring [start:end] sits inside a protected
    pattern (year, ticker, quarter)."""
    for pat in _PROTECTED_PATTERNS:
        for m in pat.finditer(text):
            if m.start() <= start and end <= m.end():
                return True
    return False


def _perturb_number(value: str, noise_pct: float, rng: random.Random) -> str:
    """Return the input number text perturbed by at most ``noise_pct``.

    Preserves decimal precision — a value of ``2.35`` stays 2 dp.
    """
    try:
        f = float(value)
    except ValueError:
        return value
    if f == 0:
        return value
    delta = rng.uniform(-noise_pct, noise_pct)
    new = f * (1.0 + delta)
    if "." in value:
        decimals = len(value.split(".")[1])
        return f"{new:.{decimals}f}"
    # integer-looking inputs stay integer-looking.
    return f"{int(round(new))}"


def _perturb_numbers_in_text(
    text: str, noise_pct: float, rng: random.Random
) -> tuple[str, list[dict[str, Any]]]:
    """Replace in-line numbers with ``noise_pct`` perturbations.

    Returns the perturbed text and a provenance log of (before, after).
    """
    perturbations: list[dict[str, Any]] = []
    result_chars: list[str] = []
    pos = 0
    for m in _NUMBER_RE.finditer(text):
        result_chars.append(text[pos : m.start()])
        token = m.group(0)
        if _token_is_protected(text, m.start(), m.end()):
            result_chars.append(token)
        else:
            new_val = _perturb_number(token, noise_pct, rng)
            if new_val != token:
                perturbations.append({"before": token, "after": new_val})
            result_chars.append(new_val)
        pos = m.end()
    result_chars.append(text[pos:])
    return "".join(result_chars), perturbations


def generate_numeric_noise_variant(
    problem: dict[str, Any],
    seed: Optional[int] = None,
    noise_pct: float = 0.01,
    variant_suffix: str = "nn1",
) -> Variant:
    """Create one variant with small relative noise on numeric literals.

    Args:
        problem: source benchmark problem dict (as in
            ``financial_reasoning_benchmark.json``).
        seed: PRNG seed for reproducibility.
        noise_pct: maximum relative perturbation (e.g. 0.01 = +/-1%).
        variant_suffix: appended to the original id to build the
            variant id.
    """
    rng = random.Random(seed)
    q, qp = _perturb_numbers_in_text(problem.get("question", ""), noise_pct, rng)
    c, cp = _perturb_numbers_in_text(problem.get("context", ""), noise_pct, rng)
    perturbations = qp + cp

    options = copy.deepcopy(problem.get("options") or problem.get("answer_options") or [])

    return Variant(
        original_id=problem.get("id", ""),
        variant_id=f"{problem.get('id', '')}__{variant_suffix}",
        variant_type="numeric_noise",
        question=q,
        context=c,
        options=options,
        category=problem.get("category", ""),
        difficulty=problem.get("difficulty", ""),
        answer_type=problem.get("answer_type", "multiple_choice"),
        correct_answer=problem.get("correct_answer", ""),
        explanation=problem.get("explanation", ""),
        reasoning_steps=list(problem.get("reasoning_steps", [])),
        tags=list(problem.get("tags", [])) + ["adversarial", "numeric_noise"],
        perturbations=perturbations,
    )


# Stubs for Phase 3 variant types — intentionally not implemented yet.

def generate_unit_swap_variant(*_args, **_kwargs) -> Variant:  # pragma: no cover
    raise NotImplementedError(
        "unit_swap variant is a Phase 3 deliverable"
    )


def generate_year_shift_variant(*_args, **_kwargs) -> Variant:  # pragma: no cover
    raise NotImplementedError(
        "year_shift variant is a Phase 3 deliverable"
    )


def generate_ticker_swap_variant(*_args, **_kwargs) -> Variant:  # pragma: no cover
    raise NotImplementedError(
        "ticker_swap variant is a Phase 3 deliverable"
    )


def generate_option_reorder_variant(*_args, **_kwargs) -> Variant:  # pragma: no cover
    raise NotImplementedError(
        "option_reorder variant is a Phase 3 deliverable"
    )


def compute_consistency_score(
    original_answer: str,
    variant_answer: str,
) -> float:
    """Return 1.0 when the answers are equivalent, 0.0 otherwise.

    Placeholder — Phase 3 replaces this with semantic-equivalence logic
    that handles numeric tolerance and option-text fuzziness.
    """
    if not original_answer or not variant_answer:
        return 0.0
    return 1.0 if original_answer.strip() == variant_answer.strip() else 0.0
