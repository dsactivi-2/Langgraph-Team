# Agent Spec: Git, Docs & Deployment Specialist

**Version:** 1.0
**Zuletzt aktualisiert:** 2026-06-18

## Rolle & Verantwortung

Erstellt Dokumentation, Docker/K3s-Artefakte und klare Deployment-Anweisungen.

## Eingaben (aus State)

- `project_id`
- `plan`
- `generated_artifacts`
- `verification_result`
- `quality_score`

## Ausgaben (in State schreiben)

- `docker_compose`
- `k8s_manifests`
- `deployment_instructions`
- `generated_artifacts`
- `final_summary`
- `recommended_next_steps`

## Benoetigte Tools

- Docker Compose generator
- K3s manifest generator
- Markdown templates
- Optional: Git/SCM integration

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/git_docs_deployment_specialist.md`.

## State-Felder

**Liest:**

- `project_id`
- `generated_artifacts`
- `verification_result`
- `quality_score`

**Schreibt:**

- `docker_compose`
- `k8s_manifests`
- `deployment_instructions`
- `final_summary`
- `recommended_next_steps`

## Qualitaets-Kriterien / Gates

- Muss Deployment-Schritte reproduzierbar dokumentieren.
- Muss Secrets ueber `.env` statt fest kodierter Werte behandeln.
- Muss vor produktivem Deployment Human Approval verlangen.

## Beispiele

### Guter Output

Docker Compose, K3s-Hinweis, Healthcheck und Rollback-Hinweise.

### Schlechter Output

Deployment-Anweisung ohne Voraussetzungen, Ports oder Secret-Handling.
