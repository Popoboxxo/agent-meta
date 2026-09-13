"""check_spec_plan_workflow: required sections incl. pipeline_stages,
no-placeholder, traceability, approval marker, ledger format, plan graph.
effective_enabled=false returns [] (no-op)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.consistency.report import Severity
from lib.consistency.spec_plan import check_spec_plan_workflow

_ENABLED = {"spec-plan-workflow": {"enabled": True}}
_DISABLED = {"spec-plan-workflow": {"enabled": False}}

_GOOD_SPEC = (
    "# Demo — Spec\n> Status: APPROVED (2026-09-13)\n"
    "## Problem\nDemo-Problem\n"
    "## Ziel\nDemo-Ziel\n"
    "## Nicht-Ziele\nDemo-Nicht-Ziel\n"
    "## Interface Contracts\n"
    "## Datenfluss\n"
    "## Acceptance Criteria\n1. AC-1\n"
    "## Offene Fragen + Risiken\n"
    "## Trace-Anker: spec-id: SPEC-demo\n"
)


def _plan(text: str) -> str:
    return (
        "# Demo Implementation Plan\n> Status: geplant\n"
        "**Goal:** demo\n**Architecture:** demo\n**Tech Stack:** demo\n"
        "**Spec:** docs/specs/2026-09-13-demo-design.md\n"
        "## Global Constraints\n- stdlib only\n"
        "## File Structure\n- Create: docs/specs/x.md\n"
        "## Trace-Anker: spec-id: SPEC-demo\n"
        "---\npipeline_stages:\n  implement: 1\n---\n"
        + text
    )


def _write(tmp_path: Path, spec: str, plan: str) -> Path:
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    (tmp_path / "docs" / "plans").mkdir(parents=True)
    (tmp_path / "docs" / "specs" / "2026-09-13-demo-design.md").write_text(spec, encoding="utf-8")
    (tmp_path / "docs" / "plans" / "2026-09-13-demo.md").write_text(plan, encoding="utf-8")
    return tmp_path


def test_disabled_returns_empty(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("- [x] Task 1\n"))
    assert check_spec_plan_workflow(
        tmp_path, _DISABLED, agent_meta_root=REPO_ROOT,
    ) == []


def test_good_artifacts_pass(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("- [x] Task 1\n"))
    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )
    assert findings == []


def test_missing_pipeline_stages_is_error(tmp_path):
    plan = _plan("- [x] Task 1\n").replace(
        "pipeline_stages:\n  implement: 1\n", "",
    )
    _write(tmp_path, _GOOD_SPEC, plan)
    findings = check_spec_plan_workflow(
        tmp_path, {**_ENABLED, "dod": {"spec-plan-required": True}},
        agent_meta_root=REPO_ROOT,
    )
    checks = {f.check for f in findings}
    assert "spec_plan_required_sections" in checks
    assert any(f.severity == Severity.ERROR for f in findings)


def test_placeholder_is_error(tmp_path):
    _write(tmp_path, _GOOD_SPEC, _plan("- [ ] TBD\n"))
    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )
    assert any(f.check == "spec_plan_no_placeholder" for f in findings)


def test_plan_graph_no_false_positive_on_acyclic_plan(tmp_path):
    plan = _plan(
        "### Task 1\n**Files:** Modify: a.py\n### Task 2\n**Files:** Modify: b.py\n"
    )
    _write(tmp_path, _GOOD_SPEC, plan)
    findings = check_spec_plan_workflow(
        tmp_path, _ENABLED, agent_meta_root=REPO_ROOT,
    )
    assert not any(f.check == "spec_plan_plan_graph" and f.severity == Severity.ERROR
                   for f in findings)
