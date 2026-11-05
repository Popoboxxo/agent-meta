"""Instance identity and resolution for multi-instance orchestrators (P3).

SPEC-orchestrator-topology-2026-11-03, P3 (issue #1077), Task 4. Contracts:
IC-2 (``resolve_orchestrator_instances`` / ``compose_instance_session_id``),
D5 (multiplicity) and D6 (state namespace).

Logical identity model: ``orchestrator#<scope-id>``. The main chat derives the
id deterministically from a scope key (plan id / task ref, branch, PR) and
normalizes it to ``[a-z0-9][a-z0-9._-]{0,39}``. The dispatch target stays the
plain role name ``orchestrator`` (no ``#`` suffix in files or
``subagent_type``); the identity travels in the A2A envelope. A missing id at
N>1 is a prompt HARD-REJECT (guard audit ``id=unset``); a duplicate id or
overlapping scope is a HARD ERROR at spawn time — the prompt contract (G2)
owns it because P3 has no runtime registry.

Run: python3 -m pytest tests/test_multi_instance_identity.py -q
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.checkpoint import validate_session_id  # noqa: E402
from scripts.lib.io import SyncError  # noqa: E402
from scripts.lib.topology import (  # noqa: E402
    DEFAULT_MAX_INSTANCES,
    TopologyResolution,
    compose_instance_session_id,
    is_valid_orchestrator_id,
    resolve_orchestrator_instances,
)


# --- identity grammar --------------------------------------------------------


@dataclass(frozen=True)
class _FakeActiveSet:
    roles: frozenset


_VALID_IDS = (
    "scope-a",
    "pr-42",
    "a",
    "a.b_c-d",
    "0123456789abcdef0123456789abcdef01234567",  # exactly 40 chars
)


@pytest.mark.parametrize("value", _VALID_IDS)
def test_valid_orchestrator_ids(value):
    assert is_valid_orchestrator_id(value) is True


@pytest.mark.parametrize(
    "value",
    [
        "",
        "Scope-A",
        "-scope",
        "a/b",
        "a\\b",
        "..",
        "a..b",
        ".scope",
        "a b",
        "0123456789abcdef0123456789abcdef012345678",  # 41 chars
        None,
        3,
    ],
)
def test_invalid_orchestrator_ids(value):
    assert is_valid_orchestrator_id(value) is False


# --- compose_instance_session_id --------------------------------------------


def test_compose_instance_session_id_none_is_identity():
    """N=1 must stay byte-identical: no suffix, no validation, no rewrite."""
    for base in ("sess1", "base", "weird base", ""):
        assert compose_instance_session_id(base, None) == base


def test_compose_instance_session_id_namespaces_the_base():
    assert (
        compose_instance_session_id("sess1", "scope-a") == "sess1__scope-a"
    )


def test_composition_is_accepted_by_checkpoint_validation():
    composed = compose_instance_session_id("sess1", "pr-42")
    validate_session_id(composed)


@pytest.mark.parametrize("value", ["Scope-A", "-scope", "a/b", "..", ""])
def test_compose_rejects_invalid_instance_ids(value):
    with pytest.raises(ValueError):
        compose_instance_session_id("sess1", value)


def test_compose_rejects_path_traversal_inside_the_grammar():
    # ``a..b`` matches the character grammar but is unsafe as a path component.
    with pytest.raises(ValueError):
        compose_instance_session_id("sess1", "a..b")


def test_compose_rejects_an_unsafe_base():
    with pytest.raises(ValueError):
        compose_instance_session_id("../escape", "scope-a")


# --- resolve_orchestrator_instances -----------------------------------------


def _capabilities(
    *,
    multiple=True,
    multiple_state="DOCUMENTED",
    support=None,
    degrade=None,
    state=None,
):
    verified = {
        "primary": "DOCUMENTED",
        "subagent": "DOCUMENTED",
        "hybrid": "UNVERIFIED",
        "multiple": multiple_state,
    }
    if state is not None:
        verified.update(state)
    return {
        "topology_support": support
        or {"primary": True, "subagent": True, "hybrid": True},
        "topology_degrade": degrade or {},
        "topology_verified_state": verified,
        "orchestrator_instances": {"multiple": multiple, "reason": None},
    }


def _topology(
    effective="subagent", *, declared=None, source="project"
) -> TopologyResolution:
    return TopologyResolution(
        declared=declared,
        effective=effective,
        source=source,
        derived_from=None,
        degraded_from=None,
        degradation_reason=None,
        verification_state=None,
    )


def _resolve(
    config=None,
    *,
    topology=None,
    capabilities=None,
    provider="Claude",
    validate=True,
):
    return resolve_orchestrator_instances(
        config or {},
        provider,
        topology or _topology(),
        capabilities=capabilities or _capabilities(),
        validate=validate,
    )


def test_default_is_one_instance_without_reason():
    assert _resolve() == (DEFAULT_MAX_INSTANCES, None)


def test_declared_three_instances_pass_with_capability_and_documented_state():
    assert _resolve({"orchestrator": {"max-instances": 3}}) == (3, None)


def test_multiple_false_clamps_to_one_with_a_reason():
    count, reason = _resolve(
        {"orchestrator": {"max-instances": 3}},
        capabilities=_capabilities(multiple=False),
    )
    assert count == 1
    assert reason is not None
    assert "multiple" in reason


def test_unverified_multiple_cell_clamps_to_one_with_a_reason():
    count, reason = _resolve(
        {"orchestrator": {"max-instances": 3}},
        capabilities=_capabilities(multiple_state="UNVERIFIED"),
    )
    assert count == 1
    assert reason is not None
    assert "UNVERIFIED" in reason or "unverified" in reason.lower()


def test_explicit_primary_with_more_than_one_raises_sync_error():
    with pytest.raises(SyncError) as excinfo:
        _resolve(
            {"orchestrator": {"topology": "primary", "max-instances": 2}},
            topology=_topology("primary", declared="primary"),
        )
    assert (
        "orchestrator.topology: primary conflicts with "
        "orchestrator.max-instances" in str(excinfo.value)
    )


def test_explicit_primary_clamps_when_validate_is_false():
    count, reason = _resolve(
        {"orchestrator": {"topology": "primary", "max-instances": 2}},
        topology=_topology("primary", declared="primary"),
        validate=False,
    )
    assert count == 1
    assert reason is not None


def test_provider_scoped_primary_with_global_multi_clamps_without_raising():
    count, reason = _resolve(
        {"orchestrator": {"max-instances": 3}},
        topology=_topology(
            "primary", declared="primary", source="provider-override"
        ),
    )
    assert count == 1
    assert reason is not None
    assert "cross-scope" in reason.lower() or "clamp" in reason.lower()


def test_derived_primary_does_not_raise_and_uses_the_capability():
    # K-1: only an explicit same-scope ``topology: primary`` is a hard error;
    # a derived primary is governed by the capability cells alone.
    assert (
        _resolve(
            {"orchestrator": {"max-instances": 2}},
            topology=_topology("primary", declared=None, source="derived"),
        )
        == (2, None)
    )


def test_singleton_with_more_than_one_raises_sync_error():
    with pytest.raises(SyncError) as excinfo:
        _resolve({"orchestrator": {"singleton": True, "max-instances": 2}})
    assert (
        "orchestrator.singleton conflicts with "
        "orchestrator.max-instances" in str(excinfo.value)
    )


def test_singleton_with_one_instance_is_redundant_but_valid():
    assert _resolve({"orchestrator": {"singleton": True}}) == (1, None)


def test_singleton_false_raises_sync_error():
    with pytest.raises(SyncError) as excinfo:
        _resolve({"orchestrator": {"singleton": False}})
    assert (
        "orchestrator.singleton: false is not supported (use max-instances)"
        in str(excinfo.value)
    )


def test_out_of_range_instance_count_fails_closed():
    with pytest.raises(SyncError):
        _resolve({"orchestrator": {"max-instances": 9}})
    assert _resolve({"orchestrator": {"max-instances": 9}}, validate=False)[0] == 1
