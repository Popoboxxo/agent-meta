"""Unit tests for scripts/lib/config.py — variable substitution and config loading."""

import pytest
from lib.config import substitute, strip_inactive_dod_blocks, build_variables
from lib.log import SyncLog


@pytest.fixture
def log():
    return SyncLog()


# ---------------------------------------------------------------------------
# substitute
# ---------------------------------------------------------------------------

def test_substitute_simple(log):
    text = "Hello {{NAME}}!"
    result = substitute(text, {"NAME": "World"}, "test.md", log)
    assert result == "Hello World!"


def test_substitute_multiple_occurrences(log):
    text = "{{VAR}} and {{VAR}} again"
    result = substitute(text, {"VAR": "x"}, "test.md", log)
    assert result == "x and x again"


def test_substitute_multiple_vars(log):
    text = "{{A}} + {{B}} = {{C}}"
    result = substitute(text, {"A": "1", "B": "2", "C": "3"}, "test.md", log)
    assert result == "1 + 2 = 3"


def test_substitute_unknown_var_leaves_placeholder(log):
    text = "Hello {{UNKNOWN}}!"
    result = substitute(text, {}, "test.md", log)
    assert "{{UNKNOWN}}" in result


def test_substitute_escape_syntax(log):
    # {{%VAR%}} should render as {{VAR}} (documentation escape)
    text = "Use {{%PROJECT_NAME%}} as a placeholder example."
    result = substitute(text, {"PROJECT_NAME": "my-project"}, "test.md", log)
    assert "{{PROJECT_NAME}}" in result
    assert "my-project" not in result


def test_substitute_no_vars_unchanged(log):
    text = "No placeholders here."
    result = substitute(text, {"UNUSED": "x"}, "test.md", log)
    assert result == text


def test_substitute_empty_string_value(log):
    text = "prefix-{{EMPTY}}-suffix"
    result = substitute(text, {"EMPTY": ""}, "test.md", log)
    assert result == "prefix--suffix"


# ---------------------------------------------------------------------------
# strip_inactive_dod_blocks
# ---------------------------------------------------------------------------

DOD_TEXT = """\
Always shown.

{{#if DOD_TESTS_REQUIRED}}
## Tests
- [ ] Tests pass
{{/if}}

{{#if DOD_SECURITY_AUDIT}}
## Security
- [ ] Audit done
{{/if}}

End.
"""


def test_strip_dod_removes_inactive_block():
    # Blocks are removed when the variable is explicitly "false"
    vars_no_tests = {"DOD_TESTS_REQUIRED": "false", "DOD_SECURITY_AUDIT": "false"}
    result = strip_inactive_dod_blocks(DOD_TEXT, vars_no_tests)
    assert "## Tests" not in result
    assert "## Security" not in result
    assert "Always shown." in result


def test_strip_dod_keeps_active_block():
    # "true" → block content kept, markers removed
    vars_with_tests = {"DOD_TESTS_REQUIRED": "true", "DOD_SECURITY_AUDIT": "false"}
    result = strip_inactive_dod_blocks(DOD_TEXT, vars_with_tests)
    assert "## Tests" in result
    assert "## Security" not in result


def test_strip_dod_keeps_all_when_all_active():
    vars_all = {"DOD_TESTS_REQUIRED": "true", "DOD_SECURITY_AUDIT": "true"}
    result = strip_inactive_dod_blocks(DOD_TEXT, vars_all)
    assert "## Tests" in result
    assert "## Security" in result


def test_strip_dod_markers_removed_from_active_block():
    text = "{{#if DOD_TESTS_REQUIRED}}\n## Tests\n{{/if}}\n"
    result = strip_inactive_dod_blocks(text, {"DOD_TESTS_REQUIRED": "true"})
    assert "{{#if" not in result
    assert "{{/if}}" not in result
    assert "## Tests" in result


def test_strip_dod_no_blocks_unchanged():
    text = "No DOD blocks here."
    result = strip_inactive_dod_blocks(text, {})
    assert result == text


# ---------------------------------------------------------------------------
# build_variables
# ---------------------------------------------------------------------------

def test_build_variables_contains_project_name(agent_meta_root):
    config = {
        "project": {"name": "test-project"},
        "ai-providers": ["Claude"],
        "roles": ["developer", "git"],
    }
    variables, warnings = build_variables(config, agent_meta_root)
    assert variables.get("PROJECT_NAME") == "test-project"


def test_build_variables_contains_agent_meta_version(agent_meta_root):
    config = {
        "project": {"name": "test-project"},
        "ai-providers": ["Claude"],
        "roles": ["developer"],
    }
    variables, _ = build_variables(config, agent_meta_root)
    assert "AGENT_META_VERSION" in variables
    assert variables["AGENT_META_VERSION"]  # non-empty


def test_build_variables_dod_fields_present(agent_meta_root):
    config = {
        "project": {"name": "test-project"},
        "ai-providers": ["Claude"],
        "roles": [],
        "dod-preset": "rapid-prototyping",
    }
    variables, _ = build_variables(config, agent_meta_root)
    assert "DOD_TESTS_REQUIRED" in variables
    assert "DOD_REQ_TRACEABILITY" in variables
    assert "DOD_SECURITY_AUDIT" in variables
