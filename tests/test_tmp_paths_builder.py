"""Builder variables for the tmp-sink (Task 2: AC-14, AC-15, AC-16, AC-25, AC-35).

Covers the contract of ``_build_orch_variables`` (``TMP_SINK_ABS_PATH``,
``PYTEST_BASETEMP``, ``TMP_SINK_ENV_PIN_BLOCK`` and the ``{{PYTEST_BASETEMP}}``
token) plus the sync-time ``system-temp-exception`` matrix.

Run: python -m pytest tests/test_tmp_paths_builder.py -q
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import (  # noqa: E402
    _validate_repo_containment,
    build_variables,
)
from lib.io import SyncError  # noqa: E402

_TOKEN = "{{PYTEST_BASETEMP}}"


def _config(repo_containment: dict | None = None) -> dict:
    """Minimal config whose suite commands carry the pytest token (AC-13/AC-14)."""
    config = {
        "project": {"name": "scratch", "prefix": "sc", "short": "sc"},
        "ai-providers": ["Claude"],
        "roles": ["orchestrator"],
        "variables": {
            "TEST_COMMANDS": f"python3 -m pytest tests/ --basetemp={_TOKEN}",
            "CODE_QUALITY_RULES": f"- basetemp: --basetemp={_TOKEN}",
        },
    }
    if repo_containment is not None:
        config["repo_containment"] = repo_containment
    return config


def _build(project_root: Path, repo_containment: dict | None = None) -> dict:
    (project_root / ".meta-config").mkdir(parents=True, exist_ok=True)
    variables, _warnings = build_variables(
        _config(repo_containment), _REPO_ROOT, project_root
    )
    return variables


def _config_path(tmp_path: Path) -> Path:
    path = tmp_path / ".meta-config" / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# --- AC-16: relative vs. absolute form ---------------------------------


def test_builder_sets_absolute_and_relative_sink(tmp_path):
    """AC-16: ``TMP_SINK_PATH`` stays relative, ``TMP_SINK_ABS_PATH`` is realpath."""
    variables = _build(tmp_path)

    assert variables["TMP_SINK_PATH"] == ".tmp"
    assert not os.path.isabs(variables["TMP_SINK_PATH"])

    absolute = variables["TMP_SINK_ABS_PATH"]
    assert os.path.isabs(absolute)
    assert absolute == os.path.realpath(tmp_path / ".tmp")
    # No symlink tail: the value is the resolved directory itself (ADR-02).
    assert not os.path.islink(absolute)
    assert os.path.realpath(absolute) == absolute


def test_builder_resolves_pytest_token_in_both_values(tmp_path):
    """AC-13: exactly one shell-quoted ``--basetemp`` argument, no token left."""
    variables = _build(tmp_path)

    for key in ("TEST_COMMANDS", "CODE_QUALITY_RULES"):
        rendered = variables[key]
        assert _TOKEN not in rendered
        assert '--basetemp="' in rendered
        basetemps = [
            arg for arg in shlex.split(rendered) if arg.startswith("--basetemp=")
        ]
        assert len(basetemps) == 1
        raw = basetemps[0].split("=", 1)[1]
        assert os.path.isabs(raw)
        assert '"' not in raw


def test_pytest_basetemp_variable_is_absolute(tmp_path):
    """IC-05: ``PYTEST_BASETEMP`` is the finished, absolute argv value."""
    variables = _build(tmp_path)

    assert os.path.isabs(variables["PYTEST_BASETEMP"])
    assert '"' not in variables["PYTEST_BASETEMP"]


# --- AC-14: unresolved token is a hard failure -------------------------


def test_unresolved_pytest_token_fails_sync(tmp_path, monkeypatch):
    """AC-14: a skipped replacement never ships a raw token.

    Simulates the documented regression (token replacement removed/skipped) by
    neutralizing the substitution helper: the builder must still notice the
    leftover token and abort instead of rendering it into an agent file.
    """
    monkeypatch.setattr(
        "lib.config._replace_pytest_basetemp_token", lambda value, basetemp: value
    )

    with pytest.raises(SyncError, match=r"tmp-sink\.pytest-token"):
        _build(tmp_path)


def test_replace_pytest_basetemp_token_is_shell_quoted():
    """The substitution helper quotes the value for shell parsing (AC-34)."""
    from lib.config import _replace_pytest_basetemp_token

    rendered = _replace_pytest_basetemp_token(
        f"--basetemp={_TOKEN}", "/tmp/with space"
    )
    assert rendered == '--basetemp="/tmp/with space"'


# --- AC-35: the env pin block uses absolute values only -----------------


def test_env_pin_block_is_absolute(tmp_path):
    """AC-35: all three exports carry the same absolute value."""
    variables = _build(tmp_path)
    block = variables["TMP_SINK_ENV_PIN_BLOCK"]

    absolute = variables["TMP_SINK_ABS_PATH"]
    assert os.path.isabs(absolute)
    for key in ("TMPDIR", "TEMP", "TMP"):
        assert f"export {key}={shlex.quote(absolute)}" in block
    # The relative form is never assigned (IC-19/ADR-12).
    assert f"TMPDIR={variables['TMP_SINK_PATH']}" not in block
    assert f"TMPDIR='{variables['TMP_SINK_PATH']}'" not in block


# --- AC-25: a disabled sink keeps TMP_SINK_PATH only --------------------


def test_disabled_sink_omits_absolute_variables(tmp_path):
    """AC-25: ``TMP_SINK_PATH`` stays set; absolute/pin variables are absent."""
    variables = _build(tmp_path, {"tmp-sink": {"enabled": False}})

    assert variables["TMP_SINK_PATH"] == ".tmp"
    assert "TMP_SINK_ABS_PATH" not in variables
    assert "TMP_SINK_ENV_PIN_BLOCK" not in variables


def _scratch_project(tmp_path: Path) -> Path:
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.3"\n'
        "ai-providers:\n- Claude\n"
        "dod-preset: rapid-prototyping\n"
        "repo_containment:\n"
        "  tmp-sink:\n"
        "    enabled: false\n"
        "variables:\n"
        "  PROJECT_NAME: scratch\n"
        "  PROJECT_PREFIX: sc\n"
        "  TEST_COMMANDS: python3 -m pytest tests/ "
        "--basetemp={{PYTEST_BASETEMP}}\n"
        "  CODE_QUALITY_RULES: 'basetemp: --basetemp={{PYTEST_BASETEMP}}'\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def test_disabled_sink_sync_dry_run_is_successful(tmp_path):
    """AC-25: ``sync.py --dry-run`` exits 0, logs ``log.skip``, creates no sink."""
    project = _scratch_project(tmp_path)

    result = subprocess.run(
        [
            sys.executable,
            str(_REPO_ROOT / "scripts" / "sync.py"),
            "--config",
            str(project / ".meta-config" / "project.yaml"),
            "--dry-run",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=300,
    )

    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "tmp-sink disabled" in output
    assert not (project / ".tmp").exists()


# --- AC-15: system-temp-exception matrix -------------------------------


def _validate(config: dict, tmp_path: Path) -> None:
    _validate_repo_containment(config, _config_path(tmp_path))


def _exception(**block) -> dict:
    return {
        "repo_containment": {
            "tmp-sink": {"system-temp-exception": block},
        }
    }


def test_system_temp_exception_accepts_valid_block(tmp_path):
    """AC-15 precondition: the documented exception block is valid."""
    _validate(_exception(enabled=True, reason="unit-test reason"), tmp_path)


@pytest.mark.parametrize(
    ("config", "expected", "temp_inside_project"),
    [
        (
            {"repo_containment": {"tmp-sink": {"system-temp-exception": "on"}}},
            "expected a mapping, got str.",
            False,
        ),
        (
            _exception(enabled=False, **{"pytest-basetemp": True}),
            "'pytest-basetemp: true' requires 'enabled: true'.",
            False,
        ),
        (
            _exception(enabled=True),
            "invalid 'repo_containment.tmp-sink.system-temp-exception.reason': "
            "required when the exception is enabled",
            False,
        ),
        (
            _exception(enabled=True, reason="unit-test reason"),
            "tmp-sink.system-temp-exception",
            True,
        ),
    ],
)
def test_system_temp_exception_matrix(
    tmp_path, capsys, monkeypatch, config, expected, temp_inside_project
):
    """AC-15: one test parameter per documented matrix case (four cases)."""
    if temp_inside_project:
        monkeypatch.setattr(tempfile, "gettempdir", lambda: str(tmp_path))

    with pytest.raises(SystemExit) as exc:
        _validate(config, tmp_path)

    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert expected in err
    if temp_inside_project:
        assert "inside the project root" in err
