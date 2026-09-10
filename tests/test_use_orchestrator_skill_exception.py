"""Regression test for issue #716: use-orchestrator.md must explicitly state
that skill-driven sub-agent loops (e.g. subagent-driven-development-style
harness skills) are NOT a third exception to the orchestrator-delegation
requirement -- only User-Override (and, in main-chat mode, the main-chat
mode itself) are."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.config import strip_inactive_conditional_blocks, substitute
from lib.log import SyncLog

_TEMPLATE_PATH = REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md"


def _render(variables: dict) -> str:
    text = _TEMPLATE_PATH.read_text(encoding="utf-8")
    text = substitute(text, variables, "use-orchestrator.md", SyncLog())
    return strip_inactive_conditional_blocks(text, variables)


_BASE_VARS = {
    "ORCH_MODE_STRICT": "true", "ORCH_MODE_ADVISORY": "false", "ORCH_MODE_MAIN_CHAT": "false",
    "DIRECT_DISPATCH_ENABLED": "false", "DIRECT_DISPATCH_SECTION": "",
    "INTENT_ROUTING_TABLE": "", "A2A_HANDOFF_BLOCK": "", "STATUS_TABLE_BLOCK": "",
    "AUTO_COMMIT_ENABLED": "false", "NATIVE_EXTENSIONS_WHITELIST_ACTIVE": "false",
    "NATIVE_EXTENSIONS_WHITELIST_TABLE": "",
}


def test_harness_skill_non_exception_documented_when_native_extensions_on():
    rendered = _render({**_BASE_VARS, "NATIVE_EXTENSIONS_ENABLED": "true"})
    assert "subagent-driven-development" in rendered
    assert "KEINE dritte Ausnahme" in rendered


def test_clarification_absent_when_native_extensions_off():
    rendered = _render({**_BASE_VARS, "NATIVE_EXTENSIONS_ENABLED": "false"})
    assert "subagent-driven-development" not in rendered
    assert "Native Extensions deaktiviert." in rendered
