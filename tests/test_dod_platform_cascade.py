"""Regression tests for the platform dod-preset cascade
(Task 4 of the platform-project-defaults feature, scripts/lib/dod.py).

Uses the real agent-meta repo_root and the real
platform-configs/hacs.defaults.yaml fixture from Task 1 (dod-preset:
standard). Distinguishing assertions use dod-presets.yaml's real per-preset
field values (config/dod-presets.yaml): full.codebase-overview=True,
standard.tests-required=True/codebase-overview=False,
rapid-prototyping.tests-required=False.
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.dod import resolve_dod, resolve_dod_preset_name

_REPO_ROOT = Path(__file__).resolve().parents[1]


def test_explicit_project_dod_preset_wins_over_platform_default():
    config = {"platforms": ["hacs"], "dod-preset": "rapid-prototyping"}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "rapid-prototyping"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["tests-required"] is False  # rapid-prototyping, not hacs' 'standard'


def test_platform_dod_preset_wins_when_project_does_not_set_one():
    config = {"platforms": ["hacs"]}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "standard"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["tests-required"] is True      # 'standard', not 'full's implicit default
    assert resolved["codebase-overview"] is False   # 'full' would be True here


def test_no_platforms_and_no_override_falls_back_to_full():
    config = {}
    assert resolve_dod_preset_name(config, _REPO_ROOT) == "full"
    resolved = resolve_dod(config, _REPO_ROOT)
    assert resolved["codebase-overview"] is True  # 'full' preset value


# --- #1158 K-02/K-13: REQ/test mandates follow the resolved DoD flags -------

_GATED_TEMPLATES = ("git", "tester", "se-developer", "se-junior-developer",
                    "se-senior-developer")
# Mandatory REQ markers: commit-format scope and test-name prefix.
_REQ_MANDATE_MARKERS = ("(REQ-xxx)", "[REQ-xxx]", "[REQ-004]", "always with a REQ reference")


def _render_with_preset(template: str, preset: str) -> str:
    from scripts.lib.variables import strip_inactive_conditional_blocks

    resolved = resolve_dod({"platforms": [], "dod-preset": preset}, _REPO_ROOT)
    flags = {
        "DOD_REQ_TRACEABILITY": "true" if resolved["req-traceability"] else "false",
        "DOD_TESTS_REQUIRED": "true" if resolved["tests-required"] else "false",
    }
    text = (_REPO_ROOT / "agents" / "1-generic" / f"{template}.md").read_text(encoding="utf-8")
    return strip_inactive_conditional_blocks(text, flags)


def test_rapid_prototyping_render_has_no_req_mandate():
    for template in _GATED_TEMPLATES:
        rendered = _render_with_preset(template, "rapid-prototyping")
        hits = [m for m in _REQ_MANDATE_MARKERS if m in rendered]
        assert not hits, f"{template}: ungated REQ mandate {hits}"


def test_full_preset_render_keeps_req_mandate():
    for template in _GATED_TEMPLATES:
        rendered = _render_with_preset(template, "full")
        assert any(m in rendered for m in _REQ_MANDATE_MARKERS), template


def test_standalone_false_flags_drop_req_mandate():
    # K-13: standalone mode has no DoD config -> DOD_* flags are inert (false),
    # so the standalone render must look like rapid-prototyping, not "full".
    from scripts.lib.standalone import _CONDITIONAL_FALSE_FLAGS
    from scripts.lib.variables import strip_inactive_conditional_blocks

    text = (_REPO_ROOT / "agents" / "1-generic" / "git.md").read_text(encoding="utf-8")
    rendered = strip_inactive_conditional_blocks(text, dict(_CONDITIONAL_FALSE_FLAGS))
    assert "(REQ-xxx)" not in rendered


def test_feature_lifecycle_render_follows_req_flag():
    from scripts.lib.pipelines import inject_pipeline_blocks, load_quality_pipelines

    pipelines = load_quality_pipelines(str(_REPO_ROOT))
    for preset, expect_req in (("rapid-prototyping", False), ("standard", False),
                               ("full", True)):
        dod = resolve_dod({"platforms": [], "dod-preset": preset,
                           "spec-plan-workflow": {"enabled": False}}, _REPO_ROOT)
        rendered = inject_pipeline_blocks(
            "{{PIPELINE_FEATURE_LIFECYCLE_BLOCK}}", pipelines, "Claude", dod,
        )
        assert ("REQ-ID" in rendered) is expect_req, (preset, rendered)
