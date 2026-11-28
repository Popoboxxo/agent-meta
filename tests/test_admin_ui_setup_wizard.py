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


# --------------------------------------------------------------------------- #
# Task 5 / AC-13: section-save error display (no browser, structure only)
# --------------------------------------------------------------------------- #

_WRITE_CALL = re.compile(
    r'await api\.(?:put|post)\(\s*["`](/api/(?:config/project(?:/section)?["`]|'
    r'submodule-protection|model-source/batch|model-inherit))'
)


def _balanced_block(src: str, open_idx: int) -> str:
    """Return the text of the ``{...}`` block whose ``{`` is at ``open_idx``."""
    depth = 0
    for i in range(open_idx, len(src)):
        if src[i] == "{":
            depth += 1
        elif src[i] == "}":
            depth -= 1
            if depth == 0:
                return src[open_idx + 1:i]
    raise AssertionError("unbalanced braces")


def _catch_block(src: str, start: int) -> str:
    """Return the body of the ``catch`` that belongs to the enclosing ``try``.

    Braces are matched from the write call: the call must sit inside a
    ``try {`` block that closes before the ``catch`` (no unrelated later catch).
    """
    pos = src.rfind("try {", max(0, start - 3000), start)
    assert pos != -1, f"write call not inside try: {src[start:start + 120]!r}"
    try_body = _balanced_block(src, pos + len("try "))
    try_end = pos + len("try ") + 1 + len(try_body) + 1
    assert try_end > start, f"try block closes before the call: {src[start:start + 120]!r}"
    m = re.match(r"\s*catch\s*(?:\(\w+\))?\s*\{", src[try_end:])
    assert m, f"no catch directly after try near: {src[start:start + 120]!r}"
    return _balanced_block(src, try_end + m.end() - 1)


def test_api_error_carries_server_detail():
    cls = HTML[HTML.index("class APIError extends Error"):]
    cls = cls[:cls.index("\n}\n")]
    assert "body?.detail" in cls and "body?.error" in cls


def test_save_project_section_helper_shows_error_and_rethrows():
    start = HTML.index("async function saveProjectSection(")
    body = HTML[start:HTML.index("/** Save multiple sections", start)]
    ok_pos = body.index('"success"')
    catch_pos = body.index("catch (err)")
    assert ok_pos < catch_pos, "success toast must sit in the try branch"
    err_branch = body[catch_pos:]
    assert 'toast(`Save failed: ${err.message}`, "error")' in err_branch
    assert "statusEl.textContent" in err_branch
    assert '"success"' not in err_branch
    assert "throw err;" in err_branch


def test_save_project_sections_success_toast_only_after_all_saved():
    start = HTML.index("async function saveProjectSections(")
    body = HTML[start:HTML.index("/* ====", start)]
    assert body.index("await saveProjectSection(") < body.index('"All sections saved"')
    assert "catch" not in body  # a failing section propagates, no success toast


def test_every_direct_project_write_has_error_branch_without_success_toast():
    calls = list(_WRITE_CALL.finditer(HTML))
    assert len(calls) >= 10, "expected the known direct project write sites"
    for m in calls:
        if m.group(1) == "/api/model-inherit":
            continue  # setInherit() helper; callers covered by the inherit test
        seg = _catch_block(HTML, m.start())
        shown = ('"error"' in seg or "Failed" in seg or "Save failed" in seg)
        assert shown, f"catch does not surface the error near: {HTML[m.start():m.start() + 120]!r}"
        assert '"success"' not in seg, (
            f"success toast in error branch near: {HTML[m.start():m.start() + 120]!r}")


def test_model_source_batch_error_uses_toast_not_blocking_alert():
    start = HTML.index('api.post("/api/model-source/batch"')
    seg = _catch_block(HTML, start)
    assert 'toast("Failed to save model source: "' in seg and '"error"' in seg
    assert "alert(" not in seg


def test_model_inherit_toggle_shows_server_error():
    start = HTML.index("await setInherit(prov, enabled);")
    seg = HTML[start:start + 700]
    assert "catch (err)" in seg
    assert 'toast(`model-inherit failed (${prov}): ${err.message}`, "error")' in seg
