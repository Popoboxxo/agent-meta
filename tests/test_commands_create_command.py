"""REQ-08 (AC-8.1-8.4): create_command never overwrites, suffix idempotent, dry-run, unmanaged."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.lib.cli_commands import _handle_create_command
from scripts.lib.active_set import compute_active_set
from scripts.lib.commands import (
    CLAUDE_COMMANDS_DIR, create_command, sync_commands_for_provider)
from scripts.lib.log import SyncLog
from scripts.lib.providers import load_providers_config
from tests.active_set_render import REPO_ROOT, default_config


def _cmd(project: Path, name: str) -> Path:
    return project / CLAUDE_COMMANDS_DIR / name


def _index_entries(project: Path) -> set[str]:
    path = _cmd(project, ".agent-meta-managed")
    if not path.is_file():
        return set()
    return {ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()}


def _sync(project: Path) -> SyncLog:
    config = default_config()
    log = SyncLog()
    active = compute_active_set(config, REPO_ROOT, project, warn_sink=[])
    sync_commands_for_provider(
        REPO_ROOT, project, config, log, False, "Claude",
        provider_config=load_providers_config(REPO_ROOT, config),
        variables={}, active_set=active)
    return log


def test_existing_file_is_never_overwritten(tmp_path):  # AC-8.1
    target = _cmd(tmp_path, "mine.md")
    target.parent.mkdir(parents=True)
    target.write_bytes(b"own content\r\n\xc3\xa4")
    log = SyncLog()
    create_command(tmp_path, "mine", log, dry_run=False)
    assert target.read_bytes() == b"own content\r\n\xc3\xa4"
    assert any("mine.md" in s for s in log.skipped)
    assert not log.actions


def test_cli_handler_never_overwrites_existing_file(tmp_path):  # AC-8.1 (CLI path)
    target = _cmd(tmp_path, "mine.md")
    target.parent.mkdir(parents=True)
    target.write_bytes(b"own content\r\n\xc3\xa4")
    log = SyncLog()
    ctx = SimpleNamespace(
        args=SimpleNamespace(create_command="mine", dry_run=False),
        log=log, project_root=tmp_path, mode=None)
    _handle_create_command(ctx)
    assert ctx.mode == "create-command:mine"
    assert target.read_bytes() == b"own content\r\n\xc3\xa4"
    assert any("mine.md" in s for s in log.skipped)
    assert not log.actions


@pytest.mark.parametrize("name", ["foo", "foo.md"])
def test_creates_file_and_suffix_is_idempotent(tmp_path, name):  # AC-8.2
    log = SyncLog()
    create_command(tmp_path, name, log, dry_run=False)
    files = sorted(p.name for p in _cmd(tmp_path, "").iterdir())
    assert files == ["foo.md"]
    assert any("CREATE" in a and "foo.md" in a for a in log.actions)
    assert "description: Foo" in _cmd(tmp_path, "foo.md").read_text(encoding="utf-8")


def test_dry_run_creates_nothing(tmp_path):  # AC-8.4
    log = SyncLog()
    create_command(tmp_path, "foo", log, dry_run=True)
    assert not _cmd(tmp_path, "foo.md").exists()
    assert not (tmp_path / CLAUDE_COMMANDS_DIR).exists()
    assert any("CREATE" in a for a in log.actions)


def test_created_command_survives_subsequent_sync(tmp_path):  # AC-8.3
    create_command(tmp_path, "my-own-cmd", SyncLog(), dry_run=False)
    target = _cmd(tmp_path, "my-own-cmd.md")
    before = target.read_bytes()
    _sync(tmp_path)
    _sync(tmp_path)
    assert target.read_bytes() == before
    assert "my-own-cmd.md" not in _index_entries(tmp_path)
    assert _index_entries(tmp_path)  # sync did manage other commands
