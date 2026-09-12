# Repo-Containment („Gefängnis-Modus")

{{#if REPO_CONTAINMENT_ENABLED}}
{{REPO_CONTAINMENT_BLOCK}}
Durchsetzung: PreToolUse-Hook = **Convention boundary** (keine Security Boundary, nur gegen akzidentellen Missbrauch; Definition: `.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`). Grenzen/Details: `docs/concepts/repo-containment-prison-mode.md`.
{{else}}
Repo-Containment ist **deaktiviert** (keine Schreibbeschränkung auf die Projekt-Wurzel). Der Opt-out (`repo_containment.enabled: false` bzw. Provider-Override) ist in `.meta-config/project.yaml` jederzeit umkehrbar.
{{/if}}
