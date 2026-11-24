"""Single implementation of the ``<id>:managed-begin/-end`` block replacer."""
from __future__ import annotations

import hashlib
import re


MANAGED_BEGIN = "<!-- agent-meta:managed-begin -->"
MANAGED_END = "<!-- agent-meta:managed-end -->"


class ManagedBlockError(ValueError):
    """Broken managed-block markers (begin without end, stray end marker)."""


def _markers(marker_id: str):
    ident = re.escape(marker_id)
    # optional ``v=<hash>`` (drift protection); legacy markers have none
    begin = re.compile(r"<!--\s*" + ident + r":managed-begin(?:\s+v=[0-9a-f]+)?\s*-->")
    end = re.compile(r"<!--\s*" + ident + r":managed-end\s*-->")
    return begin, end


# Compiled agent-meta block pattern (begin..end, markers included) for sites
# that search/split/count blocks themselves and tolerate broken markers.
MANAGED_BLOCK_RE = re.compile(
    _markers("agent-meta")[0].pattern + r".*?" + _markers("agent-meta")[1].pattern,
    re.DOTALL,
)


def body_hash(text: str, marker_id: str = "agent-meta") -> str:
    """Short hash over the body of the first block (between the marker lines)."""
    begin, end = _markers(marker_id)
    b = begin.search(text)
    e = end.search(text, b.end()) if b else None
    if b is None or e is None:
        raise ManagedBlockError(f"no complete {marker_id} managed block")
    return hashlib.sha256(text[b.end():e.start()].encode("utf-8")).hexdigest()[:12]


def stamp_block(block: str, marker_id: str = "agent-meta") -> str:
    """Return *block* with ``v=<body hash>`` in its begin marker."""
    begin, _ = _markers(marker_id)
    h = body_hash(block, marker_id)
    return begin.sub(f"<!-- {marker_id}:managed-begin v={h} -->", block, count=1)


def has_drift(text: str, marker_id: str = "agent-meta") -> bool:
    """True when the first block carries ``v=`` and its body no longer matches.

    Legacy blocks without ``v=`` never count as drift. Raises
    ``ManagedBlockError`` for an incomplete block.
    """
    begin, _ = _markers(marker_id)
    b = begin.search(text)
    if b is None:
        return False
    m = re.search(r"v=([0-9a-f]+)", b.group(0))
    return bool(m) and m.group(1) != body_hash(text, marker_id)


def has_block(text: str, marker_id: str = "agent-meta") -> bool:
    return _markers(marker_id)[0].search(text) is not None


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
