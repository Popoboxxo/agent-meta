"""Tests for model-inherit-main-chat (main-chat model inheritance).

Covers:
- resolve_model(): truthy 'model-inherit-main-chat'[provider] returns ""
  for every role of that provider, beating per-role overrides,
  tier-overrides and tier presets.
- config._validate_model_inheritance(): mutual exclusivity with
  'model-override-all' per provider (SystemExit on conflict/type errors),
  different providers never conflict.
- Regression: plain 'model-override-all' still resolves to a model ID.
- No-op semantics: absent / None / false entries change nothing.

Tests use the real config files from the repo — no mocking.
Most tests target the Claude provider for deterministic model IDs;
the generation-path regression tests target Continue (the one provider
whose transform falls back to raw role-defaults when resolution is empty).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.provider_transform import transform_agent_content_for_provider
from scripts.lib.config import _validate_model_inheritance
from scripts.lib.log import SyncLog
from scripts.lib.providers import load_providers_config
from scripts.lib.roles import resolve_model


REPO_ROOT = Path(__file__).parent.parent

CLAUDE_MODEL_POWERFUL = "claude-opus-4-8"
CLAUDE_MODEL_FAST = "claude-haiku-4-5-20251001"
CLAUDE_MODEL_BALANCED = "claude-sonnet-5"

_PROVIDER_CONFIG = load_providers_config(REPO_ROOT)


def _resolve(role: str, extra: dict | None = None) -> str:
    """Helper: resolve model for a role with the Normal preset (+ extras)."""
    project_config: dict = {"tier-preset": "Normal"}
    if extra:
        project_config.update(extra)
    return resolve_model(
        role=role,
        project_config=project_config,
        agent_meta_root=REPO_ROOT,
        provider="Claude",
        provider_config=_PROVIDER_CONFIG,
    )


# ---------------------------------------------------------------------------
# (a) Inheritance wins over everything below it
# ---------------------------------------------------------------------------

def test_inherit_returns_empty_string_for_role() -> None:
    """Truthy inherit entry → empty string so no model: field is injected."""
    assert _resolve("developer", extra={"model-inherit-main-chat": {"Claude": True}}) == ""


def test_inherit_beats_overrides_and_presets() -> None:
    """Inheritance must beat per-role overrides, tier-overrides and presets."""
    noisy = {
        "model-inherit-main-chat": {"Claude": True},
        "model-overrides": {"Claude": {"developer": CLAUDE_MODEL_POWERFUL}},
        "tier-overrides": {"developer": "fast"},
        "tier-preset": "Expensive as Hell",
        "se-focus": True,
    }
    resolved = _resolve("developer", extra=noisy)
    assert resolved == "", (
        f"Inheritance must win over overrides/presets, got {resolved!r}"
    )


def test_inherit_without_noise_would_resolve_nonempty() -> None:
    """Sanity: the same overrides WITHOUT inheritance produce a real model —
    proves the empty string above comes from inheritance, not from broken config."""
    baseline = {
        "model-overrides": {"Claude": {"developer": CLAUDE_MODEL_POWERFUL}},
        "tier-preset": "Expensive as Hell",
    }
    resolved = _resolve("developer", extra=baseline)
    assert resolved == CLAUDE_MODEL_POWERFUL


def test_inherit_only_applies_to_configured_provider() -> None:
    """A Gemini-only inherit entry must not affect the Claude provider."""
    resolved = _resolve(
        "senior-developer",
        extra={"model-inherit-main-chat": {"Gemini": True}},
    )
    assert resolved == CLAUDE_MODEL_POWERFUL, (
        f"Claude must fall through to Normal preset resolution, got {resolved!r}"
    )


# --- Continue generation path (transform_agent_content_for_provider) --------


def _generate_continue_agent(extra: dict | None = None) -> str:
    """Helper: run the full Continue generation transform for the 'developer' role."""
    content = (
        "---\n"
        "name: template-developer\n"
        'version: "1.0.0"\n'
        "description: Feature-Implementierung und Bugfixes\n"
        "---\n"
        "\n"
        "Body content.\n"
    )
    project_config: dict = {}
    if extra:
        project_config.update(extra)
    return transform_agent_content_for_provider(
        content, "Continue", "developer", "developer",
        "Feature-Implementierung und Bugfixes",
        "1-generic/developer.md@1.0.0", project_config,
        REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".continue" / "agents" / "developer.md",
        _PROVIDER_CONFIG, SyncLog(),
    )


def test_continue_generation_path_inherit_keeps_model_empty() -> None:
    """Regression: with inherit active the Continue generation path must NOT
    fall back to raw role-defaults — no model: field may be injected."""
    fm = _generate_continue_agent(
        {"model-inherit-main-chat": {"Continue": True}},
    ).split("---")[1]
    assert "model:" not in fm, f"Inherit must suppress role-defaults fallback, got: {fm!r}"


def test_continue_generation_path_without_inherit_uses_role_defaults_fallback() -> None:
    """Counter-test: WITHOUT inherit the model resolution stays as before —
    resolve_model() maps role-defaults tier 'balanced' via the Normal preset
    to a concrete ID, so the raw role-defaults fallback never triggers."""
    fm = _generate_continue_agent().split("---")[1]
    assert "model: claude-sonnet-5" in fm, (
        f"Without inherit the generation path must resolve as before, got: {fm!r}"
    )


# ---------------------------------------------------------------------------
# (b) Mutual exclusivity validation (_validate_model_inheritance)
# ---------------------------------------------------------------------------

def test_conflict_same_provider_exits_with_provider_and_keys() -> None:
    """Same provider set in both keys → SystemExit(1), message names provider + both keys."""
    config = {
        "model-inherit-main-chat": {"Claude": True},
        "model-override-all": {"Claude": "powerful"},
    }
    with pytest.raises(SystemExit) as excinfo:
        _validate_model_inheritance(config, Path("project.yaml"))

    assert excinfo.value.code == 1


def test_conflict_message_contains_provider_and_both_keys(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """The stderr output must mention the provider and BOTH conflicting keys."""
    config = {
        "model-inherit-main-chat": {"Claude": True},
        "model-override-all": {"Claude": "powerful"},
    }
    with pytest.raises(SystemExit):
        _validate_model_inheritance(config, Path("project.yaml"))

    stderr = capsys.readouterr().err
    assert "Claude" in stderr
    assert "model-override-all" in stderr
    assert "model-inherit-main-chat" in stderr


def test_no_conflict_across_different_providers(capsys: pytest.CaptureFixture[str]) -> None:
    """Different providers never conflict — no SystemExit."""
    config = {
        "model-inherit-main-chat": {"Claude": True},
        "model-override-all": {"Gemini": "powerful"},
    }
    _validate_model_inheritance(config, Path("project.yaml"))
    assert "ERROR" not in capsys.readouterr().err


def test_false_inherit_counts_as_unset_even_with_override_all() -> None:
    """'false' counts as unset: false + override-all for the SAME provider is fine."""
    config = {
        "model-inherit-main-chat": {"Claude": False},
        "model-override-all": {"Claude": "powerful"},
    }
    _validate_model_inheritance(config, Path("project.yaml"))


def test_non_bool_entry_exits_with_error(capsys: pytest.CaptureFixture[str]) -> None:
    """Non-bool provider entry (would be silently ignored at runtime) → hard abort."""
    config = {"model-inherit-main-chat": {"Claude": "yes"}}
    with pytest.raises(SystemExit) as excinfo:
        _validate_model_inheritance(config, Path("project.yaml"))

    assert excinfo.value.code == 1
    stderr = capsys.readouterr().err
    assert "model-inherit-main-chat" in stderr
    assert "'yes'" in stderr
    assert "bool" in stderr


def test_non_mapping_block_exits_with_error(capsys: pytest.CaptureFixture[str]) -> None:
    """A scalar instead of a mapping → hard abort naming the key."""
    config = {"model-inherit-main-chat": True}
    with pytest.raises(SystemExit) as excinfo:
        _validate_model_inheritance(config, Path("project.yaml"))

    assert excinfo.value.code == 1
    stderr = capsys.readouterr().err
    assert "model-inherit-main-chat" in stderr


# --- (c) Dead-config warnings (soft, sync continues) ------------------------


def test_shadowed_nested_overrides_warn_but_continue(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Per-provider entries under active inherit are dead config: one-line
    WARNING naming provider + roles, but NO SystemExit."""
    config = {
        "model-inherit-main-chat": {"Continue": True},
        "model-overrides": {"Continue": {"developer": "powerful"}},
    }
    _validate_model_inheritance(config, Path("project.yaml"))

    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "'Continue'" in captured.err
    assert "developer" in captured.err


