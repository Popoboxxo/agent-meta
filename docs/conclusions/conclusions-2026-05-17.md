# Erkenntnisse — 17. Mai 2026

## Session-Zusammenfassung

Super-Fix-Session: 7 GitHub Issues aus dem agent-meta Core umgesetzt. Fokus auf AGENTS.md Regel-Updates, sync.py Clean/Update-Modi, Meta-Repo-Docs-Scaffolding und CI-Polling für den git-Agenten.

---

## 1. AGENTS.md Regel-Updates (#152, #153, #157, #158)

### Orchestrator-Scope erweitert (#152)
- Einstiegspunkt-Text von "für alle Entwicklungsaufgaben" auf "für ALLE Aufgaben" geändert
- Neue Tabelle "Hauptchat — nur triviale Direktantworten" mit klaren Kriterien
- Merkregel: "Jede Aufgabe die Code ändert, analysiert, plant oder bewertet → orchestrator"

### Agent-Erstellungs-Grenzen (#153)
- Multi-Repo Workspace Conventions Rule #1 um MUST-Klausel ergänzt
- Agenten MÜSSEN beim Arbeiten in Sibling-Repos KEINE `.claude/` o.ä. Verzeichnisse anlegen

### Delegationssprache verschärft (#157)
- Ideation-Routing: "MUSS an ideation delegiert werden — NIE inline beantworten"
- Neue Section "Anforderungsdokumente → requirements" mit MUST/NIE-Sprache
- Grenze-Klausel: Nur bei laufendem Task mit ≤2 Sätzen und ohne externes Research

### Submodule Boundary Rule (#158)
- Neue Regel: Agenten dürfen NIE Dateien in Git-Submodules ändern
- Eskalationspfad: meta-feedback Issue oder Datei außerhalb kopieren

---

## 2. sync.py: Clean- und Update-Modi (#161)

### Neue Flags
- `--update`: Expliziter Alias für Default-Sync, loggt Mode als "update"
- `--clean`: Löscht alle generierten Dateien, dann voller Sync
- `--force`: Überspringt Bestätigung bei `--clean`

### Implementierung: `clean_generated_files()` in `scripts/lib/io.py`
- ~140 Zeilen neue Funktion
- Provider-agnostische Verzeichnis-Scan-Logik
- Drei Phasen: (1) Provider-Verzeichnisse scannen, (2) Top-level Dateien, (3) Löschen
- `_resolve_dir()` Hilfsfunktion für implizite Verzeichnis-Auflösung
- Unterstützt `--dry-run` und `--force`

### Geschützte Pfade
Settings-Dateien, Local-Settings, Extensions, `.meta-config/`, CLAUDE.md/AGENTS.md, MCP-Secrets, Pending-Tasks

---

## 3. Meta-Repo-Docs-Scaffolding (#149)

### `scaffold_meta_repo_docs()` in `scripts/lib/setup.py`
- Erstellt `docs/PATTERNS.md`, `docs/LEARNINGS.md`, `docs/CONVENTIONS.md`
- Trigger: `meta-repo: true` in `project.yaml`
- Nutzt Starter-Templates aus `.agent-meta/templates/docs/` falls vorhanden
- Integration in `--init` und `--clean --init` Pfade

---

## 4. CI/CD Status Polling (#160)

### git-Agent Erweiterung
- Version 2.2.1 → 2.3.0
- Neue Section "CI/CD Status Polling (after push)"
- Opt-in: `CI_POLL_ENABLED: true` (default: false)
- Konfigurierbar: `CI_POLL_INTERVAL` (30s), `CI_POLL_MAX_RETRIES` (10)
- Verwendet `gh run list` für GitHub Actions

### Code-Änderungen
- `scripts/lib/config.py`: `build_variables()` um CI_POLL_* erweitert
- `scripts/lib/config.py`: `strip_inactive_dod_blocks()` unterstützt jetzt `{{^VAR}}` inverse Blöcke
- `scripts/lib/agents.py`: `extra_vars=["CI_POLL_ENABLED"]` an beide Sync-Pfade
- `config/project-config.schema.json`: 3 neue Variablen registriert
- `howto/configs/project.yaml.example`: CI-Polling-Konfiguration dokumentiert
- `agents/1-generic/_wf-git-ops.md`: CI-Polling Cross-Reference in Workflow W1

---

## 5. Neue Entwicklungs-Konvention: Provider-Pflicht

### Invariante #4 in AGENTS.md
Jede Änderung MUSS für ALLE aktiven Provider (Claude, Continue, Gemini, Opencode) funktionieren.

**Prüfung vor Commit:**
```bash
python scripts/sync.py --dry-run
```

### Bugfix: Provider-Coverage in --clean
`clean_generated_files()` erweitert um `_resolve_dir()` die implizit aufgelöste Provider-Verzeichnisse erkennt (Claude hat keine expliziten `rules_dir`/`hooks_dir`/`commands_dir` Keys — diese werden aus `has_*` Flags + Provider-Namen abgeleitet).

---

## Offene Punkte

- **#154** (4 neue Agenten-Templates): Zu groß für diese Session, folgt separat
- **#155, #156, #159**: Sharkord/Docker-spezifisch, nicht agent-meta Core
