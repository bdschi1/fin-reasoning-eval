---
name: sample-valuation-skill
description: Synthetic fixture skill used by the plugin_reader tests. Does not ship; exists so tests do not depend on the sibling plugin repo clone.
---

# Sample Valuation Skill

## Overview

A minimal SKILL.md fixture that exercises the section-extraction logic in
`generators/plugin_reader.py`.

## Conventions

- Every projection, margin, and discount-factor cell must be a live formula
- Use an odd number of rows and columns in sensitivity tables (5x5 standard)
- Cite each hardcoded input with a source comment in the format `Source: [System], [Date]`
- Use probabilistic language for directional conclusions

## Output Format

- Executive summary tab with base-case implied value and sensitivity ranges
- Projection tab with five-year operating build
- WACC tab with inputs and weighted calculation
- DCF tab with terminal value, EV-to-equity bridge, per-share value, 5x5 sensitivity

## Worked Examples

- Example 1: High-growth software target with 20% top-line CAGR
- Example 2: Mature consumer-staples target with 3% top-line CAGR

## Notes

Not used outside tests.
