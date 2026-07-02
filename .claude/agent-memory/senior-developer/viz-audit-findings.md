---
name: viz-audit-findings
description: Viz feature audit 2026-07-02 — three verified broken paths (delegate_out mismatch, viz-server.py import, literal \n injection)
metadata:
  type: project
---

Viz audit on `feat/prompt-modernization-poc` (2026-07-02), status: PARTIALLY functional. Verified broken paths, none fixed yet (audit was read-only):

1. **Event-type mismatch:** logging chain (prompt block, viz-logger.py enum, MCP tool) emits `delegate_out`; `build_session_state` (viz-report.py ~L169) and live-dashboard.html only consume `delegate` → delegation edges never render. `task_id` is logged but never evaluated.
2. **viz-server.py wrapper dead:** `from admin_server import ...` fails — file is `admin-server.py` (hyphen), no importlib workaround → every wrapper command exits with error.
3. **inject_viz_prompt_block literal `\n` bug** (scripts/lib/viz.py L783/L819): source has `"\\n\\n"` (escaped) instead of `"\n\n"` → generated agents get literal `\n\n## Visualization Reporting` text on one line. Latent only because this repo has `viz.enabled: false`.
4. docs/viz-event-schema.md is stale (documents `delegate` with from/to; missing delegate_out/task_id/a2a_* events) while viz-architecture.md describes delegate_out — docs contradict each other. viz-api.md matches code exactly.
5. Zero viz tests exist (`pytest -k viz` → 0 matched).

**Why:** recorded so the fixes can be picked up without re-auditing; user asked for status report only.

**How to apply:** if asked to "fix viz", start with items 1-3; they are independent, small, and each verified by direct execution. Related: [[model-id-canonical-source]] (same session).
