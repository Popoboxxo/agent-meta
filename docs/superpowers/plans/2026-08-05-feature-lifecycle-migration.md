# feature.md → feature-lifecycle Pipeline Migration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hardcoded `feature` agent (`agents/1-generic/feature.md`, an 8-step lifecycle choreographed via real `Agent`-tool delegation) with a declarative `feature-lifecycle` pipeline built on the engine primitives from the prior plan (`docs/superpowers/plans/2026-08-05-pipeline-engine-core.md`) — `dod_flag` conditionals and `mode: plan-driven` — and remove every reference to the deleted role across the codebase.

**Architecture:** `standard-feature` (`config/role-defaults.yaml`) is renamed to `feature-lifecycle` and extended with the stages from spec Entscheidung 2. `agents/1-generic/feature.md` is deleted. Every file that referenced the `feature` role by name is updated to reference the pipeline instead. This plan depends on the pipeline-engine-core plan being merged — `dod_flag`/`plan-driven` must already exist in `scripts/lib/pipelines.py`.

**Tech Stack:** Python 3, pytest, PyYAML, Markdown/YAML agent templates.

## Global Constraints

- The renamed pipeline is `feature-lifecycle` — no `standard-feature` name survives, no alias (per spec Entscheidung 2 interview clarification: they were already the same pipeline in substance).
- `dod_flag` condition keys are exactly `req-traceability`, `tests-required`, `codebase-overview` (verified against `config/dod-presets.yaml` and `scripts/lib/dod.py:52-54` — must match verbatim, hyphenated).
- `agents/1-generic/feature.md` is deleted, not deprecated/archived.
- Before this plan's Task 1, `scripts/lib/pipelines.py` must already render `dod_flag`-conditional stages that survive the sync-time skip as plain instruction text, not as an unresolved "Conditional execution — evaluated by agent" wrapper (memory: `pipeline-engine-core-plan2-blocker` — the prior plan's final review explicitly deferred this fix to this plan's start, not to be silently skipped).
- No REQ-ID tracking required for this branch's own commits (`REQ-Traceability: false` per this project's DoD preset, per `CLAUDE.md`).

---

## File Structure

- **Modify:** `scripts/lib/pipelines.py` — Task 1 (dod_flag render fix), Task 2 (drop `feature` from `orchestrator_roles`).
- **Modify:** `config/role-defaults.yaml` — Task 3 (rename `standard-feature` → `feature-lifecycle`, extend stages, delete `roles.feature`).
- **Delete:** `agents/1-generic/feature.md` — Task 4.
- **Modify:** `agents/1-generic/_wf-orchestrator-reference.md`, `rules/1-generic/use-orchestrator.md`, `agents/1-generic/orchestrator.md`, `agents/1-generic/planner.md` — Task 4 (replace `feature`-agent references with the pipeline).
- **Modify:** `scripts/lib/viz.py`, `tests/test_opencode_agents.py`, `docs/architecture/03-agent-roles.md` — Task 5 (drop the `feature` node/role from generated-graph hardcodes, tests, and manual docs).
- **Modify:** `scripts/lib/delegation_table.py` — Task 6 (pipelines with `signal_keywords` become visible as rows in the generated intent-routing table, not just roles).
- **Create:** none — all changes are to existing files.

---

### Task 1: Render `dod_flag`-surviving conditional stages as plain instructions

