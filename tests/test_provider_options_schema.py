"""Schema tests for the ``provider-options`` frontmatter strip/keep keys.

SPEC-REFERENCE-STANDARDS-2026-09-15 (IC-05, R6/F-03):

- ``provider-options.<Provider>.frontmatter-keep-fields`` and
  ``...frontmatter-strip-fields`` are modelled as ``array[string]`` in every
  modelled provider block (Claude, Gemini, Continue, Opencode, Mammouth).
- ``frontmatter-keep-fields`` wins over strip (resolver semantics, IC-03).
- Both keys are optional: their absence stays valid.
- Each provider block keeps ``additionalProperties: false`` — unknown option
  keys are still rejected (R6).

Run: python -m pytest tests/test_provider_options_schema.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"

_MODELLED_PROVIDERS = ("Claude", "Gemini", "Continue", "Opencode", "Mammouth")
_NEW_KEYS = ("frontmatter-keep-fields", "frontmatter-strip-fields")


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _provider_options_schema() -> dict:
    return _schema()["properties"]["provider-options"]


def _config(**extra) -> dict:
    base = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
    }
    base.update(extra)
    return base


def test_keep_and_strip_fields_modelled_for_every_modelled_provider():
    props = _provider_options_schema()["properties"]
    for provider in _MODELLED_PROVIDERS:
        assert provider in props, provider
        sub = props[provider]["properties"]
        for key in _NEW_KEYS:
            assert key in sub, f"{provider}.{key} missing"
            assert sub[key]["type"] == "array"
            assert sub[key]["items"]["type"] == "string"
        assert props[provider]["additionalProperties"] is False


def test_absence_of_both_keys_remains_valid():
    jsonschema.validate(_config(), _schema())


def test_keep_and_strip_arrays_accepted():
    options = {
        provider: {
            "frontmatter-keep-fields": ["reference_standards"],
            "frontmatter-strip-fields": ["version"],
        }
        for provider in _MODELLED_PROVIDERS
    }
    jsonschema.validate(_config(**{"provider-options": options}), _schema())


def test_unknown_provider_option_key_still_rejected():
    for provider in _MODELLED_PROVIDERS:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                _config(**{"provider-options": {provider: {"bogus": 1}}}),
                _schema(),
            )


def test_non_array_keep_fields_rejected():
    for provider in _MODELLED_PROVIDERS:
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                _config(
                    **{
                        "provider-options": {
                            provider: {"frontmatter-keep-fields": "reference_standards"}
                        }
                    }
                ),
                _schema(),
            )
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(
                _config(
                    **{
                        "provider-options": {
                            provider: {"frontmatter-strip-fields": ["version", 1]}
                        }
                    }
                ),
                _schema(),
            )
