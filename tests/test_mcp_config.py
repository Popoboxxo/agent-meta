"""Regression tests for MCP provider config generation (scripts/lib/mcp.py).

Covers audit findings #388/#400: Claude Code does not read a top-level
`mcpServers` key from settings.json/settings.local.json — only from
.mcp.json at the project root. Writing there previously produced a fully
inert, silently-broken MCP integration.
"""

import json
from pathlib import Path

import yaml

from scripts.lib.log import SyncLog
from scripts.lib.mcp import _update_json_config, build_mcp_guardrails_list, generate_provider_configs
from scripts.lib.providers import load_providers_config


def test_claude_mcp_config_targets_mcp_json_not_settings():
    # Regression test for #388/#400: the real config/ai-providers.yaml must
    # point Claude's mcp-config at .mcp.json, not at settings.json/
    # settings.local.json (which Claude Code never reads mcpServers from).
    repo_root = Path(__file__).resolve().parents[1]
    provider_config = load_providers_config(repo_root)
    mcp_cfg = provider_config["Claude"]["mcp-config"]
    assert mcp_cfg["committed-file"] == ".mcp.json"
    assert mcp_cfg["secrets-file"] == ".mcp.json"
    assert ".mcp.json" in provider_config["Claude"]["gitignore_entries"]


