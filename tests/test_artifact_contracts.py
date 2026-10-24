"""Unit tests for the provider-agnostic artifact validators.

Plan Task 1 (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30), AC-13.

The validator is dispatch-free: every method takes the artifact *format* as a
parameter and never reads a provider name. The tests pin the four contract
surfaces:

* ``validate_toml`` — a malformed TOML document yields an ERROR Finding.
* ``validate_frontmatter`` — the narrow ``allowed-fields`` fixture (AC-13): an
  injected key outside the allow-list yields an ERROR Finding.
* ``validate_json_document`` — the ``opencode-json-v2`` case asserts v2 nesting
  (``mcp.servers`` present, no flat top-level ``mcp`` server map); the
  ``opencode-json`` case asserts the flat v1 shape. Plan Task 17 (AC-C8/C9/C10)
  adds the opencode v2 connection-key checks (``enabled``, ``timeout``,
  ``oauth``) and the merged-catalog counterpart
  ``consistency.artifact_contracts.check_mcp_connection_keys``.

Run: python3 -m pytest tests/test_artifact_contracts.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.artifact_validate import (  # noqa: E402
    validate_frontmatter,
    validate_json_document,
    validate_mcp_document,
    validate_toml,
)
from lib.consistency import artifact_contracts  # noqa: E402
from lib.consistency.report import Finding, Severity  # noqa: E402


def _frontmatter(body: str = "Body content.\n") -> str:
    return (
        "---\n"
        "name: developer\n"
        "description: test agent\n"
        "tools:\n"
        "  - Read\n"
        "---\n"
        + body
    )


def _errors(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == Severity.ERROR]


# --------------------------------------------------------------------------- #
# validate_toml
# --------------------------------------------------------------------------- #

def test_validate_toml_valid_document_returns_no_findings() -> None:
    text = 'name = "developer"\nmodel = "gpt-5"\n'
    assert validate_toml(text, ".codex/agents/developer.toml") == []


def test_validate_toml_empty_document_is_valid() -> None:
    assert validate_toml("", ".codex/agents/empty.toml") == []


def test_validate_toml_malformed_returns_error() -> None:
    # AC-13: malformed TOML -> Finding (unterminated string + bad table).
    text = 'name = "unterminated\n[tools\n'
    findings = validate_toml(text, ".codex/agents/broken.toml")

    errors = _errors(findings)
    assert len(errors) == 1
    assert errors[0].severity == Severity.ERROR
    assert errors[0].file == ".codex/agents/broken.toml"
    assert errors[0].check == "artifact-contract"


def test_validate_toml_singleton_after_string_returns_error() -> None:
    # Mirrors the real F1 defect: a Markdown block appended after the closing
    # """ of the serialized document (line 467 carries prose, not a comment).
    text = (
        'developer_instructions = """\nbody\n"""\n'
        "## Singleton-Regel\n"
        "- always active\n"
    )
    findings = validate_toml(text, ".codex/agents/agent-meta-manager.toml")
    assert len(_errors(findings)) == 1


# --------------------------------------------------------------------------- #
# validate_frontmatter
# --------------------------------------------------------------------------- #

def test_validate_frontmatter_required_within_allow_list_is_clean() -> None:
    findings = validate_frontmatter(
        _frontmatter(),
        allowed_fields={"name", "description", "tools"},
        required_fields={"name", "description"},
        reject_fields=set(),
        path=".opencode/agents/developer.md",
    )
    assert findings == []


def test_validate_frontmatter_extra_key_outside_narrow_allow_list() -> None:
    # AC-13 narrow allowed-fields fixture: allow-list is [name, description]
    # and the emitted document carries an injected extra key (tools).
    findings = validate_frontmatter(
        _frontmatter(),
        allowed_fields={"name", "description"},
        required_fields={"name", "description"},
        reject_fields=set(),
        path=".opencode/agents/developer.md",
    )

    errors = _errors(findings)
    assert len(errors) == 1
    assert "tools" in errors[0].message
    assert errors[0].check == "artifact-contract"
    assert errors[0].file == ".opencode/agents/developer.md"


