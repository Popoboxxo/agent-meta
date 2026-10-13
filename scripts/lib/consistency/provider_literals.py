"""Provider-literal check for generic templates (IC-30 / IC-32).

Generic templates (``agents/1-generic/*.md``, not recursive; ``rules/1-generic``
joins the scope with Q30) must stay provider-agnostic. The literal set is
derived from ``config/ai-providers.yaml`` (provider keys, ``provider_root_dirs``,
``context_file``); nothing is hardcoded. Matching is case-sensitive with word
boundaries (a literal inside a longer word is not a hit).

Tolerated: files matching ``provider_literal_allow``
(config/active-set-references.yaml) and example blocks. An example block starts
at a line beginning with ``> **Example (provider-specific):**`` (the marker is
recognized only at column 0, without leading spaces) and ends at the first line
that does not start with ``>`` (after optional leading whitespace) - a blank
line therefore ends the block.
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path

from .report import Finding, Severity
from ..io import load_yaml_file

CHECK_ID = "templates.provider-literal"
EXAMPLE_MARKER = "> **Example (provider-specific):**"
_SCAN_GLOBS = ("agents/1-generic/*.md",)


def _literals(root: Path) -> list:
    data = load_yaml_file(root / "config" / "ai-providers.yaml") or {}
    providers = data.get("providers") or {}
    found = set()
    for name, cfg in providers.items():
        found.add(str(name))
        cfg = cfg or {}
        for d in cfg.get("provider_root_dirs") or []:
            found.add(str(d))
        ctx = cfg.get("context_file")
        if isinstance(ctx, str) and ctx:
            found.add(ctx)
    found.discard("")
    return sorted(found, key=len, reverse=True)


def _compile(literal: str) -> re.Pattern:
    # Boundaries only on word-character edges, so a short name does not match
    # inside a longer word while directory literals (".x/") match as prefixes.
    head = r"(?<![\w.])" if literal[0].isalnum() else r"(?<!\w)"
    tail = r"(?!\w)" if literal[-1].isalnum() else ""
    return re.compile(head + re.escape(literal) + tail)


def _allowed(rel: str, patterns: list) -> bool:
    return any(fnmatch.fnmatch(rel, p) for p in patterns)


def check_provider_literal(agent_meta_root: Path) -> list:
    root = Path(agent_meta_root)
    refs = load_yaml_file(root / "config" / "active-set-references.yaml") or {}
    allow = [str(p) for p in (refs.get("provider_literal_allow") or [])]
    literals = _literals(root)
    if not literals:
        return []
    compiled = [(lit, _compile(lit)) for lit in literals]
    findings = []
    for pattern in _SCAN_GLOBS:
        for path in sorted(root.glob(pattern)):
            rel = path.relative_to(root).as_posix()
            if _allowed(rel, allow):
                continue
            in_example = False
            for lineno, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), 1):
                if line.startswith(EXAMPLE_MARKER):
                    in_example = True
                elif not line.lstrip().startswith(">"):
                    in_example = False
                if in_example:
                    continue
                hits = [lit for lit, rx in compiled if rx.search(line)]
                if hits:
                    findings.append(Finding(
                        Severity.WARNING, CHECK_ID, rel,
                        f"line {lineno}: provider literal(s) {', '.join(hits)}"
                        " in generic template",
                        "Use a placeholder or move into a "
                        f"'{EXAMPLE_MARKER}' block"))
    return findings
