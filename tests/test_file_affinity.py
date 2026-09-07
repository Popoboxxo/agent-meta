"""Tests for scripts/lib/file_affinity.py — static file-affinity analysis (issue #266).

Covers:
    - exact issue-#266 API shape of check_file_overlap()
    - task input normalization (str | dict | duck-typed SubTask)
    - Python-file symbol resolution (ast), Markdown/YAML reference
      parsing (regex), import-graph coupling
    - dry-run engine integration (conflicted tasks sequentialized
      before simulated FANOUT / PARALLEL_GROUP)
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _ensure_repo_scripts_importable() -> None:
    """Make ``scripts.lib.*`` importable even when a foreign ``scripts``
    package is cached (bare pytest runs).

    A bare ``python -m pytest`` collects ``external/awesome-claude-code``
    before this repo's tests; its tests put their own root on sys.path and
    import their ``scripts`` package (regular package with
    ``__init__.py``). Per PEP 420 a regular package beats a namespace
    portion regardless of sys.path order, so the cached package shadows
    this repo's ``scripts`` namespace for every later ``scripts.lib.*``
    import — the mechanism behind the pre-existing bare-run collection
    errors. This guard merges this repo's ``scripts`` directory as the
    FIRST portion of the cached package's ``__path__``: ``scripts.lib``
    resolves here while foreign subtrees (``scripts.badges`` etc.) and
    already-collected external test modules stay intact.
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
        return  # this repo is already visible — nothing to do
    mod.__path__ = [repo_portion, *portions]


_ensure_repo_scripts_importable()

from scripts.lib.file_affinity import (  # noqa: E402
    BOUNDARY_NOTE,
    check_file_overlap,
    extract_file_references,
    format_overlap_report,
)
from tests.orchestration.dry_run.engine import OrchestratorDryRun, SubTask  # noqa: E402


# ---------------------------------------------------------------------------
# API shape (issue #266, exact)
# ---------------------------------------------------------------------------


def test_result_keys_are_exactly_safe_and_conflict():
    result = check_file_overlap(
        ["Fix scripts/lib/toml_writer.py", "Fix scripts/lib/cache.py"]
    )
    assert set(result) == {"safe", "conflict"}
    assert result["safe"] == ["task_1", "task_2"]
    assert result["conflict"] == []


def test_disjoint_tasks_are_safe():
    result = check_file_overlap(
        [
            "Fix scripts/lib/toml_writer.py",
            "Write tests for tests/test_barrier_runtime.py",
        ]
    )
    assert result["safe"] == ["task_1", "task_2"]
    assert result["conflict"] == []


def test_identical_file_reference_hard_overlap():
    result = check_file_overlap(
        [
            "Fix bug in scripts/lib/toml_writer.py",
            "Fix lint in scripts/lib/toml_writer.py",
        ]
    )
    assert result["safe"] == []
    assert result["conflict"] == [
        ("task_1", "task_2", ["scripts/lib/toml_writer.py"]),
    ]


def test_none_empty_and_single_task_inputs():
    assert check_file_overlap(None) == {"safe": [], "conflict": []}
    assert check_file_overlap([]) == {"safe": [], "conflict": []}
    assert check_file_overlap("Only one task") == {
        "safe": ["task_1"],
        "conflict": [],
    }


def test_non_iterable_task_input_raises_type_error(tmp_path):
    with pytest.raises(TypeError):
        check_file_overlap(42, project_root=tmp_path)
    with pytest.raises(TypeError):
        check_file_overlap([42], project_root=tmp_path)


# ---------------------------------------------------------------------------
# Task input normalization (repo structures)
# ---------------------------------------------------------------------------


def test_dict_task_with_explicit_files_field(tmp_path):
    tasks = [
        {"id": "A", "files": ["src/x.py"]},
        {"id": "B", "files": ["src/x.py"], "description": "touch src/x.py again"},
    ]
    result = check_file_overlap(tasks, project_root=tmp_path)
    assert result["conflict"] == [("A", "B", ["src/x.py"])]
    assert result["safe"] == []


def test_mixed_input_types_keep_their_ids(tmp_path):
    subtask = SubTask(name="sub-1", agent_type="developer", description="Edit module_one.py")
    tasks = [
        subtask,
        {"task_id": "dict-7", "description": "Edit module_two.py"},
        "Edit module_three.py",
    ]
    result = check_file_overlap(tasks, project_root=tmp_path)
    assert result["safe"] == ["sub-1", "dict-7", "task_3"]
    assert result["conflict"] == []


