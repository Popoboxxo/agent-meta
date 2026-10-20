"""Task 11 (2b.2): orchestrator §2a/§9/agent-table compaction behind the profile.

Spec ``docs/specs/2026-10-11-context-profiles-spec.md`` IC-05 (AC-23 byte
stability, AC-24). Sections §2a, §9 and the ``<context>`` agent table are
wrapped in ``{{#if CONTEXT_PROFILE_COMPACT}}…{{else}}…{{/if}}``:

* ``full`` (or no opt-in): the ``{{else}}`` branch is the unchanged text and the
  render stays byte-identical to the frozen slimming golden (AC-23).
* ``compact`` (opt-in, **UNVERIFIED**): §2a points at the on-demand
  ``pipeline-details/<pipeline>.md`` files, §9 keeps the thresholds and points at
  ``_wf-orchestrator-reference.md``, and the agent table becomes a name list.

``compact`` is opt-in and unverified (IC-36): nothing here claims that the
profile is verified, validated or recommended. QG-5 freezes the ``compact``
render as ``tests/fixtures/compact-golden/orchestrator.md``.

Golden rebaseline log (the frozen ``compact`` fixture is edited only with a
documented reason):

* C2/C3/IC-05 roster gating (SPEC-CONTEXT-PROFILES-2026-10-11): the compact
  agent roster is now gated on the per-provider ``roster_in_harness`` capability.
  Claude's capability is ``true`` (roster lives in the harness), so the compact
  render legitimately drops ``**Agent table (names only):** <names>`` — the
  compact golden is rebaselined to that gated render. The ``{{else}}`` (full)
  branch is unchanged, so the slimming golden only moves with the version bump.
* Task 31 (2e.5, IC-27/AC-90): orchestrator gains the common-body §3a preview
  gate (template 8.7.0 -> 8.8.0); both goldens carry the new section and the
  version, the compact golden only additionally the version bump.
"""
from __future__ import annotations

import difflib
import re
from pathlib import Path

import pytest

from scripts.lib.agent_sync import (
    _apply_content_pipeline,
    _build_provider_vars,
    _compose_role_content,
    _finalize_agent_content,
    _resolve_sync_targets,
)
from scripts.lib.config import build_variables, load_config
from scripts.lib.log import SyncLog
from scripts.lib.providers import load_provider_capabilities, load_providers_config

_REPO_ROOT = Path(__file__).resolve().parents[1]
_TEMPLATE = _REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"
_FULL_GOLDEN = _REPO_ROOT / "tests" / "fixtures" / "slimming-golden" / "orchestrator.md"
_COMPACT_GOLDEN = _REPO_ROOT / "tests" / "fixtures" / "compact-golden" / "orchestrator.md"
_PROVIDER = "Claude"

# Anchors required in every profile (config/context-anchors.yaml, QG-3).
_ORCHESTRATOR_ANCHORS = ("Singleton-Regel", "STATUS: done", "RESULT: <", "ARTIFACTS:")

# The only inlined stage-detail marker rendered by the full §2a branch.
_INLINE_STAGE_DETAIL_MARKERS = (
    "### `feature-lifecycle`",
    "Full stage-by-stage instructions per pipeline",
)
_TABLE_HEADER = "| Agent | Core Capabilities |"
_NAMES_LINE = "**Agent table (names only):**"

_MODEL_MAP = {
    "claude-haiku-4-5-20251001": "claude-haiku-5-5",
    "claude-sonnet-5": "claude-sonnet-5-5",
    "claude-opus-4-8": "claude-opus-5-5",
}
_MODEL_LINE = re.compile(r"^model: (.*)$", re.MULTILINE)


def _roster_in_harness(provider: str) -> bool:
    """Whether ``provider`` keeps the agent roster in its harness (IC-09 key).

    Read from ``config/provider-capabilities.yaml`` (never hardcoded), so the
    assertion tracks the capability instead of a provider name.
    """
    caps = load_provider_capabilities(_REPO_ROOT)
    return (caps.get(provider) or {}).get("roster_in_harness") is True


def _normalize(text: str, variables: dict) -> str:
    """Port the release-volatile model line and drop the auto-commit tail.

    Mirrors the slimming gate's two non-template normalizations so the frozen
    goldens stay version/tier-agnostic.
    """
    text = _MODEL_LINE.sub(
        lambda m: "model: " + _MODEL_MAP.get(m.group(1), m.group(1)), text, count=1
    )
    block = variables.get("AUTO_COMMIT_BLOCK", "")
    if block and block in text:
        for span in (block + "\n\n", block + "\n"):
            if span in text:
                return text.replace(span, "", 1)
    return text


