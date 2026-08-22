# Concept: Review-Agent Fleet (Frontend / Backend / Database / UI / Security)

> Status: PLANNED · Source: content audit (#528) + web research (2026-08-22)
> Goal: close the domain-reviewer gap in `agents/1-generic/` with 5 evidence-based review roles
> and harden existing reviewers.

---

## 1. Problem

- Domain-specific code review is currently concentrated in one generic `code-reviewer`.
- Existing specialists cover only parts of the requested spectrum: `security-auditor`
  (no output contract, no OWASP/CWE evidence mapping), `accessibility-specialist` (WCAG only).
- A2A-Gate #5 requires structured worker output — reviewers must emit machine-parseable
  findings (see #528: 28 templates lack this today).

## 2. Research base (patterns that proved out)

| Pattern | Source | Adopted as |
|---|---|---|
| One reviewer per domain, parallel, **file-based data flow** + separate synthesis agent | claude-deep-review (49 specialized reviewers) | §4 Pipeline |
| **Two-pass verification**: recall pass → adversary pass filters ungrounded findings | G-Research; OWASP appsec-agent (`pr_adversary`, `fp_adversary`) | §3 P2 |
| **Rules index**: reviewer may only cite rule IDs from a project-owned index — "the model can suggest, but never define" | G-Research standards tool | §3 P3 |
| Evidence obligation: every finding = file:line + snippet + CWE/OWASP ref + concrete fix | OWASP Secure Agent Playbook | §3 P4 |
| Confidence gate: report only findings ≥80% confidence; severity + 0–100 merge score as optional gate | claude-deep-review; AGENA | §3 P5 |

## 3. Design principles for all fleet templates

1. **P1 — Output contract (mandatory):** every finding and the final report use the
   STATUS/RESULT/ARTIFACTS envelope; findings additionally follow the fixed finding schema
   (`id, severity, file:line, rule_id, evidence, fix`).
2. **P2 — Two-pass protocol:** reviewers produce findings (recall); a paired
   `*-review-adversary` pass (or orchestrator-invoked second call) confirms/expels findings.
   Adversary roles are thin wrappers around the base template to avoid template bloat.
3. **P3 — Rules index:** each reviewer references a project-configurable rules file
   (e.g. `.meta-config/review-rules/<domain>.yaml`). Findings citing unknown rule IDs are
   invalid by definition. Ships with sensible defaults per domain.
4. **P4 — Evidence & remediation:** no finding without file:line + snippet + mapped standard
   reference (OWASP Top 10/ASVS/CWE for security; WCAG 2.2 SC for UI/a11y; SQL/ORM anti-pattern
   refs for database) + minimal fix suggestion.
5. **P5 — Confidence gate:** findings below confidence threshold are dropped silently;
   report ends with `MERGE_SCORE: <0-100>` so the orchestrator can gate merges.

## 4. Role matrix

| New role | Scope highlights | Standard mapping |
|---|---|---|
| `frontend-reviewer` | component design, state management, SSR/hydration correctness, browser API misuse, bundle/render performance | — |
| `backend-reviewer` | API contracts, silent-failure hunting (swallowed errors), concurrency/async pitfalls, middleware chain | — |
| `database-reviewer` | migration safety (reversibility, locking), N+1 detection, injection vectors, schema evolution discipline | CWE-89 |
| `ui-reviewer` | design-token conformance, layout/UX consistency; delegates WCAG depth to existing `accessibility-specialist` | WCAG 2.2 (via delegation) |
| `security-reviewer` | OWASP Top 10 + ASVS coverage, secrets, injection families, supply chain; **refactor of existing** `security-auditor` onto this contract | OWASP Top 10, ASVS, CWE |

Existing roles stay responsible for their niche: `code-reviewer` (general quality),
`accessibility-specialist` (deep WCAG), `e2e-tester` (behavioral).

## 5. Orchestration integration

- Orchestrator routes by changed-path classes (mirroring platform-detection pattern):
  `*.tsx/vue/svelte → frontend-reviewer`, migrations/schema files → `database-reviewer`,
  etc.; ambiguous diffs → parallel dispatch of candidates.
- All reviewers run in parallel, write reports to files (return-channel protection,
  cf. issue #514), synthesis merges + dedupes into one PR comment block.
- Severity schema uniform: `CRITICAL | HIGH | MEDIUM | LOW | CLEAN`.

## 6. Deliverables

1. 5 new/refactored templates in `agents/1-generic/` (+ version bump per conventions)
2. `config/role-defaults.yaml` entries + CLAUDE.md/howto updates (new-role checklist)
3. Default rules indexes `config/review-rules/{frontend,backend,database,ui,security}.yaml`
4. pytest: frontmatter/contract checks extended to enforce P1/P4/P5 structurally
5. Docs: agent-graph regeneration via sync.py

## 7. Open questions

- OQ1: Adversary passes as separate templates vs. prompt-section toggle? (proposal: section toggle first)
- OQ2: Rules-index location: `.meta-config/` (project-owned) vs. `config/review-rules/` (fleet defaults)?
- OQ3: Merge-score gating default off (advisory) until stability phase?
