---
pipeline_stages:
  implement: 3
---

# Dynamic Routing + Template Slimming — Implementation Plan

> Status: geplant
> Trace-Anker: `spec-id: SPEC-dynamic-routing-template-slimming`

**Goal:** Block A — Routing-Ziele deterministisch aus `config/role-defaults.yaml` ableiten (Single Source `activation_groups`, ein kanonischer Aktiv-Resolver, explizite `addressability`, `name_index` im nicht-callable Fallback). Block B — wiederkehrende Template-Blöcke über den bestehenden `*_BLOCK`-Inlining-Mechanismus zentralisieren und die 21-fach inline duplizierte Anti-Recursion-Prosa entfernen — ohne Semantikverlust und ohne den Route-Guard zu unterlaufen.
**Architecture:** `config/role-defaults.yaml` bleibt einzige Routing-Quelle. Neuer Top-Level-Block `activation_groups` liefert die Default-Tabelle; `scripts/lib/roles.py` erhält den kanonischen Resolver (`resolve_activation_gates`, `is_role_enabled`, `resolve_active_roles`, `resolve_template_roles`). `delegation_table` und `agents` bauen Routing-Ziele, `name_index`, Hints und Tabelle aus derselben Layer-2-Menge; Abweichungen laufen in einen `warn_sink`. Block B nutzt ausschließlich benannte `*_BLOCK`-Variablen + Snippet-Dateien + `_build_snippet_variables`.
**Tech Stack:** Python 3 (Stdlib only, `from __future__ import annotations`), PyYAML, pytest, Markdown/YAML, `scripts/sync.py`.
**Spec:** docs/specs/2026-09-19-dynamic-routing-template-slimming.md

> **Spec-ID:** SPEC-dynamic-routing-template-slimming (Status APPROVED, Revision 4).
> **Branch:** `feat/dynamic-routing-template-slimming` (fortsetzen).
> **Max parallel agents:** 4.

## Decisions

| ID | Entscheidung (User-bestätigt) | Auswirkung im Plan |
|---|---|---|
| O-A | Snippet-Ablageort = `snippets/agents/` | Task 10 legt die drei neuen Block-Snippets dort ab. |
| O-B | `developer_tiers`-Gate `mode: all` beibehalten | Task 4 schreibt `config_predicate.roles_membership.mode: all` (junior+senior); kein Behavior-Change gegenüber `config.py`. |
| O-C | `name_only` bleibt im `target_agents`-Enum | Task 5 lässt `name_only`-Rollen im Enum und ergänzt sie im `name_index`. |
| O-D | Block-Snippet-Frontmatter = strippen (einheitlicher Loader) | Task 10 implementiert den Inlining-Transform inkl. Frontmatter-Strip, `\n`-Normalisierung, `strip("\n")`. |
| O-E | Golden-Baseline = committed Golden-Files | Task 11 legt `tests/fixtures/slimming-golden/` committed ab. |

> Die Spec sieht keine ADR-Ablage vor; die Entscheidungen bleiben ausschließlich in diesem Plan-Abschnitt.

## Global Constraints

- **Datei-Ownership:** Jede Datei wird in genau **einer** Task angelegt oder geändert. Disjunkte Write-Sets für parallele Tasks; `parallel_group`-Angabe je Task. Keine Zyklen.
- **Nur eigene Task-Dateien committen:** Commits erfolgen ausschließlich über den `git`-Agenten mit expliziten Pfadangaben (`git add <exakte Pfade>`). Verboten: `git add -A`, `git add .`, `git commit -a`. Der Working Tree ist mit fremden, nicht zu diesem Vorhaben gehörenden Änderungen dirty (Vorbestand); fremde Änderungen dürfen **niemals** mitcommittet werden (Gate: Task 1).
- **Conventional Commits (Englisch), max. 72 Zeichen erste Zeile, Imperativ.** Commit-/Push-Mutationen nur via `git`-Agent.
- **Spec-Gate:** Block B startet erst nach der Golden-Baseline (Task 11). Jede Migration (Tasks 12–15) läuft gegen das Äquivalenz-Gate.
- **Provider-Agnostik:** Keine `if provider == "Name"`-Logik; Format-/Fähigkeitsunterschiede ausschließlich über Capability-Keys (`config/provider-capabilities.yaml`). `route_intent_tool` bleibt unverändert `false` (A7); keine Capability-Keys ändern.
- **Route-Guard:** Routing lebt ausschließlich in `config/role-defaults.yaml`. Templates, Rules und Snippets enthalten keine `T-*`-Konstrukte; die Detektor-Logik wird nicht abgeschwächt, nur der Scope um `snippets/**/*.md` erweitert (A6).
- **Keine neuen Abhängigkeiten:** Stdlib only; keine neuen Python-Dependencies.
- **Kein Worktree:** Agenten arbeiten direkt im Projektverzeichnis (keine `isolation: "worktree"`).
- **Repo-Containment:** Schreibzugriffe nur unterhalb der Projekt-Wurzel (Ausnahme `.tmp/`).
- **Keine Rollen-/Prompt-Neufassung:** Slimming ist Deduplikation, keine inhaltliche Neufassung. Pflichtsätze (Input-Parsing, Output-Guard, Handoff-Format, Anti-Recursion) bleiben erhalten.
- **Keine No-Placeholder-Marker** in Code, Tests, Commits oder diesem Plan (keine offenen Aufgaben-/Unbestimmt-Marker, keine leeren Interfaces).

## File Structure

### Neue Dateien

