"""Path-migration + idempotency regression tests for
SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30 (Task 11).

Acceptance anchors: AC-22 (path migration with backup + rollback + user-file
guard), AC-3a (a clean scratch sync leaves ``--check`` at rc 0), AC-4
(run1 == run2 byte-identity) and AC-18 (managed-block-scoped ``--check``).

Two layers are covered:

1. **Unit layer** — the provider-agnostic primitives in
   ``scripts/lib/generated_file_drift.py`` (managed-artifact detection,
   backup-first managed delete, the ordered write-new -> verify -> backup-old
   -> remove-old migration and the final-content diff) plus the discovery
   path resolution in ``scripts/lib/sync_pipeline.py``. Dispatch is proven to
   depend only on the provider-neutral ``agent-discovery`` bool + the presence
   of the ``discovery`` sub-map, never on a provider name.
2. **Integration layer** — the real ``scripts/sync.py`` CLI against a scratch
   project: run1 == run2, ``--check`` rc 0 after a clean sync, an in-block edit
   rc 1 and an out-of-block edit rc 0.
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

_MANAGED_BEGIN = "<!-- agent-meta:managed-begin -->"
_MANAGED_END = "<!-- agent-meta:managed-end -->"
_MANAGED_BLOCK_RE = re.compile(
    r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
    re.DOTALL,
)


def _managed(body: str = "generated body") -> str:
    return f"{_MANAGED_BEGIN}\n{body}\n{_MANAGED_END}\n"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _backups_of(path: Path) -> list[Path]:
    return sorted(path.parent.glob(f"{path.name}.sync-backup-*"))


# --------------------------------------------------------------------------
# Discovery path resolution (config-data dispatch, no provider name)
# --------------------------------------------------------------------------


def _gemini_like_config() -> dict:
    """A synthetic provider entry shaped like an opt-in discovery provider."""
    return {
        "agents_dir": ".gemini/agents",
        "rules_dir": ".gemini/rules",
        "skills_dir": ".gemini/skills",
        "mcp-config": {"committed-file": ".gemini/settings.json", "format": "gemini-settings"},
        "agent-discovery": True,
        "discovery": {
            "agents_dir": ".agents/agents",
            "rules_dir": ".agents/rules",
            "skills_dir": ".agents/skills",
            "mcp-config": {
                "committed-file": ".agents/mcp_config.json",
                "format": "antigravity-mcp-json",
            },
        },
    }


def test_resolve_discovery_paths_overlays_when_enabled():
    from lib.sync_pipeline import resolve_discovery_paths

    resolved = resolve_discovery_paths(_gemini_like_config())

    assert resolved["agents_dir"] == ".agents/agents"
    assert resolved["rules_dir"] == ".agents/rules"
    assert resolved["skills_dir"] == ".agents/skills"
    assert resolved["mcp-config"]["committed-file"] == ".agents/mcp_config.json"
    assert resolved["mcp-config"]["format"] == "antigravity-mcp-json"


def test_resolve_discovery_paths_keeps_top_level_when_disabled():
    from lib.sync_pipeline import resolve_discovery_paths

    pc = _gemini_like_config()
    pc["agent-discovery"] = False

    resolved = resolve_discovery_paths(pc)

    assert resolved["agents_dir"] == ".gemini/agents"
    assert resolved["rules_dir"] == ".gemini/rules"
    assert resolved["skills_dir"] == ".gemini/skills"
    assert resolved["mcp-config"]["committed-file"] == ".gemini/settings.json"


def test_resolve_discovery_paths_keeps_top_level_without_discovery_map():
    from lib.sync_pipeline import resolve_discovery_paths

    pc = _gemini_like_config()
    del pc["discovery"]

    resolved = resolve_discovery_paths(pc)

    assert resolved["agents_dir"] == ".gemini/agents"
    assert resolved["mcp-config"]["committed-file"] == ".gemini/settings.json"


def test_resolve_discovery_paths_does_not_mutate_input():
    from lib.sync_pipeline import resolve_discovery_paths

    pc = _gemini_like_config()
    resolve_discovery_paths(pc)

    assert pc["agents_dir"] == ".gemini/agents"
    assert pc["mcp-config"]["committed-file"] == ".gemini/settings.json"


def test_resolve_discovery_paths_returns_input_object_when_disabled():
    """F5: the disabled path returns the identical input, not a fresh copy."""
    from lib.sync_pipeline import resolve_discovery_paths

    pc = _gemini_like_config()
    pc["agent-discovery"] = False

    assert resolve_discovery_paths(pc) is pc


# --------------------------------------------------------------------------
# Managed-artifact detection
# --------------------------------------------------------------------------


def test_is_managed_artifact_by_marker(tmp_path: Path):
    from lib.generated_file_drift import is_managed_artifact

    managed = tmp_path / "generated.md"
    managed.write_text(_managed(), encoding="utf-8")
    user = tmp_path / "user.md"
    user.write_text("hand written, no marker\n", encoding="utf-8")

    assert is_managed_artifact(managed) is True
    assert is_managed_artifact(user) is False


def test_is_managed_artifact_by_index(tmp_path: Path):
    from lib.generated_file_drift import is_managed_artifact

    target = tmp_path / "listed.md"
    target.write_text("no in-file marker but tracked in the index\n", encoding="utf-8")
    (tmp_path / ".agent-meta-managed").write_text("listed.md\n", encoding="utf-8")

    assert is_managed_artifact(target) is True


def test_is_managed_artifact_missing_file_is_false(tmp_path: Path):
    from lib.generated_file_drift import is_managed_artifact

    assert is_managed_artifact(tmp_path / "nope.md") is False


# --------------------------------------------------------------------------
# Ordered migration: write-new -> verify -> backup-old -> remove-old
# --------------------------------------------------------------------------


def test_migrate_managed_artifact_backup_rollback(tmp_path: Path):
    from lib.generated_file_drift import migrate_managed_artifact
    from lib.log import SyncLog

    old = tmp_path / "old" / "agent.md"
    old.parent.mkdir(parents=True)
    old.write_text(_managed("payload-v1"), encoding="utf-8")
    new = tmp_path / "new" / "agent.md"

    result = migrate_managed_artifact(old, new, tmp_path, SyncLog(), ts="20260101-000000")

    assert result["status"] == "migrated"
    assert new.is_file()
    assert new.read_bytes() == _managed("payload-v1").encode("utf-8")
    assert not old.exists()

    backups = _backups_of(old)
    assert len(backups) == 1
    assert backups[0].read_bytes() == _managed("payload-v1").encode("utf-8")
    assert result["backup"] == backups[0].relative_to(tmp_path).as_posix()

    # Rollback: renaming the backup sibling restores the pre-migration file.
    backups[0].rename(old)
    assert old.read_bytes() == _managed("payload-v1").encode("utf-8")


def test_migrate_managed_artifact_never_deletes_user_file(tmp_path: Path):
    from lib.generated_file_drift import migrate_managed_artifact
    from lib.log import SyncLog

    old = tmp_path / "old" / "user.md"
    old.parent.mkdir(parents=True)
    old.write_text("hand authored\n", encoding="utf-8")
    new = tmp_path / "new" / "user.md"

    result = migrate_managed_artifact(old, new, tmp_path, SyncLog(), ts="20260101-000000")

    assert result["status"] == "user-authored"
    assert old.is_file()
    assert old.read_text(encoding="utf-8") == "hand authored\n"
    assert not new.exists()
    assert _backups_of(old) == []


def test_migrate_managed_artifact_verify_failure_keeps_old(tmp_path: Path):
    from lib.generated_file_drift import migrate_managed_artifact
    from lib.log import SyncLog

    old = tmp_path / "old" / "agent.md"
    old.parent.mkdir(parents=True)
    old.write_text(_managed("payload-v1"), encoding="utf-8")
    new = tmp_path / "new" / "agent.md"

    result = migrate_managed_artifact(
        old, new, tmp_path, SyncLog(), verify=lambda _p: False, ts="20260101-000000"
    )

    assert result["status"] == "verify-failed"
    assert old.is_file()
    assert _backups_of(old) == []


def test_migrate_managed_artifact_dry_run_writes_nothing(tmp_path: Path):
    from lib.generated_file_drift import migrate_managed_artifact
    from lib.log import SyncLog

    old = tmp_path / "old" / "agent.md"
    old.parent.mkdir(parents=True)
    old.write_text(_managed("payload-v1"), encoding="utf-8")
    new = tmp_path / "new" / "agent.md"

    result = migrate_managed_artifact(
        old, new, tmp_path, SyncLog(), dry_run=True, ts="20260101-000000"
    )

    assert result["status"] == "would-migrate"
    assert old.is_file()
    assert not new.exists()
    assert _backups_of(old) == []


def test_remove_managed_artifact_backup_first(tmp_path: Path):
    from lib.generated_file_drift import remove_managed_artifact
    from lib.log import SyncLog

    target = tmp_path / "agents" / "gone.md"
    target.parent.mkdir(parents=True)
    target.write_text(_managed("to be removed"), encoding="utf-8")

    result = remove_managed_artifact(target, tmp_path, SyncLog(), ts="20260101-000000")

    assert result["removed"] is True
    assert not target.exists()
    backups = _backups_of(target)
    assert len(backups) == 1
    assert backups[0].read_bytes() == _managed("to be removed").encode("utf-8")


def test_remove_managed_artifact_keeps_user_file(tmp_path: Path):
    from lib.generated_file_drift import remove_managed_artifact
    from lib.log import SyncLog

    target = tmp_path / "agents" / "user.md"
    target.parent.mkdir(parents=True)
    target.write_text("hand authored\n", encoding="utf-8")

    result = remove_managed_artifact(target, tmp_path, SyncLog(), ts="20260101-000000")

    assert result["removed"] is False
    assert result["reason"] == "user-authored"
    assert target.is_file()
    assert _backups_of(target) == []


def test_remove_managed_artifact_verify_defers_removal(tmp_path: Path):
    """F3/F4: a failing verify predicate keeps the managed file in place."""
    from lib.generated_file_drift import remove_managed_artifact
    from lib.log import SyncLog

    target = tmp_path / "agents" / "gone.md"
    target.parent.mkdir(parents=True)
    target.write_text(_managed("to be removed"), encoding="utf-8")

    result = remove_managed_artifact(
        target, tmp_path, SyncLog(), ts="20260101-000000", verify=lambda _p: False,
    )

    assert result["removed"] is False
    assert result["reason"] == "verify-deferred"
    assert target.is_file()
    assert _backups_of(target) == []


# --------------------------------------------------------------------------
# Discovery migration driver (end-to-end on a temp project)
# --------------------------------------------------------------------------


def test_migrate_discovery_artifacts_moves_managed_and_spares_user(tmp_path: Path):
    from lib.log import SyncLog
    from lib.sync_pipeline import migrate_discovery_artifacts

    old_dir = tmp_path / ".gemini" / "agents"
    old_dir.mkdir(parents=True)
    managed = old_dir / "orchestrator.md"
    managed.write_text(_managed("agent"), encoding="utf-8")
    user = old_dir / "hand-authored.md"
    user.write_text("user content\n", encoding="utf-8")
    (old_dir / ".agent-meta-managed").write_text("orchestrator.md\n", encoding="utf-8")

    pc = _gemini_like_config()
    results = migrate_discovery_artifacts(tmp_path, pc, SyncLog(), ts="20260101-000000")

    new_managed = tmp_path / ".agents" / "agents" / "orchestrator.md"
    assert new_managed.is_file()
    assert new_managed.read_bytes() == _managed("agent").encode("utf-8")
    assert not managed.exists()
    assert len(_backups_of(managed)) == 1

    # The user-authored file is never deleted and never backed up.
    assert user.is_file()
    assert user.read_text(encoding="utf-8") == "user content\n"
    assert _backups_of(user) == []
    assert any(r["status"] == "migrated" for r in results)
    assert any(r["status"] == "user-authored" for r in results)


def test_apply_discovery_migration_resolves_then_migrates(tmp_path: Path):
    """The driver must see the OLD top-level paths while writers get the new ones."""
    from lib.log import SyncLog
    from lib.sync_pipeline import apply_discovery_migration

    old_dir = tmp_path / ".gemini" / "agents"
    old_dir.mkdir(parents=True)
    managed = old_dir / "orchestrator.md"
    managed.write_text(_managed("agent"), encoding="utf-8")

    resolved, results = apply_discovery_migration(
        tmp_path, _gemini_like_config(), SyncLog(), ts="20260101-000000"
    )

    # Writers get the resolved discovery path; the migration still saw the old one.
    assert resolved["agents_dir"] == ".agents/agents"
    assert (tmp_path / ".agents" / "agents" / "orchestrator.md").is_file()
    assert not managed.exists()
    assert [r["status"] for r in results] == ["migrated"]


def test_migrate_discovery_artifacts_noop_when_disabled(tmp_path: Path):
    from lib.log import SyncLog
    from lib.sync_pipeline import migrate_discovery_artifacts

    old_dir = tmp_path / ".gemini" / "agents"
    old_dir.mkdir(parents=True)
    (old_dir / "orchestrator.md").write_text(_managed("agent"), encoding="utf-8")

    pc = _gemini_like_config()
    pc["agent-discovery"] = False
    assert migrate_discovery_artifacts(tmp_path, pc, SyncLog(), ts="20260101-000000") == []
    assert (old_dir / "orchestrator.md").is_file()


def test_migrate_discovery_artifacts_verify_failure_keeps_old(tmp_path: Path):
    """F3: the write-new sequence verifies the new artifact before removal."""
    from lib.log import SyncLog
    from lib.sync_pipeline import migrate_discovery_artifacts

    old_dir = tmp_path / ".gemini" / "agents"
    old_dir.mkdir(parents=True)
    managed = old_dir / "orchestrator.md"
    managed.write_text(_managed("payload-v1"), encoding="utf-8")
    # Pre-existing, malformed new artifact => verify must fail and keep the old file.
    new_dir = tmp_path / ".agents" / "agents"
    new_dir.mkdir(parents=True)
    (new_dir / "orchestrator.md").write_text(
        "---\nkey: [unclosed\n---\nbody\n", encoding="utf-8"
    )

    results = migrate_discovery_artifacts(
        tmp_path, _gemini_like_config(), SyncLog(), ts="20260101-000000",
    )

    assert [r["status"] for r in results] == ["verify-failed"]
    assert managed.is_file()
    assert _backups_of(managed) == []


def test_load_provider_migrations_parses_real_map():
    """F1: the authoritative map is consumed as data (Copilot default-on, Gemini gated)."""
    from lib.generated_file_drift import load_provider_migrations

    migrations = load_provider_migrations(_REPO_ROOT / "config")

    assert migrations["Copilot"]["requires-flag"] is None
    assert [e["remove"] for e in migrations["Copilot"]["removals"]] == [
        ".github/copilot/agents",
        ".github/copilot/rules",
        ".github/copilot/COPILOT.md",
    ]
    assert migrations["Copilot"]["removals"][2]["kind"] == "file"
    assert migrations["Gemini"]["requires-flag"] == "agent-discovery"
    assert [e["remove"] for e in migrations["Gemini"]["removals"]] == [
        ".gemini/agents",
        ".gemini/rules",
        ".gemini/skills",
    ]


def _copilot_old_tree(tmp_path: Path) -> dict[str, Path]:
    """Old Copilot paths: managed files (agents/rules/COPILOT.md) + one user file."""
    agents = tmp_path / ".github" / "copilot" / "agents"
    agents.mkdir(parents=True)
    managed_agent = agents / "orchestrator.agent.md"
    managed_agent.write_text(_managed("copilot agent"), encoding="utf-8")
    user_agent = agents / "hand-authored.md"
    user_agent.write_text("user content\n", encoding="utf-8")
    (agents / ".agent-meta-managed").write_text("orchestrator.agent.md\n", encoding="utf-8")

    rules = tmp_path / ".github" / "copilot" / "rules"
    rules.mkdir(parents=True)
    managed_rule = rules / "rule.md"
    managed_rule.write_text(_managed("copilot rule"), encoding="utf-8")

    adapter = tmp_path / ".github" / "copilot" / "COPILOT.md"
    adapter.write_text(_managed("copilot adapter"), encoding="utf-8")
    return {
        "managed_agent": managed_agent,
        "user_agent": user_agent,
        "managed_rule": managed_rule,
        "adapter": adapter,
    }


def test_migrate_provider_paths_copilot_default_on(tmp_path: Path):
    """F1/AC-22: Copilot migrates with no flag — old managed gone, backup, user kept."""
    from lib.generated_file_drift import load_provider_migrations
    from lib.log import SyncLog
    from lib.sync_pipeline import migrate_provider_paths

    files = _copilot_old_tree(tmp_path)
    migrations = load_provider_migrations(_REPO_ROOT / "config")

    results = migrate_provider_paths(
        tmp_path, "Copilot", {"agent-discovery": False}, SyncLog(),
        ts="20260101-000000", migrations=migrations,
    )

    assert any(r["removed"] for r in results)

    # Old managed artifacts are gone and each has a byte-exact sibling.
    assert not files["managed_agent"].exists()
    agent_backups = _backups_of(files["managed_agent"])
    assert len(agent_backups) == 1
    assert agent_backups[0].read_bytes() == _managed("copilot agent").encode("utf-8")
    assert not files["managed_rule"].exists()
    assert len(_backups_of(files["managed_rule"])) == 1
    assert not files["adapter"].exists()
    adapter_backups = _backups_of(files["adapter"])
    assert len(adapter_backups) == 1
    assert adapter_backups[0].read_bytes() == _managed("copilot adapter").encode("utf-8")

    # User-authored file survives untouched and is never backed up.
    assert files["user_agent"].is_file()
    assert files["user_agent"].read_text(encoding="utf-8") == "user content\n"
    assert _backups_of(files["user_agent"]) == []

    # The old dirs survive only as the root of the rollback siblings / user file;
    # no managed, non-backup artifact is left behind.
    leftover = [
        p for p in (tmp_path / ".github" / "copilot").rglob("*")
        if p.is_file() and not p.name.startswith(".agent-meta-managed")
        and ".sync-backup-" not in p.name
    ]
    assert leftover == [files["user_agent"]]

    # Rollback is a plain rename of the backup sibling.
    agent_backups[0].rename(files["managed_agent"])
    assert files["managed_agent"].read_bytes() == _managed("copilot agent").encode("utf-8")


def test_migrate_provider_paths_requires_flag_off_leaves_paths(tmp_path: Path):
    """F1: the Gemini entry is gated by agent-discovery and must not run when false."""
    from lib.generated_file_drift import load_provider_migrations
    from lib.log import SyncLog
    from lib.sync_pipeline import migrate_provider_paths

    old_dir = tmp_path / ".gemini" / "agents"
    old_dir.mkdir(parents=True)
    managed = old_dir / "orchestrator.md"
    managed.write_text(_managed("gemini agent"), encoding="utf-8")
    migrations = load_provider_migrations(_REPO_ROOT / "config")

    results = migrate_provider_paths(
        tmp_path, "Gemini", {"agent-discovery": False}, SyncLog(),
        ts="20260101-000000", migrations=migrations,
    )

    assert results == []
    assert managed.is_file()
    assert _backups_of(managed) == []


def test_migrate_provider_paths_requires_flag_on_removes(tmp_path: Path):
    """F1: with agent-discovery true the gated entry removes the old managed paths."""
    from lib.generated_file_drift import load_provider_migrations
    from lib.log import SyncLog
    from lib.sync_pipeline import migrate_provider_paths

    old_dir = tmp_path / ".gemini" / "agents"
    old_dir.mkdir(parents=True)
    managed = old_dir / "orchestrator.md"
    managed.write_text(_managed("gemini agent"), encoding="utf-8")
    migrations = load_provider_migrations(_REPO_ROOT / "config")

    results = migrate_provider_paths(
        tmp_path, "Gemini", {"agent-discovery": True}, SyncLog(),
        ts="20260101-000000", migrations=migrations,
    )

    assert any(r["removed"] for r in results)
    assert not managed.exists()
    assert len(_backups_of(managed)) == 1
    # The dir is kept as the rollback root; only the backup sibling remains.
    assert old_dir.is_dir()
    remaining = [p.name for p in old_dir.iterdir()]
    assert all(".sync-backup-" in name for name in remaining)


def test_apply_provider_migrations_iterates_map(tmp_path: Path):
    """F1: the map drives dispatch; inactive providers are not visited."""
    from lib.generated_file_drift import load_provider_migrations
    from lib.log import SyncLog
    from lib.sync_pipeline import apply_provider_migrations

    migrations = load_provider_migrations(_REPO_ROOT / "config")
    outcome = apply_provider_migrations(
        tmp_path, _REPO_ROOT, {"Copilot": {"agent-discovery": False}}, ["Copilot"],
        SyncLog(), ts="20260101-000000", migrations=migrations,
    )

    assert set(outcome) == {"Copilot"}
    assert "Gemini" not in outcome


def test_drop_net_zero_actions_removes_clean_pending(tmp_path: Path):
    """F2: a net-zero (final == on-disk) context write is not a pending change."""
    from lib.log import SyncLog
    from lib.sync_pipeline import _drop_net_zero_actions

    (tmp_path / "AGENTS.md").write_text("stable\n", encoding="utf-8")
    log = SyncLog()
    log.action("UPDATE", "AGENTS.md", "managed block")
    log.action("WRITE", "other.md", "unrelated")

    _drop_net_zero_actions(log, tmp_path, {"AGENTS.md": "stable\n"})

    assert all("AGENTS.md" not in action for action in log.actions)
    assert any("other.md" in action for action in log.actions)


def test_drop_net_zero_actions_keeps_genuinely_changed(tmp_path: Path):
    from lib.log import SyncLog
    from lib.sync_pipeline import _drop_net_zero_actions

    (tmp_path / "AGENTS.md").write_text("old\n", encoding="utf-8")
    log = SyncLog()
    log.action("UPDATE", "AGENTS.md", "managed block")

    _drop_net_zero_actions(log, tmp_path, {"AGENTS.md": "new\n"})

    assert any("AGENTS.md" in action for action in log.actions)


# --------------------------------------------------------------------------
# Final-content diff (net-zero aware pending computation)
# --------------------------------------------------------------------------


def test_final_content_diff_reports_only_net_changes(tmp_path: Path):
    from lib.generated_file_drift import final_content_diff

    (tmp_path / "same.md").write_text("A", encoding="utf-8")
    (tmp_path / "changed.md").write_text("A", encoding="utf-8")

    diff = final_content_diff(
        tmp_path,
        {"same.md": "A", "changed.md": "B", "missing.md": "C"},
    )

    assert diff == ["changed.md", "missing.md"]


def test_final_content_diff_net_zero_is_clean(tmp_path: Path):
    from lib.generated_file_drift import final_content_diff

    (tmp_path / "file.md").write_text("intermediate", encoding="utf-8")

    # Two intermediate writes netting to the original content must report clean.
    assert final_content_diff(tmp_path, {"file.md": "intermediate"}) == []


# --------------------------------------------------------------------------
# Integration: clean scratch sync is idempotent and --check-scoped
# --------------------------------------------------------------------------


def _write_project_yaml(project_root: Path) -> Path:
    meta = project_root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    config = meta / "project.yaml"
    config.write_text(
        "agent-meta-version: 0.101.0\n"
        "ai-providers: [Gemini]\n"
        "dod-preset: rapid-prototyping\n"
        "roles:\n"
        "- orchestrator\n"
        "- developer\n"
        "- git\n"
        "project:\n"
        "  name: migration-paths\n"
        "  prefix: mp\n"
        "  short: migration-paths\n"
        "variables:\n"
        "  PROJECT_NAME: migration-paths\n"
        "  PROJECT_DESCRIPTION: Path-migration + idempotency fixture.\n"
        "  PROJECT_GOAL: Prove run1 == run2 and --check scoping.\n"
        "  GIT_PLATFORM: GitHub\n"
        "  GIT_REMOTE_URL: https://github.com/example/migration-paths\n"
        "  GIT_MAIN_BRANCH: main\n"
        "rules-preset: default\n"
        "speech-mode: full\n"
        "tier-preset: Normal\n"
        "max-parallel-agents: 2\n"
        "conventions-preset: default\n",
        encoding="utf-8",
    )
    return config


def _run_sync(project_root: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(_SYNC_PY),
            "--config",
            str(project_root / ".meta-config" / "project.yaml"),
            *extra_args,
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        timeout=180,
        check=False,
    )


def test_clean_scratch_sync_is_idempotent_and_check_scoped(tmp_path: Path):
    project_root = tmp_path / "project"
    _write_project_yaml(project_root)

    first = _run_sync(project_root)
    assert first.returncode == 0, first.stderr

    context_file = project_root / "AGENTS.md"
    assert context_file.is_file()
    run1 = _sha(context_file)

    second = _run_sync(project_root)
    assert second.returncode == 0, second.stderr
    asserts_second = _run_sync(project_root, "--check")
    assert asserts_second.returncode == 0, asserts_second.stderr
    assert _sha(context_file) == run1

    original = context_file.read_text(encoding="utf-8")

    # Edit inside the managed block -> --check rc 1.
    inside = _MANAGED_BLOCK_RE.sub(
        lambda m: m.group(0).replace("-->", "--> <!-- inside-edit -->", 1),
        original,
        count=1,
    )
    assert inside != original
    context_file.write_text(inside, encoding="utf-8")
    check_inside = _run_sync(project_root, "--check")
    assert check_inside.returncode == 1, check_inside.stdout + check_inside.stderr

    # Edit outside every managed block -> --check rc 0.
    context_file.write_text(original + "\n<!-- user note outside -->\n", encoding="utf-8")
    check_outside = _run_sync(project_root, "--check")
    assert check_outside.returncode == 0, check_outside.stdout + check_outside.stderr
