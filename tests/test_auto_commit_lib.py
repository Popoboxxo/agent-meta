"""scripts/lib/auto_commit.py: role-eligibility derivation and allowlist
shape (issue #694). Eligibility is capability-derived from each role's
OWN template frontmatter tools: list -- never a hand-maintained list."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.auto_commit import is_role_eligible, resolve_auto_commit_config  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_developer_is_eligible():
    # agents/1-generic/developer.md tools: includes Write and Edit.
    assert is_role_eligible("developer", _REPO_ROOT) is True


def test_git_is_not_eligible():
    # agents/1-generic/git.md tools: is Bash/Read/Glob/Grep/TodoWrite only --
    # no Edit/Write. It doesn't need this mechanism, it already has full
    # commit authority via its own dedicated sentinel.
    assert is_role_eligible("git", _REPO_ROOT) is False


def test_explorer_is_not_eligible():
    # Read-only role -- must never become commit-eligible even if listed
    # as an active role.
    assert is_role_eligible("explorer", _REPO_ROOT) is False


def test_resolve_config_mode_off_returns_empty_allowlist():
    result = resolve_auto_commit_config(
        config={"auto_commit": {"mode": "off"}},
        active_roles=["orchestrator", "developer", "git"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["mode"] == "off"
    assert result["eligible_roles"] == []


def test_resolve_config_auto_mode_lists_only_eligible_active_roles():
    result = resolve_auto_commit_config(
        config={"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}},
        active_roles=["orchestrator", "developer", "git", "tester"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["mode"] == "auto"
    assert "developer" in result["eligible_roles"]
    assert "tester" in result["eligible_roles"]
    assert "git" not in result["eligible_roles"]  # already has its own path
    assert result["triggers"] == ["task-boundary"]


def test_resolve_config_defaults_secret_scan_true():
    result = resolve_auto_commit_config(
        config={"auto_commit": {"mode": "auto", "triggers": ["per-edit"]}},
        active_roles=["developer"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["secret_scan"] is True


def test_resolve_config_missing_auto_commit_key_defaults_to_off():
    result = resolve_auto_commit_config(
        config={},
        active_roles=["orchestrator", "developer", "git"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["mode"] == "off"
    assert result["eligible_roles"] == []
