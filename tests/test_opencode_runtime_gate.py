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

Issue #1006 (IC-4/IC-5/IC-6) extends this: the ``default-agent`` state namespace
is a third, dict-valued sibling (AC-13), ``opencode_runtime_gate_wanted`` mirrors
the entry computation, ``_opencode_entry_point`` resolves the explicit +
generated primary role and ``_merge_default_agent`` writes/rolls back
``default_agent`` in the managed merge (AC-06…AC-09, AC-14).

Task 7 couples the deny to that entry point (AC-10): without an explicit AND
generated primary role no deny is written, exactly one warning names
``primary-role``, and a deny managed by an earlier sync is rolled back.

Follow-up decisions on top of the merged spec:

- D1a: deny and entry point are ONE invariant. A state error (the managed
  ``default_agent`` was deleted / is unusable while the gate is wanted) suspends
  the gate with a loud warning instead of leaving a half-active lockout.
- D1b: the legacy strict default is ``true`` in exactly one source
  (``variables._resolve_orch_mode``; ``orchestrator_strict`` delegates).
- D1c: an explicitly set, differing user ``default_agent`` is respected and the
  warning names that edit/shell stay locked for it.
- D2b: the flip reaches existing projects through a version-driven grace window
  (WARNING, gate deferred) before it becomes hard.

Run: python -m pytest tests/test_opencode_runtime_gate.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import isolation
from lib.log import SyncLog

_ISOLATION_KEY = isolation._STATE_ISOLATION_KEY
_RUNTIME_GATE_KEY = isolation._STATE_RUNTIME_GATE_KEY
_DEFAULT_AGENT_KEY = isolation._STATE_DEFAULT_AGENT_KEY
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
    """Namespaced state file; an absent file has no namespaces (like
    ``isolation._read_state``, which yields the empty value per key)."""
    path = project_root / _STATE_FILE
    return _read_json(path) if path.exists() else {}


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
    # D1b: the legacy default is strict (the fixture root has no VERSION, so the
    # D2b grace window is inactive -> hard). An empty orchestrator block must
    # therefore produce the deny, exactly like an explicit ``mode: strict``.
    assert isolation._opencode_runtime_gate_entries(
        {}, "Opencode", framework, provider_config
    ) == {"edit": {"**": "deny"}, "bash": {"**": "deny"}}

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
        {"Opencode": {"has_hooks": False, "primary-role": "orchestrator"}},
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
    provider_config = {"Opencode": {"has_hooks": False, "primary-role": "orchestrator"}}
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
    provider_config = {"Opencode": {"has_hooks": False, "primary-role": "orchestrator"}}
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
            "primary-role": "orchestrator",
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
        {"Opencode": {"has_hooks": False, "primary-role": "orchestrator"}},
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
        {"Opencode": {"has_hooks": False, "primary-role": "orchestrator"}},
        framework,
        log,
        dry_run=False,
    )

    data = _read_json(project_root / "opencode.json")
    assert data == {
        "permission": {"edit": {"**": "deny"}, "bash": {"**": "deny"}},
        "default_agent": "orchestrator",
    }


def test_default_agent_namespace_reads_as_dict(tmp_path):
    """IC-5: the ``default-agent`` namespace is dict-valued, ``{}`` when
    missing/invalid — never a list."""
    state_path = tmp_path / _STATE_FILE
    assert isolation._read_state(state_path, _DEFAULT_AGENT_KEY) == {}

    state_path.parent.mkdir(parents=True)
    isolation._write_state(
        state_path,
        {"value": "orchestrator", "prior": None},
        dry_run=False,
        key=_DEFAULT_AGENT_KEY,
    )

    assert _read_json(state_path)[_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }
    assert isolation._read_state(state_path, _DEFAULT_AGENT_KEY) == {
        "value": "orchestrator",
        "prior": None,
    }


