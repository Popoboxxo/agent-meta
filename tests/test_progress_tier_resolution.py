"""Tier resolution for the progress file (design doc
2026-09-10-live-progress-channel-design.md, Architecture §1): Tier A only
when EVERY active provider has a verified hook_protocol."""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.checkpoint import _progress_tier  # noqa: E402


def test_tier_a_when_no_project_yaml_defaults_to_claude(tmp_path):
    # No .meta-config/project.yaml at all -- resolve_providers() falls back
    # to "Claude" (its own documented default), which has a verified
    # hook_protocol -- Tier A. Matches the pre-existing overwrite tests that
    # use a bare tmp_path with no project.yaml (Task 1).
    assert _progress_tier(tmp_path, _REPO_ROOT) == "A"


def test_tier_b_for_hookless_provider(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "ai-providers: [Opencode]\n", encoding="utf-8"
    )
    assert _progress_tier(tmp_path, _REPO_ROOT) == "B"


def test_mixed_provider_set_falls_back_to_tier_b(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "ai-providers: [Claude, Opencode]\n", encoding="utf-8"
    )
    assert _progress_tier(tmp_path, _REPO_ROOT) == "B"


def test_tier_a_for_gemini_alone(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "ai-providers: [Gemini]\n", encoding="utf-8"
    )
    assert _progress_tier(tmp_path, _REPO_ROOT) == "A"
