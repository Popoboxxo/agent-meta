"""Tests for external skills management."""

from pathlib import Path

from scripts.lib.log import SyncLog
from scripts.lib.skills import (
    _read_skills_managed_index,
    _write_skills_managed_index,
    sync_external_skills_for_provider,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_read_skills_managed_index_missing_file_returns_empty(tmp_path):
    assert _read_skills_managed_index(tmp_path / ".claude" / "skills") == set()


def test_write_then_read_skills_managed_index_roundtrip(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"reqogniloom-change-manager", "graphify"}, dry_run=False)
    assert _read_skills_managed_index(skills_dir) == {"reqogniloom-change-manager", "graphify"}


def test_write_skills_managed_index_dry_run_does_not_write(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"graphify"}, dry_run=True)
    assert not (skills_dir / ".agent-meta-managed").exists()


# ---------------------------------------------------------------------------
# universe= merge mode — two independent writers share the same index file
# (external-skill sync vs. rules.py's 'channel: skill' lazy-rules mechanism).
# ---------------------------------------------------------------------------

def test_write_skills_managed_index_merge_preserves_other_callers_entries(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    # Caller A (e.g. rules.py) writes its own entries first, full-replace mode.
    _write_skills_managed_index(skills_dir, {"sync-interface"}, dry_run=False)
    # Caller B (external-skill sync) writes in merge mode, scoped to its own
    # universe of possible skill names — must not wipe out caller A's entry.
    _write_skills_managed_index(
        skills_dir, {"graphify"}, dry_run=False, universe={"graphify", "reqogniloom-change-manager"}
    )
    assert _read_skills_managed_index(skills_dir) == {"sync-interface", "graphify"}


def test_write_skills_managed_index_merge_removes_only_stale_entries_within_universe(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"sync-interface"}, dry_run=False)
    _write_skills_managed_index(
        skills_dir, {"graphify"}, dry_run=False, universe={"graphify", "reqogniloom-change-manager"}
    )
    # graphify is deactivated (falls out of now_managed) but "reqogniloom-
    # change-manager" was never present, and "sync-interface" belongs to a
    # different universe entirely — only graphify should ever leave.
    _write_skills_managed_index(
        skills_dir, set(), dry_run=False, universe={"graphify", "reqogniloom-change-manager"}
    )
    assert _read_skills_managed_index(skills_dir) == {"sync-interface"}


def test_write_skills_managed_index_merge_empty_result_removes_file(tmp_path):
    skills_dir = tmp_path / ".claude" / "skills"
    _write_skills_managed_index(skills_dir, {"graphify"}, dry_run=False, universe={"graphify"})
    assert (skills_dir / ".agent-meta-managed").exists()
    _write_skills_managed_index(skills_dir, set(), dry_run=False, universe={"graphify"})
    assert not (skills_dir / ".agent-meta-managed").exists()


