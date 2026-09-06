"""Rules layer: collect, sync, speech-mode, create."""
from __future__ import annotations

import sys
from pathlib import Path

from .frontmatter import _split_frontmatter
from .io import _load_yaml_or_json, safe_path, write_checked
from .log import SyncLog
from .registry_query import (
    build_mcp_guardrails_list,
    load_mcp_registry,
    resolve_active_mcp_servers,
)
from .variables import (
    _orch_mode_flags,
    _resolve_orch_mode,
    strip_inactive_conditional_blocks,
    substitute,
)
from .skill_channel import (
    cleanup_stale_skill_channel_rules,
    provider_supports_skill_channel,
    resolve_skill_description,
    write_skill_channel_managed_index,
    write_skill_channel_rule,
)
from .skill_channel import yaml_quote as _yaml_quote

RULES_DIR = "rules"
CLAUDE_RULES_DIR = ".claude/rules"
SPEECH_RULE_FILENAME = "speech-mode.md"
SPEECH_DIR = "speech"

RULES_PRESETS_CONFIG_YAML = "config/rules-presets.yaml"

# Providers that support alwaysApply frontmatter.
# Claude Code was removed (#Phase-C token-efficiency review, 2026-08-14):
# a fresh sync.py test-lab run confirmed alwaysApply: false has zero effect
# on Claude Code — it is a Cursor/Continue frontmatter convention Claude Code
# silently ignores, loading '.claude/rules/*.md' in full regardless. Keeping
# it there only added noise (and, worse, made the 'silent' preset *heavier*
# than 'default' because of the extra frontmatter bytes with no lazy-loading
# benefit). Continue does honor it — see _build_always_apply_frontmatter().
_ALWAYS_APPLY_PROVIDERS = {"Continue"}


def load_rules_presets(agent_meta_root: Path) -> dict:
    """Load config/rules-presets.yaml."""
    data, _ = _load_yaml_or_json(agent_meta_root / RULES_PRESETS_CONFIG_YAML)
    if not data:
        return {}
    presets = data.get("presets", {})
    return {k: v for k, v in presets.items() if not k.startswith("_")}


def resolve_rules(config: dict, agent_meta_root: Path) -> dict:
    """Resolve effective rule options from preset + project overrides.

    Returns dict of rule_stem -> options, e.g.:
      {"lifecycle-tasks": {"alwaysApply": False, "gemini": "skip"}}

    Precedence (highest to lowest):
      1. config["rules"][rule]        — project override
      2. rules-preset[rule]           — preset default
      3. {}                           — no options (always load, all providers)
    """
    presets = load_rules_presets(agent_meta_root)
    preset_name = config.get("rules-preset", "default") or "default"

    if preset_name not in presets and preset_name != "default":
        print(f"  !  Unknown rules-preset '{preset_name}' — falling back to 'default'",
              file=sys.stderr)
        preset_name = "default"

    preset_values = presets.get(preset_name, {})

    project_overrides = config.get("rules", {})

    # Merge: collect all known rule names from both preset and overrides
    all_rules = set(preset_values.keys()) | set(project_overrides.keys())

    resolved = {}
    for rule in all_rules:
        # Project override wins over preset
        if rule in project_overrides:
            resolved[rule] = dict(project_overrides[rule] or {})
        elif rule in preset_values:
            resolved[rule] = dict(preset_values[rule] or {})

    return resolved


def _build_always_apply_frontmatter(content: str, description: str = "") -> str:
    """Prepend alwaysApply: false (+ description) frontmatter to a rule file.

    Continue needs both alwaysApply: false AND a description to actually lazy-
    load a rule — alwaysApply: false alone is not sufficient for it to decide
    relevance. description is only added when non-empty and not already present.

    If the file already has frontmatter, inject the missing keys into it.
    Otherwise prepend a minimal frontmatter block.
    """
    if content.startswith("---"):
        # Already has frontmatter — inject missing keys after opening ---
        fm_block, body = _split_frontmatter(content)
        if not fm_block:
            return content
        inner = fm_block[3:-4]  # strip surrounding '---'/'\n---' fences
        addition = ""
        if "alwaysApply" not in inner:
            addition += "\nalwaysApply: false"
        if description and "description" not in inner:
            addition += f"\ndescription: {_yaml_quote(description)}"
        if addition:
            return "---" + inner + addition + "\n---" + body
        return content
    # No frontmatter — prepend minimal block
    fm_lines = ["alwaysApply: false"]
    if description:
        fm_lines.append(f"description: {_yaml_quote(description)}")
    return "---\n" + "\n".join(fm_lines) + "\n---\n" + content


