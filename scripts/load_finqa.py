"""Download FinQA from GitHub and convert to fin-reasoning-eval Problem schema.

Usage:
    python scripts/load_finqa.py                # Full test split
    python scripts/load_finqa.py --limit 50     # First 50 examples
    python scripts/load_finqa.py --split dev    # Validation split
    python scripts/load_finqa.py --dry-run      # Print stats without saving
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

FINQA_BASE_URL = "https://raw.githubusercontent.com/czyssrs/FinQA/main/dataset"
SPLIT_MAP = {"test": "test", "dev": "dev", "train": "train", "validation": "dev"}


# ── FinQA → Problem mapping helpers ──────────────────────────────────────


def render_table(table: list[list[str]]) -> str:
    """Convert a 2D string array to a markdown table."""
    if not table or not table[0]:
        return ""

    header = table[0]
    lines = ["| " + " | ".join(header) + " |"]
    lines.append("| " + " | ".join("---" for _ in header) + " |")

    for row in table[1:]:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[:len(header)]) + " |")

    return "\n".join(lines)


def extract_company(finqa_id: str) -> str:
    """Extract company/ticker from FinQA ID (e.g., 'ETR/2016/page_23.pdf-2' → 'ETR')."""
    parts = finqa_id.split("/")
    return parts[0] if parts else "Unknown"


def parse_program_string(program_str: str) -> list[str]:
    """Parse FinQA program string into individual operation strings.

    Input:  'subtract(5829, 5735), divide(#0, 86842000)'
    Output: ['subtract(5829, 5735)', 'divide(#0, 86842000)']
    """
    if not program_str or not program_str.strip():
        return []
    # Split on ), then re-add the closing paren
    raw = re.split(r"\)\s*,\s*", program_str.strip())
    steps = []
    for i, part in enumerate(raw):
        part = part.strip()
        if not part:
            continue
        if not part.endswith(")"):
            part += ")"
        steps.append(part)
    return steps


def count_operations(program_str: str) -> int:
    """Count function calls in a program string."""
    if not program_str:
        return 0
    return len(re.findall(r"\w+\(", program_str))


def infer_difficulty(program_str: str) -> str:
    """Infer difficulty from DSL program complexity.

    1 op → easy, 2 → medium, 3 → hard, 4+ → expert.
    """
    op_count = count_operations(program_str)
    if op_count <= 1:
        return "easy"
    elif op_count == 2:
        return "medium"
    elif op_count == 3:
        return "hard"
    return "expert"


def join_text(text_field) -> str:
    """Join pre_text/post_text which can be list[str] or str."""
    if isinstance(text_field, list):
        return " ".join(text_field)
    if isinstance(text_field, str):
        return text_field
    return ""


def build_context(example: dict) -> dict:
    """Build a FinancialContext dict from a FinQA example."""
    company = extract_company(example["id"])
    table_md = render_table(example.get("table", []))

    pre = join_text(example.get("pre_text", "")).strip()
    post = join_text(example.get("post_text", "")).strip()

    context_parts = []
    if pre:
        context_parts.append(pre)
    if table_md:
        context_parts.append(table_md)
    if post:
        context_parts.append(post)

    return {
        "company_name": company,
        "ticker": company,
        "sector": None,
        "market_cap": None,
        "fiscal_year": None,
        "revenue": None,
        "ebitda": None,
        "net_income": None,
        "eps": None,
        "free_cash_flow": None,
        "total_assets": None,
        "total_debt": None,
        "cash": None,
        "equity": None,
        "pe_ratio": None,
        "ev_ebitda": None,
        "price_to_book": None,
        "wacc": None,
        "terminal_growth": None,
        "discount_rate": None,
        "guidance": None,
        "consensus_estimates": None,
        "recent_news": None,
        "model_assumptions": {"filing_context": "\n\n".join(context_parts)},
        "formula_context": None,
    }


def convert_example(example: dict) -> dict:
    """Convert a single FinQA example to fin-reasoning-eval Problem format."""
    qa = example.get("qa", {})
    program_str = qa.get("program", "")
    exe_ans = qa.get("exe_ans")

    if exe_ans is not None:
        if isinstance(exe_ans, float):
            correct_answer = str(round(exe_ans, 6)).rstrip("0").rstrip(".")
        else:
            correct_answer = str(exe_ans)
    else:
        correct_answer = ""

    now = datetime.now(timezone.utc).isoformat()

    return {
        "id": f"finqa_{example['id']}",
        "category": "financial_statement_analysis",
        "difficulty": infer_difficulty(program_str),
        "question": qa.get("question", ""),
        "context": build_context(example),
        "answer_type": "numeric",
        "correct_answer": correct_answer,
        "answer_options": None,
        "answer_unit": None,
        "tolerance": 0.01,
        "explanation": qa.get("explanation", ""),
        "reasoning_steps": parse_program_string(program_str),
        "common_mistakes": [],
        "source": "FinQA (Chen et al., 2021)",
        "tags": ["finqa", "tabular-reasoning", "real-filing"],
        "created_at": now,
        "version": "1.0",
        "max_points": 1,
        "partial_credit": False,
    }


# ── Main pipeline ────────────────────────────────────────────────────────


def download_finqa(split: str = "test") -> list[dict]:
    """Download FinQA JSON from GitHub."""
    mapped = SPLIT_MAP.get(split, split)
    url = f"{FINQA_BASE_URL}/{mapped}.json"
    print(f"Downloading {url}...")

    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"Error downloading FinQA: {e}")
        sys.exit(1)


def load_and_convert(split: str = "test", limit: int | None = None) -> list[dict]:
    """Download FinQA and convert all examples."""
    raw = download_finqa(split)

    if limit:
        raw = raw[:limit]

    print(f"Converting {len(raw)} examples...")
    problems = []
    skipped = 0
    for example in raw:
        qa = example.get("qa", {})
        if not qa or qa.get("exe_ans") is None:
            skipped += 1
            continue
        problems.append(convert_example(example))

    if skipped:
        print(f"Skipped {skipped} examples (missing answer)")

    return problems


def build_problem_set(problems: list[dict], split: str) -> dict:
    """Wrap problems in ProblemSet metadata envelope."""
    cat_dist: dict[str, int] = {}
    diff_dist: dict[str, int] = {}
    for p in problems:
        cat_dist[p["category"]] = cat_dist.get(p["category"], 0) + 1
        diff_dist[p["difficulty"]] = diff_dist.get(p["difficulty"], 0) + 1

    return {
        "name": f"FinQA_{split}",
        "description": (
            f"FinQA {split} split converted to fin-reasoning-eval format. "
            "Source: czyssrs/FinQA (CC BY 4.0). "
            "Multi-step numerical reasoning over real SEC 10-K/Q filings."
        ),
        "version": "1.0.0",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_problems": len(problems),
        "category_distribution": cat_dist,
        "difficulty_distribution": diff_dist,
        "problems": problems,
    }


def main():
    parser = argparse.ArgumentParser(description="Load FinQA into fin-reasoning-eval format")
    parser.add_argument("--split", default="test", choices=["train", "dev", "test", "validation"])
    parser.add_argument("--limit", type=int, default=None, help="Max examples to convert")
    parser.add_argument("--dry-run", action="store_true", help="Print stats only")
    args = parser.parse_args()

    problems = load_and_convert(split=args.split, limit=args.limit)
    problem_set = build_problem_set(problems, args.split)

    print(f"\nConverted {problem_set['total_problems']} problems")
    print(f"Difficulty distribution: {problem_set['difficulty_distribution']}")

    if args.dry_run:
        print("\n[dry-run] Sample problem:")
        print(json.dumps(problems[0], indent=2)[:1000])
        return

    data_dir = Path(__file__).parent.parent / "data"
    data_dir.mkdir(exist_ok=True)
    out_path = data_dir / "benchmark_finqa.json"

    with open(out_path, "w") as f:
        json.dump(problem_set, f, indent=2)

    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
