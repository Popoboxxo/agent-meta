"""Variable-export tests for the artifact-locations matrix (Issue #1186, T6).

``build_variables`` exports exactly 54 ``ARTIFACT_*`` names from the resolved
matrix (Spec §3.4, RVW-1186-02): 22 ``_DIR`` (13 non-SE + 9 SE cell classes),
4 derived SE projections, ``ARTIFACT_SE_ROOT``, 4 file-set ``_FILE`` names and
23 ``_MODE`` values. ``SE_BASE_DIR`` is an alias of ``ARTIFACT_SE_ROOT``, and
standalone personas receive the same 54 names with framework defaults.

Run: export PYTEST_BASETEMP=.tmp/pytest-1186-t6
     python3 -m pytest tests/test_artifact_locations_variables.py \
         --basetemp="$PYTEST_BASETEMP" -q
"""
from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import config as config_module  # noqa: E402
from lib import standalone as standalone_module  # noqa: E402
from lib.artifact_locations import CLASS_REGISTRY  # noqa: E402

_AM_ROOT = _REPO_ROOT

# The 13 non-SE directory/ephemeral/state classes with an _DIR variable.
_NON_SE_DIR_STEMS = (
    "SPECS", "PLANS", "CONCEPTS", "SPIKES", "REVIEWS", "AUDITS", "ANALYSIS",
    "REPORTS", "ADR", "TRACEABILITY", "RUNBOOKS", "SCRATCH", "STATE",
)
# The 4 SE-global projections are derived from ARTIFACT_SE_ROOT (D-7); the ADR
# leaf keeps the taxonomy spelling (upper-case), the other three are lowercase.
_SE_PROJECTION_LEAVES = {
    "SE_REVIEWS": "reviews",
    "SE_REPORTS": "reports",
    "SE_ADR": "ADR",
    "SE_TRACEABILITY": "traceability",
}
_FILE_DEFAULTS = {
    "ARTIFACT_ARCHITECTURE_FILE": "docs/ARCHITECTURE.md",
    "ARTIFACT_CODEBASE_OVERVIEW_FILE": "docs/CODEBASE_OVERVIEW.md",
    "ARTIFACT_REQUIREMENTS_FILE": "docs/REQUIREMENTS.md",
    "ARTIFACT_ISSUE_LABELS_FILE": "docs/issue-labels.md",
}


def _class_stem(name: str) -> str:
    return name.upper().replace("-", "_")


def _expected_names() -> set[str]:
    """The closed 54-name set, derived from the same registry as the builder."""
    names: set[str] = set()
    for class_name, spec in CLASS_REGISTRY.items():
        stem = _class_stem(class_name)
        names.add(f"ARTIFACT_{stem}_MODE")
        if spec.form != "file-set":
            names.add(f"ARTIFACT_{stem}_DIR")
    names.add("ARTIFACT_SE_ROOT")
    for stem in _SE_PROJECTION_LEAVES:
        names.add(f"ARTIFACT_{stem}_DIR")
    names.update(_FILE_DEFAULTS)
    return names


def _built_variables(config: dict | None = None) -> dict:
    variables, _ = config_module.build_variables(config or {}, _AM_ROOT)
    return variables


def _artifact_names(variables: dict) -> set[str]:
    return {key for key in variables if key.startswith("ARTIFACT_")}


# --- 1. exact count -------------------------------------------------------


def test_artifact_variable_count_is_54():
    names = _artifact_names(_built_variables())
    assert len(names) == 54
    assert names == _expected_names()


# --- 2. dir variables -----------------------------------------------------


def test_all_dir_variables_exported():
    variables = _built_variables()
    dir_stems = [
        _class_stem(name) for name, spec in CLASS_REGISTRY.items()
        if spec.form != "file-set"
    ]
    assert len(dir_stems) == 22
    for stem in dir_stems:
        key = f"ARTIFACT_{stem}_DIR"
        assert key in variables, key
        assert variables[key] and not variables[key].endswith("/"), (key, variables[key])
    for stem in _NON_SE_DIR_STEMS:
        assert f"ARTIFACT_{stem}_DIR" in variables
    assert "ARTIFACT_SE_ROOT" in variables
    assert not variables["ARTIFACT_SE_ROOT"].endswith("/")


