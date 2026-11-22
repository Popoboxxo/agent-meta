"""E-23 / PR 4.1: reduced name_index (E2, AC-R3).

When the roster is already in the harness the name_index is dropped entirely;
otherwise it collapses to one ``name-only:`` line carrying only agent + reason.
Never a per-role description dump (the former ``short_desc/tier`` surface).
"""
from __future__ import annotations

from scripts.lib.intent_routing import render_routing_name_index_line

_ENTRIES = [
    {
        "agent": "principal-developer",
        "short_desc": "Letzte Eskalationsinstanz",
        "tier": "optional",
        "addressability": "name_only",
        "name_only_reason": "last resort",
    },
    {
        "agent": "intern-developer",
        "short_desc": "Triviale Aufgaben",
        "tier": "optional",
        "addressability": "name_only",
        "name_only_reason": "trivial",
    },
]


def test_name_index_reduced_to_agent_and_reason():
    line = render_routing_name_index_line(_ENTRIES, roster_in_harness=False)
    assert line == (
        "name-only: intern-developer (trivial); principal-developer (last resort)"
    )
    assert "short_desc" not in line
    assert "Eskalationsinstanz" not in line


def test_name_index_dropped_when_roster_in_harness():
    assert render_routing_name_index_line(_ENTRIES, roster_in_harness=True) == ""


def test_keyword_roles_do_not_appear_in_name_index_line():
    entries = [{"agent": "developer", "addressability": "keyword"}]
    assert render_routing_name_index_line(entries, roster_in_harness=False) == ""
