# Deployment Guide - LangGraph Builder Team

## Voraussetzungen

- Docker & Docker Compose Plugin fuer lokales oder VPS-Deployment
- Postgres und Qdrant, entweder ueber `docker-compose.yml` oder externe
  Production-Instanzen
- Optional: API Keys fuer spaetere Live-LLM-Adapter
- SSH-Zugang fuer VPS-Deployment
- Optional: Domain mit DNS-A-Record auf die VPS-IP

## Offizielle Produkt-Trennung

Das Production-Setup trennt die Rollen nach LangChain/LangGraph/LangSmith:

| Rolle | Produkt | Subdomain | Service |
| --- | --- | --- | --- |
| Operator UI | Builder Team App | `builder.example.com` | `app:8000` |
| Builder API | Builder Team App | `api.example.com` | `app:8000` |
| Agent Runtime API | LangGraph Server | `graph.example.com` | `langgraph-server:2024` |
| Tracing/Evals | LangSmith | `smith.langchain.com` oder eigene LangSmith-Org-URL | extern |
| Runnables/Tools | LangChain | keine eigene Subdomain | Python/JS Library im Code |
| History/Checkpointing | Postgres | keine oeffentliche Subdomain | intern |
| Vector Memory | Qdrant | keine oeffentliche Subdomain | intern |

LangChain ist bewusst kein separater Web-Service. LangSmith wird nicht
nachgebaut, sondern ueber `LANGSMITH_*` und `LANGCHAIN_TRACING_V2` angebunden.

## Schnellstart (lokal)

```bash
git clone <repo-url>
cd langgraph-builder-team
cp .env.example .env
docker compose up -d --build
curl http://localhost:8000/health
```

Die lokale UI/API laeuft standardmaessig auf Port `8000`.

## Environment Variables

| Variable | Beschreibung | Required | Beispiel |
| --- | --- | --- | --- |
| `APP_NAME` | Anzeigename der App | Nein | `LangGraph Builder Team` |
| `APP_ENV` | Laufzeitumgebung | Nein | `production` |
| `QUALITY_THRESHOLD` | Mindestscore fuer Approve | Nein | `75` |
| `PUBLIC_BASE_DOMAIN` | Basisdomain fuer Subdomains | Production | `example.com` |
| `ACME_EMAIL` | E-Mail fuer TLS-Zertifikate | Production | `admin@example.com` |
| `BUILDER_HOST` | UI-Host | Production | `builder.example.com` |
| `API_HOST` | API-Host | Production | `api.example.com` |
| `LANGGRAPH_HOST` | LangGraph Server Host | Optional | `graph.example.com` |
| `BUILDER_PUBLIC_URL` | Oeffentliche UI URL | Nein | `https://builder.example.com` |
| `API_PUBLIC_URL` | Oeffentliche API URL | Nein | `https://api.example.com` |
| `LANGGRAPH_PUBLIC_URL` | Oeffentliche LangGraph URL | Nein | `https://graph.example.com` |
| `LANGSMITH_PUBLIC_URL` | LangSmith UI URL | Nein | `https://smith.langchain.com` |
| `POSTGRES_DB` | Datenbankname fuer Compose-Postgres | Ja | `builder` |
| `POSTGRES_USER` | Datenbanknutzer fuer Compose-Postgres | Ja | `builder` |
| `POSTGRES_PASSWORD` | Datenbankpasswort fuer Compose-Postgres | Ja | `change-me` |
| `POSTGRES_DSN` | Connection String fuer Checkpointer | Ja | `postgresql://builder:builder@postgres:5432/builder` |
| `QDRANT_URL` | Vector Store URL | Ja | `http://qdrant:6333` |
| `PROJECT_MEMORY_COLLECTION` | Qdrant Collection fuer Projektmemory | Nein | `project_memory` |
| `GLOBAL_MEMORY_COLLECTION` | Qdrant Collection fuer globales Wissen | Nein | `global_meta_knowledge` |
| `OPENAI_API_KEY` | OpenAI API Key fuer spaetere LLM-Adapter | Optional | `sk-...` |
| `ANTHROPIC_API_KEY` | Claude API Key fuer spaetere LLM-Adapter | Optional | `sk-ant-...` |
| `LANGSMITH_API_KEY` | LangSmith API Key fuer Tracing/Evaluation | Optional | `lsv2_...` |
| `LANGSMITH_PROJECT` | LangSmith Projektname | Nein | `LangGraph Builder Team` |
| `LANGSMITH_ENDPOINT` | LangSmith API Endpoint | Nein | `https://api.smith.langchain.com` |
| `LANGCHAIN_TRACING_V2` | LangChain/LangSmith Tracing aktivieren | Nein | `true` |
| `MCP_SERVERS_JSON` | JSON-Konfiguration fuer MCP Server | Optional | `{"github":{"transport":"stdio","command":"..."}}` |
| `AGENT_PROTOCOL_ENABLED` | Agent-Protocol-Endpunkte aktivieren | Nein | `true` |
| `LANGCONNECT_URL` | Externes LangConnect/RAG Backend | Optional | `https://...` |
| `OPEN_SWE_URL` | Externe Open-SWE Instanz fuer Handoffs | Optional | `https://...` |
| `POSTGRES_CHECKPOINTER_ENABLED` | LangGraph PostgresSaver aktivieren | Nein | `true` |
| `LLM_PROVIDER` | LLM Adapter Typ | Nein | `openai-compatible` |
| `LLM_BASE_URL` | OpenAI-kompatible Base URL | Optional | `https://api.openai.com/v1` |
| `LLM_MODEL` | Chat Completion Modell | Nein | `gpt-4o-mini` |
| `AUTH_ENABLED` | Login fuer UI/API aktivieren | Nein | `true` |
| `AUTH_USERNAME` | Login-Benutzer | Wenn Auth aktiv | `admin` |
| `AUTH_PASSWORD` | Login-Passwort | Wenn Auth aktiv | `change-me` |
| `AUTH_SESSION_SECRET` | Cookie-Signatur-Secret | Wenn Auth aktiv | `long-random-secret` |

