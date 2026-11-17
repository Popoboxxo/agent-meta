"""Resolver-core tests for the ``artifact-locations`` matrix (Issue #1186, T4).

SPEC-1186-artifact-locations-matrix §3.3 / §3.2.1 / §3.6 and D1/D3/D4:

- four value sources with field-wise ``source``/``field_sources`` attribution,
- 23 registered classes (14 non-SE + 9 SE), ``unmanaged`` is not a class,
- per-cell SE path resolution without inventing a cell hierarchy,
- derived SE projections, class-scoped ``kind`` enums and naming tokens,
- scratch has a single source (``classes.scratch.path``); the containment key is
  a migration alias with attribution, never a second source.

Run: export PYTEST_BASETEMP=.tmp/pytest-1186-t4
     python3 -m pytest tests/test_artifact_locations_resolver.py --basetemp="$PYTEST_BASETEMP" -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.artifact_locations import (  # noqa: E402
    CLASS_REGISTRY,
    ArtifactLocationsError,
    artifact_file_stats,
    resolve_artifact_cell_path,
    resolve_artifact_locations,
    resolve_artifact_naming,
    resolve_scratch_path,
    resolve_se_projection,
)

_AM_ROOT = _REPO_ROOT


def _resolve(section=None, **extra):
    """Resolve with the real preset file from the repository root."""
    config = {} if section is None else {"artifact-locations": section}
    config.update(extra)
    return resolve_artifact_locations(config, _AM_ROOT, _REPO_ROOT)


# ---------------------------------------------------------------------------
# Registry, precedence and value sources (§3.3)
# ---------------------------------------------------------------------------


def test_class_registry_has_23_entries():
    """AC-12: 14 non-SE (12 persistent + 2 ephemeral) + 9 SE classes."""
    assert len(CLASS_REGISTRY) == 23
    non_se = [name for name in CLASS_REGISTRY if not name.startswith("se-")]
    se = [name for name in CLASS_REGISTRY if name.startswith("se-")]
    assert len(non_se) == 14
    assert len(se) == 9
    assert set(non_se) == {
        "specs", "plans", "concepts", "spikes", "reviews", "audits", "analysis",
        "reports", "adr", "traceability", "runbooks", "project-docs", "scratch",
        "state",
    }


def test_precedence_project_beats_preset():
    """Rule 1: a project key wins over the preset, never silently loses."""
    matrix = _resolve({"classes": {"reviews": {"path": "project/reviews"}}})
    reviews = matrix.classes["reviews"]
    assert reviews.path == "project/reviews"
    assert reviews.source == "project"


def test_precedence_is_fieldwise():
    """Rule 1: precedence is per field, not per class."""
    matrix = _resolve({"classes": {"reviews": {"path": "project/reviews"}}})
    reviews = matrix.classes["reviews"]
    assert reviews.field_sources["path"] == "project"
    assert reviews.field_sources["mode"] == "preset:default"


def test_project_defaults_beat_preset_defaults():
    """Rule 2: project defaults are field inheritance inside the project source."""
    matrix = _resolve({"defaults": {"naming": "{class}.md"}, "classes": {"specs": {}}})
    specs = matrix.classes["specs"]
    assert specs.naming == "{class}.md"
    assert specs.field_sources["naming"] == "project"


def test_missing_field_falls_to_schema_default():
    """Rule 3: an empty section yields framework defaults, fully attributed."""
    matrix = _resolve({})
    specs = matrix.classes["specs"]
    assert specs.path == "docs/specs"
    assert specs.mode == "files"
    assert specs.source == "schema-default"
    assert specs.field_sources["path"] == "schema-default"


def test_project_preset_is_attribution_not_a_level():
    """K3: project-preset:<name> is attribution on the preset source, not a 5th source."""
    matrix = _resolve({"preset": "minimal"})
    concepts = matrix.classes["concepts"]
    assert matrix.preset == "minimal"
    assert concepts.mode == "inline"
    assert concepts.field_sources["mode"] == "project-preset:minimal"
    assert concepts.source == "project-preset:minimal"


def test_code_fallback_is_reported(tmp_path):
    """Rule 3: no preset data means values come from code and say so."""
    config = {"artifact-locations": {}}
    matrix = resolve_artifact_locations(config, tmp_path, _REPO_ROOT)
    audits = matrix.classes["audits"]
    assert audits.path == "docs/audits"
    assert audits.source == "code-fallback"
    assert audits.field_sources["path"] == "code-fallback"


def test_enabled_false_returns_disabled_source():
    """Rule 5: disabled = today's paths with no redirection, every source 'disabled'."""
    matrix = _resolve({"enabled": False})
    assert matrix.enabled is False
    assert matrix.classes
    assert all(cls.source == "disabled" for cls in matrix.classes.values())
    assert all(
        field_source == "disabled"
        for cls in matrix.classes.values()
        for field_source in cls.field_sources.values()
    )
    assert matrix.classes["specs"].path == "docs/specs"


