# Prompt Optimization Report: `ui-ux-designer`

## 1. Executive Summary
This report provides a streamlining (Verschlankung) evaluation of the `ui-ux-designer.md` agent template, adhering strictly to the `prompt-engineer.md` guidelines (OpenAI & Lakera Best Practices, Context Engineering 2026). The current template is highly verbose, utilizing token-heavy ASCII diagrams and fully populated JSON examples. By migrating to compact structural representations and TypeScript interfaces, we can achieve significant token reduction (estimated 40-50% reduction in system prompt size) without losing instructional fidelity or violating the `agent-meta` rules.

## 2. Current State Analysis
- **Token-Heavy Examples:** The template uses large, illustrative examples (ASCII wireframes, ASCII flowcharts, extensive YAML design systems, and a 90-line JSON schema). While human-readable, these consume a massive amount of context window and increase generation latency.
- **Redundancy:** The requirements for a screen specification are defined twice: once in a Markdown table (Section 1) and once in the massive JSON output schema.
- **Formatting:** Standard Markdown is used extensively. The `prompt-engineer` persona recommends XML tags (`<instructions>`, `<output>`) for strict Handoffs and Contract-first APIs to improve structural parsing.

## 3. Optimization Proposals (Actionable Insights)

### A. Remove ASCII Art & Visual Diagrams (Structured Prompting)
LLMs do not need visual ASCII layouts to understand structure. ASCII art consumes many tokens due to spacing and pipe/box characters.
**Action:** Replace the ASCII wireframe and User Journey map with compact textual notations.
*Before (20+ lines):*
```text
┌─────────────────────────────────────────────────┐
│  HEADER: Logo                    [User] [Logout] │
...
```
*After (2-3 lines):*
```text
- Layout: [Header: Logo, User, Logout] | [Sidebar: Nav] + [Main: Content Grid] | [Footer]
- Journey: SCR-001(Landing) -> [Register] -> SCR-002(Form) -> SCR-003(Dashboard)
```

### B. Compress the JSON Output Schema (Verbosity Control)
The 90-line JSON example is fully populated with dummy data (e.g., "user@example.com", "••••••••"). This encourages the LLM to output verbose responses and wastes input tokens.
**Action:** Replace the populated JSON object with a compact TypeScript interface or a stripped-down JSON schema.
*After (Compact Schema example):*
```typescript
interface UISpec {
  ui_spec_id: string;
  project_context: string;
  screens: {
    screen_id: string; // e.g., SCR-001
    screen_name: string;
    states: string[];
    layout: { header: string; content: string; footer: string };
    components: { type: string; variant: string; label: string; action?: string }[];
    req_references?: string[]; // If DOD_REQ_TRACEABILITY active
  }[];
  design_system: { colors: any; typography: any; spacing: any };
  user_journeys: { journey_name: string; steps: string[] }[];
}
```
*Benefit:* Saves ~60-70 lines, speeds up parsing, and defines a strict API-like contract.

### C. Consolidate Redundant Specification Sections
Section 1 ("UI-Spezifikation") lists table fields that are strictly duplicated in the JSON Schema section.
**Action:** Merge Section 1 directly into the Output Schema definition. State clearly: "Return your UI specification strictly matching this schema" and eliminate the markdown table in Section 1.

### D. Implement XML Tagging (Context Engineering)
To align with "Advanced Multi-Agent & Latency Optimization", segment the prompt using XML tags. This creates clear API contracts between agents.
**Action:** Wrap sections in semantic tags:
- `<role_definition>`
- `<responsibilities>`
- `<output_contract>` (Replacing the markdown headers for the schema)
- `<constraints>` (For the Don'ts and Anti-Recursion Guard)

### E. Optimize YAML Examples
The Design System section (Section 3) has extensive YAML for typography and colors.
**Action:** Truncate the examples to just the necessary nesting structure. Tell the LLM to expand as needed.
*After:*
```yaml
colors:
  primary: { main: "#HEX", light: "#HEX", dark: "#HEX" }
  semantic: { success: "#HEX", error: "#HEX" } # Include warning/info as needed
typography:
  scale:
    h1: { size: "2rem", weight: 700 }
    body: { size: "1rem", weight: 400 } # Expand to h2-h6, small, caption
```

## 4. Proposed Streamlined Workflow Section
Instead of long textual descriptions for workflows, use "Chain-of-Symbol" or highly compact step-by-step lists to minimize token usage:
```xml
<workflow>
1. Identify REQ-ID -> 2. Review {{PROJECT_CONTEXT}} -> 3. Map Journey -> 4. Define Layout/Components -> 5. Document Spec matching `<output_contract>`.
</workflow>
```

## 5. Summary of Benefits
- **Latency Reduction:** Fewer input tokens mean faster time-to-first-token (TTFT).
- **Cost Reduction:** Removing ~100-150 lines of redundant examples significantly lowers input costs.
- **Strict Adherence:** Transitioning to TS Interfaces and XML tagging creates a stronger API-contract, reducing hallucinations and making agent handoffs more robust.
