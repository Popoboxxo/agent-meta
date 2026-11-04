"""Comment-preserving top-level YAML patcher (issues #1074, #1092).

Rewrites only the top-level segments that actually changed; every other byte
of the document -- comments, blank lines, key order, inline comments, CRLF
line endings, a missing final newline -- stays untouched.

This is deliberately *not* a YAML parser. The document is split on top-level
key lines (column 0) into segments; an unchanged segment is copied verbatim,
a changed one is re-rendered through the caller's ``dump_fn``. Leading
comment/blank lines belong to the key that follows them, so a changed
section keeps its explanatory comment.

Return contract: ``None`` means "cannot patch safely -- the caller must fall
back to a full dump". The function never raises for malformed or ambiguous
input; it refuses multi-document streams, anchors/aliases, tab indentation,
non-mapping documents, duplicate top-level keys and any result that does not
round-trip back to ``new_doc``.
"""
from __future__ import annotations

import re
from typing import Callable, Optional

import yaml

# A top-level document marker means the caller should use the full-dump path.
_DOC_MARKER_RE = re.compile(r"^(?:---|\.\.\.)[ \t]*$")
# A top-level key line: column 0, plain or quoted key, followed by ":".
_KEY_RE = re.compile(
    r"""^(?P<key>"[^"]+"|'[^']+'|[A-Za-z0-9_][^\s#:]*):(?:[ \t]|$)"""
)
_LEADING_TAB_RE = re.compile(r"^[ \t]*\t")


def _is_leading_noise(line: str) -> bool:
    """True for a blank line or a column-0 comment line."""
    stripped = line.rstrip("\r\n")
    if stripped.strip() == "":
        return True
    return stripped.startswith("#")


def _unquote_key(raw_key: str) -> str:
    if len(raw_key) >= 2 and raw_key[0] == raw_key[-1] and raw_key[0] in "\"'":
        try:
            loaded = yaml.safe_load(raw_key)
        except yaml.YAMLError:
            return raw_key
        return loaded if isinstance(loaded, str) else raw_key
    return raw_key


def _split(text: str) -> tuple[str, list[tuple[str, int, list[str]]]]:
    """Split ``text`` into a prefix plus ``(key, leading_count, lines)``.

    ``lines`` starts with the leading comment/blank lines (``leading_count``)
    followed by the key line and its body.
    """
    prefix: list[str] = []
    segments: list[tuple[str, int, list[str]]] = []
    current: Optional[list[str]] = None

    for line in text.splitlines(keepends=True):
        match = _KEY_RE.match(line.rstrip("\r\n"))
        if match is None:
            if current is None:
                prefix.append(line)
            else:
                current.append(line)
            continue

        container = current if current is not None else prefix
        cut = len(container)
        while cut and _is_leading_noise(container[cut - 1]):
            cut -= 1
        leading = container[cut:]
        del container[cut:]

        current = leading + [line]
        segments.append((_unquote_key(match.group("key")), len(leading), current))

    return "".join(prefix), segments


def _has_anchor_alias_or_multidoc(text: str) -> bool:
    """Refuse anchors/aliases and multi-document streams (event scan)."""
    documents = 0
    try:
        for event in yaml.parse(text):
            if isinstance(event, yaml.events.DocumentStartEvent):
                documents += 1
                if documents > 1:
                    return True
            if isinstance(event, yaml.events.AliasEvent):
                return True
            if getattr(event, "anchor", None) is not None:
                return True
    except yaml.YAMLError:
        return True
    return False


def _render_key(dump_fn: Callable[[dict], str], key: str, value, newline: str) -> Optional[str]:
    rendered = dump_fn({key: value})
    if not isinstance(rendered, str) or not rendered:
        return None
    # Normalise the dumped line endings to the document's own style.
    rendered = rendered.replace("\r\n", "\n")
    if newline == "\r\n":
        rendered = rendered.replace("\n", "\r\n")
    return rendered


def patch_top_level(
    original_text: str,
    new_doc: dict,
    dump_fn: Callable[[dict], str],
    comments: Optional[dict] = None,
) -> Optional[str]:
    """Patch ``original_text`` to represent ``new_doc`` without losing bytes.

    ``dump_fn`` renders one ``{key: value}`` mapping; it is only called for
    new or changed top-level keys. ``comments`` maps a new key to a one-line
    comment inserted above it. Returns ``None`` when a safe patch is not
    possible (see the module docstring).
    """
    if not isinstance(original_text, str) or not isinstance(new_doc, dict):
        return None

    for line in original_text.splitlines():
        if _LEADING_TAB_RE.match(line):
            return None
        if _DOC_MARKER_RE.match(line.rstrip("\r\n")):
            return None

    if _has_anchor_alias_or_multidoc(original_text):
        return None

    try:
        old_doc = yaml.safe_load(original_text)
    except yaml.YAMLError:
        return None
    if not isinstance(old_doc, dict):
        return None

    prefix, segments = _split(original_text)
    keys = [key for key, _, _ in segments]
    if len(set(keys)) != len(keys):
        return None

    newline = "\r\n" if "\r\n" in original_text else "\n"
    chunks: list[str] = [prefix]
    for key, leading_count, lines in segments:
        if key not in new_doc:
            continue  # removed key: drop its segment including leading comments
        leading = "".join(lines[:leading_count])
        block = "".join(lines[leading_count:])
        if key in old_doc and old_doc[key] == new_doc[key]:
            chunks.append(leading)
            chunks.append(block)
            continue
        rendered = _render_key(dump_fn, key, new_doc[key], newline)
        if rendered is None:
            return None
        if not block.endswith("\n"):
            # Preserve a missing final newline on the replaced segment.
            rendered = rendered.rstrip("\r\n")
        elif not rendered.endswith(("\n", "\r")):
            rendered += newline
        chunks.append(leading)
        chunks.append(rendered)

    result = "".join(chunks)
    for key, value in new_doc.items():
        if key in keys:
            continue
        rendered = _render_key(dump_fn, key, value, newline)
        if rendered is None:
            return None
        if result and not result.endswith(("\n", "\r")):
            result += newline
        description = (comments or {}).get(key)
        if description:
            result += f"# {str(description).splitlines()[0]}{newline}"
        if not rendered.endswith(("\n", "\r")):
            rendered += newline
        result += rendered

    try:
        if yaml.safe_load(result) != new_doc:
            return None
    except yaml.YAMLError:
        return None
    return result
