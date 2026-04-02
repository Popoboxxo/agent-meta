#!/usr/bin/env python3
"""
agent-meta sync.py
==================
Generates .claude/agents/*.md for a project from agent-meta sources.

Usage:
  python .agent-meta/scripts/sync.py --config agent-meta.config.json
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --init
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --only-variables
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --dry-run
"""

import argparse
import json
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AGENTS_DIR = "agents"
GENERIC_DIR = "1-generic"
PLATFORM_DIR = "2-platform"
PROJECT_DIR = "3-project"
CLAUDE_AGENTS_DIR = ".claude/agents"
LOGFILE = "sync.log"

# Maps generic agent filename (stem) to the output filename pattern
# orchestrator is special: uses project.short instead of prefix
ROLE_MAP = {
    "orchestrator": "{short}",
    "developer":    "{prefix}-developer",
    "tester":       "{prefix}-tester",
    "validator":    "{prefix}-validator",
    "requirements": "{prefix}-requirements",
    "documenter":   "{prefix}-documenter",
    "release":      "{prefix}-release",
    "docker":       "{prefix}-docker",
}


# ---------------------------------------------------------------------------
# Log collector
# ---------------------------------------------------------------------------

class SyncLog:
    def __init__(self):
        self.actions: list[str] = []
        self.warnings: list[str] = []
        self.skipped: list[str] = []
        self.start_time = datetime.now()

    def action(self, tag: str, target: str, source: str):
        self.actions.append(f"[{tag:<6}]  {target:<50}  ({source})")

    def warn(self, message: str):
        self.warnings.append(f"[WARN]   {message}")
        print(f"  ⚠  {message}", file=sys.stderr)

    def skip(self, target: str, reason: str):
        self.skipped.append(f"[SKIP]   {target:<50}  ({reason})")

    def write(self, log_path: Path, config_path: str, source_version: str,
              mode: str, platforms: list[str], dry_run: bool):
        lines = [
            "=" * 53,
            f"agent-meta sync — {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 53,
            f"Config:    {config_path}",
            f"Source:    .agent-meta/ (v{source_version})",
            f"Mode:      {'DRY-RUN — ' if dry_run else ''}{mode}",
            f"Platforms: {', '.join(platforms) if platforms else '(none)'}",
            "",
            "ACTIONS",
            "-------",
        ]
        lines += self.actions
        if self.skipped:
            lines += self.skipped

        if self.warnings:
            lines += ["", "WARNINGS", "--------"]
            lines += self.warnings
        else:
            lines += ["", "WARNINGS", "--------", "(none)"]

        total = len(self.actions)
        skip_count = len(self.skipped)
        warn_count = len(self.warnings)
        lines += [
            "",
            "SUMMARY",
            "-------",
            f"{total} agent(s) processed  |  {skip_count} skipped  |  {warn_count} warning(s)",
            f"Logfile: {log_path}",
        ]

        content = "\n".join(lines) + "\n"
        if not dry_run:
            log_path.write_text(content, encoding="utf-8")
        print()
        print(content)


# ---------------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------------