def test_default_agent_namespace_coexists_with_siblings(tmp_path):
    """AC-13: all three namespaces coexist; removing one leaves the others."""
    state_path = tmp_path / _STATE_FILE
    state_path.parent.mkdir(parents=True)

    isolation._write_state(state_path, ["**/.claude/**"], dry_run=False)
    isolation._write_state(
        state_path,
        {"**": {"edit": None, "bash": None}},
        dry_run=False,
        key=_RUNTIME_GATE_KEY,
    )
    isolation._write_state(
        state_path,
        {"value": "orchestrator", "prior": None},
        dry_run=False,
        key=_DEFAULT_AGENT_KEY,
    )

    data = _read_json(state_path)
    assert data[_ISOLATION_KEY] == ["**/.claude/**"]
    assert data[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}
    assert data[_DEFAULT_AGENT_KEY] == {"value": "orchestrator", "prior": None}
    assert "_agent-meta" in data

    # Removing only the default-agent namespace keeps both siblings intact.
    isolation._write_state(state_path, {}, dry_run=False, key=_DEFAULT_AGENT_KEY)

    data = _read_json(state_path)
    assert _DEFAULT_AGENT_KEY not in data
    assert data[_ISOLATION_KEY] == ["**/.claude/**"]
    assert data[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}
    assert "_agent-meta" in data


def test_entry_point_requires_explicit_primary_role():
    """IC-4: no code default — only an explicit registry key yields a role."""
    assert isolation._opencode_entry_point("Opencode", {"Opencode": {}}, None) is None
    assert (
        isolation._opencode_entry_point(
            "Opencode", {"Opencode": {"primary-role": "orchestrator"}}, None
        )
        == "orchestrator"
    )


def test_entry_point_respects_active_set():
    """IC-4: an explicit role counts only when it is also generated."""
    provider_config = {"Opencode": {"primary-role": "orchestrator"}}
    inactive = SimpleNamespace(roles=frozenset({"developer"}))
    active = SimpleNamespace(roles=frozenset({"developer", "orchestrator"}))

    assert isolation._opencode_entry_point("Opencode", provider_config, inactive) is None
    assert (
        isolation._opencode_entry_point("Opencode", provider_config, active)
        == "orchestrator"
    )
    assert (
        isolation._opencode_entry_point("Opencode", provider_config, None)
        == "orchestrator"
    )


def test_runtime_gate_wanted_mirrors_entries(tmp_path):
    """IC-4: the boolean is exactly ``bool(_opencode_runtime_gate_entries(...))``."""
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    provider_config = {"Opencode": {"has_hooks": False}}

    assert isolation.opencode_runtime_gate_wanted(
        {"orchestrator": {"mode": "strict"}}, "Opencode", framework, provider_config
    ) is True
    assert isolation.opencode_runtime_gate_wanted(
        {"orchestrator": {"mode": "advisory"}}, "Opencode", framework, provider_config
    ) is False


# ---------------------------------------------------------------------------
# #1006 Task 6 (IC-6): ``default_agent`` in the managed merge
# ---------------------------------------------------------------------------

def _pc(primary: bool = True) -> dict:
    """Provider entry with (or without) the explicit ``primary-role`` key."""
    entry: dict = {"has_hooks": False}
    if primary:
        entry["primary-role"] = "orchestrator"
    return {"Opencode": entry}


def _sync(project_root, framework, config, pc, log, active_set=None,
          dry_run: bool = False) -> None:
    isolation._sync_opencode_runtime_gate(
        project_root, config, "Opencode", pc, framework, log,
        dry_run=dry_run, active_set=active_set,
    )


def _make_project(tmp_path) -> Path:
    project_root = tmp_path / "project"
    project_root.mkdir()
    return project_root