**Files:**
- Modify: `scripts/lib/pipelines.py` (`_generate_pipeline_block()`'s `conditional` branch)
- Test: `tests/test_pipelines.py`

**Interfaces:**
- Consumes: `active_dod` parameter (already threaded through `_generate_pipeline_block()` since the pipeline-engine-core plan).
- Produces: nothing new consumed by later tasks — a pure rendering-correctness fix that Task 3's `feature-lifecycle` pipeline needs to read correctly once it exists.

**Context:** A stage with `condition: {dod_flag: X}` is fully omitted from the loop (via `continue`, added in the prior plan) when the flag is inactive. That means any such stage that *reaches* the `elif mode == "conditional":` render branch is, by construction, active — the condition has already been resolved at sync time. The current code still renders it through the generic conditional wrapper ("Conditional execution: — Condition evaluated by {agent}: {task}"), which incorrectly tells the orchestrator to re-evaluate something that's already decided.

- [ ] **Step 1: Write the failing test**

```python
def test_generate_pipeline_block_dod_flag_survivor_renders_as_plain_instruction():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {
                "id": "req",
                "agent": "requirements",
                "task": "REQ-ID vergeben",
                "mode": "conditional",
                "condition": {"dod_flag": "req-traceability"},
            },
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode", active_dod={"req-traceability": True})
    assert "REQ-ID vergeben" in block
    # Must NOT render as an unresolved conditional wrapper — the flag is
    # already decided at sync time, nothing left to evaluate at runtime.
    assert "Conditional execution" not in block
    assert "Condition evaluated by" not in block
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipelines.py::test_generate_pipeline_block_dod_flag_survivor_renders_as_plain_instruction -v`
Expected: FAIL — the stage currently renders through the generic conditional wrapper, so `"Conditional execution" not in block` fails.

- [ ] **Step 3: Special-case `dod_flag` before the generic conditional branch**

In `_generate_pipeline_block()`, the `elif mode == "conditional":` branch currently starts like this:

```python
        elif mode == "conditional":
            lines.append("")
            lines.append(f"**{stage_id}** — {fmt['conditional_start']}")
            lines.append(
                fmt["conditional_item"].format(agent=agent, task=task)
            )
            cond = stage.get("condition", {})
            if cond.get("type") == "agent_decision":
                ...
            elif "payload_flag" in cond:
                ...
            lines.append("")
```

Change it to check `dod_flag` first and render as a plain sequential-style line instead of entering the conditional-wrapper path at all:

```python
        elif mode == "conditional":
            cond = stage.get("condition", {})
            if "dod_flag" in cond:
                # Already resolved at sync time (inactive stages were skipped
                # via `continue` above) — render as a plain instruction, not
                # as an unresolved runtime conditional.
                seq_idx += 1
                line = fmt["sequential_item"].format(
                    index=seq_idx, agent=agent, task=task
                )
                lines.append(line + " → warten bis abgeschlossen")
                continue
            lines.append("")
            lines.append(f"**{stage_id}** — {fmt['conditional_start']}")
            lines.append(
                fmt["conditional_item"].format(agent=agent, task=task)
            )
            if cond.get("type") == "agent_decision":
                lines.append(f"  Decision agent: {cond.get('agent', agent)}")
                lines.append("  If 'continue': Orchestrator spawns new cell at level n+1 with sanitized context")
                lines.append("  If 'leaf': Component is final — handover to implementation discipline")
            elif "payload_flag" in cond:
                lines.append(
                    f"  Laufzeit-Skip: Orchestrator überspringt diese Stage, wenn "
                    f"payload.{cond['payload_flag']} fehlt oder false ist."
                )
            lines.append("")
```

Note the `cond = stage.get("condition", {})` line moves to the top of the branch (it was previously computed after the wrapper lines were already appended) — this is required so the `dod_flag` check can run before any wrapper text is emitted. The `continue` at the end of the `dod_flag` sub-branch skips straight to the next stage in the `for stage in stages:` loop, exactly like the `sequential` branch's fallthrough.

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS, all tests including the new one, no regressions on the two pre-existing `agent_decision`/`payload_flag` conditional tests.

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/pipelines.py tests/test_pipelines.py
git commit -m "fix: render surviving dod_flag conditionals as plain instructions"
```

---

### Task 2: Drop `feature` from the pipeline engine's circular-orchestration guard

**Files:**
- Modify: `scripts/lib/pipelines.py` (`validate_pipelines()`)
- Test: `tests/test_pipelines.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing new — this is a cleanup task that must land before Task 4 deletes the `feature` role (otherwise `validate_pipelines()` still special-cases a role that no longer exists, dead but harmless code left behind).

- [ ] **Step 1: Write the failing test**

```python
def test_validate_pipelines_only_orchestrator_is_circular_guard():
    from scripts.lib.pipelines import validate_pipelines

    # "feature" must no longer trigger the circular-orchestration guard —
    # it is being retired as a role in this plan.
    pipelines = {
        "p1": {"stages": [{"id": "x", "agent": "feature", "task": "t", "mode": "sequential"}]}
    }
    errors = validate_pipelines(pipelines, available_roles=["feature"])
    assert not any("circular delegation" in e for e in errors)

    # "orchestrator" must still trigger it.
    pipelines2 = {
        "p1": {"stages": [{"id": "x", "agent": "orchestrator", "task": "t", "mode": "sequential"}]}
    }
    errors2 = validate_pipelines(pipelines2, available_roles=["orchestrator"])
    assert any("circular delegation" in e for e in errors2)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipelines.py::test_validate_pipelines_only_orchestrator_is_circular_guard -v`
Expected: FAIL — the first assertion fails because `"feature"` is still in `orchestrator_roles`.

- [ ] **Step 3: Reduce `orchestrator_roles`**

In `validate_pipelines()`, change:

```python
    orchestrator_roles = {"orchestrator", "feature"}
```

to:

```python
    orchestrator_roles = {"orchestrator"}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/pipelines.py tests/test_pipelines.py
git commit -m "fix: remove feature from pipeline circular-orchestration guard"
```

---

### Task 3: Rename `standard-feature` to `feature-lifecycle` and extend its stages

**Files:**
- Modify: `config/role-defaults.yaml` (rename `quality_pipelines.standard-feature` → `quality_pipelines.feature-lifecycle`, extend stages; delete `roles.feature`)
- Test: `tests/test_pipelines.py` (validate the new pipeline definition parses and validates cleanly)

**Interfaces:**
- Consumes: `mode: conditional` + `condition: {dod_flag: ...}` (Task 1), `mode: plan-driven` (already in the engine from the prior plan).
- Produces: the `feature-lifecycle` pipeline definition that Tasks 4-6 reference by name.

**Context:** `standard-feature` (`config/role-defaults.yaml:1386-1414`) is today: `description: Full feature lifecycle with TDD, review, and PR`, `signal_keywords: [Feature implementieren, Feature bauen, neues Feature, Funktion bauen]`, 4 stages (branch/implement/review-loop/commit). It is renamed and extended to match what `feature.md` does today via its `{{#if DOD_...}}` blocks, per spec Entscheidung 2 — union the old and new `signal_keywords`.

- [ ] **Step 1: Write the failing test**

```python
def test_feature_lifecycle_pipeline_definition_is_valid():
    import yaml
    from scripts.lib.pipelines import load_quality_pipelines, validate_pipelines

    agent_meta_root = "."  # repo root; test runs from repo root under pytest
    pipelines = load_quality_pipelines(agent_meta_root)
    assert "standard-feature" not in pipelines
    assert "feature-lifecycle" in pipelines

    fl = pipelines["feature-lifecycle"]
    expected_keywords = {
        "Feature implementieren", "Feature bauen", "neues Feature", "Funktion bauen",
        "Feature Lifecycle", "komplexes Feature", "Feature Pipeline",
    }
    assert expected_keywords.issubset(set(fl["signal_keywords"]))

    stage_ids = [s["id"] for s in fl["stages"]]
    assert stage_ids == ["branch", "requirement", "tests", "implement", "verify", "validate-and-document", "commit"]

    implement_stage = next(s for s in fl["stages"] if s["id"] == "implement")
    assert implement_stage["mode"] == "plan-driven"
    assert implement_stage["plan-driven"]["fallback_agent"] == "developer"

    requirement_stage = next(s for s in fl["stages"] if s["id"] == "requirement")
    assert requirement_stage["condition"] == {"dod_flag": "req-traceability"}

    # role-defaults.yaml roles: `feature` must be gone.
    with open("config/role-defaults.yaml", encoding="utf-8") as f:
        roles_cfg = yaml.safe_load(f)
    assert "feature" not in roles_cfg.get("roles", {})

    # Full validation must be clean against the roles this pipeline references.
    all_roles = set(roles_cfg.get("roles", {}).keys())
    errors = validate_pipelines({"feature-lifecycle": fl}, list(all_roles))
    assert errors == [], f"Unexpected validation errors: {errors}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipelines.py::test_feature_lifecycle_pipeline_definition_is_valid -v`
Expected: FAIL — `standard-feature` is still present, `feature-lifecycle` doesn't exist yet.

- [ ] **Step 3: Replace `standard-feature` with `feature-lifecycle` in `config/role-defaults.yaml`**

Find the existing block (currently at `config/role-defaults.yaml:1386-1414`):

```yaml
  standard-feature:
    description: Full feature lifecycle with TDD, review, and PR
    signal_keywords:
    - Feature implementieren
    - Feature bauen
    - neues Feature
    - Funktion bauen
    stages:
    - id: branch
      agent: git
      task: Feature-Branch anlegen
      mode: sequential
    - id: implement
      agent: developer
      task: Feature implementieren
      mode: sequential
    - id: review
      agent: developer
      task: Code schreiben und Review-Feedback einarbeiten
      mode: loop
      loop:
        generator: developer
        critic: code-reviewer
        max_iterations: 3
    - id: commit
      agent: git
      task: Commit + Push + PR
      mode: sequential
    on_error: escalate_to_orchestrator
```

Replace it entirely with:

```yaml
  feature-lifecycle:
    description: Vollständiger Feature-Lifecycle mit optionalem Plan-Input, REQ, TDD, Review, PR
    signal_keywords:
    - Feature implementieren
    - Feature bauen
    - neues Feature
    - Funktion bauen
    - Feature Lifecycle
    - komplexes Feature
    - Feature Pipeline
    accepts_plan_ref: true
    stages:
    - id: branch
      agent: git
      task: Feature-Branch anlegen
      mode: sequential
    - id: requirement
      agent: requirements
      task: REQ-ID vergeben
      mode: conditional
      condition:
        dod_flag: req-traceability
    - id: tests
      agent: tester
      task: TDD Red Phase — Tests mit REQ-ID im Namen
      mode: conditional
      condition:
        dod_flag: tests-required
    - id: implement
      agent: developer
      task: Implementierung
      mode: plan-driven
      plan-driven:
        fallback_agent: developer
        allowed_agents:
        - junior-developer
        - developer
        - senior-developer
    - id: verify
      agent: tester
      task: Tests grün, keine Regression
      mode: conditional
      condition:
        dod_flag: tests-required
    - id: validate-and-document
      mode: parallel_group
      parallel_group:
      - agent: validator
        task: DoD-Check
      - agent: documenter
        task: CODEBASE_OVERVIEW aktualisieren
    - id: commit
      agent: git
      task: 'Commit: feat([REQ-ID]): ... + PR'
      mode: sequential
    on_error: escalate_to_orchestrator
```

Note: the `validate-and-document` stage's outer `condition: {dod_flag: codebase-overview}` from the spec draft is dropped here — `mode: parallel_group` does not support a stage-level `condition` field in the current engine (only `conditional`-mode stages do; `validate_pipelines()`/`_generate_pipeline_block()` never read `condition` on a `parallel_group` stage). Keep `validator`'s DoD-check unconditional (it should always run) and drop the `documenter` sub-stage's conditionality — CODEBASE_OVERVIEW-off projects simply get a `documenter` step whose own prompt already no-ops when the DoD flag is off (this matches the DoD-flag-in-agent-prompt pattern used everywhere else in this codebase, e.g. `{{DOD_...}}` blocks inside `documenter.md` itself, not in the pipeline stage). This is a deliberate, minimal deviation from the spec's YAML sketch — the spec sketch pre-dates the actual engine capabilities check done in this plan.

- [ ] **Step 4: Delete the `feature` role entry from `config/role-defaults.yaml`**

Remove this block entirely (currently at `config/role-defaults.yaml:195-210`):

```yaml
  feature:
    model: balanced
    memory: ''
    workflow_tier: recommended
    description: 'Feature-Lifecycle-Subagent: Branch → REQ → TDD → Dev → Validate
      → PR. Wird vom Orchestrator gestartet, nicht direkt vom User.'
    routing:
      intent_keywords:
      - Feature Lifecycle
      - komplexes Feature
      - Feature Pipeline
      parallel: true
      orchestrator_only: true
    handoff:
      input_contracts:
      - task-spec-v1
```

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS (the new `test_feature_lifecycle_pipeline_definition_is_valid`, plus no regressions in the rest of the suite — run `pytest -q --ignore=external` too, since `role-defaults.yaml` is read by many other tests).

- [ ] **Step 6: Commit**

```bash
git add config/role-defaults.yaml tests/test_pipelines.py
git commit -m "feat: rename standard-feature to feature-lifecycle, drop feature role"
```

---

### Task 4: Delete `feature.md` and repoint every direct reference to the pipeline

**Files:**
- Delete: `agents/1-generic/feature.md`
- Modify: `agents/1-generic/_wf-orchestrator-reference.md`
- Modify: `rules/1-generic/use-orchestrator.md`
- Modify: `agents/1-generic/orchestrator.md`
- Modify: `agents/1-generic/planner.md`

**Interfaces:**
- Consumes: `feature-lifecycle` pipeline name from Task 3.
- Produces: nothing new consumed by later tasks.

- [ ] **Step 1: Delete the agent template**

```bash
git rm agents/1-generic/feature.md
```

- [ ] **Step 2: Update `agents/1-generic/_wf-orchestrator-reference.md`**

Current content (lines 15-16):

```
| Single Feature | `feature` oder Pipeline: git→req→test→dev→test→review→doc→git |
| Plan vorhanden | planner→feature(plan_ref=<path>) |
```

Replace with:

```
| Single Feature | Pipeline `feature-lifecycle`: git→req→test→dev→test→review→doc→git |
| Plan vorhanden | planner→feature-lifecycle(plan_ref=<path>) |
```

Verify with: `grep -n "feature" agents/1-generic/_wf-orchestrator-reference.md` — every remaining hit must be `feature-lifecycle`, none may be the bare word `feature` referring to an agent.

- [ ] **Step 3: Update `rules/1-generic/use-orchestrator.md`**

Current content (line 23):

```
Plan vorhanden (`plan-*.md` oder Knowledge-Wiki Plan-Seite) -> `feature` mit `payload.plan_ref`, statt neuen Lifecycle blind zu starten.
```

Replace with:

```
Plan vorhanden (`plan-*.md` oder Knowledge-Wiki Plan-Seite) -> Pipeline `feature-lifecycle` mit `payload.plan_ref`, statt neuen Lifecycle blind zu starten.
```

This is the SOURCE file for the generated `.claude/rules/use-orchestrator.md` (per `.claude/rules/sync-interface.md` in this repo — generated copies are never edited directly). Do not touch `.claude/rules/use-orchestrator.md` by hand; it gets regenerated in Task 7's `sync.py` run.

- [ ] **Step 4: Update `agents/1-generic/orchestrator.md`**

Current content (lines 66, 68, 183):

```
| Complex feature | → `feature` or pipeline |
```
```
Plan available (existing `plan-*.md` or Knowledge-Wiki Plan page, or `planner` handoff) → pass its path to `feature` as `payload.plan_ref` instead of starting a fresh lifecycle blind.
```
```
{{#if DOD_REQ_TRACEABILITY}}| No feature without REQ-ID{{/if}}
```

Replace the first two with:

```
| Complex feature | → `feature-lifecycle` pipeline |
```
```
Plan available (existing `plan-*.md` or Knowledge-Wiki Plan page, or `planner` handoff) → pass its path to the `feature-lifecycle` pipeline as `payload.plan_ref` instead of starting a fresh lifecycle blind.
```

Leave the third line (`{{#if DOD_REQ_TRACEABILITY}}...{{/if}}`) unchanged — "feature" there means "a feature" (the English noun), not the deleted agent role; verify this by reading the surrounding paragraph before editing, do not pattern-match blindly on the string `feature`.

- [ ] **Step 5: Update `agents/1-generic/planner.md`**

Search for `feature` in this file (`grep -n "feature" agents/1-generic/planner.md`) and update the `<output_contract>`/persona wording that describes `plan_ref` as being handed to "the `feature` agent" — change to "the `feature-lifecycle` pipeline". Read the surrounding sentence(s) before editing (found via the grep) so the replacement reads naturally in context — do not do a blind find/replace, since the exact wording depends on nearby sentence structure that may have shifted since this plan was written.

- [ ] **Step 6: Verify no other `1-generic`/`0-external` template references the deleted role**

Run: `grep -rln "\`feature\`" agents/1-generic/ agents/0-external/ rules/1-generic/ 2>/dev/null`
Expected: no output (all direct backtick-quoted `` `feature` `` references in generic templates and rule sources are gone). If any remain, apply the same "read context, replace with `feature-lifecycle` pipeline reference" pattern as above.

- [ ] **Step 7: Commit**

```bash
git add -A agents/1-generic/ rules/1-generic/
git commit -m "feat: delete feature.md, repoint references to feature-lifecycle pipeline"
```

---

### Task 5: Remove `feature` from the generated agent-graph, tests, and manual architecture docs

**Files:**
- Modify: `scripts/lib/viz.py`
- Modify: `tests/test_opencode_agents.py`
- Modify: `docs/architecture/03-agent-roles.md`

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing new — this is the last cross-reference cleanup task before the regression pass (Task 7).

- [ ] **Step 1: Remove `feature` from `scripts/lib/viz.py`'s hardcoded delegation map**

Current content (`scripts/lib/viz.py:22-34`):

```python
_DELEGATION_MAP: dict[str, list[str]] = {
    "orchestrator": [
        "developer", "feature", "git", "documenter", "ideation",
        "release", "security-auditor", "docker", "log-analyzer",
        "feedback", "agent-meta-manager", "agent-meta-scout", "meta-feedback",
        "requirements", "validator", "tester",
    ],
    "developer": ["tester", "git"],
    "feature": ["requirements", "validator", "developer", "tester", "git"],
    "release": ["git", "documenter"],
    "log-analyzer": ["feedback", "developer", "security-auditor"],
    "agent-meta-manager": ["agent-meta-scout", "developer", "git"],
}
```

Replace with:

```python
_DELEGATION_MAP: dict[str, list[str]] = {
    "orchestrator": [
        "developer", "git", "documenter", "ideation",
        "release", "security-auditor", "docker", "log-analyzer",
        "feedback", "agent-meta-manager", "agent-meta-scout", "meta-feedback",
        "requirements", "validator", "tester",
    ],
    "developer": ["tester", "git"],
    "release": ["git", "documenter"],
    "log-analyzer": ["feedback", "developer", "security-auditor"],
    "agent-meta-manager": ["agent-meta-scout", "developer", "git"],
}
```

(Removed the `"feature"` entry from `orchestrator`'s list, and dropped the standalone `"feature": [...]` entry entirely.)

- [ ] **Step 2: Update `tests/test_opencode_agents.py`'s `DELEGATING_ROLES`**

Current content (`tests/test_opencode_agents.py:54-58`):

```python
DELEGATING_ROLES = {
    "orchestrator",
    "feature",
    "agent-meta-manager",
}
```

Replace with:

```python
DELEGATING_ROLES = {
    "orchestrator",
    "agent-meta-manager",
}
```

- [ ] **Step 3: Update `docs/architecture/03-agent-roles.md`**

This is manual documentation (not build-generated), requiring 4 separate edits:

1. Mermaid diagram (lines 6-36): remove the `FEA[feature]` node declaration and all 6 `FEA --> X` edges (`FEA --> GIT`, `FEA --> REQ`, `FEA --> TST`, `FEA --> DEV`, `FEA --> VAL`, `FEA --> DOC`).
2. The `[Open in Mermaid Live Editor]` link (line 3) contains a base64-encoded copy of the old diagram — after editing the diagram source, either regenerate this link (encode the new diagram text as base64 and rebuild the URL) or remove the link entirely if regeneration tooling isn't available in this task's scope. Prefer removing the link over leaving a stale one that renders the deleted `feature` node.
3. Rollen-Übersicht table (line 43): remove the `| \`feature\` | Vollständiger Feature-Lifecycle via Sub-Agent-Delegation | "Ich will ein neues Feature bauen" | *(voll)* |` row entirely.
4. `## feature vs. orchestrator` section (lines 72-82): remove the entire section, including its comparison table. `feature` is no longer a role to compare against `orchestrator` — the pipeline mechanism (already documented elsewhere in this repo's pipeline docs) replaces the need for this comparison.

- [ ] **Step 4: Verify**

Run: `grep -n "feature" scripts/lib/viz.py tests/test_opencode_agents.py docs/architecture/03-agent-roles.md`
Expected: no hits referring to the deleted agent role. (The word "feature" as a common noun, e.g. inside unrelated prose, is fine — read each hit before deciding it's a problem.)

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/viz.py tests/test_opencode_agents.py docs/architecture/03-agent-roles.md
git commit -m "chore: remove feature role from agent graph, tests, and docs"
```

---

### Task 6: Make pipeline `signal_keywords` visible in the generated intent-routing table

**Files:**
- Modify: `scripts/lib/delegation_table.py`
- Test: create `tests/test_delegation_table.py` (no test file exists for this module today)

**Interfaces:**
- Consumes: `quality_pipelines` dict shape from `scripts/lib/pipelines.py::load_quality_pipelines()`/`apply_overrides()` (already used elsewhere in the sync pipeline, e.g. `scripts/lib/config.py:729-731`).
- Produces: `get_intent_routing_table()`'s extended signature `(agent_meta_root, config, variables, pipelines=None)` — the new optional 4th parameter. `pipelines=None` preserves the exact current behavior (role rows only) for any caller not yet updated, which matters because this task does not update `get_intent_routing_table()`'s call site — that's out of scope here (the call site lives in `scripts/lib/config.py`, already wired to pass `effective` pipelines by the time this task runs, see Step 4).

**Context:** Spec Entscheidung 2's migration table calls this out: "Pipeline-Signal-Keywords brauchen eine eigene Sichtbarkeit in der generierten Doku (heute nur Rollen, keine Pipelines, in der Intent-Tabelle)." `feature-lifecycle`'s `signal_keywords` (Task 3) is the first pipeline whose absence from this table is now user-visible (it used to appear via the `feature` role's `routing.intent_keywords`, which Task 3 deleted along with the role).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_delegation_table.py
from scripts.lib.delegation_table import get_intent_routing_table


def test_intent_routing_table_includes_pipeline_rows(tmp_path):
    from pathlib import Path

    agent_meta_root = Path(".")
    config = {}
    variables = {
        "SE_ENABLED": "false",
        "VALIDATOR_ENABLED": "true",
        "KNOWLEDGE_ENGINE_ENABLED": "false",
        "DEVELOPER_TIERS_ENABLED": "false",
    }
    pipelines = {
        "feature-lifecycle": {
            "signal_keywords": ["Feature implementieren", "Feature bauen", "neues Feature"],
            "stages": [],
        },
        "quick-fix": {
            "signal_keywords": ["Bug fixen"],
            "stages": [],
        },
    }
    table = get_intent_routing_table(agent_meta_root, config, variables, pipelines=pipelines)
    assert "Feature implementieren, Feature bauen, neues Feature" in table
    assert "→ Pipeline: `feature-lifecycle`" in table
    assert "→ Pipeline: `quick-fix`" in table


def test_intent_routing_table_without_pipelines_arg_is_unchanged():
    from pathlib import Path

    agent_meta_root = Path(".")
    config = {}
    variables = {
        "SE_ENABLED": "false",
        "VALIDATOR_ENABLED": "true",
        "KNOWLEDGE_ENGINE_ENABLED": "false",
        "DEVELOPER_TIERS_ENABLED": "false",
    }
    # No pipelines= argument at all — must not raise, must not include any
    # "→ Pipeline:" rows (backward compatible with any caller not yet updated).
    table = get_intent_routing_table(agent_meta_root, config, variables)
    assert "→ Pipeline:" not in table
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_delegation_table.py -v`
Expected: FAIL — `get_intent_routing_table()` doesn't accept a `pipelines` parameter yet.

- [ ] **Step 3: Extend `get_intent_routing_table()`**

In `scripts/lib/delegation_table.py`, change the signature and add pipeline rows after the existing role rows:

```python
def get_intent_routing_table(agent_meta_root: Path, config: dict, variables: dict, pipelines: dict | None = None) -> str:
    """Generate the INTENT_ROUTING_TABLE from active roles and, optionally, pipelines."""
    roles_cfg = load_roles_config(agent_meta_root)
    roles = roles_cfg.get("roles", {})
    active_agents_data = get_active_agents_data(agent_meta_root, config, variables)
    active_agent_names = {agent["name"] for agent in active_agents_data}

    table_lines = [
        "> Parallel ist rein informativ — kein Runtime-Enforcement, nur CI-Konsistenzcheck bei required/recommended-Tier-Abdeckung.",
        "",
        "| Intent / Keywords | Agent | Tier | Parallel |",
        "|-------------------|-------|------|----------|"
    ]

    has_entries = False
    for role_name in sorted(roles.keys()):
        if role_name not in active_agent_names:
            continue

        role_info = roles[role_name]
        routing = role_info.get("routing", {})
        intent_keywords = routing.get("intent_keywords", [])

        if not intent_keywords:
            continue

        tier = role_info.get("workflow_tier", "optional")
        parallel = "yes" if routing.get("parallel", False) else "no"

        keywords_str = ", ".join(intent_keywords)
        table_lines.append(f"| {keywords_str} | `{role_name}` | {tier} | {parallel} |")
        has_entries = True

    for pipeline_name in sorted((pipelines or {}).keys()):
        pipeline_info = pipelines[pipeline_name]
        signal_keywords = pipeline_info.get("signal_keywords", [])
        if not signal_keywords:
            continue
        keywords_str = ", ".join(signal_keywords)
        table_lines.append(f"| {keywords_str} | → Pipeline: `{pipeline_name}` | pipeline | no |")
        has_entries = True

    if not has_entries:
        return ""

    return "\n".join(table_lines) + "\n"
```

- [ ] **Step 4: Wire the new parameter at the call site**

Find where `get_intent_routing_table()` is currently called (`grep -rn "get_intent_routing_table" scripts/`). Pass the same `effective` pipelines dict that `scripts/lib/config.py` already computes for `build_pipeline_variables()` (see `scripts/lib/config.py:729-731`, variable name `effective`) as the new `pipelines=` argument. If the call site is in a different function scope than where `effective` is computed, thread it through the same way `active_roles`/`config` already are threaded to that call — read the surrounding function to match the existing parameter-passing style rather than introducing a new pattern.

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_delegation_table.py tests/test_pipelines.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/delegation_table.py tests/test_delegation_table.py
git commit -m "feat: show pipeline signal_keywords in generated intent routing table"
```

---

### Task 7: Full regression pass — sync, validate, verify zero dangling references

**Files:**
- No file modifications expected (verification-only task); fix forward if verification finds a gap.

**Interfaces:**
- Consumes: all prior tasks' output.
- Produces: nothing — this is the plan's closing gate.

- [ ] **Step 1: Run the full test suite**

Run: `pytest -q --ignore=external`
Expected: same pass/skip/known-failure counts as the pipeline-engine-core plan's baseline (275 passed, 3 skipped, 1 pre-existing unrelated failure in `test_admin_server.py`), plus the new tests from Tasks 1, 2, 3, 6 in this plan. No new failures.

- [ ] **Step 2: Run `sync.py --validate`**

Run: `python scripts/sync.py --validate`
Expected: PASS, exit 0. This is the first real test of the `feature-lifecycle` pipeline and `dod_flag`/`plan-driven` stage modes against a live `role-defaults.yaml` — unlike the pipeline-engine-core plan, this one DOES change generated output for every project using the default `standard-feature` pipeline (now `feature-lifecycle`). A clean `--validate` run confirms the new pipeline definition round-trips through the full sync pipeline without validation errors.

- [ ] **Step 3: Search for dangling `feature`-agent references across the whole repo**

Run: `grep -rn "\`feature\`" --include="*.md" --include="*.yaml" --include="*.py" . --exclude-dir=.git --exclude-dir=external --exclude-dir=node_modules`

Expected: every hit is either (a) inside a generated file that will be regenerated by the next `sync.py` run without `--validate` (safe to ignore — these are build artifacts, not source), (b) a reference to `feature-lifecycle` (fine), or (c) an unrelated use of the English word "feature". Any hit that is a source file (under `agents/1-generic/`, `agents/2-platform/`, `agents/0-external/`, `rules/1-generic/`, `scripts/`, `config/`, `docs/architecture/`) still referring to the deleted role is a gap — fix it following the same "read context, repoint to `feature-lifecycle`" pattern used in Task 4/5, then re-run this step.

- [ ] **Step 4: Regenerate provider output**

Run: `python scripts/sync.py` (no `--dry-run`, no `--check` — an actual write, since this branch's `role-defaults.yaml` change is a real content change that downstream generated files must reflect).

Expected: exits 0, writes updated `.claude/agents/*.md` (removing the generated `feature.md` if one exists there, adding/updating pipeline-derived content in agents that reference `feature-lifecycle`), updates `.claude/rules/use-orchestrator.md` and other generated rule copies from their `rules/1-generic/` sources.

- [ ] **Step 5: Review the sync diff**

Run: `git status --short` and `git diff --stat` over the newly-generated files.

Expected: changes confined to generated output directories (`.claude/`, `.gemini/`, `.opencode/`, `.continue/`, `.mammouth/` as applicable per this repo's active providers) plus `docs/agent-graph.html`/`docs/agent-mindmap.md` (regenerated from `viz.py`, Task 5's edit should already be reflected). No unexpected changes to files this plan didn't intend to touch.

- [ ] **Step 6: Commit the regenerated output**

```bash
git add -A
git commit -m "chore: regenerate provider output after feature-lifecycle migration"
```

---

## Self-Review Notes

- **Spec coverage:** Entscheidung 2 (feature.md deletion + feature-lifecycle rename, full migration table): Tasks 3-5, 7. Entscheidung 2's audit-nachtrag on `delegation_table.py` pipeline visibility: Task 6. The `pipeline-engine-core-plan2-blocker` memory item (dod_flag-surviving-conditional rendering): Task 1 — addressed first, as the memory note required. `pipelines.py:92` `orchestrator_roles` migration-table line item: Task 2. Entscheidung 3 (`plan-driven`)'s actual use in a real pipeline: Task 3's `implement` stage. Entscheidungen 4-10 (concept-to-review pipeline, provider activation beyond feature-lifecycle, planner estimate stage, output-targets, admin-UI) are out of scope for this plan by design — separate plans.
- **Placeholder scan:** no TBD/"add error handling"/"similar to Task N" without code. Task 4 Steps 3/5/6 and Task 5 Step 3 use "read context before editing" language instead of literal diffs in a few spots — this is intentional, not a placeholder: those edits depend on exact surrounding prose in files this plan's author read at planning time but which could have shifted by execution time (multi-file prose migrations, unlike the code tasks, don't have a single canonical byte-for-byte target). Each such step names the exact grep to run and the exact verification condition, so it remains a concrete, checkable instruction, not an open-ended one.
- **Type consistency:** `_generate_pipeline_block()`'s signature is unchanged by this plan (Task 1 only reorders/branches within its existing body). `get_intent_routing_table()`'s new `pipelines: dict | None = None` parameter (Task 6) is additive and backward compatible — verified by the plan's own second test (`test_intent_routing_table_without_pipelines_arg_is_unchanged`). The `feature-lifecycle` pipeline's stage `id`s (Task 3) are referenced nowhere else in this plan by literal string except Task 7's verification grep, which matches by role-name pattern, not stage-id.

## Prerequisite

This plan requires `docs/superpowers/plans/2026-08-05-pipeline-engine-core.md` to be fully merged first (`dod_flag`, `plan-driven` stage modes must exist in `scripts/lib/pipelines.py`). Status at the time this plan was written: merged via PR #399 into `feat/planner-agent-and-cluster-cleanup`, which is itself merged into `main` as of PR #398 plus the follow-up PR #399 merge — verify with `git log --oneline -5 scripts/lib/pipelines.py` before starting Task 1 that `_max_depth`/`all_pipelines`/`dod_flag` already appear in the file.
