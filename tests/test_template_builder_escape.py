"""TemplateBuilder behavior-alignment tests (issue #476 Phase 1).

Engine 2 (TemplateBuilder.resolve_variables) gains three behaviors Engine 1
(scripts/lib/variables.py::substitute) already had: {{%VAR%}} escape syntax,
PAL_* prefix exemption, and an optional missing-variable warning.
"""
from pathlib import Path

from scripts.lib.context_templates.builder import TemplateBuilder


def test_escape_syntax_renders_literal_without_substitution():
    builder = TemplateBuilder(Path("."))
    assert builder.resolve_variables("{{%FOO%}}", {"FOO": "x"}) == "{{FOO}}"


def test_pal_prefix_passes_through_untouched_without_warning():
    class LogStub:
        def __init__(self):
            self.calls = []

        def warn(self, message):
            self.calls.append(message)

    log = LogStub()
    builder = TemplateBuilder(Path("."), log=log)
    rendered = builder.resolve_variables("{{PAL_X}}", {"PAL_X": "should-not-be-used"})

    assert rendered == "{{PAL_X}}"
    assert log.calls == []


def test_missing_variable_warns_exactly_once_when_log_given():
    class LogStub:
        def __init__(self):
            self.calls = []

        def warn(self, message):
            self.calls.append(message)

    log = LogStub()
    builder = TemplateBuilder(Path("."), log=log)
    rendered = builder.resolve_variables("a {{MISSING}} b", {})

    assert rendered == "a {{MISSING}} b"
    assert len(log.calls) == 1
    assert "MISSING" in log.calls[0]


def test_missing_variable_stays_silent_without_log():
    """Backward compat: no log -> no warning (default for all existing call sites)."""
    builder = TemplateBuilder(Path("."))
    assert builder.resolve_variables("a {{MISSING}} b", {}) == "a {{MISSING}} b"
