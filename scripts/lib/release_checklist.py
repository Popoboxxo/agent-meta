"""Structured release checklist: normalizer, validator, resolver, renderer.

The ``release-checklist`` project block is optional. Absent block, ``{}``,
``null`` or ``mode: off`` means zero behavior change. All logic lives here;
``config.py`` only calls into this module.

Two validator entry points share the same rule set:

* :func:`collect_release_checklist_errors` -- non-exiting, returns messages.
  Used by the Admin-UI section guard and the resolver.
* :func:`validate_release_checklist` -- hard exit for the config load.

The YAML-1.1 boolean trap: an unquoted ``mode: off`` parses as ``False``. The
normalizer maps only ``False`` to ``"off"``; ``True`` stays and the validator
rejects it with "quote the value" (SPEC-RELEASE-CHECKLIST-2026-10-31 §9.4).
"""

from __future__ import annotations

import logging
import re
import sys
from pathlib import Path

VALID_MODES: tuple[str, ...] = ("off", "advisory", "strict")
VALID_PHASES: tuple[str, ...] = ("precondition", "step")

RESERVED_DEFAULT_ITEMS: tuple[tuple[str, str, bool], ...] = (
    ("tests-green", "precondition", False),
    ("dod-met", "precondition", True),
    ("changelog-updated", "precondition", False),
    ("readme-current", "precondition", True),
    ("version-bumped", "step", False),
    ("build-created", "step", False),
    ("git-tag-push", "step", False),
)

_VALID_CHECKS: tuple[str, ...] = ("agent", "script")
_BLOCK_KEYS: tuple[str, ...] = ("mode", "items")
_ITEM_KEYS: tuple[str, ...] = (
    "id",
    "task",
    "verification",
    "check",
    "script",
    "phase",
    "required",
    "applies-when",
)
_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")
_QUOTE_HINT = "Invalid -- quote the value: unquoted off/on are YAML booleans."

# The rendered block is inserted into ``release.md`` before the unknown-
# placeholder check, so the free-text item fields must not contain a
# placeholder opener/closer. Enforced here; ``render_release_checklist_block``
# only documents the invariant.
_PLACEHOLDER_MARKERS: tuple[str, ...] = ("{{", "}}")
_FREE_TEXT_ITEM_KEYS: tuple[str, ...] = ("task", "verification", "script", "applies-when")

_LOGGER = logging.getLogger(__name__)


def normalize_release_checklist_mode(config: dict) -> None:
    """Map a YAML boolean ``False`` under ``release-checklist.mode`` to ``"off"``.

    Unlike ``subagent_permissions`` this maps **only** ``False``. ``True`` is
    genuine user intent and must be reported by the validator ("quote the
    value"), never silently downgraded.
    """
    block = config.get("release-checklist")
    if not isinstance(block, dict):
        return
    if block.get("mode") is False:
        block["mode"] = "off"


def collect_release_checklist_errors(config: dict) -> list[str]:
    """Return validation errors for ``release-checklist``; never raises, never exits.

    An absent, null or empty block produces no errors. Every message starts
    with the offending path (``release-checklist.items[2].script``) so the
    Admin-UI guard and the config-load error can point at the exact field.
    """
    block = config.get("release-checklist")
    if block is None:
        return []
    if not isinstance(block, dict):
        return [
            (
                "release-checklist: expected a mapping, "
                f"got {type(block).__name__}"
            )
        ]

    errors: list[str] = []
    for key in block:
        if key not in _BLOCK_KEYS:
            errors.append(
                f"release-checklist.{key}: unknown key; "
                f"allowed keys are: {', '.join(_BLOCK_KEYS)}"
            )

    if "mode" in block and block["mode"] is not False:
        mode_value = block["mode"]
        if not isinstance(mode_value, str) or mode_value not in VALID_MODES:
            errors.append(
                f"release-checklist.mode: invalid value {mode_value!r}; "
                f"valid values are: {', '.join(VALID_MODES)}. {_QUOTE_HINT}"
            )

    if "items" not in block:
        return errors
    items = block["items"]
    if not isinstance(items, list):
        errors.append(
            "release-checklist.items: expected an array, "
            f"got {type(items).__name__}"
        )
        return errors

    reserved = {item_id for item_id, _phase, _na_allowed in RESERVED_DEFAULT_ITEMS}
    seen: dict[str, int] = {}
    for index, item in enumerate(items):
        errors.extend(_collect_item_errors(index, item, reserved, seen))
    return errors


