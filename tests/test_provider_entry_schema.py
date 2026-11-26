"""Provider registry entry schema (issue #1239 / wave 5 C3, T35).

Pins the contract of ``schemas/provider-entry.schema.json`` and the validation
wired into ``--validate``:

- AC-1: every entry of the framework's ``config/ai-providers.yaml`` is valid
  (``--validate`` exit 0).
- AC-2: an unknown key or a type error is a hard error naming the provider and
  the field (``--validate`` exit 1).
- AC-2 (fallback): without ``jsonschema`` the stdlib fallback emits the same
  messages, so no new dependency is required (ADR-0001 unchanged).

Non-goals (spec C3): ``scripts/lib/schema.py::update_providers_enum`` and the
defaults table ``external_tools_drift.py`` are untouched.

Run: python3 -m pytest tests/test_provider_entry_schema.py -q
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import config, providers  # noqa: E402

_SCHEMA_PATH = REPO_ROOT / "schemas" / "provider-entry.schema.json"
_REGISTRY_PATH = REPO_ROOT / "config" / "ai-providers.yaml"


def _valid_entry(**extra) -> dict:
    entry = {"agents_dir": ".acme/agents", "context_file": "ACME.md"}
    entry.update(extra)
    return entry


#: (id, registry document, expected message fragment) fixtures for AC-2.
_BROKEN_FIXTURES = [
    (
        "unknown_key",
        {"providers": {"Claude": _valid_entry(agents_dirr="typo")}},
        "provider 'Claude': unknown key 'agents_dirr'",
    ),
    (
        "type_error",
        {"providers": {"Claude": _valid_entry(has_hooks="yes")}},
        "provider 'Claude': field 'has_hooks' must be boolean (got string)",
    ),
    (
        "missing_required",
        {"providers": {"Claude": {"agents_dir": ".claude/agents"}}},
        "provider 'Claude': missing required field 'context_file'",
    ),
    (
        "nested_unknown_key",
        {"providers": {"Claude": _valid_entry(**{"mcp-config": {"format": "x", "bogus": 1}})}},
        "provider 'Claude': unknown key 'mcp-config.bogus'",
    ),
    (
        "nested_type_error",
        {"providers": {"Claude": _valid_entry(**{"mcp-config": {"format": 3}})}},
        "provider 'Claude': field 'mcp-config.format' must be string (got integer)",
    ),
    (
        "capability_item_type",
        {"providers": {"Claude": _valid_entry(capabilities=["agents", 2])}},
        "provider 'Claude': field 'capabilities.1' must be string (got integer)",
    ),
]


def _validate(document: dict, *, use_jsonschema: bool) -> list[str]:
    """Validate *document* with or without the optional jsonschema package."""
    if use_jsonschema and not providers._JSONSCHEMA_AVAILABLE:
        pytest.skip("jsonschema not installed")
    saved = providers._JSONSCHEMA_AVAILABLE
    providers._JSONSCHEMA_AVAILABLE = use_jsonschema
    try:
        return providers.validate_provider_registry(REPO_ROOT, document=document)
    finally:
        providers._JSONSCHEMA_AVAILABLE = saved


# --- schema shape -----------------------------------------------------------


def test_schema_file_exists_and_is_draft7():
    assert _SCHEMA_PATH.is_file()
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert schema["$schema"].endswith("draft-07/schema#")
    assert "providerEntry" in schema["definitions"]
    assert schema["additionalProperties"] == {"$ref": "#/definitions/providerEntry"}


@pytest.mark.parametrize(
    "key",
    [
        # #1255 extension-hook capability
        "extension_hook_path",
        # #1253/#1254 format + command dispatch data
        "mcp-config",
        "commands_format",
        "runtime_gate-mechanism",
        "surface-version",
    ],
)
def test_wave5_keys_are_modelled(key):
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    assert key in schema["definitions"]["providerEntry"]["properties"]


def test_capabilities_are_modelled_as_string_list():
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    capabilities = schema["definitions"]["providerEntry"]["properties"]["capabilities"]
    assert capabilities == {"$ref": "#/definitions/stringList"}
    assert schema["definitions"]["stringList"]["items"] == {"type": "string"}


# --- AC-1: the shipped registry is valid -----------------------------------


def test_repo_registry_is_valid():
    assert providers.validate_provider_registry(REPO_ROOT) == []


def test_repo_registry_is_valid_without_jsonschema(monkeypatch):
    monkeypatch.setattr(providers, "_JSONSCHEMA_AVAILABLE", False)
    assert providers.validate_provider_registry(REPO_ROOT) == []


def test_unwrapped_registry_document_is_valid():
    """The loader falls back to the bare map when 'providers:' is absent."""
    data = yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8"))
    bare = data.get("providers", data)
    assert providers.validate_provider_registry(REPO_ROOT, document=bare) == []


# --- AC-2: unknown key / type error ----------------------------------------


@pytest.mark.parametrize("case,document,expected", _BROKEN_FIXTURES,
                         ids=[case for case, _doc, _expected in _BROKEN_FIXTURES])
def test_jsonschema_reports_provider_and_field(case, document, expected):
    assert expected in _validate(document, use_jsonschema=True)


@pytest.mark.parametrize("case,document,expected", _BROKEN_FIXTURES,
                         ids=[case for case, _doc, _expected in _BROKEN_FIXTURES])
def test_fallback_reports_provider_and_field(case, document, expected):
    assert expected in _validate(document, use_jsonschema=False)


@pytest.mark.parametrize("case,document,expected", _BROKEN_FIXTURES,
                         ids=[case for case, _doc, _expected in _BROKEN_FIXTURES])
def test_fallback_and_jsonschema_agree(case, document, expected):
    """Same error contract with and without the optional dependency."""
    if not providers._JSONSCHEMA_AVAILABLE:
        pytest.skip("jsonschema not installed")
    assert _validate(document, use_jsonschema=False) == _validate(
        document, use_jsonschema=True)


def test_valid_document_yields_no_messages():
    document = {"providers": {"Acme": _valid_entry(capabilities=["agents"])}}
    assert _validate(document, use_jsonschema=False) == []


# --- exit-code wiring of --validate ---------------------------------------


def _broken_framework_root(tmp_path: Path) -> Path:
    """Minimal framework root: real schema + one invalid registry entry."""
    (tmp_path / "schemas").mkdir()
    shutil.copy(_SCHEMA_PATH, tmp_path / "schemas" / _SCHEMA_PATH.name)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "ai-providers.yaml").write_text(
        "providers:\n  Acme:\n    agents_dir: .acme/agents\n"
        "    context_file: ACME.md\n    agents_dirr: typo\n",
        encoding="utf-8",
    )
    return tmp_path


def _valid_framework_root(tmp_path: Path) -> Path:
    (tmp_path / "schemas").mkdir()
    shutil.copy(_SCHEMA_PATH, tmp_path / "schemas" / _SCHEMA_PATH.name)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "ai-providers.yaml").write_text(
        "providers:\n  Acme:\n    agents_dir: .acme/agents\n"
        "    context_file: ACME.md\n",
        encoding="utf-8",
    )
    return tmp_path


def test_validate_aborts_with_exit_1_on_unknown_key(tmp_path, monkeypatch, capsys):
    root = _broken_framework_root(tmp_path)
    monkeypatch.setattr(config, "_framework_root", lambda: root)
    with pytest.raises(SystemExit) as exc:
        config._validate_provider_registry(tmp_path / ".meta-config" / "project.yaml")
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "Acme" in err and "agents_dirr" in err


def test_validate_passes_on_valid_registry(tmp_path, monkeypatch):
    root = _valid_framework_root(tmp_path)
    monkeypatch.setattr(config, "_framework_root", lambda: root)
    # No SystemExit: --validate continues with the remaining checks (exit 0 path).
    config._validate_provider_registry(tmp_path / ".meta-config" / "project.yaml")


def test_missing_schema_is_optional(tmp_path, monkeypatch):
    root = _valid_framework_root(tmp_path)
    (root / "schemas" / _SCHEMA_PATH.name).unlink()
    monkeypatch.setattr(config, "_framework_root", lambda: root)
    config._validate_provider_registry(tmp_path / ".meta-config" / "project.yaml")


def test_existing_validate_contract_unchanged():
    """The repo registry passes the same gate the CLI runs (exit 0 path)."""
    assert providers.validate_provider_registry(REPO_ROOT) == []
