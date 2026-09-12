"""scripts/lib/subagent_permissions.py + variables resolver (Feature A).

Precedence, YAML-1.1 normalization, flag shape and the defensive ``.get()``
chain (M1). The resolver is non-exiting (M3): invalid values resolve to "off".
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.subagent_permissions import (  # noqa: E402
    invalid_subagent_permission_entries,
    render_subagent_permission_block,
    resolve_effective_subagent_permission_mode,
    resolve_subagent_permission_provider_vars,
)
from lib.variables import (  # noqa: E402
    _resolve_subagent_permissions_mode,
    _subagent_permission_flags,
    normalize_subagent_permission_mode,
)


@pytest.mark.parametrize("value,expected", [
    ("strict", "strict"),
    ("warn", "warn"),
    ("off", "off"),
    ("  WARN  ", "warn"),
    ("Strict", "strict"),
    ("bogus", None),
    ("", None),
    (None, None),
    (5, None),
    ([], None),
])
def test_normalize_string_values(value, expected):
    assert normalize_subagent_permission_mode(value) == expected


@pytest.mark.parametrize("value", [False, True])
def test_normalize_bools_to_none(value):
    # YAML 1.1: unquoted off/on parse as bool -> never opt-in from a boolean.
    assert normalize_subagent_permission_mode(value) is None


def test_resolve_precedence_provider_override_beats_project():
    cfg = {"mode": "warn"}
    assert _resolve_subagent_permissions_mode(cfg) == "warn"
    assert _resolve_subagent_permissions_mode(cfg, {"mode": "strict"}) == "strict"


def test_resolve_provider_entry_without_mode_inherits_project():
    cfg = {"mode": "warn"}
    assert _resolve_subagent_permissions_mode(cfg, {}) == "warn"
    assert _resolve_subagent_permissions_mode(cfg, {"other": 1}) == "warn"


def test_resolve_unset_is_off():
    assert _resolve_subagent_permissions_mode({}) == "off"
    assert _resolve_subagent_permissions_mode({}, None) == "off"


def test_resolve_invalid_is_off_and_never_exits():
    # M3: no SystemExit — invalid resolves to the safe-side default.
    assert _resolve_subagent_permissions_mode({"mode": "sometimes"}) == "off"
    assert _resolve_subagent_permissions_mode({"mode": True}) == "off"


def test_resolve_defensive_get_chain_no_exception():
    # M1: shape oddities must never raise.
    for cfg in ({}, {"subagent_permissions": {}}, {"subagent_permissions": None}):
        assert resolve_effective_subagent_permission_mode(cfg) == "off"
    config = {
        "subagent_permissions": {
            "provider-overrides": {"Gemini": {}, "Opencode": {"mode": "strict"}},
        },
    }
    assert resolve_effective_subagent_permission_mode(config, "Gemini") == "off"
    assert resolve_effective_subagent_permission_mode(config, "Opencode") == "strict"
    assert resolve_effective_subagent_permission_mode(config, "Claude") == "off"


def test_resolve_two_providers_independent():
    config = {
        "subagent_permissions": {
            "mode": "warn",
            "provider-overrides": {"Opencode": {"mode": "strict"}},
        },
    }
    assert resolve_effective_subagent_permission_mode(config, "Opencode") == "strict"
    assert resolve_effective_subagent_permission_mode(config, "Claude") == "warn"


def test_flags_exactly_one_true_and_enabled():
    for mode in ("strict", "warn", "off"):
        flags = _subagent_permission_flags(mode)
        bools = [
            flags["SUBAGENT_PERMISSIONS_STRICT"],
            flags["SUBAGENT_PERMISSIONS_WARN"],
            flags["SUBAGENT_PERMISSIONS_OFF"],
        ]
        assert bools.count("true") == 1
        assert flags["SUBAGENT_PERMISSIONS_MODE"] == mode
        assert flags["SUBAGENT_PERMISSIONS_ENABLED"] == (
            "false" if mode == "off" else "true"
        )


def test_provider_vars_include_flags_and_block():
    config = {"subagent_permissions": {"provider-overrides": {"Opencode": {"mode": "strict"}}}}
    bundle = resolve_subagent_permission_provider_vars(config, "Opencode")
    assert bundle["SUBAGENT_PERMISSIONS_MODE"] == "strict"
    assert bundle["SUBAGENT_PERMISSIONS_STRICT"] == "true"
    assert bundle["SUBAGENT_PERMISSIONS_BLOCK"] == render_subagent_permission_block("strict")

    other = resolve_subagent_permission_provider_vars(config, "Claude")
    assert other["SUBAGENT_PERMISSIONS_MODE"] == "off"
    assert other["SUBAGENT_PERMISSIONS_BLOCK"] == ""


def test_invalid_entries_reports_global_and_provider_paths():
    config = {
        "subagent_permissions": {
            "mode": "sometimes",
            "provider-overrides": {
                "Opencode": {"mode": "nope"},
                "Gemini": {"mode": "warn"},
                "Claude": {},
            },
        },
    }
    entries = invalid_subagent_permission_entries(config)
    assert "subagent_permissions.mode" in entries
    assert "subagent_permissions.provider-overrides.Opencode.mode" in entries
    assert "subagent_permissions.provider-overrides.Gemini.mode" not in entries


def test_invalid_entries_ignores_bools_and_missing():
    assert invalid_subagent_permission_entries({}) == []
    assert invalid_subagent_permission_entries({"subagent_permissions": {"mode": False}}) == []
