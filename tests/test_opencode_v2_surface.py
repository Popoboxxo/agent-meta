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
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import lib.sync_pipeline as sync_pipeline
from lib import isolation, opencode_v2_config, runtime_gate
from lib.artifact_validate import resolve_artifact_contract, validate_frontmatter
from lib.consistency.artifact_contracts import check_artifact_contracts
from lib.consistency.model_contracts import check_model_contracts
from lib.context import apply_settings_surface_shape
from lib.log import SyncLog
from lib.opencode_v2_config import STATE_KEYS_KEY
from lib.providers import load_provider_capabilities, load_providers_config

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
    }


def _v1_pc() -> dict:
    return {
        "primary-role": "orchestrator",
        "mcp-config": _mcp_block("v1"),
        "agent-transform": {"frontmatter-mechanism": "opencode-native"},
    }


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
) -> tuple[Path, SyncLog, list]:
    """Drive ``_sync_stage_per_provider`` with every unrelated writer stubbed.

    Returns ``(project_root, log, gate_calls)``; ``gate_calls`` records the
    Spec-A runtime-gate writer, so a test can prove a tier did not dispatch it
    while the v2 managed-key writer still ran (AC-B18).
    """
    root = _stage_framework(tmp_path, tiers)
    project_root = tmp_path / "project"
    project_root.mkdir(parents=True, exist_ok=True)
    log = log if log is not None else SyncLog()
    calls = gate_calls if gate_calls is not None else []

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

    def build(provider_config: dict, config: dict, mode: str = "observe") -> list:
        return isolation._opencode_v2_gate_permissions(
            config, "Opencode", framework, provider_config, capabilities, mode
        )

    assert build({"Opencode": without_primary}, _gate_config()) == []

    with_primary = {"Opencode": _v2_pc()}
    assert build(with_primary, _gate_config()) == [_EDIT_DENY, _SHELL_DENY]

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
) -> None:
    isolation.reconcile_opencode_surface_gate(
        project_root,
        config,
        provider,
        provider_config,
        framework,
        log if log is not None else SyncLog(),
        dry_run,
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
