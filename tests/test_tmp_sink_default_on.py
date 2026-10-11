"""AC-92 (IC-15 Nr. 26): tmp-sink gitignore entry is ON without a block.

Run: python -m pytest tests/test_tmp_sink_default_on.py -q
"""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.gitignore import _tmp_sink_gitignore_entry, compute_base_gitignore_entries

_CLAUDE = {"Claude": {"has_dedicated_context_file": True}}


def _entries(cfg):
    return compute_base_gitignore_entries(["Claude"], _CLAUDE, {}, cfg)


def test_no_block_yields_default_entry():
    assert ".tmp/" in _entries(None)


def test_non_mapping_block_yields_default_entry():
    assert _tmp_sink_gitignore_entry("garbage") == ".tmp/"  # type: ignore[arg-type]
    assert _tmp_sink_gitignore_entry(None) == ".tmp/"


def test_custom_path_entry():
    cfg = {"enabled": True, "tmp-sink": {"enabled": True, "path": "scratch/out"}}
    assert "scratch/out/" in _entries(cfg)
    assert ".tmp/" not in _entries(cfg)


def test_gitignore_false_yields_no_entry():
    cfg = {"enabled": True, "tmp-sink": {"gitignore": False}}
    assert _tmp_sink_gitignore_entry(cfg) is None
    assert ".tmp/" not in _entries(cfg)


def test_sink_disabled_yields_no_entry():
    cfg = {"enabled": True, "tmp-sink": {"enabled": False}}
    assert _tmp_sink_gitignore_entry(cfg) is None
    assert ".tmp/" not in _entries(cfg)


def _scratch_project(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers:\n- Claude\n"
        "dod-preset: rapid-prototyping\n"
        "variables:\n  PROJECT_NAME: scratch\n  PROJECT_PREFIX: sc\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def test_dry_run_check_writes_nothing_but_reports_entry(tmp_path):
    project = _scratch_project(tmp_path)
    before = sorted(p.relative_to(project) for p in project.rglob("*") if ".git" not in p.parts)
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"),
         "--config", str(project / ".meta-config" / "project.yaml"), "--dry-run", "--check"],
        cwd=project, capture_output=True, text=True, timeout=300,
    )
    out = result.stdout + result.stderr
    assert "Traceback" not in out
    assert not (project / ".gitignore").exists()
    after = sorted(p.relative_to(project) for p in project.rglob("*") if ".git" not in p.parts)
    assert after == before
    gitignore_lines = [ln for ln in out.splitlines() if ln.startswith("[UPDATE") and ".gitignore" in ln]
    assert gitignore_lines, "dry-run did not report the managed .gitignore block"
    assert ".tmp/" in gitignore_lines[0]
