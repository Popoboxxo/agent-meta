"""P3 (AC-11 event part): viz events carry the four instance fields at N>1.

At the default N=1 the emitted event is unchanged: no new keys, and the log
stays the single ``.meta-viz/events.jsonl`` file (no sharding).

Run: python3 -m pytest tests/test_viz_instance_fields.py -q
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_VIZ_LOGGER = _REPO_ROOT / "scripts" / "viz-logger.py"

INSTANCE_FIELDS = ("orchestrator_id", "scope_id", "spawned_by", "spawned_at")

_SPEC = importlib.util.spec_from_file_location("viz_logger", _VIZ_LOGGER)
viz_logger = importlib.util.module_from_spec(_SPEC)
assert _SPEC is not None and _SPEC.loader is not None
_SPEC.loader.exec_module(viz_logger)


def _args(**overrides):
    base = {
        "event": "agent_start",
        "agent": "orchestrator",
        "provider": "Claude",
        "status": None,
        "payload": None,
        "target": None,
        "caller": None,
        "task_id": None,
        "tokens_in": None,
        "tokens_out": None,
    }
    base.update(overrides)
    return argparse.Namespace(**base)


def test_event_without_instance_fields_is_unchanged():
    """N=1: the historic event shape stays byte-for-byte the same key set."""
    event = viz_logger._build_event_from_args(_args())
    assert event == {
        "event": "agent_start",
        "agent": "orchestrator",
        "provider": "Claude",
    }
    assert not set(INSTANCE_FIELDS) & set(event)


def test_event_with_all_four_fields_carries_them():
    event = viz_logger._build_event_from_args(_args(
        orchestrator_id="scope-a",
        scope_id="scope-a",
        spawned_by="main_chat",
        spawned_at="2026-11-05T10:00:00Z",
    ))
    for field in INSTANCE_FIELDS:
        assert event[field] == (
            "2026-11-05T10:00:00Z" if field == "spawned_at" else
            "main_chat" if field == "spawned_by" else "scope-a"
        )


def test_mcp_params_carry_instance_fields_only_when_present():
    base = {"event": "agent_start", "agent": "orchestrator", "provider": "Claude"}
    assert not set(INSTANCE_FIELDS) & set(viz_logger._build_event_from_params(dict(base)))

    params = dict(base, **{
        "orchestrator_id": "scope-a",
        "scope_id": "scope-a",
        "spawned_by": "main_chat",
        "spawned_at": "2026-11-05T10:00:00Z",
    })
    built = viz_logger._build_event_from_params(params)
    for field in INSTANCE_FIELDS:
        assert field in built


def test_log_stays_one_events_jsonl_file(tmp_path):
    viz_logger._apply_project_root(tmp_path)
    viz_logger.write_event_safe({"event": "agent_start", "agent": "orchestrator"})
    viz_dir = tmp_path / ".meta-viz"
    assert (viz_dir / "events.jsonl").is_file()
    assert [p.name for p in viz_dir.iterdir() if p.suffix == ".jsonl"] == [
        "events.jsonl"
    ]


def test_cli_accepts_the_four_optional_flags(tmp_path):
    result = subprocess.run(
        [
            sys.executable,
            str(_VIZ_LOGGER),
            "--root",
            str(tmp_path),
            "--event",
            "agent_start",
            "--agent",
            "orchestrator",
            "--provider",
            "Claude",
            "--orchestrator-id",
            "scope-a",
            "--scope-id",
            "scope-a",
            "--spawned-by",
            "main_chat",
            "--spawned-at",
            "2026-11-05T10:00:00Z",
        ],
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    event = json.loads(
        (tmp_path / ".meta-viz" / "events.jsonl").read_text(encoding="utf-8")
    )
    for field in INSTANCE_FIELDS:
        assert event[field]
