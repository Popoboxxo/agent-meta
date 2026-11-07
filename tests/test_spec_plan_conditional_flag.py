"""SPEC_PLAN_WORKFLOW_ENABLED is a strippable conditional, a known builtin
placeholder and a false-flag in standalone rendering (R3)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.variables import strip_inactive_conditional_blocks  # noqa: E402
from lib.consistency.placeholders import _BUILTIN_VARS  # noqa: E402
from lib.standalone import _CONDITIONAL_FALSE_FLAGS  # noqa: E402


def test_conditional_true_keeps_block():
    text = "a{{#if SPEC_PLAN_WORKFLOW_ENABLED}}X{{/if}}b"
    assert strip_inactive_conditional_blocks(
        text, {"SPEC_PLAN_WORKFLOW_ENABLED": "true"},
    ) == "aXb"


def test_conditional_false_strips_block():
    text = "a{{#if SPEC_PLAN_WORKFLOW_ENABLED}}X{{/if}}b"
    assert strip_inactive_conditional_blocks(
        text, {"SPEC_PLAN_WORKFLOW_ENABLED": "false"},
    ) == "ab"


def test_registered_as_builtin_and_standalone_flag():
    assert "SPEC_PLAN_WORKFLOW_ENABLED" in _BUILTIN_VARS
    assert "SPEC_PLAN_SPECS_DIR" in _BUILTIN_VARS
    assert "SPEC_PLAN_PLANS_DIR" in _BUILTIN_VARS
    assert _CONDITIONAL_FALSE_FLAGS["SPEC_PLAN_WORKFLOW_ENABLED"] == "false"


def test_orchestrator_uses_the_conditional():
    text = (REPO_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
    assert "{{#if SPEC_PLAN_WORKFLOW_ENABLED}}" in text
    assert "{{/if}}" in text
    assert "> **Spec/Plan-Workflow aktiv**" in text
    start = text.index("{{#if SPEC_PLAN_WORKFLOW_ENABLED}}")
    end = text.index("{{/if}}", start)
    assert start < end


def test_use_orchestrator_rule_uses_the_conditional():
    """The classify/gate obligation from spec 2.1 must be anchored in the
    orchestrator rule (not only in the pipeline), so non-pipeline requests are
    forced onto the classify route too. Gated by the same master switch."""
    text = (REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md").read_text(encoding="utf-8")
    start = text.index("{{#if SPEC_PLAN_WORKFLOW_ENABLED}}")
    end = text.index("{{/if}}", start)
    assert start < end
    block = text[start:end]
    assert "Classify-Route" in block
    assert "APPROVED" in block
    assert "spec-plan-workflow" in block


def _spec_plan_render(rel: str, enabled: bool) -> str:
    text = (REPO_ROOT / rel).read_text(encoding="utf-8")
    return strip_inactive_conditional_blocks(
        text, {"SPEC_PLAN_WORKFLOW_ENABLED": "true" if enabled else "false"},
    )


def test_planner_requires_approved_spec_only_when_workflow_on():
    # #1158 K-04: the planner must not plan an unapproved M/L/XL spec.
    on = _spec_plan_render("agents/1-generic/planner.md", True)
    off = _spec_plan_render("agents/1-generic/planner.md", False)
    assert "Precondition" in on and "Status: APPROVED" in on
    assert "Precondition" not in off


def test_orchestrator_plan_driven_gate_requires_approval_when_workflow_on():
    on = _spec_plan_render("agents/1-generic/orchestrator.md", True)
    off = _spec_plan_render("agents/1-generic/orchestrator.md", False)
    gate = on[on.index("**Plan-driven gate:**"):].split("\n\n", 1)[0]
    assert "Status: APPROVED" in gate
    gate_off = off[off.index("**Plan-driven gate:**"):].split("\n\n", 1)[0]
    assert "Status: APPROVED" not in gate_off


# One canonical statement on the classify gate outside pipelines (K-05).
_CLASSIFY_GATE_CANON = "S-Klasse ohne Artefakt"


def test_classify_gate_statement_is_identical_everywhere():
    for rel in ("rules/1-generic/use-orchestrator.md",
                "rules/1-generic/spec-plan-workflow.md",
                "agents/1-generic/orchestrator.md"):
        rendered = _spec_plan_render(rel, True)
        assert _CLASSIFY_GATE_CANON in rendered, rel
