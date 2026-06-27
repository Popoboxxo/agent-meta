# Prompt Optimization Report: `api-specialist.md`

**Date:** 2026-06-27
**Target:** `/home/dduchrow/Repos/agent-meta/agents/1-generic/api-specialist.md`
**Reviewer:** `template-prompt-engineer`
**Objective:** Streamlining, token reduction, and latency optimization without functionality loss.

## 1. Findings & Current State
The `api-specialist.md` prompt is well-structured and aligns well with the agent-meta framework, but it suffers from significant token bloat in its examples and instructions. 

**Key Issues Identified:**
- **Bloated OpenAPI Template (~75 lines):** The prompt includes a massive boilerplate YAML example to demonstrate OpenAPI 3.0.3. LLMs natively understand OpenAPI syntax perfectly. Providing a full example wastes context tokens and increases caching costs.
- **Verbose JSON Output Schema (~27 lines):** The output report is defined via a verbose JSON instance. JSON formatting takes up unnecessary tokens compared to more compact schema definitions (like TypeScript interfaces).
- **Narrative Workflows:** The "Zuständigkeiten" and "Arbeitsablauf" sections use narrative sentences and spaced-out tables, which can be compressed using a "Chain-of-Symbol" or ultra-compact list approach.
- **Redundant Global Rules:** Sections like "Conventional Commits" and "Branch-Guard" duplicate information likely already handled by global framework rules (e.g., `AGENTS.md` rules). Even if necessary for context, they are too long.

## 2. Specific Optimization Proposals & Actionable Insights

### Proposal A: Compress the OpenAPI Template (Token Reduction: ~70%)
**Action:** Remove the standard OpenAPI boilerplate. Replace it with a minimal "Requirements Skeleton" that only enforces project-specific constraints (e.g., the custom `Error` schema and versioning rules).

*Optimized Example:*
```yaml
# OpenAPI 3.0.3 Skeleton (nur für spezifische Projekt-Standards)
openapi: "3.0.3"
info: { title: "{{PROJECT_NAME}} API", version: "1.0.0" }
# [Paths & normale Operations wie üblich definieren]
components:
  schemas:
    Error: # Zwingendes Error-Format für alle APIs
      type: object
      required: [code, message]
      properties:
        code: { type: string }
        message: { type: string }
        details: { type: object }
        traceId: { type: string, format: uuid }
```

### Proposal B: Use TypeScript Interfaces for Output Schema (Token Reduction: ~40%)
**Action:** Replace the verbose JSON report example with a compact TypeScript interface. LLMs parse TS interfaces highly efficiently, and it enforces strict typing while drastically reducing prompt length.

*Optimized Example:*
```typescript
// Output Format (JSON):
interface ApiSpecReport {
  spec_file: string;
  spec_version: string;
  protocol: "REST" | "gRPC" | "GraphQL";
  endpoints: Array<{ method: string; path: string; operation_id: string; breaking_change: boolean }>;
  schemas_defined: string[];
  conformance_status: "valid" | "invalid";
  recommendations: string[];
}
```

### Proposal C: Condense Workflow via Chain-of-Symbol & Keyword Lists
**Action:** Flatten the "Zuständigkeiten" and "Arbeitsablauf" into dense, high-information-density bullet points.

*Optimized Example:*
```markdown
## Workflow & Zuständigkeiten
1. **Analyse:** REQ-IDs prüfen -> Ressourcen identifizieren -> Protokoll klären (REST für CRUD, gRPC für Perf, GraphQL für flexible Queries).
2. **Design:** OpenAPI YAML (Primary Truth) -> Req/Res/Error Schemata definieren -> Validieren.
3. **Review:** User-Freigabe -> Migrationsplan (bei Breaking Changes: Feld-Löschung = Major, Optional-Feld = Minor) -> Commit.
4. **Verträge:** Abstimmung mit `se-interface-mgr` für Systemgrenzen.
```

### Proposal D: Streamline Boilerplate & High-Attention Zones
**Action:** 
1. Condense the "Conventional Commits" and "Branch-Guard" sections into single lines.
2. Move the `Don'ts` and the `Anti-Recursion Guard` to the absolute end of the file to leverage the "Recency Bias" (High-Attention Zone), ensuring the LLM strictly adheres to constraints.

*Optimized Example:*
```markdown
## Constraints & Don'ts
- **Commits:** `feat(api): ...`, `feat!(api): ...` (Breaking), `fix(api): ...`. Inkl. REQ-ID falls `{{DOD_REQ_TRACEABILITY}}`.
- **Branching:** Niemals auf `main`. Nutze `feat/api-*` oder `fix/api-*`.
- **DON'T:** Keine Implementierungsdetails in Spec.
- **DON'T:** Keine Breaking Changes ohne Major-Bump/Migrationsplan.
- **DON'T:** Keine Spec ohne Validierung committen.

## Anti-Recursion Guard
**Du bist Worker-Agent.** NIEMALS Aufgaben an `orchestrator` zurückdelegieren (weder via Tool noch Text). Bist du blockiert, frage den User.
```

## 3. Expected Impact
- **Token Efficiency:** ~35-45% reduction in total prompt tokens.
- **Latency:** Faster time-to-first-token (TTFT) due to reduced input length.
- **Accuracy:** Better adherence to constraints due to cleaner structure and optimized placement of "Don'ts" at the end of the prompt.
