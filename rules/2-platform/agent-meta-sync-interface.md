# agent-meta — sync.py Interface

`sync.py` ist der einzige Weg Agenten zu generieren. Nie direkt in `{{AGENTS_DIR}}` schreiben.

Vollständige Referenz (Flags, sync.log, Modulstruktur):
→ `.agent-meta/agents/1-generic/_wf-sync-interface.md`

## Branch-Guard-Erweiterung für agent-meta

Zusätzlich zu den generischen Branch-Guard-Regeln gilt hier:

- `sync.py` ausführen → immer Branch (Sync propagiert in alle Projekte)

**Faustregel: sync.py ausführen oder >1 Datei anfassen → Branch.**

**NIE direkt auf main:** sync.py-Läufe, Template-Änderungen, Rule-Änderungen — egal wie klein.

## Warum

Direkte Commits auf main propagieren Fehler sofort in alle Projekte beim nächsten Sync.

---

## Neue Funktionen: Smart Context Regeneration

### --check Flag (CI-Mode)

```bash
python .agent-meta/scripts/sync.py --check
python .agent-meta/scripts/sync.py --dry-run --check
```

**Verhalten:**
- Exit Code `0` wenn provider context files (CLAUDE.md, AGENTS.md, GEMINI.md, etc.) aktuell sind
- Exit Code `1` wenn Dateien regeneriert werden müssten
- Keine Dateien geschrieben (pure Status-Abfrage)

**Einsatz in CI:** Blockiert PRs wenn `.meta-config/project.yaml` verändert wurde und context files noch nicht neu generiert wurden.

**Vorteil:** Verhindert Drift zwischen Konfiguration und generiertem Projektkontext — besonders wichtig bei Multi-Provider-Setups.

### context-hashes.json (Drift-Erkennung)

Neuer Sidecar-Datei: `.meta-config/context-hashes.json`

```json
{
  "version": 1,
  "hashes": {
    "claude": "sha256:abc123...",
    "gemini": "sha256:def456...",
    "continue": "sha256:ghi789..."
  }
}
```

**Zweck:** Speichert Hashes der generierten statischen Header, um zu erkennen ob der User die Datei manuell bearbeitet hat (Drift).

**Verhalten:**
- Wird bei jedem Sync aktualisiert
- Bei Drift → Backup erstellt (`.CLAUDE.md.sync-backup-<timestamp>`) mit Warnung
- User kann Backup reviewen und Änderungen manuell merge

**WICHTIG: Mit Git committen** — ermöglicht Drift-Erkennung über Rechner und CI hinweg.

**Nicht gitignoren.**

### sync-on-config-change Hook (Automatische Re-Sync)

Neuer Hook in `hooks/1-generic/sync-on-config-change.sh`

**Trigger:** PostToolUse — reagiert auf Write/Edit-Operationen die `.meta-config/project.yaml` verändern

**Aktion:** 
- Erkennt wenn Projekt-Config geändert wurde (z.B. neue Provider hinzugefügt, Rolle aktiviert)
- Schreibt Lifecycle-Task für `agent-meta-manager` in `.claude/pending-tasks.md`
- `agent-meta-manager` merkt beim nächsten Start dass sync.py erneut laufen muss

**Konfiguration in project.yaml:**

```yaml
lifecycle-triggers:
  on-config-change:
    - agent: agent-meta-manager
      task: "Re-run sync.py — project.yaml has changed."

hooks:
  sync-on-config-change:
    enabled: true
```

**Vorteil:** Keine manuellen Sync-Aufrufe nötig wenn Konfiguration sich ändert — vollautomatische Reconciliation.

---

## Zusammenfassung: Provider Context Lifecycle

```
Developer ändert .meta-config/project.yaml
        ↓
sync-on-config-change Hook erkennt änderung
        ↓
lifecycle_check.py schreibt pending-task für agent-meta-manager
        ↓
agent-meta-manager führt sync.py aus
        ↓
sync.py vergleicht context-hashes.json mit aktuellen Hashes
        ↓
Drift erkannt? → Backup + Regeneration
Kein Drift? → Stille Aktualisierung der managed blocks
        ↓
.meta-config/context-hashes.json aktualisiert
```
