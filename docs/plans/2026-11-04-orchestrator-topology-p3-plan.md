---
pipeline_stages:
  implement: 1
status: geplant
date: 2026-11-04
base-commit: f213bcf0
trace:
  - SPEC-orchestrator-topology-2026-11-03
  - issue-1077
---

# Orchestrator-Topologie P3 (Multi-Instanz) — Implementation Plan

> Status: **Entwurf (Plan)**
>
> **Spec:** `docs/specs/2026-11-04-orchestrator-topology-spec.md`
> **Spec-ID:** `SPEC-orchestrator-topology-2026-11-03`
> **Design (Kontext):** `docs/specs/2026-11-03-orchestrator-topology-design.md` §9/§10
> **Issue:** #1077 · **Phase:** P3 (`## Phasenzerlegung`)
> **User-Entscheidungen:** **OQ-2 = A** (Sentinel-`id=` audit-only), **OQ-3 = A**
> (`max-instances` `maximum: 8`). Beide landen **nur in P3**.
> **v1-Basis:** Merge `44f39ebc`; v1 enthält P3 **nicht** (`max-instances` fehlt,
> Checkpoint-Pfade sind single-instance, die A2A-Rule hat keinen Instanz-Wortlaut).

**Goal:** P3 macht die Multiplizität des Orchestrators sicher: `orchestrator.max-instances`
(1..8, Default 1) und der presence-only Alias `orchestrator.singleton`, harte
Same-Scope-Konflikte, laute Cross-Scope-Warnung, Instanz-Identität als State-Namespace
(`<base>__<id>`, `progress-<id>.md`), envelope-/event-getaggte Audit-Daten und ein
Guard-Audit, das die optionale Sentinel-ID **nur protokolliert**. Bei N=1 (Default)
entstehen exakt die heutigen Checkpoints, Tracker- und A2A-Ausgaben.

**Architecture:** `scripts/lib/topology.py` bleibt das einzige Auflöse-Blattmodul und
erhält `resolve_orchestrator_instances()` + `compose_instance_session_id()`. Der harte
stdlib-Validator `config.py::_validate_orchestrator_topology` bekommt die Regeln (d)/(e);
`variables.py::_instance_flags` + vier fail-closed Registrierungen liefern
`ORCH_MAX_INSTANCES`/`ORCH_SINGLETON_DECLARED`; `consistency/topology.py` meldet
`singleton-redundant` (INFO) und `instances-clamped` (WARNING). `checkpoint.py` komponiert
Session-IDs ausschließlich über IC-2; `rules.py` re-resolved die effektive N pro Provider;
Guard, A2A-Schema, `delegation_syntax.py` und der Viz-Emitter tragen die Identität.
Capability-Unterschiede bleiben Daten (`orchestrator_instances.multiple`,
`topology_verified_state.multiple`), nie Provider-Namen.

**Tech Stack:** Python 3.9 (stdlib only, PyYAML als bestehende Ausnahme), pytest,
JSON-Schema (Daten, kein Validator), Markdown/YAML-Templates, Bash (Hook als Testsubjekt).

## Global Constraints

- **Python 3.9, stdlib only.** Keine neue Dependency (kein `jsonschema` als Pflicht, kein
  `pytest-timeout`); `tests/requirements.txt` bleibt unverändert. Kein `match`, keine
  PEP-604-Annotation ohne `from __future__ import annotations`.
- **Provider-agnostisch:** Unterschiede ausschließlich über
  `orchestrator_instances.multiple` / `topology_verified_state.multiple`; kein
  `if provider == "..."`, kein Provider-Namens-Literal im Auflöser.
- **Byte-Identität für N=1 ist Invariante, nicht Ergebnis.** Der Default muss heute
  reproduzieren: Checkpoint `<checkpoint-dir>/<base>.json`, Fortschritt
  `<progress-dir>/current.md`, Tracker im Kontext, A2A-Ausgabe ohne Instanzfelder.
  `sync --check` bleibt rc 0; der `{{else}}`-Zweig der A2A-Rule bleibt wortgleich.
  Nur der **explizite** Topologie-Zweig der Rule darf sich ändern (er rendert
  `ORCH_MAX_INSTANCES`).
- **Guard bleibt Convention Boundary.** Keine Enforcement-Behauptung; die Sentinel-ID ist
  **audit-only** und wird **nie** für Allow/Deny gelesen (OQ-2 = A).
- **Kein `isolation: "worktree"`.** Arbeit direkt im Projektverzeichnis.
- **Testkommando:** `python3 -m pytest <pfad> --basetemp="$PYTEST_BASETEMP"` (Basetemp
  außerhalb des Baums; `rtk pytest` ist defekt, nicht verwenden).
- **Rebaseline-Regeln:** AC-01-Baselines nur **per Eintrag** und nur für absichtlich
  geänderte Bytes; **kein** `--write`-Sammellauf; `settings.local.json` bleibt außen vor.
