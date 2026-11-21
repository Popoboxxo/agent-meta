---
description: Start or stop the admin UI server (includes viz dashboard and MCP server)
allowed-tools: ["Bash"]
argument-hint: "[start | stop | status | restart] [--mode local|network] [--allowed-hosts HOST...] [--no-viz] [--port <port>]"
---

Start or manage the agent-meta admin UI server. $ARGUMENTS

- No argument / `start`: Start admin UI + viz dashboard + MCP server
- `stop`: Stop all managed servers
- `status`: Show server status (PIDs, ports)
- `restart`: Stop, then start again
- `--mode local` (default): Bind loopback only (`127.0.0.1`), no token. Local access; cannot be exposed to the network.
- `--mode network`: Bind all interfaces (`0.0.0.0`) and generate a random token that is printed **once** at start and **never persisted** — restart rotates it. Prints reachable URLs (`http://<ip>:7420/?token=<T>`) and firewall/security guidance. Optional `--allowed-hosts` is required for writes from other machines.
- `--allowed-hosts HOST...`: Origin hosts allowed for writes (replaces the loopback default `127.0.0.1 localhost ::1`); relevant in network mode.
- `--no-viz`: Start admin UI only, skip viz and MCP subprocesses
- `--port <port>`: Use custom port (default: 7420)

```python scripts/admin-server.py $ARGUMENTS```
