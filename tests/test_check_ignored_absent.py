"""Regression tests for #752: `sync.py --check` must not report a WRITE for a
generated provider file that is merely *absent because its target root is
gitignored* (the normal state on a fresh checkout / CI clone).

`write_checked` in dry-run mode is the central choke point: a missing file is
only treated as legitimately absent when git positively confirms its directory
(rc 0) is ignored. Existing-but-different files and missing files outside any
ignore rule must still report "would write" so genuine committed drift is
never masked.

Run: python -m pytest tests/test_check_ignored_absent.py -v
"""

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import io as io_mod
from lib.io import write_checked
from lib.log import SyncLog
from lib import agent_sync, hooks as hooks_mod, mcp as mcp_mod
from lib.agent_sync import AGENTS_DIR
from lib.context import (
    _init_provider_settings_json,
    _sync_continue_context,
    init_claude_personal,
    init_opencode_personal,
    init_settings_local_json,
)


@pytest.fixture(autouse=True)
def _clear_gitignore_cache():
    """Isolate the module-level per-directory probe cache between tests."""
    io_mod._gitignored_dir_cache.clear()
    yield
    io_mod._gitignored_dir_cache.clear()


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)


def test_absent_file_under_gitignored_root_reports_no_write(tmp_path):
    """Case (a): missing file under an ignored root is not drift."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    log = SyncLog()
    result = write_checked(
        tmp_path / ".claude" / "agents" / "orchestrator.md",
        "generated content",
        log,
        "1-generic/orchestrator.md",
        dry_run=True,
    )

    assert result is False
    assert log.actions == []


def test_existing_differing_file_under_gitignored_root_still_reports_write(tmp_path):
    """Case (b): local stale content is still detected even under an ignored root."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")
    target = tmp_path / ".claude" / "agents" / "orchestrator.md"
    target.parent.mkdir(parents=True)
    target.write_text("stale content", encoding="utf-8")

    log = SyncLog()
    result = write_checked(
        target, "new generated content", log, "1-generic/orchestrator.md", dry_run=True,
    )

    assert result is True


