"""Generic (Claude/Gemini) emission: ``mode: primary`` is opencode-only.

SPEC-orchestrator-mode-topology-2026-11-09 (issue #1190), Task 15 / AC-24.

The 24-cell matrix (``tests/test_orchestrator_mode_topology_matrix.py``) checks
every cell against its own surface; this module pins the cross-surface negative
invariant that makes the matrix trustworthy in the other direction:

* Claude has no ``mode: primary`` concept at all — it is ``main_agent_selectable:
  true`` (``config/provider-capabilities.yaml``), i.e. the main chat MAY spawn
  the orchestrator (the legal ``hook`` channel). A ``mode: primary`` line there
  would invent a mechanism the platform does not have.
* Gemini does not support ``primary``: a declared ``primary`` degrades to the
  fail-safe ``subagent`` and must never be emitted as ``primary``.
* Opencode (v1 and v2) is the ONLY surface that emits ``mode: primary`` — and
  only for the resolved entry position (POS-3). The third test guards against
  over-generalising the first two into "nobody emits it".

Test data may name surfaces; the production code under test is data-driven and
never branches on a provider name.

Run: python3 -m pytest tests/test_provider_transform_topology_generic.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.providers import load_provider_capabilities  # noqa: E402
from tests.test_orchestrator_mode_topology_matrix import (  # noqa: E402
    _MODES,
    _OPENCODE_SURFACES,
    _TOPOLOGIES,
    _Cell,
    _frontmatter,
)

_CAPABILITIES = load_provider_capabilities(_REPO_ROOT)


def test_claude_never_emits_mode_primary() -> None:
    """Every Claude cell: no ``mode: primary``, no ``mode`` key at all."""
    capability = _CAPABILITIES["Claude"]
    assert capability["main_agent_selectable"] is True, (
        "Claude is `main_agent_selectable: true` — the main chat may spawn the "
        "orchestrator (hook tier); that is the legal channel, not a "
        "`mode: primary` entry point."
    )

    for mode in _MODES:
        for topology in _TOPOLOGIES:
            cell = _Cell("Claude", mode, topology)
            content = cell.transformed()
            frontmatter = _frontmatter(content)
            assert "mode: primary" not in content, (
                f"Claude x {mode} x {topology}: emitted a `mode: primary` line; "
                "Claude has no such frontmatter concept."
            )
            assert frontmatter.get("mode") != "primary"
            # The stronger, documented shape: Claude's agent frontmatter carries
            # no `mode` field at all (`permissionMode` is a different key).
            assert "mode" not in frontmatter, (
                f"Claude x {mode} x {topology}: unexpected `mode` key "
                f"{frontmatter.get('mode')!r}"
            )


def test_gemini_never_emits_mode_primary() -> None:
    """A declared ``primary`` degrades to ``subagent`` and is never emitted."""
    for mode in _MODES:
        cell = _Cell("Gemini", mode, "primary")
        assert cell.resolution.declared == "primary"
        assert cell.resolution.effective == "subagent", (
            f"Gemini x {mode}: declared `primary` must degrade to `subagent`, "
            f"got {cell.resolution.effective!r}"
        )
        assert cell.resolution.degraded_from == "primary"

        content = cell.transformed()
        frontmatter = _frontmatter(content)
        assert "mode: primary" not in content, (
            f"Gemini x {mode}: the degraded cell still emitted `mode: primary`."
        )
        assert frontmatter.get("mode") != "primary"
        assert "mode" not in frontmatter


def test_opencode_is_the_only_surface_with_mode_primary() -> None:
    """v1/v2 emit ``mode: primary`` at POS-3 and never at POS-2.

    This is the guard against an over-broad "no surface emits it" reading of
    the two tests above.
    """
    emitting: set[str] = set()

    for surface in ("v1", "v2", "Claude", "Gemini"):
        for mode in ("strict", "advisory"):
            entry = _Cell(surface, mode, "primary")
            expected_effective = "subagent" if surface == "Gemini" else "primary"
            assert entry.resolution.effective == expected_effective
            if "mode: primary" in entry.transformed():
                emitting.add(surface)

            # POS-2 (declared `subagent`): nothing is promoted, on any surface.
            subagent = _Cell(surface, mode, "subagent")
            assert subagent.resolution.effective == "subagent"
            assert "mode: primary" not in subagent.transformed(), (
                f"{surface} x {mode}: POS-2 promoted to `mode: primary`."
            )

    assert emitting == set(_OPENCODE_SURFACES), (
        "only the opencode surfaces may emit `mode: primary`; "
        f"emitting surfaces: {sorted(emitting)}"
    )
