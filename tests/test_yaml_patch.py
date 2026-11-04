"""Contract tests for ``lib.yaml_patch.patch_top_level`` (issues #1074, #1092).

The patcher rewrites only the top-level segments that changed. Every other
byte of the document -- comments, blank lines, key order, inline comments,
CRLF line endings, a missing final newline -- must survive untouched.

``None`` is the documented "cannot patch safely" signal: the caller decides
whether to fall back to a full dump. The patcher itself never raises for
malformed/ambiguous input.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import yaml

from lib.yaml_patch import patch_top_level


def dump(d):
    return yaml.safe_dump(d, sort_keys=False, default_flow_style=False, allow_unicode=True)


ORIG = ("# header comment\nproject:\n  name: x\n# keep me\nroles:\n- a\n- b\n"
        "\n# about presets\ntier-preset: Normal\n")


def test_unchanged_segments_byte_identical():
    assert patch_top_level(ORIG, yaml.safe_load(ORIG), dump) == ORIG


def test_added_top_level_key_appended_with_comment():
    doc = yaml.safe_load(ORIG)
    doc["speech-mode"] = "short"
    out = patch_top_level(ORIG, doc, dump, comments={"speech-mode": "Kommunikationsstil"})
    assert out == ORIG + "# Kommunikationsstil\nspeech-mode: short\n"


def test_changed_section_rerendered_other_sections_untouched():
    doc = yaml.safe_load(ORIG)
    doc["roles"] = ["a", "b", "c"]
    out = patch_top_level(ORIG, doc, dump)
    assert out.startswith("# header comment\nproject:\n  name: x\n# keep me\nroles:\n- a\n- b\n- c\n")
    assert out.endswith("\n# about presets\ntier-preset: Normal\n")


def test_removed_key():
    doc = yaml.safe_load(ORIG)
    del doc["roles"]
    assert patch_top_level(ORIG, doc, dump) == (
        "# header comment\nproject:\n  name: x\n\n# about presets\ntier-preset: Normal\n")


def test_inline_comment_and_crlf_preserved():
    text = "a: 1  # inline\r\nb: 2\r\n"
    doc = yaml.safe_load(text)
    doc["b"] = 3
    out = patch_top_level(text, doc, dump)
    assert out.startswith("a: 1  # inline\r\n") and yaml.safe_load(out) == {"a": 1, "b": 3}


def test_anchor_document_returns_none():
    text = "a: &x 1\nb: *x\n"
    assert patch_top_level(text, yaml.safe_load(text), dump) is None


def test_multi_document_and_non_mapping_return_none():
    assert patch_top_level("a: 1\n---\nb: 2\n", {"a": 1}, dump) is None
    assert patch_top_level("- a\n- b\n", {"a": 1}, dump) is None


def test_selfcheck_failure_returns_none():
    doc = yaml.safe_load(ORIG)
    doc["roles"] = ["z"]
    assert patch_top_level(ORIG, doc, lambda d: "roles: [unclosed\n") is None


def test_tab_indentation_returns_none():
    text = "project:\n\tname: x\n"
    assert patch_top_level(text, {"project": {"name": "x"}}, dump) is None


def test_duplicate_top_level_keys_return_none():
    # PyYAML silently keeps the last duplicate; patching would be ambiguous.
    assert patch_top_level("a: 1\na: 2\n", {"a": 2}, dump) is None


def test_no_trailing_newline_churn_on_unchanged_document():
    text = "a: 1\nb: 2"
    assert patch_top_level(text, {"a": 1, "b": 2}, dump) == text


def test_changed_last_block_keeps_missing_final_newline():
    text = "a: 1\nb: 2"
    out = patch_top_level(text, {"a": 1, "b": 3}, dump)
    assert out == "a: 1\nb: 3"
    assert yaml.safe_load(out) == {"a": 1, "b": 3}
