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
    build_pipeline_variables,
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


def build_variables(config: dict, agent_meta_root: Path) -> tuple[dict, list[str]]:
    """Returns (variables_dict, pre_warnings)."""
    # Import here to avoid circular deps — agents module uses config module
    from .agents import build_agent_hints, build_agent_table
    from .delegation_table import generate_agent_delegation_table
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
    # AGENTS_DIR: provider-agnostic generated agents directory (default: .claude/agents)
    if "AGENTS_DIR" not in variables:
        variables["AGENTS_DIR"] = ".claude/agents"
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
    # ORCHESTRATOR_OUTCOME_CACHING: auto-inject from outcome-caching block in project.yaml
    oc_config = config.get("outcome-caching", {})
    variables["ORCHESTRATOR_OUTCOME_CACHING"] = "true" if oc_config.get("enabled", False) else "false"
    variables["ORCHESTRATOR_CACHE_TTL"] = str(oc_config.get("ttl_seconds", 3600))
    variables["ORCHESTRATOR_CACHE_MAX_ENTRIES"] = str(oc_config.get("max_entries", 100))
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
    # VALIDATOR_ENABLED: auto-detect from project roles list
    variables["VALIDATOR_ENABLED"] = "true" if "validator" in config.get("roles", []) else "false"
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
        if effective:
            variables["QUALITY_PIPELINES_ENABLED"] = "true"
        # Build variables for active pipelines; also set BLOCK="" for disabled
        # base pipelines so substitute() never warns about missing placeholders.
        active_vars = build_pipeline_variables(effective, dod_resolved)
        variables.update(active_vars)
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
    return variables, unmapped


def strip_inactive_conditional_blocks(text: str, variables: dict) -> str:
    """Remove conditional blocks that are inactive in this project.

    Handles:
        {{#if VAR}}...content...{{/if}}
        {{#if VAR}}...content...{{else}}...alt-content...{{/if}}
        {{#unless VAR}}...content...{{/unless}}

    Nested blocks are resolved via repeated passes until no markers remain.
    """
    conditional_vars = {k for k in variables if (k.startswith("DOD_") or k in ("SE_ENABLED", "VALIDATOR_ENABLED", "QUALITY_PIPELINES_ENABLED")) and k != "DOD_PRESET"}
    conditional_vars.update({k for k in variables if k.startswith("PIPELINE_") and k.endswith("_ENABLED")})
    conditional_vars.update({k for k in variables if k in ("ORCHESTRATOR_ENABLED", "UNKNOWN_FALLBACK_ASK_USER", "UNKNOWN_FALLBACK_META_FEEDBACK", "UNKNOWN_FALLBACK_MAIN_CHAT")})

    if not conditional_vars:
        return text

    # Repeat until stable — handles nested blocks
    max_passes = 10
    for _pass in range(max_passes):
        made_change = False
        for var in conditional_vars:
            var_pattern = re.escape(var)

            # 1. Handle {{#if VAR}}...{{else}}...{{/if}} (if-else-endif)
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

            pattern_ife = rf"\{{{{#if {var_pattern}\}}}}\n?(.*?)\{{{{else\}}}}\n?(.*?)\{{{{/if\}}}}\n?"
            old_text = text
            text = re.sub(pattern_ife, replace_if_else, text, flags=re.DOTALL)
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

            pattern_unless = rf"\{{{{#unless {var_pattern}\}}}}\n?(.*?)\{{{{/unless\}}}}\n?"
            old_text = text
            text = re.sub(pattern_unless, replace_unless, text, flags=re.DOTALL)
            if text != old_text:
                made_change = True

            # 3. Handle {{#if VAR}}...{{/if}} (simple, no else)
            def replace_if(m: re.Match, _var: str = var) -> str:
                block_content = m.group(1)
                if variables.get(_var, "true") == "false":
                    return ""
                stripped = block_content.strip("\n")
                if m.group(0).endswith("\n"):
                    return stripped + "\n"
                return stripped

            pattern_if = rf"\{{{{#if {var_pattern}\}}}}\n?(.*?)\{{{{/if\}}}}\n?"
            old_text = text
            text = re.sub(pattern_if, replace_if, text, flags=re.DOTALL)
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
            return variables[key]
        log.warn(f"Variable {key} not in config — placeholder remains in: {source_label}")
        return match.group(0)

    text = re.sub(r"\{\{([A-Z0-9_]+)\}\}", replacer, text)

    # Third pass: restore escaped literals as {{VAR}} (no substitution happened)
    for i, name in enumerate(escaped):
        text = text.replace(f"{_SENTINEL}{i}{_SENTINEL}", f"{{{{{name}}}}}")

    return text


# ---------------------------------------------------------------------------
# Platform Orchestrator Patches — provider-specific orchestrator instructions
# injected by sync.py during agent generation (Issue #250).
# ---------------------------------------------------------------------------

