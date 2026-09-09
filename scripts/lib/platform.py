"""Platform-config loading and substitution for {{platform.*}} placeholders."""
from __future__ import annotations

import re
from pathlib import Path

from .frontmatter import _YAML_AVAILABLE
from .io import load_yaml_file
from .log import SyncLog

PLATFORM_CONFIGS_DIR = "platform-configs"
CLAUDE_PLATFORM_CONFIG = ".claude/platform-config.yaml"
_PLATFORM_VAR_RE = re.compile(r'\{\{(platform\.[^}]+)\}\}')


def _flatten_yaml_dict(d: dict, prefix: str = '') -> dict:
    """Flatten a nested dict into dot-notation keys.

    Example:
        {'platform': {'homeassistant': {'notify_group': 'all'}}}
        -> {'platform.homeassistant.notify_group': 'all'}
    """
    result = {}
    for k, v in d.items():
        key = f'{prefix}.{k}' if prefix else k
        if isinstance(v, dict):
            result.update(_flatten_yaml_dict(v, key))
        else:
            result[key] = v
    return result


def load_platform_config(
    agent_meta_root: Path,
    project_root: Path,
    platforms: list[str],
    log: 'SyncLog',
) -> dict:
    """Load and merge platform-config for all active platforms.

    For each platform in platforms:
      1. Load agent-meta/platform-configs/<platform>.defaults.yaml   (defaults)
      2. Load .claude/platform-config.yaml from project root          (overrides, optional)
      3. Merge: project overrides win over defaults
      4. Flatten nested YAML keys to dot-notation

    Returns a flat dict: {'platform.homeassistant.notify_group': 'all', ...}

    Emits [WARN] for:
      - Required fields (empty-string default) not overridden by project
      - {{platform.*}} placeholders in source files without a matching config entry
        (checked externally via warn_unresolved_platform_vars)
    """
    if not _YAML_AVAILABLE:
        log.warning(
            'PyYAML not available — platform-config substitution skipped. '
            'Install it with: pip install pyyaml'
        )
        return {}

    merged_flat: dict = {}

    # Load project overrides once — shared across all platforms. The canonical
    # single-file loader (Issue #479) with on_error="warn" keeps the old
    # warn-and-continue behavior; default=None acts as the failure sentinel
    # so a broken overrides file still leaves overrides_flat at {} exactly
    # as before (message wording is unified to the loader's SyncError-style
    # text — accepted per the #479 migration matrix).
    project_config_path = project_root / CLAUDE_PLATFORM_CONFIG
    loaded_overrides: dict | None = load_yaml_file(
        project_config_path, on_error="warn", default=None, log=log,
    )
    overrides_flat: dict = {} if loaded_overrides is None else _flatten_yaml_dict(loaded_overrides)

    for platform in platforms:
        defaults_path = agent_meta_root / PLATFORM_CONFIGS_DIR / f'{platform}.defaults.yaml'
        if not defaults_path.exists():
            # No defaults file for this platform — skip silently (not all platforms need one)
            continue

        defaults_raw = load_yaml_file(
            defaults_path, on_error="warn", default=None, log=log,
        )
        if defaults_raw is None:
            # Malformed/unreadable defaults file — this platform contributes
            # nothing (old behavior: warn + continue).
            continue

        # Merge: defaults first, then overrides win
        platform_flat = {**_flatten_yaml_dict(defaults_raw), **overrides_flat}

        # Warn for required fields (empty-string default) that are still empty
        for key, val in platform_flat.items():
            if key.startswith(f'platform.{platform}.') and val == '':
                log.warning(
                    f'platform-config: required field {{{{platform.{key[len("platform."):]}}}}}'
                    f' is empty -- add it to .claude/platform-config.yaml'
                )

        merged_flat.update(platform_flat)

    return merged_flat


