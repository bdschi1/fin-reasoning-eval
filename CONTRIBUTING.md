# Contributing

## Development Setup

```bash
git clone https://github.com/bdschi1/fin-reasoning-eval.git
cd fin-reasoning-eval
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Code Style

- Lint with `ruff check .`
- Format with `ruff format .`
- Type hints encouraged

## Testing

```bash
pytest tests/ -v
```

## Pull Requests

1. Create a feature branch from `main`
2. Make focused, single-purpose commits
3. Ensure all tests pass before submitting
4. Open a PR with a clear description of changes
