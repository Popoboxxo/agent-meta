"""Provider configuration loading and resolution."""
from __future__ import annotations

from pathlib import Path

from .io import _load_yaml_or_json, load_yaml_file

PROVIDERS_CONFIG_YAML = "config/ai-providers.yaml"
_PROVIDERS_CONFIG_LEGACY = "providers.config.yaml"
_PROVIDERS_CONFIG_JSON = "providers.config.json"
PROVIDER_CAPABILITIES_YAML = "config/provider-capabilities.yaml"  # legacy fallback


def resolve_agent_meta_root(project_root: Path) -> Path:
    """Resolve the agent-meta framework root from a project root.

    agent-meta is embedded in downstream projects as a ``.agent-meta/``
    submodule, but self-hosts inside its own checkout. Mirrors the layout
    detection every other asset lookup uses (admin-server ServiceContext.
    agent_meta_root, viz-report, consistency-check):

    1. ``project_root`` itself when it is a framework checkout
       (``agents/1-generic`` present) — self-hosting / super-admin.
    2. ``project_root/.agent-meta`` when that is a framework checkout —
       submodule layout in a downstream project.
    3. ``project_root`` as a last-resort fallback.

    Without this, a caller that omits ``agent_meta_root`` silently reads
    provider config from the PROJECT root, finds none, falls back to the
    embedded Claude-only default and mis-classifies a hook-less provider as
    Tier A (issue: live-progress-channel PR #721, Finding 1).
    """
    project_root = Path(project_root)
    if (project_root / "agents" / "1-generic").is_dir():
        return project_root
    submodule = project_root / ".agent-meta"
    if (submodule / "agents" / "1-generic").is_dir():
        return submodule
    return project_root


def load_providers_config(agent_meta_root: Path) -> dict:
    """Load config/ai-providers.yaml with fallback to legacy paths."""
    data, _ = _load_yaml_or_json(
        agent_meta_root / PROVIDERS_CONFIG_YAML,
        agent_meta_root / _PROVIDERS_CONFIG_LEGACY,
        agent_meta_root / _PROVIDERS_CONFIG_JSON,
    )
    if not data:
        # Minimal fallback — fires only when ai-providers.yaml is missing
        # entirely. Mirrors *most* of the current Claude provider schema
        # (identity, capability flags, `capabilities` list,
        # `model-tiers`/`model-aliases`) so downstream code that reads e.g. caps
        # or tiers does not trip over partial data. Five fields are intentionally
        # absent (#492): `orchestrator_hint`, `settings_local_file`,
        # `settings_local_template`, `isolation-dirs`, `mcp-config`. Every read
        # site uses `.get()` defaults, so the gap degrades gracefully (MCP stays
        # disabled, the generic orchestrator_hint applies) instead of crashing.
        # Keeping field names in sync with config/ai-providers.yaml::Claude
        # remains a manual convention, not enforced.
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


def load_provider_capabilities(agent_meta_root: Path) -> dict:
    """Load the `capabilities:` block of config/provider-capabilities.yaml.

    Framework config; a missing or malformed file yields ``{}`` (optional-file
    semantics — callers fall back to ai-providers.yaml).
    """
    data = load_yaml_file(
        agent_meta_root / PROVIDER_CAPABILITIES_YAML,
        on_error="default",
        default={},
    )
    if not isinstance(data, dict):
        return {}
    caps = data.get("capabilities", {})
    return caps if isinstance(caps, dict) else {}


def provider_has_capability(pc: dict | None, capability: str) -> bool:
    """True when a provider's config/ai-providers.yaml ``capabilities`` list
    declares ``capability`` (issue #735).

    The provider-agnostic replacement for per-dimension
    ``if provider == "Name"`` checks. An absent entry or an absent provider is
    an explicit ``False`` — never a silent Claude fallback.
    """
    return capability in ((pc or {}).get("capabilities") or [])


def provider_commands_supported(caps: dict | None) -> bool:
    """Whether slash-commands sync is enabled for a provider (issue #735).

    ``caps`` is the provider's entry from config/provider-capabilities.yaml
    (see ``load_provider_capabilities``). Only an explicit ``commands: true``
    enables the path; absent or false is an explicit "unsupported" that
    scripts/lib/commands.py reports, instead of silently returning — the old
    silent else-branch is what left 5/9 providers without any commands.
    """
    return (caps or {}).get("commands") is True


