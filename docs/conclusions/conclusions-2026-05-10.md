# Erkenntnisse — 10. Mai 2026

## Session-Zusammenfassung

Framework Health-Check + Visualisierungs-System Fix. Das Viz-Event-Logging war konfiguriert (`viz: enabled: true, mode: full`), aber `.agent-meta/viz/events.jsonl` blieb leer. Ursache und Lösung identifiziert, implementiert und verifiziert.

---

## 1. Root Cause: Agenten loggen nicht freiwillig

### Problem
- `inject_viz_prompt_block()` in `scripts/lib/viz.py` formulierte die Event-Logging-Anweisung als **"Optional — nur wenn dynamischer Modus aktiv"**
- LLMs interpretieren "optional" wörtlich → sie loggen praktisch nie
- Ergebnis: Viz-Dashboard blieb leer trotz aktivierter Konfiguration

### Lösung
- Überschrift geändert: `Optional` → `Pflicht-Anweisung`
- Einleitung geändert: `Wenn der Visualisierungsmodus aktiviert ist, berichte...` → `Der Visualisierungsmodus ist aktiv. Du MUSST deinen Status protokollieren.`
- Abschluss geändert: `Dies ist optional` → `Dies ist eine Pflicht-Anweisung. Jeder Agenten-Aufruf MUSS protokolliert werden.`

### Erkenntnis
LLMs folgen wörtlichen Instruktionen. "Optional" in Prompt-Blöcken bedeutet für das Modell: "Darf ich weglassen" — nicht "Wenn du Lust hast". Pflicht-Anweisungen müssen explizit als solche formuliert sein.

---

## 2. System-Hook als Backup-Lösung

### Problem
Selbst mit Pflicht-Prompt bleibt die Zuverlässigkeit LLM-abhängig. Agenten können den Prompt "vergessen" oder priorisieren anderes.

### Lösung: `viz-log.sh` PreToolUse Hook
- **Neue Datei:** `hooks/1-generic/viz-log.sh`
- Intercepted JEDEN Tool-Aufruf auf System-Ebene (vor Ausführung)
- Extrahiert aus dem Hook-Kontext: `tool_name`, `tool_input` (Preview), `agent_name`, `provider`
- Schreibt automatisch `tool_call`-Event in `.agent-meta/viz/events.jsonl`
- Exit 0 — blockiert den Tool-Aufruf nicht

### Provider-Abdeckung
| Provider | Hook-Infrastruktur | Logging |
|----------|-------------------|---------|
| Claude Code | ✅ PreToolUse | Hook + Prompt |
| Gemini CLI | ✅ PreToolUse | Hook + Prompt |
| Opencode | ❌ Keine Hooks | Nur Prompt |
| Continue | ❌ Keine Hooks | Nur Prompt |

---

## 3. Conditional Hook-Management in sync.py

### Neue Logik in `scripts/lib/hooks.py` (Zeile ~225-265)

Der `viz-log` Hook ist der erste **conditional Hook** im Framework:

- **viz.mode == `dynamic` oder `full`:** Hook wird kopiert + in `settings.json` als PreToolUse registriert (auto-enabled)
- **viz.mode == `off` oder `static`:** Hook wird übersprungen, als stale markiert, automatisch gelöscht aus `.claude/hooks/` UND aus `settings.json`

### Stale-Clean-up funktioniert vollautomatisch
Kein manuelles Eingreifen nötig. Beim nächsten `sync.py`-Lauf erkennt das System:
1. Hook war vorher in `.agent-meta-managed` → aber nicht mehr in `now_managed`
2. → DELETE Hook-Datei
3. → `_update_settings_hooks()` entfernt den Eintrag aus `settings.json`

### Verifikation
- `--viz-mode static` Dry-Run: Hook verschwindet wie erwartet ✅
- Live-Sync mit `mode: full`: Hook existiert + registriert ✅

---

## 4. Dokumentation-Updates

### `howto/agent-visualization.md`
- Neuer Abschnitt: "Wie es funktioniert" mit zweistufigem Ansatz (Prompt + Hook)
- Provider-Unterstützungstabelle
- Conditional Hook-Management Tabelle
- Architektur-Diagramm der Event-Logging Pipeline
- Alte Formulierungen ("freiwillig") durch korrekte ("Pflicht-Prompt-Block") ersetzt

### `docs/architecture/01-layer-model.md`
- Hooks-Sektion erweitert um conditional viz-log Logik
- Implementierungs-Referenz (hooks.py Zeilen)

### `README.md`
- Version korrigiert: `0.36.0` → `0.37.0-beta.1`

---

## 5. Offene Punkte

### Continue und Opencode
Beide Provider haben keine native Hook-Infrastruktur. Dort ist der Pflicht-Prompt-Block die einzige Option. Verbesserungsideen:
- Provider-spezifische Hook-Adapter (wenn Provider später Hooks unterstützen)
- Externe File-Watcher als Workaround (beobachtet events.jsonl auf Änderungen)

### Viz-Block in Agent-Templates
Der Viz-Prompt-Block wurde geändert (optional → Pflicht), aber kein Major/Minor Version-Bump durchgeführt. Begründung: Keine inhaltliche Änderung der Agenten-Logik, nur Präzisierung der Formulierung. Bei nächstem Template-Review sollte dies evaluiert werden.

---

## 6. Branch

`feat/agent-visualization-dashboard`
