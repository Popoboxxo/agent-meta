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

import yaml


class DelegationSyntaxEngine:
    """Substitutes abstract delegation placeholders with provider-specific syntax."""

    PLACEHOLDERS: dict[str, str] = {
        "PAL_DELEGATE": "delegate",
        "PAL_FANOUT": "fanout",
        "PAL_PARALLEL_GROUP": "parallel_group",
        "PAL_FALLBACK": "fallback",
        "PAL_TOOL_PREAMBLE": "tool_preamble_section",
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
            with open(path) as f:
                self._syntax_registry = yaml.safe_load(f)
        return self._syntax_registry or {}

    @property
    def capabilities_registry(self) -> dict[str, Any]:
        if self._capabilities_registry is None:
            path = self.config_dir / "provider-capabilities.yaml"
            with open(path) as f:
                self._capabilities_registry = yaml.safe_load(f)
        return self._capabilities_registry or {}

    def get_syntax(self, provider: str) -> dict[str, Any]:
        """Return the delegation syntax map for a provider."""
        return self.syntax_registry.get("delegation_syntax", {}).get(provider, {})

    def get_capabilities(self, provider: str) -> dict[str, Any]:
        """Return capabilities for a provider."""
        return self.capabilities_registry.get("capabilities", {}).get(provider, {})

    def apply(self, content: str, provider: str) -> str:
        """Apply provider-specific syntax to abstract placeholders in content.

        Replaces {{PAL_*}} placeholders with the native syntax defined
        for the given provider. Removes any remaining PAL placeholders.
        """
        syntax = self.get_syntax(provider)

        for placeholder, syntax_key in self.PLACEHOLDERS.items():
            pattern = r"\{\{" + re.escape(placeholder) + r"\}\}"
            replacement = syntax.get(syntax_key, "")
            content = re.sub(pattern, replacement, content)

        # Remove any remaining {{PAL_*}} placeholders (no-ops for this provider)
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
