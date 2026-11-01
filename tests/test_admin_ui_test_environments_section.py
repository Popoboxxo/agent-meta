"""Server-side tests for the ``test-environments`` Admin-API section (RF5).

The UI part of this module is added in Task 11 of
``docs/plans/2026-10-31-test-environments-plan.md``.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

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
