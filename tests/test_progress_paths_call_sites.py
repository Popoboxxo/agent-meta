"""Production call sites route through ``CheckpointStore.from_config``.

Covers AC-09 and AC-15 of ``SPEC-PROGRESS-PATHS-CONFIG-2026-09-13``: all four
production builders (write path ``checkpoint_record``, read paths ``rehydrate``,
``recovery`` and ``consistency.ledger_drift``) construct the store through the
config factory, and a project override makes writes and reads observe the same
directories (no split-brain).
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.checkpoint import Checkpoint, CheckpointStore  # noqa: E402


def _install_from_config_spy(monkeypatch, calls):
    """Record every ``CheckpointStore.from_config`` call, delegate to the real one."""
    real = CheckpointStore.from_config

    def spy(project_root, config=None, agent_meta_root=None):
        calls.append((project_root, config))
        return real(project_root, config=config, agent_meta_root=agent_meta_root)

    monkeypatch.setattr(CheckpointStore, "from_config", staticmethod(spy))


def _cp():
    return Checkpoint(
        task_id="task-1",
        agent="developer",
        task_description="do x",
        status="completed",
    )


def test_checkpoint_record_uses_from_config(tmp_path, monkeypatch):
    calls = []
    _install_from_config_spy(monkeypatch, calls)

    from lib.checkpoint_record import record_checkpoint
    from lib.log import SyncLog

    config = {"progress": {"dir": ".run/progress"}}
    rc = record_checkpoint(
        tmp_path, config, SyncLog(),
        session_id="s", task_id="task-1", agent="developer", status="completed",
    )

    assert rc == 0
    assert calls and calls[0][0] == tmp_path
    assert calls[0][1] == config


def test_rehydrate_uses_from_config(tmp_path, monkeypatch):
    calls = []
    _install_from_config_spy(monkeypatch, calls)

    from lib.log import SyncLog
    from lib.rehydrate import rehydrate

    config = {"spec-plan-workflow": {"recovery": {"rehydrate": True}}}
    rc = rehydrate(tmp_path, config, SyncLog())

    assert rc == 0
    assert calls and calls[0][0] == tmp_path
    assert calls[0][1] == config


def test_recovery_store_for_uses_from_config(tmp_path, monkeypatch):
    calls = []
    _install_from_config_spy(monkeypatch, calls)

    from lib.recovery import _store_for

    store = _store_for(tmp_path, None)

    assert store is not None
    assert calls and calls[0][0] == tmp_path
    assert calls[0][1] is None


def test_ledger_drift_store_uses_from_config(tmp_path, monkeypatch):
    calls = []
    _install_from_config_spy(monkeypatch, calls)

    from lib.consistency.ledger_drift import _store

    store = _store(tmp_path)

    assert store is not None
    assert calls and calls[0][0] == tmp_path
    assert calls[0][1] is None


def test_no_split_brain_write_then_read_with_override(tmp_path):
    config_dir = tmp_path / ".meta-config"
    config_dir.mkdir(parents=True)
    (config_dir / "project.yaml").write_text(
        "progress:\n"
        "  dir: .run/progress\n"
        "  checkpoint-dir: .run/checkpoints\n",
        encoding="utf-8",
    )

    from lib.checkpoint_record import record_checkpoint
    from lib.log import SyncLog
    from lib.recovery import resolve_recovery_sources

    config = {"progress": {"dir": ".run/progress", "checkpoint-dir": ".run/checkpoints"}}
    rc = record_checkpoint(
        tmp_path, config, SyncLog(),
        session_id="split", task_id="task-1", agent="developer",
        status="completed", plan_id="plan-x",
    )
    assert rc == 0

    # The write landed in the override directories, nowhere else.
    assert (tmp_path / ".run" / "checkpoints" / "split.json").exists()
    assert (tmp_path / ".run" / "progress" / "current.md").exists()
    assert not (tmp_path / ".meta-viz").exists()

    # The read path (best-effort config load) observes the same session.
    sources = resolve_recovery_sources(tmp_path)
    assert any(source.session_id == "split" for source in sources)
    assert CheckpointStore.from_config(tmp_path).load_session("split") is not None
