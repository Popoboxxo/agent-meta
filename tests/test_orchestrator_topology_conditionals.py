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

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import standalone as standalone_module  # noqa: E402
from scripts.lib import variables as variables_module  # noqa: E402
from scripts.lib.consistency import placeholders as placeholders_module  # noqa: E402
from scripts.lib.consistency.placeholders import (  # noqa: E402
    _BUILTIN_VARS,
    check_builder_known_set,
)
from scripts.lib.consistency.report import Severity  # noqa: E402
from scripts.lib.standalone import (  # noqa: E402
    _CONDITIONAL_FALSE_FLAGS,
    render_standalone_agent,
)
from scripts.lib.variables import (  # noqa: E402
    _FALSE_DEFAULT_CONDITIONALS,
    _TOPOLOGY_CONDITIONAL_FLAGS,
    strip_inactive_conditional_blocks,
)

_TOPOLOGY_FLAGS = (
    "ORCH_TOPOLOGY_EXPLICIT",
    "ORCH_TOPOLOGY_PRIMARY",
    "ORCH_TOPOLOGY_SUBAGENT",
    "ORCH_TOPOLOGY_HYBRID",
)

# P3 instance flags: registered fail-closed in every channel the render path
# consults. They are not boolean gates (``ORCH_MAX_INSTANCES`` carries the
# count), but an absent value must still resolve to the historic branch.
_INSTANCE_FLAGS = ("ORCH_MAX_INSTANCES", "ORCH_SINGLETON_DECLARED")

