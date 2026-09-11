"""Shared fixtures for Playwright browser tests against the admin UI.

The admin-server is started once per test session on a dedicated port (7421) so
multiple tests can reuse the same browser context without colliding with a
developer-run server on 7420.
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

try:
    from playwright.sync_api import sync_playwright
    has_playwright = True
except ImportError:
    has_playwright = False



REPO_ROOT = Path(__file__).resolve().parents[2]
TEST_PORT = 7421
BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


def _wait_for_server(url: str, timeout: float = 15.0) -> bool:
    """Poll the admin server until it answers or the timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status < 500:
                    return True
        except (urllib.error.URLError, ConnectionResetError, OSError):
            pass
        time.sleep(0.25)
    return False


@pytest.fixture(scope="session")
def admin_server():
    """Start admin-server for the test session and yield the base URL."""
    script = REPO_ROOT / "scripts" / "admin-server.py"
    if not script.exists():
        pytest.skip(f"admin-server script missing at {script}")

    proc = subprocess.Popen(
        [sys.executable, str(script), "--port", str(TEST_PORT)],
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env={**os.environ},
    )
    try:
        if not _wait_for_server(BASE_URL, timeout=15.0):
            proc.terminate()
            proc.wait(timeout=5.0)
            pytest.fail(f"admin-server did not respond on {BASE_URL} within 15s")
        yield BASE_URL
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


@pytest.fixture(scope="session")
def browser_ctx(admin_server):
    """Yield a (BrowserContext, base_url) tuple shared across the session."""
    if not has_playwright:
        pytest.skip("playwright is required for browser tests. Install with pip install playwright")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        try:
            yield ctx, admin_server
        finally:
            ctx.close()
            browser.close()


@pytest.fixture
def page(browser_ctx):
    """Function-scoped Page: one fresh tab per test, closed afterwards.

    Replaces the hand-rolled ``page = ctx.new_page(); try/finally: page.close()``
    boilerplate that used to live in every test.
    """
    ctx, _base = browser_ctx
    pg = ctx.new_page()
    try:
        yield pg
    finally:
        pg.close()


def save_and_wait(page, save_btn, section=None):
    """Click Save and block until the relevant PUT to project/section completes.

    Most project-form pages route saves through a single ``saveProjectSection()``
    call -> one ``PUT /api/config/project/section``. The Providers & Platforms
    page instead calls ``saveProjectSections()`` (see docs/ui/admin-ui.html),
    which fires several sequential PUTs to that *same* URL, one per section
    (``ai-providers``, ``platforms``, ``provider-options``, ...). Waiting on the
    first response there resolves too early and lets ``page.close()`` in fixture
    teardown race an in-flight later PUT — the exact race this helper exists to
    prevent, just moved further downstream.

    Pass ``section=`` (matching the ``section`` key in the PUT's JSON body) to
    block until that specific save round-trips instead of the first one. This
    is the real completion signal — not a fixed ``page.wait_for_timeout(...)`` —
    and prevents ``page.close()`` from aborting an in-flight save, which could
    leave the git-tracked .meta-config/project.yaml permanently polluted with
    test data.
    """
    def _matches(r):
        if not (r.url.endswith("/api/config/project/section") and r.request.method == "PUT"):
            return False
        if section is None:
            return True
        try:
            body = json.loads(r.request.post_data or "{}")
        except ValueError:
            return False
        return body.get("section") == section

    with page.expect_response(_matches):
        save_btn.click()
