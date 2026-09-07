"""Tests for the gitignore.ignore-provider-dirs toggle (issue #557).

The toggle switches the agent-meta managed .gitignore block from the
provider-internal sub-path allowlist to whole provider-root directories.
Covered cases:

(a) default off -> entries identical to the historical inline algorithm
(b) toggle on -> whole provider-root dir entries per provider, incl. the
    Copilot special case (`.github/copilot/`, NOT `.github/`) and Codex
    (`.codex/` + repo-root `.agents/`)
(c) top-level context files (CLAUDE.md, AGENTS.md, MAMMOUTH.md) and repo-root
    files (opencode.json, sync.log, CLAUDE.personal.md) keep their per-category
    behavior — never blanket-ignored via the toggle
(d) redundant sub-paths inside an ignored provider root are filtered out
(e) `gitignore.exceptions` interplay still respected

Run: python3 -m pytest tests/test_gitignore_provider_dirs.py -q
"""

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.gitignore import (  # noqa: E402
    collect_provider_roots,
    compute_base_gitignore_entries,
    filter_redundant_provider_entries,
    is_inside_provider_root,
    provider_root_dirs_for,
)

_PROVIDERS_CONFIG = _REPO_ROOT / "config" / "ai-providers.yaml"

ALL_PROVIDERS = [
    "Claude",
    "Gemini",
    "Opencode",
    "Continue",
    "Copilot",
    "Mammouth",
    "Codex",
    "ZCode",
    "KimiCode",
]


def _load_provider_config() -> dict:
    with _PROVIDERS_CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)["providers"]


def _legacy_base_entries(
    providers: list[str],
    provider_config: dict,
    gitignore_cfg: dict,
) -> list[str]:
    """Reference implementation of the historical inline sync.py logic
    (pre-issue-#557) — used to pin the default-off behavior exactly."""
    if "Claude" not in providers:
        return []
    claude_pc = provider_config.get("Claude", {})
    base: list[str] = []
    exceptions = gitignore_cfg.get("exceptions", [])

    def _should_ignore(path: str, category_default: bool) -> bool:
        return not category_default if path in exceptions else category_default

    cat_local = gitignore_cfg.get("local", True)
    local_candidates = claude_pc.get("gitignore_entries", [
        ".claude/settings.local.json",
        ".claude/agent-memory-local/",
        "CLAUDE.personal.md",
        "sync.log",
    ])
    for _p in local_candidates:
        if _should_ignore(_p, cat_local):
            base.append(_p)

    cat_gen = gitignore_cfg.get("generated", False)
    for _prov in providers:
        _pc = provider_config.get(_prov, {})
        for _dir_key in ("agents_dir", "rules_dir", "hooks_dir"):
            _d = _pc.get(_dir_key)
            if _d and _should_ignore(_d + "/", cat_gen):
                base.append(_d + "/")
        if _pc.get("has_commands") and _pc.get("commands_dir"):
            _c = _pc["commands_dir"]
            if _should_ignore(_c + "/", cat_gen):
                base.append(_c + "/")

    cat_set = gitignore_cfg.get("settings", False)
    for _prov in providers:
        _pc = provider_config.get(_prov, {})
        _sf = _pc.get("settings_file")
        if _sf and _should_ignore(_sf, cat_set):
            base.append(_sf)
        _ctx = _pc.get("context_file")
        if _ctx and _ctx != "CLAUDE.md" and _should_ignore(_ctx, cat_set):
            base.append(_ctx)

    custom_entries = gitignore_cfg.get("custom_entries", [])
    if custom_entries:
        base.extend(custom_entries)
    return base


# ---------------------------------------------------------------------------
# (a) default off -> entries identical to today
# ---------------------------------------------------------------------------


def test_default_off_matches_legacy_algorithm_claude_only():
    provider_config = _load_provider_config()
    gitignore_cfg: dict = {}
    providers = ["Claude"]
    assert compute_base_gitignore_entries(
        providers, provider_config, gitignore_cfg
    ) == _legacy_base_entries(providers, provider_config, gitignore_cfg)


