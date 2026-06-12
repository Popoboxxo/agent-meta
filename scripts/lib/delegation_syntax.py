"""Provider Abstraction Layer — Delegation Syntax Engine.

Lädt config/delegation-syntax.yaml und substituiert abstrakte
{{PAL_*}} Platzhalter in Templates durch provider-spezifische Syntax.

Usage:
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine

    engine = DelegationSyntaxEngine()
    processed = engine.apply(content, provider="Gemini")
"""

import re
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


class DelegationSyntaxEngine:
    """Substitutes abstract delegation placeholders with provider-specific syntax."""

    PLACEHOLDERS: dict[str, str] = {
        "PAL_DELEGATE": "delegate",
        "PAL_FANOUT": "fanout",
        "PAL_PARALLEL_GROUP": "parallel_group",
        "PAL_FALLBACK": "fallback",
        "PAL_TOOL_PREAMBLE": "tool_preamble",
        "PAL_PARALLEL_PATTERN": "parallel_pattern",
        "PAL_HANDOFF": "handoff",
    }

    def __init__(self, config_dir: Path | None = None) -> None:
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        self.config_dir = config_dir
        self._syntax_registry: dict[str, Any] | None = None
        self._capabilities_registry: dict[str, Any] | None = None

    @property
    def syntax_registry(self) -> dict[str, Any]:
        if self._syntax_registry is None:
            path = self.config_dir / "delegation-syntax.yaml"
            try:
                with open(path, encoding="utf-8") as f:
                    if yaml is not None:
                        self._syntax_registry = yaml.safe_load(f)
                    else:
                        self._syntax_registry = {}
            except (FileNotFoundError, yaml.YAMLError) as e:
                self._syntax_registry = {}
        return self._syntax_registry or {}

    @property
    def capabilities_registry(self) -> dict[str, Any]:
        if self._capabilities_registry is None:
            path = self.config_dir / "provider-capabilities.yaml"
            try:
                with open(path, encoding="utf-8") as f:
                    if yaml is not None:
                        self._capabilities_registry = yaml.safe_load(f)
                    else:
                        self._capabilities_registry = {}
            except (FileNotFoundError, yaml.YAMLError) as e:
                self._capabilities_registry = {}
        return self._capabilities_registry or {}

    def get_syntax(self, provider: str) -> dict[str, Any]:
        """Return the delegation syntax map for a provider."""
        return self.syntax_registry.get("delegation_syntax", {}).get(provider, {})

    def get_capabilities(self, provider: str) -> dict[str, Any]:
        """Return capabilities for a provider."""
        return self.capabilities_registry.get("capabilities", {}).get(provider, {})

    def apply(self, content: str, provider: str, log=None) -> str:
        """Apply provider-specific syntax to abstract placeholders in content.

        1. Evaluates {{#if PAL_*}}...{{/if}} blocks against this provider's
           syntax values ("false"/empty → block removed, anything else → kept).
        2. Replaces {{PAL_*}} placeholders with the native syntax defined
           for the given provider. Removes any remaining PAL placeholders.

        log: optional SyncLog — warns when content references a PAL placeholder
        that has no definition for this provider (likely a config gap).
        """
        syntax = self.get_syntax(provider)

        def eval_conditional(m: re.Match) -> str:
            syntax_key = self.PLACEHOLDERS.get(m.group(1), "")
            value = syntax.get(syntax_key, "")
            active = isinstance(value, str) and value.strip().lower() not in ("", "false")
            if not active:
                return ""
            return m.group(2).strip("\n") + "\n"

        content = re.sub(
            r"\{\{#if (PAL_[A-Z_]+)\}\}\n?(.*?)\{\{/if\}\}\n?",
            eval_conditional, content, flags=re.DOTALL,
        )

        for placeholder, syntax_key in self.PLACEHOLDERS.items():
            pattern = r"\{\{" + re.escape(placeholder) + r"\}\}"
            replacement = syntax.get(syntax_key, "")
            if not isinstance(replacement, str):
                replacement = ""
            if log is not None and not replacement and re.search(pattern, content):
                log.warn(
                    f"PAL: '{placeholder}' has no definition for provider "
                    f"'{provider}' — placeholder removed (check config/delegation-syntax.yaml)"
                )
            content = re.sub(pattern, lambda _m: replacement, content)

        # Remove any remaining {{PAL_*}} placeholders (no-ops for this provider)
        leftover = set(re.findall(r"\{\{(PAL_[A-Z_]+)\}\}", content))
        if log is not None:
            for name in sorted(leftover):
                log.warn(
                    f"PAL: unknown placeholder '{{{{{name}}}}}' for provider "
                    f"'{provider}' — removed (not in DelegationSyntaxEngine.PLACEHOLDERS)"
                )
        content = re.sub(r"\{\{PAL_[A-Z_]+\}\}", "", content)

        # Remove PAL_PREFIX: markers (used in templates to mark PAL-dependent sections)
        content = re.sub(r"PAL_PREFIX:\w+\s*\n", "", content)

        return content

    def needs_bootstrap(self, provider: str) -> bool:
        """Check if provider needs session bootstrap."""
        caps = self.get_capabilities(provider)
        return caps.get("bootstrap_required", False)

    def has_native_subagent_dispatch(self, provider: str) -> bool:
        """Check if provider has native subagent dispatch tools."""
        caps = self.get_capabilities(provider)
        return caps.get("subagent_dispatch", False)

    def has_file_based_agents(self, provider: str) -> bool:
        """Check if provider uses file-based agent discovery."""
        caps = self.get_capabilities(provider)
        return caps.get("file_based_agents", False)
