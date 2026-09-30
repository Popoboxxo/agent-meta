---
pipeline_stages:
  implement: 1
---

# Implementierungsplan — Konfigurierbare Progress-/Checkpoint-Pfade

> Status: geplant

**Spec:** `docs/specs/2026-09-13-progress-paths-config-design.md`

> Trace-Anker: `spec-id: SPEC-PROGRESS-PATHS-CONFIG-2026-09-13` (Status APPROVED)
> Verwandte Spec: `SPEC-PROGRESS-LEDGER-2026-09-13` — Checkpoint-Identität, `.meta-viz`-Default-Layout und Read/Write-Verdrahtung bleiben; ersetzt wird nur die direkte Konstruktion an den vier IC-04-Callsites.

**Goal:** Den hartcodierten Progress-/Checkpoint-Speicherort über einen neuen Top-Level-`progress:`-Block in `.meta-config/project.yaml` konfigurierbar machen — über einen findings-statt-Exceptions-Resolver, einen rückwärtskompatiblen `CheckpointStore.from_config`-Factory und die Migration aller vier Produktions-Callsites, bei byte-identischen Defaults ohne `progress:`-Block.
**Architecture:** Vorbild ist `scripts/lib/repo_containment.py::resolve_effective_repo_containment` + `tmp_sink_path_error` (Default-plus-Override, Findings, Traversal-validierter Pfad) und `scripts/lib/recovery.py::_load_project_config` (`SyncError`/`OSError` → `{}`). Ein neues Leaf-Modul `scripts/lib/progress_paths.py` besitzt Defaults und Auflösungslogik und importiert ausschließlich Stdlib plus `from .io import SyncError, _load_yaml_or_json` (kein Import von `checkpoint`, kein Zyklus). `CheckpointStore` bekommt injizierte Pfade statt Modulkonstanten; `from_config` bündelt die Auflösung; die vier Callsites lesen und schreiben dadurch dieselben Verzeichnisse (kein Split-Brain). Der provider-scoped Key `checkpoint_dir` wird nie konsultiert (Option b, Ratchet unverändert).
**Tech Stack:** Python 3.9 (Stdlib only, `from __future__ import annotations`, `typing.Optional`/`Tuple`/`List`, keine PEP-604-Union-Annotationen), JSON Schema (`config/project-config.schema.json`), Markdown/YAML, pytest, Bash-Szenario-Harness (`tests/scenarios/run.sh`).

## Global Constraints

- **Verdrahten statt erfinden:** `CheckpointStore`, `_load_yaml_or_json`, das `tmp_sink_path_error`-Validierungsmuster und `doc/consistency`-Konventionen werden genutzt und erweitert. Kein zweiter Fortschritts-Speicherort, keine zweite ID-Vergabe, kein neues CLI-Flag.
- **Byte-identische Defaults:** Ohne `progress:`-Block müssen Pfade und Dateiinhalte exakt `.meta-viz/progress/current.md` und `.meta-viz/checkpoints/<session>.json` bleiben; die bestehende Testsuite läuft unverändert grün (AC-07).
- **Provider-Agnostik:** Kein Provider-Literal und kein `if provider == …` in neuen/geänderten Modulen; der vestigiale Provider-Key `checkpoint_dir` wird an keiner Stelle gelesen, `tests/test_provider_hooks_config.py` bleibt unverändert.
- **Py3.9 & Stdlib:** Neue Module nutzen `from __future__ import annotations`; keine externen Abhängigkeiten; `scripts/consistency-check.py` (Py3.9-Union-Check) muss rc 0 liefern.
- **Findings statt Exceptions:** Der Resolver wirft nie und beendet nie; jeder ungültige Wert fällt auf den Framework-Default zurück und emittiert höchstens eine `warning`-Finding.
- **Traversal-Sicherheit:** Konfigurierte Pfade bleiben unter `project_root`; die bestehende Session-ID-Confinement in `_session_file`/`_session_raw_dir` gilt für ein benutzerdefiniertes Checkpoint-Verzeichnis unverändert weiter.
- **Datei-Ownership je Task:** Jede Datei wird in genau einer Task angelegt/geändert; die Reihenfolge ist streng abhängigkeitskorrekt (`Depends on` referenziert immer eine frühere Task).
- **Bite-sized & TDD:** Jede Task ist einzeln testbar und committbar (Test fail → implementieren → Test pass → Commit); kein Task ist „done" ohne beobachteten Test.
- **Namens-Verbot:** Kein externer Marken-/Referenzmodellname in Code, Doku, Kommentaren, Commit-Messages oder diesem Plan.
- **Keine Rollen-Routen:** `agents/1-generic/*` und `rules/1-generic/*` erhalten keine Route-Tabellen und keine `roleA → roleB`-Ketten; `tests/test_no_role_routes_in_templates.py` bleibt unverändert grün.

