"""Shared CHANGELOG section extraction for the docs guardrail tests.

The release workflow keeps ``## [Unreleased]`` as an (usually empty) heading and
adds the fresh content below the new version heading. Tests that pin "the
current changelog block" must therefore cover the ``[Unreleased]`` section plus
the immediately following versioned release block, otherwise every release
breaks them although the content is still present.

``latest_changelog_section`` returns both contiguous sections and stays correct
when ``[Unreleased]`` genuinely carries bullets (then it is included as well).
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
