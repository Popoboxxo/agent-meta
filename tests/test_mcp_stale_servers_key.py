"""Tests for lib.mcp_provider_config._warn_stale_mcp_servers_key (#719):
a leftover `mcpServers` key from before the #388/#400 migration to .mcp.json
must be detected and warned about -- never auto-removed, for the secret and
non-secret case alike -- and a literal secret found inside it must escalate
the log message to [SECURITY] instead of a plain cleanup hint."""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog
from lib.mcp_provider_config import _warn_stale_mcp_servers_key

_PROVIDER_CFG = {
    "settings_file": ".claude/settings.json",
    "settings_local_file": ".claude/settings.local.json",
}


def _write_settings(project_root: Path, data: dict) -> Path:
    p = project_root / ".claude" / "settings.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


def test_stale_key_without_secret_is_warned_but_not_removed(tmp_path):
    original_data = {
        "mcpServers": {"honcho": {"command": "npx", "args": ["honcho-mcp"]}},
        "permissions": {"allow": []},
    }
    settings = _write_settings(tmp_path, original_data)
    log = SyncLog()

    _warn_stale_mcp_servers_key(tmp_path, _PROVIDER_CFG, ".mcp.json", None, log, dry_run=False)

    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data == original_data  # never removed, only flagged
    assert any("mcpServers" in w for w in log.warnings)


def test_stale_key_with_literal_bearer_token_escalates_severity(tmp_path):
    original_data = {
        "mcpServers": {"honcho": {"headers": {"Authorization": "Bearer sk-live-abc123XYZ789secret"}}},
    }
    settings = _write_settings(tmp_path, original_data)
    log = SyncLog()

    _warn_stale_mcp_servers_key(tmp_path, _PROVIDER_CFG, ".mcp.json", None, log, dry_run=False)

    data = json.loads(settings.read_text(encoding="utf-8"))
    assert data == original_data  # never removed, even for a detected secret
    assert any("[SECURITY]" in w for w in log.warnings)


def test_bearer_env_placeholder_is_not_treated_as_a_secret(tmp_path):
    _write_settings(tmp_path, {
        "mcpServers": {"honcho": {"headers": {"Authorization": "Bearer ${HONCHO_TOKEN}"}}},
    })
    log = SyncLog()

    _warn_stale_mcp_servers_key(tmp_path, _PROVIDER_CFG, ".mcp.json", None, log, dry_run=False)

    assert not any("[SECURITY]" in w for w in log.warnings)
    assert any("mcpServers" in w for w in log.warnings)  # still flagged, not removed


def test_file_is_never_touched_regardless_of_dry_run(tmp_path):
    settings = _write_settings(tmp_path, {"mcpServers": {"honcho": {}}})
    original = settings.read_text(encoding="utf-8")
    log = SyncLog()

    for dry_run in (True, False):
        _warn_stale_mcp_servers_key(tmp_path, _PROVIDER_CFG, ".mcp.json", None, log, dry_run=dry_run)
        assert settings.read_text(encoding="utf-8") == original

    assert any("mcpServers" in w for w in log.warnings)


def test_no_stale_key_produces_no_warning(tmp_path):
    _write_settings(tmp_path, {"permissions": {"allow": []}})
    log = SyncLog()

    _warn_stale_mcp_servers_key(tmp_path, _PROVIDER_CFG, ".mcp.json", None, log, dry_run=False)

    assert log.warnings == []