## Interfaces

Neue und geänderte Symbole als `file:Symbol`. Das Leaf-Modul wird eingeführt, alle anderen genannten Symbole existieren bereits.

| Symbol | Art | Vertrag |
|---|---|---|
| `scripts/lib/progress_paths.py:DEFAULT_PROGRESS_DIR` / `DEFAULT_CHECKPOINT_DIR` | neu | `.meta-viz/progress` / `.meta-viz/checkpoints` |
| `scripts/lib/progress_paths.py:SOURCE_PROJECT` / `SOURCE_DEFAULT` / `SOURCE_SAFE_FALLBACK` | neu | `"project"` / `"default"` / `"safe-fallback"` |
| `scripts/lib/progress_paths.py:ProgressPathFinding` | neu | `@dataclass(level: str, code: str, message: str)` |
| `scripts/lib/progress_paths.py:ResolvedProgressPaths` | neu | `@dataclass(progress_dir: Path, checkpoint_dir: Path, progress_rel: str, checkpoint_rel: str, progress_source: str, checkpoint_source: str, findings: Tuple[ProgressPathFinding, ...])` |
| `scripts/lib/progress_paths.py:resolve_progress_paths` | neu | `(project_root: Path, config: Optional[dict] = None) -> ResolvedProgressPaths` |
| `scripts/lib/progress_paths.py:progress_path_error` | neu | `(path: object, project_root: Optional[Path] = None) -> Optional[str]` |
| `scripts/lib/checkpoint.py:CheckpointStore.__init__` | geändert | `(project_root=None, agent_meta_root=None, progress_dir=None, checkpoint_dir=None)` |
| `scripts/lib/checkpoint.py:CheckpointStore.from_config` | neu | `@classmethod (project_root, config=None, agent_meta_root=None) -> "CheckpointStore"` |
| `scripts/lib/checkpoint.py:CheckpointStore.progress_dir` | neu | absolutes `Path`-Attribut; `checkpoint_dir` behält Name/Semantik |
| `scripts/lib/checkpoint.py:_write_progress_file` | geändert | schreibt `<progress_dir>/current.md` statt `project_root / _PROGRESS_DIR / current.md` |
| `scripts/lib/checkpoint.py:CHECKPOINT_DIR` / `_PROGRESS_DIR` | geändert | Kompatibilitäts-Aliase auf `DEFAULT_CHECKPOINT_DIR` / `DEFAULT_PROGRESS_DIR` |
| `config/project-config.schema.json:progress` | neu | Top-Level-Objekt `{dir?, checkpoint-dir?}`, beide `string`, `additionalProperties: false` |

## File Structure

### Neue Dateien

- Create: `scripts/lib/progress_paths.py` — Leaf-Modul: Defaults, Findings-Dataclasses, Traversal-Validator, Resolver.
- Create: `tests/test_progress_paths.py` — Resolver-Unit-Tests inkl. Provider-Agnostik-/Py3.9-Guard.
- Create: `tests/test_checkpoint_paths.py` — Store-Pfadinjektion, `from_config`, Progress-Write-Confinement, Default-Regression.
- Create: `tests/test_progress_paths_call_sites.py` — Spy-basierte Callsite-Prüfung plus Split-Brain-Round-Trip.
- Create: `tests/scenarios/configs/60-progress-paths-config.project.yaml` — Szenario-Config mit `progress:`-Override.
- Create: `tests/scenarios/asserts/60-progress-paths-config.sh` — Default- vs. Override-Assertions (ausführbar).

### Geänderte Dateien

