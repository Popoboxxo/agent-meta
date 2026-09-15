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

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.agent_sync import (
    _agent_has_provenance,
    _agent_provenance_is_external_skill,
    _cleanup_stale_agents,
    _collect_active_skill_wrapper_filenames,
    _collect_all_registry_wrapper_filenames,
    _should_skip_role,
    plan_agent_cleanup,
    sync_agents_for_provider,
)
from lib.log import SyncLog
from lib.providers import load_providers_config
  # noqa: E402


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

# Issue #735: the verbose skip/note logging is now capability-gated instead of
# provider-name gated. Claude declares `verbose-sync-log`; Opencode does not.
_CLAUDE_PC = {"agent_ext": ".md", "capabilities": ["verbose-sync-log"]}
_NO_LOG_PC = {"agent_ext": ".md"}

# A provider entry WITHOUT the `external-skill-agent-files` capability: the
# wrapper union must not depend on it (IC-03 / issue #735).
_PROVIDER = "Opencode"
_CLEANUP_PC = {"agent_ext": ".md"}


def _cleanup(target_dir, expected, project_root, log, dry_run=False,
             provider=_PROVIDER, pc=None, wrappers=None):
    """Call ``_cleanup_stale_agents`` with the Task-2 signature and defaults."""
    _cleanup_stale_agents(
        target_dir, expected, provider, wrappers if wrappers is not None else set(),
        pc if pc is not None else _CLEANUP_PC, project_root, dry_run, log)


def _write_skill_registry(agent_meta_root, skill_yaml):
    """Write a minimal ``config/skills-registry.yaml`` under *agent_meta_root*."""
    path = agent_meta_root / "config" / "skills-registry.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(skill_yaml, encoding="utf-8")