def test_default_agent_written_with_state_and_idempotent(tmp_path):
    """AC-06: a missing ``default_agent`` is written once, with state."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    config = {"orchestrator": {"mode": "strict"}}
    (project_root / "opencode.json").write_text(
        json.dumps({"theme": "x"}) + "\n", encoding="utf-8"
    )

    _sync(project_root, framework, config, _pc(), SyncLog())

    data = _read_json(project_root / "opencode.json")
    assert data["default_agent"] == "orchestrator"
    assert data["theme"] == "x"
    assert _read_state(project_root)[_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }

    first_json = (project_root / "opencode.json").read_bytes()
    first_state = (project_root / _STATE_FILE).read_bytes()

    _sync(project_root, framework, config, _pc(), SyncLog())

    assert (project_root / "opencode.json").read_bytes() == first_json
    assert (project_root / _STATE_FILE).read_bytes() == first_state


def test_differing_user_default_agent_not_overwritten_warns(tmp_path):
    """AC-07: a user value wins, exactly one warning (with consequence under
    an effective gate); the gate deny is still written."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    (project_root / "opencode.json").write_text(
        json.dumps({"default_agent": "build"}) + "\n", encoding="utf-8"
    )
    log = SyncLog()

    _sync(project_root, framework, {"orchestrator": {"mode": "strict"}}, _pc(), log)

    data = _read_json(project_root / "opencode.json")
    assert data["default_agent"] == "build"
    assert data["permission"]["edit"]["**"] == "deny"
    assert _DEFAULT_AGENT_KEY not in _read_state(project_root)
    assert len(log.warnings) == 1, log.warnings
    # D1c: the concrete consequence is named — edit/shell stay locked for the
    # user's agent (it is respected, never overwritten).
    for token in ("build", "orchestrator", "provider-overrides", "edit", "shell"):
        assert token in log.warnings[0], log.warnings

    # Without strict the gate is not effective: no consequence hint.
    quiet_root = tmp_path / "project2"
    quiet_root.mkdir()
    (quiet_root / "opencode.json").write_text(
        json.dumps({"default_agent": "build"}) + "\n", encoding="utf-8"
    )
    quiet_log = SyncLog()

    _sync(
        quiet_root, framework, {"orchestrator": {"mode": "advisory"}},
        _pc(), quiet_log,
    )

    assert _read_json(quiet_root / "opencode.json")["default_agent"] == "build"
    assert not (quiet_root / _STATE_FILE).exists()
    assert len(quiet_log.warnings) == 1, quiet_log.warnings
    assert "build" in quiet_log.warnings[0]
    assert "orchestrator" in quiet_log.warnings[0]
    assert "provider-overrides" not in quiet_log.warnings[0]


def test_same_user_default_agent_records_prior_and_survives_rollback(tmp_path):
    """AC-08: user value == entry point -> no file change, ``prior`` recorded."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    (project_root / "opencode.json").write_text(
        json.dumps({"default_agent": "orchestrator"}, indent=2) + "\n",
        encoding="utf-8",
    )
    before = (project_root / "opencode.json").read_bytes()
    advisory = {"orchestrator": {"mode": "advisory"}}

    _sync(project_root, framework, advisory, _pc(), SyncLog())

    assert (project_root / "opencode.json").read_bytes() == before
    assert _read_state(project_root)[_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": "orchestrator",
    }

    _sync(project_root, framework, advisory, _pc(primary=False), SyncLog())

    assert _read_json(project_root / "opencode.json")["default_agent"] == "orchestrator"
    assert _DEFAULT_AGENT_KEY not in _read_state(project_root)


def test_default_agent_rollback_removes_key_when_prior_none(tmp_path):
    """AC-09: prior ``None`` -> key removed; user keys and sibling namespaces
    stay untouched."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    config = {"orchestrator": {"mode": "strict"}}
    (project_root / "opencode.json").write_text(
        json.dumps({"theme": "x"}) + "\n", encoding="utf-8"
    )
    state_path = project_root / _STATE_FILE
    state_path.parent.mkdir(parents=True)
    isolation._write_state(state_path, ["**/.claude/**"], dry_run=False)

    _sync(project_root, framework, config, _pc(), SyncLog())

    data = _read_json(project_root / "opencode.json")
    assert data["default_agent"] == "orchestrator"
    state = _read_state(project_root)
    assert state[_DEFAULT_AGENT_KEY] == {"value": "orchestrator", "prior": None}
    assert state[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}

    _sync(project_root, framework, config, _pc(primary=False), SyncLog())

    data = _read_json(project_root / "opencode.json")
    assert "default_agent" not in data
    assert data["theme"] == "x"
    state = _read_state(project_root)
    assert _DEFAULT_AGENT_KEY not in state
    assert state[_ISOLATION_KEY] == ["**/.claude/**"]
    # #1006 Task 7: the deny is coupled to the entry point, so dropping the
    # primary role takes the managed deny back as well.
    assert _RUNTIME_GATE_KEY not in state


def test_default_agent_rollback_keeps_user_changed_value(tmp_path):
    """AC-09: a user change after the managed write survives the rollback."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    config = {"orchestrator": {"mode": "strict"}}

    _sync(project_root, framework, config, _pc(), SyncLog())
    data = _read_json(project_root / "opencode.json")
    assert data["default_agent"] == "orchestrator"
    data["default_agent"] = "build"
    (project_root / "opencode.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )

    _sync(project_root, framework, config, _pc(primary=False), SyncLog())

    assert _read_json(project_root / "opencode.json")["default_agent"] == "build"
    assert _DEFAULT_AGENT_KEY not in _read_state(project_root)


def test_default_agent_follows_changed_primary_role(tmp_path):
    """IC-6: a changed explicit role is followed while the state is ours."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    config = {"orchestrator": {"mode": "strict"}}

    _sync(project_root, framework, config, _pc(), SyncLog())
    assert _read_state(project_root)[_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }

    changed = {"Opencode": {"has_hooks": False, "primary-role": "developer"}}
    _sync(project_root, framework, config, changed, SyncLog())

    assert _read_json(project_root / "opencode.json")["default_agent"] == "developer"
    assert _read_state(project_root)[_DEFAULT_AGENT_KEY] == {
        "value": "developer",
        "prior": None,
    }


