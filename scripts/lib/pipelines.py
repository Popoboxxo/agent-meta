"""Quality pipeline configuration management and provider-specific injection."""
from __future__ import annotations

import json
import logging
import os
import re
from functools import lru_cache
from pathlib import Path

# Module-level logger for fail-soft branches that have no SyncLog instance in
# scope (Issue #568) — DEBUG-level only, so troubleshooting information isn't
# lost even though the error itself is deliberately non-fatal.
_logger = logging.getLogger(__name__)

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


def _stage_requires_approval(stage: dict, pipeline: dict) -> bool:
    """Return whether `stage` needs explicit user approval before it runs.

    Stage-level `requires_approval` overrides the pipeline-level
    `approval_default`. Neither field set means `False` — backward
    compatible with pipelines that predate this mechanism.
    """
    return bool(stage.get("requires_approval", pipeline.get("approval_default", False)))


@lru_cache(maxsize=None)
def load_quality_pipelines(agent_meta_root: str) -> dict:
    """Load quality_pipelines from config/role-defaults.yaml.

    Cached per ``agent_meta_root`` (process lifetime) — read-only framework
    config, re-parsed on every call otherwise (#553 perf hotspot).
    """
    try:
        import yaml
    except ImportError:
        return {}
    defaults_path = os.path.join(agent_meta_root, "config", "role-defaults.yaml")
    if not os.path.exists(defaults_path):
        return {}
    with open(defaults_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return config.get("quality_pipelines", {})


def load_pipeline_overrides(config_path: str) -> dict:
    """Load quality-pipelines Overrides from .meta-config/project.yaml."""
    try:
        import yaml
    except ImportError:
        return {}
    if not os.path.exists(config_path):
        return {}
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}
    return config.get("quality-pipelines", {})


def apply_overrides(base: dict, overrides: dict) -> dict:
    """Merge overrides: {**base, **override} per pipeline.

    Handles two override sources:
    - overrides.get('overrides')   -> modify existing base pipelines
    - overrides.get('custom-pipelines') -> add new project-specific pipelines
    """
    result = dict(base)

    # Apply explicit overrides to existing pipelines
    for name, override in overrides.get("overrides", {}).items():
        if name not in result:
            # New pipeline from overrides (if not explicitly disabled)
            if override.get("enabled", True):
                result[name] = override
            continue

        if override.get("enabled") is False:
            result.pop(name, None)
            continue

        merged_pipeline = {**result[name], **override}

        # Stage-level merging: override may supply stages as list or dict keyed by id
        base_stages = result[name].get("stages", [])
        override_stages = override.get("stages")
        if override_stages is not None:
            if isinstance(override_stages, list):
                merged_pipeline["stages"] = override_stages
            elif isinstance(override_stages, dict):
                # Dict keyed by stage id -> merge into base stages list
                base_by_id = {s["id"]: s for s in base_stages}
                for stage_id, stage_override in override_stages.items():
                    if stage_id in base_by_id:
                        base_by_id[stage_id] = {**base_by_id[stage_id], **stage_override}
                    else:
                        base_by_id[stage_id] = stage_override
                merged_pipeline["stages"] = list(base_by_id.values())

        result[name] = merged_pipeline

    # Add custom pipelines
    for name, custom in overrides.get("custom-pipelines", {}).items():
        result[name] = custom

    return result


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
        current_stages = current.get("stages", [])
        if not isinstance(current_stages, list):
            return  # malformed structure already reported by validate_pipelines()
        for stage in current_stages:
            if not isinstance(stage, dict):
                continue
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


