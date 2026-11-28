"""Static structure checks for the Admin UI setup wizard (AC-10).

Reads ``docs/ui/admin-ui.html`` as text; no browser involved.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HTML = (REPO_ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def _init_body() -> str:
    start = HTML.index("async function init() {")
    end = HTML.index("\ninit();", start)
    return HTML[start:end]


def _wizard_body() -> str:
    start = HTML.index("function viewSetupWizard(")
    end = HTML.index("async function init() {", start)
    return HTML[start:end]


def test_init_branches_on_setup_required():
    body = _init_body()
    assert "setup_required" in body
    assert "viewSetupWizard(" in body


def test_setup_branch_skips_navigation_and_routes():
    body = _init_body()
    m = re.search(r"if\s*\(\s*[^)]*setup_required[^)]*\)\s*\{(.*?)\n  \}", body, re.S)
    assert m, "no setup_required branch in init()"
    branch = m.group(1)
    assert "viewSetupWizard(" in branch
    assert "return" in branch
    assert "buildSidebar" not in branch
    # normal routes/sidebar come strictly after the early return
    assert body.index("return", body.index("setup_required")) < body.index("buildSidebar()")
    assert body.index("return", body.index("setup_required")) < body.index("router.register")


def test_wizard_container_and_steps():
    w = _wizard_body()
    assert "setup-wizard" in w
    for label in ("Identity", "Provider", "Git", "Review"):
        assert label in w, label
    assert "Anlegen" in w
    assert "Erst-Sync starten" in w


def test_wizard_uses_three_setup_endpoints():
    w = _wizard_body()
    assert 'api.get("/api/setup/options")' in w
    assert 'api.post("/api/setup/config"' in w
    assert 'api.post("/api/setup/init-sync"' in w


def test_wizard_error_display_and_busy_state():
    w = _wizard_body()
    assert "err.status === 409" in w
    assert "err.body" in w and "detail" in w
    assert "disabled = true" in w and "disabled = false" in w


def test_reload_after_completion():
    w = _wizard_body()
    assert "location.reload()" in w
    assert w.index("/api/setup/init-sync") < w.index("location.reload()")


def test_wizard_has_no_unsafe_sinks():
    w = _wizard_body()
    assert "innerHTML" not in w
    assert "eval(" not in w
    assert "insertAdjacentHTML" not in w


def test_setup_branch_clears_nav():
    body = _init_body()
    start = body.index("if (mode.setup_required)")
    branch = body[start:body.index("return", start)]
    assert 'getElementById("nav").replaceChildren()' in branch


def test_busy_state_bound_to_sync_button():
    w = _wizard_body()
    start = w.index("syncBtn.addEventListener")
    handler = w[start:w.index("/api/setup/init-sync", start)]
    assert "syncBtn.disabled = true" in handler
    assert "Sync läuft" in handler
    assert "syncBtn.disabled = false" in w[start:]


def test_hashchange_cannot_destroy_wizard():
    router_src = HTML[HTML.index("class Router {"):HTML.index("const router = new Router()")]
    resolve = router_src[router_src.index("  resolve() {"):]
    assert "if (this.locked) return;" in resolve.split("\n", 3)[1] + resolve.split("\n", 3)[2]
    body = _init_body()
    assert body.index("router.locked = true") < body.index("viewSetupWizard(")
    assert body.index("router.locked = true") < body.index("router.resolve()")


def test_provider_step_gates_next_button():
    w = _wizard_body()
    assert 'nextBtn.disabled = s === "Provider" && !answers.providers.length' in w
    assert "nextBtn.disabled = !answers.providers.length" in w
