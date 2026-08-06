#!/usr/bin/env python3
"""Post-hoc cost-aware metrics for an existing predictions file.

Computes budget-conditioned pass rates and quality-per-token from a
``*_predictions.json`` written by run_benchmark — no model calls are made.

Predictions written before is_correct was persisted are backfilled with a
text-match correctness check. Records that also carry ``answer_type`` are
regraded exactly; older records without it fall back to multiple_choice
matching (numeric tolerance approximated). The report flags when backfill
was used.

Usage:
    python scripts/cost_report.py results/claude-haiku-4-5_predictions.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from evaluation.metrics import FinancialReasoningMetrics, compute_cost_metrics  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("predictions_file", type=Path)
    args = parser.parse_args()

    predictions = json.loads(args.predictions_file.read_text())
    if not isinstance(predictions, list):
        print("Expected a JSON list of prediction records.", file=sys.stderr)
        return 1

    backfilled = 0
    checker = FinancialReasoningMetrics()
    for p in predictions:
        if "is_correct" not in p:
            p["is_correct"] = checker._check_correctness(
                p.get("predicted") or "",
                p.get("correct_answer") or "",
                answer_type=p.get("answer_type") or "multiple_choice",
            )
            backfilled += 1

    report = {
        "predictions_file": str(args.predictions_file),
        "n_predictions": len(predictions),
        "is_correct_backfilled": backfilled,
        "cost_metrics": compute_cost_metrics(predictions),
    }
    if backfilled:
        report["backfill_note"] = (
            "is_correct was recomputed for records predating its persistence; "
            "records without a stored answer_type were graded as "
            "multiple_choice (numeric tolerance approximated)."
        )

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
