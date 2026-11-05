"""IC-15 Nr. 16 as amended (AC-B1/AC-B2): the OpenCode v2 settings surface
drops the top-level ``subagent_depth`` key (the v2 parser discards it), and
provider isolation never denies a provider the shared ``AGENTS.md`` core it
actively reads.

Two coupled regressions from the context-budget study (§3.3):

* The v1 ``subagent_depth`` key was dropped by the v2 settings transform, so an
  orchestrator chain fell back to depth 1. Spec Amendment B2 (2026-10-23) makes
  ``sync_opencode_v2_managed_keys`` the **single owner** of the replacement path
  ``experimental.subagent_depth`` (project option, else the capability
  ``required_depth``); the init transform only removes the dead top-level key.
  The document-level AC-B1 assertion (value under ``experimental``, no top-level
  key) therefore lives in the end-to-end Task 9 tests of
  ``tests/test_opencode_v2_surface.py``; this file pins the shape transform's
  contribution plus the deny regression.
* In a multi-provider project the shared core ``AGENTS.md`` is listed as an
  isolation-dir by some providers, so an ``AGENTS.md``-reading provider
  (``agents_md_visible_to_subagents: true``) received a ``**/AGENTS.md``
  permission deny and could no longer read the core. Isolation now skips a
  foreign isolation-dir that is the target provider's own context file when
  the capability marks it as an active reader.

Provider-agnostic by construction: behaviour is keyed on the resolved
``mcp-config.format``, the ``required_depth`` / ``agents_md_visible_to_subagents``
capabilities and the provider's declared ``context_file`` — no provider name
appears in a dispatch branch.

Run: python3 -m pytest tests/test_settings_depth_and_deny.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.context import (
    _init_provider_settings_json,
    apply_settings_surface_shape,
    init_settings_json,
)
from lib.isolation import sync_provider_isolation
from lib.log import SyncLog
from lib.providers import load_provider_capabilities, load_providers_config

_V2_PC = {
    "surface-version": "v2",
    "primary-role": "orchestrator",
    "context_file": "AGENTS.md",
    "mcp-config": {"format": "opencode-json-v2"},
}

_V2_TEMPLATE = (
    "{\n"
    "  // opencode configuration\n"
    '  "subagent_depth": 3,\n'
    "  // \"model\": \"anthropic/claude-sonnet-4-6\",\n"
    "}\n"
)

_V1_PC = {"surface-version": "v1", "mcp-config": {"format": "opencode-json"}}


# ---------------------------------------------------------------------------
# Depth: the v2 settings surface must not drop the orchestrator depth.
# ---------------------------------------------------------------------------


def test_ac_b1_v2_settings_remove_top_level_subagent_depth():
    """AC-B1 (Amendment B2): the shape removes the dead key, writes no depth.

    Single ownership: the depth is written by
    ``sync_opencode_v2_managed_keys``; the document-level assertion for the
    capability-sourced value lives in
    ``tests/test_opencode_v2_surface.py::test_ac_b1_end_to_end_capability_depth_reaches_document``.
    """
    caps = load_provider_capabilities(_REPO_ROOT)["Opencode"]
    doc = json.loads(apply_settings_surface_shape(_V2_TEMPLATE, _V2_PC, caps))
    assert "subagent_depth" not in doc, (
        "the v2 surface must not keep the top-level subagent_depth key"
    )
    assert "experimental" not in doc, (
        "single ownership (Amendment B2): the init transform must not write "
        "experimental.subagent_depth"
    )


def test_ac_b1_v2_settings_capabilities_do_not_change_shape():
    """Capabilities cannot reshape the settings document (single ownership)."""
    with_caps = apply_settings_surface_shape(_V2_TEMPLATE, _V2_PC, {"required_depth": 2})
    without_caps = apply_settings_surface_shape(_V2_TEMPLATE, _V2_PC)
    assert with_caps == without_caps
    assert "subagent_depth" not in json.loads(with_caps)


def test_v2_settings_still_emit_default_agent_from_primary_role():
    doc = json.loads(apply_settings_surface_shape(_V2_TEMPLATE, _V2_PC))
    assert doc["default_agent"] == "orchestrator"


def test_v1_settings_are_byte_identical():
    assert apply_settings_surface_shape(_V2_TEMPLATE, _V1_PC) == _V2_TEMPLATE


# ---------------------------------------------------------------------------
# Deny: an active AGENTS.md reader must not receive a **/AGENTS.md deny.
# ---------------------------------------------------------------------------


def _read_opencode(tmp_path: Path) -> dict:
    return json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))


def _denied_globs(doc: dict) -> set:
    permission = doc.get("permission") or {}
    globs = set()
    for family in ("read", "edit"):
        mapping = permission.get(family)
        if isinstance(mapping, dict):
            globs.update(k for k, v in mapping.items() if v == "deny")
    return globs


def test_agents_md_deny_skipped_for_active_reader(tmp_path):
    """Opencode reads AGENTS.md (capability true) -> no **/AGENTS.md deny."""
    provider_config = load_providers_config(_REPO_ROOT)
    sync_provider_isolation(
        tmp_path,
        ["Opencode", "Codex"],
        provider_config,
        SyncLog(),
        dry_run=False,
        agent_meta_root=_REPO_ROOT,
    )
    denied = _denied_globs(_read_opencode(tmp_path))
    assert "**/AGENTS.md" not in denied, (
        "an active AGENTS.md reader must not be denied access to the shared core"
    )
    assert ".codex/**" in denied, (
        "foreign provider directories must still be isolated"
    )


def test_agents_md_deny_kept_without_reader_capability(tmp_path):
    """No capability data -> the conservative deny is retained (fail-safe)."""
    provider_config = load_providers_config(_REPO_ROOT)
    sync_provider_isolation(
        tmp_path,
        ["Opencode", "Codex"],
        provider_config,
        SyncLog(),
        dry_run=False,
    )
    denied = _denied_globs(_read_opencode(tmp_path))
    assert "**/AGENTS.md" in denied


# ---------------------------------------------------------------------------
# #1090/D16: settings init uses the per-provider emitted-role predicate.
# ---------------------------------------------------------------------------


def _init_pc() -> dict:
    """v2 settings surface with an explicit primary role."""
    return {
        "settings_file": "opencode.json",
        "surface-version": "v2",
        "primary-role": "orchestrator",
        "mcp-config": {"format": "opencode-json-v2"},
    }


def test_init_omits_default_agent_for_provider_scoped_main_chat(tmp_path):
    """Global strict + provider-scoped main-chat must NOT write an entry point.

    The old predicate read the global ``ORCH_MODE_MAIN_CHAT`` variable and
    ignored ``orchestrator.provider-overrides``; the init function now resolves
    the mode through ``role_emitted_for_provider``.
    """
    project = tmp_path / "project"
    config = {
        "orchestrator": {
            "mode": "strict",
            "provider-overrides": {"Opencode": {"mode": "main-chat"}},
        }
    }

    _init_provider_settings_json(
        project, _init_pc(), _REPO_ROOT, {"ORCH_MODE_MAIN_CHAT": "false"},
        SyncLog(), False, provider="Opencode", config=config,
    )

    doc = json.loads((project / "opencode.json").read_text(encoding="utf-8"))
    assert "default_agent" not in doc


def test_init_keeps_default_agent_for_provider_scoped_strict(tmp_path):
    """Global main-chat + provider-scoped strict still writes the entry point."""
    project = tmp_path / "project"
    config = {
        "orchestrator": {
            "mode": "main-chat",
            "provider-overrides": {"Opencode": {"mode": "strict"}},
        }
    }

    _init_provider_settings_json(
        project, _init_pc(), _REPO_ROOT, {"ORCH_MODE_MAIN_CHAT": "true"},
        SyncLog(), False, provider="Opencode", config=config,
    )

    doc = json.loads((project / "opencode.json").read_text(encoding="utf-8"))
    assert doc["default_agent"] == "orchestrator"


def test_init_omits_default_agent_when_role_is_not_in_active_set(tmp_path):
    """The active-set allowlist is honoured too (not just the mode)."""
    project = tmp_path / "project"
    active = SimpleNamespace(
        roles=frozenset({"developer"}), known_roles=frozenset({"orchestrator", "developer"})
    )

    _init_provider_settings_json(
        project, _init_pc(), _REPO_ROOT, {}, SyncLog(), False,
        provider="Opencode", config={"orchestrator": {"mode": "strict"}},
        active_set=active,
    )

    doc = json.loads((project / "opencode.json").read_text(encoding="utf-8"))
    assert "default_agent" not in doc


def test_init_settings_json_reads_provider_mode_from_project_config(tmp_path):
    """The real sync-stage entry point (no config argument) resolves the mode."""
    project = tmp_path / "project"
    config_dir = project / ".meta-config"
    config_dir.mkdir(parents=True)
    (config_dir / "project.yaml").write_text(
        yaml.safe_dump({
            "orchestrator": {
                "mode": "strict",
                "provider-overrides": {"Opencode": {"mode": "main-chat"}},
            }
        }),
        encoding="utf-8",
    )

    init_settings_json(
        _REPO_ROOT, project, SyncLog(), False,
        providers=["Opencode"],
        provider_config={"Opencode": _init_pc()},
        variables={"ORCH_MODE_MAIN_CHAT": "false"},
    )

    doc = json.loads((project / "opencode.json").read_text(encoding="utf-8"))
    assert "default_agent" not in doc
