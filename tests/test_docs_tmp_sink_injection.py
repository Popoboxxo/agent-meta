"""Documentation guards for the tmp-sink injection (plan Task 17, AC-41).

The concept document must name the configuration key and the rendered token
instead of repeating a machine temp literal. The mandatory rule sentence stays
verbatim (Q11/ADR-16) — Task 21 switches the rule text itself to the token;
this module guards the configuration section, the example config and the
changelog entry.
"""

import re
from pathlib import Path

import yaml

from tests.changelog_sections import release_section

ROOT = Path(__file__).resolve().parent.parent
PRISON_MODE_DOC = ROOT / "docs" / "concepts" / "repo-containment-prison-mode.md"
PROJECT_YAML_EXAMPLE = ROOT / "templates" / "configs" / "project.yaml.example"
CHANGELOG = ROOT / "CHANGELOG.md"

#: The release that shipped the tmp-sink injection (SPEC-tmp-sink-injection).
_RELEASE = "2.0.0-beta.4"

MANDATORY_RULE = "Der pytest-Basetemp darf NIE im Arbeitsbaum liegen"


def _read(path):
    return path.read_text(encoding="utf-8")


def _section_5_5(text):
    """Return the body of section 5.5, up to the next heading of the same level."""
    match = re.search(
        r"^### 5\.5\b(?P<body>.*?)(?=^### 5\.6\b|^## 6\.)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    assert match, "section '### 5.5' is missing from the prison-mode document"
    return match.group("body")


def test_prison_mode_documents_temp_exception():
    """§5.5 names the config key and the token that carries the basetemp value."""
    section = _section_5_5(_read(PRISON_MODE_DOC))

    assert "system-temp-exception" in section
    assert "PYTEST_BASETEMP" in section


def test_prison_mode_keeps_mandatory_basetemp_rule():
    """Q11 is no content reversal: the mandatory rule sentence stays verbatim."""
    section = _section_5_5(_read(PRISON_MODE_DOC))

    assert MANDATORY_RULE in section


def test_prison_mode_section_uses_basetemp_variable():
    """AC-41: the rule text points at the token, not at a machine temp literal."""
    section = _section_5_5(_read(PRISON_MODE_DOC))

    assert "PYTEST_BASETEMP" in section
    assert "system-temp-exception" in section
    assert MANDATORY_RULE in section
    assert "--basetemp=/tmp" not in section


def test_project_yaml_example_documents_temp_exception():
    """The example config carries the opt-in exception with a documented reason."""
    text = _read(PROJECT_YAML_EXAMPLE)
    assert "system-temp-exception:" in text

    data = yaml.safe_load(text)
    exception = data["repo_containment"]["tmp-sink"]["system-temp-exception"]

    assert exception["enabled"] is True
    reason = exception["reason"]
    assert isinstance(reason, str) and reason.strip()
    assert exception["pytest-basetemp"] is True
    assert exception["toolchain-caches"] is False


def test_changelog_documents_tmp_sink_injection():
    """The release section of the shipped feature names the injected sink and the env/token pin."""
    text = _read(CHANGELOG)
    assert "## [Unreleased]" in text, "CHANGELOG.md must keep an [Unreleased] section."
    section = release_section(text, _RELEASE)
    assert section.startswith(f"## [{_RELEASE}]"), (
        f"CHANGELOG.md must carry a ## [{_RELEASE}] release section."
    )

    assert "tmp-sink" in section
    assert "PYTEST_BASETEMP" in section
    assert "SPEC-tmp-sink-injection" in section