def validate_pipelines(pipelines: dict, available_roles: list, roles_config: dict | None = None) -> list[str]:
    """Validate pipelines and return a list of error messages (empty = valid).

    Checks:
    - agent exists in available_roles
    - loop.generator / loop.critic exist
    - no circular orchestration (orchestrator agents inside pipelines)
    - providers field is well-formed (default/include/exclude, known providers)
    - run_pipeline composition: referenced pipelines exist, no cycles, depth limit
    - plan-driven stage roles (fallback_agent, allowed_agents) exist
    """
    errors = []
    orchestrator_roles = {"orchestrator"}

    for name, pipeline in pipelines.items():
        stages = pipeline.get("stages", [])
        if not isinstance(stages, list):
            errors.append(
                f"Pipeline '{name}': 'stages' must be a list, got "
                f"{type(stages).__name__} (check for a malformed override in "
                f".meta-config/project.yaml)"
            )
            continue
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

        approval_default = pipeline.get("approval_default")
        if approval_default is not None and not isinstance(approval_default, bool):
            errors.append(
                f"Pipeline '{name}': approval_default must be a boolean, got "
                f"{type(approval_default).__name__}"
            )

        errors.extend(_validate_pipeline_composition(pipelines, name, pipeline))

        for stage in stages:
            requires_approval = stage.get("requires_approval")
            if requires_approval is not None and not isinstance(requires_approval, bool):
                errors.append(
                    f"Pipeline '{name}': stage '{stage.get('id')}' requires_approval "
                    f"must be a boolean, got {type(requires_approval).__name__}"
                )

            agent = stage.get("agent")
            if agent and agent not in available_roles:
                if stage.get("optional"):
                    continue  # Optional stages are skipped when role is not available
                errors.append(
                    f"Pipeline '{name}': stage '{stage.get('id')}' agent '{agent}' "
                    f"not found in available roles. "
                    f"Add '{agent}' to roles: in .meta-config/project.yaml to enable this pipeline."
                )

            mode = stage.get("mode")
            if mode == "loop":
                loop = stage.get("loop", {})
                gen = loop.get("generator")
                crit = loop.get("critic")
                if gen and gen not in available_roles:
                    errors.append(
                        f"Pipeline '{name}': loop generator '{gen}' not found in available roles. "
                        f"Add '{gen}' to roles: in .meta-config/project.yaml to enable this pipeline."
                    )
                if crit and crit not in available_roles:
                    errors.append(
                        f"Pipeline '{name}': loop critic '{crit}' not found in available roles. "
                        f"Add '{crit}' to roles: in .meta-config/project.yaml to enable this pipeline."
                    )

            if mode == "parallel_group":
                pg = stage.get("parallel_group", [])
                for item in pg:
                    sub_agent = item.get("agent")
                    if sub_agent and sub_agent not in available_roles:
                        errors.append(
                            f"Pipeline '{name}': parallel_group agent '{sub_agent}' "
                            f"not found in available roles. "
                            f"Add '{sub_agent}' to roles: in .meta-config/project.yaml to enable this pipeline."
                        )

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

            # Circular orchestration guard
            if agent in orchestrator_roles and not stage.get("allow_orchestrator"):
                errors.append(
                    f"Pipeline '{name}': stage '{stage.get('id')}' uses orchestrator "
                    f"agent '{agent}' — would create circular delegation"
                )

    # Consolidated hint for missing roles
    missing_roles = set()
    for err in errors:
        if "not found in available roles" in err:
            # Extract agent name from error message
            match = re.search(r"agent '([^']+)'", err)
            if match:
                missing_roles.add(match.group(1))
            match = re.search(r"generator '([^']+)'", err)
            if match:
                missing_roles.add(match.group(1))
            match = re.search(r"critic '([^']+)'", err)
            if match:
                missing_roles.add(match.group(1))
    if missing_roles:
        errors.append(
            f"Summary: {len(missing_roles)} missing role(s): {', '.join(sorted(missing_roles))}. "
            f"Add them to 'roles:' in .meta-config/project.yaml."
        )

    # Check plan-producer coupling (non-fatal warnings)
    if roles_config is not None:
        coupling_warnings = check_plan_producer_coupling(pipelines, roles_config)
        errors.extend(coupling_warnings)

    return errors