def substitute_platform(
    text: str,
    platform_vars: dict,
    source_label: str,
    log: 'SyncLog',
) -> str:
    """Replace {{platform.*}} occurrences using platform_vars dict.

    Keys in platform_vars use dot-notation (e.g. 'platform.homeassistant.notify_group').
    Placeholders in text look like {{platform.homeassistant.notify_group}}.

    Warns for any {{platform.*}} placeholder that has no matching key in platform_vars.
    Does NOT touch {{UPPERCASE}} placeholders — those are handled by substitute().
    """
    def replacer(match):
        raw_key = match.group(1)   # e.g. 'platform.homeassistant.notify_group'
        if raw_key in platform_vars:
            return str(platform_vars[raw_key])
        log.warning(
            f'platform-config: placeholder {{{{{raw_key}}}}} not found in platform defaults '
            f'or project overrides — placeholder remains in: {source_label}'
        )
        return match.group(0)

    return _PLATFORM_VAR_RE.sub(replacer, text)


# Fields whose "+"-suffixed variant should be JOINED (not just overridden)
# when more than one platform in `platforms:` sets it. Command-like fields
# default to "&&" (matches the existing "cmd-a && cmd-b" convention already
# used for TEST_COMMANDS in this repo's templates/examples); free-text
# fields get an explicit, more readable join character. Per-field, not
# global (design spec "Offene Implementierungs-Punkte" §3).
_ADDITIVE_JOIN: dict[str, str] = {
    "CODE_CONVENTIONS": "; ",
}


def resolve_platform_defaults(
    platforms: list[str], platform_config_dir: 'Path | None' = None,
) -> dict:
    """Merge dod-preset/conventions-preset/variables across every active
    platform's platform-configs/<name>.defaults.yaml (Task 1's new sections).

    Single pass over `platforms` in list order -- for each platform's
    `variables` entries:
      - a plain key (no `+`) REPLACES whatever the field currently holds
        (from an earlier platform's plain key OR an earlier platform's `+`
        chain) -- "<FIELD> ersetzt komplett" (design spec).
      - a `<FIELD>+` key APPENDS onto whatever the field currently holds,
        using _ADDITIVE_JOIN.get(FIELD, " && ") as the join string; if
        nothing is held yet, it simply becomes the field's value (no
        leading join string) -- "<FIELD>+ hängt an" (design spec).
    Top-level `dod-preset`/`conventions-preset` scalars follow the same
    last-platform-wins rule as plain variables.

    A platform without a matching platform-configs/<name>.defaults.yaml
    file (or an unreadable/malformed one) contributes nothing and is not an
    error -- mirrors load_platform_config()'s "not all platforms need one,
    skip silently" contract (this module, L77-79/84-87).

    platform_config_dir defaults to <agent-meta repo root>/platform-configs
    -- derived from this file's own location (three parents up: lib -> scripts
    -> repo root), a convenience default for callers that don't already
    thread an explicit agent_meta_root (unlike load_platform_config()/
    resolve_dod()/resolve_conventions(), which always receive agent_meta_root
    explicitly and should pass `agent_meta_root / PLATFORM_CONFIGS_DIR` here
    rather than relying on this default).

    Returns {"dod-preset": str | None, "conventions-preset": str | None,
             "variables": dict[str, str]}.
    """
    if platform_config_dir is None:
        platform_config_dir = Path(__file__).resolve().parent.parent.parent / PLATFORM_CONFIGS_DIR

    result: dict = {"dod-preset": None, "conventions-preset": None, "variables": {}}

    for platform in platforms:
        defaults_path = platform_config_dir / f'{platform}.defaults.yaml'
        raw = load_yaml_file(defaults_path, on_error="default", default={})
        if not raw:
            continue

        if "dod-preset" in raw:
            result["dod-preset"] = raw["dod-preset"]
        if "conventions-preset" in raw:
            result["conventions-preset"] = raw["conventions-preset"]

        platform_vars = raw.get("variables", {})
        if not isinstance(platform_vars, dict):
            continue
        for key, value in platform_vars.items():
            if key.endswith("+"):
                field = key[:-1]
                base = result["variables"].get(field, "")
                join_char = _ADDITIVE_JOIN.get(field, " && ")
                result["variables"][field] = f"{base}{join_char}{value}" if base else str(value)
            else:
                result["variables"][key] = value

    return result
