"""Provider-less global topology flags and provider-scoped re-resolution (IC-4).

SPEC-orchestrator-topology-2026-11-03, P1 (issue #1077), Task 10.

Contract under test:

* ``config.build_variables`` runs without a provider. Its ``ORCH_TOPOLOGY*``
  block is therefore the **project-level declaration** — the project key or
  ``""`` — never a provider-derived resolution. A project override alone must
  not make the global block explicit (AC-6/AC-18 byte identity).
* Every provider-scoped render path re-resolves the *declared* value with
  ``provider=...`` and overwrites the global pair. ``rules._merged_rule_vars``
  must also work for ``variables=None`` callers (S23) and build the flags
  itself; on that path an undeclared key must still render the else branch
  (fail-closed default, AC-18).

Run: python3 -m pytest tests/test_orchestrator_topology_global_flags.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.config import build_variables  # noqa: E402
from scripts.lib.rules import _merged_rule_vars  # noqa: E402
from scripts.lib.variables import strip_inactive_conditional_blocks  # noqa: E402

_POSITION_FLAGS = (
    "ORCH_TOPOLOGY_PRIMARY",
    "ORCH_TOPOLOGY_SUBAGENT",
    "ORCH_TOPOLOGY_HYBRID",
)

# The rule-render shape: the topology gate with its historic else branch. No
# nested role gate here — ``variables=None`` callers have no ROLE_* bundle, and
# rule templates do not reference it.
_PROBE_TEMPLATE = (
    "Head\n"
    "{{#if ORCH_TOPOLOGY_EXPLICIT}}NEW{{else}}OLD{{/if}}\n"
    "Tail"
)


def _global_vars(config: dict) -> dict:
    variables, _warnings = build_variables(config, _REPO_ROOT)
    return variables


def _assert_all_positions_false(variables: dict) -> None:
    assert variables["ORCH_TOPOLOGY"] == ""
    assert all(variables[flag] == "false" for flag in _POSITION_FLAGS)


# --- provider-less global contract -----------------------------------------


def test_build_variables_without_provider_never_derives_a_position():
    variables = _global_vars({})

    _assert_all_positions_false(variables)
    assert variables["ORCH_TOPOLOGY_EXPLICIT"] == "false"
    assert variables["ORCH_TOPOLOGY_SOURCE"] == "derived"

    # A provider override is a provider-scope declaration. It must not leak
    # into the provider-less block, which stays undeclared and fail-closed.
    override_only = _global_vars({
        "orchestrator": {
            "provider-overrides": {"Claude": {"topology": "primary"}},
        },
    })
    _assert_all_positions_false(override_only)
    assert override_only["ORCH_TOPOLOGY_EXPLICIT"] == "false"


def test_build_variables_global_block_is_the_project_declaration():
    variables = _global_vars({"orchestrator": {"topology": "primary"}})

    assert variables["ORCH_TOPOLOGY"] == "primary"
    assert variables["ORCH_TOPOLOGY_PRIMARY"] == "true"
    assert variables["ORCH_TOPOLOGY_SUBAGENT"] == "false"
    assert variables["ORCH_TOPOLOGY_HYBRID"] == "false"
    assert variables["ORCH_TOPOLOGY_EXPLICIT"] == "true"
    assert variables["ORCH_TOPOLOGY_SOURCE"] == "project"


# --- provider-scoped re-resolution -----------------------------------------


def test_provider_scoped_render_overrides_the_global_value():
    config = {
        "orchestrator": {
            "topology": "primary",
            "provider-overrides": {"Claude": {"topology": "subagent"}},
        },
    }
    global_vars = _global_vars(config)
    assert global_vars["ORCH_TOPOLOGY"] == "primary"
    assert global_vars["ORCH_TOPOLOGY_PRIMARY"] == "true"

    scoped = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, config, "Claude", {}, global_vars,
        active_set=frozenset(),
    )
    assert scoped["ORCH_TOPOLOGY"] == "subagent"
    assert scoped["ORCH_TOPOLOGY_SUBAGENT"] == "true"
    assert scoped["ORCH_TOPOLOGY_PRIMARY"] == "false"
    assert scoped["ORCH_TOPOLOGY_EXPLICIT"] == "true"
    assert scoped["ORCH_TOPOLOGY_SOURCE"] == "provider-override"

    # Another provider keeps the project declaration (no cross-provider leak).
    other = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, config, "Gemini", {}, global_vars,
        active_set=frozenset(),
    )
    assert other["ORCH_TOPOLOGY"] == "primary"
    assert other["ORCH_TOPOLOGY_PRIMARY"] == "true"


# --- variables=None path (S23) ---------------------------------------------


def test_merged_rule_vars_without_variables_builds_flags_fail_closed():
    merged = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, {}, "Claude", {}, None,
        active_set=frozenset(),
    )

    _assert_all_positions_false(merged)
    assert merged["ORCH_TOPOLOGY_EXPLICIT"] == "false"

    rendered = strip_inactive_conditional_blocks(_PROBE_TEMPLATE, merged)
    assert rendered == "Head\nOLD\nTail"
    assert "NEW" not in rendered
