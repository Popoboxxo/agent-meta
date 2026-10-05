"""Regression tests for issue #864.

``--init`` / ``--fill-defaults`` (and the ``--setup`` wizard) left
``.meta-config/project.yaml`` at ``0644`` under a typical ``022`` umask, while
the Admin-UI save path already chmodded it to ``0600`` (issue #589). A
plaintext ``admin-ui.token`` or other credential key in that file was
therefore group/world-readable.

The fix hardens the file (and its ``plugin-catalog.yaml`` sibling, mirroring
``admin-server.py`` PROJECT_FILES) after every non-dry-run CLI write.
"""
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402

pytestmark = pytest.mark.skipif(
    os.name == "nt", reason="POSIX file modes do not apply on Windows"
)


def _mode(path: Path) -> int:
    return path.stat().st_mode & 0o777


def _seed_config(project_root: Path, mode: int = 0o644) -> Path:
    config_dir = project_root / ".meta-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "project.yaml"
    config_path.write_text(
        "project:\n  name: perm-test\n  prefix: pt\nai-providers:\n  - Claude\n",
        encoding="utf-8",
    )
    os.chmod(config_path, mode)
    return config_path


def test_fill_defaults_sets_owner_only(tmp_path: Path) -> None:
    """The --fill-defaults write path must end at 0600 (was 0644)."""
    from lib.config import fill_defaults

    config_path = _seed_config(tmp_path)
    assert _mode(config_path) == 0o644  # precondition

    fill_defaults(config_path, REPO_ROOT, SyncLog(), dry_run=False)

    assert _mode(config_path) == 0o600


def test_init_like_fill_defaults_sets_owner_only(tmp_path: Path) -> None:
    """--init runs fill_defaults under the hood, so it must also end at 0600."""
    from lib.config import fill_defaults

    config_path = _seed_config(tmp_path)
    assert _mode(config_path) == 0o644

    # --init calls fill_defaults(silent=True) inside the sync pipeline.
    fill_defaults(config_path, REPO_ROOT, SyncLog(), dry_run=False, silent=True)

    assert _mode(config_path) == 0o600


def test_fill_defaults_dry_run_does_not_chmod(tmp_path: Path) -> None:
    """--dry-run must not touch the filesystem — mode stays 0644."""
    from lib.config import fill_defaults

    config_path = _seed_config(tmp_path)

    fill_defaults(config_path, REPO_ROOT, SyncLog(), dry_run=True)

    assert _mode(config_path) == 0o644


def test_setup_wizard_writer_sets_owner_only(tmp_path: Path) -> None:
    """The --setup wizard's _write_config is a project.yaml writer too."""
    from lib.setup import _write_config

    config_dir = tmp_path / ".meta-config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "project.yaml"

    _write_config(config_path, {"project": {"name": "perm-test", "prefix": "pt"}})

    assert _mode(config_path) == 0o600
    assert config_path.read_text(encoding="utf-8")


def test_plugin_catalog_sibling_is_hardened_when_present(tmp_path: Path) -> None:
    """The Admin-UI path also protects the .meta-config plugin catalog."""
    from lib.permissions import harden_admin_config_files

    config_path = _seed_config(tmp_path)
    catalog = tmp_path / ".meta-config" / "plugin-catalog.yaml"
    catalog.write_text("plugins: {}\n", encoding="utf-8")
    os.chmod(catalog, 0o644)

    harden_admin_config_files(config_path)

    assert _mode(config_path) == 0o600
    assert _mode(catalog) == 0o600


def test_missing_file_is_soft_noop(tmp_path: Path) -> None:
    """A missing path must not raise — hardening is best-effort."""
    from lib.permissions import restrict_owner_only

    assert restrict_owner_only(tmp_path / "does-not-exist.yaml") is False
