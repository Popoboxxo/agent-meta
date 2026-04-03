---
snippet: developer-syntax
version: "1.0.0"
language: "Python"
runtime: "pytest"
description: "Code-Patterns und Best Practices für Python-Projekte."
---

### Imports & Exports

```python
# ✅ Explizite Imports, kein wildcard
from queue_manager import QueueManager, VideoItem

# ❌ NICHT
from queue_manager import *
```

### Typisierung

```python
# ✅ Type hints für alle Funktionen
def add_video(item: VideoItem) -> None: ...
def process(input: str) -> ProcessResult: ...

# ❌ NICHT
def add_video(item): ...
```

### Fehlerbehandlung

```python
# ✅ Benutzerfreundliche Fehlermeldung
if not item.url:
    raise ValueError("Video URL is required")

# ✅ Technische Details loggen
logger.info("Processing item %s", item.id)
logger.error("Failed to parse response: %s", e)
```

### Dateinamen & Struktur

```
src/
  queue_manager.py        # snake_case Modulname
  test_queue_manager.py   # Test: test_<module>.py
  utils/
    format_duration.py
```

### Async / Await

```python
# ✅ async/await für IO-Operationen
async def fetch_video(url: str) -> VideoItem:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        response.raise_for_status()
        return VideoItem(**response.json())
```
