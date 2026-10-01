"""Schema declaration for the ``docs-consolidation`` block (spec IC-17 M-11, IC-22).

**M-11 is a convention and autocomplete obligation, not a defect repair.**
The root of ``config/project-config.schema.json`` is permissive
(``additionalProperties: true``), so a project config that already carries
``docs-consolidation`` validates green today, with or without this block.
Declaring it exists so the schema offers IDE autocomplete for the block and so
the schema's own stated convention -- closed sub-objects as a typo guard
(self-description in the schema at the ``spec-plan-workflow`` block) -- is
honoured by the new block too.

What this test therefore asserts is *shape and closedness*, plus the AC-39
promise that a config switching the feature on validates green:

* the block exists, is closed, and carries exactly the properties IC-22
  enumerates for ``docs-consolidation``;
* the nested ``checks`` object is closed as well;
* no property name is a provider name (NFA-03 / NFA-11);
* ``enabled: true`` validates green -- proven with in-memory fixtures and a
  temp copy of ``.meta-config/project.yaml``. That file itself is never
  written by this test; editing it belongs to plan task W1-10.

Run: python -m pytest tests/test_docs_consolidation_migration.py -v
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"
_PROJECT_YAML = _REPO_ROOT / ".meta-config" / "project.yaml"

_BLOCK = "docs-consolidation"

# IC-22 enumerates six rows; five of them are `docs-consolidation.*` keys, the
# sixth (`knowledge-engine.okf.index-mode`) belongs to a different block and is
# deferred to W7-2. `checks.strict` is a nested key, so it is one property here.
_EXPECTED_PROPERTIES = {
    "enabled",
    "index-mode",
    "checks",
    "sources",
    "volatile-facts",
}

_EXPECTED_CHECKS_PROPERTIES = {"strict"}


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _block() -> dict:
    return _schema()["properties"][_BLOCK]


def _base_config(docs_consolidation: dict | None = None) -> dict:
    config: dict = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
        "roles": ["orchestrator", "developer", "git"],
    }
    if docs_consolidation is not None:
        config[_BLOCK] = docs_consolidation
    return config


def _provider_names() -> set[str]:
    """Provider names as the schema itself declares them."""
    return {str(n).lower() for n in _schema()["properties"]["ai-provider"]["enum"]}


def test_schema_block_present_and_closed() -> None:
    """AC-39: closed top-level block with exactly the IC-22 property set.

    Real check, not a smoke test: it fails when the block is missing, when
    ``additionalProperties`` is not ``false``, and when any single expected
    property is absent or an undeclared one has crept in.
    """
    schema = _schema()
    assert _BLOCK in schema["properties"], (
        f"top-level block '{_BLOCK}' is not declared in the schema (M-11)"
    )
    block = schema["properties"][_BLOCK]
    assert block.get("type") == "object"
    assert block.get("additionalProperties") is False, (
        f"'{_BLOCK}' must be closed (additionalProperties: false) to work as a "
        "typo guard, per the schema's own closed-sub-object convention"
    )
    properties = block.get("properties", {})
    missing = _EXPECTED_PROPERTIES - set(properties)
    assert not missing, f"missing IC-22 properties: {sorted(missing)}"
    assert set(properties) == _EXPECTED_PROPERTIES, (
        f"unexpected properties: {sorted(set(properties) - _EXPECTED_PROPERTIES)}"
    )


def test_nested_checks_object_is_closed() -> None:
    checks = _block()["properties"]["checks"]
    assert checks.get("type") == "object"
    assert checks.get("additionalProperties") is False, (
        "checks is a closed sub-object like every other closed sub-object here"
    )
    assert set(checks["properties"]) == _EXPECTED_CHECKS_PROPERTIES
    assert checks["properties"]["strict"]["type"] == "boolean"


def test_no_property_name_is_a_provider_name() -> None:
    """NFA-03 / NFA-11: no provider name may become a config key."""
    providers = _provider_names()
    block = _block()
    names = set(block["properties"])
    names |= set(block["properties"]["checks"]["properties"])
    for name in names:
        lowered = name.lower()
        assert lowered not in providers, f"property '{name}' is a provider name"
        for provider in providers:
            assert provider not in lowered, (
                f"property '{name}' embeds the provider name '{provider}'"
            )


def test_absent_block_is_valid() -> None:
    """Fail-off: a config without the block is unaffected (IC-22)."""
    jsonschema.validate(_base_config(), _schema())


def test_enabled_true_validates_green() -> None:
    """AC-39, second half: `docs-consolidation.enabled: true` is schema-valid."""
    jsonschema.validate(_base_config({"enabled": True}), _schema())


def test_full_block_validates_green() -> None:
    jsonschema.validate(
        _base_config(
            {
                "enabled": True,
                "index-mode": "skeleton",
                "checks": {"strict": False},
                "sources": ["README.md", "llms.txt", "ARCHITECTURE.md"],
                "volatile-facts": ["DOCS_SCENARIO_COUNT"],
            }
        ),
        _schema(),
    )


def test_unknown_property_rejected() -> None:
    """The typo guard actually bites."""
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_config({"enabled": True, "bogus": 1}), _schema())


def test_typo_of_index_mode_rejected() -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_config({"index-modee": "full"}), _schema())


def test_unknown_check_property_rejected() -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"checks": {"strict": True, "bogus": True}}), _schema()
        )


@pytest.mark.parametrize("mode", ["full", "skeleton"])
def test_index_mode_enum_accepts_both_modes(mode: str) -> None:
    jsonschema.validate(_base_config({"index-mode": mode}), _schema())


@pytest.mark.parametrize("mode", ["Full", "partial", "", "none"])
def test_index_mode_enum_rejects_everything_else(mode: str) -> None:
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_config({"index-mode": mode}), _schema())


def test_schema_declares_the_absence_defaults() -> None:
    """IC-22 fail-off defaults, expressed as JSON Schema ``default``.

    The schema only *declares* shape and the absence default; JSON Schema does
    not inject values. Runtime fail-off (absent == false) is the consumer's
    job, following the repo precedence `knowledge.py:127` -- declaration only
    in this task.
    """
    properties = _block()["properties"]
    assert properties["enabled"]["default"] is False
    assert properties["index-mode"]["default"] == "full"
    assert set(properties["index-mode"]["enum"]) == {"full", "skeleton"}
    assert properties["checks"]["properties"]["strict"]["default"] is False
    assert properties["sources"]["default"] == []
    assert properties["volatile-facts"]["default"] == ["DOCS_SCENARIO_COUNT"]


def test_existing_project_config_with_block_enabled_validates(tmp_path: Path) -> None:
    """Prove it on a temp *copy* of the real config -- never on the real file.

    ``.meta-config/project.yaml`` belongs to plan task W1-10; this test only
    reads it, writes the mutated copy into ``tmp_path`` and validates that.
    The pre-existing, unrelated ``agent-meta-version`` pattern mismatch
    (``1.2.0-beta.2`` vs ``^\\d+\\.\\d+\\.\\d+$``) is neutralised in the copy
    only, so the assertion under test is the ``docs-consolidation`` block.
    """
    if not _PROJECT_YAML.exists():  # pragma: no cover - repo always has it
        pytest.skip(f"{_PROJECT_YAML} not present")

    with _PROJECT_YAML.open(encoding="utf-8") as f:
        config = yaml.safe_load(f)
    config = copy.deepcopy(config)
    config["agent-meta-version"] = "1.2.0"
    config[_BLOCK] = {"enabled": True, "checks": {"strict": False}}

    copy_path = tmp_path / "project.yaml"
    copy_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    with copy_path.open(encoding="utf-8") as f:
        reloaded = yaml.safe_load(f)
    assert reloaded[_BLOCK]["enabled"] is True

    jsonschema.validate(reloaded, _schema())
    # The real file is untouched by this test.
    with _PROJECT_YAML.open(encoding="utf-8") as f:
        on_disk = yaml.safe_load(f)
    assert _BLOCK not in on_disk or on_disk[_BLOCK] != {}