def test_user_deleted_default_agent_is_not_rewritten_warns(tmp_path):
    """IC-6: a deleted managed key is NOT re-created; warn and keep state."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    config = {"orchestrator": {"mode": "strict"}}

    _sync(project_root, framework, config, _pc(), SyncLog())
    data = _read_json(project_root / "opencode.json")
    assert data["default_agent"] == "orchestrator"
    data.pop("default_agent")
    (project_root / "opencode.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    log = SyncLog()

    _sync(project_root, framework, config, _pc(), log)

    assert "default_agent" not in _read_json(project_root / "opencode.json")
    assert _read_state(project_root)[_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": None,
    }
    assert len(log.warnings) == 1, log.warnings
    assert "orchestrator" in log.warnings[0]
    # A deleted key has no value to quote: never render the literal 'None'.
    assert "'None'" not in log.warnings[0], log.warnings
    assert "None" not in log.warnings[0], log.warnings
    assert "missing" in log.warnings[0], log.warnings
    assert "removed" in log.warnings[0], log.warnings


def test_three_sync_restores_different_prior_value(tmp_path):
    """IC-6: a prior user value survives two managed rewrites.

    ``orchestrator`` (user, same as the first entry point) → primary role
    changes to ``developer`` (managed write) → primary role removed ⇒ the
    original ``orchestrator`` is restored, not the intermediate managed value.
    """
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    config = {}
    (project_root / "opencode.json").write_text(
        json.dumps({"default_agent": "orchestrator"}, indent=2) + "\n",
        encoding="utf-8",
    )

    # Sync 1: the user already set our entry point -> prior recorded.
    _sync(project_root, framework, config, _pc(), SyncLog())
    assert _read_json(project_root / "opencode.json")["default_agent"] == "orchestrator"
    assert _read_state(project_root)[_DEFAULT_AGENT_KEY] == {
        "value": "orchestrator",
        "prior": "orchestrator",
    }

    # Sync 2: the explicit primary role changes -> managed rewrite.
    developer = {"Opencode": {"has_hooks": False, "primary-role": "developer"}}
    _sync(project_root, framework, config, developer, SyncLog())
    assert _read_json(project_root / "opencode.json")["default_agent"] == "developer"
    assert _read_state(project_root)[_DEFAULT_AGENT_KEY] == {
        "value": "developer",
        "prior": "orchestrator",
    }

    # Sync 3: the primary role is gone -> the ORIGINAL user value comes back.
    _sync(project_root, framework, config, _pc(primary=False), SyncLog())
    assert _read_json(project_root / "opencode.json")["default_agent"] == "orchestrator"
    assert _DEFAULT_AGENT_KEY not in _read_state(project_root)


def test_sync_action_names_only_what_changed(tmp_path):
    """RVW-A2-2: the action text must not claim a deny that was never written."""
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")

    # Non-strict: no deny at all — only the entry point changes.
    non_strict = {"orchestrator": {"mode": "advisory"}}
    non_strict_root = _make_project(tmp_path)
    non_strict_log = SyncLog()
    _sync(non_strict_root, framework, non_strict, _pc(), non_strict_log)
    writes = [a for a in non_strict_log.actions if "WRITE" in a]
    assert len(writes) == 1, non_strict_log.actions
    assert "default_agent" in writes[0]
    assert "runtime-gate deny" not in writes[0], writes[0]

    # Strict: the deny is written and named, plus the entry point.
    strict_root = tmp_path / "project-strict"
    strict_root.mkdir()
    strict_log = SyncLog()
    _sync(
        strict_root, framework, {"orchestrator": {"mode": "strict"}}, _pc(), strict_log
    )
    writes = [a for a in strict_log.actions if "WRITE" in a]
    assert len(writes) == 1, strict_log.actions
    for token in ("runtime-gate deny", "default_agent"):
        assert token in writes[0], writes[0]

    # Strict -> non-strict: the text reports the removal, not a write.
    rollback_log = SyncLog()
    _sync(strict_root, framework, non_strict, _pc(), rollback_log)
    writes = [a for a in rollback_log.actions if "WRITE" in a]
    assert len(writes) == 1, rollback_log.actions
    assert "runtime-gate deny removed" in writes[0], writes[0]
    assert "default_agent" not in writes[0], writes[0]


def test_inactive_primary_role_gets_no_default_agent(tmp_path):
    """IC-4/IC-6: a non-generated primary role writes neither key nor state."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    active_set = SimpleNamespace(roles=frozenset({"developer"}))

    _sync(
        project_root,
        framework,
        {"orchestrator": {"mode": "strict"}},
        _pc(),
        SyncLog(),
        active_set=active_set,
    )

    assert "default_agent" not in _read_json(project_root / "opencode.json")
    assert _DEFAULT_AGENT_KEY not in _read_state(project_root)


