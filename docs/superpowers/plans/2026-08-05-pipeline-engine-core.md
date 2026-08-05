# Pipeline-Engine-Kern Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `scripts/lib/pipelines.py` with the stage-engine primitives the pipeline-driven-orchestration spec needs (`providers`, `dod_flag`/`payload_flag` conditionals, `run_pipeline` composition, `plan-driven`), so later plans (feature-lifecycle migration, output-targets, admin-UI) can build on a working engine.

**Architecture:** All changes live in `scripts/lib/pipelines.py` (the sync-time text generator for agent prompts — it never executes pipelines at runtime, it only renders instructions the orchestrator follows) plus one caller fix in `scripts/lib/agents.py`. No new files except the test file; no changes to `role-defaults.yaml` content (that's Plan 2).

**Tech Stack:** Python 3, pytest, PyYAML (already a soft dependency in `pipelines.py`).

## Global Constraints

- `max_depth` default is exactly `4` when a pipeline defines no `max_depth` field (spec Entscheidung 1).
- Known providers are exactly `("Claude", "Opencode", "Gemini", "Continue", "Mammouth")` (existing tuple in `build_pipeline_variables`, spec Entscheidung 5).
- `dod_flag` conditionals resolve at sync time (stage fully omitted from generated text when inactive); missing flag defaults to **active** (`True`), matching the existing `dod_resolved.get(flag, True)` convention in `scripts/lib/config.py:768`.
- `payload_flag` conditionals stay visible in generated text; the orchestrator skips them at runtime — no sync-time omission (spec Entscheidung 11).
- `plan-driven` and `run_pipeline` are pure text-generation concerns here — no runtime dispatch logic belongs in `pipelines.py` (that's the orchestrator's job per spec Entscheidung 3).
- Every new stage field must be handled generically (no per-pipeline-name special casing) — spec Entscheidung 9.

---

## File Structure

- **Modify:** `scripts/lib/pipelines.py` — all engine changes (provider filtering, conditional types, composition, plan-driven, validation).
- **Modify:** `scripts/lib/agents.py:1497-1501` — `inject_pipeline_blocks()` call currently passes `active_dod={}` (a no-op placeholder); switch to the real resolved DOD dict so `dod_flag` conditionals work in generated output.
- **Create:** `tests/test_pipelines.py` — no test file for `scripts/lib/pipelines.py` exists today; this plan creates the first one, scoped to the new behavior (not full pre-existing-function coverage).

---

### Task 1: `providers` field — pipeline-wide activation filter

**Files:**
- Modify: `scripts/lib/pipelines.py` (add `KNOWN_PROVIDERS` constant, `_pipeline_active_for_provider()`, wire into `build_pipeline_variables()` and `inject_pipeline_blocks()`, add validation in `validate_pipelines()`)
- Test: `tests/test_pipelines.py`

**Interfaces:**
- Produces: `KNOWN_PROVIDERS: tuple[str, ...]` — module-level constant, reused by Tasks 2-5.
- Produces: `_pipeline_active_for_provider(pipeline: dict, provider: str) -> bool` — used by later tasks' rendering code.

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_pipelines.py
from scripts.lib.pipelines import (
    KNOWN_PROVIDERS,
    _pipeline_active_for_provider,
    build_pipeline_variables,
    validate_pipelines,
)


def test_known_providers_constant():
    assert KNOWN_PROVIDERS == ("Claude", "Opencode", "Gemini", "Continue", "Mammouth")


def test_pipeline_active_for_provider_no_field_means_everywhere_active():
    pipeline = {"stages": []}
    for provider in KNOWN_PROVIDERS:
        assert _pipeline_active_for_provider(pipeline, provider) is True


def test_pipeline_active_for_provider_exclude():
    pipeline = {"providers": {"default": "active", "exclude": ["Claude"]}}
    assert _pipeline_active_for_provider(pipeline, "Claude") is False
    assert _pipeline_active_for_provider(pipeline, "Opencode") is True


def test_pipeline_active_for_provider_include_only():
    pipeline = {"providers": {"default": "inactive", "include": ["Gemini"]}}
    assert _pipeline_active_for_provider(pipeline, "Gemini") is True
    assert _pipeline_active_for_provider(pipeline, "Claude") is False


def test_build_pipeline_variables_empty_block_for_excluded_provider():
    pipelines = {
        "concept-to-review": {
            "description": "test",
            "providers": {"default": "active", "exclude": ["Claude"]},
            "stages": [{"id": "plan", "agent": "planner", "task": "Plan", "mode": "sequential"}],
        }
    }
    variables = build_pipeline_variables(pipelines, {})
    blocks = variables["PIPELINE_CONCEPT_TO_REVIEW_PROVIDER_BLOCKS"]
    assert blocks["Claude"] == ""
    assert blocks["Opencode"] != ""


def test_validate_pipelines_rejects_unknown_provider():
    pipelines = {
        "p1": {
            "providers": {"default": "active", "exclude": ["NotAProvider"]},
            "stages": [],
        }
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("NotAProvider" in e for e in errors)


def test_validate_pipelines_rejects_bad_default_value():
    pipelines = {"p1": {"providers": {"default": "sometimes"}, "stages": []}}
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("providers.default" in e for e in errors)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipelines.py -v`
Expected: FAIL — `ImportError: cannot import name 'KNOWN_PROVIDERS'` (and the rest, since none of the new symbols exist yet).

- [ ] **Step 3: Implement `KNOWN_PROVIDERS` and `_pipeline_active_for_provider()`**

In `scripts/lib/pipelines.py`, add near the top (after the `import` block, before `load_quality_pipelines`):

```python
KNOWN_PROVIDERS = ("Claude", "Opencode", "Gemini", "Continue", "Mammouth")
DEFAULT_MAX_DEPTH = 4


def _pipeline_active_for_provider(pipeline: dict, provider: str) -> bool:
    """Return whether a pipeline is active for `provider` per its `providers` field.

    No `providers` field means active everywhere (backward compatible with
    pipelines that predate this field, e.g. quick-fix/bugfix).
    """
    providers_cfg = pipeline.get("providers")
    if not providers_cfg:
        return True
    default = providers_cfg.get("default", "active")
    if default == "active":
        return provider not in providers_cfg.get("exclude", [])
    return provider in providers_cfg.get("include", [])
```

- [ ] **Step 4: Wire the filter into `build_pipeline_variables()` and `inject_pipeline_blocks()`**

Replace the provider loop in `build_pipeline_variables()`:

```python
        provider_blocks = {}
        for provider in KNOWN_PROVIDERS:
            if _pipeline_active_for_provider(pipeline, provider):
                provider_blocks[provider] = _generate_pipeline_block(pipeline, provider)
            else:
                provider_blocks[provider] = ""
        variables[f"PIPELINE_{var_name}_PROVIDER_BLOCKS"] = provider_blocks
```

Replace the `_replacer` inner function in `inject_pipeline_blocks()`:

```python
    def _replacer(match):
        name = match.group(1).lower().replace("_", "-")
        pipeline = pipelines.get(name)
        if not pipeline:
            return match.group(0)
        if not _pipeline_active_for_provider(pipeline, provider):
            return ""
        return _generate_pipeline_block(pipeline, provider)
```

- [ ] **Step 5: Add provider validation to `validate_pipelines()`**

Inside the `for name, pipeline in pipelines.items():` loop in `validate_pipelines()`, after the existing `stages` loop (still inside the outer `for`, same indentation as `stages = pipeline.get("stages", [])`), add:

```python
        providers_cfg = pipeline.get("providers")
        if providers_cfg:
            default = providers_cfg.get("default", "active")
            if default not in ("active", "inactive"):
                errors.append(
                    f"Pipeline '{name}': providers.default must be 'active' or "
                    f"'inactive', got '{default}'"
                )
            for key in ("include", "exclude"):
                for p in providers_cfg.get(key, []):
                    if p not in KNOWN_PROVIDERS:
                        errors.append(
                            f"Pipeline '{name}': providers.{key} entry '{p}' is not "
                            f"a known provider ({', '.join(KNOWN_PROVIDERS)})"
                        )
```

- [ ] **Step 6: Run tests to verify they pass**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS (7/7 so far)

- [ ] **Step 7: Commit**

```bash
git add scripts/lib/pipelines.py tests/test_pipelines.py
git commit -m "feat: add provider activation filter to quality pipelines"
```

---

### Task 2: `dod_flag` conditional — sync-time stage omission

**Files:**
- Modify: `scripts/lib/pipelines.py` (`_generate_pipeline_block()` signature gains `active_dod`, stage loop skips `dod_flag`-inactive stages)
- Test: `tests/test_pipelines.py`

**Interfaces:**
- Consumes: nothing new from Task 1.
- Produces: `_generate_pipeline_block(pipeline, provider, all_pipelines=None, active_dod=None, _depth=0)` — the extended signature Tasks 3-5 build on. `all_pipelines` and `_depth` are added now (unused until Task 4) so the signature only changes once.

- [ ] **Step 1: Write the failing tests**

```python
def test_generate_pipeline_block_skips_inactive_dod_flag_stage():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {"id": "always", "agent": "git", "task": "Branch anlegen", "mode": "sequential"},
            {
                "id": "req",
                "agent": "requirements",
                "task": "REQ-ID vergeben",
                "mode": "conditional",
                "condition": {"dod_flag": "req-traceability"},
            },
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode", active_dod={"req-traceability": False})
    assert "Branch anlegen" in block
    assert "REQ-ID vergeben" not in block


def test_generate_pipeline_block_includes_active_dod_flag_stage():
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


def test_generate_pipeline_block_dod_flag_defaults_to_active_when_missing():
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
    # active_dod does not mention "req-traceability" at all
    block = _generate_pipeline_block(pipeline, "Opencode", active_dod={})
    assert "REQ-ID vergeben" in block
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipelines.py -v`
Expected: FAIL — `TypeError: _generate_pipeline_block() got an unexpected keyword argument 'active_dod'`

- [ ] **Step 3: Extend the signature and add the skip check**

Change the function signature:

```python
def _generate_pipeline_block(
    pipeline: dict,
    provider: str,
    all_pipelines: dict | None = None,
    active_dod: dict | None = None,
    _depth: int = 0,
) -> str:
    """Generate a provider-specific markdown block for a single pipeline."""
    provider_key = provider.lower()
    fmt = _PROVIDER_NOTATION.get(provider_key, _PROVIDER_NOTATION["opencode"])
    active_dod = active_dod or {}
    lines = []
    stages = pipeline.get("stages", [])
    seq_idx = 0
```

At the top of the `for stage in stages:` loop, before reading `mode`/`agent`/`task`, add the skip check:

```python
    for stage in stages:
        mode = stage.get("mode", "sequential")
        if mode == "conditional":
            cond = stage.get("condition", {})
            if "dod_flag" in cond and not active_dod.get(cond["dod_flag"], True):
                continue
        agent = stage.get("agent", "")
        task = stage.get("task", "")
        stage_id = stage.get("id", "")
```

(This replaces the existing four lines that read `mode`, `agent`, `task`, `stage_id` — the new block reorders them so `mode` is available before the skip check, keeping the rest of the loop body unchanged.)

- [ ] **Step 4: Update the two callers to pass `active_dod` through**

In `build_pipeline_variables()`, the call inside the provider loop becomes:

```python
                provider_blocks[provider] = _generate_pipeline_block(
                    pipeline, provider, active_dod=active_dod
                )
```

In `inject_pipeline_blocks()`'s `_replacer`:

```python
        return _generate_pipeline_block(pipeline, provider, active_dod=active_dod)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS (10/10 so far)

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/pipelines.py tests/test_pipelines.py
git commit -m "feat: add dod_flag conditional stage omission to pipelines"
```

---

### Task 3: `payload_flag` conditional — runtime-skip annotation

**Files:**
- Modify: `scripts/lib/pipelines.py` (`conditional` branch in `_generate_pipeline_block()`)
- Test: `tests/test_pipelines.py`

**Interfaces:**
- Consumes: `_generate_pipeline_block(..., active_dod=...)` from Task 2 (unchanged signature).
- Produces: nothing new consumed by later tasks — this is a leaf rendering change.

- [ ] **Step 1: Write the failing test**

```python
def test_generate_pipeline_block_payload_flag_annotation():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {
                "id": "scope",
                "agent": "ideation",
                "task": "Idee scopen",
                "mode": "conditional",
                "condition": {"payload_flag": "needs_scoping"},
            },
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode")
    # payload_flag stages stay in the text (unlike dod_flag) — orchestrator
    # decides at runtime whether to skip them.
    assert "Idee scopen" in block
    assert "needs_scoping" in block
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipelines.py::test_generate_pipeline_block_payload_flag_annotation -v`
Expected: FAIL — `assert "needs_scoping" in block` fails (annotation text not generated yet).

- [ ] **Step 3: Add the `payload_flag` branch**

In the `elif mode == "conditional":` block, after the existing `if cond.get("type") == "agent_decision":` block, add an `elif`:

```python
        elif mode == "conditional":
            lines.append("")
            lines.append(f"**{stage_id}** — {fmt['conditional_start']}")
            lines.append(
                fmt["conditional_item"].format(agent=agent, task=task)
            )
            cond = stage.get("condition", {})
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

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS (11/11 so far)

- [ ] **Step 5: Commit**

```bash
git add scripts/lib/pipelines.py tests/test_pipelines.py
git commit -m "feat: annotate payload_flag conditional stages for runtime skip"
```

---

### Task 4: `run_pipeline` composition — cycle detection, depth limit, recursive rendering

**Files:**
- Modify: `scripts/lib/pipelines.py` (`validate_pipelines()` gains composition checks, `_generate_pipeline_block()` gains a `run_pipeline` branch)
- Test: `tests/test_pipelines.py`

**Interfaces:**
- Consumes: `_generate_pipeline_block(pipeline, provider, all_pipelines=None, active_dod=None, _depth=0)` from Task 2 (the `all_pipelines`/`_depth` params were reserved then, used now).
- Produces: nothing new consumed by later tasks.

- [ ] **Step 1: Write the failing tests**

```python
def test_validate_pipelines_detects_direct_cycle():
    pipelines = {
        "a": {"stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}]},
        "b": {"stages": [{"id": "y", "run_pipeline": "a", "mode": "run_pipeline"}]},
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("circular" in e.lower() for e in errors)


def test_validate_pipelines_detects_missing_referenced_pipeline():
    pipelines = {
        "a": {"stages": [{"id": "x", "run_pipeline": "does-not-exist", "mode": "run_pipeline"}]},
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("does-not-exist" in e for e in errors)


def test_validate_pipelines_enforces_default_max_depth():
    # a -> b -> c -> d -> e is 4 hops; default max_depth is 4, so 5 pipelines
    # (depth 5 reached) must fail, depth 4 must pass.
    pipelines = {
        "a": {"stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}]},
        "b": {"stages": [{"id": "x", "run_pipeline": "c", "mode": "run_pipeline"}]},
        "c": {"stages": [{"id": "x", "run_pipeline": "d", "mode": "run_pipeline"}]},
        "d": {"stages": [{"id": "x", "run_pipeline": "e", "mode": "run_pipeline"}]},
        "e": {"stages": []},
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert any("max_depth" in e for e in errors)


def test_validate_pipelines_max_depth_override_allows_deeper_nesting():
    pipelines = {
        "a": {
            "max_depth": 5,
            "stages": [{"id": "x", "run_pipeline": "b", "mode": "run_pipeline"}],
        },
        "b": {"stages": [{"id": "x", "run_pipeline": "c", "mode": "run_pipeline"}]},
        "c": {"stages": [{"id": "x", "run_pipeline": "d", "mode": "run_pipeline"}]},
        "d": {"stages": [{"id": "x", "run_pipeline": "e", "mode": "run_pipeline"}]},
        "e": {"stages": []},
    }
    errors = validate_pipelines(pipelines, available_roles=[])
    assert errors == []


def test_generate_pipeline_block_renders_nested_pipeline_indented():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipelines = {
        "outer": {
            "stages": [{"id": "implement", "run_pipeline": "inner", "mode": "run_pipeline"}]
        },
        "inner": {
            "stages": [{"id": "step", "agent": "developer", "task": "Feature implementieren", "mode": "sequential"}]
        },
    }
    block = _generate_pipeline_block(pipelines["outer"], "Opencode", all_pipelines=pipelines)
    assert "enthält Pipeline `inner`" in block
    assert "Feature implementieren" in block


def test_generate_pipeline_block_run_pipeline_missing_reference_is_marked():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {"stages": [{"id": "implement", "run_pipeline": "ghost", "mode": "run_pipeline"}]}
    block = _generate_pipeline_block(pipeline, "Opencode", all_pipelines={})
    assert "nicht aufgelöst" in block
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipelines.py -v`
Expected: FAIL — cycle/missing-reference/max_depth errors are never produced (no composition checks yet), and `run_pipeline` stages render nothing (mode falls through every existing `elif`).

- [ ] **Step 3: Add composition validation to `validate_pipelines()`**

Add a module-level helper above `validate_pipelines()`:

```python
def _validate_pipeline_composition(pipelines: dict, name: str, pipeline: dict) -> list[str]:
    """Check run_pipeline references for missing targets, cycles, and depth limit."""
    errors = []
    max_depth = pipeline.get("max_depth", DEFAULT_MAX_DEPTH)

    def _walk(current_name: str, visited: list[str], depth: int) -> None:
        if depth > max_depth:
            errors.append(
                f"Pipeline '{name}': run_pipeline nesting exceeds max_depth="
                f"{max_depth} (path: {' -> '.join(visited)})"
            )
            return
        current = pipelines.get(current_name)
        if current is None:
            errors.append(
                f"Pipeline '{name}': referenced pipeline '{current_name}' not found"
            )
            return
        for stage in current.get("stages", []):
            ref = stage.get("run_pipeline")
            if not ref:
                continue
            if ref in visited:
                errors.append(
                    f"Pipeline '{name}': circular run_pipeline reference "
                    f"({' -> '.join(visited + [ref])})"
                )
                continue
            _walk(ref, visited + [ref], depth + 1)

    _walk(name, [name], 1)
    return errors
```

Inside `validate_pipelines()`, in the `for name, pipeline in pipelines.items():` loop, after the `providers_cfg` block added in Task 1, add:

```python
        errors.extend(_validate_pipeline_composition(pipelines, name, pipeline))
```

- [ ] **Step 4: Add the `run_pipeline` rendering branch**

At the top of `_generate_pipeline_block()`, compute the depth cap once:

```python
    max_depth = pipeline.get("max_depth", DEFAULT_MAX_DEPTH)
```

Add a new `elif` branch (after the existing `conditional` branch, same indentation level as the other mode branches):

```python
        elif mode == "run_pipeline":
            ref_name = stage.get("run_pipeline", "")
            ref_pipeline = (all_pipelines or {}).get(ref_name)
            lines.append("")
            lines.append(f"**{stage_id}** — enthält Pipeline `{ref_name}`:")
            if ref_pipeline is None:
                lines.append(f"  [nicht aufgelöst — Pipeline '{ref_name}' nicht gefunden]")
            elif _depth >= max_depth:
                lines.append(f"  [nicht aufgelöst — max_depth={max_depth} erreicht]")
            else:
                sub_block = _generate_pipeline_block(
                    ref_pipeline,
                    provider,
                    all_pipelines=all_pipelines,
                    active_dod=active_dod,
                    _depth=_depth + 1,
                )
                for sub_line in sub_block.splitlines():
                    lines.append(f"  {sub_line}")
            lines.append("")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS (17/17 so far)

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/pipelines.py tests/test_pipelines.py
git commit -m "feat: add run_pipeline composition with cycle and depth checks"
```

---

### Task 5: `mode: plan-driven` — validation and rendering

**Files:**
- Modify: `scripts/lib/pipelines.py` (`validate_pipelines()` gains `plan-driven` role checks, `_generate_pipeline_block()` gains a `plan-driven` branch)
- Test: `tests/test_pipelines.py`

**Interfaces:**
- Consumes: `available_roles` param already present on `validate_pipelines()`.
- Produces: nothing new consumed by later tasks — last engine-primitive task in this plan.

- [ ] **Step 1: Write the failing tests**

```python
def test_validate_pipelines_plan_driven_rejects_unknown_fallback_agent():
    pipelines = {
        "p1": {
            "stages": [
                {
                    "id": "implement",
                    "mode": "plan-driven",
                    "plan-driven": {"fallback_agent": "ghost-role"},
                }
            ]
        }
    }
    errors = validate_pipelines(pipelines, available_roles=["developer"])
    assert any("ghost-role" in e for e in errors)


def test_validate_pipelines_plan_driven_rejects_unknown_allowed_agent():
    pipelines = {
        "p1": {
            "stages": [
                {
                    "id": "implement",
                    "mode": "plan-driven",
                    "plan-driven": {
                        "fallback_agent": "developer",
                        "allowed_agents": ["developer", "ghost-role"],
                    },
                }
            ]
        }
    }
    errors = validate_pipelines(pipelines, available_roles=["developer"])
    assert any("ghost-role" in e for e in errors)


def test_validate_pipelines_plan_driven_accepts_known_roles():
    pipelines = {
        "p1": {
            "stages": [
                {
                    "id": "implement",
                    "mode": "plan-driven",
                    "plan-driven": {
                        "fallback_agent": "developer",
                        "allowed_agents": ["junior-developer", "developer", "senior-developer"],
                    },
                }
            ]
        }
    }
    errors = validate_pipelines(
        pipelines, available_roles=["junior-developer", "developer", "senior-developer"]
    )
    assert errors == []


def test_generate_pipeline_block_plan_driven_rendering():
    from scripts.lib.pipelines import _generate_pipeline_block

    pipeline = {
        "stages": [
            {
                "id": "implement",
                "mode": "plan-driven",
                "plan-driven": {
                    "fallback_agent": "developer",
                    "allowed_agents": ["junior-developer", "developer", "senior-developer"],
                },
            }
        ]
    }
    block = _generate_pipeline_block(pipeline, "Opencode")
    assert "Plan-driven" in block
    assert "developer" in block
    assert "kein stiller Fallback" in block
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_pipelines.py -v`
Expected: FAIL — no `plan-driven` validation exists, and rendering produces nothing (mode falls through all branches).

- [ ] **Step 3: Add `plan-driven` validation to `validate_pipelines()`**

In the `for stage in stages:` loop in `validate_pipelines()`, after the existing `if mode == "parallel_group":` block, add:

```python
            if mode == "plan-driven":
                pd = stage.get("plan-driven", {})
                fallback = pd.get("fallback_agent")
                if fallback and fallback not in available_roles:
                    errors.append(
                        f"Pipeline '{name}': stage '{stage.get('id')}' plan-driven "
                        f"fallback_agent '{fallback}' not found in available roles."
                    )
                for allowed in pd.get("allowed_agents", []):
                    if allowed not in available_roles:
                        errors.append(
                            f"Pipeline '{name}': stage '{stage.get('id')}' plan-driven "
                            f"allowed_agents entry '{allowed}' not found in available roles."
                        )
```

- [ ] **Step 4: Add the `plan-driven` rendering branch**

Add a new `elif` branch in `_generate_pipeline_block()` (after the `run_pipeline` branch from Task 4):

```python
        elif mode == "plan-driven":
            pd = stage.get("plan-driven", {})
            fallback = pd.get("fallback_agent", "")
            allowed = pd.get("allowed_agents", [])
            lines.append("")
            lines.append(
                f"**{stage_id}** — Plan-driven: Agent aus payload.plan_ref "
                f"(Stage-ID '{stage_id}') übernehmen."
            )
            if allowed:
                lines.append(f"  Erlaubte Rollen: {', '.join(allowed)}")
            lines.append(f"  Ohne plan_ref: fallback_agent = {fallback}")
            lines.append(
                "  Plan_ref vorhanden, aber Stage-Zeile fehlt: Fehler, kein stiller Fallback."
            )
            lines.append("")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS (21/21 so far)

- [ ] **Step 6: Commit**

```bash
git add scripts/lib/pipelines.py tests/test_pipelines.py
git commit -m "feat: add plan-driven stage validation and rendering"
```

---

### Task 6: Wire real `dod_resolved` into the `agents.py` call site + full regression pass

**Files:**
- Modify: `scripts/lib/agents.py:1496-1501`
- Test: existing suite (no new test file — this task closes a latent gap so `dod_flag` actually works end-to-end when agents are generated)

**Interfaces:**
- Consumes: `resolve_dod(config: dict, agent_meta_root: Path) -> dict` from `scripts/lib/dod.py` (existing function, already used by `scripts/lib/config.py:680`).

**Context:** `sync_agents_for_provider()` in `agents.py` currently calls `inject_pipeline_blocks(content, effective, provider, {})` — the fourth argument (`active_dod`) is hardcoded to an empty dict. Since Task 2 made `active_dod` actually do something (`dod_flag` stage omission), this hardcoded `{}` means every `dod_flag`-conditional stage would render as if all DOD flags were active (because of the `.get(flag, True)` default) regardless of the project's actual DoD preset — silently wrong for any project with `req-traceability`/`tests-required`/`codebase-overview` disabled.

- [ ] **Step 1: Write the failing test**

```python
# In tests/test_pipelines.py — this test exercises agents.py, not pipelines.py directly,
# so it lives alongside the pipeline tests but imports from agents.
def test_sync_agents_passes_real_dod_resolved_to_inject_pipeline_blocks(monkeypatch):
    import scripts.lib.agents as agents_mod

    captured = {}

    def _fake_inject(content, pipelines, provider, active_dod):
        captured["active_dod"] = active_dod
        return content

    monkeypatch.setattr(agents_mod, "inject_pipeline_blocks", _fake_inject, raising=False)
    # This test only asserts the call-site wiring, not the full sync pipeline;
    # if sync_agents_for_provider is not directly unit-testable in isolation,
    # assert instead via source inspection:
    import inspect

    source = inspect.getsource(agents_mod.sync_agents_for_provider)
    assert "inject_pipeline_blocks(content, effective, provider, {})" not in source
    assert "resolve_dod(" in source
```

*(Note: this is a source-inspection test rather than a behavioral one — `sync_agents_for_provider` has too many filesystem/config side effects to unit-test cheaply in isolation. The assertion catches the exact regression described above: the hardcoded `{}` silently reappearing.)*

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_pipelines.py::test_sync_agents_passes_real_dod_resolved_to_inject_pipeline_blocks -v`
Expected: FAIL — `assert "resolve_dod(" in source` fails, `agents.py` doesn't call it yet.

- [ ] **Step 3: Fix the call site**

In `scripts/lib/agents.py`, inside `sync_agents_for_provider()`, change:

```python
        # Inject provider-specific pipeline blocks before standard substitution
        pipelines = load_quality_pipelines(str(agent_meta_root))
        pipeline_overrides = config.get("quality-pipelines", {})
        effective = apply_overrides(pipelines, pipeline_overrides)
        if effective:
            content = inject_pipeline_blocks(content, effective, provider, {})
```

to:

```python
        # Inject provider-specific pipeline blocks before standard substitution
        pipelines = load_quality_pipelines(str(agent_meta_root))
        pipeline_overrides = config.get("quality-pipelines", {})
        effective = apply_overrides(pipelines, pipeline_overrides)
        if effective:
            from .dod import resolve_dod

            dod_resolved = resolve_dod(config, agent_meta_root)
            content = inject_pipeline_blocks(content, effective, provider, dod_resolved)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_pipelines.py -v`
Expected: PASS (22/22)

- [ ] **Step 5: Run the full existing suite to confirm no regression**

Run: `pytest -q`
Expected: same pass/skip/known-failure counts as the pre-existing baseline, plus the 22 new tests in `tests/test_pipelines.py`. No new failures.

- [ ] **Step 6: Run `sync.py --validate`**

Run: `python scripts/sync.py --validate`
Expected: PASS — confirms the engine changes don't break generation for the current (unchanged) `role-defaults.yaml` content, since no pipeline in the repo uses the new fields yet (that's Plan 2 onward).

- [ ] **Step 7: Commit**

```bash
git add scripts/lib/agents.py tests/test_pipelines.py
git commit -m "fix: pass real DOD-resolved flags into pipeline block injection"
```

---

## Self-Review Notes

- **Spec coverage:** Entscheidung 1 (run_pipeline: Task 4), Entscheidung 5 (providers: Task 1), Entscheidung 9 (generic handling: satisfied by design — every new field is data-driven, no pipeline-name special-casing anywhere in Tasks 1-5), Entscheidung 11 (dod_flag/payload_flag: Tasks 2-3). Entscheidung 3 (plan-driven): Task 5 covers validation/rendering; the runtime dispatch/error-on-missing-plan-row half of Entscheidung 3 is explicitly the orchestrator's responsibility, out of scope for this engine-only plan (tracked for the plan that touches `orchestrator.md`/`_wf-orchestrator-reference.md`). Entscheidung 2, 4, 6, 7, 8, 10 are out of scope for this plan by design (separate plans).
- **Placeholder scan:** no TBD/"add error handling"/"similar to Task N" — every step has literal code.
- **Type consistency:** `_generate_pipeline_block(pipeline, provider, all_pipelines=None, active_dod=None, _depth=0)` is the final signature after Tasks 2 and 4; Task 3 and 5 use it unchanged. `KNOWN_PROVIDERS` and `DEFAULT_MAX_DEPTH` (Task 1) are reused verbatim in Task 4's `_validate_pipeline_composition()` and `_generate_pipeline_block()`. `validate_pipelines(pipelines: dict, available_roles: list) -> list[str]` signature is unchanged throughout — all new checks append to the same `errors` list.

## Next Plan

Once this lands, Plan 2 (`feature.md` → `feature-lifecycle`) can define the actual pipeline using `mode: conditional` with `dod_flag`, `mode: plan-driven`, and rename `standard-feature`. That plan depends on this one; do not start it before this plan's Task 6 is merged.
