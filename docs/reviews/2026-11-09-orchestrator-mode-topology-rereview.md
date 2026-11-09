# Re-Review — Orchestrator `mode` × `topology` (#1190), Rev. 2

> Reviewer: `concept-reviewer` · Datum: 2026-11-09 · Modus: fokussiertes Re-Review (read-only)
> Gegenstand: `docs/specs/2026-11-09-orchestrator-mode-topology-design.md` (Rev. 2, 1113 Zeilen)
> und `docs/plans/2026-11-09-orchestrator-mode-topology-plan.md` (Rev. 2, 1083 Zeilen)
> Referenz: `docs/reviews/2026-11-09-orchestrator-mode-topology-review.md` (Review 1)
> Branch `docs/1190-orchestrator-topology`, HEAD `aaed14c2`
> Ergebnis: **CHANGES_REQUESTED** — 1 BLOCKER, 3 MAJOR, 6 MINOR, 3 NIT (neu), alle
> drei Rev.-1-Blocker geschlossen.
>
> **Status-Nachtrag:** Re-Review 1 (vor Revision 3) — Befunde in Rev. 3 eingearbeitet
> (Spec §14, Plan §16).

## Scope

Geprüft: Auflösung der Rev.-1-Befunde R-01…R-20 (Schwerpunkt R-01, R-02, R-03, R-04/R-10/R-12,
R-06/R-07, R-09), Konsistenz Spec↔Plan (Flags, Check-IDs, Signaturen, AC-Nummern, Task-Größen),
Traceability (31 ACs), Vakuum-Grüne Gates, leere Zellen, Scope-Abgrenzung zu #1077/#1007.

Nicht im Scope: Implementierung, Formulierung, erneute Capability-Herleitung.
Verifikationsbasis: jede tragende Stelle in dieser Runde im Repo gelesen (`datei:zeile`);
keine Testausführung (read-only Review).

---

## Auflösung der Rev.-1-Befunde

