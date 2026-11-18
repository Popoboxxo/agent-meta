"""Admin API write-guard tests for ``artifact-locations`` (issue #1186, T18).

The admin server maps ``ValueError`` raised by ``_write_project_section`` to
HTTP 400 (``do_PUT``/``do_POST``), so the tests below exercise the partial-section
route directly and assert ``ValueError`` with the offending field name in the
message. This mirrors the ``test_invalid_partial_section_rejected_without_write``
seam in ``tests/test_admin_server.py``.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ADMIN_SERVER_PATH = _PROJECT_ROOT / "scripts" / "admin-server.py"
# The hyphen in ``admin-server.py`` prevents a normal import; load by path and
# make the real ``scripts/lib`` importable up front (same seam as
# tests/test_admin_server.py).
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))


def _load_admin_server():
    spec = importlib.util.spec_from_file_location(
        "admin_server_artifact_api", _ADMIN_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server_artifact_api"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()


def _make_handler(root: Path) -> Any:
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
    admin_server.AdminRequestHandler.root = root
    admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
        root, mode="project_admin")
    handler._send_json = lambda result, status=200: None
    return handler


def _put_artifact_section(handler: Any, data: Any) -> None:
    handler._read_body = lambda: {"section": "artifact-locations", "data": data}
    handler._write_project_section()


# --------------------------------------------------------------------------- #
# T18 — 9 tests (plan §5, AC-06)
# --------------------------------------------------------------------------- #


def test_put_relative_path_persists(tmp_path: Path) -> None:
    """A valid section is persisted (HTTP 200); se/off is accepted (AC-11)."""
    handler = _make_handler(tmp_path)
    data = {
        "enabled": True,
        "classes": {
            "specs": {"path": "docs/specs", "mode": "files"},
            # se-decomposition is exempt from the fallback-parent rule.
            "se-decomposition": {"mode": "off"},
        },
    }
    _put_artifact_section(handler, data)
    assert handler.config_manager.read("project")["artifact-locations"] == data


def test_put_dotdot_path_rejected_with_field_name(tmp_path: Path) -> None:
    """``../x`` -> HTTP 400 with the offending field name (AC-06 verbatim)."""
    handler = _make_handler(tmp_path)
    with pytest.raises(ValueError, match=r"artifact-locations\.classes\.specs\.path"):
        _put_artifact_section(handler, {"classes": {"specs": {"path": "../x"}}})


def test_put_absolute_path_rejected(tmp_path: Path) -> None:
    """An absolute path is rejected just like a ``..`` path."""
    handler = _make_handler(tmp_path)
    with pytest.raises(ValueError, match=r"artifact-locations\.classes\.specs\.path"):
        _put_artifact_section(handler, {"classes": {"specs": {"path": "/etc/x"}}})


def test_put_unknown_class_rejected(tmp_path: Path) -> None:
    """An unknown class key is rejected (schema guard + own guard)."""
    handler = _make_handler(tmp_path)
    with pytest.raises(ValueError, match=r"artifact-locations\.classes\.bogus"):
        _put_artifact_section(handler, {"classes": {"bogus": {"path": "docs/bogus"}}})


def test_put_se_requirements_off_rejected_when_cascade_active(tmp_path: Path) -> None:
    """se-requirements.mode=off with an active cascade -> 400 with the reason."""
    handler = _make_handler(tmp_path)
    handler.config_manager.write("project", {"systems-engineering": {"enabled": True}})
    with pytest.raises(ValueError, match="se-decomposition"):
        _put_artifact_section(
            handler, {"classes": {"se-requirements": {"mode": "off"}}})


def test_put_legacy_intersection_rejected(tmp_path: Path) -> None:
    """A legacy[] entry shadowing an active class path -> 400."""
    handler = _make_handler(tmp_path)
    data = {"classes": {"specs": {"path": "docs/specs"}}, "legacy": ["docs/specs"]}
    with pytest.raises(ValueError, match=r"artifact-locations\.legacy"):
        _put_artifact_section(handler, data)


def test_put_unmanaged_intersection_rejected(tmp_path: Path) -> None:
    """An unmanaged[] entry shadowing an active class path -> 400 (D-8)."""
    handler = _make_handler(tmp_path)
    data = {"classes": {"specs": {"path": "docs/specs"}}, "unmanaged": ["docs/specs"]}
    with pytest.raises(ValueError, match=r"artifact-locations\.unmanaged"):
        _put_artifact_section(handler, data)


def test_guard_runs_before_disk_write(tmp_path: Path) -> None:
    """A rejected write leaves project.yaml byte-identical."""
    handler = _make_handler(tmp_path)
    handler.config_manager.write(
        "project", {"artifact-locations": {"classes": {"specs": {"path": "docs/specs"}}}})
    project_file = tmp_path / ".meta-config" / "project.yaml"
    before = project_file.read_bytes()
    with pytest.raises(ValueError):
        _put_artifact_section(handler, {"classes": {"specs": {"path": "../x"}}})
    assert project_file.read_bytes() == before


def test_guard_is_wired_into_guard_block() -> None:
    """The guard is called inside _write_project_section before the disk write."""
    tree = ast.parse(_ADMIN_SERVER_PATH.read_text(encoding="utf-8"))
    fn = next(
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "_write_project_section"
    )
    guard_lines = [
        node.lineno for node in ast.walk(fn)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "_guard_artifact_locations_write"
    ]
    write_lines = [
        node.lineno for node in ast.walk(fn)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write"
        and isinstance(node.func.value, ast.Attribute)
        and node.func.value.attr == "config_manager"
    ]
    assert guard_lines, "guard must be wired into _write_project_section"
    assert write_lines, "config_manager.write must exist in the section writer"
    assert min(guard_lines) < min(write_lines), "guard must run before the disk write"
