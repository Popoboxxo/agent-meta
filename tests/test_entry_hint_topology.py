"""Topology-aware entry-point hint (SPEC orchestrator topology §5-G5, AC-20/AC-24).

The entry hint (``> **Einstiegspunkt:** …``) is a position statement, so it may
only be rendered where the renderer knows the physical file's readers:

* provider-own file + ``effective == primary`` -> names the session entry;
* provider-own file + ``effective == subagent`` -> the historic wording
  byte-for-byte (AC-16, this repository's own position);
* ``mode: main-chat`` -> the historic main-chat wording, byte-for-byte;
* shared file whose active sharers resolve to *different* positions -> the
  neutral text from §5-G5 (no position claim that would be false for one of
  the readers, and no ordering-dependent oscillation).

``build_agent_hints`` only selects the text block; the decision lives in
``context._position_aware_agent_hints`` (provider, target file and sharer set
are known there). The last test pins AC-24's prose consequence: under
``mode: main-chat`` the orchestrator role is not emitted, so
``ROLE_ORCHESTRATOR_ACTIVE`` must be ``"false"`` and the A2A gate must render
the role-inactive wording.

Run: ``python3 -m pytest tests/test_entry_hint_topology.py``
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import build_variables  # noqa: E402
from lib.context import _position_aware_agent_hints  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402
from lib.variables import strip_inactive_conditional_blocks, substitute  # noqa: E402

_RULE = _REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md"
_INACTIVE_GOLDEN = (
    _REPO_ROOT / "tests" / "fixtures" / "topology-golden"
    / "a2a-delegation-gates.role-inactive.md"
)

#: The historic subagent wording (``agents.py``), unchanged by this feature.
SUBAGENT_HINT = (
    "> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle "
    "Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal "
    "Router«."
)

#: The primary wording (AC-20): names the entry, no absolute spawnability claim.
PRIMARY_HINT = (
    "> **Einstiegspunkt:** Diese Session startet im `orchestrator`-Agenten. Ein "
    "Start im Main Chat erfüllt das Gate nur bei Delegation an den "
    "`orchestrator` — siehe `use-orchestrator.md`."
)

#: The neutral wording for a shared file with mixed sharer positions (§5-G5).
NEUTRAL_HINT = (
    "> **Einstiegspunkt:** Entwicklungsaufgaben laufen über den "
    "`orchestrator`-Agenten. Ob er der Session-Einstieg ist oder ein Subagent, "
    "hängt von `orchestrator.topology` ab — siehe `use-orchestrator.md`."
)

#: The historic main-chat wording, unchanged by this feature.
MAIN_CHAT_HINT = (
    "> **Einstiegspunkt:** Du bist im `main-chat` Modus. Du agierst direkt als "
    "Router und Worker (siehe `use-orchestrator.md`)."
)

#: Providers sharing the physical ``AGENTS.md`` (config/ai-providers.yaml).
_AGENTS_MD_SHARERS = ("Gemini", "Opencode")


def _config(**orchestrator) -> dict:
    """Single-provider Claude config; knowledge engine off for exact text asserts."""
    return {
        "ai-providers": ["Claude"],
        "knowledge-engine": {"enabled": False},
        "orchestrator": orchestrator,
    }


def _shared_config(**orchestrator) -> dict:
    """Two-provider config whose providers share ``AGENTS.md``."""
    return {
        "ai-providers": list(_AGENTS_MD_SHARERS),
        "knowledge-engine": {"enabled": False},
        "orchestrator": orchestrator,
    }


def _hint(config: dict, provider: str, provider_config: dict,
          target: str, position: str) -> str:
    """Render the hint-only variant (``AGENT_HINTS_CLAUDE``) for *provider*."""
    hints = _position_aware_agent_hints(
        config, provider, provider_config, _REPO_ROOT, target,
        active_set=None, position=position,
    )
    return hints["AGENT_HINTS_CLAUDE"]


def _golden_gate_line() -> str:
    """The role-inactive gate-2 line, taken verbatim from the frozen fixture."""
    lines = [
        line for line in _INACTIVE_GOLDEN.read_text(encoding="utf-8").splitlines()
        if "Worker" in line and "HARD REJECT" in line
    ]
    assert len(lines) == 1, f"expected exactly one gate-2 line, got {lines!r}"
    return lines[0]


def test_hint_primary_names_the_entry():
    """AC-20: a provider-own file at ``primary`` names the session entry."""
    hint = _hint(
        _config(mode="strict", topology="primary"), "Claude",
        load_providers_config(_REPO_ROOT), "CLAUDE.md", "primary",
    )
    assert hint == PRIMARY_HINT
    # No absolute spawnability claim: an unverified provider may still be able
    # to run the role as a subagent (spec §5-G5 safe side).
    assert "cannot run as a subagent" not in hint
    assert "kein Spawn-Kanal" not in hint


def test_hint_subagent_keeps_historic_wording():
    """AC-16: ``subagent`` renders the historic string byte-identically."""
    hint = _hint(
        _config(mode="strict", topology="subagent"), "Claude",
        load_providers_config(_REPO_ROOT), "CLAUDE.md", "subagent",
    )
    assert hint == SUBAGENT_HINT


def test_hint_main_chat_is_unchanged():
    """AC-20: ``mode: main-chat`` keeps today's text, regardless of position."""
    provider_config = load_providers_config(_REPO_ROOT)
    for position in ("primary", "subagent", "neutral"):
        hint = _hint(
            _config(mode="main-chat"), "Claude", provider_config,
            "CLAUDE.md", position,
        )
        assert hint == MAIN_CHAT_HINT, position


