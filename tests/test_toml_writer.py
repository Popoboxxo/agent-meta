"""Unit tests for the stdlib TOML writer (scripts/lib/toml_writer.py).

Background: the codex-toml frontmatter-mechanism (Codex provider) needs a
TOML writer; Python ships tomllib (read-only) but no writer, and agent-meta
is stdlib-only apart from PyYAML. The core guarantee pinned here is the
round-trip: tomllib.loads(toml_writer.dumps(x)) == x for every fixture of
the supported subset (see the module docstring of toml_writer.py).
"""
from __future__ import annotations

import tomllib

import pytest

from scripts.lib.toml_writer import (
    dumps,
    format_key,
    format_multiline_string,
    format_string,
    format_value,
)


def _rt(data: dict) -> dict:
    """dumps() + tomllib parse; empty documents parse to {}."""
    out = dumps(data)
    return tomllib.loads(out) if out.strip() else {}


# ---------------------------------------------------------------------------
# Round-trip fixtures (the guarantee: tomllib.loads(dumps(x)) == x)
# ---------------------------------------------------------------------------

ROUND_TRIP_FIXTURES = [
    {},
    {"a": 1},
    {"s": "hi", "i": -3, "f": 1.5, "b": True, "b2": False},
    {"list": [1, "two", 3.0, True], "empty_list": [], "empty_dict": {}},
    {"table": {"x": 1, "sub": {"deep": "v"}}, "top": "stays first"},
    {"aot": [{"n": 1, "sub": {"k": "v"}}, {"n": 2}], "after": "t"},
    {"nested_aot": {"outer": [{"inner": [{"x": 1}]}]}},
    {"weird key": 1, "a.b": 2, "": "empty key", "k-m_o9": 3},
    {"ml": "line1\nline2\n"},
    {"q": 'say """hi""" ok'},
    {"trail_q1": 'end"', "trail_q2": 'end""', "trail_q3": 'end"""'},
    {"bs": "C:\\path\\to\\x", "esc_nl": "a\\nb"},
    {"ctl": "a\tb\rc\x08d\n", "del": "\x7f", "us": "ab"},
    {"mixed": [1, {"a": 2}, "three"]},
    {"tab": "a\tb", "sq": "it's \"quoted\""},
    {"leading_nl": "\nstart\n", "empty_str": ""},
]

_IDS = [
    "empty", "int", "scalars", "inline-containers", "nested-tables",
    "array-of-tables", "nested-aot", "exotic-keys", "multiline",
    "triple-quote", "trailing-quotes", "backslash", "control-chars",
    "mixed-list", "tab-and-quotes", "leading-newline",
]


@pytest.mark.parametrize("data", ROUND_TRIP_FIXTURES, ids=_IDS)
def test_round_trip_tomllib(data: dict) -> None:
    """tomllib.loads(dumps(x)) == x for every fixture of the subset."""
    assert _rt(data) == data


# ---------------------------------------------------------------------------
# Deterministic output
# ---------------------------------------------------------------------------

def test_empty_dict_returns_empty_string() -> None:
    assert dumps({}) == ""


def test_scalars_before_tables_toml_requirement() -> None:
    out = dumps({"t": {"x": 1}, "s": 0})
    assert out == 's = 0\n[t]\nx = 1'


def test_insertion_order_preserved() -> None:
    out = dumps({"z": 1, "a": 2, "m": 3})
    assert out == "z = 1\na = 2\nm = 3"


def test_determinism_same_input_same_output() -> None:
    fixture = {
        "ml": "body\nwith \"\"\" quotes\n",
        "t": {"x": 1, "sub": {"deep": [1, 2]}},
        "aot": [{"n": 1}, {"n": 2}],
    }
    assert dumps(fixture) == dumps(fixture)
    # No trailing whitespace on any line
    for line in dumps(fixture).split("\n"):
        assert line == line.rstrip()


def test_dumps_rejects_non_dict_root() -> None:
    with pytest.raises(TypeError):
        dumps([1, 2])  # type: ignore[arg-type]


@pytest.mark.parametrize("value", [None, object(), b"bytes"])
def test_dumps_rejects_unsupported_value_types(value: object) -> None:
    with pytest.raises(TypeError):
        dumps({"k": value})


# ---------------------------------------------------------------------------
# Keys
# ---------------------------------------------------------------------------

def test_bare_keys() -> None:
    assert format_key("agent-meta_X9") == "agent-meta_X9"


def test_exotic_keys_are_quoted_and_escaped() -> None:
    assert format_key("a.b") == '"a.b"'
    assert format_key("") == '""'
    assert format_key('say "hi"') == '"say \\"hi\\""'


