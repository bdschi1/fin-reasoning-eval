"""Tests for PRBench-style rubric scoring and FLaME taxonomy alignment."""

import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent


# ── Rubric Scoring ────────────────────────────────────────────────────────

class TestRubricImports:
    def test_import_rubric_scoring(self):
        from evaluation.rubric_scoring import (  # noqa: F401
            RubricCriterion,
            RubricGrader,
            RubricResult,
            RUBRIC_CATEGORIES,
            DEFAULT_CRITERIA,
        )

    def test_rubric_scoring_file_exists(self):
        assert (REPO_ROOT / "evaluation" / "rubric_scoring.py").exists()


class TestRubricCriterion:
    def test_met_scores_weight(self):
        from evaluation.rubric_scoring import RubricCriterion
        c = RubricCriterion("T_001", "Test criterion", weight=3)
        assert c.score(True) == 3

    def test_not_met_scores_zero(self):
        from evaluation.rubric_scoring import RubricCriterion
        c = RubricCriterion("T_001", "Test criterion", weight=3)
        assert c.score(False) == 0

    def test_default_weight_is_one(self):
        from evaluation.rubric_scoring import RubricCriterion
        c = RubricCriterion("T_001", "Test")
        assert c.weight == 1


class TestRubricGrader:
    def test_default_criteria_loaded(self):
        from evaluation.rubric_scoring import RubricGrader
        grader = RubricGrader()
        assert len(grader.criteria) > 0

    def test_seven_categories(self):
        from evaluation.rubric_scoring import RubricGrader, RUBRIC_CATEGORIES
        grader = RubricGrader()
        assert len(grader.categories) == len(RUBRIC_CATEGORIES)

    def test_total_possible_positive(self):
        from evaluation.rubric_scoring import RubricGrader
        grader = RubricGrader()
        assert grader.total_possible > 0

    def test_all_met_scores_100(self):
        from evaluation.rubric_scoring import RubricGrader
        grader = RubricGrader()
        judgments = {c.id: True for c in grader.criteria}
        result = grader.score(judgments)
        assert result.overall_pct == pytest.approx(100.0)

    def test_none_met_scores_zero(self):
        from evaluation.rubric_scoring import RubricGrader
        grader = RubricGrader()
        judgments = {c.id: False for c in grader.criteria}
        result = grader.score(judgments)
        assert result.overall_pct == pytest.approx(0.0)

    def test_partial_scoring(self):
        from evaluation.rubric_scoring import RubricGrader
        grader = RubricGrader()
        # Meet only the first criterion in each category
        judgments = {}
        for cat_criteria in grader._by_category.values():
            if cat_criteria:
                judgments[cat_criteria[0].id] = True
        result = grader.score(judgments)
        assert 0.0 < result.overall_pct < 100.0

    def test_result_has_all_categories(self):
        from evaluation.rubric_scoring import RubricGrader
        grader = RubricGrader()
        judgments = {c.id: True for c in grader.criteria}
        result = grader.score(judgments)
        for cat in grader.categories:
            assert cat in result.category_scores

    def test_result_to_dict(self):
        from evaluation.rubric_scoring import RubricGrader
        grader = RubricGrader()
        judgments = {c.id: True for c in grader.criteria}
        result = grader.score(judgments)
        d = result.to_dict()
        assert "overall_score" in d
        assert "categories" in d
        assert isinstance(d["overall_score"], float)

    def test_empty_judgments(self):
        from evaluation.rubric_scoring import RubricGrader
        grader = RubricGrader()
        result = grader.score({})
        assert result.overall_pct == pytest.approx(0.0)

    def test_custom_criteria(self):
        from evaluation.rubric_scoring import RubricGrader, RubricCriterion
        criteria = [
            RubricCriterion("C1", "Criterion 1", weight=5, category="test"),
            RubricCriterion("C2", "Criterion 2", weight=3, category="test"),
        ]
        grader = RubricGrader(criteria)
        result = grader.score({"C1": True, "C2": False})
        assert result.overall_earned == 5
        assert result.overall_possible == 8


class TestCategoryScore:
    def test_pct_computation(self):
        from evaluation.rubric_scoring import CategoryScore
        cs = CategoryScore("test", earned=7, possible=10)
        assert cs.pct == pytest.approx(70.0)

    def test_pct_zero_possible(self):
        from evaluation.rubric_scoring import CategoryScore
        cs = CategoryScore("test", earned=0, possible=0)
        assert cs.pct == pytest.approx(0.0)


