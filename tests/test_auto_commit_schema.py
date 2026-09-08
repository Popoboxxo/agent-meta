"""auto_commit config schema (issue #694): mode enum, trigger enum, and the
two invalid-combination rules -- triggers set without mode: auto, and
mode: custom / triggers containing "custom" without a custom_script."""

import json
import sys
from pathlib import Path

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _base_config(auto_commit: dict) -> dict:
    return {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
        "roles": ["orchestrator", "developer", "git"],
        "auto_commit": auto_commit,
    }


def test_mode_off_is_valid_minimal():
    jsonschema.validate(_base_config({"mode": "off"}), _schema())


def test_mode_auto_with_triggers_is_valid():
    jsonschema.validate(
        _base_config({"mode": "auto", "triggers": ["task-boundary", "context-pressure"]}),
        _schema(),
    )


def test_invalid_mode_value_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_config({"mode": "sometimes"}), _schema())


def test_invalid_trigger_value_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"mode": "auto", "triggers": ["whenever-i-feel-like-it"]}),
            _schema(),
        )


def test_duplicate_triggers_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"mode": "auto", "triggers": ["per-edit", "per-edit"]}),
            _schema(),
        )


def test_file_count_threshold_must_be_positive_int():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"mode": "auto", "triggers": ["file-count-threshold"], "file_count_threshold": 0}),
            _schema(),
        )
