"""B3 (IC-4, AC-5/AC-6): Continue subagent degrade + primary prose-only findings.

SPEC 2026-11-19-worker-control-capability, Plan Task B3.

The consistency checker must emit the **same** O5 finding
(``orchestrator-topology.subagent-unsupported``) when a provider's fail-safe
lands back on an unsupported ``subagent`` cell — declared *or* derived. Its
message carries the E-17 phrase ``subagent unsupported → sequential-text
degradation``. There is no clamp to ``primary`` and no silent degradation.

A provider whose effective ``primary`` has no mechanical entry mechanism is
reported as ``prose-only`` (Claude/Kimi); no primary setting is written.

All detection is data-driven (``topology_support`` / ``topology_degrade`` /
``primary-role`` / ``topology_verified_state``) — no provider-name branch.

Run: python3 -m pytest tests/test_topology_capability_findings.py -q
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.consistency import topology as topology_module  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402
from lib.consistency.topology import check_orchestrator_topology  # noqa: E402
from lib.providers import load_provider_capabilities  # noqa: E402
from lib.topology import resolve_topology  # noqa: E402

_ACTIVE = SimpleNamespace(
    roles=frozenset({"orchestrator", "developer"}),
    known_roles=frozenset({"orchestrator", "developer"}),
)

_CONTINUE_CAPS = {
    "subagent_dispatch": False,
    "main_agent_selectable": True,
    "topology_support": {"primary": True, "subagent": False, "hybrid": False},
    "topology_degrade": {
        "primary": None,
        "subagent": "sequential-text",
        "hybrid": "subagent",
    },
    "topology_verified_state": {
        "primary": "DOCUMENTED",
        "subagent": "DOCUMENTED",
        "hybrid": "UNVERIFIED",
    },
}

_PROSE_PRIMARY_CAPS = {
    "subagent_dispatch": True,
    "main_agent_selectable": True,
    "topology_support": {"primary": True, "subagent": True, "hybrid": False},
    "topology_degrade": {"primary": None, "subagent": None, "hybrid": "subagent"},
    "topology_verified_state": {
        "primary": "DOCUMENTED",
        "subagent": "DOCUMENTED",
        "hybrid": "UNVERIFIED",
    },
}


def _check(tmp_path, config, *, provider, caps, pcs=None, active_set=_ACTIVE):
    return check_orchestrator_topology(
        tmp_path,
        config,
        provider_config={provider: {}} if pcs is None else pcs,
        capabilities={provider: dict(caps)},
        providers=[provider],
        active_set=active_set,
    )


def _by_check(findings, check):
    return [f for f in findings if f.check == check]


# --- data-driven provider membership (no hard-coded names in code) ---------


def test_real_config_carries_the_continue_degrade_pattern():
    """The checker's trigger is config data, not a provider-name branch."""
    caps = load_provider_capabilities(_REPO_ROOT)["Continue"]
    assert caps["subagent_dispatch"] is False
    assert caps["topology_support"]["subagent"] is False
    assert caps["topology_degrade"]["subagent"] == "sequential-text"


# --- AC-5: exactly one WARNING, no clamp, no silent degrade ----------------


def test_declared_subagent_emits_exactly_one_unsupported_warning(tmp_path):
    findings = _check(
        tmp_path,
        {"orchestrator": {"topology": "subagent"}},
        provider="Continue",
        caps=_CONTINUE_CAPS,
    )
    hits = _by_check(findings, topology_module.CHECK_SUBAGENT_UNSUPPORTED)
    assert len(hits) == 1
    assert hits[0].severity == Severity.WARNING
    assert "subagent unsupported → sequential-text degradation" in hits[0].message
    assert "Continue" in hits[0].message
    assert "prose" in hits[0].message
    # No second, deviating finding for the same condition.
    assert len(findings) == 1
    assert all(f.severity != Severity.ERROR for f in findings)