- Modify: `scripts/lib/checkpoint.py` — `progress_dir`-Injektion, `from_config`, `_write_progress_file`, Konstanten-Aliase.
- Modify: `scripts/lib/checkpoint_record.py` — Callsite bei `:83` auf `CheckpointStore.from_config(project_root, config)`.
- Modify: `scripts/lib/rehydrate.py` — Callsite bei `:71` auf `CheckpointStore.from_config(project_root, config)`.
- Modify: `scripts/lib/recovery.py` — `_store_for` bei `:363` auf `CheckpointStore.from_config(project_root)`.
- Modify: `scripts/lib/consistency/ledger_drift.py` — `_store` bei `:154` auf `CheckpointStore.from_config(project_root)`.
- Modify: `config/project-config.schema.json` — `progress`-Block nach `repo_containment`, vor dem schließenden `},` der Root-`properties`.
- Modify: `tests/test_spec_plan_config_schema.py` — Akzeptanz-/Reject-Fälle für den `progress`-Block.
- Modify: `tests/test_checkpoint_cli.py` — test stub adapted to `CheckpointStore.from_config` (call-site migration).
- Modify: `tests/scenarios/registry.md` — Zeile `60-progress-paths-config`.
- Modify: `snippets/orchestrator/checkpointing.md` — Pfadangaben als konfigurierbar dokumentieren, Default-Literal erhalten.
- Modify: `rules/1-generic/plan-ledger.md` — checkpoint-Wurzel als konfigurierbar kennzeichnen.
- Modify: `rules/1-generic/session-recovery.md` — Checkpoint-Speicherort als konfigurierbar kennzeichnen.
- Modify: `docs/api/cli-reference.md` — beide `.meta-viz/...`-Nennungen um den Override-Hinweis ergänzen.
- Modify: `tests/test_progress_file_documented.py` — Override-Dokumentation als Testfall ergänzen.

### Step-Agent-Map (plan-driven `implement`)

| Step | Task | Agent |
|------|------|-------|
| 1 | Resolver-Modul `progress_paths` | developer |
| 2 | Store-Pfadinjektion und `from_config` | senior-developer |
| 3 | Produktions-Callsites auf den Config-Factory | developer |
| 4 | Schema-Block `progress` | developer |
| 5 | Szenario 60 | developer |
| 6 | Doku-Referenzen | developer |
| 7 | Vollständiges Verifikations-Gate | developer |

---

### Task 1: Resolver-Modul `progress_paths`

**Files:**
- Create: `scripts/lib/progress_paths.py`
- Test: `tests/test_progress_paths.py`

**Interfaces:** (Produces / Consumes)
- Produces: alle in `## Interfaces` genannten Symbole aus `scripts/lib/progress_paths.py`; Finding-Codes `progress.not-mapping`, `progress.dir-type`, `progress.checkpoint-dir-type`, `progress.dir-traversal`, `progress.dir-invalid`, `progress.checkpoint-dir-traversal`, `progress.checkpoint-dir-invalid`.
- Consumes: Stdlib `dataclasses`, `os`, `re`, `pathlib.Path`, `typing.Optional`/`Tuple`/`List`/`Dict`; `from .io import SyncError, _load_yaml_or_json`.

**Agent:** developer
**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_progress_paths.py::test_default_resolution` (AC-01: `progress_rel == ".meta-viz/progress"`, `checkpoint_rel == ".meta-viz/checkpoints"`, beide unter `project_root`, Quellen `default`, keine Finding), `::test_progress_dir_override` (AC-02), `::test_checkpoint_dir_override` (AC-03), `::test_partial_override_is_independent` (AC-04), `::test_non_string_type_falls_back_with_finding` (AC-05, parametrisiert `int`/`list`/`dict`; erwartet Framework-Default, Quelle `safe-fallback`, Finding-Code `progress.dir-type` bzw. `progress.checkpoint-dir-type`, kein Raise), `::test_empty_or_whitespace_resolves_to_default_without_finding` (AC-05: `""`, `"   "`, `"\t"` → Quelle `default`, keine Finding), `::test_progress_block_not_mapping_falls_back` (IC-02), `::test_traversal_values_rejected` (AC-06, parametrisiert absoluter Pfad, `C:`-Laufwerkspfad, `.`, `..`, `a/../..`, `x/../../escape`; je `*-traversal`/`*-invalid`-Finding, Framework-Default, kein Pfad außerhalb `project_root`), `::test_config_none_best_effort_load` (IC-02: Fixture `tmp/.meta-config/project.yaml` mit `progress:`-Block wird gelesen), `::test_unreadable_or_non_mapping_config_never_raises`, `::test_no_provider_literals_and_py39_syntax` (AC-11/AC-12: Quelltext enthält kein Provider-Literal, kein `if provider ==`, `from __future__ import annotations` vorhanden, keine PEP-604-Union-Annotation).
- [ ] Step 2: Implementieren — Modul-Docstring; `from __future__ import annotations`; Konstanten und Dataclasses exakt wie im Interface-Vertrag. `resolve_progress_paths`-Algorithmus: (a) `root = Path(project_root)`; (b) `config is None` → best-effort `_load_yaml_or_json(root/".meta-config"/"project.yaml", root/".meta-config"/"project.json")`, `except (SyncError, OSError)` → `{}`, Nicht-Dict → `{}`; (c) `progress` fehlt oder ist `None` → leerer Block; `progress` nicht-Mapping → Finding `progress.not-mapping` (level `warning`) und beide Pfade als `safe-fallback`; (d) je Schlüssel: fehlend → Default/`default`; nicht-`str` → Default/`safe-fallback` + `progress.<key>-type`; `str` mit `strip() == ""` → Default/`default` ohne Finding; sonst `progress_path_error(raw, root)` prüfen → bei Fehler Default/`safe-fallback` + `progress.<key>-traversal` bzw. `progress.<key>-invalid`; sonst Projektwert/`project`. (e) Gültige Werte: `\` → `/`, `os.path.normpath`, `os.path.abspath(os.path.join(str(root), norm))`, `progress_rel`/`checkpoint_rel` als `Path(norm).as_posix()`. (f) `progress_path_error` implementiert exakt die sechs IC-02-Regeln (String; nicht leer/whitespace; relativ ohne `os.path.isabs`, kein `^[A-Za-z]:`; nicht `.`/`..`, kein `..`-Segment nach `\`→`/`; `normpath` nicht leer/`.`/`..`/`..<sep>`-Präfix; bei gegebenem `project_root` muss `os.path.commonpath([abspath(root), target]) == abspath(root)` gelten, `ValueError` = Verstoß) und gibt `None` bei Gültigkeit zurück. Kein `raise`, kein `sys.exit` (AC-11/AC-12).
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_progress_paths.py -q` → rc 0.
- [ ] Step 4: Commit — `feat: add configurable progress path resolver`.