def test_validate_frontmatter_missing_required_yields_error() -> None:
    text = "---\nname: developer\n---\n\nBody.\n"
    findings = validate_frontmatter(
        text,
        allowed_fields=None,
        required_fields={"name", "description"},
        reject_fields=set(),
        path=".opencode/agents/developer.md",
    )

    errors = _errors(findings)
    assert len(errors) == 1
    assert "description" in errors[0].message


def test_validate_frontmatter_rejected_key_yields_error() -> None:
    text = "---\nname: x\ndescription: y\nsubagent_depth: 2\n---\n"
    findings = validate_frontmatter(
        text,
        allowed_fields=None,
        required_fields=set(),
        reject_fields={"subagent_depth"},
        path=".opencode/agents/developer.md",
    )

    errors = _errors(findings)
    assert len(errors) == 1
    assert "subagent_depth" in errors[0].message


def test_validate_frontmatter_none_allow_list_accepts_any_key() -> None:
    findings = validate_frontmatter(
        _frontmatter(),
        allowed_fields=None,
        required_fields={"name"},
        reject_fields=set(),
        path=".opencode/agents/developer.md",
    )
    assert findings == []


def test_validate_frontmatter_malformed_yaml_yields_error() -> None:
    text = "---\nname: [unterminated\n---\n\nBody.\n"
    findings = validate_frontmatter(
        text,
        allowed_fields=None,
        required_fields=set(),
        reject_fields=set(),
        path=".opencode/agents/developer.md",
    )
    assert len(_errors(findings)) == 1


def test_validate_frontmatter_missing_block_yields_error() -> None:
    findings = validate_frontmatter(
        "Just a body, no frontmatter.\n",
        allowed_fields=None,
        required_fields={"name"},
        reject_fields=set(),
        path=".opencode/agents/developer.md",
    )
    assert len(_errors(findings)) >= 1


# --------------------------------------------------------------------------- #
# validate_json_document
# --------------------------------------------------------------------------- #

def test_validate_json_document_v2_nested_servers_is_clean() -> None:
    text = (
        '{"$schema": "https://opencode.ai/config.json",'
        ' "mcp": {"servers": {"foo": {"type": "local"}}},'
        ' "default_agent": "orchestrator"}'
    )
    assert validate_json_document(text, "opencode-json-v2", "opencode.json") == []


def test_validate_json_document_v2_missing_servers_is_error() -> None:
    text = '{"mcp": {"foo": {"type": "local"}}}'
    errors = _errors(validate_json_document(text, "opencode-json-v2", "opencode.json"))
    assert len(errors) == 1
    assert "servers" in errors[0].message


def test_validate_json_document_v2_flat_mcp_is_error() -> None:
    # A v2 document whose mcp map is the flat v1 server map (no servers key).
    text = '{"mcp": {"foo": {"type": "local"}, "bar": {"type": "local"}}}'
    errors = _errors(validate_json_document(text, "opencode-json-v2", "opencode.json"))
    assert errors


def test_validate_json_document_v2_accepts_subagent_depth() -> None:
    # IC-15 Nr. 16: subagent_depth is retained on the v2 surface, not v1-only.
    text = '{"mcp": {"servers": {}}, "subagent_depth": 2}'
    assert validate_json_document(text, "opencode-json-v2", "opencode.json") == []


def test_validate_json_document_v1_flat_mcp_is_clean() -> None:
    text = '{"mcp": {"foo": {"type": "local"}}}'
    assert validate_json_document(text, "opencode-json", "opencode.json") == []


def test_validate_json_document_v1_missing_mcp_is_clean() -> None:
    # issue #849 follow-up: no MCP servers configured -> no top-level 'mcp'
    # object is legitimate and MUST NOT produce a finding.
    text = '{"default_agent": "orchestrator"}'
    assert validate_json_document(text, "opencode-json", "opencode.json") == []


def test_validate_json_document_v1_empty_mcp_is_clean() -> None:
    text = '{"mcp": {}}'
    assert validate_json_document(text, "opencode-json", "opencode.json") == []


def test_validate_json_document_v1_wrong_mcp_type_is_error() -> None:
    # A populated-but-wrong-shape 'mcp' value stays fail-loud (issue #849).
    text = '{"mcp": ["not-an-object"]}'
    errors = _errors(validate_json_document(text, "opencode-json", "opencode.json"))
    assert len(errors) == 1
    assert errors[0].check == "artifact-contract"
    assert "mcp" in errors[0].message


