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
  ``opencode-json`` case asserts the flat v1 shape.

Run: python3 -m pytest tests/test_artifact_contracts.py -q
"""
from __future__ import annotations

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


def test_validate_json_document_v2_rejects_v1_only_key() -> None:
    text = '{"mcp": {"servers": {}}, "subagent_depth": 2}'
    errors = _errors(validate_json_document(text, "opencode-json-v2", "opencode.json"))
    assert len(errors) == 1
    assert "subagent_depth" in errors[0].message


def test_validate_json_document_v1_flat_mcp_is_clean() -> None:
    text = '{"mcp": {"foo": {"type": "local"}}}'
    assert validate_json_document(text, "opencode-json", "opencode.json") == []


def test_validate_json_document_v1_missing_mcp_is_error() -> None:
    text = '{"default_agent": "orchestrator"}'
    errors = _errors(validate_json_document(text, "opencode-json", "opencode.json"))
    assert len(errors) == 1
    assert errors[0].check == "artifact-contract"


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


def test_validate_mcp_document_wrong_v1_shape_is_error(tmp_path: Path) -> None:
    (tmp_path / "opencode.json").write_text('{"default_agent": "orchestrator"}', encoding="utf-8")
    mcp = {"committed-file": "opencode.json", "format": "opencode-json"}

    errors = _errors(validate_mcp_document(mcp, tmp_path))
    assert len(errors) == 1
    assert "flat top-level 'mcp'" in errors[0].message


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
