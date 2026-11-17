"""Schema tests for the ``artifact-locations`` matrix section (Issue #1186, AC-01).

SPEC-1186-artifact-locations-matrix §4.1 contract:

- ``artifact-locations`` is an optional root section with a closed object shape
  (``additionalProperties: false`` on every object level).
- Eight shared ``$defs`` implement the class forms: ``artifactKind``,
  ``artifactClassName``, ``artifactNaming``, ``artifactClass``, ``artifactSeClass``,
  ``artifactFileSet``, ``artifactEphemeral``, ``artifactState``.
- ``kind`` is an array of the closed ``artifactKind`` enum with ``uniqueItems: true``
  (a scalar is invalid). ``fallback-parent`` is a class-name enum. ``naming`` is the
  shared closed-token pattern.
- Paths reject absolute values and ``..``; SE ``subdir`` is a single segment;
  ``project-docs`` requires ``files``; ephemeral classes have no ``mode``.

Test style follows ``tests/test_context_topology_schema.py`` (importorskip).
Run: python -m pytest tests/test_artifact_locations_schema.py -q
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _config(**extra) -> dict:
    base = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
    }
    base.update(extra)
    return base


def _section(**body) -> dict:
    """Wrap ``body`` in a minimal artifact-locations root section."""
    return {"artifact-locations": body}


def test_section_accepts_minimal_entry():
    jsonschema.validate(_config(**_section(enabled=True)), _schema())


def test_unknown_section_subkey_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(**_section(bogus=1)), _schema())


def test_unknown_defaults_subkey_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(**_section(defaults={"bogus": 1})), _schema())


def test_unknown_class_subkey_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**_section(classes={"specs": {"bogus": 1}})), _schema()
        )


def test_mode_enum_rejects_unknown_value():
    for value in ("files", "inline", "off"):
        jsonschema.validate(
            _config(**_section(classes={"specs": {"mode": value}})), _schema()
        )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**_section(classes={"specs": {"mode": "both"}})), _schema()
        )


def test_path_pattern_rejects_absolute_and_dotdot():
    for bad in ("/abs", "../x", "a/../../b", ""):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                _config(**_section(classes={"specs": {"path": bad}})), _schema()
            )
    jsonschema.validate(
        _config(**_section(classes={"specs": {"path": "docs/specs"}})), _schema()
    )


def test_se_class_subdir_is_single_segment():
    for good in ("", "validation"):
        jsonschema.validate(
            _config(
                **_section(classes={"se-validation": {"subdir": good}})
            ),
            _schema(),
        )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **_section(classes={"se-validation": {"subdir": "a/b"}})
            ),
            _schema(),
        )


def test_se_class_rejects_nested_subdir_key():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **_section(
                    classes={"se-validation": {"subdirs": {"logs": "x"}}}
                )
            ),
            _schema(),
        )


def test_project_docs_requires_files():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**_section(classes={"project-docs": {}})), _schema()
        )
    jsonschema.validate(
        _config(
            **_section(
                classes={
                    "project-docs": {"files": {"architecture": "docs/ARCHITECTURE.md"}}
                }
            )
        ),
        _schema(),
    )


def test_ephemeral_rejects_mode_key():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**_section(classes={"scratch": {"mode": "off"}})), _schema()
        )


def test_legacy_is_string_array():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(**_section(legacy=[1])), _schema())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(**_section(legacy="x")), _schema())
    jsonschema.validate(
        _config(**_section(legacy=["docs/conclusions/"])), _schema()
    )


def test_unmanaged_is_string_array():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(**_section(unmanaged=[1])), _schema())
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(**_section(unmanaged="x")), _schema())
    jsonschema.validate(
        _config(**_section(unmanaged=["docs/api/**"])), _schema()
    )


def test_kind_is_closed_enum():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**_section(classes={"reviews": {"kind": ["bogus"]}})), _schema()
        )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(**_section(classes={"reviews": {"kind": "code"}})), _schema()
        )
    jsonschema.validate(
        _config(
            **_section(classes={"reviews": {"kind": ["code", "concept"]}})
        ),
        _schema(),
    )


def test_fallback_parent_enum_rejects_unknown_class():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **_section(classes={"reviews": {"fallback-parent": "bogus"}})
            ),
            _schema(),
        )
    jsonschema.validate(
        _config(
            **_section(
                classes={"reviews": {"fallback-parent": "se-requirements"}}
            )
        ),
        _schema(),
    )


def test_fallback_parent_rejected_on_ephemeral():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **_section(classes={"scratch": {"fallback-parent": "reviews"}})
            ),
            _schema(),
        )


def test_project_docs_accepts_issue_labels():
    jsonschema.validate(
        _config(
            **_section(
                classes={
                    "project-docs": {
                        "files": {"issue-labels": "docs/issue-labels.md"}
                    }
                }
            )
        ),
        _schema(),
    )
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **_section(classes={"project-docs": {"files": {"bogus": "x"}}})
            ),
            _schema(),
        )


def test_naming_accepts_canonical_tokens():
    for value in (
        "{date}-{slug}.md",
        "ADR-{nnn}_{slug}.md",
        "{kind}-{date}-{slug}.md",
        "{date}-issue-{n}-{topic}-spike.md",
    ):
        jsonschema.validate(
            _config(**_section(classes={"specs": {"naming": value}})), _schema()
        )


def test_naming_rejects_unknown_token():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **_section(classes={"specs": {"naming": "{bogus}-{slug}.md"}})
            ),
            _schema(),
        )


def test_naming_rejects_path_separator_and_dotdot():
    for value in ("sub/{slug}.md", "../{slug}.md", ""):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                _config(**_section(classes={"specs": {"naming": value}})),
                _schema(),
            )


def test_naming_rejects_angle_bracket_form():
    # The <TOKEN> display form is documentation prose, not a config value.
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(
                **_section(
                    classes={"specs": {"naming": "<YYYY-MM-DD>-<slug>.md"}}
                )
            ),
            _schema(),
        )


def test_artifact_naming_def_is_shared():
    defs = _schema()["$defs"]
    pattern = defs["artifactNaming"]["pattern"]
    for token in (
        "class", "date", "slug", "kind", "n", "topic", "scope", "nnn",
        "level", "folder",
    ):
        assert token in pattern
    assert defs["artifactClass"]["properties"]["naming"] == {
        "$ref": "#/$defs/artifactNaming"
    }
    assert defs["artifactSeClass"]["properties"]["naming"] == {
        "$ref": "#/$defs/artifactNaming"
    }
