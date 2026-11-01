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
