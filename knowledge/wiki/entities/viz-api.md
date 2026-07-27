---
type: "API Reference"
title: "Viz-Report API-Dokumentation"
description: "Dieses Dokument beschreibt die HTTP-API-Endpunkte des viz-report.py WSGI-Servers."
tags: [api]
timestamp: "2026-07-27"
resource: "../../sources/docs/api/viz-api.md"
migrated_from: "docs/api/viz-api.md"
---
# Viz-Report API-Dokumentation

Dieses Dokument beschreibt die HTTP-API-Endpunkte des `viz-report.py` WSGI-Servers.

## Basis-URL

```
http://localhost:8765
```

## Endpunkte

### GET /

Liefert das Live-Dashboard (`docs/live-dashboard.html`).

**Response:** `text/html`

---

### GET /api/state

Aktueller Session-State (Agenten, Edges, Timeline) für das gewählte Zeitfenster.

**Query-Parameter:**

| Parameter | Typ    | Beschreibung                                           |
|-----------|--------|--------------------------------------------------------|
| `window`  | string | Optional. Zeitfenster-Filter (siehe Window-Formate).   |

**Window-Formate:**
- `15m`, `30m`, `60m` — Letzte N Minuten
- `1h`, `3h`, `6h`, `24h` — Letzte N Stunden
- `today` — Seit Mitternacht UTC
- `all` — Kein Filter (alle Events)

**Response:** `application/json`

```json
{
  "agents": {
    "orchestrator": {
      "status": "running",
      "started_at": "2026-05-11T14:32:00+00:00",
      "ended_at": null,
      "duration_sec": 120.5,
      "last_error": null,
      "tool_calls": 3,
      "tools_used": {"bash": 2, "read": 1},
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514"
    }
  },
  "edges": [
    {"from": "orchestrator", "to": "developer", "count": 2, "tasks": ["fix bug"], "ts": "2026-05-11T14:32:00+00:00"}
  ],
  "timeline": [
    {"ts": "2026-05-11T14:32:00+00:00", "icon": "▶", "msg": "orchestrator gestartet"}
  ],
  "duration_sec": 120.5,
  "session_start": "2026-05-11T14:32:00+00:00",
  "session_end": "2026-05-11T14:34:00+00:00",
  "session_name": "Dashboard-Verbesserungen"
}
```

---

### GET /api/events

Rohdaten aller Events im gewählten Zeitfenster.

**Query-Parameter:**

| Parameter | Typ    | Beschreibung                                         |
|-----------|--------|------------------------------------------------------|
| `window`  | string | Optional. Zeitfenster-Filter (siehe Window-Formate). |

**Response:** `application/json` — Array von Event-Objekten

---

### POST /api/clear-log

Leert das Event-Log atomar.

**Response:** `application/json`

```json
{"ok": true, "cleared": 142}
```

---

### GET /api/sessions

Liste aller bekannten Session-IDs.

**Response:** `application/json`

```json
["2026-05-11-abcd", "2026-05-10-efgh"]
```

---

### GET /api/session/<id>

Rohdaten aller Events einer bestimmten Session.

**Response:** `application/json` — Array von Event-Objekten

---

### GET /api/debug

Server-Debug-Informationen (Event-Count, Typ-Verteilung, etc.).

**Response:** `application/json`

```json
{
  "event_log": ".meta-viz/events.jsonl",
  "event_log_exists": true,
  "event_count": 142,
  "event_types": {"agent_start": 5, "agent_end": 5, "delegate": 3},
  "event_agents": {"orchestrator": 50, "developer": 30},
  "sessions": ["2026-05-11-abcd"],
  "debug_mode": false,
  "docs_dir": "docs"
}
```

## Fehler-Codes

| Status | Bedeutung                              |
|--------|----------------------------------------|
| 404    | Endpunkt oder Datei nicht gefunden.    |
| 500    | Interner Server-Fehler.                |

## Thread-Safety

Alle Lese-/Schreibzugriffe auf `events.jsonl` werden durch einen `threading.RLock` serialisiert. Der Server verwendet `ThreadingMixIn`, um parallele HTTP-Requests zu verarbeiten.