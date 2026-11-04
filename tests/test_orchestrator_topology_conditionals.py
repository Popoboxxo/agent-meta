"""Fail-closed conditional registration tests (AC-18).

SPEC-orchestrator-topology-2026-11-03, P1 (issue #1077), Task 8.

An absent topology variable must read as INACTIVE. The engine's generic
default is the opposite (an absent variable keeps its ``{{#if}}`` block), so
the four boolean flags are registered in ``_FALSE_DEFAULT_CONDITIONALS`` and
their names are in the internally built ``conditional_vars`` whitelist of
``strip_inactive_conditional_blocks`` — even when the variables dict does not
carry them yet. Otherwise the new branch renders in every consumer project
that has not set ``orchestrator.topology`` (AC-6/AC-18).

Run: python3 -m pytest tests/test_orchestrator_topology_conditionals.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.consistency.placeholders import (  # noqa: E402
    check_builder_known_set,
)
from scripts.lib.variables import (  # noqa: E402
    _FALSE_DEFAULT_CONDITIONALS,
    strip_inactive_conditional_blocks,
)

_TOPOLOGY_FLAGS = (
    "ORCH_TOPOLOGY_EXPLICIT",
    "ORCH_TOPOLOGY_PRIMARY",
    "ORCH_TOPOLOGY_SUBAGENT",
    "ORCH_TOPOLOGY_HYBRID",
)

# Mirrors the intended consumer shape: a new branch, an else branch that keeps
# the historic wording, and a nested role-activity gate inside the else. The
# role flag is always present in a real render (build_variables emits it), so
# the probe carries it; the topology flag is the one under test.
_PROBE_TEMPLATE = (
    "Head\n"
    "{{#if ORCH_TOPOLOGY_EXPLICIT}}NEW{{else}}"
    "{{#if ROLE_ORCHESTRATOR_ACTIVE}}OLD{{/if}}{{/if}}\n"
    "Tail"
)
_ROLE_ACTIVE = {"ROLE_ORCHESTRATOR_ACTIVE": "true"}


def test_false_default_conditionals_register_all_four_topology_flags():
    assert set(_TOPOLOGY_FLAGS) <= set(_FALSE_DEFAULT_CONDITIONALS)


def test_absent_variable_renders_the_else_branch_only():
    rendered = strip_inactive_conditional_blocks(_PROBE_TEMPLATE, dict(_ROLE_ACTIVE))
    assert rendered == "Head\nOLD\nTail"
    assert "NEW" not in rendered
    assert rendered.count("OLD") == 1


def test_absent_explicit_with_present_position_flags_renders_else_branch():
    """The explicit flag stays inactive even when its siblings are present."""
    rendered = strip_inactive_conditional_blocks(
        _PROBE_TEMPLATE,
        {
            **_ROLE_ACTIVE,
            "ORCH_TOPOLOGY_PRIMARY": "false",
            "ORCH_TOPOLOGY_SUBAGENT": "true",
            "ORCH_TOPOLOGY_HYBRID": "false",
        },
    )
    assert rendered == "Head\nOLD\nTail"
    assert "NEW" not in rendered


def test_explicit_true_renders_the_new_branch_only():
    rendered = strip_inactive_conditional_blocks(
        _PROBE_TEMPLATE, {**_ROLE_ACTIVE, "ORCH_TOPOLOGY_EXPLICIT": "true"}
    )
    assert rendered == "Head\nNEW\nTail"
    assert "OLD" not in rendered


def test_explicit_false_renders_the_else_branch_only():
    rendered = strip_inactive_conditional_blocks(
        _PROBE_TEMPLATE, {**_ROLE_ACTIVE, "ORCH_TOPOLOGY_EXPLICIT": "false"}
    )
    assert rendered == "Head\nOLD\nTail"
    assert "NEW" not in rendered


def test_builder_known_set_is_clean():
    assert check_builder_known_set(_REPO_ROOT) == []
