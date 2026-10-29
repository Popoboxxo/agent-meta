"""`handoff.*` gate: the data-driven advisory marker (issue #1031).

Two contracts are locked here:

* The eight read-only review roles added in 2.0.0-beta.4 declare
  ``handoff.advisory: true`` in ``config/role-defaults.yaml`` — a DATA flag, so
  the check reads a field instead of a role allowlist in code.
* The gate stays sharp: an unconsumed output of a role *without* the marker
  still produces ``handoff.output-not-consumed`` (WARNING), and the marker never
  silences the neighbouring ``target-role-missing`` / ``input-no-producer``
  checks. A non-``True`` value does not silence anything.
"""

import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.consistency.handoff_contracts import check_handoff_contracts  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402

_ROLE_DEFAULTS = _ROOT / "config" / "role-defaults.yaml"

#: Advisory review roles and the output contract each one declares.
ADVISORY_ROLES = {
    "memory-architect": "memory-architecture-v1",
    "context-engineer": "context-budget-report-v1",
    "red-team-agent": "redteam-findings-v1",
    "secrets-manager": "secret-inventory-v1",
    "chaos-engineer": "chaos-experiment-v1",
    "reproducible-builds-engineer": "build-determinism-v1",
    "ux-researcher": "ux-research-findings-v1",
    "privacy-compliance-officer": "privacy-assessment-v1",
}


def _roles():
    return yaml.safe_load(_ROLE_DEFAULTS.read_text(encoding="utf-8"))["roles"]


def _root(tmp_path, roles) -> Path:
    """Minimal agent-meta root: only config/role-defaults.yaml is read."""
    (tmp_path / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "config" / "role-defaults.yaml").write_text(
        yaml.safe_dump({"roles": roles}, sort_keys=False), encoding="utf-8"
    )
    return tmp_path


def _checks(findings, check):
    return [f for f in findings if f.check == check]


# ------------------------------------------------------------- repo data gate

def test_advisory_roles_declare_the_data_marker():
    roles = _roles()
    for name, contract in ADVISORY_ROLES.items():
        handoff = roles[name].get("handoff") or {}
        assert handoff.get("advisory") is True, name
        assert handoff.get("output_contract") == contract, name
        assert handoff.get("target_roles"), name


def test_advisory_marker_set_matches_the_review_role_list():
    marked = {
        name for name, cfg in _roles().items()
        if ((cfg.get("handoff") or {}).get("advisory") is True)
    }
    assert marked == set(ADVISORY_ROLES)


def test_repo_has_no_unconsumed_output_finding():
    findings = check_handoff_contracts(_ROOT)
    assert _checks(findings, "handoff.output-not-consumed") == []


def test_check_reads_the_marker_not_a_role_allowlist():
    """D5(ii): the exception lives in the data, never as role names in code."""
    source = (
        _ROOT / "scripts" / "lib" / "consistency" / "handoff_contracts.py"
    ).read_text(encoding="utf-8")
    for role in ADVISORY_ROLES:
        assert role not in source, role


# ----------------------------------------------------- gate stays sharp (unit)

def test_unconsumed_non_advisory_output_still_warns(tmp_path):
    root = _root(tmp_path, {
        "producer": {"handoff": {"output_contract": "alpha-v1",
                                 "target_roles": ["consumer"]}},
        "consumer": {"handoff": {"input_contracts": ["task-spec-v1"]}},
    })
    warns = _checks(check_handoff_contracts(root), "handoff.output-not-consumed")
    assert len(warns) == 1
    assert warns[0].severity is Severity.WARNING
    assert "alpha-v1" in warns[0].message and "producer" in warns[0].message
    assert "advisory: true" in warns[0].suggestion


def test_marker_silences_only_the_consumption_warning(tmp_path):
    root = _root(tmp_path, {
        "producer": {"handoff": {"output_contract": "alpha-v1",
                                 "target_roles": ["consumer"],
                                 "advisory": True}},
        "consumer": {"handoff": {"input_contracts": ["task-spec-v1"]}},
    })
    assert _checks(check_handoff_contracts(root), "handoff.output-not-consumed") == []


def test_non_boolean_marker_does_not_silence(tmp_path):
    for value in ("yes", 1, "true"):
        root = _root(tmp_path / str(value), {
            "producer": {"handoff": {"output_contract": "alpha-v1",
                                     "target_roles": ["consumer"],
                                     "advisory": value}},
            "consumer": {"handoff": {"input_contracts": ["task-spec-v1"]}},
        })
        warns = _checks(check_handoff_contracts(root), "handoff.output-not-consumed")
        assert len(warns) == 1, value


def test_marker_does_not_silence_target_role_existence(tmp_path):
    root = _root(tmp_path, {
        "producer": {"handoff": {"output_contract": "alpha-v1",
                                 "target_roles": ["ghost"],
                                 "advisory": True}},
    })
    findings = check_handoff_contracts(root)
    assert not _checks(findings, "handoff.output-not-consumed")
    errors = _checks(findings, "handoff.target-role-missing")
    assert len(errors) == 1 and errors[0].severity is Severity.ERROR


def test_marker_does_not_silence_input_without_producer(tmp_path):
    root = _root(tmp_path, {
        "producer": {"handoff": {"output_contract": "alpha-v1",
                                 "target_roles": ["consumer"],
                                 "input_contracts": ["orphan-v1"],
                                 "advisory": True}},
        "consumer": {"handoff": {"input_contracts": ["task-spec-v1"]}},
    })
    warns = _checks(check_handoff_contracts(root), "handoff.input-no-producer")
    assert len(warns) == 1 and warns[0].severity is Severity.WARNING
    assert "orphan-v1" in warns[0].message


def test_consumed_advisory_output_is_fine(tmp_path):
    """The marker is redundant once a peer declares the contract — never harmful."""
    root = _root(tmp_path, {
        "producer": {"handoff": {"output_contract": "alpha-v1",
                                 "target_roles": ["consumer"],
                                 "advisory": True}},
        "consumer": {"handoff": {"input_contracts": ["alpha-v1"]}},
    })
    assert _checks(check_handoff_contracts(root), "handoff.output-not-consumed") == []
