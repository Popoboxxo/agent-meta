# Best Practice Audit — agent-meta (July 2026)

**Date:** 2026-07-12  
**Branch:** fix/best-practice-audit  
**Scope:** Orchestration patterns, A2A gates, quality enforcement, resilience, context management  
**Sources:** `docs/analysis/274-industry-bestpractices.md`, `docs/analysis/276-architecture-robustness-audit.md`

---

## Implementation Status

| Priority | Item | Status | File(s) | Notes |
|----------|------|--------|---------|-------|
| P0 | Provider-Limits in A2A-Gates | Done | `rules/1-generic/a2a-delegation-gates.md` | Commit b2cc84f |
| P0 | Execution-Trace-Isolation in A2A-Gates | Done | `rules/1-generic/a2a-delegation-gates.md` | Commit b2cc84f |
| P1 | Tool-Risk-Rating in orchestrator.md | Done | `agents/1-generic/orchestrator.md` | New section "## Tool Risk Classification" |
| P1 | DoD-as-Gate | Done (concept) | `docs/concepts/active/circuit-breaker-dod-gate-judge-pattern.md` | `hooks/dod-push-check.sh` not found — gap documented |
| P2 | Instruction-Bleed in agent-meta-conventions | Done (uncommitted) | `rules/2-platform/agent-meta-conventions.md` | "Composition-Risiko: Instruction Bleed" section |
| P2 | Circuit-Breaker / Token-Budget-Guard | Done (concept) | `docs/concepts/active/circuit-breaker-dod-gate-judge-pattern.md` | Implementation deferred |
| P2 | Trace-Isolation in A2A-Gates | Done | `rules/1-generic/a2a-delegation-gates.md` | Commit b2cc84f |
| P2 | disallowedTools / effort in 2-platform | Not recommended | — | See evaluation below — whitelist is sufficient; effort violates provider-agnosticity |
| P3 | Judge/Validator-Agent Pattern | Done (concept) | `docs/concepts/active/circuit-breaker-dod-gate-judge-pattern.md` | Context isolation model documented |

**Orchestrator version bump:** `agents/1-generic/orchestrator.md` 6.5.0 → 6.6.0 (uncommitted, matches content additions)

---

## Deferred Items (from industry best practices analysis)

Items from `docs/analysis/274-industry-bestpractices.md` not addressed in this cycle:

| Area | Gap | Priority |
|------|-----|----------|
| Context | Rolling Summary / auto-compression | Medium |
| Context | RAG-based selective context loading | Low |
| A2A | Agent Card / Capability Advertisement | Medium |
| A2A | Streaming protocol (SSE) for long-running tasks | Low |
| A2A | `trace_context` propagation in all agent templates | High |
| A2A | Google A2A / AutoGen Protocol interoperability | Low |
| Resilience | Exponential backoff (currently count-based retry only) | Medium |
| Resilience | Session-level retry budget | Low |
| Resilience | Dead Letter Queue for failed tasks | Low |
| Observability | Structured Decision Logging (persistent) | High |
| Observability | OpenTelemetry export | Medium |
| Observability | Token usage per agent (only envelope overhead tracked) | Medium |

---

## Current 2-platform Architecture

### Files Analyzed

| File | Type | Based-On | Tools Count |
|------|------|----------|-------------|
| agent-meta-developer.md | extends + patches | 1-generic/developer.md@2.5.2 | 8 |
| sharkord-developer.md | extends + patches | 1-generic/developer.md@2.3.0 | 8 |
| agent-meta-claude-expert.md | 2-platform override | 1-generic/provider-expert.md@1.0.0 | 9 |
| homeassistant-developer.md | extends + patches | 1-generic/developer.md@2.3.0 | 8 |

**Pattern:** All 2-platform files explicitly define `tools:` list in frontmatter. Tools are inherited from base template or extended by platform needs.

### Tool Whitelisting Strategy

**1-generic/developer.md tools:**
```yaml
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - TodoWrite
  - Agent
```

**2-platform overrides:** Inherit or extend base tools as needed.
- **agent-meta-developer.md**: Same 8 tools (no additions or removals)
- **sharkord-developer.md**: Same 8 tools
- **homeassistant-developer.md**: Same 8 tools
- **agent-meta-claude-expert.md**: Adds WebFetch → 9 tools (specialized for provider platform)

**Pattern:** Tools are whitelisted explicitly; no platform file currently uses `disallowedTools`.

---

## disallowedTools Evaluation

### Current Usage
- **Grep result:** 0 files in 2-platform/ use `disallowedTools`

### Assessment

**Not Recommended for 2-platform overrides.**

**Rationale:**

1. **Explicit whitelist is sufficient**: Each 2-platform file specifies exactly which tools are available via `tools:` list. This is a positive whitelist — only listed tools are permitted.

