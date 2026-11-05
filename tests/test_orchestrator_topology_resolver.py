"""Resolver tests for the orchestrator position axis (IC-2).

SPEC-orchestrator-topology-2026-11-03, P1 (issue #1077), Task 6.

``scripts/lib/topology.py`` is a leaf module: it owns the resolution and
writes nothing. The pinned rule is:

    declared  = provider-override > project > unset
    unset     => derive from providers.<P>.primary-role + active set
                 (``primary`` only when the role is in the active set; never
                 ``hybrid``)
    fallback  = support.<axis> is False OR state.<axis> is UNVERIFIED
                 => ``topology_degrade.<axis>`` when it is a valid topology,
                    otherwise fail-safe ``subagent``
    invariant = ``effective`` is always in ``VALID_TOPOLOGIES``
    warning   = only when ``degraded_from`` is not None (declared really
                 changed); the Continue coincidence case produces none.

Run: python3 -m pytest tests/test_orchestrator_topology_resolver.py -q
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.io import SyncError  # noqa: E402
from scripts.lib.topology import (  # noqa: E402
    VALID_TOPOLOGIES,
    TopologyResolution,
    resolve_topology,
    topology_explicit,
)

_PROVIDERS = {
    "Opencode": {"primary-role": "orchestrator"},
    "Claude": {},
}


@dataclass(frozen=True)
class _FakeActiveSet:
    roles: frozenset


_ACTIVE_WITH_ORCHESTRATOR = _FakeActiveSet(frozenset({"orchestrator", "developer"}))
_ACTIVE_WITHOUT_ORCHESTRATOR = _FakeActiveSet(frozenset({"developer"}))


def _caps(*, support=None, degrade=None, state=None) -> dict:
    return {
        "topology_support": support or {},
        "topology_degrade": degrade or {},
        "topology_verified_state": state or {},
    }


_PERMISSIVE = _caps(
    support={"primary": True, "subagent": True, "hybrid": True},
    degrade={"primary": None, "subagent": None, "hybrid": None},
    state={
        "primary": "DOCUMENTED",
        "subagent": "DOCUMENTED",
        "hybrid": "DOCUMENTED",
    },
)


def _resolve(
    config=None,
    provider="Claude",
    *,
    provider_config=None,
    capabilities=None,
    active_set=None,
    validate=True,
):
    return resolve_topology(
        config or {},
        provider,
        provider_config=provider_config if provider_config is not None else _PROVIDERS,
        capabilities=capabilities if capabilities is not None else _PERMISSIVE,
        mode="strict",
        active_set=active_set,
        validate=validate,
    )


def _assert_valid(resolution: TopologyResolution) -> None:
    assert resolution.effective in VALID_TOPOLOGIES


# --- precedence: provider-override > project > derived -----------------------


def test_provider_override_wins_over_project():
    resolution = _resolve(
        {"orchestrator": {
            "topology": "primary",
            "provider-overrides": {"Claude": {"topology": "subagent"}},
        }},
        "Claude",
    )
    assert resolution.declared == "subagent"
    assert resolution.effective == "subagent"
    assert resolution.source == "provider-override"
    assert resolution.degraded_from is None
    assert resolution.derived is False
    _assert_valid(resolution)


def test_project_value_wins_over_derivation():
    resolution = _resolve({"orchestrator": {"topology": "primary"}}, "Claude")
    assert resolution.declared == "primary"
    assert resolution.effective == "primary"
    assert resolution.source == "project"
    assert resolution.derived is False
    _assert_valid(resolution)


def test_override_for_other_provider_does_not_leak():
    resolution = _resolve(
        {"orchestrator": {
            "provider-overrides": {"Opencode": {"topology": "primary"}}
        }},
        "Claude",
        provider_config=_PROVIDERS,
    )
    # No project value, Claude has no primary-role => derived subagent.
    assert resolution.source == "derived"
    assert resolution.effective == "subagent"
    _assert_valid(resolution)


# --- derivation --------------------------------------------------------------


def test_unset_derives_primary_from_opencode_primary_role():
    resolution = _resolve(
        {}, "Opencode", active_set=_ACTIVE_WITH_ORCHESTRATOR
    )
    assert resolution.declared is None
    assert resolution.derived is True
    assert resolution.source == "derived"
    assert resolution.derived_from == "providers.Opencode.primary-role"
    assert resolution.effective == "primary"
    assert resolution.degraded_from is None
    assert resolution.degradation_reason is None
    _assert_valid(resolution)


def test_unset_derives_subagent_without_primary_role():
    resolution = _resolve({}, "Claude", active_set=_ACTIVE_WITH_ORCHESTRATOR)
    assert resolution.derived is True
    assert resolution.effective == "subagent"
    assert resolution.degraded_from is None
    _assert_valid(resolution)


def test_primary_role_outside_active_set_derives_subagent():
    resolution = _resolve(
        {}, "Opencode", active_set=_ACTIVE_WITHOUT_ORCHESTRATOR
    )
    assert resolution.derived is True
    assert resolution.effective == "subagent"
    _assert_valid(resolution)


def test_derivation_never_yields_hybrid():
    for provider in ("Opencode", "Claude"):
        for active_set in (
            _ACTIVE_WITH_ORCHESTRATOR,
            _ACTIVE_WITHOUT_ORCHESTRATOR,
            None,
        ):
            resolution = _resolve({}, provider, active_set=active_set)
            assert resolution.effective != "hybrid"
            _assert_valid(resolution)


# --- fallback (B2) -----------------------------------------------------------


def test_support_false_clamps_to_degrade_target():
    capabilities = _caps(
        support={"primary": False, "subagent": True, "hybrid": False},
        degrade={"primary": "subagent", "subagent": None, "hybrid": "subagent"},
        state={"primary": "DOCUMENTED", "subagent": "DOCUMENTED", "hybrid": "UNVERIFIED"},
    )
    resolution = _resolve(
        {"orchestrator": {"topology": "primary"}},
        "Claude",
        capabilities=capabilities,
    )
    assert resolution.declared == "primary"
    assert resolution.effective == "subagent"
    assert resolution.degraded_from == "primary"
    assert "support=false" in resolution.degradation_reason
    _assert_valid(resolution)


def test_unverified_cell_clamps_to_degrade_target():
    capabilities = _caps(
        support={"primary": True, "subagent": True, "hybrid": True},
        degrade={"primary": "subagent", "subagent": None, "hybrid": "subagent"},
        state={"primary": "VERIFIED-RUNTIME", "subagent": "DOCUMENTED", "hybrid": "UNVERIFIED"},
    )
    resolution = _resolve(
        {"orchestrator": {"topology": "hybrid"}},
        "Claude",
        capabilities=capabilities,
    )
    assert resolution.effective == "subagent"
    assert resolution.degraded_from == "hybrid"
    assert "UNVERIFIED" in resolution.degradation_reason
    _assert_valid(resolution)


def test_mechanism_word_never_becomes_effective():
    capabilities = _caps(
        support={"primary": False, "subagent": True, "hybrid": False},
        degrade={"primary": "subagent", "subagent": None, "hybrid": "sequential-text"},
        state={"primary": "DOCUMENTED", "subagent": "DOCUMENTED", "hybrid": "DOCUMENTED"},
    )
    resolution = _resolve(
        {"orchestrator": {"topology": "hybrid"}},
        "Claude",
        capabilities=capabilities,
    )
    assert resolution.effective == "subagent"
    assert resolution.degraded_from == "hybrid"
    assert "sequential-text" in resolution.degradation_reason
    assert resolution.effective != "sequential-text"
    _assert_valid(resolution)


def test_continue_coincidence_reports_no_degradation():
    """Continue: declared subagent, support false, degrade sequential-text."""
    capabilities = _caps(
        support={"primary": True, "subagent": False, "hybrid": False},
        degrade={"primary": None, "subagent": "sequential-text", "hybrid": "subagent"},
        state={"primary": "DOCUMENTED", "subagent": "DOCUMENTED", "hybrid": "UNVERIFIED"},
    )
    resolution = _resolve(
        {"orchestrator": {"topology": "subagent"}},
        "Continue",
        capabilities=capabilities,
    )
    assert resolution.declared == "subagent"
    assert resolution.effective == "subagent"
    assert resolution.degraded_from is None
    assert resolution.degradation_reason is None
    _assert_valid(resolution)


def test_supported_cell_passes_declared_value_through():
    resolution = _resolve(
        {"orchestrator": {"topology": "hybrid"}},
        "Claude",
        capabilities=_caps(
            support={"primary": True, "subagent": True, "hybrid": True},
            degrade={},
            state={
                "primary": "VERIFIED-RUNTIME",
                "subagent": "VERIFIED-RUNTIME",
                "hybrid": "VERIFIED-RUNTIME",
            },
        ),
    )
    assert resolution.effective == "hybrid"
    assert resolution.degraded_from is None
    _assert_valid(resolution)


# --- error path / invariant --------------------------------------------------


def test_unknown_declared_value_raises_sync_error_with_hint():
    with pytest.raises(SyncError) as excinfo:
        _resolve({"orchestrator": {"topology": "hybrid2"}}, "Claude")
    message = str(excinfo.value)
    assert "hybrid2" in message
    for value in ("primary", "subagent", "hybrid"):
        assert value in message
    assert "Hint:" in message


def test_unknown_declared_value_falls_back_when_validate_is_false():
    resolution = _resolve(
        {"orchestrator": {"topology": "hybrid2"}}, "Claude", validate=False
    )
    assert resolution.effective in VALID_TOPOLOGIES
    assert resolution.effective == "subagent"
    _assert_valid(resolution)


def test_effective_is_always_a_valid_topology():
    configs = [
        {},
        {"orchestrator": {"topology": "primary"}},
        {"orchestrator": {"topology": "subagent"}},
        {"orchestrator": {"topology": "hybrid"}},
        {"orchestrator": {
            "topology": "primary",
            "provider-overrides": {"Claude": {"topology": "hybrid"}},
        }},
    ]
    capabilities = [
        _PERMISSIVE,
        _caps(
            support={"primary": False, "subagent": False, "hybrid": False},
            degrade={"primary": "sequential-text", "subagent": None, "hybrid": "nope"},
            state={
                "primary": "UNVERIFIED",
                "subagent": "UNVERIFIED",
                "hybrid": "UNVERIFIED",
            },
        ),
    ]
    for config in configs:
        for caps in capabilities:
            for provider in ("Opencode", "Claude", "Continue"):
                resolution = _resolve(
                    config,
                    provider,
                    capabilities=caps,
                    active_set=_ACTIVE_WITH_ORCHESTRATOR,
                )
                assert resolution.effective in VALID_TOPOLOGIES


# --- topology_explicit -------------------------------------------------------


def test_topology_explicit_project_scope():
    assert topology_explicit({"orchestrator": {"topology": "subagent"}}) is True
    assert topology_explicit({}) is False


def test_topology_explicit_provider_scope():
    config = {
        "orchestrator": {
            "provider-overrides": {"Opencode": {"topology": "primary"}}
        }
    }
    assert topology_explicit(config, "Opencode") is True
    assert topology_explicit(config, "Claude") is False
    # Without a provider argument only the project-level key counts.
    assert topology_explicit(config) is False
