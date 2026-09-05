"""Golden-output comparison tests for the two templating engines.

Issue #476 (Phase 2 item 2.1, plan: docs/plans/2026-09-05-issue-674-roadmap.md).

Two engines perform ``{{...}}`` substitution in this repo:

* **Engine 1** — ``substitute()`` (``scripts/lib/variables.py``), used for
  agent/rule/command/skill rendering.
* **Engine 2** — ``TemplateBuilder`` (``scripts/lib/context_templates/builder.py``),
  used for context templates (loops/conditionals/partials).

This suite pins the *current, call-site-visible output of both engines* as
hard-coded golden values. It must stay green on the pre-cutover dual-engine
state AND after the unification onto the shared escape-safe substitution core
(``scripts/lib/substitution.py``): any golden value going red after the
cutover means an existing call site's output changed — forbidden.

Known, intentional engine discrepancies (issue #476; intentionally NOT
resolved by silently picking a winner — the unified core preserves both
behaviors via per-engine lookup/keep policies):

===  =====================================================  ==========================  ====================================
 #   Input                                                  substitute()                TemplateBuilder.resolve_variables()
===  =====================================================  ==========================  ====================================
D1   ``{{ VAR }}`` (whitespace inside braces)               kept verbatim               substituted; missing -> ``{{VAR}}``
D2   lowercase name ``{{lower_key}}``                       kept even if defined        substituted when defined
D3   escape syntax ``{{%VAR%}}``                            rendered as ``{{VAR}}``     kept verbatim (no escape support)
D4   ``{{PAL_*}}`` (delegation-syntax placeholders)         exempt, kept silently       substituted when defined
D5   variable explicitly bound to ``None``                  ``str(None)`` -> ``None``   kept as placeholder
D6   missing variable                                       warn (strict: raise)        silent keep
D7   empty name ``{{ }}``                                   kept verbatim               rebuilt as ``{{}}``
D8   newline inside braces                                  kept verbatim               substituted
===  =====================================================  ==========================  ====================================

Values that historically triggered the raw-replacement escape bug (#674)
— backslashes, ``$`` group references, regex metacharacters — are asserted
verbatim for BOTH engines in every shape (plain, loop item, conditional
branch), guarding the escape-safety invariant of the unified path.
"""

from pathlib import Path

import pytest

from scripts.lib.context_templates.builder import TemplateBuilder
from scripts.lib.io import SyncError
from scripts.lib.log import SyncLog
from scripts.lib.variables import substitute

# ---------------------------------------------------------------------------
# Shared corpora
# ---------------------------------------------------------------------------

# Values whose bytes must survive every engine verbatim (#674 class of bug).
# Covers: backslash escapes (\s, \U, trailing), $ group refs, regex
# metacharacters, German umlauts/UTF-8, multiline values.
HAZARD_VALUES = [
    r"C:\Users\x\s",
    r"C:\Users\HerMES",
    r"group ref \1 hazard",
    "trailing backslash \\",
    r"$1 \g<0> ${VAR}",
    r"a.*[b](c){d}$^?+|",
    "Straße mit Ümläuten ✓",
    "line1\nline2",
]


def run_builder_pipeline(template: str, variables: dict) -> str:
    """Render through Engine 2's full pipeline in build() order (no file IO).

    build() order: partials -> loops -> conditionals -> variables. Partials
    need the filesystem and are covered separately; this helper runs the
    three in-memory passes in the exact same order.
    """
    builder = TemplateBuilder(Path("."))
    rendered = builder.resolve_loops(template, variables)
    rendered = builder.resolve_conditionals(rendered, variables)
    return builder.resolve_variables(rendered, variables)


# ---------------------------------------------------------------------------
# Golden corpus: plain {{...}} placeholder kinds, both engines
# ---------------------------------------------------------------------------

