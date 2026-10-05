"""Regression tests for issue #847.

The Admin-UI save paths for ``config/ai-providers.yaml`` used to re-serialise
the document with ``yaml.dump``, silently stripping every YAML comment (and
potentially reordering mapping keys). Both paths now run a save-time round-trip
guard: by default they abort (HTTP 400 / raised :class:`YamlRoundTripLoss`) when
a save would lose comments or reorder keys; an explicit ``__allow_lossy__`` body
flag opts into the old, lossy behaviour.

Covers both write paths named in the issue:

* ``PUT /api/config/ai-providers``   → ``AdminRequestHandler._route_put_config``
* ``POST /api/ai-providers/update``  → ``AdminRequestHandler._handle_post_ai_providers_update``

plus the guard module itself (``scripts/lib/yaml_roundtrip.py``).
"""

from __future__ import annotations

import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any

import yaml

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ADMIN_SERVER_PATH = _PROJECT_ROOT / "scripts" / "admin-server.py"

sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))

from lib.yaml_roundtrip import (
    ALLOW_LOSSY_KEY,
    YamlRoundTripLoss,
    analyze_roundtrip,
    assert_roundtrip_preserved,
)


def _load_admin_server():
    spec = importlib.util.spec_from_file_location("admin_server", _ADMIN_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()


#: A commented registry shaped like the real ``config/ai-providers.yaml``.
_COMMENTED_REGISTRY = """\
# Provider registry — comments must survive an unchanged save.
providers:
  # The first provider block.
  Alpha:
    agents_dir: .agents/alpha
    surface-version: "v1"  # inline comment
    # Nested capability list.
    capabilities:
      - agents
      - rules
  Beta:
    agents_dir: .agents/beta
    surface-version: "v1"
"""

_COMMENT_FREE_REGISTRY = """\
providers:
  Alpha:
    surface-version: "v1"
"""


def _registry_path(root: Path) -> Path:
    return root / "config" / "ai-providers.yaml"


def _write_registry(root: Path, text: str) -> Path:
    path = _registry_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _make_handler(root: Path):
    (root / ".meta-config").mkdir(exist_ok=True)
    handler = admin_server.AdminRequestHandler.__new__(
        admin_server.AdminRequestHandler)
    admin_server.AdminRequestHandler.root = root
    admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
        root, mode="super_admin")
    return handler


def _registry_body(path: Path) -> dict[str, Any]:
    """The payload the Admin UI would send back for an unchanged form."""
    return yaml.safe_load(path.read_text(encoding="utf-8"))


class TestGuardUnit(unittest.TestCase):
    """Direct tests of the round-trip guard module."""

    def test_comment_loss_is_detected(self) -> None:
        report = analyze_roundtrip(_COMMENTED_REGISTRY, _COMMENT_FREE_REGISTRY)
        self.assertTrue(report.lossy)
        self.assertGreater(report.lost_comments, 0)

    def test_identical_text_is_lossless(self) -> None:
        report = analyze_roundtrip(_COMMENTED_REGISTRY, _COMMENTED_REGISTRY)
        self.assertFalse(report.lossy)

    def test_comment_free_roundtrip_is_lossless(self) -> None:
        dumped = yaml.safe_dump(
            yaml.safe_load(_COMMENT_FREE_REGISTRY), sort_keys=False)
        report = analyze_roundtrip(_COMMENT_FREE_REGISTRY, dumped)
        self.assertFalse(report.lossy)

    def test_key_reorder_is_detected(self) -> None:
        before = "providers:\n  Alpha: {}\n  Beta: {}\n"
        after = "providers:\n  Beta: {}\n  Alpha: {}\n"
        report = analyze_roundtrip(before, after)
        self.assertTrue(report.order_changed)
        self.assertTrue(report.lossy)

    def test_semantic_key_add_is_not_a_reorder(self) -> None:
        before = "providers:\n  Alpha:\n    a: 1\n    b: 2\n"
        after = "providers:\n  Alpha:\n    a: 1\n    b: 2\n    c: 3\n"
        report = analyze_roundtrip(before, after)
        self.assertFalse(report.order_changed)

    def test_list_reorder_is_not_a_key_reorder(self) -> None:
        before = "providers:\n  Alpha:\n    capabilities: [a, b]\n"
        after = "providers:\n  Alpha:\n    capabilities: [b, a]\n"
        report = analyze_roundtrip(before, after)
        self.assertFalse(report.order_changed)

    def test_assert_aborts_by_default(self) -> None:
        with self.assertRaises(YamlRoundTripLoss):
            assert_roundtrip_preserved(_COMMENTED_REGISTRY, _COMMENT_FREE_REGISTRY)

    def test_assert_returns_report_when_allowed(self) -> None:
        report = assert_roundtrip_preserved(
            _COMMENTED_REGISTRY,
            _COMMENT_FREE_REGISTRY,
            allow_lossy=True,
        )
        self.assertTrue(report.lossy)