def test_unknown_preset_raises():
    """§4.1: an undeclared preset is a hard error, never a silent fallback."""
    with pytest.raises(ArtifactLocationsError) as exc:
        _resolve({"preset": "unknown-preset"})
    assert exc.value.code == "artifact-locations.unknown-preset"
    assert "unknown-preset" in str(exc.value)


def test_legacy_is_additive():
    """Rule 4: a project extends the framework legacy list but cannot remove entries."""
    matrix = _resolve({"legacy": ["docs/custom/"]})
    assert "docs/custom/" in matrix.legacy
    assert "docs/conclusions/" in matrix.legacy
    assert "docs/se/**" in matrix.legacy


# ---------------------------------------------------------------------------
# SE cells, projections and kind scoping (§3.2 / D4 / D-7)
# ---------------------------------------------------------------------------


def test_se_validation_and_se_requirements_resolve_per_cell():
    """AC-10: two SE classes in the same cell keep their distinct configured roots."""
    matrix = _resolve({"classes": {
        "se-validation": {"path": "external-evidence"},
        "se-requirements": {"path": "SE"},
    }})
    p_val = resolve_artifact_cell_path(
        "se-validation", 3, "Steuerung", False, matrix=matrix,
    )
    p_req = resolve_artifact_cell_path(
        "se-requirements", 3, "Steuerung", False, matrix=matrix,
    )
    assert p_val.startswith("external-evidence/")
    assert p_val.endswith("/validation/L3_Steuerung_Validation.md")
    assert p_req.startswith("SE/")
    assert p_req.endswith("/L3_Steuerung_Requirements.md")
    assert p_val != p_req


def test_reports_vv_alias():
    """D-7: vv is a reports kind, SE/VV/** remains legacy (not a 24th class)."""
    matrix = _resolve({})
    assert "vv" in matrix.classes["reports"].kinds
    assert "SE/VV/**" in matrix.legacy


def test_reports_path_stays_docs_reports():
    """AC-04 + D-7: reports.path is static; SE paths are derived projections."""
    matrix = _resolve({})
    assert matrix.classes["reports"].path == "docs/reports"
    assert resolve_se_projection("se-reports") == "SE/reports"
    assert resolve_se_projection("se-reviews") == "SE/reviews"


def test_se_projection_is_derived_not_configured():
    """RVW-1186-05: projections follow SE root only, never a cell class path."""
    before = resolve_se_projection("se-reports")
    matrix = _resolve({"classes": {"se-validation": {"path": "external-evidence"}}})
    after = resolve_se_projection("se-reports", matrix=matrix)
    assert before == after == "SE/reports"
    assert resolve_se_projection("se-adr") == "SE/ADR"
    assert resolve_se_projection("se-traceability") == "SE/traceability"


def test_kind_enum_is_class_scoped():
    """AC-13: kind enums belong to four classes only; elsewhere they are empty."""
    matrix = _resolve({})
    assert len(matrix.classes["reviews"].kinds) == 6
    assert len(matrix.classes["audits"].kinds) == 6
    assert len(matrix.classes["analysis"].kinds) == 7
    assert matrix.classes["reports"].kinds == ("vv",)
    for name, cls in matrix.classes.items():
        if name not in {"reviews", "audits", "analysis", "reports"}:
            assert cls.kinds == (), name
    with pytest.raises(ArtifactLocationsError) as exc:
        resolve_artifact_naming(
            matrix, "reviews", kind="bogus", date="2026-11-09", slug="x",
        )
    assert exc.value.code == "artifact-locations.kind-invalid"


def test_fallback_parent_is_exposed():
    """RVW-1186-04: fallback-parent is reported, validation is T5's job."""
    matrix = _resolve({"classes": {
        "reviews": {"mode": "off", "fallback-parent": "se-requirements"},
    }})
    assert matrix.classes["reviews"].fallback_parent == "se-requirements"
    assert _resolve({}).classes["reviews"].fallback_parent is None


def test_conclusions_is_legacy_not_class():
    """D-6: conclusions is a legacy target directory, not a 15th non-SE class."""
    matrix = _resolve({})
    assert "conclusions" not in matrix.classes
    assert "docs/conclusions/" in matrix.legacy


# ---------------------------------------------------------------------------
# Scratch single source (D1) and state projection
# ---------------------------------------------------------------------------


def test_scratch_path_is_single_source():
    """D1: classes.scratch.path is the only source when it is present."""
    matrix = _resolve({"classes": {"scratch": {"path": "custom-scratch"}}})
    scratch = matrix.classes["scratch"]
    assert scratch.path == "custom-scratch"
    assert scratch.source == "project"
    assert scratch.field_sources["path"] == "project"


