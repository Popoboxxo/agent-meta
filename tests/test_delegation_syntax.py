"""Tests for scripts.lib.delegation_syntax — DelegationSyntaxEngine.

Covers:
  - build_handoff(): envelope creation, provider syntax, edge cases
  - apply(): {{A2A_ENVELOPE}} substitution, PAL_* integration, runtime placeholders
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.a2a import A2AEnvelope, HANDOFF_ID_RE
from scripts.lib.delegation_syntax import (
    DelegationSyntaxEngine,
    _A2A_ENVELOPE_PLACEHOLDER,
    _RUNTIME_PLACEHOLDERS,
)


# Path to the config directory (relative to project root).
_CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def engine() -> DelegationSyntaxEngine:
    """Provide a DelegationSyntaxEngine pointed at the real config dir."""
    return DelegationSyntaxEngine(config_dir=_CONFIG_DIR)


# ---------------------------------------------------------------------------
# build_handoff()
# ---------------------------------------------------------------------------


class TestBuildHandoff:
    """Tests for DelegationSyntaxEngine.build_handoff()."""

    def test_creates_valid_envelope(self, engine: DelegationSyntaxEngine) -> None:
        """build_handoff() returns a dict with a validated A2AEnvelope."""
        result = engine.build_handoff(
            provider="Claude",
            source="orchestrator",
            target="developer",
            payload={"t": "Fix bug #42"},
        )
        assert "envelope" in result
        assert "provider_syntax" in result

        envelope = result["envelope"]
        assert isinstance(envelope, A2AEnvelope)
        assert envelope.source_agent == "orchestrator"
        assert envelope.target_agent == "developer"
        assert envelope.payload == {"t": "Fix bug #42"}
        assert HANDOFF_ID_RE.match(envelope.handoff_id)

    def test_provider_syntax_claude(self, engine: DelegationSyntaxEngine) -> None:
        """build_handoff() replaces {{agent}} and {{task}} in Claude delegate syntax."""
        result = engine.build_handoff(
            provider="Claude",
            source="orchestrator",
            target="developer",
            payload={"t": "Implement login"},
        )
        syntax = result["provider_syntax"]
        assert "developer" in syntax
        assert "Implement login" in syntax
        assert "{{agent}}" not in syntax
        assert "{{task}}" not in syntax
        # Claude delegate template: Agent(subagent_type="{{agent}}", prompt="{{task}}")
        assert "subagent_type" in syntax
        assert "prompt" in syntax

    def test_provider_syntax_opencode(self, engine: DelegationSyntaxEngine) -> None:
        """build_handoff() works for Opencode delegate syntax."""
        result = engine.build_handoff(
            provider="Opencode",
            source="orchestrator",
            target="tester",
            payload={"t": "Run tests"},
        )
        syntax = result["provider_syntax"]
        assert "tester" in syntax
        assert "Run tests" in syntax
        # Opencode delegate: task(subagent_type="{{agent}}", ... prompt="{{task}}")
        assert "task(" in syntax
        assert "subagent_type" in syntax

    def test_provider_syntax_gemini(self, engine: DelegationSyntaxEngine) -> None:
        """build_handoff() works for Gemini text-based delegate syntax."""
        result = engine.build_handoff(
            provider="Gemini",
            source="orchestrator",
            target="documenter",
            payload={"t": "Update README"},
        )
        syntax = result["provider_syntax"]
        assert "documenter" in syntax
        assert "Update README" in syntax

    def test_with_all_optional_params(self, engine: DelegationSyntaxEngine) -> None:
        """build_handoff() passes through schema_ref and trace_parent."""
        result = engine.build_handoff(
            provider="Claude",
            source="se-architect",
            target="se-critic",
            payload={"feature": "REQ-042"},
            schema_ref="schemas/se-task.schema.json",
            trace_parent="HOFF-20260601-001",
        )
        envelope = result["envelope"]
        assert envelope.schema_ref == "schemas/se-task.schema.json"
        assert envelope.trace_parent == "HOFF-20260601-001"

    def test_none_payload_defaults_to_empty_dict(
        self, engine: DelegationSyntaxEngine
    ) -> None:
        """build_handoff() with payload=None uses an empty dict."""
        result = engine.build_handoff(
            provider="Claude",
            source="orch",
            target="dev",
            payload=None,
        )
        assert result["envelope"].payload == {}

    def test_unknown_provider_returns_empty_syntax(
        self, engine: DelegationSyntaxEngine
    ) -> None:
        """build_handoff() with unknown provider returns empty provider_syntax."""
        result = engine.build_handoff(
            provider="NonExistentProvider",
            source="orch",
            target="dev",
            payload={"t": "test"},
        )
        assert isinstance(result["envelope"], A2AEnvelope)
        assert result["provider_syntax"] == ""

    def test_payload_without_t_field(self, engine: DelegationSyntaxEngine) -> None:
        """build_handoff() uses str(payload) when no 't' field exists."""
        result = engine.build_handoff(
            provider="Claude",
            source="orch",
            target="dev",
            payload={"ctx": "some context", "pri": "high"},
        )
        syntax = result["provider_syntax"]
        # str({"ctx": "some context", "pri": "high"}) will be used as task
        assert "ctx" in syntax or len(syntax) > 0


# ---------------------------------------------------------------------------
# apply() — A2A_ENVELOPE handling
# ---------------------------------------------------------------------------


class TestApplyA2AEnvelope:
    """Tests for DelegationSyntaxEngine.apply() with {{A2A_ENVELOPE}}."""

    def test_replaces_a2a_envelope_with_placeholder_comment(
        self, engine: DelegationSyntaxEngine
    ) -> None:
        """apply() replaces {{A2A_ENVELOPE}} with a placeholder comment."""
        content = "Before\n{{A2A_ENVELOPE}}\nAfter"
        result = engine.apply(content, provider="Claude")
        assert "{{A2A_ENVELOPE}}" not in result
        assert "A2A_ENVELOPE: generated at runtime" in result
        assert "Before" in result
        assert "After" in result

    def test_preserves_agent_and_task_placeholders(
        self, engine: DelegationSyntaxEngine
    ) -> None:
        """apply() preserves {{agent}} and {{task}} as runtime placeholders."""
        content = 'Call: Agent(subagent_type="{{agent}}", prompt="{{task}}")'
        result = engine.apply(content, provider="Claude")
        assert "{{agent}}" in result
        assert "{{task}}" in result

    def test_combined_pal_handoff_and_a2a_envelope(
        self, engine: DelegationSyntaxEngine
    ) -> None:
        """apply() substitutes PAL_HANDOFF and then handles A2A_ENVELOPE within it."""
        content = "{{PAL_HANDOFF}}"
        result = engine.apply(content, provider="Claude")
        # PAL_HANDOFF → handoff template text (which contains {{A2A_ENVELOPE}})
        # → {{A2A_ENVELOPE}} gets replaced with placeholder
        assert "{{PAL_HANDOFF}}" not in result
        assert "{{A2A_ENVELOPE}}" not in result
        assert "A2A_ENVELOPE: generated at runtime" in result
        assert "A2A Handoff Protocol" in result

    def test_multiple_a2a_envelope_occurrences(
        self, engine: DelegationSyntaxEngine
    ) -> None:
        """apply() replaces ALL occurrences of {{A2A_ENVELOPE}}."""
        content = "One: {{A2A_ENVELOPE}}\nTwo: {{A2A_ENVELOPE}}"
        result = engine.apply(content, provider="Claude")
        assert result.count("A2A_ENVELOPE: generated at runtime") == 2

    def test_no_a2a_envelope_unchanged(
        self, engine: DelegationSyntaxEngine
    ) -> None:
        """apply() does not modify content without {{A2A_ENVELOPE}}."""
        content = "Just some text with {{PAL_DELEGATE}}"
        result = engine.apply(content, provider="Claude")
        assert "A2A_ENVELOPE" not in result
        # PAL_DELEGATE still gets substituted
        assert "{{PAL_DELEGATE}}" not in result


# ---------------------------------------------------------------------------
# apply() — general PAL_* substitution
# ---------------------------------------------------------------------------


class TestApplyPalSubstitution:
    """Tests for DelegationSyntaxEngine.apply() PAL_* placeholder handling."""

    def test_pal_delegate_resolved(self, engine: DelegationSyntaxEngine) -> None:
        """apply() replaces {{PAL_DELEGATE}} with provider-specific delegate syntax."""
        result = engine.apply("{{PAL_DELEGATE}}", provider="Claude")
        assert "{{PAL_DELEGATE}}" not in result
        # Claude delegate syntax preserves agent/task placeholders
        assert "{{agent}}" in result
        assert "{{task}}" in result

    def test_unknown_pal_removed(self, engine: DelegationSyntaxEngine) -> None:
        """apply() removes unknown {{PAL_*}} placeholders."""
        result = engine.apply("Text {{PAL_UNKNOWN}} here", provider="Claude")
        assert "{{PAL_UNKNOWN}}" not in result
        assert "Text " in result
        assert " here" in result

    def test_pal_prefix_removed(self, engine: DelegationSyntaxEngine) -> None:
        """apply() removes PAL_PREFIX: markers."""
        result = engine.apply(
            "PAL_PREFIX:claude\nSome content\nPAL_PREFIX:gemini\nMore",
            provider="Claude",
        )
        assert "PAL_PREFIX:" not in result
        assert "Some content" in result
        assert "More" in result

    def test_provider_without_syntax_uses_empty_strings(
        self, engine: DelegationSyntaxEngine
    ) -> None:
        """apply() with unknown provider replaces PAL_* with empty strings."""
        result = engine.apply("{{PAL_DELEGATE}}", provider="NonExistent")
        # Unknown provider: delegate field is empty string → PAL is removed
        assert "{{PAL_DELEGATE}}" not in result


# ---------------------------------------------------------------------------
# _RUNTIME_PLACEHOLDERS constant
# ---------------------------------------------------------------------------


class TestRuntimePlaceholders:
    """Tests for the _RUNTIME_PLACEHOLDERS frozen set."""

    def test_contains_expected_keys(self) -> None:
        """_RUNTIME_PLACEHOLDERS contains agent, task, A2A_ENVELOPE."""
        assert "agent" in _RUNTIME_PLACEHOLDERS
        assert "task" in _RUNTIME_PLACEHOLDERS
        assert "A2A_ENVELOPE" in _RUNTIME_PLACEHOLDERS

    def test_is_immutable(self) -> None:
        """_RUNTIME_PLACEHOLDERS is a frozenset (immutable)."""
        assert isinstance(_RUNTIME_PLACEHOLDERS, frozenset)