# (case_id, template, variables, expected_substitute, expected_builder)
PLACEHOLDER_CORPUS = [
    # Engines agree:
    ("simple_present", "t = {{TITLE}}", {"TITLE": "VAL"}, "t = VAL", "t = VAL"),
    (
        "empty_string_value",
        "x {{X}} y",
        {"X": ""},
        "x  y",
        "x  y",
    ),
    (
        "lowercase_missing",
        "a {{lower_key}} b",
        {},
        "a {{lower_key}} b",
        "a {{lower_key}} b",
    ),
    (
        "escape_missing",
        "e {{%NOPE%}}",
        {},
        "e {{NOPE}}",
        "e {{%NOPE%}}",
    ),
    (
        "pal_missing",
        "p {{PAL_INVOKE}}",
        {},
        "p {{PAL_INVOKE}}",
        "p {{PAL_INVOKE}}",
    ),
    # D1: whitespace variant — substitute() never matches, builder strips:
    (
        "ws_present",
        "a {{ TITLE }} b",
        {"TITLE": "VAL"},
        "a {{ TITLE }} b",
        "a VAL b",
    ),
    (
        "tab_variant_present",
        "a {{\tTITLE\t}} b",
        {"TITLE": "VAL"},
        "a {{\tTITLE\t}} b",
        "a VAL b",
    ),
    (
        "ws_missing",
        "a {{ NOPE }} b",
        {},
        "a {{ NOPE }} b",
        "a {{NOPE}} b",
    ),
    # D2: lowercase name — substitute() pattern is uppercase-only:
    (
        "lowercase_present",
        "a {{lower_key}} b",
        {"lower_key": "L"},
        "a {{lower_key}} b",
        "a L b",
    ),
    # D3: escape syntax — substitute() renders literal, builder keeps raw:
    (
        "escape_present",
        "e {{%WIN_PATH%}}",
        {"WIN_PATH": r"C:\x\s"},
        "e {{WIN_PATH}}",
        "e {{%WIN_PATH%}}",
    ),
    # D4: PAL_* delegation placeholders — substitute() exempts them even
    # when defined; builder has no PAL awareness:
    (
        "pal_present_in_vars",
        "p {{PAL_INVOKE}}",
        {"PAL_INVOKE": "X"},
        "p {{PAL_INVOKE}}",
        "p X",
    ),
    # D5: explicit None value — key-in-dict vs get-is-not-None semantics:
    (
        "none_value",
        "n {{NIL}}",
        {"NIL": None},
        "n None",
        "n {{NIL}}",
    ),
    # D7/D8: degenerate names — builder rebuilds stripped/empty names:
    (
        "empty_braces",
        "x {{}} y {{ }} z",
        {},
        "x {{}} y {{ }} z",
        "x {{}} y {{}} z",
    ),
    (
        "newline_in_placeholder",
        "x {{ NOPE\n}} y",
        {},
        "x {{ NOPE\n}} y",
        "x {{NOPE}} y",
    ),
]


class TestGoldenPlaceholders:
    """Golden outputs for every placeholder kind, both engines."""

    @pytest.mark.parametrize(
        "case_id, template, variables, expected_substitute, expected_builder",
        PLACEHOLDER_CORPUS,
        ids=[c[0] for c in PLACEHOLDER_CORPUS],
    )
    def test_substitute_engine(
        self,
        case_id: str,
        template: str,
        variables: dict,
        expected_substitute: str,
        expected_builder: str,
    ) -> None:
        """Engine 1 output is byte-identical to the pinned golden value."""
        assert substitute(template, variables, "golden", SyncLog()) == expected_substitute

    @pytest.mark.parametrize(
        "case_id, template, variables, expected_substitute, expected_builder",
        PLACEHOLDER_CORPUS,
        ids=[c[0] for c in PLACEHOLDER_CORPUS],
    )
    def test_builder_engine(
        self,
        case_id: str,
        template: str,
        variables: dict,
        expected_substitute: str,
        expected_builder: str,
    ) -> None:
        """Engine 2 output is byte-identical to the pinned golden value."""
        assert run_builder_pipeline(template, variables) == expected_builder


# ---------------------------------------------------------------------------
# Escape-safety invariant (#674): hazard values verbatim in both engines
# ---------------------------------------------------------------------------