- **Hook-Änderung:** `# version:` bumpen (minor) **und** `# changelog:`-Zeile ergänzen.
- **Kein Merge/Push/Tag/Branch durch den Executor.** Commit pro Task, Englisch,
  Conventional Commits, ≤ 72 Zeichen, ohne BOM; vor dem Commit Secret-Scan.
- **Sprache:** Plan/Doku Deutsch, Code/Commits/Tests Englisch.

## File Structure

### Task 1 — Schema
- Modify: `config/project-config.schema.json` — `max-instances`, `singleton`, AC-12-Texte
- Modify: `tests/test_orchestrator_topology_schema.py`

### Task 2 — Validator
- Modify: `scripts/lib/config.py` — `_validate_orchestrator_topology` (d)/(e)
- Modify: `tests/test_orchestrator_topology_validator.py`

### Task 3 — Flags & Registrierungen
- Modify: `scripts/lib/variables.py` — `_instance_flags`, Whitelist, `_FALSE_DEFAULT_CONDITIONALS`
- Modify: `scripts/lib/standalone.py` — `_CONDITIONAL_FALSE_FLAGS`
- Modify: `scripts/lib/consistency/placeholders.py` — `_BUILTIN_VARS`
- Modify: `scripts/lib/config.py` — provider-lose Global-Flags in `_build_orch_variables`
- Modify: `tests/test_orchestrator_topology_flags.py`
- Modify: `tests/test_orchestrator_topology_conditionals.py`

### Task 4 — Instanz-Identität & Auflösung
- Modify: `scripts/lib/topology.py` — `resolve_orchestrator_instances`, `compose_instance_session_id`, ID-Grammatik
- Create: `tests/test_multi_instance_identity.py`

### Task 5 — Zustands-Namespaces
- Modify: `scripts/lib/checkpoint.py`
- Create: `tests/test_multi_instance_state.py`
- Modify: `tests/test_checkpoint_paths.py`

### Task 6 — Konsistenz (INFO + Clamp)
- Modify: `scripts/lib/consistency/topology.py`
- Modify: `tests/test_orchestrator_topology_consistency.py`

### Task 7 — A2A-Rule & provider-skopierte N
- Modify: `rules/1-generic/a2a-delegation-gates.md`
- Modify: `scripts/lib/rules.py`
- Create: `tests/test_a2a_instance_wording.py`

