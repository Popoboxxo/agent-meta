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
6. **P6 — Model-tier assignment:** every fleet role gets an explicit `tier` entry in
   `config/role-defaults.yaml` at introduction time (no implicit defaults). Proposal:
   `security-reviewer` + `database-reviewer` → strongest review tier (deep analysis),
   `frontend-reviewer` / `backend-reviewer` / `ui-reviewer` → standard tier.
   All remain overridable via the existing chain (`model-overrides` per role,
   `model-inherit-main-chat`, `model-override-all`).

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

## 5. Orchestrator routing (optimization)

### 5.1 Path-based routing matrix (config-driven, not prompt-hardcoded)

New config file `config/routing/reviewers.yaml` — the orchestrator reads class patterns
from here instead of embedding them in its prompt text:

```yaml
routes:
  - match: "**/*.{tsx,jsx,vue,svelte,css,scss}"
    reviewers: [frontend-reviewer, ui-reviewer]
  - match: "**/migrations/**"          # + *.sql, schema files
    reviewers: [database-reviewer]
  - match: "**/{api,server,controllers,services}/**"
    reviewers: [backend-reviewer]
  - match: "**/*.{py,ts,go,java}"      # fallback: always security-scan code diffs
    reviewers: [security-reviewer]
synthesis: true                        # merge + dedupe into one report
max_parallel: 5
```

- Ambiguous diffs → parallel dispatch of all matched candidates (fan-out).
- `ui-reviewer` delegates WCAG depth to `accessibility-specialist` per concept §4.
- Cheap-tier prefilter possible later: routing classifier picks reviewer set before full review.

### 5.2 Routing-eval integration

All new roles enter the existing routing LLM-eval catalog (`tests/routing-llm-eval/`,
B1 classification) so misrouting is measurable: each new role gets ≥3 catalog cases
(positive intent, negative intent, ambiguous). CI gate stays non-blocking until stable.

### 5.3 Cost-aware tiering in routing

Routing prefers the lowest sufficient tier per §3 P6; `model-inherit-main-chat` and
`model-override-all` keep precedence over tier resolution unchanged.

## 6. Deliverables

1. 5 new/refactored templates in `agents/1-generic/` (+ version bump per conventions)
2. `config/role-defaults.yaml` entries **with explicit tier assignment** (P6) + CLAUDE.md/howto updates (new-role checklist)
3. Default rules indexes `config/review-rules/{frontend,backend,database,ui,security}.yaml`
4. Routing matrix `config/routing/reviewers.yaml` (§5.1) + orchestrator template update to consume it
5. pytest: frontmatter/contract checks extended to enforce P1/P4/P5/P6 structurally; routing-eval catalog cases for all new roles (§5.2)
6. Docs: agent-graph regeneration via sync.py

## 7. Open questions

- OQ1: Adversary passes as separate templates vs. prompt-section toggle? (proposal: section toggle first)
- OQ2: Rules-index location: `.meta-config/` (project-owned) vs. `config/review-rules/` (fleet defaults)?
- OQ3: Merge-score gating default off (advisory) until stability phase?