def load_config(config_path: Path) -> dict:
    if not config_path.exists():
        print(f"ERROR: Config not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with config_path.open(encoding="utf-8") as f:
        return json.load(f)


def find_agent_meta_root(script_path: Path) -> Path:
    """agent-meta root is the parent of the scripts/ directory."""
    return script_path.parent.parent


def read_version(agent_meta_root: Path) -> str:
    """Read version from agent-meta's own package/version file if available."""
    version_file = agent_meta_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    # Fallback: read from config that was passed in
    return "unknown"


def build_agent_table(config: dict, agent_meta_root: Path) -> tuple[str, list[str]]:
    """Generate markdown table of active agents for {{AGENT_TABLE}}.

    Returns (table_markdown, list_of_unmapped_roles).
    Unmapped roles are roles found in source dirs but missing from ROLE_MAP.
    """
    platforms = config.get("platforms", [])
    sources = collect_sources(agent_meta_root, platforms)

    rows = []
    unmapped = []
    for role, source_path in sorted(sources.items()):
        filename = target_filename(role, config)
        if not filename:
            unmapped.append(f"Rolle '{role}' ({source_path.name}) nicht in ROLE_MAP — in AGENT_TABLE übersprungen")
            continue
        agent_name = Path(filename).stem
        layer = source_path.parts[-2]  # e.g. "1-generic" or "2-platform"
        rows.append(f"| `{agent_name}` | `{source_path.name}` | {layer} |")

    header = (
        "| Agent | Quelle | Layer |\n"
        "|-------|--------|-------|"
    )
    return header + "\n" + "\n".join(rows), unmapped


def build_variables(config: dict, agent_meta_root: Path) -> tuple[dict, list[str]]:
    """Merge all variable sources into one flat dict.

    Returns (variables, pre_warnings) where pre_warnings are issues found
    before the SyncLog exists (e.g. unmapped roles in AGENT_TABLE).
    """
    variables = {}
    # From project block
    project = config.get("project", {})
    variables["PREFIX"] = project.get("prefix", "")
    variables["PROJECT_SHORT"] = project.get("short", "")
    variables["PROJECT_NAME"] = project.get("name", "")
    # Auto-inject meta variables
    variables["AGENT_META_VERSION"] = read_version(agent_meta_root)
    variables["AGENT_META_DATE"] = datetime.now().strftime("%Y-%m-%d")
    agent_table, unmapped_warnings = build_agent_table(config, agent_meta_root)
    variables["AGENT_TABLE"] = agent_table
    # From variables block (overrides project block, but not auto-injected meta vars)
    variables.update(config.get("variables", {}))
    return variables, unmapped_warnings


def substitute(text: str, variables: dict, source_label: str, log: SyncLog) -> str:
    """Replace all {{VAR}} occurrences. Warn for missing variables."""
    def replacer(match):
        key = match.group(1)
        if key in variables:
            return variables[key]
        log.warn(
            f"Variable {key} nicht in config — Platzhalter bleibt in: {source_label}"
        )
        return match.group(0)  # leave placeholder intact

    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", replacer, text)


def build_frontmatter(content: str, name: str, description: str) -> str:
    """Replace name and description in YAML frontmatter."""
    content = re.sub(
        r"(^---\n.*?^name:\s*)(.+?)(\n)",
        lambda m: f"{m.group(1)}{name}{m.group(3)}",
        content,
        count=1,
        flags=re.MULTILINE | re.DOTALL,
    )
    content = re.sub(
        r"(^description:\s*\")(.+?)(\"\n)",
        lambda m: f'{m.group(1)}{description}{m.group(3)}',
        content,
        count=1,
        flags=re.MULTILINE,
    )
    return content


def target_filename(role: str, config: dict) -> str:
    prefix = config["project"]["prefix"]
    short = config["project"]["short"]
    pattern = ROLE_MAP.get(role)
    if not pattern:
        return None
    return pattern.format(prefix=prefix, short=short) + ".md"


def role_from_platform_file(filename: str, platforms: list[str]) -> str | None:
    """Extract role name from a platform file like 'sharkord-release.md' → 'release'."""
    stem = Path(filename).stem  # e.g. "sharkord-release"
    for platform in platforms:
        prefix = f"{platform}-"
        if stem.startswith(prefix):
            return stem[len(prefix):]  # e.g. "release"
    return None


# ---------------------------------------------------------------------------
# Sync logic
# ---------------------------------------------------------------------------

def collect_sources(agent_meta_root: Path, platforms: list[str]) -> dict[str, Path]:
    """
    Returns a dict: role → source_path
    Platform agents override generic ones. Project agents override platform ones.
    """
    sources: dict[str, Path] = {}

    # 1. Generic agents
    generic_dir = agent_meta_root / AGENTS_DIR / GENERIC_DIR
    for f in sorted(generic_dir.glob("*.md")):
        role = f.stem
        sources[role] = f

    # 2. Platform agents — override generic if role matches
    platform_dir = agent_meta_root / AGENTS_DIR / PLATFORM_DIR
    for platform in platforms:
        for f in sorted(platform_dir.glob(f"{platform}-*.md")):
            role = role_from_platform_file(f.name, platforms)
            if role:
                sources[role] = f

    # 3. Project-level agents — override everything
    project_dir = agent_meta_root / AGENTS_DIR / PROJECT_DIR
    if project_dir.exists():
        for f in sorted(project_dir.glob("*.md")):
            role = f.stem
            sources[role] = f

    return sources


def sync_agents(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    platforms = config.get("platforms", [])
    sources = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / CLAUDE_AGENTS_DIR

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    for role, source_path in sources.items():
        filename = target_filename(role, config)
        if not filename:
            log.skip(str(source_path.name), "keine Rolle in ROLE_MAP")
            continue

        target_path = target_dir / filename
        content = source_path.read_text(encoding="utf-8")

        # Substitute variables
        rel_source = str(source_path.relative_to(agent_meta_root))
        content = substitute(content, variables, rel_source, log)

        # Fix frontmatter name + description
        name = Path(filename).stem
        project_name = config["project"]["name"]
        description = f"Agent für {project_name}."
        content = build_frontmatter(content, name, description)

        rel_source_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        log.action("WRITE", str(target_path.relative_to(project_root)), rel_source_label)

        if not dry_run:
            target_path.write_text(content, encoding="utf-8")


def init_claude_md(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    template_path = agent_meta_root / "howto" / "CLAUDE.project-template.md"
    target_path = project_root / "CLAUDE.md"

    if target_path.exists():
        print(f"  ℹ  CLAUDE.md existiert bereits — übersprungen (nutze --only-variables um Platzhalter zu ersetzen)")
        log.skip("CLAUDE.md", "existiert bereits")
        return

    if not template_path.exists():
        log.warn(f"CLAUDE.project-template.md nicht gefunden in {template_path}")
        return

    content = template_path.read_text(encoding="utf-8")
    content = substitute(content, variables, "CLAUDE.project-template.md", log)
    log.action("INIT", "CLAUDE.md", "howto/CLAUDE.project-template.md")

    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def only_variables(
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Replace {{VARIABLE}} markers in existing CLAUDE.md only."""
    target_path = project_root / "CLAUDE.md"
    if not target_path.exists():
        print("  ✗  CLAUDE.md nicht gefunden — nutze --init für erstmalige Generierung")
        sys.exit(1)

    content = target_path.read_text(encoding="utf-8")
    new_content = substitute(content, variables, "CLAUDE.md", log)

    if new_content == content:
        log.action("SKIP", "CLAUDE.md", "keine offenen Platzhalter")
    else:
        log.action("WRITE", "CLAUDE.md", "variables aus config")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync agent-meta agents into a project."
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Path to agent-meta.config.json (relative to project root)",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help="Also generate CLAUDE.md from template (only if it does not exist yet)",
    )
    parser.add_argument(
        "--only-variables",
        action="store_true",
        help="Only substitute {{VARIABLE}} in existing CLAUDE.md — do not touch agents",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without writing any files",
    )
    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    agent_meta_root = find_agent_meta_root(script_path)
    project_root = Path(args.config).resolve().parent
    config_path = Path(args.config).resolve()

    config = load_config(config_path)
    variables, pre_warnings = build_variables(config, agent_meta_root)
    platforms = config.get("platforms", [])
    source_version = config.get("agent-meta-version", read_version(agent_meta_root))

    log = SyncLog()
    for w in pre_warnings:
        log.warn(w)

    if args.dry_run:
        print("DRY-RUN — keine Dateien werden geschrieben\n")

    if args.only_variables:
        mode = "only-variables"
        only_variables(project_root, config, variables, log, args.dry_run)
    else:
        mode = "init" if args.init else "sync"
        if args.init:
            init_claude_md(agent_meta_root, project_root, config, variables, log, args.dry_run)
        sync_agents(agent_meta_root, project_root, config, variables, log, args.dry_run)

    log_path = project_root / LOGFILE
    log.write(log_path, args.config, source_version, mode, platforms, args.dry_run)


if __name__ == "__main__":
    main()
