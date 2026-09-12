# Literature-Anchored Agent Improvements — Triage & Implementation Plan (#769–#780)

## STATUS

- **Date:** 2026-09-12
- **HEAD:** `5db4bbd5`
- **VERSION:** 1.1.0
- **Mode:** Plan — keine Implementierung. Dieses Dokument ist die einzige Änderung; keine Templates, Configs, Skripte, Commits oder Git-Operationen.
- **Batch:** #769, #770, #771, #772, #773, #774, #775, #776, #777, #778, #779, #780 (12 Issues, Label `audit-2026-09`).
- **Sammel-Branch (Ziel):** `feat/literature-agent-improvements`
- **Quelle:** GitHub-API via `webfetch` (`https://api.github.com/repos/Popoboxxo/agent-meta/issues/769` … `/780`) — alle 12 Issues vollständig gelesen (Stand 2026-09-12).
- **Decision-Log-Umfang:** #769–#777 = **244 Bullets / 243 Literature-Vorschläge** über 9 Rollengruppen; #778 (6 Findings) + #779 (7 Findings) + #780 (3 Optionen) = 16 zusätzliche Design-/Routing-Items.
- **Gesamt-Verteilung (243 Vorschläge):** **accept 208 · modify 27 · reject 1 · duplicate 7**.
- **Design-Gate-Top-3:** (1) #780 Sprachrouting → **Option C**; (2) #778-F1 Referenzstandards → **neues optionales Frontmatter-Feld `reference_standards`**; (3) #778-F2 Boundary-Platzierung → **Routing-Boundaries zentral, nur Self-Constraints im Template**.
- **Design-Gate-Status (2026-09-13):** Alle 9 User-Entscheidungen (D1–D9) verbindlich bestätigt — keine offenen Punkte (§3/§7).
- **Ziel-VERSION (WP13):** **1.2.0** (Minor, D9 — neue optionale Felder/Sektionen).
- **Modus der Triage:** Policy-basiert (siehe Scope/Method). `accept` = konkreter, prüfbarer Vorschlag ohne Duplikat; `modify` = sinnvoll, aber anderer Zielpfad/enge Reformulierung nötig; `reject` = kein Prüfanker / widerspricht Konventionen; `duplicate` = auf HEAD bereits erledigt oder obsolet.

---

## Scope/Method

