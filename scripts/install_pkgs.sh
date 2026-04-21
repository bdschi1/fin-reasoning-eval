#!/bin/bash
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  exit 0
fi
if [ -f pyproject.toml ]; then
  pip install -e . 2>/dev/null || pip install .
fi
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi
exit 0
