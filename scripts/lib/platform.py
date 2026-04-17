"""Platform-config loading and substitution for {{platform.*}} placeholders."""

import re
from pathlib import Path

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
    try:
        import yaml as _yaml
    except ImportError:
        log.warn(
            'PyYAML not available — platform-config substitution skipped. '
            'Install it with: pip install pyyaml'
        )
        return {}

    merged_flat: dict = {}

    # Load project overrides once — shared across all platforms
    project_config_path = project_root / CLAUDE_PLATFORM_CONFIG
    overrides_flat: dict = {}
    if project_config_path.exists():
        try:
            with project_config_path.open(encoding='utf-8') as f:
                overrides_flat = _flatten_yaml_dict(_yaml.safe_load(f) or {})
        except Exception as e:
            log.warn(f'platform-config: failed to load {CLAUDE_PLATFORM_CONFIG}: {e}')

    for platform in platforms:
        defaults_path = agent_meta_root / PLATFORM_CONFIGS_DIR / f'{platform}.defaults.yaml'
        if not defaults_path.exists():
            # No defaults file for this platform — skip silently (not all platforms need one)
            continue

        try:
            with defaults_path.open(encoding='utf-8') as f:
                defaults_raw = _yaml.safe_load(f) or {}
        except Exception as e:
            log.warn(f'platform-config: failed to load {defaults_path.name}: {e}')
            continue

        # Merge: defaults first, then overrides win
        platform_flat = {**_flatten_yaml_dict(defaults_raw), **overrides_flat}

        # Warn for required fields (empty-string default) that are still empty
        for key, val in platform_flat.items():
            if key.startswith(f'platform.{platform}.') and val == '':
                log.warn(
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
        log.warn(
            f'platform-config: placeholder {{{{{raw_key}}}}} not found in platform defaults '
            f'or project overrides — placeholder remains in: {source_label}'
        )
        return match.group(0)

    return _PLATFORM_VAR_RE.sub(replacer, text)
