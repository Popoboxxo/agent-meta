"""Topology precondition inside the ``# CRITICAL GATE`` section (G1).

Covers issue #1190 (SPEC-orchestrator-mode-topology-2026-11-09, design §5-G1):

- AC-3: an effective ``primary`` position states the *position* (the
  ``orchestrator`` is the session entry, ``strict`` requires that) instead of
  the absolute ``Keine Ausnahmen.`` claim, and names both legal paths
  (delegation, qualified by the provider prerequisite) plus the
  ``orchestrator.mode: main-chat`` escape hatch.
- AC-3/AC-6 continuity: an effective ``subagent`` position renders the
  historic gate block **byte-identically** — the golden string is shared with
  ``tests/test_runtime_gate_rendering.py``.
- AC-14: the rule carries no provider-name condition and never branches on
  ``ORCH_TOPOLOGY_EXPLICIT``; the only new conditional is
  ``ORCH_TOPOLOGY_EFFECTIVE_PRIMARY``.
- #1182: the ``# CRITICAL GATE`` heading (and its tier suffixes) is unchanged —
  the compact path anchors on it (``config/context-anchors.yaml:83``).
- Tiers: the topology changes the *executability*, not the strength of the
  promise, so the ``GATE_PARTIAL``/``GATE_ADVISORY`` provenance paragraph
  survives in both variants.

The render mirrors the production substitute-then-strip order
(``rules.py::sync_rules``) and builds the effective axis from the real T1 seam
(``variables._topology_flags`` + ``variables._effective_topology_flags``).

Run: python3 -m pytest tests/test_use_orchestrator_topology_rendering.py -v
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.providers import runtime_gate_vars  # noqa: E402
from lib.variables import (  # noqa: E402
    _effective_topology_flags,
    _orch_mode_flags,
    _topology_flags,
    strip_inactive_conditional_blocks,
    substitute,
)
from scripts.lib.topology import TopologyResolution  # noqa: E402

_USE_ORCHESTRATOR = _REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md"

# Shared golden string with tests/test_runtime_gate_rendering.py:44-47 —
# the historic strict GATE_ENFORCED block that the ``subagent`` branch (and the
# absent-flag default) must reproduce byte-for-byte.
_ENFORCED_STRICT_BLOCK = (
    "# CRITICAL GATE\n"
    "MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen.\n"
)

_ENFORCED_HEADING = "# CRITICAL GATE"
_PARTIAL_HEADING = "# CRITICAL GATE (runtime-partially enforced)"
_ADVISORY_HEADING = "# CRITICAL GATE (advisory)"
_NEUTRAL_HEADING = "# CRITICAL GATE (neutral)"

_HEADING_PATTERN = re.compile(r"^# CRITICAL GATE(?: \(.+\))?$")

_PROVIDER_NAMES = ("Claude", "Opencode", "Gemini", "Continue", "Copilot", "Mammouth")

_IF_CONDITION = re.compile(r"\{\{#if\s+([^}]*)\}\}")
_WHITESPACE = re.compile(r"\s+")

# Design §5-G1 phrases (whitespace-normalised — the source wraps them).
_POSITION_SENTENCE = "der Session-Einstieg (`strict` verlangt das)"
_PROVIDER_PREREQUISITE = (
    "vorausgesetzt, der Provider lässt diesen Start aus dem Main Chat zu"
)
_DELEGATION_PATH = (
    "nur, wenn sie jede Entwicklungsaufgabe an den `orchestrator` delegiert"
)
_MAIN_CHAT_ESCAPE = "`orchestrator.mode: main-chat`"

# Rev.-1 wording that design §5-G1 deliberately drops: it is false on a
# provider whose main agent may legally spawn (RVW2-1190-04).
_FORBIDDEN_ABSOLUTE_CLAIMS = (
    "kein Spawn-Kanal",
    "cannot run as a subagent",
    "erfüllt dieses Gate nicht",
)

_TOPOLOGY_POSITIONS = ("primary", "subagent")


def _tier_pc(tier: str) -> dict:
    """Machine flags (``ai-providers.yaml`` analogue) that yield ``tier``."""
    if tier == "hook":
        return {"has_hooks": True, "hook_protocol": "claude-code-json"}
    if tier == "plugin":
        return {"has_plugins": True, "plugin_protocol": "opencode-plugin-js"}
    return {}


def _tier_caps(tier: str) -> dict:
    """Declared capability tier (``provider-capabilities.yaml`` analogue)."""
    return {"runtime_gate": tier} if tier in ("permission", "advisory") else {}


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


def _effective_position(effective: str) -> dict:
    """The effective-topology axis exactly as the T1 builder emits it.

    ``primary`` is the derived case (nothing declared), ``subagent`` is this
    repository's declared position (``.meta-config/project.yaml``).
    """
    declared = "" if effective == "primary" else effective
    source = "derived" if effective == "primary" else "project"
    flags = _topology_flags(declared, explicit=bool(declared), source=source)
    flags.update(
        _effective_topology_flags(
            _resolution(declared or None, effective, source), mode="strict"
        )
    )
    return flags


def _gate_flags(tier: str, effective: str | None = None) -> dict:
    """``ORCH_MODE_STRICT`` + the tier bundle + the effective-topology axis.

    ``effective is None`` renders the fail-closed default: the flag is absent
    from the dict (a consumer project that never configures the axis).
    """
    flags = _orch_mode_flags("strict")
    flags.update(runtime_gate_vars(_tier_pc(tier), _tier_caps(tier), {}))
    if effective is not None:
        flags.update(_effective_position(effective))
    return flags


def _render(flags: dict) -> str:
    text = substitute(_USE_ORCHESTRATOR.read_text(encoding="utf-8"), flags, _USE_ORCHESTRATOR.name, None)
    return strip_inactive_conditional_blocks(text, flags)


def _flat(text: str) -> str:
    """Whitespace-normalised text so wrapped sentences stay assertable."""
    return _WHITESPACE.sub(" ", text).strip()


def _gate_section(rendered: str) -> str:
    """The rendered ``# CRITICAL GATE`` block (heading through the last line)."""
    lines = rendered.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith(_ENFORCED_HEADING)), None
    )
    assert start is not None, "no CRITICAL GATE heading rendered"
    end = start
    while end < len(lines) and lines[end].strip():
        end += 1
    return "\n".join(lines[start:end])


