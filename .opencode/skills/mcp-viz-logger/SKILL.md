---
name: mcp-viz-logger
description: "Use when logging agent visualization events via the viz-logger MCP server."
---

# MCP: viz-logger

> agent-meta visualization event logger — tracks agent_start, delegate_out, agent_end for graph generation

---

## Erlaubte Tools

- `log_viz_event`

## Agent-Hinweise

Nutze log_viz_event um Agenten-Starts, Delegationen und Beendigungen zu protokollieren.
Parameter: event (agent_start|delegate_out|agent_end), agent, provider, status, target, caller, task_id, payload.

## Verbindungstyp

- Typ: `stdio`
- Kommando: `python scripts/viz-logger.py --mcp`

---

*Generiert von agent-meta aus `config/mcp-registry.yaml` — nicht manuell bearbeiten.*
