"""Interaction tests for the project form editors that actually click, fill and
save — not just render checks.

Covers the three pages the issue calls out:
- ``/#/project/orchestrator``      (enum select, styled boolean toggle, number)
- ``/#/project/providers``         (per-provider Options dict editor)
- ``/#/project/model-overrides``   (provider/role selects + model id input)

All three pages write straight to this repo's real ``.meta-config/project.yaml``
via ``PUT /api/config/project/section``, so every test snapshots the sections it
touches and restores the file. The restore is **byte-level** on purpose:
``ConfigManager.write`` re-serializes the whole document through
``yaml_dump_preserving_multiline``, so a section-level PUT round trip silently
drops every comment in the file and normalises quoting — it can never put the
repository config back exactly as it was found. ``_project_yaml_guard`` therefore
snapshots the raw bytes (plus the file mode and the server's ``.bak.*``
side-cars) and rewrites them verbatim in a ``finally`` block, so an assertion
failure, an exception or an interrupt that unwinds the stack all leave
``project.yaml`` byte-identical. The one thing no in-process ``finally`` can
survive is an uncatchable SIGKILL of the pytest process.

Every value these tests write is schema-valid by construction: the two dict /
override editors reject nothing themselves, but
``config/project-config.schema.json`` does (``provider-options.<P>`` and
``model-overrides`` both close their ``additionalProperties``), so an arbitrary
test key or model id would persist a document that the next ``sync.py`` run
refuses. ``_plan_option_edit`` / ``_plan_model_override`` pick the values from
the schema itself instead of hard-coding a marker string.
"""

import json
import os
import re
from contextlib import contextmanager
from copy import deepcopy
from pathlib import Path

import pytest
pytest.importorskip("playwright")
from playwright.sync_api import expect


REPO_ROOT = Path(__file__).resolve().parents[2]
PROJECT_YAML = REPO_ROOT / ".meta-config" / "project.yaml"
PROJECT_SCHEMA = REPO_ROOT / "config" / "project-config.schema.json"

# The model-overrides editor builds its input with ``list="global-model-list"``
# and assigns the value through the DOM property, so this is the only stable
# structural handle on a model cell (see _rows_with_model).
MODEL_INPUT = 'input[list="global-model-list"]'


# --------------------------------------------------------------------------- #
# Schema helpers — keep every test payload inside config/project-config.schema
# --------------------------------------------------------------------------- #

def _schema_section(name):
    """Return the ``properties[name]`` subschema of the project config schema."""
    with PROJECT_SCHEMA.open(encoding="utf-8") as fh:
        return json.load(fh)["properties"][name]


def _schema_types(node):
    """Every JSON type a schema node (or its anyOf/oneOf/allOf branch) allows."""
    types = {node["type"]} if isinstance(node.get("type"), str) else set()
    for combiner in ("anyOf", "oneOf", "allOf"):
        for branch in node.get(combiner) or []:
            if isinstance(branch, dict) and isinstance(branch.get("type"), str):
                types.add(branch["type"])
    return types


def _enum_values(node):
    """Every enum member a schema node (or its combined branch) accepts.

    ``prompt-mode`` declares its values directly, while a model-override value
    schema wraps the enums in ``anyOf`` next to a ``pattern`` branch — both
    forms have to be collected or the planner finds nothing.
    """
    values = list(node.get("enum") or [])
    for combiner in ("anyOf", "oneOf", "allOf"):
        for branch in node.get(combiner) or []:
            if isinstance(branch, dict):
                values.extend(_enum_values(branch))
    return values


def _plan_option_edit(options):
    """Pick a ``provider-options`` key the dict editor can actually render.

    ``provider-options.<Provider>`` sets ``additionalProperties: false``, so a
    made-up test key is schema-invalid. The nested dict editor only emits
    ``string`` or ``bool`` values, which narrows the usable surface to
    Continue's ``prompt-mode`` (string enum) and ``generate-prompts`` (boolean)
    — every other provider's keys are arrays, which the editor cannot produce.

    Returns ``(provider, key, old_value, new_value)``. ``old_value`` is ``None``
    when the key is not set yet, in which case the test only adds a row;
    otherwise it removes the row first, because the editor rejects a duplicate
    key. ``new_value`` is always schema-valid and differs from ``old_value`` so
    persistence is observable.
    """
    schema = _schema_section("provider-options")
    for provider, sub in schema["properties"].items():
        current = options.get(provider) or {}
        for key, prop in sub.get("properties", {}).items():
            types = _schema_types(prop)
            if "boolean" in types:
                allowed = [True, False]
            elif "string" in types:
                allowed = _enum_values(prop) or [f"e2e-probe-{key}"]
            else:
                continue
            old = current.get(key)
            fresh = [v for v in allowed if v != old]
            if fresh:
                return provider, key, old, fresh[0]
    raise AssertionError(
        "config/project-config.schema.json declares no scalar provider-options "
        "key the dict editor could render"
    )


