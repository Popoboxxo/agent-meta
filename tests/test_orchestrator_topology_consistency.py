"""Consistency checks for the resolved orchestrator topology (IC-5).

SPEC-orchestrator-topology-2026-11-03, P2 (issue #1077), Task 14.

``check_orchestrator_topology`` is read-only: it resolves the topology exactly
like the sync does and reports WARNINGs — never a write, never an exit code.

Pinned here:

* ``degraded`` fires once per provider/run **only** when
  ``degraded_from is not None`` (a real declared != effective degradation);
  an unchanged ``UNVERIFIED => no`` cell must not warn (D9/AC-16).
* the cross-scope ``main-chat`` override produces exactly one
  ``main-chat-supersedes`` WARNING (AC-7).
* ``gate-inactive`` fires when the gate is wanted but the effective topology
  withholds the entry point (AC-20).
* ``default-agent-conflict`` fires for a user-owned ``default_agent`` on the
  orchestrator role while the topology is not ``primary`` (AC-14).
* several check IDs may fire for the same provider in the same run; each ID is
  emitted at most once per provider (not one WARNING in total).

Run: python3 -m pytest tests/test_orchestrator_topology_consistency.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.consistency.report import Severity  # noqa: E402
from lib.consistency.topology import check_orchestrator_topology  # noqa: E402

_DEGRADED = "orchestrator-topology.degraded"
_HYBRID = "orchestrator-topology.hybrid-unverified"
_MAIN_CHAT = "orchestrator-topology.main-chat-supersedes"
_GATE = "orchestrator-topology.gate-inactive"
_CONFLICT = "orchestrator-topology.default-agent-conflict"

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

# primary not supported -> degrade to subagent (a real degradation).
_PRIMARY_UNSUPPORTED = {
    "topology_support": {"primary": False, "subagent": True, "hybrid": False},
    "topology_degrade": {"primary": "subagent", "subagent": None, "hybrid": "subagent"},
    "topology_verified_state": {
        "primary": "UNVERIFIED",
        "subagent": "DOCUMENTED",
        "hybrid": "UNVERIFIED",
    },
}


def _check(tmp_path, config, *, providers=None, caps=None, pcs=None):
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
        active_set=_ACTIVE,
    )


def _by_check(findings, check):
    return [f for f in findings if f.check == check]


# --- degraded ---------------------------------------------------------------


def test_degraded_fires_once_for_a_real_degradation(tmp_path):
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "strict", "topology": "primary"}},
        caps={"Alpha": dict(_PRIMARY_UNSUPPORTED)},
    )
    degraded = _by_check(findings, _DEGRADED)
    assert len(degraded) == 1
    assert degraded[0].severity == Severity.WARNING
    assert "primary" in degraded[0].message and "subagent" in degraded[0].message


def test_unchanged_no_cell_without_declaration_does_not_warn(tmp_path):
    # Unset key: derivation may fall back to subagent, but that is not a
    # degradation (degraded_from stays None — D9).
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "strict"}},
        caps={"Alpha": dict(_PRIMARY_UNSUPPORTED)},
    )
    assert _by_check(findings, _DEGRADED) == []


def test_degraded_is_one_per_provider_not_one_per_run(tmp_path):
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "strict", "topology": "primary"}},
        providers=["Alpha", "Beta"],
        caps={"Alpha": dict(_PRIMARY_UNSUPPORTED), "Beta": dict(_PRIMARY_UNSUPPORTED)},
    )
    assert len(_by_check(findings, _DEGRADED)) == 2


# --- hybrid ----------------------------------------------------------------


def test_declared_hybrid_on_unverified_cell_warns(tmp_path):
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "strict", "topology": "hybrid"}},
        caps={"Alpha": dict(_PRIMARY_UNSUPPORTED)},
    )
    assert len(_by_check(findings, _HYBRID)) == 1


# --- cross-scope main-chat -------------------------------------------------


def test_cross_scope_main_chat_override_is_exactly_one_warning(tmp_path):
    findings = _check(
        tmp_path,
        {
            "orchestrator": {
                "mode": "strict",
                "topology": "primary",
                "provider-overrides": {"Alpha": {"mode": "main-chat"}},
            }
        },
    )
    supersedes = _by_check(findings, _MAIN_CHAT)
    assert len(supersedes) == 1
    assert supersedes[0].severity == Severity.WARNING
    assert "Alpha" in supersedes[0].message
    # No same-scope error: the checker emits findings, never exits.
    assert all(f.severity != Severity.ERROR for f in findings)


# --- gate inactive ---------------------------------------------------------


def test_gate_inactive_when_topology_withholds_the_entry_point(tmp_path):
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "strict", "topology": "subagent"}},
        pcs={"Alpha": {"primary-role": "orchestrator", "settings_file": "opencode.json"}},
        caps={"Alpha": dict(_SUPPORTED, runtime_gate="permission")},
    )
    gate = _by_check(findings, _GATE)
    assert len(gate) == 1
    assert "subagent" in gate[0].message


def test_gate_inactive_absent_for_primary_topology(tmp_path):
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "strict", "topology": "primary"}},
        pcs={"Alpha": {"primary-role": "orchestrator", "settings_file": "opencode.json"}},
        caps={"Alpha": dict(_SUPPORTED, runtime_gate="permission")},
    )
    assert _by_check(findings, _GATE) == []


# --- default_agent conflict ------------------------------------------------


def test_user_owned_default_agent_conflicts_with_non_primary_topology(tmp_path):
    (tmp_path / "opencode.json").write_text(
        json.dumps({"default_agent": "orchestrator"}) + "\n", encoding="utf-8"
    )
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "strict", "topology": "subagent"}},
        pcs={"Alpha": {"primary-role": "orchestrator", "settings_file": "opencode.json"}},
    )
    conflict = _by_check(findings, _CONFLICT)
    assert len(conflict) == 1
    assert "orchestrator" in conflict[0].message
    assert "no auto-delete" in conflict[0].suggestion.lower()


# --- several IDs, each once ------------------------------------------------


def test_multiple_check_ids_fire_together_without_duplicates(tmp_path):
    (tmp_path / "opencode.json").write_text(
        json.dumps({"default_agent": "orchestrator"}) + "\n", encoding="utf-8"
    )
    findings = _check(
        tmp_path,
        {"orchestrator": {"mode": "strict", "topology": "subagent"}},
        pcs={"Alpha": {"primary-role": "orchestrator", "settings_file": "opencode.json"}},
        caps={"Alpha": dict(_SUPPORTED, runtime_gate="permission")},
    )
    checks = [f.check for f in findings]
    assert checks.count(_GATE) == 1
    assert checks.count(_CONFLICT) == 1
    assert set(checks) == {_GATE, _CONFLICT}


# --- zero findings without the key -----------------------------------------


def test_repository_without_the_key_produces_zero_findings():
    findings = check_orchestrator_topology(_REPO_ROOT, {})
    assert findings == []
