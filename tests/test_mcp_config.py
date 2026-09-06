"""Regression tests for MCP provider config generation (scripts/lib/mcp.py).

Covers audit findings #388/#400: Claude Code does not read a top-level
`mcpServers` key from settings.json/settings.local.json — only from
.mcp.json at the project root. Writing there previously produced a fully
inert, silently-broken MCP integration.
"""

import json
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

import yaml

from scripts.lib.log import SyncLog
from scripts.lib.mcp import _update_json_config, build_mcp_guardrails_list, generate_provider_configs
from scripts.lib.mcp_provider_config import (
    _update_codex_toml_config,
    _update_zcode_json_config,
    _write_provider_config,
)
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


def _write_mcp_catalog(agent_meta_root: Path, servers: dict) -> None:
    # mcp_registry.load_mcp_registry now sources from the unified
    # config/plugin-catalog.yaml (kind: mcp-server slice) instead of the old
    # config/mcp-registry.yaml — see scripts/lib/plugins.py.
    plugins = {name: {**sdef, "kind": "mcp-server"} for name, sdef in servers.items()}
    _write(
        agent_meta_root / "config" / "plugin-catalog.yaml",
        yaml.dump({"version": "1.0.0", "plugins": plugins}),
    )


def test_generate_provider_configs_writes_resolved_secrets_to_mcp_json(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"

    _write_mcp_catalog(agent_meta_root, {
        "example-server": {
            "description": "test server",
            "connection": {
                "type": "sse",
                "url": "{{EXAMPLE_URL}}",
                "headers": {"Authorization": "Bearer {{EXAMPLE_TOKEN}}"},
            },
        }
    })
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

    _write_mcp_catalog(agent_meta_root, {
        "example-server": {
            "connection": {"type": "sse", "url": "{{EXAMPLE_URL}}"},
        }
    })
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


# ---------------------------------------------------------------------------
# Codex (codex-toml-mcp), ZCode (zcode-json), KimiCode (claude-settings reuse)
# ---------------------------------------------------------------------------

def _codex_mcp_entries() -> dict:
    """Committed-entry shape as produced by _build_connection_entry(secrets=None):
    {{VAR}} already substituted to ${VAR}, plus the generic `type` discriminator.
    """
    return {
        "filesystem": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/ws"],
            "env": {"NODE_ENV": "${NODE_ENV}"},
        },
        "search": {
            "type": "sse",
            "url": "${SEARCH_URL}",
            "headers": {"Authorization": "Bearer ${SEARCH_TOKEN}", "X-Custom": "${CUSTOM_VAL}"},
        },
    }


def test_codex_toml_mcp_writer_golden(tmp_path):
    path = tmp_path / ".codex" / "config.toml"
    log = SyncLog()
    entries = _codex_mcp_entries()

    _update_codex_toml_config(path, entries, log, dry_run=False, allow_secrets=True)

    content = path.read_text(encoding="utf-8")
    # The emitted block must be valid TOML.
    parsed = tomllib.loads(content)
    assert "[mcp_servers.filesystem]" in content
    assert "[mcp_servers.search]" in content

    filesystem = parsed["mcp_servers"]["filesystem"]
    assert filesystem["command"] == "npx"
    assert filesystem["args"] == ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/ws"]
    assert filesystem["env"] == {"NODE_ENV": "${NODE_ENV}"}  # ${VAR} placeholders preserved
    assert "type" not in filesystem  # Codex has no type discriminator

    search = parsed["mcp_servers"]["search"]
    assert search["url"] == "${SEARCH_URL}"
    # Bearer ${VAR} header → native bearer_token_env_var env indirection (V8).
    assert search["bearer_token_env_var"] == "SEARCH_TOKEN"
    assert "Authorization" not in search["headers"]
    assert search["headers"]["X-Custom"] == "${CUSTOM_VAL}"
    assert "type" not in search

    # Idempotent: re-run on unchanged content → skip, file untouched.
    log2 = SyncLog()
    _update_codex_toml_config(path, entries, log2, dry_run=False, allow_secrets=True)
    assert any("unchanged" in s for s in log2.skipped)
    assert path.read_text(encoding="utf-8") == content