PLATFORM_ORCHESTRATOR_PATCHES: dict[str, list[dict]] = {
    "Gemini": [
        {
            "op": "append-after",
            "anchor": "## Mention-Interception Policy (Pflicht)",
            "content": (
                "### Gemini/Antigravity-spezifische Hinweise\n"
                "\n"
                "**Technische Einschränkung:** Die Gemini/Antigravity UI interceptet **ausschließlich** den `@orchestrator`-Mention.\n"
                "Alle anderen `@<agent>`-Mentions (`@git`, `@feedback`, `@meta-feedback`, `@developer`, etc.) werden als\n"
                "reiner Text gerendert und lösen **keine** Subagent-Invocation aus.\n"
                "\n"
                "**Pflicht-Regeln für Gemini:**\n"
                "1. Verwende IMMER `@orchestrator <Aufgabe>` für alle Delegationsaufrufe\n"
                "2. Verwende NIEMALS `@git`, `@feedback`, `@developer` oder andere Agent-Mentions\n"
                "3. Wenn der Hauptchat delegieren muss: `@orchestrator Delegiere an git: \"Commit message...\"`\n"
                "4. Die \"Ausnahmen — direkter Dispatch\" aus use-orchestrator.md gelten in Gemini **nicht** als User-Mentions — sie sind rein interne Delegationsentscheidungen\n"
                "\n"
                "**Wichtiger Hinweis zur Delegation:**\n"
                "Gemini/Antigravity unterstützt kein natives Subagent-Dispatch-Tool wie andere Umgebungen.\n"
                "Die ausgelieferten `.gemini/agents/*.md`-Dateien werden von Antigravity **nicht** automatisch geladen.\n"
                "Siehe Bootstrap-Instruktionen in `GEMINI.md` für die Session-Start-Registrierung.\n"
                "\n"
                "**Beispiel — Falsch (funktioniert nicht in Gemini):**\n"
                "> \"@meta-feedback Bitte erstelle ein Issue für...\"\n"
                "\n"
                "**Beispiel — Richtig:**\n"
                "> \"@orchestrator Delegiere an meta-feedback: Erstelle ein Issue für...\""
            ),
        },
        {
            "op": "append",
            "content": (
                "## Gemini/Antigravity — SE-Cascade Workaround\n"
                "\n"
                "Gemini unterstützt kein natives Subagent-Dispatch-Tool. "
                "Für SE-Cascades verwende `scripts/run-cascade.py`:\n"
                "1. `python scripts/run-cascade.py --input \"<Stakeholder Need>\"`\n"
                "2. Prompt-Dateien aus `.se-cascade/<session>/prompts/` in Gemini einfügen\n"
                "3. Ergebnisse in `.se-cascade/<session>/` speichern\n"
                "4. `--resume <session-id>` für Fortsetzung nach Unterbrechung\n"
                "\n"
                "Dokumentation: `howto/SE_CASCADE_GEMINI.md`\n"
            ),
        },
    ],
    "Continue": [
        {
            "op": "append-after",
            "anchor": "## Mention-Interception Policy (Pflicht)",
            "content": (
                "### Continue-spezifische Delegation\n"
                "\n"
                "Continue unterstützt **kein** natives Subagent-Dispatch-Tool.\n"
                "Delegation erfolgt ausschließlich über `@agent`-Text-Mentions:\n"
                "\n"
                "**Syntax:**\n"
                "- `@developer Implementiere Feature X`\n"
                "- `@git Commit und push`\n"
                "- `@code-reviewer Prüfe die Änderungen`\n"
                "\n"
                "**Einschränkungen:**\n"
                "- Keine parallele Subagent-Ausführung — Aufgaben sequentiell abarbeiten\n"
                "- Agent-Dateien müssen in `.continue/prompts/` liegen\n"
                "- Der `@orchestrator`-Mention wird von Continue unterstützt\n"
                "\n"
                "**Pflicht-Regeln für Continue:**\n"
                "1. Verwende `@agent <Aufgabe>` für alle Delegationen\n"
                "2. Keine parallelen Delegationen — sequentiell abarbeiten\n"
                "3. Prüfe nach jeder Delegation das Ergebnis vor der nächsten\n"
            ),
        },
    ],
    "Copilot": [
        {
            "op": "append-after",
            "anchor": "## Mention-Interception Policy (Pflicht)",
            "content": (
                "### Copilot-spezifische Delegation\n"
                "\n"
                "Copilot verwendet `@agent`-Text-Mentions für Agenten-Dispatch:\n"
                "\n"
                "**Syntax:**\n"
                "- `@developer Implementiere Feature X`\n"
                "- `@git Commit und push`\n"
                "\n"
                "**Einschränkungen:**\n"
                "- Keine parallele Subagent-Ausführung — sequentiell\n"
                "- Agenten werden aus `.github/copilot/agents/` geladen\n"
            ),
        },
    ],
}
