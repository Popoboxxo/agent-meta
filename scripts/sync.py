#!/usr/bin/env python3
"""
agent-meta sync.py
==================
Generates .claude/agents/*.md for a project from agent-meta sources.
Manages .claude/3-project/<prefix>-<role>-ext.md extension files.
Syncs snippets, rules, hooks and external skill agents.

Usage:
  python .agent-meta/scripts/sync.py --config agent-meta.config.json
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --init
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --only-variables
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext <role>
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --update-ext
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --create-rule <name>
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --create-hook <name>
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --dry-run
  python .agent-meta/scripts/sync.py --add-skill <repo-url> --skill-name <name>
                                      --source <path> --role <role> [--entry <file>]

External skills (external-skills.config.json):
  - Managed centrally in agent-meta (Modell A)
  - Each enabled skill generates a wrapper agent in .claude/agents/<role>.md
  - Skill files are copied to .claude/skills/<skill-name>/
  - Use --add-skill to register a new submodule + skill entry
  - Use enabled: true/false in external-skills.config.json to activate/deactivate
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AGENTS_DIR = "agents"
GENERIC_DIR = "1-generic"
PLATFORM_DIR = "2-platform"
PROJECT_DIR = "3-project"
SNIPPETS_DIR = "snippets"
EXTERNAL_DIR = "0-external"
SKILL_WRAPPER = "_skill-wrapper.md"
EXTERNAL_SKILLS_CONFIG = "external-skills.config.json"
CLAUDE_AGENTS_DIR = ".claude/agents"
CLAUDE_EXT_DIR = ".claude/3-project"
CLAUDE_SNIPPETS_DIR = ".claude/snippets"
CLAUDE_SKILLS_DIR = ".claude/skills"
CLAUDE_RULES_DIR = ".claude/rules"
RULES_DIR = "rules"
CLAUDE_HOOKS_DIR = ".claude/hooks"
HOOKS_DIR = "hooks"
LOGFILE = "sync.log"

# Maps role name to the output filename in .claude/agents/ (no prefix)
ROLE_MAP = {
    "orchestrator":  "orchestrator",
    "developer":     "developer",
    "tester":        "tester",
    "validator":     "validator",
    "requirements":  "requirements",
    "ideation":      "ideation",
    "documenter":    "documenter",
    "release":       "release",
    "docker":        "docker",
    "meta-feedback":       "meta-feedback",
    "git":                 "git",
    "agent-meta-manager":  "agent-meta-manager",
    "feature":             "feature",
    "agent-meta-scout":    "agent-meta-scout",
    "security-auditor":    "security-auditor",
    "openscad-developer":  "openscad-developer",
}

EXT_SUFFIX = "-ext"
ROLES_CONFIG = "roles.config.json"
MANAGED_BEGIN = "<!-- agent-meta:managed-begin -->"
MANAGED_END   = "<!-- agent-meta:managed-end -->"


# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------

PROVIDER_CONFIG = {
    "Claude": {
        "agents_dir":        ".claude/agents",
        "agent_ext":         ".md",
        "context_file":      "CLAUDE.md",
        "context_template":  "howto/CLAUDE.project-template.md",
        "has_rules":         True,
        "has_hooks":         True,
        "has_settings":      True,
        "settings_file":     ".claude/settings.json",
    },
    "Gemini": {
        "agents_dir":        ".gemini/agents",
        "agent_ext":         ".md",
        "context_file":      ".gemini/GEMINI.md",
        "context_template":  "howto/GEMINI.project-template.md",
        "has_rules":         False,
        "has_hooks":         False,
        "has_settings":      True,
        "settings_file":     ".gemini/settings.json",
    },
    "Continue": {
        "agents_dir":        ".continue/agents",
        "agent_ext":         ".md",
        "context_file":      ".continue/rules/project-context.md",
        "context_template":  "howto/CONTINUE.project-template.md",
        "has_rules":         False,
        "has_hooks":         False,
        "has_settings":      True,
        "settings_file":     ".continue/config.yaml",
        "settings_template": "howto/CONTINUE.config-template.yaml",
    },
}

# Managed block content template — uses {{PLATZHALTER}} from config variables
# This is what gets updated on --update-ext. Keep it concise and useful.
MANAGED_BLOCK_TEMPLATE = """\
<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on --update-ext. -->
<!-- Project-specific additions belong in the section BELOW this marker. -->

**Projekt:** {{PROJECT_NAME}} | **Plattform:** {{PLATFORM}} | **Runtime:** {{RUNTIME}}
**Build:** `{{BUILD_COMMAND}}` | **Test:** `{{TEST_COMMAND}}`
<!-- agent-meta:managed-end -->"""

PROJECT_SECTION_STUB = """\

---

## Projektspezifische Erweiterungen

<!-- This section is NEVER modified by sync.py. -->
<!-- Add project-specific knowledge, rules, and patterns here. -->
"""


# ---------------------------------------------------------------------------
# Log collector
# ---------------------------------------------------------------------------

class SyncLog:
    def __init__(self):
        self.actions: list[str] = []
        self.warnings: list[str] = []
        self.skipped: list[str] = []
        self.infos: list[str] = []
        self.start_time = datetime.now()

    def action(self, tag: str, target: str, source: str):
        self.actions.append(f"[{tag:<8}]  {target:<50}  ({source})")

    def warn(self, message: str):
        self.warnings.append(f"[WARN]   {message}")
        print(f"  !  {message}", file=sys.stderr)

    def skip(self, target: str, reason: str):
        self.skipped.append(f"[SKIP]   {target:<50}  ({reason})")

    def info(self, target: str, reason: str):
        self.infos.append(f"[INFO]   {target:<50}  ({reason})")


    def provider_header(self, provider: str):
        self.infos.append("")
        self.infos.append(f"[PROVIDER] {provider}")
        self.infos.append(f"{'~' * (len(provider) + 11)}")

    def write(self, log_path: Path, config_path: str, source_version: str,
              mode: str, platforms: list[str], dry_run: bool,
              providers: list[str] | None = None,
              speech_mode: str = "full"):
        lines = [
            "=" * 60,
            f"agent-meta sync — {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            f"Config:    {config_path}",
            f"Source:    .agent-meta/ (v{source_version})",
            f"Mode:      {'DRY-RUN — ' if dry_run else ''}{mode}",
            f"Platforms: {', '.join(platforms) if platforms else '(none)'}",
            f"Providers: {', '.join(providers) if providers else '(none)'}",
            f"Speech:    {speech_mode}",
            "",
            "ACTIONS",
            "-------",
        ]
        lines += self.actions
        if self.skipped:
            lines += ["", "SKIPPED", "-------"]
            lines += self.skipped
        if self.infos:
            lines += ["", "INFO", "----"]
            lines += self.infos

        if self.warnings:
            lines += ["", "WARNINGS", "--------"]
            lines += self.warnings
        else:
            lines += ["", "WARNINGS", "--------", "(none)"]

        lines += [
            "",
            "SUMMARY",
            "-------",
            f"{len(self.actions)} action(s)  |  {len(self.skipped)} skipped  |  {len(self.warnings)} warning(s)",
            f"Logfile: {log_path}",
        ]

        content = "\n".join(lines) + "\n"
        if not dry_run:
            log_path.write_text(content, encoding="utf-8")
        print()
        print(content)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
        sys.exit(1)
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

    schema_path = Path(__file__).resolve().parent.parent / "agent-meta.schema.json"
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
    return script_path.parent.parent


# ---------------------------------------------------------------------------
# fill_defaults — write missing config fields with their schema defaults
# ---------------------------------------------------------------------------

# Top-level fields with a meaningful default value.
# dod sub-fields are handled separately via DOD_DEFAULTS.
_CONFIG_FIELD_DEFAULTS: dict = {
    "dod-preset": "full",
    "max-parallel-agents": 2,
    "speech-mode": "full",
}

# dod sub-fields with defaults (mirrors DOD_DEFAULTS defined later in the file)
_DOD_FIELD_DEFAULTS: dict = {
    "req-traceability": True,
    "tests-required": True,
    "codebase-overview": True,
    "security-audit": False,
}


def _load_schema_variable_keys(agent_meta_root: Path) -> list[str]:
    """Return the list of known variable keys from agent-meta.schema.json."""
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
    log: "SyncLog",
    dry_run: bool,
) -> None:
    """Write missing config fields with their default values into agent-meta.config.json.

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

    # --- Write back if changed ---
    if changed and not dry_run:
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


def build_agent_hints(config: dict, agent_meta_root: Path) -> str:
    """Generate agent usage hints for {{AGENT_HINTS}}.

    Reads hint (preferred) or description from each active agent's template frontmatter.
    If orchestrator is active, adds a prominent start hint.
    """
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    lines = []
    has_orchestrator = (
        "orchestrator" in overrides
        and (allowed_roles is None or "orchestrator" in allowed_roles)
    )
    if has_orchestrator:
        lines.append(
            "> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben."
        )
        lines.append("")

    lines.append("| Agent | Zuständigkeit |")
    lines.append("|-------|--------------|")
    for role, source_path in sorted(overrides.items()):
        if allowed_roles is not None and role not in allowed_roles:
            continue
        if not target_filename(role):
            continue
        content = source_path.read_text(encoding="utf-8")
        hint = extract_frontmatter_field(content, "hint") \
            or extract_frontmatter_field(content, "description") \
            or ""
        lines.append(f"| `{role}` | {hint} |")

    return "\n".join(lines)


def build_agent_table(config: dict, agent_meta_root: Path) -> tuple[str, list[str]]:
    """Generate markdown table for {{AGENT_TABLE}}. Returns (table, unmapped_warnings).

    Only includes roles present in config['roles'] whitelist (if set).
    """
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    rows = []
    unmapped = []
    for role, source_path in sorted(overrides.items()):
        if allowed_roles is not None and role not in allowed_roles:
            continue
        filename = target_filename(role)
        if not filename:
            unmapped.append(
                f"Role '{role}' ({source_path.name}) not in ROLE_MAP — skipped in AGENT_TABLE"
            )
            continue
        agent_name = Path(filename).stem
        layer = source_path.parts[-2]
        rows.append(f"| `{agent_name}` | `{source_path.name}` | {layer} |")

    header = "| Agent | Quelle | Layer |\n|-------|--------|-------|"
    return header + "\n" + "\n".join(rows), unmapped


def build_variables(config: dict, agent_meta_root: Path) -> tuple[dict, list[str]]:
    """Returns (variables_dict, pre_warnings)."""
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
        variables["AI_PROVIDER"] = config.get("ai-provider", "") or ", ".join(resolve_providers(config))
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


def substitute(text: str, variables: dict, source_label: str, log: SyncLog) -> str:
    """Replace {{VAR}} occurrences. Warn for missing variables.

    Escape syntax: {{%VAR%}} renders as {{VAR}} without substitution (for literal docs).
    """
    # First pass: resolve escaped literals {{% ... %}} → {{...}} (no substitution)
    text = re.sub(r"\{\{%([A-Z0-9_]+)%\}\}", r"{{\1}}", text)

    def replacer(match):
        key = match.group(1)
        if key in variables:
            return variables[key]
        log.warn(f"Variable {key} not in config — placeholder remains in: {source_label}")
        return match.group(0)
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", replacer, text)


