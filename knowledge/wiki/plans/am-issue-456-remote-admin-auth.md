---
type: Plan
title: "Issue #456 – Admin UI Remote Access (Bind-Host, Token Auth, Host Allowlist)"
source: "GitHub Issue #456"
estimated_effort: "~3 h (effort-estimator: 6 einzelne Code-Änderungsschritte, 7 Dateien tangiert, mittlere Komplexität durch Security-kritischen Token-Flow; nur eine Datei (admin-server.py) wird substanziell geändert)"
created: "2026-08-10"
status: "planned"
branch: "fix/sync-drift-and-external-pin"
---

# Plan: Issue #456 – Admin UI Remote Access

**Source:** GitHub Issue #456
**Estimated effort:** ~3 h (reference `effort-estimator` — 8 discrete code-change steps, 2 files touched, security-critical token flow; medium complexity — only `admin-server.py` gets substantive changes, schema is additive)

## Overview

Three mandatory components:
1. **Configurable Bind-Host** (`--host 0.0.0.0` via CLI or `admin-ui.bind-host` in `project.yaml`)
2. **Token Authentication** (mandatory when binding non-loopback: CLI `--admin-token`, env `ADMIN_UI_TOKEN`, `project.yaml` `admin-ui.token` or `admin-ui.token-file`)
3. **Configurable Host Allowlist** (`--allowed-hosts` / `admin-ui.allowed-hosts`, default = loopback, extends DNS-rebinding protection)

Critical invariants:
- **Default = 127.0.0.1 + Loopback-only Allowlist — no regression**
- **Fail closed:** Binding non-loopback without token → hard error, server refuses to start
- **Token never logged, never in API responses, never returned by `/api/mode`**
- **Constant-time token comparison** (`hmac.compare_digest` — stdlib, zero dependencies)

---

## Steps

### Step 1: Schema Update — Add new keys to `project-config.schema.json` admin-ui block

| Field | Value |
|-------|-------|
| **File** | `config/project-config.schema.json` |
| **Lines** | 897–925 (existing `admin-ui` block) |
| **Agent** | `developer` |
| **Depends on** | — |

**Changes:**

1.1 — Replace `"additionalProperties": false` (line 924) with explicitly listed new properties (or set to `true`):

```jsonc
"bind-host": {
  "type": "string",
  "default": "127.0.0.1",
  "description": "IP address the Admin UI HTTP server binds to. Default: 127.0.0.1 (loopback only). Set to 0.0.0.0 for network access — requires token authentication."
},
"token": {
  "type": "string",
  "description": "Authentication token for remote access. REQUIRED when bind-host is non-loopback. Equivalent to --admin-token CLI flag or ADMIN_UI_TOKEN env var. NEVER commit to version control."
},
"token-file": {
  "type": "string",
  "description": "Path to a file containing the admin auth token. Alternative to inline 'token' key for secret management (e.g., Docker secrets, 1Password CLI)."
},
"allowed-hosts": {
  "type": "array",
  "items": { "type": "string" },
  "default": ["127.0.0.1", "localhost", "::1"],
  "description": "List of host:port origins allowed for CORS / DNS-rebinding protection. Extends the default loopback set. Use when binding to a specific network interface."
}
```

1.2 — Change `"additionalProperties": false` to `"additionalProperties": true` (line 924). This avoids breaking the config-write path (line 3330 already allows `"admin-ui"` as a writeable section; new keys will flow through without schema rejection).

**Acceptance criterion:** `python scripts/sync.py --validate` reports no schema errors. IDE autocompletion recognizes `admin-ui.bind-host`, `admin-ui.token`, `admin-ui.token-file`, `admin-ui.allowed-hosts`.

---

### Step 2: Constants + Dynamic Allowed Hosts Infrastructure

| Field | Value |
|-------|-------|
| **File** | `scripts/admin-server.py` |
| **Lines** | 34–48 (imports), 60–61 (DEFAULT_HOST), 112–115 (ALLOWED_HOSTS) |
| **Agent** | `developer` |
| **Depends on** | — *(can run in parallel with Step 1 — disjoint file)* |

**Changes:**

2.1 — Add `import hmac` to imports (insert after line 36 `import os`):

```python
import hmac
```

