# Fleet-Server (Phase 1+2: Read-Only Dashboard + Config View) — Design Spec

> Brainstormed 2026-09-07 (Architectural path). Source: GitHub issue #682 §7
> ("Agent-Meta Fleet-Server"), explicitly staged there as **IDEA**, not
> DRAFT — this spec resolves the 6 open questions from §7.8 and narrows
> scope to Phase 1+2 only, per the issue's own recommendation ("Nicht vor
> Phase 1+2 (rein lesend) committen, bevor nicht das Auth-/Token-Modell
> konkret ausspezifiziert und geprüft ist"). Phase 3 (remote sync trigger)
> and Phase 4 (remote config edit) are explicitly **out of scope** for
> this spec and its implementation plan — they need their own future
> design pass once Phase 1+2 has run in practice.

## Problem

`admin-server.py` today runs per-repo, with no cross-repo visibility
(`docs/superpowers/specs/admin-ui-concept.md` §12 left this "noch offen").
A user managing multiple agent-meta-instrumented repos (ReqogniLoom,
ha-health-o-mat, ha-go-gauge, agent-meta itself, ...) has no single place
to see which repos are on which version, when they last synced, or
whether their sync is healthy — they have to open each repo's own
admin-server separately.

## Answered open questions (issue §7.8)

