"""Config loading, validation, variable building and substitution."""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .io import _load_yaml_or_json, _write_yaml
from .log import SyncLog
from .pipelines import (
    load_quality_pipelines,
    load_pipeline_overrides,
    apply_overrides,
    validate_pipelines,
    build_pipeline_variables,
    generate_pipeline_match_table,
)

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

try:
    import jsonschema as _jsonschema
    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _JSONSCHEMA_AVAILABLE = False


# Top-level fields with a meaningful default value.
_CONFIG_FIELD_DEFAULTS: dict = {
    "dod-preset": "full",
    "max-parallel-agents": 2,
    "speech-mode": "full",
}

# dod sub-fields with defaults (mirrors the "full" preset in dod-presets.config.yaml)
_DOD_FIELD_DEFAULTS: dict = {
    "req-traceability": True,
    "tests-required": True,
    "codebase-overview": True,
    "security-audit": False,
    "se-required": "false",
}


def load_config(config_path: Path) -> dict:
    """Load .meta-config/project.yaml or .meta-config/project.yaml.

    If the provided path ends in .json but a sibling .yaml file exists,
    the YAML file is preferred (migration path: old --config still works).
    """
    if not config_path.exists():
        # Try YAML counterpart if a .json path was given
        if config_path.suffix == ".json":
            yaml_path = config_path.with_suffix(".yaml")
            if yaml_path.exists():
                config_path = yaml_path
            else:
                print(f"ERROR: config not found: {config_path}", file=sys.stderr)
                sys.exit(1)
        else:
            print(f"ERROR: config not found: {config_path}", file=sys.stderr)
            sys.exit(1)

    suffix = config_path.suffix.lower()
    if suffix in (".yaml", ".yml"):
        if not _YAML_AVAILABLE:
            print(f"ERROR: PyYAML not installed but {config_path.name} requires it. "
                  f"Run: pip install pyyaml", file=sys.stderr)
            sys.exit(1)
        try:
            with config_path.open(encoding="utf-8") as f:
                config = _yaml.safe_load(f) or {}
        except _yaml.YAMLError as exc:
            # Provide file name and line info for easier debugging
            mark = getattr(exc, "problem_mark", None)
            location = f" (line {mark.line + 1}, col {mark.column + 1})" if mark else ""
            print(
                f"ERROR: YAML parse error in {config_path}{location}: {exc}",
                file=sys.stderr,
            )
            sys.exit(1)
    else:
        try:
            with config_path.open(encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as exc:
            print(
                f"ERROR: JSON parse error in {config_path} (line {exc.lineno}, col {exc.colno}): {exc.msg}",
                file=sys.stderr,
            )
            sys.exit(1)

    _validate_config(config, config_path)
    return config


def _validate_config(config: dict, config_path: Path) -> None:
    """Validate config against agent-meta.schema.json if jsonschema is available.

    Validation errors are printed as warnings — never hard-fails so existing
    projects without the dependency continue to work unchanged.
    """
    if not _JSONSCHEMA_AVAILABLE:
        return

    schema_path = Path(__file__).resolve().parent.parent.parent / "config/project-config.schema.json"
    if not schema_path.exists():
        schema_path = Path(__file__).resolve().parent.parent.parent / "agent-meta.schema.json"
    if not schema_path.exists():
        return

    try:
        with schema_path.open(encoding="utf-8") as f:
            schema = json.load(f)
        validator = _jsonschema.Draft7Validator(schema)
        errors = sorted(validator.iter_errors(config), key=lambda e: list(e.path))
        if errors:
            print(f"  !  Config validation warnings ({len(errors)}) — "
                  f"fix or install jsonschema to suppress this check:", file=sys.stderr)
            for err in errors[:5]:  # cap at 5 to avoid noise
                path = ".".join(str(p) for p in err.path) or "(root)"
                print(f"       {path}: {err.message}", file=sys.stderr)
            if len(errors) > 5:
                print(f"       ... and {len(errors) - 5} more", file=sys.stderr)
    except (ImportError, TypeError, ValueError) as e:
        pass  # jsonschema not installed or validation error — best-effort


def find_agent_meta_root(script_path: Path) -> Path:
    # script_path = scripts/sync.py → scripts/ → agent-meta root
    return script_path.parent.parent


def _load_schema_variable_keys(agent_meta_root: Path) -> list[str]:
    """Return the list of known variable keys from agent-meta.schema.json."""
    schema_path = agent_meta_root / "config/project-config.schema.json"
    if not schema_path.exists():
        schema_path = agent_meta_root / "agent-meta.schema.json"
    if not schema_path.exists():
        return []
    try:
        with schema_path.open(encoding="utf-8") as f:
            schema = json.load(f)
        props = schema.get("properties", {}).get("variables", {}).get("properties", {})
        return list(props.keys())
    except (OSError, json.JSONDecodeError, KeyError):
        return []


def fill_defaults(
    config_path: Path,
    agent_meta_root: Path,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Write missing config fields with their default values into .meta-config/project.yaml.

    Structural fields (dod-preset, max-parallel-agents, speech-mode, dod.*):
      Written into the config file when absent.

    Variable fields (variables.*):
      Only reported as [WARN] — no empty strings written (no sensible default).
    """
    config = load_config(config_path)
    changed = False
    added: list[str] = []

    # --- Top-level structural fields ---
    for field, default in _CONFIG_FIELD_DEFAULTS.items():
        if field not in config:
            config[field] = default
            added.append(f"{field} = {json.dumps(default)}")
            changed = True

    # --- dod sub-fields ---
    # Only fill dod.* fields when no preset is set (or preset is "full").
    # A non-full preset already defines its own defaults — writing "full" defaults
    # on top would silently override the preset and create an inconsistent config.
    active_preset = config.get("dod-preset", "full")
    if active_preset == "full":
        dod_block = config.get("dod", {})
        dod_additions: list[str] = []
        for field, default in _DOD_FIELD_DEFAULTS.items():
            if field not in dod_block:
                dod_block[field] = default
                dod_additions.append(f"dod.{field} = {json.dumps(default)}")
                changed = True
        if dod_additions:
            config["dod"] = dod_block
            added.extend(dod_additions)
    else:
        log.info("fill-defaults", f"dod.* skipped — preset '{active_preset}' defines its own defaults")

    # --- Write back if changed ---
    if changed and not dry_run:
        if config_path.suffix.lower() in (".yaml", ".yml"):
            _write_yaml(config_path, config)
        else:
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
                f.write("\n")

    for entry in added:
        action = "FILL" if not dry_run else "FILL(dry)"
        log.action(action, str(config_path.name), entry)

    if not changed:
        log.info("fill-defaults", "all structural fields already set — nothing to write")

    # --- Warn about missing variable keys ---
    known_vars = _load_schema_variable_keys(agent_meta_root)
    set_vars = set(config.get("variables", {}).keys())
    missing_vars = [v for v in known_vars if v not in set_vars]
    for var in missing_vars:
        log.warn(f"Variable not set in config: variables.{var}")


def read_version(agent_meta_root: Path) -> str:
    version_file = agent_meta_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "unknown"


def read_git_version(agent_meta_root: Path) -> str:
    """Return the actual git tag version of agent-meta via git describe --tags.

    Falls back to 'unknown' if git is unavailable or no tags exist.
    """
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=str(agent_meta_root),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip().lstrip("v")
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


def _load_se_variable_defaults(agent_meta_root: Path) -> dict:
    """Load SE cascade variable defaults from config/role-defaults.yaml se_variables block.

    Returns a dict of {TEMPLATE_VAR_NAME: default_value} for variables not set
    in the project config. Template var names are the same as the YAML keys (uppercase).
    """
    defaults_path = agent_meta_root / "config" / "role-defaults.yaml"
    if not defaults_path.exists():
        return {}
    try:
        raw = _load_yaml_or_json(defaults_path)
        se_vars = raw.get("se_variables", {})
        if not isinstance(se_vars, dict):
            return {}
        return {str(k): v for k, v in se_vars.items()}
    except Exception:
        return {}


def build_variables(config: dict, agent_meta_root: Path) -> tuple[dict, list[str]]:
    """Returns (variables_dict, pre_warnings)."""
    # Import here to avoid circular deps — agents module uses config module
    from .agents import build_agent_hints, build_agent_table
    from .delegation_table import (
        generate_agent_delegation_table,
        generate_intent_routing_table,
    )
    from .dod import resolve_dod
    from .providers import load_providers_config, resolve_providers

    variables = {}
    project = config.get("project", {})
    variables["PREFIX"]       = project.get("prefix", "")
    variables["PROJECT_SHORT"] = project.get("short", "")
    variables["PROJECT_NAME"]  = project.get("name", "")
    variables["AGENT_META_VERSION"] = read_version(agent_meta_root)
    variables["AGENT_META_DATE"]    = datetime.now().strftime("%Y-%m-%d")
    agent_table, unmapped = build_agent_table(config, agent_meta_root)
    variables["AGENT_TABLE"] = agent_table
    variables["AGENT_HINTS"] = build_agent_hints(config, agent_meta_root)
    # AGENT_HINTS_CLAUDE: entry-point hint without the per-agent table.
    # Claude Code injects agent descriptions natively into the system prompt,
    # so the table in CLAUDE.md would be a duplication — dropped for Claude only.
    variables["AGENT_HINTS_CLAUDE"] = build_agent_hints(
        config, agent_meta_root, include_table=False
    )
    # User variables may be YAML scalars (true, 20) — coerce to the string form
    # templates expect ("true"/"false" for {{#if}} blocks, str() otherwise).
    for key, value in (config.get("variables") or {}).items():
        if isinstance(value, bool):
            variables[key] = "true" if value else "false"
        elif not isinstance(value, str):
            variables[key] = str(value)
        else:
            variables[key] = value
    # REQ category placeholders: guarantee substitution so generated context
    # files never keep a literal {{REQ_CATEGORIES_LIST}} / {{REQ_CATEGORIES}}.
    # User-set values (loaded above) take precedence; otherwise derive the long
    # form from the short form (and vice versa), falling back to generic defaults.
    if not variables.get("REQ_CATEGORIES_LIST"):
        variables["REQ_CATEGORIES_LIST"] = variables.get("REQ_CATEGORIES") or (
            "- **Kernfunktionalität** — Kernfeatures des Projekts\n"
            "- **Lifecycle** — Startup, Shutdown, Fehlerbehandlung\n"
            "- **Nichtfunktionale Anforderungen** — Performance, Sicherheit, Wartbarkeit"
        )
    if not variables.get("REQ_CATEGORIES"):
        variables["REQ_CATEGORIES"] = variables.get("REQ_CATEGORIES_LIST") or (
            "- Kernfunktionalität\n- Lifecycle\n- Nichtfunktionale Anforderungen"
        )
    # AGENTS_DIR: provider-agnostic generated agents directory (default: .claude/agents)
    if "AGENTS_DIR" not in variables:
        variables["AGENTS_DIR"] = ".claude/agents"
    # PROJECT_GOAL: fall back to the project description when not set explicitly
    if not variables.get("PROJECT_GOAL") and variables.get("PROJECT_DESCRIPTION"):
        variables["PROJECT_GOAL"] = variables["PROJECT_DESCRIPTION"]
    # AI_PROVIDER: auto-inject from top-level config field (not nested in variables)
    if "AI_PROVIDER" not in variables:
        provider_config = load_providers_config(agent_meta_root)
        variables["AI_PROVIDER"] = config.get("ai-provider", "") or ", ".join(
            resolve_providers(config, provider_config)
        )
    # MAX_PARALLEL_AGENTS: auto-inject from top-level config field (default: 2)
    variables["MAX_PARALLEL_AGENTS"] = str(config.get("max-parallel-agents", 2))
    # ORCHESTRATOR_MODE: auto-inject from orchestrator block in project.yaml
    orch_config = config.get("orchestrator", {})
    variables["ORCHESTRATOR_ENABLED"] = "true" if orch_config.get("enabled", True) else "false"
    variables["ORCHESTRATOR_STRICT"] = "true" if orch_config.get("strict", True) else "false"
    variables["DIRECT_DISPATCH_ENABLED"] = "true" if orch_config.get("direct-dispatch-enabled", True) else "false"
    # ORCH_MODE_*: mutually-exclusive, flat mode flags for the use-orchestrator rule.
    # Exactly one is "true". These replace nested {{#if}}/{{else}} in the rule
    # template so the conditional stripper can never render two modes at once.
    _orch_enabled = orch_config.get("enabled", True)
    _orch_strict = orch_config.get("strict", True)
    variables["ORCH_MODE_DISABLED"] = "true" if not _orch_enabled else "false"
    variables["ORCH_MODE_STRICT"]   = "true" if (_orch_enabled and _orch_strict) else "false"
    variables["ORCH_MODE_ADVISORY"] = "true" if (_orch_enabled and not _orch_strict) else "false"
    # A2A_PROTOCOL_ENABLED: structured agent-to-agent handoff envelope.
    # Active when orchestrator.handoff.protocol is set (default "a2a-v1").
    # Disable via handoff.protocol: none/false to drop the ~90-line A2A section.
    _handoff_cfg = orch_config.get("handoff", {})
    _handoff_protocol = _handoff_cfg.get("protocol", "a2a-v1") if isinstance(_handoff_cfg, dict) else _handoff_cfg
    variables["A2A_PROTOCOL_ENABLED"] = (
        "false" if str(_handoff_protocol).lower() in ("none", "false", "off", "") else "true"
    )
    # DIRECT_DISPATCH_SECTION: loaded from central template file; empty when direct dispatch is disabled
    _dd_enabled = orch_config.get("direct-dispatch-enabled", True)
    if _dd_enabled:
        _dd_template = agent_meta_root / "templates" / "direct-dispatch-section.md"
        variables["DIRECT_DISPATCH_SECTION"] = _dd_template.read_text(encoding="utf-8") if _dd_template.exists() else ""
    else:
        variables["DIRECT_DISPATCH_SECTION"] = ""
    # ORCHESTRATOR_OUTCOME_CACHING: auto-inject from outcome-caching block in project.yaml
    oc_config = config.get("outcome-caching", {})
    variables["ORCHESTRATOR_OUTCOME_CACHING"] = "true" if oc_config.get("enabled", False) else "false"
    variables["ORCHESTRATOR_CACHE_TTL"] = str(oc_config.get("ttl_seconds", 3600))
    variables["ORCHESTRATOR_CACHE_MAX_ENTRIES"] = str(oc_config.get("max_entries", 100))
    # CHECKPOINTING_ENABLED: persistent session checkpoints for long orchestrations.
    # Default on; disable via orchestrator.checkpointing: false for lightweight projects.
    variables["CHECKPOINTING_ENABLED"] = (
        "false" if orch_config.get("checkpointing", True) is False else "true"
    )
    # ANALYSIS_ENABLED: AST-based file affinity analysis for parallelization hints.
    # Activate via: analysis: enabled: true in project.yaml (default: false).
    # When enabled, FILE_AFFINITY_HINT is populated with a Markdown dependency table.
    _analysis_cfg = config.get("analysis", {})
    _analysis_enabled = bool(_analysis_cfg.get("enabled", False)) if isinstance(_analysis_cfg, dict) else False
    variables["ANALYSIS_ENABLED"] = "true" if _analysis_enabled else "false"
    if _analysis_enabled:
        try:
            from .analysis import FileAffinityAnalyzer, analyze_project
            _deps = analyze_project(agent_meta_root)
            _analyzer = FileAffinityAnalyzer(agent_meta_root)
            variables["FILE_AFFINITY_HINT"] = _analyzer.format_hint(_deps)
        except Exception:
            variables["FILE_AFFINITY_HINT"] = ""
    else:
        variables["FILE_AFFINITY_HINT"] = ""
    # UNKNOWN_FALLBACK: granular flags (new object format) or legacy string
    unknown_fallback = orch_config.get("unknown-fallback", {})
    if isinstance(unknown_fallback, str):
        # Legacy string format: backward compatibility
        variables["UNKNOWN_FALLBACK_META_FEEDBACK"] = "true" if unknown_fallback == "meta-feedback" else "false"
        variables["UNKNOWN_FALLBACK_MAIN_CHAT"] = "true" if unknown_fallback == "main-chat" else "false"
        variables["UNKNOWN_FALLBACK_ASK_USER"] = "true" if unknown_fallback == "ask-user" else "false"
    else:
        # New object format: individual boolean flags
        variables["UNKNOWN_FALLBACK_META_FEEDBACK"] = "true" if unknown_fallback.get("meta-feedback", True) else "false"
        variables["UNKNOWN_FALLBACK_MAIN_CHAT"] = "true" if unknown_fallback.get("main-chat", True) else "false"
        variables["UNKNOWN_FALLBACK_ASK_USER"] = "true" if unknown_fallback.get("ask-user", False) else "false"
    # SYSTEMS_ENGINEERING_ENABLED
    se_config = config.get("systems-engineering", {})
    variables["SE_ENABLED"] = "true" if se_config.get("enabled", False) else "false"
    # SE_BASE_DIR: configurable output directory for SE artifacts.
    # Read from se_output.base_dir (default: "SE").
    se_output = config.get("se_output", {})
    variables["SE_BASE_DIR"] = se_output.get("base_dir", "SE") if isinstance(se_output, dict) else "SE"
    # SE cascade variables — fall back to role-defaults.yaml defaults if not set in project config.
    _se_vars_defaults = _load_se_variable_defaults(agent_meta_root)
    for _sv_key, _sv_val in _se_vars_defaults.items():
        if _sv_key not in variables:
            variables[_sv_key] = str(_sv_val)
    # A2A_T_SIZE_LIMIT / A2A_T_SIZE_LIMIT_TOKENS: hard gate for payload.t inline length.
    t_limit = _handoff_cfg.get("t-size-limit", 300) if isinstance(_handoff_cfg, dict) else 300
    variables["A2A_T_SIZE_LIMIT"] = str(t_limit)
    variables["A2A_T_SIZE_LIMIT_TOKENS"] = str(max(1, t_limit // 4))
    # A2A_MAX_DEPTH: configurable maximum delegation depth before HARD REJECT.
    # Read from orchestrator.delegation.max_depth (default: 10, range: 1-50).
    _delegation_cfg = orch_config.get("delegation", {})
    _max_depth = _delegation_cfg.get("max_depth", 10) if isinstance(_delegation_cfg, dict) else 10
    if not isinstance(_max_depth, int) or isinstance(_max_depth, bool):
        _max_depth = 10
    _max_depth = max(1, min(50, _max_depth))  # clamp to valid range
    variables["A2A_MAX_DEPTH"] = str(_max_depth)
    # VALIDATOR_ENABLED: auto-detect from project roles list
    variables["VALIDATOR_ENABLED"] = "true" if "validator" in config.get("roles", []) else "false"
    # DEVELOPER_TIERS_ENABLED: 3-tier developer system (junior/developer/senior)
    # — active only when both tier roles are enabled in the project
    _roles = config.get("roles", [])
    variables["DEVELOPER_TIERS_ENABLED"] = (
        "true" if "junior-developer" in _roles and "senior-developer" in _roles else "false"
    )
    # EFFORT_ESTIMATOR_ENABLED: auto-detect from project roles list
    # — orchestrator gates effort-estimator routes behind this flag to avoid dead routes
    variables["EFFORT_ESTIMATOR_ENABLED"] = "true" if "effort-estimator" in _roles else "false"
    # WEB_PROJECT_ENABLED: auto-detect web-oriented projects from the roles list.
    # — derived purely from role activation (e2e-tester present), no separate
    #   config flag. Gates browser-verification and web-vitals blocks in the
    #   developer/senior-developer/performance-optimizer templates.
    variables["WEB_PROJECT_ENABLED"] = "true" if "e2e-tester" in _roles else "false"
    # AGENT_DELEGATION_TABLE: generate after SE_ENABLED and VALIDATOR_ENABLED are set
    variables["AGENT_DELEGATION_TABLE"] = generate_agent_delegation_table(agent_meta_root, config, variables)
    # PROJECT_SPECIFIC_AGENTS: placeholder for future project-specific agent table injection
    # Currently empty — will be populated when project-specific agent discovery is implemented
    variables["PROJECT_SPECIFIC_AGENTS"] = ""
    # DOD_*: resolve from dod-preset (base) + dod (overrides).
    # Precedence: dod (project override) > dod-preset > "full" (implicit default).
    dod_resolved = resolve_dod(config, agent_meta_root)
    variables["DOD_REQ_TRACEABILITY"] = "true" if dod_resolved.get("req-traceability", True) else "false"
    variables["DOD_TESTS_REQUIRED"]   = "true" if dod_resolved.get("tests-required", True) else "false"
    variables["DOD_CODEBASE_OVERVIEW"] = "true" if dod_resolved.get("codebase-overview", True) else "false"
    variables["DOD_SECURITY_AUDIT"]   = "true" if dod_resolved.get("security-audit", False) else "false"
    variables["DOD_PRESET"]           = config.get("dod-preset", "full")
    # SE-Required mode: derive boolean flags from the se-required string field
    se_required = str(dod_resolved.get("se-required", "false")).lower()
    variables["DOD_SE_REQUIRED"]    = se_required  # "false" | "recommended" | "true"
    variables["DOD_SE_OPTIONAL"]    = "true" if se_required == "false" else "false"
    variables["DOD_SE_RECOMMENDED"] = "true" if se_required == "recommended" else "false"
    variables["DOD_SE_STRICT"]      = "true" if se_required == "true" else "false"
    # INTENT_ROUTING_TABLE: generate after all gating flags are resolved
    variables["INTENT_ROUTING_TABLE"] = generate_intent_routing_table(agent_meta_root, config, variables)
    # REFLECTION_PAIRS_ENABLED: auto-detect from role-defaults.yaml
    variables["REFLECTION_PAIRS_ENABLED"] = "false"
    variables["MAX_ITERATIONS"] = "3"  # default for reflection loops
    try:
        roles_defaults_path = agent_meta_root / "config" / "role-defaults.yaml"
        if roles_defaults_path.exists() and _YAML_AVAILABLE:
            with roles_defaults_path.open(encoding="utf-8") as f:
                roles_defaults = _yaml.safe_load(f) or {}
            if roles_defaults.get("reflection_pairs"):
                variables["REFLECTION_PAIRS_ENABLED"] = "true"
    except Exception:
        pass
    # QUALITY_PIPELINES_ENABLED: auto-detect from role-defaults.yaml + project overrides
    variables["QUALITY_PIPELINES_ENABLED"] = "false"
    try:
        pipelines = load_quality_pipelines(str(agent_meta_root))
        overrides = config.get("quality-pipelines", {})
        effective = apply_overrides(pipelines, overrides)
        # Validate pipeline agent references against available roles
        from .roles import build_role_map
        all_roles = list(build_role_map(agent_meta_root).keys())
        if "roles" in config:
            available_roles = set(config["roles"])
        else:
            available_roles = set(all_roles)
        pipeline_errors = validate_pipelines(effective, list(available_roles))
        for err in pipeline_errors:
            unmapped.append(f"quality-pipelines: {err}")
        if effective:
            variables["QUALITY_PIPELINES_ENABLED"] = "true"
        # Build variables for active pipelines; also set BLOCK="" for disabled
        # base pipelines so substitute() never warns about missing placeholders.
        active_vars = build_pipeline_variables(effective, dod_resolved)
        variables.update(active_vars)
        variables["PIPELINE_MATCH_TABLE"] = generate_pipeline_match_table(effective)
        for name in pipelines:
            var_name = name.upper().replace("-", "_")
            block_key = f"PIPELINE_{var_name}_BLOCK"
            enabled_key = f"PIPELINE_{var_name}_ENABLED"
            if block_key not in variables:
                variables[block_key] = ""
            if enabled_key not in variables:
                variables[enabled_key] = "false"
    except Exception:
        pass
    # AGENT_PROMPTS: mode config for Modern/Hybrid/Legacy prompt rendering.
    # Reads agent-prompts block: {default: legacy, modes: {developer: modern, ...}}
    _ap = config.get("agent-prompts", {}) or {}
    _ap_default = _ap.get("default", "legacy") if isinstance(_ap, dict) else "legacy"
    _ap_modes = _ap.get("modes", {}) or {} if isinstance(_ap, dict) else {}
    variables["AGENT_PROMPTS_DEFAULT"] = _ap_default
    for _role, _mode in (_ap_modes.items() if isinstance(_ap_modes, dict) else {}.items()):
        variables[f"AGENT_PROMPTS_MODE_{_role.upper().replace('-', '_')}"] = str(_mode)

    # Pre-resolved block variables for Modern Mode templates (no {{#if}} needed).
    # Each block is either the real content or an empty string when the flag is off.
    _dod_req = dod_resolved.get("req-traceability", True)
    variables["DOD_REQ_BLOCK"] = (
        "REQ-ID aus `REQUIREMENTS.md` prüfen — kein Commit ohne REQ-ID." if _dod_req else ""
    )
    _dod_tests = dod_resolved.get("tests-required", True)
    variables["DOD_TESTS_BLOCK"] = (
        "Tests schreiben/aktualisieren — Pflicht vor Commit." if _dod_tests else ""
    )
    variables["A2A_HANDOFF_BLOCK"] = (
        "A2A-Envelopes verwenden: IPayload (t, ctx, con, refs, pri, dep), "
        "IEnvelope (protocol_version, handoff_id, source_agent, target_agent, schema_ref, payload). "
        f"payload.t ≤ {variables.get('A2A_T_SIZE_LIMIT', '300')} Zeichen."
        if variables.get("A2A_PROTOCOL_ENABLED") == "true" else ""
    )
    variables["ANTI_RECURSION_BLOCK"] = (
        "Anti-Recursion: NIEMALS zurück an orchestrator delegieren. "
        "Nur tester/documenter/requirements/validator aus Kontext verweisen."
    )

    # Orchestrator conditional blocks loaded from snippets (token optimization).
    # Each block is either the real conditional section or an empty string.
    _snippets_dir = agent_meta_root / "snippets" / "orchestrator"
    for _snippet_name, _var_stem in (
        ("se-mode", "SE_MODE"),
        ("a2a-protocol", "A2A_PROTOCOL"),
        ("checkpointing", "CHECKPOINTING"),
        ("quality-pipelines", "QUALITY_PIPELINES"),
    ):
        _snippet_path = _snippets_dir / f"{_snippet_name}.md"
        _var_name = f"{_var_stem}_BLOCK"
        variables[_var_name] = _snippet_path.read_text(encoding="utf-8") if _snippet_path.exists() else ""

    return variables, unmapped


def strip_inactive_conditional_blocks(text: str, variables: dict) -> str:
    """Remove conditional blocks that are inactive in this project.

    Handles:
        {{#if VAR}}...content...{{/if}}
        {{#if VAR}}...content...{{else}}...alt-content...{{/if}}
        {{#unless VAR}}...content...{{/unless}}

    Nested blocks are resolved via repeated passes until no markers remain.

    Uses a guarded non-greedy pattern to prevent cross-block matching
    (e.g. DOD_REQ_TRACEABILITY accidentally matching the ORCHESTRATOR_ENABLED
    block's {{else}} token).
    """
    conditional_vars = {k for k in variables if (k.startswith("DOD_") or k in ("SE_ENABLED", "VALIDATOR_ENABLED", "QUALITY_PIPELINES_ENABLED", "DEVELOPER_TIERS_ENABLED", "EFFORT_ESTIMATOR_ENABLED", "WEB_PROJECT_ENABLED")) and k != "DOD_PRESET"}
    conditional_vars.update({k for k in variables if k.startswith("PIPELINE_") and k.endswith("_ENABLED")})
    conditional_vars.update({k for k in variables if k in ("ORCHESTRATOR_ENABLED", "ORCHESTRATOR_STRICT", "DIRECT_DISPATCH_ENABLED", "UNKNOWN_FALLBACK_ASK_USER", "UNKNOWN_FALLBACK_META_FEEDBACK", "UNKNOWN_FALLBACK_MAIN_CHAT", "A2A_PROTOCOL_ENABLED", "ORCHESTRATOR_OUTCOME_CACHING", "CHECKPOINTING_ENABLED", "ANALYSIS_ENABLED", "FILE_BASED_AGENTS")})
    conditional_vars.update({k for k in variables if k.startswith("ORCH_MODE_")})

    if not conditional_vars:
        return text

    # Repeat until stable — handles nested blocks
    max_passes = 10
    for _pass in range(max_passes):
        made_change = False
        for var in conditional_vars:
            var_pattern = re.escape(var)

            # Process simple-if FIRST (before if-else) to prevent
            # cross-block matching: a simple {{#if A}}...{{/if}} should
            # never accidentally capture a downstream {{else}} token.
            #
            # 1. Handle {{#if VAR}}...{{/if}} (simple, no else)
            def replace_if(m: re.Match, _var: str = var) -> str:
                block_content = m.group(1)
                if variables.get(_var, "true") == "false":
                    return ""
                stripped = block_content.strip("\n")
                if m.group(0).endswith("\n"):
                    return stripped + "\n"
                return stripped

            # Guard: prevent simple-if from matching if-else blocks
            # by not crossing {{/if}} or {{else}} boundaries. Also refuse to
            # cross a nested opening marker ({{#if}}/{{#unless}}), so only true
            # innermost blocks match. This makes stripping resolve nested blocks
            # inner-to-outer regardless of the (set-derived) variable iteration
            # order — otherwise output is non-deterministic across processes.
            _simple_body = r"(?:(?!\{\{/if\}\}|\{\{else\}\}|\{\{#if |\{\{#unless ).)*?"
            pattern_if = rf"\{{{{#if {var_pattern}\}}}}\n?({_simple_body})\{{{{/if\}}}}\n?"
            old_text = text
            text = re.sub(pattern_if, replace_if, text, flags=re.DOTALL)
            if text != old_text:
                made_change = True

            # 2. Handle {{#unless VAR}}...{{/unless}}
            def replace_unless(m: re.Match, _var: str = var) -> str:
                block_content = m.group(1)
                is_true = variables.get(_var, "true") == "true"
                if is_true:
                    return ""
                stripped = block_content.strip("\n")
                if m.group(0).endswith("\n") and stripped:
                    return stripped + "\n"
                return stripped

            _unless_body = r"(?:(?!\{\{/unless\}\}|\{\{/if\}\}|\{\{else\}\}|\{\{#if |\{\{#unless ).)*?"
            pattern_unless = rf"\{{{{#unless {var_pattern}\}}}}\n?({_unless_body})\{{{{/unless\}}}}\n?"
            old_text = text
            text = re.sub(pattern_unless, replace_unless, text, flags=re.DOTALL)
            if text != old_text:
                made_change = True

            # 3. Handle {{#if VAR}}...{{else}}...{{/if}} (if-else-endif)
            def replace_if_else(m: re.Match, _var: str = var) -> str:
                true_branch = m.group(1)
                false_branch = m.group(2)
                is_true = variables.get(_var, "true") == "true"
                result = true_branch if is_true else false_branch
                # Preserve trailing newline if original match ended with one
                if m.group(0).endswith("\n"):
                    if not result.endswith("\n"):
                        result = result + "\n"
                return result

            # Guard: prevent if-else from matching past {{/if}} into
            # other blocks (e.g. DOD simple-if capturing orchestrator's {{else}}).
            # Both branches refuse to cross nested opening markers so if-else
            # blocks also resolve inner-to-outer (order-independent, see above).
            _ife_body = r"(?:(?!\{\{/if\}\}|\{\{else\}\}|\{\{#if |\{\{#unless ).)*?"
            pattern_ife = rf"\{{{{#if {var_pattern}\}}}}\n?({_ife_body})\{{{{else\}}}}\n?({_ife_body})\{{{{/if\}}}}\n?"
            old_text = text
            text = re.sub(pattern_ife, replace_if_else, text, flags=re.DOTALL)
            if text != old_text:
                made_change = True

        if not made_change:
            break

    # Final cleanup: remove any remaining orphaned template markers
    # (e.g. from nested {{#unless A}}{{#unless B}}...{{/unless}}{{/unless}})
    text = re.sub(r'\{\{#if\s+\w+\}\}', '', text)
    text = re.sub(r'\{\{/if\}\}', '', text)
    text = re.sub(r'\{\{else\}\}', '', text)
    text = re.sub(r'\{\{#unless\s+\w+\}\}', '', text)
    text = re.sub(r'\{\{/unless\}\}', '', text)

    return text


def substitute(text: str, variables: dict, source_label: str, log: SyncLog) -> str:
    """Replace {{VAR}} occurrences. Warn for missing variables.

    Escape syntax: {{%VAR%}} renders as {{VAR}} without substitution (for literal docs).
    """
    # First pass: protect escaped literals {{%VAR%}} with unique sentinel
    _SENTINEL = "\x00ESC\x00"
    escaped: list[str] = []

    def stash_escape(m):
        escaped.append(m.group(1))
        return f"{_SENTINEL}{len(escaped) - 1}{_SENTINEL}"

    text = re.sub(r"\{\{%([A-Z0-9_]+)%\}\}", stash_escape, text)

    # Second pass: substitute real {{VAR}} placeholders
    def replacer(match):
        key = match.group(1)
        # PAL_* placeholders are handled by the delegation syntax engine,
        # not by general substitution — skip silently.
        if key.startswith("PAL_"):
            return match.group(0)
        if key in variables:
            return str(variables[key])
        log.warn(f"Variable {key} not in config — placeholder remains in: {source_label}")
        return match.group(0)

    text = re.sub(r"\{\{([A-Z0-9_]+)\}\}", replacer, text)

    # Third pass: restore escaped literals as {{VAR}} (no substitution happened)
    for i, name in enumerate(escaped):
        text = text.replace(f"{_SENTINEL}{i}{_SENTINEL}", f"{{{{{name}}}}}")

    return text



