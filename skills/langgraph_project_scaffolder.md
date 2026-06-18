# Skill Definition: langgraph_project_scaffolder

**Version:** 1.0
**Hermes-kompatibel:** Ja

## Beschreibung

Generiert LangGraph-Projektskelette mit typisiertem State, Workflow-Graph,
Tests, Dokumentation und Deployment-Artefakten. Die Skill ist fuer Builder-Teams
gedacht, die aus einer Projektanfrage ein lauffaehiges, pruefbares und
self-hostbares Repository erzeugen.

## Input Schema

```json
{
  "type": "object",
  "properties": {
    "user_request": {
      "type": "string",
      "description": "Natural-language request describing the LangGraph project to build."
    },
    "project_id": {
      "type": "string",
      "description": "Optional stable project identifier."
    },
    "deployment_target": {
      "type": "string",
      "enum": ["local", "docker-compose", "k3s", "vps"],
      "default": "docker-compose"
    },
    "quality_threshold": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100,
      "default": 75
    }
  },
  "required": ["user_request"]
}
```

## Output Schema

```json
{
  "type": "object",
  "properties": {
    "project_id": {
      "type": "string"
    },
    "status": {
      "type": "string",
      "enum": ["completed", "needs_human", "failed", "reflection"]
    },
    "quality_score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100
    },
    "artifacts": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "filename": {"type": "string"},
          "artifact_type": {"type": "string"},
          "description": {"type": "string"}
        },
        "required": ["filename", "artifact_type"]
      }
    },
    "deployment_instructions": {
      "type": "string"
    },
    "recommended_next_steps": {
      "type": "array",
      "items": {"type": "string"}
    }
  },
  "required": ["project_id", "status", "quality_score", "artifacts"]
}
```

## Implementation

- **Typ**: LangGraph Tool / Node / Hermes Skill
- **Datei**: `skills/langgraph_project_scaffolder.py`
- **Abhaengigkeiten**: LangGraph, Pydantic, Docker Compose, optional Qdrant und Postgres

## Beispiele

### Beispiel 1

**Input:**

```json
{
  "user_request": "Build a LangGraph agent workflow with planner, builder, tester and deployer.",
  "project_id": "customer-agent-builder",
  "deployment_target": "vps",
  "quality_threshold": 75
}
```

**Output:**

```json
{
  "project_id": "customer-agent-builder",
  "status": "completed",
  "quality_score": 90,
  "artifacts": [
    {
      "filename": "graph.py",
      "artifact_type": "code",
      "description": "Generated LangGraph workflow."
    },
    {
      "filename": "docker-compose.yml",
      "artifact_type": "docker",
      "description": "Self-hosting deployment stack."
    }
  ],
  "deployment_instructions": "Run docker compose up -d --build on the target VPS.",
  "recommended_next_steps": [
    "Configure production secrets",
    "Enable Postgres checkpointer",
    "Run sandbox tests"
  ]
}
```

## Version History

| Version | Datum | Aenderungen |
| --- | --- | --- |
| 1.0 | 2026-06-18 | Initiale Version |

## Hinweise zur Hermes-Integration

Diese Skill kann direkt in ein Hermes-Profil uebernommen werden. Im aktuellen
Builder-Workflow wird ein `hermes_profile.yaml` Artefakt erzeugt, das diese
Skill als Projekt-Scaffolding-Faehigkeit referenzieren kann.
