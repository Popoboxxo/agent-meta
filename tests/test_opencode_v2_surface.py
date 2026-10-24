"""Opencode v2 surface wiring tests.

SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, §4.1 / AC-5 / AC-21 / AC-23
(design DECISION-7; scenario 69):

``surface-version`` is config data that selects TWO declared surfaces:

  - ``mcp-config.format`` through ``mcp-config.surface-formats``
    (covered by ``tests/test_surface_version_selection.py``);
  - ``agent-transform.frontmatter-mechanism`` through
    ``agent-transform.surface-mechanisms`` (new wiring under test here,
    ``v1`` -> ``opencode-native``, ``v2`` -> ``opencode-native-v2``).

Both selections happen once, generically, in ``load_providers_config``; the
writers consume the resolved value only and never read ``surface-version``.

The v2 settings surface (``opencode.json``) drops the dead top-level
``subagent_depth`` key (IC-15 Nr. 16 as amended by
SPEC-OPENCODE-V2-SUPPORT-2026-10-22: the C0 spike showed the v2 parser discards
it) and emits ``default_agent`` from the ``primary-role`` data key.
``apply_settings_surface_shape`` dispatches on the resolved ``mcp-config.format``
value only; every non-v2 format is returned byte-for-byte so the shipped v1
surface stays frozen.

Amendment B2 (2026-10-23) — single ownership: ``experimental.subagent_depth``
is written **only** by ``sync_opencode_v2_managed_keys`` (project option, else
the capability ``required_depth``). The init transform must not write it, so a
fresh project takes merge row 1 instead of adopting an untracked value (row 3a),
a project override wins, and a v2→v1 rollback removes the key. The AC-B1
*document-level* assertion therefore lives in the end-to-end Task 9 tests below,
not in the settings-shape unit tests.

Run: python3 -m pytest tests/test_opencode_v2_surface.py -q
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
# The AC-01 harness owns the "render one project with scripts/sync.py" helper;
# the lab diff below reuses it instead of adding a second renderer.
sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_ac01_render_identity as render_harness  # noqa: E402

import lib.sync_pipeline as sync_pipeline
from lib import isolation, opencode_v2_config, provider_transform, runtime_gate
from lib.artifact_validate import resolve_artifact_contract, validate_frontmatter
from lib.consistency.artifact_contracts import check_artifact_contracts
from lib.consistency.model_contracts import check_model_contracts
from lib.context import apply_settings_surface_shape
from lib.io import SyncError
from lib.log import SyncLog
from lib.mcp_provider_config import (
    _build_connection_entry,
    _build_mcp_entries,
    _write_provider_config,
    generate_provider_configs,
)
from lib.opencode_v2_config import STATE_KEYS_KEY
from lib.providers import (
    load_provider_capabilities,
    load_providers_config,
    provider_runtime_gate_tier,
)

_SURFACE_MECHANISMS = {"v1": "opencode-native", "v2": "opencode-native-v2"}

_SETTINGS_TEMPLATE = (
    "{\n"
    "  // opencode configuration\n"
    '  "subagent_depth": 3,\n'
    "  // \"model\": \"anthropic/claude-sonnet-4-6\",\n"
    "}\n"
)


def _write_config(root: Path, providers: dict) -> None:
    """Write a minimal ``config/ai-providers.yaml`` fixture under ``root``."""
    cfg_dir = root / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "ai-providers.yaml").write_text(
        yaml.safe_dump({"providers": providers}, sort_keys=False),
        encoding="utf-8",
    )


def _opencode_like(surface: str, mechanisms: dict | None = _SURFACE_MECHANISMS) -> dict:
    transform: dict = {"frontmatter-mechanism": "opencode-native"}
    if mechanisms is not None:
        transform["surface-mechanisms"] = dict(mechanisms)
    mcp: dict = {"committed-file": "opencode.json", "format": "opencode-json"}
    mcp["surface-formats"] = {"v1": "opencode-json", "v2": "opencode-json-v2"}
    return {
        "surface-version": surface,
        "primary-role": "orchestrator",
        "mcp-config": mcp,
        "agent-transform": transform,
    }


# --- mechanism selection ----------------------------------------------------


def test_real_registry_opencode_v1_keeps_opencode_native():
    """AC-5: the committed v1 default resolves to the v1 mechanism."""
    cfg = load_providers_config(_REPO_ROOT)["Opencode"]
    assert cfg["surface-version"] == "v1"
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native"


def test_real_registry_declares_surface_mechanisms_map():
    """The mechanism selection data exists on the Opencode entry."""
    cfg = load_providers_config(_REPO_ROOT)["Opencode"]
    assert (
        cfg["agent-transform"]["surface-mechanisms"] == _SURFACE_MECHANISMS
    )


def test_v2_selects_opencode_native_v2(tmp_path):
    _write_config(tmp_path, {"Opencode": _opencode_like("v2")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"


def test_v1_selects_opencode_native(tmp_path):
    _write_config(tmp_path, {"Opencode": _opencode_like("v1")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native"


def test_absent_surface_mechanisms_leaves_declared_value(tmp_path):
    """A provider without ``surface-mechanisms`` is untouched — even on v2."""
    _write_config(
        tmp_path,
        {
            "Other": {
                "surface-version": "v2",
                "agent-transform": {"frontmatter-mechanism": "provider-md"},
            }
        },
    )
    cfg = load_providers_config(tmp_path)["Other"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "provider-md"


def test_unknown_surface_version_keeps_declared_mechanism(tmp_path):
    _write_config(tmp_path, {"Opencode": _opencode_like("v3")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native"


def test_mechanism_selection_is_provider_name_agnostic(tmp_path):
    """Selection keys off the declared data (map + version), not the name."""
    _write_config(
        tmp_path,
        {
            "FutureProvider": {
                "surface-version": "v2",
                "agent-transform": {
                    "frontmatter-mechanism": "placeholder",
                    "surface-mechanisms": _SURFACE_MECHANISMS,
                },
            }
        },
    )
    cfg = load_providers_config(tmp_path)["FutureProvider"]
    assert cfg["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"


def test_mechanism_selection_does_not_leak_to_neighbours(tmp_path):
    _write_config(
        tmp_path,
        {
            "Mapped": _opencode_like("v2"),
            "Plain": {
                "surface-version": "v2",
                "agent-transform": {"frontmatter-mechanism": "codex-toml"},
            },
        },
    )
    cfg = load_providers_config(tmp_path)
    assert cfg["Mapped"]["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"
    assert cfg["Plain"]["agent-transform"]["frontmatter-mechanism"] == "codex-toml"


# --- v2 settings surface ----------------------------------------------------


def _pc_v2() -> dict:
    return {
        "surface-version": "v2",
        "primary-role": "orchestrator",
        "mcp-config": {"format": "opencode-json-v2"},
    }


def test_ac_b1_v2_settings_remove_top_level_subagent_depth_and_emit_default_agent():
    """AC-B1 (Amendment B2): the settings shape removes the dead key only.

    Single ownership: ``experimental.subagent_depth`` is written by
    ``sync_opencode_v2_managed_keys``, so the init transform must not create an
    ``experimental`` block (the document-level assertion lives in the Task 9
    end-to-end test below).
    """
    out = apply_settings_surface_shape(_SETTINGS_TEMPLATE, _pc_v2())
    doc = json.loads(out)
    assert "subagent_depth" not in doc, (
        "the v2 surface must not carry a top-level subagent_depth key (the v2 "
        "parser discards it)"
    )
    assert "experimental" not in doc, (
        "single ownership (Amendment B2): the settings shape must not write "
        "experimental.subagent_depth — the managed-merge writer owns it"
    )
    assert doc["default_agent"] == "orchestrator"


def test_ac_b1_v2_settings_ignore_capabilities_single_ownership():
    """Single ownership: a resolved ``required_depth`` cannot make this writer act.

    The capability-sourced value is asserted end-to-end against the managed
    writer (``test_ac_b1_end_to_end_capability_depth_reaches_document``).
    """
    doc = json.loads(
        apply_settings_surface_shape(_SETTINGS_TEMPLATE, _pc_v2(), {"required_depth": 2})
    )
    assert "subagent_depth" not in doc
    assert "experimental" not in doc


def test_v2_settings_default_agent_comes_from_primary_role():
    pc = _pc_v2()
    pc["primary-role"] = "developer"
    doc = json.loads(apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc))
    assert doc["default_agent"] == "developer"


def test_ac_b1_v2_settings_without_primary_role_emits_no_default_agent():
    pc = _pc_v2()
    pc.pop("primary-role")
    doc = json.loads(apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc))
    assert "subagent_depth" not in doc
    assert "experimental" not in doc
    assert "default_agent" not in doc


def test_v1_settings_template_is_byte_identical():
    """The shipped v1 surface must stay frozen, comments included."""
    pc = {"surface-version": "v1", "mcp-config": {"format": "opencode-json"}}
    assert apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc) == _SETTINGS_TEMPLATE


def test_ac_b2_v1_settings_unchanged():
    """AC-B2: the v2 key migration must not leak into the v1 surface.

    The authoritative v1 freeze is ``test_v1_settings_template_is_byte_identical``;
    this test additionally passes capability data to prove that even a resolved
    ``required_depth`` cannot reshape v1 (no ``experimental`` block, top-level
    ``subagent_depth`` untouched).
    """
    pc = {"surface-version": "v1", "mcp-config": {"format": "opencode-json"}}
    out = apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc, {"required_depth": 2})
    assert out == _SETTINGS_TEMPLATE
    assert '"experimental"' not in out


def test_non_v2_format_is_byte_identical():
    pc = {"surface-version": "v2", "mcp-config": {"format": "gemini-settings"}}
    assert apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc) == _SETTINGS_TEMPLATE


def test_unparseable_template_is_returned_unchanged():
    pc = _pc_v2()
    broken = "{ not valid json"
    assert apply_settings_surface_shape(broken, pc) == broken


# --- AC-D8: evidence for opencode.json / opencode.jsonc loading --------------


def test_ac_d8_evidence_present_with_result_line():
    """AC-D8: the jsonc-loading evidence exists and states one clear result.

    Guards plan Task 24 (spec §3.9): before ``opencode.jsonc`` may be removed
    from the repo root, the evidence document must exist and carry exactly one
    ``ERGEBNIS:`` line, so the removal decision has a single, greppable verdict.
    """
    evidence = (
        _REPO_ROOT / "docs/analysis/evidence/2026-10-22-opencode-jsonc-loading.md"
    )
    assert evidence.is_file(), f"missing AC-D8 evidence: {evidence}"

    result_lines = [
        line
        for line in evidence.read_text(encoding="utf-8").splitlines()
        if line.startswith("ERGEBNIS:")
    ]
    assert len(result_lines) == 1, (
        f"expected exactly one 'ERGEBNIS:' line, found {len(result_lines)}: "
        f"{result_lines}"
    )
    assert result_lines[0].strip() in {
        "ERGEBNIS: JSONC-TRAEGT-NICHTS-BEI",
        "ERGEBNIS: JSONC-TRAEGT-INHALT-BEI",
    }


def test_ac_d8_repo_root_has_no_opencode_jsonc():
    """AC-D8 (Task 26): the repo root keeps only the managed ``opencode.json``.

    The evidence for Task 24 resolved ``ERGEBNIS: JSONC-TRAEGT-NICHTS-BEI``:
    ``opencode.jsonc`` carried nothing but comments and a ``$schema`` value
    already present in ``opencode.json``, while a content-bearing JSONC would
    *override* the managed JSON (v1 and v2 probe). So the duplicate is removed
    instead of migrated — and it must not come back, because recreating it
    would re-open the shadowing risk for this repo itself.

    The evidence file is asserted too: the removal decision stays traceable.
    """
    evidence = (
        _REPO_ROOT / "docs/analysis/evidence/2026-10-22-opencode-jsonc-loading.md"
    )
    assert evidence.is_file(), f"missing AC-D8 evidence: {evidence}"
    assert not (_REPO_ROOT / "opencode.jsonc").exists(), (
        "the repo root must not carry a duplicate opencode.jsonc next to the "
        "managed opencode.json (AC-D8, evidence 2026-10-22-opencode-jsonc-loading)"
    )


# ===========================================================================
# Phase B / Task 9 (B.6): ``sync_opencode_v2_managed_keys`` (file I/O)
# ===========================================================================
#
# The decision table itself (spec §3.2 rows 1…4a) is pinned in
# ``tests/test_opencode_v2_config.py``. These tests pin the I/O layer around it:
# ownership-first provider binding (N-M2), the provider-derived file/state paths,
# the state encoding, empty-container pruning on rollback, the two-stage secret
# gate and dry-run/data-loss protection (AC-B4/5/6/7/8/14/15/16/17/19/20, AC-T7).

_V2_STATE_REL = Path(".opencode") / "agent-meta-state.json"


def _mcp_block(active_surface: str = "v2") -> dict:
    """Resolved ``mcp-config`` of a registry entry that offers both surfaces.

    Ownership is independent of the active surface: ``surface-formats`` and
    ``committed-file`` are declared on the entry either way (spec §3.2, N-M2).
    """
    return {
        "format": "opencode-json-v2" if active_surface == "v2" else "opencode-json",
        "committed-file": "opencode.json",
        "surface-formats": {"v1": "opencode-json", "v2": "opencode-json-v2"},
    }


def _v2_pc() -> dict:
    return {
        "primary-role": "orchestrator",
        "mcp-config": _mcp_block("v2"),
        "agent-transform": {"frontmatter-mechanism": "opencode-native-v2"},
        # Resolved by ``providers._apply_surface_aux_selection`` (Task 6); the
        # v1 entry carries no such key, which is exactly AC-D7's "no file" case.
        "cli_file": "cli.json",
    }


def _v1_pc() -> dict:
    return {
        "primary-role": "orchestrator",
        "mcp-config": _mcp_block("v1"),
        "agent-transform": {"frontmatter-mechanism": "opencode-native"},
    }


def _v1_pc_with_cli_files() -> dict:
    """A v1 entry as the loader leaves it: no ``cli_file``, surface map survives.

    ``providers._apply_surface_aux_selection`` only *adds* the flat
    ``cli_file`` for the active surface; the registry-level ``cli-files`` map
    stays on the entry (spec §3.1), so a v2→v1 rollback can still name the file
    a previous v2 surface wrote.
    """
    pc = _v1_pc()
    pc["cli-files"] = {"v2": _CLI_FILE}
    return pc


def _config(depth: int | None = None, **options) -> dict:
    """Project config with the Opencode v2 options; no depth ⇒ capability default."""
    block = dict(options)
    if depth is not None:
        block["experimental-subagent-depth"] = depth
    return {"provider-options": {"Opencode": block}}


def _write_json(path: Path, data: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return path


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_state_doc(project_root: Path) -> dict:
    path = project_root / _V2_STATE_REL
    return _read_json(path) if path.exists() else {}


def _write_capabilities(root: Path, provider: str, required_depth: int) -> Path:
    """Framework root whose capability registry declares ``required_depth``."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "provider-capabilities.yaml").write_text(
        yaml.safe_dump({"capabilities": {provider: {"required_depth": required_depth}}}),
        encoding="utf-8",
    )
    return root


def _run(
    project_root: Path,
    config: dict,
    providers: dict,
    framework: Path,
    log: SyncLog | None = None,
    dry_run: bool = False,
    provider: str = "Opencode",
    claimed_files: set[str] | None = None,
) -> SyncLog:
    log = log if log is not None else SyncLog()
    opencode_v2_config.sync_opencode_v2_managed_keys(
        project_root, config, provider, providers, framework, log, dry_run,
        claimed_files=claimed_files if claimed_files is not None else set(),
    )
    return log


def _warned(log: SyncLog, message: str) -> bool:
    """True when *message* appears in the log (entries carry a ``[WARN]`` prefix)."""
    return any(message in warning for warning in log.warnings)


def _v2_settings_shape() -> str:
    """The document the init transform produces for the v2 settings template."""
    return apply_settings_surface_shape(
        _SETTINGS_TEMPLATE,
        {
            "primary-role": "orchestrator",
            "mcp-config": {"format": "opencode-json-v2"},
        },
    )


def test_ac_b1_end_to_end_single_writer_owns_depth_and_rollback(tmp_path):
    """AC-B1 + QA-B-01: init shape + managed writer, one owner of the depth.

    A fresh v2 project first runs the settings transform (which only removes the
    dead top-level key) and then the managed writer with an explicit project
    depth. The result must take merge row 1 — value written, state recorded,
    no ``opencode-v2-managed`` warning. Since the init no longer pre-writes the
    depth, the writer cannot mistake it for an untracked equal user value
    (row 3a). A v2→v1 rollback then removes the key and empties the namespace.
    """
    project = tmp_path / "project"
    project.mkdir()
    shaped = _v2_settings_shape()
    (project / "opencode.json").write_text(shaped, encoding="utf-8")
    assert "subagent_depth" not in json.loads(shaped)

    log = _run(project, _config(3), {"Opencode": _v2_pc()}, tmp_path / "fw")

    doc = _read_json(project / "opencode.json")
    assert doc["experimental"]["subagent_depth"] == 3
    assert "subagent_depth" not in doc, (
        "the v2 parser discards the top-level key; it must stay removed"
    )
    assert doc["default_agent"] == "orchestrator"
    assert not _warned(log, "opencode-v2-managed"), log.warnings
    assert _read_state_doc(project)[STATE_KEYS_KEY]["experimental.subagent_depth"] == {
        "value": 3,
        "prior": None,
        "prior_absent": True,
    }

    _run(project, _config(3), {"Opencode": _v1_pc()}, tmp_path / "fw")

    rolled_back = _read_json(project / "opencode.json")
    assert "experimental" not in rolled_back, (
        "row 4 rollback must delete the depth and prune the empty container"
    )
    assert "subagent_depth" not in rolled_back
    assert STATE_KEYS_KEY not in _read_state_doc(project)


def test_ac_b1_end_to_end_capability_depth_reaches_document(tmp_path):
    """AC-B1: without a project option the capability ``required_depth`` wins.

    Relocated from the settings-shape unit test: the value is produced by the
    single owner (``build_managed_keys``), not by the init transform.
    """
    project = tmp_path / "project"
    project.mkdir()
    (project / "opencode.json").write_text(_v2_settings_shape(), encoding="utf-8")
    framework = _write_capabilities(tmp_path / "fw", "Opencode", 2)

    log = _run(project, _config(), {"Opencode": _v2_pc()}, framework)

    doc = _read_json(project / "opencode.json")
    assert doc["experimental"]["subagent_depth"] == 2
    assert doc["experimental"]["subagent_depth"] >= 2
    # QA-B2-04: bind the produced document to the *shipped* registry value
    # instead of the fixture number, read at test time (never hardcoded).
    assert doc["experimental"]["subagent_depth"] == (
        load_provider_capabilities(_REPO_ROOT)["Opencode"]["required_depth"]
    )
    assert "subagent_depth" not in doc
    assert not _warned(log, "opencode-v2-managed"), log.warnings


def test_ac_b1_review_single_ownership_e2e_adopt_change_rollback(tmp_path):
    """QA-B-12: row 3a (adopt) → row 2 (value change) → rollback restores prior.

    The document starts with the target value as an *untracked* user value, so
    the first sync adopts it (no write, no warning, ``prior == value``). A later
    option change updates the value (row 2, prior kept), and the v1 rollback
    restores the original prior instead of deleting the key.
    """
    project = tmp_path / "project"
    _write_json(project / "opencode.json", {"experimental": {"subagent_depth": 3}})
    before = (project / "opencode.json").read_bytes()
    providers = {"Opencode": _v2_pc()}

    adopted = _run(project, _config(3), providers, tmp_path / "fw")

    assert (project / "opencode.json").read_bytes() == before, (
        "row 3a adopts silently and must not rewrite the document"
    )
    assert not _warned(adopted, "opencode-v2-managed"), adopted.warnings
    assert _read_state_doc(project)[STATE_KEYS_KEY]["experimental.subagent_depth"] == {
        "value": 3,
        "prior": 3,
        "prior_absent": False,
    }

    _run(project, _config(4), providers, tmp_path / "fw")

    assert _read_json(project / "opencode.json")["experimental"]["subagent_depth"] == 4
    assert _read_state_doc(project)[STATE_KEYS_KEY]["experimental.subagent_depth"] == {
        "value": 4,
        "prior": 3,
        "prior_absent": False,
    }

    _run(project, _config(4), {"Opencode": _v1_pc()}, tmp_path / "fw")

    assert _read_json(project / "opencode.json")["experimental"]["subagent_depth"] == 3
    assert STATE_KEYS_KEY not in _read_state_doc(project)


def test_ac_b11_schema_preserved_through_v2_merge(tmp_path):
    """RVW-B-02: an existing ``$schema`` survives a v2 merge byte-exactly."""
    project = tmp_path / "project"
    schema_url = "https://example.invalid/opencode-schema.json"
    _write_json(
        project / "opencode.json",
        {"$schema": schema_url, "theme": "dark"},
    )

    _run(project, _config(3), {"Opencode": _v2_pc()}, tmp_path / "fw")

    raw = (project / "opencode.json").read_text(encoding="utf-8")
    assert f'"$schema": "{schema_url}"' in raw
    assert _read_json(project / "opencode.json")["$schema"] == schema_url


def test_ac_b5_non_dict_ancestor_is_kept_with_warning(tmp_path):
    """QA-B-03: a non-object ancestor is never clobbered to reach a leaf."""
    project = tmp_path / "project"
    user_doc = {"experimental": "legacy-user-value", "theme": "dark"}
    _write_json(project / "opencode.json", user_doc)
    before = (project / "opencode.json").read_bytes()

    log = _run(
        project,
        _config(**{"experimental-todo": True}),
        {"Opencode": _v2_pc()},
        tmp_path / "fw",
    )

    assert (project / "opencode.json").read_bytes() == before, (
        "a scalar under the container name is user data and must survive"
    )
    assert _read_json(project / "opencode.json")["experimental"] == "legacy-user-value"
    assert _warned(
        log, "opencode-v2-managed: experimental.todo user value kept"
    ), log.warnings
    assert STATE_KEYS_KEY not in _read_state_doc(project)


def test_ac_b4_user_keys_survive_managed_merge(tmp_path):
    """AC-B4: user keys (plugin/instructions/model/mcp) survive the merge.

    Only the explicitly managed paths may change; unknown top-level keys and
    nested user structures stay exactly as they were (spec §3.2 rule 5).
    """
    project = tmp_path / "project"
    user_doc = {
        "plugin": ["acme.js"],
        "instructions": ["AGENTS.md"],
        "model": "opencode-go/deepseek-v4-pro",
        "subagent_depth": 9,
        "mcp": {"servers": {"my-own": {"type": "local", "command": ["x"]}}},
    }
    _write_json(project / "opencode.json", user_doc)
    provider_value = {
        "name": "opencode-go",
        "env": ["OC_API_KEY"],
        "settings": {"baseURL": "https://example.invalid/v1"},
    }

    _run(
        project,
        _config(3, providers={"opencode-go": provider_value}),
        {"Opencode": _v2_pc()},
        tmp_path / "fw",
    )

    doc = _read_json(project / "opencode.json")
    for key in ("plugin", "instructions", "model", "subagent_depth", "mcp"):
        assert doc[key] == user_doc[key], f"user key {key!r} was modified"
    assert doc["experimental"]["subagent_depth"] == 3
    assert doc["providers"]["opencode-go"] == provider_value


def test_ac_b5_user_value_kept_with_warning(tmp_path):
    """AC-B5 (row 3): an unmanaged user value wins and produces the warning."""
    project = tmp_path / "project"
    _write_json(project / "opencode.json", {"experimental": {"subagent_depth": 7}})

    log = _run(project, _config(3), {"Opencode": _v2_pc()}, tmp_path / "fw")

    doc = _read_json(project / "opencode.json")
    assert doc["experimental"]["subagent_depth"] == 7
    assert _warned(
        log, "opencode-v2-managed: experimental.subagent_depth user value kept"
    )
    assert STATE_KEYS_KEY not in _read_state_doc(project)


def test_ac_b6_capability_change_updates_value(tmp_path):
    """AC-B6 (row 2): our own value is updated when the capability changes."""
    project = tmp_path / "project"
    framework = _write_capabilities(tmp_path / "fw", "Opencode", 3)
    providers = {"Opencode": _v2_pc()}

    _run(project, _config(), providers, framework)
    doc = _read_json(project / "opencode.json")
    assert doc["experimental"]["subagent_depth"] == 3
    state = _read_state_doc(project)[STATE_KEYS_KEY]
    assert state["experimental.subagent_depth"] == {
        "value": 3,
        "prior": None,
        "prior_absent": True,
    }

    _write_capabilities(framework, "Opencode", 4)
    _run(project, _config(), providers, framework)

    doc = _read_json(project / "opencode.json")
    assert doc["experimental"]["subagent_depth"] == 4
    state = _read_state_doc(project)[STATE_KEYS_KEY]
    assert state["experimental.subagent_depth"] == {
        "value": 4,
        "prior": None,
        "prior_absent": True,
    }


