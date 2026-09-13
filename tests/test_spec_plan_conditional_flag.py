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