### Task 8 — Guard-Audit
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`
- Modify: `tests/test_orchestrator_guard_hook.py`

### Task 9 — Envelope, Delegation-Syntax & Viz
- Modify: `schemas/a2a-handoff.schema.json`
- Modify: `scripts/lib/delegation_syntax.py`
- Modify: `scripts/viz-logger.py`
- Create: `tests/test_multi_instance_envelope.py`
- Create: `tests/test_viz_instance_fields.py`

### Task 10 — Doku & CHANGELOG
- Modify: `docs/concepts/active/orchestrator-topology.md`
- Modify: `docs/concepts/active/singleton-orchestrator-architecture.md`
- Modify: `docs/plans/2026-11-04-orchestrator-topology-v1-plan.md`
- Modify: `tests/test_orchestrator_topology_docs.py`
- Modify: `CHANGELOG.md`

---

## Tasks

### Task 1: Schema `max-instances` / `singleton` (AC-8 Schema-Teil, AC-12)

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `tests/test_orchestrator_topology_schema.py`
**Interfaces:** Produces `orchestrator.max-instances` (`integer`, `minimum: 1`, `maximum: 8`,
`default: 1`) und `orchestrator.singleton` (`enum: [true]`, **kein** `default`); die
`description`s von `max-instances` und `max-parallel-agents` grenzen sich gegenseitig ab.
Consumes nichts.

- [ ] Step 1: Schema-Test erweitern: `max-instances` existiert mit Typ/Grenzen/Default;
  `singleton` hat `enum: [true]` und **keinen** `default`-Key; `singleton: false` wird vom
  Schema abgelehnt; beide `description`s nennen den jeweils anderen Key (AC-12);
  konsistente Config (`max-instances: 8`, `singleton: true`) validiert. Lauf:
  `python3 -m pytest tests/test_orchestrator_topology_schema.py --basetemp="$PYTEST_BASETEMP"`
  → **rot — 6 failed**.
- [ ] Step 2: Beide Properties unter `orchestrator.properties` ergänzen; `singleton` ohne
  Schema-`default`; `max-parallel-agents`-Description um „Anzahl paralleler Worker
  **innerhalb eines** Orchestrators, nicht die Anzahl Orchestratoren" erweitern. Lauf:
  → **grün — 6 passed**.
- [ ] Step 3: `python3 scripts/sync.py --validate` → **rc 0**; `max-instances: 9` und
  `singleton: false` werden vom Schema als ungültig gemeldet.
- [ ] Step 4: Commit `feat: declare multi-instance keys in project config schema`.

### Task 2: Harter Validator (d)/(e) (AC-8, AC-9, AC-17 P3)

**Agent:** senior-developer
**Depends on:** —
**Files:**
- Modify: `scripts/lib/config.py`
- Modify: `tests/test_orchestrator_topology_validator.py`
**Interfaces:** Produces die P3-Regeln in
`config.py::_validate_orchestrator_topology(config, config_path)` mit den gepinnten
Teilstrings aus IC-8; Consumes `orchestrator.max-instances` / `orchestrator.singleton`.

- [ ] Step 1: Test erweitern: `singleton` present + N>1 →
  `orchestrator.singleton conflicts with orchestrator.max-instances`;
  `singleton: false` → `orchestrator.singleton: false is not supported (use max-instances)`;
  `primary` + N>1 im selben Scope →
  `orchestrator.topology: primary conflicts with orchestrator.max-instances`;
  Negativfälle: `singleton` present + N=1 **kein** Exit, Cross-Scope (Provider-Override
  `primary` + globales N>1) **kein** Validator-Fehler. Lauf:
  `python3 -m pytest tests/test_orchestrator_topology_validator.py --basetemp="$PYTEST_BASETEMP"`
  → **rot — 6 failed**.
- [ ] Step 2: (d)/(e) nach den bestehenden (a)-(c) implementieren; `max-instances` fehlt ⇒
  N=1; `singleton`-Presence über Schlüssel-Existenz (nicht Truthiness). `singleton: false`
  wird zusätzlich zum Schema-`enum: [true]` (Warn-/Editor-Kanal) hart abgelehnt; alle
  Fehler über `_topology_error` (stderr `ERROR: <path>: …`, `sys.exit(1)`), stdlib-only.
  Lauf: → **grün — 6 passed**.
- [ ] Step 3: Subprozess-Nachweis: `sync.py` **und** `sync.py --validate` liefern für je
  eine widersprüchliche Temp-Config **rc≠0**; `singleton: true` + N=1 liefert **rc 0**.
- [ ] Step 4: Commit `feat: reject multi-instance contradictions before sync`.

### Task 3: `_instance_flags` + vier fail-closed Registrierungen (AC-8 Flags)

**Agent:** developer
**Depends on:** 2
**Files:**
- Modify: `scripts/lib/variables.py`
- Modify: `scripts/lib/standalone.py`
- Modify: `scripts/lib/consistency/placeholders.py`
- Modify: `scripts/lib/config.py`
- Modify: `tests/test_orchestrator_topology_flags.py`
- Modify: `tests/test_orchestrator_topology_conditionals.py`
**Interfaces:** Produces `variables.py::_instance_flags(max_instances, *, singleton_declared)
-> {"ORCH_MAX_INSTANCES": "1".."8", "ORCH_SINGLETON_DECLARED": "true"|"false"}`; die
provider-losen Global-Werte in `config.py::_build_orch_variables`; Consumes
`orchestrator.max-instances` / `orchestrator.singleton`.

- [ ] Step 1: Flag-/Conditional-Test erweitern: `_instance_flags(1, singleton_declared=False)`
  → `"1"`/`"false"`; `_instance_flags(3, singleton_declared=True)` → `"3"`/`"true"`;
  `ORCH_MAX_INSTANCES`/`ORCH_SINGLETON_DECLARED` stehen in
  `strip_inactive_conditional_blocks`-Whitelist, `_FALSE_DEFAULT_CONDITIONALS`,
  `standalone._CONDITIONAL_FALSE_FLAGS` und `placeholders._BUILTIN_VARS`; abwesende
  Conditional-Variable ⇒ inaktiv. Lauf: `python3 -m pytest
  tests/test_orchestrator_topology_flags.py tests/test_orchestrator_topology_conditionals.py
  --basetemp="$PYTEST_BASETEMP"` → **rot — 6 failed**.
- [ ] Step 2: `_instance_flags` implementieren (pure, provider-agnostisch, Wert außerhalb
  1..8 fail-closed auf `"1"`); beide Flags **explizit** in die `conditional_vars`-Menge
  aufnehmen (nicht nur über das `ORCH_TOPOLOGY_`-Präfix); `_FALSE_DEFAULT_CONDITIONALS` um
  beide ergänzen; `_CONDITIONAL_FALSE_FLAGS` um `"ORCH_MAX_INSTANCES": "1"` und
  `"ORCH_SINGLETON_DECLARED": "false"`; `_BUILTIN_VARS` um beide; in
  `_build_orch_variables` `variables.update(_instance_flags(...))` aus dem Projekt-Scope
  einsetzen. Lauf: → **grün — 6 passed**.
- [ ] Step 3: `python3 scripts/sync.py --check` → **rc 0**; `tests/test_standalone_render.py`
  → **0 failed** (keine Byte-Drift, da noch kein Template den Platzhalter nutzt).
- [ ] Step 4: Commit `feat: add multi-instance flags, fail-closed registered`.

### Task 4: Instanz-Identität + Auflösung (AC-10, AC-11 Identitäts-Teil)

**Agent:** senior-developer
**Depends on:** —
**Files:**
- Modify: `scripts/lib/topology.py`
- Create: `tests/test_multi_instance_identity.py`
**Interfaces:** Produces `ORCHESTRATOR_ID_RE` (oder `is_valid_orchestrator_id`),
`resolve_orchestrator_instances(config, provider, topology, *, capabilities, validate=True)
-> tuple[int, str | None]` und `compose_instance_session_id(base_session_id, instance_id)
-> str`; Consumes `TopologyResolution`, `orchestrator_instances.multiple`,
`topology_verified_state.multiple`.

- [ ] Step 1: Identitäts-Test schreiben: Grammatik `[a-z0-9][a-z0-9._-]{0,39}` akzeptiert
  `scope-a`/`pr-42`, lehnt `Scope-A`, `-scope`, `a/b`, `..` und >40 Zeichen ab;
  `compose(base, None)` ist die Identität; `compose("base", "scope-a") ==
  "base__scope-a"`; `checkpoint.validate_session_id` akzeptiert die Komposition; ungültige
  ID/ Komposition → `ValueError`. Lauf:
  `python3 -m pytest tests/test_multi_instance_identity.py --basetemp="$PYTEST_BASETEMP"`
  → **rot — 5 failed** (Symbole fehlen).
- [ ] Step 2: Resolver-Test schreiben: Default N=1/Reason `None`; N=3 + `multiple: true`+
  `DOCUMENTED` → `(3, None)`; `multiple: false` → `(1, reason)`; `multiple: UNVERIFIED` →
  `(1, reason)`; explizites `primary` + N>1 same-scope → `SyncError` (bei `validate=True`),
  `validate=False` → `(1, reason)`; Provider-Override `primary` + globales N>1 → `(1, reason)`
  **ohne** `SyncError`; `singleton` present + N>1 → `SyncError`; `singleton` present + N=1 →
  `(1, None)`; `singleton: false` → `SyncError`. Lauf: → **rot — 9 failed**.
- [ ] Step 3: Implementieren. `resolve_orchestrator_instances`: N aus Projekt-Scope
  (Default 1), Same-Scope-Konflikte hart, Capability-Clamp auf 1 mit Reason,
  Cross-Scope-`primary` auf 1 mit Reason. `compose_instance_session_id`: `None` ⇒ Basis
  unverändert; sonst `<base>__<id>` und `validate_session_id` **lazy** importieren
  (kein Modul-Zyklus). Das logische Identitätsmodell **`orchestrator#<scope-id>`** als
  Docstring festhalten: Main Chat leitet die ID deterministisch aus dem Scope-Schlüssel
  (Plan-ID/Task-Ref, Branch, PR) ab und normalisiert sie; das Dispatch-Ziel bleibt
  `orchestrator` (keine `#`-Suffixe in Datei/`subagent_type`), die Identität reist im
  Envelope. Fehlende ID bei N>1 = Prompt-HARD-REJECT + Guard-Audit `id=unset`; doppelte
  ID/Scope-Überlappung = HARD ERROR beim Spawn (Prompt-Vertrag, keine Runtime-Registry).
  Lauf: → **grün — 14 passed**.