def test_shadowed_flat_overrides_warn_for_claude(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Legacy flat role map applies to Claude only — warn when Claude inherit
    is active; no warning when only another provider inherits."""
    config = {
        "model-inherit-main-chat": {"Claude": True},
        "model-overrides": {"developer": "powerful"},
    }
    _validate_model_inheritance(config, Path("project.yaml"))
    assert "WARNING" in capsys.readouterr().err

    config["model-inherit-main-chat"] = {"Gemini": True}
    _validate_model_inheritance(config, Path("project.yaml"))
    assert "WARNING" not in capsys.readouterr().err


# ---------------------------------------------------------------------------
# (c) REGRESSION: override-all still resolves to a model ID
# ---------------------------------------------------------------------------

def test_regression_override_all_resolves_tier_to_model_id() -> None:
    """Plain override-all with a tier name must resolve to the concrete model ID."""
    resolved = _resolve("developer", extra={"model-override-all": {"Claude": "powerful"}})
    assert resolved == CLAUDE_MODEL_POWERFUL


def test_regression_override_all_passthrough_model_id() -> None:
    """Plain override-all with a full model ID must be returned as-is."""
    resolved = _resolve("developer", extra={"model-override-all": {"Claude": CLAUDE_MODEL_FAST}})
    assert resolved == CLAUDE_MODEL_FAST


# ---------------------------------------------------------------------------
# (d) No-op semantics: absent / None / false
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "extra",
    [
        pytest.param({}, id="key-absent"),
        pytest.param({"model-inherit-main-chat": None}, id="explicit-none"),
        pytest.param({"model-inherit-main-chat": {"Claude": False}}, id="explicit-false"),
        pytest.param({"model-inherit-main-chat": {}}, id="empty-block"),
    ],
)
def test_noop_variants_behave_like_baseline(extra: dict) -> None:
    """Absent/None/false/empty inherit must not change normal resolution."""
    resolved = _resolve("developer", extra=extra)
    baseline = _resolve("developer")
    assert resolved == baseline == CLAUDE_MODEL_BALANCED, (
        f"No-op variant must match Normal-preset baseline: got {resolved!r}, expected {baseline!r}"
    )
