# MCP Hard Prohibitions

> Kurzfassung der harten Tool-Verbote aktiver MCP-Server. Vollständige Tool-Listen und
> Hinweise: pro Provider in `.claude/skills` — jeweils `mcp-<server>/SKILL.md` (`use-lazy-rules.md`).

- **honcho:** `delete_conclusion`, `set_config` — absolut verboten.
- **playwright:** `browser_run_code_unsafe`, `browser_evaluate`, `browser_file_upload`, `browser_handle_dialog` — absolut verboten.
- **reqogniloom:** `workspace.close`, `workspace.reactivate`, `workspace.delete`, `permissions.set_rule`, `permissions.list`, `permissions.revoke`, `permissions.check`, `admin.backup_create`, `admin.backup_list`, `admin.restore`, `audit.query`, `audit.ai_review`, `events.dlq_list`, `events.dlq_replay`, `user.create`, `user.assign_role`, `user.list`, `user.deactivate` — absolut verboten.
