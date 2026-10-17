"""IC-15 Nr. 21 / Task 1.40 (AC-10): read-only roles map to sandbox read-only.

A provider can enforce read-only access through a sandbox field. It declares
the capability ``read_only_enforcement: sandbox``
(config/provider-capabilities.yaml) and the override map
``read-only-extra-fields`` in its ``agent-transform`` spec
(config/ai-providers.yaml). A role whose template tool list carries neither
``Write`` nor ``Edit`` then emits the read-only sandbox value instead of the
default (``workspace-write``); every other role keeps the default.

The mechanism is pure data — ``provider_transform`` reads the capability and
the spec keys, never a provider name (guard:
``tests/test_provider_agnostic_dispatch.py``).
"""
from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

import yaml

from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import (
    _effective_extra_fields,
    _role_read_only,
    transform_agent_content_for_provider,
)
from scripts.lib.providers import load_providers_config

REPO_ROOT = Path(__file__).resolve().parents[1]
_PROVIDER_CONFIG = load_providers_config(REPO_ROOT)
_CAPS = yaml.safe_load(
    (REPO_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8")
)["capabilities"]


def _content(tools: list[str] | None) -> str:
    tool_block = "" if tools is None else "tools:\n" + "".join(f"  - {t}\n" for t in tools)
    return (
        "---\n"
        "name: template-role\n"
        'version: "1.0.0"\n'
        "description: old description\n"
        f"{tool_block}"
        "---\n"
        "\n# Role\n\nBody.\n"
    )


def _transform_codex(role: str, tools: list[str] | None) -> dict:
    log = SyncLog()
    out = transform_agent_content_for_provider(
        _content(tools), "Codex", role, role, "desc",
        "1-generic/role.md@1.0.0", {}, REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".codex" / "agents" / f"{role}.toml", _PROVIDER_CONFIG, log,
        provider_capabilities=_CAPS,
    )
    return tomllib.loads(out)


# ---------------------------------------------------------------------------
# Config: capability + data-driven override map
# ---------------------------------------------------------------------------

def test_codex_declares_sandbox_read_only_enforcement() -> None:
    assert _CAPS["Codex"]["read_only_enforcement"] == "sandbox"
    spec = _PROVIDER_CONFIG["Codex"]["agent-transform"]
    assert spec["extra-fields"]["sandbox_mode"] == "workspace-write"
    assert spec["read-only-extra-fields"]["sandbox_mode"] == "read-only"


# ---------------------------------------------------------------------------
# End-to-end: Codex TOML sandbox_mode per role
# ---------------------------------------------------------------------------

def test_read_only_role_gets_sandbox_read_only() -> None:
    doc = _transform_codex("explorer", ["Read", "Grep", "Glob", "Bash"])
    assert doc["sandbox_mode"] == "read-only"


def test_write_role_keeps_workspace_write() -> None:
    doc = _transform_codex("developer", ["Read", "Bash", "Write", "Edit"])
    assert doc["sandbox_mode"] == "workspace-write"


def test_edit_only_role_keeps_workspace_write() -> None:
    doc = _transform_codex("developer", ["Read", "Edit"])
    assert doc["sandbox_mode"] == "workspace-write"


def test_missing_tools_is_read_only() -> None:
    # Mirrors the doctor ``tools_without`` predicate: an empty/missing tool
    # list counts as "without Write/Edit".
    doc = _transform_codex("explorer", None)
    assert doc["sandbox_mode"] == "read-only"


# ---------------------------------------------------------------------------
# Mechanism is capability-gated, not provider-named
# ---------------------------------------------------------------------------

def test_role_read_only_helper() -> None:
    assert _role_read_only({"tools": ["Read", "Grep"]}) is True
    assert _role_read_only({"tools": []}) is True
    assert _role_read_only({}) is True
    assert _role_read_only({"tools": ["Read", "Write"]}) is False
    assert _role_read_only({"tools": ["Read", "Edit"]}) is False


def test_effective_extra_fields_is_capability_gated() -> None:
    spec = {
        "extra-fields": {"sandbox_mode": "workspace-write"},
        "read-only-extra-fields": {"sandbox_mode": "read-only"},
    }
    read_only_fm = {"tools": ["Read", "Grep"]}
    write_fm = {"tools": ["Read", "Write"]}
    # Non-sandbox capabilities (or a missing capability) keep the default.
    for caps in ({}, {"read_only_enforcement": "none"},
                 {"read_only_enforcement": "tools"},
                 {"read_only_enforcement": "permission-map"}):
        assert _effective_extra_fields(spec, caps, read_only_fm) == {
            "sandbox_mode": "workspace-write"}
    # sandbox applies the override for read-only roles only.
    assert _effective_extra_fields(
        spec, {"read_only_enforcement": "sandbox"}, read_only_fm
    ) == {"sandbox_mode": "read-only"}
    assert _effective_extra_fields(
        spec, {"read_only_enforcement": "sandbox"}, write_fm
    ) == {"sandbox_mode": "workspace-write"}


def test_effective_extra_fields_without_override_map_is_a_plain_copy() -> None:
    spec = {"extra-fields": {"mode": "subagent"}}
    fm = {"tools": ["Read"]}
    assert _effective_extra_fields(
        spec, {"read_only_enforcement": "sandbox"}, fm
    ) == {"mode": "subagent"}
