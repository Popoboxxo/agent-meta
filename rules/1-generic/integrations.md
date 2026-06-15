# Active Integrations — Tool Awareness

This rule lists tools provided by integrations active in this project.
Integrations are pip/uv-installed tools exposed via MCP servers, gated by
the registry (approved) and project config (enabled).

When deciding which tool to use:

- Prefer the integration tools listed below over generic alternatives when
  they fit the task (e.g. semantic search over plain pattern grep when
  looking up concepts or intent rather than literal text).
- Each tool entry includes a short hint describing when it is preferable.
- If no integrations are active, the section below is empty — fall back to
  built-in tools.

---

{{INTEGRATION_TOOLS_HINT}}