2.2 — Rename the module-level `ALLOWED_HOSTS` tuple (line 115) to clarify it's the *default* set:

```python
# Before (line 115):
ALLOWED_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")

# After:
DEFAULT_ALLOWED_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")
```

2.3 — Add a new module-level constant for the loopback set (used by fail-closed check in constructor):

```python
LOOPBACK_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")
```

2.4 — Update the docstring comment on line 112–114 to reflect that remote binding is now possible with token auth.

**Acceptance criterion:** `rtk grep "ALLOWED_HOSTS" scripts/admin-server.py` returns zero results (all references updated). `rtk grep "DEFAULT_ALLOWED_HOSTS" scripts/admin-server.py` returns all former `ALLOWED_HOSTS` usage sites.

---

### Step 3: Config Loading — `_load_admin_ui_config()`

| Field | Value |
|-------|-------|
| **File** | `scripts/admin-server.py` |
| **Lines** | 186–225 (modeled on `_load_viz_config`) |
| **Agent** | `developer` |
| **Depends on** | Step 2 (same file, sequential — needs `DEFAULT_ALLOWED_HOSTS` constant) |

**Changes:**

3.1 — Insert a new function `_load_admin_ui_config()` immediately after `_load_viz_config()` (after the blank line at 225). Model it on `_load_viz_config()`:

```python
def _load_admin_ui_config(root: Path) -> dict:
    """Load admin-ui configuration from ``.meta-config/project.yaml``.

    Returns a flat dict:
      * ``bind_host``     (str)          — admin-ui.bind-host
      * ``token``         (str | None)   — admin-ui.token (None if not set)
      * ``token_file``    (str | None)   — admin-ui.token-file (None if not set)
      * ``allowed_hosts`` (list[str])    — admin-ui.allowed-hosts
      * ``enabled``       (bool)         — admin-ui.enabled
      * ``port``          (int)          — admin-ui.port
    """
    config_path = root / ".meta-config" / "project.yaml"
    try:
        sys.path.insert(0, str(root / "scripts"))
        sys.path.insert(0, str(root / ".agent-meta" / "scripts"))
        from lib.config import load_config  # type: ignore[import]
        config = load_config(config_path)
        admin_cfg = config.get("admin-ui") or {}
        return {
            "bind_host":     str(admin_cfg.get("bind-host", DEFAULT_HOST)),
            "token":         admin_cfg.get("token"),    # None if absent
            "token_file":    admin_cfg.get("token-file"),  # None if absent
            "allowed_hosts": list(admin_cfg.get("allowed-hosts", list(DEFAULT_ALLOWED_HOSTS))),
            "enabled":       bool(admin_cfg.get("enabled", True)),
            "port":          int(admin_cfg.get("port", DEFAULT_PORT)),
        }
    except Exception:  # noqa: BLE001
        return {
            "bind_host":     DEFAULT_HOST,
            "token":         None,
            "token_file":    None,
            "allowed_hosts": list(DEFAULT_ALLOWED_HOSTS),
            "enabled":       True,
            "port":          DEFAULT_PORT,
        }
```

**Acceptance criterion:** Calling `_load_admin_ui_config(Path("."))` on a project without `admin-ui` block returns the default dict (`bind_host: "127.0.0.1"`, `token: None`, `allowed_hosts: ["127.0.0.1", "localhost", "::1"]`). When `admin-ui.bind-host: "0.0.0.0"` is set in `project.yaml`, the function returns `bind_host: "0.0.0.0"`.

---

### Step 4: Token Infrastructure — AuthError, Constant-Time Comparison, Token Resolution

| Field | Value |
|-------|-------|
| **File** | `scripts/admin-server.py` |
| **Lines** | 517–518 (SecurityError), 969–976 (_send_json), new functions ~226–280 |
| **Agent** | `senior-developer` |
| **Depends on** | Step 3 |

**Changes:**

4.1 — Add `AuthError` exception class after `SecurityError` (after line 518):

```python
class AuthError(Exception):
    """Raised when token authentication fails. Mapped to HTTP 401."""
```

4.2 — Add constant-time token verification function (new function, after `SecurityError`/`AuthError` section):

