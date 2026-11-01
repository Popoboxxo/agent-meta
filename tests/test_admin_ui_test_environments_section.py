"""Server-side tests for the ``test-environments`` Admin-API section (RF5).

The UI part of this module is added in Task 11 of
``docs/plans/2026-10-31-test-environments-plan.md``.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")
HELP_REF = (REPO_ROOT / "docs" / "api" / "admin-ui-reference.md").read_text(
    encoding="utf-8"
)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _te_admin_helpers import _handler, _post, admin_server  # noqa: E402

ENVS = {"HA_DEV_TOKEN": {"description": "t", "secret": True}}
VALID = {
    "ha-dev": {
        "kind": "remote",
        "url": "http://ha-dev.lan:8123",
        "token-env": "HA_DEV_TOKEN",
        "access": "read",
        "remote-access": "ask",
    }
}


def test_whitelist_contains_section():  # AC-ENV-12
    assert "test-environments" in admin_server.PROJECT_WRITABLE_SECTIONS


def test_valid_payload_round_trips(tmp_path):
    h = _handler(tmp_path)
    h.config_manager.write("project", {"environments": ENVS})
    _post(h, "test-environments", VALID)
    assert h.config_manager.read("project")["test-environments"] == VALID


@pytest.mark.parametrize(
    "bad,needle",
    [
        ({"a": {"kind": "remoteish"}}, "kind"),
        ({"a": {"kind": True}}, "quote the value"),
        ({"a": {"colour": "x"}}, "unknown key"),
        ({"a": {"url": "http://u:p@h"}}, "userinfo"),
        ({"a": {"token-env": "HA_DEV_TOKEN"}}, "not defined"),
    ],
)
def test_invalid_payload_rejected_nothing_written(tmp_path, bad, needle):
    h = _handler(tmp_path)
    h.config_manager.write("project", {"git": {"keep": 1}})
    with pytest.raises(ValueError) as exc:
        _post(h, "test-environments", bad)
    assert needle in str(exc.value) and h.config_manager.read("project") == {
        "git": {"keep": 1}
    }


def test_token_env_with_non_secret_entry_rejected(tmp_path):
    h = _handler(tmp_path)
    h.config_manager.write(
        "project",
        {"environments": {"HA_DEV_TOKEN": {"description": "t", "secret": False}}},
    )
    with pytest.raises(ValueError, match="secret: true"):
        _post(h, "test-environments", VALID)


def test_null_deletes_section_without_error(tmp_path):  # RF5
    h = _handler(tmp_path)
    h.config_manager.write(
        "project", {"environments": ENVS, "test-environments": VALID}
    )
    _post(h, "test-environments", None)
    assert h.config_manager.read("project").get("test-environments") is None


def test_environments_write_breaking_reference_rejected(tmp_path):  # RF5
    h = _handler(tmp_path)
    h.config_manager.write(
        "project", {"environments": ENVS, "test-environments": VALID}
    )
    with pytest.raises(
        ValueError, match="environments entry 'HA_DEV_TOKEN' not defined"
    ):
        _post(h, "environments", {})
    assert h.config_manager.read("project")["environments"] == ENVS


def test_environments_write_unrelated_variable_ok(tmp_path):
    h = _handler(tmp_path)
    h.config_manager.write(
        "project", {"environments": ENVS, "test-environments": VALID}
    )
    _post(h, "environments", {**ENVS, "OTHER": {"description": "x"}})


def test_full_document_put_guarded(tmp_path):  # RF5
    h = _handler(tmp_path)
    h.config_manager.write("project", {"git": {"keep": 1}})
    h._read_body = lambda: {"test-environments": {"a": {"kind": "x"}}}
    with pytest.raises(ValueError):
        h._route_put_config("project")
    assert h.config_manager.read("project") == {"git": {"keep": 1}}


def test_unrelated_section_not_blocked_by_preexisting_invalid_config(tmp_path):  # RF5
    h = _handler(tmp_path)
    h.config_manager.write("project", {"test-environments": {"a": {"kind": "x"}}})
    _post(h, "git", {"auto_commit": False})


# --------------------------------------------------------------------------- #
# UI part (Task 11)                                                           #
# --------------------------------------------------------------------------- #


def _view_body() -> str:
    """Return the body of ``viewProjectTestEnvironments`` up to the next view."""
    return HTML.split("async function viewProjectTestEnvironments(", 1)[1].split(
        "\nasync function ", 1
    )[0]


def test_view_defined_routed_and_in_nav():  # AC-ENV-12
    assert "async function viewProjectTestEnvironments(" in HTML
    assert re.search(
        r'router\.register\(\s*"/project/test-environments"\s*,\s*'
        r"viewProjectTestEnvironments\s*\)",
        HTML,
    )
    assert 'route: "/project/test-environments"' in HTML


def test_saved_via_partial_update_with_string_enums():
    body = _view_body()
    assert 'saveProjectSection("test-environments"' in body
    for enum in (
        '["local", "remote", "both"]',
        '["read", "deploy"]',
        '["deny", "ask", "allow"]',
    ):
        assert enum in body


def test_no_secret_value_input():  # Z7, AZ2
    body = _view_body()
    assert not re.search(r'type:\s*"password"', body)
    assert "TOKEN_ENV_RE" in body and "^[A-Z][A-Z0-9_]*$" in body
    assert "nie hier eintragen" in body


def test_remote_activation_requires_confirmation():
    assert "confirmDestructive(" in _view_body()


def test_cross_hints_between_environments_views():  # AC-ENV-17
    assert "Environment Variables" in _view_body() and "secret" in _view_body().lower()
    env_view = HTML.split("async function viewProjectEnvironments(", 1)[1].split(
        "\nasync function ", 1
    )[0]
    assert "Test Environments" in env_view


def test_routemap_and_help_block_and_checker():
    assert '"project/test-environments": "project_instance-test_environments"' in HTML
    assert "<!-- help-id: project_instance-test_environments -->" in HELP_REF
    from lib.consistency.docs import check_ui_help_mappings

    assert [
        f.message
        for f in check_ui_help_mappings(REPO_ROOT)
        if "test_environments" in f.message
    ] == []
