---
description: Start or stop the admin UI server (includes viz dashboard and MCP server)
allowed-tools: ["Bash"]
argument-hint: "[start | stop | status | --no-viz | --port <port>]"
invokable: true
---

Start or manage the agent-meta admin UI server. $ARGUMENTS

- No argument / `start`: Start admin UI + viz dashboard + MCP server
- `stop`: Stop all managed servers
- `status`: Show server status (PIDs, ports)
- `--no-viz`: Start admin UI only, skip viz and MCP subprocesses
- `--port <port>`: Use custom port (default: 7420)

```python scripts/admin-server.py $ARGUMENTS```
