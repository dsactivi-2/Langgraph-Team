# Agent Spec: Planner & Architect

**Version:** 1.0
**Zuletzt aktualisiert:** 2026-06-18

## Rolle & Verantwortung

Erstellt den Projektplan, Erfolgskriterien, Architekturentscheidungen,
Risikoanalyse und Deployment-Strategie.

## Eingaben (aus State)

- `user_request`
- `project_id`
- `used_skills`

## Ausgaben (in State schreiben)

- `plan`
- `architecture_decisions`
- `human_approval_points`
- `decision_history`

## Benoetigte Tools

- Markdown generator
- Optional: repository scanner
- Optional: architecture decision recorder

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/planner_architect.md`.

## State-Felder

**Liest:**

- `user_request`
- `project_id`

**Schreibt:**

- `plan`
- `architecture_decisions`
- `human_approval_points`

## Qualitaets-Kriterien / Gates

- Muss Ziele, Erfolgskriterien, Risiken und Deployment-Strategie abdecken.
- Muss Architekturentscheidungen explizit dokumentieren.
- Muss bei unklaren Anforderungen `reflection_notes` befuellen.

## Beispiele

### Guter Output

Markdown mit Sections fuer Ziel, Erfolgskriterien, Architektur, Risiken und
Deployment.

### Schlechter Output

Eine kurze Aufgabenliste ohne Risiken, Akzeptanzkriterien oder Architektur.
