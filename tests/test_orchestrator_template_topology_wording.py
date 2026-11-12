"""Three-way topology branches in the orchestrator-bearing templates (#1190 T8).

SPEC-orchestrator-mode-topology-2026-11-09, design §5-G2 "Verwendung"
(AC-14/AC-17/AC-27). The three templates that describe the session entry
(``agents/1-generic/orchestrator.md``, ``agents/1-generic/_reference-agent.md``
and ``rules/1-generic/a2a-delegation-gates.md``) branch on the **effective**
topology, not on the declaration:

* ``ORCH_TOPOLOGY_EFFECTIVE_PRIMARY`` → entry-point wording (the orchestrator
  **is** the session entry; no ``main_chat``-only spawn claim). This is the
  intended change of the round (AC-17) and is *not* covered by the byte
  identity promise.
* ``{{#if ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT}}`` → today's explicit branch,
  word-identical (AC-6/AC-16, this repository is a declared ``subagent``).
* ``{{else}}`` → today's unset/derived-``subagent`` branch, word-identical.

``ORCH_TOPOLOGY_EXPLICIT`` stays an audit flag in the variables dict and may no
longer select a branch (AC-14).

The render mirrors production order: ``substitute()`` then
``strip_inactive_conditional_blocks()``.

Run: python3 -m pytest tests/test_orchestrator_template_topology_wording.py -q
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.variables import (  # noqa: E402
    strip_inactive_conditional_blocks,
    substitute,
)

_ORCHESTRATOR = _REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"
_REFERENCE_AGENT = _REPO_ROOT / "agents" / "1-generic" / "_reference-agent.md"
_A2A_GATES = _REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md"
_GOLDEN_DECLARED_PRIMARY = (
    _REPO_ROOT
    / "tests"
    / "fixtures"
    / "topology-golden"
    / "orchestrator.singleton-declared-primary.md"
)

# --- historic wording, frozen (``git show HEAD:<path>``) --------------------
# Declared ``subagent`` position (``ORCH_TOPOLOGY_EXPLICIT=true``): the branch
# that must stay byte-identical to the pre-T8 templates.
_ORCHESTRATOR_EXPLICIT_BRANCH = (
    "**Singleton (subagent):** Worker → `orchestrator` → HARD REJECT, always. "
    "Only `main_chat` spawns the orchestrator: `primary` = session entry, "
    "`subagent`/`hybrid` = main chat spawns. A position without provider "
    "support degrades loudly to `subagent` "
    "(see `docs/concepts/active/orchestrator-topology.md`)."
)
_REFERENCE_EXPLICIT_BRANCH = (
    "**Singleton (subagent):** Only `main_chat` spawns `orchestrator` "
    "(`primary` = session entry, `subagent`/`hybrid` = main chat spawns); "
    "every worker's `subagent_type: orchestrator` → HARD REJECT. A position "
    "without provider support degrades loudly to `subagent` "
    "(see `docs/concepts/active/orchestrator-topology.md`)."
)
_A2A_EXPLICIT_BLOCK = (
    "2. **Orchestrator-Topologie (subagent):**\n"
    "   G1 Ein Worker dispatcht NIE einen `orchestrator` — HARD REJECT, bei jedem N.\n"
    "   G2 Unter `subagent`/`hybrid` spawnt NUR `main_chat` den Orchestrator; unter\n"
    "      `primary` ist der Orchestrator der Session-Einstieg. Höchstens\n"
    "      1 gleichzeitig (bei 1 gilt der heutige Singleton),\n"
    "      jede mit eindeutiger `orchestrator_id` und disjunktem Scope. Fehlende\n"
    "      oder doppelte ID = HARD ERROR beim Spawn (beide Eigentümer nennen).\n"
    "   G3 Ein Orchestrator dispatcht NIE einen Orchestrator — HARD REJECT.\n"
    "   Der Main Chat ist der einzige Aggregator; fehlende Provider-Unterstützung\n"
    "   degradiert laut auf `subagent`."
)

# Derived ``subagent`` position (flag axis inactive): today's ``{{else}}``.
_ORCHESTRATOR_ELSE_BRANCH = (
    "**Singleton:** Self-spawn (`subagent_type: orchestrator`) → HARD REJECT. "
    "Only `main_chat` may create you."
)
_REFERENCE_ELSE_BRANCH = (
    "**Singleton:** Only `main_chat` spawns `orchestrator`. "
    "`subagent_type: orchestrator` → HARD REJECT."
)
_A2A_ELSE_BRANCH = (
    "2. **Orchestrator-Singleton:** NUR `main_chat` darf den `orchestrator` "
    "spawnen. Worker → `orchestrator` → HARD REJECT "
    "(siehe `singleton-orchestrator-architecture.md`)."
)

# The forbidden claim of the old ``subagent``-only templates (AC-17).
_FORBIDDEN_MAIN_CHAT_ONLY = (
    "Only `main_chat` may create you",
    "NUR `main_chat` darf den `orchestrator` spawnen",
)
# Shared entry-point wording of the primary branch (consistency of the three
# templates, AC-27).
_ENTRY_POINT_CLAIM = "the session entry point"


def _flags(*, primary: bool, explicit: bool, topology: str) -> dict:
    """The topology axis as the renderer builds it (declared + effective)."""
    return {
        "ORCH_TOPOLOGY": topology,
        "ORCH_TOPOLOGY_EXPLICIT": "true" if explicit else "false",
        "ORCH_TOPOLOGY_PRIMARY": "true" if topology == "primary" else "false",
        "ORCH_TOPOLOGY_SUBAGENT": "true" if topology == "subagent" else "false",
        "ORCH_TOPOLOGY_HYBRID": "false",
        "ORCH_TOPOLOGY_SOURCE": "project" if topology else "derived",
        "ORCH_TOPOLOGY_EFFECTIVE": "primary" if primary else "subagent",
        "ORCH_TOPOLOGY_EFFECTIVE_SOURCE": "project" if topology else "derived",
        "ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT": "true" if explicit else "false",
        "ORCH_TOPOLOGY_EFFECTIVE_PRIMARY": "true" if primary else "false",
        "ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT": "false" if primary else "true",
        "ORCH_TOPOLOGY_EFFECTIVE_HYBRID": "false",
        "ORCH_TOPOLOGY_INERT": "false",
        "ORCH_MAX_INSTANCES": "1",
        "ROLE_ORCHESTRATOR_ACTIVE": "true",
    }


def _render(path: Path, flags: dict) -> str:
    source = path.read_text(encoding="utf-8")
    text = substitute(source, flags, path.name, None)
    return strip_inactive_conditional_blocks(text, flags)


def _derived_primary() -> dict:
    return _flags(primary=True, explicit=False, topology="")


def _declared_subagent() -> dict:
    return _flags(primary=False, explicit=True, topology="subagent")


def _declared_primary() -> dict:
    return _flags(primary=True, explicit=True, topology="primary")


def _derived_subagent() -> dict:
    return _flags(primary=False, explicit=False, topology="")


def test_derived_primary_has_no_main_chat_only_claim():
    """AC-17: an effective ``primary`` states the entry, not a spawn absolute."""
    flags = _derived_primary()
    orchestrator = _render(_ORCHESTRATOR, flags)
    a2a = _render(_A2A_GATES, flags)

    assert "Only `main_chat` may create you" not in orchestrator
    assert "NUR `main_chat` darf den `orchestrator` spawnen" not in a2a

    # Positive side: the entry-point wording actually rendered (a vanishing
    # block must not turn this test green by accident).
    assert _ENTRY_POINT_CLAIM in orchestrator
    assert "Session-Einstieg" in a2a


def test_declared_subagent_keeps_historic_wording():
    """AC-6/AC-16: this repo's declared ``subagent`` stays byte-identical."""
    flags = _declared_subagent()

    orchestrator = _render(_ORCHESTRATOR, flags)
    assert _ORCHESTRATOR_EXPLICIT_BRANCH in orchestrator
    assert _ORCHESTRATOR_ELSE_BRANCH not in orchestrator

    reference = _render(_REFERENCE_AGENT, flags)
    assert _REFERENCE_EXPLICIT_BRANCH in reference
    assert _REFERENCE_ELSE_BRANCH not in reference

    a2a = _render(_A2A_GATES, flags)
    assert _A2A_EXPLICIT_BLOCK in a2a
    assert _A2A_ELSE_BRANCH not in a2a