def collect_rule_sources(agent_meta_root: Path, platforms: list[str]) -> list[tuple[Path, str]]:
    """Collect rule files from 0-external, 1-generic and 2-platform layers.

    Returns list of (source_path, output_filename) tuples.
    Later entries override earlier ones with the same output filename —
    platform rules override generic rules of the same name.
    """
    seen: dict[str, Path] = {}

    # 0-external: rules from external skill repos
    ext_rules_dir = agent_meta_root / RULES_DIR / "0-external"
    if ext_rules_dir.exists():
        for f in sorted(ext_rules_dir.glob("*.md")):
            seen[f.name] = f

    # 1-generic (skip _ prefix — reserved for lazy-load knowledge files)
    generic_dir = agent_meta_root / RULES_DIR / "1-generic"
    if generic_dir.exists():
        for f in sorted(generic_dir.glob("*.md")):
            if not f.name.startswith("_"):
                seen[f.name] = f

    # 2-platform (platform-prefixed, e.g. sharkord-security.md → security.md)
    # Skip _ prefix files — reserved for lazy-load knowledge files
    platform_dir = agent_meta_root / RULES_DIR / "2-platform"
    if platform_dir.exists():
        for platform in platforms:
            for f in sorted(platform_dir.glob(f"{platform}-*.md")):
                if not f.name.startswith("_"):
                    output_name = f.name[len(platform) + 1:]
                    seen[output_name] = f

    return [(src, name) for name, src in seen.items()]


