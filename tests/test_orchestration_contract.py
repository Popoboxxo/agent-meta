"""Tests for scripts/lib/orchestration.py — FANOUT/BARRIER contract (issue #265).

Covers (per spike docs/spikes/2026-09-06-issue-265-async-fanout-spike.md §8
step 2/3 acceptance criteria):
    - FanoutTask/FanoutPlan/BarrierEntry/BarrierResult data contract
    - validate_plan: empty/duplicate ids, deadlocks, cycles,
      over-commitment, file overlap (#266 seam), tier_override
    - execute_plan over stub dispatchers: success/failed/timeout/partial
      aggregation (cases mirroring tests/test_barrier_runtime.py),
      deterministic order, #267 checkpoint persistence
    - summarize_result (#267) and render_barrier_result (§7-compatible)
    - dry-run engine repurpose: capability lookup instead of the hardcoded
      provider list, graph validation fail-closed, batch validation
      delegation (no duplicated validation logic)
    - post-sync consistency check (scripts/lib/consistency/fanout_contracts.py):
      clean repo passes, deliberately broken fixtures produce error findings
"""

import shutil
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _ensure_repo_scripts_importable() -> None:
    """Make ``scripts.lib.*`` importable even when a foreign ``scripts``
    package is cached (bare pytest runs).

    Same guard as tests/test_file_affinity.py — see that module's docstring
    for the PEP 420 namespace-shadowing mechanism behind the pre-existing
    bare-run collection errors.
    """
    repo_scripts = (_REPO_ROOT / "scripts").resolve()
    mod = sys.modules.get("scripts")
    if mod is None:
        return
    mod_path = getattr(mod, "__path__", None)
    if not mod_path:
        return
    portions = [str(p) for p in mod_path]
    repo_portion = str(repo_scripts)
    if repo_portion in portions:
        return
    mod.__path__ = [repo_portion, *portions]


_ensure_repo_scripts_importable()

from scripts.lib.checkpoint import CheckpointStore  # noqa: E402
from scripts.lib.consistency.fanout_contracts import (  # noqa: E402
    check_fanout_backend_contract,
)
from scripts.lib.orchestration import (  # noqa: E402
    BARRIER_ENTRY_MARKER,
    BarrierEntry,
    BarrierResult,
    FanoutPlan,
    FanoutTask,
    check_plan_file_overlap,
    execute_plan,
    find_dependency_errors,
    render_barrier_result,
    summarize_result,
    validate_plan,
)
from tests.orchestration.dry_run.engine import DispatchPlan, OrchestratorDryRun, SubTask  # noqa: E402


def _task(task_id: str, agent: str = "developer", prompt: str | None = None, **overrides) -> FanoutTask:
    return FanoutTask(
        task_id=task_id,
        target_agent=agent,
        prompt=prompt if prompt is not None else f"do {task_id}",
        **overrides,
    )


def _two_task_plan(**task_overrides) -> FanoutPlan:
    return FanoutPlan(
        kind="fanout",
        tasks=(
            _task("t1", "developer", **task_overrides),
            _task("t2", "tester", **task_overrides),
        ),
    )


class StubDispatcher:
    """Dispatcher stub returning a fixed entry per task (task order)."""

    def __init__(self, status: str = "success", raw: str | None = None):
        self.status = status
        self.raw = raw

    def dispatch(self, tasks):
        return [
            BarrierEntry(
                task_id=t.task_id,
                agent=t.target_agent,
                status=self.status,
                summary=f"did {t.task_id}",
                raw_output=self.raw,
            )
            for t in tasks
        ]


class MixedDispatcher:
    """Dispatcher stub with per-task statuses, returned out of order."""

    def __init__(self, statuses: dict[str, str]):
        self.statuses = statuses

    def dispatch(self, tasks):
        entries = [
            BarrierEntry(
                task_id=t.task_id,
                agent=t.target_agent,
                status=self.statuses.get(t.task_id, "success"),
                summary=f"did {t.task_id}",
            )
            for t in tasks
        ]
        entries.reverse()  # deliberately not in plan order
        return entries


class ExplodingDispatcher:
    """Dispatcher stub raising for one task (harness-side failure)."""

    def dispatch(self, tasks):
        raise RuntimeError("harness dispatch exploded")


