"""Tests for lib.gitignore.detect_shadowed_provider_roots (#713): a
pre-existing broad .gitignore rule (e.g. `.claude/`) that predates -- and is
never covered by -- agent-meta's own managed block silently untracks every
file the syncer just wrote, with no warning today."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.context import ensure_gitignore_entries
from lib.gitignore import (
    GITIGNORE_BLOCK_BEGIN,
    GITIGNORE_BLOCK_END,
    compute_base_gitignore_entries,
    detect_shadowed_provider_roots,
)
from lib.log import SyncLog

_PROVIDER_CONFIG = {"Claude": {"agents_dir": ".claude/agents"}}

# Same provider shape the exact-mode writer needs (dedicated context file).
_EXACT_PROVIDER_CONFIG = {
    "Claude": {
        "has_dedicated_context_file": True,
        "agents_dir": ".claude/agents",
        "gitignore_entries": [".claude/settings.local.json"],
    }
}


def _init_repo(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)


def test_warns_when_preexisting_broad_rule_shadows_managed_block(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    warnings = detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=False,
    )

    assert len(warnings) == 1
    assert "Claude" in warnings[0]
    assert ".claude/agents/" in warnings[0]
    assert ".gitignore:1:.claude/" in warnings[0]
    assert "gitignore: {ignore-provider-dirs: true}" in warnings[0]  # AC-1085c-1


def test_no_warning_when_nothing_is_ignored(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    warnings = detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=False,
    )

    assert warnings == []


def test_no_warning_when_toggle_intentionally_ignores_provider_root(tmp_path):
    # ignore-provider-dirs: true means the managed block ITSELF added the
    # broad rule -- a match is then expected, not a shadowing bug.
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    warnings = detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=True,
    )

    assert warnings == []


def test_no_warning_without_a_git_repo(tmp_path):
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")

    warnings = detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=False,
    )

    assert warnings == []


def test_no_warning_when_rule_inside_managed_block(tmp_path):
    # #1072: a matching rule that lives INSIDE the agent-meta managed block
    # was written by the syncer itself -- that is not silent shadowing.
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(
        f"{GITIGNORE_BLOCK_BEGIN}\n.claude/\n{GITIGNORE_BLOCK_END}\n", encoding="utf-8")

    assert detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=False) == []


def test_warning_when_rule_outside_block_even_if_block_exists(tmp_path):
    # #1072: presence of a managed block must not suppress warnings for
    # unrelated rules that still shadow the provider output.
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(
        f".claude/\n{GITIGNORE_BLOCK_BEGIN}\nsync.log\n{GITIGNORE_BLOCK_END}\n", encoding="utf-8")

    warnings = detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=False)

    assert len(warnings) == 1 and ".gitignore:1:.claude/" in warnings[0]


def test_warning_when_managed_block_begin_is_unbalanced(tmp_path):
    # Advisory: an unterminated BEGIN must not mark the rest of the file as
    # "inside" — otherwise one truncated marker suppresses every later warning.
    _init_repo(tmp_path)
    (tmp_path / ".gitignore").write_text(
        f"{GITIGNORE_BLOCK_BEGIN}\nsync.log\n.claude/\n", encoding="utf-8")

    warnings = detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _PROVIDER_CONFIG, ignore_provider_dirs=False)

    assert len(warnings) == 1
    assert ".gitignore:3:.claude/" in warnings[0]


def test_end_to_end_custom_entry_in_written_block_is_not_shadowing(tmp_path):
    # Advisory: real pipeline (compute -> exact write -> detect) must not warn
    # when the user's own `custom_entries` put `.claude/` into the managed
    # block, even with the provider-dir toggle off.
    _init_repo(tmp_path)
    entries = compute_base_gitignore_entries(
        ["Claude"], _EXACT_PROVIDER_CONFIG, {"custom_entries": [".claude/"]})
    assert ".claude/" in entries
    ensure_gitignore_entries(
        tmp_path, SyncLog(), dry_run=False, exact_entries=entries)

    assert detect_shadowed_provider_roots(
        tmp_path, ["Claude"], _EXACT_PROVIDER_CONFIG, ignore_provider_dirs=False) == []
