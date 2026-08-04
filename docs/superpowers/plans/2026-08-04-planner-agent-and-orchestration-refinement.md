# Planner Agent, Intent-Tabelle, Cluster-Cleanup, Delegation-Enforcement — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a native `planner` agent that turns concepts/REQs/bugs into ordered, executable plans consumed by `feature`; sharpen the orchestrator intent table; clean up 6 real quality issues across a 7-role cluster; and make the silent `orchestrator.strict` no-op on non-Claude providers visible via `sync.py --validate`.

**Architecture:** All changes are additive edits to existing agent-meta source layers (`agents/1-generic/*.md`, `config/role-defaults.yaml`, `knowledge/schema.md`, `scripts/lib/*.py`) plus one new Python consistency-check module and its pytest coverage. No new runtime component, no schema-breaking change. `sync.py` regenerates all derived output (`.claude/agents/*.md`, `.claude/rules/use-orchestrator.md`, etc.) from these sources — generated files are never hand-edited.

**Tech Stack:** Python 3.9–3.12 (stdlib + PyYAML), Markdown/YAML agent templates, pytest.

## Global Constraints

- `.claude/agents`, `.claude/rules/*` and all other provider output directories are generated — never edit them directly (see `.claude/rules/conventions.md`). Edit sources under `agents/1-generic/`, `config/`, `knowledge/`, `scripts/`.
- Bump the agent's frontmatter `version` on every content change to a template (`agents/1-generic/*.md`): major = renamed variable/behavior change/new mandatory section, minor = new optional section/expanded scope, patch = text clarification/config-path fix (`.claude/rules/conventions.md`).
- Placeholders are always `{{SCREAMING_SNAKE_CASE}}` — no other casing matches (`.claude/rules/conventions.md`).
- Conventional Commits, English, imperative, first line ≤72 chars (`.claude/rules/commit-conventions.md`).
- All git mutations (commit, push, add) go through the `git` agent — never run them directly in the main chat (`.claude/rules/use-orchestrator.md`, enforced live by `hooks/1-generic/orchestrator-guard.sh`).
- Work happens on the existing branch `feat/planner-agent-and-cluster-cleanup` — do not create a new branch, do not push without being asked.
- `sync.py --validate` and `python -m pytest tests/ -q` must both stay green (or improve) after every task that touches `scripts/lib/` or `agents/1-generic/`.

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `agents/1-generic/planner.md` | New agent template | create |
| `config/role-defaults.yaml` | Role registry (routing, tiers) | add `planner` entry; remove `Feature` keyword from `developer` |
| `scripts/lib/delegation_table.py` | Generates the orchestrator intent table | add Tier/Parallel clarification line |
| `agents/1-generic/_wf-orchestrator-reference.md` | Few-shot orchestrator patterns | fix Refactoring row |
| `scripts/lib/consistency/orchestrator_strict.py` | New consistency check | create |
| `tests/test_orchestrator_strict_visibility.py` | Coverage for the new check | create |
| `scripts/consistency-check.py` | Wires all consistency checks together | register the new check |
| `agents/1-generic/feature.md` | Feature lifecycle orchestrator | add Step 0 "Load plan", `plan_ref` payload/constraint/output field, description/hint trim, senior-developer escalation row |
| `knowledge/schema.md` | Knowledge Engine concept types | add `Plan` type |
| `agents/1-generic/ideation.md` | Scoping/exploration agent | description/hint trim, explicit boundary to `planner` |
| `agents/1-generic/concept-reviewer.md` | Concept critic | description/hint trim, remove dead `architect` cross-ref |
| `agents/1-generic/developer.md` | Feature/bugfix implementer | description/hint trim, remove dead `Agent` tool grant, dedupe self-verification paragraph |
| `agents/1-generic/senior-developer.md` | Senior implementer | dedupe self-verification paragraph (cross-reference `developer`) |
| `agents/1-generic/effort-estimator.md` | Effort estimation | add missing `TodoWrite` tool grant |

---

## Task 1: Create the `planner` agent template

**Files:**
- Create: `agents/1-generic/planner.md`

**Interfaces:**
- Produces: agent role name `planner`, frontmatter `tools: [Read, Write, Glob, Grep, TodoWrite]`, output artifact format `planner-output-v1` (Markdown table: `#, Step, Agent, Depends on, Acceptance criteria`) consumed by Task 8 (`feature.md` Step 0).

- [ ] **Step 1: Write the new template file**

