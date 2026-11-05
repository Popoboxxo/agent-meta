"""The derived orchestrator topology is summarised once per sync (IC-11).

SPEC-orchestrator-topology-2026-11-03, P2 (issue #1077), Task 15.

The derivation is invisible in the render (the key is unset). ``emit_topology_summary``
is the ONE producer of its sentence:

    topology: <effective> (derived from providers.<P>.primary-role)
    topology: subagent (derived: active-set default)

Exactly one line per derived provider, only in ``mode == "sync"`` and only when
``TopologyResolution.source == "derived"``. ``--check``/``--validate`` never see
it — the sync output stays byte-identical (AC-6/AC-19).

Run: python3 -m pytest tests/test_topology_summary_line.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.sync_pipeline import emit_topology_summary  # noqa: E402

_ACTIVE = SimpleNamespace(
    roles=frozenset({"orchestrator", "developer"}),
    known_roles=frozenset({"orchestrator", "developer"}),
)

_SUPPORTED = {
    "topology_support": {"primary": True, "subagent": True, "hybrid": False},
    "topology_degrade": {"primary": None, "subagent": None, "hybrid": "subagent"},
    "topology_verified_state": {
        "primary": "DOCUMENTED",
        "subagent": "DOCUMENTED",
        "hybrid": "UNVERIFIED",
    },
}


class _Recorder:
    def __init__(self) -> None:
        self.notes: list = []

    def note(self, target: str, reason: str) -> None:
        self.notes.append((target, reason))

    def warning(self, message: str) -> None:  # pragma: no cover - asserted absent
        self.notes.append(("WARNING", message))


def _emit(config, *, providers=("Alpha",), pcs=None, caps=None, mode="sync", active_set=_ACTIVE):
    pcs = pcs or {"Alpha": {"primary-role": "orchestrator"}}
    caps = caps or {name: dict(_SUPPORTED) for name in providers}
    log = _Recorder()
    emit_topology_summary(
        config,
        pcs,
        list(providers),
        log,
        mode=mode,
        capabilities=caps,
        active_set=active_set,
    )
    return log.notes


def test_derived_from_primary_role_is_one_exact_line():
    notes = _emit({})
    assert notes == [
        ("topology", "topology: primary (derived from providers.Alpha.primary-role)")
    ]


def test_derived_active_set_default_is_one_exact_line():
    notes = _emit({}, pcs={"Alpha": {}})
    assert notes == [("topology", "topology: subagent (derived: active-set default)")]


def test_explicit_project_key_emits_no_line():
    assert _emit({"orchestrator": {"topology": "primary"}}) == []


def test_explicit_provider_override_emits_no_line():
    config = {
        "orchestrator": {"provider-overrides": {"Alpha": {"topology": "subagent"}}}
    }
    assert _emit(config) == []


def test_check_and_validate_modes_emit_no_line():
    assert _emit({}, mode="check") == []
    assert _emit({}, mode="validate") == []


def test_at_most_one_line_per_provider():
    notes = _emit({}, providers=("Alpha", "Alpha"))
    assert len(notes) == 1
    assert notes[0][1].startswith("topology: primary")


def test_one_line_per_derived_provider():
    notes = _emit(
        {},
        providers=("Alpha", "Beta"),
        pcs={"Alpha": {"primary-role": "orchestrator"}, "Beta": {}},
        caps={"Alpha": dict(_SUPPORTED), "Beta": dict(_SUPPORTED)},
    )
    assert [reason for _, reason in notes] == [
        "topology: primary (derived from providers.Alpha.primary-role)",
        "topology: subagent (derived: active-set default)",
    ]


def test_function_never_writes_and_uses_the_note_channel():
    notes = _emit({})
    assert all(target == "topology" for target, _ in notes)
