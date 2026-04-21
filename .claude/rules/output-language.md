---
description: Output language — prohibit overconfidence/certainty language in investment analysis; enforce probabilistic framing
---

## Output Language Rules

All repo output — agent analysis, README prose, eval scenarios, test assertions, commit messages, generated reports — must avoid **overconfidence / certainty language**. Phrases like "100% confident", "sure thing", "can't lose", "guaranteed", "no risk", "certain to", "will definitely" are prohibited. Investment analysis is probabilistic; language must reflect that.

This applies to:
- LLM agent prompts and expected outputs (bull case, bear case, macro view, PM memo)
- Eval ground-truth scenarios and grading rubrics
- README descriptions and documentation
- Any generated text in the pipeline

If existing code or tests produce or accept overconfident language, flag it and fix it.
