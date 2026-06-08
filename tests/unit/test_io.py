"""Tests for scripts.lib.io — YAML/JSON loading, hashing, safe paths."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lib.io import (
    SyncError,
    _load_yaml_or_json,
    content_hash,
    is_unchanged,
    safe_path,
)


class TestLoadYamlOrJson:
    def test_loads_yaml_file(self, temp_dir: Path) -> None:
        path = temp_dir / "test.yaml"
        path.write_text("key: value\nlist:\n  - a\n  - b\n", encoding="utf-8")
        data, used = _load_yaml_or_json(path)
        assert data == {"key": "value", "list": ["a", "b"]}
        assert used == path

    def test_loads_json_file(self, temp_dir: Path) -> None:
        path = temp_dir / "test.json"
        path.write_text('{"key": "value", "num": 42}', encoding="utf-8")
        data, used = _load_yaml_or_json(path)
        assert data == {"key": "value", "num": 42}

    def test_returns_empty_when_no_file_exists(self, temp_dir: Path) -> None:
        path = temp_dir / "nonexistent.yaml"
        data, used = _load_yaml_or_json(path)
        assert data == {}
        assert used == path

    def test_prefers_first_existing_file(self, temp_dir: Path) -> None:
        first = temp_dir / "first.yaml"
        second = temp_dir / "second.yaml"
        first.write_text("from: first\n", encoding="utf-8")
        second.write_text("from: second\n", encoding="utf-8")
        data, used = _load_yaml_or_json(first, second)
        assert data["from"] == "first"
        assert used == first

    def test_falls_back_to_second(self, temp_dir: Path) -> None:
        first = temp_dir / "missing.yaml"
        second = temp_dir / "present.yaml"
        second.write_text("from: second\n", encoding="utf-8")
        data, used = _load_yaml_or_json(first, second)
        assert data["from"] == "second"
        assert used == second


class TestContentHash:
    def test_same_input_same_hash(self) -> None:
        h1 = content_hash("hello world")
        h2 = content_hash("hello world")
        assert h1 == h2
        assert len(h1) == 16

    def test_different_input_different_hash(self) -> None:
        h1 = content_hash("hello")
        h2 = content_hash("world")
        assert h1 != h2

    def test_returns_string(self) -> None:
        h = content_hash("test")
        assert isinstance(h, str)
        # Hex digest check
        assert all(c in "0123456789abcdef" for c in h)


class TestIsUnchanged:
    def test_unchanged_file(self, temp_dir: Path) -> None:
        path = temp_dir / "file.txt"
        path.write_text("content", encoding="utf-8")
        assert is_unchanged(path, "content") is True

    def test_changed_content(self, temp_dir: Path) -> None:
        path = temp_dir / "file.txt"
        path.write_text("old", encoding="utf-8")
        assert is_unchanged(path, "new") is False

    def test_missing_file(self, temp_dir: Path) -> None:
        path = temp_dir / "missing.txt"
        assert is_unchanged(path, "content") is False


class TestSafePath:
    def test_path_inside_base(self) -> None:
        base = Path("/base")
        result = safe_path(base, "sub", "file.txt")
        assert result == Path("/base/sub/file.txt")

    def test_path_traversal_blocked(self) -> None:
        base = Path("/base")
        with pytest.raises(ValueError, match="Path traversal"):
            safe_path(base, "..", "..", "etc", "passwd")

    def test_multiple_parts(self) -> None:
        base = Path("/base")
        result = safe_path(base, "a", "b", "c")
        assert result == Path("/base/a/b/c")


class TestSyncError:
    def test_is_exception(self) -> None:
        with pytest.raises(SyncError, match="test error"):
            raise SyncError("test error")

    def test_can_be_caught(self) -> None:
        try:
            raise SyncError("boom")
        except SyncError as e:
            assert str(e) == "boom"
        else:
            pytest.fail("Expected SyncError")