def test_derived_subagent_emits_the_identical_warning(tmp_path):
    """The derived fail-safe is not silent and reuses the O5 message."""
    declared = _check(
        tmp_path,
        {"orchestrator": {"topology": "subagent"}},
        provider="Continue",
        caps=_CONTINUE_CAPS,
    )
    derived = _check(
        tmp_path,
        {"orchestrator": {}},
        provider="Continue",
        caps=_CONTINUE_CAPS,
    )
    declared_hits = _by_check(
        declared, topology_module.CHECK_SUBAGENT_UNSUPPORTED
    )
    derived_hits = _by_check(derived, topology_module.CHECK_SUBAGENT_UNSUPPORTED)
    assert len(derived_hits) == 1
    assert derived_hits[0].severity == Severity.WARNING
    assert derived_hits[0].message == declared_hits[0].message
    assert len(derived) == 1


def test_fail_safe_stays_on_subagent_without_a_primary_clamp():
    resolution = resolve_topology(
        {"orchestrator": {"topology": "subagent"}},
        "Continue",
        provider_config={"Continue": {}},
        capabilities=_CONTINUE_CAPS,
        mode="strict",
        active_set=_ACTIVE,
        validate=False,
    )
    assert resolution.effective == "subagent"
    assert resolution.degraded_from is None


def test_declared_primary_degrading_does_not_get_a_second_warning(tmp_path):
    """O5 owns declared-subagent; a real primary→subagent stays a degrade."""
    caps = dict(_CONTINUE_CAPS)
    caps["topology_support"] = {
        "primary": False,
        "subagent": False,
        "hybrid": False,
    }
    caps["topology_degrade"] = {
        "primary": "subagent",
        "subagent": "sequential-text",
        "hybrid": "subagent",
    }
    findings = _check(
        tmp_path,
        {"orchestrator": {"topology": "primary"}},
        provider="Continue",
        caps=caps,
    )
    assert len(_by_check(findings, topology_module.CHECK_DEGRADED)) == 1
    assert _by_check(findings, topology_module.CHECK_SUBAGENT_UNSUPPORTED) == []


# --- AC-6: primary cell reported prose-only, nothing set mechanically ------


def test_claude_and_kimi_primary_are_reported_prose_only(tmp_path):
    for provider in ("Claude", "Kimi"):
        findings = _check(
            tmp_path,
            {"orchestrator": {"topology": "primary"}},
            provider=provider,
            caps=_PROSE_PRIMARY_CAPS,
            pcs={provider: {}},  # no primary-role => no entry mechanism
        )
        hits = _by_check(findings, topology_module.CHECK_PRIMARY_PROSE_ONLY)
        assert len(hits) == 1, [f.check for f in findings]
        assert hits[0].severity == Severity.WARNING
        assert "prose-only" in hits[0].message
        assert all(f.severity != Severity.ERROR for f in findings)


def test_primary_with_an_entry_mechanism_is_not_prose_only(tmp_path):
    findings = _check(
        tmp_path,
        {"orchestrator": {"topology": "primary"}},
        provider="Opencode",
        caps=_PROSE_PRIMARY_CAPS,
        pcs={"Opencode": {"primary-role": "orchestrator"}},
    )
    assert _by_check(findings, topology_module.CHECK_PRIMARY_PROSE_ONLY) == []


def test_checker_writes_no_primary_setting(tmp_path):
    _check(
        tmp_path,
        {"orchestrator": {"topology": "primary"}},
        provider="Claude",
        caps=_PROSE_PRIMARY_CAPS,
        pcs={"Claude": {}},
    )
    assert not any(tmp_path.iterdir())


# --- AC-10: capability-key based, never a provider-name branch -------------


def test_checker_has_no_provider_name_branch():
    source = (
        _REPO_ROOT / "scripts" / "lib" / "consistency" / "topology.py"
    ).read_text(encoding="utf-8")
    offenders = []
    for node in ast.walk(ast.parse(source)):
        if (
            isinstance(node, ast.Compare)
            and isinstance(node.left, ast.Name)
            and node.left.id == "provider"
        ):
            for comparator in node.comparators:
                if isinstance(comparator, ast.Constant) and isinstance(
                    comparator.value, str
                ):
                    offenders.append(comparator.value)
    assert offenders == []
