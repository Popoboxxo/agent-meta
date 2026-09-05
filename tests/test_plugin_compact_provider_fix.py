"""ZCode/KimiCode have no lazy channel (no rules, no skills capability): under
project-wide compact mode they must still receive the FULL embedded plugin
content, or the agent-hint is silently lost. Regression for the spec gap.

Note (Task 4 Step 2): the brief's integration-level variant of this test
depends on a `context.build_agent_hints_for_provider(...)` helper that does
not exist in the current `scripts/lib/context.py` -- the module only exposes
`_build_managed_block`, a private function entangled with SyncLog/variables
plumbing that isn't practical to call standalone for a single assertion.
Building that helper is out of scope for this surgical fix (see task brief:
"if wiring ... is impractical, keep only the unit assertions ... the unit
test fully covers the decision logic"). The RED state before the
`scripts/lib/context.py` fix was verified manually by inspecting
`_build_managed_block` (pre-fix it fed the single global `_compact` flag
straight into `_generate_rule_content`/`_generate_tool_rule_content` with no
per-provider lazy-channel check), and the fix's correctness is covered here
at the unit level plus by the existing `tests/test_context_compact_mode.py`
suite exercising the real rendering path end to end.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.plugins import resolve_plugin_compact  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402


def test_zcode_and_kimicode_forced_full_under_compact():
    pc = load_providers_config(REPO_ROOT)
    assert resolve_plugin_compact(True, [pc["ZCode"]]) is False
    assert resolve_plugin_compact(True, [pc["KimiCode"]]) is False
    # Claude has a native rules dir -> compact honoured
    assert resolve_plugin_compact(True, [pc["Claude"]]) is True
    # Opencode has the skills capability -> lazy channel -> compact honoured
    assert resolve_plugin_compact(True, [pc["Opencode"]]) is True
    # shared AGENTS.md mixing Opencode + ZCode -> convergence-safe full
    assert resolve_plugin_compact(True, [pc["Opencode"], pc["ZCode"]]) is False
