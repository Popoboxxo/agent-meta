"""External skills: loading, commit checks, sync, add."""

import re
import subprocess
from pathlib import Path

from .io import _load_yaml_or_json, _write_yaml
from .log import SyncLog

EXTERNAL_SKILLS_CONFIG = "config/skills-registry.yaml"
_EXTERNAL_SKILLS_CONFIG_LEGACY = "external-skills.config.yaml"
_EXTERNAL_SKILLS_CONFIG_JSON = "external-skills.config.json"  # legacy fallback


def _skill_is_active(skill_name: str, skill_cfg: dict, project_skills: dict) -> bool:
    """Return True if a skill should be generated for the current project.

    Two-gate check:
    1. approved: true in external-skills.config.yaml  (meta-maintainer quality gate)
    2. enabled:  true in .meta-config/project.yaml        (project opt-in)

    If project has no "external-skills" block at all, no skill is generated.
    """
    return (
        skill_cfg.get("approved", False)
        and project_skills.get(skill_name, {}).get("enabled", False)
    )


def load_external_skills_config(agent_meta_root: Path) -> dict:
    """Load config/skills-registry.yaml with fallback to legacy paths."""
    data, _ = _load_yaml_or_json(
        agent_meta_root / EXTERNAL_SKILLS_CONFIG,
        agent_meta_root / _EXTERNAL_SKILLS_CONFIG_LEGACY,
        agent_meta_root / _EXTERNAL_SKILLS_CONFIG_JSON,
    )
    if not data:
        return {"repos": {}, "skills": {}}
    # Strip _comment keys (JSON legacy)
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


def normalize_skill_paths(content: str, skill_base_path: str) -> str:
    """Replace relative ./file references in skill content with absolute .claude/skills/... paths.

    Handles patterns like:
      - ./reference.md
      - **./reference.md**
      - [text](./reference.md)

    This allows SKILL.md files from external repos to use relative paths
    without knowing the agent-meta directory structure.
    """
    # Replace markdown link targets: (./file) → (skill_base_path/file)
    content = re.sub(
        r'\(\./([^)]+)\)',
        lambda m: f"({skill_base_path}/{m.group(1)})",
        content
    )
    # Replace bare ./file references (bold, plain, list items)
    content = re.sub(
        r'(?<!\()\.\/([^\s\)]+\.md)',
        lambda m: f"{skill_base_path}/{m.group(1)}",
        content
    )
    return content


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
    1. approved: true in external-skills.config.yaml  (meta-maintainer quality gate)
    2. enabled:  true in .meta-config/project.yaml        (project opt-in)
    """
    from .agents import AGENTS_DIR, EXTERNAL_DIR, SKILL_WRAPPER
    from .config import substitute

    CLAUDE_AGENTS_DIR = ".claude/agents"
    CLAUDE_SKILLS_DIR = ".claude/skills"

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
            log.info(role_label, f"skill '{skill_name}' not enabled in .meta-config/project.yaml — skipping")
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

        commit = get_skill_commit(agent_meta_root, local_path)

        # Canonical paths in the target project
        skill_base_path  = f".claude/skills/{skill_name}"
        skill_entry_path = f"{skill_base_path}/{entry_file}"

        # Build skill-specific variables (extend project variables)
        skill_vars = dict(variables)
        skill_vars["SKILL_NAME"]          = skill_name
        skill_vars["SKILL_NAME_DISPLAY"]  = display_name
        skill_vars["SKILL_ROLE"]          = role
        skill_vars["SKILL_DESCRIPTION"]   = description
        skill_vars["SKILL_COMMIT"]        = commit
        skill_vars["SKILL_ENTRY_PATH"]    = skill_entry_path
        skill_vars["SKILL_BASE_PATH"]     = skill_base_path
        skill_vars["SKILL_ADDITIONAL_FILES_SECTION"] = build_additional_files_section(
            skill_name, additional
        )

        # Generate thin wrapper agent (no inline skill content)
        agent_content = substitute(wrapper_template, skill_vars,
                                   f"0-external/{skill_name}", log)

        agent_target = agents_dir / f"{role}.md"
        log.action("WRITE", str(agent_target.relative_to(project_root)),
                   f"0-external/{skill_name}@{commit}")

        # Copy + normalize skill files to .claude/skills/<skill_name>/
        skill_target_dir = skills_dir / skill_name

        # Entry file: copy and normalize relative paths
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

            # Normalize ./ref paths in entry file → .claude/skills/<skill>/ref
            entry_content = entry_path.read_text(encoding="utf-8")
            entry_content = normalize_skill_paths(entry_content, skill_base_path)
            (skill_target_dir / entry_file).write_text(entry_content, encoding="utf-8")

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
    """Register a new submodule + skill entry in external-skills.config.yaml.

    Runs: git submodule add <repo_url> external/<submodule_name>
    Then updates external-skills.config.yaml (or .json fallback) with the new entry.
    """
    import json
    import sys

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

    # Update config/skills-registry.yaml (or legacy fallback)
    yaml_path = agent_meta_root / EXTERNAL_SKILLS_CONFIG
    legacy_path = agent_meta_root / _EXTERNAL_SKILLS_CONFIG_LEGACY
    json_path = agent_meta_root / _EXTERNAL_SKILLS_CONFIG_JSON

    try:
        import yaml as _yaml
        _yaml_available = True
    except ImportError:
        _yaml_available = False

    if yaml_path.exists() and _yaml_available:
        config_path = yaml_path
        with config_path.open(encoding="utf-8") as f:
            raw = _yaml.safe_load(f) or {}
    elif legacy_path.exists() and _yaml_available:
        config_path = yaml_path  # write to new path even when reading legacy
        with legacy_path.open(encoding="utf-8") as f:
            raw = _yaml.safe_load(f) or {}
    elif json_path.exists():
        config_path = json_path
        with config_path.open(encoding="utf-8") as f:
            raw = json.load(f)
    else:
        config_path = yaml_path
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
        if config_path.suffix.lower() in (".yaml", ".yml"):
            _write_yaml(config_path, raw)
        else:
            with config_path.open("w", encoding="utf-8") as f:
                json.dump(raw, f, indent=2, ensure_ascii=False)
        print(f"  +  {config_path.name} updated")
        print(f"  i  Repo '{submodule_name}' pinned to commit {actual_commit[:8]}")
        print(f"  i  Skill '{skill_name}' added (approved: false) → role: '{role}'")
        print(f"  i  To activate: set approved: true in {config_path.name},")
        print(f"     then add to .meta-config/project.yaml: external-skills: {skill_name}: enabled: true")