```markdown
---
name: template-planner
version: "1.0.0"
description: "Use when a concept, REQ, or bug needs to be turned into a concrete, ordered implementation plan before work starts."
hint: "Nutze planner wenn ein Konzept/REQ/Bug in konkrete, geordnete Umsetzungsschritte übersetzt werden muss."
prompt_mode: modern
tools:
  - Read
  - Write
  - Glob
  - Grep
  - TodoWrite
---

> **Extension:** If `{{EXTENSION_DIR}}/{{PREFIX}}-planner-ext.md` exists → read and apply immediately.

<persona>
You are the **Planner** for {{PROJECT_NAME}}. You turn a concept, REQ, or bug into a concrete, ordered implementation plan — geordnete Tasks, Abhängigkeiten, Akzeptanzkriterien pro Schritt. You implement **nothing** yourself.

**Worker role:** Never re-delegate to `orchestrator`.
</persona>

<workflow>
## 1. Parse input

A2A envelope present → parse `payload.{t,ctx,con,refs,pri,dep}`. Otherwise: plain directive from `main_chat`. Accepted sources: a concept (`concept-<topic>.md` or Knowledge-Wiki `Concept` page), a REQ-ID (`docs/REQUIREMENTS.md`), or a bug description.

## 2. Decompose into ordered steps

- Break the source into the smallest set of sequential/parallel steps that each map to exactly one existing agent role (`developer`, `tester`, `requirements`, `senior-developer`, ...).
- Record dependencies between steps (which step must finish before the next can start).
- Write one measurable acceptance criterion per step — not "works correctly", but an observable, checkable outcome.

## 3. Estimate effort (delegate, do not duplicate)

Reference `effort-estimator` in text for an overall effort summary — do not call it as a tool, do not compute your own effort numbers. Consistent with the `developer`/`senior-developer` delegation pattern (text reference only, see `<constraints>`).

## 4. Persist (dual convention)

- **Knowledge Engine active** (`project.yaml` → `knowledge-engine.enabled: true`): write directly to `knowledge/wiki/plans/<topic>.md` with frontmatter `type: Plan` (see `knowledge/schema.md`). Update `knowledge/wiki/index.md` and `knowledge/wiki/log.md` yourself, same OKF frontmatter/log conventions `knowledge-ingestor` uses for other sources — no delegation to `knowledge-ingestor` (avoids a redundant agent hop for a single artifact).
- **Knowledge Engine inactive:** write `plan-<topic>.md` in the project root (same naming convention as `ideation`'s `concept-<topic>.md`).

## 5. Hand off

Report the plan using `<output_contract>`. Do not auto-trigger `feature` — the user/orchestrator decides whether and when the plan is executed (pass the persisted path as `payload.plan_ref` when they do).
</workflow>

<context>
**Project context:** {{PROJECT_CONTEXT}}
**Goal:** {{PROJECT_GOAL}}
**Languages:** {{PROJECT_LANGUAGES}}

## Boundary to `ideation`

`ideation` scopes a raw idea (no ordered plan, no agent assignment). `planner` starts once the input is a concept, REQ, or bug — it never runs the initial scoping conversation.
</context>

<tools>
- **Read** — read the source concept/REQ/bug
- **Write** — persist `plan-<topic>.md` or the Knowledge-Wiki page
- **Glob/Grep** — check existing project structure before assigning steps to roles
- **TodoWrite** — track decomposition for plans with >3 steps
</tools>

<output_contract>
```
## Plan: <title>

**Source:** <REQ-ID | concept-<topic>.md | Bug-#NNN>
**Estimated effort:** <effort-estimator summary, text reference>

| # | Step | Agent | Depends on | Acceptance criteria |
|---|---|---|---|---|
| 1 | <task> | <role> | — | <measurable> |
| 2 | <task> | <role> | 1 | <measurable> |

**Persisted to:** <knowledge/wiki/plans/<topic>.md | plan-<topic>.md>
```
</output_contract>

<constraints>
- Never implement — only plan
- Every step must map to exactly one existing agent role
- Every acceptance criterion must be measurable/observable — no "works correctly"
- Reference `effort-estimator` in text only — never delegate via tool call
- Do not auto-hand-off to `feature` — report the plan and let the user/orchestrator decide

**User proxy:** `main_chat`.

**Language:** communication → {{COMMUNICATION_LANGUAGE}}. Plan artifacts → project language.
</constraints>
```

- [ ] **Step 2: Verify frontmatter parses and the file matches sibling conventions**

Run: `python -c "import yaml,sys; txt=open('agents/1-generic/planner.md',encoding='utf-8').read(); end=txt.find(chr(10)+'---',3); yaml.safe_load(txt[3:end]); print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add agents/1-generic/planner.md
git commit -m "feat: add planner agent template"
```

## Task 2: Register `planner` in `config/role-defaults.yaml`

**Files:**
- Modify: `config/role-defaults.yaml:180-181` (insert new block between the `ideation` block, which ends at line 180, and the `feature:` block, which starts at line 181)

