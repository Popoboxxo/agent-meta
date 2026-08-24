---
name: env-tmp-disk-full
description: This dev environment's /tmp is chronically full from unrelated projects, and a globally-installed pytest-homeassistant-custom-component plugin breaks any pytest run in agent-meta unless disabled.
metadata:
  type: project
---

Two independent environment gotchas observed 2026-08-24 while running `pytest tests/` in agent-meta (unrelated to any code change):

1. **`/tmp` (tmpfs, 2.9G) is chronically ~100% full**, filled by *other* projects' artifacts (`/tmp/pytest-of-hermes` ~660M, `/tmp/run_*.log` ~830M, `/tmp/ci-*.log` ~830M — none belong to agent-meta). This causes widespread `OSError: [Errno 28] No space left on device` in any test using `tmp_path`/`tmpfile`, and also breaks the Bash tool's own output capture (`/tmp/claude-1001/.../tasks` ENOSPC errors on *every* command, even `echo`).
   - Deleting those unrelated files is out of scope and gets blocked by the permission classifier (correctly — they belong to other work).
   - **Do NOT** set `TMPDIR`/`--basetemp` to a directory on the root filesystem (`/`) to work around this — a full-suite pytest run there consumed the ~2.7G free on `/` and filled it to 100%, a worse outage than the original problem. Root fs only has single-digit GB headroom.
   - Workaround that worked without side effects: redirect command output to a file inside the repo (`cmd > repo/.some.log 2>&1`) so the Bash tool's own capture buffer stays tiny, then read that file with the `Read` tool (which is unaffected by the ENOSPC issue) — and delete the log file immediately after.

2. **A globally-installed `pytest-homeassistant-custom-component` (site-packages, unrelated to agent-meta) autoloads as a pytest11 plugin** (`entry point name: homeassistant`) and its import chain (`homeassistant` → `hass_nabucasa` → `acme` → `pyOpenSSL`) crashes with `AttributeError: module 'lib' has no attribute 'GEN_EMAIL'` (pyOpenSSL/cryptography version mismatch) — this happens purely during plugin loading, before any test collection, so it breaks `pytest tests/...` unconditionally.
   - Fix: pass `-p no:homeassistant` to every pytest invocation in this repo/environment.

**Why:** Both issues are pre-existing environment state from unrelated work (likely a Home Assistant / HACS-related project sharing this user's site-packages and `/tmp`), not caused by agent-meta code or template changes.
**How to apply:** Always run `python3 -m pytest tests/ ... -p no:homeassistant` in this environment. If `/tmp` ENOSPC errors appear, redirect to an in-repo log file + Read tool instead of retrying raw Bash output capture, and never point `TMPDIR`/`--basetemp` at `/` for a full-suite run.