def test_ac_b7_v2_to_v1_removes_managed_keys_and_empty_containers(tmp_path):
    """AC-B7 (rows 4/4a): rollback removes managed keys, prunes empty parents.

    A user value that was changed by hand survives with its warning (row 4a);
    an unrelated user ``agents.title`` object is never special-cased.
    """
    clean = tmp_path / "clean"
    provider_value = {"name": "opencode-go", "env": ["OC_API_KEY"]}
    user_doc = {"theme": "dark", "agents": {"title": {"name": "user-title"}}}
    _write_json(clean / "opencode.json", user_doc)

    v2_config = _config(
        3, **{"experimental-todo": True, "providers": {"opencode-go": provider_value}}
    )
    _run(clean, v2_config, {"Opencode": _v2_pc()}, tmp_path / "fw")
    written = _read_json(clean / "opencode.json")
    assert written["experimental"] == {"subagent_depth": 3, "todo": True}
    assert written["providers"]["opencode-go"] == provider_value

    _run(clean, _config(3), {"Opencode": _v1_pc()}, tmp_path / "fw")

    doc = _read_json(clean / "opencode.json")
    assert "experimental" not in doc
    assert "providers" not in doc
    assert doc["theme"] == user_doc["theme"]
    assert doc["agents"] == user_doc["agents"]
    assert STATE_KEYS_KEY not in _read_state_doc(clean)

    changed = tmp_path / "changed"
    _run(changed, _config(3), {"Opencode": _v2_pc()}, tmp_path / "fw")
    user_edited = _read_json(changed / "opencode.json")
    user_edited["experimental"]["subagent_depth"] = 9
    _write_json(changed / "opencode.json", user_edited)

    log = _run(changed, _config(3), {"Opencode": _v1_pc()}, tmp_path / "fw")

    kept = _read_json(changed / "opencode.json")
    assert kept["experimental"]["subagent_depth"] == 9, "row 4a must not restore/overwrite"
    assert _warned(
        log, "opencode-v2-managed: experimental.subagent_depth user value kept"
    )
    assert STATE_KEYS_KEY not in _read_state_doc(changed)


def test_ac_b8_second_run_is_byte_identical(tmp_path):
    """AC-B8: a second sync without changes leaves file and state byte-identical."""
    project = tmp_path / "project"
    config = _config(3, **{"experimental-todo": True})
    providers = {"Opencode": _v2_pc()}

    _run(project, config, providers, tmp_path / "fw")
    file_bytes = (project / "opencode.json").read_bytes()
    state_bytes = (project / _V2_STATE_REL).read_bytes()

    _run(project, config, providers, tmp_path / "fw")

    assert (project / "opencode.json").read_bytes() == file_bytes
    assert (project / _V2_STATE_REL).read_bytes() == state_bytes


def test_ac_b14_dry_run_writes_nothing(tmp_path):
    """AC-B14 (rule 7): dry-run writes neither the file nor the state, but logs."""
    project = tmp_path / "project"
    project.mkdir()

    log = _run(
        project,
        _config(3, **{"experimental-todo": True}),
        {"Opencode": _v2_pc()},
        tmp_path / "fw",
        dry_run=True,
    )

    assert not (project / "opencode.json").exists()
    assert not (project / _V2_STATE_REL).exists()
    assert any("opencode.json" in action for action in log.actions), log.actions


def test_ac_b15_broken_json_writes_nothing_and_warns(tmp_path):
    """AC-B15 (rule 6): an unparseable file is never overwritten, only warned."""
    project = tmp_path / "project"
    broken = project / "opencode.json"
    broken.parent.mkdir(parents=True)
    broken.write_text("{ not valid json", encoding="utf-8")
    before = broken.read_bytes()

    log = _run(project, _config(3), {"Opencode": _v2_pc()}, tmp_path / "fw")

    assert broken.read_bytes() == before
    assert not (project / _V2_STATE_REL).exists()
    assert any("could not parse JSON" in warning for warning in log.warnings), log.warnings


def test_ac_b16_namespace_isolation_no_clobber(tmp_path):
    """AC-B16: the writer touches only ``opencode-v2-keys``; siblings stay put."""
    project = tmp_path / "project"
    _write_json(
        project / "opencode.json",
        {"experimental": {"subagent_depth": 3}},
    )
    sibling_isolation = ["**/.claude/**"]
    sibling_gate = {"**": {"edit": None, "bash": None}}
    _write_json(
        project / _V2_STATE_REL,
        {
            "isolation-deny": sibling_isolation,
            "runtime-gate-deny": sibling_gate,
            STATE_KEYS_KEY: {
                "experimental.subagent_depth": {
                    "value": 3,
                    "prior": None,
                    "prior_absent": True,
                }
            },
        },
    )
    before = _read_json(project / _V2_STATE_REL)

    _run(project, _config(3), {"Opencode": _v2_pc()}, tmp_path / "fw")

    after = _read_json(project / _V2_STATE_REL)
    assert after["isolation-deny"] == sibling_isolation
    assert after["runtime-gate-deny"] == sibling_gate
    assert after[STATE_KEYS_KEY] == before[STATE_KEYS_KEY]
    assert set(after[STATE_KEYS_KEY]) == {"experimental.subagent_depth"}
    assert isinstance(isolation._read_state(project / _V2_STATE_REL, STATE_KEYS_KEY), dict)

    file_bytes = (project / "opencode.json").read_bytes()
    state_bytes = (project / _V2_STATE_REL).read_bytes()
    _run(project, _config(3), {"Opencode": _v2_pc()}, tmp_path / "fw")
    assert (project / "opencode.json").read_bytes() == file_bytes
    assert (project / _V2_STATE_REL).read_bytes() == state_bytes
    assert _read_json(project / _V2_STATE_REL)["isolation-deny"] == sibling_isolation


def test_ac_b17_equal_user_value_no_warning_and_survives_rollback(tmp_path):
    """AC-B17 (rows 3a/4): an equal user value is adopted silently and kept."""
    project = tmp_path / "project"
    _write_json(project / "opencode.json", {"experimental": {"todo": True}})
    before = (project / "opencode.json").read_bytes()
    providers = {"Opencode": _v2_pc()}

    log = _run(project, _config(**{"experimental-todo": True}), providers, tmp_path / "fw")

    assert (project / "opencode.json").read_bytes() == before
    assert log.warnings == [], log.warnings
    assert _read_state_doc(project)[STATE_KEYS_KEY]["experimental.todo"] == {
        "value": True,
        "prior": True,
        "prior_absent": False,
    }

    _run(project, _config(**{"experimental-todo": True}), {"Opencode": _v1_pc()}, tmp_path / "fw")

    assert _read_json(project / "opencode.json")["experimental"]["todo"] is True
    assert STATE_KEYS_KEY not in _read_state_doc(project)


def test_ac_b19_user_deleted_key_not_rewritten(tmp_path):
    """AC-B19 (row 3c): a user-deleted managed key stays deleted, with warning."""
    project = tmp_path / "project"
    providers = {"Opencode": _v2_pc()}
    _run(project, _config(3), providers, tmp_path / "fw")
    assert _read_json(project / "opencode.json")["experimental"]["subagent_depth"] == 3

    # The user removes the managed key (and the now-empty container) by hand.
    _write_json(project / "opencode.json", {"theme": "dark"})
    before = (project / "opencode.json").read_bytes()

    log = _run(project, _config(3), providers, tmp_path / "fw")

    assert (project / "opencode.json").read_bytes() == before, (
        "row 3c must not rewrite or reformat the document"
    )
    doc = _read_json(project / "opencode.json")
    assert "experimental" not in doc
    assert _warned(
        log, "opencode-v2-managed: experimental.subagent_depth user value kept"
    )
    assert _read_state_doc(project)[STATE_KEYS_KEY]["experimental.subagent_depth"] == {
        "value": 3,
        "prior": None,
        "prior_absent": True,
    }


def test_ac_t7_plaintext_apikey_blocks_write_and_reports_in_dry_run(tmp_path):
    """AC-T7: a plaintext credential under ``providers`` blocks, even in dry-run.

    Detection is by KEY NAME (``X-Api-Key`` contains ``key``), never by the
    concrete value; ``{env:VAR}`` values stay valid (spec §3.3).
    """
    plaintext = _config(
        3,
        providers={
            "x": {
                "settings": {"baseURL": "https://example.invalid/v1"},
                "headers": {"X-Api-Key": "EXAMPLE_NOT_A_KEY"},
            }
        },
    )
    finding = "opencode-v2-secret-plaintext: providers.x.headers.X-Api-Key"

    dry_project = tmp_path / "dry"
    dry_project.mkdir()
    dry_log = _run(
        dry_project,
        plaintext,
        {"Opencode": _v2_pc()},
        tmp_path / "fw",
        dry_run=True,
    )
    assert not (dry_project / "opencode.json").exists()
    assert any(finding in error for error in dry_log.errors), dry_log.errors

    real_project = tmp_path / "real"
    real_project.mkdir()
    real_log = _run(real_project, plaintext, {"Opencode": _v2_pc()}, tmp_path / "fw")
    assert not (real_project / "opencode.json").exists()
    assert any(finding in error for error in real_log.errors), real_log.errors

    # Positive control: baseURL + {env:VAR} indirection is valid and is written.
    ok_project = tmp_path / "ok"
    ok_project.mkdir()
    valid_provider = {
        "settings": {"baseURL": "https://example.invalid/v1"},
        "env": ["OC_API_KEY"],
    }
    _run(
        ok_project,
        _config(3, providers={"x": valid_provider}),
        {"Opencode": _v2_pc()},
        tmp_path / "fw",
    )
    doc = _read_json(ok_project / "opencode.json")
    assert doc["providers"]["x"]["env"] == ["OC_API_KEY"]


def test_writer_passes_secret_gate_params_to_write_checked(tmp_path, monkeypatch):
    """The writer delegates the secret gate to ``io.write_checked`` (not a copy).

    The call must carry ``allow_secrets``, ``verify_gitignored``, ``config`` and
    ``dry_run`` — a variant that only calls ``find_plaintext_secrets`` is
    explicitly not sufficient (spec §3.3, plan global constraint).
    """
    calls = []

    def fake_write_checked(path, content, log, rel_label, **kwargs):
        calls.append((path, content, rel_label, kwargs))
        return True

    monkeypatch.setattr(opencode_v2_config.io, "write_checked", fake_write_checked)
    providers = {"Opencode": _v2_pc()}
    config = _config(3, **{"experimental-todo": True})

    plain_project = tmp_path / "plain"
    plain_project.mkdir()
    _run(plain_project, config, providers, tmp_path / "fw", dry_run=False)

    allowed_project = tmp_path / "allowed"
    allowed_project.mkdir()
    _run(
        allowed_project,
        {**config, "allow-committed-secrets": True},
        providers,
        tmp_path / "fw",
        dry_run=False,
    )

    assert len(calls) == 2, calls
    _, content, rel_label, kwargs = calls[0]
    assert rel_label == "opencode.json"
    assert content.endswith("\n")
    assert json.loads(content)["experimental"]["todo"] is True
    assert set(kwargs) >= {"allow_secrets", "verify_gitignored", "config", "dry_run"}
    assert kwargs["allow_secrets"] is False
    assert kwargs["verify_gitignored"] is False
    assert kwargs["config"] == config
    assert kwargs["dry_run"] is False
    assert calls[1][3]["allow_secrets"] is True


def test_ac_b20_non_owner_provider_is_noop_even_with_state(tmp_path, monkeypatch):
    """AC-B20 (N-M2): a non-owner is a no-op *before* the state is read.

    The read spy makes the test non-vacuous: moving the ownership guard behind
    the state read makes this test fail instead of silently passing.
    """
    project = tmp_path / "project"
    file_path = project / "opencode.json"
    _write_json(file_path, {"theme": "dark", "experimental": {"subagent_depth": 3}})
    _write_json(
        project / _V2_STATE_REL,
        {
            "isolation-deny": ["**/.claude/**"],
            STATE_KEYS_KEY: {
                "experimental.subagent_depth": {
                    "value": 3,
                    "prior": None,
                    "prior_absent": True,
                }
            },
        },
    )
    file_before = file_path.read_bytes()
    state_before = (project / _V2_STATE_REL).read_bytes()
    non_owner = {
        "Claude": {
            "mcp-config": {"format": "claude-settings", "committed-file": ".mcp.json"}
        }
    }

    def _forbidden(*args, **kwargs):
        raise AssertionError("state must not be read for a non-owner provider")

    monkeypatch.setattr(isolation, "_read_state", _forbidden)

    log = SyncLog()
    _run(project, _config(3), non_owner, tmp_path / "fw", log=log, provider="Claude")

    assert file_path.read_bytes() == file_before
    assert (project / _V2_STATE_REL).read_bytes() == state_before
    assert log.actions == [] and log.warnings == [] and log.errors == []
    assert log.skipped == [] and log.infos == []


# ===========================================================================
# Phase B / Task 10 (B.7): tier-independent wiring + N-M2 owner conflict
# ===========================================================================
#
# The writer itself is pinned by the Task 9 tests above. These tests pin the
# *sync seam*: the writer runs in EVERY provider iteration, outside the
# ``provider_runtime_gate_tier(...) == "permission"`` call condition (Spec-A
# freeze), warns about v2-only project options on a non-v2 surface (AC-B13) and
# lets exactly one owner per managed file act per run (N-M2 / AC-B20).


def _non_owner_pc() -> dict:
    """A provider entry without a selectable v2 surface (Claude-shaped data)."""
    return {
        "mcp-config": {"format": "claude-settings", "committed-file": ".mcp.json"}
    }


def _stage_framework(tmp_path: Path, tiers: dict) -> Path:
    """Minimal framework root whose capability registry declares the tiers."""
    root = tmp_path / "framework"
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "provider-capabilities.yaml").write_text(
        yaml.safe_dump(
            {"capabilities": {provider: {"runtime_gate": tier}
                              for provider, tier in tiers.items()}}
        ),
        encoding="utf-8",
    )
    return root


def _run_stage(
    tmp_path: Path,
    monkeypatch,
    provider_config: dict,
    providers: list,
    config: dict,
    tiers: dict,
    log: SyncLog | None = None,
    gate_calls: list | None = None,
    plugin_calls: list | None = None,
) -> tuple[Path, SyncLog, list]:
    """Drive ``_sync_stage_per_provider`` with every unrelated writer stubbed.

    Returns ``(project_root, log, gate_calls)``; ``gate_calls`` records the
    Spec-A runtime-gate writer, so a test can prove a tier did not dispatch it
    while the v2 managed-key writer still ran (AC-B18). ``plugin_calls`` is an
    optional out-parameter that records the capability-gated plugin writer, so
    a test can pin the ``has_plugins`` dispatch of the same seam (QA-D-01)
    instead of calling the writer directly.
    """
    root = _stage_framework(tmp_path, tiers)
    project_root = tmp_path / "project"
    project_root.mkdir(parents=True, exist_ok=True)
    log = log if log is not None else SyncLog()
    calls = gate_calls if gate_calls is not None else []
    plugin_dispatches = plugin_calls if plugin_calls is not None else []

    monkeypatch.setattr(sync_pipeline, "sync_agents_for_provider", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_prompts_for_continue", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_rules", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_speech_mode", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_embedded_rule_files", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "generate_mcp_artifacts", lambda *a, **k: [])
    monkeypatch.setattr(
        sync_pipeline, "generate_external_tool_artifacts", lambda *a, **k: []
    )
    monkeypatch.setattr(
        sync_pipeline, "sync_snippets_for_provider", lambda *a, **k: None
    )
    monkeypatch.setattr(
        sync_pipeline, "sync_external_skills_for_provider", lambda *a, **k: None
    )
    monkeypatch.setattr(
        sync_pipeline, "sweep_orphan_skill_channel_rules", lambda *a, **k: None
    )
    monkeypatch.setattr(
        sync_pipeline, "_sync_opencode_runtime_gate",
        lambda *a, **k: calls.append((a, k)),
    )
    monkeypatch.setattr(
        sync_pipeline, "sync_runtime_gate_plugins",
        lambda *a, **k: plugin_dispatches.append((a, k)),
    )

    import lib.external_tools as external_tools_module
    import lib.mcp as mcp_module

    monkeypatch.setattr(mcp_module, "load_mcp_registry", lambda *a, **k: {})
    monkeypatch.setattr(
        external_tools_module, "load_external_tools_registry", lambda *a, **k: {}
    )

    sync_pipeline._sync_stage_per_provider(
        root, project_root, config, provider_config, list(providers), {},
        None, False, False, [], argparse.Namespace(dry_run=False), log, None,
    )
    return project_root, log, calls


def test_ac_b13_option_ignored_on_non_v2_with_warning_and_no_write(
    tmp_path, monkeypatch
):
    """AC-B13: a v2-only project option on a non-v2 surface warns, writes nothing."""
    config = _config(3, **{"experimental-todo": True})

    project, log, _ = _run_stage(
        tmp_path, monkeypatch, {"Opencode": _v1_pc()}, ["Opencode"],
        config, {"Opencode": "advisory"},
    )

    assert not (project / "opencode.json").exists()
    assert not (project / _V2_STATE_REL).exists()
    assert _warned(
        log,
        "opencode-v2-option-ignored: experimental-todo requires surface-version v2",
    ), log.warnings
    assert _warned(
        log,
        "opencode-v2-option-ignored: experimental-subagent-depth"
        " requires surface-version v2",
    ), log.warnings


def test_ac_b18_managed_key_written_under_advisory_tier(tmp_path, monkeypatch):
    """AC-B18: the managed-key writer is not gated by the permission tier."""
    config = _config(3, **{"experimental-todo": True})

    project, _, gate_calls = _run_stage(
        tmp_path, monkeypatch, {"Opencode": _v2_pc()}, ["Opencode"],
        config, {"Opencode": "advisory"},
    )

    assert gate_calls == [], "advisory must not dispatch the Spec-A gate writer"
    doc = _read_json(project / "opencode.json")
    assert doc["experimental"] == {"subagent_depth": 3, "todo": True}
    assert STATE_KEYS_KEY in _read_state_doc(project)


def test_ac_b18_v1_rollback_runs_regardless_of_tier(tmp_path, monkeypatch):
    """AC-B18: a v1 surface rolls back prior v2 keys even on a non-permission tier."""
    project = tmp_path / "project"
    _write_json(
        project / "opencode.json",
        {"theme": "dark", "experimental": {"subagent_depth": 3}},
    )
    _write_json(
        project / _V2_STATE_REL,
        {
            STATE_KEYS_KEY: {
                "experimental.subagent_depth": {
                    "value": 3,
                    "prior": None,
                    "prior_absent": True,
                }
            }
        },
    )

    project, _, gate_calls = _run_stage(
        tmp_path, monkeypatch, {"Opencode": _v1_pc()}, ["Opencode"],
        _config(), {"Opencode": "advisory"},
    )

    assert gate_calls == []
    doc = _read_json(project / "opencode.json")
    assert "experimental" not in doc
    assert doc["theme"] == "dark"
    assert STATE_KEYS_KEY not in _read_state_doc(project)


def test_ac_b20_opencode_v2_plus_claude_two_syncs_byte_identical(
    tmp_path, monkeypatch
):
    """AC-B20: file and state are byte-identical across two syncs AND both orders."""
    config = _config(3, **{"experimental-todo": True})
    providers = {"Opencode": _v2_pc(), "Claude": _non_owner_pc()}
    tiers = {"Opencode": "advisory", "Claude": "advisory"}
    snapshots: dict[str, tuple[bytes, bytes]] = {}

    for label, order in (
        ("opencode-first", ["Opencode", "Claude"]),
        ("claude-first", ["Claude", "Opencode"]),
    ):
        base = tmp_path / label
        project, _, _ = _run_stage(
            base, monkeypatch, providers, order, config, tiers
        )
        first_file = (project / "opencode.json").read_bytes()
        first_state = (project / _V2_STATE_REL).read_bytes()
        _run_stage(base, monkeypatch, providers, order, config, tiers)
        assert (project / "opencode.json").read_bytes() == first_file
        assert (project / _V2_STATE_REL).read_bytes() == first_state
        snapshots[label] = (first_file, first_state)

    assert snapshots["opencode-first"] == snapshots["claude-first"]


def test_ac_b20_claude_iteration_triggers_no_rollback(tmp_path, monkeypatch):
    """AC-B20: a non-owner iteration never rolls back or logs the v2 writers."""
    config = _config(3, **{"experimental-todo": True})
    base = tmp_path / "seeded"
    project, _, _ = _run_stage(
        base, monkeypatch, {"Opencode": _v2_pc()}, ["Opencode"],
        config, {"Opencode": "advisory"},
    )
    file_before = (project / "opencode.json").read_bytes()
    state_before = (project / _V2_STATE_REL).read_bytes()

    log = SyncLog()
    _run_stage(
        base, monkeypatch, {"Claude": _non_owner_pc()}, ["Claude"],
        config, {"Claude": "advisory"}, log=log,
    )

    assert (project / "opencode.json").read_bytes() == file_before
    assert (project / _V2_STATE_REL).read_bytes() == state_before
    forbidden = ("opencode-v2-managed", "opencode-v2-owner-conflict",
                 "opencode-v2-option-ignored")
    leaked = [
        line
        for line in log.actions + log.warnings + log.skipped + log.infos + log.errors
        if any(marker in line for marker in forbidden)
    ]
    assert leaked == [], leaked


def test_ac_b20_owner_conflict_first_owner_without_work_does_not_block(
    tmp_path, monkeypatch
):
    """QA-B-02: a claimant with nothing to do must not shadow the real owner.

    The claim is taken only after the "no targets and no state" check, so an
    owner that would be a no-op never blocks the next provider. ``idle-first``
    therefore has no owner conflict and writes normally. In ``worker-first`` the
    idle owner runs *after* the writer and sees its state; it must be rejected
    by the claim (one conflict warning) instead of rolling the managed keys back.
    Both orders end byte-identical.
    """
    providers = {"Idle": _v2_pc(), "Worker": _v2_pc()}
    config = {"provider-options": {"Worker": {"experimental-subagent-depth": 3}}}
    tiers = {"Idle": "advisory", "Worker": "advisory"}

    snapshots = {}
    for label, order, expected_conflicts in (
        ("idle-first", ["Idle", "Worker"], 0),
        ("worker-first", ["Worker", "Idle"], 1),
    ):
        base = tmp_path / label
        log = SyncLog()
        project, _, _ = _run_stage(
            base, monkeypatch, providers, order, config, tiers, log=log
        )
        conflicts = [w for w in log.warnings if "opencode-v2-owner-conflict" in w]
        assert len(conflicts) == expected_conflicts, log.warnings
        doc = _read_json(project / "opencode.json")
        assert doc["experimental"] == {"subagent_depth": 3}
        assert STATE_KEYS_KEY in _read_state_doc(project)
        snapshots[label] = (
            (project / "opencode.json").read_bytes(),
            (project / _V2_STATE_REL).read_bytes(),
        )

    assert snapshots["idle-first"] == snapshots["worker-first"]


def test_ac_b20_owner_conflict_warns_and_second_provider_is_noop(
    tmp_path, monkeypatch
):
    """N-M2 (3): only the first owner acts per managed file; the rest warn."""
    providers = {"First": _v2_pc(), "Second": _v2_pc()}
    config = {
        "provider-options": {
            "First": {"experimental-subagent-depth": 3},
            "Second": {"experimental-subagent-depth": 3},
        }
    }
    tiers = {"First": "advisory", "Second": "advisory"}
    reads: list = []
    real_read = isolation._read_json_safe

    def _counting_read(*args, **kwargs):
        reads.append(args[0])
        return real_read(*args, **kwargs)

    monkeypatch.setattr(isolation, "_read_json_safe", _counting_read)

    snapshots = {}
    for label, order in (
        ("first-first", ["First", "Second"]),
        ("second-first", ["Second", "First"]),
    ):
        reads.clear()
        base = tmp_path / label
        log = SyncLog()
        project, _, _ = _run_stage(
            base, monkeypatch, providers, order, config, tiers, log=log
        )
        assert len(reads) == 1, (
            "the second owner must be rejected before any file read"
        )
        warnings = [w for w in log.warnings if "opencode-v2-owner-conflict" in w]
        assert len(warnings) == 1, log.warnings
        assert "opencode-v2-owner-conflict: opencode.json" in warnings[0]
        doc = _read_json(project / "opencode.json")
        assert doc["experimental"] == {"subagent_depth": 3}
        snapshots[label] = (
            (project / "opencode.json").read_bytes(),
            (project / _V2_STATE_REL).read_bytes(),
        )

    assert snapshots["first-first"] == snapshots["second-first"]


# ===========================================================================
# Phase B / Task 12 (B.9): model-id format `provider/model[#variant]`
# ===========================================================================
#
# The check is driven purely by the *resolved* `agent-transform.model-pattern`
# (Task 6: `surface-model-patterns[<surface-version>]` -> `model-pattern`). No
# provider name and no surface-version comparison appears here or in the code
# under test; an artifact contract without a resolved `model-pattern` performs
# no model check at all (the v1 surface stays untouched).

_V2_MODEL_PATTERN = r"^[^/#\s]+/[^#\s]+(#[A-Za-z0-9._-]+)?$"


def _model_contract_pc(surface: str) -> dict:
    """An Opencode-shaped entry whose v2 surface declares the model pattern."""
    pc = _opencode_like(surface)
    pc["agents_dir"] = ".probe/agents"
    pc["agent_ext"] = ".md"
    pc["agent-transform"]["surface-model-patterns"] = {"v2": _V2_MODEL_PATTERN}
    return pc


def _agent_with_model(model: str) -> str:
    return (
        "---\n"
        "name: probe\n"
        "description: model-id format probe\n"
        f"model: {model}\n"
        "---\n"
        "Body content.\n"
    )


def _validate_model(root: Path, surface: str, model: str) -> tuple[dict, list]:
    """Resolve the surface's contract from a fixture registry and validate *model*."""
    _write_config(root, {"Opencode": _model_contract_pc(surface)})
    pc = load_providers_config(root)["Opencode"]
    contract = resolve_artifact_contract(pc)
    findings = validate_frontmatter(
        _agent_with_model(model),
        allowed_fields=contract.allowed_fields,
        required_fields=set(contract.required_fields),
        reject_fields=contract.reject_fields,
        path=".probe/agents/probe.md",
        model_pattern=contract.model_pattern,
    )
    return pc, findings