def _plan_model_override(existing):
    """Pick a schema-valid ``model-overrides`` row that does not collide.

    ``model-overrides`` only allows the four provider blocks it enumerates
    (``additionalProperties`` at the top level is the legacy *flat* string
    form, not a nested object), and every value must match one of that
    provider's tier/family enums or its model-id ``pattern``. So the model value
    is taken from the provider's enum members rather than a marker string, and
    both the role and the value are chosen to be unused in ``existing``.
    """
    schema = _schema_section("model-overrides")
    used_models = {m for block in existing.values() if isinstance(block, dict)
                   for m in block.values()}
    for provider, sub in schema["properties"].items():
        values = _enum_values(sub.get("additionalProperties", {}))
        if not values:
            continue
        model = next((v for v in values if v not in used_models), None)
        if model is None:
            continue
        return provider, model, set(existing.get(provider) or {})
    raise AssertionError(
        "config/project-config.schema.json declares no model-overrides provider "
        "with a free tier value to test with"
    )


# --------------------------------------------------------------------------- #
# project.yaml backup / restore
# --------------------------------------------------------------------------- #

def _read_project(ctx, base):
    response = ctx.request.get(f"{base}/api/config/project")
    assert response.ok, (
        f"could not read project.yaml: {response.status}"
    )
    return response.json()


def _snapshot_project_sections(ctx, base, sections):
    """Read an exact copy of the project sections a UI save may replace."""
    project = _read_project(ctx, base)
    missing = [section for section in sections if section not in project]
    assert not missing, f"project.yaml is missing sections required by test: {missing}"
    return {section: deepcopy(project[section]) for section in sections}


def _write_bytes(path, data, mode):
    """Replace ``path`` with ``data`` atomically, preserving ``mode``."""
    tmp = path.with_name(path.name + ".pytest-restore")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    os.chmod(path, mode)


@contextmanager
def _project_yaml_guard():
    """Byte-exact snapshot/restore of ``.meta-config/project.yaml``.

    ``ConfigManager.write`` drops a ``project.yaml.bak.<stamp>`` side-car next
    to the file on every save and prunes the oldest ones down to ``MAX_BACKUPS``,
    so a test run both *creates* and *deletes* side-cars. Restoring only the
    main file would leave the newest backup holding a copy of the test payload
    and would shrink the pre-existing set, so the side-cars are snapshotted as
    well: files the test created are removed, and files the server rewrote or
    pruned are put back byte-for-byte.
    """
    original = PROJECT_YAML.read_bytes()
    mode = PROJECT_YAML.stat().st_mode & 0o7777
    sidecars = {path: (path.read_bytes(), path.stat().st_mode & 0o7777)
                for path in PROJECT_YAML.parent.glob(PROJECT_YAML.name + ".bak.*")}
    try:
        yield
    finally:
        if not PROJECT_YAML.exists() or PROJECT_YAML.read_bytes() != original:
            _write_bytes(PROJECT_YAML, original, mode)
        for path in PROJECT_YAML.parent.glob(PROJECT_YAML.name + ".bak.*"):
            if path not in sidecars:
                path.unlink(missing_ok=True)
        for path, (data, sidecar_mode) in sidecars.items():
            if not path.exists() or path.read_bytes() != data:
                _write_bytes(path, data, sidecar_mode)
        assert PROJECT_YAML.exists(), "project.yaml vanished during the browser test"
        assert PROJECT_YAML.read_bytes() == original, (
            "could not restore .meta-config/project.yaml byte-for-byte"
        )


@contextmanager
def _project_section_guard(ctx, base, sections):
    """Snapshot the sections a test may overwrite and restore the file exactly.

    Yields the section snapshot so a test can read its own pre-test state (to
    pick non-colliding values, for instance). Restoration is byte-level — see
    :func:`_project_yaml_guard` — so byte equality subsumes any per-section
    comparison, and the snapshot doubles as the precondition check that the
    sections the test is about to touch actually exist.
    """
    with _project_yaml_guard():
        snapshot = _snapshot_project_sections(ctx, base, sections)
        yield snapshot


