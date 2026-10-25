"""AC-92 (IC-15 Nr. 26): tmp-sink gitignore entry is ON without a block.

Run: python -m pytest tests/test_tmp_sink_default_on.py -q
"""

import ast
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.gitignore import _tmp_sink_gitignore_entry, compute_base_gitignore_entries
from lib.tmp_paths import resolve_tmp_paths

_CLAUDE = {"Claude": {"has_dedicated_context_file": True}}
_LIB = _REPO_ROOT / "scripts" / "lib"


def _entries(cfg):
    return compute_base_gitignore_entries(["Claude"], _CLAUDE, {}, cfg)


def _paths(tmp_path, cfg):
    return resolve_tmp_paths(tmp_path, {"repo_containment": cfg})


def test_no_block_yields_default_entry():
    assert ".tmp/" in _entries(None)


def test_non_mapping_block_yields_default_entry():
    assert ".tmp/" in _entries("garbage")  # type: ignore[arg-type]
    assert ".tmp/" in _entries(None)


def test_custom_path_entry():
    cfg = {"enabled": True, "tmp-sink": {"enabled": True, "path": "scratch/out"}}
    assert "scratch/out/" in _entries(cfg)
    assert ".tmp/" not in _entries(cfg)


def test_tmp_sink_entry_uses_resolved_path(tmp_path):
    """AC-31/IC-16: the entry comes from TmpPaths.relative, not a second parse."""
    cfg = {"enabled": True, "tmp-sink": {"enabled": True, "path": "scratch/out"}}
    assert _tmp_sink_gitignore_entry(_paths(tmp_path, cfg)) == "scratch/out/"
    assert "scratch/out/" in _entries(cfg)
    assert ".tmp/" not in _entries(cfg)

    disabled = {"enabled": True, "tmp-sink": {"enabled": False}}
    assert _tmp_sink_gitignore_entry(_paths(tmp_path, disabled)) is None
    assert ".tmp/" not in _entries(disabled)


def test_gitignore_false_yields_no_entry(tmp_path):
    cfg = {"enabled": True, "tmp-sink": {"gitignore": False}}
    assert ".tmp/" not in _entries(cfg)


def test_sink_disabled_yields_no_entry(tmp_path):
    cfg = {"enabled": True, "tmp-sink": {"enabled": False}}
    assert ".tmp/" not in _entries(cfg)


def _identifiers(tree):
    """Every referenced identifier: names, attribute accesses, import aliases."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            yield node.id
        elif isinstance(node, ast.Attribute):
            yield node.attr
        elif isinstance(node, ast.alias):
            yield node.name.split(".")[-1]
            if node.asname:
                yield node.asname


def test_sink_consumers_do_not_reparse_the_config():
    """IC-16: no second sink resolution in gitignore.py / doctor_detectors.py."""
    for name in ("gitignore.py", "doctor_detectors.py"):
        tree = ast.parse((_LIB / name).read_text(encoding="utf-8"))
        assert "resolve_effective_repo_containment" not in set(_identifiers(tree)), name
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "get_path"):
                continue
            literals = [arg.value for arg in node.args
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str)]
            assert not any("tmp-sink.path" in value for value in literals), name


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
