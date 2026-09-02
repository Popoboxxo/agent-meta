"""Provider configuration loading and resolution."""

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
        # Minimal-but-schema-complete fallback — used only if ai-providers.yaml is
        # missing entirely. Mirrors the current Claude provider schema (identity,
        # capability flags, `capabilities` list, `model-tiers`/`model-aliases`) so
        # downstream code that reads e.g. caps or tiers does not trip over partial
        # data. Keep field names in sync with config/ai-providers.yaml::Claude.
        return {
            "Claude": {
                "agents_dir": ".claude/agents",
                "agent_ext": ".md",
                "context_file": "CLAUDE.md",
                "context_template": "templates/configs/CLAUDE.project-template.md",
                "has_rules": True,
                "has_hooks": True,
                "has_commands": True,
                "has_settings": True,
                "capabilities": [
                    "agents",
                    "rules",
                    "hooks",
                    "commands",
                    "settings",
                    "snippets",
                    "skills",
                    "context-managed-block",
                    "artifacts",
                    "checkpoints",
                    "mcp",
                ],
                "artifact_dir": ".claude/artifacts",
                "checkpoint_dir": ".meta-viz",
                "settings_file": ".claude/settings.json",
                "settings_template": "templates/configs/CLAUDE.settings-template.json",
                "skills_dir": ".claude/skills",
                "snippets_dir": ".claude/snippets",
                "pending_tasks_file": ".claude/pending-tasks.md",
                "extension_dir": ".claude/3-project",
                "gitignore_entries": [
                    ".claude/settings.local.json",
                    ".claude/agent-memory-local/",
                    ".claude/pending-tasks.md",
                    "CLAUDE.personal.md",
                    "sync.log",
                    ".mcp.json",
                ],
                "model-tiers": {
                    "nano": "claude-haiku-4-5-20251001",
                    "fast": "claude-haiku-4-5-20251001",
                    "balanced": "claude-sonnet-5",
                    "powerful": "claude-opus-4-8",
                    "max": "claude-fable-5",
                },
                "model-aliases": {
                    "haiku": "claude-haiku-4-5-20251001",
                    "sonnet": "claude-sonnet-4-6",
                    "opus": "claude-opus-4-8",
                    "fable": "claude-fable-5",
                },
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


def resolve_context_filename(context_file: str, provider: str) -> str:
    """Resolve the effective context filename for a provider.

    Non-Claude providers that still resolve to the default "CLAUDE.md"
    (i.e. they have no explicit `context_file` override in
    config/ai-providers.yaml) fall back to "AGENTS.md" instead — e.g.
    Opencode/Gemini-style providers share a generic context file rather
    than a Claude-specific one.

    Args:
        context_file: The raw context filename, e.g. from
            `provider_config[provider].get("context_file", f"{provider.upper()}.md")`.
        provider: The provider name (e.g. "Claude", "Opencode").

    Returns:
        "AGENTS.md" if `context_file == "CLAUDE.md"` and `provider != "Claude"`,
        otherwise `context_file` unchanged.
    """
    if context_file == "CLAUDE.md" and provider != "Claude":
        return "AGENTS.md"
    return context_file


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
