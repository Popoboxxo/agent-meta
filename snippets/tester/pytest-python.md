---
snippet: tester-syntax
version: "1.0.0"
language: "Python"
runtime: "pytest"
description: "Test-Syntax und Beispiele für Python-Projekte mit pytest."
---

### Test-Syntax

```python
import pytest

class TestModuleName:
    def test_req_xxx_should_do_something_specific(self):
        # Arrange
        input_value = # realistischer Wert
        # Act
        result = function_under_test(input_value)
        # Assert
        assert result == expected_value
```

### Test-Benennung

```python
class TestQueueManager:
    def test_req004_should_add_video_to_queue(self):
        ...

    def test_req007_should_remove_video_by_position(self):
        ...
```

### Echte Assertions

```python
# ❌ FALSCH — prüft nichts Sinnvolles
def test_req004_should_add_video():
    assert True

# ✅ RICHTIG — prüft das tatsächliche Ergebnis
def test_req004_should_add_video_to_queue():
    add_video(item)
    assert len(queue) == 1
    assert queue[0].id == item.id
```

### Realitätsnahe Testdaten

```python
# ❌ FALSCH — bedeutungslose Dummy-Daten
video = {"id": "abc", "title": "test", "url": "foo"}

# ✅ RICHTIG — realistische Daten die dem echten Use-Case entsprechen
video = {
    "id": "yt-dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "duration": 213,
}
```
