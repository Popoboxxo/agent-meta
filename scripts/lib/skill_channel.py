"""Shared 'channel: skill' routing for rule-emitting registries.

Any registry that emits provider rule files — rules.py's plain rules/ layer,
mcp.py's mcp-<server>.md, external_tools.py's tool-<name>.md — can opt a rule
into rendering as <skills_dir>/<rule-stem>/SKILL.md instead of a plain
<rules_dir>/<rule-stem>.md file, for providers with real Skill lazy-loading
support (see PROVIDERS). This module centralizes the write + stale-cleanup +
shared-managed-index bookkeeping so all three call sites stay consistent.

Rule options come from rules.py::resolve_rules() (config/rules-presets.yaml +
project.yaml overrides), keyed by the rule's *output filename stem* — plain
rules use their own stem (e.g. "sync-interface"); mcp/tool-generated rules
use their prefixed stem (e.g. "mcp-honcho", "tool-graphify") so one flat
rules-preset config can address all three channels uniformly.
"""
from __future__ import annotations

from pathlib import Path

from .io import safe_path, write_checked
from .log import SyncLog

# Providers for which channel: skill renders to <skills_dir>/<name>/SKILL.md.
# Deliberately restricted — Gemini/Copilot/Mammouth have unclear or outdated
# native Skill support per the provider-capability matrix; no scope expansion
# beyond what's verified working (Claude Code Skills). Opencode is NOT
# included despite sharing the skills_dir convention: every call site that
# would exercise this channel (mcp.py::generate_mcp_artifacts,
# external_tools.py::generate_external_tool_artifacts, sync.py's sync_rules()
# call sites) is gated behind pc.get("has_rules"), and Opencode's has_rules
# is false (rules are embedded into AGENTS.md, no native rules dir) — so
# including it here would be a dead, unreachable promise. Wiring channel:
# skill to work independent of has_rules is a real, separate feature change,
# not done here.
PROVIDERS = {"Claude"}


def provider_supports_skill_channel(provider: str, pc: dict) -> bool:
    """Whether channel: skill renders to <skills_dir>/<name>/SKILL.md for this provider."""
    if provider not in PROVIDERS:
        return False
    return bool(pc.get("skills_dir"))


def yaml_quote(value: str) -> str:
    """Double-quote a scalar for safe inline embedding in generated YAML frontmatter."""
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def first_body_line_after_h1(content: str) -> str:
    """Fallback one-line description: first non-empty, non-heading body line
    after the '# Title' H1 heading (blockquote '>' prefix stripped)."""
    lines = content.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.strip().startswith("# "):
            start = i + 1
            break
    for line in lines[start:]:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped.lstrip(">").strip()
    return ""


def resolve_skill_description(opts: dict, content: str) -> str:
    """Resolve a one-line description for a rule.

    Precedence: explicit 'skill-description' option (rules-presets.yaml) >
    first body line after the rule's H1 heading.
    """
    explicit = (opts.get("skill-description") or "").strip()
    if explicit:
        return explicit
    return first_body_line_after_h1(content)


def build_skill_frontmatter(name: str, description: str, body: str) -> str:
    """Build SKILL.md content: YAML frontmatter (name + description) followed
    by the unmodified rule body, per the Claude Code Skill format."""
    desc = description or name
    return f"---\nname: {name}\ndescription: {yaml_quote(desc)}\n---\n\n{body}"


def write_skill_channel_rule(
    rule_stem: str,
    content: str,
    opts: dict,
    skills_target_dir: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    src_label: str,
) -> None:
    """Write <skills_target_dir>/<rule_stem>/SKILL.md.

    Caller must already have confirmed provider_supports_skill_channel() and
    opts.get('channel') == 'skill'.
    """
    description = resolve_skill_description(opts, content)
    skill_content = build_skill_frontmatter(rule_stem, description, content)
    skill_target_path = safe_path(skills_target_dir, rule_stem, "SKILL.md")
    rel_out = str(skill_target_path.relative_to(project_root))
    if not dry_run:
        skill_target_path.parent.mkdir(parents=True, exist_ok=True)
    if write_checked(skill_target_path, skill_content, log, src_label, dry_run=dry_run):
        log.action("WRITE", rel_out, src_label)
    else:
        log.skip(rel_out, "unchanged")


