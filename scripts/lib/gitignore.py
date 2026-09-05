"""Managed .gitignore entry computation (issue #557).

Pure helper functions that compute the entries for the agent-meta managed
.gitignore block. Extracted from sync.py so the derivation is unit-testable
without running a full sync.

Provider differences are expressed exclusively through config keys in
config/ai-providers.yaml (`provider_root_dirs`, `agents_dir`,
`gitignore_entries`) — never through `if provider == "Name"` branches in this
module (provider-agnostic policy).

Toggle semantics (`gitignore.ignore-provider-dirs: true` in project.yaml):
the managed block receives whole provider-root directory entries (`<root>/`)
instead of the provider-internal sub-path allowlist. Entries inside an
ignored provider root are redundant and filtered out. Repo-root files
(sync.log, CLAUDE.personal.md, .mcp.json, opencode.json, top-level context
files, ...) keep their per-category behavior.

Note on additivity: `ensure_gitignore_entries()` rewrites the managed block
exactly only on the Claude-gated path; other paths are additive. Existing
projects may therefore keep previously written sub-path entries after
enabling the toggle — they are harmless (redundant) until the block is
rewritten in exact mode.
"""
from __future__ import annotations

# Category fallback for Claude's gitignore_entries when the provider config
# carries none (mirrors the historical inline default in sync.py).
_CLAUDE_LOCAL_ENTRIES_FALLBACK: list[str] = [
    ".claude/settings.local.json",
    ".claude/agent-memory-local/",
    "CLAUDE.personal.md",
    "sync.log",
]


def _ensure_trailing_slash(path: str) -> str:
    """Return `path` with a guaranteed trailing slash (directory pattern)."""
    return path if path.endswith("/") else path + "/"


def _first_dot_prefixed_segment(path: str) -> str | None:
    """Return the first dot-prefixed segment of a relative path, or None.

    Example: ".claude/agents" -> ".claude"; "agents" -> None.
    """
    for segment in path.split("/"):
        if segment.startswith("."):
            return segment
    return None


def provider_root_dirs_for(provider_cfg: dict) -> list[str]:
    """Resolve the provider-root directory patterns for one provider.

    The explicit config key `provider_root_dirs` (list of directory paths)
    wins. Fallback derivation when the key is missing: the first
    dot-prefixed path segment of `agents_dir` (e.g. `.claude/agents` ->
    `.claude/`). Providers whose generated files do NOT live under a
    dot-directory — or under a dot-directory that is too broad for this
    purpose, e.g. Copilot's `.github/copilot/` inside `.github/` — must
    declare `provider_root_dirs` explicitly.
    """
    explicit = provider_cfg.get("provider_root_dirs")
    if isinstance(explicit, list) and explicit:
        return [_ensure_trailing_slash(str(d)) for d in explicit]
    agents_dir = provider_cfg.get("agents_dir")
    if not agents_dir:
        return []
    segment = _first_dot_prefixed_segment(str(agents_dir))
    return [_ensure_trailing_slash(segment)] if segment else []


def collect_provider_roots(
    providers: list[str],
    provider_config: dict,
) -> list[str]:
    """Ordered, de-duplicated provider-root patterns of the active providers."""
    roots: list[str] = []
    seen: set[str] = set()
    for prov in providers:
        for root in provider_root_dirs_for(provider_config.get(prov, {})):
            if root not in seen:
                seen.add(root)
                roots.append(root)
    return roots


def is_inside_provider_root(path: str, roots: list[str]) -> bool:
    """True when `path` is a provider root itself or lives inside one.

    Both arguments are gitignore-style relative paths; trailing slashes are
    insignificant (gitignore dir patterns end with `/`, file entries do not).
    """
    normalized = path.rstrip("/")
    for root in roots:
        root_dir = root.rstrip("/")
        if normalized == root_dir or normalized.startswith(root_dir + "/"):
            return True
    return False


def filter_redundant_provider_entries(
    entries: list[str],
    roots: list[str],
) -> list[str]:
    """Drop entries that sit inside an ignored provider root (redundant).

    A `.gitignore` entry like `.claude/agents/` has no effect of its own once
    the whole `.claude/` directory is ignored, so toggle mode removes it from
    the computed entry set. Entries outside every provider root pass through
    unchanged (order-preserving). With empty `roots` the input is returned
    unchanged.
    """
    if not roots:
        return list(entries)
    return [entry for entry in entries if not is_inside_provider_root(entry, roots)]