def extract_frontmatter_field(content: str, field: str) -> str | None:
    """Extract a single-line YAML frontmatter field value (unquoted or quoted)."""
    match = re.search(
        rf'^{re.escape(field)}:\s*"?([^"\n]+)"?\s*$',
        content, flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def build_frontmatter(content: str, name: str, description: str,
                      generated_from: str | None = None) -> str:
    """Replace name and description in YAML frontmatter.

    Preserves existing version/based-on fields.
    Inserts/updates generated-from when generated_from is provided.
    """
    content = re.sub(
        r"(^---\n.*?^name:\s*)(.+?)(\n)",
        lambda m: f"{m.group(1)}{name}{m.group(3)}",
        content, count=1, flags=re.MULTILINE | re.DOTALL,
    )
    content = re.sub(
        r"(^description:\s*\")(.+?)(\"\n)",
        lambda m: f'{m.group(1)}{description}{m.group(3)}',
        content, count=1, flags=re.MULTILINE,
    )
    if generated_from is not None:
        # Update existing generated-from field, or insert after description line
        if re.search(r"^generated-from:", content, flags=re.MULTILINE):
            content = re.sub(
                r'^generated-from:.*$',
                f'generated-from: "{generated_from}"',
                content, count=1, flags=re.MULTILINE,
            )
        else:
            content = re.sub(
                r'(^description:.*\n)',
                rf'\1generated-from: "{generated_from}"\n',
                content, count=1, flags=re.MULTILINE,
            )
    return content


DOD_PRESETS_CONFIG = "dod-presets.config.json"

# Default DoD values (= "full" preset) — used as ultimate fallback
DOD_DEFAULTS = {
    "req-traceability": True,
    "tests-required": True,
    "codebase-overview": True,
    "security-audit": False,
}


def load_dod_presets(agent_meta_root: Path) -> dict:
    """Load dod-presets.config.json from agent-meta root. Returns empty dict if not found."""
    config_path = agent_meta_root / DOD_PRESETS_CONFIG
    if not config_path.exists():
        return {}
    with config_path.open(encoding="utf-8") as f:
        data = json.load(f)
    presets = data.get("presets", {})
    # Strip comments
    return {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
            for k, v in presets.items() if not k.startswith("_")}


def resolve_dod(config: dict, agent_meta_root: Path) -> dict:
    """Resolve effective DoD values from preset + overrides.

    Precedence (highest to lowest):
    1. Project override:  config["dod"][key]
    2. Preset default:    dod-presets.config.json[preset][key]
    3. Global default:    DOD_DEFAULTS[key]
    """
    presets = load_dod_presets(agent_meta_root)
    preset_name = config.get("dod-preset", "full")
    preset_values = presets.get(preset_name, {})
    if preset_name not in presets and preset_name != "full":
        print(f"  !  Unknown dod-preset '{preset_name}' — falling back to 'full'",
              file=sys.stderr)
    dod_overrides = config.get("dod", {})

    resolved = {}
    for key, default_val in DOD_DEFAULTS.items():
        if key in dod_overrides:
            resolved[key] = dod_overrides[key]
        elif key in preset_values:
            resolved[key] = preset_values[key]
        else:
            resolved[key] = default_val
    return resolved



def resolve_provider_options(config: dict, provider: str) -> dict:
    """Return provider-specific options from config["provider-options"][provider].

    Falls back to empty dict — all options are optional.

    Example config:
        "provider-options": {
            "Continue": {
                "generate-prompts": true,
                "prompt-mode": "full"   # "full" | "slim"
            }
        }
    """
    return config.get("provider-options", {}).get(provider, {})


def resolve_providers(config: dict) -> list:
    """Resolve active AI providers from config.

    Supports:
    - "ai-providers": ["Claude", "Gemini"]  (new multi-provider)
    - "ai-provider":  "Claude"               (legacy, backward-compat)

    Falls back to ["Claude"] if neither key is set.
    """
    if "ai-providers" in config:
        providers = config["ai-providers"]
        if isinstance(providers, list):
            return [p for p in providers if p in PROVIDER_CONFIG]
        if isinstance(providers, str) and providers in PROVIDER_CONFIG:
            return [providers]
    if "ai-provider" in config:
        p = config["ai-provider"]
        if isinstance(p, str) and p in PROVIDER_CONFIG:
            return [p]
    return ["Claude"]


def load_roles_config(agent_meta_root: Path) -> dict:
    """Load roles.config.json from agent-meta root. Returns empty structure if not found."""
    config_path = agent_meta_root / ROLES_CONFIG
    if not config_path.exists():
        return {"roles": {}}
    with config_path.open(encoding="utf-8") as f:
        data = json.load(f)
    return {"roles": {k: v for k, v in data.get("roles", {}).items() if not k.startswith("_")}}


def resolve_model(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the model for a role.

    Precedence (highest to lowest):
    1. Project override: project_config["model-overrides"][role]
    2. Meta default:     roles.config.json roles[role].model
    3. Empty string:     no model: field injected (agent inherits from parent)
    """
    project_overrides = project_config.get("model-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return roles_cfg["roles"].get(role, {}).get("model", "")


def resolve_permission_mode(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the permissionMode for a role.

    Precedence (highest to lowest):
    1. Project override: project_config["permission-mode-overrides"][role]
    2. Meta default:     roles.config.json roles[role].permission_mode
    3. Empty string:     no permissionMode: field injected
    """
    project_overrides = project_config.get("permission-mode-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return roles_cfg["roles"].get(role, {}).get("permission_mode", "")


def resolve_memory(role: str, project_config: dict, agent_meta_root: Path) -> str:
    """Resolve the memory scope for a role.

    Precedence (highest to lowest):
    1. Project override: project_config["memory-overrides"][role]
    2. Meta default:     roles.config.json roles[role].memory
    3. Empty string:     no memory: field injected
    """
    project_overrides = project_config.get("memory-overrides", {})
    if role in project_overrides:
        return str(project_overrides[role])
    roles_cfg = load_roles_config(agent_meta_root)
    return roles_cfg["roles"].get(role, {}).get("memory", "")


def inject_permission_mode_field(content: str, permission_mode: str) -> str:
    """Insert or update the permissionMode: field in YAML frontmatter.

    If permission_mode is empty, removes any existing permissionMode: field.
    If set, inserts/updates after the memory: line (or model: or name: as fallback).
    """
    if not permission_mode:
        content = re.sub(r"^permissionMode:.*\n", "", content, count=1, flags=re.MULTILINE)
        return content

    if re.search(r"^permissionMode:", content, flags=re.MULTILINE):
        return re.sub(
            r"^permissionMode:.*$",
            f"permissionMode: {permission_mode}",
            content, count=1, flags=re.MULTILINE,
        )

    # Insert after memory: if present, else after model:, else after name:
    if re.search(r"^memory:", content, flags=re.MULTILINE):
        anchor = r"^memory:.*$"
    elif re.search(r"^model:", content, flags=re.MULTILINE):
        anchor = r"^model:.*$"
    else:
        anchor = r"^name:.*$"

    return re.sub(
        rf"({anchor}\n)",
        rf"\1permissionMode: {permission_mode}\n",
        content, count=1, flags=re.MULTILINE,
    )


def inject_memory_field(content: str, memory: str) -> str:
    """Insert or update the memory: field in YAML frontmatter.

    If memory is empty, removes any existing memory: field.
    If memory is set, inserts/updates after the model: line (or name: if no model:).
    """
    if not memory:
        content = re.sub(r"^memory:.*\n", "", content, count=1, flags=re.MULTILINE)
        return content

    # Update existing memory: field
    if re.search(r"^memory:", content, flags=re.MULTILINE):
        return re.sub(
            r"^memory:.*$",
            f"memory: {memory}",
            content, count=1, flags=re.MULTILINE,
        )

    # Insert after model: if present, else after name:
    anchor = r"^model:.*$" if re.search(r"^model:", content, flags=re.MULTILINE) else r"^name:.*$"
    return re.sub(
        rf"({anchor}\n)",
        rf"\1memory: {memory}\n",
        content, count=1, flags=re.MULTILINE,
    )


def inject_model_field(content: str, model: str) -> str:
    """Insert or update the model: field in YAML frontmatter.

    If model is empty, removes any existing model: field (clean slate).
    If model is set, inserts/updates after the name: line.
    """
    if not model:
        # Remove existing model: field if present
        content = re.sub(r"^model:.*\n", "", content, count=1, flags=re.MULTILINE)
        return content

    # Update existing model: field
    if re.search(r"^model:", content, flags=re.MULTILINE):
        return re.sub(
            r"^model:.*$",
            f"model: {model}",
            content, count=1, flags=re.MULTILINE,
        )

    # Insert after name: line
    return re.sub(
        r"(^name:.*\n)",
        rf"\1model: {model}\n",
        content, count=1, flags=re.MULTILINE,
    )


def target_filename(role: str) -> str | None:
    name = ROLE_MAP.get(role)
    return (name + ".md") if name else None


def ext_target_filename(role: str, prefix: str) -> str:
    """Extension file name: <prefix>-<role>-ext.md (or <role>-ext.md if no prefix)."""
    if prefix:
        return f"{prefix}-{role}{EXT_SUFFIX}.md"
    return f"{role}{EXT_SUFFIX}.md"


def role_from_platform_file(filename: str, platforms: list[str]) -> str | None:
    stem = Path(filename).stem
    for platform in platforms:
        if stem.startswith(f"{platform}-"):
            return stem[len(platform) + 1:]
    return None


# ---------------------------------------------------------------------------
# Managed block helpers
# ---------------------------------------------------------------------------

def render_managed_block(variables: dict, source_label: str, log: SyncLog) -> str:
    """Render the managed block content from config variables."""
    content = substitute(MANAGED_BLOCK_TEMPLATE, variables, source_label, log)
    return content


def update_managed_block(existing: str, new_managed: str) -> str:
    """Replace the managed block in an existing extension file."""
    pattern = re.compile(
        r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
        re.DOTALL,
    )
    if pattern.search(existing):
        return pattern.sub(new_managed, existing, count=1)
    # No block found — prepend (should not happen in normal flow)
    return new_managed + "\n\n" + existing


# ---------------------------------------------------------------------------
# Composition engine (extends: / patches: system)
# ---------------------------------------------------------------------------

def _split_frontmatter(content: str) -> tuple[str, str]:
    """Split content into (frontmatter_block, body).

    Returns ('', content) if no frontmatter found.
    frontmatter_block includes the surrounding '---' delimiters.
    """
    if not content.startswith("---"):
        return "", content
    end = content.find("\n---", 3)
    if end == -1:
        return "", content
    fm_block = content[: end + 4]   # includes closing ---
    body = content[end + 4:]        # everything after closing ---
    return fm_block, body


def _parse_frontmatter_yaml(content: str) -> dict:
    """Parse YAML frontmatter into a dict. Returns {} on failure or missing yaml."""
    if not _YAML_AVAILABLE:
        return {}
    fm_block, _ = _split_frontmatter(content)
    if not fm_block:
        return {}
    # Strip the --- delimiters for yaml.safe_load
    inner = re.sub(r"^---\n?", "", fm_block)
    inner = re.sub(r"\n?---\s*$", "", inner)
    try:
        result = _yaml.safe_load(inner)
        return result if isinstance(result, dict) else {}
    except Exception:
        return {}


def _find_section_bounds(lines: list[str], anchor: str) -> tuple[int, int] | None:
    """Find (start, end) line indices for a Markdown section.

    anchor must match the heading line exactly (e.g. '## Don\\'ts').
    start is inclusive (the heading line).
    end is exclusive (first line of next section at same or higher level, or len(lines)).
    """
    anchor_stripped = anchor.strip()
    anchor_level = len(anchor_stripped) - len(anchor_stripped.lstrip("#"))

    start_idx = None
    for i, line in enumerate(lines):
        if line.rstrip() == anchor_stripped:
            start_idx = i
            break

    if start_idx is None:
        return None

    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            if level <= anchor_level:
                return (start_idx, i)

    return (start_idx, len(lines))


def _patch_append_after(content: str, anchor: str, patch_content: str,
                        log: SyncLog, source_label: str) -> str:
    """Insert patch_content after the section identified by anchor."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warn(f"Composition patch 'append-after': anchor '{anchor}' not found in {source_label}")
        return content
    _, end_idx = bounds
    # Trim trailing blank lines before the insertion point
    insert_at = end_idx
    patch_lines = ("\n\n" + patch_content.rstrip("\n") + "\n\n").splitlines(keepends=True)
    result_lines = lines[:insert_at] + patch_lines + lines[insert_at:]
    return "".join(result_lines)


def _patch_replace(content: str, anchor: str, patch_content: str,
                   log: SyncLog, source_label: str) -> str:
    """Replace the entire section identified by anchor with patch_content."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warn(f"Composition patch 'replace': anchor '{anchor}' not found in {source_label}")
        return content
    start_idx, end_idx = bounds
    patch_lines = (patch_content.rstrip("\n") + "\n").splitlines(keepends=True)
    result_lines = lines[:start_idx] + patch_lines + lines[end_idx:]
    return "".join(result_lines)


def _patch_delete(content: str, anchor: str, log: SyncLog, source_label: str) -> str:
    """Delete the entire section identified by anchor."""
    lines = content.splitlines(keepends=True)
    bounds = _find_section_bounds(lines, anchor)
    if bounds is None:
        log.warn(f"Composition patch 'delete': anchor '{anchor}' not found in {source_label}")
        return content
    start_idx, end_idx = bounds
    # Also remove leading blank line before section if present
    trim_start = start_idx
    if trim_start > 0 and lines[trim_start - 1].strip() == "":
        trim_start -= 1
    result_lines = lines[:trim_start] + lines[end_idx:]
    return "".join(result_lines)


def apply_patch(content: str, patch: dict, log: SyncLog, source_label: str) -> str:
    """Apply a single composition patch to content."""
    op = patch.get("op", "")
    anchor = patch.get("anchor", "")
    patch_content = patch.get("content", "")

    if op == "append":
        return content.rstrip("\n") + "\n\n" + patch_content.rstrip("\n") + "\n"
    elif op == "append-after":
        return _patch_append_after(content, anchor, patch_content, log, source_label)
    elif op == "replace":
        return _patch_replace(content, anchor, patch_content, log, source_label)
    elif op == "delete":
        return _patch_delete(content, anchor, log, source_label)
    else:
        log.warn(f"Composition: unknown patch op '{op}' in {source_label}")
        return content


def _merge_frontmatter(base_content: str, override_fm: dict) -> str:
    """Replace the frontmatter block in base_content with values from override_fm.

    Fields 'extends' and 'patches' are stripped (composition metadata).
    All other override fields (name, version, description, hint, tools, based-on) win.
    """
    fm_block, body = _split_frontmatter(base_content)
    if not _YAML_AVAILABLE:
        return base_content  # Cannot merge without yaml — return base unchanged

    # Parse base frontmatter
    base_fm = _parse_frontmatter_yaml(base_content)

    # Merge: base first, then override wins
    merged = {**base_fm, **override_fm}

    # Strip composition-only keys from the output frontmatter
    for key in ("extends", "patches"):
        merged.pop(key, None)

    # Serialize back to YAML
    try:
        new_fm_inner = _yaml.dump(merged, allow_unicode=True, default_flow_style=False,
                                  sort_keys=False).rstrip("\n")
    except Exception:
        return base_content

    new_fm_block = f"---\n{new_fm_inner}\n---"
    return new_fm_block + body


def compose_agent(
    base_path: Path,
    override_content: str,
    log: SyncLog,
) -> str:
    """Load base template, apply patches from override frontmatter, merge frontmatter.

    Returns the composed document ready for variable substitution.
    """
    if not _YAML_AVAILABLE:
        log.warn(
            "PyYAML not available — composition skipped. "
            "Install it with: pip install pyyaml"
        )
        return override_content

    if not base_path.exists():
        log.warn(f"Composition: base template not found: {base_path}")
        return override_content

    base_content = base_path.read_text(encoding="utf-8")
    override_fm = _parse_frontmatter_yaml(override_content)
    patches = override_fm.get("patches") or []

    # Start from base, apply each patch
    result = base_content
    source_label = base_path.name
    for patch in patches:
        result = apply_patch(result, patch, log, source_label)

    # Merge frontmatter: override fields win over base fields
    result = _merge_frontmatter(result, override_fm)

    return result


# ---------------------------------------------------------------------------
# Sync logic
# ---------------------------------------------------------------------------

def collect_sources(
    agent_meta_root: Path, platforms: list[str]
) -> tuple[dict[str, Path], set[str]]:
    """
    Returns (overrides, known_ext_roles).

    overrides: role → source_path for generated agents (.claude/agents/)
      Priority: 1-generic < 2-platform < 3-project/<role>.md (full override)

    known_ext_roles: roles that have a 3-project/<role>-ext.md in meta-repo.
      These are NOT used as templates — just signals that the role supports extensions.
      (Currently unused since 3-project/ in meta-repo has no templates by design.)
    """
    overrides: dict[str, Path] = {}
    known_ext_roles: set[str] = set()

    # 1. Generic agents
    generic_dir = agent_meta_root / AGENTS_DIR / GENERIC_DIR
    for f in sorted(generic_dir.glob("*.md")):
        overrides[f.stem] = f

    # 2. Platform agents
    platform_dir = agent_meta_root / AGENTS_DIR / PLATFORM_DIR
    for platform in platforms:
        for f in sorted(platform_dir.glob(f"{platform}-*.md")):
            role = role_from_platform_file(f.name, platforms)
            if role:
                overrides[role] = f

    # 3. Project-level agents (in meta-repo 3-project/)
    project_dir = agent_meta_root / AGENTS_DIR / PROJECT_DIR
    if project_dir.exists():
        for f in sorted(project_dir.glob("*.md")):
            stem = f.stem
            if stem.endswith(EXT_SUFFIX):
                known_ext_roles.add(stem[: -len(EXT_SUFFIX)])
            else:
                overrides[stem] = f

    return overrides, known_ext_roles


def sync_agents(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Generate all .claude/agents/*.md files."""
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / CLAUDE_AGENTS_DIR

    # Optional role whitelist — if "roles" key is absent, all roles are generated
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    # Track which filenames will be written in this sync
    expected_filenames: set[str] = set()

    project_name = config["project"]["name"]
    for role, source_path in overrides.items():
        filename = target_filename(role)
        if not filename:
            log.skip(str(source_path.name), "role not in ROLE_MAP")
            continue

        if allowed_roles is not None and role not in allowed_roles:
            log.skip(str(target_dir / filename).replace(str(project_root) + "/", "").replace(str(project_root) + "\\", ""),
                     f"role '{role}' not in config['roles']")
            continue

        expected_filenames.add(filename)
        target_path = target_dir / filename
        content = source_path.read_text(encoding="utf-8")

        # Composition mode: if 'extends:' present in frontmatter, compose from base
        extends_base = extract_frontmatter_field(content, "extends")
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)
            log.info(
                str(target_path.relative_to(project_root)),
                f"composed from {extends_base} + {source_path.name}",
            )

        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, "version")
        # Preserve template description; interpolate {{PROJECT_NAME}} if present
        template_description = extract_frontmatter_field(content, "description")
        description = (template_description or f"Agent for {project_name}.")
        description = description.replace("{{PROJECT_NAME}}", project_name)
        content = substitute(content, variables, rel_source, log)
        name = Path(filename).stem
        layer = source_path.parts[-2]  # "1-generic" or "2-platform"
        source_label = f"{layer}/{source_path.name}"
        generated_from = f"{source_label}@{source_version}" if source_version else source_label
        content = build_frontmatter(content, name, description,
                                    generated_from=generated_from)

        # Inject model: field (meta default from roles.config.json or project override)
        model = resolve_model(role, config, agent_meta_root)
        content = inject_model_field(content, model)
        if model:
            model_src = "project override" if role in config.get("model-overrides", {}) else "meta default"
            log.info(
                str(target_path.relative_to(project_root)),
                f"model: {model} (from {model_src})",
            )

        # Inject memory: field (meta default from roles.config.json or project override)
        memory = resolve_memory(role, config, agent_meta_root)
        content = inject_memory_field(content, memory)
        if memory:
            memory_src = "project override" if role in config.get("memory-overrides", {}) else "meta default"
            log.info(
                str(target_path.relative_to(project_root)),
                f"memory: {memory} (from {memory_src})",
            )

        # Inject permissionMode: field (meta default from roles.config.json or project override)
        permission_mode = resolve_permission_mode(role, config, agent_meta_root)
        content = inject_permission_mode_field(content, permission_mode)
        if permission_mode:
            pm_src = "project override" if role in config.get("permission-mode-overrides", {}) else "meta default"
            log.info(
                str(target_path.relative_to(project_root)),
                f"permissionMode: {permission_mode} (from {pm_src})",
            )

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        log.action("WRITE", str(target_path.relative_to(project_root)), rel_label)
        if not dry_run:
            target_path.write_text(content, encoding="utf-8")

    # Also track external skill agent filenames (they are not in overrides)
    ext_config = load_external_skills_config(agent_meta_root)
    project_skills = config.get("external-skills", {})
    for skill_name, skill_cfg in ext_config.get("skills", {}).items():
        if _skill_is_active(skill_name, skill_cfg, project_skills):
            role = skill_cfg.get("role", skill_name)
            expected_filenames.add(f"{role}.md")


    # Remove stale agent files that are no longer in the active role set
    if target_dir.exists():
        for existing_file in sorted(target_dir.glob("*.md")):
            if existing_file.name not in expected_filenames:
                log.action("DELETE", str(existing_file.relative_to(project_root)),
                           "role removed from config")
                if not dry_run:
                    existing_file.unlink()



def _strip_frontmatter(content: str) -> str:
    """Remove the YAML frontmatter block from content entirely."""
    if not content.startswith('---'):
        return content
    end = content.find('\n---', 3)
    if end == -1:
        return content
    return content[end + 4:].lstrip('\n')


def _remove_frontmatter_fields(content: str, fields: list) -> str:
    """Remove specific fields from YAML frontmatter."""
    import re as _re
    for field in fields:
        content = _re.sub(
            rf'^{_re.escape(field)}:.*\n', '', content, count=1, flags=_re.MULTILINE,
        )
    return content


def sync_agents_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
):
    """Generate agent files for a specific provider.

    Claude:    .claude/agents/<role>.md   — full frontmatter, all fields
    Gemini:    .gemini/agents/<role>.md   — frontmatter without permissionMode/memory
    Continue:  .continue/agents/<role>.md — minimal frontmatter (name, description, alwaysApply: false)
    """
    pc = PROVIDER_CONFIG.get(provider)
    if not pc:
        log.warn(f"Unknown provider '{provider}' — skipping agent sync")
        return

    platforms = config.get('platforms', [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / pc['agents_dir']

    allowed_roles = set(config['roles']) if 'roles' in config else None

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    expected_filenames: set = set()
    project_name = config['project']['name']

    for role, source_path in overrides.items():
        filename = target_filename(role)
        if not filename:
            if provider == 'Claude':
                log.skip(str(source_path.name), 'role not in ROLE_MAP')
            continue

        if allowed_roles is not None and role not in allowed_roles:
            if provider == 'Claude':
                rel = (str(target_dir / filename)
                       .replace(str(project_root) + '/', '')
                       .replace(str(project_root) + chr(92), ""))
                log.skip(rel, f"role '{role}' not in config['roles']")
            continue

        expected_filenames.add(filename)
        target_path = target_dir / filename
        content = source_path.read_text(encoding='utf-8')

        # Composition mode
        extends_base = extract_frontmatter_field(content, 'extends')
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)
            if provider == 'Claude':
                log.info(
                    str(target_path.relative_to(project_root)),
                    f'composed from {extends_base} + {source_path.name}',
                )

        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, 'version')
        template_description = extract_frontmatter_field(content, 'description')
        description = (template_description or f'Agent for {project_name}.')
        description = description.replace('{{PROJECT_NAME}}', project_name)
        content = substitute(content, variables, rel_source, log)
        name = Path(filename).stem
        layer = source_path.parts[-2]
        source_label = f'{layer}/{source_path.name}'
        generated_from = f'{source_label}@{source_version}' if source_version else source_label

        if provider == 'Continue':
            # Continue agents: minimal frontmatter (name + description only)
            # alwaysApply: false — agent is invoked by name, not auto-loaded
            fm = f"---\nname: {name}\ndescription: \"{description}\"\nalwaysApply: false\n---\n"
            body = _strip_frontmatter(content)
            body = _strip_claude_specific_lines(body)
            content = fm + body
        else:
            content = build_frontmatter(content, name, description, generated_from=generated_from)

            if provider == 'Claude':
                model = resolve_model(role, config, agent_meta_root)
                content = inject_model_field(content, model)
                if model:
                    src = 'project override' if role in config.get('model-overrides', {}) else 'meta default'
                    log.info(str(target_path.relative_to(project_root)), f'model: {model} (from {src})')

                memory = resolve_memory(role, config, agent_meta_root)
                content = inject_memory_field(content, memory)
                if memory:
                    src = 'project override' if role in config.get('memory-overrides', {}) else 'meta default'
                    log.info(str(target_path.relative_to(project_root)), f'memory: {memory} (from {src})')

                permission_mode = resolve_permission_mode(role, config, agent_meta_root)
                content = inject_permission_mode_field(content, permission_mode)
                if permission_mode:
                    src = 'project override' if role in config.get('permission-mode-overrides', {}) else 'meta default'
                    log.info(str(target_path.relative_to(project_root)), f'permissionMode: {permission_mode} (from {src})')

            elif provider == 'Gemini':
                # Gemini: model only; strip memory and permissionMode
                model = resolve_model(role, config, agent_meta_root)
                content = inject_model_field(content, model)
                content = _remove_frontmatter_fields(content, ['memory', 'permissionMode'])

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        log.action('WRITE', str(target_path.relative_to(project_root)), rel_label)
        if not dry_run:
            target_path.write_text(content, encoding='utf-8')

    # External skill filenames are always in .claude/agents/ (Claude only)
    if provider == 'Claude':
        ext_config = load_external_skills_config(agent_meta_root)
        project_skills = config.get('external-skills', {})
        for skill_name, skill_cfg in ext_config.get('skills', {}).items():
            if _skill_is_active(skill_name, skill_cfg, project_skills):
                ext_role = skill_cfg.get('role', skill_name)
                expected_filenames.add(f'{ext_role}.md')

    # Remove stale agent files
    if target_dir.exists():
        managed_index = target_dir / '.agent-meta-managed'
        previously_managed: set = set()
        if managed_index.exists():
            for line in managed_index.read_text(encoding='utf-8').splitlines():
                if line.strip():
                    previously_managed.add(line.strip())

        for existing_file in sorted(target_dir.glob('*.md')):
            if existing_file.name not in expected_filenames:
                if not managed_index.exists() or existing_file.name in previously_managed:
                    log.action('DELETE', str(existing_file.relative_to(project_root)),
                               'role removed from config')
                    if not dry_run:
                        existing_file.unlink()

        if not dry_run and expected_filenames:
            managed_index.write_text(
                '\n'.join(sorted(expected_filenames)) + '\n', encoding='utf-8'
            )


def _strip_claude_specific_lines(content: str) -> str:
    """Remove Claude Code-specific lines that are meaningless in other providers.

    Currently strips:
    - Extension-Hook lines: > **Extension:** Falls `.claude/3-project/...` existiert → ...
    - Read-Tool instructions referencing .claude/ paths
    """
    lines = content.splitlines(keepends=True)
    out = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("> **Extension:**") and ".claude/3-project/" in stripped:
            continue
        out.append(line)
    return "".join(out)


def _make_slim_body(content: str) -> str:
    """Reduce agent body to a compact prompt-friendly version.

    Keeps: role description, active DoD table, core workflow steps, Don'ts.
    Strips: extension hooks, verbose sub-sections, examples.
    """
    lines = content.splitlines()
    out = []
    skip_section = False
    slim_stop_anchors = {
        "## Workflow",
        "## Workflows",
        "## Schritt-für-Schritt",
        "## Beispiele",
        "## Beispiel",
        "## Anhang",
    }
    keep_sections = {
        "## Don'ts",
        "## Donts",
        "## Don",
        "## Kernregeln",
        "## Aktive DoD",
        "## DoD",
    }

    for line in lines:
        stripped = line.strip()
        # Skip extension-hook lines (Claude-specific)
        if stripped.startswith("> **Extension:**"):
            continue
        # Detect section changes
        if stripped.startswith("## "):
            skip_section = stripped in slim_stop_anchors
        if not skip_section:
            out.append(line)

    # Cap at ~80 lines for slim mode
    if len(out) > 80:
        out = out[:80]
        out.append("\n\n*[Prompt truncated — use agent mode for full context]*")

    return "\n".join(out)


def sync_prompts_for_continue(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Generate .continue/prompts/<role>.md as invokable slash-commands.

    Controlled by provider-options.Continue:
        generate-prompts: true          # enable (default: false)
        prompt-mode: "full" | "slim"    # full = complete agent body (default)
                                        # slim = compact role + core rules only

    Works with any local LLM — no tool calling required.
    Slash-commands: /developer, /git, /orchestrator, ...
    """
    opts = resolve_provider_options(config, "Continue")
    if not opts.get("generate-prompts", False):
        return

    prompt_mode = opts.get("prompt-mode", "full")
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    allowed_roles: set | None = set(config["roles"]) if "roles" in config else None

    prompts_dir = project_root / ".continue" / "prompts"
    if not dry_run:
        prompts_dir.mkdir(parents=True, exist_ok=True)

    expected: set[str] = set()

    for role, source_path in overrides.items():
        filename = target_filename(role)
        if not filename:
            continue
        if allowed_roles is not None and role not in allowed_roles:
            continue

        expected.add(filename)
        target_path = prompts_dir / filename
        content = source_path.read_text(encoding="utf-8")

        # Composition
        extends_base = extract_frontmatter_field(content, "extends")
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)

        rel_source = str(source_path.relative_to(agent_meta_root))
        content = substitute(content, variables, rel_source, log)

        template_description = extract_frontmatter_field(content, "description") or f"Agent for {role}."
        template_description = template_description.replace("{{PROJECT_NAME}}", config["project"]["name"])

        # Strip original frontmatter, optionally slim the body
        body = _strip_frontmatter(content)
        body = _strip_claude_specific_lines(body)
        if prompt_mode == "slim":
            body = _make_slim_body(body)

        # Build Continue prompt frontmatter
        fm = (
            f"---\n"
            f"name: {role}\n"
            f'description: "{template_description}"\n'
            f"invokable: true\n"
            f"---\n"
        )
        final = fm + body

        layer = source_path.parts[-2]
        log.action("WRITE", str(target_path.relative_to(project_root)),
                   f"{layer}/{source_path.name} [prompt/{prompt_mode}]")
        if not dry_run:
            target_path.write_text(final, encoding="utf-8")

    # Stale cleanup
    managed_index = prompts_dir / ".agent-meta-managed"
    previously_managed: set[str] = set()
    if managed_index.exists():
        for line in managed_index.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    if prompts_dir.exists():
        for existing_file in sorted(prompts_dir.glob("*.md")):
            if existing_file.name not in expected:
                if not managed_index.exists() or existing_file.name in previously_managed:
                    log.action("DELETE", str(existing_file.relative_to(project_root)),
                               "role removed from config")
                    if not dry_run:
                        existing_file.unlink()

    if not dry_run and expected:
        managed_index.write_text("\n".join(sorted(expected)) + "\n", encoding="utf-8")


def sync_snippets(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Copy snippet files from agent-meta/snippets/ to .claude/snippets/ in the project.

    Only copies snippets referenced via TESTER_SNIPPETS_PATH (or similar *_SNIPPETS_PATH
    variables) in the project config. Unknown snippet files are skipped.
    All referenced paths are resolved relative to agent-meta/snippets/.
    """
    variables = config.get("variables", {})
    snippets_root = agent_meta_root / SNIPPETS_DIR
    target_root = project_root / CLAUDE_SNIPPETS_DIR

    if not snippets_root.exists():
        return

    # Collect all *_SNIPPETS_PATH values from config variables
    snippet_paths: list[str] = [
        v for k, v in variables.items()
        if k.endswith("_SNIPPETS_PATH") and v
    ]

    if not snippet_paths:
        return

    for rel_path in snippet_paths:
        source_path = snippets_root / rel_path
        if not source_path.exists():
            log.warn(f"Snippet not found: snippets/{rel_path}")
            continue

        target_path = target_root / rel_path
        source_content = source_path.read_text(encoding="utf-8")
        snippet_version = extract_frontmatter_field(source_content, "version")
        version_label = f"@{snippet_version}" if snippet_version else ""

        log.action(
            "COPY",
            str(target_path.relative_to(project_root)),
            f"snippets/{rel_path}{version_label}",
        )
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(source_content, encoding="utf-8")


def collect_rule_sources(agent_meta_root: Path, platforms: list[str]) -> list[tuple[Path, str]]:
    """Collect rule files from 0-external, 1-generic and 2-platform layers.

    Returns list of (source_path, output_filename) tuples.
    Later entries override earlier ones with the same output filename —
    platform rules override generic rules of the same name.
    """
    # Use dict to track filename → source_path (last writer wins = platform > generic > external)
    seen: dict[str, Path] = {}

    # 0-external: rules from external skill repos (registered in external-skills.config.json)
    ext_rules_dir = agent_meta_root / RULES_DIR / "0-external"
    if ext_rules_dir.exists():
        for f in sorted(ext_rules_dir.glob("*.md")):
            seen[f.name] = f

    # 1-generic
    generic_dir = agent_meta_root / RULES_DIR / "1-generic"
    if generic_dir.exists():
        for f in sorted(generic_dir.glob("*.md")):
            seen[f.name] = f

    # 2-platform (platform-prefixed, e.g. sharkord-security.md → security.md)
    platform_dir = agent_meta_root / RULES_DIR / "2-platform"
    if platform_dir.exists():
        for platform in platforms:
            for f in sorted(platform_dir.glob(f"{platform}-*.md")):
                # Strip platform prefix from output filename
                output_name = f.name[len(platform) + 1:]
                seen[output_name] = f

    return [(src, name) for name, src in seen.items()]


def sync_rules(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Copy rule files from agent-meta/rules/ layers to .claude/rules/ in the project.

    Layer priority (highest wins for same output filename):
      2-platform  >  1-generic  >  0-external

    Project rules in .claude/rules/ that are NOT from agent-meta are never touched.
    Stale agent-meta-managed rules (tracked in .claude/rules/.agent-meta-managed) are removed.
    """
    platforms = config.get("platforms", [])
    sources = collect_rule_sources(agent_meta_root, platforms)

    if not sources:
        return

    target_dir = project_root / CLAUDE_RULES_DIR
    managed_index_path = target_dir / ".agent-meta-managed"

    # Load previously managed filenames so we can clean up stale ones
    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                previously_managed.add(line)

    now_managed: set[str] = set()

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        target_path = target_dir / output_name
        source_content = source_path.read_text(encoding="utf-8")
        layer = source_path.parts[-2]  # "1-generic", "2-platform", "0-external"

        log.action("COPY", str(target_path.relative_to(project_root)),
                   f"rules/{layer}/{source_path.name}")
        now_managed.add(output_name)

        if not dry_run:
            target_path.write_text(source_content, encoding="utf-8")

    # Remove stale managed rules no longer in current sources
    for stale_name in sorted(previously_managed - now_managed):
        stale_path = target_dir / stale_name
        if stale_path.exists():
            log.action("DELETE", str(stale_path.relative_to(project_root)),
                       "rule removed from agent-meta sources")
            if not dry_run:
                stale_path.unlink()

    # Update managed index
    if not dry_run and now_managed:
        managed_index_path.write_text("\n".join(sorted(now_managed)) + "\n", encoding="utf-8")


SPEECH_RULE_FILENAME = "speech-mode.md"
SPEECH_DIR = "speech"


def sync_speech_mode(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Copy speech/<mode>.md to .claude/rules/speech-mode.md.

    - 'full' (default): removes any existing speech-mode rule (no rule = default behavior).
    - Any other mode: copies speech/<mode>.md as .claude/rules/speech-mode.md.

    The rule is tracked in .claude/rules/.agent-meta-managed so stale entries are
    cleaned up by sync_rules on the next run. We also handle it directly here for
    the 'full' -> 'full' no-op and 'full' -> remove transition.
    """
    mode = config.get("speech-mode", "full")
    target_dir = project_root / CLAUDE_RULES_DIR
    target_path = target_dir / SPEECH_RULE_FILENAME
    managed_index_path = target_dir / ".agent-meta-managed"

    if mode == "full":
        # Remove any previously generated speech-mode rule
        if target_path.exists():
            log.action("DELETE", str(target_path.relative_to(project_root)),
                       "speech-mode is 'full' — no rule needed")
            if not dry_run:
                target_path.unlink()
        else:
            log.skip(str(target_path.relative_to(project_root)),
                     "speech-mode is 'full' — no rule needed")
        # Remove from managed index if present
        if not dry_run and managed_index_path.exists():
            lines = [l for l in managed_index_path.read_text(encoding="utf-8").splitlines()
                     if l.strip() and l.strip() != SPEECH_RULE_FILENAME]
            managed_index_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return

    source_path = agent_meta_root / SPEECH_DIR / f"{mode}.md"
    if not source_path.exists():
        log.warn(f"speech-mode '{mode}': source file not found at {source_path} — skipping")
        return

    source_content = source_path.read_text(encoding="utf-8")
    log.action("COPY", str(target_path.relative_to(project_root)),
               f"speech/{mode}.md")

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path.write_text(source_content, encoding="utf-8")

        # Add to managed index so sync_rules stale-cleanup knows about it
        currently_managed: list[str] = []
        if managed_index_path.exists():
            currently_managed = [l.strip() for l in
                                  managed_index_path.read_text(encoding="utf-8").splitlines()
                                  if l.strip()]
        if SPEECH_RULE_FILENAME not in currently_managed:
            currently_managed.append(SPEECH_RULE_FILENAME)
            managed_index_path.write_text("\n".join(sorted(currently_managed)) + "\n",
                                          encoding="utf-8")


def create_rule(
    project_root: Path,
    name: str,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/rules/<name>.md as an empty template (never overwrites)."""
    if not name.endswith(".md"):
        name = f"{name}.md"
    target_path = project_root / CLAUDE_RULES_DIR / name

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)),
                 "rule already exists — edit it manually")
        return

    content = f"""\
# {Path(name).stem.replace('-', ' ').replace('_', ' ').title()}

<!-- This file lives in .claude/rules/ and is automatically loaded into every agent context. -->
<!-- Add project-specific rules, policies, and conventions here. -->

"""
    log.action("CREATE", str(target_path.relative_to(project_root)),
               f"--create-rule {name}")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Hooks layer
# ---------------------------------------------------------------------------

HOOK_TEMPLATE_SH = """\
#!/bin/bash
# hook: %(stem)s
# version: 1.0.0
# event: PreToolUse
# matcher: Bash
# description: %(description)s
# enabled_by_default: false

# Claude Code passes hook context as JSON on stdin.
# Exit 0 = allow, exit 2 = block (stdout shown to Claude as context).
# See howto/hooks.md for full documentation.

INPUT=$(cat)

# TODO: implement hook logic here
# tip: use python3 to parse JSON from $INPUT
# example check:
#   TOOL_NAME=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_name',''))")

exit 0
"""


def parse_hook_metadata(script_content: str) -> dict:
    """Read # key: value header comments from a hook script.

    Reads from the top of the file; stops at first non-comment / non-shebang line.
    Expected keys: hook, version, event, matcher, description, enabled_by_default
    """
    meta: dict = {}
    for line in script_content.splitlines():
        line = line.rstrip()
        if line.startswith("#!"):
            continue  # skip shebang
        if not line.startswith("#"):
            break
        m = re.match(r"^#\s*([\w-]+):\s*(.+)$", line)
        if m:
            meta[m.group(1)] = m.group(2).strip()
    return meta


def collect_hook_sources(
    agent_meta_root: Path, platforms: list[str]
) -> list[tuple[Path, str]]:
    """Collect hook scripts from 0-external, 1-generic and 2-platform layers.

    Returns list of (source_path, output_filename) tuples.
    Layer priority (highest wins for same output filename):
      2-platform  >  1-generic  >  0-external
    """
    seen: dict[str, Path] = {}

    # 0-external
    ext_dir = agent_meta_root / HOOKS_DIR / "0-external"
    if ext_dir.exists():
        for f in sorted(ext_dir.glob("*.sh")):
            seen[f.name] = f

    # 1-generic
    generic_dir = agent_meta_root / HOOKS_DIR / "1-generic"
    if generic_dir.exists():
        for f in sorted(generic_dir.glob("*.sh")):
            seen[f.name] = f

    # 2-platform (strip platform prefix, e.g. sharkord-dod-push-check.sh → dod-push-check.sh)
    platform_dir = agent_meta_root / HOOKS_DIR / "2-platform"
    if platform_dir.exists():
        for platform in platforms:
            for f in sorted(platform_dir.glob(f"{platform}-*.sh")):
                output_name = f.name[len(platform) + 1:]
                seen[output_name] = f

    return [(src, name) for name, src in seen.items()]


def _hook_settings_command(output_filename: str) -> str:
    """Return the shell command string registered in settings.json for a hook."""
    return f"bash .claude/hooks/{output_filename}"


def _update_settings_hooks(
    project_root: Path,
    previously_managed: set[str],
    now_managed: set[str],
    active_entries: list[dict],
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Merge managed hook entries into .claude/settings.json.

    - Removes entries for stale managed hooks (in previously_managed but not now_managed)
    - Removes then re-adds entries for active hooks (clean replace)
    - Preserves all non-managed entries (user hooks, permissions, etc.)

    Hooks are identified in settings.json by their command string
    ``bash .claude/hooks/<filename>``.
    """
    settings_path = project_root / ".claude" / "settings.json"

    all_managed = previously_managed | now_managed
    if not all_managed and not settings_path.exists():
        return  # nothing to do

    # Load or initialise settings
    if settings_path.exists():
        try:
            with settings_path.open(encoding="utf-8") as f:
                settings = json.load(f)
        except (json.JSONDecodeError, OSError):
            log.warn("settings.json could not be parsed — hooks section not updated")
            return
    else:
        if not active_entries:
            return
        settings = {"permissions": {"allow": [], "deny": []}}

    hooks_section: dict = settings.get("hooks", {})

    # All commands we might have ever written (to remove stale + re-add active)
    all_managed_cmds = {_hook_settings_command(n) for n in all_managed}

    # Strip all managed entries from every event bucket
    for event_name in list(hooks_section.keys()):
        cleaned = [
            entry for entry in hooks_section[event_name]
            if not ({h.get("command", "") for h in entry.get("hooks", [])} & all_managed_cmds)
        ]
        if cleaned:
            hooks_section[event_name] = cleaned
        else:
            del hooks_section[event_name]

    # Add back currently active entries
    for entry_meta in active_entries:
        event = entry_meta["event"]
        matcher = entry_meta.get("matcher", "")
        command = entry_meta["command"]
        hook_entry: dict = {"hooks": [{"type": "command", "command": command}]}
        if matcher:
            hook_entry["matcher"] = matcher
        hooks_section.setdefault(event, []).append(hook_entry)

    # Update or remove hooks key
    if hooks_section:
        settings["hooks"] = hooks_section
    else:
        settings.pop("hooks", None)

    new_content = json.dumps(settings, indent=2, ensure_ascii=False) + "\n"

    stale = previously_managed - now_managed
    if stale:
        log.action("UPDATE", ".claude/settings.json",
                   f"removed stale hooks: {', '.join(Path(s).stem for s in sorted(stale))}")
    if active_entries:
        names = ", ".join(e["name"] for e in active_entries)
        log.action("UPDATE", ".claude/settings.json", f"registered hooks: {names}")
    elif not stale:
        return  # no effective change

    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(new_content, encoding="utf-8")


def sync_hooks(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Copy hook scripts from agent-meta/hooks/ layers to .claude/hooks/ in the project.

    Layer priority (same as rules and agents):
      2-platform  >  1-generic  >  0-external

    All hook scripts are always copied (like rules — no opt-in needed for the file).
    Registration in .claude/settings.json is opt-in per project:

      agent-meta.config.json:
        "hooks": { "dod-push-check": { "enabled": true } }

    Stale managed hooks (tracked in .claude/hooks/.agent-meta-managed) are deleted.
    Project-owned hook scripts (not in .agent-meta-managed) are never touched.
    """
    platforms = config.get("platforms", [])
    sources = collect_hook_sources(agent_meta_root, platforms)

    if not sources:
        return

    target_dir = project_root / CLAUDE_HOOKS_DIR
    managed_index_path = target_dir / ".agent-meta-managed"

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                previously_managed.add(line.strip())

    now_managed: set[str] = set()
    project_hooks_cfg = config.get("hooks", {})
    active_entries: list[dict] = []

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for source_path, output_name in sources:
        target_path = target_dir / output_name
        source_content = source_path.read_text(encoding="utf-8")
        meta = parse_hook_metadata(source_content)
        layer = source_path.parts[-2]

        log.action("COPY", str(target_path.relative_to(project_root)),
                   f"hooks/{layer}/{source_path.name}")
        now_managed.add(output_name)

        if not dry_run:
            target_path.write_text(source_content, encoding="utf-8")

        hook_stem = Path(output_name).stem
        is_enabled = project_hooks_cfg.get(hook_stem, {}).get("enabled", False)

        if is_enabled:
            event = meta.get("event", "PreToolUse")
            active_entries.append({
                "name": hook_stem,
                "event": event,
                "matcher": meta.get("matcher", ""),
                "command": _hook_settings_command(output_name),
            })
            log.info(str(target_path.relative_to(project_root)),
                     f"registered in settings.json (event: {event})")
        else:
            log.info(str(target_path.relative_to(project_root)),
                     f"copied (not enabled) — add \"hooks\": {{\"{hook_stem}\": {{\"enabled\": true}}}} to activate")

    # Remove stale hook scripts
    if target_dir.exists():
        for existing in sorted(target_dir.glob("*.sh")):
            if existing.name not in now_managed and existing.name in previously_managed:
                log.action("DELETE", str(existing.relative_to(project_root)),
                           "hook removed from agent-meta sources")
                if not dry_run:
                    existing.unlink()

    # Update .agent-meta-managed index
    if not dry_run and now_managed:
        managed_index_path.write_text(
            "\n".join(sorted(now_managed)) + "\n", encoding="utf-8"
        )

    # Merge hooks into settings.json
    _update_settings_hooks(
        project_root, previously_managed, now_managed, active_entries, log, dry_run
    )


def create_hook(
    project_root: Path,
    name: str,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Create .claude/hooks/<name>.sh from template (never overwrites).

    The created file is a project-owned hook — it will never be touched by sync.py
    (not added to .agent-meta-managed).  To register it in settings.json, add
    it to agent-meta.config.json:  "hooks": { "<name>": { "enabled": true } }
    """
    if not name.endswith(".sh"):
        name = f"{name}.sh"
    target_path = project_root / CLAUDE_HOOKS_DIR / name

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)),
                 "hook already exists — edit it manually")
        return

    stem = Path(name).stem
    description = f"{stem.replace('-', ' ').replace('_', ' ').title()} hook"
    content = HOOK_TEMPLATE_SH % {"stem": stem, "description": description}

    log.action("CREATE", str(target_path.relative_to(project_root)),
               f"--create-hook {stem}")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def _skill_is_active(skill_name: str, skill_cfg: dict, project_skills: dict) -> bool:
    """Return True if a skill should be generated for the current project.

    Two-gate check:
    1. approved: true in external-skills.config.json  (meta-maintainer quality gate)
    2. enabled:  true in agent-meta.config.json        (project opt-in)

    If project has no "external-skills" block at all, no skill is generated.
    """
    return (
        skill_cfg.get("approved", False)
        and project_skills.get(skill_name, {}).get("enabled", False)
    )


def load_external_skills_config(agent_meta_root: Path) -> dict:
    """Load external-skills.config.json from agent-meta root. Returns empty structure if not found."""
    config_path = agent_meta_root / EXTERNAL_SKILLS_CONFIG
    if not config_path.exists():
        return {"repos": {}, "skills": {}}
    with config_path.open(encoding="utf-8") as f:
        data = json.load(f)
    # Strip _comment keys
    return {
        "repos":   {k: v for k, v in data.get("repos", {}).items()   if not k.startswith("_")},
        "skills":  {k: v for k, v in data.get("skills", {}).items()  if not k.startswith("_")},
    }


def check_pinned_commits(ext_config: dict, agent_meta_root: Path, log: SyncLog) -> None:
    """Warn if any repo submodule is not at its pinned_commit."""
    for repo_name, repo_cfg in ext_config.get("repos", {}).items():
        pinned = repo_cfg.get("pinned_commit", "")
        if not pinned:
            continue
        local_path = repo_cfg.get("local_path", f"external/{repo_name}")
        actual = get_skill_commit(agent_meta_root, local_path)
        # get_skill_commit returns short hash — compare prefix
        if actual != "unknown" and not pinned.startswith(actual):
            log.warn(
                f"repo '{repo_name}': submodule is at {actual}, "
                f"expected pinned_commit {pinned[:8]} — "
                f"run: cd {local_path} && git checkout {pinned[:8]}"
            )


def get_skill_commit(agent_meta_root: Path, submodule_path: str) -> str:
    """Return short commit hash of a submodule. Falls back to 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(agent_meta_root / submodule_path),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def build_additional_files_section(skill_name: str, additional_files: list[str]) -> str:
    """Render the additional_files read-list for the wrapper template."""
    if not additional_files:
        return "_Keine weiteren Referenzdateien konfiguriert._"
    lines = ["Falls du detaillierte Referenzen brauchst, lies mit dem Read-Tool:"]
    for f in additional_files:
        lines.append(f"- `.claude/skills/{skill_name}/{f}`")
    return "\n".join(lines)


def normalize_skill_paths(content: str, skill_base_path: str) -> str:
    """Replace relative ./file references in skill content with absolute .claude/skills/... paths.

    Handles patterns like:
      - ./reference.md
      - **./reference.md**
      - [text](./reference.md)

    This allows SKILL.md files from external repos to use relative paths
    without knowing the agent-meta directory structure.
    """
    # Replace markdown link targets: (./file) → (skill_base_path/file)
    content = re.sub(
        r'\(\./([^)]+)\)',
        lambda m: f"({skill_base_path}/{m.group(1)})",
        content
    )
    # Replace bare ./file references (bold, plain, list items)
    content = re.sub(
        r'(?<!\()\.\/([^\s\)]+\.md)',
        lambda m: f"{skill_base_path}/{m.group(1)}",
        content
    )
    return content


def sync_external_skills(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Generate .claude/agents/<role>.md wrapper agents for approved + project-enabled skills.

    Two-gate check per skill:
    1. approved: true in external-skills.config.json  (meta-maintainer quality gate)
    2. enabled:  true in agent-meta.config.json        (project opt-in)
    """
    ext_config = load_external_skills_config(agent_meta_root)
    skills = ext_config.get("skills", {})
    repos = ext_config.get("repos", {})
    project_skills = config.get("external-skills", {})

    wrapper_path = agent_meta_root / AGENTS_DIR / EXTERNAL_DIR / SKILL_WRAPPER
    if not wrapper_path.exists():
        log.warn(f"Skill wrapper template not found: {wrapper_path}")
        return

    wrapper_template = wrapper_path.read_text(encoding="utf-8")
    agents_dir = project_root / CLAUDE_AGENTS_DIR
    skills_dir = project_root / CLAUDE_SKILLS_DIR

    for skill_name, skill_cfg in skills.items():
        role_label = f".claude/agents/{skill_cfg.get('role', skill_name)}.md"
        if not skill_cfg.get("approved", False):
            log.info(role_label, f"skill '{skill_name}' not approved — skipping")
            continue
        project_skill_cfg = project_skills.get(skill_name, {})
        if not project_skill_cfg.get("enabled", False):
            log.info(role_label, f"skill '{skill_name}' not enabled in agent-meta.config.json — skipping")
            continue

        repo_key   = skill_cfg.get("repo", "")
        repo_cfg   = repos.get(repo_key, {})
        local_path = repo_cfg.get("local_path", f"external/{repo_key}")
        source_rel    = skill_cfg.get("source", "")
        entry_file    = skill_cfg.get("entry", "SKILL.md")
        role          = skill_cfg.get("role", skill_name)
        display_name  = skill_cfg.get("name", skill_name)
        description   = skill_cfg.get("description", "")
        additional    = skill_cfg.get("additional_files", [])

        skill_source_dir = agent_meta_root / local_path / source_rel
        entry_path = skill_source_dir / entry_file

        # Detect uninitialized submodule (directory exists but is empty)
        submodule_dir = agent_meta_root / local_path
        if submodule_dir.exists() and not any(submodule_dir.iterdir()):
            log.warn(
                f"Submodule '{local_path}' is not initialized (empty directory) — "
                f"please run: git submodule update --init --recursive"
            )
            continue

        if not entry_path.exists():
            log.warn(f"Skill entry not found: {entry_path}")
            continue

        commit = get_skill_commit(agent_meta_root, local_path)

        # Canonical paths in the target project
        skill_base_path  = f".claude/skills/{skill_name}"
        skill_entry_path = f"{skill_base_path}/{entry_file}"

        # Build skill-specific variables (extend project variables)
        skill_vars = dict(variables)
        skill_vars["SKILL_NAME"]          = skill_name
        skill_vars["SKILL_NAME_DISPLAY"]  = display_name
        skill_vars["SKILL_ROLE"]          = role
        skill_vars["SKILL_DESCRIPTION"]   = description
        skill_vars["SKILL_COMMIT"]        = commit
        skill_vars["SKILL_ENTRY_PATH"]    = skill_entry_path
        skill_vars["SKILL_BASE_PATH"]     = skill_base_path
        skill_vars["SKILL_ADDITIONAL_FILES_SECTION"] = build_additional_files_section(
            skill_name, additional
        )

        # Generate thin wrapper agent (no inline skill content)
        agent_content = substitute(wrapper_template, skill_vars,
                                   f"0-external/{skill_name}", log)

        agent_target = agents_dir / f"{role}.md"
        log.action("WRITE", str(agent_target.relative_to(project_root)),
                   f"0-external/{skill_name}@{commit}")

        # Copy + normalize skill files to .claude/skills/<skill_name>/
        skill_target_dir = skills_dir / skill_name

        # Entry file: copy and normalize relative paths
        log.action("COPY", str((skill_target_dir / entry_file).relative_to(project_root)),
                   f"{local_path}/{source_rel}/{entry_file}")
        for af in additional:
            af_source = skill_source_dir / af
            if af_source.exists():
                log.action("COPY", str((skill_target_dir / af).relative_to(project_root)),
                           f"{local_path}/{source_rel}/{af}")
            else:
                log.warn(f"additional_file not found: {af_source}")

        if not dry_run:
            agents_dir.mkdir(parents=True, exist_ok=True)
            agent_target.write_text(agent_content, encoding="utf-8")
            skill_target_dir.mkdir(parents=True, exist_ok=True)

            # Normalize ./ref paths in entry file → .claude/skills/<skill>/ref
            entry_content = entry_path.read_text(encoding="utf-8")
            entry_content = normalize_skill_paths(entry_content, skill_base_path)
            (skill_target_dir / entry_file).write_text(entry_content, encoding="utf-8")

            for af in additional:
                af_source = skill_source_dir / af
                if af_source.exists():
                    (skill_target_dir / af).write_text(
                        af_source.read_text(encoding="utf-8"), encoding="utf-8"
                    )


def add_skill(
    agent_meta_root: Path,
    repo_url: str,
    skill_name: str,
    source_path: str,
    role: str,
    entry: str,
    log: SyncLog,
    dry_run: bool,
):
    """Register a new submodule + skill entry in external-skills.config.json.

    Runs: git submodule add <repo_url> external/<submodule_name>
    Then updates external-skills.config.json with the new submodule + skill entry.
    """
    # Derive submodule name from repo URL (last path segment without .git)
    submodule_name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
    local_path = f"external/{submodule_name}"

    # Run git submodule add (skip if already exists)
    submodule_target = agent_meta_root / local_path
    if submodule_target.exists():
        print(f"  i  Submodule already exists: {local_path}")
    else:
        print(f"  >  git submodule add {repo_url} {local_path}")
        if not dry_run:
            result = subprocess.run(
                ["git", "submodule", "add", repo_url, local_path],
                cwd=str(agent_meta_root),
                capture_output=False,
            )
            if result.returncode != 0:
                print(f"  !  git submodule add failed", file=sys.stderr)
                return

    # Update external-skills.config.json
    config_path = agent_meta_root / EXTERNAL_SKILLS_CONFIG
    if config_path.exists():
        with config_path.open(encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = {"repos": {}, "skills": {}}

    # Capture current commit for pinning
    actual_commit = get_skill_commit(agent_meta_root, local_path)

    raw.setdefault("repos", {})[submodule_name] = {
        "repo": repo_url,
        "local_path": local_path,
        "pinned_commit": actual_commit,
    }
    raw.setdefault("skills", {})[skill_name] = {
        "approved": False,
        "repo": submodule_name,
        "source": source_path,
        "entry": entry,
        "role": role,
        "name": skill_name.replace("-", " ").title(),
        "description": f"Specialist for {skill_name}.",
        "additional_files": [],
    }

    log.action("UPDATE", EXTERNAL_SKILLS_CONFIG,
               f"added repo '{submodule_name}' @{actual_commit[:8]}, skill '{skill_name}'")
    if not dry_run:
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2, ensure_ascii=False)
        print(f"  +  {EXTERNAL_SKILLS_CONFIG} updated")
        print(f"  i  Repo '{submodule_name}' pinned to commit {actual_commit[:8]}")
        print(f"  i  Skill '{skill_name}' added (approved: false) → role: '{role}'")
        print(f"  i  To activate: set approved: true in {EXTERNAL_SKILLS_CONFIG},")
        print(f"     then add to agent-meta.config.json: \"external-skills\": {{\"{skill_name}\": {{\"enabled\": true}}}}")


def create_extension(
    project_root: Path,
    config: dict,
    variables: dict,
    role: str,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/3-project/<prefix>-<role>-ext.md if it does not exist yet."""
    if role not in ROLE_MAP:
        print(f"  !  Unknown role '{role}'. Valid roles: {', '.join(ROLE_MAP)}", file=sys.stderr)
        return

    prefix = config["project"].get("prefix", "")
    filename = ext_target_filename(role, prefix)
    target_path = project_root / CLAUDE_EXT_DIR / filename

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)), "extension already exists — use --update-ext to update")
        return

    managed = render_managed_block(variables, f"--create-ext {role}", log)
    content = managed + PROJECT_SECTION_STUB

    log.action("CREATE", str(target_path.relative_to(project_root)), f"generated for role '{role}'")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def update_extensions(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Update the managed block in all existing extension files."""
    ext_dir = project_root / CLAUDE_EXT_DIR
    if not ext_dir.exists():
        log.skip(CLAUDE_EXT_DIR, "directory not found — no extensions to update")
        return

    for ext_file in sorted(ext_dir.glob(f"*{EXT_SUFFIX}.md")):
        existing = ext_file.read_text(encoding="utf-8")
        new_managed = render_managed_block(variables, str(ext_file.name), log)
        new_content = update_managed_block(existing, new_managed)

        if new_content == existing:
            log.skip(str(ext_file.relative_to(project_root)), "managed block unchanged")
        else:
            log.action("UPDATE", str(ext_file.relative_to(project_root)), "managed block")
            if not dry_run:
                ext_file.write_text(new_content, encoding="utf-8")


CLAUDE_MD_MANAGED_TEMPLATE = """\
<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`
DoD-Preset: **{{DOD_PRESET}}** | REQ-Traceability: {{DOD_REQ_TRACEABILITY}} | Tests: {{DOD_TESTS_REQUIRED}} | Codebase-Overview: {{DOD_CODEBASE_OVERVIEW}} | Security-Audit: {{DOD_SECURITY_AUDIT}}

{{AGENT_HINTS}}
<!-- agent-meta:managed-end -->"""


def sync_claude_md_managed(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Update the managed block in CLAUDE.md if it exists and contains the marker."""
    target_path = project_root / "CLAUDE.md"
    if not target_path.exists():
        return

    existing = target_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
        re.DOTALL,
    )
    if not pattern.search(existing):
        log.warn(
            "CLAUDE.md exists but has no managed block — "
            "AGENT_TABLE will not be updated. "
            "Add the following block at the desired location in CLAUDE.md:\n"
            "  <!-- agent-meta:managed-begin -->\n"
            "  <!-- agent-meta:managed-end -->"
        )
        return

    new_managed = substitute(CLAUDE_MD_MANAGED_TEMPLATE, variables, "CLAUDE.md managed block", log)
    new_content = pattern.sub(new_managed, existing, count=1)

    if new_content == existing:
        log.skip("CLAUDE.md", "managed block unchanged")
    else:
        log.action("UPDATE", "CLAUDE.md", "managed block (AGENT_TABLE + version)")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")



def sync_context_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
):
    """Create or update the context file for a given provider.

    Claude:   CLAUDE.md - managed block updated on every sync
    Gemini:   .gemini/GEMINI.md - created once from template; managed block updated
    Continue: .continue/config.yaml - skeleton, created once (never overwritten)
    """
    pc = PROVIDER_CONFIG.get(provider)
    if not pc:
        return

    if provider == "Claude":
        sync_claude_md_managed(project_root, variables, log, dry_run)

    elif provider == "Gemini":
        context_file = pc["context_file"]
        if context_file is None:
            return
        target_path = project_root / context_file
        template_name = pc["context_template"]
        template_path = agent_meta_root / template_name if template_name else None

        if not target_path.exists():
            if template_path and template_path.exists():
                gcontent = template_path.read_text(encoding="utf-8")
                gcontent = substitute(gcontent, variables, template_name, log)
                log.action("INIT", str(target_path.relative_to(project_root)), template_name)
            else:
                project_name = config["project"]["name"]
                gcontent = (
                    f"# {project_name}\n\n"
                    "<!-- agent-meta:managed-begin -->\n"
                    "<!-- agent-meta:managed-end -->\n\n"
                    "## Agents\n\n"
                    f"Agent files are in .gemini/agents/ (use @agent-name).\n"
                )
                log.action("INIT", str(target_path.relative_to(project_root)),
                           "minimal fallback (GEMINI.project-template.md not found)")
            if not dry_run:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(gcontent, encoding="utf-8")
        else:
            existing = target_path.read_text(encoding="utf-8")
            managed_pattern = re.compile(
                r"<!--\s*agent-meta:managed-begin\s*-->"
                r".*?<!--\s*agent-meta:managed-end\s*-->",
                re.DOTALL,
            )
            if managed_pattern.search(existing):
                new_managed = substitute(CLAUDE_MD_MANAGED_TEMPLATE, variables,
                                         str(target_path.relative_to(project_root)), log)
                new_content = managed_pattern.sub(new_managed, existing, count=1)
                if new_content != existing:
                    log.action("UPDATE", str(target_path.relative_to(project_root)),
                               "managed block")
                    if not dry_run:
                        target_path.write_text(new_content, encoding="utf-8")
                else:
                    log.skip(str(target_path.relative_to(project_root)), "managed block unchanged")

    elif provider == "Continue":
        # 1. .continue/rules/project-context.md — created once from template; managed block updated
        context_file = pc["context_file"]
        if context_file:
            ctx_path = project_root / context_file
            template_path = agent_meta_root / pc["context_template"]
            if not ctx_path.exists():
                if template_path.exists():
                    ccontent = substitute(
                        template_path.read_text(encoding="utf-8"),
                        variables, pc["context_template"], log,
                    )
                else:
                    ccontent = (
                        f"# {variables.get('PROJECT_NAME', 'Project Context')}\n\n"
                        f"{variables.get('PROJECT_CONTEXT', '')}\n\n"
                        "<!-- agent-meta:managed-begin -->\n"
                        "<!-- agent-meta:managed-end -->\n\n"
                        "## Agent Rules\n\n"
                        "Agent context files are in `.continue/rules/`.\n"
                        "Continue loads all Markdown files in this directory automatically as context.\n"
                    )
                    log.action("INIT", str(ctx_path.relative_to(project_root)),
                               "minimal fallback (CONTINUE.project-template.md not found)")
                log.action("INIT", str(ctx_path.relative_to(project_root)),
                           pc["context_template"])
                if not dry_run:
                    ctx_path.parent.mkdir(parents=True, exist_ok=True)
                    ctx_path.write_text(ccontent, encoding="utf-8")
            else:
                # Update managed block on every sync
                existing = ctx_path.read_text(encoding="utf-8")
                new_managed = render_managed_block(variables, context_file, log)
                updated = update_managed_block(existing, new_managed)
                if updated != existing:
                    log.action("UPDATE", str(ctx_path.relative_to(project_root)),
                               "managed block refreshed")
                    if not dry_run:
                        ctx_path.write_text(updated, encoding="utf-8")
                else:
                    log.skip(str(ctx_path.relative_to(project_root)), "managed block unchanged")

        # 2. .continue/config.yaml — skeleton, created once (never overwritten)
        settings_file = pc["settings_file"]
        settings_path = project_root / settings_file
        if settings_path.exists():
            log.skip(str(settings_path.relative_to(project_root)),
                     "already exists - not overwritten")
        else:
            settings_template_rel = pc.get("settings_template")
            if settings_template_rel:
                settings_template_path = agent_meta_root / settings_template_rel
            else:
                settings_template_path = None

            if settings_template_path and settings_template_path.exists():
                yaml_content = settings_template_path.read_text(encoding="utf-8")
                source_label = settings_template_rel
            else:
                yaml_content = (
                    "# Continue configuration\n"
                    "# See https://docs.continue.dev for full documentation\n"
                    "\n"
                    "# Agents are in .continue/agents/ - managed by agent-meta\n"
                    "# Project rules are in .continue/rules/ - managed by agent-meta\n"
                )
                source_label = "minimal fallback"
                if settings_template_rel:
                    log.warn(f"{settings_template_rel} not found — using minimal fallback for {settings_file}")
            log.action("INIT", str(settings_path.relative_to(project_root)),
                       source_label)
            if not dry_run:
                settings_path.parent.mkdir(parents=True, exist_ok=True)
                settings_path.write_text(yaml_content, encoding="utf-8")

def init_claude_personal(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Copy CLAUDE.personal-template.md to CLAUDE.personal.md if not present yet."""
    template_path = agent_meta_root / "howto" / "CLAUDE.personal-template.md"
    target_path = project_root / "CLAUDE.personal.md"

    if target_path.exists():
        log.skip("CLAUDE.personal.md", "already exists")
        return

    if not template_path.exists():
        log.warn("CLAUDE.personal-template.md not found — skipping CLAUDE.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "CLAUDE.personal.md", "howto/CLAUDE.personal-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def init_settings_json(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/settings.json if it does not exist yet.

    The file is created once as a skeleton for team-shared settings.
    The hooks section is managed separately by sync_hooks() on every sync.
    """
    target_path = project_root / ".claude" / "settings.json"
    if target_path.exists():
        log.skip(".claude/settings.json", "already exists")
        return

    content = '{\n  "permissions": {\n    "allow": [],\n    "deny": []\n  }\n}\n'
    log.action("INIT", ".claude/settings.json", "team permissions skeleton")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def init_settings_local_json(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Create .claude/settings.local.json skeleton if it does not exist yet.

    This file is gitignored and intended for personal / machine-local overrides
    (e.g. allow-listing commands during development, local hook overrides).
    Created once on --init or first Claude sync — never overwritten afterwards.
    """
    target_path = project_root / ".claude" / "settings.local.json"
    if target_path.exists():
        log.skip(".claude/settings.local.json", "already exists")
        return

    content = (
        '{\n'
        '  "permissions": {\n'
        '    "allow": [],\n'
        '    "deny": []\n'
        '  }\n'
        '}\n'
    )
    log.action("INIT", ".claude/settings.local.json", "personal/local settings skeleton (gitignored)")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


GITIGNORE_ENTRIES = [
    ".claude/settings.local.json",
    ".claude/agent-memory-local/",
    "CLAUDE.personal.md",
    "sync.log",
]

GITIGNORE_BLOCK_BEGIN = "# --- agent-meta managed (do not edit) ---"
GITIGNORE_BLOCK_END   = "# --- end agent-meta managed ---"


def ensure_gitignore_entries(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Ensure required entries exist in a managed block in .gitignore.

    Writes a clearly marked block so users know the entries are managed by
    agent-meta and should not be removed manually.
    If the block already exists, it is updated in-place (entries added, never removed).
    Entries that already exist outside the block are not duplicated.
    """
    gitignore_path = project_root / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

    # Extract current block content if present
    block_pattern = re.compile(
        re.escape(GITIGNORE_BLOCK_BEGIN) + r"(.*?)" + re.escape(GITIGNORE_BLOCK_END),
        re.DOTALL,
    )
    block_match = block_pattern.search(existing)
    block_entries: set[str] = set()
    if block_match:
        block_entries = {
            line.strip() for line in block_match.group(1).splitlines() if line.strip()
        }

    # Entries already present anywhere in the file (outside block too)
    all_present = {line.strip() for line in existing.splitlines() if line.strip() and not line.startswith("#")}

    missing = [e for e in GITIGNORE_ENTRIES if e not in block_entries]
    if not missing:
        log.skip(".gitignore", "all required entries already present")
        return

    new_block_entries = sorted(block_entries | set(missing))
    new_block = (
        GITIGNORE_BLOCK_BEGIN + "\n"
        + "\n".join(new_block_entries) + "\n"
        + GITIGNORE_BLOCK_END
    )

    if block_match:
        new_content = block_pattern.sub(new_block, existing)
    else:
        new_content = existing.rstrip("\n") + "\n\n" + new_block + "\n"

    log.action("UPDATE", ".gitignore", f"added to managed block: {', '.join(missing)}")
    if not dry_run:
        gitignore_path.write_text(new_content, encoding="utf-8")


def init_claude_md(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    template_path = agent_meta_root / "howto" / "CLAUDE.project-template.md"
    target_path = project_root / "CLAUDE.md"

    if target_path.exists():
        print("  i  CLAUDE.md already exists — skipped (use --only-variables)")
        log.skip("CLAUDE.md", "already exists")
        return

    if not template_path.exists():
        log.warn(f"CLAUDE.project-template.md not found at {template_path}")
        return

    content = template_path.read_text(encoding="utf-8")
    content = substitute(content, variables, "CLAUDE.project-template.md", log)
    log.action("INIT", "CLAUDE.md", "howto/CLAUDE.project-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def only_variables(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    target_path = project_root / "CLAUDE.md"
    if not target_path.exists():
        print("  !  CLAUDE.md not found — use --init to create it")
        sys.exit(1)

    content = target_path.read_text(encoding="utf-8")
    new_content = substitute(content, variables, "CLAUDE.md", log)

    if new_content == content:
        log.action("SKIP", "CLAUDE.md", "no open placeholders")
    else:
        log.action("WRITE", "CLAUDE.md", "variables from config")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync agent-meta agents into a project."
    )
    parser.add_argument("--config", required=False, default=None,
                        help="Path to agent-meta.config.json (not required for --add-skill)")
    parser.add_argument("--init", action="store_true",
                        help="Also generate CLAUDE.md from template (only if not present)")
    parser.add_argument("--only-variables", action="store_true",
                        help="Only substitute {{VARIABLE}} in existing CLAUDE.md")
    parser.add_argument("--create-ext", metavar="ROLE",
                        help="Create extension file for ROLE (or 'all'). "
                             "Does not overwrite existing files.")
    parser.add_argument("--update-ext", action="store_true",
                        help="Update managed block in all existing extension files")
    parser.add_argument("--create-rule", metavar="NAME",
                        help="Create .claude/rules/<NAME>.md template (never overwrites)")
    parser.add_argument("--create-hook", metavar="NAME",
                        help="Create .claude/hooks/<NAME>.sh template (never overwrites). "
                             "Enable via agent-meta.config.json: "
                             "\"hooks\": {\"<NAME>\": {\"enabled\": true}}")
    parser.add_argument("--fill-defaults", action="store_true",
                        help="Write missing config fields with their default values into "
                             "agent-meta.config.json. Structural fields (dod-preset, "
                             "max-parallel-agents, speech-mode, dod.*) are written when absent. "
                             "Missing variable keys are reported as warnings only.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without writing files")

    # External skill management
    parser.add_argument("--add-skill", metavar="REPO_URL",
                        help="Register a new external skill: git submodule add + config entry")
    parser.add_argument("--skill-name", metavar="NAME",
                        help="Skill identifier (used in external-skills.config.json)")
    parser.add_argument("--source", metavar="PATH",
                        help="Path to skill directory within the submodule repo")
    parser.add_argument("--role", metavar="ROLE",
                        help="Agent role name for the generated wrapper agent")
    parser.add_argument("--entry", metavar="FILE", default="SKILL.md",
                        help="Entry file within the skill directory (default: SKILL.md)")

    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    agent_meta_root = find_agent_meta_root(script_path)

    log = SyncLog()

    if args.dry_run:
        print("DRY-RUN — no files will be written\n")

    if args.add_skill:
        mode = "add-skill"
        for required, flag in [(args.skill_name, "--skill-name"),
                               (args.source, "--source"),
                               (args.role, "--role")]:
            if not required:
                print(f"  !  --add-skill requires {flag}", file=sys.stderr)
                sys.exit(1)
        add_skill(agent_meta_root, args.add_skill, args.skill_name,
                  args.source, args.role, args.entry, log, args.dry_run)
        log.write(agent_meta_root / LOGFILE, EXTERNAL_SKILLS_CONFIG,
                  read_version(agent_meta_root), mode, [], args.dry_run)
        return

    # All other modes require --config
    if not args.config:
        print("  !  --config is required (except for --add-skill)", file=sys.stderr)
        sys.exit(1)

    project_root = Path(args.config).resolve().parent
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    variables, pre_warnings = build_variables(config, agent_meta_root)
    platforms = config.get("platforms", [])
    source_version = config.get("agent-meta-version", read_version(agent_meta_root))

    for w in pre_warnings:
        log.warn(w)

    if args.fill_defaults:
        mode = "fill-defaults"
        fill_defaults(config_path, agent_meta_root, log, args.dry_run)

    elif args.only_variables:
        mode = "only-variables"
        only_variables(project_root, variables, log, args.dry_run)

    elif args.create_ext:
        mode = f"create-ext:{args.create_ext}"
        roles = list(ROLE_MAP.keys()) if args.create_ext == "all" else [args.create_ext]
        for role in roles:
            create_extension(project_root, config, variables, role, log, args.dry_run)

    elif args.update_ext:
        mode = "update-ext"
        update_extensions(project_root, variables, log, args.dry_run)

    elif args.create_rule:
        mode = f"create-rule:{args.create_rule}"
        create_rule(project_root, args.create_rule, log, args.dry_run)

    elif args.create_hook:
        mode = f"create-hook:{args.create_hook}"
        create_hook(project_root, args.create_hook, log, args.dry_run)

    else:
        providers = resolve_providers(config)
        mode = "init" if args.init else "sync"
        log.info("providers", "active: " + ", ".join(providers))
        # Log resolved DoD
        preset_name = config.get("dod-preset", "full")
        dod_resolved = resolve_dod(config, agent_meta_root)
        dod_summary = ", ".join(f"{k}: {v}" for k, v in dod_resolved.items())
        log.info("DoD", f"preset '{preset_name}' -> {dod_summary}")
        is_claude = "Claude" in providers
        if args.init or is_claude:
            init_claude_md(agent_meta_root, project_root, config, variables, log, args.dry_run)
            init_claude_personal(agent_meta_root, project_root, log, args.dry_run)
            init_settings_json(project_root, log, args.dry_run)
            init_settings_local_json(project_root, log, args.dry_run)
            ensure_gitignore_entries(project_root, log, args.dry_run)
        # Per-provider sync
        for provider in providers:
            pc = PROVIDER_CONFIG[provider]
            log.provider_header(provider)
            sync_agents_for_provider(agent_meta_root, project_root, config, variables,
                                     log, args.dry_run, provider)
            sync_context_for_provider(agent_meta_root, project_root, config, variables,
                                      log, args.dry_run, provider)
            if provider == "Continue":
                sync_prompts_for_continue(agent_meta_root, project_root, config,
                                          variables, log, args.dry_run)
            if pc["has_rules"] and provider == "Claude":
                sync_rules(agent_meta_root, project_root, config, log, args.dry_run)
                sync_speech_mode(agent_meta_root, project_root, config, log, args.dry_run)
            if pc["has_hooks"] and provider == "Claude":
                sync_hooks(agent_meta_root, project_root, config, log, args.dry_run)
        sync_snippets(agent_meta_root, project_root, config, log, args.dry_run)
        # Check pinned commits + warn for unknown/unapproved skills in project config
        ext_config = load_external_skills_config(agent_meta_root)
        check_pinned_commits(ext_config, agent_meta_root, log)
        if "external-skills" in config:
            known_skills = set(ext_config.get("skills", {}).keys())
            for skill_name in config["external-skills"]:
                if skill_name not in known_skills:
                    log.warn(f"external-skills: '{skill_name}' not found in external-skills.config.json -- skipping")
                elif not ext_config["skills"][skill_name].get("approved", False):
                    log.warn(f"external-skills: '{skill_name}' is not approved by meta-maintainer -- skipping")
        sync_external_skills(agent_meta_root, project_root, config, variables, log, args.dry_run)

    log_path = project_root / LOGFILE
    _providers = resolve_providers(config) if config else []
    _speech = config.get("speech-mode", "full") if config else "full"
    log.write(log_path, args.config, source_version, mode, platforms, args.dry_run,
              providers=_providers, speech_mode=_speech)


if __name__ == "__main__":
    main()