**Interfaces:**
- Produces: role entry `planner` with `workflow_tier: recommended` — required by `scripts/lib/consistency/crossrefs.py::check_role_defaults_coverage` (every `agents/1-generic/*.md` must have a matching entry) and `check_orchestrator_table` (every `required`/`recommended` role must appear in the generated intent table).

- [ ] **Step 1: Insert the new role block**

Insert immediately before the existing `  feature:` line (currently line 181):

```yaml
  planner:
    model: balanced
    memory: ''
    workflow_tier: recommended
    description: Erzeugt konkrete, geordnete Umsetzungspläne aus Konzepten/REQs/Bugs
    routing:
      intent_keywords:
      - Plan
      - Planung
      - Schritte
      - Umsetzungsplan
      - "wie setzen wir das um"
      parallel: false
      orchestrator_only: false
    short_desc: Umsetzungsplanung
```

- [ ] **Step 2: Remove the `Feature` keyword collision from `developer`**

In the `developer:` block (currently lines 19-25), remove the `- Feature` line so `intent_keywords` reads:

```yaml
    routing:
      intent_keywords:
      - Bugfix
      - Refactoring
      - Implementierung
      - Code schreiben
      parallel: true
      orchestrator_only: false
```

- [ ] **Step 3: Validate YAML and role coverage**

Run: `python -c "import yaml; yaml.safe_load(open('config/role-defaults.yaml',encoding='utf-8'))" && echo OK`
Expected: `OK`

Run: `python scripts/consistency-check.py`
Expected: no new `crossrefs.role-not-in-role-defaults` or `crossrefs.orchestrator-table-incomplete` finding for `planner` (it will still show `orchestrator-table-incomplete` until Task 16 regenerates `.claude/rules/use-orchestrator.md` — that is expected at this point, not a regression).

- [ ] **Step 4: Commit**

```bash
git add config/role-defaults.yaml
git commit -m "feat: register planner role, drop Feature keyword clash on developer"
```

## Task 3: Document that "Parallel" is informational-only in the generated intent table

**Files:**
- Modify: `scripts/lib/delegation_table.py:57-60`

**Interfaces:**
- Consumes: nothing new (pure string literal change inside `get_intent_routing_table`).
- Produces: an extra Markdown line above the table header, present in every regenerated `use-orchestrator.md`.

- [ ] **Step 1: Add the clarification line**

Change:

```python
    table_lines = [
        "| Intent / Keywords | Agent | Tier | Parallel |",
        "|-------------------|-------|------|----------|"
    ]
```

to:

```python
    table_lines = [
        "> Parallel ist rein informativ — kein Runtime-Enforcement, nur CI-Konsistenzcheck bei required/recommended-Tier-Abdeckung.",
        "",
        "| Intent / Keywords | Agent | Tier | Parallel |",
        "|-------------------|-------|------|----------|"
    ]
```

- [ ] **Step 2: Verify by generating the table in isolation**

Run:
```bash
python -c "
import sys; sys.path.insert(0, 'scripts')
from pathlib import Path
from lib.delegation_table import get_intent_routing_table
from lib.config import load_config
cfg = load_config(Path('.meta-config/project.yaml'))
print(get_intent_routing_table(Path('.'), cfg, {})[:200])
"
```
Expected: output starts with `> Parallel ist rein informativ...`

- [ ] **Step 3: Commit**

```bash
git add scripts/lib/delegation_table.py
git commit -m "docs: clarify Parallel column is informational-only in intent table"
```

## Task 4: Fix the Refactoring few-shot pattern in `_wf-orchestrator-reference.md`

**Files:**
- Modify: `agents/1-generic/_wf-orchestrator-reference.md:18`

**Interfaces:** none (standalone documentation table row).

- [ ] **Step 1: Replace the wrong agent in the pattern**

Change:
```
| Refactoring | ideation→dev→tester→review→git |
```
to:
```
| Refactoring | explorer→dev→tester→review→git |
```

- [ ] **Step 2: Verify no other reference to the old pattern exists**

Run: `grep -rn "ideation→dev" agents/ docs/ 2>/dev/null || echo "none found"`
Expected: `none found`

- [ ] **Step 3: Commit**

```bash
git add agents/1-generic/_wf-orchestrator-reference.md
git commit -m "fix: correct Refactoring few-shot pattern (ideation -> explorer)"
```

## Task 5: New consistency check — `orchestrator.strict` silent no-op visibility

**Files:**
- Create: `scripts/lib/consistency/orchestrator_strict.py`
- Test: `tests/test_orchestrator_strict_visibility.py`