- [ ] Step 4: `python3 scripts/sync.py --check` → **rc 0** (kein Konsument verdrahtet).
- [ ] Step 5: Commit `feat: resolve orchestrator instance count and session ids`.

### Task 5: Checkpoint-/Progress-Namespaces (AC-10, AC-11 Zustands-Teil)

**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `scripts/lib/checkpoint.py`
- Create: `tests/test_multi_instance_state.py`
- Modify: `tests/test_checkpoint_paths.py`
**Interfaces:** Produces optionalen `CheckpointStore(..., orchestrator_id=None)` (auch über
`from_config`), Session-ID-Komposition über `topology.compose_instance_session_id`, Pfad
`<base>__<id>.json` und `progress-<id>.md`; Consumes Task 4.

- [ ] Step 1: Test schreiben: Default-Store (`orchestrator_id=None`) schreibt
  `sess1.json` + `current.md` **byte-identisch**; Store mit `orchestrator_id="scope-a"`
  schreibt `sess1__scope-a.json` und `progress-scope-a.md`, **kein** `current.md`;
  `validate_session_id("base__scope-a")` akzeptiert; `_session_file` bleibt im
  Checkpoint-Verzeichnis; Raw-Output-Verzeichnis nutzt dieselbe Komposition. Lauf:
  `python3 -m pytest tests/test_multi_instance_state.py tests/test_checkpoint_paths.py
  --basetemp="$PYTEST_BASETEMP"` → **rot — 6 failed**.
- [ ] Step 2: `orchestrator_id`-Parameter ergänzen; `_session_file`/`_session_raw_dir`
  komponieren vor der Validierung; `_write_progress_file` schreibt bei gesetzter ID nur
  `progress-<id>.md` (rein menschlich, **kein** Konsument), sonst unverändert `current.md`.
  Tracker bleibt im Kontext: kein Datei-Artefakt, kein Code-Pfad. Lauf: → **grün — 6 passed**;
  bestehende `test_checkpoint_paths.py` **0 failed**.