**Acceptance:** AC-01, AC-02, AC-03, AC-04, AC-05, AC-06, AC-11, AC-12.

---

### Task 2: Store-Pfadinjektion und `from_config`

**Files:**
- Modify: `scripts/lib/checkpoint.py`
- Test: `tests/test_checkpoint_paths.py`

**Interfaces:** (Produces / Consumes)
- Produces: `CheckpointStore.__init__(project_root=None, agent_meta_root=None, progress_dir=None, checkpoint_dir=None)`; `@classmethod CheckpointStore.from_config(project_root, config=None, agent_meta_root=None)`; neues Attribut `self.progress_dir`; `_write_progress_file` nutzt `self.progress_dir / "current.md"`; Konstanten-Aliase `CHECKPOINT_DIR`/`_PROGRESS_DIR`.
- Consumes: `progress_paths.DEFAULT_PROGRESS_DIR`, `progress_paths.DEFAULT_CHECKPOINT_DIR`, `progress_paths.resolve_progress_paths`.

**Agent:** senior-developer
**Depends on:** 1

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_checkpoint_paths.py::test_default_constructor_is_byte_identical` (AC-07: `CheckpointStore(project_root=tmp)` schreibt Session-JSON nach `.meta-viz/checkpoints/<session>.json` und `current.md` nach `.meta-viz/progress/current.md`; `current.md`-Inhalt entspricht dem Voränderungs-Rendering), `::test_two_argument_constructor_backward_compatible` (AC-07), `::test_from_config_honours_both_overrides` (AC-08: `.run/progress` und `.run/checkpoints`, nichts unter `.meta-viz`), `::test_write_progress_file_confined_to_progress_dir` (IC-03 Defense-in-Depth: kein Schreiben außerhalb von `self.progress_dir`), `::test_custom_checkpoint_dir_keeps_session_confinement` (Traversal bleibt über `_session_file` abgewiesen), `::test_module_aliases_point_to_new_defaults`.
- [ ] Step 2: Implementieren — am Modulkopf `from .progress_paths import DEFAULT_CHECKPOINT_DIR, DEFAULT_PROGRESS_DIR, resolve_progress_paths` ergänzen; `CHECKPOINT_DIR = DEFAULT_CHECKPOINT_DIR` und `_PROGRESS_DIR = DEFAULT_PROGRESS_DIR` als deprecatete Kompatibilitäts-Aliase belassen (Docstring-Hinweis, keine Quelle der Wahrheit mehr). `__init__` um `progress_dir` und `checkpoint_dir` erweitern: bei `None` jeweils `self.project_root / DEFAULT_CHECKPOINT_DIR` bzw. `self.project_root / DEFAULT_PROGRESS_DIR`, bei explizitem Wert `Path(...)` unverändert als absoluten Pfad übernehmen (nicht erneut an `project_root` joinen); `project_root`/`agent_meta_root`/`checkpoint_dir` behalten Name und Semantik. `from_config` ruft `resolve_progress_paths(Path(project_root), config)` und konstruiert `cls(project_root=..., agent_meta_root=..., progress_dir=resolved.progress_dir, checkpoint_dir=resolved.checkpoint_dir)`. In `_write_progress_file` `self.project_root / _PROGRESS_DIR / "current.md"` durch `self.progress_dir / "current.md"` ersetzen und der Schreibpfad vor dem Schreiben mit `resolve()` + `relative_to(self.progress_dir.resolve())` absichern; bei Verstoß nicht außerhalb schreiben.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_checkpoint_paths.py tests/test_progress_file.py tests/test_progress_file_migration.py tests/test_checkpoint_raw_output.py tests/test_persistence_atomicity.py -q` → rc 0.
- [ ] Step 4: Commit — `feat: inject resolved progress paths into CheckpointStore`.

