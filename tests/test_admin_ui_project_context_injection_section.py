"""Admin-API writability for the ``project-context-injection`` project section
(issue #1187, T12).

T12 registers the section in ``PROJECT_WRITABLE_SECTIONS`` and guards the
partial-section write path: the section round-trips through
``PUT /api/config/project/section`` while every other section (incl. ``git``)
is left untouched. A misspelled section still produces HTTP 400.

The UI-side tests (nav/router/help wiring, pane persistence and enums) are
appended in T13 under the ``T13 — ui`` banner below.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _te_admin_helpers import _handler, _post, admin_server  # noqa: E402

SECTION = "project-context-injection"


# --------------------------------------------------------------------------- #
# T12 — api                                                                    #
# --------------------------------------------------------------------------- #


def test_whitelist_contains_section():
    assert SECTION in admin_server.PROJECT_WRITABLE_SECTIONS


def test_valid_payload_round_trips(tmp_path):
    h = _handler(tmp_path)
    _post(h, SECTION, {"mode": "core"})
    assert h.config_manager.read("project")[SECTION] == {"mode": "core"}


def test_invalid_section_still_400(tmp_path):
    """A section missing from the whitelist is rejected with HTTP 400."""
    h = _handler(tmp_path)
    captured: dict = {}
    h._send_json = lambda result, status=200: captured.update(
        result=result, status=status
    )
    h.path = "/api/config/project/section"
    body = json.dumps(
        {"section": "project-context-injectio", "data": {"mode": "core"}}
    ).encode("utf-8")
    h.headers = {"Content-Length": str(len(body))}
    h.rfile = io.BytesIO(body)
    h._check_token = lambda: None
    h._check_origin = lambda: None
    h.do_PUT()
    assert captured["status"] == 400
    assert "section not allowed" in captured["result"]["detail"]


def test_roundtrip_does_not_touch_other_sections(tmp_path):
    h = _handler(tmp_path)
    git = {"default_branch": "main", "keep": 1}
    h.config_manager.write("project", {"git": git})
    _post(h, SECTION, {"mode": "core"})
    project = h.config_manager.read("project")
    assert project[SECTION] == {"mode": "core"}
    assert project["git"] == git