def test_every_provider_secrets_file_is_gitignored():
    # Regression test found live in a follow-up system audit (2026-08-07):
    # Continue's mcp-config.secrets-file was `.continue/config.local.yaml`,
    # but gitignore_entries listed `.continue/settings.local.yaml` -- a
    # filename that matched nothing, so the real secrets file was never
    # gitignored. Opencode had the same class of gap: its secrets-file
    # (`.opencode/mcp.local.json`) is a *third*, distinct path from
    # settings_local_file and was missing from gitignore_entries entirely.
    # Both are the same severity as #388/#400 (secrets ending up somewhere
    # unprotected) -- generalized here so it can't silently regress again
    # for any provider, present or future.
    repo_root = Path(__file__).resolve().parents[1]
    provider_config = load_providers_config(repo_root)
    missing = []
    for name, pc in provider_config.items():
        secrets_file = pc.get("mcp-config", {}).get("secrets-file")
        settings_local = pc.get("settings_local_file")
        entries = set(pc.get("gitignore_entries", []))
        for path in (secrets_file, settings_local):
            if path and path not in entries:
                missing.append(f"{name}: {path!r} not in gitignore_entries")
    assert not missing, "\n".join(missing)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_generate_provider_configs_writes_resolved_secrets_to_mcp_json(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"

    _write(
        agent_meta_root / "config" / "mcp-registry.yaml",
        yaml.dump({
            "mcp-servers": {
                "example-server": {
                    "description": "test server",
                    "connection": {
                        "type": "sse",
                        "url": "{{EXAMPLE_URL}}",
                        "headers": {"Authorization": "Bearer {{EXAMPLE_TOKEN}}"},
                    },
                }
            }
        }),
    )
    _write(
        project_root / ".meta-config" / "secrets.local.yaml",
        yaml.dump({"EXAMPLE_URL": "https://real.example.com", "EXAMPLE_TOKEN": "sk-real-secret"}),
    )

    config = {"mcp-servers": ["example-server"], "platforms": []}
    provider_config = {
        "Claude": {
            "mcp-config": {
                "committed-file": ".mcp.json",
                "secrets-file": ".mcp.json",
                "format": "claude-settings",
            }
        }
    }
    log = SyncLog()

    generate_provider_configs(
        agent_meta_root, project_root, config, provider_config, log,
        dry_run=False, provider="Claude",
    )

    mcp_json_path = project_root / ".mcp.json"
    assert mcp_json_path.exists()
    written = json.loads(mcp_json_path.read_text(encoding="utf-8"))
    assert "example-server" in written["mcpServers"]
    entry = written["mcpServers"]["example-server"]
    # Real, resolved secret values — not the {{VAR}}/${VAR} placeholder form.
    assert entry["url"] == "https://real.example.com"
    assert entry["headers"]["Authorization"] == "Bearer sk-real-secret"

    # Must NOT have leaked mcpServers into settings.json/settings.local.json —
    # those files should not even exist, since nothing else in this test
    # writes them and generate_provider_configs() only touches the
    # configured committed-file/secrets-file paths.
    assert not (project_root / ".claude" / "settings.json").exists()
    assert not (project_root / ".claude" / "settings.local.json").exists()


def test_update_json_config_self_heals_empty_file(tmp_path):
    # Regression test for #400 Secondary Finding A: a zero-byte existing
    # file must not be treated as an unparseable conflict that silently
    # skips MCP injection.
    path = tmp_path / ".mcp.json"
    path.write_text("", encoding="utf-8")
    log = SyncLog()

    _update_json_config(path, "mcpServers", {"foo": {"type": "sse", "url": "https://x"}}, log, dry_run=False, allow_secrets=True)

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["mcpServers"]["foo"]["url"] == "https://x"


def test_generate_provider_configs_warns_about_leftover_mcp_servers_key(tmp_path):
    # Migration aid for #388/#400: a project synced before the .mcp.json fix
    # can have an inert mcpServers block left over in settings.local.json.
    # sync.py must call this out instead of leaving it silently stale.
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"

    _write(
        agent_meta_root / "config" / "mcp-registry.yaml",
        yaml.dump({
            "mcp-servers": {
                "example-server": {
                    "connection": {"type": "sse", "url": "{{EXAMPLE_URL}}"},
                }
            }
        }),
    )
    # Simulate the pre-fix leftover in the old target file.
    _write(
        project_root / ".claude" / "settings.local.json",
        json.dumps({"mcpServers": {"example-server": {"type": "sse", "url": "${EXAMPLE_URL}"}}}),
    )

    config = {"mcp-servers": ["example-server"], "platforms": []}
    provider_config = {
        "Claude": {
            "settings_file": ".claude/settings.json",
            "settings_local_file": ".claude/settings.local.json",
            "mcp-config": {
                "committed-file": ".mcp.json",
                "secrets-file": ".mcp.json",
                "format": "claude-settings",
            },
        }
    }
    log = SyncLog()

    generate_provider_configs(
        agent_meta_root, project_root, config, provider_config, log,
        dry_run=False, provider="Claude",
    )

    assert any("leftover 'mcpServers'" in w for w in log.warnings)


# ---------------------------------------------------------------------------
# build_mcp_guardrails_list — generated (not hand-maintained) hard-prohibitions
# ---------------------------------------------------------------------------

def test_build_mcp_guardrails_list_renders_active_servers_with_blocked_tools():
    registry = {
        "honcho": {"tools": {"blocked": ["delete_conclusion", "set_config"]}},
        "playwright": {"tools": {"blocked": ["browser_evaluate"]}},
        "reqflow": {"tools": {"blocked": ["issue.delete"]}},  # not active
    }
    result = build_mcp_guardrails_list(registry, ["honcho", "playwright"])
    lines = result.splitlines()
    assert lines == [
        "- **honcho:** `delete_conclusion`, `set_config` — absolut verboten.",
        "- **playwright:** `browser_evaluate` — absolut verboten.",
    ]


def test_build_mcp_guardrails_list_sorted_regardless_of_input_order():
    registry = {
        "zserver": {"tools": {"blocked": ["z_tool"]}},
        "aserver": {"tools": {"blocked": ["a_tool"]}},
    }
    result = build_mcp_guardrails_list(registry, ["zserver", "aserver"])
    assert result.splitlines()[0].startswith("- **aserver:**")


def test_build_mcp_guardrails_list_excludes_servers_without_blocked_tools():
    registry = {
        "honcho": {"tools": {"blocked": ["delete_conclusion"]}},
        "viz-logger": {"tools": {"allowed": ["log_event"]}},  # no blocked list
    }
    result = build_mcp_guardrails_list(registry, ["honcho", "viz-logger"])
    assert "viz-logger" not in result
    assert "honcho" in result


def test_build_mcp_guardrails_list_empty_when_no_active_server_has_blocked_tools():
    result = build_mcp_guardrails_list({}, [])
    assert result == "- (keine aktiven MCP-Server mit gesperrten Tools)"
