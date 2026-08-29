# Remote Access to the Admin UI

The Admin UI (`scripts/admin-server.py` + `docs/ui/admin-ui.html`) is a
zero-dependency HTTP server that exposes a visual configuration surface for
agent-meta. By default it binds to **loopback only** (`127.0.0.1`) and requires
**no authentication** — anyone with shell access to the machine can open it.
This guide shows you how to:

1. Run and manage the server (start / stop / status / restart).
2. Expose it beyond localhost **with token authentication**.
3. Access it from a browser or `curl` — and how the token travels.
4. Diagnose the most common failure modes.

> **In a consumer repository** agent-meta is a submodule. The server script then
> lives at `.agent-meta/scripts/admin-server.py` and you usually pass
> `--root .` so the server finds `.meta-config/project.yaml`. All commands below
> use the top-level `scripts/admin-server.py` path; adapt it if you run from a
> submodule layout.

---

## 1. Server lifecycle

Run the server in the **foreground** (historic default, stops on `Ctrl+C`):

```bash
python3 scripts/admin-server.py
```

Or manage it as a **detached background process**:

```bash
python3 scripts/admin-server.py start      # launch detached, returns immediately
python3 scripts/admin-server.py status     # show running state of all services
python3 scripts/admin-server.py restart    # stop, then start again
python3 scripts/admin-server.py stop       # stop Admin UI + Viz dashboard + MCP server
```

Notes on the detached mode:

- `start` writes its PID to `.meta-viz/.admin-server-pid` and logs to
  `.meta-viz/admin-server.log`. A second `start` while the server is running
  prints `Admin UI already running (PID: …)` and does nothing.
- `stop` tears down **all three** services together (Admin UI, Viz dashboard,
  MCP SSE server) — `start` brings them up together.
- The same server can be launched via the sync entry point:
  `python3 scripts/sync.py --admin` (after a sync) or
  `python3 scripts/sync.py --admin-only` (skip the sync).

---

## 2. CLI flags

The server accepts the following flags (verified against the built-in `--help`):

| Flag | Type / Default | Semantics |
|---|---|---|
| `command` | `start` \| `stop` \| `status` \| `restart` | Detached lifecycle commands. Omitted → foreground mode until `Ctrl+C`. |
| `--port PORT` | int, default `7420` | TCP port the Admin UI binds to. |
| `--host HOST` | default `127.0.0.1` | Bind address. **Non-loopback addresses (e.g. `0.0.0.0`) require `--admin-token` or the `ADMIN_UI_TOKEN` env var.** |
| `--admin-token TOKEN` | default none | Authentication token for remote access. Required when `--host` is non-loopback. Equivalent to the `ADMIN_UI_TOKEN` env var or `admin-ui.token` in `project.yaml`. |
| `--allowed-hosts [HOST …]` | default none | Additional allowed origin hosts for the CORS / DNS-rebinding protection. **Extends** (does not replace) the default loopback set `127.0.0.1 localhost ::1`. |
| `--root DIR` | default `.` | Project root directory (where `.meta-config/project.yaml` lives). |
| `--watch` | flag | Enable the filesystem watcher: polls config files every 2 s and emits events to `.meta-viz/events.jsonl` (feeds the live-events stream). |
| `--no-viz` | flag | Skip starting the Viz dashboard and MCP server subprocesses. Useful for lightweight / CI environments that only need the Admin UI. |

