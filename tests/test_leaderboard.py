"""Tests for Phase-1 leaderboard schema and renderers."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from leaderboard.leaderboard import (  # noqa: E402
    Leaderboard,
    LeaderboardEntry,
    create_entry_from_results,
)


RESULTS_WITH_TOTALS = {
    "model": "claude-sonnet-4-20250514",
    "timestamp": "2026-04-18T00:00:00",
    "dataset_size": 10,
    "metrics": {
        "overall_accuracy": 0.80,
        "total_examples": 10,
        "category_accuracy": {"earnings_surprise": 0.85},
        "difficulty_accuracy": {"easy": 1.0, "hard": 0.6},
        "brier_score_avg": 0.12,
        "calibration_error": 0.04,
    },
    "judge_model": "claude-haiku-4-5-20251001",
    "prompt_version": "v1.2.0",
    "totals": {
        "input_tokens": 20000,
        "output_tokens": 4000,
        "wall_time_s": 123.4,
        "cost_usd": 1.20,
    },
}


class TestEntryFactoryReadsTotals(unittest.TestCase):
    def test_cost_fields_populated(self):
        entry = create_entry_from_results(RESULTS_WITH_TOTALS)
        self.assertEqual(entry.total_cost_usd, 1.20)
        self.assertEqual(entry.total_input_tokens, 20000)
        self.assertEqual(entry.total_output_tokens, 4000)
        self.assertAlmostEqual(entry.total_wall_time_s, 123.4)
        # 10 examples * 0.80 accuracy = 8 correct → $/100 correct = $15
        self.assertAlmostEqual(entry.cost_per_100_correct, 15.0, places=2)
        self.assertEqual(entry.judge_model, "claude-haiku-4-5-20251001")
        self.assertEqual(entry.prompt_version, "v1.2.0")

    def test_missing_totals_degrades_gracefully(self):
        stripped = {k: v for k, v in RESULTS_WITH_TOTALS.items() if k != "totals"}
        entry = create_entry_from_results(stripped)
        self.assertIsNone(entry.total_cost_usd)
        self.assertIsNone(entry.cost_per_100_correct)
        self.assertIsNotNone(entry.overall_accuracy)


class TestMarkdownRenderingHasNewColumns(unittest.TestCase):
    def _leaderboard_with_one_entry(self) -> Leaderboard:
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        tmp.write(b'{"entries": []}')
        tmp.flush()
        lb = Leaderboard(storage_path=tmp.name)
        lb.add_entry(create_entry_from_results(RESULTS_WITH_TOTALS))
        return lb

    def test_overall_table_exposes_calibration_columns(self):
        lb = self._leaderboard_with_one_entry()
        md = lb.to_markdown_table()
        self.assertIn("Brier", md)
        self.assertIn("ECE", md)

    def test_cost_table_exposes_cost_columns(self):
        lb = self._leaderboard_with_one_entry()
        md = lb.to_cost_table()
        self.assertIn("Total $", md)
        self.assertIn("$/100 Correct", md)
        self.assertIn("claude-sonnet-4-20250514", md)

    def test_report_includes_cost_section(self):
        lb = self._leaderboard_with_one_entry()
        report = lb.generate_report()
        self.assertIn("Cost & Efficiency", report)


if __name__ == "__main__":
    unittest.main()
