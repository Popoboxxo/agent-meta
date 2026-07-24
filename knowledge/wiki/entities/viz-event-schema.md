---
type: "API Reference"
title: "Viz-Event-Schema"
description: "Dieses Dokument beschreibt alle Event-Typen die in .meta-viz/events.jsonl protokolliert werden."
tags: [api]
timestamp: "2026-07-19T10:29:50Z"
resource: "../../sources/docs/api/viz-event-schema.md"
migrated_from: "docs/api/viz-event-schema.md"
---
# Viz-Event-Schema

Dieses Dokument beschreibt alle Event-Typen die in `.meta-viz/events.jsonl` protokolliert werden.

Jede Zeile ist ein JSON-Objekt (JSONL-Format). Alle Events tragen ein `ts`-Feld (ISO8601 Timestamp, UTC).

## Event-Typen

### `session_start`

Markiert den Beginn einer neuen Session.

| Feld      | Typ    | Beschreibung                     |
|-----------|--------|----------------------------------|
| `event`   | string | `session_start`                  |
| `ts`      | string | ISO8601 Timestamp                |
| `payload` | object | Enthält `task` (Session-Name).   |

**Beispiel:**
```json
{"event":"session_start","ts":"2026-05-11T14:00:00+00:00","payload":{"task":"Dashboard-Verbesserungen"}}
```

---

### `session_end`

Markiert das Ende einer Session.

| Feld    | Typ    | Beschreibung      |
|---------|--------|-------------------|
| `event` | string | `session_end`     |
| `ts`    | string | ISO8601 Timestamp |

**Beispiel:**
```json
{"event":"session_end","ts":"2026-05-11T14:30:00+00:00"}
```

---

### `agent_start`

Ein Agent beginnt mit der Aufgabenbearbeitung.

| Feld       | Typ    | Beschreibung                                |
|------------|--------|---------------------------------------------|
| `event`    | string | `agent_start`                               |
| `ts`       | string | ISO8601 Timestamp                           |
| `agent`    | string | Name des Agenten (z.B. `developer`).        |
| `provider` | string | Optional. KI-Provider (z.B. `anthropic`).   |
| `model`    | string | Optional. Modell-ID (z.B. `claude-sonnet`). |
| `caller`   | string | Optional. Name des delegierenden Agenten (Eltern-Agent). |
| `task_id`  | string | Optional. Eindeutige UUID für Delegation-Tracking. |

**Beispiel (ohne Delegation):**
```json
{"event":"agent_start","ts":"2026-05-11T14:32:00+00:00","agent":"developer","provider":"anthropic","model":"claude-sonnet-4-20250514"}
```

**Beispiel (mit Delegation):**
```json
{"event":"agent_start","ts":"2026-05-11T14:32:00+00:00","agent":"developer","provider":"anthropic","model":"claude-sonnet-4-20250514","caller":"orchestrator","task_id":"550e8400-e29b-41d4-a716-446655440000"}
```

---

### `agent_end`

Ein Agent hat seine Aufgabe beendet.

| Feld         | Typ     | Beschreibung                                       |
|--------------|---------|----------------------------------------------------|
| `event`      | string  | `agent_end`                                        |
| `ts`         | string  | ISO8601 Timestamp                                  |
| `agent`      | string  | Name des Agenten.                                  |
| `status`     | string  | `success` oder `error`.                            |
| `target`     | string  | Optional. Name des Agenten der diesen Agent delegiert hat (für Delegation-Tracking). |
| `payload`    | object  | Bei `error`: enthält `error`-Nachricht.            |
| `tokens_in`  | integer | Optional. Input-Token-Anzahl dieser Ausführung.    |
| `tokens_out` | integer | Optional. Output-Token-Anzahl dieser Ausführung.   |

**Beispiel (Erfolg):**
```json
{"event":"agent_end","ts":"2026-05-11T14:35:00+00:00","agent":"developer","status":"success"}
```