def check_plan_producer_coupling(pipelines: dict, roles_config: dict) -> list[str]:
    """Check that every pipeline with plan-driven stages has a declared producer.

    Returns a list of warning messages (non-fatal). Empty list = consistent.
    """
    warnings = []
    roles = roles_config.get("roles", {})

    plan_driven_pipelines = set()
    for name, pipeline in pipelines.items():
        if not pipeline.get("enabled", True):
            continue
        stages = pipeline.get("stages", [])
        if not isinstance(stages, list):
            continue  # malformed structure already reported by validate_pipelines()
        for stage in stages:
            if not isinstance(stage, dict):
                continue
            if stage.get("mode") == "plan-driven":
                plan_driven_pipelines.add(name)

    if not plan_driven_pipelines:
        return warnings

    producers_by_pipeline: dict[str, list[str]] = {}
    for role_name, role_info in roles.items():
        produces = role_info.get("produces", {})
        plan_cfg = produces.get("plan")
        if plan_cfg and plan_cfg.get("pipeline"):
            pipeline_name = plan_cfg["pipeline"]
            producers_by_pipeline.setdefault(pipeline_name, []).append(role_name)

    missing = plan_driven_pipelines - set(producers_by_pipeline.keys())
    for pipeline_name in sorted(missing):
        warnings.append(
            f"Pipeline '{pipeline_name}' has plan-driven stage(s) but no role "
            f"declares produces.plan.pipeline = '{pipeline_name}'. "
            f"Add a 'produces:' block to the planner role in config/role-defaults.yaml."
        )

    for pipeline_name, producers in producers_by_pipeline.items():
        if pipeline_name not in pipelines:
            warnings.append(
                f"Role(s) {', '.join(producers)} declare produces.plan.pipeline = "
                f"'{pipeline_name}' but this pipeline does not exist."
            )
        elif pipeline_name not in plan_driven_pipelines:
            warnings.append(
                f"Role(s) {', '.join(producers)} declare produces.plan.pipeline = "
                f"'{pipeline_name}' but this pipeline has no plan-driven stages."
            )

    return warnings


def parse_plan_ref(plan_path: str) -> dict:
    """Parse a plan markdown file and extract stage-to-agent mappings.

    Recognizes two sources of stage-to-agent information, in priority order:
    1. Frontmatter field `pipeline_stages:` — explicit mapping of pipeline
       stage IDs to step numbers: ``{implement: 4, verify: 5}``
    2. Steps table (markdown table with columns Step and Agent) — treated
       as fallback: step_index → agent mapping, consumer must match stage
       IDs to step indices externally.

    Returns:
        dict with keys:
        - 'stages': dict[str, int]  — {stage_id: step_number} from frontmatter
        - 'steps':  dict[int, str]  — {step_number: agent_name} from table
        - 'raw_agents': list[str]    — all agent names found in the plan
        - 'file_exists': bool
    """
    result = {
        "stages": {},
        "steps": {},
        "raw_agents": [],
        "file_exists": False,
    }

    if not os.path.exists(plan_path):
        return result

    result["file_exists"] = True

    with open(plan_path, "r", encoding="utf-8") as f:
        content = f.read()

    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        try:
            import yaml
        except ImportError as e:
            # PyYAML is an optional dependency project-wide (see e.g.
            # lib/io.py::_YAML_AVAILABLE) — without it, the pipeline_stages
            # frontmatter override is simply unavailable; result["stages"]
            # stays at its already-initialized empty default.
            _logger.debug("parse_plan_ref: PyYAML unavailable, skipping pipeline_stages frontmatter: %s", e)
        else:
            try:
                fm = yaml.safe_load(fm_match.group(1)) or {}
                ps = fm.get("pipeline_stages")
                if isinstance(ps, dict):
                    result["stages"] = {str(k): int(v) for k, v in ps.items()}
            except (yaml.YAMLError, AttributeError, TypeError, ValueError) as e:
                # An optional `pipeline_stages:` frontmatter override is nice-
                # to-have only — malformed YAML (YAMLError), a non-mapping
                # top-level value (AttributeError on fm.get), or a non-numeric
                # stage value (TypeError/ValueError from int(v)) all fall back
                # to the already-initialized empty result["stages"] rather
                # than aborting plan-ref parsing entirely.
                _logger.debug("parse_plan_ref: pipeline_stages frontmatter ignored for %s: %s: %s", plan_path, type(e).__name__, e)

    table_pattern = re.compile(
        r'^\|\s*(\d+)\s*\|\s*.+?\|\s*`?(\w[\w-]*)`?\s*\|',
        re.MULTILINE,
    )
    for match in table_pattern.finditer(content):
        step_num = int(match.group(1))
        agent = match.group(2)
        result["steps"][step_num] = agent
        if agent not in result["raw_agents"]:
            result["raw_agents"].append(agent)

    return result


