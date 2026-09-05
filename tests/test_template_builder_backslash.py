r"""Regression tests for escape-safe re.sub replacement in TemplateBuilder.

Issue #674 Phase 0, Task 0.4
(plan: docs/plans/2026-09-05-issue-674-roadmap.md).

Historical bug: TemplateBuilder.resolve_loops() passed the raw value as
the re.sub *replacement string*. Values containing backslashes were then
interpreted as replacement-template escapes and crashed with
``re.PatternError: bad escape \s`` (``\s``), ``bad escape \U`` (Windows
user paths) or ``invalid group reference`` (literal ``\1``).

Fix (Task 0.2): function replacement (``lambda m, val=str(v): val``) —
re.sub treats the return value of a function replacement literally.

This suite pins the invariant across the whole substitution path:
resolve_loops(), resolve_variables() and resolve_conditionals() must
insert backslash values verbatim and must never raise re.PatternError.
resolve_variables()/resolve_conditionals() already used function
replacement; their tests document that invariant defensively.
"""

from pathlib import Path

import pytest

from scripts.lib.context_templates.builder import TemplateBuilder


# Values that crashed the raw replacement-string path before the fix:
#   \s   -> re.PatternError: bad escape \s
#   \U   -> re.PatternError: bad escape \U
#   \1   -> re.PatternError: invalid group reference 1
#   "\"  -> re.PatternError: bad escape (end of pattern)
ESCAPE_HAZARD_VALUES = [
    r"C:\Users\x\s",
    r"C:\Users\HerMES",
    r"group ref \1 hazard",
    "trailing backslash \\",
]


@pytest.fixture()
def builder() -> TemplateBuilder:
    """TemplateBuilder with a dummy dir (substitution methods never touch the FS)."""
    return TemplateBuilder(Path("."))


class TestResolveLoopsBackslash:
    """Task 0.4 core case: {{#each}} loop items with backslash values."""

    @pytest.mark.parametrize("value", ESCAPE_HAZARD_VALUES)
    def test_loop_item_value_is_verbatim(
        self, builder: TemplateBuilder, value: str
    ) -> None:
        """A loop item value with backslashes is inserted verbatim (no re.PatternError)."""
        template = "{{#each items}}- {{name}} = {{value}}\n{{/each}}"
        variables = {"items": [{"name": "win_path", "value": value}]}

        rendered = builder.resolve_loops(template, variables)

        assert rendered == f"- win_path = {value}\n"

    def test_loop_multiple_backslash_items_all_verbatim(
        self, builder: TemplateBuilder
    ) -> None:
        """All hazard values survive a single loop expansion unmodified."""
        template = "{{#each items}}[{{name}}] {{value}}; {{/each}}"
        variables = {
            "items": [
                {"name": f"item_{i}", "value": value}
                for i, value in enumerate(ESCAPE_HAZARD_VALUES)
            ]
        }

        rendered = builder.resolve_loops(template, variables)

        for i, value in enumerate(ESCAPE_HAZARD_VALUES):
            assert f"[item_{i}] {value}; " in rendered

    def test_loop_non_backslash_value_unchanged(
        self, builder: TemplateBuilder
    ) -> None:
        """Sanity: normal values still substitute (fix does not change semantics)."""
        template = "{{#each items}}- {{name}}: {{value}}{{/each}}"
        variables = {"items": [{"name": "plain", "value": "hello world"}]}

        rendered = builder.resolve_loops(template, variables)

        assert rendered == "- plain: hello world"


class TestResolveVariablesBackslash:
    """Invariant: variable substitution is escape-safe (function replacement)."""

    @pytest.mark.parametrize("value", ESCAPE_HAZARD_VALUES)
    def test_variable_value_is_verbatim(
        self, builder: TemplateBuilder, value: str
    ) -> None:
        """A variable value with backslashes is inserted verbatim."""
        rendered = builder.resolve_variables(
            "path = {{WIN_PATH}}", {"WIN_PATH": value}
        )

        assert rendered == f"path = {value}"

    def test_unknown_variable_left_untouched(self, builder: TemplateBuilder) -> None:
        """Unresolved placeholders keep their literal {{NAME}} form."""
        rendered = builder.resolve_variables(
            "x = {{NOPE}}", {"WIN_PATH": r"C:\Users\x\s"}
        )

        assert rendered == "x = {{NOPE}}"


class TestResolveConditionalsBackslash:
    """Invariant: conditional bodies with backslashes stay verbatim."""

    def test_if_body_backslash_content_verbatim(
        self, builder: TemplateBuilder
    ) -> None:
        """If-branch content containing backslashes passes through verbatim."""
        template = r"{{#if WIN_PATH}}win: C:\Users\x\s{{else}}unix{{/if}}"

        rendered = builder.resolve_conditionals(
            template, {"WIN_PATH": r"C:\Users\HerMES"}
        )

        assert rendered == r"win: C:\Users\x\s"

    def test_else_body_literal_group_ref_verbatim(
        self, builder: TemplateBuilder
    ) -> None:
        """Else-branch content containing a literal \\1 passes through verbatim."""
        template = "{{#if FLAG}}yes{{else}}alt \\1 path{{/if}}"

        rendered = builder.resolve_conditionals(template, {"FLAG": False})

        assert rendered == "alt \\1 path"

    def test_backslash_value_is_truthy(self, builder: TemplateBuilder) -> None:
        """A backslash value controls truthiness without breaking the regex pass."""
        template = "{{#if WIN_PATH}}taken{{else}}empty{{/if}}"

        rendered = builder.resolve_conditionals(
            template, {"WIN_PATH": r"C:\Users\x\s"}
        )

        assert rendered == "taken"
