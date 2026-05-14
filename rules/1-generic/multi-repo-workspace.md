---
description: Multi-Repo Workspace — conventions for projects spanning multiple repositories
---

# Multi-Repo Workspace Conventions

> Activated when `WORKSPACE_REPOS` is configured in `project.yaml`.

## Rules

1. **Agent files live ONLY in the meta-repo root.**
   - Never create `.claude/`, `.opencode/`, `.continue/`, `.gemini/` directories in sibling repos.
   - All agent configuration is managed centrally in the meta-repo.

2. **Use absolute or relative paths from the meta-repo root.**
   - Sibling repos: `../sharkord-vid-with-friends/src/index.ts`
   - Always verify the working directory before running commands.

3. **Build and test commands must run in the correct repo directory.**
   - Example: `cd ../sharkord-vid-with-friends && bun test`

4. **Workspace-level documentation belongs in the meta-repo.**
   - Cross-plugin conventions → `docs/CONVENTIONS.md`
   - Cross-plugin patterns → `docs/PATTERNS.md`
   - Lessons learned → `docs/LEARNINGS.md`
   - Plugin-specific docs → stay in the respective plugin repo

5. **Standardized learning capture.**
   - When a developer discovers a pattern or solves a bug, use `.agent-meta/templates/learning-capture.md`
   - Propose adding it to the meta-repo's `docs/LEARNINGS.md`

## VS Code Workspace (Optional)

If using VS Code, create a `.code-workspace` file in the meta-repo root:

```json
{
  "folders": [
    { "name": "sharkord-meta", "path": "." },
    { "name": "vid-with-friends", "path": "../sharkord-vid-with-friends" },
    { "name": "stream-with-friends", "path": "../sharkord-stream-with-friends" },
    { "name": "hero-introducer", "path": "../sharkord-hero-introducer" }
  ]
}
```

## Cross-Repo Operations

When delegating to agents for cross-repo work:

```
Delegiere an: developer
Aufgabe: Editiere ../sharkord-vid-with-friends/src/index.ts
         Arbeitsverzeichnis: ../sharkord-vid-with-friends/
```
