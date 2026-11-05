# Release Checklist Implementation Plan

> Status: DONE (2026-10-31) — branch `feat/release-checklist`, PR opened after this commit. Review verdict: CHANGES_REQUESTED with 1 blocking finding ("Admin UI used `step` as the item-phase default instead of `precondition`"); the blocking finding and 5 of 6 advisories are fixed, the remaining advisory is a plan defect (see "Ausführungsnachweis (Ledger)").
>
> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development (recommended) or superpowers:executing-plans. Steps use checkbox syntax (`- [ ]`) for tracking.

**Goal:** Projekte steuern die Release-Checkliste über den neuen optionalen Block `release-checklist` (`mode: off|advisory|strict`, eigene agenten- oder skriptbewertete Punkte, Dry-Check `MODE: check-only`), ohne dass sich bei `off` ein generiertes Byte ändert.
**Architecture:** Gesamte Logik (Normalizer, Validator, Resolver, Renderer, Variablen-Builder) liegt im neuen Modul `scripts/lib/release_checklist.py`; `config.py`/`variables.py`/`standalone.py`/`admin-server.py` bekommen nur Aufruf-, Registrierungs- und Guard-Zeilen. Der Release-Agent wertet einen per Platzhalter `{{RELEASE_CHECKLIST_BLOCK}}` gerenderten Prosa-Block aus (kein Laufzeit-Code); Schema, Admin-UI-Sektion, Manager-Rezept und Commands folgen dem Muster von `subagent_permissions`/`auto_commit`.
**Tech Stack:** Python >= 3.9 (nur stdlib), pytest, JSON-Schema (Draft 7 `if/then`), Markdown-Templates mit `{{VAR}}`/`{{#if}}`, vanilla JS in `docs/ui/admin-ui.html`, Bash (Szenario-Asserts).
**Spec:** docs/specs/2026-10-31-release-checklist-spec.md (spec-id: SPEC-RELEASE-CHECKLIST-2026-10-31, rev 1.2, Status APPROVED)

## Global Constraints

- Python-Stdlib only; Python >= 3.9 (kein `X | Y` zur Laufzeit ohne `from __future__ import annotations`, kein `match`) (C1).
- Provider-Agnostik: Unterschiede nur über Config-Keys/Capability-Flags, nie `if provider == "Name"`; der Release-Agent-Text ist provider-neutral (C2).
- Default `off` (Block fehlt, `{}`, `null` oder `mode: off`) => alle generierten Templates (`release.md` und Overrides) byte-identisch; der `{{#if RELEASE_CHECKLIST_ENABLED}}`-Block hinterlässt keine Leerzeile (C3, AC-REL-1).
- Neue lib-Module <= 600 Zeilen (`scripts/lib/release_checklist.py`); bestehende Module (`config.py` 2466, `variables.py` 796, `standalone.py` 537, `admin-server.py`) wachsen nur um Aufruf-/Registrierungs-/Guard-Zeilen (C4, AC-REL-19).
- Neue Platzhalter (`RELEASE_CHECKLIST_MODE`, `RELEASE_CHECKLIST_ENABLED`, `RELEASE_CHECKLIST_BLOCK`) nur mit Registrierung nach `rules/2-platform/agent-meta-conventions.md` ("Adding a New Placeholder", Z.105-109): `config.py`, `consistency/placeholders.py`, `standalone.py`, Whitelist in `variables.py`, Doku `docs/guides/features/sync-concept.md`; Doku-Beispiele mit `{{%RELEASE_CHECKLIST_BLOCK%}}` escapen (C5, Issue #1082).
- YAML-1.1-Bool-Falle: Normalizer bildet NUR `False` -> `"off"` ab (nicht `_normalize_subagent_permissions_mode` 1:1); `True` bleibt, Validator meldet "quote the value" (C6).
- Lese-Resolver beenden nie den Prozess; harte Fehler nur im Python-Validator; das JSON-Schema ist Zusatz (warnt nur, nur mit `jsonschema`) und hat kein Top-Level-`default` (C7, C9).
- Gates (`pre-release-check.sh`, Schritt 0) bleiben in JEDEM Modus hart; `strict` ist nur Prompt-/Konventions-Boundary, nie als Sicherheitsgarantie formulieren (NZ3, AZ2).
- Conventional Commits, Englisch, erste Zeile <= 72 Zeichen, Imperativ, kein führendes BOM; Commit-Trailer laut Session-Attribution. Dokumente Deutsch, Code/Commits/Identifier Englisch, `README.md` Englisch (C8).
- Testkommando-Konvention: `python3 -m pytest <datei>::<test> --basetemp="$PYTEST_BASETEMP"`. `PYTEST_BASETEMP` ist der Wert des Tokens `{{PYTEST_BASETEMP}}` aus `.meta-config/project.yaml` (`variables.TEST_COMMANDS`; Quelle `repo_containment.tmp-sink.system-temp-exception`) und wird vor Start einmal in der Shell gesetzt; kein Literalpfad, kein Basetemp im Arbeitsbaum.
- Verifikation an Template-/Config-Tasks zusätzlich: `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.
- Ausführung auf Feature-Branch `feat/release-checklist` (nicht `main`); Push/Merge nur durch den `git`-Agenten, kein Merge in diesem Plan.

## Review Focus

Eingaben/Fehlerfälle, die die Spec impliziert, aber kein Spec-AC direkt testet. Jede Zeile hat einen benannten Test im besitzenden Task.

| # | Eingabe / Fehlerfall | Erwartung | Test (Task) |
|---|---|---|---|
| R1 | `release-checklist:` leer (YAML `null`), `{}` oder nur `items: []` | wie Block fehlt: Modus `off`, kein Validator-Fehler, `RELEASE_CHECKLIST_ENABLED="false"`, `release.md` byte-identisch | `test_null_and_empty_block_are_absent` (Task 1), `test_resolve_absent_null_empty_is_off` (Task 2), `test_null_and_empty_block_render_identical` (Task 4) |
| R2 | `items` ist kein Array (z. B. String/Mapping) oder ein Item ist kein Mapping | Validator: Fehler mit Pfad (`release-checklist.items`, `release-checklist.items[0]`); Resolver wirft nie, liefert `mode="off"`, `items=[]` | `test_non_list_items_and_non_mapping_item` (Task 1), `test_resolve_broken_structure_never_raises` (Task 2) |
| R3 | `check: script` mit Whitespace-only-`script` oder `script` mit `\r`/`\n` | Fehler: whitespace-only zählt als leer, `\r` zählt wie `\n` als Zeilenumbruch | `test_script_whitespace_only_and_cr` (Task 1) |
| R4 | Item mit falschen Feldtypen: `id` kein String/Pattern-Verstoß (`Foo`, `a_b`, `123`), `required` kein Bool, `task`/`verification` fehlend oder leer | Validator-Fehler je Feld mit Pfad (harte Fehler stehen nur im Python-Validator, das Schema warnt nur) | `test_item_field_types_are_hard_errors` (Task 1) |
| R5 | Admin-UI-Payload mit `mode: false` (Bool) bzw. `mode: true`; Roundtrip von `"off"` durch den YAML-Writer (OF-8) | `False` wird im Guard zu `"off"` normalisiert und gequotet geschrieben (Rücklesen ergibt den String `"off"`); `True` => HTTP 400 "quote the value", nichts geschrieben | `test_guard_normalizes_false_and_rejects_true`, `test_off_roundtrips_as_string` (Task 7) |

---

## File Structure

Abweichung zur Spec §16 (gegen den Code geprüft, im Plan korrigiert): Szenario-IDs 79-87 sind in `registry.md` bereits vergeben (Katalog-Tabelle endet bei 79, Zeilen 79-87 stehen lose am Dateiende) => neue Szenarien tragen `88`/`89`/`90`; `config.py`-Aufrufstellen sind :326 (Normalizer), :396 (Validator) und das Ende von `_build_convention_variables` (:2293-2350); Admin-UI-Nav bei :1632, `router.register` bei :10857, `routeMap` bei :10961; AC-01-Baseline, `slimming-golden`, `compact-golden` und Standalone-Export (`standalone/agents/{release,agent-meta-manager}.md`) sind nachzuziehen (Task 11) und stehen nicht in Spec §16.

| Datei | Verantwortung | neu/ändern |
|---|---|---|
| `scripts/lib/release_checklist.py` | Normalizer, Validator (hart + nicht-exitend), Resolver, Renderer, Variablen-Builder, `RESERVED_DEFAULT_ITEMS` (<= 600 Zeilen) | neu |
| `config/project-config.schema.json` | Schema-Key `release-checklist` (Zusatz, kein `default`) | ändern |
| `scripts/lib/config.py` | je 1 Aufruf: Normalizer (:326), Validator (:396), Variablen (Ende `_build_convention_variables`) | ändern |
| `scripts/lib/variables.py` | Präfix `RELEASE_CHECKLIST_` in Conditional-Whitelist (neben :446) | ändern |
| `scripts/lib/consistency/placeholders.py` | 3 Platzhalter als bekannt eintragen (:106-107) | ändern |
| `scripts/lib/standalone.py` | `_CONDITIONAL_FALSE_FLAGS` + `_ORCHESTRATION_FALLBACKS` | ändern |
| `docs/guides/features/sync-concept.md` | Tabelle "Auto-injiziert" (:280-287) | ändern |
| `agents/1-generic/release.md` | Block nach Z.65, `version` 1.12.2 -> 1.13.0 | ändern |
| `agents/2-platform/hacs-release.md` | `based-on` @1.13.0, `version` 1.1.0 -> 1.1.1 | ändern |
| `agents/2-platform/sharkord-release.md` | Block vor "## Checkliste vor Release", `based-on` @1.13.0, `version` 1.3.2 -> 1.3.3 | ändern |
| `commands/1-generic/release-check.md` | Dry-Check-Command | neu |
| `commands/1-generic/set-release-checklist.md` | Einricht-Command (Vorlage `set-preset.md`) | neu |
| `agents/1-generic/agent-meta-manager.md` | §3-Zeile + Rezept 14d, `version` 1.25.0 -> 1.26.0 | ändern |
| `scripts/admin-server.py` | Whitelist (:233-252) + Section-Guard (:5176-5200) | ändern |
| `docs/ui/admin-ui.html` | `viewProjectReleaseChecklist`, Nav (:1632), Router (:10857), `routeMap` (:10961) | ändern |
| `docs/api/admin-ui-reference.md` | Help-Block `project_instance-release_checklist` | ändern |
| `tests/test_release_checklist_schema.py` | Schema-Tests | neu |
| `tests/test_release_checklist_lib.py` | Validator-/Resolver-/Renderer-Tests | neu |
| `tests/test_release_checklist_consistency.py` | Registrierung/Variablen/Standalone | neu |
| `tests/test_release_checklist_render.py` | Sync-Render: byte-identisch, Text-Asserts, Overrides | neu |
| `tests/test_release_checklist_texts.py` | Commands, Manager, Doku Text-Asserts | neu |
| `tests/test_admin_ui_release_checklist_section.py` | Whitelist/Guard/Parität/UI-Wiring | neu |
| `tests/scenarios/registry.md`, `configs/{88,89,90}-*.project.yaml`, `asserts/{88,89,90}-*.sh` | Szenarien | ändern/neu |
| `docs/RELEASE_GATES.md`, `docs/api/slash-commands.md`, `README.md`, `howto/configs/project.yaml.example`, `CHANGELOG.md` | Doku | ändern |
| `tests/fixtures/ac01-baseline/hashes.json`, `tests/test_ac01_render_identity.py`, `tests/test_opencode_v2_surface.py`, `tests/fixtures/slimming-golden/agent-meta-manager.md`, `standalone/agents/{release,agent-meta-manager}.md`, `standalone/README.md` | Rebaseline/Export | ändern |

> **Nachtrag:** Zwei zusätzlich berührte Dateien fehlen in den Files-Listen der Tasks: `tests/fixtures/slimming-golden/release.md` (Slimming-Gate, Task 11) und §19 im `docs/plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md` (Rebaseline-Dokumentation, Task 11) — der Plan hat sie unter-spezifiziert.

---
pipeline_stages:
  implement: 3
---

## DAG

`1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 -> 9 -> 10 -> 11 -> 12` (linear). Task 5 und 6 teilen `tests/test_release_checklist_texts.py`, Task 7 und 8 teilen `tests/test_admin_ui_release_checklist_section.py` — deshalb keine Parallelgruppe (Ownership-Barriere); inhaltlich wären 5/6 und 7 unabhängig voneinander.

### Task 1: Schema, Normalizer und Validator

**Agent:** developer
**Depends on:** —
**Files:**
- Create: `scripts/lib/release_checklist.py`
- Modify: `config/project-config.schema.json` (neuer Key neben `subagent_permissions`, :1617)
- Modify: `scripts/lib/config.py` (:326 Normalizer-Aufruf, :396 Validator-Aufruf)
- Create: `tests/test_release_checklist_schema.py`
- Create: `tests/test_release_checklist_lib.py`

**Interfaces:**
- Produces (`scripts/lib/release_checklist.py`, `from __future__ import annotations`):
  - `VALID_MODES: tuple[str, ...] = ("off", "advisory", "strict")`, `VALID_PHASES: tuple[str, ...] = ("precondition", "step")`
  - `RESERVED_DEFAULT_ITEMS: tuple[tuple[str, str, bool], ...]` = `(("tests-green","precondition",False), ("dod-met","precondition",True), ("changelog-updated","precondition",False), ("readme-current","precondition",True), ("version-bumped","step",False), ("build-created","step",False), ("git-tag-push","step",False))`
  - `normalize_release_checklist_mode(config: dict) -> None` (nur `False` -> `"off"`)
  - `collect_release_checklist_errors(config: dict) -> list[str]` (nicht-exitend, akzeptiert `False` als `off`, lehnt `True` ab)
  - `validate_release_checklist(config: dict, config_path: Path) -> None` (druckt `ERROR: <path>: <msg>` nach stderr und `sys.exit(1)`)
- Consumes: `config.py::load_config` (:276), `_validate_config` (:367), `_normalize_null_blocks` (:254; macht `null` zu `{}`).

- [x] **Step 1: Failing Tests schreiben**

`tests/test_release_checklist_schema.py`:
```python
import json
from pathlib import Path
import pytest

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "config" / "project-config.schema.json").read_text(encoding="utf-8"))
BLOCK = SCHEMA["properties"]["release-checklist"]
ITEM = BLOCK["properties"]["items"]["items"]

