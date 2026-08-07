"""Regression tests for #425: DEVELOPER_SNIPPETS_PATH, TESTER_SNIPPETS_PATH and
DEV_STACK_START are optional, project-specific string variables. Templates
interpolate them (e.g. "{{SNIPPETS_DIR}}/{{DEVELOPER_SNIPPETS_PATH}}"), so a
plain empty-string fallback (like ARCHITECTURE/DEV_COMMANDS in
test_config_variable_fallbacks.py) would render a misleading trailing-slash
path instead of omitting the clause. build_variables() instead derives a
<VAR>_SET boolean so templates can wrap the whole clause in a standalone
{{#if <VAR>_SET}}...{{/if}} line (own-line, not inline — an inline trailing
clause would make strip_inactive_conditional_blocks's inactive-block removal
also eat the newline before the following line, merging it into the next
line of prose).
"""

from pathlib import Path

from scripts.lib.config import build_variables, strip_inactive_conditional_blocks, substitute
from scripts.lib.log import SyncLog

OPTIONAL_VARS = ("DEVELOPER_SNIPPETS_PATH", "TESTER_SNIPPETS_PATH", "DEV_STACK_START")


def test_unset_optional_vars_default_to_empty_string_and_unset_flag():
    repo_root = Path(__file__).resolve().parents[1]
    variables, _ = build_variables({}, repo_root)
    for var in OPTIONAL_VARS:
        assert variables.get(var) == ""
        assert variables.get(f"{var}_SET") == "false"


def test_explicit_optional_var_sets_flag_true():
    repo_root = Path(__file__).resolve().parents[1]
    config = {"variables": {"DEVELOPER_SNIPPETS_PATH": "python-fastapi"}}
    variables, _ = build_variables(config, repo_root)
    assert variables["DEVELOPER_SNIPPETS_PATH"] == "python-fastapi"
    assert variables["DEVELOPER_SNIPPETS_PATH_SET"] == "true"
    # Vars the project never set stay unset.
    assert variables["TESTER_SNIPPETS_PATH_SET"] == "false"


def test_conditional_block_omitted_when_unset_no_placeholder_leak_no_line_merge():
    repo_root = Path(__file__).resolve().parents[1]
    variables, _ = build_variables({}, repo_root)
    template = (
        "4. Read context.\n"
        "{{#if DEVELOPER_SNIPPETS_PATH_SET}}`{{SNIPPETS_DIR}}/{{DEVELOPER_SNIPPETS_PATH}}` if present — apply patterns.{{/if}}\n"
        "5. Implement."
    )
    rendered = strip_inactive_conditional_blocks(template, variables)
    rendered = substitute(rendered, variables, "test", SyncLog())
    assert rendered == "4. Read context.\n5. Implement."
    assert "DEVELOPER_SNIPPETS_PATH" not in rendered
    assert "{{" not in rendered


def test_conditional_block_rendered_when_set():
    repo_root = Path(__file__).resolve().parents[1]
    config = {"variables": {
        "DEVELOPER_SNIPPETS_PATH": "python-fastapi",
        "SNIPPETS_DIR": "snippets",
    }}
    variables, _ = build_variables(config, repo_root)
    template = (
        "4. Read context.\n"
        "{{#if DEVELOPER_SNIPPETS_PATH_SET}}`{{SNIPPETS_DIR}}/{{DEVELOPER_SNIPPETS_PATH}}` if present — apply patterns.{{/if}}\n"
        "5. Implement."
    )
    rendered = strip_inactive_conditional_blocks(template, variables)
    rendered = substitute(rendered, variables, "test", SyncLog())
    assert rendered == "4. Read context.\n`snippets/python-fastapi` if present — apply patterns.\n5. Implement."
    assert "{{" not in rendered