# ---------------------------------------------------------------------------
# validate_plan — graph checks
# ---------------------------------------------------------------------------


def test_valid_plan_has_no_errors():
    assert validate_plan(_two_task_plan(), max_parallel=2) == []


def test_empty_plan_rejected():
    plan = FanoutPlan(kind="fanout", tasks=())
    errors = validate_plan(plan)
    assert len(errors) == 1
    assert "no tasks" in errors[0]


def test_duplicate_task_ids_rejected():
    plan = FanoutPlan(kind="fanout", tasks=(_task("t1"), _task("t1")))
    errors = find_dependency_errors(plan.tasks)
    assert any("duplicate task_id 't1'" in e for e in errors)


def test_unknown_dependency_is_deadlock():
    plan = FanoutPlan(kind="fanout", tasks=(_task("t1", dependencies=("ghost",)),))
    errors = validate_plan(plan)
    assert any("deadlock" in e and "'ghost'" in e for e in errors)


def test_self_dependency_rejected():
    plan = FanoutPlan(kind="fanout", tasks=(_task("t1", dependencies=("t1",)),))
    errors = validate_plan(plan)
    assert any("depends on itself" in e for e in errors)


def test_two_node_cycle_detected():
    plan = FanoutPlan(
        kind="fanout",
        tasks=(
            _task("a", dependencies=("b",)),
            _task("b", dependencies=("a",)),
        ),
    )
    errors = validate_plan(plan)
    assert any("cycle detected" in e and "a" in e and "b" in e for e in errors)


def test_dependency_chain_passes():
    plan = FanoutPlan(
        kind="fanout",
        tasks=(
            _task("a", dependencies=("b",)),
            _task("b"),
        ),
    )
    assert validate_plan(plan, max_parallel=2) == []


def test_cycle_does_not_mask_dangling_dependency():
    plan = FanoutPlan(
        kind="fanout",
        tasks=(
            _task("a", dependencies=("b", "ghost")),
            _task("b", dependencies=("a",)),
        ),
    )
    errors = validate_plan(plan)
    assert any("deadlock" in e for e in errors)
    assert any("cycle detected" in e for e in errors)


# ---------------------------------------------------------------------------
# validate_plan — over-commitment, file overlap, tier_override
# ---------------------------------------------------------------------------


def test_over_commitment_rejected():
    plan = FanoutPlan(kind="fanout", tasks=tuple(_task(f"t{i}") for i in range(3)))
    errors = validate_plan(plan, max_parallel=2)
    assert len(errors) == 1
    assert "over-commitment" in errors[0]
    assert "max_parallel is 2" in errors[0]


def test_over_commitment_uses_plan_max_parallel_by_default():
    """Without an explicit ceiling, the plan's own max_parallel rules.

    A plan declaring ``max_parallel=4`` with 3 tasks is valid when no
    explicit parameter is passed — the former hard-wired ``validate_plan``
    default of 2 produced a false over-commitment error for this exact
    case. An explicit parameter still overrides the plan's ceiling.
    """
    plan = FanoutPlan(
        kind="fanout",
        tasks=tuple(_task(f"t{i}") for i in range(3)),
        max_parallel=4,
    )
    assert validate_plan(plan) == []
    errors = validate_plan(plan, max_parallel=2)
    assert len(errors) == 1
    assert "over-commitment" in errors[0]
    assert "max_parallel is 2" in errors[0]


def test_over_commitment_message_reports_plan_ceiling():
    """The fallback path reports the plan's ceiling in the error message."""
    plan = FanoutPlan(
        kind="fanout",
        tasks=tuple(_task(f"t{i}") for i in range(5)),
        max_parallel=4,
    )
    errors = validate_plan(plan)
    assert len(errors) == 1
    assert "over-commitment" in errors[0]
    assert "max_parallel is 4" in errors[0]


def test_plan_at_parallel_limit_passes():
    plan = FanoutPlan(kind="fanout", tasks=tuple(_task(f"t{i}") for i in range(2)))
    assert validate_plan(plan, max_parallel=2) == []


def _conflict_result() -> dict:
    return {"safe": [], "conflict": [("t1", "t2", ["scripts/lib/cache.py"])]}


