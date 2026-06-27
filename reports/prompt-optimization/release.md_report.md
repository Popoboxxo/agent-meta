# Prompt Optimization Report: `release.md`

**Agent:** prompt-engineer  
**Target:** `agents/1-generic/release.md`  

## 1. Executive Summary
An evaluation of `release.md` was conducted based on the advanced Context Engineering and Prompt Compression practices outlined in the `prompt-engineer` template. The current template is well-structured but suffers from redundancy, slightly wordy prose, and a violation of the `1-generic` framework rule (hardcoded technology specifics). By streamlining these areas, we can reduce token consumption and improve the agent's adherence to instructions without sacrificing capabilities.

## 2. Findings & Current State

1. **Violation of `1-generic` Abstraction:** 
   - Line 51 mentions `bun test`. As per `agent-meta` rules, `1-generic` templates must remain completely agnostic of specific platforms, languages, or testing frameworks.
2. **Redundancy between Workflow and Checklist:**
   - Section `2. Release-Workflow` and `4. Pre-Release Checklist` essentially describe the same lifecycle phase. This wastes tokens and splits the agent's attention.
3. **Verbose Persona & Prose:**
   - The intro uses conversational sentences ("Du bist der Release Manager für... Du koordinierst..."). Structured prompting (e.g., Key-Value) is more token-efficient.
4. **Anti-Recursion Guard Verbosity:**
   - The `Anti-Recursion Guard` is slightly verbose. As a standard inclusion, it can be tightened into a more compact format.

## 3. Specific Optimization Proposals

### Proposal 1: Fix `1-generic` Violation (Critical)
Replace the hardcoded `bun test` with a generic framework placeholder or generalized instruction.
**Current:**
`1. Tests grün?                → bun test (oder projektspezifisch)`
**Proposed:**
`1. Tests grün?                → {{TEST_COMMAND}}`

### Proposal 2: Merge Workflow and Checklist
Combine Section 2 and Section 4 into a single, authoritative `Release-Lifecycle` checklist to save tokens and provide a single source of truth.
**Proposed Structure:**
```markdown
## Release Lifecycle
Prüfe sequenziell vor jedem Release:
- [ ] 1. Tests grün (`{{TEST_COMMAND}}`)
- [ ] 2. DoD aller Features erfüllt (`validator` check)
- [ ] 3. CHANGELOG.md aktualisiert (Format siehe unten)
- [ ] 4. Version gebumpt (SemVer)
- [ ] 5. README.md & CODEBASE_OVERVIEW.md aktuell
- [ ] 6. Build erfolgreich (`{{BUILD_COMMANDS}}`)
- [ ] 7. Commit, Tag, Push via `git`-Agent durchgeführt
- [ ] 8. GitHub Release erstellt
```

### Proposal 3: Compress Persona Intro
Use structured prompting for the persona definition.
**Current:**
```markdown
Du bist der **Release Manager** für {{PROJECT_NAME}}.
Du koordinierst Versionierung, Changelogs, Build-Prozesse und GitHub-Releases.
```
**Proposed:**
```markdown
**Role:** Release Manager ({{PROJECT_NAME}})
**Focus:** Semantic Versioning, Changelogs, Build-Pipelines, GitHub Releases.
```

### Proposal 4: Condense Delegation Rules
Transform the Delegation section into a tighter mapping.
**Current:**
```markdown
- Tests fehlen/brechen? → `tester`
- DoD nicht erfüllt? → `validator`
...
```
**Proposed:**
```markdown
## Delegation Routing
| Condition | Target Agent |
|---|---|
| Test Failure | `tester` |
| DoD Failed | `validator` |
| Docs Outdated | `documenter` |
| Git Ops (Push/Tag)| `git` |
```

## 4. Conclusion
Implementing these changes will:
- **Reduce Token Load:** By eliminating the redundant checklist and trimming conversational prose.
- **Ensure Framework Compliance:** By removing `bun test`, ensuring the template is truly generic.
- **Improve Latency & Reliability:** A denser, checklist-driven prompt reduces reasoning drift and accelerates generation.