**Acceptance:** AC-07, AC-08, AC-15.

---

### Task 3: Produktions-Callsites auf den Config-Factory umstellen

**Files:**
- Modify: `scripts/lib/checkpoint_record.py`
- Modify: `scripts/lib/rehydrate.py`
- Modify: `scripts/lib/recovery.py`
- Modify: `scripts/lib/consistency/ledger_drift.py`
- Test: `tests/test_progress_paths_call_sites.py`

**Interfaces:** (Produces / Consumes)
- Produces: `checkpoint_record.handle_checkpoint` (Schreibpfad) konstruiert `CheckpointStore.from_config(project_root, config)`; `rehydrate.handle_rehydrate` (Lesepfad) konstruiert `CheckpointStore.from_config(project_root, config)`; `recovery._store_for(project_root, store)` liefert bei `store is None` `CheckpointStore.from_config(project_root)`; `consistency.ledger_drift._store(project_root)` liefert `CheckpointStore.from_config(project_root)`.
- Consumes: `CheckpointStore.from_config` aus Task 2; `resolve_progress_paths`-Override-Semantik.

**Agent:** developer
**Depends on:** 2

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_progress_paths_call_sites.py::test_checkpoint_record_uses_from_config`, `::test_rehydrate_uses_from_config`, `::test_recovery_store_for_uses_from_config`, `::test_ledger_drift_store_uses_from_config` (jeweils Spy-Monkeypatch auf `lib.checkpoint.CheckpointStore.from_config`, der Aufruf und Argumente protokolliert und einen realen Store zurückgibt) sowie `::test_no_split_brain_write_then_read_with_override` (AC-09: mit `progress:`-Override schreibt `handle_checkpoint` unter die Override-Verzeichnisse und `recovery`/`rehydrate` lesen dieselbe Session; nichts landet unter `.meta-viz`).
- [ ] Step 2: Implementieren — `scripts/lib/checkpoint_record.py`: `CheckpointStore(project_root=project_root)` → `CheckpointStore.from_config(project_root, config)`. `scripts/lib/rehydrate.py`: gleiches Muster mit dem bereits vorhandenen `config`. `scripts/lib/recovery.py::_store_for`: `CheckpointStore(project_root=project_root)` → `CheckpointStore.from_config(project_root)` (kein neuer Parameter, best-effort-Load im Resolver). `scripts/lib/consistency/ledger_drift.py::_store`: analog `from_config(project_root)`. Keine neue CLI-Option, keine Signaturänderung an den Callsites.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_progress_paths_call_sites.py tests/test_checkpoint_cli.py tests/test_rehydrate_cli.py tests/test_recovery.py tests/test_spec_plan_consistency.py -q` → rc 0.
- [ ] Step 4: Commit — `refactor: route checkpoint call sites through from_config`.

**Acceptance:** AC-09, AC-15.

---

### Task 4: Schema-Block `progress`

**Files:**
- Modify: `config/project-config.schema.json`
- Test: `tests/test_spec_plan_config_schema.py`

**Interfaces:** (Produces / Consumes)
- Produces: Top-Level-Property `progress` mit `properties.dir` (`type: string`, `default: ".meta-viz/progress"`) und `properties.checkpoint-dir` (`type: string`, `default: ".meta-viz/checkpoints"`), jeweils `additionalProperties: false`; beide optional.
- Consumes: nichts (Declaration/Tippfehler-Guard; die Laufzeit-Auflösung bleibt defensiv in Task 1).

**Agent:** developer
**Depends on:** —

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_spec_plan_config_schema.py::test_progress_block_accepted` (AC-10: `_base_config(progress={"dir": ".run/progress", "checkpoint-dir": ".run/checkpoints"})` validiert), `::test_progress_partial_block_accepted`, `::test_progress_unknown_subkey_rejected` (AC-10: `additionalProperties: false` lehnt `progress={"bogus": "x"}` ab), `::test_progress_non_string_dir_rejected` (AC-10: `progress={"dir": 1}` → `ValidationError`), `::test_progress_defaults_documented_in_schema` (beide `default`-Werte sind exakt die Framework-Defaults). Die Fälle nutzen `pytest.importorskip("jsonschema")` wie die bestehenden Tests.
- [ ] Step 2: Implementieren — in `config/project-config.schema.json` nach dem schließenden `}` des letzten Top-Level-Properties `repo_containment` und vor dem `},` der Root-`properties` (aktuell Zeile 2276, direkt vor `"required"`) den `progress`-Block einfügen. Root-`additionalProperties` bleibt `true`; der neue Block selbst ist mit `additionalProperties: false` geschlossen. `description` nennt Projekt-Root-Relativität und die historischen `.meta-viz`-Defaults.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_spec_plan_config_schema.py -q` → rc 0; zusätzlich `python3 scripts/sync.py --validate` → rc 0.
- [ ] Step 4: Commit — `feat: declare progress config block in project schema`.

