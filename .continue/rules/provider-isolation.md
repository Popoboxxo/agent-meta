# Provider Isolation

This project uses multiple AI providers. Do not read or write files in directories
managed by other providers:

- `.claude` — Claude Code only
- `CLAUDE.md` — another provider only
- `.gemini` — Gemini CLI only
- `.opencode` — Opencode only
- `opencode.json` — Opencode only
- `AGENTS.md` — Opencode only

Only read files in your own provider directory (`.continue/`) unless explicitly
asked by the user to inspect another provider's configuration.

<!-- agent-meta managed — do not edit manually -->
