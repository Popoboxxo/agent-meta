"""Rules layer: collect, sync, speech-mode, create."""

import sys
from pathlib import Path

from .io import _load_yaml_or_json
from .log import SyncLog

RULES_DIR = "rules"
CLAUDE_RULES_DIR = ".claude/rules"
SPEECH_RULE_FILENAME = "speech-mode.md"
SPEECH_DIR = "speech"

RULES_PRESETS_CONFIG_YAML = "config/rules-presets.yaml"

# Providers that support alwaysApply frontmatter
_ALWAYS_APPLY_PROVIDERS = {"Claude", "Continue"}


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
    preset_name = config.get("rules-preset", "default")
    preset_values = presets.get(preset_name, {})

    if preset_name not in presets and preset_name != "default":
        print(f"  !  Unknown rules-preset '{preset_name}' — falling back to 'default'",
              file=sys.stderr)
        preset_values = {}

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


def _build_always_apply_frontmatter(content: str) -> str:
    """Prepend alwaysApply: false frontmatter to a rule file.

    If the file already has frontmatter, inject alwaysApply into it.
    Otherwise prepend a minimal frontmatter block.
    """
    if content.startswith("---"):
        # Already has frontmatter — inject alwaysApply: false after opening ---
        end = content.find("\n---", 3)
        if end != -1:
            fm = content[3:end]
            if "alwaysApply" not in fm:
                content = "---" + fm + "\nalwaysApply: false" + content[end:]
        return content
    # No frontmatter — prepend minimal block
    return "---\nalwaysApply: false\n---\n" + content


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
):
    """Copy rule files from agent-meta/rules/ layers to <rules_dir>/ in the project.

    Layer priority (highest wins for same output filename):
      2-platform  >  1-generic  >  0-external

    Rule options (from resolve_rules()):
      alwaysApply: false  → prepend frontmatter (Claude + Continue only)
      gemini: skip        → skip rule entirely for Gemini provider

    Project rules in .claude/rules/ that are NOT from agent-meta are never touched.
    Stale agent-meta-managed rules (tracked in <rules_dir>/.agent-meta-managed) are removed.
    """
    from .platform import substitute_platform
    from .config import substitute

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

    for source_path, output_name in sources:
        rule_stem = Path(output_name).stem
        opts = rule_options.get(rule_stem, {})

        # Provider-aware: skip rule entirely for Gemini if gemini: skip
        if provider == "Gemini" and opts.get("gemini") == "skip":
            log.skip(str((target_dir / output_name).relative_to(project_root)),
                     f"rules-preset: gemini: skip for '{rule_stem}'")
            continue

        target_path = target_dir / output_name
        source_content = source_path.read_text(encoding="utf-8")
        layer = source_path.parts[-2]
        rel_source = f"rules/{layer}/{source_path.name}"

        if variables is not None:
            source_content = substitute(source_content, variables, rel_source, log)

        if platform_vars is not None:
            source_content = substitute_platform(source_content, platform_vars, rel_source, log)

        # Provider-aware: inject alwaysApply: false for Claude + Continue
        if opts.get("alwaysApply") is False and provider in _ALWAYS_APPLY_PROVIDERS:
            source_content = _build_always_apply_frontmatter(source_content)
            log.info(str(target_path.relative_to(project_root)),
                     f"alwaysApply: false (rules-preset: '{config.get('rules-preset', 'default')}')")

        log.action("COPY", str(target_path.relative_to(project_root)),
                   f"rules/{layer}/{source_path.name}")
        now_managed.add(output_name)

        if not dry_run:
            target_path.write_text(source_content, encoding="utf-8")

    # Remove stale managed rules no longer in current sources
    for stale_name in sorted(previously_managed - now_managed):
        stale_path = target_dir / stale_name
        if stale_path.exists():
            log.action("DELETE", str(stale_path.relative_to(project_root)),
                       "rule removed from agent-meta sources")
            if not dry_run:
                stale_path.unlink()

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
        log.warn(f"speech-mode '{mode}': source file not found at {source_path} — skipping")
        return

    source_content = source_path.read_text(encoding="utf-8")
    log.action("COPY", str(target_path.relative_to(project_root)), f"speech/{mode}.md")

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)
        target_path.write_text(source_content, encoding="utf-8")

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
    target_path = project_root / CLAUDE_RULES_DIR / name

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