**Acceptance:** AC-10.

---

### Task 5: Szenario 60

**Files:**
- Create: `tests/scenarios/configs/60-progress-paths-config.project.yaml`
- Create: `tests/scenarios/asserts/60-progress-paths-config.sh`
- Modify: `tests/scenarios/registry.md`

**Interfaces:** (Produces / Consumes)
- Produces: eigenständige Consumer-Config mit aktivem `spec-plan-workflow` und einem `progress:`-Override (`.run/progress`, `.run/checkpoints`); ausführbares Assert-Script, das beide Läufe prüft — Lauf ohne `progress:` erzeugt die historischen `.meta-viz`-Pfade, Lauf mit Override erzeugt die konfigurierten Pfade; Katalogzeile `| \`60-progress-paths-config\` | Claude | strict (default) | … |`.
- Consumes: `scripts/lib/progress_paths.py` (Task 1), `CheckpointStore.from_config` (Task 2), `tests/scenarios/run.sh`-Vertrag (`cwd` = Temp-Projekt, `$1`/`REPO_ROOT` = Checkout).

**Agent:** developer
**Depends on:** 1, 2, 3, 4

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/scenarios/asserts/60-progress-paths-config.sh` mit `fail()`-Helper und `REPO_ROOT`-Prüfung anlegen; das Script erst per `chmod +x` ausführbar machen. Registry-Zeile `60-progress-paths-config` nach `59-progress-ledger` ergänzen. Auf `dry_rc=0 && sync_rc=0 && val_rc=0 && assert_rc=0` auslegen.
- [ ] Step 2: Implementieren — Config-Datei mit `progress: {dir: .run/progress, checkpoint-dir: .run/checkpoints}` und minimalem Sync-Setup. Assert-Script: `.agent-meta`-Symlink wie in `59-progress-ledger.sh` emulieren; per `python3 -` gegen `$REPO_ROOT` (a) `resolve_progress_paths(Path("."), {})` → Default-Pfade und `source == "default"`, (b) `resolve_progress_paths(Path("."), {"progress": {"dir": ".run/progress", "checkpoint-dir": ".run/checkpoints"}})` → Override-Pfade und `source == "project"`, (c) Default-Store schreibt `.meta-viz/progress/current.md` + `.meta-viz/checkpoints/<s>.json`, (d) `from_config`-Store mit Override schreibt unter `.run/` und nicht unter `.meta-viz`; jede Abweichung ruft `fail`.
- [ ] Step 3: Test (pass) — `tests/scenarios/run.sh 60` → `PASS` (rc 0); danach `tests/scenarios/run.sh` vollständig → alle `PASS`.
- [ ] Step 4: Commit — `test: add scenario 60 for configurable progress paths`.

**Acceptance:** AC-13.

---

### Task 6: Doku-Referenzen

**Files:**
- Modify: `snippets/orchestrator/checkpointing.md`
- Modify: `rules/1-generic/plan-ledger.md`
- Modify: `rules/1-generic/session-recovery.md`
- Modify: `docs/api/cli-reference.md`
- Modify: `tests/test_progress_file_documented.py`

**Interfaces:** (Produces / Consumes)
- Produces: Snippet und beide Rules dokumentieren `progress.dir`/`progress.checkpoint-dir` samt Defaults; die CLI-Referenz nennt den Checkpoint-/Progress-Speicherort nicht mehr als unveränderlich; `tests/test_progress_file_documented.py::test_configurable_paths_are_documented` prüft die neuen Hinweise in Snippet, Rules und CLI-Referenz.
- Consumes: nichts (reine Doku-Oberfläche), aber die Default-Literale `.meta-viz/progress/current.md` bzw. `.meta-viz/checkpoints` müssen in `snippets/orchestrator/checkpointing.md` erhalten bleiben (bestehender Test).

**Agent:** developer
**Depends on:** 2, 3

**Steps:**
- [ ] Step 1: Test schreiben (fail) — `tests/test_progress_file_documented.py::test_configurable_paths_are_documented` ergänzen: Snippet, `rules/1-generic/plan-ledger.md`, `rules/1-generic/session-recovery.md` und `docs/api/cli-reference.md` enthalten `progress.dir` und `progress.checkpoint-dir` sowie den Hinweis, dass `.meta-viz` nur der Framework-Default ist.
- [ ] Step 2: Implementieren — `snippets/orchestrator/checkpointing.md`: die beiden festen Pfadaussagen um den Hinweis ergänzen, dass `.meta-viz/checkpoints/<session>.json` und `.meta-viz/progress/current.md` die Defaults von `progress.checkpoint-dir` bzw. `progress.dir` sind (Default-Literale bleiben für den bestehenden Test erhalten). `rules/1-generic/plan-ledger.md`: `barrier.checkpoint_ref`-Beispiel als illustrativ kennzeichnen und die Checkpoint-Wurzel als konfigurierbar benennen. `rules/1-generic/session-recovery.md`: gleicher Hinweis für den Checkpoint-Store. `docs/api/cli-reference.md`: beide `.meta-viz/checkpoints/`-Nennungen um den Override-Hinweis ergänzen. Keine Rollen-Namen, keine Route-Sätze.
- [ ] Step 3: Test (pass) — `python3 -m pytest tests/test_progress_file_documented.py tests/test_progress_file.py tests/test_checkpointing_gating.py tests/test_no_role_routes_in_templates.py -q` → rc 0.
- [ ] Step 4: Commit — `docs: document configurable progress and checkpoint paths`.

**Acceptance:** AC-14.

---

### Task 7: Vollständiges Verifikations-Gate

**Files:**
- Test: `tests/test_progress_paths.py`, `tests/test_checkpoint_paths.py`, `tests/test_progress_paths_call_sites.py`, `tests/test_spec_plan_config_schema.py`

**Interfaces:** (Produces / Consumes)
- Produces: dokumentiertes, reproduzierbares Abnahme-Ergebnis für die gesamte Änderung; kein Produktionscode, keine neuen Dateien.
- Consumes: alle Artefakte aus Task 1 bis Task 6.

**Agent:** developer
**Depends on:** 1, 2, 3, 4, 5, 6

**Steps:**
- [ ] Step 1: Alle neuen Unit-Tests grün — `python3 -m pytest tests/test_progress_paths.py tests/test_checkpoint_paths.py tests/test_progress_paths_call_sites.py tests/test_spec_plan_config_schema.py -q` → rc 0.
- [ ] Step 2: Sync-Validierung — `python3 scripts/sync.py --validate` → rc 0 und `python3 scripts/sync.py --check` → rc 0.
- [ ] Step 3: Konsistenz inkl. Py3.9/Provider-Agnostik — `python3 scripts/consistency-check.py` → rc 0.
- [ ] Step 4: Szenario-Harness vollständig — `tests/scenarios/run.sh` → alle Szenarien `PASS` (insbesondere `46`, `47`, `48`, `59`, `60`).
- [ ] Step 5: Ratchets unverändert grün — `python3 -m pytest tests/test_no_role_routes_in_templates.py tests/test_spec_plan_group_consistency.py tests/test_provider_hooks_config.py -q` → rc 0.
- [ ] Step 6: Plan-Validierung (Ausgabe dokumentieren, **kein Pass-Gate**) — `python3 scripts/sync.py --validate-spec-plan` wird für diesen Plan ausgeführt und seine Ausgabe festgehalten. Erwarteter rc: **1**, bekannt und nicht-regressiv. Ursache ist die vorbestehende Validator-vs-Design-Inkonsistenz: `scripts/lib/orchestration.py::validate_plan` wendet den `file_overlap`-Check ohne `kind`-Gate an, sodass `spec_plan_plan_graph` auch sequenzielle Pläne mit import-/doku-gekoppelten Dateien meldet (hier 4 Findings zwischen Task 1/2/3/6). Der Design-Contract (`docs/superpowers/specs/2026-09-13-spec-plan-workflow-design.md:778`) verlangt File-Overlap-Fehler nur innerhalb einer `parallel_group`. Dies ist eine dokumentierte Limitierung des Validators, keine Code-Regression dieses Plans (Beleg: Schwesterplan `docs/plans/2026-09-13-progress-ledger-system.md` → 48 vergleichbare Findings; Repo-weit 340).
- [ ] Step 7: Commit — `test: verify configurable progress paths end to end`.

**Acceptance:** AC-01 bis AC-15 (Abnahme-Nachweis).

---

## Acceptance-Criteria → Task-Mapping

| AC | Task(s) |
|----|---------|
| AC-01 | 1 |
| AC-02 | 1 |
| AC-03 | 1 |
| AC-04 | 1 |
| AC-05 | 1 |
| AC-06 | 1 |
| AC-07 | 2 |
| AC-08 | 2 |
| AC-09 | 3 |
| AC-10 | 4 |
| AC-11 | 1, 7 |
| AC-12 | 1, 7 |
| AC-13 | 5 |
| AC-14 | 6 |
| AC-15 | 1, 2, 3, 4, 5, 7 |

## Self-Review

- **AC-Abdeckung:** Alle 15 Acceptance Criteria sind mindestens einer Task zugeordnet; kein AC ohne Task, keine Task ohne AC-Bezug.
- **Test je Task:** Jede Task besitzt einen konkreten, benannten Testfall und ein Verifikationskommando mit erwartetem rc; kein Task ist ohne beobachtbaren Test „done".
- **Traceability:** `spec-id: SPEC-PROGRESS-PATHS-CONFIG-2026-09-13` ↔ `**Spec:**`-Pfad ↔ Task-ID ↔ Testname ist durchgängig; `pipeline_stages.implement` zeigt auf Step 1 des Step-Agent-Map (Agent `developer`).
- **Interface-Vollständigkeit:** Jede Task hat nicht-leere `Produces`/`Consumes`; alle neuen Symbole sind mit Datei, Name und Signatur benannt; jede referenzierte `file:Symbol` existiert oder wird durch eine Task eingeführt.
- **Abhängigkeiten:** Der Graph ist zyklenfrei und vorwärtsgerichtet: 1 → 2 → 3, 4 unabhängig, 5 integriert 1–4, 6 hängt an 2–3, 7 schließt alles ab. Die vier IC-04-Callsites werden in genau einer Task (3) migriert, damit kein Split-Brain-Zwischenstand committet wird.
- **Datei-Ownership:** Keine Datei wird von zwei Tasks angelegt/geändert; überlappende Schreibzugriffe entfallen. Die Plan-Graph-Prüfung (`spec_plan_plan_graph`) meldet dennoch 4 File-Overlap-Findings zwischen Task 1/2/3/6 — ein bekannter False Positive des Validators: `scripts/lib/orchestration.py::validate_plan` wendet `file_overlap` ohne `kind`-Gate an und markiert daher gekoppelte Dateien (Import/Doku-Referenz) auch über korrekt sequenzielle `Depends on:`-Kanten hinweg. Dokumentierte Validator-Limitierung, keine Verletzung der Datei-Ownership.
- **Rahmenbedingungen:** Provider-agnostisch (kein Provider-Literal; `checkpoint_dir`-Ratchet unangetastet), Stdlib-only, Py3.9-konform, byte-identische Defaults, keine Rollen-Routen in `rules/1-generic/*`, keine Modellnamen.
- **No-Placeholder:** Keine Platzhalter-Marker, keine leeren Interfaces; exakte Pfade, Symbole, Signaturen, Testnamen und Commit-Messages.

## Ausführungs-Handoff

- **Reihenfolge:** Task 1 → Task 7 in aufsteigender Numerik. Task 4 ist von 1 unabhängig und darf nach Task 1 parallel zu Task 2/3 laufen; Task 5 erst nach 1–4, Task 6 nach 2–3, Task 7 zuletzt. Barrieren/Ownership kommen aus dem `Files:`-Block.
- **Task-für-Task (SDD):** Jede Task wird von einem frischen Subagenten mit frischem Kontext ausgeführt, reviewt und erst dann committet; die Ledger-Checkboxen werden nach Task-Abschluss über den Writer aktualisiert. Kein Task ohne Test und Commit.
- **Blocked-Regel:** Kann eine Task ihre Akzeptanz nicht belegen, bleibt sie offen (`- [ ]`), wird an den Orchestrator eskaliert und blockiert Nachfolger; sie wird nie stillschweigend übersprungen oder umsortiert.
- **Merge-Reihenfolge:** Der Plan teilt `checkpoint.py`, `recovery.py`, `rehydrate.py` und `checkpoint_record.py` mit der in-flight Progress-/Ledger-Spec; diese Änderung zuerst anwenden oder die Shared-File-Edits koordinieren, um Konflikte zu vermeiden.
- **Abschluss-Gate:** Vor Freigabe laufen `python3 scripts/sync.py --validate` (rc 0), `python3 scripts/sync.py --check` (rc 0), `python3 scripts/consistency-check.py` (rc 0), `tests/scenarios/run.sh` (alle `PASS`) sowie die in Task 7 genannten Ratchet-Suiten (rc 0).