def registered_provider_names(agent_meta_root: Path) -> list[str]:
    """Return the canonical, sorted provider registry (issue #732).

    Union of the provider names declared in ``config/provider-capabilities.yaml``
    and ``config/ai-providers.yaml`` — the two framework registries kept in
    sync by tests/test_provider_three_file_invariant.py. Consumed by schema
    generation (schema.update_providers_enum) and load-time validation
    (config._validate_providers).
    """
    names = set(load_provider_capabilities(agent_meta_root).keys())
    names.update(load_providers_config(agent_meta_root).keys())
    return sorted(names)


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
    registered = set(provider_config)

    def _reject(value: object, field: str) -> None:
        # Issue #732: an unknown provider used to be silently dropped, which
        # then fell back to Claude. Fail loud instead of producing a silent
        # Claude run (load_config._validate_providers catches this earlier for
        # the normal sync path; this guards direct resolve_providers() callers).
        raise ValueError(
            f"Unknown provider {value!r} in '{field}' — registered providers: "
            f"{', '.join(sorted(registered)) or '(none)'}. "
            "Use a provider from config/provider-capabilities.yaml."
        )

    providers: list[str] = []
    if "ai-providers" in config:
        raw = config["ai-providers"]
        if isinstance(raw, list):
            for item in raw:
                if not isinstance(item, str) or item not in registered:
                    _reject(item, "ai-providers")
            providers = list(raw)
        elif isinstance(raw, str):
            if raw not in registered:
                _reject(raw, "ai-providers")
            providers = [raw]

    if not providers and "ai-provider" in config:
        p = config["ai-provider"]
        if isinstance(p, str):
            if p not in registered:
                _reject(p, "ai-provider")
            providers = [p]

    if not providers:
        default_provider = config.get("default-provider", "Claude")
        if default_provider not in registered:
            _reject(default_provider, "default-provider")
        providers = [default_provider]

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
        provider: The provider name (e.g. "Claude", "Opencode"). Kept for
            signature compatibility; behavior is resolved solely from `pc`
            (issue #735 — no `provider == "Claude"` fallback).
        pc: This provider's config/ai-providers.yaml entry, if available.

    Returns:
        "AGENTS.md" if `context_file == "CLAUDE.md"` and the provider has no
        dedicated context file, otherwise `context_file` unchanged.
    """
    has_dedicated = (pc or {}).get("has_dedicated_context_file", False)
    if context_file == "CLAUDE.md" and not has_dedicated:
        return "AGENTS.md"
    return context_file


# Hook event/payload contracts sync.py knows how to mirror hook scripts for.
# hooks/1-generic/*.sh are written against exactly one contract today (JSON on
# stdin, PreToolUse/PostToolUse, exit-code-2-blocks) — see ai-providers.yaml's
# `hook_protocol` field comment (issue #630).
#
# `antigravity-hooks-json` (issue #674 Phase 3.1): Google Antigravity's
# hooks.json contract (verified 2026-09 against antigravity.google/docs/hooks).
# It deviates from the Claude contract in three verified ways — registration
# artifact (hooks.json at the workspace .agents/ location, hook-name-keyed
# schema — NOT settings.json), stdin payload keys (hookEventName/
# toolCall.{name,args} camelCase, no cwd) and output semantics ({"decision":
# "deny", "reason"} JSON on stdout instead of exit-code-2 + stderr) — so it is
# a dedicated protocol value, not a claude-code-json alias. hooks/1-generic/
# antigravity-json-adapter.sh translates between the two contracts at runtime.
SUPPORTED_HOOK_PROTOCOLS = {"claude-code-json", "antigravity-hooks-json"}


def provider_hooks_supported(pc: dict) -> bool:
    """Whether a provider's hooks should actually be synced/mirrored.

    `has_hooks: true` alone only records that a hooks_dir/settings_file path
    is configured for the provider — it does NOT mean the provider's hook
    event/payload model is verified to match the contract hooks/1-generic/
    scripts are written against. Only providers with a `hook_protocol` in
    `SUPPORTED_HOOK_PROTOCOLS` get hooks mirrored (issue #630).
    """
    return bool(pc.get("has_hooks", False)) and pc.get("hook_protocol") in SUPPORTED_HOOK_PROTOCOLS


def all_providers_support_hooks(active: list, provider_config: dict) -> bool:
    """Tier-A gate: True only when the active set is non-empty AND every
    active provider has a verified hook_protocol (provider_hooks_supported).

    Single source of truth for the "Tier A iff all active providers support
    hooks" rule, shared by the runtime tier decision (checkpoint._progress_tier)
    and the sync-time PROGRESS_CHAT_PUSH_ENABLED variable
    (config._build_orch_variables) — see the live-progress-channel design doc
    2026-09-10, Architecture §1. A mixed Tier-A/Tier-B provider set returns
    False so no hook-less provider silently loses its only progress signal.
    """
    return bool(active) and all(
        provider_hooks_supported(provider_config.get(p, {})) for p in active
    )


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
