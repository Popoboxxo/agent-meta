"""--validate-spec-plan exits 0 without artifacts and is a no-op when the
master switch is off (F12)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.spec_plan_validate import validate_spec_plan  # noqa: E402


def _log(tmp_path):
    return SyncLog()


def test_no_artifacts_exit_zero(tmp_path):
    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": True}}, _log(tmp_path),
    )
    assert code == 0


def test_enabled_false_is_noop_exit_zero(tmp_path):
    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": False}}, _log(tmp_path),
    )
    assert code == 0


def test_flag_registered_in_parser():
    from sync import _build_arg_parser
    args = _build_arg_parser().parse_args(["--validate-spec-plan"])
    assert args.validate_spec_plan is True


def _write_plan(tmp_path, name, text="# Legacy plan\n\nTBD\n"):
    plans = tmp_path / "docs" / "plans"
    plans.mkdir(parents=True, exist_ok=True)
    (plans / name).write_text(text, encoding="utf-8")


def test_unchanged_artifact_out_of_scope_exit_zero(tmp_path, monkeypatch):
    """`scan.changed-files-only` (default true) must exclude unchanged legacy
    artifacts even when they contain findings-causing content (§5.1/§10.2)."""
    _write_plan(tmp_path, "2020-01-01-legacy.md")
    monkeypatch.setattr("lib.spec_plan_validate._changed_files", lambda root: set())

    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": True}}, _log(tmp_path),
    )
    assert code == 0


def test_changed_artifact_in_scope_detects_placeholder(tmp_path, monkeypatch):
    """A changed artifact within scope is scanned and its placeholder yields
    exit 1 — proving the changed-files filter is not a blanket no-op."""
    _write_plan(tmp_path, "2020-01-01-legacy.md")
    monkeypatch.setattr(
        "lib.spec_plan_validate._changed_files",
        lambda root: {"docs/plans/2020-01-01-legacy.md"},
    )

    code = validate_spec_plan(
        tmp_path, {"platforms": [], "spec-plan-workflow": {"enabled": True}}, _log(tmp_path),
    )
    assert code == 1
