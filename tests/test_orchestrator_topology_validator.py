"""Hard stdlib validator tests for the orchestrator position axis (IC-8).

SPEC-orchestrator-topology-2026-11-03, P1 (issue #1077), Task 7.

The validator is the single hard exit for same-scope contradictions. It runs in
``_validate_config`` after ``_validate_providers`` and therefore fires for both
``sync`` and ``sync --validate`` — with stdlib only, no ``jsonschema``.

Pinned P1 substrings (AC-17):

* ``unknown orchestrator.topology``
* ``orchestrator.topology conflicts with orchestrator.mode: main-chat``
* ``orchestrator.topology conflicts with orchestrator.enabled: false``
* ``provider-overrides.<P>.topology conflicts with
  provider-overrides.<P>.mode: main-chat``

Cross-scope (provider override ``mode: main-chat`` + a global topology) is
deliberately NOT a validator error — it stays the P2 WARNING.

The 3x3 ``mode`` x ``topology`` matrix from the spec is exposed as data
(``ORCHESTRATOR_TOPOLOGY_MATRIX``) plus ``orchestrator_topology_cell`` so AC-5
can test all nine cells, including the ``main-chat`` ERROR/inert rule.

Run: python3 -m pytest tests/test_orchestrator_topology_validator.py -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.config import (  # noqa: E402
    ORCHESTRATOR_TOPOLOGY_MATRIX,
    _validate_orchestrator_topology,
    orchestrator_topology_cell,
)

_MODES = ("strict", "advisory", "main-chat")
_TOPOLOGIES = ("primary", "subagent", "hybrid")


def _config_path(tmp_path: Path) -> Path:
    path = tmp_path / ".meta-config" / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _validate(config: dict, tmp_path: Path) -> None:
    _validate_orchestrator_topology(config, _config_path(tmp_path))


def _valid_orchestrator(**extra) -> dict:
    base = {"topology": "primary"}
    base.update(extra)
    return base


# --- Happy path --------------------------------------------------------------


def test_absent_orchestrator_block_is_valid(tmp_path):
    _validate({}, tmp_path)


def test_consistent_topology_is_valid(tmp_path):
    _validate({"orchestrator": _valid_orchestrator(mode="strict")}, tmp_path)


@pytest.mark.parametrize("topology", _TOPOLOGIES)
def test_each_valid_topology_is_accepted(tmp_path, topology):
    _validate({"orchestrator": {"topology": topology}}, tmp_path)


# --- (a) unknown enum --------------------------------------------------------


def test_unknown_project_topology_is_a_hard_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate({"orchestrator": {"topology": "hybrid2"}}, tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "unknown orchestrator.topology" in err
    assert "hybrid2" in err
    assert "'primary', 'subagent', 'hybrid'" in err


def test_unknown_provider_override_topology_is_a_hard_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {
                "orchestrator": {
                    "provider-overrides": {"Opencode": {"topology": "hybrid2"}}
                }
            },
            tmp_path,
        )
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "unknown orchestrator.topology" in err
    assert "Opencode" in err


# --- (b) project scope: topology x main-chat --------------------------------


def test_project_topology_conflicts_with_project_mode_main_chat(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"orchestrator": {"topology": "primary", "mode": "main-chat"}},
            tmp_path,
        )
    assert exc.value.code == 1
    assert (
        "orchestrator.topology conflicts with orchestrator.mode: main-chat"
        in capsys.readouterr().err
    )


@pytest.mark.parametrize("topology", _TOPOLOGIES)
def test_main_chat_dominates_every_topology_in_the_same_scope(
    tmp_path, capsys, topology
):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"orchestrator": {"topology": topology, "mode": "main-chat"}},
            tmp_path,
        )
    assert exc.value.code == 1
    assert (
        "orchestrator.topology conflicts with orchestrator.mode: main-chat"
        in capsys.readouterr().err
    )


# --- (b2) project scope: topology x enabled: false -------------------------


def test_project_topology_conflicts_with_enabled_false(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"orchestrator": {"topology": "subagent", "enabled": False}},
            tmp_path,
        )
    assert exc.value.code == 1
    assert (
        "orchestrator.topology conflicts with orchestrator.enabled: false"
        in capsys.readouterr().err
    )


# --- (c) provider override: same-object main-chat --------------------------


def test_same_object_override_main_chat_is_a_hard_error(tmp_path, capsys):
    """The same object may not declare ``mode: main-chat`` and a topology."""
    with pytest.raises(SystemExit) as exc:
        _validate(
            {
                "orchestrator": {
                    "provider-overrides": {
                        "Opencode": {"mode": "main-chat", "topology": "primary"}
                    }
                }
            },
            tmp_path,
        )
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert (
        "provider-overrides.Opencode.topology conflicts with "
        "provider-overrides.Opencode.mode: main-chat" in err
    )


def test_provider_override_topology_conflicts_with_override_mode(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {
                "orchestrator": {
                    "provider-overrides": {
                        "Claude": {"topology": "hybrid", "mode": "main-chat"}
                    }
                }
            },
            tmp_path,
        )
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert (
        "provider-overrides.Claude.topology conflicts with "
        "provider-overrides.Claude.mode: main-chat" in err
    )


# --- Cross-scope is NOT a hard error ---------------------------------------


def test_cross_scope_main_chat_override_with_global_topology_is_not_an_error(
    tmp_path,
):
    _validate(
        {
            "orchestrator": {
                "topology": "primary",
                "provider-overrides": {"Claude": {"mode": "main-chat"}},
            }
        },
        tmp_path,
    )


def test_cross_scope_topology_override_with_global_main_chat_is_not_an_error(
    tmp_path,
):
    _validate(
        {
            "orchestrator": {
                "mode": "main-chat",
                "provider-overrides": {"Claude": {"topology": "primary"}},
            }
        },
        tmp_path,
    )


# --- (d) singletons x max-instances (P3, AC-8) -----------------------------


def test_singleton_present_with_more_than_one_instance_is_a_hard_error(
    tmp_path, capsys
):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"orchestrator": {"singleton": True, "max-instances": 2}},
            tmp_path,
        )
    assert exc.value.code == 1
    assert (
        "orchestrator.singleton conflicts with orchestrator.max-instances"
        in capsys.readouterr().err
    )


def test_singleton_false_is_rejected_with_an_actionable_hint(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"orchestrator": {"singleton": False, "max-instances": 1}},
            tmp_path,
        )
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert (
        "orchestrator.singleton: false is not supported (use max-instances)"
        in err
    )


def test_singleton_present_with_one_instance_is_not_an_error(tmp_path):
    """Redundant, not contradictory: the P3 INFO owns this case, not the exit."""
    _validate(
        {"orchestrator": {"singleton": True, "max-instances": 1}},
        tmp_path,
    )


def test_singleton_present_without_max_instances_defaults_to_one(tmp_path):
    _validate({"orchestrator": {"singleton": True}}, tmp_path)


def test_absent_singleton_with_many_instances_is_valid(tmp_path):
    _validate({"orchestrator": {"max-instances": 8}}, tmp_path)


# --- (e) primary x max-instances in the same scope (P3, AC-9) ---------------


def test_primary_with_more_than_one_instance_in_the_same_scope_is_a_hard_error(
    tmp_path, capsys
):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"orchestrator": {"topology": "primary", "max-instances": 2}},
            tmp_path,
        )
    assert exc.value.code == 1
    assert (
        "orchestrator.topology: primary conflicts with "
        "orchestrator.max-instances" in capsys.readouterr().err
    )


def test_primary_with_one_instance_is_valid(tmp_path):
    _validate(
        {"orchestrator": {"topology": "primary", "max-instances": 1}},
        tmp_path,
    )


def test_cross_scope_primary_override_with_global_instances_is_not_an_error(
    tmp_path,
):
    """AC-9: the provider-scoped ``primary`` is clamped by a WARNING, not here."""
    _validate(
        {
            "orchestrator": {
                "max-instances": 3,
                "provider-overrides": {"Opencode": {"topology": "primary"}},
            }
        },
        tmp_path,
    )


# --- max-instances range (P3) -----------------------------------------------


@pytest.mark.parametrize("value", [0, 9, -1])
def test_max_instances_outside_one_to_eight_is_a_hard_error(
    tmp_path, capsys, value
):
    with pytest.raises(SystemExit) as exc:
        _validate({"orchestrator": {"max-instances": value}}, tmp_path)
    assert exc.value.code == 1
    assert "orchestrator.max-instances" in capsys.readouterr().err


@pytest.mark.parametrize("value", [1.5, "3", True])
def test_max_instances_non_integer_is_a_hard_error(tmp_path, capsys, value):
    with pytest.raises(SystemExit) as exc:
        _validate({"orchestrator": {"max-instances": value}}, tmp_path)
    assert exc.value.code == 1
    assert "orchestrator.max-instances" in capsys.readouterr().err


# --- 3x3 matrix (AC-5) ------------------------------------------------------


def test_mode_topology_matrix_all_nine_cells():
    """Every cell of the normative 3x3 table is pinned."""
    assert set(ORCHESTRATOR_TOPOLOGY_MATRIX) == {
        (mode, topology) for mode in _MODES for topology in _TOPOLOGIES
    }
    for mode in ("strict", "advisory"):
        assert orchestrator_topology_cell(mode, "primary") == "entry"
        assert orchestrator_topology_cell(mode, "subagent") == "spawned"
        assert orchestrator_topology_cell(mode, "hybrid") == "position-agnostic"
    for topology in _TOPOLOGIES:
        assert orchestrator_topology_cell("main-chat", topology) == "error"
        assert (
            orchestrator_topology_cell("main-chat", topology, same_scope=False)
            == "inert"
        )


def test_matrix_rejects_unknown_mode_or_topology():
    with pytest.raises(KeyError):
        orchestrator_topology_cell("disabled", "primary")
    with pytest.raises(KeyError):
        orchestrator_topology_cell("strict", "hybrid2")


# --- Subprocess proof: sync AND --validate both abort ----------------------

_CONTRADICTORY_CONFIG = """\
project:
  name: topology-validator-test
  prefix: tv
  short: tv
