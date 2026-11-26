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
        # Real Claude config: hooks are mirrored, so a stale hook fallback
        # manifest can exist and must be cleaned up when the native capability
        # applies.
        "hooks_dir": ".claude/hooks",
        "has_hooks": True,
        "hook_protocol": "claude-code-json",
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
    # No hook capability either: no manifest fallback is materialised.
    assert not (tmp_path / ".claude" / "hooks" / "lib" / "mcp-deny.json").exists()


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


def test_sync_mcp_deny_writes_exactly_the_blocked_tools(tmp_path):
    """AC-1 (exactness): the machine list is the blocked list — no more, no less."""
    settings = _settings(tmp_path)
    settings.write_text(
        json.dumps({"permissions": {"deny": ["Bash(rm -rf:*)"]}}), encoding="utf-8",
    )
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha", "beta", "quiet"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    deny = _read_json(settings)["permissions"]["deny"]
    assert {entry for entry in deny if entry.startswith("mcp__")} == set(
        build_mcp_deny_rules(_REGISTRY, ["alpha", "beta", "quiet"])
    )
    assert deny[0] == "Bash(rm -rf:*)"


def test_sync_mcp_deny_does_not_create_a_settings_file_without_rules(tmp_path):
    """Empty deny list → no entry, and no spurious settings artifact.

    Mirrors the empty-companion-state-file guard: a freshly created
    ``{"permissions": {"deny": []}}`` file would be a foreign injection for the
    drift scanner even though nothing is prohibited.
    """
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["quiet"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    assert not (tmp_path / ".claude" / "settings.json").exists()
    assert not (tmp_path / ".claude" / "agent-meta-state.json").exists()


def test_sync_mcp_deny_keeps_unparseable_settings_file(tmp_path):
    settings = _settings(tmp_path)
    original = "{not json"
    settings.write_text(original, encoding="utf-8")
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    assert settings.read_text(encoding="utf-8") == original


# --- hook fallback manifest (issue #1263b) --------------------------------
#
# Providers WITHOUT the native permission-deny capability get the same rules as
# a manifest next to the deployed hook lib, where hook_common.sh reads them
# (hook_mcp_tool_denied). Same source, different transport — never a second
# deny list.

_HOOK_PROVIDER = "HookOnly"
_HOOK_PROVIDER_CONFIG = {
    _HOOK_PROVIDER: {
        "hooks_dir": ".hookonly/hooks",
        "has_hooks": True,
        "hook_protocol": "claude-code-json",
    },
}
_HOOK_CAPABILITIES = {_HOOK_PROVIDER: {MCP_DENY_CAPABILITY: False}}


def _hook_manifest(tmp_path: Path) -> Path:
    return tmp_path / ".hookonly" / "hooks" / "lib" / "mcp-deny.json"


def _sync_hook_provider(tmp_path: Path, active: list[str], dry_run: bool = False) -> None:
    sync_mcp_deny(
        tmp_path, _HOOK_PROVIDER, _HOOK_PROVIDER_CONFIG, _REGISTRY, active,
        SyncLog(), dry_run, capabilities=_HOOK_CAPABILITIES,
    )


def test_sync_mcp_deny_writes_hook_manifest_without_capability(tmp_path):
    """AC-1: the hook manifest carries exactly the same rules as the native list."""
    _sync_hook_provider(tmp_path, ["alpha", "beta"])
    manifest = _read_json(_hook_manifest(tmp_path))
    assert manifest["rules"] == build_mcp_deny_rules(_REGISTRY, ["alpha", "beta"])
    assert manifest["rules"] == [
        "mcp__alpha__admin.restore",
        "mcp__alpha__delete",
        "mcp__beta__drop",
    ]


def test_sync_mcp_deny_hook_manifest_is_agent_meta_managed(tmp_path):
    """Provenance marker: sync may later remove/replace only its own file."""
    _sync_hook_provider(tmp_path, ["alpha"])
    manifest = _read_json(_hook_manifest(tmp_path))
    assert manifest["_agent-meta"] == (
        "agent-meta managed — do not edit manually"
    )


def test_sync_mcp_deny_hook_manifest_not_written_with_capability(tmp_path):
    """Capability providers keep the native surface; no duplicate hook copy."""
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    assert not (tmp_path / ".claude" / "hooks" / "lib" / "mcp-deny.json").exists()
    assert _read_json(_settings(tmp_path))["permissions"]["deny"]


def test_sync_mcp_deny_hook_manifest_absent_without_blocked_tools(tmp_path):
    _sync_hook_provider(tmp_path, ["quiet"])
    assert not _hook_manifest(tmp_path).exists()


def test_sync_mcp_deny_hook_manifest_removes_stale_managed_rules(tmp_path):
    _sync_hook_provider(tmp_path, ["alpha", "beta"])
    _sync_hook_provider(tmp_path, ["beta"])
    assert _read_json(_hook_manifest(tmp_path))["rules"] == ["mcp__beta__drop"]


def test_sync_mcp_deny_hook_manifest_removed_when_list_becomes_empty(tmp_path):
    _sync_hook_provider(tmp_path, ["alpha"])
    assert _hook_manifest(tmp_path).exists()
    _sync_hook_provider(tmp_path, ["quiet"])
    assert not _hook_manifest(tmp_path).exists()


def test_sync_mcp_deny_hook_manifest_dry_run_writes_nothing(tmp_path):
    _sync_hook_provider(tmp_path, ["alpha"], dry_run=True)
    assert not _hook_manifest(tmp_path).exists()


def test_sync_mcp_deny_keeps_unparseable_hook_manifest(tmp_path):
    manifest = _hook_manifest(tmp_path)
    manifest.parent.mkdir(parents=True)
    manifest.write_text("{not json", encoding="utf-8")
    _sync_hook_provider(tmp_path, ["alpha"])
    assert manifest.read_text(encoding="utf-8") == "{not json"


def test_sync_mcp_deny_native_capability_drops_managed_hook_manifest(tmp_path):
    """A provider that gains the capability must not keep the hook fallback."""
    manifest = tmp_path / ".claude" / "hooks" / "lib" / "mcp-deny.json"
    manifest.parent.mkdir(parents=True)
    manifest.write_text(
        json.dumps({
            "_agent-meta": "agent-meta managed — do not edit manually",
            "rules": ["mcp__alpha__delete"],
        }),
        encoding="utf-8",
    )
    sync_mcp_deny(
        tmp_path, "Claude", _PROVIDER_CONFIG, _REGISTRY, ["alpha"],
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    assert not manifest.exists()


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
