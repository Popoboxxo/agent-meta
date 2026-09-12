"""Schema tests for ``subagent_permissions`` and ``git`` (Feature A/B)."""

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


def _config(**extra) -> dict:
    base = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
    }
    base.update(extra)
    return base


@pytest.mark.parametrize("mode", ["off", "warn", "strict"])
def test_subagent_mode_valid(mode):
    jsonschema.validate(_config(subagent_permissions={"mode": mode}), _schema())


def test_subagent_invalid_mode_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(subagent_permissions={"mode": "sometimes"}), _schema()
        )


def test_subagent_provider_override_valid():
    jsonschema.validate(
        _config(subagent_permissions={"provider-overrides": {"Claude": {"mode": "warn"}}}),
        _schema(),
    )


def test_subagent_provider_override_empty_entry_valid():
    jsonschema.validate(
        _config(subagent_permissions={"provider-overrides": {"Claude": {}}}),
        _schema(),
    )


def test_subagent_provider_override_invalid_sub_mode_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(subagent_permissions={"provider-overrides": {"Claude": {"mode": "sometimes"}}}),
            _schema(),
        )


def test_subagent_block_additional_property_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(subagent_permissions={"mode": "off", "extra": 1}), _schema()
        )


def test_subagent_provider_entry_additional_property_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(subagent_permissions={"provider-overrides": {"Claude": {"mode": "off", "x": 1}}}),
            _schema(),
        )


def test_git_section_valid():
    jsonschema.validate(
        _config(git={
            "platform": "GitHub",
            "remote-url": "https://github.com/owner/repo",
            "main-branch": "main",
            "branch-prefixes": {"feat": "feat/", "fix": "fix/", "chore": "chore/"},
        }),
        _schema(),
    )


def test_git_invalid_platform_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(git={"platform": "Bitbucket"}), _schema())


def test_git_unknown_property_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(git={"remote_url": "x"}), _schema())


def test_git_branch_prefix_unknown_key_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(git={"branch-prefixes": {"feature": "feature/"}}), _schema()
        )
