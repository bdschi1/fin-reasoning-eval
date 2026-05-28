"""Tests for the plugin-derived scenario wiring in runners/run_evaluation.py.

Covers the two helpers that route plugin scenarios to the skill-adherence
rubric + skill-conventions judge context.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from runners.run_evaluation import _plugin_grading_context, _plugin_skill_slug

_PLUGIN_REPO_PRESENT = Path(
    "/Users/bdsm4/code/work/bds_repos/Tier_1/financial-services-plugins/"
    "financial-analysis/skills/dcf-model/SKILL.md"
).exists()


def test_plugin_skill_slug_extracts_from_tags():
    tags = ["plugin-derived", "skill:dcf-model", "plugin:financial-analysis"]
    assert _plugin_skill_slug(tags) == "dcf-model"


def test_plugin_skill_slug_none_for_regular_problem():
    assert _plugin_skill_slug(["earnings", "guidance"]) is None


def test_plugin_skill_slug_none_when_marker_absent():
    # No `plugin-derived` tag — skill: tag alone should not trigger routing
    assert _plugin_skill_slug(["skill:dcf-model"]) is None


def test_plugin_skill_slug_none_for_empty_tags():
    assert _plugin_skill_slug([]) is None
    assert _plugin_skill_slug(None) is None  # type: ignore[arg-type]


def test_plugin_grading_context_returns_none_for_missing_skill():
    criteria, conv = _plugin_grading_context("this-skill-does-not-exist")
    assert criteria is None
    assert conv is None


@pytest.mark.skipif(not _PLUGIN_REPO_PRESENT, reason="sibling plugin repo not cloned")
def test_plugin_grading_context_loads_dcf_model():
    criteria, conv = _plugin_grading_context("dcf-model")
    assert criteria is not None
    assert conv is not None
    # PRBench default (27) + 5 skill_adherence criteria
    assert len(criteria) >= 32
    adherence = [c for c in criteria if c.category == "skill_adherence"]
    assert len(adherence) == 5
    assert all(c.id.startswith("SA_DCF_MODEL") for c in adherence)
    assert "dcf-model" in conv.lower() or "dcf model" in conv.lower()