- Create: `snippets/agents/background-process-guard.md` — kanonischer Block für `{{BACKGROUND_PROCESS_GUARD_BLOCK}}` (49 Vorkommen).
- Create: `snippets/agents/output-guard.md` — kanonischer Block für `{{OUTPUT_GUARD_BLOCK}}` (51 Vorkommen).
- Create: `snippets/agents/parse-input.md` — kanonischer Block für `{{PARSE_INPUT_BLOCK}}` (47 Vorkommen).
- Create: `tests/test_role_activation_resolver.py` — Unit-Tests des Aktiv-Resolvers.
- Create: `tests/test_role_activation_schema.py` — Schema-/Determinismus-Test des `activation_groups`-Blocks.
- Create: `tests/test_role_addressability_coverage.py` — Adressierbarkeits-Coverage (81/2/1) und `keyword`-Patterns.
- Create: `tests/test_routing_overlap.py` — Keyword-/Example-Overlap-Erkennung zwischen Rollen.
- Create: `tests/test_unified_active_set.py` — Routing-Ziele == Layer 2 == Hints/Tabelle; `warn_sink` statt stillem Drop.
- Create: `tests/test_active_role_call_sites.py` — Layer-2-Aufrufer ohne explizite Template-Rollen (lazy Auflösung, kein ValueError).
- Create: `tests/test_routing_name_index.py` — `name_index` vollständig, sortiert, idempotent.
- Create: `tests/test_developer_tiers_gate.py` — `principal-developer` bei aktiver/inaktiver `developer_tiers`-Gruppe.
- Create: `tests/test_validator_gate.py` — `validator`-Gate nur über `config` (nicht über `variables`).
- Create: `tests/test_orchestrator_name_dispatch.py` — Fallback-Prompt nennt `name_index`; Payload enthält `name_only`-Einträge.
- Create: `tests/test_route_guard_snippets.py` — Snippets im neuen Guard-Scope ohne Routen-Konstrukte.
- Create: `tests/test_snippet_inlining_transform.py` — Frontmatter-Strip/Whitespace/Normalisierung deterministisch.
- Create: `tests/test_warn_sink_wiring.py` — `warn_sink`-Injektion über die Variablen-Builder.
- Create: `tests/test_template_slimming_equivalence.py` — B2a/B2b-Äquivalenz gegen die Golden-Baseline.
- Create: `tests/test_snippet_copy_contract.py` — `*_SNIPPETS_PATH`-Kopiervertrag (B3).
- Create: `tests/fixtures/slimming-golden/README.md` + `tests/fixtures/slimming-golden/<role>.md` — committed Golden-Baseline (nach Block A, vor Block B).
- Create: `docs/plans/2026-09-19-dynamic-routing-template-slimming-worktree-preflight.md` — Dirty-Tree-Inventar.
- Create: `docs/plans/2026-09-19-dynamic-routing-template-slimming-snippet-preflight.md` — RVW-20-Pre-Flight-Audit.
- Create: `docs/plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md` — B2b-Diff-Manifest der normalisierten Near-Duplikate.
- Create: `docs/plans/2026-09-19-dynamic-routing-template-slimming-verification.md` — Abschluss-Verifikationsreport.

### Geänderte Dateien

- Modify: `scripts/lib/roles.py` — Resolver-Fundament + `activation_groups`-Loader.
- Modify: `config/role-defaults.yaml` — `activation_groups`, `routing.addressability`, `name_only_reason`, `openscad-developer`-Patterns.
- Modify: `scripts/lib/delegation_table.py` — Layer-2-Menge, `warn_sink`, `name_index`.
- Modify: `scripts/lib/agents.py` — Hints/Tabelle auf Layer 2, `name_index`-Durchreichung, `warn_sink`.
- Modify: `scripts/lib/config.py` — Block-A-Verdrahtung + Block-Snippet-Loader + `warn_sink`-Injektion.
- Modify: `scripts/lib/agent_sync.py` — Rollen-Gate-Aufruf auf den Resolver migrieren.
- Modify: `scripts/lib/frontmatter.py` — `_is_role_enabled` als 3-Parameter-Re-Export.
- Modify: `agents/1-generic/orchestrator.md` — Fallback-Contract für `name_index`.
- Modify: 14 × `agents/1-generic/se-*.md`, 7 × `agents/1-generic/knowledge-*.md`, 52 × übrige `agents/1-generic/*.md`, 4 × `agents/2-platform/*.md` — Inline-Blöcke durch `{{*_BLOCK}}`-Referenzen ersetzen.
- Modify: `snippets/orchestrator/se-mode.md`, `snippets/orchestrator/a2a-protocol.md` — nur falls der Pre-Flight nicht-`D-NONROLE`-Treffer zeigt.
- Modify: `tests/test_routing_tool_definitions.py`, `tests/test_no_role_routes_in_templates.py`, `tests/test_se_role_boundary.py`, `tests/test_knowledge_engine.py` — Semantik-/Signatur-Migration.

## Step-Agent-Map (plan-driven `implement`)

| Step | Task | Agent |
|---|---|---|
| 3 | Resolver-Fundament (roles.py) | developer |
| 4 | Config-Schema activation_groups + addressability | senior-developer |
| 5 | Unified Active Set + name_index | senior-developer |
| 6 | Orchestrator-Fallback name_index | developer |
| 9 | Re-Export _is_role_enabled | developer |
| 10 | Config-Wiring + Block-Snippet-Loader | senior-developer |
| 12 | Slimming se-*-Templates | senior-developer |
| 14 | Slimming übrige 1-generic-Templates | senior-developer |

> `pipeline_stages.implement = 3` entspricht Step 3 (Agent `developer`, in `allowed_agents` der `feature-lifecycle`-Stage `implement`).

---

### Task 1: Working-Tree-Isolation-Gate

**Files:**
- Create: docs/plans/2026-09-19-dynamic-routing-template-slimming-worktree-preflight.md

