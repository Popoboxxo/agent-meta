"""Shared CHANGELOG section extraction for the docs guardrail tests.

The release workflow keeps ``## [Unreleased]`` as an (usually empty) heading and
adds the fresh content below the new version heading. Tests that pin "the
current changelog block" must therefore cover the ``[Unreleased]`` section plus
the immediately following versioned release block, otherwise every release
breaks them although the content is still present.

``latest_changelog_section`` returns both contiguous sections and stays correct
when ``[Unreleased]`` genuinely carries bullets (then it is included as well).

``release_section`` addresses one release block by version: guardrails for a
feature that already shipped must point at the release that documents it, not at
the moving "current" window.
"""

from __future__ import annotations

import re

_HEADING_RE = re.compile(r"(?m)^## \[[^\]]+\]")


def latest_changelog_section(text: str) -> str:
    """Return the ``[Unreleased]`` block plus the next versioned release block.

    Returns an empty string when the text has no ``## [Unreleased]`` heading (or
    when ``[Unreleased]`` is not the first level-2 bracket heading), so callers
    keep their explicit presence assertions.
    """
    headings = list(_HEADING_RE.finditer(text))
    if not headings or not headings[0].group(0).startswith("## [Unreleased]"):
        return ""
    end = headings[2].start() if len(headings) >= 3 else len(text)
    return text[headings[0].start():end]


def release_section(text: str, version: str) -> str:
    """Return the level-2 block of the release ``version`` (heading plus body).

    Guardrail tests that pin documentation of a *shipped* feature belong to the
    release that shipped it: after the next promotion the entry sits two blocks
    below ``[Unreleased]``, so ``latest_changelog_section`` no longer reaches it.
    Pinning the version keeps the assertion exact (a different release block can
    never satisfy it) and stable across later releases.

    Returns an empty string when ``version`` has no section, so callers keep
    their explicit presence assertions.
    """
    headings = list(_HEADING_RE.finditer(text))
    marker = f"## [{version}]"
    for index, heading in enumerate(headings):
        if heading.group(0) != marker:
            continue
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        return text[heading.start():end]
    return ""
