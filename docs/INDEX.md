# Dokumentations-Index

Hauptindex der Dokumentation unter `docs/`; zugleich Fallback-Index für `spec-plan-workflow` (`.meta-config/project.yaml`, Schlüssel `fallback-index`).

- Stand: 2026-11-15 — 375 Dateien unter `docs/`, davon 366 Markdown-Dateien.
- Pflege: neue Datei unter `docs/` -> hier eintragen. Titel, Status und Datum nur aus dem Dateikopf übernehmen; fehlender Status = „—“.
- Weitere Übersichten: [plans/README.md](plans/README.md), [concepts/archive/README.md](concepts/archive/README.md).
- `knowledge/wiki/index.md` ist ein separater (Wiki-)Index und hier nicht enthalten.
- Nicht-Markdown-Dateien (9; nicht einzeln indexiert): .gitkeep in spikes, specs, plans; `guides/project.yaml.example`; `guides/ci/github-actions-sync-check.yml`; HTML/PNG in `ui/` (live-dashboard.html, favicon.png, admin-ui.html, agent-graph.html).

## Root-Dateien

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [test-scenario.md](test-scenario.md) | Test-Szenario — Smart-Light IoT Controller | Entwurf | 2026-05-24 |
| [CODEBASE_OVERVIEW.md](CODEBASE_OVERVIEW.md) | CODEBASE_OVERVIEW — agent-meta | — | — |
| [RELEASE_GATES.md](RELEASE_GATES.md) | Mechanized Pre-Release Gates | — | — |
| [REQUIREMENTS.md](REQUIREMENTS.md) | Anforderungen — agent-meta | — | — |
| [agent-mindmap.md](agent-mindmap.md) | Agenten-Übersicht | — | — |
| [process-capability-gaps.md](process-capability-gaps.md) | Prozess-/Capability-Gaps — Fortschritts-, Ausführungs- und Verifikationssystem | — | — |
| [spec-plan-workflow-coverage.md](spec-plan-workflow-coverage.md) | Spec/Plan-Workflow — Coverage-Matrix | — | — |
| [test-validation-checklist.md](test-validation-checklist.md) | Test Validation Checklist — SE Framework Extensions | — | — |

