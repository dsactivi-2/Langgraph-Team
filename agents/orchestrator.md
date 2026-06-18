# Agent Spec: Orchestrator

**Version:** 1.0
**Zuletzt aktualisiert:** 2026-06-18

## Rolle & Verantwortung

Koordiniert den Gesamtworkflow, waehlt den naechsten Agenten und erzwingt
Quality Gates, Reflection-Loops und Human Gates.

## Eingaben (aus State)

- `user_request`
- `plan`
- `generated_artifacts`
- `test_results`
- `review_feedback`
- `verification_result`
- `quality_score`
- `status`

## Ausgaben (in State schreiben)

- `current_agent`
- `decision_history`
- `status`
- `human_approval_points`
- `reflection_notes`

## Benoetigte Tools

- LangGraph `StateGraph`
- Optional: Human-approval UI
- Optional: structured LLM output parser

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/orchestrator.md`.

## State-Felder

**Liest:**

- `user_request`
- `plan`
- `quality_score`
- `verification_result`
- `review_feedback`

**Schreibt:**

- `current_agent`
- `decision_history`
- `status`
- `reflection_notes`

## Qualitaets-Kriterien / Gates

- Muss immer einen eindeutig naechsten Schritt bestimmen.
- Muss bei kritischen Review-Issues `NEEDS_HUMAN` setzen.
- Muss bei `quality_score < 75` eine Reflection-Schleife ausloesen.

## Beispiele

### Guter Output

```json
{
  "next_agent": "planner_architect",
  "action": "delegate",
  "reason": "No plan exists yet",
  "quality_gate_passed": false
}
```

### Schlechter Output

Freitext ohne `next_agent`, `action` oder nachvollziehbare Begruendung.
