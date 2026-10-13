"""Format helpers for the doctor detectors (IC-21, IC-22, Task 0d.2).

Pure stdlib helpers: a TOML subset parser (Q21), a JSON-schema subset
validator (Q22), the 120-character ``quoted`` clip and the version ordering
used for ``fixed-in``. No file writes, no provider knowledge.
"""
from __future__ import annotations

import json
import re

QUOTED_MAX = 120
_CONTROL = re.compile(r"[\x00-\x1f\x7f]+")
_BARE_KEY = re.compile(r"[A-Za-z0-9_-]+")
_INT = re.compile(r"[+-]?\d[\d_]*")


def clip(text, limit: int = QUOTED_MAX) -> str:
    """Collapse control characters and cut *text* to at most *limit* chars."""
    flat = _CONTROL.sub(" ", str(text)).strip()
    return flat if len(flat) <= limit else flat[: limit - 3] + "..."


# ------------------------------------------------------------------ versions

def version_key(version: str) -> tuple:
    """Orderable key: numeric parts, a release sorts after its prerelease."""
    text = str(version or "").strip().lstrip("v")
    core, _, pre = text.partition("-")
    nums = tuple(int(p) for p in re.findall(r"\d+", core))
    return nums, 0 if pre else 1, pre


# ---------------------------------------------------------------- TOML subset

class TomlUnsupported(ValueError):
    """The text uses TOML syntax outside the supported subset."""


def _strip_comment(line: str) -> str:
    quote = ""
    for i, ch in enumerate(line):
        if quote:
            if ch == quote and line[i - 1] != "\\":
                quote = ""
        elif ch in "\"'":
            quote = ch
        elif ch == "#":
            return line[:i]
    return line


def _split_top(text: str, sep: str) -> list:
    parts, depth, quote, cur = [], 0, "", []
    for ch in text:
        if quote:
            quote = "" if ch == quote else quote
        elif ch in "\"'":
            quote = ch
        elif ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    parts.append("".join(cur))
    return parts


def _split_key(text: str) -> list:
    keys = []
    for part in _split_top(text.strip(), "."):
        part = part.strip()
        if _BARE_KEY.fullmatch(part):
            keys.append(part)
        elif len(part) >= 2 and part[0] == part[-1] and part[0] in "\"'":
            keys.append(part[1:-1])
        else:
            raise TomlUnsupported(f"unsupported key {part!r}")
    return keys


def _parse_value(text: str):
    text = text.strip()
    if text in ("true", "false"):
        return text == "true"
    if text.startswith(('"""', "'''")) or text.startswith("{"):
        raise TomlUnsupported("multi-line strings and inline tables are unsupported")
    if text.startswith('"') and text.endswith('"') and len(text) >= 2:
        try:
            return json.loads(text)
        except ValueError as exc:
            raise TomlUnsupported(str(exc)) from exc
    if text.startswith("'") and text.endswith("'") and len(text) >= 2:
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        items = [p for p in _split_top(inner, ",") if p.strip()]
        return [_parse_value(p) for p in items]
    if _INT.fullmatch(text):
        return int(text.replace("_", ""))
    try:
        return float(text)
    except ValueError as exc:
        raise TomlUnsupported(f"unsupported value {text!r}") from exc


def _descend(root: dict, keys: list) -> dict:
    node = root
    for key in keys:
        node = node.setdefault(key, {})
        if not isinstance(node, dict):
            raise TomlUnsupported(f"key {key!r} redefined")
    return node


def parse_toml_subset(text: str) -> dict:
    """Parse tables, dotted keys and scalar / one-line array values only."""
    root: dict = {}
    current = root
    for raw in text.splitlines():
        line = _strip_comment(raw).strip()
        if not line:
            continue
        if line.startswith("[["):
            raise TomlUnsupported("arrays of tables are unsupported")
        if line.startswith("["):
            if not line.endswith("]"):
                raise TomlUnsupported("multi-line arrays are unsupported")
            current = _descend(root, _split_key(line[1:-1]))
            continue
        key, sep, value = line.partition("=")
        if not sep:
            raise TomlUnsupported("expected key = value")
        keys = _split_key(key)
        _descend(current, keys[:-1])[keys[-1]] = _parse_value(value)
    return root


# ------------------------------------------------------------ JSON-schema subset

_TYPES = {
    "object": dict, "array": list, "string": str, "boolean": bool,
    "null": type(None),
}


def _type_ok(value, name: str) -> bool:
    if name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    return isinstance(value, _TYPES.get(name, ()))


def validate_schema_subset(instance, schema: dict, path: str = "") -> list:
    """Validate type / required / properties / additionalProperties:false / enum."""
    errors: list = []
    where = path or "(root)"
    wanted = schema.get("type")
    if wanted is not None:
        names = wanted if isinstance(wanted, list) else [wanted]
        if not any(_type_ok(instance, n) for n in names):
            errors.append(f"{where}: unexpected type")
            return errors
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{where}: value not in enum")
    if isinstance(instance, dict):
        for name in schema.get("required") or []:
            if name not in instance:
                errors.append(f"{where}: missing required property {name}")
        props = schema.get("properties") or {}
        for name, sub in props.items():
            if name in instance and isinstance(sub, dict):
                errors.extend(validate_schema_subset(
                    instance[name], sub, f"{path}.{name}" if path else name))
        if schema.get("additionalProperties") is False:
            for name in sorted(set(instance) - set(props), key=str):
                errors.append(f"{where}: unexpected property {name}")
    return errors


def schema_from_capability_value(value) -> dict:
    """Derive the schema from a capability value (Interpretation, IC-21 / 0d.1 Nachzug 10).

    A list of field names (or a mapping keyed by field name) becomes
    ``properties`` + ``additionalProperties: false``.
    """
    if isinstance(value, dict):
        value = list(value)
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise ValueError("capability value is not a list of field names")
    return {
        "type": "object",
        "properties": {name: {} for name in value},
        "additionalProperties": False,
    }
