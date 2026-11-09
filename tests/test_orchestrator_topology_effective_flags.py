"""Effective-topology render flags (G2, AC-15/AC-16/AC-21/AC-30).

Issue #1190, plan §5 Tasks 1 and 3.

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

Task 3 adds the global (provider-LESS) basis in
``config._build_orch_variables``. That dict is explicitly *non-authoritative*:
every provider-scoped render seam overwrites the seven flags via
``_provider_topology_flags`` (T4–T6). The AC-30 ratchet below fails if a render
seam starts reading (or importing) the global basis directly.

Run: python3 -m pytest tests/test_orchestrator_topology_effective_flags.py -q
"""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import config as config_module  # noqa: E402
from scripts.lib.topology import (  # noqa: E402
    VALID_TOPOLOGIES,
    TopologyResolution,
    resolve_topology,
)
from scripts.lib.variables import (  # noqa: E402
    _effective_topology_flags,
    _topology_flags,
)

#: Provider-scoped render seams (plan §5 Tasks 4–6). From T4 onward they MUST
#: call the provider-aware helper; touching the global basis is AC-30 failure.
_RENDER_SEAMS = (
    "rules.py",
    "context.py",
    "agent_sync.py",
    "sync_pipeline.py",
    "agents.py",
    "isolation.py",
    "provider_transform.py",
)

#: The provider-less helper under ratchet — only ``config.py`` may call/import it.
_GLOBAL_BASIS_HELPER = "_effective_topology_flags"

_LIB_ROOT = _REPO_ROOT / "scripts" / "lib"

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


# --- Task 3: the provider-less (non-authoritative) global basis -------------


def _global_orch_vars(orchestrator_cfg: dict) -> dict:
    """Run the real global builder and return the produced variables dict."""
    variables: dict = {}
    config_module._build_orch_variables(
        variables,
        [],
        {"orchestrator": orchestrator_cfg},
        _REPO_ROOT,
        project_root=_REPO_ROOT,
    )
    return variables


def test_global_block_is_declared_or_failsafe():
    unset = _global_orch_vars({})

    assert unset["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert unset["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "false"
    assert unset["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "false"
    assert unset["ORCH_TOPOLOGY_INERT"] == "false"
    assert unset["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "derived"
    # The declaration flags keep their IC-4 meaning and are not rewritten.
    assert unset["ORCH_TOPOLOGY"] == ""
    assert unset["ORCH_TOPOLOGY_EXPLICIT"] == "false"

    declared = _global_orch_vars({"topology": "primary"})

    assert declared["ORCH_TOPOLOGY_EFFECTIVE"] == "primary"
    assert declared["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "true"
    assert declared["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "project"
    assert declared["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert declared["ORCH_TOPOLOGY"] == "primary"
    assert declared["ORCH_TOPOLOGY_EXPLICIT"] == "true"

    # Unknown value fails safe to "subagent" here; the hard enum error stays in
    # _validate_orchestrator_topology.
    bogus = _global_orch_vars({"topology": "bogus"})

    assert bogus["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert bogus["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"
    assert bogus["ORCH_TOPOLOGY"] == ""  # _topology_flags fails closed


def test_global_block_honours_main_chat():
    flags = _global_orch_vars({"mode": "main-chat"})

    assert flags["ORCH_MODE_MAIN_CHAT"] == "true"
    assert flags["ORCH_TOPOLOGY_INERT"] == "true"
    # INERT expresses the main-chat case; the position basis is unchanged.
    assert flags["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"


def test_global_block_is_documented_as_non_authoritative():
    source = inspect.getsource(config_module._build_orch_variables)

    assert "non-authoritative basis" in source, (
        "the global basis block must be documented as non-authoritative "
        "(RVW2-1190-09) so no seam treats it as a provider resolution"
    )

    # The produced values are the fail-safe basis, not a provider resolution:
    # a provider override must never leak into the provider-less dict.
    flags = _global_orch_vars(
        {"provider-overrides": {"Claude": {"topology": "primary"}}}
    )

    assert flags["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "false"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "derived"
    assert flags["ORCH_TOPOLOGY"] == ""


def _basis_references(path: Path) -> tuple[list[int], list[int]]:
    """Return (call line numbers, import line numbers) for the global helper."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: list[int] = []
    imports: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            is_basis_call = (
                isinstance(func, ast.Name) and func.id == _GLOBAL_BASIS_HELPER
            ) or (
                isinstance(func, ast.Attribute)
                and func.attr == _GLOBAL_BASIS_HELPER
            )
            if is_basis_call:
                calls.append(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == _GLOBAL_BASIS_HELPER:
                    imports.append(node.lineno)
    return calls, imports


def test_no_render_seam_reads_the_global_basis():
    """AC-30 ratchet: only config.py may consume the provider-less basis."""
    definition = (_LIB_ROOT / "variables.py").read_text(encoding="utf-8")
    assert f"def {_GLOBAL_BASIS_HELPER}(" in definition, (
        "ratchet target vanished from variables.py — update the ratchet with "
        "the new helper name instead of deleting it"
    )

    callers: dict[str, list[int]] = {}
    importers: dict[str, list[int]] = {}
    for path in sorted(_LIB_ROOT.rglob("*.py")):
        rel = path.relative_to(_LIB_ROOT).as_posix()
        if rel == "variables.py":  # the definition itself
            continue
        calls, imports = _basis_references(path)
        if calls:
            callers[rel] = calls
        if imports:
            importers[rel] = imports

    assert list(callers) == ["config.py"], (
        f"only the global builder may call {_GLOBAL_BASIS_HELPER}; "
        f"render seams must use _provider_topology_flags. Found: {callers}"
    )
    assert list(importers) == ["config.py"], (
        f"only the global builder may import {_GLOBAL_BASIS_HELPER}; "
        f"direct imports bypass the provider override. Found: {importers}"
    )

    # Explicit per-seam pin: a seam must neither call nor import the basis.
    for seam in _RENDER_SEAMS:
        assert seam not in callers, (
            f"render seam {seam} calls the provider-less "
            f"{_GLOBAL_BASIS_HELPER} — use _provider_topology_flags (AC-30)"
        )
        assert seam not in importers, (
            f"render seam {seam} imports the provider-less "
            f"{_GLOBAL_BASIS_HELPER} — use _provider_topology_flags (AC-30)"
        )

