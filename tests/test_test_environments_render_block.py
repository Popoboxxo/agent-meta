"""Renderer for the ``{{TEST_ENVIRONMENT_BLOCK}}`` (Task 6).

The block is role-agnostic Markdown (b12/C2): a table over all resolved
environments plus the rules from spec §10.1/§10.4. The remote approval protocol
(``APPROVAL_REQUEST``/``APPROVED``) is rendered only when at least one
environment is ``kind: remote|both``; table cells are sanitised (RF4).

Run: ``python3 -m pytest tests/test_test_environments_render_block.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib.test_environments import render_test_environment_block  # noqa: E402

HA_ENV = {
    "ha-dev": {
        "kind": "both",
        "url": "http://ha-dev.lan:8123",
        "url_source": "config",
        "token-env": "HA_DEV_TOKEN",
        "access": "deploy",
        "remote-access": "ask",
        "notes": "Integration erst lokal testen.",
    }
}
LOCAL_ENV = {
    "sharkord-local": {
        "kind": "local",
        "url": None,
        "url_source": "",
        "token-env": None,
        "access": "read",
        "remote-access": "ask",
        "notes": "docker compose run --rm test",
    }
}


def _with(env, **over):
    return {k: {**v, **over} for k, v in env.items()}


def test_empty_returns_empty_string():
    assert render_test_environment_block({}) == ""


def test_table_lists_all_environments_sorted():
    out = render_test_environment_block({**LOCAL_ENV, **HA_ENV})
    assert out.startswith("## Test environments")
    assert "| Name | kind | URL / source | access | remote-access | notes |" in out
    assert (
        "| ha-dev | both | http://ha-dev.lan:8123 | deploy | ask "
        "| Integration erst lokal testen. |" in out
    )
    assert "| sharkord-local | local | — | — | — | docker compose run --rm test |" in out
    assert out.index("| ha-dev |") < out.index("| sharkord-local |")


def test_ask_protocol_texts():  # AC-ENV-8, AC-ENV-20
    out = render_test_environment_block(HA_ENV)
    for s in (
        "stop BEFORE the first remote access",
        "STATUS: partial",
        "APPROVAL_REQUEST: env=<name>; action=<read|deploy: action>",
        "APPROVED: env=<name>; action=<action>",
        "applies only to the named environment and action",
        "Record the approval in your report",
    ):
        assert s in out


def test_both_requires_local_first():
    assert (
        "test locally first, then the remote environment only after approval"
        in render_test_environment_block(HA_ENV)
    )


def test_deny_text():  # AC-ENV-20
    out = render_test_environment_block(_with(HA_ENV, **{"remote-access": "deny"}))
    assert "never contact the environment" in out and "report it to main_chat" in out
    assert "APPROVAL_REQUEST: env=" not in out


def test_allow_text():  # AC-ENV-20
    out = render_test_environment_block(_with(HA_ENV, **{"remote-access": "allow"}))
    assert "report every deploy" in out and "APPROVAL_REQUEST: env=" not in out


def test_protocol_texts_absent_for_local_only():
    out = render_test_environment_block(LOCAL_ENV)
    assert "APPROVAL_REQUEST: env=" not in out and "never contact" not in out
    assert (
        "Access approval is a prompt convention (convention boundary), "
        "not a technical barrier." in out
    )


def test_secret_hint_names_only_the_name():  # AC-ENV-6
    out = render_test_environment_block(HA_ENV)
    for s in (
        "`${HA_DEV_TOKEN}`",
        "source .meta-config/env.sh",
        "Never print, log or write the value",
        "`secret: true`",
    ):
        assert s in out


def test_missing_url_marker_and_target_rule():  # AC-ENV-4
    out = render_test_environment_block(_with(HA_ENV, url=None, url_source=""))
    assert "URL not configured" in out and "APPROVAL_REQUEST: target?" in out


def test_fallback_url_shows_source():
    out = render_test_environment_block(
        _with(HA_ENV, url="http://dev:8123", url_source="platform.hacs.dev_instance_url")
    )
    assert "http://dev:8123 (from platform.hacs.dev_instance_url)" in out


def test_unclear_target_rule_only_when_needed():
    assert "APPROVAL_REQUEST: target?" in render_test_environment_block(
        {**LOCAL_ENV, **HA_ENV}
    )
    assert "APPROVAL_REQUEST: target?" not in render_test_environment_block(LOCAL_ENV)


def test_cells_are_sanitized():  # RF4
    out = render_test_environment_block(_with(LOCAL_ENV, notes="a|b\nc"))
    assert "| a\\|b c |" in out


def test_deploy_rule_mentions_deny_wins():
    assert "deny always wins" in render_test_environment_block(HA_ENV)


def test_render_is_deterministic_without_trailing_newline():
    a = render_test_environment_block({**LOCAL_ENV, **HA_ENV})
    assert a == render_test_environment_block({**HA_ENV, **LOCAL_ENV})
    assert not a.endswith("\n")


def test_namensabgrenzung_sentence():  # AC-ENV-17
    assert (
        "`environments:` defines environment variables"
        in render_test_environment_block(LOCAL_ENV)
    )
