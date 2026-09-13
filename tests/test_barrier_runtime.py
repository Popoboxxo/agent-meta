import time
from pathlib import Path

from scripts.lib.consistency.report import Severity
from scripts.lib.consistency.spec_plan import check_spec_plan_workflow
from scripts.lib.runtime import (
    SubagentBarrierRuntime,
    SubagentTask,
)

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SPEC_PLAN_ENABLED = {"spec-plan-workflow": {"enabled": True}}


def test_basic_parallel_execution():
    runtime = SubagentBarrierRuntime(max_workers=3)

    def task1_func():
        time.sleep(0.1)
        return "result 1"

    def task2_func():
        time.sleep(0.1)
        return "result 2"

    tasks = [
        SubagentTask(task_id="t1", subagent_type="developer", prompt="Prompt 1", func=task1_func),
        SubagentTask(task_id="t2", subagent_type="git", prompt="Prompt 2", func=task2_func),
    ]

    start_time = time.perf_counter()
    barrier_res = runtime.execute(tasks)
    duration = time.perf_counter() - start_time

    assert barrier_res.status == "success"
    assert len(barrier_res.results) == 2
    assert barrier_res.results[0].task_id == "t1"
    assert barrier_res.results[0].status == "success"
    assert barrier_res.results[0].output == "result 1"
    assert barrier_res.results[0].duration >= 0.1

    assert barrier_res.results[1].task_id == "t2"
    assert barrier_res.results[1].status == "success"
    assert barrier_res.results[1].output == "result 2"
    assert barrier_res.results[1].duration >= 0.1

    # Since they run in parallel, total duration should be close to 0.1s, and definitely less than 0.18s
    assert duration < 0.18


def test_exception_handling():
    runtime = SubagentBarrierRuntime(max_workers=2)

    def fail_func():
        raise ValueError("Something went wrong!")

    tasks = [
        SubagentTask(task_id="t1", subagent_type="developer", prompt="Prompt 1", func=lambda: "success"),
        SubagentTask(task_id="t2", subagent_type="validator", prompt="Prompt 2", func=fail_func),
    ]

    barrier_res = runtime.execute(tasks)

    assert barrier_res.status == "failed"
    assert barrier_res.results[0].status == "success"
    assert barrier_res.results[0].output == "success"

    assert barrier_res.results[1].status == "failed"
    assert "ValueError: Something went wrong!" in barrier_res.results[1].error
    assert barrier_res.results[1].output is None


def test_individual_timeout():
    runtime = SubagentBarrierRuntime(max_workers=2)

    def slow_func():
        time.sleep(0.3)
        return "too late"

    tasks = [
        SubagentTask(task_id="t1", subagent_type="developer", prompt="Prompt 1", func=lambda: "quick"),
        SubagentTask(task_id="t2", subagent_type="validator", prompt="Prompt 2", func=slow_func, timeout=0.1),
    ]

    barrier_res = runtime.execute(tasks)

    assert barrier_res.status == "timeout"
    assert barrier_res.results[0].status == "success"
    assert barrier_res.results[0].output == "quick"

    assert barrier_res.results[1].status == "timeout"
    assert "Task timeout exceeded" in barrier_res.results[1].error
    assert barrier_res.results[1].output is None


def test_global_timeout():
    runtime = SubagentBarrierRuntime(max_workers=2)

    def slow_func():
        time.sleep(0.4)
        return "slow"

    tasks = [
        SubagentTask(task_id="t1", subagent_type="developer", prompt="Prompt 1", func=lambda: "quick"),
        SubagentTask(task_id="t2", subagent_type="validator", prompt="Prompt 2", func=slow_func),
    ]

    barrier_res = runtime.execute(tasks, global_timeout=0.15)

    assert barrier_res.status == "timeout"
    assert barrier_res.results[0].status == "success"
    assert barrier_res.results[0].output == "quick"

    assert barrier_res.results[1].status == "timeout"
    assert "Global timeout exceeded" in barrier_res.results[1].error
    assert barrier_res.results[1].output is None


def test_spec_plan_graph_cycle_is_error(tmp_path):
    """Graph-validator wiring (spec §7.3 / F6): a cyclic plan surfaces as a
    spec_plan_plan_graph ERROR — the barrier runtime's dependency contract
    starts here."""
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    (tmp_path / "docs" / "specs" / "2026-09-13-demo-design.md").write_text(
        "# Demo — Spec\n> Status: APPROVED (2026-09-13)\n"
        "## Problem\np\n## Ziel\nz\n## Nicht-Ziele\nn\n"
        "## Interface Contracts\n## Datenfluss\n## Acceptance Criteria\n1. a\n"
        "## Offene Fragen + Risiken\n## Trace-Anker: spec-id: SPEC-demo\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "plans" / "2026-09-13-demo.md").write_text(
        "# Demo Implementation Plan\n> Status: geplant\n"
        "**Goal:** demo\n**Architecture:** demo\n**Tech Stack:** demo\n"
        "**Spec:** docs/specs/2026-09-13-demo-design.md\n"
        "## Global Constraints\n- stdlib only\n"
        "## File Structure\n- Create: docs/specs/x.md\n"
        "## Trace-Anker: spec-id: SPEC-demo\n"
        "---\npipeline_stages:\n  implement: 1\n---\n"
        "### Task 1: alpha\n**Agent:** developer\n**Files:** Modify: a.py\n"
        "**Depends on:** task-2\n"
        "### Task 2: beta\n**Agent:** tester\n**Files:** Modify: b.py\n"
        "**Depends on:** task-1\n",
        encoding="utf-8",
    )
    findings = check_spec_plan_workflow(
        tmp_path, _SPEC_PLAN_ENABLED, agent_meta_root=_REPO_ROOT,
    )
    assert any(
        f.check == "spec_plan_plan_graph" and f.severity == Severity.ERROR
        for f in findings
    ), str(findings)