def test_ac_b12_model_without_provider_prefix_is_finding(tmp_path):
    """AC-B12: a bare model id is an ``artifact-contract`` finding on v2.

    The pattern comes from the resolved contract (Task 6 data), so the check
    needs no provider-name branch. The end-to-end consistency path is asserted
    as well: it turns the finding into a non-zero exit code.
    """
    pc, findings = _validate_model(tmp_path / "fw", "v2", "deepseek-v4")

    assert pc["agent-transform"]["model-pattern"] == _V2_MODEL_PATTERN
    errors = [f for f in findings if f.severity.value == "ERROR"]
    assert len(errors) == 1, findings
    assert errors[0].check == "artifact-contract"
    assert errors[0].message == "model 'deepseek-v4' is not provider/model[#variant]"
    assert errors[0].file == ".probe/agents/probe.md"

    # End-to-end: the same fixture through the shared consistency checker.
    project = tmp_path / "project"
    _write_config(project, {"Opencode": _model_contract_pc("v2")})
    agent = project / ".probe" / "agents" / "probe.md"
    agent.parent.mkdir(parents=True)
    agent.write_text(_agent_with_model("deepseek-v4"), encoding="utf-8")
    e2e = check_artifact_contracts(project)
    assert [f.message for f in e2e if f.check == "artifact-contract"] == [
        "model 'deepseek-v4' is not provider/model[#variant]"
    ], e2e

    # v1 regression: without a resolved `model-pattern` nothing is checked.
    v1_pc, v1_findings = _validate_model(tmp_path / "v1-fw", "v1", "deepseek-v4")
    assert "model-pattern" not in v1_pc["agent-transform"]
    assert resolve_artifact_contract(v1_pc).model_pattern is None
    assert v1_findings == [], v1_findings


def test_ac_b12_valid_ids_accepted(tmp_path):
    """AC-B12: ``provider/model`` and ``provider/model#variant`` both pass."""
    for model in ("opencode-go/deepseek-v4-pro#high", "opencode-go/deepseek-v4-pro"):
        slug = model.split("/", 1)[1].replace("#", "-")
        pc, findings = _validate_model(tmp_path / slug, "v2", model)
        assert pc["agent-transform"]["model-pattern"] == _V2_MODEL_PATTERN
        assert findings == [], (model, findings)

    # Negative controls: the pattern is not vacuous. (The pattern's model
    # segment is `[^#\s]+`, so extra slashes are permitted by design; only the
    # missing provider prefix and a dangling `#` are violations.)
    for model in ("deepseek-v4", "opencode-go/deepseek-v4-pro#", "/deepseek-v4"):
        _, findings = _validate_model(
            tmp_path / ("bad-" + model.replace("/", "_").replace("#", "-")), "v2", model
        )
        assert len(findings) == 1, (model, findings)