**Interfaces:** Produces: Inventar der dirty Dateien + Zuordnung "gehört zu diesem Vorhaben ja/nein" + Liste der Plan-Ziel-Dateien, die bereits fremd-dirty sind. Consumes: `.meta-config/project.yaml` (Branch-/Rollen-Kontext) und die Git-Arbeitsbaum-Sicht.
**Agent:** git
**Depends on:** —
**Ziel-AK:** Querschnitt (B4-Vorbedingung, Commit-Hygiene)
**Verifikation:** `git status --porcelain=v1` und `git diff --stat` sind im Report vollständig abgebildet; Report listet jedes Plan-Ziel-File mit Status.
**Akzeptanz:** Der Report führt jede dirty Datei auf und markiert Plan-Ziel-Überschneidungen. Bei Überschneidung mit `agents/1-generic/orchestrator.md`, `tests/test_routing_tool_definitions.py` oder einer anderen Ziel-Datei wird **gestoppt und an User/Orchestrator eskaliert** (fremde Änderungen separat committen/stashen lassen). Es wird nichts committet und keine fremde Datei angefasst.

**Steps:**
- [ ] Step 1: `git status --porcelain=v1` und `git diff --stat` erfassen.
- [ ] Step 2: Dirty-Dateien gegen die Plan-Ziel-Dateien (File Structure) abgleichen.
- [ ] Step 3: Report schreiben; bei Überschneidung Blocker dokumentieren und eskalieren.
- [ ] Step 4: Commit nur des Reports via `git`-Agent: `docs(repo): add worktree preflight for routing slimming`.

---

### Task 2: Snippet-Pre-Flight-Audit (RVW-20)

**Files:**
- Create: docs/plans/2026-09-19-dynamic-routing-template-slimming-snippet-preflight.md
- Modify: snippets/orchestrator/se-mode.md
- Modify: snippets/orchestrator/a2a-protocol.md

**Interfaces:** Produces: Treffer-Inventar des Route-Guard-Detektors über `snippets/**/*.md` (je Treffer: Datei, Zeile, Konstrukt, `D-NONROLE`-Beleg oder Rewrite). Consumes: die im Route-Guard-Test definierten Detektor-/Ausnahme-Regeln sowie die beiden genannten Snippet-Dateien.
**Agent:** developer
**Depends on:** —
**Ziel-AK:** A6 (Pre-Flight-Vorbedingung)
**Verifikation:** `python3 -m pytest tests/test_no_role_routes_in_templates.py -q` (Bestands-Scope, muss weiter grün sein); Detektor-Dry-Run über `snippets/**` ist im Report dokumentiert.
**Akzeptanz:** Der Report enthält 0 nicht-`D-NONROLE`-belegte Treffer. Etwaige nicht-exempte Treffer sind ausschließlich durch Umschreiben der betroffenen Snippet-Datei (keine Detektoränderung) beseitigt; sind keine nötig, bleiben die beiden Dateien unverändert.

**Steps:**
- [ ] Step 1: Detektor-Logik über `snippets/**/*.md` trockenlaufen lassen (Bestands-Scope).
- [ ] Step 2: Treffer klassifizieren (`D-NONROLE`-Beleg vs. echte Verletzung).
- [ ] Step 3: Echte Verletzungen per Snippet-Umschreibung beseitigen (nur bei Bedarf).
- [ ] Step 4: Report schreiben; Commit via `git`-Agent: `chore(guard): preflight snippet corpus for route guard scope`.

---

### Task 3: Resolver-Fundament in roles.py

**Files:**
- Modify: scripts/lib/roles.py
- Create: tests/test_role_activation_resolver.py

**Interfaces:** Produces: `resolve_dotted`, `resolve_activation_gates`, `is_role_enabled`, `resolve_template_roles`, `resolve_active_roles` sowie das Laden des `activation_groups`-Blocks über den bestehenden Rollen-Config-Loader. Consumes: `config/role-defaults.yaml`, Projekt-`config`-Dict, `pathlib.Path`-Root.
**Agent:** developer
**Depends on:** —
**Ziel-AK:** A2
**Verifikation:** `python3 -m pytest tests/test_role_activation_resolver.py -q`
**Akzeptanz:** Resolver-Tests decken ab: `config_flag` mit fehlendem Pfad → `default`; `roles_membership` `any`/`all`; `config` schlägt `default`; `require_template=False` liefert Layer 1 ohne ValueError; `template_roles=None` wird lazy aufgelöst; `warn_sink` erhält deterministisch sortierte, deduplizierte Strings.

**Steps:**
- [ ] Step 1: Tests schreiben (rot) für alle Resolver-Fälle inkl. Determinismus.
- [ ] Step 2: Resolver implementieren; `activation_groups` im Rollen-Loader verfügbar machen (abwärtskompatibel für bestehende `roles`-Leser).
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `feat(routing): add canonical activation resolver`.

---

### Task 4: Config-Schema activation_groups + Addressability

**Files:**
- Modify: config/role-defaults.yaml
- Create: tests/test_role_activation_schema.py
- Create: tests/test_role_addressability_coverage.py
- Create: tests/test_routing_overlap.py
- Modify: tests/test_routing_tool_definitions.py

**Interfaces:** Produces: Top-Level-`activation_groups` (se/knowledge/validator/developer_tiers) mit expliziten `config_predicate`-Blöcken; `routing.addressability` + `routing.name_only_reason` für alle 84 Rollen; echte `routing_patterns` für `openscad-developer`. Consumes: Task 3 (Schema-Lesbarkeit des `activation_groups`-Blocks).
**Agent:** senior-developer
**Depends on:** Task 3
**Ziel-AK:** A1, A5
**Verifikation:** `python3 -m pytest tests/test_role_activation_schema.py tests/test_role_addressability_coverage.py tests/test_routing_overlap.py tests/test_routing_tool_definitions.py -q`
**Akzeptanz:** Verteilung exakt `81 keyword / 2 name_only / 1 excluded`; `excluded` genau `orchestrator`; jede `keyword`-Rolle hat nicht-leere `routing_patterns.keywords` oder `.examples`; `principal-developer`/`intern-developer` sind `name_only` mit nicht-leerem `name_only_reason`; `orchestrator` ist unabhängig von der Ableitung `excluded`; `openscad-developer` hat Patterns. Der bisherige Patternless-Test ist auf die neue Semantik aktualisiert (nicht gelöscht); die `validator`-Erwartung ist auf ein `config={"roles": ["validator"]}`-Fixture migriert.