def _write_skill_fixture(tmp_path: Path, monkeypatch) -> tuple[Path, Path]:
    """agent-meta root with a local fake skill repo + a wrapper template.

    ``ensure_skill_repo``/``get_skill_commit`` are stubbed so the test never
    touches the network or spawns git — the source tree is created directly
    under project_root (the "project admin" resolution path).
    """
    from scripts.lib import skills as skills_mod

    monkeypatch.setattr(skills_mod, "ensure_skill_repo", lambda *a, **k: None)
    monkeypatch.setattr(skills_mod, "get_skill_commit", lambda *a, **k: "abc1234")

    agent_meta_root = tmp_path / "agent-meta"
    (agent_meta_root / "config").mkdir(parents=True)
    (agent_meta_root / "config" / "skills-registry.yaml").write_text(
        "repos:\n"
        "  fake-repo:\n"
        "    repo: https://example.invalid/fake\n"
        "    local_path: external/fake-repo\n"
        "skills:\n"
        "  fake-skill:\n"
        "    approved: true\n"
        "    enabled-by-default: true\n"
        "    repo: fake-repo\n"
        "    source: skills/fake\n"
        "    entry: SKILL.md\n"
        "    role: fake-role\n"
        "    name: Fake Skill\n"
        "    description: A fake external skill.\n"
        "    additional_files:\n"
        "      - reference.md\n",
        encoding="utf-8",
    )
    (agent_meta_root / "agents" / "0-external").mkdir(parents=True)
    (agent_meta_root / "agents" / "0-external" / "_skill-wrapper.md").write_text(
        (_REPO_ROOT / "agents" / "0-external" / "_skill-wrapper.md").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    project_root = tmp_path / "project"
    project_root.mkdir()
    # agent_meta_root != project_root → repo_dir resolves under
    # project_root/local_path.
    source_dir = project_root / "external" / "fake-repo" / "skills" / "fake"
    source_dir.mkdir(parents=True)
    (source_dir / "SKILL.md").write_text(
        "---\nname: fake\n---\nSkill body referencing ./reference.md\n", encoding="utf-8")
    (source_dir / "reference.md").write_text("reference body\n", encoding="utf-8")
    return agent_meta_root, project_root


def test_sync_external_skills_is_idempotent(tmp_path, monkeypatch):
    """An unchanged external skill must not be logged as WRITE/COPY — otherwise
    `sync.py --check` reports permanent drift (issue #802)."""
    agent_meta_root, project_root = _write_skill_fixture(tmp_path, monkeypatch)
    provider_config = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}
    config = {"external-skills": {"fake-skill": {"enabled": True}}}

    first = SyncLog()
    sync_external_skills_for_provider(
        agent_meta_root, project_root, config, {}, first, dry_run=False,
        provider="Claude", provider_config=provider_config,
    )
    first_writes = [a for a in first.actions if "WRITE" in a or "COPY" in a]
    assert first_writes, "first sync must write the skill artifacts"

    second = SyncLog()
    sync_external_skills_for_provider(
        agent_meta_root, project_root, config, {}, second, dry_run=False,
        provider="Claude", provider_config=provider_config,
    )
    assert second.actions == [], (
        "unchanged skill must log no actions (got: "
        f"{[a for a in second.actions if 'WRITE' in a or 'COPY' in a]})"
    )
    assert any("unchanged" in s for s in second.skipped), second.skipped


def test_sync_external_skills_logs_change_when_content_changes(tmp_path, monkeypatch):
    """A genuine content change must still log WRITE/COPY (not be swallowed)."""
    agent_meta_root, project_root = _write_skill_fixture(tmp_path, monkeypatch)
    provider_config = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}
    config = {"external-skills": {"fake-skill": {"enabled": True}}}

    sync_external_skills_for_provider(
        agent_meta_root, project_root, config, {}, SyncLog(), dry_run=False,
        provider="Claude", provider_config=provider_config,
    )

    entry = project_root / "external" / "fake-repo" / "skills" / "fake" / "SKILL.md"
    entry.write_text(entry.read_text(encoding="utf-8") + "\nnew line\n", encoding="utf-8")

    second = SyncLog()
    sync_external_skills_for_provider(
        agent_meta_root, project_root, config, {}, second, dry_run=False,
        provider="Claude", provider_config=provider_config,
    )
    copies = [a for a in second.actions if "COPY" in a]
    assert copies, "changed skill entry must be logged as COPY"


def test_sync_external_skills_secret_content_warns_not_raises(tmp_path, monkeypatch):
    """Third-party skill content is not agent-meta's to police: a secret-looking
    line in a foreign SKILL.md must warn only, never raise SyncError and break
    an otherwise-working sync (issue #802 review F3). The pre-``write_checked``
    raw ``write_text`` never scanned it; the non-blocking variant preserves
    those semantics."""
    agent_meta_root, project_root = _write_skill_fixture(tmp_path, monkeypatch)
    entry = project_root / "external" / "fake-repo" / "skills" / "fake" / "SKILL.md"
    entry.write_text(
        '---\nname: fake\n---\napi_key = "abcdef1234567890"\n',
        encoding="utf-8",
    )
    provider_config = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}
    config = {"external-skills": {"fake-skill": {"enabled": True}}}

    log = SyncLog()
    # Must not raise SyncError despite the generic API-key assignment.
    sync_external_skills_for_provider(
        agent_meta_root, project_root, config, {}, log, dry_run=False,
        provider="Claude", provider_config=provider_config,
    )
    assert any("potential secret" in w for w in log.warnings), log.warnings
