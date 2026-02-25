# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-02-19

### Added
- 306 curated financial reasoning problems across 7 categories (earnings surprises, DCF sanity checks, accounting red flags, catalyst identification, formula audit, financial statement, risk assessment)
- 4-tier difficulty distribution: easy (10), medium (111), hard (141), expert (44)
- 60 advanced problems covering alpha/beta separation, factor models, position sizing, risk decomposition, portfolio construction, and performance attribution
- Per-category problem generators with shared base class
- Multi-provider LLM evaluation runners (Anthropic, OpenAI, HuggingFace, Ollama)
- Evaluation framework with accuracy metrics, category/difficulty breakdowns, reasoning quality, and latency tracking
- Rubric-based scoring system aligned with PRBench methodology
- FLaME taxonomy alignment for cross-benchmark comparability
- Vendor assessment framework for comparative LLM evaluation
- Gradio leaderboard UI for HuggingFace Spaces
- HuggingFace dataset export with train/validation/test splits
- `run.sh` orchestrator for setup, generation, evaluation, and leaderboard