**Interfaces:**
- Consumes: `scripts.lib.consistency.report.Finding`, `Severity` (constructor `Finding(severity, check, file, message, suggestion="")`, see `scripts/lib/consistency/report.py:28-34`); `scripts.lib.providers.load_providers_config`, `resolve_providers` (see `scripts/lib/providers.py:12,42`).
- Produces: `check_orchestrator_strict_hook_support(project_root: Path, config: dict, provider_config: dict) -> list[Finding]`, consumed by Task 6 (`sync.py` wiring).

- [ ] **Step 1: Write the failing test**

```python
"""Tests for scripts/lib/consistency/orchestrator_strict.py.

Covers Entscheidung 7 of docs/superpowers/specs/2026-08-02-agent-orchestration-refinement-design.md:
`orchestrator.strict: true` has zero runtime effect on providers whose
config/ai-providers.yaml entry has `has_hooks: false` (e.g. Opencode, Gemini) --
this must surface as a WARNING, not stay a silent no-op.

Run: python -m pytest tests/test_orchestrator_strict_visibility.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.consistency.orchestrator_strict import check_orchestrator_strict_hook_support
from lib.consistency.report import Severity

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _provider_config():
    from lib.providers import load_providers_config
    return load_providers_config(_REPO_ROOT)


def test_warns_for_active_provider_without_hook_support():
    config = {"ai-providers": ["Claude", "Opencode"],
              "orchestrator": {"enabled": True, "strict": True}}
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert any(f.severity == Severity.WARNING and "Opencode" in f.message for f in findings)


def test_no_warning_when_only_hook_capable_providers_active():
    config = {"ai-providers": ["Claude"],
              "orchestrator": {"enabled": True, "strict": True}}
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert findings == []


def test_no_warning_when_strict_mode_off():
    config = {"ai-providers": ["Claude", "Opencode"],
              "orchestrator": {"enabled": True, "strict": False}}
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert findings == []


def test_provider_override_narrows_strict_mode_to_claude_only():
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {
            "enabled": True,
            "strict": True,
            "provider-overrides": {"Opencode": {"mode": "advisory"}},
        },
    }
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert findings == []
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `python -m pytest tests/test_orchestrator_strict_visibility.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'lib.consistency.orchestrator_strict'`

- [ ] **Step 3: Implement the check**

```python
"""Consistency check: is orchestrator.strict actually enforceable on every active provider?

hooks/1-generic/orchestrator-guard.sh is the only runtime enforcement of
orchestrator.strict — and scripts/lib/hooks.py only wires PreToolUse hooks
for providers whose config/ai-providers.yaml entry sets has_hooks: true
(currently Claude, Mammouth). On every other active provider (Opencode,
Gemini, Continue, Copilot as of this writing), orchestrator.strict is a
silent no-op: the setting exists in .meta-config/project.yaml, but nothing
enforces it. This mirrors the mode-resolution logic in
hooks/1-generic/orchestrator-guard.sh's resolve_mode() so the two stay in
sync -- provider-overrides can legitimately narrow strict mode to a subset
of providers.
"""

from pathlib import Path

from .report import Finding, Severity


def _resolve_effective_strict(orch: dict, provider: str) -> bool:
    """Mirror resolve_mode() in hooks/1-generic/orchestrator-guard.sh."""
    override = orch.get("provider-overrides", {}).get(provider, {})
    mode = override.get("mode")
    if mode is not None:
        return str(mode).strip().lower() == "strict"
    strict = orch.get("strict", False)
    enabled = orch.get("enabled", True)
    return bool(strict) and bool(enabled)


