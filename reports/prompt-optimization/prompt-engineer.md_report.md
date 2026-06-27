# Prompt Optimization Report: `prompt-engineer.md`

## 1. Objective
Perform a rigorous evaluation of the `prompt-engineer` generic template (`1-generic/prompt-engineer.md`) to identify opportunities for streamlining (Verschlankung) and token reduction, thereby reducing latency and inference costs. The optimization must strictly preserve all `agent-meta` framework rules and the agent's functionality.

## 2. Current State Analysis
- **File size:** 204 lines, ~12.7 KB.
- **Characteristics:** Highly informative, but suffers from "instruction bloat". The prompt explains standard prompt engineering concepts to an LLM that already understands them.
- **Irony:** The prompt explicitly advises to use "Structured Prompting" and avoid "erzählendem Fließtext", yet the prompt itself is largely written in verbose prose.
- **Critical Requirements:** Framework-specific rules (Schichten-Architektur, Composition, Platzhalter) are correctly defined but can be significantly compressed.

## 3. Core Optimization Strategies

### A. Remove Implicit Knowledge Explanations
LLMs do not need to be taught *what* "Chain-of-Thought" or "Lost in the Middle" means; they only need to be instructed to *apply* these principles.
* **Action:** Strip all definitions and rationales. Transform explanatory sentences into direct imperatives.

### B. Shift to High-Density Structured Prompting
Convert verbose paragraphs into dense key-value pairs or concise bullet points.
* **Action:** Replace conversational phrases (e.g., "Um Token-Kosten zu senken und die Performance (Latenz) zu verbessern, wende diese Best Practices für kompaktere Prompts an:") with strict headers (e.g., "## 3. Prompt Compression").

### C. Condense `agent-meta` Framework Rules (Section 5)
The rules in Section 5 are critical invariants but can be expressed with 50% fewer tokens by removing filler words and formatting them as compact reference lists.
* **Action:** Use symbol-chaining and strict list formats (e.g., `1-generic: Neutral, NO provider names` instead of "Darf niemals Provider-Namen (...) enthalten").

## 4. Specific Section-by-Section Proposals

### Section 1 & 2: OpenAI & Lakera Best Practices
**Current:** ~25 lines of explanatory text.
**Proposed:** Dense bullet points:
- **Persona & Intent:** Spezifische Persona setzen, Tasks in Sub-Tasks zerlegen.
- **Delimiters:** XML-Tags (`<instructions>`, `<context>`) zur Trennung von System-Prompt und User-Input nutzen (Prompt Injection Prevention).
- **CoT & Tools:** `Chain-of-Thought` erzwingen (`<thought>`), Tools aktiv priorisieren.
- **Constraints:** Strikte "Don'ts" und Output-Formate (JSON) definieren.

### Section 3 & 4: Compression & Advanced Context Engineering
**Current:** ~40 lines explaining APO, Latency, and Verbosity.
**Proposed:**
- **Structured Prompting:** Markdown/Key-Value statt Fließtext.
- **Verbosity Control:** Kurze Outputs erzwingen ("Telegram-Stil", "Nur Code").
- **High-Attention Zones:** Constraints ans absolute Ende setzen.
- **Context Management:** Unnötigen Kontext filtern, Handoffs als strikte API-Verträge (XML/JSON) definieren.
- **Latency:** Token-Generierung minimieren (z.B. Chain-of-Symbol `->` statt CoT-Prosa).

### Section 5: Agent-Meta Framework Mastery
**Current:** Very verbose prose describing the framework.
**Proposed:**
- **Schichten:**
  - `1-generic`: Neutral (LLM/Model). Keine Provider-Namen/Pfade.
  - `2-platform`: Provider-Overrides. Frontmatter: `based-on: "1-generic/<rolle>.md@<version>"`.
  - `3-project`: Projekt-spezifisch. YAML Composition (`extends:`, `patches: [append-after, replace, delete]`).
- **Platzhalter:** Zwingend `{{GROSS_MIT_UNTERSTRICH}}` (für `sync.py`).
- **A2A Handoffs:** `delegation_depth <= 10`, `payload.t <= 300` Zeichen, `source != target`. Kein "Du bist..." in Payloads.
- **Versioning:** Major (Verhalten/Pflicht), Minor (Optional/Scope), Patch (Typo).
- **Lifecycle:** Branch-Pflicht (>1 Datei), Conventional Commits, `gh issue close`.

### Section 6: Workflow
**Current:** Conversational phases.
**Proposed:** Strikte Checkliste:
1. **Analyse:** Ziel, Persona, Tools, Schicht (1/2/3).
2. **Draft:** Frontmatter → Intro → Steps → Don'ts → Handoff.
3. **Review:** Isolation OK? Platzhalter OK? CoT integriert? Injection-sicher?

### Anti-Recursion Guard
**Proposed:**
`**Du bist Worker-Agent. NIEMALS an orchestrator oder Worker zurückdelegieren.**`
`Verboten: @orchestrator, Task() an orchestrator. (Hard Reject)`

## 5. Projected Impact
By implementing these changes, the prompt can be reduced from ~12.7 KB to approximately 5-6 KB (a **~50% token reduction**). This will:
1. **Decrease Latency:** Faster Time-to-First-Token (TTFT) and reduced output generation times.
2. **Lower Inference Costs:** Significantly fewer input tokens per execution.
3. **Increase Instruction Adherence:** Denser prompts suffer less from the "Lost in the Middle" phenomenon, ensuring the model adheres more strictly to the `agent-meta` framework rules.
