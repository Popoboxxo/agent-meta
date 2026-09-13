"""Schema tests for the spec/plan workflow config surface (F8). The
systems-engineering declaration is deliberately NOT covered -- it is the
out-of-scope follow-up F1."""
import copy
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


def test_dod_preset_enum_includes_concept_driven():
    schema = _schema()
    assert "concept-driven" in schema["properties"]["dod-preset"]["enum"]


def test_dod_properties_accept_spec_plan_flags():
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(
        _base_config(dod={"spec-plan-required": True, "spec-plan-traceability": False}),
        _schema(),
    )


def test_dod_rejects_unknown_spec_plan_key():
    jsonschema = pytest.importorskip("jsonschema")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_config(dod={"spec-plan-bogus": True}), _schema())


def test_full_preset_defines_both_keys():
    from lib.dod import load_dod_presets
    presets = load_dod_presets(REPO_ROOT)
    assert "spec-plan-required" in presets["full"]
    assert "spec-plan-traceability" in presets["full"]


def test_concept_driven_preset_requires_spec_plan():
    from lib.dod import load_dod_presets
    presets = load_dod_presets(REPO_ROOT)
    assert presets["concept-driven"]["spec-plan-required"] is True
    assert presets["concept-driven"]["spec-plan-traceability"] is False