def test_validate_json_document_v2_missing_mcp_is_clean() -> None:
    text = '{"default_agent": "orchestrator", "permission": {}}'
    assert validate_json_document(text, "opencode-json-v2", "opencode.json") == []


def test_validate_json_document_v2_empty_mcp_is_clean() -> None:
    text = '{"mcp": {}}'
    assert validate_json_document(text, "opencode-json-v2", "opencode.json") == []


def test_validate_json_document_invalid_json_is_error() -> None:
    errors = _errors(validate_json_document("{not json", "opencode-json-v2", "opencode.json"))
    assert len(errors) == 1


def test_validate_json_document_unknown_format_is_clean() -> None:
    # Formats without a declared contract are not guessed.
    assert validate_json_document("{}", "some-other-format", "x.json") == []


# validate_mcp_document (issue #849 — shared committed-MCP-document resolver)


def test_validate_mcp_document_valid_v1_document_is_clean(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text(
        '{"mcp": {"foo": {"type": "local"}}}', encoding="utf-8"
    )
    mcp = {"committed-file": "opencode.json", "format": "opencode-json"}

    assert validate_mcp_document(mcp, tmp_path) == []


def test_validate_mcp_document_invalid_json_is_error(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text("{ not valid json", encoding="utf-8")
    mcp = {"committed-file": "opencode.json", "format": "opencode-json"}

    findings = validate_mcp_document(mcp, tmp_path)

    errors = _errors(findings)
    assert len(errors) == 1
    assert errors[0].check == "artifact-contract"
    assert errors[0].file == "opencode.json"
    assert "invalid JSON" in errors[0].message


def test_validate_mcp_document_no_mcp_is_clean(tmp_path: Path) -> None:
    # issue #849 follow-up: a generated project without MCP servers has an
    # opencode.json that carries isolation/permission keys but no 'mcp' object.
    (tmp_path / "opencode.json").write_text(
        '{"subagent_depth": 3, "permission": {"edit": {"**": "deny"}}}',
        encoding="utf-8",
    )
    mcp = {"committed-file": "opencode.json", "format": "opencode-json"}

    assert validate_mcp_document(mcp, tmp_path) == []


def test_validate_mcp_document_wrong_v1_shape_is_error(tmp_path: Path) -> None:
    # A populated-but-wrong-shape 'mcp' value stays fail-loud (issue #849).
    (tmp_path / "opencode.json").write_text('{"mcp": ["not-an-object"]}', encoding="utf-8")
    mcp = {"committed-file": "opencode.json", "format": "opencode-json"}

    errors = _errors(validate_mcp_document(mcp, tmp_path))
    assert len(errors) == 1
    assert "flat top-level object" in errors[0].message


def test_validate_mcp_document_toml_format_is_validated(tmp_path: Path) -> None:
    (tmp_path / ".codex" / "config.toml").parent.mkdir(parents=True)
    (tmp_path / ".codex" / "config.toml").write_text("[mcp_servers.broken\n", encoding="utf-8")
    mcp = {"committed-file": ".codex/config.toml", "format": "codex-toml-mcp"}

    assert len(_errors(validate_mcp_document(mcp, tmp_path))) == 1


def test_validate_mcp_document_absent_file_is_clean(tmp_path: Path) -> None:
    mcp = {"committed-file": "opencode.json", "format": "opencode-json"}
    assert validate_mcp_document(mcp, tmp_path) == []


def test_validate_mcp_document_undeclared_format_is_clean(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text("{ not valid json", encoding="utf-8")
    mcp = {"committed-file": "opencode.json", "format": "claude-settings"}
    assert validate_mcp_document(mcp, tmp_path) == []


def test_validate_mcp_document_missing_config_is_clean(tmp_path: Path) -> None:
    assert validate_mcp_document(None, tmp_path) == []
    assert validate_mcp_document({}, tmp_path) == []


# --------------------------------------------------------------------------- #
# opencode v2 connection keys (plan Task 17, AC-C8/C9/C10)
# --------------------------------------------------------------------------- #

_V2_PATH = "opencode.json"


def _v2_document(servers: dict) -> str:
    return json.dumps({"$schema": "https://opencode.ai/config.json",
                       "mcp": {"servers": servers}})


def test_v2_server_with_enabled_is_finding() -> None:
    # AC-C10: 'enabled' is the frozen v1 active flag; v2 emits no such key.
    text = _v2_document({"foo": {"type": "local", "enabled": True}})

    errors = _errors(validate_json_document(text, "opencode-json-v2", _V2_PATH))

    assert len(errors) == 1
    assert errors[0].check == "artifact-contract"
    assert "v2 server uses legacy 'enabled'" in errors[0].message
    assert "foo" in errors[0].message


def test_v2_timeout_non_integer_is_finding() -> None:
    # AC-C10: timeout carries integer millisecond budgets only ('startup' is
    # optional, Amendment B1) -- a duration string is not a valid budget.
    text = _v2_document(
        {"foo": {"type": "local", "timeout": {"catalog": "5s", "execution": 60000}}}
    )

    errors = _errors(validate_json_document(text, "opencode-json-v2", _V2_PATH))

    assert len(errors) == 1
    assert errors[0].check == "artifact-contract"
    assert "timeout" in errors[0].message
    assert "catalog" in errors[0].message


def test_v2_oauth_camel_case_is_finding() -> None:
    # AC-C10: the registry/writer use snake_case; camelCase would be dropped.
    text = _v2_document(
        {"foo": {"type": "local", "oauth": {"clientId": "id", "clientSecret": "s"}}}
    )

    errors = _errors(validate_json_document(text, "opencode-json-v2", _V2_PATH))

    assert len(errors) == 1
    assert errors[0].check == "artifact-contract"
    assert "oauth" in errors[0].message
    assert "clientId" in errors[0].message


def test_v2_valid_server_has_no_finding() -> None:
    # AC-C8/C9: integer timeouts (startup optional) and snake_case oauth are the
    # supported v2 shape, so a writer-emitted document stays clean.
    text = _v2_document(
        {
            "foo": {
                "type": "local",
                "command": ["npx", "-y", "some-server"],
                "timeout": {"startup": 5000, "catalog": 5000, "execution": 60000},
                "oauth": {
                    "client_id": "{env:OC_ID}",
                    "client_secret": "{env:OC_SECRET}",
                    "scope": "read",
                },
                "disabled": False,
            }
        }
    )

    assert validate_json_document(text, "opencode-json-v2", _V2_PATH) == []


def _write_catalog(root: Path, plugins: dict) -> None:
    """Write a framework-shaped plugin catalog (JSON is valid YAML)."""
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "plugin-catalog.yaml").write_text(
        json.dumps({"version": "1.0.0", "plugins": plugins}, indent=2),
        encoding="utf-8",
    )


def test_check_mcp_connection_keys_invalid_timeout_is_error(tmp_path: Path) -> None:
    _write_catalog(
        tmp_path,
        {
            "bad": {
                "kind": "mcp-server",
                "connection": {"type": "stdio", "timeout": {"catalog": "5s"}},
            }
        },
    )

    findings = artifact_contracts.check_mcp_connection_keys(tmp_path)

    errors = _errors(findings)
    assert len(errors) == 1
    assert errors[0].severity == Severity.ERROR
    assert errors[0].message == "mcp-connection-key: bad.timeout invalid"
    assert "catalog" in errors[0].suggestion


def test_check_mcp_connection_keys_valid_catalog_has_no_finding() -> None:
    # The real framework catalog carries no v2 connection keys yet, so the
    # registry-wide check must stay silent (no false positive on the repo).
    findings = artifact_contracts.check_mcp_connection_keys(_REPO_ROOT)

    assert findings == []


def test_check_mcp_connection_keys_validates_merged_project_override(
    tmp_path: Path,
) -> None:
    # Framework: 'shared' is valid, 'framework-bad' carries an invalid timeout.
    _write_catalog(
        tmp_path,
        {
            "shared": {
                "kind": "mcp-server",
                "connection": {"type": "stdio", "command": "npx", "args": []},
            },
            "framework-bad": {
                "kind": "mcp-server",
                "connection": {"type": "stdio", "timeout": {"execution": "soon"}},
            },
        },
    )
    # Project override (deep-merged over the framework entry):
    # * 'framework-bad' replaces the invalid timeout with a valid one,
    # * 'shared' adds a camelCase oauth block (invalid on the v2 surface).
    project_dir = tmp_path / ".meta-config"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "plugin-catalog.yaml").write_text(
        json.dumps(
            {
                "plugins": {
                    "framework-bad": {"connection": {"timeout": {"execution": 60000}}},
                    "shared": {"connection": {"oauth": {"clientId": "id"}}},
                }
            }
        ),
        encoding="utf-8",
    )

    errors = _errors(artifact_contracts.check_mcp_connection_keys(tmp_path))

    assert len(errors) == 1, [f.message for f in errors]
    assert errors[0].message == "mcp-connection-key: shared.oauth invalid"
    assert "clientId" in errors[0].suggestion


# --------------------------------------------------------------------------- #
# settings-file duplicate guard (plan Task 25, AC-D9)
# --------------------------------------------------------------------------- #

#: AC-D9-mandated finding label. A constant, not a provider dispatch: the check
#: iterates the registry and composes the message from the actual file names.
_CHECK_SETTINGS_DUPLICATE = "opencode-config-duplicate"


def _write_provider_registry(root: Path, providers: dict) -> None:
    """Write a minimal framework-shaped provider registry (JSON is valid YAML)."""
    config_dir = root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "ai-providers.yaml").write_text(
        json.dumps({"providers": providers}, indent=2),
        encoding="utf-8",
    )


