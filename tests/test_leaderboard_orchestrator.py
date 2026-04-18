"""Tests for scripts/run_leaderboard.py.

Covers config loading, cost-total math, API-key check, and the --dry-run
path. No API calls are made.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from scripts import run_leaderboard  # noqa: E402


CONFIG_ITEMS_4_5 = REPO_ROOT / "leaderboard_configs" / "phase1_items_4_5.yaml"
CONFIG_FULL = REPO_ROOT / "leaderboard_configs" / "phase1_full_leaderboard.yaml"


def test_items_4_5_config_loads():
    cfg = run_leaderboard.load_config(CONFIG_ITEMS_4_5)
    names = [m.name for m in cfg.models]
    assert names == ["claude-sonnet-4", "claude-opus-4", "gpt-4.1"]
    assert cfg.prompt_version == "v1.2.0"
    assert cfg.judge_model == "claude-haiku-4-5-20251001"
    assert cfg.hard_ceiling_usd == 100.0


def test_full_leaderboard_config_loads():
    cfg = run_leaderboard.load_config(CONFIG_FULL)
    # o3 is commented out in the YAML; ensure it is not loaded.
    names = [m.name for m in cfg.models]
    assert "o3" not in names
    assert len(cfg.models) == 6
    assert cfg.hard_ceiling_usd == 250.0


def test_estimate_totals_items_4_5():
    cfg = run_leaderboard.load_config(CONFIG_ITEMS_4_5)
    totals = run_leaderboard.estimate_totals(cfg)
    # 12 + 57 + 6.5 = 75.5 generation-only
    assert totals["base_usd"] == pytest.approx(75.5)
    # 25% contingency (helper rounds to 2dp)
    assert totals["contingency_usd"] == pytest.approx(18.88, abs=0.01)
    assert totals["ceiling_usd"] == pytest.approx(94.38, abs=0.01)
    # Under the $100 hard ceiling
    assert totals["ceiling_usd"] < cfg.hard_ceiling_usd


def test_estimate_totals_full_under_hard_ceiling():
    cfg = run_leaderboard.load_config(CONFIG_FULL)
    totals = run_leaderboard.estimate_totals(cfg)
    assert totals["ceiling_usd"] < cfg.hard_ceiling_usd


def test_check_api_keys_missing(monkeypatch):
    cfg = run_leaderboard.load_config(CONFIG_ITEMS_4_5)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    missing = run_leaderboard.check_api_keys(cfg)
    assert "ANTHROPIC_API_KEY" in missing
    assert "OPENAI_API_KEY" in missing


def test_check_api_keys_present(monkeypatch):
    cfg = run_leaderboard.load_config(CONFIG_ITEMS_4_5)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "x")
    monkeypatch.setenv("OPENAI_API_KEY", "x")
    assert run_leaderboard.check_api_keys(cfg) == []


def test_preview_contains_totals():
    cfg = run_leaderboard.load_config(CONFIG_ITEMS_4_5)
    text = run_leaderboard.preview(cfg)
    assert "claude-sonnet-4" in text
    assert "claude-opus-4" in text
    assert "gpt-4.1" in text
    assert "75.50" in text or "75.5" in text
    assert "Hard budget: $100.00" in text


def test_dry_run_makes_no_api_calls(tmp_path, monkeypatch):
    # Point output_dir at a temp path so we don't pollute real results/.
    import yaml

    cfg_dict = yaml.safe_load(CONFIG_ITEMS_4_5.read_text())
    cfg_dict["output_dir"] = str(tmp_path / "out")
    tmp_cfg = tmp_path / "cfg.yaml"
    tmp_cfg.write_text(yaml.safe_dump(cfg_dict))

    # Run as a subprocess so the real __main__ path executes.
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "run_leaderboard.py"),
            "--config",
            str(tmp_cfg),
            "--dry-run",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((Path(cfg_dict["output_dir"]) / "manifest.json").read_text())
    assert manifest["dry_run"] is True
    assert len(manifest["entries"]) == 3
    for e in manifest["entries"]:
        assert e["status"] == "dry_run_ok"
        assert e["dry_run"] is True


def test_yes_without_keys_refuses(tmp_path, monkeypatch):
    import yaml

    cfg_dict = yaml.safe_load(CONFIG_ITEMS_4_5.read_text())
    cfg_dict["output_dir"] = str(tmp_path / "out")
    tmp_cfg = tmp_path / "cfg.yaml"
    tmp_cfg.write_text(yaml.safe_dump(cfg_dict))

    env = os.environ.copy()
    env.pop("ANTHROPIC_API_KEY", None)
    env.pop("OPENAI_API_KEY", None)
    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "run_leaderboard.py"),
            "--config",
            str(tmp_cfg),
            "--yes",
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    # Missing keys must cause non-zero exit.
    assert proc.returncode == 2
    assert "Missing env vars" in proc.stderr


def test_no_yes_no_dry_run_refuses(tmp_path, monkeypatch):
    import yaml

    cfg_dict = yaml.safe_load(CONFIG_ITEMS_4_5.read_text())
    cfg_dict["output_dir"] = str(tmp_path / "out")
    tmp_cfg = tmp_path / "cfg.yaml"
    tmp_cfg.write_text(yaml.safe_dump(cfg_dict))

    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = "x"
    env["OPENAI_API_KEY"] = "x"

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "run_leaderboard.py"),
            "--config",
            str(tmp_cfg),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )
    assert proc.returncode == 2
    assert "--yes" in proc.stderr


def test_only_filter(tmp_path):
    import yaml

    cfg_dict = yaml.safe_load(CONFIG_ITEMS_4_5.read_text())
    cfg_dict["output_dir"] = str(tmp_path / "out")
    tmp_cfg = tmp_path / "cfg.yaml"
    tmp_cfg.write_text(yaml.safe_dump(cfg_dict))

    proc = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "run_leaderboard.py"),
            "--config",
            str(tmp_cfg),
            "--dry-run",
            "--only",
            "gpt-4.1",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert proc.returncode == 0, proc.stderr
    manifest = json.loads((Path(cfg_dict["output_dir"]) / "manifest.json").read_text())
    assert [e["model"] for e in manifest["entries"]] == ["gpt-4.1"]
