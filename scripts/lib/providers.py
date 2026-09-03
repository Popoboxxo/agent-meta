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
                "has_dedicated_context_file": True,
                "has_rules": True,
                "has_hooks": True,
                "hook_protocol": "claude-code-json",
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

    Falls back to config["default-provider"] if neither key is set (issue #631)
    -- itself defaulting to "Claude" for backward compatibility, but expressed
    as an explicit, overridable config key instead of a hardcoded literal.

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
        default_provider = config.get("default-provider", "Claude")
        providers = [default_provider] if default_provider in provider_config else ["Claude"]

    if filter_deactivated:
        dc = config.get("provider-deactivation", {})
        if dc.get("enabled", False):
            mode = dc.get("mode", "all")
            if mode == "all":
                return []
            deactivated = set(dc.get("providers", []) if isinstance(dc.get("providers"), list) else [])
            providers = [p for p in providers if p not in deactivated]

    return providers


def resolve_context_filename(context_file: str, provider: str, pc: dict | None = None) -> str:
    """Resolve the effective context filename for a provider.

    Providers that still resolve to the default "CLAUDE.md" (i.e. they have
    no explicit `context_file` override in config/ai-providers.yaml) AND
    don't have their own dedicated context file fall back to "AGENTS.md"
    instead — e.g. Opencode/Gemini-style providers share a generic context
    file rather than a Claude-specific one.

    Driven by the `has_dedicated_context_file` capability flag (issue #631)
    instead of a literal `provider != "Claude"` check -- Claude is the only
    provider with that flag set today, but any future provider with its own
    dedicated context-file handling (like Claude's sync_claude_md_static())
    can opt in via config/ai-providers.yaml alone, no code change needed.

    Args:
        context_file: The raw context filename, e.g. from
            `provider_config[provider].get("context_file", f"{provider.upper()}.md")`.
        provider: The provider name (e.g. "Claude", "Opencode"), used only
            when `pc` is not supplied (falls back to `provider == "Claude"`
            for callers that haven't been updated to pass `pc` yet).
        pc: This provider's config/ai-providers.yaml entry, if available.

    Returns:
        "AGENTS.md" if `context_file == "CLAUDE.md"` and the provider has no
        dedicated context file, otherwise `context_file` unchanged.
    """
    has_dedicated = (
        pc.get("has_dedicated_context_file", False) if pc is not None
        else provider == "Claude"
    )
    if context_file == "CLAUDE.md" and not has_dedicated:
        return "AGENTS.md"
    return context_file


# Hook event/payload contracts sync.py knows how to mirror hook scripts for.
# hooks/1-generic/*.sh are written against exactly one contract today (JSON on
# stdin, PreToolUse/PostToolUse, exit-code-2-blocks) — see ai-providers.yaml's
# `hook_protocol` field comment (issue #630).
SUPPORTED_HOOK_PROTOCOLS = {"claude-code-json"}


def provider_hooks_supported(pc: dict) -> bool:
    """Whether a provider's hooks should actually be synced/mirrored.

    `has_hooks: true` alone only records that a hooks_dir/settings_file path
    is configured for the provider — it does NOT mean the provider's hook
    event/payload model is verified to match the contract hooks/1-generic/
    scripts are written against. Only providers with a `hook_protocol` in
    `SUPPORTED_HOOK_PROTOCOLS` get hooks mirrored (issue #630).
    """
    return bool(pc.get("has_hooks", False)) and pc.get("hook_protocol") in SUPPORTED_HOOK_PROTOCOLS


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
