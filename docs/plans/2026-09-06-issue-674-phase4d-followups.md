# Phase 4d SE-Cascade Follow-ups & Design-Artefakte (Issues #207, #548, #452, #534, #317, #318)

| | |
|---|---|
| **Date** | 2026-09-06 |
| **Status** | Documentation — Phase-4d-Teilumsetzung dokumentiert; verbleibende Arbeit als issue-template-ready Follow-ups konsolidiert |
| **Roadmap** | `docs/plans/2026-09-05-issue-674-roadmap.md` — Phase 4d "SE Cascade (P4)" (Zeile 122) |
| **Issues** | #207 · #548 · #452 · #534 · #317 · #318 (Sektionsreihenfolge) |
| **Related** | Design-Docs (dieselbe Phase, eigenständige Dateien): #329 → `docs/se-cascade/se-baseline-change-control-design.md` · #330 → `docs/se-cascade/se-metrics-design.md`. Struktur-Präzedenz: `docs/plans/2026-09-06-issue-674-phase4b-harness-dependencies.md` |

## 0. Scope boundary

agent-meta ist ein statischer Datei-Generator. Er kontrolliert **Templates / Configs / Rules / Lib / Doku**
und hat **keine Runtime-Kontrolle** über Subagent-Dispatch, LLM-Ausführungsschleifen, Token-Zählung oder
Browser-Test-Umgebungen. Alles, was ein agent-meta-Artefakt zur Laufzeit nicht selbst ausführen kann,
wird unten als **Harness-seitige Abhängigkeit** mit konkreten, issue-fertigen Follow-up-Items dokumentiert —
nicht hier implementiert. Zwei der sechs Issues (#317, #318) tragen zusätzlich einen
**Umgebungs-Constraint** dieses Workspaces: `tests/browser/*` bricht im Setup, weil `pytest_socket`
den vom `admin_server`-Fixture gestarteten Subprozess blockiert (Details §5). Neue Browser-Tests
konnten in diesem Lauf daher nicht grün validiert werden — sie werden als **Test-Spec** ausgeliefert,
nicht als implementierte Suite.

---

## 1. Issue #207 — SE-Runner / autonome MBSE-Engine

### Umgesetzt in agent-meta (Phase-1-Teilansatz)

- `scripts/run-cascade.py` (510 Zeilen): provider-agnostischer **Prompt-File-Generator** — der
  Modul-Docstring (Zeilen 2–5) definiert den Umfang exakt: "Generates structured prompt files for
  each SE stage that can be executed in any LLM environment (Gemini, Claude, Opencode, etc.)".
  Kein Agent-Dispatch, keine Rekursion, kein Budget-Code.
- **9 Stufen** in `SE_STAGES` (Zeilen 31–95): `l1-requirements`, `l1-critic`, `l2-architecture`,
  `l2-critic`, `interface-sync`, `termination-check`, `validation`, `verification`, `integration-test` —
  mit `input_from`-Verkettung und 4000-Zeichen-Kontext-Truncation (Zeilen 182–201, Truncation Zeile 195).
- Session-Management: `.se-cascade/<session-id>/` mit `prompts/`, `stage_*.md`-Outputs und
  `session.json` (Konstanten Zeilen 104–106, Meta-Schreibweise 128–155); Resume/Status/List/Clean-Flags
  (Usage Zeilen 7–13).
- Pipeline-Definition (Prompt-Ebene): `config/role-defaults.yaml` → `quality_pipelines.se-cascade`-Block
  mit Loop-Stufen (`generator` + `critic`, `max_iterations: 3`), conditional Termination
  (Stage `termination`, `type: agent_decision`), Implementation-Routing über 3 Developer-Tiers
  (Stage `implementation`) und V&V-`parallel_group` (Stage `validation`).

### Nicht umgesetzt (verifiziert)

- `scripts/se-runner.py` — **existiert nicht** (Repo-Glob: 0 Treffer).
- `scripts/lib/se/` — **existiert nicht** (Repo-Glob: 0 Treffer).
- **Limits-/Budget-Enforcement:** keine `SE_MAX_*`/`cost_limit`-Referenzen in `run-cascade.py`
  (Datei-Grep: 0 Treffer). Die Limits existieren ausschließlich als Prompt-Variablen:
  `config/role-defaults.yaml` → `se_variables`-Block (`SE_MIN_DEPTH: 2`, `SE_MAX_DEPTH: 6`,
  `SE_MAX_CRITIC_ITERATIONS: 3`, `SE_MAX_PARALLEL_CELLS: 4`, `SE_MAX_CELLS: 20`, `cost_limit_eur: 5`,
  `output_persistence: true`, `resume_pointer_path: .se-state.yaml`), registriert als bekannte
  Platzhalter in `scripts/lib/consistency/placeholders.py:86-87` — d. h. sie landen in Agent-Prompts,
  aber kein Code zählt Zellen/Tokens/EUR oder bricht hart ab.
- **Layout-Divergenz:** `run-cascade.py` persistiert nach `.se-cascade/<session>/` (Zeilen 104–106),
  die dokumentierte Persistenz-Konvention verlangt `docs/se/<projektname>/` + `.se-state.yaml`
  (`docs/se-cascade/se-resume-session.md:52-79`; REQ-SE-01/03 in `docs/REQUIREMENTS.md:41-45`).
  Zwei Resume-Mechanismen existieren parallel (`session.json` vs. `.se-state.yaml`).

### Issue-Seite (Stand laut Task-Envelope)

Label `wontfix`, Issue offen. Sehr detaillierte Spec: MVP mit 8 Akzeptanzkriterien, Phase 2
Full-Auto, 4 offene Designfragen (1. API vs. Payload, 2. Input-Format, 3. Registry-Backend,
4. Budget-Zählung).

### Follow-up items (issue-template ready)

- [ ] **`scripts/se-runner.py` MVP (Prompt-File-Executor)** — `Labels: enhancement, se-cascade, framework`
  Konsumiert die von `run-cascade.py` erzeugten Prompt-Files und dispatcht sie an generierte Agenten.
  Umfang: die 8 MVP-Akzeptanzkriterien aus #207; Budget-/Limits-Enforcement (**harte** Abbruch-Grenze im
  Runner-Code, nicht im Prompt — `SE_MAX_CELLS`, `SE_MAX_DEPTH`, `SE_MAX_CRITIC_ITERATIONS`,
  `cost_limit_eur` aus `se_variables`-Block in `config/role-defaults.yaml`). Referenz: #207, 4 offene Designfrage 4
  (Budget-Zählung). Acceptance: MVP-8-AK-Checkliste im Issue vollständig abgehakt; Limit-Verstoß bricht
  den Lauf deterministisch ab (Exit-Code + Grundmeldung), getestet ohne echten LLM-Call.