def test_block_shape():
    assert "default" not in BLOCK                                   # C9
    assert BLOCK["additionalProperties"] is False
    assert BLOCK["properties"]["mode"]["enum"] == ["strict", "advisory", "off"]

def test_item_shape():
    assert ITEM["required"] == ["id", "task", "verification"]
    assert ITEM["additionalProperties"] is False
    assert ITEM["properties"]["id"]["pattern"] == "^[a-z0-9][a-z0-9-]*$"
    assert ITEM["properties"]["check"]["enum"] == ["agent", "script"]
    assert ITEM["properties"]["phase"]["enum"] == ["precondition", "step"]
    assert ITEM["then"] == {"required": ["script"]}

def test_jsonschema_accepts_and_rejects():
    jsonschema = pytest.importorskip("jsonschema")
    ok = {"mode": "advisory", "items": [{"id": "a", "task": "t", "verification": "v"}]}
    jsonschema.validate(ok, BLOCK)
    for bad in ({"mode": "on"}, {"items": [{"id": "A", "task": "t", "verification": "v"}]},
                {"items": [{"id": "a", "task": "t", "verification": "v", "check": "script"}]},
                {"unknown": 1}):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(bad, BLOCK)
```

`tests/test_release_checklist_lib.py` (Validierungsteil; Header: `REPO_ROOT = Path(__file__).resolve().parents[1]`, `sys.path.insert(0, str(REPO_ROOT / "scripts"))`, `from lib import release_checklist as rc`; Helfer `_item(**kw)` = `{"id": "a-1", "task": "t", "verification": "v", **kw}`, `_errs(block)` = `rc.collect_release_checklist_errors({"release-checklist": block})`):
```python
def test_normalize_false_only():
    cfg = {"release-checklist": {"mode": False}}
    rc.normalize_release_checklist_mode(cfg)
    assert cfg["release-checklist"]["mode"] == "off"
    cfg = {"release-checklist": {"mode": True}}
    rc.normalize_release_checklist_mode(cfg)
    assert cfg["release-checklist"]["mode"] is True
    assert any("quote the value" in e for e in _errs({"mode": True}))      # AC-REL-3

def test_invalid_mode_names_path():                                         # AC-REL-2
    assert any("release-checklist.mode" in e for e in _errs({"mode": "loose"}))

def test_duplicate_and_reserved_ids():                                      # AC-REL-4
    assert _errs({"items": [_item(), _item()]})
    assert _errs({"items": [_item(id="tests-green")]})

def test_script_check_rules():                                              # AC-REL-5
    assert _errs({"items": [_item(check="script")]})
    assert _errs({"items": [_item(check="agent", script="x")]})
    assert _errs({"items": [_item(check="script", script="a\nb")]})
    assert not _errs({"items": [_item(check="script", script="python3 -V")]})

def test_unknown_keys_and_phase():                                          # AC-REL-5, AC-REL-21
    assert _errs({"bogus": 1})
    assert _errs({"items": [_item(bogus=1)]})
    assert _errs({"items": [_item(phase="later")]})
    assert not _errs({"items": [_item(phase="step", required=False, **{"applies-when": "x"})]})

def test_null_and_empty_block_are_absent():                                 # R1
    for cfg in ({}, {"release-checklist": None}, {"release-checklist": {}},
                {"release-checklist": {"items": []}}):
        assert rc.collect_release_checklist_errors(cfg) == []

def test_non_list_items_and_non_mapping_item():                             # R2
    assert any("release-checklist.items" in e for e in _errs({"items": "x"}))
    assert any("release-checklist.items[0]" in e for e in _errs({"items": ["x"]}))

def test_script_whitespace_only_and_cr():                                   # R3
    assert _errs({"items": [_item(check="script", script="   ")]})
    assert _errs({"items": [_item(check="script", script="a\rb")]})

def test_item_field_types_are_hard_errors():                                # R4
    for bad in (_item(id="Foo"), _item(id="a_b"), _item(id=123), _item(required="yes"),
                _item(task=""), _item(verification=None)):
        assert _errs({"items": [bad]}), bad
    assert _errs({"items": [{"id": "x", "verification": "v"}]})            # task missing

def test_validate_exits_with_path(capsys, tmp_path):
    with pytest.raises(SystemExit):
        rc.validate_release_checklist({"release-checklist": {"mode": "loose"}}, tmp_path / "project.yaml")
    assert "release-checklist.mode" in capsys.readouterr().err

def test_load_config_normalizes_unquoted_off(tmp_path):                     # AC-REL-3 end-to-end
    from lib.config import load_config
    p = tmp_path / "project.yaml"
    p.write_text("project: {name: x, prefix: x}\nrelease-checklist:\n  mode: off\n", encoding="utf-8")
    assert load_config(p)["release-checklist"]["mode"] == "off"