class TestGoldenEscapeSafety:
    """Backslash/$/metachar/UTF-8 values survive verbatim — no re.PatternError."""

    @pytest.mark.parametrize("value", HAZARD_VALUES)
    def test_substitute_hazard_value_verbatim(self, value: str) -> None:
        """Engine 1 inserts hazard values byte-identically (function replacement)."""
        rendered = substitute("v = {{VAL}}", {"VAL": value}, "golden", SyncLog())
        assert rendered == f"v = {value}"

    @pytest.mark.parametrize("value", HAZARD_VALUES)
    def test_builder_hazard_value_verbatim(self, value: str) -> None:
        """Engine 2 inserts hazard values byte-identically (function replacement)."""
        assert run_builder_pipeline("v = {{VAL}}", {"VAL": value}) == f"v = {value}"

    @pytest.mark.parametrize("value", HAZARD_VALUES)
    def test_builder_loop_item_hazard_value_verbatim(self, value: str) -> None:
        """{{#each}} item values are inserted verbatim in both engines' shapes."""
        builder = TemplateBuilder(Path("."))
        rendered = builder.resolve_loops(
            "A{{#each items}}[{{val}}]{{/each}}B",
            {"items": [{"val": value}]},
        )
        assert rendered == f"A[{value}]B"

    def test_substitute_multiline_value_keeps_newlines(self) -> None:
        """A multiline value is not re-interpreted by either engine."""
        value = "line1\nline2\nline3"
        assert substitute("{{ML}}", {"ML": value}, "golden", SyncLog()) == value
        assert run_builder_pipeline("{{ML}}", {"ML": value}) == value


# ---------------------------------------------------------------------------
# Engine 1 policy contract: warnings, strict mode, exemptions
# ---------------------------------------------------------------------------


class TestGoldenSubstitutePolicy:
    """substitute()-specific policies (warnings / strict) stay byte-identical."""

    def test_missing_variable_warns_and_keeps_placeholder(self) -> None:
        """D6: missing var emits a warning naming key and source, keeps {{KEY}}."""
        log = SyncLog()
        rendered = substitute("a {{MISSING_VAR}} b", {}, "rules/x.md", log)

        assert rendered == "a {{MISSING_VAR}} b"
        assert len(log.warnings) == 1
        assert "MISSING_VAR" in log.warnings[0]
        assert "rules/x.md" in log.warnings[0]

    def test_pal_missing_never_warns(self) -> None:
        """PAL_* placeholders are exempt from the missing-variable warning."""
        log = SyncLog()
        rendered = substitute("a {{PAL_INVOKE}} b", {}, "rules/x.md", log)

        assert rendered == "a {{PAL_INVOKE}} b"
        assert log.warnings == []

    def test_strict_mode_raises_on_unknown_placeholder(self) -> None:
        """strict=True raises SyncError for an unknown, non-exempt placeholder."""
        with pytest.raises(SyncError, match="MISSING_VAR"):
            substitute(
                "a {{MISSING_VAR}} b", {}, "rules/x.md", SyncLog(), strict=True
            )

    def test_strict_mode_exempts_escapes_and_pal(self) -> None:
        """strict=True never raises for escaped or PAL_* placeholders."""
        rendered = substitute(
            "a {{PAL_X}} b {{%NOPE%}}",
            {},
            "rules/x.md",
            SyncLog(),
            strict=True,
        )
        assert rendered == "a {{PAL_X}} b {{NOPE}}"

    def test_strict_mode_raises_before_substituting_rest(self) -> None:
        """The strict check fires during the substitution pass on first miss."""
        with pytest.raises(SyncError):
            substitute(
                "{{KNOWN}} {{MISSING_VAR}}",
                {"KNOWN": "ok"},
                "rules/x.md",
                SyncLog(),
                strict=True,
            )


# ---------------------------------------------------------------------------
# Engine 2 golden: {{#each}} loop semantics
# ---------------------------------------------------------------------------