def cleanup_stale_skill_channel_rules(
    skills_target_dir: Path,
    project_root: Path,
    universe: set[str],
    now_managed: set[str],
    log: SyncLog,
    dry_run: bool,
    reason: str,
) -> None:
    """Delete SKILL.md (+ its now-empty directory) for rule stems that fell
    out of now_managed but are within this caller's universe of possible
    names (scoping avoids touching entries owned by a different writer of
    the same shared skills_dir index — see skills._write_skills_managed_index).
    """
    from .skills import _read_skills_managed_index

    previously_managed = _read_skills_managed_index(skills_target_dir) & universe
    for stale_stem in sorted(previously_managed - now_managed):
        stale_skill_md = safe_path(skills_target_dir, stale_stem, "SKILL.md")
        if stale_skill_md.exists():
            log.action("DELETE", str(stale_skill_md.relative_to(project_root)), reason)
            if not dry_run:
                stale_skill_md.unlink()
                stale_dir = stale_skill_md.parent
                try:
                    if stale_dir.exists() and not any(stale_dir.iterdir()):
                        stale_dir.rmdir()
                except OSError:
                    pass


def sweep_orphan_skill_channel_rules(
    project_root: Path,
    skills_target_dir: Path,
    union_universe: set[str],
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Delete skill-channel orphans: index entries NO writer claims anymore.

    Every writer of the shared ``<skills_dir>/.agent-meta-managed`` index
    cleans only within its own current universe (merge-mode, see
    ``skills._write_skills_managed_index``). A stem that disappears from ALL
    sources — e.g. a rule file deleted from ``rules/`` (issue #437:
    python-conventions), a server removed from ``mcp-registry.yaml`` — is in
    nobody's universe, so the per-writer cleanups above never touch it and
    its SKILL.md stays in the always-scanned skills_dir forever: a dead,
    stale entry in every agent context. The sweep closes that gap: anything
    OUTSIDE the union of all writers' possible stems (rules sources + mcp
    registry + external-tools registry + skills registry — see
    sync_pipeline._skill_channel_universe) is removed together with its
    index entry; anything any writer could still own is protected.
    """
    from .skills import _read_skills_managed_index, _write_skills_managed_index

    orphans = _read_skills_managed_index(skills_target_dir) - union_universe
    if not orphans:
        return
    for stale_stem in sorted(orphans):
        stale_skill_md = safe_path(skills_target_dir, stale_stem, "SKILL.md")
        if stale_skill_md.exists():
            log.action(
                "DELETE", str(stale_skill_md.relative_to(project_root)),
                "skill-channel orphan — stem no longer managed by any source "
                "(removed from rules/mcp/tools/skills sources)",
            )
            if not dry_run:
                stale_skill_md.unlink()
                stale_dir = stale_skill_md.parent
                try:
                    if stale_dir.exists() and not any(stale_dir.iterdir()):
                        stale_dir.rmdir()
                except OSError:
                    pass
    # Drop the orphan entries from the shared index. Merge-mode with
    # universe=orphans and an empty now_managed set removes exactly these
    # entries — other writers' entries survive untouched; an index that ends
    # up empty is deleted by _write_skills_managed_index.
    _write_skills_managed_index(skills_target_dir, set(), dry_run, universe=orphans)


def write_skill_channel_managed_index(
    skills_target_dir: Path,
    now_managed: set[str],
    dry_run: bool,
    universe: set[str],
) -> None:
    """Merge now_managed into skills_target_dir's shared managed index,
    scoped to `universe` (see skills._write_skills_managed_index)."""
    from .skills import _write_skills_managed_index

    _write_skills_managed_index(skills_target_dir, now_managed, dry_run, universe=universe)
