"""Legacy paths are read (WARNING, not ERROR) and never auto-moved."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.consistency.report import Severity
from lib.consistency.spec_plan import check_spec_plan_workflow

_ENABLED = {
    "spec-plan-workflow": {
        "enabled": True,
        "paths": {"legacy": ["docs/superpowers/specs"]},
    }
}


def test_legacy_without_template_is_warning_not_error(tmp_path):
    legacy = tmp_path / "docs" / "superpowers" / "specs"
    legacy.mkdir(parents=True)
    (legacy / "old-note.md").write_text("# old\n", encoding="utf-8")
    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )
    assert all(f.severity != Severity.ERROR for f in findings)


def test_no_auto_move_of_legacy_files(tmp_path):
    legacy = tmp_path / "docs" / "superpowers" / "specs"
    legacy.mkdir(parents=True)
    original = legacy / "2026-01-01-old-design.md"
    original.write_text("# old design\n", encoding="utf-8")
    check_spec_plan_workflow(tmp_path, _ENABLED, agent_meta_root=REPO_ROOT)
    assert original.exists()
