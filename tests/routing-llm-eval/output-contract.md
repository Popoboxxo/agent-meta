## Eval output contract (role routing)

This session is a routing evaluation, not a normal development task. The
wrapping harness reads only the JSON object below.

Reply with exactly one JSON object and nothing else. No prose, no Markdown, no
code fence, no explanation, and no tool calls.

```json
{"target": "<role-name or pipeline:<name> or ASK>", "tier_escalation": false}
```

- `target` is the single best target for the user request: a role name from
  the routing rules, a `pipeline:<name>` id, or `ASK` when the request is
  genuinely ambiguous.
- Always include `tier_escalation`. Use `true` only when the target role is
  orchestrator-only or requires tier escalation; otherwise `false`.
- For an ambiguous request answer `{"target": "ASK", "tier_escalation": false}`.
- Never return more than one target and never explain the choice.