```python
def _verify_token(provided: str | None, expected: str | None) -> bool:
    """Constant-time token comparison using hmac.compare_digest.

    Returns False if either argument is None or empty.
    Never logs or returns token values in error messages.
    """
    if not provided or not expected:
        return False
    return hmac.compare_digest(
        provided.encode("utf-8"),
        expected.encode("utf-8"),
    )
```

4.3 — Add token resolution function (new function, after `_verify_token`):

```python
def _resolve_admin_token(
    cli_token: str | None,
    config_token: str | None,
    config_token_file: str | None,
    env_var_name: str = "ADMIN_UI_TOKEN",
) -> str | None:
    """Resolve the admin token from multiple sources.

    Priority (highest first):
      1. CLI --admin-token
      2. Environment variable ADMIN_UI_TOKEN
      3. project.yaml admin-ui.token
      4. project.yaml admin-ui.token-file (file content, stripped)

    Returns None if no token is configured from any source.
    """
    if cli_token:
        return cli_token
    env_token = os.environ.get(env_var_name)
    if env_token:
        return env_token
    if config_token:
        return config_token
    if config_token_file:
        try:
            return Path(config_token_file).read_text().strip()
        except OSError:
            pass
    return None
```

4.4 — Add `_send_json` support for `WWW-Authenticate` header on 401 responses. Modify `_send_json` (lines 969–976) to accept an optional `extra_headers` parameter:

```python
# Before (line 969):
def _send_json(self, payload: Any, status: int = 200) -> None:

# After:
def _send_json(self, payload: Any, status: int = 200,
               extra_headers: dict[str, str] | None = None) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json; charset=utf-8")
    self.send_header("Content-Length", str(len(body)))
    self.send_header("Cache-Control", "no-store")
    if extra_headers:
        for key, value in extra_headers.items():
            self.send_header(key, value)
    self.end_headers()
    self.wfile.write(body)
```

Note: `extra_headers` parameter name is deliberate — avoids collision with HTTP `headers` property.

**Acceptance criteria:**
- `_verify_token("abc", "abc")` returns `True`; `_verify_token("abc", "xyz")` returns `False`; `_verify_token(None, "abc")` returns `False`
- `_resolve_admin_token(cli_token="secret", config_token="other")` returns `"secret"` (CLI wins)
- `_resolve_admin_token(cli_token=None, config_token=None, config_token_file=None)` with `ADMIN_UI_TOKEN=envsecret` returns `"envsecret"`
- `_send_json({"error":"unauthorized"}, status=401, extra_headers={"WWW-Authenticate":"Bearer"})` sends the correct header

---

### Step 5: Constructor Changes — AdminServer.__init__ New Parameters

| Field | Value |
|-------|-------|
| **File** | `scripts/admin-server.py` |
| **Lines** | 3939–3973 |
| **Agent** | `developer` |
| **Depends on** | Steps 2, 3, 4 |

**Changes:**

5.1 — Add new parameters to `AdminServer.__init__` (lines 3939–3946):

```python
# Before:
def __init__(
    self,
    root: Path,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    enable_watcher: bool = False,
    enable_viz: bool = True,
) -> None:

# After:
def __init__(
    self,
    root: Path,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    enable_watcher: bool = False,
    enable_viz: bool = True,
    admin_token: str | None = None,
    admin_token_file: str | None = None,
    allowed_hosts: tuple[str, ...] | None = None,
) -> None:
```

5.2 — Replace the hard loopback validation (lines 3947–3951) with fail-closed logic:

```python
# Before (lines 3947–3951):
if host not in ALLOWED_HOSTS:
    raise ValueError(
        f"refusing to bind on non-loopback host {host!r}; "
        f"allowed: {', '.join(ALLOWED_HOSTS)}"
    )

# After:
# Load admin-ui config from project.yaml (token, allowed-hosts, bind-host)
admin_cfg = _load_admin_ui_config(root)
# CLI args override config file values
effective_token = _resolve_admin_token(
    cli_token=admin_token,
    config_token=admin_cfg["token"],
    config_token_file=admin_token_file or admin_cfg["token_file"],
)
# Allowed hosts: CLI > config > default loopback
effective_allowed_hosts = tuple(allowed_hosts) if allowed_hosts else tuple(admin_cfg["allowed_hosts"])
# --- Fail-closed: non-loopback requires token ---
is_loopback = host in LOOPBACK_HOSTS
if not is_loopback and not effective_token:
    raise ValueError(
        f"refusing to bind on non-loopback host {host!r} without token authentication.\n"
        f"Configure admin-ui.token in .meta-config/project.yaml, set ADMIN_UI_TOKEN "
        f"environment variable, or pass --admin-token."
    )
if not is_loopback:
    print(f"  * Token auth enabled — binding to {host}:{port}", file=sys.stderr)
```

