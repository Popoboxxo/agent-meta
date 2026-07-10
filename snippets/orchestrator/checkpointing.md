{{#if CHECKPOINTING_ENABLED}}
## Checkpointing

Persistente Session-Checkpoints für lange Orchestrierungen (>5 Schritte).

**Format** — `.meta-viz/checkpoint-<timestamp>.json`:
```json
{
  "session_id": "<YYYYMMDD-HHMMSS>",
  "created_at": "<ISO-8601>",
  "task_summary": "<Ein-Satz-Beschreibung der Gesamtaufgabe>",
  "completed_steps": [
    { "step": 1, "agent": "<agent>", "result_key": "<key>", "status": "done" }
  ],
  "pending_steps": [
    { "step": 2, "agent": "<agent>", "task": "<task-summary>" }
  ],
  "context": "<Zusammenfassung relevanter Zwischenergebnisse, max. 3 Sätze>"
}
```

**Wann schreiben:** Vor jedem BARRIER-Punkt — also nachdem alle parallelen Sub-Tasks
gestartet wurden, aber bevor auf ihre Ergebnisse gewartet wird. Sichert den
Fortschritt gegen Context-Reset während laufender Delegation.

**Wann lesen:** Beim Start einer neuen Session prüfen ob Checkpoints existieren:
1. `.meta-viz/checkpoint-*.json` scannen (neuester zuerst nach `created_at`)
2. Wenn Checkpoint gefunden → User informieren:
   > "Es gibt einen unvollständigen Checkpoint vom `<created_at>`: `<task_summary>`.
   > Fortsetzen ab Schritt `<nächster pending_step>`?"
3. Bei Bestätigung → `pending_steps` sequentiell abarbeiten, `completed_steps` überspringen
4. Nach Abschluss: Checkpoint-Datei löschen

**Cleanup:** Checkpoints älter als 24h automatisch löschen (beim nächsten Start).
Maximale Checkpoint-Größe: 50 KB — große `context`-Felder kürzen.
{{/if}}
