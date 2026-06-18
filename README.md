# LangGraph Builder Team

> Meta-Agent-System zum Bau von LangGraph Agents, Workflows, Skills und deploybaren Projekten.

## Uebersicht

Dieses Repository enthaelt ein production-orientiertes MVP fuer ein LangGraph Builder Team. Der Workflow plant ein Projekt, erzeugt erste Code-Artefakte, beschreibt Memory und Skills, fuehrt deterministische Sandbox-Checks aus, reviewed das Ergebnis, vergibt einen Quality Score und erzeugt Deployment-Hinweise.

Die Web-UI stellt ein Build Studio mit Bereichen fuer Agenten, Memory/Archiv,
Settings/API-Key-Status, Deployment-Checkliste und Build-History bereit.

## Ziele & Erfolgskriterien

- [x] Typisiertes State-Schema mit Pydantic
- [x] LangGraph Workflow mit Planner, Builder, Memory Designer, Executor, Reviewer, Verifier und Deployment Specialist
- [x] FastAPI UI/API
- [x] Operator-UI fuer Build-Planung, Agenten, Memory, Settings, History und Deployment
- [x] Docker Compose mit App, Postgres und Qdrant
- [x] Tests fuer Graph, API und Modelle

## Architektur

Siehe [ARCHITECTURE.md](./docs/ARCHITECTURE.md).

## Agents

Siehe [AGENTS.md](./docs/AGENTS.md) und die einzelnen Agent Specs im Ordner [agents](./agents).

## Memory & Skills

- **Checkpointer**: Postgres empfohlen
- **Vector Memory**: Qdrant mit Namespace pro `project_id`
- **Skill Registry**: Siehe [skills](./skills)

## Quick Start

```bash
cp .env.example .env
docker compose up -d --build
```

Danach:

- UI: `http://localhost:8000`
- Healthcheck: `http://localhost:8000/health`

API Keys werden nicht im Browser gesetzt oder angezeigt. Lokal gehoeren sie in
`.env`, auf dem VPS in Environment Variables oder einen Secret Manager.

## Lokal Entwickeln

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
make check
uvicorn langgraph_builder_team.api:app --reload
```

## Operator-Kommandos

```bash
make check
make build
make up
make health
make logs
```

## Production Deployment

Siehe [DEPLOYMENT.md](./docs/DEPLOYMENT.md).

Production-Readiness-Status und empfohlene Erweiterungen stehen in
[PRODUCTION_READINESS.md](./docs/PRODUCTION_READINESS.md).

## Lizenz

MIT License
