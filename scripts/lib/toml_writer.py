"""Minimal stdlib TOML serializer (writer only).

Python ships tomllib (read-only) but no TOML writer, and agent-meta is
stdlib-only apart from PyYAML — so the writer side of the codex-toml agent
mechanism lives here. The module is generic: no agent/provider specifics.

Supported subset (round-trip safe):

- dict -> TOML document. Nested dicts become dotted ``[table.sub]`` sections;
  a homogeneous list of dicts becomes ``[[array-of-tables]]`` blocks.
- Scalar values: str, int, float, bool (bool is checked before int, since
  bool subclasses int in Python).
- Lists of scalars / lists of lists as inline arrays. Mixed lists (scalars
  and dicts together) fall back to inline arrays of inline tables.
- Strings: single-line basic strings, or multi-line basic strings
  (triple double-quote form) when the value contains a newline. Control
  characters are escaped; backslash and double-quote escapes follow the
  TOML basic-string rules. For multi-line strings the mandatory leading
  newline after the opening delimiter is always emitted so the trim rule
  never eats content.
- Keys: bare for ``[A-Za-z0-9_-]+``, otherwise quoted with escapes.

Determinism: dict insertion order is preserved; within a table every scalar
key/value pair is emitted before any ``[sub-table]``/``[[array-of-table]]``
header (a TOML requirement — anything after a header belongs to that
sub-table); output lines never carry trailing whitespace; ``dumps({})``
returns ``""`` and ``dumps`` never appends a trailing newline.

Round-trip guarantee: for every value composed exclusively of the supported
types, ``tomllib.loads(dumps(value)) == value``. Unsupported types
(datetime, date, time, bytes, None, ...) raise TypeError instead of
silently producing lossy output.
"""
from __future__ import annotations

import re

__all__ = ["dumps", "format_string", "format_multiline_string", "format_value"]

_BARE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")

# Short escapes for control characters (TOML basic-string escape set).
_CHAR_ESCAPES = {
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
    '"': '\\"',
    "\\": "\\\\",
}

# Control characters (plus DEL) that have no short escape -> \uXXXX.
_CTRL_START, _CTRL_END = 0x00, 0x1F
_DEL = 0x7F


def _escape_control_char(ch: str) -> str:
    """Return the TOML escape sequence for a single control character."""
    if ch in _CHAR_ESCAPES:
        return _CHAR_ESCAPES[ch]
    return f"\\u{ord(ch):04X}"


def _is_control(ch: str) -> bool:
    """True for characters that must never appear literally in a string."""
    return _CTRL_START <= ord(ch) <= _CTRL_END or ord(ch) == _DEL


def _format_string_single(value: str) -> str:
    """Format as a single-line basic string (newlines become \\n escapes)."""
    out = []
    for ch in value:
        if ch in _CHAR_ESCAPES:
            out.append(_CHAR_ESCAPES[ch])
        elif _is_control(ch):
            out.append(_escape_control_char(ch))
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _escape_multiline_body(value: str) -> str:
    """Escape a value for embedding between triple-double-quote delimiters.

    Backslashes are doubled first, control characters escaped (a literal
    newline stays literal — it is what makes the string multi-line), and
    every triple-quote run is broken up by escaping one quote so no three
    consecutive unescaped quotes remain anywhere (including where the body
    meets the closing delimiter).
    """
    out = []
    for ch in value.replace("\\", "\\\\"):
        if ch == "\n":
            out.append(ch)  # the multi-line carrier — stays literal
        elif _is_control(ch):
            out.append(_escape_control_char(ch))
        else:
            out.append(ch)
    escaped = "".join(out)
    # Break every >=3-quote run: '"""' -> '""\"'. Applying the replace
    # repeatedly is unnecessary — each replacement ends in an escaped quote,
    # so the scan never re-matches across a replacement boundary.
    return escaped.replace('"""', '""\\"')


def format_multiline_string(value: str) -> str:
    """Format as a multi-line basic string (triple double-quote form).

    A newline is always emitted right after the opening delimiter: TOML
    trims exactly one newline there, so the parsed value equals ``value``
    byte-for-byte. Round-trips exactly for any str input.
    """
    return '"""\n' + _escape_multiline_body(value) + '"""'


def format_string(value: str) -> str:
    """Format a string, choosing the deterministic string form.

    Values containing a newline are emitted as multi-line basic strings;
    everything else as a single-line basic string.
    """
    if "\n" in value:
        return format_multiline_string(value)
    return _format_string_single(value)


def _format_inline_table(value: dict) -> str:
    """Format a dict as a single-line inline table (no multiline strings)."""
    if not value:
        return "{}"
    pairs = [
        f"{format_key(str(k))} = {_format_inline_value(v)}"
        for k, v in value.items()
    ]
    return "{" + ", ".join(pairs) + "}"


def _format_inline_value(value) -> str:
    """Format any supported value in inline (single-line) form."""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, str):
        return _format_string_single(value)
    if isinstance(value, list):
        return "[" + ", ".join(_format_inline_value(v) for v in value) + "]"
    if isinstance(value, dict):
        return _format_inline_table(value)
    raise TypeError(f"unsupported TOML value type: {type(value).__name__}")


def format_value(value) -> str:
    """Format a value in the form used for ``key = value`` lines.

    Strings use the deterministic single/multi-line choice of
    :func:`format_string` (safe on their own line); every other supported
    type renders inline. Raises TypeError for unsupported types.
    """
    if isinstance(value, str):
        return format_string(value)
    return _format_inline_value(value)


def format_key(key: str) -> str:
    """Format a TOML key: bare for [A-Za-z0-9_-]+, quoted otherwise."""
    if _BARE_KEY_RE.match(key):
        return key
    return _format_string_single(key)


def _is_array_of_tables(value) -> bool:
    """True for a non-empty list whose items are all dicts."""
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, dict) for item in value
    )


def _emit_table(data: dict, path: tuple, lines: list) -> None:
    """Emit one table context: scalars first, then sub-tables/AoTs in order."""
    for key, value in data.items():
        if isinstance(value, dict) or _is_array_of_tables(value):
            continue
        lines.append(f"{format_key(str(key))} = {format_value(value)}")
    for key, value in data.items():
        sub_path = path + (str(key),)
        header = ".".join(format_key(part) for part in sub_path)
        if isinstance(value, dict):
            # An empty dict still gets its header so the key survives the
            # round-trip; implicitly-created parent tables need no header.
            lines.append(f"[{header}]")
            _emit_table(value, sub_path, lines)
        elif _is_array_of_tables(value):
            for item in value:
                lines.append(f"[[{header}]]")
                _emit_table(item, sub_path, lines)


def dumps(data: dict) -> str:
    """Serialize a dict to a TOML document string (see module docstring).

    Raises TypeError if ``data`` is not a dict or contains unsupported
    value types.
    """
    if not isinstance(data, dict):
        raise TypeError(f"dumps() expects a dict, got {type(data).__name__}")
    lines: list = []
    _emit_table(data, (), lines)
    return "\n".join(lines)