def test_shared_hint_is_provider_neutral():
    """AC-20: mixed sharer positions render the neutral text for every sharer.

    ``Opencode`` is forced to ``primary`` via the provider override while
    ``Gemini`` stays on the project ``subagent``. The assertion is on the
    rendered string (not on flags) and must be identical for both sharers --
    whichever one writes the shared file first.
    """
    config = _shared_config(
        mode="strict",
        topology="subagent",
        **{"provider-overrides": {"Opencode": {"topology": "primary"}}},
    )
    provider_config = load_providers_config(_REPO_ROOT)
    as_opencode = _hint(config, "Opencode", provider_config, "AGENTS.md", "primary")
    as_gemini = _hint(config, "Gemini", provider_config, "AGENTS.md", "subagent")
    assert as_opencode == NEUTRAL_HINT
    assert as_gemini == NEUTRAL_HINT
    assert as_opencode == as_gemini


def test_same_position_shared_hint_keeps_the_position_from_text():
    """AC-16: agreeing sharers keep their position text (no position loss)."""
    config = _shared_config(mode="strict", topology="subagent")
    provider_config = load_providers_config(_REPO_ROOT)
    for provider in _AGENTS_MD_SHARERS:
        hint = _hint(config, provider, provider_config, "AGENTS.md", "subagent")
        assert hint == SUBAGENT_HINT, provider


def test_hint_is_deterministic_for_shared_context():
    """AC-20: swapping the provider order must not change the rendered text."""
    config = _shared_config(
        mode="strict",
        topology="subagent",
        **{"provider-overrides": {"Opencode": {"topology": "primary"}}},
    )
    provider_config = load_providers_config(_REPO_ROOT)
    reversed_config = dict(reversed(list(provider_config.items())))
    forward = _hint(config, "Opencode", provider_config, "AGENTS.md", "primary")
    backward = _hint(config, "Opencode", reversed_config, "AGENTS.md", "primary")
    assert forward == backward == NEUTRAL_HINT


def test_role_orchestrator_active_under_main_chat_prose():
    """AC-24: ``main-chat`` deactivates the orchestrator role's prose.

    The role is not emitted in that mode (``role_emitted_for_provider``), so
    ``ROLE_ORCHESTRATOR_ACTIVE`` must be false and the A2A gate must render the
    frozen role-inactive gate-2 line, not ``Worker → `orchestrator` → HARD
    REJECT``.
    """
    config = {"ai-providers": ["Claude"], "orchestrator": {"mode": "main-chat"}}
    variables, _warnings = build_variables(
        config, _REPO_ROOT, project_root=_REPO_ROOT
    )
    assert variables["ROLE_ORCHESTRATOR_ACTIVE"] == "false"

    source = _RULE.read_text(encoding="utf-8")
    rendered = substitute(source, variables, _RULE.name, SyncLog())
    rendered = strip_inactive_conditional_blocks(rendered, variables)
    gate_lines = [
        line for line in rendered.splitlines()
        if "Worker" in line and "HARD REJECT" in line
    ]
    assert len(gate_lines) == 1, gate_lines
    assert gate_lines[0] == _golden_gate_line()
