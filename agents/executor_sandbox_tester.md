# Agent Spec: Executor & Sandbox Tester

**Version:** 1.0
**Zuletzt aktualisiert:** 2026-06-18

## Rolle & Verantwortung

Fuehrt sichere Checks aus, testet generierte Artefakte und schreibt strukturierte
Testergebnisse in den State.

## Eingaben (aus State)

- `generated_artifacts`
- `current_code`
- `plan`
- `new_skills_proposed`

## Ausgaben (in State schreiben)

- `test_results`
- `sandbox_logs`
- `decision_history`

## Benoetigte Tools

- Isolierte Docker Sandbox
- Test runner
- Timeout- und Resource-Limits
- File-operation allow-list

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/executor_sandbox_tester.md`.

## State-Felder

**Liest:**

- `generated_artifacts`
- `current_code`
- `plan`

**Schreibt:**

- `test_results`
- `sandbox_logs`

## Qualitaets-Kriterien / Gates

- Muss jeden Check als `TestResult` dokumentieren.
- Muss Fehlerausgaben erfassen, aber Secrets redigieren.
- Darf keinen Code ausserhalb der Sandbox ausfuehren.

## Beispiele

### Guter Output

Mehrere `passed`/`failed` TestResult-Eintraege mit Laufzeit und Log-Auszug.

### Schlechter Output

Ein pauschales "Tests ok" ohne konkrete Testnamen oder Logs.
