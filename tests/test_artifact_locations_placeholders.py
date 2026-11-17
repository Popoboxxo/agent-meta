"""T7: ARTIFACT_* placeholder allow-list registration (issue #1186, Spec §4.7).

The 54 names exported by T6's ``_build_artifact_variables`` must be registered
in ``_BUILTIN_VARS`` so that ``check_builder_known_set`` stays green. The
shrink-only ``_UNREGISTERED_BUILDER_RATCHET`` must not be touched.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.consistency import placeholders as ph  # noqa: E402

# The exact 54-name contract from plan §3.3 / Spec §3.4 (T6/T7 pin this set).
# The two pre-existing release vars (ARTIFACT_ZIP_CMD, ARTIFACT_TAR_CMD) are
# already registered and are intentionally not part of this set.
EXPECTED_ARTIFACT_NAMES: frozenset[str] = frozenset({
    # 13 non-SE _DIR
    "ARTIFACT_SPECS_DIR", "ARTIFACT_PLANS_DIR", "ARTIFACT_CONCEPTS_DIR",
    "ARTIFACT_SPIKES_DIR", "ARTIFACT_REVIEWS_DIR", "ARTIFACT_AUDITS_DIR",
    "ARTIFACT_ANALYSIS_DIR", "ARTIFACT_REPORTS_DIR", "ARTIFACT_ADR_DIR",
    "ARTIFACT_TRACEABILITY_DIR", "ARTIFACT_RUNBOOKS_DIR",
    "ARTIFACT_SCRATCH_DIR", "ARTIFACT_STATE_DIR",
    # 9 SE cell-class _DIR
    "ARTIFACT_SE_REQUIREMENTS_DIR", "ARTIFACT_SE_ARCHITECTURE_DIR",
    "ARTIFACT_SE_DECOMPOSITION_DIR", "ARTIFACT_SE_INTERFACES_DIR",
    "ARTIFACT_SE_IMPLEMENTATION_DIR", "ARTIFACT_SE_TESTPLAN_DIR",
    "ARTIFACT_SE_VALIDATION_DIR", "ARTIFACT_SE_VERIFICATION_DIR",
    "ARTIFACT_SE_DECISIONS_DIR",
    # 4 derived SE projection _DIR
    "ARTIFACT_SE_REVIEWS_DIR", "ARTIFACT_SE_REPORTS_DIR",
    "ARTIFACT_SE_ADR_DIR", "ARTIFACT_SE_TRACEABILITY_DIR",
    # 1 root (alias SE_BASE_DIR)
    "ARTIFACT_SE_ROOT",
    # 4 project-docs _FILE
    "ARTIFACT_ARCHITECTURE_FILE", "ARTIFACT_CODEBASE_OVERVIEW_FILE",
    "ARTIFACT_REQUIREMENTS_FILE", "ARTIFACT_ISSUE_LABELS_FILE",
    # 23 _MODE (one per class)
    "ARTIFACT_SPECS_MODE", "ARTIFACT_PLANS_MODE", "ARTIFACT_CONCEPTS_MODE",
    "ARTIFACT_SPIKES_MODE", "ARTIFACT_REVIEWS_MODE", "ARTIFACT_AUDITS_MODE",
    "ARTIFACT_ANALYSIS_MODE", "ARTIFACT_REPORTS_MODE", "ARTIFACT_ADR_MODE",
    "ARTIFACT_TRACEABILITY_MODE", "ARTIFACT_RUNBOOKS_MODE",
    "ARTIFACT_SCRATCH_MODE", "ARTIFACT_STATE_MODE",
    "ARTIFACT_PROJECT_DOCS_MODE", "ARTIFACT_SE_REQUIREMENTS_MODE",
    "ARTIFACT_SE_ARCHITECTURE_MODE", "ARTIFACT_SE_DECOMPOSITION_MODE",
    "ARTIFACT_SE_INTERFACES_MODE", "ARTIFACT_SE_IMPLEMENTATION_MODE",
    "ARTIFACT_SE_TESTPLAN_MODE", "ARTIFACT_SE_VALIDATION_MODE",
    "ARTIFACT_SE_VERIFICATION_MODE", "ARTIFACT_SE_DECISIONS_MODE",
})

# Exact current ratchet contents, pinned so any growth fails this task.
EXPECTED_BUILDER_RATCHET: frozenset[str] = frozenset({
    "AGENT_HINTS_CLAUDE", "AGENT_LOCATIONS", "DEVELOPER_SNIPPETS_PATH_SET",
    "DEV_STACK_START_SET", "EFFORT_ESTIMATOR_ENABLED", "KNOWLEDGE_BUNDLE_PATH",
    "KNOWLEDGE_ENGINE_ENABLED", "KNOWLEDGE_SCHEMA_PATH", "KNOWLEDGE_SOURCES_DIR",
    "KNOWLEDGE_WIKI_DIR", "NATIVE_EXTENSIONS_ENABLED",
    "NATIVE_EXTENSIONS_WHITELIST_ACTIVE", "NATIVE_EXTENSIONS_WHITELIST_TABLE",
    "ORCH_MODE_ADVISORY", "ORCH_MODE_DISABLED", "ORCH_MODE_MAIN_CHAT",
    "ORCH_MODE_STRICT", "PROGRESS_CHAT_PUSH_ENABLED", "PROVIDER_ROUTING",
    "TESTER_SNIPPETS_PATH_SET", "WEB_PROJECT_ENABLED",
})


def _derived_artifact_names() -> set[str]:
    """ARTIFACT_* names produced by the builders on an empty config."""
    return {k for k in ph.derive_builder_vars(ROOT) if k.startswith("ARTIFACT_")}


def test_all_derived_artifact_vars_are_registered():
    """Every builder-produced ARTIFACT_* name must be in the allow-list."""
    missing = _derived_artifact_names() - ph._BUILTIN_VARS
    assert missing == set(), f"Unregistered ARTIFACT_* vars: {sorted(missing)}"


def test_exactly_54_artifact_names_derived_and_registered():
    """The builder yields exactly the pinned 54 names, all registered."""
    assert len(EXPECTED_ARTIFACT_NAMES) == 54
    assert _derived_artifact_names() == set(EXPECTED_ARTIFACT_NAMES)
    assert EXPECTED_ARTIFACT_NAMES <= ph._BUILTIN_VARS


def test_template_artifact_placeholders_resolve_to_allow_list(tmp_path):
    """All 54 names used in a template produce no placeholders.unknown."""
    template = tmp_path / "a.md"
    body = "Use " + ", ".join(f"{{{{{name}}}}}" for name in sorted(EXPECTED_ARTIFACT_NAMES)) + ".\n"
    template.write_text("---\nname: a\n---\n" + body, encoding="utf-8")
    findings = ph.check_placeholders(template, template.read_text(encoding="utf-8"), tmp_path)
    unknown = [f for f in findings if f.check == "placeholders.unknown"]
    assert unknown == [], f"Unknown placeholders: {[f.message for f in unknown]}"


def test_builder_ratchet_is_unchanged():
    """The shrink-only builder ratchet is not used to absorb the new names."""
    assert ph._UNREGISTERED_BUILDER_RATCHET == EXPECTED_BUILDER_RATCHET
    assert not (EXPECTED_ARTIFACT_NAMES & ph._UNREGISTERED_BUILDER_RATCHET)


def test_builder_known_set_real_repo_is_clean():
    """Regression guard: the real repo has zero builder-known-set findings."""
    assert ph.check_builder_known_set(ROOT) == []