- [ ] Step 3: `python3 scripts/sync.py --check` → **rc 0**; `git status --porcelain` zeigt
  nur die erwarteten Dateien.
- [ ] Step 4: Commit `feat: namespace checkpoints and progress per orchestrator instance`.

### Task 6: `singleton-redundant` (INFO) + `instances-clamped` (WARNING) (AC-8, AC-9)

**Agent:** developer
**Depends on:** 1, 4
**Files:**
- Modify: `scripts/lib/consistency/topology.py`
- Modify: `tests/test_orchestrator_topology_consistency.py`
**Interfaces:** Produces Check-IDs `orchestrator-topology.singleton-redundant` (INFO) und
`orchestrator-topology.instances-clamped` (WARNING); Consumes
`resolve_orchestrator_instances`, `orchestrator.singleton`, Capability-Multiple.

- [ ] Step 1: Test schreiben: `singleton: true` + N=1 ⇒ genau ein INFO
  `singleton-redundant`, **kein** ERROR, rc 0; N=3 auf Provider mit `multiple: false` ⇒
  genau eine WARNING `instances-clamped`; Cross-Scope Provider-Override `primary` +
  globales N=3 ⇒ genau eine WARNING + effektiv N=1; Dedup je Check-ID; N=1 ohne
  `singleton` ⇒ keine Findings. Lauf:
  `python3 -m pytest tests/test_orchestrator_topology_consistency.py --basetemp="$PYTEST_BASETEMP"`
  → **rot — 5 failed**.
- [ ] Step 2: `_append_once` um `severity` (Default WARNING) erweitern; pro Provider
  `resolve_orchestrator_instances` aufrufen; INFO/WARNING mit Provider, N und Reason
  anhängen; **kein** Schreiben, kein Exit. Lauf: → **grün — 5 passed**.
- [ ] Step 3: `python3 scripts/consistency-check.py` → keine neuen ERRORs;
  `--check`-rc unverändert 0.
- [ ] Step 4: Commit `feat: report redundant singleton and clamped instances`.

### Task 7: A2A-Rule-Wortlaut + provider-skopierte effektive N (AC-9 Gate-Teil)

**Agent:** developer
**Depends on:** 3, 4
**Files:**
- Modify: `rules/1-generic/a2a-delegation-gates.md`
- Modify: `scripts/lib/rules.py`
- Create: `tests/test_a2a_instance_wording.py`
**Interfaces:** Produces den P3-Wortlaut **nur** im `{{#if ORCH_TOPOLOGY_EXPLICIT}}`-Zweig
(`höchstens {{ORCH_MAX_INSTANCES}}`, G1/G2/G3, ID/Scope-Regel) und die provider-skopierte
Überschreibung von `ORCH_MAX_INSTANCES` mit der effektiven N in
`rules.py::_merged_rule_vars`; Consumes `_instance_flags`, `resolve_orchestrator_instances`.

- [ ] Step 1: Test schreiben: ungesetzte Topologie rendert den `{{else}}`-Zweig
  **wortgleich** zu heute (kein `ORCH_MAX_INSTANCES`, kein neuer Satz); explizite
  Topologie rendert „höchstens {{ORCH_MAX_INSTANCES}}" statt „Genau eine Instanz";
  Provider mit `multiple: false` rendert effektiv `1`; `_merged_rule_vars(..., variables=None)`
  baut die Instanz-Flags selbst. Lauf:
  `python3 -m pytest tests/test_a2a_instance_wording.py --basetemp="$PYTEST_BASETEMP"`
  → **rot — 4 failed**.
- [ ] Step 2: Rule-Zweig ändern: G2 ersetzt „Genau eine Instanz" durch „höchstens
  {{ORCH_MAX_INSTANCES}}" und nennt eindeutige `orchestrator_id` + disjunkten Scope;
  fehlende/doppelte ID = HARD ERROR beim Spawn (Prompt-Vertrag); der `{{else}}`-Zweig
  bleibt Zeichen für Zeichen unverändert. In `rules.py` nach der Topologie-Auflösung
  `resolve_orchestrator_instances(...)` + `_instance_flags(...)` re-resolven und
  `ORCH_MAX_INSTANCES` mit der effektiven N überschreiben. Lauf: → **grün — 4 passed**.
- [ ] Step 3: `python3 scripts/sync.py --check` → **rc 0** (Topologie in diesem Repo
  ungesetzt ⇒ else-Zweig byte-identisch); `tests/test_orchestrator_topology_conditionals.py`
  → **0 failed**.
- [ ] Step 4: Commit `docs: state multi-instance gate wording behind explicit topology`.

### Task 8: Guard-Sentinel `id=` audit-only (AC-11 Guard-Teil, OQ-2 = A)

**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`
- Modify: `tests/test_orchestrator_guard_hook.py`
**Interfaces:** Produces Sentinel-Grammatik
`^#agent-meta:agent=([A-Za-z0-9_-]+)(?:\s+id=([A-Za-z0-9._-]+))?$` und ein Audit-Feld
`orchestrator_id=<id|unset>` **nur** im Audit-Log; Consumes die ID-Grammatik aus Task 4.

