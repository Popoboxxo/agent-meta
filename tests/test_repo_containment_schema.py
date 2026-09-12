"""Schema tests for the ``repo_containment`` block (spec §2.1).

The block is purely additive: a config without it stays valid and the block
itself carries the framework defaults (enabled true, tmp-sink enabled + path
``.tmp`` + gitignore true + cleanup ``manual``). The only closed value set is
``tmp-sink.cleanup`` (``manual`` | ``on-sync``).

Run: python -m pytest tests/test_repo_containment_schema.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _base_config(repo_containment: dict | None = None) -> dict:
    config = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
        "roles": ["orchestrator", "developer", "git"],
    }
    if repo_containment is not None:
        config["repo_containment"] = repo_containment
    return config


def _rc_schema() -> dict:
    return _schema()["properties"]["repo_containment"]


# --- Additive / structural ---------------------------------------------


def test_block_is_additive_config_without_it_is_valid():
    jsonschema.validate(_base_config(), _schema())


def test_minimal_block_is_valid():
    jsonschema.validate(
        _base_config({"enabled": True}), _schema()
    )


def test_full_block_is_valid():
    jsonschema.validate(
        _base_config(
            {
                "enabled": True,
                "provider-overrides": {"Claude": {"enabled": False}},
                "tmp-sink": {
                    "enabled": True,
                    "path": ".tmp",
                    "gitignore": True,
                    "cleanup": "manual",
                },
            }
        ),
        _schema(),
    )


def test_block_additional_properties_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"enabled": True, "bogus": 1}), _schema()
        )


# --- Type traps --------------------------------------------------------


def test_non_boolean_enabled_rejected():
    for bogus in ("yes", "true", 1, None):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(_base_config({"enabled": bogus}), _schema())


def test_non_boolean_tmp_sink_enabled_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"tmp-sink": {"enabled": "on"}}), _schema()
        )


def test_tmp_sink_additional_properties_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"tmp-sink": {"path": ".tmp", "bogus": True}}),
            _schema(),
        )


def test_provider_override_values_must_be_objects():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"provider-overrides": {"Claude": False}}),
            _schema(),
        )


def test_provider_override_entry_additional_properties_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config(
                {"provider-overrides": {"Claude": {"enabled": True, "mode": "x"}}}
            ),
            _schema(),
        )


# --- cleanup enum ------------------------------------------------------


@pytest.mark.parametrize("cleanup", ["manual", "on-sync"])
def test_cleanup_enum_accepts_both_modes(cleanup):
    jsonschema.validate(
        _base_config({"tmp-sink": {"cleanup": cleanup}}), _schema()
    )


@pytest.mark.parametrize("cleanup", ["sometimes", "", "auto", "Manual"])
def test_cleanup_enum_rejects_everything_else(cleanup):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"tmp-sink": {"cleanup": cleanup}}), _schema()
        )


# --- Defaults (must match the framework resolver) ----------------------


def test_schema_defaults_match_spec():
    rc = _rc_schema()
    assert rc["properties"]["enabled"]["default"] is True
    sink = rc["properties"]["tmp-sink"]["properties"]
    assert sink["enabled"]["default"] is True
    assert sink["path"]["default"] == ".tmp"
    assert sink["gitignore"]["default"] is True
    assert sink["cleanup"]["default"] == "manual"
    assert set(sink["cleanup"]["enum"]) == {"manual", "on-sync"}


def test_block_is_closed_at_top_level():
    assert _rc_schema().get("additionalProperties") is False
