"""Config loading, validation, variable building and substitution."""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .io import _write_yaml, _yaml, _YAML_AVAILABLE
from .log import SyncLog

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
        with config_path.open(encoding="utf-8") as f:
            config = _yaml.safe_load(f) or {}
    else:
        with config_path.open(encoding="utf-8") as f:
            config = json.load(f)

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
    except (ImportError, TypeError, ValueError):
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


def build_variables(config: dict, agent_meta_root: Path) -> tuple[dict, list[str]]:
    """Returns (variables_dict, pre_warnings)."""
    # Import here to avoid circular deps — agents module uses config module
    from .agents import build_agent_hints, build_agent_table
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
    variables.update(config.get("variables", {}))
    # AI_PROVIDER: auto-inject from top-level config field (not nested in variables)
    if "AI_PROVIDER" not in variables:
        provider_config = load_providers_config(agent_meta_root)
        variables["AI_PROVIDER"] = config.get("ai-provider", "") or ", ".join(
            resolve_providers(config, provider_config)
        )
    # MAX_PARALLEL_AGENTS: auto-inject from top-level config field (default: 2)
    variables["MAX_PARALLEL_AGENTS"] = str(config.get("max-parallel-agents", 2))
    # WORKSPACE_REPOS: auto-inject for multi-repo workspace support
    workspace_repos = config.get("variables", {}).get("WORKSPACE_REPOS", "")
    if workspace_repos:
        variables["WORKSPACE_REPOS"] = workspace_repos
    # SUB_PROJECTS: auto-inject for meta-repo coordination
    sub_projects = config.get("variables", {}).get("SUB_PROJECTS", "")
    if sub_projects:
        variables["SUB_PROJECTS"] = sub_projects
    # META_REPO: auto-inject from top-level config field (default: false)
    # When true, activates cross-plugin standardization and centralized docs
    meta_repo = config.get("meta-repo", False)
    if meta_repo:
        variables["META_REPO"] = "true"
    # DOD_*: resolve from dod-preset (base) + dod (overrides).
    # Precedence: dod (project override) > dod-preset > "full" (implicit default).
    dod_resolved = resolve_dod(config, agent_meta_root)
    variables["DOD_REQ_TRACEABILITY"] = "true" if dod_resolved.get("req-traceability", True) else "false"
    variables["DOD_TESTS_REQUIRED"]   = "true" if dod_resolved.get("tests-required", True) else "false"
    variables["DOD_CODEBASE_OVERVIEW"] = "true" if dod_resolved.get("codebase-overview", True) else "false"
    variables["DOD_SECURITY_AUDIT"]   = "true" if dod_resolved.get("security-audit", False) else "false"
    variables["DOD_PRESET"]           = config.get("dod-preset", "full")
    # CI_POLL_*: CI/CD status polling after push (opt-in, default disabled)
    user_vars = config.get("variables", {})
    variables["CI_POLL_ENABLED"]    = user_vars.get("CI_POLL_ENABLED", "false")
    variables["CI_POLL_INTERVAL"]   = user_vars.get("CI_POLL_INTERVAL", "30")
    variables["CI_POLL_MAX_RETRIES"] = user_vars.get("CI_POLL_MAX_RETRIES", "10")
    # EVALUATOR_OPTIMIZER_*: Generator-Evaluator quality loops
    eo_config = config.get("evaluator-optimizer", {})
    variables["EVALUATOR_OPTIMIZER_ENABLED"] = "true" if eo_config.get("enabled", False) else "false"
    variables["EVALUATOR_OPTIMIZER_AUTO_APPROVE"] = "true" if eo_config.get("auto_approve", False) else "false"
    pairs = eo_config.get("pairs", [])
    variables["EVALUATOR_OPTIMIZER_PAIR_COUNT"] = str(len(pairs))
    for i, pair in enumerate(pairs):
        for key in ["generator", "evaluator", "max_iterations", "modes", "criteria"]:
            val = pair.get(key, "")
            if isinstance(val, list):
                val = ",".join(str(v) for v in val)
            variables[f"EVALUATOR_OPTIMIZER_PAIR_{i}_{key.upper()}"] = str(val)
    # EVALUATOR_CRITERIA_TABLE: central criteria definitions from config/evaluator-criteria.yaml
    variables["EVALUATOR_CRITERIA_TABLE"] = _build_criteria_table(agent_meta_root)
    # OUTPUT_SCHEMA_*: inject structured output schemas for each agent
    _inject_output_schema_variables(variables, config, agent_meta_root)
    return variables, unmapped