- [ ] **`scripts/lib/se/` Modul-Layer** — `Labels: refactor, se-cascade`
  Zell-Buchhaltung, Limits-Registry, Budget-Counter als stdlib-Module — testbar ohne LLM
  (Fixture-Pattern analog `tests/test_se_persistence.py`). Runner (`se-runner.py`) und
  `run-cascade.py` konsumieren dieselben Module. Referenz: #207 Phase 2 (Full-Auto-Vorbereitung).
- [ ] **Designfragen 1–3 aus #207 beantworten (RFC-Antwort, kein Code)** — `Labels: documentation, se-cascade`
  (1) API vs. Payload, (2) Input-Format, (3) Registry-Backend — je Entscheidung + Begründung als
  Issue-Kommentar in #207; Ergebnis-Auszug nach `docs/se-cascade/` (kann auf die Persistenz-/Schemas-Entscheidungen
  aus `docs/se-cascade/se-resume-session.md` und `schemas/se-*.json` referenzieren).
- [ ] **Layout-Vereinheitlichung `.se-cascade/` ↔ `docs/se/` + `.se-state.yaml`** —
  `Labels: chore, se-cascade` Entscheidung: Migration von `run-cascade.py` auf die
  `resume_pointer_path`-Konvention (`.se-state.yaml`, `se_variables` → `resume_pointer_path`
  in `config/role-defaults.yaml`) oder dokumentierte Dualität mit expliziter Abgrenzung.
  Acceptance: genau ein dokumentierter Resume-Pfad; die andere Variante entfernt oder als
  Legacy markiert.