2. **No provider incompatibility detected**: All analyzed 2-platform files use tools that are universally available (Bash, Read, Write, Edit, Glob, Grep, TodoWrite, Agent). Only WebFetch was added for specialized use case (claude-expert).

3. **Composition clarity**: Using only `tools:` keeps the override file clean. Adding `disallowedTools` would introduce negative constraints ("don't use X"), complicating the semantics when the positive whitelist already defines the boundary.

4. **Rule precedence**: If a 1-generic template lists tools A, B, C and a 2-platform override specifies `tools: [A, C]`, the result is clear — B is implicitly unavailable. Adding `disallowedTools: [B]` is redundant.

**Conclusion:** Keep status quo. Use only explicit `tools:` whitelist in 2-platform overrides.

---

## Effort Evaluation

### Current Usage
- **Grep result:** 0 files in 2-platform/ use `effort`

### Context: Model Selection & Effort Control

**role-defaults.yaml model tiers:**
```yaml
developer:
  model: powerful        # Strong model for feature implementation
  
junior-developer:
  model: fast            # Cheap, fast model for trivial changes
  
senior-developer:
  model: max             # Maximum capability for complex work
```

**Effort in Provider Context:**
- Some providers (e.g., Claude with o1/o3 reasoning models) support `effort` settings
- `effort` is a model-specific, provider-specific setting
- Currently, role-defaults.yaml assigns **tier names** ("fast", "powerful", "max"), not specific model IDs

### Assessment

**Not Applicable for 2-platform overrides.**

**Rationale:**

1. **Tier-based model assignment**: role-defaults.yaml uses abstract tier names that translate to provider-specific models at sync time. A 2-platform file cannot assume a specific model is selected.

2. **Provider agnosticity**: 2-platform files must remain generic enough to work across providers (Claude, Gemini, Continue, etc.). Specifying `effort: extended` would only apply to providers that support extended thinking — incompatible with provider-agnostic architecture.

3. **Sync-time resolution**: Model selection (and thus effort settings) is resolved during `sync.py` execution when the target provider is known. This is a provider-specific injection, not a 2-platform composition concern.

4. **Separation of concerns**: 
   - **role-defaults.yaml** → Abstract tier ("powerful")
   - **Provider config** → Maps tier to specific model (e.g., claude-3-5-sonnet)
   - **3-project overrides or hooks** → Provider-specific tweaks (e.g., effort settings)

**Conclusion:** Effort control belongs in provider-specific layers (3-project or sync-time injection), not 2-platform overrides.

---

## Best Practice Recommendations

### For 2-platform Overrides

| Pattern | Status | Notes |
|---------|--------|-------|
| Explicit `tools:` whitelist | ✅ Current | Clear, unambiguous. Maintain. |
| `extends: "1-generic/<role>.md"` | ✅ Current | Good composition pattern. Maintain. |
| `patches:` for fine-grained changes | ✅ Current | Reduces duplication. Maintain. |
| `based-on:` version tracking | ✅ Current | Enables sync validation. Maintain. |
| `disallowedTools` | ❌ Not needed | Whitelist is sufficient. Don't add. |
| `effort` | ❌ Not applicable | Provider-specific, belongs elsewhere. Don't add. |

### Implementation Impact

**No changes required.**

Current 2-platform structure is sound. Adding `disallowedTools` or `effort` would:
- Add complexity without benefit
- Violate provider-agnosticity (effort case)
- Create false constraints (disallowedTools case)

---

## Files Audited

| File | Status | Reason |
|------|--------|--------|
| agents/2-platform/agent-meta-developer.md | ✅ | Composition pattern verified; no disallowedTools/effort needed |
| agents/2-platform/sharkord-developer.md | ✅ | Tool whitelist adequate; no special constraints |
| agents/2-platform/agent-meta-claude-expert.md | ✅ | WebFetch addition is appropriate; no effort needed |
| agents/2-platform/homeassistant-developer.md | ✅ | Domain-specific tools sufficient; no provider-specific settings |
| agents/2-platform/sharkord-release.md | ✓ | Reviewed for pattern consistency |
| agents/2-platform/homeassistant-documenter.md | ✓ | Reviewed for pattern consistency |
| agents/2-platform/homeassistant-log-analyzer.md | ✓ | Reviewed for pattern consistency |
| agents/2-platform/sharkord-docker.md | ✓ | Reviewed for pattern consistency |

**Legend:** ✅ = Detailed; ✓ = Pattern verified

---

## Conclusion

**The 2-platform override system is well-designed and does not require disallowedTools or effort fields.** The explicit tool whitelist (`tools:`) combined with role-defaults.yaml model tiers provides adequate control without unnecessary complexity.

**Recommendation:** Close audit without implementation changes. Document this finding for future contributors to avoid introducing these fields without clear justification.

---

**Report Prepared:** 2026-07-12  
**Audit Status:** Complete  
**Recommendation:** No implementation required