**Steps:**
- [ ] Step 1: Schema-/Coverage-/Overlap-Tests schreiben (rot); Patternless- und Validator-Assertions migrieren.
- [ ] Step 2: `activation_groups` und `routing.addressability` in der Config ergänzen; `openscad-developer`-Patterns + `name_only_reason` setzen.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `feat(routing): add activation groups and role addressability`.

---

### Task 5: Unified Active Set + name_index

**Files:**
- Modify: scripts/lib/delegation_table.py
- Modify: scripts/lib/agents.py
- Create: tests/test_unified_active_set.py
- Create: tests/test_active_role_call_sites.py
- Create: tests/test_routing_name_index.py

**Interfaces:** Produces: Layer-2-Aktivmenge in Routing-Zielen, Hints und Tabelle; `template_roles`/`warn_sink`-Keyword-Parameter an den betroffenen Buildern; `name_index`-Einträge (`agent`, `short_desc`, `tier`, `orchestrator_only`, `addressability`, `name_only_reason`) und deren Durchreichung in den Routing-Payload. Consumes: Task 3 (Resolver), Task 4 (Adressierbarkeit), das Rollen-Config-Dict.
**Agent:** senior-developer
**Depends on:** Task 3, Task 4
**Ziel-AK:** A3, A4
**Verifikation:** `python3 -m pytest tests/test_unified_active_set.py tests/test_active_role_call_sites.py tests/test_routing_name_index.py tests/test_delegation_table.py -q`
**Akzeptanz:** Routing-Ziele sind exakt die Layer-2-Menge ohne `orchestrator`; Hints/Tabelle nutzen dieselbe Menge; jede Abweichung erzeugt einen deterministischen `warn_sink`-Eintrag, nie einen stillen Drop. `name_index` enthält genau einen Eintrag pro Zielrolle (inkl. `name_only`), ist nach `agent` sortiert und über zwei Aufrufe identisch. Aufrufe ohne explizite Template-Rollen lösen lazy auf und werfen keinen ValueError.

**Steps:**
- [ ] Step 1: Tests schreiben (rot) für Unified Set, Call-Sites und `name_index`.
- [ ] Step 2: Aktivmengen vereinheitlichen, Parameter ergänzen, `name_index` bauen und durchreichen.
- [ ] Step 3: Tests grün; bestehende Delegation-Tests unverändert grün.
- [ ] Step 4: Commit via `git`-Agent: `feat(routing): unify active set and expose name index`.

---

### Task 6: Orchestrator-Fallback-Contract (name_index)

**Files:**
- Modify: agents/1-generic/orchestrator.md
- Create: tests/test_orchestrator_name_dispatch.py

**Interfaces:** Produces: Fallback-Anweisung, Name-Dispatch über `name_index` zu betreiben, und die Kennzeichnung von `name_only`-Rollen als ausschließlich über diesen Kanal erreichbar. Consumes: Task 5 (`name_index` im Routing-Payload), Task 1 (Dirty-Tree-Gate für diese Datei).
**Agent:** developer
**Depends on:** Task 5, Task 1
**Ziel-AK:** A9
**Verifikation:** `python3 -m pytest tests/test_orchestrator_name_dispatch.py -q`
**Akzeptanz:** Der Test rendert den Fallback-Zweig und weist die `name_index`-Anweisung im Prompt-Text nach; der gerenderte `INTENT_ROUTING_TOOLS`-Payload enthält die `name_only`-Einträge. Der Route-Guard bleibt für diese Datei grün.

**Steps:**
- [ ] Step 1: Test schreiben (rot) für Prompt-Text und Payload-Assert.
- [ ] Step 2: Fallback-Zweig um den `name_index`-Contract erweitern.
- [ ] Step 3: Tests grün; `tests/test_no_role_routes_in_templates.py` grün.
- [ ] Step 4: Commit via `git`-Agent: `feat(orchestrator): consume name index in routing fallback`.

---

### Task 7: developer_tiers-Gate-Komplement

**Files:**
- Create: tests/test_developer_tiers_gate.py

**Interfaces:** Produces: Nachweis, dass `principal-developer` bei aktiver `developer_tiers`-Gruppe in Zielmenge und `name_index` liegt, aber keine Keyword-Regel erhält, und bei inaktiver Gruppe in beiden fehlt. Consumes: Task 4 (Gate-Definition), Task 5 (`name_index`/Zielmenge).
**Agent:** developer
**Depends on:** Task 4, Task 5
**Ziel-AK:** A8
**Verifikation:** `python3 -m pytest tests/test_developer_tiers_gate.py -q`
**Akzeptanz:** Beide Zustände (aktiv `all` junior+senior / inaktiv per Default) sind als je ein Testfall abgedeckt; die inaktive Erwartung ist deckungsgleich mit dem bestehenden `principal`-Gate-Fall.

**Steps:**
- [ ] Step 1: Testfälle (rot) für aktiv und inaktiv schreiben.
- [ ] Step 2: Falls nötig Test-Fixtures präzisieren (keine Produktionsänderung in dieser Task).
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `test(routing): cover developer tiers gate complement`.

---

### Task 8: Route-Guard Snippet-Scope (A6)

**Files:**
- Modify: tests/test_no_role_routes_in_templates.py
- Create: tests/test_route_guard_snippets.py

**Interfaces:** Produces: erweiterter Guard-Scope um `snippets/**/*.md` (Detektor-Logik unverändert) und ein Regressionstest über den Snippet-Korpus. Consumes: Task 2 (Pre-Flight-Ergebnis: Korpus ist `D-NONROLE`-exempt).
**Agent:** developer
**Depends on:** Task 2
**Ziel-AK:** A6
**Verifikation:** `python3 -m pytest tests/test_no_role_routes_in_templates.py tests/test_route_guard_snippets.py -q`
**Akzeptanz:** 0 Verstöße der Detektoren `T-ROUTE-COL`, `T-ROLE-ARROW`, `T-HANDOFF`, `T-NEXT` in Templates, Rules **und** Snippets; die `D-*`-Ausnahmen und die Detektor-Regexe sind unverändert.