def test_file_overlap_precomputed_dict_reports_conflicts():
    errors = validate_plan(_two_task_plan(), file_overlap=_conflict_result())
    assert len(errors) == 1
    assert "'t1'" in errors[0] and "'t2'" in errors[0]
    assert "scripts/lib/cache.py" in errors[0]


def test_file_overlap_callable_receives_projected_tasks():
    seen = {}

    def fake_overlap(projected):
        seen["tasks"] = projected
        return {"safe": ["t1", "t2"], "conflict": []}

    assert validate_plan(_two_task_plan(), file_overlap=fake_overlap) == []
    assert seen["tasks"] == [
        {"id": "t1", "task": "do t1", "files": []},
        {"id": "t2", "task": "do t2", "files": []},
    ]


def test_file_overlap_callable_flat_list_variant():
    errors = validate_plan(_two_task_plan(), file_overlap=lambda tasks: ["t1 vs t2 conflict"])
    assert errors == ["t1 vs t2 conflict"]


def test_file_overlap_unsupported_shape_fails_closed():
    errors = validate_plan(_two_task_plan(), file_overlap=lambda tasks: {"weird": True})
    assert len(errors) == 1
    assert "unsupported result type" in errors[0]


def test_file_overlap_none_skips_check():
    assert validate_plan(_two_task_plan(), file_overlap=None) == []


def test_invalid_tier_override_rejected():
    plan = _two_task_plan(tier_override="ultra-plus")
    errors = validate_plan(plan)
    assert any("invalid tier_override 'ultra-plus'" in e for e in errors)


def test_valid_tier_override_passes():
    plan = _two_task_plan(tier_override="max")
    assert validate_plan(plan) == []


def test_check_plan_file_overlap_seam_returns_266_shape(tmp_path):
    (tmp_path / "scripts" / "lib").mkdir(parents=True)
    (tmp_path / "scripts" / "lib" / "cache.py").write_text("x = 1\n", encoding="utf-8")
    plan = FanoutPlan(
        kind="fanout",
        tasks=(
            _task("t1", prompt="Fix scripts/lib/cache.py"),
            _task("t2", prompt="Refactor scripts/lib/cache.py"),
        ),
    )
    result = check_plan_file_overlap(plan, project_root=tmp_path)
    assert set(result) == {"safe", "conflict"}
    assert result["conflict"] == [("t1", "t2", ["scripts/lib/cache.py"])]


# ---------------------------------------------------------------------------
# execute_plan — barrier aggregation over the injected dispatcher
# ---------------------------------------------------------------------------


def test_execute_all_success():
    result = execute_plan(_two_task_plan(), StubDispatcher(), plan_id="FANOUT-T1")
    assert result.plan_id == "FANOUT-T1"
    assert result.status == "success"
    assert [e.task_id for e in result.entries] == ["t1", "t2"]
    assert result.total_duration_s >= 0.0


def test_execute_partial_when_some_tasks_fail():
    result = execute_plan(
        _two_task_plan(), MixedDispatcher({"t1": "success", "t2": "failed"})
    )
    assert result.status == "partial"


def test_execute_failed_when_all_tasks_fail():
    result = execute_plan(_two_task_plan(), StubDispatcher(status="failed"))
    assert result.status == "failed"


def test_execute_timeout_dominates():
    result = execute_plan(
        _two_task_plan(), MixedDispatcher({"t1": "success", "t2": "timeout"})
    )
    assert result.status == "timeout"


def test_execute_preserves_plan_order():
    result = execute_plan(_two_task_plan(), MixedDispatcher({"t1": "success", "t2": "success"}))
    assert [e.task_id for e in result.entries] == ["t1", "t2"]


def test_execute_generated_plan_id_falls_back_to_kind():
    result = execute_plan(_two_task_plan(), StubDispatcher())
    assert result.plan_id.startswith("FANOUT-")


