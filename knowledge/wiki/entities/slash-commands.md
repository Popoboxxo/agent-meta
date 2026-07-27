---
type: "API Reference"
title: "Slash Commands Reference"
description: "Slash Commands are chat shortcuts that allow you to trigger specific workflows within the AI Providers (e.g., Claude, Gemini)."
tags: [api]
timestamp: "2026-07-27"
resource: "../../sources/docs/api/slash-commands.md"
migrated_from: "docs/api/slash-commands.md"
---
# Slash Commands Reference

Slash Commands are chat shortcuts that allow you to trigger specific workflows within the AI Providers (e.g., Claude, Gemini).

| Command | Description |
|---------|-------------|
| `/add-mcp-server` | Guided setup to activate an MCP server |
| `/add-project-role` | Add a project-specific agent role (override or extension) |
| `/add-provider` | Add an AI provider to this project |
| `/admin` | Start or stop the Admin UI server (includes viz dashboard and MCP server) |
| `/analysis` | Run AST dependency analysis |
| `/analyze-logs` | Analyze log files with severity classification (RFC 5424) |
| `/checkpoint` | List or resume orchestrator checkpoints |
| `/commit` | Stage changes and create a conventional commit |
| `/consistency-check` | Validate agent templates, commands, cross-references |
| `/diagnose` | Health-check the agent-meta setup |
| `/doc-now` | Update CODEBASE_OVERVIEW.md via documenter agent |
| `/feedback` | Report bug/feature as standardized GitHub issue |
| `/merge` | Create PR for current branch and merge into main |
| `/open-docs` | Open docs/ folder or specific analysis document |
| `/pipelines` | Show all quality pipelines — active/disabled status |
| `/report-bug` | Report a bug via feedback agent |
| `/set-preset` | Change DoD preset or speech mode |
| `/test-orchestration` | Run orchestration dry-run and validate functions |
| `/update-extensions` | Update managed blocks in project extension files |
| `/update-meta` | Re-sync all agents without upgrading version |
| `/upgrade-meta` | Upgrade submodule to latest version and re-sync |
| `/what-is` | Explain what an agent does |