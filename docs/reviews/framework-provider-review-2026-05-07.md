# Framework & Provider Best Practices Review

> **Stand:** v0.34.0 | **Datum:** 2026-05-07 | **Reviewer:** developer-agent
> **Scope:** agent-meta Framework + Claude, Continue, Gemini, Opencode Provider

---

## Executive Summary

Das agent-meta Framework ist **architektonisch gut durchdacht** und folgt klaren Schichten-Prinzipien. Die Multi-Provider-Unterstützung (Claude, Continue, Gemini, Opencode) ist sauber abstrahiert. Es gibt jedoch **signifikante Lücken** in Security, Testing, Error Handling und Code-Konsistenz die behoben werden sollten.

**Gesamtbewertung:** B+ (gutes Fundament, aber produktionsreif erst mit Security-Hardening und Tests)

---

## 1. Architektur & Design Patterns ✅

### Was gut ist
- **Klare Schichten:** 0-external → 1-generic → 2-platform → 3-project
- **Provider-Abstraktion:** `config/ai-providers.yaml` zentralisiert Provider-spezifika
- **Composition-System:** `extends:` + `patches:` für Agenten-Overrides ist elegant
- **Managed Blocks:** Automatisch aktualisierte Blöcke in generierten Dateien
- **Variable Substitution:** `{{VAR}}`-System mit Escape-Support (`{{%VAR%}}`)

### Was verbessert werden sollte
- **Keine Plugin-Architektur:** sync.py ist monolithisch — keine Hooks für benutzerdefinierte Transformationen
- **Feste Verzeichnisstruktur:** `.claude/`, `.gemini/` etc. sind hardcodiert, nicht konfigurierbar
- **Keine Caching-Schicht:** Bei großen Projekten wird sync.py langsam (keine Incremental-Sync)

---

## 2. Code Quality & Maintainability ⚠️

### Positiv
- **Dokstrings:** Alle Module haben ausführliche Docstrings
- **Type Hints:** Große Teile des Codes nutzen Python 3.10+ Type Hints (`str | None`)
- **Konstanten:** Magic Strings sind zentralisiert (`AGENTS_DIR`, `RULES_DIR`, etc.)
- **Legacy-Fallbacks:** Gute Rückwärtskompatibilität (`.json` → `.yaml` Migration)

### Kritisch

#### 2.1 Bare `except Exception:` (7 Vorkommen)
**Risiko:** Silent Failures, schwieriges Debugging

```python
# agents.py:205-208
try:
    import yaml as _yaml
    data = _yaml.safe_load(...)
except Exception:
    pass
```

**Empfohlene Fixes:**
```python
try:
    import yaml as _yaml
    data = _yaml.safe_load(...)
except (yaml.YAMLError, ImportError) as e:
    log.warn(f"YAML parse error in {path}: {e}")
```

**Betroffene Dateien:**
- `agents.py:205` — YAML parsing
- `agents.py:325` — PyYAML composition
- `config.py:218` — Schema loading
- `hooks.py:124` — JSON parsing (bereits spezifisch: `except (json.JSONDecodeError, OSError)`)
- `skills.py:73` — Git subprocess
- `platform.py:69` — YAML loading
- `lifecycle_check.py:138` — YAML loading

#### 2.2 Code Duplikation
**Risiko:** Inkonsistenzen bei Änderungen

| Dupliziertes Muster | Vorkommen | Lösung |
|---------------------|-----------|--------|
| `try: import yaml` | 4 Dateien | Zentral in `io.py` |
| `_load_yaml_or_json` Wrapper | Jedes Config-Modul | Bereits in `io.py`, aber Module duplizieren Fallback-Logik |
| `config/... .yaml` + Legacy-Pfade | 5 Dateien | Helper-Funktion `load_config_file()` |
| Provider-spezifische Memory-Injection | `agents.py:490`, `agents.py:653` | Extrahieren in `inject_agent_fields()` |

#### 2.3 Keine Unit Tests
**Risiko:** Regressionen bei Änderungen, keine CI-Validierung

```
scripts/
  lib/
    tests/           ← FEHLEND
      test_agents.py
      test_rules.py
      test_config.py
      test_hooks.py
```

**Empfohlene Test-Abdeckung:**
- Config loading & validation
- Variable substitution (inkl. Escaping)
- Agent composition (extends + patches)
- Rule precedence (platform overrides generic)
- Memory/permissionMode injection
- DoD preset resolution

