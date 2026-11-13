# Repo-Containment („Gefängnis-Modus")

{{#if REPO_CONTAINMENT_ENABLED}}
{{REPO_CONTAINMENT_BLOCK}}
Durchsetzung: PreToolUse-Hook = **Convention boundary** (keine Security Boundary, nur gegen akzidentellen Missbrauch; Convention boundary = fail-closed nur gegen akzidentellen Missbrauch, Security boundary = auch gegen deliberate Umgehung).
Kerngrenzen: Indirektion (`eval`, `bash -c`, `xargs`, Interpreter, Variablen-Ziele) und exotische Redirections/`cd`-Ketten umgehen den Tokenizer; Symlink-/TOCTOU-Escape ist nur per `realpath` gemildert; MCP-/Nicht-Tool-Schreibpfade und Selbst-Deaktivierung des Guards durch den Agenten sind nicht abgedeckt; hook-lose Provider erhalten nur die Prompt-Konvention.
{{else}}
Repo-Containment ist **deaktiviert** (keine Schreibbeschränkung auf die Projekt-Wurzel). Der Opt-out (`repo_containment.enabled: false` bzw. Provider-Override) ist in `.meta-config/project.yaml` jederzeit umkehrbar.
{{/if}}