def test_codex_toml_mcp_writer_preserves_user_content_and_replaces_block(tmp_path):
    path = tmp_path / ".codex" / "config.toml"
    _write(path, '# my hand-written profile\n[profile.full]\nmodel = "gpt-5.5"\n')
    log = SyncLog()

    _update_codex_toml_config(path, _codex_mcp_entries(), log, dry_run=False, allow_secrets=True)
    first = path.read_text(encoding="utf-8")
    # Block appended at the end — user content above it is untouched.
    assert first.startswith('# my hand-written profile\n[profile.full]\nmodel = "gpt-5.5"\n\n')

    # A changed server set replaces the managed block in place, keeping the
    # user content byte-identical.
    _update_codex_toml_config(
        path, {"only": {"type": "stdio", "command": "uvx", "args": ["m"]}},
        log, dry_run=False, allow_secrets=True,
    )
    second = path.read_text(encoding="utf-8")
    assert second.startswith('# my hand-written profile\n[profile.full]\nmodel = "gpt-5.5"\n\n')
    assert "[mcp_servers.only]" in second
    assert "filesystem" not in second
    assert "search" not in second
    parsed = tomllib.loads(second)
    assert set(parsed["mcp_servers"]) == {"only"}
    assert parsed["profile"]["full"]["model"] == "gpt-5.5"


def test_generate_provider_configs_codex_toml_wires_committed_file(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"

    _write_mcp_catalog(agent_meta_root, {
        "search": {
            "connection": {
                "type": "sse",
                "url": "{{SEARCH_URL}}",
                "headers": {"Authorization": "Bearer {{SEARCH_TOKEN}}"},
            },
        },
        "local-fs": {
            "connection": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "fs"],
                "env": {"API_KEY": "{{API_KEY}}"},
            },
        },
    })

    config = {"mcp-servers": ["search", "local-fs"], "platforms": []}
    provider_config = {
        "Codex": {
            "mcp-config": {
                "committed-file": ".codex/config.toml",
                "format": "codex-toml-mcp",
            }
        }
    }
    log = SyncLog()

    generate_provider_configs(
        agent_meta_root, project_root, config, provider_config, log,
        dry_run=False, provider="Codex",
    )

    toml_path = project_root / ".codex" / "config.toml"
    assert toml_path.exists()
    parsed = tomllib.loads(toml_path.read_text(encoding="utf-8"))
    # {{VAR}} → ${VAR} committed substitution happened before rendering.
    assert parsed["mcp_servers"]["search"]["url"] == "${SEARCH_URL}"
    assert parsed["mcp_servers"]["search"]["bearer_token_env_var"] == "SEARCH_TOKEN"
    assert "Authorization" not in parsed["mcp_servers"]["search"].get("headers", {})
    assert parsed["mcp_servers"]["local-fs"]["command"] == "npx"
    assert parsed["mcp_servers"]["local-fs"]["env"] == {"API_KEY": "${API_KEY}"}
    # V8: Codex has no secrets-file — no local file may be generated.
    assert not (project_root / ".codex" / "config.local.toml").exists()


def test_codex_mcp_config_has_no_secrets_file():
    # V8: Codex has no include/import mechanism for a second TOML file — a
    # secrets-file entry would be dead config that is silently never read.
    repo_root = Path(__file__).resolve().parents[1]
    provider_config = load_providers_config(repo_root)
    assert "secrets-file" not in provider_config["Codex"]["mcp-config"]
    assert provider_config["Codex"]["mcp-config"]["format"] == "codex-toml-mcp"
    assert provider_config["Codex"]["mcp-config"]["committed-file"] == ".codex/config.toml"


def test_zcode_json_writer_creates_nested_mcp_servers(tmp_path):
    path = tmp_path / ".zcode" / "config.json"
    log = SyncLog()

    _update_zcode_json_config(
        path, {"srv": {"type": "sse", "url": "https://x"}}, log, dry_run=False, allow_secrets=True,
    )

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written == {"mcp": {"servers": {"srv": {"type": "sse", "url": "https://x"}}}}