**Beispiel (Erfolg mit Tokens):**
```json
{"event":"agent_end","ts":"2026-05-11T14:35:00+00:00","agent":"developer","status":"success","tokens_in":1500,"tokens_out":350}
```

**Beispiel (Fehler):**
```json
{"event":"agent_end","ts":"2026-05-11T14:35:00+00:00","agent":"developer","status":"error","payload":{"error":"Datei nicht gefunden"}}
```

**Beispiel (mit Rückgabe an Delegator):**
```json
{"event":"agent_end","ts":"2026-05-11T14:35:00+00:00","agent":"developer","status":"success","target":"orchestrator","tokens_in":1500,"tokens_out":350}
```

---

### `delegate_out`

Ein Agent delegiert an einen anderen Agenten (ausgehende Delegation).

| Feld     | Typ    | Beschreibung                                  |
|----------|--------|-----------------------------------------------|
| `event`  | string | `delegate_out`                                |
| `ts`     | string | ISO8601 Timestamp                             |
| `agent`  | string | Name des delegierenden Agenten.               |
| `target` | string | Name des Ziel-Agenten.                        |
| `task_id`| string | Optional. Eindeutige UUID für Correlation.    |
| `task`   | string | Optional. Aufgabenbeschreibung.               |

**Beispiel:**
```json
{"event":"delegate_out","ts":"2026-05-11T14:33:00+00:00","agent":"orchestrator","target":"developer","task_id":"550e8400-e29b-41d4-a716-446655440000","task":"Bugfix implementieren"}
```

---

### `delegate` (Legacy Alias)

Veraltertes Event-Format für Delegationen. Wird noch akzeptiert für Rückwärtskompatibilität, sollte aber durch `delegate_out` ersetzt werden.

| Feld    | Typ    | Beschreibung                        |
|---------|--------|-------------------------------------|
| `event` | string | `delegate`                          |
| `ts`    | string | ISO8601 Timestamp                   |
| `from`  | string | Delegierender Agent.                |
| `to`    | string | Ziel-Agent.                         |
| `task`  | string | Optional. Aufgabenbeschreibung.     |

**Beispiel (nicht empfohlen):**
```json
{"event":"delegate","ts":"2026-05-11T14:33:00+00:00","from":"orchestrator","to":"developer","task":"Bugfix implementieren"}
```

---

### `tool_call`

Ein Agent führt ein Tool aus.

| Feld    | Typ    | Beschreibung              |
|---------|--------|---------------------------|
| `event` | string | `tool_call`               |
| `ts`    | string | ISO8601 Timestamp         |
| `agent` | string | Name des Agenten.         |
| `tool`  | string | Name des Tools (z.B. `bash`, `read`, `edit`). |

**Beispiel:**
```json
{"event":"tool_call","ts":"2026-05-11T14:33:30+00:00","agent":"developer","tool":"edit"}
```

---

### `log`

Ein Agent protokolliert eine Nachricht.

| Feld      | Typ    | Beschreibung                              |
|-----------|--------|-------------------------------------------|
| `event`   | string | `log`                                     |
| `ts`      | string | ISO8601 Timestamp                         |
| `agent`   | string | Name des Agenten.                         |
| `payload` | object | Enthält `level` (`info`/`warn`/`error`) und `message`. |

**Beispiel:**
```json
{"event":"log","ts":"2026-05-11T14:34:00+00:00","agent":"developer","payload":{"level":"info","message":"Datei erfolgreich geschrieben"}}
```

---

## A2A Handoff Debug Events

Diese Events werden **nur im Debug-Modus** emittiert (wenn `viz.debug: true` in `project.yaml` konfiguriert ist). Sie verfolgen die Details von Agent-zu-Agent-Handoffs auf der Protokoll-Ebene.

### `a2a_handoff_start`

Ein A2A-Envelope wurde erstellt und ist bereit für Dispatch.

| Feld     | Typ    | Beschreibung                                  |
|----------|--------|-----------------------------------------------|
| `event`  | string | `a2a_handoff_start`                           |
| `ts`     | string | ISO8601 Timestamp                             |
| `task_id`| string | Eindeutige UUID für diesen Handoff.           |
| `payload`| object | Enthält `handoff_id` und `contract` Details. |