def test_checkpoint_style_dict_input_is_supported():
    # Mirrors scripts/lib/checkpoint.py Checkpoint.to_dict() keys.
    result = check_file_overlap(
        [{"task_id": "cp-1", "task_description": "Fix scripts/lib/toml_writer.py"}]
    )
    assert result == {"safe": ["cp-1"], "conflict": []}


# ---------------------------------------------------------------------------
# Reference extraction (regex pass)
# ---------------------------------------------------------------------------


def test_extract_file_references_regex_pass():
    text = (
        "Fix `scripts/lib/config.py`, rewrite .claude/rules/x.md; "
        "see docs\\x.yaml and README.md."
    )
    assert extract_file_references(text) == [
        "scripts/lib/config.py",
        ".claude/rules/x.md",
        "docs/x.yaml",
        "README.md",
    ]


def test_extract_file_references_deduplicates():
    assert extract_file_references("a.md then a.md again") == ["a.md"]


# ---------------------------------------------------------------------------
# Coupling analysis (tmp projects)
# ---------------------------------------------------------------------------


def test_import_graph_coupling_conflict(tmp_path):
    (tmp_path / "a.py").write_text("import b\n\n\ndef run_pipeline():\n    pass\n")
    (tmp_path / "b.py").write_text("def helper_module():\n    pass\n")
    result = check_file_overlap(
        ["Rewrite a.py", "Rewrite b.py"], project_root=tmp_path
    )
    assert result["safe"] == []
    assert result["conflict"] == [("task_1", "task_2", ["a.py", "b.py"])]


def test_doc_reference_coupling_conflict(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("Run `scripts/lib/tools.py` before the migration.\n")
    lib_dir = tmp_path / "scripts" / "lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "tools.py").write_text("def tools_entry():\n    pass\n")
    result = check_file_overlap(
        ["Update docs/guide.md", "Fix scripts/lib/tools.py"], project_root=tmp_path
    )
    assert result["conflict"] == [
        ("task_1", "task_2", ["docs/guide.md", "scripts/lib/tools.py"]),
    ]


def test_yaml_frontmatter_reference_conflict(tmp_path):
    (tmp_path / "settings.yaml").write_text(
        "---\ntarget: scripts/lib/loader.py\n---\nmode: safe\n"
    )
    (tmp_path / "loader.py").write_text("def load_all():\n    pass\n")
    result = check_file_overlap(
        ["Adjust settings.yaml", "Edit scripts/lib/loader.py"], project_root=tmp_path
    )
    assert result["conflict"] == [
        ("task_1", "task_2", ["scripts/lib/loader.py", "settings.yaml"]),
    ]


def test_symbol_resolution_maps_task_to_defining_file(tmp_path):
    (tmp_path / "session.py").write_text(
        "def resolve_user_session(token: str) -> None:\n    pass\n"
    )
    result = check_file_overlap(
        ["Refactor resolve_user_session handling", "Update session.py"],
        project_root=tmp_path,
    )
    assert result["conflict"] == [("task_1", "task_2", ["session.py"])]


def test_nonexistent_planned_files_still_overlap(tmp_path):
    # Planned (not yet existing) paths overlap by reference identity;
    # missing files must not crash the import/doc passes.
    result = check_file_overlap(
        [
            "Create scripts/lib/newmod.py",
            "Test scripts/lib/newmod.py",
        ],
        project_root=tmp_path,
    )
    assert result["conflict"] == [("task_1", "task_2", ["scripts/lib/newmod.py"])]


# ---------------------------------------------------------------------------
# Determinism + report format
# ---------------------------------------------------------------------------


def test_result_is_deterministic_across_calls():
    tasks = [
        "Fix scripts/lib/toml_writer.py",
        "Rewrite scripts/lib/toml_writer.py",
        "Write tests for tests/test_barrier_runtime.py",
    ]
    first = check_file_overlap(tasks)
    second = check_file_overlap(tasks)
    assert first == second
    assert first["conflict"] == [("task_1", "task_2", ["scripts/lib/toml_writer.py"])]
    assert first["safe"] == ["task_3"]


def test_format_overlap_report_lists_conflicts_and_boundary():
    overlap = check_file_overlap(
        ["Fix scripts/lib/toml_writer.py", "Fix scripts/lib/toml_writer.py"]
    )
    report = format_overlap_report(overlap)
    assert "task_1" in report and "task_2" in report
    assert "scripts/lib/toml_writer.py" in report
    assert "harness-side" in report
    assert BOUNDARY_NOTE in report


# ---------------------------------------------------------------------------
# Dry-run engine integration (issue #266)
# ---------------------------------------------------------------------------


def test_engine_fanout_unchanged_without_file_references():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    report = engine.run("Fix parser crash, renderer leak, validator error")
    ops = report.plan.operations
    assert ops[0]["type"] == "FANOUT"
    assert len(ops[0]["tasks"]) == 3
    assert all(op["type"] != "SEQUENTIAL" for op in ops)


def test_engine_fanout_batching_unchanged_without_conflicts():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 2})
    report = engine.run("Fix parser, renderer, validator")
    assert [op["type"] for op in report.plan.operations] == [
        "FANOUT", "BARRIER", "FANOUT",
    ]


