"""Shared JSON-document persistence helpers for cache.py and checkpoint.py.

Both modules read a small JSON state file, must tolerate a corrupted file
without crashing (#576), and must write back atomically (#573). That
read/error-handling/write triplet was duplicated with subtly different
error handling in each module (#586) — this is the single place it lives
now.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .io import write_atomic

_logger = logging.getLogger(__name__)


def load_json_document(path: Path, default: Any = None) -> Any:
    """Read a JSON document, returning `default` when missing or corrupt.

    A corrupt file (partial write, disk error, hand-edited garbage) is
    logged as a warning and treated the same as a missing file — callers
    must keep working (skip the entry, start fresh) instead of crashing.
    """
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        _logger.warning("corrupt JSON file %s: %s: %s", path, type(e).__name__, e)
        return default


def save_json_document(path: Path, data: dict) -> None:
    """Write a JSON document atomically (see io.write_atomic)."""
    write_atomic(path, json.dumps(data, indent=2, ensure_ascii=False))