def test_quoted_key_round_trip() -> None:
    assert _rt({"weird key": 1, "a.b": 2}) == {"weird key": 1, "a.b": 2}


# ---------------------------------------------------------------------------
# Strings: single-line escaping
# ---------------------------------------------------------------------------

def test_string_escaping_quotes_and_backslashes() -> None:
    out = dumps({"s": 'a"b\\c'})
    assert out == 's = "a\\"b\\\\c"'
    assert _rt({"s": 'a"b\\c'}) == {"s": 'a"b\\c'}


def test_control_chars_escaped() -> None:
    out = dumps({"s": "a\bb\fc"})
    assert out == 's = "a\\bb\\fc"'
    assert _rt({"s": "a\bb\fc"}) == {"s": "a\bb\fc"}


def test_other_control_chars_use_unicode_escape() -> None:
    out = dumps({"s": "a\x01b"})
    assert "\\u0001" in out
    assert _rt({"s": "a\x01b"}) == {"s": "a\x01b"}


# ---------------------------------------------------------------------------
# Strings: single vs multi-line decision
# ---------------------------------------------------------------------------

def test_string_without_newline_is_single_line() -> None:
    assert format_string("no newline") == '"no newline"'


def test_string_with_newline_is_multiline() -> None:
    out = format_string("a\nb")
    assert out.startswith('"""\n')
    assert out.endswith('"""')


def test_multiline_leading_newline_trim_rule() -> None:
    """The newline after the opening delimiter is trimmed — emitting one
    keeps the value exact, even when the value itself starts with \\n."""
    assert tomllib.loads('v = """\n\nfoo"""')["v"] == "\nfoo"
    assert format_string("\nfoo") == '"""\n\nfoo"""'


def test_multiline_body_with_triple_quotes_round_trips() -> None:
    value = 'x = """\nsay """hi""" now\nend"""\n'
    out = dumps({"body": value})
    assert tomllib.loads(out)["body"] == value


def test_multiline_trailing_quotes_and_newlines_round_trip() -> None:
    for value in ("end\n", 'end"', 'end""', 'end"""', 'end\n"""\n'):
        assert _rt({"v": value}) == {"v": value}


def test_format_multiline_string_forces_multiline_form() -> None:
    out = format_multiline_string("single line value")
    assert out.startswith('"""\n') and out.endswith('"""')
    assert tomllib.loads(f'v = {out}')["v"] == "single line value"


# ---------------------------------------------------------------------------
# Tables / arrays-of-tables shapes
# ---------------------------------------------------------------------------

def test_nested_dicts_become_dotted_table_paths() -> None:
    out = dumps({"a": {"b": {"c": 1}}})
    assert out == "[a]\n[a.b]\nc = 1"
    assert _rt({"a": {"b": {"c": 1}}}) == {"a": {"b": {"c": 1}}}


def test_empty_dict_still_gets_table_header() -> None:
    out = dumps({"a": {}})
    assert out == "[a]"
    assert _rt({"a": {}}) == {"a": {}}


def test_array_of_tables_shape() -> None:
    out = dumps({"aot": [{"n": 1}, {"n": 2}]})
    assert out == "[[aot]]\nn = 1\n[[aot]]\nn = 2"


def test_aot_item_sub_tables_attach_to_last_element() -> None:
    out = dumps({"aot": [{"x": 1, "sub": {"k": "v"}}]})
    assert out == '[[aot]]\nx = 1\n[aot.sub]\nk = "v"'
    assert _rt({"aot": [{"x": 1, "sub": {"k": "v"}}]}) == {
        "aot": [{"x": 1, "sub": {"k": "v"}}],
    }


def test_mixed_list_renders_as_inline_array() -> None:
    out = dumps({"m": [1, {"a": 2}, "three"]})
    assert out == 'm = [1, {a = 2}, "three"]'
    assert _rt({"m": [1, {"a": 2}, "three"]}) == {"m": [1, {"a": 2}, "three"]}


# ---------------------------------------------------------------------------
# format_value (shared helper used by agent_toml for extra fields)
# ---------------------------------------------------------------------------

def test_format_value_uses_multiline_form_for_strings_with_newlines() -> None:
    out = format_value("a\nb")
    assert out.startswith('"""\n')


def test_format_value_scalars() -> None:
    assert format_value(True) == "true"
    assert format_value(False) == "false"
    assert format_value(7) == "7"
    assert format_value(2.5) == "2.5"
    assert format_value("x") == '"x"'
