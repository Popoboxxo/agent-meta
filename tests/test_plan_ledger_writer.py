"""Plan ledger writer -- round-trip against ``parse_plan_ledger``.

Covers AC-07..AC-10 of the progress/ledger system design
(``SPEC-PROGRESS-LEDGER-2026-09-13``, IC-05): checkbox toggling per task block,
untouched neighbours, parser ``complete`` guarantee, first ``Status:`` write,
missing-plan and unknown-task error behaviour, no-op write avoidance and the
handler's exit codes.
"""
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import plan_ledger  # noqa: E402
from lib.consistency.spec_plan import (  # noqa: E402
    parse_plan_ledger,
    parse_task_ledgers,
)
from lib.plan_ledger import (  # noqa: E402
    MODE,
    handle_update_plan_ledger,
    set_plan_status,
    update_plan_ledger,
)

PLAN_NAME = "2026-09-13-demo.md"

PLAN = (
    "# Demo Implementation Plan\n"
    "> Status: geplant\n"
    "\n"
    "### Task 1: First\n"
    "- [ ] a\n"
    "- [ ] b\n"
    "\n"
    "### Task 2: Second\n"
    "- [ ] c\n"
    "\n"
)


def _plan(tmp_path: Path, text: str = PLAN) -> Path:
    path = tmp_path / PLAN_NAME
    path.write_text(text, encoding="utf-8")
    return path


def _ctx(tmp_path: Path, *, plan=None, tasks=None, status=None, open_=False,
         dry_run=False, project_root=None):
    args = SimpleNamespace(
        update_plan_ledger=plan,
        task=tasks,
        status=status,
        open=open_,
        dry_run=dry_run,
    )
    return SimpleNamespace(args=args,
                           project_root=project_root or tmp_path,
                           log=MagicMock())


# ---------------------------------------------------------------------------
# AC-07 -- toggle one task on
# ---------------------------------------------------------------------------

def test_toggle_task_on_matches_parser(tmp_path, monkeypatch):
    path = _plan(tmp_path)
    writes = []
    real_write_atomic = plan_ledger.write_atomic

    def spy(target, content, *args, **kwargs):
        writes.append(content)
        return real_write_atomic(target, content, *args, **kwargs)

    monkeypatch.setattr(plan_ledger, "write_atomic", spy)

    result = update_plan_ledger(path, {"task-1": True})

    assert result.ok is True
    assert result.reason is None
    assert result.tasks_updated == ("task-1",)
    assert result.checkboxes_toggled == 2
    assert result.unmatched == ()

    ledger = parse_plan_ledger(path)
    assert ledger["checkboxes"] == 3
    assert ledger["checked"] == 2
    assert ledger["complete"] is False

    # Other task untouched.
    assert "- [ ] c" in path.read_text(encoding="utf-8")

    # Atomic single write and disk content equals the built document.
    assert len(writes) == 1
    assert writes[0] == path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# AC-08 -- toggle one task off, neighbours untouched
# ---------------------------------------------------------------------------

def test_toggle_task_off_and_others_untouched(tmp_path):
    text = (
        "# Demo\n> Status: complete\n"
        "### Task 1: A\n- [x] a\n"
        "### Task 2: B\n- [x] b\n- [x] c\n"
        "### Task 3: C\n- [x] d\n"
    )
    path = _plan(tmp_path, text)

    result = update_plan_ledger(path, {"task-2": False})

    assert result.checkboxes_toggled == 2
    assert result.tasks_updated == ("task-2",)

    written = path.read_text(encoding="utf-8")
    assert "- [ ] b" in written
    assert "- [ ] c" in written
    assert "- [x] a" in written
    assert "- [x] d" in written
    assert parse_plan_ledger(path)["complete"] is False


# ---------------------------------------------------------------------------
# AC-09 -- all closed => parser complete; status read back
# ---------------------------------------------------------------------------

