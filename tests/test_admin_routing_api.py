"""Roadmap PR 5.4 / P27 — Block C (Tasks 13-15) tests.

Task 13: read-only routing API (``GET /api/routing/model``,
``GET /api/routing/preview?provider=<P>``) plus the fail-closed write guard on
the existing ``PUT /api/config/project/section`` path for ``routing-overrides``
(AC-R5). Decision 3 (21.11.): no ``routing_lint.py`` / ``RL-*`` codes — the
guard composes ``lib.doctor_formats.validate_schema_subset`` (schema
``additionalProperties: false``) with
``lib.consistency.active_set_refs.check_keyword_overlap`` (IC-29).
Task 14: static wiring/a11y assertions for the ``/project/routing`` Admin UI
view (AC-R9).
Task 15: eval generator data source (``routing.triggers``), collision report,
idempotence, >= 55 cases and the ``list_cases.py`` listing (AC-R8).

No LLM call and no network access happens in this module.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ADMIN_SERVER_PATH = _PROJECT_ROOT / "scripts" / "admin-server.py"
sys.path.insert(0, str(_PROJECT_ROOT / "scripts"))


def _load_admin_server():
    spec = importlib.util.spec_from_file_location(
        "admin_server_routing_api", _ADMIN_SERVER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["admin_server_routing_api"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


admin_server = _load_admin_server()


def _make_handler(root: Path):
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    handler = admin_server.AdminRequestHandler.__new__(admin_server.AdminRequestHandler)
    # Framework assets (role-defaults.yaml, schema) live in the repo root;
    # only project.yaml is redirected to the throw-away root (self-hosting).
    admin_server.AdminRequestHandler.root = _PROJECT_ROOT
    admin_server.AdminRequestHandler.config_manager = admin_server.ConfigManager(
        root, mode="project_admin")
    captured: dict = {}
    handler._send_json = lambda payload, status=200: captured.update(
        payload=payload, status=status)
    return handler, captured


def _put_routing(handler, data) -> None:
    handler._read_body = lambda: {"section": "routing-overrides", "data": data}
    handler._write_project_section()


def _project_file(root: Path) -> Path:
    return root / ".meta-config" / "project.yaml"


# --------------------------------------------------------------------------- #
# Task 13 — API routes, model, preview, fail-closed guard                    #
# --------------------------------------------------------------------------- #

def test_routing_overrides_is_writable_section():
    assert "routing-overrides" in admin_server.PROJECT_WRITABLE_SECTIONS


def test_get_routes_registered_without_post_alias():
    """Decision 4: use the existing PUT route; no POST alias for routing."""
    routes = admin_server.AdminRequestHandler._GET_EXACT_ROUTES
    assert routes.get("/api/routing/model") == "_route_get_routing_model"
    assert routes.get("/api/routing/preview") == "_route_get_routing_preview"
    posts = admin_server.AdminRequestHandler._POST_EXACT_ROUTES
    assert "/api/config/project/section" not in posts
    assert "/api/routing/model" not in posts
    assert "/api/routing/preview" not in posts
    put = admin_server.AdminRequestHandler._PUT_EXACT_ROUTES
    assert put.get("/api/config/project/section") == "_write_project_section"


def test_get_routing_model_reports_effective_fields_and_source(tmp_path: Path):
    handler, captured = _make_handler(tmp_path)
    handler.config_manager.write("project", {
        "routing-overrides": {
            "format": "compact",
            "roles": {"developer": {"triggers": ["Feature bauen"]}},
        },
    })
    handler._route_get_routing_model()
    payload = captured["payload"]
    assert isinstance(payload["roles"], dict) and "developer" in payload["roles"]
    dev = payload["roles"]["developer"]
    assert "Feature bauen" in dev["triggers"]
    source = payload["source"]
    assert source["roles.developer.triggers"] == "override"
    assert source["format"] == "override"
    assert source["roles.tester.triggers"] == "default"
    assert payload["overrides"]["format"] == "compact"


def test_get_routing_preview_has_bytes_token_proxy_and_lint(tmp_path: Path):
    handler, captured = _make_handler(tmp_path)
    handler.path = "/api/routing/preview?provider=Claude"
    handler._route_get_routing_preview()
    payload = captured["payload"]
    assert payload["provider"] == "Claude"
    assert isinstance(payload["block"], str) and payload["block"]
    assert payload["bytes"] == len(payload["block"].encode("utf-8"))
    assert payload["tokens_est"] == payload["bytes"] // 4
    assert payload["token_basis"] == "bytes/4 (proxy)"
    assert isinstance(payload["lint"], list)
    assert payload["format"] in {"compact", "json", "off"}


def test_preview_unknown_provider_is_fail_soft(tmp_path: Path):
    """No provider literal/branch: an unknown provider yields an empty block."""
    handler, captured = _make_handler(tmp_path)
    handler.path = "/api/routing/preview?provider=NotAProvider"
    handler._route_get_routing_preview()
    payload = captured["payload"]
    assert payload["block"] == ""
    assert payload["bytes"] == 0


def test_put_routing_overrides_unknown_key_rejected_without_write(tmp_path: Path):
    """Schema ``additionalProperties: false`` -> HTTP 400, project.yaml unchanged."""
    handler, _ = _make_handler(tmp_path)
    handler.config_manager.write("project", {"version": "1.2.3"})
    before = _project_file(tmp_path).read_bytes()
    with pytest.raises(ValueError, match=r"unexpected property.*bogus"):
        _put_routing(handler, {"bogus": True})
    assert _project_file(tmp_path).read_bytes() == before


def test_put_routing_overrides_unknown_nested_key_rejected_without_write(tmp_path: Path):
    """``roles.<role>.additionalProperties: false`` -> HTTP 400, no write."""
    handler, _ = _make_handler(tmp_path)
    handler.config_manager.write("project", {"version": "1.2.3"})
    before = _project_file(tmp_path).read_bytes()
    with pytest.raises(ValueError, match=r"unexpected property.*typo"):
        _put_routing(handler, {"roles": {"developer": {"typo": 1}}})
    assert _project_file(tmp_path).read_bytes() == before


def test_put_routing_overrides_unknown_role_rejected_without_write(tmp_path: Path):
    handler, _ = _make_handler(tmp_path)
    handler.config_manager.write("project", {"version": "1.2.3"})
    before = _project_file(tmp_path).read_bytes()
    with pytest.raises(ValueError, match=r"unknown role"):
        _put_routing(handler, {"roles": {"no-such-role": {"triggers": ["x"]}}})
    assert _project_file(tmp_path).read_bytes() == before


def test_put_routing_overrides_new_overlap_rejected_without_write(tmp_path: Path):
    """check_keyword_overlap (IC-29) is fail-closed for NEW collisions (AC-R5)."""
    handler, _ = _make_handler(tmp_path)
    handler.config_manager.write("project", {"version": "1.2.3"})
    before = _project_file(tmp_path).read_bytes()
    data = {"roles": {
        "developer": {"triggers": ["shared-routing-token"]},
        "tester": {"triggers": ["shared-routing-token"]},
    }}
    with pytest.raises(ValueError, match=r"overlap"):
        _put_routing(handler, data)
    assert _project_file(tmp_path).read_bytes() == before


def test_put_routing_overrides_valid_section_persists(tmp_path: Path):
    handler, _ = _make_handler(tmp_path)
    data = {"format": "compact", "roles": {"developer": {"priority": 2}}}
    _put_routing(handler, data)
    assert handler.config_manager.read("project")["routing-overrides"] == data


# --------------------------------------------------------------------------- #
# Task 14 — UI wiring + WCAG 2.1 AA static assertions                        #
# --------------------------------------------------------------------------- #

HTML = (_PROJECT_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
HELP_REF = (_PROJECT_ROOT / "docs" / "api" / "admin-ui-reference.md").read_text(encoding="utf-8")


def _routing_view() -> str:
    start = HTML.index("async function viewProjectRouting()")
    end = HTML.index("/* --------------------------- Release Checklist", start)
    return HTML[start:end]


def test_ui_nav_router_and_help_wired():
    assert 'route: "/project/routing"' in HTML
    assert 'router.register("/project/routing",         viewProjectRouting)' in HTML
    assert '"project/routing": "project_instance-routing"' in HTML
    assert "<!-- help-id: project_instance-routing -->" in HELP_REF


def test_ui_view_has_role_table_badges_reset_and_server_preview():
    view = _routing_view()
    assert 'el("table"' in view and 'scope: "col"' in view
    assert "Default" in view and "Override" in view
    assert "Reset to default" in view
    assert 'api.get("/api/routing/model")' in view
    assert "/api/routing/preview?provider=" in view
    assert "saveProjectSection(\"routing-overrides\"" in view


def test_ui_preview_is_debounced_and_accessible():
    view = _routing_view()
    assert "setTimeout" in view and "400" in view
    assert 'role: "status"' in view and '"aria-live": "polite"' in view
    assert 'a11yField(' in view
    assert "Bytes/4" in view or "bytes/4" in view
    assert "tagEditorField(" in view


# --------------------------------------------------------------------------- #
# Task 15 — eval generator: routing.triggers, collisions, idempotence        #
# --------------------------------------------------------------------------- #

def _generator():
    spec = importlib.util.spec_from_file_location(
        "gen_role_routing_eval_catalog_test",
        _PROJECT_ROOT / "scripts" / "gen_role_routing_eval_catalog.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_generator_prefers_routing_triggers(monkeypatch):
    """Decision 2: `routing.triggers` is the primary source; legacy is fallback."""
    gen = _generator()
    roles = {
        "developer": {
            "routing": {"triggers": ["Feature bauen"], "examples": ["Baue Feature X."]},
            "routing_patterns": {"keywords": ["LEGACY"], "examples": ["legacy ex"]},
        },
        "tester": {
            "routing_patterns": {"keywords": ["Tests schreiben"], "examples": []},
        },
    }
    monkeypatch.setattr(gen, "load_roles_config", lambda _root: {"roles": roles})
    cases = gen.generate_catalog(_PROJECT_ROOT)["cases"]
    tasks = [c["task"] for c in cases]
    assert any("Feature bauen" in t for t in tasks)
    assert any("Baue Feature X." in t for t in tasks)
    assert not any("LEGACY" in t for t in tasks)
    assert any("Tests schreiben" in t for t in tasks)


def test_generator_collision_report_and_idempotence():
    gen = _generator()
    catalog = gen.generate_catalog(_PROJECT_ROOT)
    assert len(catalog["cases"]) >= 55
    again = gen.generate_catalog(_PROJECT_ROOT)
    assert gen.render_catalog(catalog) == gen.render_catalog(again)
    report = gen.collision_report(catalog)
    assert report  # the framework has known overlap tokens (IC-29)
    assert all(len(item["owners"]) >= 2 for item in report)
    assert all(item["token"] for item in report)
    # Every reported collision has explicit ASK + per-owner disambiguation cases.
    ids = {c["id"] for c in catalog["cases"]}
    for item in report:
        slug = item["token"].replace(" ", "-")
        assert f"rc-{slug}-ask" in ids
        for owner in item["owners"]:
            assert any(cid.startswith(f"rc-{slug}-{owner}-") for cid in ids)


def test_committed_catalog_matches_generator():
    gen = _generator()
    committed = (_PROJECT_ROOT / "tests" / "routing-llm-eval" / "roles"
                 / gen.GENERATED_NAME).read_bytes()
    assert committed == gen.render_catalog(gen.generate_catalog(_PROJECT_ROOT)).encode("utf-8")


def test_list_cases_lists_role_cases_without_llm(tmp_path: Path):
    """AC-R8 (decision 5): `list_cases.py` is the dry listing, no run_eval.sh."""
    catalog = (_PROJECT_ROOT / "tests" / "routing-llm-eval" / "roles"
               / "catalog.generated.yaml")
    result = subprocess.run(
        [sys.executable, str(_PROJECT_ROOT / "tests" / "routing-llm-eval" / "list_cases.py"),
         str(catalog)],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    expected = len((__import__("yaml").safe_load(catalog.read_text()) or {}).get("cases", []))
    assert len(lines) == expected
    assert all(line.split("\x1f")[0].startswith(("rk-", "rx-", "rn-", "rc-")) for line in lines)
