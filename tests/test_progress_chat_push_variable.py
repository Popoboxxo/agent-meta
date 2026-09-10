"""PROGRESS_CHAT_PUSH_ENABLED variable (design doc 2026-09-10-live-progress-
channel-design.md, Architecture §1 Tier-A gate)."""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import build_variables  # noqa: E402


def _config(providers):
    return {
        "project": {"name": "t", "prefix": "t"},
        "ai-providers": providers,
        "roles": ["orchestrator", "developer"],
    }


def test_true_for_claude_only():
    variables, _ = build_variables(_config(["Claude"]), _REPO_ROOT)
    assert variables["PROGRESS_CHAT_PUSH_ENABLED"] == "true"


def test_false_for_opencode_only():
    variables, _ = build_variables(_config(["Opencode"]), _REPO_ROOT)
    assert variables["PROGRESS_CHAT_PUSH_ENABLED"] == "false"


def test_false_for_mixed_claude_and_opencode():
    variables, _ = build_variables(_config(["Claude", "Opencode"]), _REPO_ROOT)
    assert variables["PROGRESS_CHAT_PUSH_ENABLED"] == "false"