def test_declared_primary_has_a_golden_fixture():
    """AC-27: the declared ``primary`` singleton paragraph is frozen."""
    rendered = _render(_ORCHESTRATOR, _declared_primary())
    paragraph = next(
        (
            line
            for line in rendered.splitlines()
            if line.startswith("**Singleton (session entry):**")
        ),
        None,
    )
    assert paragraph is not None, "no primary singleton paragraph rendered"

    golden = _GOLDEN_DECLARED_PRIMARY.read_text(encoding="utf-8").strip()
    assert paragraph == golden


def test_derived_subagent_keeps_historic_else_branch():
    """AC-16: an unset/derived ``subagent`` keeps today's ``{{else}}`` text."""
    flags = _derived_subagent()

    orchestrator = _render(_ORCHESTRATOR, flags)
    assert _ORCHESTRATOR_ELSE_BRANCH in orchestrator
    assert _ORCHESTRATOR_EXPLICIT_BRANCH not in orchestrator

    reference = _render(_REFERENCE_AGENT, flags)
    assert _REFERENCE_ELSE_BRANCH in reference
    assert _REFERENCE_EXPLICIT_BRANCH not in reference

    a2a = _render(_A2A_GATES, flags)
    assert _A2A_ELSE_BRANCH in a2a
    assert _A2A_EXPLICIT_BLOCK not in a2a


def test_reference_agent_matches_orchestrator_wording():
    """AC-27: all three templates agree on the session-entry claim."""
    flags = _derived_primary()
    orchestrator = _render(_ORCHESTRATOR, flags)
    reference = _render(_REFERENCE_AGENT, flags)

    assert _ENTRY_POINT_CLAIM in orchestrator
    assert _ENTRY_POINT_CLAIM in reference
    for rendered in (orchestrator, reference):
        assert "Only `main_chat`" not in rendered


def test_no_declared_conditional_left_for_semantics():
    """AC-14: ``ORCH_TOPOLOGY_EXPLICIT`` is an audit flag, never a branch."""
    declared_conditional = re.compile(
        r"\{\{#if[^}]*ORCH_TOPOLOGY_EXPLICIT[^}]*\}\}"
    )
    for path in (_ORCHESTRATOR, _REFERENCE_AGENT, _A2A_GATES):
        source = path.read_text(encoding="utf-8")
        assert declared_conditional.search(source) is None, path
        assert "{{#if ORCH_TOPOLOGY_EFFECTIVE_PRIMARY}}" in source, path
        assert "{{#if ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT}}" in source, path