def validate_plan_ref(
    plan_path: str,
    pipeline_name: str,
    stage_id: str,
    fallback_agent: str,
    allowed_agents: list[str],
) -> list[str]:
    """Validate a plan file against a pipeline's plan-driven stage constraints.

    Returns:
        list of error messages (empty = valid plan_ref for this stage).
    """
    errors = []
    plan = parse_plan_ref(plan_path)

    if not plan["file_exists"]:
        errors.append(
            f"Plan file '{plan_path}' does not exist. "
            f"Check the plan_ref path in the payload."
        )
        return errors

    if plan["stages"]:
        if stage_id not in plan["stages"]:
            errors.append(
                f"Plan file '{plan_path}' has pipeline_stages frontmatter "
                f"but stage '{stage_id}' is not mapped. "
                f"Available stages: {', '.join(sorted(plan['stages'].keys()))}."
            )
            return errors
        step_num = plan["stages"][stage_id]
        agent = plan["steps"].get(step_num)
    else:
        if not plan["steps"]:
            errors.append(
                f"Plan file '{plan_path}' contains no parsable steps table. "
                f"Expected format: | # | Step | Agent | ... |"
            )
            return errors
        return errors

    if agent is None:
        errors.append(
            f"Plan stage '{stage_id}' maps to step {step_num}, "
            f"but step {step_num} has no agent assigned."
        )
        return errors

    if allowed_agents and agent not in allowed_agents:
        errors.append(
            f"Plan assigns agent '{agent}' to stage '{stage_id}', "
            f"but pipeline '{pipeline_name}' only allows: "
            f"{', '.join(allowed_agents)}. "
            f"Fallback agent '{fallback_agent}' will be used instead."
        )

    return errors


def generate_pipeline_match_table(pipelines: dict) -> str:
    """Generate Pipeline Match Check table from quality_pipelines config."""
    lines = ["| Signal | Pipeline |", "|--------|----------|"]
    for name, pipeline in pipelines.items():
        if not pipeline.get("enabled", True):
            continue
        keywords = pipeline.get("signal_keywords", [pipeline.get("description", name)])
        signal = " / ".join(keywords[:3])  # max 3 keywords
        lines.append(f"| {signal} | `{name}` |")
    return "\n".join(lines)


def build_pipeline_variables(pipelines: dict, active_dod: dict) -> dict:
    """Build Mustache variables for template substitution.

    Returns:
        dict with keys:
        - PIPELINE_<NAME>_ENABLED: "true" or "false"
        - PIPELINE_<NAME>_STAGES: JSON string of stages
        - PIPELINE_<NAME>_DESCRIPTION: string
        - PIPELINE_<NAME>_BLOCK: empty string (replaced by inject_pipeline_blocks)
        - PIPELINE_<NAME>_PROVIDER_BLOCKS: dict(provider -> formatted block)
    """
    variables = {}
    for name, pipeline in pipelines.items():
        var_name = name.upper().replace("-", "_")
        variables[f"PIPELINE_{var_name}_ENABLED"] = (
            "true" if pipeline.get("enabled", True) else "false"
        )
        variables[f"PIPELINE_{var_name}_STAGES"] = json.dumps(
            pipeline.get("stages", []), ensure_ascii=False
        )
        variables[f"PIPELINE_{var_name}_DESCRIPTION"] = pipeline.get("description", "")
        # Set BLOCK to empty string so substitute() never warns.
        # inject_pipeline_blocks replaces it with provider-specific content
        # before substitute() runs; for disabled pipelines strip_inactive_conditional_blocks
        # removes the surrounding {{#if}} block.
        variables[f"PIPELINE_{var_name}_BLOCK"] = ""
        # Pre-compute provider-specific blocks for later injection
        provider_blocks = {}
        for provider in KNOWN_PROVIDERS:
            if _pipeline_active_for_provider(pipeline, provider):
                provider_blocks[provider] = _generate_pipeline_block(
                    pipeline, provider, all_pipelines=pipelines, active_dod=active_dod
                )
            else:
                provider_blocks[provider] = ""
        variables[f"PIPELINE_{var_name}_PROVIDER_BLOCKS"] = provider_blocks
    return variables