class TestPutSaveRoundTrip(unittest.TestCase):
    """PUT /api/config/ai-providers (``_route_put_config``)."""

    def test_unchanged_commented_save_aborts_and_keeps_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_registry(root, _COMMENTED_REGISTRY)
            before = path.read_text(encoding="utf-8")
            handler = _make_handler(root)
            handler._read_body = lambda: _registry_body(path)
            handler._send_json = lambda result, status=200: None

            with self.assertRaises(YamlRoundTripLoss):
                handler._route_put_config("ai-providers")

            self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_opt_in_lossy_save_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_registry(root, _COMMENTED_REGISTRY)
            body = _registry_body(path)
            body[ALLOW_LOSSY_KEY] = True
            handler = _make_handler(root)
            handler._read_body = lambda: body
            captured: dict[str, Any] = {}
            handler._send_json = lambda result, status=200: captured.update(
                result=result, status=status)

            handler._route_put_config("ai-providers")

            self.assertEqual(captured["status"], 200)
            persisted = yaml.safe_load(path.read_text(encoding="utf-8"))
            # The opt-in flag must never be persisted as a registry key.
            self.assertNotIn(ALLOW_LOSSY_KEY, persisted)
            self.assertIn("Alpha", persisted["providers"])

    def test_comment_free_save_still_works(self) -> None:
        """No regression: a comment-free registry saves without the flag."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_registry(root, _COMMENT_FREE_REGISTRY)
            handler = _make_handler(root)
            handler._read_body = lambda: _registry_body(path)
            captured: dict[str, Any] = {}
            handler._send_json = lambda result, status=200: captured.update(
                result=result, status=status)

            handler._route_put_config("ai-providers")

            self.assertEqual(captured["status"], 200)


class TestPostSaveRoundTrip(unittest.TestCase):
    """POST /api/ai-providers/update (``_handle_post_ai_providers_update``)."""

    def _post_handler(self, root: Path, payload: Any):
        handler = _make_handler(root)
        raw = json.dumps(payload).encode("utf-8")
        handler.headers = {"Content-Length": str(len(raw))}
        handler.rfile = io.BytesIO(raw)
        return handler

    def test_unchanged_commented_save_returns_400_and_keeps_comments(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_registry(root, _COMMENTED_REGISTRY)
            before = path.read_text(encoding="utf-8")
            handler = self._post_handler(root, _registry_body(path))
            captured: dict[str, Any] = {}
            handler._send_json = lambda result, status=200: captured.update(
                result=result, status=status)

            handler._handle_post_ai_providers_update()

            self.assertEqual(captured["status"], 400)
            self.assertIn("error", captured["result"])
            self.assertEqual(path.read_text(encoding="utf-8"), before)

    def test_opt_in_lossy_save_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_registry(root, _COMMENTED_REGISTRY)
            body = _registry_body(path)
            body[ALLOW_LOSSY_KEY] = True
            handler = self._post_handler(root, body)
            captured: dict[str, Any] = {}
            handler._send_json = lambda result, status=200: captured.update(
                result=result, status=status)

            handler._handle_post_ai_providers_update()

            self.assertEqual(captured["status"], 200)
            persisted = yaml.safe_load(path.read_text(encoding="utf-8"))
            self.assertNotIn(ALLOW_LOSSY_KEY, persisted)
            self.assertIn("Alpha", persisted["providers"])

    def test_comment_free_save_still_works(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_registry(root, _COMMENT_FREE_REGISTRY)
            handler = self._post_handler(root, _registry_body(path))
            captured: dict[str, Any] = {}
            handler._send_json = lambda result, status=200: captured.update(
                result=result, status=status)

            handler._handle_post_ai_providers_update()

            self.assertEqual(captured["status"], 200)


class TestConfigManagerWriteGuard(unittest.TestCase):
    """The guard also protects direct ``ConfigManager.write`` callers."""

    def test_write_ai_providers_aborts_on_comment_loss(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_registry(root, _COMMENTED_REGISTRY)
            manager = admin_server.ConfigManager(root, mode="super_admin")
            with self.assertRaises(YamlRoundTripLoss):
                manager.write("ai-providers", {"providers": {"Alpha": {}}})

    def test_write_allow_lossy_proceeds(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_registry(root, _COMMENTED_REGISTRY)
            manager = admin_server.ConfigManager(root, mode="super_admin")
            result = manager.write(
                "ai-providers",
                {"providers": {"Alpha": {"surface-version": "v1"}}},
                allow_lossy=True,
            )
            self.assertEqual(result["status"], "saved")
            self.assertIn("Alpha", yaml.safe_load(path.read_text())["providers"])


if __name__ == "__main__":
    unittest.main()
