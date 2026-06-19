# LangGraph Builder Team

> Meta-Agent-System zum Bau von LangGraph Agents, Workflows, Skills und deploybaren Projekten.

## Uebersicht

Dieses Repository enthaelt ein production-orientiertes MVP fuer ein LangGraph Builder Team. Der Workflow plant ein Projekt, erzeugt erste Code-Artefakte, beschreibt Memory und Skills, fuehrt deterministische Sandbox-Checks aus, reviewed das Ergebnis, vergibt einen Quality Score und erzeugt Deployment-Hinweise.

Die Web-UI stellt ein Build Studio mit Bereichen fuer Agenten, Memory/Archiv,
Settings/API-Key-Status, Deployment-Checkliste und Build-History bereit. Builds
und Chat-History werden in Postgres persistiert, Qdrant liefert Memory-Suche,
und ein OpenAI-kompatibler LLM-Adapter ist vorbereitet. Zusaetzlich sind
Adapter fuer LangChain, LangChain.js, LangGraph Server, LangGraph.js,
Deep Agents, Deep Agents.js, MCP, Agent Protocol und Open-SWE-Handoffs
enthalten.

## Ziele & Erfolgskriterien

- [x] Typisiertes State-Schema mit Pydantic
- [x] LangGraph Workflow mit Planner, Builder, Memory Designer, Executor, Reviewer, Verifier und Deployment Specialist
- [x] FastAPI UI/API
- [x] Operator-UI fuer Build-Planung, Agenten, Memory, Settings, History und Deployment
- [x] Persistente Build-/Chat-History ueber Postgres mit Fallback
- [x] Qdrant Memory Search mit lokalem Fallback fuer Tests
- [x] Optionaler Login/Auth-Schutz fuer UI/API
- [x] OpenAI-kompatibler LLM-Adapter
- [x] LangChain Runnable/Tool Adapter
- [x] LangGraph Server Config via `langgraph.json`
- [x] MCP Adapter ueber `langchain-mcp-adapters`
- [x] Agent Protocol kompatible Thread-/Run-Endpunkte
- [x] Deep Agents Python/JS Starter-Code
- [x] Open SWE Task-Handoff Adapter
- [x] LangChain.js/LangGraph.js Adapter-Paket unter `js-adapters/`
- [x] Docker Compose mit App, Postgres und Qdrant
- [x] Tests fuer Graph, API und Modelle

## Integrationen

| Integration | Status | Einstieg |
| --- | --- | --- |
| LangChain | Eingebaut | `src/langgraph_builder_team/langchain_adapter.py` |
| LangChain.js | Eingebaut als Adapterpaket | `js-adapters/src/langchain.ts` |
| LangGraph | Eingebaut | `src/langgraph_builder_team/graph.py` |
| LangGraph Server | Eingebaut als Config | `langgraph.json` |
| LangGraph.js | Eingebaut als Adapterpaket | `js-adapters/src/langgraph.ts` |
| Deep Agents | Eingebaut als Starter/Runtime Adapter | `/integrations/deep-agents/code` |
| Deep Agents.js | Eingebaut als Adapterpaket | `js-adapters/src/deep-agents.ts` |
| Open SWE | Eingebaut als Task-Handoff | `/integrations/open-swe/task` |
| MCP Adapters | Eingebaut | `/mcp/tools`, `MCP_SERVERS_JSON` |
| Agent Protocol | Eingebaut | `/agent-protocol/*` |
| LangSmith | Konfigurierbar | `LANGSMITH_API_KEY`, `LANGCHAIN_TRACING_V2` |

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

Wichtige Production-Settings:

- `AUTH_ENABLED=true`
- `AUTH_USERNAME=admin`
- `AUTH_PASSWORD=<strong-password>`
- `AUTH_SESSION_SECRET=<long-random-secret>`
- `OPENAI_API_KEY=<provider-key>`
- `LLM_BASE_URL=<optional-openai-compatible-url>`
- `LLM_MODEL=<model-name>`

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
