---
type: "Guide"
title: "CI: Provider Context Sync Check"
description: "Verhindert dass veraltete provider context files (CLAUDE.md, AGENTS.md, etc.) in main committed werden."
tags: [guide]
timestamp: "2026-07-27"
resource: "../../sources/docs/guides/ci/sync-check.md"
migrated_from: "docs/guides/ci/sync-check.md"
---
# CI: Provider Context Sync Check

**Verhindert dass veraltete provider context files (CLAUDE.md, AGENTS.md, etc.) in `main` committed werden.**

---

## Problem

Wenn Developer die `.meta-config/project.yaml` ändert (neue Provider, Rolle aktiviert), müssen die generierten context files neu generiert werden:

```
Developer ändert .meta-config/project.yaml
        ↓
Vergisst sync.py lokal zu laufen
        ↓
context files sind veraltet
        ↓
PR merged → alle Projekte die agent-meta pullen haben jetzt veralteten Kontext
```

---

## Lösung: --check Flag in CI

Nutze `sync.py --check` um CI fehlschlagen zu lassen wenn context files veraltet sind.

### GitHub Actions Template

Copy into `.github/workflows/sync-check.yml`:

```yaml
name: agent-meta sync check

on: [push, pull_request]

jobs:
  sync-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          submodules: recursive

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.8"

      - name: Check provider context files are up to date
        run: python .agent-meta/scripts/sync.py --dry-run --check
        # Fails if CLAUDE.md, AGENTS.md, GEMINI.md, etc. would be regenerated
        # Fix: Run `python .agent-meta/scripts/sync.py` locally and push
```

**Tipp:** Der Job läuft für jeden `push` und `pull_request`. PRs mit veralteten context files schlagen fehl und zeigen:

```
Exit code 1: provider context files out of sync
Run: python .agent-meta/scripts/sync.py
```

---

## Workflow: Was tun wenn CI fehlschlägt?

**Der Developer:**

1. Lokal ausführen:
   ```bash
   python .agent-meta/scripts/sync.py
   ```

2. Alle Änderungen stagieren und committen:
   ```bash
   git add .claude/ .gemini/ .continue/ .meta-config/project.yaml CLAUDE.md
   git commit -m "chore: regenerate provider context files"
   ```

3. Pushen → CI sollte jetzt grün sein

---

## Technische Details: --check vs. --dry-run

| Flag | Effekt | Exit Code |
|------|--------|-----------|
| `--dry-run` | Zeigt was gemacht würde, schreibt nicht | 0 (immer erfolgreich) |
| `--dry-run --check` | Zeigt was gemacht würde + prüft auf Drift | 0 wenn keine Änderungen, 1 wenn Drift |
| `--check` (ohne --dry-run) | Nur Status-Abfrage, keine Vorschau | 0 wenn aktuell, 1 wenn Drift |

**Empfehlung für CI:** `--dry-run --check` — gibt Developers maximale Info bei Fehlschlag.

---

## Sidecar-Datei: context-hashes.json

Damit der Check funktioniert, muss `.meta-config/context-hashes.json` **mit Git committed** sein.

Diese Datei speichert die Hashes der zuletzt generierten statischen Header pro Provider:

```json
{
  "version": 1,
  "hashes": {
    "claude": "sha256:abc...",
    "gemini": "sha256:def..."
  }
}
```

**Wichtig:**
- Nicht gitignoren
- Wird bei jedem `sync.py`-Lauf aktualisiert
- Ermöglicht Drift-Erkennung über Rechner und CI hinweg

---

## Multi-Provider Setup

Wenn Projekt mehrere Provider nutzt (Claude + Gemini + Continue), prüft `--check` alle:

```bash
$ python .agent-meta/scripts/sync.py --dry-run --check
Exit 1: CLAUDE.md out of sync
Exit 1: GEMINI.md out of sync
```

Ein einziger `sync.py`-Lauf lokale behebt alle:

```bash
python .agent-meta/scripts/sync.py
# Regeneriert alle context files gleichzeitig
```

---

## Troubleshooting

### "No such file or directory: context-hashes.json"

Datei existiert noch nicht. Führe `sync.py` lokal aus:

```bash
python .agent-meta/scripts/sync.py
git add .meta-config/context-hashes.json
git commit -m "chore: add context-hashes.json"
```

### CI passed but files still look wrong

Möglich dass Developer lokale Änderungen an context files hatte die nicht gemerkt wurden. Prüfe `.sync-backup-*` Dateien:

```bash
ls -la .claude/CLAUDE.md.sync-backup-*
```

Wenn Backup existiert: Review it, merge wanted changes manuell, dann neu-sync.

### CI stuck in loop (always fails)

Wenn CI trotz `sync.py`-Lauf weiterhin fehlschlägt:

1. Prüfe ob `.meta-config/context-hashes.json` committed ist
2. Führe lokal aus: `git add .meta-config/context-hashes.json && git commit -m "fix: update hashes"`
3. Push → CI sollte grün sein

---

## Empfehlungen

### Bei agent-meta als Submodul

**Alle Projekte die agent-meta nutzen sollten CI-Check aktiviert haben.** Das verhindert dass Submodul-Updates ohne Re-Sync committed werden.

### Bei Custom Platform Agents

Falls Projekt `2-platform/<plattform>-*.md` Overrides hat, nutzt `--check` auch diese:

```bash
# CI prüft auch 2-platform/ Änderungen
python .agent-meta/scripts/sync.py --dry-run --check
```

### Mit lifecycle-triggers

Wenn `sync-on-config-change` Hook aktiviert ist, wird sync.py automatisch neu gestartet sobald `.meta-config/project.yaml` ändert. In diesem Fall ist CI-Check ein zusätzliches Sicherheitsnetz für manuell verpasste Syncs.

```yaml
# .meta-config/project.yaml
lifecycle-triggers:
  on-config-change:
    - agent: agent-meta-manager
      task: "Re-run sync.py"

hooks:
  sync-on-config-change:
    enabled: true
```