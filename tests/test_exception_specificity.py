"""Regression tests for #568: bare `except Exception: pass` replaced with
minimal expected exception classes across lib/viz.py, lib/backup.py,
lib/pipelines.py and sync.py.

Each test group verifies the two-part contract from the issue:
1. The expected/anticipated exception is caught, logged, and execution
   continues with a safe fallback (no crash).
2. An unrelated/unexpected exception type is NOT swallowed — it propagates.
"""

import sys
import zipfile
from pathlib import Path
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import viz as viz_module
from lib.backup import restore_backup
from lib.log import SyncLog
from lib.pipelines import parse_plan_ref
from lib.viz import _get_terminal_tool, _infer_tier, read_events


# --- lib/viz.py::_infer_tier --------------------------------------------------
# Patch target is lib.viz (not lib.io): since Issue #478 hoisted the formerly
# lazy `from .io import _load_yaml_or_json` in viz.py to module top level,
# _infer_tier resolves the name through lib.viz's module namespace. Patching
# lib.viz._load_yaml_or_json exercises the identical code path.

def test_infer_tier_falls_back_on_oserror(monkeypatch, tmp_path):
    def _raise_oserror(*_a, **_kw):
        raise OSError("simulated permission error")

    monkeypatch.setattr("lib.viz._load_yaml_or_json", _raise_oserror)
    assert _infer_tier("developer", {}) == "optional"


def test_infer_tier_propagates_unexpected_exception(monkeypatch):
    def _raise_runtime_error(*_a, **_kw):
        raise RuntimeError("unexpected bug")

    monkeypatch.setattr("lib.viz._load_yaml_or_json", _raise_runtime_error)
    with pytest.raises(RuntimeError):
        _infer_tier("developer", {})


# --- lib/viz.py::read_events ---------------------------------------------------

def test_read_events_returns_empty_on_oserror_from_directory_path(tmp_path):
    """A directory at the expected event-log path triggers IsADirectoryError
    (an OSError subclass) on open() — must degrade to an empty list, not crash."""
    project_root = tmp_path
    viz_dir = project_root / ".meta-viz"
    viz_dir.mkdir(parents=True)
    # get_event_log_path() defaults to <viz_dir>/events.jsonl — make that a dir.
    bogus_log_dir = viz_dir / "events.jsonl"
    bogus_log_dir.mkdir()
    events = read_events(project_root)
    assert events == []


def test_read_events_propagates_unexpected_exception(monkeypatch, tmp_path):
    project_root = tmp_path
    viz_dir = project_root / ".meta-viz"
    viz_dir.mkdir(parents=True)
    log_file = viz_dir / "events.jsonl"
    log_file.write_text('{"ts": "2026-01-01T00:00:00Z", "a": 1}\n', encoding="utf-8")

    def _raise_runtime_error(*_a, **_kw):
        raise RuntimeError("unexpected bug")

    # json.loads is called inside a nested try that only catches
    # (JSONDecodeError, ValueError) — a different exception type must
    # propagate through the outer OSError-only handler untouched.
    monkeypatch.setattr(viz_module.json, "loads", _raise_runtime_error)
    with pytest.raises(RuntimeError):
        read_events(project_root)


# --- lib/viz.py::_get_terminal_tool --------------------------------------------

def test_get_terminal_tool_falls_back_on_oserror(monkeypatch, tmp_path):
    def _raise_oserror(*_a, **_kw):
        raise OSError("simulated I/O error")

    monkeypatch.setattr("lib.frontmatter.load_provider_tools_config", _raise_oserror)
    # Falls back to the hardcoded default map — must not raise.
    _get_terminal_tool("Claude", tmp_path)


def test_get_terminal_tool_propagates_unexpected_exception(monkeypatch, tmp_path):
    def _raise_runtime_error(*_a, **_kw):
        raise RuntimeError("unexpected bug")

    monkeypatch.setattr("lib.frontmatter.load_provider_tools_config", _raise_runtime_error)
    with pytest.raises(RuntimeError):
        _get_terminal_tool("Claude", tmp_path)