```

- [x] **Step 2: Run -> FAIL erwarten**
`python3 -m pytest tests/test_release_checklist_schema.py tests/test_release_checklist_lib.py --basetemp="$PYTEST_BASETEMP"` — erwartet: `KeyError: 'release-checklist'` bzw. `ImportError: cannot import name 'release_checklist'`.

- [x] **Step 3: Implementierung**
  - Schema: den Block aus Spec §9.2 wörtlich unter `properties` einfügen (neben `subagent_permissions`); kein Top-Level-`default`. Danach `python3 scripts/sync.py --validate` (formatiert nur um — reine Formatierungsdrift nicht committen).
  - `release_checklist.py`: die oben gelisteten Symbole. `collect_release_checklist_errors` prüft §9.4 Regeln 1-6 plus Typ-/Pattern-Regeln (R4: `id` String + `^[a-z0-9][a-z0-9-]*$`, `task`/`verification` nicht-leere Strings, `required` Bool, `applies-when` nicht-leerer String falls gesetzt, `check` in {agent, script}), `script` per `.strip()` nicht leer und ohne `\n`/`\r`; Fehlertext beginnt jeweils mit dem Pfad (`release-checklist.items[<i>].<key>`); Block `None`/`{}` => keine Fehler; `validate_release_checklist` formatiert wie `_validate_subagent_permissions` (:674-707).
  - `config.py`: nach :326 `normalize_release_checklist_mode(config)`; neben :396 `validate_release_checklist(config, config_path)` (Import lokal wie im Bestand: `from .release_checklist import ...`).

- [x] **Step 4: Run -> PASS**
Dasselbe Kommando; zusätzlich `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate` (kein neuer Fehler).

- [x] **Step 5: Commit**
`git add scripts/lib/release_checklist.py config/project-config.schema.json scripts/lib/config.py tests/test_release_checklist_schema.py tests/test_release_checklist_lib.py`
`git commit -m "feat: add release-checklist schema, normalizer and validator"`

### Task 2: Resolver, Renderer und Variablen-Builder

**Agent:** developer
**Depends on:** 1
**Files:**
- Modify: `scripts/lib/release_checklist.py`
- Modify: `tests/test_release_checklist_lib.py`

**Interfaces:**
- Consumes: `collect_release_checklist_errors`, `RESERVED_DEFAULT_ITEMS`, `VALID_MODES` (Task 1).
- Produces:
  - `resolve_release_checklist(config: dict) -> dict` -> `{"mode": str, "items": list[dict]}`; Items mit Defaults `check="agent"`, `phase="precondition"`, `required=True`; `script`/`applies-when` nur falls gesetzt; bei `collect_release_checklist_errors(config) != []` oder kaputter Struktur: `{"mode": "off", "items": []}` + `logging.getLogger(__name__).warning(...)`; wirft nie, beendet nie.
  - `render_release_checklist_block(resolved: dict) -> str` (`""` bei `mode == "off"`)
  - `build_release_checklist_variables(config: dict) -> dict[str, str]` -> Keys `RELEASE_CHECKLIST_MODE`, `RELEASE_CHECKLIST_ENABLED` (`"true"`/`"false"`), `RELEASE_CHECKLIST_BLOCK`.

Block-Inhalt (Reihenfolge, Englisch, provider-neutral; Items-Tabelle `| id | phase | check | required | task | verification | applies-when |`, bei `check: script` steht das Skript als `` `<script>` `` in der `verification`-Spalte; ohne Items eine Zeile "Project items: none."): (1) Überschrift + Modus-Prosa mit Verweis auf Step 0 (Gates bleiben in jedem Modus hart, `STATUS: failed`), "Prompt-/Konventions-Boundary"-Satz bei `strict`; (2) Klassen Vorbedingung (`tests-green`, `dod-met`, `changelog-updated`, `readme-current`) vs. Schritt (`version-bumped`, `build-created`, `git-tag-push`); (3) Items-Tabelle; (4) Script-Regeln (Exit 0 = pass, != 0 = fail, fehlendes Skript = fail, side-effect free); (5) Ablauf 1-5 aus Spec §10.2 und Freigabeprotokoll R-S6..R-S8 (`APPROVAL_REQUEST`, `APPROVED:`); (6) `n/a`-Regeln R-S3/R-S9 (`reason` Pflicht, einzeilig; `n/a` in strict nur mit `applies-when`, für `dod-met`/`readme-current` mit Begründung); (7) Ergebnis-Contract §10.3 (`CHECKLIST_MODE`, `CHECKLIST`-Tabelle mit Spalte `phase`, `CHECKLIST_SUMMARY: pass fail n/a not_run required_failed`, `APPROVAL_REQUEST`, STATUS-Zuordnung; `CHECKLIST_*`-Zeilen dem Return voranstellen); (8) `check-only`-Regeln §10.4 (`MODE: check-only`, Schritte `n/a (nicht ausgeführt)`, Verbote, kein `APPROVAL_REQUEST`); (9) R-S4 (Modus nie selbst ändern).

- [x] **Step 1: Failing Tests** (Ergänzung in `tests/test_release_checklist_lib.py`)
```python
REQUIRED_PHRASES = (                       # AC-REL-6..9, 11, 21-25 (Template-Text-Asserts)
    "CHECKLIST_MODE", "CHECKLIST_SUMMARY", "not_run", "required_failed", "APPROVAL_REQUEST", "APPROVED:",
    "MODE: check-only", "n/a (nicht ausgeführt)", "Exit 0 = pass", "side-effect free",
    "Step 0", "STATUS: failed", "dod-met", "readme-current", "tests-green", "changelog-updated",
    "version-bumped", "build-created", "git-tag-push", "| phase |",
)
def _res(mode, items=()):
    return rc.resolve_release_checklist({"release-checklist": {"mode": mode, "items": list(items)}})

def test_resolve_defaults():
    r = _res("advisory", [_item()])
    assert r["mode"] == "advisory"
    assert r["items"][0]["check"] == "agent" and r["items"][0]["phase"] == "precondition" and r["items"][0]["required"] is True

def test_resolve_absent_null_empty_is_off():                                # R1
    for cfg in ({}, {"release-checklist": None}, {"release-checklist": {}}):
        assert rc.resolve_release_checklist(cfg) == {"mode": "off", "items": []}
    assert rc.resolve_release_checklist({"release-checklist": {"mode": False}})["mode"] == "off"

def test_resolve_broken_structure_never_raises():                           # R2
    for cfg in ({"release-checklist": "x"}, {"release-checklist": {"items": "x"}},
                {"release-checklist": {"mode": "strict", "items": ["x"]}}, {"release-checklist": {"mode": True}}):
        assert rc.resolve_release_checklist(cfg) == {"mode": "off", "items": []}

def test_render_empty_when_off():
    assert rc.render_release_checklist_block(_res("off", [_item()])) == ""

def test_render_modes_contain_contract():
    for mode in ("advisory", "strict"):
        text = rc.render_release_checklist_block(_res(mode, [_item(id="docker-pushed", phase="step", required=False)]))
        for phrase in REQUIRED_PHRASES: assert phrase in text, (mode, phrase)
        assert "docker-pushed" in text
        assert "non-blocking" not in text and "not blocking" not in text   # AC-REL-22
    assert "Prompt-/Konventions-Boundary" in rc.render_release_checklist_block(_res("strict"))   # AC-REL-7

def test_render_script_item_row():
    text = rc.render_release_checklist_block(_res("strict", [_item(id="sv", check="script", script="python3 scripts/sync.py --validate")]))
    assert "`python3 scripts/sync.py --validate`" in text                   # AC-REL-9

def test_reserved_items_flags_and_template_rowcount():                      # AC-REL-21, b10
    flags = {i: f for i, _, f in rc.RESERVED_DEFAULT_ITEMS}
    assert {i for i, f in flags.items() if f} == {"dod-met", "readme-current"}
    assert {p for _, p, _ in rc.RESERVED_DEFAULT_ITEMS} == {"precondition", "step"}
    tpl = (REPO_ROOT / "agents" / "1-generic" / "release.md").read_text(encoding="utf-8")
    head = tpl.split("## 1. Pre-release checklist", 1)[1].split("{{RELEASE_CUSTOM_CHECKLIST_BLOCK}}", 1)[0]
    rows = [l for l in head.splitlines() if l.startswith("| ") and not l.startswith(("| Check", "|--"))]
    assert len(rows) == len(rc.RESERVED_DEFAULT_ITEMS)

def test_strict_block_na_rules():                                           # AC-REL-8, AC-REL-25
    text = rc.render_release_checklist_block(_res("strict"))
    assert "`reason`" in text and "applies-when" in text
    assert "single line" in text      # einzeilige Begründung

def test_build_variables():
    off = rc.build_release_checklist_variables({})
    assert off == {"RELEASE_CHECKLIST_MODE": "off", "RELEASE_CHECKLIST_ENABLED": "false", "RELEASE_CHECKLIST_BLOCK": ""}
    on = rc.build_release_checklist_variables({"release-checklist": {"mode": "strict"}})
    assert on["RELEASE_CHECKLIST_ENABLED"] == "true" and on["RELEASE_CHECKLIST_BLOCK"]

def test_module_size_limit():                                               # AC-REL-19
    assert len((REPO_ROOT / "scripts" / "lib" / "release_checklist.py").read_text(encoding="utf-8").splitlines()) <= 600