5.3 — Pass the resolved allowed hosts to `AdminRequestHandler` as class attribute (after line 3971):

```python
AdminRequestHandler.allowed_hosts = effective_allowed_hosts
AdminRequestHandler.admin_token = effective_token
```

**Acceptance criteria:**
- `AdminServer(Path("."), host="127.0.0.1")` — starts normally (loopback, no token needed)
- `AdminServer(Path("."), host="0.0.0.0")` — raises `ValueError` with message about missing token
- `AdminServer(Path("."), host="0.0.0.0", admin_token="secret")` — prints "Token auth enabled" and proceeds

---

### Step 6: `_check_origin()` Update — Dynamic Allowlist

| Field | Value |
|-------|-------|
| **File** | `scripts/admin-server.py` |
| **Lines** | 1011–1046 |
| **Agent** | `developer` |
| **Depends on** | Step 5 (`AdminRequestHandler.allowed_hosts` must exist) |

**Changes:**

6.1 — Replace the hard-coded allowed_origins and allowed_hosts sets in `_check_origin()` (lines 1029–1044) with the configured `AdminRequestHandler.allowed_hosts` class attribute:

```python
# Before (lines 1029–1044):
        else:
            allowed_origins = {
                f"http://127.0.0.1:{expected_port}",
                f"http://localhost:{expected_port}",
                f"http://[::1]:{expected_port}",
            }
            if origin not in allowed_origins:
                raise SecurityError(f"origin not allowed: {origin!r}")

        host = self.headers.get("Host", "")
        allowed_hosts = {
            f"127.0.0.1:{expected_port}",
            f"localhost:{expected_port}",
            f"[::1]:{expected_port}",
        }
        # Allow the configured bind host as well (covers explicit ``--host``).
        allowed_hosts.add(f"{expected_host}:{expected_port}")
        if host not in allowed_hosts:
            raise SecurityError(f"host header not allowed: {host!r}")

# After:
        else:
            allowed_origins = set()
            for h in self.__class__.allowed_hosts:
                allowed_origins.add(f"http://{h}:{expected_port}")
            if origin not in allowed_origins:
                raise SecurityError(f"origin not allowed: {origin!r}")

        host = self.headers.get("Host", "")
        allowed_hosts = set()
        for h in self.__class__.allowed_hosts:
            allowed_hosts.add(f"{h}:{expected_port}")
        # Always allow the actual bind host (covers explicit ``--host``).
        allowed_hosts.add(f"{expected_host}:{expected_port}")
        if host not in allowed_hosts:
            raise SecurityError(f"host header not allowed: {host!r}")
```

6.2 — Update the docstring (lines 1012–1018) to reflect that allowed-hosts are now configurable.

**Acceptance criterion:** With `allowed_hosts=("127.0.0.1", "192.168.1.100")`, an Origin header `http://192.168.1.100:7420` passes validation. An Origin header `http://10.0.0.1:7420` raises `SecurityError`.

---

### Step 7: Token Enforcement — `_check_token()` in All HTTP Methods

| Field | Value |
|-------|-------|
| **File** | `scripts/admin-server.py` |
| **Lines** | 1060–1117 (do_GET, do_PUT, do_POST, do_DELETE), ~1010 (new _check_token method) |
| **Agent** | `developer` |
| **Depends on** | Steps 4, 5 |

**Changes:**

7.1 — Add `_check_token()` method to `AdminRequestHandler`, immediately before `_check_origin()` (before line 1011):

