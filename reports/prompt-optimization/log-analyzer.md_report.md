# Prompt Optimization Report: `log-analyzer.md`

## 1. Current State Analysis
- **Target File:** `agents/1-generic/log-analyzer.md`
- **Current Token Load:** ~5.8 KB (approx. 1200-1500 tokens).
- **Structure:** Good baseline structure with tables and explicit steps, but contains conversational padding ("Du bist...", "Reduziert Token-Verbrauch massiv") and fragmented sections (e.g., "Modus wählen" and "Tiefer Modus" are separated).
- **Implicit LLM Knowledge:** The prompt explicitly lists standard log formats (Step 3: syslog, Docker, Python traces) which modern LLMs already recognize natively, wasting context window.

## 2. Optimization Strategy 
Based on the `prompt-engineer` practices (Prompt Compression, Context Engineering 2026):
- **Structured Prompting:** Convert conversational text into dense Key-Value pairs and telegraphic commands.
- **Redundancy Elimination:** Merge `--deep` mode description directly into the main workflow.
- **Relevance Filtering:** Remove the verbose "Format erkennen" table.
- **High-Attention Zones:** Consolidate constraints (Don'ts) and Anti-Recursion rules at the absolute end of the file.

## 3. Specific Proposals & Before/After Examples

### Proposal 1: Compress Persona & Goal
*Rationale: Conversational filler uses tokens without adding steering value.*
**Before:**
```markdown
Du bist der **Log-Analyzer** für {{PROJECT_NAME}}.
Du analysierst Logs aus Dateien, Verzeichnissen oder Copy-paste-Input — und lieferst strukturierte Findings mit Severity, Root-Cause-Hypothese und klarer Delegations-Empfehlung.
```
**After:**
```markdown
**Role:** Log-Analyzer (`{{PROJECT_NAME}}`)
**Task:** Analyze logs (file/dir/paste) -> Output structured findings (Severity, Root-Cause, Delegation).
```

### Proposal 2: Consolidate Modes
*Rationale: Spreading mode definitions across the file causes context fragmentation.*
**Action:** Replace the `Modus wählen` table and the `Tiefer Modus` section with a single, dense definition at the top:
```markdown
**Modes:** 
- `--quick` (Default): Fast clustering & reporting (Steps 1-6).
- `--deep`: Includes code/config search and web research (Steps 1-7).
```

### Proposal 3: Streamline Workflow Steps
*Rationale: Reduce reasoning effort and token count by making instructions punchy.*

**Step 1 (Discovery):** Convert to a compact list.
```markdown
### 1. Discovery
- **Path:** `glob "**/*.log"`
- **Auto:** `/var/log/*`, `~/.homeassistant/*.log`, `./log*/*.log`, `journalctl -n 500`, `docker ps`
- **Paste:** Goto 2.
```

**Step 2 (Clustering):** Keep the bash snippet but drop the narrative "Reduziert Token-Verbrauch massiv...".
```markdown
### 2. Frequency-Clustering (Mandatory Pre-Analysis)
Run this to cluster identical errors (analyze only count ≥ 2 or HIGH+ severity):
[... bash snippet ...]
```

**Step 3 (Format Recognition):** Drop the entire table. Replace with:
```markdown
### 3. Parse 
Auto-detect log format natively (syslog, docker, python, etc.).
```

**Step 6 & 7 (Delegation & Deep Analysis):** Compress tables into single-line mappings.
```markdown
### 6. Delegation Targets
`feedback` (Issue) | `developer` (Fix) | `security-auditor` (Auth/Injection) | `requirements` (New req) | `orchestrator` (Coordination)

### 7. Deep Analysis (`--deep` only)
`Grep` codebase for affected module/class, check configs, `WebSearch` exact error strings.
```

### Proposal 4: Output Shaping (Findings Report)
*Rationale: Ensure strict adherence to the output contract.*
Keep the markdown block for `## Finding #N` as it serves as an excellent Few-Shot Output Template. 

### Proposal 5: Consolidate Constraints (High-Attention Zone)
Merge `Don'ts` and `Anti-Recursion Guard` into a strict `<rules>` or `## Rules & Constraints` block at the very end of the file. Remove the conversational explanations in the Anti-Recursion table and stick to the hard mapping.

## 4. Expected Impact
- **Token Reduction:** Prompt size reduced by ~30-40%.
- **Latency Reduction:** Faster generation due to minimized context parsing and clear, telegraphic instructions.
- **Framework Compliance:** Remains 100% compliant with `agent-meta` rules (Variable injection, Anti-Recursion, DoD).

## 5. Next Steps
Apply these changes to `agents/1-generic/log-analyzer.md` and bump the `version` in the frontmatter to `1.2.0` (Minor release for optimization and structure refinement).