def sync_rules(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    platform_vars: dict | None = None,
    variables: dict | None = None,
    rules_dir: str | None = None,
    provider: str = "Claude",
    provider_config: dict | None = None,
):
    """Copy rule files from agent-meta/rules/ layers to <rules_dir>/ in the project.

    Layer priority (highest wins for same output filename):
      2-platform  >  1-generic  >  0-external

    Rule options (from resolve_rules()):
      alwaysApply: false  → prepend frontmatter (Continue only)
      gemini: skip        → skip rule entirely for Gemini provider
      channel: skill       → render to <skills_dir>/<rule-stem>/SKILL.md instead
                             of <rules_dir>/<rule-stem>.md (Claude + Opencode only,
                             see _SKILL_CHANNEL_PROVIDERS); unsupported providers
                             fall back to the normal rules_dir file, unchanged.

    Project rules in .claude/rules/ that are NOT from agent-meta are never touched.
    Stale agent-meta-managed rules (tracked in <rules_dir>/.agent-meta-managed) are removed.
    channel: skill rules share <skills_dir>/.agent-meta-managed with the external-skill
    sync (scripts/lib/skills.py) via merge-mode writes — see skill_channel.py.
    """
    from .platform import substitute_platform

    pc = (provider_config or {}).get(provider, {})
    provider_vars = {
        'EXTENSION_DIR': pc.get('extension_dir', '.claude/3-project'),
        'SNIPPETS_DIR': pc.get('snippets_dir', '.claude/snippets'),
        'PENDING_TASKS_FILE': pc.get('pending_tasks_file', '.claude/pending-tasks.md'),
        'SKILLS_DIR': pc.get('skills_dir', '.claude/skills'),
        'ORCHESTRATOR_INVOCATION_HINT': pc.get('orchestrator_hint', '- Bitte wählt den Orchestrator-Agenten aus.'),
    }
    
    # Provider-specific orchestrator mode override
    orch_config = config.get("orchestrator", {})
    provider_override = orch_config.get("provider-overrides", {}).get(provider, {})
    _orch_mode = _resolve_orch_mode(orch_config, provider_override)
    provider_vars.update(_orch_mode_flags(_orch_mode))
    
    # Override hint if main-chat mode is active
    if _orch_mode == "main-chat":
        provider_vars["ORCHESTRATOR_INVOCATION_HINT"] = "- Du bist der Orchestrator! Befolge die Regeln in use-orchestrator.md."

    # MCP registry resolution comes from lib.registry_query (Issue #478) —
    # the plugins-free resolution layer. Importing from mcp.py here would
    # recreate the mcp/mcp_provider_config/rules cycle mcp_registry.py was
    # extracted to break (#613); registry_query sits below both.
    mcp_registry = load_mcp_registry(agent_meta_root, config, project_root)
    active_mcp_servers = resolve_active_mcp_servers(config, agent_meta_root, project_root, registry=mcp_registry)
    provider_vars['MCP_GUARDRAILS_LIST'] = build_mcp_guardrails_list(mcp_registry, active_mcp_servers)

    merged_vars = {**variables, **provider_vars} if variables is not None else provider_vars

    platforms = config.get("platforms", [])
    sources = collect_rule_sources(agent_meta_root, platforms)

    if not sources:
        return

    rule_options = resolve_rules(config, agent_meta_root)

    target_dir = project_root / (rules_dir or CLAUDE_RULES_DIR)
    managed_index_path = target_dir / ".agent-meta-managed"

    previously_managed: set[str] = set()
    if managed_index_path.exists():
        for line in managed_index_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                previously_managed.add(line)

    now_managed: set[str] = set()

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    # channel: skill bookkeeping — computed once, outside the loop, so the
    # post-loop stale-cleanup below is correct even on a run where nothing
    # is currently flagged (e.g. rules-preset just switched away from a
    # preset that used channel: skill).
    all_rule_stems = {Path(output_name).stem for _, output_name in sources}
    supports_skill_channel = provider_supports_skill_channel(provider, pc)
    skills_dir_rel = pc.get("skills_dir")
    skills_target_dir = (project_root / skills_dir_rel) if (skills_dir_rel and supports_skill_channel) else None
    now_managed_skill_rules: set[str] = set()

    for source_path, output_name in sources:
        rule_stem = Path(output_name).stem
        opts = rule_options.get(rule_stem, {})

        # Provider-aware: skip rule entirely for Gemini if gemini: skip
        if provider == "Gemini" and opts.get("gemini") == "skip":
            log.skip(str((target_dir / output_name).relative_to(project_root)),
                     f"rules-preset: gemini: skip for '{rule_stem}'")
            continue

        source_content = source_path.read_text(encoding="utf-8")
        layer = source_path.parts[-2]
        rel_source = f"rules/{layer}/{source_path.name}"
        src_label = f"rules/{layer}/{source_path.name}"

        source_content = substitute(source_content, merged_vars, rel_source, log)
        source_content = strip_inactive_conditional_blocks(source_content, merged_vars)

        if platform_vars is not None:
            source_content = substitute_platform(source_content, platform_vars, rel_source, log)

        # channel: skill — render into skills_dir instead of rules_dir, for
        # providers with real Skill lazy-loading support. Deliberately NOT
        # added to `now_managed` (rules_dir index): if this rule previously
        # rendered as a plain rules_dir file (preset changed since), the
        # normal stale-cleanup below removes that old copy automatically.
        if opts.get("channel") == "skill" and skills_target_dir is not None:
            now_managed_skill_rules.add(rule_stem)
            write_skill_channel_rule(
                rule_stem, source_content, opts, skills_target_dir, project_root,
                log, dry_run, src_label,
            )
            continue

        target_path = safe_path(target_dir, output_name)

        # Provider-aware: inject alwaysApply: false for Continue
        if opts.get("alwaysApply") is False and provider in _ALWAYS_APPLY_PROVIDERS:
            description = resolve_skill_description(opts, source_content)
            source_content = _build_always_apply_frontmatter(source_content, description)
            log.note(str(target_path.relative_to(project_root)),
                     f"alwaysApply: false (rules-preset: '{config.get('rules-preset', 'default')}')")

        rel_out = str(target_path.relative_to(project_root))
        now_managed.add(output_name)

        if write_checked(target_path, source_content, log, rel_source, dry_run=dry_run):
            log.action("COPY", rel_out, src_label)
        else:
            log.skip(rel_out, "unchanged")

    # Remove stale managed rules no longer in current sources
    # speech-mode.md is owned by sync_speech_mode (speech/ layer), not the rules/
    # hierarchy — never treat it as stale here or it gets deleted and recreated
    # on every sync (infinite drift).
    for stale_name in sorted(previously_managed - now_managed):
        if stale_name == SPEECH_RULE_FILENAME:
            continue
        stale_path = safe_path(target_dir, stale_name)
        if stale_path.exists():
            log.action("DELETE", str(stale_path.relative_to(project_root)),
                       "rule removed from agent-meta sources")
            if not dry_run:
                stale_path.unlink()

    # channel: skill stale-cleanup + shared managed-index merge in skills_dir.
    # Scoped to `all_rule_stems` (this caller's full possible name-space) so
    # entries owned by the external-skill sync (scripts/lib/skills.py) in the
    # same shared index are never touched.
    if skills_target_dir is not None:
        cleanup_stale_skill_channel_rules(
            skills_target_dir, project_root, all_rule_stems, now_managed_skill_rules,
            log, dry_run, "rule no longer routed to channel: skill",
        )
        write_skill_channel_managed_index(
            skills_target_dir, now_managed_skill_rules, dry_run, universe=all_rule_stems
        )

    if not dry_run and now_managed:
        managed_index_path.write_text("\n".join(sorted(now_managed)) + "\n", encoding="utf-8")


