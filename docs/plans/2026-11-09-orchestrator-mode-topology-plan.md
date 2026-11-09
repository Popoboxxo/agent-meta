---
pipeline_stages:
  implement: 1
status: DRAFT
revision: 4
date: 2026-11-09
base-commit: aaed14c2
branch: docs/1190-orchestrator-topology
trace:
  - SPEC-orchestrator-mode-topology-2026-11-09
  - SPEC-orchestrator-topology-2026-11-03
  - issue-1190
---

# Orchestrator `mode` × `topology` — Umsetzungsplan (#1190)

> **Status: DRAFT** · **Revision: 4** · Issue **#1190** · Klasse **XL / Architectural** · Datum 2026-11-09
> Review 1 (`docs/reviews/2026-11-09-orchestrator-mode-topology-review.md`, vor Revision 2) ist
> vollständig eingearbeitet; Nachweis in §16 „Review-Auflösung (2026-11-09)".
> Re-Review 1 (`docs/reviews/2026-11-09-orchestrator-mode-topology-rereview.md`, vor Revision 3) ist
> mit RVW2-1190-01…-13 ebenfalls eingearbeitet; Nachweis in §16, Block „Re-Review 1".
> **Revision 4** arbeitet die drei **User-Entscheidungen vom 2026-11-09** ein (`DECIDED 2026-11-09`:
> D-OQ1, D-OQ2, D-OQ3 — Spec §14). Neu: Positionsmodell-Task (T18), Positions-Paritätstests für
> Opencode (T19), explizite Deklaration `orchestrator.topology: subagent` als eigener Umsetzungsschritt
> **nach** dem Code-Fix (T20) und daraus folgend das Abschluss-Gate als T21; Szenarien `100`–`104` auf
> die neuen Positionen umgestellt.
> Die Spec steht auf `Status: DRAFT`; der Plan startet erst nach `Status: APPROVED`
> (Master-Rule `spec-plan-workflow`).
> **spec-id:** `SPEC-orchestrator-mode-topology-2026-11-09`
> **Normativer Vorgänger:** `SPEC-orchestrator-topology-2026-11-03`
> (`docs/specs/2026-11-04-orchestrator-topology-spec.md`, D1–D10, AC-1…AC-20 — bleibt gültig,
> wird **nicht** neu aufgerollt)
> **Design-Quelle:** `docs/specs/2026-11-03-orchestrator-topology-design.md` (Rev. 4)
> **Entscheidungen:** D-Q1…D-Q5 und D-OQ1…D-OQ3 der Spec (§4, §14), neun Lücken G1…G9 (§5),
> **37 ACs** (§8)

**Spec:** docs/specs/2026-11-09-orchestrator-mode-topology-design.md

**Goal:** Emission und alle Render-Seams — Rules, Context, Agent-Templates sowie Singleton-Block und
Einstiegshinweis — verzweigen auf **eine** effektive Orchestrator-Topologie (dieselbe
`resolve_topology`-Auflösung, derselbe per-Sync-`ActiveSet`), der `# CRITICAL GATE` nennt die
Position statt einer unausführbaren Pflicht, und die drei neuen Checks diagnostizieren `main-chat` ×
abgeleitetes `primary`, den Entry-Point-Mismatch und das wirkungslose `direct-dispatch-enabled` —
jeweils ohne rc≠0 auf gültigen Configs. Zusätzlich (`DECIDED 2026-11-09`) werden die **drei
Positionen** POS-1/POS-2/POS-3 dokumentiert und je Position getestet, und dieses Repo deklariert
seine Position am Ende **explizit** als `strict × subagent` (`orchestrator.topology: subagent`),
sodass „derived vs. declared" auch hier keine Divergenz mehr erzeugt.

**Architecture:** Ein neuer reiner Helfer `_effective_topology_flags` in `variables.py` erzeugt fünf
Bool- und zwei String-Flags aus einer `TopologyResolution`; ein zweiter Helfer
`_provider_topology_flags` reicht die bereits aufgelöste Position **und** den per-Sync-`ActiveSet` an
die Seams weiter (kein vierter Resolver, keine Neuauflösung pro Aufruf). Die Templates verzweigen
dreiwertig (`EFFECTIVE_PRIMARY` → `EFFECTIVE_EXPLICIT` → historischer else-Zweig). Der v2-Reconcile
bekommt `topology=` als Durchreich-Parameter. Neue Diagnostik ist additiv in `consistency/` und
WARNING/INFO-only. Die **Position** ist keine Config-Achse, sondern eine Emission-/Render-Ableitung
aus `mode` + `effective` (Spec §3.8.2); die Deklaration dieses Repos ist eine einzelne Config-Zeile
plus Regeneration (T20) und wird als letzter Schritt vor dem Abschluss-Gate gefahren.

**Tech Stack:** Python 3.9 (stdlib; einzige dokumentierte Ausnahme PyYAML,
`docs/adr/0001-pyyaml-runtime-ausnahme.md`), Markdown-Templates mit `{{#if}}`-Conditionals, YAML-
Frontmatter, `pytest`, `python3 scripts/sync.py`.

**Voraussetzungen (vor T1 zu erfüllen):**

1. Spec auf `Status: APPROVED` (heute `DRAFT`, `docs/specs/2026-11-09-orchestrator-mode-topology-design.md:3`).
   Solange sie `DRAFT` ist, meldet `consistency/spec_plan.py` den **beabsichtigten** ERROR
   `spec_plan_approval_marker` für diesen Plan (er nennt `**Spec:**` wörtlich und hat Tasks).
2. Branch `docs/1190-orchestrator-topology` (HEAD `aaed14c2`) — **nie** `main`/`master`.
3. **M0 ist noch nicht gelaufen.** Die Baseline wird in M0 erzeugt und im Plan dokumentiert
   (Exit-Code von `--validate`, `--check`, Topologie-Testfamilie). Zitate auf Baseline-Dateien
   entstehen erst **nach** M0; es gibt keine vorab eingefrorene Baseline.
4. K-1 und K-2 sind mit Spec Rev. 2 erledigt (§13) — keine offene Entscheidung vor T1.
5. Die drei User-Entscheidungen vom 2026-11-09 sind in Spec Rev. 4 eingearbeitet (`DECIDED 2026-11-09`:
   D-OQ1/D-OQ2/D-OQ3). **T20 ist die einzige Config-Änderung dieses Plans** und läuft ausdrücklich
   **nach** T19 (Code-Fix); sie ist kein Bestandteil der Spec (Spec §7).

**Größe:** 21 Tasks in 12 Meilensteinen. S = ≤40 LOC / ≤2 h, M = ≤1 Tag / ≤150 LOC,
L = >1 Tag. Summe (Rev. 4): **10 × S** (T1, T2, T3, T9, T10, T11, T12, T13, T20, T21),
**10 × M** (T4, T5, T6, T7, T8, T14, T16, T17, T18, T19), **1 × L** (T15).

---

## 1. Zielbild

1. `mode` und `topology` werden an **allen** Render-Seams gleich aufgelöst: die *effektive*
   Topologie (`resolve_topology(...)`) steuert Emission, Rules, Context, Agent-Templates,
   Singleton-Block und Einstiegshinweis — der deklarierte Wert bleibt als Audit-Aussage erhalten.
2. Der `# CRITICAL GATE`-Text spricht die Topologie-Vorbedingung aus: unter `primary` nennt die
   Regel den Session-Einstieg und den Ausweg (`orchestrator.mode: main-chat`) statt einer
   unausführbaren Pflicht — ohne die auf Claude falsche Behauptung „kein Spawn-Kanal" (Spec §5-G1).
3. Der unausführbare Zustand wird diagnostizierbar: zwei WARNINGs und ein INFO benennen
   `main-chat` + abgeleitetes `primary`, den Entry-Point-Mismatch und das unter `main-chat`
   wirkungslose `direct-dispatch-enabled` — ohne rc≠0 auf gültigen Configs.
4. Der v2-Reconcile übergibt `topology` an `_opencode_entry_point`, sodass `subagent` auf v2
   **kein** `permissions[]`-Deny schreibt und statt einer gegenläufigen Remediation genau eine
   `gate-inactive`-Warnung entsteht.
5. Die Entscheidungsmatrix (4 Surfaces × 6 Kombinationen) liegt testbar dokumentiert vor, die elf
   Doku-Widersprüche sind einzeln aufgelöst, und der Default-Render bleibt für `topology`
   ungesetzt ∧ `effective == "subagent"` byte-identisch; abgeleitetes `primary` ist die
   beabsichtigte Änderung mit eigener Golden-Fixture.
6. (`DECIDED 2026-11-09`) Die drei **Positionen** POS-1/POS-2/POS-3 sind definiert, gemappt
   (`mode × topology → Position`) und je Position getestet; dieses Repo deklariert am Ende
   `strict × subagent` **explizit** — die Position mit 1 Hop, ehrlichem `gate-inactive` und ohne
   Abwertung gegenüber `primary`, das als dritte, optionale Position gleichwertig dokumentiert bleibt.

---

## Global Constraints

- **Byte-Identität des Defaults ist Invariante, nicht Ergebnis — aber nur für `topology`
  ungesetzt ∧ `effective == "subagent"`.** Kein `topology`-Key **und** alle aktiven Renderer lösen
  `subagent` auf ⇒ dieselbe Emission wie heute (`scripts/lib/provider_transform.py:488-499`,
  `scripts/lib/isolation.py:857-862`); `sync --check` bleibt rc 0 (AC-16/AC-27). **Abgeleitetes**
  `primary` (Key ungesetzt, `effective == "primary"`, in diesem Repo der Fall) ist dagegen die
  **beabsichtigte** Änderung aus AC-17 und hat eine eigene Golden-Fixture; ein **deklariertes**
  `topology: primary` ebenso, und ein **deklariertes** `topology: subagent` (Zustand dieses Repos ab
  T20) ebenfalls (§8, AC-36).
- **Ein Resolver.** Ausschließlich `scripts/lib/topology.py::resolve_topology` (Zeile 186) und
  `topology_explicit` (Zeile 101). Kein vierter Resolver (Risiko R-3 der Spec, §9.2).
- **Ein `ActiveSet` pro Provider und Lauf.** `_provider_topology_flags` bekommt `active_set` als
  **Pflicht-Keyword**, löst den `ActiveSet` nie selbst auf (kein `compute_active_set` im Helfer) und
  bildet die Position über `resolve_topology` genau einmal pro Aufruf. Der Context-Seam liegt in
  **Stage 4**:
  `sync_pipeline._sync_stage_contexts` (`:732-737`, Aufruf von `sync_context_for_provider` bei
  `:788-790`) erhält `active_set` als **Pflicht-Keyword** (kein Default) von
  `cli_commands.py:1543` (`ctx.active_set`, gesetzt `:964`); `sync_context_for_provider` und
  `_dispatch_context_strategy` reichen ihn weiter. `_sync_stage_per_provider` (`:1335-1446`) reicht
  denselben Set an Emission, Rules und den Reconcile (T14). Ohne Bindung fällt `_derive`
  (`topology.py:135-140`) auf die leere Menge zurück (`rules.py:281-288`, `context.py:2575-2581`).
- **Die provider-lose Basis ist nicht autoritativ (RVW2-1190-09).** `config._build_orch_variables`
  (`:2013-2037`) füllt die neuen Flags einmal provider-los; dieser Wert ist nur der Ausgangspunkt.
  Kein Render-Seam darf `ORCH_TOPOLOGY_EFFECTIVE*` aus dieser Basis lesen, ohne dass
  `_provider_topology_flags` ihn überschreibt (Ratchet-Test, AC-30).
- **Positions-Parität statt Einheitslogik (`DECIDED 2026-11-09`, D-OQ2).** Jede Position wird
  **einzeln** generiert und getestet (`POS-1` Main-Chat, `POS-2` Subagent, `POS-3` Session-Einstieg).
  Unterschiede entstehen ausschließlich über Capability-Flags und Config-Keys — kein
  `if provider == "…"`, keine gemeinsame Sonderbehandlung mehrerer Provider. Keine Position wird als
  „nicht empfohlen" markiert.
- **Dieses Repo deklariert seine Position explizit — aber erst in T20 (`DECIDED 2026-11-09`, D-OQ1).**
  Die Zeile `orchestrator.topology: subagent` in `.meta-config/project.yaml` ist die **einzige**
  Config-Änderung des Plans. Sie läuft **nach** dem Code-Fix (T19), wird regeneriert, committet und
  ist rückrollbar (Zeile entfernen ⇒ Ableitung greift wieder). Bis T20 bleibt die Position abgeleitet.
- **Regeneration ist ein Task-Schritt, kein Nachgedanke.** Jeder Task, der gerenderte Artefakte
  ändert (T4–T10, T14, T19, T20), endet mit `python3 scripts/sync.py`, Diff-Prüfung der regenerierten
  Dateien und Commit. Die `--check`-Gates von M1/M3/M9/M10 und T21 sind erst **nach** dieser
  Regeneration einfahrbar (AC-31).
- **Provider-Agnostik.** Verzweigung nur über Flags/`effective`/Capability-Daten; kein
  `if provider == "..."`, kein Provider-Name im Fließtext einer neuen Bedingung
  (`config/provider-capabilities.yaml:206-209`, `:263-266` sind die einzige Wahrheit).
- **`resolve_topology` bleibt mode-agnostisch.** `mode` beeinflusst die Position nie
  (`scripts/lib/topology.py:196-206`); die Negativ-Invariante ist AC-21.
- **Python 3.9, stdlib only** (PyYAML = dokumentierte Ausnahme,
  `docs/adr/0001-pyyaml-runtime-ausnahme.md`); `from __future__ import annotations` in neuen
  Modulen, keine PEP-604-Annotationen ohne Future-Import.
- **Fail-closed-Registrierung an vier Stellen** für jedes neue Bool-Flag (AC-15):
  `_FALSE_DEFAULT_CONDITIONALS` (`scripts/lib/variables.py:54-73`), Präfix-/Statik-Whitelist in
  `strip_inactive_conditional_blocks` (`:556-598`), `standalone._CONDITIONAL_FALSE_FLAGS`
  (`scripts/lib/standalone.py:130-191`), `consistency/placeholders._BUILTIN_VARS`
  (`scripts/lib/consistency/placeholders.py:70-78`).
- **String-Flags sind keine Conditionals.** `ORCH_TOPOLOGY` / `ORCH_TOPOLOGY_SOURCE` /
  `ORCH_TOPOLOGY_EFFECTIVE` dürfen **nie** in `{{#if}}` stehen (Muster-Warnung
  `scripts/lib/variables.py:95-97`).
- **`# CRITICAL GATE` bleibt ein Heading** mit Text `CRITICAL GATE` oder `CRITICAL GATE <suffix>`
  — sonst bricht der Compact-Pfad (`scripts/lib/context.py:2141-2167`,
  `config/context-anchors.yaml:82-89`) und #1182 verschärft sich.
- **Severity-Disziplin:** neue Findings sind WARNING/INFO, rc bleibt 0 (AC-2 unverändert hart).
- **Doku-Sprache:** Plan/Doku Deutsch, Code/Commits/Tests Englisch; Commit-Messages
  Conventional Commits, ≤72 Zeichen, ohne BOM, kein Push/Tag/Branch durch den Executor.
- **Testkommando:** `python3 -m pytest <pfad> --basetemp="$PYTEST_BASETEMP"`; `rtk pytest` ist
  defekt und wird nicht verwendet.
- **Kein `isolation: "worktree"`** — Arbeit direkt im Projektverzeichnis.

---

## File Structure

### Produktion

| Datei | neu/ändern | Zweck | Task |
|---|---|---|---|
| `scripts/lib/variables.py` | ändern | `_effective_topology_flags`, `_provider_topology_flags`, `_TOPOLOGY_EFFECTIVE_CONDITIONAL_FLAGS`, `_FALSE_DEFAULT_CONDITIONALS`, Strip-Whitelist (`:54-93`, `:311-356`, `:575-598`) | T1, T2 |
| `scripts/lib/config.py` | ändern | provider-lose Basiswerte der neuen Flags in `_build_orch_variables` (`:2013-2037`) | T3 |
| `scripts/lib/rules.py` | ändern | provider-skopierte Effektiv-Flags in `_merged_rule_vars` (`:238-293`); `active_set`-Durchreichung in `sync_rules` (`:574-585`) und `sync_embedded_rule_files` (`:471`) | T4 |
| `scripts/lib/context.py` | ändern | provider-skopierte Effektiv-Flags in `_build_managed_block` (`:2563-2586`, gelesen aus `variables`); `active_set` als Pflicht-Keyword durch `sync_context_for_provider` (`:1593-1603`) → `_dispatch_context_strategy` (`:1391-1427`) → `_sync_opencode_context` (`:890`), `_sync_managed_block_context` (`:799`), `_sync_continue_context` (`:1145`); neuer Helfer `_position_aware_agent_hints` (Hinweis-Entscheidung); Shared-Detektion `_shared_context_users` (`:2246`) | T5, T10 |
| `scripts/lib/agent_sync.py` | ändern | `_build_provider_vars` + `active_set` (`:489-554`, Aufruf `:1427-1430`); Singleton-Block (`:969-986`) | T6, T9 |
| `scripts/lib/sync_pipeline.py` | ändern | Override-Zweig um Topologie-Flags (`:1405-1431`); `_sync_stage_contexts` erhält `active_set` und mischt die Provider-Flags (`:732-737`, `:788-790`); per-Provider-Resolution + `topology=` an den Reconcile (`:1598-1602`) | T5, T6, T14 |
| `scripts/lib/cli_commands.py` | ändern | `active_set=ctx.active_set` an `_sync_stage_contexts` (`:1543`, `:964`); `topology=` im `--test-generated`-Reconcile-Aufruf (`:344-348`) | T5, T14 |
| `rules/1-generic/use-orchestrator.md` | ändern | G1-Gate-Vorbedingung im `# CRITICAL GATE` (`:1-24`) | T7 |
| `agents/1-generic/orchestrator.md` | ändern | Dreiweg-Zweig statt `ORCH_TOPOLOGY_EXPLICIT` (`:19`) | T8 |
| `agents/1-generic/_reference-agent.md` | ändern | derselbe Wortlaut (`:24`) | T8 |
| `rules/1-generic/a2a-delegation-gates.md` | ändern | G2-Wortlaut auf `EFFECTIVE_*` (`:6-19`) | T8 |
| `scripts/lib/agents.py` | ändern | `build_agent_hints` erhält nur den `position`-Parameter (Textbausteine `:171-179`); **keine** Provider-/Ziel-Entscheidung im Rumpf | T10 |
| `scripts/lib/consistency/topology.py` | ändern | zwei neue WARNINGs (`:62-71`, `:186-403`) | T11, T12 |
| `scripts/lib/consistency/orchestrator_strict.py` | ändern | INFO `direct-dispatch-inert` (`:36-39`, `:182-250`) | T13 |
| `scripts/lib/isolation.py` | ändern | `reconcile_opencode_surface_gate(..., topology=None)` (`:1751-1761`); Durchreichung an `_opencode_entry_point` (`:1826-1830`) und `_opencode_v2_gate_permissions` (`:1840-1843`, `:1457`); ursachenbewusste Warnungen (`:1351-1405`, `:1881-1889`) | T14 |
| `scripts/lib/provider_transform.py` | prüfen, nur bei rotem Test ändern | Positions-Parität: Frontmatter-`mode` fällt bei `effective != "primary"` auf `subagent` (`:494-499`, `:1052`, `:1298`); `main-chat` emittiert die Rolle nicht | T19 |
| `.meta-config/project.yaml` | ändern | **eine** Zeile `orchestrator.topology: subagent` (nach `:311`) — explizite Deklaration dieses Repos, rückrollbar | T20 |

