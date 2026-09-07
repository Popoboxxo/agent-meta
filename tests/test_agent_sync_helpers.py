"""Unit tests for the sync_agents_for_provider extraction helpers (issue #483).

Covers the two risk-staged helpers in isolation:

- ``_should_skip_role``: the four skip gates (ROLE_MAP, config['roles'],
  role-enabled, MAIN_CHAT orchestrator) with their Claude-gated log.skip
  messages byte-identical to the pre-split monolith.
- ``_cleanup_stale_agents``: stale-file pruning (ext-aware globs), the
  managed-index contract and the DELETE-log/dry-run semantics.
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.agent_sync import _cleanup_stale_agents, _should_skip_role  # noqa: E402


class _LogRecorder:
    """Duck-typed SyncLog stand-in that records skip/action/note/warning calls."""

    def __init__(self):
        self.events = []

    def skip(self, label, reason):
        self.events.append(("skip", label, reason))

    def action(self, kind, label, detail):
        self.events.append(("action", kind, label, detail))

    def note(self, label, detail):
        self.events.append(("note", label, detail))

    def warning(self, msg):
        self.events.append(("warning", msg))


_ROLE_MAP = {
    "developer": "developer",
    "orchestrator": "orchestrator",
    "knowledge-gardener": "knowledge-gardener",
    "se-architect": "se-architect",
}


def _skip_call(provider="Claude", role="developer", pc=None, allowed=None,
               config=None, variables=None, tmp_path=None):
    """Call _should_skip_role with defaults matching a normal project."""
    tmp = tmp_path or Path("/tmp")
    return _should_skip_role(
        role=role,
        source_path=tmp / "agents" / "1-generic" / f"{role}.md",
        provider=provider,
        pc=pc or {"agent_ext": ".md"},
        role_map=_ROLE_MAP,
        allowed_roles=allowed,
        config=config or {},
        variables=variables or {},
        project_root=tmp,
        target_dir=tmp / "claude-agents",
        log=_LogRecorder(),
    )


def _events(log_recorder):
    return log_recorder.events


# ---------------------------------------------------------------------------
# _should_skip_role
# ---------------------------------------------------------------------------

def test_skip_role_not_in_role_map(tmp_path):
    skip, filename = _skip_call(role="unknown-role", tmp_path=tmp_path)
    assert skip is True
    assert filename is None


def test_skip_role_not_in_role_map_logs_claude_only(tmp_path):
    log = _LogRecorder()
    _should_skip_role(
        role="unknown-role",
        source_path=tmp_path / "agents" / "1-generic" / "unknown-role.md",
        provider="Claude",
        pc={"agent_ext": ".md"},
        role_map=_ROLE_MAP,
        allowed_roles=None,
        config={},
        variables={},
        project_root=tmp_path,
        target_dir=tmp_path / "claude-agents",
        log=log,
    )
    assert log.events == [("skip", "unknown-role.md", "role not in ROLE_MAP")]

    log2 = _LogRecorder()
    _should_skip_role(
        role="unknown-role",
        source_path=tmp_path / "agents" / "1-generic" / "unknown-role.md",
        provider="Opencode",
        pc={"agent_ext": ".md"},
        role_map=_ROLE_MAP,
        allowed_roles=None,
        config={},
        variables={},
        project_root=tmp_path,
        target_dir=tmp_path / "claude-agents",
        log=log2,
    )
    assert log2.events == []


def test_skip_role_not_in_allowed_roles(tmp_path):
    log = _LogRecorder()
    skip, filename = _should_skip_role(
        role="developer",
        source_path=tmp_path / "agents" / "1-generic" / "developer.md",
        provider="Claude",
        pc={"agent_ext": ".md"},
        role_map=_ROLE_MAP,
        allowed_roles={"tester"},
        config={},
        variables={},
        project_root=tmp_path,
        target_dir=tmp_path / "claude-agents",
        log=log,
    )
    assert skip is True
    assert filename == "developer.md"
    assert log.events == [(
        "skip", "claude-agents/developer.md",
        "role 'developer' not in config['roles']",
    )]


def test_skip_knowledge_role_disabled_by_default(tmp_path):
    # knowledge- roles are disabled unless knowledge-engine.enabled is true
    skip, filename = _skip_call(role="knowledge-gardener", tmp_path=tmp_path)
    assert skip is True
    assert filename == "knowledge-gardener.md"


def test_knowledge_role_log_message(tmp_path):
    log = _LogRecorder()
    _should_skip_role(
        role="knowledge-gardener",
        source_path=tmp_path / "agents" / "1-generic" / "knowledge-gardener.md",
        provider="Claude",
        pc={"agent_ext": ".md"},
        role_map=_ROLE_MAP,
        allowed_roles=None,
        config={},
        variables={},
        project_root=tmp_path,
        target_dir=tmp_path / "claude-agents",
        log=log,
    )
    assert log.events == [("skip", "claude-agents/knowledge-gardener.md",
                           "knowledge-engine is disabled")]


def test_se_role_log_message_when_disabled(tmp_path):
    log = _LogRecorder()
    _should_skip_role(
        role="se-architect",
        source_path=tmp_path / "agents" / "1-generic" / "se-architect.md",
        provider="Claude",
        pc={"agent_ext": ".md"},
        role_map=_ROLE_MAP,
        allowed_roles=None,
        config={"systems-engineering": {"enabled": False}},
        variables={},
        project_root=tmp_path,
        target_dir=tmp_path / "claude-agents",
        log=log,
    )
    assert log.events == [("skip", "claude-agents/se-architect.md",
                           "systems-engineering is disabled")]


def test_enabled_engines_do_not_skip(tmp_path):
    config = {
        "knowledge-engine": {"enabled": True},
        "systems-engineering": {"enabled": True},
    }
    skip_ke, _ = _skip_call(role="knowledge-gardener", config=config, tmp_path=tmp_path)
    skip_se, _ = _skip_call(role="se-architect", config=config, tmp_path=tmp_path)
    assert (skip_ke, skip_se) == (False, False)


def test_orchestrator_skipped_in_main_chat_mode(tmp_path):
    log = _LogRecorder()
    skip, filename = _should_skip_role(
        role="orchestrator",
        source_path=tmp_path / "agents" / "1-generic" / "orchestrator.md",
        provider="Claude",
        pc={"agent_ext": ".md"},
        role_map=_ROLE_MAP,
        allowed_roles=None,
        config={},
        variables={"ORCH_MODE_MAIN_CHAT": "true"},
        project_root=tmp_path,
        target_dir=tmp_path / "claude-agents",
        log=log,
    )
    assert skip is True
    assert filename == "orchestrator.md"
    assert log.events == [("skip", "claude-agents/orchestrator.md",
                           "orchestrator skipped — ORCH_MODE_MAIN_CHAT active")]


def test_orchestrator_synced_outside_main_chat_mode(tmp_path):
    skip, filename = _skip_call(role="orchestrator", tmp_path=tmp_path)
    assert (skip, filename) == (False, "orchestrator.md")


def test_happy_path_no_skip_and_no_log(tmp_path):
    log = _LogRecorder()
    skip, filename = _skip_call(tmp_path=tmp_path)
    assert (skip, filename) == (False, "developer.md")
    assert log.events == []


def test_target_filename_uses_provider_agent_ext(tmp_path):
    skip, filename = _skip_call(pc={"agent_ext": ".toml"}, tmp_path=tmp_path)
    assert (skip, filename) == (False, "developer.toml")


# ---------------------------------------------------------------------------
# _cleanup_stale_agents
# ---------------------------------------------------------------------------

def _write_managed_index(target_dir, names):
    (target_dir / ".agent-meta-managed").write_text(
        "\n".join(names) + "\n", encoding="utf-8")


def _read_managed_index(target_dir):
    return (target_dir / ".agent-meta-managed").read_text(encoding="utf-8")


def test_stale_managed_file_deleted_and_index_rewritten(tmp_path):
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "developer.md").write_text("keep", encoding="utf-8")
    (target_dir / "stale-old.md").write_text("stale", encoding="utf-8")
    (target_dir / "untracked-x.md").write_text("foreign", encoding="utf-8")
    _write_managed_index(target_dir, ["developer.md", "stale-old.md"])

    log = _LogRecorder()
    _cleanup_stale_agents(target_dir, {"developer.md"}, {"agent_ext": ".md"},
                          tmp_path, False, log)

    # managed + no longer expected → DELETE; unmanaged → kept; expected → kept
    assert (target_dir / "developer.md").exists()
    assert not (target_dir / "stale-old.md").exists()
    assert (target_dir / "untracked-x.md").exists()
    assert log.events == [("action", "DELETE", "agents/stale-old.md",
                           "role removed from config")]
    # managed index rewritten to the sorted expected set
    assert _read_managed_index(target_dir) == "developer.md\n"


def test_dry_run_logs_delete_but_keeps_files_and_index(tmp_path):
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "stale-old.md").write_text("stale", encoding="utf-8")
    _write_managed_index(target_dir, ["stale-old.md"])

    log = _LogRecorder()
    _cleanup_stale_agents(target_dir, set(), {"agent_ext": ".md"},
                          tmp_path, True, log)

    assert (target_dir / "stale-old.md").exists()
    assert log.events == [("action", "DELETE", "agents/stale-old.md",
                           "role removed from config")]
    # index write requires (not dry_run and expected_filenames)
    assert _read_managed_index(target_dir) == "stale-old.md\n"


def test_empty_expected_filenames_never_rewrites_index(tmp_path):
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    _write_managed_index(target_dir, ["old.md"])

    log = _LogRecorder()
    _cleanup_stale_agents(target_dir, set(), {"agent_ext": ".md"},
                          tmp_path, False, log)

    assert _read_managed_index(target_dir) == "old.md\n"


def test_no_managed_index_prunes_everything_unexpected(tmp_path):
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "developer.md").write_text("keep", encoding="utf-8")
    (target_dir / "stale-a.md").write_text("a", encoding="utf-8")
    (target_dir / "stale-b.md").write_text("b", encoding="utf-8")

    log = _LogRecorder()
    _cleanup_stale_agents(target_dir, {"developer.md"}, {"agent_ext": ".md"},
                          tmp_path, False, log)

    assert (target_dir / "developer.md").exists()
    assert not (target_dir / "stale-a.md").exists()
    assert not (target_dir / "stale-b.md").exists()
    # DELETE log order follows the sorted candidate iteration
    assert [e[2] for e in log.events] == ["agents/stale-a.md", "agents/stale-b.md"]


def test_stale_detection_is_ext_aware(tmp_path):
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "developer.md").write_text("keep", encoding="utf-8")
    (target_dir / "codex-agent.toml").write_text("keep", encoding="utf-8")
    (target_dir / "leftover.toml").write_text("stale", encoding="utf-8")

    log = _LogRecorder()
    _cleanup_stale_agents(target_dir, {"developer.md", "codex-agent.toml"},
                          {"agent_ext": ".toml"}, tmp_path, False, log)

    assert (target_dir / "codex-agent.toml").exists()
    assert not (target_dir / "leftover.toml").exists()
    assert [e[2] for e in log.events] == ["agents/leftover.toml"]


def test_missing_target_dir_is_a_noop(tmp_path):
    log = _LogRecorder()
    _cleanup_stale_agents(tmp_path / "does-not-exist", set(),
                          {"agent_ext": ".md"}, tmp_path, False, log)
    assert log.events == []