**Steps:**
- [ ] Step 1: Scope-Test erweitern; neuen Snippet-Scope-Test schreiben (rot vor Scope-Erweiterung).
- [ ] Step 2: Scope-Globs um `snippets/**/*.md` erweitern (Detektoren unangetastet).
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `test(guard): extend route guard scope to snippets`.

---

### Task 9: Re-Export des Rollen-Gates + Test-Migration

**Files:**
- Modify: scripts/lib/frontmatter.py
- Modify: tests/test_se_role_boundary.py
- Modify: tests/test_knowledge_engine.py

**Interfaces:** Produces: der öffentliche Rollen-Gate-Helper mit 3-Parameter-Signatur als Re-Export des Resolvers aus Task 3. Consumes: Task 3 (Resolver), Task 5 (Produktions-Aufrufer in den Agent-Buildern bereits migriert), Task 10 (Config-/Sync-Aufrufer bereits migriert).
**Agent:** developer
**Depends on:** Task 5, Task 10
**Ziel-AK:** A2 (SE-Default-Vereinheitlichung, Signatur-Freeze)
**Verifikation:** `python3 -m pytest tests/test_se_role_boundary.py tests/test_knowledge_engine.py -q`
**Akzeptanz:** Der Helper delegiert an den Resolver; es existiert kein zweiter SE-Default mehr. Die Tests sind auf die neue Signatur migriert; der SE-Default-Test ist an `activation_groups.se.default: false` angeglichen (nicht ersatzlos entfernt). Keine versteckte Global-/Cache-Abhängigkeit.

**Steps:**
- [ ] Step 1: Tests auf die neue Signatur und die neue SE-Default-Semantik migrieren (rot).
- [ ] Step 2: Helper als dünnen Re-Export implementieren.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `refactor(frontmatter): route role gate through activation resolver`.

---

### Task 10: Config-Wiring + Block-Snippet-Loader

**Files:**
- Modify: scripts/lib/config.py
- Modify: scripts/lib/agent_sync.py
- Create: snippets/agents/background-process-guard.md
- Create: snippets/agents/output-guard.md
- Create: snippets/agents/parse-input.md
- Create: tests/test_snippet_inlining_transform.py
- Create: tests/test_warn_sink_wiring.py

**Interfaces:** Produces: Anzeige-Mirror-Variablen für die Aktivierungsgruppen; `warn_sink`-Injektion in die Variablen-Builder; Inlining-Transform (Frontmatter-Strip, `\n`-Normalisierung, `strip("\n")`) und die drei neuen Block-Variablen aus `snippets/agents/`; migrierter Rollen-Gate-Aufruf im Sync. Consumes: Task 3 (Resolver), Task 4 (Config), Task 5 (`template_roles`/`warn_sink`-Signaturen).
**Agent:** senior-developer
**Depends on:** Task 3, Task 4, Task 5
**Ziel-AK:** A2 (Mirror-Variablen), A3 (`warn_sink`-Injektion), B1 (Loader), B3 (Block-Snippet-Transform)
**Verifikation:** `python3 -m pytest tests/test_snippet_inlining_transform.py tests/test_warn_sink_wiring.py tests/test_routing_tool_definitions.py -q`
**Akzeptanz:** Die drei neuen Block-Variablen werden deterministisch aus den Snippet-Dateien geladen und durchlaufen den Transform; der bestehende Snippet-Ladepfad bleibt output-neutral (keine Byte-Änderung generierter SE-/A2A-/Checkpoint-Blöcke). `warn_sink` erhält die Builder-Warnungen statt eines stillen Drops. Der Sync-Rollen-Gate-Aufruf nutzt den Resolver (kein 2-Parameter-Aufruf mehr). Die drei Snippet-Dateien sind route-guard-sauber.

**Steps:**
- [ ] Step 1: Transform-Tests und Wiring-Tests schreiben (rot).
- [ ] Step 2: Transform + Loader für die drei Block-Variablen implementieren; Mirror-Variablen und `warn_sink`-Injektion verdrahten; Sync-Aufruf migrieren.
- [ ] Step 3: Tests grün; bestehende Block-Outputs unverändert.
- [ ] Step 4: Commit via `git`-Agent: `feat(config): wire activation variables and block snippet loader`.

---

### Task 11: Golden-Baseline einfrieren

**Files:**
- Create: tests/fixtures/slimming-golden/README.md
- Create: tests/fixtures/slimming-golden/<role>.md

**Interfaces:** Produces: committed Golden-Files des generierten Outputs für jede aktive Rolle **nach Block A und vor Block B**. Consumes: Tasks 1,3,4,5,6,7,8,9,10.
**Agent:** developer
**Depends on:** Task 1, Task 3, Task 4, Task 5, Task 6, Task 7, Task 8, Task 9, Task 10
**Ziel-AK:** B2 (Freeze-Punkt)
**Verifikation:** `python3 scripts/sync.py --dry-run` und `python3 scripts/sync.py --validate`; die Golden-Files sind per Render-Pfad reproduzierbar.
**Akzeptanz:** Für jede aktive Rolle existiert genau eine Golden-Datei; das `README.md` dokumentiert Erzeugungskommando, Freeze-Zeitpunkt (nach Block A, vor Block B) und den Hinweis, dass Updates nur bewusst mit Diff-Manifest erfolgen. Diese Task ist eine harte Barriere vor jeder Migration.

**Steps:**
- [x] Step 1: Golden-Dateien über den bestehenden Render-/Sync-Pfad erzeugen.
- [x] Step 2: `README.md` mit Freeze-Punkt und Erzeugungskommando schreiben.
- [x] Step 3: Reproduzierbarkeit prüfen (erneuter Render identisch).
- [x] Step 4: Commit via `git`-Agent: `test(slimming): freeze golden baseline before extraction`.

