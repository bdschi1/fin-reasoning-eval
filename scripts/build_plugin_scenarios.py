#!/usr/bin/env python3
"""Build plugin-derived free-text evaluation scenarios.

Reads SKILL.md files from the sibling financial-services-plugins clone,
generates one `Problem` per pilot skill, and writes the result to
`data/plugin_scenarios.json` as a ProblemSet.

Usage:
    python scripts/build_plugin_scenarios.py
    python scripts/build_plugin_scenarios.py --output data/plugin_scenarios.json
    FIN_PLUGINS_ROOT=/custom/path python scripts/build_plugin_scenarios.py

Requires the sibling clone at
`~/code/work/bds_repos/Tier_1/financial-services-plugins` or
`FIN_PLUGINS_ROOT` env override.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from generators.plugin_reader import get_plugins_root, load_skill  # noqa: E402
from generators.plugin_scenarios import (  # noqa: E402
    PluginScenarioConfig,
    PluginScenarioGenerator,
)
from problems import ProblemSet  # noqa: E402


PILOT_SKILLS: list[str] = [
    "dcf-model",
    "comps-analysis",
    "lbo-model",
    "ic-memo",
    "earnings-preview",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default=str(REPO_ROOT / "data" / "plugin_scenarios.json"),
        help="Output JSON path",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for synthetic context generation",
    )
    parser.add_argument(
        "--skills",
        nargs="*",
        default=None,
        help="Override the pilot skill list (default: 5 pilot skills)",
    )
    args = parser.parse_args()

    plugins_root = get_plugins_root()
    if not plugins_root.exists():
        print(
            f"[error] Plugin repo not found at {plugins_root}.\n"
            f"Clone via: git clone https://github.com/anthropics/"
            f"financial-services-plugins {plugins_root}",
            file=sys.stderr,
        )
        return 2

    skills = args.skills or PILOT_SKILLS
    gen = PluginScenarioGenerator(PluginScenarioConfig(seed=args.seed))

    problems = []
    for slug in skills:
        try:
            spec = load_skill(slug)
        except FileNotFoundError as exc:
            print(f"[warn] skipping {slug}: {exc}", file=sys.stderr)
            continue
        problem = gen.generate_from_spec(spec)
        problems.append(problem)
        print(
            f"[ok] {slug} -> {problem.category.value} "
            f"({problem.difficulty.value}, id={problem.id})"
        )

    if not problems:
        print("[error] no scenarios generated", file=sys.stderr)
        return 1

    problem_set = ProblemSet(
        name="plugin_scenarios_pilot",
        description=(
            "Plugin-derived free-text scenarios for fin-reasoning-eval "
            "pilot. Ground truth sourced from SKILL.md files in "
            "anthropic/financial-services-plugins."
        ),
        problems=problems,
        version="0.1.0",
    )

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    problem_set.to_json(str(output_path))
    print(f"[done] wrote {len(problems)} scenarios to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
