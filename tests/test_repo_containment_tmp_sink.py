"""tmp-sink provisioning / cleanup tests (spec §5).

Covers ``ensure_tmp_sink`` (idempotent mkdir, no-op when disabled),
``ensure_tmp_sink_gitignore`` (self-ignoring fallback), the managed
``.gitignore`` entry, ``cleanup_tmp_sink`` (``manual`` never deletes,
``on-sync`` empties) and the sync stage wiring ``_sync_stage_tmp_sink``.

Run: python -m pytest tests/test_repo_containment_tmp_sink.py -v
"""

import argparse
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.gitignore import compute_base_gitignore_entries
from lib.log import SyncLog
from lib.repo_containment import (
    ResolvedRepoContainment,
    TMP_SINK_GITIGNORE_CONTENT,
    cleanup_tmp_sink,
    ensure_tmp_sink,
    ensure_tmp_sink_gitignore,
    resolve_effective_repo_containment,
)
from lib.sync_pipeline import _sync_stage_tmp_sink


def _effective(config: dict):
    return resolve_effective_repo_containment({"repo_containment": config})


# --- Provisioning -------------------------------------------------------


def test_ensure_tmp_sink_creates_directory(tmp_path):
    effective = _effective({"enabled": True})
    sink = ensure_tmp_sink(tmp_path, effective)
    assert sink == tmp_path / ".tmp"
    assert sink.is_dir()


def test_ensure_tmp_sink_is_idempotent(tmp_path):
    effective = _effective({"enabled": True})
    ensure_tmp_sink(tmp_path, effective)
    (tmp_path / ".tmp" / "keep.txt").write_text("x", encoding="utf-8")
    ensure_tmp_sink(tmp_path, effective)
    assert (tmp_path / ".tmp" / "keep.txt").exists()


def test_ensure_tmp_sink_disabled_creates_nothing(tmp_path):
    effective = _effective({"enabled": True, "tmp-sink": {"enabled": False}})
    assert ensure_tmp_sink(tmp_path, effective) is None
    assert not (tmp_path / ".tmp").exists()


def test_custom_relative_path_is_used(tmp_path):
    effective = _effective(
        {"enabled": True, "tmp-sink": {"enabled": True, "path": "scratch/x"}}
    )
    sink = ensure_tmp_sink(tmp_path, effective)
    assert sink == tmp_path / "scratch" / "x"
    assert sink.is_dir()


# --- Managed .gitignore block ------------------------------------------


def test_managed_block_includes_tmp_sink(tmp_path):
    entries = compute_base_gitignore_entries(
        ["Claude"],
        {"Claude": {}},
        {},
        {"enabled": True, "tmp-sink": {"enabled": True, "path": ".tmp"}},
    )
    assert ".tmp/" in entries


def test_managed_block_has_no_entry_without_block():
    entries = compute_base_gitignore_entries(["Claude"], {"Claude": {}}, {})
    assert ".tmp/" not in entries


def test_managed_block_honors_gitignore_false():
    entries = compute_base_gitignore_entries(
        ["Claude"],
        {"Claude": {}},
        {},
        {
            "enabled": True,
            "tmp-sink": {"enabled": True, "gitignore": False},
        },
    )
    assert ".tmp/" not in entries


# --- Self-ignoring fallback --------------------------------------------


def test_self_ignoring_gitignore_is_written(tmp_path):
    effective = _effective({"enabled": True})
    ensure_tmp_sink(tmp_path, effective)
    outcome = ensure_tmp_sink_gitignore(tmp_path, effective)
    assert outcome.changed is True
    assert outcome.path == tmp_path / ".tmp" / ".gitignore"
    assert outcome.path.read_text(encoding="utf-8") == TMP_SINK_GITIGNORE_CONTENT