# --------------------------------------------------------------------------- #
# Locator helpers
# --------------------------------------------------------------------------- #

def _rows_with_model(rows, model):
    """Rows whose model cell *displays* ``model``.

    ``viewProjectModelOverrides`` assigns the model with
    ``modelInp.value = row.model``, i.e. a DOM property. The input therefore
    carries no ``value`` attribute and an ``input[value="..."]`` attribute
    selector matches nothing after a reload. Reading the property is the only
    correct way to find a persisted model cell.
    """
    return [rows.nth(i) for i in range(rows.count())
            if rows.nth(i).locator(MODEL_INPUT).input_value() == model]


def _option_rows_by_key(rows, key):
    """Dict-editor rows whose key cell displays ``key`` (keyed by property too)."""
    return [rows.nth(i) for i in range(rows.count())
            if rows.nth(i).locator("input").nth(0).input_value() == key]


def _editor_value(value):
    """How the dict editor renders a schema value in its text cell."""
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value)


def _save_and_wait(page, save_btn, done_text):
    """Click Save and block until the save round trip reported success.

    Asserting only that no error toast is up passes *instantly* -- at that
    moment the request is usually still in flight -- so a ``page.reload()`` right
    after it can cancel the PUT and the reload then reads the pre-save file. The
    app emits its own completion message once every section has been answered
    ("Saved project.<key>" for a single-section save, "All sections saved" for
    the providers page's multi-section save), which is what this waits for.
    """
    save_btn.click()
    expect(page.get_by_text(done_text, exact=True)).to_be_visible(timeout=15000)
    expect(page.locator(".toast-error")).to_have_count(0, timeout=2000)


def _add_option_row(add_btn, rows, key, value):
    """Add an Options row through the UI and commit the key rename.

    ``Tab`` is the user-equivalent commit gesture: moving focus off the key cell
    is the only browser event that makes ``renderDictEditor`` run its rename
    handler. ``fill()`` alone does not commit, and a synthetic
    ``dispatch_event("change")`` runs the handler twice — once synthetic, once
    natively when focus is lost afterwards — so the second run trips the
    duplicate-key guard against the rename just performed and the cell silently
    reverts to ``NEW_KEY_n``.
    """
    add_btn.click()
    key_input = rows.last.locator("input").nth(0)
    key_input.fill(key)
    key_input.press("Tab")
    expect(key_input).to_have_value(key)
    row = rows.last
    if isinstance(value, bool):
        row.locator("select").select_option("bool")
    row.locator("input").nth(1).fill(_editor_value(value))
    expect(row.locator("input").nth(0)).to_have_value(key)
    expect(row.locator("input").nth(1)).to_have_value(_editor_value(value))


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_orchestrator_mode_checkbox_and_number_roundtrip(browser_ctx):
    """User flow: open Orchestrator, flip Mode + Direct dispatch + Max depth,
    save, see it stick — then restore the original section exactly."""
    ctx, base = browser_ctx
    with _project_section_guard(ctx, base, ("orchestrator",)):
        page = ctx.new_page()
        try:
            page.goto(f"{base}/#/project/orchestrator")
            page.wait_for_load_state("networkidle")

            def mode_select():
                return page.locator(".field").filter(
                    has=page.get_by_text("Mode", exact=True)
                ).locator("select")

            def dd_field():
                return page.locator(".field").filter(
                    has=page.get_by_text("Direct dispatch enabled", exact=True)
                )

            def dd_is_checked():
                return dd_field().locator('input[type="checkbox"]').is_checked()

            def dd_toggle():
                """Click the visible track of the styled boolean toggle.

                The raw checkbox is a 0x0, opacity:0 a11y hook (`.toggle input`);
                `.slider` is the 40x22 track a user actually clicks, and the
                wrapping <label> forwards the activation to the checkbox.
                """
                slider = dd_field().locator(".slider")
                expect(slider).to_be_visible(timeout=5000)
                slider.click()

            def depth_input():
                # Max depth lives in a .field-row inside a .panel, not in a
                # .field like Mode and Direct dispatch.
                return page.locator(".field-row").filter(
                    has=page.get_by_text("Max depth", exact=True)
                ).locator('input[type="number"]')

            original_mode = mode_select().input_value()
            original_dd = dd_is_checked()
            original_depth = depth_input().input_value()

            new_mode = "advisory" if original_mode != "advisory" else "strict"
            new_depth = "7" if original_depth != "7" else "9"

            save_btn = page.get_by_role("button", name="Save", exact=True)

            try:
                # --- enum select ---
                mode_select().select_option(new_mode)
                assert mode_select().input_value() == new_mode

                # --- styled boolean toggle ---
                dd_toggle()
                assert dd_is_checked() == (not original_dd)

                # --- number input ---
                depth_input().fill(new_depth)
                assert depth_input().input_value() == new_depth

                _save_and_wait(page, save_btn, "Saved project.orchestrator")

                page.reload()
                page.wait_for_load_state("networkidle")
                expect(mode_select()).to_have_value(new_mode, timeout=5000)
                assert dd_is_checked() == (not original_dd)
                assert depth_input().input_value() == new_depth
                saved = _read_project(ctx, base)["orchestrator"]
                assert saved["mode"] == new_mode
                assert saved["delegation"]["max_depth"] == int(new_depth)
            finally:
                # Put the form back through the same controls, so a failing
                # assertion never leaves a half-edited config behind.
                mode_select().select_option(original_mode)
                if dd_is_checked() != original_dd:
                    dd_toggle()
                depth_input().fill(original_depth)
                _save_and_wait(page, save_btn, "Saved project.orchestrator")
        finally:
            page.close()


