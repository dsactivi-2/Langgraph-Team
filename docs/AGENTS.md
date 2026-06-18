# Agents

## Orchestrator

Der Orchestrator ist im MVP als statischer LangGraph-Workflow umgesetzt. Die Entscheidungslogik ist durch die Kanten im Graphen abgebildet.

## Planner & Architect

Erstellt Ziele, Erfolgskriterien, Architekturentscheidungen und Risiken.

## Agent Builder

Erzeugt initiale LangGraph-Code-Artefakte.

## Memory, Skills & Tools Designer

Definiert Skill-Nutzung, neue Skill-Vorschlaege und Hermes-kompatible Profile.

## Executor & Sandbox Tester

Fuehrt deterministische Checks ueber Plan, Code, Artefakte und Memory-Design aus.

## Reviewer & Critic

Erstellt priorisiertes Feedback zu Architektur, Code und Deployment-Reife.

## Verifier & Evaluator

Berechnet den Quality Score und gibt eine Empfehlung aus.

## Git, Docs & Deployment Specialist

Erstellt Deployment-Hinweise und dokumentiert die naechsten Produktionsschritte.