| # | Question | Answer | Consequence for this spec |
|---|---|---|---|
| 1 | Hosting | Part of the agent-meta repo, self-hosted by the user wherever they run it | `scripts/fleet-server.py` ships in this repo like `admin-server.py`; no separate deployment story needed |
| 2 | CI runners register too? | No — durable repos only | No registry-cleanup-for-ephemeral-entries mechanism needed in Phase 1+2 |
| 3 | Network context | Mixed / not yet fixed | Plan defensively: Phone-Home (Push), full token+TLS-when-non-localhost model from day 1 (matches the issue's own fallback recommendation when §7.3's own premise is unresolved) |
| 4 | Roles | Single fleet-admin token is enough for the MVP | No user/role management in Phase 1+2 |
| 5 | Transport | (c) SSE + HTTP long-poll | No new dependency, no hand-rolled WebSocket framing (see §7.4.1 in the issue for why raw stdlib WebSocket isn't available) |
| 6 | Token storage / registry encryption | Same priority chain as `admin-server.py` (`--fleet-token` > env var > `project.yaml` > token file); registry stays plaintext JSON (live metadata only, no secrets) | No new token-resolution convention; no registry encryption needed for Phase 1+2's data shape |

## Scope

**In scope (Phase 1 — read-only dashboard):**
- Instance registration (a repo's `admin-server.py`, given `--fleet-url`
  + a token, registers with the fleet server and holds an SSE connection
  open for future commands).
- Heartbeat (liveness signal on the same connection).
- Fleet dashboard (`docs/ui/fleet-ui.html`, same zero-dependency
  single-file principle as `admin-ui.html`): list of registered
  instances — name/prefix, agent-meta version, last-sync timestamp,
  health status (online/offline via heartbeat recency).
- Log tail: fleet server can request the last N lines of an instance's
  `sync.log`/`admin-server.log` over the same channel.

**In scope (Phase 2 — config view):**
- Read-only proxy: fleet server relays a `get-config` command to an
  instance and displays the returned `project.yaml` (redacted — see
  Security below) in the fleet dashboard.

**Explicitly out of scope for this spec:**
- Phase 3 (remote sync trigger) and Phase 4 (remote config edit) — no
  write path of any kind. The command vocabulary in Phase 1+2 is
  `register`, `heartbeat`, `get-status`, `get-logs`, `get-config` only.
  `trigger-sync` and `put-config` are NOT implemented, not even behind a
  disabled flag — adding them is a separate future spec once Phase 1+2
  has been used in practice and the write-path security model can be
  re-evaluated with real operational experience.
- Roles/multi-user access.
- CI-runner registration / ephemeral-instance cleanup.
- Registry encryption at rest (registry holds only what Phase 1+2 needs:
  instance name, version, last-heartbeat timestamp, connection state —
  no config content is persisted, only relayed live).

## Architecture

### Components

1. **`scripts/fleet-server.py`** (new): the central process. Owns:
   - An HTTP server (stdlib `http.server`, matching `admin-server.py`'s
     existing zero-dependency convention) exposing:
     - `POST /register` — an instance registers itself (name, prefix,
       agent-meta version, its own token). Returns a session id.
     - `GET /events/<session_id>` — the long-lived SSE connection an
       instance holds open; the fleet server writes commands onto this
       stream as they're issued from the dashboard.
     - `POST /result/<session_id>` — the instance POSTs a command's
       result back (e.g. the requested log tail, the requested config).
     - `POST /heartbeat/<session_id>` — periodic liveness ping.
     - `GET /` — serves `fleet-ui.html`.
     - `GET /api/instances` — dashboard-facing: list of registered
       instances + their live status, for `fleet-ui.html` to poll.
   - An in-memory + JSON-file-backed registry (see Data Model below).
2. **Fleet client** (extension of `scripts/admin-server.py`): new flags
   `--fleet-url <url>` and `--fleet-token <token>` (with the priority
   chain from answered question 6). When set, on startup the instance:
   - `POST`s to `/register` on the fleet server.
   - Opens `GET /events/<session_id>` and blocks on it in a background
     thread, dispatching any command it receives to the *existing*
     local `/api/*` handlers `admin-server.py` already has (pure relay —
     no new config/log-reading logic duplicated; Phase 1+2 only ever
     dispatches `get-status`, `get-logs`, `get-config`, never a write
     endpoint).
   - Sends a heartbeat on a fixed interval (30s) via `/heartbeat/<id>`.
3. **`docs/ui/fleet-ui.html`** (new): single-file dashboard, same
   zero-dependency principle as `admin-ui.html` — polls
   `GET /api/instances`, renders the instance table, and on request
   triggers `get-logs`/`get-config` for a selected instance (fleet server
   relays to that instance's SSE stream, waits for the `/result` POST,
   returns it to the dashboard's poll/fetch).

### Data flow (command/response over SSE + POST)

```
fleet-ui.html --GET /api/instances--> fleet-server.py --(in-memory registry)
fleet-ui.html --POST /api/instances/<id>/get-logs--> fleet-server.py
                                                         |
                                          writes "get-logs" event onto
                                          the instance's open SSE stream
                                                         |
                                                         v
                                          admin-server.py (instance) reads
                                          the event, calls its OWN existing
                                          log-read logic, POSTs the result
                                          back to /result/<session_id>
                                                         |
                                                         v
                                          fleet-server.py holds the pending
                                          request open until the result
                                          arrives (or times out), then
                                          returns it as the response to
                                          fleet-ui.html's original POST
```

This keeps `fleet-server.py` a pure relay (issue §7.4, point 4): it never
reads a file, never touches an instance's `project.yaml` directly — it
only ever forwards a command and relays the answer.

### Data model (registry)

`~/.agent-meta-fleet/registry.json` (fleet server's own machine, not
per-repo — this is the fleet server's state, analogous to
`admin-server.py`'s `.claude/agent-meta-state.json` being per-instance
state):

```json
{
  "version": 1,
  "instances": {
    "<session_id>": {
      "name": "agent-meta",
      "prefix": "am",
      "agent_meta_version": "0.101.0",
      "token_hash": "<sha256 of the instance's own token, never the token itself>",
      "registered_at": "2026-09-07T12:00:00Z",
      "last_heartbeat": "2026-09-07T12:05:00Z"
    }
  }
}
```

No config content, no log content, no raw tokens are ever persisted to
this file — it is pure live/session metadata. This is what makes "no
registry encryption in Phase 1+2" a correct call per answered question 6:
there is nothing confidential to encrypt yet.

## Security (non-negotiable, per issue §7.5)

- **Per-instance token, not shared.** Each instance generates its own
  token at `--fleet-token` setup time (or accepts one issued by the fleet
  admin) — a compromised instance token never grants access to any other
  instance's data. The fleet server never accepts a bare instance name as
  identity; every command result is bound to the session id the token
  established.
- **TLS required whenever the fleet server is not bound to `localhost`.**
  Enforced at startup: if `--host` is anything other than
  `127.0.0.1`/`localhost` and no TLS cert/key is configured, refuse to
  start (fail closed) — the network-context answer above is "mixed/not
  yet fixed", so the safe default is to never allow an accidental
  plaintext cross-network deployment.
- **Explicit opt-in only.** `--fleet-url` is a manually-set flag on the
  instance; nothing in `admin-server.py`'s default startup path ever
  attempts fleet registration on its own.
- **Read-only is structural, not just policy.** Phase 1+2 has no
  `trigger-sync`/`put-config` handler anywhere in the code — there is no
  flag to accidentally enable a write path that doesn't exist yet.
- **Config redaction on the `get-config` relay (Phase 2).** Before an
  instance's `admin-server.py` returns `project.yaml` content over
  `/result`, it MUST redact the same categories `admin-server.py`
  already redacts for its own local config view today (secrets,
  tokens) — reuse that existing redaction function, do not reimplement it.
- **Audit log, both sides.** Every relayed command (`get-status`,
  `get-logs`, `get-config`) is appended to `~/.agent-meta-fleet/audit.log`
  on the fleet server AND to the instance's own existing audit-log
  mechanism (`.claude/hooks/.guard-audit.log`'s sibling convention) —
  who asked, when, for what.
- **Mutual identity check.** Since network context is unresolved (mixed),
  the instance must verify it is talking to the fleet server it expects
  before registering — a certificate fingerprint pinned in the
  `--fleet-url`/`--fleet-token` setup step (compared on every
  reconnect), not just trusting whatever answers at that URL.

## Testing

- Unit tests for the registry (register/heartbeat/list, TTL-based
  offline detection when no heartbeat arrives within e.g. 90s).
- Unit tests for the command/response relay logic using a fake SSE
  stream (no real network needed — inject events, assert dispatch).
- A fail-closed test: starting `fleet-server.py` with a non-localhost
  `--host` and no TLS config must exit non-zero with a clear message,
  never silently fall back to plaintext.
- An integration test spinning up both `fleet-server.py` and
  `admin-server.py --fleet-url ...` as real subprocesses on `localhost`,
  registering, and completing one `get-status` and one `get-logs`
  round-trip.

## Out of scope / explicit follow-ups

- Phase 3 (remote sync trigger) and Phase 4 (remote config edit) — need
  their own design pass, informed by how Phase 1+2 actually gets used.
- Multi-role/multi-user fleet access.
- CI-runner registration.
- Registry encryption at rest (revisit if a future phase persists
  anything more sensitive than live session metadata).
- Coordination with the CISO/security branch's auth model, once merged
  (per issue §7.5's own closing note) — this spec's token model should be
  reconciled with that work before Phase 3+ is designed, not before
  Phase 1+2 ships.