> **Reading flags vs. writing config:** the bind address and port are controlled
> by `--host` / `--port` on the command line. From `.meta-config/project.yaml`
> the server currently applies only `admin-ui.token`, `admin-ui.token-file` and
> `admin-ui.allowed-hosts` (see [Token persistence](#6-token-persistence)); the
> schema also documents `admin-ui.bind-host` and `admin-ui.port`, but the server
> does not apply those two at runtime.

---

## 3. Port matrix

`start` launches up to three services. Only the Admin UI itself can be exposed
to the network; the two sub-servers are hard-bound to loopback.

| Port | Service | Default | Configured by | Bind |
|---|---|---|---|---|
| `7420` | **Admin UI** (`admin-server.py`) | yes | `--port` / `admin-ui.port` | `--host` (default `127.0.0.1`) |
| `8765` | **Viz dashboard** (`viz-report.py --serve`) | yes | `viz.server.port` in `project.yaml` | `127.0.0.1` only |
| `9090` | **MCP SSE server** (`viz-logger.py --http`) | yes | `viz.mcp.port` in `project.yaml` | `127.0.0.1` only |

Remote users reach only the Admin UI (`http://<host>:7420/`). The Viz dashboard
and MCP SSE endpoint stay local; if you need them on another machine, tunnel
them (see [Troubleshooting](#9-troubleshooting)).

---

## 4. Bind behavior

**Loopback = no token required (by default).** The default bind hosts
`127.0.0.1`, `localhost` and `::1` are the trusted loopback set. With the
default configuration (no token set anywhere) the authentication check is a
no-op, so the historic local workflow stays unchanged: start the server, open
`http://127.0.0.1:7420/`, done. If you *do* configure a token, it is enforced
on loopback as well — loopback just removes the requirement, it does not
disable the check.

**Non-loopback = token mandatory (fail-closed).** Binding anywhere else
(`--host 0.0.0.0`, a LAN IP, …) without a token aborts startup with an error:

```
ValueError: refusing to bind on non-loopback host '0.0.0.0' without token authentication.
Configure admin-ui.token in .meta-config/project.yaml, set ADMIN_UI_TOKEN
environment variable, or pass --admin-token.
```

You cannot accidentally expose the server without a token — it refuses to start.

Minimal remote launch:

```bash
python3 scripts/admin-server.py --host 0.0.0.0 --admin-token '<your-token>'
```

---

## 5. Setting the admin token

The token is resolved with the following precedence (**CLI > env > config > file**):

1. `--admin-token <token>` (CLI flag)
2. `ADMIN_UI_TOKEN` (environment variable)
3. `admin-ui.token` (in `.meta-config/project.yaml`)
4. `admin-ui.token-file` (path to a file whose trimmed content is the token)

For a one-off remote session, the environment variable keeps the token out of
shell history and process listings of other users:

```bash
ADMIN_UI_TOKEN='<your-token>' python3 scripts/admin-server.py --host 0.0.0.0
```

Generate a strong token with:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 6. Token persistence

Persist the token in `.meta-config/project.yaml` under the top-level
`admin-ui` block:

```yaml
admin-ui:
  enabled: true
  port: 7420
  token: "<your-token>"          # exact key path: admin-ui.token
  # token-file: ".secrets/admin-token"   # alternative: read token from a file
  allowed-hosts: ["myhost.example.com"]
```

- The exact key path is **`admin-ui.token`** (kebab-case, top-level `admin-ui`
  block) — verified against `config/project-config.schema.json` and
  `scripts/admin-server.py`.
- **Never commit the token to version control.** The schema explicitly warns
  about this; use `token-file` or the `ADMIN_UI_TOKEN` env var for secret
  management (Docker secrets, password managers, …).
- `admin-ui.allowed-hosts` is an array of hostnames/IPs; it extends the default
  loopback set `["127.0.0.1", "localhost", "::1"]`.

---

## 7. Accessing from a browser

**Option A — token deep link.** Open the UI with the token in the URL:

```
http://<host>:7420/?token=<your-token>
```

The UI reads `?token=` on load, stores it in `sessionStorage` (key
`agent-meta-admin-token`) and immediately scrubs it from the URL via
`history.replaceState`, so it does not linger in browser history, logs or
referrer headers.

**Option B — login overlay.** Open `http://<host>:7420/` without a token. The
UI shell loads (it is public), the first `/api/*` request returns `401`, and a
*"Admin token required"* overlay appears. Enter the token; it is only persisted
to `sessionStorage` after the server accepted it.

How the token travels afterwards:

1. Regular requests (`/api/*`) send `Authorization: Bearer <token>` — injected
   by the UI's central fetch wrapper. The server accepts the header **or** a
   `?token=` query parameter (constant-time comparison, no plain `==`).
2. `GET /` and `GET /favicon.png` are public and load before authentication.
   Every `/api/*` endpoint is token-gated; mutations (`PUT`/`POST`/`DELETE`)
   additionally enforce the origin/Host check (CORS + DNS-rebinding defence).
3. The live-events stream (`/api/events`, SSE) is the exception: browsers'
   `EventSource` cannot set `Authorization` headers, so the UI appends the
   token as `?token=` to the SSE URL. See [Security](#10-security-considerations)
   for why this matters.

**Full remote operation needs `--allowed-hosts`.** Mutating requests are
rejected with `403` when the browser's `Origin`/`Host` header does not match an
allowed host (default: loopback only). If you reach the UI as
`http://myhost.example.com:7420`, add that name at server start:

```bash
python3 scripts/admin-server.py --host 0.0.0.0 --admin-token '<your-token>' \
  --allowed-hosts myhost.example.com
```

Viewing works with the token alone; saving configs, running syncs and similar
mutations require the host to be allowed.

---

## 8. Accessing from the command line

With a token configured, API calls need the `Authorization` header (or the
`?token=` query parameter — the server accepts both):

```bash
curl -H "Authorization: Bearer <your-token>" http://<host>:7420/api/mode
curl "http://<host>:7420/api/mode?token=<your-token>"
```

Without a token (or with a wrong one) you get a `401`:

```json
{"error": "unauthorized", "detail": "invalid or missing admin token"}
```

`GET /` returns the UI shell and is the only path that works without a token —
handy as a connectivity check:

```bash
curl -s -o /dev/null -w "%{http_code}\n" http://<host>:7420/
```

---

## 9. Troubleshooting

### `ERR_CONNECTION_REFUSED` — remote client cannot reach the server

The server binds loopback only (the default). A remote browser gets a
connection-refused error even though the server is running on the host.

- Verify the bind: `python3 scripts/admin-server.py status` prints the URL the
  server actually bound to.
- Fix (requires token): bind to all interfaces —
  `python3 scripts/admin-server.py --host 0.0.0.0 --admin-token '<token>'`.
- Or keep loopback and tunnel: `ssh -L 7420:127.0.0.1:7420 user@host`, then
  open `http://127.0.0.1:7420/` locally (no token needed on the loopback side).
- Remember: the Viz dashboard (`8765`) and MCP SSE server (`9090`) are always
  loopback-bound — tunnel them too if you need them remotely.

### `401 invalid or missing admin token` — authentication failed

The JSON body is `{"error": "unauthorized", "detail": "invalid or missing
admin token"}` with a `WWW-Authenticate: Bearer` header. In the browser the
login overlay appears (or re-appears with *"Invalid token. Please try again."*).

- Check which token the server actually uses (precedence):
  `--admin-token` > `ADMIN_UI_TOKEN` > `admin-ui.token` > `admin-ui.token-file`.
  A leftover `ADMIN_UI_TOKEN` env var silently overrides your `project.yaml`
  value.
- If you use the deep link, make sure the token is URL-safe (no `+`, `/`, `=`
  unencoded — `secrets.token_urlsafe()` output is fine).
- Wrong tokens are never persisted to `sessionStorage`; clear it if a rejected
  token lingers.

### Port collision — crash loop on startup

The Admin UI port is already in use by another process:

- Foreground mode: Python exits with a traceback containing
  `OSError: [Errno 98] Address already in use`.
- Detached mode: the child process dies immediately; `start` reports
  `! Admin UI failed to start -- see .meta-viz/admin-server.log`, and the log
  contains the same `Address already in use` error. `status` shows `STOPPED`
  even though the port is occupied — by a foreign process, a stale instance,
  or a previous server whose PID file was lost.

Fixes: stop the conflicting process, or run on another port:
`python3 scripts/admin-server.py --port 7421 …` (the UI is a single-page app —
the port only affects the URL you open).

### `403` on save — host not allowed

Mutating requests carry an origin/Host check. Add the hostname/IP you use to
reach the UI via `--allowed-hosts` (or `admin-ui.allowed-hosts`), see
[Section 7](#7-accessing-from-a-browser).

---

## 10. Security considerations

- **The token is a shared secret.** Anyone who has it can read and modify every
  configuration file the server exposes (in `super_admin` mode: the framework
  `config/*.yaml` files; in `project_admin` mode: `.meta-config/project.yaml`).
  Treat it like a password: rotate it, never commit it, prefer the
  `ADMIN_UI_TOKEN` env var or `token-file` over an inline `admin-ui.token`.
- **The SSE stream puts the token in the URL.** Because `EventSource` cannot
  send `Authorization` headers, the UI connects to `/api/events` with the token
  as a `?token=` query parameter (code comment in `docs/ui/admin-ui.html`:
  *"EventSource cannot carry Authorization headers, so the token travels as a
  query parameter"*). Query strings are routinely recorded by HTTP server and
  reverse-proxy access logs, and can leak through `Referer` headers on
  outbound links. The UI scrubs the *initial* deep-link token from the browser
  URL, but the SSE request line still hits every layer in front of the server.
- **Mitigations for remote deployments:**
  - Sanitize or redact `token` from access logs, or disable query-string
    logging on the proxy/web server in front of the Admin UI.
  - Keep log retention short and restrict access to the logs.
  - Terminate TLS in front of the server (reverse proxy): the Admin UI speaks
    plain HTTP and must not travel unencrypted over untrusted networks.
  - Restrict exposure with `--allowed-hosts` and, ideally, a firewall rule so
    the port is reachable only from the networks/users that need it.
  - If possible, prefer the login overlay over handing out deep links
    (`?token=`) — the overlay keeps the token out of URLs entirely, except for
    the SSE connection described above.

---

## Related

- [Admin UI & Function Reference](../api/admin-ui-reference.md) — UI panels and configuration options.
- [CLI Reference](../api/cli-reference.md) — `sync.py` flags including `--admin` / `--admin-only`.