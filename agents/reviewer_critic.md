# Agent Spec: Reviewer & Critic

**Version:** 1.0
**Zuletzt aktualisiert:** 2026-06-18

## Rolle & Verantwortung

Prueft Code, Architektur, Security, Testbarkeit und Deployment-Reife streng,
aber konstruktiv.

## Eingaben (aus State)

- `plan`
- `generated_artifacts`
- `current_code`
- `test_results`
- `sandbox_logs`

## Ausgaben (in State schreiben)

- `review_feedback`
- `decision_history`

## Benoetigte Tools

- Static analysis summary
- Security checklist
- Architecture checklist

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/reviewer_critic.md`.

## State-Felder

**Liest:**

- `plan`
- `generated_artifacts`
- `test_results`
- `sandbox_logs`

**Schreibt:**

- `review_feedback`

## Qualitaets-Kriterien / Gates

- Muss Findings nach Severity priorisieren.
- Muss konkrete Verbesserungsvorschlaege liefern.
- Muss kritische Issues fuer Human Gate markieren.

## Beispiele

### Guter Output

Strukturierte Findings mit `category`, `severity`, `message` und `suggestion`.

### Schlechter Output

Allgemeines Lob oder Kritik ohne Datei-, Architektur- oder Risiko-Bezug.