def test_execute_with_store_archives_raw_output_and_sets_checkpoint_ref(tmp_path):
    store = CheckpointStore(project_root=tmp_path)
    plan = _two_task_plan()
    raws = {"t1": "RAW OUTPUT ONE", "t2": "RAW OUTPUT TWO"}
    dispatcher = StubDispatcher(raw="IGNORED")
    dispatcher.dispatch = lambda tasks: [  # per-task raw output
        BarrierEntry(
            task_id=t.task_id, agent=t.target_agent, status="success",
            summary=f"did {t.task_id}", raw_output=raws[t.task_id],
        )
        for t in tasks
    ]
    result = execute_plan(plan, dispatcher, store=store, session_id="orch-x1")
    assert result.status == "success"
    for entry in result.entries:
        assert entry.raw_output is None, "raw output must not ride in entries"
        assert entry.checkpoint_ref is not None
        archived = (tmp_path / entry.checkpoint_ref).read_text(encoding="utf-8")
        assert archived == raws[entry.task_id]
        assert entry.checkpoint_ref.startswith(".meta-viz/checkpoints/orch-x1/")


def test_execute_without_store_keeps_raw_output_and_no_checkpoint_ref():
    result = execute_plan(_two_task_plan(), StubDispatcher(raw="RAW"))
    assert all(e.raw_output == "RAW" for e in result.entries)
    assert all(e.checkpoint_ref is None for e in result.entries)


def test_execute_defensive_against_missing_and_extra_entries():
    class SloppyDispatcher:
        def dispatch(self, tasks):
            return [
                BarrierEntry(task_id="t2", agent="tester", status="success", summary="ok"),
                BarrierEntry(task_id="ghost", agent="x", status="failed", summary="?"),
            ]

    result = execute_plan(_two_task_plan(), SloppyDispatcher())
    assert [e.task_id for e in result.entries] == ["t2", "ghost"]
    assert result.status == "partial"


def test_execute_dispatcher_contract_is_structural():
    """A plain function is NOT a Dispatcher — the protocol requires .dispatch()."""
    with pytest.raises(AttributeError):
        execute_plan(_two_task_plan(), lambda tasks: [])


# ---------------------------------------------------------------------------
# summarize_result (#267)
# ---------------------------------------------------------------------------


def test_summary_marker_inline_preferred():
    raw = "STATUS: done\nRESULT: ok\nSUMMARY: fixed cache eviction\nARTIFACTS: none"
    assert summarize_result(raw) == "fixed cache eviction"


def test_summary_marker_multiline_block():
    raw = (
        "STATUS: done\n"
        "SUMMARY: fixed the race\n"
        "tests added for eviction\n"
        "\n"
        "ARTIFACTS: none"
    )
    assert summarize_result(raw) == "fixed the race tests added for eviction"


def test_summary_fallback_first_sentences():
    raw = "One sentence. Two sentence. Three. Four. Five."
    assert summarize_result(raw) == "One sentence. Two sentence. Three."


def test_summary_fallback_respects_max_sentences():
    raw = "Alpha. Beta. Gamma. Delta."
    assert summarize_result(raw, max_sentences=2) == "Alpha. Beta."


def test_summary_fallback_length_capped():
    raw = "word " * 300
    summary = summarize_result(raw)
    assert len(summary) <= 401  # cap + ellipsis
    assert summary.endswith("…")


def test_summary_empty_input():
    assert summarize_result("") == ""


# ---------------------------------------------------------------------------
# render_barrier_result (§7-compatible)
# ---------------------------------------------------------------------------


def _barrier_result() -> BarrierResult:
    return BarrierResult(
        plan_id="FANOUT-20260906-001",
        status="partial",
        entries=(
            BarrierEntry(
                task_id="t1", agent="developer", status="success",
                summary="fixed it", checkpoint_ref=".meta-viz/checkpoints/s/a.txt",
                overlap_warnings=("t1 vs t2: scripts/lib/cache.py",),
            ),
            BarrierEntry(task_id="t2", agent="tester", status="failed", summary="boom"),
        ),
        total_duration_s=1.5,
    )


def test_render_contains_s7_wrapper_and_status():
    rendered = render_barrier_result(_barrier_result())
    assert BARRIER_ENTRY_MARKER + "developer result_key=t1 status=success |||" in rendered
    assert BARRIER_ENTRY_MARKER + "tester result_key=t2 status=failed |||" in rendered
    assert rendered.startswith("BARRIER FANOUT-20260906-001: partial")


