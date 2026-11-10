"""The v2 reconcile consumes the topology resolved by the caller (G7, AC-22/23).

SPEC-orchestrator-mode-topology-2026-11-09, Task 14.

The defect this module pins: ``_sync_opencode_runtime_gate`` (Spec A) already
passes ``topology=`` to the single entry-point source, but the two v2 actors
``reconcile_opencode_surface_gate`` and ``_opencode_v2_gate_permissions`` were
topology-blind. On v2 + ``strict`` + ``subagent`` that produced a
``permissions[]`` deny that the surface cannot back with an entry point, plus a
"set ``default_agent``" remedy that contradicts the resolved position.

Pinned here:

* v2 + ``strict`` + ``subagent`` writes no ``permissions[]`` triple and emits
  exactly ONE sync-log warning — the cause-aware row-6 text (Spec §6.4).
* v2 emits NO consistency finding for that state (the check is tier
  ``permission``-bound, v2 is tier ``plugin``).
* v1 keeps its historic split: one log warning AND one finding — counted per
  channel, never deduplicated across channels (Spec §6.4 counting rule).
* ``topology: primary`` on v2 still writes the triples (regression).
* the resolved object is passed THROUGH — every ``_opencode_entry_point`` call
  site carries ``topology``, both reconcile callers resolve exactly once and
  pass the value down, and the object the reconcile received is the *same*
  object its two callees see (identity, no re-resolution).

Run: python3 -m pytest tests/test_isolation_v2_topology_reconcile.py -q
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import isolation  # noqa: E402
from lib.consistency.topology import (  # noqa: E402
    CHECK_GATE_INACTIVE,
    check_orchestrator_topology,
)
from lib.log import SyncLog  # noqa: E402
from lib.providers import (  # noqa: E402
    load_provider_capabilities,
    load_providers_config,
)
from lib.topology import resolve_topology  # noqa: E402
from lib.variables import _resolve_orch_mode  # noqa: E402

PROVIDER = "Opencode"

AS = SimpleNamespace(
    roles=frozenset({"orchestrator", "developer"}),
    known_roles=frozenset({"orchestrator", "developer", "tester"}),
)

#: The pinned substrings of Spec §6.4 (channel rule, v2 / tier ``plugin``).
PINNED_V2_HEAD = "opencode-v2 gate (permissions deny) NOT written for provider"
PINNED_V2_CAUSE = "effective orchestrator topology is 'subagent'"
PINNED_V1_LOG = "orchestrator-topology.gate-inactive: runtime gate"


# --- fixtures ---------------------------------------------------------------


def _config(topology: str, *, surface: str = "v2") -> dict:
    """Project config for one topology/surface combination.

    ``surface`` rides on the existing ``provider-options`` passthrough — no new
    key, no provider literal in the production code under test.
    """
    config: dict = {
        "ai-providers": [PROVIDER],
        "orchestrator": {"mode": "strict", "topology": topology},
    }
    if surface == "v2":
        config["provider-options"] = {PROVIDER: {"surface-version": "v2"}}
    return config


def _registry(config: dict) -> tuple[dict, dict]:
    """``(provider_config, capabilities)`` for *config*."""
    provider_config = load_providers_config(_REPO_ROOT, config)
    capabilities = load_provider_capabilities(_REPO_ROOT)
    return provider_config, capabilities


def _resolution(config: dict, provider_config: dict, capabilities: dict):
    """The topology resolution the production callers hand to the reconcile."""
    orch = config.get("orchestrator", {})
    return resolve_topology(
        config,
        PROVIDER,
        provider_config=provider_config,
        capabilities=capabilities.get(PROVIDER, {}),
        mode=_resolve_orch_mode(orch, None),
        active_set=AS,
    )


def _setup(tmp_path: Path, topology: str, *, surface: str = "v2", document=None):
    """A tmp project with an ``opencode.json`` and the resolved inputs."""
    config = _config(topology, surface=surface)
    provider_config, capabilities = _registry(config)
    (tmp_path / "opencode.json").write_text(
        json.dumps(document if document is not None else {}), encoding="utf-8"
    )
    resolution = _resolution(config, provider_config, capabilities)
    return config, provider_config, capabilities, resolution


def _read_doc(project: Path) -> dict:
    return json.loads((project / "opencode.json").read_text(encoding="utf-8"))


def _warnings(log: SyncLog) -> list[str]:
    return list(log.warnings)


def _triples(document: dict) -> list[dict]:
    permissions = document.get("permissions")
    if not isinstance(permissions, list):
        return []
    return [entry for entry in permissions if isinstance(entry, dict)]


# --- v2 + strict + subagent: no deny, exactly one warning -------------------


def test_v2_subagent_writes_no_permission_triples(tmp_path):
    config, provider_config, capabilities, resolution = _setup(
        tmp_path, "subagent", surface="v2"
    )
    assert resolution.effective == "subagent"

    log = SyncLog()
    isolation.reconcile_opencode_surface_gate(
        tmp_path, config, PROVIDER, provider_config, _REPO_ROOT, log, False,
        active_set=AS, topology=resolution,
    )

    document = _read_doc(tmp_path)
    assert _triples(document) == []
    assert not document.get("permissions")


def test_v2_subagent_emits_exactly_one_log_warning(tmp_path):
    config, provider_config, capabilities, resolution = _setup(
        tmp_path, "subagent", surface="v2"
    )

    log = SyncLog()
    isolation.reconcile_opencode_surface_gate(
        tmp_path, config, PROVIDER, provider_config, _REPO_ROOT, log, False,
        active_set=AS, topology=resolution,
    )

    hits = [
        warning for warning in _warnings(log)
        if PINNED_V2_HEAD in warning
    ]
    assert len(hits) == 1, _warnings(log)
    warning = hits[0]
    assert PINNED_V2_CAUSE in warning
    assert "orchestrator-topology.gate-inactive" in warning
    # The historic, now-wrong remedy must be gone from this channel.
    assert "default_agent is missing" not in warning
    assert "Set `default_agent` to 'orchestrator'" not in warning
    assert "declare primary-role" not in warning

    # v2 is tier ``plugin``: the tier-``permission``-bound check cannot fire.
    findings = check_orchestrator_topology(
        tmp_path, config, provider_config=provider_config,
        capabilities=capabilities, providers=[PROVIDER], active_set=AS,
    )
    assert [f for f in findings if f.check == CHECK_GATE_INACTIVE] == []
    assert findings == []


# --- v1: two channels, one message each ------------------------------------


def test_v1_subagent_counts_per_channel(tmp_path):
    config, provider_config, capabilities, _ = _setup(
        tmp_path, "subagent", surface="v1"
    )

    log = SyncLog()
    isolation._sync_opencode_runtime_gate(
        tmp_path, config, PROVIDER, provider_config, _REPO_ROOT, log, False,
        active_set=AS,
    )

    log_hits = [
        warning for warning in _warnings(log) if PINNED_V1_LOG in warning
    ]
    assert len(log_hits) == 1, _warnings(log)

    findings = check_orchestrator_topology(
        tmp_path, config, provider_config=provider_config,
        capabilities=capabilities, providers=[PROVIDER], active_set=AS,
    )
    finding_hits = [f for f in findings if f.check == CHECK_GATE_INACTIVE]
    assert len(finding_hits) == 1, [f.check for f in findings]
    # One finding per channel, not per check ID across channels.
    assert len(findings) == 1, [f.check for f in findings]


# --- regression: primary still writes --------------------------------------


def test_v2_primary_still_writes_the_triples(tmp_path):
    config, provider_config, capabilities, resolution = _setup(
        tmp_path, "primary", surface="v2",
        document={"default_agent": "orchestrator"},
    )
    assert resolution.effective == "primary"

    log = SyncLog()
    isolation.reconcile_opencode_surface_gate(
        tmp_path, config, PROVIDER, provider_config, _REPO_ROOT, log, False,
        active_set=AS, topology=resolution,
    )

    document = _read_doc(tmp_path)
    triples = _triples(document)
    assert len(triples) == len(isolation._V2_GATE_ACTIONS) == 2
    assert {
        (t.get("action"), t.get("resource"), t.get("effect")) for t in triples
    } == {
        (action, isolation._V2_GATE_RESOURCE, isolation._V2_GATE_EFFECT)
        for action in isolation._V2_GATE_ACTIONS
    }
    assert not any(PINNED_V2_HEAD in warning for warning in _warnings(log))


# --- pass-through instead of a re-resolution -------------------------------


def _calls(path: Path, name: str) -> list[ast.Call]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: list[ast.Call] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        fname = getattr(func, "id", None) or getattr(func, "attr", None)
        if fname == name:
            found.append(node)
    return found


def _keyword(call: ast.Call, name: str):
    for keyword in call.keywords:
        if keyword.arg == name:
            return keyword.value
    return None


def test_all_three_entry_point_calls_pass_topology():
    calls = _calls(_REPO_ROOT / "scripts" / "lib" / "isolation.py",
                   "_opencode_entry_point")
    assert len(calls) == 3, [call.lineno for call in calls]
    for call in calls:
        value = _keyword(call, "topology")
        assert value is not None, f"line {call.lineno}: keyword `topology` missing"
        assert not (isinstance(value, ast.Constant) and value.value is None), (
            f"line {call.lineno}: literal None passed as topology"
        )


def test_both_reconcile_callers_pass_topology():
    calls = (
        _calls(_REPO_ROOT / "scripts" / "lib" / "sync_pipeline.py",
               "reconcile_opencode_surface_gate")
        + _calls(_REPO_ROOT / "scripts" / "lib" / "cli_commands.py",
                 "reconcile_opencode_surface_gate")
    )
    assert len(calls) == 2, [call.lineno for call in calls]
    for call in calls:
        value = _keyword(call, "topology")
        assert value is not None, f"line {call.lineno}: keyword `topology` missing"
        # Pass-through, not a second resolution point: the callers hand over a
        # name they resolved before, never an inline call result.
        assert isinstance(value, ast.Name) and value.id == "topology", (
            f"line {call.lineno}: expected a pass-through name, "
            f"got {ast.dump(value)}"
        )


def test_reconcile_passes_the_resolved_object_downstream(tmp_path, monkeypatch):
    config, provider_config, capabilities, resolution = _setup(
        tmp_path, "subagent", surface="v2"
    )
    seen: dict[str, list] = {"entry": [], "v2": []}

    def entry_stub(*args, **kwargs):
        seen["entry"].append(kwargs)
        return None

    def v2_stub(*args, **kwargs):
        seen["v2"].append(kwargs)
        return []

    monkeypatch.setattr(isolation, "_opencode_entry_point", entry_stub)
    monkeypatch.setattr(isolation, "_opencode_v2_gate_permissions", v2_stub)

    isolation.reconcile_opencode_surface_gate(
        tmp_path, config, PROVIDER, provider_config, _REPO_ROOT, SyncLog(), False,
        active_set=AS, topology=resolution,
    )

    assert len(seen["entry"]) == 1, seen
    assert len(seen["v2"]) == 1, seen
    assert seen["entry"][0].get("topology") is resolution
    assert seen["v2"][0].get("topology") is resolution


# --- row 6 is cause-aware ---------------------------------------------------


def test_row_six_warning_is_cause_aware(tmp_path):
    config, provider_config, capabilities, resolution = _setup(
        tmp_path, "subagent", surface="v2"
    )

    log = SyncLog()
    isolation.reconcile_opencode_surface_gate(
        tmp_path, config, PROVIDER, provider_config, _REPO_ROOT, log, False,
        active_set=AS, topology=resolution,
    )

    hits = [w for w in _warnings(log) if PINNED_V2_HEAD in w]
    assert len(hits) == 1, _warnings(log)
    warning = hits[0]
    assert PINNED_V2_CAUSE in warning
    assert "orchestrator-topology.gate-inactive" in warning
    # The ``primary-role`` diagnosis belongs to the topology-less case only.
    assert "no explicit and generated primary-role" not in warning
    assert "declare primary-role" not in warning
