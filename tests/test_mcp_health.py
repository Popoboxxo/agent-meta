"""MCP health WARN checks (#1080 / D17).

``check_mcp_health`` reports, once per affected server and never as an error:

* ``mcp.secret-empty`` — a required secret is set neither non-empty in
  ``secrets.local.yaml`` nor in the environment,
* ``mcp.command-unresolved`` — a stdio server's command (after the python3
  interpreter fallback) does not resolve on ``PATH``.

Honcho is not an error: a missing optional memory server only warns.

Run: python3 -m pytest tests/test_mcp_health.py -v
"""
import socket
import sys
from pathlib import Path

import pytest

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


def test_malformed_connection_override_does_not_abort_the_check(tmp_path, monkeypatch):
    """A string ``connection`` override has no ``.get`` — the advisory check
    must skip it instead of raising AttributeError out of the sync (#1080)."""
    monkeypatch.setattr(
        mh, "load_mcp_registry", lambda *a, **k: {"broken": {"connection": "sse"}}
    )
    monkeypatch.setattr(mh, "resolve_active_mcp_servers", lambda *a, **k: ["broken"])
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert log.errors == []
    assert log.warnings == []


def test_non_dict_registry_entry_does_not_abort_the_check(tmp_path, monkeypatch):
    monkeypatch.setattr(mh, "load_mcp_registry", lambda *a, **k: {"broken": "sse"})
    monkeypatch.setattr(mh, "resolve_active_mcp_servers", lambda *a, **k: ["broken"])
    log = SyncLog()
    mh.check_mcp_health(tmp_path, tmp_path, {}, log, env={})
    assert log.errors == []
    assert log.warnings == []


# ---------------------------------------------------------------------------
# #1262 (C1): validate_mcp_health — structural URL/secret checks, no network
# ---------------------------------------------------------------------------

def _findings(tmp_path, registry, active, env=None, secrets_text=None):
    if secrets_text is not None:
        _secrets(tmp_path, secrets_text)
    return mh.validate_mcp_health(
        tmp_path, tmp_path, {}, env={} if env is None else env,
        registry=registry, active=active,
    )


def test_validate_invalid_url_is_error_with_server_name(tmp_path):
    registry = {
        "bad": {"connection": {"type": "sse", "url": "ftp://example.test/mcp"}}
    }
    findings = _findings(tmp_path, registry, ["bad"])
    assert len(findings) == 1
    server, severity, message = findings[0]
    assert server == "bad"
    assert severity == mh.SEVERITY_ERROR
    assert "bad" in message and "ftp" in message


def test_validate_url_without_scheme_is_error(tmp_path):
    registry = {"bad": {"connection": {"type": "sse", "url": "example.test/mcp"}}}
    findings = _findings(tmp_path, registry, ["bad"])
    assert [f[1] for f in findings] == [mh.SEVERITY_ERROR]
    assert "bad" in findings[0][2]


def test_validate_plaintext_secret_is_error_and_value_is_redacted(tmp_path):
    marker = "plain-test-marker"
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "https://api.test/mcp",
                "headers": {"Authorization": f"Bearer {marker}"},
            }
        }
    }
    findings = _findings(tmp_path, registry, ["api"])
    assert len(findings) == 1
    server, severity, message = findings[0]
    assert server == "api"
    assert severity == mh.SEVERITY_ERROR
    assert "Authorization" in message
    assert marker not in message


def test_validate_url_userinfo_is_plaintext_error_without_value(tmp_path):
    registry = {
        "api": {
            "connection": {
                "type": "sse", "url": "https://user:hunter2@api.test/mcp",
            }
        }
    }
    findings = _findings(tmp_path, registry, ["api"])
    assert [f[1] for f in findings] == [mh.SEVERITY_ERROR]
    assert "hunter2" not in findings[0][2]


def test_validate_valid_env_referenced_config_has_no_findings(tmp_path):
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "${MCP_API_URL}/mcp",
                "headers": {"Authorization": "Bearer ${MCP_API_TOKEN}"},
            }
        }
    }
    findings = _findings(
        tmp_path, registry, ["api"],
        env={"MCP_API_URL": "https://api.test", "MCP_API_TOKEN": "t"},
    )
    assert findings == []


def test_validate_template_placeholders_are_references(tmp_path):
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "{{MCP_API_URL}}/mcp",
                "headers": {"Authorization": "Bearer {{MCP_API_TOKEN}}"},
            }
        }
    }
    findings = _findings(
        tmp_path, registry, ["api"],
        env={"MCP_API_URL": "wss://api.test", "MCP_API_TOKEN": "t"},
    )
    assert findings == []


