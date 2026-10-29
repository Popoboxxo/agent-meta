"""#1020: roll back the managed runtime gate on tier change / provider removal.

The managed merge (``isolation._sync_opencode_runtime_gate``) used to run ONLY
while ``provider_runtime_gate_tier(...) == "permission"``. Two consequences:

(a) a tier change away from ``permission`` skipped the rollback branch, leaving
    ``permission.edit/bash["**"] = "deny"`` and the state namespaces
    ``runtime-gate-deny`` / ``default-agent`` behind;
(b) a removed provider was only cleaned up as FILES — ``opencode.json`` kept the
    managed deny and ``default_agent`` while the state file (inside the removed
    provider directory) disappeared, so nothing could ever take them back.

Covered here: the tier-independent rollback helper, the per-provider dispatch
(tier change), the legacy-cleanup path (provider removed from project.yaml) and
the deactivation path (``deactivation.remove_provider_dir``). Every case keeps
the conservative contract: only state-recorded values are touched, a user value
survives, and a foreign provider never touches the shared document.

Run: python -m pytest tests/test_issue_1020_gate_rollback.py -v
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import scripts.lib.sync_pipeline as sync_pipeline  # noqa: E402
from lib import isolation  # noqa: E402
from lib.deactivation import remove_provider_dir  # noqa: E402
from lib.log import SyncLog  # noqa: E402

PROVIDER = "Opencode"
_SETTINGS = Path("opencode.json")
_STATE_FILE = Path(".opencode") / "agent-meta-state.json"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _framework_root(tmp_path: Path, name: str, tier: str) -> Path:
    """Minimal framework root declaring ``PROVIDER`` at the given gate tier."""
    root = tmp_path / name
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "provider-capabilities.yaml").write_text(
        yaml.safe_dump({"capabilities": {PROVIDER: {"runtime_gate": tier}}}),
        encoding="utf-8",
    )
    return root


def _provider_config(primary_role: str | None = "orchestrator") -> dict:
    """Owner entry: declares the managed gate document (``settings_file``)."""
    pc = {
        "has_rules": True,
        "rules_dir": ".test/rules",
        "has_hooks": False,
        "has_commands": False,
        "agents_dir": ".opencode/agents",
        "settings_file": "opencode.json",
        "isolation-dirs": [".opencode/"],
    }
    if primary_role is not None:
        pc["primary-role"] = primary_role
    return {PROVIDER: pc}


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_state(project_root: Path) -> dict:
    path = project_root / _STATE_FILE
    return _read_json(path) if path.exists() else {}


def _project_with_user_values(tmp_path: Path) -> tuple[Path, dict]:
    """Project whose pre-existing user values must be restored exactly."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    original = {
        "permission": {
            "edit": {"src/**": "ask", "**": "allow"},
            "bash": {"**": "allow"},
            "read": {"secret/**": "deny"},
        },
        "default_agent": "user-choice",
        "theme": "night",
    }
    (project_root / _SETTINGS).write_text(
        json.dumps(original, indent=2) + "\n", encoding="utf-8"
    )
    return project_root, original


def _strict_sync(project_root: Path, framework: Path, provider_config: dict,
                 log: SyncLog) -> None:
    isolation._sync_opencode_runtime_gate(
        project_root,
        {"orchestrator": {"mode": "strict"}},
        PROVIDER,
        provider_config,
        framework,
        log,
        dry_run=False,
    )