def _skip_call(provider="Claude", role="developer", pc=None, allowed=None,
               config=None, variables=None, tmp_path=None):
    """Call _should_skip_role with defaults matching a normal project."""
    tmp = tmp_path or Path("/tmp")
    return _should_skip_role(
        role=role,
        source_path=tmp / "agents" / "1-generic" / f"{role}.md",
        provider=provider,
        pc=pc or _CLAUDE_PC,
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
        pc=_CLAUDE_PC,
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
        pc=_NO_LOG_PC,
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
        pc=_CLAUDE_PC,
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
        pc=_CLAUDE_PC,
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
        pc=_CLAUDE_PC,
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
        pc=_CLAUDE_PC,
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
    """AC-01: index-tracked stale file is deleted (backup-first) and the index
    is rewritten to exactly the expected set; an untracked non-provenance file
    survives."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "developer.md").write_text("keep", encoding="utf-8")
    (target_dir / "stale-old.md").write_text("stale", encoding="utf-8")
    (target_dir / "untracked-x.md").write_text("foreign", encoding="utf-8")
    _write_managed_index(target_dir, ["developer.md", "stale-old.md"])

    log = _LogRecorder()
    _cleanup(target_dir, {"developer.md"}, tmp_path, log)

    assert (target_dir / "developer.md").exists()
    assert not (target_dir / "stale-old.md").exists()
    assert (target_dir / "untracked-x.md").exists()
    assert log.events == [("action", "DELETE", "agents/stale-old.md",
                           "role removed from config")]
    assert _read_managed_index(target_dir) == "developer.md\n"
    backups = list(target_dir.glob("stale-old.md.sync-backup-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "stale"



def test_dry_run_logs_delete_but_keeps_files_and_index(tmp_path):
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "stale-old.md").write_text("stale", encoding="utf-8")
    _write_managed_index(target_dir, ["stale-old.md"])

    log = _LogRecorder()
    _cleanup(target_dir, set(), tmp_path, log, dry_run=True)

    assert (target_dir / "stale-old.md").exists()
    assert log.events == [("action", "DELETE", "agents/stale-old.md",
                           "role removed from config")]
    assert _read_managed_index(target_dir) == "stale-old.md\n"
    assert list(target_dir.glob("stale-old.md.sync-backup-*")) == []


def test_index_rewritten_when_expected_equals_previous(tmp_path):
    """AC-02: a non-empty index equal to the expected set is rewritten, nothing
    is deleted (distinct from AC-04's empty case)."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "developer.md").write_text("keep", encoding="utf-8")
    _write_managed_index(target_dir, ["developer.md"])

    log = _LogRecorder()
    _cleanup(target_dir, {"developer.md"}, tmp_path, log)

    assert (target_dir / "developer.md").exists()
    assert log.events == []
    assert _read_managed_index(target_dir) == "developer.md\n"


def test_empty_expected_filenames_writes_empty_index(tmp_path):
    """AC-04: ``expected_filenames == set()`` deletes index-listed files and
    rewrites the index to 0 bytes (replaces the old never-rewrite contract)."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "old.md").write_text("stale", encoding="utf-8")
    _write_managed_index(target_dir, ["old.md"])

    log = _LogRecorder()
    _cleanup(target_dir, set(), tmp_path, log)

    assert not (target_dir / "old.md").exists()
    assert _read_managed_index(target_dir) == ""


def test_no_managed_index_prunes_only_provenance_files(tmp_path):
    """AC-03: no index ⇒ fail-closed provenance bootstrap — a marker-less
    unexpected file survives, a provenance-carrying one is deleted and logged
    (replaces the former fail-open "delete everything unexpected")."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "managed.md").write_text(
        "---\nname: managed\nversion: \"1.0.0\"\n"
        "generated-from: 1-generic/developer.md@1.0.0\n---\nbody\n",
        encoding="utf-8")
    (target_dir / "user-own.md").write_text("hand-authored\n", encoding="utf-8")

    entries = plan_agent_cleanup(
        target_dir, set(), _PROVIDER, set(), _CLEANUP_PC, tmp_path)
    assert [(e.path, e.reason, e.tracked, e.adopted) for e in entries] == [
        ("agents/managed.md", "role removed from config", False, False)]

    log = _LogRecorder()
    _cleanup(target_dir, set(), tmp_path, log)

    assert not (target_dir / "managed.md").exists()
    assert (target_dir / "user-own.md").exists()
    assert log.events == [("action", "DELETE", "agents/managed.md",
                           "role removed from config")]


def test_corrupt_index_warns_and_deletes_only_provenance(tmp_path):
    """AC-05: an unreadable index warns once and falls back to predicate
    bootstrap — only provenance-carrying files are deleted."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / ".agent-meta-managed").write_bytes(b"\xff\xfe not utf-8\n")
    (target_dir / "managed.md").write_text(
        "---\ngenerated-from: 1-generic/developer.md@1.0.0\n---\n",
        encoding="utf-8")
    (target_dir / "plain.md").write_text("hand-authored\n", encoding="utf-8")

    log = _LogRecorder()
    _cleanup(target_dir, set(), tmp_path, log)

    assert not (target_dir / "managed.md").exists()
    assert (target_dir / "plain.md").exists()
    assert any(e[0] == "warning" for e in log.events)
    assert [e[2] for e in log.events if e[0] == "action"] == ["agents/managed.md"]


def test_stale_detection_is_ext_aware(tmp_path):
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "developer.md").write_text("keep", encoding="utf-8")
    (target_dir / "codex-agent.toml").write_text("keep", encoding="utf-8")
    (target_dir / "leftover.toml").write_text("stale", encoding="utf-8")
    _write_managed_index(target_dir, ["codex-agent.toml", "leftover.toml"])

    log = _LogRecorder()
    _cleanup(target_dir, {"developer.md", "codex-agent.toml"}, tmp_path, log,
             pc={"agent_ext": ".toml"})

    assert (target_dir / "codex-agent.toml").exists()
    assert not (target_dir / "leftover.toml").exists()
    assert [e[2] for e in log.events] == ["agents/leftover.toml"]


def test_missing_target_dir_is_a_noop(tmp_path):
    log = _LogRecorder()
    _cleanup(tmp_path / "does-not-exist", set(), tmp_path, log)
    assert log.events == []


def test_foreign_file_never_deleted_backed_up_or_rewritten(tmp_path):
    """AC-15: an index-unlisted, marker-less file is foreign — never deleted,
    never backed up and never rewritten."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    foreign = target_dir / "user-notes.md"
    foreign.write_text("hand-authored\n", encoding="utf-8")
    _write_managed_index(target_dir, ["developer.md"])

    log = _LogRecorder()
    _cleanup(target_dir, {"developer.md"}, tmp_path, log)

    assert foreign.exists()
    assert foreign.read_text(encoding="utf-8") == "hand-authored\n"
    assert _read_managed_index(target_dir) == "developer.md\n"
    assert log.events == []
    assert list(target_dir.glob("user-notes.md.sync-backup-*")) == []


def test_markerless_and_based_only_files_are_foreign(tmp_path):
    """AC-21 (negative): a marker-less file and a ``based-on:``-only file are
    foreign and survive; ``based-on:`` never drives reconciliation."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "markerless.md").write_text("hand-authored\n", encoding="utf-8")
    (target_dir / "based-only.md").write_text(
        "---\nname: based-only\nbased-on: 1-generic/developer.md@1.0.0\n---\n",
        encoding="utf-8")
    _write_managed_index(target_dir, ["keep.md"])

    assert plan_agent_cleanup(
        target_dir, {"keep.md"}, _PROVIDER, set(), _CLEANUP_PC, tmp_path) == []

    log = _LogRecorder()
    _cleanup(target_dir, {"keep.md"}, tmp_path, log)

    assert (target_dir / "markerless.md").exists()
    assert (target_dir / "based-only.md").exists()
    assert log.events == []


def test_no_index_based_only_file_survives(tmp_path):
    """R-03/AC-21: with **no** readable index, a ``based-on:``-only file is not
    adopted by the provenance bootstrap and is never deleted; a primary-marker
    file is still swept."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "based-only.md").write_text(
        "---\nname: based-only\nbased-on: 1-generic/developer.md@1.0.0\n---\n",
        encoding="utf-8")
    (target_dir / "primary.md").write_text(
        "---\ngenerated-from: 1-generic/developer.md@1.0.0\n---\n",
        encoding="utf-8")

    entries = plan_agent_cleanup(
        target_dir, set(), _PROVIDER, set(), _CLEANUP_PC, tmp_path)
    assert [e.path for e in entries] == ["agents/primary.md"]

    log = _LogRecorder()
    _cleanup(target_dir, set(), tmp_path, log)

    assert (target_dir / "based-only.md").exists()
    assert not (target_dir / "primary.md").exists()
    assert [e[2] for e in log.events if e[0] == "action"] == ["agents/primary.md"]