def compute_base_gitignore_entries(
    providers: list[str],
    provider_config: dict,
    gitignore_cfg: dict,
) -> list[str]:
    """Compute the base entries of the agent-meta managed .gitignore block.

    Covers the local/generated/settings categories plus user `custom_entries`
    — a faithful extraction of the previously inline sync.py logic, extended
    by the `gitignore.ignore-provider-dirs` toggle (issue #557):

    - Toggle off (default): identical to the historical behavior — only the
      sub-path allowlist is emitted, and `gitignore.exceptions` entries invert
      their category default.
    - Toggle on: whole provider-root directories (`<root>/`, resolved via
      `provider_root_dirs` or the agents_dir fallback) are emitted first and
      provider-internal entries from the categories are filtered out as
      redundant. Repo-root files keep their category behavior;
      `custom_entries` are never filtered (user-explicit).

    Note: sync.py applies the result only when Claude is an active provider
    (the exact-managed-block path is Claude-gated) — the same guard is kept
    here so the helper mirrors the historical behavior exactly.
    """
    if "Claude" not in providers:
        return []

    exceptions = gitignore_cfg.get("exceptions", [])
    ignore_provider_dirs = bool(gitignore_cfg.get("ignore-provider-dirs", False))
    roots = (
        collect_provider_roots(providers, provider_config)
        if ignore_provider_dirs
        else []
    )

    def _should_ignore(path: str, category_default: bool) -> bool:
        return not category_default if path in exceptions else category_default

    def _keep(path: str, category_default: bool) -> bool:
        if roots and is_inside_provider_root(path, roots):
            return False  # redundant: already covered by the provider-root entry
        return _should_ignore(path, category_default)

    entries: list[str] = []
    claude_pc = provider_config.get("Claude", {})

    # Whole provider-root directories (toggle mode only; exceptions respected —
    # e.g. `exceptions: [".claude/"]` keeps Claude's dirs committed).
    for root in roots:
        if _should_ignore(root, True):
            entries.append(root)

    # Category "local" (default true): personal/machine-local files. Repo-root
    # files (CLAUDE.personal.md, sync.log, .mcp.json) survive toggle mode; only
    # provider-internal candidates are filtered as redundant.
    cat_local = gitignore_cfg.get("local", True)
    local_candidates = claude_pc.get("gitignore_entries", _CLAUDE_LOCAL_ENTRIES_FALLBACK)
    for _p in local_candidates:
        if _keep(_p, cat_local):
            entries.append(_p)

    # Category "generated" (default false): generated directories. Repo-root
    # dirs (e.g. Codex `rules_dir: rules`) are NOT provider roots and keep
    # their category behavior — the toggle must never swallow them.
    cat_gen = gitignore_cfg.get("generated", False)
    for _prov in providers:
        _pc = provider_config.get(_prov, {})
        for _dir_key in ("agents_dir", "rules_dir", "hooks_dir"):
            _d = _pc.get(_dir_key)
            if _d and _keep(_d + "/", cat_gen):
                entries.append(_d + "/")
        if _pc.get("has_commands") and _pc.get("commands_dir"):
            _c = _pc["commands_dir"]
            if _keep(_c + "/", cat_gen):
                entries.append(_c + "/")

    # Category "settings" (default false): committed settings/context files.
    # Top-level context files (CLAUDE.md never, AGENTS.md/MAMMOUTH.md via the
    # settings category) keep their per-category behavior in toggle mode.
    cat_set = gitignore_cfg.get("settings", False)
    for _prov in providers:
        _pc = provider_config.get(_prov, {})
        _sf = _pc.get("settings_file")
        if _sf and _keep(_sf, cat_set):
            entries.append(_sf)
        _ctx = _pc.get("context_file")
        if _ctx and _ctx != "CLAUDE.md" and _keep(_ctx, cat_set):
            entries.append(_ctx)

    custom_entries = gitignore_cfg.get("custom_entries", [])
    if custom_entries:
        entries.extend(custom_entries)

    return entries