def _run_per_provider(project_root: Path, framework: Path, monkeypatch,
                      config: dict, provider_config: dict, log: SyncLog) -> None:
    """Drive ``_sync_stage_per_provider`` with every unrelated writer stubbed."""
    monkeypatch.setattr(sync_pipeline, "sync_rules", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_speech_mode", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_agents_for_provider", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_prompts_for_continue", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_embedded_rule_files", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "generate_mcp_artifacts", lambda *a, **k: [])
    monkeypatch.setattr(sync_pipeline, "generate_external_tool_artifacts", lambda *a, **k: [])
    monkeypatch.setattr(sync_pipeline, "sync_snippets_for_provider", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_external_skills_for_provider", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sweep_orphan_skill_channel_rules", lambda *a, **k: None)

    import lib.external_tools as external_tools_module
    import lib.mcp as mcp_module

    monkeypatch.setattr(mcp_module, "load_mcp_registry", lambda *a, **k: {})
    monkeypatch.setattr(
        external_tools_module, "load_external_tools_registry", lambda *a, **k: {}
    )

    sync_pipeline._sync_stage_per_provider(
        framework, project_root, config, provider_config, [PROVIDER], {},
        None, False, False, [], argparse.Namespace(dry_run=False), log, None,
    )


# ---------------------------------------------------------------------------
# Ownership guard (provider-agnostic, no provider-name literal)
# ---------------------------------------------------------------------------

def test_gate_surface_ownership_is_derived_from_resolved_data():
    assert isolation.owns_gate_surface(
        {"Opencode": {"settings_file": "opencode.json"}}, "Opencode"
    ) is True
    assert isolation.owns_gate_surface(
        {"Probe": {"mcp-config": {"committed-file": "opencode.json"}}}, "Probe"
    ) is True
    # Foreign providers declare their own settings document (or none at all).
    assert isolation.owns_gate_surface(
        {"Claude": {"settings_file": ".claude/settings.json"}}, "Claude"
    ) is False
    assert isolation.owns_gate_surface({"Claude": {"has_hooks": True}}, "Claude") is False


