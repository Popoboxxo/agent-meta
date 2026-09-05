---
name: shared-context-file-strategy-convergence
description: Providers sharing a context_file must use ONE render strategy; #638 union only covers within-_build_managed_block, cross-strategy divergence needs dispatch guard
metadata:
  type: project
---

Providers pointing `context_file` at the SAME physical file (e.g. AGENTS.md shared by Opencode/Gemini/Codex/ZCode/KimiCode) must render a byte-identical managed block, else a lone `sync.py --check` reports a permanent, unfixable false "out of sync" (#638 oscillation).

**Two independent convergence layers — both required:**
1. WITHIN `_build_managed_block` (context.py): the #638 union logic (`_shared()` join, union rule/tool inclusion) makes content identical across sharers that ALL use the embedded-rules strategy.
2. ACROSS strategies (the gap this session fixed): dispatch in `sync_context_for_provider` routes by per-provider capability. A provider with `context-managed-block` renders a SMALLER block (`_update_managed_html_block`, no embedded rules) than a sharer with `context-embedded-rules` (`_build_managed_block`). Same file, two contents → oscillation. Fix = `_shares_context_with_embedded_rules()` guard: any provider sharing a context_file with an embedded-rules provider is routed through the Opencode/embedded-rules strategy (superset). Generic — keys off the shared-file capability set, no hardcoded provider name.

**Why:** #638 was originally verified only against Opencode+Gemini (both embedded-rules), so the cross-strategy case never appeared. Adding Codex/ZCode/KimiCode with `context-managed-block` (V-plan config) reopened it. Same "generic fix that wasn't quite generic" class as the recurring py3.9 bug.

**How to apply:** When adding any provider that shares an existing `context_file`, it inherits the strategy of the embedded-rules sharer automatically now. Convergence check: 3x `sync.py --check` must yield identical AGENTS.md SHA + zero `AGENTS.md ... UPDATE` actions; plus `tests/test_agents_md_shared_context_convergence.py` (its `_AGENTS_MD_SHARERS` tuple must list every sharer). Related: [[multi-provider-three-file-invariant]], [[tier-resolution-missing-key-silent-empty]].