def test_engine_sequentializes_conflicting_fanout():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    report = engine.run(
        "Fix bug in scripts/lib/toml_writer.py, fix lint in scripts/lib/toml_writer.py"
    )
    ops = report.plan.operations
    assert [op["type"] for op in ops] == ["SEQUENTIAL", "SEQUENTIAL"]
    assert ops[0]["task"].startswith("Fix bug in")
    assert ops[1]["task"].startswith("fix lint in")


def test_engine_sequentializes_conflicting_parallel_group():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    subtasks = [
        SubTask(name="task_1", agent_type="developer", description="Fix scripts/lib/toml_writer.py"),
        SubTask(
            name="task_2",
            agent_type="documenter",
            description="Update docs for scripts/lib/toml_writer.py",
        ),
    ]
    plan = engine.generate_dispatch_plan(subtasks)
    ops = plan.operations
    assert [op["type"] for op in ops] == ["SEQUENTIAL", "SEQUENTIAL"]
    assert ops[0]["agent"] == "developer"
    assert ops[1]["agent"] == "documenter"


def test_engine_partial_conflict_keeps_safe_tasks_parallel():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    subtasks = [
        SubTask(name="task_1", agent_type="developer", description="Fix bug in scripts/lib/toml_writer.py"),
        SubTask(name="task_2", agent_type="developer", description="Fix lint in scripts/lib/toml_writer.py"),
        SubTask(name="task_3", agent_type="developer", description="Refactor scripts/lib/gitignore.py"),
        SubTask(name="task_4", agent_type="developer", description="Refactor scripts/lib/cache.py"),
    ]
    plan = engine.generate_dispatch_plan(subtasks)
    ops = plan.operations
    assert [op["type"] for op in ops] == [
        "FANOUT", "BARRIER", "SEQUENTIAL", "SEQUENTIAL",
    ]
    # The FANOUT contains only the conflict-free subset.
    assert ops[0]["tasks"] == [
        "Refactor scripts/lib/gitignore.py",
        "Refactor scripts/lib/cache.py",
    ]
    # Conflicted tasks are sequentialized in original input order.
    assert ops[2]["task"] == "Fix bug in scripts/lib/toml_writer.py"
    assert ops[3]["task"] == "Fix lint in scripts/lib/toml_writer.py"


def test_engine_mixed_safe_types_stay_parallel_group():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    subtasks = [
        SubTask(name="task_1", agent_type="developer", description="Fix scripts/lib/toml_writer.py"),
        SubTask(name="task_2", agent_type="documenter", description="Update docs/affinity-guide.md"),
        SubTask(
            name="task_3",
            agent_type="tester",
            description="Write tests for tests/test_barrier_runtime.py",
        ),
    ]
    plan = engine.generate_dispatch_plan(subtasks)
    assert [op["type"] for op in plan.operations] == ["PARALLEL_GROUP"]


def test_engine_logs_file_overlap_checked_event():
    engine = OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    report = engine.run(
        "Fix bug in scripts/lib/toml_writer.py, fix lint in scripts/lib/toml_writer.py"
    )
    events = [e for e in report.events if e.type == "file_overlap_checked"]
    assert len(events) == 1
    data = events[0].data
    assert data["sequentialized"] == ["task_1", "task_2"]
    assert data["method"] == "static-analysis"
    assert data["enforcement"] == "harness-side"
    assert data["conflicts"] == [
        ("task_1", "task_2", ["scripts/lib/toml_writer.py"]),
    ]


def test_engine_falls_back_to_previous_plan_when_module_unavailable(monkeypatch):
    # Degradation contract: without the analysis module the engine must
    # behave exactly as before issue #266 (no gate, no event).
    import tests.orchestration.dry_run.engine as engine_module

    monkeypatch.setattr(engine_module, "_FILE_AFFINITY_AVAILABLE", False)
    engine = engine_module.OrchestratorDryRun("Opencode", {"max-parallel-agents": 4})
    report = engine.run(
        "Fix bug in scripts/lib/toml_writer.py, fix lint in scripts/lib/toml_writer.py"
    )
    assert [op["type"] for op in report.plan.operations] == ["FANOUT"]
    assert not [e for e in report.events if e.type == "file_overlap_checked"]
