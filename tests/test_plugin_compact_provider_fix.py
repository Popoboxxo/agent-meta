"""ZCode/KimiCode now carry the `skills` capability (SPEC-PROVIDER-AUDIT-
OPENCODE-V2-2026-09-30, §2.1:161/§2.2:176), so like every registered provider
they have a lazy channel for full plugin content. Under project-wide compact
mode they receive the compact variant instead of being forced full.

Regression context: before `skills` was declared, ZCode/KimiCode had neither a
rules dir nor the skills capability, so compact mode had to force the FULL
embedded plugin content — otherwise the agent-hint was silently lost. The
capability data now mirrors the already-generated skills artifacts
(`skills_dir` non-null), which flips `provider_has_lazy_channel` to True.

The forced-full branch is still required for any provider that has BOTH no
native rules dir and no skills capability; no live provider is in that state
after the §2.1/§2.2 data fix, so it is covered with a synthetic shape below.

Note (Task 4 Step 2): the brief's integration-level variant of this test
depends on a `context.build_agent_hints_for_provider(...)` helper that does
not exist in the current `scripts/lib/context.py` -- the module only exposes
`_build_managed_block`, a private function entangled with SyncLog/variables
plumbing that isn't practical to call standalone for a single assertion.
Building that helper is out of scope for this surgical change (see task brief:
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

from lib.plugins import resolve_plugin_compact
from lib.providers import load_providers_config


def test_zcode_and_kimicode_have_lazy_channel_under_compact():
    pc = load_providers_config(REPO_ROOT)
    # §2.1/§2.2: both declare skills: true + 'skills' in ai-providers
    # capabilities -> lazy channel -> compact mode is honoured for them.
    assert resolve_plugin_compact(True, [pc["ZCode"]]) is True
    assert resolve_plugin_compact(True, [pc["KimiCode"]]) is True

    assert resolve_plugin_compact(True, [pc["Claude"]]) is True

    assert resolve_plugin_compact(True, [pc["Opencode"]]) is True

    assert resolve_plugin_compact(True, [pc["Opencode"], pc["ZCode"]]) is True
    assert resolve_plugin_compact(True, [pc["ZCode"], pc["KimiCode"]]) is True


def test_provider_without_lazy_channel_forces_full_under_compact():
    """Forced-full fallback is preserved for a provider that has neither a
    native rules dir nor the skills capability. No live provider is in that
    state after the §2.1/§2.2 data fix, so the branch is pinned synthetically
    (otherwise the convergence guard would lose its only regression coverage).
    """
    pc = load_providers_config(REPO_ROOT)
    bare = {**pc["ZCode"], "has_rules": False, "capabilities": []}
    assert resolve_plugin_compact(True, [bare]) is False
    assert resolve_plugin_compact(True, [pc["Opencode"], bare]) is False