def test_default_off_matches_legacy_all_providers_with_categories():
    provider_config = _load_provider_config()
    for gitignore_cfg in (
        {},
        {"generated": True},
        {"settings": True},
        {"generated": True, "settings": True},
        {"local": False},
        {"local": False, "generated": True, "settings": True},
        {"exceptions": ["sync.log", ".gemini/agents/"], "generated": True},
        {"custom_entries": ["build/cache/", "tmp/"]},
    ):
        providers = list(ALL_PROVIDERS)
        assert compute_base_gitignore_entries(
            providers, provider_config, gitignore_cfg
        ) == _legacy_base_entries(providers, provider_config, gitignore_cfg), (
            f"mismatch for gitignore_cfg={gitignore_cfg!r}"
        )


def test_default_off_sub_path_allowlist_still_emitted():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(["Claude"], provider_config, {})
    # Historical default entries (sub-path allowlist) must survive untouched.
    assert ".claude/settings.local.json" in entries
    assert ".claude/agent-memory-local/" in entries
    assert ".claude/pending-tasks.md" in entries
    assert "CLAUDE.personal.md" in entries
    assert "sync.log" in entries
    assert ".mcp.json" in entries


def test_toggle_off_by_explicit_false_is_identical_to_default():
    provider_config = _load_provider_config()
    providers = list(ALL_PROVIDERS)
    default = compute_base_gitignore_entries(providers, provider_config, {})
    explicit = compute_base_gitignore_entries(
        providers, provider_config, {"ignore-provider-dirs": False}
    )
    assert default == explicit


def test_without_claude_base_entries_stay_empty():
    """The exact-managed-block path is Claude-gated — preserved by the helper."""
    provider_config = _load_provider_config()
    assert compute_base_gitignore_entries(
        ["Gemini", "Opencode"], provider_config, {"ignore-provider-dirs": True}
    ) == []


# ---------------------------------------------------------------------------
# (b) toggle on -> whole provider-root dir entries
# ---------------------------------------------------------------------------


def _toggle_on_cfg(**extra) -> dict:
    cfg = {"ignore-provider-dirs": True}
    cfg.update(extra)
    return cfg


def test_toggle_on_emits_provider_root_dirs_for_every_provider():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        list(ALL_PROVIDERS), provider_config, _toggle_on_cfg()
    )
    for root in (
        ".claude/",
        ".gemini/",
        ".opencode/",
        ".continue/",
        ".github/copilot/",
        ".mammouth/",
        ".codex/",
        ".agents/",
        ".zcode/",
        ".kimi-code/",
    ):
        assert root in entries, f"missing provider root entry: {root}"


def test_toggle_on_copilot_ignores_only_copilot_subdir_not_github():
    """Ignoring `.github/` wholesale would also exclude GitHub workflows — the
    Copilot provider root must be the copilot subdirectory only."""
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        ["Claude", "Copilot"], provider_config, _toggle_on_cfg()
    )
    assert ".github/copilot/" in entries
    assert ".github/" not in entries


def test_toggle_on_codex_roots_include_agents_dir_but_never_rules():
    """Codex: `.codex/` plus repo-root `.agents/` (skills_dir). `rules/`
    (rules_dir at repo root) must NEVER become a provider root."""
    provider_config = _load_provider_config()
    roots = collect_provider_roots(["Codex"], provider_config)
    assert roots == [".codex/", ".agents/"]
    entries = compute_base_gitignore_entries(
        ["Claude", "Codex"], provider_config, _toggle_on_cfg(generated=True)
    )
    assert "rules/" in entries  # untouched: category-driven, not provider-root


def test_toggle_on_does_not_affect_repo_root_local_files():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        list(ALL_PROVIDERS), provider_config, _toggle_on_cfg()
    )
    assert "CLAUDE.personal.md" in entries
    assert "sync.log" in entries
    assert ".mcp.json" in entries


