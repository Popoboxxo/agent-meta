"""Admin surface for the ``release-checklist`` project section.

Task 7 covers the server side: the section is part of the writable
whitelist and every write goes through ``_guard_release_checklist_write``,
which normalises the YAML-1.1 ``False`` mode to ``"off"``, rejects ``True``
("quote the value") and rejects any payload that would abort the next
``sync.py`` run — all before a single byte is persisted.

Task 8 covers the Admin UI wiring: sidebar entry, router registration,
``routeMap`` help-id and the matching help block in the API reference.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
_ADMIN_SERVER_PATH = REPO_ROOT / "scripts" / "admin-server.py"
# `lib.*` imports inside admin-server resolve through the real scripts dir.
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _load_admin_server():
    spec = importlib.util.spec_from_file_location("admin_server", _ADMIN_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()


def _make_handler(root: Path):
    (root / ".meta-config").mkdir(exist_ok=True)
    handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
    admin_server.AdminRequestHandler.root = root
    admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
        root, mode="project_admin")
    handler._send_json = lambda result: None
    return handler


def _put(handler, data):
    handler._read_body = lambda: {"section": "release-checklist", "data": data}
    handler._write_project_section()


# --------------------------------------------------------------------------- #
# Task 7 — whitelist and section guard                                       #
# --------------------------------------------------------------------------- #


def test_whitelist_contains_section():                                      # AC-REL-13
    assert "release-checklist" in admin_server.PROJECT_WRITABLE_SECTIONS


def test_valid_payload_roundtrip(tmp_path):
    h = _make_handler(tmp_path)
    payload = {"mode": "strict", "items": [{"id": "schema-valid", "task": "t", "verification": "v", "check": "script", "script": "python3 -V"}]}
    _put(h, payload)
    assert h.config_manager.read("project")["release-checklist"] == payload


def test_invalid_payloads_rejected_without_write(tmp_path):                 # AC-REL-13
    h = _make_handler(tmp_path)
    h.config_manager.write("project", {"release-checklist": {"mode": "advisory"}})
    dup = {"mode": "strict", "items": [{"id": "a", "task": "t", "verification": "v"}] * 2}
    for bad in ({"mode": "loose"}, {"mode": True}, {"mode": "strict", "bogus": 1}, dup):
        with pytest.raises(ValueError):
            _put(h, bad)
    assert h.config_manager.read("project")["release-checklist"] == {"mode": "advisory"}


def test_guard_normalizes_false_and_rejects_true(tmp_path):                 # R5
    h = _make_handler(tmp_path)
    _put(h, {"mode": False})
    assert h.config_manager.read("project")["release-checklist"]["mode"] == "off"
    with pytest.raises(ValueError, match="quote the value"):
        _put(h, {"mode": True})


def test_off_roundtrips_as_string(tmp_path):                                # R5, OF-8
    h = _make_handler(tmp_path)
    _put(h, {"mode": "off"})
    raw = (tmp_path / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
    loaded = yaml.safe_load(raw)["release-checklist"]["mode"]
    assert loaded == "off" and isinstance(loaded, str)                      # Writer quotet "off"


def test_parity_with_direct_yaml_fragment(tmp_path):                        # AC-REL-15
    payload = {"mode": "advisory", "items": [{"id": "x-1", "task": "t", "verification": "v", "phase": "step", "required": False}]}
    h = _make_handler(tmp_path)
    _put(h, payload)
    manual = yaml.safe_load(yaml.safe_dump({"release-checklist": payload}))
    assert yaml.safe_load((tmp_path / ".meta-config" / "project.yaml").read_text(encoding="utf-8")) == manual