Der aktuelle MVP laeuft deterministisch ohne LLM-Key. Sobald Live-LLM-Nodes
aktiviert werden, muessen die passenden Provider-Secrets gesetzt werden.

Fuer Production muessen mindestens `POSTGRES_PASSWORD` und `POSTGRES_DSN` auf
starke, VPS-spezifische Werte geaendert werden. Wenn die UI oeffentlich
erreichbar ist, muss `AUTH_ENABLED=true` gesetzt werden.

## VPS Deployment per SSH

```bash
ssh user@your-vps
git clone <repo-url> langgraph-builder-team
cd langgraph-builder-team
cp .env.example .env
docker compose up -d --build
curl http://localhost:8000/health
```

## VPS Deployment mit Subdomains

DNS vorbereiten:

```text
builder.example.com  A  <VPS-IP>
api.example.com      A  <VPS-IP>
graph.example.com    A  <VPS-IP>
```

`.env` auf dem VPS setzen:

```bash
APP_ENV=production
PUBLIC_BASE_DOMAIN=example.com
ACME_EMAIL=admin@example.com
BUILDER_HOST=builder.example.com
API_HOST=api.example.com
LANGGRAPH_HOST=graph.example.com
BUILDER_PUBLIC_URL=https://builder.example.com
API_PUBLIC_URL=https://api.example.com
LANGGRAPH_PUBLIC_URL=https://graph.example.com
LANGSMITH_PUBLIC_URL=https://smith.langchain.com
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD=<strong-password>
AUTH_SESSION_SECRET=<long-random-secret>
POSTGRES_PASSWORD=<strong-db-password>
POSTGRES_DSN=postgresql://builder:<strong-db-password>@postgres:5432/builder
QDRANT_URL=http://qdrant:6333
LANGCHAIN_TRACING_V2=true
LANGSMITH_API_KEY=<langsmith-key>
LANGSMITH_PROJECT=LangGraph Builder Team
```

Start:

```bash
docker compose -f docker-compose.yml -f docker-compose.official.yml up -d --build
docker compose -f docker-compose.yml -f docker-compose.official.yml ps
```

Pruefen:

```bash
curl -fsS https://builder.example.com/health
curl -fsS https://api.example.com/health
curl -fsS https://graph.example.com/docs
```

Wenn `graph.example.com` nicht oeffentlich erreichbar sein soll, keinen
DNS-Record setzen und den `langgraph-server` nur intern verwenden.

## VPS Deployment per Script

```bash
export VPS_HOST=203.0.113.10
export VPS_USER=deploy
export VPS_PATH=/opt/langgraph-builder-team
./scripts/deploy_vps.sh
```

Das Skript synchronisiert den Workspace per `rsync`, legt auf dem Server bei
Bedarf `.env` aus `.env.example` an und startet `docker compose up -d --build`.

## Production Deployment (K3s / Kubernetes)

Ein minimales K3s-Manifest liegt unter
[deployments/k3s/app.yaml](../deployments/k3s/app.yaml).

```bash
kubectl apply -f deployments/k3s/
```

Fuer produktive K3s-Nutzung muessen Image Registry, Secrets, Ingress und
persistente Datenbanken projektspezifisch ergaenzt werden.

## Reverse Proxy & TLS

Fuer Produktivbetrieb sollte vor der App ein Reverse Proxy mit TLS laufen, zum
Beispiel Caddy, Traefik oder Nginx.

Das Repo enthaelt dafuer `deployments/caddy/Caddyfile` und
`docker-compose.official.yml`. Caddy terminiert TLS und routet:

```text
builder.example.com -> app:8000
api.example.com     -> app:8000
graph.example.com   -> langgraph-server:2024
```

## Health Checks & Monitoring

- Health Endpoint: `/health`
- LangGraph Server Health/Docs: `https://graph.example.com/docs`
- Auth Status: `/auth/status`
- Memory Search: `/memory/search`
- Chat History: `/chat/{project_id}`
- LLM Test: `/llm/complete`
- Integration Matrix: `/integrations`
- Agent Protocol: `/agent-protocol/info`, `/agent-protocol/threads`, `/agent-protocol/runs`
- MCP Tools: `/mcp/tools`
- Open SWE Handoff: `/integrations/open-swe/task`
- LangConnect Query: `/integrations/langconnect/query`
- Lokale Logs: `docker compose logs -f`
- App Logs: `docker compose logs -f app`
- Postgres Status: `docker compose ps postgres`
- Optional spaeter: LangSmith Project `LangGraph Builder Team`

## Backup & Restore

Postgres Backup aus dem Compose-Stack:

```bash
docker compose exec postgres pg_dump -U builder builder > backup.sql
```

Postgres Restore:

```bash
cat backup.sql | docker compose exec -T postgres psql -U builder builder
```

Qdrant-Daten liegen im Volume `qdrant_data`. Fuer Production sollten Snapshots
oder volume-level Backups eingerichtet werden.

## Bekannte Limitationen

- Auth ist in `.env.example` fuer lokale Entwicklung standardmaessig deaktiviert.
- Die LLM-Nodes nutzen den Adapter noch nicht automatisch in jedem Agenten;
  `/llm/complete` stellt die Runtime-Integration bereit.
- K3s-Manifeste sind ein Basis-Startpunkt und noch kein vollstaendiges
  Production-Cluster-Setup.
- Echtes VPS-Deployment kann erst mit Host/IP und SSH-User ausgefuehrt werden.