def _duplicate_findings(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.check == _CHECK_SETTINGS_DUPLICATE]


def test_ac_d9_duplicate_jsonc_is_warning(tmp_path: Path) -> None:
    # AC-D9: a content-bearing .jsonc is merged over the managed .json (last
    # write wins, evidence doc §3), so the duplicate is a permanent WARNING.
    _write_provider_registry(tmp_path, {"Opencode": {"settings_file": "opencode.json"}})
    (tmp_path / "opencode.json").write_text("{}", encoding="utf-8")
    (tmp_path / "opencode.jsonc").write_text("{}", encoding="utf-8")

    findings = artifact_contracts.check_settings_file_duplicates(
        tmp_path, {"ai-providers": ["Opencode"]}
    )

    assert len(findings) == 1, [f.message for f in findings]
    assert findings[0].severity == Severity.WARNING
    assert findings[0].check == "opencode-config-duplicate"
    assert findings[0].message == (
        "opencode-config-duplicate: opencode.json and opencode.jsonc "
        "both present; keep one"
    )


def test_ac_d9_no_finding_without_jsonc(tmp_path: Path) -> None:
    # AC-D9: without a .jsonc twin there is nothing shadowing the settings file.
    _write_provider_registry(tmp_path, {"Opencode": {"settings_file": "opencode.json"}})
    (tmp_path / "opencode.json").write_text("{}", encoding="utf-8")

    findings = artifact_contracts.check_artifact_contracts(
        tmp_path, {"ai-providers": ["Opencode"]}
    )

    assert _duplicate_findings(findings) == []


def test_ac_d9_check_is_provider_agnostic(tmp_path: Path) -> None:
    # AC-D9: a synthetic provider with a different settings_file (and a second
    # one without a twin) produces the same finding — the check reads the
    # registry's settings_file and never a provider name.
    _write_provider_registry(
        tmp_path,
        {
            "SyntheticAlpha": {"settings_file": "foo.json"},
            "SyntheticBeta": {"settings_file": "nested/bar.json"},
        },
    )
    (tmp_path / "foo.json").write_text("{}", encoding="utf-8")
    (tmp_path / "foo.jsonc").write_text("{}", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "bar.json").write_text("{}", encoding="utf-8")

    findings = _duplicate_findings(
        artifact_contracts.check_artifact_contracts(
            tmp_path, {"ai-providers": ["SyntheticAlpha", "SyntheticBeta"]}
        )
    )

    assert len(findings) == 1, [f.message for f in findings]
    assert findings[0].severity == Severity.WARNING
    assert findings[0].check == "opencode-config-duplicate"
    assert findings[0].message == (
        "opencode-config-duplicate: foo.json and foo.jsonc both present; keep one"
    )
    assert "Opencode" not in findings[0].message
