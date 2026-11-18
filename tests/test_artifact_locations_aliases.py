"""Alias/deprecation warning tests for the artifact-locations matrix (Issue #1186, T9).

Once ``artifact-locations.enabled`` is true the matrix is the single source;
legacy keys (``spec-plan-workflow.paths.*``, ``se_output.base_dir``,
``repo_containment.tmp-sink.path``, ``progress.*`` / ``viz.event_log``) are
deprecated aliases. Each divergence produces exactly one WARNING Finding,
drained once into ``build_variables``' pre-warning sink. With ``enabled: false``
the old keys stay the sole source and no warning is emitted. ``TMP_SINK_PATH``
is fed from ``ARTIFACT_SCRATCH_DIR`` (D1) — one resolver result, one source.

Run: export PYTEST_BASETEMP=.tmp/pytest-1186-t9
     python3 -m pytest tests/test_artifact_locations_aliases.py \
         --basetemp="$PYTEST_BASETEMP" -q
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import config as config_module  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.artifact_locations import (  # noqa: E402
    SOURCE_ALIAS,
    SOURCE_CODE_FALLBACK,
    SOURCE_PRESET_PREFIX,
    SOURCE_PROJECT,
    SOURCE_SCHEMA_DEFAULT,
    resolve_artifact_locations,
)
from lib.consistency.report import Severity  # noqa: E402

_AM_ROOT = _REPO_ROOT


def _warnings(config: dict) -> list:
    return config_module._artifact_deprecation_warnings(config, _AM_ROOT, None)


# --- 1. spec-plan-workflow.paths divergence warns once --------------------


def test_spec_plan_paths_divergence_warns_once():
    config = {
        "spec-plan-workflow": {"paths": {"specs": "docs/specs-old"}},
        "artifact-locations": {"enabled": True},
    }
    findings = _warnings(config)
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    text = findings[0].message
    assert "spec-plan-workflow.paths.specs" in text
    assert "artifact-locations.classes.specs.path" in text

    # The Finding is drained into build_variables' pre-warning sink once during
    # a real sync (a caller-supplied ActiveSet); static derivation stays silent.
    active_set = compute_active_set(config, _AM_ROOT, _AM_ROOT, warn_sink=[])
    _, unmapped = config_module.build_variables(
        config, _AM_ROOT, _AM_ROOT, active_set=active_set,
    )
    deprecations = [w for w in unmapped if "artifact-locations.deprecated-alias" in w]
    assert len(deprecations) == 1
    assert "artifact-locations.classes.specs.path" in deprecations[0]
    _, static_unmapped = config_module.build_variables(config, _AM_ROOT, None)
    assert not [w for w in static_unmapped if "artifact-locations.deprecated-alias" in w]


# --- 2. equal spec-plan paths stay silent ---------------------------------


def test_spec_plan_paths_equal_produces_no_warning():
    config = {
        "spec-plan-workflow": {
            "paths": {"specs": "docs/specs", "plans": "docs/plans"}
        },
        "artifact-locations": {"enabled": True},
    }
    assert _warnings(config) == []


# --- 3. se_output.base_dir divergence warns -------------------------------


def test_se_output_divergence_warns():
    config = {
        "se_output": {"base_dir": "docs/se"},
        "artifact-locations": {"enabled": True},
    }
    findings = _warnings(config)
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    text = findings[0].message
    assert "se_output.base_dir" in text
    assert "artifact-locations.classes.se-" in text
    assert "deprecated" in text


# --- 4. scratch alias is attribution, not a fifth value source ------------


def test_scratch_alias_is_attribution_not_a_level():
    # A non-empty matrix section keeps the alias attribution visible (T4).
    config = {
        "artifact-locations": {"classes": {}},
        "repo_containment": {"tmp-sink": {"path": "legacy-sink"}},
    }
    matrix = resolve_artifact_locations(config, _AM_ROOT, None)
    scratch = matrix.classes["scratch"]
    assert scratch.path == "legacy-sink"
    assert scratch.field_sources["path"] == "project-alias:repo_containment.tmp-sink.path"
    assert scratch.source == SOURCE_PROJECT
    # The alias is an attribution family, never a fifth value source (D1, AC-15).
    value_sources = {
        SOURCE_PROJECT,
        SOURCE_PRESET_PREFIX + "default",
        SOURCE_SCHEMA_DEFAULT,
        SOURCE_CODE_FALLBACK,
    }
    assert len(value_sources) == 4
    assert scratch.field_sources["path"].startswith(SOURCE_ALIAS)
    assert not any(source.startswith(SOURCE_ALIAS) for source in value_sources)


# --- 5. scratch deprecation warning carries the migration hint ------------


def test_scratch_deprecation_warning_has_migration_hint():
    config = {"repo_containment": {"tmp-sink": {"path": "legacy-sink"}}}
    findings = _warnings(config)
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    text = findings[0].message
    assert "artifact-locations.classes.scratch.path" in text
    assert "deprecated" in text
    assert "--migrate-artifact-aliases" in text


# --- 6. class-only scratch is already migrated ----------------------------


def test_scratch_class_only_produces_no_warning():
    config = {"artifact-locations": {"classes": {"scratch": {"path": "matrix-sink"}}}}
    assert _warnings(config) == []


# --- 7. both scratch keys equal: one warning to remove the alias ----------


def test_scratch_both_equal_warns_once_about_removal():
    config = {
        "artifact-locations": {"classes": {"scratch": {"path": "shared-sink"}}},
        "repo_containment": {"tmp-sink": {"path": "shared-sink"}},
    }
    findings = _warnings(config)
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    text = findings[0].message
    assert "repo_containment.tmp-sink.path" in text
    assert "deprecated" in text
    assert "remove" in text.lower()


# --- 8. TMP_SINK_PATH comes from the resolved matrix ----------------------


def test_tmp_sink_path_variable_comes_from_matrix():
    variables, _ = config_module.build_variables(
        {"artifact-locations": {"classes": {"scratch": {"path": "matrix-sink"}}}},
        _AM_ROOT,
        None,
    )
    assert variables["TMP_SINK_PATH"] == variables["ARTIFACT_SCRATCH_DIR"]
    assert variables["TMP_SINK_PATH"] == "matrix-sink"

    # Exactly one assignment in config.py, sourced from ARTIFACT_SCRATCH_DIR.
    source = (_AM_ROOT / "scripts" / "lib" / "config.py").read_text(encoding="utf-8")
    assigned_values = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if (
                isinstance(target, ast.Subscript)
                and isinstance(target.value, ast.Name)
                and target.value.id == "variables"
                and isinstance(target.slice, ast.Constant)
                and target.slice.value == "TMP_SINK_PATH"
            ):
                assigned_values.append(node.value)
    assert len(assigned_values) == 1
    value = assigned_values[0]
    assert isinstance(value, ast.Subscript) and isinstance(value.value, ast.Name)
    assert value.value.id == "variables"
    assert isinstance(value.slice, ast.Constant)
    assert value.slice.value == "ARTIFACT_SCRATCH_DIR"


# --- 9. state alias divergence warns --------------------------------------


def test_state_divergence_warns():
    config = {
        "progress": {"dir": "legacy-progress"},
        "artifact-locations": {
            "classes": {"state": {"subdirs": {"progress": "matrix-progress"}}}
        },
    }
    findings = _warnings(config)
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    text = findings[0].message
    assert "progress.dir" in text
    assert "artifact-locations.classes.state.subdirs.progress" in text


# --- 10. disabled matrix suppresses all deprecation warnings --------------


def test_disabled_matrix_suppresses_deprecation_warnings():
    config = {
        "spec-plan-workflow": {"paths": {"specs": "docs/specs-old"}},
        "se_output": {"base_dir": "docs/se"},
        "repo_containment": {"tmp-sink": {"path": "legacy-sink"}},
        "progress": {"dir": "legacy-progress"},
        "artifact-locations": {
            "enabled": False,
            "classes": {"state": {"subdirs": {"progress": "matrix-progress"}}},
        },
    }
    assert _warnings(config) == []
    active_set = compute_active_set(config, _AM_ROOT, _AM_ROOT, warn_sink=[])
    _, unmapped = config_module.build_variables(
        config, _AM_ROOT, _AM_ROOT, active_set=active_set,
    )
    assert not [w for w in unmapped if "artifact-locations.deprecated-alias" in w]