def test_self_ignoring_gitignore_is_idempotent(tmp_path):
    effective = _effective({"enabled": True})
    ensure_tmp_sink(tmp_path, effective)
    ensure_tmp_sink_gitignore(tmp_path, effective)
    outcome = ensure_tmp_sink_gitignore(tmp_path, effective)
    assert outcome.changed is False


def test_self_ignoring_gitignore_skipped_when_disabled(tmp_path):
    effective = _effective(
        {"enabled": True, "tmp-sink": {"enabled": True, "gitignore": False}}
    )
    outcome = ensure_tmp_sink_gitignore(tmp_path, effective)
    assert outcome.path is None
    assert not (tmp_path / ".tmp" / ".gitignore").exists()


# --- Cleanup policy -----------------------------------------------------


def _seed_sink(tmp_path: Path) -> Path:
    effective = _effective({"enabled": True})
    sink = ensure_tmp_sink(tmp_path, effective)
    (sink / "artifact.txt").write_text("data", encoding="utf-8")
    (sink / "sub").mkdir()
    (sink / "sub" / "nested.txt").write_text("data", encoding="utf-8")
    return sink


def test_cleanup_manual_deletes_nothing(tmp_path):
    sink = _seed_sink(tmp_path)
    effective = _effective({"enabled": True, "tmp-sink": {"cleanup": "manual"}})
    assert cleanup_tmp_sink(tmp_path, effective) is None
    assert (sink / "artifact.txt").exists()
    assert (sink / "sub" / "nested.txt").exists()


def test_cleanup_on_sync_empties_contents_but_keeps_directory(tmp_path):
    sink = _seed_sink(tmp_path)
    effective = _effective({"enabled": True, "tmp-sink": {"cleanup": "on-sync"}})
    outcome = cleanup_tmp_sink(tmp_path, effective)
    assert outcome is not None
    assert outcome.performed is True
    assert "artifact.txt" in outcome.removed
    assert "sub" in outcome.removed
    assert sink.is_dir()
    assert list(sink.iterdir()) == []


def test_cleanup_on_sync_dry_run_reports_without_deleting(tmp_path):
    sink = _seed_sink(tmp_path)
    effective = _effective({"enabled": True, "tmp-sink": {"cleanup": "on-sync"}})
    outcome = cleanup_tmp_sink(tmp_path, effective, dry_run=True)
    assert outcome is not None
    assert outcome.performed is False
    assert (sink / "artifact.txt").exists()


# --- Sync stage wiring --------------------------------------------------


def _run_stage(tmp_path: Path, config: dict, dry_run: bool = False) -> None:
    config_path = tmp_path / ".meta-config" / "project.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("repo_containment: {}\n", encoding="utf-8")
    _sync_stage_tmp_sink(
        tmp_path, config_path, config, argparse.Namespace(dry_run=dry_run), SyncLog()
    )


def test_sync_stage_provisions_sink(tmp_path):
    _run_stage(tmp_path, {"repo_containment": {"enabled": True}})
    assert (tmp_path / ".tmp").is_dir()
    assert (tmp_path / ".tmp" / ".gitignore").is_file()


def test_sync_stage_disabled_creates_nothing(tmp_path):
    _run_stage(
        tmp_path,
        {"repo_containment": {"enabled": True, "tmp-sink": {"enabled": False}}},
    )
    assert not (tmp_path / ".tmp").exists()


def test_sync_stage_dry_run_provisions_nothing(tmp_path):
    _run_stage(
        tmp_path, {"repo_containment": {"enabled": True}}, dry_run=True
    )
    assert not (tmp_path / ".tmp").exists()


