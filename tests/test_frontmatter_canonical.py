"""Unit tests for the canonical frontmatter parsing/split helpers (#571).

Covers `lib.frontmatter.parse_frontmatter_file` (the new file-reading wrapper
introduced to replace config_audit.py's duplicate `_parse_frontmatter`) plus
regression coverage for the `_split_frontmatter`-based rewrites of
`lib.commands._add_frontmatter_field` and
`lib.rules._build_always_apply_frontmatter` — both used to reimplement the
"---"-fence detection inline instead of delegating to the canonical splitter.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.commands import _add_frontmatter_field
from lib.frontmatter import parse_frontmatter_file
from lib.rules import _build_always_apply_frontmatter


# --- parse_frontmatter_file -------------------------------------------------

def test_parse_frontmatter_file_reads_valid_frontmatter(tmp_path):
    p = tmp_path / "agent.md"
    p.write_text("---\nname: developer\nversion: 1.0.0\n---\nBody text\n", encoding="utf-8")
    fm = parse_frontmatter_file(p)
    assert fm["name"] == "developer"
    assert fm["version"] == "1.0.0"


def test_parse_frontmatter_file_missing_frontmatter_returns_empty_dict(tmp_path):
    p = tmp_path / "agent.md"
    p.write_text("No frontmatter here.\n", encoding="utf-8")
    assert parse_frontmatter_file(p) == {}


def test_parse_frontmatter_file_malformed_yaml_returns_empty_dict(tmp_path):
    p = tmp_path / "agent.md"
    p.write_text("---\nname: [unclosed\n---\nBody\n", encoding="utf-8")
    assert parse_frontmatter_file(p) == {}


def test_parse_frontmatter_file_missing_file_returns_empty_dict(tmp_path):
    assert parse_frontmatter_file(tmp_path / "does-not-exist.md") == {}


# --- commands._add_frontmatter_field ----------------------------------------

def test_add_frontmatter_field_inserts_new_field():
    content = "---\nname: x\ndescription: y\n---\nbody text"
    out = _add_frontmatter_field(content, "invokable", "true")
    assert out == "---\nname: x\ndescription: y\ninvokable: true\n---\nbody text"


def test_add_frontmatter_field_noop_when_field_present():
    content = "---\nname: x\ninvokable: true\n---\nbody"
    assert _add_frontmatter_field(content, "invokable", "true") == content


def test_add_frontmatter_field_noop_without_frontmatter():
    content = "no frontmatter here"
    assert _add_frontmatter_field(content, "invokable", "true") == content


def test_add_frontmatter_field_noop_on_malformed_frontmatter():
    """Opening fence with no closing fence must be left untouched, not treated
    as 'no frontmatter' (which would incorrectly prepend a second block)."""
    content = "---\nno closing fence at all"
    assert _add_frontmatter_field(content, "invokable", "true") == content


# --- rules._build_always_apply_frontmatter ----------------------------------

def test_build_always_apply_frontmatter_injects_into_existing_block():
    content = "---\nname: x\n---\nbody"
    out = _build_always_apply_frontmatter(content, "")
    assert out == "---\nname: x\nalwaysApply: false\n---\nbody"


def test_build_always_apply_frontmatter_noop_on_malformed_frontmatter():
    content = "---\nno closing fence"
    assert _build_always_apply_frontmatter(content, "hello") == content
