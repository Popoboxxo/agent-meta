"""SR-A-24: validate_test_repo judges the current run, not a stale sync.log."""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.cli_commands import validate_test_repo  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_CONFIG = {"ai-providers": ["Claude"], "variables": {"PROJECT_NAME": "t", "PROJECT_PREFIX": "t"}}


def _run(tmp_path, monkeypatch, fake_sync):
    import lib.agent_sync as agent_sync

    monkeypatch.setattr(agent_sync, "sync_agents_for_provider", fake_sync)
    log = SyncLog()
    ok = validate_test_repo(tmp_path, _REPO_ROOT, dict(_CONFIG), log, dry_run=True)
    return ok, log


def test_error_in_current_run_fails_validation(tmp_path, monkeypatch):
    def failing(*args, **kwargs):
        args[4].error("agents/x.md", "boom")  # (root, repo, config, vars, log, ...)

    ok, _ = _run(tmp_path, monkeypatch, failing)
    assert ok is False


def test_stale_error_in_old_sync_log_is_ignored(tmp_path, monkeypatch):
    (tmp_path / "sync.log").write_text("[ERROR]  agents/old.md  fixed long ago\n", encoding="utf-8")
    ok, _ = _run(tmp_path, monkeypatch, lambda *a, **k: None)
    assert ok is True


def test_errors_from_before_the_run_are_not_counted(tmp_path, monkeypatch):
    import lib.agent_sync as agent_sync

    monkeypatch.setattr(agent_sync, "sync_agents_for_provider", lambda *a, **k: None)
    log = SyncLog()
    log.error("earlier-stage", "unrelated")
    assert validate_test_repo(tmp_path, _REPO_ROOT, dict(_CONFIG), log, dry_run=True) is True
