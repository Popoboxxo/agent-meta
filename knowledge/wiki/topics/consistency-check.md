---
type: "Guide"
title: "Howto: Consistency-Check"
description: "Validiert Agent-Templates, Commands und Cross-References im agent-meta-Framework auf Konsistenz — deterministische Prüfungen ohne LLM-Aufruf."
tags: [guide, feature]
timestamp: "2026-07-27"
resource: "../../sources/docs/guides/features/consistency-check.md"
migrated_from: "docs/guides/features/consistency-check.md"
---
# Howto: Consistency-Check

Validiert Agent-Templates, Commands und Cross-References im agent-meta-Framework auf Konsistenz —
deterministische Prüfungen ohne LLM-Aufruf.

---

## Wann ausführen

| Zeitpunkt | Empfehlung |
|---|---|
| Nach dem Anlegen eines neuen Agenten oder Commands | `--changed` (nur neue Dateien) |
| Vor einem Commit auf einem Feature-Branch | `--changed` |
| Nach einem Sync (`sync.py`) | `--changed` |
| Vor einem Release | Vollständiger Check (ohne Flags) |
| In CI/CD auf Pull Requests | `--changed --json` |

---

## Manuelle Ausführung

### Voraussetzung

Python 3.8+ und PyYAML (`pip install pyyaml`).  
PyYAML ist optional — ohne es funktioniert ein Fallback-Parser (Regex), der jedoch
komplexe YAML-Strukturen (z.B. `patches:` in 2-platform-Dateien) nicht vollständig parst.

### Ausführung aus einem Projekt heraus

```bash
# Nur geänderte Dateien prüfen (Standard, schnell):
py .agent-meta/scripts/consistency-check.py --changed

# Alle Agenten + Commands prüfen (vollständiger Audit):
py .agent-meta/scripts/consistency-check.py

# Einzelne Datei prüfen:
py .agent-meta/scripts/consistency-check.py --file agents/1-generic/my-agent.md

# Strict-Modus (Warnings = Fehler, exit 1):
py .agent-meta/scripts/consistency-check.py --changed --strict

# JSON-Output für CI-Pipelines:
py .agent-meta/scripts/consistency-check.py --changed --json
```

### Ausführung direkt im agent-meta Meta-Repo

```bash
# Im Repo-Root:
py scripts/consistency-check.py --changed
py scripts/consistency-check.py
py scripts/consistency-check.py --file agents/1-generic/feedback.md
```

### Über den Slash-Command (Claude Code)

```
/consistency-check              → geänderte Dateien prüfen
/consistency-check --all        → vollständige Prüfung
/consistency-check --strict     → Warnings als Fehler werten
```

### Über den agent-meta-manager

```
Starte agent-meta-manager und sage:
"Führe einen Consistency-Check durch"
→ Agent wählt automatisch --changed und erklärt alle Findings
```

---

## Exit-Codes

| Code | Bedeutung |
|------|-----------|
| `0` | Keine Fehler (Warnings werden toleriert, außer bei `--strict`) |
| `1` | Mindestens ein ERROR gefunden (oder WARNING bei `--strict`) |
| `2` | Script-Fehler (Datei nicht gefunden, ungültige Argumente) |

---

## Alle CLI-Flags

| Flag | Beschreibung |
|---|---|
| *(kein Flag)* | Alle Agents + Commands vollständig prüfen |
| `--changed` | Nur git-geänderte Dateien prüfen (staged + unstaged + untracked in agents/ + commands/) |
| `--file <path>` | Nur diese eine Datei prüfen |
| `--strict` | Warnings ebenfalls als Fehler werten → exit 1 |
| `--json` | Findings als JSON ausgeben (für CI-Pipelines) |
| `--root <dir>` | agent-meta Wurzelverzeichnis explizit setzen (Standard: Elternverzeichnis von scripts/) |

---

## Checks im Detail

### Frontmatter-Checks (`lib/consistency/frontmatter.py`)

| Check-ID | Severity | Was geprüft wird |
|---|---|---|
| `frontmatter.missing` | ERROR | Keine `---` Frontmatter im Agent gefunden |
| `frontmatter.version-missing` | ERROR | Kein `version:` Feld vorhanden |
| `frontmatter.version-format` | WARNING | Version entspricht nicht semver `X.Y.Z` |
| `frontmatter.version-bump` | ERROR | Datei geändert, aber `version:` nicht erhöht (git-diff-basiert) |
| `frontmatter.name-missing` | WARNING | Kein `name:` Feld vorhanden |
| `frontmatter.description-missing` | WARNING | Kein `description:` Feld vorhanden |
| `frontmatter.tools-not-list` | ERROR | `tools:` ist kein YAML-Array |
| `frontmatter.workflow-tier-invalid` | ERROR | `workflow_tier` hat ungültigen Wert |
| `frontmatter.based-on-missing` | WARNING | 2-platform Agent hat kein `based-on:` Feld |
| `frontmatter.extends-not-found` | ERROR | `extends:` Datei existiert nicht |
| `frontmatter.patch-anchor-missing` | WARNING | `patches[n]` hat kein `anchor:` (für ops die es benötigen) |
| `frontmatter.patch-anchor-not-found` | ERROR | Anchor-String nicht in der Basis-Datei gefunden |

**Version-Bump-Konvention:**

