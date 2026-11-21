"""Issue #1263: enforce the MCP catalog's blocked-tool list as permission deny.

The guardrail in ``rules/1-generic/mcp-guardrails.md`` is prompt convention
only. This module pins the provider-agnostic half of the fix: every ``blocked``
tool of an ACTIVE catalog server is rendered as a ``mcp__<server>__<tool>``
permission deny entry, merged into the provider's settings file without
dropping user entries (managed-state namespace). Providers without the declared
capability keep the prompt convention (no silent format guessing).

Run: python3 -m pytest tests/test_mcp_deny.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.mcp_deny import (  # noqa: E402
    MCP_DENY_CAPABILITY,
    MCP_DENY_STATE_KEY,
    build_mcp_deny_rules,
    sync_mcp_deny,
    validate_mcp_deny,
)

_REGISTRY = {
    "alpha": {"tools": {"allowed": ["read"], "blocked": ["delete", "admin.restore"]}},
    "beta": {"tools": {"blocked": ["drop"]}},
    "quiet": {"tools": {"blocked": []}},
}

_PROVIDER_CONFIG = {
    "Claude": {
        "settings_file": ".claude/settings.json",
        "isolation-mechanism": "claude-settings-deny",
    },
    "Opencode": {
        "settings_file": "opencode.json",
        "isolation-mechanism": "opencode-permissions",
    },
}

_CAPABILITIES = {
    "Claude": {MCP_DENY_CAPABILITY: True},
    "Opencode": {MCP_DENY_CAPABILITY: False},
}


def _settings(tmp_path: Path) -> Path:
    path = tmp_path / ".claude" / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# --- pure rule generation --------------------------------------------------


def test_build_mcp_deny_rules_is_sorted_and_scoped_to_active_servers():
    assert build_mcp_deny_rules(_REGISTRY, ["beta", "alpha", "quiet", "missing"]) == [
        "mcp__alpha__admin.restore",
        "mcp__alpha__delete",
        "mcp__beta__drop",
    ]


def test_build_mcp_deny_rules_empty_without_blocked_tools():
    assert build_mcp_deny_rules(_REGISTRY, ["quiet"]) == []
    assert build_mcp_deny_rules({}, []) == []


# --- merge into the provider settings --------------------------------------


def test_sync_mcp_deny_merges_with_user_entries(tmp_path):
    settings = _settings(tmp_path)
    settings.write_text(
        json.dumps({"permissions": {"allow": [], "deny": ["Bash(rm -rf:*)"]}}),
        encoding="utf-8",
    )
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha", "beta"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    deny = _read_json(settings)["permissions"]["deny"]
    assert "Bash(rm -rf:*)" in deny
    for rule in build_mcp_deny_rules(_REGISTRY, ["alpha", "beta"]):
        assert rule in deny


def test_sync_mcp_deny_records_managed_rules_in_state(tmp_path):
    _settings(tmp_path).write_text(json.dumps({"permissions": {"deny": []}}), encoding="utf-8")
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    state = _read_json(tmp_path / ".claude" / "agent-meta-state.json")
    assert state[MCP_DENY_STATE_KEY] == ["mcp__alpha__admin.restore", "mcp__alpha__delete"]


def test_sync_mcp_deny_removes_stale_managed_rules_only(tmp_path):
    settings = _settings(tmp_path)
    settings.write_text(json.dumps({"permissions": {"deny": []}}), encoding="utf-8")
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha", "beta"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["beta"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    deny = _read_json(settings)["permissions"]["deny"]
    assert "mcp__beta__drop" in deny
    assert "mcp__alpha__delete" not in deny
    assert "mcp__alpha__admin.restore" not in deny


def test_sync_mcp_deny_skips_provider_without_capability(tmp_path):
    settings = _settings(tmp_path)
    original = json.dumps({"permissions": {"deny": ["Bash(rm -rf:*)"]}})
    settings.write_text(original, encoding="utf-8")
    sync_mcp_deny(
        tmp_path, "Opencode", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    assert settings.read_text(encoding="utf-8") == original
    assert not (tmp_path / ".claude" / "agent-meta-state.json").exists()


def test_sync_mcp_deny_dry_run_writes_nothing(tmp_path):
    settings = _settings(tmp_path)
    original = json.dumps({"permissions": {"deny": []}})
    settings.write_text(original, encoding="utf-8")
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), True, capabilities=_CAPABILITIES,
    )
    assert settings.read_text(encoding="utf-8") == original
    assert not (tmp_path / ".claude" / "agent-meta-state.json").exists()


def test_sync_mcp_deny_does_not_create_a_state_file_without_rules(tmp_path):
    """No active MCP server → no deny rules → no spurious state artifact.

    An empty companion file would be reported as a foreign injection by the
    external-tools drift scanner and break the AC-01 render identity.
    """
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, [],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    assert not (tmp_path / ".claude" / "agent-meta-state.json").exists()


def test_sync_mcp_deny_tolerates_missing_settings_file(tmp_path):
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    deny = _read_json(_settings(tmp_path))["permissions"]["deny"]
    assert "mcp__alpha__delete" in deny


def test_sync_mcp_deny_keeps_unparseable_settings_file(tmp_path):
    settings = _settings(tmp_path)
    original = "{not json"
    settings.write_text(original, encoding="utf-8")
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    assert settings.read_text(encoding="utf-8") == original


# --- --validate coverage ---------------------------------------------------


def test_validate_mcp_deny_flags_missing_rules(tmp_path):
    findings = validate_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        capabilities=_CAPABILITIES,
    )
    assert any("mcp__alpha__delete" in message for message in findings)


def test_validate_mcp_deny_clean_after_sync(tmp_path):
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    assert validate_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        capabilities=_CAPABILITIES,
    ) == []


def test_validate_mcp_deny_silent_for_unsupported_provider(tmp_path):
    assert validate_mcp_deny(
        tmp_path, "Opencode", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        capabilities=_CAPABILITIES,
    ) == []