def test_scratch_alias_applies_only_when_class_absent():
    """D1: the containment key is read only while classes.scratch is absent."""
    matrix = _resolve({"classes": {}}, repo_containment={"tmp-sink": {"path": "legacy-sink"}})
    scratch = matrix.classes["scratch"]
    assert scratch.path == "legacy-sink"
    assert scratch.source == "project"
    assert scratch.field_sources["path"] == "project-alias:repo_containment.tmp-sink.path"
    # The standalone helper returns the same path and attribution.
    assert resolve_scratch_path(
        {"repo_containment": {"tmp-sink": {"path": "legacy-sink"}}}, {},
    ) == ("legacy-sink", "project-alias:repo_containment.tmp-sink.path")


def test_scratch_alias_equal_values_are_resolved():
    """D1: both keys set to the same value is allowed; the alias stays visible."""
    matrix = _resolve(
        {"classes": {"scratch": {"path": "same"}}},
        repo_containment={"tmp-sink": {"path": "same"}},
    )
    scratch = matrix.classes["scratch"]
    assert scratch.path == "same"
    assert scratch.field_sources["path"] == "project"
    assert scratch.field_sources["path-alias"] == "project-alias:repo_containment.tmp-sink.path"


def test_se_root_default_is_SE():
    """D4: all nine SE classes default to SE, never to docs/se."""
    matrix = _resolve({})
    se_classes = [cls for name, cls in matrix.classes.items() if name.startswith("se-")]
    assert len(se_classes) == 9
    assert all(cls.path == "SE" for cls in se_classes)
    assert all("docs/se" not in cls.path for cls in se_classes)


def test_state_projects_progress_and_event_log():
    """Spec §3.6: state is a projection of progress.* and viz.event_log."""
    matrix = _resolve(
        {"classes": {}},
        progress={"dir": "custom/progress", "checkpoint-dir": "custom/checkpoints"},
        viz={"event_log": "custom/events.jsonl"},
    )
    state = matrix.classes["state"]
    assert state.subdirs["progress"] == "custom/progress"
    assert state.subdirs["checkpoints"] == "custom/checkpoints"
    assert state.event_log == "custom/events.jsonl"


def test_backup_siblings_excluded_from_counts():
    """#1195: *.sync-backup-* siblings never count as artifacts or as newest."""
    count, newest = artifact_file_stats([
        "a.md", "b.md", "a.md.sync-backup-2026-11-01", "c.sync-backup-x.md",
    ])
    assert count == 2
    assert newest == "b.md"


def test_unmanaged_is_not_a_class():
    """D-8: unmanaged[] is a negative declaration, additive, never a class."""
    matrix = _resolve({})
    assert "unmanaged" not in matrix.classes
    assert len(matrix.classes) == 23
    assert ".meta-config/issue-labels-state.json" in matrix.unmanaged

    extended = _resolve({"unmanaged": ["docs/extra/**"]})
    assert "docs/extra/**" in extended.unmanaged
    assert ".meta-config/issue-labels-state.json" in extended.unmanaged


# ---------------------------------------------------------------------------
# Naming resolution (D3)
# ---------------------------------------------------------------------------


def test_naming_resolves_per_class():
    """D3: closed tokens resolve per class; {nnn} is 3-digit zero padded."""
    matrix = _resolve({})
    assert resolve_artifact_naming(matrix, "specs", date="2026-11-09", slug="x") == "2026-11-09-x.md"
    assert resolve_artifact_naming(matrix, "adr", n=7, slug="slug") == "ADR-007_slug.md"
    assert resolve_artifact_naming(
        matrix, "reviews", kind="code", date="2026-11-09", slug="x",
    ) == "code-2026-11-09-x.md"
    assert "L3_Steuerung_Validation.md" in resolve_artifact_naming(
        matrix, "se-validation", level=3, folder="Steuerung",
    )


def test_naming_unknown_token_raises():
    """D3: an unknown token is a hard naming-invalid error."""
    with pytest.raises(ArtifactLocationsError) as exc:
        _resolve({"classes": {"specs": {"naming": "{bogus}"}}})
    assert exc.value.code == "artifact-locations.naming-invalid"
    assert "{bogus}" in str(exc.value)


def test_naming_is_reported_per_class():
    """D3: each path-bearing persistent class carries its default naming."""
    matrix = _resolve({})
    persistent = [
        "specs", "plans", "concepts", "spikes", "reviews", "audits", "analysis",
        "reports", "adr", "traceability", "runbooks",
    ]
    assert all(matrix.classes[name].naming == CLASS_REGISTRY[name].naming for name in persistent)
    for name in ("project-docs", "scratch", "state"):
        assert matrix.classes[name].naming is None


def test_legacy_accepts_adr_non_canonical_forms():
    """D3/D4: both non-canonical ADR forms and docs/se/** stay legacy globs."""
    matrix = _resolve({})
    legacy = set(matrix.legacy)
    assert "docs/adr/[0-9][0-9][0-9][0-9]-*.md" in legacy
    assert "docs/adr/ADR-[0-9][0-9][0-9]-*.md" in legacy
    assert "docs/se/**" in legacy