# --- 3. SE projections ----------------------------------------------------


def test_se_projection_variables_exported():
    variables = _built_variables()
    root = variables["ARTIFACT_SE_ROOT"]
    for stem, leaf in _SE_PROJECTION_LEAVES.items():
        assert variables[f"ARTIFACT_{stem}_DIR"] == f"{root}/{leaf}"


# --- 4. mode variables ----------------------------------------------------


def test_mode_variables_exported():
    variables = _built_variables()
    matrix_values = _built_variables({
        "artifact-locations": {"classes": {"specs": {"mode": "inline"}}}
    })
    for class_name in CLASS_REGISTRY:
        key = f"ARTIFACT_{_class_stem(class_name)}_MODE"
        assert variables[key] in {"files", "inline", "off"}
        assert variables[key] == "files"
    # A configured mode propagates from the resolved matrix.
    assert matrix_values["ARTIFACT_SPECS_MODE"] == "inline"


# --- 5. ephemeral modes are constants ------------------------------------


def test_ephemeral_mode_is_files_constant():
    variables = _built_variables()
    assert variables["ARTIFACT_SCRATCH_MODE"] == "files"
    assert variables["ARTIFACT_STATE_MODE"] == "files"


# --- 6. file-set variables ------------------------------------------------


def test_file_set_variables_exported():
    variables = _built_variables()
    for key, value in _FILE_DEFAULTS.items():
        assert variables[key] == value
    # project-docs has no _DIR variable — only _FILE and _MODE.
    assert "ARTIFACT_PROJECT_DOCS_DIR" not in variables
    assert "ARTIFACT_PROJECT_DOCS_MODE" in variables


# --- 7. SE_BASE_DIR alias -------------------------------------------------


def test_se_base_dir_is_alias():
    variables = _built_variables({
        "se_output": {"base_dir": "LEGACY_SE"},
        "artifact-locations": {"classes": {"se-requirements": {"path": "MATRIX_SE"}}},
    })
    assert variables["ARTIFACT_SE_ROOT"] == "MATRIX_SE"
    assert variables["SE_BASE_DIR"] == variables["ARTIFACT_SE_ROOT"]
    assert variables["ARTIFACT_SE_REVIEWS_DIR"] == "MATRIX_SE/reviews"


# --- 8. builder totality on empty config ---------------------------------


def test_builder_is_total_on_empty_config():
    variables: dict = {}
    config_module._build_artifact_variables(variables, {}, _AM_ROOT, None)
    assert _artifact_names(variables) == _expected_names()
    assert len(_artifact_names(variables)) == 54


# --- 9. standalone fallbacks ---------------------------------------------


def test_standalone_supplies_artifact_variables():
    fallbacks = standalone_module._ARTIFACT_FALLBACKS
    assert set(fallbacks) == _expected_names()
    standalone_vars = standalone_module._standalone_variables(_AM_ROOT)
    for key in _expected_names():
        assert standalone_vars[key] == fallbacks[key]
    rendered = standalone_module.render_standalone_agent("developer", _AM_ROOT)
    assert "{{ARTIFACT_" not in rendered
    for line in rendered.splitlines():
        assert not ("ARTIFACT_" in line and "not available" in line)


# --- 10. reference-agent escape convention --------------------------------


def test_reference_agent_placeholders_remain_escaped():
    reference = (_AM_ROOT / "agents" / "1-generic" / "_reference-agent.md").read_text(
        encoding="utf-8"
    )
    assert re.findall(r"\{\{%[A-Z0-9_]+%\}\}", reference)
    assert not re.search(r"\{\{ARTIFACT_[A-Z0-9_]+\}\}", reference)


# --- 11. single builder call, correctly ordered --------------------------


def test_variables_built_once_per_provider():
    source = (_AM_ROOT / "scripts" / "lib" / "config.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    def call_lines(name: str) -> list[int]:
        return [
            node.lineno for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
            and node.func.id == name
        ]

    artifact_calls = call_lines("_build_artifact_variables")
    platform_calls = call_lines("_build_platform_variables")
    dod_calls = call_lines("_build_dod_variables")
    assert len(artifact_calls) == 1
    assert platform_calls and dod_calls
    assert max(platform_calls) < artifact_calls[0] < min(dod_calls)