def test_missing_file_outside_gitignore_still_reports_write(tmp_path):
    """Case (c): a missing non-ignored file is genuine drift."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    log = SyncLog()
    result = write_checked(
        tmp_path / "generated" / "committed.md",
        "generated content",
        log,
        "generated/committed.md",
        dry_run=True,
    )

    assert result is True


def test_missing_file_without_git_repo_fails_open(tmp_path, monkeypatch):
    """Case (d): unknown ignore status keeps the old behaviour — simulated via
    an unavailable `git`, so the test does not assume the tmp dir is outside a repo."""
    monkeypatch.setattr(io_mod, "run_git_check_ignore", lambda *a, **k: None)

    log = SyncLog()
    result = write_checked(
        tmp_path / ".claude" / "agents" / "orchestrator.md",
        "generated content",
        log,
        "1-generic/orchestrator.md",
        dry_run=True,
    )

    assert result is True


def test_missing_file_git_error_rc128_fails_open(tmp_path, monkeypatch):
    """Case (d'): a git error (>1, e.g. not a repo) must not trigger the skip."""
    monkeypatch.setattr(
        io_mod,
        "run_git_check_ignore",
        lambda *a, **k: subprocess.CompletedProcess([], 128, "", "fatal: not a git repository"),
    )

    log = SyncLog()
    result = write_checked(
        tmp_path / ".claude" / "agents" / "orchestrator.md",
        "generated content",
        log,
        "1-generic/orchestrator.md",
        dry_run=True,
    )

    assert result is True


def test_probe_is_cached_per_directory(tmp_path, monkeypatch):
    """Many absent files in one ignored dir must not spawn one git call each."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    calls: list[str] = []
    real = io_mod.run_git_check_ignore

    def _counting(target, cwd, *flags):
        calls.append(target)
        return real(target, cwd, *flags)

    monkeypatch.setattr(io_mod, "run_git_check_ignore", _counting)

    log = SyncLog()
    results = [
        write_checked(
            tmp_path / ".claude" / "agents" / f"role-{i}.md",
            "generated content",
            log,
            f"role-{i}",
            dry_run=True,
        )
        for i in range(5)
    ]

    assert results == [False] * 5
    assert log.actions == []
    assert calls == [str(tmp_path / ".claude" / "agents")]


# --- Direct writers bypassing write_checked (#752, follow-up) ---------------

def test_settings_init_direct_writer_skips_absent_gitignored_in_dry_run(tmp_path):
    """context.py::_init_provider_settings_json must not action an absent
    gitignored settings file in `--check`/dry-run mode."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    log = SyncLog()
    _init_provider_settings_json(
        tmp_path,
        {"settings_file": ".claude/settings.json", "settings_template": None},
        tmp_path,
        {},
        log,
        dry_run=True,
    )

    assert log.actions == []
    assert any("absent (target root gitignored)" in s for s in log.skipped)


def test_settings_init_direct_writer_still_writes_on_real_run(tmp_path):
    """A real `sync.py` run must still create the gitignored settings file."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    log = SyncLog()
    _init_provider_settings_json(
        tmp_path,
        {"settings_file": ".claude/settings.json", "settings_template": None},
        tmp_path,
        {},
        log,
        dry_run=False,
    )

    assert (tmp_path / ".claude" / "settings.json").exists()
    assert len(log.actions) == 1


def test_settings_init_direct_writer_non_gitignored_still_actions(tmp_path):
    """Guard must not mask a missing file whose root is not ignored."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    log = SyncLog()
    _init_provider_settings_json(
        tmp_path,
        {"settings_file": "generated/settings.json", "settings_template": None},
        tmp_path,
        {},
        log,
        dry_run=True,
    )

    assert len(log.actions) == 1
    assert (tmp_path / "generated" / "settings.json").exists() is False


def test_settings_local_direct_writer_skips_absent_gitignored_in_dry_run(tmp_path):
    """context.py::init_settings_local_json must not action absent gitignored
    local settings skeletons in dry-run mode."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n.opencode/\n.gemini/\n", encoding="utf-8")

    log = SyncLog()
    init_settings_local_json(
        tmp_path,
        tmp_path,
        log,
        dry_run=True,
        providers=["Claude", "Opencode", "Gemini"],
        provider_config={
            "Claude": {"settings_local_file": ".claude/settings.local.json"},
            "Opencode": {"settings_local_file": ".opencode/settings.local.json"},
            "Gemini": {"settings_local_file": ".gemini/settings.local.json"},
        },
        variables={},
    )

    assert log.actions == []
    assert len([s for s in log.skipped if "absent (target root gitignored)" in s]) == 3


def _agent_file_args(tmp_path):
    """Build the `_write_agent_file` call args for an absent gitignored target."""
    am_root = tmp_path / "amroot"
    source = am_root / AGENTS_DIR / "1-generic" / "orchestrator.md"
    source.parent.mkdir(parents=True)
    source.write_text("template", encoding="utf-8")
    return {
        "target_path": tmp_path / ".claude" / "agents" / "orchestrator.md",
        "content": "generated content",
        "source_path": source,
        "agent_meta_root": am_root,
        "project_root": tmp_path,
        "config": {},
        "dry_run": True,
    }


def test_write_agent_file_skips_absent_gitignored_in_dry_run(tmp_path):
    """agent_sync._write_agent_file must log a skip (no WRITE) for an absent
    gitignored provider agent file in dry-run mode."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    log = SyncLog()
    agent_sync._write_agent_file(**(_agent_file_args(tmp_path)), log=log)

    assert log.actions == []
    assert any("absent (target root gitignored)" in s for s in log.skipped)


def test_hooks_settings_skips_absent_gitignored_in_dry_run(tmp_path):
    """hooks._update_settings_hooks must not action an absent gitignored settings.json."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    log = SyncLog()
    hooks_mod._update_settings_hooks(
        tmp_path,
        set(),
        {"dod-push-check"},
        [{"name": "dod-push-check", "event": "PreToolUse", "matcher": "", "command": "bash x.sh"}],
        log,
        dry_run=True,
    )

    assert log.actions == []
    assert any("absent (target root gitignored)" in s for s in log.skipped)


def test_hooks_antigravity_skips_absent_gitignored_in_dry_run(tmp_path):
    """hooks._update_antigravity_hooks_json must not action an absent gitignored config."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".gemini/\n", encoding="utf-8")

    log = SyncLog()
    hooks_mod._update_antigravity_hooks_json(
        tmp_path,
        set(),
        {"dod-push-check"},
        [{"name": "dod-push-check", "event": "PreToolUse", "file": "dod-push-check.sh"}],
        log,
        dry_run=True,
        provider_config={"hooks_config_file": ".gemini/hooks.json", "hooks_dir": ".gemini/hooks"},
    )

    assert log.actions == []
    assert any("absent (target root gitignored)" in s for s in log.skipped)


def test_mcp_secrets_template_skips_absent_gitignored_in_dry_run(tmp_path, monkeypatch):
    """mcp.sync_secrets_template must not action the absent gitignored secrets file."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".meta-config/secrets.local.yaml\n", encoding="utf-8")
    monkeypatch.setattr(
        mcp_mod, "_required_secrets_by_server", lambda *a, **k: {"srv": ["API_KEY"]},
    )

    log = SyncLog()
    mcp_mod.sync_secrets_template(tmp_path, tmp_path, {}, log, dry_run=True)

    assert log.actions == []
    assert any("absent (target root gitignored)" in s for s in log.skipped)


def test_mcp_secrets_template_still_writes_on_real_run(tmp_path, monkeypatch):
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".meta-config/secrets.local.yaml\n", encoding="utf-8")
    monkeypatch.setattr(
        mcp_mod, "_required_secrets_by_server", lambda *a, **k: {"srv": ["API_KEY"]},
    )

    log = SyncLog()
    mcp_mod.sync_secrets_template(tmp_path, tmp_path, {}, log, dry_run=False)

    assert (tmp_path / ".meta-config" / "secrets.local.yaml").exists()
    assert len(log.actions) == 1


def test_personal_files_skip_absent_gitignored_in_dry_run(tmp_path):
    """context.init_claude_personal/init_opencode_personal must not action the
    absent gitignored personal files in dry-run mode, but write on a real run."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("CLAUDE.personal.md\nAGENTS.personal.md\n", encoding="utf-8")
    am_root = tmp_path / "amroot"
    templates = am_root / "templates" / "configs"
    templates.mkdir(parents=True)
    (templates / "CLAUDE.personal-template.md").write_text("personal\n", encoding="utf-8")
    (templates / "AGENTS.personal-template.md").write_text("personal\n", encoding="utf-8")

    log = SyncLog()
    init_claude_personal(am_root, tmp_path, log, dry_run=True)
    init_opencode_personal(am_root, tmp_path, log, dry_run=True)
    assert log.actions == []

    init_claude_personal(am_root, tmp_path, log, dry_run=False)
    init_opencode_personal(am_root, tmp_path, log, dry_run=False)
    assert (tmp_path / "CLAUDE.personal.md").exists()
    assert (tmp_path / "AGENTS.personal.md").exists()


_CONTINUE_PC = {
    "Continue": {
        "context_file": ".continue/rules/project-context.md",
        "context_template": "templates/configs/CONTINUE.project-template.md",
        "settings_file": ".continue/config.yaml",
        "settings_template": "templates/configs/CONTINUE.config-template.yaml",
    }
}


def test_continue_context_dry_run_skips_absent_gitignored(tmp_path):
    """Both Continue direct writers must log skips (no actions) in dry-run when
    `.continue/` is gitignored and the files are absent."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".continue/\n", encoding="utf-8")

    log = SyncLog()
    _sync_continue_context(
        tmp_path, tmp_path, {}, {"PROJECT_NAME": "p", "PROJECT_CONTEXT": "ctx"},
        log, dry_run=True, provider="Continue", provider_config=_CONTINUE_PC,
    )

    assert log.actions == []
    skipped = "\n".join(log.skipped)
    assert ".continue/rules/project-context.md" in skipped
    assert ".continue/config.yaml" in skipped
    assert skipped.count("absent (target root gitignored)") == 2


def test_continue_context_real_run_creates_files(tmp_path):
    """Real runs must still create both Continue files under the ignored root."""
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".continue/\n", encoding="utf-8")

    log = SyncLog()
    _sync_continue_context(
        tmp_path, tmp_path, {}, {"PROJECT_NAME": "p", "PROJECT_CONTEXT": "ctx"},
        log, dry_run=False, provider="Continue", provider_config=_CONTINUE_PC,
    )

    assert (tmp_path / ".continue" / "rules" / "project-context.md").exists()
    assert (tmp_path / ".continue" / "config.yaml").exists()
    assert len(log.actions) == 2