```

- [x] **Step 2: Run -> FAIL** (`AttributeError: module 'lib.release_checklist' has no attribute 'resolve_release_checklist'`):
`python3 -m pytest tests/test_release_checklist_lib.py --basetemp="$PYTEST_BASETEMP"`
- [x] **Step 3: Implementierung** der drei Funktionen in `scripts/lib/release_checklist.py` mit exakt den Signaturen oben; der Block-Text trägt alle Phrasen aus `REQUIRED_PHRASES` (der Test ist der Inhaltsvertrag); die Zeichenfolge `{{` darf im Block nicht vorkommen (der Block wird vor der Platzhalter-Prüfung eingesetzt, ein `{{` würde als unbekannter Platzhalter gemeldet).
- [x] **Step 4: Run -> PASS** (selbes Kommando).
- [x] **Step 5: Commit**
`git add scripts/lib/release_checklist.py tests/test_release_checklist_lib.py`
`git commit -m "feat: add release-checklist resolver, renderer and variables"`

### Task 3: Platzhalter-Registrierung

**Agent:** developer
**Depends on:** 2
**Files:**
- Modify: `scripts/lib/config.py` (Ende von `_build_convention_variables`, nach der `for _domain`-Schleife, ~:2350)
- Modify: `scripts/lib/variables.py` (neben :446 `SUBAGENT_PERMISSIONS_`)
- Modify: `scripts/lib/consistency/placeholders.py` (:106-107)
- Modify: `scripts/lib/standalone.py` (`_ORCHESTRATION_FALLBACKS` :81-108, `_CONDITIONAL_FALSE_FLAGS` :122-145)
- Modify: `docs/guides/features/sync-concept.md` (Tabelle :280-287)
- Create: `tests/test_release_checklist_consistency.py`

**Interfaces:**
- Consumes: `build_release_checklist_variables(config) -> dict[str, str]` (Task 2).
- Produces: `variables["RELEASE_CHECKLIST_MODE|_ENABLED|_BLOCK"]` aus `build_variables(config, agent_meta_root)`; Conditional-Whitelist erkennt `RELEASE_CHECKLIST_*`; Standalone-Fallbacks `RELEASE_CHECKLIST_ENABLED="false"`, `RELEASE_CHECKLIST_BLOCK=""`.

- [x] **Step 1: Failing Tests** (`tests/test_release_checklist_consistency.py`; Fixture `base_config` und Helfer `_build` wie in `tests/test_conventions_migration_invariant.py:51-63`)
```python
def test_build_variables_default_and_enabled(base_config):
    off = _build(base_config)
    assert off["RELEASE_CHECKLIST_ENABLED"] == "false" and off["RELEASE_CHECKLIST_BLOCK"] == ""
    cfg = copy.deepcopy(base_config); cfg["release-checklist"] = {"mode": "advisory"}
    on = _build(cfg)
    assert on["RELEASE_CHECKLIST_ENABLED"] == "true" and "CHECKLIST_MODE" in on["RELEASE_CHECKLIST_BLOCK"]

def test_whitelist_strips_inactive_block():
    from lib.variables import strip_inactive_conditional_blocks as strip
    src = "a\n{{#if RELEASE_CHECKLIST_ENABLED}}\nX\n{{/if}}\nb\n"
    assert strip(src, {"RELEASE_CHECKLIST_ENABLED": "false"}) == "a\nb\n"          # AC-REL-1 (kein Leerzeilen-Rest)
    assert strip(src, {"RELEASE_CHECKLIST_ENABLED": "true"}) == "a\nX\nb\n"

def test_placeholders_known_and_builder_check_clean():
    from lib.consistency.placeholders import check_builder_known_set
    assert [f for f in check_builder_known_set(REPO_ROOT) if "RELEASE_CHECKLIST" in f.message] == []

def test_standalone_fallbacks():
    from lib.standalone import _CONDITIONAL_FALSE_FLAGS, _ORCHESTRATION_FALLBACKS
    assert _CONDITIONAL_FALSE_FLAGS["RELEASE_CHECKLIST_ENABLED"] == "false"
    assert _ORCHESTRATION_FALLBACKS["RELEASE_CHECKLIST_BLOCK"] == ""

def test_sync_concept_documents_placeholders():
    doc = (REPO_ROOT / "docs/guides/features/sync-concept.md").read_text(encoding="utf-8")
    for name in ("RELEASE_CHECKLIST_MODE", "RELEASE_CHECKLIST_ENABLED", "RELEASE_CHECKLIST_BLOCK"):
        assert name in doc
    assert "{{RELEASE_CHECKLIST_BLOCK}}" not in doc and "{{%RELEASE_CHECKLIST_BLOCK%}}" in doc   # escaped (#1082)
```
- [x] **Step 2: Run -> FAIL** (`KeyError: 'RELEASE_CHECKLIST_ENABLED'`):
`python3 -m pytest tests/test_release_checklist_consistency.py --basetemp="$PYTEST_BASETEMP"`
- [x] **Step 3: Implementierung** (nur Aufruf-/Registrierungszeilen, keine Logik): `config.py`: am Ende von `_build_convention_variables` lokaler Import `from .release_checklist import build_release_checklist_variables` und `variables.update(build_release_checklist_variables(config))`; `variables.py`: `conditional_vars.update({k for k in variables if k.startswith("RELEASE_CHECKLIST_")})`; `placeholders.py`: die drei Namen in die Menge mit `RELEASE_CUSTOM_CHECKLIST_BLOCK`; `standalone.py`: `"RELEASE_CHECKLIST_BLOCK": ""` und `"RELEASE_CHECKLIST_ENABLED": "false"` mit Kommentar im Stil von `SUBAGENT_PERMISSIONS_*`; `sync-concept.md`: drei Tabellenzeilen (Block-Beispiel mit `{{%RELEASE_CHECKLIST_BLOCK%}}`).
- [x] **Step 4: Run -> PASS**; zusätzlich `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate` und `python3 scripts/consistency-check.py --changed` (keine neuen ERRORs).
- [x] **Step 5: Commit**
`git add scripts/lib/config.py scripts/lib/variables.py scripts/lib/consistency/placeholders.py scripts/lib/standalone.py docs/guides/features/sync-concept.md tests/test_release_checklist_consistency.py`
`git commit -m "feat: register release-checklist placeholders"`

### Task 4: Templates release.md, hacs-release, sharkord-release

**Agent:** developer
**Depends on:** 3
**Files:**
- Modify: `agents/1-generic/release.md` (Frontmatter :3; Einfügen nach :65)
- Modify: `agents/2-platform/hacs-release.md` (:3-4)
- Modify: `agents/2-platform/sharkord-release.md` (:3-4; vor :226)
- Create: `tests/test_release_checklist_render.py`

**Interfaces:**
- Consumes: Variablen aus Task 3; Sync-Aufruf `python3 scripts/sync.py` (cwd = Projektverzeichnis mit `.meta-config/project.yaml`).
- Produces: Test-Helfer `_sync(tmp_path: Path, block: dict | None, platforms: list[str]) -> str` (liefert den Inhalt von `.claude/agents/release.md`); gerendertes `release.md` mit Block bei `mode != off`.

- [x] **Step 1: Failing Tests** (`tests/test_release_checklist_render.py`; `_sync` schreibt eine Minimal-Config wie `configs/87-project-description.project.yaml` mit `roles: [orchestrator, developer, git, release]`, `platforms`, optional `release-checklist`, startet `sys.executable scripts/sync.py` per `subprocess.run(..., cwd=tmp_path, check=True)` und liest `.claude/agents/release.md`)
```python
def test_off_absent_and_empty_are_byte_identical(tmp_path):                 # AC-REL-1
    ref = _sync(tmp_path / "a", None, [])
    assert _sync(tmp_path / "b", {"mode": "off"}, []) == ref
    assert _sync(tmp_path / "c", {"mode": False}, []) == ref
    assert "CHECKLIST_MODE" not in ref and "RELEASE_CHECKLIST" not in ref

def test_null_and_empty_block_render_identical(tmp_path):                   # R1
    ref = _sync(tmp_path / "a", None, [])
    assert _sync(tmp_path / "b", {}, []) == ref
    assert _sync(tmp_path / "c", {"items": []}, []) == ref

def test_advisory_text(tmp_path):                                           # AC-REL-6, 11, 21-23
    text = _sync(tmp_path, {"mode": "advisory", "items": [ITEM_A, ITEM_B]}, [])
    for phrase in REQUIRED_PHRASES: assert phrase in text
    assert ITEM_A["id"] in text and ITEM_B["id"] in text
    assert text.index("## 1. Pre-release checklist") < text.index("CHECKLIST_MODE") < text.index("## 2. Versioning")
    assert "{{" not in text

def test_strict_text(tmp_path):                                             # AC-REL-7, 8, 24, 25
    text = _sync(tmp_path, {"mode": "strict"}, [])
    assert "Prompt-/Konventions-Boundary" in text and "required_failed" in text

def test_gates_step0_text_unchanged(tmp_path):                              # AC-REL-22
    text = _sync(tmp_path, {"mode": "strict"}, [])
    assert "Exit code ≠ 0 → abort the release, `STATUS: failed`" in text

def test_hacs_override(tmp_path):                                           # AC-REL-12
    text = _sync(tmp_path, {"mode": "advisory"}, ["hacs"])
    assert "HACS Release-Regeln" in text and "CHECKLIST_MODE" in text
    assert 'based-on: "1-generic/release.md@1.13.0"' in (REPO_ROOT / "agents/2-platform/hacs-release.md").read_text(encoding="utf-8")

def test_sharkord_override(tmp_path):
    adv = _sync(tmp_path / "a", {"mode": "advisory"}, ["sharkord"])
    assert "CHECKLIST_MODE" in adv and adv.index("CHECKLIST_MODE") < adv.index("## Checkliste vor Release")
    assert "CHECKLIST_MODE" not in _sync(tmp_path / "b", {"mode": "off"}, ["sharkord"])
    assert _sync(tmp_path / "c", {"mode": "off"}, ["sharkord"]) == _sync(tmp_path / "d", None, ["sharkord"])

def test_template_versions():
    import re
    def ver(p): return re.search(r'^version: "([^"]+)"', (REPO_ROOT / p).read_text(encoding="utf-8"), re.M).group(1)
    assert (ver("agents/1-generic/release.md"), ver("agents/2-platform/hacs-release.md"),
            ver("agents/2-platform/sharkord-release.md")) == ("1.13.0", "1.1.1", "1.3.3")
```
(`REQUIRED_PHRASES` aus Task 2 kopieren; `ITEM_A`/`ITEM_B`: ein `agent`-Item `changelog-unreleased`, ein `script`-Item `schema-valid` aus Spec §9.1; `sharkord`-Variablen (`PLUGIN_DIR_NAME`, `REQUIRED_BINARY_NAMES`, ...) wie `tests/scenarios/configs/04-platform-bundle.project.yaml`.)
- [x] **Step 2: Run -> FAIL** (`assert 'CHECKLIST_MODE' in text`):
`python3 -m pytest tests/test_release_checklist_render.py --basetemp="$PYTEST_BASETEMP"`
- [x] **Step 3: Implementierung**
  - `release.md`: `version: "1.13.0"`; direkt nach `{{RELEASE_CUSTOM_CHECKLIST_BLOCK}}` (Z.65), vor `## 2. Versioning`, exakt `{{#if RELEASE_CHECKLIST_ENABLED}}` / `{{RELEASE_CHECKLIST_BLOCK}}` / `{{/if}}` je auf eigener Zeile. Schritt-0-Text und Default-Tabelle bleiben im Wortlaut.
  - `hacs-release.md`: `version: "1.1.1"`, `based-on: "1-generic/release.md@1.13.0"`; Patch unverändert.
  - `sharkord-release.md`: `version: "1.3.3"`, `based-on: "1-generic/release.md@1.13.0"`; vor `## Checkliste vor Release` dieselbe `{{#if}}`-Dreizeilengruppe, davor (innerhalb des `{{#if}}`) ein Satz: "Step 0: if a `pre-release-check.sh` gate hook exists, run it first; exit code != 0 aborts the release with `STATUS: failed` in every mode." (Sharkord hat keinen eigenen Schritt 0).
- [x] **Step 4: Run -> PASS**; `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`; `python3 -m pytest tests/test_conventions_migration_invariant.py --basetemp="$PYTEST_BASETEMP"` (grün). `tests/test_ac01_render_identity.py` hier nur beobachten: rot ist erwartet, falls der Render von `version` abhängt; Behebung in Task 11.
- [x] **Step 5: Commit**
`git add agents/1-generic/release.md agents/2-platform/hacs-release.md agents/2-platform/sharkord-release.md tests/test_release_checklist_render.py`
`git commit -m "feat: render release-checklist block in release templates"`

### Task 5: Commands release-check und set-release-checklist

**Agent:** developer
**Depends on:** 4
**Files:**
- Create: `commands/1-generic/release-check.md`
- Create: `commands/1-generic/set-release-checklist.md`
- Modify: `docs/api/slash-commands.md` (Tabelle ~:21-23)
- Modify: `README.md` (Befehlstabelle ~:499, Englisch)
- Create: `tests/test_release_checklist_texts.py`

**Interfaces:**
- Consumes: Auftragsparameter `MODE: check-only` des Release-Agenten (Task 2/4).
- Produces: Slash-Commands `/release-check` (Frontmatter `description`; delegiert nur an `release`) und `/set-release-checklist` (`allowed-tools: ["Read", "Edit", "Bash"]`, `argument-hint: "<off|advisory|strict>"`).

- [x] **Step 1: Failing Tests** (`tests/test_release_checklist_texts.py`; Header wie die anderen Testdateien)
```python
def test_release_check_command():                                           # AC-REL-10
    t = (REPO_ROOT / "commands/1-generic/release-check.md").read_text(encoding="utf-8")
    assert t.startswith("---\ndescription:") and "MODE: check-only" in t
    for forbidden in ("tag", "push", "build", "version bump", "edit", "commit", "gh release"):
        assert forbidden in t.lower()
    assert "not active" in t.lower()                                        # Release-Agent inaktiv => Hinweis

def test_set_release_checklist_command():
    t = (REPO_ROOT / "commands/1-generic/set-release-checklist.md").read_text(encoding="utf-8")
    assert "release-checklist" in t and "quote" in t and "--validate" in t

def test_commands_documented():
    for p in ("docs/api/slash-commands.md", "README.md"):
        s = (REPO_ROOT / p).read_text(encoding="utf-8")
        assert "/release-check" in s and "/set-release-checklist" in s
```
- [x] **Step 2: Run -> FAIL** (`FileNotFoundError`): `python3 -m pytest tests/test_release_checklist_texts.py --basetemp="$PYTEST_BASETEMP"`
- [x] **Step 3: Implementierung**
  - `release-check.md`: dünner Prompt: "Delegate to the `release` agent with `MODE: check-only`; return its `CHECKLIST` table"; Verbote vollständig (Tag, Push, Build, Version-Bump, CHANGELOG-/Datei-Edit, Commit, `gh release`); Hinweis, dass `check: script`-Items trotzdem laufen und side-effect free sein müssen; "If the release agent is not active in this project, say so and stop."; funktioniert auch bei `mode: off` (der Agent kennt `check-only` nur aus diesem Text).
  - `set-release-checklist.md`: Vorlage `set-preset.md`: `.meta-config/project.yaml` lesen, `release-checklist.mode` ändern (Wert gequotet: "quote the value"), bei `strict` explizite Bestätigung ("prompt convention only, gates stay hard"), sync, `--validate`.
  - Docs: je eine Zeile in `slash-commands.md` und `README.md` (Englisch).
- [x] **Step 4: Run -> PASS**; `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.
- [x] **Step 5: Commit**
`git add commands/1-generic/release-check.md commands/1-generic/set-release-checklist.md docs/api/slash-commands.md README.md tests/test_release_checklist_texts.py`
`git commit -m "feat: add release-check and set-release-checklist commands"`

### Task 6: agent-meta-manager Rezept

**Agent:** developer
**Depends on:** 5
**Files:**
- Modify: `agents/1-generic/agent-meta-manager.md` (Frontmatter :3; §3-Tabelle :60-73; neuer Abschnitt `### 14d` nach :418)
- Modify: `tests/test_release_checklist_texts.py`

**Interfaces:**
- Consumes: Schema-Key `release-checklist` (Task 1).
- Produces: Manager `version: "1.26.0"`; Rezept 14d "Structured release checklist (opt-in)"; §3-Zeile für `strict`.

- [x] **Step 1: Failing Tests** (Ergänzung)
```python
def test_manager_recipe():                                                  # AC-REL-16
    t = (REPO_ROOT / "agents/1-generic/agent-meta-manager.md").read_text(encoding="utf-8")
    assert 'version: "1.26.0"' in t and "### 14d." in t and "release-checklist" in t
    sec3 = t.split("## 3. Confirmation required", 1)[1].split("## 4.", 1)[0]
    assert "release-checklist.mode" in sec3 and "strict" in sec3
    assert "gates stay hard in every mode" in t.lower()
    assert "weicher" not in t and "softer" not in t.lower()                 # U8: kein "Gates werden weicher"
    assert "quote" in t.lower()
```
- [x] **Step 2: Run -> FAIL** (`assert 'version: "1.26.0"' in t`): `python3 -m pytest tests/test_release_checklist_texts.py::test_manager_recipe --basetemp="$PYTEST_BASETEMP"`
- [x] **Step 3: Implementierung**: Version 1.26.0; §3-Zeile `Enable release-checklist.mode strict | Behavior change: mandatory items stop the release (prompt convention only, no hook)`; Abschnitt 14d im Stil 14a-c: (1) Block lesen, (2) Modus erfragen, (3) Items ergänzen (id/task/verification/check/phase), (4) `project.yaml` editieren (Modus gequotet, YAML-Beispiel aus Spec §9.1), (5) `python scripts/sync.py` + `--validate`, (6) Hinweis "strict = prompt convention; gates stay hard in every mode"; Verweis auf Schema als Autorität (§15) und `/set-release-checklist`.
- [x] **Step 4: Run -> PASS**; `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`; `python3 scripts/consistency-check.py --changed` (frontmatter.version-bump grün).
- [x] **Step 5: Commit**
`git add agents/1-generic/agent-meta-manager.md tests/test_release_checklist_texts.py`
`git commit -m "feat: add release-checklist recipe to agent-meta-manager"`

### Task 7: Admin-Server Whitelist und Section-Guard

**Agent:** developer
**Depends on:** 2
**Files:**
- Modify: `scripts/admin-server.py` (:233-252 `PROJECT_WRITABLE_SECTIONS`; `_write_project_section` :5176-5200 + neue Methode `_guard_release_checklist_write` neben `_guard_model_block_write` :5202)
- Create: `tests/test_admin_ui_release_checklist_section.py`

**Interfaces:**
- Consumes: `collect_release_checklist_errors`, `normalize_release_checklist_mode` (Task 1); Handler-Muster aus `tests/test_admin_server.py` (`_load_admin_server` :40-50, `AdminRequestHandler.__new__`, `ConfigManager(root, mode="project_admin")`, `_make_handler` wie `TestContextProfileWriteGuard` :1957).
- Produces: `AdminRequestHandler._guard_release_checklist_write(self, section: str, data: Any) -> Any` — gibt bei `section == "release-checklist"` die normalisierte Payload zurück (`False` -> `"off"`), wirft `ValueError(...)` (-> HTTP 400) bei Fehlerliste; sonst gibt es `data` unverändert zurück. In `_write_project_section`: `data = self._guard_release_checklist_write(section, data)` vor `existing[section] = data`.

- [x] **Step 1: Failing Tests** (Loader und `_make_handler` aus `tests/test_admin_server.py` kopieren)
```python
def _put(handler, data):
    handler._read_body = lambda: {"section": "release-checklist", "data": data}
    handler._write_project_section()

def test_whitelist_contains_section():                                      # AC-REL-13
    assert "release-checklist" in admin_server.PROJECT_WRITABLE_SECTIONS

def test_valid_payload_roundtrip(tmp_path):
    h = _make_handler(tmp_path)
    payload = {"mode": "strict", "items": [{"id": "schema-valid", "task": "t", "verification": "v", "check": "script", "script": "python3 -V"}]}
    _put(h, payload)
    assert h.config_manager.read("project")["release-checklist"] == payload

def test_invalid_payloads_rejected_without_write(tmp_path):                 # AC-REL-13
    h = _make_handler(tmp_path)
    h.config_manager.write("project", {"release-checklist": {"mode": "advisory"}})
    dup = {"mode": "strict", "items": [{"id": "a", "task": "t", "verification": "v"}] * 2}
    for bad in ({"mode": "loose"}, {"mode": True}, {"mode": "strict", "bogus": 1}, dup):
        with pytest.raises(ValueError): _put(h, bad)
    assert h.config_manager.read("project")["release-checklist"] == {"mode": "advisory"}

def test_guard_normalizes_false_and_rejects_true(tmp_path):                 # R5
    h = _make_handler(tmp_path)
    _put(h, {"mode": False})
    assert h.config_manager.read("project")["release-checklist"]["mode"] == "off"
    with pytest.raises(ValueError, match="quote the value"): _put(h, {"mode": True})

def test_off_roundtrips_as_string(tmp_path):                                # R5, OF-8
    h = _make_handler(tmp_path)
    _put(h, {"mode": "off"})
    raw = (tmp_path / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
    loaded = yaml.safe_load(raw)["release-checklist"]["mode"]
    assert loaded == "off" and isinstance(loaded, str)                      # Writer quotet "off"

def test_parity_with_direct_yaml_fragment(tmp_path):                        # AC-REL-15
    payload = {"mode": "advisory", "items": [{"id": "x-1", "task": "t", "verification": "v", "phase": "step", "required": False}]}
    h = _make_handler(tmp_path); _put(h, payload)
    manual = yaml.safe_load(yaml.safe_dump({"release-checklist": payload}))
    assert yaml.safe_load((tmp_path / ".meta-config" / "project.yaml").read_text(encoding="utf-8")) == manual
```
- [x] **Step 2: Run -> FAIL** (`assert 'release-checklist' in PROJECT_WRITABLE_SECTIONS`): `python3 -m pytest tests/test_admin_ui_release_checklist_section.py --basetemp="$PYTEST_BASETEMP"`
- [x] **Step 3: Implementierung**: `"release-checklist"` in die Whitelist (Kommentar: Release-Checkliste, Admin UI); Guard: lokaler Import `from lib.release_checklist import collect_release_checklist_errors, normalize_release_checklist_mode`; Kopie `{"release-checklist": copy.deepcopy(data)}` normalisieren, `collect_release_checklist_errors`, bei Fehlern `raise ValueError("invalid 'release-checklist': " + "; ".join(errors))`, sonst normalisierte Payload zurück. Falls `test_off_roundtrips_as_string` rot bleibt (OF-8): den Writer-Pfad `lib/io.py::yaml_dump_preserving_multiline` anpassen, sodass `"off"` gequotet wird, und den Fix im Commit-Body erwähnen.
- [x] **Step 4: Run -> PASS**; `python3 -m pytest tests/test_admin_server.py --basetemp="$PYTEST_BASETEMP"` (keine Regression).
- [x] **Step 5: Commit**
`git add scripts/admin-server.py tests/test_admin_ui_release_checklist_section.py`
`git commit -m "feat: guard release-checklist writes in admin server"`

### Task 8: Admin-UI Sektion, Router, Help

**Agent:** developer
**Depends on:** 7
**Files:**
- Modify: `docs/ui/admin-ui.html` (Nav :1632, neue `viewProjectReleaseChecklist` nach `viewProjectAutoCommit` :7637-7764, `router.register` :10857, `routeMap` :10961-10972)
- Modify: `docs/api/admin-ui-reference.md` (nach Auto-Commit-Block ~:185)
- Modify: `tests/test_admin_ui_release_checklist_section.py`

**Interfaces:**
- Consumes: `saveProjectSection(key, value, statusEl)` (:5958), Helfer `el`, `dropdownField` (:6200), `checkboxField` (:6219), `textInputEl` (:7456), `a11yField` (:5990), `showModal(title, body, footer)` (:820), `loadProject()`, `clone()`; Server-Guard (Task 7).
- Produces: Route `/project/release-checklist`, `async function viewProjectReleaseChecklist()`, Help-ID `project_instance-release_checklist`.

- [x] **Step 1: Failing Tests** (Muster `tests/test_admin_ui_git_section.py`; `HTML`/`HELP_REF`/`REPO_ROOT` dort einlesen)
```python
ROUTE, VIEW, HELP = "/project/release-checklist", "viewProjectReleaseChecklist", "project_instance-release_checklist"

def test_view_route_nav_routemap_help():                                    # AC-REL-14
    assert f"async function {VIEW}(" in HTML and HTML.count(VIEW) >= 2
    assert re.search(r'router\.register\(\s*"' + re.escape(ROUTE) + r'"\s*,\s*' + VIEW + r'\s*\)', HTML)
    assert f'route: "{ROUTE}"' in HTML
    assert f'"project/release-checklist": "{HELP}"' in HTML
    assert f"<!-- help-id: {HELP} -->" in HELP_REF

def test_saved_via_partial_update_and_fields():
    assert 'saveProjectSection("release-checklist"' in HTML
    for token in ('"off"', '"advisory"', '"strict"', "precondition", "applies-when",
                  "must be side-effect free", "Prompt convention only", "gates stay hard in every mode"):
        assert token in HTML

def test_script_field_only_for_script_check_and_no_execution():
    assert "item-script" in HTML and "/api/exec" not in HTML

def test_help_mappings_checker_clean():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.consistency.docs import check_ui_help_mappings
    assert [f.message for f in check_ui_help_mappings(REPO_ROOT) if HELP in f.message] == []
```
- [x] **Step 2: Run -> FAIL** (`assert 'async function viewProjectReleaseChecklist(' in HTML`): `python3 -m pytest tests/test_admin_ui_release_checklist_section.py --basetemp="$PYTEST_BASETEMP"`
- [x] **Step 3: Implementierung**: Nav-Eintrag `{ route: "/project/release-checklist", label: "Release Checklist", icon: "☑" }` nach Auto-Commit; View nach dem Muster `viewProjectAutoCommit`: `mode`-Dropdown (Hilfetext "Prompt convention only, no hook; gates stay hard in every mode"), Items-Tabelle mit Add/Edit/Delete über `showModal` (Felder id, task, verification, check, script [Feld `id="item-script"` nur sichtbar bei `check == "script"`, Hinweis "must be side-effect free"], phase, required, applies-when); Speichern sendet `mode` immer als String und nur gesetzte Keys; clientseitiges Gate: `check == "script"` ohne `script` => `setError`. Help-Block mit `help-id`, `last-updated`, `author` wie die Nachbarn. Keine Skript-Ausführung aus der UI.
- [x] **Step 4: Run -> PASS**; `python3 -m pytest tests/test_admin_ui_git_section.py --basetemp="$PYTEST_BASETEMP"` (Nachbarn grün).
- [x] **Step 5: Commit**
`git add docs/ui/admin-ui.html docs/api/admin-ui-reference.md tests/test_admin_ui_release_checklist_section.py`
`git commit -m "feat: add release checklist section to admin ui"`

### Task 9: Szenarien 88-90

**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `tests/scenarios/registry.md` (3 Zeilen am Ende der Katalog-Tabelle nach `79-opencode-v2-full-surface`, :126; die losen Zeilen :162-170 bleiben unberührt)
- Create: `tests/scenarios/configs/88-release-checklist-off.project.yaml`
- Create: `tests/scenarios/configs/89-release-checklist-advisory.project.yaml`
- Create: `tests/scenarios/configs/90-release-checklist-strict.project.yaml`
- Create: `tests/scenarios/asserts/88-release-checklist-off.sh`
- Create: `tests/scenarios/asserts/89-release-checklist-advisory.sh`
- Create: `tests/scenarios/asserts/90-release-checklist-strict.sh`

**Interfaces:**
- Consumes: `tests/scenarios/run.sh` (cwd = Temp-Projekt, `$1`/`REPO_ROOT` = Checkout; Assert nur wenn ausführbar); Config-Vorlage `configs/87-project-description.project.yaml` mit `roles: [orchestrator, developer, git, release]`.
- Produces: Szenarien `88-release-checklist-off`, `89-release-checklist-advisory`, `90-release-checklist-strict`.

- [x] **Step 1: Failing Test** — Configs und Asserts anlegen (Asserts wie `asserts/87-project-description.sh`, `fail()`-Helfer, `chmod +x`):
  - 88: Config mit `release-checklist: {mode: "off"}`; Assert: `.claude/agents/release.md` enthält weder `CHECKLIST_MODE` noch `RELEASE_CHECKLIST`; zweiter Sync in `mktemp -d` mit derselben Config ohne den `release-checklist`-Block und `cmp` der beiden `release.md` => identisch (AC-REL-1).
  - 89: `mode: "advisory"` + Items `changelog-unreleased` (agent), `schema-valid` (script `python3 scripts/sync.py --validate`), `docker-image-pushed` (`phase: step`, `required: false`, `applies-when`); Assert: `grep -q` auf `CHECKLIST_MODE`, `APPROVAL_REQUEST`, `APPROVED:`, `n/a (nicht ausgeführt)`, alle drei Item-IDs, kein `{{`.
  - 90: `mode: "strict"` + ein Item; Assert: `Prompt-/Konventions-Boundary`, `required_failed`, `STATUS: failed`, Item-ID.
  - Registry-Zeilen im Format der Katalog-Tabelle: `| \`88-release-checklist-off\` | Claude | strict (default) | <Feature> |` (analog 89, 90).
  - Erste Fassung von Assert 90 enthält bewusst die falsche Phrase `Sicherheitsgarantie`, damit der Fail beobachtet wird.
- [x] **Step 2: Run -> FAIL**: `tests/scenarios/run.sh 88 89 90` — erwartet `FAIL  90-release-checklist-strict` (assert), 88/89 `PASS`.
- [x] **Step 3: Implementierung**: Assert 90 auf die echte Phrase `Prompt-/Konventions-Boundary` korrigieren.
- [x] **Step 4: Run -> PASS**: `tests/scenarios/run.sh 88 89 90` (3x `PASS`); danach `tests/scenarios/run.sh` komplett (AC-REL-18, Regression).
- [x] **Step 5: Commit**
`git add tests/scenarios/registry.md tests/scenarios/configs tests/scenarios/asserts`
`git commit -m "test: add release-checklist scenarios 88-90"`

### Task 10: Doku und CHANGELOG

**Agent:** documenter
**Depends on:** 8, 9
**Files:**
- Modify: `docs/RELEASE_GATES.md` (neuer Abschnitt `## Checklist-Modus` nach "Projekt-eigene Pre-Release-Checkliste" :511-531)
- Modify: `README.md` (Englisch; Abschnitt zur Release-Checkliste/`custom_checklist`)
- Modify: `howto/configs/project.yaml.example` (auskommentiertes Beispiel nahe `release-gates` :77-91)
- Modify: `CHANGELOG.md` (`## [Unreleased]` -> `### Added`)
- Modify: `tests/test_release_checklist_texts.py`

**Interfaces:**
- Consumes: Verhalten aus Tasks 1-9.
- Produces: Abschnitt "Checklist-Modus" in `docs/RELEASE_GATES.md`.

- [x] **Step 1: Failing Tests** (Ergänzung)
```python
def test_release_gates_doc():                                               # AC-REL-20
    t = (REPO_ROOT / "docs/RELEASE_GATES.md").read_text(encoding="utf-8")
    sec = t.split("## Checklist-Modus", 1)[1]
    for phrase in ("off", "advisory", "strict", "Gates bleiben in jedem Modus hart", "seiteneffektfrei",
                   "Prompt-/Konventions-Boundary", "--release-check", "Hook", "access: read"):
        assert phrase in sec, phrase

def test_changelog_and_example():
    cl = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split("## [2.0.0-beta.5]", 1)[0]
    assert "release-checklist" in cl and "advisory" in cl and "strict" in cl and "Prompt" in cl
    assert "release-checklist:" in (REPO_ROOT / "howto/configs/project.yaml.example").read_text(encoding="utf-8")
```
- [x] **Step 2: Run -> FAIL** (`IndexError`): `python3 -m pytest tests/test_release_checklist_texts.py::test_release_gates_doc tests/test_release_checklist_texts.py::test_changelog_and_example --basetemp="$PYTEST_BASETEMP"`
- [x] **Step 3: Implementierung**: `## Checklist-Modus` (Deutsch): Modi, Beispiel §9.1, Phasen-Klassen, Freigabeprotokoll, Dry-Check (`/release-check`), Hinweise "Gates bleiben in jedem Modus hart" und "Skript-Items müssen seiteneffektfrei sein" (laufen auch im Dry-Check; Vertrauensstufe wie `TEST_COMMANDS`, keine Allowlist), "strict = Prompt-/Konventions-Boundary, kein Hook", Folge-Optionen F1 (harter Hook) und F2 (`sync.py --release-check`), und genau ein Satz: "Ein Dry-Check gegen eine Test-Umgebung führt nur Aktionen mit `access: read` aus (Anforderung aus Spec 2, AC-ENV-19)." README-Absatz (Englisch), Beispiel-Block, CHANGELOG-Eintrag unter `### Added` (Englisch wie die Nachbarn).
- [x] **Step 4: Run -> PASS**; `python3 scripts/consistency-check.py --changed` (Placeholder-Check meldet keine ungeescapten `{{RELEASE_CHECKLIST_*}}`-Beispiele).
- [x] **Step 5: Commit**
`git add docs/RELEASE_GATES.md README.md howto/configs/project.yaml.example CHANGELOG.md tests/test_release_checklist_texts.py`
`git commit -m "docs: document release-checklist mode and dry-check"`

### Task 11: Rebaseline und Standalone-Export

**Agent:** senior-developer
**Depends on:** 10
**Files:**
- Modify: `tests/fixtures/ac01-baseline/hashes.json` (nur betroffene Einträge)
- Modify: `tests/test_ac01_render_identity.py` (Rebaseline-Log im Docstring)
- Modify: `tests/test_opencode_v2_surface.py` (AC-T4-Digest folgt `hashes.json`)
- Modify: `tests/fixtures/slimming-golden/agent-meta-manager.md`
- Modify: `standalone/agents/release.md`
- Modify: `standalone/agents/agent-meta-manager.md`
- Modify: `standalone/README.md` (falls der Export-Test es verlangt)
- Modify: `.meta-config/generated-file-hashes.json`

**Interfaces:**
- Consumes: Guard-Tests `tests/test_ac01_render_identity.py`, `tests/test_template_slimming_equivalence.py`, `tests/test_standalone_export_in_sync.py`, `tests/test_context_budgets.py`, `tests/test_opencode_v2_surface.py`; Regeln "Praxis-Hinweise" in `rules/2-platform/agent-meta-conventions.md`.
- Produces: grüne Guard-Tests; nur Einträge bewegt, die durch neue Commands, Manager 1.26.0 und Template-Versionen betroffen sind; `AC01_EXCEPTIONS` bleibt unverändert.

- [x] **Step 1: Failing Tests** — Ist-Zustand erfassen: `python3 -m pytest tests/test_ac01_render_identity.py tests/test_template_slimming_equivalence.py tests/test_standalone_export_in_sync.py tests/test_context_budgets.py tests/test_opencode_v2_surface.py --basetemp="$PYTEST_BASETEMP"`; Liste der roten Tests und bewegten Pfade notieren.
- [x] **Step 2: Run -> FAIL erwartet** für mindestens `test_ac01_render_identical_to_manifest` (Provider-Command-Renders `release-check`/`set-release-checklist`, Manager-Artefakte) und den Standalone-/Slimming-Vergleich; ein roter Test ohne Bezug zu dieser Änderung wird nicht rebaselined, sondern gemeldet.
- [x] **Step 3: Implementierung**: `python3 scripts/sync.py --render-standalone`; `slimming-golden/agent-meta-manager.md` aus dem gerenderten Manager neu erzeugen; `hashes.json` Eintrag für Eintrag aus den gerenderten Bytes nachziehen (Vorgehen laut Rebaseline-Log "Issue #1055": per Entry patchen, Digest mit `_hash_file` des Harness nachrechnen; `--write` nur auf sauberem `main`); AC-T4-Digest in `test_opencode_v2_surface.py` neu berechnen; Rebaseline-Log-Eintrag im Docstring von `test_ac01_render_identity.py` (Begründung: neue Commands, Manager 1.26.0, release-Template-Versionen; X von N Hashes bewegt; `AC01_EXCEPTIONS` NICHT erweitert); `python3 scripts/sync.py` auf agent-meta selbst nur, falls `--check` rot ist (aktualisiert `generated-file-hashes.json`).
- [x] **Step 4: Run -> PASS**: dasselbe Kommando wie Step 1; zusätzlich `python3 scripts/sync.py --check` und `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.
- [x] **Step 5: Commit**
`git add tests/fixtures tests/test_ac01_render_identity.py tests/test_opencode_v2_surface.py standalone .meta-config/generated-file-hashes.json`
`git commit -m "test: rebaseline render fixtures for release-checklist"`

### Task 12: Self-Review der Gesamtänderung und PR-Vorbereitung

**Agent:** code-reviewer
**Depends on:** 11
**Files:**
- Modify: `docs/plans/2026-10-31-release-checklist-plan.md` (Checkboxen, Status `complete`)

**Interfaces:**
- Consumes: gesamter Diff `main...feat/release-checklist`, Tabelle "Spec Coverage" (unten).
- Produces: PR-Beschreibungstext (Rückgabe an den Aufrufer; Push/PR-Erstellung durch den `git`-Agenten, kein Merge).

- [x] **Step 1: Volllauf** — `python3 -m pytest tests/ --basetemp="$PYTEST_BASETEMP"`, `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`, `python3 scripts/consistency-check.py --all`, `tests/scenarios/run.sh`. Erwartung: alles grün; jede Abweichung wird als Befund an den besitzenden Task zurückgegeben statt hier zu fixen.
- [x] **Step 2: Diff-Review gegen Constraints** — `git diff --stat main...HEAD`: `wc -l scripts/lib/release_checklist.py` <= 600; `git diff main...HEAD -- scripts/lib/config.py scripts/lib/variables.py scripts/lib/standalone.py scripts/admin-server.py` enthält nur Aufruf-/Registrierungs-/Guard-Zeilen (AC-REL-19); `grep -n 'provider ==' scripts/lib/release_checklist.py` leer; kein Literalpfad für Basetemp in neuen Dateien (`grep -n "/tmp" tests/test_release_checklist_*.py tests/test_admin_ui_release_checklist_section.py` leer).
- [x] **Step 3: Spec-Coverage prüfen** — jede Zeile der Tabelle "Spec Coverage" gegen den benannten Test/Task abhaken; Review-Focus R1-R5: jeder genannte Test existiert und läuft grün (`python3 -m pytest tests/ -k "null_and_empty or non_list_items or whitespace_only or field_types or normalizes_false or roundtrips_as_string" --basetemp="$PYTEST_BASETEMP"`).
- [x] **Step 4: Plan abschließen** — Plan-Status auf `complete`, alle Checkboxen abhaken; PR-Text (Titel `feat: structured release checklist (off|advisory|strict)`, Zusammenfassung, Testplan, Hinweis auf Plan 2) an den Aufrufer zurückgeben.
- [x] **Step 5: Commit**
`git add docs/plans/2026-10-31-release-checklist-plan.md`
`git commit -m "docs: close out release-checklist plan"`

## Spec Coverage

| AC | Task | Nachweis |
|---|---|---|
| AC-REL-1 | 3, 4, 9 | `test_whitelist_strips_inactive_block`, `test_off_absent_and_empty_are_byte_identical`, Szenario 88 |
| AC-REL-2 | 1 | `test_invalid_mode_names_path` |
| AC-REL-3 | 1 | `test_normalize_false_only`, `test_load_config_normalizes_unquoted_off` |
| AC-REL-4 | 1 | `test_duplicate_and_reserved_ids` |
| AC-REL-5 | 1 | `test_script_check_rules`, `test_unknown_keys_and_phase` |
| AC-REL-6 | 2, 4 | `test_render_modes_contain_contract`, `test_advisory_text`, Szenario 89 |
| AC-REL-7 | 2, 4 | `test_render_modes_contain_contract`, `test_strict_text`, Szenario 90 |
| AC-REL-8 | 2, 4 | `test_strict_block_na_rules`, `test_strict_text` |
| AC-REL-9 | 2 | `test_render_script_item_row`, `REQUIRED_PHRASES` ("Exit 0 = pass", "side-effect free") |
| AC-REL-10 | 5 | `test_release_check_command` |
| AC-REL-11 | 2, 4 | `REQUIRED_PHRASES` ("MODE: check-only"), `test_advisory_text` |
| AC-REL-12 | 4 | `test_hacs_override` |
| AC-REL-13 | 7 | `test_whitelist_contains_section`, `test_invalid_payloads_rejected_without_write` |
| AC-REL-14 | 8 | `test_view_route_nav_routemap_help`, `test_help_mappings_checker_clean` |
| AC-REL-15 | 6, 7 | `test_parity_with_direct_yaml_fragment`, `test_manager_recipe` |
| AC-REL-16 | 6 | `test_manager_recipe` |
| AC-REL-17 | 3 | `test_placeholders_known_and_builder_check_clean`, `test_standalone_fallbacks`, `test_sync_concept_documents_placeholders` |
| AC-REL-18 | 9 | `tests/scenarios/run.sh 88 89 90` |
| AC-REL-19 | 2, 12 | `test_module_size_limit`, Diff-Review Step 2 |
| AC-REL-20 | 10 | `test_release_gates_doc`, `test_changelog_and_example` |
| AC-REL-21 | 1, 2, 4 | Schema-Test `phase`-Enum, `test_reserved_items_flags_and_template_rowcount`, `\| phase \|` in `REQUIRED_PHRASES` |
| AC-REL-22 | 2, 4 | `test_render_modes_contain_contract` (kein "non-blocking"), `test_gates_step0_text_unchanged` |
| AC-REL-23 | 2, 4 | `REQUIRED_PHRASES` ("APPROVAL_REQUEST", "APPROVED:"), `test_advisory_text` |
| AC-REL-24 | 2, 4 | `REQUIRED_PHRASES` ("not_run", "n/a (nicht ausgeführt)"), `test_strict_text` |
| AC-REL-25 | 2, 4 | `test_strict_block_na_rules`, `test_reserved_items_flags_and_template_rowcount`, `test_strict_text` |

## Hinweis: Plan 2 (Test-Umgebungen)

Plan 2 (`docs/specs/2026-10-31-test-environments-spec.md`) wird NACH diesem Plan ausgeführt. Gemeinsame Berührungspunkte:
- `agents/1-generic/agent-meta-manager.md`: dieser Plan setzt `1.26.0`; Plan 2 bumpt auf `1.27.0` und ergänzt sein Rezept nach 14d — keine Neuordnung von 14d.
- `docs/RELEASE_GATES.md`: Task 10 schreibt den Satz zu AC-ENV-19 ("Dry-Check gegen eine Test-Umgebung führt nur `access: read`-Aktionen aus") in den Abschnitt "Checklist-Modus"; Plan 2 verweist darauf und dupliziert ihn nicht.
- `PROJECT_WRITABLE_SECTIONS` und `docs/ui/admin-ui.html`: `saveProjectSection("environments", ...)` existiert bereits (:8700/:8748); die Zeile `"release-checklist"` bleibt von Plan 2 unberührt.
- Rebaseline (Task 11): Plan 2 rebaselined `ac01-baseline`, `slimming-golden` und Standalone-Export erneut auf dem Stand nach diesem Plan.

## Self-Review

- Spec-Coverage: AC-REL-1..25 stehen alle in der Tabelle "Spec Coverage" mit mindestens einem Task und einem benannten Test.
- Step-Scan: keine Platzhalter-Steps; Funktionskörper nur dort, wo Signatur und Test sie nicht festlegen (Renderer-Prosa ist durch `REQUIRED_PHRASES` als Inhaltsvertrag fixiert).
- Konsistenz: `collect_release_checklist_errors`/`normalize_release_checklist_mode` (Task 1) werden in Task 2 (Resolver) und Task 7 (Guard) mit identischer Signatur konsumiert; `build_release_checklist_variables` (Task 2) in Task 3; Route/Help-ID/View-Name (`/project/release-checklist`, `project_instance-release_checklist`, `viewProjectReleaseChecklist`) in Task 8 einheitlich.
- Review Focus R1-R5: je ein benannter Test im besitzenden Task (R1 Task 1/2/4, R2 Task 1/2, R3 und R4 Task 1, R5 Task 7).
- Jeder Task mappt auf genau eine Rolle; keine Dateiüberlappung innerhalb einer Parallelgruppe, da der Plan linear ist (geteilte Testdateien in 5/6 und 7/8 erzwingen die Reihenfolge).
- Proportion: Plan kleiner als die Spec; Task-Größen entsprechen Spec §20 (WP1-WP7 plus Rebaseline- und Review-Task).

---

## Ausführungsnachweis (Ledger)

### Task → Commit

| Task | Commit | Gegenstand |
|---|---|---|
| T1 | `a08a3366` | Schema, Normalizer und Validator |
| T2 | `5dfd4e9c` | Resolver, Renderer und Variablen-Builder |
| T3 | `16d523eb` | Platzhalter-Registrierung |
| T4 | `2837a930` | Templates `release.md`, `hacs-release`, `sharkord-release` |
| T5 | `be75c6a9` | Commands `release-check` und `set-release-checklist` |
| T6 | `77238a8b` | `agent-meta-manager`-Rezept 14d |
| T7 | `f5a6f2c6` | Admin-Server-Whitelist und Section-Guard |
| T8 | `95ea2666` | Admin-UI-Sektion, Router, Help |
| T9 | `201d5913` | Szenarien 88-90 |
| T10 | `3e18202` | Doku und CHANGELOG |
| T11 | `97138b28` | Rebaseline und Standalone-Export |
| T12 | dieser Commit (`docs: close out release-checklist plan`) | Self-Review der Gesamtänderung und PR-Vorbereitung |
| Review-Follow-up (blocking + Validator-Härtung + 2 Doku-Korrekturen) | `ed4964f8` | Phase-Default `precondition` im Admin-UI, Validator-Härtung |
| Review-Follow-up (YAML-Bool-Formulierung im Setup-Command + 7-Einträge-Rebaseline) | `9b03315c` | Setup-Command-Wortlaut, Rebaseline |

### Nachweise

- Feature-Suiten: 56 passed.
- `tests/test_admin_server.py`: 140 passed.
- Szenarien: 91/91 passed.
- AC-01 / opencode / slimming / compact: 265 + 135 passed an ihren jeweiligen Messpunkten.
- `python3 scripts/sync.py --validate`: Exit 0.
- `scripts/consistency-check.py` (ohne Flag, siehe Abweichung 4): PASS.
- AC-01-Rebaseline: 45 Einträge in T11 (31 geändert + 14 neu), weitere 7 Einträge beim Wortlaut-Fix — jeweils per Entry, kein `--write`, `AC01_EXCEPTIONS` unverändert.

### Abweichungen vom Plan

- AC-01-Drift in T11 betrug **45** Einträge (31 geändert + 14 neu), nicht die 9 vor T5/T6 gemessenen — die Command- und Manager-Renders waren enthalten.
- Zwei berührte Dateien standen nicht in den per-Task-Files-Listen, waren aber für das Slimming-Gate nötig: `tests/fixtures/slimming-golden/release.md` und §19 des Diff-Manifests — der Plan hat sie unter-spezifiziert (siehe Nachtrag oben).
- Der Wortlaut-Fix an `/set-release-checklist` erforderte eine Rebaseline von 7 Einträgen (durch den Auftraggeber autorisiert), die zusätzlich den `ac01-baseline`-Tree-Digest in `tests/test_opencode_v2_surface.py` neu festgezogen hat.
- Task 12 nennt in Step 1 `scripts/consistency-check.py --all`, ein Flag, das die CLI nicht besitzt — verwendet wurde der Aufruf ohne Flag.
- Task 10 wurde von der Rolle `documenter` entworfen; diese hat in dieser Runtime keine Shell, daher hat ein `developer` die Arbeit verifiziert und committet.