---

## 3. Security 🔴

### 3.1 Path Traversal Risiko
**Risiko:** Mittel | **Datei:** `sync.py`, `agents.py`, `rules.py`

```python
# Problem: Keine Validierung dass generierte Pfade innerhalb des Project Roots bleiben
# Wenn config['project']['prefix'] = "../../evil" enthält:
target_path = project_root / ".claude/agents/" / f"{prefix}-{role}.md"
# → Könnte außerhalb des Project Roots schreiben
```

**Fix:**
```python
def safe_path(base: Path, *parts: str) -> Path:
    path = base.joinpath(*parts).resolve()
    if not str(path).startswith(str(base.resolve())):
        raise ValueError(f"Path traversal detected: {path}")
    return path
```

### 3.2 Shell Injection in Hooks
**Risiko:** Hoch | **Datei:** `hooks.py`

Hooks werden als Shell-Scripts ausgeführt. Wenn ein Hook dynamisch generierte Commands enthält:
```bash
# Dod-Push-Check Hook (Beispiel)
TOOL_NAME=$(echo "$INPUT" | python3 -c "...")
# Keine Quoting-Validierung des JSON-Inputs
```

**Empfohlung:** Hooks sollten JSON über stdin parsen, nicht Shell-Substitution nutzen.

### 3.3 Keine Secrets Detection
**Risiko:** Mittel

- `sync.py` kopiert Dateien ohne Secrets-Scanning
- `project.yaml` könnte API-Keys enthalten (insbesondere `model-overrides` mit vollständigen Modell-IDs)
- Kein `.claude/settings.json` Validation auf hardcodierte Tokens

**Empfohlung:**
```python
# In sync.py vor dem Write:
if _contains_secrets(content):
    log.warn(f"Potential secret detected in {path} — review before committing")
```

### 3.4 Keine Datei-Berechtigungsprüfung
**Risiko:** Niedrig

- Generierte `.sh` Hook-Scripts haben keine execute-Bits gesetzt
- `sync.py` schreibt mit Default-Permissions (u=rw, g=r, o=r)
- `.claude/agent-memory/` Dateien sind für alle lesbar

---

## 4. Error Handling & Robustheit ⚠️

### 4.1 Graceful Degradation
**Positiv:**
- PyYAML fehlt → klare Fehlermeldung + `sys.exit(1)`
- jsonschema fehlt → Warnung, kein Hard-Fail
- Config-Datei fehlt → Fallback zu Legacy-Pfaden

### 4.2 Race Conditions
**Risiko:** Niedrig | **Datei:** `sync.py`

```python
# Problem: Kein File Locking bei parallelen sync.py-Läufen
if target_path.exists():
    target_path.unlink()  # Race condition hier
```

### 4.3 Unvollständige Rollbacks
**Risiko:** Mittel

Wenn sync.py in der Mitte fehlschlägt:
- Bereits geschriebene Dateien bleiben zurück
- Keine atomische Transaktion
- `.agent-meta-managed` Index kann inkonsistent werden

**Empfohlung:** Dry-Run als Default, oder `--atomic` Flag mit Temp-Verzeichnis + Rename.

---

## 5. Provider-Implementierungen 📊

### 5.1 Claude ✅ (Referenz-Implementierung)

| Feature | Status | Bemerkung |
|---------|--------|-----------|
| Agents | ✅ | Vollständig mit Frontmatter |
| Rules | ✅ | `alwaysApply` Unterstützung |
| Hooks | ✅ | Settings.json Integration |
| Commands | ✅ | `.md` Format |
| Settings | ✅ | JSON mit Hook-Registrierung |
| Memory | ✅ | `.claude/agent-memory/` |
| Context | ✅ | `CLAUDE.md` |

**Stärken:**
- Vollständigste Implementierung
- `alwaysApply` Frontmatter für Rules
- Hook-Event-System (PreToolUse, etc.)

**Schwächen:**
- Hardcodiert als "default" Provider in `resolve_providers()`
- `settings.json` Merge-Logik ist komplex und fehleranfällig

### 5.2 Continue ⚠️

| Feature | Status | Bemerkung |
|---------|--------|-----------|
| Agents | ✅ | `.md` Files |
| Prompts | ✅ | Separate Prompt-Generierung |
| Rules | ⚠️ | Kein `alwaysApply` (nicht unterstützt) |
| Hooks | ❌ | Nicht unterstützt |
| Commands | ✅ | `.md` Files |
| Settings | ✅ | `config.yaml` |
| Context | ✅ | `project-context.md` |

