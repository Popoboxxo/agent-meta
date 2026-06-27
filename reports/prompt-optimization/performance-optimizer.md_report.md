# Prompt Optimization Report: `performance-optimizer.md`

## 1. Executive Summary
**Agent:** `performance-optimizer`
**Current State:** 267 lines, ~9.2 KB
**Optimization Potential:** High (estimated 40-50% token reduction)
**Goal:** Verschlankung (Streamlining) without losing functionality, adhering to `prompt-engineer` and `agent-meta` guidelines.

The current prompt is well-structured but overly verbose. It spends a significant amount of tokens explaining basic Computer Science concepts (like Big-O notation and standard bottleneck indicators) which modern LLMs already deeply understand. Additionally, it uses a massive 65-line JSON example for output definition and contains redundant constraint sections.

## 2. Analysis & Findings (Based on `prompt-engineer` Practices)

### Finding 1: Redundant "Common Sense" Knowledge (Relevance Filtering)
The prompt includes large tables explaining standard concepts:
- **Big-O Komplexitätsanalyse:** Explains that O(1) is good and O(n²) is bad.
- **Bottleneck-Identifikation:** Explains that High RAM means Memory Leaks.
*Evaluation:* Modern LLMs possess this knowledge natively. Supplying it consumes input tokens and context window space without adding behavioral value. 

### Finding 2: Bloated Output Definition (Output Shaping)
The `JSON Output Schema — Performance-Bericht` section provides a 65-line instantiated JSON example. 
*Evaluation:* Generating large JSON objects is slow (high latency). Providing huge examples costs input tokens. A compact TypeScript interface or a minimal YAML/JSON structure is much more token-efficient for both input and output.

### Finding 3: Fragmented Constraints (Latency & Attention Optimization)
There are multiple sections enforcing the same rules:
- `Grundprinzipien` (lines 34-53)
- `Warnung: Keine funktionalen Änderungen` (lines 222-237)
- `Don'ts` (lines 239-247)
*Evaluation:* Spreading constraints across the prompt dilutes the LLM's attention. Consolidating them at the end of the prompt (High-Attention Zone) improves adherence and saves tokens.

### Finding 4: Empty Templates
The `Before/After-Vergleichsmetriken` table is a layout of empty fields.
*Evaluation:* This does not guide the LLM effectively; a simple instruction of which metrics to track is sufficient and more compact.

## 3. Actionable Optimization Proposals

### Proposal 1: Replace CS Knowledge with Directives
Remove the extensive tables for "Big-O Komplexitätsanalyse" and "Bottleneck-Identifikation". Replace them with a single, dense instruction block.
**Before (approx 40 lines):** Detailed tables explaining O(1) to O(n!).
**After (3 lines):** 
> "Analysiere Big-O Komplexität und Ressourcen-Profile (CPU, Mem, I/O, DB). Optimiere kritische Pfade (>= O(n²)) rigoros auf O(n log n) oder besser, basierend auf Pareto-Prinzip."

### Proposal 2: Compress the JSON Output Schema
Replace the huge JSON example with a compact JSON schema or TypeScript interface, and instruct the model to omit empty fields.
**After (Compact Format):**
```typescript
// Output Format: JSON
interface PerfReport {
  id: string; // e.g. PERF-001
  baseline: { latency_p95: number, rps: number, cpu_pct: number, mem_mb: number };
  bottlenecks: Array<{ loc: string, before: string, after: string, fix: string }>;
  metrics_after?: { latency_p95: number, cpu_pct: number };
  functional_change: false; // MUST be false
}
```
*Impact:* Saves ~50 lines of input tokens and speeds up generation time by enforcing shorter output keys.

### Proposal 3: Consolidate "Don'ts" and Constraints
Merge `Grundprinzipien`, `Warnung`, und `Don'ts` into a single, high-impact `<constraints>` block placed near the end of the file.

**Draft:**
```xml
<constraints>
- NIEMALS funktionales Verhalten oder API-Verträge ändern (Gleicher Input -> Gleicher Output).
- KEINE Optimierung ohne Profiling-Daten und Vorher/Nachher-Messung.
- BIG-O FIRST: Algorithmische Komplexität vor Mikro-Optimierungen.
- Jede Änderung erfordert einen erfolgreichen Regressionstest.
</constraints>
```

### Proposal 4: Streamline Workflow
Convert the multi-phase `Arbeitsablauf` into a compact numbered list using symbols (Chain-of-Symbol pattern) to save space.

**Draft:**
```markdown
## Workflow
1. **Measure:** Baseline (Latenz, RPS, CPU/Mem) erfassen -> Top Bottlenecks identifizieren.
2. **Analyze:** Big-O berechnen -> Typ klassifizieren -> Impact vs. Aufwand abwägen.
3. **Fix:** Optimierung implementieren -> Regressionstests ausführen (Equivalence Check).
4. **Validate:** Delta messen -> Output als `PerfReport`-JSON generieren.
```

## 4. Conclusion
By implementing these changes, the `performance-optimizer` prompt can be reduced from 267 lines to approximately 100-120 lines. This will result in:
1. **Lower Token Costs:** Significant reduction in input context.
2. **Lower Latency:** Faster Time-To-First-Token (TTFT) and generation speed.
3. **Higher Accuracy:** Better prompt adherence due to consolidated constraints in high-attention zones.
4. **Framework Compliance:** Fully adheres to `agent-meta` and `prompt-engineer` guidelines.
