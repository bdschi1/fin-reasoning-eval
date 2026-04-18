#!/usr/bin/env python3
"""Refresh the HuggingFace export under data/huggingface/.

Reads the live benchmark JSON files (``benchmark_train.json``,
``benchmark_validation.json``, ``benchmark_test.json``) and rewrites the
three split JSONL files plus ``dataset_info.json`` so they stay in lockstep
with the curated problem set.

Idempotent. Run after any problem authoring pass.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
HF_DIR = DATA_DIR / "huggingface"
SPLIT_FILES = {
    "train": DATA_DIR / "benchmark_train.json",
    "validation": DATA_DIR / "benchmark_validation.json",
    "test": DATA_DIR / "benchmark_test.json",
}
MASTER_FILE = DATA_DIR / "financial_reasoning_benchmark.json"


def _load_problems(path: Path) -> list[dict]:
    with open(path) as fh:
        obj = json.load(fh)
    if isinstance(obj, dict) and "problems" in obj:
        return obj["problems"]
    if isinstance(obj, list):
        return obj
    raise ValueError(f"Unexpected schema in {path}")


def _to_hf_record(p: dict) -> dict:
    opts = p.get("answer_options") or p.get("options") or []
    # Normalize either legacy AnswerOption objects or dict records.
    options = []
    for opt in opts:
        if isinstance(opt, dict):
            options.append({"id": opt.get("id", ""), "text": opt.get("text", "")})
        else:
            options.append({"id": getattr(opt, "id", ""), "text": getattr(opt, "text", "")})
    return {
        "id": p.get("id", ""),
        "category": p.get("category", ""),
        "difficulty": p.get("difficulty", ""),
        "question": p.get("question", ""),
        "context": p.get("context", ""),
        "answer_type": p.get("answer_type", "multiple_choice"),
        "correct_answer": p.get("correct_answer", ""),
        "options": options,
        "explanation": p.get("explanation", ""),
        "reasoning_steps": p.get("reasoning_steps", []),
        "tags": p.get("tags", []),
    }


def refresh(version: str = "1.2.0") -> dict:
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"Master benchmark not found: {MASTER_FILE}")

    with open(MASTER_FILE) as fh:
        master = json.load(fh)

    master_problems = master.get("problems", [])
    master_version = master.get("version", version)

    HF_DIR.mkdir(parents=True, exist_ok=True)

    split_counts: dict[str, int] = {}
    category_counter: Counter = Counter()
    difficulty_counter: Counter = Counter()

    for split_name, split_path in SPLIT_FILES.items():
        if not split_path.exists():
            print(f"WARN: missing split {split_path}; skipping", file=sys.stderr)
            continue
        problems = _load_problems(split_path)
        out_path = HF_DIR / f"{split_name}.jsonl"
        with open(out_path, "w") as fh:
            for p in problems:
                fh.write(json.dumps(_to_hf_record(p)) + "\n")
        split_counts[split_name] = len(problems)
        print(f"Wrote {split_name}.jsonl ({len(problems)} records)")

    for p in master_problems:
        category_counter[p.get("category", "unknown")] += 1
        difficulty_counter[p.get("difficulty", "unknown")] += 1

    dataset_info = {
        "dataset_name": "financial-reasoning-eval",
        "description": (
            master.get("description")
            or "Benchmark for evaluating LLM financial reasoning across seven categories."
        ),
        "version": master_version or version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "total_examples": len(master_problems),
        "splits": split_counts,
        "features": {
            "id": "string",
            "category": "string",
            "difficulty": "string",
            "question": "string",
            "context": "string",
            "answer_type": "string",
            "correct_answer": "string",
            "options": "list",
            "explanation": "string",
            "reasoning_steps": "list",
            "tags": "list",
        },
        "categories": sorted(category_counter.keys()),
        "category_counts": dict(category_counter),
        "difficulties": sorted(difficulty_counter.keys()),
        "difficulty_counts": dict(difficulty_counter),
        "license": "MIT",
        "citation": (
            "@misc{financial-reasoning-eval,\n"
            "  title={Financial Reasoning Eval Benchmark},\n"
            "  year={2026},\n"
            "  publisher={HuggingFace}\n"
            "}"
        ),
        "dataset_size": len(master_problems),
    }

    info_path = HF_DIR / "dataset_info.json"
    with open(info_path, "w") as fh:
        json.dump(dataset_info, fh, indent=2)
    print(f"Wrote {info_path}")

    return dataset_info


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--version",
        default="1.2.0",
        help="Fallback version string if master JSON lacks one.",
    )
    args = parser.parse_args()
    info = refresh(version=args.version)
    print("\nSummary:")
    print(f"  version: {info['version']}")
    print(f"  total:   {info['total_examples']}")
    print(f"  splits:  {info['splits']}")
    print(f"  cats:    {info['category_counts']}")


if __name__ == "__main__":
    main()
