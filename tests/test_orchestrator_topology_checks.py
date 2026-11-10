"""New topology check IDs (issue #1190), Task 11.

Pinned here: ``orchestrator-topology.main-chat-derived-primary`` (D-Q1,
AC-1/AC-2). ``mode: main-chat`` with an **undeclared** topology that derives
``primary`` is not a contradiction the user wrote — it is a dangling pointer:
the role is never emitted, so the derived position is inert. The checker
reports exactly one WARNING (rc stays 0); a **declared** topology next to
``main-chat`` remains the hard validator's business (``config.py``), and the
consistency checker adds nothing for it.

Run: python3 -m pytest tests/test_orchestrator_topology_checks.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.consistency import orchestrator_strict, topology  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402
from lib.consistency.topology import check_orchestrator_topology  # noqa: E402

_DERIVED = "orchestrator-topology.main-chat-derived-primary"

_ACTIVE = SimpleNamespace(
    roles=frozenset({"orchestrator", "developer"}),
    known_roles=frozenset({"orchestrator", "developer"}),
)

# primary supported everywhere, no gate tier.
_SUPPORTED = {
    "topology_support": {"primary": True, "subagent": True, "hybrid": False},
    "topology_degrade": {"primary": None, "subagent": None, "hybrid": "subagent"},
    "topology_verified_state": {
        "primary": "DOCUMENTED",
        "subagent": "DOCUMENTED",
        "hybrid": "UNVERIFIED",
    },
}


def _check(tmp_path, config, *, providers=None, caps=None, pcs=None, active_set=None):
    provider_config = pcs or {
        name: {"primary-role": "orchestrator"} for name in (providers or ["Alpha"])
    }
    capabilities = caps or {name: dict(_SUPPORTED) for name in provider_config}
    return check_orchestrator_topology(
        tmp_path,
        config,
        provider_config=provider_config,
        capabilities=capabilities,
        providers=providers or list(provider_config),
        active_set=_ACTIVE if active_set is None else active_set,
    )


def _by_check(findings, check):
    return [f for f in findings if f.check == check]


# --- D-Q1: main-chat + derived primary -------------------------------------


def test_main_chat_derived_primary_warns_once(tmp_path):
    findings = _check(tmp_path, {"orchestrator": {"mode": "main-chat"}})

    warned = _by_check(findings, _DERIVED)
    assert len(warned) == 1
    finding = warned[0]
    assert finding.severity == Severity.WARNING
    assert finding.check == "orchestrator-topology.main-chat-derived-primary"

    message = finding.message
    # Pinned substring from spec §4-D-Q1 (after the check-ID prefix).
    assert "orchestrator.mode is 'main-chat' for provider 'Alpha'" in message
    assert "derives 'primary'" in message
    assert "(providers.Alpha.primary-role names the role" in message
    assert "the derived position is inert" in message
    assert "orchestrator.provider-overrides.Alpha.topology: subagent" in message
    assert "is an ERROR, not a remedy" in message

    # WARNING only: the checker never escalates to ERROR (AC-6 continuity).
    assert all(f.severity != Severity.ERROR for f in findings)


def test_declared_topology_in_main_chat_stays_a_hard_error(tmp_path):
    # The hard validator (config.py) owns this case; the consistency checker
    # must not duplicate it as a WARNING.
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "main-chat", "topology": "primary"}},
    )

    assert _by_check(findings, _DERIVED) == []
    assert all(f.severity != Severity.ERROR for f in findings)


def test_no_finding_without_derivation_source(tmp_path):
    # (a) No primary-role: the derivation falls back to subagent.
    no_role = _check(
        tmp_path,
        {"orchestrator": {"mode": "main-chat"}},
        pcs={"Alpha": {}},
    )
    assert _by_check(no_role, _DERIVED) == []

    # (b) primary-role present, but the role is not in the active set.
    inactive = SimpleNamespace(
        roles=frozenset({"developer"}),
        known_roles=frozenset({"orchestrator", "developer"}),
    )
    role_inactive = _check(
        tmp_path,
        {"orchestrator": {"mode": "main-chat"}},
        active_set=inactive,
    )
    assert _by_check(role_inactive, _DERIVED) == []


def test_dedup_per_provider_and_run(tmp_path):
    config = {"orchestrator": {"mode": "main-chat"}}
    for _run in range(2):
        findings = _check(tmp_path, config, providers=["Alpha", "Beta"])
        warned = _by_check(findings, _DERIVED)
        assert len(warned) == 2
        assert len([f for f in warned if "provider 'Alpha'" in f.message]) == 1
        assert len([f for f in warned if "provider 'Beta'" in f.message]) == 1


def test_check_lives_in_consistency_topology():
    assert (
        topology.CHECK_MAIN_CHAT_DERIVED_PRIMARY
        == "orchestrator-topology.main-chat-derived-primary"
    )
    # Storage rule (AC-21): not defined in another checker module.
    assert not hasattr(orchestrator_strict, "CHECK_MAIN_CHAT_DERIVED_PRIMARY")
