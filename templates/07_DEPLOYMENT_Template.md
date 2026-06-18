# Deployment Guide - {{ project_name }}

## Voraussetzungen

- Docker & Docker Compose (lokal)
- Postgres + Qdrant Instanz (Production)
- API Keys fuer die genutzten LLMs

## Schnellstart (lokal)

```bash
git clone {{ repo_url }}
cd {{ project_name }}
cp .env.example .env
docker compose up -d
```

## Environment Variables

| Variable | Beschreibung | Required | Beispiel |
| --- | --- | --- | --- |
| `POSTGRES_DSN` | Connection String fuer Checkpointer | Ja | `postgresql://user:pass@postgres:5432/db` |
| `QDRANT_URL` | Vector Store URL | Ja | `http://qdrant:6333` |
| `ANTHROPIC_API_KEY` | Claude API Key | Optional | `sk-ant-...` |
| `OPENAI_API_KEY` | OpenAI API Key | Optional | `sk-...` |

## Production Deployment (K3s / Kubernetes)

```bash
kubectl apply -f deployments/k3s/
```

## Health Checks & Monitoring

- LangSmith Project: `{{ project_name }}`
- Health Endpoint: `/health`
- Logs: `docker compose logs -f`

## Backup & Restore

Postgres Backup:

```bash
pg_dump {{ db_name }} > backup.sql
```

## Bekannte Limitationen

- ...
