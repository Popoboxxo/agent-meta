"""A2 root-deny + namespaced managed state.

Covers the Phase-0 permission-path tightening (SPEC-OPENCODE-RUNTIME-GATE-
2026-09-13, IC-09):

- AC-10: the Main-Chat deny is merged into an *existing* ``opencode.json`` via
  the isolation merge path (never ``context._init_provider_settings_json``,
  #747), in mapping form ``{'edit': {'**': 'deny'}, 'bash': {'**': 'deny'}}``;
  every user glob survives and a pre-existing user value at ``"**"`` is
  recorded in the ``runtime-gate-deny`` state namespace.
- AC-11: a strict sync is idempotent/byte-identical and a later non-strict sync
  restores the prior user value exactly.
- AC-23: the A2 writer and the isolation writer coexist on the same
  ``opencode.json`` and the same state file (``isolation-deny`` +
  ``runtime-gate-deny``) without clobbering each other.

Run: python -m pytest tests/test_opencode_runtime_gate.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import isolation
from lib.log import SyncLog

_ISOLATION_KEY = isolation._STATE_ISOLATION_KEY
_RUNTIME_GATE_KEY = isolation._STATE_RUNTIME_GATE_KEY
_STATE_FILE = Path(".opencode") / "agent-meta-state.json"


def _write_caps(root: Path, provider: str, tier: str) -> Path:
    """Create a minimal framework root whose capabilities registry declares
    ``provider`` with the given ``runtime_gate`` tier."""
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "provider-capabilities.yaml").write_text(
        yaml.safe_dump({"capabilities": {provider: {"runtime_gate": tier}}}),
        encoding="utf-8",
    )
    return root


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_state(project_root: Path) -> dict:
    return _read_json(project_root / _STATE_FILE)


def test_read_write_state_preserves_sibling_namespaces(tmp_path):
    """AC-23: read-modify-write replaces only one namespace at a time."""
    state_path = tmp_path / _STATE_FILE
    state_path.parent.mkdir(parents=True)

    isolation._write_state(state_path, ["**/.claude/**"], dry_run=False)
    isolation._write_state(
        state_path,
        {"**": {"edit": None, "bash": None}},
        dry_run=False,
        key=_RUNTIME_GATE_KEY,
    )

    data = _read_json(state_path)
    assert data[_ISOLATION_KEY] == ["**/.claude/**"]
    assert data[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}

    # The isolation writer must preserve the runtime-gate namespace (and vice
    # versa) — neither writer may clobber the sibling.
    isolation._write_state(state_path, ["**/opencode.json"], dry_run=False)
    data = _read_json(state_path)
    assert data[_ISOLATION_KEY] == ["**/opencode.json"]
    assert data[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}

    assert isolation._read_state(state_path) == ["**/opencode.json"]
    assert isolation._read_state(state_path, _RUNTIME_GATE_KEY) == {
        "**": {"edit": None, "bash": None}
    }


def test_empty_runtime_gate_namespace_is_removed(tmp_path):
    """AC-11: an empty namespace is dropped, siblings are left intact."""
    state_path = tmp_path / _STATE_FILE
    state_path.parent.mkdir(parents=True)

    isolation._write_state(state_path, ["**/.claude/**"], dry_run=False)
    isolation._write_state(
        state_path, {"**": {"edit": None, "bash": None}}, dry_run=False,
        key=_RUNTIME_GATE_KEY,
    )
    isolation._write_state(state_path, {}, dry_run=False, key=_RUNTIME_GATE_KEY)

    data = _read_json(state_path)
    assert _RUNTIME_GATE_KEY not in data
    assert data[_ISOLATION_KEY] == ["**/.claude/**"]


def test_runtime_gate_entries_mapping_form_under_strict(tmp_path):
    """AC-10: mapping-form deny globs only for a permission tier under strict."""
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    provider_config = {"Opencode": {"has_hooks": False}}

    strict = {"orchestrator": {"mode": "strict"}}
    assert isolation._opencode_runtime_gate_entries(
        strict, "Opencode", framework, provider_config
    ) == {"edit": {"**": "deny"}, "bash": {"**": "deny"}}

    # Only strict mode is in scope (OQ-6).
    assert isolation._opencode_runtime_gate_entries(
        {"orchestrator": {"mode": "advisory"}}, "Opencode", framework, provider_config
    ) == {}
    assert isolation._opencode_runtime_gate_entries(
        {}, "Opencode", framework, provider_config
    ) == {}

    # provider-overrides may narrow strict off for the provider.
    narrowed = {
        "orchestrator": {
            "mode": "strict",
            "provider-overrides": {"Opencode": {"mode": "advisory"}},
        }
    }
    assert isolation._opencode_runtime_gate_entries(
        narrowed, "Opencode", framework, provider_config
    ) == {}

    # A non-permission tier never produces an entry (fail-safe).
    advisory_framework = _write_caps(tmp_path / "fw-advisory", "Opencode", "advisory")
    assert isolation._opencode_runtime_gate_entries(
        strict, "Opencode", advisory_framework, provider_config
    ) == {}

    hook_provider_config = {
        "Opencode": {"has_hooks": True, "hook_protocol": "claude-code-json"}
    }
    assert isolation._opencode_runtime_gate_entries(
        strict, "Opencode", framework, hook_provider_config
    ) == {}


def test_scalar_permission_family_tolerated(tmp_path):
    """D-C4/AC-10: a scalar family is normalised, never raises."""
    assert isolation._permission_mapping("ask") == {"**": "ask"}
    assert isolation._permission_mapping({"src/**": "ask"}) == {"src/**": "ask"}
    assert isolation._permission_mapping(None) == {}
    assert isolation._permission_mapping(["nope"]) == {}

    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "opencode.json").write_text(
        json.dumps({"permission": {"edit": "ask"}}), encoding="utf-8"
    )
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    log = SyncLog()

    isolation._sync_opencode_runtime_gate(
        project_root,
        {"orchestrator": {"mode": "strict"}},
        "Opencode",
        {"Opencode": {"has_hooks": False}},
        framework,
        log,
        dry_run=False,
    )

    data = _read_json(project_root / "opencode.json")
    assert data["permission"]["edit"]["**"] == "deny"
    assert _read_state(project_root)[_RUNTIME_GATE_KEY]["**"]["edit"] == "ask"


def test_prior_user_value_recorded_and_restored(tmp_path):
    """AC-10/AC-11: user entries survive and the prior ``"**"`` value is restored."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    original = {
        "permission": {
            "edit": {"src/**": "ask", "**": "allow"},
            "bash": {"**": "allow"},
            "read": {"secret/**": "deny"},
        }
    }
    (project_root / "opencode.json").write_text(
        json.dumps(original, indent=2) + "\n", encoding="utf-8"
    )
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    provider_config = {"Opencode": {"has_hooks": False}}
    log = SyncLog()

    isolation._sync_opencode_runtime_gate(
        project_root,
        {"orchestrator": {"mode": "strict"}},
        "Opencode",
        provider_config,
        framework,
        log,
        dry_run=False,
    )

    data = _read_json(project_root / "opencode.json")
    assert data["permission"]["edit"]["src/**"] == "ask"
    assert data["permission"]["edit"]["**"] == "deny"
    assert data["permission"]["bash"]["**"] == "deny"
    assert data["permission"]["read"] == {"secret/**": "deny"}
    assert _read_state(project_root)[_RUNTIME_GATE_KEY]["**"] == {
        "edit": "allow",
        "bash": "allow",
    }

    # strict -> non-strict restores the pre-existing user value exactly.
    isolation._sync_opencode_runtime_gate(
        project_root,
        {"orchestrator": {"mode": "advisory"}},
        "Opencode",
        provider_config,
        framework,
        log,
        dry_run=False,
    )

    data = _read_json(project_root / "opencode.json")
    assert data["permission"]["edit"]["src/**"] == "ask"
    assert data["permission"]["edit"]["**"] == "allow"
    assert data["permission"]["bash"]["**"] == "allow"
    assert data["permission"]["read"] == {"secret/**": "deny"}
    assert _RUNTIME_GATE_KEY not in _read_state(project_root)


