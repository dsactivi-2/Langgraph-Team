# Agent Spec: Verifier & Evaluator

**Version:** 1.0
**Zuletzt aktualisiert:** 2026-06-18

## Rolle & Verantwortung

Berechnet den finalen Quality Score, entscheidet ueber Approve/Revise/Reject und
stoesst bei Bedarf Reflection an.

## Eingaben (aus State)

- `test_results`
- `review_feedback`
- `generated_artifacts`
- `plan`

## Ausgaben (in State schreiben)

- `verification_result`
- `quality_score`
- `status`
- `reflection_notes`

## Benoetigte Tools

- Scoring rubric
- Structured output validator
- Optional: eval dataset runner

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/verifier_evaluator.md`.

## State-Felder

**Liest:**

- `test_results`
- `review_feedback`
- `generated_artifacts`
- `plan`

**Schreibt:**

- `verification_result`
- `quality_score`
- `status`
- `reflection_notes`

## Qualitaets-Kriterien / Gates

- Muss Score zwischen 0 und 100 liefern.
- Muss `approve`, `revise` oder `reject` setzen.
- Muss bei Score unter 75 Reflection empfehlen.

## Beispiele

### Guter Output

JSON mit `overall_score`, `category_scores`, `recommendation` und
Verbesserungsvorschlaegen.

### Schlechter Output

Eine subjektive Bewertung ohne Score oder klare Empfehlung.