**Probleme:**
- `config.yaml` wird "already exists — not overwritten" übersprungen → Updates funktionieren nicht
- Keine Hook-Unterstützung → `dod-push-check` etc. funktionieren nicht
- `alwaysApply` wird ignoriert (Continue hat kein Äquivalent)

### 5.3 Gemini ⚠️

| Feature | Status | Bemerkung |
|---------|--------|-----------|
| Agents | ✅ | `.md` Files, Frontmatter ohne `memory`/`permissionMode` |
| Rules | ⚠️ | Kein `alwaysApply`, manche Rules skipped |
| Hooks | ❌ | Nur Claude-spezifisch |
| Commands | ✅ | `.toml` Format |
| Settings | ✅ | `settings.json` |
| Context | ✅ | `GEMINI.md` |

**Probleme:**
- `rules-preset: gemini: skip` für 5 Rules → Gemini-Agenten bekommen weniger Kontext
- Keine Hook-Unterstützung
- `memory` und `permissionMode` werden aus Frontmatter entfernt

### 5.4 Opencode ⚠️

| Feature | Status | Bemerkung |
|---------|--------|-----------|
| Agents | ✅ | `.md` Files, `model: provider/model-id` Format |
| Rules | ❌ | In `AGENTS.md` eingebettet |
| Hooks | ❌ | Nicht unterstützt |
| Commands | ✅ | `.md` Files |
| Settings | ✅ | `opencode.json` |
| Context | ✅ | `AGENTS.md` |

**Probleme:**
- Rules sind in `AGENTS.md` eingebettet, nicht als separate Dateien
- Keine native Rules/Dir → schwieriger zu debuggen
- Keine Hook-Unterstützung

### 5.5 Provider-Konsistenz-Gaps

```
Feature              | Claude | Continue | Gemini | Opencode
---------------------|--------|----------|--------|----------
Hooks                | ✅     | ❌       | ❌     | ❌
alwaysApply Rules    | ✅     | ❌       | ❌     | ❌
Memory Scope         | ✅     | N/A      | N/A    | N/A
Settings Auto-Update | ✅     | ⚠️       | ✅     | ✅
Commands Format      | .md    | .md      | .toml  | .md
Agent Frontmatter    | voll   | voll     | reduz. | voll
```

**Empfohlung:** Feature-Matrix in `docs/providers/multi-provider.md` dokumentieren und Lücken als Issues tracken.

---

## 6. Performance ⚠️

### 6.1 Kein Incremental Sync
**Risiko:** Hoch bei großen Projekten

```python
# sync.py liest und schreibt ALLE Dateien bei jedem Lauf
# Bei 50 Agenten × 4 Provider = 200 Datei-Operationen
# Keine Prüfung ob sich Quelldatei geändert hat
```

**Fix-Idee:**
```python
def _needs_update(source: Path, target: Path) -> bool:
    if not target.exists():
        return True
    return source.stat().st_mtime > target.stat().st_mtime
```

### 6.2 Keine Parallelisierung
**Risiko:** Mittel

Provider werden sequentiell verarbeitet:
```python
for provider in providers:
    sync_agents(...)      # 1. Provider
    sync_rules(...)       # 1. Provider
    sync_hooks(...)       # 1. Provider
# Dann 2. Provider, etc.
```

**Empfohlung:** `asyncio` oder `concurrent.futures` für parallele Provider-Generierung.

### 6.3 Memory-Leaks
**Risiko:** Niedrig

- `sync.log` wird bei jedem Lauf komplett neu geschrieben (kein Rotation)
- `substitute()` erzeugt bei jedem Lauf neue String-Objekte (unvermeidbar, aber akzeptabel)

---

## 7. Konfiguration & Validierung ⚠️

### 7.1 JSON Schema Validation
**Positiv:**
- `project-config.schema.json` existiert
- `jsonschema` wird optional genutzt
- Fehler werden als Warnungen ausgegeben (nicht hard-fail)

### 7.2 Config Gaps
**Fehlende Validierungen:**
- `model-overrides` Werte werden nicht gegen `ai-providers.yaml` geprüft
- `memory-overrides` Werte werden nicht gegen gültige Scopes geprüft
- `roles` Liste wird nicht gegen `role-defaults.yaml` validiert
- `platforms` werden nicht gegen existierende Platform-Dirs geprüft

