"""#1242 / spec A2: one-time migration stages are gated on legacy paths."""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

_BEGIN = "<!-- agent-meta:managed-begin -->"
_END = "<!-- agent-meta:managed-end -->"


def _cfg() -> dict:
    return {
        "agents_dir": ".gemini/agents",
        "agent-discovery": True,
        "discovery": {"agents_dir": ".agents/agents"},
    }


def _spy(monkeypatch):
    from lib import sync_pipeline

    calls = []
    real = sync_pipeline.migrate_managed_artifact

    def spy(*a, **kw):
        calls.append(a)
        return real(*a, **kw)

    monkeypatch.setattr(sync_pipeline, "migrate_managed_artifact", spy)
    return calls


def test_migrated_project_skips_migration_stage(tmp_path, monkeypatch):
    from lib.log import SyncLog
    from lib.sync_pipeline import apply_discovery_migration

    calls = _spy(monkeypatch)
    (tmp_path / ".agents" / "agents").mkdir(parents=True)
    resolved, results = apply_discovery_migration(tmp_path, _cfg(), SyncLog())
    assert results == [] and calls == []
    assert resolved["agents_dir"] == ".agents/agents"


def test_legacy_project_migrates_exactly_once(tmp_path, monkeypatch):
    from lib.log import SyncLog
    from lib.sync_pipeline import apply_discovery_migration

    calls = _spy(monkeypatch)
    old = tmp_path / ".gemini" / "agents"
    old.mkdir(parents=True)
    (old / "a.md").write_text(f"{_BEGIN}\nx\n{_END}\n", encoding="utf-8")
    apply_discovery_migration(tmp_path, _cfg(), SyncLog(), ts="20260101-000000")
    apply_discovery_migration(tmp_path, _cfg(), SyncLog(), ts="20260101-000000")
    assert len(calls) == 1


def test_provider_migration_gated_without_legacy_paths(tmp_path):
    from lib.log import SyncLog
    from lib.sync_pipeline import migrate_provider_paths

    migrations = {"X": {"removals": [{"remove": ".x/old", "kind": "dir"}]}}
    log = SyncLog()
    assert migrate_provider_paths(tmp_path, "X", {}, log, migrations=migrations) == []


def test_gate_fails_open_with_warning(tmp_path):
    from lib import sync_pipeline
    from lib.log import SyncLog

    class Boom:
        def exists(self):
            raise OSError("boom")

    log = SyncLog()
    warned = []
    log.warn = lambda m, p0=False: warned.append(m)
    assert sync_pipeline._legacy_path_exists([Boom()], log, "s") is True
    assert warned
