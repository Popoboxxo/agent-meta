"""Regression test: every provider with has_hooks/has_settings true must have
its own hooks_dir/settings_file, not silently fall back to Claude's paths.

Run: python -m pytest tests/test_provider_hooks_config.py -v
"""

from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PROVIDERS_CONFIG = _REPO_ROOT / "config" / "ai-providers.yaml"


def _load_providers() -> dict:
    with _PROVIDERS_CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_mammouth_has_its_own_hooks_dir_and_settings_file():
    """Without an explicit hooks_dir/settings_file, sync_hooks()/
    _init_provider_settings_json() silently default to Claude's paths
    (.claude/hooks, .claude/settings.json) — Mammouth must not collide with Claude.
    """
    providers = _load_providers()["providers"]
    mammouth = providers["Mammouth"]
    claude = providers["Claude"]
    assert mammouth.get("has_hooks") is True
    assert mammouth.get("hooks_dir") == ".mammouth/hooks"
    assert mammouth.get("settings_file") == ".mammouth/settings.json"
    assert mammouth["hooks_dir"] != claude.get("hooks_dir", ".claude/hooks")
    assert mammouth["settings_file"] != claude["settings_file"]


def test_codex_has_hooks_true_with_reserved_own_hooks_dir():
    """Codex declares has_hooks:true with its own hooks_dir as a PATH RESERVATION
    only (no hook_protocol yet — see config/ai-providers.yaml). The dir must
    differ from Claude's default .claude/hooks so a future hook mirror cannot
    silently collide with Claude's hook scripts.
    """
    providers = _load_providers()["providers"]
    codex = providers["Codex"]
    assert codex.get("has_hooks") is True
    assert codex.get("hooks_dir") == ".codex/hooks"
    assert codex["hooks_dir"] != providers["Claude"].get("hooks_dir", ".claude/hooks")
    # Deliberately no hook_protocol: sync must NOT mirror hook scripts until the
    # contract deviations are handled (config comment, issue #630 pattern).
    assert codex.get("hook_protocol") is None


def test_gemini_antigravity_hooks_supported():
    """Gemini (Antigravity) declares the VERIFIED hooks.json contract with a
    dedicated hook_protocol value (issue #674 Phase 3.1) — provider_hooks_supported()
    must return True so the orchestrator-strict.no-hook-support validate
    finding disappears. The protocol value is registered in
    scripts/lib/providers.py SUPPORTED_HOOK_PROTOCOLS (not a claude-code-json
    alias: registration artifact, payload keys and decision-JSON output all
    deviate from the Claude contract — see the config block comment)."""
    import sys

    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from lib.providers import SUPPORTED_HOOK_PROTOCOLS, provider_hooks_supported  # noqa: E402

    providers = _load_providers()["providers"]
    gemini = providers["Gemini"]
    assert gemini.get("has_hooks") is True
    assert "hooks" in gemini.get("capabilities", [])
    assert gemini.get("hook_protocol") == "antigravity-hooks-json"
    assert gemini.get("hook_protocol") in SUPPORTED_HOOK_PROTOCOLS
    assert provider_hooks_supported(gemini) is True
    # Registration artifacts (verified Antigravity workspace locations):
    # hooks.json at the documented .agents/ customization dir, mirrored
    # scripts beside it — NOT under .gemini/ (AGY does not read hooks from
    # Gemini CLI's settings surface there).
    assert gemini.get("hooks_dir") == ".agents/hooks"
    assert gemini.get("hooks_config_file") == ".agents/hooks.json"


def test_gemini_hooks_paths_do_not_collide_with_gemini_settings():
    """The Antigravity hook reservation must not collide with anything already
    owned by the Gemini provider itself (settings_file .gemini/settings.json is
    Gemini CLI's settings surface AND the MCP committed-file target — the
    hooks registration artifact is a separate file at the documented AGY
    workspace location)."""
    providers = _load_providers()["providers"]
    gemini = providers["Gemini"]
    assert gemini["hooks_dir"] != gemini["settings_file"]
    assert gemini["hooks_config_file"] != gemini["settings_file"]
    assert gemini["hooks_config_file"] != gemini["mcp-config"]["committed-file"]
    # And nothing under .gemini/ may be claimed by the hooks reservation —
    # .gemini/ stays exclusively the Gemini CLI surface (agents, commands,
    # settings, skills, ...).
    assert not gemini["hooks_dir"].startswith(".gemini/")
    assert not gemini["hooks_config_file"].startswith(".gemini/")


def test_gemini_hooks_registration_artifact_is_committed():
    """.agents/hooks.json + .agents/hooks/ are committed artifacts (like
    .claude/settings.json) — they must NOT appear in gitignore_entries, and
    `.agents/` must NOT be claimed as a provider root (shared cross-tool
    directory: Codex claims .agents/skills; whole-dir ignoring would hide
    other tools' files)."""
    providers = _load_providers()["providers"]
    gemini = providers["Gemini"]
    entries = set(gemini.get("gitignore_entries", []))
    assert ".agents/hooks.json" not in entries
    assert ".agents/" not in entries and ".agents/" not in gemini.get("provider_root_dirs", [])


