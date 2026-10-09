---
snippet: escalate-card
version: "1.0.0"
language: markdown
runtime: "agent-meta Modern Mode"
---

<escalate-card>
## Escalation Card (canonical contract)
```
STATUS: escalate
RESULT: <what was completed>
ESCALATE_REASON: <categorical: blast_radius_growth | scope_violation | repeated_failure | security_risk | blocked_dependency>
ESCALATE_METRIC: <quantifiable, e.g. affected_files > 5 | subsystems: 3 | attempts: 2>
RECOMMENDED_TIER: <target tier>
PARTIAL_WORK: <what is already done>
NEXT_STEPS: <concrete next steps>
```
`ESCALATE_REASON` (categorical) + `ESCALATE_METRIC` (quantifiable) are MANDATORY (issue #346): a card without both is invalid — the orchestrator rejects the tier change and requests structured re-submission.
</escalate-card>
