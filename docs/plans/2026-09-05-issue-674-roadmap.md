# Implementation Plan: Issue #674 — Consolidated Backlog Roadmap (P0–P4 Batches)

| | |
|---|---|
| **Date** | 2026-09-05 |
| **Status** | PROPOSED (analysis-based revision of the RFC in #674) |
| **Scope** | Repo-wide backlog execution order: hotfix, CISO security suite, core consolidation, provider harmonization, context/runtime/refactor/SE batches |
| **Issues** | Master: #674 · Hotfix: #476 (partial), test-encoding (new) · CISO: #666–#673 · Core: #476, #552, #528, #473, #479, #478, #484, #492, #661 · Providers: #614/#359 (done), Antigravity hooks, Copilot MCP · Context: #540, #437, #192, #395, #346 · Runtime: #267, #506, #266, #517, #264, #265 · Refactor: #481, #482, #483, #603, #547 · SE: #339, #364, #338, #334, #332, #330, #329, #370, #207, #527, #534, #548, #452, #523, #317, #318 |
| **Estimate** | Phase 0: ~0.5 pd · Phase 1: ~8–12 pd (8 issue-PRs) · Phase 2: ~6–9 pd · Phase 3: ~4–6 pd · Phases 4+: unbounded (per-batch estimates pending) |

---

## 1. Executive Summary

Issue #674 is an RFC/meta-issue that consolidates all 55 open backlog items into 8 prioritized
batches (P0–P4). This plan validates the RFC against the actual codebase state, applies
corrections (one batch item is already done), and turns the RFC into an actionable phased
execution order.

Key validation results:

- The two P0 blockers are **real** but environment-dependent: the `re.sub` escape bug in
  `scripts/lib/context_templates/builder.py:101` triggers only on values containing backslashes
  (Windows paths / regex-like data), and the fixture-test encoding bug triggers only on
  Windows `cp1252` locales. Both are trivially fixable and tested.
- **Batch 4 item 1 is obsolete**: branch `feat/plugin-catalog-unification` was merged TODAY
  (PR #665, commit `c4832c98`, 2026-09-05T17:52Z). `config/plugin-catalog.yaml`,
  `scripts/lib/plugins.py` and the migration-invariant test are already on `origin/main`.
- Provider claims verified: Gemini `has_hooks: false` + no `hooks` capability; Copilot
  capabilities lack `mcp`. Bonus finding: the 3 current `sync.py --validate` warnings
  (`orchestrator-strict.no-hook-support` for Opencode/Mammouth/Gemini) are directly resolved
  by the Batch 4 Antigravity-hooks task (Gemini) — and a working non-Claude hook-protocol
  reference implementation already exists (Codex provider: `hooks.json` + inline `[hooks]`).
- #476 (dual templating engines) confirmed: `substitute()` (`scripts/lib/variables.py:196`)
  coexists with `TemplateBuilder` (`scripts/lib/context_templates/builder.py`). The P0 bug
  exists only in `TemplateBuilder`; #476 is the permanent root-cause fix.

## 2. Corrections to the RFC

| RFC claim | Correction |
|---|---|
| Batch 4.1: merge `feat/plugin-catalog-unification` | **Done** (PR #665, merged 2026-09-05). Remove from backlog; action-plan "Phase 2" complete. |
| "54 open issues" | Actually 55 open (off-by-one; RFC written before merge-cycle churn). |
| "Acute blocker on Python 3.14" | Real bug, but platform/data-dependent, not version-specific (bad-escape in `re.sub` replacement strings exists since Python 3.7). Reproduced logically, not triggered on Linux/Py 3.13 (validate = PASS). |
| Action plan Phase 1: "directly on current branch" | Violates branch-guard. Hotfix must go on its own `fix/` branch via PR. |
| P0 batch = 5 items | Only items 1–2 are blockers; #557, #507, #496 are hygiene → move to P1-adjacent chore batch. |
| Missing: batch dependencies, per-batch DoD | Added in §4 below. Notably #395 (Headroom MCP) is now unblocked by the merged plugin catalog. |

## 3. Verified Facts (codebase, `origin/main` @ c4832c98)

1. `scripts/lib/context_templates/builder.py:101`: `rendered = re.sub(r'\{\{\s*' + re.escape(k) + r'\s*\}\}', str(v), rendered)` — raw replacement string; backslash values crash with `re.PatternError: bad escape \s` (or `\U` for Windows paths).
2. `tests/test_plugin_catalog_migration_invariant.py:21-22` (on `origin/main` after #665): `.read_text()` without `encoding=` → cp1252 corruption risk for German-umlaut fixtures on Windows.
3. `config/ai-providers.yaml`: Gemini → `has_hooks: false`, capabilities without `hooks`; Copilot → capabilities without `mcp`; Codex → full hook protocol (reference implementation for Antigravity task).
4. `sync.py --validate` on Linux/Py 3.13.5: PASS with 3 warnings (`orchestrator-strict.no-hook-support`: Opencode, Mammouth, Gemini).
5. Dual templating confirmed (see Executive Summary).
6. All referenced backlog issues re-checked OPEN (17 sampled incl. full CISO suite #666–#673).

## 4. Phases

### Phase 0 — Hotfix (P0, ~0.5 pd) — branch `fix/py314-escape-utf8`

| # | Task | Details |
|---|---|---|
| 0.1 | Sync local `main` | `git pull` (local main is 1 commit behind: `c4832c98`). Delegated to `git` agent. |
| 0.2 | Fix `builder.py:101` | Replace raw `str(v)` replacement with `lambda m, val=str(v): val`. |
| 0.3 | Fix test encoding | `read_text(encoding="utf-8")` in `test_plugin_catalog_migration_invariant.py` (+ audit sibling tests from #665 for the same pattern). |
| 0.4 | Regression test | Feed a value containing `C:\Users\x\s` through the `#each` loop; assert no `re.PatternError` and verbatim output. |
| 0.5 | Housekeeping PRs (from RFC P0 items 3–5) | #557 (gitignore provider dirs), #507 (container `--rm` footgun), #496 (post-merge branch cleanup in `git` agent) — separate small PRs, non-blocking. |
| 0.6 | Issue hygiene | Comment on #674: Batch 4.1 done via #665; link this plan. |

**DoD:** `python3 scripts/sync.py --validate` green (warnings acceptable), new regression test red-before/green-after, `rtk pytest` full suite green, conventional commits.

### Phase 1 — CISO Vibe-Coding Initiative (P1, ~8–12 pd) — branch per issue `feat/ciso-*`

Order: new agents first, then extensions.

| # | Issue | Deliverable |
|---|---|---|
| 1.1 | #667 | New agent `ai-security-guardian` (slopsquatting, unsafe cloud defaults) |
| 1.2 | #668 | New agent `prompt-governor` (prompts as source, PromptBOM, audit trail) |
| 1.3 | #669 | New agent `app-lifecycle-governor` (ownership, SLA, deprecation) |
| 1.4 | #666 | `security-auditor` checklists (frontend, auth, DIY-crypto, AI risks) |
| 1.5 | #670 | `code-reviewer` VCAL gate + AI-origin tracking |
| 1.6 | #673 | Rules: CISO checklist / security paved roads in DoD |
| 1.7 | #671 | `devops-engineer` staging validation + MTTG metrics |
| 1.8 | #672 | `prompt-engineer` secure-prompting checklist + banned patterns |

**DoD per item:** template in `agents/1-generic/` (provider-agnostic), frontmatter version bump per conventions skill, `sync.py` run on branch, no `if provider ==` branches, issue closed via PR keyword.

**Dependencies:** none on Phase 0 (pure prompt/templates, zero Python-core risk). Can start immediately after Phase 0 lands.

### Phase 2 — Core Architecture Consolidation (P2, ~6–9 pd) — branch `refactor/*` per item

| # | Issue | Notes |
|---|---|---|
| 2.1 | #476 | Unify `substitute()` + `TemplateBuilder` — permanent root-cause fix for the Phase 0 bug; keep one escape-safe substitution path. Highest architectural value. |
| 2.2 | #552 / #528 | Output contracts (STATUS/RESULT/ARTIFACTS) for remaining 34 agent templates; pytest ratchet green. |
| 2.3 | #473 | Canonical frontmatter parsing (dedupe 4×). |
| 2.4 | #479 | Consolidate YAML/JSON loading into `scripts/lib/io.py`. |
| 2.5 | #478 | Resolve circular dependency `agents ↔ config ↔ viz`. |
| 2.6 | #484, #492, #661 | Docstrings, review-findings follow-ups, MCP onboarding checklist (docs). |

**Dependencies:** 2.1 after Phase 0 (don't fix the same file twice in flight). 2.3–2.5 sequenced after 2.1 (shared module surface).

### Phase 3 — Provider Capabilities Harmonization (P2, ~4–6 pd)

| # | Task | Notes |
|---|---|---|
| 3.1 | Antigravity lifecycle hooks | Gemini: `has_hooks` + `hook_protocol` modeled on Codex reference; `hooks.json` (PreToolUse, PostToolUse, Stop). Resolves the Gemini `orchestrator-strict.no-hook-support` validate warning. Follows provider-agnostic policy — no `if provider ==` code. |
| 3.2 | Native delegation syntax for Gemini | `config/delegation-syntax.yaml`: `invoke_subagent(...)` toolcall instead of free-text instruction. |
| 3.3 | Copilot agent-mode MCP | Enable `mcp` capability + `.vscode/mcp.json` wiring. |

**Dependencies:** none hard; 3.1 benefits from Codex hook-protocol patterns shipped in #662.

### Phase 4 — Context / Runtime / Refactor / SE (P3/P4)

| Batch | Items | Sequencing note |
|---|---|---|
| 4a Context (P3) | #540 (managed-block slimming per arXiv:2602.11988), #437, #192, #395, #346 | #395 now **unblocked** (plugin catalog merged). Start with #540 RFC decision. |
| 4b Runtime (P3) | #267, #506, #266, #517, #264, #265 | Highest complexity; needs design spike before #265 (async barrier). |
| 4c Refactor (P3/P4) | #481, #482, #483, #603, #547 | #481–#483 are mechanical splits — good first issues. |
| 4d SE Cascade (P4) | #339, #364, #338, #334, #332, #330, #329, #370, #207, #527, #534, #548, #452, #523, #317, #318 | Domain backlog; run per-quarter. |

## 5. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Escape-fix changes template output | Regression test asserts verbatim output for backslash values; full suite + validate. |
| #476 unify touches every template path | Do after hotfix; golden-output comparison tests between engines before cutover. |
| CISO suite drifts provider-specific | Conventions skill + provider-agnostic review on each PR. |
| RFC stays stale | Treat #674 as living roadmap: tick off batches, comment on completion (issue-lifecycle skill). |
| Hook-protocol work regresses Claude hooks | Capability-flag pattern (`_has_capability`) only; path-collision tests from `test_provider_hooks_config.py` extended. |

## 6. Out of Scope

- Batches 5–8 detailed task-level estimates (needed per-batch before scheduling).
- Milestone/project-board setup on GitHub (optional follow-up).
- `rtk init -g` tool-hook integration into agent-meta's own hooks (separate decision).