def test_all_closed_parser_complete_true(tmp_path):
    path = _plan(tmp_path)

    update_plan_ledger(path, {"task-1": True, "task-2": True})
    result = set_plan_status(path, "complete")

    assert result.ok is True
    ledger = parse_plan_ledger(path)
    assert ledger["checkboxes"] == 3
    assert ledger["checked"] == 3
    assert ledger["complete"] is True
    assert ledger["status"] == "complete"


def test_status_written_and_read_back(tmp_path):
    path = _plan(tmp_path, "# Demo Implementation Plan\n")

    result = set_plan_status(path, "IN PROGRESS")

    assert result.ok is True
    assert result.status == "IN PROGRESS"
    assert result.tasks_updated == ()
    text = path.read_text(encoding="utf-8")
    assert text.startswith("# Demo Implementation Plan\n> Status: IN PROGRESS")
    assert parse_plan_ledger(path)["status"] == "IN PROGRESS"


def test_status_replaces_only_first_existing_line(tmp_path):
    path = _plan(tmp_path, "# Demo\n> Status: geplant\n> Status: other\n")

    set_plan_status(path, "complete")

    text = path.read_text(encoding="utf-8")
    assert "> Status: complete" in text
    assert "> Status: other" in text
    assert text.count("Status:") == 2
    assert parse_plan_ledger(path)["status"] == "complete"


# ---------------------------------------------------------------------------
# AC-10 -- missing plan and unknown task
# ---------------------------------------------------------------------------

def test_missing_plan_reason_plan_not_found(tmp_path):
    path = tmp_path / "does-not-exist.md"

    result = update_plan_ledger(path, {"task-1": True})

    assert result.ok is False
    assert result.reason == "plan-not-found"
    assert result.checkboxes_toggled == 0
    assert not path.exists()


def test_unknown_task_in_unmatched_others_written(tmp_path):
    path = _plan(tmp_path)

    result = update_plan_ledger(path, {"task-1": True, "task-99": True})

    assert result.ok is True
    assert result.unmatched == ("task-99",)
    assert result.tasks_updated == ("task-1",)
    assert result.checkboxes_toggled == 2
    assert parse_plan_ledger(path)["checked"] == 2


# ---------------------------------------------------------------------------
# No-op and dry-run write avoidance
# ---------------------------------------------------------------------------

def test_no_change_no_write(tmp_path, monkeypatch):
    path = _plan(tmp_path, "# Demo\n> Status: complete\n### Task 1: A\n- [x] a\n")
    before = path.read_text(encoding="utf-8")
    calls = []
    monkeypatch.setattr(plan_ledger, "write_atomic",
                        lambda *args, **kwargs: calls.append(args))

    result = update_plan_ledger(path, {"task-1": True})

    assert calls == []
    assert path.read_text(encoding="utf-8") == before
    assert result.ok is True
    assert result.checkboxes_toggled == 0
    assert result.tasks_updated == ()


def test_dry_run_reports_but_does_not_write(tmp_path):
    path = _plan(tmp_path)
    before = path.read_text(encoding="utf-8")

    result = update_plan_ledger(path, {"task-1": True}, status="IN PROGRESS",
                                dry_run=True)

    assert result.dry_run is True
    assert result.ok is True
    assert result.checkboxes_toggled == 2
    assert result.status == "IN PROGRESS"
    assert path.read_text(encoding="utf-8") == before


# ---------------------------------------------------------------------------
# CLI handler (M3: manual validation => exit code 1)
# ---------------------------------------------------------------------------

def test_handler_marks_task_and_exits_0(tmp_path):
    path = _plan(tmp_path)

    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(tmp_path, plan=PLAN_NAME, tasks=["1"])
        )

    assert exc.value.code == 0
    assert parse_plan_ledger(path)["checked"] == 2


def test_handler_sets_mode(tmp_path):
    _plan(tmp_path)
    ctx = _ctx(tmp_path, plan=PLAN_NAME, tasks=["1"])

    with pytest.raises(SystemExit):
        handle_update_plan_ledger(ctx)

    assert ctx.mode == MODE


