"""Tests for the Phase-2 seed memo problem set.

These problems are long-form (free_text) and paired with a gold
solution + PRBench-style rubric. The tests enforce schema hygiene so
Phase-2 wiring can rely on the shape.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from problems.memo_problems import MEMO_PROBLEMS, get_memo_problems, get_memo_problem  # noqa: E402


# Categories already covered at the MC level in v1.2.0 that should have
# a memo seed. risk_assessment is deliberately excluded — Phase 3 will
# expand that category with its own memo set.
EXPECTED_CATEGORIES = {
    "earnings_surprise",
    "dcf_sanity_check",
    "accounting_red_flag",
    "catalyst_identification",
    "financial_statement_analysis",
}


class TestMemoSetBasics(unittest.TestCase):
    def test_five_memo_problems(self):
        self.assertEqual(len(MEMO_PROBLEMS), 5)

    def test_ids_are_unique(self):
        ids = [p["id"] for p in MEMO_PROBLEMS]
        self.assertEqual(len(ids), len(set(ids)))

    def test_one_per_core_category(self):
        cats = {p["category"] for p in MEMO_PROBLEMS}
        self.assertEqual(cats, EXPECTED_CATEGORIES)

    def test_all_free_text(self):
        for p in MEMO_PROBLEMS:
            self.assertEqual(p["answer_type"], "free_text", f"{p['id']} not free_text")


class TestMemoSchema(unittest.TestCase):
    REQUIRED_KEYS = {
        "id",
        "category",
        "difficulty",
        "answer_type",
        "tags",
        "question",
        "context",
        "gold_solution",
        "rubric",
    }

    def test_all_required_keys_present(self):
        for p in MEMO_PROBLEMS:
            self.assertTrue(
                self.REQUIRED_KEYS.issubset(p.keys()),
                f"{p['id']} missing keys: {self.REQUIRED_KEYS - p.keys()}",
            )

    def test_prompt_length_within_window(self):
        # Plan says 150-300 words for the prompt.
        for p in MEMO_PROBLEMS:
            words = len(p["question"].split())
            self.assertGreaterEqual(words, 40, f"{p['id']} question too short: {words}w")
            self.assertLessEqual(words, 260, f"{p['id']} question too long: {words}w")

    def test_gold_solution_length_within_window(self):
        # Plan target: 400-800 words; allow 300-900 to permit terser
        # memos where the structural critique is naturally shorter.
        for p in MEMO_PROBLEMS:
            words = len(p["gold_solution"].split())
            self.assertGreaterEqual(words, 300, f"{p['id']} solution too short: {words}w")
            self.assertLessEqual(words, 900, f"{p['id']} solution too long: {words}w")


class TestRubricHygiene(unittest.TestCase):
    def test_each_problem_has_binary_rubric(self):
        for p in MEMO_PROBLEMS:
            rubric = p["rubric"]
            self.assertGreaterEqual(len(rubric), 5, f"{p['id']} rubric too small")
            self.assertLessEqual(len(rubric), 20, f"{p['id']} rubric too large")
            for crit in rubric:
                self.assertIn("id", crit)
                self.assertIn("text", crit)
                self.assertIn("weight", crit)
                self.assertIsInstance(crit["weight"], int)
                self.assertGreaterEqual(crit["weight"], 1)

    def test_rubric_ids_are_unique_within_problem(self):
        for p in MEMO_PROBLEMS:
            ids = [c["id"] for c in p["rubric"]]
            self.assertEqual(len(ids), len(set(ids)), f"{p['id']} rubric ids not unique")

    def test_each_rubric_has_overconfidence_check(self):
        """House rule: investment analysis is probabilistic. A rubric
        that does not penalise overconfident language risks grading
        aggressive language as 'confident'."""
        for p in MEMO_PROBLEMS:
            texts = " ".join(c["text"].lower() for c in p["rubric"])
            self.assertTrue(
                any(
                    phrase in texts
                    for phrase in (
                        "overconfident",
                        "probabilistic",
                        "not 'certainly'",
                        "not 'guaranteed'",
                    )
                ),
                f"{p['id']} rubric missing overconfidence criterion",
            )


class TestAccessors(unittest.TestCase):
    def test_get_memo_problems_returns_list(self):
        self.assertEqual(get_memo_problems(), MEMO_PROBLEMS)

    def test_get_by_id(self):
        p = get_memo_problem("memo_dcf_001")
        self.assertEqual(p["category"], "dcf_sanity_check")

    def test_get_by_unknown_id_raises(self):
        with self.assertRaises(KeyError):
            get_memo_problem("memo_unknown_999")


if __name__ == "__main__":
    unittest.main()
