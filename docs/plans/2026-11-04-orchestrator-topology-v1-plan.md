---
pipeline_stages:
  implement: 1
status: geplant
date: 2026-11-04
base-commit: 802380e5
trace:
  - SPEC-orchestrator-topology-2026-11-03
  - issue-1077
---

# Orchestrator-Topologie v1 (P0–P2 + P4) — Implementation Plan

> Status: **DONE (2026-11-04)** — Branch `feat/orchestrator-topology-v1`,
> PR → `main` (Refs #1077), Merge `44f39ebc`; **21/21 Checks grün**.
>
> **OQ-5 = A:** v1 = P0–P2 + P4. P3 (Multi-Instanz, Guard-Audit, `max-instances`,
> `singleton`, AC-8…AC-12) ist der unmittelbar nächste Schritt und **nicht** Teil
> dieses Plans.

**Goal:** v1 macht die Position des Orchestrators zu einem expliziten, validierten
Nutzerentscheid (`orchestrator.topology: primary | subagent | hybrid`) mit genau
einem spawnbaren Orchestrator und einem Builder-Default auf Opencode v2. Bei
ungesetztem Key bleibt das Verhalten byte-identisch; jede Degradierung ist laut
(genau eine WARNING pro Check-ID und Provider), und keine Matrix-Zelle behauptet
eine Fähigkeit ohne aufgezeichnete Evidenz.

**Architecture:** Ein neues Blattmodul `scripts/lib/topology.py` besitzt
ausschließlich die Auflösung (`TopologyResolution`, `resolve_topology`) und
schreibt nichts. Konsumenten sind der harte stdlib-Validator in
`config.py::_validate_orchestrator_topology`, die Emissionspfade
`provider_transform.py::_apply_agent_transform`, `isolation.py::_opencode_entry_point`
und der **bestehende** Bool `emit_default_agent` in
`context.py::apply_settings_surface_shape` (kein zweiter Steuerparameter), der
Konsistenz-Checker `consistency/topology.py` sowie eine Sync-Summary-Zeile in
`sync_pipeline.py`. Capability-Daten (`topology_support`, `topology_degrade`,
`orchestrator_instances`, `topology_verified_state`) bleiben der einzige
Provider-Unterschied; es gibt keinen `if provider ==`-Zweig.

**Tech Stack:** Python 3.9 (stdlib only), PyYAML (bestehende Ausnahme), pytest,
JSON-Schema (Daten, kein Validator), Markdown/YAML-Templates, Bash (nur als
Testsubjekt).

**Spec:** docs/specs/2026-11-04-orchestrator-topology-spec.md
**Spec-ID:** SPEC-orchestrator-topology-2026-11-03
**Design (Kontext):** docs/specs/2026-11-03-orchestrator-topology-design.md (Rev. 4)
**Issue:** #1077 · **Phasen:** P0, P1, P2, P4 aus `## Phasenzerlegung` der Spec
**Aufwand:** Spec nennt XL über alle Phasen (44–51 Datei-Berührungen); v1 berührt
**19 Tasks / 40 Dateien** (davon 19 neu, 1 Testmodul erweitert). Eine belastbare
Schätzung liefert `effort-estimator` (Textverweis, hier nicht berechnet).

## Trace-Anker

`spec-id: SPEC-orchestrator-topology-2026-11-03` — referenziert über `**Spec:**`.
Die Spec heißt bewusst `*-spec.md`; `consistency/spec_plan.py::_classify` ordnet
sie deshalb als `plan` ein (akzeptierte WARNING-only-Governance, Spec §Trace-Anker).

## Ausgangslage (verifiziert 2026-11-04 gegen `main` `802380e5`)

| Fakt | Beleg |
|---|---|
| `role_emitted_for_provider` existiert mit Signatur `(role, active_set, config, provider)` | `scripts/lib/active_set.py::role_emitted_for_provider` |
| Die vier Capability-Strukturen existieren **noch nicht**; `main_agent_selectable`/`subagent_dispatch`/`parallel_execution` existieren je Provider | `config/provider-capabilities.yaml` |
| `scripts/lib/topology.py`, `scripts/lib/consistency/topology.py`, `scripts/topology-probe.py` existieren nicht | `glob scripts/**/*topology*` → nur `consistency/context_topology.py` |
| `variables.py::_FALSE_DEFAULT_CONDITIONALS` und `strip_inactive_conditional_blocks` existieren | `scripts/lib/variables.py` |
| `standalone.py::_CONDITIONAL_FALSE_FLAGS` existiert; `placeholders.py::_UNREGISTERED_BUILDER_RATCHET` ist shrink-only | `scripts/lib/standalone.py`, `scripts/lib/consistency/placeholders.py` |
| `agent_sync.py::_should_skip_role` liest heute `ORCH_MODE_MAIN_CHAT` direkt | `scripts/lib/agent_sync.py:_should_skip_role` |
| `tests/test_ac01_render_identity.py` existiert | `tests/` |

## Klarstellungen (Plan-Präzisierung, keine Spec-Änderung)

- **K-1 (`file:symbol` statt Spec-Line-Refs):** Zwei Spec-Symbole sind gegen
  `802380e5` nicht auffindbar und werden hier auf den realen Träger abgebildet:
  `context.py::_build_context_vars` → `context.py::_build_managed_block` (dort
  stehen die provider-skopierten `ORCH_MODE_*`/`REPO_CONTAINMENT_*`-Zuweisungen);
  `config.py::_build_variables` → `config.py::build_variables`. Beides ist eine
  Namenskorrektur, keine Vertragsänderung — der IC-4-Vertrag (provider-los vs.
  provider-skopiert) bleibt wörtlich.
- **K-2 (AC-16-Baseline):** Der Evidenz-Test transkribiert die **normative**
  Pre-P0-Matrix der Spec einmal als Testdaten (`PRE_P0_BASELINE`). Jede Abweichung
  davon ist ein Upgrade und braucht alle drei Gate-Bedingungen. Die Endzahl `N`
  wird **berechnet**, nie gepinnt.
- **K-3 (Fixture-Ownership):** Golden-Fixtures entstehen erst in Task 16, nachdem
  Transform (11) und Entry-Point (12) ihre Endform haben; `sync --check`-Bytes
  dürfen nicht gegen einen Zwischenstand eingefroren werden.
- **K-4 (P1 liefert keinen `primary_role`-Accessor):** `providers.explicit_primary_role`
  bleibt der einzige Registry-Read (#1090/B1); `primary-role` wird nur als
  Ableitungsquelle gelesen.

## Global Constraints

- **Python 3.9, stdlib only.** Keine neue Dependency (kein `jsonschema`, kein
  `pytest-timeout`); `tests/requirements.txt` bleibt unverändert. Kein
  `match`, keine PEP-604-Annotation ohne `from __future__ import annotations`.
- **Provider-agnostisch:** Unterschiede ausschließlich über Capability-Daten
  (`topology_support`, `topology_degrade`, `orchestrator_instances`,
  `topology_verified_state`) — kein `if provider == "..."`, kein
  Provider-Namens-Literal im Auflöser.
- **AC-6 Byte-Identität ist Invariante, nicht Ergebnis:** Bei ungesetztem Key
  (`ORCH_TOPOLOGY_EXPLICIT != "true"`) rendert jedes Template byte-identisch zu
  heute, inklusive des **fail-closed** registrierten
  `_FALSE_DEFAULT_CONDITIONALS` (abwesende Variable ⇒ Zweig inaktiv). Ein
  fehlender Registrierungseintrag ist ein Fehler, kein Rebaseline-Grund.
- **Keine `pytest.ini` / `pyproject.toml` / `setup.cfg`** anlegen oder ändern.
- **Testkommando:** `python3 -m pytest <pfad> --basetemp="$PYTEST_BASETEMP"`
  (niemals ein Basetemp im Baum; `rtk pytest` ist defekt, nicht verwenden).
- **Rebaseline-Regeln:** AC-01-Baselines nur **per Eintrag** und nur für die
  Dateien, deren Bytes sich absichtlich ändern; **kein** `--write`-Sammellauf;
  das host-lokale `settings.local.json` bleibt aus AC-01 ausgeschlossen.
- **Kein Merge durch den Executor.** Push/Tag/Branch ausschließlich Rolle `git`;
  ein Commit pro Task, Englisch, Conventional Commits, ≤ 72 Zeichen, ohne BOM.
- **Kein `isolation: "worktree"`.** Arbeit direkt im Projektverzeichnis.
- **Hook-Änderungen** (in v1 keine; erst P3) verlangen `# version:`/`# changelog:`.
- **Sprache:** Plan und Doku Deutsch, Code/Commits/Tests Englisch.

## File Structure

### P0 — Capability-Daten & Evidenz

- Modify: `config/provider-capabilities.yaml` — vier Strukturen je Provider (T1, T3)
- Create: `scripts/topology-probe.py` — read-only Probe-Harness, fünf Probes (T2)
- Create: `docs/spikes/2026-11-03-issue-1077-topology-probe.md` — Evidenz-Dokument (T3)
- Create: `tests/test_topology_capability_invariant.py` — AC-13/AC-15-Invariante (T1)
- Create: `tests/test_topology_probe_evidence.py` — Upgrade-/Zählregel + „not run" (T4)

### P1 — Config-Fläche, Auflöser, Validator, Flags

- Modify: `config/project-config.schema.json` — Enum + Provider-Override (T5)
- Create: `scripts/lib/topology.py` — Auflöser, Blattmodul (T6)
- Modify: `scripts/lib/config.py` — Validator (T7), provider-lose Global-Flags (T10)
- Modify: `scripts/lib/variables.py` — `_topology_flags`, Whitelist, `_FALSE_DEFAULT_CONDITIONALS` (T8)
- Modify: `scripts/lib/standalone.py` — `_CONDITIONAL_FALSE_FLAGS` (T9)
- Modify: `scripts/lib/consistency/placeholders.py` — `_BUILTIN_VARS` (T9)
- Modify: `scripts/lib/context.py`, `scripts/lib/rules.py` — provider-skopiertes Re-Resolver (T10)
- Create: `tests/test_orchestrator_topology_schema.py` (T5)
- Create: `tests/test_orchestrator_topology_resolver.py` (T6)
- Create: `tests/test_orchestrator_topology_validator.py` (T7, inkl. 3×3-Matrix)
- Create: `tests/test_orchestrator_topology_flags.py` (T8)
- Create: `tests/test_orchestrator_topology_conditionals.py` (T8, AC-18; grün erst mit T9)
- Create: `tests/test_orchestrator_topology_global_flags.py` (T10)

### P2 — Emission, laute Degradierung, Builder-Default

- Modify: `scripts/lib/provider_transform.py` — Topologie-Konjunktion (T11)
- Modify: `config/ai-providers.yaml` — Kommentar zur Topologie-Achse (T11)
- Modify: `scripts/lib/isolation.py`, `scripts/lib/context.py` — Entry-Point + `emit_default_agent` (T12)
- Modify: `scripts/lib/agent_sync.py` — `_should_skip_role` nutzt das Prädikat (T13)
- Create: `scripts/lib/consistency/topology.py` — Checker (T14)
- Modify: `scripts/consistency-check.py` — Checker registrieren (T14)
- Modify: `scripts/lib/sync_pipeline.py` — `emit_topology_summary` (T15)
- Modify: `tests/test_ac01_render_identity.py` + Create: `tests/fixtures/topology-golden/*` (T16)
- Create: `tests/test_orchestrator_topology_emission.py` (T11)
- Create: `tests/test_orchestrator_topology_entrypoint.py` (T12)
- Create: `tests/test_orchestrator_topology_skip_role.py` (T13)
- Create: `tests/test_orchestrator_topology_consistency.py` (T14)
- Create: `tests/test_topology_summary_line.py` (T15)

### P4 — Regel- und Doku-Amendment

- Create: `docs/concepts/active/orchestrator-topology.md` (T17)
- Modify: `docs/concepts/active/singleton-orchestrator-architecture.md` — Cross-Link (T18)
- Modify: `rules/1-generic/a2a-delegation-gates.md` — conditional Gate-Wortlaut (T18)
- Modify: `agents/1-generic/orchestrator.md`, `agents/1-generic/_reference-agent.md` — Topologie-Zeile (T18)
- Create: `tests/test_orchestrator_topology_docs.py` (T17)
- Modify: `CHANGELOG.md` (T19)

---

## Tasks

### Task 1: Capability-Strukturen + Invariantentest (AC-13, AC-15)

**Agent:** developer
**Depends on:** —
**Files:**
- Modify: `config/provider-capabilities.yaml`
- Create: `tests/test_topology_capability_invariant.py`
**Interfaces:** Produces `topology_support` / `topology_degrade` / `orchestrator_instances` / `topology_verified_state` je Provider; Consumes bestehende `main_agent_selectable` / `subagent_dispatch` / `parallel_execution`.

- [x] Step 1: Test schreiben (parametrisiert über alle registry-Provider): alle vier Strukturen vorhanden, `topology_support.<achse>` bool, `topology_degrade.<achse>` str, `orchestrator_instances.multiple` bool, `topology_verified_state.<achse> ∈ {VERIFIED-RUNTIME, DOCUMENTED, UNVERIFIED}`, Invariante `support == true ⇒ state != UNVERIFIED`. Lauf: **rot — 9 failed** (ein Fehlschlag je registriertem Provider, Meldung nennt die fehlenden Schlüssel).
- [x] Step 2: Vier Strukturen für alle neun Provider eintragen; Werte ausschließlich aus der **normativen Pre-P0-Matrix** der Spec. `topology_verified_state` = `DOCUMENTED` nur für Zellen, die aus einem vorhandenen Capability-Key abgeleitet sind; `UNVERIFIED` für die 15 konservativen Zellen. Kein `yes` ohne Ableitungsquelle.
- [x] Step 3: Kopfkommentar der Datei um den Vertrag ergänzen (vier Keys Pflicht je Provider, `UNVERIFIED ⇒ no`, Fail-safe-Ziel `subagent`, kein Registry-Eintrag für `custom`).
- [x] Step 4: Lauf: **grün — 9 passed**. Zusätzlich `python3 scripts/sync.py --validate` → rc 0.
- [x] Step 5: Commit `feat: add orchestrator topology capability structures`.

### Task 2: Read-only Probe-Harness (P0-1…P0-5)

**Agent:** developer
**Depends on:** —
**Files:**
- Create: `scripts/topology-probe.py`
**Interfaces:** Produces fünf Probe-IDs `P0-1`…`P0-5` (Mapping Design §16 Nr. 2–6) mit `--list` / `--probe <id> --dry-run`; Consumes keine Config, schreibt nichts.

- [x] Step 1: Gerüst mit fünf Probe-Deskriptoren (`id`, `provider`, `question`, `command`, `needs_binary`) aus Design §16 Nr. 2–6; CLI `--list`, `--probe <id>`, `--dry-run`; jeder Schreibzugriff höchstens unter `.tmp/`.
- [x] Step 2: Ausführung implementieren: Befehl starten, Exit-Code + stdout/stderr + erkannte Provider-Version erfassen, Ergebnis als Record mit `command`, `date`, `version`, `observed`. Keine Mutation am Repo, kein `sync.py`-Aufruf.
- [x] Step 3: „not run"-Pfad: fehlt das Binary (`shutil.which`), wird wörtlich `not run — CLI unavailable` plus Grund ausgegeben, Exit 0 — kein Fehlschlag, keine Wiederholung.
- [x] Step 4: Lauf: `python3 scripts/topology-probe.py --list` → **5 Zeilen**, Exit 0; `--probe P0-2 --dry-run` → gibt den Befehl aus, Exit 0; `git status --porcelain` unverändert (leer).
- [x] Step 5: Commit `feat: add read-only topology probe harness`.

### Task 3: Probes ausführen + Evidenz-Dokument (P0-Gate 1/2)

**Agent:** developer
**Depends on:** 1, 2
**Files:**
- Create: `docs/spikes/2026-11-03-issue-1077-topology-probe.md`
- Modify: `config/provider-capabilities.yaml`
**Interfaces:** Produces Evidenz-Record je Probe (`P0-1`…`P0-5`) und ggf. Zell-Upgrades; Consumes Harness aus Task 2 und Baseline aus Task 1.

- [x] Step 1: Dokument-Gerüst mit fünf Abschnitten `## P0-1` … `## P0-5`; je Abschnitt die Felder Befehl, Datum, Provider-Version, beobachtetes Ergebnis inkl. Fehlerfall oder die wörtliche Zeile `not run — CLI unavailable` mit Grund.
- [x] Step 2: Alle fünf Probes real ausführen; Ausgabe wörtlich eintragen. Nicht verfügbare CLIs erhalten die wörtliche `not run`-Zeile — das ist ein gültiges Ergebnis, kein Blocker.
- [x] Step 3: Upgrade-Prozedur anwenden: Eine Zelle wechselt nur auf `yes`, wenn **alle drei** Bedingungen erfüllt sind — (1) Evidenzzeile im Dokument, (2) `topology_verified_state.<achse>` ∈ {DOCUMENTED, VERIFIED-RUNTIME}, (3) §3.1-Zeile ohne offene `unverified`-Felder außer `prompt-caching`/`progress`. Jede Änderung wird im Dokument mit Zellname + Bedingung 1–3 protokolliert.
- [x] Step 4: Verifikation: `grep -c '^## P0-'` = 5; `grep -c 'not run — CLI unavailable'` ≤ 5 und jede Probe hat **entweder** einen Ergebnis-Record **oder** die wörtliche Zeile; `python3 scripts/sync.py --validate` → rc 0.
- [x] Step 5: Commit `docs: record orchestrator topology probe evidence`.

### Task 4: Evidenz-/Zählregel-Test (AC-15, AC-16, P0-Gate 3)

**Agent:** developer
**Depends on:** 1, 3
**Files:**
- Create: `tests/test_topology_probe_evidence.py`
**Interfaces:** Produces Prüffunktion „Zelle darf nur mit Evidenz `yes` sein" + Bilanz `25 + N` / `15 − N`; Consumes Spike-Doc und `provider-capabilities.yaml`.

- [x] Step 1: Negativtest zuerst: synthetisches Upgrade ohne Evidenzzeile muss als Verstoß gemeldet werden; ebenso Upgrade mit Evidenz, aber `UNVERIFIED`-State. Lauf: **rot — 2 failed** (`ImportError`/fehlende Prüffunktion).
- [x] Step 2: Parser für das Spike-Dokument (Probe-ID, Ergebniszeile, `not run`) und einmalige Transkription der normativen Pre-P0-Matrix als `PRE_P0_BASELINE` (K-2) implementieren.
- [x] Step 3: Prüffunktion implementieren: Abweichung von der Baseline = Upgrade ⇒ alle drei Gate-Bedingungen; `N` = Anzahl belegter Upgrades; Bilanz `25 + N` datenabgeleitet / `15 − N` `UNVERIFIED ⇒ no`; `0 ≤ N ≤ 15`; 0 spekulative `yes`.
- [x] Step 4: „not run"-Zweig pinnen: ein `not run`-Eintrag lässt die Zelle `no`, erzeugt **keine** WARNING und lässt den Test grün.
- [x] Step 5: Lauf: **grün — 6 passed** (2 Negativ, 2 Bilanz, 1 not-run, 1 state-Invariante), ohne gepinnte Endzahl.
- [x] Step 6: Commit `test: enforce topology evidence upgrade rule`.

### Task 5: Schema-Enum + Provider-Override (AC-1 Schema-Teil, AC-5)

**Agent:** junior-developer
**Depends on:** —
**Files:**
- Modify: `config/project-config.schema.json`
- Create: `tests/test_orchestrator_topology_schema.py`
**Interfaces:** Produces `orchestrator.topology` (enum) und `orchestrator.provider-overrides.<P>.topology`; Consumes nichts.

- [x] Step 1: Test schreiben (stdlib `json`): Enum akzeptiert `primary|subagent|hybrid`, lehnt `hybrid2` ab; `provider-overrides.<P>` behält `additionalProperties: false` **und** akzeptiert `topology` neben `mode`; `description` von `context_file.topology` grenzt gegen Agent-Topologie ab; **kein** Schema-`default` auf `orchestrator.topology`. Lauf: **rot — 4 failed**.
- [x] Step 2: `topology` + `provider-overrides.<P>.topology` ergänzen (Enum, Beschreibung, kein Default); `additionalProperties: false` unverändert lassen.
- [x] Step 3: Lauf: **grün — 4 passed**; `python3 scripts/sync.py --validate` → rc 0.
- [x] Step 4: Commit `feat: declare orchestrator topology in project config schema`.

### Task 6: Auflöser `scripts/lib/topology.py` (AC-2, AC-15)

**Agent:** senior-developer
**Depends on:** 5
**Files:**
- Create: `scripts/lib/topology.py`
- Create: `tests/test_orchestrator_topology_resolver.py`
**Interfaces:** Produces `VALID_TOPOLOGIES`, `VERIFIED_STATES`, `TopologyResolution`, `resolve_topology(...)`, `topology_explicit(...)`; Consumes `config`-Dict, `provider_config`, `capabilities`, aufgelösten `mode`, optional `active_set`.

- [x] Step 1: Test schreiben: Präzedenz (Override > Projekt > Ableitung), Ableitung (`primary-role` gesetzt **und** Rolle im ActiveSet ⇒ `primary`, sonst `subagent`; `hybrid` nie abgeleitet), Key ungesetzt ⇒ `degraded_from is None`. Lauf: **rot — Modul-Collection-Error** (`ModuleNotFoundError: scripts.lib.topology`), 0 Tests gesammelt.
- [x] Step 2: Konstanten + frozen `TopologyResolution` + `topology_explicit` implementieren; Lauf: **rot — 3 failed** (Resolver fehlt).
- [x] Step 3: `resolve_topology` mit Präzedenz + Ableitung implementieren; `validate=True` wirft `SyncError` bei unbekanntem Enum, `validate=False` liefert normalisiert.
- [x] Step 4: Fallback-Regel implementieren (B2): `support == false` **oder** `UNVERIFIED` ⇒ `effective` aus `topology_degrade` falls in `VALID_TOPOLOGIES`, sonst Fail-safe `subagent`; `degraded_from = declared` nur bei echter Änderung; Mechanismus-Wort ausschließlich in `degradation_reason`; Koinzidenz-Fall (Continue: declared `subagent`, Fail-safe `subagent`) ⇒ `degraded_from is None`.
- [x] Step 5: Lauf: **grün — 14 passed** (4 Präzedenz, 3 Ableitung, 5 Fallback inkl. Koinzidenz, 2 Fehlerpfad/Invariante); jede Assertion prüft `effective in VALID_TOPOLOGIES`.
- [x] Step 6: Commit `feat: add orchestrator topology resolver`.

### Task 7: Harter stdlib-Validator + 3×3-Matrix (AC-1, AC-2, AC-17 P1, AC-5)

**Agent:** developer
**Depends on:** 6
**Files:**
- Modify: `scripts/lib/config.py`
- Create: `tests/test_orchestrator_topology_validator.py`
**Interfaces:** Produces `config.py::_validate_orchestrator_topology(config, config_path)`; Consumes `topology.VALID_TOPOLOGIES`.

- [x] Step 1: Test schreiben: (a) `unknown orchestrator.topology`; (b) `orchestrator.topology conflicts with orchestrator.mode: main-chat` inkl. **Same-Object**; (b2) `... conflicts with orchestrator.enabled: false`; (c) `provider-overrides.<P>.topology conflicts with provider-overrides.<P>.mode: main-chat`; Negativfall: Cross-Scope wird **nicht** abgelehnt; Matrix-Test über alle **neun** Zellen der 3×3-Tabelle. Lauf: **rot — 6 failed**.
- [x] Step 2: `_validate_orchestrator_topology` implementieren: stdlib, stderr `ERROR: <config-path>: …`, `sys.exit(1)`; Aufruf in `_validate_config` **nach** `_validate_providers`, damit `sync` **und** `--validate` greifen.
- [x] Step 3: Lauf: **grün — 6 passed**; Subprozess-Nachweis: `sync.py` und `sync.py --validate` liefern je rc≠0 für eine widersprüchliche Temp-Config.
- [x] Step 4: Commit `feat: validate orchestrator topology conflicts hard and early`.

### Task 8: Flache Flags + Registrierungen 1–2 + AC-18-Test (AC-18)

**Agent:** developer
**Depends on:** 6
**Files:**
- Modify: `scripts/lib/variables.py`
- Create: `tests/test_orchestrator_topology_flags.py`
- Create: `tests/test_orchestrator_topology_conditionals.py`
**Interfaces:** Produces `variables.py::_topology_flags(topology, *, explicit, source)` mit `ORCH_TOPOLOGY`, `ORCH_TOPOLOGY_EXPLICIT`, `ORCH_TOPOLOGY_PRIMARY/_SUBAGENT/_HYBRID`, `ORCH_TOPOLOGY_SOURCE`; Consumes `TopologyResolution`.

- [x] Step 1: Flag-Test schreiben: genau eines von `_PRIMARY/_SUBAGENT/_HYBRID` ist `"true"` bei gesetztem Key, alle `"false"` bei `ORCH_TOPOLOGY == ""`; `ORCH_TOPOLOGY_EXPLICIT` ist nur bei Projekt-Scope `"true"` (Provider-Override zählt nicht). Lauf: **rot — 3 failed**.
- [x] Step 2: Conditional-Test schreiben: Probe-Template mit `{{#if ORCH_TOPOLOGY_EXPLICIT}}` rendert bei ungesetztem Key exakt den else-Zweig (inkl. verschachteltem `ROLE_ORCHESTRATOR_ACTIVE`), kein Zweig rendert doppelt; Mitgliedschaft in `strip_inactive_conditional_blocks`-Whitelist und `_FALSE_DEFAULT_CONDITIONALS` wird geprüft. Lauf: **rot — 4 failed** (zwei davon bleiben bis Task 9 rot).
- [x] Step 3: `_topology_flags` analog `_orch_mode_flags` implementieren; Präfix `ORCH_TOPOLOGY_` in die intern gebaute `conditional_vars`-Menge von `strip_inactive_conditional_blocks` aufnehmen; die vier `_EXPLICIT/_PRIMARY/_SUBAGENT/_HYBRID` in `_FALSE_DEFAULT_CONDITIONALS` eintragen (fail-closed).
- [x] Step 4: Lauf: Flag-Test **grün — 3 passed**; Conditional-Test **rot — 2 failed** (nur `_CONDITIONAL_FALSE_FLAGS`/`_BUILTIN_VARS`), dokumentiert als Übergabe an Task 9.
- [x] Step 5: Commit `feat: add flat orchestrator topology flags, fail-closed registered`.

### Task 9: Registrierungen 3–4 (Standalone + Placeholder-Ratchet) (AC-18)

**Agent:** junior-developer
**Depends on:** 8
**Files:**
- Modify: `scripts/lib/standalone.py`
- Modify: `scripts/lib/consistency/placeholders.py`
**Interfaces:** Produces literale `"false"`-Einträge für die vier Flags + Fallback `ORCH_TOPOLOGY: ""` in `_CONDITIONAL_FALSE_FLAGS`; `_BUILTIN_VARS`-Registrierung aller neuen Builder-Variablen; Consumes Task 8.

- [x] Step 1: Lauf als Rot-Beleg: `python3 -m pytest tests/test_orchestrator_topology_conditionals.py --basetemp="$PYTEST_BASETEMP"` → **2 failed** (beide Registrierungen fehlen).
- [x] Step 2: `_CONDITIONAL_FALSE_FLAGS` um die vier Flags plus `"ORCH_TOPOLOGY": ""` erweitern; `_BUILTIN_VARS` um alle neuen Builder-Variablen (kein Eintrag im shrink-only Ratchet).
- [x] Step 3: Lauf: **grün — 7 passed** im Conditional-Modul; `python3 -m pytest tests/test_standalone_render.py --basetemp="$PYTEST_BASETEMP"` → **0 failed** (unveränderte Anzahl).
- [x] Step 4: Commit `feat: register topology flags for standalone and placeholder checks`.

### Task 10: Provider-lose Global-Flags + provider-skopiertes Re-Resolver (IC-4)

**Agent:** developer
**Depends on:** 6, 8
**Files:**
- Modify: `scripts/lib/config.py`
- Modify: `scripts/lib/context.py`
- Modify: `scripts/lib/rules.py`
- Create: `tests/test_orchestrator_topology_global_flags.py`
**Interfaces:** Produces provider-losen Vertrag in `config.py::build_variables` (`ORCH_TOPOLOGY` = Projekt-Wert oder `""`, `ORCH_TOPOLOGY_EXPLICIT` nur Projekt-Scope) und provider-skopierte Überschreibung in `context.py::_build_managed_block` / `rules.py::_merged_rule_vars`; Consumes `topology_explicit`, `resolve_topology`.

- [x] Step 1: Test schreiben: `build_variables` ohne Provider liefert **nie** einen abgeleiteten Provider-Wert; `_merged_rule_vars(variables=None)` baut die Flags selbst; provider-skopierter Render überschreibt den globalen Wert (Override > Projekt). Lauf: **rot — 3 failed**.
- [x] Step 2: `build_variables` um den provider-losen Block ergänzen (Muster `REPO_CONTAINMENT_*`).
- [x] Step 3: In `_build_managed_block` und `_merged_rule_vars` die Topologie-Flags mit `provider=...` re-resolven und die globalen Werte überschreiben — exakt wie `ORCH_MODE_*`; Kommentar mit Präzedenz.
- [x] Step 4: Lauf: **grün — 3 passed**; `python3 scripts/sync.py --check` auf diesem Repo → rc 0 (nur bei explizit gesetztem Key darf sich etwas ändern; hier ist der Key ungesetzt ⇒ keine Drift).
- [x] Step 5: Commit `feat: resolve topology flags provider-scoped, never derived globally`.

### Task 11: Emission in `provider_transform` (AC-3 Transform-Teil, AC-5)

**Agent:** senior-developer
**Depends on:** 6, 10
**Files:**
- Modify: `scripts/lib/provider_transform.py`
- Modify: `config/ai-providers.yaml`
- Create: `tests/test_orchestrator_topology_emission.py`
**Interfaces:** Produces `mode: primary` nur bei `role == explicit_primary_role(...)` **und** `resolution.effective == "primary"`; Consumes `resolve_topology`.

- [x] Step 1: Test schreiben: Matrix über {`primary`, `subagent`, `hybrid`} × {opencode v1, opencode v2} — v2 `subagent` ⇒ `mode: subagent`, v1 `subagent` ⇒ kein `mode`, `primary`/`hybrid` (nur wenn effektiv `primary`) ⇒ `mode: primary`. Lauf: **rot — 5 failed**.
- [x] Step 2: Konjunktion in `_apply_agent_transform` ergänzen; Kommentar „Topologie ist kein zweiter emitted-Begriff" + Per-Provider-Fall begründen. Template-Fallback (`mode or template_fm["mode"]`) und Write-Scope-Lock bleiben unverändert an `mode == 'primary'` gebunden.
- [x] Step 3: `config/ai-providers.yaml` um einen Kommentar zur Topologie-Achse ergänzen (keine Datenänderung).
- [x] Step 4: Lauf: **grün — 5 passed**; bestehende Emissionstests (`tests/test_provider_*`-Familie, soweit betroffen) **0 failed**.
- [x] Step 5: Commit `feat: emit agent mode from resolved topology`.

### Task 12: Entry-Point + `emit_default_agent`-Faltung (AC-14, AC-20)

**Agent:** senior-developer
**Depends on:** 6, 11
**Files:**
- Modify: `scripts/lib/isolation.py`
- Modify: `scripts/lib/context.py`
- Create: `tests/test_orchestrator_topology_entrypoint.py`
**Interfaces:** Produces `_opencode_entry_point(..., *, topology=None)` und den Bool `emit_default_agent = role_emitted_for_provider(...) and topology.effective == "primary"`; Consumes `TopologyResolution` (einmal pro Provider im Aufrufer).

- [x] Step 1: Test schreiben: frische v2-Settings bei `subagent` ⇒ kein `default_agent`; verwalteter Wert rollt bei `primary → subagent` zurück; nutzereigener Wert bleibt erhalten (kein Auto-Delete). Lauf: **rot — 4 failed**.
- [x] Step 2: `_sync_opencode_runtime_gate` löst **einmal** `resolve_topology(..., mode=<aus _resolve_orch_mode>)` auf und reicht das Objekt an `_opencode_entry_point` weiter; dort Topologie-Konjunktion ergänzen. ActiveSet-Konjunkt unverändert.
- [x] Step 3: `_init_provider_settings_json` berechnet den **bestehenden** `emit_default_agent`-Bool als Konjunktion; `apply_settings_surface_shape`-Signatur bleibt **unverändert** (kein `topology_effective`).
- [x] Step 4: Lauf: **grün — 4 passed**; `tests/test_ac01_render_identity.py` **0 failed** (noch ohne neue Goldens).
- [x] Step 5: Commit `feat: fold topology into the existing default-agent decision`.

### Task 13: `_should_skip_role` nutzt das bestehende Prädikat (R1)

**Agent:** developer
**Depends on:** 6
**Files:**
- Modify: `scripts/lib/agent_sync.py`
- Create: `tests/test_orchestrator_topology_skip_role.py`
**Interfaces:** Produces genau eine Datei-Emissions-Entscheidung (`role_emitted_for_provider`); Consumes `active_set.py::role_emitted_for_provider` (Signatur unverändert).

- [x] Step 1: Test schreiben: `main-chat` (global und Override) ⇒ Rolle wird geskippt; `topology: subagent` ⇒ `orchestrator.md` wird **weiterhin** emittiert; Grep-/AST-Assertion: kein `ORCH_MODE_MAIN_CHAT`-Read mehr in `agent_sync.py`. Lauf: **rot — 3 failed**.
- [x] Step 2: `_should_skip_role` auf das Prädikat umstellen, Variablen-Read entfernen, Skip-Text anpassen (Grund kommt aus dem Modus, nicht aus der Variable).
- [x] Step 3: Lauf: **grün — 3 passed**; `tests/test_agent_sync*`-Familie **0 failed**.
- [x] Step 4: Commit `refactor: route orchestrator skip through one emission predicate`.

### Task 14: Konsistenz-Checker `consistency/topology.py` (AC-3, AC-7, AC-16, AC-20)

**Agent:** developer
**Depends on:** 6, 12
**Files:**
- Create: `scripts/lib/consistency/topology.py`
- Modify: `scripts/consistency-check.py`
- Create: `tests/test_orchestrator_topology_consistency.py`
**Interfaces:** Produces `check_orchestrator_topology(agent_meta_root, project_config) -> list[Finding]` mit den Check-IDs `degraded`, `hybrid-unverified`, `main-chat-supersedes`, `instances-clamped`, `unresolved-global-flags`, `default-agent-conflict`, `gate-inactive`; Consumes `resolve_topology` + emittierte Settings.

- [x] Step 1: Test schreiben: `degraded` genau einmal pro Provider/Lauf **nur** bei `degraded_from is not None`; unveränderte `no`-Zelle warnt nicht; Cross-Scope `main-chat` ⇒ genau eine `main-chat-supersedes`-WARN, rc bleibt 0; `gate-inactive` genau einmal, wenn das Gate gewollt ist und `_opencode_entry_point` `None` liefert; `default-agent-conflict` bei nutzereigenem Wert; mehrere Check-IDs dürfen im selben Lauf feuern. Lauf: **rot — 8 failed**.
- [x] Step 2: Checker implementieren — kein Schreiben, kein Exit, nur `Finding`s; Dedup **je Check-ID** (nicht je Lauf).
- [x] Step 3: In `consistency-check.py` registrieren; keine zweite WARNING pro ID.
- [x] Step 4: Lauf: **grün — 8 passed**; `python3 scripts/consistency-check.py` → keine neuen ERRORs, `--check`-rc unverändert.
- [x] Step 5: Commit `feat: warn loudly on topology degradation and inactive gate`.

### Task 15: Sync-Summary-Zeile (AC-19, OQ-4 = A)

**Agent:** developer
**Depends on:** 6, 10
**Files:**
- Modify: `scripts/lib/sync_pipeline.py`
- Create: `tests/test_topology_summary_line.py`
**Interfaces:** Produces `sync_pipeline.py::emit_topology_summary(config, provider_config, providers, log, *, mode, capabilities=None)`; Consumes `TopologyResolution.source == "derived"`.

- [x] Step 1: Test schreiben: exakter Text `topology: <effective> (derived from providers.<P>.primary-role)` und `topology: subagent (derived: active-set default)`; keine Zeile bei explizitem Key/Override; höchstens eine Zeile pro Provider. Lauf: **rot — 4 failed**.
- [x] Step 2: Funktion implementieren; Aufruf in `sync_pipeline` **nach** der Provider-Schleife und **vor** `log.finish`, ausschließlich bei `mode == "sync"`.
- [x] Step 3: Negativtest pinnen: `mode` `"check"`/`"validate"` ⇒ Funktion wird nicht aufgerufen, Ausgabe byte-identisch.
- [x] Step 4: Lauf: **grün — 5 passed**; `python3 scripts/sync.py --check` Ausgabe unverändert (keine neue INFO-Zeile).
- [x] Step 5: Commit `feat: summarize derived orchestrator topology once per sync`.

### Task 16: Golden-Fixtures „Rolle aktiv/inaktiv + Key unset" (AC-6, AC-18)

**Agent:** developer
**Depends on:** 11, 12
**Files:**
- Create: `tests/fixtures/topology-golden/*`
- Modify: `tests/test_ac01_render_identity.py`
**Interfaces:** Produces zwei byte-genaue Goldens (Rolle aktiv/inaktiv, Key ungesetzt); Consumes finale Transform-/Entry-Point-Form.

- [x] Step 1: Test erweitern: beide Fälle rendern exakt die heutigen Bytes; ein künstlich gesetzter Key (`ORCH_TOPOLOGY_EXPLICIT=true`) rendert **abweichend** (beweist, dass der Test nicht vakuum-grün ist). Lauf: **rot — 2 failed** (Fixtures fehlen).
- [x] Step 2: Goldens aus dem heutigen Stand erzeugen (nur diese zwei Fälle, per Eintrag; kein `--write`-Sammellauf).
- [x] Step 3: Lauf: **grün — 2 passed**; `python3 -m pytest tests/test_ac01_render_identity.py --basetemp="$PYTEST_BASETEMP"` → **0 failed**; `sync --check` bleibt rc 0.
- [x] Step 4: AC-01-Baseline **nur per Eintrag** für absichtlich geänderte Dateien anpassen; `settings.local.json` bleibt ausgeschlossen.
- [x] Step 5: Commit `test: freeze render identity for unset topology key`.

### Task 17: Concept-Doc + Doku-Test (AC-4 Text-Teil)

**Agent:** developer
**Depends on:** 11, 14
**Files:**
- Create: `docs/concepts/active/orchestrator-topology.md`
- Create: `tests/test_orchestrator_topology_docs.py`
**Interfaces:** Produces Concept-Doc mit drei Topologien, Support-/Degradierungsmatrix, `hybrid`-Deviationssatz (D2) und `P3, designed, not shipped`-Marker; Consumes Spec + Implementierungsstand.

- [x] Step 1: Text-Test schreiben: Doc existiert, nennt `primary`/`subagent`/`hybrid`, enthält den Deviationssatz, enthält den P3-Marker, verlinkt auf Spec und A2A-Rule. Lauf: **rot — 4 failed**.
- [x] Step 2: Doc schreiben; Matrix als Tabelle mit `UNVERIFIED ⇒ no` und Fail-safe-Ziel; explizit „kein Multi-Instanz-Versprechen in v1".
- [x] Step 3: Lauf: **grün — 4 passed**; Link-Check über das `consistency/docs.py`-Muster grün.
- [x] Step 4: Commit `docs: document orchestrator topology and its degradation rules`.

### Task 18: A2A-Rule + Agent-Zeilen + Cross-Link (AC-4 Link-Teil, R4)

**Agent:** developer
**Depends on:** 17
**Files:**
- Modify: `rules/1-generic/a2a-delegation-gates.md`
- Modify: `agents/1-generic/orchestrator.md`
- Modify: `agents/1-generic/_reference-agent.md`
- Modify: `docs/concepts/active/singleton-orchestrator-architecture.md`
**Interfaces:** Produces conditionalen Gate-Wortlaut (`{{#if ORCH_TOPOLOGY_EXPLICIT}}`) mit **wortgleichem** else-Zweig; Consumes `ORCH_TOPOLOGY`-Flags aus Task 8–10.

- [x] Step 1: Rot-Beleg: Render mit ungesetztem Key gegen den heutigen Byte-Stand vergleichen (Diff muss **leer** sein) — heute grün als Charakterisierung; nach der Änderung ist derselbe Vergleich der Regressionsschutz.
- [x] Step 2: Rule-Amendment: Topologie-Satz **inline** in bestehende Zeilen, `{{#if ORCH_TOPOLOGY_EXPLICIT}}` um den neuen Satz, else-Zweig wortgleich; kein `{{else}}` auf eigener Zeile; kein `ORCH_MAX_INSTANCES`-Platzhalter (P3).
- [x] Step 3: Orchestrator-/Reference-Agent-Zeilen: Position + Degradierungs-Hinweis, conditional, sonst byte-identisch; Cross-Link auf das Concept-Doc in der Singleton-Concept.
- [x] Step 4: Lauf: `python3 scripts/sync.py --check` → rc 0 und leerer Diff für ungesetzten Key; `python3 -m pytest tests/test_orchestrator_topology_docs.py --basetemp="$PYTEST_BASETEMP"` → **0 failed**.
- [x] Step 5: Commit `docs: state orchestrator position conditionally in gate rules`.

### Task 19: CHANGELOG

**Agent:** junior-developer
**Depends on:** 18
**Files:**
- Modify: `CHANGELOG.md`
**Interfaces:** Produces einen Eintrag „Orchestrator-Topologie (v1)"; Consumes abgeschlossene Tasks 1–18.

- [x] Step 1: Eintrag unter `Unreleased` ergänzen: neuer Key, Builder-Default, laute Degradierung, Evidenz-Regel, Hinweis „P3 (Multi-Instanz) folgt".
- [x] Step 2: Lauf: `python3 -m pytest tests/test_changelog*` bzw. der bestehende Changelog-Guard → **0 failed** (kein Formatbruch).
- [x] Step 3: Commit `docs: note orchestrator topology v1 in changelog`.

---

## Exit-Kriterien (v1)

v1 ist fertig, wenn **alle** folgenden Punkte erfüllt sind:

1. **DoD-ACs grün:** AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-13, AC-14,
   AC-15, AC-16, AC-18, AC-19, AC-20 sowie die **P1-Zeilen** von AC-17.
2. **P0-Gate erfüllt:** alle fünf Probes (`P0-1`…`P0-5`) haben im
   Evidenz-Dokument entweder einen vollständigen Ergebnis-Record **oder** die
   wörtliche Zeile `not run — CLI unavailable` mit Grund; kein `yes` ohne alle
   drei Gate-Bedingungen; `N` ist gemessen, nicht gepinnt.
3. **`sync --check` byte-identisch** auf einem unveränderten Projekt ohne
   `orchestrator.topology` (inkl. des Fail-closed-Verhaltens der vier
   Conditional-Registrierungen); `--validate` rc 0.
4. **Volle Suite:** `python3 -m pytest tests/ --basetemp="$PYTEST_BASETEMP"`
   ohne neue Fehlschläge. Laufzeit ~3,4 h lokal — **CI shardet** die Suite; der
   lokale Nachweis darf über die berührten Shards geführt werden, das Ergebnis
   muss aber pro Shard dokumentiert sein.
5. **AC-01/Golden-Regeln:** Baseline-Anpassungen ausschließlich **per Eintrag**
   für Dateien, deren Bytes sich absichtlich ändern; **kein** `--write`-Sammellauf;
   `settings.local.json` (host-lokal) bleibt aus AC-01 ausgeschlossen.
6. **Kein Merge, kein Push durch den Executor;** Branch-Management liegt bei `git`.

**Explizit nicht in v1 (P3-only, nicht vergessen):** AC-8, AC-9, AC-10, AC-11,
AC-12 und die **P3-Zeilen** von AC-17 (`singleton: false`, `singleton` × N>1,
`primary` × N>1), `max-instances`/`singleton`, `orchestrator_id`, Guard-Audit,
Zustands-Namespaces, `singleton-redundant`-INFO.

## Risiken

| # | Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| R1 | Zweite Skip-Stelle bleibt (`ORCH_MODE_MAIN_CHAT` + Topologie) | Orchestrator verschwindet still oder doppelt gepruned | Task 13 stellt auf das **bestehende** Prädikat um; Grep-/AST-Assertion „genau eine Funktion entscheidet" |
| R2 | `default_agent` ↔ Gate-Deny-Kopplung, zweiter Schreiber | Nutzer verliert Builder-Default oder Schreibblockade | `emit_default_agent`-Faltung (Task 12), Signatur unverändert; `gate-inactive`-WARN (Task 14) |
| R4 | Byte-Identität bricht durch unbedingte Textänderung oder `{{else}}` auf eigener Zeile | Jede Consumer-Projekt meldet Drift | Inline-Marker + wortgleicher else-Zweig (Task 18); Goldens (Task 16); AC-18-Test (Task 8/9) |
| R10 | Matrix-Zellen werden als Freigabe gelesen, obwohl `UNVERIFIED` | Spec verspricht `hybrid`/N>1 ohne Evidenz | Drei-Bedingungs-Gate in Task 3/4; Baseline-Transkription K-2 |
| R11 | Probe-CLIs fehlen lokal | P0 sieht „unvollständig" aus | `not run — CLI unavailable` ist gültiges Ergebnis; Zelle bleibt `no`, keine WARNING |
| R12 | Rebaseline per `--write` | AC-01-Baseline verwässert, Regressionsschutz weg | Global Constraint + Exit-Kriterium 5; nur zwei neue Goldens (Task 16) |

## Annahmen und Self-Review

**Annahmen** (wenn falsch, wird der betroffene Task neu geschnitten — nicht die Spec):

1. `scripts/lib/topology.py` bleibt ein Blattmodul ohne Import von `variables.py`
   (kein zweiter Mode-Resolver); `mode` kommt aufgelöst herein.
2. Die Spec-Matrix „Stand vor P0" ist die normative Baseline; Zell-Upgrades sind
   ausschließlich Evidenz-getrieben.
3. `provider-capabilities.yaml` ist die einzige Provider-Wahrheit für die
   Topologie-Achse; `providers.explicit_primary_role` bleibt der einzige
   `primary-role`-Read.
4. Golden-Fixtures werden erst nach Task 11/12 erzeugt (K-3).
5. `build_variables`/`_build_managed_block`/`_merged_rule_vars` sind die realen
   Träger der provider-losen bzw. provider-skopierten Flags (K-1).

**Self-Review:**

- **Agenten:** Jeder Task hat genau eine Rolle aus {`junior-developer`,
  `developer`, `senior-developer`}. Kein Task ist ohne Agent.
- **Datei-Ownership:** Innerhalb jeder Parallel-Gruppe berührt kein Task eine
  Datei eines anderen. Gruppen:
  **G1** {1, 2, 5}; **G2** {3}; **G3** {4, 6}; **G4** {7, 8, 13}; **G5** {9};
  **G6** {10, 11}; **G7** {12}; **G8** {14, 15}; **G9** {16}; **G10** {17};
  **G11** {18}; **G12** {19}. `config.py` liegt nur in 7 und 10 (verschiedene
  Gruppen), `context.py` nur in 10 und 12, `provider-capabilities.yaml` nur in 1
  und 3 — jeweils sequenziell, nie parallel.
- **AC-Abdeckung:** Jedes v1-AC ist mindestens einem Task zugeordnet
  (Matrix unten). Kein v1-AC ist ungetestet.
- **P3-Abgrenzung:** AC-8…AC-12 und die P3-Zeilen von AC-17 sind namentlich als
  „P3-only" markiert (Exit-Kriterien), nicht stillschweigend entfernt.
- **Keine neue offene Frage:** Der Plan fügt der Spec **0** OQ hinzu; K-1…K-4
  sind Präzisierungen gegen den Checkout, keine Entscheidungsbedarfe.

| AC | Tasks |
|---|---|
| AC-1 | 5, 7 |
| AC-2 | 6, 7 |
| AC-3 | 11, 14 |
| AC-4 | 17, 18 |
| AC-5 | 5, 6, 7, 11 |
| AC-6 | 12, 16 |
| AC-7 | 14 |
| AC-13 | 1 |
| AC-14 | 12, 14, 16 |
| AC-15 | 1, 4, 6 |
| AC-16 | 4, 14 |
| AC-17 (P1) | 7 |
| AC-18 | 8, 9, 16 |
| AC-19 | 15 |
| AC-20 | 12, 14 |
| P0-Gate | 2, 3, 4 |

---

## Ausführungsnachweis (Ledger)

v1 wurde auf `feat/orchestrator-topology-v1` in 19 Tasks implementiert (20 Commits
inkl. Marker-Fix) und als `44f39ebc` nach `main` gemerged. Die Commit-Titel unten
sind die je Task festgelegten Commit-Steps; Fix-Commit und Merge sind mit Hash
belegt.

| Task | Commit |
|---|---|
| 1 | `feat: add orchestrator topology capability structures` |
| 2 | `feat: add read-only topology probe harness` |
| 3 | `docs: record orchestrator topology probe evidence` |
| 4 | `test: enforce topology evidence upgrade rule` |
| 5 | `feat: declare orchestrator topology in project config schema` |
| 6 | `feat: add orchestrator topology resolver` |
| 7 | `feat: validate orchestrator topology conflicts hard and early` |
| 8 | `feat: add flat orchestrator topology flags, fail-closed registered` |
| 9 | `feat: register topology flags for standalone and placeholder checks` |
| 10 | `feat: resolve topology flags provider-scoped, never derived globally` |
| 11 | `feat: emit agent mode from resolved topology` |
| 12 | `feat: fold topology into the existing default-agent decision` |
| 13 | `refactor: route orchestrator skip through one emission predicate` |
| 14 | `feat: warn loudly on topology degradation and inactive gate` |
| 15 | `feat: summarize derived orchestrator topology once per sync` |
| 16 | `test: freeze render identity for unset topology key` |
| 17 | `docs: document orchestrator topology and its degradation rules` |
| 18 | `docs: state orchestrator position conditionally in gate rules` |
| 19 | `docs: note orchestrator topology v1 in changelog` |
| Fix | `e8ba3414` — Marker-Form-Fix (Task 18) |

### Evidenz

- **Testläufe über die Runden:** 257 + 422 + 40 + 451 + 110 Tests grün.
- **Byte-Identität (AC-6):** `sync --check` → rc 0; `topology-golden` unverändert,
  Byte-Identität in allen vier Zuständen bewiesen.
- **Config:** `sync --validate` → rc 0.
- **Governance:** `consistency-check` PASS.
- **AC-01:** 9 Einträge per Eintrag neu gepinnt, ohne `--write`-Sammellauf.
- **P0-Gate:** fünf Probes ausgeführt — **0 `evidence`, 3 `inconclusive`,
  2 `not run — CLI unavailable`**; **keine Zelle hochgestuft**; Matrix unverändert
  **25 datenabgeleitet / 15 `UNVERIFIED ⇒ no`**. Quelle:
  `docs/spikes/2026-11-03-issue-1077-topology-probe.md`.

### Abweichungen

- **Task 4 — Spike-Dateiname:** zuerst als `2026-11-04-…` angelegt, dann auf den normativen Namen `2026-11-03-…` umbenannt.
- **Task 1 — Branch:** der Commit landete versehentlich auf `main` und wurde auf den Feature-Branch verschoben; `main` wurde auf `origin/main` zurückgesetzt (es war kein Push erfolgt).
- **Task 18 — A2A-Markerform:** die erste Form nutzte Inline-Marker über Zeilengrenzen und wurde von `test_no_role_routes_in_templates.py` abgelehnt; der Fix `e8ba3414` verwendet Block-Form-Marker und hält den else-Zweig byte-identisch.
- **Task 16 — Fixture-Registrierung:** die `topology-golden`-Fixtures stehen nicht in `_FIXTURE_TREES`; sie werden durch ihre eigenen Tests abgesichert.
- **P0 — `hybrid`:** in v1 nirgends gewährt (Evidenz-Gate); die Probes brauchen interaktive Sessions, das Upgrade bleibt ein expliziter Follow-up.
- **P3 — delivered:** Multi-Instanz (AC-8…AC-12) ist in Issue #1077 umgesetzt.
- **Test 16 — P4-Form:** die vier Flag-Kombinationsfälle üben die prospektive P4-Regelform über die reale Conditional-Engine.