def test_validate_unset_env_var_is_warning_not_error(tmp_path):
    registry = {
        "api": {"connection": {"type": "sse", "url": "{{MCP_API_URL}}/mcp"}}
    }
    findings = _findings(tmp_path, registry, ["api"])
    assert len(findings) == 1
    server, severity, message = findings[0]
    assert server == "api"
    assert severity == mh.SEVERITY_WARNING
    assert "MCP_API_URL" in message


def test_validate_string_connection_override_is_skipped(tmp_path):
    findings = _findings(tmp_path, {"broken": {"connection": "sse"}}, ["broken"])
    assert findings == []


def test_validate_opens_no_network_socket(tmp_path, monkeypatch):
    def _boom(*args, **kwargs):
        raise AssertionError("network access attempted by validate_mcp_health")

    monkeypatch.setattr(socket, "socket", _boom)
    monkeypatch.setattr(socket, "create_connection", _boom)
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "https://api.test/mcp",
                "headers": {"Authorization": "Bearer ${MCP_API_TOKEN}"},
            }
        }
    }
    findings = _findings(tmp_path, registry, ["api"], env={"MCP_API_TOKEN": "t"})
    assert findings == []


# ---------------------------------------------------------------------------
# Env-reference forms: every supported syntax must resolve, never be read as a
# literal secret (#1262 review F1).
# ---------------------------------------------------------------------------

ENV_REF_FORMS = (
    "${env:MCP_API_TOKEN}",   # provider-native connector form
    "{env:MCP_API_TOKEN}",    # provider-native form without the leading ``$``
    "$MCP_API_TOKEN",         # plain shell form
    "${MCP_API_TOKEN}",       # shell / committed-config form
    "{{MCP_API_TOKEN}}",      # catalog template form
)


@pytest.mark.parametrize("ref", ENV_REF_FORMS)
def test_validate_env_ref_form_with_value_is_not_plaintext(tmp_path, ref):
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "https://api.test/mcp",
                "headers": {"Authorization": f"Bearer {ref}"},
            }
        }
    }
    findings = _findings(tmp_path, registry, ["api"], env={"MCP_API_TOKEN": "t"})
    assert findings == []


@pytest.mark.parametrize("ref", ENV_REF_FORMS)
def test_validate_env_ref_form_unset_is_warning_not_error(tmp_path, ref):
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "https://api.test/mcp",
                "headers": {"Authorization": f"Bearer {ref}"},
            }
        }
    }
    findings = _findings(tmp_path, registry, ["api"], env={})
    assert [f[1] for f in findings] == [mh.SEVERITY_WARNING]
    assert "MCP_API_TOKEN" in findings[0][2]
    assert "plaintext" not in findings[0][2]


@pytest.mark.parametrize("ref", ["${env:MCP_API_URL}", "{env:MCP_API_URL}", "$MCP_API_URL"])
def test_validate_url_env_ref_form_resolves(tmp_path, ref):
    registry = {"api": {"connection": {"type": "sse", "url": f"{ref}/mcp"}}}
    findings = _findings(tmp_path, registry, ["api"], env={"MCP_API_URL": "https://api.test"})
    assert findings == []


# ---------------------------------------------------------------------------
# Key classification: credential *endpoints* and non-secret look-alikes
# (#1262 review F2). Real credentials must stay flagged.
# ---------------------------------------------------------------------------

def test_validate_url_style_keys_are_not_plaintext_secrets(tmp_path):
    """``*_url``/``*_uri`` keys describe an endpoint, not a credential value."""
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "https://api.test/mcp",
                "headers": {
                    "authorization_url": "https://auth.test/authorize",
                    "token_url": "https://auth.test/token",
                    "token_uri": "https://auth.test/token",
                },
            }
        }
    }
    assert _findings(tmp_path, registry, ["api"]) == []


def test_validate_author_header_is_not_flagged(tmp_path):
    """``X-Author`` names a person, not an ``auth`` credential."""
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "https://api.test/mcp",
                "headers": {"X-Author": "Jane Doe"},
            }
        }
    }
    assert _findings(tmp_path, registry, ["api"]) == []


@pytest.mark.parametrize(
    "key", ["Authorization", "token", "api_key", "X-Api-Key", "password", "apiKey"]
)
def test_validate_real_credential_keys_stay_plaintext_errors(tmp_path, key):
    """The endpoint/word-boundary exemption must not loosen genuine slots."""
    registry = {
        "api": {
            "connection": {
                "type": "sse",
                "url": "https://api.test/mcp",
                "headers": {key: "literal-secret-value"},
            }
        }
    }
    findings = _findings(tmp_path, registry, ["api"])
    assert [f[1] for f in findings] == [mh.SEVERITY_ERROR]
    assert key in findings[0][2]
    assert "literal-secret-value" not in findings[0][2]

