"""Tests for lib.gitignore.detect_shadowed_provider_roots (#713): a
pre-existing broad .gitignore rule (e.g. `.claude/`) that predates -- and is
never covered by -- agent-meta's own managed block silently untracks every
file the syncer just wrote, with no warning today."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.gitignore import detect_shadowed_provider_roots

_PROVIDER_CONFIG = {"Claude": {"agents_dir": ".claude/agents"}}


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