| Befund | Status | Beleg |
|---|---|---|
| **R-01** D-Q5 falsche Prämisse | **GESCHLOSSEN** | Bedingung jetzt `mode == "main-chat"` ∧ Key-**Präsenz** (Spec §4-D-Q5 Z. 348-350, §6.2 Z. 619, AC-12 Z. 764-768, AC-13 Z. 769-773). Prämisse korrigiert: `DIRECT_DISPATCH_SECTION` wird modusunabhängig gebaut (`config.py:2090-2101`), gerendert über `agents/1-generic/orchestrator.md:203-205`. Dieses Repo ist `mode: strict`, Key gesetzt (`.meta-config/project.yaml:311,321`) ⇒ **kein** neues Finding. INFO-Text enthält Entfernungs-Rat nur für den Fall „main-chat beabsichtigt" (dort ist der Key tatsächlich verbraucherlos) und nennt für den anderen Fall den wirksamen Weg (Z. 353-359). |
| **R-02** „kein Spawn-Kanal" provider-agnostisch falsch | **GESCHLOSSEN (Kern) / TEILWEISE (Resttext)** | Aussage ersatzlos gestrichen und ausdrücklich als bewusst nicht aufgenommen markiert (§5-G1 Z. 405-411); AC-3 pinnt sie nicht mehr und fordert einen Negativtest gegen Provider-Namen/Spawnbarkeits-Behauptung (Z. 721-723); §6.5-Caveat (Z. 672-676) und §12.4-Caveat (Z. 1001-1005) benennen Claude korrekt (`main_agent_selectable: true`, `provider-capabilities.yaml:144`; `topology_support.primary: true`, `:148`). **Rest:** der Ersatztext enthält weiter eine provider-agnostische Entweder-oder-Aussage → RVW2-1190-04. |
| **R-03** T14 adressiert falsche Funktion | **GESCHLOSSEN** | T14 zielt jetzt auf `reconcile_opencode_surface_gate` (`isolation.py:1751-1761`) und `_opencode_v2_gate_permissions` (`:1408-1463`); `topology=None` als Durchreich-Parameter; Durchreichung an `:1827` und `:1840-1843`, dort weiter an `:1457`. Aufrufer `sync_pipeline.py:1598-1602` und `cli_commands.py:344-348` in File-Map, T14-Files und AC-23. `_sync_opencode_runtime_gate` (`:725`) ist korrekt als **bereits** topology-durchgereicht abgegrenzt (`:846-856`, `:866-872`). |
| **R-04** Ablage der Checks widersprüchlich | **GESCHLOSSEN** | §5-G6 (Z. 526-535), §6.2 mit Ort-Spalte (Z. 615-621), AC-21 (Z. 812-817), Plan T11/T12 (`topology.py`) vs. T13 (`orchestrator_strict.py`), Plan §6.3 (Z. 803-804) — deckungsgleich. |
| **R-10** v1/v2-Kanäle unscharf | **GESCHLOSSEN** | §6.4 Kanal-Tabelle + Zählregel (Z. 649-661): v2 = genau eine Sync-Log-Warnung, kein Finding (`_gate_wanted` Tier-`permission`-gebunden, `consistency/topology.py:103-105`); v1 = Log **und** Finding, je Kanal eine. AC-22 (Z. 818-826) und T14-Tests übernehmen die Regel. |
| **R-12** Inert-Variante / tote Flags | **GESCHLOSSEN** | Signatur `_singleton_constraint_block(effective: str, *, inert: bool)` in §5-G4 (Z. 474-484), §6.2 (Z. 787), T9 (Z. 449-466); `ORCH_TOPOLOGY_INERT` dort verdrahtet, in AC-15 als eines der fünf Bool-Flags registrierungspflichtig; `_EFFECTIVE_SOURCE` als Audit-Flag deklariert (§6.3 Z. 636-640). Nur Definitions-Nuance → RVW2-1190-12. |
| **R-06** `--check`-Gates nicht erfüllbar | **GESCHLOSSEN** | Regeneration ist Task-Schritt (§Global Constraints Z. 101-104, T4-T10/T14 „Verifikation", M1/M2/M3/M5/M8), AC-31 (Z. 867-870), T18-Gate erst danach. |
| **R-07** Render-Seams ohne per-Sync-`ActiveSet` | **TEILWEISE** | `_provider_topology_flags` mit `active_set` als **Pflicht-Keyword** (§5-G2 Z. 446-453, §6.2 Z. 780, T4/T5/T6), AC-30 (Z. 862-866). **Aber:** der Context-Seam liegt in `_sync_stage_contexts` (`sync_pipeline.py:732-737`), nicht in `_sync_stage_per_provider`; die Funktion hat keinen `active_set`-Parameter, ihr Aufrufer `cli_commands.py:1543` fehlt in der File-Map → RVW2-1190-03. |
| **R-09** Pflichtsektionen / Approval-Gate | **GESCHLOSSEN** | Plan-Kopf enthält `pipeline_stages` (Z. 2), `**Spec:**` (Z. 29), `**Goal:**` (Z. 31), `**Architecture:**` (Z. 38), `**Tech Stack:**` (Z. 46), `## Global Constraints` (Z. 86), `## File Structure` (Z. 133) — alle `REQUIRED_PLAN_SECTIONS` (`spec_plan.py:36-39`) als Substring vorhanden. `**Spec:**` matcht `_SPEC_FIELD_RE` (`:79-81`), damit greift `_check_approval_markers` (`:479-507`) und meldet den **beabsichtigten** DRAFT-ERROR. `_classify`-Folgen (Spec wird als `plan` geprüft, `specs` bleibt leer) sind in Spec §13 (Z. 1059-1069) korrekt dokumentiert. Rest: selbstreferenzieller `TBD`-Treffer → RVW2-1190-07. |

**Zusatzprüfung R-09:** Task-Größensumme stimmt (9×S + 8×M + 1×L = 18; Plan Z. 62-63).
AC-Traceability vollständig (AC-1…AC-31; Plan §10 „alle 31"). Keine leeren Zellen in
§12.2-§12.5, §6.2, §6.4 oder Plan §10.

---

## Neue Befunde

### RVW2-1190-01 · Dimension: Logik / Konsistenz — **BLOCKER** — Byte-Identität und die beabsichtigten Render-Fixes schließen sich aus

**Spec AC-16 (§8 Z. 789-791), AC-17 (Z. 792-795), §5-G5 (Z. 499-503), AC-27 (Z. 848-852);
Plan §8 (Z. 867-869), T10 (Z. 485-487), T18 (Z. 741-744).**

AC-16 und AC-27 verlangen: **ungesetzter `topology`-Key ⇒ Ausgabe byte-identisch zu heute**
(„Invariante, nicht Ergebnis", Plan Global Constraints Z. 88-92). AC-17 verlangt für
**abgeleitetes** `primary` (per Definition: Key ungesetzt), dass `orchestrator.md` den Satz
„Only `main_chat` may create you" **nicht** mehr enthält. Beides kann nicht gleichzeitig gelten:

- Der heutige Render für abgeleitetes `primary` ist der else-Zweig
  (`agents/1-generic/orchestrator.md:19`, `ORCH_TOPOLOGY_EXPLICIT == "false"`,
  `variables.py:349-355`; Spec §3.2 Z. 117 belegt das selbst) — er **enthält** genau diesen Satz.
- Dieses Repo ist der Fall: kein `topology`-Key, abgeleitetes `primary`
  (`.meta-config/project.yaml:308-323`, `scripts/lib/topology.py:135-140`).
- T7 sagt das offen: „dieses Repo ist `strict` + `effective=primary` ⇒ der Gate-Text ändert sich
  hier **beabsichtigt**" (Z. 407-409). T18s `test_unset_topology_render_is_byte_identical`
  („für alle aktiven Provider **ohne** `topology`-Key", Z. 741-742) kann damit nicht grün werden.

Zweite, unabhängige Verletzung derselben Invariante: §5-G5 ändert den `subagent`-Hinweis von
heute „Starte mit dem `orchestrator`-Agenten …" (`scripts/lib/agents.py:174`) auf
„Delegiere jede Entwicklungsaufgabe an den `orchestrator`-Subagenten" (Z. 502), und T10 pinnt
diesen neuen Text (Z. 485-487). Plan §8 behauptet dagegen „gleicher Hinweis für
rein-subagent-Projekte" (Z. 869) — Plan-interner Widerspruch.

**Korrektur:** Byte-Identität auf `ungesetzt ∧ effective == "subagent"` schärfen und
abgeleitetes `primary` ausdrücklich als beabsichtigte Änderung mit eigener Golden-Fixture führen
(T18-Test entsprechend umbenennen/teilen). Zusätzlich entscheiden: entweder den heutigen
`subagent`-Hinweis beibehalten (dann G5-Tabelle/T10-Test korrigieren) oder die Hinweis-Änderung
als beabsichtigt deklarieren und aus der Identitätszusage herausnehmen.

### RVW2-1190-02 · Dimension: Ausführbarkeit — **MAJOR** — T10 kann die Shared-vs-eigene-Datei-Entscheidung in `build_agent_hints` nicht treffen

**Spec §5-G5 (Z. 505-522), AC-20 (Z. 804-811); Plan T10 (Z. 473-508), §6.2 (Z. 788), K-4 (Z. 1001).**

T10 verlangt: „Ist die Zieldatei **geteilt** (`_shared_context_users`, `:2445-2455`), rendert
**immer** der neutrale Text; nur in provider-eigenen Dateien gilt ‚primary-Hinweis iff ∃ Provider
mit `effective == "primary"`". Die Funktion hat diese Information nicht:

- `build_agent_hints(config, agent_meta_root, include_table, *, template_roles, warn_sink,
  active_set)` kennt weder Provider noch Zieldatei (`scripts/lib/agents.py:132-140`).
- Sie wird **provider-los** in den globalen Variablen-Bau aufgerufen
  (`config.py:1686-1688`, `:1950-1953`) und liefert dort **einen** String
  `AGENT_HINTS`/`AGENT_HINTS_CLAUDE`.
- Die Shared-Entscheidung lebt in `_build_managed_block` (`context.py:2445-2464`), nicht in
  `agents.py`; der Plan fügt weder `provider` noch `target_context_file`/`is_shared` als
  Parameter hinzu (§6.2-Signatur ist als verbindlich deklariert).

Folgen: (a) In einem gemischten Repo (dieses Repo: Opencode `primary`, Gemini `subagent`) kann
AC-20s provider-eigene Erwartung nicht gleichzeitig mit dem neutralen Text für `AGENTS.md`
erfüllt werden — ein globaler String kann nicht zwei Ziele bedienen. (b) Die in T10
wiedereingeführte ∃-Regel ist exakt die in K-4 „verworfen (R-05)" markierte Rev.-1-Regel; sie
würde z. B. `CLAUDE.md` (eigene Datei, Claude leitet `subagent` ab) den Satz „Diese Session
startet im `orchestrator`-Agenten" rendern lassen, weil ein *anderer* Provider `primary` ist —
dieselbe Falschaussage, nur in eine provider-eigene Datei verschoben.

**Korrektur:** Entscheidung an die Stelle verlagern, die das Ziel kennt
(`_build_managed_block`/`sync_context_for_provider` mit `provider` + `target_path`), und
`build_agent_hints` entweder mit explizitem `position`-Parameter (pro Aufruf gesetzt) oder als
rein neutralen Text definieren. K-4 und T10 auf **eine** Regel bringen (∃-Regel streichen),
AC-20 entsprechend präzisieren.

### RVW2-1190-03 · Dimension: Ausführbarkeit / Konsistenz — **MAJOR** — Context-Seam ist der falschen Pipeline-Funktion zugeordnet

**Spec §5-G2 (Z. 446-453), Plan Global Constraints (Z. 95-100), T5 (Z. 330-353), File-Map
`sync_pipeline.py` (Z. 144).**

Die Spec sagt, der per-Sync-`ActiveSet` werde „aus `sync_pipeline._sync_stage_per_provider`
(`:1335-1446`) an alle vier Seams" durchgereicht. Für den Context-Seam ist das falsch:

- `sync_context_for_provider` wird aus `_sync_stage_contexts` aufgerufen
  (`sync_pipeline.py:732-737`, Aufruf `:788-790`) — Stage 4, **vor** Stage 6.
- `_sync_stage_contexts` hat **keinen** `active_set`-Parameter; sein Aufrufer ist
  `cli_commands.py:1543`, der `ctx.active_set` (`:964`) bereits besitzt.
- T5 nennt nur `sync_pipeline.py:788-790`, nicht die nötige Signaturerweiterung von
  `_sync_stage_contexts` und nicht `cli_commands.py:1543`; die File-Map führt `sync_pipeline.py`
  nur für T6/T14.
- Zusätzlich: `sync_context_for_provider` hat zahlreiche Test-Aufrufer (u. a.
  `tests/test_context_*`, `test_agents_md_shared_context_convergence.py`), die bei einem
  **Pflicht**-Keyword mitgezogen werden müssen — kein Task nennt das.

**Korrektur:** §5-G2/Global Constraints auf „`_sync_stage_contexts` (Stage 4) erhält `active_set`
von `cli_commands.py:1543` (`ctx.active_set`)" umstellen; T5- und File-Map-Zeilen ergänzen;
Default-`None` ausdrücklich ausschließen (sonst AC-30-Verstoß) und die Test-Aufrufer als
Folgeschritt führen.

### RVW2-1190-04 · Dimension: Logik / Konsistenz — **MAJOR** — der neue G1-Text bleibt für Claude `primary` falsch

**Spec §5-G1 (Z. 387-395), AC-3 (Z. 716-723), §6.5 (Z. 672-676), §12.4 (Z. 995, 1001-1005).**

Der gepinnte `primary`-Text lautet: „Eine Session, die im Main Chat läuft, erfüllt dieses Gate
nicht: sie darf nicht selbst editieren und muss entweder im `orchestrator` starten, oder der
Nutzer schaltet `orchestrator.mode: main-chat`." Diese Entweder-oder-Liste ist erschöpfend
formuliert und damit provider-agnostisch falsch:

- §12.4 führt `strict × primary` auf Claude als **ALLOWED** (Hop 0 nur bei Start im
  Orchestrator) und stellt im Caveat fest, dass eine Main-Chat-Session den Orchestrator
  **spawnen darf** (`main_agent_selectable: true`, `hook`-Tier, 1 Hop).
- Ein Claude-`primary`-Projekt mit Main-Chat-Session, die an den Orchestrator delegiert,
  erfüllt das Gate („ALLES -> orchestrator") — der Text sagt aber, sie erfülle es nicht.

Das ist die verbliebene Hälfte von RVW-1190-02: die falsche Behauptung ist weg, die
unvollständige Handlungsanweisung ist an ihre Stelle getreten und wird über AC-3 für **jede**
effektive `primary`-Position gepinnt.

**Korrektur:** Entweder den zweiten Satz capability-/positionsbasiert öffnen („… oder delegiere
aus dem Main Chat an den `orchestrator`, wo der Provider das unterstützt") oder auf den Fall
begrenzen, in dem die `primary`-Rolle mit `mode: primary` emittiert wird; AC-3 um den
Claude-Fall als Negativ-Assertion ergänzen.

### RVW2-1190-05 · Dimension: Ausführbarkeit — **MINOR** — T13-Ablage ist hinter dem Strict-Gate und erzeugt ein INFO pro Provider

**Plan T13 (Z. 583-590), AC-12 (Z. 764-768); Code `consistency/orchestrator_strict.py:182-259`.**

Die Anweisung „Prüfung in `check_orchestrator_strict_hook_support` **vor** der Tier-Auflösung"
ist zu unpräzise:

- Die Tier-Auflösung steht in Z. 231, das `continue` für nicht-effektiv-strict davor in
  Z. 227-228. `_resolve_effective_strict` liefert für `mode: main-chat` **False** (`:141`) —
  eine Prüfung „vor der Tier-Auflösung", aber innerhalb des Loops, feuert also **nie** im
  einzigen Zielmodus.
- Wird sie vor das Strict-Gate gezogen, liegt sie im `for provider in active_providers`-Loop
  (`:226`) und erzeugt **ein Finding pro Provider**; die Funktion hat kein `_append_once`
  (das existiert nur in `consistency/topology.py:164-183`), und der Text nennt keinen Provider.
  AC-12 fordert aber „genau ein INFO" (nicht „pro Provider und Lauf").

**Korrektur:** Prüfung **einmal pro Lauf vor dem Provider-Loop** platzieren (Modus + Präsenz sind
provider-unabhängig) und in T13/AC-12 „einmal pro Lauf" festschreiben; alternativ Provider in den
Text aufnehmen und die Zählregel angleichen.

### RVW2-1190-06 · Dimension: Prüfbarkeit — **MINOR** — „kein `[INF]`" ist auf diesem Repo wörtlich falsch; Kanal-Angabe zu weit

**Spec §4-D-Q5 Konsequenzen (Z. 369-371), AC-12 (Z. 767-768).**

Dieses Repo emittiert bereits ein INFO: `check_orchestrator_strict_hook_support` meldet für
Opencode (Tier `permission`, `surface-version: v1`, `config/ai-providers.yaml:260`) unter
`strict` den bestehenden INFO `orchestrator-strict.no-hook-support`
(`consistency/orchestrator_strict.py:234-245`). AC-12s Formulierung „entsteht **kein** `[INF]`"
ist damit als Test-Assertion nicht erfüllbar; korrekt ist „kein `[INF]` mit der ID
`orchestrator-strict.direct-dispatch-inert`" (so präzise nur T13, Z. 588-589).

Zusätzlich: §4-D-Q5 sagt „ein INFO in `--validate` und `consistency-check`". Der Check wird aber
ausschließlich aus `_handle_validate` gerufen (`cli_commands.py:1457-1464`); der
Consistency-Check-Runner (`scripts/consistency-check.py`) ruft
`check_orchestrator_strict_hook_support` nicht auf. Es ist also ein **`--validate`-only**-Kanal.

**Korrektur:** AC-12 und §4-D-Q5 auf die Check-ID präzisieren und den Kanal auf `--validate`
einschränken.

### RVW2-1190-07 · Dimension: Prüfbarkeit — **MINOR** — der Plan blockiert `--validate-spec-plan` durch einen selbstreferenziellen `TBD`-Treffer

**Plan §15 (Z. 1025); Code `consistency/spec_plan.py:88-97`, `:366-384`.**

Die Zeile „Keine Platzhalter, kein `TBD`; …" enthält das Literal `TBD`. `_check_placeholders`
prüft **jeden** Workflow-Artefakttext mit `\bTBD\b` und meldet `Severity.ERROR`
(`spec_plan_no_placeholder`) — unabhängig von `spec-plan-required`. Der Plan kann damit auch
nach `Status: APPROVED` nie einen sauberen `--validate-spec-plan`-Lauf erreichen.

**Korrektur:** Formulierung ohne das Literal („keine Platzhalter"), oder den Checker um
Backtick-/Code-Span-Ausnahmen erweitern (dann eigener Task).

### RVW2-1190-08 · Dimension: Konsistenz — **MINOR** — P3-Status wird in der Spec zweifach gegensätzlich aufgelöst

**Spec §5-G9 (Z. 594-599), §9.1 B-7 (Z. 886); Plan T16 (Z. 687-689); Vorgänger-Spec
`docs/specs/2026-11-04-orchestrator-topology-spec.md:791-792`.**

§5-G9 sagt, der Widerspruch werde „zugunsten der Vorgänger-Spec (`:791-792`) aufgelöst". Die
Vorgänger-Spec markiert P3 dort ausdrücklich als **„P3, designed, not shipped"**. §9.1 B-7 und
T16 (`test_p3_status_is_single_valued`) legen dagegen „**shipped**" fest. Damit pinnt T16 eine
Statusaussage, die der normativ bleibenden Vorgänger-Spec widerspricht.

**Korrektur:** Status einmalig entscheiden; bei „shipped" die Vorgänger-Spec-Zeile als überholt
markieren (ohne D1–D10 neu aufzurollen), bei „designed, not shipped" §9.1 B-7 und T16 korrigieren.

### RVW2-1190-09 · Dimension: Konsistenz / Logik — **MINOR** — K-3 umgeht den „Ein Resolver"-Constraint und liefert für abgeleitetes `primary` global `subagent`

**Spec §5-G2 (Z. 424-427), Plan Global Constraints (Z. 93-94), T3 (Z. 277-299), K-3 (Z. 1000);
Code `config.py:2013-2027`, `topology.py:135-140`.**

T3 baut die provider-lose Basis aus einer **synthetischen** `TopologyResolution`
(`effective = declared or "subagent"`, `source = project|derived`). Das ist kein
`resolve_topology`-Aufruf und widerspricht dem Global Constraint „Ein Resolver. Ausschließlich
`resolve_topology` … Kein vierter Resolver". Konkret: In diesem Repo (kein Key, abgeleitetes
`primary`) steht im globalen Dict `ORCH_TOPOLOGY_EFFECTIVE = "subagent"`, obwohl die Ableitung
`primary` ergibt; jeder Renderpfad, der das globale Dict ohne Provider-Override konsumiert,
bekäme die falsche Position — genau die H1-Klasse. Kein AC deckt diesen Konsumenten ab.

**Korrektur:** Entweder die Basis über `resolve_topology` je Provider bilden (dann kein
provider-loses Flag) oder in der Spec explizit festhalten, dass die globalen Effektiv-Flags
**nicht autoritativ** sind, plus Test „kein Render-Seam konsumiert die provider-lose Basis"
(z. B. Grep/Ratchet auf `ORCH_TOPOLOGY_EFFECTIVE_*` außerhalb der Provider-Vars).

### RVW2-1190-10 · Dimension: Konsistenz — **NIT** — Zahlen in Plan §7

**Plan §7 (Z. 833-842).** „Neue Testdateien (8)" listet zehn (acht plus zwei), die Datei-Tabelle
führt ebenfalls zehn. „24 Zellen (4 Surfaces × 6 Kombinationen) × 4 Surfaces … = 96" zählt die
Surfaces doppelt; korrekt ist 24 Zellen × 4 Assertions = 96.

### RVW2-1190-11 · Dimension: Konsistenz — **NIT** — Branch-Angabe widersprüchlich

**Plan Frontmatter (Z. 8) `branch: docs/1190-orchestrator-topology` vs. §14 (Z. 1007)
`feat/1190-orchestrator-mode-topology`.** Kein Fehler, aber der Übergang (Doku-Branch →
Implementierungs-Branch) sollte explizit benannt sein, sonst liest §14 wie ein Verstoß gegen die
eigene Basis.

### RVW2-1190-12 · Dimension: Konsistenz — **NIT** — Zeilen-/Definitions-Drift

- Spec §14 RVW-1190-03 nennt `_opencode_v2_gate_permissions` „(`:1420`)"; die Funktion beginnt
  bei `:1408` (der Entry-Aufruf liegt `:1457`). §3.5 nennt korrekt `:1408`.
- `ORCH_TOPOLOGY_INERT` ist in §5-G2 (Z. 428) als „`mode == "main-chat"` **und** eine
  Positionsaussage existiert (declared oder derived)" definiert, in §6.3 (Z. 631/640), T1
  (Z. 245) und K-3 dagegen nur als `mode == "main-chat"`. Da `effective` nie leer ist, ist die
  Zusatzbedingung derzeit wirkungslos — entweder streichen oder in T1 abbilden.

### RVW2-1190-13 · Dimension: Prüfbarkeit — **MINOR** — mehrere neue Tests sind unterschrieben (vakuum-anfällig)

- AC-24 nennt `test_role_orchestrator_active_under_main_chat_prose`, aber keine Assertion
  („wird korrekt gerendert", T10 Z. 494-495) — ohne konkreten erwarteten String nicht prüfbar.
- AC-23s `test_all_three_entry_point_calls_pass_topology` / `test_both_reconcile_callers_pass_topology`
  sind „AST/Grep"-Tests ohne definierte Negativbedingung; ein Grep, der die Aufrufe nicht findet,
  ist grün. Ein Fixture-basierter Nachweis (Monkeypatch-Zähler) wäre belastbar.
- AC-25s Doku-Test („absolute Aussage außerhalb eines topologie-qualifizierten Kontexts") nennt
  keinen Datei-Scope und keine Ausnahmeliste — entweder false positive auf der eigenen Spec
  (§12.4 enthält „der Main Chat **kann** spawnen") oder vakuum-grün.

**Korrektur:** je Test den erwarteten String bzw. die Zählmethode pinnen; bei Grep-Tests
mindestens eine Trefferzahl-Assertion ergänzen.

---

## Positiv (was trägt)

- **Alle drei Rev.-1-Blocker sind sachlich geschlossen** (R-01, R-02-Kern, R-03), jeweils mit
  korrigierter Code-Basis.
- R-04/R-10/R-12 sind vollständig und widerspruchsfrei umgesetzt (Ablage, Kanäle, Zählregel,
  Inert-Signatur).
- R-06 ist als Prozessschritt gelöst (Regeneration + Diff + Commit je Task, AC-31) — nicht nur
  als Doku-Hinweis.
- R-09: der Plan ist jetzt regex-konform; der Approval-Gate ist wieder scharf (der DRAFT-ERROR ist
  beabsichtigt und in §13 dokumentiert).
- Scope-Disziplin hält: `topology`-Enum, `hybrid`-Degradierung, Multi-Instanz-Achse und die
  Capability-Zellen bleiben unverändert (#1077/#1007 werden nicht neu aufgerollt; Spec §7,
  §10; Capability-Datei unberührt).
- AC-Traceability ist vollständig (31 ACs, alle einem Task zugeordnet); Task-Größensumme stimmt;
  keine leeren Zellen.

---

## Verdikt

**CHANGES_REQUESTED.**

Die drei Rev.-1-Blocker sind eingearbeitet und belegt geschlossen; die Rev.-2-Arbeit ist
substanziell. Zwei neue Punkte blockieren die Freigabe:

1. **RVW2-1190-01 (BLOCKER):** AC-16/AC-27 („ohne Key byte-identisch") und AC-17/§5-G5
   (abgeleitetes `primary` und `subagent`-Hinweis ändern sich) sind logisch unvereinbar; T18s
   Golden-Test kann mit T7/T8/T10 nicht gleichzeitig grün werden.
2. **RVW2-1190-02 (MAJOR):** T10/AC-20 verlangen eine ziel-/providerabhängige Entscheidung in
   einer Funktion, die weder Provider noch Zieldatei kennt (`build_agent_hints`), und
   reintroduzieren die in K-4 verworfene ∃-Regel.

Dazu kommen zwei MAJOR mit klarer Lokalisierung (Context-Seam in `_sync_stage_contexts` statt
`_sync_stage_per_provider`; G1-Resttext für Claude `primary`) sowie sechs MINOR/NIT, die in
derselben Überarbeitung mitlaufen können. Nach Korrektur von RVW2-1190-01…-04 ist das Paar
approvbar.

**Governance:** `# CRITICAL GATE` bleibt als Heading erhalten (T7-Test), der Tier-Absatz bleibt in
beiden Gate-Varianten, `main-chat` und `topology: subagent` werden nicht regressiv verändert, der
Provider-Agnostik-Constraint ist eingehalten (keine Provider-Namen in Bedingungen), und die
Severity-Disziplin (WARNING/INFO, rc 0) ist durchgängig.
