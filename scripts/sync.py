#!/usr/bin/env python3
"""
agent-meta sync.py
==================
Generates .claude/agents/*.md for a project from agent-meta sources.
Manages .claude/3-project/<prefix>-<role>-ext.md extension files.

Usage:
  python .agent-meta/scripts/sync.py --config agent-meta.config.json
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --init
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --only-variables
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext <role>
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --update-ext
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --dry-run

Extension files (.claude/3-project/<prefix>-<role>-ext.md):
  - Created by --create-ext <role> (or --create-ext all)
  - Contain a managed block (<!-- agent-meta:managed-begin/end -->) with
    auto-generated context from config variables — updated by --update-ext
  - Contain a project section below the managed block — never touched
  - The generated agent reads the extension file at startup via Extension-Hook
"""

import argparse
import json
import re
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
CLAUDE_EXT_DIR = ".claude/3-project"
LOGFILE = "sync.log"

# Maps role name to the output filename in .claude/agents/ (no prefix)
ROLE_MAP = {
    "orchestrator":  "orchestrator",
    "developer":     "developer",
    "tester":        "tester",
    "validator":     "validator",
    "requirements":  "requirements",
    "documenter":    "documenter",
    "release":       "release",
    "docker":        "docker",
    "meta-feedback": "meta-feedback",
}

EXT_SUFFIX = "-ext"
MANAGED_BEGIN = "<!-- agent-meta:managed-begin -->"
MANAGED_END   = "<!-- agent-meta:managed-end -->"

# Managed block content template — uses {{PLATZHALTER}} from config variables
# This is what gets updated on --update-ext. Keep it concise and useful.
MANAGED_BLOCK_TEMPLATE = """\
<!-- agent-meta:managed-begin -->
<!-- Dieser Block wird von sync.py bei --update-ext automatisch aktualisiert. -->
<!-- Projektspezifische Ergänzungen gehören in den Abschnitt UNTERHALB dieser Markierung. -->

**Projekt:** {{PROJECT_NAME}} | **Plattform:** {{PLATFORM}} | **Runtime:** {{RUNTIME}}
**Build:** `{{BUILD_COMMAND}}` | **Test:** `{{TEST_COMMAND}}`
<!-- agent-meta:managed-end -->"""

