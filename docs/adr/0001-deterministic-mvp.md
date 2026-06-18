# ADR 0001: Deterministischer MVP vor Live-LLM-Orchestrierung

## Status

Accepted

## Kontext

Das Builder Team soll lokal, in CI und auf einem VPS reproduzierbar starten,
auch wenn noch kein LLM-Key gesetzt ist.

## Entscheidung

Die ersten Agent-Nodes sind deterministisch implementiert. Sie erzeugen
strukturierte Plaene, Artefakte, Reviews und Scores ohne externen Modellaufruf.

## Konsequenzen

- Tests sind stabil und schnell.
- Docker-Deployment funktioniert ohne Secret-Abhaengigkeit.
- Echte LLM-Adapter koennen spaeter pro Node ergaenzt werden.