def test_unparseable_opencode_json_is_left_untouched(tmp_path):
    """AC-14: an unparseable file is never rewritten; no state is created."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    settings = project_root / "opencode.json"
    settings.write_text("{not json", encoding="utf-8")
    log = SyncLog()

    _sync(project_root, framework, {"orchestrator": {"mode": "strict"}}, _pc(), log)

    assert settings.read_text(encoding="utf-8") == "{not json"
    assert not (project_root / _STATE_FILE).exists()
    assert log.warnings


def test_dry_run_with_primary_role_never_writes(tmp_path):
    """AC-14: ``dry_run`` writes neither ``opencode.json`` nor the state file."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")

    _sync(
        project_root,
        framework,
        {"orchestrator": {"mode": "strict"}},
        _pc(),
        SyncLog(),
        dry_run=True,
    )

    assert not (project_root / "opencode.json").exists()
    assert not (project_root / _STATE_FILE).exists()


# ---------------------------------------------------------------------------
# #1006 Task 7 (IC-6 step 2): gate-deny coupled to the entry point
# ---------------------------------------------------------------------------

def test_strict_with_primary_role_writes_deny_and_default_agent(tmp_path):
    """AC-10: an explicit AND generated primary role keeps deny + entry point."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")

    _sync(
        project_root,
        framework,
        {"orchestrator": {"mode": "strict"}},
        _pc(),
        SyncLog(),
    )

    data = _read_json(project_root / "opencode.json")
    assert data["permission"]["edit"]["**"] == "deny"
    assert data["permission"]["bash"]["**"] == "deny"
    assert data["default_agent"] == "orchestrator"
    state = _read_state(project_root)
    assert state[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}
    assert state[_DEFAULT_AGENT_KEY] == {"value": "orchestrator", "prior": None}


def test_strict_without_primary_role_writes_no_deny_and_warns(tmp_path):
    """AC-10: strict without an entry point writes NO deny (it would lock every
    agent) and warns about the missing ``primary-role`` — exactly once."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    log = SyncLog()

    _sync(
        project_root,
        framework,
        {"orchestrator": {"mode": "strict"}},
        _pc(primary=False),
        log,
    )

    data = _read_json(project_root / "opencode.json")
    assert "permission" not in data
    assert "default_agent" not in data
    state = _read_state(project_root)
    assert _RUNTIME_GATE_KEY not in state
    assert _DEFAULT_AGENT_KEY not in state
    assert len(log.warnings) == 1, log.warnings
    assert "primary-role" in log.warnings[0], log.warnings
    assert "NOT written" in log.warnings[0], log.warnings
    assert "Opencode" in log.warnings[0], log.warnings


