"""Staged ``# CRITICAL GATE`` rendering for the runtime-gate tiers.

Covers the Phase-0 rules output (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13,
IC-07 / F-05):

- AC-05 / AC-15: a hook-tier provider renders the ``GATE_ENFORCED`` block
  **byte-identically** to the historic strict wording (heading
  ``# CRITICAL GATE`` + the sentence ending ``Keine Ausnahmen.``).
- AC-05: a ``permission`` provider renders the PARTIAL variant and must not
  contain the unconditional runtime claim; an ``advisory`` provider renders
  the ADVISORY variant.
- AC-06: after ``strip_inactive_conditional_blocks`` exactly one tier block
  survives, and outside strict mode none is rendered.
- IC-07: the ``a2a-delegation-gates`` tier note names
  ``{{ENFORCEMENT_TIER}}`` and points at the "Bekannte Grenzen" section.

The flags are built from the real Task-3 seam (``providers.runtime_gate_vars``
+ ``variables._orch_mode_flags``) so the test exercises the same bundle the
sync renderers receive, and mirrors the production substitute-then-strip
order (``rules.py::sync_rules``).

Run: python -m pytest tests/test_runtime_gate_rendering.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.providers import runtime_gate_vars
from lib.variables import (
    _orch_mode_flags,
    strip_inactive_conditional_blocks,
    substitute,
)

_USE_ORCHESTRATOR = _REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md"
_A2A_GATES = _REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md"

# Verbatim pre-change strict wording (rules/1-generic/use-orchestrator.md:2-3,
# F-05). The GATE_ENFORCED block must reproduce this byte-for-byte.
_ENFORCED_STRICT_BLOCK = (
    "# CRITICAL GATE\n"
    "MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen."
)

_PARTIAL_HEADING = "# CRITICAL GATE (runtime-partially enforced)"
_ADVISORY_HEADING = "# CRITICAL GATE (advisory)"
_ENFORCED_HEADING = "# CRITICAL GATE"
_NEUTRAL_HEADING = "# CRITICAL GATE (neutral)"


def _tier_pc(tier: str) -> dict:
    """Machine flags (ai-providers.yaml analogue) that yield ``tier``."""
    if tier == "hook":
        return {"has_hooks": True, "hook_protocol": "claude-code-json"}
    if tier == "plugin":
        return {"has_plugins": True, "plugin_protocol": "opencode-plugin-js"}
    return {}


def _tier_caps(tier: str) -> dict:
    """Declared capability tier (provider-capabilities.yaml analogue)."""
    return {"runtime_gate": tier} if tier in ("permission", "advisory") else {}


def _gate_flags(tier: str, orch_mode: str = "strict") -> dict:
    flags = _orch_mode_flags(orch_mode)
    flags.update(runtime_gate_vars(_tier_pc(tier), _tier_caps(tier), {}))
    return flags


def _render(path: Path, flags: dict) -> str:
    text = substitute(path.read_text(encoding="utf-8"), flags, path.name, None)
    return strip_inactive_conditional_blocks(text, flags)


def _gate_headings(rendered: str) -> list:
    return [line for line in rendered.splitlines() if line.startswith(_ENFORCED_HEADING)]


def test_hook_tier_renders_enforced_verbatim():
    """AC-05/AC-15: hook tier is byte-identical to the historic strict block."""
    rendered = _render(_USE_ORCHESTRATOR, _gate_flags("hook"))
    assert rendered.startswith(_ENFORCED_STRICT_BLOCK + "\n")
    assert _PARTIAL_HEADING not in rendered
    assert _ADVISORY_HEADING not in rendered
    assert _gate_headings(rendered) == [_ENFORCED_HEADING]


def test_plugin_tier_renders_enforced_verbatim():
    """GATE_ENFORCED covers ``hook`` and ``plugin`` (tier semantics, OQ-4)."""
    rendered = _render(_USE_ORCHESTRATOR, _gate_flags("plugin"))
    assert rendered.startswith(_ENFORCED_STRICT_BLOCK + "\n")
    assert _gate_headings(rendered) == [_ENFORCED_HEADING]


def test_permission_tier_renders_partial():
    """AC-05: PARTIAL variant, no unconditional runtime claim."""
    rendered = _render(_USE_ORCHESTRATOR, _gate_flags("permission"))
    assert _PARTIAL_HEADING in rendered
    assert "NICHT erzwungen" in rendered
    assert "Keine Ausnahmen." not in rendered
    assert "rein prompt-basiert" not in rendered
    assert _gate_headings(rendered) == [_PARTIAL_HEADING]


def test_advisory_tier_renders_advisory():
    """AC-05: ADVISORY variant, no unconditional runtime claim."""
    rendered = _render(_USE_ORCHESTRATOR, _gate_flags("advisory"))
    assert _ADVISORY_HEADING in rendered
    assert "rein prompt-basiert" in rendered
    assert "Keine Ausnahmen." not in rendered
    assert "NICHT erzwungen" not in rendered
    assert _gate_headings(rendered) == [_ADVISORY_HEADING]


def test_only_one_gate_block_survives():
    """AC-06: conditional stripping leaves exactly the active tier block."""
    expected = {
        "hook": _ENFORCED_HEADING,
        "plugin": _ENFORCED_HEADING,
        "permission": _PARTIAL_HEADING,
        "advisory": _ADVISORY_HEADING,
    }
    for tier, heading in expected.items():
        rendered = _render(_USE_ORCHESTRATOR, _gate_flags(tier))
        assert _gate_headings(rendered) == [heading], (
            f"tier {tier!r}: expected exactly [{heading!r}]"
        )


def test_no_gate_block_outside_strict_mode():
    """AC-06: the tier blocks are nested inside the ORCH_MODE_STRICT guard."""
    rendered = _render(_USE_ORCHESTRATOR, _gate_flags("hook", orch_mode="advisory"))
    assert _gate_headings(rendered) == []
    assert "Keine Ausnahmen." not in rendered


def test_a2a_tier_note_names_tier_and_points_to_known_limits():
    """IC-07: the delegation-gates rule states the active guarantee."""
    source = _A2A_GATES.read_text(encoding="utf-8")
    assert "{{ENFORCEMENT_TIER}}" in source
    assert "Bekannte Grenzen" in source

    for tier in ("hook", "plugin", "permission", "advisory"):
        rendered = _render(_A2A_GATES, _gate_flags(tier))
        assert f"## Runtime-Enforcement-Tier: `{tier}`" in rendered
        assert "{{ENFORCEMENT_TIER}}" not in rendered


def test_neutral_core_renders_directive_without_runtime_promise():
    """AC-23: ``GATE_NEUTRAL`` states the directive, no runtime promise."""
    flags = _gate_flags("permission")
    flags.update({"GATE_NEUTRAL": "true", "GATE_PARTIAL": "false"})
    rendered = _render(_USE_ORCHESTRATOR, flags)
    assert rendered.startswith(_NEUTRAL_HEADING + "\n"), rendered[:80]
    assert "MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`." in rendered
    assert _PARTIAL_HEADING not in rendered
    assert "NICHT erzwungen" not in rendered
    assert "Keine Ausnahmen." not in rendered
    assert "rein prompt-basiert" not in rendered
    assert _gate_headings(rendered) == [_NEUTRAL_HEADING]

    a2a = _render(_A2A_GATES, flags)
    assert "multiple providers" in a2a
    assert "Adapter" in a2a
    assert "{{ENFORCEMENT_TIER}}" not in a2a


def test_neutral_core_state_is_opt_in_by_default():
    """AC-23: an absent ``GATE_NEUTRAL`` never renders the neutral block.

    The render state must be asked for explicitly; the engine's generic
    absent-means-on default must not leak it into the tier renders.
    """
    for tier in ("hook", "plugin", "permission", "advisory"):
        assert _NEUTRAL_HEADING not in _render(_USE_ORCHESTRATOR, _gate_flags(tier))
        assert _NEUTRAL_HEADING not in _render(_A2A_GATES, _gate_flags(tier))
