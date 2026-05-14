"""Provider isolation: prevent AI providers from reading each other's directories.

When multiple providers are active (e.g. Claude + Gemini + Opencode), sync.py
generates hard-block configurations so each provider cannot read or write files
managed by other providers.

Mechanisms per provider:
  Claude   — permissions.deny in .claude/settings.json (glob patterns)
  Opencode — permission.read + permission.edit in opencode.json (glob patterns, last-match-wins)
  Gemini   — TOML policy file .gemini/policies/provider-isolation.toml (regex on tool arguments)
  Continue — soft rule .continue/rules/provider-isolation.md (no native hard block available)

Trigger: only when len(active_providers) > 1 AND project.yaml does not have
provider-isolation: disabled.
"""

import json
import re
from pathlib import Path

from .io import safe_path, write_checked
from .log import SyncLog

# Companion state files — store agent-meta tracking data outside tool JSON schemas.
# Both Claude Code and Opencode use strict schema validation (Zod .strict() /
# JSON Schema) and reject unknown root keys, making the entire config file invalid.
# Tracking data is therefore stored in separate companion files that are not
# subject to those schemas.
_CLAUDE_STATE_FILE = ".claude/agent-meta-state.json"
_OPENCODE_STATE_FILE = ".opencode/agent-meta-state.json"