def test_render_checkpoint_ref_line():
    rendered = render_barrier_result(_barrier_result())
    assert "Full output: .meta-viz/checkpoints/s/a.txt" in rendered


def test_render_overlap_warnings():
    rendered = render_barrier_result(_barrier_result())
    assert "Overlap warning: t1 vs t2: scripts/lib/cache.py" in rendered


def test_render_closing_count_line():
    rendered = render_barrier_result(_barrier_result())
    assert rendered.rstrip().endswith("[2] agents completed")


def test_render_never_leaks_raw_output():
    result = BarrierResult(
        plan_id="P", status="success",
        entries=(BarrierEntry(
            task_id="t1", agent="dev", status="success",
            summary="ok", raw_output="SECRET RAW BLOB",
        ),),
    )
    assert "SECRET RAW BLOB" not in render_barrier_result(result)


# ---------------------------------------------------------------------------
# Dry-run engine repurpose (capability lookup + graph validation)
# ---------------------------------------------------------------------------


def test_engine_parallel_capability_is_capability_driven():
    """Codex/KimiCode are parallel per capabilities; Continue is not; unknown
    providers fail closed to sequential (replaces the hardcoded list)."""
    for provider, expected in (
        ("Claude", True), ("Opencode", True), ("Gemini", True),
        ("Codex", True), ("KimiCode", True),
        ("Continue", False), ("Copilot", False), ("Mammouth", False),
        ("ZCode", False), ("UnknownProvider", False),
    ):
        engine = OrchestratorDryRun(provider, {"max-parallel-agents": 4})
        assert engine._parallel_supported is expected, provider
        assert engine._parallel_supported == (
            engine._fanout_mechanism in ("native-batch", "tool-mediated", "swarm")
        ), provider


def test_engine_code_parallel_fanout_after_capability_lookup():
    """Codex previously fell outside the hardcoded parallel list — capability
    lookup now yields a real FANOUT emission for it."""
    engine = OrchestratorDryRun("Codex", {"max-parallel-agents": 4})
    report = engine.run("Fix parser, renderer")
    assert [op["type"] for op in report.plan.operations] == ["FANOUT"]
    assert report.syntax.valid


def test_engine_cycle_fails_closed_to_sequential():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    subtasks = [
        SubTask(name="task_1", agent_type="developer", description="Fix A", dependencies=["task_2"]),
        SubTask(name="task_2", agent_type="developer", description="Fix B", dependencies=["task_1"]),
    ]
    plan = engine.generate_dispatch_plan(subtasks)
    assert [op["type"] for op in plan.operations] == ["SEQUENTIAL", "SEQUENTIAL"]
    failed_events = [e for e in engine.events if e.type == "plan_validation_failed"]
    assert len(failed_events) == 1
    assert any("cycle detected" in err for err in failed_events[0].data["errors"])


def test_engine_dangling_dependency_fails_closed():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    subtasks = [
        SubTask(name="task_1", agent_type="developer", description="Fix A", dependencies=["ghost"]),
        SubTask(name="task_2", agent_type="developer", description="Fix B"),
    ]
    plan = engine.generate_dispatch_plan(subtasks)
    assert [op["type"] for op in plan.operations] == ["SEQUENTIAL", "SEQUENTIAL"]
    failed_events = [e for e in engine.events if e.type == "plan_validation_failed"]
    assert any("deadlock" in err for err in failed_events[0].data["errors"])


def test_engine_batch_validation_delegates_over_commitment():
    """A hand-built oversized FANOUT op is rejected through the production
    validator (no duplicated max-parallel logic in the engine)."""
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 2})
    plan = DispatchPlan()
    plan.operations = [{
        "type": "FANOUT", "batch": 1,
        "agents": ["developer"] * 3, "tasks": ["a", "b", "c"],
    }]
    report = engine.validate_syntax(plan)
    assert not report.valid
    assert any("over-commitment" in e for e in report.errors)


def test_engine_sequential_provider_error_names_mechanism():
    engine = OrchestratorDryRun("Continue", {"max-parallel-agents": 4})
    plan = DispatchPlan()
    plan.operations = [{"type": "FANOUT", "batch": 1, "agents": ["dev"], "tasks": ["a"]}]
    report = engine.validate_syntax(plan)
    assert not report.valid
    assert any(
        "fanout_mechanism='sequential-fallback'" in e and "Continue" in e
        for e in report.errors
    )