def test_fallback_derivation_from_agents_dir():
    """Providers without explicit provider_root_dirs derive the root from the
    first dot-prefixed segment of agents_dir."""
    assert provider_root_dirs_for({"agents_dir": ".claude/agents"}) == [".claude/"]
    assert provider_root_dirs_for({"agents_dir": ".future/agents"}) == [".future/"]
    # No dot-prefixed segment -> no derivable root.
    assert provider_root_dirs_for({"agents_dir": "agents"}) == []
    assert provider_root_dirs_for({}) == []
    # Explicit key wins over derivation.
    assert provider_root_dirs_for({
        "agents_dir": ".github/copilot/agents",
        "provider_root_dirs": [".github/copilot/"],
    }) == [".github/copilot/"]


def test_every_registered_provider_resolves_at_least_one_root():
    """The toggle must work for every provider in the registry without code
    changes (provider-agnostic policy)."""
    provider_config = _load_provider_config()
    for name, cfg in provider_config.items():
        roots = provider_root_dirs_for(cfg)
        assert roots, f"provider {name} yields no provider_root_dirs"
        for root in roots:
            assert root.endswith("/"), f"provider {name}: root '{root}' lacks trailing slash"


def test_collect_provider_roots_deduplicates_and_preserves_order():
    provider_config = {
        "A": {"agents_dir": ".shared/agents"},
        "B": {"agents_dir": ".shared/agents"},
        "C": {"agents_dir": ".other/agents"},
    }
    roots = collect_provider_roots(["A", "B", "C"], provider_config)
    assert roots == [".shared/", ".other/"]


# ---------------------------------------------------------------------------
# (c) top-level context files stay tracked / individually handled as before
# ---------------------------------------------------------------------------


def test_toggle_on_context_files_not_blanket_ignored_by_default():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        list(ALL_PROVIDERS), provider_config, _toggle_on_cfg()
    )
    for ctx in ("CLAUDE.md", "AGENTS.md", "MAMMOUTH.md", "opencode.json"):
        assert ctx not in entries, f"{ctx} must stay tracked with toggle on"


def test_toggle_on_settings_category_keeps_top_level_files_individually():
    """With gitignore.settings=true the top-level context/settings files are
    still individually ignored exactly as before — the toggle neither drops
    nor adds them."""
    provider_config = _load_provider_config()
    cfg = _toggle_on_cfg(settings=True)
    entries = compute_base_gitignore_entries(list(ALL_PROVIDERS), provider_config, cfg)
    legacy = _legacy_base_entries(list(ALL_PROVIDERS), provider_config, {"settings": True})
    for ctx in ("AGENTS.md", "MAMMOUTH.md", "opencode.json"):
        assert ctx in entries, f"{ctx} must stay individually ignored (settings=true)"
    # CLAUDE.md is never gitignored (handwritten sections) — before and after.
    assert "CLAUDE.md" not in entries
    assert "CLAUDE.md" not in legacy
    # Provider-internal settings/context files are redundant now.
    assert ".gemini/settings.json" not in entries
    assert ".continue/rules/project-context.md" not in entries
    assert ".continue/config.yaml" not in entries


# ---------------------------------------------------------------------------
# (d) redundant sub-paths inside an ignored root are filtered
# ---------------------------------------------------------------------------


def test_toggle_on_filters_provider_internal_local_entries():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        ["Claude"], provider_config, _toggle_on_cfg()
    )
    assert ".claude/settings.local.json" not in entries
    assert ".claude/agent-memory-local/" not in entries
    assert ".claude/pending-tasks.md" not in entries
    assert ".claude/" in entries


def test_toggle_on_filters_generated_dirs_inside_roots():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        list(ALL_PROVIDERS), provider_config, _toggle_on_cfg(generated=True)
    )
    for redundant in (
        ".claude/agents/",
        ".gemini/agents/",
        ".gemini/commands/",
        ".opencode/agents/",
        ".opencode/commands/",
        ".continue/rules/",
        ".github/copilot/rules/",
        ".mammouth/rules/",
        ".mammouth/hooks/",
        ".codex/hooks/",
        ".kimi-code/agents/",
        ".zcode/agents/",
    ):
        assert redundant not in entries, f"redundant entry survived: {redundant}"


