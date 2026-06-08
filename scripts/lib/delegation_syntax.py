"""Provider Abstraction Layer — Delegation Syntax Engine.

Lädt config/delegation-syntax.yaml und substituiert abstrakte
{{PAL_*}} Platzhalter in Templates durch provider-spezifische Syntax.

Usage:
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine

    engine = DelegationSyntaxEngine()
    processed = engine.apply(content, provider="Gemini")

    # A2A handoff generation (runtime/programmatic):
    result = engine.build_handoff("Claude", "orchestrator", "developer",
                                  payload={"t": "Fix bug #248"})
"""

import re
from pathlib import Path
from typing import Any

from .a2a import A2AEnvelope

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]


# Runtime placeholders that are filled by the LLM at invocation time,
# not by the sync build process.  `apply()` preserves them unchanged.
_RUNTIME_PLACEHOLDERS: frozenset[str] = frozenset(
    {"agent", "task", "A2A_ENVELOPE"}
)

# Replacement for {{A2A_ENVELOPE}} at build time — a comment marker
# that tells the LLM to generate a real A2A envelope at runtime.
_A2A_ENVELOPE_PLACEHOLDER: str = (
    "<!-- A2A_ENVELOPE: generated at runtime — "
    "create via A2AEnvelope.create(source=<you>, target=<subagent>, "
    "payload={...}) → to_json() → insert here -->"
)


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

    def apply(self, content: str, provider: str) -> str:
        """Apply provider-specific syntax to abstract placeholders in content.

        Replaces {{PAL_*}} placeholders with the native syntax defined
        for the given provider. Removes any remaining PAL placeholders.
        """
        syntax = self.get_syntax(provider)

        for placeholder, syntax_key in self.PLACEHOLDERS.items():
            pattern = r"\{\{" + re.escape(placeholder) + r"\}\}"
            replacement = syntax.get(syntax_key, "")
            if not isinstance(replacement, str):
                replacement = ""
            content = re.sub(pattern, replacement, content)

        # Remove any remaining {{PAL_*}} placeholders (no-ops for this provider)
        content = re.sub(r"\{\{PAL_[A-Z_]+\}\}", "", content)

        # Remove PAL_PREFIX: markers (used in templates to mark PAL-dependent sections)
        content = re.sub(r"PAL_PREFIX:\w+\s*\n", "", content)

        # Replace {{A2A_ENVELOPE}} with a runtime placeholder comment.
        # The actual envelope is generated at invocation time by the LLM.
        content = content.replace("{{A2A_ENVELOPE}}", _A2A_ENVELOPE_PLACEHOLDER)

        return content

    def build_handoff(
        self,
        provider: str,
        source: str,
        target: str,
        payload: dict | None = None,
        schema_ref: str | None = None,
        trace_parent: str | None = None,
    ) -> dict:
        """Erzeuge einen A2A-Envelope + provider-spezifische Delegations-Syntax.

        Args:
            provider: Provider name (Claude, Opencode, Gemini, ...).
            source: Role name of the delegating agent.
            target: Role name of the target agent.
            payload: Domain-specific payload dict. If None, an empty dict is used.
            schema_ref: URI to the JSON Schema for the payload.
            trace_parent: handoff_id of the parent handoff.

        Returns:
            dict with:
                - "envelope": A2AEnvelope instance (already validated)
                - "provider_syntax": str — native delegation code for the provider
                  with {{agent}} and {{task}} replaced by actual values.

        Raises:
            ValueError: If the envelope validation fails.
        """
        actual_payload: dict = payload if payload is not None else {}
        envelope = A2AEnvelope.create(
            source=source,
            target=target,
            payload=actual_payload,
            schema_ref=schema_ref,
            trace_parent=trace_parent,
        )

        syntax = self.get_syntax(provider)
        delegate_template = syntax.get("delegate", "")
        if not isinstance(delegate_template, str):
            delegate_template = ""

        # Extract a human-readable task summary from the payload.
        task_summary = actual_payload.get("t", str(actual_payload))

        # Replace runtime placeholders with actual values.
        provider_syntax = delegate_template.replace("{{agent}}", target)
        provider_syntax = provider_syntax.replace("{{task}}", task_summary)

        return {
            "envelope": envelope,
            "provider_syntax": provider_syntax,
        }

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