def test_engine_unknown_mechanism_config_raises_loudly():
    """Config drift (unknown mechanism key) must fail loudly in the engine."""
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine
    engine_module = sys.modules["tests.orchestration.dry_run.engine"]
    original = engine_module._SYNTAX_ENGINE
    stub = DelegationSyntaxEngine()
    stub._capabilities_registry = {"capabilities": {"X": {"fanout_mechanism": "warp"}}}
    engine_module._SYNTAX_ENGINE = stub
    try:
        with pytest.raises(ValueError, match="Unknown fanout_mechanism"):
            OrchestratorDryRun("X", {"max-parallel-agents": 4})
    finally:
        engine_module._SYNTAX_ENGINE = original


# ---------------------------------------------------------------------------
# Post-sync consistency check (scripts/lib/consistency/fanout_contracts.py)
# ---------------------------------------------------------------------------


def _fixture_root(tmp_path: Path) -> Path:
    """Real config copies + minimal orchestrator template for fixture runs."""
    root = tmp_path / "agent-meta-fixture"
    (root / "config").mkdir(parents=True)
    (root / "agents" / "1-generic").mkdir(parents=True)
    shutil.copy(_REPO_ROOT / "config" / "provider-capabilities.yaml", root / "config" / "provider-capabilities.yaml")
    shutil.copy(_REPO_ROOT / "config" / "delegation-syntax.yaml", root / "config" / "delegation-syntax.yaml")
    (root / "agents" / "1-generic" / "orchestrator.md").write_text(
        "## 7. BARRIER protocol\n2. Wrap " + BARRIER_ENTRY_MARKER + "<name> result_key=<key> |||\n",
        encoding="utf-8",
    )
    return root


def _rewrite_yaml(path: Path, old: str, new: str) -> None:
    content = path.read_text(encoding="utf-8")
    assert old in content, f"fixture anchor not found: {old!r}"
    path.write_text(content.replace(old, new, 1), encoding="utf-8")


def _error_findings(findings):
    return [f for f in findings if f.severity.value == "ERROR"]


def test_fanout_contract_clean_repo_has_no_errors():
    findings = check_fanout_backend_contract(_REPO_ROOT)
    assert _error_findings(findings) == [], str(findings)


def _break_capabilities_registry(capabilities_file: Path, case: str) -> None:
    """Make the capabilities registry unusable in the given way."""
    if case == "missing":
        capabilities_file.unlink()
    elif case == "empty":
        capabilities_file.write_text("", encoding="utf-8")
    elif case == "invalid":
        capabilities_file.write_text("capabilities: [unclosed\n", encoding="utf-8")
    else:  # pragma: no cover - pytest parametrize guard
        raise ValueError(f"unknown case: {case}")


@pytest.mark.parametrize("case", ["missing", "empty", "invalid"])
def test_fanout_contract_unusable_capabilities_registry_fails_closed(tmp_path, case):
    """A missing/empty/invalid capabilities registry must fail closed.

    The former fail-soft guard returned ``[]`` for all three cases — the
    backend-contract check silently passed exactly when its input was
    unusable. Now the check reports ``fanout.capabilities-missing`` and
    skips the registry-dependent per-provider checks.
    """
    root = _fixture_root(tmp_path)
    _break_capabilities_registry(root / "config" / "provider-capabilities.yaml", case)
    findings = check_fanout_backend_contract(root)
    errors = _error_findings(findings)
    assert [f.check for f in errors] == ["fanout.capabilities-missing"], str(findings)
    assert "provider-capabilities.yaml" in errors[0].message


def test_fanout_contract_marker_check_survives_unusable_registry(tmp_path):
    """Only the per-provider checks are skipped; §7 marker drift still runs."""
    root = _fixture_root(tmp_path)
    (root / "config" / "provider-capabilities.yaml").write_text("", encoding="utf-8")
    (root / "agents" / "1-generic" / "orchestrator.md").write_text(
        "## 7. BARRIER protocol\ncollect everything\n", encoding="utf-8"
    )
    findings = check_fanout_backend_contract(root)
    checks = {f.check for f in findings}
    assert checks == {"fanout.capabilities-missing", "fanout.barrier-marker-drift"}