def test_strict_with_inactive_primary_role_writes_no_deny(tmp_path):
    """AC-10: a declared but not-generated primary role writes no deny either."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    active_set = SimpleNamespace(roles=frozenset({"developer"}))
    log = SyncLog()

    _sync(
        project_root,
        framework,
        {"orchestrator": {"mode": "strict"}},
        _pc(),
        log,
        active_set=active_set,
    )

    data = _read_json(project_root / "opencode.json")
    assert "permission" not in data
    assert "default_agent" not in data
    assert _RUNTIME_GATE_KEY not in _read_state(project_root)
    assert len(log.warnings) == 1, log.warnings
    assert "primary-role" in log.warnings[0], log.warnings


def test_managed_deny_rolled_back_when_entry_point_disappears(tmp_path):
    """AC-10: losing the entry point takes the managed deny back — the prior
    user value is restored (``edit``), an absent one is removed (``bash``), and
    the ``default_agent`` plus both state namespaces are dropped."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    config = {"orchestrator": {"mode": "strict"}}
    (project_root / "opencode.json").write_text(
        json.dumps({"permission": {"edit": {"**": "allow"}}}) + "\n",
        encoding="utf-8",
    )

    _sync(project_root, framework, config, _pc(), SyncLog())

    data = _read_json(project_root / "opencode.json")
    assert data["permission"]["edit"]["**"] == "deny"
    assert data["permission"]["bash"]["**"] == "deny"
    assert data["default_agent"] == "orchestrator"

    log = SyncLog()
    _sync(project_root, framework, config, _pc(primary=False), log)

    data = _read_json(project_root / "opencode.json")
    assert data["permission"]["edit"]["**"] == "allow"
    assert "**" not in data["permission"]["bash"]
    assert "default_agent" not in data
    state = _read_state(project_root)
    assert _RUNTIME_GATE_KEY not in state
    assert _DEFAULT_AGENT_KEY not in state
    assert len(log.warnings) == 1, log.warnings
    assert "primary-role" in log.warnings[0], log.warnings


# ---------------------------------------------------------------------------
# AC-B16 (part 1): the four opencode-v2 state namespaces are dict-valued
# ---------------------------------------------------------------------------

# Contract literals, deliberately spelled out here (not imported from
# ``isolation``) so the RED phase fails on the *behaviour* rather than on a
# missing attribute. The trailing assertions pin the constants to them.
_V2_NAMESPACES = (
    "opencode-v2-keys",
    "opencode-v2-permissions",
    "opencode-v2-cli",
    "opencode-v2-mcp",
)


def test_ac_b16_read_state_returns_dict_for_v2_namespaces(tmp_path):
    """AC-B16: each v2 namespace reads as ``{}`` when the state file is absent,
    when the namespace key is missing and when a non-dict value is stored —
    never as ``[]`` (a list default would make the managed-merge engine treat
    the namespace as an empty list and clobber it on write)."""
    state_path = tmp_path / _STATE_FILE

    # 1. missing file
    for namespace in _V2_NAMESPACES:
        assert isolation._read_state(state_path, namespace) == {}

    # 2. existing file, namespace key absent
    state_path.parent.mkdir(parents=True)
    state_path.write_text(
        json.dumps({_ISOLATION_KEY: ["**/.claude/**"]}) + "\n", encoding="utf-8"
    )
    for namespace in _V2_NAMESPACES:
        assert isolation._read_state(state_path, namespace) == {}

    # 3. existing file, namespace holds a non-dict value
    state_path.write_text(
        json.dumps({namespace: [] for namespace in _V2_NAMESPACES}) + "\n",
        encoding="utf-8",
    )
    for namespace in _V2_NAMESPACES:
        assert isolation._read_state(state_path, namespace) == {}

    # Single source of truth for Task 7 (``opencode_v2_config`` imports these).
    assert isolation._STATE_V2_KEYS == "opencode-v2-keys"
    assert isolation._STATE_V2_PERMISSIONS == "opencode-v2-permissions"
    assert isolation._STATE_V2_CLI == "opencode-v2-cli"
    assert isolation._STATE_V2_MCP == "opencode-v2-mcp"


def test_ac_b16_v2_namespaces_do_not_clobber_siblings(tmp_path):
    """AC-B16: writing the ``opencode-v2-keys`` namespace preserves the
    pre-existing ``isolation-deny`` and ``runtime-gate-deny`` namespaces."""
    state_path = tmp_path / _STATE_FILE
    state_path.parent.mkdir(parents=True)

    isolation._write_state(state_path, ["**/.claude/**"], dry_run=False)
    isolation._write_state(
        state_path,
        {"**": {"edit": None, "bash": None}},
        dry_run=False,
        key=_RUNTIME_GATE_KEY,
    )

    v2_state = {
        "experimental.todo": {
            "value": True, "prior": None, "prior_absent": True,
        }
    }
    isolation._write_state(state_path, v2_state, dry_run=False, key="opencode-v2-keys")

    data = _read_json(state_path)
    assert data[_ISOLATION_KEY] == ["**/.claude/**"]
    assert data[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}
    assert data["opencode-v2-keys"] == v2_state

    # Dropping the v2 namespace again leaves both siblings untouched.
    isolation._write_state(state_path, {}, dry_run=False, key="opencode-v2-keys")
    data = _read_json(state_path)
    assert data[_ISOLATION_KEY] == ["**/.claude/**"]
    assert data[_RUNTIME_GATE_KEY] == {"**": {"edit": None, "bash": None}}
    assert "opencode-v2-keys" not in data


