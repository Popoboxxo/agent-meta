---
spec-id: SPEC-orchestrator-topology-2026-11-03
title: Orchestrator-Topologie konfigurierbar (primary | subagent | hybrid) — Systemdesign
issue: 1077
related-issues: [1007, 1006, 547, 516, 369]
status: Entwurf
---

# Orchestrator-Topologie konfigurierbar — Design

> Status: **Entwurf** — dieses Dokument ist **Spec-Input**. Den Approval-Marker
> `Status: APPROVED` setzt ausschließlich `concept-reviewer`, nicht dieses Dokument.
> Trace-Anker (von der Spec unverändert zu übernehmen):
> `spec-id: SPEC-orchestrator-topology-2026-11-03`

Dieses Dokument ist ein **Systemdesign** (Architectural, XL): Komponentenkarte,
Schnittstellen-Contracts, Trade-off-Entscheidungen, Datenfluss, Phasenzerlegung.
Es enthält **keinen Implementierungscode** und **keine Spec**. Es ist der
vorgelagerte Stage-Input der Pipeline `quality_pipelines.concept-driven-dev`
(Stage `specify`), siehe `.opencode/skills/spec-plan-workflow/SKILL.md`.

- **Grundlage:** Issue #1077 (Body + Kommentar vom 2026-11-02), #1007 (nur §1/§3
  als Kontext für den Opencode-Surface), #1006 (Opencode-Entry-Point), #547
  (Worktree-Isolation, Nicht-Ziel), #516 (Guard-Selbstdeklaration), #369
  (Delegationstiefe).
- **Verifizierter Stand:** `main` == `origin/main` == `95756dfe` (Auftragsangabe,
  §16 Nr. 1 — in dieser Runde nicht selbst nachgeprüft).
- **Verifikations-Legende:** **VERIFIED** = im Repo gelesen (Fundstelle als
  `datei:symbol`); **HYPOTHESIS** = nicht verifiziert, im Text markiert;
  **BRIEF** = aus dem Auftrag übernommen, nicht selbst geprüft.

### Revision

