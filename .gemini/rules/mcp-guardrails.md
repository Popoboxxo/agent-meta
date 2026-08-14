# MCP Hard Prohibitions

> Kurzfassung der harten Tool-Verbote aktiver MCP-Server. Vollständige Tool-Listen und
> Hinweise: siehe `.claude/skills/mcp-<server>/SKILL.md` (`use-lazy-rules.md`).

- **honcho:** `delete_conclusion`, `set_config` — absolut verboten.
- **reqogniloom:** `workspace.close|reactivate|delete`, alle `permissions.*`, `admin.*`, `audit.*`, `events.dlq_*`, alle `user.*` — absolut verboten.
- **playwright:** `browser_run_code_unsafe`, `browser_evaluate`, `browser_file_upload`, `browser_handle_dialog` — absolut verboten.