def test_ac_b12_model_catalog_check_ignores_variant(tmp_path):
    """AC-B12: the catalog compares the id WITHOUT ``#variant`` (no false mismatch)."""
    root = tmp_path / "fw"
    (root / "config").mkdir(parents=True)
    (root / "config" / "ai-providers.yaml").write_text(
        yaml.safe_dump(
            {
                "providers": {
                    "Probe": {
                        "agents_dir": ".probe/agents",
                        "agent_ext": ".md",
                        "model-format": "{model}",
                        "model-catalog": ["opencode-go/deepseek-v4-pro"],
                        "agent-transform": {"frontmatter-mechanism": "provider-md"},
                    }
                }
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    agents = root / ".probe" / "agents"
    agents.mkdir(parents=True)
    (agents / "variant.md").write_text(
        _agent_with_model("opencode-go/deepseek-v4-pro#high"), encoding="utf-8"
    )

    # A declared variant is the same catalog model: no finding.
    assert check_model_contracts(root) == []

    # Control: an id outside the catalog is still fail-loud, variant included.
    (agents / "unknown.md").write_text(
        _agent_with_model("opencode-go/not-in-catalog#high"), encoding="utf-8"
    )
    errors = [f for f in check_model_contracts(root) if f.check == "model-contract"]
    assert len(errors) == 1, errors
    assert "is not in the configured model-catalog" in errors[0].message
    assert "opencode-go/not-in-catalog#high" in errors[0].message


# ===========================================================================
# Phase C1 / Task 13 (C1.1): ``permissions[]`` gate builder and writer
# ===========================================================================
#
# Amendment B1 (Spike Q3, VERIFIED): ``permissions[]`` is evaluated
# *last match wins*, agent rules are appended last. The managed deny triples are
# therefore appended at the END of the list (an early deny would be the weakest
# position), and the rollback identifies its own triples position-independently
# by the exact triple — never by list index.
#
# The writer is exclusively called by ``reconcile_opencode_surface_gate``
# (Task 13a); these tests pin its own contract in isolation: END insertion,
# single occurrence, user order preserved, position-independent rollback, the
# dedicated ``opencode-v2-permissions`` state namespace, and the Spec-A
# regression (v2 loses the ``permission`` map, v1 keeps it byte-identically).

_V2_GATE_STATE_KEY = isolation._STATE_V2_PERMISSIONS
_EDIT_DENY = {"action": "edit", "resource": "**", "effect": "deny"}
_SHELL_DENY = {"action": "shell", "resource": "**", "effect": "deny"}


class _ActiveSetStub:
    """Minimal ``ActiveSet`` shape — only ``roles`` is read by the gate code."""

    def __init__(self, *roles: str) -> None:
        self.roles = frozenset(roles)


def _active(*roles: str) -> _ActiveSetStub:
    return _ActiveSetStub(*roles)


# The fixture registries declare ``primary-role: orchestrator``; this models the
# normal case (role declared AND generated). Tests that need the non-generated
# case (QA-C-01) pass their own active set.
_GENERATED = _active("orchestrator")


def _write_caps(root: Path, provider: str, tier: str) -> Path:
    """Minimal framework root whose capability registry declares ``tier``."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "provider-capabilities.yaml").write_text(
        yaml.safe_dump({"capabilities": {provider: {"runtime_gate": tier}}}),
        encoding="utf-8",
    )
    return root


def _gate_config(mode: str = "strict") -> dict:
    """Project config selecting *mode* via the three-tier precedence."""
    return {"orchestrator": {"mode": mode}}


def _run_v2_permissions(
    project_root: Path,
    entries: list,
    log: SyncLog | None = None,
    provider_config: dict | None = None,
    dry_run: bool = False,
) -> bool:
    return isolation._sync_opencode_v2_gate_permissions(
        project_root,
        provider_config if provider_config is not None else _v2_pc(),
        entries,
        log if log is not None else SyncLog(),
        dry_run,
    )


def _run_runtime_gate(
    project_root: Path,
    framework: Path,
    provider_config: dict,
    config: dict | None = None,
    log: SyncLog | None = None,
    active_set: object = _GENERATED,
) -> SyncLog:
    log = log if log is not None else SyncLog()
    isolation._sync_opencode_runtime_gate(
        project_root,
        config if config is not None else _gate_config(),
        "Opencode",
        provider_config,
        framework,
        log,
        dry_run=False,
        active_set=active_set,
    )
    return log


def test_permission_deny_required_truth_table():
    """A pure decision over resolved data: permission tier, or plugin+observe.

    ``plugin`` + ``enforce`` is False because the baked plugin then blocks on
    its own (the deny would double up); ``advisory`` never blocks. The tier is
    the IC-03 resolver's output — no provider literal participates.
    """
    permission_caps = {"runtime_gate": "permission"}
    plugin_pc = {"has_plugins": True, "plugin_protocol": "opencode-plugin-js"}

    assert isolation.permission_deny_required({}, permission_caps, "observe") is True
    assert isolation.permission_deny_required({}, permission_caps, "enforce") is True
    assert isolation.permission_deny_required(plugin_pc, {}, "observe") is True
    assert isolation.permission_deny_required(plugin_pc, {}, "enforce") is False
    assert (
        isolation.permission_deny_required({}, {"runtime_gate": "advisory"}, "observe")
        is False
    )
    assert isolation.permission_deny_required({}, {}, "observe") is False


def test_ac_c5_idempotent_each_triple_once(tmp_path):
    """AC-C5: END insertion, one occurrence per triple, second run byte-identical.

    Amendment B1: the managed triples follow every existing entry; a repeat run
    neither duplicates them nor reorders the user's entries.
    """
    project = tmp_path / "project"
    user_permissions = [
        {"action": "edit", "resource": "src/**", "effect": "allow"},
        {"action": "shell", "resource": "npm run *", "effect": "allow"},
    ]
    _write_json(
        project / "opencode.json",
        {"theme": "dark", "permissions": list(user_permissions)},
    )
    log = SyncLog()

    assert _run_v2_permissions(project, [_EDIT_DENY, _SHELL_DENY], log) is True

    doc = _read_json(project / "opencode.json")
    permissions = doc["permissions"]
    assert doc["theme"] == "dark"
    assert permissions[:2] == user_permissions, "user entries keep their order"
    assert permissions[2:] == [_EDIT_DENY, _SHELL_DENY], (
        "managed triples must be appended at the END (last match wins)"
    )
    assert len(permissions) == 4, "each triple exactly once"
    assert _read_state_doc(project)[_V2_GATE_STATE_KEY] == {
        "triples": [["edit", "**", "deny"], ["shell", "**", "deny"]]
    }

    file_bytes = (project / "opencode.json").read_bytes()
    state_bytes = (project / _V2_STATE_REL).read_bytes()
    assert _run_v2_permissions(project, [_EDIT_DENY, _SHELL_DENY], SyncLog()) is False, (
        "a second identical run is a no-op"
    )
    assert (project / "opencode.json").read_bytes() == file_bytes
    assert (project / _V2_STATE_REL).read_bytes() == state_bytes


def test_ac_c4_writer_rollback_removes_only_state_triples_keeps_user_order(tmp_path):
    """AC-C4: rollback works after the triples moved — identified by triple."""
    project = tmp_path / "project"
    edit_allow = {"action": "edit", "resource": "src/**", "effect": "allow"}
    shell_allow = {"action": "shell", "resource": "git *", "effect": "allow"}
    _write_json(project / "opencode.json", {"permissions": [edit_allow, shell_allow]})

    _run_v2_permissions(project, [_EDIT_DENY, _SHELL_DENY])
    written = _read_json(project / "opencode.json")["permissions"]
    assert written[2:] == [_EDIT_DENY, _SHELL_DENY]

    # The user moves the managed triples to the front. A rollback that used
    # list indices would now remove the wrong entries.
    _write_json(
        project / "opencode.json",
        {"permissions": [written[3], written[1], written[2], written[0]]},
    )

    assert _run_v2_permissions(project, []) is True

    remaining = _read_json(project / "opencode.json")["permissions"]
    assert remaining == [shell_allow, edit_allow], (
        "only the state triples were removed; user relative order survived"
    )
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)


def test_user_identical_triple_not_claimed_and_survives_rollback(tmp_path):
    """A user entry identical to a managed triple is never claimed or removed."""
    project = tmp_path / "project"
    user_shell = dict(_SHELL_DENY)
    _write_json(project / "opencode.json", {"permissions": [user_shell]})

    _run_v2_permissions(project, [_EDIT_DENY, _SHELL_DENY])

    permissions = _read_json(project / "opencode.json")["permissions"]
    assert permissions[0] == user_shell
    assert permissions[1:] == [_EDIT_DENY], "no duplicate shell triple is written"
    assert _read_state_doc(project)[_V2_GATE_STATE_KEY] == {
        "triples": [["edit", "**", "deny"]]
    }, "the user's identical triple must not enter our state"

    assert _run_v2_permissions(project, []) is True

    assert _read_json(project / "opencode.json")["permissions"] == [user_shell], (
        "the user's own triple survives the rollback"
    )
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)


def test_ac_b16_permissions_namespace_isolated(tmp_path):
    """AC-B16: only ``opencode-v2-permissions`` is written; siblings stay put."""
    project = tmp_path / "project"
    _write_json(project / "opencode.json", {"permissions": []})
    siblings = {
        "isolation-deny": ["**/.claude/**"],
        "runtime-gate-deny": {"**": {"edit": None, "bash": None}},
        STATE_KEYS_KEY: {
            "experimental.subagent_depth": {
                "value": 3,
                "prior": None,
                "prior_absent": True,
            }
        },
        "opencode-v2-cli": {"plugins": {"value": ["acme.js"], "prior": None}},
        "opencode-v2-mcp": {"mcp.servers.acme": {"value": {"type": "local"}}},
    }
    _write_json(project / _V2_STATE_REL, siblings)

    _run_v2_permissions(project, [_EDIT_DENY, _SHELL_DENY])

    after = _read_state_doc(project)
    for key, value in siblings.items():
        assert after[key] == value, f"namespace {key!r} was clobbered"
    assert after[_V2_GATE_STATE_KEY] == {
        "triples": [["edit", "**", "deny"], ["shell", "**", "deny"]]
    }
    assert isinstance(
        isolation._read_state(project / _V2_STATE_REL, _V2_GATE_STATE_KEY), dict
    ), "AC-B16: the namespace reads back as a dict"

    file_bytes = (project / "opencode.json").read_bytes()
    state_bytes = (project / _V2_STATE_REL).read_bytes()
    _run_v2_permissions(project, [_EDIT_DENY, _SHELL_DENY])
    assert (project / "opencode.json").read_bytes() == file_bytes
    assert (project / _V2_STATE_REL).read_bytes() == state_bytes
    assert _read_state_doc(project)["isolation-deny"] == siblings["isolation-deny"]


def test_v2_gate_permissions_empty_without_entry_point(tmp_path):
    """AC-C15 (builder part): no explicit+generated primary role ⇒ no entries."""
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    capabilities = load_provider_capabilities(framework)
    without_primary = _v2_pc()
    without_primary.pop("primary-role")

    def build(provider_config: dict, config: dict, mode: str = "observe",
              active_set: object = _GENERATED) -> list:
        return isolation._opencode_v2_gate_permissions(
            config, "Opencode", framework, provider_config, capabilities, mode,
            active_set=active_set,
        )

    assert build({"Opencode": without_primary}, _gate_config()) == []

    with_primary = {"Opencode": _v2_pc()}
    assert build(with_primary, _gate_config()) == [_EDIT_DENY, _SHELL_DENY]

    # QA-C-01: only an explicit AND generated primary role is an entry point.
    assert build(
        with_primary, _gate_config(), active_set=_active("developer")
    ) == [], "a declared but not generated role yields no triples"

    # Negative controls: each single gate condition is load-bearing.
    assert build(with_primary, _gate_config("advisory")) == [], "strict is required"
    assert build(with_primary, _gate_config("strict"), mode="enforce") == [
        _EDIT_DENY,
        _SHELL_DENY,
    ], "the permission tier ignores the plugin mode"
    advisory_framework = _write_caps(tmp_path / "fw-advisory", "Opencode", "advisory")
    assert (
        isolation._opencode_v2_gate_permissions(
            _gate_config(), "Opencode", advisory_framework, with_primary,
            load_provider_capabilities(advisory_framework), "observe",
            active_set=_GENERATED,
        )
        == []
    ), "an advisory tier never emits deny triples"
    assert build({"Opencode": _v1_pc()}, _gate_config()) == [], (
        "v2_active is required — v1 keeps the Spec-A permission map"
    )
    plugin_pc = dict(_v2_pc(), has_plugins=True, plugin_protocol="opencode-plugin-js")
    assert build({"Opencode": plugin_pc}, _gate_config(), mode="observe") == [
        _EDIT_DENY,
        _SHELL_DENY,
    ], "plugin + observe keeps the deny"
    assert build({"Opencode": plugin_pc}, _gate_config(), mode="enforce") == [], (
        "plugin + enforce relies on the plugin, not on the deny"
    )


def test_v2_runtime_gate_skips_permission_map_step(tmp_path):
    """AC-C3 (Spec-A step 4 skipped): v2 gets ``default_agent`` only."""
    project = tmp_path / "project"
    project.mkdir()
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")

    log = _run_runtime_gate(project, framework, {"Opencode": _v2_pc()})

    doc = _read_json(project / "opencode.json")
    assert doc["default_agent"] == "orchestrator"
    assert "permission" not in doc, (
        "on v2 the Spec-A permission map must not be written (N-M1 owner)"
    )
    assert "permissions" not in doc, (
        "this path never writes the v2 triples — reconcile owns them"
    )
    assert log.warnings == [], log.warnings

    state = _read_state_doc(project)
    assert isolation._STATE_RUNTIME_GATE_KEY not in state, (
        "no runtime-gate-deny state may be created for a v2 surface"
    )
    assert state[isolation._STATE_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }


def test_ac_c6_v1_permission_map_unchanged_and_no_permissions_list(tmp_path):
    """AC-C6 (regression): v1 keeps the byte-identical ``permission`` map."""
    project = tmp_path / "project"
    project.mkdir()
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")

    _run_runtime_gate(project, framework, {"Opencode": _v1_pc()})

    doc = _read_json(project / "opencode.json")
    assert doc == {
        "permission": {"edit": {"**": "deny"}, "bash": {"**": "deny"}},
        "default_agent": "orchestrator",
    }
    assert "permissions" not in doc, "v1 never gets the v2 list form"

    state = _read_state_doc(project)
    assert state[isolation._STATE_RUNTIME_GATE_KEY] == {
        "**": {"edit": None, "bash": None}
    }
    assert state[isolation._STATE_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }
    assert _V2_GATE_STATE_KEY not in state


def test_ac_c16a_default_agent_merge_runs_on_v2(tmp_path):
    """AC-C16a (regression): the entry-point merge is unchanged on v2.

    A user value wins with a warning and is never tracked; an absent key is
    written and tracked in the ``default-agent`` namespace.
    """
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")

    user_value = tmp_path / "user-value"
    _write_json(
        user_value / "opencode.json",
        {"default_agent": "developer", "permissions": []},
    )
    log = _run_runtime_gate(user_value, framework, {"Opencode": _v2_pc()})

    assert _read_json(user_value / "opencode.json")["default_agent"] == "developer"
    assert any(
        "default_agent is 'developer' but the entry point role is 'orchestrator'"
        in warning
        for warning in log.warnings
    ), log.warnings
    assert isolation._STATE_DEFAULT_AGENT_KEY not in _read_state_doc(user_value)

    fresh = tmp_path / "fresh"
    fresh.mkdir()
    _run_runtime_gate(fresh, framework, {"Opencode": _v2_pc()})

    assert _read_json(fresh / "opencode.json")["default_agent"] == "orchestrator"
    assert _read_state_doc(fresh)[isolation._STATE_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }


def test_ac_c16a_default_agent_removed_when_primary_role_disappears(tmp_path):
    """AC-C16 (a) rollback half (RVW-C-06): losing the entry point reverts it.

    ``primary-role`` disappears after a managed write ⇒ ``default_agent`` is
    removed (``prior`` was absent) and the ``default-agent`` namespace is
    emptied, while the sibling ``default_agent`` handling stays on the v2 path.
    """
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    project = tmp_path / "project"
    project.mkdir()
    with_role = {"Opencode": _v2_pc()}

    _run_runtime_gate(project, framework, with_role)
    assert _read_json(project / "opencode.json")["default_agent"] == "orchestrator"
    assert _read_state_doc(project)[isolation._STATE_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }

    without_role = _v2_pc()
    without_role.pop("primary-role")
    log = _run_runtime_gate(project, framework, {"Opencode": without_role})

    doc = _read_json(project / "opencode.json")
    assert "default_agent" not in doc, "the managed value is removed on rollback"
    assert "permissions" not in doc, "no triples without an entry point"
    assert isolation._STATE_DEFAULT_AGENT_KEY not in _read_state_doc(project), (
        "the default-agent state entry must be emptied"
    )
    assert any("primary-role" in warning for warning in log.warnings), log.warnings


# ===========================================================================
# Phase C1 / Task 13a (C1.2): ``reconcile_opencode_surface_gate``
# ===========================================================================
#
# The binding 7-row rollback matrix of spec §3.4. The reconciler is the ONLY
# actor for the v2 ``permissions[]`` triples and for the surface-switch
# rollback. It is tier-independent but provider-bound: a non-owner returns
# before any read (N-M2), so a Claude/Gemini iteration can never undo the
# opencode state.
#
# Fixtures carry explicit ``allow``/``deny`` entries (Amendment B1 note): the
# default ``ask`` plus ``--auto`` is not a confirmation and would make an
# automated gate probe meaningless (Spike Q2, RVW-C0-06).


def _reconcile(
    project_root: Path,
    config: dict,
    provider_config: dict,
    framework: Path,
    provider: str = "Opencode",
    log: SyncLog | None = None,
    dry_run: bool = False,
    active_set: object = _GENERATED,
) -> None:
    """Call the reconciler with the same active set a production sync passes.

    ``_GENERATED`` is the fixture default (``primary-role: orchestrator`` is
    declared AND generated); a test that needs a non-generated role passes its
    own stub — ``active_set`` is a required keyword on the production function
    (QA-C-01), never a fail-open ``None``.
    """
    isolation.reconcile_opencode_surface_gate(
        project_root,
        config,
        provider,
        provider_config,
        framework,
        log if log is not None else SyncLog(),
        dry_run,
        active_set=active_set,
    )


_USER_PERMISSIONS = [
    {"action": "edit", "resource": "src/**", "effect": "allow"},
    {"action": "shell", "resource": "git *", "effect": "allow"},
]


def _seed_v1_strict(project: Path) -> None:
    """A v1-strict project with the Spec-A map deny plus ``runtime-gate-deny``.

    ``edit`` has a user entry next to the managed glob; the recorded prior is
    ``"allow"`` for edit and ``None`` (key absent) for bash.
    """
    _write_json(
        project / "opencode.json",
        {
            "theme": "dark",
            "permissions": list(_USER_PERMISSIONS),
            "permission": {
                "edit": {"**": "deny", "docs/**": "allow"},
                "bash": {"**": "deny", "git *": "allow"},
            },
        },
    )
    _write_json(
        project / _V2_STATE_REL,
        {
            isolation._STATE_DEFAULT_AGENT_KEY: {
                "value": "orchestrator",
                "prior": None,
            },
            isolation._STATE_RUNTIME_GATE_KEY: {
                "**": {"edit": "allow", "bash": None}
            },
        },
    )


def _seed_v2_triples(project: Path, user: bool = True) -> None:
    """A v2 project whose managed triples are written and recorded in state."""
    permissions = list(_USER_PERMISSIONS) if user else []
    _write_json(project / "opencode.json", {"theme": "dark", "permissions": permissions})
    _run_v2_permissions(project, [_EDIT_DENY, _SHELL_DENY])


def _plugin_pc() -> dict:
    """A v2 owner resolved to the ``plugin`` tier from its machine flags."""
    return dict(_v2_pc(), has_plugins=True, plugin_protocol="opencode-plugin-js")


# --- AC-C3 / AC-C4 (wiring) ------------------------------------------------


def test_ac_c3_v2_strict_tier_permission_writes_triples_and_no_permission_map(
    tmp_path, monkeypatch
):
    """AC-C3: wired sync writes the triples at the END and no v1 map.

    The call site is the real ``_sync_stage_per_provider`` seam (only the
    unrelated writers are stubbed), so this pins the Task-13a wiring as well as
    the matrix row "v2, Tier permission, strict on".
    """
    project = tmp_path / "project"
    project.mkdir()
    _write_json(project / "opencode.json", {"permissions": list(_USER_PERMISSIONS)})

    project, _, gate_calls = _run_stage(
        tmp_path, monkeypatch, {"Opencode": _v2_pc()}, ["Opencode"],
        _gate_config(), {"Opencode": "permission"},
    )

    assert gate_calls, "the permission tier must dispatch the Spec-A writer"
    doc = _read_json(project / "opencode.json")
    assert doc["permissions"][:2] == _USER_PERMISSIONS, "user entries keep their order"
    assert doc["permissions"][2:] == [_EDIT_DENY, _SHELL_DENY], (
        "managed triples must be appended at the END (last match wins)"
    )
    assert "permission" not in doc, "v2 must not carry the v1 permission map"
    assert _read_state_doc(project)[_V2_GATE_STATE_KEY] == {
        "triples": [["edit", "**", "deny"], ["shell", "**", "deny"]]
    }


def test_ac_c4_strict_off_removes_managed_triples_keeps_user_order(tmp_path):
    """AC-C4: strict off removes exactly the recorded triples, user order intact."""
    project = tmp_path / "project"
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    _seed_v2_triples(project)

    log = SyncLog()
    _reconcile(
        project, _gate_config("advisory"), {"Opencode": _v2_pc()}, framework, log=log
    )

    assert _read_json(project / "opencode.json")["permissions"] == _USER_PERMISSIONS
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)
    assert any("opencode-v2 gate permissions" in action for action in log.actions), (
        log.actions
    )


# --- AC-C15 (entry point) --------------------------------------------------


def test_ac_c15_no_primary_role_writes_no_triple_and_warns(tmp_path):
    """AC-C15: no entry point ⇒ no triple; exactly one warning names the cause.

    On the ``permission`` tier Spec A's coupling warning is the only one (the
    reconcile function stays silent). On every other tier Spec A does not run,
    so ``reconcile_opencode_surface_gate`` emits the warning itself.
    """
    pc_without_role = _v2_pc()
    pc_without_role.pop("primary-role")

    # Tier permission: Spec A warns, reconcile stays silent.
    project = tmp_path / "permission-tier"
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    log = SyncLog()
    _run_runtime_gate(
        project, framework, {"Opencode": pc_without_role}, log=log
    )
    _reconcile(
        project, _gate_config(), {"Opencode": pc_without_role}, framework, log=log
    )
    assert "permissions" not in _read_json(project / "opencode.json")
    warnings = [w for w in log.warnings if "primary-role" in w]
    assert len(warnings) == 1, log.warnings
    assert "lock every agent" in warnings[0], warnings[0]
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)

    # Tier advisory: Spec A never runs, reconcile owns the warning.
    project = tmp_path / "advisory-tier"
    framework = _write_caps(tmp_path / "fw-advisory", "Opencode", "advisory")
    log = SyncLog()
    _reconcile(
        project, _gate_config(), {"Opencode": pc_without_role}, framework, log=log
    )
    assert not (project / "opencode.json").exists()
    warnings = [w for w in log.warnings if "primary-role" in w]
    assert len(warnings) == 1, log.warnings
    assert "lock every agent" in warnings[0], warnings[0]


# --- AC-C15 / QA-C-01 (entry point = explicit AND generated) ----------------


def test_ac_c15_non_generated_primary_role_gets_no_triples_on_permission_tier(
    tmp_path,
):
    """QA-C-01 (tier ``permission``): the reconciler uses the same active set.

    A declared primary role that is NOT in the active set is no entry point for
    Spec A either (it warns "the gate would lock every agent"). The v2 builder
    must therefore also produce no triples — and the positive control proves the
    threaded ``active_set`` still lets the generated role through.
    """
    project = tmp_path / "project"
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    pc = {"Opencode": _v2_pc()}
    not_generated = _active("developer")

    log = _run_runtime_gate(project, framework, pc, log=SyncLog(), active_set=not_generated)
    _reconcile(project, _gate_config(), pc, framework, log=log, active_set=not_generated)

    doc = _read_json(project / "opencode.json")
    assert "permissions" not in doc, (
        "a role that was never generated must not get v2 deny triples (QA-C-01)"
    )
    warnings = [w for w in log.warnings if "primary-role" in w]
    assert len(warnings) == 1, log.warnings
    assert "lock every agent" in warnings[0], warnings[0]
    state = _read_state_doc(project)
    assert _V2_GATE_STATE_KEY not in state
    assert isolation._STATE_RUNTIME_GATE_KEY not in state

    # Positive control: the generated role still gets triples through the same
    # required keyword — the fix is not a blanket suppression.
    _reconcile(project, _gate_config(), pc, framework, active_set=_GENERATED)

    assert _read_json(project / "opencode.json")["permissions"] == [
        _EDIT_DENY,
        _SHELL_DENY,
    ]
    assert _read_state_doc(project)[_V2_GATE_STATE_KEY] == {
        "triples": [["edit", "**", "deny"], ["shell", "**", "deny"]]
    }


def test_ac_c15_non_generated_primary_role_gets_no_triples_on_plugin_observe(
    tmp_path, monkeypatch
):
    """QA-C-01 (tier ``plugin`` + ``observe``): no triples, warning, no state.

    Spec A never runs on this tier, so the reconciler owns the warning itself.
    Before the fix it wrote silent v2 deny triples for a non-generated role.
    """
    project = tmp_path / "project"
    framework = _write_caps(tmp_path / "fw", "Opencode", "advisory")
    pc = {"Opencode": _plugin_pc()}
    not_generated = _active("developer")
    monkeypatch.setattr(runtime_gate, "_baked_plugin_mode", lambda: "observe")

    log = SyncLog()
    _reconcile(project, _gate_config(), pc, framework, log=log, active_set=not_generated)

    assert not (project / "opencode.json").exists(), "no file is created without triples"
    warnings = [w for w in log.warnings if "primary-role" in w]
    assert len(warnings) == 1, log.warnings
    assert "lock every agent" in warnings[0], warnings[0]
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)

    # Positive control: plugin+observe is exactly where the deny must stay.
    _reconcile(project, _gate_config(), pc, framework, active_set=_GENERATED)

    assert _read_json(project / "opencode.json")["permissions"] == [
        _EDIT_DENY,
        _SHELL_DENY,
    ]
    assert _V2_GATE_STATE_KEY in _read_state_doc(project)


# --- AC-B21 / AC-B22 (surface switches) ------------------------------------


def test_ac_b21_v1_strict_to_v2_removes_permission_map_and_empties_runtime_gate_deny(
    tmp_path,
):
    """AC-B21 (matrix row 1): v1 map out first, then the v2 triples in."""
    project = tmp_path / "project"
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    _seed_v1_strict(project)

    _reconcile(project, _gate_config(), {"Opencode": _v2_pc()}, framework)

    doc = _read_json(project / "opencode.json")
    assert doc["permission"]["edit"] == {"**": "allow", "docs/**": "allow"}, (
        "the recorded prior is restored, the user entry is untouched"
    )
    assert doc["permission"]["bash"] == {"git *": "allow"}, (
        "an absent prior removes the managed glob and prunes the empty family"
    )
    assert doc["permissions"][:2] == _USER_PERMISSIONS, "user order preserved"
    assert doc["permissions"][2:] == [_EDIT_DENY, _SHELL_DENY]
    state = _read_state_doc(project)
    assert isolation._STATE_RUNTIME_GATE_KEY not in state, (
        "the Spec-A namespace is emptied once the v1 map was taken back"
    )
    assert state[isolation._STATE_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }, "sibling namespaces are untouched"


def test_ac_b22_v2_to_v1_empties_permissions_namespace_and_list(tmp_path):
    """AC-B22 (matrix row 2): v2→v1 always rolls back, then Spec A writes v1."""
    # Tier permission: rollback + the Spec-A map afterwards.
    project = tmp_path / "project"
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    _seed_v2_triples(project)

    _reconcile(project, _gate_config(), {"Opencode": _v1_pc()}, framework)

    doc = _read_json(project / "opencode.json")
    assert doc["permissions"] == _USER_PERMISSIONS, "user order preserved"
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)

    _run_runtime_gate(project, framework, {"Opencode": _v1_pc()})
    doc = _read_json(project / "opencode.json")
    assert doc["permission"] == {
        "edit": {"**": "deny"},
        "bash": {"**": "deny"},
    }, "Spec A writes the v1 map after the rollback"
    assert _read_state_doc(project)[isolation._STATE_RUNTIME_GATE_KEY] == {
        "**": {"edit": None, "bash": None}
    }

    # Tier advisory: the rollback still runs (no v1 map, Spec A never ran).
    project = tmp_path / "advisory"
    framework = _write_caps(tmp_path / "fw-advisory", "Opencode", "advisory")
    _seed_v2_triples(project)

    _reconcile(project, _gate_config(), {"Opencode": _v1_pc()}, framework)

    doc = _read_json(project / "opencode.json")
    assert doc["permissions"] == _USER_PERMISSIONS
    assert "permission" not in doc
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)


# --- AC-C14 (tier plugin) --------------------------------------------------


def test_ac_c14_observe_keeps_triples_enforce_removes(tmp_path, monkeypatch):
    """AC-C14: ``observe`` keeps the deny, ``enforce`` drops it without Spec A."""
    project = tmp_path / "project"
    framework = _write_caps(tmp_path / "fw", "Opencode", "advisory")
    plugin_config = {"Opencode": _plugin_pc()}

    monkeypatch.setattr(runtime_gate, "_baked_plugin_mode", lambda: "observe")
    _reconcile(project, _gate_config(), plugin_config, framework)
    doc = _read_json(project / "opencode.json")
    assert doc["permissions"] == [_EDIT_DENY, _SHELL_DENY], (
        "plugin in observe mode never weakens the gate"
    )
    assert _read_state_doc(project)[_V2_GATE_STATE_KEY]["triples"] == [
        ["edit", "**", "deny"],
        ["shell", "**", "deny"],
    ]

    monkeypatch.setattr(runtime_gate, "_baked_plugin_mode", lambda: "enforce")
    _reconcile(project, _gate_config(), plugin_config, framework)

    assert "permissions" not in _read_json(project / "opencode.json"), (
        "enforce removes the triples although _sync_opencode_runtime_gate never ran"
    )
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)


# --- AC-B20 / AC-B8 (provider binding, idempotency) ------------------------


def test_ac_b20_reconcile_noop_for_non_owner_provider(tmp_path, monkeypatch):
    """AC-B20 (N-M2): a non-owner returns before any read; nothing changes."""
    project = tmp_path / "project"
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    _seed_v2_triples(project)
    file_before = (project / "opencode.json").read_bytes()
    state_before = (project / _V2_STATE_REL).read_bytes()

    def _forbidden(*args, **kwargs):
        raise AssertionError("state must not be read for a non-owner provider")

    monkeypatch.setattr(isolation, "_read_state", _forbidden)

    log = SyncLog()
    _reconcile(
        project, _gate_config(), {"Claude": _non_owner_pc()}, framework,
        provider="Claude", log=log,
    )

    assert (project / "opencode.json").read_bytes() == file_before
    assert (project / _V2_STATE_REL).read_bytes() == state_before
    assert log.actions == [] and log.warnings == [] and log.errors == []


def test_ac_b8_reconcile_noop_when_nothing_in_state_and_idempotent(tmp_path):
    """AC-B8 (matrix row 7): strict off + empty state is a byte-identical no-op."""
    project = tmp_path / "project"
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    _write_json(project / "opencode.json", {"permissions": list(_USER_PERMISSIONS)})
    file_before = (project / "opencode.json").read_bytes()
    state_path = project / _V2_STATE_REL

    log = SyncLog()
    _reconcile(
        project, _gate_config("advisory"), {"Opencode": _v2_pc()}, framework, log=log
    )

    assert (project / "opencode.json").read_bytes() == file_before
    assert not state_path.exists(), "a no-op must not create the state file"
    assert log.actions == [] and log.warnings == []

    # Gate effectively active: triples appear, a second run is byte-identical.
    _reconcile(project, _gate_config(), {"Opencode": _v2_pc()}, framework)
    first_file = (project / "opencode.json").read_bytes()
    first_state = state_path.read_bytes()
    assert _read_json(project / "opencode.json")["permissions"][2:] == [
        _EDIT_DENY,
        _SHELL_DENY,
    ]

    _reconcile(project, _gate_config(), {"Opencode": _v2_pc()}, framework)
    assert (project / "opencode.json").read_bytes() == first_file
    assert state_path.read_bytes() == first_state


# --- the binding 7-row matrix ---------------------------------------------


def _matrix_v1_to_v2(project: Path, framework: Path) -> None:
    project.mkdir(parents=True)
    _seed_v1_strict(project)
    _reconcile(project, _gate_config(), {"Opencode": _v2_pc()}, framework)
    doc = _read_json(project / "opencode.json")
    assert doc["permission"]["edit"]["**"] == "allow"
    assert doc["permission"]["bash"] == {"git *": "allow"}
    assert isolation._STATE_RUNTIME_GATE_KEY not in _read_state_doc(project)
    assert doc["permissions"][:2] == _USER_PERMISSIONS
    assert doc["permissions"][2:] == [_EDIT_DENY, _SHELL_DENY]


def _matrix_v1_to_v2_advisory(project: Path, framework: Path) -> None:
    """Row 1 on an ``advisory`` tier (RVW-C-02): map out, no triples.

    The v1 map is taken back regardless of the tier; ``permission_deny_required``
    is false on ``advisory``, so no triples are written and the state stays
    empty. The document keeps only the user entries that were already there.
    """
    project.mkdir(parents=True)
    _seed_v1_strict(project)
    _reconcile(project, _gate_config(), {"Opencode": _v2_pc()}, framework)
    doc = _read_json(project / "opencode.json")
    assert doc["permission"]["edit"]["**"] == "allow"
    assert doc["permission"]["bash"] == {"git *": "allow"}
    state = _read_state_doc(project)
    assert isolation._STATE_RUNTIME_GATE_KEY not in state
    assert doc["permissions"] == _USER_PERMISSIONS, "no triples on the advisory tier"
    assert _V2_GATE_STATE_KEY not in state


def _matrix_v2_to_v1(project: Path, framework: Path) -> None:
    _seed_v2_triples(project)
    _reconcile(project, _gate_config(), {"Opencode": _v1_pc()}, framework)
    assert _read_json(project / "opencode.json")["permissions"] == _USER_PERMISSIONS
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)


def _matrix_permission_strict_off(project: Path, framework: Path) -> None:
    _seed_v2_triples(project)
    _reconcile(project, _gate_config("advisory"), {"Opencode": _v2_pc()}, framework)
    assert _read_json(project / "opencode.json")["permissions"] == _USER_PERMISSIONS
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)


def _matrix_plugin_observe(project: Path, framework: Path) -> None:
    _reconcile(project, _gate_config(), {"Opencode": _plugin_pc()}, framework)
    doc = _read_json(project / "opencode.json")
    assert doc["permissions"] == [_EDIT_DENY, _SHELL_DENY]
    assert _V2_GATE_STATE_KEY in _read_state_doc(project)


def _matrix_tier_downgrade(project: Path, framework: Path, monkeypatch) -> None:
    # Tier plugin + enforce: the plugin blocks on its own, the deny goes.
    _seed_v2_triples(project)
    monkeypatch.setattr(runtime_gate, "_baked_plugin_mode", lambda: "enforce")
    _reconcile(project, _gate_config(), {"Opencode": _plugin_pc()}, framework)
    assert _read_json(project / "opencode.json")["permissions"] == _USER_PERMISSIONS
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)

    # Tier advisory: same removal, Spec A never runs.
    alternative = project / "advisory"
    _seed_v2_triples(alternative)
    _reconcile(alternative, _gate_config(), {"Opencode": _v2_pc()}, framework)
    assert _read_json(alternative / "opencode.json")["permissions"] == _USER_PERMISSIONS
    assert _V2_GATE_STATE_KEY not in _read_state_doc(alternative)


def _matrix_no_entry_point(project: Path, framework: Path) -> None:
    pc_without_role = _v2_pc()
    pc_without_role.pop("primary-role")
    _seed_v2_triples(project)
    log = SyncLog()
    _reconcile(
        project, _gate_config(), {"Opencode": pc_without_role}, framework, log=log
    )
    assert _read_json(project / "opencode.json")["permissions"] == _USER_PERMISSIONS
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)
    assert any("primary-role" in warning for warning in log.warnings), log.warnings


def _matrix_nothing_in_state(project: Path, framework: Path) -> None:
    project.mkdir(parents=True)
    _write_json(project / "opencode.json", {"permissions": list(_USER_PERMISSIONS)})
    file_before = (project / "opencode.json").read_bytes()
    _reconcile(project, _gate_config("advisory"), {"Opencode": _v2_pc()}, framework)
    assert (project / "opencode.json").read_bytes() == file_before
    assert not (project / _V2_STATE_REL).exists()


def test_reconcile_matrix_seven_rows(tmp_path, monkeypatch):
    """Spec §3.4: each of the seven binding rows produces its stated action."""
    permission_fw = _write_caps(tmp_path / "fw-permission", "Opencode", "permission")
    advisory_fw = _write_caps(tmp_path / "fw-advisory", "Opencode", "advisory")

    rows = [
        ("1-v1-to-v2", permission_fw, False, _matrix_v1_to_v2),
        ("1b-v1-to-v2-advisory", advisory_fw, False, _matrix_v1_to_v2_advisory),
        ("2-v2-to-v1", advisory_fw, False, _matrix_v2_to_v1),
        ("3-v2-permission-strict-off", permission_fw, False, _matrix_permission_strict_off),
        ("4-v2-plugin-observe", advisory_fw, False, _matrix_plugin_observe),
        ("5-v2-plugin-enforce-or-advisory", advisory_fw, True, _matrix_tier_downgrade),
        ("6-v2-no-entry-point", advisory_fw, False, _matrix_no_entry_point),
        ("7-v2-nothing-in-state-strict-off", permission_fw, False, _matrix_nothing_in_state),
    ]

    for label, framework, needs_monkeypatch, check in rows:
        project = tmp_path / label
        if needs_monkeypatch:
            check(project, framework, monkeypatch)
        else:
            check(project, framework)


# --- IC-4 freeze -----------------------------------------------------------

# SHA-256 of the normalised source of the two Spec-A functions, captured at the
# start of Task 13a (commit f07ab459). Spec-A invariant: ``permissions[]`` is
# reconciled elsewhere; these two functions and the tier call condition keep
# their exact shape (spec §3.4, IC-4 / m-6, AC-C14).
_IC4_SOURCE_HASHES = {
    "_opencode_runtime_gate_entries": (
        "b4a6c1420a851f096fe095ddaf5e0f0702be2eab883231f56bc828e513dd9001"
    ),
    "opencode_runtime_gate_wanted": (
        "294986792a899dedaa05a03786cb657c82081dafc1968aeb065de80aeba1deea"
    ),
}
_RUNTIME_GATE_CALL_CONDITION = 'provider_runtime_gate_tier(pc, caps) == "permission"'
# RVW-C-01: the condition must not merely exist once — the guarded call must sit
# *inside* the block. Asserted in place: ``if <condition>:`` followed by the
# deeper-indented ``_sync_opencode_runtime_gate(`` on the next code line.
_RUNTIME_GATE_CALL_BLOCK = re.compile(
    r"^(?P<indent>[ \t]*)if "
    + re.escape(_RUNTIME_GATE_CALL_CONDITION)
    + r":\n(?P=indent)[ \t]+_sync_opencode_runtime_gate\(\n",
    re.MULTILINE,
)


def _call_block(text: str, match: re.Match) -> str:
    """Source of the guarded call: from the ``if`` line to its closing paren."""
    indent = match.group("indent")
    end = text.index("\n" + indent + ")\n", match.end())
    return text[match.start():end]


def _normalised_function_source(source: str, name: str) -> str:
    start = source.index(f"\ndef {name}(") + 1
    rest = source[start + 1:]
    match = re.search(r"^(?:def |# ---)", rest, re.M)
    end = start + 1 + match.start() if match else len(source)
    block = source[start:end].strip("\n")
    return "\n".join(line.rstrip() for line in block.split("\n")) + "\n"


def test_ic4_functions_and_call_condition_unchanged():
    """IC-4 freeze: both functions and both call conditions are byte-identical."""
    source = Path(isolation.__file__).read_text(encoding="utf-8")
    for name, expected in _IC4_SOURCE_HASHES.items():
        actual = hashlib.sha256(
            _normalised_function_source(source, name).encode("utf-8")
        ).hexdigest()
        assert actual == expected, f"Spec-A function {name} changed: {actual}"

    lib_dir = Path(__file__).resolve().parent.parent / "scripts" / "lib"
    for filename in ("sync_pipeline.py", "cli_commands.py"):
        text = (lib_dir / filename).read_text(encoding="utf-8")
        assert text.count(_RUNTIME_GATE_CALL_CONDITION) == 1, (
            f"{filename}: call condition must stay exactly once"
        )
        # RVW-C-01: assert the condition *in place* — the guarded Spec-A writer
        # is the first statement inside the block, not somewhere else in the
        # file, and it receives the real active set (QA-C-01).
        matches = list(_RUNTIME_GATE_CALL_BLOCK.finditer(text))
        assert len(matches) == 1, (
            f"{filename}: the condition must directly guard "
            "_sync_opencode_runtime_gate"
        )
        gate_block = _call_block(text, matches[0])
        assert "active_set=active_set" in gate_block, gate_block

        # The tier-independent reconciler is called with the same active set;
        # a fail-open default there was the QA-C-01 blocker.
        reconcile = re.compile(
            r"^(?P<indent>[ \t]*)reconcile_opencode_surface_gate\(\n",
            re.MULTILINE,
        )
        reconcile_matches = list(reconcile.finditer(text))
        assert len(reconcile_matches) == 1, filename
        reconcile_block = _call_block(text, reconcile_matches[0])
        assert "active_set=active_set" in reconcile_block, reconcile_block

        # RVW-C-02: the reconciler must be called at the *same* indentation as
        # the guarded Spec-A ``if`` block, i.e. OUTSIDE it (indent 8). Any extra
        # wrapper such as ``if provider_runtime_gate_tier(...) == "permission":``
        # around the reconciler would silently drop the tier ``plugin``/``advisory``
        # rollback and must fail here — the mutation is only observable through
        # the indentation, not through the call text or the condition count.
        guard_indent = matches[0].group("indent")
        reconcile_indent = reconcile_matches[0].group("indent")
        assert len(guard_indent) == 8, (
            f"{filename}: the runtime-gate block must stay at indent 8 inside "
            f"the per-provider iteration, got indent {len(guard_indent)}"
        )
        assert reconcile_indent == guard_indent, (
            f"{filename}: reconcile_opencode_surface_gate must be called at the "
            f"same indentation as the guarded _sync_opencode_runtime_gate block "
            f"(outside the if, indent {len(guard_indent)}), got indent "
            f"{len(reconcile_indent)} — the tier-independent reconciler must not "
            f"be nested in a runtime-gate-tier condition"
        )


# ===========================================================================
# Phase C2 / Task 15 (C2.2): the v2 MCP connection entry
# ===========================================================================
#
# ``_build_connection_entry`` dispatches on the resolved ``mcp-config.format``
# value only — never on a provider name and never on ``surface-version`` (H-1 /
# AC-14, AC-23). On the v2 format the entry drops the frozen v1
# ``enabled: true`` and may carry the documented ``disabled`` / ``timeout`` /
# ``oauth`` keys (spec §3.5, AC-C7/C8/C9); the v1 ``opencode-json`` path and
# every other format stay byte-identical (AC-C11).
#
# Fixture note (Amendment B1 / Spike Q2): these MCP assertions make no
# permission decision, so no ``ask``/``--auto`` fixture is involved; the
# permission fixtures elsewhere in this file carry explicit ``allow``/``deny``.

_V2_STDIO_CONN = {
    "type": "stdio",
    "command": "npx",
    "args": ["-y", "srv"],
    "env": {"API_KEY": "{{API_KEY}}"},
}


def test_ac_c7_v2_entry_has_no_enabled_and_no_disabled_by_default():
    """AC-C7: active v2 servers carry neither ``enabled`` nor ``disabled``."""
    v2 = _build_connection_entry(_V2_STDIO_CONN, None, "opencode-json-v2")
    assert "enabled" not in v2
    assert "disabled" not in v2
    assert v2["type"] == "local"
    assert v2["command"] == ["npx", "-y", "srv"]
    # the frozen v1 entry keeps the active flag
    v1 = _build_connection_entry(_V2_STDIO_CONN, None, "opencode-json")
    assert v1["enabled"] is True


def test_ac_c7_disabled_true_only_with_registry_flag():
    """AC-C7: ``disabled: true`` is emitted only for the literal registry flag."""
    enabled_conn = {"type": "sse", "url": "{{URL}}"}
    registry = {
        "on": {"connection": enabled_conn},
        "off": {"connection": dict(enabled_conn, disabled=True)},
    }
    entries = _build_mcp_entries(["on", "off"], registry, None, "opencode-json-v2")
    assert "disabled" not in entries["on"]
    assert entries["off"]["disabled"] is True

    # No other value is a registry "flag" — the key stays absent.
    for value in (False, "true", 1, None):
        entry = _build_connection_entry(
            dict(enabled_conn, disabled=value), None, "opencode-json-v2"
        )
        assert "disabled" not in entry, value

    # v1 does not know the key (byte freeze).
    v1 = _build_connection_entry(dict(enabled_conn, disabled=True), None, "opencode-json")
    assert "disabled" not in v1


def test_ac_c8_timeout_passthrough_v2_and_absent_v1():
    """AC-C8: v2 passes the millisecond timeouts through, v1 never sees them."""
    conn = {"type": "sse", "url": "{{URL}}", "timeout": {"catalog": 5000, "execution": 60000}}
    v2 = _build_connection_entry(conn, None, "opencode-json-v2")
    assert v2["timeout"] == {"catalog": 5000, "execution": 60000}

    # Amendment B1: the optional ``startup`` budget is carried along.
    with_startup = dict(
        conn, timeout={"startup": 30000, "catalog": 5000, "execution": 60000}
    )
    assert _build_connection_entry(
        with_startup, None, "opencode-json-v2"
    )["timeout"] == {"catalog": 5000, "execution": 60000, "startup": 30000}

    assert "timeout" not in _build_connection_entry(conn, None, "opencode-json")

    # Invalid shapes are not emitted at all (the catalog check reports them).
    invalid = (
        {},
        {"catalog": "5000", "execution": 60000},
        {"catalog": 0, "execution": 60000},
        {"catalog": True, "execution": 60000},
        {"catalog": 5000.5, "execution": 60000},
        {"catalog": 5000, "execution": 60000, "bogus": 1},
        {"catalog": 5000, "execution": 60000, "startup": "30000"},
        "5000",
        None,
    )
    for shape in invalid:
        entry = _build_connection_entry(
            dict(conn, timeout=shape), None, "opencode-json-v2"
        )
        assert "timeout" not in entry, shape


def test_ac_c9_oauth_snake_case_and_plaintext_secret_rejected():
    """AC-C9: snake_case oauth pass-through, plaintext ``client_secret`` aborts."""
    conn = {
        "type": "sse",
        "url": "{{URL}}",
        "oauth": {
            "client_id": "{{OC_ID}}",
            "client_secret": "{{OC_SECRET}}",
            "scope": "read",
        },
    }
    v2 = _build_connection_entry(conn, None, "opencode-json-v2")
    assert v2["oauth"] == {
        "client_id": "{env:OC_ID}",
        "client_secret": "{env:OC_SECRET}",
        "scope": "read",
    }

    # camelCase is not a supported input shape: no oauth key at all
    # (artifact/schema validation reports the catalog entry, Task 17).
    camel = dict(conn, oauth={"clientId": "{{OC_ID}}"})
    assert "oauth" not in _build_connection_entry(camel, None, "opencode-json-v2")
    # v1 does not know oauth (byte freeze).
    assert "oauth" not in _build_connection_entry(conn, None, "opencode-json")

    # A plaintext secret stops through the same error path as the existing
    # committed-config secret gate (``io.write_checked`` -> SyncError).
    plain = dict(
        conn, oauth={"client_id": "{{OC_ID}}", "client_secret": "PLAINTEXT-OC-SECRET"}
    )
    with pytest.raises(SyncError) as excinfo:
        _build_connection_entry(plain, None, "opencode-json-v2")
    assert "oauth.client_secret" in str(excinfo.value)

    # The local/secrets render is allowed (the allow_secrets=True path).
    local = _build_connection_entry(
        conn,
        {"OC_ID": "client-id-value", "OC_SECRET": "resolved-secret-value"},
        "opencode-json-v2",
    )
    assert local["oauth"]["client_secret"] == "resolved-secret-value"


# Checked-in AC-C11 reference: the committed v1 Opencode MCP entry shape. It is
# spelled out here on purpose — the test must not be derived from the builder
# it guards.
_AC_C11_V1_REFERENCE = {
    "filesystem": {
        "type": "local",
        "enabled": True,
        "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp/ws"],
        "environment": {"NODE_ENV": "{env:NODE_ENV}"},
    },
    "search": {
        "type": "remote",
        "enabled": True,
        "url": "{env:SEARCH_URL}",
        "headers": {"Authorization": "Bearer {env:SEARCH_TOKEN}"},
    },
}

_AC_C11_V1_REGISTRY = {
    "filesystem": {
        "connection": {
            "type": "stdio",
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp/ws"],
            "env": {"NODE_ENV": "{{NODE_ENV}}"},
        }
    },
    "search": {
        "connection": {
            "type": "sse",
            "url": "{{SEARCH_URL}}",
            "headers": {"Authorization": "Bearer {{SEARCH_TOKEN}}"},
        }
    },
}


def test_ac_c11_v1_entry_byte_identical_to_reference(tmp_path):
    """AC-C11: the v1 Opencode MCP output is byte-identical to the reference."""
    entries = _build_mcp_entries(
        list(_AC_C11_V1_REFERENCE), _AC_C11_V1_REGISTRY, None, "opencode-json"
    )
    assert entries == _AC_C11_V1_REFERENCE

    path = tmp_path / "opencode.json"
    _write_provider_config(
        path=path,
        mcp_entries=entries,
        fmt="opencode-json",
        log=SyncLog(),
        dry_run=False,
        allow_secrets=True,
    )
    expected = (
        json.dumps({"mcp": _AC_C11_V1_REFERENCE}, indent=2, ensure_ascii=False) + "\n"
    )
    assert path.read_text(encoding="utf-8") == expected


def test_other_formats_ignore_new_connection_keys():
    """Only ``opencode-json-v2`` knows ``disabled``/``timeout``/``oauth``."""
    conn = {
        "type": "sse",
        "url": "{{URL}}",
        "disabled": True,
        "timeout": {"catalog": 5000, "execution": 60000},
        "oauth": {"client_id": "{{OC_ID}}"},
    }
    for fmt in (
        "opencode-json",
        "claude-settings",
        "gemini-settings",
        "vscode-settings",
        "antigravity-mcp-json",
        "continue-yaml",
        "kimi-json",
        "zcode-json",
        "codex-toml-mcp",
        None,
    ):
        entry = _build_connection_entry(conn, None, fmt)
        assert not ({"disabled", "timeout", "oauth"} & set(entry)), fmt


# ===========================================================================
# Phase C2 / Task 16 (C2.3): MCP-managed paths + provider-bound rollback
# ===========================================================================
#
# One managed path per server: ``mcp.servers.<name>`` with the whole server
# object as the managed value (spec §3.5, M-3). Unlike the old wholesale
# replacement, user servers live next to managed ones. The rollback is
# reachable from the early-return paths of ``generate_provider_configs`` (no
# registry, no active servers), so a v2→v1 switch removes the recorded paths
# even when no agent-meta server is active (AC-C17). It never runs for a
# non-owner provider and never touches another writer's state namespace
# (AC-B20/AC-B16).


def _write_mcp_catalog(agent_meta_root: Path, servers: dict) -> None:
    """Write a minimal ``config/plugin-catalog.yaml`` with MCP servers."""
    plugins = {name: {**sdef, "kind": "mcp-server"} for name, sdef in servers.items()}
    (agent_meta_root / "config").mkdir(parents=True, exist_ok=True)
    (agent_meta_root / "config" / "plugin-catalog.yaml").write_text(
        yaml.safe_dump({"version": "1.0.0", "plugins": plugins}), encoding="utf-8"
    )


def _managed_server(url: str = "https://example.invalid/mcp") -> dict:
    return {"description": "managed", "connection": {"type": "sse", "url": url}}


def _sync_mcp(
    project_root: Path,
    config: dict,
    provider_config: dict,
    framework: Path,
    log: SyncLog | None = None,
    dry_run: bool = False,
    provider: str = "Opencode",
) -> SyncLog:
    """Drive the real ``generate_provider_configs`` entry point for one provider."""
    log = log if log is not None else SyncLog()
    generate_provider_configs(
        framework,
        project_root,
        config,
        provider_config,
        log,
        dry_run=dry_run,
        provider=provider,
    )
    return log


def test_ac_b4_user_mcp_server_survives_v2_sync(tmp_path):
    """AC-B4 (MCP part): a user server stays next to the managed one.

    The managed path is ``mcp.servers.<name>`` per server (never a wholesale
    ``mcp`` replacement), so ``my-own`` is untouched. Flat v1-style keys next
    to ``servers`` are dropped: the v2 document allows only ``servers`` under
    ``mcp`` (``artifact_validate._validate_opencode_v2``).
    """
    framework = tmp_path / "fw"
    project = tmp_path / "project"
    _write_mcp_catalog(framework, {"managed": _managed_server()})
    user_server = {"type": "local", "command": ["my-own"]}
    _write_json(
        project / "opencode.json",
        {
            "plugin": ["acme.js"],
            "mcp": {
                "servers": {"my-own": user_server},
                "legacy-flat": {"type": "local", "command": ["old"]},
            },
        },
    )

    _sync_mcp(
        project,
        {"mcp-servers": ["managed"], "platforms": []},
        {"Opencode": _v2_pc()},
        framework,
    )

    doc = _read_json(project / "opencode.json")
    assert doc["plugin"] == ["acme.js"]
    assert doc["mcp"]["servers"]["my-own"] == user_server
    assert doc["mcp"]["servers"]["managed"] == {
        "type": "remote",
        "url": "https://example.invalid/mcp",
    }
    assert "legacy-flat" not in doc["mcp"], (
        "the v2 document allows only 'servers' under 'mcp'"
    )
    state = _read_state_doc(project)[opencode_v2_config.STATE_MCP_KEY]
    assert set(state) == {"mcp.servers.managed"}
    assert state["mcp.servers.managed"]["prior_absent"] is True


def test_ac_c7_disabled_true_reaches_document_end_to_end(tmp_path):
    """RVW-C-03: AC-C7's ``disabled`` flag survives ``generate_provider_configs``.

    A catalog server whose connection carries ``disabled: true`` must reach the
    committed document as ``mcp.servers.<name>.disabled is True`` — and never
    with the v1 ``enabled`` flag.
    """
    framework = tmp_path / "fw"
    project = tmp_path / "project"
    _write_mcp_catalog(
        framework,
        {
            "off": {
                "connection": {
                    "type": "sse",
                    "url": "https://example.invalid/off",
                    "disabled": True,
                }
            }
        },
    )

    _sync_mcp(
        project,
        {"mcp-servers": ["off"], "platforms": []},
        {"Opencode": _v2_pc()},
        framework,
    )

    entry = _read_json(project / "opencode.json")["mcp"]["servers"]["off"]
    assert entry["disabled"] is True
    assert "enabled" not in entry, "v2 never emits the legacy enabled flag"


def test_qa_c04_flat_v1_keys_dropped_with_one_warning_per_key(tmp_path):
    """QA-C-04: a hand-written flat v1 server never disappears silently."""
    framework = tmp_path / "fw"
    project = tmp_path / "project"
    _write_mcp_catalog(framework, {"managed": _managed_server()})
    _write_json(
        project / "opencode.json",
        {
            "mcp": {
                "servers": {"my-own": {"type": "local", "command": ["my-own"]}},
                "legacy-flat": {"type": "local", "command": ["old"]},
                "second-flat": {"type": "remote", "url": "https://example.invalid"},
            }
        },
    )

    log = _sync_mcp(
        project,
        {"mcp-servers": ["managed"], "platforms": []},
        {"Opencode": _v2_pc()},
        framework,
    )

    mcp = _read_json(project / "opencode.json")["mcp"]
    assert set(mcp) == {"servers"}, "only 'servers' is allowed on v2"
    dropped = [w for w in log.warnings if "dropped flat v1 key" in w]
    assert len(dropped) == 2, log.warnings
    assert any("'mcp.legacy-flat'" in w for w in dropped), dropped
    assert any("'mcp.second-flat'" in w for w in dropped), dropped
    assert not any("'mcp.servers'" in w for w in dropped), (
        "the managed container itself is never reported as dropped"
    )


def test_ac_b7_v2_to_v1_with_active_servers_removes_managed_server_paths(tmp_path):
    """AC-B7: a v2→v1 switch with active servers removes the managed v2 paths.

    The rollback runs before the (byte-frozen) v1 writer, so no nested
    ``mcp.servers`` block survives; the v1 writer emits the flat ``mcp`` map
    and the namespace is dropped.
    """
    framework = tmp_path / "fw"
    project = tmp_path / "project"
    _write_mcp_catalog(framework, {"managed": _managed_server()})
    _write_json(project / "opencode.json", {"theme": "dark"})
    config = {"mcp-servers": ["managed"], "platforms": []}

    _sync_mcp(project, config, {"Opencode": _v2_pc()}, framework)
    assert "servers" in _read_json(project / "opencode.json")["mcp"]
    assert opencode_v2_config.STATE_MCP_KEY in _read_state_doc(project)

    _sync_mcp(project, config, {"Opencode": _v1_pc()}, framework)

    doc = _read_json(project / "opencode.json")
    assert "servers" not in doc["mcp"], "managed v2 paths must be gone"
    assert doc["mcp"]["managed"]["enabled"] is True, "v1 writer stays flat"
    assert doc["theme"] == "dark"
    assert opencode_v2_config.STATE_MCP_KEY not in _read_state_doc(project)


def test_ac_c17_v2_to_v1_without_active_servers_removes_managed_paths_keeps_user_entry(
    tmp_path,
):
    """AC-C17: rollback runs on the early return without active servers.

    Previously ``generate_provider_configs`` returned before any cleanup, so a
    v2→v1 switch left an orphaned ``mcp.servers``. Now the recorded managed
    paths are removed, the unrecorded user entry stays and no flat v1 map is
    emitted (there is nothing to write).
    """
    framework = tmp_path / "fw"
    project = tmp_path / "project"
    _write_mcp_catalog(framework, {"managed": _managed_server()})
    user_server = {"type": "local", "command": ["my-own"]}
    _write_json(
        project / "opencode.json",
        {"theme": "dark", "mcp": {"servers": {"my-own": user_server}}},
    )
    _sync_mcp(
        project,
        {"mcp-servers": ["managed"], "platforms": []},
        {"Opencode": _v2_pc()},
        framework,
    )

    log = _sync_mcp(
        project,
        {"mcp-servers": [], "platforms": []},
        {"Opencode": _v1_pc()},
        framework,
    )

    doc = _read_json(project / "opencode.json")
    assert doc["mcp"] == {"servers": {"my-own": user_server}}, (
        "only the managed path is removed; the user server stays"
    )
    assert doc["theme"] == "dark"
    assert "managed" not in doc["mcp"], "no flat v1 map on the early return"
    assert opencode_v2_config.STATE_MCP_KEY not in _read_state_doc(project)
    assert not _warned(log, "opencode-v2-managed"), log.warnings


def test_ac_c17_namespace_removed_after_rollback(tmp_path):
    """AC-C17: the ``opencode-v2-mcp`` namespace is dropped, siblings survive."""
    framework = tmp_path / "fw"
    project = tmp_path / "project"
    _write_mcp_catalog(framework, {"managed": _managed_server()})
    _sync_mcp(
        project,
        {"mcp-servers": ["managed"], "platforms": []},
        {"Opencode": _v2_pc()},
        framework,
    )
    state_path = project / _V2_STATE_REL
    seeded = _read_json(state_path)
    seeded["isolation-deny"] = ["**/.claude/**"]
    _write_json(state_path, seeded)
    assert opencode_v2_config.STATE_MCP_KEY in seeded

    _sync_mcp(
        project,
        {"mcp-servers": [], "platforms": []},
        {"Opencode": _v1_pc()},
        framework,
    )

    after = _read_json(state_path)
    assert opencode_v2_config.STATE_MCP_KEY not in after
    assert after["isolation-deny"] == ["**/.claude/**"]
    assert isolation._read_state(state_path, opencode_v2_config.STATE_MCP_KEY) == {}


def test_ac_b16_mcp_namespace_isolated_from_keys_namespace(tmp_path):
    """AC-B16: the MCP writer owns ``opencode-v2-mcp`` and nothing else."""
    framework = tmp_path / "fw"
    project = tmp_path / "project"
    _write_mcp_catalog(framework, {"managed": _managed_server()})
    _write_json(project / "opencode.json", {"theme": "dark"})
    keys_state = {
        "experimental.todo": {
            "value": True,
            "prior": None,
            "prior_absent": True,
        }
    }
    _write_json(project / _V2_STATE_REL, {STATE_KEYS_KEY: keys_state})

    config = {"mcp-servers": ["managed"], "platforms": []}
    _sync_mcp(project, config, {"Opencode": _v2_pc()}, framework)

    after = _read_json(project / _V2_STATE_REL)
    assert after[STATE_KEYS_KEY] == keys_state, "a foreign namespace is never touched"
    assert set(after[opencode_v2_config.STATE_MCP_KEY]) == {"mcp.servers.managed"}

    file_bytes = (project / "opencode.json").read_bytes()
    state_bytes = (project / _V2_STATE_REL).read_bytes()
    _sync_mcp(project, config, {"Opencode": _v2_pc()}, framework)
    assert (project / "opencode.json").read_bytes() == file_bytes
    assert (project / _V2_STATE_REL).read_bytes() == state_bytes


def test_ac_b20_mcp_rollback_not_run_for_non_owner_provider(tmp_path, monkeypatch):
    """AC-B20: a non-owner iteration leaves file and state byte-identical.

    The read spy makes the test non-vacuous: the ownership guard must run
    before any state access, even though the rollback is reached through the
    normal provider loop.
    """
    framework = tmp_path / "fw"
    project = tmp_path / "project"
    _write_mcp_catalog(framework, {"managed": _managed_server()})
    _sync_mcp(
        project,
        {"mcp-servers": ["managed"], "platforms": []},
        {"Opencode": _v2_pc()},
        framework,
    )
    file_before = (project / "opencode.json").read_bytes()
    state_before = (project / _V2_STATE_REL).read_bytes()

    def _forbidden(*args, **kwargs):
        raise AssertionError("state must not be read for a non-owner provider")

    monkeypatch.setattr(isolation, "_read_state", _forbidden)

    log = SyncLog()
    _sync_mcp(
        project,
        {"mcp-servers": ["managed"], "platforms": []},
        {"Claude": _non_owner_pc()},
        framework,
        log=log,
        provider="Claude",
    )

    assert (project / "opencode.json").read_bytes() == file_before
    assert (project / _V2_STATE_REL).read_bytes() == state_before
    assert (project / ".mcp.json").exists(), "the non-owner writes its own surface"
    leaked = [
        line
        for line in log.actions + log.warnings + log.skipped + log.infos + log.errors
        if "opencode-v2-" in line
    ]
    assert leaked == [], leaked


def test_mcp_writer_passes_secret_gate_params_to_write_checked(tmp_path, monkeypatch):
    """The v2 MCP writer delegates the secret gate to ``io.write_checked``.

    Same parameter shape as ``mcp_provider_config._write_json_config``: an
    override of ``allow-committed-secrets`` is honoured, the committed file is
    never treated as a gitignored local file, and the caller's ``config`` is
    forwarded. ``dry_run`` is passed through unchanged.
    """
    project = tmp_path / "project"
    project.mkdir()
    config = {"allow-committed-secrets": True}
    calls: list = []

    def _capture(*args, **kwargs):
        calls.append((args, kwargs))
        return True

    monkeypatch.setattr(opencode_v2_config.io, "write_checked", _capture)

    entries = {"example": {"type": "remote", "url": "https://example.invalid"}}
    opencode_v2_config.sync_opencode_mcp_managed(
        project, {"Opencode": _v2_pc()}, "Opencode", entries, SyncLog(), False,
        config=config,
    )

    assert len(calls) == 1, calls
    args, kwargs = calls[0]
    assert args[3] == "opencode.json"
    payload = json.loads(args[1])
    assert payload["mcp"]["servers"]["example"] == entries["example"]
    assert kwargs["allow_secrets"] is True
    assert kwargs["verify_gitignored"] is False
    assert kwargs["config"] is config
    assert kwargs["dry_run"] is False


# ===========================================================================
# Phase C3 / Task 18 (C3.1): v2 gate plugin, protocol and data activation
# ===========================================================================
#
# ``VERDICT-C3: GO`` (spike 2026-10-23, ``docs/spikes/2026-10-22-issue-1007-
# opencode-v2-plugin-api-spike.md``) unlocks the native v2 plugin runtime. The
# activation is DATA only: ``surface-plugin-protocols.v2`` and
# ``surface-has-plugins.v2`` on the registry entry are resolved by
# ``providers._apply_surface_aux_selection`` into the flat ``plugin_protocol`` /
# ``has_plugins`` keys. The static ``has_plugins: false`` stays, so a v1 project
# never reaches tier ``plugin`` and never gets an artifact (B-D7 / AC-C13).
#
# The plugin stays additive: ``MODE=observe`` means the permission deny of spec
# §3.4 remains the gate (``isolation.permission_deny_required``), and the v2
# template never registers a blocking ``ctx.permission.hook("evaluate")``


def _resolved_surface_pc(surface: str | None = "v2") -> dict:
    """Resolve the real registry entry for *surface* (``None`` = committed v1)."""
    project_config = (
        None
        if surface is None
        else {"provider-options": {"Opencode": {"surface-version": surface}}}
    )
    return load_providers_config(_REPO_ROOT, project_config)["Opencode"]


def _opencode_caps() -> dict:
    """The declared capability record of the real Opencode registry entry."""
    return load_provider_capabilities(_REPO_ROOT)["Opencode"]


def _sync_gate_plugin(project_root: Path, pc: dict) -> SyncLog:
    """Run the capability-gated plugin writer for one resolved provider entry."""
    log = SyncLog()
    runtime_gate.sync_runtime_gate_plugins(
        _REPO_ROOT,
        project_root,
        {},
        log,
        dry_run=False,
        provider="Opencode",
        provider_config={"Opencode": pc},
    )
    return log


def test_ac_c12_v2_project_gets_plugin_file_and_tier_plugin(tmp_path):
    """AC-C12: the v2 surface resolves to tier ``plugin`` and writes the artifact.

    The entry is the SHIPPED registry (no fixture copy): the C3 keys must exist
    there, the resolved protocol must be ``opencode-plugin-v2-js`` and the
    generated file must carry the v2 object export from spike Q4.
    """
    pc = _resolved_surface_pc("v2")
    caps = _opencode_caps()

    assert pc["has_plugins"] is True
    assert pc["plugin_protocol"] == "opencode-plugin-v2-js"
    assert provider_runtime_gate_tier(pc, caps) == "plugin"
    assert runtime_gate.PLUGIN_TEMPLATE_BY_PROTOCOL["opencode-plugin-v2-js"] == (
        "templates/plugins/runtime-gate.opencode-v2-plugin.js.tmpl"
    )

    log = _sync_gate_plugin(tmp_path, pc)

    target = tmp_path / ".opencode/plugins/agent-meta-runtime-gate.js"
    assert target.is_file(), log.warnings
    content = target.read_text(encoding="utf-8")

    # Same sync-time substitution as the v1 artifact: no placeholder survives.
    assert "{{" not in content
    assert 'MODE = "observe"' in content
    assert 'MODE = "enforce"' not in content

    # Spike Q4: default export OBJECT with id + setup(ctx), hook registration
    # through ctx.tool.hook("execute.before").
    assert "export default {" in content
    assert 'id: "agent-meta-runtime-gate"' in content
    assert "async setup(ctx)" in content
    assert 'ctx.tool.hook("execute.before"' in content
    assert "tool.execute.before" not in content, (
        "the v1 hook name is ignored by the v2 loader (spike Q4)"
    )

    # Observe only: the blocking permission hook must not be registered
    # (`await ctx.permission.hook(…)` is the only registration form).
    assert "await ctx.permission.hook(" not in content


def test_ac_c12_v1_project_keeps_tier_permission_and_no_plugin_file(tmp_path):
    """AC-C12 (v1 half): the static ``has_plugins: false`` keeps v1 frozen.

    Same registry data, default surface ``v1`` → tier ``permission``, the
    static ``opencode-plugin-js`` protocol stays, and the plugin writer creates
    no artifact (and not even the plugin directory).
    """
    pc = _resolved_surface_pc(None)
    caps = _opencode_caps()

    assert pc["surface-version"] == "v1"
    assert pc["has_plugins"] is False
    assert pc["plugin_protocol"] == "opencode-plugin-js", (
        "v1 has no surface-plugin-protocols entry, so the static value stays"
    )
    assert provider_runtime_gate_tier(pc, caps) == "permission"
    assert caps["runtime_gate"] == "permission"

    _sync_gate_plugin(tmp_path, pc)

    assert not (tmp_path / ".opencode/plugins").exists(), (
        "a v1 project must not receive any plugin artifact"
    )


def test_ac_c13_has_plugins_false_resolved_means_no_plugin_file(tmp_path):
    """AC-C13: activation hinges on the RESOLVED ``has_plugins``, not the map.

    A fixture registry offers the v2 protocol but resolves ``has_plugins`` to
    ``false``: no artifact, tier stays ``permission``. The positive control
    (same fixture, map value ``true``) proves the assertion is not vacuous.
    """
    base = {
        "surface-version": "v2",
        "primary-role": "orchestrator",
        "has_plugins": False,
        "plugin_dir": ".opencode/plugins",
        "plugin_ext": ".js",
        "plugin_protocol": "opencode-plugin-js",
        "surface-plugin-protocols": {"v2": "opencode-plugin-v2-js"},
        "mcp-config": _mcp_block("v2"),
        "agent-transform": {"frontmatter-mechanism": "opencode-native-v2"},
    }
    caps = {"runtime_gate": "permission"}

    off_root = tmp_path / "fw-off"
    _write_config(off_root, {"Opencode": dict(base, **{"surface-has-plugins": {"v2": False}})})
    off_pc = load_providers_config(off_root)["Opencode"]
    assert off_pc["plugin_protocol"] == "opencode-plugin-v2-js", (
        "the protocol resolves even though the capability is off"
    )
    assert off_pc["has_plugins"] is False
    assert provider_runtime_gate_tier(off_pc, caps) == "permission"

    project_off = tmp_path / "project-off"
    log = _sync_gate_plugin(project_off, off_pc)
    assert not (project_off / ".opencode/plugins").exists(), log.warnings

    # Positive control: the same fixture with the capability on writes the file.
    on_root = tmp_path / "fw-on"
    _write_config(on_root, {"Opencode": dict(base, **{"surface-has-plugins": {"v2": True}})})
    on_pc = load_providers_config(on_root)["Opencode"]
    assert on_pc["has_plugins"] is True
    assert provider_runtime_gate_tier(on_pc, caps) == "plugin"

    project_on = tmp_path / "project-on"
    _sync_gate_plugin(project_on, on_pc)
    assert (
        project_on / ".opencode/plugins/agent-meta-runtime-gate.js"
    ).is_file(), "positive control must write the artifact"


# --- QA-D-01: the ``has_plugins`` dispatch of the real stage seam ------------
#
# All C3 tests above call ``sync_runtime_gate_plugins`` directly or through
# ``_sync_gate_plugin``; none of them drove the production dispatch. A broken
# ``if pc.get("has_plugins")`` in ``_sync_stage_per_provider`` would therefore
# have left every test green. These two tests pin the dispatch itself against
# the SHIPPED registry entry (v2 dispatches, v1 never does).


def test_qa_d01_stage_dispatches_plugin_writer_for_real_v2_registry(
    tmp_path, monkeypatch
):
    """QA-D-01: the shipped v2 entry dispatches the plugin writer at the seam."""
    pc = _resolved_surface_pc("v2")
    plugin_calls: list = []
    log = SyncLog()

    _, _, gate_calls = _run_stage(
        tmp_path, monkeypatch, {"Opencode": pc}, ["Opencode"],
        _gate_config(), {"Opencode": "plugin"}, log=log,
        plugin_calls=plugin_calls,
    )

    assert gate_calls == [], (
        "tier plugin must not dispatch the Spec-A writer (it is gated on "
        "tier permission)"
    )
    assert len(plugin_calls) == 1, log.warnings + log.actions
    args, _kwargs = plugin_calls[0]
    assert args[5] == "Opencode", "the writer must receive the provider name"
    assert args[6] == {"Opencode": pc}, (
        "the writer must receive the resolved provider registry (not a single "
        "provider entry)"
    )


def test_qa_d01_stage_does_not_dispatch_plugin_writer_for_v1(
    tmp_path, monkeypatch
):
    """QA-D-01 (v1 half): the shipped v1 entry never dispatches the writer.

    Same seam, same test body — only the resolved surface differs. The v1
    entry keeps the static ``has_plugins: false``, so the writer must not be
    called at all (``test_plugin_dispatch_noop_without_capability`` proves the
    same for a synthetic fixture).
    """
    pc = _resolved_surface_pc(None)
    assert pc["has_plugins"] is False, (
        "non-vacuity: the v1 entry really resolves the capability off"
    )
    plugin_calls: list = []
    log = SyncLog()

    _run_stage(
        tmp_path, monkeypatch, {"Opencode": pc}, ["Opencode"],
        _gate_config(), {"Opencode": "permission"}, log=log,
        plugin_calls=plugin_calls,
    )

    assert plugin_calls == [], "a v1 surface must never dispatch the plugin writer"
    assert not (tmp_path / "project" / ".opencode" / "plugins").exists()


# ===========================================================================
# Phase C3 / Task 19 (C3.2): assurance tests for tier ``plugin``
# ===========================================================================
#
# No production code here: the behaviour under test already lives in
# ``isolation.permission_deny_required`` (Task 13) and
# ``isolation.reconcile_opencode_surface_gate`` (Task 13a). These tests pin it
# against the SHIPPED registry (Task 18: ``surface-plugin-protocols.v2`` /
# ``surface-has-plugins.v2``), so an edit to the registry data or a lost
# observe branch fails loudly (AC-C14, OQ-B12).
#
# Fixtures use the real registry entry and real capabilities — no synthetic
# ``has_plugins``/``plugin_protocol`` stub — because the point of C3 is that
# the DATA resolves to tier ``plugin``. Explicit ``allow``/``deny`` project
# entries keep the probe deterministic (Spike Q2: default ``ask`` plus
# ``--auto`` is not a confirmation).


def test_ac_c14_real_v2_registry_plugin_observe_keeps_deny_triples(
    tmp_path, monkeypatch
):
    """AC-C14: on the shipped v2 registry ``observe`` keeps the deny triples.

    Tier ``plugin`` comes from the machine flags, not from a fixture:
    ``provider_runtime_gate_tier`` must return ``"plugin"`` for the resolved v2
    entry. ``permission_deny_required`` is then the single decision that keeps
    the deny additive in ``observe`` mode and drops it in ``enforce`` mode —
    the latter without ``_sync_opencode_runtime_gate`` ever running (it is
    gated on tier ``permission``).
    """
    pc = _resolved_surface_pc("v2")
    caps = _opencode_caps()

    # Non-vacuity: the real registry really is in the C3 plugin state.
    assert pc["has_plugins"] is True, "the shipped v2 entry lost surface-has-plugins.v2"
    assert pc["plugin_protocol"] == "opencode-plugin-v2-js"
    assert provider_runtime_gate_tier(pc, caps) == "plugin"

    # The predicate itself, over real resolved data.
    assert isolation.permission_deny_required(pc, caps, "observe") is True, (
        "a plugin in observe mode never blocks, so the deny must stay"
    )
    assert isolation.permission_deny_required(pc, caps, "enforce") is False, (
        "an enforcing plugin blocks on its own; the redundant deny is dropped"
    )

    project = tmp_path / "project"
    monkeypatch.setattr(runtime_gate, "_baked_plugin_mode", lambda: "observe")
    log = SyncLog()
    _reconcile(project, _gate_config(), {"Opencode": pc}, _REPO_ROOT, log=log)

    doc = _read_json(project / "opencode.json")
    assert doc["permissions"] == [_EDIT_DENY, _SHELL_DENY], (
        "tier plugin + observe must keep both deny triples (AC-C14)"
    )
    assert _read_state_doc(project)[_V2_GATE_STATE_KEY]["triples"] == [
        ["edit", "**", "deny"],
        ["shell", "**", "deny"],
    ]

    monkeypatch.setattr(runtime_gate, "_baked_plugin_mode", lambda: "enforce")
    _reconcile(project, _gate_config(), {"Opencode": pc}, _REPO_ROOT)

    assert "permissions" not in _read_json(project / "opencode.json"), (
        "enforce removes the triples although the Spec-A writer never ran"
    )
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project)
    assert not any(
        "runtime gate (permission.edit/bash deny)" in warning
        for warning in log.warnings
    ), log.warnings


def test_oqb12_tier_plugin_writes_no_default_agent_but_checks_entry_point(
    tmp_path, monkeypatch
):
    """OQ-B12: tier ``plugin`` skips Spec-A step 3; reconcile checks it itself.

    Spec A's ``default_agent`` merge is called under the unchanged tier
    ``permission`` condition (Spec-A freeze, IC-7), so on tier ``plugin`` the
    stage dispatch never reaches it. ``reconcile_opencode_surface_gate``
    therefore evaluates the entry point on its own (``_opencode_entry_point``)
    and writes no ``default_agent``; a missing entry point yields exactly one
    WARNING and no triple.
    """
    pc = _resolved_surface_pc("v2")
    caps = _opencode_caps()
    assert provider_runtime_gate_tier(pc, caps) == "plugin"

    monkeypatch.setattr(runtime_gate, "_baked_plugin_mode", lambda: "observe")

    # (a) The real stage seam at tier ``plugin``: Spec-A is not dispatched.
    project, _, gate_calls = _run_stage(
        tmp_path / "plugin-tier", monkeypatch, {"Opencode": pc}, ["Opencode"],
        _gate_config(), {"Opencode": "plugin"},
    )
    assert gate_calls == [], (
        "tier plugin must not dispatch the Spec-A writer (its step 3 owns "
        "default_agent) — the reconcile function is the only actor"
    )
    doc = _read_json(project / "opencode.json")
    assert "default_agent" not in doc, (
        "reconcile must not write default_agent at tier plugin (OQ-B12 default)"
    )
    assert doc["permissions"] == [_EDIT_DENY, _SHELL_DENY], (
        "the reconcile function must still keep the deny triples"
    )

    # (b) No entry point: reconcile checks it and warns exactly once itself.
    entry_point_calls = []
    real_entry_point = isolation._opencode_entry_point

    def _spy(provider, provider_config, active_set):
        role = real_entry_point(provider, provider_config, active_set)
        entry_point_calls.append(role)
        return role

    monkeypatch.setattr(isolation, "_opencode_entry_point", _spy)

    pc_without_role = _resolved_surface_pc("v2")
    pc_without_role.pop("primary-role")
    assert provider_runtime_gate_tier(pc_without_role, caps) == "plugin", (
        "the tier is flag-derived and must not depend on the entry point"
    )

    project_no_entry = tmp_path / "no-entry"
    log = SyncLog()
    _reconcile(
        project_no_entry, _gate_config(), {"Opencode": pc_without_role}, _REPO_ROOT,
        log=log,
    )

    assert entry_point_calls, (
        "reconcile must evaluate the entry point itself via _opencode_entry_point"
    )
    assert set(entry_point_calls) == {None}, entry_point_calls
    warnings = [w for w in log.warnings if "primary-role" in w]
    assert len(warnings) == 1, log.warnings
    assert "lock every agent" in warnings[0], warnings[0]
    assert not (project_no_entry / "opencode.json").exists(), (
        "no entry point => no triple, so the document is never created"
    )
    assert _V2_GATE_STATE_KEY not in _read_state_doc(project_no_entry)


def test_ac_c16a_no_default_agent_reconciliation_at_tier_plugin(
    tmp_path, monkeypatch
):
    """AC-C16(a) as scoped by Amendment B4 (QA-D-02): no reconciliation at ``plugin``.

    Amendment B4 narrows AC-C16(a): the ``default_agent`` managed merge (with
    its ``default-agent`` state and its user-value warning) runs on tier
    ``permission`` only, because Spec A's call condition is frozen at
    ``== "permission"`` (OQ-B12: "Eigenprüfung genügt"). On the C3 v2 surface
    (tier ``plugin``) ``settings-init`` writes ``default_agent`` once and
    ``reconcile_opencode_surface_gate`` only CHECKS the entry point — nothing
    reconciles afterwards. A user-deleted ``default_agent`` therefore stays
    deleted (accepted limitation).

    The permission-tier half is the non-vacuity control: the same seeded
    document *does* get ``default_agent`` re-added there, because the real
    managed merge runs.
    """
    pc = _resolved_surface_pc("v2")
    caps = _opencode_caps()
    assert provider_runtime_gate_tier(pc, caps) == "plugin"

    monkeypatch.setattr(runtime_gate, "_baked_plugin_mode", lambda: "observe")

    # (a) settings-init writes `default_agent` once — and only once.
    base = tmp_path / "plugin"
    project = base / "project"
    project.mkdir(parents=True)
    (project / "opencode.json").write_text(_v2_settings_shape(), encoding="utf-8")
    seeded = _read_json(project / "opencode.json")
    assert seeded["default_agent"] == "orchestrator", (
        "settings-init must write default_agent from primary-role"
    )
    assert not (project / _V2_STATE_REL).exists(), (
        "settings-init records no managed state"
    )

    # (b) A full stage run at tier plugin neither removes nor re-records it.
    log = SyncLog()
    _, _, gate_calls = _run_stage(
        base, monkeypatch, {"Opencode": pc}, ["Opencode"],
        _gate_config(), {"Opencode": "plugin"}, log=log,
    )
    assert gate_calls == [], (
        "tier plugin must not dispatch the Spec-A writer — it owns the "
        "default_agent merge (Amendment B4)"
    )
    doc = _read_json(project / "opencode.json")
    assert doc["default_agent"] == "orchestrator", (
        "reconcile must leave the settings-init value untouched"
    )
    assert isolation._STATE_DEFAULT_AGENT_KEY not in _read_state_doc(project), (
        "tier plugin writes no default-agent state, so no rollback/reconcile "
        "exists for it"
    )
    assert not _warned(log, "default_agent"), log.warnings

    # (c) The accepted limitation: a user-deleted value is not re-added, and
    #     no user-value warning appears (no merge runs at all).
    del doc["default_agent"]
    _write_json(project / "opencode.json", doc)
    before = (project / "opencode.json").read_bytes()
    stage_log = SyncLog()
    _run_stage(
        base, monkeypatch, {"Opencode": pc}, ["Opencode"],
        _gate_config(), {"Opencode": "plugin"}, log=stage_log,
    )

    assert (project / "opencode.json").read_bytes() == before, (
        "no writer may touch (or re-add) default_agent at tier plugin"
    )
    markers = ("default_agent", "opencode-v2-managed", "primary-role")
    leaked = [w for w in stage_log.warnings if any(m in w for m in markers)]
    assert leaked == [], leaked

    # (d) Non-vacuity control: at tier permission the managed merge runs and
    #     re-adds the deleted value (the behaviour AC-C16(a) originally meant).
    control_base = tmp_path / "permission"
    control_project = control_base / "project"
    control_project.mkdir(parents=True)
    control_doc = json.loads(_v2_settings_shape())
    del control_doc["default_agent"]
    _write_json(control_project / "opencode.json", control_doc)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    control_pc = _v2_pc()  # same v2 surface, without the plugin capability
    assert provider_runtime_gate_tier(control_pc, {"runtime_gate": "permission"}) == (
        "permission"
    ), "control precondition: without has_plugins the tier stays permission"

    _run_runtime_gate(control_project, framework, {"Opencode": control_pc})

    control_after = _read_json(control_project / "opencode.json")
    assert control_after["default_agent"] == "orchestrator", (
        "on tier permission the managed merge must re-add the deleted value"
    )
    assert isolation._STATE_DEFAULT_AGENT_KEY in _read_state_doc(control_project)


def test_v1_tier_permission_unchanged_with_c3_registry(tmp_path):
    """AC-C14 / v1: the same registry data keeps v1 on tier ``permission``.

    ``surface-plugin-protocols``/``surface-has-plugins`` are surface-keyed;
    the v1 resolution must keep the static ``has_plugins: false`` and the
    static protocol, so v1 stays on the unchanged Spec-A path
    (``permission`` map plus ``default_agent``) and the mode never matters.
    """
    v1 = _resolved_surface_pc(None)
    v2 = _resolved_surface_pc("v2")
    caps = _opencode_caps()

    # The C3 data is shared registry data, not a v2-only entry.
    assert v1["surface-plugin-protocols"] == {"v2": "opencode-plugin-v2-js"}
    assert v1["surface-has-plugins"] == {"v2": True}
    assert provider_runtime_gate_tier(v2, caps) == "plugin", (
        "positive control: the same entry is plugin-tier on the v2 surface"
    )

    assert v1["has_plugins"] is False, "the static v1 flag stays false"
    assert v1["plugin_protocol"] == "opencode-plugin-js", (
        "no surface-plugin-protocols entry for v1, so the static value stays"
    )
    assert provider_runtime_gate_tier(v1, caps) == "permission"
    for mode in ("observe", "enforce"):
        assert isolation.permission_deny_required(v1, caps, mode) is True, (
            f"tier permission never depends on the plugin mode (mode={mode})"
        )

    # Behavioural check: v1 still goes through the Spec-A writer (permission
    # map + default_agent), never through the triples.
    project = tmp_path / "project"
    log = SyncLog()
    _run_runtime_gate(project, _REPO_ROOT, {"Opencode": v1}, log=log)
    doc = _read_json(project / "opencode.json")
    assert doc["permission"] == {
        "edit": {"**": "deny"},
        "bash": {"**": "deny"},
    }, log.warnings
    assert doc["default_agent"] == "orchestrator"
    assert "permissions" not in doc


# --- AC-D1 / AC-C6: closed-world v2 permission builder ----------------------


def test_ac_d1_builder_allows_mapped_actions():
    """AC-D1 (3.7): mapped Claude tools yield one ``allow`` entry per action.

    ``Write``/``Edit`` -> ``edit``, ``Bash`` -> ``shell``, ``Agent`` ->
    ``subagent``. The result is an ordered list with exactly one entry per
    action in the fixed order ``edit``, ``shell``, ``subagent``.
    """
    assert provider_transform.map_tools_to_opencode_v2_permissions(
        ["Bash", "Read", "Write", "Edit", "Agent"],
    ) == [
        {"action": "edit", "resource": "*", "effect": "allow"},
        {"action": "shell", "resource": "*", "effect": "allow"},
        {"action": "subagent", "resource": "*", "effect": "allow"},
    ]

    # Partial mapping: only the mapped actions are allowed, the order stays.
    assert provider_transform.map_tools_to_opencode_v2_permissions(
        ["Bash", "Read"],
    ) == [
        {"action": "edit", "resource": "*", "effect": "deny"},
        {"action": "shell", "resource": "*", "effect": "allow"},
        {"action": "subagent", "resource": "*", "effect": "deny"},
    ]
    assert provider_transform.map_tools_to_opencode_v2_permissions(
        ["Write", "Edit", "Agent"],
    ) == [
        {"action": "edit", "resource": "*", "effect": "allow"},
        {"action": "shell", "resource": "*", "effect": "deny"},
        {"action": "subagent", "resource": "*", "effect": "allow"},
    ]
    # A single ``Write`` is enough for the ``edit`` action.
    assert provider_transform.map_tools_to_opencode_v2_permissions(["Write"])[0] == {
        "action": "edit", "resource": "*", "effect": "allow",
    }


def test_ac_d1_builder_closed_world_denies_unmapped_actions():
    """AC-D1 (M-5): a read-only role gets all three actions ``deny``.

    Closed-world: unmapped actions are denied, never omitted, so a role
    without ``Write``/``Edit`` cannot silently gain ``edit`` rights.
    """
    assert provider_transform.map_tools_to_opencode_v2_permissions(["Read"]) == [
        {"action": "edit", "resource": "*", "effect": "deny"},
        {"action": "shell", "resource": "*", "effect": "deny"},
        {"action": "subagent", "resource": "*", "effect": "deny"},
    ]
    # Every entry carries the same closed-world shape.
    for entry in provider_transform.map_tools_to_opencode_v2_permissions([]):
        assert entry["resource"] == "*"
        assert entry["effect"] == "deny"
    # Unknown / unmapped tools never widen the surface.
    unmapped = ["Glob", "Grep", "TodoWrite"]
    assert provider_transform.map_tools_to_opencode_v2_permissions(unmapped) == [
        {"action": "edit", "resource": "*", "effect": "deny"},
        {"action": "shell", "resource": "*", "effect": "deny"},
        {"action": "subagent", "resource": "*", "effect": "deny"},
    ]


def test_ac_d1_builder_ignores_deny_list():
    """AC-D1 (3.7): ``deny_list``/``opencode_deny_critical`` has no effect.

    The v1 deny list exists to close the *map* surface; the v2 builder is
    closed-world by construction, so the same roles stay identical whether the
    list is omitted, empty or populated.
    """
    tools = ["Bash", "Write", "Edit", "Agent"]
    without = provider_transform.map_tools_to_opencode_v2_permissions(tools)
    assert provider_transform.map_tools_to_opencode_v2_permissions(
        tools, deny_list=None,
    ) == without
    assert provider_transform.map_tools_to_opencode_v2_permissions(
        tools, deny_list=[],
    ) == without
    assert provider_transform.map_tools_to_opencode_v2_permissions(
        tools, deny_list=["Bash", "Write", "Edit"],
    ) == without
    assert without == [
        {"action": "edit", "resource": "*", "effect": "allow"},
        {"action": "shell", "resource": "*", "effect": "allow"},
        {"action": "subagent", "resource": "*", "effect": "allow"},
    ]
    # read-only role stays closed-world regardless of the deny list.
    read_only = provider_transform.map_tools_to_opencode_v2_permissions(["Read"])
    assert provider_transform.map_tools_to_opencode_v2_permissions(
        ["Read"], deny_list=["Bash", "Write", "Edit"],
    ) == read_only


def test_ac_c6_v1_mapper_unchanged():
    """AC-C6 / decision 8: the v1 permission map stays frozen.

    The v1 mapper keeps its own vocabulary (``bash``/``read``/``edit``/...)
    and its allow-then-deny semantics; the v2 builder must not touch it.
    """
    full_reference = {
        "bash": "allow",
        "read": "allow",
        "edit": "allow",
        "glob": "allow",
        "grep": "allow",
        "webfetch": "allow",
        "websearch": "allow",
        "task": "allow",
        "todowrite": "allow",
    }
    assert provider_transform._map_claude_tools_to_opencode_permissions(
        ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch",
         "WebSearch", "Agent", "TodoWrite"],
    ) == full_reference
    # An explicitly allowed tool wins over the deny list (unchanged v1 rule).
    assert provider_transform._map_claude_tools_to_opencode_permissions(
        ["Bash", "Read", "Write", "Edit", "Glob", "Grep", "WebFetch",
         "WebSearch", "Agent", "TodoWrite"],
        deny_list=["Bash", "Write", "Edit"],
    ) == full_reference
    # Deny only applies to tools the template did not allow.
    assert provider_transform._map_claude_tools_to_opencode_permissions(
        ["Read"], deny_list=["Bash", "Write", "Edit"],
    ) == {"read": "allow", "bash": "deny", "edit": "deny"}


# ===========================================================================
# Phase D1 / Task 21 (D1.2): native v2 agent frontmatter
# ===========================================================================
#
# Spec §3.7 / AC-D1-D4: the ``opencode-native-v2`` mechanism gets its own
# frontmatter builder instead of sharing the v1 one. A v2 artifact carries
# ``permissions:`` (closed-world list of ``{action, resource, effect}``),
# ``steps`` (never the ``maxSteps`` alias and never the v1 sampling fields),
# ``model`` with an optional ``#variant``, never ``tools``, never
# ``subagent_depth`` and never a separate ``system:`` field — the Markdown body
# IS the system prompt (Spike Q5, VERIFIED). The v1 builder and the Mammouth
# path (``opencode-native`` without a surface mechanism) stay byte-identical.

_V2_TEMPLATE = (
    "---\n"
    "name: template-developer\n"
    'version: "2.0.0"\n'
    "description: old description\n"
    "{tools}"
    "{extra}"
    "---\n"
    "\n"
    "Body content.\n"
)

_V2_FULL_TOOLS = ("Read", "Write", "Bash", "Agent")


def _v2_template(tools=_V2_FULL_TOOLS, extra=""):
    tools_block = ""
    if tools:
        tools_block = "tools:\n" + "".join(f"  - {tool}\n" for tool in tools)
    return _V2_TEMPLATE.format(tools=tools_block, extra=extra)


def _frontmatter_of(content: str) -> dict:
    return yaml.safe_load(content.split("---", 2)[1]) or {}


def _render_opencode_v2(content: str, *, model: str = "", steps: str = "",
                        variant: str | None = None) -> str:
    return provider_transform._transform_frontmatter_for_opencode_v2(
        content, "developer", "new description", model, steps,
        "1-generic/developer.md@2.0.0", _REPO_ROOT, variant=variant,
    )


def test_ac_d1_v2_artifact_has_permissions_list_and_no_legacy_keys():
    """AC-D1 (3.7 a/d/e): ``permissions[]`` replaces the v1 legacy surface.

    No ``permission:`` map, no ``tools:``, no ``maxSteps``, no
    ``subagent_depth``, no sampling fields and no separate ``system:`` field;
    ``permissions`` is a list of ``{action, resource, effect}`` with one entry
    per action in the fixed order.
    """
    content = _v2_template(
        extra=(
            "permission:\n"
            "  edit: allow\n"
            "subagent_depth: 3\n"
            "maxSteps: 40\n"
            "temperature: 0.2\n"
            "max_tokens: 1000\n"
            "top_p: 0.9\n"
            "system: legacy prompt\n"
        ),
    )
    fm = _frontmatter_of(_render_opencode_v2(content))

    assert fm["permissions"] == [
        {"action": "edit", "resource": "*", "effect": "allow"},
        {"action": "shell", "resource": "*", "effect": "allow"},
        {"action": "subagent", "resource": "*", "effect": "allow"},
    ]
    for legacy in (
        "permission", "tools", "maxSteps", "subagent_depth", "system",
        "temperature", "max_tokens", "top_p",
    ):
        assert legacy not in fm, f"{legacy} must not appear in a v2 artifact"
    # The body stays the system prompt: it is never moved into the frontmatter.
    assert fm["name"] == "developer"
    assert fm["description"] == "new description"


def test_ac_d1_role_without_write_has_edit_deny():
    """AC-D1 (M-5): a role without ``Write``/``Edit`` gets ``edit: deny``.

    Closed-world: the action is still present, it is just denied — regardless
    of ``opencode_deny_critical``.
    """
    role_with_shell = _frontmatter_of(
        _render_opencode_v2(_v2_template(["Read", "Grep", "Glob", "Bash", "Agent"])),
    )
    assert {
        entry["action"]: entry["effect"] for entry in role_with_shell["permissions"]
    } == {"edit": "deny", "shell": "allow", "subagent": "allow"}

    read_only = _frontmatter_of(
        _render_opencode_v2(_v2_template(["Read", "Grep", "TodoWrite"])),
    )
    assert read_only["permissions"] == [
        {"action": "edit", "resource": "*", "effect": "deny"},
        {"action": "shell", "resource": "*", "effect": "deny"},
        {"action": "subagent", "resource": "*", "effect": "deny"},
    ]


def test_ac_d2_steps_emitted_without_maxsteps():
    """AC-D2 (3.7 b): ``steps`` is emitted, ``maxSteps`` never is."""
    for extra in ("steps: 40\n", "maxSteps: 40\n"):
        fm = _frontmatter_of(_render_opencode_v2(_v2_template(extra=extra)))
        assert fm["steps"] == 40, extra
        assert "maxSteps" not in fm, extra

    # Template frontmatter wins over the resolved role default, exactly like v1.
    fm = _frontmatter_of(
        _render_opencode_v2(_v2_template(extra="steps: 40\n"), steps="25"),
    )
    assert fm["steps"] == 40


def test_ac_d3_variant_appended_to_model_only_for_configured_role(tmp_path):
    """AC-D3 (3.7 c): ``#variant`` only for the configured role.

    The variant comes from ``provider-options.<provider>.model-variants[<role>]``
    and is appended to the resolved model ID — roles without an entry keep the
    plain ID, and an absent model stays absent.
    """
    model = "opencode-go/deepseek-v4-pro"
    assert _frontmatter_of(
        _render_opencode_v2(_v2_template(), model=model, variant="high"),
    )["model"] == f"{model}#high"
    assert _frontmatter_of(
        _render_opencode_v2(_v2_template(), model=model),
    )["model"] == model
    assert "model" not in _frontmatter_of(
        _render_opencode_v2(_v2_template(), variant="high"),
    )

    # Branch wiring: the mechanism branch resolves the variant per role.
    registry = load_providers_config(_REPO_ROOT)
    opencode = json.loads(json.dumps(registry["Opencode"]))
    opencode["agent-transform"]["frontmatter-mechanism"] = "opencode-native-v2"
    provider_config = dict(registry)
    provider_config["Opencode"] = opencode
    config = {
        "model-overrides": {"Opencode": {
            "developer": model,
            "code-reviewer": "opencode-go/deepseek-v4-flash",
        }},
        "provider-options": {"Opencode": {
            "model-variants": {"developer": "high"},
        }},
    }

    def _render_role(role: str) -> dict:
        return _frontmatter_of(
            provider_transform.transform_agent_content_for_provider(
                _v2_template(), "Opencode", role, role, "new description",
                f"1-generic/{role}.md@2.0.0", config, _REPO_ROOT, tmp_path,
                tmp_path / f"{role}.md", provider_config, SyncLog(),
            ),
        )

    assert _render_role("developer")["model"] == f"{model}#high"
    assert _render_role("code-reviewer")["model"] == "opencode-go/deepseek-v4-flash"


def test_ac_d4_v1_artifacts_byte_identical_to_pre_change_output(tmp_path):
    """AC-D4 / decision 10: the v1 builder output is byte-frozen.

    Reference captured from ``_transform_frontmatter_for_opencode`` before the
    v2 builder existed; the mechanism branch keeps routing v1 projects to that
    exact function (``permission:`` map, no ``permissions:`` list).
    """
    content = _v2_template(
        extra="steps: 40\ntemperature: 0.2\nmax_tokens: 1000\ntop_p: 0.9\n",
    )
    expected = (
        "---\n"
        "name: developer\n"
        "version: 2.0.0\n"
        "description: new description\n"
        "steps: 40\n"
        "temperature: 0.2\n"
        "max_tokens: 1000\n"
        "mode: subagent\n"
        "generated-from: 1-generic/developer.md@2.0.0\n"
        "model: opencode-go/deepseek-v4-flash\n"
        "permission:\n"
        "  read: allow\n"
        "  edit: allow\n"
        "  bash: allow\n"
        "  task: allow\n"
        "---\n"
        "Body content.\n"
    )
    assert provider_transform._transform_frontmatter_for_opencode(
        content, "developer", "new description",
        model="opencode-go/deepseek-v4-flash", steps="",
        generated_from="1-generic/developer.md@2.0.0",
        agent_meta_root=_REPO_ROOT,
    ) == expected

    # Real v1 registry: the opencode-native mechanism still dispatches to the
    # unchanged builder — `permission:` map, never a `permissions:` list.
    v1_artifact = provider_transform.transform_agent_content_for_provider(
        _v2_template(), "Opencode", "developer", "developer", "new description",
        "1-generic/developer.md@2.0.0", {}, _REPO_ROOT, tmp_path,
        tmp_path / "developer.md", load_providers_config(_REPO_ROOT), SyncLog(),
    )
    v1_fm = _frontmatter_of(v1_artifact)
    assert "permission" in v1_fm
    assert "permissions" not in v1_fm


# ===========================================================================
# Phase D1 / Task 22 (D1.3): agent-level edit deny, Mammouth isolation, `system`
# ===========================================================================
#
# Spec §3.4 ("Agent-Ebene"), §3.7, AC-C16(b), AC-D6, AC-C14 (Amendment B3):
#
# * `deny_edit=True` turns the primary role's closed-world `edit: allow` entry
#   into `{action: edit, resource: "*", effect: deny}` followed by one `allow`
#   entry per path in `opencode_primary_edit_allow` — the `*` deny comes FIRST
#   because last match wins (Amendment B1, Spike Q3 VERIFIED);
# * the frontmatter call site resolves `deny_edit` with
#   `isolation.permission_deny_required(provider_config, capabilities,
#   plugin_mode)` — NOT with the frozen `opencode_runtime_gate_wanted` (tier
#   `permission` only), so tier `plugin` + `observe` is covered too (Amendment
#   B3, AC-C14 on the agent level);
# * a provider without `surface-mechanisms` (the Mammouth fork) stays on the
#   `opencode-native` v1 path and is only reported through the REV-R5 warning;
# * `system` is part of the Opencode `agent-transform.allowed-fields` registry.

_V2_ORCHESTRATOR_TOOLS = ("Read", "Grep", "Glob", "Bash", "Edit", "Write", "Agent")


def _registry_for_surface(surface: str) -> dict:
    """The real registry resolved for *surface* via the project option channel."""
    return load_providers_config(
        _REPO_ROOT, {"provider-options": {"Opencode": {"surface-version": surface}}},
    )


def _render_orchestrator(
    tmp_path: Path,
    project_config: dict,
    *,
    registry: dict | None = None,
    tools: tuple[str, ...] = _V2_ORCHESTRATOR_TOOLS,
) -> dict:
    """Render the primary orchestrator artifact and return its frontmatter."""
    if registry is None:
        registry = _registry_for_surface("v2")
    rendered = provider_transform.transform_agent_content_for_provider(
        _v2_template(tools), "Opencode", "orchestrator", "orchestrator", "desc",
        "1-generic/orchestrator.md@2.0.0", project_config, _REPO_ROOT,
        tmp_path, tmp_path / "orchestrator.md", registry, SyncLog(),
    )
    return _frontmatter_of(rendered)


def _edit_entries(permissions: list[dict]) -> list[tuple[int, dict]]:
    return [
        (index, entry)
        for index, entry in enumerate(permissions)
        if entry.get("action") == "edit"
    ]


def _assert_scoped_edit_deny(permissions: list[dict]) -> None:
    """AC-C16(b) + Amendment B1: `*` deny first, then the configured allows."""
    edit = _edit_entries(permissions)
    assert edit, permissions
    deny_index, deny_entry = edit[0]
    assert deny_entry == {"action": "edit", "resource": "*", "effect": "deny"}, edit

    allows = [(index, entry) for index, entry in edit if entry["effect"] == "allow"]
    assert [entry["resource"] for _, entry in allows] == [".tmp/**", ".meta-viz/**"]
    assert all(entry["resource"] != "*" for _, entry in allows)
    assert all(index > deny_index for index, _ in allows), (
        "the root deny must precede the path allows — last match wins in Opencode"
    )


def test_ac_c16b_orchestrator_artifact_has_edit_deny_when_gate_active(tmp_path):
    """AC-C16(b), tier `permission` + strict: the primary edit scope is closed."""
    project_config = {"orchestrator": {"mode": "strict"}}
    fm = _render_orchestrator(tmp_path, project_config)

    assert fm["mode"] == "primary"
    _assert_scoped_edit_deny(fm["permissions"])
    # The gate never reaches into the other actions.
    assert {
        entry["action"]: entry["effect"]
        for entry in fm["permissions"] if entry["action"] != "edit"
    } == {"shell": "allow", "subagent": "allow"}


def test_ac_c16b_no_edit_deny_without_gate(tmp_path):
    """AC-C16(b): without an active gate the template-derived allow survives."""
    fm = _render_orchestrator(tmp_path, {})

    assert fm["mode"] == "primary"
    assert isinstance(fm["permissions"], list), "v2 surface expected"
    assert _edit_entries(fm["permissions"]) == [
        (0, {"action": "edit", "resource": "*", "effect": "allow"}),
    ]


def test_ac_c14_orchestrator_artifact_has_edit_deny_at_plugin_observe(tmp_path):
    """AC-C14 (Amendment B3): tier `plugin` + `observe` still denies at the agent level.

    The config triples use `permission_deny_required`, and the agent level MUST
    use the same predicate: with the frozen `opencode_runtime_gate_wanted`
    (tier `permission` only) this artifact would keep `edit: allow` and, being
    appended last, overrule the global deny.
    """
    registry = _registry_for_surface("v2")
    pc = registry["Opencode"]
    caps = load_provider_capabilities(_REPO_ROOT)
    assert provider_runtime_gate_tier(pc, caps.get("Opencode")) == "plugin"
    assert runtime_gate._baked_plugin_mode() == "observe"
    assert isolation.permission_deny_required(
        pc, caps.get("Opencode"), runtime_gate._baked_plugin_mode(),
    ) is True

    fm = _render_orchestrator(
        tmp_path, {"orchestrator": {"mode": "strict"}}, registry=registry,
    )

    _assert_scoped_edit_deny(fm["permissions"])
    assert fm["mode"] == "primary"


def test_ac_d6_mammouth_with_surface_v2_keeps_opencode_native_output(tmp_path):
    """AC-D6: a fork without `surface-mechanisms` keeps the v1 surface (REV-R5).

    Mammouth declares an explicit non-default `surface-version` without a
    `mcp-config.surface-formats` map, so the selection is a no-op and the
    resolution reports the REV-R5 warning. The agent artifact therefore keeps
    the `permission:` map — never a v2 `permissions:` list.
    """
    from lib import providers as providers_lib

    entry = json.loads(json.dumps(load_providers_config(_REPO_ROOT)["Mammouth"]))
    entry["surface-version"] = "v2"
    assert "surface-mechanisms" not in (entry.get("agent-transform") or {})
    _write_config(tmp_path, {"Mammouth": entry})
    registry = load_providers_config(tmp_path)

    assert registry["Mammouth"]["agent-transform"]["frontmatter-mechanism"] == (
        "opencode-native"
    )
    warnings = providers_lib._surface_version_warnings(registry)
    assert len(warnings) == 1, warnings
    assert "Mammouth" in warnings[0]
    assert "surface-formats" in warnings[0]

    rendered = provider_transform.transform_agent_content_for_provider(
        _v2_template(_V2_ORCHESTRATOR_TOOLS), "Mammouth", "orchestrator",
        "orchestrator", "desc", "1-generic/orchestrator.md@2.0.0", {}, _REPO_ROOT,
        tmp_path, tmp_path / "orchestrator.md", registry, SyncLog(),
    )
    fm = _frontmatter_of(rendered)

    assert isinstance(fm.get("permission"), dict), fm
    assert fm["permission"]["edit"] == "allow"
    assert "permissions" not in fm


def test_system_in_allowed_fields():
    """Task 22: `system` belongs to the Opencode allow-list superset (§4.3)."""
    allowed = load_providers_config(_REPO_ROOT)["Opencode"]["agent-transform"][
        "allowed-fields"
    ]
    assert "system" in allowed

    # Contract proof: on the v2 surface the allow-list is enforced, and a
    # v1 artifact carrying `system` is no finding.
    contract = resolve_artifact_contract(_registry_for_surface("v2")["Opencode"])
    assert contract.allowed_fields is not None
    assert "system" in contract.allowed_fields
    findings = validate_frontmatter(
        "---\nname: agent\ndescription: d\nsystem: prompt\n---\nbody\n",
        allowed_fields=contract.allowed_fields,
        required_fields=set(),
        reject_fields=contract.reject_fields,
        path="agent.md",
    )
    assert findings == []


# ===========================================================================
# Phase D2 / Task 23 (D2): ``cli.json`` as a managed file
# ===========================================================================
#
# Spec §3.8 / Amendment B1 / AC-D7, AC-B16 (cli part), AC-B20 (cli part):
#
# * ``plugins`` is the ONLY documented top-level key of ``cli.json``; the writer
#   stays a generic passthrough of the user-provided top-level keys (no
#   allow-list) and the tests make no claim about ``theme``/``autoupdate``;
# * the file name is the resolved ``cli_file`` (Task 6), relative to the
#   directory of ``mcp-config.committed-file`` — never a hardcoded literal;
# * the writer owns the ``opencode-v2-cli`` state namespace only, starts with
#   ``owns_opencode_surface`` (non-owners are no-ops before any state read) and
#   writes through ``io.write_checked`` with the Task-9 secret-gate parameters;
# * ``tui.json`` is never created, modified or deleted.

_CLI_FILE = "cli.json"


def _run_cli(
    project_root: Path,
    config: dict,
    providers: dict,
    provider: str = "Opencode",
    log: SyncLog | None = None,
    dry_run: bool = False,
) -> SyncLog:
    log = log if log is not None else SyncLog()
    opencode_v2_config.sync_opencode_cli_file(
        project_root, config, provider, providers, log, dry_run,
    )
    return log


def test_ac_d7_cli_json_written_with_exact_keys(tmp_path):
    """AC-D7 (Amendment B1): the documented ``plugins`` key is passed through.

    The written document carries exactly the user's top-level keys (generic
    passthrough, no invented allow-list). Removing the project option rolls the
    managed key back and empties the ``opencode-v2-cli`` namespace — even though
    the option no longer exists in the project config.
    """
    project = tmp_path / "project"
    project.mkdir()
    plugins = ["opencode-acme-cli"]
    providers = {"Opencode": _v2_pc()}

    _run_cli(project, _config(cli={"plugins": plugins}), providers)

    doc = _read_json(project / _CLI_FILE)
    assert doc == {"plugins": plugins}, doc
    assert _read_state_doc(project)[opencode_v2_config.STATE_CLI_KEY] == {
        "plugins": {"value": plugins, "prior": None, "prior_absent": True}
    }

    # Rollback: the option is gone, the managed key must go with it.
    log = _run_cli(project, _config(), providers)

    assert not (project / _CLI_FILE).exists(), (
        "a rollback that leaves no content must not keep an empty cli.json"
    )
    assert opencode_v2_config.STATE_CLI_KEY not in _read_state_doc(project)
    assert not _warned(log, "opencode-v2-managed"), log.warnings


def test_ac_d7_no_cli_json_without_option_or_on_v1(tmp_path, monkeypatch):
    """AC-D7: no option or a v1 surface never creates ``cli.json``.

    Drives the real stage seam (so it is a green regression test before the
    writer exists): without a ``cli`` option there is nothing to write, and on
    v1 the resolved ``cli_file`` is absent, so the option is ignored.
    """
    no_option, _, _ = _run_stage(
        tmp_path / "no-option", monkeypatch, {"Opencode": _v2_pc()}, ["Opencode"],
        _config(3), {"Opencode": "advisory"},
    )
    assert not (no_option / _CLI_FILE).exists()
    assert opencode_v2_config.STATE_CLI_KEY not in _read_state_doc(no_option)

    on_v1, _, _ = _run_stage(
        tmp_path / "v1", monkeypatch, {"Opencode": _v1_pc()}, ["Opencode"],
        _config(cli={"plugins": ["opencode-acme-cli"]}), {"Opencode": "advisory"},
    )
    assert not (on_v1 / _CLI_FILE).exists(), (
        "v1 has no resolved cli_file, so the writer must stay a no-op"
    )
    assert opencode_v2_config.STATE_CLI_KEY not in _read_state_doc(on_v1)


def test_ac_d7_tui_json_never_touched(tmp_path):
    """AC-D7: ``tui.json`` is never created, modified or deleted by the writer."""
    project = tmp_path / "project"
    tui = project / "tui.json"
    tui.parent.mkdir(parents=True)
    tui.write_bytes(b'{"theme": "user-owned"}\n')
    before = tui.read_bytes()
    providers = {"Opencode": _v2_pc()}

    first = _run_cli(
        project, _config(cli={"plugins": ["opencode-acme-cli"]}), providers,
    )
    assert (project / _CLI_FILE).is_file()
    assert tui.read_bytes() == before

    second = _run_cli(project, _config(), providers)  # rollback
    assert tui.read_bytes() == before

    touched = [
        line
        for line in first.actions + first.skipped + first.warnings
        + second.actions + second.skipped + second.warnings
        if "tui.json" in line
    ]
    assert touched == [], touched


def test_ac_b16_cli_namespace_isolated(tmp_path):
    """AC-B16 (cli part): only ``opencode-v2-cli`` is written; siblings survive.

    A second run is byte-identical for both the managed file and the state
    file, and the namespace stays a ``dict`` for ``isolation._read_state``.
    """
    project = tmp_path / "project"
    sibling_isolation = ["**/.claude/**"]
    sibling_keys = {
        "experimental.subagent_depth": {
            "value": 3,
            "prior": None,
            "prior_absent": True,
        }
    }
    sibling_mcp = {
        "mcp.servers.example": {
            "value": {"type": "local"},
            "prior": None,
            "prior_absent": True,
        }
    }
    _write_json(
        project / _V2_STATE_REL,
        {
            "isolation-deny": sibling_isolation,
            STATE_KEYS_KEY: sibling_keys,
            opencode_v2_config.STATE_MCP_KEY: sibling_mcp,
        },
    )
    before = _read_json(project / _V2_STATE_REL)
    providers = {"Opencode": _v2_pc()}
    config = _config(cli={"plugins": ["opencode-acme-cli"]})

    _run_cli(project, config, providers)

    after = _read_json(project / _V2_STATE_REL)
    assert after["isolation-deny"] == before["isolation-deny"]
    assert after[STATE_KEYS_KEY] == before[STATE_KEYS_KEY]
    assert after[opencode_v2_config.STATE_MCP_KEY] == before[opencode_v2_config.STATE_MCP_KEY]
    assert set(after[opencode_v2_config.STATE_CLI_KEY]) == {"plugins"}
    assert isinstance(
        isolation._read_state(project / _V2_STATE_REL, opencode_v2_config.STATE_CLI_KEY),
        dict,
    )

    file_bytes = (project / _CLI_FILE).read_bytes()
    state_bytes = (project / _V2_STATE_REL).read_bytes()
    _run_cli(project, config, providers)

    assert (project / _CLI_FILE).read_bytes() == file_bytes
    assert (project / _V2_STATE_REL).read_bytes() == state_bytes


def test_ac_b20_cli_writer_noop_for_non_owner_provider(tmp_path, monkeypatch):
    """AC-B20 (cli part): a non-owner is a no-op *before* the state is read."""
    project = tmp_path / "project"
    _write_json(project / "opencode.json", {"theme": "dark"})
    _write_json(
        project / _V2_STATE_REL,
        {
            opencode_v2_config.STATE_CLI_KEY: {
                "plugins": {
                    "value": ["opencode-acme-cli"],
                    "prior": None,
                    "prior_absent": True,
                }
            }
        },
    )
    file_before = (project / "opencode.json").read_bytes()
    state_before = (project / _V2_STATE_REL).read_bytes()

    def _forbidden(*args, **kwargs):
        raise AssertionError("state must not be read for a non-owner provider")

    monkeypatch.setattr(isolation, "_read_state", _forbidden)

    log = SyncLog()
    _run_cli(
        project,
        _config(cli={"plugins": ["opencode-acme-cli"]}),
        {"Claude": _non_owner_pc()},
        provider="Claude",
        log=log,
    )

    assert not (project / _CLI_FILE).exists()
    assert (project / "opencode.json").read_bytes() == file_before
    assert (project / _V2_STATE_REL).read_bytes() == state_before
    assert log.actions == [] and log.warnings == [] and log.errors == []
    assert log.skipped == [] and log.infos == []


def test_cli_writer_passes_secret_gate_params_to_write_checked(tmp_path, monkeypatch):
    """The CLI writer delegates the secret gate to ``io.write_checked``.

    Same parameters as the Task-9 writer: ``allow_secrets`` from
    ``allow-committed-secrets``, ``verify_gitignored=False`` (committed file),
    the caller's ``config`` and ``dry_run``.
    """
    calls = []

    def fake_write_checked(path, content, log, rel_label, **kwargs):
        calls.append((path, content, rel_label, kwargs))
        return True

    monkeypatch.setattr(opencode_v2_config.io, "write_checked", fake_write_checked)
    providers = {"Opencode": _v2_pc()}
    config = _config(cli={"plugins": ["opencode-acme-cli"]})

    plain_project = tmp_path / "plain"
    plain_project.mkdir()
    _run_cli(plain_project, config, providers)

    allowed_project = tmp_path / "allowed"
    allowed_project.mkdir()
    _run_cli(allowed_project, {**config, "allow-committed-secrets": True}, providers)

    assert len(calls) == 2, calls
    path, content, rel_label, kwargs = calls[0]
    assert path == plain_project / _CLI_FILE
    assert rel_label == _CLI_FILE
    assert content.endswith("\n")
    assert json.loads(content) == {"plugins": ["opencode-acme-cli"]}
    assert set(kwargs) >= {"allow_secrets", "verify_gitignored", "config", "dry_run"}
    assert kwargs["allow_secrets"] is False
    assert kwargs["verify_gitignored"] is False
    assert kwargs["config"] == config
    assert kwargs["dry_run"] is False
    assert calls[1][3]["allow_secrets"] is True


def test_ac_b22_cli_json_rolled_back_on_v1_surface(tmp_path):
    """AC-B22/AC-B7: a v2→v1 switch must roll back the managed CLI file too.

    ``cli_file`` resolves only on v2 (spec §3.1), so the v1 re-sync has to find
    the file through the registry-level ``cli-files`` map that survives the
    surface selection. Without that fallback ``cli.json`` and the
    ``opencode-v2-cli`` state namespace survive the switch, contradicting
    AC-B7/AC-B22 ("die State-Namespaces ... sind leer/entfernt").
    """
    project = tmp_path / "project"
    plugins = ["opencode-acme-cli"]
    v2 = {"Opencode": _v2_pc()}
    v1 = {"Opencode": _v1_pc_with_cli_files()}

    _run_cli(project, _config(cli={"plugins": plugins}), v2)
    assert _read_json(project / _CLI_FILE) == {"plugins": plugins}
    assert opencode_v2_config.STATE_CLI_KEY in _read_state_doc(project)

    assert "cli_file" not in v1["Opencode"], "a v1 surface resolves no cli_file"
    log = _run_cli(project, _config(), v1)

    assert not (project / _CLI_FILE).exists(), (
        "a rollback that leaves no content must delete the managed file"
    )
    assert opencode_v2_config.STATE_CLI_KEY not in _read_state_doc(project), (
        "AC-B22: the opencode-v2-cli namespace must be gone after the switch"
    )
    assert not _warned(log, "cannot resolve managed file for rollback"), log.warnings


def test_ac_b7_cli_rollback_keeps_user_keys(tmp_path):
    """AC-B7 (rows 4/4a): only the managed keys go, a user key keeps the file."""
    project = tmp_path / "project"
    plugins = ["opencode-acme-cli"]
    _write_json(project / _CLI_FILE, {"theme": "user-owned"})

    _run_cli(project, _config(cli={"plugins": plugins}), {"Opencode": _v2_pc()})
    assert _read_json(project / _CLI_FILE) == {
        "theme": "user-owned",
        "plugins": plugins,
    }, "a user key is never overwritten or dropped"

    _run_cli(project, _config(), {"Opencode": _v1_pc_with_cli_files()})

    assert _read_json(project / _CLI_FILE) == {"theme": "user-owned"}
    assert opencode_v2_config.STATE_CLI_KEY not in _read_state_doc(project)


def test_cli_rollback_resolves_existing_candidate_among_several(tmp_path):
    """Several ``cli-files`` values: only an existing file identifies the owner."""
    project = tmp_path / "project"
    plugins = ["opencode-acme-cli"]
    _run_cli(project, _config(cli={"plugins": plugins}), {"Opencode": _v2_pc()})

    pc = _v1_pc_with_cli_files()
    pc["cli-files"] = {"v1": "cli-legacy.json", "v2": _CLI_FILE}
    log = _run_cli(project, _config(), {"Opencode": pc})

    assert not (project / _CLI_FILE).exists()
    assert not (project / "cli-legacy.json").exists(), (
        "a non-existing candidate is never guessed"
    )
    assert opencode_v2_config.STATE_CLI_KEY not in _read_state_doc(project)
    assert not _warned(log, "ambiguous managed file for rollback"), log.warnings


def test_cli_rollback_cannot_resolve_leaves_file_and_state(tmp_path):
    """Documented limitation: with no unambiguous file the writer never guesses.

    Two cases — the entry carries no ``cli-files`` map at all, and several map
    values point at files that all exist. Both leave the managed file and the
    ``opencode-v2-cli`` namespace untouched and log the canonical warning.
    """
    plugins = ["opencode-acme-cli"]
    cases = {
        "no-map": None,
        "ambiguous": {"v1": "cli-a.json", "v2": _CLI_FILE},
    }
    for name, cli_files in cases.items():
        project = tmp_path / name
        _run_cli(project, _config(cli={"plugins": plugins}), {"Opencode": _v2_pc()})
        # A second existing file makes the "ambiguous" case genuinely ambiguous.
        _write_json(project / "cli-a.json", {"stale": True})
        file_bytes = (project / _CLI_FILE).read_bytes()

        pc = _v1_pc()
        if cli_files is not None:
            pc["cli-files"] = dict(cli_files)
        log = _run_cli(project, _config(), {"Opencode": pc})

        assert (project / _CLI_FILE).read_bytes() == file_bytes, name
        assert opencode_v2_config.STATE_CLI_KEY in _read_state_doc(project), name
        assert _warned(
            log, "opencode-v2-cli: cannot resolve managed file for rollback"
        ), name


# ===========================================================================
# Phase D / Task 27 (D4): provider doc reflects the delivered v2 surface
# ===========================================================================
#
# SPEC-OPENCODE-V2-SUPPORT-2026-10-22 §3.10 / AC-D10. The provider doc is an
# external artifact, so the assertions stay narrow: the ``Stand`` header must
# follow ``VERSION`` (the old ``v0.33.x`` line is stale), the four sections of
# the delivered surface must exist, and the context-file rule must be stated as
# AGENTS.md-only (no dedicated rules directory).

_PROVIDER_DOC = _REPO_ROOT / "docs/providers/opencode.md"


def test_provider_doc_current():
    """AC-D10: no stale version, all four delivered-surface sections present."""
    text = _PROVIDER_DOC.read_text(encoding="utf-8")
    assert "v0.33" not in text, (
        "the 'Stand' line must follow VERSION, not the stale v0.33.x value"
    )
    for heading in (
        "## Surface v1 vs. v2",
        "## Aktivierung",
        "## Managed Keys und User-Keys",
        "## Dateien",
    ):
        assert heading in text, f"missing documented section: {heading}"


def test_provider_doc_states_agents_md_only():
    """§3.10: AGENTS.md is the single managed context file for Opencode."""
    text = _PROVIDER_DOC.read_text(encoding="utf-8")
    assert "AGENTS.md-only" in text
    assert ".opencode/rules/" not in text, (
        "Opencode has no dedicated rules directory; the doc must not reference one"
    )


# ===========================================================================
# Phase D / Task 29 (T.2): lab diff v1 <-> v2 and the full switch rollback
# ===========================================================================
#
# AC-T2 / AC-B7 (integration) / AC-B21 / AC-B22 (integration). The renderer is
# the AC-01 harness (``test_ac01_render_identity._run_sync``): scenario 79 is
# synced twice — once with the four v2 project options removed (v1) and once as
# shipped (v2) — and the two trees are compared file by file. Every input other
# than the surface selector is identical by construction, so the file set that
# differs is the surface delta and nothing else.

_SCENARIO_79_CONFIG = (
    _REPO_ROOT / "tests/scenarios/configs/79-opencode-v2-full-surface.project.yaml"
)
# The complete v2 opt-in of scenario 79 (Amdmt B1: no `small-model`).
_SCENARIO_79_V2_OPTIONS = ("surface-version", "experimental-todo", "model-variants", "cli")

# AC-T2: the exhaustive difference between the two renders. `AGENTS.md` is a
# shared artifact; its only difference here is Opencode's runtime-gate tier
# contribution (`permission` vs `plugin`), asserted separately below.
_LAB_DIFF_CHANGED = (
    ".meta-config/generated-file-hashes.json",
    ".opencode/agent-meta-state.json",
    ".opencode/agents/developer.md",
    ".opencode/agents/orchestrator.md",
    "AGENTS.md",
    "opencode.json",
)
_LAB_DIFF_ONLY_ON_V2 = (
    ".opencode/plugins/.agent-meta-managed",
    ".opencode/plugins/agent-meta-runtime-gate.js",
    "cli.json",
)
# Input fixture, not render output: the two runs must differ here on purpose.
_NON_RENDER_INPUTS = (".meta-config/project.yaml",)
_GATE_TRIPLES = [
    {"action": "edit", "resource": "**", "effect": "deny"},
    {"action": "shell", "resource": "**", "effect": "deny"},
]
_V2_NAMESPACES = (
    isolation._STATE_V2_KEYS,
    isolation._STATE_V2_PERMISSIONS,
    isolation._STATE_V2_CLI,
    isolation._STATE_V2_MCP,
)


def _scenario_79_project(*, surface: str) -> dict:
    """Scenario-79 config; for ``v1`` the v2 project channel is removed."""
    config = yaml.safe_load(_SCENARIO_79_CONFIG.read_text(encoding="utf-8"))
    options = (config.get("provider-options") or {}).get("Opencode") or {}
    if surface == "v1":
        for key in _SCENARIO_79_V2_OPTIONS:
            options.pop(key, None)
        if not options:
            config.pop("provider-options", None)
    else:
        assert options.get("surface-version") == "v2", (
            f"scenario 79 must opt into v2 through the project channel (got {options!r})"
        )
    return config


def _sync_scenario_79(project: Path, config: dict, *, init: bool) -> None:
    """Render ``config`` into ``project`` through the AC-01 sync runner."""
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    (project / ".meta-config" / "project.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    if init:
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = render_harness._run_sync(project, *(["--init"] if init else []))
    assert result.returncode == 0, (
        f"sync failed ({'--init' if init else 'plain'}):\n"
        f"{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
    )


def _rendered_files(project: Path) -> dict:
    """Relative path -> compared bytes of one rendered tree.

    Only run-specific values are normalized (the scratch root and the date
    stamps, exactly as the AC-01 harness does); model lines are NOT normalized,
    because the model variant is one of the asserted surface differences.
    """
    root = project.resolve()
    dates = sorted({date.today().isoformat(), render_harness._resolve_agent_meta_date(_REPO_ROOT)})
    files = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if render_harness._SKIP_RE.search(rel) or rel in _NON_RENDER_INPUTS:
            continue
        data = path.read_bytes().replace(b"\r\n", b"\n")
        for needle in sorted({str(root), root.as_posix()}, key=len, reverse=True):
            data = data.replace(needle.encode(), b"<ROOT>")
        for stamp in dates:
            data = data.replace(stamp.encode(), b"<DATE>")
        files[rel] = data
    return files


def _frontmatter(data: bytes) -> dict:
    text = data.decode("utf-8")
    assert text.startswith("---"), "agent artifacts start with YAML frontmatter"
    return yaml.safe_load(text.split("---", 2)[1]) or {}


def test_lab_diff_v1_v2(tmp_path):
    """AC-T2: the same project on v1 and v2 differs in exactly the v2 surface.

    The diff report names every changed / added / removed path, so a regression
    is diagnosable from the failure alone.
    """
    v1_root = tmp_path / "v1"
    v2_root = tmp_path / "v2"
    _sync_scenario_79(v1_root, _scenario_79_project(surface="v1"), init=True)
    _sync_scenario_79(v2_root, _scenario_79_project(surface="v2"), init=True)

    v1 = _rendered_files(v1_root)
    v2 = _rendered_files(v2_root)

    changed = tuple(sorted(p for p in set(v1) & set(v2) if v1[p] != v2[p]))
    only_v1 = tuple(sorted(set(v1) - set(v2)))
    only_v2 = tuple(sorted(set(v2) - set(v1)))
    report = (
        f"\nchanged={list(changed)}\nonly-in-v1={list(only_v1)}\n"
        f"only-in-v2={list(only_v2)}\n"
        f"compared {len(v1)} v1 files against {len(v2)} v2 files"
    )
    assert changed == _LAB_DIFF_CHANGED, f"unexpected changed files:{report}"
    assert only_v1 == (), f"v2 must not remove generated files:{report}"
    assert only_v2 == _LAB_DIFF_ONLY_ON_V2, f"unexpected new files:{report}"

    # --- opencode.json: mcp form, experimental.*, permissions vs permission
    doc_v1 = json.loads(v1["opencode.json"])
    doc_v2 = json.loads(v2["opencode.json"])
    assert set(doc_v1) == {"subagent_depth", "mcp", "default_agent", "permission"}, doc_v1
    assert doc_v1["mcp"]["playwright"]["enabled"] is True, (
        "v1 keeps the flat mcp entry with the legacy 'enabled' flag"
    )
    assert set(doc_v2) == {"default_agent", "mcp", "permissions", "experimental"}, doc_v2
    assert set(doc_v2["mcp"]) == {"servers"}, doc_v2["mcp"]
    assert "enabled" not in doc_v2["mcp"]["servers"]["playwright"]
    assert doc_v2["experimental"] == {"subagent_depth": 2, "todo": True}
    assert doc_v1["permission"] == {"edit": {"**": "deny"}, "bash": {"**": "deny"}}
    assert doc_v2["permissions"] == _GATE_TRIPLES

    # --- .opencode/agents/*.md: permissions format and model variant
    for role in ("developer", "orchestrator"):
        rel = f".opencode/agents/{role}.md"
        fm_v1 = _frontmatter(v1[rel])
        fm_v2 = _frontmatter(v2[rel])
        assert isinstance(fm_v1["permission"], dict), (role, fm_v1)
        assert "permissions" not in fm_v1, (role, fm_v1)
        assert isinstance(fm_v2["permissions"], list), (role, fm_v2)
        assert "permission" not in fm_v2, (role, fm_v2)
        for entry in fm_v2["permissions"]:
            assert set(entry) == {"action", "resource", "effect"}, (role, entry)
        assert "#" not in fm_v1["model"], (role, fm_v1["model"])
    developer_v2 = _frontmatter(v2[".opencode/agents/developer.md"])
    orchestrator_v2 = _frontmatter(v2[".opencode/agents/orchestrator.md"])
    assert developer_v2["model"].endswith("#high"), (
        f"the configured model variant must reach the artifact "
        f"(got {developer_v2['model']!r})"
    )
    assert "#" not in orchestrator_v2["model"], (
        "a role without a configured variant keeps the plain model id"
    )

    # --- cli.json and the plugin artifact exist only on v2
    assert json.loads(v2["cli.json"]) == {"plugins": ["opencode-acme-cli"]}
    assert b"export default {" in v2[".opencode/plugins/agent-meta-runtime-gate.js"]

    # --- the derived hash manifest differs only where the surface differs
    hashes_v1 = json.loads(v1[".meta-config/generated-file-hashes.json"])["hashes"]
    hashes_v2 = json.loads(v2[".meta-config/generated-file-hashes.json"])["hashes"]
    assert {
        key for key in set(hashes_v1) | set(hashes_v2)
        if hashes_v1.get(key) != hashes_v2.get(key)
    } == {
        ".opencode/agents/developer.md",
        ".opencode/agents/orchestrator.md",
        ".opencode/plugins/agent-meta-runtime-gate.js",
    }, "the managed hash manifest must follow the surface, not drift on its own"

    # --- AGENTS.md differs only in Opencode's runtime-gate tier contribution
    agents_v1 = v1["AGENTS.md"].decode("utf-8")
    agents_v2 = v2["AGENTS.md"].decode("utf-8")
    tier_marker = "## Runtime-Enforcement-Tier:"
    assert agents_v1.split(tier_marker)[0] == agents_v2.split(tier_marker)[0], (
        "no AGENTS.md section before the runtime-gate tier may differ"
    )
    assert agents_v1.split("## Git Delegation")[1] == agents_v2.split("## Git Delegation")[1], (
        "no AGENTS.md section after the gate block may differ"
    )
    assert f"{tier_marker} `permission`" in agents_v1
    assert f"{tier_marker} `plugin`" in agents_v2
    assert "# CRITICAL GATE (runtime-partially enforced)" in agents_v1
    assert "# CRITICAL GATE\nMAIN CHAT darf nicht selbst editieren." in agents_v2


def test_v2_to_v1_switch_rolls_back_all_namespaces(tmp_path):
    """AC-B7/AC-B21/AC-B22: v2 -> v1 empties all four namespaces, and back.

    One project is synced on v2, switched to v1 and switched back. The rollback
    must clear ``opencode-v2-keys``/-permissions/-cli/-mcp, leave no managed
    ``experimental`` / ``permissions`` / ``mcp.servers`` content behind, keep
    user keys, and delete ``cli.json`` once it is empty. The reverse direction
    must take the v1 ``permission``-map denies out and empty ``runtime-gate-deny``.
    """
    project = tmp_path / "project"
    _sync_scenario_79(project, _scenario_79_project(surface="v2"), init=True)

    # --- v2 surface fully written ----------------------------------------
    doc = _read_json(project / "opencode.json")
    assert "experimental" in doc and "permissions" in doc, doc
    assert _read_json(project / "cli.json") == {"plugins": ["opencode-acme-cli"]}
    state = _read_state_doc(project)
    assert {ns for ns in _V2_NAMESPACES if ns in state} == set(_V2_NAMESPACES), state

    # User keys next to the managed ones (AC-B7: "geänderte User-Werte bleiben").
    doc["theme"] = "acme-dark"
    doc["plugin"] = ["user-plugin.js"]
    _write_json(project / "opencode.json", doc)

    # --- v2 -> v1 --------------------------------------------------------
    _sync_scenario_79(project, _scenario_79_project(surface="v1"), init=False)

    doc = _read_json(project / "opencode.json")
    assert "experimental" not in doc, doc
    assert "permissions" not in doc, doc
    assert "servers" not in doc["mcp"], "the nested v2 container must be pruned"
    assert doc["mcp"]["playwright"]["enabled"] is True, "the v1 flat form is back"
    assert doc["theme"] == "acme-dark", "a user key survives the rollback"
    assert doc["plugin"] == ["user-plugin.js"], "a user key survives the rollback"
    assert doc["permission"] == {"edit": {"**": "deny"}, "bash": {"**": "deny"}}, (
        "Spec A writes the v1 map after the v2 triples are gone"
    )
    assert not (project / "cli.json").exists(), (
        "the managed CLI file is removed once the rollback leaves it empty"
    )
    state = _read_state_doc(project)
    assert [ns for ns in state if ns.startswith("opencode-v2-")] == [], state
    assert state[isolation._STATE_RUNTIME_GATE_KEY] == {
        "**": {"edit": None, "bash": None}
    }, "Spec A owns the v1 deny state again"

    # --- v1 -> v2 (reverse direction, AC-B21) ----------------------------
    _sync_scenario_79(project, _scenario_79_project(surface="v2"), init=False)

    doc = _read_json(project / "opencode.json")
    assert "permission" not in doc, (
        f"the v1 deny map must be taken back (prior restored): {doc}"
    )
    assert doc["permissions"] == _GATE_TRIPLES, doc
    assert doc["experimental"] == {"subagent_depth": 2, "todo": True}
    assert doc["theme"] == "acme-dark" and doc["plugin"] == ["user-plugin.js"]
    state = _read_state_doc(project)
    assert isolation._STATE_RUNTIME_GATE_KEY not in state, state
    assert {ns for ns in _V2_NAMESPACES if ns in state} == set(_V2_NAMESPACES), state


# ===========================================================================
# Phase D / Task 30 (T.3): no cross-provider effect, golden fixtures frozen
# ===========================================================================
#
# AC-D5 / AC-D6 / AC-T4 (Spec §3.7, decision 10, global constraint "keine
# Querwirkung"). The same four-provider project is rendered twice — once with
# Opencode on v1, once on v2 — and every byte that is NOT Opencode-owned must
# match. The provider-spanning files are listed explicitly and checked one by
# one: `AGENTS.md` is shared by Gemini/Mammouth/Opencode, and its runtime-gate
# tier is folded to the weakest provider, so Opencode's v1→v2 tier change must
# NOT leak into it; `.meta-config/generated-file-hashes.json` is a derived
# manifest over all providers, so only its Opencode entries may move.

# Provider order matters: the AC-B8 re-review flagged an order-dependent
# rollback, so Opencode is listed first and the comparison stays order-sensitive.
_AC_D5_PROVIDERS = ("Opencode", "Claude", "Gemini", "Mammouth")

_AC_D5_BASE_CONFIG = {
    "agent-meta-version": "2.0.0-beta.2",
    "ai-providers": list(_AC_D5_PROVIDERS),
    "dod-preset": "rapid-prototyping",
    "platforms": [],
    "roles": ["orchestrator", "developer"],
    "orchestrator": {"mode": "strict"},
    "project": {
        "name": "ac-d5-cross-provider",
        "prefix": "ad5",
        "short": "ac-d5",
    },
    "variables": {
        "PROJECT_NAME": "ac-d5-cross-provider",
        "PROJECT_DESCRIPTION": "Cross-provider isolation proof for the v2 surface.",
        "PROJECT_GOAL": "Prove that Opencode v2 never touches other providers.",
        "GIT_PLATFORM": "GitHub",
        "GIT_REMOTE_URL": "https://github.com/example/ac-d5-cross-provider",
        "GIT_MAIN_BRANCH": "main",
    },
    "rules-preset": "default",
    "speech-mode": "full",
    "tier-preset": "Normal",
    "se-focus": False,
    "max-parallel-agents": 2,
    "conventions-preset": "default",
    "debug-mode": False,
    "allow-committed-secrets": False,
}

# Provider-owned trees of Claude, Gemini and Mammouth (AC-D5): never changed.
_AC_D5_FOREIGN_PREFIXES = (".claude/", ".gemini/", ".mammouth/")
# Non-prefixed artifacts of the same three providers.
_AC_D5_FOREIGN_FILES = ("CLAUDE.md", "AGENTS.personal.md", "mammouth.json")
# Provider-spanning files, explicitly listed (AC-D5).
_AC_D5_SPANNING_FILES = ("AGENTS.md", ".meta-config/generated-file-hashes.json")
# The complete delta of the two renders: the Opencode surface plus the derived
# hash manifest (validated separately below).
_AC_D5_CHANGED = (
    ".meta-config/generated-file-hashes.json",
    ".opencode/agent-meta-state.json",
    ".opencode/agents/developer.md",
    ".opencode/agents/orchestrator.md",
    # The v2 settings document itself.
    "opencode.json",
)
_AC_D5_ONLY_ON_V2 = (
    ".opencode/plugins/.agent-meta-managed",
    ".opencode/plugins/agent-meta-runtime-gate.js",
)


def _ac_d5_config(surface: str) -> dict:
    """The four-provider config; ``v1`` drops the Opencode surface option."""
    config = json.loads(json.dumps(_AC_D5_BASE_CONFIG))
    if surface == "v2":
        config["provider-options"] = {"Opencode": {"surface-version": "v2"}}
    return config


def _sync_four_providers(project: Path, surface: str) -> None:
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    (project / ".meta-config" / "project.yaml").write_text(
        yaml.safe_dump(_ac_d5_config(surface), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = render_harness._run_sync(project, "--init")
    assert result.returncode == 0, (
        f"{surface} sync failed:\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
    )


def _assert_provider_tree_identical(
    v1: dict, v2: dict, prefix: str,
) -> None:
    """Every file below *prefix* is present and byte-identical in both renders."""
    paths_v1 = {rel for rel in v1 if rel.startswith(prefix)}
    paths_v2 = {rel for rel in v2 if rel.startswith(prefix)}
    assert paths_v1, f"guard: {prefix} must produce artifacts"
    assert paths_v1 == paths_v2, (
        f"{prefix} file set changed: only-v1={sorted(paths_v1 - paths_v2)} "
        f"only-v2={sorted(paths_v2 - paths_v1)}"
    )
    differing = sorted(rel for rel in paths_v1 if v1[rel] != v2[rel])
    assert differing == [], f"{prefix} artifacts changed under Opencode v2: {differing}"


def test_ac_d5_other_providers_byte_identical_when_opencode_is_v2(tmp_path):
    """AC-D5: Opencode v2 leaves Claude, Gemini and Mammouth byte-identical.

    Reference = the same project with Opencode on v1. Every provider-owned
    artifact must match byte for byte. The provider-spanning files are listed
    explicitly and validated individually:

    * ``AGENTS.md`` — identical, because the shared runtime-gate tier folds to
      the weakest provider; Opencode's own tier change must not leak into it
      (the single-provider delta is covered by ``test_lab_diff_v1_v2``);
    * ``.meta-config/generated-file-hashes.json`` — only its Opencode entries
      may differ (developer, orchestrator, runtime-gate plugin).
    """
    v1_root = tmp_path / "opencode-v1"
    v2_root = tmp_path / "opencode-v2"
    _sync_four_providers(v1_root, "v1")
    _sync_four_providers(v2_root, "v2")

    v1 = _rendered_files(v1_root)
    v2 = _rendered_files(v2_root)

    only_v1 = tuple(sorted(set(v1) - set(v2)))
    only_v2 = tuple(sorted(set(v2) - set(v1)))
    changed = tuple(sorted(rel for rel in set(v1) & set(v2) if v1[rel] != v2[rel]))
    report = (
        f"\nchanged={list(changed)}\nonly-in-v1={list(only_v1)}\n"
        f"only-in-v2={list(only_v2)}\n"
        f"compared {len(v1)} v1 files against {len(v2)} v2 files"
    )

    # --- the complete, closed delta --------------------------------------
    assert only_v1 == (), f"v2 must not remove a file:{report}"
    assert only_v2 == _AC_D5_ONLY_ON_V2, f"unexpected new files:{report}"
    assert changed == tuple(sorted(_AC_D5_CHANGED)), (
        f"the cross-provider delta is not the Opencode surface:{report}"
    )

    # --- Claude / Gemini / Mammouth: byte-identical ----------------------
    for prefix in _AC_D5_FOREIGN_PREFIXES:
        _assert_provider_tree_identical(v1, v2, prefix)
    for rel in _AC_D5_FOREIGN_FILES:
        assert rel in v1 and rel in v2, f"missing foreign artifact {rel}{report}"
        assert v1[rel] == v2[rel], f"foreign artifact changed under v2: {rel}"

    # --- the explicitly listed provider-spanning files -------------------
    # Only the derived manifest may move; `AGENTS.md` must stay identical.
    spanning_changed = tuple(
        rel for rel in _AC_D5_SPANNING_FILES if v1[rel] != v2[rel]
    )
    assert spanning_changed == (".meta-config/generated-file-hashes.json",), (
        f"unexpected provider-spanning delta {spanning_changed}: "
        f"allowed files are {_AC_D5_SPANNING_FILES}{report}"
    )

    # --- provider-spanning file 1: AGENTS.md -----------------------------
    # Shared by Opencode/Gemini/Mammouth. The tier is the weakest of the
    # involved providers, so both renders stay `advisory` and the file must be
    # byte-identical; an Opencode-only tier change would be a leak.
    agents_v1 = v1["AGENTS.md"].decode("utf-8")
    agents_v2 = v2["AGENTS.md"].decode("utf-8")
    assert agents_v1 == agents_v2, (
        "AGENTS.md is provider-spanning: only Opencode parts may change, but "
        "the shared runtime-gate tier is advisory on both surfaces"
    )
    assert "## Runtime-Enforcement-Tier: `advisory`" in agents_v1
    assert "## Runtime-Enforcement-Tier: `advisory`" in agents_v2

    # --- provider-spanning file 2: derived hash manifest -----------------
    hashes_v1 = json.loads(v1[".meta-config/generated-file-hashes.json"])["hashes"]
    hashes_v2 = json.loads(v2[".meta-config/generated-file-hashes.json"])["hashes"]
    manifest_delta = {
        key for key in set(hashes_v1) | set(hashes_v2)
        if hashes_v1.get(key) != hashes_v2.get(key)
    }
    assert manifest_delta == {
        ".opencode/agents/developer.md",
        ".opencode/agents/orchestrator.md",
        ".opencode/plugins/agent-meta-runtime-gate.js",
    }, (
        "the generated hash manifest may only follow the Opencode surface, "
        f"got {sorted(manifest_delta)}"
    )


# AC-T4 (plan-wide constraint): the golden fixtures are the baseline after the
# Plan-A merge and must not be touched by any task of the v2 plan. The expected
# values are the frozen digests of the three fixture trees (relpath + NUL +
# bytes + NUL, files sorted by relpath) — literals, never recomputed.
_FIXTURE_TREES = {
    "ac01-baseline": "09bdcb53dd33621430978851dc7ca85a1710eabad6724f440043f951cb6dfd5f",
    "slimming-golden": "66c7a598dc6bf7729bee5a46dfc22889bda4f3d65816c4c1f6c4938a8242b505",
    "compact-golden": "d56b299c7512ff6678e3f401d823084fcdf3e9b813af1397192b7b99d64f77ba",
}


def _fixture_tree_sha256(root: Path) -> str:
    """Deterministic digest over a fixture directory (paths and contents)."""
    digest = hashlib.sha256()
    files = sorted(
        (path for path in root.rglob("*") if path.is_file()),
        key=lambda path: path.relative_to(root).as_posix(),
    )
    for path in files:
        digest.update(path.relative_to(root).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def test_ac_t4_fixtures_unchanged():
    """AC-T4: the three golden fixture trees still match their frozen digests.

    A changed fixture invalidates every golden comparison downstream, so this
    is the guard for the whole plan — the expected digests are embedded
    literals and the check runs in-process (no subprocess).
    """
    fixtures_root = _REPO_ROOT / "tests" / "fixtures"
    mismatched = []
    for name, expected in _FIXTURE_TREES.items():
        root = fixtures_root / name
        assert root.is_dir(), f"missing golden fixture directory: {root}"
        actual = _fixture_tree_sha256(root)
        if actual != expected:
            mismatched.append(f"{name}: expected {expected}, got {actual}")
    assert mismatched == [], (
        "golden fixtures changed (AC-T4 requires them frozen):\n"
        + "\n".join(mismatched)
    )


# --- AC coverage + provider agnosticism meta-tests (Task 31, AC-T3/AC-T6) ----

#: Spec AC-T3: every AC owned by this file must have at least one named test.
_AC_T3_SURFACE_IDS = (
    "b1", "b2", "b4", "b5", "b7", "b12", "b16", "b17", "b18", "b19",
    "b20", "b21", "b22", "c3", "c4", "c7", "c14", "c15", "c16a", "c16b",
    "c17", "d1", "d3", "d4", "d7",
)

_AC_T3_REQUIRED_PATTERN = re.compile(
    r"^def test_ac_(b1|b2|b4|b5|b7|b12|b16|b17|b18|b19|b20|b21|b22|"
    r"c3|c4|c7|c14|c15|c16a|c16b|c17|d1|d3|d4|d7)_",
    re.MULTILINE,
)

_OPENCODE_V2_CONFIG_PATH = _REPO_ROOT / "scripts" / "lib" / "opencode_v2_config.py"


def test_ac_t3_required_acs_have_tests():
    """AC-T3: every required AC has at least one test named after it.

    The sweep reads the source text of this file (regex on
    ``def test_ac_<id>_``), so deleting or renaming a test is caught even when
    the suite stays green for another reason. AC-D9 is owned by
    ``tests/test_artifact_contracts.py`` and AC-C1/AC-C2 by
    ``tests/test_opencode_v2_spike.py`` (spec AC-T3) — those files are checked
    explicitly rather than folded into this file's list.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    found = set(_AC_T3_REQUIRED_PATTERN.findall(source))
    missing = [ac for ac in _AC_T3_SURFACE_IDS if ac not in found]
    assert missing == [], (
        "AC-T3: no test named 'def test_ac_<id>_...' in "
        f"tests/test_opencode_v2_surface.py for: {missing}"
    )

    contracts = (_REPO_ROOT / "tests" / "test_artifact_contracts.py").read_text(
        encoding="utf-8"
    )
    assert re.search(r"^def test_ac_d9_", contracts, re.MULTILINE), (
        "AC-T3/AC-D9: no 'def test_ac_d9_...' test in "
        "tests/test_artifact_contracts.py"
    )

    spike = (_REPO_ROOT / "tests" / "test_opencode_v2_spike.py").read_text(
        encoding="utf-8"
    )
    for ac_id in ("c1", "c2"):
        assert re.search(rf"^def test_ac_{ac_id}_", spike, re.MULTILINE), (
            f"AC-T3/AC-{ac_id.upper()}: no 'def test_ac_{ac_id}_...' test in "
            "tests/test_opencode_v2_spike.py"
        )


def _docstring_constants(tree: ast.AST) -> set[int]:
    """``id()`` of ``Constant`` nodes that are module/class/function docstrings."""
    found: set[int] = set()
    for parent in ast.walk(tree):
        if not isinstance(
            parent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
        ):
            continue
        body = parent.body
        if (
            body
            and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)
        ):
            found.add(id(body[0].value))
    return found