def inject_pipeline_blocks(content: str, pipelines: dict, provider: str, active_dod: dict) -> str:
    """Replace {{PIPELINE_<NAME>_BLOCK}} in template with provider-optimised notation.

    Also replaces the aggregate {{PIPELINE_DETAIL_BLOCKS}} marker (all active
    pipelines, one after another) where present — see
    `generate_pipeline_detail_blocks()`.

    Runs *before* standard variable substitution so the placeholder does not
    trigger a "missing variable" warning.
    """
    pattern = re.compile(r"\{\{PIPELINE_([A-Z0-9_]+)_BLOCK\}\}")

    def _replacer(match):
        name = match.group(1).lower().replace("_", "-")
        pipeline = pipelines.get(name)
        if not pipeline:
            return match.group(0)
        if not _pipeline_active_for_provider(pipeline, provider):
            return ""
        return _generate_pipeline_block(
            pipeline, provider, all_pipelines=pipelines, active_dod=active_dod
        )

    content = pattern.sub(_replacer, content)
    if "{{PIPELINE_DETAIL_BLOCKS}}" in content:
        content = content.replace(
            "{{PIPELINE_DETAIL_BLOCKS}}",
            generate_pipeline_detail_blocks(pipelines, provider, active_dod),
        )
    return content


def generate_pipeline_detail_blocks(pipelines: dict, provider: str, active_dod: dict) -> str:
    """Concatenate provider-specific stage-detail blocks for every active pipeline.

    Companion to `generate_pipeline_match_table()` (which only lists signal →
    pipeline-name rows): this renders the actual stage-by-stage instructions
    `_generate_pipeline_block()` produces, headed by the pipeline name, for
    every pipeline that is enabled and active for `provider`.
    """
    sections = []
    for name, pipeline in pipelines.items():
        if not pipeline.get("enabled", True):
            continue
        if not _pipeline_active_for_provider(pipeline, provider):
            continue
        block = _generate_pipeline_block(
            pipeline, provider, all_pipelines=pipelines, active_dod=active_dod
        )
        if block:
            sections.append(f"### `{name}`\n{block}")
    return "\n\n".join(sections)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PROVIDER_NOTATION = {
    "opencode": {
        "task_fmt": 'task(subagent_type="{agent}", prompt="{task}")',
        "mention_fmt": "@{agent} {task}",
        "loop_start": "REPEAT_UNTIL Loop:",
        "loop_item": '  - task(subagent_type="{agent}", prompt="{task}")',
        "parallel_start": "Parallel dispatch:",
        "parallel_item": '  - task(subagent_type="{agent}", prompt="{task}")',
        "fanout_start": "FANOUT({count}, {agent}):",
        "fanout_item": '  - task(subagent_type="{agent}", prompt="{task}")',
        "conditional_start": "Conditional execution:",
        "conditional_item": '  - Condition evaluated by {agent}: {task}',
        "sequential_start": "",
        "sequential_item": '{index}. task(subagent_type="{agent}", prompt="{task}")',
    },
    "claude": {
        "task_fmt": 'background(agent="{agent}", prompt="{task}")',
        "mention_fmt": "@{agent} {task}",
        "loop_start": "REPEAT_UNTIL Loop:",
        "loop_item": '  - background(agent="{agent}", prompt="{task}")',
        "parallel_start": "Parallel dispatch:",
        "parallel_item": '  - background(agent="{agent}", prompt="{task}")',
        "fanout_start": "FANOUT({count}, {agent}):",
        "fanout_item": '  - background(agent="{agent}", prompt="{task}")',
        "conditional_start": "Conditional execution:",
        "conditional_item": '  - Condition evaluated by {agent}: {task}',
        "sequential_start": "",
        "sequential_item": '{index}. background(agent="{agent}", prompt="{task}")',
    },
    "mammouth": {
        "task_fmt": 'background(agent="{agent}", prompt="{task}")',
        "mention_fmt": "@{agent} {task}",
        "loop_start": "REPEAT_UNTIL Loop:",
        "loop_item": '  - background(agent="{agent}", prompt="{task}")',
        "parallel_start": "Parallel dispatch:",
        "parallel_item": '  - background(agent="{agent}", prompt="{task}")',
        "fanout_start": "FANOUT({count}, {agent}):",
        "fanout_item": '  - background(agent="{agent}", prompt="{task}")',
        "conditional_start": "Conditional execution:",
        "conditional_item": '  - Condition evaluated by {agent}: {task}',
        "sequential_start": "",
        "sequential_item": '{index}. background(agent="{agent}", prompt="{task}")',
    },
    "gemini": {
        "task_fmt": 'invoke_subagent("{agent}", "{task}")',
        "mention_fmt": "@{agent} {task}",
        "loop_start": "REPEAT_UNTIL Loop:",
        "loop_item": '  - invoke_subagent("{agent}", "{task}")',
        "parallel_start": "Parallel dispatch:",
        "parallel_item": '  - invoke_subagent("{agent}", "{task}")',
        "fanout_start": "FANOUT({count}, {agent}):",
        "fanout_item": '  - invoke_subagent("{agent}", "{task}")',
        "conditional_start": "Conditional execution:",
        "conditional_item": '  - Condition evaluated by {agent}: {task}',
        "sequential_start": "",
        "sequential_item": '{index}. invoke_subagent("{agent}", "{task}")',
    },
    "continue": {
        "task_fmt": "@{agent} {task}",
        "mention_fmt": "@{agent} {task}",
        "loop_start": "Iterative Review Loop (max {max_iterations}):",
        "loop_item": "  - @{agent} {task}",
        "parallel_start": "Parallel group (executed sequentially in Continue):",
        "parallel_item": "  - @{agent} {task}",
        "fanout_start": "FANOUT ({count}× {agent}):",
        "fanout_item": "  - @{agent} {task}",
        "conditional_start": "Conditional execution:",
        "conditional_item": "  - Condition evaluated by @{agent}: {task}",
        "sequential_start": "",
        "sequential_item": "{index}. @{agent} {task}",
    },
}


