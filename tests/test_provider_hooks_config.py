"""Regression test: every provider with has_hooks/has_settings true must have
its own hooks_dir/settings_file, not silently fall back to Claude's paths.

Run: python -m pytest tests/test_provider_hooks_config.py -v
"""

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PROVIDERS_CONFIG = _REPO_ROOT / "config" / "ai-providers.yaml"


def _load_providers() -> dict:
    with _PROVIDERS_CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_mammouth_has_its_own_hooks_dir_and_settings_file():
    """Without an explicit hooks_dir/settings_file, sync_hooks()/
    _init_provider_settings_json() silently default to Claude's paths
    (.claude/hooks, .claude/settings.json) — Mammouth must not collide with Claude.
    """
    providers = _load_providers()["providers"]
    mammouth = providers["Mammouth"]
    claude = providers["Claude"]
    assert mammouth.get("has_hooks") is True
    assert mammouth.get("hooks_dir") == ".mammouth/hooks"
    assert mammouth.get("settings_file") == ".mammouth/settings.json"
    assert mammouth["hooks_dir"] != claude.get("hooks_dir", ".claude/hooks")
    assert mammouth["settings_file"] != claude["settings_file"]
