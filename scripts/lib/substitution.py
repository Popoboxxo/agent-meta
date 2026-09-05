"""Shared escape-safe placeholder-substitution core.

ONE replacement routine for both templating engines (issue #476, plan
Phase 2 item 2.1 of docs/plans/2026-09-05-issue-674-roadmap.md):

* Engine 1 — ``substitute()`` (``scripts/lib/variables.py``): agent/rule/
  command/skill rendering, ``{{UPPERCASE}}`` + ``{{%VAR%}}`` escape syntax.
* Engine 2 — ``TemplateBuilder`` (``scripts/lib/context_templates/builder.py``):
  context-template rendering (loops/conditionals/partials), permissive
  ``{{...}}`` placeholder syntax.

Both delegate their variable-replacement pass to ``substitute_placeholders()``
with engine-specific policies:

  * *pattern*   — which placeholders to match (name captured as group 1).
  * *lookup*    — maps a placeholder name to its replacement text, or
                  ``None`` if the name is unresolved.
  * *keep*      — fallback policy for unresolved names; receives the full
                  match and the captured name and returns the text to leave
                  in place (warn-and-keep, rebuild, or pass-through).

**Escape-safety invariant (issue #674).** Values are injected through a
replacement *function*, so ``re.sub`` inserts the returned string literally:
backslashes, ``$`` group references and regex metacharacters in values are
never interpreted as replacement-template escapes. A raw dynamic string as
the ``re.sub`` replacement argument is forbidden on every rendering path —
route dynamic replacements through this module instead.

This module is stdlib-only and must never import other ``scripts.lib``
modules — it is the neutral bottom of the substitution layer.
"""
from __future__ import annotations

import re
from collections.abc import Callable

Lookup = Callable[[str], "str | None"]
"""Maps a placeholder name to its replacement text, or None if unresolved."""

KeepPolicy = Callable[[str, str], str]
"""Receives (matched_text, name); returns the text to leave in place."""


def replacement_function(
    lookup: Lookup, keep: KeepPolicy | None = None
) -> Callable[[re.Match[str]], str]:
    """Build a re.sub replacement callback from a lookup/keep policy pair.

    The callback resolves the placeholder name (match group 1) via
    ``lookup``; on ``None`` it defers to ``keep(matched, name)`` — or keeps
    the matched text verbatim when no keep policy is given. Because re.sub
    inserts a function's return value literally, the resolved value is
    emitted verbatim (issue #674).

    Args:
        lookup: Resolves a placeholder name to replacement text, or None.
        keep: Fallback for unresolved placeholders. Defaults to keeping the
            matched text unchanged.

    Returns:
        A callback suitable as the re.sub replacement argument.
    """

    def repl(match: re.Match[str]) -> str:
        value = lookup(match.group(1))
        if value is None:
            if keep is None:
                return match.group(0)
            return keep(match.group(0), match.group(1))
        return value

    return repl


def substitute_placeholders(
    text: str,
    pattern: "re.Pattern[str] | str",
    lookup: Lookup,
    keep: KeepPolicy | None = None,
) -> str:
    """Replace regex-matched placeholders in one escape-safe pass.

    Args:
        text: Template text containing placeholders.
        pattern: Placeholder regex; group 1 must capture the placeholder
            name (pass a compiled pattern to avoid recompilation).
        lookup: Resolves a placeholder name to replacement text, or None.
        keep: Fallback for unresolved placeholders — receives the full
            match and the captured name, returns the text to leave in
            place. Defaults to keeping the matched text unchanged.

    Returns:
        Text with all resolved placeholders replaced verbatim.

    Raises:
        Any exception raised by ``lookup``/``keep`` (e.g. a strict-mode
        ``SyncError`` from Engine 1) propagates unchanged.
    """
    return re.sub(pattern, replacement_function(lookup, keep), text)


def constant_lookup(value: object) -> Lookup:
    """Return a lookup resolving every name to ``str(value)``.

    Used by the ``{{#each}}`` loop path (TemplateBuilder): item values are
    rendered as ``str(value)`` regardless of the matched name — including
    ``None`` -> ``"None"`` — matching the pre-unification behavior.

    Args:
        value: The loop item value to render.

    Returns:
        A lookup function emitting ``str(value)`` verbatim for any name.
    """
    rendered = str(value)

    def lookup(name: str) -> str | None:
        return rendered

    return lookup
