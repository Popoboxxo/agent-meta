"""Unit tests for the shared escape-safe substitution core.

Issue #476 (Phase 2 item 2.1). ``scripts/lib/substitution.py`` is the ONE
replacement routine both templating engines delegate to; these tests pin
its own contract:

* function-based re.sub replacement — values are inserted verbatim
  (#674 invariant: no ``bad escape``/``invalid group reference`` crashes,
  no ``$``-group interpolation),
* lookup/keep policy flow (including the keep=None identity default),
* constant_lookup() semantics for the {{#each}} loop path,
* exceptions raised by lookup/keep propagate unchanged (strict mode).
"""

from __future__ import annotations

import re

import pytest

from scripts.lib.substitution import (
    constant_lookup,
    replacement_function,
    substitute_placeholders,
)


class TestSubstitutePlaceholders:
    """Contract of the shared substitution routine."""

    def test_values_are_inserted_verbatim(self) -> None:
        """Backslash/$-hazard values never hit the replacement-string parser."""
        for value in (r"C:\Users\x\s", r"\1 \g<0>", r"${VAR} \s \U", "a\\"):
            rendered = substitute_placeholders(
                "v={{V}}",
                re.compile(r"\{\{([A-Z0-9_]+)\}\}"),
                lambda name, _value=value: _value,
            )
            assert rendered == f"v={value}"

    def test_lookup_miss_defers_to_keep(self) -> None:
        """Unresolved names are routed through the keep policy."""
        rendered = substitute_placeholders(
            "a {{A}} b {{B}} c",
            re.compile(r"\{\{([A-Z0-9_]+)\}\}"),
            lambda name: "VAL" if name == "A" else None,
            lambda matched, name: f"<kept:{name}>",
        )
        assert rendered == "a VAL b <kept:B> c"

    def test_keep_defaults_to_identity(self) -> None:
        """Without a keep policy, unresolved placeholders pass through."""
        rendered = substitute_placeholders(
            "a {{A}} b {{B}} c",
            re.compile(r"\{\{([A-Z0-9_]+)\}\}"),
            lambda name: "VAL" if name == "A" else None,
        )
        assert rendered == "a VAL b {{B}} c"

    def test_keep_receives_full_match_and_name(self) -> None:
        """The keep policy can inspect the raw match (e.g. whitespace form)."""
        seen: list[tuple[str, str]] = []

        def keep(matched: str, name: str) -> str:
            seen.append((matched, name))
            return matched

        substitute_placeholders(
            "x {{ NAME }} y",
            re.compile(r"\{\{([^}]*)\}\}"),
            lambda name: None,
            keep,
        )
        assert seen == [("{{ NAME }}", " NAME ")]

    def test_pattern_must_capture_name_as_group_1(self) -> None:
        """A pattern without group 1 breaks the lookup contract (guard)."""
        with pytest.raises(IndexError):
            substitute_placeholders("v", re.compile(r"v"), lambda name: name)

    def test_lookup_exception_propagates(self) -> None:
        """Strict-mode-style exceptions are not swallowed by the core."""

        class Boom(Exception):
            pass

        def lookup(name: str) -> str | None:
            raise Boom(f"unknown {name}")

        with pytest.raises(Boom, match="unknown X"):
            substitute_placeholders(
                "{{X}}", re.compile(r"\{\{([A-Z0-9_]+)\}\}"), lookup
            )

    def test_keep_exception_propagates(self) -> None:
        """Exceptions raised by the keep policy propagate unchanged."""

        class Boom(Exception):
            pass

        with pytest.raises(Boom):
            substitute_placeholders(
                "{{X}}",
                re.compile(r"\{\{([A-Z0-9_]+)\}\}"),
                lambda name: None,
                lambda matched, name: (_ for _ in ()).throw(Boom()),
            )

    def test_all_matches_replaced_in_one_pass(self) -> None:
        """Every occurrence of a resolved placeholder is replaced."""
        rendered = substitute_placeholders(
            "{{A}}-{{A}}-{{B}}",
            re.compile(r"\{\{([A-Z0-9_]+)\}\}"),
            lambda name: "V" if name == "A" else None,
        )
        assert rendered == "V-V-{{B}}"


class TestReplacementFunction:
    """The callback factory behind substitute_placeholders()."""

    def test_returns_re_sub_compatible_callback(self) -> None:
        """Works when passed directly as a re.sub replacement argument."""
        repl = replacement_function(lambda name: str(name).lower())
        assert re.sub(r"\{\{([A-Z0-9_]+)\}\}", repl, "{{AB}} {{CD}}") == "ab cd"

    def test_hazard_value_via_replacement_function(self) -> None:
        """The callback itself is escape-safe when fed to re.sub directly."""
        repl = replacement_function(lambda name: r"C:\x\s \1")
        assert re.sub(r"\{\{(V)\}\}", repl, "p {{V}}") == f"p {r'C:\x\s \1'}"


class TestConstantLookup:
    """Loop-path lookup: every name resolves to str(value)."""

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("text", "text"),
            (None, "None"),
            (0, "0"),
            (False, "False"),
            (r"C:\x\s", r"C:\x\s"),
            ([1, 2], "[1, 2]"),
        ],
    )
    def test_renders_str_of_value_for_any_name(self, value, expected: str) -> None:
        """str(value) is emitted verbatim, including for None (loop quirk)."""
        lookup = constant_lookup(value)
        assert lookup("anything") == expected