# The builder emits these six keys via ``_topology_flags`` (IC-4); every one
# must be registered in the placeholder check (the ratchet is shrink-only).
_TOPOLOGY_BUILDER_VARS = (
    "ORCH_TOPOLOGY",
    "ORCH_TOPOLOGY_EXPLICIT",
    "ORCH_TOPOLOGY_PRIMARY",
    "ORCH_TOPOLOGY_SUBAGENT",
    "ORCH_TOPOLOGY_HYBRID",
    "ORCH_TOPOLOGY_SOURCE",
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


def test_standalone_and_placeholder_registrations_keep_render_identical():
    """Registrations 3-4 (AC-18) exist and change no standalone byte.

    The standalone export is the historical baseline a consumer project sees:
    with ``orchestrator.topology`` unset, adding the fail-closed flags must not
    alter a single byte of an orchestrator-bearing persona.
    """
    for flag in _TOPOLOGY_FLAGS:
        assert _CONDITIONAL_FALSE_FLAGS.get(flag) == "false", (
            f"{flag} must be registered as a literal 'false' in "
            "_CONDITIONAL_FALSE_FLAGS (standalone has no project config)"
        )
    assert _CONDITIONAL_FALSE_FLAGS.get("ORCH_TOPOLOGY") == ""
    assert set(_TOPOLOGY_BUILDER_VARS) <= _BUILTIN_VARS, (
        "every builder-emitted topology variable must be in _BUILTIN_VARS, "
        "not the shrink-only ratchet"
    )

    rendered = render_standalone_agent("orchestrator", _REPO_ROOT)
    committed = (
        _REPO_ROOT / "standalone" / "agents" / "orchestrator.md"
    ).read_text(encoding="utf-8")
    assert rendered == committed


# --- P3 instance-flag registrations (AC-8 flags) ---------------------------

_INSTANCE_PROBE = (
    "Head\n"
    "{{#if ORCH_SINGLETON_DECLARED}}DECLARED{{else}}UNDECLARED{{/if}}\n"
    "{{#if ORCH_MAX_INSTANCES}}MANY{{else}}ONE{{/if}}\n"
    "Tail"
)


def test_instance_flags_are_registered_in_all_static_sets():
    assert set(_INSTANCE_FLAGS) <= set(_FALSE_DEFAULT_CONDITIONALS)
    assert _CONDITIONAL_FALSE_FLAGS.get("ORCH_MAX_INSTANCES") == "1"
    assert _CONDITIONAL_FALSE_FLAGS.get("ORCH_SINGLETON_DECLARED") == "false"
    assert set(_INSTANCE_FLAGS) <= _BUILTIN_VARS


def test_absent_instance_flags_render_the_historic_branch_without_markers():
    rendered = strip_inactive_conditional_blocks(_INSTANCE_PROBE, {})
    assert rendered == "Head\nUNDECLARED\nONE\nTail"
    assert "{{" not in rendered and "}}" not in rendered


def test_instance_flags_are_in_the_strip_whitelist():
    # A present value only activates when the name is in the whitelist; without
    # it the orphaned-marker cleanup would leave the raw markers in the output.
    rendered = strip_inactive_conditional_blocks(
        _INSTANCE_PROBE, {"ORCH_SINGLETON_DECLARED": "true"}
    )
    assert rendered == "Head\nDECLARED\nONE\nTail"
    # ``ORCH_MAX_INSTANCES`` carries "1", never "true": even present it is not a
    # boolean gate (plan K-2), so the count branch stays closed.
    assert "MANY" not in rendered
    assert "{{" not in rendered


def test_builder_known_set_has_no_instance_flag_findings():
    assert check_builder_known_set(_REPO_ROOT) == []


# --- G2 effective-topology flags (issue #1190, Task 2, AC-15) --------------
# The five boolean flags of the *effective* axis are opt-in exactly like the
# declared position flags: an absent value must read INACTIVE (fail-closed),
# otherwise a consumer project that never configures the effective axis would
# render the new branch. The two string flags are audit values and must never
# appear in a boolean registration.

_EFFECTIVE_BOOL_FLAGS = (
    "ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT",
    "ORCH_TOPOLOGY_EFFECTIVE_PRIMARY",
    "ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT",
    "ORCH_TOPOLOGY_EFFECTIVE_HYBRID",
    "ORCH_TOPOLOGY_INERT",
)

_EFFECTIVE_STRING_FLAGS = (
    "ORCH_TOPOLOGY_EFFECTIVE",
    "ORCH_TOPOLOGY_EFFECTIVE_SOURCE",
)

_EFFECTIVE_BUILDER_VARS = _EFFECTIVE_BOOL_FLAGS + _EFFECTIVE_STRING_FLAGS


def _effective_probe(flag: str) -> str:
    return f"Head\n{{{{#if {flag}}}}}NEW{{{{else}}}}OLD{{{{/if}}}}\nTail"


@pytest.mark.parametrize("flag", _EFFECTIVE_BOOL_FLAGS)
def test_new_effective_flags_are_false_default(flag):
    probe = _effective_probe(flag)
    # Absent => engine default (inactive) => else branch only.
    absent = strip_inactive_conditional_blocks(probe, {})
    assert absent == "Head\nOLD\nTail"
    assert "NEW" not in absent
    # An explicit "false" behaves identically to absence.
    assert strip_inactive_conditional_blocks(probe, {flag: "false"}) == "Head\nOLD\nTail"
    # A present "true" proves the name is resolvable (whitelisted), i.e. the
    # conditional actually fires instead of leaking through orphan cleanup.
    assert strip_inactive_conditional_blocks(probe, {flag: "true"}) == "Head\nNEW\nTail"


@pytest.mark.parametrize("flag", _EFFECTIVE_BOOL_FLAGS)
def test_false_default_registration_is_load_bearing(monkeypatch, flag):
    probe = _effective_probe(flag)
    assert strip_inactive_conditional_blocks(probe, {}) == "Head\nOLD\nTail"
    # Drop exactly this flag from `_FALSE_DEFAULT_CONDITIONALS`: the engine's
    # generic default (absent => block active) opens the if-branch.
    monkeypatch.setattr(
        variables_module,
        "_FALSE_DEFAULT_CONDITIONALS",
        frozenset(_FALSE_DEFAULT_CONDITIONALS) - {flag},
    )
    leaked = strip_inactive_conditional_blocks(probe, {})
    assert leaked == "Head\nNEW\nTail"
    assert "OLD" not in leaked


@pytest.mark.parametrize("flag", _EFFECTIVE_BOOL_FLAGS)
def test_strip_whitelist_registration_is_load_bearing(monkeypatch, flag):
    probe = _effective_probe(flag)
    assert strip_inactive_conditional_blocks(probe, {}) == "Head\nOLD\nTail"
    # Drop exactly this flag from the static strip whitelist and keep it absent
    # from the variables dict: the block is no longer resolvable, so the
    # orphaned-marker cleanup keeps both branches instead of picking one.
    monkeypatch.setattr(
        variables_module,
        "_TOPOLOGY_EFFECTIVE_CONDITIONAL_FLAGS",
        frozenset(variables_module._TOPOLOGY_EFFECTIVE_CONDITIONAL_FLAGS) - {flag},
    )
    leaked = strip_inactive_conditional_blocks(probe, {})
    assert "NEW" in leaked and "OLD" in leaked


@pytest.mark.parametrize("flag", _EFFECTIVE_BOOL_FLAGS)
def test_standalone_registration_is_load_bearing(monkeypatch, flag):
    probe = _effective_probe(flag)
    assert strip_inactive_conditional_blocks(probe, dict(_CONDITIONAL_FALSE_FLAGS)) == (
        "Head\nOLD\nTail"
    )
    patched = dict(_CONDITIONAL_FALSE_FLAGS)
    patched.pop(flag)
    monkeypatch.setattr(standalone_module, "_CONDITIONAL_FALSE_FLAGS", patched)
    # Isolate the standalone channel: the engine-wide fail-closed default is
    # also removed for this name, so the literal "false" the standalone dict
    # carries is the only guard left. Without it the if-branch leaks.
    monkeypatch.setattr(
        variables_module,
        "_FALSE_DEFAULT_CONDITIONALS",
        frozenset(_FALSE_DEFAULT_CONDITIONALS) - {flag},
    )
    leaked = strip_inactive_conditional_blocks(probe, patched)
    assert "NEW" in leaked
    # Restoring the standalone entry closes the branch again even though the
    # engine default is still absent.
    assert strip_inactive_conditional_blocks(probe, dict(_CONDITIONAL_FALSE_FLAGS)) == (
        "Head\nOLD\nTail"
    )


@pytest.mark.parametrize("flag", _EFFECTIVE_BOOL_FLAGS)
def test_builtin_vars_registration_is_load_bearing(monkeypatch, flag):
    assert check_builder_known_set(_REPO_ROOT) == []
    real_derive = placeholders_module.derive_builder_vars
    monkeypatch.setattr(
        placeholders_module,
        "_BUILTIN_VARS",
        frozenset(_BUILTIN_VARS) - {flag},
    )
    # The builder emits all seven names in the real pipeline (T1/T3); simulate
    # that output so the check sees the flag as builder-derived.
    monkeypatch.setattr(
        placeholders_module,
        "derive_builder_vars",
        lambda root: real_derive(root) | set(_EFFECTIVE_BUILDER_VARS),
    )
    findings = check_builder_known_set(_REPO_ROOT)
    assert len(findings) == 1
    assert findings[0].severity == Severity.ERROR
    assert findings[0].check == "placeholders.builder-known-set"
    assert flag in findings[0].message


def test_string_flags_are_not_conditionals():
    bool_registrations = (
        _FALSE_DEFAULT_CONDITIONALS,
        _TOPOLOGY_CONDITIONAL_FLAGS,
        variables_module._TOPOLOGY_EFFECTIVE_CONDITIONAL_FLAGS,
        frozenset(_CONDITIONAL_FALSE_FLAGS),
    )
    for flag in _EFFECTIVE_STRING_FLAGS:
        for registration in bool_registrations:
            assert flag not in registration, (
                f"{flag} is an audit string and must not be a boolean conditional"
            )
    # The pre-existing string flags stay out of the three boolean sets too
    # (`_CONDITIONAL_FALSE_FLAGS` carries ORCH_TOPOLOGY="" as render fallback).
    for flag in ("ORCH_TOPOLOGY", "ORCH_TOPOLOGY_SOURCE"):
        for registration in bool_registrations[:3]:
            assert flag not in registration


def test_standalone_and_builtin_vars_carry_new_names():
    for flag in _EFFECTIVE_BOOL_FLAGS:
        assert _CONDITIONAL_FALSE_FLAGS.get(flag) == "false", (
            f"{flag} must be registered as a literal 'false' in "
            "_CONDITIONAL_FALSE_FLAGS (standalone has no project config)"
        )
    assert set(_EFFECTIVE_BUILDER_VARS) <= _BUILTIN_VARS, (
        "all seven effective-axis names (five bool + two audit strings) must be "
        "registered in _BUILTIN_VARS"
    )

