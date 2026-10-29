"""Static assertions for the "Backup in progress" hang fix (issue #897 AC3).

The overlay used to stay open forever when ``POST /api/backups/create`` never
settled, because a never-settling promise never reaches the ``finally`` that
calls ``hideModal()``. The fix is a per-call request deadline in the Admin UI
API layer plus an explicit budget on the backup-create call.

Scope note: these assertions are STATIC evidence — they read
``docs/ui/admin-ui.html`` as text and pin the wiring. They are not runtime
proof that a hung request aborts after the deadline; that would need a browser
test, which the decision for this issue explicitly excludes.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")

EXPECTED_TIMEOUT_MS = 180000


def _backup_create_region() -> str:
    """The Create-Backup button handler, from the API call to its label."""
    start = HTML.index('api.post("/api/backups/create"')
    end = HTML.index('["Create Backup"]', start)
    return HTML[start:end]


# ---------------------------------------------------------------------------
# API layer: opt-in timeout, default behaviour unchanged
# ---------------------------------------------------------------------------


def test_timed_fetch_uses_abort_controller_and_clears_timer():
    assert "async function timedFetch(url, opts, timeoutMs)" in HTML
    block = HTML[HTML.index("async function timedFetch("):]
    block = block[: block.index("async function authFetch(")]
    assert "new AbortController()" in block
    assert "controller.abort()" in block
    assert "signal: controller.signal" in block
    assert "clearTimeout(timer)" in block


def test_timed_fetch_maps_abort_to_timeout_error():
    """A deadline hit must be distinguishable from a network/HTTP failure."""
    block = HTML[HTML.index("async function timedFetch("):]
    block = block[: block.index("async function authFetch(")]
    assert re.search(r'if \(e && e\.name === "AbortError"\)', block)
    assert 'err.name = "TimeoutError";' in block
    assert "err.timeoutMs = timeoutMs;" in block


def test_auth_fetch_timeout_is_opt_in():
    """No global default: omitting the option must keep requests unbounded."""
    assert "async function authFetch(url, options = {}, timeout = {})" in HTML
    assert "const timeoutMs = timeout.timeoutMs || 0;" in HTML
    # both fetch attempts (initial + post-token-retry) go through timedFetch
    block = HTML[HTML.index("async function authFetch("):]
    block = block[: block.index("class API {")]
    assert block.count("await timedFetch(url, opts, timeoutMs)") == 2
    assert "await fetch(url, opts)" not in block


def test_post_forwards_per_call_options():
    assert "async post(path, body = {}, options = {})" in HTML
    region = HTML[HTML.index("async post(path, body = {}, options = {})"):]
    region = region[: region.index("async delete(")]
    assert "}, options);" in region


# ---------------------------------------------------------------------------
# Backup call site: named constant + distinguishable message
# ---------------------------------------------------------------------------


def test_backup_timeout_constant_exists():
    match = re.search(r"const BACKUP_CREATE_TIMEOUT_MS = (\d+);", HTML)
    assert match, "BACKUP_CREATE_TIMEOUT_MS not declared"
    assert int(match.group(1)) == EXPECTED_TIMEOUT_MS
    # the user-facing message derives its seconds from the same constant, so
    # value and wording cannot drift apart
    assert "const BACKUP_CREATE_TIMEOUT_SECONDS = BACKUP_CREATE_TIMEOUT_MS / 1000;" in HTML


def test_backup_create_call_passes_the_timeout():
    assert (
        'api.post("/api/backups/create", { label }, { timeoutMs: BACKUP_CREATE_TIMEOUT_MS })'
        in HTML
    )


def test_timeout_produces_a_distinguishable_message():
    region = _backup_create_region()
    assert 'e.name === "TimeoutError"' in region
    assert "Backup timed out after " in region
    assert "BACKUP_CREATE_TIMEOUT_SECONDS" in region
    # the generic error path (and its alert) stays for non-timeout failures
    assert 'alert("Error: " + e)' in region


def test_finally_still_closes_the_overlay():
    """The overlay must close on every settlement path, timeout included."""
    region = _backup_create_region()
    assert re.search(r"\}\s*finally\s*\{", region), "finally block missing"
    # hideModal() and load() live inside that finally, in that order
    assert re.search(r"finally\s*\{[^}]*hideModal\(\);[^}]*load\(\);", region, re.S)
    # the overlay is still opened with no footer (no cancel button to press)
    assert 'showModal("Backup in progress", body, [])' in HTML
