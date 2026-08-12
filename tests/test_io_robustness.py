"""Regression tests for scripts/lib/io.py config loading and JSONC parsing.

Covers:
- #461 `_load_yaml_or_json()` crashed with an unhandled `yaml.YAMLError` on a
  malformed config, and returned non-dict data that every caller then blew up
  on with an opaque `AttributeError: 'list' object has no attribute 'get'`.
- #474 `read_json_lenient()` stripped inline comments with a quote-excluding
  regex, truncating any line whose *string value* contained `//` (a URL, a
  regex, a path) and silently returning None for the whole file.
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.io import (  # noqa: E402
    SyncError,
    _load_yaml_or_json,
    read_json_lenient,
    strip_jsonc_comments,
)


# ---------------------------------------------------------------------------
# #461 -- _load_yaml_or_json robustness
# ---------------------------------------------------------------------------

def test_malformed_yaml_raises_sync_error(tmp_path):
    path = tmp_path / "project.yaml"
    path.write_text("key: [unclosed\n  other: :\n", encoding="utf-8")
    with pytest.raises(SyncError) as exc:
        _load_yaml_or_json(path)
    assert "project.yaml" in str(exc.value)


def test_malformed_json_raises_sync_error(tmp_path):
    path = tmp_path / "config.json"
    path.write_text('{"a": 1,,}', encoding="utf-8")
    with pytest.raises(SyncError) as exc:
        _load_yaml_or_json(path)
    assert "config.json" in str(exc.value)


@pytest.mark.parametrize("body", ["- a\n- b\n", "just a string\n", "42\n"])
def test_non_mapping_root_raises_sync_error(tmp_path, body):
    # Every caller immediately does data.get(...) -- a list/scalar root must
    # fail with a readable message, not an AttributeError deep in a caller.
    path = tmp_path / "roles.yaml"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(SyncError) as exc:
        _load_yaml_or_json(path)
    assert "mapping" in str(exc.value)


def test_empty_yaml_still_returns_empty_dict(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    data, used = _load_yaml_or_json(path)
    assert data == {}
    assert used == path


def test_missing_file_returns_preferred_path(tmp_path):
    preferred = tmp_path / "a.yaml"
    data, used = _load_yaml_or_json(preferred, tmp_path / "b.yaml")
    assert data == {}
    assert used == preferred


def test_valid_yaml_roundtrip(tmp_path):
    path = tmp_path / "ok.yaml"
    path.write_text("roles:\n  developer:\n    model: balanced\n", encoding="utf-8")
    data, _ = _load_yaml_or_json(path)
    assert data["roles"]["developer"]["model"] == "balanced"


# ---------------------------------------------------------------------------
# #474 -- JSONC comment stripping must not touch string values
# ---------------------------------------------------------------------------

def test_double_slash_inside_string_survives(tmp_path):
    path = tmp_path / "opencode.jsonc"
    path.write_text('{\n  "pattern": "match a // b"\n}\n', encoding="utf-8")
    assert read_json_lenient(path) == {"pattern": "match a // b"}


def test_url_in_string_survives(tmp_path):
    path = tmp_path / "opencode.jsonc"
    path.write_text('{\n  "url": "https://example.com/x"\n}\n', encoding="utf-8")
    assert read_json_lenient(path) == {"url": "https://example.com/x"}


def test_full_line_and_inline_comments_are_stripped(tmp_path):
    path = tmp_path / "opencode.jsonc"
    path.write_text(
        '{\n'
        '  // leading comment\n'
        '  "a": 1, // trailing comment\n'
        '  "b": 2,\n'
        '}\n',
        encoding="utf-8",
    )
    assert read_json_lenient(path) == {"a": 1, "b": 2}


def test_bom_is_tolerated(tmp_path):
    path = tmp_path / "opencode.jsonc"
    path.write_bytes(b'\xef\xbb\xbf{"a": 1}')
    assert read_json_lenient(path) == {"a": 1}


def test_unparsable_file_returns_none(tmp_path):
    path = tmp_path / "broken.jsonc"
    path.write_text("{ this is not json", encoding="utf-8")
    assert read_json_lenient(path) is None


def test_escaped_quote_does_not_desync_string_tracking():
    # A \" inside a string must not be read as the closing quote -- otherwise
    # the stripper thinks it is outside a string and eats the rest.
    text = '{"a": "he said \\" // not a comment", "b": 1}'
    assert strip_jsonc_comments(text) == text


def test_comment_stripping_preserves_line_count():
    # Line structure must survive so json's error line numbers stay usable.
    text = '{\n  "a": 1 // c\n}\n'
    assert strip_jsonc_comments(text).count("\n") == text.count("\n")