def _render_orchestrator(profile, project_root: Path):
    """Render the orchestrator through the real per-role sync path (Claude).

    ``profile`` is the ``context-profile`` axis value or ``None`` for the
    default (no opt-in). Writes only into ``project_root`` (a temp dir).
    """
    config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
    if profile is not None:
        config = {**config, "context-profile": profile}
    project_root.mkdir(parents=True, exist_ok=True)
    variables, _warnings = build_variables(config, _REPO_ROOT, project_root)
    variables.setdefault("PIPELINE_DETAILS_DIR", ".claude/pipeline-details")
    provider_config = load_providers_config(_REPO_ROOT)
    log = SyncLog()
    pc, _role_map, overrides, target_dir = _resolve_sync_targets(
        _PROVIDER, provider_config, _REPO_ROOT, project_root, config, True, log
    )
    assert pc is not None, "Claude provider config missing"
    source_path = overrides["orchestrator"]
    target_path = target_dir / "orchestrator.md"
    project_name = config.get("project", {}).get("name", "unknown")
    content, can_spawn, rel_source, source_version, description = _compose_role_content(
        source_path, _PROVIDER, project_name, _REPO_ROOT, project_root,
        target_path, log, pc=pc,
    )
    merged = _build_provider_vars(pc, _PROVIDER, variables, _REPO_ROOT, config=config)
    merged.setdefault("PIPELINE_DETAILS_DIR", ".claude/pipeline-details")
    content = _apply_content_pipeline(
        content, config, _PROVIDER, merged, rel_source, None, _REPO_ROOT, log
    )
    content = _finalize_agent_content(
        content, "orchestrator", "orchestrator.md", source_path, _PROVIDER,
        provider_config, source_version, description, can_spawn, config,
        _REPO_ROOT, project_root, target_path, variables, False, log,
    )
    return content, variables


@pytest.fixture(scope="module")
def rendered(tmp_path_factory: pytest.TempPathFactory):
    root = tmp_path_factory.mktemp("orchestrator-compact")
    full, full_vars = _render_orchestrator(None, root / "full")
    compact, compact_vars = _render_orchestrator("compact", root / "compact")
    return {
        "full": full,
        "full_vars": full_vars,
        "compact": compact,
        "compact_vars": compact_vars,
    }


def _diff(expected: str, actual: str, label: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            expected.splitlines(), actual.splitlines(), f"golden/{label}", f"now/{label}",
            lineterm="",
        )
    )


def test_template_wraps_sections_in_profile_conditional():
    """Exactly the three sections carry a ``CONTEXT_PROFILE_COMPACT`` conditional."""
    content = _TEMPLATE.read_text(encoding="utf-8")
    assert content.count("{{#if CONTEXT_PROFILE_COMPACT}}") == 3, (
        "§2a, §9 and the agent table must each be wrapped once"
    )
    # The compact branch reaches the on-demand sources.
    assert "{{PIPELINE_DETAILS_DIR}}/<pipeline>.md" in content
    assert "{{AGENT_META_REL_PATH}}agents/1-generic/_wf-orchestrator-reference.md" in content
    assert "{{ACTIVE_ROLES}}" in content


def test_full_render_is_byte_identical_to_golden(rendered):
    """No opt-in: the ``{{else}}`` branch reproduces the frozen golden (AC-23)."""
    golden = _normalize(_FULL_GOLDEN.read_text(encoding="utf-8"), rendered["full_vars"])
    current = _normalize(rendered["full"], rendered["full_vars"])
    assert golden == current, _diff(golden, current, "orchestrator(full)")


def test_compact_render_drops_inline_detail_and_table(rendered):
    """``compact`` removes the inlined stage detail and the table overhead."""
    compact = rendered["compact"]
    for marker in _INLINE_STAGE_DETAIL_MARKERS + (_TABLE_HEADER,):
        assert marker not in compact, f"compact render still contains {marker!r}"
    assert "`.claude/pipeline-details/<pipeline>.md`" in compact
    assert "{{PIPELINE_DETAILS_DIR}}" not in compact


def test_compact_render_keeps_anchors_and_thresholds(rendered):
    """Thresholds stay verbatim, the anchors and the §9 pointer survive (QG-3)."""
    compact = rendered["compact"]
    for anchor in _ORCHESTRATOR_ANCHORS:
        assert anchor in compact, f"compact render lost the anchor {anchor!r}"
    assert "After >5 delegations: summarize in 2–3 sentences." in compact
    assert "Summarization-as-a-Contract (issue #267)" in compact
    assert "_wf-orchestrator-reference.md" in compact
    assert "{{" not in compact, "compact render carries unresolved placeholders"


def test_compact_render_matches_compact_golden(rendered):
    """QG-5: the opt-in render is frozen as a compact golden."""
    assert _COMPACT_GOLDEN.is_file(), (
        f"compact golden missing: {_COMPACT_GOLDEN} (QG-5)"
    )
    golden = _COMPACT_GOLDEN.read_text(encoding="utf-8")
    current = _normalize(rendered["compact"], rendered["compact_vars"])
    assert golden == current, _diff(golden, current, "orchestrator(compact)")
    assert _NAMES_LINE not in golden, (
        "the frozen compact golden must reflect the roster_in_harness gating "
        "(no names-only line for a roster-in-harness provider)"
    )


def test_compact_omits_roster_when_provider_keeps_it_in_harness(rendered):
    """C2/C3/IC-05: a ``roster_in_harness: true`` provider renders NO roster.

    Claude keeps the agent roster in its harness (``roster_in_harness: true``),
    so the compact ``<context>`` drops the names-only line entirely; the full
    render is untouched and keeps the delegation table.
    """
    assert _roster_in_harness(_PROVIDER) is True, (
        f"{_PROVIDER} is expected to declare roster_in_harness: true"
    )

    compact = rendered["compact"]
    assert _NAMES_LINE not in compact, (
        "roster_in_harness=true must omit the compact names-only roster"
    )
    assert "{{ACTIVE_ROLES}}" not in compact, "the roster placeholder must be resolved"
    assert "{{#unless ROSTER_IN_HARNESS}}" not in compact, (
        "the gating marker must be resolved"
    )
    assert "{{ROSTER_IN_HARNESS}}" not in compact, (
        "the bare roster marker must not leak into the render"
    )

    full = rendered["full"]
    assert _NAMES_LINE not in full
    assert _TABLE_HEADER in full, "the full render must keep the agent table"