def test_reconciled_external_skill_wrapper_adopted(tmp_path):
    """AC-21 (F-01): an index-unlisted file with a primary ``0-external/``
    provenance marker is adopted, deleted backup-first and the index is
    unchanged."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    wrapper = target_dir / "legacy-wrapper.md"
    wrapper.write_text(
        "---\ngenerated-from: 0-external/foo@abc123\n---\nbody\n",
        encoding="utf-8")
    (target_dir / "keep.md").write_text("keep", encoding="utf-8")
    _write_managed_index(target_dir, ["keep.md"])

    entries = plan_agent_cleanup(
        target_dir, {"keep.md"}, _PROVIDER, set(), _CLEANUP_PC, tmp_path)
    assert [(e.path, e.reason, e.tracked, e.adopted) for e in entries] == [
        ("agents/legacy-wrapper.md", "skill deactivated", False, True)]

    log = _LogRecorder()
    _cleanup(target_dir, {"keep.md"}, tmp_path, log)

    assert not wrapper.exists()
    assert (target_dir / "keep.md").exists()
    assert _read_managed_index(target_dir) == "keep.md\n"
    backups = list(target_dir.glob("legacy-wrapper.md.sync-backup-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8").endswith("body\n")


def test_index_listed_phantom_deleted_with_restorable_backup(tmp_path):
    """AC-21 (F-07): an index-listed phantom (marker stripped/user-authored) is
    deleted — trust-the-index — and its backup restores the exact content."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    phantom = target_dir / "phantom.md"
    phantom.write_text("user authored phantom\n", encoding="utf-8")
    _write_managed_index(target_dir, ["phantom.md"])

    log = _LogRecorder()
    _cleanup(target_dir, set(), tmp_path, log)

    assert not phantom.exists()
    backups = list(target_dir.glob("phantom.md.sync-backup-*"))
    assert len(backups) == 1
    assert backups[0].read_text(encoding="utf-8") == "user authored phantom\n"


