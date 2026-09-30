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
