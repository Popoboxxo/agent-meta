"""Quality pipeline configuration management and provider-specific injection."""

import json
import os
import re

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


def load_quality_pipelines(agent_meta_root: str) -> dict:
    """Load quality_pipelines from config/role-defaults.yaml."""
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


def validate_pipelines(pipelines: dict, available_roles: list) -> list[str]:
    """Validate pipelines and return a list of error messages (empty = valid).

    Checks:
    - agent exists in available_roles
    - loop.generator / loop.critic exist
    - no circular orchestration (orchestrator agents inside pipelines)
    """
    errors = []
    orchestrator_roles = {"orchestrator", "feature"}

    for name, pipeline in pipelines.items():
        stages = pipeline.get("stages", [])
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

        errors.extend(_validate_pipeline_composition(pipelines, name, pipeline))

        for stage in stages:
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

    return pattern.sub(_replacer, content)


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

        elif mode == "run_pipeline":
            ref_name = stage.get("run_pipeline", "")
            ref_pipeline = (all_pipelines or {}).get(ref_name)
            lines.append("")
            lines.append(f"**{stage_id}** — enthält Pipeline `{ref_name}`:")
            if ref_pipeline is None:
                lines.append(f"  [nicht aufgelöst — Pipeline '{ref_name}' nicht gefunden]")
            elif _depth >= _max_depth:
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

    if not lines:
        return ""

    return "\n".join(lines)
