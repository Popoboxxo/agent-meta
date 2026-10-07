"""Tests for the gitignore.keep / re-include mechanism (issue #746).

With `gitignore.ignore-provider-dirs: true`, whole provider roots (`.claude/`)
are ignored — which also hides project-owned, non-generated files underneath.
`gitignore.keep` re-includes specific paths: the managed block emits a
CONTENT-exclude (`/.claude/*`) + re-include negations (`!/.claude/3-project/`)
instead of the whole-dir exclude, because git cannot re-include a file whose
parent directory is excluded.

CRITICAL: the ordering bug (sorted() puts `!` before `/`, neutralizing the
negation under git's last-match-wins) is INVISIBLE to a pure string/set test.
The end-to-end test here therefore builds a REAL git repo and runs
`git check-ignore` against the written .gitignore — the only reliable guard.

Run: python3 -m pytest tests/test_gitignore_keep.py -q
"""

import subprocess
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.context import ensure_gitignore_entries  # noqa: E402
from lib.gitignore import (  # noqa: E402
    _group_keep_paths_by_root,
    _keep_reinclude_entries,
    compute_base_gitignore_entries,
    detect_invisible_keep_paths,
)
from lib.log import SyncLog  # noqa: E402

_PROVIDERS_CONFIG = _REPO_ROOT / "config" / "ai-providers.yaml"


def _load_provider_config() -> dict:
    with _PROVIDERS_CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)["providers"]


def _toggle_cfg(**extra) -> dict:
    cfg = {"ignore-provider-dirs": True}
    cfg.update(extra)
    return cfg


# ---------------------------------------------------------------------------
# unit: re-include chain + grouping
# ---------------------------------------------------------------------------


def test_keep_reinclude_chain_directory():
    assert _keep_reinclude_entries(".claude/", ".claude/3-project/") == [
        "!/.claude/3-project/"
    ]


def test_keep_reinclude_chain_nested_single_file():
    assert _keep_reinclude_entries(".gemini/", ".gemini/rules/test-scope.md") == [
        "!/.gemini/rules/",
        "/.gemini/rules/*",
        "!/.gemini/rules/test-scope.md",
    ]


def test_keep_reinclude_chain_root_itself_is_noop():
    # A keep path equal to the root has no sub-path to re-include.
    assert _keep_reinclude_entries(".claude/", ".claude/") == []


def test_group_keep_paths_by_root():
    roots = [".claude/", ".gemini/"]
    grouped = _group_keep_paths_by_root(
        [".claude/3-project/", ".gemini/rules/test-scope.md", "outside/x.md"], roots
    )
    assert grouped == {
        ".claude/": [".claude/3-project/"],
        ".gemini/": [".gemini/rules/test-scope.md"],
    }


# ---------------------------------------------------------------------------
# unit: compute_base_gitignore_entries emits content-exclude + negations
# ---------------------------------------------------------------------------


def test_keep_replaces_whole_dir_with_content_exclude():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        ["Claude"], provider_config, _toggle_cfg(keep=[".claude/3-project/"])
    )
    assert "/.claude/*" in entries
    assert ".claude/" not in entries  # whole-dir exclude replaced
    assert "!/.claude/3-project/" in entries


def test_keep_only_affects_roots_with_keep_paths():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        ["Claude", "Gemini"], provider_config, _toggle_cfg(keep=[".claude/3-project/"])
    )
    # Gemini root has no keep -> stays a whole-dir exclude.
    assert ".gemini/" in entries
    assert "/.gemini/*" not in entries


def test_keep_without_toggle_is_noop():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        ["Claude"], provider_config, {"keep": [".claude/3-project/"]}
    )
    assert "!/.claude/3-project/" not in entries
    assert "/.claude/*" not in entries


# ---------------------------------------------------------------------------
# CRITICAL end-to-end: REAL git check-ignore against the written .gitignore
# ---------------------------------------------------------------------------


def _write_managed_block(tmp_path: Path, keep: list[str]) -> None:
    """Run the real compute + exact-write pipeline into tmp_path/.gitignore."""
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        ["Claude", "Gemini"], provider_config, _toggle_cfg(keep=keep)
    )
    ensure_gitignore_entries(
        tmp_path, SyncLog(), dry_run=False, exact_entries=entries
    )


def _check_ignored(repo: Path, rel: str) -> bool:
    """True if git considers `rel` ignored (check-ignore exit 0)."""
    res = subprocess.run(
        ["git", "check-ignore", "-q", rel],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    return res.returncode == 0


def test_end_to_end_real_git_check_ignore(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _write_managed_block(tmp_path, [".claude/3-project/", ".gemini/rules/test-scope.md"])

    for sub in (".claude/3-project", ".claude/agents", ".gemini/rules", ".gemini/agents"):
        (tmp_path / sub).mkdir(parents=True, exist_ok=True)
    for rel in (
        ".claude/3-project/NEW.md",
        ".claude/settings.local.json",
        ".claude/agents/gen.md",
        ".gemini/rules/test-scope.md",
        ".gemini/rules/generated.md",
        ".gemini/agents/x.md",
    ):
        (tmp_path / rel).write_text("x", encoding="utf-8")

    # Kept paths must NOT be ignored (the ordering-bug regression lives here).
    assert not _check_ignored(tmp_path, ".claude/3-project/NEW.md")
    assert not _check_ignored(tmp_path, ".gemini/rules/test-scope.md")
    # Everything else under the provider roots must stay ignored.
    assert _check_ignored(tmp_path, ".claude/settings.local.json")
    assert _check_ignored(tmp_path, ".claude/agents/gen.md")
    assert _check_ignored(tmp_path, ".gemini/rules/generated.md")
    assert _check_ignored(tmp_path, ".gemini/agents/x.md")


def test_written_block_orders_excludes_before_negations(tmp_path):
    """Pin the exclude-before-negate ordering in the written file directly."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _write_managed_block(tmp_path, [".claude/3-project/"])
    lines = [
        ln.strip()
        for ln in (tmp_path / ".gitignore").read_text(encoding="utf-8").splitlines()
        if ln.strip() and not ln.startswith("#")
    ]
    exclude_idx = lines.index("/.claude/*")
    negate_idx = lines.index("!/.claude/3-project/")
    assert exclude_idx < negate_idx, (
        f"exclude must precede negation, got {lines!r}"
    )
    # No negation may appear before its matching content-exclude.
    first_negation = next(i for i, ln in enumerate(lines) if ln.startswith("!"))
    last_nonneg = max(i for i, ln in enumerate(lines) if not ln.startswith("!"))
    assert first_negation > last_nonneg


# ---------------------------------------------------------------------------
# --validate safety net: detect_invisible_keep_paths
# ---------------------------------------------------------------------------


def test_detect_invisible_keep_paths_warns_on_legacy_whole_dir_rule(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    # Legacy whole-dir rule shadows the keep path -> negation ineffective.
    (tmp_path / ".gitignore").write_text(".claude/\n", encoding="utf-8")
    warnings = detect_invisible_keep_paths(
        tmp_path, {"keep": [".claude/3-project/"]}
    )
    assert warnings
    assert ".claude/3-project/" in warnings[0]


def test_detect_invisible_keep_paths_silent_when_honored(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    _write_managed_block(tmp_path, [".claude/3-project/"])
    warnings = detect_invisible_keep_paths(
        tmp_path, {"keep": [".claude/3-project/"]}
    )
    assert warnings == []


def test_detect_invisible_keep_paths_noop_without_keep(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    assert detect_invisible_keep_paths(tmp_path, {}) == []