def test_fanout_contract_missing_mechanism_while_parallel(tmp_path):
    root = _fixture_root(tmp_path)
    _rewrite_yaml(
        root / "config" / "provider-capabilities.yaml",
        "    fanout_mechanism: native-batch\n    barrier_collect: true\n    description: \"Agent-Orchestrierung via task() tool",
        "    barrier_collect: true\n    description: \"Agent-Orchestrierung via task() tool",
    )
    findings = check_fanout_backend_contract(root)
    checks = {f.check for f in _error_findings(findings)}
    assert "fanout.mechanism-missing" in checks


def test_fanout_contract_unknown_mechanism(tmp_path):
    root = _fixture_root(tmp_path)
    _rewrite_yaml(
        root / "config" / "provider-capabilities.yaml",
        "    fanout_mechanism: native-batch\n    barrier_collect: true\n    description: \"Agent-Orchestrierung via task() tool",
        "    fanout_mechanism: warp-drive\n    barrier_collect: true\n    description: \"Agent-Orchestrierung via task() tool",
    )
    findings = check_fanout_backend_contract(root)
    checks = {f.check for f in _error_findings(findings)}
    assert "fanout.unknown-mechanism" in checks


def test_fanout_contract_barrier_collect_mismatch(tmp_path):
    root = _fixture_root(tmp_path)
    _rewrite_yaml(
        root / "config" / "provider-capabilities.yaml",
        "    fanout_mechanism: native-batch\n    barrier_collect: true\n    description: \"Agent-Orchestrierung via task() tool",
        "    fanout_mechanism: native-batch\n    barrier_collect: false\n    description: \"Agent-Orchestrierung via task() tool",
    )
    findings = check_fanout_backend_contract(root)
    checks = {f.check for f in _error_findings(findings)}
    assert "fanout.barrier-collect-mismatch" in checks


def test_fanout_contract_sequential_wording_missing(tmp_path):
    root = _fixture_root(tmp_path)
    _rewrite_yaml(
        root / "config" / "delegation-syntax.yaml",
        '    fanout: "Bearbeite diese Aufgaben der Reihe nach:\\n1. @<agent_1> <task_1>\\n2. @<agent_2> <task_2>"\n    parallel_group: "Bearbeite diese Aufgaben der Reihe nach:\\n1. @<agent_1> <task_1>\\n2. @<agent_2> <task_2>"\n    fallback: "Bearbeite: <task>"\n    bootstrap: "file-based"\n    tool_preamble: "false"\n    auto_parallel: false\n    parallel_pattern: "**Parallel-Pattern:**\\nGitHub Copilot',
        '    fanout: "Alle Agent-Calls in EINER Antwort absetzen"\n    parallel_group: "Mehrere Calls in einer Antwort"\n    fallback: "Bearbeite: <task>"\n    bootstrap: "file-based"\n    tool_preamble: "false"\n    auto_parallel: false\n    parallel_pattern: "**Parallel-Pattern:**\\nGitHub Copilot',
    )
    findings = check_fanout_backend_contract(root)
    checks = {f.check for f in _error_findings(findings)}
    assert "fanout.sequential-wording-missing" in checks


def test_fanout_contract_barrier_marker_drift(tmp_path):
    root = _fixture_root(tmp_path)
    template = root / "agents" / "1-generic" / "orchestrator.md"
    template.write_text("## 7. BARRIER protocol\ncollect everything\n", encoding="utf-8")
    findings = check_fanout_backend_contract(root)
    checks = {f.check for f in _error_findings(findings)}
    assert "fanout.barrier-marker-drift" in checks


def test_fanout_contract_tool_surface_missing(tmp_path):
    root = _fixture_root(tmp_path)
    _rewrite_yaml(
        root / "config" / "provider-capabilities.yaml",
        '    native_agent_tools: ["spawn_agent", "send_input", "resume_agent", "wait_agent", "close_agent"]',
        "    native_agent_tools: []",
    )
    findings = check_fanout_backend_contract(root)
    checks = {f.check for f in _error_findings(findings)}
    assert "fanout.tool-surface-missing" in checks