# --- symlink hardening (review finding: _resolve_sink_dir followed symlinks) ---


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_symlinked_sink_is_refused_and_provisions_nothing(tmp_path):
    """A ``.tmp`` symlink to a directory outside the root is never used.

    ``normpath``/``commonpath`` alone would happily target the link target and
    ``ensure_tmp_sink_gitignore`` would write outside the project root.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    os.symlink(outside, root / ".tmp")

    effective = _effective({"enabled": True})
    assert ensure_tmp_sink(root, effective) is None
    outcome = ensure_tmp_sink_gitignore(root, effective)
    assert outcome.path is None
    assert not (outside / ".gitignore").exists()
    assert (root / ".tmp").is_symlink()


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_on_sync_cleanup_with_symlinked_sink_deletes_nothing_outside_root(tmp_path):
    """``cleanup: on-sync`` must not delete through a symlinked sink.

    This is the destructive half of the finding: the old code deleted every
    child of the *resolved* sink, i.e. everything in ``outside/``.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    victim = outside / "keep.txt"
    victim.write_text("data", encoding="utf-8")
    root = tmp_path / "root"
    root.mkdir()
    os.symlink(outside, root / ".tmp")

    effective = _effective({"enabled": True, "tmp-sink": {"cleanup": "on-sync"}})
    assert cleanup_tmp_sink(root, effective) is None
    assert victim.exists()
    assert victim.read_text(encoding="utf-8") == "data"


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_symlinked_sink_pointing_inside_root_is_also_refused(tmp_path):
    """Any symlinked sink is refused, even when the target is inside the root.

    Refusing unconditionally avoids a TOCTOU race where the link is retargeted
    between the containment check and the write/delete.
    """
    root = tmp_path / "root"
    real = root / "real_tmp"
    real.mkdir(parents=True)
    os.symlink(real, root / ".tmp")

    effective = _effective({"enabled": True})
    assert ensure_tmp_sink(root, effective) is None
    assert cleanup_tmp_sink(
        root, _effective({"enabled": True, "tmp-sink": {"cleanup": "on-sync"}})
    ) is None


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_sink_under_symlinked_parent_outside_root_is_refused(tmp_path):
    """A non-leaf symlink component that escapes the root is also rejected.

    The sink itself (``link/scratch``) does not exist yet, so only the realpath
    containment re-check catches the escape.
    """
    outside = tmp_path / "outside"
    outside.mkdir()
    root = tmp_path / "root"
    root.mkdir()
    os.symlink(outside, root / "link")

    effective = _effective(
        {"enabled": True, "tmp-sink": {"path": "link/scratch"}}
    )
    assert ensure_tmp_sink(root, effective) is None
    assert ensure_tmp_sink_gitignore(root, effective).path is None
    assert not (outside / "scratch").exists()


# --- root-equality hardening (review finding: sink path resolving to root) ---


@pytest.mark.parametrize("sink_path", ["", ".", "./.", "././"])
def test_sink_resolving_to_root_provisions_and_cleans_nothing(tmp_path, sink_path):
    """A manually constructed sink resolving to the project root is refused.

    The naive ``commonpath`` check accepts ``target_real == root_real``, so
    ``cleanup_tmp_sink`` with ``cleanup: on-sync`` would delete every top-level
    project entry. ``_resolve_sink_dir`` must refuse the root itself so all
    three consumers (provision, gitignore fallback, cleanup) are no-ops.
    """
    victim = tmp_path / "keep.txt"
    victim.write_text("data", encoding="utf-8")
    pkg = tmp_path / "pkg"
    pkg.mkdir()
    (pkg / "module.py").write_text("x", encoding="utf-8")

    effective = ResolvedRepoContainment(
        enabled=True,
        source="project",
        tmp_sink_enabled=True,
        tmp_sink_path=sink_path,
        cleanup="on-sync",
    )

    assert ensure_tmp_sink(tmp_path, effective) is None
    assert ensure_tmp_sink_gitignore(tmp_path, effective).path is None
    assert cleanup_tmp_sink(tmp_path, effective) is None

    assert victim.read_text(encoding="utf-8") == "data"
    assert (pkg / "module.py").read_text(encoding="utf-8") == "x"
    assert not (tmp_path / ".gitignore").exists()