def _collect_item_errors(
    index: int,
    item: object,
    reserved: set[str],
    seen: dict[str, int],
) -> list[str]:
    """Validate one checklist item and return its error messages."""
    prefix = f"release-checklist.items[{index}]"
    if not isinstance(item, dict):
        return [f"{prefix}: expected a mapping, got {type(item).__name__}"]

    errors: list[str] = []
    for key in item:
        if key not in _ITEM_KEYS:
            errors.append(
                f"{prefix}.{key}: unknown key; "
                f"allowed keys are: {', '.join(_ITEM_KEYS)}"
            )

    item_id = item.get("id")
    if "id" not in item:
        errors.append(f"{prefix}.id: missing required key")
    elif not isinstance(item_id, str):
        errors.append(
            f"{prefix}.id: expected a string, got {type(item_id).__name__}"
        )
    elif not _ID_PATTERN.match(item_id):
        errors.append(
            f"{prefix}.id: invalid id {item_id!r}; "
            "must match ^[a-z0-9][a-z0-9-]*$"
        )
    else:
        if item_id in reserved:
            errors.append(
                f"{prefix}.id: {item_id!r} is reserved for a default item"
            )
        if item_id in seen:
            errors.append(
                f"{prefix}.id: duplicate id {item_id!r} "
                f"(first defined at items[{seen[item_id]}])"
            )
        else:
            seen[item_id] = index

    for key in ("task", "verification"):
        if key not in item:
            errors.append(f"{prefix}.{key}: missing required key")
        elif not isinstance(item[key], str) or not item[key].strip():
            errors.append(f"{prefix}.{key}: expected a non-empty string")

    if "required" in item and not isinstance(item["required"], bool):
        errors.append(
            f"{prefix}.required: expected true/false (bool), "
            f"got {item['required']!r}"
        )

    check_valid = True
    if "check" in item and item["check"] not in _VALID_CHECKS:
        check_valid = False
        errors.append(
            f"{prefix}.check: invalid value {item['check']!r}; "
            f"valid values are: {', '.join(_VALID_CHECKS)}"
        )
    effective_check = item.get("check", "agent")

    if "phase" in item and item["phase"] not in VALID_PHASES:
        errors.append(
            f"{prefix}.phase: invalid value {item['phase']!r}; "
            f"valid values are: {', '.join(VALID_PHASES)}"
        )

    if "applies-when" in item:
        applies_when = item["applies-when"]
        if not isinstance(applies_when, str) or not applies_when.strip():
            errors.append(
                f"{prefix}.applies-when: expected a non-empty string"
            )

    for key in _FREE_TEXT_ITEM_KEYS:
        value = item.get(key)
        if not isinstance(value, str):
            continue
        marker = next((m for m in _PLACEHOLDER_MARKERS if m in value), None)
        if marker is not None:
            errors.append(
                f"{prefix}.{key}: must not contain the placeholder marker "
                f"{marker!r}"
            )

    if "script" in item:
        script = item["script"]
        if not isinstance(script, str):
            errors.append(
                f"{prefix}.script: expected a string, "
                f"got {type(script).__name__}"
            )
        elif not script.strip():
            errors.append(
                f"{prefix}.script: must not be empty "
                "(whitespace-only counts as empty)"
            )
        elif "\n" in script or "\r" in script:
            errors.append(
                f"{prefix}.script: must be a single line (no line break)"
            )
        if check_valid and effective_check != "script":
            errors.append(
                f"{prefix}.script: not allowed when check is {effective_check!r}"
            )
    elif check_valid and effective_check == "script":
        errors.append(f"{prefix}.script: required when check is 'script'")

    return errors


