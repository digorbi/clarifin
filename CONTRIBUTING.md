# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Linting & type checks

```bash
ruff check .
mypy .
```

## Tests

```bash
pytest
```

Integration tests are marked with `@pytest.mark.integration` and may require env vars (e.g. API keys). They run in CI only on `main`.