class TestGoldenBuilderLoops:
    """Pinned TemplateBuilder loop semantics (unchanged by the unification)."""

    @pytest.mark.parametrize(
        "case_id, template, variables, expected",
        [
            # Loop item value None renders as str(None):
            (
                "item_none_value_renders_None",
                "A{{#each items}}[{{k}}]{{/each}}B",
                {"items": [{"k": None}]},
                "A[None]B",
            ),
            # Non-dict items are skipped entirely:
            (
                "non_dict_items_skipped",
                "A{{#each items}}x{{/each}}B",
                {"items": ["s", 42, {"k": "ok"}]},
                "AxB",
            ),
            # Missing/empty list removes the block, keeps surroundings:
            (
                "missing_list_removes_block",
                "A{{#each items}}x{{/each}}B",
                {},
                "AB",
            ),
            (
                "empty_list_removes_block",
                "A{{#each items}}x{{/each}}B",
                {"items": []},
                "AB",
            ),
            # Item keys are matched by re.escape — non-identifier keys work:
            (
                "dotted_item_key",
                "A{{#each items}}{{a.b}}{{/each}}B",
                {"items": [{"a.b": "DOT"}]},
                "ADOTB",
            ),
            # Keys absent from the item stay for the later variable pass
            # (loop output still shows the raw placeholder — the fallback
            # to the global variables dict happens in resolve_variables):
            (
                "loop_keeps_item_miss_for_later_passes",
                "A{{#each items}}{{k}}|{{g}}{{/each}}B",
                {"items": [{"k": "i"}], "g": "G"},
                "Ai|{{g}}B",
            ),
            # Empty-string item value substitutes to nothing:
            (
                "item_empty_string_value",
                "A{{#each items}}[{{k}}]{{/each}}B",
                {"items": [{"k": ""}]},
                "A[]B",
            ),
            # Nested {{#each}}: the outer match ends at the FIRST {{/each}},
            # so the inner block re-matches against the top-level variables
            # and the outer item data is lost (quirk, deterministic):
            (
                "nested_each_current_quirk",
                "A{{#each outer}}{{#each inner}}{{x}}{{/each}}-{{y}}{{/each}}B",
                {"outer": [{"inner": [{"x": "1"}, {"x": "2"}], "y": "Y1"}]},
                "AB",
            ),
        ],
    )
    def test_loop_golden(
        self, case_id: str, template: str, variables: dict, expected: str
    ) -> None:
        """Loop rendering is byte-identical to the pinned golden value."""
        builder = TemplateBuilder(Path("."))
        assert builder.resolve_loops(template, variables) == expected

    def test_if_inside_each_uses_global_scope(self) -> None:
        """{{#if}} inside {{#each}} is evaluated AFTER loops against the
        GLOBAL variables dict — item fields are not in scope (quirk)."""
        variables = {"items": [{"on": "true"}, {"on": "false"}]}
        assert run_builder_pipeline(
            "{{#each items}}{{#if on}}Y{{else}}N{{/if}}{{/each}}", variables
        ) == "NN"

    @pytest.mark.parametrize("value", HAZARD_VALUES)
    def test_loop_hazard_values_verbatim(self, value: str) -> None:
        """Every hazard value class is loop-safe (no re.PatternError)."""
        builder = TemplateBuilder(Path("."))
        rendered = builder.resolve_loops(
            "A{{#each items}}[{{v}}]{{/each}}B", {"items": [{"v": value}]}
        )
        assert rendered == f"A[{value}]B"


# ---------------------------------------------------------------------------
# Engine 2 golden: {{#if}}/{{#unless}} semantics
# ---------------------------------------------------------------------------