---

### Task 12: Slimming se-*-Templates + Äquivalenz-Gate

**Files:**
- Modify: agents/1-generic/se-architect.md
- Modify: agents/1-generic/se-component-requirements.md
- Modify: agents/1-generic/se-critic.md
- Modify: agents/1-generic/se-developer.md
- Modify: agents/1-generic/se-integration-and-test-manager.md
- Modify: agents/1-generic/se-interface-mgr.md
- Modify: agents/1-generic/se-junior-developer.md
- Modify: agents/1-generic/se-requirements.md
- Modify: agents/1-generic/se-senior-developer.md
- Modify: agents/1-generic/se-termination.md
- Modify: agents/1-generic/se-test-engineer.md
- Modify: agents/1-generic/se-testreviewer.md
- Modify: agents/1-generic/se-validator.md
- Modify: agents/1-generic/se-verifier.md
- Create: tests/test_template_slimming_equivalence.py

**Interfaces:** Produces: das B2-Äquivalenz-Gate (B2a byte-identisch / B2b normalisiert) gegen die Golden-Baseline sowie die Entfernung der inline Anti-Recursion-Prosa in allen `se-*`-Templates. Consumes: Task 10 (Block-Variablen + Loader), Task 11 (Golden-Files).
**Agent:** senior-developer
**Depends on:** Task 10, Task 11
**Verifikation:** `python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_no_role_routes_in_templates.py -q`
**Ziel-AK:** B1, B2
**Akzeptanz:** In den 14 `se-*`-Templates ist jede inline Anti-Recursion-Prosa durch `{{ANTI_RECURSION_BLOCK}}` ersetzt und die übrigen Blöcke durch die passenden `{{*_BLOCK}}`-Referenzen; kein `se-*`-Template enthält einen migrierten Block noch wörtlich. Das Äquivalenz-Gate ist grün: B2a-Vorkommen byte-identisch, B2b-Fälle im Test als normalisiert markiert. Route-Guard 0 Verstöße.

**Steps:**
- [x] Step 1: Äquivalenz-Test schreiben (grün gegen Golden, bevor migriert wird).
- [x] Step 2: Inline-Blöcke in den 14 `se-*`-Templates durch Referenzen ersetzen.
- [x] Step 3: Äquivalenz- und Guard-Tests grün.
- [x] Step 4: Commit via `git`-Agent: `refactor(templates): centralize se role blocks`.

---

### Task 13: Slimming knowledge-*-Templates

**Files:**
- Modify: agents/1-generic/knowledge-curator.md
- Modify: agents/1-generic/knowledge-gardener.md
- Modify: agents/1-generic/knowledge-indexer.md
- Modify: agents/1-generic/knowledge-ingestor.md
- Modify: agents/1-generic/knowledge-linter.md
- Modify: agents/1-generic/knowledge-migrator.md
- Modify: agents/1-generic/knowledge-querier.md

**Interfaces:** Produces: Entfernung der inline Anti-Recursion-Prosa und Zentralisierung der übrigen Blöcke in den 7 `knowledge-*`-Templates. Consumes: Task 10 (Block-Variablen + Loader), Task 11 (Golden-Files), Task 12 (Äquivalenz-Gate-Test).
**Agent:** developer
**Depends on:** Task 10, Task 11
**Ziel-AK:** B1, B2
**Verifikation:** `python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_no_role_routes_in_templates.py -q`
**Akzeptanz:** Kein `knowledge-*`-Template enthält einen migrierten Block wörtlich; Anti-Recursion inline = 0; Äquivalenz-Gate grün; Route-Guard 0 Verstöße.

**Steps:**
- [ ] Step 1: Vorkommen je Datei erfassen (inline Anti-Recursion, Output-Guard, Background-Process, Parse-Input).
- [ ] Step 2: Blöcke durch Referenzen ersetzen.
- [ ] Step 3: Äquivalenz- und Guard-Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `refactor(templates): centralize knowledge role blocks`.

---

### Task 14: Slimming übrige 1-generic-Templates

**Files:**
- Modify: agents/1-generic/_reference-agent.md
- Modify: agents/1-generic/accessibility-specialist.md
- Modify: agents/1-generic/agent-meta-manager.md
- Modify: agents/1-generic/ai-security-guardian.md
- Modify: agents/1-generic/api-specialist.md
- Modify: agents/1-generic/app-lifecycle-governor.md
- Modify: agents/1-generic/bug-feature-analyzer.md
- Modify: agents/1-generic/code-reviewer.md
- Modify: agents/1-generic/concept-architect.md
- Modify: agents/1-generic/concept-reviewer.md
- Modify: agents/1-generic/concept-specifier.md
- Modify: agents/1-generic/copyeditor.md
- Modify: agents/1-generic/data-engineer.md
- Modify: agents/1-generic/database-engineer.md
- Modify: agents/1-generic/dependency-auditor.md
- Modify: agents/1-generic/design-system-architect.md
- Modify: agents/1-generic/developer.md
- Modify: agents/1-generic/devops-engineer.md
- Modify: agents/1-generic/docker.md
- Modify: agents/1-generic/documenter.md
- Modify: agents/1-generic/e2e-tester.md
- Modify: agents/1-generic/effort-estimator.md
- Modify: agents/1-generic/explorer.md
- Modify: agents/1-generic/export-manager.md
- Modify: agents/1-generic/feedback.md
- Modify: agents/1-generic/frontend-component-engineer.md
- Modify: agents/1-generic/git.md
- Modify: agents/1-generic/incident-responder.md
- Modify: agents/1-generic/junior-developer.md
- Modify: agents/1-generic/log-analyzer.md
- Modify: agents/1-generic/mammouth-expert.md
- Modify: agents/1-generic/meta-feedback.md
- Modify: agents/1-generic/openscad-developer.md
- Modify: agents/1-generic/performance-optimizer.md
- Modify: agents/1-generic/planner.md
- Modify: agents/1-generic/principal-developer.md
- Modify: agents/1-generic/product-manager.md
- Modify: agents/1-generic/prompt-engineer.md
- Modify: agents/1-generic/prompt-governor.md
- Modify: agents/1-generic/proofreader.md
- Modify: agents/1-generic/provider-expert.md
- Modify: agents/1-generic/refactoring-specialist.md
- Modify: agents/1-generic/release.md
- Modify: agents/1-generic/requirements.md
- Modify: agents/1-generic/security-auditor.md
- Modify: agents/1-generic/senior-developer.md
- Modify: agents/1-generic/sre-engineer.md
- Modify: agents/1-generic/technical-writer.md
- Modify: agents/1-generic/test-executor.md
- Modify: agents/1-generic/tester.md
- Modify: agents/1-generic/ui-ux-designer.md
- Modify: agents/1-generic/validator.md

