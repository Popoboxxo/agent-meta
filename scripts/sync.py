#!/usr/bin/env python3
"""
agent-meta sync.py
==================
Generates .claude/agents/*.md for a project from agent-meta sources.
Manages .claude/3-project/<prefix>-<role>-ext.md extension files.
Syncs snippets and external skill agents.

Usage:
  python .agent-meta/scripts/sync.py --config agent-meta.config.json
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --init
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --only-variables
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --create-ext <role>
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --update-ext
  python .agent-meta/scripts/sync.py --config agent-meta.config.json --dry-run
  python .agent-meta/scripts/sync.py --add-skill <repo-url> --skill-name <name>
                                      --source <path> --role <role> [--entry <file>]

External skills (external-skills.config.json):
  - Managed centrally in agent-meta (Modell A)
  - Each enabled skill generates a wrapper agent in .claude/agents/<role>.md
  - Skill files are copied to .claude/skills/<skill-name>/
  - Use --add-skill to register a new submodule + skill entry
  - Use enabled: true/false in external-skills.config.json to activate/deactivate
"""

import argparse
import json
import re
import subprocess
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
SNIPPETS_DIR = "snippets"
EXTERNAL_DIR = "0-external"
SKILL_WRAPPER = "_skill-wrapper.md"
EXTERNAL_SKILLS_CONFIG = "external-skills.config.json"
CLAUDE_AGENTS_DIR = ".claude/agents"
CLAUDE_EXT_DIR = ".claude/3-project"
CLAUDE_SNIPPETS_DIR = ".claude/snippets"
CLAUDE_SKILLS_DIR = ".claude/skills"
LOGFILE = "sync.log"

# Maps role name to the output filename in .claude/agents/ (no prefix)
ROLE_MAP = {
    "orchestrator":  "orchestrator",
    "developer":     "developer",
    "tester":        "tester",
    "validator":     "validator",
    "requirements":  "requirements",
    "ideation":      "ideation",
    "documenter":    "documenter",
    "release":       "release",
    "docker":        "docker",
    "meta-feedback":       "meta-feedback",
    "git":                 "git",
    "agent-meta-manager":  "agent-meta-manager",
    "feature":             "feature",
}

EXT_SUFFIX = "-ext"
MANAGED_BEGIN = "<!-- agent-meta:managed-begin -->"
MANAGED_END   = "<!-- agent-meta:managed-end -->"

# Managed block content template — uses {{PLATZHALTER}} from config variables
# This is what gets updated on --update-ext. Keep it concise and useful.
MANAGED_BLOCK_TEMPLATE = """\
<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on --update-ext. -->
<!-- Project-specific additions belong in the section BELOW this marker. -->

**Projekt:** {{PROJECT_NAME}} | **Plattform:** {{PLATFORM}} | **Runtime:** {{RUNTIME}}
**Build:** `{{BUILD_COMMAND}}` | **Test:** `{{TEST_COMMAND}}`
<!-- agent-meta:managed-end -->"""

PROJECT_SECTION_STUB = """\

---

## Projektspezifische Erweiterungen

<!-- This section is NEVER modified by sync.py. -->
<!-- Add project-specific knowledge, rules, and patterns here. -->
"""


# ---------------------------------------------------------------------------
# Log collector
# ---------------------------------------------------------------------------

class SyncLog:
    def __init__(self):
        self.actions: list[str] = []
        self.warnings: list[str] = []
        self.skipped: list[str] = []
        self.infos: list[str] = []
        self.start_time = datetime.now()

    def action(self, tag: str, target: str, source: str):
        self.actions.append(f"[{tag:<8}]  {target:<50}  ({source})")

    def warn(self, message: str):
        self.warnings.append(f"[WARN]   {message}")
        print(f"  !  {message}", file=sys.stderr)

    def skip(self, target: str, reason: str):
        self.skipped.append(f"[SKIP]   {target:<50}  ({reason})")

    def info(self, target: str, reason: str):
        self.infos.append(f"[INFO]   {target:<50}  ({reason})")

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
        if self.infos:
            lines += ["", "INFO", "----"]
            lines += self.infos

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
        print(f"ERROR: config not found: {config_path}", file=sys.stderr)
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