def validate_release_checklist(config: dict, config_path: Path) -> None:
    """Hard-validate ``release-checklist``: print every error and exit 1.

    The config load is the only place with a hard exit. All read paths use
    :func:`collect_release_checklist_errors` instead.
    """
    errors = collect_release_checklist_errors(config)
    if not errors:
        return
    for message in errors:
        print(f"ERROR: {config_path}: {message}", file=sys.stderr)
    sys.exit(1)


# --- Resolver --------------------------------------------------------------

def _off_checklist(reason: str) -> dict:
    """Log a warning and return the inert checklist shape."""
    _LOGGER.warning("release-checklist: %s; treating as off", reason)
    return {"mode": "off", "items": []}


def resolve_release_checklist(config: dict) -> dict:
    """Resolve ``release-checklist`` into ``{"mode": str, "items": list[dict]}``.

    Never raises and never exits: any broken structure degrades to
    ``{"mode": "off", "items": []}`` with a logged warning. Items are filled
    with the defaults from SPEC §9.3 (``check="agent"``,
    ``phase="precondition"``, ``required=True``); ``script`` and
    ``applies-when`` only appear when configured.
    """
    try:
        return _resolve_release_checklist(config)
    except Exception as exc:  # noqa: BLE001 - the read path must never raise
        return _off_checklist(f"resolver failed ({exc})")


def _resolve_release_checklist(config: dict) -> dict:
    if not isinstance(config, dict):
        return _off_checklist("config is not a mapping")
    block = config.get("release-checklist")
    if block is None:
        return {"mode": "off", "items": []}
    if not isinstance(block, dict):
        return _off_checklist(
            f"expected a mapping, got {type(block).__name__}"
        )
    errors = collect_release_checklist_errors(config)
    if errors:
        return _off_checklist(
            f"invalid configuration, {len(errors)} error(s): {errors[0]}"
        )
    mode = block.get("mode", "off")
    if mode is False:
        mode = "off"
    if mode not in VALID_MODES:
        return _off_checklist(f"invalid mode {mode!r}")
    return {
        "mode": mode,
        "items": [_resolve_item(item) for item in block.get("items") or []],
    }


def _resolve_item(item: dict) -> dict:
    """Fill the item defaults; keep optional keys only when present."""
    resolved = {
        "id": item["id"],
        "task": item["task"],
        "verification": item["verification"],
        "check": item.get("check", "agent"),
        "phase": item.get("phase", "precondition"),
        "required": item.get("required", True),
    }
    if "script" in item:
        resolved["script"] = item["script"]
    if "applies-when" in item:
        resolved["applies-when"] = item["applies-when"]
    return resolved


# --- Renderer --------------------------------------------------------------

_ITEM_TABLE_HEAD = (
    "| id | phase | check | required | task | verification | applies-when |",
    "|----|-------|-------|----------|------|--------------|--------------|",
)


