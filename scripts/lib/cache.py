"""Outcome-Cache für Orchestrator-Delegationen."""
from __future__ import annotations
import hashlib
import time
from pathlib import Path
from typing import Any

from .json_persistence import load_json_document, save_json_document

CACHE_FILE = ".meta-viz/delegation-cache.json"

_EMPTY_CACHE = {"entries": {}, "stats": {"hits": 0, "misses": 0}}


def cache_key(agent: str, prompt: str) -> str:
    """SHA256-Hash aus Agent-Name und Prompt (erste 200 Zeichen)."""
    raw = f"{agent}:{prompt[:200]}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def read(cache_path: str, key: str, ttl: int = 3600) -> Any | None:
    """Liest cached result oder None wenn expired/missing.

    Side-effect-free (#580): does not touch the cache file. Hit statistics
    used to be updated here via a read-modify-write on every read, which
    corrupted the cache file under concurrent access (multiple orchestrator
    delegations reading the same cache in parallel). Call ``record_hit()``
    separately if hit statistics are needed — it is decoupled from the read
    path on purpose so a burst of concurrent reads never races on a write.
    """
    data = load_json_document(Path(cache_path), default=None)
    if data is None:
        return None

    entry = data.get("entries", {}).get(key)
    if entry is None:
        return None

    if time.time() - entry.get("timestamp", 0) > ttl:
        return None

    return entry.get("result")


def _hits_journal_path(cache_path: str) -> Path:
    return Path(str(cache_path) + ".hits")


def record_hit(cache_path: str) -> None:
    """Record a cache hit without touching the shared cache file (#580).

    Appends one line to a small companion journal file instead of doing a
    read-modify-write on the JSON cache — a single small append is atomic
    on POSIX filesystems, so concurrent hit recordings never corrupt each
    other. ``write()`` drains the journal into the persisted hit counter
    the next time it writes the cache anyway (batched, not locked).
    """
    journal = _hits_journal_path(cache_path)
    try:
        with open(journal, "a", encoding="utf-8") as f:
            f.write("1\n")
    except OSError:
        pass  # stats are best-effort — never fail the caller over this


def _drain_hits_journal(cache_path: str) -> int:
    """Consume and delete the hits journal, returning the recorded count."""
    journal = _hits_journal_path(cache_path)
    if not journal.exists():
        return 0
    try:
        count = sum(1 for _ in journal.open(encoding="utf-8"))
        journal.unlink()
        return count
    except OSError:
        return 0


def _pending_hits(cache_path: str) -> int:
    """Peek at the hits journal without draining it (read-only, for stats)."""
    journal = _hits_journal_path(cache_path)
    if not journal.exists():
        return 0
    try:
        return sum(1 for _ in journal.open(encoding="utf-8"))
    except OSError:
        return 0


def write(cache_path: str, key: str, result: Any, max_entries: int = 100) -> None:
    """Schreibt Ergebnis in Cache mit LRU-Eviction."""
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = load_json_document(path, default=dict(_EMPTY_CACHE))
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
    stats = data.setdefault("stats", {"hits": 0, "misses": 0})
    stats["hits"] = stats.get("hits", 0) + _drain_hits_journal(cache_path)
    stats["misses"] = stats.get("misses", 0) + 1
    save_json_document(path, data)


def invalidate(cache_path: str) -> bool:
    """Löscht Cache-Datei. Returns True wenn erfolgreich."""
    path = Path(cache_path)
    deleted = False
    if path.exists():
        path.unlink()
        deleted = True
    journal = _hits_journal_path(cache_path)
    if journal.exists():
        journal.unlink()
    return deleted


def cache_stats(cache_path: str) -> dict:
    """Returns hit count, miss count, cache size."""
    path = Path(cache_path)
    data = load_json_document(path, default=None)
    if data is None:
        return {"hits": 0, "misses": 0, "entries": 0, "size_bytes": 0}

    stats = data.get("stats", {})
    return {
        "hits": stats.get("hits", 0) + _pending_hits(cache_path),
        "misses": stats.get("misses", 0),
        "entries": len(data.get("entries", {})),
        "size_bytes": path.stat().st_size,
    }
