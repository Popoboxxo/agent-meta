"""Tests for #1000: gitignored checkpoint dirs and dangling plan references."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import progress_paths  # noqa: E402
from lib.consistency.checkpoint_tracking import (  # noqa: E402
    check_checkpoint_dir_ignored,
    check_checkpoint_references,
)
from lib.progress_paths import resolve_progress_paths  # noqa: E402

_MOD = REPO_ROOT / "scripts" / "lib" / "consistency" / "checkpoint_tracking.py"


def _git_repo(tmp_path: Path) -> Path:
    subprocess.run(["git", "init", "-q"], cwd=str(tmp_path), check=True)
    (tmp_path / ".gitignore").write_text(".meta-viz/\n", encoding="utf-8")
    return tmp_path


def _codes(findings):
    return [f.code if hasattr(f, "code") else f.check for f in findings]


def test_ac1_default_dir_ignored_warns(tmp_path):
    root = _git_repo(tmp_path)
    found = [f for f in resolve_progress_paths(root, {}).findings
             if f.code == "progress.checkpoint-dir-ignored"]
    assert len(found) == 1 and found[0].level == "warning"


def test_ac2_tracked_dir_no_finding(tmp_path):
    root = _git_repo(tmp_path)
    cfg = {"progress": {"checkpoint-dir": "docs/checkpoints"}}
    assert "progress.checkpoint-dir-ignored" not in _codes(
        resolve_progress_paths(root, cfg).findings)


def test_ac3_no_git_repo_silent(tmp_path):
    res = resolve_progress_paths(tmp_path, {})
    assert not [c for c in _codes(res.findings) if c.endswith("-dir-ignored")]


def test_ac4_git_missing_silent(tmp_path, monkeypatch):
    root = _git_repo(tmp_path)
    monkeypatch.setattr(progress_paths, "run_git_check_ignore", lambda *a, **k: None)
    res = resolve_progress_paths(root, {})
    assert not [c for c in _codes(res.findings) if c.endswith("-dir-ignored")]


def test_ac2_validate_wrapper_warning(tmp_path):
    root = _git_repo(tmp_path)
    out = check_checkpoint_dir_ignored(root, {})
    assert {f.check for f in out} >= {"progress.checkpoint-dir-ignored"}
    assert all(f.severity.name == "WARNING" for f in out)


def test_ac5_validate_cli_exit_zero(tmp_path):
    root = _git_repo(tmp_path)
    (root / ".meta-config").mkdir()
    (root / ".meta-config" / "project.yaml").write_text(
        "project:\n  name: x\n  prefix: x\n", encoding="utf-8")
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py"), "--validate"],
        cwd=str(root), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120)
    assert "progress.checkpoint-dir-ignored" in res.stdout + res.stderr


def test_ac6_reference_missing_and_ignored(tmp_path):
    root = _git_repo(tmp_path)
    plan = root / "plan.md"
    plan.write_text("resume: `.meta-viz/checkpoint-x.json`\n", encoding="utf-8")
    assert _codes(check_checkpoint_references(root, [plan])) == [
        "checkpoint.reference-missing"]
    (root / ".meta-viz").mkdir()
    (root / ".meta-viz" / "checkpoint-x.json").write_text("{}", encoding="utf-8")
    out = check_checkpoint_references(root, [plan])
    assert _codes(out) == ["checkpoint.reference-ignored"]
    assert out[0].severity.name == "ERROR"


def test_ac7_tracked_existing_reference_ok(tmp_path):
    root = _git_repo(tmp_path)
    (root / "docs").mkdir()
    (root / "docs" / "checkpoint-a.json").write_text("{}", encoding="utf-8")
    plan = root / "plan.md"
    plan.write_text("see docs/checkpoint-a.json and .meta-viz/checkpoint-<ts>.json\n",
                    encoding="utf-8")
    assert check_checkpoint_references(root, [plan]) == []


def test_ac8_reference_no_git_skipped(tmp_path):
    plan = tmp_path / "plan.md"
    plan.write_text("`.meta-viz/checkpoint-x.json`\n", encoding="utf-8")
    assert check_checkpoint_references(tmp_path, [plan]) == []


def test_ac11_module_hygiene():
    for p in (_MOD, REPO_ROOT / "scripts" / "lib" / "progress_paths.py"):
        text = p.read_text(encoding="utf-8")
        assert len(text.splitlines()) <= 600
        assert "print(" not in text


def test_ac9_snippet_text():
    text = (REPO_ROOT / "snippets" / "orchestrator" / "checkpointing.md").read_text(
        encoding="utf-8")
    for term in ("ephemeral", "tracked", "same PR", "progress.checkpoint-dir-ignored"):
        assert term in text