def test_zcode_json_writer_merges_into_existing_config(tmp_path):
    path = tmp_path / ".zcode" / "config.json"
    _write(path, json.dumps({"model": {"main": "glm-5.3"}, "mcp": {"other": True}}))
    log = SyncLog()

    _update_zcode_json_config(
        path, {"srv": {"type": "sse", "url": "https://x"}}, log, dry_run=False, allow_secrets=True,
    )

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["mcp"]["servers"] == {"srv": {"type": "sse", "url": "https://x"}}
    assert written["mcp"]["other"] is True  # unrelated keys under mcp preserved
    assert written["model"] == {"main": "glm-5.3"}  # unrelated top-level keys preserved

    # Re-run identical content → idempotent skip.
    log2 = SyncLog()
    _update_zcode_json_config(
        path, {"srv": {"type": "sse", "url": "https://x"}}, log2, dry_run=False, allow_secrets=True,
    )
    assert any("unchanged" in s for s in log2.skipped)


def test_kimicode_mcp_config_reuses_claude_settings_format():
    # V13: Kimi Code reads the wire-identical {"mcpServers": ...} top-level
    # key from .kimi-code/mcp.json — the claude-settings JSON branch is
    # reused instead of a new format branch. No secrets-file (Kimi-native
    # env indirection is a P6 detail).
    repo_root = Path(__file__).resolve().parents[1]
    provider_config = load_providers_config(repo_root)
    mcp_cfg = provider_config["KimiCode"]["mcp-config"]
    assert mcp_cfg["format"] == "claude-settings"
    assert mcp_cfg["committed-file"] == ".kimi-code/mcp.json"
    assert "secrets-file" not in mcp_cfg


def test_write_provider_config_claude_settings_writes_kimicode_mcp_json(tmp_path):
    # Functional reuse check: format claude-settings writes the mcpServers
    # top-level key regardless of which provider directory the file lives in.
    path = tmp_path / ".kimi-code" / "mcp.json"
    log = SyncLog()
    entries = {"srv": {"type": "stdio", "command": "npx", "args": ["-y", "kimi-mcp"]}}

    _write_provider_config(path, entries, "claude-settings", log, dry_run=False, allow_secrets=True)

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["mcpServers"] == entries
    assert any("mcpServers" in a for a in log.actions)


def test_write_provider_config_warns_and_skips_unknown_format(tmp_path):
    path = tmp_path / "config.unknown"
    log = SyncLog()

    _write_provider_config(
        path, {"srv": {"type": "sse", "url": "https://x"}}, "mystery-format",
        log, dry_run=False, allow_secrets=True,
    )

    assert not path.exists()
    assert any("unknown provider format 'mystery-format'" in w for w in log.warnings)


# ---------------------------------------------------------------------------
# Copilot agent-mode MCP (vscode-settings) — issue #674 Phase 3.3
# ---------------------------------------------------------------------------

def test_write_provider_config_vscode_settings_writes_servers_key(tmp_path):
    """VS Code agent-mode MCP (.vscode/mcp.json) uses a top-level {"servers": ...}
    key — NOT the Claude {"mcpServers": ...} shape."""
    path = tmp_path / ".vscode" / "mcp.json"
    log = SyncLog()
    entries = {"srv": {"type": "stdio", "command": "npx", "args": ["-y", "fs"]}}

    _write_provider_config(path, entries, "vscode-settings", log, dry_run=False, allow_secrets=True)

    written = json.loads(path.read_text(encoding="utf-8"))
    assert written["servers"] == entries
    assert "mcpServers" not in written
    assert any("servers" in a for a in log.actions)


def test_write_provider_config_vscode_settings_idempotent(tmp_path):
    path = tmp_path / ".vscode" / "mcp.json"
    log = SyncLog()
    entries = {"srv": {"type": "stdio", "command": "npx", "args": ["-y", "fs"]}}

    _write_provider_config(path, entries, "vscode-settings", log, dry_run=False, allow_secrets=True)
    first = path.read_text(encoding="utf-8")

    log2 = SyncLog()
    _write_provider_config(path, entries, "vscode-settings", log2, dry_run=False, allow_secrets=True)
    assert any("unchanged" in s for s in log2.skipped)
    assert path.read_text(encoding="utf-8") == first