# ── FLaME Taxonomy Alignment ─────────────────────────────────────────────

class TestFLaMEImports:
    def test_import_flame(self):
        from evaluation.flame_alignment import (  # noqa: F401
            FLAME_CATEGORIES,
            CATEGORY_TO_FLAME,
            FINRATE_QA_PATHWAYS,
            analyze_coverage,
            get_flame_categories,
            get_finrate_pathway,
        )

    def test_flame_file_exists(self):
        assert (REPO_ROOT / "evaluation" / "flame_alignment.py").exists()


class TestFLaMECategories:
    def test_six_flame_categories(self):
        from evaluation.flame_alignment import FLAME_CATEGORIES
        assert len(FLAME_CATEGORIES) == 6

    def test_three_finrate_pathways(self):
        from evaluation.flame_alignment import FINRATE_QA_PATHWAYS
        assert len(FINRATE_QA_PATHWAYS) == 3

    def test_all_problem_categories_mapped(self):
        from evaluation.flame_alignment import CATEGORY_TO_FLAME
        from problems.schema import ProblemCategory
        for cat in ProblemCategory:
            assert cat.value in CATEGORY_TO_FLAME, f"{cat.value} not mapped to FLaME"

    def test_cross_entity_qa_mapped(self):
        from evaluation.flame_alignment import get_flame_categories
        cats = get_flame_categories("cross_entity_qa")
        assert "question_answering" in cats
        assert "information_retrieval" in cats

    def test_longitudinal_qa_mapped(self):
        from evaluation.flame_alignment import get_flame_categories
        cats = get_flame_categories("longitudinal_qa")
        assert "question_answering" in cats
        assert "causal_reasoning" in cats


class TestFLaMECoverage:
    def test_analyze_coverage(self):
        from evaluation.flame_alignment import analyze_coverage
        categories = [
            "earnings_surprise", "dcf_sanity_check",
            "cross_entity_qa", "longitudinal_qa",
        ]
        result = analyze_coverage(categories)
        assert result.total_problems == 4
        assert result.flame_coverage["question_answering"] >= 3

    def test_finrate_pathway_coverage(self):
        from evaluation.flame_alignment import analyze_coverage
        categories = ["cross_entity_qa", "longitudinal_qa", "earnings_surprise"]
        result = analyze_coverage(categories)
        assert result.finrate_coverage["cross_entity_qa"] == 1
        assert result.finrate_coverage["longitudinal_qa"] == 1
        assert result.finrate_coverage["detail_oriented_qa"] == 1

    def test_to_dict(self):
        from evaluation.flame_alignment import analyze_coverage
        result = analyze_coverage(["earnings_surprise"])
        d = result.to_dict()
        assert "flame_coverage" in d
        assert "finrate_coverage" in d
        assert "total_problems" in d

    def test_empty_coverage(self):
        from evaluation.flame_alignment import analyze_coverage
        result = analyze_coverage([])
        assert result.total_problems == 0

    def test_unmapped_category(self):
        from evaluation.flame_alignment import analyze_coverage
        result = analyze_coverage(["nonexistent_category"])
        assert result.unmapped == 1


class TestFinRATEPathways:
    def test_get_finrate_pathway(self):
        from evaluation.flame_alignment import get_finrate_pathway
        assert get_finrate_pathway("cross_entity_qa") == "cross_entity_qa"
        assert get_finrate_pathway("longitudinal_qa") == "longitudinal_qa"
        assert get_finrate_pathway("earnings_surprise") == "detail_oriented_qa"

    def test_default_pathway(self):
        from evaluation.flame_alignment import get_finrate_pathway
        assert get_finrate_pathway("unknown") == "detail_oriented_qa"


# ── New Problem Categories in Schema ──────────────────────────────────────

class TestNewProblemCategories:
    def test_cross_entity_category_exists(self):
        from problems.schema import ProblemCategory
        assert hasattr(ProblemCategory, "CROSS_ENTITY_QA")
        assert ProblemCategory.CROSS_ENTITY_QA.value == "cross_entity_qa"

    def test_longitudinal_category_exists(self):
        from problems.schema import ProblemCategory
        assert hasattr(ProblemCategory, "LONGITUDINAL_QA")
        assert ProblemCategory.LONGITUDINAL_QA.value == "longitudinal_qa"

    def test_total_categories_is_ten(self):
        from problems.schema import ProblemCategory
        assert len(ProblemCategory) == 10
