"""Plugin SKILL.md reader.

Parses a `SKILL.md` file from the anthropic/financial-services-plugins repo
into a structured `SkillSpec`. Pure parsing — no LLM calls, deterministic
outputs, suitable for build-time scenario generation.

Resolution order for the plugin repo root:
1. `FIN_PLUGINS_ROOT` environment variable (absolute path)
2. Sibling clone at `~/code/work/bds_repos/Tier_1/financial-services-plugins`
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml


DEFAULT_PLUGINS_ROOT = (
    Path.home() / "code/work/bds_repos/Tier_1/financial-services-plugins"
)


@dataclass
class SkillSpec:
    """Structured representation of a parsed SKILL.md."""

    slug: str
    plugin: str
    name: str
    description: str
    body: str
    conventions: list[str] = field(default_factory=list)
    output_schema: str = ""
    examples: list[str] = field(default_factory=list)
    frontmatter: dict = field(default_factory=dict)

    @property
    def source_ref(self) -> str:
        return f"plugin:{self.plugin}/{self.slug}"


def get_plugins_root() -> Path:
    """Return the resolved plugins repo root."""
    override = os.environ.get("FIN_PLUGINS_ROOT")
    if override:
        return Path(override).expanduser()
    return DEFAULT_PLUGINS_ROOT


def find_skill_path(slug: str, plugins_root: Optional[Path] = None) -> Path:
    """Locate a skill directory by slug across all plugin subdirs.

    Searches: financial-analysis/skills, equity-research/skills,
    investment-banking/skills, private-equity/skills, wealth-management/skills,
    partner-built/lseg/skills, partner-built/spglobal/skills.
    """
    root = plugins_root or get_plugins_root()
    if not root.exists():
        raise FileNotFoundError(
            f"Plugin repo not found at {root}. Clone via: "
            "git clone https://github.com/anthropics/financial-services-plugins "
            f"{root}"
        )

    plugin_dirs = [
        "financial-analysis",
        "equity-research",
        "investment-banking",
        "private-equity",
        "wealth-management",
        "partner-built/lseg",
        "partner-built/spglobal",
    ]

    for plugin in plugin_dirs:
        candidate = root / plugin / "skills" / slug
        if (candidate / "SKILL.md").exists():
            return candidate

    raise FileNotFoundError(
        f"Skill '{slug}' not found under any plugin in {root}"
    )


def _plugin_name_from_path(skill_dir: Path) -> str:
    parts = skill_dir.parts
    try:
        skills_idx = parts.index("skills")
    except ValueError:
        return skill_dir.parent.name
    if skills_idx >= 2 and parts[skills_idx - 2] == "partner-built":
        return f"partner-built/{parts[skills_idx - 1]}"
    return parts[skills_idx - 1]


_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n(.*)$", re.DOTALL)


def _split_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter and body from a SKILL.md string."""
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}, text
    try:
        frontmatter = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        frontmatter = {}
    body = match.group(2)
    return frontmatter, body


def _extract_section(body: str, heading_keywords: list[str]) -> str:
    """Extract the first markdown section whose heading matches any keyword.

    Matches H2/H3 headings case-insensitively. Returns the section body up to
    the next heading of equal-or-higher level, or empty string if not found.
    """
    lines = body.splitlines()
    collected: list[str] = []
    in_section = False
    section_level = 0

    for line in lines:
        heading_match = re.match(r"^(#{2,4})\s+(.*)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip().lower()
            if in_section:
                if level <= section_level:
                    break
            else:
                if any(kw.lower() in heading_text for kw in heading_keywords):
                    in_section = True
                    section_level = level
                    continue
        if in_section:
            collected.append(line)

    return "\n".join(collected).strip()


def _extract_bullets(section: str) -> list[str]:
    """Extract top-level bullet items from a section of markdown."""
    bullets: list[str] = []
    for line in section.splitlines():
        stripped = line.lstrip()
        if stripped.startswith(("- ", "* ")) and not line.startswith("  "):
            bullets.append(stripped[2:].strip())
    return bullets


def parse_skill_md(text: str, slug: str, plugin: str) -> SkillSpec:
    """Parse a SKILL.md string into a SkillSpec."""
    frontmatter, body = _split_frontmatter(text)

    name = str(frontmatter.get("name", slug))
    description = str(frontmatter.get("description", "")).strip()

    conventions_section = _extract_section(
        body, ["conventions", "critical constraints", "rules", "requirements"]
    )
    conventions = _extract_bullets(conventions_section)
    if not conventions and conventions_section:
        conventions = [conventions_section.split("\n", 1)[0].strip()]

    output_schema = _extract_section(
        body, ["output format", "output schema", "deliverable", "output"]
    )

    examples_section = _extract_section(body, ["example", "worked example"])
    examples = _extract_bullets(examples_section) or (
        [examples_section] if examples_section else []
    )

    return SkillSpec(
        slug=slug,
        plugin=plugin,
        name=name,
        description=description,
        body=body,
        conventions=conventions,
        output_schema=output_schema,
        examples=examples,
        frontmatter=frontmatter,
    )


def load_skill(slug: str, plugins_root: Optional[Path] = None) -> SkillSpec:
    """Load and parse a SKILL.md by slug."""
    skill_dir = find_skill_path(slug, plugins_root)
    plugin = _plugin_name_from_path(skill_dir)
    text = (skill_dir / "SKILL.md").read_text()
    return parse_skill_md(text, slug=slug, plugin=plugin)


def load_skill_from_file(path: Path, slug: str, plugin: str) -> SkillSpec:
    """Load and parse a SKILL.md from an explicit file path (used for tests)."""
    text = Path(path).read_text()
    return parse_skill_md(text, slug=slug, plugin=plugin)
