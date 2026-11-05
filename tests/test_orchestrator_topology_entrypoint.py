"""Entry point and ``default_agent`` follow the resolved topology (IC-7).

SPEC-orchestrator-topology-2026-11-03, P2 (issue #1077), Task 12.

The topology is folded into the EXISTING decision — no second control
parameter:

    emit_default_agent = role_emitted_for_provider(...) and topology.effective == "primary"

Consequences pinned here:

* a fresh v2 project with ``topology: subagent`` gets no ``default_agent``;
* a managed value rolls back when the topology switches ``primary -> subagent``;
* a user-owned value is preserved (no auto-delete) with the
  ``orchestrator-topology.default-agent-conflict`` warning;
* ``topology: primary`` is byte-identical to the unset key.

Run: python3 -m pytest tests/test_orchestrator_topology_entrypoint.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import isolation  # noqa: E402
from lib.context import _init_provider_settings_json  # noqa: E402
from lib.log import SyncLog  # noqa: E402

AS = SimpleNamespace(
    roles=frozenset({"orchestrator", "developer"}),
    known_roles=frozenset({"orchestrator", "developer", "tester"}),
)
PC = {"Opencode": {"primary-role": "orchestrator"}}
STRICT = {"orchestrator": {"mode": "strict"}}
SUBAGENT = {"orchestrator": {"mode": "strict", "topology": "subagent"}}
PRIMARY = {"orchestrator": {"mode": "strict", "topology": "primary"}}


def _init_pc() -> dict:
    return {
        "settings_file": "opencode.json",
        "surface-version": "v2",
        "primary-role": "orchestrator",
        "mcp-config": {"format": "opencode-json-v2"},
    }


def _init_project(tmp_path: Path, config: dict) -> dict:
    project = tmp_path / "project"
    _init_provider_settings_json(
        project, _init_pc(), _REPO_ROOT, {}, SyncLog(), False,
        provider="Opencode", config=config, active_set=AS,
    )
    return json.loads((project / "opencode.json").read_text(encoding="utf-8"))


def _run_gate(tmp_path: Path, config: dict, initial: str = "{}\n"):
    (tmp_path / "opencode.json").write_text(initial, encoding="utf-8")
    log = SyncLog()
    isolation._sync_opencode_runtime_gate(
        tmp_path, config, "Opencode", PC, _REPO_ROOT, log, False, AS
    )
    doc = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    return doc, log


# --- fresh init surface -----------------------------------------------------


def test_fresh_v2_project_with_subagent_topology_has_no_default_agent(tmp_path):
    doc = _init_project(tmp_path, SUBAGENT)
    assert "default_agent" not in doc


def test_fresh_v2_project_with_primary_topology_keeps_default_agent(tmp_path):
    assert _init_project(tmp_path, PRIMARY)["default_agent"] == "orchestrator"


def test_unset_topology_is_byte_identical_to_primary_on_init(tmp_path):
    assert _init_project(tmp_path / "unset", STRICT) == _init_project(
        tmp_path / "primary", PRIMARY
    )


# --- managed rollback -------------------------------------------------------


def test_managed_default_agent_rolls_back_on_switch_to_subagent(tmp_path):
    doc, _ = _run_gate(tmp_path, STRICT)
    assert doc["default_agent"] == "orchestrator"

    log = SyncLog()
    isolation._sync_opencode_runtime_gate(
        tmp_path, SUBAGENT, "Opencode", PC, _REPO_ROOT, log, False, AS
    )
    assert (
        "default_agent"
        not in json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    )


# --- user-owned value -------------------------------------------------------


def test_user_owned_default_agent_survives_with_conflict_warning(tmp_path):
    doc, log = _run_gate(
        tmp_path, SUBAGENT, initial='{"default_agent": "orchestrator"}\n'
    )
    assert doc["default_agent"] == "orchestrator"
    assert any(
        "orchestrator-topology.default-agent-conflict" in warning
        for warning in log.warnings
    )


# --- gate coupling ----------------------------------------------------------


def test_gate_inactive_warning_is_emitted_once_per_run(tmp_path):
    doc, log = _run_gate(tmp_path, SUBAGENT)
    hits = [
        warning for warning in log.warnings
        if "orchestrator-topology.gate-inactive" in warning
    ]
    assert len(hits) == 1
    # The deny is deliberately withheld: without an entry point it would lock
    # every agent out.
    assert doc.get("permission", {}).get("edit", {}).get("**") != "deny"


def test_primary_topology_writes_the_expected_gate_and_entry_point(tmp_path):
    doc, _ = _run_gate(tmp_path, PRIMARY)
    assert doc["default_agent"] == "orchestrator"
    assert doc["permission"]["edit"]["**"] == "deny"
