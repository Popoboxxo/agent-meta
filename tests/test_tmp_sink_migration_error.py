"""AC-99: unsafe pre-existing tmp-sink paths abort the sync with a migration hint.

Run: python -m pytest tests/test_tmp_sink_migration_error.py -v
"""

import ast
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import _validate_repo_containment

_SYNC = _REPO_ROOT / "scripts" / "sync.py"


def _config_path(tmp_path: Path) -> Path:
    path = tmp_path / ".meta-config" / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _cfg(path: str) -> dict:
    return {"repo_containment": {"tmp-sink": {"path": path}}}


def _assert_full_message(err: str) -> None:
    assert "repo_containment.tmp-sink.path" in err
    assert "Migration:" in err
    assert ".tmp" in err and "scratch/out" in err


@pytest.mark.parametrize(
    "path",
    ["C:\\x", "\\\\server\\share\\x", "CON", ".GIT"],
)
def test_unsafe_legacy_path_is_hard_error_with_migration(path, tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate_repo_containment(_cfg(path), _config_path(tmp_path))
    assert exc.value.code != 0
    err = capsys.readouterr().err
    _assert_full_message(err)
    assert repr(path) in err


def test_intermediate_symlink_escape_is_hard_error(tmp_path, capsys):
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    try:
        os.symlink(outside, project / "link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    with pytest.raises(SystemExit) as exc:
        _validate_repo_containment(_cfg("link/x"), _config_path(project))
    assert exc.value.code != 0
    _assert_full_message(capsys.readouterr().err)


@pytest.mark.parametrize("path", [".tmp", "scratch/out"])
def test_safe_paths_pass(path, tmp_path):
    _validate_repo_containment(_cfg(path), _config_path(tmp_path))


def test_sync_renders_nothing_on_unsafe_path(tmp_path):
    project = tmp_path / "proj"
    (project / ".meta-config").mkdir(parents=True)
    (project / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers:\n- Claude\n"
        "dod-preset: rapid-prototyping\n"
        "repo_containment:\n  tmp-sink:\n    path: 'C:\\x'\n"
        "variables:\n  PROJECT_NAME: m\n  PROJECT_PREFIX: mx\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = subprocess.run(
        [sys.executable, str(_SYNC), "--config",
         str(project / ".meta-config" / "project.yaml")],
        cwd=project, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode != 0
    _assert_full_message(result.stderr)
    assert not (project / ".claude" / "agents").exists()


def test_matrix_fixtures_are_free_of_tmp_sink_paths():
    ac01_path = _REPO_ROOT / "tests" / "test_ac01_render_identity.py"
    source = ac01_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    funcs = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_make_project"
    ]
    if not funcs:
        pytest.fail(
            f"fixture anchor '_make_project' not found in {ac01_path.name}; "
            "it was renamed or removed - update this test to the new fixture builder"
        )
    segment = ast.get_source_segment(source, funcs[0]) or ""
    assert segment, f"could not extract source of _make_project from {ac01_path.name}"
    assert "tmp-sink" not in segment
    base = _REPO_ROOT / "tests" / "fixtures" / "ac01-baseline"
    for f in base.rglob("*.y*ml"):
        assert "tmp-sink" not in f.read_text(encoding="utf-8", errors="replace")