def test_reason_precedence_registry_vs_role(tmp_path):
    """AC-22: a tracked stale wrapper name is "skill deactivated"; a tracked
    stale non-wrapper name is "role removed from config"; both carry the active
    provider and adopted == False."""
    target_dir = tmp_path / "agents"
    target_dir.mkdir()
    (target_dir / "wrapper.md").write_text("x", encoding="utf-8")
    (target_dir / "plain.md").write_text("y", encoding="utf-8")
    _write_managed_index(target_dir, ["wrapper.md", "plain.md"])

    entries = plan_agent_cleanup(
        target_dir, set(), _PROVIDER, {"wrapper.md"}, _CLEANUP_PC, tmp_path)
    by_name = {Path(e.path).name: e for e in entries}

    assert set(by_name) == {"wrapper.md", "plain.md"}
    assert by_name["wrapper.md"].reason == "skill deactivated"
    assert by_name["plain.md"].reason == "role removed from config"
    assert all(e.provider == _PROVIDER for e in entries)
    assert all(e.tracked is True and e.adopted is False for e in entries)


@pytest.mark.parametrize(
    "provider, agents_dir",
    [("Opencode", ".opencode/agents"), ("Gemini", ".gemini/agents")],
)
def test_wrapper_tracked_for_non_capability_provider(tmp_path, provider, agents_dir):
    """AC-06: the wrapper union is unconditional (no
    ``external-skill-agent-files`` capability) — an active skill's wrapper is
    expected and a deactivated one's is swept with provider + reason."""
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_skill_registry(
        agent_meta_root,
        "skills:\n"
        "  foo:\n"
        "    role: foo\n"
        "    enabled-by-default: true\n"
        "  bar:\n"
        "    role: bar\n"
        "    enabled-by-default: false\n",
    )
    target_dir = project_root / agents_dir
    target_dir.mkdir(parents=True)
    (target_dir / "bar.md").write_text(
        "---\ngenerated-from: 0-external/bar@deadbeef\n---\n", encoding="utf-8")
    _write_managed_index(target_dir, ["bar.md"])

    assert _collect_active_skill_wrapper_filenames(
        agent_meta_root, {"roles": []}) == {"foo.md"}
    assert _collect_all_registry_wrapper_filenames(agent_meta_root) == {
        "foo.md", "bar.md"}

    entries = plan_agent_cleanup(
        target_dir, {"foo.md"}, provider, {"foo.md", "bar.md"}, _CLEANUP_PC,
        project_root)
    assert [(e.path, e.provider, e.reason, e.tracked, e.adopted)
            for e in entries] == [
        (f"{agents_dir}/bar.md", provider, "skill deactivated", True, False)]

    provider_config = {provider: {"agents_dir": agents_dir, "agent_ext": ".md"}}
    sync_agents_for_provider(
        agent_meta_root, project_root, {"roles": []}, {}, SyncLog(),
        dry_run=False, provider=provider, provider_config=provider_config)

    index = _read_managed_index(target_dir)
    assert "foo.md" in index
    assert "bar.md" not in index
    assert not (target_dir / "bar.md").exists()


def test_deactivated_skill_wrapper_swept_and_index_cleaned(tmp_path):
    """AC-07: a wrapper expected in a prior run and then deactivated is swept by
    the agents cleanup and dropped from the agents index."""
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_skill_registry(
        agent_meta_root,
        "skills:\n"
        "  old:\n"
        "    role: old-skill\n"
        "    enabled-by-default: false\n",
    )
    target_dir = project_root / ".opencode" / "agents"
    target_dir.mkdir(parents=True)
    (target_dir / "old-skill.md").write_text(
        "---\ngenerated-from: 0-external/old@deadbeef\n---\n", encoding="utf-8")
    _write_managed_index(target_dir, ["old-skill.md"])

    provider_config = {"Opencode": {"agents_dir": ".opencode/agents", "agent_ext": ".md"}}
    sync_agents_for_provider(
        agent_meta_root, project_root, {"roles": []}, {}, SyncLog(),
        dry_run=False, provider="Opencode", provider_config=provider_config)

    assert not (target_dir / "old-skill.md").exists()
    assert _read_managed_index(target_dir) == ""