ai-providers: [Claude]
orchestrator:
  topology: primary
  mode: main-chat
"""


@pytest.mark.parametrize("mode_flag", [[], ["--validate"]])
def test_cli_aborts_for_sync_and_validate(tmp_path, mode_flag):
    config = tmp_path / ".meta-config" / "project.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(_CONTRADICTORY_CONFIG, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "scripts" / "sync.py"),
            "--config",
            str(config),
            *mode_flag,
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert (
        "orchestrator.topology conflicts with orchestrator.mode: main-chat"
        in result.stderr
    )


_INSTANCE_CONFLICT_CONFIG = """\
project:
  name: topology-instance-conflict-test
  prefix: ti
  short: ti
ai-providers: [Claude]
orchestrator:
  singleton: true
  max-instances: 2
"""


@pytest.mark.parametrize("mode_flag", [[], ["--validate"]])
def test_cli_aborts_for_instance_conflicts_in_sync_and_validate(
    tmp_path, mode_flag
):
    config = tmp_path / ".meta-config" / "project.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(_INSTANCE_CONFLICT_CONFIG, encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "scripts" / "sync.py"),
            "--config",
            str(config),
            *mode_flag,
        ],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode != 0
    assert (
        "orchestrator.singleton conflicts with orchestrator.max-instances"
        in result.stderr
    )