def test_handler_missing_plan_arg_exits_1(tmp_path):
    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(_ctx(tmp_path, plan=None, tasks=["1"]))
    assert exc.value.code == 1


def test_handler_without_action_exits_1(tmp_path):
    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(_ctx(tmp_path, plan=PLAN_NAME))
    assert exc.value.code == 1


def test_handler_unknown_task_exits_1(tmp_path):
    _plan(tmp_path)
    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(tmp_path, plan=PLAN_NAME, tasks=["99"])
        )
    assert exc.value.code == 1


def test_handler_open_resets_checkboxes(tmp_path):
    path = _plan(tmp_path, "# Demo\n### Task 1: A\n- [x] a\n")

    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(tmp_path, plan=PLAN_NAME, tasks=["1"], open_=True)
        )

    assert exc.value.code == 0
    assert "- [ ] a" in path.read_text(encoding="utf-8")


def test_handler_rejects_path_outside_project_root(tmp_path):
    outside = tmp_path.parent / "outside-plan.md"
    outside.write_text("# Outside\n- [ ] a\n", encoding="utf-8")
    project_root = tmp_path / "project"
    project_root.mkdir()

    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(project_root, plan=str(outside), tasks=["1"],
                 project_root=project_root)
        )

    assert exc.value.code == 1
    assert "- [ ] a" in outside.read_text(encoding="utf-8")


WAVE_PLAN = (
    "# Wave Demo\n"
    "\n"
    "> Status: geplant\n"
    "\n"
    "### W2-0: Erste Welle\n"
    "\n"
    "- [ ] a\n"
    "- [ ] b\n"
    "\n"
    "### W2-1: Zweite Welle\n"
    "\n"
    "- [ ] c\n"
)

REPO_PLAN = (REPO_ROOT / "docs" / "plans"
             / "2026-09-25-repository-documentation-consolidation.md")

requires_repo_plan = pytest.mark.skipif(
    not REPO_PLAN.exists(), reason="repository plan document not present"
)


def test_wave_header_ledger_round_trip(tmp_path):
    """W2-9 (b): ``update_plan_ledger`` <-> ``parse_plan_ledger`` on wave headers."""

    path = _plan(tmp_path, WAVE_PLAN)

    result = update_plan_ledger(path, {"W2-0": True})

    assert result.ok is True
    assert result.reason is None
    assert result.unmatched == ()
    assert result.tasks_updated == ("W2-0",)
    assert result.checkboxes_toggled == 2

    per_task = parse_task_ledgers(path)
    assert sorted(per_task) == ["W2-0", "W2-1"]
    assert per_task["W2-0"]["complete"] is True
    assert per_task["W2-1"]["complete"] is False

    ledger = parse_plan_ledger(path)
    assert ledger["checkboxes"] == 3
    assert ledger["checked"] == 2
    assert ledger["complete"] is False


def test_wave_header_does_not_answer_classic_task_ids(tmp_path):
    """W2-9 (b): the two header forms stay separate -- no id is matched twice."""

    path = _plan(tmp_path, WAVE_PLAN)

    result = update_plan_ledger(path, {"task-1": True})

    assert result.unmatched == ("task-1",)
    assert result.tasks_updated == ()


@requires_repo_plan
def test_ledger_writer_addresses_this_plan(tmp_path):
    """W2-9 (c): end-to-end proof against the plan itself.

    Before W2-9 ``update_plan_ledger(..., {"W2-6": ...})`` reported
    ``unmatched == ("W2-6",)`` and the CLI handler exited 1; afterwards the id
    resolves and the handler exits 0. ``dry_run`` keeps the plan untouched --
    the ledger itself is written by the orchestrator.
    """

    result = update_plan_ledger(REPO_PLAN, {"W2-6": True}, dry_run=True)

    assert result.ok is True
    assert result.reason is None
    assert result.unmatched == ()
    assert parse_task_ledgers(REPO_PLAN)["W2-6"]["total"] > 0

    with pytest.raises(SystemExit) as exc:
        handle_update_plan_ledger(
            _ctx(tmp_path, plan=str(REPO_PLAN), tasks=["W2-6"],
                 dry_run=True, project_root=REPO_ROOT)
        )

    assert exc.value.code == 0


