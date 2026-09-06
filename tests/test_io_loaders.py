"""Behavior-matrix tests for the canonical single-file loaders (#479).

`load_yaml_file` / `load_json_file` (lib.io) replace ~7 hand-rolled per-module
YAML/JSON loaders. These tests pin the error-behavior matrix each migrated
module relies on:

| condition            | "raise"    | "default" | "warn"             |
|----------------------|------------|-----------|--------------------|
| missing file         | default    | default   | default (silent)   |
| PyYAML unavailable   | SyncError  | default   | warning + default  |
| unreadable (OSError) | SyncError  | default   | warning + default  |
| malformed YAML/JSON  | SyncError  | default   | warning + default  |
| non-mapping top level| SyncError  | default   | warning + default  |
| empty document       | {}         | {}        | {}                 |
| valid mapping        | parsed     | parsed    | parsed             |
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.io import (  # noqa: E402
    SyncError,
    load_json_file,
    load_yaml_file,
)
from lib.log import SyncLog  # noqa: E402


# --- load_yaml_file: on_error modes ------------------------------------------

def test_yaml_missing_file_returns_default_in_every_mode(tmp_path):
    missing = tmp_path / "nope.yaml"
    assert load_yaml_file(missing, on_error="raise", default={}) == {}
    assert load_yaml_file(missing, on_error="default", default={}) == {}
    assert load_yaml_file(missing, on_error="warn", default={}, log=SyncLog()) == {}


def test_yaml_missing_file_returns_none_sentinel_when_default_is_none(tmp_path):
    assert load_yaml_file(tmp_path / "nope.yaml", on_error="default", default=None) is None


def test_yaml_malformed_raise_mode_sync_error_with_location(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("key: [unclosed\n  other: :\n", encoding="utf-8")
    with pytest.raises(SyncError) as exc:
        load_yaml_file(path, on_error="raise", default={})
    assert "broken.yaml" in str(exc.value)


def test_yaml_malformed_default_mode_returns_default(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("key: [unclosed\n", encoding="utf-8")
    sentinel = {"fallback": True}
    assert load_yaml_file(path, on_error="default", default=sentinel) is sentinel


def test_yaml_malformed_warn_mode_warns_and_returns_default(tmp_path):
    path = tmp_path / "broken.yaml"
    path.write_text("key: [unclosed\n", encoding="utf-8")
    log = SyncLog()
    assert load_yaml_file(path, on_error="warn", default={}, log=log) == {}
    assert len(log.warnings) == 1
    assert "broken.yaml" in log.warnings[0]


@pytest.mark.parametrize("body", ["- a\n- b\n", "just a string\n", "42\n"])
def test_yaml_non_mapping_top_level_follows_on_error(tmp_path, body):
    path = tmp_path / "list.yaml"
    path.write_text(body, encoding="utf-8")
    with pytest.raises(SyncError):
        load_yaml_file(path, on_error="raise", default={})
    assert load_yaml_file(path, on_error="default", default={}) == {}
    log = SyncLog()
    assert load_yaml_file(path, on_error="warn", default={}, log=log) == {}
    assert log.warnings


def test_yaml_empty_document_yields_empty_dict_in_every_mode(tmp_path):
    path = tmp_path / "empty.yaml"
    path.write_text("", encoding="utf-8")
    assert load_yaml_file(path, on_error="raise", default={"x": 1}) == {}
    assert load_yaml_file(path, on_error="default", default={"x": 1}) == {}


def test_yaml_valid_mapping_parsed(tmp_path):
    path = tmp_path / "ok.yaml"
    path.write_text("roles:\n  dev:\n    workflow_tier: required\n", encoding="utf-8")
    data = load_yaml_file(path, on_error="raise", default={})
    assert data["roles"]["dev"]["workflow_tier"] == "required"


def test_yaml_invalid_on_error_mode_rejected(tmp_path):
    with pytest.raises(ValueError):
        load_yaml_file(tmp_path / "x.yaml", on_error="explode")  # type: ignore[arg-type]


# --- load_json_file: on_error modes ------------------------------------------

def test_json_missing_file_returns_default(tmp_path):
    assert load_json_file(tmp_path / "nope.json", on_error="raise", default={}) == {}
    assert load_json_file(tmp_path / "nope.json", on_error="default") is None


def test_json_malformed_raise_mode_sync_error_with_line_col(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"a": 1,,}', encoding="utf-8")
    with pytest.raises(SyncError) as exc:
        load_json_file(path, on_error="raise", default={})
    assert "broken.json" in str(exc.value)


def test_json_malformed_default_and_warn_modes(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text("{oops}", encoding="utf-8")
    assert load_json_file(path, on_error="default", default=None) is None
    log = SyncLog()
    assert load_json_file(path, on_error="warn", default={}, log=log) == {}
    assert len(log.warnings) == 1


def test_json_lists_are_legitimate_documents(tmp_path):
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]\n", encoding="utf-8")
    assert load_json_file(path, on_error="raise", default=None) == [1, 2, 3]


def test_json_valid_object_parsed(tmp_path):
    path = tmp_path / "ok.json"
    path.write_text('{"version": 1, "hashes": {"claude": "x"}}\n', encoding="utf-8")
    assert load_json_file(path, on_error="default", default={})["version"] == 1
