"""Consistency check: provider config vs. ``hook_known_tool_name`` allow-list (#1323).

The hand-maintained closed allow-list in ``hooks/1-generic/lib/hook_common.sh``
stays fail-closed. This module only *reports* deltas between the tool names
declared in the framework provider config and the case literals of
``hook_known_tool_name``. It is a config<->allow-list comparison (no live
harness feed), INFO-only, read-only and fail-soft: a missing/unreadable source
or config yields no findings, never an exception and never an ERROR.
"""

from __future__ import annotations

import re
from pathlib import Path

from ..io import load_yaml_file
from ..providers import load_provider_capabilities
from .report import Finding, Severity

HOOK_LIB_REL = "hooks/1-generic/lib/hook_common.sh"
CHECK_ID = "hooks.unknown-tool-name"

# A case arm whose alternatives are all plain literals, e.g.
#   Agent|Bash|...|LS) return 0 ;;
# Wildcards (the mcp__?*__?* arm) and comment lines do not match.
_CASE_ARM = re.compile(
    r"^\s*([A-Za-z][A-Za-z0-9_]*(?:\|[A-Za-z][A-Za-z0-9_]*)*)\)"
    r"\s*return\s+0\s*;;"
)
_LITERAL = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")

_CAPABILITY_TOOL_KEYS = ("native_agent_tools", "worker_control_tools")
# provider-tools.yaml keys that are not provider tool-name lists.
_EXCLUDED_TOOLS_KEYS = frozenset({
    "opencode_deny_critical",
    "opencode_primary_edit_allow",
    "terminal_tool",
})


def parse_known_tool_names(source_text: str) -> frozenset[str]:
    """Return the case literals of ``hook_known_tool_name`` from ``source_text``.

    Only the body of the function is inspected. The MCP wildcard arm and
    comment-only mentions (e.g. ``EnterWorktree``) are not case literals and
    are therefore excluded. Original spelling is preserved; case-insensitive
    comparison happens in :func:`check_unknown_tool_names`.
    """
    if not isinstance(source_text, str) or not source_text:
        return frozenset()
    start = source_text.find("hook_known_tool_name()")
    if start < 0:
        return frozenset()
    # The closing ``esac`` of the case block is indented in the shipped hook,
    # so a literal "\nesac" search would miss it and extend the body to EOF,
    # folding in any later ``return 0 ;;`` arm outside the function.
    esac_match = re.search(r"^\s*esac\b", source_text[start:], re.M)
    end = start + esac_match.start() if esac_match else len(source_text)
    body = source_text[start:end]
    names: set[str] = set()
    for line in body.splitlines():
        match = _CASE_ARM.match(line)
        if match:
            names.update(match.group(1).split("|"))
    return frozenset(names)


def _add_tool_name(names: dict[str, str], name: object) -> None:
    """Add ``name`` casefolded -> original spelling, skipping meta patterns."""
    if not isinstance(name, str) or not name or name.startswith("mcp__"):
        return
    if not _LITERAL.fullmatch(name):
        return
    names.setdefault(name.casefold(), name)


def _load_expected_tool_name_map(agent_meta_root: Path) -> dict[str, str]:
    """Build ``casefold -> original spelling`` from the two config sources.

    Source 1: ``config/provider-capabilities.yaml`` (``native_agent_tools`` and
    ``worker_control_tools`` of every provider block). Source 2:
    ``config/provider-tools.yaml`` (provider blocks only; ``*-silent``,
    ``opencode_deny_critical``, ``opencode_primary_edit_allow`` and
    ``terminal_tool`` are excluded).
    """
    root = Path(agent_meta_root)
    names: dict[str, str] = {}

    caps = load_provider_capabilities(root)
    for provider in (caps or {}).values():
        if not isinstance(provider, dict):
            continue
        for key in _CAPABILITY_TOOL_KEYS:
            values = provider.get(key) or []
            if not isinstance(values, list):
                continue
            for name in values:
                _add_tool_name(names, name)

    tools = load_yaml_file(root / "config" / "provider-tools.yaml",
                           on_error="default", default={})
    for key, values in (tools or {}).items():
        if key in _EXCLUDED_TOOLS_KEYS or str(key).endswith("-silent"):
            continue
        if not isinstance(values, list):
            continue
        for name in values:
            _add_tool_name(names, name)
    return names


def load_expected_tool_names(agent_meta_root: Path) -> frozenset[str]:
    """Return the casefold-normalised config-derived expected tool-name set."""
    return frozenset(_load_expected_tool_name_map(agent_meta_root))


def check_unknown_tool_names(  # noqa: ARG001 - signature parity with sibling checks
    project_root: Path, agent_meta_root: Path, config: dict, provider_config: dict
) -> list[Finding]:
    """Report config<->allow-list deltas as INFO findings (never blocking).

    ``project_root``, ``config`` and ``provider_config`` are accepted for
    signature parity with the other consistency checks; the data source is
    exclusively the framework config and the hook source under
    ``agent_meta_root``. A truly unknown tool still fails closed in the guards.
    """
    root = Path(agent_meta_root)
    try:
        source = (root / HOOK_LIB_REL).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return []
    known = {name.casefold(): name for name in parse_known_tool_names(source)}
    expected = _load_expected_tool_name_map(root)
    # Fail-soft: no allow-list or no config => nothing to compare.
    if not known or not expected:
        return []

    findings: list[Finding] = []
    for folded in sorted(set(expected) | set(known)):
        in_expected = folded in expected and folded not in known
        in_known = folded in known and folded not in expected
        if not (in_expected or in_known):
            continue
        if in_expected:
            name = expected[folded]
            message = (
                f"Tool name '{name}' is declared in the provider capability config "
                "but not listed in hook_known_tool_name (config-only)."
            )
            suggestion = (
                f"Consider adding '{name}' to hook_known_tool_name in "
                f"{HOOK_LIB_REL} if the harness can emit it; the allow-list "
                "stays fail-closed."
            )
        else:
            name = known[folded]
            message = (
                f"Tool name '{name}' is listed in hook_known_tool_name but not "
                "declared in the provider capability config (allow-list-only)."
            )
            suggestion = (
                f"Document '{name}' in config/provider-tools.yaml or "
                "config/provider-capabilities.yaml, or confirm it is "
                "intentionally allow-list-only in hook_known_tool_name."
            )
        findings.append(Finding(Severity.INFO, CHECK_ID, HOOK_LIB_REL, message, suggestion))
    return findings