def test_gate_state_present_only_for_gate_namespaces(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    state_path = project_root / _STATE_FILE
    state_path.parent.mkdir(parents=True)

    isolation._write_state(state_path, ["**/.claude/**"], dry_run=False)
    assert isolation.gate_state_present(project_root) is False

    isolation._write_state(
        state_path, {"**": {"edit": None, "bash": None}}, dry_run=False,
        key=isolation._STATE_RUNTIME_GATE_KEY,
    )
    assert isolation.gate_state_present(project_root) is True


# ---------------------------------------------------------------------------
# (a) Tier change: the rollback is decoupled from the tier
# ---------------------------------------------------------------------------

def test_tier_change_to_advisory_rolls_back_deny_and_entry_point(tmp_path, monkeypatch):
    """permission -> advisory restores priors and removes both namespaces."""
    project_root, original = _project_with_user_values(tmp_path)
    permission_root = _framework_root(tmp_path, "fw-permission", "permission")
    advisory_root = _framework_root(tmp_path, "fw-advisory", "advisory")
    provider_config = _provider_config()
    log = SyncLog()
    config = {"orchestrator": {"mode": "strict"}}

    _run_per_provider(project_root, permission_root, monkeypatch, config,
                      provider_config, log)

    strict = _read_json(project_root / _SETTINGS)
    assert strict["permission"]["edit"]["**"] == "deny"
    assert strict["permission"]["bash"]["**"] == "deny"
    state = _read_state(project_root)
    assert state[isolation._STATE_RUNTIME_GATE_KEY]["**"] == {
        "edit": "allow", "bash": "allow",
    }
    # A differing user value is never overwritten, so it is not state-tracked.
    assert "default_agent" not in state.get(isolation._STATE_DEFAULT_AGENT_KEY, {})
    assert strict["default_agent"] == "user-choice"

    _run_per_provider(project_root, advisory_root, monkeypatch, config,
                      provider_config, log)

    rolled_back = _read_json(project_root / _SETTINGS)
    # Prior user values restored exactly, unrelated keys untouched.
    assert rolled_back["permission"] == original["permission"]
    assert rolled_back["default_agent"] == "user-choice"
    assert rolled_back["theme"] == "night"
    assert isolation._STATE_RUNTIME_GATE_KEY not in _read_state(project_root)
    assert isolation._STATE_DEFAULT_AGENT_KEY not in _read_state(project_root)


def test_advisory_sync_without_gate_state_still_skips_the_writer(tmp_path, monkeypatch):
    """The dispatch stays narrow: no state ⇒ no writer call, no file created."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    advisory_root = _framework_root(tmp_path, "fw-advisory", "advisory")
    calls: list = []
    monkeypatch.setattr(
        sync_pipeline, "_sync_opencode_runtime_gate",
        lambda *a, **k: calls.append((a, k)),
    )

    _run_per_provider(project_root, advisory_root, monkeypatch,
                      {"orchestrator": {"mode": "strict"}},
                      _provider_config(), SyncLog())

    assert calls == []
    assert not (project_root / _SETTINGS).exists()


# ---------------------------------------------------------------------------
# (b) Provider removal: legacy cleanup + deactivation
# ---------------------------------------------------------------------------

def _removal_project(tmp_path: Path) -> tuple[Path, dict]:
    """A project as left behind by strict sync + generated provider output."""
    project_root = tmp_path / "project"
    (project_root / ".opencode" / "agents").mkdir(parents=True)
    (project_root / ".opencode" / "agents" / "orchestrator.md").write_text(
        "agent\n", encoding="utf-8"
    )
    (project_root / "AGENTS.md").write_text("context\n", encoding="utf-8")
    (project_root / "opencode.json").write_text(
        json.dumps({
            "permission": {
                "edit": {"**": "deny", "**/.claude/**": "deny"},
                "bash": {"**": "deny"},
                "read": {"**/.claude/**": "deny"},
            },
            "default_agent": "orchestrator",
            "theme": "night",
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    state_path = project_root / _STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({
        "_agent-meta": "agent-meta managed — do not edit manually",
        isolation._STATE_ISOLATION_KEY: ["**/.claude/**"],
        isolation._STATE_RUNTIME_GATE_KEY: {"**": {"edit": None, "bash": None}},
        isolation._STATE_DEFAULT_AGENT_KEY: {"value": "orchestrator", "prior": None},
    }, indent=2) + "\n", encoding="utf-8")
    return project_root, _provider_config()


def test_legacy_cleanup_of_removed_provider_rolls_back_gate(tmp_path):
    """#1020 (b): removal leaves no managed deny, no entry point, no state."""
    project_root, provider_config = _removal_project(tmp_path)
    log = SyncLog()

    sync_pipeline._sync_stage_legacy_cleanup(
        project_root, {}, provider_config, [], argparse.Namespace(dry_run=False), log,
    )

    data = _read_json(project_root / _SETTINGS)
    assert "permission" not in data, "managed gate + isolation denies must be gone"
    assert "default_agent" not in data
    assert data["theme"] == "night", "unrelated user content survives"
    assert not (project_root / _STATE_FILE).exists()
    assert not (project_root / ".opencode" / "agents").exists()


def test_legacy_cleanup_leaves_foreign_provider_gate_untouched(tmp_path):
    """A removed foreign provider must never touch the shared opencode file."""
    project_root, _ = _removal_project(tmp_path)
    before = (project_root / _SETTINGS).read_bytes()
    claude_config = {"Claude": {"settings_file": ".claude/settings.json",
                                "agents_dir": ".claude/agents"}}
    (project_root / ".claude" / "agents").mkdir(parents=True)
    (project_root / ".claude" / "agents" / "developer.md").write_text(
        "agent\n", encoding="utf-8"
    )

    sync_pipeline._sync_stage_legacy_cleanup(
        project_root, {}, claude_config, [], argparse.Namespace(dry_run=False),
        SyncLog(),
    )

    assert (project_root / _SETTINGS).read_bytes() == before
    assert (project_root / _STATE_FILE).exists()


def test_deactivation_remove_provider_dir_rolls_back_gate(tmp_path):
    """#1020: deactivation used to delete the provider root only."""
    project_root, provider_config = _removal_project(tmp_path)
    log = SyncLog()

    removed = remove_provider_dir(
        project_root, PROVIDER, provider_config, log, False, config={},
    )

    assert removed is True
    assert not (project_root / ".opencode").exists()
    data = _read_json(project_root / _SETTINGS)
    assert "permission" not in data, "managed gate + isolation denies must be gone"
    assert "default_agent" not in data
    assert data["theme"] == "night", "unrelated user content survives"
    assert not (project_root / _STATE_FILE).exists()


def test_deactivation_rollback_keeps_user_value_it_never_wrote(tmp_path):
    """Conservative: a user ``default_agent`` (not state-recorded) stays."""
    project_root = tmp_path / "project"
    (project_root / ".opencode").mkdir(parents=True)
    (project_root / "opencode.json").write_text(
        json.dumps({"default_agent": "user-choice"}) + "\n", encoding="utf-8"
    )

    remove_provider_dir(
        project_root, PROVIDER, _provider_config(), SyncLog(), False, config={},
    )

    assert _read_json(project_root / _SETTINGS)["default_agent"] == "user-choice"
    assert not (project_root / ".opencode").exists()


def test_rollback_helper_is_idempotent_without_state(tmp_path):
    """No managed state ⇒ no-op (no file creation, no error)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    log = SyncLog()

    isolation.rollback_opencode_runtime_gate(
        project_root, PROVIDER, _provider_config(), log, False, config={},
    )

    assert not (project_root / _SETTINGS).exists()
    assert not (project_root / _STATE_FILE).exists()


def test_tier_change_does_not_touch_the_isolation_deny(tmp_path, monkeypatch):
    """The isolation stage (later in the same sync) owns those globs — rolling
    them back here would only cause churn, so the tier change leaves them."""
    project_root, _ = _project_with_user_values(tmp_path)
    (project_root / _SETTINGS).write_text(
        json.dumps({
            "permission": {
                "edit": {"src/**": "ask", "**": "allow", "**/.claude/**": "deny"},
                "bash": {"**": "allow"},
            },
        }, indent=2) + "\n",
        encoding="utf-8",
    )
    state_path = project_root / _STATE_FILE
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps({
        "_agent-meta": "agent-meta managed — do not edit manually",
        isolation._STATE_ISOLATION_KEY: ["**/.claude/**"],
    }, indent=2) + "\n", encoding="utf-8")

    permission_root = _framework_root(tmp_path, "fw-permission", "permission")
    advisory_root = _framework_root(tmp_path, "fw-advisory", "advisory")
    provider_config = _provider_config()
    log = SyncLog()
    config = {"orchestrator": {"mode": "strict"}}

    _run_per_provider(project_root, permission_root, monkeypatch, config,
                      provider_config, log)
    _run_per_provider(project_root, advisory_root, monkeypatch, config,
                      provider_config, log)

    data = _read_json(project_root / _SETTINGS)
    assert data["permission"]["edit"]["**/.claude/**"] == "deny"
    assert _read_state(project_root)[isolation._STATE_ISOLATION_KEY] == ["**/.claude/**"]


def test_isolation_rollback_keeps_a_user_changed_glob(tmp_path):
    """Only a value still carrying the managed ``deny`` is removed."""
    project_root = tmp_path / "project"
    (project_root / ".opencode").mkdir(parents=True)
    (project_root / _SETTINGS).write_text(
        json.dumps({"permission": {"read": {"**/.claude/**": "allow"}}}) + "\n",
        encoding="utf-8",
    )
    (project_root / _STATE_FILE).write_text(json.dumps({
        "_agent-meta": "agent-meta managed — do not edit manually",
        isolation._STATE_ISOLATION_KEY: ["**/.claude/**"],
    }, indent=2) + "\n", encoding="utf-8")

    isolation.rollback_opencode_runtime_gate(
        project_root, PROVIDER, _provider_config(), SyncLog(), False,
        config={}, include_isolation_deny=True,
    )

    assert _read_json(project_root / _SETTINGS)["permission"]["read"]["**/.claude/**"] == "allow"
    assert isolation._STATE_ISOLATION_KEY not in _read_state(project_root)