def test_new_v2_code_has_no_provider_branch():
    """AC-T6: the v2 writer branches on resolved values, never on a provider
    name, and never reads the raw ``surface-version`` selector.

    Static AST scan of ``scripts/lib/opencode_v2_config.py``:

    * a registered provider-name literal as an operand of any comparison
      (``==``/``!=``/``in``/``not in``/ordering) is a provider branch;
    * a live ``"surface-version"`` constant (subscript, ``.get`` call,
      comparison, assignment) is a raw-selector read.

    Docstrings are ignored: they document the rule without executing it, and
    comments never reach the AST.
    """
    tree = ast.parse(_OPENCODE_V2_CONFIG_PATH.read_text(encoding="utf-8"))
    providers = yaml.safe_load(
        (_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
    )
    names = set((providers.get("providers") or {}).keys())
    assert names, "config/ai-providers.yaml declares no registered providers"

    docstrings = _docstring_constants(tree)
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for operand in (node.left, *node.comparators):
                for sub in ast.walk(operand):
                    if (
                        isinstance(sub, ast.Constant)
                        and isinstance(sub.value, str)
                        and sub.value in names
                    ):
                        offenders.append(
                            f"opencode_v2_config.py:{sub.lineno}: compares "
                            f"provider name {sub.value!r}"
                        )
        if (
            isinstance(node, ast.Constant)
            and node.value == "surface-version"
            and id(node) not in docstrings
        ):
            offenders.append(
                f"opencode_v2_config.py:{node.lineno}: reads 'surface-version'"
            )
    assert offenders == [], (
        "AC-T6: scripts/lib/opencode_v2_config.py must dispatch on resolved "
        "config values only:\n" + "\n".join(sorted(offenders))
    )


# --- AC-T5: CHANGELOG entry for the opencode v2 surface (Task 32 / R.1) -----


def _changelog_unreleased_section() -> str:
    """Return the body of the ``## [Unreleased]`` section of ``CHANGELOG.md``.

    The section ends at the next level-2 heading, so a later release block can
    never satisfy an assertion about the unreleased entry.
    """
    changelog = _REPO_ROOT / "CHANGELOG.md"
    assert changelog.is_file(), f"missing CHANGELOG.md: {changelog}"
    text = changelog.read_text(encoding="utf-8")
    marker = "## [Unreleased]"
    assert marker in text, f"CHANGELOG.md carries no {marker!r} section"
    body = text.split(marker, 1)[1]
    return body.split("\n## ", 1)[0]


def test_changelog_mentions_opencode_v2_support():
    """AC-T5 (Task 32): the Unreleased section records the v2 surface.

    The entry is the user-facing summary of the whole v2 package, so it must
    name the feature (``opencode v2``) and the newly managed file
    (``cli.json``) — both were absent before this task.
    """
    unreleased = _changelog_unreleased_section().lower()
    assert "opencode v2" in unreleased, (
        "the [Unreleased] section must document the opencode v2 surface"
    )
    assert "cli.json" in unreleased, (
        "the [Unreleased] section must document the managed cli.json"
    )