---

## 2. Issue #548 — Meta-Agent-Manager RFC (Sammel-RFC)

### Stand

- **Sammel-RFC** mit Positionen **B1–B7 / C1–C5 / D1–D4**; Issue-Mandat:
  „Einzelmaßnahmen bitte mit Referenz auf die jeweilige B/C/D-Nummer ausklinken".
  Priorisierungstabelle und **3 offene Checkbox-Fragen** existieren im Issue.
  Verlinkte Einzel-Issues: **#540 → B6** (Context-Managed-Block, Phase-4a-Batch), **#547 → B5/C3**
  (Refactor, Phase-4c-Batch).
- **Repo-Seite:** #548 wird nur in der Roadmap referenziert
  (`docs/plans/2026-09-05-issue-674-roadmap.md:8,122`); ein B/C/D-Mapping existiert **nicht** im Repo
  (Grep über `docs/`: keine weitere Fundstelle).

### Zurückgestellt / Begründung

Phase 4d kann Einzelmaßnahmen nicht ausklinken, solange die **3 offenen Checkbox-Fragen** im Issue
unbeantwortet sind — sie blockieren die Einzel-Issue-Erstellung. Ausklinken ist Issue-Hygiene
(Metadaten-Arbeit im Tracker), kein agent-meta-Code-Artefakt. Parallel dazu existieren repo-seitig
bereits Lieferungen, die Teile der B/C/D-Liste vermutlich abdecken (#540, #547, Phase-4a/4b/4c-Artefakte) —
aber ohne Mapping bleibt unklar, welche Positionen noch eigenständige Tickets brauchen.

### Follow-up items (issue-template ready — Mandatskonform: jede Maßnahme trägt ihre B/C/D-Referenz)

- [ ] **B/C/D-Ausklink-Index erstellen** — `Labels: documentation, meta-rfc`
  Mapping-Tabelle über alle Positionen B1–B7, C1–C5, D1–D4: pro Position entweder
  „abgedeckt durch <Issue/PR/Doku-Datei>" (mit file:line-Evidenz) oder „neues Einzel-Issue nötig".
  Bekannte Anker: B6 → #540, B5/C3 → #547. Output: Kommentar in #548 + Ablage als
  `  docs/plans/2026-09-06-issue-548-bcd-index.md`. Acceptance: jede der 16 Positionen hat genau
  einen Zustand (abgedeckt mit Evidenz / offenes Einzel-Issue mit Link).
- [ ] **3 offene Checkbox-Fragen in #548 entscheiden** — `Labels: meta-rfc, decision`
  Je Frage eine begründete Entscheidung (Kommentar), danach Checkboxen abhaken. Blockiert die
  Einzel-Issue-Erstellung (siehe nächstes Item).
- [ ] **Einzel-Issues für ungemappte Positionen** — `Labels: je nach Position`
  Pro ungemappter B/C/D-Position ein Issue; Titel/Body-Muster: `Aus #548, Position <Bn|Cn|Dn>: <Kurztitel>`
  (erfüllt das Issue-Mandat wörtlich). Erst nach Abschluss der beiden vorigen Items.

---

## 3. Issue #452 — Release-Prozess-Templates je Projekttyp

### Umgesetzt in agent-meta

*(nichts — bewusst; das ist die deliverable-faithful Auslage des §F-Folge-Tickets)*

### Zurückgestellt / Begründung (mit Evidenz)

- `docs/concepts/2026-08-18-convention-profiles.md` — **§F „Issue #452 (Prozess je Projekttyp)"**
  (Zeile 202) stellt #452 explizit zurück: „**v1 baut NICHT:** Projekttyp-Prozessvarianten (#452 —
  separates, kleineres Folge-Ticket mit dem `{{#if PROJECT_TYPE_*}}`-Ansatz)" (Zeile 212).
  Begründung dort (Zeile 208): #452 betrifft *Workflow-Schritte* (Build-Artefakt ja/nein,
  npm-Publish ja/nein, GitHub-Release ja/nein), nicht *wie Dinge heißen* — Unterbringung im
  `conventions-presets.yaml`-Schema würde die Domain-Grenze verwischen, die Abschnitt A bewusst gezogen hat.
