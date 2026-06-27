# Prompt Optimization Report: `docker.md`

**Target File:** `agents/1-generic/docker.md`
**Current Version:** 1.4.2
**Evaluator:** Prompt-Engineer Agent

## 1. Executive Summary
The `docker.md` template is well-structured and functional but contains significant opportunities for token reduction and streamlining (Verschlankung). By applying "Context Engineering" and "Prompt Compression" best practices, we can reduce the token footprint (lowering latency and cost) without degrading the agent's capability or violating the `agent-meta` framework rules. 

## 2. Analysis & Optimization Findings

### 2.1. Eradication of Cosmetic Tokens (Relevance Filtering)
- **ASCII Art:** The "Startup-Anzeige" section uses a large ASCII art box. LLMs process these as numerous individual tokens, providing zero functional value.
- **Alignment Spaces:** The "Diagnosebefehle" section uses dozens of consecutive spaces to align comments on the right side. These spaces consume unnecessary tokens.

### 2.2. Compression of Code Examples (Verbosity Control)
- **Init-Container Script:** The bash script in the `init-binaries` compose block is verbose. It can be written as a more compact one-liner or shortened by removing excessive logging (`echo "Done!"`).
- **Test-Stack Boilerplate:** The `Dockerfile.test` and `docker-compose.yml` examples contain empty lines and standard boilerplate that the LLM already knows. We can reduce these to the absolute essentials (the specific bindings, environments, and commands).

### 2.3. Structural Prompting & Conciseness
- **Conversational Prose:** Phrases like "Du bist der Docker-Agent..." and "Bei jedem Neuaufsatz (besonders nach `down --volumes`) IMMER ausgeben:" can be condensed into strict directives (e.g., `Persona: Docker-Agent für {{PROJECT_NAME}}` or `Trigger: Neuaufsatz -> Output: ...`).
- **Redundant Separators:** The repeated use of `---` markdown separators is visually nice for humans but unnecessary for the LLM's parsing logic.

### 2.4. Advanced Context Engineering (Latency Optimization)
- **Output Shaping:** The prompt lacks a strict directive forcing the model to be concise in its general responses. Adding a "Verbosity Control" constraint (e.g., "Antworte extrem prägnant, nur Code oder Befehle, keine Prosa") will speed up generation.
- **XML Tagging:** Wrapping distinct sections (like commands, checklists, rules) in XML tags (e.g., `<diagnostics>`, `<checklists>`) helps the model parse the contract more strictly and reliably, matching 2026 Context Engineering standards.

## 3. Specific Refactoring Proposals

### Proposal 1: Streamline Startup-Anzeige
**Before:**
```text
╔════════════════════════════════════════════════════════════════╗
║            ✅ DOCKER STACK NEUGESTARTET                        ║
╚════════════════════════════════════════════════════════════════╝
🌐 App-URL:
```
**After (Token Optimized):**
```text
> **✅ DOCKER STACK NEUGESTARTET**
🌐 App-URL: {{APP_URL}}
```

### Proposal 2: Compress Diagnosebefehle
**Before:**
```bash
docker ps -a | grep {{CONTAINER_NAME}}                              # Status
docker logs {{CONTAINER_NAME}} --tail 100                           # Logs (100)
```
**After (Space Removed):**
```bash
docker ps -a | grep {{CONTAINER_NAME}} # Status
docker logs {{CONTAINER_NAME}} --tail 100 # Logs (100)
```

### Proposal 3: Optimize Test-Stack compose
Merge and compress the YAML structure.
**After (Compressed):**
```yaml
services:
  test-runner:
    build: { context: ../.., dockerfile: tests/docker/Dockerfile.test }
    volumes: ["../../src:/app/src:ro", "../../tests:/app/tests:ro"]
    environment: [NODE_ENV=test]
    command: [{{TEST_COMMAND}}]
```
*(LLMs understand JSON-like inline YAML perfectly, saving massive vertical token space).*

### Proposal 4: Consolidate Rules & Don'ts
Combine the explicit "Don'ts" and Add "Verbosity Control" directly above the Anti-Recursion Guard to leverage Recency Bias.
**Addition:**
```markdown
## Constraints & Output Shaping
- **Verbosity:** Antworte extrem prägnant. Minimiere Erklärungen, maximiere Code/Befehle.
- **Don'ts:** KEIN `compose up` ohne Build, KEINE hardcodierten Secrets, KEIN `down --volumes` ohne User-Warnung.
```

## 4. Conclusion & Next Steps
By applying these changes, the prompt's token size can be reduced by ~20-30%, leading to faster response times and lower API costs for every invocation of the Docker agent. 

**Recommended Action:**
1. Apply the token reduction strategies directly to `agents/1-generic/docker.md`.
2. Update the frontmatter `version` to `1.5.0` (as structural and instruction density changes are significant).
3. Run `python scripts/sync.py` to propagate the changes across the `agent-meta` ecosystem.