@pytest.mark.parametrize("provider", ["ZCode", "KimiCode"])
def test_no_hooks_providers_reserve_no_hooks_dir(provider):
    """ZCode/KimiCode have has_hooks:false — no hooks_dir may be configured for
    them, so no hook path is reserved/consumed (project-level hooks are ignored
    by both harnesses; user-level config only)."""
    providers = _load_providers()["providers"]
    assert providers[provider].get("has_hooks") is False
    assert providers[provider].get("hooks_dir") is None


# ---------------------------------------------------------------------------
# Provider path-collision sweep (Codex/ZCode/KimiCode onboarding, 2026-09)
#
# Every generated path a provider owns must be owned by AT MOST ONE provider —
# a shared path would make two providers' sync runs fight over the same
# directory/file. Intentionally shared values are asserted explicitly below and
# excluded from the sweep:
#   - context_file AGENTS.md: shared by Gemini/Opencode/Mammouth/Codex/ZCode/
#     KimiCode (documented multi-provider context convergence),
#   - checkpoint_dir .meta-viz: shared viz checkpoint dir for all providers.
# ---------------------------------------------------------------------------

# Path keys that must be provider-exclusive. hooks_dir applies hooks.py's
# .claude/hooks default for has_hooks providers that don't declare it.
# hooks_config_file (issue #674 Phase 3.1): the Antigravity hooks.json
# registration artifact — provider-exclusive like hooks_dir/settings_file.
_COLLISION_PATH_KEYS = (
    "agents_dir", "hooks_dir", "hooks_config_file", "skills_dir", "snippets_dir",
    "extension_dir", "artifact_dir", "settings_file", "pending_tasks_file",
)

_INTENTIONAL_AGENTS_MD_SHARERS = ("Gemini", "Opencode", "Codex", "ZCode", "KimiCode")


def _collect_sweep_paths(providers: dict) -> dict:
    """provider -> {path_key: configured path} for the collision sweep.

    Applies hooks.py's default (pc.get("hooks_dir", ".claude/hooks")) for
    has_hooks providers without an explicit hooks_dir, so the sweep also sees
    Claude's effective default.
    """
    sweep: dict = {}
    for provider, pcfg in providers.items():
        paths = {}
        for key in _COLLISION_PATH_KEYS:
            value = pcfg.get(key)
            if value is None and key == "hooks_dir" and pcfg.get("has_hooks"):
                value = ".claude/hooks"  # default in scripts/lib/hooks.py
            if value:
                paths[key] = value
        sweep[provider] = paths
    return sweep


def test_path_collision_sweep_each_path_owned_by_one_provider():
    """No path from _COLLISION_PATH_KEYS may be owned by more than one
    (provider, key) across the whole registry."""
    providers = _load_providers()["providers"]
    owners: dict = {}
    for provider, paths in _collect_sweep_paths(providers).items():
        for key, rel in paths.items():
            owners.setdefault(rel, []).append(f"{provider}:{key}")

    collisions = {p: who for p, who in owners.items() if len(who) > 1}
    assert not collisions, (
        f"Provider path collisions in config/ai-providers.yaml: {collisions}"
    )


def test_intentionally_shared_context_file_agents_md():
    """context_file is EXCLUDED from the sweep — AGENTS.md is the documented
    multi-provider context convergence; assert the exact documented sharer set
    instead of silently allowing arbitrary overlap."""
    providers = _load_providers()["providers"]
    sharers = sorted(p for p, pcfg in providers.items()
                     if pcfg.get("context_file") == "AGENTS.md")
    assert sharers == sorted(_INTENTIONAL_AGENTS_MD_SHARERS)
    # Claude keeps its dedicated context file.
    assert providers["Claude"]["context_file"] == "CLAUDE.md"


def test_checkpoint_dir_meta_viz_shared_by_all_providers():
    """checkpoint_dir .meta-viz is EXCLUDED from the sweep — the viz checkpoint
    dir is deliberately shared infrastructure across all providers."""
    providers = _load_providers()["providers"]
    for provider, pcfg in providers.items():
        assert pcfg.get("checkpoint_dir") == ".meta-viz", (
            f"{provider}: checkpoint_dir must stay the shared .meta-viz"
        )


def test_codex_cross_tool_skills_dir_is_codex_only():
    """.agents/skills is the cross-tool Codex convention — no other provider
    may claim it (belt-and-braces on top of the sweep for the one path whose
    owner is NOT the provider's own dot-directory)."""
    providers = _load_providers()["providers"]
    assert providers["Codex"]["skills_dir"] == ".agents/skills"
    claimants = [p for p, pcfg in providers.items()
                 if pcfg.get("skills_dir") == ".agents/skills"]
    assert claimants == ["Codex"]
