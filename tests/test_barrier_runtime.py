import time
import pytest
from scripts.lib.runtime import SubagentBarrierRuntime, SubagentTask, SubagentResult, BarrierResult

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
