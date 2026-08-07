"""Outcome-Cache für Orchestrator-Delegationen."""
from __future__ import annotations
import hashlib
import json
import time
from pathlib import Path
from typing import Any

CACHE_FILE = ".meta-viz/delegation-cache.json"


def cache_key(agent: str, prompt: str) -> str:
    """SHA256-Hash aus Agent-Name und Prompt (erste 200 Zeichen)."""
    raw = f"{agent}:{prompt[:200]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read(cache_path: str, key: str, ttl: int = 3600) -> Any | None:
    """Liest cached result oder None wenn expired/missing."""
    path = Path(cache_path)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return None

    entry = data.get("entries", {}).get(key)
    if entry is None:
        return None

    if time.time() - entry.get("timestamp", 0) > ttl:
        return None

    data["stats"]["hits"] = data.get("stats", {}).get("hits", 0) + 1
    _save(cache_path, data)
    return entry.get("result")


def write(cache_path: str, key: str, result: Any, max_entries: int = 100) -> None:
    """Schreibt Ergebnis in Cache mit LRU-Eviction."""
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        data = {"entries": {}, "stats": {"hits": 0, "misses": 0}}

    entries = data.get("entries", {})

    # LRU Eviction
    if len(entries) >= max_entries and key not in entries:
        oldest_key = min(entries, key=lambda k: entries[k].get("timestamp", 0))
        del entries[oldest_key]

    entries[key] = {
        "result": result,
        "timestamp": time.time(),
    }
    data["entries"] = entries
    data["stats"]["misses"] = data.get("stats", {}).get("misses", 0) + 1
    _save(cache_path, data)


def invalidate(cache_path: str) -> bool:
    """Löscht Cache-Datei. Returns True wenn erfolgreich."""
    path = Path(cache_path)
    if path.exists():
        path.unlink()
        return True
    return False


def cache_stats(cache_path: str) -> dict:
    """Returns hit count, miss count, cache size."""
    path = Path(cache_path)
    if not path.exists():
        return {"hits": 0, "misses": 0, "entries": 0, "size_bytes": 0}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return {"hits": 0, "misses": 0, "entries": 0, "size_bytes": 0}

    stats = data.get("stats", {})
    return {
        "hits": stats.get("hits", 0),
        "misses": stats.get("misses", 0),
        "entries": len(data.get("entries", {})),
        "size_bytes": path.stat().st_size,
    }


def _save(cache_path: str, data: dict) -> None:
    path = Path(cache_path)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
