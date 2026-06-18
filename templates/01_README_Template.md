# {{ project_name }}

> {{ short_description }}

## Uebersicht

{{ long_description }}

## Ziele & Erfolgskriterien

- [ ] ...
- [ ] ...

## Architektur

Siehe [ARCHITECTURE.md](./ARCHITECTURE.md)

## Agents

Siehe [AGENTS.md](./AGENTS.md) oder die einzelnen Agent Specs im Ordner `agents/`.

## Memory & Skills

- **Checkpointer**: Postgres (empfohlen)
- **Vector Memory**: Qdrant (Namespace = `{{ project_id }}`)
- **Skill Registry**: Siehe `skills/`

## Quick Start (lokal)

```bash
docker compose up -d
```

## Production Deployment

Siehe [DEPLOYMENT.md](./DEPLOYMENT.md)

## Entwicklung & Beitragen

Siehe [DEVELOPMENT.md](./DEVELOPMENT.md)

## Lizenz

MIT License