## analysis (29)

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [analysis/274-industry-bestpractices.md](analysis/274-industry-bestpractices.md) | Industry Best Practices: Agentic Systems (#274) | — | 2026-06-15 |
| [analysis/276-architecture-robustness-audit.md](analysis/276-architecture-robustness-audit.md) | Audit: Architecture Robustness (Issue #276) | — | 2026-06-15 |
| [analysis/402-systemaudit-kernziele.md](analysis/402-systemaudit-kernziele.md) | Systemaudit: Kernziele (Issue #402) | — | 2026-08-06 |
| [analysis/2026-09-30-provider-audit-docs-part1.md](analysis/2026-09-30-provider-audit-docs-part1.md) | Provider Audit — Online-Doc Contract Comparison (Part 1) | — | 2026-09-30 |
| [analysis/2026-09-30-provider-audit-docs-part2.md](analysis/2026-09-30-provider-audit-docs-part2.md) | Provider Audit — Online-Doc Contract Comparison (Part 2) | — | 2026-09-30 |
| [analysis/2026-09-30-provider-audit-generation.md](analysis/2026-09-30-provider-audit-generation.md) | Provider Audit — AGENT-Artifact Generation (9 Providers) | — | 2026-09-30 |
| [analysis/2026-09-30-provider-audit-runtime-consolidation.md](analysis/2026-09-30-provider-audit-runtime-consolidation.md) | Provider Audit — Phase C Runtime Consolidation (Single Source of Truth) | — | 2026-09-30 |
| [analysis/2026-10-11-context-budget-provider-study.md](analysis/2026-10-11-context-budget-provider-study.md) | Context-Budget-Studie — was die 9 Provider tatsächlich laden und was es kostet | FINAL (Evidenzbasis, keine Spezifikation); Nachtrag §10 (Rev… | 2026-10-11 |
| [analysis/2026-10-11-context-tokenizer-measurement.md](analysis/2026-10-11-context-tokenizer-measurement.md) | Kontext-Messung: Bytes und Token je Artefakt | Messung Bytes real, Token approximiert (Bytes / 4) — Tokeniz… | 2026-10-11 |
| [analysis/2026-10-22-opencode-permission-precedence.md](analysis/2026-10-22-opencode-permission-precedence.md) | Permission-Rangfolge in Opencode (OQ-1) — Evidenz | — | 2026-10-22 |
| [analysis/2026-11-11-hook-api-ask-permission.md](analysis/2026-11-11-hook-api-ask-permission.md) | Hook-API-Prüfung: 'ask'-Permission vs. exit 2 | Analyse (Vorbedingung für Task 1 der Phase D), kein Beschlus… | 2026-11-13 |
| [analysis/2026-11-14-audit-prioritization.md](analysis/2026-11-14-audit-prioritization.md) | Audit-Priorisierung agent-meta — 2026-11-14 | Analyse (kein Beschluss) | 2026-11-14 |
| [analysis/2026-11-14-fable-concept-audit.md](analysis/2026-11-14-fable-concept-audit.md) | Grobe Konzeptprüfung agent-meta — 2026-11-14 | Analyse (kein Beschluss) | 2026-11-14 |
| [analysis/2026-11-14-fable-provider-hooks-audit.md](analysis/2026-11-14-fable-provider-hooks-audit.md) | Vertiefte Konzeptprüfung: Provider-Agnostik + Hooks (Claude / Opencode v2) | Analyse (kein Beschluss) | 2026-11-14 |
| [analysis/2026-11-14-fable-viz-extensions-audit.md](analysis/2026-11-14-fable-viz-extensions-audit.md) | Audit: viz, Extensions-Mechanik, ReqogniLoom-Integration, Agent Meta gesamt | Analyse (kein Beschluss) | 2026-11-14 |
| [analysis/2026-11-15-fable-framework-settings-audit.md](analysis/2026-11-15-fable-framework-settings-audit.md) | Framework-Settings-Audit agent-meta — 2026-11-15 (Fable) | Analyse (kein Beschluss) | 2026-11-15 |
| [analysis/2026-11-15-fable-language-feature-audit.md](analysis/2026-11-15-fable-language-feature-audit.md) | Audit: Sprach-Feature (Language / Speech-Mode) — warum es nicht greift | Analyse (kein Beschluss) | 2026-11-15 |
| [analysis/2026-11-15-fable-orchestration-rollout-audit.md](analysis/2026-11-15-fable-orchestration-rollout-audit.md) | Audit: Orchestrierungs-Einstellungen & -Modus — Rollout je Provider | Analyse (kein Beschluss) | 2026-11-15 |
| [analysis/2026-11-15-fable-verification-of-unchecked.md](analysis/2026-11-15-fable-verification-of-unchecked.md) | Verifikation der „NICHT GEPRÜFT / Lücken“-Punkte der Audits 2026-11-14/15 | Analyse (kein Beschluss) | 2026-11-15 |
| [analysis/2026-04-template-gap-analysis.md](analysis/2026-04-template-gap-analysis.md) | Template Gap-Analyse — Stand 2026-04-01 | — | — |

### analysis/evidence

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [analysis/evidence/2026-09-30-entry-file-verification.md](analysis/evidence/2026-09-30-entry-file-verification.md) | Evidence — Entry-/Kontextdatei-Verifikation (Phase B) | — | 2026-09-30 |
| [analysis/evidence/2026-09-30-regression-tests.md](analysis/evidence/2026-09-30-regression-tests.md) | Regression Tests — Provider-Audit OpenCode v2 (Phase D) | — | 2026-09-30 |
| [analysis/evidence/2026-09-30-runtime-claude-antigravity.md](analysis/evidence/2026-09-30-runtime-claude-antigravity.md) | Runtime Evidence — Claude Code + Gemini/Antigravity (real harness load) | — | 2026-09-30 |
| [analysis/evidence/2026-09-30-runtime-codex-kimi-zcode.md](analysis/evidence/2026-09-30-runtime-codex-kimi-zcode.md) | Runtime-Evidenz — Codex (D1) · KimiCode (H6) · ZCode (H5) | — | 2026-09-30 |
| [analysis/evidence/2026-09-30-runtime-continue.md](analysis/evidence/2026-09-30-runtime-continue.md) | Runtime-/Schema-Evidenz — Continue (H7 Auto-Discovery · H8 SSE-'headers' · H9 'skills' · bare Model-Alias) | — | 2026-09-30 |
| [analysis/evidence/2026-09-30-runtime-mammouth-copilot.md](analysis/evidence/2026-09-30-runtime-mammouth-copilot.md) | Runtime-Evidenz — Mammouth (H10 / MM-2 / MM-4) · Copilot (Artefakt-Validierung) | — | 2026-09-30 |
| [analysis/evidence/2026-09-30-runtime-opencode-v1.md](analysis/evidence/2026-09-30-runtime-opencode-v1.md) | Runtime Evidence — Opencode **v1** (real harness load + dispatch errors) | — | 2026-09-30 |
| [analysis/evidence/2026-09-30-runtime-opencode-v2.md](analysis/evidence/2026-09-30-runtime-opencode-v2.md) | Runtime Evidence — Opencode **v2** (installability + schema validation) | — | 2026-09-30 |
| [analysis/evidence/2026-10-22-opencode-jsonc-loading.md](analysis/evidence/2026-10-22-opencode-jsonc-loading.md) | Evidence — Ladeverhalten 'opencode.json' + 'opencode.jsonc' | — | 2026-10-23 |

## plans (83)

### 2026-09

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [plans/2026-09-04-provider-codex-zcode.md](plans/2026-09-04-provider-codex-zcode.md) | Implementation Plan: New Providers "Codex" (OpenAI Codex CLI), "ZCode" (zcode.z.ai) & "Kimi Code" (Moonshot AI Kimi Code CLI) | — | 2026-09-04 |
| [plans/2026-09-04-verification-results.md](plans/2026-09-04-verification-results.md) | P1 Verification Results — Plan "Codex / ZCode / Kimi Code" (2026-09-04) | — | 2026-09-04 |
| [plans/2026-09-05-issue-674-roadmap.md](plans/2026-09-05-issue-674-roadmap.md) | Implementation Plan: Issue #674 — Consolidated Backlog Roadmap (P0–P4 Batches) | — | 2026-09-05 |
| [plans/2026-09-05-plugin-catalog-unification.md](plans/2026-09-05-plugin-catalog-unification.md) | Design: Vereinheitlichter Plugin-Katalog (External Tools + MCP Server) | — | 2026-09-05 |
| [plans/2026-09-06-issue-523-agent-eval-plan-v2.md](plans/2026-09-06-issue-523-agent-eval-plan-v2.md) | Agent-Eval-Plan v2 — Revision zu Concept-Review #523 (promptfoo-basiertes Agent-Eval-Framework) | — | 2026-09-06 |
| [plans/2026-09-06-issue-674-phase4b-harness-dependencies.md](plans/2026-09-06-issue-674-phase4b-harness-dependencies.md) | Phase 4b Harness Dependencies & Follow-ups (Issues #264–#267, #506, #517) | — | 2026-09-06 |
| [plans/2026-09-06-issue-674-phase4d-followups.md](plans/2026-09-06-issue-674-phase4d-followups.md) | Phase 4d SE-Cascade Follow-ups & Design-Artefakte (Issues #207, #548, #452, #534, #317, #318) | — | 2026-09-06 |
| [plans/2026-09-06-phase4c-blast-radius.md](plans/2026-09-06-phase4c-blast-radius.md) | Blast-Radius-Analyse: Strangler-Refactor Phase 4c (#481/#482/#483) | — | 2026-09-06 |
| [plans/2026-09-11-audit-batch-730-743-plan.md](plans/2026-09-11-audit-batch-730-743-plan.md) | Audit Batch Triage & Implementation Plan — #712, #730–#743 | — | 2026-09-11 |
| [plans/2026-09-12-issue-763-hacs-entity-rules-plan.md](plans/2026-09-12-issue-763-hacs-entity-rules-plan.md) | Plan — Issue #763: HACS-Preset — englische Entity-Namen via 'translation_key' + Entity-Registry-Migration bei Rename | — | 2026-09-12 |
| [plans/2026-09-12-literature-anchored-agent-improvements-plan.md](plans/2026-09-12-literature-anchored-agent-improvements-plan.md) | Literature-Anchored Agent Improvements — Triage & Implementation Plan (#769–#780) | — | 2026-09-12 |
| [plans/2026-09-13-context-file-modes.md](plans/2026-09-13-context-file-modes.md) | Implementierungsplan — Context-File Modes (Phase 1 / Phase 2) | Phase 1 (Tasks 1–6) implementiert — Stand 2026-09-14 im Arbe… | 2026-09-13 |
| [plans/2026-09-13-opencode-runtime-gate.md](plans/2026-09-13-opencode-runtime-gate.md) | Implementierungsplan — OpenCode Runtime Gate (Problem A) | PHASE 0 COMPLETE — PHASE 1 (Tasks 8-9) DECLINED (won't-do) | 2026-09-13 |
| [plans/2026-09-13-progress-ledger-system.md](plans/2026-09-13-progress-ledger-system.md) | Progress / Ledger System Implementation Plan | geplant | 2026-09-13 |
| [plans/2026-09-13-progress-paths-config.md](plans/2026-09-13-progress-paths-config.md) | Implementierungsplan — Konfigurierbare Progress-/Checkpoint-Pfade | geplant | 2026-09-13 |
| [plans/2026-09-13-stale-role-cleanup.md](plans/2026-09-13-stale-role-cleanup.md) | Implementierungsplan — Stale Role Cleanup (B1 → B3 → B2) | complete | 2026-09-13 |
| [plans/2026-09-15-bugfix-block-744-749-750.md](plans/2026-09-15-bugfix-block-744-749-750.md) | Bugfix Block #744 / #749 / #750 Implementation Plan | planned (spec 'Status: APPROVED', 2026-09-15; 'git commit'/'… | 2026-09-15 |
| [plans/2026-09-15-reference-standards.md](plans/2026-09-15-reference-standards.md) | Implementierungsplan — Framework-Support für 'reference_standards' | geplant | 2026-09-15 |
| [plans/2026-09-16-lit-cluster-core-agents-stacking-note.md](plans/2026-09-16-lit-cluster-core-agents-stacking-note.md) | Stacking-Note — 'feat/lit-cluster-core-agents' (Cluster aus PR #795 + #791) | aufgelöst — Branch auf 'origin/main' rebased, PR-Basis auf '… | 2026-09-16 |
| [plans/2026-09-16-lit-cluster-product-planning-stacking-note.md](plans/2026-09-16-lit-cluster-product-planning-stacking-note.md) | Stacking-Note — 'feat/lit-cluster-product-planning' (Cluster aus PR #787 + #793) | aufgelöst — Branch auf 'origin/main' rebased, PR-Basis auf '… | 2026-09-16 |
| [plans/2026-09-16-lit-cluster-review-security-stacking-note.md](plans/2026-09-16-lit-cluster-review-security-stacking-note.md) | Stacking-Note — 'feat/lit-cluster-review-security' (Cluster aus PR #790 + #792) | aufgelöst — Branch auf 'origin/main' rebased, PR-Basis auf '… | 2026-09-16 |
| [plans/2026-09-16-lit-cluster-se-test-stacking-note.md](plans/2026-09-16-lit-cluster-se-test-stacking-note.md) | Stacking-Note — 'feat/lit-cluster-se-test' (Cluster aus PR #788 + #789) | aufgelöst — Branch auf 'origin/main' rebased, PR-Basis auf '… | 2026-09-16 |
| [plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md](plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md) | Dynamic Routing + Template Slimming — B2b-Diff-Manifest | abgeschlossen (Task 16) | 2026-09-19 |
| [plans/2026-09-19-dynamic-routing-template-slimming-plan.md](plans/2026-09-19-dynamic-routing-template-slimming-plan.md) | Dynamic Routing + Template Slimming — Implementation Plan | complete (umgesetzt, PR #833 gemergt; alle 68 Checkboxen ges… | 2026-09-19 |
| [plans/2026-09-19-dynamic-routing-template-slimming-snippet-preflight.md](plans/2026-09-19-dynamic-routing-template-slimming-snippet-preflight.md) | Snippet-Pre-Flight-Audit (RVW-20) | abgeschlossen | 2026-09-19 |
| [plans/2026-09-19-dynamic-routing-template-slimming-verification.md](plans/2026-09-19-dynamic-routing-template-slimming-verification.md) | Dynamic Routing + Template Slimming — Task 17 Verification Report | — | 2026-09-19 |
| [plans/2026-09-19-dynamic-routing-template-slimming-worktree-preflight.md](plans/2026-09-19-dynamic-routing-template-slimming-worktree-preflight.md) | Worktree-Preflight — Dynamic-Routing Template-Slimming | — | 2026-09-19 |
| [plans/2026-09-30-provider-audit-opencode-v2-plan.md](plans/2026-09-30-provider-audit-opencode-v2-plan.md) | Provider-Audit Gap Closure + Opencode v2 Support — Implementation Plan | ACTIVE (Spec APPROVED 2026-10-01) | 2026-09-30 |

### 2026-10

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [plans/2026-10-03-admin-ui-opencode-surface-plan.md](plans/2026-10-03-admin-ui-opencode-surface-plan.md) | Admin-UI + Project-Level 'surface-version' Gap Closure — Implementation Plan | geplant (amendment APPROVED 2026-10-03) | 2026-10-03 |
| [plans/2026-10-04-oreilly-cybersecurity-2026-role-enrichment.md](plans/2026-10-04-oreilly-cybersecurity-2026-role-enrichment.md) | Literature-Anchored Role Enrichment — O'Reilly "Cybersecurity Month 2026" | — | 2026-10-04 |
| [plans/2026-10-04-prioritized-issue-backlog-plan.md](plans/2026-10-04-prioritized-issue-backlog-plan.md) | Priorisierter Issue-Backlog — Ausführungsplan | proposed | 2026-10-04 |
| [plans/2026-10-05-backlog-execution-status.md](plans/2026-10-05-backlog-execution-status.md) | Backlog-Abarbeitungsstatus — 2026-10-05 | complete (Track A final) | 2026-10-05 |
| [plans/2026-10-06-bugfix-wave-plan.md](plans/2026-10-06-bugfix-wave-plan.md) | Bugfix-Wave — Implementierungsplan (52 Issues, 8 Cluster) | APPROVED | 2026-10-06 |
| [plans/2026-10-07-admin-ui-network-and-manager-plan.md](plans/2026-10-07-admin-ui-network-and-manager-plan.md) | Admin-UI Network-Mode (#897, #896) + Status #899/#855 — Spec + Implementation Plan | DRAFT | 2026-10-07 |
| [plans/2026-10-07-bugfix-batch-2.md](plans/2026-10-07-bugfix-batch-2.md) | Bugfix-Batch 2 — Umsetzung System-Review 2026-10-07 — Implementation Plan | APPROVED | 2026-10-08 |
| [plans/2026-10-11-context-profiles-plan.md](plans/2026-10-11-context-profiles-plan.md) | Context Profiles — Phase 0/1 Implementation Plan | geplant | 2026-10-11 |
| [plans/2026-10-17-context-profiles-phase2-plan.md](plans/2026-10-17-context-profiles-phase2-plan.md) | Context Profiles — Phase 2 Implementation Plan (Profil 'compact', Config-Optimizer) | APPROVED | 2026-10-17 |
| [plans/2026-10-18-context-profiles-phase2-status.md](plans/2026-10-18-context-profiles-phase2-status.md) | Context Profiles — Phase 2 Status / Handoff | — | 2026-10-18 |
| [plans/2026-10-22-opencode-entrypoint-1006-plan.md](plans/2026-10-22-opencode-entrypoint-1006-plan.md) | Opencode-Einstiegspunkt (#1006) — Implementation Plan | complete (APPROVED 2026-10-22; umgesetzt, PR #1010 gemergt) | 2026-10-22 |
| [plans/2026-10-22-opencode-execution-status.md](plans/2026-10-22-opencode-execution-status.md) | Opencode v2-Support — Ausführungsstatus (Plan B / Issue #1007) | — | 2026-10-22 |
| [plans/2026-10-22-opencode-v2-support-plan.md](plans/2026-10-22-opencode-v2-support-plan.md) | Opencode v2-Support (Phasen C0, B, C1/C2, C3, D) — Implementation Plan | complete (APPROVED 2026-10-22; umgesetzt, Phasen C0-D gemerg… | 2026-10-22 |
| [plans/2026-10-23-fleet-server-f1-plan.md](plans/2026-10-23-fleet-server-f1-plan.md) | Fleet-Server F1 (Phase 1+2: Read-Only-Dashboard + Config-Ansicht) Implementation Plan | geplant | 2026-10-23 |
| [plans/2026-10-23-fleet-server-f2-plan.md](plans/2026-10-23-fleet-server-f2-plan.md) | Fleet-Server F2 (Schreibpfad, Phase 3+4) — Implementation Plan | geplant | 2026-10-23 |
| [plans/2026-10-24-tmp-sink-injection-plan.md](plans/2026-10-24-tmp-sink-injection-plan.md) | Tmp-Sink-Injektion Implementation Plan | complete (APPROVED 2026-10-24; umgesetzt, PR #1023 gemergt, … | 2026-10-24 |
| [plans/2026-10-24-tmp-sink-injection-status.md](plans/2026-10-24-tmp-sink-injection-status.md) | Tmp-Sink-Injection — Ausführungsstatus | — | 2026-10-24 |
| [plans/2026-10-29-bugfix-wave-3-plan.md](plans/2026-10-29-bugfix-wave-3-plan.md) | Bugfix-Welle 3 (Rest-Welle) — Implementation Plan | complete (2026-10-30) — PR A #1047 (Merge '6f52326a'), PR B … | 2026-10-29 |
| [plans/ci-test-improvement-plan.md](plans/ci-test-improvement-plan.md) | CI- und Test-Verbesserungsplan | APPROVED | 2026-10-29 |
| [plans/2026-10-30-wave-4-continuation-plan.md](plans/2026-10-30-wave-4-continuation-plan.md) | Welle 4 — Fortsetzungsplan (Tracking) | Entwurf | 2026-10-30 |
| [plans/2026-10-31-bug-batch-plan.md](plans/2026-10-31-bug-batch-plan.md) | Bug Batch Implementation Plan | DONE (2026-11-04) — alle 22 Batch-Issues geschlossen; 9 PRs … | 2026-10-31 |
| [plans/2026-10-31-release-checklist-plan.md](plans/2026-10-31-release-checklist-plan.md) | Release Checklist Implementation Plan | DONE (2026-10-31) — branch 'feat/release-checklist', PR open… | 2026-10-31 |
| [plans/2026-10-31-test-environments-plan.md](plans/2026-10-31-test-environments-plan.md) | Test Environments Implementation Plan | DONE (2026-11-01) — branch 'feat/test-environments', PR open… | 2026-10-31 |
| [plans/2026-10-31-wave-4-p1-timeout-contract-plan.md](plans/2026-10-31-wave-4-p1-timeout-contract-plan.md) | Welle 4 / P1 — Timeout-Contract + Hook-Slice-Isolation (Implementation Plan) | abgeschlossen | 2026-10-31 |
| [plans/2026-10-31-wave-4-status.md](plans/2026-10-31-wave-4-status.md) | Welle 4 (Test-Hygiene #945) — Status / Pause-Punkt | pausiert (2026-10-31) | 2026-10-31 |

### 2026-11

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [plans/2026-11-04-orchestrator-topology-p3-plan.md](plans/2026-11-04-orchestrator-topology-p3-plan.md) | Orchestrator-Topologie P3 (Multi-Instanz) — Implementation Plan | geplant | 2026-11-04 |
| [plans/2026-11-04-orchestrator-topology-v1-plan.md](plans/2026-11-04-orchestrator-topology-v1-plan.md) | Orchestrator-Topologie v1 (P0–P2 + P4) — Implementation Plan | geplant | 2026-11-04 |
| [plans/2026-11-06-system-audit-remediation-plan.md](plans/2026-11-06-system-audit-remediation-plan.md) | System-Audit-Remediation 2026-11-06 — Implementation Plan | geplant | 2026-11-06 |
| [plans/2026-11-09-1189-tmp-sink-pin-plan.md](plans/2026-11-09-1189-tmp-sink-pin-plan.md) | Tmp-Sink-Pin vs. System-Temp-Root (Issue #1189) — Implementation Plan | APPROVED | 2026-11-09 |
| [plans/2026-11-09-artifact-locations-matrix-plan.md](plans/2026-11-09-artifact-locations-matrix-plan.md) | Artifact-Locations-Matrix für alle Artefakt-Klassen (Issue #1186) — Implementation Plan | APPROVED | 2026-11-09 |
| [plans/2026-11-09-commit-authority-grant-plan.md](plans/2026-11-09-commit-authority-grant-plan.md) | Projektseitiger Commit-Authority-Grant für Edit-only-Rollen (Issue #1181) — Implementation Plan | APPROVED | 2026-11-09 |
| [plans/2026-11-09-config-wave-overview.md](plans/2026-11-09-config-wave-overview.md) | Config-Welle #1187 / #1186 / #1188 / #1181 — Wave-Overview | APPROVED — Approved: 2026-11-09 (User-Freigabe via main_chat… | 2026-11-09 |
| [plans/2026-11-09-issue-label-taxonomy-plan.md](plans/2026-11-09-issue-label-taxonomy-plan.md) | Deklarative Issue-Label-Taxonomie mit steckbaren Tracker-Adaptern (#1188) — Umsetzungsplan | APPROVED | 2026-11-09 |
| [plans/2026-11-09-orchestrator-mode-topology-plan.md](plans/2026-11-09-orchestrator-mode-topology-plan.md) | Orchestrator 'mode' × 'topology' — Umsetzungsplan (#1190) | APPROVED | 2026-11-09 |
| [plans/2026-11-09-project-context-injection-scope-plan.md](plans/2026-11-09-project-context-injection-scope-plan.md) | Project-Context-Injection Scope — Implementation Plan | APPROVED — Approved: 2026-11-09 (User-Freigabe via main_chat… | 2026-11-09 |
| [plans/2026-11-14-agent-improvement-loop-plan.md](plans/2026-11-14-agent-improvement-loop-plan.md) | Agent-Verbesserungsschleife (alle Rollen) — Analyse und Implementation Plan | DRAFT | 2026-11-14 |
| [plans/2026-11-14-audit-top5-execution-plan.md](plans/2026-11-14-audit-top5-execution-plan.md) | Audit Top-5 Abarbeitung — Ausführungsplan | DRAFT | 2026-11-14 |
| [plans/2026-11-14-bugfix-batch-3-plan.md](plans/2026-11-14-bugfix-batch-3-plan.md) | Bugfix-Batch 3 — Implementation Plan | DRAFT | 2026-11-14 |
| [plans/2026-11-14-intent-routing-table-plan.md](plans/2026-11-14-intent-routing-table-plan.md) | Intent-Routing-Tabelle — Modernisierung (Konzept + Plan) | DRAFT | 2026-11-14 |
| [plans/2026-11-15-master-roadmap.md](plans/2026-11-15-master-roadmap.md) | Master-Roadmap — agent-meta (Stand origin/main 6bdc31ec, 2026-11-15) | DRAFT — Roadmap | 2026-11-15 |

### ohne Datum

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [plans/README.md](plans/README.md) | docs/plans/ | — | — |
| [plans/admin-server-split-backlog.md](plans/admin-server-split-backlog.md) | admin-server.py Split — Backlog | open | — |
| [plans/archive/admin-ui-token-report.md](plans/archive/admin-ui-token-report.md) | Admin-UI Remote-Token Fix — Report (#514) | — | — |
| [plans/archive/audit-2026-08-refactoring-roadmap.md](plans/archive/audit-2026-08-refactoring-roadmap.md) | Refactoring-Roadmap — Deep-Dive-Audit 2026-08-31 (Issues #560–#602) | — | — |
| [plans/archive/audit-2026-09-system-concept.md](plans/archive/audit-2026-09-system-concept.md) | Grobaudit: System-Konzept & Provider-Agnostik — 2026-09-02 | — | — |
| [plans/archive/issue-546-report.md](plans/archive/issue-546-report.md) | Issue #546 — Compact-Modus verlustfrei (Fix-Report) | — | — |
| [plans/archive/merge-main-report.md](plans/archive/merge-main-report.md) | Merge Report — beide Fix-Branches auf main (#514) | done | — |
| [plans/archive/model-inherit-activate-report.md](plans/archive/model-inherit-activate-report.md) | Report — Main-Chat Modell-Vererbung aktivieren | done | — |
| [plans/archive/push-main-report.md](plans/archive/push-main-report.md) | Push Report — main an origin gepusht (#514) | done | — |
| [plans/archive/report-2026-09-provider-support-claude-opencode-gemini.md](plans/archive/report-2026-09-provider-support-claude-opencode-gemini.md) | Kompakt-Bericht: Provider-Support — Claude Code / OpenCode / Antigravity (Gemini) | — | — |
| [plans/audit-2026-09-detailed-system-audit.md](plans/audit-2026-09-detailed-system-audit.md) | Detail-Audit: System, Templates, Doku, Config — 2026-09-03 | — | — |
| [plans/audit-admin-ui-model-loading.md](plans/audit-admin-ui-model-loading.md) | Audit: Admin-UI Model / Pricing Loading (All Providers) | — | — |
| [plans/hacs-platform-preset-audit.md](plans/hacs-platform-preset-audit.md) | HACS Platform Preset Audit (Issue #534) | — | — |
| [plans/issue-540-baseline.md](plans/issue-540-baseline.md) | Issue #540 — Context-Baseline (Phase A2) | — | — |
| [plans/issue-540-context-compression.md](plans/issue-540-context-compression.md) | Implementation Plan: #540 Context-File-Overhead Compression | — | — |

## specs (66)

### 2026-09

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [specs/2026-09-13-context-file-modes-design.md](specs/2026-09-13-context-file-modes-design.md) | Context-File Modes (unified / per-provider) — Technical Specification | APPROVED | 2026-09-13 |
| [specs/2026-09-13-context-file-modes-rereview.md](specs/2026-09-13-context-file-modes-rereview.md) | Context-File Modes — Spec Re-Review (independent critic, iteration 2) | — | 2026-09-13 |
| [specs/2026-09-13-context-file-modes-review.md](specs/2026-09-13-context-file-modes-review.md) | Context-File Modes (unified / per-provider) — Spec Review (independent critic) | — | 2026-09-13 |
| [specs/2026-09-13-context-file-modes-system-design.md](specs/2026-09-13-context-file-modes-system-design.md) | Context-File Modes — System Design | Entwurf | 2026-09-13 |
| [specs/2026-09-13-opencode-runtime-gate-design.md](specs/2026-09-13-opencode-runtime-gate-design.md) | OpenCode Runtime Gate (Problem A) — Technical Specification | APPROVED | 2026-09-13 |
| [specs/2026-09-13-opencode-runtime-gate-review-2.md](specs/2026-09-13-opencode-runtime-gate-review-2.md) | OpenCode Runtime Gate (Problem A) — Spec Re-Review (iteration 2) | — | 2026-09-13 |
| [specs/2026-09-13-opencode-runtime-gate-review.md](specs/2026-09-13-opencode-runtime-gate-review.md) | OpenCode Runtime Gate (Problem A) — Spec Review (independent critic) | — | 2026-09-13 |
| [specs/2026-09-13-opencode-runtime-gate-system-design.md](specs/2026-09-13-opencode-runtime-gate-system-design.md) | OpenCode Runtime Gate — System Design (Problem A) | Entwurf | 2026-09-13 |
| [specs/2026-09-13-progress-ledger-system-design.md](specs/2026-09-13-progress-ledger-system-design.md) | Progress / Ledger System Design | APPROVED | 2026-09-13 |
| [specs/2026-09-13-progress-paths-config-design.md](specs/2026-09-13-progress-paths-config-design.md) | Configurable Progress / Checkpoint Paths | APPROVED | 2026-09-13 |
| [specs/2026-09-13-stale-role-cleanup-design.md](specs/2026-09-13-stale-role-cleanup-design.md) | Stale Role Cleanup — Technical Specification | APPROVED | 2026-09-13 |
| [specs/2026-09-13-stale-role-cleanup-rereview.md](specs/2026-09-13-stale-role-cleanup-rereview.md) | Stale Role Cleanup — Spec Re-Review (independent critic) | — | 2026-09-13 |
| [specs/2026-09-13-stale-role-cleanup-review.md](specs/2026-09-13-stale-role-cleanup-review.md) | Stale Role Cleanup — Spec Review (independent critic) | — | 2026-09-13 |
| [specs/2026-09-13-stale-role-cleanup-system-design.md](specs/2026-09-13-stale-role-cleanup-system-design.md) | Stale Role Cleanup — System Design | Entwurf | 2026-09-13 |
| [specs/2026-09-15-bugfix-block-744-749-750-design.md](specs/2026-09-15-bugfix-block-744-749-750-design.md) | Bugfix Block — Release-Gate Artifact-Config Path (#744), Plugin-Catalog ProjectAtlas Entry (#749), Generated MCP Block Source Reference (#750) | APPROVED | 2026-09-15 |
| [specs/2026-09-15-reference-standards-design.md](specs/2026-09-15-reference-standards-design.md) | Framework-Support für das Agent-Frontmatter-Feld 'reference_standards' | APPROVED | 2026-09-15 |
| [specs/2026-09-15-reference-standards-review.md](specs/2026-09-15-reference-standards-review.md) | Reference Standards — Spec Review (independent critic) | APPROVED' was set (user pre-approved the direction/policy on… | 2026-09-15 |
| [specs/2026-09-19-dynamic-routing-template-slimming-final-rereview.md](specs/2026-09-19-dynamic-routing-template-slimming-final-rereview.md) | Finales Re-Review — Spec '2026-09-19-dynamic-routing-template-slimming.md' (Revision 3) | — | 2026-09-19 |
| [specs/2026-09-19-dynamic-routing-template-slimming-rereview.md](specs/2026-09-19-dynamic-routing-template-slimming-rereview.md) | Re-Review — Spec '2026-09-19-dynamic-routing-template-slimming.md' (Revision 2) | — | 2026-09-19 |
| [specs/2026-09-19-dynamic-routing-template-slimming-review.md](specs/2026-09-19-dynamic-routing-template-slimming-review.md) | Review — Spec '2026-09-19-dynamic-routing-template-slimming.md' | — | 2026-09-19 |
| [specs/2026-09-19-dynamic-routing-template-slimming.md](specs/2026-09-19-dynamic-routing-template-slimming.md) | Dynamic Routing + Template Slimming — Spec | APPROVED (2026-09-19) | 2026-09-19 |
| [specs/2026-09-30-provider-audit-opencode-v2-amendment-step1-review.md](specs/2026-09-30-provider-audit-opencode-v2-amendment-step1-review.md) | Amendment Step-1 Review — Provider-Audit Gap Closure + Opencode v2 | — | 2026-09-30 |
| [specs/2026-09-30-provider-audit-opencode-v2-design.md](specs/2026-09-30-provider-audit-opencode-v2-design.md) | Provider-Audit Gap Closure + Opencode v2 Support — System Design | Entwurf | 2026-09-30 |
| [specs/2026-09-30-provider-audit-opencode-v2-review.md](specs/2026-09-30-provider-audit-opencode-v2-review.md) | Review — Provider-Audit Gap Closure + Opencode v2 Support (Spec + Design) | — | 2026-09-30 |
| [specs/2026-09-30-provider-audit-opencode-v2.md](specs/2026-09-30-provider-audit-opencode-v2.md) | Provider-Audit Gap Closure + Opencode v2 Support — Spec | APPROVED (2026-10-01) | 2026-09-30 |

### 2026-10

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [specs/2026-10-03-admin-ui-opencode-surface-amendment.md](specs/2026-10-03-admin-ui-opencode-surface-amendment.md) | Admin-UI + Project-Level 'surface-version' Gap Closure — Spec Amendment | APPROVED (2026-10-03) | 2026-10-03 |
| [specs/2026-10-05-838-post-render-verification-review.md](specs/2026-10-05-838-post-render-verification-review.md) | Review — SPEC-838-POST-RENDER-VERIFICATION-2026-10-05 | — | 2026-10-05 |
| [specs/2026-10-05-838-post-render-verification.md](specs/2026-10-05-838-post-render-verification.md) | Post-Render Verification Stage — Mini-Spec / Design Note | proposed | 2026-10-05 |
| [specs/2026-10-06-844-compress-root-context-review.md](specs/2026-10-06-844-compress-root-context-review.md) | Spec-Review — Compress Generated Root Context (#844) | — | 2026-10-06 |
| [specs/2026-10-06-844-compress-root-context.md](specs/2026-10-06-844-compress-root-context.md) | Compress Generated Root Context (AGENTS.md/CLAUDE.md) — Technical Specification | APPROVED | 2026-10-06 |
| [specs/2026-10-06-852-mammouth-provider-fixes-review.md](specs/2026-10-06-852-mammouth-provider-fixes-review.md) | Concept-Review — Mammouth Provider Fixes (#852/#853/#857) | — | 2026-10-06 |
| [specs/2026-10-06-852-mammouth-provider-fixes.md](specs/2026-10-06-852-mammouth-provider-fixes.md) | Mammouth Provider Fixes — model-format, settings_file, mcp-config — Mini-Spec | APPROVED | 2026-10-06 |
| [specs/2026-10-06-855-copilot-subagent-capability-review.md](specs/2026-10-06-855-copilot-subagent-capability-review.md) | Spec Review — Copilot Subagent-Dispatch Capability Correction | — | 2026-10-06 |
| [specs/2026-10-06-855-copilot-subagent-capability.md](specs/2026-10-06-855-copilot-subagent-capability.md) | Copilot subagent-dispatch capability correction — Mini-Spec | APPROVED | 2026-10-06 |
| [specs/2026-10-07-339-se-housekeeper-standardization-review.md](specs/2026-10-07-339-se-housekeeper-standardization-review.md) | Concept-Review — SPEC-339-SE-HOUSEKEEPER-2026-10-07 | — | 2026-10-07 |
| [specs/2026-10-07-339-se-housekeeper-standardization.md](specs/2026-10-07-339-se-housekeeper-standardization.md) | SE-Kaskaden-Standardisierung — se-housekeeper & Rest-Arbeit (#339) | APPROVED | 2026-10-07 |
| [specs/2026-10-11-context-profiles-spec.md](specs/2026-10-11-context-profiles-spec.md) | Context Profiles (full/compact) — token-effiziente Kontextartefakte für alle 9 Provider | APPROVED | 2026-10-11 |
| [specs/2026-10-11-pr-templates-spec.md](specs/2026-10-11-pr-templates-spec.md) | PR-Templates (generic / platform / project, mit Variablen) — Feature-Spezifikation | DRAFT | 2026-10-11 |
| [specs/2026-10-22-opencode-entrypoint-1006-spec.md](specs/2026-10-22-opencode-entrypoint-1006-spec.md) | Opencode-Einstiegspunkt (#1006) — mode primary + default_agent auch auf v1, Gate-Kopplung, Managed-Merge | APPROVED | 2026-10-22 |
| [specs/2026-10-22-opencode-v2-support-spec.md](specs/2026-10-22-opencode-v2-support-spec.md) | Opencode v2-Support Phasen B-D (Config-Keys, Permissions/MCP/Gate-Plugin, Agent-Frontmatter nativ) | APPROVED | 2026-10-22 |
| [specs/2026-10-23-fleet-server-spec.md](specs/2026-10-23-fleet-server-spec.md) | Fleet-Server (Phasen 1-4) — Read-Only-Dashboard, Config-Ansicht, Remote-Sync-Trigger, Remote-Config-Edit | APPROVED (2026-10-29) | 2026-10-23 |
| [specs/2026-10-24-tmp-sink-injection-spec.md](specs/2026-10-24-tmp-sink-injection-spec.md) | Tmp-Sink-Injektion — Spec | APPROVED (2026-10-24) | 2026-10-24 |
| [specs/2026-10-29-bugfix-wave-3-spec.md](specs/2026-10-29-bugfix-wave-3-spec.md) | Bugfix-Welle 3 — Spec (Rest-Welle) | APPROVED (2026-10-29) | 2026-10-29 |
| [specs/2026-10-30-test-hygiene-945-design.md](specs/2026-10-30-test-hygiene-945-design.md) | Test-Hygiene #945 (Wave 4) — Spec | APPROVED (2026-10-31) | 2026-10-30 |
| [specs/2026-10-31-release-checklist-spec.md](specs/2026-10-31-release-checklist-spec.md) | Strukturierte Release-Checkliste (off\|advisory\|strict) mit Dry-Check | APPROVED | 2026-10-31 |
| [specs/2026-10-31-test-environments-spec.md](specs/2026-10-31-test-environments-spec.md) | Test-Umgebungen (lokal/remote) pro Projekt mit Remote-Freigabemodell | APPROVED | 2026-10-31 |

### 2026-11

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [specs/2026-11-03-orchestrator-topology-design.md](specs/2026-11-03-orchestrator-topology-design.md) | Orchestrator-Topologie konfigurierbar (primary \| subagent \| hybrid) — Systemdesign | Entwurf | 2026-11-03 |
| [specs/2026-11-04-orchestrator-topology-spec.md](specs/2026-11-04-orchestrator-topology-spec.md) | Orchestrator-Topologie konfigurierbar — Spec | APPROVED (2026-11-04) | 2026-11-04 |
| [specs/2026-11-06-system-audit-remediation-spec.md](specs/2026-11-06-system-audit-remediation-spec.md) | System-Audit-Remediation 2026-11-06 — Spec | APPROVED (2026-11-06) | 2026-11-06 |
| [specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-approval-note.md](specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-approval-note.md) | Freigabe-Vermerk (Rev 4) — 'SPEC-1189-tmp-sink-pin-vs-system-temp' | — | 2026-11-08 |
| [specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-rereview.md](specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-rereview.md) | Re-Review — Spec 'SPEC-1189-tmp-sink-pin-vs-system-temp' (Issue #1189), Revision 2 | — | 2026-11-08 |
| [specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-rereview2.md](specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-rereview2.md) | Re-Review-Nachtrag (Rev 3) — Spec 'SPEC-1189-tmp-sink-pin-vs-system-temp' | — | 2026-11-08 |
| [specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-review.md](specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-review.md) | Review — Spec 'SPEC-1189-tmp-sink-pin-vs-system-temp' (Issue #1189) | — | 2026-11-08 |
| [specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md](specs/2026-11-08-1189-tmp-sink-pin-vs-system-temp-spec.md) | Tmp-Sink-Pin vs. System-Temp-Root (Issue #1189) — Spec | APPROVED (2026-11-09) — durch den User freigegeben. Der Appr… | 2026-11-08 |
| [specs/2026-11-09-artifact-locations-matrix-spec.md](specs/2026-11-09-artifact-locations-matrix-spec.md) | Artifact-Locations-Matrix für alle Artefakt-Klassen (Issue #1186) — Spec | APPROVED — Approved: 2026-11-09 (User-Freigabe via main_chat… | 2026-11-09 |
| [specs/2026-11-09-commit-authority-grant-spec.md](specs/2026-11-09-commit-authority-grant-spec.md) | Projektseitiger Commit-Authority-Grant für Edit-only-Rollen | APPROVED | 2026-11-09 |
| [specs/2026-11-09-issue-label-taxonomy-spec.md](specs/2026-11-09-issue-label-taxonomy-spec.md) | Issue #1188 — Deklarative Issue-Label-Taxonomie mit steckbaren Tracker-Adaptern — Spec | APPROVED — Approved: 2026-11-09 (User-Freigabe via main_chat… | 2026-11-09 |
| [specs/2026-11-09-orchestrator-mode-topology-design.md](specs/2026-11-09-orchestrator-mode-topology-design.md) | Orchestrator 'mode' × 'topology' — Entscheidungs- und Design-Spec | APPROVED | 2026-11-09 |
| [specs/2026-11-09-project-context-injection-scope-spec.md](specs/2026-11-09-project-context-injection-scope-spec.md) | Project-Context-Injection Scope — Spec | APPROVED — Approved: 2026-11-09 (User-Freigabe via main_chat… | 2026-11-09 |
| [specs/2026-11-11-1000-checkpoint-tracking-spec.md](specs/2026-11-11-1000-checkpoint-tracking-spec.md) | Checkpoint-Tracking (#1000) — Spec | APPROVED (User, 2026-11-12) | 2026-11-12 |
| [specs/2026-11-11-phase-c-sync-config-spec.md](specs/2026-11-11-phase-c-sync-config-spec.md) | Phase C Sync/Config-Robustheit — Spec | APPROVED (User, 2026-11-12) | 2026-11-12 |
| [specs/2026-11-11-git-agent-merge-permission-spec.md](specs/2026-11-11-git-agent-merge-permission-spec.md) | Machbarkeit einer Permission-Regel nur für den git-Agenten (Merge) | DRAFT | 2026-11-13 |
| [specs/2026-11-11-guard-destructive-ask-spec.md](specs/2026-11-11-guard-destructive-ask-spec.md) | ask-Approval-Pfad für destruktive Git-Operationen im Orchestrator-Guard | DRAFT | 2026-11-13 |
| [specs/2026-11-11-guard-role-attribution-spec.md](specs/2026-11-11-guard-role-attribution-spec.md) | Rollenbindung im Orchestrator-Guard über ein Payload-Feld (Sentinel-Fälschbarkeit) | APPROVED | 2026-11-13 |
| [specs/2026-11-11-hook-single-parse-spec.md](specs/2026-11-11-hook-single-parse-spec.md) | Einmal-Parse der Hook-Payload (hook_json_get_many) im Orchestrator-Guard | APPROVED | 2026-11-13 |

### ohne Datum

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [specs/767-auto-commit-permission-authority.md](specs/767-auto-commit-permission-authority.md) | auto_commit Commit-Authority vs. tatsächliche Permissions — Spec | Entwurf \| Issue: #767 \| verwandt: #694, #706 | — |

## adr (2)

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [adr/0001-pyyaml-runtime-ausnahme.md](adr/0001-pyyaml-runtime-ausnahme.md) | ADR 0001: PyYAML als dokumentierte Runtime-Ausnahme | Accepted | 2026-10-30 |
| [adr/0002-orchestrator-mode-topology.md](adr/0002-orchestrator-mode-topology.md) | ADR 0002: Orchestrator 'mode' × 'topology' — Positionen, Gate-Zusagen und Defaults | Accepted | 2026-11-09 |

## reviews (15)

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [reviews/2026-10-07-system-review.md](reviews/2026-10-07-system-review.md) | System-Review agent-meta — 2026-10-07/08 | — | 2026-10-07 |
| [reviews/2026-10-11-context-profiles-spec-review-2.md](reviews/2026-10-11-context-profiles-spec-review-2.md) | Re-Review: SPEC-CONTEXT-PROFILES-2026-10-11 (Rev. 3, DRAFT) | — | 2026-10-11 |
| [reviews/2026-10-11-context-profiles-spec-review-3.md](reviews/2026-10-11-context-profiles-spec-review-3.md) | Drittes Review (begrenzt): SPEC-CONTEXT-PROFILES-2026-10-11 (Rev. 3.3, DRAFT) | — | 2026-10-11 |
| [reviews/2026-10-11-context-profiles-spec-review.md](reviews/2026-10-11-context-profiles-spec-review.md) | Review: SPEC-CONTEXT-PROFILES-2026-10-11 (Rev. 2.2, DRAFT) | — | 2026-10-11 |
| [reviews/2026-10-11-provider-support-und-bug-reduktionsplan.md](reviews/2026-10-11-provider-support-und-bug-reduktionsplan.md) | Provider-Support-Analyse und Bug-Reduktionsplan — 2026-10-11 | — | 2026-10-11 |
| [reviews/2026-10-11-w2-b1-dod-push-check-review-findings.md](reviews/2026-10-11-w2-b1-dod-push-check-review-findings.md) | Review-Befunde W2-B1 — 'dod-push-check.sh' (SR-B-02/03/04/21, SR-B-07) | — | 2026-10-11 |
| [reviews/2026-10-22-opencode-entrypoint-1006-spec-rereview.md](reviews/2026-10-22-opencode-entrypoint-1006-spec-rereview.md) | Re-Review: Opencode-Einstiegspunkt (#1006) — Spec Rev. 1.1 + Plan | — | 2026-10-22 |
| [reviews/2026-10-22-opencode-entrypoint-1006-spec-review.md](reviews/2026-10-22-opencode-entrypoint-1006-spec-review.md) | Review: Opencode-Einstiegspunkt (#1006) — Spec | — | 2026-10-22 |
| [reviews/2026-10-22-opencode-v2-support-spec-rereview.md](reviews/2026-10-22-opencode-v2-support-spec-rereview.md) | Re-Review: SPEC-OPENCODE-V2-SUPPORT-2026-10-22 (Rev. 1.1) und Plan | — | 2026-10-22 |
| [reviews/2026-10-22-opencode-v2-support-spec-review.md](reviews/2026-10-22-opencode-v2-support-spec-review.md) | Review: SPEC-OPENCODE-V2-SUPPORT-2026-10-22 (Rev. 1.0, Entwurf) | — | 2026-10-22 |
| [reviews/2026-10-24-tmp-sink-injection-spec-review.md](reviews/2026-10-24-tmp-sink-injection-spec-review.md) | Review — Tmp-Sink-Injektion Spec | — | 2026-10-24 |
| [reviews/2026-10-30-test-hygiene-945-rev3-narrow-review.md](reviews/2026-10-30-test-hygiene-945-rev3-narrow-review.md) | Narrow Review — SPEC-test-hygiene-945, Revision 3 | — | 2026-10-30 |
| [reviews/2026-11-03-orchestrator-topology-design-review.md](reviews/2026-11-03-orchestrator-topology-design-review.md) | Review — Orchestrator-Topologie (SPEC-orchestrator-topology-2026-11-03) | — | 2026-11-03 |
| [reviews/2026-11-09-orchestrator-mode-topology-rereview.md](reviews/2026-11-09-orchestrator-mode-topology-rereview.md) | Re-Review — Orchestrator 'mode' × 'topology' (#1190), Rev. 2 | — | 2026-11-09 |
| [reviews/2026-11-09-orchestrator-mode-topology-review.md](reviews/2026-11-09-orchestrator-mode-topology-review.md) | Review — Orchestrator 'mode' × 'topology' (#1190) | — | 2026-11-09 |

## guides (33)

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [guides/context-block-inventory.md](guides/context-block-inventory.md) | Context-Block-Inventory (Issue #540, Phase A3) | — | — |
| [guides/cross-harness-dev-isolation.md](guides/cross-harness-dev-isolation.md) | Cross-Harness Dev-Isolation via Separate Git Checkouts | — | — |
| [guides/framework-reference.md](guides/framework-reference.md) | Framework-Referenz | — | — |
| [guides/mcp-onboarding-checklist.md](guides/mcp-onboarding-checklist.md) | MCP Onboarding-Checkliste | — | — |
| [guides/mcp-setup.md](guides/mcp-setup.md) | MCP Setup — Best Practices | — | — |
| [guides/quality-pipelines.md](guides/quality-pipelines.md) | Quality Pipelines | — | — |
| [guides/reflection-loops.md](guides/reflection-loops.md) | Reflection-Loops — Generische Iterative Verbesserung | — | — |
| [guides/test-repo-validation.md](guides/test-repo-validation.md) | Test-Repository Validation | — | — |

### guides/ci

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [guides/ci/sync-check.md](guides/ci/sync-check.md) | CI: Provider Context Sync Check | — | — |

### guides/features

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [guides/features/agent-composition.md](guides/features/agent-composition.md) | Agent Composition — extends & patches | — | — |
| [guides/features/agent-delegation-map.md](guides/features/agent-delegation-map.md) | Agent Delegation Map | — | — |
| [guides/features/agent-isolation.md](guides/features/agent-isolation.md) | Agent Isolation — 'isolation: worktree' | — | — |
| [guides/features/agent-memory.md](guides/features/agent-memory.md) | Agent Memory — Persistentes Agenten-Gedächtnis | — | — |
| [guides/features/agent-versioning.md](guides/features/agent-versioning.md) | Agent-Versionierung | — | — |
| [guides/features/commands.md](guides/features/commands.md) | Commands — Slash Commands im agent-meta Layer-System | — | — |
| [guides/features/consistency-check.md](guides/features/consistency-check.md) | Howto: Consistency-Check | — | — |
| [guides/features/external-skills.md](guides/features/external-skills.md) | External Skills — Vollständige Anleitung | — | — |
| [guides/features/hooks.md](guides/features/hooks.md) | Hooks — Shell-Hooks im agent-meta Layer-System | — | — |
| [guides/features/lifecycle-triggers.md](guides/features/lifecycle-triggers.md) | Lifecycle Triggers — Agenten-Tasks bei Git-Events | — | — |
| [guides/features/platform-config.md](guides/features/platform-config.md) | Platform Config Instantiation | — | — |
| [guides/features/provider-abstraction-layer.md](guides/features/provider-abstraction-layer.md) | Provider Abstraction Layer (PAL) — Syntax-Isolation | — | — |
| [guides/features/recommended-skills.md](guides/features/recommended-skills.md) | Recommended Skills Registry — Anleitung | — | — |
| [guides/features/rules-preset-optimization.md](guides/features/rules-preset-optimization.md) | Rules-Optimierung für Token-Effizienz | — | — |
| [guides/features/rules.md](guides/features/rules.md) | Rules — Projekt-globale Regeln für alle Agenten | — | — |
| [guides/features/sync-concept.md](guides/features/sync-concept.md) | agent-meta Sync-Konzept | — | — |
| [guides/features/test-environments.md](guides/features/test-environments.md) | Test-Umgebungen ('test-environments') | — | — |

### guides/mcp

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [guides/mcp/honcho-setup.md](guides/mcp/honcho-setup.md) | Honcho MCP Setup | — | — |
| [guides/mcp/playwright-setup.md](guides/mcp/playwright-setup.md) | Playwright MCP — Setup | — | — |
| [guides/mcp/reqogniloom-setup.md](guides/mcp/reqogniloom-setup.md) | ReqogniLoom MCP Setup | — | — |

### guides/setup

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [guides/setup/config-layout.md](guides/setup/config-layout.md) | Config-Layout — Drei Ebenen, klare Zuständigkeiten | — | — |
| [guides/setup/first-steps.md](guides/setup/first-steps.md) | First Steps — agent-meta einrichten | — | — |
| [guides/setup/instantiate-project.md](guides/setup/instantiate-project.md) | Howto: Neues Projekt mit agent-meta einrichten | — | — |
| [guides/setup/upgrade-guide.md](guides/setup/upgrade-guide.md) | Upgrade Guide — agent-meta auf neue Version aktualisieren | — | — |

## api (7)

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [api/admin-ui-reference.md](api/admin-ui-reference.md) | Admin UI & Function Reference | — | — |
| [api/cli-reference.md](api/cli-reference.md) | CLI Reference: 'sync.py' | — | — |
| [api/composition-system.md](api/composition-system.md) | Agent-Meta Composition System | — | — |
| [api/pal-variables.md](api/pal-variables.md) | Provider Abstraction Layer (PAL) Variables | — | — |
| [api/slash-commands.md](api/slash-commands.md) | Slash Commands Reference | — | — |
| [api/viz-api.md](api/viz-api.md) | Viz-Report API-Dokumentation | — | — |
| [api/viz-event-schema.md](api/viz-event-schema.md) | Viz-Event-Schema | — | — |

## concepts (37)

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [concepts/2026-08-18-convention-profiles.md](concepts/2026-08-18-convention-profiles.md) | Konzept: Konfigurierbare Namens-/Versionierungs-Konventionen ("Convention Profiles") | Draft für Review-Stufe. Kein REQ-ID vergeben — Ideation-Phas… | 2026-08-18 |
| [concepts/a2a-handoff-protocol.md](concepts/a2a-handoff-protocol.md) | A2A-Handoff-Protokoll — Implementationsnahe Konzeptschärfung | Konzept v2.1 — Implementation-nah, entschlackt | — |
| [concepts/agent-meta-version-badge.md](concepts/agent-meta-version-badge.md) | Konzept — agent-meta Version-Badge | Draft (entschieden: Q1 Offer statt Force, Q2 tag-spezifische… | — |
| [concepts/architecture_law.md](concepts/architecture_law.md) | Overall Architectural Systems Engineering Breakdown Rules | — | — |
| [concepts/branch-guard-known-limits.md](concepts/branch-guard-known-limits.md) | Branch-Guard: Guard-Terminologie und bekannte Grenzen | — | — |
| [concepts/context-compaction-v2.md](concepts/context-compaction-v2.md) | Konzept: Modulare Context-Templates (Erweitert) | — | — |
| [concepts/integrations-framework.md](concepts/integrations-framework.md) | Generalisiertes Integrations-Framework für agent-meta — paket-verwaltete MCP-Tools (Referenz-Implementierung: semble v0.3.4) | — | — |
| [concepts/knowledge-engine-concept.md](concepts/knowledge-engine-concept.md) | Knowledge Engine für agent-meta — Konzept v4 (Final Deep-Dive) | Implementiert (Phase A-C abgeschlossen, main gemerged). Zwei… | — |
| [concepts/repo-containment-prison-mode.md](concepts/repo-containment-prison-mode.md) | Konzept — Repo-Containment („Gefängnis-Modus") & '.tmp'-Scratch-Sink | Accepted (Implementierung freigegeben; Umsetzung in diesem L… | — |
| [concepts/runtime-gate-tiers.md](concepts/runtime-gate-tiers.md) | Konzept — Runtime-Gate-Tiers des CRITICAL GATE | Accepted (Phase 0 implementiert und abgenommen; Phase 1 / Pl… | — |
| [concepts/subagent-permissions-git-admin-ui.md](concepts/subagent-permissions-git-admin-ui.md) | Technische Spezifikation — Subagent-Permission-Policy & Admin-UI-Sektion „Git" | Draft v2 (Review-CHANGES_REQUESTED B1/B2/M1-M5/m1-m8/n1-n3 e… | — |
| [concepts/viz-logging-mcp.md](concepts/viz-logging-mcp.md) | Konzept: Visualisierung & Logging Simplifizierung (MCP / CLI Fallback) | — | — |

### concepts/active

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [concepts/active/circuit-breaker-dod-gate-judge-pattern.md](concepts/active/circuit-breaker-dod-gate-judge-pattern.md) | Circuit-Breaker, DoD-as-Gate, and Judge/Validator Pattern | Concept (planned) | 2026-07-12 |
| [concepts/active/main-chat-orchestrator-mode.md](concepts/active/main-chat-orchestrator-mode.md) | Konzept: Main-Chat-Orchestrator-Modus | Umgesetzt — aktiv | — |
| [concepts/active/orchestrator-topology.md](concepts/active/orchestrator-topology.md) | Orchestrator-Topologie ('primary \| subagent \| hybrid') | Aktiv (v1, P0–P4) — implementiert am 2026-11-04; P3 (Multi-I… | — |
| [concepts/active/singleton-orchestrator-architecture.md](concepts/active/singleton-orchestrator-architecture.md) | Architektur: Provider-agnostische Subagent-Spawn-Restriction (Singleton-Orchestrator) | Aktiv — Body-Constraint Phase implementiert (2026-06-30) | — |

### concepts/archive

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [concepts/archive/2026-05-se-agent-concept.md](concepts/archive/2026-05-se-agent-concept.md) | Konzept: Systems Engineering Agenten-Kaskade | Konzept-Phase \| Branch: 'feat/se-agent-concept' | 2026-05-20 |
| [concepts/archive/2026-05-orchestrator-first-architecture.md](concepts/archive/2026-05-orchestrator-first-architecture.md) | Konzept: Orchestrator-First Architecture — Provider-agnostische Delegations-Pyramide | Konzept-Phase \| Branch: 'feat/orchestrator-first-architectu… | 2026-05-21 |
| [concepts/archive/2026-06-a2a-best-practice-analysis.md](concepts/archive/2026-06-a2a-best-practice-analysis.md) | A2A Best Practice Analysis | Konzept-Ergänzung | 2026-06-07 |
| [concepts/archive/2026-05-agent-visualization-dashboard-v1.md](concepts/archive/2026-05-agent-visualization-dashboard-v1.md) | Konzept: Agent-Visualisierungs-Dashboard (AVD) | Konzept-Entwurf \| Branch: 'feat/agent-visualization-dashboa… | — |
| [concepts/archive/2026-05-agent-visualization-v2.md](concepts/archive/2026-05-agent-visualization-v2.md) | Konzept: Agent-Visualisierung Dashboard v2 | Feature-Spezifikation \| Branch: 'feat/agent-visualization-d… | — |
| [concepts/archive/2026-06-prompt-modernization-draft-v2.md](concepts/archive/2026-06-prompt-modernization-draft-v2.md) | Konzept: Prompt-Modernisierung durch Two-Mode-Prompt-Architektur | Konzept-Entwurf v2.1 — überarbeitet nach Machbarkeits-Analys… | — |
| [concepts/archive/2026-06-prompt-modernization-phase1.md](concepts/archive/2026-06-prompt-modernization-phase1.md) | Prompt-Modernisierung — Konzept (Aktiv) | Aktiv — Phase 1 implementiert | — |
| [concepts/archive/2026-06-se-agent-implementation-plan.md](concepts/archive/2026-06-se-agent-implementation-plan.md) | Implementierungsplan: Systems Engineering Agenten-Kaskade (Generic Edition) | Entwurf | — |
| [concepts/archive/2026-06-se-cascade-optimization-339.md](concepts/archive/2026-06-se-cascade-optimization-339.md) | Konzept: SE-Kaskaden-Standardisierung — Issue #339 | Konzept-Entwurf v1.2 \| Datum: 2026-06-28 | — |
| [concepts/archive/2026-06-se-pipeline-extension.md](concepts/archive/2026-06-se-pipeline-extension.md) | Konzept: SE-Pipeline-Erweiterung — Teilresultat-Protokoll & Rollentrennung | Konzept-Phase \| Datum: 2026-06-21 | — |
| [concepts/archive/2026-06-se-principles-evaluation.md](concepts/archive/2026-06-se-principles-evaluation.md) | Evaluierung der generischen Systems-Engineering-Prinzipien | — | — |
| [concepts/archive/2026-06-se-und-prompt-modernisierung.md](concepts/archive/2026-06-se-und-prompt-modernisierung.md) | Konzept: SE-Kaskaden-Standardisierung & Prompt-Modernisierung | Konzept-Entwurf v1.0 — zusammengeführt aus se-cascade-optimi… | — |
| [concepts/archive/2026-08-a2a-best-practice-analysis.md](concepts/archive/2026-08-a2a-best-practice-analysis.md) | A2A Best-Practice-Analyse — Update 2026-08-07 | — | — |
| [concepts/archive/README.md](concepts/archive/README.md) | Archiv | — | — |

### concepts/archive/1-generic-modern

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [concepts/archive/1-generic-modern/developer.md](concepts/archive/1-generic-modern/developer.md) | Developer — {{PROJECT_NAME}} (Modern Mode) | — | — |

### concepts/planned

| Datei | Titel | Status | Datum |
|---|---|---|---|
| [concepts/planned/admin-ui-architecture.md](concepts/planned/admin-ui-architecture.md) | Architektur: agent-meta Admin-UI — Technische Spezifikation | Architektur-Entwurf v1.0 \| 2026-06-14 | — |
| [concepts/planned/admin-ui-concept.md](concepts/planned/admin-ui-concept.md) | Konzept: agent-meta Admin-UI — Config Surface & Workflow Editor | Konzept-Entwurf v1.0 \| 2026-06-14 | — |
| [concepts/planned/dynamic-model-presets.md](concepts/planned/dynamic-model-presets.md) | Konzept: Dynamische Modellerfassung & Tier-Presets | Umgesetzt | — |
| [concepts/planned/orchestrator-routing-test-suite.md](concepts/planned/orchestrator-routing-test-suite.md) | Konzept: Multi-Provider-Test-Suite für Orchestrator-Intent-Routing | Konzept-Entwurf v1.1 \| 2026-08-15 | — |
| [concepts/planned/review-agent-fleet.md](concepts/planned/review-agent-fleet.md) | Concept: Review-Agent Fleet (Frontend / Backend / Database / UI / Security) | PLANNED · Source: content audit (#528) + web research (2026-… | — |
| [concepts/planned/ui-expert-agents.md](concepts/planned/ui-expert-agents.md) | Konzept: UI-Experten-Rollen (Design-System & Frontend-Komponenten) | Konzept-Entwurf v1.2 (Owner-Override, siehe Abschnitt 10) \|… | — |

## Weitere Verzeichnisse

| Verzeichnis | Anzahl .md | Hinweis |
|---|---|---|
| [architecture/](architecture/) | 8 | Architektur-Dokumente |
| [conclusions/](conclusions/) | 9 | Abschlussberichte |
| [howto/](howto/) | 1 | Anleitungen |
| [issues/](issues/) | 5 | Issue-Notizen |
| [providers/](providers/) | 6 | Provider-Dokumentation |
| [se-cascade/](se-cascade/) | 9 | SE-Kaskaden-Artefakte |
| [spikes/](spikes/) | 4 | Spike-Ergebnisse |
| [superpowers/](superpowers/) | 42 | Massen-/generierte Artefakte; nur nach Anzahl gelistet, nicht einzeln indexiert |
| [testing/](testing/) | 1 | Testdokumentation |
| [ui/](ui/) | 1 | UI-Dateien (HTML/PNG, siehe Hinweis oben) plus Markdown |
