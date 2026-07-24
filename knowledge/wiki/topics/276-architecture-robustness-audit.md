---
type: "Guide"
title: "Audit: Architecture Robustness (Issue #276)"
description: "Branch: feat/framework-issues-batch-2 Datum: 2026-06-15 Scope: scripts/lib/config.py, scripts/lib/agents.py, scripts/lib/runtime.py, scripts/lib/viz.py"
tags: [analysis]
timestamp: "2026-06-15T19:29:50Z"
resource: "../../sources/docs/analysis/276-architecture-robustness-audit.md"
migrated_from: "docs/analysis/276-architecture-robustness-audit.md"
---
# Audit: Architecture Robustness (Issue #276)

**Branch:** `feat/framework-issues-batch-2`
**Datum:** 2026-06-15
**Scope:** `scripts/lib/config.py`, `scripts/lib/agents.py`, `scripts/lib/runtime.py`, `scripts/lib/viz.py`

---

## Zusammenfassung

Das Codebase ist insgesamt solide strukturiert. Kritische Pfade (`load_config`, `substitute`) sind
gut abgesichert. Die gefundenen Lücken konzentrieren sich auf **Silent-Failure-Muster** bei optionalen
Features und **fehlendes Error-Propagation** in der Pipeline-Validierung.

---

## Top-5 Architektur-Lücken

### Lücke 1 — `config.py:412`: Silent-Failure in `build_variables()` (HOCH)

**Datei:** `scripts/lib/config.py`, Zeilen 384–413

```python
try:
    pipelines = load_quality_pipelines(str(agent_meta_root))
    overrides = config.get("quality-pipelines", {})
    effective = apply_overrides(pipelines, overrides)
    # Validate pipeline agent references against available roles
    ...
    pipeline_errors = validate_pipelines(effective, list(available_roles))
    for err in pipeline_errors:
        unmapped.append(f"quality-pipelines: {err}")
    ...
except Exception:
    pass
```

**Problem:** Der gesamte `QUALITY_PIPELINES_ENABLED`-Block fällt bei jedem Fehler lautlos zurück
auf `"false"`. Enthält `load_quality_pipelines()` oder `apply_overrides()` einen Bug oder eine
kaputte YAML-Datei, gibt es keine Fehlermeldung — Pipelines werden still deaktiviert. Der `unmapped`-
Mechanismus wird umgangen, da er außerhalb des `except` liegt.

**Empfehlung:** Exception explizit fangen und als Warning in `unmapped` oder `log.warn()` ausgeben:
```python
except Exception as e:
    unmapped.append(f"quality-pipelines: load error — {e}")
    variables["QUALITY_PIPELINES_ENABLED"] = "false"
```

---

### Lücke 2 — `config.py:330`: FileAffinityAnalyzer-Fehler unsichtbar (MITTEL)

**Datei:** `scripts/lib/config.py`, Zeilen 325–331

```python
try:
    from .analysis import FileAffinityAnalyzer, analyze_project
    _deps = analyze_project(agent_meta_root)
    _analyzer = FileAffinityAnalyzer(agent_meta_root)
    variables["FILE_AFFINITY_HINT"] = _analyzer.format_hint(_deps)
except Exception:
    variables["FILE_AFFINITY_HINT"] = ""
```

**Problem:** Fehler im neuen `analysis`-Modul (untracked im Branch) werden komplett verschluckt.
Da `analysis.py` neu ist und noch nicht getestet ist, können ImportErrors oder AttributeErrors hier
auftreten — ohne jede Rückmeldung an den Nutzer.

**Empfehlung:** Spezifisch auf `ImportError` und `ModuleNotFoundError` eingrenzen; andere Exceptions
als Warnung ausgeben:
```python
except ImportError:
    variables["FILE_AFFINITY_HINT"] = ""  # optionales Feature, nicht verfügbar
except Exception as e:
    log.warn(f"FileAffinityAnalyzer error: {e} — FILE_AFFINITY_HINT leer")
    variables["FILE_AFFINITY_HINT"] = ""
```

---

### Lücke 3 — `config.py:380`: Reflection-Pairs-Fehler lautlos ignoriert (MITTEL)

**Datei:** `scripts/lib/config.py`, Zeilen 373–381

```python
try:
    roles_defaults_path = agent_meta_root / "config" / "role-defaults.yaml"
    if roles_defaults_path.exists() and _YAML_AVAILABLE:
        with roles_defaults_path.open(encoding="utf-8") as f:
            roles_defaults = _yaml.safe_load(f) or {}
        if roles_defaults.get("reflection_pairs"):
            variables["REFLECTION_PAIRS_ENABLED"] = "true"
except Exception:
    pass
```

**Problem:** YAML-Parsefehler in `role-defaults.yaml` werden ignoriert. Da diese Datei kritisch für
die gesamte Agent-Generierung ist, sollte ein Lesefehler sichtbar sein.

**Empfehlung:** Exception nicht komplett schlucken — mindestens als stderr-Warning ausgeben, da
`role-defaults.yaml` eine Pflichtdatei ist.

