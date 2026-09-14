"""Endpoint and UI-source tests for the stale-role cleanup admin routes.

Covers IC-07 (``/api/roles/cleanup/preview`` and ``/api/roles/cleanup/apply``)
and IC-10 (the ``admin-ui.html`` preview -> confirm -> apply control) from
``docs/specs/2026-09-13-stale-role-cleanup-design.md``:

* AC-11 preview route returns the payload without writing
* AC-12 apply refuses without ``confirm: true`` (400, no ``run()``)
* AC-13 apply rejects a stale fingerprint (409, no ``run()``)
* AC-14 apply derives ``deleted`` from the recomputed preview's stale paths
  and emits no ``deleted`` on failure
* AC-15 (mirror) ``foreign`` entries are never deleted
* AC-25 the UI control is wired preview -> confirm -> apply with a 409 re-render

``admin-server.py`` is loaded through :mod:`importlib` because the file name
contains a hyphen (the pattern of ``tests/test_admin_server.py``).

No test here mutates the repository: the real ``SyncExecutor`` subprocess is
monkeypatched and the route tests use a ``Mock`` executor.
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path
from typing import Any
from unittest import mock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "admin_server_cleanup_endpoint", REPO_ROOT / "scripts" / "admin-server.py"
)
admin_server = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(admin_server)

HTML = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def _stale(path: str, reason: str = "role removed from config") -> dict:
    return {
        "provider": "Claude",
        "path": path,
        "reason": reason,
        "tracked": True,
        "adopted": False,
    }


def _make_handler(body: Any = None) -> tuple[Any, dict]:
    """Build a bare handler whose ``_send_json`` records instead of writing."""
    handler = admin_server.AdminRequestHandler.__new__(
        admin_server.AdminRequestHandler
    )
    raw = json.dumps(body if body is not None else {}).encode("utf-8")
    handler.headers = {"Content-Length": str(len(raw))}
    handler.rfile = io.BytesIO(raw)
    captured: dict = {}

    def _send_json(payload, status=200, **kwargs):  # noqa: ANN001
        captured["payload"] = payload
        captured["status"] = status

    handler._send_json = _send_json
    return handler, captured


@pytest.fixture()
def executor(monkeypatch: pytest.MonkeyPatch) -> mock.Mock:
    stub = mock.Mock()
    monkeypatch.setattr(
        admin_server.AdminRequestHandler, "sync_executor", stub, raising=False
    )
    return stub


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def test_cleanup_routes_registered() -> None:
    routes = admin_server.AdminRequestHandler._POST_EXACT_ROUTES
    assert routes["/api/roles/cleanup/preview"] == "_route_post_roles_cleanup_preview"
    assert routes["/api/roles/cleanup/apply"] == "_route_post_roles_cleanup_apply"


# ---------------------------------------------------------------------------
# AC-11 — preview route
# ---------------------------------------------------------------------------


def test_preview_route_returns_payload(executor: mock.Mock) -> None:
    stale = [_stale(".claude/agents/foo.md")]
    foreign = [
        {
            "provider": "Claude",
            "path": ".claude/agents/my-own.md",
            "legacy_unmarked": True,
        }
    ]
    executor.cleanup_preview.return_value = {
        "success": True,
        "stale": stale,
        "foreign": foreign,
        "fingerprint": "sha256:abc",
    }
    handler, captured = _make_handler({})

    handler._route_post_roles_cleanup_preview()

    assert captured["status"] == 200
    assert captured["payload"] == {
        "success": True,
        "stale": stale,
        "foreign": foreign,
        "fingerprint": "sha256:abc",
    }
    # Read-only: the apply path must not be touched by a preview request.
    executor.run.assert_not_called()
    executor.cleanup_preview.assert_called_once_with()


def test_preview_route_reports_preview_failure_as_500(executor: mock.Mock) -> None:
    executor.cleanup_preview.return_value = {
        "success": False,
        "error": "sync_preview_failed",
        "output": "boom",
    }
    handler, captured = _make_handler({})

    handler._route_post_roles_cleanup_preview()

    assert captured["status"] == 500
    assert captured["payload"]["success"] is False
    assert captured["payload"]["error"] == "sync_preview_failed"
    executor.run.assert_not_called()


# ---------------------------------------------------------------------------
# AC-12 — confirm required
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("body", [{}, {"confirm": False}, {"confirm": "true"}])
def test_apply_requires_confirm_true(executor: mock.Mock, body: dict) -> None:
    handler, captured = _make_handler(body)

    handler._route_post_roles_cleanup_apply()

    assert captured["status"] == 400
    assert captured["payload"] == {"error": "confirmation_required"}
    executor.cleanup_preview.assert_not_called()
    executor.run.assert_not_called()


def test_apply_confirmation_checked_before_preview(executor: mock.Mock) -> None:
    """A missing confirm must short-circuit before any preview recomputation."""
    executor.cleanup_preview.side_effect = AssertionError("preview must not run")
    handler, captured = _make_handler({"confirm": False})

    handler._route_post_roles_cleanup_apply()

    assert captured["status"] == 400
    executor.run.assert_not_called()


# ---------------------------------------------------------------------------
# AC-13 — TOCTOU fingerprint mismatch
# ---------------------------------------------------------------------------


def test_apply_fingerprint_mismatch_is_409(executor: mock.Mock) -> None:
    recomputed_stale = [_stale(".claude/agents/foo.md")]
    executor.cleanup_preview.return_value = {
        "success": True,
        "stale": recomputed_stale,
        "foreign": [],
        "fingerprint": "sha256:new",
    }
    handler, captured = _make_handler(
        {"confirm": True, "fingerprint": "sha256:old"}
    )

    handler._route_post_roles_cleanup_apply()

    assert captured["status"] == 409
    assert captured["payload"] == {
        "error": "preview_stale",
        "stale": recomputed_stale,
    }
    executor.run.assert_not_called()


def test_apply_preview_failure_is_500(executor: mock.Mock) -> None:
    executor.cleanup_preview.return_value = {
        "success": False,
        "error": "sync_preview_failed",
        "output": "boom",
    }
    handler, captured = _make_handler(
        {"confirm": True, "fingerprint": "sha256:cur"}
    )

    handler._route_post_roles_cleanup_apply()

    assert captured["status"] == 500
    assert captured["payload"]["error"] == "sync_preview_failed"
    executor.run.assert_not_called()


# ---------------------------------------------------------------------------
# AC-14 — deleted derived from the recomputed preview
# ---------------------------------------------------------------------------


def test_apply_success_returns_recomputed_stale_paths(executor: mock.Mock) -> None:
    p1 = _stale(".claude/agents/p1.md")
    p2 = _stale(".claude/agents/p2.md", reason="skill deactivated")
    executor.cleanup_preview.return_value = {
        "success": True,
        "stale": [p1, p2],
        "foreign": [],
        "fingerprint": "sha256:cur",
    }
    executor.run.return_value = {
        "success": True,
        "returncode": 0,
        # Misleading stdout: `deleted` must come from the recomputed preview,
        # never from parsing a human-readable sync log (F-03).
        "output": "DELETE .claude/agents/from-stdout.md",
    }
    handler, captured = _make_handler(
        {"confirm": True, "fingerprint": "sha256:cur"}
    )

    handler._route_post_roles_cleanup_apply()

    assert captured["status"] == 200
    assert captured["payload"]["success"] is True
    assert captured["payload"]["returncode"] == 0
    assert captured["payload"]["deleted"] == [p1["path"], p2["path"]]
    assert ".claude/agents/from-stdout.md" not in captured["payload"]["deleted"]
    executor.run.assert_called_once_with()


@pytest.mark.parametrize(
    "run_result",
    [
        {"success": False, "returncode": 1, "output": "sync failed"},
        {"success": False, "returncode": -1, "output": "sync.py timed out (300s)"},
    ],
)
def test_apply_failure_returns_500_without_deleted(
    executor: mock.Mock, run_result: dict
) -> None:
    executor.cleanup_preview.return_value = {
        "success": True,
        "stale": [_stale(".claude/agents/p1.md")],
        "foreign": [],
        "fingerprint": "sha256:cur",
    }
    executor.run.return_value = run_result
    handler, captured = _make_handler(
        {"confirm": True, "fingerprint": "sha256:cur"}
    )

    handler._route_post_roles_cleanup_apply()

    assert captured["status"] == 500
    assert captured["payload"]["error"] == "sync_failed"
    assert "deleted" not in captured["payload"]


# ---------------------------------------------------------------------------
# AC-15 (mirror) — foreign entries are never deleted
# ---------------------------------------------------------------------------


def test_foreign_never_deleted_in_preview_and_apply(executor: mock.Mock) -> None:
    foreign = [
        {
            "provider": "Claude",
            "path": ".claude/agents/my-own.md",
            "legacy_unmarked": True,
        }
    ]

    # Preview: foreign is surfaced, stale stays empty.
    executor.cleanup_preview.return_value = {
        "success": True,
        "stale": [],
        "foreign": foreign,
        "fingerprint": "sha256:cur",
    }
    handler, captured = _make_handler({})
    handler._route_post_roles_cleanup_preview()
    assert captured["payload"]["foreign"] == foreign
    assert captured["payload"]["stale"] == []

    # Apply: deleted comes from stale only, never from foreign.
    handler, captured = _make_handler(
        {"confirm": True, "fingerprint": "sha256:cur"}
    )
    executor.run.return_value = {"success": True, "returncode": 0, "output": ""}
    handler._route_post_roles_cleanup_apply()
    assert captured["payload"]["deleted"] == []
    for entry in foreign:
        assert entry["path"] not in captured["payload"]["deleted"]


# ---------------------------------------------------------------------------
# SyncExecutor.cleanup_preview parsing (IC-07 contract)
# ---------------------------------------------------------------------------


def test_cleanup_preview_parses_and_flattens_provider_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = admin_server.SyncExecutor(REPO_ROOT)
    payload = {
        "version": 1,
        "providers": [
            {
                "provider": "Claude",
                "stale": [_stale(".claude/agents/x.md")],
                "foreign": [{"path": ".claude/agents/own.md", "legacy_unmarked": True}],
                "backups_to_prune": [".claude/agents/x.md.sync-backup-1"],
            },
            {
                "provider": "Opencode",
                "stale": [],
                "foreign": [],
                "backups_to_prune": [],
            },
        ],
        "fingerprint": "sha256:z",
    }
    monkeypatch.setattr(
        instance,
        "_run",
        lambda args: {"success": True, "output": json.dumps(payload), "returncode": 0},
    )

    result = instance.cleanup_preview()

    assert result["success"] is True
    assert result["fingerprint"] == "sha256:z"
    assert result["stale"][0]["provider"] == "Claude"
    assert result["stale"][0]["path"] == ".claude/agents/x.md"
    assert result["foreign"][0]["path"] == ".claude/agents/own.md"
    assert result["backups_to_prune"] == [".claude/agents/x.md.sync-backup-1"]


def test_cleanup_preview_rejects_non_json_output(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = admin_server.SyncExecutor(REPO_ROOT)
    monkeypatch.setattr(
        instance,
        "_run",
        lambda args: {"success": True, "output": "not json", "returncode": 0},
    )

    result = instance.cleanup_preview()

    assert result["success"] is False
    assert result["error"] == "sync_preview_failed"


def test_cleanup_preview_reports_subprocess_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    instance = admin_server.SyncExecutor(REPO_ROOT)
    monkeypatch.setattr(
        instance,
        "_run",
        lambda args: {"success": False, "output": "boom", "returncode": 1},
    )

    result = instance.cleanup_preview()

    assert result["success"] is False
    assert result["error"] == "sync_preview_failed"
    assert result["output"] == "boom"


# ---------------------------------------------------------------------------
# AC-25 — UI control wiring (source assertion; no DOM harness exists)
# ---------------------------------------------------------------------------


def test_ui_cleanup_control_wiring() -> None:
    # 1. The preview trigger is a button in the sync btn-row.
    assert '["Preview cleanup"]' in HTML
    assert "[runBtn, dryBtn, standaloneBtn, cleanupPreviewBtn]" in HTML

    # 2. Preview requests the read-only preview route.
    assert 'api.post("/api/roles/cleanup/preview")' in HTML

    # 3. A single Remove-N danger button is disabled unless N > 0.
    assert "Remove ${" in HTML
    assert "cleanupRemoveBtn.disabled = !(canRemove && count > 0)" in HTML

    # 4. Confirm posts confirm:true plus the stored fingerprint.
    assert (
        'api.post("/api/roles/cleanup/apply", { confirm: true, fingerprint: cleanupFingerprint })'
        in HTML
    )
    assert "confirmDestructive(" in HTML

    # 5. A 409 re-renders from the returned stale list and never wedges the
    #    controls (all mutation paths re-enable the sync buttons in finally).
    assert "err.status === 409" in HTML
    assert "renderCleanupPanel((err.body && err.body.stale) || [], [], false)" in HTML
    assert HTML.count("finally { setSyncButtonsDisabled(false); }") >= 2

    # 6. foreign entries are rendered read-only with the legacy flag.
    assert "legacy_unmarked" in HTML
