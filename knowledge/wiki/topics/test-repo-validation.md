---
type: "Guide"
title: "Test-Repository Validation"
description: "Validiert die generierten Agenten-Dateien nach einer Implementierung in einem separaten Test-Repository."
tags: [guide]
timestamp: "2026-07-27"
resource: "../../sources/docs/guides/test-repo-validation.md"
migrated_from: "docs/guides/test-repo-validation.md"
---
# Test-Repository Validation

Validiert die generierten Agenten-Dateien nach einer Implementierung in einem separaten Test-Repository.

## Konfiguration

### project.yaml

```yaml
test-repo:
  enabled: true
  path: "../agent-meta-test"          # relativ zum Workspace
  env-var: "AGENT_META_TEST_REPO"     # optional: Umgebungsvariable fur Override
```

### Pfad-Auflösung (Prioritätsreihenfolge)

1. **Umgebungsvariable** `AGENT_META_TEST_REPO` (höchste Priorität)
2. **Relativer Pfad** aus `test-repo.path` (relativ zum Workspace-Root)
3. **Absoluter Pfad** aus `test-repo.path` (falls gesetzt)

## Usage

### Dry-Run (existierend)

```bash
python scripts/sync.py --dry-run
```

Zeigt was geändert würde, ohne Dateien zu schreiben.

### Validation (neu)

```bash
python scripts/sync.py --validate
```

Führt einen vollständigen Sync in das Test-Repository durch und prüft `sync.log` auf Errors.

### Combined

```bash
python scripts/sync.py --dry-run --validate
```

Validierung im Dry-Run-Modus — kein Schreibzugriff auf das Test-Repo.

## Workflow

1. **Entwicklung** → Änderungen an Templates in `agents/1-generic/` oder `2-platform/`
2. **Dry-Run** → `python scripts/sync.py --dry-run` (schnelle Prüfung)
3. **Validate** → `python scripts/sync.py --validate` (vollständige Validierung im Test-Repo)
4. **Commit** → Wenn Validation erfolgreich

## Fehlerbehandlung

| Szenario | Verhalten |
|----------|-----------|
| `test-repo` nicht konfiguriert | Error mit Hinweis auf Konfiguration |
| Pfad existiert nicht | Error mit Hinweis auf `AGENT_META_TEST_REPO` oder `test-repo.path` |
| `sync.log` enthält Errors | Validation failed, Errors werden gelistet |
| Validation erfolgreich | Exit-Code 0, keine Errors im Log |

## CI/CD Integration

```yaml
# Beispiel GitHub Actions
- name: Validate sync
  run: python scripts/sync.py --validate
  env:
    AGENT_META_TEST_REPO: ${{ github.workspace }}/test-repo
```