**Beispiel:**
```json
{"event":"a2a_handoff_start","ts":"2026-05-11T14:33:05+00:00","task_id":"550e8400-e29b-41d4-a716-446655440000","payload":{"handoff_id":"HOFF-001","contract":"standard"}}
```

---

### `a2a_handoff_validated`

Ein A2A-Envelope wurde validiert und akzeptiert.

| Feld     | Typ    | Beschreibung                                  |
|----------|--------|-----------------------------------------------|
| `event`  | string | `a2a_handoff_validated`                       |
| `ts`     | string | ISO8601 Timestamp                             |
| `task_id`| string | Eindeutige UUID des Handoffs.                 |
| `payload`| object | Enthält `handoff_id` und `valid: true`.       |

**Beispiel:**
```json
{"event":"a2a_handoff_validated","ts":"2026-05-11T14:33:06+00:00","task_id":"550e8400-e29b-41d4-a716-446655440000","payload":{"handoff_id":"HOFF-001","valid":true}}
```

---

### `a2a_handoff_delivered`

Ein A2A-Envelope wurde an den Ziel-Agenten delivered.

| Feld     | Typ    | Beschreibung                                  |
|----------|--------|-----------------------------------------------|
| `event`  | string | `a2a_handoff_delivered`                       |
| `ts`     | string | ISO8601 Timestamp                             |
| `task_id`| string | Eindeutige UUID des Handoffs.                 |
| `payload`| object | Enthält `handoff_id` und `status: accepted`.  |

**Beispiel:**
```json
{"event":"a2a_handoff_delivered","ts":"2026-05-11T14:33:07+00:00","task_id":"550e8400-e29b-41d4-a716-446655440000","payload":{"handoff_id":"HOFF-001","status":"accepted"}}
```

---

### `a2a_handoff_failed`

Ein A2A-Envelope-Handoff ist fehlgeschlagen.

| Feld     | Typ    | Beschreibung                                  |
|----------|--------|-----------------------------------------------|
| `event`  | string | `a2a_handoff_failed`                          |
| `ts`     | string | ISO8601 Timestamp                             |
| `task_id`| string | Eindeutige UUID des Handoffs.                 |
| `payload`| object | Enthält `handoff_id` und `errors: [...]`.     |

**Beispiel:**
```json
{"event":"a2a_handoff_failed","ts":"2026-05-11T14:33:08+00:00","task_id":"550e8400-e29b-41d4-a716-446655440000","payload":{"handoff_id":"HOFF-001","errors":["Validation failed: missing required field"]}}
```

---

### `a2a_supersession`

Ein A2A-Handoff wurde durch einen neueren Handoff überschrieben (Supersession).

| Feld     | Typ    | Beschreibung                                  |
|----------|--------|-----------------------------------------------|
| `event`  | string | `a2a_supersession`                            |
| `ts`     | string | ISO8601 Timestamp                             |
| `task_id`| string | Eindeutige UUID des neuen Handoffs.           |
| `payload`| object | Enthält `handoff_id`, `supersedes` und `reason`. |

**Beispiel:**
```json
{"event":"a2a_supersession","ts":"2026-05-11T14:33:09+00:00","task_id":"550e8400-e29b-41d4-a716-446655440001","payload":{"handoff_id":"HOFF-002","supersedes":"HOFF-001","reason":"Delegation retried with updated parameters"}}
```

---

## Verwendung durch Agenten

Agenten emittieren Events über das MCP-Tool `log_viz_event` oder über Bash-Befehle, die in `scripts/lib/viz.py` durch `inject_viz_prompt_block()` generiert werden. Alle Events werden append-only in `.meta-viz/events.jsonl` geschrieben.

**Hinweis:** Die A2A Debug Events werden nur emittiert, wenn der Visualisierungsmodus mit `viz.debug: true` aktiviert ist.