| Datum | Autor | Änderung |
|---|---|---|
| 2026-11-03 | concept-architect | Erstfassung (Rev. 1). 10 Entscheidungen (D1–D10), Provider-Matrix über das *tatsächlich registrierte* Set, Phasen P0–P4. |
| 2026-11-03 | concept-architect | **Rev. 2 — B1:** Matrix aus vorhandenen Capability-Keys abgeleitet, `hybrid` in v1 nirgends gewährt, `topology_verified_state` je Provider (§4.1, D10, §7, P0). |
| 2026-11-03 | concept-architect | **Rev. 2 — B2:** `context.py::apply_settings_surface_shape` ist P2-Contract: kein `default_agent` bei effektiver Topologie ≠ `primary`; AC-14 + Migrationsregel (§4.6, D9, §11 P2, §12). |
| 2026-11-03 | concept-architect | **Rev. 2 — B3:** Same-Scope-Konflikt als harter stdlib-Check `config.py::_validate_orchestrator_topology` (Muster `_validate_providers`); Schema-`if/then` nur Dokumentationshilfe (§4.7, D3, AC-1, AC-17). |
| 2026-11-03 | concept-architect | **Rev. 2 — B4:** `variables.py::_expand_conditionals`-Whitelist, `standalone.py::_CONDITIONAL_FALSE_FLAGS`, `consistency/placeholders.py::_BUILTIN_VARS` in P1; else-Zweig mit verschachteltem `ROLE_ORCHESTRATOR_ACTIVE` wortgleich; Golden-Fixture „Rolle inaktiv + Key unset" (§4.3, §10, P1/P4, AC-6, AC-18). |
| 2026-11-03 | concept-architect | **Rev. 2 — B5:** `singleton` ist presence-only Alias ohne Schema-`default`; Konflikt im stdlib-Validator; Cross-Scope `primary` × globales N>1 in D3/§8 (D5, §4.7, AC-8/AC-9). |
| 2026-11-03 | concept-architect | **Rev. 2 — A1:** Deviationssatz `hybrid` (positions-agnostisch statt „primary *und* zusätzlich spawnbar") in §1, D2 und Concept-Doc (P4). |
| 2026-11-03 | concept-architect | **Rev. 2 — A2:** `resolve_topology` nimmt `mode: str` als Parameter; `topology.py` bleibt Blattmodul ohne `variables.py`-Import (§4.1). |
| 2026-11-03 | concept-architect | **Rev. 2 — A3:** Global-Vertrag für provider-lose `ORCH_TOPOLOGY_*`-Flags in `_build_variables` definiert (§4.3, §5). |
| 2026-11-03 | concept-architect | **Rev. 2 — A4:** S2 korrigiert: zwei direkte `primary-role`-Leser; „ein Lesezugriff" ist Ziel, nicht Ist-Zustand; `providers.primary_role` als Accessor (§2 S2, §4.5). |
| 2026-11-03 | concept-architect | **Rev. 2 — A5:** ActiveSet-Konjunkt aus `_opencode_entry_point` explizit erhalten (§4.6, §8, AC-14). |
| 2026-11-03 | concept-architect | **Rev. 2 — A6:** Same-Object-Fall `provider-overrides.<P>.{mode: main-chat, topology: primary}` explizit D3 (1) = ERROR (§4.7, §8). |
| 2026-11-03 | concept-architect | **Rev. 2 — A7:** Audit-Datensatz auf id + scope + spawn time + spawned-by erweitert (§9.1, AC-11). |
| 2026-11-03 | concept-architect | **Rev. 2 — A8:** Phasenschnitt: P1 landet `role_emitted_for_provider` + Tests, **keine** Call-Site; `agent_sync.py` wandert nach P2 (§11, R1). |
| 2026-11-03 | concept-architect | **Rev. 2 — A9:** `--validate-spec-plan` bleibt WARNING (`spec-plan-required: false`, DoD `rapid-prototyping`); Klassifikations-Mismatch dokumentiert, Spec trägt die literalen Überschriften (§13, §17). |
| 2026-11-03 | concept-architect | **Rev. 2 — A10:** `progress-<id>.md` ist rein menschlich lesbar (kein Konsument); `current.md` bleibt das einzige maschinell gelesene Fortschritts-Artefakt; `recovery.py` liest nur Checkpoints (§5, §9.3). |
| 2026-11-03 | concept-architect | **Rev. 2 — A11:** S9 auf `datei:symbol` umgestellt (§2 S9). |
| 2026-11-03 | concept-architect | **Rev. 3 — M1:** custom-Zeile behauptet **kein** `subagent: yes` mehr (alle vier Zellen `UNVERIFIED ⇒ no`); Zählung einmalig auf **40 = 25 datenabgeleitet + 15 `UNVERIFIED ⇒ no`** korrigiert (10 hybrid, 2 unverifizierte `primary` [Codex, Mammouth], 3 custom); AC-16 und R10 tragen denselben Satz. |
| 2026-11-03 | concept-architect | **Rev. 3 — M2:** falsche Symbolnamen ersetzt — `variables.py::strip_inactive_conditional_blocks` (Whitelist Z. 431–451), `_conditional_active` (Z. 404), `_FALSE_DEFAULT_CONDITIONALS` (Z. 52); `rules.py::_merged_rule_vars` mit `variables=None` ist real; `ORCH_TOPOLOGY_EXPLICIT` u. a. fail-closed in `_FALSE_DEFAULT_CONDITIONALS` ist P1-Pflicht (sonst rendert der abwesende Key den neuen Zweig). |
| 2026-11-03 | concept-architect | **Rev. 3 — M3:** AC-8/AC-9, die Singleton-Zeilen von AC-17 und §4.7 (d)/(e) sind **P3-only**; `max-instances` hat genau ein Zuhause (Key + `maximum: 8` in P3, vorher existiert er nicht); `ORCH_MAX_INSTANCES`/`ORCH_SINGLETON_DECLARED` gehören P3, nicht P1. |
| 2026-11-03 | concept-architect | **Rev. 3 — Minor 1:** `topology_effective != "main-chat-inert"` durch das boolesche Prädikat `_role_suppressed_by_mode` ersetzt; kein Pseudo-Topologie-Wert (§4.2). |
| 2026-11-03 | concept-architect | **Rev. 3 — Minor 2:** `ORCH_SINGLETON` → `ORCH_SINGLETON_DECLARED` (Deklaration ≠ effektiver Zustand); effektiver Singleton folgt aus `ORCH_MAX_INSTANCES == "1"` (§4.3, AC-18). |
| 2026-11-03 | concept-architect | **Rev. 3 — Minor 3:** Validator-Meldungstext als stabiler Teilstring-Vertrag gepinnt (§4.7), AC-17 testet Teilstrings statt Satzformen. |
| 2026-11-03 | concept-architect | **Rev. 3 — Minor 4:** degradiertes `hybrid` fällt fail-safe auf **`subagent`** (nicht „provider-eigene Position"); damit entsteht auf Claude/Opencode/Continue/Kimi kein `default_agent: orchestrator` (§1, D10, §7). |
| 2026-11-03 | concept-architect | **Rev. 3 — Info:** OQ-5 „v1-Schnitt (Builder-Default + genau ein spawnbarer Orchestrator; Multi-Instanz = P3)" mit Default **ja** und dem Hinweis, dass P3 der unmittelbar nächste Schritt ist (§11, §15). |

---

## 1. Problem und Ziel

Die Frage „ist der Orchestrator ein **Primary Agent** oder ein **gespawnter
Subagent**?" ist heute **kein User-Entscheid**, sondern ein Nebeneffekt genau
eines Daten-Keys: `providers.<P>.primary-role` in `config/ai-providers.yaml`
(VERIFIED, `config/ai-providers.yaml` → `Opencode.primary-role` — nur
`Opencode` setzt ihn).
Daraus folgen drei Probleme (Issue #1077 §1.2):

1. **Strukturell unterschiedliches Verhalten je Provider** ohne
   Konfigurationsmöglichkeit — die Antwort steckt im Framework-Registry.
2. **Nicht auffindbar:** `orchestrator.mode` (`strict|advisory|main-chat`)
   klingt so, als steuere er das, tut es aber nicht (`strict`/`advisory` ändern
   nur die Gate-Stärke, `main-chat` entfernt den Orchestrator ganz, VERIFIED
   `scripts/lib/variables.py:_resolve_orch_mode`,
   `scripts/lib/agent_sync.py:_should_skip_role`).
3. **Kein Multi-Orchestrator**, obwohl scope-disjunkte Parallel-Stränge je
   ihren eigenen Delegations-Wurzel-Agenten bräuchten — die Singleton-Regel
   (`rules/1-generic/a2a-delegation-gates.md:6`, VERIFIED) verbietet
   `subagent_type: orchestrator` pauschal für Worker.

**Ziel:** eine explizite, dokumentierte Projekt-Einstellung
`orchestrator.topology` mit `primary | subagent | hybrid`, ein dazu
orthogonaler Multi-Instanz-Vertrag, harte Lautstärke bei Degradierung, und
**exakte Rückwärtskompatibilität** bei ungesetztem Key.

**Nutzer-Intent (Auftrag, bisher im Design unterbelichtet):** Mit
`topology: subagent` muss in einem **frischen** Opencode-v2-Projekt der
Main-Chat-Default der **Builder** (Main Chat) sein — nicht der Orchestrator.
Der Orchestrator läuft dann als `mode: subagent`; ein
`default_agent: orchestrator` auf eine Subagent-Datei ist der zu vermeidende
Zustand. Das ist nicht nur eine Emissions-, sondern eine **Writer**-Anforderung
(§4.6, AC-14).

**Deviation zu #1077 §2 (A1, verbindlich):** #1077 beschreibt `hybrid` als
„die Rolle ist primary **und** kann zusätzlich gespawnt werden". Dieses Design
verengt `hybrid` auf **positions-agnostisch (entweder/oder)** — dieselbe Rolle
darf als Einstieg *oder* als gespawnter Subagent auftreten. Begründung: die
„primary + zusätzliche gescopte Instanzen"-Lesart verlangt einen
`kind`-Diskriminator in der Identität, zwei Checkpoint-Namespaces, zwei
Gate-Stärken und eine zweite Adressierungsregel (D2, verworfene Alternative).
Die Verengung ist keine Implementierungsvereinfachung, sondern eine bewusste
Semantik-Entscheidung; sie steht zusätzlich im Concept-Doc (P4) und muss in
jeder Doku-Tabelle neben der Issue-Tabelle genannt werden.

**Nicht-Ziel** dieses Designs: Implementierung, Spec, Plan.

---

## 2. Ist-Stand (verifizierte Fakten, die das Design tragen muss)

| # | Fakt | Fundstelle |
|---|---|---|
| S1 | Topologie entsteht als Nebeneffekt: `mode = 'primary'` **nur** wenn ein explizites `primary-role` die Rolle nennt; v2 pinnt alle anderen auf `subagent`; v1 lässt `mode` weg | `scripts/lib/provider_transform.py:_apply_agent_transform` |
| S2 | **Es gibt heute zwei direkte `primary-role`-Leser** — `context.py::apply_settings_surface_shape` (`pc.get("primary-role")`, ohne Default) und `provider_transform.py::_apply_agent_transform` (`.get('primary-role', 'orchestrator')`, **mit** Code-Default für die Subagent-Allowlist). `providers.explicit_primary_role()` ist **nicht** der einzige Leser; „genau ein Lesezugriff" ist das Ziel von R1, nicht der Ist-Zustand. | `scripts/lib/context.py:apply_settings_surface_shape`, `scripts/lib/provider_transform.py:_apply_agent_transform`, `scripts/lib/providers.py:explicit_primary_role` |
| S3 | Der Entry-Point (`default_agent`) wird an **zwei** Stellen geschrieben: `apply_settings_surface_shape` für die v2-Erstinitialisierung (Datei wird beim Anlegen geschrieben) und der Managed-Merge für v1+v2 | `scripts/lib/context.py:apply_settings_surface_shape`, `_init_provider_settings_json`, `scripts/lib/isolation.py:_sync_opencode_runtime_gate` |
| S4 | `default_agent` und Gate-Deny sind **eine** Invariante (D1a): ohne valides `default_agent` wird kein Deny geschrieben, der Gate wird lautstark suspendiert | `scripts/lib/isolation.py:_gate_invariant_warning`, `_has_valid_default_agent` |
| S5 | Entry-Point-Prädikat ist „explizit **und** generiert": `explicit_primary_role` ∩ `ActiveSet.roles`; der ActiveSet-Konjunkt ist `active_set is not None and role not in active_set.roles ⇒ None` | `scripts/lib/isolation.py:_opencode_entry_point` |
| S6 | Mode-Auflösung mit Präzedenz `provider-override.mode > orch_config.mode > legacy enabled/strict`; genau eine Funktion | `scripts/lib/variables.py:_resolve_orch_mode` |
| S7 | Der Per-Provider-Loop baut die `ORCH_MODE_*`-Flags nur neu, wenn der Provider-Override `mode` setzt; das geteilte `variables`-Dict wird nie mutiert | `scripts/lib/sync_pipeline.py:sync_all_providers` (Override-Block) |
| S8 | Unter `main-chat` wird die Rolle `orchestrator` **gar nicht** emittiert (nicht in `expected_filenames` → stale Datei wird gepruned) | `scripts/lib/agent_sync.py:_should_skip_role` |
| S9 | Ein einheitliches „wird diese Rolle für diesen Provider emittiert"-Prädikat existiert **noch nicht**; es ist als `role_emitted_for_provider` in `active_set.py` bereits geplant (D16 des Bug-Batch-Plans, ausdrücklich „#1077-fähig") | `docs/plans/2026-10-31-bug-batch-plan.md` (`role_emitted_for_provider`, `active_set.py`) |
| S10 | Schema: `orchestrator` ist offen (`additionalProperties: true`), `provider-overrides` ist geschlossen (`additionalProperties: false`) und kennt nur `mode` | `config/project-config.schema.json` (`orchestrator`, `provider-overrides`) |
| S11 | `max-parallel-agents` ist **top-level** (nicht unter `orchestrator`), `integer 1..5`, Default `2`, Bedeutung: Parallelität *innerhalb* eines Koordinators | `config/project-config.schema.json`, `scripts/lib/config.py:_build_variables` |
| S12 | Checkpoints liegen als `<checkpoint-dir>/<session-id>.json`; die Session-ID wird fail-closed validiert (keine Separatoren, kein `..`, kein absolut) | `scripts/lib/checkpoint.py:validate_session_id`, `CheckpointStore._session_file` |
| S13 | Der Fortschritts-Report ist **eine** Datei `<progress-dir>/current.md` (Tier A overwrite, Tier B append mit Lock); es gibt **keinen** Code-Leser für `progress-<id>.md` | `scripts/lib/checkpoint.py:_write_progress_file` |
| S14 | Legacy-Checkpoints werden über den Glob `.meta-viz/checkpoint-*.json` gelesen; `recovery.py` liest ausschließlich Checkpoints, keine Fortschrittsdateien | `scripts/lib/recovery.py:_LEGACY_GLOB` |
| S15 | Viz-Event-Log ist **eine** append-only Datei (Default `.meta-viz/events.jsonl`) | `config/project-config.schema.json` (`viz.event_log`) |
| S16 | Ein „Delegations-Tracker" existiert **nur im Kontext** (Prompt-Artefakt), nicht als Datei | `rules/1-generic/a2a-delegation-gates.md`, `config/delegation-syntax.yaml` |
| S17 | Der Guard ist selbstdeklariert (`#agent-meta:agent=<name>`), Sentinel-Regex ist auf `[A-Za-z0-9_-]+` und Zeilenende verankert; Audit-Log existiert | `hooks/1-generic/orchestrator-guard-impl.sh` |
| S18 | Die Provider-Registry hat **9** Einträge (Claude, Gemini, Opencode, Continue, Copilot, Mammouth, Codex, ZCode, KimiCode); `registered_provider_names()` ist die Union beider Registry-Dateien | `config/ai-providers.yaml`, `config/provider-capabilities.yaml`, `scripts/lib/providers.py:registered_provider_names` |
| S19 | Capability-Daten sind der einzige erlaubte Provider-Unterschied (kein `if provider == "Name"`) | `AGENTS.md` (Code-Konventionen), `.opencode/skills/provider-agnostic/SKILL.md` |
| S20 | Singleton-Sätze stehen in **generierten** Artefakten und in Golden-Fixtures | `agents/1-generic/orchestrator.md` (§ Singleton-Regel), `agents/1-generic/_reference-agent.md`, `tests/fixtures/compact-golden/*`, `tests/fixtures/slimming-golden/*` |
| S21 | `apply_settings_surface_shape` schreibt für `opencode-json-v2` **unbedingt** `document["default_agent"] = pc.get("primary-role")`, ohne Topologie-/ActiveSet-Bezug; `_init_provider_settings_json` schreibt die Datei beim Anlegen. Der Managed-Merge räumt einen solchen Wert **nicht** ab, wenn `desired is None` und kein State-Record existiert (`_merge_default_agent` lässt Nutzerwerte stehen) | `scripts/lib/context.py:apply_settings_surface_shape`, `_init_provider_settings_json`, `scripts/lib/isolation.py:_merge_default_agent` |
| S22 | `_validate_config` behandelt **nur** `_validate_model_inheritance`, `_validate_providers`, `_validate_repo_containment`, `_validate_subagent_permissions` u. a. hart; Schema-Verstöße werden als **Warnungen** gedruckt (max. 5) und bei fehlendem `jsonschema` komplett übersprungen. Ein Schema-`if/then` erzeugt weder rc≠0 noch Sync-Abbruch | `scripts/lib/config.py:_validate_config` (Docstring + Rumpf), `_validate_providers` |
| S23 | Die Conditional-Maschinerie ist `strip_inactive_conditional_blocks`: die Whitelist (`conditional_vars`) wird **innerhalb** der Funktion aus `variables` gebaut (Z. 431–451; Präfixe `DOD_*`, `ORCH_MODE_*`, `REPO_CONTAINMENT_*`, `SUBAGENT_PERMISSIONS_*`, `RELEASE_CHECKLIST_*`, `*_SET`, `ROLE_*_ACTIVE`); ein **nicht** gelistetes `{{#if}}` wird nicht gestrippt und behält **beide** Zweige. `_conditional_active` behandelt eine **abwesende** Variable als **aktiv** (`default = "false" if var in _FALSE_DEFAULT_CONDITIONALS else "true"`); nur ein Eintrag in `_FALSE_DEFAULT_CONDITIONALS` macht „abwesend" = „inaktiv" (genau deshalb stehen `GATE_NEUTRAL`/`CONTEXT_PROFILE_COMPACT` dort). `_merged_rule_vars` unterstützt `variables=None` ausdrücklich und baut die Provider-Flags selbst — dieser Render-Pfad ist real. `standalone.py::_CONDITIONAL_FALSE_FLAGS` braucht je Flag einen literalen Eintrag; `consistency/placeholders.py::_BUILTIN_VARS` meldet fehlende neue Builder-Variablen als ERROR | `scripts/lib/variables.py:strip_inactive_conditional_blocks`, `scripts/lib/variables.py:_conditional_active`, `scripts/lib/variables.py:_FALSE_DEFAULT_CONDITIONALS`, `scripts/lib/rules.py:_merged_rule_vars`, `scripts/lib/standalone.py:_CONDITIONAL_FALSE_FLAGS`, `scripts/lib/consistency/placeholders.py:_BUILTIN_VARS` (`check_builder_known_set`) |
| S24 | `topology_support`, `topology_degrade`, `orchestrator_instances`, `topology_verified_state` existieren heute **nicht**; vorhanden sind `main_agent_selectable`, `subagent_dispatch`, `parallel_execution`, `file_based_agents`, `bootstrap_required`, `fanout_mechanism` sowie das Muster `surface_verified_state` | `config/provider-capabilities.yaml` |

**Konsequenz aus S20:** Jede *unbedingte* Textänderung an der Singleton-Regel
ändert Bytes in **jedem** bestehenden Consumer-Projekt und bricht damit die
Byte-Identitäts-AC (§12). Die Regeländerung aus §10 muss deshalb
**conditional** gerendert werden (Default-Zweig = heutiger Text, inklusive des
verschachtelten `{{#if ROLE_ORCHESTRATOR_ACTIVE}}`).

**Konsequenz aus S22:** Ein „Schema-ERROR" ist in diesem Repo **kein**
Fehlerkanal. Die Same-Scope-Widersprüche aus D3/D5 werden deshalb als harter
stdlib-Check in `_validate_config` verankert (§4.7); das Schema-`if/then`
bleibt als Dokumentations- und Editor-Hilfe, nicht als Enforcement.

**Konsequenz aus S24:** Die Matrix (§7) darf keine neuen, unbelegten Keys
behaupten. Sie leitet jede Zelle aus den **vorhandenen** Capability-Keys ab und
markiert die Zellen, die keine Datenbasis haben, als `UNVERIFIED ⇒ no`
(Repo-Konvention: `provider-capabilities.yaml` Kopfkommentar, „an UNVERIFIED …
maps to sequential-fallback/false, never to a speculative mechanism").

### 2.1 Trace: Issue → Design

| Quelle | Anforderung | Design-Abschnitt | Abgedeckt |
|---|---|---|---|
| #1077 §1 | Topologie ist Nebeneffekt, nicht auffindbar, kein Multi-Orchestrator | §1, §2 S1/S8, D9 | ja |
| #1077 §2 | Enum `primary \| subagent \| hybrid`; `hybrid` = primary **und** zusätzlich spawnbar | §1 (Deviation), D1, D2, §7 | ja — mit dokumentierter Verengung (A1) |
| #1077 §2.1 | Zwei orthogonale Achsen (Topologie × Multiplizität) | D4, D5, §8 | ja |
| #1077 §3 | Provider-Analyse **vor** Enum-Finalisierung; nichts versprechen, was nicht belegbar ist | §7, §11 P0, D10 | ja — konservative Ableitung + `topology_verified_state` (B1) |
| #1077 §4 | Multi-Instanz: Identität, Zustands-Isolation, Audit | §9, D6, D7, AC-10/AC-11 | ja |
| #1077 §5 | ACs: kein Verhaltenswechsel ohne Key, laute Degradierung, Doku | §12 AC-1…AC-7, D9, D10 | ja |
| Kommentar (Achsen) | Topologie und Anzahl sind getrennte Achsen, keine stille Präzedenz | D1, D5 | ja |
| Kommentar (Matrix) | Provider × Struktur als Tabelle | §7 | ja |
| Kommentar (Evidenz) | Matrix ist Vorbedingung, nicht Nacharbeit | §7-Kopf, §11 P0, §16 | ja |
| Kommentar §4 (Audit) | Datensatz = id + scope + spawn time + spawned-by | §9.1, AC-11 | ja (A7) |
| Kommentar (singleton) | `singleton`-Alias mit Default `true` | D5, §4.7, AC-8 | ja — presence-only, Default aus `max-instances` abgeleitet (B5) |
| Kommentar (Doku/Regeln) | Regel- und Doku-Anpassung | §10, AC-4, P4 | ja |
| **Nutzer-Intent (Auftrag)** | **Main-Chat-Default = Builder; Orchestrator als Subagent** | §1, §4.6, D9, AC-14, R2 | ja (B2) |
| Review B1 | Matrix als Vorbedingung vs. Behauptung | §7, D10, P0 | ja |
| Review B2 | zweiter `default_agent`-Schreiber | §4.6, D9, AC-14, P2 | ja |
| Review B3 | Same-Scope-Fehlerkanal | §4.7, D3, AC-1/AC-17 | ja |
| Review B4 | Conditional-Maschinerie + Byte-Identität | §4.3, §10, P1/P4, AC-6/AC-18 | ja |
| Review B5 | `singleton`-Semantik | D5, §4.7, D3, AC-8/AC-9 | ja — P3-only (M3) |
| Review Rev.3 M1 | Matrix ohne unbelegte `yes`-Zellen; genau eine Zählung | §7, AC-16, R10 | ja |
| Review Rev.3 M2 | echte Conditional-Symbole + fail-closed Default | S23, §4.3, §10, P1, AC-18 | ja |
| Review Rev.3 M3 | Phasenschnitt vs. ACs; ein Zuhause für `max-instances` | AC-8/AC-9/AC-17, §4.7, P3, R8 | ja |

---

## 3. Komponentenkarte

Neue und geänderte Komponenten mit Grenzen und Verantwortlichkeit (je genau eine):

```
+-------------------------------------------------------------------+
| C1  Schema  config/project-config.schema.json                     |
|     Besitzt: Enum, Defaults, dokumentierende Kreuz-Constraints    |
+----------------------------+--------------------------------------+
                             | liest
+----------------------------v--------------------------------------+
| C2  Auflöser  scripts/lib/topology.py  (NEU, Blattmodul)          |
|     Besitzt: declared -> effective -> supported/degraded          |
|     Kennt: providers.py, caps; mode kommt als Parameter            |
+----+----------------+----------------+----------------+------------+
     |                |                |                |
     v                v                v                v
+---------+   +---------------+  +------------+  +------------------+
| C3      |   | C4 Variables  |  | C5 Emitter |  | C6 Konsistenz    |
| active_ |   | ORCH_TOPOLOGY |  | provider_  |  | topology.py      |
| set.py  |   | ORCH_MAX_...  |  | transform  |  | (WARNING/INFO)   |
| role_   |   | (flat flags)  |  | isolation  |  |                  |
| emitted |   |               |  | context    |  |                  |
+---------+   +---------------+  +------------+  +------------------+
                    |                   |                  |
                    v                   v                  v
              +----------------------------------------------------+
              | C7  Multi-Instanz-Zustand                          |
              |     checkpoint.py (session-id-Komposition)         |
              |     delegation_syntax.py (Envelope-Feld)           |
              |     viz-Events (Feld-Tagging, keine Datei-Shards)  |
              +----------------------------------------------------+
+-------------------------------------------------------------------+
| C8  Config-Validator  scripts/lib/config.py                       |
|     Besitzt: harte Same-Scope-Ablehnung (stdlib, kein jsonschema)  |
+-------------------------------------------------------------------+
```

| Komponente | Typ | Verantwortlichkeit (genau eine) | Grenze / Begründung |
|---|---|---|---|
| **C1 Schema** | geändert | Deklariert die Keys, Defaults und die *dokumentierbaren* Widersprüche | Darf keine Provider-Semantik kennen → keine Provider-Enums im Schema; kein `default` für `singleton` (B5) |
| **C2 `topology.py`** | **neu** (Blattmodul) | Eine Auflösungskette `declared → effective → degraded`, plus Instanzzahl | Eigene Datei statt `variables.py`-Extension, weil `variables.py` bereits 797 Zeilen hat und `_resolve_orch_mode` dort *ausdrücklich* die eine Mode-Quelle ist. **Importiert `variables.py` nicht**; `mode` wird als Parameter übergeben (A2). Muster: `context_profile.py` / `repo_containment.py` |
| **C3 `role_emitted_for_provider`** | **neu** in `active_set.py` | Ein einziges Prädikat „wird Rolle R für Provider P emittiert?" | Verhindert die zweite Skip-Stelle (Risiko R1). Ist im Bug-Batch-Plan schon als D16 vorgesehen → **Koordinationspflicht** |
| **C4 Variables** | geändert | Rendert die aufgelösten Werte in flache, sich gegenseitig ausschließende Flags | Keine Logik; nur `_orch_mode_flags`-Analogon; Whitelist-Registrierung ist Teil des Contracts (B4) |
| **C5 Emitter** | geändert | Setzt die *effektive* Topologie in `mode` / `default_agent` / Skip um | Liest nur den aufgelösten Wert, nie den Roh-Key, nie den Provider-Namen. **Ausnahme Contract:** `apply_settings_surface_shape` erhält die aufgelöste Topologie als Parameter (B2) |
| **C6 Konsistenz** | **neu** (`consistency/topology.py`) | Macht Degradierung laut (WARNING) und die Ableitung sichtbar (INFO) | Kein Schreiben, kein Exit; nur `Finding`s |
| **C7 Zustand** | geändert | Namespaces für N Instanzen; Migration | Nur bei N>1 aktiv; bei N=1 byte-identisch |
| **C8 Validator** | **neu** in `config.py` | Harte Ablehnung der *selbstwidersprüchlichen* Konfiguration | stdlib-only, läuft in `sync` **und** `--validate`; Muster `_validate_providers`; kein `jsonschema` nötig (B3) |

**Warum nicht eine Komponente?** Schema (statische Constraints), Auflöser
(Laufzeit-Präzedenz), Emitter (Provider-Form), Validator (harter Abbruch) und
Konsistenz (Report) haben unterschiedliche Fehlerverträge: Schema = Editor-Hilfe,
Validator = harter Abbruch, Auflöser = `SyncError` mit Hint, Emitter =
schreiben, Konsistenz = nie abbrechen. Ein Zusammenlegen würde genau die
Fehlerklasse erzeugen, die #1077 beklagt (stille Präzedenz).

**Warum nicht mehr Komponenten?** Kein eigenes `topology_config.py`, kein
weiterer Resolver-Cache, keine Provider-spezifische Emitter-Datei — die
bestehende Daten-Dispatch-Struktur (`agent-transform`-Block, Capability-Flags)
trägt die Differenzierung bereits (S19).

### 3.1 Invocation-/Main-Loop-Unterschiede (Checkliste je Provider)

Die Topologie beschreibt die *Position* der Rolle, nicht den Aufrufpfad. Für
die Spec ist trotzdem je Provider zu klären, ob die Rolle in beiden Positionen
denselben Main-Loop sieht. Die Tabelle ist eine **Prüf-Checkliste**, keine
Behauptung: `unverified` heißt „kein Datum im Repo, vor einem Zell-Upgrade
belegen" (§16).

| Provider | Prompt-Caching | Delegationstiefe (#369) | Resume/Checkpoint | Progress-Kanal |
|---|---|---|---|---|
| Claude | `unverified` (kein Capability-Key) | `required_depth: 2` (DOCUMENTED) | `unverified` | `unverified` |
| Opencode | `unverified` | `required_depth: 2` (DOCUMENTED) | `unverified` (kein `resume` in `task`) | `unverified` |
| Gemini | `unverified` | `required_depth: 2` (DOCUMENTED) | `unverified` | `unverified` |
| Continue | `unverified` | `required_depth: 2` (DOCUMENTED) | `n/a` (kein Subagent-Kanal) | `unverified` |
| Copilot | `unverified` | `required_depth: 2` (DOCUMENTED) | `unverified` | `unverified` |
| Mammouth | `unverified` | `required_depth: 2` (DOCUMENTED) | `unverified` | `unverified` |
| Codex | `unverified` | `required_depth: 2` (DOCUMENTED) | `resume_agent` (DOCUMENTED) | `unverified` |
| ZCode | `unverified` | `required_depth: 2` (DOCUMENTED) | `unverified` | `unverified` |
| KimiCode | `unverified` | `required_depth: 2` (DOCUMENTED) | `resume`-Feld (DOCUMENTED) | `unverified` |

**Vertrag:** Ein `topology_support`-Wert darf nur dann `true` werden, wenn die
zugehörige Zeile dieser Checkliste für die *Position* keine offenen
`unverified`-Felder mehr hat — außer `prompt-caching` (kein Topologie-Delta)
und `progress` (Kanal ist topologie-unabhängig). Bis dahin bleibt die
`topology_verified_state`-Zelle auf `UNVERIFIED` und die Auflösung konservativ.

---

## 4. Schnittstellen-Contracts

Alle Pfade relativ zum Framework-Root; Signaturen sind Design-Vorgabe, keine
Implementierung. Fehlerpfad-Konvention des Repos: `SyncError` (→ CLI rc 1) im
Auflöser; **harte Config-Checks** folgen `_validate_providers` (stderr +
`sys.exit(1)`), weil sie vor dem Sync und in `--validate` laufen (§4.7).

### 4.1 `scripts/lib/topology.py` (neu)

```python
VALID_TOPOLOGIES: frozenset[str] = frozenset({"primary", "subagent", "hybrid"})
DEFAULT_MAX_INSTANCES: int = 1
VERIFIED_STATES: frozenset[str] = frozenset(
    {"VERIFIED-RUNTIME", "DOCUMENTED", "UNVERIFIED"}
)

@dataclass(frozen=True)
class TopologyResolution:
    declared: str | None       # Roh-Wert oder None (Key ungesetzt)
    effective: str             # "primary" | "subagent" | "hybrid"
    source: str                # "provider-override" | "project" | "derived"
    derived_from: str | None   # z.B. "providers.Opencode.primary-role"
    degraded_from: str | None  # gesetzt, wenn declared != effective
    degradation_reason: str | None
    verification_state: str    # Zelle aus topology_verified_state

def resolve_topology(
    config: dict,
    provider: str,
    *,
    provider_config: dict,
    capabilities: dict,
    mode: str,                 # bereits durch _resolve_orch_mode aufgelöst
    validate: bool = True,
) -> TopologyResolution:
    """Deklariert -> effektiv -> unterstützt/degradiert, für genau einen Provider.

    Präzedenz: provider-overrides.<P>.topology > orchestrator.topology >
    Ableitung aus providers.<P>.primary-role.

    `mode` kommt als Parameter herein (A2): topology.py importiert variables.py
    NICHT (Blattmodul) und baut keinen zweiten Mode-Resolver.

    Konservative Auflösung (B1): Ist die Zielzelle in
    `capabilities.<P>.topology_verified_state` = UNVERIFIED, wird der
    konservative Fallback aus `topology_degrade` zurückgegeben, NIEMALS der
    deklarierte Wert. Das Ergebnis trägt degraded_from +
    degradation_reason = "capability cell UNVERIFIED".

    `validate=False` liefert den normalisierten String ohne zu werfen
    (Konsistenz-Checker).
    Raises: SyncError bei unbekanntem Enum-Wert.
    """

def topology_explicit(config: dict, provider: str | None = None) -> bool:
    """True, wenn der Key in dem für *provider* wirksamen Scope explizit steht.

    provider=None => nur Projekt-Scope (der provider-lose Builder-Vertrag, §4.3).
    """

def resolve_orchestrator_instances(
    config: dict, provider: str, topology: TopologyResolution, *,
    capabilities: dict, validate: bool = True,
) -> tuple[int, str | None]:
    """(max_instances, warning_reason|None).

    N>1 wird nur gewährt, wenn `orchestrator_instances.multiple` true UND die
    Zelle `topology_verified_state.multiple` nicht UNVERIFIED ist; sonst
    effektiv 1 + warning_reason (Cross-Scope-Fall, D3 (4)).

    Raises: SyncError bei `singleton`-Widerspruch oder `topology: primary`
    mit max_instances > 1 im SELBEN Scope (D5).
    """

def compose_instance_session_id(base_session_id: str, instance_id: str | None) -> str:
    """`base` bei None; sonst `f"{base}__{instance_id}"` (D6).

    Raises: ValueError, wenn die Komposition validate_session_id() verletzt.
    """
```

**Daten-Eigentum:** `topology.py` besitzt *nur* die Auflösung; es schreibt
nichts, kennt keinen Pfad und keinen Provider-Namen. Es liest die
Capability-Daten und `providers.py`; `mode` wird ihm übergeben (A2).

**Capability-Struktur (P0, je registriertem Provider):**

```yaml
topology_support:  {primary: bool, subagent: bool, hybrid: bool}
topology_degrade:  {primary: "subagent"|null, subagent: "sequential-text"|null,
                    hybrid: "subagent"}   # v1: immer "subagent" (fail-safe, Minor 4)
orchestrator_instances: {multiple: bool, reason: str|null}
topology_verified_state: {primary: str, subagent: str, hybrid: str, multiple: str}
```

`topology_verified_state` ist das Muster von `surface_verified_state`
(`config/known-issues.yaml` kennt die Ableitung bereits) und verhindert, dass
„Annahme" als „Daten" gelesen wird. **Invariante:** jeder registrierte Provider
trägt alle vier Strukturen (AC-15), und `topology_support.* == true` impliziert
`topology_verified_state.* != UNVERIFIED`.

### 4.2 `scripts/lib/active_set.py` (geändert)

```python
def role_emitted_for_provider(
    role: str,
    provider: str,
    config: dict,
    *,
    active_set: "ActiveSet | None" = None,
    provider_config: dict | None = None,
    capabilities: dict | None = None,
    mode: str | None = None,
) -> bool:
    """Einzige Quelle für 'wird diese Rolle für diesen Provider erzeugt?'.

    Drei boolesche Konjunkte — kein Pseudo-Topologie-Wert (Minor 1):
      1. Rolle im ActiveSet,
      2. Provider aktiv,
      3. `not _role_suppressed_by_mode(role, mode)`, wobei das Prädikat
         genau dann True liefert, wenn `mode == "main-chat"` UND
         `role == "orchestrator"` ist.

    `mode` ist der bereits durch `_resolve_orch_mode` aufgelöste String
    ("strict" | "advisory" | "main-chat"); `None` heißt: intern über
    `_resolve_orch_mode(config, provider_override)` bestimmen. "main-chat" ist
    **kein** Wert von `VALID_TOPOLOGIES` und keine Topologie; es wird deshalb
    nie als Topologie-Vergleich formuliert, sondern als eigenes boolesches
    Prädikat. Der ActiveSet-Konjunkt der heutigen `_opencode_entry_point`
    bleibt Bestandteil (A5, S5).
    """
```

`agent_sync._should_skip_role` (S8) und `isolation._opencode_entry_point` (S5)
müssen **dasselbe** Prädikat konsumieren. Der bestehende
`ORCH_MODE_MAIN_CHAT`-String-Vergleich bleibt als deprecated Alias bestehen,
aber nicht als zweite Wahrheit. **Phasenschnitt:** die Funktion entsteht in P1
mit Unit-Tests; die Call-Site-Umstellung ist P2 (A8).

### 4.3 `scripts/lib/variables.py` (geändert)

**P1 — Topologie-Flags**, Analogon zu `_orch_mode_flags()` (S6), exakt eines wahr:

```python
def _topology_flags(topology: str, *, explicit: bool, source: str) -> dict[str, str]:
    # ORCH_TOPOLOGY_PRIMARY / _SUBAGENT / _HYBRID : "true"|"false"
    # ORCH_TOPOLOGY                               : "primary"|"subagent"|"hybrid"
    # ORCH_TOPOLOGY_EXPLICIT                      : "true"|"false"
    # ORCH_TOPOLOGY_SOURCE                        : "provider-override"|"project"|"derived"
```

**P3 — Instanz-Flags** (eigenes Zuhause, Minor 2/M3 — **nicht** in P1):

```python
def _instance_flags(max_instances: int, *, singleton_declared: bool) -> dict[str, str]:
    # ORCH_MAX_INSTANCES       : "1".."8"
    # ORCH_SINGLETON_DECLARED  : "true"|"false"   (presence-only Key)
```

`ORCH_SINGLETON_DECLARED` sagt **nur**, ob der presence-only Key gesetzt ist —
nicht, ob der Zustand effektiv singleton ist. Der effektive Zustand folgt aus
`ORCH_MAX_INSTANCES == "1"` und wird **nicht** als eigene Variable emittiert;
sonst wäre „Key unset + `max-instances: 1`" als `"false"` lesbar, obwohl der
Lauf effektiv singleton ist.

**Global-Vertrag (A3):** `config.py::_build_variables` baut die Flags
provider-**los**. Deshalb gilt:

| Flag | provider-loser Wert | Phase |
|---|---|---|
| `ORCH_TOPOLOGY` | Projekt-Scope-Wert, sonst `""` (nie ein abgeleiteter Provider-Wert) | P1 |
| `ORCH_TOPOLOGY_EXPLICIT` | `"true"` **nur** wenn `orchestrator.topology` im Projekt-Scope steht; Provider-Override zählt hier **nicht** | P1 |
| `ORCH_TOPOLOGY_PRIMARY/_SUBAGENT/_HYBRID` | genau eines `"true"`, sonst alle `"false"` (wenn `ORCH_TOPOLOGY == ""`) | P1 |
| `ORCH_MAX_INSTANCES` | existiert vor P3 **nicht**; ab P3 Projekt-Scope-Wert, Default `"1"` | P3 |
| `ORCH_SINGLETON_DECLARED` | existiert vor P3 **nicht**; ab P3 `"true"` nur bei presence-only Key, sonst `"false"` | P3 |

Jede provider-skopierte Rendering-Stelle (`context.py::_build_context_vars`,
`rules.py::_merged_rule_vars`, `provider_transform.py`) **muss** mit
`provider=...` re-resolven und die globalen Werte überschreiben — exakt wie
`REPO_CONTAINMENT_*` (S7). `rules.py::_merged_rule_vars` unterstützt
`variables=None` ausdrücklich (S23) und baut die Flags selbst; der
Topologie-Zweig muss dort genauso stehen wie `_orch_mode_flags`, sonst rendert
ein Direktaufrufer die Flags nicht. Das ist fail-closed, weil der else-Zweig
der byte-identische Default ist (AC-6). Ein Template, das `ORCH_TOPOLOGY_*`
nutzt, darf nur über einen provider-skopierten Pfad gerendert werden; ein
Consistency-Check (§4.4) meldet ein provider-loses Rendering als WARNING.

**Conditional-Registrierung (B4, Teil des Contracts):** Zwei **getrennte**
Registrierungen sind nötig; fehlt eine, rendert der heutige Mechanismus
**beide** Zweige bzw. den **falschen**:

1. **Whitelist** in `scripts/lib/variables.py::strip_inactive_conditional_blocks`
   — das Set `conditional_vars` wird *innerhalb* der Funktion aus `variables`
   gebaut (Z. 431–451). Präfix `ORCH_TOPOLOGY_` ergänzen. Ein nicht gelistetes
   `{{#if}}` wird nicht gestrippt und behält beide Zweige.
2. **Fail-closed-Default** in `scripts/lib/variables.py::_FALSE_DEFAULT_CONDITIONALS`
   (Z. 52) — `ORCH_TOPOLOGY_EXPLICIT`, `ORCH_TOPOLOGY_PRIMARY`,
   `ORCH_TOPOLOGY_SUBAGENT`, `ORCH_TOPOLOGY_HYBRID` eintragen. **Grund:**
   `_conditional_active` liest eine abwesende Variable als `"true"`
   (`default = "false" if var in _FALSE_DEFAULT_CONDITIONALS else "true"`).
   Ohne diesen Eintrag würde **jeder** Render-Pfad, der
   `ORCH_TOPOLOGY_EXPLICIT` nicht setzt, den **neuen** expliziten Zweig
   rendern statt der heutigen Bytes — exakt der Grund, aus dem
   `GATE_NEUTRAL`/`CONTEXT_PROFILE_COMPACT` dort stehen. Diese Registrierung
   ist **P1-Pflicht**, nicht P4.
3. `scripts/lib/standalone.py::_CONDITIONAL_FALSE_FLAGS` — literale `"false"`-
   Einträge für dieselben vier Flags; zusätzlich Fallback `ORCH_TOPOLOGY: ""`.
   (`ORCH_MAX_INSTANCES`/`ORCH_SINGLETON_DECLARED` folgen erst in P3.)
4. `scripts/lib/consistency/placeholders.py::_BUILTIN_VARS` — alle neuen
   Builder-Variablen registrieren (der Ratchet ist shrink-only; „New builder
   variables must be registered, not added here").
5. `CLAUDE.md`/`AGENTS.md`-Variablentabelle (Doku, P4).

**Kritisch:** diese Variablen dürfen in **bestehenden** Templates nur in
`{{#if ORCH_TOPOLOGY_EXPLICIT}}`-Zweigen benutzt werden (§10, §12 AC-6).

### 4.4 `scripts/lib/consistency/topology.py` (neu)

| Check-ID | Severity | Bedingung |
|---|---|---|
| `orchestrator-topology.degraded` | WARNING | `resolution.degraded_from is not None` (Provider kann den deklarierten Wert nicht ausdrücken **oder** Zelle ist `UNVERIFIED`) |
| `orchestrator-topology.hybrid-unverified` | WARNING | Deklaration `hybrid` und `topology_verified_state.hybrid == "UNVERIFIED"` (v1: immer) |
| `orchestrator-topology.main-chat-supersedes` | WARNING | Cross-Scope: Provider-Override `mode: main-chat` bei global/übergeordnet gesetzter Topologie (§4.7 (2)) |
| `orchestrator-topology.instances-clamped` | WARNING | `max-instances > 1`, aber `orchestrator_instances.multiple == false` **oder** Cross-Scope `topology: primary` + globales N>1 (D3 (4)) |
| `orchestrator-topology.derived` | INFO | Topologie ist abgeleitet (nur wenn OQ-4 „INFO" gewählt wird) |
| `orchestrator-topology.unresolved-global-flags` | WARNING | Ein `ORCH_TOPOLOGY_*`-Platzhalter wurde provider-los gerendert (A3) |

Signatur (Muster: `consistency/orchestrator_strict.py`):

```python
def check_orchestrator_topology(
    agent_meta_root: Path, project_config: dict
) -> list[Finding]: ...
```

### 4.5 `scripts/lib/provider_transform.py` (geändert)

Die Ableitung in `_apply_agent_transform` (S1) wird von
`explicit_primary_role(...)` auf `resolve_topology(...).effective` umgestellt:

| effektive Topologie | opencode-native v1 | opencode-native v2 |
|---|---|---|
| `primary` (Rolle == entry role) | `mode: primary` | `mode: primary` |
| `subagent` | `mode` **nicht** geschrieben (heutiges v1-Verhalten für Nicht-Primary) | `mode: subagent` |
| `hybrid` | wie `primary` (v1 nie gewährt, immer WARNING + Fallback) | wie `primary` |

Die Template-Fallbacks (`mode or template_fm["mode"]`) und der Write-Scope-Lock
(„primary ⇒ edit-deny") bleiben an `mode == 'primary'` gebunden — **keine**
zweite Bedingung.

**Ein Lesezugriff (A4, S2):** Die Subagent-Allowlist in
`_apply_agent_transform` liest heute `.get('primary-role', 'orchestrator')`
direkt. In P1 entsteht `providers.primary_role(provider_config, provider, *,
default: str | None = None)` als **einziger** Lesezugriff; beide Aufrufer
werden migriert:

- `context.py::apply_settings_surface_shape` → `default=None` (kein Code-Default,
  #1006/IC-1),
- `provider_transform.py::_apply_agent_transform` → `default="orchestrator"`,
  um die heutigen Allowlist-Bytes zu erhalten (der Code-Default ist hier
  bewusst Teil des Ist-Verhaltens und wird nicht stillschweigend entfernt).

„Ein Lesezugriff" ist damit das **Ziel** von R1, nicht die Behauptung über den
Ist-Zustand.

### 4.6 `scripts/lib/isolation.py` + `context.py` (geändert)

`_opencode_entry_point` liefert `None`, sobald die effektive Topologie
`subagent` ist (auch wenn `primary-role` deklariert ist). Damit greift
automatisch die bestehende D1a-Invariante (S4): kein `default_agent` ⇒ kein
Deny, Gate wird laut suspendiert. **Der ActiveSet-Konjunkt bleibt unverändert
erhalten (A5, S5):**

```python
role = providers.primary_role(provider_config, provider, default=None)
if role is None:
    return None
if active_set is not None and role not in active_set.roles:
    return None
if resolve_topology(..., mode=mode).effective != "primary":
    return None
return role
```

Damit erhält ein Projekt mit deaktivierter Orchestrator-Rolle **keinen** neuen
`default_agent`; der ungesetzte Key bleibt byte-identisch. Zusätzlich entsteht
ein WARNING, wenn `topology: subagent` den Entry Point entfernt und der
Runtime-Gate dadurch inaktiv wird (§8 Regel 3, R2).

**Zweiter Schreiber (B2, S21):** `context.py::apply_settings_surface_shape`
schreibt heute unbedingt `default_agent` aus `primary-role` für
`opencode-json-v2`. Der P2-Contract lautet:

```python
def apply_settings_surface_shape(
    content: str,
    pc: dict,
    capabilities: dict | None = None,
    *,
    topology_effective: str | None = None,
) -> str:
    """... unverändert für jedes Nicht-v2-Format ...

    topology_effective ist die *aufgelöste effektive* Topologie für diesen
    Provider (nicht der Roh-Flag-Wert!). None = Legacy-Aufrufer, heutiges
    Verhalten (byte-identisch).

    Ist topology_effective != "primary": `document.pop("default_agent", None)`
    und KEIN Schreiben. Ist topology_effective == "primary": heutiges Verhalten.
    """
```

Der Aufrufer `_init_provider_settings_json` erhält die `TopologyResolution`
aus dem Per-Provider-Loop (der `config`, `provider_config`, `capabilities` und
`mode` besitzt) und reicht `topology.effective` durch. Wichtig: **nicht**
`variables["ORCH_TOPOLOGY"]` durchreichen — der globale Wert ist bei
ungesetztem Key `""`, während die effektive Topologie für Opencode `primary`
ist (sonst würde der Default-Pfad brechen).

**Migrationsregel (B2):**

| Fall | Verhalten |
|---|---|
| Frisches v2-Projekt, effektive Topologie ≠ `primary` | Datei wird ohne `default_agent` angelegt; **kein** WARNING (gewünschter Zustand, AC-14) |
| Bestehender Wert **verwaltet** (`default-agent`-State-Record vorhanden) | `_merge_default_agent` rollt beim Wechsel `primary → subagent` zurück (bereits vorhanden, `desired=None` + State-Record) |
| Bestehender Wert **nutzereigen** (kein State-Record) und Topologie ≠ `primary` | **WARN** `orchestrator-topology.default-agent-conflict` mit Handlungssatz („entferne `default_agent` oder setze `topology: primary`"); **kein Auto-Delete** — konsistent zu D1c/D16. Der Legacy-Init-Wert fällt in diese Klasse (nicht unterscheidbar), die Einschränkung ist dokumentiert |
| `topology: primary` | heutiges Verhalten unverändert |

### 4.7 `scripts/lib/config.py` (geändert, harter stdlib-Check)

Neue Funktion, aufgerufen aus `_validate_config` **nach** `_validate_providers`
(S22-Muster):

```python
def _validate_orchestrator_topology(config: dict, config_path: Path) -> None:
    """Harte Same-Scope-Widersprüche; stdlib-only, kein jsonschema.

    Muster: _validate_providers — stderr 'ERROR: <pfad>: ...', dann sys.exit(1).
    Läuft in `sync` UND `--validate` (load_config -> _validate_config).

    Geprüft (jeweils SELBER Scope):
    P1:
    (a) topology-Enum unbekannt.
    (b) topology explizit UND (mode == 'main-chat' ODER enabled == false).
    (c) provider-overrides.<P>.{topology, mode/enabled} — auch der
        Same-Object-Fall mode: main-chat + topology: primary (A6).
    P3-only (erst mit dem Key `max-instances`, M3):
    (d) `singleton` presence-only: max-instances > 1 => ERROR;
        max-instances == 1 => INFO (redundant); `singleton: false` => ERROR
        mit Hint "use max-instances".
    (e) topology == 'primary' UND max-instances > 1 => ERROR.
    """
```

**Meldungsvertrag (Minor 3):** Jede Meldung beginnt mit
`ERROR: <config-path>: ` (Muster `_validate_providers`) und enthält genau
einen der folgenden **stabilen Teilstrings**. AC-17 assertet den Teilstring,
nicht die Satzform; damit ist die Meldung testbar, ohne den Fließtext
einzufrieren.

| Regel | stabiler Teilstring | Phase |
|---|---|---|
| (b) mode | `orchestrator.topology conflicts with orchestrator.mode: main-chat` | P1 |
| (b) enabled | `orchestrator.topology conflicts with orchestrator.enabled: false` | P1 |
| (c) override | `provider-overrides.<P>.topology conflicts with provider-overrides.<P>.mode: main-chat` | P1 |
| (d) singleton × N | `orchestrator.singleton conflicts with orchestrator.max-instances` | P3 |
| (d) singleton false | `orchestrator.singleton: false is not supported (use max-instances)` | P3 |
| (e) primary × N | `orchestrator.topology: primary conflicts with orchestrator.max-instances` | P3 |

`<P>` wird durch den tatsächlichen Provider-Namen ersetzt; `<config-path>` ist
der übergebene Pfad. Der Handler bleibt `sys.exit(1)` (R11).

**Cross-Scope** wird hier absichtlich **nicht** abgelehnt: das ist die
Dominanz-/Clamp-Regel aus D3 (2)/(4) und bleibt WARNING im
Konsistenz-Report. Das Schema-`if/then` bleibt bestehen, wird aber nur noch
als Dokumentations-/Editor-Hilfe beschrieben (`description`, IDE-Hinweis) —
**nicht** als Enforcement.

---

## 5. Datenfluss

```
project.yaml                      ai-providers.yaml          provider-capabilities.yaml
orchestrator.topology  ---------+ providers.<P>.primary-role   topology_support
orchestrator.provider-  |        |                             topology_degrade
  overrides.<P>.topology|        |                             orchestrator_instances
orchestrator.max-       |        |                             topology_verified_state
  instances (P3)        |        |                                        |
                         v        v                                        v
                   [C2 topology.resolve_topology(mode=...)]  <------------+
                         |
      +------------------+-------------------+--------------------+
      v                  v                   v                    v
 ORCH_TOPOLOGY_*   C5a provider_transform  C5b isolation      C6 Konsistenz
 (+ EXPLICIT)           (mode: primary|sub)   (_opencode_entry)   (WARNING/INFO)
      |                  |                   |                    |
      v                  v                   v                    v
  Templates (nur   .opencode/agents/    opencode.json        sync-Report / --check
  bei EXPLICIT)    orchestrator.md      default_agent
      |
      v
 [C8 _validate_orchestrator_topology]  (vor jedem Schreiben; hart)
```

**Zustands-Eigentum bei N>1 (C7):**

| Artefakt | Eigentümer | Namespace / Konsument |
|---|---|---|
| `<checkpoint-dir>/<session>.json` | je Instanz | Session-ID = `<base>__<orchestrator-id>` (§9.3); Konsument: `recovery.py`/`CheckpointStore` |
| `<progress-dir>/current.md` | **nur** die Wurzel-Session | unverändert; einziger maschinell gelesener Fortschritt (`CheckpointStore._write_progress_file`) |
| `<progress-dir>/progress-<orchestrator-id>.md` | je Instanz | **rein menschlich lesbar**; kein Code-Konsument (A10, S13/S14). Die Identität ist dieselbe normalisierte `orchestrator_id` wie im Checkpoint-Suffix |
| `.meta-viz/events.jsonl` | gemeinsam (append) | **Feld** `orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at` in jedem Event, **keine** Datei-Shards |
| Delegations-Tracker | je Instanz | nur im Kontext (S16) — kollidiert nicht |
| `.opencode/agents/orchestrator.md` | Framework (eine Datei) | Instanz-Identität ist **kein** Dateiname |

Begründung „Feld statt Datei" für das Event-Log: der Konsument
(`viz-report.py`, Admin-UI) liest genau eine Datei (S15); Sharding würde jeden
Konsumenten brechen und den vorhandenen Byte-Identitäts-Pfad verlassen.

---

## 6. Entscheidungen (D1–D10)

Format je Entscheidung: Kontext → Wahl → Alternativen → Konsequenzen →
**Veto-Konsequenz** (was gilt, wenn die Empfehlung verworfen wird).

### D1 — Naming und Enum

```
DECISION
context: Eine Konfigurationsfläche für "wo lebt der Orchestrator" existiert nicht;
         der Begriff "topology" ist im Repo bereits für Dateilayout belegt
         (context_file.topology) und muss abgegrenzt werden.
choice:     `orchestrator.topology` mit enum `primary | subagent | hybrid`.
            Semantik:
              primary  = Die Rolle IST der Session-Einstieg. Ein Orchestrator pro
                         Session; kein Spawn-Kanal (max-instances ist dann 1).
              subagent = Die Rolle ist NIE Einstieg; der Main Chat besitzt den
                         Session-Kontext und spawnt 1..max-instances Instanzen.
              hybrid   = Die Rolle ist positions-agnostisch (entweder/oder):
                         dieselbe Rolle darf als Einstieg ODER als gespawnter
                         Subagent auftreten (Deviation zu #1077 §2, §1).
alternatives:
  - `orchestrator.position` / `.placement` / `.agent-kind` — semantisch enger,
    kollidiert nicht mit context_file.topology, bricht aber die Issue-Terminologie
    und den Titel (#1077) und damit die Auffindbarkeit.
  - `orchestrator.primary: bool` — binär; kann `hybrid` und die
    Multi-Instanz-Achse nicht ausdrücken (Issue-Kommentar §1 trennt beide Achsen).
  - Key unter `providers.<P>` — falsche Ebene: es ist eine Projektentscheidung,
    nicht eine Provider-Eigenschaft (Provider-Eigenschaft ist die *Fähigkeit*,
    nicht die *Wahl*).
consequences:
  + Ein Schlüssel, ein Enum, direkt zitierbar in Doku/Rule/Fehlermeldung.
  + Deckt sich mit dem Vokabular von `provider-capabilities.yaml`.
  - Zwei "topology"-Begriffe im Repo; die Schema-`description` MUSS
    "Dateilayout, nicht Agent-Topologie" für context_file.topology sagen.
```

**Veto-Konsequenz:** Fällt der Name, ist `orchestrator.position` die
Rückfalloption; dann müssen Issue, Concept-Doc, Spec und der Trace-Anchor
gemeinsam umbenannt werden, und die Abgrenzung zu `context_file.topology`
entfällt (Vorteil), während die Issue-Rückverfolgbarkeit leidet (Nachteil).

### D2 — Bedeutung von `hybrid`

```
DECISION
context: Zwei Lesarten sind möglich: (a) eine Rolle, die in beiden Positionen
         erscheinen kann; (b) ein Primary plus zusätzliche Instanzen für
         abgegrenzte Parallelarbeit. Die Wahl ändert das Adressierungsmodell.
         #1077 §2 formuliert (b) ("primary and can additionally be spawned");
         dieses Design wählt bewusst (a) und dokumentiert die Deviation (§1).
choice:     (a) EINE positions-agnostische Rolle. `hybrid` beschreibt
            Positions-Fähigkeit, NICHT Anzahl. Anzahl ist ausschließlich
            `max-instances` (D5). Die realisierte Positionsmenge ist
            provider-bestimmt und wird als WARNING gemeldet, wenn sie schrumpft.
            In v1 wird `hybrid` auf KEINEM Provider gewährt: die Zelle ist
            überall UNVERIFIED, die effektive Topologie ist der konservative
            Fallback (B1). Der Enum-Wert ist damit ein *akzeptierter, laut
            degradierter* Vorwärts-Wert.
alternatives:
  - (b) zweiklassige Instanzen (primary + scoped): verlangt einen
    `kind`-Diskriminator in der Identität (`orchestrator#primary` vs
    `orchestrator#scoped`), zwei Checkpoint-Namespaces, zwei Gate-Stärken und
    eine zweite Adressierungsregel im A2A-Gate. Auf Opencode degradiert (b)
    ohnehin zu (a), weil ein `mode: primary`-Agent nicht per `task` spawnbar ist
    (#1006; Umkehrung unverifiziert, §16 Nr. 2).
  - `hybrid` streichen: dann bleibt "Opencode primary + Claude subagent" nur
    per Provider-Override ausdrückbar (D4) — das ist genau der heutige Zustand
    plus Konfiguration; der Enum-Wert aus dem Issue fehlt.
consequences:
  + Ein Identitätsmodell für alle Topologien (§9): Rolle = `orchestrator`,
    Instanz = Suffix. Kein zweiter Namensraum.
  + `hybrid` ist im Schema akzeptiert, aber v1 verspricht keine zwei
    gleichzeitigen Positionen; die Degradierung ist laut und testbar.
  - Die Issue-Tabelle liest sich anders; die Deviation muss in §1 und im
    Concept-Doc stehen (A1).
```

**Veto-Konsequenz:** Wird (b) gewählt, muss §9 neu abgeleitet werden
(`kind` im Identitäts-Schema, zwei Namespaces in §5, Gate-Regel mit
Klassen-Unterscheidung) und D6 gilt als nicht mehr gültig; der Aufwand wandert
von P3 nach P1 (Adressierung ist dann nicht mehr nachrüstbar).

### D3 — `main-chat` × Topologie und `primary` × N: Same-Scope = harter ERROR, Cross-Scope = WARNING

```
DECISION
context: `mode: main-chat` entfernt den Orchestrator vollständig (S8); eine
         gesetzte Topologie wäre dann gegenstandslos. Zwei Aussagen können sich
         widersprechen: im SELBEN Scope (beide Keys in derselben Ebene) oder
         über Scopes hinweg (global gesetzt, per Provider auf main-chat
         genarrowt). Zusätzlich: `topology: primary` + N>1 ist nur im selben
         Scope prüfbar.
choice:     Zwei Regeln, ein Prinzip — "expliziter Selbstwiderspruch ist ein
            Fehler, eine bewusste Scope-Verengung ist eine dokumentierte
            Dominanz mit Warnung":
            (1) SELBER Scope: `topology` explizit UND (`mode: main-chat` ODER
                `enabled: false`) in derselben Ebene  =>  HARTE Ablehnung
                durch `_validate_orchestrator_topology` (stdlib, §4.7),
                rc≠0 in `sync` UND `--validate`, kein Sync. Gilt für
                `orchestrator.*` UND `orchestrator.provider-overrides.<P>.*`,
                inklusive des Same-Object-Falls
                `{mode: main-chat, topology: primary}` (A6).
                Gleiches Prinzip für `topology: primary` + `max-instances > 1`
                im selben Scope.
                Das JSON-Schema-`if/then` bleibt als Editor-Hilfe, ist aber
                KEIN Fehlerkanal (S22).
            (2) CROSS-Scope: Provider-Override `mode: main-chat` bei global
                gesetzter Topologie  =>  `main-chat` gewinnt, Topologie ist für
                diesen Provider inert, Sync-WARNING
                `orchestrator-topology.main-chat-supersedes` (nennt Provider,
                globalen Wert und den Grund).
            (3) Abgeleiteter main-chat (nur `enabled:false`-Legacy, kein
                explizites `mode`) + explizite Topologie im selben Scope
                =>  wie (1).
            (4) CROSS-Scope `provider-overrides.<P>.topology: primary` bei
                globalem `max-instances > 1`  =>  WARNING
                `orchestrator-topology.instances-clamped`; effektiv N=1 für
                diesen Provider. Kein ERROR (der globale Wert ist nicht
                selbstwidersprüchlich).
alternatives:
  - ERROR in beiden Fällen: bricht den legitimen Fall "Claude im main-chat,
    Opencode strict" (der Per-Provider-Narrowing-Pfad existiert bewusst, S7) —
    der Nutzer müsste den globalen Key löschen und pro Provider duplizieren.
  - WARNING in beiden Fällen (Präzedenz überall): verwirft eine explizite
    Nutzeraussage im selben Scope; genau das nennt das Issue unacceptable.
  - Topologie bei main-chat "mitrendern" (toter Text): erzeugt eine Aussage
    über einen Agenten, der nicht existiert — schlimmste Variante.
  - Auf Schema-`if/then` als Fehlerkanal bauen: existiert in diesem Repo nicht
    (S22) — würde eine Durchsetzung behaupten, die nicht stattfindet.
consequences:
  + Selbstwiderspruch bricht früh und mit Pfad-Angabe (der Validator nennt
    `orchestrator.topology` / den Override-Pfad).
  + Der einzige legitime Mischfall bleibt möglich und ist trotzdem laut.
  + Der wahrscheinlichste Tippfehler (Same-Object) ist ein Fehler, kein
    WARNING (A6).
  - Zwei Fehlerkanäle (Validator vs. Sync-WARNING) für ein Thema; muss in der
    Doku zusammen erklärt werden.
```

**Veto-Konsequenz:** Fällt (1), gilt überall (2) mit WARNING; dann ist die
Byte-Identität einfacher (kein Validator), aber ein Tippfehler-Paar
(`mode: main-chat` + `topology: primary`) sync'd stillschweigend weiter. Fällt
(2), gilt überall (1); dann ist der Multi-Provider-Mischbetrieb nur noch über
das Weglassen des globalen Keys möglich — ein Rückschritt gegenüber heute.

### D4 — `mode` × `topology`: orthogonal, mit genau einer Dominanzzelle; Topologie ist per Provider überschreibbar

```
DECISION
context: `mode` beschreibt die Gate-Stärke/Existenz, `topology` die Position.
         `provider-overrides.<P>.mode` existiert bereits (S7/S10); die Frage ist,
         ob Topologie denselben Override-Kanal bekommt.
choice:     Zwei orthogonale Achsen in einem 3x3-Raster (§8). Genau EINE Zelle
            ist nicht orthogonal: `mode: main-chat` macht Topologie inert.
            Topologie ist per Provider überschreibbar:
            `orchestrator.provider-overrides.<P>.topology` (Schema erweitern,
            Per-Provider-Loop S7 um den Topologie-Zweig ergänzen).
            Präzedenz exakt wie `mode`: provider-override > project > derived.
alternatives:
  - Topologie NICHT per Provider überschreibbar (v1): dann kann ein
    Multi-Provider-Projekt "Opencode primary, Claude subagent" nur über den
    abgeleiteten Default ausdrücken; jede bewusste Abweichung erzeugt eine
    dauerhafte Degradierungs-Warnung, die der Nutzer nicht abstellen kann
    (Warnungs-Müdigkeit).
  - Topologie in `mode` einbetten (neue Enum-Werte `main-chat-primary` o.ä.):
    kombinatorische Explosion, bricht die bestehende Enum-Semantik und den
    Legacy-Migrationspfad von `enabled`/`strict`.
consequences:
  + Symmetrie: wer `mode` pro Provider versteht, versteht `topology` sofort.
  + Degradierung ist pro Provider auflösbar (Warnung abschaltbar durch die
    richtige Wahl, nicht durch Ignorieren).
  - Ein weiterer Override-Key; das Schema-Objekt `provider-overrides` muss von
    `additionalProperties: false` + nur `mode` auf zwei Properties erweitert
    werden (bewusste, getestete Schema-Änderung).
```

**Veto-Konsequenz:** Ohne Provider-Override bleibt (2) aus D3 die einzige
Lautstärke; der Nutzer kann eine Degradierung nur global beseitigen. Die
Empfehlung wäre dann, `topology` als „nur global" zu dokumentieren und die
Warnung als akzeptiert zu markieren (kein Stummschalt-Mechanismus) — das ist
die schlechtere UX und sollte bewusst entschieden werden.

### D5 — Multi-Instanz-Vertrag

```
DECISION
context: Der Issue-Kommentar fordert eine von der Enum unabhängige
         Multiplizitäts-Achse, mit hartem Konflikt statt stiller Präzedenz.
choice:
  - `orchestrator.max-instances`: integer, minimum 1, maximum 8 (OQ-3).
    **Einziges Zuhause: P3.** Der Key existiert vor P3 **nicht** — es gibt
    keinen Zwischenschritt mit `maximum: 1` (M3). Obergrenze der
    Orchestrator-Instanzen, die der Main Chat pro Session spawnen darf.
    Kanonischer Wert.
  - `orchestrator.singleton`: presence-only Alias (P3, gemeinsam mit
    `max-instances`), `enum: [true]`, **kein Schema-`default`** (B5).
    Abwesend = aus `max-instances` abgeleitet
    (`max-instances == 1` ⇒ effektiv singleton; `> 1` ⇒ nicht). Present +
    `max-instances > 1` => harter Validator-ERROR. Present + `max-instances: 1`
    => zulässig und redundant (Sync-INFO). `singleton: false` => Schema- und
    Validator-ERROR mit Hint "use max-instances". Da es keinen Default gibt,
    kann der Validator "explizit gesetzt" von "abgeleitet" unterscheiden.
  - Konflikt (harter Validator, kein Vorrang): `singleton` present UND
    `max-instances > 1`.
  - `topology: primary` UND `max-instances > 1` im selben Scope =>
    harter Validator-ERROR (primär = Session-Einstieg, kein Spawn-Kanal).
    Cross-Scope (Provider-Override primary, global N>1) => WARNING +
    effektiv N=1 (D3 (4)).
  - N>1 wird zusätzlich nur gewährt, wenn `orchestrator_instances.multiple`
    true und die Capability-Zelle nicht UNVERIFIED ist (D10/B1).
  - Abgrenzung zu `max-parallel-agents` (S11) wird in BEIDEN
    Schema-descriptions ausgesprochen: `max-parallel-agents` begrenzt die
    Parallelität INNERHALB eines Orchestrators, `max-instances` die ANZAHL der
    Orchestratoren. (Höchster Verwechslungsfaktor laut Issue-Kommentar.)
consequences:
  + Opt-in, Default byte-identisch (1 = heutiges Verhalten).
  + Kein stiller Vorrang: der Widerspruch ist ein Validierungsfehler.
  - Zwei Keys für eine Dimension (Alias); Legacy-Schuld, aber explizit im
    Kommentar gefordert. Der Alias hat bewusst keinen Default — sonst wäre
    jedes N>1 per Default im Konflikt (B5).
```

**Veto-Konsequenz:** Ohne `singleton`-Alias bleibt nur `max-instances`
(sauberer, aber der Kommentar-Zuschnitt entfällt). Ohne `max-instances` ist N>1
nicht ausdrückbar → der gesamte Kommentar-Slice (P3) entfällt und
`subagent`/`hybrid` bedeuten faktisch N=1; das Issue-Ziel „mehr als ein
Orchestrator" wäre verfehlt.

### D6 — Zustands-Isolation für N Instanzen

```
DECISION
context: Checkpoints sind eine Datei pro Session (S12), der Fortschritt ist EINE
         Datei (S13), das Event-Log ist EINE Datei (S15); der Tracker ist
         kontextlokal (S16). Bei N>1 kollidieren Checkpoint und Fortschritt.
choice:
  - Instanz-Identität ist ein STATEF-NAMESPACE, kein Rollenname:
    `orchestrator_id` = `[a-z0-9][a-z0-9._-]{0,39}`; kanonischer Default (N=1)
    = None. Dieselbe normalisierte ID wird für Checkpoint-Suffix UND
    Fortschrittsdatei verwendet (eine Ableitung, zwei Dateinamen).
  - Session-ID-Komposition: `compose_instance_session_id(base, id)` =
    `<base>` bei None, sonst `<base>__<id>` (Doppel-Unterstrich; überlebt
    `_sanitize_component` und `validate_session_id` auf allen Plattformen).
  - Checkpoint: `<checkpoint-dir>/<base>__<id>.json`. Kein neues Verzeichnis.
  - Fortschritt: Instanzen schreiben `<progress-dir>/progress-<id>.md`;
    `current.md` bleibt der Wurzel-Session vorbehalten. `progress-<id>.md` ist
    **rein menschlich lesbar** — es gibt keinen Code-Konsumenten (A10); wer
    maschinell liest, liest Checkpoints (`recovery.py`) bzw. `current.md`.
  - Event-Log: unverändert eine Datei; jedes Event trägt `orchestrator_id`,
    `scope_id`, `spawned_by`, `spawned_at` (Feld-Tagging, A7).
  - Migration: N=1 (Default) erzeugt exakt die heutigen Pfade; bestehende
    `<session>.json` und der Legacy-Glob `.meta-viz/checkpoint-*.json` (S14)
    bleiben unberührt lesbar. Kein Rename, kein Backfill. Rollback = Suffix
    entfällt beim nächsten Sync-Lauf von selbst.
consequences:
  + N>1 ist ohne neue Verzeichnisstruktur und ohne Konsumenten-Bruch möglich.
  + Der Byte-Identitäts-Pfad (N=1) ist beweisbar unverändert, weil die
    Kompositions-Funktion bei None nichts tut.
  - `current.md` ist bei N>1 nicht mehr "der" Fortschritt; die Doku muss sagen,
    wer aggregiert (Main Chat, §9.4), und dass `progress-<id>.md` nur für
    Menschen ist.
```

**Veto-Konsequenz:** Ohne Namespaces darf N>1 **nicht** freigeschaltet werden —
sonst überschreiben sich parallele Läufe die Checkpoints (stiller
Resume-Datenverlust). Dann entfällt P3 komplett und `max-instances` wird in
dieser Veto-Variante gar nicht erst eingeführt (kein `maximum: 1`-Zwischenstand).

### D7 — Singleton-Regel: Provinz statt Kardinalität

```
DECISION
context: Die Regel "NUR main_chat darf orchestrator spawnen, Worker nie" ist
         heute über "es gibt genau einen" begründet. Bei N>1 ist diese Begründung
         falsch; die Regel muss ohne Kardinalität beweisbar bleiben.
choice:     Drei Klauseln, alle mechanisch aus dem Envelope prüfbar:
            G1  Worker -> orchestrator: HARD REJECT, unbedingt, bei jedem N.
            G2  Nur `main_chat` spawnt Orchestratoren, höchstens
                `max-instances`, jede mit eindeutiger `orchestrator_id` und
                disjunktem Scope. Doppelte ID oder Scope-Überlappung = HARD
                ERROR beim Spawn (Main-Chat-Pflicht, §9.2).
            G3  orchestrator -> orchestrator: HARD REJECT (bleibt verboten).
            Beweis ohne Kardinalität: "Jede Instanz hat genau einen Spawner of
            record (main_chat); die Delegationskante orchestrator->orchestrator
            existiert nicht." Beides ist aus `source_agent`/`target_agent` bzw.
            dem Spawn-Report ableitbar.
            Audit (A7): `orchestrator_id`, `scope_id`, `spawned_by`,
            `spawned_at` reisen im Envelope/Event; der Guard schreibt die ID
            ins Audit-Log (§10).
alternatives:
  - Kommentar-Variante "orchestrator darf für disjunkten Scope spawnen": macht
    G3 bedingt und verlangt eine Scope-Registry (neues Zustandsartefakt) plus
    eine Laufzeitprüfung, die kein Provider liefert → Anti-Recursion wäre nicht
    mehr aus dem Envelope beweisbar, sondern nur behauptet.
  - "Es gibt genau einen" beibehalten: schließt `subagent`/`hybrid` mit N>1 aus
    und widerspricht dem Issue-Ziel.
consequences:
  + Beweis bleibt zweizeilig und gate-fähig (Envelope-Namen).
  + Kein neues State-Artefakt in v1.
  - Der im Kommentar skizzierte "disjunkte Scope"-Spawn ist in v1 nicht
    erlaubt; er wird als dokumentierte Erweiterung (P5, nicht Teil dieses
    Designs) geführt.
```

**Veto-Konsequenz:** Wird die Kommentar-Variante gewählt, braucht v1 eine
Scope-Registry (Datei + Lock + Konsistenz-Check) und G3 wird zu einer
Zwei-Bedingungs-Regel; der Anti-Recursion-Beweis verliert seine
Envelope-Basis und die Guard-Aussage wird noch schwächer (R3).

### D8 — Guard-Konsequenz

```
DECISION
context: `orchestrator-guard.sh` arbeitet mit einem selbstdeklarierten Sentinel
         (S17); Rollen-Identität ist von keinem Provider verifizierbar (#516).
choice:     Die Convention-Boundary-Rahmung bleibt. Keine instanz-aware
            Prüfung. Ergänzt wird ausschließlich AUDIT: der Sentinel darf
            optional eine Instanz-ID tragen (`#agent-meta:agent=orchestrator
            id=<id>`), der Guard parst sie, nutzt sie NIE für eine
            Autorisierungsentscheidung und schreibt sie in
            `.claude/hooks/.guard-audit.log`. Der "Bekannte Grenzen"-Text wird
            um den Satz ergänzt: Instanz-Scoping ist nicht durchgesetzt; die
            behauptete ID ist nachträglich auditierbar, nicht verifiziert.
alternatives:
  - Instanz-aware Check (Guard verweigert Schreibzugriff bei ID-Kollision):
    braucht eine harness-gelieferte Instanz-Identität; kein Provider liefert
    sie (#516-Logik, `agent_id` sagt nur "irgendein Subagent") → würde eine
    Durchsetzung behaupten, die nicht existiert.
  - Guard ganz absenten: verliert auch den Versehenschutz für die
    Main-Chat-Schreibblockade.
consequences:
  + Ehrlich: keine neue Sicherheitszusage, aber Nachvollziehbarkeit.
  + Kein Test-Umbau der Autorisierungspfade, nur ein zusätzlicher Parse-Zweig.
  - Der Sentinel-Grammatik-Zweig ist ein Hook-Change (Version + Tests).
```

**Veto-Konsequenz:** Ohne Audit-Feld bleibt der Guard unverändert; dann ist
eine Instanz-Überschreitung nach dem Lauf **nicht** nachvollziehbar, und der
Nutzer muss dem Prompt-Vertrag vollständig vertrauen (Dokumentation muss das
dann explizit sagen).

### D9 — Rückwärtskompatibilität und Builder-Default

```
DECISION
context: Kein Projekt darf durch das Upgrade sein Verhalten ändern (§5 AC "no
         behavior change for projects that do not set the key"). Gleichzeitig
         muss ein Projekt, das `topology: subagent` setzt, den Main Chat als
         Default behalten (Nutzer-Intent, B2).
choice:     Key ungesetzt  =>  Topologie wird exakt wie heute abgeleitet:
            `providers.<P>.primary-role == role` und Rolle im ActiveSet
            =>  `primary` (heute nur Opencode), sonst `subagent`.
            `hybrid` wird NIE abgeleitet (kein Provider deklariert es heute).
            Der abgeleitete Wert wird sichtbar gemacht über (a) eine
            Sync-Summary-Zeile pro Provider (`topology: primary (derived from
            providers.Opencode.primary-role)`) und (b) optional einen
            INFO-Finding (OQ-4).
            KEIN neues Rendering in bestehenden Templates, solange
            `ORCH_TOPOLOGY_EXPLICIT != "true"` (S20-Konsequenz).

            Key gesetzt (`topology: subagent`) => der Main-Chat-Default bleibt
            der Builder: `apply_settings_surface_shape` schreibt in einem
            frischen v2-Projekt KEIN `default_agent`; `_opencode_entry_point`
            liefert `None` (ActiveSet-Konjunkt bleibt, A5); der Runtime-Gate
            wird laut suspendiert (S4/R2).
alternatives:
  - Default `subagent` überall: würde Opencode vom Default-Agent-Einstieg
    entfernen = Verhaltensbruch; verboten.
  - Default `primary` überall: würde Provider ohne Einstiegs-Konzept in einen
    nicht existierenden Zustand zwingen.
  - `default_agent` bei `topology: subagent` stehen lassen (Ist-Zustand):
    zeigt auf eine `mode: subagent`-Datei — genau der Zustand, den der
    Nutzer-Intent ausschließt (B2).
consequences:
  + `sync --check` bleibt auf unveränderten Consumer-Projekten byte-identisch
    (kein Template-Delta, keine Pfad-Änderung, kein Schema-Effekt).
  + Die Ableitung ist erklärbar, nicht magisch.
  - Zwei Quellen für "primary" (Registry-Daten + abgeleiteter Default); die
    Doku muss sagen, dass `topology: primary` auf Opencode dasselbe bewirkt wie
    das Weglassen des Keys.
  - Bestehende v2-Projekte mit nutzereigenem `default_agent` erhalten nur ein
    WARNING, kein Auto-Delete (D1c/D16).
```

**Veto-Konsequenz:** Wird der Default anders gewählt, ist die Kern-AC des
Issues („kein Silent-Topology-Change") verletzt; dann müsste jede Änderung
hinter einem Migrations-Switch mit Grace-Window laufen (Muster
`_STRICT_DEFAULT_GRACE_UNTIL`) — deutlich teurer und in v1 nicht empfohlen.

### D10 — Provider × Capability-Matrix: konservativ, datenabgeleitet, mit Verified-State

```
DECISION
context: Das Issue macht die Matrix zur Freigabe-Vorbedingung: nicht auf einem
         Provider versprechen, was er nicht kann; Degradierung laut. Rev. 1
         behauptete 13 Zellen und verschob die Evidenz in ein P0 nach der
         Freigabe — genau die Reihenfolge, die #1077 §3 verbietet (B1).
choice:     (a) Die Matrix (§7) wird aus den VORHANDENEN Capability-Keys
                abgeleitet (`main_agent_selectable`, `subagent_dispatch`,
                `parallel_execution`), nicht aus Provider-Namen.
            (b) Neue Strukturen je Provider: `topology_support`,
                `topology_degrade`, `orchestrator_instances` UND
                `topology_verified_state` (Muster `surface_verified_state`).
            (c) Konservative Regel: `UNVERIFIED ⇒ no`. `hybrid` wird in v1
                auf keinem Provider gewährt (`topology_support.hybrid: false`,
                `topology_degrade.hybrid: "subagent"` — **fail-safe**, Minor 4);
                die effektive Topologie ist der Fallback, nie der deklarierte
                Wert. „Providers eigene Position" ist bewusst verworfen: sie
                ergäbe auf Claude/Opencode/Continue/Kimi `primary` und damit
                `default_agent: orchestrator` — genau der Zustand, den §1
                ausschließt. Damit hängt die Spec nicht an einer unbelegten
                Annahme.
            (d) Zell-Upgrades (z. B. `hybrid: true`) sind ausdrücklich
                NACH v1 und brauchen eine Evidenzzeile in §3.1 + einen
                `verified_state`-Wechsel; sie sind kein Bestandteil der
                Freigabe dieses Designs.
            (e) Jede Degradierung erzeugt (a) einen Sync-WARNING
                `orchestrator-topology.degraded` mit Provider, deklariertem und
                effektivem Wert und (b) einen Matrix-Eintrag in der
                Concept-Doc. `--check` bleibt rc 0 (WARNING, nicht ERROR).
alternatives:
  - P0 als Pre-Approval-Gate (Spike vor der Spec): ehrlich, aber blockiert die
    Spec an 9 Providern × 3 Strukturen plus drei Hybrid-Zellen; der Nutzen
    (Enum + Konfigurationsfläche) ist unabhängig davon erreichbar.
  - Matrix als reine Doku-Tabelle: driftet beim nächsten Provider-Upgrade
    auseinander (genau das Muster, das `commands: false` vor #807 erzeugte).
  - Degradierung still (nur Doku): explizit vom Issue verboten.
consequences:
  + Keine Zelle der Spec ist eine Behauptung; 40/40 Zellen sind entweder
    datenabgeleitet oder explizit `UNVERIFIED ⇒ no` (B1).
  + Ein Datenort, maschinell prüfbar, testbar (Invariante AC-15).
  + Neue Provider sind ohne Code-Änderung korrekt eingeordnet (fail-safe).
  - `hybrid` liefert in v1 keinen zusätzlichen Nutzen gegenüber `subagent`
    (nur Akzeptanz + laute Degradierung); das ist der Preis für die
    konservative Freigabe.
```

**Veto-Konsequenz:** Ohne Capability-Daten bleibt nur eine Doku-Matrix; dann
muss die Spec eine manuelle Drift-Prüfung als DoD-Punkt aufnehmen, und das
Issue-Risiko „silent degradation" ist nur durch Review diszipliniert, nicht
durch Tests.

---

## 7. Provider × Topologie-Matrix (Freigabe-Artefakt, nicht Nacharbeit)

**Ableitungsregel (B1):** Jede Zelle ist aus den vorhandenen Capability-Keys
abgeleitet; Zellen ohne Datenbasis sind `UNVERIFIED ⇒ no`. Es gibt in dieser
Tabelle **keine** unbelegte `yes`-Zelle.

| Achse | Ableitung | `verified_state`-Quelle |
|---|---|---|
| `primary` | `main_agent_selectable == true` | `topology_verified_state.primary` |
| `subagent` | `subagent_dispatch == true` | `topology_verified_state.subagent` |
| `hybrid` | **keine Datenbasis** → immer `false`, `degrade` = `"subagent"` (fail-safe, Minor 4) | `topology_verified_state.hybrid = UNVERIFIED` |
| `N>1` | `subagent_dispatch == true AND parallel_execution == true` | `topology_verified_state.multiple` |

| Provider | `primary` | `subagent` | `hybrid` | N>1 |
|---|---|---|---|---|
| **Claude** | **yes** — `main_agent_selectable: true`; Einstieg via `claude --agent orchestrator` (DOCUMENTED) | **yes** — `subagent_dispatch: true` | **no→subagent** — `UNVERIFIED`; Fail-safe-Ziel `subagent` (Minor 4) | **yes** — `parallel_execution: true` |
| **Opencode** | **yes** — `mode: primary` + `default_agent` (VERIFIED-RUNTIME, S1/S3) | **yes** — `subagent_dispatch: true`; **neu in v1**: `mode: subagent` (bzw. kein `mode` auf v1) und **kein** `default_agent` | **no→subagent** — `UNVERIFIED`; ein `mode: primary`-Eintrag ist nicht per `task` spawnbar (#1006, §16 Nr. 2); Fail-safe = `subagent` | **yes** — `parallel_execution: true` |
| **Gemini / Antigravity** | **no→subagent** — `main_agent_selectable: false` | **yes** — generierter Roster (`provider-bootstrap.yaml`, `instructions_mode: generated`) | **no→subagent** — `UNVERIFIED` | **yes** — `parallel_execution: true` (`native-batch`) |
| **Continue** | **yes** — `main_agent_selectable: true` (`cn --agent`, DOCUMENTED) | **degraded→sequential-text** — `subagent_dispatch: false`: nur `@agent`-Text-Mention, keine Isolation | **no→subagent** — `UNVERIFIED`; Fail-safe bleibt `subagent`, obwohl `subagent_dispatch: false` — `hybrid` wird ohnehin nie gewährt | **no** — `parallel_execution: false` |
| **Copilot** | **no→subagent** — `main_agent_selectable: false` | **yes** — `agents:`-Allow-List + `agent`-Tool (#855) | **no→subagent** — `UNVERIFIED` | **no** — `parallel_execution: false` (Rev. 1: fälschlich `yes`) |
| **Mammouth** | **no→subagent** — Quell-Key selbst UNVERIFIED (§16 Nr. 5), zählt **nicht** als datenabgeleitet | **yes** — natives `task` (F-11/IC-15 Nr. 6) | **no→subagent** — `UNVERIFIED` | **no** — `parallel_execution: false` (Rev. 1: fälschlich `yes`) |
| **Codex** | **no→subagent** — Quell-Key selbst UNVERIFIED (§16 Nr. 4), zählt **nicht** als datenabgeleitet | **yes** — `spawn_agent`/`wait_agent`, Config-Layer-Auto-Load | **no→subagent** — `UNVERIFIED` | **yes** — `parallel_execution: true` (tool-mediated Barrier) |
| **ZCode** | **no→subagent** — `main_agent_selectable: false` | **yes** — `Agent`-Toolcall + Bootstrap-Roster (`instructions_mode: static`) | **no→subagent** — `UNVERIFIED` | **no** — `parallel_execution: false` (Rev. 1: fälschlich `yes`) |
| **KimiCode** | **yes** — `main_agent_selectable: true` (DOCUMENTED, §16 Nr. 6) | **yes** — `Agent` + `AgentSwarm` | **no→subagent** — `UNVERIFIED`; dieselbe Markdown-Datei in beiden Positionen ist plausibel, aber nicht belegt; Fail-safe = `subagent` | **yes** — `parallel_execution: true` (`AgentSwarm`) |
| *(custom / nicht im Registry)* | **no** — `UNVERIFIED`, kein Registry-Datum (fail-safe; **kein** generischer Default, M1) | **no** — `UNVERIFIED`, kein Registry-Datum (fail-safe; **kein** `yes`, M1) | **no→subagent** — `UNVERIFIED`; Fail-safe-Ziel der Auflösung, keine Capability-Zusage | **no** (keine Capability-Daten) |

**Hinweis zur custom-Zeile (M1):** Ein nicht registrierter Provider hat
**keine** Capability-Daten. Alle vier Zellen sind deshalb `UNVERIFIED ⇒ no`;
`subagent: yes` wäre ein generischer Default ohne Evidenz und genau das, was
S24/§2 verbieten. Das `no→subagent` in der `hybrid`-Spalte ist das
*Ziel der Degradierung* (D10 (c), Minor 4), **keine** Subagent-Fähigkeitszusage
— die effektive Topologie eines nicht registrierten Providers bleibt der
abgeleitete Default aus D9.

**Zählung (B1):**

- 40 Zellen (10 Zeilen × 4 Spalten).
- **25 Zellen datenabgeleitet** — Quell-Key vorhanden und nicht UNVERIFIED:
  `primary` 7 (Claude, Opencode, Gemini, Continue, Copilot, ZCode, Kimi),
  `subagent` 9 (alle registrierten Provider), `N>1` 9 (alle registrierten
  Provider). Auch die `no→`-Zellen leiten ihr `no` aus `false`-Daten ab.
- **15 Zellen `UNVERIFIED ⇒ no`**:
  - 10× `hybrid` (9 registrierte Provider + custom) — keine Datenbasis,
  - 2× `primary` mit selbst als UNVERIFIED markiertem Quell-Key (Codex
    §16 Nr. 4, Mammouth §16 Nr. 5),
  - 3× custom-Restzellen (`primary`, `subagent`, `N>1`) ohne Registry-Daten.
- **0 spekulative `yes`-Zellen.**

**Wichtig:** `N>1 = yes` heißt „der Provider kann N Subagenten parallel
dispatchen" (Capability `parallel_execution`), **nicht** „N Orchestratoren sind
in v1 freigegeben". Die Aktivierung von `max-instances > 1` bleibt bis P3
(Zustands-Isolation, D6/R8) gesperrt; die Matrix ist keine Freigabe für N>1.
`topology_verified_state.multiple` ist für diese Zellen `DOCUMENTED`, nicht
`VERIFIED-RUNTIME` — die Audit-/Scope-Semantik ist Konventions-Pflicht
(D7/§9), keine Provider-Zusage.
- Gegenüber Rev. 1 **6 Zellen abgesenkt**: 3× `hybrid` (Claude `yes`,
  Opencode `degraded`, Kimi `yes` → `no→…`) und 3× `N>1` (Copilot, Mammouth,
  ZCode `yes` → `no`). Die vierte `parallel_execution: false`-Zelle (Continue)
  war bereits `no`; sie bleibt `no` und ist jetzt als Datenzeile markiert.
- **Rev. 3 (M1):** die custom-Zeile behauptet **kein** `subagent: yes` mehr; sie
  ist in allen vier Zellen `UNVERIFIED ⇒ no`. Ein generischer Default ohne
  Registry-Datum ist genau das, was S24/§2 verbieten. Ebenso zählen Codex und
  Mammouth `primary` **nicht** als datenabgeleitet, weil der Quell-Key selbst
  UNVERIFIED ist.
- **Resultierende `hybrid`-Zeile:** alle zehn Zeilen `no→subagent` — in **allen**
  Fällen WARNING `orchestrator-topology.hybrid-unverified`. Der Fail-safe-
  Zielwert ist bewusst **nicht** „providers eigene Position": auf Claude/
  Opencode/Continue/Kimi wäre das `primary` und damit `default_agent:
  orchestrator` auf einer Rolle, die §1 ausdrücklich vermeiden will (Minor 4).

**Zehn Zeilen:** Das Briefing nennt „zehn Provider"; die Registry enthält
**neun** (S18, verifiziert über `providers.registered_provider_names()`). Die
zehnte Zeile ist deshalb bewusst der *nicht registrierte* Provider — der
fail-safe Fall, der ohne Capability-Daten niemals `primary`/`hybrid`
verspricht.

**Loudness-Regel:** Jede Zelle mit `degraded→X`, `no→X` oder `UNVERIFIED`
erzeugt beim Sync genau *einen* WARNING pro Provider und Lauf
(`orchestrator-topology.degraded` / `.hybrid-unverified`, Text nennt Provider,
Deklaration, effektiven Wert und die Capability, die es verhindert) sowie einen
Matrix-Eintrag in der Concept-Doc. Kein stilles Absenken, kein stilles Clamping.

**Upgrade-Pfad (nicht Teil dieses Designs):** Eine Zelle darf erst `true`
werden, wenn (1) §3.1 für die Position keine offenen `unverified`-Felder mehr
hat, (2) `topology_verified_state` auf `DOCUMENTED`/`VERIFIED-RUNTIME` steht
und (3) ein Invariantentest die Änderung abdeckt. Das ist die Pre-Approval-
Evidenz für die *nächste* Revision — nicht für diese.

---

## 8. `mode` × `topology`-Interaktionsmatrix

Lesart: **Zeile = `mode`** (effektiv, nach Präzedenz S6), **Spalte = `topology`**.

| `mode` \ `topology` | `primary` | `subagent` | `hybrid` |
|---|---|---|---|
| `strict` | Einstieg, strikte Gates, 1 Instanz | Main Chat spawnt 1..N, strikte Gates | positions-agnostisch, strikte Gates |
| `advisory` | Einstieg, advisory Gates | Main Chat spawnt 1..N, advisory | positions-agnostisch, advisory |
| `main-chat` | **ERROR** (gleicher Scope, inkl. Same-Object) bzw. **inert + WARNING** (Cross-Scope) | **ERROR** (gleicher Scope) bzw. **inert + WARNING** (Cross-Scope) | **ERROR** (gleicher Scope) bzw. **inert + WARNING** (Cross-Scope) |

Regeln, die daraus folgen:

1. `main-chat` ist die **einzige** Dominanzzelle: sie löscht die Rolle
   (S8), also kann keine Topologie gelten. Gleicher Scope = harter Validator-
   ERROR (§4.7); Cross-Scope = WARNING (`main-chat-supersedes`).
2. `topology` ändert **nie** die Gate-Stärke; `mode` ändert **nie** die
   Position. Wer beides gleichzeitig will, setzt beide Keys.
3. Bei `mode != main-chat` und `topology: subagent` auf Opencode entfällt der
   `default_agent` — damit entfällt auch der Runtime-Gate-Deny (S4/D1a). Das ist
   eine **Folge der Nutzerentscheidung**, wird aber als eigener WARNING
   gemeldet („runtime gate inactive because topology=subagent removed the
   entry point") — nicht als Nebensatz. Der **ActiveSet-Konjunkt** aus
   `_opencode_entry_point` bleibt dabei erhalten (A5): eine deaktivierte
   Orchestrator-Rolle liefert weiterhin `None`, unabhängig von der Topologie.
4. **Cross-Scope `primary` × globales N>1:** Provider-Override
   `topology: primary` bei globalem `max-instances > 1` ist **kein** harter
   ERROR (D3 (1) gilt nur im selben Scope), sondern WARNING
   `instances-clamped`; die effektive Instanzzahl für diesen Provider ist 1.
5. **Builder-Default (B2):** Ein `default_agent` wird nur geschrieben, wenn die
   effektive Topologie `primary` ist **und** die Rolle im ActiveSet liegt.
   Sonst bleibt der Main Chat der Default; ein vorhandener nutzereigener Wert
   wird nicht gelöscht, sondern als `default-agent-conflict` gewarnt (§4.6).

---

## 9. Multi-Instanz-Vertrag

### 9.1 Instanz-Identität

- **Form:** `orchestrator_id` = `[a-z0-9][a-z0-9._-]{0,39}`.
- **Quelle:** Der Main Chat vergibt sie beim Spawn. Deterministische Ableitung:
  der Scope-Schlüssel des Strangs (Plan-ID/Task-Ref, Branch-Name oder
  PR-Nummer), normalisiert (`_sanitize_component`-Regeln).
- **Default:** `None` bei `max-instances == 1` → **keine** sichtbare Änderung
  an Rollennamen, Dateinamen, Session-IDs.
- **Adressierung:** Der Dispatch-Zielname bleibt **`orchestrator`** (Dateien
  und `subagent_type` kennen keine `#`-Suffixe). Die Identität reist im
  Envelope: `orchestrator_id` (neues optionales Feld,
  `schemas/a2a-handoff.schema.json`) plus `metadata.scope_id`.
- **Audit-Datensatz (A7, Kommentar §4):** Vollständig ist
  `{orchestrator_id, scope_id, spawned_by, spawned_at}`. `spawned_by` ist der
  Spawner of record (`main_chat`), `spawned_at` der Spawn-Zeitpunkt. Der
  Datensatz steht im Viz-Event (§5) und — reduziert auf die ID — im
  Guard-Audit-Log (§10). Die Reduktion im Guard ist bewusst: der Hook sieht
  keinen Spawn-Zeitpunkt und keinen Scope.
- **Fehlende ID (N>1):** HARD REJECT durch den Main Chat (Prompt-Vertrag, §10)
  und WARNING im Guard-Audit (`id=unset`).
- **Doppelte ID / Scope-Überlappung:** HARD ERROR **beim Spawn**, mit beiden
  Eigentümern im Text. Kein Laufzeit-Race — die Prüfung liegt vor dem ersten
  Dispatch (Main Chat ist der einzige, der alle Instanzen sieht).

### 9.2 Scope-Regel

Ein Scope ist eine Menge von Dateien/PRs/Branches. Zwei Instanzen mit
überlappendem Scope dürfen nicht koexistieren. Die Prüfung ist
**Main-Chat-Pflicht** (Prompt + A2A-Gate G2), nicht Framework-Runtime — es gibt
keinen Interception-Punkt (dieselbe akzeptierte Grenze wie
`validate_envelope`, S16).

### 9.3 Zustands-Namespaces

| Artefakt | N=1 (Default) | N>1 |
|---|---|---|
| Checkpoint | `<checkpoint-dir>/<base>.json` | `<checkpoint-dir>/<base>__<id>.json` |
| Fortschritt | `<progress-dir>/current.md` | `<progress-dir>/progress-<id>.md` (Instanz, **nur menschlich**) + `current.md` (nur Wurzel, maschinell gelesen) |
| Event-Log | `.meta-viz/events.jsonl` | gleich, Felder `orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at` |
| Tracker | im Kontext | im Kontext (je Instanz) |

**Eine Identität, zwei Dateinamen:** `<base>__<id>` (Checkpoint) und
`progress-<id>.md` (Mensch) leiten sich aus **derselben** normalisierten
`orchestrator_id` ab. `recovery.py` liest nur Checkpoints; `current.md` ist der
einzige maschinell gelesene Fortschritt (A10, S13/S14).

### 9.4 Teardown / Aggregation

Nur der Main Chat sieht alle Instanzen; er aggregiert Ergebnisse und schreibt
den Gesamt-Fortschritt. Keine Orchestrator→Orchestrator-Koordination (G3).
Instanz-Teardown = Kontextende; es gibt kein "Abmelden"-Artefakt.

---

## 10. Regel- und Guard-Anpassung (Text-Skizze, conditional)

`rules/1-generic/a2a-delegation-gates.md` Gate 2 erhält **zwei Zweige**. Der
`{{else}}`-Zweig bleibt **wortgleich** zum heutigen Text (S20), inklusive des
verschachtelten `{{#if ROLE_ORCHESTRATOR_ACTIVE}}` (B4):

**v1 (P4) — Topologie-Zweig ohne Instanz-Platzhalter** (`ORCH_MAX_INSTANCES`
existiert erst mit P3, M3):

```markdown
{{#if ORCH_TOPOLOGY_EXPLICIT}}2. **Orchestrator-Topologie ({{ORCH_TOPOLOGY}}):**
   G1 Ein Worker dispatcht NIE einen `orchestrator` — HARD REJECT, bei jedem N.
   G2 NUR `main_chat` spawnt **genau einen** Orchestrator pro Session, mit
      eindeutiger `orchestrator_id` und disjunktem Scope. Doppelte ID oder
      Scope-Überlappung = HARD ERROR beim Spawn (beide Eigentümer nennen).
   G3 Ein Orchestrator dispatcht NIE einen Orchestrator — HARD REJECT.
   Der Main Chat ist der einzige Aggregator; Instanzen koordinieren sich nicht.{{else}}2. **Orchestrator-Singleton:** NUR `main_chat` darf den `orchestrator` spawnen. Worker{{#if ROLE_ORCHESTRATOR_ACTIVE}} → `orchestrator`{{/if}} → HARD REJECT (siehe `singleton-orchestrator-architecture.md`).{{/if}}
```

**P3 — Instanz-Wortlaut (Amendment, nicht v1):** Mit dem Key `max-instances`
ersetzt G2 „**genau einen**" durch „**höchstens {{ORCH_MAX_INSTANCES}}**"
(dieselbe Datei, dieselbe Branch-Struktur). Vor P3 rendert die Gate-Zeile
keinen `ORCH_MAX_INSTANCES`-Platzhalter; damit bleibt v1s DoD ohne P3
erreichbar (M3).

**Byte-Identitäts-Vorschrift (B4):** Die Marker `{{#if …}}` und `{{else}}`
stehen **inline unmittelbar vor dem ersten Zeichen** des jeweiligen Zweigs; der
`{{else}}`-Zweig ist **eine** Zeile, ohne führenden/abschließenden Whitespace
gegenüber dem heutigen Text. Nur so liefert der ungesetzte Key exakt die
heutigen Bytes. Ein `{{else}}` auf eigener Zeile würde einen zusätzlichen
Zeilenumbruch rendern und AC-6 verletzen.

**Maschinerie-Voraussetzung (B4, S23):** Der obige Block rendert mit dem
heutigen Mechanismus **beide** Zweige bzw. den **falschen**, solange
`ORCH_TOPOLOGY_EXPLICIT` nicht an **beiden** Stellen registriert ist (Details
§4.3):

- `scripts/lib/variables.py::strip_inactive_conditional_blocks` — Whitelist
  (`conditional_vars`, Z. 431–451) um Präfix `ORCH_TOPOLOGY_` erweitern,
- `scripts/lib/variables.py::_FALSE_DEFAULT_CONDITIONALS` (Z. 52) —
  `ORCH_TOPOLOGY_EXPLICIT`/`_PRIMARY`/`_SUBAGENT`/`_HYBRID` eintragen, sonst
  liest `_conditional_active` die abwesende Variable als aktiv und rendert den
  **neuen** Zweig,
- `scripts/lib/standalone.py::_CONDITIONAL_FALSE_FLAGS` (literale Flags; die
  `ROLE_*_ACTIVE`-Flags werden dort für alle Rollen auf `"true"` gesetzt, das
  verschachtelte `{{#if ROLE_ORCHESTRATOR_ACTIVE}}` löst also wie heute auf),
- `scripts/lib/consistency/placeholders.py::_BUILTIN_VARS` (Builder-Variablen).

`rules.py::_merged_rule_vars` ist ein realer Render-Pfad mit `variables=None`
(S23); er muss die Topologie-Flags genauso selbst bauen wie `_orch_mode_flags`,
sonst rendert ein Direktaufrufer den else-Zweig (fail-closed, aber bewusst).

Dieselbe Conditional-Logik gilt für:

- `agents/1-generic/orchestrator.md` (§ Singleton-Regel, Zeile „Ich bin bereits
  der einzige Orchestrator"),
- `agents/1-generic/_reference-agent.md` (Singleton-Zeile),
- die generierten `CLAUDE.md`/`AGENTS.md`-Regelblöcke (über dieselbe Quelle).

Für diese drei Stellen gilt dieselbe Marker-Platzierung; der Default-Zweig ist
jeweils wortgleich zum heutigen Text.

**Golden-Fixtures (B4):** Zwei Fälle sind Pflicht (AC-18):

1. **Rolle inaktiv + Key unset** → `Worker → HARD REJECT` (ohne
   `→ orchestrator`), exakt heutige Bytes.
2. **Rolle aktiv + Key unset** → `Worker → orchestrator → HARD REJECT`
   (Status quo, Standalone-Fall).

Guard (`hooks/1-generic/orchestrator-guard-impl.sh`):

- Sentinel-Grammatik erweitern auf
  `^#agent-meta:agent=([A-Za-z0-9_-]+)(?:\s+id=([A-Za-z0-9._-]+))?$`.
- Die ID wird **nur** ins Audit-Log geschrieben (`hook_audit_log_append`),
  niemals in einer Allow/Deny-Entscheidung benutzt.
- Der bestehende Audit-Log-Redaction-/Rechte-Pfad bleibt unverändert.

---

## 11. Phasenzerlegung

Jede Phase ist **eigenständig mergebar** (grün, rückrollbar) und lässt
`sync --check` auf unveränderten Consumer-Projekten byte-identisch.
Größen nach `spec-plan-workflow` (S/M/L/XL, F7-Kriterium).

| Phase | Größe | Dateien | Was sie landet | Warum getrennt mergebar |
|---|---|---|---|---|
| **P0 — Capability-Daten & Verified-State** | **S–M** (3) | `config/provider-capabilities.yaml` (+4 Strukturen je Provider, konservative Werte), `tests/test_topology_capability_invariant.py` (neu), `docs/spikes/2026-11-03-issue-1077-topology-probe.md` (Evidenzplan, **kein** Freigabe-Gate) | Die Datenbasis der Matrix (§7): `topology_support`, `topology_degrade`, `orchestrator_instances`, `topology_verified_state` + Invariante | Reine Daten/Doku, keine Emission berührt; die Werte sind bereits konservativ, also ist P0 **keine** Vorbedingung der Spec — die Spec hängt an §7, nicht an einem Spike (B1) |
| **P1 — Config-Fläche, Auflöser, Validator, Flags** | **L** (11–12) | `config/project-config.schema.json`, `scripts/lib/topology.py` (neu), `scripts/lib/config.py` (`_validate_orchestrator_topology` (a)–(c), globale Flags), `scripts/lib/variables.py` (`_topology_flags`, Whitelist in `strip_inactive_conditional_blocks`, `_FALSE_DEFAULT_CONDITIONALS`), `scripts/lib/standalone.py` (`_CONDITIONAL_FALSE_FLAGS`), `scripts/lib/consistency/placeholders.py` (`_BUILTIN_VARS`), `scripts/lib/providers.py` (`primary_role`-Accessor), `scripts/lib/active_set.py` (`role_emitted_for_provider`, **nur** Funktion + Unit-Test), `tests/test_orchestrator_topology.py` (neu), `tests/test_orchestrator_topology_schema.py` (neu), `tests/test_orchestrator_topology_validator.py` (neu), Doku-Beispiele | Enum + Defaults, hartes Same-Scope-Validieren (a)–(c), Auflösekette, flache Topologie-Flags, **fail-closed** Conditional-Registrierung, ein `primary-role`-Lesezugriff | Key wird akzeptiert und aufgelöst, aber **noch nicht** in die Emission verdrahtet; `role_emitted_for_provider` ist gelandet, hat aber **keine Call-Site** (A8); unset-Verhalten byte-identisch (fail-closed durch `_FALSE_DEFAULT_CONDITIONALS`); einzeln revertierbar |
| **P2 — Emission, laute Degradierung, Builder-Default** | **L** (10–11) | `scripts/lib/provider_transform.py`, `scripts/lib/isolation.py`, `scripts/lib/context.py` (`apply_settings_surface_shape`, `_init_provider_settings_json`), `scripts/lib/agent_sync.py` (Call-Site auf `role_emitted_for_provider`), `scripts/lib/consistency/topology.py` (neu), `scripts/consistency-check.py`, `tests/test_provider_transform_topology.py` (neu), `tests/test_topology_consistency.py` (neu), `tests/test_ac01_render_identity.py` (Fälle + Golden-Fixtures), `tests/fixtures/topology-golden/*` (neu), `config/ai-providers.yaml` (Kommentar) | `subagent` auf Opencode funktioniert real; Entry-Point/Gate-Kopplung folgt der Topologie; **kein** `default_agent` bei Topologie ≠ `primary`; `agent_sync.py` nutzt das Prädikat an der zweiten Stelle; WARNING + INFO | Braucht P1 (Auflöser, Validator, Flags); ist der einzige Schritt, der emittierte Bytes ändern kann — und nur bei explizitem Key. Die Call-Site-Umstellung ist bewusst hier, nicht in P1 (A8) |
| **P3 — Multi-Instanz-Vertrag & Zustands-Namespaces** | **L** (10–12) | `config/project-config.schema.json` (`max-instances` mit `maximum: 8`, `singleton`), `scripts/lib/config.py` (`_validate_orchestrator_topology` (d)/(e)), `scripts/lib/variables.py` (`_instance_flags`: `ORCH_MAX_INSTANCES`, `ORCH_SINGLETON_DECLARED` + Whitelist-/`_FALSE_DEFAULT_CONDITIONALS`-/`_CONDITIONAL_FALSE_FLAGS`-Einträge), `scripts/lib/topology.py` (Instanz-Auflösung), `rules/1-generic/a2a-delegation-gates.md` (Instanz-Wortlaut, §10), `scripts/lib/checkpoint.py`, `schemas/a2a-handoff.schema.json`, `scripts/lib/delegation_syntax.py`, Viz-Emitter (`scripts/viz-logger.py` o. ä.), `tests/test_multi_instance_state.py` (neu), `tests/test_checkpoint_paths.py` (Fälle) | N>1 sicher: presence-only `singleton`, ID, Session-ID-Komposition, Event-Tagging (`scope_id`/`spawned_by`/`spawned_at`), Gate-Wortlaut mit `max {{ORCH_MAX_INSTANCES}}` | Setzt P1 voraus, **nicht** P2 (die Multiplizitäts-Achse ist laut Kommentar unabhängig). `max-instances` **existiert vor P3 nicht**; er wird hier gemeinsam mit `maximum: 8` und der Zustands-Isolation eingeführt (M3, AC-8/AC-9/AC-17 sind P3-only). |
| **P4 — Regel-, Guard- und Doku-Amendment** | **M** (7–9) | `rules/1-generic/a2a-delegation-gates.md`, `agents/1-generic/orchestrator.md`, `agents/1-generic/_reference-agent.md`, `hooks/1-generic/orchestrator-guard-impl.sh`, `docs/concepts/active/orchestrator-topology.md` (neu, inkl. A1-Deviationssatz), `docs/concepts/active/singleton-orchestrator-architecture.md` (Status-Hinweis), `tests/test_orchestrator_guard_hook.py`, `CHANGELOG.md` | Neue Gate-Formulierung (conditional, else wortgleich, **ohne** Instanz-Platzhalter), Audit-ID, Concept-Doc + Cross-Links | Braucht nur P1 (nutzt `ORCH_TOPOLOGY_EXPLICIT`); der Instanz-Wortlaut kommt mit P3 (§10). Die drei Conditional-Dateien `variables.py`, `standalone.py`, `placeholders.py` sind **P1**-Änderungen und werden in P4 nur konsumiert/verifiziert |

**Summe:** 41–48 Datei-Berührungen (mit Doppelzählungen von
`project-config.schema.json`, `config.py` und `topology.py`), **XL** (F7:
öffentliche Config-Contracts + Schema + mehr als eine Subsystemgrenze →
Architectural unabhängig von der Dateizahl).

**Ehrliche Schnittkante (OQ-5, Default: ja):** v1 = **P0–P2 + P4**
(Config-Fläche + Auflöser + laute Degradierung + sichtbare Regel + Doku)
liefert den Builder-Default und **genau einen** spawnbaren Orchestrator; es ist
eigenständig nützlich und ohne Zustandsrisiko. Multi-Instanz = **P3** ist der
riskante Teil und der **unmittelbar nächste Schritt** (kein offenes Ende); er
kann v1 nicht blockieren, weil v1 keinen `max-instances`-Key und keine
P3-only-AC referenziert (M3).


---

## 12. Acceptance Criteria

### Aus Issue §5 (Framework-Seite)

| ID | Kriterium | Prüfbar durch |
|---|---|---|
| **AC-1** | `config/project-config.schema.json` deklariert `orchestrator.topology` (enum, präzise `mode`-Interaktion, Default = heutige Ableitung); der Same-Scope-Widerspruch wird **nicht** vom Schema, sondern von `config.py::_validate_orchestrator_topology` hart abgelehnt | Schema-Test + Validator-Test (`--validate` rc≠0) |
| **AC-2** | Der Auflöser liefert `SyncError` mit handlungsfähigem Hint für unbekannte Enum-Werte; der Same-Scope-`main-chat`-Konflikt kommt aus dem stdlib-Validator (kein `jsonschema` nötig) | Unit-Test (Fehlertext-Assertion) + Validator-Test |
| **AC-3** | Emission respektiert die Auflösung; Per-Provider-Degradierung ist im Code kommentiert **und** als Consistency-WARNING sichtbar | `check_orchestrator_topology()` + Transform-Test |
| **AC-4** | Concept-Doc erklärt drei Topologien, Support-/Degradierungsmatrix, Multi-Instanz-Adressierung **und den `hybrid`-Deviationssatz (A1)**; verlinkt aus Singleton-Concept und A2A-Rule | Doku-Existenz + Link-Check (`consistency/docs.py`-Muster) |
| **AC-5** | Tests: Enum, `mode`×`topology`-Matrix, `main-chat`-Konflikt, abgeleiteter Default | 4 Testmodule aus P1/P2 |
| **AC-6** | Kein Verhaltenswechsel ohne Key: `sync --check` auf unverändertem Consumer-Projekt byte-identisch — inklusive der Golden-Fixtures „Rolle inaktiv + Key unset" und „Rolle aktiv + Key unset" | `tests/test_ac01_render_identity.py` + `tests/fixtures/topology-golden/*` |
| **AC-7** | Cross-Scope-Fall (`provider-overrides.<P>.mode: main-chat` bei globaler Topologie) erzeugt genau einen WARNING, keinen Fehler | Konsistenz-Test |

### Aus dem Issue-Kommentar (Multi-Instanz-Slice)

> **Phasen-Geltung (M3):** Die mit **(P3-only)** markierten ACs gehören **nicht**
> zur v1-DoD. v1 (= P0–P2 + P4) prüft AC-1…AC-7, AC-13…AC-16, AC-18 und die
> P1-Zeilen von AC-17; AC-8…AC-12 und die P3-Zeilen von AC-17 werden mit P3
> grün (OQ-5, Default: ja).

| ID | Kriterium | Prüfbar durch |
|---|---|---|
| **AC-8** | **(P3-only)** Schema akzeptiert `orchestrator.max-instances` (`maximum: 8`, Default 1 — der Key existiert vor P3 nicht) und `singleton` (nur `true`, **kein Schema-`default`**); `singleton` present + `max-instances > 1` ist ein harter Validator-ERROR; `--validate` ist grün bei konsistenten Configs | Schema-Test (beide Richtungen) + Validator-Test |
| **AC-9** | **(P3-only)** `topology: primary` + `max-instances > 1` im selben Scope ist ein harter ERROR; der Cross-Scope-Fall (Provider-Override `primary`, globales N>1) ist WARNING + effektiv N=1 | Validator-Test + Konsistenz-Test |
| **AC-10** | **(P3-only)** N=1 erzeugt exakt die heutigen Checkpoint-/Progress-Pfade; N=2 erzeugt `<base>__<id>`-Dateien; `validate_session_id` akzeptiert die Komposition | `tests/test_checkpoint_paths.py`-Erweiterung |
| **AC-11** | **(P3-only)** Audit-Datensatz vollständig: Viz-Events bei N>1 tragen `orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at`; das Log bleibt **eine** Datei; `viz-report` konsumiert unverändert; das Guard-Audit-Log trägt die ID (Reduktion dort dokumentiert) | Event-Fixture + Reader-Test + Hook-Test |
| **AC-12** | **(P3-only)** `max-instances` und `max-parallel-agents` sind in beiden Schema-descriptions gegeneinander abgegrenzt (Text-Assertion) | Schema-Text-Test |
| **AC-13** | Jeder registrierte Provider trägt `topology_support`, `topology_degrade`, `orchestrator_instances` **und** `topology_verified_state` (Invariante) | Provider-Invariantentest (Muster `test_provider_three_file_invariant.py`) |

### Aus den Review-Findings (Rev. 2)

| ID | Kriterium | Prüfbar durch |
|---|---|---|
| **AC-14** | Frisches Opencode-v2-Projekt mit `topology: subagent` enthält **kein** `default_agent` auf der Orchestrator-Rolle; ein verwalteter Wert wird beim Wechsel `primary → subagent` zurückgerollt; ein nutzereigener Wert erzeugt `default-agent-conflict` (WARN, kein Auto-Delete); der ActiveSet-Konjunkt aus `_opencode_entry_point` bleibt wirksam | `tests/test_ac01_render_identity.py` + Isolation-Test |
| **AC-15** | `topology_support.* == true` ⇒ `topology_verified_state.* != UNVERIFIED`; der Resolver gibt bei `UNVERIFIED` **nie** den deklarierten Wert zurück; in v1 ist `hybrid` auf allen Providern `UNVERIFIED` und effektiv degradiert | Provider-Invariantentest + Resolver-Test |
| **AC-16** | Die Matrix (§7) hat 40 Zellen: **25 datenabgeleitet**, **15 `UNVERIFIED ⇒ no`** (10× `hybrid` [9 Provider + custom], 2× unverifizierte `primary` [Codex, Mammouth], 3× custom-Restzellen), **0 spekulative `yes`**; jede Degradierung erzeugt genau einen WARNING pro Provider und Lauf | Matrix-Zähl-Test + Konsistenz-Test |
| **AC-17** | Der harte stdlib-Validator lehnt ab (rc≠0 in `sync` **und** `--validate`, ohne `jsonschema`) mit den in §4.7 gepinnten Teilstrings: **(P1)** Same-Scope `main-chat` × Topologie (auch Same-Object), `enabled: false` × Topologie; **(P3-only)** `singleton: false`, `singleton` present × N>1, `primary` × N>1 im selben Scope | `tests/test_orchestrator_topology_validator.py` (P1-Fälle) + P3-Testerweiterung |
| **AC-18** | `ORCH_TOPOLOGY_*` sind in der Whitelist von `strip_inactive_conditional_blocks` registriert **und** `ORCH_TOPOLOGY_EXPLICIT`/`_PRIMARY`/`_SUBAGENT`/`_HYBRID` stehen in `_FALSE_DEFAULT_CONDITIONALS` (**fail-closed:** abwesend ⇒ inaktiv); `_CONDITIONAL_FALSE_FLAGS` und `_BUILTIN_VARS` tragen dieselben Flags; Key unset rendert exakt den heutigen else-Zweig (inkl. verschachteltem `ROLE_ORCHESTRATOR_ACTIVE`); kein Zweig rendert doppelt | Golden-Fixtures + `check_builder_known_set` + Conditional-Test (abwesende Variable ⇒ else) |

---

## 13. Risiken und Gegenmaßnahmen

| # | Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| **R1** | **Zweite Skip-Stelle** (`main-chat`-Skip in `agent_sync.py` + neue Topologie-Logik) | Orchestrator verschwindet still oder wird doppelt gepruned | Ein Prädikat `role_emitted_for_provider` (C3); **P1 landet nur die Funktion + Unit-Test, P2 stellt beide Call-Sites um** (A8); Test: „genau eine Funktion entscheidet" (AST-/Grep-Assertion) |
| **R2** | **`default_agent` ↔ Gate-Deny-Kopplung** (S4) **und zweiter Schreiber** (S21): `topology: subagent` entfernt den Entry Point, `apply_settings_surface_shape` schreibt ihn aber weiter | Nutzer verliert den Builder-Default oder die Main-Chat-Schreibblockade — je nach Pfad | `_opencode_entry_point` bleibt die *einzige* Quelle; `apply_settings_surface_shape` erhält `topology_effective` (P2/AC-14); D1a-Invariante unverändert; zusätzlicher WARNING „gate inactive because topology removed the entry point"; Test: `subagent` ⇒ kein `default_agent`, kein Deny, aber WARNING |
| **R3** | **Selbstdeklarierter Guard**: N Instanzen sind nicht durchsetzbar | Falsche Sicherheitserwartung | Convention-Boundary-Text bleibt; Audit-ID (D8); „Bekannte Grenzen" explizit erweitert; keine Enforcement-Behauptung in Doku/ACs |
| R4 | **Byte-Identität bricht** durch unbedingte Textänderung an der Singleton-Regel (S20) oder durch ein `{{else}}` auf eigener Zeile (B4) | Jedes Consumer-Projekt meldet Drift nach Upgrade | Conditional-Rendering mit **inline** platzierten Markern und wortgleichem else-Zweig; AC-6 + AC-18; Golden-Fixtures „Rolle inaktiv/aktiv + Key unset" |
| R5 | **Warnungs-Müdigkeit** (jeder Provider degradiert irgendwo, v1 zusätzlich `hybrid` überall) | Nutzer ignoriert die Warnung, die eigentliche Degradierung fällt nicht auf | Provider-Override (D4) macht die Warnung abstellbar; genau eine Warnung pro Provider und Lauf (dedupliziert); Text nennt die Capability; `hybrid` ist in v1 bewusst nicht gewährt (kein Dauer-Warning ohne Deklaration) |
| R6 | **Schema bleibt offen** (`additionalProperties: true`, S10) | Tippfehler `topolgy` wird still akzeptiert | In v1 dokumentierte Keys + Hint in der `description`; ein „unbekannte `orchestrator.*`-Keys"-Finding ist als optionaler Folgeschritt notiert (nicht Teil des Umfangs) |
| R7 | **Koordinationskollision mit D16** (`role_emitted_for_provider` im Bug-Batch-Plan) | Doppelimplementierung oder Merge-Konflikt | P1 übernimmt die Funktion *einmal*; D16 referenziert sie nur noch |
| R8 | **N>1 ohne Zustands-Isolation** | Stiller Resume-Datenverlust | Harte Kopplung: der Key `max-instances` **existiert vor P3 nicht**; er wird in P3 gemeinsam mit `maximum: 8` und der Zustands-Isolation eingeführt. Kein Zwischenschritt mit `maximum: 1` (M3) |
| R9 | **Provider-Verhalten driftet** (Matrix veraltet) | Falsches Versprechen | Ableitung aus Capability-Daten + Invariantentest AC-13/AC-15, nicht aus Namen; `topology_verified_state` trennt Daten von Annahme |
| R10 | **Matrix-Zellen werden als Freigabe gelesen, obwohl `UNVERIFIED`** | Spec verspricht `hybrid`/N>1, das kein Provider belegt | §7 zählt **25 datenabgeleitete / 15 `UNVERIFIED ⇒ no`**-Zellen (10 hybrid, 2 unverifizierte `primary`, 3 custom); AC-15/AC-16; `UNVERIFIED ⇒ no` im Resolver |
| R11 | **Validator nutzt `sys.exit(1)` statt `SyncError`** | Bibliotheks-Aufrufer, die `SyncError` erwarten, sehen einen harten Prozessabbruch | Bewusst: `_validate_config` läuft vor dem Sync und in `--validate`; Muster ist `_validate_providers`. Der Auflöser selbst wirft weiterhin `SyncError` (klare Trennung Config-Check vs. Laufzeit-Auflösung) |
| R12 | **`--validate-spec-plan` meldet dieses Design-Doc** (`_classify` → `spec`, literale Überschriften fehlen) | ~8 Section-Findings, obwohl das Dokument korrekt ist | Bewusst akzeptiert: DoD `rapid-prototyping` setzt `spec-plan-required: false` → WARNING; die abgeleitete **Spec** trägt die literalen Überschriften (A9, §17) |

---

## 14. Nicht-Ziele

- **Keine** Parallel-Workstream-Isolation selbst (Worktrees/Checkouts) — Issue
  #547, ausdrücklich out of scope.
- **Keine** Reparatur des OpenCode-v1/v2-Surface-Bugs (#1006). Die
  `primary`-Emission nutzt den bestehenden, korrekten Pfad; wenn #1006 etwas
  ändert, ändert es die *Form*, nicht die Topologie-Semantik.
- **Kein** neuer Provider, keine Änderung der Provider-Registry.
- **Keine** SE-Kaskade (kein `systems-engineering`-Auto-Start).
- **Kein** Admin-UI-Editor für Topologie (nur Schema/Doku); Admin-UI ist ein
  eigener Change.
- **Keine** Per-Instanz-Kosten-/Token-Abrechnung.
- **Keine** Scope-Registry und **kein** Orchestrator→Orchestrator-Spawn in v1
  (D7).
- **Keine** Änderung an `max-parallel-agents` (Semantik, Default, Grenzen).
- **Kein** Runtime-Enforcement von N oder von Instanz-Scopes (D8).
- **Kein** Zell-Upgrade der Matrix in v1: `hybrid` bleibt auf allen Providern
  `UNVERIFIED ⇒ no`; Upgrades sind die Evidenz-Arbeit der nächsten Revision.

---

## 15. Offene Fragen (max. 5, je mit Default)

| ID | Frage | Empfohlener Default | Warum eine Nutzerentscheidung |
|---|---|---|---|
| **OQ-1** | Welche Evidenz hebt eine `hybrid`-Zelle von `UNVERIFIED` auf `DOCUMENTED`/`VERIFIED-RUNTIME` (und damit `topology_support.hybrid: true`)? | **Runtime-Probe je Provider; kein Upgrade vor §3.1-Evidenz + Invariantentest** | Ein vorgezogenes `hybrid: true` kostet Vertrauen; ein dauerhaftes `no` kostet den Enum-Nutzen. Beides ist vertretbar, aber die Entscheidung ist eine Produkt-/Risiko-Entscheidung |
| **OQ-2** | Soll der Guard die optionale Instanz-ID im Sentinel parsen (Audit-only, Hook-Change + Testumbau) oder unverändert bleiben? | **Parsen, audit-only** | Es ist der einzige Nachweis bei Instanz-Überschreitung, kostet aber einen Hook-Version-Bump |
| **OQ-3** | Obergrenze für `max-instances` (Schema-`maximum`)? | **8** | Direkte Kosten-/Token-Folge; 5 ist zu knapp für „ein Strang je PR-Linie", >8 ist unrealistisch |
| **OQ-4** | Soll die *abgeleitete* Topologie als INFO-Finding in `--check` erscheinen (mehr Sichtbarkeit, mehr Output für jedes Projekt) oder nur als Sync-Summary-Zeile? | **Nur Sync-Summary** (kein `--check`-Delta) | Sichtbarkeit gegen „null Output-Delta für unveränderte Projekte" — eine Produktentscheidung |
| **OQ-5** | Ist der v1-Schnitt akzeptiert: v1 liefert **Builder-Default + genau einen spawnbaren Orchestrator**; **Multi-Instanz ist P3**? | **Ja** — und P3 ist der **unmittelbar nächste Schritt**, kein offenes Ende | Der Schnitt erlaubt ein früh grünes, byte-identisches v1 und entkoppelt zwei Risiken (Byte-Identität vs. Zustands-Isolation). Die Alternative (P3 in v1) macht AC-8/AC-9/AC-17-Singleton zur v1-DoD und koppelt den riskanten Teil an den sicheren |

---

## 16. Unverifiziert (explizit)

1. **Stand `95756dfe` / clean tree** — BRIEF, nicht selbst geprüft (kein
   Shell-Zugriff in dieser Runde).
2. **Opencode: ist eine `mode: primary`-Rolle zusätzlich per
   `task(subagent_type: "orchestrator")` aufrufbar?** Das ist die Umkehrung von
   #1006 Variante B; nirgends belegt. Entscheidet, ob Opencode `hybrid` echtes
   `yes` bekommt (v1: nein).
3. **Claude: Ist `claude --agent orchestrator` wirklich ein "Primary" im Sinne
   dieser Definition** (gleicher Kontext wie der Main Chat, gleiche
   Hook-Payload-Semantik, Prompt-Caching)? Nur der Hint-Text belegt den Aufruf,
   nicht die Kontext-Identität.
4. **Codex `main_agent_selectable`** ist in `provider-capabilities.yaml` selbst
   als UNVERIFIED markiert; die Matrix ist deshalb konservativ `no`.
5. **Mammouth `primary`** (OpenCode-Fork mit `mode: primary`/`default_agent`)
   ist nicht belegt.
6. **KimiCode: exakter Auswahlmechanismus** für `main_agent_selectable: true`
   (CLI-Flag? Config-Feld?) in dieser Runde nicht geprüft.
7. **Gemini/Antigravity: können mehrere `define_subagent`-Registrierungen
   derselben Rolle mit unterschiedlichen Instanz-IDs koexistieren?** Für die
   Zustands-Namespaces irrelevant (Identität ist Envelope + Dateiname), für die
   Audit-Aussage relevant.
8. **Liefert irgendein Provider eine *Liste* laufender Instanzen?** Ohne sie ist
   die Duplikat-Erkennung Main-Chat-Prompt-Pflicht (§9.1) statt Runtime-Check.
9. **`sync --check`-Byte-Identität nach rein additiven Schema-Keys** — plausibel
   (Schema wird nicht in Projekte emittiert), aber erst durch AC-6 belegt.
10. **Akzeptiert `--validate` heute unbekannte `orchestrator.*`-Keys**
    (`additionalProperties: true`, S10) — angenommen, nicht mit einem Lauf
    geprüft.
11. **`viz-report`-Verhalten bei unbekannten Event-Feldern** (`viz-logger` /
    `viz-report` nicht im Detail gelesen).
12. **Prompt-Caching / Main-Loop-Identität** für alle Provider (§3.1) — kein
    Capability-Key vorhanden; vor einem `primary`-Zell-Upgrade zu belegen.

**Summe: 22 unverifizierte Posten** — 12 Sachverhalte (§16.1–12) + 10
`hybrid`-Matrix-Zellen (`topology_verified_state.hybrid: UNVERIFIED`). Die zwei
unverifizierten `primary`-Zellen (Codex, Mammouth) sind in Nr. 4/5 enthalten,
nicht zusätzlich gezählt. Davon sind 10 durch die konservative Auflösung für v1
**entschärft** (kein Versprechen, laute Degradierung); die restlichen 12
blockieren v1 nicht, sind aber vor einem Zell-Upgrade zu belegen.

---

## 17. Übergabe an die Spec

- **Trace-Anker:** `spec-id: SPEC-orchestrator-topology-2026-11-03` (unverändert
  übernehmen).
- **Spec-Input:** D1–D10 (Entscheidungen), §4 (Interface Contracts), §7
  (Matrix als normative Tabelle, inkl. Zählung und `UNVERIFIED ⇒ no`), §9
  (Multi-Instanz-Vertrag inkl. 4-Feld-Audit), §11 (Phasen), §12 (ACs).
- **Nicht** in die Spec zu übernehmen: offene Fragen als Fakten, unverifizierte
  Matrix-Zellen als `yes`, P0-Evidenz als bereits erbracht.
- **A9 (Governance):** `consistency/spec_plan.py::_classify` ordnet
  `*-design.md` als **spec** ein und verlangt die literalen Überschriften
  (`## Problem`, `## Ziel`, `## Nicht-Ziele`, `## Interface Contracts`,
  `## Datenfluss`, `## Acceptance Criteria`, `## Offene Fragen`,
  `## Trace-Anker`). Dieses Design-Dokument nutzt die numerierte Struktur und
  erzeugt daher ~8 Section-Findings unter `--validate-spec-plan`; das ist
  **WARNING-only**, weil die aktive DoD `rapid-prototyping`
  `spec-plan-required: false` setzt. Die **abgeleitete Spec** (Stage
  `specify`) MUSS die literalen Überschriften tragen — dann ist
  `--validate-spec-plan` für sie grün.
- **Freigabe:** `concept-reviewer`; dieses Dokument bleibt `Status: Entwurf`.


