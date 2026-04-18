#!/usr/bin/env python3
"""Leaderboard orchestrator.

Loads a YAML config from leaderboard_configs/ and runs each listed model
against the benchmark via runners/run_evaluation.py. This is the single
entrypoint for the two deferred Phase 1 runs:

  - leaderboard_configs/phase1_items_4_5.yaml       (~$75, 3 models)
  - leaderboard_configs/phase1_full_leaderboard.yaml (~$210, 6 models)

Live API spend — the orchestrator refuses to run without an explicit
--yes flag and prints a cost preview before any call. --dry-run skips all
network calls so the scaffolding can be verified end-to-end offline.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ModelSpec:
    name: str
    provider: str
    max_tokens: int
    auto_rubric: bool
    est_cost_usd: float
    est_wall_min: float
    api_key_env: str


@dataclass
class LeaderboardConfig:
    name: str
    description: str
    prompt_version: str
    judge_model: str
    split: str
    data_dir: str
    output_dir: str
    models: list[ModelSpec]
    hard_ceiling_usd: float
    contingency_pct: float


def load_config(path: Path) -> LeaderboardConfig:
    with open(path) as f:
        raw = yaml.safe_load(f)

    budget = raw.get("budget", {}) or {}
    models = [
        ModelSpec(
            name=m["name"],
            provider=m["provider"],
            max_tokens=int(m.get("max_tokens", 4096)),
            auto_rubric=bool(m.get("auto_rubric", True)),
            est_cost_usd=float(m.get("est_cost_usd", 0.0)),
            est_wall_min=float(m.get("est_wall_min", 0.0)),
            api_key_env=str(m.get("api_key_env", "")),
        )
        for m in raw.get("models", [])
    ]

    return LeaderboardConfig(
        name=str(raw.get("name", path.stem)),
        description=str(raw.get("description", "")),
        prompt_version=str(raw.get("prompt_version", "v1.2.0")),
        judge_model=str(raw.get("judge_model", "claude-haiku-4-5-20251001")),
        split=str(raw.get("split", "test")),
        data_dir=str(raw.get("data_dir", "data")),
        output_dir=str(raw.get("output_dir", "results")),
        models=models,
        hard_ceiling_usd=float(budget.get("hard_ceiling_usd", 0.0)),
        contingency_pct=float(budget.get("contingency_pct", 25)),
    )


def estimate_totals(cfg: LeaderboardConfig) -> dict[str, float]:
    base = sum(m.est_cost_usd for m in cfg.models)
    contingency = base * (cfg.contingency_pct / 100.0)
    total_wall_min = sum(m.est_wall_min for m in cfg.models)
    return {
        "base_usd": round(base, 2),
        "contingency_usd": round(contingency, 2),
        "ceiling_usd": round(base + contingency, 2),
        "total_wall_min": round(total_wall_min, 1),
    }


def preview(cfg: LeaderboardConfig) -> str:
    totals = estimate_totals(cfg)
    lines: list[str] = []
    lines.append(f"=== Leaderboard run: {cfg.name} ===")
    if cfg.description:
        lines.append(cfg.description.strip())
    lines.append("")
    lines.append(f"Prompt version: {cfg.prompt_version}")
    lines.append(f"Judge model:    {cfg.judge_model}")
    lines.append(f"Split:          {cfg.split}")
    lines.append(f"Output dir:     {cfg.output_dir}")
    lines.append("")
    lines.append(f"{'Model':<22} {'Provider':<12} {'MaxTok':>7} {'EstCost':>10} {'WallMin':>9}")
    lines.append("-" * 62)
    for m in cfg.models:
        lines.append(
            f"{m.name:<22} {m.provider:<12} {m.max_tokens:>7} "
            f"${m.est_cost_usd:>8.2f} {m.est_wall_min:>8.0f}"
        )
    lines.append("-" * 62)
    lines.append(
        f"{'TOTAL':<22} {'':<12} {'':>7} ${totals['base_usd']:>8.2f} "
        f"{totals['total_wall_min']:>8.0f}"
    )
    lines.append(
        f"Contingency ({cfg.contingency_pct:.0f}%): ${totals['contingency_usd']:.2f}  "
        f"| Ceiling: ${totals['ceiling_usd']:.2f}  "
        f"| Hard budget: ${cfg.hard_ceiling_usd:.2f}"
    )
    if cfg.hard_ceiling_usd and totals["ceiling_usd"] > cfg.hard_ceiling_usd:
        lines.append(
            f"  ⚠ Estimated ceiling exceeds hard_ceiling_usd — run will be refused."
        )
    return "\n".join(lines)


def check_api_keys(cfg: LeaderboardConfig) -> list[str]:
    """Return list of missing env var names required by the config."""
    needed = {m.api_key_env for m in cfg.models if m.api_key_env}
    return sorted(n for n in needed if not os.environ.get(n))


def get_git_sha(repo_root: Path) -> Optional[str]:
    try:
        import subprocess
        out = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(repo_root), timeout=5
        )
        return out.decode().strip()
    except Exception:
        return None


def run_model(
    spec: ModelSpec,
    cfg: LeaderboardConfig,
    dry_run: bool,
    force: bool,
) -> dict[str, Any]:
    """Run one model via the existing evaluate_model entrypoint.

    Returns a manifest entry. In --dry-run mode, emits a manifest stub and
    makes no network calls.
    """
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    result_path = output_dir / f"{spec.name.replace('/', '_')}_results.json"

    entry: dict[str, Any] = {
        "model": spec.name,
        "provider": spec.provider,
        "result_path": str(result_path),
        "dry_run": dry_run,
        "started_at": _utc_now_iso(),
    }

    if dry_run:
        entry["status"] = "dry_run_ok"
        entry["note"] = "No API call made. Preview only."
        return entry

    if result_path.exists() and not force:
        entry["status"] = "skipped_exists"
        entry["note"] = f"Result file exists: {result_path}. Use --force to overwrite."
        return entry

    # Env plumbing so downstream writers record correct judge/prompt pins.
    os.environ.setdefault("JUDGE_MODEL", cfg.judge_model)
    os.environ.setdefault("PROMPT_VERSION", cfg.prompt_version)

    from runners.run_evaluation import evaluate_model

    try:
        results = evaluate_model(
            model=spec.name,
            split=cfg.split,
            data_dir=cfg.data_dir,
            output_dir=str(output_dir),
            max_tokens=spec.max_tokens,
            auto_rubric=spec.auto_rubric,
        )
        entry["status"] = "completed"
        entry["overall_accuracy"] = results.get("metrics", {}).get("overall_accuracy")
        entry["total_cost_usd"] = results.get("totals", {}).get("cost_usd")
    except KeyboardInterrupt:
        entry["status"] = "interrupted"
        raise
    except Exception as exc:  # noqa: BLE001 — surface at manifest level
        entry["status"] = "failed"
        entry["error"] = f"{type(exc).__name__}: {exc}"

    entry["finished_at"] = _utc_now_iso()
    return entry


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        required=True,
        help="Path to a leaderboard_configs/*.yaml file.",
    )
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Explicit budget approval. Required for non-dry-run execution.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print preview, validate keys, and exit. Makes no API calls.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing result files. Default skips models already run.",
    )
    parser.add_argument(
        "--only",
        nargs="+",
        help="Run only the specified model names from the config.",
    )
    args = parser.parse_args()

    if not args.config.exists():
        print(f"Config not found: {args.config}", file=sys.stderr)
        return 2

    cfg = load_config(args.config)
    if args.only:
        cfg.models = [m for m in cfg.models if m.name in set(args.only)]
        if not cfg.models:
            print("No models in config matched --only filter.", file=sys.stderr)
            return 2

    print(preview(cfg))
    print()

    totals = estimate_totals(cfg)
    if cfg.hard_ceiling_usd and totals["ceiling_usd"] > cfg.hard_ceiling_usd:
        print(
            f"Refusing: estimated ceiling ${totals['ceiling_usd']:.2f} exceeds "
            f"hard_ceiling_usd ${cfg.hard_ceiling_usd:.2f}.",
            file=sys.stderr,
        )
        return 2

    missing_keys = check_api_keys(cfg)
    if missing_keys and not args.dry_run:
        print(
            f"Missing env vars: {', '.join(missing_keys)}. "
            f"Set them before running, or use --dry-run to preview.",
            file=sys.stderr,
        )
        return 2

    if not args.dry_run and not args.yes:
        print(
            "Live API spend requires --yes to confirm the budget above. "
            "Re-run with --dry-run for a safe preview or --yes to proceed.",
            file=sys.stderr,
        )
        return 2

    manifest: dict[str, Any] = {
        "config": args.config.name,
        "run_name": cfg.name,
        "prompt_version": cfg.prompt_version,
        "judge_model": cfg.judge_model,
        "git_sha": get_git_sha(REPO_ROOT),
        "started_at": _utc_now_iso(),
        "dry_run": args.dry_run,
        "entries": [],
    }

    for spec in cfg.models:
        print(f"\n--- {spec.name} ---")
        entry = run_model(spec, cfg, dry_run=args.dry_run, force=args.force)
        manifest["entries"].append(entry)
        print(json.dumps(entry, indent=2))

    manifest["finished_at"] = _utc_now_iso()

    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest: {manifest_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
