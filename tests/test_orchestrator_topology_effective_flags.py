"""Effective-topology render flags (G2, AC-15/AC-16/AC-21).

Issue #1190, plan §5 Task 1.

``_effective_topology_flags`` reports the *resolved* position, not the
declaration:

    ORCH_TOPOLOGY_EFFECTIVE          resolution.effective (never "", never "none")
    ORCH_TOPOLOGY_EFFECTIVE_SOURCE   resolution.source (audit flag)
    ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT source != "derived" (Rev. 2, K-1)
    ORCH_TOPOLOGY_EFFECTIVE_{PRIMARY,SUBAGENT,HYBRID}
                                     exactly one is "true"
    ORCH_TOPOLOGY_INERT              "true" iff mode == "main-chat"

``ORCH_TOPOLOGY_EXPLICIT`` (from the unchanged ``_topology_flags``) keeps
answering "did the user write it?" and must not be conflated with the
effective flags. AC-21 pins the negative invariant: the mode never changes the
resolution.

Run: python3 -m pytest tests/test_orchestrator_topology_effective_flags.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.topology import (  # noqa: E402
    VALID_TOPOLOGIES,
    TopologyResolution,
    resolve_topology,
)
from scripts.lib.variables import (  # noqa: E402
    _effective_topology_flags,
    _topology_flags,
)

_POSITION_FLAGS = (
    "ORCH_TOPOLOGY_EFFECTIVE_PRIMARY",
    "ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT",
    "ORCH_TOPOLOGY_EFFECTIVE_HYBRID",
)

_ALL_MODES = ("strict", "advisory", "main-chat")

# (declared, effective, source) — one entry per position, at least one per
# source value, plus a declared-but-degraded case.
_TRIPLES = (
    (None, "primary", "derived"),
    (None, "subagent", "derived"),
    ("primary", "primary", "project"),
    ("subagent", "subagent", "provider-override"),
    ("hybrid", "hybrid", "project"),
    ("primary", "subagent", "project"),
)


def _resolution(declared, effective, source) -> TopologyResolution:
    degraded_from = declared if declared is not None and declared != effective else None
    return TopologyResolution(
        declared=declared,
        effective=effective,
        source=source,
        derived_from="providers.Claude.primary-role" if source == "derived" else None,
        degraded_from=degraded_from,
        degradation_reason=(
            f"degraded from {declared}" if degraded_from is not None else None
        ),
        verification_state="DOCUMENTED",
    )


def test_effective_flags_report_resolution_not_declaration():
    flags = {
        **_topology_flags("", explicit=False, source="derived"),
        **_effective_topology_flags(
            _resolution(None, "primary", "derived"), mode="strict"
        ),
    }

    assert flags["ORCH_TOPOLOGY_EFFECTIVE"] == "primary"
    assert flags["ORCH_TOPOLOGY_EXPLICIT"] == "false"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "derived"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "false"


def test_effective_topology_is_never_none():
    for declared, effective, source in _TRIPLES:
        flags = _effective_topology_flags(
            _resolution(declared, effective, source), mode="strict"
        )

        assert flags["ORCH_TOPOLOGY_EFFECTIVE"] in VALID_TOPOLOGIES, (
            declared,
            effective,
            source,
        )
        assert flags["ORCH_TOPOLOGY_EFFECTIVE"] != ""
        assert flags["ORCH_TOPOLOGY_EFFECTIVE"] != "none"


def test_exactly_one_position_flag_is_true():
    for declared, effective, source in _TRIPLES:
        flags = _effective_topology_flags(
            _resolution(declared, effective, source), mode="advisory"
        )

        values = [flags[flag] for flag in _POSITION_FLAGS]
        assert values.count("true") == 1, (declared, effective, source)
        assert all(value in {"true", "false"} for value in values)
        assert flags[f"ORCH_TOPOLOGY_EFFECTIVE_{effective.upper()}"] == "true"


def test_inert_is_true_only_for_main_chat():
    resolution = _resolution(None, "primary", "derived")

    for mode in _ALL_MODES:
        flags = _effective_topology_flags(resolution, mode=mode)
        expected = "true" if mode == "main-chat" else "false"
        assert flags["ORCH_TOPOLOGY_INERT"] == expected, mode


def test_resolve_topology_ignores_mode():
    config = {
        "orchestrator": {"provider-overrides": {"Claude": {"topology": "primary"}}}
    }
    provider_config = {"Claude": {"primary-role": "orchestrator"}}
    capabilities = {
        "topology_support": {"primary": True, "subagent": True, "hybrid": True},
        "topology_degrade": {"primary": None, "subagent": None, "hybrid": None},
        "topology_verified_state": {
            "primary": "DOCUMENTED",
            "subagent": "DOCUMENTED",
            "hybrid": "DOCUMENTED",
        },
    }

    resolutions = [
        resolve_topology(
            config,
            "Claude",
            provider_config=provider_config,
            capabilities=capabilities,
            mode=mode,
            active_set=None,
        )
        for mode in _ALL_MODES
    ]

    assert {resolution.effective for resolution in resolutions} == {"primary"}
    assert {resolution.source for resolution in resolutions} == {"provider-override"}
