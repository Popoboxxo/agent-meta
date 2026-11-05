"""P3 (AC-11 event part): the A2A envelope carries the instance identity.

The dispatch target stays the plain role name ``orchestrator`` — the identity
travels in the envelope (``orchestrator_id`` / ``scope_id`` / ``spawned_by`` /
``spawned_at``), never as a ``orchestrator#<scope>`` suffix. At N=1 no new key
is added (the default render/validation surface is unchanged).

Run: python3 -m pytest tests/test_multi_instance_envelope.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.delegation_syntax import DelegationSyntaxEngine  # noqa: E402

_SCHEMA = _REPO_ROOT / "schemas" / "a2a-handoff.schema.json"

INSTANCE_FIELDS = ("orchestrator_id", "scope_id", "spawned_by", "spawned_at")
_ID_PATTERN = r"^[a-z0-9][a-z0-9._-]{0,39}$"


def _base_envelope(**overrides):
    envelope = {
        "protocol_version": "1.0.0",
        "handoff_id": "HOFF-20261105-001",
        "source_agent": "main_chat",
        "target_agent": "orchestrator",
        "payload": {"t": "Fix the thing"},
        "delegation_depth": 1,
    }
    envelope.update(overrides)
    return envelope


def test_schema_declares_optional_instance_fields():
    """The four instance fields are optional data — never required (N unknown)."""
    schema = json.loads(_SCHEMA.read_text(encoding="utf-8"))
    props = schema["properties"]
    for field in INSTANCE_FIELDS:
        assert field in props, f"missing optional envelope property {field}"
        assert field not in schema["required"], f"{field} must not be required"
    assert props["orchestrator_id"]["pattern"] == _ID_PATTERN
    assert props["scope_id"]["pattern"] == _ID_PATTERN
    metadata_scope = schema["properties"]["metadata"]["properties"]["scope_id"]
    assert metadata_scope["pattern"] == _ID_PATTERN


def test_validate_envelope_accepts_valid_optional_identity():
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(
        orchestrator_id="scope-a",
        scope_id="scope-a",
        spawned_by="main_chat",
        spawned_at="2026-11-05T10:00:00Z",
        metadata={"scope_id": "scope-a"},
    )
    assert engine.validate_envelope(envelope, agent_meta_root=_REPO_ROOT) == []


def test_validate_envelope_rejects_invalid_ids():
    engine = DelegationSyntaxEngine()
    for bad in ("Scope-A", "scope/a", "..", "-leading", "x" * 41):
        envelope = _base_envelope(orchestrator_id=bad)
        errors = engine.validate_envelope(envelope, agent_meta_root=_REPO_ROOT)
        assert any("orchestrator_id" in e for e in errors), (bad, errors)

    bad_metadata = _base_envelope(metadata={"scope_id": "Bad Scope"})
    errors = engine.validate_envelope(bad_metadata, agent_meta_root=_REPO_ROOT)
    assert any("metadata.scope_id" in e for e in errors), errors


def test_validate_envelope_rejects_suffixed_dispatch_target():
    """Identity must not leak into the target role name."""
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope(target_agent="orchestrator#scope-a")
    errors = engine.validate_envelope(envelope, agent_meta_root=_REPO_ROOT)
    assert any("target_agent" in e and "#" in e for e in errors), errors


def test_emit_instance_identity_is_a_noop_at_n1():
    """All-None identity returns the envelope unchanged (no new keys)."""
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope()
    emitted = engine.apply_instance_identity(envelope)
    assert emitted is envelope
    assert not set(INSTANCE_FIELDS) & set(emitted)


def test_emit_and_parse_round_trip_at_n_greater_than_one():
    engine = DelegationSyntaxEngine()
    envelope = _base_envelope()
    emitted = engine.apply_instance_identity(
        envelope,
        orchestrator_id="scope-a",
        scope_id="scope-a",
        spawned_by="main_chat",
        spawned_at="2026-11-05T10:00:00Z",
    )
    assert emitted is not envelope
    assert envelope.get("orchestrator_id") is None
    for field in INSTANCE_FIELDS:
        assert emitted[field]
    assert engine.parse_instance_identity(emitted) == {
        "orchestrator_id": "scope-a",
        "scope_id": "scope-a",
        "spawned_by": "main_chat",
        "spawned_at": "2026-11-05T10:00:00Z",
    }

    # metadata.scope_id is the documented alternate placement.
    alternate = _base_envelope(
        orchestrator_id="scope-a", metadata={"scope_id": "scope-a"}
    )
    parsed = engine.parse_instance_identity(alternate)
    assert parsed["scope_id"] == "scope-a"


def test_emit_instance_identity_rejects_invalid_id():
    engine = DelegationSyntaxEngine()
    with pytest.raises(ValueError):
        engine.apply_instance_identity(_base_envelope(), orchestrator_id="Scope-A")
