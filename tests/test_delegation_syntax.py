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


# --- Issue #346: depth gate degraded to documentation ---
# The former max_depth range check was removed from validate_envelope():
# platform limits (e.g. Claude Code's own subagent depth cap) already enforce
# a ceiling, so the local check was ritual without gate effect. The
# `max_depth` project.yaml configuration stays documented
# (docs/concepts/a2a-handoff-protocol.md) but is no longer plumbed through.

def test_delegation_depth_exceeding_max_is_not_enforced():
    """Issue #346: delegation_depth range is no longer a validation error —
    the gate was degraded to a documented convention."""
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(delegation_depth=11)
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT)
    assert errors == []
    assert not any("out of range" in e for e in errors)


def test_validate_envelope_has_no_max_depth_parameter():
    """Issue #346: the enforced max_depth path (project.yaml plumbing) was
    removed — the parameter no longer exists on validate_envelope()."""
    import inspect
    params = inspect.signature(DelegationSyntaxEngine.validate_envelope).parameters
    assert "max_depth" not in params


def test_tier_override_must_be_string_when_present():
    """Structural tier_override check in validate_envelope; the full
    guardrails (preset bounds, downgrade block) live in resolve_tier_override
    (see tests/test_tier_override.py)."""
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(payload={"t": "Fix the thing", "tier_override": 7})
    errors = engine.validate_envelope(envelope, agent_meta_root=REPO_ROOT)
    assert any("tier_override" in e for e in errors)

    ok = _base_envelope(payload={"t": "Fix the thing", "tier_override": "max"})
    assert engine.validate_envelope(ok, agent_meta_root=REPO_ROOT) == []


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


# ---------------------------------------------------------------------------
# FANOUT/BARRIER capability getters (issue #265)
# ---------------------------------------------------------------------------

# Capability matrix: provider → (fanout_mechanism, has_async_fanout,
# barrier_collect). Every provider of config/ai-providers.yaml must be
# mapped — conservative default for unverified parallelism is
# sequential-fallback / false.
_FANOUT_CAPABILITY_MATRIX = {
    "Claude":     ("native-batch",         True,  True),
    "Opencode":   ("native-batch",         True,  True),
    "Gemini":     ("native-batch",         True,  True),
    "Continue":   ("sequential-fallback",  False, False),
    "Copilot":    ("sequential-fallback",  False, False),
    "Mammouth":   ("sequential-fallback",  False, False),
    "Codex":      ("tool-mediated",        True,  True),
    "ZCode":      ("sequential-fallback",  False, False),
    "KimiCode":   ("swarm",                True,  True),
}


def test_get_fanout_mechanism_covers_all_providers():
    engine = DelegationSyntaxEngine()
    for provider, (mechanism, _async, _barrier) in _FANOUT_CAPABILITY_MATRIX.items():
        assert engine.get_fanout_mechanism(provider) == mechanism, provider


def test_has_async_fanout_matrix():
    engine = DelegationSyntaxEngine()
    for provider, (_mechanism, async_fanout, _barrier) in _FANOUT_CAPABILITY_MATRIX.items():
        assert engine.has_async_fanout(provider) is async_fanout, provider


def test_get_barrier_collect_matrix():
    engine = DelegationSyntaxEngine()
    for provider, (_mechanism, _async, barrier) in _FANOUT_CAPABILITY_MATRIX.items():
        assert engine.get_barrier_collect(provider) is barrier, provider


def test_all_ai_providers_have_fanout_mechanism_mapped():
    """Every provider registry entry must have a fanout_mechanism key — a new
    provider added to ai-providers.yaml without a mapping is config drift."""
    from scripts.lib.io import load_yaml_file
    providers = load_yaml_file(REPO_ROOT / "config" / "ai-providers.yaml") or {}
    engine = DelegationSyntaxEngine()
    for provider in (providers.get("providers") or {}):
        assert engine.get_fanout_mechanism(provider) is not None, (
            f"provider '{provider}' has no fanout_mechanism mapping "
            "(issue #265 capability matrix is incomplete)"
        )


def test_get_fanout_mechanism_unknown_key_raises():
    """Mechanism-key validation must fail loudly on config drift (spike §8
    step 1 acceptance criterion) — never silently degrade."""
    engine = DelegationSyntaxEngine()
    engine._capabilities_registry = {
        "capabilities": {"X": {"fanout_mechanism": "warp-drive"}},
    }
    with pytest.raises(ValueError, match="Unknown fanout_mechanism 'warp-drive'"):
        engine.get_fanout_mechanism("X")


def test_fanout_getters_fail_closed_for_unknown_provider():
    engine = DelegationSyntaxEngine()
    assert engine.get_fanout_mechanism("DoesNotExist") is None
    assert engine.has_async_fanout("DoesNotExist") is False
    assert engine.get_barrier_collect("DoesNotExist") is False


def test_barrier_collect_consistent_with_mechanism():
    """barrier_collect must be true exactly for async mechanisms — a config
    invariant the post-sync fanout contract check enforces as an error."""
    engine = DelegationSyntaxEngine()
    for provider in _FANOUT_CAPABILITY_MATRIX:
        mechanism = engine.get_fanout_mechanism(provider)
        expected = mechanism in ("native-batch", "tool-mediated", "swarm")
        assert engine.get_barrier_collect(provider) is expected, provider
