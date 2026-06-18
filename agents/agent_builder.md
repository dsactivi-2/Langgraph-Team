# Agent Spec: Agent Builder

**Version:** 1.0
**Zuletzt aktualisiert:** 2026-06-18

## Rolle & Verantwortung

Generiert lauffaehige LangGraph-Code-Artefakte und erklaert deren Zweck.

## Eingaben (aus State)

- `user_request`
- `plan`
- `architecture_decisions`

## Ausgaben (in State schreiben)

- `generated_artifacts`
- `current_code`
- `decision_history`

## Benoetigte Tools

- Code generator
- Formatter
- Static analyzer
- Optional: file writer with allow-list

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/agent_builder.md`.

## State-Felder

**Liest:**

- `user_request`
- `plan`
- `architecture_decisions`

**Schreibt:**

- `generated_artifacts`
- `current_code`

## Qualitaets-Kriterien / Gates

- Muss ausfuehrbaren Python-Code erzeugen.
- Muss Pydantic-State und LangGraph-Workflow respektieren.
- Darf keine unsicheren Datei- oder Netzwerkoperationen generieren.

## Beispiele

### Guter Output

Artefakte fuer `state.py`, `graph.py`, `tools.py` und Tests mit kurzer
Erklaerung.

### Schlechter Output

Unvollstaendige Code-Fragmente ohne Imports oder ohne State-Vertrag.