def check_orchestrator_strict_hook_support(project_root: Path, config: dict,
                                            provider_config: dict) -> list[Finding]:
    """Warn when orchestrator.strict is effectively active for a provider with no
    PreToolUse hook wiring (config/ai-providers.yaml has_hooks: false)."""
    from .. import providers as providers_lib

    findings: list[Finding] = []
    orch = config.get("orchestrator", {})
    if not orch:
        return findings

    active_providers = providers_lib.resolve_providers(config, provider_config)
    for provider in active_providers:
        if not _resolve_effective_strict(orch, provider):
            continue
        pc = provider_config.get(provider, {})
        if pc.get("has_hooks", False):
            continue
        findings.append(Finding(
            Severity.WARNING,
            "orchestrator-strict.no-hook-support",
            ".meta-config/project.yaml",
            f"orchestrator.strict is active for provider '{provider}', but this "
            f"provider has no PreToolUse hook wiring (config/ai-providers.yaml: "
            f"has_hooks: false) — the setting has no runtime effect there.",
            f"Add a provider-overrides entry to scope strict mode to hook-capable "
            f"providers only, or accept that delegation is not enforced on '{provider}'.",
        ))
    return findings
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python -m pytest tests/test_orchestrator_strict_visibility.py -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/consistency/orchestrator_strict.py tests/test_orchestrator_strict_visibility.py
git commit -m "feat: warn when orchestrator.strict has no hook support on a provider"
```

## Task 6: Wire the new check into `sync.py --validate`

**Files:**
- Modify: `scripts/sync.py:840-863` (the `elif args.validate:` block)

**Interfaces:**
- Consumes: `check_orchestrator_strict_hook_support` from Task 5; `load_providers_config`, `resolve_providers` (already imported elsewhere in `sync.py`, e.g. `scripts/sync.py:357`).
- Produces: WARNING-level findings printed via the existing `print_report`, without affecting the process exit code (matches Entscheidung 7: "WARNING statt Hard-Fail").

- [ ] **Step 1: Extend the validate branch**

In `scripts/sync.py`, inside `elif args.validate:` (currently lines 840-863), after the existing `consistency_errors = _run_consistency_checks(agent_meta_root)` line, add:

```python
        from lib.consistency.orchestrator_strict import check_orchestrator_strict_hook_support
        from lib.consistency.report import print_report
        from lib.providers import load_providers_config as _load_pc, resolve_providers as _resolve_p

        _provider_config = _load_pc(agent_meta_root)
        _strict_findings = check_orchestrator_strict_hook_support(project_root, config, _provider_config)
        if _strict_findings:
            print_report(_strict_findings, project_root, changed_only=False)
```

Place this directly after the `consistency_errors = ...` line and before the `test_repo_path = resolve_test_repo_path(...)` line. Do **not** add `_strict_findings` to `consistency_errors` — these are warnings only, per Entscheidung 7 ("kein Hard-Fail — Sichtbarkeit, keine neue harte Gate-Bedingung").

- [ ] **Step 2: Verify against this repo's own config**

Run: `python scripts/sync.py --validate`
Expected: output includes a line matching `orchestrator-strict.no-hook-support` for `Opencode` and for `Gemini` (this repo's `.meta-config/project.yaml` has `ai-providers: [Claude, Opencode, Gemini]` and `orchestrator.strict: true`, and both Opencode and Gemini have `has_hooks: false` in `config/ai-providers.yaml`). Exit code is unaffected by these warnings (still 0 if no other errors).

- [ ] **Step 3: Commit**

```bash
git add scripts/sync.py
git commit -m "feat: surface orchestrator-strict hook-support warning in sync.py --validate"
```

## Task 7: `feature.md` — Step 0 "Load plan", `plan_ref` payload, cleanup #1 + #3

**Files:**
- Modify: `agents/1-generic/feature.md`

**Interfaces:**
- Consumes: `planner-output-v1` artifact format from Task 1 (`plan-<topic>.md` or Knowledge-Wiki `Plan` page with columns `#, Step, Agent, Depends on, Acceptance criteria`).
- Produces: `payload.plan_ref` field understood by any future orchestrator prompt that hands off a plan.