**Interfaces:** Produces: Zentralisierung von Output-Guard, Background-Process-Guard und Parse-Input in den übrigen `agents/1-generic`-Templates. Consumes: Task 10 (Block-Variablen + Loader), Task 11 (Golden-Files), Task 12 (Äquivalenz-Gate-Test).
**Agent:** senior-developer
**Depends on:** Task 10, Task 11
**Ziel-AK:** B1, B2
**Verifikation:** `python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_no_role_routes_in_templates.py -q`
**Akzeptanz:** In allen 52 Dateien ist jedes vorhandene Vorkommen des jeweiligen Blocks durch die zugehörige Referenz ersetzt; kein migrierter Block bleibt wörtlich. Die vorhandene `{{ANTI_RECURSION_BLOCK}}`-Referenz in `_reference-agent.md` und `developer.md` bleibt unverändert. Äquivalenz-Gate grün; Route-Guard 0 Verstöße.

**Steps:**
- [ ] Step 1: Vorkommen je Datei erfassen.
- [ ] Step 2: Blöcke durch Referenzen ersetzen.
- [ ] Step 3: Äquivalenz- und Guard-Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `refactor(templates): centralize repeated generic blocks`.

---

### Task 15: Slimming 2-platform-Templates

**Files:**
- Modify: agents/2-platform/agent-meta-developer.md
- Modify: agents/2-platform/homeassistant-developer.md
- Modify: agents/2-platform/homeassistant-documenter.md
- Modify: agents/2-platform/sharkord-developer.md

**Interfaces:** Produces: Zentralisierung der eingebetteten Blöcke in den Plattform-Overrides; dokumentierte B2b-Normalisierung für abweichende Einrückung. Consumes: Task 10 (Block-Variablen + Loader), Task 11 (Golden-Files), Task 12 (Äquivalenz-Gate-Test).
**Agent:** developer
**Depends on:** Task 10, Task 11
**Ziel-AK:** B1, B2
**Verifikation:** `python3 -m pytest tests/test_template_slimming_equivalence.py tests/test_no_role_routes_in_templates.py -q`
**Akzeptanz:** Die eingebetteten Parse-Input-/Output-Guard-/Background-Process-Blöcke sind durch Referenzen ersetzt; abweichende Original-Einrückung ist als B2b normalisiert markiert (keine Byte-Identität zugesichert); die bestehenden `{{ANTI_RECURSION_BLOCK}}`-Referenzen bleiben. Äquivalenz-Gate grün; Route-Guard 0 Verstöße.

**Steps:**
- [ ] Step 1: Einrückung je Vorkommen erfassen und B2a/B2b klassifizieren.
- [ ] Step 2: Blöcke durch Referenzen ersetzen.
- [ ] Step 3: Äquivalenz- und Guard-Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `refactor(templates): centralize platform override blocks`.

---

### Task 16: Diff-Manifest + Snippet-Copy-Contract

**Files:**
- Create: docs/plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md
- Create: tests/test_snippet_copy_contract.py

**Interfaces:** Produces: B2b-Diff-Manifest aller normalisierten Near-Duplikate mit abschnittsweisem Äquivalenz-Nachweis (Input-Parsing, Output-Guard, Handoff-Format, Anti-Recursion erhalten) und den B3-Kopiervertrag der `*_SNIPPETS_PATH`-referenzierten Snippets. Consumes: Tasks 12,13,14,15.
**Agent:** developer
**Depends on:** Task 12, Task 13, Task 14, Task 15
**Ziel-AK:** B2b, B3
**Verifikation:** `python3 -m pytest tests/test_snippet_copy_contract.py tests/test_template_slimming_equivalence.py -q`
**Akzeptanz:** Jedes normalisierte Near-Duplikat ist im Manifest mit Datei, Block und Nachweis gelistet; kein Pflichtsatz ist verloren. Der Kopiervertrag testet, dass genau referenzierte Snippets kopiert werden und Block-Snippet-Dateien (Inlining-Pfad) dem Transform folgen.

**Steps:**
- [ ] Step 1: Normalisierte Diffs aus den Migrationen erfassen.
- [ ] Step 2: Manifest und Kopiervertrag-Test schreiben.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit via `git`-Agent: `docs(slimming): add diff manifest and snippet copy contract`.

---

### Task 17: Vollständiges Verifikations-Gate

**Files:**
- Create: docs/plans/2026-09-19-dynamic-routing-template-slimming-verification.md

