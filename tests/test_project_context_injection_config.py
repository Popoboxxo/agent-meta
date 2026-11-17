"""Tests for the project-context-injection config surface (issue #1187).

Shared across T1-T3 and T14. Test groups are kept clearly separated by
section comments so later tasks can append their own tests without touching
the schema tests below.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "config" / "project-config.schema.json"
sys.path.insert(0, str(REPO_ROOT / "scripts"))


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _base_config(**extra):
    cfg = {
        "project": {"name": "test", "prefix": "tst", "short": "test"},
        "platforms": [],
    }
    cfg.update(extra)
    return cfg


def _validator():
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft7Validator(_schema())


# ---------------------------------------------------------------------------
# T1 — schema section `project-context-injection`
# ---------------------------------------------------------------------------


def test_schema_section_accepts_all_four_modes():
    validator = _validator()
    for mode in ("all", "core+orchestrator", "core+whitelist", "core"):
        config = _base_config(**{
            "project-context-injection": {"mode": mode},
        })
        assert validator.is_valid(config), f"mode {mode!r} should be valid"


def test_schema_section_rejects_unknown_key():
    validator = _validator()
    config = _base_config(**{
        "project-context-injection": {"enabled": True},
    })
    assert not validator.is_valid(config)


def test_schema_section_rejects_duplicate_and_nonstring_whitelist():
    validator = _validator()
    for whitelist in (["developer", "developer"], [1]):
        config = _base_config(**{
            "project-context-injection": {"whitelist": whitelist},
        })
        assert not validator.is_valid(config), f"whitelist {whitelist!r} should be invalid"


def test_schema_defaults_are_mode_whitelist_orchestrator_pointer_language():
    props = _schema()["properties"]["project-context-injection"]["properties"]
    assert props["mode"]["default"] == "all"
    assert props["whitelist"]["default"] == []
    assert props["orchestrator"]["default"] == "inherit"
    assert props["pointer-language"]["default"] == "en"


def test_schema_orchestrator_roles_and_pointer_text_have_no_default():
    props = _schema()["properties"]["project-context-injection"]["properties"]
    assert "default" not in props["orchestrator-roles"]
    assert "default" not in props["pointer-text"]


def test_schema_section_accepts_orchestrator_roles_and_pointer_settings():
    validator = _validator()
    valid = _base_config(**{
        "project-context-injection": {
            "orchestrator-roles": ["orchestrator", "senior-developer"],
            "pointer-language": "de",
            "pointer-text": "Projektkontext: lies `{context_file}`.",
        },
    })
    assert validator.is_valid(valid)
    for roles in (["senior-developer", "senior-developer"], [1]):
        invalid = _base_config(**{
            "project-context-injection": {"orchestrator-roles": roles},
        })
        assert not validator.is_valid(invalid), f"roles {roles!r} should be invalid"


def test_schema_rejects_unknown_pointer_language_and_empty_pointer_text():
    validator = _validator()
    for section in (
        {"pointer-language": "fr"},
        {"pointer-text": ""},
    ):
        config = _base_config(**{"project-context-injection": section})
        assert not validator.is_valid(config), f"section {section!r} should be invalid"
