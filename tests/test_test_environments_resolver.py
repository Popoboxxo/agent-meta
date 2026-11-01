"""Resolver and platform fallback for ``test-environments`` (Task 5).

Covers the default resolution (AC-ENV-3) and the URL fallback precedence
``platform.hacs.dev_instance_url`` > ``platform.homeassistant.ha_url``
(AC-ENV-4, spec §10.2). The resolver never raises and never exits: broken
input yields ``{}`` plus a warning.

Run: ``python3 -m pytest tests/test_test_environments_resolver.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib.test_environments import (  # noqa: E402
    load_project_platform_vars,
    resolve_test_environments,
)

HACS, HA = "platform.hacs.dev_instance_url", "platform.homeassistant.ha_url"


def _cfg(envs, **extra):
    return {"test-environments": envs, **extra}


def test_defaults_resolve():  # AC-ENV-3
    assert resolve_test_environments(_cfg({"a": {}}), {})["a"] == {
        "kind": "local",
        "url": None,
        "url_source": "",
        "token-env": None,
        "access": "read",
        "remote-access": "ask",
        "notes": "",
    }


def test_invalid_or_odd_input_yields_empty_and_never_raises():
    assert resolve_test_environments(_cfg({"a": {"kind": "x"}}), {}) == {}
    assert resolve_test_environments({"test-environments": ["x"]}, {}) == {}
    assert resolve_test_environments({}, None) == {}


def test_fallback_prefers_hacs_over_ha():  # AC-ENV-4
    r = resolve_test_environments(
        _cfg({"ha": {"kind": "remote"}}),
        {HACS: "http://dev:8123", HA: "http://ha:8123"},
    )
    assert (r["ha"]["url"], r["ha"]["url_source"]) == ("http://dev:8123", HACS)


def test_fallback_ha_only():
    r = resolve_test_environments(_cfg({"ha": {"kind": "both"}}), {HA: "http://ha:8123"})
    assert (r["ha"]["url"], r["ha"]["url_source"]) == ("http://ha:8123", HA)


def test_explicit_url_wins():
    r = resolve_test_environments(
        _cfg({"ha": {"kind": "remote", "url": "http://own"}}), {HACS: "http://dev:8123"}
    )
    assert (r["ha"]["url"], r["ha"]["url_source"]) == ("http://own", "config")


def test_platform_default_alone_triggers_nothing():
    # Defaults are never part of the project-layer variables.
    r = resolve_test_environments(_cfg({"ha": {"kind": "remote"}}), {})
    assert (r["ha"]["url"], r["ha"]["url_source"]) == (None, "")


def test_empty_platform_value_is_ignored():
    assert (
        resolve_test_environments(_cfg({"ha": {"kind": "remote"}}), {HACS: ""})["ha"]["url"]
        is None
    )


def test_two_urlless_remote_envs_get_no_fallback():
    r = resolve_test_environments(
        _cfg({"a": {"kind": "remote"}, "b": {"kind": "both"}}), {HACS: "http://dev:8123"}
    )
    assert r["a"]["url"] is None and r["b"]["url"] is None


def test_local_env_does_not_count_and_gets_no_fallback():
    r = resolve_test_environments(
        _cfg({"loc": {}, "ha": {"kind": "remote"}}), {HACS: "http://dev:8123"}
    )
    assert r["loc"]["url"] is None and r["ha"]["url"] == "http://dev:8123"


def test_load_project_platform_vars_reads_only_project_layer(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "platform-config.yaml").write_text(
        "platform:\n  hacs:\n    dev_instance_url: http://dev:8123\n"
        "  homeassistant:\n    notify_group: all\n",
        encoding="utf-8",
    )
    assert load_project_platform_vars(tmp_path) == {
        HACS: "http://dev:8123",
        "platform.homeassistant.notify_group": "all",
    }


def test_load_project_platform_vars_missing_or_broken_file(tmp_path):
    assert load_project_platform_vars(tmp_path) == {}
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "platform-config.yaml").write_text(
        "platform: [unclosed", encoding="utf-8"
    )
    assert load_project_platform_vars(tmp_path) == {}