def test_providers_option_add_edit_remove_roundtrip(browser_ctx):
    """User flow: add an Options KV row through the UI, save, confirm it
    persisted, then remove it again through the delete-confirmation modal. The
    complete project sections are restored afterward."""
    ctx, base = browser_ctx
    with _project_section_guard(
        ctx,
        base,
        ("ai-providers", "platforms", "provider-options", "provider-isolation"),
    ) as snapshot:
        provider, option_key, old_value, new_value = _plan_option_edit(
            snapshot["provider-options"]
        )
        shown_value = _editor_value(new_value)
        page = ctx.new_page()
        try:
            page.goto(f"{base}/#/project/providers")
            page.wait_for_load_state("networkidle")

            def rebind():
                """Re-derive the locators for ``provider``'s Options editor.

                Each provider gets a collapsible section whose header carries the
                provider name in a ``span.mono`` inside a plain ``div`` — the AI
                provider checkboxes reuse ``span.mono`` too, so the ``div >``
                combinator keeps those out. The body div holding the dict editor
                is the header's next sibling *div*.
                """
                header = page.locator(
                    "div > span.mono", has_text=re.compile(rf"^{re.escape(provider)}$")
                )
                expect(header).to_have_count(1, timeout=5000)
                body = header.locator("xpath=..").locator("xpath=following-sibling::div[1]")
                add = body.get_by_role("button", name="+ Add Options", exact=True)
                return add, add.locator("xpath=preceding-sibling::div[1]").locator("> div")

            add_btn, rows = rebind()
            expect(add_btn).to_be_visible(timeout=5000)
            save_btn = page.get_by_role("button", name="Save", exact=True)

            try:
                # --- clear the key so it can be re-added through the UI ---
                if old_value is not None:
                    existing = _option_rows_by_key(rows, option_key)
                    assert len(existing) == 1, (
                        f"expected exactly one {option_key!r} option row, "
                        f"found {len(existing)}"
                    )
                    existing[0].locator(".btn-danger").click()
                    page.get_by_role("button", name="Delete", exact=True).click()
                    assert not _option_rows_by_key(rows, option_key), (
                        f"{option_key!r} row survived the delete-confirmation modal"
                    )

                # --- add a row and fill it in ---
                _add_option_row(add_btn, rows, option_key, new_value)

                # --- save and confirm the new option persisted ---
                _save_and_wait(page, save_btn, "All sections saved")

                page.reload()
                page.wait_for_load_state("networkidle")
                add_btn, rows = rebind()
                persisted = _option_rows_by_key(rows, option_key)
                assert len(persisted) == 1, (
                    f"expected exactly one persisted {option_key!r} option row, "
                    f"found {len(persisted)}"
                )
                expect(persisted[0].locator("input").nth(1)).to_have_value(shown_value)
                saved = _read_project(ctx, base)["provider-options"]
                assert saved[provider][option_key] == new_value
            finally:
                # Undo through the UI: drop the row again, re-adding the
                # original value when the key existed before the test.
                add_btn, rows = rebind()
                leftovers = _option_rows_by_key(rows, option_key)
                if leftovers:
                    leftovers[0].locator(".btn-danger").click()
                    page.get_by_role("button", name="Delete", exact=True).click()
                    if old_value is not None:
                        _add_option_row(add_btn, rows, option_key, old_value)
                    _save_and_wait(
                        page, page.get_by_role("button", name="Save", exact=True),
                        "All sections saved",
                    )
        finally:
            page.close()