def test_filter_redundant_provider_entries_for_extra_allowlist():
    """The per-provider gitignore_entries (extra allowlist) lose only their
    provider-internal entries; repo-root entries pass through unchanged."""
    provider_config = _load_provider_config()
    roots = collect_provider_roots(list(ALL_PROVIDERS), provider_config)
    extra = [
        "AGENTS.personal.md",
        ".opencode/settings.local.json",
        ".opencode/pending-tasks.md",
        ".opencode/mcp.local.json",
        ".gemini/settings.local.json",
        ".continue/config.local.yaml",
    ]
    filtered = filter_redundant_provider_entries(extra, roots)
    assert filtered == ["AGENTS.personal.md"]


def test_filter_redundant_provider_entries_noop_without_roots():
    entries = [".claude/agents/", "AGENTS.personal.md"]
    assert filter_redundant_provider_entries(entries, []) == entries


def test_is_inside_provider_root_edge_cases():
    roots = [".claude/", ".github/copilot/"]
    assert is_inside_provider_root(".claude/", roots)
    assert is_inside_provider_root(".claude/agents/", roots)
    assert is_inside_provider_root(".claude/settings.local.json", roots)
    assert is_inside_provider_root(".github/copilot/pending-tasks.md", roots)
    assert not is_inside_provider_root(".github/workflows/ci.yml", roots)
    assert not is_inside_provider_root("CLAUDE.personal.md", roots)
    assert not is_inside_provider_root("opencode.json", roots)


# ---------------------------------------------------------------------------
# (e) exceptions interplay still respected
# ---------------------------------------------------------------------------


def test_toggle_on_exceptions_still_invert_category_defaults():
    provider_config = _load_provider_config()
    cfg = _toggle_on_cfg(exceptions=["sync.log"])
    entries = compute_base_gitignore_entries(["Claude"], provider_config, cfg)
    assert "sync.log" not in entries  # local category (true) inverted
    assert "CLAUDE.personal.md" in entries


def test_toggle_on_exceptions_can_exclude_provider_root():
    provider_config = _load_provider_config()
    cfg = _toggle_on_cfg(exceptions=[".claude/"])
    entries = compute_base_gitignore_entries(
        ["Claude", "Gemini"], provider_config, cfg
    )
    assert ".claude/" not in entries
    assert ".gemini/" in entries


def test_exceptions_match_legacy_behavior_without_toggle():
    provider_config = _load_provider_config()
    for exceptions in (["sync.log"], ["CLAUDE.personal.md"], [".claude/agents/"]):
        cfg = {"exceptions": exceptions}
        providers = list(ALL_PROVIDERS)
        assert compute_base_gitignore_entries(
            providers, provider_config, cfg
        ) == _legacy_base_entries(providers, provider_config, cfg), (
            f"exceptions mismatch: {exceptions!r}"
        )


def test_exception_on_sub_path_inside_ignored_root_is_redundant():
    """Git cannot re-include a file inside an ignored directory, so excepting a
    sub-path under an ignored provider root is a no-op — the toggle filters the
    entry as redundant either way (documented behavior)."""
    provider_config = _load_provider_config()
    cfg = _toggle_on_cfg(
        local=False,  # entry would only be ignored via an exception otherwise
        exceptions=[".claude/settings.local.json"],
    )
    entries = compute_base_gitignore_entries(["Claude"], provider_config, cfg)
    assert ".claude/" in entries
    assert ".claude/settings.local.json" not in entries


# ---------------------------------------------------------------------------
# config invariants (ai-providers.yaml regression guards)
# ---------------------------------------------------------------------------


def test_providers_yaml_copilot_root_is_not_github():
    provider_config = _load_provider_config()
    assert provider_config["Copilot"].get("provider_root_dirs") == [".github/copilot/"]


def test_providers_yaml_codex_declares_both_roots():
    provider_config = _load_provider_config()
    assert provider_config["Codex"].get("provider_root_dirs") == [".codex/", ".agents/"]
