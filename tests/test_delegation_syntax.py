"""Tests for DelegationSyntaxEngine.validate_envelope().

validate_envelope() has no automatic runtime interception point (the
orchestrator dispatches subagents via the Agent/Task tool call, not through
this Python module — see docs/concepts/a2a-handoff-protocol.md §12). It is a
manually-invokable validation utility. These tests are what makes it a real,
usable asset instead of untested dead code.
"""

from pathlib import Path

import pytest

from scripts.lib.delegation_syntax import DelegationSyntaxEngine

REPO_ROOT = Path(__file__).resolve().parents[1]


def _base_envelope(**overrides):
    envelope = {
        "protocol_version": "1.0.0",
        "handoff_id": "HOFF-20260807-001",
        "source_agent": "orchestrator",
        "target_agent": "developer",
        "payload": {"t": "Fix the thing"},
        "delegation_depth": 1,
    }
    envelope.update(overrides)
    return envelope


def test_valid_envelope_has_no_errors():
    engine = DelegationSyntaxEngine()
    errors = engine.validate_envelope(_base_envelope(), agent_meta_root=REPO_ROOT)
    assert errors == []


def test_missing_required_field_is_reported():
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope()
    del envelope["target_agent"]
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT)
    assert any("target_agent" in e for e in errors)


def test_self_handoff_is_rejected():
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(source_agent="developer", target_agent="developer")
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT)
    assert any("Self-handoff" in e for e in errors)


def test_delegation_depth_within_default_max_is_accepted():
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(delegation_depth=10)
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT)
    assert errors == []


def test_delegation_depth_exceeding_max_is_rejected():
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(delegation_depth=11)
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT)
    assert any("out of range" in e for e in errors)


def test_delegation_depth_respects_custom_max_depth():
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(delegation_depth=3)
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT, max_depth=2)
    assert any("out of range" in e for e in errors)


def test_non_integer_delegation_depth_is_rejected():
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(delegation_depth="deep")
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT)
    assert any("Invalid delegation_depth" in e for e in errors)


def test_get_schema_ref_known_names():
    engine = DelegationSyntaxEngine()
    assert engine.get_schema_ref("a2a-handoff") == "schemas/a2a-handoff.schema.json"
    assert engine.get_schema_ref("task-spec") == "schemas/handoffs/task-spec.schema.json"


def test_get_schema_ref_unknown_name_returns_empty_string():
    engine = DelegationSyntaxEngine()
    assert engine.get_schema_ref("does-not-exist") == ""


def test_full_schema_validation_catches_bad_handoff_id_format():
    pytest.importorskip("jsonschema")
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(handoff_id="not-a-valid-id")
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT)
    assert any("does not match" in e for e in errors)


# --- Regression coverage for the 2026-08-07 A2A concept cleanup ---
# (docs/concepts/a2a-best-practice-analysis-2026-08.md): several envelope
# fields and project.yaml handoff config keys were removed because they had
# no consumer anywhere (neither code nor agent prompt text). These tests
# guard against them silently creeping back in.

_REMOVED_ENVELOPE_FIELDS = (
    "retry_count", "max_retries", "escalation", "timeout_seconds", "negotiated_format",
)
_REMOVED_DEFINITIONS = ("handoffRoute", "agentContract", "handoffRegistry")
_REMOVED_PROJECT_HANDOFF_KEYS = (
    "validate-before-delegate", "supersession-tracking", "strict-validation",
    "compact-mode", "max_retries", "human_approval_required", "protocol_routing",
    "token-budget",
)


def test_envelope_schema_has_no_unimplemented_fields():
    import json
    schema = json.loads((REPO_ROOT / "schemas" / "a2a-handoff.schema.json").read_text(encoding="utf-8"))
    for field in _REMOVED_ENVELOPE_FIELDS:
        assert field not in schema["properties"], f"{field} should have been removed (no implementation)"
    for definition in _REMOVED_DEFINITIONS:
        assert definition not in schema.get("definitions", {}), f"{definition} should have been removed (unused)"


def test_project_config_schema_handoff_only_declares_protocol():
    import json
    schema = json.loads((REPO_ROOT / "config" / "project-config.schema.json").read_text(encoding="utf-8"))
    handoff_props = schema["properties"]["orchestrator"]["properties"]["handoff"]["properties"]
    assert set(handoff_props) == {"protocol"}


def test_local_project_yaml_handoff_block_has_no_dead_keys():
    import yaml as _yaml
    config = _yaml.safe_load((REPO_ROOT / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
    handoff_cfg = config.get("orchestrator", {}).get("handoff", {})
    for key in _REMOVED_PROJECT_HANDOFF_KEYS:
        assert key not in handoff_cfg, f"{key} should have been removed from project.yaml (no consumer)"


# ---------------------------------------------------------------------------
# Gemini native dispatch syntax (issue #674 Phase 3.2)
# ---------------------------------------------------------------------------

def test_gemini_delegate_entries_use_native_invoke_subagent():
    """The Gemini entries must carry the native `invoke_subagent` toolcall
    (the dispatch API the runtime exposes and the pipeline renderers already
    emit) instead of the former free-text instruction."""
    engine = DelegationSyntaxEngine()
    syntax = engine.get_syntax("Gemini")
    for key in ("delegate", "fanout", "parallel_group", "parallel_pattern"):
        value = syntax.get(key, "")
        assert "invoke_subagent" in value, (
            f"Gemini '{key}' must use the native invoke_subagent toolcall "
            "(issue #674 Phase 3.2)"
        )


def test_gemini_bootstrap_and_fallback_unchanged():
    """Phase 3.2 replaces ONLY the dispatch syntax — registration stays
    api-define_subagent (session-start), fallback stays self-processing."""
    engine = DelegationSyntaxEngine()
    syntax = engine.get_syntax("Gemini")
    assert syntax.get("bootstrap") == "api-define_subagent"
    assert "define_subagent" in syntax["bootstrap_sequence"][0]["template"]
    assert syntax.get("fallback")  # still present


def test_gemini_values_follow_string_encoding_conventions():
    """No {{var}} inside values (LLM would read them as unresolved sync
    placeholders); runtime slots use <angle-brackets> in the instructional
    entries (delegate/fanout/parallel_group). parallel_pattern follows the
    repo-wide concrete-example style (see the Claude/Codex entries)."""
    engine = DelegationSyntaxEngine()
    syntax = engine.get_syntax("Gemini")
    for key in ("delegate", "fanout", "parallel_group", "parallel_pattern"):
        value = syntax.get(key, "")
        assert "{{" not in value, f"Gemini '{key}' must not contain {{...}} tokens"
    for key in ("delegate", "fanout", "parallel_group"):
        value = syntax.get(key, "")
        assert "<" in value and ">" in value, (
            f"Gemini '{key}' should keep the <angle-brackets> runtime-slot convention"
        )


def test_gemini_pal_placeholders_resolve_without_leftovers():
    """End-to-end: the PAL engine substitutes all delegation placeholders for
    Gemini and the output neither carries leftover {{PAL_*}} tokens nor an
    empty delegate instruction."""
    engine = DelegationSyntaxEngine()
    template = (
        "{{PAL_DELEGATE}}\n"
        "{{PAL_FANOUT}}\n"
        "{{PAL_PARALLEL_GROUP}}\n"
        "{{PAL_FALLBACK}}\n"
        "{{PAL_PARALLEL_PATTERN}}\n"
    )
    import re as _re
    resolved = engine.apply(template, provider="Gemini")
    assert not _re.search(r"\{\{PAL_[A-Z_]+\}\}", resolved)
    assert "invoke_subagent" in resolved