def render_release_checklist_block(resolved: dict) -> str:
    """Render the checklist prose block; ``""`` when the mode is ``off``.

    The output is inserted into ``release.md`` before the unknown-placeholder
    check, so it must never contain the placeholder opener ``{{``. Free-text
    item fields that would introduce one are rejected by
    :func:`collect_release_checklist_errors`; the renderer only documents the
    invariant.
    """
    mode = resolved.get("mode", "off")
    if mode == "off":
        return ""
    items = resolved.get("items") or []
    lines: list[str] = [
        f"### Release checklist (mode: `{mode}`)",
        "",
        "**Step 0 stays hard in every mode.** Run the pre-release gates first. "
        "A non-zero gate exit stops the release with `STATUS: failed` — in "
        "`off`, `advisory` and `strict`. The checklist never softens the gates.",
        "",
    ]
    lines.extend(_render_mode_semantics(mode))
    lines.extend(["", "Item classes:"])
    lines.append(
        "- `precondition` — evaluated before any mutation: `tests-green`, "
        "`dod-met`, `changelog-updated`, `readme-current`."
    )
    lines.append(
        "- `step` — confirmed only after execution: `version-bumped`, "
        "`build-created`, `git-tag-push`."
    )
    if items:
        lines.extend(["", "Project items:", _ITEM_TABLE_HEAD[0], _ITEM_TABLE_HEAD[1]])
        lines.extend(_render_item_row(item) for item in items)
    else:
        lines.extend(["", "Project items: none."])
    lines.extend(["", *_STATIC_BLOCK_SECTIONS])
    return "\n".join(lines)


def _render_mode_semantics(mode: str) -> list[str]:
    lines = [
        "",
        "Mode semantics:",
        "- `advisory`: every item is evaluated and reported. A non-pass "
        "precondition needs an explicit approval before any mutation; a "
        "failing step leaves the run `partial` and needs a fresh approval "
        "before tag/push.",
    ]
    if mode == "strict":
        lines.append(
            "- `strict`: every required item must be `pass`. A failing "
            "required precondition means `STATUS: failed` with no mutation, "
            "no tag and no push; a failing required step means no tag/push."
        )
        lines.append("")
        lines.append(
            "Boundary: `strict` is a Prompt-/Konventions-Boundary (convention "
            "boundary), not a hook and not a security guarantee."
        )
    else:
        lines.append("")
        lines.append(
            "Boundary: `advisory` is a Prompt-Konvention (prompt convention), "
            "not a hook and not a security guarantee."
        )
    return lines


def _cell(value: object) -> str:
    """Escape a value for a single markdown table cell."""
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _render_item_row(item: dict) -> str:
    check = item.get("check", "agent")
    verification = _cell(item.get("verification", ""))
    if check == "script" and item.get("script"):
        verification = f"{verification} (`{_cell(item['script'])}`)"
    return (
        f"| {_cell(item.get('id', ''))} "
        f"| {_cell(item.get('phase', 'precondition'))} "
        f"| {_cell(check)} "
        f"| {'true' if item.get('required', True) else 'false'} "
        f"| {_cell(item.get('task', ''))} "
        f"| {verification} "
        f"| {_cell(item.get('applies-when', '-'))} |"
    )