- Kontext (Zeile 8): der Release-**Prozess** ist hartkodiert und variiert real zwischen Projekttypen
  (Library vs. CLI vs. Web-App).
- v1-Scope von conventions-presets schließt #452 damit **by design** aus.

### Follow-up items (issue-template ready — exakt das §F-Folge-Ticket)

- [ ] **project-type release-process Templates** — `Labels: enhancement, conventions, templates`
  Scope (laut #452): (1) optionale `release:`-Sektion in `.meta-config/project.yaml` mit Projekttyp-Auswahl
  (library / cli / web-app / home-assistant); (2) Templates `docs/templates/RELEASE_PROCESS.<project-type>.md`
  inkl. Home-Assistant-PoC (Releases via HACS-Semantik, siehe bestehende HACS-Release-Naming-Blöcke in
  `rules/2-platform/hacs-integration-development.md` + `agents/2-platform/hacs-release.md`); (3) die
  6 Checkbox-Akzeptanzkriterien aus #452. Mechanik-Vorlage: der `{{#if VAR}}`-Conditional-Block-Mechanismus
  existiert bereits und ist getestet (`tests/test_optional_snippets_path_conditional.py` — unset-Variablen
  rendern den Block weg, gesetzte rendern ihn). Referenz: §F in
  `docs/concepts/2026-08-18-convention-profiles.md:202-212`.
  Acceptance: Sync eines `library`-Dummy-Projekts rendert RELEASE_PROCESS.library.md ohne
  `{{UPPERCASE}}`-Residue; Home-Assistant-PoC-Projekt rendert die HA-Variante; beide Varianten
  in `sync.py --validate` grün.

---

## 4. Issue #534 — HACS Platform Preset (bereits implementiert)

### Umgesetzt in agent-meta (verifiziert, alle Evidenzen file:line)

- **Test-Suite:** `tests/test_platform_hacs_preset.py` (812 Zeilen, Contract-Quelle:
  `docs/plans/hacs-platform-preset-audit.md` laut Modul-Docstring Zeilen 1–8). Aufbau:
  Tier 1 Config-Load (`TestTier1PlatformConfigLoad`, 6 Tests, Zeilen 275–389) · Tier 2 Collection/
  Role-Mapping (`TestTier2CollectionAndRoleMapping`, 9 Testfunktionen inkl. 1 parametrisiertem
  Test ×5 Agenten, Zeilen 399–501) · Tier 2b Release-Naming-Addendum
  (`TestTier2ReleaseNamingBlock`, 5 Tests, Zeilen 527–601) · Tier 3 Temp-Project-Sync
  (`TestTier3TempProjectSync`, 4 Tests, Zeilen 612–812). → **24 Testfunktionen, 28 gesammelte Testfälle**
  (Parametrisierung ×5 über `_HACS_AGENT_FILES`, Zeilen 140–146).
- **Audit/Contract:** `docs/plans/hacs-platform-preset-audit.md` (317 Zeilen, Stand 2026-08-29,
  Branch `feat/hacs-platform-preset` laut Kopf).
- **Doku:** `docs/CODEBASE_OVERVIEW.md` §16 „HACS Platform Preset" (Zeilen 2008–2049):
  Aktivierung via `platforms: [hacs]`, Artefakte, Composition-Kette (`extends` + `patches`,
  Meta-Keys werden gestrippt, `agents.py:910-911`).
- **Artefakte:** `platform-configs/hacs.defaults.yaml` (5 Keys) ·
  `rules/2-platform/hacs-integration-development.md` (ohne Frontmatter, Skill-Quelle) ·
  `config/rules-presets.yaml` → `presets.lazy.integration-development` (`channel: skill`) ·
  5 Agent-Overrides `agents/2-platform/hacs-{code-reviewer,developer,devops-engineer,release,tester}.md`.
- Branch `feat/hacs-platform-preset` ist gemerged (laut Task-Envelope).

### Korrektur gegenüber der Vorauswertung

`docs/CODEBASE_OVERVIEW.md:2010,2029` meldet „19 Testfunktionen → 23 Testfälle" — das ist **stale**:
nach dem Tier-2b-Release-Naming-Addendum (Modul-Docstring Zeilen 34–37) sind es aktuell
**24 Testfunktionen → 28 Testfälle**. Der Zähler im Overview ist ein Doku-Hygiene-Follow-up (unten).

### Follow-up items (issue-template ready)

- [ ] **#534 verifizieren und schließen** — `Labels: verification`
  Schließ-Kommentar mit Evidence-Liste (obige 4 Evidenzblöcke) + Testlauf-Nachweis:
  `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_platform_hacs_preset.py -q`
  (Plugin-Autoload-Hinweis steht im Modul-Docstring, Zeilen 10–13). Schließen via
  PR-Issue-Keyword-Konvention (`Closes #534`) oder direkte Close-Aktion mit Kommentar.
- [ ] **CODEBASE_OVERVIEW-Testzähler korrigieren** — `Labels: documentation, chore`
  `docs/CODEBASE_OVERVIEW.md:2010,2029`: „19 Testfunktionen → 23 Testfälle" →
  „24 Testfunktionen → 28 Testfälle (1 parametrisiert ×5, Tier-2b-Release-Naming-Addendum inklusive)".

---

## 5. Issue #317 — viz-dashboard iframe E2E (nicht implementiert; Test-Spec)

### Stand (verifiziert)

- **Kein Test existiert:** `tests/browser/` enthält 7 Testdateien (plus `conftest.py`, `__init__.py`,
  34 Testfunktionen gesamt) — **null** Treffer für `viz-dashboard`, `subserver`, `iframe`
  (Grep über `tests/browser/`: 0 Fundstellen).
- **Testziel existiert:** die Admin-UI-Page rendert das Viz-Dashboard als iframe-Embed mit
  Subserver-Controls — `docs/ui/admin-ui.html:8071` (`viewVizDashboard`), iframe-Embed-Area
  (Kommentar Zeile 8085: „Embed area — iframe (running) or placeholder (stopped)"),
  Start/Stop/Restart-Controls pro Subserver (Zeilen 8095–8115), Route `/viz-dashboard`
  (Zeile 9789), Sidebar-Eintrag (Zeile 1555).

### Umgebungs-Constraint (dieser Workspace)

`tests/browser/conftest.py` startet den admin-server als **Subprozess** auf Port 7421 und pollt
HTTP bis zur Antwort (Fixture `admin_server`, Zeilen 45–71; `_wait_for_server` Zeilen 31–42).
In dieser Umgebung blockiert `pytest_socket` diesen Netz-/Subprozess-Pfad — **28 der 34
Testfunktionen** (alle, die `browser_ctx`/`admin_server` konsumieren) brechen bereits im Setup.
*(Vorauswertung sprach von „29 ERROR" — statische Zählung ergibt 28 `browser_ctx`-abhängige
Funktionen; ein pytest-Lauf zur exakten ERROR-Zählung war in dieser Umgebung nicht möglich.)*
Konsequenz: neue Browser-Tests konnten hier nicht grün validiert werden → Auslieferung als
**Test-Spec**, Implementierung in einer Umgebung mit erlaubtem localhost-Socket.

### Follow-up items (issue-template ready)

- [ ] **Test-Spec: viz-dashboard iframe E2E** — `Labels: enhancement, testing, e2e`
  Cases (Playwright-Suite in `tests/browser/`, `browser_ctx`-Fixture):
  (1) bei laufendem Viz-Subserver: iframe-Embed sichtbar und geladen;
  (2) bei gestopptem Subserver: Placeholder-Panel statt iframe;
  (3) Start → Status-Dot wechselt auf „running", iframe erscheint;
  (4) Stop → iframe entfernt, „stopped";
  (5) Restart überlebt einen in-flight Click (Guard `inFlight`, `admin-ui.html:8092`);
  (6) Status-Dots korrekt für beide Subserver (viz + MCP, Zeilen 8115 ff.).
  Acceptance: 6 Cases grün in einer Umgebung mit erlaubtem localhost-Socket.
- [ ] **pytest_socket-Ausnahme für den Test-Server** — `Labels: testing, ci`
  Konfigurationsebene (pyproject/pytest-Addopts oder Fixture-Marker), die dem
  `admin_server`-Fixture in `tests/browser/conftest.py:45-71` localhost-Bind auf 7421 erlaubt.
  Ohne diese Vorbedingung bleiben #317/#318-Suiten in jedem gesockelten Lauf rot.
  Acceptance: volle `tests/browser/`-Suite läuft (28 browser_ctx-Tests) ohne Setup-ERROR.

---

## 6. Issue #318 — Admin-UI Form-Editor Browser-Tests (teilweise; Gap-Analyse + Test-Spec)

### Abgedeckt (verifiziert)

- **Generic-Dict-Editor (Rename-Kollisionen):**
  `tests/browser/test_dict_editor_rename_collision.py` (190 Zeilen, 4 Tests): Header-Rename auf
  existierenden Key abgelehnt (Zeile 19), Rename auf leeren Key abgelehnt (Zeile 56),
  Provider-Option-Rename (Zeile 88), Env-Var-Rename (Zeile 134). Deckt `/project/plugin-overrides`
  (Zeile 23) und `/project/providers` (Zeile 96) ab.
- **Models-Page:** `tests/browser/test_models_page.py` (13 Tests, Zeilen 26–441) inkl.
  Provider-Filter-Strip, Toggle-Verhalten, Source-Provenance, modelsdev-Override-Regression.
- **Orchestrator-Page nur als Smoke:** `tests/browser/test_admin_ui_consistency_p1.py:74`
  (Save wirft nicht) und `:44` (entfernte Handoff-Keys haben keine Rest-Form-Controls).

### Nicht abgedeckt (Gap, verifiziert)

- **`/project/orchestrator` Handoff-Toggles:** Page existiert (`viewProjectOrchestrator`,
  `docs/ui/admin-ui.html:9798`); funktionale Toggle-Tests (Toggle → Persistenz → Re-Render) fehlen.
- **`/project/model-overrides` Tabellen-Editor:** Page existiert (`viewProjectModelOverrides`,
  `docs/ui/admin-ui.html:9801`); kein Test.
- Serverseitiges Write-Gate als Testziel: `_write_project_section` mit allowed-Set
  (`scripts/admin-server.py:4603-4631`, erlaubte Sektionen inkl. `orchestrator`, `model-overrides`
  in Zeilen 4614–4623) + `_guard_model_block_write` (Zeile 4633 ff.) — die Reject-Pfade des Guards
  sind browserseitig ungetestet.

### Umgebungs-Constraint

Identisch zu §5: `pytest_socket` blockiert das `admin_server`-Fixture — die folgenden Specs
werden in einer socket-erlaubten Umgebung implementiert (Vorbedingung: pytest_socket-Follow-up in §5).

### Follow-up items (issue-template ready)

- [ ] **Gap-Test-Spec: orchestrator handoff-toggles E2E** — `Labels: enhancement, testing, e2e`
  Cases: (1) Toggle an → `POST` Sektion `orchestrator` → Wert in `.meta-config/project.yaml`
  persistiert (Fixture-Server schreibt in ein temp-Workspace); (2) Toggle aus → Key entfernt;
  (3) Serverseitige Guard-Rejection (`_guard_model_block_write`) erzeugt sichtbaren Fehler-Toast
  und lässt den UI-State unverändert; (4) Re-Render nach Save zeigt gespeicherten Zustand.
  Acceptance: 4 Cases grün in socket-erlaubter Umgebung.
- [ ] **Gap-Test-Spec: model-overrides Tabellen-Editor E2E** — `Labels: enhancement, testing, e2e`
  Cases: (1) Override pro Rolle/Provider anlegen → persistiert in Sektion `model-overrides`;
  (2) Override entfernen → Vererbung (`lib/roles.py::resolve_model`, `scripts/lib/roles.py:159`)
  greift wieder; (3) invalider Tier-Wert → UI-Rejection ohne Korruption; (4) `model-override-all`-
  Kollisionsfall → Guard-Rejection (Konflikt-Semantik analog `_guard_model_block_write`).
  Acceptance: 4 Cases grün; bestehende Dict-Editor-Suite bleibt unverändert grün.

---

## 7. Cross-issue Abhängigkeiten

| Thema | Betrifft | Besitzer fehlendes Stück |
|---|---|---|
| **pytest_socket/conftest-Blocker** (localhost-Subprozess-Server) | #317, #318 (beide Browser-Suiten) | Test-Infrastruktur (Config-Änderung in `tests/browser/conftest.py`/pytest-Konfiguration); Vorbedingung für alle Browser-Specs |
| **Harness-Grenze Runner** (Dispatch, Token-Zählung, Budget-Abbruch zur Laufzeit) | #207 — analog zum Phase-4b-Muster (`docs/plans/2026-09-06-issue-674-phase4b-harness-dependencies.md` §0) | Harness/Runner (`scripts/se-runner.py` als künftiger In-Repo-Runner schränkt die Grenze ein) |
| **Issue-Hygiene-Kette** | #534 (schließen) → #548 (B/C/D ausklinken) → #452 (§F-Folge-Ticket erstellen) | Issue-Tracker-Arbeit, kein Code |
| **Design-Verdrahtung #329 ↔ #330 ↔ #207** | Baseline-Freeze stabilisiert den RVI (#330 braucht #329-CR-Historie für exakte Werte; bis dahin Review-Protokoll-Proxy per Taxonomie #334) · Budget-Zählung ist Runner-Sache (#207), #330 berichtet nur · #330-Gaps==0 ist Freeze-Vorbedingung (#329) | Design-Seite abgeschlossen (2 Design-Docs, siehe Header) — Implementierung durch die Do-Not-Implement-Klauseln der Issues #329/#330 gesperrt |
| **SE-Cascade deaktiviert** | Alle SE-Items (#207, #329, #330): Pipeline per `.meta-config/project.yaml` → `quality-pipelines.overrides.se-cascade.enabled: false` (bewusste Entscheidung, Issue #652; `docs/architecture/07-se-cascade.md:7-10`) | Reaktivierung nur auf explizite Anfrage |

## 8. Korrekturen gegenüber der Vorauswertung (Recon)

1. **#534-Testanzahl:** „23 cases" → tatsächlich **24 Testfunktionen / 28 gesammelte Testfälle**
   (Parametrisierung ×5; Tier-2b-Addendum nach dem Overview-Eintrag; §4).
2. **#317-ERROR-Anzahl:** „29 ERROR at setup" → statisch **28 browser_ctx-abhängige** der 34
   Testfunktionen; exakte pytest-ERROR-Zählung in dieser Umgebung nicht reproduzierbar (§5).
3. Bestätigt ohne Korrektur: `run-cascade.py` 510 Zeilen / 9 Stufen; `scripts/se-runner.py` und
   `scripts/lib/se/` fehlen; #452-§F-Deferral (`convention-profiles.md:202-212`); #534-Artefakte
   inkl. `docs/CODEBASE_OVERVIEW.md` §16 (exakt Zeile 2008–2010); null viz-dashboard-Tests;
   `test_dict_editor_rename_collision.py` deckt Providers/Plugin-Overrides ab.
