"""Provider configuration loading and resolution."""

import sys
from pathlib import Path

from .io import _load_yaml_or_json

PROVIDERS_CONFIG_YAML = "config/ai-providers.yaml"
_PROVIDERS_CONFIG_LEGACY = "providers.config.yaml"
_PROVIDERS_CONFIG_JSON = "providers.config.json"  # legacy fallback


def load_providers_config(agent_meta_root: Path) -> dict:
    """Load config/ai-providers.yaml with fallback to legacy paths."""
    data, _ = _load_yaml_or_json(
        agent_meta_root / PROVIDERS_CONFIG_YAML,
        agent_meta_root / _PROVIDERS_CONFIG_LEGACY,
        agent_meta_root / _PROVIDERS_CONFIG_JSON,
    )
    if not data:
        # Minimal fallback — keeps backward compat if providers.config.yaml is missing
        return {
            "Claude": {
                "agents_dir": ".claude/agents",
                "agent_ext": ".md",
                "context_file": "CLAUDE.md",
                "context_template": "templates/configs/CLAUDE.project-template.md",
                "has_rules": True,
                "has_hooks": True,
                "has_settings": True,
                "settings_file": ".claude/settings.json",
                "gitignore_entries": [
                    ".claude/settings.local.json",
                    ".claude/agent-memory-local/",
                    "CLAUDE.personal.md",
                    "sync.log",
                ],
            }
        }
    return data.get("providers", data)


def resolve_providers(config: dict, provider_config: dict, filter_deactivated: bool = True) -> list:
    """Resolve active AI providers from config.

    Supports:
    - "ai-providers": ["Claude", "Gemini"]  (new multi-provider)
    - "ai-provider":  "Claude"               (legacy, backward-compat)

    Falls back to ["Claude"] if neither key is set.

    When filter_deactivated is True (default), providers marked as deactivated in
    provider-deactivation config are excluded.
    """
    providers: list[str] = []
    if "ai-providers" in config:
        raw = config["ai-providers"]
        if isinstance(raw, list):
            providers = [p for p in raw if p in provider_config]
        elif isinstance(raw, str) and raw in provider_config:
            providers = [raw]

    if not providers and "ai-provider" in config:
        p = config["ai-provider"]
        if isinstance(p, str) and p in provider_config:
            providers = [p]

    if not providers:
        providers = ["Claude"]

    if filter_deactivated:
        dc = config.get("provider-deactivation", {})
        if dc.get("enabled", False):
            mode = dc.get("mode", "all")
            if mode == "all":
                return []
            deactivated = set(dc.get("providers", []) if isinstance(dc.get("providers"), list) else [])
            providers = [p for p in providers if p not in deactivated]

    return providers


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
