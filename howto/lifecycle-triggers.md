# Lifecycle Triggers — Agenten-Tasks bei Git-Events

Lifecycle Triggers lösen Agenten-Tasks automatisch aus wenn definierte Git-Events eintreten:
Release-Tag gesetzt, Version hochgezählt, Branch gemergt.

**Kernprinzip:** Bestimmte Aufgaben (CODEBASE_OVERVIEW, Traceability-Audit, ARCHITECTURE-Update)
sind nicht bei jedem Commit sinnvoll — sondern nur zu Schlüsselmomenten im Entwicklungsprozess.

---

## Wie es funktioniert

```
Entwickler macht git push --tags v1.2.0
        ↓
lifecycle-check.sh Hook (PostToolUse) erkennt Tag-Push
        ↓
lifecycle_check.py liest lifecycle-triggers aus .meta-config/project.yaml
        ↓
.claude/pending-tasks.md wird geschrieben (gitignored)
        ↓
Beim nächsten Konversationsstart: lifecycle-tasks Rule erinnert Claude
        ↓
Claude fragt User → delegiert Tasks an die konfigurierten Agenten
```

---

## Konfiguration

In `.meta-config/project.yaml`:

```yaml
lifecycle-triggers:
  on-release:
    - agent: documenter
      task: "Update CODEBASE_OVERVIEW.md and ARCHITECTURE.md for this release."
    - agent: validator
      task: "Run full DoD audit and traceability check."

  on-version-bump-minor:
    - agent: documenter
      task: "Update CODEBASE_OVERVIEW.md — new features may have changed the structure."

  on-version-bump-major:
    - agent: documenter
      task: "Full architecture review and ARCHITECTURE.md update."
    - agent: requirements
      task: "Review and close completed REQ-IDs."

  on-merge:
    - agent: validator
      task: "Quick DoD check for merged changes."
```

### Unterstützte Events

| Event | Wann ausgelöst | Typische Tasks |
|-------|---------------|----------------|
| `on-commit` | Jeder erfolgreiche `git commit` | Leichtgewichtige Checks (sparsam nutzen) |
| `on-merge` | `git merge` oder `gh pr merge` | DoD-Check, Quick-Audit |
| `on-version-bump-patch` | Commit mit Patch-Bump-Nachricht | Changelog-Prüfung |
| `on-version-bump-minor` | Commit mit Minor-Bump-Nachricht | Doku-Update |
| `on-version-bump-major` | Commit mit Major-Bump-Nachricht | Full Audit, ARCHITECTURE |
| `on-release` | `git push` mit Tag-Referenz | Vollständige Release-Checkliste |

**Erkennung von Version-Bumps:** Der Hook erkennt Commits deren Nachricht
`bump version`, `version bump` oder `chore: bump` enthält (case-insensitive).

---

## Aktivierung

### Schritt 1: Hook aktivieren

In `.meta-config/project.yaml`:

```yaml
hooks:
  lifecycle-check:
    enabled: true
```

### Schritt 2: Sync ausführen

```bash
py .agent-meta/scripts/sync.py
```

Der Hook wird nach `.claude/hooks/lifecycle-check.sh` kopiert und in `.claude/settings.json`
als `PostToolUse` Hook registriert.

### Schritt 3: Triggers konfigurieren

`lifecycle-triggers` Block in `.meta-config/project.yaml` eintragen (s. oben).
Kein weiterer Sync nötig — `lifecycle_check.py` liest die Config zur Laufzeit.

---

## Pending Tasks Datei

Wenn ein Trigger auslöst, schreibt `lifecycle_check.py` eine Datei:

```
.claude/pending-tasks.md
```

Format:

```markdown
# Ausstehende Lifecycle-Tasks

## Release / Git-Tag — 2026-04-18 14:32

- [ ] **[documenter]** Update CODEBASE_OVERVIEW.md and ARCHITECTURE.md for this release.
- [ ] **[validator]** Run full DoD audit and traceability check.
```

**Eigenschaften:**
- Gitignored (`.claude/pending-tasks.md` wird vom Sync zur `.gitignore` hinzugefügt)
- Akkumuliert Tasks — neue Einträge werden angehängt, nicht überschrieben
- Bereits erledigte Tasks (`- [x]`) werden nicht erneut hinzugefügt
- Nach Erledigung aller Tasks: Datei manuell oder per Agent löschen

---

## Abgrenzung zu bestehenden Hooks

| | Hooks (bestehend) | Lifecycle Triggers (neu) |
|--|------------------|--------------------------|
| Trigger | Tool-Aufrufe (`PreToolUse`) | Git-Events (`PostToolUse`) |
| Aktion | Shell-Script — blockiert oder erlaubt | Agenten-Tasks anstoßen |
| Token-Kosten | Niedrig (Shell) | Mittel-Hoch (Agent) |
| Konfiguration | `hooks: name: enabled: true` | `lifecycle-triggers: event: [...]` |
| Beispiel | `dod-push-check` blockiert Push ohne Tests | `on-release` startet CODEBASE_OVERVIEW-Update |

---

## Empfohlene Konfigurationen

### Minimal (nur Release-Checkliste)

```yaml
hooks:
  lifecycle-check:
    enabled: true

lifecycle-triggers:
  on-release:
    - agent: documenter
      task: "Update CODEBASE_OVERVIEW.md and ARCHITECTURE.md for this release."
    - agent: validator
      task: "Run full DoD audit and traceability check before release."
```

### Standard (Release + Merge-Check)

```yaml
lifecycle-triggers:
  on-release:
    - agent: documenter
      task: "Update CODEBASE_OVERVIEW.md and ARCHITECTURE.md for this release."
    - agent: validator
      task: "Run full DoD audit and traceability check."
  on-merge:
    - agent: validator
      task: "Quick DoD check: were all DoD criteria met for the merged changes?"
  on-version-bump-major:
    - agent: documenter
      task: "Full architecture review — update ARCHITECTURE.md and CODEBASE_OVERVIEW.md."
    - agent: requirements
      task: "Review open REQ-IDs — close completed requirements."
```

### Token-Sparend (nur bei Major-Events)

```yaml
lifecycle-triggers:
  on-version-bump-major:
    - agent: documenter
      task: "Full architecture review and ARCHITECTURE.md update."
  on-release:
    - agent: documenter
      task: "Update CODEBASE_OVERVIEW.md for this release."
```

---

## Troubleshooting

### Hook löst nicht aus

1. Prüfe ob der Hook in `settings.json` registriert ist:
   ```bash
   cat .claude/settings.json | grep lifecycle
   ```
2. Prüfe ob `lifecycle-check` in `.meta-config/project.yaml` auf `enabled: true` steht
3. Führe `sync.py` erneut aus

### Keine Tasks in `pending-tasks.md`

- Prüfe ob das Git-Kommando dem erkannten Muster entspricht
  - Tag-Push: `git push origin v1.2.3` oder `git push --tags`
  - Merge: `git merge` oder `gh pr merge`
  - Version-Bump: Commit-Nachricht muss `bump version` o.ä. enthalten
- Prüfe ob `lifecycle-triggers` in `.meta-config/project.yaml` befüllt ist
- Manuell testen:
  ```bash
  python3 .agent-meta/scripts/lifecycle_check.py on-release
  ```

### PyYAML nicht installiert

`lifecycle_check.py` benötigt PyYAML für YAML-Configs:
```bash
pip install pyyaml
# oder
pip3 install pyyaml
```

Bei JSON-Config (`agent-meta.config.json`) wird PyYAML nicht benötigt.