- **Scope:** STRIKT #769–#780. **Keine** angrenzenden Issues (#528, #552, #264, #540, #346, #360 etc. sind nur Referenzen/Präzedenz, kein Scope).
- **Method:**
  1. Alle 12 Issues per GitHub-API vollständig gelesen (Body).
  2. Jeder Vorschlag gegen den Ist-Zustand von HEAD `5db4bbd5` abgeglichen (verifizierte Dateien siehe unten).
  3. Triage-Klassen über eine feste Policy (unten) vergeben; Cluster-Aggregation je Rolle nur, wo Vorschläge gleichartig sind, mit positional sichtbarer Klassen-Zuordnung.
  4. Cross-Cutting-Findings (#778/#779/#780) als eigenständige Design-Gate-Entscheidungen vor die Per-Role-Edits gezogen.
- **Triage-Policy:**
  - `accept` → konkret, prüfbar, passt in 1-generic-Template/Config, kein Duplikat auf HEAD.
  - `modify` → Nutzen anerkannt, aber Zielort/Form anders: z. B. Review-Regel → `config/review-rules/<domain>.yaml` statt Template-Prosa (#778-F3); Routing-/Boundary-Aussage → `config/role-defaults.yaml` statt Template (#778-F2); Prozess-/Tooling-Abhängigkeit → optionaler Hinweis statt Mandat.
  - `reject` → keine Messgröße/kein Prüfanker, Mandat für Dinge außerhalb der Framework-Kontrolle, oder Widerspruch zur provider-agnostic-Policy/Konvention.
  - `duplicate` → auf HEAD bereits implementiert/dokumentiert (mit Beleg).
- **Verifizierter Ist-Zustand (Spot-Checks, HEAD `5db4bbd5`):**
  - `config/role-defaults.yaml`: 84 Rollen; `openscad-developer` (Z. 803) hat **kein** `routing`/`routing_patterns` → IT-1 bestätigt. `principal-developer` (Z. 147) hat nur `parallel/orchestrator_only`. `provider-expert` hat **keinen** Eintrag.
  - `agents/1-generic/`: 80 Rollen-Templates (inkl. `provider-expert.md`); `provider-expert` ist via `scripts/lib/frontmatter.py:44` (`WRAPPER_TEMPLATES`) und `scripts/lib/config_audit.py` als **Wrapper-Base, nicht selektierbare Rolle** dokumentiert; `CHANGELOG.md:46` bestätigt „documented `provider-expert` as a wrapper base (not a selectable role)" (#736/WP5). → #778-F6-Orphan und #779-IT-2 sind **duplicate**.
  - `config/review-rules/`: 5 Domänen — `frontend.yaml` (FE-01…FE-06, inkl. FE-03 „SSR/hydration safety"), `backend.yaml`, `database.yaml`, `ui.yaml`, `security.yaml` (SEC-01…SEC-06 mit OWASP-/CWE-`standard_ref`). Kein ID-Schema für code-/concept-/accessibility-/dependency-Rollen.
  - `scripts/lib/delegation_table.py:97` `get_routing_rules()`: Fallback `routing_patterns.keywords` → legacy `routing.intent_keywords`; `examples` werden unverändert (sprach-agnostisch) emittiert. **Keine Sprachvariable im Generator.** `scripts/lib/agents.py:224` `build_routing_tool_definition()` emittiert `keywords`+`examples` provider-neutral.
  - `tests/test_routing_tool_definitions.py`: `test_roles_without_routing_stay_patternless` schreibt `openscad-developer` explizit als patternlos fest; `test_role_defaults_routing_patterns_match_intent_keywords` erzwingt `routing_patterns.keywords == routing.intent_keywords` (301 Keywords, ~29 deutsch). Keine Coverage-/Overlap-Prüfung.
  - `scripts/consistency-check.py` + `scripts/lib/consistency/` = zentraler Consistency-Runner; `python3 scripts/sync.py --validate` als Basischeck.
  - Contract-Ratchet: `tests/test_contract_labels.py` (Exception-Registry als Ratchet) + Block-Budget-Ratchet in `tests/test_context_compact_mode.py` — beide bei Template-Wachstum betroffen.
- **Skills-Kontext herangezogen:** `architecture` (0/1/2/3-Schichten, Composition/Instruction-Bleed), `sync-interface` (Branch-Pflicht bei sync/Template-Änderungen, `--check`), `conventions` (Versions-Bump, neuer Placeholder/Rolle, Change-Checkliste), `provider-agnostic` (keine `if provider ==`-Logik; Capability-Flags).
- **Out of scope:** Implementierung, Issue-/PR-Mutation, Wiki/CHANGELOG/index-Updates, Git-Operationen.
- **Nicht verifizierbar / gekennzeichnet:** Ob einzelne Formulierungen bereits wortgleich in jedem der 80 Templates stehen, wurde stichprobenartig (nicht vollständig) geprüft. Wo „accept" trotz möglicher Teil-Überlappung steht, ist das als „dedupe beim Edit prüfen" markiert. Externe Literatur-/URL-Claims wurden **nicht** erneut HTTP-geprüft — die Quellenangaben stammen aus den Issues.

---

## 1. Per-Issue-Triage (#769–#780)

**Legende Klasse:** `A` = accept · `M` = modify · `R` = reject · `D` = duplicate.
**Spalten `S1…Sn`** = Issue-Bullets in Reihenfolge; Position entspricht der Klasse. Quellen/URLs je Vorschlag stehen im jeweiligen Issue (verlinkt in der Tabelle). `Zielpfad` = primärer Änderungsort.

### 1.1 #769 — Core development roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/769))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | S4 | S5 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|---|---|
| `orchestrator` | complexity-gate; decentralized-path; subagent-contract-line; disjoint-sources-fanout; routing-gate-target-desc | A | M | M | A | A | `agents/1-generic/orchestrator.md`, `config/role-defaults.yaml` | M | 3/2/0/0 |
| `developer` | small-self-contained-commits; self-review-before-done; read-generated-change; context-switch-criterion | A | A | A | M | — | `agents/1-generic/developer.md`, `rules/1-generic/commit-conventions.md` | S | 3/1/0/0 |
| `junior-developer` | debugging-techniques; focus-seriality; read-surrounding-code | A | A | A | — | — | `agents/1-generic/junior-developer.md` | S | 3/0/0/0 |
| `senior-developer` | repro-failing-test-fix; tech-debt-tradeoff; twelve-factor-checklist | A | A | M | — | — | `agents/1-generic/senior-developer.md` | S | 2/1/0/0 |
| `principal-developer` | experiment-fault-isolation; regression-test-pins-rootcause; lessons-postmortem | A | A | A | — | — | `agents/1-generic/principal-developer.md` | S | 3/0/0/0 |
| `explorer` | read-strategy-as-needed; call-graph-querying; coverage-field | A | M | A | — | — | `agents/1-generic/explorer.md` | S | 2/1/0/0 |
| `git` | recovery-revert-amend-reflog; branching-model-options; breaking-change-multiple-commits; signed-commits-tags | A | M | A | M | — | `agents/1-generic/git.md`, `rules/1-generic/commit-conventions.md` | S | 2/2/0/0 |
| `release` | changelog-schema; semver-increments; deprecation-workflow; artifact-commit-coupling | A | A | A | A | — | `agents/1-generic/release.md`, `scripts/lib/conventions.py` | M | 4/0/0/0 |
| `docker` | rebuild-freshness-pull; image-security-scan; reproducible-tags; build-vs-runtime | A | M | A | A | — | `agents/1-generic/docker.md` | S | 3/1/0/0 |

**Netto #769: A 25 · M 8 · R 0 · D 0 (33).**

**Decision-Log #769 (Nicht-`accept`-Fälle):**
- `orchestrator/S2` decentralized/group-chat → **modify**: nicht als Pfad implementieren, sondern als „unsupported by design; centralized routing only" **dokumentieren** (vermeidet unklare Erwartung).
- `orchestrator/S3` Subagent-Contract-Zeile → **modify**: nicht in jeden Worker, sondern als Pflichtfeld der Delegation (`role-defaults`/Delegations-Contract) ergänzen; Templates haben bereits „Worker role"-Sätze (Dedupe beim Edit prüfen).
- `developer/S4` context-switch criterion → **modify**: nur mit prüfbarem Kriterium (z. B. „neue Session nach Kontextwechsel/Fehlerspur") aufnehmen, sonst reine Heuristik ohne Anker.
- `senior-developer/S3` Twelve-Factor-Checkliste → **modify**: nicht Checkliste inline duplizieren, sondern als `reference_standard` (Design-Gate D2) referenzieren.
- `explorer/S2` call/dependency-graph → **modify**: auf vorhandenes `graphify` (Repo-Tool) referenzieren statt neues Tooling zu fordern.
- `git/S2` branching-model options → **modify**: `--no-ff`/release/hotfix als **optionale** Projektkonvention, nicht generisches Mandat.
- `git/S4` signed commits/tags → **modify**: optionale Capability/Projektentscheidung, nicht generischer Default (Schlüssel-/CI-Abhängigkeit).
- `docker/S2` image security scan → **modify**: optionaler Pre-Release-Gate-Hinweis (`trivy`/`docker scout`), keine harte Abhängigkeit.
- `release/S1–S4` → **accept**: Keep-a-Changelog/SemVer/Deprecation/Artifact-Coupling sind prüfbar; Kollision mit `scripts/lib/conventions.py` beim Edit prüfen (Dedupe).

### 1.2 #770 — Product & planning roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/770))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | S4 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|---|
| `feedback` | duplicate-precheck; issue-form-required-fields; pre-submit-check | A | A | A | — | `agents/1-generic/feedback.md` | S | 3/0/0/0 |
| `requirements` | user-story-form-ac; nfr-category; elicitation-step; req-metadata-baseline | A | A | A | A | `agents/1-generic/requirements.md`, `docs/REQUIREMENTS.md` | M | 4/0/0/0 |
| `ideation` | risky-assumptions-cheapest-test; opportunity-view; pivot-kill-criterion; min-divergence-3 | A | A | A | A | `agents/1-generic/ideation.md` | S | 4/0/0/0 |
| `planner` | replanning-assumptions; review-test-gate-per-step | A | D | — | — | `agents/1-generic/planner.md` | XS | 1/0/0/1 |
| `product-manager` | discovery-step; story-outcome-metric; market-competitor-check | A | A | M | — | `agents/1-generic/product-manager.md` | S | 2/1/0/0 |
| `effort-estimator` | uncertainty-band; delphi-consensus; task-catalog-overridable | A | A | A | — | `agents/1-generic/effort-estimator.md` | S | 3/0/0/0 |
| `bug-feature-analyzer` | duplicate-check; enforce-required-fields; label-sla-governance | A | M | M | — | `agents/1-generic/bug-feature-analyzer.md` | S | 1/2/0/0 |
| `export-manager` | idempotency-keys; target-validation; token-rotation-audit | A | A | M | — | `agents/1-generic/export-manager.md` | M | 2/1/0/0 |
| `meta-feedback` | flywheel-loop; duplicate-priority-check; dor-feat-design | A | A | A | — | `agents/1-generic/meta-feedback.md` | S | 3/0/0/0 |
| `app-lifecycle-governor` | portfolio-inventory-debt; sla-sli-coupling; deprecation-exit-archive | A | A | A | — | `agents/1-generic/app-lifecycle-governor.md` | S | 3/0/0/0 |
| `intern-developer` | router-exclusion | A | — | — | — | `config/role-defaults.yaml` (Routing) | XS | 1/0/0/0 |

**Netto #770: A 27 · M 4 · R 0 · D 1 (32).**

**Decision-Log #770:**
- `planner/S2` review/test-gate per step → **duplicate**: Der Planner-Contract fordert pro Schritt bereits eine messbare Acceptance-Criterion (`planner.md`-Output-Tabelle). Kein neues Gate nötig; Re-Planning-Punkt (`S1`) bleibt accept.
- `product-manager/S3` market/competitor check → **modify**: optionaler, klar begrenzter Hinweis (kein Marktforschungs-Mandat).
- `bug-feature-analyzer/S2` Pflichtfelder erzwingen statt `UNCLEAR` → **modify**: Widerspruch zur Triage-Aufgabe — stattdessen „needs-info"-Rückfragepfad statt erzwungenem Default; `S3` SLA-Governance → **modify** (Label-Schema ja, SLA-Definition außerhalb Rollenkontrolle).
- `export-manager/S3` token rotation + audit log → **modify**: Audit-Log ja, Rotation als Sicherheitskonfigurations-Hinweis (kein Runtime-Mandat); `S1/S2` accept.
- `intern-developer` → **accept (Router-Exclusion)**: expliziter Ausschluss in `config/role-defaults.yaml`/Routing-Gate (easter-egg darf nie selektiert werden). Dies ist der einzige Nicht-Literatur-Bullet in #770 (Routing-Safety); er zählt als Vorschlag.

### 1.3 #771 — Testing & V&V roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/771))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|
| `tester` | test-size-guideline; determinism-rule; behavioral-coverage | A | A | A | `agents/1-generic/tester.md` | S | 3/0/0/0 |
| `e2e-tester` | e2e-count-guideline; flakiness-quarantine; visual-baseline-governance | A | A | A | `agents/1-generic/e2e-tester.md` | S | 3/0/0/0 |
| `test-executor` | flakiness-triage; deterministic-env; failure-classification | A | A | A | `agents/1-generic/test-executor.md` | S | 3/0/0/0 |
| `validator` | dod-vs-ac; traceability-matrix; nfr-in-dod | A | A | A | `agents/1-generic/validator.md` | M | 3/0/0/0 |
| `se-verifier` | verification-method-catalog; rigor-integrity; coverage-report | A | A | A | `agents/1-generic/se-verifier.md` | M | 3/0/0/0 |
| `se-validator` | user-journey-catalog; realistic-acceptance; journey-l1-coupling | A | A | A | `agents/1-generic/se-validator.md` | M | 3/0/0/0 |
| `se-test-engineer` | technique-catalog; model-coverage; integration-determinism | A | A | A | `agents/1-generic/se-test-engineer.md` | M | 3/0/0/0 |
| `se-testreviewer` | fault-detection-assessment; boundary-coverage-quant; negative-path-quota | A | A | M | `agents/1-generic/se-testreviewer.md` | S | 2/1/0/0 |
| `se-integration-and-test-manager` | strategy-rationale; iso-29119-2; vv-report-mandatory | A | A | A | `agents/1-generic/se-integration-and-test-manager.md` | M | 3/0/0/0 |

**Netto #771: A 26 · M 1 · R 0 · D 0 (27).**
- `se-testreviewer/S3` negative-path quota → **modify**: als **Metrik/Report-Feld**, nicht als starre Quote (Quoten sind gaming-anfällig).
- SE-V&V-Referenzen (IEEE 1012/29119-2/29119-4/ISTQB) → **accept**, aber als `reference_standards` (D2) statt Inline-Katalog (Dedupe beim Edit).

### 1.4 #772 — Systems-Engineering (V-Modell) roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/772))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|
| `se-requirements` | elicitation-catalog; quality-gate; nfr-l1 | A | A | A | `agents/1-generic/se-requirements.md` | M | 3/0/0/0 |
| `se-architect` | decomposition-criteria; interface-contracts; style-tradeoff-adr | A | A | M | `agents/1-generic/se-architect.md` | M | 2/1/0/0 |
| `se-critic` | ieee-1028-findings; suspect-marking; gate-criteria | A | A | A | `agents/1-generic/se-critic.md` | S | 3/0/0/0 |
| `se-interface-mgr` | contract-version-pre-post; versioning-compat; collision-deadlock | A | A | M | `agents/1-generic/se-interface-mgr.md` | M | 2/1/0/0 |
| `se-termination` | leaf-criteria; abstraction-endpoint; risk-based-depth | A | A | A | `agents/1-generic/se-termination.md` | S | 3/0/0/0 |
| `se-component-requirements` | allocation-flowdown; ac-l3; l3-interface-registry | A | A | A | `agents/1-generic/se-component-requirements.md` | S | 3/0/0/0 |
| `se-junior-developer` | interface-fidelity; test-per-leaf; read-spec | A | A | A | `agents/1-generic/se-junior-developer.md` | S | 3/0/0/0 |
| `se-developer` | cqrs-orthogonality; pre-post-oracles; cohesion-check | M | A | A | `agents/1-generic/se-developer.md` | S | 2/1/0/0 |
| `se-senior-developer` | isp-check; contract-completeness; icd-check | A | A | A | `agents/1-generic/se-senior-developer.md` | M | 3/0/0/0 |

**Netto #772: A 24 · M 3 · R 0 · D 0 (27).**
- `se-architect/S3` „force style trade-off in ADR" → **modify**: an das bestehende `se-cascade-adr-standard`-Skill koppeln (nicht CQRS als Pflichtbeispiel).
- `se-interface-mgr/S3` \"deterministic collision/deadlock checks\" → **modify**: als **Checkliste/Prüfschritt** (kein deterministischer Solver im Framework).
- `se-developer/S1` CQRS/orthogonality → **modify**: allgemeine Orthogonalitäts-Regel accept, CQRS nur als Beispiel (over-prescriptive vermeiden).

### 1.5 #773 — Review & quality roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/773))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | S4 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|---|
| `code-reviewer` | review-size-limit; explicit-goal; code-health; solid-evidence | A | A | A | A | `agents/1-generic/code-reviewer.md` | M | 4/0/0/0 |
| `concept-reviewer` | completeness-rubric; blocking-reason; alternatives | A | A | A | — | `agents/1-generic/concept-reviewer.md` | S | 3/0/0/0 |
| `frontend-reviewer` | ssr-hydration; re-render-memo; a11y-rules-index | D | A | M | — | `config/review-rules/frontend.yaml`, `ui.yaml` | S | 1/1/0/1 |
| `backend-reviewer` | observability-rule; api-contract-drift; concurrency-rules | A | A | A | — | `config/review-rules/backend.yaml` | M | 3/0/0/0 |
| `database-reviewer` | expand-contract; n1-rule; indexing-sqli | A | A | M | — | `config/review-rules/database.yaml`, `security.yaml` | M | 2/1/0/0 |
| `ui-reviewer` | wcag22-testable; consistent-identification; interaction-states | M | A | A | — | `config/review-rules/ui.yaml` | S | 2/1/0/0 |
| `refactoring-specialist` | seam-model; catalog-small-steps; characterization-tests | A | A | A | — | `agents/1-generic/refactoring-specialist.md` | S | 3/0/0/0 |
| `performance-optimizer` | use-method; profiling-flamegraphs; golden-signals | A | A | A | — | `agents/1-generic/performance-optimizer.md` | S | 3/0/0/0 |

**Netto #773: A 21 · M 3 · R 0 · D 1 (25).** → Review-Regel-Vorschläge landen gemäß D4 in `config/review-rules/*`, nicht als Prosa im Template.
- `frontend-reviewer/S1` SSR/hydration → **duplicate**: `config/review-rules/frontend.yaml:14` (FE-03 „SSR/hydration safety") existiert.
- `frontend-reviewer/S3` a11y-Regeln in Rules-Index → **modify**: nach `ui.yaml` (nicht `frontend.yaml`).
- `database-reviewer/S3` Indexing + SQLi → **modify**: SQLi ist bereits `security.yaml` SEC-01 (CWE-89); nur Indexing-Regel neu in `database.yaml`.
- `ui-reviewer/S1` WCAG 2.2 testable → **modify**: als `standard_ref: WCAG22` in `ui.yaml` verankern (nicht Template-Prosa).

### 1.6 #774 — Security & operations roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/774))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|
| `security-auditor` | owasp-asvs; secrets-git-history; stride | M | A | M | `config/review-rules/security.yaml`, `agents/1-generic/security-auditor.md` | M | 1/2/0/0 |
| `dependency-auditor` | sbom-cyclonedx; osv-nvd-automation; transitive-provenance | A | M | A | `agents/1-generic/dependency-auditor.md` | M | 2/1/0/0 |
| `ai-security-guardian` | prompt-injection; package-hallucination; governance-overreliance | A | A | A | `agents/1-generic/ai-security-guardian.md` | M | 3/0/0/0 |
| `accessibility-specialist` | conformance-level-legal; aria-apg; test-mix | A | A | A | `agents/1-generic/accessibility-specialist.md` | S | 3/0/0/0 |
| `log-analyzer` | log-quality; baseline-anomaly; correlate-traces-metrics | A | A | A | `agents/1-generic/log-analyzer.md` | S | 3/0/0/0 |
| `incident-responder` | incident-command; postmortem-handoff; status-cadence | A | A | A | `agents/1-generic/incident-responder.md` | S | 3/0/0/0 |
| `sre-engineer` | sli-slo-user; error-budget; toil-automation | A | A | A | `agents/1-generic/sre-engineer.md` | M | 3/0/0/0 |

**Netto #774: A 18 · M 3 · R 0 · D 0 (21).**
- `security-auditor/S1` OWASP ASVS → **modify**: `security.yaml` nutzt bereits OWASP-Axx-`standard_ref`; um ASVS-Level-Feld ergänzen (kein neuer Katalog).
- `security-auditor/S3` STRIDE → **modify**: als Threat-Modeling-Struktur-Referenz (`threat-model-4-questions`-Skill), nicht als Pflicht-Framework.
- `dependency-auditor/S2` OSV/NVD-Automation → **modify**: Werkzeug-/Netzabhängigkeit → optionaler Prüfpfad dokumentieren, kein Runtime-Mandat.

### 1.7 #775 — Knowledge-engine & documentation roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/775))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|
| `knowledge-curator` | schema-evolution; vocabulary-governance; linking-methodology | A | A | A | `agents/1-generic/knowledge-curator.md`, `knowledge/schema.md` | M | 3/0/0/0 |
| `knowledge-ingestor` | extraction-methodology; atomic-note; source-provenance | A | A | A | `agents/1-generic/knowledge-ingestor.md` | S | 3/0/0/0 |
| `knowledge-querier` | retrieval-strategy; grounding-citations; answer-quality-eval | A | A | A | `agents/1-generic/knowledge-querier.md` | S | 3/0/0/0 |
| `knowledge-linter` | orphan-criteria; link-rot; claim-expiry | A | A | A | `agents/1-generic/knowledge-linter.md` | S | 3/0/0/0 |
| `knowledge-indexer` | ia-catalog; index-log-separation; completeness-staleness | A | D | A | `agents/1-generic/knowledge-indexer.md` | S | 2/0/0/1 |
| `knowledge-gardener` | frontmatter-convention; tag-taxonomy; link-repair | M | A | A | `agents/1-generic/knowledge-gardener.md`, `knowledge/schema.md` | S | 2/1/0/0 |
| `knowledge-migrator` | okf-frictionless; idempotency-no-data-loss; structure-first | M | A | A | `agents/1-generic/knowledge-migrator.md` | M | 2/1/0/0 |
| `documenter` | diataxis; c4-views; arc42-readme | A | A | A | `agents/1-generic/documenter.md` | M | 3/0/0/0 |
| `technical-writer` | style-guide; diataxis-separation; openapi-api-ref | A | A | A | `agents/1-generic/technical-writer.md` | M | 3/0/0/0 |

**Netto #775: A 24 · M 2 · R 0 · D 1 (27).**
- `knowledge-indexer/S2` index/log separation → **duplicate**: `knowledge/schema.md` + OKF §6/§7 legen index=State / log=Events bereits fest.
- `knowledge-gardener/S1` frontmatter convention → **modify**: `knowledge/schema.md` ist der Owner; Garden verweist darauf, dupliziert nicht.
- `knowledge-migrator/S1` OKF/Frictionless → **modify**: OKF-Konformität ja; Frictionless nur optional (kein Bundle-Standard).

### 1.8 #776 — Platform-expert & meta roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/776))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|
| `prompt-engineer` | versioning-eval; context-tool-dimension; technique-taxonomy | A | A | A | `agents/1-generic/prompt-engineer.md` | M | 3/0/0/0 |
| `prompt-governor` | prompt-as-code; eval-gate; model-drift | A | A | A | `agents/1-generic/prompt-governor.md` | M | 3/0/0/0 |
| `agent-meta-scout` | skill-rubric; ecosystem-standards; build-vs-integrate | A | A | A | `agents/1-generic/agent-meta-scout.md` | S | 3/0/0/0 |
| `agent-meta-manager` | upgrade-safety; config-docs-consistency; submodule-guard | A | M | D | `agents/1-generic/agent-meta-manager.md` | S | 1/1/0/1 |
| `mammouth-expert` | official-docs; pal-placeholder-gap; model-effort-mapping | A | A | A | `agents/2-platform`, `agents/1-generic/mammouth-expert.md` | S | 3/0/0/0 |
| `provider-expert` | resolve-orphan; capability-flags; official-docs | D | D | R | — (Wrapper-Base) | — | 0/0/1/2 |

**Netto #776: A 13 · M 1 · R 1 · D 3 (18).**
- `provider-expert/S1` Orphan auflösen → **duplicate**: bereits via #736/WP5 (#758, Commit `0a1f3c03`) — `CHANGELOG.md:46`, `WRAPPER_TEMPLATES` in `scripts/lib/frontmatter.py:44`, Audit-Tests. Kein `role-defaults`-Eintrag by design.
- `provider-expert/S2` Capability-Flags statt `if provider ==` → **duplicate**: provider-agnostic-Policy + #735/WP2 (#756, Commit `554998f9`, „AST-verified 0") bereits erfüllt.
- `provider-expert/S3` offizielle Per-Provider-Docs als Primärquelle → **reject**: `provider-expert` ist Wrapper-Base ohne selektierbare Rolle; ein Docs-Mandat dort hätte keinen Adressaten (Doku gehört in die 2-platform-Experten).
- `agent-meta-manager/S3` submodule/boundary guard → **duplicate**: `submodule-protection`-Skill/Regel existiert. `S2` Konsistenzcheck → **modify** (bestehende `--audit-config`/`sync --check` erweitern statt Duplikat).

### 1.9 #777 — Design, data & content roles ([Issue](https://github.com/Popoboxxo/agent-meta/issues/777))

| Rolle | Vorschläge (Kurz) | S1 | S2 | S3 | Zielpfad | Größe | Netto A/M/R/D |
|---|---|---|---|---|---|---|---|
| `ui-ux-designer` | usability-heuristics; wcag-refs; journey-mapping | A | M | A | `agents/1-generic/ui-ux-designer.md` | S | 2/1/0/0 |
| `design-system-architect` | w3c-tokens; token-framework-mapping; contrast-gate-separation | A | A | A | `agents/1-generic/design-system-architect.md` | M | 3/0/0/0 |
| `frontend-component-engineer` | a11y-baseline; props-api; state-matrix | A | A | A | `agents/1-generic/frontend-component-engineer.md` | S | 3/0/0/0 |
| `api-specialist` | design-guidelines; spec-evolution; error-model | A | A | A | `agents/1-generic/api-specialist.md` | M | 3/0/0/0 |
| `database-engineer` | index-design; migration-governance; normalization-tradeoff | A | A | A | `agents/1-generic/database-engineer.md` | M | 3/0/0/0 |
| `data-engineer` | transformation-best-practices; data-quality-gates; streaming-patterns | A | A | M | `agents/1-generic/data-engineer.md` | S | 2/1/0/0 |
| `devops-engineer` | dora-metrics; k8s-architecture; observability-baseline | A | A | A | `agents/1-generic/devops-engineer.md` | M | 3/0/0/0 |
| `proofreader` | german-orthography; terminology-consistency | A | A | — | `agents/1-generic/proofreader.md` | S | 2/0/0/0 |
| `copyeditor` | plain-language; readability | A | A | — | `agents/1-generic/copyeditor.md` | S | 2/0/0/0 |
| `concept-specifier` | adr-decisions; given-when-then; completeness-rubric | A | A | A | `agents/1-generic/concept-specifier.md` | S | 3/0/0/0 |
| `concept-architect` | service-decomposition; adr-mandatory; parnas-decomposition | A | D | A | `agents/1-generic/concept-architect.md` | S | 2/0/0/1 |
| `openscad-developer` | official-docs; printability-rules; parametric-conventions | A | A | A | `agents/1-generic/openscad-developer.md` | S | 3/0/0/0 |

**Netto #777: A 31 · M 2 · R 0 · D 1 (34).**
- `ui-ux-designer/S2` WCAG-Refs → **modify**: als `standard_ref`/D2-Referenz, nicht Prosa-Duplikat.
- `data-engineer/S3` streaming patterns → **modify**: projektabhängig optional.
- `concept-architect/S2` ADRs mandatory → **duplicate**: `se-cascade-adr-standard`-Skill + ADR-Skills existieren bereits als verbindlicher Standard.

### 1.10 Gesamt-Zählung #769–#777

| Issue | Rollen | Bullets | accept | modify | reject | duplicate |
|---|---|---|---|---|---|---|
| #769 | 9 | 33 | 25 | 8 | 0 | 0 |
| #770 | 11 | 32 | 27 | 4 | 0 | 1 |
| #771 | 9 | 27 | 26 | 1 | 0 | 0 |
| #772 | 9 | 27 | 24 | 3 | 0 | 0 |
| #773 | 8 | 25 | 21 | 3 | 0 | 1 |
| #774 | 7 | 21 | 18 | 3 | 0 | 0 |
| #775 | 9 | 27 | 24 | 2 | 0 | 1 |
| #776 | 6 | 18 | 13 | 1 | 1 | 3 |
| #777 | 12 | 34 | 31 | 2 | 0 | 1 |
| **Σ** | **80** | **244** | **209** | **27** | **1** | **7** |

> **243 Literature-Vorschläge** = 244 Bullets minus 1 Nicht-Literatur-Bullet (`intern-developer` Routing-Exclusion, #770). Die Verteilung über die 243 Literature-Vorschläge lautet **accept 208 · modify 27 · reject 1 · duplicate 7**; mit dem Routing-Exclusion-Bullet als accept ergibt sich die oben ausgewiesene Gesamtverteilung **209 / 27 / 1 / 7** über 244 Bullets.

### 1.11 #778 — Cross-cutting design findings ([Issue](https://github.com/Popoboxxo/agent-meta/issues/778))

| ID | Finding | Klasse | Kurzbegründung | Zielpfad | Größe |
|---|---|---|---|---|---|
| F-1 | Referenzstandards nicht systematisch verankert | A | Prüfbares, optionales Frontmatter-Feld löst genau das; siehe D2 | `agents/1-generic/*.md` Frontmatter, `scripts/lib/frontmatter.py`, `consistency` | M |
| F-2 | Cross-Agent-Boundaries zentral statt in Templates | A | DRY/Drift-Reduktion; Routing → `role-defaults`, Self-Constraint → Template; siehe D3 | `config/role-defaults.yaml`, `agents/1-generic/orchestrator.md` | M |
| F-3 | Review-/Audit-Rollen brauchen Rule-IDs + Evidenzpflicht | A | `config/review-rules/*` existiert für 5 Domänen; Standardisierung schließt Lücke; siehe D4 | `config/review-rules/*.yaml`, Review-Templates | M |
| F-4 | Shared tool/MCP needs | M | Pro Item entscheiden; in diesem Batch **dokumentieren**, kein neuer MCP-Server (D5) | Doku/Skills | M |
| F-5 | Review-Methodik & Reliability | A | Provenienz/Quellen-Offenlegung ergänzen; kein Code | Doku/Plan | XS |
| F-6 | Role-wide patterns; `provider-expert` orphan | D | `provider-expert` ist seit #736/WP5 Wrapper-Base (`CHANGELOG:46`); intern-easter-egg via #770-Routing adressiert | — | — |

**Netto #778: A 4 · M 1 · R 0 · D 1 (6).**

### 1.12 #779 — Intent-Routing-Tabelle ([Issue](https://github.com/Popoboxxo/agent-meta/issues/779))

| ID | Finding | Klasse | Kurzbegründung | Zielpfad | Größe |
|---|---|---|---|---|---|
| IT-1 | `openscad-developer` nicht keyword-routbar | A | Verifiziert: Z. 803 ohne `routing_patterns`; Keywords ergänzen | `config/role-defaults.yaml` | S |
| IT-2 | `provider-expert` orphan | D | Bereits via #736/WP5 erledigt (`CHANGELOG:46`, `WRAPPER_TEMPLATES`) | — | — |
| IT-3 | 9 ambige Keywords, kein Tie-Break | A | Schema-Tie-Break nötig; siehe D6 (offene User-Entscheidung) | `config/role-defaults.yaml`, Schema | M |
| IT-4 | Sprach-Mismatch (29/301 DE) | M | Mechanismus-Entscheidung fällt in #780 (Option C); Datenfix folgt dort | `config/role-defaults.yaml`, Generator | M |
| IT-5 | Duplikat `routing_patterns.keywords` == `intent_keywords` | M | Deprecation erst nach abgeschlossener Migration + Lockup-Test; Fallback bleibt vorerst (D6) | `role-defaults.yaml`, `delegation_table.py` | M |
| IT-6 | Kein Coverage-Test | A | Test „jede aktive non-orchestrator Rolle ≥1 Keyword oder explizit name-only" | `tests/test_routing_tool_definitions.py` | S |
| IT-7 | Kein Overlap-Detektor | A | CI-Lint/Test auf Duplikat-Keywords | `tests/`, `consistency-check` | S |

**Netto #779: A 4 · M 2 · R 0 · D 1 (7).**

### 1.13 #780 — Language-aware intent routing ([Issue](https://github.com/Popoboxxo/agent-meta/issues/780))

| Option | Klasse | Kurzbegründung | Zielpfad | Größe |
|---|---|---|---|---|
| A — DE-Synonyme in Keyword-Liste | R | Monolingualer Stop-Gap, skaliert nicht pro Projekt; kein Mechanismus | — | — |
| B — Generator wählt DE/EN-Set aus `USER_INPUT_LANGUAGE` | R | Verdoppelt Keyword-Pflege und reintroduziert Coverage-Gaps (IT-1/IT-6) pro Sprache | — | — |
| C — kanonische language-neutrale Keywords + `examples` je `COMMUNICATION_LANGUAGE` | A | Empfohlen; eine Coverage-Quelle, Sprachadaption in freiem `examples`-Layer; siehe D1 | `scripts/lib/delegation_table.py`, `config/role-defaults.yaml`, Tests | L |

**Netto #780: A 1 · R 2 (3).**

### 1.14 Gesamt-Zählung inkl. Design-Findings

| Block | accept | modify | reject | duplicate | Σ |
|---|---|---|---|---|---|
| #769–#777 (243 Literature-Vorschläge) | 208 | 27 | 1 | 7 | 243 |
| #770 `intern-developer` Routing-Exclusion (Nicht-Literatur) | 1 | 0 | 0 | 0 | 1 |
| #778 Findings | 4 | 1 | 0 | 1 | 6 |
| #779 Findings | 4 | 2 | 0 | 1 | 7 |
| #780 Optionen | 1 | 0 | 2 | 0 | 3 |
| **Gesamt** | **218** | **30** | **3** | **9** | **260** |

---

## 2. Notes

- **Provider-expert ist kein offener Punkt.** #778-F6 und #779-IT-2 sind auf HEAD `5db4bbd5` bereits erledigt (#736 → PR #758, Commit `0a1f3c03`). Beweis: `CHANGELOG.md:46`; `scripts/lib/frontmatter.py:44` (`WRAPPER_TEMPLATES`); `scripts/lib/config_audit.py:71-89`; `tests/test_config_audit.py:390+`. Die 2-plattform-Experten (`claude-/gemini-/opencode-/continue-/copilot-expert`) haben ihre eigenen Overrides; `provider-expert.md` bleibt ausschließlich Base.
- **`openscad-developer` IT-1 ist der einzige verifizierte Routing-Datenfehler.** `config/role-defaults.yaml:803` hat keinen `routing`-Block; `tests/test_routing_tool_definitions.py:72` zementiert das derzeit.
- **#773 ist teilweise `duplicate`/`modify`, weil `config/review-rules/*` existiert.** FE-03 (SSR/hydration) und SEC-01 (SQLi) sind bereits vorhanden; die richtige Antwort auf F-3 ist Erweiterung/Normalisierung, nicht Parallel-Doku.
- **Mehrere `accept`-Vorschläge könnten in Templates schon teilweise vorhanden sein.** Das wurde nicht vollständig geprüft (80 Templates). Beim Edit gilt: erst deduplizieren, dann ergänzen; bei Wortgleichheit `duplicate` statt Doppelung.
- **Zwei Ratchets sind beim Hinzufügen von Template-Inhalt betroffen:** `tests/test_contract_labels.py` (Contract-Label-Exception-Registry) und der Block-Budget-Ratchet in `tests/test_context_compact_mode.py`. Beide sind in WP13 als Verifikation eingeplant.
- **Version-Bump-Pflicht:** jede Template-Änderung erfordert einen Frontmatter-Versions-Bump (`conventions`-Skill); Patch bei Textklarstellungen, Minor bei neuer optionaler Sektion.
- **SE-Rollen:** Die `se-*`-Vorschläge (#771/#772) müssen mit dem `se-cascade-*`-Skill-Set und dem ADR-Standard konsistent bleiben; keine zweite ADR-Konvention einführen.
- **Externe Quellen** (Microsoft/Azure, Google eng-practices, Fowler, OWASP, IEEE, arXiv etc.) wurden aus den Issues übernommen, aber im Rahmen dieses Plans **nicht erneut HTTP-geprüft**.

---

## 3. Design-Gate (vor den Per-Role-Template-Edits)

Jede Entscheidung: Optionen → Empfehlung → Begründung → Auswirkung → **User-Entscheidung (bestätigt 2026-09-13)**.

### D1 — #780 Sprachrouting (P1, blockiert Routing-WP)

- **Optionen:** A DE-Synonyme (data-only); B Generator selektiert DE-/EN-Set aus `USER_INPUT_LANGUAGE`; C kanonische language-neutrale Keywords + Sprache im `examples`-Layer.
- **Empfehlung:** **Option C**.
- **Begründung:** Routing wird vom LLM semantisch gegen `keywords` + `examples` aufgelöst; die kritischen Größen sind Coverage und Anker-Konsistenz. Eine zweite Keywords-Sprache verdoppelt Pflege und reproduziert die Coverage-Lückenklasse (IT-1, IT-6) pro Sprache. `COMMUNICATION_LANGUAGE`/`USER_INPUT_LANGUAGE` existieren bereits (`scripts/lib/config.py:144-145`) und werden vom Routing-Generator noch nicht konsumiert — genau die Lücke, die C schließt.
- **Auswirkung:**
  - `config/role-defaults.yaml`: `keywords` bleiben kanonisch/englisch; `examples` pro Rolle werden sprachlich gepflegt und im Generator durch `COMMUNICATION_LANGUAGE` gerendert.
  - `scripts/lib/delegation_table.py` `get_routing_rules()`: `examples` werden zur Emissionszeit durch die Sprachvariable gerendert; `keywords` bleiben sprach-invariant.
  - `tests/test_routing_tool_definitions.py`: neuer Test „DE-Konfiguration → deutsche Examples; EN-Konfiguration → englische Examples, identische Keywords"; Guard gegen sprachspezifische Strings in `keywords`.
  - `config/role-defaults.yaml` erhält eine Guideline/Regel „keywords = language-neutral domain anchors".
- **User-Entscheidung (D1, bestätigt 2026-09-13):** **DE/EN-Example-Paare** — pro Rolle bilingual in `config/role-defaults.yaml` gepflegt; der Generator wählt/emittiert anhand `COMMUNICATION_LANGUAGE`. `keywords` bleiben kanonisch/englisch (Option C bestätigt). **Deterministisch, kein LLM.**

### D2 — #778-F1 Referenzstandards (Frontmatter-Feld)

- **Optionen:**
  - (a) Freitext in `description` → nicht prüfbar, **reject**.
  - (b) Referenzen zentral in `config/role-defaults.yaml` → falscher Ort: Standards sind Rollen-Inhalt, nicht Routing-Daten, **reject**.
  - (c) Neues **optionales** Frontmatter-Feld in `agents/1-generic/<role>.md` → **empfohlen**.
- **Feldname (entschieden 2026-09-13):** `reference_standards` (Plural, Liste).
- **Werteformat (entschieden 2026-09-13):** Liste von Strings `"<STANDARD>[@<version>][#<section/level>]"`, z. B. `"IEEE 1012-2024#Verification Methods"`, `"WCAG 2.2#SC 3.2.4"`, `"OWASP ASVS#L2"`, `"SemVer 2.0.0"`. **MVP = String-Liste**; strukturierte Map `{name, version, section, url}` bleibt spätere Option (D2).
- **Schema-/Validierungsort:** geparst von `scripts/lib/frontmatter.py` (Frontmatter-Parser); validiert im `consistency-check` (`scripts/lib/consistency/`) als **optionales** Feld (kein Pflichtfeld → keine Massen-Backfill). Zusätzlich `config/review-rules/*.yaml` `standard_ref` für Review-Regeln konsistent halten.
- **Backfill-Strategie:** opportunistisch — nur Rollen, die in diesem Batch ohnehin editiert werden, erhalten `reference_standards`; keine separate Massen-Migration. Ein späteres `--audit-config`-Reporting kann Coverage ausweisen.
- **Auswirkung:** `conventions`-Skill/„Adding a new Agent Role" um das optionale Feld ergänzen; Frontmatter-Version-Bump (Minor) je berührter Rolle.
- **User-Entscheidung (D2, bestätigt 2026-09-13):** Feldname **`reference_standards`**; Werteformat **String-Liste** `"<STANDARD>[@<version>][#<section>]"` (MVP). Die strukturierte Map bleibt eine spätere Option.

### D3 — #778-F2 Boundary-Platzierung

- **Optionen:**
  - (a) Alles in Templates (Status quo) → Drift/DRY-Verstoß, **reject**.
  - (b) Alles zentral in `config/role-defaults.yaml` → verliert Behavioral-Self-Constraints, **reject**.
  - (c) **Zweiteilung** → **empfohlen**.
- **Empfehlung (c):**
  - **Routing-/Ownership-Boundary** (welcher Agent, wann, wer besitzt was) → `config/role-defaults.yaml` (`routing`, `handoff.input/output_contracts`) + `agents/1-generic/orchestrator.md` (Routing/Eskalation).
  - **Behavioral Self-Constraint** (was eine Rolle während der Arbeit nicht tun darf) → `<constraints>` im Template.
  - **Regel:** keine Routing-Entscheidung im Template duplizieren.
- **Auswirkung:** `requirements`-„Boundary to planner", `ideation`-„hand off to planner", „→ delegate to X"-Hinweise in Templates werden auf Self-Constraints reduziert; Routing-Verweise zeigen auf die zentrale Quelle. Betrifft **alle 80 Rollen-Templates** → in WP2 gebündelt, mit `consistency`-Check auf verbliebene Routing-Duplikate.
- **User-Entscheidung (D3, bestätigt 2026-09-13):** Bereinigungsumfang = **alle 80 Rollen-Templates** (vollständig, nicht opportunistisch). Die per-Gruppe-Umsetzung erfolgt vollständig in WP2 und WP4–WP12 (siehe §4).

### D4 — #778-F3 Review-Rule-IDs + Evidenzpflicht

- **Optionen:** (a) Prosa-Findings je Template; (b) standardisierte `config/review-rules/<domain>.yaml` mit IDs + Evidenzpflicht → **empfohlen**; (c) zentrales Mega-Index-File → schlechtere Domänen-Trennung, reject.
- **Konvention:** `id: <DOMAIN>-NN` (z. B. `FE-01`, `SEC-06`; neue Domänen `CR-` code-review, `CONCEPT-`, `A11Y-`, `DEP-`), Felder `title`, `severity_hint`, `standard_ref` (D2-Format).
- **Obligation:** „kein Finding ohne `rule_id` + Evidenz (file:line + Snippet)" als Pflicht in Review-/Audit-Templates; `database-reviewer.md:88` ist bereits Vorbild.
- **Auswirkung:** `code-reviewer`, `concept-reviewer`, `security-auditor`, `ai-security-guardian`, `dependency-auditor`, `accessibility-specialist` erhalten Zugriff auf ihre Domänen-Datei `config/review-rules/<domain>.yaml` (D4: Rollen gleicher Domäne teilen die Datei); bestehende 5 Domänen werden auf `standard_ref` normalisiert.
- **User-Entscheidung (D4, bestätigt 2026-09-13):** Granularität = **je Domäne** (`config/review-rules/<domain>.yaml`); Rollen mit gleicher Domäne teilen sich die Datei.

### D5 — #778-F4 MCP-/Tool-Bedarf

- **Optionen:** (a) neue MCP-Server sofort einführen; (b) pro Item dokumentierten manuellen Pfad ergänzen, MCP später; → **Empfehlung (b)**.
- **Empfehlung:** In diesem Batch **keine** neuen MCP-Server. Vier Items aus F-4:
  1. Observability/Tracing (OpenTelemetry GenAI) → Doku-Hinweis, optional.
  2. RAG/Vector-Retrieval → über bestehendes Knowledge-Wiki abbilden, kein neuer MCP.
  3. Confluence/Jira/Notion (export-manager) → manueller Pfad + Idempotenz/Vaildierung (siehe #770).
  4. Provider-Gateways (OpenRouter/LiteLLM) → out of scope, späteres Design-Issue.
- **Auswirkung:** F-4 wird `modify` (Doku statt Infrastruktur); keine Änderung an `config/skills-registry.yaml`.
- **User-Entscheidung (D5, bestätigt 2026-09-13):** Ein **separates MCP-Design-Issue** wird eröffnet (Folge-Issue). Im Plan als **Deliverable/Follow-up** verankert (WP13).

### D6 — #779 Schema-Erweiterung: Tie-Break (IT-3) + Coverage/Overlap (IT-6/IT-7)

- **IT-3 Optionen:** (A) Keywords eindeutig schärfen; (B) Priority/Disambiguation-Feld im Schema; (C) Hybrid → **Empfehlung**.
- **Empfehlung IT-3 = Hybrid:** zuerst Keywords pro Rolle schärfen, wo trivial (`audit` → `security audit` vs. `code review`); zusätzlich ein **optionales** `priority`-Feld (Integer, kleiner = spezifischer) im Routing-Schema, das der Generator deterministisch in die Rule-Dicts übernimmt; verbleibende Ambiguität wird durch die bestehende Orchestrator-Regel „ambiguous target description → clarify instead of dispatch" (aus #769-orchestrator-S5) aufgelöst.
- **IT-6 (Coverage):** Test in `tests/test_routing_tool_definitions.py`: „jede aktive Non-Orchestrator-Rolle hat ≥1 Rule (`keywords`/`examples`) **oder** ist in einer expliziten `name_only`-Allowlist (`intern-developer`, `principal-developer`)". Ersetzt/erweitert `test_roles_without_routing_stay_patternless`.
- **IT-7 (Overlap):** Detektor als eigenständiger Test/Consistency-Schritt, der Duplikat-Keywords über Rollen meldet; Ambiguitäts-Report als Warnung (PID/Level-basiert), nicht als Hard-Fail.
- **Auswirkung:** Schema (`config/role-defaults.yaml` + ggf. `config/project-config.schema.json` falls exponiert) + Generator + Tests.
- **User-Entscheidung (D6, bestätigt 2026-09-13):** **Hybrid** — Keyword-Schärfung, wo trivial, **und** ein optionales `priority`-Feld (Integer) im Routing-Schema. Das Feld ist **rückwärtskompatibel** (Default), kein Breaking-Change.

### D7 — #778-F5 Review-Methodik

- **Empfehlung:** `accept` (Doku). In den betroffenen Rollen/Plan-Doku die Provenienz der Literatur-Anker offenlegen (a = interner Literatur-Index mit Sektion/Score; b = verifizierte Online-Standards). Kein Code.
- **User-Entscheidung:** Keine offene — als `accept` (Doku) bestätigt; keine §7-Position (siehe §7-Nummerierungshinweis).

### D8 — #778-F6 / #779-IT-2 provider-expert-Orphan

- **Empfehlung:** `duplicate` — keine Aktion. Verifikation: `CHANGELOG.md:46`, `scripts/lib/frontmatter.py:44`, `scripts/lib/config_audit.py`, `tests/test_config_audit.py`. Im Abschluss-PR nur als „verified — no action" dokumentieren.

---

## 4. Arbeitspakete (WP0…WP13)

Reihenfolge = ausführungsreif; Abhängigkeiten explizit. Jedes WP ist ein **eigener Commit** im großen Sammel-PR (D7, siehe §6) — kein eigener Teil-PR.

> **Boundary-Bereinigung (D3, bestätigt 2026-09-13):** Die Routing-/Delegations-Boundary-Bereinigung erfolgt **vollständig über alle Rollen der jeweiligen Gruppe** (WP4–WP12) — nicht opportunistisch. WP2 verankert die zentrale Quelle und liefert den grep-basierten Vollcheck über **alle 80 Rollen-Templates**.

### WP0 — Design-Gate-Entscheidungen + Branch/Reihenfolge
- **Inhalt:** §3-Gates D1–D8 und die 9 User-Entscheidungen D1–D9 (§7) sind am **2026-09-13** verbindlich bestätigt; Sammel-Branch `feat/literature-agent-improvements` von `5db4bbd5` anlegen; Commit-/Reihenfolge festlegen (§6).
- **Akzeptanzkriterien:**
  1. Alle 9 User-Entscheidungen aus §7 sind mit Ergebnis + Datum `2026-09-13` dokumentiert; keine offenen Punkte.
  2. Branch existiert, Commit-Reihenfolge dokumentiert.
  3. Kein Code/Template geändert.
- **Verifikation:** dieses Dokument reviewed; keine Commands.

### WP1 — Routing & Language-Mechanismus (blockierend für sprachliche Template-Inhalte)
- **Quellen:** #780 (Option C), #779 IT-1/IT-3/IT-5/IT-6/IT-7, #770 intern-Router-Exclusion, #769 orchestrator routing-gate, #778-F6 (dup, no action).
- **Inhalt:** `delegation_table.py` rendert `examples` per `COMMUNICATION_LANGUAGE`; kanonische `keywords`; `openscad-developer`-`routing_patterns` ergänzen; optionales `priority`-Tie-Break-Feld; Coverage-/Overlap-Tests; `intern-developer` in `name_only`-Allowlist; Legacy-`intent_keywords` als deprecated markieren (Fallback bleibt bis Lockup-Test).
- **Akzeptanzkriterien:**
  1. DE-Projekt erhält deutsche `examples`, EN-Projekt englische — bei identischen `keywords` (Test).
  2. `openscad-developer` hat ≥1 Keyword/Example und erscheint als Routing-Rule (Test).
  3. Coverage-Test grün; Overlap-Report läuft im CI/Consistency-Schritt.
  4. Guard verhindert sprachspezifische Strings in `keywords`.
  5. `python3 scripts/sync.py --validate` und `tests/test_routing_tool_definitions.py` grün.
- **Abhängigkeit:** WP0.

### WP2 — Referenzstandards + Boundary-Bereinigung
- **Quellen:** #778-F1 (D2), #778-F2 (D3).
- **Inhalt:** `reference_standards`-Feld in Frontmatter-Parser/Consistency aufnehmen, `conventions`-Skill dokumentieren; Routing-Duplikate aus **allen 80 Rollen-Templates** entfernen und zentral verankern (D3).
- **Akzeptanzkriterien:**
  1. `reference_standards` ist optional, parsebar und wird im Consistency-Lauf geprüft.
  2. Mindestens 3 Rollen (z. B. `security-auditor`, `release`, `se-verifier`) tragen valide `reference_standards`.
  3. Kein Template der 80 enthält nach der Bereinigung einen Routing-/Delegations-Boundary-Satz, der `role-defaults`/`orchestrator` dupliziert (grep-basierter **Vollcheck**, D3).
  4. `sync.py --validate` + `consistency-check` grün.
- **Abhängigkeit:** WP0; WP1 für Routing-relevante Formulierungen.

### WP3 — Review-Rule-Index-Standardisierung
- **Quellen:** #778-F3 (D4), Review-Findings aus #773/#774.
- **Inhalt:** `config/review-rules/<domain>.yaml` für `code-reviewer`/`concept-reviewer`/`security-auditor`/`ai-security-guardian`/`dependency-auditor`/`accessibility-specialist`; bestehende 5 Domänen normalisieren (`standard_ref`); Evidenz-/`rule_id`-Pflicht in Templates.
- **Akzeptanzkriterien:**
  1. Jede Review-/Audit-Rolle referenziert genau eine Rules-Datei; IDs eindeutig (`<DOMAIN>-NN`).
  2. `security.yaml`/`frontend.yaml` etc. validieren (YAML-Schema, `standard_ref` im D2-Format).
  3. `consistency-check` prüft Rule-ID-Eindeutigkeit und Evidenzfelder.
  4. Tests grün.
- **Abhängigkeit:** WP0; WP2 (D2-Format).

### WP4 — Core-Development-Rollen-Templates (#769)
- **Inhalt:** Edits an `orchestrator`, `developer`, `junior-developer`, `senior-developer`, `principal-developer`, `explorer`, `git`, `release`, `docker` gemäß §1.1; Dedupe gegen vorhandene Sätze; Versions-Bump je Rolle.
- **Akzeptanzkriterien:**
  1. Alle `accept`-Punkte umgesetzt; alle `modify`-Punkte in der jeweiligen Zielform.
  2. Kein neuer `if provider ==`-Branch, keine Provider-Namen in 1-generic.
  3. Contract-Ratchet (`tests/test_contract_labels.py`) und Block-Budget-Ratchet (`tests/test_context_compact_mode.py`) grün.
  4. `sync.py --validate` grün.
- **Abhängigkeit:** WP0–WP2.

### WP5 — Product-&-Planning-Rollen (#770): `feedback`, `requirements`, `ideation`, `planner`, `product-manager`, `effort-estimator`, `bug-feature-analyzer`, `export-manager`, `meta-feedback`, `app-lifecycle-governor`.
- **Akzeptanzkriterien:** §1.2 accept/modify umgesetzt (insb. `bug-feature-analyzer` needs-info-Pfad statt UNCLEAR-Default); Versions-Bumps; Tests grün.
- **Abhängigkeit:** WP0.

### WP6 — Testing-&-V&V-Rollen (#771): `tester`, `e2e-tester`, `test-executor`, `validator`, `se-verifier`, `se-validator`, `se-test-engineer`, `se-testreviewer`, `se-integration-and-test-manager`.
- **Akzeptanzkriterien:** §1.3 umgesetzt; negative-path als Metrik; `reference_standards` für IEEE/ISTQB; Tests grün.
- **Abhängigkeit:** WP0, WP2.

### WP7 — SE-Rollen (#772): `se-requirements`, `se-architect`, `se-critic`, `se-interface-mgr`, `se-termination`, `se-component-requirements`, `se-junior-developer`, `se-developer`, `se-senior-developer`.
- **Akzeptanzkriterien:** §1.4 umgesetzt; Konsistenz mit `se-cascade-*`-Skills und ADR-Standard nachgewiesen; Tests grün.
- **Abhängigkeit:** WP0, WP2, WP3.

### WP8 — Review-&-Quality-Rollen (#773) plus Rules-Daten
- **Inhalt:** `code-reviewer`, `concept-reviewer`, `frontend-/backend-/database-/ui-reviewer`, `refactoring-specialist`, `performance-optimizer`; FE-03/Duplikate unangetastet; neue Rules in `config/review-rules`.
- **Akzeptanzkriterien:** §1.5 umgesetzt; FE-03/SEC-01 nicht dupliziert; Tests grün.
- **Abhängigkeit:** WP3.

### WP9 — Security-&-Operations-Rollen (#774): `security-auditor`, `dependency-auditor`, `ai-security-guardian`, `accessibility-specialist`, `log-analyzer`, `incident-responder`, `sre-engineer`.
- **Akzeptanzkriterien:** §1.6 umgesetzt; ASVS/STRIDE als Referenz (D2) statt neuer Katalog; Tests grün.
- **Abhängigkeit:** WP2, WP3.

### WP10 — Knowledge-&-Documentation-Rollen (#775): `knowledge-*`, `documenter`, `technical-writer`.
- **Akzeptanzkriterien:** §1.7 umgesetzt; `knowledge/schema.md` bleibt Frontmatter-/Index-Log-Owner (keine Duplikation); Tests (Knowledge-Engine) grün.
- **Abhängigkeit:** WP0.

### WP11 — Platform-Expert-&-Meta-Rollen (#776): `prompt-engineer`, `prompt-governor`, `agent-meta-scout`, `agent-meta-manager`, `mammouth-expert`; `provider-expert` = no action (duplicate).
- **Akzeptanzkriterien:** §1.8 umgesetzt; Mammouth-PAL-Placeholder-Gap adressiert; `provider-expert` unverändert/als Base; Tests grün.
- **Abhängigkeit:** WP0.

### WP12 — Design-, Data-&-Content-Rollen (#777): `ui-ux-designer`, `design-system-architect`, `frontend-component-engineer`, `api-specialist`, `database-engineer`, `data-engineer`, `devops-engineer`, `proofreader`, `copyeditor`, `concept-specifier`, `concept-architect`, `openscad-developer`.
- **Akzeptanzkriterien:** §1.9 umgesetzt; `concept-architect`-ADR-Duplikat vermieden; Tests grün.
- **Abhängigkeit:** WP0, WP2, WP3.

### WP13 — Verifikation, DoD & Delivery
- **Inhalt:** Gesamtlauf aller Checks, Sammel-Branch-/Sammel-PR-Abschluss, CHANGELOG-/VERSION-Bump (**Minor → 1.2.0**, D9), DoD-Checkliste, Release-Handoff; **Folge-Issue für das MCP-Design (D5)** als Deliverable dokumentieren.
- **Akzeptanzkriterien:**
  1. `python3 scripts/sync.py --validate` → PASS (0 Fehler).
  2. `python3 scripts/sync.py --check` → exit 0 (keine Drift).
  3. `tests/test_routing_tool_definitions.py` grün (inkl. neuer Coverage-/Overlap-/Sprachtests).
  4. `python3 scripts/consistency-check.py` (ggf. `--strict`) grün.
  5. `tests/test_contract_labels.py` + `tests/test_context_compact_mode.py` (Ratchet) grün.
  6. `python -m pytest tests/ -q` grün (bekannte Umgebungs-Skips dokumentiert).
  7. Alle berührten Rollen haben Frontmatter-Versions-Bump; Conventional Commit; Branch-Guard eingehalten.
- **Abhängigkeit:** WP1–WP12.

---

## 5. Risiko-Register

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|---|---|---|---|
| Template-Bloat durch 208 `accept`-Punkte (D8: alle sofort) → Block-Budget-/Kontext-Kosten | Hoch | Hoch | Pro Rolle deduplizieren (Dedupe-Pflicht gegen bestehende Template-Inhalte); kurze, prüfbare Sätze; relevante Punkte als `reference_standards`/Rules auslagern (D2/D4); Block-Budget-Ratchet in WP13 |
| Instruction Bleed durch `extends`+`patches` (2-platform) bei Text-Edits | Mittel | Mittel | `conventions`-Prüfpunkte vor Patch-Commit; Composition-Tests; keine Semantik-Überschreibung in ankerfremden Sections |
| Sprachadaption (D1) bricht Routing-Snapshots/Erwartungen | Mittel | Mittel | Keywords sprach-invariant halten; nur `examples` rendern; explizite DE/EN-Tests; idempotente, sortierte Ausgabe |
| Schema-Tie-Break (D6) als Breaking-Change für Konsumenten | Mittel | Hoch | `priority` optional + Default; schrittweise Keyword-Schärfung zuerst; Konsumenten-Versionierung; Rückwärtskompatibilitätstest |
| Konflikte auf Hotfile `config/role-defaults.yaml` (WP1 vs. WP4/WP5) | Hoch | Mittel | WP1 zuerst committen; Änderungen an `role-defaults` serialisieren; übrige WPs nur Template-Dateien; Commit-Reihenfolge (§6) |
| Review-Rule-IDs driften / doppelte Domänen | Mittel | Niedrig | Ein Domänen-File je Domäne (D4); Eindeutigkeits-Check im `consistency-check`; Ratchet-Test |
| Ungenügende Verifikation einzelner `accept`-Punkte (kein Prüfanker) | Mittel | Mittel | Akzeptanzkriterien je WP messbar; `--validate`/`--check`/Tests/Ratchet als DoD; Review durch `validator` |
| Provider-agnostic-Verstoß durch neue Tool-/Provider-Referenzen | Niedrig | Hoch | Änderungen nur in 1-generic ohne Provider-Namen; `provider-agnostic`-Skill-Check; AST-/Grep-Check (`if provider ==`) |
| `provider-expert`-Doppelarbeit durch falsch verstandenes IT-2/F-6 | Niedrig | Niedrig | Als `duplicate` dokumentiert; im PR „verified — no action" |
| Zu breite `modify`-Interpretation (Zielpfad-Drift) | Mittel | Mittel | D3/D4-Zielpfade verbindlich; Review-Gate vor Merge |
| VERSION-/CHANGELOG-Inkonsistenz nach Sammel-Branch | Niedrig | Mittel | WP13-Bump; `test_version_bookkeeping.py`/`sync --check` |
| Submodul-/Containment-Risiko beim Sync in Zielprojekten | Niedrig | Mittel | `submodule-protection`-Skill; Sync nur über `sync.py`; Branch-Pflicht |

---

## 6. Branch-/Delivery-Strategie (Sammel-Branch `feat/literature-agent-improvements`)

- **Grundmodell (D7, bestätigt 2026-09-13):** Ein **Sammel-Branch** von `5db4bbd5`; Delivery als **ein großer Sammel-PR** vom Sammel-Branch nach `main` — **keine** gestapelten Teil-PRs.
- **Reviewbarkeit trotz Sammel-PR (D7-Mitigation):** Im Sammel-PR liegt **je WP ein eigener, sauberer Commit** (Conventional Commit + WP-Referenz). Review erfolgt **commit-by-commit**; die per-WP-Akzeptanzkriterien aus §4 und die **WP13-Ratchets** (`tests/test_contract_labels.py`, `tests/test_context_compact_mode.py`) greifen als Gate. So bleiben Blast-Radius und Prüfbarkeit ohne Teil-PRs begrenzt.
- **Warum nicht gestapelte Teil-PRs:** Ein konsistenter Sammel-PR vermeidet Zwischen-Merge-Zustände und Reihenfolge-Konflikte auf den Hotfiles; die Commit-Struktur liefert dieselbe Prüfbarkeit.
- **Warum nicht 13 unabhängige Branches:** Kollisionen auf Hotfiles und Reihenfolgeabhängigkeiten (Routing/Schema) machen parallele Branches konfliktanfällig.
- **Commit-Reihenfolge im Sammel-PR:**
  1. **WP1** (Routing/Language) — berührt `config/role-defaults.yaml` und `delegation_table.py`; zuerst, um Konflikte zu vermeiden.
  2. **WP2** (Standards/Boundary) und **WP3** (Review-Rules) — Config/Schema, nach WP1.
  3. **WP4–WP12** (Rollentemplates) — je WP ein eigener Commit; Template-Dateien sind disjunkt; nur WPs **ohne** `config/role-defaults.yaml`-Zugriff.
  4. **WP13** (Verifikation/Delivery) — zuletzt.
- **Serialisierung auf `config/*.yaml`-Hotfiles (Commit-Reihenfolge, keine Merge-Konflikte):**
  - `config/role-defaults.yaml`: **nur WP1** darf sie ändern (inkl. `openscad-developer`-Routing und optionalem `priority`-Feld aus D6). Neue `reference_standards` gehören in Template-Frontmatter (WP2), nicht in `role-defaults`.
  - `config/review-rules/*.yaml`: **nur WP3/WP8/WP9**; Änderungen dort serialisieren (nicht parallel).
  - `config/project-config.schema.json`: nur falls D6 es berührt (WP1); sonst unangetastet.
- **Commit-/DoD-Konventionen:** Conventional Commits (`feat:`/`fix:`/`chore:`), erste Zeile ≤72 Zeichen, Imperativ, Englisch; Feature-Branch (kein direkter `main`-Commit); DoD = Code komplett, keine Regression, Konventionen eingehalten; Template-Versions-Bump je Rolle; `sync.py --validate` + `--check` + Tests vor **dem Sammel-PR**.
- **Sammel-PR-Beschreibung:** Verweis auf dieses Plan-Dokument, **Commit-/WP-Liste (commit-by-commit)**, Akzeptanzkriterien-Ergebnisse, Verteilung (accept/modify), „no action"-Nachweis für provider-expert/F-6/IT-2, sowie den Verweis auf die Ratchet-Tests.
- **Freigabe:** Kein Auto-Merge; der Sammel-PR wird erst nach WP13-Gesamtlauf und Validator-Check gemergt. Der Branch wird nicht direkt durch den Planner erstellt/gepusht (keine Git-Operation in diesem Task).

---

## 7. User-Entscheidungen — entschieden (2026-09-13)

Alle 9 Design-Gate-/Prozess-Entscheidungen sind am **2026-09-13** verbindlich bestätigt. **Keine offenen Punkte.**

> **Nummerierung:** D1–D6 entsprechen den Design-Gates in §3; D7–D9 sind Prozess-/Delivery-Entscheidungen außerhalb der §3-Gates (§3-D7/D8 bleiben unverändert — dort gab es keine offene Entscheidung).

| # | Entscheidung | Ergebnis (verbindlich) | Datum |
|---|---|---|---|
| D1 | Sprachrouting-Mechanik | **DE/EN-Example-Paare** — pro Rolle bilingual in `config/role-defaults.yaml`; der Generator wählt/emittiert anhand `COMMUNICATION_LANGUAGE`. `keywords` bleiben kanonisch/englisch (Option C bestätigt). Deterministisch, kein LLM. | 2026-09-13 |
| D2 | Referenzstandard-Feld | Feldname **`reference_standards`**; Werteformat **String-Liste** `"<STANDARD>[@<version>][#<section>]"` (MVP); strukturierte Map bleibt spätere Option. | 2026-09-13 |
| D3 | Boundary-Bereinigungsumfang | **alle 80 Templates** (vollständig), nicht opportunistisch. | 2026-09-13 |
| D4 | Review-Rules-Granularität | **je Domäne** (`config/review-rules/<domain>.yaml`); Rollen mit gleicher Domäne teilen die Datei. | 2026-09-13 |
| D5 | MCP/Tool-Bedarf (F-4) | **separates MCP-Design-Issue** wird eröffnet (Folge-Issue); im Plan als Deliverable/Follow-up verankert (WP13). | 2026-09-13 |
| D6 | Routing-Tie-Break | **Hybrid** — Keyword-Schärfung wo trivial **und** optionales `priority`-Feld im Routing-Schema (rückwärtskompatibel, Default = keine Ambiguitätsänderung). | 2026-09-13 |
| D7 | Delivery | **ein großer Sammel-PR** (nicht gestapelte Teil-PRs); Mitigation: **ein eigener, sauberer Commit je WP** im Sammel-PR (Review commit-by-commit) + WP13-Ratchets. | 2026-09-13 |
| D8 | accept-Umfang | **alle 208 accepts sofort**, mit **Dedupe-Pflicht** gegen bestehende Template-Inhalte und Block-Budget-Ratchet. | 2026-09-13 |
| D9 | VERSION-Bump | **Minor → 1.2.0**. | 2026-09-13 |

**Verbleibende sachliche offene Punkte:** keine. D5 (MCP-Design-Issue) und D8 (Dedupe je Vorschlag) sind als Folge-Deliverable bzw. Akzeptanzkriterium in den WPs verankert — keine offenen Entscheidungen.

---

## 8. Anhang — Verifikationsanker (HEAD `5db4bbd5`)

| Behauptung | Beleg |
|---|---|
| `provider-expert` ist Wrapper-Base, keine selektierbare Rolle (→ #778-F6 / #779-IT-2 duplicate) | `CHANGELOG.md:46`; `scripts/lib/frontmatter.py:44` (`WRAPPER_TEMPLATES`); `scripts/lib/config_audit.py:71-89`; `tests/test_config_audit.py:390+` |
| Provider-agnostische Command-Dispatch bereits erledigt (→ #776 provider-expert/S2 duplicate) | `CHANGELOG.md:7-10` (#735/#743, PR #756, Commit `554998f9`, „AST-verified 0") |
| `openscad-developer` ohne Routing-Block (→ #779-IT-1 valid) | `config/role-defaults.yaml:803`; `tests/test_routing_tool_definitions.py:72` |
| `frontend.yaml` FE-03 SSR/hydration existiert (→ #773 frontend-reviewer/S1 duplicate) | `config/review-rules/frontend.yaml:14` |
| `security.yaml` SEC-01…SEC-06 mit OWASP-/CWE-`standard_ref` (→ #774 security-auditor/S1 modify) | `config/review-rules/security.yaml:4-28` |
| Routing-Generator sprach-agnostisch (→ #780 / #779-IT-4 valid) | `scripts/lib/delegation_table.py:97-186`; `scripts/lib/agents.py:224-294`; `scripts/lib/config.py:144-145` |
| Contract-Ratchet + Block-Budget-Ratchet vorhanden | `tests/test_contract_labels.py:24-55`; `tests/test_context_compact_mode.py:422-480` |
| Consistency-Runner vorhanden | `scripts/consistency-check.py`; `scripts/lib/cli_commands.py:150` |
