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

**Beispiel:**
```json
{"event":"agent_start","ts":"2026-05-11T14:32:00+00:00","agent":"developer","provider":"anthropic","model":"claude-sonnet-4-20250514"}
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

---

### `delegate`

Ein Agent delegiert an einen anderen Agenten.

| Feld    | Typ    | Beschreibung                        |
|---------|--------|-------------------------------------|
| `event` | string | `delegate`                          |
| `ts`    | string | ISO8601 Timestamp                   |
| `from`  | string | Delegierender Agent.                |
| `to`    | string | Ziel-Agent.                         |
| `task`  | string | Optional. Aufgabenbeschreibung.     |

**Beispiel:**
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

## Verwendung durch Agenten

Agenten emittieren Events über Bash-Befehle die in `scripts/lib/viz.py` durch `inject_viz_prompt_block()` generiert werden. Alle Events werden append-only in `.meta-viz/events.jsonl` geschrieben.