@requires_repo_plan
def test_parse_plan_tasks_against_this_plan():
    """W2-9 (e): the plan graph of this plan, no phantom dep ids.

    K62 / RVW-7-04: the dep-token pattern used to be the hard-coded
    ``task-\\d+|\\d+``, which splits a bold ``**W2-0**`` into the phantom ids
    ``task-2`` / ``task-0``. ``find_dependency_errors`` would then report a
    dangling dependency and ``validate_plan`` would return *before* the
    overlap check -- the fail-closed ownership clause would be lost.
    """

    from lib.consistency.spec_plan import _parse_plan_tasks
    from lib.orchestration import find_dependency_errors

    text = REPO_PLAN.read_text(encoding="utf-8")
    tasks = _parse_plan_tasks(text)
    task_ids = {task.task_id for task in tasks}
    by_id = {task.task_id: task for task in tasks}

    # 50 is the real contract for *this* plan revision (Rev. 0.7 + the W2-9
    # task added in 3b32c156's predecessor), not a constant of the parser: one
    # task per ``### W<n>-<k>`` header. Any plan edit that adds or removes a
    # task header must move this number in the same commit.
    assert len(tasks) == 50, "expected one task per wave header in this plan"
    assert len(task_ids) == len(tasks), "duplicate task ids in the plan graph"
    assert {"W2-0", "W2-6", "W2-9"} <= task_ids

    # VACUUM WARNING: this loop never executes against this plan, because the
    # two assertions below prove that 0 of the 50 tasks carry a dependency. It
    # is the correct guard for a plan whose ``Depends on:`` fields are
    # line-anchored, and it starts to bite the moment ``_DEPENDS_RE`` is
    # widened -- which is exactly why it is kept rather than deleted.
    for task in tasks:
        for dep in task.dependencies:
            assert not dep.startswith("task-"), (
                f"{task.task_id}: phantom dep id {dep!r}"
            )
            assert dep in task_ids, f"{task.task_id}: dangling dep id {dep!r}"

    assert find_dependency_errors(tasks) == []

    # W2-9 (e) expects ``W2-6 => {W2-0}``; measured against this plan that is
    # not what the extractor yields. This plan writes every dependency field
    # mid-line ("**Agent:** developer - **Depends on:** **W2-0** - ..."), and
    # ``_DEPENDS_RE`` is line-start anchored, so it matches nothing here:
    # ``_DEPENDS_RE.findall(plan_text)`` is empty and 0 of 50 tasks carry a
    # dependency -- which is also why the loop above never sees a token. Pinned
    # as the *measured* state, explicitly not as the desired one: widening
    # ``_DEPENDS_RE`` is outside W2-9 because it would change the dependency
    # graph of every plan. The K62 dep-token fix itself is pinned in isolation
    # by test_wave_header_dep_tokens_yield_wave_ids_only.
    # VACUUM (marked at the assertion, not only above): 0 == 0 is a tautology
    # until the dep fields are extractable -- it is a canary, not a proof.
    assert sum(1 for task in tasks if task.dependencies) == 0, (
        "0 of 50 tasks carry a dependency: _DEPENDS_RE is line-start anchored "
        "while this plan writes '**Depends on:**' mid-line. If this fires, the "
        "extraction started working -- revisit the (e) deviation note."
    )
    assert by_id["W2-6"].dependencies == (), (
        "measured, not desired: acceptance (e) expects W2-6 => {W2-0}. See the "
        "deviation note in the plan (open item 1)."
    )


