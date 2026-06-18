# Agent Spec: {{ agent_name }}

**Version:** 1.0
**Zuletzt aktualisiert:** {{ date }}

## Rolle & Verantwortung

Kurze Beschreibung der Rolle dieses Agents im Gesamtsystem.

## Eingaben (aus State)

- `user_request`
- `plan` (falls vorhanden)
- ...

## Ausgaben (in State schreiben)

- ...

## Benoetigte Tools

- ...

## Prompt-Strategie

Der Agent verwendet den System Prompt aus `prompts/{{ agent_name }}.md`.

## State-Felder

**Liest:**

- ...

**Schreibt:**

- ...

## Qualitaets-Kriterien / Gates

- Muss strukturierte Ausgabe liefern (JSON oder klar definierte Markdown Sections)
- Muss bei Unsicherheit `reflection_notes` befuellen
- Darf keine unsicheren Operationen ohne Sandbox durchfuehren

## Beispiele

### Guter Output

...

### Schlechter Output

...