def test_isolation_namespace_still_returns_list(tmp_path):
    """Regression guard: list-shaped namespaces keep returning ``[]`` and the
    two Spec-A dict namespaces keep returning ``{}`` — the v2 extension must not
    change any existing default."""
    state_path = tmp_path / _STATE_FILE

    # Absent file: isolation-deny is a list, the Spec-A namespaces are dicts.
    assert isolation._read_state(state_path) == []
    assert isolation._read_state(state_path, _ISOLATION_KEY) == []
    assert isolation._read_state(state_path, _RUNTIME_GATE_KEY) == {}
    assert isolation._read_state(state_path, _DEFAULT_AGENT_KEY) == {}

    state_path.parent.mkdir(parents=True)
    isolation._write_state(state_path, ["**/opencode.json"], dry_run=False)
    isolation._write_state(
        state_path,
        {"value": "orchestrator", "prior": None},
        dry_run=False,
        key=_DEFAULT_AGENT_KEY,
    )

    assert isolation._read_state(state_path) == ["**/opencode.json"]
    assert isolation._read_state(state_path, _ISOLATION_KEY) == ["**/opencode.json"]
    assert isolation._read_state(state_path, _DEFAULT_AGENT_KEY) == {
        "value": "orchestrator", "prior": None,
    }
    # Missing runtime-gate namespace still degrades to a dict, not a list.
    assert isolation._read_state(state_path, _RUNTIME_GATE_KEY) == {}


# ---------------------------------------------------------------------------
# D1a: deny and entry point are ONE invariant (no half-active gate)
# ---------------------------------------------------------------------------

def test_deleted_default_agent_suspends_gate_instead_of_locking_out(tmp_path):
    """D1a: a managed key the user deleted is a state error, not a silent
    half-active gate — the deny is taken back and a loud warning is emitted.

    Without the invariant the second sync would keep the project-wide deny while
    no agent is pre-selected: exactly the #1006 lockout.
    """
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    config = {"orchestrator": {"mode": "strict"}}

    _sync(project_root, framework, config, _pc(), SyncLog())
    data = _read_json(project_root / "opencode.json")
    assert data["default_agent"] == "orchestrator"
    assert data["permission"]["bash"]["**"] == "deny"

    # The user deletes the managed entry point.
    data.pop("default_agent")
    (project_root / "opencode.json").write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    log = SyncLog()

    _sync(project_root, framework, config, _pc(), log)

    data = _read_json(project_root / "opencode.json")
    assert "default_agent" not in data
    # The managed deny is rolled back (prior was absent) — the document keeps
    # NO project-wide edit/bash deny without an entry point.
    assert "**" not in data["permission"]["edit"]
    assert "**" not in data["permission"]["bash"]
    assert _RUNTIME_GATE_KEY not in _read_state(project_root)
    assert _DEFAULT_AGENT_KEY in _read_state(project_root)
    assert len(log.warnings) == 1, log.warnings
    warning = log.warnings[0]
    assert "SUSPENDED" in warning, warning
    assert "orchestrator" in warning, warning
    assert "lock" in warning.lower(), warning


def test_unusable_default_agent_value_suspends_gate(tmp_path):
    """D1a: a non-string ``default_agent`` (unusable value) is not a valid
    entry point either — the deny is not written."""
    project_root = _make_project(tmp_path)
    framework = _write_caps(tmp_path / "fw", "Opencode", "permission")
    (project_root / "opencode.json").write_text(
        json.dumps({"default_agent": 42}) + "\n", encoding="utf-8"
    )
    log = SyncLog()

    _sync(
        project_root, framework, {"orchestrator": {"mode": "strict"}},
        _pc(), log,
    )

    data = _read_json(project_root / "opencode.json")
    assert "permission" not in data, "no deny without a usable entry point"
    assert data["default_agent"] == 42, "a user value is never overwritten"
    assert any("SUSPENDED" in w for w in log.warnings), log.warnings


# ---------------------------------------------------------------------------
# D1b: the legacy strict default is ``true`` — ONE source
# ---------------------------------------------------------------------------

