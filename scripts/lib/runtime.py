"""Parallel subagent execution barrier runtime."""

import time
import traceback
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SubagentTask:
    task_id: str
    subagent_type: str
    prompt: str
    func: Callable[[], Any]  # The function to execute the subagent task
    description: str = ""
    timeout: float | None = None


@dataclass
class SubagentResult:
    task_id: str
    subagent_type: str
    prompt: str
    status: str  # "success", "failed", "timeout"
    output: Any = None
    error: str | None = None
    duration: float = 0.0


@dataclass
class BarrierResult:
    results: list[SubagentResult] = field(default_factory=list)
    total_duration: float = 0.0
    status: str = "success"  # "success", "failed", "timeout"


class SubagentBarrierRuntime:
    """Deterministic barrier runtime for executing subagent tasks in parallel."""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers

    def execute(self, tasks: list[SubagentTask], global_timeout: float | None = None) -> BarrierResult:
        """Executes a list of SubagentTask instances in parallel using a thread pool.

        Maintains barrier synchronization, aggregates outcomes, handles timeouts (both individual and global),
        captures exceptions, and records durations.
        """
        start_time = time.perf_counter()
        results: dict[str, SubagentResult] = {}
        futures = {}

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for task in tasks:
                # Wrap each task to track its individual start time and duration, and capture exceptions
                def worker(t=task) -> SubagentResult:
                    t_start = time.perf_counter()
                    try:
                        res = t.func()
                        t_duration = time.perf_counter() - t_start
                        return SubagentResult(
                            task_id=t.task_id,
                            subagent_type=t.subagent_type,
                            prompt=t.prompt,
                            status="success",
                            output=res,
                            duration=t_duration
                        )
                    except Exception as e:  # noqa: BLE001
                        t_duration = time.perf_counter() - t_start
                        tb = traceback.format_exc()
                        return SubagentResult(
                            task_id=t.task_id,
                            subagent_type=t.subagent_type,
                            prompt=t.prompt,
                            status="failed",
                            error=f"{e!s}\n{tb}",
                            duration=t_duration
                        )

                future = executor.submit(worker)
                futures[future] = task

            # Deterministic sequential wait implementing a barrier with timeouts
            for future, task in futures.items():
                # How much time is left from global timeout?
                time_left = None
                if global_timeout is not None:
                    elapsed = time.perf_counter() - start_time
                    time_left = max(0.0, global_timeout - elapsed)

                # Determine the actual timeout to use for this specific future
                # It is the minimum of its individual timeout and the remaining global timeout
                current_timeout = task.timeout
                if time_left is not None:  # noqa: SIM102
                    if current_timeout is None or current_timeout > time_left:
                        current_timeout = time_left

                try:
                    res = future.result(timeout=current_timeout)
                    results[task.task_id] = res
                except TimeoutError:
                    future.cancel()
                    # Mark as timeout
                    results[task.task_id] = SubagentResult(
                        task_id=task.task_id,
                        subagent_type=task.subagent_type,
                        prompt=task.prompt,
                        status="timeout",
                        error="Task timeout exceeded" if (task.timeout is not None and current_timeout == task.timeout) else "Global timeout exceeded"
                    )
                except Exception as e:  # noqa: BLE001
                    # In case of internal ThreadPoolExecutor exceptions
                    tb = traceback.format_exc()
                    results[task.task_id] = SubagentResult(
                        task_id=task.task_id,
                        subagent_type=task.subagent_type,
                        prompt=task.prompt,
                        status="failed",
                        error=f"{e!s}\n{tb}"
                    )

        # Ensure all tasks have a result (e.g. if ThreadPoolExecutor exited otherwise)
        for task in tasks:
            if task.task_id not in results:
                results[task.task_id] = SubagentResult(
                    task_id=task.task_id,
                    subagent_type=task.subagent_type,
                    prompt=task.prompt,
                    status="failed",
                    error="Task did not complete execution"
                )

        total_duration = time.perf_counter() - start_time
        results_list = [results[t.task_id] for t in tasks]

        # Determine overall status
        status = "success"
        if any(r.status == "timeout" for r in results_list):
            status = "timeout"
        elif any(r.status == "failed" for r in results_list):
            status = "failed"

        return BarrierResult(
            results=results_list,
            total_duration=total_duration,
            status=status
        )
