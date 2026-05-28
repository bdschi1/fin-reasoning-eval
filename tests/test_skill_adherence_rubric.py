"""Tests for evaluation.rubric_scoring.build_skill_adherence_criteria."""

from __future__ import annotations

import pytest

from evaluation.rubric_scoring import (
    OVERCONFIDENT_PHRASES,
    RUBRIC_CATEGORIES,
    RubricGrader,
    build_skill_adherence_criteria,
    contains_overconfident_language,
)


def test_skill_adherence_category_registered():
    assert "skill_adherence" in RUBRIC_CATEGORIES


def test_builder_emits_five_criteria():
    criteria = build_skill_adherence_criteria(
        skill_slug="dcf-model",
        conventions=["Use live formulas", "Odd-size sensitivity tables"],
        output_schema="Executive summary + DCF tab + WACC tab",
    )
    assert len(criteria) == 5
    for c in criteria:
        assert c.category == "skill_adherence"
        assert c.weight >= 1
        assert c.id.startswith("SA_DCF_MODEL")


def test_builder_weights_total_twelve():
    criteria = build_skill_adherence_criteria(
        skill_slug="dcf-model",
        conventions=["rule"],
        output_schema="",
    )
    assert sum(c.weight for c in criteria) == 12


def test_builder_ids_are_unique_across_skills():
    a = build_skill_adherence_criteria(skill_slug="dcf-model")
    b = build_skill_adherence_criteria(skill_slug="comps-analysis")
    ids_a = {c.id for c in a}
    ids_b = {c.id for c in b}
    assert ids_a.isdisjoint(ids_b)


def test_probabilistic_criterion_present():
    criteria = build_skill_adherence_criteria(skill_slug="ic-memo")
    probabilistic = [c for c in criteria if c.id.endswith("_PROBABILISTIC")]
    assert len(probabilistic) == 1
    assert "probabilistic" in probabilistic[0].description.lower()


def test_rubric_grader_scores_skill_adherence_category():
    criteria = build_skill_adherence_criteria(skill_slug="dcf-model")
    grader = RubricGrader(criteria=criteria)

    judgments = {c.id: True for c in criteria}
    result = grader.score(judgments)

    assert "skill_adherence" in result.category_scores
    assert result.category_scores["skill_adherence"].earned == 12
    assert result.overall_pct == 100.0

    judgments[criteria[0].id] = False
    result = grader.score(judgments)
    assert result.overall_pct < 100.0


@pytest.mark.parametrize(
    "phrase",
    [
        "This investment is 100% correct.",
        "The return is guaranteed.",
        "The position will definitely outperform.",
        "There is no risk of capital loss.",
        "Certain to deliver alpha.",
    ],
)
def test_contains_overconfident_language_positive(phrase):
    assert contains_overconfident_language(phrase)


@pytest.mark.parametrize(
    "phrase",
    [
        "The base case suggests a 60% probability of outperformance.",
        "Execution risk remains material.",
        "",
    ],
)
def test_contains_overconfident_language_negative(phrase):
    assert not contains_overconfident_language(phrase)


def test_overconfident_phrase_list_nonempty():
    assert len(OVERCONFIDENT_PHRASES) >= 5
    assert all(p and p == p.lower() for p in OVERCONFIDENT_PHRASES)
