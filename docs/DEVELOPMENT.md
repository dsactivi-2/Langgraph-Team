# Development

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Checks

```bash
pytest
ruff check .
```

## Lokaler Server

```bash
uvicorn langgraph_builder_team.api:app --reload
```