```python
def _check_token(self) -> None:
    """Verify the admin token when token auth is configured.

    Extracts token from:
      1. ``Authorization: Bearer <token>`` header
      2. ``?token=<token>`` query parameter

    When no token is configured (AdminRequestHandler.admin_token is None),
    this is a no-op — the server is loopback-only and auth is not required.

    Raises AuthError on mismatch or missing token.
    """
    expected = self.__class__.admin_token
    if expected is None:
        return  # No token configured → no check needed (loopback-only mode)

    # Extract token from Authorization header
    auth_header = self.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        provided = auth_header[7:]  # len("Bearer ") == 7
        if _verify_token(provided, expected):
            return

    # Extract token from query parameter (convenience for browser access)
    parsed = urlparse(self.path)
    query_params: dict[str, list[str]] = {}
    from urllib.parse import parse_qs
    query_params = parse_qs(parsed.query)
    token_list = query_params.get("token", [])
    if token_list and _verify_token(token_list[0], expected):
        return

    raise AuthError("invalid or missing admin token")
```

**Note:** `from urllib.parse import parse_qs` must be added to the imports at line 47. Change line 47:
```python
# Before:
from urllib.parse import urlparse

# After:
from urllib.parse import parse_qs, urlparse
```

7.2 — Add `_check_token()` call to `do_GET` (line 1061, as first action in try block):

```python
def do_GET(self) -> None:
    try:
        self._check_token()     # <-- NEW
        self._dispatch_get()
    except SecurityError as exc:
        ...
    except AuthError as exc:    # <-- NEW: 401 instead of 403
        self._send_json(
            {"error": "unauthorized", "detail": str(exc)},
            status=401,
            extra_headers={"WWW-Authenticate": "Bearer"},
        )
    ...
```

7.3 — Add `_check_token()` call to `do_PUT`, `do_POST`, `do_DELETE` (lines 1077, 1093, 1107 — as first action in try block, BEFORE `_check_origin()`). Also add `AuthError` handler (same pattern as do_GET):

```python
def do_PUT(self) -> None:
    try:
        self._check_token()     # <-- NEW (before _check_origin)
        self._check_origin()
        self._dispatch_put()
    except AuthError as exc:    # <-- NEW
        self._send_json(
            {"error": "unauthorized", "detail": str(exc)},
            status=401,
            extra_headers={"WWW-Authenticate": "Bearer"},
        )
    except SecurityError as exc:
        ...

# Same pattern for do_POST (line 1092) and do_DELETE (line 1106)
```

**Acceptance criteria:**
- **Loopback, no token:** `do_GET` passes `_check_token` (no-op), all existing behavior preserved.
- **Remote, valid token:** `curl -H "Authorization: Bearer secret" http://0.0.0.0:7420/api/mode` → 200.
- **Remote, invalid token:** `curl -H "Authorization: Bearer wrong" http://0.0.0.0:7420/api/mode` → 401 with `WWW-Authenticate: Bearer` header, body `{"error":"unauthorized"}`.
- **Remote, no token:** `curl http://0.0.0.0:7420/api/mode` → 401.
- **Token never appears** in response body, error messages, or `/api/mode` output.

---

### Step 8: CLI Args + main() Wiring

| Field | Value |
|-------|-------|
| **File** | `scripts/admin-server.py` |
| **Lines** | 4041–4077 (argparser + main function) |
| **Agent** | `developer` |
| **Depends on** | Steps 1–7 |

**Changes:**

8.1 — Update `--host` argument (line 4047) to accept any string (remove `choices`), update help text:

```python
# Before (line 4047):
parser.add_argument("--host", default=DEFAULT_HOST, choices=list(ALLOWED_HOSTS),
                    help=f"Bind host -- loopback only (default: {DEFAULT_HOST})")

# After:
parser.add_argument("--host", default=DEFAULT_HOST,
                    help=f"Bind host address (default: {DEFAULT_HOST}). "
                         f"Non-loopback addresses (e.g., 0.0.0.0) require --admin-token or ADMIN_UI_TOKEN env var.")
```

8.2 — Add new `--admin-token` argument (after `--host`, ~line 4049):

```python
parser.add_argument("--admin-token", default=None,
                    help="Authentication token for remote access. "
                         "REQUIRED when --host is non-loopback. "
                         "Equivalent to ADMIN_UI_TOKEN env var or admin-ui.token in project.yaml.")
```

8.3 — Add new `--allowed-hosts` argument (after `--admin-token`):

```python
parser.add_argument("--allowed-hosts", nargs="*", default=None,
                    help="Additional allowed origin hosts for CORS/DNS-rebinding protection. "
                         "Default: 127.0.0.1 localhost ::1. "
                         "Extends (does not replace) the default loopback set.")
```