**Interfaces:** Produces: Abschlussreport mit Befehlsnachweisen zu `sync.py --validate`, `sync.py --dry-run`, der vollständigen relevanten Test-Suite, dem Äquivalenz-Gate und dem Capability-Unchanged-Nachweis (A7). Consumes: alle Tasks.
**Agent:** validator
**Depends on:** Task 16
**Ziel-AK:** A7, B4, B5
**Verifikation:** `python3 scripts/sync.py --validate && python3 scripts/sync.py --dry-run`; `python3 -m pytest tests/test_no_role_routes_in_templates.py tests/test_routing_tool_definitions.py tests/test_delegation_table.py tests/test_provider_agnostic_dispatch.py tests/test_template_slimming_equivalence.py tests/test_route_guard_snippets.py -q`
**Akzeptanz:** Alle Befehle sind fehlerfrei; `route_intent_tool` ist für alle 9 Provider unverändert `false`, keine Capability-Keys neu/entfernt; der Fallback-`{{#if ROUTE_INTENT_CALLABLE}}`-Zweig besteht. Der Report weist die informativen Zeilen-/Byte-Reduktionszahlen als Metrik aus (kein Hard-Gate).

**Steps:**
- [ ] Step 1: Relevante Test-Suite ausführen und Ergebnis protokollieren.
- [ ] Step 2: `sync.py --validate` und `--dry-run` ausführen.
- [ ] Step 3: Capability-Diff und Reduktionsmetrik dokumentieren.
- [ ] Step 4: Commit via `git`-Agent: `docs(verify): add routing slimming verification report`.

## Parallelisierung / Barrieren

- `parallel_group_1` = {Task 3}: keine parallele Abhängigkeit.
- `parallel_group_2` = {Task 4}: blockiert alle folgenden Block-A-Code-Tasks.
- `parallel_group_3` = {Task 5}: nach Task 3 + Task 4.
- `parallel_group_4` = {Task 6, Task 7, Task 8}: disjunkte Write-Sets; Task 6 zusätzlich Task-1-Gate.
- `parallel_group_5` = {Task 10}: danach Task 9 (wartet auf die migrierten Produktions-Aufrufer in Task 10).
- `barrier_1` = Task 11 (Golden-Baseline) nach allen Block-A-Tasks.
- `parallel_group_6` = {Task 12, Task 13, Task 14, Task 15}: maximale Breite 4, disjunkte Template-Dateisätze.
- `barrier_2` = Task 16 nach allen Migrationen; Task 17 schließt ab.
- **Dependency-Kette (kritischer Pfad):** Task 3 → Task 4 → Task 5 → Task 10 → Task 11 → Task 12/14 → Task 16 → Task 17.

## Self-Review

- **Pflicht-Header vorhanden:** `**Goal:**`, `**Architecture:**`, `**Tech Stack:**`, `**Spec:**`, `## Global Constraints`, `## File Structure`, `pipeline_stages` ✓.
- **AK-Abdeckung:** A1/A5→Task 4; A2→Task 3 + Task 9; A3→Task 5 + Task 10; A4→Task 5; A6→Task 2 + Task 8; A7→Task 17 (unverändert-Verifikation, keine Datei-Änderung an der Capability-Matrix); A8→Task 7; A9→Task 6; B1→Tasks 12–15; B2→Task 11 + Task 12 (Gate) + Task 16 (Manifest); B3→Task 10 + Task 16; B4→Task 17; B5→Task 17. Alle 14 AKs sind abgedeckt.
- **Ownership:** Jede Datei ist in genau einer Task gelistet; keine Datei-Überschneidung. Parallele Gruppen (Task 6–8, Task 12–15) haben disjunkte Write-Sets. Keine Zyklen (Depends-on zeigt ausschließlich auf frühere oder gleichzeitige, aber dateidisjunkte Tasks).
- **Provider-Agnostik:** Keine Provider-Name-Branches; keine Capability-Änderung; `route_intent` bleibt nicht-callable.
- **Dirty-Tree-Schutz:** Task 1 ist Pflicht-Gate; Task 4 und Task 6 dependen darauf; Commit-Regel `git add <exakte Pfade>` global.
- **Keine Platzhalter:** Exakte Pfade, Symbole und Signaturbeschreibungen; keine offenen Aufgaben-/Unbestimmt-Marker, kein leerer Interfaces-Block.
- **Re-Planning-Regel:** Nach Task 11 und nach Task 16 wird der Plan gegen die noch gültigen Annahmen geprüft und bei Abweichung aktualisiert; der Plan ist nicht eingefroren.

## Offene Annahmen

1. **Dirty-Tree-Liste:** Die exakten 12 fremd-dirty Dateien lagen dem Plan nicht als vollständige Liste vor (kein Git-Lesezugriff während der Planung); nur `agents/1-generic/orchestrator.md` und `tests/test_routing_tool_definitions.py` sind namentlich bekannt. Task 1 erhebt die vollständige Liste. Falls eine weitere Plan-Ziel-Datei fremd-dirty ist, blockiert Task 1 die betroffene Task (4 oder 6) bis zur Trennung durch User/Orchestrator.
2. **SE-Default-Migrationstreffer:** `tests/test_knowledge_engine.py` enthält einen Bestandstest, der `se-*` mit leerer Config als enabled erwartet. Da A2 den SE-Default auf `false` vereinheitlicht, wird diese Erwartung in Task 9 auf `false` migriert. Sollte der User die Bestandserwartung erhalten wollen, wäre A2 zu präzisieren (Spec dokumentiert den Behavior-Change jedoch als bewusst).
3. **Import-/Symbol-Referenz-Kanten:** Der statische Plan-Graph prüft neben direkten Datei-Überschneidungen auch Import-/Doc-Referenz-Kanten. Die Task-Beschreibungen nennen daher Produktions-Symbole fremder Module nur beschreibend, nicht als Identifier. Sollte die Konsistenzprüfung dennoch eine Kante als Overlap melden, werden die betroffenen Tasks gemergt (Re-Planning), nicht die Constraints aufgeweicht.
4. **Golden-Umfang:** Der Golden-Satz deckt die aktiven Rollen der Repo-eigenen Config ab; inaktive Rollen (`se-*`, `knowledge-*` soweit nicht aktiv) werden nicht byte-verglichen, sondern über das Äquivalenz-Gate der Migration semantisch geprüft. Die exakte Dateiliste wird in Task 11 aus der aktiven Rollenmenge erzeugt.
