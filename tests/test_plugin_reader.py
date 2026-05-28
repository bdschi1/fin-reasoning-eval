"""Tests for generators.plugin_reader — SKILL.md parsing.

Uses the self-contained fixture at tests/fixtures/plugin_skill_sample.md
so the test suite does not depend on the sibling plugin repo clone.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from generators.plugin_reader import (
    SkillSpec,
    _extract_bullets,
    _extract_section,
    _split_frontmatter,
    load_skill_from_file,
    parse_skill_md,
)


FIXTURE_PATH = Path(__file__).parent / "fixtures" / "plugin_skill_sample.md"


def test_split_frontmatter_extracts_yaml_block():
    text = "---\nname: foo\ndescription: bar\n---\n# Body\n\nmore"
    frontmatter, body = _split_frontmatter(text)
    assert frontmatter == {"name": "foo", "description": "bar"}
    assert body.startswith("# Body")


def test_split_frontmatter_returns_empty_when_missing():
    frontmatter, body = _split_frontmatter("# Body only\n")
    assert frontmatter == {}
    assert body == "# Body only\n"


def test_extract_section_matches_by_keyword():
    body = (
        "## Conventions\n\n"
        "- rule one\n"
        "- rule two\n\n"
        "## Output Format\n\n"
        "- field one\n"
    )
    section = _extract_section(body, ["conventions"])
    assert "rule one" in section
    assert "rule two" in section
    assert "Output Format" not in section


def test_extract_bullets_handles_common_markers():
    section = "- alpha\n- beta\n* gamma\n  - indented ignored\n"
    bullets = _extract_bullets(section)
    assert bullets == ["alpha", "beta", "gamma"]


def test_parse_skill_md_populates_spec_fields():
    text = FIXTURE_PATH.read_text()
    spec = parse_skill_md(text, slug="sample-valuation-skill", plugin="fixture")

    assert isinstance(spec, SkillSpec)
    assert spec.slug == "sample-valuation-skill"
    assert spec.plugin == "fixture"
    assert spec.name == "sample-valuation-skill"
    assert "fixture" in spec.description.lower()
    assert spec.frontmatter["name"] == "sample-valuation-skill"


def test_parse_skill_md_extracts_conventions():
    spec = load_skill_from_file(
        FIXTURE_PATH, slug="sample-valuation-skill", plugin="fixture"
    )
    assert spec.conventions, "conventions should not be empty"
    joined = " ".join(spec.conventions).lower()
    assert "formula" in joined
    assert "probabilistic" in joined
    assert "odd number" in joined


def test_parse_skill_md_extracts_output_schema():
    spec = load_skill_from_file(
        FIXTURE_PATH, slug="sample-valuation-skill", plugin="fixture"
    )
    assert spec.output_schema
    assert "DCF tab" in spec.output_schema or "sensitivity" in spec.output_schema.lower()


def test_parse_skill_md_source_ref():
    spec = load_skill_from_file(
        FIXTURE_PATH, slug="sample-valuation-skill", plugin="financial-analysis"
    )
    assert spec.source_ref == "plugin:financial-analysis/sample-valuation-skill"


def test_load_skill_from_file_missing_path_raises():
    with pytest.raises(FileNotFoundError):
        load_skill_from_file(
            FIXTURE_PATH.parent / "does_not_exist.md",
            slug="missing",
            plugin="fixture",
        )