PROJECT_SECTION_STUB = """\

---

## Projektspezifische Erweiterungen

<!-- Dieser Abschnitt wird von sync.py NIE verändert. -->
<!-- Füge hier projektspezifisches Wissen, Regeln und Patterns hinzu. -->
"""


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
        self.actions.append(f"[{tag:<8}]  {target:<50}  ({source})")

    def warn(self, message: str):
        self.warnings.append(f"[WARN]   {message}")
        print(f"  ⚠  {message}", file=sys.stderr)

    def skip(self, target: str, reason: str):
        self.skipped.append(f"[SKIP]   {target:<50}  ({reason})")

    def write(self, log_path: Path, config_path: str, source_version: str,
              mode: str, platforms: list[str], dry_run: bool):
        lines = [
            "=" * 60,
            f"agent-meta sync — {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
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
            lines += ["", "SKIPPED", "-------"]
            lines += self.skipped

        if self.warnings:
            lines += ["", "WARNINGS", "--------"]
            lines += self.warnings
        else:
            lines += ["", "WARNINGS", "--------", "(none)"]

        lines += [
            "",
            "SUMMARY",
            "-------",
            f"{len(self.actions)} action(s)  |  {len(self.skipped)} skipped  |  {len(self.warnings)} warning(s)",
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
    return script_path.parent.parent


def read_version(agent_meta_root: Path) -> str:
    version_file = agent_meta_root / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "unknown"


def build_agent_table(config: dict, agent_meta_root: Path) -> tuple[str, list[str]]:
    """Generate markdown table for {{AGENT_TABLE}}. Returns (table, unmapped_warnings)."""
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)

    rows = []
    unmapped = []
    for role, source_path in sorted(overrides.items()):
        filename = target_filename(role)
        if not filename:
            unmapped.append(
                f"Rolle '{role}' ({source_path.name}) nicht in ROLE_MAP — in AGENT_TABLE übersprungen"
            )
            continue
        agent_name = Path(filename).stem
        layer = source_path.parts[-2]
        rows.append(f"| `{agent_name}` | `{source_path.name}` | {layer} |")

    header = "| Agent | Quelle | Layer |\n|-------|--------|-------|"
    return header + "\n" + "\n".join(rows), unmapped


def build_variables(config: dict, agent_meta_root: Path) -> tuple[dict, list[str]]:
    """Returns (variables_dict, pre_warnings)."""
    variables = {}
    project = config.get("project", {})
    variables["PREFIX"]       = project.get("prefix", "")
    variables["PROJECT_SHORT"] = project.get("short", "")
    variables["PROJECT_NAME"]  = project.get("name", "")
    variables["AGENT_META_VERSION"] = read_version(agent_meta_root)
    variables["AGENT_META_DATE"]    = datetime.now().strftime("%Y-%m-%d")
    agent_table, unmapped = build_agent_table(config, agent_meta_root)
    variables["AGENT_TABLE"] = agent_table
    variables.update(config.get("variables", {}))
    return variables, unmapped


def substitute(text: str, variables: dict, source_label: str, log: SyncLog) -> str:
    """Replace {{VAR}} occurrences. Warn for missing variables."""
    def replacer(match):
        key = match.group(1)
        if key in variables:
            return variables[key]
        log.warn(f"Variable {key} nicht in config — Platzhalter bleibt in: {source_label}")
        return match.group(0)
    return re.sub(r"\{\{([A-Z0-9_]+)\}\}", replacer, text)


def extract_frontmatter_field(content: str, field: str) -> str | None:
    """Extract a single-line YAML frontmatter field value (unquoted or quoted)."""
    match = re.search(
        rf'^{re.escape(field)}:\s*"?([^"\n]+)"?\s*$',
        content, flags=re.MULTILINE,
    )
    return match.group(1).strip() if match else None


def build_frontmatter(content: str, name: str, description: str,
                      generated_from: str | None = None) -> str:
    """Replace name and description in YAML frontmatter.

    Preserves existing version/based-on fields.
    Inserts/updates generated-from when generated_from is provided.
    """
    content = re.sub(
        r"(^---\n.*?^name:\s*)(.+?)(\n)",
        lambda m: f"{m.group(1)}{name}{m.group(3)}",
        content, count=1, flags=re.MULTILINE | re.DOTALL,
    )
    content = re.sub(
        r"(^description:\s*\")(.+?)(\"\n)",
        lambda m: f'{m.group(1)}{description}{m.group(3)}',
        content, count=1, flags=re.MULTILINE,
    )
    if generated_from is not None:
        # Update existing generated-from field, or insert after description line
        if re.search(r"^generated-from:", content, flags=re.MULTILINE):
            content = re.sub(
                r'^generated-from:.*$',
                f'generated-from: "{generated_from}"',
                content, count=1, flags=re.MULTILINE,
            )
        else:
            content = re.sub(
                r'(^description:.*\n)',
                rf'\1generated-from: "{generated_from}"\n',
                content, count=1, flags=re.MULTILINE,
            )
    return content


def target_filename(role: str) -> str | None:
    name = ROLE_MAP.get(role)
    return (name + ".md") if name else None


def ext_target_filename(role: str, prefix: str) -> str:
    """Extension file name: <prefix>-<role>-ext.md (or <role>-ext.md if no prefix)."""
    if prefix:
        return f"{prefix}-{role}{EXT_SUFFIX}.md"
    return f"{role}{EXT_SUFFIX}.md"


def role_from_platform_file(filename: str, platforms: list[str]) -> str | None:
    stem = Path(filename).stem
    for platform in platforms:
        if stem.startswith(f"{platform}-"):
            return stem[len(platform) + 1:]
    return None


# ---------------------------------------------------------------------------
# Managed block helpers
# ---------------------------------------------------------------------------

def render_managed_block(variables: dict, source_label: str, log: SyncLog) -> str:
    """Render the managed block content from config variables."""
    content = substitute(MANAGED_BLOCK_TEMPLATE, variables, source_label, log)
    return content


def update_managed_block(existing: str, new_managed: str) -> str:
    """Replace the managed block in an existing extension file."""
    pattern = re.compile(
        r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
        re.DOTALL,
    )
    if pattern.search(existing):
        return pattern.sub(new_managed, existing, count=1)
    # No block found — prepend (should not happen in normal flow)
    return new_managed + "\n\n" + existing


# ---------------------------------------------------------------------------
# Sync logic
# ---------------------------------------------------------------------------

def collect_sources(
    agent_meta_root: Path, platforms: list[str]
) -> tuple[dict[str, Path], set[str]]:
    """
    Returns (overrides, known_ext_roles).

    overrides: role → source_path for generated agents (.claude/agents/)
      Priority: 1-generic < 2-platform < 3-project/<role>.md (full override)

    known_ext_roles: roles that have a 3-project/<role>-ext.md in meta-repo.
      These are NOT used as templates — just signals that the role supports extensions.
      (Currently unused since 3-project/ in meta-repo has no templates by design.)
    """
    overrides: dict[str, Path] = {}
    known_ext_roles: set[str] = set()

    # 1. Generic agents
    generic_dir = agent_meta_root / AGENTS_DIR / GENERIC_DIR
    for f in sorted(generic_dir.glob("*.md")):
        overrides[f.stem] = f

    # 2. Platform agents
    platform_dir = agent_meta_root / AGENTS_DIR / PLATFORM_DIR
    for platform in platforms:
        for f in sorted(platform_dir.glob(f"{platform}-*.md")):
            role = role_from_platform_file(f.name, platforms)
            if role:
                overrides[role] = f

    # 3. Project-level agents (in meta-repo 3-project/)
    project_dir = agent_meta_root / AGENTS_DIR / PROJECT_DIR
    if project_dir.exists():
        for f in sorted(project_dir.glob("*.md")):
            stem = f.stem
            if stem.endswith(EXT_SUFFIX):
                known_ext_roles.add(stem[: -len(EXT_SUFFIX)])
            else:
                overrides[stem] = f

    return overrides, known_ext_roles


def sync_agents(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Generate all .claude/agents/*.md files."""
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    target_dir = project_root / CLAUDE_AGENTS_DIR

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    project_name = config["project"]["name"]
    for role, source_path in overrides.items():
        filename = target_filename(role)
        if not filename:
            log.skip(str(source_path.name), "keine Rolle in ROLE_MAP")
            continue

        target_path = target_dir / filename
        content = source_path.read_text(encoding="utf-8")
        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, "version")
        content = substitute(content, variables, rel_source, log)
        name = Path(filename).stem
        layer = source_path.parts[-2]  # "1-generic" or "2-platform"
        source_label = f"{layer}/{source_path.name}"
        generated_from = f"{source_label}@{source_version}" if source_version else source_label
        content = build_frontmatter(content, name, f"Agent für {project_name}.",
                                    generated_from=generated_from)

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        log.action("WRITE", str(target_path.relative_to(project_root)), rel_label)
        if not dry_run:
            target_path.write_text(content, encoding="utf-8")


def create_extension(
    project_root: Path,
    config: dict,
    variables: dict,
    role: str,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/3-project/<prefix>-<role>-ext.md if it does not exist yet."""
    if role not in ROLE_MAP:
        print(f"  ✗  Unbekannte Rolle '{role}'. Gültige Rollen: {', '.join(ROLE_MAP)}", file=sys.stderr)
        return

    prefix = config["project"].get("prefix", "")
    filename = ext_target_filename(role, prefix)
    target_path = project_root / CLAUDE_EXT_DIR / filename

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)), "Extension existiert bereits — nutze --update-ext zum Aktualisieren")
        return

    managed = render_managed_block(variables, f"--create-ext {role}", log)
    content = managed + PROJECT_SECTION_STUB

    log.action("CREATE", str(target_path.relative_to(project_root)), f"generated for role '{role}'")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def update_extensions(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Update the managed block in all existing extension files."""
    ext_dir = project_root / CLAUDE_EXT_DIR
    if not ext_dir.exists():
        log.skip(CLAUDE_EXT_DIR, "Verzeichnis nicht vorhanden — keine Extensions zum Aktualisieren")
        return

    for ext_file in sorted(ext_dir.glob(f"*{EXT_SUFFIX}.md")):
        existing = ext_file.read_text(encoding="utf-8")
        new_managed = render_managed_block(variables, str(ext_file.name), log)
        new_content = update_managed_block(existing, new_managed)

        if new_content == existing:
            log.skip(str(ext_file.relative_to(project_root)), "managed block unverändert")
        else:
            log.action("UPDATE", str(ext_file.relative_to(project_root)), "managed block")
            if not dry_run:
                ext_file.write_text(new_content, encoding="utf-8")


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
        print("  ℹ  CLAUDE.md existiert bereits — übersprungen (nutze --only-variables)")
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
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
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
    parser.add_argument("--config", required=True,
                        help="Path to agent-meta.config.json")
    parser.add_argument("--init", action="store_true",
                        help="Also generate CLAUDE.md from template (only if not present)")
    parser.add_argument("--only-variables", action="store_true",
                        help="Only substitute {{VARIABLE}} in existing CLAUDE.md")
    parser.add_argument("--create-ext", metavar="ROLE",
                        help="Create extension file for ROLE (or 'all'). "
                             "Does not overwrite existing files.")
    parser.add_argument("--update-ext", action="store_true",
                        help="Update managed block in all existing extension files")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without writing files")
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
        only_variables(project_root, variables, log, args.dry_run)

    elif args.create_ext:
        mode = f"create-ext:{args.create_ext}"
        roles = list(ROLE_MAP.keys()) if args.create_ext == "all" else [args.create_ext]
        for role in roles:
            create_extension(project_root, config, variables, role, log, args.dry_run)

    elif args.update_ext:
        mode = "update-ext"
        update_extensions(project_root, variables, log, args.dry_run)

    else:
        mode = "init" if args.init else "sync"
        if args.init:
            init_claude_md(agent_meta_root, project_root, config, variables, log, args.dry_run)
        sync_agents(agent_meta_root, project_root, config, variables, log, args.dry_run)

    log_path = project_root / LOGFILE
    log.write(log_path, args.config, source_version, mode, platforms, args.dry_run)


if __name__ == "__main__":
    main()