_GEMINI_POLICIES_DIR = ".gemini/policies"
_GEMINI_ISOLATION_FILE = ".gemini/policies/provider-isolation.toml"
_CONTINUE_ISOLATION_FILE = ".continue/rules/provider-isolation.md"


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def sync_provider_isolation(
    project_root: Path,
    providers: list[str],
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Generate provider isolation blocks for all active providers.

    Does nothing when fewer than 2 providers are active (no cross-provider
    isolation needed).
    """
    if len(providers) < 2:
        log.skip("provider-isolation", f"only {len(providers)} provider active — skipping")
        return

    log.info("provider-isolation", f"generating isolation for: {', '.join(providers)}")

    for provider in providers:
        # foreign_dirs = isolation-dirs of all OTHER active providers
        foreign_dirs: list[str] = []
        for other in providers:
            if other == provider:
                continue
            other_pc = provider_config.get(other, {})
            for d in other_pc.get("isolation-dirs", []):
                if d not in foreign_dirs:
                    foreign_dirs.append(d)

        if not foreign_dirs:
            log.skip(f"provider-isolation/{provider}", "no foreign dirs found")
            continue

        if provider == "Claude":
            _sync_claude_isolation(project_root, foreign_dirs, log, dry_run)
        elif provider == "Opencode":
            _sync_opencode_isolation(project_root, foreign_dirs, log, dry_run)
        elif provider == "Gemini":
            _sync_gemini_isolation(project_root, foreign_dirs, log, dry_run)
        elif provider == "Continue":
            _sync_continue_isolation(project_root, foreign_dirs, log, dry_run)
        else:
            log.skip(f"provider-isolation/{provider}", "no isolation mechanism defined for this provider")


# ---------------------------------------------------------------------------
# JSON helpers (shared by Claude and Opencode)
# ---------------------------------------------------------------------------

def _read_json_safe(path: Path, log: SyncLog | None = None) -> dict | None:
    """Read a JSON file, tolerating JSONC-style // line comments.

    Returns None if the file does not exist.
    Returns None (with a warning) if the file exists but cannot be parsed —
    callers must skip their update to avoid silent data loss.
    """
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    stripped = re.sub(r'(?m)^\s*//.*$', '', text)
    stripped = re.sub(r'\s*//[^"]*$', '', stripped, flags=re.MULTILINE)
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        if log:
            log.warn(f"{path.name}: could not parse JSON — skipping isolation update to avoid data loss")
        return None


def _read_state(state_path: Path) -> list[str]:
    """Read previously managed isolation glob patterns from a companion state file.

    Returns an empty list when the file does not exist or cannot be parsed.
    """
    if not state_path.exists():
        return []
    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
        return data.get("isolation-deny", [])
    except (json.JSONDecodeError, ValueError, KeyError):
        return []


def _write_state(state_path: Path, managed_patterns: list[str], dry_run: bool) -> None:
    """Write managed isolation patterns to a companion state file."""
    if dry_run:
        return
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps({"isolation-deny": managed_patterns}, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _dir_to_glob(directory: str) -> str:
    """Convert an isolation-dir path to a glob pattern.

    Examples:
      '.claude/'    → '.claude/**'
      'opencode.json' → 'opencode.json'   (exact file, no ** needed)
      'AGENTS.md'   → 'AGENTS.md'
    """
    if directory.endswith("/"):
        return directory + "**"
    return directory


# ---------------------------------------------------------------------------
# Claude: permissions.deny in .claude/settings.json
# ---------------------------------------------------------------------------

def _sync_claude_isolation(
    project_root: Path,
    foreign_dirs: list[str],
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Inject/replace provider isolation entries in .claude/settings.json.

    Tracking data (previously managed patterns) is stored in a companion file
    .claude/agent-meta-state.json to avoid polluting settings.json with unknown
    root keys — Claude Code rejects the entire file when unknown root keys are present.

    Strategy:
    - Read previously managed patterns from companion state file.
    - Read existing settings.json; skip on parse error (data-loss guard).
    - Remove old managed deny entries from permissions.deny.
    - Append new managed entries; write settings.json + state file.
    """
    settings_path = safe_path(project_root, ".claude", "settings.json")
    state_path = safe_path(project_root, _CLAUDE_STATE_FILE)

    prev_managed = _read_state(state_path)
    new_managed: list[str] = [_dir_to_glob(d) for d in foreign_dirs]

    existing = _read_json_safe(settings_path, log)
    if existing is None and settings_path.exists():
        return  # parse error — warning already emitted, skip to avoid data loss
    existing = existing or {}

    permissions = existing.setdefault("permissions", {})
    current_deny: list[str] = permissions.get("deny", [])
    user_deny = [p for p in current_deny if p not in prev_managed]
    permissions["deny"] = user_deny + new_managed

    settings_content = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
    rel_settings = ".claude/settings.json"
    rel_state = _CLAUDE_STATE_FILE

    if dry_run:
        log.action("WRITE", rel_settings, f"provider-isolation deny: {', '.join(new_managed)}")
        log.action("WRITE", rel_state, "provider-isolation state")
        return

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(settings_path, settings_content, log, rel_settings):
        log.action("WRITE", rel_settings, f"provider-isolation deny: {', '.join(new_managed)}")
    else:
        log.skip(rel_settings, "provider-isolation unchanged")
    _write_state(state_path, new_managed, dry_run)


# ---------------------------------------------------------------------------
# Opencode: permission.read + permission.edit in opencode.json
# ---------------------------------------------------------------------------

def _sync_opencode_isolation(
    project_root: Path,
    foreign_dirs: list[str],
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Inject/replace provider isolation entries in opencode.json.

    Tracking data is stored in .opencode/agent-meta-state.json to avoid
    polluting opencode.json with unknown root keys — Opencode uses Zod .strict()
    validation and rejects the entire config when unknown root keys are present.

    opencode uses last-match-wins glob permission rules.
    """
    settings_path = safe_path(project_root, "opencode.json")
    state_path = safe_path(project_root, _OPENCODE_STATE_FILE)

    prev_managed = _read_state(state_path)
    new_entries: dict[str, str] = {_dir_to_glob(d): "deny" for d in foreign_dirs}
    new_managed_keys = list(new_entries.keys())

    existing = _read_json_safe(settings_path, log)
    if existing is None and settings_path.exists():
        return  # parse error — warning already emitted, skip to avoid data loss
    existing = existing or {}

    permission = existing.setdefault("permission", {})
    read_perms: dict[str, str] = {k: v for k, v in permission.get("read", {}).items()
                                   if k not in prev_managed}
    edit_perms: dict[str, str] = {k: v for k, v in permission.get("edit", {}).items()
                                   if k not in prev_managed}
    read_perms.update(new_entries)
    edit_perms.update(new_entries)
    permission["read"] = read_perms
    permission["edit"] = edit_perms

    settings_content = json.dumps(existing, indent=2, ensure_ascii=False) + "\n"
    rel_settings = "opencode.json"
    rel_state = _OPENCODE_STATE_FILE

    if dry_run:
        log.action("WRITE", rel_settings, f"provider-isolation deny: {', '.join(new_managed_keys)}")
        log.action("WRITE", rel_state, "provider-isolation state")
        return

    settings_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(settings_path, settings_content, log, rel_settings):
        log.action("WRITE", rel_settings, f"provider-isolation deny: {', '.join(new_managed_keys)}")
    else:
        log.skip(rel_settings, "provider-isolation unchanged")
    _write_state(state_path, new_managed_keys, dry_run)


# ---------------------------------------------------------------------------
# Gemini: TOML policy file .gemini/policies/provider-isolation.toml
# ---------------------------------------------------------------------------

def _build_gemini_toml_rule(directory: str, priority_offset: int) -> str:
    """Build a single [[rule]] TOML block for a foreign directory.

    Gemini policy rules match on tool argument patterns (regex on JSON-serialised
    arguments). The argsPattern targets file_path and path keys commonly used by
    file-reading and file-writing tools.
    """
    # Escape the directory path for use as a TOML inline string and regex literal
    # Dots must be escaped in regex; slashes are literal
    pattern_dir = re.escape(directory).replace("/", "/")

    # Build the deny message — strip trailing slash for readability
    display_dir = directory.rstrip("/")
    provider_name = _guess_provider_name_from_dir(directory)

    priority = 900 + priority_offset

    lines = [
        "[[rule]]",
        'toolName = ["read_file", "write_file", "replace", "list_directory"]',
        f'argsPattern = \'"(?:file_path|path)":"[^"]*{pattern_dir}\'',
        'decision = "deny"',
        f"priority = {priority}",
        f'denyMessage = "Provider isolation: {display_dir} is managed by {provider_name} only."',
    ]
    return "\n".join(lines)


def _guess_provider_name_from_dir(directory: str) -> str:
    """Infer the owning provider name from the directory path."""
    d = directory.lower().rstrip("/")
    if ".claude" in d:
        return "Claude Code"
    if ".gemini" in d:
        return "Gemini CLI"
    if ".opencode" in d or "opencode" in d or "agents.md" in d:
        return "Opencode"
    if ".continue" in d:
        return "Continue"
    return "another provider"


def _sync_gemini_isolation(
    project_root: Path,
    foreign_dirs: list[str],
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Generate .gemini/policies/provider-isolation.toml with one rule per foreign dir."""
    target_path = safe_path(project_root, _GEMINI_ISOLATION_FILE)
    rel = _GEMINI_ISOLATION_FILE

    rule_blocks = []
    for idx, d in enumerate(foreign_dirs):
        rule_blocks.append(_build_gemini_toml_rule(d, idx))

    content_lines = [
        "# agent-meta managed — do not edit manually",
        "# Generated by sync.py — provider isolation rules for Gemini CLI",
        "# One [[rule]] block per foreign provider directory.",
        "",
    ]
    content_lines.extend("\n".join(rule_blocks[i:i+1]) for i in range(len(rule_blocks)))
    content = "\n\n".join(content_lines[:4] + rule_blocks) + "\n"

    if dry_run:
        log.action("WRITE", rel, f"provider-isolation ({len(foreign_dirs)} rule(s))")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(target_path, content, log, rel):
        log.action("WRITE", rel, f"provider-isolation ({len(foreign_dirs)} rule(s))")
    else:
        log.skip(rel, "provider-isolation unchanged")


# ---------------------------------------------------------------------------
# Continue: soft rule .continue/rules/provider-isolation.md
# ---------------------------------------------------------------------------

def _sync_continue_isolation(
    project_root: Path,
    foreign_dirs: list[str],
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Generate .continue/rules/provider-isolation.md (soft guidance, no native hard block)."""
    target_path = safe_path(project_root, _CONTINUE_ISOLATION_FILE)
    rel = _CONTINUE_ISOLATION_FILE

    # Build list items grouped by provider
    dir_lines = []
    for d in foreign_dirs:
        provider_name = _guess_provider_name_from_dir(d)
        display = d.rstrip("/")
        dir_lines.append(f"- `{display}` — {provider_name} only")

    dirs_block = "\n".join(dir_lines)

    content = (
        "# Provider Isolation\n"
        "\n"
        "This project uses multiple AI providers. Do not read or write files in directories\n"
        "managed by other providers:\n"
        "\n"
        f"{dirs_block}\n"
        "\n"
        "Only read files in your own provider directory (`.continue/`) unless explicitly\n"
        "asked by the user to inspect another provider's configuration.\n"
        "\n"
        "<!-- agent-meta managed — do not edit manually -->\n"
    )

    if dry_run:
        log.action("WRITE", rel, f"provider-isolation ({len(foreign_dirs)} dir(s))")
        return

    target_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(target_path, content, log, rel):
        log.action("WRITE", rel, f"provider-isolation ({len(foreign_dirs)} dir(s))")
    else:
        log.skip(rel, "provider-isolation unchanged")