_STATIC_BLOCK_SECTIONS: tuple[str, ...] = (
    "Script rules (`check: script`):",
    "- Exit 0 = pass; any non-zero exit = fail.",
    "- A missing or non-executable script is a fail, never `n/a`.",
    "- Scripts must be side-effect free: they also run under "
    "`MODE: check-only` and must not mutate files, tags or remotes.",
    "",
    "Procedure (do not reorder):",
    "1. Step 0: run the release gates (hard in every mode).",
    "2. Evaluate preconditions — default preconditions first, then the "
    "project preconditions. This happens before any mutation.",
    "3. Decide: in `strict` a failing required precondition means "
    "`STATUS: failed` and the run ends. Any non-pass item that needs "
    "approval stops the run before the first mutation with `STATUS: partial` "
    "and an `APPROVAL_REQUEST`, unless the task already contains a matching "
    "`APPROVED:` line.",
    "4. Mutations and steps in this order: version bump (confirm "
    "`version-bumped`), CHANGELOG edit, build (confirm `build-created`), "
    "project steps, then tag and push through the `git` agent (confirm "
    "`git-tag-push`). A failing step: `strict` with a required item means "
    "`STATUS: failed`; `advisory` means `STATUS: partial`.",
    "5. Emit the result table and decide.",
    "",
    "Approval protocol:",
    "- Stop before the first mutation and return `STATUS: partial` with "
    "`APPROVAL_REQUEST: release <version>; actions=bump,changelog,build,tag,push; "
    "accept=<ids of the non-pass items>`.",
    "- The orchestrator asks the user and re-dispatches with "
    "`APPROVED: <action/ids>` in the task. The approval covers only the named "
    "action and ids; another non-pass item or a failing step needs a new "
    "`APPROVAL_REQUEST` (for example "
    "`APPROVAL_REQUEST: continue-after-step-fail <ids>` before tag/push).",
    "- On a re-dispatch, evaluate the preconditions again; if the result "
    "differs from the approved ids, the approval gate applies again.",
    "",
    "`n/a` rules:",
    "- In `advisory`, `n/a` needs a concrete single line `reason`; an empty "
    "reason scores the item as `fail`.",
    "- In `strict`, `n/a` is only allowed when the item has `applies-when` "
    "and the condition does not apply, or when the item is `dod-met` or "
    "`readme-current`. Those two need a single line `reason` that is not "
    "empty.",
    "- Every other default item (including `tests-green` and "
    "`changelog-updated`) is never `n/a` in `strict`.",
    "",
    "Result contract (prepend these lines to the return, before `STATUS`):",
    "```",
    "CHECKLIST_MODE: off|advisory|strict",
    "CHECKLIST:",
    "| id | phase | check | result | reason (1 line) |",
    "|----|-------|-------|--------|-----------------|",
    "| tests-green | precondition | script | pass | exit 0 |",
    "| version-bumped | step | agent | n/a (nicht ausgeführt) | dry-check |",
    "CHECKLIST_SUMMARY: pass=<n> fail=<n> n/a=<n> not_run=<n> required_failed=<n>",
    "APPROVAL_REQUEST: <action/ids>  # only for STATUS: partial because of an "
    "approval, otherwise omit",
    "```",
    "",
    "`result` is one of `pass`, `fail`, `n/a` or `n/a (nicht ausgeführt)`. "
    "`reason` is mandatory for `n/a` (single line, not empty); a missing "
    "reason scores as `fail`. `not_run` counts `n/a (nicht ausgeführt)` and "
    "never contributes to `required_failed`.",
    "`STATUS` mapping: in `strict`, `required_failed > 0` means `failed`; in "
    "`advisory`, `fail > 0` or an open approval means `partial` (with "
    "`APPROVAL_REQUEST`), otherwise `done`. A gate error in Step 0 means "
    "`STATUS: failed` in every mode.",
    "",
    "Dry-check (`MODE: check-only`):",
    "- Allowed: Step 0, reading or running every precondition (script items "
    "must be side-effect free), the result table.",
    "- Every `phase: step` item (default `version-bumped`, `build-created`, "
    "`git-tag-push` and project steps) is `n/a (nicht ausgeführt)` and has no "
    "effect on `strict`.",
    "- Forbidden: tag, push, build, version bump, CHANGELOG or file edits, "
    "commit, `gh release`.",
    "- A dry-check never emits `APPROVAL_REQUEST` (no mutation). Result: "
    "`done` (release-ready), `partial` (`advisory` with a failing "
    "precondition) or `failed` (gate error or `strict` with a failing "
    "required precondition).",
    "",
    "R-S4: never change the checklist mode yourself in any mode; only the "
    "project configuration changes it.",
)


# --- Variables -------------------------------------------------------------


def build_release_checklist_variables(config: dict) -> dict[str, str]:
    """Build the three ``RELEASE_CHECKLIST_*`` template variables."""
    resolved = resolve_release_checklist(config)
    mode = resolved["mode"]
    return {
        "RELEASE_CHECKLIST_MODE": mode,
        "RELEASE_CHECKLIST_ENABLED": "true" if mode != "off" else "false",
        "RELEASE_CHECKLIST_BLOCK": render_release_checklist_block(resolved),
    }
