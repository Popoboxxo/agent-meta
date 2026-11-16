"""#1195 (Spec S4): per-directory total cap, content dedup, --prune-sync-backups."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import sync  # noqa: E402
from lib.generated_file_drift import (  # noqa: E402
    backup_drifted_files,
    select_prunable_sync_backups,
)
from lib.log import SyncLog  # noqa: E402

# Relative to now: fixed dates would age past the 30-day prune rule (#1270).
_BASE = datetime.now().replace(microsecond=0) - timedelta(days=5)


def _git_init(root: Path, ignore: bool = True) -> None:
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True,
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
    if ignore:
        (root / ".gitignore").write_text("*.sync-backup-*\n", encoding="utf-8")


def _make_backups(target: Path, sources: int, per_source: int) -> dict:
    """Distinct timestamps: source i, backup j -> minute i*per_source+j."""
    target.mkdir(parents=True, exist_ok=True)
    stamps = {}
    for i in range(sources):
        for j in range(per_source):
            ts = (_BASE + timedelta(minutes=i * per_source + j)).strftime("%Y%m%d-%H%M%S")
            path = target / f"s{i:02d}.md.sync-backup-{ts}"
            path.write_text(f"{i}-{j}", encoding="utf-8")
            stamps[path] = (i, j)
    return stamps


def _newest_per_source(stamps: dict) -> set:
    best: dict = {}
    for path, (i, j) in stamps.items():
        if i not in best or j > best[i][1]:
            best[i] = (path, j)
    return {p for p, _ in best.values()}


def test_total_cap_keeps_newest_of_every_source(tmp_path):
    _git_init(tmp_path)
    stamps = _make_backups(tmp_path / "agents", 10, 3)
    got = select_prunable_sync_backups(
        tmp_path / "agents", 3, max_total=12, project_root=tmp_path)
    assert len(got) == 18
    assert not set(got) & _newest_per_source(stamps)


def test_total_cap_default_30_selects_oldest(tmp_path):
    _git_init(tmp_path)
    stamps = _make_backups(tmp_path / "agents", 12, 3)
    got = select_prunable_sync_backups(
        tmp_path / "agents", 3, max_total=30, project_root=tmp_path)
    assert len(got) == 6
    candidates = sorted(set(stamps) - _newest_per_source(stamps), key=lambda p: p.name[-15:])
    assert set(got) == set(candidates[:6])


def test_more_sources_than_cap_keeps_all_newest(tmp_path):
    _git_init(tmp_path)
    stamps = _make_backups(tmp_path / "agents", 35, 2)
    got = select_prunable_sync_backups(
        tmp_path / "agents", 3, max_total=30, project_root=tmp_path)
    assert len(got) == 35
    assert not set(got) & _newest_per_source(stamps)


def test_total_cap_never_selects_unignored_or_without_git(tmp_path, monkeypatch):
    # Keep git from discovering an enclosing repo (basetemp under repo .tmp/).
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path.parent))
    _git_init(tmp_path, ignore=False)  # repo, but nothing ignored
    _make_backups(tmp_path / "agents", 12, 3)
    assert select_prunable_sync_backups(
        tmp_path / "agents", 3, max_total=30, project_root=tmp_path) == []
    # no repo at all / no project_root
    plain = tmp_path.parent / (tmp_path.name + "-plain")
    _make_backups(plain / "agents", 12, 3)
    assert select_prunable_sync_backups(
        plain / "agents", 3, max_total=30, project_root=plain) == []
    assert select_prunable_sync_backups(plain / "agents", 3, max_total=30) == []


def test_backup_dedup_reuses_existing_backup(tmp_path, monkeypatch):
    import lib.generated_file_drift as drift

    class _Clock:
        n = 0
        strptime = staticmethod(datetime.strptime)

        @classmethod
        def now(cls):
            cls.n += 1
            return _BASE + timedelta(seconds=cls.n)

    monkeypatch.setattr(drift, "datetime", _Clock)
    (tmp_path / "a.md").write_text("on disk", encoding="utf-8")
    findings = [{"path": "a.md", "provider": "Claude", "pre_text": "user edit"}]
    first = backup_drifted_files(findings, tmp_path, SyncLog())
    second = backup_drifted_files(findings, tmp_path, SyncLog())
    assert len(list(tmp_path.glob("a.md.sync-backup-*"))) == 1
    assert second == first
    findings[0]["pre_text"] = "other edit"
    third = backup_drifted_files(findings, tmp_path, SyncLog())
    assert third != first
    assert len(list(tmp_path.glob("a.md.sync-backup-*"))) == 2


def test_steady_state_five_syncs_stay_within_cap(tmp_path, monkeypatch):
    import lib.generated_file_drift as drift

    _git_init(tmp_path)
    agents = tmp_path / "agents"
    _make_backups(agents, 12, 3)

    class _Clock:
        n = 0
        strptime = staticmethod(datetime.strptime)

        @classmethod
        def now(cls):
            cls.n += 1
            return _BASE + timedelta(days=1, seconds=cls.n)

    monkeypatch.setattr(drift, "datetime", _Clock)
    (agents / "s00.md").write_text("x", encoding="utf-8")
    for run in range(5):
        findings = [{"path": "agents/s00.md", "provider": "C", "pre_text": f"edit{run}"}]
        backup_drifted_files(findings, tmp_path, SyncLog())
        drift.prune_sync_backups(
            agents, tmp_path, SyncLog(), False, 30, 3, max_total=30)
        assert len(list(agents.glob("*.sync-backup-*"))) <= 30


def _cli_project(root: Path) -> None:
    _git_init(root)
    cfg = root / ".meta-config"
    cfg.mkdir()
    (cfg / "project.yaml").write_text(
        "agent-meta-version: 0.101.0\nai-providers: [Claude]\n"
        "roles: [orchestrator, developer, git]\n"
        "project:\n  name: t\n  prefix: t\n  short: t\n", encoding="utf-8")
    agents = root / ".claude" / "agents"
    _make_backups(agents, 12, 3)


def _cli(root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"),
         "--config", str(root / ".meta-config" / "project.yaml"),
         "--prune-sync-backups", *extra],
        cwd=str(root), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=120)


def test_cli_prune_dry_run_lists_and_cli_prunes_with_parity(tmp_path):
    _cli_project(tmp_path)
    agents = tmp_path / ".claude" / "agents"
    before = sorted(p.name for p in agents.iterdir())
    expected = sorted(
        p.relative_to(tmp_path).as_posix() for p in select_prunable_sync_backups(
            agents, sync._PREVIEW_PRUNE_MAX_PER_SOURCE,
            max_total=sync._PREVIEW_PRUNE_MAX_TOTAL, project_root=tmp_path))
    assert len(expected) == 6
    assert sync._preview_backups_to_prune(agents, tmp_path) == expected

    dry = _cli(tmp_path, "--dry-run")
    assert dry.returncode == 0, dry.stdout + dry.stderr
    assert json.loads(dry.stdout)["candidates"] == expected
    assert sorted(p.name for p in agents.iterdir()) == before

    real = _cli(tmp_path)
    assert real.returncode == 0, real.stdout + real.stderr
    assert len(list(agents.glob("*.sync-backup-*"))) == 30
    assert not [e for e in expected if (tmp_path / e).exists()]


def test_managed_dirs_for_prune_includes_project_root(tmp_path):
    """#1270: root-level backups (e.g. CLAUDE.md.sync-backup-*) must be pruned too."""
    from lib.sync_pipeline import _managed_dirs_for_prune

    assert tmp_path in _managed_dirs_for_prune(tmp_path, {}, {})


def test_age_rule_prunes_lone_old_backup_only(tmp_path):
    """#1270 (E-09): newer>=keep OR older than max_age_days."""
    def stamp(days):
        return (datetime.now() - timedelta(days=days)).strftime("%Y%m%d-%H%M%S")

    old = tmp_path / f"old.md.sync-backup-{stamp(31)}"
    young = tmp_path / f"young.md.sync-backup-{stamp(29)}"
    for path in (old, young):
        path.write_text("x", encoding="utf-8")
    assert select_prunable_sync_backups(tmp_path, 3, max_age_days=30) == [old]
    assert select_prunable_sync_backups(tmp_path, 3) == []  # default: count-only
