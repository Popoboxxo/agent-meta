"""Python validator for ``test-environments`` (SPEC-TEST-ENVIRONMENTS-2026-10-31).

Part A covers structure, names, enums (including the bool/"quote the value"
rule, C6), ``url``/``notes`` sanitisation and the warning-only semantics.
Part B (Task 4) adds the ``token-env`` reference resolution (RF3) and the
hard abort wired into the config load path.

Run: ``python3 -m pytest tests/test_test_environments_lib.py``
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
import yaml

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib.test_environments import check_test_environments  # noqa: E402


def _cfg(envs, **extra):
    return {"test-environments": envs, **extra}


def test_absent_null_and_empty_block_are_unconfigured():  # RF1
    for cfg in ({}, {"test-environments": None}, {"test-environments": {}}):
        assert check_test_environments(cfg) == ([], [])


@pytest.mark.parametrize("bad", [[], ["a"], "text", 3])
def test_non_mapping_block_is_hard_error(bad):  # RF1
    errors, _ = check_test_environments({"test-environments": bad})
    assert errors == [f"test-environments: expected a mapping, got {type(bad).__name__}"]


@pytest.mark.parametrize("name", ["Bad", "-x", "a_b", "", 123, True, None])
def test_invalid_environment_name(name):  # RF2
    errors, _ = check_test_environments(_cfg({name: {}}))
    assert len(errors) == 1 and "invalid environment name" in errors[0]


def test_entry_must_be_mapping():
    assert check_test_environments(_cfg({"a": "x"}))[0] == [
        "test-environments.a: expected a mapping, got str"
    ]


def test_unknown_key_is_error():
    assert check_test_environments(_cfg({"a": {"colour": "red"}}))[0] == [
        "test-environments.a.colour: unknown key"
    ]


@pytest.mark.parametrize(
    "key,bad", [("kind", "remoteish"), ("access", "write"), ("remote-access", "maybe")]
)
def test_invalid_enum_value(key, bad):
    err = check_test_environments(_cfg({"a": {key: bad}}))[0][0]
    assert f"test-environments.a.{key}" in err and "invalid value" in err


@pytest.mark.parametrize("key", ["kind", "access", "remote-access"])
@pytest.mark.parametrize("val", [True, False])
def test_bool_in_enum_field_is_error_quote_the_value(key, val):
    assert "quote the value" in check_test_environments(_cfg({"a": {key: val}}))[0][0]


def test_yaml_1_1_off_is_caught():
    cfg = yaml.safe_load("test-environments:\n  a:\n    kind: remote\n    remote-access: off\n")
    assert any("quote the value" in e for e in check_test_environments(cfg)[0])


@pytest.mark.parametrize("url", ["http://u:p@host/x", "https://user@host", "https://:pw@host"])
def test_url_userinfo_is_error(url):
    assert "url must not contain userinfo" in check_test_environments(
        _cfg({"a": {"kind": "remote", "url": url}})
    )[0][0]


@pytest.mark.parametrize("url", ["", 5])
def test_url_empty_or_non_string_is_error(url):
    assert "url must be a non-empty string" in check_test_environments(_cfg({"a": {"url": url}}))[0][0]


@pytest.mark.parametrize(
    "key,val", [("url", "http://h/{{X}}"), ("notes", "see {{TOKEN}}"), ("notes", "a }} b")]
)
def test_placeholder_syntax_rejected(key, val):  # RF4
    assert "placeholder syntax not allowed" in check_test_environments(
        _cfg({"a": {"kind": "remote", key: val}})
    )[0][0]


def test_notes_must_be_string():
    assert "notes must be a string" in check_test_environments(_cfg({"a": {"notes": 5}}))[0][0]


def test_defaults_alone_have_no_findings():
    assert check_test_environments(_cfg({"a": {}})) == ([], [])


def test_warnings_for_ineffective_or_conflicting_settings():
    _, w = check_test_environments(_cfg({"a": {"kind": "local", "url": "http://x"}}))
    assert w == ["test-environments.a: kind: local ignores url"]
    _, w = check_test_environments(_cfg({"a": {"kind": "local", "remote-access": "ask"}}))
    assert w == ["test-environments.a: kind: local ignores remote-access"]
    _, w = check_test_environments(_cfg({"a": {"kind": "local", "access": "deploy"}}))
    assert w == ["test-environments.a: access: deploy has no effect for kind: local"]
    _, w = check_test_environments(
        _cfg({"a": {"kind": "remote", "access": "deploy", "remote-access": "deny"}})
    )
    assert w == ["test-environments.a: access: deploy conflicts with remote-access: deny (deny wins)"]


def _root_imports(tree):
    roots = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            roots |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.level == 0 and n.module:
            roots.add(n.module.split(".")[0])
    return roots


def test_module_budget_and_constraints():  # AC-ENV-18, AC-ENV-11
    text = (SCRIPTS / "lib" / "test_environments.py").read_text(encoding="utf-8")
    assert text.count("\n") <= 600 and "provider ==" not in text and "provider==" not in text
    assert _root_imports(ast.parse(text)) <= {
        "__future__",
        "re",
        "pathlib",
        "typing",
        "sys",
        "logging",
        "urllib",
    }