- [ ] Step 1: Hook-Test erweitern: Sentinel mit `id=scope-a` liefert **denselben**
  Allow/Deny-Exit wie ohne ID; Audit-Log-Zeile enthält `orchestrator_id=scope-a`; Sentinel
  ohne ID → `orchestrator_id=unset`; ungültige ID (`scope/a`, `Scope-A`, `..`) macht den
  Sentinel unparsebar (Rolle leer), ohne den Hook zu crashen; git-Sentinel-Zeile bleibt
  unverändert. Lauf:
  `python3 -m pytest tests/test_orchestrator_guard_hook.py --basetemp="$PYTEST_BASETEMP"`
  → **rot — 4 failed**.
- [ ] Step 2: Regex im Sentinel-Parser erweitern, beide Gruppen ausgeben, ID an die
  Audit-Zeile des Orchestrator-Sentinels hängen; Entscheidungspfad liest die ID **nie**;
  Kommentarblock dokumentiert den 4-Feld-Audit-Datensatz `{orchestrator_id, scope_id,
  spawned_by, spawned_at}` und die Reduktion auf `orchestrator_id`. `# version: 1.9.3` →
  `1.10.0`, `# changelog:`-Zeile ergänzen. Lauf: → **grün — 4 passed**; bestehende
  Hook-Tests **0 failed**.
- [ ] Step 3: `bash -n hooks/1-generic/orchestrator-guard-impl.sh` → **rc 0**.
- [ ] Step 4: Commit `feat: audit orchestrator instance id in the guard sentinel`.

### Task 9: A2A-Envelope, Delegation-Syntax & Viz-Emitter (AC-11 Event-Teil)

**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `schemas/a2a-handoff.schema.json`
- Modify: `scripts/lib/delegation_syntax.py`
- Modify: `scripts/viz-logger.py`
- Create: `tests/test_multi_instance_envelope.py`
- Create: `tests/test_viz_instance_fields.py`
**Interfaces:** Produces optionales `orchestrator_id` + `metadata.scope_id` im Envelope,
stdlib-Pattern-Check in `validate_envelope`, CLI/MCP-Felder `--orchestrator-id`,
`--scope-id`, `--spawned-by`, `--spawned-at` im Viz-Emitter; Consumes die ID-Grammatik
aus Task 4.

- [ ] Step 1: Tests schreiben: Schema akzeptiert gültige optionale `orchestrator_id` +
  `metadata.scope_id`, lehnt ungültige ab, verlangt sie **nicht** (N unbekannt);
  `validate_envelope` akzeptiert gültige optionale Felder und lehnt `target_agent:
  orchestrator#scope-a` ab (Ziel bleibt `orchestrator`); Event ohne Instanzfelder ist
  unverändert (keine neuen Keys); Event mit allen vier Feldern trägt sie; das Log bleibt
  **eine** Datei (`events.jsonl`, kein Shard). Lauf: `python3 -m pytest
  tests/test_multi_instance_envelope.py tests/test_viz_instance_fields.py
  --basetemp="$PYTEST_BASETEMP"` → **rot — 6 failed**.
- [ ] Step 2: Schema-Properties ergänzen (nicht `required`); Pattern-Check in
  `validate_envelope`; Viz-CLI/MCP um die vier optionalen Felder erweitern und nur bei
  Vorhandensein in das Event schreiben. Lauf: → **grün — 6 passed**.
- [ ] Step 3: `python3 scripts/sync.py --validate` → **rc 0**;
  `python3 scripts/viz-report.py --help` → **rc 0** (Reader unverändert).
- [ ] Step 4: Commit `feat: carry orchestrator identity in envelopes and viz events`.

### Task 10: Doku-Flip + CHANGELOG + v1-Ledger (AC-8…AC-11 Doku)

**Agent:** junior-developer
**Depends on:** 1, 2, 3, 4, 5, 6, 7, 8, 9
**Files:**
- Modify: `docs/concepts/active/orchestrator-topology.md`
- Modify: `docs/concepts/active/singleton-orchestrator-architecture.md`
- Modify: `docs/plans/2026-11-04-orchestrator-topology-v1-plan.md`
- Modify: `tests/test_orchestrator_topology_docs.py`
- Modify: `CHANGELOG.md`
**Interfaces:** Produces die P3-Doku (Keys, ID-Modell, Namespaces, Guard-Audit, Scope-Regel)
und den CHANGELOG-Eintrag; Consumes den implementierten Stand aus Tasks 1–9.

- [ ] Step 1: Doku-Test anpassen: Concept-Doc enthält **nicht** mehr
  „P3, designed, not shipped", sondern den Shipped-Status und die neuen Keys; die
  Singleton-Concept verlinkt auf den Shipped-Abschnitt; das v1-Ledger nennt P3
  „umgesetzt"; der CHANGELOG-Eintrag existiert. Lauf:
  `python3 -m pytest tests/test_orchestrator_topology_docs.py --basetemp="$PYTEST_BASETEMP"`
  → **rot — 4 failed**.