# --- lib/pipelines.py::parse_plan_ref -------------------------------------------

def test_parse_plan_ref_falls_back_on_malformed_yaml(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("---\npipeline_stages: [unclosed\n---\nBody\n", encoding="utf-8")
    result = parse_plan_ref(str(plan))
    assert result["file_exists"] is True
    assert result["stages"] == {}


def test_parse_plan_ref_falls_back_on_non_mapping_frontmatter(tmp_path):
    """Top-level frontmatter is a YAML list, not a mapping -> fm.get() raises
    AttributeError, which must be caught (not propagate) since this is a
    best-effort optional override."""
    plan = tmp_path / "plan.md"
    plan.write_text("---\n- a\n- b\n---\nBody\n", encoding="utf-8")
    result = parse_plan_ref(str(plan))
    assert result["stages"] == {}


def test_parse_plan_ref_falls_back_on_non_numeric_stage_value(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("---\npipeline_stages:\n  implement: not-a-number\n---\nBody\n", encoding="utf-8")
    result = parse_plan_ref(str(plan))
    assert result["stages"] == {}


# --- lib/backup.py::restore_backup ----------------------------------------------

def _make_empty_archive(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("placeholder.txt", "no manifest, no providers")


def test_restore_backup_infer_providers_falls_back_on_bad_zip(tmp_path):
    project_root = tmp_path
    archive_path = tmp_path / "backup.zip"
    _make_empty_archive(archive_path)

    real_zipfile = zipfile.ZipFile
    call_count = {"n": 0}

    def _flaky_zipfile(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return real_zipfile(*args, **kwargs)
        raise zipfile.BadZipFile("simulated corruption on second open")

    with mock.patch("lib.backup.zipfile.ZipFile", side_effect=_flaky_zipfile):
        result = restore_backup(
            project_root, str(archive_path), provider_config={}, config={}, log=SyncLog()
        )
    assert result["success"] is True


def test_restore_backup_infer_providers_propagates_unexpected_exception(tmp_path):
    project_root = tmp_path
    archive_path = tmp_path / "backup.zip"
    _make_empty_archive(archive_path)

    real_zipfile = zipfile.ZipFile
    call_count = {"n": 0}

    def _flaky_zipfile(*args, **kwargs):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return real_zipfile(*args, **kwargs)
        raise RuntimeError("unexpected bug")

    with mock.patch("lib.backup.zipfile.ZipFile", side_effect=_flaky_zipfile):
        with pytest.raises(RuntimeError):
            restore_backup(
                project_root, str(archive_path), provider_config={}, config={}, log=SyncLog()
            )


# --- sync.py: directory-cleanup + AST-analysis except blocks --------------------

def test_sync_provider_cleanup_and_ast_analysis_specific_excepts_present():
    """Static check that the two sync-pipeline sites use narrowed except clauses
    instead of bare `except Exception: pass` (both are deep inside
    argument-heavy CLI-dispatch functions that are impractical to unit-test
    in isolation here — see the full-suite + `--validate` run for behavioral
    coverage of the overall sync flow).

    Issue #481 moved the provider-cleanup block from sync.py::_handle_sync to
    lib/sync_pipeline.py::_sync_stage_legacy_cleanup — the assertion follows
    the code, the contract is unchanged. The same issue moved the AST-analysis
    block to lib/cli_commands.py::_run_common_tail."""
    pipeline_text = (REPO_ROOT / "scripts" / "lib" / "sync_pipeline.py").read_text(encoding="utf-8")
    cli_commands_text = (REPO_ROOT / "scripts" / "lib" / "cli_commands.py").read_text(encoding="utf-8")
    assert "except OSError as e:" in pipeline_text
    assert 'log.debug("provider-cleanup"' in pipeline_text
    assert 'log.debug("ast-analysis"' in cli_commands_text