def _execution_mode_for_pipeline(stages: list) -> str:
    """Derive the dominant execution mode label from pipeline stages."""
    modes = {s.get("mode", "sequential") for s in stages}
    if "loop" in modes:
        return "loop"
    if "parallel_group" in modes or "fanout" in modes:
        return "parallel_group"
    return "sequential"


def _generate_pipeline_block(
    pipeline: dict,
    provider: str,
    all_pipelines: dict | None = None,
    active_dod: dict | None = None,
    _depth: int = 0,
    _max_depth: int | None = None,
) -> str:
    """Generate a provider-specific markdown block for a single pipeline."""
    provider_key = provider.lower()
    fmt = _PROVIDER_NOTATION.get(provider_key, _PROVIDER_NOTATION["opencode"])
    active_dod = active_dod or {}
    lines = []
    stages = pipeline.get("stages", [])
    seq_idx = 0
    # max_depth is resolved once at the entry point (_depth == 0) from the
    # root pipeline's own field, then threaded unchanged through recursion —
    # mirrors _validate_pipeline_composition()'s semantics, so a validated
    # composition renders consistently instead of being cut off early by a
    # sub-pipeline's own (possibly lower) default.
    if _max_depth is None:
        _max_depth = pipeline.get("max_depth", DEFAULT_MAX_DEPTH)

    # Execution mode header (Issue #285)
    exec_mode = _execution_mode_for_pipeline(stages)
    lines.append(f"Execution mode: {exec_mode}")
    lines.append("")

    for stage in stages:
        mode = stage.get("mode", "sequential")
        if mode == "conditional":
            cond = stage.get("condition", {})
            if "dod_flag" in cond and not active_dod.get(cond["dod_flag"], True):
                continue
        agent = stage.get("agent", "")
        task = stage.get("task", "")
        stage_id = stage.get("id", "")

        if _stage_requires_approval(stage, pipeline):
            lines.append(
                f"⏸ Abnahme erforderlich vor Stage '{stage_id}' — warte auf "
                f"explizite Nutzerbestätigung, bevor {agent or 'diese Stage'} startet."
            )

        if mode == "sequential":
            seq_idx += 1
            line = fmt["sequential_item"].format(
                index=seq_idx, agent=agent, task=task
            )
            lines.append(line + " → warten bis abgeschlossen")

        elif mode == "parallel_group":
            lines.append("")
            lines.append(f"**{stage_id}** — {fmt['parallel_start']}")
            pg = stage.get("parallel_group", [])
            for item in pg:
                lines.append(
                    fmt["parallel_item"].format(
                        agent=item.get("agent", ""), task=item.get("task", "")
                    )
                )
            lines.append("")

        elif mode == "fanout":
            lines.append("")
            lines.append(
                fmt["fanout_start"].format(
                    count=len(stage.get("fanout_items", [1])),
                    agent=agent,
                )
            )
            for item in stage.get("fanout_items", []):
                lines.append(
                    fmt["fanout_item"].format(
                        agent=agent, task=item.get("task", task)
                    )
                )
            lines.append("")

        elif mode == "loop":
            loop = stage.get("loop", {})
            max_iter = loop.get("max_iterations", 3)
            gen = loop.get("generator", agent)
            crit = loop.get("critic", "")
            lines.append("")
            lines.append(
                f"**{stage_id}** — {fmt['loop_start'].format(max_iterations=max_iter)}"
            )
            lines.append(
                fmt["loop_item"].format(agent=gen, task=task)
            )
            if crit:
                lines.append(
                    fmt["loop_item"].format(
                        agent=crit, task="Review / Critic feedback"
                    )
                )
            lines.append(f"  Max iterations: {max_iter} → Erfolg pruefen; bei Abbruch User benachrichtigen")
            lines.append("")

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

        elif mode == "run_pipeline":
            ref_name = stage.get("run_pipeline", "")
            ref_pipeline = (all_pipelines or {}).get(ref_name)
            lines.append("")
            lines.append(f"**{stage_id}** — enthält Pipeline `{ref_name}`:")
            if ref_pipeline is None:
                lines.append(f"  [nicht aufgelöst — Pipeline '{ref_name}' nicht gefunden]")
            elif not _pipeline_active_for_provider(ref_pipeline, provider):
                lines.append(
                    f"  [nicht aufgelöst — Pipeline '{ref_name}' für Provider {provider} inaktiv]"
                )
            elif _depth + 1 >= _max_depth:
                lines.append(f"  [nicht aufgelöst — max_depth={_max_depth} erreicht]")
            else:
                sub_block = _generate_pipeline_block(
                    ref_pipeline,
                    provider,
                    all_pipelines=all_pipelines,
                    active_dod=active_dod,
                    _depth=_depth + 1,
                    _max_depth=_max_depth,
                )
                for sub_line in sub_block.splitlines():
                    lines.append(f"  {sub_line}")
            lines.append("")

        elif mode == "plan-driven":
            pd = stage.get("plan-driven", {})
            fallback = pd.get("fallback_agent", "")
            allowed = pd.get("allowed_agents", [])
            lines.append("")
            lines.append(
                f"**{stage_id}** — Plan-driven: Agent aus payload.plan_ref "
                f"(Stage-ID '{stage_id}') übernehmen."
            )
            lines.append("")
            lines.append("  **Plan-Validierung (vor Delegation):**")
            lines.append(f"  1. Prüfe: payload.plan_ref-Pfad existiert → sonst fallback_agent = `{fallback}`")
            lines.append(f"  2. Prüfe: Plan-Frontmatter `pipeline_stages` enthält `{stage_id}` → sonst Fehler")
            if allowed:
                lines.append(f"  3. Prüfe: Agent in Stage `{stage_id}` ∈ {{{', '.join(allowed)}}} → sonst `{fallback}`")
            else:
                lines.append(f"  3. Keine allowed_agents-Restriktion — jeder Agent aus Plan akzeptiert")
            lines.append(f"  4. Bei allen Fehlern: `{fallback}` verwenden, Fehler in Status-Payload dokumentieren")
            lines.append("")

    if not lines:
        return ""

    return "\n".join(lines)


