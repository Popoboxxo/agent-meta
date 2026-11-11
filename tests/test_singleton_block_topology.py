"""Topology-aware singleton constraint block (G4, AC-19).

Issue #1190, plan §5 Task 9.

The singleton guard block that ``_finalize_agent_content`` appends to every
spawning agent used to hard-code the ``subagent`` position ("der vom
``main_chat`` gespawnte"). Under ``effective == "primary"`` the orchestrator
*is* the session entry, and under ``ORCH_TOPOLOGY_INERT`` there is no
orchestrator sub-agent instance at all — the wording therefore has to follow
the provider-scoped effective topology (T4/T6), not a literal.

The ``subagent`` variant stays byte-identical to the historic block, including
the deliberately conserved dead "Gate #5" reference (AC-16, spec §5-G4).
"""

from scripts.lib.agent_sync import _singleton_applies, _singleton_constraint_block

# ---------------------------------------------------------------------------
# The historic block, verbatim from agent_sync._finalize_agent_content
# (pre-Task-9 inline literal). This is the AC-16 byte-identity anchor.
# ---------------------------------------------------------------------------
HISTORIC_SUBAGENT_BLOCK = (
    "\n\n## Singleton-Regel: Orchestrator-Spawn (auto-generated)\n\n"
    "**NIEMALS** `task(subagent_type=\"orchestrator\", ...)` oder "
    "`Agent(subagent_type=\"orchestrator\", ...)` aufrufen.\n\n"
    "- Es existiert genau **EIN Orchestrator** pro Session — der vom `main_chat` gespawnte.\n"
    "- Mehrere Orchestrator-Instanzen verursachen Routing-Konflikte und Session-State-Korruption.\n"
    "- Bei unklarem Routing: Ergebnis an den Aufrufer zurückgeben, nicht weiter delegieren.\n\n"
    "> Durchgesetzt via `rules/1-generic/a2a-delegation-gates.md` Gate #5.\n"
)

_NEVER_LINE = (
    "**NIEMALS** `task(subagent_type=\"orchestrator\", ...)` oder "
    "`Agent(subagent_type=\"orchestrator\", ...)` aufrufen."
)


def test_primary_block_names_the_session_entry():
    """``primary``: the orchestrator *is* the entry, not a spawned sub-agent."""
    block = _singleton_constraint_block("primary", inert=False)

    assert "er **ist** der Session-Einstieg" in block
    assert "der vom `main_chat` gespawnte" not in block
    assert _NEVER_LINE in block


def test_subagent_block_is_byte_identical():
    """``subagent``: unchanged — including the consciously conserved Gate #5."""
    block = _singleton_constraint_block("subagent", inert=False)

    assert block == HISTORIC_SUBAGENT_BLOCK
    assert "Gate #5" in block


def test_inert_block_has_no_spawn_claim():
    """``inert`` (mode: main-chat): neutral sentence, no position claim."""
    block = _singleton_constraint_block("subagent", inert=True)

    assert "der vom `main_chat` gespawnte" not in block
    assert "Session-Einstieg" not in block
    assert _NEVER_LINE in block
    # A neutral statement replaces the spawner/entry bullet.
    assert (
        "- In diesem Modus ist der Main Chat Router + Worker; es existiert keine "
        "aktive Orchestrator-Subagent-Instanz." in block
    )


def test_block_is_injected_only_for_spawners():
    """The injection condition is unchanged and independently testable."""
    assert _singleton_applies("orchestrator", can_spawn=True) is False
    assert _singleton_applies("developer-iteration", can_spawn=True) is False
    assert _singleton_applies("developer", can_spawn=True) is True
    assert _singleton_applies("developer", can_spawn=False) is False
