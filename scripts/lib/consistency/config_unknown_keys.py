"""WARN-ONLY detection of unknown top-level project-config keys (#1141).

A typo such as ``dod-presett`` is silently accepted because the project config
schema keeps top-level ``additionalProperties: true``. This check reads the
schema's ``properties`` (the authoritative key list), supplements it with the
Admin UI's writable-section whitelist and a small legacy set, and emits one
``config.unknown-key`` WARNING per unknown top-level key with a ``did you
mean`` suggestion via ``difflib.get_close_matches``.

Never fatal: findings are ``Severity.WARNING`` only, so callers keep rc 0.
Nested objects are deliberately out of scope (spec Q1).
"""
from __future__ import annotations

import ast
import difflib
import json
from pathlib import Path

from ..io import load_yaml_file
from .report import Finding, Severity

SCHEMA_REL = "config/project-config.schema.json"
ADMIN_SERVER_REL = "scripts/admin-server.py"
CONFIG_REL = ".meta-config/project.yaml"
CHECK_ID = "config.unknown-key"

# Legitimate top-level keys that exist in shipped configs but are not (yet)
# listed in the schema properties or the Admin UI whitelist. Kept here so the
# self-hosted config does not produce false positives while the schema stays
# unchanged for this warn-only fix (AC-03 / Q2). Schema-derived keys remain the
# primary source (ADR-1141-2) — this is only a supplementary legacy set.
_LEGACY_KNOWN_KEYS = frozenset({
    "mcp",
    "provider-deactivation",
    "se-export",
    "systems-engineering",
    "test-repo",
})


def check_unknown_config_keys(
    agent_meta_root: Path,
    config_path: Path | None = None,
) -> list[Finding]:
    """Return WARNING findings for unknown top-level keys in the project config.

    Args:
        agent_meta_root: Absolute path to the agent-meta repository root.
        config_path: Project config path. Defaults to
            ``<agent_meta_root>/.meta-config/project.yaml``.

    Returns:
        One ``config.unknown-key`` WARNING per unknown top-level key, sorted by
        key. Empty when the config is missing, unreadable, or has no unknowns.
    """
    path = config_path if config_path is not None else agent_meta_root / CONFIG_REL
    if not path.exists():
        return []
    config = load_yaml_file(path, on_error="default", default={})
    if not isinstance(config, dict) or not config:
        return []

    known = _known_top_level_keys(agent_meta_root)
    unknown = sorted(set(config) - known)
    if not unknown:
        return []

    candidates = sorted(known)
    findings: list[Finding] = []
    for key in unknown:
        suggestions = difflib.get_close_matches(key, candidates, n=1, cutoff=0.6)
        if suggestions:
            message = (
                f"{CHECK_ID}: '{key}' is not a known top-level config key "
                f"— did you mean '{suggestions[0]}'?"
            )
        else:
            message = f"{CHECK_ID}: '{key}' is not a known top-level config key."
        findings.append(Finding(Severity.WARNING, CHECK_ID, CONFIG_REL, message))
    return findings


def _known_top_level_keys(agent_meta_root: Path) -> set[str]:
    """Build the authoritative + supplementary set of known top-level keys."""
    known: set[str] = set(_LEGACY_KNOWN_KEYS)
    known.update(_schema_property_keys(agent_meta_root))
    known.update(_admin_writable_sections(agent_meta_root))
    return known


def _schema_property_keys(agent_meta_root: Path) -> set[str]:
    """:return: top-level ``properties`` keys from the project-config schema."""
    schema_path = agent_meta_root / SCHEMA_REL
    try:
        with schema_path.open("r", encoding="utf-8") as handle:
            schema = json.load(handle)
    except (OSError, ValueError):
        return set()
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return set()
    return {key for key in properties if isinstance(key, str)}


def _admin_writable_sections(agent_meta_root: Path) -> set[str]:
    """Statically read ``PROJECT_WRITABLE_SECTIONS`` from the Admin UI source.

    Parsed with ``ast`` instead of importing ``scripts/admin-server.py``: the
    hyphenated filename is not importable by module name, and importing the
    server would drag in its whole dependency tree. The whitelist remains the
    single source of truth — it is read in place, never duplicated here.
    """
    source = agent_meta_root / ADMIN_SERVER_REL
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return set()
    for node in ast.walk(tree):
        targets: list[ast.expr]
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        if not any(
            isinstance(target, ast.Name)
            and target.id == "PROJECT_WRITABLE_SECTIONS"
            for target in targets
        ):
            continue
        value = node.value
        if (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "frozenset"
            and value.args
        ):
            value = value.args[0]
        if isinstance(value, (ast.Set, ast.List, ast.Tuple)):
            return {
                element.value
                for element in value.elts
                if isinstance(element, ast.Constant)
                and isinstance(element.value, str)
            }
    return set()
