"""Single implementation of the ``<id>:managed-begin/-end`` block replacer."""
from __future__ import annotations

import re


MANAGED_BEGIN = "<!-- agent-meta:managed-begin -->"
MANAGED_END = "<!-- agent-meta:managed-end -->"


class ManagedBlockError(ValueError):
    """Broken managed-block markers (begin without end, stray end marker)."""


def _markers(marker_id: str):
    ident = re.escape(marker_id)
    begin = re.compile(r"<!--\s*" + ident + r":managed-begin\s*-->")
    end = re.compile(r"<!--\s*" + ident + r":managed-end\s*-->")
    return begin, end


# Compiled agent-meta block pattern (begin..end, markers included) for sites
# that search/split/count blocks themselves and tolerate broken markers.
MANAGED_BLOCK_RE = re.compile(
    _markers("agent-meta")[0].pattern + r".*?" + _markers("agent-meta")[1].pattern,
    re.DOTALL,
)


def replace_line_block(text: str, begin: str, end: str, body: str):
    """Replace the first line-anchored *begin*..*end* block (e.g. ``# ...`` YAML
    comment form) with *body*, verbatim. Returns None when no block exists."""
    pat = re.compile(
        rf"^{re.escape(begin)}.*?^{re.escape(end)}", re.MULTILINE | re.DOTALL
    )
    if not pat.search(text):
        return None
    return pat.sub(lambda _m: body, text, count=1)


def render_block(marker_id: str, body: str) -> str:
    """Wrap *body* into a managed block (canonical marker spelling)."""
    return (
        f"<!-- {marker_id}:managed-begin -->\n{body}\n"
        f"<!-- {marker_id}:managed-end -->"
    )


def replace_block(text: str, body: str, marker_id: str = "agent-meta") -> str:
    """Replace the first managed block (markers included) with *body*, verbatim.

    *body* is a complete block (e.g. from ``render_block``). Without any block
    the block is prepended (legacy behaviour, changes in #1269). Raises
    ``ManagedBlockError`` for a begin marker without end or an end without
    begin; *text* is never modified in place.
    """
    begin, end = _markers(marker_id)
    b = begin.search(text)
    if b is None:
        if end.search(text):
            raise ManagedBlockError(f"{marker_id}:managed-end without managed-begin")
        return body + "\n\n" + text
    e = end.search(text, b.end())
    if e is None:
        raise ManagedBlockError(f"{marker_id}:managed-begin without managed-end")
    if len(end.findall(text)) > len(begin.findall(text)):
        raise ManagedBlockError(f"duplicate {marker_id}:managed-end marker")
    return text[:b.start()] + body + text[e.end():]
