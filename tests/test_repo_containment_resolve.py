"""Resolver tests for scripts/lib/repo_containment.py (spec §2.3).

Covers the three-tier precedence ``provider-override > project > framework
default``, the defensive ``.get()``/isinstance chain (the resolver never exits
and never raises), the YAML-1.1 bool trap and the safe-side ON fallback for a
present-but-non-boolean ``enabled`` (F4).

Also asserts the base-variable wiring added to
``scripts/lib/config.py::_build_orch_variables``: the base ``build_variables``
dict carries ``REPO_CONTAINMENT_*`` and the provider-aware render path
(``rules.py::_merged_rule_vars``, which both ``context.py`` and ``rules.py``
delegate to) honors a provider override.

Run: python -m pytest tests/test_repo_containment_resolve.py -v
"""

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import build_variables
from lib.repo_containment import (
    DEFAULT_TMP_SINK_CLEANUP,
    DEFAULT_TMP_SINK_PATH,
    SOURCE_DEFAULT,
    SOURCE_PROJECT,
    SOURCE_PROVIDER_OVERRIDE,
    SOURCE_SAFE_FALLBACK,
    resolve_effective_repo_containment,
)
from lib.rules import _merged_rule_vars
from lib.variables import repo_containment_variables


# --- Precedence --------------------------------------------------------


def test_default_when_block_absent():
    resolved = resolve_effective_repo_containment({})
    assert resolved.enabled is True
    assert resolved.source == SOURCE_DEFAULT
    assert resolved.findings == []


def test_project_value_overrides_default():
    resolved = resolve_effective_repo_containment(
        {"repo_containment": {"enabled": False}}
    )
    assert resolved.enabled is False
    assert resolved.source == SOURCE_PROJECT


def test_provider_override_beats_project():
    config = {
        "repo_containment": {
            "enabled": True,
            "provider-overrides": {"Continue": {"enabled": False}},
        }
    }
    resolved = resolve_effective_repo_containment(config, "Continue")
    assert resolved.enabled is False
    assert resolved.source == SOURCE_PROVIDER_OVERRIDE
    assert resolved.provider == "Continue"


def test_provider_override_can_widen_containment():
    config = {
        "repo_containment": {
            "enabled": False,
            "provider-overrides": {"Claude": {"enabled": True}},
        }
    }
    assert resolve_effective_repo_containment(config, "Claude").enabled is True


def test_provider_without_override_inherits_project():
    config = {
        "repo_containment": {
            "enabled": False,
            "provider-overrides": {"Claude": {"enabled": True}},
        }
    }
    resolved = resolve_effective_repo_containment(config, "Opencode")
    assert resolved.enabled is False
    assert resolved.source == SOURCE_PROJECT


def test_no_provider_argument_uses_project_value():
    config = {
        "repo_containment": {
            "enabled": False,
            "provider-overrides": {"Claude": {"enabled": True}},
        }
    }
    assert resolve_effective_repo_containment(config).enabled is False


# --- YAML bool trap + safe-side ON -------------------------------------


def test_yaml_off_parses_to_bool_false_not_a_string():
    parsed = yaml.safe_load("enabled: off")
    assert parsed == {"enabled": False}
    resolved = resolve_effective_repo_containment(
        {"repo_containment": parsed}
    )
    assert resolved.enabled is False
    assert resolved.source == SOURCE_PROJECT


def test_quoted_false_string_is_safe_side_on():
    resolved = resolve_effective_repo_containment(
        {"repo_containment": {"enabled": "false"}}
    )
    assert resolved.enabled is True
    assert resolved.source == SOURCE_SAFE_FALLBACK
    assert resolved.has_findings


def test_numeric_enabled_is_safe_side_on():
    resolved = resolve_effective_repo_containment(
        {"repo_containment": {"enabled": 1}}
    )
    assert resolved.enabled is True
    assert resolved.source == SOURCE_SAFE_FALLBACK


def test_null_enabled_is_safe_side_on():
    resolved = resolve_effective_repo_containment(
        {"repo_containment": {"enabled": None}}
    )
    assert resolved.enabled is True
    assert resolved.source == SOURCE_SAFE_FALLBACK


# --- Defensive .get() / isinstance chain -------------------------------