8.4 — Update `main()` to pass new args to `AdminServer` constructor (lines 4070–4076):

```python
# Before (lines 4070–4076):
server = AdminServer(
    root,
    host=args.host,
    port=args.port,
    enable_watcher=args.watch,
    enable_viz=not args.no_viz,
)

# After:
server = AdminServer(
    root,
    host=args.host,
    port=args.port,
    enable_watcher=args.watch,
    enable_viz=not args.no_viz,
    admin_token=args.admin_token,
    allowed_hosts=tuple(args.allowed_hosts) if args.allowed_hosts else None,
)
```

**Acceptance criteria:**
- `python scripts/admin-server.py` — starts on 127.0.0.1:7420 (no change)
- `python scripts/admin-server.py --host 0.0.0.0` — exits with error (no token)
- `python scripts/admin-server.py --host 0.0.0.0 --admin-token secret` — prints "Token auth enabled", starts on 0.0.0.0:7420
- `python scripts/admin-server.py --host 0.0.0.0 --allowed-hosts 192.168.1.0` — exits with error (no token, host validation fires before allowed-hosts matters)
- `ADMIN_UI_TOKEN=secret python scripts/admin-server.py --host 0.0.0.0` — starts with env-var token, no CLI token needed

---

## Test Plan

| Test | Command | Expected |
|------|---------|----------|
| Default behavior | `python scripts/admin-server.py` | Binds 127.0.0.1:7420, no auth |
| Non-loopback without token | `python scripts/admin-server.py --host 0.0.0.0` | ValueError, does not start |
| Remote with CLI token | `python scripts/admin-server.py --host 0.0.0.0 --admin-token s3cret` | Starts, prints "Token auth enabled" |
| Remote with env token | `ADMIN_UI_TOKEN=s3cret python scripts/admin-server.py --host 0.0.0.0` | Starts |
| Authenticated GET | `curl -H "Authorization: Bearer s3cret" http://0.0.0.0:7420/` | 200, HTML returned |
| Unauthenticated GET | `curl http://0.0.0.0:7420/api/mode` | 401, `{"error":"unauthorized"}`, `WWW-Authenticate: Bearer` |
| Wrong token GET | `curl -H "Authorization: Bearer wrong" http://0.0.0.0:7420/api/mode` | 401 |
| Query param token | `curl "http://0.0.0.0:7420/api/mode?token=s3cret"` | 200 |
| Token not in response | `curl -H "Authorization: Bearer s3cret" http://0.0.0.0:7420/api/mode` | Response body must NOT contain "s3cret" |
| CSRF protection (remote) | POST with wrong Origin header | 403 forbidden |
| DNS rebinding (remote) | Request with wrong Host header | 403 forbidden |
| Allowed-hosts extends loopback | `--allowed-hosts 192.168.1.0` + token | Origin `http://192.168.1.0:7420` passes |
| Token timing side-channel | (automated timing test) | Constant-time comparison — no correlation between match/mismatch and response time |

---

## Persistence

- **Persisted to:** `knowledge/wiki/plans/am-issue-456-remote-admin-auth.md`

---

## Notes for Implementers

1. **No new dependencies.** `hmac` is in Python stdlib. `parse_qs` from `urllib.parse` is also stdlib.
2. **Token sanitization in logging:** `log_message()` (line 961) is already suppressed (`return` — no-op). But if any `print()` statements are added for debugging, ensure token values are never printed. The existing `print()` call in Step 5.2 (`print(f"  * Token auth enabled — binding to {host}:{port}")`) deliberately does NOT include the token value.
3. **`DEFAULT_ALLOWED_HOSTS` rename:** Search the entire file for `ALLOWED_HOSTS` references before renaming. There are 3 usage sites: line 115 (definition), line 3947 (constructor validation), line 4047 (argparser `choices`). The argparser reference is removed in Step 8.
4. **`admin-ui` write path:** Line 3330 already includes `"admin-ui"` in the allowed write-sections set — no change needed for the UI's config write endpoint.
5. **Loopback token behavior:** When `admin_token` is explicitly configured but host is loopback, the token check still runs. This is intentional — a user who configures a token wants auth even on localhost. Clean separation: `_check_token()` is a no-op ONLY when `admin_token is None`.