def test_wave_header_dep_tokens_yield_wave_ids_only():
    """W2-9 (e) / K62: the dep-token fix in isolation.

    ``_DEPENDS_RE`` is line-anchored, so a ``Depends on:`` field that starts
    its own line is matched. A wave id in that field must stay a single wave
    id -- the regression this pin guards is ``W2-0`` -> ``task-2``/``task-0``.
    """

    from lib.consistency.spec_plan import _parse_plan_tasks

    tasks = _parse_plan_tasks(
        "### W2-6: Registrierung\n"
        "\n"
        "**Files:** Modify: `scripts/lib/consistency/docs.py`\n"
        "**Agent:** developer\n"
        "**Depends on:** **W2-0**\n"
        "**parallel_group:** - (sequenziell)\n"
    )

    assert [task.task_id for task in tasks] == ["W2-6"]
    assert tasks[0].target_agent == "developer"
    assert tasks[0].dependencies == ("W2-0",)


@requires_repo_plan
def test_validate_plan_reaches_the_expected_overlap_verdict():
    """W2-9 (e): only the expected overlap rest finding survives.

    ``check_file_overlap`` rates a shared write-set file as a *hard* overlap,
    which is the correct rendering of the plan rule "several writing tasks for
    the same file => sequential only". The finding is pinned, not defined
    away, so a later change is noticed.
    """

    from lib.consistency.spec_plan import _parse_plan_tasks
    from lib.orchestration import (
        FanoutPlan,
        check_plan_file_overlap,
        validate_plan,
    )

    text = REPO_PLAN.read_text(encoding="utf-8")
    tasks = _parse_plan_tasks(text)
    fanout = FanoutPlan(kind="sequential", tasks=tuple(tasks),
                        max_parallel=len(tasks))

    errors = validate_plan(fanout,
                           file_overlap=check_plan_file_overlap(fanout, REPO_ROOT))

    graph_errors = [error for error in errors
                    if error.startswith("deadlock:") or "cycle detected" in error]
    assert graph_errors == [], "plan graph must be acyclic and fully resolvable"
    assert errors, "the hard-overlap rest finding is expected for this plan"
    assert all(error.startswith("file overlap between ") for error in errors)
    # TRIPWIRE with a maintained pin -- MAINTENANCE DUTY: when this literal
    # moves, do NOT relax the assert (no ``>=``, no ``<=``, no skip, no xfail,
    # no narrowed ``-k``). Re-measure with ``check_plan_file_overlap``, name the
    # cause, then update the literal and record it. The pin is born-red history
    # is documented in the plan note of W2-9.
    #
    # WHY 18 IS NOT A SEMANTIC CONSTANT: every task in this plan has an empty
    # write set (``files_touched == ()``, see the assertion below), because
    # ``_FILES_FIELD_RE`` demands "Modify:"/"Create:" WITH a colon while this
    # plan writes the field without one. ``check_file_overlap`` therefore builds
    # its write sets from the file names mentioned in the task *titles*, widened
    # by the import/doc-reference edges of the working tree. So the count
    # tracks plan wording and doc-file content -- not a rule this repo defines.
    # That is the point: the pin must trip so a reviewer looks again.
    assert len(errors) == 18, (
        "TRIPWIRE tripped: the hard-overlap finding count for this plan moved -- "
        f"expected 18, got {len(errors)}. This number is derived from the plan "
        "task titles and the working tree's import/doc-reference edges, NOT from "
        "the write sets (every one is empty here) and NOT from a semantic "
        "constant. Maintenance duty: re-measure, confirm what moved, then update "
        f"this literal to {len(errors)} -- never weaken the assert. "
        f"Findings: {errors}"
    )

    # The plan names scripts/lib/consistency/docs.py (W2-1/W2-2/W2-0/W2-7) as
    # the expected overlap, but that pair cannot surface: _FILES_FIELD_RE
    # requires "Modify:"/"Create:" WITH a colon and this plan writes the field
    # without one, so every task has an empty write set and the overlaps come
    # from the task titles instead. Pinned so the gap is visible rather than
    # silently assumed to be covered.
    assert not any("scripts/lib/consistency/docs.py" in error for error in errors)
    assert all(task.files_touched == () for task in tasks)
