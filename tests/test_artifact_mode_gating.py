"""Artifact-mode gating (#1209 / Roadmap PR 3.4, SPEC-artifact-mode-gating-2026-11-20).

TDD contract tests for E-T8: the two derived template-gate flags
``ARTIFACT_<CLASS>_MODE_FILES`` / ``..._MODE_INLINE``, the renderer suffix
whitelist and the absent-config default (Entscheidung 56, spec §3.1-§3.4).

OFFEN-1 (which of the 26 templates carry gates) and OFFEN-2 (the content of
the Kern-AC-05 contract change) are deliberately open in the approved spec.
``test_gated_templates_enumeration`` (AC-I4) and any Kern-AC-05 test change
are therefore NOT part of this file — those decisions must not be invented.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.config import build_variables  # noqa: E402
from lib.consistency import placeholders as ph  # noqa: E402
from lib.variables import (  # noqa: E402
    _FALSE_DEFAULT_CONDITIONALS,
    _conditional_active,
    strip_inactive_conditional_blocks,
    substitute,
)

GATE_SUFFIXES = ("_MODE_FILES", "_MODE_INLINE")


def test_mode_flags_derived_from_mode():
    """AC-I6 (spec §3.1): the exact value table for files / inline / off."""
    from lib.artifact_locations import artifact_mode_flags

    assert artifact_mode_flags("files") == ("true", "false")
    assert artifact_mode_flags("inline") == ("false", "true")
    assert artifact_mode_flags("off") == ("false", "false")


def test_builder_derives_mode_flags_per_class():
    """AC-I6: the builder exports exactly two gate flags per artifact class."""
    config = {"artifact-locations": {"enabled": True, "classes": {
        "specs": {"mode": "inline"},
        "plans": {"mode": "off", "fallback-parent": "specs"},
    }}}
    variables = build_variables(config, ROOT, None)[0]
    assert variables["ARTIFACT_SPECS_MODE_FILES"] == "false"
    assert variables["ARTIFACT_SPECS_MODE_INLINE"] == "true"
    assert variables["ARTIFACT_PLANS_MODE_FILES"] == "false"
    assert variables["ARTIFACT_PLANS_MODE_INLINE"] == "false"
    # Unconfigured classes keep today's default (files).
    assert variables["ARTIFACT_REVIEWS_MODE_FILES"] == "true"
    assert variables["ARTIFACT_REVIEWS_MODE_INLINE"] == "false"


def test_mode_off_removes_block_and_mode_files_keeps_it():
    """AC-I2: off drops the gated block, files keeps it."""
    text = "A\n{{#if ARTIFACT_SPECS_MODE_FILES}}kept{{/if}}\nB\n"
    off = {"ARTIFACT_SPECS_MODE_FILES": "false"}
    files = {"ARTIFACT_SPECS_MODE_FILES": "true"}
    assert strip_inactive_conditional_blocks(text, off) == "A\nB\n"
    assert strip_inactive_conditional_blocks(text, files) == "A\nkept\nB\n"


def test_absent_config_renders_byte_identical():
    """AC-I1: without config the gate renders byte-identically to today."""
    text = "A\n{{#if ARTIFACT_SPECS_MODE_FILES}}kept{{/if}}\nB\n"
    variables = build_variables({}, ROOT, None)[0]
    assert strip_inactive_conditional_blocks(text, variables) == (
        strip_inactive_conditional_blocks(text, {})
    )


def test_no_unresolved_artifact_if_marker_survives_render():
    """AC-I3: no unresolved gate marker survives strip + substitute."""
    template = (
        "{{#if ARTIFACT_SPECS_MODE_FILES}}"
        "{{ARTIFACT_SPECS_DIR}}\n"
        "{{/if}}"
    )
    variables = build_variables({}, ROOT, None)[0]
    rendered = substitute(template, variables, "mode-gating-probe", None)
    rendered = strip_inactive_conditional_blocks(rendered, variables)
    assert "{{" not in rendered
    assert "#if" not in rendered
    assert "docs/specs" in rendered


def test_zip_cmd_not_swallowed_by_whitelist():
    """AC-I5 (Abweichung 10): suffix match, not prefix match."""
    text = (
        "{{#if ARTIFACT_ZIP_CMD}}zip{{/if}}"
        "|{{#if ARTIFACT_TAR_CMD}}tar{{/if}}"
        "|{{#if ARTIFACT_SPECS_MODE_FILES}}gate{{/if}}"
    )
    variables = {
        "ARTIFACT_ZIP_CMD": "false",
        "ARTIFACT_TAR_CMD": "false",
        "ARTIFACT_SPECS_MODE_FILES": "false",
    }
    output = strip_inactive_conditional_blocks(text, variables)
    assert "zip" in output and "tar" in output
    assert "gate" not in output


def test_mode_flags_default_true_without_config():
    """AC-I7 (spec §3.3): absent flag is active and never default-off."""
    assert _conditional_active({}, "ARTIFACT_SPECS_MODE_FILES") is True
    assert _conditional_active({}, "ARTIFACT_SPECS_MODE_INLINE") is True
    assert not {
        name for name in _FALSE_DEFAULT_CONDITIONALS
        if name.endswith(GATE_SUFFIXES)
    }


def test_gate_flags_registered_and_ratchet_untouched():
    """Spec §3.4: all derived gate flags are registered, not ratcheted."""
    gate_names = {
        name for name in ph.derive_builder_vars(ROOT)
        if name.endswith(GATE_SUFFIXES)
    }
    assert gate_names
    assert gate_names <= ph._BUILTIN_VARS, (
        f"Unregistered gate flags: {sorted(gate_names - ph._BUILTIN_VARS)}"
    )
    assert not (gate_names & ph._UNREGISTERED_BUILDER_RATCHET)


def test_standalone_defaults_include_gate_flags():
    """Spec §3.4: standalone personas ship the derived flags as well."""
    from lib.standalone import _ARTIFACT_FALLBACKS

    assert _ARTIFACT_FALLBACKS["ARTIFACT_SPECS_MODE_FILES"] == "true"
    assert _ARTIFACT_FALLBACKS["ARTIFACT_SPECS_MODE_INLINE"] == "false"


def test_pal_variables_doc_lists_mode_flags():
    """AC-I8 (spec §3.5): the doc names both gate-flag suffixes."""
    doc = (ROOT / "docs/api/pal-variables.md").read_text(encoding="utf-8")
    for suffix in GATE_SUFFIXES:
        assert suffix in doc
