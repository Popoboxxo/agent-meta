"""Preset data tests for the ``artifact-locations`` matrix (Issue #1186, AC-15).

SPEC-1186-artifact-locations-matrix §4.2 contract:

- ``config/artifact-locations-presets.yaml`` is data, not code, with top-level
  ``version: 1`` and exactly four presets: ``default``, ``minimal``, ``flat``,
  ``docs-only``.
- ``default`` is the full matrix from §3.2 (14 non-SE + 9 SE classes), including
  the framework ``legacy[]`` and ``unmanaged[]`` lists.
- The three alternative presets only restate deviations, never a full copy of
  the default.
- Every field used in a preset is declared in the T1 schema (root section
  properties and the eight shared ``$defs``); ``naming`` values use only the
  closed token canon from §3.2.1 (D3).

Run: python3 -m pytest tests/test_artifact_locations_presets.py -q
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.io import load_yaml_file  # noqa: E402

_PRESET_PATH = _REPO_ROOT / "config" / "artifact-locations-presets.yaml"
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"

_PRESET_NAMES = {"default", "minimal", "flat", "docs-only"}
_NAMING_TOKENS = {
    "class", "date", "slug", "kind", "n", "topic", "scope", "nnn", "level", "folder",
}
_TOKEN_RE = re.compile(r"\{([^{}]*)\}")

# SPEC §4.2 / §3.2: framework-owned legacy globs (read-only, additive).
_FRAMEWORK_LEGACY = {
    "docs/superpowers/specs",
    "docs/superpowers/plans",
    "docs/plans/audit-*.md",
    "docs/specs/*-review.md",
    "docs/conclusions/",
    "docs/estimates/",
    "docs/research/",
    ".meta-viz/handoffs/**",
    "SE/VV/**",
    "docs/se/**",
    "docs/adr/[0-9][0-9][0-9][0-9]-*.md",
    "docs/adr/ADR-[0-9][0-9][0-9]-*.md",
}
# SPEC §3.2a (D-8, RVW2-X-02): negative declarations, never classes.
_FRAMEWORK_UNMANAGED = {
    ".meta-config/issue-labels-state.json",
    "docs/api/**",
    "docs/howto/**",
    "docs/guides/**",
    "docs/testing/**",
    "docs/providers/**",
    "docs/issues/**",
    "docs/se-cascade/**",
}


def _payload() -> dict:
    return load_yaml_file(_PRESET_PATH, on_error="raise")


def _presets() -> dict:
    return _payload()["presets"]


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _section_schema() -> dict:
    return _schema()["properties"]["artifact-locations"]


def _field_count(preset: dict) -> int:
    """Number of explicitly set class fields (a rough 'deviation size')."""
    return sum(len(entry) for entry in preset["classes"].values())


def test_file_has_exactly_four_presets():
    """§4.2b: no silent fallback to an undeclared preset."""
    assert set(_presets()) == _PRESET_NAMES


def test_default_preset_covers_all_23_classes():
    """§3: 14 non-SE classes (12 persistent + 2 ephemeral) plus 9 SE classes."""
    declared = _section_schema()["properties"]["classes"]["properties"]
    classes = _presets()["default"]["classes"]

    assert set(classes) == set(declared)
    non_se = [name for name in classes if not name.startswith("se-")]
    se = [name for name in classes if name.startswith("se-")]
    assert len(non_se) == 14
    assert len(se) == 9
    assert len(classes) == 14 + 9

    assert "files" in classes["project-docs"]
    for ephemeral in ("scratch", "state"):
        assert ephemeral in classes
        # Ephemeral schema forms have no mode (T1 test_ephemeral_rejects_mode_key).
        assert "mode" not in classes[ephemeral]


def test_every_preset_field_exists_in_schema():
    """Data-level foreRunner of F-2: only schema-declared field names."""
    schema = _schema()
    section = _section_schema()
    section_props = section["properties"]
    class_props = section_props["classes"]["properties"]

    for preset_name, preset in _presets().items():
        assert set(preset) <= set(section_props), preset_name
        for class_name, entry in preset["classes"].items():
            assert class_name in class_props, f"{preset_name}.{class_name}"
            def_name = class_props[class_name]["$ref"].rsplit("/", 1)[-1]
            def_props = schema["$defs"][def_name]["properties"]
            assert set(entry) <= set(def_props), f"{preset_name}.{class_name}"
            if "files" in entry:
                file_props = def_props["files"]["properties"]
                assert set(entry["files"]) <= set(file_props), f"{preset_name}.{class_name}.files"
            if "kind" in entry:
                allowed_kinds = set(schema["$defs"]["artifactKind"]["enum"])
                assert set(entry["kind"]) <= allowed_kinds, f"{preset_name}.{class_name}.kind"


def test_preset_does_not_restate_defaults():
    """§4.2: minimal/flat/docs-only carry deviations only, never a full copy."""
    presets = _presets()
    baseline = _field_count(presets["default"])

    for name in ("minimal", "flat", "docs-only"):
        assert _field_count(presets[name]) < baseline, name
        for class_name, entry in presets[name]["classes"].items():
            assert not {"path", "naming", "git"} <= set(entry), f"{name}.{class_name}"


def test_legacy_contains_framework_paths():
    """§3.2/§4.2: all framework globs (incl. D3 ADR forms and D4 docs/se)."""
    presets = _presets()

    assert _FRAMEWORK_LEGACY <= set(presets["default"]["legacy"])
    # Rule (e): ADR legacy forms and docs/se/** live in every preset.
    inherited = {
        "docs/se/**",
        "docs/adr/[0-9][0-9][0-9][0-9]-*.md",
        "docs/adr/ADR-[0-9][0-9][0-9]-*.md",
    }
    for name, preset in presets.items():
        assert inherited <= set(preset["legacy"]), name


def test_default_adr_naming_is_canonical():
    """D3: one canonical ADR naming; the other two forms stay in legacy[]."""
    presets = _presets()

    assert presets["default"]["classes"]["adr"]["naming"] == "ADR-{nnn}_{slug}.md"
    legacy = set(presets["default"]["legacy"])
    assert "docs/adr/[0-9][0-9][0-9][0-9]-*.md" in legacy
    assert "docs/adr/ADR-[0-9][0-9][0-9]-*.md" in legacy
    # No preset silently promotes a hyphenated ADR-...-{slug} default.
    for name, preset in presets.items():
        adr_naming = preset["classes"].get("adr", {}).get("naming", "")
        assert "ADR-{nnn}-{slug}.md" != adr_naming, name


def test_every_preset_naming_uses_canonical_tokens():
    """§3.2.1 (D3): only closed-list tokens, no angle/display form."""
    for preset_name, preset in _presets().items():
        for class_name, entry in preset["classes"].items():
            naming = entry.get("naming")
            if naming is None:
                continue
            tokens = _TOKEN_RE.findall(naming)
            assert set(tokens) <= _NAMING_TOKENS, f"{preset_name}.{class_name}: {tokens}"
            assert "<" not in naming and ">" not in naming, f"{preset_name}.{class_name}"
            assert "/" not in naming and ".." not in naming, f"{preset_name}.{class_name}"
            assert naming.endswith(".md"), f"{preset_name}.{class_name}"


def test_default_unmanaged_contains_state_file():
    """D-8: negative declarations include #1188's state file, not issue-labels."""
    presets = _presets()

    for name, preset in presets.items():
        unmanaged = set(preset["unmanaged"])
        assert _FRAMEWORK_UNMANAGED <= unmanaged, name
        assert "docs/issue-labels.md" not in unmanaged, name


def test_preset_names_are_loadable_yaml():
    """§4.2: loadable YAML plus schema-conformant section data (T1 contract)."""
    jsonschema = pytest.importorskip("jsonschema")
    payload = _payload()

    assert set(payload) == {"version", "presets"}
    assert payload["version"] == 1

    schema = _schema()
    base = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
    }
    for name, preset in payload["presets"].items():
        try:
            jsonschema.validate({**base, "artifact-locations": preset}, schema)
        except jsonschema.ValidationError as exc:
            raise AssertionError(f"preset {name}: {exc.message}") from exc
