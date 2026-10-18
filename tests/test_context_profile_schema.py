"""Schema tests for the ``context-profile`` keys (SPEC-CONTEXT-PROFILES-2026-10-11).

Plan: docs/plans/2026-10-17-context-profiles-phase2-plan.md, Task 2a.2.
Covers IC-01:

- ``context-profile`` is a top-level string enum (``full``/``compact``) with a
  virtual default ``full`` (never persisted).
- ``provider-overrides.<Provider>.context-profile`` is a nested enum with
  ``additionalProperties: false`` (only ``context-profile`` per provider).
- An out-of-enum value is a validation error naming the allowed values.
- ``provider-overrides: null`` is treated like a missing block.
- The new top-level ``provider-overrides`` block does not collide with the
  existing nested ``context_file.provider-overrides`` block.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"

sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import load_config


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


@pytest.mark.parametrize("value", ["full", "compact"])
def test_context_profile_each_enum_value_accepted(value):
    jsonschema.validate(_config(**{"context-profile": value}), _schema())


def test_context_profile_out_of_enum_rejected_with_allowed_values():
    with pytest.raises(jsonschema.ValidationError) as exc:
        jsonschema.validate(_config(**{"context-profile": "ultra"}), _schema())
    message = exc.value.message
    assert "ultra" in message
    assert "full" in message and "compact" in message


def test_context_profile_absence_is_valid():
    jsonschema.validate(_config(), _schema())
    prop = _schema()["properties"]["context-profile"]
    assert prop["enum"] == ["full", "compact"]
    # No schema "default": a virtual default is never persisted by fill_defaults.
    assert "default" not in prop


@pytest.mark.parametrize("value", ["full", "compact"])
def test_provider_override_enum_value_accepted(value):
    jsonschema.validate(
        _config(**{"provider-overrides": {"Opencode": {"context-profile": value}}}),
        _schema(),
    )


def test_provider_override_out_of_enum_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **{
                    "provider-overrides": {
                        "Opencode": {"context-profile": "ultra"}
                    }
                }
            ),
            _schema(),
        )


def test_provider_override_unknown_subkey_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **{
                    "provider-overrides": {
                        "Opencode": {"context-profile": "compact", "x": 1}
                    }
                }
            ),
            _schema(),
        )


def test_new_top_level_block_does_not_collide_with_nested_provider_overrides():
    jsonschema.validate(
        _config(
            **{
                "provider-overrides": {"Gemini": {"context-profile": "compact"}},
                "context_file": {
                    "provider-overrides": {"Claude": {"topology": "unified"}}
                },
            }
        ),
        _schema(),
    )


def _load_body(tmp_path: Path, body: str) -> dict:
    path = tmp_path / "project.yaml"
    path.write_text(body, encoding="utf-8")
    return load_config(path)


def test_provider_overrides_null_is_treated_like_missing_block(tmp_path: Path):
    config = _load_body(
        tmp_path,
        "project:\n  name: t\n  prefix: t\n  short: t\n"
        "ai-providers:\n  - Claude\n"
        "provider-overrides: null\n",
    )
    assert config["provider-overrides"] == {}


def test_context_profile_enum_is_not_persisted_by_default(tmp_path: Path):
    """IC-01: a missing key stays absent — the safe-side ``full`` default is
    virtual (schema ``default`` + resolver fallback), never materialised."""
    import yaml

    from lib.config import fill_defaults
    from lib.log import SyncLog

    config = _load_body(
        tmp_path,
        "project:\n  name: t\n  prefix: t\n  short: t\n"
        "ai-providers:\n  - Claude\n",
    )
    assert "context-profile" not in config
    fill_defaults(tmp_path / "project.yaml", _REPO_ROOT, SyncLog(), dry_run=False)
    reloaded = yaml.safe_load((tmp_path / "project.yaml").read_text(encoding="utf-8"))
    assert "context-profile" not in reloaded


# --- IC-01 error path (2a review fix): context-profile.invalid --------------

_P10_FIXTURE = _REPO_ROOT / "tests" / "fixtures" / "active-set" / "p10"
_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"


def _cli_project(tmp_path: Path, extra: str = "") -> Path:
    """p10 fixture copy as a throwaway sync project with *extra* appended."""
    project = tmp_path / "p10"
    (project / ".meta-config").mkdir(parents=True)
    (project / ".meta-config" / "project.yaml").write_text(
        (_P10_FIXTURE / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
        + extra,
        encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    return project


def _run_cli(project: Path, mode: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC_PY),
         "--config", str(project / ".meta-config" / "project.yaml"), mode],
        cwd=project, capture_output=True, text=True, timeout=300)


def test_cli_validate_reports_invalid_profile_without_traceback(tmp_path: Path):
    project = _cli_project(tmp_path, "context-profile: ultra\n")
    proc = _run_cli(project, "--validate")
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "context-profile.invalid" in out
    assert "full, compact" in out
    assert "Traceback" not in out


def test_cli_sync_aborts_cleanly_on_invalid_profile(tmp_path: Path):
    project = _cli_project(tmp_path, "context-profile: ultra\n")
    proc = _run_cli(project, "--init")
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "context-profile.invalid" in out
    assert "full, compact" in out
    assert "Traceback" not in out


def test_cli_validate_flags_invalid_override_for_inactive_provider(tmp_path: Path):
    # The sync path only resolves active providers, so an out-of-enum
    # override for an inactive provider must surface via the config audit.
    project = _cli_project(
        tmp_path,
        "provider-overrides:\n  Opencode:\n    context-profile: ultra\n")
    proc = _run_cli(project, "--validate")
    out = proc.stdout + proc.stderr
    assert proc.returncode != 0
    assert "context-profile.invalid" in out
    assert "provider-overrides.Opencode" in out
    assert "Traceback" not in out


def test_audit_config_flags_invalid_profile_values(tmp_path: Path):
    from lib.config_audit import audit_config

    project = _cli_project(
        tmp_path,
        "context-profile: ultra\n"
        "provider-overrides:\n  Opencode:\n    context-profile: turbo\n")
    report = audit_config(_REPO_ROOT, project / ".meta-config" / "project.yaml")
    issues = report.by_category("context-profile.invalid")
    assert len(issues) == 2
    assert {i.severity for i in issues} == {"error"}
    messages = "\n".join(i.message for i in issues)
    assert "'ultra'" in messages and "'turbo'" in messages
    assert "provider-overrides.Opencode.context-profile" in messages
    assert "full, compact" in messages