### Tests

| Datei | neu/ändern | Zweck | Task |
|---|---|---|---|
| `tests/test_orchestrator_topology_effective_flags.py` | neu | sieben neue Flags, Invariante „nie `none`", Global-Basis | T1, T3 |
| `tests/test_orchestrator_topology_conditionals.py` | ändern | Registrierung an vier Stellen, Ratchet-Test | T2 |
| `tests/test_orchestrator_topology_render_parity.py` | neu | Provider-Parität Rules/Context/Agents + `sync_pipeline`-Override | T4, T5, T6 |
| `tests/test_use_orchestrator_topology_rendering.py` | neu | G1 unter `primary`/`subagent`, Grep-Assertion AC-14 | T7 |
| `tests/test_orchestrator_template_topology_wording.py` | neu | AC-17 (`orchestrator.md`, `_reference-agent.md`, a2a) | T8 |
| `tests/test_singleton_block_topology.py` | neu | G4 drei Varianten | T9 |
| `tests/test_entry_hint_topology.py` | neu | G5 + `main-chat` unverändert | T10 |
| `tests/test_orchestrator_topology_checks.py` | neu | drei neue Check-IDs inkl. Negativfälle | T11, T12, T13 |
| `tests/test_isolation_v2_topology_reconcile.py` | neu | G7 v2 + `subagent`, kein Deny, eine Warnung | T14 |
| `tests/test_opencode_positions.py` | neu | Positions-Parität: je ein Test für POS-1, POS-2, POS-3 (v1 + v2) | T19 |
| `tests/test_orchestrator_mode_topology_matrix.py` | neu | 24 Zellen × Surfaces (Szenario-Logik) | T15, T17 |
| `tests/test_orchestrator_topology_docs.py` | ändern | Matrix-Doc-Test (AC-6/7/8/10/11) + 11-Befund-Test + Positions-/Mapping-Test + #1182-Bedingung | T15, T16, T18 |
| `tests/test_provider_transform_topology_generic.py` | neu | Claude/Gemini-Emission (AC-24) | T15 |
| `tests/scenarios/registry.md` | ändern | Einträge `100`–`104` (`:46-132`, `:176`), `103` als `BLOCKED (#1182)` | T17 |
| `tests/scenarios/configs/100-strict-subagent-opencode-v2.project.yaml`, `101-strict-primary-opencode-v2.project.yaml`, `102-main-chat-derived-primary.project.yaml`, `104-claude-strict-subagent.project.yaml` | neu | je ein ausführbares Szenario (`100`=POS-2 Default, `101`=POS-3, `102`=POS-1, `104`=Claude POS-2) | T17 |
| `tests/scenarios/configs/blocked-103-advisory-subagent.project.yaml` | neu | Szenario `103` (POS-2), **außerhalb** des `10*`-Matches (blockiert durch #1182) | T17 |
| `tests/scenarios/asserts/100-strict-subagent-opencode-v2.sh` … `104-claude-strict-subagent.sh` | neu | konkrete Assertions je Szenario | T17 |
| `tests/scenarios/asserts/blocked-103-advisory-subagent.sh` | neu | Assertion des `BLOCKED`-Szenarios (nicht ausgeführt) | T17 |

### Doku

| Datei | neu/ändern | Zweck | Task |
|---|---|---|---|
| `docs/concepts/active/orchestrator-topology.md` | ändern | 24-Zellen-Matrix **mit Positions-Spalte**, Derived-Zeile, P3-Status (`:75-79`, `:91-96`); Positionsmodell POS-1/POS-2/POS-3 als eigener Abschnitt | T15, T18 |
| `docs/adr/0002-orchestrator-mode-topology.md` | neu | ADR (MADR-minimal, D-Q1…D-Q5 **und** D-OQ1…D-OQ3) | T16 |
| `README.md` | ändern | Key-Tabelle + Mermaid (`:210`, `:410-419`): zwei Opencode-Positionen statt einer Aussage | T16, T18 |
| `CLAUDE.md` | ändern | Singleton-Satz qualifizieren (`:102`) | T16 |
| `AGENTS.md` | **nicht** editieren | generiert; Änderung kommt über G1 | T7 |
| `.claude/rules/use-orchestrator.md` | **nicht** editieren | generiert; Änderung kommt über T7 | T7 |
| `docs/CODEBASE_OVERVIEW.md` | ändern | §13.2 qualifizieren (`:1724-1727`); beide Opencode-Positionen benennen | T16, T18 |
| `docs/concepts/active/singleton-orchestrator-architecture.md` | ändern | Status-Hinweis (`:8-14`) | T16 |
| `docs/concepts/active/main-chat-orchestrator-mode.md` | ändern | offener Hook-Punkt (`:109` vs. `:178`); POS-1 als Position einordnen | T16, T18 |
| `docs/concepts/runtime-gate-tiers.md` | ändern | INFO-Check-ID im Severity-Abschnitt (`:135-151`) | T13 |

---

## 4. Meilensteine (jeder einzeln grün)

| MS | Inhalt | Tasks | Zwischentest-Gate |
|---|---|---|---|
| **M0** | **Baseline erzeugen und dokumentieren** (erster Schritt, keine Code-Änderung): `python3 scripts/sync.py --check` (erwartet rc 0), `python3 scripts/sync.py --validate` (Exit-Code notieren), `python3 -m pytest tests/ -k topology` (Pass/Fail-Zahlen notieren); Ergebnis als kurzer Block in §17 „Baseline (M0)" eintragen | — | Alle drei Befehle sind **ausgeführt** und ihr Ergebnis steht in §17; erst danach dürfen T13/T21 diese Werte zitieren |
| **M1** | Flags + Registrierungen (G2-Kern) | T1–T3 | `tests/test_orchestrator_topology_effective_flags.py`, `…_conditionals.py` grün; **danach** `python3 scripts/sync.py` + Diff-Prüfung; `--check` rc 0 erwartet (Default-Render unverändert) |
| **M2** | Provider-Parität Rules/Context/Agents (G3) | T4–T6 | `tests/test_orchestrator_topology_render_parity.py` grün (3 Provider × 2 Topologien, Zwei-Sharer-Fall); **danach** `python3 scripts/sync.py` + Diff-Prüfung der regenerierten Artefakte + Commit |
| **M3** | Wortlaut (G1, G2-Nutzung, G4, G5) | T7–T10 | alle vier Wortlaut-Testdateien grün; **danach** `python3 scripts/sync.py`, Diff-Prüfung (`AGENTS.md`, `.claude/rules/use-orchestrator.md`, `.claude/agents/*`), Commit, **dann** `--check` rc 0 |
| **M4** | Diagnostik (G6) | T11–T13 | `tests/test_orchestrator_topology_checks.py` grün; `--validate` rc 0 |
| **M5** | v2-Reconcile (G7) | T14 | `tests/test_isolation_v2_topology_reconcile.py` grün; `tests/test_orchestrator_topology_entrypoint.py` 0 failed; `python3 scripts/sync.py` + Diff-Prüfung `opencode.json` |
| **M6** | Matrix (G8/G9-Teil 1) | T15 | `tests/test_orchestrator_topology_docs.py`, `…matrix.py`, `…generic.py` grün |
| **M7** | Doku-Angleichung + ADR (G9) | T16 | 11-Befund-Test grün; `docs/adr/0002` vorhanden |
| **M8** | Positionsmodell-Doku (`DECIDED 2026-11-09`, D-OQ1/D-OQ3) | T18 | Positions- und Mapping-Doku-Tests grün |
| **M9** | Positions-Parität Opencode (D-OQ2) | T19 | `tests/test_opencode_positions.py` grün (je ein Test pro Position, v1 **und** v2); `python3 scripts/sync.py` + Diff-Prüfung + Commit |
| **M10** | Szenarien | T17 | `tests/scenarios/run.sh 10` → **4× PASS** (`100`, `101`, `102`, `104`; `103` läuft außerhalb des Matches als `BLOCKED`) |
| **M11** | Explizite Deklaration + Abschluss | T20, T21 | `orchestrator.topology: subagent` gesetzt, regeneriert, `--check` rc 0; Vollsuite 0 failed; `--validate` rc wie in M0 |

Jeder Meilenstein endet mit `python3 -m pytest <berührte Dateien> --basetemp="$PYTEST_BASETEMP"` grün
**und** — sobald der Meilenstein gerenderte Artefakte verändert — `python3 scripts/sync.py`,
Diff-Prüfung, Commit, **dann** `python3 scripts/sync.py --check` rc 0 (AC-31).

---

## 5. Bite-sized TDD-Tasks

> Lesart je Task: **Files** (Ownership), **Interfaces** (Produces/Consumes), **Test-zuerst**
> (Testname + Assertion), **Implementierung** (Signatur), **Verifikation** (Befehl + Erwartung),
> **Abhängigkeiten**, **Größe**.
>
> **Task-IDs:** Überschrift `### Task <n>:` ist die maschinenlesbare Form (Plan-Graph-Parser);
> die Kurzform `T<n>` im Fließtext und in §10 bezeichnet denselben Task (`T5` = `### Task 5`).

### Task 1: Effektiv-Flags im Builder (G2, AC-15/AC-16/AC-21)

**Files:** `scripts/lib/variables.py` (`:311-356`), neu
`tests/test_orchestrator_topology_effective_flags.py`.
**Interfaces:** Produces `_effective_topology_flags(resolution: TopologyResolution, *, mode: str) -> dict[str, str]`
(fünf Bool-, zwei String-Flags). Consumes `TopologyResolution` aus `resolve_topology`.
**Test-zuerst:**
`test_effective_flags_report_resolution_not_declaration` — bei `declared=None`,
`effective="primary"`, `source="derived"`: `ORCH_TOPOLOGY_EFFECTIVE == "primary"`,
`ORCH_TOPOLOGY_EXPLICIT == "false"`, `ORCH_TOPOLOGY_EFFECTIVE_PRIMARY == "true"`,
`ORCH_TOPOLOGY_EFFECTIVE_SOURCE == "derived"`.
`test_effective_topology_is_never_none` — für alle 6 `(declared, effective, source)`-Tripel gilt
`ORCH_TOPOLOGY_EFFECTIVE in VALID_TOPOLOGIES` (nie `""`, nie `"none"`).
`test_exactly_one_position_flag_is_true` — genau eines von
`EFFECTIVE_PRIMARY/_SUBAGENT/_HYBRID` ist `"true"`.
`test_inert_is_true_only_for_main_chat` — `mode="main-chat"` ⇒ `ORCH_TOPOLOGY_INERT == "true"`;
`strict`/`advisory` ⇒ `"false"`.
`test_resolve_topology_ignores_mode` — `resolve_topology(..., mode=m)` liefert für
`m ∈ {strict, advisory, main-chat}` denselben `effective` (Negativ-Invariante, AC-21).
**Implementierung:** neue reine Funktion
`_effective_topology_flags(resolution: TopologyResolution, *, mode: str) -> dict` neben
`_topology_flags` (`:330`); liefert `ORCH_TOPOLOGY_EFFECTIVE`,
`ORCH_TOPOLOGY_EFFECTIVE_SOURCE`, `ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT`,
`ORCH_TOPOLOGY_EFFECTIVE_{PRIMARY,SUBAGENT,HYBRID}`, `ORCH_TOPOLOGY_INERT`.
`EFFECTIVE_EXPLICIT := "true" if resolution.source != "derived" else "false"` (Spec Rev. 2, K-1).
`INERT := "true"` iff `mode == "main-chat"`. `_topology_flags` bleibt unverändert.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_effective_flags.py --basetemp="$PYTEST_BASETEMP"`
→ **rot (5 failed)** vor, **grün (5 passed)** nach der Implementierung.
**Depends on:** — · **Größe:** S

### Task 2: Fail-closed-Registrierung an vier Stellen (G2, AC-15)

**Files:** `scripts/lib/variables.py:54-93`, `:575-598`; `scripts/lib/standalone.py:177-191`;
`scripts/lib/consistency/placeholders.py:70-78`; `tests/test_orchestrator_topology_conditionals.py`.
**Interfaces:** Produces `_TOPOLOGY_EFFECTIVE_CONDITIONAL_FLAGS: frozenset[str]` (fünf Bool-Namen) und
deren Registrierung; Consumes die Flag-Namen aus T1.
**Test-zuerst:**
`test_new_effective_flags_are_false_default` — für jedes der fünf Bool-Flags
(`…_EFFECTIVE_EXPLICIT`, `…_EFFECTIVE_PRIMARY`, `…_EFFECTIVE_SUBAGENT`, `…_EFFECTIVE_HYBRID`,
`ORCH_TOPOLOGY_INERT`) gilt: fehlt der Key, rendert `strip_inactive_conditional_blocks` den
`{{else}}`-Zweig (Verhalten wie `"false"`), nicht den `{{#if}}`-Zweig.
`test_each_registration_is_load_bearing` (parametrisiert über die vier Registrierungen) —
Entfernt der Test ein Flag aus **je einer** Registrierung, schlägt genau dieser Fall fehl
(Ratchet, AC-15).
`test_string_flags_are_not_conditionals` — `ORCH_TOPOLOGY`, `ORCH_TOPOLOGY_SOURCE`,
`ORCH_TOPOLOGY_EFFECTIVE` stehen in **keiner** Bool-Registrierung.
`test_standalone_and_builtin_vars_carry_new_names` — `standalone._CONDITIONAL_FALSE_FLAGS` und
`consistency/placeholders._BUILTIN_VARS` enthalten die neuen Namen.
**Implementierung:** `_TOPOLOGY_EFFECTIVE_CONDITIONAL_FLAGS: frozenset[str]` (fünf Bool-Namen) anlegen,
in `_FALSE_DEFAULT_CONDITIONALS` (`:54`) und in `strip_inactive_conditional_blocks` (`:587`)
registrieren; `standalone.py` um die fünf Bool-Keys (Default `false`) erweitern;
`_BUILTIN_VARS` (`:73-78`) um alle **sieben** neuen Namen ergänzen (fünf Bool + zwei String:
`ORCH_TOPOLOGY_EFFECTIVE`, `ORCH_TOPOLOGY_EFFECTIVE_SOURCE`).
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_conditionals.py --basetemp="$PYTEST_BASETEMP"`
→ **grün, 0 failed**; die bestehende Datei bleibt zusätzlich 0 failed.
**Depends on:** T1 · **Größe:** S

### Task 3: Provider-lose Basiswerte (G2, AC-16/AC-30)

**Files:** `scripts/lib/config.py:2013-2037` (`_build_orch_variables`), Test in
`tests/test_orchestrator_topology_effective_flags.py` (aus T1).
**Interfaces:** Produces die provider-lose Basis der sieben Flags im globalen Variablen-Dict —
ausdrücklich **nicht autoritativ** (RVW2-1190-09); jeder Provider-Seam (T4–T6, Stage 4) überschreibt
sie.
**Test-zuerst:**
`test_global_block_is_declared_or_failsafe` — kein `topology`-Key ⇒
`ORCH_TOPOLOGY_EFFECTIVE == "subagent"`, `…_EFFECTIVE_EXPLICIT == "false"`,
`…_EFFECTIVE_PRIMARY == "false"`, `ORCH_TOPOLOGY_INERT == "false"`; gesetztes
`topology: primary` ⇒ `EFFECTIVE == "primary"`, `EFFECTIVE_EXPLICIT == "true"`,
`EFFECTIVE_SOURCE == "project"`.
`test_global_block_honours_main_chat` — `mode: main-chat`, kein Key ⇒ `INERT == "true"`
(`ORCH_MODE_MAIN_CHAT == "true"` bleibt unverändert).
`test_global_block_is_documented_as_non_authoritative` — der Block trägt den Kommentar
„non-authoritative basis", und `test_no_render_seam_reads_the_global_basis` (AC-30-Ratchet) schlägt
fehl, wenn ein Render-Seam die globalen `ORCH_TOPOLOGY_EFFECTIVE*`-Werte ohne Provider-Override
liest (RVW2-1190-09).
**Implementierung:** nach `_topology_flags(...)` (`:2023-2027`) zusätzlich
`variables.update(_effective_topology_flags(_GlobalResolution(...), mode=_orch_mode))` mit einer
dokumentierten Fail-safe-`TopologyResolution` (`declared=<project topology or None>`,
`effective=<declared or "subagent">`, `source="project" if declared else "derived"`) — **kein**
Provider-Loop, weil dieses Dict nur die Basis ist, die jeder provider-skopierte Seam überschreibt
(`:2019-2021`). K-3.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_effective_flags.py --basetemp="$PYTEST_BASETEMP"`
→ **grün**; `python3 scripts/sync.py --check` → **rc 0**.
**Depends on:** T1, T2 · **Größe:** S

### Task 4: Provider-Parität in `rules.py` (G3/G2, AC-14/AC-18/AC-30)

**Files:** `scripts/lib/rules.py:238-313` (`_merged_rule_vars`), `:471` (`sync_embedded_rule_files`),
`:574-585` (`sync_rules`); `scripts/lib/sync_pipeline.py:1470-1474` (Aufrufer); neu
`tests/test_orchestrator_topology_render_parity.py`.
**Interfaces:** Consumes `_effective_topology_flags`/`_provider_topology_flags` (T1),
`ActiveSet` (per Sync). Produces `provider_vars` mit den sieben Topologie-Flags, Paritätsvertrag für
T5/T6.
**Test-zuerst:**
`test_rules_render_effective_flags_per_provider` — `orchestrator.provider-overrides.Opencode.topology: subagent`
bei globalem `primary`: `_merged_rule_vars(..., provider="Opencode", active_set=AS)` liefert
`ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT == "true"`, für `provider="Claude"` (ohne Override)
`…_EFFECTIVE_PRIMARY == "true"`.
`test_rules_derivation_uses_active_set` — kein Key, `primary-role` gesetzt, Rolle im ActiveSet ⇒
`ORCH_TOPOLOGY_EFFECTIVE == "primary"`, `ORCH_TOPOLOGY == ""` (declared bleibt leer).
`test_rules_passes_the_shared_active_set` — zwei Provider, Rolle **nicht** im Set ⇒ beide
`effective == "subagent"`; derselbe `ActiveSet` kommt in Emission und Rules an (AC-30).
**Implementierung:** nach `_topology_flags(...)` (`:289-293`) den Helfer
`_provider_topology_flags(config, provider, *, agent_meta_root, mode, active_set)` aus
`variables.py` aufrufen und mit `provider_vars.update(...)` mischen. `active_set` ist
**Pflicht-Keyword** (kein Default, kein Lazy-Load, kein `compute_active_set` im Helfer); der Helfer
lädt nur Caps + Provider-Registry und ruft `resolve_topology` **genau einmal**.
`sync_rules`/`sync_embedded_rule_files` erhalten `active_set` als Keyword und reichen es an
`_merged_rule_vars` weiter; der Aufrufer `sync_pipeline.py:1471-1474` übergibt `active_set=active_set`.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_render_parity.py --basetemp="$PYTEST_BASETEMP"`
→ **rot (3 failed)** → **grün**; danach `python3 scripts/sync.py`, Diff der regenerierten
`rules/`-Kopien prüfen, committen; **dann** `python3 scripts/sync.py --check` rc 0 (AC-31).
**Depends on:** T1–T3 · **Größe:** M

### Task 5: Provider-Parität in `context.py` + Stage-4-Seam (G3/G2, AC-20/AC-30)

**Files:** `scripts/lib/context.py:2563-2586` (`_build_managed_block`), `:1593-1603`
(`sync_context_for_provider`), `:1391-1427` (`_dispatch_context_strategy`), `:799` /
`:890` / `:1145` (die drei Strategien), `:848-852` (`_sync_managed_block_context` — Hinweis-Seam);
`scripts/lib/sync_pipeline.py:732-737` (`_sync_stage_contexts`-Signatur), `:788-790` (Aufruf);
`scripts/lib/cli_commands.py:1543` (Aufrufer), `:964` (`ctx.active_set`); Test wie T4.
**Interfaces:** Consumes `_provider_topology_flags` (T1/T4) + `ActiveSet`. Produces die
provider-skopierten Flags in `provider_variables` (Stage 4) sowie `local_vars` mit denselben Flags
und den Hinweis-Seam für T10.
**Test-zuerst:**
`test_context_render_effective_flags_per_provider` — derselbe Override-Fall wie T4, geprüft über
den gerenderten Managed Block (Marker `ORCH_TOPOLOGY_EFFECTIVE_*` via `{{…}}`-Probe-Template oder
Rückgriff auf `local_vars`).
`test_shared_context_renders_one_deterministic_block` — zwei Sharer mit **unterschiedlicher**
Effektivposition (Opencode `primary`, Gemini `subagent`) ⇒ **ein** deterministischer Block, der
**tatsächlich gerenderte Text** enthält keine positionsspezifische Aussage (kein Oszillieren,
Muster `_shared_context_users`, `:2246`; Spec §5-G5/AC-20).
`test_context_uses_the_shared_active_set` — Rolle nicht im Set ⇒ `effective == "subagent"` auch im
Managed Block (AC-30).
`test_stage4_requires_active_set` — `_sync_stage_contexts(...)` ohne `active_set` ist ein
`TypeError` (Pflicht-Keyword, kein Default-`None`); der Aufrufer `cli_commands.py:1543` übergibt
`ctx.active_set` (RVW2-1190-03).
**Implementierung:** `_sync_stage_contexts(..., *, active_set)` erweitern und **einmal** pro
Provider `_provider_topology_flags(config, provider, agent_meta_root=…, mode=…, active_set=active_set)`
aufrufen (das ist die eine Auflösung des Laufs, `resolve_topology` intern genau einmal); das
Ergebnis wird in `provider_variables` gemischt (wie heute die `ORCH_MODE_*`-Flags, `:757-769`).
`sync_context_for_provider(..., *, active_set)` und `_dispatch_context_strategy(..., *, active_set)`
reichen den Set an die drei Strategien; `_build_managed_block` **liest** die Effektiv-Flags aus dem
übergebenen `variables`-Dict (keine eigene Neuauflösung, `:2575-2586` bleibt nur für die
`declared`-Flags). Die bestehenden Test-Aufrufer von `sync_context_for_provider`
(u. a. `tests/test_context_*.py`, `tests/test_agents_md_shared_context_convergence.py`) werden im
selben Task auf das Pflicht-Keyword umgestellt (Folgeschritt, RVW2-1190-03).
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_render_parity.py tests/test_context_topology_consistency.py --basetemp="$PYTEST_BASETEMP"`
→ **grün**; danach `python3 scripts/sync.py`, Diff `AGENTS.md`/`.claude/rules/`, Commit, **dann**
`--check` rc 0.
**Depends on:** T4 · **Größe:** M

### Task 6: Provider-Parität in `agent_sync.py` + `sync_pipeline.py` (G3, AC-18/AC-30)

**Files:** `scripts/lib/agent_sync.py:489-554`, `:1427-1430`; `scripts/lib/sync_pipeline.py:1405-1431`;
Test wie T4.
**Interfaces:** Consumes `ActiveSet` + `_provider_topology_flags`. Produces `provider_vars` für die
Agent-Templates (Grundlage für T9) und den Override-Zweig des Pipelines.
**Test-zuerst:**
`test_agent_templates_carry_provider_scoped_effective_flags` — `_build_provider_vars(pc, "Opencode", vars, root, config=config, active_set=AS)`
liefert `EFFECTIVE_SUBAGENT == "true"`, für einen zweiten Provider `EFFECTIVE_PRIMARY == "true"`
(AC-18).
`test_sync_pipeline_override_branch_carries_topology_flags` — im `_orch_override_active`-Zweig
(`:1414-1417`) sind die sieben neuen Keys gesetzt, nicht nur `ORCH_MODE_*`.
`test_agents_use_the_shared_active_set` — Rolle nicht im Set ⇒ `effective == "subagent"` auch in den
Agent-Templates (AC-30).
**Implementierung:** `_build_provider_vars(..., *, active_set)` erweitern (Keyword **Pflicht**, kein
Default) und beim Aufruf `:1458` `active_set=active_set` übergeben (vorhanden ab `:1427-1430`);
`provider_vars.update(_provider_topology_flags(config, provider, agent_meta_root=agent_meta_root, mode=..., active_set=active_set))`.
In `sync_pipeline.py` den `_orch_override_active`-Zweig um denselben Aufruf erweitern — mit
demselben `active_set`, das die Pipeline schon besitzt.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_render_parity.py --basetemp="$PYTEST_BASETEMP"`
→ **grün**; `python3 -m pytest tests/test_orchestrator_topology_skip_role.py --basetemp="$PYTEST_BASETEMP"` → 0 failed;
danach `python3 scripts/sync.py` + Diff `.claude/agents/`, Commit, **dann** `--check` rc 0.
**Depends on:** T4, T5 · **Größe:** M

### Task 7: G1: Gate-Vorbedingung im `# CRITICAL GATE` (AC-3/AC-14)

**Files:** `rules/1-generic/use-orchestrator.md:1-24`; neu
`tests/test_use_orchestrator_topology_rendering.py`.
**Interfaces:** Consumes `ORCH_TOPOLOGY_EFFECTIVE_PRIMARY` (T1), `GATE_*` (bestehend). Produces den
topologieabhängigen Gate-Satz; regeneriert `AGENTS.md` und `.claude/rules/use-orchestrator.md`.
**Test-zuerst:**
`test_strict_gate_primary_states_the_position` — gerendert mit `ORCH_MODE_STRICT=true`,
`GATE_ENFORCED=true`, `ORCH_TOPOLOGY_EFFECTIVE_PRIMARY=true`: enthält den Satz „der Session-Einstieg
(`strict` verlangt das)", den qualifizierten Delegations-Weg („vorausgesetzt, der Provider lässt
diesen Start aus dem Main Chat zu", Spec §5-G1) und den Ausweg „`orchestrator.mode: main-chat`";
enthält **nicht** „Keine Ausnahmen." (AC-3).
`test_strict_gate_primary_has_no_absolute_claim` — der `primary`-Text enthält **weder** „kein
Spawn-Kanal" **noch** „cannot run as a subagent" **noch** „erfüllt dieses Gate nicht" **noch** einen
Provider-Namen; die Delegations-Alternative ist als zulässiger Weg genannt (Rev. 3 / RVW2-1190-04,
Spec §6.5).
`test_strict_gate_subagent_is_byte_identical` — mit `EFFECTIVE_PRIMARY=false` ist die Ausgabe
byte-identisch zur heutigen (Golden-String aus M0, AC-3/AC-6-Kontinuität).
`test_tier_paragraph_survives_both_variants` — `GATE_PARTIAL`- und `GATE_ADVISORY`-Provenienz-Absatz
stehen in beiden Varianten.
`test_gate_rule_has_no_provider_or_declared_condition` — Grep: Datei enthält weder
`ORCH_TOPOLOGY_EXPLICIT` noch einen Provider-Namen in einer Bedingung (AC-14).
`test_critical_gate_heading_is_unchanged` — Heading bleibt `# CRITICAL GATE` bzw.
`# CRITICAL GATE <suffix>` (Compact-Pfad, `config/context-anchors.yaml:83`).
**Implementierung:** innerhalb jeder der vier `GATE_*`-Blöcke den Impressiv-Satz durch
`{{#if ORCH_TOPOLOGY_EFFECTIVE_PRIMARY}}…{{else}}<heutiger Satz>{{/if}}` ersetzen; Sektionstitel
unverändert. Kein `{{#if}}` außerhalb der bestehenden `GATE_*`/`ORCH_MODE_*`-Struktur außer dem
neuen Topologie-Zweig.
**Verifikation:** `python3 -m pytest tests/test_use_orchestrator_topology_rendering.py --basetemp="$PYTEST_BASETEMP"`
→ **rot (4 failed)** → **grün (6 passed)**; danach `python3 scripts/sync.py`, Diff der regenerierten
`AGENTS.md` und `.claude/rules/use-orchestrator.md` prüfen (dieses Repo ist `strict` +
`effective=primary` ⇒ der Gate-Text ändert sich hier **beabsichtigt**, das ist G1), Commit, **dann**
`python3 scripts/sync.py --check` → **rc 0** (AC-31). Die Byte-Identität gilt für den
`subagent`-Zweig und für AC-27-Consumer (`ungesetzt ∧ effective == "subagent"`).
**Depends on:** T1–T3 · **Größe:** M

### Task 8: Templates auf Effektivposition (G2-Nutzung, AC-14/AC-17)

**Files:** `agents/1-generic/orchestrator.md:19`, `agents/1-generic/_reference-agent.md:24`,
`rules/1-generic/a2a-delegation-gates.md:6-19`; neu
`tests/test_orchestrator_template_topology_wording.py`.
**Interfaces:** Consumes `ORCH_TOPOLOGY_EFFECTIVE_PRIMARY`/`_EFFECTIVE_EXPLICIT` (T1/T6). Produces
dreiwegige Template-Zweige; Golden-Fixture für deklariertes `primary` (AC-27).
**Test-zuerst:**
`test_derived_primary_has_no_main_chat_only_claim` — gerendert mit `EFFECTIVE_PRIMARY=true`,
`EFFECTIVE_EXPLICIT=false`, `ORCH_TOPOLOGY=""`: `orchestrator.md` enthält **nicht**
„Only `main_chat` may create you", `a2a-delegation-gates.md` **nicht**
„NUR `main_chat` darf den `orchestrator` spawnen" (AC-17). Dieser Fall ist die **beabsichtigte**
Änderung (Spec §5-G5, Plan „Migration & Rollback") — er unterliegt **nicht** der
Byte-Identitätszusage (AC-16 gilt nur für `effective == "subagent"`).
`test_declared_subagent_keeps_historic_wording` — `EFFECTIVE_PRIMARY=false`,
`EFFECTIVE_EXPLICIT=true` ⇒ beide Dateien byte-identisch zu heute.
`test_declared_primary_has_a_golden_fixture` — `EFFECTIVE_PRIMARY=true`,
`EFFECTIVE_EXPLICIT=true` ⇒ Text entspricht der neuen Golden-Fixture (bewusste Änderung, AC-27).
`test_derived_subagent_keeps_historic_else_branch` — `EFFECTIVE_PRIMARY=false`,
`EFFECTIVE_EXPLICIT=false` ⇒ heutiger `{{else}}`-Text unverändert.
`test_reference_agent_matches_orchestrator_wording` — `_reference-agent.md` rendert denselben
Singleton-Satz (Konsistenz der drei Templates).
`test_no_declared_conditional_left_for_semantics` — Grep-Assertion: die Semantik-Zweige in diesen
drei Dateien verzweigen nicht mehr auf `ORCH_TOPOLOGY_EXPLICIT` (AC-14).
**Implementierung:** Dreiweg-Struktur je Datei:
`{{#if ORCH_TOPOLOGY_EFFECTIVE_PRIMARY}}` (Einstiegs-Wortlaut, „Session-Einstieg", G1/G3-HARD-REJECT)
`{{else}}{{#if ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT}}` (heutiger expliziter Zweig, wortgleich)
`{{else}}` (heutiger else-Zweig, wortgleich) `{{/if}}{{/if}}`. `ORCH_TOPOLOGY_EXPLICIT` bleibt als
Audit-Flag im Variablen-Dict, steuert aber keinen Zweig mehr.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_template_topology_wording.py --basetemp="$PYTEST_BASETEMP"`
→ **rot (4 failed)** → **grün (6 passed)**; `tests/test_orchestrator_topology_conditionals.py` 0 failed;
danach `python3 scripts/sync.py`, Diff `.claude/agents/orchestrator.md` + `.opencode/agents/…` prüfen,
Commit, **dann** `--check` rc 0 (AC-31).
**Depends on:** T7 · **Größe:** M

### Task 9: Singleton-Block topologieabhängig (G4, AC-19)

**Files:** `scripts/lib/agent_sync.py:969-986`; neu `tests/test_singleton_block_topology.py`.
**Interfaces:** Produces `_singleton_constraint_block(effective: str, *, inert: bool) -> str`
(drei Varianten); Consumes `resolve_topology`-Ergebnis aus T4/T6, kein eigener Resolver.
**Test-zuerst:**
`test_primary_block_names_the_session_entry` — `effective == "primary"`, `inert=False`: Block enthält
„er **ist** der Session-Einstieg", **nicht** „der vom `main_chat` gespawnte"; die Zeile
„**NIEMALS** `task(subagent_type=\"orchestrator\", ...)`" bleibt (AC-19).
`test_subagent_block_is_byte_identical` — `effective == "subagent"`, `inert=False`: Block
zeichengleich zu heute — inklusive des toten Verweises „Gate #5" (`:981`), der **bewusst**
konserviert wird (kein neuer Fehler, Spec §5-G4).
`test_inert_block_has_no_spawn_claim` — `inert=True` (`mode: main-chat`): neutraler Satz ohne
Spawner-Behauptung, `NIEMALS`-Zeile bleibt; die Inert-Quelle ist `ORCH_TOPOLOGY_INERT`, nicht ein
Modus-Literal im Rumpf.
`test_block_is_injected_only_for_spawners` — `role != "orchestrator" and not
role.endswith("-iteration") and can_spawn` (heutige Bedingung `:985`) unverändert.
**Implementierung:** Block-Erzeugung in
`_singleton_constraint_block(effective: str, *, inert: bool) -> str` auslagern (drei Varianten,
`inert` als Pflicht-Keyword), in `_finalize_agent_content` mit der dort bereits verfügbaren
`provider`/`config`/`active_set`-Auflösung aufrufen (`:1463-1468`); keine neue Auflösung —
`resolve_topology` bzw. `_provider_topology_flags` aus T4/T6.
**Verifikation:** `python3 -m pytest tests/test_singleton_block_topology.py --basetemp="$PYTEST_BASETEMP"`
→ **rot (4 failed)** → **grün**; danach `python3 scripts/sync.py`, Diff der Agent-Dateien, Commit,
**dann** `--check` rc 0 für den `subagent`-Zweig (AC-31).
**Depends on:** T6 · **Größe:** S

### Task 10: Einstiegshinweis topologieabhängig (G5, AC-20/AC-24)

**Files:** `scripts/lib/agents.py:132-204` (`build_agent_hints` erhält `position`);
`scripts/lib/context.py:848-852` (neuer Helfer `_position_aware_agent_hints`, `:2246`
`_shared_context_users`); `scripts/lib/config.py:1686`, `:1950` (globale Aufrufer bleiben neutral);
neu `tests/test_entry_hint_topology.py`.
**Interfaces:** Consumes `active_set` + die provider-skopierte Position (aus den
Effektiv-Flags in `variables`, T5) + `provider`, `target_name`, `provider_config`. Produces
`build_agent_hints(..., *, position: str = "neutral") -> str` und
`_position_aware_agent_hints(config, provider, provider_config, agent_meta_root, target_name, *, active_set, position) -> dict[str, str]`.
**Test-zuerst:**
`test_hint_primary_names_the_entry` — provider-**eigene** Kontextdatei, `position == "primary"` ⇒
„**Einstiegspunkt:** Diese Session startet im `orchestrator`-Agenten. Ein Start im Main Chat
erfüllt das Gate nur bei Delegation an den `orchestrator` — siehe `use-orchestrator.md`." (AC-20;
**keine** absolute Spawnbarkeits-Behauptung).
`test_hint_subagent_keeps_historic_wording` — `position == "subagent"` ⇒ **exakt** der heutige
String `agents.py:174` („Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben —
Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«."); Assertion auf Gleichheit, nicht
auf Teilstring (Rev. 3 / RVW2-1190-01).
`test_hint_main_chat_is_unchanged` — `mode: main-chat` ⇒ heutiger Text (`:177-179`), byte-identisch.
`test_shared_hint_is_provider_neutral` — zwei Sharer mit **unterschiedlicher** Effektivposition
(Opencode `primary`, Gemini `subagent`) ⇒ `_position_aware_agent_hints` liefert für **beide**
Sharer denselben neutralen Text aus Spec §5-G5; Assertion auf den **tatsächlich gerenderten**
String, nicht auf Flags (AC-20).
`test_same_position_shared_hint_keeps_the_position_from_text` — zwei Sharer, beide `subagent` ⇒
der historische `subagent`-Text (kein Positionsverlust, AC-16).
`test_hint_is_deterministic_for_shared_context` — zwei Läufe mit vertauschter Provider-Reihenfolge
liefern denselben Text (kein Render-Order-Oszillieren).
`test_role_orchestrator_active_under_main_chat_prose` — `mode: main-chat` ⇒
`variables["ROLE_ORCHESTRATOR_ACTIVE"] == "false"` und die gerenderte `a2a-delegation-gates`-Zeile
ist `Worker → HARD REJECT` (Golden-Fixture
`tests/fixtures/topology-golden/a2a-delegation-gates.role-inactive.md`), nicht die
`orchestrator`-Variante (AC-24, Rev. 3 / RVW2-1190-13).
**Implementierung:** `build_agent_hints(..., *, position: str = "neutral")` — der Rumpf wählt nur
noch den Textbaustein, löst **nichts** auf. Die Entscheidung trifft
`_position_aware_agent_hints`: `shared_users = _shared_context_users(provider, provider_config,
config, target_name=target_name)`; bei **einer** Position über alle aktiven Sharer wird genau
dieser Text gerendert, bei **unterschiedlichen** Positionen der neutrale Text. Die Position des
aktuellen Providers kommt aus den Flags in `variables` (Stage 4), die der übrigen Sharer aus
`resolve_topology(...)` mit **denselben** Eingaben (`config`, `active_set`) — dieselbe Funktion,
kein zweiter Resolver. Aufruf in `_sync_managed_block_context` anstelle der beiden direkten
`build_agent_hints`-Aufrufe (`:850`, `:852`), Ergebnis in `variables["AGENT_HINTS"]` bzw.
`AGENT_HINTS_CLAUDE`. Die globalen Aufrufer (`config.py:1686`, `:1950`) bleiben ohne
`position`-Argument (neutral) — sie kennen weder Provider noch Zieldatei, und der neutrale Text ist
für jeden Leser wahr (RVW2-1190-02). K-4 bleibt damit **eine** Regel.
**Verifikation:** `python3 -m pytest tests/test_entry_hint_topology.py --basetemp="$PYTEST_BASETEMP"`
→ **rot** → **grün**; `tests/test_orchestrator_active_set_prose.py` 0 failed; danach
`python3 scripts/sync.py`, Diff `CLAUDE.md` (dieses Repo: Claude leitet `subagent` ab ⇒ **keine**
Änderung), Commit, **dann** `--check` rc 0 (AC-31).
**Depends on:** T6 · **Größe:** S

### Task 11: Check `orchestrator-topology.main-chat-derived-primary` (D-Q1, AC-1/AC-2)

**Files:** `scripts/lib/consistency/topology.py:62-71`, `:245-403`; neu
`tests/test_orchestrator_topology_checks.py`.
**Interfaces:** Produces `CHECK_MAIN_CHAT_DERIVED_PRIMARY` + Finding-Text (gepinnt). Consumes
`resolve_topology`/`topology_explicit`, `mode`; kein neuer Resolver.
**Test-zuerst:**
`test_main_chat_derived_primary_warns_once` — `mode: main-chat`, kein `topology`,
`primary-role` gesetzt, Rolle im ActiveSet ⇒ genau **ein** Finding, `severity == WARNING`,
`check == "orchestrator-topology.main-chat-derived-primary"`, Nachricht enthält den gepinnten
Teilstring (Spec §4-D-Q1) inkl. Provider-Name und der Override-Remediation.
`test_declared_topology_in_main_chat_stays_a_hard_error` — derselbe Scope mit deklarierter
Topologie: der Konsistenz-Check meldet **nichts** Zusätzliches; der harte Validator
(`config.py:557-563`) bleibt die Instanz mit rc≠0 (AC-2).
`test_no_finding_without_derivation_source` — kein `primary-role` oder Rolle nicht im ActiveSet ⇒
kein Finding.
`test_dedup_per_provider_and_run` — zwei Aufrufe ⇒ ein Finding pro Provider und Lauf.
`test_check_lives_in_consistency_topology` — die ID wird in `consistency/topology.py` erzeugt
(AC-21-Ablageregel).
**Implementierung:** `CHECK_MAIN_CHAT_DERIVED_PRIMARY`-Konstante neben `:65-71`; im Provider-Loop
nach `resolve_topology` (`:252-260`) prüfen: `mode == "main-chat"` **und**
`not topology_explicit(config, provider)` **und** `resolution.effective == "primary"`; Text wörtlich
aus der Spec, `_append_once` mit `Severity.WARNING`.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_checks.py --basetemp="$PYTEST_BASETEMP"`
→ **rot (4 failed)**; nach Implementierung grün; `python3 scripts/consistency-check.py` und
`python3 scripts/sync.py --validate` → rc 0.
**Depends on:** T1 · **Größe:** S

### Task 12: Check `orchestrator-topology.strict-primary-entry-mismatch` (D-Q2-2, AC-4)

**Files:** `scripts/lib/consistency/topology.py` (neuer Helper + Aufruf im Loop), Test wie T11.
**Interfaces:** Produces `CHECK_STRICT_PRIMARY_ENTRY_MISMATCH` +
`_strict_primary_entry_mismatch(agent_meta_root, provider_config, provider, pc, *, mode, effective) -> str | None`;
Consumes `read_json_lenient`/`_settings_path`, `owns_gate_surface`.
**Test-zuerst:**
`test_strict_primary_without_entry_point_warns` — `mode: strict`, `effective == "primary"`,
Provider mit `default_agent`-Fläche (`isolation.owns_gate_surface`, `isolation.py:302`),
`default_agent` fehlt in `opencode.json` ⇒ genau eine WARNING mit dem gepinnten Text
(Spec §4-D-Q2, gepinnt), `<absent>` als Wert (AC-4).
`test_strict_primary_with_foreign_default_agent_warns` — `default_agent: developer` ⇒ eine
WARNING, Wert `developer` im Text.
`test_no_finding_when_entry_point_matches` — `default_agent == "orchestrator"` ⇒ kein Finding.
`test_no_finding_when_effective_is_not_primary` — `topology: subagent` + `strict` ⇒ kein Finding.
`test_early_return_of_user_owned_check_is_untouched` — `_user_owned_default_agent` (`:118-128`)
bleibt unverändert; der neue Check ist ein eigener Pfad (G6).
**Implementierung:** `CHECK_STRICT_PRIMARY_ENTRY_MISMATCH`-Konstante; Helper
`_strict_primary_entry_mismatch(agent_meta_root, provider_config, provider, pc, mode, effective) -> str | None`
— liest die `default_agent`-Fläche über `_settings_path` (`:108-115`) und
`read_json_lenient`, **keine** State-Rollback-Logik (anders als `_user_owned_default_agent`).
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_checks.py --basetemp="$PYTEST_BASETEMP"`
→ **grün**; `--validate` rc 0.
**Depends on:** T11 · **Größe:** S

### Task 13: INFO `orchestrator-strict.direct-dispatch-inert` (D-Q5, AC-12/AC-13)

**Files:** `scripts/lib/consistency/orchestrator_strict.py:36-39`, `:182-250`;
`docs/concepts/runtime-gate-tiers.md:135-151`; Test in `tests/test_orchestrator_topology_checks.py`.
**Interfaces:** Produces `_DISPATCH_INERT_CHECK_ID = "orchestrator-strict.direct-dispatch-inert"` +
INFO-Finding; Consumes `orchestrator.mode` und die **Präsenz** des Keys (kein Resolver, kein
`direct-dispatch`-Verbraucher).
**Test-zuerst:**
`test_direct_dispatch_key_present_under_main_chat_is_info` — `mode: main-chat` **und** Key
`direct-dispatch-enabled` **präsent** ⇒ genau ein Finding **pro Lauf**, `severity == INFO`,
`check == "orchestrator-strict.direct-dispatch-inert"`, gepinnter Text (Spec §4-D-Q5), rc 0 (AC-12).
`test_info_is_emitted_once_per_run_not_per_provider` — zwei aktive Provider, `main-chat`, Key
präsent ⇒ **genau ein** INFO (die Prüfung liegt vor dem Provider-Loop, RVW2-1190-05).
`test_key_under_strict_produces_no_finding` — `mode: strict`, Key präsent ⇒ **kein** Finding: der Key
ist dort wirksam (`agents/1-generic/orchestrator.md:203-205`) (AC-12/AC-13).
`test_absent_key_produces_no_finding` — `mode: main-chat`, Key fehlt (Default `true` laut
`config.py:2003`) ⇒ kein Finding (AC-13).
`test_advisory_mode_produces_no_finding` — `mode: advisory`, Key präsent ⇒ kein Finding (AC-13).
`test_presence_not_truthiness` — `direct-dispatch-enabled: false` unter `main-chat` ⇒ **doch** ein
Finding (Präsenz-Semantik).
`test_check_lives_in_orchestrator_strict` — die ID wird in `consistency/orchestrator_strict.py`
erzeugt (AC-21-Ablageregel).
**Implementierung:** `_DISPATCH_INERT_CHECK_ID = "orchestrator-strict.direct-dispatch-inert"`;
Prüfung **einmal pro Lauf vor dem Provider-Loop** — nach dem `isinstance(orch, dict)`-Guard
(`:220-221`) und **vor** `active_providers = ...` (`:225`), also nicht hinter dem
Strict-Gate (`_resolve_effective_strict`, `:227-228`, liefert für `main-chat` `False` und würde die
Prüfung im einzigen Zielmodus nie feuern lassen). `Severity.INFO`, Text ohne Provider-Namen.
Bedingung: aufgelöster Projekt-Modus `main-chat` ∧ `"direct-dispatch-enabled" in orchestrator`.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_checks.py --basetemp="$PYTEST_BASETEMP"`
→ **grün**; `python3 scripts/sync.py --validate` zeigt auf **diesem** Repo (`mode: strict`) **kein**
`[INF]` mit der ID `orchestrator-strict.direct-dispatch-inert` (der bestehende
`orchestrator-strict.no-hook-support` bleibt möglich) und endet mit dem in M0 dokumentierten
Exit-Code (Verweis auf §17, kein Baseline-Zitat).
**Depends on:** T11 · **Größe:** S

### Task 14: G7: v2-Reconcile übergibt `topology` (AC-22/AC-23)

**Files:** `scripts/lib/isolation.py:1751-1761` (`reconcile_opencode_surface_gate`-Signatur),
`:1826-1830`, `:1840-1843`, `:1408-1463` (`_opencode_v2_gate_permissions`), `:1351-1405`,
`:1881-1889`; `scripts/lib/sync_pipeline.py:1598-1602`; `scripts/lib/cli_commands.py:344-348`; neu
`tests/test_isolation_v2_topology_reconcile.py`.
**Interfaces:** Produces
`reconcile_opencode_surface_gate(project_root, config, provider, provider_config, agent_meta_root, log, dry_run, *, active_set, topology=None)`
und `_opencode_v2_gate_permissions(..., *, active_set, topology=None)`. Consumes das bereits
aufgelöste `TopologyResolution` **von außen** (kein dritter Auflösungspunkt pro Provider und Lauf).
**Test-zuerst:**
`test_v2_subagent_writes_no_permission_triples` — `surface-version: v2`, `mode: strict`,
`topology: subagent`, `opencode.json` ohne `default_agent` ⇒ Ergebnis-Dokument enthält **keine**
`permissions[]`-Tripel (AC-22).
`test_v2_subagent_emits_exactly_one_log_warning` — genau eine Sync-Log-Warnung mit den in Spec §6.4
gepinnten Teilstrings (`opencode-v2 gate (permissions deny) NOT written for provider` und
`effective orchestrator topology is 'subagent'`), **kein** Consistency-Finding (Tier `plugin`),
**kein** „default_agent is missing", **kein** „Set `default_agent` to 'orchestrator'" (AC-22).
`test_v1_subagent_counts_per_channel` — v1: eine Log-Warnung **und** ein Finding, je Kanal genau eine
(Spec §6.4-Zählregel).
`test_v2_primary_still_writes_the_triples` — `topology: primary` ⇒ Tripel vorhanden, kein neues
Warnbild (Regression).
`test_all_three_entry_point_calls_pass_topology` — AST-Test mit **erwarteter Trefferzahl**: genau
**3** `Call`-Knoten von `_opencode_entry_point` in `isolation.py` (`:869`, `:1457`, `:1827`) tragen
das Keyword `topology`; `None` ist nur an `:869` erlaubt, wenn `rollback_only` gilt oder
`config is None` ist (AC-23).
`test_both_reconcile_callers_pass_topology` — AST-Test: genau **2** `Call`-Knoten von
`reconcile_opencode_surface_gate` (`sync_pipeline.py`, `cli_commands.py`) tragen das Keyword
`topology=` (Durchreichung, keine Neuresolution).
`test_reconcile_passes_the_resolved_object_downstream` — Fixture-Test mit Monkeypatch-Zähler:
ein Reconcile-Lauf ruft `_opencode_entry_point` genau einmal und `_opencode_v2_gate_permissions`
genau einmal; beide Aufrufe tragen `topology` und zwar **dasselbe Objekt** (Identität).
`test_row_six_warning_is_cause_aware` — die Zeile-6-Warnung nennt bei `effective != "primary"`
`orchestrator-topology.gate-inactive` statt einer fehlenden `primary-role`.
**Implementierung:** `reconcile_opencode_surface_gate(..., *, active_set, topology=None)` erweitern
und den Wert an `_opencode_entry_point(..., topology=topology)` (`:1826-1830`) sowie an
`_opencode_v2_gate_permissions(..., topology=topology)` (`:1840-1843`) weiterreichen; in
`_opencode_v2_gate_permissions` denselben Wert an `_opencode_entry_point(...)` (`:1457`) geben.
`_v2_gate_invariant_warning(provider, desired, *, merge_rewrites, topology=None)` ergänzen: bei
`topology is not None and topology.effective != "primary"` keine `default_agent`-Empfehlung
(`:1395-1399`). Zeile-6-Zweig (`:1881-1889`) um die Topologie-Ursache erweitern. In
`sync_pipeline._sync_stage_per_provider` **eine** Resolution pro Provider bilden
(`resolve_topology` mit derselben Eingabemenge — `config`, `provider`, `active_set` — die auch
`_provider_topology_flags` an den Render-Seams benutzt) und sie an den Reconcile übergeben;
`reconcile_opencode_surface_gate` löst **nicht** selbst auf. `cli_commands.py` analog im
`--test-generated`-Pfad.
**Verifikation:** `python3 -m pytest tests/test_isolation_v2_topology_reconcile.py tests/test_orchestrator_topology_entrypoint.py --basetemp="$PYTEST_BASETEMP"`
→ **rot** → **grün**; danach `python3 scripts/sync.py`, Diff `opencode.json`, Commit,
**dann** `--check` rc 0 (AC-31).
**Depends on:** T1, T6 · **Größe:** M

### Task 15: Matrix + Doku-Tests (AC-6/7/8/10/11, G8)

**Files:** `docs/concepts/active/orchestrator-topology.md` (Matrix-Abschnitt nach `:79`);
`tests/test_orchestrator_topology_docs.py` (ändern); neu
`tests/test_orchestrator_mode_topology_matrix.py`, `tests/test_provider_transform_topology_generic.py`.
**Interfaces:** Produces `EXPECTED_MATRIX: dict[tuple[str, str, str], str]` (24 Einträge) und die vier
Surface-Tabellen in der Concept-Doc; Consumes Spec §12.2–§12.6 als Datenquelle.
**Test-zuerst:**
`test_matrix_has_24_rows` — vier Surface-Tabellen × sechs `mode`×`topology`-Kombinationen
(`strict/advisory/main-chat` × `primary/subagent`), jede Zeile mit Urteil und Positionsangabe
(AC-6).
`test_verdict_vocabulary_is_closed` — das **erste Token** der Urteilszelle ist ausschließlich
`RECOMMENDED|ALLOWED|DEGRADED|FORBIDDEN` (Zusätze wie „(optional, 0 Hop)" sind erlaubt); jede Zeile
trägt eine Positions-ID aus `{POS-1, POS-2, POS-3}`; `dito`-Zellen sind innerhalb ihrer Tabelle auf
eine Zelle mit eigener `datei:zeile`-Referenz auflösbar (AC-6).
`test_exactly_one_recommended_per_surface` — Menge exakt
`{(v1, strict, subagent), (v2, strict, subagent), (Claude, strict, subagent), (Gemini, strict,
subagent)}` (AC-7, `DECIDED 2026-11-09` D-OQ1); `strict × primary` ist auf v1/v2 `ALLOWED` und nicht
abgewertet.
`test_v2_rows_name_tier_facts_and_recommendation_basis` — die `RECOMMENDED`-Zeile nennt
Session-Ownership **und** `gate-inactive` (kein Deny); die `ALLOWED`-Zeile `strict × primary` nennt
`observe` **und** `permissions`-Deny, nicht das Plugin als Erzwingungsinstanz (AC-8).
`test_cost_section_has_hop_definition_threshold_and_estimate` — (a) „POS-3 = 0 Hop, POS-2 = 1 Hop,
POS-1 = 0 Hop", (b) „S ≤2 Dateien → direkter Dispatch", (c) eine `ESTIMATE`-Zahl **mit** Messmethode
und ohne Messbehauptung (AC-10).
`test_single_user_recommendation_is_strict_subagent_with_primary_option` — Default
`strict × subagent` (POS-2) **und** `strict × primary` (POS-3) als gleichwertige Option mit
„gleiche Governance, kein Hop, dafür Session-Start-Bindung" (AC-11).
`test_gemini_primary_degrades_with_one_warning` — Resolver-Fall: `topology: primary` + Gemini-Zelle
⇒ `effective == "subagent"` + genau eine `orchestrator-topology.degraded` (AC-9).
`test_emission_matrix_body` (in `…matrix.py`, parametrisiert über 24 Zellen) — pro Zelle:
`mode`-Frontmatter, Lock-Präsenz, Deny-Form; `test_generic_emission` (in
`…topology_generic.py`): Claude/Gemini emittieren **nie** `mode: primary` ohne deklarierte
`primary`-Zelle (AC-24).
**Implementierung:** die vier Tabellen aus Spec §12.2–§12.5 (Zeilen 781-827) plus Evidenz-Index
(§12.6, Zeilen 829-844) in die Concept-Doc übernehmen; `EXPECTED_MATRIX` als Test-Datenstruktur
in `tests/test_orchestrator_topology_docs.py`.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_docs.py tests/test_orchestrator_mode_topology_matrix.py tests/test_provider_transform_topology_generic.py --basetemp="$PYTEST_BASETEMP"`
→ **rot** (Matrix fehlt) → **grün**.
**Depends on:** T7, T8, T14 · **Größe:** L

### Task 16: G9: elf Doku-Befunde + ADR (AC-25/AC-28)

**Files:** `README.md:210`, `:410-419`; `CLAUDE.md:102`; `docs/CODEBASE_OVERVIEW.md:1724-1727`;
`docs/concepts/active/singleton-orchestrator-architecture.md:8-14`;
`docs/concepts/active/main-chat-orchestrator-mode.md:109`, `:178`;
`docs/concepts/active/orchestrator-topology.md:75-79`, `:91-96`; neu
`docs/adr/0002-orchestrator-mode-topology.md`; Test in `tests/test_orchestrator_topology_docs.py`.
**Interfaces:** Produces die elf Doku-Korrekturen + den ADR; Consumes Spec §9.1 (B-1…B-11) und
D-Q1…D-Q5 als Textquelle.
**Test-zuerst:**
`test_no_absolute_singleton_claim_without_topology_qualifier` — geprüft werden **genau** die elf
Belegstellen aus Spec §9.1 (B-1…B-11); verbotene Literale „nur der `main_chat` spawnt",
„NUR `main_chat` darf", „Only `main_chat` may create you", „der vom `main_chat` gespawnte",
„one per session, spawned by the main chat" dürfen nur erscheinen, wenn `topology`, `subagent`
oder `primary` im **selben** Absatz stehen; Spec/Review/Plan sind ausgenommen (AC-25, Rev. 3 /
RVW2-1190-13).
`test_p3_status_is_single_valued` — `orchestrator-topology.md:91` und
`singleton-orchestrator-architecture.md:13` sagen beide „P3, shipped"; die Vorgänger-Spec-Zeile
`docs/specs/2026-11-04-orchestrator-topology-spec.md:791-792` wird **nicht** editiert, sondern in
`docs/concepts/active/orchestrator-topology.md` als überholt ausgewiesen (Rev. 3 / RVW2-1190-08).
`test_gate_render_is_single_variant_per_file` — B-9: die gerenderte Gate-Fassung enthält **eine**
Variante; ein suffixloses `# CRITICAL GATE` mit zusätzlichem PARTIAL-Absatz in derselben Datei
schlägt fehl (Rev. 2 / R-15; Ursache ist ein doppelter `GATE_*`-Treffer, kein zweiter Wortlaut).
`test_readme_lists_the_topology_key` — Key-Tabelle (`README.md:210`-Nachbarschaft) nennt
`orchestrator.topology`; Mermaid (`:415`) hat zwei Knoten (`primary` = entry, `subagent` = spawned)
(B-2/B-3).
`test_adr_records_dq1_to_dq5` — `docs/adr/0002-…` existiert, enthält D-Q1…D-Q5 als
Entscheidungen mit Konsequenzen (MADR-minimal, `se-cascade-adr-standard`) (AC-28).
`test_adr_records_doq1_to_doq3` — derselbe ADR enthält D-OQ1, D-OQ2 und D-OQ3 mit dem Datum
`2026-11-09` und je einer Konsequenz (Default `strict × subagent`, Gate-Tier je Surface,
#1182-Bedingung) (AC-28).
**Implementierung:** elf Einzeländerungen (B-1…B-11, Spec §9.1) plus ADR.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_docs.py --basetemp="$PYTEST_BASETEMP"`
→ **grün**; `python3 -m pytest tests/test_orchestrator_topology_docs.py tests/test_orchestrator_topology_consistency.py --basetemp="$PYTEST_BASETEMP"` → 0 failed.
**Depends on:** T15 · **Größe:** M

### Task 17: Szenarien `100`–`104` auf das Positionsmodell ausgerichtet (G8, AC-29)

**Files:** `tests/scenarios/registry.md` (`:46-132`, `:176`); neu
`tests/scenarios/configs/100-strict-subagent-opencode-v2.project.yaml`,
`101-strict-primary-opencode-v2.project.yaml`, `102-main-chat-derived-primary.project.yaml`,
`104-claude-strict-subagent.project.yaml`; neu
`tests/scenarios/asserts/100-strict-subagent-opencode-v2.sh` … `104-claude-strict-subagent.sh`; das
blockierte Szenario liegt **außerhalb** des `10*`-Matches:
`tests/scenarios/configs/blocked-103-advisory-subagent.project.yaml` +
`tests/scenarios/asserts/blocked-103-advisory-subagent.sh`.
**Interfaces:** Produces vier ausführbare Szenarien (`100`, `101`, `102`, `104`) und ein
dokumentiertes `BLOCKED`-Szenario (`103`); Consumes die Geräte aus T7/T8/T14/T15/T19. Die
Szenario-Nummern sind die **einzige** Zuordnung — sie werden nirgends anders vergeben.

**Zuordnung (verbindlich, `DECIDED 2026-11-09` D-OQ1/D-OQ3):**

| Szenario | Config | Position | Erwartung |
|---|---|---|---|
| `100` | Opencode v2, `mode: strict`, `topology: subagent` (**neuer Default**) | POS-2 | kein `default_agent`, `mode: subagent` im Agenten-Frontmatter, keine `permissions[]`-Tripel, genau eine Log-Warnung mit den §6.4-Teilstrings |
| `101` | Opencode v2, `mode: strict`, `topology: primary` | POS-3 | `default_agent == "orchestrator"`, `mode: primary`, zwei `permissions`-Tripel, `--validate` rc 0 |
| `102` | `mode: main-chat`, kein `topology`, `primary-role` gesetzt | POS-1 | genau eine `orchestrator-topology.main-chat-derived-primary`-Warnung, rc 0, **kein** generierter Orchestrator-Agent, **kein** `default_agent` |
| `103` | `mode: advisory`, `topology: subagent`, `context-profile: compact` | POS-2 | **BLOCKED (#1182)** — nicht ausgeführt, Katalog `BLOCKED (#1182)`, Name außerhalb `10*` |
| `104` | Claude, `mode: strict`, `topology: subagent` | POS-2 | `hook`-Tier-Text, kein Entry-Point auf den Orchestrator, keine Orphan-Platzhalter |

**Test-zuerst (Assertions):**
`100-strict-subagent-opencode-v2` — kein `default_agent` in `opencode.json`, `mode: subagent` im
Agenten-Frontmatter, `permissions`-Tripel **abwesend**, genau eine Warnung mit
`opencode-v2 gate (permissions deny) NOT written for provider` **und**
`effective orchestrator topology is 'subagent'` (AC-29/AC-35).
`101-strict-primary-opencode-v2` — `default_agent == "orchestrator"`, `mode: primary`, zwei
`permissions`-Tripel (POS-3-Regression, AC-29).
`102-main-chat-derived-primary` — genau eine `orchestrator-topology.main-chat-derived-primary`-Warnung,
`--validate` rc 0, kein `orchestrator`-Agent, kein `default_agent` (AC-29/AC-34).
`blocked-103-advisory-subagent` — **blockiert durch #1182** (`context-profile: compact` bricht für
`advisory` ab); Config liegt außerhalb des `10*`-Matches, Katalog führt `BLOCKED (#1182)`, das Skript
wird **nicht** ausgeführt. `run.sh` kennt **kein** `SKIP` (`run.sh:231`) — eine Skip-Konvention wird
nicht eingeführt (AC-29/AC-37).
`104-claude-strict-subagent` — Claude, `mode: strict`, `topology: subagent`: kein Orchestrator als
Entry, `hook`-Tier-Text, keine Orphan-Platzhalter (AC-29).
**Implementierung:** vier Configs nach dem Muster von
`tests/scenarios/configs/69-opencode-v2-surface.project.yaml`, fünf Assert-Skripte (cwd = Temp-Dir,
`REPO_ROOT`/`$1`), Katalogzeilen `100`–`104` (davon `103` als `BLOCKED` mit Namensnennung
`blocked-103-…`). Die Nummern `100`/`101` sind gegenüber Rev. 3 **getauscht** (Default ist jetzt
`subagent`, D-OQ1) — es gibt keine Altbelegung.
**Verifikation:** `tests/scenarios/run.sh 10` → **4× PASS** (`100`, `101`, `102`, `104`);
`--validate` je ausgeführtem Szenario rc 0; ein `grep`-Test stellt sicher, dass `blocked-103-…` nicht
vom `10*`-Match erfasst wird.
**Depends on:** T15, T16, T19 · **Größe:** M

### Task 18: Positionsmodell + Mapping-Doku (`DECIDED 2026-11-09`, D-OQ1/D-OQ3; AC-32/AC-37)

**Files:** `docs/concepts/active/orchestrator-topology.md` (neuer Abschnitt „Positionen" vor der
Matrix), `README.md` (`:210`, `:410-419`), `docs/CODEBASE_OVERVIEW.md` (`:1724-1727`),
`docs/concepts/active/main-chat-orchestrator-mode.md` (`:109`, `:178`);
`tests/test_orchestrator_topology_docs.py` (ändern).
**Interfaces:** Produces die drei Positions-Definitionen (`POS-1`, `POS-2`, `POS-3`), die
Mapping-Tabelle `mode` × `topology` → Position (zehn Zeilen) und `EXPECTED_POSITION_MAP:
dict[tuple[str, str], str]` im Doku-Test; Consumes Spec §3.8.1/§3.8.2 und die Matrix aus T15.
**Test-zuerst:**
`test_position_model_has_three_positions` — die Concept-Doc definiert genau `POS-1`, `POS-2`,
`POS-3`, je mit den sieben Feldern aus Spec §3.8.1; keine Position fehlt, keine vierte existiert
(AC-32).
`test_position_mapping_has_ten_rows_without_empty_cells` — die Mapping-Tabelle hat zehn
`mode`×`topology`-Zeilen, jede mit Positionsangabe aus `{POS-1, POS-2, POS-3, keine Position}`, und
**keine** Zelle ist leer (AC-32).
`test_positions_are_defined_before_they_are_used` — jede in der Matrix (T15) verwendete Positions-ID
ist in der Concept-Doc **vor** der Matrix definiert (Reihenfolge-Prüfung, AC-32).
`test_readme_explains_both_opencode_positions` — `README.md` nennt `mode: main-chat` (POS-1) **und**
`topology: subagent` (POS-2) als gleichwertige Opencode-Positionen; die Mermaid-Darstellung hat für
`primary` und `subagent` je einen Knoten (B-2/B-3 der Spec bleiben erfüllt, AC-32).
`test_codebase_overview_names_both_positions` — `docs/CODEBASE_OVERVIEW.md` beschreibt beide
Positionen statt einer absoluten Aussage (AC-32).
`test_advisory_subagent_carries_1182_condition_everywhere` — jede Stelle, die `advisory` × `subagent`
empfiehlt (Concept-Doc, `README.md`), trägt im selben Absatz „#1182" (AC-37).
**Implementierung:** Positions-Abschnitt aus Spec §3.8.1/§3.8.2 übernehmen (deutsch, gleiche
Tabellenspalten), in `README.md` die Kurzfassung in Englisch ergänzen (beide Positionen, `POS-3` als
optional), in `docs/CODEBASE_OVERVIEW.md` den Singleton-Absatz topologie-qualifizieren. Keine
Code-Änderung.
**Verifikation:** `python3 -m pytest tests/test_orchestrator_topology_docs.py --basetemp="$PYTEST_BASETEMP"`
→ **rot (6 failed)** vor, **grün** nach der Doku-Änderung; `tests/test_orchestrator_topology_docs.py`
und `tests/test_orchestrator_mode_topology_matrix.py` gemeinsam 0 failed.
**Depends on:** T15, T16 · **Größe:** M

### Task 19: Opencode-Generierung je Position (D-OQ2; AC-33/AC-34/AC-35/AC-36)

**Files:** neu `tests/test_opencode_positions.py`; `scripts/lib/provider_transform.py` (`:494-499`,
`:1052`, `:1298`) und `scripts/lib/isolation.py` (`:864-924`, `:926-970`) **nur**, wenn ein Test rot
wird.
**Interfaces:** Consumes `resolve_topology` (T1), `role_emitted_for_provider`
(`scripts/lib/active_set.py:206-217`), `_opencode_entry_point` und
`reconcile_opencode_surface_gate(..., topology=…)` (T14). Produces die drei Positions-Tests plus den
Determinismus-Test für die deklarierte Position.
**Test-zuerst:**
`test_opencode_main_chat_position_generates_clean` (**POS-1**) — `mode: main-chat`: keine generierte
`orchestrator`-Datei, `opencode.json` ohne von der Sync geschriebenen `default_agent`, keine
`permissions[]`-Tripel; ein **verwalteter** Alt-Wert wird per State-Rollback zurückgenommen; ein
**nutzereigener** Wert bleibt und erzeugt genau eine `opencode.default-agent.dangling`-Warnung
(`isolation.py:910-924`). Parametrisiert über `surface-version: v1` **und** `v2` (AC-34).
`test_opencode_subagent_position_generates_clean` (**POS-2**) — `topology: subagent`: Frontmatter
`mode: subagent` und **nicht** `mode: primary` (`provider_transform.py:1052`, `:1298`), kein
`default_agent`, keine Tripel; v1: genau eine Log-Warnung **und** ein Finding
(`gate-inactive`, §6.4-Zählregel), v2: genau die ursachenbewusste Log-Warnung aus G7, **kein**
Finding. Parametrisiert über v1/v2 (AC-35).
`test_opencode_primary_position_generates_clean` (**POS-3**) — `topology: primary`: `mode: primary`,
`default_agent: orchestrator`, Write-Scope-Lock und Deny vorhanden (Regressionsschutz, AC-33).
`test_explicit_subagent_topology_changes_output_deterministically` — deklariert vs. abgeleitet:
`ORCH_TOPOLOGY == "subagent"`, `ORCH_TOPOLOGY_EFFECTIVE_SOURCE == "project"`,
`ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT == "true"` gegenüber `""`/`"derived"`/`"false"`; zwei Renderings mit
vertauschter Provider-Reihenfolge sind byte-identisch; die Textdifferenz liegt **nur** im expliziten
Zweig (zwei Golden-Fixtures, AC-36).
`test_no_position_is_tested_in_a_combined_case` — Quelltext-Grep auf `tests/test_opencode_positions.py`:
kein Testname enthält zwei Positions-IDs; die drei `*_position_generates_clean`-Tests existieren
(AC-33).
**Implementierung:** Test-zuerst; erwartet wird **grün** für POS-1/POS-3 (heutiges Verhalten trägt),
**rot** höchstens für POS-2, falls das Frontmatter-`mode` bei `effective != "primary"` aus dem
Template statt auf `subagent` fällt. Fix ist lokal in `provider_transform.py` (der `mode`-Fallback
`:1052`, `:1298` bleibt die einzige Stelle) bzw. im Entry-Point-Rollback in `isolation.py` — **kein**
neuer Resolver, **kein** Provider-Name im Code.
**Verifikation:** `python3 -m pytest tests/test_opencode_positions.py --basetemp="$PYTEST_BASETEMP"`
→ **grün**; `tests/test_provider_transform_topology.py`, `tests/test_opencode_primary_edit_lock.py`
0 failed; danach `python3 scripts/sync.py`, Diff-Prüfung der Agent-Dateien und `opencode.json`,
Commit, **dann** `--check` rc 0 (AC-31).
**Depends on:** T14, T18 · **Größe:** M

### Task 20: Explizite Deklaration `orchestrator.topology: subagent` (D-OQ1; AC-36/AC-31)

**Files:** `.meta-config/project.yaml` (Orchestrator-Block, eine Zeile nach `:311`); regenerierte
Artefakte (`AGENTS.md`, `.claude/rules/use-orchestrator.md`, `.claude/agents/*.md`,
`.opencode/agents/*.md`, `opencode.json`); `tests/test_opencode_positions.py` (aus T19, zwei
zusätzliche Tests).
**Interfaces:** Produces die **deklarierte** Position dieses Repos (`source == "project"`,
`ORCH_TOPOLOGY == "subagent"`) und die daraus folgende Regeneration; Consumes die Render-Seams aus
T4–T10 und die Positions-Parität aus T19. Kein Schema-Change (Spec §6.1), kein neuer Key.
**Test-zuerst:**
`test_repo_declares_subagent_explicitly` — `.meta-config/project.yaml` enthält im
`orchestrator`-Block `topology: subagent`; **keine** `provider-overrides` sind dafür nötig
(AC-36).
`test_repo_render_is_the_explicit_branch` — gerendert mit der Repo-Config: `ORCH_TOPOLOGY ==
"subagent"`, `ORCH_TOPOLOGY_EXPLICIT == "true"`, `ORCH_TOPOLOGY_EFFECTIVE_SOURCE == "project"`, und
`AGENTS.md`/`.claude/agents/orchestrator.md` tragen den expliziten `subagent`-Zweig
(Golden-Fixture aus T8/AC-36).
`test_repo_has_no_derived_position_warnings` — `python3 scripts/sync.py --validate` erzeugt **kein**
`orchestrator-topology.main-chat-derived-primary` und **kein**
`orchestrator-topology.strict-primary-entry-mismatch`; `strict`- und `subagent`-Zustand bleiben
rc-kompatibel zu M0/§17 (AC-36).
`test_declaration_is_deterministic` — zwei aufeinanderfolgende `python3 scripts/sync.py`-Läufe
erzeugen byte-identische Artefakte; `--check` rc 0 (AC-31).
**Implementierung:** genau eine Zeile `topology: subagent` im `orchestrator`-Block von
`.meta-config/project.yaml` (nach dem `mode: strict`-Eintrag, `:311`), dann `python3 scripts/sync.py`,
Diff-Prüfung, Commit. **Keine** weitere Config-Änderung, kein `provider-overrides`.
**Erwartetes, beabsichtigtes Warnbild danach:** auf diesem Repo erscheint im Sync-Log
`orchestrator-topology.gate-inactive` (v1 + POS-2: kein `default_agent`, kein Deny) — das ist die
ehrliche Meldung aus §6.4 der Spec, **kein** Fehler; rc bleibt 0. Ebenso darf der v1-Consistency-Check
`runtime gate is wanted for provider` (Tier `permission`) genau einmal feuern; er ist WARNING.
**Rollback (verbindlich):** Zeile entfernen, `python3 scripts/sync.py` erneut ausführen, Diff gegen
den Stand vor T20 prüfen — der Baum fällt auf die **abgeleitete** `primary`-Position zurück
(Golden-Fixture aus T8/T21, AC-17). Der Rollback ist ein eigener Commit (`revert`-Charakter), kein
Force-Push; **kein** Push/Tag/Branch durch den Executor.
**Verifikation:** `python3 -m pytest tests/test_opencode_positions.py --basetemp="$PYTEST_BASETEMP"`
→ **grün**; `python3 scripts/sync.py` → Diff zeigt **nur** die beabsichtigte Änderung (Topologie-Zweige
in `AGENTS.md`, `.claude/rules/use-orchestrator.md`, Agent-Dateien), `python3 scripts/sync.py --check`
→ **rc 0**, `--validate` → Exit-Code wie in M0/§17; Commit `feat(orchestrator): declare subagent
topology explicitly` (≤72 Zeichen, ohne BOM, Secret-Scan vorher).
**Depends on:** T17, T19 · **Größe:** S

### Task 21: Abschluss-Gate: Byte-Identität + Vollsuite (AC-16/AC-26/AC-27)

**Files:** keine neuen Dateien; Test-Ergänzung in
`tests/test_orchestrator_topology_effective_flags.py` und `tests/test_orchestrator_topology_docs.py`.
**Interfaces:** Consumes die Golden-Fixtures aus M0 (§17), T7/T8 und die deklarierte Position aus T20;
Produces den Abschlussnachweis (Byte-Identität, Schema-Diff, Vollsuite).
**Test-zuerst:**
`test_unset_topology_subagent_render_is_byte_identical` — Golden-Fixture: Rendering für alle aktiven
Provider **ohne** `topology`-Key **und** mit `effective == "subagent"` ist byte-gleich zum
Baseline-Stand `aaed14c2` (AC-16/AC-27).
`test_derived_primary_render_matches_intentional_golden` — ohne `topology`-Key, abgeleitetes
`primary` (Zustand **vor** T20): weicht **beabsichtigt** ab und entspricht der neuen Golden-Fixture
(Gate-Text, `orchestrator.md`/`_reference-agent.md`, Singleton-Block); keine
Byte-Identitäts-Zusage (AC-17, Rev. 3 / RVW2-1190-01).
`test_declared_primary_render_matches_new_golden` — deklariertes `topology: primary` weicht
**beabsichtigt** ab und entspricht der neuen Golden-Fixture (AC-27).
`test_declared_subagent_render_matches_new_golden` — deklariertes `topology: subagent` (der Zustand
dieses Repos ab T20) entspricht der Golden-Fixture aus T8/T19 und unterscheidet sich deterministisch
vom abgeleiteten Fall (AC-36).
`test_schema_has_no_new_properties` — Diff-Assertion gegen den Stand vor der Umsetzung:
`config/project-config.schema.json` hat dieselben `properties` (nur `description`-Texte dürfen
abweichen) (AC-26).
`test_default_effective_is_primary_or_subagent` — `ORCH_TOPOLOGY_EFFECTIVE ∈ {"primary","subagent"}`
im Default (AC-16).
**Implementierung:** keine Produktionsänderung; nur Fixtures/Assertions.
**Verifikation:** `python3 -m pytest tests/ --basetemp="$PYTEST_BASETEMP"` → **0 failed** (Referenz:
die in M0/§17 dokumentierte Testzahl der Topologie-Familie bleibt unverändert grün; 19 Dateien
matchen `tests/*topology*.py`); `python3 scripts/sync.py --check` → **rc 0**; `python3 scripts/sync.py
--validate` → Exit-Code wie in M0/§17 dokumentiert.
**Depends on:** T1–T17, T18–T20 · **Größe:** S

---

## 6. Interfaces & Signaturen

### 6.1 Flags (verbindlich)

| Flag | Werte | Quelle | Condition-Flag? |
|---|---|---|---|
| `ORCH_TOPOLOGY` | `""` \| `primary` \| `subagent` \| `hybrid` | deklariert (`topology_flags`, `variables.py:330-356`) | **nein** (String) |
| `ORCH_TOPOLOGY_EXPLICIT` | `true`\|`false` | Projekt-Scope-Deklaration | ja (bestehend) |
| `ORCH_TOPOLOGY_{PRIMARY,SUBAGENT,HYBRID}` | genau eines `true` bei deklariertem Wert | deklariert | ja (bestehend) |
| `ORCH_TOPOLOGY_SOURCE` | `provider-override`\|`project`\|`derived` | deklariert | **nein** (String) |
| **`ORCH_TOPOLOGY_EFFECTIVE`** | `primary`\|`subagent`\|`hybrid` (**nie** `none`/leer) | `resolution.effective` | **nein** (String) |
| **`ORCH_TOPOLOGY_EFFECTIVE_SOURCE`** | `provider-override`\|`project`\|`derived` | `resolution.source` | **nein** (String, Audit-/Doku-Flag) |
| **`ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT`** | `true`\|`false` | `source != "derived"` (Spec Rev. 2) | ja |
| **`ORCH_TOPOLOGY_EFFECTIVE_{PRIMARY,SUBAGENT,HYBRID}`** | genau eines `true` | `resolution.effective` | ja |
| **`ORCH_TOPOLOGY_INERT`** | `true`\|`false` | `mode == "main-chat"` | ja |

**Position ist kein Flag und kein Key (`DECIDED 2026-11-09`, D-OQ1).** `POS-1`/`POS-2`/`POS-3` werden
aus `mode` + `effective` abgeleitet (Spec §3.8.2) und in Doku/Tests verwendet; es gibt **kein**
`ORCH_POSITION_*`-Flag und keinen `position`-Key. Die Deklaration dieses Repos (`topology: subagent`,
T20) nutzt ausschließlich den bestehenden Key `orchestrator.topology`.

### 6.2 Funktionen

| Symbol | Art | Vertrag |
|---|---|---|
| `variables._effective_topology_flags` | neu | `(resolution: TopologyResolution, *, mode: str) -> dict[str, str]` |
| `variables._provider_topology_flags` | neu | `(config, provider, *, agent_meta_root: Path, mode: str, active_set) -> dict[str, str]` — `active_set` ist **Pflicht-Keyword** (derselbe Set wie die Emission); lädt Caps + Provider-Registry, ruft `resolve_topology` **einmal** |
| `config._build_orch_variables` | geändert (Rumpf) | zusätzliche `variables.update(_effective_topology_flags(...))` für die provider-lose **nicht autoritative** Basis (K-3, RVW2-1190-09) |
| `rules._merged_rule_vars` | geändert (Rumpf) | `provider_vars.update(_provider_topology_flags(..., active_set=active_set))` (`:289-293`) |
| `rules.sync_rules` / `rules.sync_embedded_rule_files` | **Signatur** | zusätzliches Keyword `active_set` (durchgereicht an `_merged_rule_vars`) |
| `context._build_managed_block` | geändert (Rumpf) | liest die provider-skopierten Effektiv-Flags aus dem übergebenen `variables`-Dict (keine eigene Neuauflösung; `:2575-2586` bleibt für `declared`) |
| `context.sync_context_for_provider` | **Signatur** | zusätzliches Pflicht-Keyword `active_set` |
| `context._dispatch_context_strategy` | **Signatur** | zusätzliches Pflicht-Keyword `active_set` (durchgereicht an alle drei Strategien) |
| `context._position_aware_agent_hints` | neu | `(config, provider, provider_config, agent_meta_root, target_name, *, active_set, position) -> dict[str, str]` — entscheidet Position vs. neutral über `_shared_context_users` (`:2246`) |
| `sync_pipeline._sync_stage_contexts` | **Signatur** | zusätzliches Pflicht-Keyword `active_set`; ruft **einmal** pro Provider `_provider_topology_flags(...)` und mischt die Flags in `provider_variables` (Stage 4) |
| `agent_sync._build_provider_vars` | **Signatur** | `(pc, provider, variables, agent_meta_root, config=None, *, active_set) -> dict` (Keyword Pflicht) |
| `agent_sync._singleton_constraint_block` | neu | `(effective: str, *, inert: bool) -> str` (drei Varianten) |
| `agents.build_agent_hints` | **Signatur** | `(config, agent_meta_root, include_table=True, *, template_roles=None, warn_sink=None, active_set=None, position: str = "neutral") -> str` — reine Textwahl, **keine** Provider-/Ziel-Auflösung |
| `isolation.reconcile_opencode_surface_gate` | **Signatur** | `(project_root, config, provider, provider_config, agent_meta_root, log, dry_run, *, active_set, topology=None) -> None` — **Durchreichung**, keine Neuresolution |
| `isolation._opencode_v2_gate_permissions` | **Signatur** | `(config, provider, agent_meta_root, provider_config, capabilities, plugin_mode, *, active_set, topology=None) -> list[dict]` |
| `isolation._v2_gate_invariant_warning` | **Signatur** | `(provider: str, desired: str \| None, *, merge_rewrites: bool, topology=None) -> str` |
| `consistency.topology._strict_primary_entry_mismatch` | neu | `(agent_meta_root: Path, provider_config: dict, provider: str, pc: dict, *, mode: str, effective: str) -> str \| None` |
| `consistency.orchestrator_strict.check_orchestrator_strict_hook_support` | geändert (Rumpf) | zusätzliches INFO `orchestrator-strict.direct-dispatch-inert` |

### 6.3 Check-IDs (neu)

| ID | Severity | Bedingung | Text-Anker |
|---|---|---|---|
| `orchestrator-topology.main-chat-derived-primary` | WARNING | `mode == "main-chat"` ∧ kein `topology` ∧ `effective == "primary"` | Spec §4-D-Q1, gepinnt |
| `orchestrator-topology.strict-primary-entry-mismatch` | WARNING | `mode == "strict"` ∧ `effective == "primary"` ∧ `owns_gate_surface` ∧ `default_agent` fehlt/fremd | Spec §4-D-Q2, gepinnt |
| `orchestrator-strict.direct-dispatch-inert` | INFO | `mode == "main-chat"` ∧ Key **präsent**; einmal pro Lauf, Kanal `--validate` | Spec §4-D-Q5, gepinnt |

Ablage (Rev. 2): die zwei `orchestrator-topology.*`-IDs in `consistency/topology.py`, die
`orchestrator-strict.*`-ID in `consistency/orchestrator_strict.py`.

Bestehende IDs bleiben unverändert: `orchestrator-topology.{degraded, hybrid-unverified,
main-chat-supersedes, gate-inactive, default-agent-conflict, singleton-redundant,
instances-clamped}` (`consistency/topology.py:65-71`), `orchestrator-strict.no-hook-support`
(`consistency/orchestrator_strict.py:36`).

### 6.4 Matrix-Datenstruktur

- **Quelle (Doku):** vier Markdown-Tabellen in `docs/concepts/active/orchestrator-topology.md`
  (je Surface: `mode` × `topology` → Urteil + Tier + Lock + Hop + A2A).
- **Erwartung (Test):** `EXPECTED_MATRIX: dict[tuple[str, str, str], str]` in
  `tests/test_orchestrator_topology_docs.py` — Schlüssel `(surface, mode, topology)`,
  Wert `RECOMMENDED|ALLOWED|DEGRADED|FORBIDDEN`. 24 Einträge, Test vergleicht Doc-Parsing gegen
  diese Struktur (AC-6/AC-7). Die **Positions-Spalte** (`POS-1`/`POS-2`/`POS-3`) wird zusätzlich als
  `EXPECTED_POSITION_MAP: dict[tuple[str, str], str]` geparst (T18/AC-32); sie ist **nicht** Teil des
  Urteils-Schlüssels.
- **Produktionsdaten unverändert:** `config.py:435-463` (`ORCHESTRATOR_TOPOLOGY_MATRIX`,
  `orchestrator_topology_cell`) bleibt die normative Zell-Semantik für den Validator.

---

## 7. Teststrategie

1. **Bestehende Suite bleibt Referenz.** Die Zahl der Topologie-Testdateien/-Tests wird in **M0**
   gemessen und in §17 dokumentiert (kein Vorab-Zitat: 19 Dateien matchen `tests/*topology*.py`,
   Glob verifiziert). Zusätzlich unverändert grün zu halten:
   `tests/test_orchestrator_topology_entrypoint.py` (`:34-69`, `:124-139`),
   `tests/test_orchestrator_topology_validator.py`, `tests/test_orchestrator_topology_resolver.py`,
   `tests/test_topology_capability_invariant.py`,
   `tests/test_opencode_primary_edit_lock.py`, `tests/test_provider_transform_topology.py`.
2. **Neue Testdateien (11):** `test_orchestrator_topology_effective_flags.py`,
   `test_orchestrator_topology_render_parity.py`, `test_use_orchestrator_topology_rendering.py`,
   `test_orchestrator_template_topology_wording.py`, `test_singleton_block_topology.py`,
   `test_entry_hint_topology.py`, `test_orchestrator_topology_checks.py`,
   `test_isolation_v2_topology_reconcile.py`, `test_orchestrator_mode_topology_matrix.py`,
   `test_provider_transform_topology_generic.py` (Rev. 3 / RVW2-1190-10) sowie
   `test_opencode_positions.py` (Rev. 4, D-OQ2).
3. **Matrix-Tests:** 24 Zellen (4 Surfaces × 6 Kombinationen) in
   `test_orchestrator_mode_topology_matrix.py`; je Zelle vier Assertions
   (`effective`, Frontmatter-`mode`/Lock, Deny-Form, Warnbild) = **24 × 4 = 96** parametrisierte
   Fälle. `hybrid` ist **keine** eigene Zeile (degradiert immer, `provider-capabilities.yaml:209`).
4. **Zwischentests je Meilenstein:** M1 → T1/T2/T3-Dateien; M2 → Parity; M3 → vier
   Wortlaut-Dateien; M4 → Checks; M5 → Reconcile; M6 → Doc/Matrix/Generic; M7 → Doc-Test;
   M8 → Positions-/Mapping-Doku; M9 → `test_opencode_positions.py`; M10 → Szenarien; M11 → Deklaration
   + Abschluss.
5. **Genau ein Szenariotest am Ende (M10):** `tests/scenarios/run.sh 10` mit `100`, `101`, `102`,
   `104` (`100` = `strict × subagent` = neuer Default, `101` = `strict × primary`, `102` =
   `main-chat`, `104` = Claude `strict × subagent`); `103` (advisory×subagent) ist **blockiert durch
   #1182** und liegt als `blocked-103-advisory-subagent` **außerhalb** des `10*`-Matches, im Katalog
   als `BLOCKED` geführt. `run.sh` kennt kein `SKIP` (`run.sh:231`) — eine Skip-Konvention wird nicht
   eingeführt (AC-29).
   **Nummernwahl:** der Katalog führt `88`–`93` (`tests/scenarios/registry.md:127-132`) und endet
   bei `87` in der Nachtragsliste (`:168-176`); kein Eintrag ≥ `100` existiert. Die Aussage
   „`94`–`99` sind für die Config-Welle reserviert" ist eine **Annahme** aus der Config-Welle
   (PR #1212, extern zu diesem Vorhaben, hier **nicht** verifiziert) — für die Wahl `100`+ ist sie
   nicht tragend.
6. **Nicht-Ziel der Teststrategie:** kein neuer Runtime-Test für den Guard-Hook (#1210 begrenzt
   die Erzwingbarkeit; D-Q2 (c) bleibt Nutzungsfehler).

---

## 8. Migration & Rollback

- **Genau eine Config-Änderung — und sie ist ein eigener Task (`DECIDED 2026-11-09`, D-OQ1).** Keine
  neuen Keys (§6.1 der Spec); `config/project-config.schema.json` bleibt strukturell unverändert
  (AC-26). T20 setzt **eine** Zeile `orchestrator.topology: subagent` in `.meta-config/project.yaml`
  (nach Zeile 311) — **nach** dem Code-Fix (T19), mit Regeneration, Commit und Rollback
  (Zeile entfernen ⇒ Ableitung greift wieder; Golden-Fixture aus T8/T21). Es ist **keine**
  `primary`-Deklaration: der Default dieses Repos ist `strict × subagent`.
- **Default-Verhalten byte-identisch — nur für `topology` ungesetzt ∧ `effective == "subagent"`:**
  kein `topology`-Key **und** alle aktiven Renderer lösen `subagent` auf ⇒ gleiche Emission
  (`provider_transform.py:488-499`), gleicher `subagent`-Regelzweig (T7-Golden), gleicher
  Singleton-Text (T9-Golden), **gleicher** Einstiegshinweis (`agents.py:174`, in Rev. 3 bewusst
  unverändert). Nachweis: T21-Golden-Fixture + `sync --check` rc 0.
- **Abgeleitetes `primary` (Key ungesetzt) ändert sich beabsichtigt:** in diesem Repo leitet der
  Resolver `primary` ab (`topology.py:135-140`), deshalb ersetzt der `EFFECTIVE_PRIMARY`-Zweig den
  heutigen else-Zweig — Gate-Text (G1), `orchestrator.md`/`_reference-agent.md`/a2a
  (`EFFECTIVE_EXPLICIT`), Singleton-Block (G4) und Einstiegshinweis (G5). Golden-Fixture des neuen
  Texts, **keine** Byte-Identitäts-Zusage (AC-17, Rev. 3 / RVW2-1190-01).
- **Deklariertes `topology: primary` ändert sich ebenfalls beabsichtigt:** derselbe
  `EFFECTIVE_PRIMARY`-Zweig ersetzt den heutigen expliziten Zweig. Dafür gilt eine
  **Golden-Fixture des neuen Texts** (T8/T21), keine Byte-Identitäts-Zusage (AC-27).
- **Deklariertes `topology: subagent` (dieses Repo ab T20) ändert sich beabsichtigt:** der
  explizite `subagent`-Zweig ersetzt den heutigen else-Zweig; `ORCH_TOPOLOGY_EFFECTIVE_SOURCE` wird
  `project` statt `derived`, `ORCH_TOPOLOGY_EXPLICIT` `true` statt `false`. Golden-Fixture aus
  T8/T19, Determinismus-Test in T20 (AC-36). **Rollback:** Zeile entfernen + `sync` ⇒ Baum fällt auf
  den abgeleiteten Zustand zurück.
- **Rollback = Revert der Flag-/Wortlaut-/Check-Änderungen.** Alle neuen Flags sind additiv; ein
  Revert entfernt sie, ohne dass Configs oder Capability-Daten angefasst werden müssen. Die
  fail-closed-Registrierung macht einen Teil-Revert ungefährlich (fehlende Flags ⇒ historischer
  Zweig), aber nicht byte-sicher — deshalb Revert **je Meilenstein/Task-Commit**.
- **Keine Capability-Änderung:** `topology_support`/`topology_degrade`/`topology_verified_state`
  bleiben unangetastet (Spec §7, `config/provider-capabilities.yaml:206-209`, `:263-266`).
- **Doku-Rollback:** T15/T16/T18 sind reine Textänderungen; ein Revert stellt die alte Matrix/Aussagen
  wieder her, ohne Codefolgen.

---

## 9. Risiko-Tabelle

| # | Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| P-1 | **Inkonsistente derived/declared-Flags:** ein Seam nutzt `declared`, ein anderer `effective` (heutiger Zustand: Emission `effective`, Rendering `declared`) | derselbe Build erzeugt widersprüchliche Artefakte; AC-17 bleibt offen | Genau **ein** Helfer `_provider_topology_flags`; T4/T5/T6 prüfen alle drei Seams gegen dieselbe Erwartung; Grep-Test, dass kein neuer Seam `_topology_flags` allein für Semantik nutzt |
| P-2 | **v2-Surface:** topology-blinder Reconcile schreibt Deny ohne Entry Point oder empfiehlt die Rücknahme der Topologie | #1006-Lockout / irreführende Remediation | T14: `topology=` an **allen** `config is not None`-Aufrufen (AC-23, AST-Assertion); D1a-Guard bleibt unverändert |
| P-3 | **Gate-Aussagen ohne Runtime:** `strict` suggeriert Erzwingung, die auf `permission`/`plugin`-`observe` nur teilweise trägt | Nutzer überschätzt die Zusage | Tier-Absatz bleibt in beiden G1-Varianten; `orchestrator-topology.gate-inactive` bleibt Pflicht (T14/AC-22) |
| P-4 | **Doku-Drift:** elf Stellen, davon zwei gegenläufige Statusaussagen (B-7/B-8) | Widerspruch bleibt sichtbar, Doku-Test schlägt fehl | T16 arbeitet die Liste einzeln ab; Test pinnt „keine absolute Aussage ohne Qualifier" |
| P-5 | **#1182-Abhängigkeit:** `advisory` + `context-profile: compact` bricht am fehlenden `CRITICAL GATE`-Heading | Szenario 103 nicht lauffähig; Team-Empfehlung praktisch blockiert | G1 benennt die Sektion **nicht** um (T7-Test); Szenario 103 als `BLOCKED` markiert; Empfehlung mit Blockerhinweis |
| P-6 | **Warnungs-Flut** auf Bestandsprojekten (R-1 der Spec) | Checks werden ignoriert | Jede Bedingung an Präsenz/Widerspruch gebunden: D-Q1 nur `main-chat` + derived `primary`, D-Q5 nur `main-chat` **und** präsenter Key; Dedup je Check-ID/Provider/Lauf (`_append_once`, `consistency/topology.py:164-183`) |
| P-7 | **Byte-Identität bricht** durch neue Conditional-Flags (R-2) | `sync --check`-Drift auf allen Consumern | Vier Registrierungen + Golden-Fixtures (T2/T21); `EFFECTIVE_EXPLICIT` bewusst `source != "derived"` (K-1), sonst kippt jeder Default |
| P-8 | **Vierter Resolver** (R-3) | Emission/Rendering driften erneut | `_provider_topology_flags` ist der einzige neue Pfad und ruft ausschließlich `resolve_topology` |
| P-9 | **Merge-Konflikte** mit #1187/#1186/#1188/#1181 | halb gefixte Zustände | Serialisierungsregel §12 |
| P-10 | **Positionen werden vermischt:** ein Test/eine Doku-Aussage behandelt `main-chat` und `subagent` gemeinsam, dadurch bleibt eine Position ungetestet | eine der beiden first-class-Opencode-Positionen bricht unbemerkt (D-OQ2) | Je Position ein eigener Test (T19), Quelltext-Grep gegen kombinierte Fälle, Positions-Spalte in Matrix und Mapping (T18/AC-32/AC-33) |
| P-11 | **Explizite Deklaration driftet zurück:** ein späterer Edit entfernt `orchestrator.topology: subagent` und die derived-vs-declared-Divergenz kehrt zurück | Lücken 2/4/5 werden im Alltag wieder sichtbar; D-Q1 feuert erneut | T20-Test `test_repo_declares_subagent_explicitly` pinnt die Zeile; Determinismus-Test + `--check` rc 0 als Regressionsschutz (AC-36) |
| P-12 | **`advisory × subagent` wird als freigegeben gelesen** (D-OQ3) | Team stellt vor #1182 um und läuft in den compact-Bruch | Bedingung an jeder Empfehlungsstelle (T18/AC-37); Szenario `103` bleibt `BLOCKED` |

---

## 10. AC → Task-Traceability (alle 37)

| AC | Kurzinhalt | Task(s) | Test |
|---|---|---|---|
| AC-1 | WARN `main-chat-derived-primary`, rc 0 | T11 | `test_main_chat_derived_primary_warns_once` |
| AC-2 | deklariert × `main-chat` bleibt ERROR | T11 | `test_declared_topology_in_main_chat_stays_a_hard_error` |
| AC-3 | Gate-Text `primary` (positionsbasiert) vs. `subagent` | T7 | `…_primary_states_the_position`, `…_subagent_is_byte_identical`, `…_primary_has_no_spawn_claim` |
| AC-4 | WARN `strict-primary-entry-mismatch` | T12 | `test_strict_primary_without_entry_point_warns` |
| AC-5 | Lock bei `primary`, kein Lock + `gate-inactive` bei `subagent` | T14, T15 | `test_v2_primary_still_writes_the_triples` (Regression `test_opencode_primary_edit_lock.py`) |
| AC-6 | 24 Matrix-Zeilen, Urteile, `dito`-Auflösung | T15 | `test_matrix_has_24_rows`, `…verdict_vocabulary_is_closed` |
| AC-7 | genau eine `RECOMMENDED` je Surface, Menge = alle `strict × subagent`; `strict × primary` bleibt `ALLOWED` | T15 | `test_exactly_one_recommended_per_surface` |
| AC-8 | v2: `RECOMMENDED` nennt Session-Ownership + `gate-inactive`, `ALLOWED` nennt `observe` + Deny | T15 | `test_v2_rows_name_tier_facts_and_recommendation_basis` |
| AC-9 | Gemini `primary` → `subagent` + `degraded` | T15 | `test_gemini_primary_degrades_with_one_warning` |
| AC-10 | Kostenabschnitt: Hop-Definition, S-Schwelle, ESTIMATE | T15 | `test_cost_section_has_hop_definition_threshold_and_estimate` |
| AC-11 | Single-User-Default `strict × subagent`, `strict × primary` als gleichwertige Option | T15 | `test_single_user_recommendation_is_strict_subagent_with_primary_option` |
| AC-12 | INFO `direct-dispatch-inert` nur unter `main-chat`, ein INFO pro Lauf, Kanal `--validate` | T13 | `test_direct_dispatch_key_present_under_main_chat_is_info`, `test_info_is_emitted_once_per_run_not_per_provider`, `test_key_under_strict_produces_no_finding` |
| AC-13 | kein Finding ohne Key / unter `strict`/`advisory`; Präsenz-Semantik | T13 | `test_absent_key_produces_no_finding`, `…advisory_mode_produces_no_finding`, `…presence_not_truthiness` |
| AC-14 | Gate verzweigt nur über `EFFECTIVE_PRIMARY` | T7, T8 | `test_gate_rule_has_no_provider_or_declared_condition` |
| AC-15 | fünf Bool-Flags in vier Registrierungen; zwei String-Flags nur `_BUILTIN_VARS` | T1, T2 | `test_each_registration_is_load_bearing`, `test_string_flags_are_not_conditionals` |
| AC-16 | Default byte-identisch nur bei `effective == "subagent"`; `EFFECTIVE` nie `none` | T3, T21 | `test_unset_topology_subagent_render_is_byte_identical`, `…_never_none` |
| AC-17 | derived `primary` ohne „nur main_chat"-Satz, beabsichtigte Änderung mit Golden | T8, T21 | `test_derived_primary_has_no_main_chat_only_claim`, `test_derived_primary_render_matches_intentional_golden` |
| AC-18 | Provider-Override paritätisch in Agent-Templates | T6 | `test_agent_templates_carry_provider_scoped_effective_flags` |
| AC-19 | Singleton-Block topologieabhängig, `NIEMALS` bleibt | T9 | `test_primary_block_names_the_session_entry` |
| AC-20 | Einstiegshinweis dreiwertig + neutraler Shared-File-Text; `subagent` unverändert | T5, T10 | `test_hint_primary_names_the_entry`, `test_hint_subagent_keeps_historic_wording`, `…shared_hint_is_provider_neutral` |
| AC-21 | `mode` beeinflusst `effective` nicht; Check-Ablage 2× `topology.py` / 1× `orchestrator_strict.py` | T1, T11, T12, T13 | `test_resolve_topology_ignores_mode`, `test_check_lives_in_consistency_topology`, `test_check_lives_in_orchestrator_strict` |
| AC-22 | v2 + `subagent`: keine Tripel, eine Log-Warnung, kein Finding, keine falsche Remediation; v1-Zählregel | T14 | `test_v2_subagent_writes_no_permission_triples`, `…emits_exactly_one_log_warning`, `…v1_subagent_counts_per_channel` |
| AC-23 | drei `_opencode_entry_point`-Aufrufe + beide Reconcile-Aufrufer mit `topology=` (Trefferzahlen + Objekt-Identität) | T14 | `test_all_three_entry_point_calls_pass_topology`, `test_both_reconcile_callers_pass_topology`, `test_reconcile_passes_the_resolved_object_downstream` |
| AC-24 | Testliste G8 deckt die sieben Flächen inkl. `ROLE_ORCHESTRATOR_ACTIVE` unter `main-chat` (konkrete Assertion) | T1, T4–T10, T14, T15 | Summe der neuen Dateien; `test_role_orchestrator_active_under_main_chat_prose` (T10) |
| AC-25 | elf Doku-Befunde einzeln (B-9 als Render-Widerspruch), Datei-Scope + Ausnahmen | T16 | `test_no_absolute_singleton_claim_without_topology_qualifier`, `test_gate_render_is_single_variant_per_file` |
| AC-26 | keine neuen Schema-Properties | T21 | `test_schema_has_no_new_properties` |
| AC-27 | `--check` byte-identisch nur bei `ungesetzt ∧ effective == "subagent"`; derived **und** deklariert `primary` = beabsichtigte Änderung mit Golden | T21, T8 | Vollsuite + `--check`/`--validate`, `test_derived_primary_render_matches_intentional_golden`, `test_declared_primary_render_matches_new_golden` |
| AC-28 | ADR D-Q1…D-Q5 **und** D-OQ1…D-OQ3 + Matrix im Concept | T15, T16 | `test_adr_records_dq1_to_dq5`, `test_adr_records_doq1_to_doq3` |
| AC-29 | Szenarien: `100`=`strict × subagent`, `101`=`primary`, `102`=`main-chat`, `104`=Claude, `103` als `BLOCKED` außerhalb `10*` | T17 | `tests/scenarios/run.sh 10` → 4 PASS + Grep-Test auf Namensschema |
| AC-30 | ein `ActiveSet` für Emission + drei Render-Seams; kein Seam liest die provider-lose Basis | T3, T4, T5, T6 | `test_rules_passes_the_shared_active_set`, `test_context_uses_the_shared_active_set`, `test_agents_use_the_shared_active_set`, `test_no_render_seam_reads_the_global_basis` |
| AC-31 | Regeneration + Commit je emissionsrelevantem Task; danach `--check` rc 0 | T4–T10, T14, T19, T20, T21 | Verifikationsschritt jedes Tasks + M1/M3/M9/M10/T21 |
| AC-32 | Positionsmodell + Mapping-Doku (drei Positionen, zehn Zeilen), beide Opencode-Positionen in README/CODEBASE_OVERVIEW | T18 | `test_position_model_has_three_positions`, `test_position_mapping_has_ten_rows_without_empty_cells`, `test_readme_explains_both_opencode_positions`, `test_codebase_overview_names_both_positions` |
| AC-33 | je **ein** Test pro Position (POS-1/POS-2/POS-3), v1 **und** v2 | T19 | `test_opencode_main_chat_position_generates_clean`, `test_opencode_subagent_position_generates_clean`, `test_opencode_primary_position_generates_clean`, `test_no_position_is_tested_in_a_combined_case` |
| AC-34 | POS-1: kein dangling `default_agent`, keine Rolle, keine Tripel | T19, T17 | `test_opencode_main_chat_position_generates_clean`, Szenario `102` |
| AC-35 | POS-2: kein `mode: primary`, kein `default_agent`, ehrliches `gate-inactive` | T19, T17 | `test_opencode_subagent_position_generates_clean`, Szenario `100` |
| AC-36 | deklariertes `topology: subagent` ändert die Ausgabe deterministisch (declared vs. derived) | T19, T20, T21 | `test_explicit_subagent_topology_changes_output_deterministically`, `test_repo_render_is_the_explicit_branch`, `test_declared_subagent_render_matches_new_golden` |
| AC-37 | `advisory × subagent` überall als #1182-abhängig markiert | T18, T17 | `test_advisory_subagent_carries_1182_condition_everywhere`, Szenario `103` (`BLOCKED`) |

---

## 11. Backlog- und Issue-Bezug

| Issue | Status | Bezug zu diesem Plan |
|---|---|---|
| **#1190** | offen | Haupt-Issue; Quelle der D-Q1…D-Q5 |
| **#1077** | closed | Mechanismus (`topology`-Enum, D1–D10, P3). **Nicht** neu aufrollen — T1–T21 ändern weder Enum noch Degradierung |
| **#1182** | offen | Blockiert `advisory` + `context-profile: compact` und Szenario `103`; **`DECIDED 2026-11-09` (D-OQ3):** `advisory × subagent` wird erst nach dem Fix empfohlen, bis dahin ist `strict × subagent` die Team-Empfehlung. G1 darf `# CRITICAL GATE` nicht umbenennen (T7-Test) |
| **#1007** | offen | V2-Surface-Matrix. T14 ist bewusst klein und lokal; die v2-Empfehlung stützt sich auf `docs/concepts/runtime-gate-tiers.md:36-55`, nicht auf #1007-Ergebnisse |
| **#1090** | closed | Dangling `default_agent` in `main-chat`; liefert `role_emitted_for_provider` (`isolation.py:920-924`). D-Q1 ist die Rückrichtung |
| **#794** | closed | Main-Chat-Mutationen ohne Gate (kein Runtime-Gate) — Motiv für die ehrliche Tier-Zusage (T15-Matrix) |
| **#683** | closed | `strict` blockierte delegierte Implementer — Motiv für „Nutzungsfehler statt Config-Fehler" (T7) |
| **#1210** | offen | Guard kann einen Sentinel keiner Rolle zuordnen; begrenzt, wie stark D-Q2 (c) erzwungen werden kann. Keine Abhängigkeit, gleicher Ehrlichkeits-Maßstab (kein Runtime-Test in T21) |
| **#1187** | offen | Projekt-Kontext-Injektion; berührt `agents/1-generic/*.md` und `variables.py` → Konfliktfläche (§12) |
| **#1186 / #1188 / #1181** | offen | Schema-Blöcke / Issue-Label-Taxonomie / Commit-Authority — Konfliktflächen (§12) |
| **#1209 / #1006 / #885** | offen / closed / closed | **real bestätigt** (Review-Befund W5): #1209 Artifact-Mode-Gating (Konfliktfläche `variables.py`), #1006 Entry-Point-Invariante (Vorgänger von G7), #885 Framework-Conformity-Audit (Kontext der Doku-Befunde). Keine Erfindung, keine neue Abhängigkeit |
| **#1141 / #1208** | — | Nur als Nummern geführt; kein inhaltlicher Bezug in diesem Vorhaben |

---

## 12. Cross-Vorhaben-Konfliktmatrix & Serialisierungsregel

| Datei | Dieses Vorhaben | Kollidiert mit | Serialisierung |
|---|---|---|---|
| `config/project-config.schema.json` | **keine** Property-Änderung (AC-26); nur `description` optional | **#1186** (artifact-locations), **#1188** (issue-label-taxonomy) legen neue Blöcke an (`:2469-2492` ist der Orchestrator-Block) | Dieses Vorhaben **zuletzt** und **text-only**; Schema-Diff muss leer sein (T21) |
| `scripts/lib/config.py` | T3 (Rumpf von `_build_orch_variables`, `:2013-2037`) | **#1186** (Validierung neuer Blöcke), **#1187** | Nicht parallel schneiden; T3 berührt nur den Orchestrator-Block, kein Validator-Code |
| `scripts/lib/agent_sync.py` | T6 (`_build_provider_vars`, `:489-554`), T9 (`:969-986`) | **#1181** (Commit-Authority für Edit-only-Rollen; Body nennt nur `agents/1-generic/documenter.md`, der Seam liegt plausibel hier — im Body **nicht belegt**) | Getrennte Commits; T6/T9 berühren Provider-Vars/Singleton-Block, #1181 eher den Commit-Block |
| `scripts/lib/variables.py` | T1/T2 (`:54-93`, `:311-356`, `:575-598`) | **#1209** (Artifact-Mode-Gating), **#1187** (Context-Injection-Scope) fassen `_build_variables`/Flag-Registrierung an | Reihenfolge: #1187/#1209 zuerst, dann T1/T2 (additiv, aber heiße Datei) |
| `agents/1-generic/*.md` | T8 (`orchestrator.md:19`, `_reference-agent.md:24`) | **#1187** (Projekt-Kontext in vielen Templates), **#1209** (Output-Pfad-Gating) | `orchestrator.md` ist in allen drei Vorhaben betroffen → **eine** Datei, drei Themen, Serialisierung Pflicht; `_reference-agent.md` mit #1187 abstimmen |
| `.meta-config/project.yaml` | **eine** Zeile `orchestrator.topology: subagent` (T20, nach dem Code-Fix, rückrollbar) | **#1186/#1188** (neue Blöcke), **#1187** | T20 zuletzt; die Zeile liegt im bestehenden `orchestrator`-Block, kein neuer Block, kein Schema-Effekt |
| `docs/concepts/active/orchestrator-topology.md` | T15 (Matrix mit Positions-Spalte), T18 (Positions-Abschnitt) | **#1007** (v2-Surface-Matrix) | T15/T18 sind Doku-only; die Positions-Spalte ist additiv, keine Umdeutung bestehender Zellen |
| `rules/1-generic/use-orchestrator.md` | T7 | **#1182** (compact verlangt Sektion `CRITICAL GATE`) | T7 ändert nur Sektionsinhalt, nie den Sektionstitel; #1182-Fix danach |
| `scripts/lib/isolation.py` | T14 (zwei Durchreichungen) | **#1007** (v2-Surface) | T14 zuerst (klein, lokal) |
| `scripts/lib/consistency/topology.py` | T11/T12 (drei IDs) | — | Check-ID-Doku (`runtime-gate-tiers.md:135-151`, Concept-Doc) mitpflegen |

**Serialisierungsregel (verbindlich):** Bei Überlappung gewinnt die Datei-Ownership des zuerst
gemergten Vorhabens. Vor jedem Task-Commit `git log -1 --format=%h -- <datei>` prüfen; ist die
Datei seit dem Plan-Baseline `aaed14c2` von einem anderen Vorhaben geändert worden, wird der Task
**rebase-first** ausgeführt und der Plan an dieser Stelle nachgeführt (Re-Planning-Punkt).

---

## 13. Offene Entscheidungen

### Aus der Spec (OQ-1…OQ-5) — **`DECIDED 2026-11-09`**

| # | Frage | Entscheidung | Blockadewirkung je Task |
|---|---|---|---|
| **OQ-1** | Soll dieses Repo `orchestrator.topology` **explizit** deklarieren? | **Ja, `subagent`** (D-OQ1) — löst B-5/B-6/B-11, beseitigt die derived-vs-declared-Divergenz und macht D-Q1 hier gegenstandslos (Spec §9.3) | **Keine Task blockiert.** Umsetzung ist **T20** (eine Zeile, nach T19, mit Rollback). T11 nutzt eine synthetische Config |
| **OQ-2** | Bleibt `strict × subagent` eine dokumentierte Zelle? | **Ja — erlaubt und empfohlen** (D-OQ2), keine Abwertung | **Entblockt T15/AC-6/AC-7**: die `RECOMMENDED`-Menge ist jetzt `{(v1, strict, subagent), (v2, strict, subagent), (Claude, strict, subagent), (Gemini, strict, subagent)}`; `strict × primary` bleibt `ALLOWED` |
| **OQ-3** | Namespace der neuen Check-IDs | **Bereits entschieden** durch Spec §6.2: `orchestrator-topology.` für Positionsbefunde, `orchestrator-strict.` für Gate-Befunde | **Keine Blockade** — T11–T13 setzen §6.2 um |
| OQ-4 | Wird #1182 vor der Team-Empfehlung gefixt? | **Erst nach #1182** (D-OQ3); bis dahin `strict × subagent` | Blockiert **Szenario `103`** (T17) und die Team-Empfehlung (AC-37), **kein** Task |
| OQ-5 | Kurzmatrix in `README.md`? | Ja, Kurzfassung mit **beiden** Opencode-Positionen; volle Matrix im Concept-Doc | Blockiert **nichts**; bei „nein" entfällt nur der README-Teil von T16/T18 |

**ACs, die auf OQ-Entscheidungen warten: 0.** Alle fünf Fragen sind am 2026-11-09 entschieden
(Spec §9.3, §14); AC-7/AC-11/AC-29/AC-32…AC-37 sind daraus abgeleitet. Offen bleibt allein die
externe Terminierung von #1182 (kein Entscheid dieses Vorhabens).

### Zusätzliche Plan-Klärungen (vor T1 zu bestätigen)

| # | Klärung | Warum nötig | Stand |
|---|---|---|---|
| **K-1** | `ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT := source != "derived"` statt der Rev.-1-Spec-Formel `effective != declared or source != "derived"` | Die Rev.-1-Formel ist bei `declared is None` **immer** `true` und würde in jedem Default-Consumer den `{{#if}}`-Zweig öffnen → Verstoß gegen AC-16/AC-27 | **Erledigt — in Spec Rev. 2 übernommen** (Spec §5-G2 „Formel-Korrektur"). Keine offene Bestätigung vor T8; T1 setzt die Formel direkt um |
| **K-2** | AC-1 nennt `sync --check` als Kanal, die Findings entstehen aber in `consistency/` (`scripts/consistency-check.py:264-267`) und werden über `--validate` gerendert | `sync --check` führt keine Consistency-Checks aus | **Erledigt — in Spec Rev. 2 übernommen** (AC-1 nennt `--validate`/`consistency-check`). Kein neues `--check`-Wiring |
| **K-3** | Provider-lose Basiswerte der neuen Flags (`_build_orch_variables`) | Das globale Dict ist die Basis, die jeder Provider-Seam überschreibt (`config.py:2013-2021`) | `EFFECTIVE = declared or "subagent"`, `EXPLICIT = source != "derived"`, `INERT = (mode == main-chat)`; jeder Provider-Seam (T3–T6, Stage 4) überschreibt. Die Basis ist **nicht autoritativ** (RVW2-1190-09): in diesem Repo steht dort `subagent`, obwohl die Ableitung `primary` ergibt — ein Ratchet-Test (AC-30) verhindert, dass ein Render-Seam sie liest |
| **K-4** | Einstiegshinweis in einer **geteilten** Kontextdatei | Geteilte Datei darf nicht oszillieren (`_shared_context_users`, `context.py:2246`) **und** keine positionsspezifische Falschaussage für einzelne Sharer tragen (Spec §5-G5) | **Eine** Regel (RVW2-1190-02): Entscheidung in `_position_aware_agent_hints` (`_sync_managed_block_context`, `:848-852`) — gleichpositionierte Sharer ⇒ genau dieser Text (Byte-Identität für reine `subagent`-Dateien), gemischte Sharer ⇒ neutraler Text. `build_agent_hints` bekommt nur `position`; die Rev.-1-Regel „primary-Hinweis iff ∃ Provider mit `effective == 'primary'`" bleibt **verworfen** (R-05) |

---

## 14. Branch-Guard

Umsetzung ausschließlich auf **`feat/1190-orchestrator-mode-topology`** (Basis `aaed14c2`).
Dieser Plan selbst wird auf dem **Doku-Branch** `docs/1190-orchestrator-topology` geführt
(Frontmatter `branch:`, HEAD `aaed14c2`); der Wechsel auf den Implementierungs-Branch
`feat/1190-orchestrator-mode-topology` erfolgt **vor T1** und ist der reguläre
Branch-Guard-Übergang (Doku → Code), kein Verstoß gegen die eigene Basis (Rev. 3 /
RVW2-1190-11).
Keine Commits auf `main`/`master` (`rules/1-generic/branch-guard.md`). Ein Commit pro Task,
Englisch, Conventional Commits, ≤72 Zeichen, ohne BOM; vor jedem Commit Secret-Scan; **kein**
Push/Tag/Branch-Management durch den Executor (das ist `git`-Rolle).

---

## 15. Self-Review

- Jeder Task mappt auf **eine** Rolle (`developer` für T1–T21; `documenter` optional für T16/T18-Text,
  dann als eigener Task zu splitten — aktuell bewusst beim `developer`, weil der Doc-Test die
  Assertion liefert).
- Jedes Akzeptanzkriterium ist messbar: Testname + Assertion oder Befehl + erwarteter Exit-Code.
  AC-29…AC-37 sind ergänzt und in §10 einem Task zugeordnet (AC-31…AC-37 aus Rev. 4).
- `Files:`/`Interfaces:` vollständig (21 von 21 Tasks); innerhalb einer Parallel-Gruppe überlappt
  keine Datei (T4/T5/T6 sind sequenziell, nicht parallel, weil sie denselben Helfer aus T1 nutzen;
  T17–T20 sind ebenfalls sequenziell).
- `pipeline_stages` deckt die `plan-driven`-Stage `implement` der `feature-lifecycle`-Pipeline ab
  (`config/role-defaults.yaml:2678-2688`); T1 ist der erste Implementierungsschritt.
- **Positions-Konsistenz (Rev. 4):** Szenario-IDs (`100`–`104`), Positions-IDs (`POS-1`–`POS-3`) und
  Task-IDs (T1–T21) sind je genau einmal definiert; die Reihenfolge ist `T18` (Doku) →
  `T19` (Positions-Parität) → `T17` (Szenarien) → `T20` (Deklaration) → `T21` (Abschluss).
- Keine Platzhalter im Sinne von `spec_plan_no_placeholder` (auch das Wort mit den drei
  Großbuchstaben ist im Plan nicht mehr enthalten, Rev. 3 / RVW2-1190-07); jede Code-Referenz mit
  `datei:zeile` aus dieser Runde.
  Baseline-Zahlen werden **nicht** vorab zitiert, sondern in M0 erzeugt und in §17 dokumentiert.
- Byte-Identität, beabsichtigte Änderung und Golden-Fixtures sind getrennt: AC-16/AC-27 gelten nur
  für `topology` ungesetzt ∧ `effective == "subagent"`; abgeleitetes und deklariertes `primary`
  haben je eine eigene Fixture (RVW2-1190-01).
- Re-Planning nach jedem Meilenstein (M0…M11): Annahmen prüfen, Reihenfolge bestätigen, Plan
  fortschreiben — der Plan ist nicht eingefroren.

---

## 16. Review-Auflösung (2026-11-09)

Gegenstand: `docs/reviews/2026-11-09-orchestrator-mode-topology-review.md` (Review 1, vor Revision 2).
Die Spec-Seite derselben Befunde steht in Spec §14.

| Befund-ID | Änderung im Plan | Stelle |
|---|---|---|
| RVW-1190-01 | T13 prüft `main-chat` statt `strict`; Testnamen und Erwartungen umgestellt; Verifikation „kein `[INF]` **mit dieser ID**" (Rev. 3 präzisiert, RVW2-1190-06) | T13, §10 AC-12/AC-13 |
| RVW-1190-02 | T7 pinnt nur noch die positionsbasierte Aussage; eigener Negativtest gegen „kein Spawn-Kanal"/„cannot run as a subagent" | T7, §1 Zielbild 2 |
| RVW-1190-03 | T14 auf `reconcile_opencode_surface_gate` + `_opencode_v2_gate_permissions` umgeschrieben; `sync_pipeline.py` und `cli_commands.py` in File Map, Files-Zeile und Tests | §File Structure, T14, §6.2 |
| RVW-1190-04 | T13 bleibt in `orchestrator_strict.py`; T11/T12 in `topology.py`; je ein Ablagetest; AC-21 entsprechend | T11, T12, T13, §6.3 |
| RVW-1190-05 | T5/T10: Zwei-Sharer-Test mit Assertion auf den tatsächlich gerenderten Text; K-4 neu gefasst (Rev. 3: gemischte Sharer ⇒ neutral, gleichpositionierte ⇒ Positions-Text) | T5, T10, §13 K-4 |
| RVW-1190-06 | Regenerationsschritt in T4–T10 und T14; M1/M2/M3/M5/M8 und T21 um `sync` + Diff + Commit + `--check` erweitert; AC-31 | §Global Constraints, M0–M8, T4–T10, T14, T21, AC-31 |
| RVW-1190-07 | `active_set` Pflicht-Keyword; `sync_rules`/`sync_embedded_rule_files`/`sync_context_for_provider`/`_build_provider_vars` mit Durchreichung; drei Paritätstests; AC-30 | T4, T5, T6, §6.2, AC-30 |
| RVW-1190-08 | K-1/K-2 auf „in Spec Rev. 2 übernommen" degradiert; T1/T8 ohne Bestätigungsvorbehalt | §13, T1, T8 |
| RVW-1190-09 | Kopf trägt `**Goal:**`, `**Architecture:**`, `**Tech Stack:**`, `**Spec:**` (Regex-konform), `## Global Constraints`, `## File Structure`, `pipeline_stages`; `_classify`-Folgen in der Spec | Plan-Kopf, §Global Constraints, §File Structure, Spec §13 |
| RVW-1190-10 | T14 prüft die Log-Warnung mit den §6.4-Teilstrings und schließt ein v2-Finding aus; v1-Zählregel als eigener Test | T14, §6.3, Spec §6.4 |
| RVW-1190-11 | alle `.tmp/`-Zitate entfernt; M0 erzeugt die Baseline; §17 als Ablage | Voraussetzungen 3, M0, T13, T21, §17 |
| RVW-1190-12 | T9-Signatur `_singleton_constraint_block(effective, *, inert)`; `ORCH_TOPOLOGY_INERT` dort verdrahtet; `_EFFECTIVE_SOURCE` als Audit-Flag | T9, §6.2, §6.1 |
| RVW-1190-13 | 103 heißt `blocked-103-advisory-subagent` und liegt außerhalb `10*`; M8 = 4 PASS; kein SKIP | T17, M8, „Teststrategie", AC-29 |
| RVW-1190-14 | `test_role_orchestrator_active_under_main_chat_prose` in T10; AC→Task-Zeile AC-24 ergänzt | T10, §10 AC-24 |
| RVW-1190-15 | T16-Test `test_gate_render_is_single_variant_per_file` (B-9 als Render-Widerspruch) | T16 |
| RVW-1190-16 | AC-23 im Plan auf drei Aufrufstellen + `None`-Ausnahme an `:869`; eigener Caller-Test | T14, §10 AC-23 |
| RVW-1190-17 | §8 trennt Byte-Identität (`ungesetzt ∧ effective == "subagent"`, Rev. 3 geschärft) von abgeleitetem/deklariertem `primary` (Golden-Fixture); T8/T21 haben den Golden-Test | §8, T8, T21, AC-16, AC-27 |
| RVW-1190-18 | T11 pingt die Override-Remediation aus Spec §4-D-Q1 | T11 |
| RVW-1190-19 | H-Map steht in Spec §13 (Plan verweist) | Spec §13, §1 Zielbild |
| RVW-1190-20 | 7 neue Flags; Injektionsbedingung mit `not role.endswith("-iteration")`; „Gate #5" als bewusst konserviert; „cannot run as a subagent" als `ISSUE` | T2, T9, §6.1 |
| B1 | Größen-Summe korrigiert: 9 × S, 8 × M, 1 × L (18 Tasks) | Plan-Kopf |
| B2 | AC-21↔T13-Ablage durch RVW-1190-04 konsistent | §10 AC-21, T13 |
| B3 | AC-15 im Plan auf fünf Bool-Flags + zwei String-Flags getrennt | §6.1, §10 AC-15, T2 |
| W1 | AC-1-Kanal `--validate`/`consistency-check` | §10 AC-1, T11 |
| W2 | AC-29 für T17 ergänzt | §10 AC-29, T17 |
| W3 | Spec-Anker `…-spec.md:3` | Voraussetzungen 1 |
| W4 | 94–99 als Annahme mit Quelle (Config-Welle, PR #1212) markiert; `100`+ kollisionsfrei | „Teststrategie" |
| W5 | #1209/#1006/#885 als real bestätigt (bestehende Issues, keine Erfindung) | §11 |
| W6 | Plan-Kopf trägt `Revision: 3` (Rev. 2 → Rev. 3) | Plan-Kopf |

### Re-Review 1 (vor Revision 3) — RVW2-1190-01…-13

Gegenstand: `docs/reviews/2026-11-09-orchestrator-mode-topology-rereview.md`. Die Spec-Seite
derselben Befunde steht in Spec §14.

| Befund-ID | Änderung im Plan | Stelle |
|---|---|---|
| RVW2-1190-01 (BLOCKER) | Byte-Identität nur noch `ungesetzt ∧ effective == "subagent"`; abgeleitetes `primary` als beabsichtigte Änderung mit eigener Golden-Fixture; `subagent`-Hinweis **nicht** geändert (T10 zurückgenommen) | „Global Constraints", §8, T7, T8, T10, T21, §10 AC-16/17/27 |
| RVW2-1190-02 (MAJOR) | T10: Entscheidung aus `build_agent_hints` nach `context._position_aware_agent_hints` verlegt; `position`-Parameter; gemischte Sharer ⇒ neutral, gleichpositionierte ⇒ Positions-Text; K-4 auf **eine** Regel | T10, §6.2, K-4, §10 AC-20 |
| RVW2-1190-03 (MAJOR) | T5: Context-Seam ist `_sync_stage_contexts` (Stage 4), `active_set`-Pflichtkette bis `sync_context_for_provider`, Aufrufer `cli_commands.py:1543`; Test-Aufrufer als Folgeschritt | T5, „Global Constraints", File-Map (`context.py`, `sync_pipeline.py`, `cli_commands.py`), §6.2, §10 AC-30 |
| RVW2-1190-04 (MAJOR) | T7 pinnt den qualifizierten Delegations-Weg; neuer Negativtest gegen die absolute Aussage („erfüllt dieses Gate nicht") | T7, §10 AC-3 |
| RVW2-1190-05 (MINOR) | T13: Prüfung einmal pro Lauf **vor** dem Provider-Loop (`:220-221` → `:225`), eigener Zähltest | T13, §10 AC-12 |
| RVW2-1190-06 (MINOR) | T13-Verifikation auf die Check-ID präzisiert; `no-hook-support` ausdrücklich ausgenommen; Kanal `--validate` | T13, §10 AC-12 |
| RVW2-1190-07 (MINOR) | Self-Review ohne das Literal, das `spec_plan_no_placeholder` auslöst | §15 |
| RVW2-1190-08 (MINOR) | T16 pinnt „P3, shipped" als einzige Aussage; Vorgänger-Spec-Zeile als überholt ausgewiesen (nicht editiert) | T16, §10 AC-25 |
| RVW2-1190-09 (MINOR) | T3 deklariert die provider-lose Basis als **nicht autoritativ**; Ratchet-Test in T3/AC-30 | T3, „Global Constraints", §6.2, §10 AC-30 |
| RVW2-1190-10 (NIT) | Testdateien **10**; „24 Zellen × 4 Assertions = 96" | „Teststrategie" |
| RVW2-1190-11 (NIT) | Branch-Übergang `docs/…` → `feat/…` explizit benannt | „Branch-Guard" |
| RVW2-1190-12 (NIT) | `_opencode_v2_gate_permissions` durchgängig `:1408`; `INERT` einheitlich `mode == "main-chat"` | File-Map, T14, T1, K-3, §6.1 |
| RVW2-1190-13 (MINOR) | T10-Prosa-Assertion, T14-Trefferzahlen/Monkeypatch-Zähler, T16-Datei-Scope konkretisiert | T10, T14, T16, §10 AC-23/24/25 |

### User-Entscheidungen (2026-11-09) — D-OQ1…D-OQ3

Gegenstand: die drei Nutzer-Entscheidungen zu #1190 vom 2026-11-09 (Spec §14, Block
„User-Entscheidungen"). Die Spec-Seite derselben Änderungen steht dort.

| ID | Änderung im Plan | Stelle |
|---|---|---|
| **D-OQ1** (Default dieses Repos = `strict × subagent`, beide Opencode-Positionen first-class) | Größen-/Meilenstein-Struktur auf 21 Tasks / 12 Meilensteine umgestellt; Positionsmodell-Task **T18** (Doku + Mapping), Determinismus-Test in **T19**, explizite Deklaration als **T20**, Abschluss-Gate zu **T21**; Szenario `100` ist jetzt `strict × subagent`; OQ-1 entschieden | Plan-Kopf, „Global Constraints", File Structure (`.meta-config/project.yaml`), M8–M11, T17, T18, T19, T20, T21, §8, §13 |
| **D-OQ2** (`strict × subagent` bleibt erlaubt und empfohlen; Gate-Tier je Surface; Opencode generiert je Position sauber) | Neuer Task **T19** mit drei Positions-Tests (POS-1/POS-2/POS-3) und dem Verbot kombinierter Fälle; neues Testmodul `tests/test_opencode_positions.py`; `provider_transform.py` als Prüf-/Fix-Ort in die File-Map; AC-7/AC-8 in §10 nachgeführt | File Structure, T19, §6.1, §6.4, §7, §9 (P-10), §10 |
| **D-OQ3** (`advisory × subagent` erst nach #1182) | Szenario `103` bleibt `BLOCKED (#1182)`; Bedingung in §7, §11 und §12; AC-37 plus Doku-Test `test_advisory_subagent_carries_1182_condition_everywhere` | T17, T18, §7, §11, §12, §13, §10 (AC-37), P-12 |

---

## 17. Baseline (M0)

Wird in **M0** erzeugt und hier eingetragen — vorher enthält dieser Abschnitt bewusst keine Zahlen.
Format des Eintrags (drei Zeilen, je Befehl eine):

| Befehl | Exit | Notiz |
|---|---|---|
| `python3 scripts/sync.py --check` | zu erheben in M0 | erwartet `0`; bei ≠ 0 ist die Arbeitskopie vor T1 nicht sauber |
| `python3 scripts/sync.py --validate` | zu erheben in M0 | Referenz für T13/T21 |
| `python3 -m pytest tests/ -k topology` | zu erheben in M0 | Pass/Fail-Zahlen der Topologie-Familie (19 Dateien matchen `tests/*topology*.py`) |

Zusätzlich notiert M0 den Commit-Hash der Arbeitsbasis (`aaed14c2`) und ob `git status` clean ist.
Erst nach diesem Eintrag dürfen T13/T21 „wie in §17 dokumentiert" zitieren.
