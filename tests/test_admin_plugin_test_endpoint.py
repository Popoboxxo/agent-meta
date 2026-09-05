from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location("admin_server", REPO_ROOT / "scripts" / "admin-server.py")
admin_server = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(admin_server)


def test_match_plugin_test_route():
    h = admin_server.AdminRequestHandler
    assert h._match_plugin_test_route("/api/plugins/graphify/test") == "graphify"
    assert h._match_plugin_test_route("/api/plugins//test") is None
    assert h._match_plugin_test_route("/api/plugins/graphify") is None
    assert h._match_plugin_test_route("/api/other") is None


def test_plugin_catalog_registered_as_config_file():
    assert admin_server.SUPER_ADMIN_FILES.get("plugin-catalog") == "config/plugin-catalog.yaml"
    assert admin_server.PROJECT_FILES.get("project-plugin-catalog") == ".meta-config/plugin-catalog.yaml"