def sync_speech_mode(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    rules_dir: str | None = None,
):
    """Copy speech/<mode>.md to .claude/rules/speech-mode.md.

    - 'full' (default): removes any existing speech-mode rule (no rule = default behavior).
    - Any other mode: copies speech/<mode>.md as .claude/rules/speech-mode.md.

    The rule is tracked in .claude/rules/.agent-meta-managed so stale entries are
    cleaned up by sync_rules on the next run. We also handle it directly here for
    the 'full' -> 'full' no-op and 'full' -> remove transition.
    """
    mode = config.get("speech-mode", "full")
    target_dir = project_root / (rules_dir or CLAUDE_RULES_DIR)
    target_path = target_dir / SPEECH_RULE_FILENAME
    managed_index_path = target_dir / ".agent-meta-managed"

    if mode == "full":
        if target_path.exists():
            log.action("DELETE", str(target_path.relative_to(project_root)),
                       "speech-mode is 'full' — no rule needed")
            if not dry_run:
                target_path.unlink()
        else:
            log.skip(str(target_path.relative_to(project_root)),
                     "speech-mode is 'full' — no rule needed")
        if not dry_run and managed_index_path.exists():
            lines = [l for l in managed_index_path.read_text(encoding="utf-8").splitlines()
                     if l.strip() and l.strip() != SPEECH_RULE_FILENAME]
            managed_index_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return

    source_path = agent_meta_root / SPEECH_DIR / f"{mode}.md"
    if not source_path.exists():
        log.warning(f"speech-mode '{mode}': source file not found at {source_path} — skipping")
        return

    source_content = source_path.read_text(encoding="utf-8")
    rel_out = str(target_path.relative_to(project_root))
    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
    if write_checked(target_path, source_content, log, f"speech/{mode}.md", dry_run=dry_run):
        log.action("COPY", rel_out, f"speech/{mode}.md")
    else:
        log.skip(rel_out, "unchanged")

    if not dry_run:
        currently_managed: list[str] = []
        if managed_index_path.exists():
            currently_managed = [l.strip() for l in
                                  managed_index_path.read_text(encoding="utf-8").splitlines()
                                  if l.strip()]
        if SPEECH_RULE_FILENAME not in currently_managed:
            currently_managed.append(SPEECH_RULE_FILENAME)
            managed_index_path.write_text("\n".join(sorted(currently_managed)) + "\n",
                                          encoding="utf-8")


def create_rule(
    project_root: Path,
    name: str,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/rules/<name>.md as an empty template (never overwrites)."""
    if not name.endswith(".md"):
        name = f"{name}.md"
    target_path = safe_path(project_root, CLAUDE_RULES_DIR, name)

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)),
                 "rule already exists — edit it manually")
        return

    content = f"""\
# {Path(name).stem.replace('-', ' ').replace('_', ' ').title()}

<!-- This file lives in .claude/rules/ and is automatically loaded into every agent context. -->
<!-- Add project-specific rules, policies, and conventions here. -->

"""
    log.action("CREATE", str(target_path.relative_to(project_root)),
               f"--create-rule {name}")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
