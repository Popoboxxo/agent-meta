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

The v2 settings surface (``opencode.json``) additionally retains the
``subagent_depth`` key (sourced from the ``required_depth`` capability when
available — IC-15 Nr. 16: the v2 surface must not drop the orchestrator depth)
and emits ``default_agent`` from the ``primary-role`` data key.
``apply_settings_surface_shape`` dispatches on the resolved
``mcp-config.format`` value only; every non-v2 format is returned
byte-for-byte so the shipped v1 surface stays frozen.

Run: python3 -m pytest tests/test_opencode_v2_surface.py -q
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import lib.sync_pipeline as sync_pipeline
from lib import isolation, opencode_v2_config
from lib.context import apply_settings_surface_shape
from lib.log import SyncLog
from lib.opencode_v2_config import STATE_KEYS_KEY
from lib.providers import load_providers_config

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


def test_v2_settings_keep_subagent_depth_and_emit_default_agent():
    out = apply_settings_surface_shape(_SETTINGS_TEMPLATE, _pc_v2())
    doc = json.loads(out)
    assert doc["subagent_depth"] == 3, (
        "the v2 surface must retain the shipped subagent_depth (IC-15 Nr. 16)"
    )
    assert doc["default_agent"] == "orchestrator"


def test_v2_settings_subagent_depth_comes_from_required_depth():
    doc = json.loads(
        apply_settings_surface_shape(_SETTINGS_TEMPLATE, _pc_v2(), {"required_depth": 2})
    )
    assert doc["subagent_depth"] == 2


def test_v2_settings_default_agent_comes_from_primary_role():
    pc = _pc_v2()
    pc["primary-role"] = "developer"
    doc = json.loads(apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc))
    assert doc["default_agent"] == "developer"


def test_v2_settings_without_primary_role_emits_no_default_agent():
    pc = _pc_v2()
    pc.pop("primary-role")
    doc = json.loads(apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc))
    assert doc["subagent_depth"] == 3
    assert "default_agent" not in doc


def test_v1_settings_template_is_byte_identical():
    """The shipped v1 surface must stay frozen, comments included."""
    pc = {"surface-version": "v1", "mcp-config": {"format": "opencode-json"}}
    assert apply_settings_surface_shape(_SETTINGS_TEMPLATE, pc) == _SETTINGS_TEMPLATE


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
) -> SyncLog:
    log = log if log is not None else SyncLog()
    opencode_v2_config.sync_opencode_v2_managed_keys(
        project_root, config, provider, providers, framework, log, dry_run
    )
    return log


def _warned(log: SyncLog, message: str) -> bool:
    """True when *message* appears in the log (entries carry a ``[WARN]`` prefix)."""
    return any(message in warning for warning in log.warnings)


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

    log = _run(project, _config(3), providers, tmp_path / "fw")

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
    assert kwargs["config"] is config
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
