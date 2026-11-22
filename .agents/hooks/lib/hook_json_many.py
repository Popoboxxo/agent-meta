#!/usr/bin/env python3
"""Read several dotted fields from a PreToolUse JSON payload in one process.

Issues #1169 (single parse instead of one interpreter start per field) and
#1238 (the Python core lives in an importable module behind a thin shell shim).

Contract (SPEC-HOOK-SINGLE-PARSE-2026-11-11, §2):

* ``read_many(payload_bytes, paths) -> bytes`` returns one NUL-terminated
  field per requested path, in argument order, followed by an ``ok`` trailer.
* A path that does not resolve, a ``null`` value and object/array values read
  as an empty field (matching ``hook_json_get``'s ``default=""``).
* Scalars are stringified with ``str()``, matching ``hook_json_get``.
* Bytes in / bytes out with ``surrogateescape`` on input and output, with a
  ``surrogatepass`` fallback for lone surrogates (v1.0.1 behavior).
* Any failure -- invalid JSON, a NUL byte inside a *requested* value, an
  unencodable value -- fails the WHOLE call: nothing is written to stdout and
  the caller exits 1.  A NUL field would otherwise shift the following fields
  into the wrong variables (AC-6); failing closed is safer than masking it.

This module is stdlib-only.  The shell shim in ``hook_common.sh`` resolves the
interpreter through the shared ``hook_python_bin`` helper, so there is a single
Python resolution for this code path (#1238).
"""
from __future__ import annotations

import json
import sys
from typing import Iterable, List


class PayloadError(ValueError):
    """Raised when the payload cannot be read safely; callers fail closed."""


def _encode(text: str) -> bytes:
    """Encode a scalar the same way ``hook_json_get`` emits it."""
    try:
        return text.encode("utf-8", "surrogateescape")
    except UnicodeEncodeError:
        return text.encode("utf-8", "surrogatepass")


def read_many(payload: bytes, paths: Iterable[str]) -> bytes:
    """Return NUL-terminated fields plus the ``ok`` trailer for ``paths``.

    :raises PayloadError: on invalid JSON or a NUL byte inside a requested
        value.  No partial output is ever produced -- the result is assembled
        in memory and returned only after every field has been validated.
    """
    requested: List[str] = list(paths)
    if not requested:
        raise PayloadError("no paths requested")

    try:
        document = json.loads(payload.decode("utf-8", "surrogateescape"))
    except Exception as exc:  # malformed JSON, undecodable input, etc.
        raise PayloadError("payload is not valid JSON") from exc

    chunks: List[bytes] = []
    for path in requested:
        current = document
        for key in path.split("."):
            if isinstance(current, dict):
                current = current.get(key)
            else:
                current = None
                break
        if current is None or isinstance(current, (dict, list)):
            value = b""
        else:
            value = _encode(str(current))
        if b"\x00" in value:
            raise PayloadError("NUL byte in requested field: " + path)
        chunks.append(value + b"\x00")

    chunks.append(b"ok\x00")
    return b"".join(chunks)


def main(argv: List[str]) -> int:
    """CLI entry point: payload on stdin, paths in ``argv``."""
    if len(argv) < 1:
        return 1
    try:
        output = read_many(sys.stdin.buffer.read(), argv)
    except PayloadError:
        return 1
    sys.stdout.buffer.write(output)
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
