"""Static assertions for the Admin UI "Git" / "Auto-Commit" / "Subagent
Permissions" project-instance sections (feature ``subagent-permissions-git-admin-ui``).

These tests read ``docs/ui/admin-ui.html`` and ``docs/api/admin-ui-reference.md``
as text and verify the wiring the spec requires: sidebar entries, router
registrations, the ``routeMap`` help-id mapping and its matching help blocks,
plus the client-side gates (``custom`` mode requires ``custom_script``).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
HELP_REF = (REPO_ROOT / "docs" / "api" / "admin-ui-reference.md").read_text(encoding="utf-8")

NEW_ROUTES = {
    "/project/subagent-permissions": ("viewProjectSubagentPermissions", "project_instance-subagent_permissions"),
    "/project/git": ("viewProjectGit", "project_instance-git"),
    "/project/auto-commit": ("viewProjectAutoCommit", "project_instance-auto_commit"),
}


def test_views_defined_and_routed():
    """Each view function is declared and referenced by the router (>= 2x)."""
    for route, (view, _help_id) in NEW_ROUTES.items():
        assert f"async function {view}(" in HTML, f"{view} not defined"
        assert HTML.count(view) >= 2, f"{view} is not referenced by the router"


def test_routes_registered():
    for route, (view, _help_id) in NEW_ROUTES.items():
        pattern = re.compile(
            r'router\.register\(\s*["\']' + re.escape(route) + r'["\']\s*,\s*' + re.escape(view) + r'\s*\)'
        )
        assert pattern.search(HTML), f"router.register missing for {route} -> {view}"


def test_sidebar_nav_entries():
    for route in NEW_ROUTES:
        assert f'route: "{route}"' in HTML, f"sidebar entry missing for {route}"


def test_sections_saved_via_partial_update():
    for section in ("subagent_permissions", "git", "auto_commit"):
        assert f'saveProjectSection("{section}"' in HTML, f"{section} is not persisted via saveProjectSection"


def test_routemap_and_help_docs():
    for route, (_view, help_id) in NEW_ROUTES.items():
        route_key = route.lstrip("/")
        assert f'"{route_key}": "{help_id}"' in HTML, f"routeMap entry missing for {route_key}"
        assert f"<!-- help-id: {help_id} -->" in HELP_REF, f"help block missing for {help_id}"


def test_help_mappings_checker_reports_no_findings_for_new_routes():
    """The real consistency checker accepts the three new routeMap entries."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    try:
        from lib.consistency.docs import check_ui_help_mappings  # noqa: E402
    finally:
        sys.path.pop(0)

    findings = check_ui_help_mappings(REPO_ROOT)
    new_ids = {help_id for _view, help_id in NEW_ROUTES.values()}
    offenders = [f.message for f in findings if any(h in f.message for h in new_ids)]
    assert offenders == [], offenders


def test_auto_commit_client_gate_and_enums():
    # mode enum + default off
    for mode in ('"off"', '"suggest"', '"auto"', '"custom"'):
        assert mode in HTML
    # custom requires custom_script
    assert "requires a custom_script" in HTML
    # triggers enum
    for trigger in ("task-boundary", "per-edit", "context-pressure", "file-count-threshold"):
        assert trigger in HTML


def test_git_platform_enum_and_branch_prefixes():
    for platform in ("GitHub", "GitLab", "Gitea", "Codeberg"):
        assert platform in HTML
    # branch-prefix inputs share one generated id template (`git-prefix-<key>`) …
    assert "`git-prefix-${key}`" in HTML
    # … and feed the historic defaults into the `branch-prefixes` section.
    assert '"branch-prefixes"' in HTML
    for prefix in ('"feat/"', '"fix/"', '"chore/"'):
        assert prefix in HTML


def test_subagent_permissions_modes_and_precedence_help():
    assert '"provider-overrides"' in HTML
    for mode in ("strict", "warn", "off"):
        assert mode in HTML
    assert "provider override > project value > framework default" in HTML
