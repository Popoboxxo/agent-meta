"""Generalized artifact scaffolding (Issue #1186, T8).

The matrix resolver decides which class directories are managed; the scaffold
creates one marker per ``files`` class plus the D-6 legacy ``docs/conclusions``
marker. It is dry-run-safe and idempotent. Marker files are declared here so
T14/T16 can reuse the exact same exemption source.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.artifact_locations import resolve_artifact_locations  # noqa: E402
from lib.artifact_scaffold import MARKER_FILENAMES, scaffold_artifact_dirs  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.spec_plan_scaffold import scaffold_spec_plan_dirs  # noqa: E402

# The 11 non-SE directory classes from Spec §3.1 (form ``directory``).
FILES_CLASSES = (
    "specs", "plans", "concepts", "spikes", "reviews", "audits", "analysis",
    "reports", "adr", "traceability", "runbooks",
)
LEGACY_PATHS = {
    "specs": "docs/specs", "plans": "docs/plans", "spikes": "docs/spikes",
}


def _config(*, artifact_enabled=None):
    cfg = {
        "spec-plan-workflow": {
            "enabled": True,
            "paths": dict(LEGACY_PATHS),
            "index": {"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"},
        },
        "knowledge-engine": {"enabled": True},
    }
    if artifact_enabled is not None:
        cfg["artifact-locations"] = {"enabled": artifact_enabled}
    return cfg


def _matrix_paths(cfg):
    matrix = resolve_artifact_locations(cfg, REPO_ROOT, Path("/unused"))
    return {name: cls.path for name, cls in matrix.classes.items()}


@pytest.mark.parametrize("name", FILES_CLASSES)
def test_files_mode_creates_directory_and_gitkeep(tmp_path, name):
    cfg = _config()
    log = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, cfg, log, dry_run=False)
    rel = _matrix_paths(cfg)[name]
    assert (tmp_path / rel / ".gitkeep").is_file(), f"missing {rel}/.gitkeep"


def test_ignored_classes_get_no_gitkeep(tmp_path):
    log = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, _config(), log, dry_run=False)
    assert not (tmp_path / ".tmp" / ".gitkeep").exists()
    assert not (tmp_path / ".meta-viz" / ".gitkeep").exists()


def test_legacy_conclusions_dir_is_scaffolded_without_class(tmp_path):
    cfg = _config()
    log = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, cfg, log, dry_run=False)
    assert (tmp_path / "docs" / "conclusions" / ".gitkeep").is_file()
    matrix = resolve_artifact_locations(cfg, REPO_ROOT, tmp_path)
    assert "conclusions" not in matrix.classes


def test_marker_filenames_constant_covers_scaffold_markers():
    assert MARKER_FILENAMES == frozenset({".gitkeep", ".gitignore", ".keep"})


def test_dry_run_writes_nothing(tmp_path):
    log = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, _config(), log, dry_run=True)
    assert not (tmp_path / "docs").exists()
    actions = [a for a in log.actions if "artifact scaffolding" in a]
    assert len(actions) == 12, actions


def test_second_run_is_idempotent(tmp_path):
    cfg = _config()
    first = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, cfg, first, dry_run=False)
    second = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, cfg, second, dry_run=False)
    assert not [a for a in second.actions if "artifact scaffolding" in a]
    assert len([u for u in second.unchanged if ".gitkeep" in u]) == 12
    for name in FILES_CLASSES:
        rel = _matrix_paths(cfg)[name]
        assert len(list((tmp_path / rel).glob(".gitkeep"))) == 1


def test_dry_run_with_existing_markers_logs_no_create(tmp_path):
    """--check must stay clean when markers already exist (T8 regression).

    A synced checkout has all 12 markers on disk; a dry-run over that state
    must report zero CREATE actions so ``sync.py --check`` exits 0. Missing
    markers are still reported (covered by ``test_dry_run_writes_nothing``).
    """
    cfg = _config()
    real = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, cfg, real, dry_run=False)
    assert len([a for a in real.actions if "artifact scaffolding" in a]) == 12

    check = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, cfg, check, dry_run=True)
    assert [a for a in check.actions if "artifact scaffolding" in a] == []
    assert len([u for u in check.unchanged if ".gitkeep" in u]) == 12


def test_wrapper_keeps_old_behaviour(tmp_path):
    log = SyncLog()
    scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, _config(), log, dry_run=False)
    for rel in LEGACY_PATHS.values():
        assert (tmp_path / rel / ".gitkeep").is_file(), f"missing {rel}/.gitkeep"
    # The legacy wrapper must not scaffold the generalized class set.
    assert not (tmp_path / "docs" / "audits").exists()


def test_disabled_matrix_falls_back_to_legacy_scaffold(tmp_path):
    cfg = _config(artifact_enabled=False)
    log = SyncLog()
    scaffold_artifact_dirs(REPO_ROOT, tmp_path, cfg, log, dry_run=False)
    for rel in LEGACY_PATHS.values():
        assert (tmp_path / rel / ".gitkeep").is_file(), f"missing {rel}/.gitkeep"
    assert not (tmp_path / "docs" / "audits").exists()
    assert not (tmp_path / "docs" / "conclusions").exists()
