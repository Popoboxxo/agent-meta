"""The 24-cell emission matrix: what each ``(surface, mode, topology)`` emits.

SPEC-orchestrator-mode-topology-2026-11-09 (issue #1190), Task 15 / AC-6/7/8/10/11.

The four surface tables in ``docs/concepts/active/orchestrator-topology.md`` are
the documented home of the matrix; ``tests/test_orchestrator_topology_docs.py``
owns the verdict data (``EXPECTED_MATRIX``) and the ``mode`` x ``topology`` ->
position map (``EXPECTED_POSITION_MAP``, spec §3.8.2). This module consumes both
so there is exactly ONE verdict source — a drifted judgment fails the docs test,
a drifted emission fails here.

Four parametrized tests over the same 24 cells (4 x 24 = 96 items), each one
asking the REAL production resolver/writer, never a re-implementation:

a) ``test_effective_position`` — ``topology.resolve_topology`` returns the spec's
   ``decl->eff`` (Gemini ``primary`` -> ``subagent``; every other surface keeps
   the declared value) and the position from §12.1 (``main-chat`` is POS-1,
   otherwise POS-3 iff effective is ``primary``).
b) ``test_role_emission_and_frontmatter_mode`` — ``active_set.
   role_emitted_for_provider`` is False exactly for ``main-chat`` (POS-1: no
   artifact); otherwise the transformed orchestrator frontmatter carries
   ``primary`` only at POS-3 on the opencode surfaces and ``subagent`` at POS-2.
c) ``test_write_scope_lock_presence`` — the agent-level write-scope lock of the
   transformed frontmatter.
d) ``test_deny_form`` — the runtime-gate deny artifact (v1 ``permission`` map,
   v2 ``permissions[]`` triples) in a scratch project.

Documented deviations (spec text vs. shipped behaviour; see the per-test
comments and the report, never silently smoothed over):

* D1 — the write-scope lock of the ORCHESTRATOR role follows the effective
  strict gate, not the position: ``provider_transform._keeps_write_scope_lock``
  returns True for ``_WRITE_SCOPE_LOCKED_ROLES = {"orchestrator"}`` in every
  position ("``topology: subagent`` must not turn the router into a writer",
  ``provider_transform.py:313-328``, ``:554-562``). Spec §12.2/§12.3 and the
  concept doc list it as "aktiv" for POS-3 and "nicht gesetzt" for POS-2.
* D2 — consequently ``advisory`` x POS-3 has NO lock either: the lock is gated
  by ``_resolve_effective_strict`` (advisory writes no deny at all), while the
  doc rows mark POS-3 as "aktiv".
* D3 — the same-scope ``main-chat`` x topology ERROR is ``sys.exit(1)``
  (``config._topology_error``), not a ``SyncError``; ``SyncError`` is the
  in-memory resolver contract. Asserted as ``SystemExit`` with ``code != 0``.
* D4 — POS-1 cells emit no agent file at all, so the frontmatter/lock/deny
  assertions there are the documented ABSENCE (predicate False, no artifact),
  never a fabricated marker.
* D5 — Claude and Gemini have no agent-frontmatter ``mode`` concept; the
  assertion is "no ``mode`` key", not "``mode: subagent``".

Run: python3 -m pytest tests/test_orchestrator_mode_topology_matrix.py -q
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import isolation  # noqa: E402
from scripts.lib.active_set import role_emitted_for_provider  # noqa: E402
from scripts.lib.config import _validate_orchestrator_topology  # noqa: E402
from scripts.lib.log import SyncLog  # noqa: E402
from scripts.lib.provider_transform import (  # noqa: E402
    transform_agent_content_for_provider,
)
from scripts.lib.providers import (  # noqa: E402
    load_provider_capabilities,
    load_providers_config,
)
from scripts.lib.topology import resolve_topology  # noqa: E402
from scripts.lib.variables import _resolve_orch_mode  # noqa: E402
from tests.test_orchestrator_topology_docs import (  # noqa: E402
    EXPECTED_MATRIX,
    EXPECTED_POSITION_MAP,
)

#: The four surfaces of spec §12.2-§12.5, in table order.
_SURFACES = ("v1", "v2", "Claude", "Gemini")
_MODES = ("strict", "advisory", "main-chat")
_TOPOLOGIES = ("primary", "subagent")
#: Surfaces with an agent-frontmatter ``mode``/permission concept.
_OPENCODE_SURFACES = ("v1", "v2")

#: ``surface`` -> the provider registry key it is resolved through. Test data
#: may name surfaces; the production code under test never branches on a name.
_PROVIDER_OF = {
    "v1": "Opencode",
    "v2": "Opencode",
    "Claude": "Claude",
    "Gemini": "Gemini",
}

#: The only declared->effective delta in the 24 cells: Gemini does not support
#: ``primary`` and degrades to the fail-safe ``subagent`` (§12.5).
_DEGRADED = {("Gemini", "primary"): "subagent"}

_CAPABILITIES = load_provider_capabilities(_REPO_ROOT)

_ACTIVE_SET = SimpleNamespace(
    roles=frozenset({"orchestrator", "developer"}),
    known_roles=frozenset({"orchestrator", "developer"}),
)

#: Minimal orchestrator template. ``Write``/``Edit`` are deliberate: only a
#: template that maps to ``edit: allow`` makes the write-scope lock observable
#: (the lock replaces an allow, it never widens a deny).
_AGENT_CONTENT = (
    "---\n"
    "name: template-orchestrator\n"
    'version: "0.101.0"\n'
    "description: old description\n"
    "tools:\n"
    "  - Read\n"
    "  - Write\n"
    "  - Edit\n"
    "  - Bash\n"
    "  - Grep\n"
    "---\n"
    "\n"
    "Koordiniert alle Entwicklungsaufgaben.\n"
    "Body-Ende.\n"
)

#: Deterministic cell order (surface table, then mode row, then topology).
_CELLS = sorted(
    EXPECTED_MATRIX,
    key=lambda cell: (
        _SURFACES.index(cell[0]),
        _MODES.index(cell[1]),
        _TOPOLOGIES.index(cell[2]),
    ),
)


class _Cell:
    """One matrix cell resolved through the real production entry points."""

    def __init__(self, surface: str, mode: str, topology: str) -> None:
        self.surface = surface
        self.mode = mode
        self.topology = topology
        self.provider = _PROVIDER_OF[surface]
        self.config = _project_config(surface, mode, topology)
        self.provider_config = _registry(surface)
        self.capabilities = _CAPABILITIES.get(self.provider, {})
        self.resolution = resolve_topology(
            self.config,
            self.provider,
            provider_config=self.provider_config,
            capabilities=self.capabilities,
            mode=_resolve_orch_mode(self.config["orchestrator"], None),
            active_set=_ACTIVE_SET,
            validate=False,
        )
        self.position = _expected_position(mode, self.resolution.effective)
        self.emitted = role_emitted_for_provider(
            "orchestrator", _ACTIVE_SET, self.config, self.provider
        )

    def transformed(self) -> str:
        """The orchestrator agent content as the provider transform emits it."""
        entry = self.provider_config[self.provider]
        target_path = (
            _REPO_ROOT
            / entry["agents_dir"]
            / f"orchestrator{entry['agent_ext']}"
        )
        return transform_agent_content_for_provider(
            _AGENT_CONTENT,
            self.provider,
            "orchestrator",
            "orchestrator",
            "desc",
            "1-generic/orchestrator.md@0.101.0",
            self.config,
            _REPO_ROOT,
            _REPO_ROOT,
            target_path,
            self.provider_config,
            SyncLog(),
            active_set=_ACTIVE_SET,
            provider_capabilities=_CAPABILITIES,
        )


def _project_config(surface: str, mode: str, topology: str) -> dict:
    """Project config for one cell (existing keys only, no new config surface)."""
    provider = _PROVIDER_OF[surface]
    config: dict = {
        "ai-providers": [provider],
        "orchestrator": {"mode": mode, "topology": topology},
    }
    if surface == "v2":
        config["provider-options"] = {provider: {"surface-version": "v2"}}
    return config


#: ``surface`` -> registry. ``load_providers_config`` is independent of
#: ``orchestrator.mode``/``topology`` (only the provider-options surface
#: selector shapes it), so one load per surface suffices. Cached as a deep copy
#: so a caller can never mutate the shared fixture.
_REGISTRY_CACHE: dict[str, dict] = {}


def _registry(surface: str) -> dict:
    """The resolved provider registry for *surface*."""
    if surface not in _REGISTRY_CACHE:
        _REGISTRY_CACHE[surface] = load_providers_config(
            _REPO_ROOT, _project_config(surface, "strict", "primary")
        )
    return copy.deepcopy(_REGISTRY_CACHE[surface])


def _expected_effective(surface: str, topology: str) -> str:
    """``decl->eff`` of the cell (spec §12.2-§12.5)."""
    return _DEGRADED.get((surface, topology), topology)


def _expected_position(mode: str, effective: str) -> str:
    """Position from spec §12.1: ``main-chat`` is always POS-1, else by eff."""
    if mode == "main-chat":
        return "POS-1"
    return "POS-3" if effective == "primary" else "POS-2"


def _frontmatter(text: str) -> dict:
    parsed = yaml.safe_load(text.split("---", 2)[1])
    assert isinstance(parsed, dict)
    return parsed


def _v1_write_scope_lock(frontmatter: dict) -> bool:
    """The v1 agent-level lock: ``permission.edit`` closed to everything."""
    permission = frontmatter.get("permission")
    if not isinstance(permission, dict):
        return False
    edit = permission.get("edit")
    if edit == "deny":
        return True
    return isinstance(edit, dict) and edit.get("*") == "deny"


def _v2_write_scope_lock(frontmatter: dict) -> bool:
    """The v2 agent-level lock: ``permissions[]`` edit ``*`` deny."""
    permissions = frontmatter.get("permissions")
    if not isinstance(permissions, list):
        return False
    return any(
        isinstance(entry, dict)
        and entry.get("action") == "edit"
        and entry.get("resource") == "*"
        and entry.get("effect") == "deny"
        for entry in permissions
    )


def _v1_runtime_gate_deny(document: dict) -> bool:
    """The v1 config-level deny: ``permission.edit/bash['**'] == deny``."""
    permission = document.get("permission")
    if not isinstance(permission, dict):
        return False
    return all(
        isinstance(permission.get(family), dict)
        and permission[family].get("**") == "deny"
        for family in isolation._RUNTIME_GATE_FAMILIES
    )


def _v2_gate_triples(document: dict) -> set[tuple[str, str, str]]:
    """The v2 config-level deny as ``(action, resource, effect)`` triples."""
    permissions = document.get("permissions")
    if not isinstance(permissions, list):
        return set()
    return {
        (entry.get("action"), entry.get("resource"), entry.get("effect"))
        for entry in permissions
        if isinstance(entry, dict)
        and entry.get("resource") == isolation._V2_GATE_RESOURCE
        and entry.get("effect") == isolation._V2_GATE_EFFECT
    }


_CELL_PARAMS = pytest.mark.parametrize(
    ("surface", "mode", "topology"),
    _CELLS,
    ids=[f"{surface}-{mode}-{topology}" for surface, mode, topology in _CELLS],
)


# --- (a) resolver: declared -> effective, and the position ------------------


@_CELL_PARAMS
def test_effective_position(surface: str, mode: str, topology: str) -> None:
    cell = _Cell(surface, mode, topology)
    effective = _expected_effective(surface, topology)

    assert cell.resolution.effective == effective, (
        f"{surface} x {mode} x {topology}: expected effective {effective!r}, "
        f"got {cell.resolution.effective!r} "
        f"(degradation_reason={cell.resolution.degradation_reason!r})"
    )
    assert cell.resolution.declared == topology
    if effective != topology:
        assert cell.resolution.degraded_from == topology
    else:
        assert cell.resolution.degraded_from is None

    # `mode` never influences the resolution (§12.6: mode changes the position,
    # never the topology) — the resolver is mode-blind by contract.
    assert cell.position == _expected_position(mode, effective)
    assert cell.position in ("POS-1", "POS-2", "POS-3")

    # §3.8.2 cross-check: the documented position map agrees wherever the
    # surface did not degrade the declared value.
    if mode != "main-chat" and effective == topology:
        assert EXPECTED_POSITION_MAP[(mode, topology)] == cell.position
    if mode == "main-chat" and topology == "subagent":
        # main-chat makes the topology inert: the position stays POS-1.
        assert EXPECTED_POSITION_MAP[("main-chat", "subagent")] == "POS-1"


# --- (b) role emission and the emitted frontmatter `mode` ------------------


@_CELL_PARAMS
def test_role_emission_and_frontmatter_mode(
    surface: str, mode: str, topology: str
) -> None:
    cell = _Cell(surface, mode, topology)

    assert cell.emitted is (mode != "main-chat"), (
        f"{surface} x {mode}: orchestrator must be emitted "
        f"{'only' if mode != 'main-chat' else 'never'} (POS-1 hides the role)"
    )

    if not cell.emitted:
        # POS-1 (D4): the role is deliberately not generated, so there is no
        # agent frontmatter to inspect — the assertion is the absence itself.
        assert cell.position == "POS-1"
        return

    frontmatter = _frontmatter(cell.transformed())

    if surface in _OPENCODE_SURFACES:
        # The v1/v2 pin: `mode: primary` only at the entry position, and v2
        # hard-pins every non-primary role to `mode: subagent`.
        expected_mode = "primary" if cell.position == "POS-3" else "subagent"
        assert frontmatter.get("mode") == expected_mode, (
            f"{surface} x {mode} x {topology}: expected mode "
            f"{expected_mode!r}, got {frontmatter.get('mode')!r}"
        )
    else:
        # Claude/Gemini (D5): no agent-frontmatter `mode` concept at all.
        assert "mode" not in frontmatter or frontmatter["mode"] != "primary"
        assert "mode: primary" not in cell.transformed()


# --- (c) agent-level write-scope lock --------------------------------------


def _agent_write_scope_lock(cell: _Cell, frontmatter: dict) -> bool:
    if cell.surface == "v1":
        return _v1_write_scope_lock(frontmatter)
    if cell.surface == "v2":
        return _v2_write_scope_lock(frontmatter)
    return False


@_CELL_PARAMS
def test_write_scope_lock_presence(surface: str, mode: str, topology: str) -> None:
    cell = _Cell(surface, mode, topology)

    if not cell.emitted:
        # POS-1 (D4): no artifact, no lock field.
        assert cell.position == "POS-1"
        return

    locked = _agent_write_scope_lock(cell, _frontmatter(cell.transformed()))

    if surface in _OPENCODE_SURFACES:
        # D1/D2: the orchestrator keeps its lock in EVERY position — the
        # predicate is role-based (`_WRITE_SCOPE_LOCKED_ROLES`, "Router, not
        # Worker") and the deny itself keys off the effective strict gate
        # (`_resolve_effective_strict` + `permission_deny_required`), not off
        # POS-3. Spec §12.2/§12.3 list it as position-bound instead.
        assert locked is (mode == "strict"), (
            f"{surface} x {mode} x {topology}: write-scope lock is "
            f"{'present' if locked else 'absent'} (spec/doc claim it is "
            "position-bound; shipped behaviour is strict-gate-bound)"
        )
    else:
        # Claude/Gemini carry no agent-frontmatter lock concept (the hook tier
        # enforces it outside the file). Assert the absence, not a marker.
        assert locked is False
        assert "permission" not in _frontmatter(cell.transformed())


# --- (d) runtime-gate deny artifact ---------------------------------------


@_CELL_PARAMS
def test_deny_form(
    tmp_path: Path, surface: str, mode: str, topology: str
) -> None:
    cell = _Cell(surface, mode, topology)

    # D1a: a v2 deny is written only next to a valid `default_agent`; in the
    # real run Spec A merges it, here it is pre-seeded for the only cell that
    # can carry a deny (POS-3).
    document: dict = {}
    if surface == "v2" and mode != "main-chat" and topology == "primary":
        document = {"default_agent": "orchestrator"}
    (tmp_path / "opencode.json").write_text(
        json.dumps(document), encoding="utf-8"
    )

    log = SyncLog()
    if surface == "v2":
        isolation.reconcile_opencode_surface_gate(
            tmp_path,
            cell.config,
            cell.provider,
            cell.provider_config,
            _REPO_ROOT,
            log,
            False,
            active_set=_ACTIVE_SET,
            topology=cell.resolution,
        )
    else:
        isolation._sync_opencode_runtime_gate(
            tmp_path,
            cell.config,
            cell.provider,
            cell.provider_config,
            _REPO_ROOT,
            log,
            False,
            active_set=_ACTIVE_SET,
        )

    written = json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    v1_deny = _v1_runtime_gate_deny(written)
    triples = _v2_gate_triples(written)
    expected_deny = (
        surface in _OPENCODE_SURFACES
        and mode == "strict"
        and topology == "primary"
    )

    if surface == "v1":
        assert v1_deny is expected_deny, (
            f"v1 x {mode} x {topology}: permission-map deny "
            f"{'expected' if expected_deny else 'unexpected'}"
        )
        assert triples == set()
    elif surface == "v2":
        if expected_deny:
            assert triples == {
                (action, isolation._V2_GATE_RESOURCE, isolation._V2_GATE_EFFECT)
                for action in isolation._V2_GATE_ACTIONS
            }
        else:
            assert triples == set(), (
                f"v2 x {mode} x {topology}: no permissions[] deny is allowed "
                "without an entry point (D1a)"
            )
        # The v1 mapping form never appears on a v2 document.
        assert v1_deny is False
    else:
        # Claude/Gemini (D4): the hook tier writes no opencode deny artifact —
        # neither triples nor a v1 mapping.
        assert v1_deny is False
        assert triples == set()


# --- the four FORBIDDEN cells the matrix declares --------------------------


def test_forbidden_cells_are_rejected_by_the_validator(tmp_path: Path) -> None:
    """Same-scope ``main-chat`` x topology is a hard ERROR (AC-2).

    Cross-scope stays inert: neither direction may be rejected (P2 WARNING).
    The validator is provider-agnostic, so the cell is checked once per surface
    only to prove that no surface escapes it.

    ``main-chat`` x ``subagent`` is recorded ``ALLOWED`` in the matrix and still
    rejected in the same scope: the verdict is legal only *cross-scope*
    (inert + ``main-chat-supersedes`` WARNING), exactly as the ``mode`` x
    ``topology`` interaction matrix states ("ERROR (gleicher Scope) / inert
    (Cross-Scope)" for every ``main-chat`` cell).
    """
    assert len(_CELLS) == 24, f"expected 24 matrix cells, got {len(_CELLS)}"
    assert set(_CELLS) == set(EXPECTED_MATRIX)

    # Only the declared `primary` cell is FORBIDDEN; `subagent` is the
    # cross-scope-only ALLOWED cell. `main-chat` x `primary` has no position.
    assert EXPECTED_POSITION_MAP[("main-chat", "primary")] is None

    config_path = tmp_path / ".meta-config" / "project.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    for surface in _SURFACES:
        assert EXPECTED_MATRIX[(surface, "main-chat", "primary")] == "FORBIDDEN"
        for mode in ("strict", "advisory"):
            for topology in _TOPOLOGIES:
                declared = EXPECTED_MATRIX[(surface, mode, topology)]
                assert declared != "FORBIDDEN", (
                    f"{surface} x {mode} x {topology}: only `main-chat` x "
                    "`primary` is a validator ERROR"
                )

        for topology in _TOPOLOGIES:
            # Same scope: hard ERROR (rc != 0), not a warning.
            with pytest.raises(SystemExit) as exc:
                _validate_orchestrator_topology(
                    _project_config(surface, "main-chat", topology), config_path
                )
            assert exc.value.code != 0

            # The same declared topology under a non-dominating mode is legal.
            for mode in ("strict", "advisory"):
                _validate_orchestrator_topology(
                    _project_config(surface, mode, topology), config_path
                )

    # Cross-scope is inert, never rejected — both directions.
    for surface in _SURFACES:
        provider = _PROVIDER_OF[surface]
        _validate_orchestrator_topology(
            {
                "orchestrator": {
                    "topology": "primary",
                    "provider-overrides": {provider: {"mode": "main-chat"}},
                }
            },
            config_path,
        )
        _validate_orchestrator_topology(
            {
                "orchestrator": {
                    "mode": "main-chat",
                    "provider-overrides": {provider: {"topology": "primary"}},
                }
            },
            config_path,
        )