### 7.3 Typos in Config
**Risiko:** Mittel

```yaml
# Keine Warnung bei Tippfehlern:
 speach-mode: submissive   # ← Tippfehler, wird ignoriert
 speech-mode: submissive   # ← Korrekt
```

**Empfohlung:** `jsonschema` `additionalProperties: false` für striktere Validierung.

---

## 8. Dokumentation ✅

### Positiv
- `CLAUDE.md` ist umfassend
- `howto/` enthält detaillierte Guides
- `CHANGELOG.md` ist gepflegt
- Jeder Agent hat `description` + `hint`

### Lücken
- Keine API-Dokumentation für `scripts/lib/` Module
- Keine CONTRIBUTING.md für neue Entwickler
- `docs/providers/multi-provider.md` fehlt Feature-Matrix
- Keine Troubleshooting-Sektion für häufige sync.py-Fehler

---

## 9. Git & Workflow ✅

### Positiv
- Branch-Guard Rule erzwingt Feature-Branches
- Commit-Conventions sind dokumentiert
- `.gitignore` wird automatisch verwaltet
- `sync.log` wird generiert (aber nicht committed)

### Schwächen
- Keine Pre-Commit Hooks im Repo selbst (nur im generierten `.claude/`)
- `sync.log` sollte `.gitignore` sein (ist es bereits)
- Kein CI/CD für das agent-meta Repo selbst

---

## 10. Empfohlene Prioritäten

### P0 — Kritisch (sofort)
1. **Path Traversal Fix** in `sync.py` — Security-Risiko
2. **Bare `except Exception:`** durch spezifische Exceptions ersetzen
3. **Unit Tests** für `config.py`, `agents.py`, `rules.py` erstellen

### P1 — Hoch (nächster Sprint)
4. **Provider Feature-Matrix** dokumentieren und Lücken tracken
5. **Config Validation** erweitern (model/memory/roles gegen Defaults prüfen)
6. **Incremental Sync** implementieren (mtime-Check)

### P2 — Mittel (nachster Release)
7. **Secrets Detection** in generierten Dateien
8. **Hook-Security** (JSON statt Shell-Parsing)
9. **API-Dokumentation** für `scripts/lib/` Module
10. **CI/CD** für agent-meta Repo (GitHub Actions)

### P3 — Niedrig (Backlog)
11. **Plugin-System** für benutzerdefinierte Transformationen
12. **Parallelisierung** der Provider-Generierung
13. **Caching-Schicht** für große Projekte
14. **Atomic Sync** mit Rollback-Support

---

## Anhang: Datei-Status-Übersicht

| Datei | Zeilen | Bewertung | Haupt-Probleme |
|-------|--------|-----------|----------------|
| `scripts/sync.py` | 410 | B+ | Keine Tests, monolithisch |
| `scripts/lib/agents.py` | 933 | B+ | Duplikation, bare excepts |
| `scripts/lib/rules.py` | 301 | A- | Gut strukturiert |
| `scripts/lib/hooks.py` | 320 | B | Shell-Injection-Risiko |
| `scripts/lib/config.py` | 316 | B+ | Keine Input-Sanitization |
| `scripts/lib/providers.py` | 78 | A | Klar und fokussiert |
| `scripts/lib/skills.py` | 339 | B+ | Subprocess ohne Timeout-Check |
| `scripts/lib/extensions.py` | 141 | A- | Gut abstrahiert |
| `scripts/lib/log.py` | 78 | A | Einfach und effektiv |
| `scripts/lib/roles.py` | 147 | A- | Klare Precedence-Logik |
| `scripts/lib/context.py` | ~800 | B | Sehr groß, sollte aufgeteilt werden |
| `scripts/lib/dod.py` | 66 | A | Fokussiert |
| `scripts/lib/platform.py` | 125 | A- | Gute Error-Handling |
| `scripts/lib/setup.py` | 267 | B | Keine Tests, Interaktiv |
| `scripts/lib/io.py` | 41 | A | Minimal und sauber |

---

*Dieses Review wurde mit dem `developer`-Agenten durchgeführt. Empfohlene Nachverfolgung: Issues für P0+P1 erstellen und im nächsten Sprint priorisieren.*