def test_no_fail_open_managed_index_clause_in_agent_sync():
    """AC-24 (agent_sync clause): the fail-open
    ``not managed_index.exists() or …`` delete clause is gone."""
    source = (_REPO_ROOT / "scripts" / "lib" / "agent_sync.py").read_text(
        encoding="utf-8")
    assert "not managed_index.exists() or" not in source


def test_provenance_marker_forms_recognised(tmp_path):
    """IC-02/R-03: only **primary** marker forms are recognised by
    ``_agent_has_provenance``; the secondary ``based-on:`` is not a bootstrap
    provenance signal and only primary ``0-external/`` origins satisfy
    ``_agent_provenance_is_external_skill``."""
    fm = tmp_path / "a.md"
    toml = tmp_path / "b.toml"
    comment = tmp_path / "c.md"
    based = tmp_path / "d.md"
    none = tmp_path / "e.md"

    assert _agent_has_provenance(fm, "---\ngenerated-from: 1-generic/x.md@1\n---\n")
    assert _agent_has_provenance(toml, "# generated-from: 1-generic/x.md@1\n")
    assert _agent_has_provenance(comment, "<!-- agent-meta-provenance: generated-from=1-generic/x.md@1 -->\n")
    assert not _agent_has_provenance(based, "---\nbased-on: 1-generic/x.md@1\n---\n")
    assert not _agent_has_provenance(none, "hand-authored\n")

    assert _agent_provenance_is_external_skill(
        fm, "---\ngenerated-from: 0-external/foo@abc\n---\n")
    assert _agent_provenance_is_external_skill(
        toml, "# generated-from: 0-external/foo@abc\n")
    assert _agent_provenance_is_external_skill(
        comment, "<!-- agent-meta-provenance: generated-from=0-external/foo@abc -->\n")
    assert not _agent_provenance_is_external_skill(
        fm, "---\ngenerated-from: 1-generic/x.md@1\n---\n")
    assert not _agent_provenance_is_external_skill(
        based, "---\nbased-on: 0-external/foo@abc\n---\n")


def test_ac19_removed_role_backup_restore_and_resync(tmp_path):
    """AC-19 (rollback): removing a role from ``project.yaml → roles`` deletes
    its generated agent file backup-first, the ``.sync-backup-<ts>`` sibling
    restores the exact pre-delete content, and re-adding the role re-syncs it
    deterministically byte-for-byte."""
    agent_meta_root = _REPO_ROOT
    project_root = tmp_path / "project"
    project_root.mkdir()
    agents_dir = project_root / ".claude" / "agents"
    provider_config = load_providers_config(agent_meta_root)
    variables = {"PROJECT_NAME": "ac19"}
    with_developer = {"roles": ["developer", "git"], "project": {"name": "ac19"}}
    without_developer = {"roles": ["git"], "project": {"name": "ac19"}}

    def _sync(config):
        sync_agents_for_provider(
            agent_meta_root, project_root, config, variables, SyncLog(),
            dry_run=False, provider="Claude", provider_config=provider_config)

    # Generated role file exists and is byte-deterministic across re-syncs.
    _sync(with_developer)
    agent_path = agents_dir / "developer.md"
    assert agent_path.exists()
    original = agent_path.read_bytes()

    # Role removed from the config → generated file removed, backup-first.
    _sync(without_developer)
    assert not agent_path.exists()
    backups = list(agents_dir.glob("developer.md.sync-backup-*"))
    assert len(backups) == 1
    assert backups[0].read_bytes() == original
    assert _read_managed_index(agents_dir) == "git.md\n"

    # Role re-added → deterministic regeneration of the exact same content.
    _sync(with_developer)
    assert agent_path.exists()
    assert agent_path.read_bytes() == original

    # The backup sibling restores the deleted file's pre-delete content.
    agent_path.unlink()
    backups = list(agents_dir.glob("developer.md.sync-backup-*"))
    assert len(backups) == 1
    backups[0].rename(agent_path)
    assert agent_path.read_bytes() == original

