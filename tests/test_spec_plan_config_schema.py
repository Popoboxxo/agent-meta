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


def test_spec_plan_workflow_block_valid():
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(
        _base_config(**{
            "spec-plan-workflow": {
                "enabled": True,
                "paths": {
                    "specs": "docs/specs",
                    "plans": "docs/plans",
                    "spikes": "docs/spikes",
                    "legacy": ["docs/superpowers/specs", "docs/superpowers/plans"],
                },
                "scan": {"include": ["*.md"], "changed-files-only": True},
                "index": {"mode": "file-index", "fallback-index": "docs/INDEX.md"},
                "archive": {
                    "mode": "ask", "agent": "documenter",
                    "trigger": "plan-complete", "target": "docs/plans/archive",
                },
                "external-system-override": {"enabled": False, "system": "", "note": ""},
            }
        }),
        _schema(),
    )


@pytest.mark.parametrize(
    "block",
    [
        {"bogus": 1},
        {"paths": {"bogus": 1}},
        {"scan": {"bogus": 1}},
        {"index": {"bogus": 1}},
        {"archive": {"bogus": 1}},
        {"external-system-override": {"bogus": 1}},
    ],
    ids=["top-level", "paths", "scan", "index", "archive", "external-system-override"],
)
def test_spec_plan_workflow_block_rejects_unknown_key(block):
    jsonschema = pytest.importorskip("jsonschema")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_config(**{"spec-plan-workflow": block}), _schema())


def test_spec_plan_workflow_has_no_schema_default():
    block = _schema()["properties"]["spec-plan-workflow"]
    assert "default" not in block
    assert "default" not in block["properties"]["enabled"]


def _iter_defaults(node):
    """Yield every ``default`` value found recursively in a schema node."""
    if isinstance(node, dict):
        if "default" in node:
            yield node["default"]
        for value in node.values():
            yield from _iter_defaults(value)
    elif isinstance(node, list):
        for item in node:
            yield from _iter_defaults(item)


def test_spec_plan_workflow_defaults_contain_no_legacy_path():
    """Design-Addendum §D.3: no schema default may point at a legacy path."""
    block = _schema()["properties"]["spec-plan-workflow"]
    defaults = list(_iter_defaults(block))
    assert defaults, "expected at least one default in the spec-plan-workflow block"
    offending = [d for d in defaults if "docs/superpowers" in json.dumps(d)]
    assert offending == [], f"legacy path in schema default(s): {offending}"


def test_project_structure_lists_spec_plan_paths():
    from lib.io import _load_yaml_or_json
    data, _ = _load_yaml_or_json(REPO_ROOT / ".meta-config" / "project.yaml")
    structure = data["variables"]["PROJECT_STRUCTURE"]
    assert "docs/specs/" in structure
    assert "docs/plans/" in structure
    assert "docs/spikes/" in structure


def test_recovery_and_ledger_drift_accepted():
    """AC-25/IC-09: the recovery and ledger-drift declaration keys are accepted."""
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(
        _base_config(**{
            "spec-plan-workflow": {
                "recovery": {
                    "rehydrate": True,
                    "max-age-seconds": 3600,
                    "include-legacy": False,
                },
                "ledger-drift": {"enabled": True, "severity": "WARNING"},
            }
        }),
        _schema(),
    )


def test_unknown_recovery_key_rejected():
    """The recovery object stays a strict typo guard (F7)."""
    jsonschema = pytest.importorskip("jsonschema")
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config(**{
                "spec-plan-workflow": {"recovery": {"rehydrate": True, "bogus": 1}}
            }),
            _schema(),
        )


def test_root_cause_required_accepted():
    """AC-25: the resolved dod object accepts the root-cause-required flag."""
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(_base_config(dod={"root-cause-required": True}), _schema())
    jsonschema.validate(_base_config(dod={"root-cause-required": False}), _schema())


def test_task_review_max_rounds_accepted():
    """IC-08/IC-09: the pipeline override schema declares task-review.max-rounds."""
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(
        _base_config(**{
            "quality-pipelines": {
                "overrides": {
                    "concept-driven-dev": {"task-review": {"max-rounds": 4}}
                }
            }
        }),
        _schema(),
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config(**{
                "quality-pipelines": {
                    "overrides": {
                        "concept-driven-dev": {"task-review": {"max-rounds": 0}}
                    }
                }
            }),
            _schema(),
        )


def test_condition_payload_flag_accepted():
    """AC-25: stageItem.condition declares the consumed dod_flag/payload_flag keys."""
    jsonschema = pytest.importorskip("jsonschema")
    jsonschema.validate(
        _base_config(**{
            "quality-pipelines": {
                "overrides": {
                    "demo-pipeline": {
                        "stages": [
                            {
                                "id": "scope",
                                "agent": "orchestrator",
                                "task": "Scope the feature",
                                "mode": "conditional",
                                "condition": {"payload_flag": "needs_scoping"},
                            },
                            {
                                "id": "tests",
                                "agent": "tester",
                                "task": "Write tests",
                                "mode": "conditional",
                                "condition": {"dod_flag": "tests-required"},
                            },
                        ]
                    }
                }
            }
        }),
        _schema(),
    )