def _build_criteria_table(agent_meta_root: Path) -> str:
    """Build markdown table from config/evaluator-criteria.yaml."""
    criteria_path = agent_meta_root / "config" / "evaluator-criteria.yaml"
    if not criteria_path.is_file():
        return "| (no criteria defined) | |"
    try:
        raw = _yaml.safe_load(criteria_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return "| (error loading criteria) | |"
    lines = ["| Kriterium | Was prüfen? |", "|-----------|-------------|"]
    for name, desc in raw.items():
        lines.append(f"| `{name}` | {desc} |")
    return "\n".join(lines)


def _load_role_defaults(agent_meta_root: Path) -> dict:
    """Load role-defaults.yaml and return the roles dict, or empty dict on failure."""
    defaults_path = agent_meta_root / "config" / "role-defaults.yaml"
    if not defaults_path.is_file():
        return {}
    try:
        raw = _yaml.safe_load(defaults_path.read_text(encoding="utf-8")) or {}
        return raw.get("roles", {})
    except Exception:
        return {}


def _generate_example_from_schema(schema: dict) -> dict:
    """Generate a plausible example JSON object from a JSON schema."""
    props = schema.get("properties", {})
    # Merge base schema properties if allOf is used
    for clause in schema.get("allOf", []):
        if "$ref" in clause:
            # $ref handled by caller - base props already merged in
            continue
        if "properties" in clause:
            for k, v in clause["properties"].items():
                if k not in props:
                    props[k] = v
    example = {}
    for key, prop in props.items():
        if key in ("status",):
            example[key] = "success"
        elif key in ("message",):
            example[key] = "Task completed successfully."
        elif key in ("warnings", "errors"):
            example[key] = []
        elif prop.get("type") == "string":
            if "enum" in prop:
                example[key] = prop["enum"][0]
            else:
                example[key] = f"<{key}>"
        elif prop.get("type") == "integer":
            example[key] = 0
        elif prop.get("type") == "number":
            example[key] = 0.0
        elif prop.get("type") == "boolean":
            example[key] = False
        elif prop.get("type") == "array":
            items = prop.get("items", {})
            if isinstance(items, dict) and items.get("type") == "object":
                inner_props = items.get("properties", {})
                inner_example = {}
                for ik, ip in inner_props.items():
                    if ip.get("type") == "string":
                        inner_example[ik] = ip.get("enum", ["<value>"])[0] if "enum" in ip else f"<{ik}>"
                    elif ip.get("type") == "integer":
                        inner_example[ik] = 0
                    elif ip.get("type") == "number":
                        inner_example[ik] = 0.0
                    elif ip.get("type") == "boolean":
                        inner_example[ik] = False
                    else:
                        inner_example[ik] = f"<{ik}>"
                example[key] = [inner_example]
            elif isinstance(items, dict) and items.get("type") == "string":
                example[key] = ["<value>"]
            else:
                example[key] = []
        elif prop.get("type") == "object":
            example[key] = {}
    return example


def _inject_output_schema_variables(variables: dict, config: dict, agent_meta_root: Path) -> None:
    """Inject OUTPUT_SCHEMA_<CLUSTER> variables from role-defaults.yaml output_schema entries.

    Groups roles by their output_schema path (cluster schemas), deduplicates,
    and injects one variable per unique schema. Variable name is derived from
    the schema file stem (e.g. execution-result → OUTPUT_SCHEMA_EXECUTION_RESULT).
    Also injects per-role variables for backward compatibility.
    Sets HAS_OUTPUT_SCHEMAS to "true" if any schemas were loaded.
    """
    roles = _load_role_defaults(agent_meta_root)
    schemas_dir = agent_meta_root / "config" / "output-schemas"
    has_any = False
    processed_schemas: dict[str, str] = {}  # schema_stem → role_var_name

    for role_name, role_def in roles.items():
        schema_rel = role_def.get("output_schema", "")
        if not schema_rel:
            continue
        schema_path = agent_meta_root / schema_rel
        if not schema_path.is_file():
            continue
        schema_stem = schema_path.name.replace(".schema.json", "")  # "execution-result"

        # Skip if already processed this cluster schema
        if schema_stem in processed_schemas:
            # Still inject per-role alias for backward compat
            role_var = role_name.upper().replace("-", "_")
            cluster_var = processed_schemas[schema_stem]
            variables[f"OUTPUT_SCHEMA_{role_var}"] = variables[f"OUTPUT_SCHEMA_{cluster_var}"]
            variables[f"OUTPUT_SCHEMA_{role_var}_EXAMPLE"] = variables[f"OUTPUT_SCHEMA_{cluster_var}_EXAMPLE"]
            continue

        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        # Merge base schema properties if allOf is used
        merged_props = dict(schema.get("properties", {}))
        for clause in schema.get("allOf", []):
            ref = clause.get("$ref", "")
            if ref:
                ref_path = schemas_dir / ref
                if ref_path.is_file():
                    try:
                        base = json.loads(ref_path.read_text(encoding="utf-8"))
                        for k, v in base.get("properties", {}).items():
                            if k not in merged_props:
                                merged_props[k] = v
                    except (json.JSONDecodeError, OSError):
                        pass

        # Derive variable name from schema stem (cluster name)
        cluster_var = schema_stem.upper().replace("-", "_")
        display_schema = {
            "title": schema.get("title", f"{cluster_var} Output"),
            "description": schema.get("description", ""),
            "required": schema.get("required", []),
            "properties": merged_props,
        }
        variables[f"OUTPUT_SCHEMA_{cluster_var}"] = json.dumps(display_schema, indent=2, ensure_ascii=False)

        # Generate example
        example = _generate_example_from_schema(schema)
        variables[f"OUTPUT_SCHEMA_{cluster_var}_EXAMPLE"] = json.dumps(example, indent=2, ensure_ascii=False)

        # Also inject per-role aliases for backward compatibility
        role_var = role_name.upper().replace("-", "_")
        variables[f"OUTPUT_SCHEMA_{role_var}"] = variables[f"OUTPUT_SCHEMA_{cluster_var}"]
        variables[f"OUTPUT_SCHEMA_{role_var}_EXAMPLE"] = variables[f"OUTPUT_SCHEMA_{cluster_var}_EXAMPLE"]

        processed_schemas[schema_stem] = cluster_var
        has_any = True

    variables["HAS_OUTPUT_SCHEMAS"] = "true" if has_any else "false"


def strip_inactive_dod_blocks(text: str, variables: dict, extra_vars: list[str] | None = None) -> str:
    """Remove conditional blocks that are inactive in this project.

    Recognizes two patterns:
        {{#if VAR}}
        ...content...
        {{/if}}

        {{^VAR}}
        ...content...
        {{/if}}

    For {{#if VAR}}: if VAR is "false" or empty/missing, the entire block is removed.
    For {{^VAR}} (inverse): if VAR is "true", the entire block is removed.

    By default handles DOD_* variables. Pass extra_vars to handle additional
    conditional variables (e.g. CI_POLL_ENABLED, OUTPUT_SCHEMA_*).

    For DOD_* variables: missing = "true" (show block by default).
    For OUTPUT_SCHEMA_* and other extra_vars: missing = "false" (hide block by default).
    """
    dod_vars = {k for k in variables if k.startswith("DOD_") and k != "DOD_PRESET"}
    extra_vars_set = set(extra_vars) if extra_vars else set()
    all_vars = dod_vars | extra_vars_set

    for var in all_vars:
        # Determine default value based on variable type
        is_extra = var in extra_vars_set
        default_when_missing = "false" if is_extra else "true"

        # --- Inverse blocks: {{^VAR}}...{{/if}} ---
        # Shown when VAR is "false", removed when VAR is "true"
        def replace_inverse(m: re.Match, _var: str = var, _def: str = default_when_missing) -> str:
            block_content = m.group(1)
            val = variables.get(_var, _def)
            if val == "true":
                return ""
            return block_content.strip("\n") + "\n"

        inverse_pattern = rf"\{{{{\^{re.escape(var)}\}}}}\n?(.*?)\{{{{/if\}}}}\n?"
        text = re.sub(inverse_pattern, replace_inverse, text, flags=re.DOTALL)

        # --- Standard blocks: {{#if VAR}}...{{/if}} ---
        def replace_block(m: re.Match, _var: str = var, _def: str = default_when_missing) -> str:
            block_content = m.group(1)
            val = variables.get(_var, _def)
            if val in ("false", ""):
                return ""
            return block_content.strip("\n") + "\n"

        pattern = rf"\{{{{#if {re.escape(var)}\}}}}\n?(.*?)\{{{{/if\}}}}\n?"
        text = re.sub(pattern, replace_block, text, flags=re.DOTALL)

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
        if key in variables:
            return variables[key]
        log.warn(f"Variable {key} not in config — placeholder remains in: {source_label}")
        return match.group(0)

    text = re.sub(r"\{\{([A-Z0-9_]+)\}\}", replacer, text)

    # Third pass: restore escaped literals as {{VAR}} (no substitution happened)
    for i, name in enumerate(escaped):
        text = text.replace(f"{_SENTINEL}{i}{_SENTINEL}", f"{{{{{name}}}}}")

    return text