def test_vscode_settings_replaces_managed_key_preserving_user_keys(tmp_path):
    """The shared JSON writer replaces the managed "servers" key wholesale
    (same semantics as mcpServers for every other JSON format) while
    unrelated top-level keys (e.g. VS Code "inputs") are preserved."""
    path = tmp_path / ".vscode" / "mcp.json"
    _write(path, json.dumps({"servers": {"mine": {"type": "stdio", "command": "x"}},
                             "inputs": [{"type": "promptString", "id": "k"}]}))
    log = SyncLog()

    _write_provider_config(
        path, {"srv": {"type": "stdio", "command": "npx"}},
        "vscode-settings", log, dry_run=False, allow_secrets=True,
    )

    written = json.loads(path.read_text(encoding="utf-8"))
    assert set(written["servers"]) == {"srv"}
    assert written["inputs"] == [{"type": "promptString", "id": "k"}]  # preserved


def test_generate_provider_configs_vscode_settings_wires_committed_placeholders(tmp_path):
    """Full pipeline: {{VAR}} → ${env:VAR} (VS Code-native expansion) in the
    committed .vscode/mcp.json; sse entries map to VS Code's "http" type;
    no secrets-file → no local file is generated."""
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"

    _write_mcp_catalog(agent_meta_root, {
        "search": {
            "connection": {
                "type": "sse",
                "url": "{{SEARCH_URL}}",
                "headers": {"Authorization": "Bearer {{SEARCH_TOKEN}}"},
            },
        },
        "local-fs": {
            "connection": {
                "type": "stdio",
                "command": "npx",
                "args": ["-y", "fs"],
                "env": {"API_KEY": "{{API_KEY}}"},
            },
        },
    })

    config = {"mcp-servers": ["search", "local-fs"], "platforms": []}
    provider_config = {
        "Copilot": {
            "mcp-config": {
                "committed-file": ".vscode/mcp.json",
                "format": "vscode-settings",
            }
        }
    }
    log = SyncLog()

    generate_provider_configs(
        agent_meta_root, project_root, config, provider_config, log,
        dry_run=False, provider="Copilot",
    )

    mcp_json_path = project_root / ".vscode" / "mcp.json"
    assert mcp_json_path.exists()
    written = json.loads(mcp_json_path.read_text(encoding="utf-8"))

    search = written["servers"]["search"]
    assert search["type"] == "http"  # VS Code deprecates the legacy "sse" type
    assert search["url"] == "${env:SEARCH_URL}"
    assert search["headers"]["Authorization"] == "Bearer ${env:SEARCH_TOKEN}"

    local_fs = written["servers"]["local-fs"]
    assert local_fs["type"] == "stdio"
    assert local_fs["command"] == "npx"
    assert local_fs["env"] == {"API_KEY": "${env:API_KEY}"}

    # No secrets-file strategy → no local file may be generated.
    assert not (project_root / ".vscode" / "mcp.local.json").exists()


def test_copilot_mcp_config_wiring_in_real_registry():
    """The real config/ai-providers.yaml Copilot block: mcp capability on,
    .vscode/mcp.json committed (VS Code agent-mode shape), NO secrets-file
    (committed ${env:VAR} placeholders keep secrets out — Codex block shows
    the equivalent no-secrets-file precedent), and `.vscode/` NOT claimed as
    a provider root (shared editor directory, not Copilot-only)."""
    repo_root = Path(__file__).resolve().parents[1]
    provider_config = load_providers_config(repo_root)
    copilot = provider_config["Copilot"]
    assert "mcp" in copilot["capabilities"]
    mcp_cfg = copilot["mcp-config"]
    assert mcp_cfg["format"] == "vscode-settings"
    assert mcp_cfg["committed-file"] == ".vscode/mcp.json"
    assert "secrets-file" not in mcp_cfg
    assert ".vscode/" not in copilot.get("provider_root_dirs", [])
