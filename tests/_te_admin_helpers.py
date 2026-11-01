"""Shared helpers for the admin-server test-environment section tests.

``scripts/admin-server.py`` has a hyphen in its filename, so it cannot be
imported with the usual ``import scripts.admin_server`` syntax; like
``tests/test_admin_server.py`` this module loads it via :mod:`importlib`.

The admin-server imports ``lib.*`` lazily from ``<root>/scripts``. Tests run
against a throw-away root with no ``scripts/lib`` of its own, so the real
repository ``scripts`` directory is put on ``sys.path`` up front.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
_ADMIN_SERVER_PATH = REPO_ROOT / "scripts" / "admin-server.py"

_SCRIPTS_DIR = str(REPO_ROOT / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)


def _load_admin_server():
    """Load ``admin-server.py`` as a module (once per import)."""
    spec = importlib.util.spec_from_file_location(
        "admin_server_test_environments", _ADMIN_SERVER_PATH
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server_test_environments"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()


def _handler(root: Path):
    """Return a bare handler bound to ``root`` (class attrs as in production)."""
    admin_server.AdminRequestHandler.root = root
    admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
        root, mode="project_admin"
    )
    handler = admin_server.AdminRequestHandler.__new__(
        admin_server.AdminRequestHandler
    )
    handler._send_json = lambda result: None
    return handler


def _post(handler: Any, section: str, data: Any) -> None:
    """Drive the partial-section write path with ``section``/``data``."""
    handler._read_body = lambda: {"section": section, "data": data}
    handler._write_project_section()