def build_agent_hints(config: dict, agent_meta_root: Path) -> str:
    """Generate agent usage hints for {{AGENT_HINTS}}.

    Reads hint (preferred) or description from each active agent's template frontmatter.
    If orchestrator is active, adds a prominent start hint.
    """
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    lines = []
    has_orchestrator = (
        "orchestrator" in overrides
        and (allowed_roles is None or "orchestrator" in allowed_roles)
    )
    if has_orchestrator:
        lines.append(
            "> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben."
        )
        lines.append("")

    lines.append("| Agent | Zuständigkeit |")
    lines.append("|-------|--------------|")
    for role, source_path in sorted(overrides.items()):
        if allowed_roles is not None and role not in allowed_roles:
            continue
        if not target_filename(role):
            continue
        content = source_path.read_text(encoding="utf-8")
        hint = extract_frontmatter_field(content, "hint") \
            or extract_frontmatter_field(content, "description") \
            or ""
        lines.append(f"| `{role}` | {hint} |")

    return "\n".join(lines)


def build_agent_table(config: dict, agent_meta_root: Path) -> tuple[str, list[str]]:
    """Generate markdown table for {{AGENT_TABLE}}. Returns (table, unmapped_warnings).

    Only includes roles present in config['roles'] whitelist (if set).
    """
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    rows = []
    unmapped = []
    for role, source_path in sorted(overrides.items()):
        if allowed_roles is not None and role not in allowed_roles:
            continue
        filename = target_filename(role)
        if not filename:
            unmapped.append(
                f"Role '{role}' ({source_path.name}) not in ROLE_MAP — skipped in AGENT_TABLE"
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
    variables["AGENT_HINTS"] = build_agent_hints(config, agent_meta_root)
    variables.update(config.get("variables", {}))
    # AI_PROVIDER: auto-inject from top-level config field (not nested in variables)
    if "AI_PROVIDER" not in variables:
        variables["AI_PROVIDER"] = config.get("ai-provider", "")
    return variables, unmapped


def substitute(text: str, variables: dict, source_label: str, log: SyncLog) -> str:
    """Replace {{VAR}} occurrences. Warn for missing variables.

    Escape syntax: {{%VAR%}} renders as {{VAR}} without substitution (for literal docs).
    """
    # First pass: resolve escaped literals {{% ... %}} → {{...}} (no substitution)
    text = re.sub(r"\{\{%([A-Z0-9_]+)%\}\}", r"{{\1}}", text)

    def replacer(match):
        key = match.group(1)
        if key in variables:
            return variables[key]
        log.warn(f"Variable {key} not in config — placeholder remains in: {source_label}")
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

    # Optional role whitelist — if "roles" key is absent, all roles are generated
    allowed_roles: set[str] | None = None
    if "roles" in config:
        allowed_roles = set(config["roles"])

    if not dry_run:
        target_dir.mkdir(parents=True, exist_ok=True)

    # Track which filenames will be written in this sync
    expected_filenames: set[str] = set()

    project_name = config["project"]["name"]
    for role, source_path in overrides.items():
        filename = target_filename(role)
        if not filename:
            log.skip(str(source_path.name), "role not in ROLE_MAP")
            continue

        if allowed_roles is not None and role not in allowed_roles:
            log.skip(str(target_dir / filename).replace(str(project_root) + "/", "").replace(str(project_root) + "\\", ""),
                     f"role '{role}' not in config['roles']")
            continue

        expected_filenames.add(filename)
        target_path = target_dir / filename
        content = source_path.read_text(encoding="utf-8")
        rel_source = str(source_path.relative_to(agent_meta_root))
        source_version = extract_frontmatter_field(content, "version")
        # Preserve template description; interpolate {{PROJECT_NAME}} if present
        template_description = extract_frontmatter_field(content, "description")
        description = (template_description or f"Agent for {project_name}.")
        description = description.replace("{{PROJECT_NAME}}", project_name)
        content = substitute(content, variables, rel_source, log)
        name = Path(filename).stem
        layer = source_path.parts[-2]  # "1-generic" or "2-platform"
        source_label = f"{layer}/{source_path.name}"
        generated_from = f"{source_label}@{source_version}" if source_version else source_label
        content = build_frontmatter(content, name, description,
                                    generated_from=generated_from)

        rel_label = str(source_path.relative_to(agent_meta_root / AGENTS_DIR))
        log.action("WRITE", str(target_path.relative_to(project_root)), rel_label)
        if not dry_run:
            target_path.write_text(content, encoding="utf-8")

    # Also track external skill agent filenames (they are not in overrides)
    ext_config = load_external_skills_config(agent_meta_root)
    project_skills = config.get("external-skills", {})
    for skill_name, skill_cfg in ext_config.get("skills", {}).items():
        if _skill_is_active(skill_name, skill_cfg, project_skills):
            role = skill_cfg.get("role", skill_name)
            expected_filenames.add(f"{role}.md")


    # Remove stale agent files that are no longer in the active role set
    if target_dir.exists():
        for existing_file in sorted(target_dir.glob("*.md")):
            if existing_file.name not in expected_filenames:
                log.action("DELETE", str(existing_file.relative_to(project_root)),
                           "role removed from config")
                if not dry_run:
                    existing_file.unlink()


def sync_snippets(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Copy snippet files from agent-meta/snippets/ to .claude/snippets/ in the project.

    Only copies snippets referenced via TESTER_SNIPPETS_PATH (or similar *_SNIPPETS_PATH
    variables) in the project config. Unknown snippet files are skipped.
    All referenced paths are resolved relative to agent-meta/snippets/.
    """
    variables = config.get("variables", {})
    snippets_root = agent_meta_root / SNIPPETS_DIR
    target_root = project_root / CLAUDE_SNIPPETS_DIR

    if not snippets_root.exists():
        return

    # Collect all *_SNIPPETS_PATH values from config variables
    snippet_paths: list[str] = [
        v for k, v in variables.items()
        if k.endswith("_SNIPPETS_PATH") and v
    ]

    if not snippet_paths:
        return

    for rel_path in snippet_paths:
        source_path = snippets_root / rel_path
        if not source_path.exists():
            log.warn(f"Snippet not found: snippets/{rel_path}")
            continue

        target_path = target_root / rel_path
        source_content = source_path.read_text(encoding="utf-8")
        snippet_version = extract_frontmatter_field(source_content, "version")
        version_label = f"@{snippet_version}" if snippet_version else ""

        log.action(
            "COPY",
            str(target_path.relative_to(project_root)),
            f"snippets/{rel_path}{version_label}",
        )
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(source_content, encoding="utf-8")


def _skill_is_active(skill_name: str, skill_cfg: dict, project_skills: dict) -> bool:
    """Return True if a skill should be generated for the current project.

    Two-gate check:
    1. approved: true in external-skills.config.json  (meta-maintainer quality gate)
    2. enabled:  true in agent-meta.config.json        (project opt-in)

    If project has no "external-skills" block at all, no skill is generated.
    """
    return (
        skill_cfg.get("approved", False)
        and project_skills.get(skill_name, {}).get("enabled", False)
    )


def load_external_skills_config(agent_meta_root: Path) -> dict:
    """Load external-skills.config.json from agent-meta root. Returns empty structure if not found."""
    config_path = agent_meta_root / EXTERNAL_SKILLS_CONFIG
    if not config_path.exists():
        return {"repos": {}, "skills": {}}
    with config_path.open(encoding="utf-8") as f:
        data = json.load(f)
    # Strip _comment keys
    return {
        "repos":   {k: v for k, v in data.get("repos", {}).items()   if not k.startswith("_")},
        "skills":  {k: v for k, v in data.get("skills", {}).items()  if not k.startswith("_")},
    }


def check_pinned_commits(ext_config: dict, agent_meta_root: Path, log: SyncLog) -> None:
    """Warn if any repo submodule is not at its pinned_commit."""
    for repo_name, repo_cfg in ext_config.get("repos", {}).items():
        pinned = repo_cfg.get("pinned_commit", "")
        if not pinned:
            continue
        local_path = repo_cfg.get("local_path", f"external/{repo_name}")
        actual = get_skill_commit(agent_meta_root, local_path)
        # get_skill_commit returns short hash — compare prefix
        if actual != "unknown" and not pinned.startswith(actual):
            log.warn(
                f"repo '{repo_name}': submodule is at {actual}, "
                f"expected pinned_commit {pinned[:8]} — "
                f"run: cd {local_path} && git checkout {pinned[:8]}"
            )


def get_skill_commit(agent_meta_root: Path, submodule_path: str) -> str:
    """Return short commit hash of a submodule. Falls back to 'unknown'."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(agent_meta_root / submodule_path),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"


def build_additional_files_section(skill_name: str, additional_files: list[str]) -> str:
    """Render the additional_files read-list for the wrapper template."""
    if not additional_files:
        return "_Keine weiteren Referenzdateien konfiguriert._"
    lines = ["Falls du detaillierte Referenzen brauchst, lies mit dem Read-Tool:"]
    for f in additional_files:
        lines.append(f"- `.claude/skills/{skill_name}/{f}`")
    return "\n".join(lines)


def sync_external_skills(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Generate .claude/agents/<role>.md wrapper agents for approved + project-enabled skills.

    Two-gate check per skill:
    1. approved: true in external-skills.config.json  (meta-maintainer quality gate)
    2. enabled:  true in agent-meta.config.json        (project opt-in)
    """
    ext_config = load_external_skills_config(agent_meta_root)
    skills = ext_config.get("skills", {})
    repos = ext_config.get("repos", {})
    project_skills = config.get("external-skills", {})

    wrapper_path = agent_meta_root / AGENTS_DIR / EXTERNAL_DIR / SKILL_WRAPPER
    if not wrapper_path.exists():
        log.warn(f"Skill wrapper template not found: {wrapper_path}")
        return

    wrapper_template = wrapper_path.read_text(encoding="utf-8")
    agents_dir = project_root / CLAUDE_AGENTS_DIR
    skills_dir = project_root / CLAUDE_SKILLS_DIR

    for skill_name, skill_cfg in skills.items():
        role_label = f".claude/agents/{skill_cfg.get('role', skill_name)}.md"
        if not skill_cfg.get("approved", False):
            log.info(role_label, f"skill '{skill_name}' not approved — skipping")
            continue
        project_skill_cfg = project_skills.get(skill_name, {})
        if not project_skill_cfg.get("enabled", False):
            log.info(role_label, f"skill '{skill_name}' not enabled in agent-meta.config.json — skipping")
            continue

        repo_key   = skill_cfg.get("repo", "")
        repo_cfg   = repos.get(repo_key, {})
        local_path = repo_cfg.get("local_path", f"external/{repo_key}")
        source_rel    = skill_cfg.get("source", "")
        entry_file    = skill_cfg.get("entry", "SKILL.md")
        role          = skill_cfg.get("role", skill_name)
        display_name  = skill_cfg.get("name", skill_name)
        description   = skill_cfg.get("description", "")
        additional    = skill_cfg.get("additional_files", [])

        skill_source_dir = agent_meta_root / local_path / source_rel
        entry_path = skill_source_dir / entry_file

        # Detect uninitialized submodule (directory exists but is empty)
        submodule_dir = agent_meta_root / local_path
        if submodule_dir.exists() and not any(submodule_dir.iterdir()):
            log.warn(
                f"Submodule '{local_path}' is not initialized (empty directory) — "
                f"please run: git submodule update --init --recursive"
            )
            continue

        if not entry_path.exists():
            log.warn(f"Skill entry not found: {entry_path}")
            continue

        # Read + substitute SKILL_CONTENT
        skill_content = entry_path.read_text(encoding="utf-8")
        # Strip frontmatter from skill content if present
        skill_content = re.sub(r"^---\n.*?\n---\n", "", skill_content,
                               count=1, flags=re.DOTALL).lstrip()

        commit = get_skill_commit(agent_meta_root, local_path)

        # Build skill-specific variables (extend project variables)
        skill_vars = dict(variables)
        skill_vars["SKILL_NAME"]          = skill_name
        skill_vars["SKILL_NAME_DISPLAY"]  = display_name
        skill_vars["SKILL_ROLE"]          = role
        skill_vars["SKILL_DESCRIPTION"]   = description
        skill_vars["SKILL_COMMIT"]        = commit
        skill_vars["SKILL_CONTENT"]       = skill_content
        skill_vars["SKILL_ADDITIONAL_FILES_SECTION"] = build_additional_files_section(
            skill_name, additional
        )

        # Generate wrapper agent
        agent_content = substitute(wrapper_template, skill_vars,
                                   f"0-external/{skill_name}", log)

        agent_target = agents_dir / f"{role}.md"
        log.action("WRITE", str(agent_target.relative_to(project_root)),
                   f"0-external/{skill_name}@{commit}")

        # Copy skill files to .claude/skills/<skill_name>/
        skill_target_dir = skills_dir / skill_name
        log.action("COPY", str((skill_target_dir / entry_file).relative_to(project_root)),
                   f"{local_path}/{source_rel}/{entry_file}")
        for af in additional:
            af_source = skill_source_dir / af
            if af_source.exists():
                log.action("COPY", str((skill_target_dir / af).relative_to(project_root)),
                           f"{local_path}/{source_rel}/{af}")
            else:
                log.warn(f"additional_file not found: {af_source}")

        if not dry_run:
            agents_dir.mkdir(parents=True, exist_ok=True)
            agent_target.write_text(agent_content, encoding="utf-8")
            skill_target_dir.mkdir(parents=True, exist_ok=True)
            (skill_target_dir / entry_file).write_text(
                entry_path.read_text(encoding="utf-8"), encoding="utf-8"
            )
            for af in additional:
                af_source = skill_source_dir / af
                if af_source.exists():
                    (skill_target_dir / af).write_text(
                        af_source.read_text(encoding="utf-8"), encoding="utf-8"
                    )


def add_skill(
    agent_meta_root: Path,
    repo_url: str,
    skill_name: str,
    source_path: str,
    role: str,
    entry: str,
    log: SyncLog,
    dry_run: bool,
):
    """Register a new submodule + skill entry in external-skills.config.json.

    Runs: git submodule add <repo_url> external/<submodule_name>
    Then updates external-skills.config.json with the new submodule + skill entry.
    """
    # Derive submodule name from repo URL (last path segment without .git)
    submodule_name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
    local_path = f"external/{submodule_name}"

    # Run git submodule add (skip if already exists)
    submodule_target = agent_meta_root / local_path
    if submodule_target.exists():
        print(f"  i  Submodule already exists: {local_path}")
    else:
        print(f"  >  git submodule add {repo_url} {local_path}")
        if not dry_run:
            result = subprocess.run(
                ["git", "submodule", "add", repo_url, local_path],
                cwd=str(agent_meta_root),
                capture_output=False,
            )
            if result.returncode != 0:
                print(f"  !  git submodule add failed", file=sys.stderr)
                return

    # Update external-skills.config.json
    config_path = agent_meta_root / EXTERNAL_SKILLS_CONFIG
    if config_path.exists():
        with config_path.open(encoding="utf-8") as f:
            raw = json.load(f)
    else:
        raw = {"repos": {}, "skills": {}}

    # Capture current commit for pinning
    actual_commit = get_skill_commit(agent_meta_root, local_path)

    raw.setdefault("repos", {})[submodule_name] = {
        "repo": repo_url,
        "local_path": local_path,
        "pinned_commit": actual_commit,
    }
    raw.setdefault("skills", {})[skill_name] = {
        "approved": False,
        "repo": submodule_name,
        "source": source_path,
        "entry": entry,
        "role": role,
        "name": skill_name.replace("-", " ").title(),
        "description": f"Specialist for {skill_name}.",
        "additional_files": [],
    }

    log.action("UPDATE", EXTERNAL_SKILLS_CONFIG,
               f"added repo '{submodule_name}' @{actual_commit[:8]}, skill '{skill_name}'")
    if not dry_run:
        with config_path.open("w", encoding="utf-8") as f:
            json.dump(raw, f, indent=2, ensure_ascii=False)
        print(f"  +  {EXTERNAL_SKILLS_CONFIG} updated")
        print(f"  i  Repo '{submodule_name}' pinned to commit {actual_commit[:8]}")
        print(f"  i  Skill '{skill_name}' added (approved: false) → role: '{role}'")
        print(f"  i  To activate: set approved: true in {EXTERNAL_SKILLS_CONFIG},")
        print(f"     then add to agent-meta.config.json: \"external-skills\": {{\"{skill_name}\": {{\"enabled\": true}}}}")


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
        print(f"  !  Unknown role '{role}'. Valid roles: {', '.join(ROLE_MAP)}", file=sys.stderr)
        return

    prefix = config["project"].get("prefix", "")
    filename = ext_target_filename(role, prefix)
    target_path = project_root / CLAUDE_EXT_DIR / filename

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)), "extension already exists — use --update-ext to update")
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
        log.skip(CLAUDE_EXT_DIR, "directory not found — no extensions to update")
        return

    for ext_file in sorted(ext_dir.glob(f"*{EXT_SUFFIX}.md")):
        existing = ext_file.read_text(encoding="utf-8")
        new_managed = render_managed_block(variables, str(ext_file.name), log)
        new_content = update_managed_block(existing, new_managed)

        if new_content == existing:
            log.skip(str(ext_file.relative_to(project_root)), "managed block unchanged")
        else:
            log.action("UPDATE", str(ext_file.relative_to(project_root)), "managed block")
            if not dry_run:
                ext_file.write_text(new_content, encoding="utf-8")


CLAUDE_MD_MANAGED_TEMPLATE = """\
<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`

{{AGENT_HINTS}}
<!-- agent-meta:managed-end -->"""


def sync_claude_md_managed(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Update the managed block in CLAUDE.md if it exists and contains the marker."""
    target_path = project_root / "CLAUDE.md"
    if not target_path.exists():
        return

    existing = target_path.read_text(encoding="utf-8")
    pattern = re.compile(
        r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
        re.DOTALL,
    )
    if not pattern.search(existing):
        log.warn(
            "CLAUDE.md exists but has no managed block — "
            "AGENT_TABLE will not be updated. "
            "Add the following block at the desired location in CLAUDE.md:\n"
            "  <!-- agent-meta:managed-begin -->\n"
            "  <!-- agent-meta:managed-end -->"
        )
        return

    new_managed = substitute(CLAUDE_MD_MANAGED_TEMPLATE, variables, "CLAUDE.md managed block", log)
    new_content = pattern.sub(new_managed, existing, count=1)

    if new_content == existing:
        log.skip("CLAUDE.md", "managed block unchanged")
    else:
        log.action("UPDATE", "CLAUDE.md", "managed block (AGENT_TABLE + version)")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


def init_claude_personal(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Copy CLAUDE.personal-template.md to CLAUDE.personal.md if not present yet."""
    template_path = agent_meta_root / "howto" / "CLAUDE.personal-template.md"
    target_path = project_root / "CLAUDE.personal.md"

    if target_path.exists():
        log.skip("CLAUDE.personal.md", "already exists")
        return

    if not template_path.exists():
        log.warn("CLAUDE.personal-template.md not found — skipping CLAUDE.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "CLAUDE.personal.md", "howto/CLAUDE.personal-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def init_settings_json(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/settings.json if it does not exist yet."""
    target_path = project_root / ".claude" / "settings.json"
    if target_path.exists():
        log.skip(".claude/settings.json", "already exists")
        return

    content = '{\n  "permissions": {\n    "allow": [],\n    "deny": []\n  }\n}\n'
    log.action("INIT", ".claude/settings.json", "team permissions skeleton")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


GITIGNORE_ENTRIES = [
    ".claude/settings.local.json",
    "CLAUDE.personal.md",
    "sync.log",
]


def ensure_gitignore_entries(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Ensure required entries exist in .gitignore. Creates .gitignore if absent."""
    gitignore_path = project_root / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

    missing = [e for e in GITIGNORE_ENTRIES if e not in existing]
    if not missing:
        log.skip(".gitignore", "all required entries already present")
        return

    new_content = existing.rstrip("\n") + "\n" + "\n".join(missing) + "\n"
    log.action("UPDATE", ".gitignore", f"added: {', '.join(missing)}")
    if not dry_run:
        gitignore_path.write_text(new_content, encoding="utf-8")


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
        print("  i  CLAUDE.md already exists — skipped (use --only-variables)")
        log.skip("CLAUDE.md", "already exists")
        return

    if not template_path.exists():
        log.warn(f"CLAUDE.project-template.md not found at {template_path}")
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
        print("  !  CLAUDE.md not found — use --init to create it")
        sys.exit(1)

    content = target_path.read_text(encoding="utf-8")
    new_content = substitute(content, variables, "CLAUDE.md", log)

    if new_content == content:
        log.action("SKIP", "CLAUDE.md", "no open placeholders")
    else:
        log.action("WRITE", "CLAUDE.md", "variables from config")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sync agent-meta agents into a project."
    )
    parser.add_argument("--config", required=False, default=None,
                        help="Path to agent-meta.config.json (not required for --add-skill)")
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

    # External skill management
    parser.add_argument("--add-skill", metavar="REPO_URL",
                        help="Register a new external skill: git submodule add + config entry")
    parser.add_argument("--skill-name", metavar="NAME",
                        help="Skill identifier (used in external-skills.config.json)")
    parser.add_argument("--source", metavar="PATH",
                        help="Path to skill directory within the submodule repo")
    parser.add_argument("--role", metavar="ROLE",
                        help="Agent role name for the generated wrapper agent")
    parser.add_argument("--entry", metavar="FILE", default="SKILL.md",
                        help="Entry file within the skill directory (default: SKILL.md)")

    args = parser.parse_args()

    script_path = Path(__file__).resolve()
    agent_meta_root = find_agent_meta_root(script_path)

    log = SyncLog()

    if args.dry_run:
        print("DRY-RUN — no files will be written\n")

    if args.add_skill:
        mode = "add-skill"
        for required, flag in [(args.skill_name, "--skill-name"),
                               (args.source, "--source"),
                               (args.role, "--role")]:
            if not required:
                print(f"  !  --add-skill requires {flag}", file=sys.stderr)
                sys.exit(1)
        add_skill(agent_meta_root, args.add_skill, args.skill_name,
                  args.source, args.role, args.entry, log, args.dry_run)
        log.write(agent_meta_root / LOGFILE, EXTERNAL_SKILLS_CONFIG,
                  read_version(agent_meta_root), mode, [], args.dry_run)
        return

    # All other modes require --config
    if not args.config:
        print("  !  --config is required (except for --add-skill)", file=sys.stderr)
        sys.exit(1)

    project_root = Path(args.config).resolve().parent
    config_path = Path(args.config).resolve()
    config = load_config(config_path)
    variables, pre_warnings = build_variables(config, agent_meta_root)
    platforms = config.get("platforms", [])
    source_version = config.get("agent-meta-version", read_version(agent_meta_root))

    for w in pre_warnings:
        log.warn(w)

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
        is_claude = variables.get("AI_PROVIDER", "").strip().lower() == "claude"
        mode = "init" if args.init else "sync"
        if args.init or is_claude:
            init_claude_md(agent_meta_root, project_root, config, variables, log, args.dry_run)
            init_claude_personal(agent_meta_root, project_root, log, args.dry_run)
            init_settings_json(project_root, log, args.dry_run)
            ensure_gitignore_entries(project_root, log, args.dry_run)
        sync_agents(agent_meta_root, project_root, config, variables, log, args.dry_run)
        sync_snippets(agent_meta_root, project_root, config, log, args.dry_run)
        # Check pinned commits + warn for unknown/unapproved skills in project config
        ext_config = load_external_skills_config(agent_meta_root)
        check_pinned_commits(ext_config, agent_meta_root, log)
        if "external-skills" in config:
            known_skills = set(ext_config.get("skills", {}).keys())
            for skill_name in config["external-skills"]:
                if skill_name not in known_skills:
                    log.warn(f"external-skills: '{skill_name}' not found in external-skills.config.json — skipping")
                elif not ext_config["skills"][skill_name].get("approved", False):
                    log.warn(f"external-skills: '{skill_name}' is not approved by meta-maintainer — skipping")
        sync_external_skills(agent_meta_root, project_root, config, variables, log, args.dry_run)
        if is_claude:
            sync_claude_md_managed(project_root, variables, log, args.dry_run)
        elif (project_root / "CLAUDE.md").exists():
            log.info("CLAUDE.md", f"managed block update skipped (ai-provider: '{variables.get('AI_PROVIDER', '')}')")

    log_path = project_root / LOGFILE
    log.write(log_path, args.config, source_version, mode, platforms, args.dry_run)


if __name__ == "__main__":
    main()
