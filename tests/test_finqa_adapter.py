"""Tests for the FinQA adapter (scripts/load_finqa.py)."""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from load_finqa import (
    render_table,
    extract_company,
    infer_difficulty,
    parse_program_string,
    count_operations,
    join_text,
    build_context,
    convert_example,
    build_problem_set,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


SAMPLE_TABLE = [
    ["", "2023", "2022", "2021"],
    ["Revenue", "1,200", "1,000", "850"],
    ["Net Income", "150", "120", "95"],
]

SAMPLE_FINQA_EXAMPLE = {
    "id": "AAPL/2023/page_42.pdf-1",
    "pre_text": ["The following table shows our revenue breakdown.",
                 "Revenue increased in all segments."],
    "post_text": ["Revenue increased primarily due to services growth."],
    "table": SAMPLE_TABLE,
    "qa": {
        "question": "What was the percent change in revenue from 2022 to 2023?",
        "program": "subtract(1200, 1000), divide(#0, 1000)",
        "gold_inds": [1],
        "exe_ans": 0.2,
        "explanation": "",
    },
}


# ── Table rendering ──────────────────────────────────────────────────────


class TestRenderTable:
    def test_basic_table(self):
        result = render_table(SAMPLE_TABLE)
        lines = result.split("\n")
        assert len(lines) == 4  # header + separator + 2 data rows
        assert "2023" in lines[0]
        assert "---" in lines[1]
        assert "Revenue" in lines[2]

    def test_empty_table(self):
        assert render_table([]) == ""
        assert render_table([[]]) == ""

    def test_single_row(self):
        result = render_table([["Col A", "Col B"]])
        assert "Col A" in result
        assert "---" in result

    def test_short_rows_padded(self):
        table = [["A", "B", "C"], ["x"]]
        result = render_table(table)
        lines = result.split("\n")
        assert lines[2].count("|") == lines[0].count("|")


# ── Company extraction ───────────────────────────────────────────────────


class TestExtractCompany:
    def test_standard_id(self):
        assert extract_company("ADI/2009/page_49.pdf-1") == "ADI"

    def test_ticker_only(self):
        assert extract_company("MSFT") == "MSFT"

    def test_empty_string(self):
        assert extract_company("") == ""

    def test_complex_path(self):
        assert extract_company("ABBV/2023/Q3/page_12.pdf-3") == "ABBV"


# ── Program parsing ──────────────────────────────────────────────────────


class TestParseProgramString:
    def test_single_op(self):
        steps = parse_program_string("subtract(5829, 5735)")
        assert steps == ["subtract(5829, 5735)"]

    def test_multi_op(self):
        steps = parse_program_string("subtract(92710000, 86842000), divide(#0, 86842000)")
        assert len(steps) == 2
        assert steps[0] == "subtract(92710000, 86842000)"
        assert steps[1] == "divide(#0, 86842000)"

    def test_three_ops(self):
        steps = parse_program_string("add(1, 2), multiply(#0, 3), divide(#1, 6)")
        assert len(steps) == 3

    def test_empty(self):
        assert parse_program_string("") == []
        assert parse_program_string(None) == []


class TestCountOperations:
    def test_single(self):
        assert count_operations("subtract(5829, 5735)") == 1

    def test_multi(self):
        assert count_operations("subtract(100, 50), divide(#0, 50)") == 2

    def test_empty(self):
        assert count_operations("") == 0
        assert count_operations(None) == 0


# ── Difficulty inference ─────────────────────────────────────────────────


class TestInferDifficulty:
    def test_single_op_easy(self):
        assert infer_difficulty("subtract(100, 50)") == "easy"

    def test_two_ops_medium(self):
        assert infer_difficulty("subtract(100, 50), divide(#0, 50)") == "medium"

    def test_three_ops_hard(self):
        assert infer_difficulty("add(1, 2), multiply(#0, 3), divide(#1, 6)") == "hard"

    def test_four_plus_expert(self):
        assert infer_difficulty("add(1, 2), add(3, 4), add(#0, #1), divide(#2, 2)") == "expert"

    def test_empty_program(self):
        assert infer_difficulty("") == "easy"


# ── Text joining ─────────────────────────────────────────────────────────


class TestJoinText:
    def test_list_of_strings(self):
        result = join_text(["Hello world.", "Second sentence."])
        assert result == "Hello world. Second sentence."

    def test_single_string(self):
        assert join_text("already a string") == "already a string"

    def test_empty_list(self):
        assert join_text([]) == ""

    def test_none(self):
        assert join_text(None) == ""


# ── Context building ─────────────────────────────────────────────────────


class TestBuildContext:
    def test_has_company(self):
        ctx = build_context(SAMPLE_FINQA_EXAMPLE)
        assert ctx["company_name"] == "AAPL"
        assert ctx["ticker"] == "AAPL"

    def test_has_filing_context(self):
        ctx = build_context(SAMPLE_FINQA_EXAMPLE)
        filing = ctx["model_assumptions"]["filing_context"]
        assert "revenue breakdown" in filing
        assert "Revenue" in filing
        assert "services growth" in filing

    def test_joins_pre_text_list(self):
        ctx = build_context(SAMPLE_FINQA_EXAMPLE)
        filing = ctx["model_assumptions"]["filing_context"]
        # Both pre_text paragraphs should be joined
        assert "all segments" in filing

    def test_all_financial_fields_none(self):
        ctx = build_context(SAMPLE_FINQA_EXAMPLE)
        for field in ["revenue", "ebitda", "net_income", "eps", "wacc"]:
            assert ctx[field] is None


# ── Full conversion ──────────────────────────────────────────────────────


class TestConvertExample:
    def test_basic_conversion(self):
        result = convert_example(SAMPLE_FINQA_EXAMPLE)
        assert result["id"] == "finqa_AAPL/2023/page_42.pdf-1"
        assert result["category"] == "financial_statement_analysis"
        assert result["difficulty"] == "medium"  # 2 ops
        assert result["answer_type"] == "numeric"
        assert result["correct_answer"] == "0.2"
        assert result["tolerance"] == 0.01
        assert result["source"] == "FinQA (Chen et al., 2021)"
        assert "finqa" in result["tags"]
        assert "real-filing" in result["tags"]

    def test_has_reasoning_steps(self):
        result = convert_example(SAMPLE_FINQA_EXAMPLE)
        assert len(result["reasoning_steps"]) == 2
        assert "subtract(1200, 1000)" in result["reasoning_steps"][0]

    def test_context_is_dict(self):
        result = convert_example(SAMPLE_FINQA_EXAMPLE)
        assert isinstance(result["context"], dict)
        assert result["context"]["company_name"] == "AAPL"

    def test_integer_answer(self):
        example = {**SAMPLE_FINQA_EXAMPLE, "qa": {**SAMPLE_FINQA_EXAMPLE["qa"], "exe_ans": 42}}
        result = convert_example(example)
        assert result["correct_answer"] == "42"

    def test_float_precision(self):
        example = {**SAMPLE_FINQA_EXAMPLE, "qa": {**SAMPLE_FINQA_EXAMPLE["qa"], "exe_ans": 0.333333}}
        result = convert_example(example)
        assert result["correct_answer"] == "0.333333"


# ── Problem set wrapper ──────────────────────────────────────────────────


class TestBuildProblemSet:
    def test_metadata(self):
        problems = [convert_example(SAMPLE_FINQA_EXAMPLE)]
        ps = build_problem_set(problems, "test")
        assert ps["name"] == "FinQA_test"
        assert ps["total_problems"] == 1
        assert "financial_statement_analysis" in ps["category_distribution"]
        assert "medium" in ps["difficulty_distribution"]
        assert "CC BY 4.0" in ps["description"]

    def test_valid_json(self):
        problems = [convert_example(SAMPLE_FINQA_EXAMPLE)]
        ps = build_problem_set(problems, "test")
        serialized = json.dumps(ps)
        loaded = json.loads(serialized)
        assert loaded["total_problems"] == 1
        assert len(loaded["problems"]) == 1


# ── Loader compatibility ─────────────────────────────────────────────────


class TestLoaderCompatibility:
    """Verify converted output matches schema expected by evaluation/dataset.py."""

    def test_problem_has_required_fields(self):
        result = convert_example(SAMPLE_FINQA_EXAMPLE)
        required = [
            "id", "category", "difficulty", "question", "context",
            "answer_type", "correct_answer", "answer_options",
            "explanation", "reasoning_steps", "tags",
        ]
        for field in required:
            assert field in result, f"Missing field: {field}"

    def test_context_dict_has_company_name(self):
        result = convert_example(SAMPLE_FINQA_EXAMPLE)
        assert "company_name" in result["context"]

    def test_answer_options_nullable(self):
        result = convert_example(SAMPLE_FINQA_EXAMPLE)
        assert result["answer_options"] is None