- [ ] Step 2: Concept-Doc-Abschnitt auf „shipped" umschreiben (`max-instances`/`singleton`,
  `orchestrator#<scope-id>`-Modell, `<base>__<id>`/`progress-<id>.md`, audit-only
  Guard-ID, Main-Chat-Scope-Pflicht); Singleton-Concept-Status aktualisieren; v1-Ledger-
  P3-Notiz von „offen" auf „umgesetzt in P3" ändern; CHANGELOG unter `Unreleased`
  ergänzen (Keys, harte Konflikte, INFO/WARNING, State-Namespaces, Guard-Audit, N=1
  byte-identisch). Lauf: → **grün — 4 passed**.
- [ ] Step 3: `python3 scripts/sync.py --check` → **rc 0**;
  `python3 scripts/consistency-check.py` → keine neuen ERRORs.
- [ ] Step 4: Commit `docs: document shipped multi-instance orchestrators`.

---

## Exit-Kriterien

P3 ist fertig, wenn **alle** folgenden Punkte erfüllt sind:

1. **AC-8 (P3-only) — Schema:** Given eine konsistente Config, when validiert wird, then
   akzeptiert das Schema `max-instances` (min 1, **max 8**, Default 1; der Key existiert
   vor P3 nicht) und `singleton` (nur `true`, **kein** `default`); `singleton` present +
   N>1 ist ein harter Validator-ERROR; `singleton` present + N=1 ist **kein** Fehler,
   sondern das INFO `orchestrator-topology.singleton-redundant` (rc bleibt 0);
   `--validate` ist grün.
2. **AC-9 (P3-only) — `primary` × N:** Given `topology: primary` und `max-instances > 1`
   im selben Scope, when validiert wird, then ist das ein harter ERROR; given
   Provider-Override `primary` bei globalem N>1, then ist es eine WARNING und effektiv N=1.
3. **AC-10 (P3-only) — Zustands-Pfade:** Given N=1, when ein Checkpoint geschrieben wird,
   then entsteht exakt der heutige Pfad; given N=2, then entstehen `<base>__<id>`-Dateien
   und `validate_session_id` akzeptiert die Komposition.
4. **AC-11 (P3-only) — Audit-Datensatz:** Given N>1, when Events geschrieben werden, then
   tragen sie `orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at`; das Log bleibt
   eine Datei; `viz-report` konsumiert unverändert; das Guard-Audit-Log trägt die ID, und
   die Reduktion des Audit-Datensatzes auf `orchestrator_id` ist im Guard-Audit
   dokumentiert (Feldname + Reduktionssatz, nicht nur implizit). Given ein Sentinel mit
   `id=`, when der Guard entscheidet, then wird die ID **nie** für Allow/Deny benutzt
   (**OQ-2 = A**).
5. **AC-12 (P3-only) — Abgrenzung:** Given die Schema-`description`s, when sie geprüft
   werden, then sind `max-instances` (Anzahl Orchestratoren) und `max-parallel-agents`
   (Parallelität innerhalb eines Orchestrators) gegeneinander abgegrenzt
   (Text-Assertion).
6. **AC-17 P3-Zeilen (verbatim):** **(P3-only)** `singleton: false`, `singleton` present ×
   N>1, `primary` × N>1 im selben Scope. Jeder dieser Teilstrings wird **assertet**,
   nicht nur dokumentiert.
7. **N=1-Byte-Identität bewiesen:** `sync --check` rc 0 auf unverändertem Projekt;
   `tests/test_ac01_render_identity.py` unverändert grün; `settings.local.json` aus AC-01
   ausgeschlossen; die Goldens bleiben unverändert; **keine** pauschale Rebaseline.
8. **Volle Suite:** `python3 -m pytest tests/ --basetemp="$PYTEST_BASETEMP"` ohne neue
   Fehlschläge. Laufzeit ~3,4 h lokal — **CI shardet** die Suite; der lokale Nachweis darf
   über die berührten Shards geführt werden, das Ergebnis muss pro Shard dokumentiert sein.
9. **Kein Merge, kein Push durch den Executor;** Branch-Management liegt bei `git`.

## Risiken

| # | Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| R1 | `max-instances` ohne Zustands-Isolation | Stiller Resume-Datenverlust | Key + `maximum: 8` + `<base>__<id>`/`progress-<id>.md` landen gemeinsam (Tasks 4/5); kein Zwischenschritt mit `maximum: 1` |
| R2 | `singleton` bekommt versehentlich einen Schema-Default | Presence-only-Semantik kippt | Task 1 testet explizit `"default" not in singleton`; Abwesenheit = aus `max-instances` abgeleitet |
| R3 | Guard nutzt die Sentinel-ID für Allow/Deny | Neue, unhaltbare Sicherheitszusage | Task 8 testet „gleicher Exit mit/ohne ID"; Kommentar + Doku sagen **audit-only** |
| R4 | Byte-Identität bricht durch unbedingte Rule-Änderung | Jedes Consumer-Projekt meldet Drift | Nur der `ORCH_TOPOLOGY_EXPLICIT`-Zweig ändert sich; `{{else}}` bleibt wortgleich; Task 7/10 + bestehende Goldens |
| R5 | Provider-skopierte N weicht von der globalen N ab | Gate-Wortlaut nennt die falsche Zahl | `rules.py` überschreibt `ORCH_MAX_INSTANCES` mit der effektiven N (Task 7); Task 6 meldet Clamps laut |
| R6 | Doku behauptet weiter „P3, designed, not shipped" | Widerspruch zum ausgelieferten Code | Task 10 flippt den Marker und pinnt ihn im Doku-Test |
| R7 | v1-Doku-Test wird zu weit aufgeweicht | AC-4-Regression | Nur der P3-Marker wird geändert; alle v1-Textassertions bleiben bestehen |
| R8 | Hook-Version/Changelog vergessen | Stale-Hook-Drift-Warnung | Global Constraint + Task 8, Step 2 |

## Annahmen und Self-Review

**Annahmen** (wenn falsch, wird der betroffene Task neu geschnitten — nicht die Spec):

1. `orchestrator_instances.multiple` und `topology_verified_state.multiple` existieren für
   jeden registrierten Provider (verifiziert in `config/provider-capabilities.yaml`); es
   gibt keinen provider-skopierten `max-instances`-Key.
2. `checkpoint.validate_session_id` akzeptiert `__` bereits (es verbietet nur Pfad-
   separierer, `..`, absolute Pfade und Leerstrings); die Komposition ist rein additiv.
3. `viz-report.py` ignoriert unbekannte Event-Felder und `metadata` erlaubt zusätzliche
   Properties; die neuen Felder sind additiv.
4. Die A2A-Rule ist der einzige byte-identitätskritische Renderpfad; der explizite
   Topologie-Zweig darf sich ändern, der `{{else}}`-Zweig nicht.
5. `hook_audit_log_append` bleibt unverändert; Task 8 erweitert nur die übergebene Zeile
   und den Sentinel-Parser.
6. **K-1 (Plan-Präzisierung, keine OQ):** Ein *abgeleitetes* `primary` (kein explizites
   `topology: primary`) + N>1 ist kein Same-Scope-Validatorfehler; es wird ausschließlich
   über `orchestrator_instances.multiple`/`topology_verified_state.multiple` geclampt.
   Die Spec pinnt den harten Fehler nur für die explizite Deklaration.
7. **K-2:** `ORCH_MAX_INSTANCES` wird spec-konform in
   `_FALSE_DEFAULT_CONDITIONALS`/`_CONDITIONAL_FALSE_FLAGS` registriert, aber **nicht** als
   boolesches Gate verwendet (sein Default ist `"1"`, sein Einsatz ist der Platzhalter).
8. **K-3:** `compose_instance_session_id` importiert `checkpoint.validate_session_id`
   lazy, um den Modul-Zyklus `checkpoint → topology → checkpoint` zu vermeiden.

**Self-Review:**

- **Agenten:** Jeder Task hat genau eine Rolle aus {`junior-developer`, `developer`,
  `senior-developer`}. Kein Task ist ohne Agent.
- **Datei-Ownership:** Innerhalb jeder Parallel-Gruppe berührt kein Task eine Datei eines
  anderen. Gruppen: **G1** {1, 2, 4} (Schema/Test-Schema, `config.py`/Test-Validator,
  `topology.py`/neuer Identitätstest); **G2** {3} (`config.py` erst nach Task 2);
  **G3** {5, 6, 7, 8, 9} (Checkpoint, Consistency, Rule/`rules.py`, Hook, Schema/
  Delegation/Viz — disjunkt); **G4** {10} (Doku/CHANGELOG). `config.py` liegt nur in 2
  und 3 (sequenziell), `topology.py` nur in 4.
- **AC-Abdeckung:** AC-8 → 1, 2, 6; AC-9 → 2, 6; AC-10 → 4, 5; AC-11 → 8, 9 (plus 4);
  AC-12 → 1; AC-17 P3 → 2. Kein P3-AC ist ungetestet.
- **Keine v1-AC-Regression:** AC-6 bleibt durch unveränderte Goldens + `sync --check`
  rc 0 geschützt; AC-18 bleibt durch die additiven Registrierungen und den unveränderten
  else-Zweig geschützt; AC-1/2/17(P1)/3/7/14/19/20 werden nicht umgeschrieben, nur um
  neue, separate Findings/Flags ergänzt; AC-4 wird nur am P3-Marker aktualisiert, nicht
  inhaltlich aufgeweicht.
- **Keine offene Frage:** OQ-2 = A und OQ-3 = A sind eingefaltet; der Plan fügt **0** OQ
  hinzu. K-1…K-3 sind Präzisierungen gegen den Checkout mit gewähltem Verhalten, keine
  Entscheidungsbedarfe.
