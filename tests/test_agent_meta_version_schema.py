"""Regression test for issue #850 — the ``agent-meta-version`` schema pattern
rejected SemVer pre-release/build versions (e.g. ``2.0.0-beta.1``), so the repo
failed its own ``config/project-config.schema.json`` and sync.py emitted a
non-fatal ``Config validation warnings`` entry.

Run: python -m pytest tests/test_agent_meta_version_schema.py -v
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

jsonschema = pytest.importorskip("jsonschema")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"
_PROJECT_YAML = _REPO_ROOT / ".meta-config" / "project.yaml"


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _config(version: str) -> dict:
    """Minimal config carrying just the field under test."""
    return {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "agent-meta-version": version,
    }


@pytest.mark.parametrize(
    "version",
    [
        "0.16.5",  # plain release stays valid (backward compatible)
        "2.0.0-beta.1",  # the version the repo failed on
        "1.2.0-beta.2",
        "2.0.0+build.5",  # build metadata only
        "2.0.0-rc.1+build.5",  # pre-release + build metadata
    ],
)
def test_valid_versions_pass_schema(version: str) -> None:
    jsonschema.validate(_config(version), _schema())


@pytest.mark.parametrize("version", ["1.2", "1.2.3.4", "v1.2.3"])
def test_invalid_versions_fail_schema(version: str) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(version), _schema())


def test_repo_project_yaml_version_satisfies_schema() -> None:
    """The shipped repo must not warn against its own schema (issue #850).

    Mirrors sync.py's config validation: only the ``agent-meta-version``
    error path is asserted, so unrelated fields cannot mask a regression.
    """
    config = yaml.safe_load(_PROJECT_YAML.read_text(encoding="utf-8"))
    validator = jsonschema.Draft7Validator(_schema())
    errors = [
        e for e in validator.iter_errors(config) if list(e.path) == ["agent-meta-version"]
    ]
    assert errors == [], [e.message for e in errors]