- [ ] **Step 1: Trim frontmatter description/hint (cleanup #1)**

Change lines 4-5 from:
```yaml
description: "Full feature lifecycle: Branch → Requirements → TDD → Implementation → Validation → Commit → PR."
hint: "Feature lifecycle subagent: Branch → REQ → TDD → Dev → Validate → PR. Started by the orchestrator, not directly by the user."
```
to:
```yaml
description: "Use when the orchestrator needs to run a full feature lifecycle (branch through PR) instead of a single delegated step."
hint: "Nur vom Orchestrator gestartet — orchestriert den kompletten Feature-Lifecycle, nie direkt vom User aufrufen."
```

- [ ] **Step 2: Bump version (minor — new optional workflow step)**

Change line 3 from `version: "1.10.1"` to `version: "1.11.0"`.

- [ ] **Step 3: Insert Step 0 "Load plan" before the existing lifecycle table**

In the `<workflow>` block, immediately before `## 2. Feature lifecycle (8 steps)`, insert:

```markdown
## 0. Load plan (optional)

**Active when:** `payload.plan_ref` is set.

1. Read the referenced plan (`plan-<topic>.md` or a Knowledge-Wiki `Plan` page).
2. Validate: table with columns `#, Step, Agent, Depends on, Acceptance criteria` present, at least one row, no circular dependencies in "Depends on".
3. On invalid plan: report the missing/broken fields, abort — do not create a branch, do not start step 1.
4. Map plan steps onto the lifecycle phases below by `Agent` column: `tester` → step 3, `developer` → step 4, `requirements` → step 2 (if not already satisfied).

```

- [ ] **Step 4: Renumber to "1." and add senior-developer escalation row (cleanup #3)**

Change `## 2. Feature lifecycle (8 steps)` to `## 1. Feature lifecycle (8 steps)`, and add an escalation note directly under the existing table (after the `**After 8:**` line):

```markdown
**Escalation:** if `developer` (step 4) returns `STATUS: escalate`, re-run step 4 with `senior-developer` instead — same task, same context, `payload.ctx` carries the escalation findings.
```

- [ ] **Step 5: Add `plan_ref` to the A2A inbound payload docs and constraints**

In `## 1. Parse input` (renumber existing numbered sections by +0, this section keeps its heading text, only the following section numbers shift by the new Step 0 above it — do not renumber "1. Parse input" itself), add one line:

```markdown
`payload.plan_ref` (optional): relative path to a plan file/page in `planner-output-v1` format — triggers Step 0.
```

In `<constraints>`, add:
```markdown
- When `plan_ref` is set: validate the plan before branch creation. Do not create a branch for an invalid plan.
```

- [ ] **Step 6: Add `PLAN_REF` to the output contract**

In `<output_contract>`, add a line after `REQ_ID: <id>`:
```
PLAN_REF: <path | n/a>
```

- [ ] **Step 7: Verify frontmatter still parses and consistency-check passes on this file**

Run: `python scripts/consistency-check.py --file agents/1-generic/feature.md`
Expected: no new ERROR-severity finding (existing PASS baseline preserved).

- [ ] **Step 8: Commit**

```bash
git add agents/1-generic/feature.md
git commit -m "feat: add plan_ref handoff and senior-developer escalation to feature lifecycle"
```

## Task 8: Add the `Plan` concept type to `knowledge/schema.md`

**Files:**
- Modify: `knowledge/schema.md:33` (insert a new table row after the `Session Conclusion` row)

**Interfaces:**
- Consumes: nothing.
- Produces: `type: Plan` frontmatter value, used by Task 1's planner persistence and validated by `knowledge-linter` (no code change needed there — it already accepts any type listed in this table per its existing OKF-compliance check).

- [ ] **Step 1: Add the new row**

After:
```markdown
| `Session Conclusion` | `knowledge/wiki/sources/` | Summary of a completed work session (decisions made, what changed, follow-ups) |
```
add:
```markdown
| `Plan` | `knowledge/wiki/plans/` | Concrete, ordered implementation plan derived from a concept, REQ, or bug — produced by the `planner` role |
```

- [ ] **Step 2: Create the target directory placeholder**

Run: `mkdir -p knowledge/wiki/plans` (no file needed yet — the directory is created lazily by `planner` on first write; this step only pre-creates it so `git status` reflects the new location cleanly if the user inspects the tree before first use — skip if the directory already tracked via `.gitkeep` convention elsewhere in `knowledge/wiki/`; check with `ls knowledge/wiki/` first and match the existing pattern).

- [ ] **Step 3: Verify no existing type conflicts**

Run: `grep -n "^| \`Plan\`" knowledge/schema.md`
Expected: exactly one match (the row just added).

- [ ] **Step 4: Commit**

```bash
git add knowledge/schema.md
git commit -m "docs: add Plan concept type for planner role output"
```

## Task 9: `ideation.md` — scope clarification + cleanup #1

**Files:**
- Modify: `agents/1-generic/ideation.md`

- [ ] **Step 1: Trim frontmatter description/hint (cleanup #1)**

Change lines 4-5 from:
```yaml
description: "Idea generation, vision sharpening and concept concretization — asks questions, thinks around corners, hands mature ideas to Requirements."
hint: "Explore new ideas, sharpen vision, hand off to requirements"
```
to:
```yaml
description: "Use when an idea needs scoping and thoughts need sorting before a concept or REQ exists."
hint: "Nutze ideation zum Scopen einer rohen Idee, bevor ein Konzept oder REQ existiert."
```

- [ ] **Step 2: Bump version (minor — clarified boundary, still same behavior)**

Change line 3 from `version: "1.6.2"` to `version: "1.7.0"`.

- [ ] **Step 3: Add the explicit boundary to `planner` (Entscheidung 5)**

In `<constraints>` (currently lines 114-119), add as the last bullet before `**User proxy:**`:
```markdown
- Do not produce an ordered implementation plan — hand off to `planner` for that.
```

- [ ] **Step 4: Verify**

Run: `python scripts/consistency-check.py --file agents/1-generic/ideation.md`
Expected: no new ERROR-severity finding.

- [ ] **Step 5: Commit**

```bash
git add agents/1-generic/ideation.md
git commit -m "docs: sharpen ideation scope, trim description/hint, add planner boundary"
```

## Task 10: `concept-reviewer.md` — dead cross-ref + cleanup #1

**Files:**
- Modify: `agents/1-generic/concept-reviewer.md`

- [ ] **Step 1: Trim frontmatter description (cleanup #1)**

Change line 4 from:
```yaml
description: "Generic concept critic: reviews design docs and concepts for completeness, logic gaps, assumptions, alternatives, risks, feasibility, and consistency."
```
to:
```yaml
description: "Use when a concept or design doc needs a structural review before requirements — completeness, logic, assumptions, risks, feasibility."
```
`hint` (line 5) already reads as a trigger — leave unchanged.

- [ ] **Step 2: Remove the dead `architect` cross-ref**

Change line 94 from:
```markdown
**Not your job:** code review → `code-reviewer` · engineering review → `se-critic` · requirement capture → `requirements` · implementation details → `developer`/`architect`
```
to:
```markdown
**Not your job:** code review → `code-reviewer` · engineering review → `se-critic` · requirement capture → `requirements` · implementation details → `developer`
```

- [ ] **Step 3: Bump version (patch — text clarification + dead-ref fix)**

Change line 3 from `version: "1.0.2"` to `version: "1.0.3"`.

- [ ] **Step 4: Verify no other file references the non-existent `architect` role**

Run: `grep -rln "\`architect\`" agents/1-generic/ 2>/dev/null || echo "none found"`
Expected: `none found`

- [ ] **Step 5: Commit**

```bash
git add agents/1-generic/concept-reviewer.md
git commit -m "fix: remove dead architect cross-ref, trim concept-reviewer description"
```

## Task 11: `developer.md` — cleanup #1, #5, #6

**Files:**
- Modify: `agents/1-generic/developer.md`

- [ ] **Step 1: Trim frontmatter description/hint (cleanup #1)**

Change lines 4-5 from:
```yaml
description: "Implements features and bugfixes in Modern Mode with XML structure and TypeScript contracts."
hint: "Feature implementation and bugfixes by REQ-ID"
```
to:
```yaml
description: "Use when a REQ-ID or clearly scoped task needs direct feature/bugfix implementation."
hint: "Use for feature/bugfix implementation by REQ-ID — Modern Mode, XML structure, TS contracts."
```

- [ ] **Step 2: Remove the dead `Agent` tool grant (cleanup #5)**

Change the `tools:` list (lines 7-16) from:
```yaml
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - TodoWrite
  - Agent
```
to:
```yaml
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - TodoWrite
```

Also remove the now-inconsistent bullet in `<tools>` (line 76):
```markdown
- **Agent** — delegate to other roles (only when explicitly allowed)
```
(delete this line entirely — `<constraints>` line 115 already says "Reference `tester`, `documenter`, `requirements`, `validator` in text only — never delegate via tool call", so the tool grant and this bullet were both dead/contradictory).

- [ ] **Step 3: Replace the self-verification paragraph with the canonical version (cleanup #6, source of truth)**

Leave `developer.md` step 6 in `<workflow>` (currently line 34) as the canonical, unabridged version — no change to its text. (Task 12 makes `senior-developer.md` reference this instead of duplicating it.)

- [ ] **Step 4: Bump version (patch — dead grant removed, text trimmed, no behavior change)**

Change line 3 from `version: "3.1.0"` to `version: "3.1.1"`.

- [ ] **Step 5: Verify**

Run: `python scripts/consistency-check.py --file agents/1-generic/developer.md`
Expected: no new ERROR-severity finding.

- [ ] **Step 6: Commit**

```bash
git add agents/1-generic/developer.md
git commit -m "fix: drop dead Agent tool grant, trim developer description/hint"
```

## Task 12: `senior-developer.md` — cross-reference the self-verification paragraph (cleanup #6)

**Files:**
- Modify: `agents/1-generic/senior-developer.md:38`

**Interfaces:**
- Consumes: `developer.md` workflow step 6 (Task 11) as the canonical self-verification text — this task only changes the cross-reference, not `developer.md` again.

- [ ] **Step 1: Replace the near-duplicate paragraph with a cross-reference**

Change line 38 from:
```markdown
4. SELF-VERIFICATION: actually run the changed components; observe cross-cutting effects on neighbouring subsystems and caller paths; do not report done before observing the expected behavior
```
to:
```markdown
4. SELF-VERIFICATION: same discipline as `developer` (see developer.md workflow step 6 — actually run/call the changed code, do not rely on green tests alone) — additionally observe cross-cutting effects on neighbouring subsystems and caller paths; do not report done before observing the expected behavior
```

- [ ] **Step 2: Bump version (patch — text dedup, no behavior change)**

Change line 3 from `version: "1.2.0"` to `version: "1.2.1"`.

- [ ] **Step 3: Verify**

Run: `python scripts/consistency-check.py --file agents/1-generic/senior-developer.md`
Expected: no new ERROR-severity finding.

- [ ] **Step 4: Commit**

```bash
git add agents/1-generic/senior-developer.md
git commit -m "docs: cross-reference developer self-verification instead of duplicating it"
```

## Task 13: `effort-estimator.md` — add missing `TodoWrite` tool grant (cleanup #4)

**Files:**
- Modify: `agents/1-generic/effort-estimator.md:7-10`

- [ ] **Step 1: Add the missing tool**

Change:
```yaml
tools:
  - Read
  - Glob
  - Grep
```
to:
```yaml
tools:
  - Read
  - Glob
  - Grep
  - TodoWrite
```

(The `<tools>` prose at line 68 already documents `TodoWrite — for decomposition >3 sub-tasks` — this was referenced in the body without being granted in frontmatter.)

- [ ] **Step 2: Bump version (patch — structural fix, no new behavior)**

Change line 3 from `version: "1.0.2"` to `version: "1.0.3"`.

- [ ] **Step 3: Verify**

Run: `python scripts/consistency-check.py --file agents/1-generic/effort-estimator.md`
Expected: no new ERROR-severity finding.

- [ ] **Step 4: Commit**

```bash
git add agents/1-generic/effort-estimator.md
git commit -m "fix: grant TodoWrite tool referenced in effort-estimator workflow"
```

## Task 14: Full regeneration and validation of this repo's own dogfooded output

**Files:**
- Regenerates (generated output, not hand-edited): `.claude/agents/planner.md` (new), `.claude/agents/{feature,ideation,concept-reviewer,developer,senior-developer,effort-estimator}.md`, `.claude/rules/use-orchestrator.md`, and Opencode/Gemini equivalents for the same roles.

**Interfaces:** none — this task only runs existing tooling (`scripts/sync.py`, `scripts/consistency-check.py`, `pytest`) and inspects the result.

- [ ] **Step 1: Run a real (non-validate) sync to regenerate derived files**

Run: `python scripts/sync.py`
Expected: exit code 0; log shows `CREATE agents/1-generic/planner.md → .claude/agents/planner.md` (and Opencode/Gemini equivalents) plus `UPDATE .claude/rules/use-orchestrator.md`.

- [ ] **Step 2: Confirm the generated intent table contains `planner` with the correct keywords**

Run: `grep -n "planner" .claude/rules/use-orchestrator.md`
Expected: one row containing `Plan, Planung, Schritte, Umsetzungsplan, "wie setzen wir das um"` and `recommended`.

- [ ] **Step 3: Run the full consistency-check suite**

Run: `python scripts/consistency-check.py`
Expected: exit code 0 (no ERROR-severity findings). The `orchestrator-strict.no-hook-support` findings from Task 5/6 are WARNING-severity and do not affect this exit code — confirm they still appear via `python scripts/sync.py --validate`.

- [ ] **Step 4: Run `sync.py --validate` end-to-end**

Run: `python scripts/sync.py --validate`
Expected: exit code 0; output includes the two `orchestrator-strict.no-hook-support` warnings for `Opencode` and `Gemini` from Task 6, Step 2.

- [ ] **Step 5: Run the full pytest suite**

Run: `python -m pytest tests/ -q`
Expected: all tests pass (including the four new tests from Task 5); no pre-existing test starts failing because of the role-defaults/template changes above.

- [ ] **Step 6: Review the generated-file diff before staging**

Run: `git status --short .claude .opencode .gemini 2>/dev/null`
Expected: only the files listed at the top of this task changed; no unrelated generated file touched (a broader diff would indicate an unrelated regression — stop and investigate before committing).

- [ ] **Step 7: Commit the regenerated output**

```bash
git add .claude .opencode .gemini
git commit -m "chore: regenerate provider output for planner role and cluster cleanup"
```

## Task 15: Final review pass on the spec's manual-only acceptance criteria

**Files:** none modified — read-only verification.

- [ ] **Step 1: Re-read the four semantic cleanup diffs against the spec's acceptance criteria**

Open `agents/1-generic/ideation.md`, `agents/1-generic/concept-reviewer.md`, `agents/1-generic/feature.md`, `agents/1-generic/developer.md` and confirm each `description`/`hint` now reads as a pure "Use when..." trigger, matching `docs/superpowers/specs/2026-08-02-agent-orchestration-refinement-design.md` → Cleanup-Abschnitt Punkt 1. No automated check covers this (documented gap in the spec's Testing section) — this is the manual verification step it calls for.

- [ ] **Step 2: Confirm all spec Akzeptanzkriterien checkboxes are satisfiable**

Walk the "Akzeptanzkriterien" section of the spec top to bottom; for each checkbox, name the task in this plan that satisfies it. If any checkbox has no corresponding task, stop and add one before proceeding — do not mark this step done with a gap.

- [ ] **Step 3: Report status**

No commit in this step (read-only). Summarize completion against the spec's P1-P4 priority table for the user.