---

### Lücke 4 — `agents.py:44`: Provider-Tools-Config lautlos leer (MITTEL)

**Datei:** `scripts/lib/agents.py`, Zeilen 35–46

```python
try:
    config_path = agent_meta_root / PROVIDER_TOOLS_CONFIG
    if config_path.exists():
        if _YAML_AVAILABLE:
            with open(config_path, encoding="utf-8") as f:
                _provider_tools_cache = _yaml.safe_load(f) or {}
        else:
            _provider_tools_cache = {}
    else:
        _provider_tools_cache = {}
except Exception:
    _provider_tools_cache = {}
```

**Problem:** `load_provider_tools_config()` liefert bei jedem Lesefehler ein leeres Dict. Damit
wird die Tool-Whitelist-Validierung deaktiviert (`_validate_tools_against_whitelist()` gibt alle
Tools durch wenn die Whitelist leer ist). Ein korruptes `config/provider-tools.yaml` würde unbemerkt
zu unkontrollierten Tool-Sets führen.

**Empfehlung:** Fehler beim Lesen einer existierenden Config-Datei als Warning loggen, nicht still
ignorieren.

---

### Lücke 5 — `runtime.py:112`: ThreadPoolExecutor-Fehler ohne spezifischen Typ (NIEDRIG)

**Datei:** `scripts/lib/runtime.py`, Zeilen 112–121

```python
except Exception as e:
    # In case of internal ThreadPoolExecutor exceptions
    tb = traceback.format_exc()
    results[task.task_id] = SubagentResult(
        ...
        status="failed",
        error=f"{str(e)}\n{tb}"
    )
```

**Problem:** Kein `except` für `concurrent.futures.CancelledError` oder `KeyboardInterrupt`.
`KeyboardInterrupt` erbt von `BaseException`, nicht `Exception`, und wird hier korrekt nicht gefangen —
aber `CancelledError` in Python 3.8 erbt von `concurrent.futures.CancelledError` (später von
`BaseException`), was zu unerwarteten Status-Werten führen kann.

**Empfehlung:** Explizit `concurrent.futures.CancelledError` als eigenen Case behandeln und
als `status="cancelled"` markieren.

---

## Weitere Befunde

### TODO-Marker

| Datei | Zeile | Inhalt |
|-------|-------|--------|
| `scripts/lib/hooks.py` | 28 | `# TODO: implement hook logic here` |

`hooks.py` enthält ein leeres TODO — das Modul ist ein Stub. Falls Hooks in zukünftigen Features
benötigt werden, sollte der Stub entweder entfernt oder mit einem `NotImplementedError` versehen werden.

### Breite Exception-Catches in `viz.py`

`scripts/lib/viz.py` enthält 6 weitere `except Exception`-Blöcke (Zeilen 67, 115, 527, 609, 649, 687).
Da `viz.py` ein optionales Feature ist, sind stille Failures dort vertretbar — aber ein zentrales
`log.warn()` bei viz-Fehlern würde Debugging erleichtern.

### Keine Typen-Validierung für `config`-Dict

`build_variables()` in `config.py` vertraut darauf, dass `config` ein `dict` ist (nach `load_config()`).
Es gibt keine Defense gegen den Fall dass `project.yaml` ein leeres File oder ein YAML-Scalar ist
(`_yaml.safe_load()` würde `None` liefern — dies wird in `load_config()` mit `or {}` abgefangen,
in `_validate_config()` jedoch nicht explizit geprüft).

---

## Empfehlungen nach Priorität

| Priorität | # | Datei | Maßnahme |
|-----------|---|-------|----------|
| HOCH | 1 | `config.py:412` | `except Exception: pass` → `except Exception as e: unmapped.append(...)` |
| MITTEL | 2 | `config.py:330` | ImportError vs. allgemeine Exception trennen, Fehler loggen |
| MITTEL | 3 | `config.py:380` | Exception bei `role-defaults.yaml`-Lesefehler als Warning ausgeben |
| MITTEL | 4 | `agents.py:44` | Fehler beim Lesen einer existierenden Config-Datei loggen |
| NIEDRIG | 5 | `runtime.py:112` | `CancelledError` explizit als eigenen Status behandeln |
| NIEDRIG | — | `hooks.py:28` | TODO-Stub entfernen oder mit `NotImplementedError` versehen |

---

## Fazit

Die Architektur ist für den Produktionseinsatz geeignet. Die kritischen Pfade (Config-Parsing,
Template-Substitution) sind gut abgesichert. Die gefundenen Lücken betreffen ausnahmslos optionale
Features, die bei Fehlern stillschweigend deaktiviert werden statt einen sichtbaren Fehler zu werfen.
Das Hauptrisiko ist erschwerte Fehlerdiagnose: Nutzer erhalten keine Rückmeldung wenn Pipelines oder
der FileAffinity-Analyzer nicht laden — das Feature ist einfach inaktiv.
