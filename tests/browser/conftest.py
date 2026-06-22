"""Shared fixtures for Playwright browser tests against the admin UI.

The admin-server is started once per test session on a dedicated port (7421) so
multiple tests can reuse the same browser context without colliding with a
developer-run server on 7420.
"""

import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

import pytest

try:
    from playwright.sync_api import sync_playwright
except ImportError as exc:  # pragma: no cover - import-time error path
    raise ImportError(
        "playwright is required for browser tests. Install with:\n"
        "  pip install playwright\n"
        "  playwright install chromium"
    ) from exc


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
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context()
        try:
            yield ctx, admin_server
        finally:
            ctx.close()
            browser.close()