class TestGoldenBuilderConditionals:
    """Pinned TemplateBuilder conditional truthiness and branch semantics."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("true", "T"),
            ("false", "F"),
            ("False", "F"),
            ("0", "T"),  # non-empty string other than 'false' is truthy
            ("", "F"),
            ("yes", "T"),
            (None, "F"),
            (0, "F"),
            (False, "F"),
        ],
    )
    def test_if_truthiness_table(self, value, expected: str) -> None:
        """bool(val and str(val).lower() != 'false') — pinned per value."""
        builder = TemplateBuilder(Path("."))
        rendered = builder.resolve_conditionals(
            "{{#if V}}T{{else}}F{{/if}}", {"V": value}
        )
        assert rendered == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("true", ""),
            ("false", "T"),
            (None, "T"),
        ],
    )
    def test_unless_truthiness(self, value, expected: str) -> None:
        """{{#unless}} inverts the truthiness decision."""
        builder = TemplateBuilder(Path("."))
        rendered = builder.resolve_conditionals("{{#unless V}}T{{/unless}}", {"V": value})
        assert rendered == expected

    @pytest.mark.parametrize(
        "variables, expected",
        [
            ({"a": "true", "b": "true"}, "ABC"),
            ({"a": "true", "b": "false"}, "Ab-falseC"),
            ({"a": "false", "b": "true"}, ""),
        ],
    )
    def test_nested_if_resolves_inner_to_outer(
        self, variables: dict, expected: str
    ) -> None:
        """Nested ifs resolve innermost-first via repeated passes."""
        builder = TemplateBuilder(Path("."))
        rendered = builder.resolve_conditionals(
            "{{#if a}}A{{#if b}}B{{else}}b-false{{/if}}C{{/if}}", variables
        )
        assert rendered == expected

    def test_if_branch_hazard_content_verbatim(self) -> None:
        """Backslash content in the if-branch passes through untouched."""
        builder = TemplateBuilder(Path("."))
        rendered = builder.resolve_conditionals(
            r"{{#if V}}win: C:\Users\x\s{{else}}unix{{/if}}", {"V": "true"}
        )
        assert rendered == r"win: C:\Users\x\s"

    def test_else_branch_literal_group_ref_verbatim(self) -> None:
        """A literal \\1 in the else-branch is not a replacement-group hazard."""
        builder = TemplateBuilder(Path("."))
        rendered = builder.resolve_conditionals(
            "{{#if V}}yes{{else}}alt \\1 path{{/if}}", {"V": False}
        )
        assert rendered == "alt \\1 path"


# ---------------------------------------------------------------------------
# Engine 2 golden: full build() pipeline (frontmatter, partials, file IO)
# ---------------------------------------------------------------------------


class TestGoldenBuilderBuild:
    """End-to-end build() golden values (the call-site-visible pipeline)."""

    @pytest.fixture()
    def template_dir(self, tmp_path: Path) -> Path:
        """Template dir with a frontmattered template and a partial."""
        partials = tmp_path / "partials"
        partials.mkdir()
        (tmp_path / "t.md").write_text(
            "---\nname: t\nversion: 1.0.0\n---\nHello {{NAME}} {{> hdr }}tail\n",
            encoding="utf-8",
        )
        (partials / "hdr.md").write_text(
            "---\nfm: stripped\n---\nP={{N}}\n", encoding="utf-8"
        )
        return tmp_path

    def test_build_full_pipeline(self, template_dir: Path) -> None:
        """Frontmatter stripped, partial inlined (own frontmatter stripped too)."""
        builder = TemplateBuilder(template_dir)
        rendered = builder.build("t", {"NAME": "N1", "N": "PV"})
        assert rendered == "Hello N1 P=PV\ntail\n"

    def test_build_missing_partial_and_var(self, tmp_path: Path) -> None:
        """Missing partial renders empty; missing variable keeps placeholder."""
        (tmp_path / "t2.md").write_text("A{{> nope }}B{{MISSING}}", encoding="utf-8")
        builder = TemplateBuilder(tmp_path)
        assert builder.build("t2", {}) == "AB{{MISSING}}"

    def test_build_hazard_value_end_to_end(self, template_dir: Path) -> None:
        """A hazard value flows through partial + variable passes verbatim."""
        (template_dir / "t3.md").write_text(
            "{{> hdr }}path={{P}}", encoding="utf-8"
        )
        builder = TemplateBuilder(template_dir)
        rendered = builder.build("t3", {"N": "N1", "P": r"C:\Users\x\s"})
        assert rendered == f"P=N1\npath={r'C:\Users\x\s'}"