def resolve_pipeline_details_dir(pc: dict, provider: str) -> str:
    """Resolve the provider-specific pipeline-detail-files directory.

    An explicit `pipeline_details_dir` in ai-providers.yaml wins. Otherwise
    derived as a sibling of `agents_dir` — not a naive `.{provider.lower()}/`
    literal — so providers with non-standard nesting (e.g. Copilot's
    `.github/copilot/agents`) resolve correctly instead of a wrong
    `.copilot/pipeline-details`. The basename is always "pipeline-details"
    regardless of provider (see `_PIPELINE_DETAILS_DIR_NAME` in
    external_tools_drift.py, which relies on this for drift-detection).
    """
    if pc.get("pipeline_details_dir"):
        return pc["pipeline_details_dir"]
    agents_dir = pc.get("agents_dir", f".{provider.lower()}/agents")
    return str(Path(agents_dir).parent / "pipeline-details")


def sync_pipeline_detail_files(
    pipelines: dict,
    provider: str,
    target_dir,
    project_root,
    active_dod: dict,
    log,
    dry_run: bool,
) -> None:
    """Write one `<name>.md` stage-detail file per active pipeline to `target_dir`.

    Lean, token-saving companion to `generate_pipeline_detail_blocks()`: instead
    of inlining every pipeline's full stage detail into an always-loaded rules
    file (main-chat mode's `use-orchestrator.md`), each pipeline gets its own
    file that `main_chat` reads on demand only once it actually routes there —
    the always-on cost stays a single routing-table line pointing at this
    directory. Stale files (pipeline renamed/removed/disabled) are cleaned up
    via the same previously_managed/now_managed index pattern used by
    `mcp.py`/`external_tools.py` (`scripts/lib/rule_index.py`).
    """
    from .io import safe_path, write_checked
    from .rule_index import (
        bootstrap_previously_managed,
        cleanup_stale_managed_files,
        write_managed_index,
    )

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    managed_index_path = target_dir / ".agent-meta-managed"
    previously_managed = bootstrap_previously_managed(target_dir, managed_index_path, "*.md")
    now_managed: set[str] = set()

    for name, pipeline in pipelines.items():
        if not pipeline.get("enabled", True):
            continue
        if not _pipeline_active_for_provider(pipeline, provider):
            continue
        block = _generate_pipeline_block(
            pipeline, provider, all_pipelines=pipelines, active_dod=active_dod
        )
        if not block:
            continue

        filename = f"{name}.md"
        now_managed.add(filename)
        target_path = safe_path(target_dir, filename)
        rel_out = str(target_path.relative_to(project_root))
        content = f"# Pipeline `{name}`\n\n{block}\n"

        if write_checked(target_path, content, log, f"pipelines/{name}", dry_run=dry_run):
            log.action("WRITE", rel_out, f"pipeline-details/{name}")
        else:
            log.skip(rel_out, "unchanged")

    cleanup_stale_managed_files(
        target_dir, project_root, previously_managed, now_managed, log, dry_run,
        "pipeline no longer active/enabled",
    )
    write_managed_index(managed_index_path, now_managed, dry_run)