def test_second_strict_sync_is_idempotent_and_byte_identical(tmp_path):
    """AC-11: a repeated strict sync does not touch the files."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    (project_root / "opencode.json").write_text(
        json.dumps({"permission": {"edit": {"src/**": "ask"}}}) + "\n",
        encoding="utf-8",
    )
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    provider_config = {"Opencode": {"has_hooks": False}}
    config = {"orchestrator": {"mode": "strict"}}
    log = SyncLog()

    isolation._sync_opencode_runtime_gate(
        project_root, config, "Opencode", provider_config, framework, log, dry_run=False
    )
    first_json = (project_root / "opencode.json").read_bytes()
    first_state = (project_root / _STATE_FILE).read_bytes()

    isolation._sync_opencode_runtime_gate(
        project_root, config, "Opencode", provider_config, framework, log, dry_run=False
    )

    assert (project_root / "opencode.json").read_bytes() == first_json
    assert (project_root / _STATE_FILE).read_bytes() == first_state
    assert _read_state(project_root)[_RUNTIME_GATE_KEY] == {
        "**": {"edit": None, "bash": None}
    }


def test_isolation_and_runtime_gate_coexist(tmp_path):
    """AC-23: both writers, both glob families, both namespaces survive."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    provider_config = {
        "Claude": {
            "isolation-dirs": [".claude/"],
            "isolation-mechanism": "claude-settings-deny",
        },
        "Opencode": {
            "has_hooks": False,
            "isolation-dirs": ["opencode.json"],
            "isolation-mechanism": "opencode-permissions",
        },
    }
    config = {"orchestrator": {"mode": "strict"}}
    log = SyncLog()

    def full_sync() -> None:
        # Stage 6 (A2) before stages 8+9 (isolation) — IC-09 writer ordering.
        isolation._sync_opencode_runtime_gate(
            project_root, config, "Opencode", provider_config, framework, log,
            dry_run=False,
        )
        isolation.sync_provider_isolation(
            project_root, ["Claude", "Opencode"], provider_config, log, dry_run=False
        )

    full_sync()
    data = _read_json(project_root / "opencode.json")
    assert data["permission"]["edit"]["**"] == "deny"
    assert data["permission"]["bash"]["**"] == "deny"
    assert data["permission"]["edit"][".claude/**"] == "deny"
    assert data["permission"]["read"][".claude/**"] == "deny"

    state = _read_state(project_root)
    assert state[_ISOLATION_KEY] == [".claude/**"]
    assert state[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}

    first_json = (project_root / "opencode.json").read_bytes()
    first_state = (project_root / _STATE_FILE).read_bytes()

    full_sync()
    assert (project_root / "opencode.json").read_bytes() == first_json
    assert (project_root / _STATE_FILE).read_bytes() == first_state


def test_dry_run_never_writes(tmp_path):
    """IC-09 error path: ``dry_run`` never touches disk."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    log = SyncLog()

    isolation._sync_opencode_runtime_gate(
        project_root,
        {"orchestrator": {"mode": "strict"}},
        "Opencode",
        {"Opencode": {"has_hooks": False}},
        framework,
        log,
        dry_run=True,
    )

    assert not (project_root / "opencode.json").exists()
    assert not (project_root / _STATE_FILE).exists()


def test_absent_config_is_created_with_managed_block(tmp_path):
    """IC-09 error path: an absent ``opencode.json`` is created with only the
    managed permission block — never through the #747 create-only initializer."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    log = SyncLog()

    isolation._sync_opencode_runtime_gate(
        project_root,
        {"orchestrator": {"mode": "strict"}},
        "Opencode",
        {"Opencode": {"has_hooks": False}},
        framework,
        log,
        dry_run=False,
    )

    data = _read_json(project_root / "opencode.json")
    assert data == {"permission": {"edit": {"**": "deny"}, "bash": {"**": "deny"}}}
