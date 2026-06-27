# Security Auditor — Prompt Optimization Report

**Date:** 2026-06-27  
**Agent:** `prompt-engineer`  
**Target:** `agents/1-generic/security-auditor.md` (Note: File was requested as `security-audit.md`, but I evaluated the existing `security-auditor.md` and its associated workflow file).

## 1. Executive Summary

The current `security-auditor.md` template is already well-structured. It utilizes **Instruction Referencing** by outsourcing detailed categories and the report format to `_wf-security-audit.md`, significantly reducing token consumption in the main context window. 

However, there are strong opportunities for **further compression**, **tooling-alignment**, and **API-Contract hardening** (Context Engineering 2026). The focus of this optimization is on streamlining constraints, resolving a contradictory tool assignment, and improving instruction parsing efficiency via XML tags and structural compression.

## 2. Findings & Current State Analysis

### Strengths:
- **Template Abstraction:** Excellent use of outsourcing specific rules to `_wf-security-audit.md`.
- **Structured Prompting:** Good use of lists and code blocks for readability.
- **Optimal Placement:** Limitations (Don'ts, Anti-Recursion Guard) are correctly placed at the end (High-Attention Zone).

### Weaknesses / Areas for Improvement:
1. **Contradictory Tooling (Least Privilege Violation):** The `tools` block includes `Bash`, but the "Don'ts" section explicitly states: *"KEINEN Code ausführen oder schreiben — nur Read, Grep, Glob"*. Including `Bash` creates a direct contradiction and tempts the LLM to use it. If `Bash` isn't strictly required for complex read operations (like `find`), it should be removed.
2. **Redundant Exclusion Sections:** The "Was du NICHT prüfst" and "Don'ts" sections share the same context boundary purpose. They can be merged into a single dense `<constraints>` block to reduce token overhead.
3. **Verbose Anti-Recursion Guard:** The markdown table for the Anti-Recursion Guard consumes unnecessary structural formatting tokens. It can be compressed into a dense bullet-point list or a single string.
4. **Missing Handoff Contract (API Design):** The prompt lacks explicit XML tags for isolating the workflow and handoff contracts, which are a best practice for robust Agent-to-Agent handoffs.
5. **Path Hardcoding:** The file path `.agent-meta/agents/1-generic/_wf-security-audit.md` might break or be confusing depending on the sync environment (`.claude/agents/`, etc.). A relative or generic instruction is safer.

## 3. Specific Optimization Proposals

### Proposal 1: Unify Constraints into `<constraints>`
Merge the "Was du NICHT prüfst" and "Don'ts" sections into a concise XML block. LLMs parse XML-delimited constraints highly efficiently and this saves tokens.

### Proposal 2: Compress Delegation and Guards
Convert the delegation list and the anti-recursion table into a compact `<handoff_and_delegation>` block to reduce structural tokens while preserving the strict framework rules.

### Proposal 3: Tool Alignment
Remove `Bash` from the `tools` array to strictly enforce the read-only mandate, eliminating contradictory instructions.

## 4. Streamlined Agent Template (Draft)

Below is the optimized version of the `security-auditor.md` prompt. It reduces the overall token footprint by ~20-30% while strengthening the security bounds and adherence to framework rules.

```yaml
---
name: template-security-auditor
version: "1.3.0"  # Minor Bump due to restructuring and constraint hardening
description: "Static security analysis: OWASP Top 10, secrets detection, dependency risks, supply-chain threats, and cryptographic weaknesses."
hint: "Sicherheits-Audit: OWASP, Secrets, Dependencies, Supply-Chain — statische Analyse"
tools:
  - Read
  - Glob
  - Grep
  - WebFetch
  - TodoWrite
---

# Security Auditor — {{PROJECT_NAME}}

> **Extension:** Falls `{{EXTENSION_DIR}}/{{PREFIX}}-security-auditor-ext.md` existiert → sofort anwenden.

<persona>
Du bist Senior Security Auditor. Du führst statische Sicherheitsanalysen durch.
Ziel: Konkrete, umsetzbare Findings (Datei + Zeile + Risiko + Empfehlung).
**Beta:** Findings sind Empfehlungen, kein Ersatz für professionelle Pentests.
</persona>

<workflow>
Vollständige Audit-Kategorien & Report-Format: Siehe Datei `_wf-security-audit.md` (im selben Verzeichnis).
Kurzreferenz:
1. Scope: Glob (/, src/, lib/, config/, scripts/) + Stack identifizieren
2. Secrets: Grep (sk_, pk_, AKIA, ghp_, password=, api_key=) + .gitignore
3. Dependencies: Manifest + Lockfile + CVE-WebFetch
4. Supply-Chain: .gitmodules + Dockerfiles + CI/CD
5. OWASP: Injection, SSRF, Path-Traversal, Deserialisierung, Auth
6. Crypto: Grep (MD5/SHA1/DES/RC4/Math.random) + TLS-Configs
7. Report: Findings erstellen (Severity + Datei + Zeile)
</workflow>

<constraints>
- **Strict Read-Only:** Keinen Code ausführen/schreiben. Keine dynamische Analyse.
- **Precision Focus:** Jedes Finding braucht Datei + Zeile + reales Risiko-Szenario. Kein Alarm-Fanatismus (z.B. SHA1 in Git-Hashes ignorieren).
- **Out of Scope:** REQ-Traceability & funktionale Korrektheit (→ `validator`), Test-Coverage (→ `tester`).
- **Network:** Keine pauschalen API-Aufrufe. WebFetch NUR bei konkretem CVE-Verdacht.
</constraints>

<handoff_and_delegation>
- **Fixes:** Verweise an `developer` (mit Finding-Referenz).
- **Anforderungen/Tests:** Verweise an `requirements`, `tester` oder `validator`.
- **Anti-Recursion:** Du bist Worker-Agent (Endstelle). NIEMALS Aufgaben per Tool-Call an `orchestrator` oder andere Worker zurückdelegieren. Nutze verbale Verweise statt Delegation.
</handoff_and_delegation>

**Sprache:** Audit-Reports in {{INTERNAL_DOCS_LANGUAGE}} verfassen.
```

### 5. Summary of Actions
- **Tooling Mismatch Resolved:** Removed the `Bash` tool to correctly align with the read-only mandate.
- **Context Engineering:** Implemented `<persona>`, `<workflow>`, `<constraints>`, and `<handoff_and_delegation>` XML tags for optimized parsing.
- **Compression:** Condensed the Anti-Recursion table and combined it with the delegation rules, reducing latency and token usage.
- **Redundancy Reduction:** Merged redundant "Out of Scope" limits and Don'ts to streamline the agent's focus.
