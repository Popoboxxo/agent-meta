"""Config loading, validation, variable building and substitution."""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from .io import _load_yaml_or_json, _write_yaml
from .log import SyncLog

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
    except Exception:
        pass  # schema validation is best-effort


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
    except Exception:
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
    except Exception:
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
    # DOD_*: resolve from dod-preset (base) + dod (overrides).
    # Precedence: dod (project override) > dod-preset > "full" (implicit default).
    dod_resolved = resolve_dod(config, agent_meta_root)
    variables["DOD_REQ_TRACEABILITY"] = "true" if dod_resolved.get("req-traceability", True) else "false"
    variables["DOD_TESTS_REQUIRED"]   = "true" if dod_resolved.get("tests-required", True) else "false"
    variables["DOD_CODEBASE_OVERVIEW"] = "true" if dod_resolved.get("codebase-overview", True) else "false"
    variables["DOD_SECURITY_AUDIT"]   = "true" if dod_resolved.get("security-audit", False) else "false"
    variables["DOD_PRESET"]           = config.get("dod-preset", "full")
    return variables, unmapped


def strip_inactive_dod_blocks(text: str, variables: dict) -> str:
    """Remove DoD-conditional blocks that are inactive in this project.

    Recognizes the pattern:
        {{#if DOD_X}}
        ...content...
        {{/if}}

    If the corresponding DOD_X variable is "false", the entire block (including
    markers) is removed. If "true", the markers are stripped but content kept.
    This keeps generated agent files lean when DoD features are disabled.
    """
    dod_vars = {k for k in variables if k.startswith("DOD_") and k != "DOD_PRESET"}

    def replace_block(m: re.Match) -> str:
        var_name = m.group(1)
        block_content = m.group(2)
        if variables.get(var_name, "true") == "false":
            return ""
        return block_content.strip("\n") + "\n"

    for var in dod_vars:
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
