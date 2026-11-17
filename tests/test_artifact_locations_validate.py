"""Sync-time validator tests for the ``artifact-locations`` matrix (Issue #1186, T5).

The validator is the single hard exit for the semantic matrix checks: an
``ArtifactLocationsError`` from the T4 resolver is translated into a
``stderr`` message plus ``sys.exit(1)``. Structure/path checks run even when
``enabled: false`` so a later opt-in never surfaces a dormant misconfiguration
(spec §4.1, AC-1186-11).

Run: export PYTEST_BASETEMP=.tmp/pytest-1186-t5
     python3 -m pytest tests/test_artifact_locations_validate.py --basetemp="$PYTEST_BASETEMP" -q
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import (  # noqa: E402
    _validate_artifact_locations,
    _validate_config,
)

_AM_ROOT = _REPO_ROOT


def _config_path(tmp_path: Path) -> Path:
    path = tmp_path / ".meta-config" / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _validate(config: dict, tmp_path: Path):
    return _validate_artifact_locations(config, _config_path(tmp_path), _AM_ROOT)


def _section(**classes) -> dict:
    return {"artifact-locations": {"classes": classes}}


# --- 1. path-invalid ----------------------------------------------------


def test_path_invalid_is_hard_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(_section(specs={"path": "../x"}), tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.path-invalid" in err
    assert "artifact-locations.classes.specs.path" in err
    assert "must stay inside the project root" in err


# --- 2./3. mode-parent-missing + fallback-parent ------------------------


def test_off_without_parent_is_hard_error(tmp_path, capsys):
    # `reviews` without an active SE cascade has no documented frontmatter sink.
    with pytest.raises(SystemExit) as exc:
        _validate(_section(reviews={"mode": "off"}), tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.mode-parent-missing" in err
    assert "fallback-parent" in err


def test_off_with_fallback_parent_is_accepted(tmp_path):
    _validate(
        _section(reviews={"mode": "off", "fallback-parent": "se-requirements"}),
        tmp_path,
    )


def test_fallback_parent_unknown_is_hard_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(_section(reviews={"fallback-parent": "bogus"}), tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.fallback-parent-unknown" in err
    assert "bogus" in err


# --- 4. kind-invalid ----------------------------------------------------


def test_kind_outside_enum_is_hard_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(_section(analysis={"kind": ["bogus"]}), tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.kind-invalid" in err
    assert "artifact-locations.classes.analysis.kind" in err


# --- 5. documented frontmatter sink -------------------------------------


def test_off_with_frontmatter_sink_is_accepted(tmp_path):
    # Active SE cascade: SE review findings land in the `review_state`
    # frontmatter of se-requirements (se-critic.md) — no extra parent needed.
    config = {
        "systems-engineering": {"enabled": True},
        "artifact-locations": {"classes": {"reviews": {"mode": "off"}}},
    }
    _validate(config, tmp_path)


# --- 6./7./8. SE start-critical -----------------------------------------


def test_se_requirements_off_with_active_cascade_is_hard_error(tmp_path, capsys):
    config = {
        "systems-engineering": {"enabled": True},
        "artifact-locations": {"classes": {"se-requirements": {"mode": "off"}}},
    }
    with pytest.raises(SystemExit) as exc:
        _validate(config, tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.se-required-off" in err
    assert "se-decomposition" in err


def test_se_requirements_off_without_cascade_is_accepted(tmp_path):
    config = {
        "systems-engineering": {"enabled": False},
        "artifact-locations": {"classes": {"se-requirements": {"mode": "off"}}},
    }
    _validate(config, tmp_path)


def test_se_decomposition_off_is_accepted(tmp_path):
    config = {
        "systems-engineering": {"enabled": True},
        "artifact-locations": {"classes": {"se-decomposition": {"mode": "off"}}},
    }
    _validate(config, tmp_path)


# --- 9. subdir-invalid --------------------------------------------------


def test_subdir_invalid_is_hard_error(tmp_path, capsys):
    for value in ("a/b", ".."):
        with pytest.raises(SystemExit) as exc:
            _validate(_section(**{"se-validation": {"subdir": value}}), tmp_path)
        assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.subdir-invalid" in err


# --- 10. unknown-preset -------------------------------------------------


def test_unknown_preset_is_hard_error(tmp_path, capsys):
    config = {"artifact-locations": {"preset": "nope"}}
    with pytest.raises(SystemExit) as exc:
        _validate(config, tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.unknown-preset" in err
    assert "nope" in err


# --- 11./12. legacy / unmanaged intersection ---------------------------


def test_legacy_intersect_is_hard_error(tmp_path, capsys):
    config = {
        "artifact-locations": {
            "classes": {"specs": {"path": "docs/specs"}},
            "legacy": ["docs/specs"],
        }
    }
    with pytest.raises(SystemExit) as exc:
        _validate(config, tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.legacy-intersect" in err
    assert "docs/specs" in err


def test_unmanaged_intersect_is_hard_error(tmp_path, capsys):
    config = {
        "artifact-locations": {
            "classes": {"specs": {"path": "docs/specs"}},
            "unmanaged": ["docs/specs"],
        }
    }
    with pytest.raises(SystemExit) as exc:
        _validate(config, tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.unmanaged-intersect" in err
    assert "docs/specs" in err


# --- 13. structure always runs -----------------------------------------


def test_validation_runs_even_when_enabled_false(tmp_path, capsys):
    config = {
        "artifact-locations": {
            "enabled": False,
            "classes": {"specs": {"path": "../x"}},
        }
    }
    with pytest.raises(SystemExit) as exc:
        _validate(config, tmp_path)
    assert exc.value.code == 1
    assert "artifact-locations.path-invalid" in capsys.readouterr().err


# --- 14. wiring ---------------------------------------------------------


def test_validation_is_called_by_validate_config():
    source = (_REPO_ROOT / "scripts" / "lib" / "config.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    fn = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_validate_config"
    )
    calls = sorted(
        (node.lineno, node.func.id)
        for node in ast.walk(fn)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    )
    names = [name for _, name in calls]
    i_repo = names.index("_validate_repo_containment")
    i_matrix = names.index("_validate_artifact_locations")
    i_sub = names.index("_validate_subagent_permissions")
    assert i_repo < i_matrix < i_sub


# --- 15./16./17. scratch single source (D1) -----------------------------


def test_scratch_sink_divergence_is_hard_error(tmp_path, capsys):
    config = {
        "artifact-locations": {"classes": {"scratch": {"path": "sink-a"}}},
        "repo_containment": {"tmp-sink": {"path": "sink-b"}},
    }
    with pytest.raises(SystemExit) as exc:
        _validate(config, tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.scratch-sink-divergence" in err
    assert "artifact-locations.classes.scratch.path" in err
    assert "repo_containment.tmp-sink.path" in err
    assert "remove the legacy key" in err


def test_scratch_alias_equal_values_pass_validation(tmp_path):
    config = {
        "artifact-locations": {"classes": {"scratch": {"path": "sink"}}},
        "repo_containment": {"tmp-sink": {"path": "sink"}},
    }
    _validate(config, tmp_path)


def test_scratch_class_only_passes_validation(tmp_path):
    _validate(_section(scratch={"path": "sink"}), tmp_path)


# --- 18./19. naming-invalid (D3) ----------------------------------------


def test_naming_unknown_token_is_hard_error(tmp_path, capsys):
    config = {"artifact-locations": {"classes": {"specs": {"naming": "{bogus}-{slug}.md"}}}}
    with pytest.raises(SystemExit) as exc:
        _validate(config, tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "artifact-locations.naming-invalid" in err
    assert "{bogus}" in err
    assert "{class}" in err and "{nnn}" in err and "{folder}" in err


def test_naming_token_not_applicable_is_hard_error(tmp_path, capsys):
    bad = {"artifact-locations": {"classes": {"audits": {"naming": "{level}-{slug}.md"}}}}
    with pytest.raises(SystemExit) as exc:
        _validate(bad, tmp_path)
    assert exc.value.code == 1
    assert "artifact-locations.naming-invalid" in capsys.readouterr().err

    good = {"artifact-locations": {"classes": {"adr": {"naming": "{nnn}-{slug}.md"}}}}
    _validate(good, tmp_path)