def test_none_config_does_not_raise():
    resolved = resolve_effective_repo_containment(None)
    assert resolved.enabled is True


def test_non_mapping_block_uses_defaults_with_finding():
    resolved = resolve_effective_repo_containment(
        {"repo_containment": "enabled"}
    )
    assert resolved.enabled is True
    assert resolved.source == SOURCE_DEFAULT
    assert resolved.has_findings


def test_non_mapping_provider_overrides_ignored():
    config = {"repo_containment": {"enabled": False, "provider-overrides": "nope"}}
    resolved = resolve_effective_repo_containment(config, "Claude")
    assert resolved.enabled is False
    assert resolved.source == SOURCE_PROJECT
    assert resolved.has_findings


def test_non_mapping_override_entry_falls_back_to_project():
    config = {
        "repo_containment": {
            "enabled": False,
            "provider-overrides": {"Claude": "off"},
        }
    }
    resolved = resolve_effective_repo_containment(config, "Claude")
    assert resolved.enabled is False
    assert resolved.source == SOURCE_PROJECT
    assert resolved.has_findings


def test_override_entry_without_enabled_falls_back_to_project():
    config = {
        "repo_containment": {
            "enabled": False,
            "provider-overrides": {"Claude": {}},
        }
    }
    resolved = resolve_effective_repo_containment(config, "Claude")
    assert resolved.enabled is False
    assert resolved.source == SOURCE_PROJECT


def test_non_boolean_provider_override_is_safe_side_on():
    config = {
        "repo_containment": {
            "enabled": False,
            "provider-overrides": {"Claude": {"enabled": "yes"}},
        }
    }
    resolved = resolve_effective_repo_containment(config, "Claude")
    assert resolved.enabled is True
    assert resolved.source == SOURCE_SAFE_FALLBACK


# --- tmp-sink settings (independent of the master switch) --------------


def test_tmp_sink_defaults_apply_even_when_master_switch_off():
    resolved = resolve_effective_repo_containment(
        {"repo_containment": {"enabled": False}}
    )
    assert resolved.tmp_sink_enabled is True
    assert resolved.tmp_sink_path == DEFAULT_TMP_SINK_PATH
    assert resolved.cleanup == DEFAULT_TMP_SINK_CLEANUP


def test_invalid_sink_path_falls_back_to_default():
    resolved = resolve_effective_repo_containment(
        {"repo_containment": {"tmp-sink": {"path": "../escape"}}}
    )
    assert resolved.tmp_sink_path == DEFAULT_TMP_SINK_PATH
    assert resolved.has_findings


def test_invalid_cleanup_falls_back_to_manual():
    resolved = resolve_effective_repo_containment(
        {"repo_containment": {"tmp-sink": {"cleanup": "sometimes"}}}
    )
    assert resolved.cleanup == DEFAULT_TMP_SINK_CLEANUP
    assert resolved.has_findings


# --- Base-variable wiring (item 4) -------------------------------------


def _minimal_config() -> dict:
    return {
        "project": {"prefix": "t", "short": "T", "name": "T"},
        "roles": ["developer"],
    }


def test_build_variables_exposes_base_repo_containment_enabled():
    variables, unmapped = build_variables(
        _minimal_config(), _REPO_ROOT, _REPO_ROOT
    )
    assert variables["REPO_CONTAINMENT_ENABLED"] == "true"
    assert variables["REPO_CONTAINMENT_TMP_PATH"] == DEFAULT_TMP_SINK_PATH
    assert not [u for u in unmapped if "REPO_CONTAINMENT" in u]


def test_provider_override_is_honored_on_the_render_path():
    config = _minimal_config()
    config["ai-providers"] = ["Continue"]
    config["repo_containment"] = {
        "enabled": True,
        "provider-overrides": {"Continue": {"enabled": False}},
    }

    # Base (provider-independent) dict: still "true".
    assert repo_containment_variables(config)["REPO_CONTAINMENT_ENABLED"] == "true"

    # Render path shared by context.py/rules.py: provider override wins.
    provider_vars = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, config, "Continue", {"has_rules": False}, None
    )
    assert provider_vars["REPO_CONTAINMENT_ENABLED"] == "false"
