"""Regression tests for COMPACT_MODE derivation from context_file.mode.

Issue #540 Phase C1: build_variables() must derive the boolean flag
COMPACT_MODE from the new top-level config key context_file.mode. Safe-side
direction is mandatory: True ONLY for mode == "compact" — a missing key, an
invalid value or a non-mapping block must all resolve to False (full mode),
so context compression can never activate by accident.

Also verifies the B2 wiring contract: {{#if COMPACT_MODE}} blocks in context
templates are resolved against exactly this variables dict by
TemplateBuilder.resolve_conditionals().
"""

from pathlib import Path

from scripts.lib.config import build_variables
from scripts.lib.context_templates.builder import TemplateBuilder


def _compact_mode(config: dict) -> str:
    """Run build_variables() and return the derived COMPACT_MODE flag."""
    repo_root = Path(__file__).resolve().parents[1]
    variables, _ = build_variables(config, repo_root)
    return variables["COMPACT_MODE"]


def test_compact_mode_true_when_mode_is_compact():
    assert _compact_mode({"context_file": {"mode": "compact"}}) == "true"


def test_compact_mode_false_when_mode_is_full():
    assert _compact_mode({"context_file": {"mode": "full"}}) == "false"


def test_compact_mode_false_when_key_missing():
    assert _compact_mode({}) == "false"


def test_compact_mode_false_when_value_invalid():
    # Any value other than "compact" (wrong casing, unknown word, wrong type)
    # must fall back to full mode — never enable compression by accident.
    for invalid in ("Compact", "COMPACT", "slim", "", None, True):
        assert _compact_mode({"context_file": {"mode": invalid}}) == "false", (
            f"mode={invalid!r} unexpectedly enabled compact mode"
        )


def test_compact_mode_false_when_context_file_not_a_mapping():
    # Defensive: a scalar context_file block (config typo) must not crash
    # and must not enable compact mode.
    assert _compact_mode({"context_file": "compact"}) == "false"


def test_compact_mode_overrides_stale_user_variable():
    # context_file.mode is the canonical source — a leftover
    # variables.COMPACT_MODE entry in project.yaml must not win.
    config = {
        "context_file": {"mode": "full"},
        "variables": {"COMPACT_MODE": "true"},
    }
    assert _compact_mode(config) == "false"


def test_if_conditional_resolves_against_derived_flag():
    # Wiring contract for B2: TemplateBuilder.resolve_conditionals() evaluates
    # {{#if COMPACT_MODE}} against the build_variables() output dict.
    template = "{{#if COMPACT_MODE}}compact{{else}}full{{/if}}"
    builder = TemplateBuilder(Path(__file__).resolve().parents[1] / "templates")
    compact_vars = {"COMPACT_MODE": "true"}
    full_vars = {"COMPACT_MODE": "false"}
    assert builder.resolve_conditionals(template, compact_vars).strip() == "compact"
    assert builder.resolve_conditionals(template, full_vars).strip() == "full"
