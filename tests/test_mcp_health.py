"""MCP health WARN checks (#1080 / D17).

``check_mcp_health`` reports, once per affected server and never as an error:

* ``mcp.secret-empty`` — a required secret is set neither non-empty in
  ``secrets.local.yaml`` nor in the environment,
* ``mcp.command-unresolved`` — a stdio server's command (after the python3
  interpreter fallback) does not resolve on ``PATH``.

Honcho is not an error: a missing optional memory server only warns.

Run: python3 -m pytest tests/test_mcp_health.py -v
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
import scripts.lib.mcp_health as mh
from scripts.lib.log import SyncLog

REG = {
    "reqo": {
        "connection": {"type": "sse", "url": "{{MCP_REQ_URL}}"},
        "secrets": ["MCP_REQ_URL", "MCP_REQ_KEY"],
    },
    "honcho": {
        "connection": {"type": "sse", "url": "{{MCP_HONCHO_URL}}"},
        "secrets": ["MCP_HONCHO_URL"],
    },
    "viz": {"connection": {"type": "stdio", "command": "python3"}, "secrets": []},
}


def _patch(monkeypatch, active, which="/bin/x"):
    monkeypatch.setattr(mh, "load_mcp_registry", lambda *a, **k: REG)
    monkeypatch.setattr(mh, "resolve_active_mcp_servers", lambda *a, **k: active)
    monkeypatch.setattr(mh.shutil, "which", lambda c: which)


def _secrets(tmp_path, text):
    p = tmp_path / ".meta-config" / "secrets.local.yaml"
    p.parent.mkdir(parents=True)
    p.write_text(text, encoding="utf-8")


def test_empty_secret_warns_once_per_server(tmp_path, monkeypatch):
    _patch(monkeypatch, ["reqo"])
    _secrets(tmp_path, 'MCP_REQ_URL: ""\nMCP_REQ_KEY: ""\n')
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert len(log.warnings) == 1
    assert (
        "mcp.secret-empty" in log.warnings[0]
        and "MCP_REQ_URL" in log.warnings[0]
        and "MCP_REQ_KEY" in log.warnings[0]
    )


def test_env_var_counts_as_set(tmp_path, monkeypatch):
    _patch(monkeypatch, ["reqo"])
    _secrets(tmp_path, 'MCP_REQ_URL: ""\nMCP_REQ_KEY: ""\n')
    log = SyncLog()
    mh.check_mcp_health(
        tmp_path, tmp_path, {}, log, env={"MCP_REQ_URL": "u", "MCP_REQ_KEY": "k"}
    )
    assert log.warnings == []


def test_filled_secret_no_warn(tmp_path, monkeypatch):
    _patch(monkeypatch, ["reqo"])
    _secrets(tmp_path, "MCP_REQ_URL: u\nMCP_REQ_KEY: k\n")
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert log.warnings == []


def test_inactive_server_not_checked(tmp_path, monkeypatch):
    _patch(monkeypatch, [])
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert log.warnings == []


def test_unresolved_command_warns(tmp_path, monkeypatch):
    _patch(monkeypatch, ["viz"], which=None)
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert len(log.warnings) == 1 and "mcp.command-unresolved" in log.warnings[0]


def test_honcho_missing_secret_is_warning_not_error(tmp_path, monkeypatch):
    _patch(monkeypatch, ["honcho"])
    _secrets(tmp_path, 'MCP_HONCHO_URL: ""\n')
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert log.errors == []
    assert len(log.warnings) == 1 and "mcp.secret-empty" in log.warnings[0]
