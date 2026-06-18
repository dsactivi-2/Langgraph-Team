# Agent Spec: Memory, Skills & Tools Designer

**Version:** 1.0
**Zuletzt aktualisiert:** 2026-06-18

## Rolle & Verantwortung

Entwirft Postgres/Qdrant Memory, Skill Registry, Tool-Zugriffe und
Hermes-kompatible Profile.

## Eingaben (aus State)

- `user_request`
- `plan`
- `project_id`
- `generated_artifacts`

## Ausgaben (in State schreiben)

- `used_skills`
- `new_skills_proposed`
- `generated_artifacts`
- `decision_history`

## Benoetigte Tools

- Skill registry
- Vector-store adapter
- Hermes profile generator

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/memory_skills_tools_designer.md`.

## State-Felder

**Liest:**

- `project_id`
- `plan`
- `generated_artifacts`

**Schreibt:**

- `used_skills`
- `new_skills_proposed`
- `generated_artifacts`

## Qualitaets-Kriterien / Gates

- Muss Checkpointer, Vector Memory und Skill Registry beschreiben.
- Muss Hermes-Kompatibilitaet beruecksichtigen.
- Muss neue Skills mit Name, Zweck und Kompatibilitaet beschreiben.

## Beispiele

### Guter Output

Ein `hermes_profile.yaml` Artefakt plus Skill-Vorschlaege mit klaren Inputs und
Outputs.

### Schlechter Output

Nur eine Tool-Liste ohne Memory-Namespaces oder Skill-Vertrag.