def test_legacy_strict_default_is_true_in_one_source():
    """D1b: template rendering and runtime gate resolve the same default."""
    from lib import variables
    from lib.consistency import orchestrator_strict as orch_strict

    assert variables._resolve_orch_mode({}) == "strict"
    assert variables._resolve_orch_mode({"enabled": True}) == "strict"
    assert variables._resolve_orch_mode({"enabled": False}) == "main-chat"
    assert variables._resolve_orch_mode({}, {"mode": "advisory"}) == "advisory"

    # The gate resolver delegates to that single source (no second resolver):
    # VERSION of this checkout is inside the D2b grace window, so the *implicit*
    # default is announced, while every explicit setting is hard.
    assert orch_strict._resolve_effective_strict(
        {"mode": "strict"}, "Opencode", _REPO_ROOT
    ) is True
    assert orch_strict._resolve_effective_strict(
        {"mode": "advisory"}, "Opencode", _REPO_ROOT
    ) is False
    assert orch_strict._resolve_effective_strict(
        {"enabled": False}, "Opencode", _REPO_ROOT
    ) is False
    # Fail-soft for an invalid mode (the checker must not abort the process —
    # same behaviour as before the resolver unification).
    assert orch_strict._resolve_effective_strict(
        {"mode": "bogus"}, "Opencode", _REPO_ROOT
    ) is False


# ---------------------------------------------------------------------------
# D2b: version-driven grace window for the implicit strict default
# ---------------------------------------------------------------------------

def _framework_with_version(tmp_path: Path, version: str) -> Path:
    root = _write_caps(tmp_path / f"fw-{version}", "Opencode", "permission")
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")
    return root


def test_strict_default_grace_window_is_data_driven(tmp_path):
    """D2b: < 2.1.0 announces (gate off), >= 2.1.0 enforces (gate on)."""
    from lib.consistency import orchestrator_strict as orch_strict

    grace_root = _framework_with_version(tmp_path, "2.0.0-beta.4")
    hard_root = _framework_with_version(tmp_path, "2.1.0")

    assert orch_strict.strict_default_grace_active(grace_root) is True
    assert orch_strict.strict_default_grace_active(hard_root) is False
    # A fixture root without VERSION is not a real installation -> hard.
    assert orch_strict.strict_default_grace_active(tmp_path / "no-version") is False

    # Implicit default: deferred inside the window, hard afterwards.
    assert orch_strict._resolve_effective_strict({}, "Opencode", grace_root) is False
    assert orch_strict._resolve_effective_strict({}, "Opencode", hard_root) is True
    # Explicit settings are ALWAYS hard, even inside the grace window.
    assert orch_strict._resolve_effective_strict(
        {"strict": True}, "Opencode", grace_root
    ) is True
    assert orch_strict._resolve_effective_strict(
        {"mode": "strict"}, "Opencode", grace_root
    ) is True
    assert orch_strict._resolve_effective_strict(
        {"strict": False}, "Opencode", hard_root
    ) is False

    notice = orch_strict.strict_default_notice({}, grace_root)
    assert notice is not None
    assert "2.1.0" in notice, notice
    assert "advisory" in notice and "strict" in notice, notice
    assert orch_strict.strict_default_notice({}, hard_root) is None
    assert orch_strict.strict_default_notice({"mode": "strict"}, grace_root) is None
    # main-chat never receives the strict-default notice.
    assert orch_strict.strict_default_notice({"enabled": False}, grace_root) is None


def test_default_strict_grace_defers_gate_but_still_writes_entry_point(tmp_path):
    """D2b end-to-end: the behaviour change does not break existing projects.

    A project without explicit config keeps the pre-flip gate behaviour for one
    minor release (no deny) while the entry point still lands, so the eventual
    flip cannot produce the #1006 lockout.
    """
    grace_root = _framework_with_version(tmp_path, "2.0.0")
    project = _make_project(tmp_path)
    log = SyncLog()

    _sync(project, grace_root, {}, _pc(), log)

    data = _read_json(project / "opencode.json")
    assert "permission" not in data, "grace: no gate deny yet"
    assert data["default_agent"] == "orchestrator", "entry point lands immediately"
    assert _RUNTIME_GATE_KEY not in _read_state(project)

    hard_root = _framework_with_version(tmp_path, "2.1.0")
    hard_project = tmp_path / "project-hard"
    hard_project.mkdir()

    _sync(hard_project, hard_root, {}, _pc(), SyncLog())

    data = _read_json(hard_project / "opencode.json")
    assert data["permission"]["edit"]["**"] == "deny"
    assert data["permission"]["bash"]["**"] == "deny"
    assert data["default_agent"] == "orchestrator"