def test_model_overrides_add_row_select_and_save_roundtrip(browser_ctx):
    """User flow: on Model Overrides, add a row, pick a provider + role via
    the dropdowns, type a model id, save, and confirm the count/status updates;
    the exact model-overrides section is restored afterward."""
    ctx, base = browser_ctx
    with _project_section_guard(ctx, base, ("model-overrides",)) as snapshot:
        wanted_provider, wanted_model, used_roles = _plan_model_override(
            snapshot["model-overrides"]
        )
        page = ctx.new_page()
        try:
            page.goto(f"{base}/#/project/model-overrides")
            page.wait_for_load_state("networkidle")

            add_row_btn = page.get_by_role("button", name="Add override", exact=True)
            expect(add_row_btn).to_be_visible(timeout=5000)
            save_btn = page.get_by_role("button", name="Save", exact=True)

            rows = page.locator("table.data tbody tr")
            # The button is rendered after the table, so its visibility
            # guarantees the first render already happened.
            before_count = rows.count()
            before_models = [rows.nth(i).locator(MODEL_INPUT).input_value()
                             for i in range(before_count)]
            assert wanted_model not in before_models, (
                f"model {wanted_model!r} is already overridden, the "
                "persistence assertion could not be unique"
            )

            try:
                add_row_btn.click()
                expect(rows).to_have_count(before_count + 1)
                new_row = rows.last

                # Only pick a provider the project schema declares a nested
                # block for; the dropdown also offers providers (Codex,
                # KimiCode, ZCode, ...) that would be schema-invalid here.
                prov_select = new_row.locator("select").nth(0)
                prov_values = [
                    prov_select.locator("option").nth(i).get_attribute("value")
                    for i in range(prov_select.locator("option").count())
                ]
                assert wanted_provider in prov_values, (
                    f"provider {wanted_provider!r} missing from the dropdown: {prov_values}"
                )
                prov_select.select_option(wanted_provider)

                role_select = new_row.locator("select").nth(1)
                role_values = [
                    role_select.locator("option").nth(i).get_attribute("value")
                    for i in range(role_select.locator("option").count())
                ]
                free_roles = [r for r in role_values if r and r not in used_roles]
                assert free_roles, (
                    f"every role is already overridden for {wanted_provider!r}, "
                    "the persistence assertion could not be unique"
                )
                wanted_role = free_roles[0]
                role_select.select_option(wanted_role)

                model_input = new_row.locator(MODEL_INPUT)
                model_input.fill(wanted_model)
                expect(model_input).to_have_value(wanted_model)

                assert prov_select.input_value() == wanted_provider
                assert role_select.input_value() == wanted_role

                _save_and_wait(page, save_btn, "Saved project.model-overrides")

                page.reload()
                page.wait_for_load_state("networkidle")
                rows = page.locator("table.data tbody tr")
                expect(rows).to_have_count(before_count + 1, timeout=5000)
                persisted = _rows_with_model(rows, wanted_model)
                assert len(persisted) == 1, (
                    f"expected exactly one row displaying {wanted_model!r}, "
                    f"found {len(persisted)}"
                )
                expect(persisted[0].locator("select").nth(0)).to_have_value(wanted_provider)
                expect(persisted[0].locator("select").nth(1)).to_have_value(wanted_role)
                saved = _read_project(ctx, base)["model-overrides"]
                assert saved[wanted_provider][wanted_role] == wanted_model
            finally:
                # Undo through the UI, so a failing assertion never leaves the
                # row behind for the next run to trip over.
                rows = page.locator("table.data tbody tr")
                leftovers = _rows_with_model(rows, wanted_model)
                if leftovers:
                    leftovers[0].locator(".btn-danger").click()
                    expect(rows).to_have_count(before_count)
                    _save_and_wait(
                        page, page.get_by_role("button", name="Save", exact=True),
                        "Saved project.model-overrides",
                    )
        finally:
            page.close()