| Änderungstyp | Bump |
|---|---|
| Umbenannte Variable, geändertes Verhalten, neue Pflichtsektion | Major (`X.0.0`) |
| Neue optionale Sektion, erweiterter Scope | Minor (`x.Y.0`) |
| Textverbesserung, Klarstellung, Tippfehler | Patch (`x.y.Z`) |

### Cross-Reference-Checks (`lib/consistency/crossrefs.py`)

| Check-ID | Severity | Was geprüft wird |
|---|---|---|
| `crossrefs.role-not-in-role-defaults` | ERROR | `agents/1-generic/<rolle>.md` hat keinen Eintrag in `config/role-defaults.yaml` |
| `crossrefs.role-defaults-orphan` | WARNING | Eintrag in `role-defaults.yaml` ohne zugehörige `1-generic/<rolle>.md` |
| `crossrefs.orchestrator-table-incomplete` | WARNING | Rolle mit `workflow_tier: required/recommended` fehlt in Orchestrator-Tabelle |
| `crossrefs.changelog-no-unreleased` | WARNING | Neue Datei hinzugefügt, aber kein `[Unreleased]` Abschnitt in CHANGELOG |
| `crossrefs.changelog-missing-entry` | WARNING | Neue Agent/Command-Datei nicht im `[Unreleased]` Abschnitt erwähnt |

### Platzhalter-Checks (`lib/consistency/placeholders.py`)

| Check-ID | Severity | Was geprüft wird |
|---|---|---|
| `placeholders.typo` | ERROR | Bekannter Tippfehler in `{{VAR}}` (z.B. `DOCS_LANGAUGE`) |
| `placeholders.unknown` | WARNING | `{{VAR}}` ist kein bekannter Built-in-Platzhalter |

> **Hinweis:** `placeholders.unknown` ist eine Warnung, kein Fehler — Projekte können
> eigene Variablen in `project.yaml variables:` definieren. Nur echte Typos sind ERRORs.

Alle bekannten Built-in-Variablen: `scripts/lib/consistency/placeholders.py` → `_BUILTIN_VARS`.

### Command-Checks (`lib/consistency/commands.py`)

| Check-ID | Severity | Was geprüft wird |
|---|---|---|
| `commands.frontmatter-missing` | ERROR | Command-Datei hat keine Frontmatter |
| `commands.description-missing` | ERROR | Kein `description:` Feld |
| `commands.allowed-tools-missing` | WARNING | Kein `allowed-tools:` Feld |
| `commands.allowed-tools-not-list` | ERROR | `allowed-tools` ist String statt Array |
| `commands.argument-hint-missing` | INFO | Kein `argument-hint:` Feld |
| `commands.arguments-not-used` | WARNING | `argument-hint` deutet auf Argumente, `$ARGUMENTS` aber nicht im Body |
| `commands.duplicate-in-layer` | WARNING | Zwei Command-Dateien gleichen Namens in derselben Schicht |

---

## JSON-Output-Format (für CI)

```json
{
  "findings": [
    {
      "severity": "ERROR",
      "check": "frontmatter.version-bump",
      "file": "agents/1-generic/orchestrator.md",
      "message": "File changed but version '2.6.0' was not bumped (same as HEAD).",
      "suggestion": "Increment version per conventions: patch=text, minor=new section, major=behaviour change."
    }
  ],
  "summary": {
    "total": 1,
    "errors": 1,
    "warnings": 0
  }
}
```

---

## Integration in CI/CD (GitHub Actions)

```yaml
# .github/workflows/consistency-check.yml
name: agent-meta consistency check

on: [pull_request]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          submodules: true

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install pyyaml

      - name: Consistency check (changed files)
        run: python .agent-meta/scripts/consistency-check.py --changed --strict
```

---

## Neue Checks hinzufügen

1. Prüflogik in das passende Modul schreiben (`scripts/lib/consistency/*.py`)
2. `Finding`-Objekte mit `Severity.ERROR` oder `Severity.WARNING` zurückgeben
3. Check in `scripts/consistency-check.py` → `run_checks()` einbinden
4. Dieses Howto um den neuen Check-ID + Beschreibung ergänzen

Beispiel (Minimal-Check):

```python
# scripts/lib/consistency/crossrefs.py

def check_my_new_rule(agent_meta_root: Path) -> list[Finding]:
    findings = []
    # ... Logik ...
    if problem_found:
        findings.append(Finding(
            Severity.ERROR,
            "crossrefs.my-new-check",          # eindeutige Check-ID
            "path/to/affected/file.md",
            "Konkrete Fehlerbeschreibung.",
            "-> Konkreter Fix-Hinweis.",
        ))
    return findings
```

```python
# scripts/consistency-check.py → run_checks()
from lib.consistency.crossrefs import check_my_new_rule
...
findings += check_my_new_rule(root)
```

---

## Skript-Struktur

```
scripts/
  consistency-check.py              # CLI-Einstiegspunkt
  lib/
    consistency/
      __init__.py                   # Paket-Init, re-exportiert Finding + Severity
      report.py                     # Finding-Datenklasse + Report-Ausgabe (text/JSON)
      frontmatter.py                # Frontmatter-Validierung für Agent-Templates
      crossrefs.py                  # Cross-Reference-Prüfungen (role-defaults, Orchestrator, CHANGELOG)
      placeholders.py               # {{VAR}}-Platzhalter-Scanner
      commands.py                   # Command-spezifische Checks
```