def _gate_headings(rendered: str) -> list:
    return [line for line in rendered.splitlines() if line.startswith(_ENFORCED_HEADING)]


def test_strict_gate_primary_states_the_position():
    """AC-3: the effective ``primary`` gate states the position, not the absolute."""
    gate = _flat(_gate_section(_render(_gate_flags("hook", "primary"))))

    assert _POSITION_SENTENCE in gate
    assert _PROVIDER_PREREQUISITE in gate
    assert _MAIN_CHAT_ESCAPE in gate
    assert "Keine Ausnahmen." not in gate


def test_strict_gate_primary_has_no_absolute_claim():
    """AC-3 / RVW2-1190-04: no absolute spawn claim, no provider name, both paths."""
    gate = _flat(_gate_section(_render(_gate_flags("hook", "primary"))))

    for claim in _FORBIDDEN_ABSOLUTE_CLAIMS:
        assert claim not in gate, claim
    for provider in _PROVIDER_NAMES:
        assert provider not in gate, f"provider name in gate text: {provider}"

    # The delegation route is named as a *legal* path, not as impossible.
    assert _DELEGATION_PATH in gate
    assert _MAIN_CHAT_ESCAPE in gate


def test_strict_gate_subagent_is_byte_identical():
    """AC-3/AC-6 continuity: the ``subagent`` branch keeps the historic bytes."""
    for effective in ("subagent", None):
        flags = _gate_flags("hook", effective)
        rendered = _render(flags)

        assert rendered.startswith(_ENFORCED_STRICT_BLOCK), (
            f"effective={effective!r} is not byte-identical to the historic gate"
        )
        assert _POSITION_SENTENCE not in rendered
        assert _MAIN_CHAT_ESCAPE not in rendered


def test_tier_paragraph_survives_both_variants():
    """G1: the topology changes executability, not the strength of the promise."""
    for effective in _TOPOLOGY_POSITIONS:
        partial = _render(_gate_flags("permission", effective))
        assert _PARTIAL_HEADING in partial, effective
        assert "NICHT erzwungen" in partial, effective

        advisory = _render(_gate_flags("advisory", effective))
        assert _ADVISORY_HEADING in advisory, effective
        assert "rein prompt-basiert" in advisory, effective


def test_gate_rule_has_no_provider_or_declared_condition():
    """AC-14: no provider-name condition, no ``ORCH_TOPOLOGY_EXPLICIT`` branch."""
    source = _USE_ORCHESTRATOR.read_text(encoding="utf-8")

    assert "ORCH_TOPOLOGY_EXPLICIT" not in source

    conditions = _IF_CONDITION.findall(source)
    assert conditions, "expected the historic conditional structure"
    for condition in conditions:
        lowered = condition.lower()
        for provider in _PROVIDER_NAMES:
            assert provider.lower() not in lowered, (condition, provider)
        assert re.fullmatch(r"[A-Z0-9_]+", condition), condition

    # The topology precondition is the ONLY new conditional and it lives inside
    # each of the four GATE_* blocks — never outside them (plan §5 Task 7).
    _TOPOLOGY_MARKER = "{{#if ORCH_TOPOLOGY_EFFECTIVE_PRIMARY}}"
    for tier_flag in ("GATE_ENFORCED", "GATE_PARTIAL", "GATE_ADVISORY", "GATE_NEUTRAL"):
        block = re.search(
            r"\{\{#if %s\}\}(.*?)\{\{/if\}\}" % tier_flag, source, re.DOTALL
        )
        assert block, tier_flag
        assert _TOPOLOGY_MARKER in block.group(1), tier_flag
    assert source.count(_TOPOLOGY_MARKER) == 4


def test_critical_gate_heading_is_unchanged():
    """#1182: the compact path anchors on ``# CRITICAL GATE``; never rename it."""
    source = _USE_ORCHESTRATOR.read_text(encoding="utf-8")
    for line in source.splitlines():
        if line.startswith(_ENFORCED_HEADING):
            assert _HEADING_PATTERN.match(line), line

    neutral_flags = _gate_flags("permission")
    neutral_flags.update({"GATE_NEUTRAL": "true", "GATE_PARTIAL": "false"})

    expected = {
        "hook": _ENFORCED_HEADING,
        "permission": _PARTIAL_HEADING,
        "advisory": _ADVISORY_HEADING,
    }
    for effective in _TOPOLOGY_POSITIONS:
        for tier, heading in expected.items():
            rendered = _render(_gate_flags(tier, effective))
            assert _gate_headings(rendered) == [heading], (tier, effective)

        neutral = _render({**neutral_flags, **_effective_position(effective)})
        assert _gate_headings(neutral) == [_NEUTRAL_HEADING], effective

    for tier in expected:
        rendered = _render(_gate_flags(tier, "primary"))
        for line in rendered.splitlines():
            if line.startswith(_ENFORCED_HEADING):
                assert _HEADING_PATTERN.match(line), line

