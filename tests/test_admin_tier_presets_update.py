"""Regression tests for issue #1173.

``POST /api/tier-presets/update`` re-serialised ``config/tier-presets.yaml``
with plain ``yaml.dump`` and silently dropped every YAML comment. The handler
now runs the same save-time round-trip guard as ai-providers (issue #847):
HTTP 400 on a lossy save unless the body carries ``__allow_lossy__``.
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

from lib.yaml_roundtrip import ALLOW_LOSSY_KEY  # noqa: E402


def _load_admin_server():
    spec = importlib.util.spec_from_file_location("admin_server", _ADMIN_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()

_COMMENTED_PRESETS = """\
# Tier presets — comments must not vanish silently.
Normal:
  tiers:
    junior: haiku  # inline comment
    senior: opus
"""

_COMMENT_FREE_PRESETS = """\
Normal:
  tiers:
    junior: haiku
    senior: opus
"""


def _write_presets(root: Path, text: str) -> Path:
    path = root / "config" / "tier-presets.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _post(root: Path, payload: Any) -> dict:
    (root / ".meta-config").mkdir(exist_ok=True)
    handler = admin_server.AdminRequestHandler.__new__(
        admin_server.AdminRequestHandler)
    admin_server.AdminRequestHandler.root = root
    admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
        root, mode="super_admin")
    raw = json.dumps(payload).encode("utf-8")
    handler.headers = {"Content-Length": str(len(raw))}
    handler.rfile = io.BytesIO(raw)
    captured: dict[str, Any] = {}
    handler._send_json = lambda result, status=200: captured.update(
        result=result, status=status)
    handler._handle_post_tier_presets_update()
    return captured


class TestTierPresetsUpdateGuard(unittest.TestCase):

    def test_commented_save_returns_400_and_keeps_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_presets(root, _COMMENTED_PRESETS)
            captured = _post(root, yaml.safe_load(_COMMENTED_PRESETS))

            self.assertEqual(captured["status"], 400)
            self.assertIn(ALLOW_LOSSY_KEY, captured["result"]["error"])
            self.assertEqual(path.read_text(encoding="utf-8"), _COMMENTED_PRESETS)

    def test_allow_lossy_writes_without_persisting_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_presets(root, _COMMENTED_PRESETS)
            body = yaml.safe_load(_COMMENTED_PRESETS)
            body[ALLOW_LOSSY_KEY] = True
            captured = _post(root, body)

            self.assertEqual(captured["status"], 200)
            written = path.read_text(encoding="utf-8")
            self.assertNotIn(ALLOW_LOSSY_KEY, written)
            self.assertEqual(yaml.safe_load(written),
                             yaml.safe_load(_COMMENT_FREE_PRESETS))

    def test_comment_free_save_writes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = _write_presets(root, _COMMENT_FREE_PRESETS)
            body = yaml.safe_load(_COMMENT_FREE_PRESETS)
            body["Normal"]["tiers"]["junior"] = "sonnet"
            captured = _post(root, body)

            self.assertEqual(captured["status"], 200)
            self.assertEqual(
                yaml.safe_load(path.read_text(encoding="utf-8"))["Normal"]["tiers"]["junior"],
                "sonnet")


if __name__ == "__main__":
    unittest.main()
