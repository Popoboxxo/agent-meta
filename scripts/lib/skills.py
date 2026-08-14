"""External skills: loading, commit checks, sync, add."""

import os
import re
import stat
import subprocess
from pathlib import Path

from .io import _load_yaml_or_json, _write_yaml, safe_path
from .log import SyncLog

EXTERNAL_SKILLS_CONFIG = "config/skills-registry.yaml"
_EXTERNAL_SKILLS_CONFIG_LEGACY = "external-skills.config.yaml"
_EXTERNAL_SKILLS_CONFIG_JSON = "external-skills.config.json"  # legacy fallback


def _rmtree_force(path) -> None:
    """shutil.rmtree that survives Windows' read-only .git pack/idx files.

    Git marks objects in .git/objects/pack/* read-only; plain shutil.rmtree()
    fails there with [WinError 5] Access Denied. On error, clear the
    read-only bit and retry the removal once.
    """
    import shutil

    def _on_error(func, target_path, exc_info):
        os.chmod(target_path, stat.S_IWRITE)
        func(target_path)

    shutil.rmtree(path, onerror=_on_error)


def _normalize_project_skills(raw) -> dict:
    """Normalize project external-skills config to dict format.

    Accepts both legacy list format ['skill-a', 'skill-b'] and
    canonical dict format {'skill-a': {'enabled': True}}.
    Returns dict format always.
    """
    if isinstance(raw, list):
        return {name: {"enabled": True} for name in raw}
    if isinstance(raw, dict):
        return raw
    return {}


def _read_skills_managed_index(skills_dir: Path) -> set[str]:
    """Read the .agent-meta-managed index from skills_dir.

    Returns empty set if file doesn't exist.
    """
    managed_index_path = skills_dir / ".agent-meta-managed"
    if not managed_index_path.exists():
        return set()
    return {
        line.strip()
        for line in managed_index_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }


def _write_skills_managed_index(
    skills_dir: Path,
    now_managed: set[str],
    dry_run: bool,
    universe: set[str] | None = None,
) -> None:
    """Write (or merge into) the .agent-meta-managed index for skills_dir.

    skills_dir has two independent writers now: external-skill sync (this
    module) and the lazy-rules 'channel: skill' mechanism (see
    scripts/lib/skill_channel.py). universe=None (default): full replace —
    legacy behavior, skipped if now_managed is empty. universe=<set>: merge
    mode — only entries within `universe` (this caller's own name-space) are
    added/removed, so another writer's entries in the same shared index
    survive untouched.
    """
    if dry_run:
        return
    managed_index_path = skills_dir / ".agent-meta-managed"
    if universe is None:
        if not now_managed:
            return
        merged = set(now_managed)
    else:
        existing = _read_skills_managed_index(skills_dir)
        merged = (existing - universe) | now_managed
    managed_index_path.parent.mkdir(parents=True, exist_ok=True)
    if merged:
        managed_index_path.write_text("\n".join(sorted(merged)) + "\n", encoding="utf-8")
    elif managed_index_path.exists():
        managed_index_path.unlink()


def _skill_is_active(skill_name: str, skill_cfg: dict, project_skills: dict) -> bool:
    """Return True if a skill should be generated for the current project.

    Project explicitly enables/disables? -> Use project setting (Override)
    Else -> Use enabled-by-default flag from skills-registry.yaml (Default)
    """
    if skill_name in project_skills and "enabled" in project_skills[skill_name]:
        return project_skills[skill_name]["enabled"]
    if "enabled-by-default" in skill_cfg:
        return skill_cfg["enabled-by-default"]
    return not skill_cfg.get("planned", True)


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
    """Warn if any dynamically cloned skill repo is not at its pinned_commit."""
    for repo_name, repo_cfg in ext_config.get("repos", {}).items():
        pinned = repo_cfg.get("pinned_commit", "")
        if not pinned:
            continue
        local_path = repo_cfg.get("local_path", f"external/{repo_name}")
        repo_dir = agent_meta_root / local_path
        if not repo_dir.exists():
            continue  # Not cloned, which is fine if not enabled

        actual = get_skill_commit(agent_meta_root, local_path)
        # get_skill_commit returns short hash — compare prefix
        if actual != "unknown" and not pinned.startswith(actual):
            log.warn(
                f"repo '{repo_name}': dynamic clone is at {actual}, "
                f"expected pinned_commit {pinned[:8]} — "
                f"run: git -C {local_path} checkout {pinned[:8]}"
            )


def get_skill_commit(agent_meta_root: Path, submodule_path: str) -> str:
    """Return short commit hash of a submodule. Falls back to 'unknown'."""
    try:
        result = subprocess.run(  # noqa: PLW1510
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(agent_meta_root / submodule_path),
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return "unknown"


def build_additional_files_section(skill_name: str, additional_files: list[str], skill_base_path: str) -> str:
    """Render the additional_files read-list for the wrapper template."""
    if not additional_files:
        return "_Keine weiteren Referenzdateien konfiguriert._"
    lines = ["Falls du detaillierte Referenzen brauchst, lies mit dem Read-Tool:"]
    for f in additional_files:
        lines.append(f"- `{skill_base_path}/{f}`")
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


def ensure_skill_repo(agent_meta_root: Path, project_root: Path, repo_name: str, repo_cfg: dict, pinned_commit: str, log: SyncLog) -> None:
    """Dynamically clone or submodule add a skill repository if it doesn't exist."""
    import shutil
    repo_url = repo_cfg.get("repo", "")
    if not repo_url:
        return
        
    local_path = repo_cfg.get("local_path", f"external/{repo_name}")
    is_project_admin = agent_meta_root != project_root
    
    if is_project_admin:
        target_dir = project_root / local_path
        if target_dir.exists() and not any(target_dir.iterdir()):
            log.info(local_path, f"Initializing existing skill submodule: {repo_url}")
            result = subprocess.run(["git", "submodule", "update", "--init", local_path], cwd=str(project_root), capture_output=True)
            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8', errors='ignore').strip()
                log.warning(
                    f"Failed to init submodule {local_path}: {stderr}\n"
                    f"  -> Fix: cd {project_root} && git submodule update --init {local_path}"
                )
                return
        elif not target_dir.exists():
            log.info(local_path, f"Adding skill submodule: {repo_url}")
            result = subprocess.run(["git", "submodule", "add", "--depth", "1", repo_url, local_path], cwd=str(project_root), capture_output=True)
            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8', errors='ignore').strip()
                if "is found locally" in stderr or "already exists" in stderr:
                    log.info(local_path, f"Local git directory conflict for {local_path} — cleaning up and retrying with force")
                    # Proper git cleanup: deinit, rm from index, remove config, then filesystem cleanup
                    subprocess.run(["git", "submodule", "deinit", "-f", local_path],
                                   cwd=str(project_root), capture_output=True)
                    subprocess.run(["git", "rm", "--cached", "-f", local_path],
                                   cwd=str(project_root), capture_output=True)
                    subprocess.run(["git", "config", "--remove-section", f"submodule.{local_path}"],
                                   cwd=str(project_root), capture_output=True)
                    shutil.rmtree(str(target_dir), ignore_errors=True)
                    git_modules_dir = project_root / ".git" / "modules" / local_path
                    if git_modules_dir.exists():
                        shutil.rmtree(str(git_modules_dir), ignore_errors=True)
                    result2 = subprocess.run(["git", "submodule", "add", "--force", "--depth", "1", repo_url, local_path], cwd=str(project_root), capture_output=True)
                    if result2.returncode != 0:
                        stderr2 = result2.stderr.decode('utf-8', errors='ignore').strip()
                        log.warning(
                            f"Failed to add submodule {local_path} (retry with --force): {stderr2}\n"
                            f"  -> Fix: cd {project_root} && rm -rf {local_path} && git submodule add --depth 1 {repo_url} {local_path}"
                        )
                        return
                else:
                    log.warning(
                        f"Failed to add submodule {local_path}: {stderr}\n"
                        f"  -> Fix: cd {project_root} && git submodule add --depth 1 {repo_url} {local_path}"
                    )
                    return
        # Verify submodule is properly initialized after add/init
        if target_dir.exists() and not any(target_dir.iterdir()):
            log.warning(
                f"Submodule directory {local_path} exists but is empty after init.\n"
                f"  -> Fix: cd {project_root} && git submodule update --init --recursive {local_path}"
            )
            return
    else:
        target_dir = agent_meta_root / local_path
        if not target_dir.exists():
            log.info(local_path, f"Dynamically cloning skill repo: {repo_url}")
            result = subprocess.run(["git", "clone", "--no-recursive", "--depth", "1", repo_url, local_path], cwd=str(agent_meta_root), capture_output=True)
            if result.returncode != 0:
                stderr = result.stderr.decode('utf-8', errors='ignore').strip()
                log.warning(
                    f"Failed to clone {repo_url} into {local_path}: {stderr}\n"
                    f"  -> Fix: cd {agent_meta_root} && git clone --depth 1 {repo_url} {local_path}"
                )
                return
            
    if pinned_commit:
        result = subprocess.run(["git", "checkout", pinned_commit], cwd=str(target_dir), capture_output=True)
        if result.returncode != 0:
            stderr = result.stderr.decode('utf-8', errors='ignore').strip()
            log.warning(
                f"Failed to checkout {pinned_commit} in {local_path}: {stderr}\n"
                f"  -> Fix: cd {target_dir} && git checkout {pinned_commit}"
            )


def deinit_skill_repo(agent_meta_root: Path, project_root: Path, local_path: str, log: SyncLog, dry_run: bool, is_submodule: bool = True) -> None:
    """Deinit a skill submodule when no active skill references its repo."""
    import shutil
    is_project_admin = agent_meta_root != project_root
    cwd = str(project_root) if is_project_admin else str(agent_meta_root)
    target_dir = Path(cwd) / local_path

    if not target_dir.exists():
        return

    log.info(local_path, f"Deinitializing unused skill repo: {local_path}")
    if not dry_run:
        if is_submodule:
            result = subprocess.run(
                ["git", "submodule", "deinit", "-f", local_path],
                cwd=cwd, capture_output=True, timeout=30,
            )
            if result.returncode != 0:
                log.warn(
                    f"Failed to deinit submodule {local_path}: "
                    f"{result.stderr.decode('utf-8', errors='ignore').strip()}"
                )
            result = subprocess.run(
                ["git", "rm", "-f", local_path],
                cwd=cwd, capture_output=True, timeout=30,
            )
            if result.returncode != 0:
                log.warn(
                    f"Failed to rm submodule {local_path} from git index: "
                    f"{result.stderr.decode('utf-8', errors='ignore').strip()}"
                )
            modules_dir = Path(cwd) / ".git" / "modules" / local_path
            if modules_dir.exists():
                try:
                    _rmtree_force(modules_dir)
                except Exception as e:
                    log.warn(f"Failed to remove .git/modules/{local_path}: {e}")
            try:
                _rmtree_force(target_dir)
            except Exception as e:
                log.warn(f"Failed to remove working directory {local_path}: {e}")
        else:
            try:
                _rmtree_force(target_dir)
            except Exception as e:
                log.warn(f"Failed to remove cloned repo {local_path}: {e}")


def sync_external_skills_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
):
    """Generate provider-specific wrapper agents for approved + project-enabled skills.

    Two-gate check per skill:
    1. approved: true in external-skills.config.yaml  (meta-maintainer quality gate)
    2. enabled:  true in .meta-config/project.yaml        (project opt-in)

    Skill files are copied into the provider-specific skills_dir so that every
    active provider gets its own self-contained skill reference tree.
    """
    from .agents import AGENTS_DIR, EXTERNAL_DIR, SKILL_WRAPPER
    from .config import substitute

    pc = provider_config.get(provider, {})
    agents_dir_rel = pc.get('agents_dir', '.claude/agents')
    skills_dir_rel = pc.get('skills_dir', '.claude/skills')
    agents_dir = project_root / agents_dir_rel
    skills_dir = project_root / skills_dir_rel

    now_managed: set[str] = set()

    ext_config = load_external_skills_config(agent_meta_root)
    skills = ext_config.get("skills", {})
    repos = ext_config.get("repos", {})
    project_skills = _normalize_project_skills(config.get("external-skills", {}))

    # Collect active repos for dynamic cloning/submodule
    active_repos = {}
    for skill_name, skill_cfg in skills.items():
        if _skill_is_active(skill_name, skill_cfg, project_skills):
            repo = skill_cfg.get("repo")
            if repo:
                override_commit = project_skills.get(skill_name, {}).get("pinned_commit")
                default_commit = repos.get(repo, {}).get("pinned_commit", "")
                active_repos[repo] = override_commit or default_commit
            
    # agent-meta-scout implicitly requires awesome-claude-code (unless disabled via enabled: false)
    # Project can override: external-skills.awesome-claude-code.enabled: false
    roles = config.get("roles", [])
    acc_cfg = repos.get("awesome-claude-code", {})
    acc_project_override = project_skills.get("awesome-claude-code", {})
    if (
        acc_cfg.get("enabled", True)
        and acc_project_override.get("enabled", True)
        and "agent-meta-scout" in roles
    ):
        active_repos["awesome-claude-code"] = acc_cfg.get("pinned_commit", "")
        
    # Ensure all active repos are present locally
    for repo_name, pinned_commit in active_repos.items():
        if repo_name and repo_name in repos:
            ensure_skill_repo(agent_meta_root, project_root, repo_name, repos[repo_name], pinned_commit, log)

    wrapper_path = agent_meta_root / AGENTS_DIR / EXTERNAL_DIR / SKILL_WRAPPER
    if not wrapper_path.exists():
        log.warn(f"Skill wrapper template not found: {wrapper_path}")
        return

    wrapper_template = wrapper_path.read_text(encoding="utf-8")

    for skill_name, skill_cfg in skills.items():
        role = skill_cfg.get('role', skill_name)
        role_label = f"{agents_dir_rel}/{role}.md"
        agent_target = safe_path(agents_dir, f"{role}.md")
        skill_target_dir = safe_path(skills_dir, skill_name)

        if not _skill_is_active(skill_name, skill_cfg, project_skills):
            log.info(role_label, f"skill '{skill_name}' is not active — skipping")
            if not dry_run:
                if agent_target.exists():
                    agent_target.unlink()
                import shutil
                if skill_target_dir.exists():
                    shutil.rmtree(skill_target_dir, ignore_errors=True)
            continue

        now_managed.add(skill_name)

        repo_key   = skill_cfg.get("repo", "")
        repo_cfg   = repos.get(repo_key, {})
        local_path = repo_cfg.get("local_path", f"external/{repo_key}")
        source_rel    = skill_cfg.get("source", "")
        entry_file    = skill_cfg.get("entry", "SKILL.md")
        display_name  = skill_cfg.get("name", skill_name)
        description   = skill_cfg.get("description", "")
        additional    = skill_cfg.get("additional_files", [])

        is_project_admin = agent_meta_root != project_root
        if is_project_admin:
            repo_dir = project_root / local_path
            skill_source_dir = repo_dir / source_rel
            entry_path = skill_source_dir / entry_file
            commit = get_skill_commit(project_root, local_path)
        else:
            repo_dir = agent_meta_root / local_path
            skill_source_dir = repo_dir / source_rel
            entry_path = skill_source_dir / entry_file
            commit = get_skill_commit(agent_meta_root, local_path)

        # Ensure repo directory is valid
        if not repo_dir.exists() or not any(repo_dir.iterdir()):
            log.warn(f"Dynamic skill repo '{local_path}' is missing or empty.")
            continue

        if not entry_path.exists():
            log.warn(f"Skill entry not found: {entry_path}")
            continue

        # Canonical paths in the target project (provider-specific)
        skill_base_path  = f"{skills_dir_rel}/{skill_name}"
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
            skill_name, additional, skill_base_path
        )

        # Generate thin wrapper agent (no inline skill content)
        agent_content = substitute(wrapper_template, skill_vars,
                                   f"0-external/{skill_name}", log)

        agent_target = safe_path(agents_dir, f"{role}.md")

        # Apply provider-specific transformations (Opencode, Continue, etc.)
        from .agents import transform_agent_content_for_provider
        agent_content = transform_agent_content_for_provider(
            content=agent_content,
            provider=provider,
            role=role,
            name=role,
            description=description,
            generated_from=f"0-external/{skill_name}@{commit}",
            config=config,
            agent_meta_root=agent_meta_root,
            project_root=project_root,
            target_path=agent_target,
            provider_config=provider_config,
            log=log,
        )
        log.action("WRITE", str(agent_target.relative_to(project_root)),
                   f"0-external/{skill_name}@{commit}")

        # Copy + normalize skill files to <provider>/skills/<skill_name>/
        skill_target_dir = safe_path(skills_dir, skill_name)

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

            # Normalize ./ref paths in entry file → <provider>/skills/<skill>/ref
            entry_content = entry_path.read_text(encoding="utf-8")
            entry_content = normalize_skill_paths(entry_content, skill_base_path)
            (skill_target_dir / entry_file).write_text(entry_content, encoding="utf-8")

            for af in additional:
                af_source = skill_source_dir / af
                if af_source.exists():
                    (skill_target_dir / af).write_text(
                        af_source.read_text(encoding="utf-8"), encoding="utf-8"
                    )

    _write_skills_managed_index(skills_dir, now_managed, dry_run, universe=set(skills.keys()))

    # Deinit repos that are no longer needed by any active skill
    is_project_admin = agent_meta_root != project_root
    all_skill_repos: set[str] = set()
    active_skill_repos: set[str] = set()
    for skill_name, skill_cfg in skills.items():
        repo = skill_cfg.get("repo")
        if repo:
            all_skill_repos.add(repo)
            if _skill_is_active(skill_name, skill_cfg, project_skills):
                active_skill_repos.add(repo)

    inactive_repos = all_skill_repos - active_skill_repos
    for repo_name in inactive_repos:
        repo_cfg = repos.get(repo_name, {})
        local_path = repo_cfg.get("local_path", f"external/{repo_name}")
        deinit_skill_repo(agent_meta_root, project_root, local_path, log, dry_run, is_submodule=is_project_admin)

    # awesome-claude-code is a reference-data repo (no skill entries), only needed by agent-meta-scout
    if "awesome-claude-code" in repos and (not acc_cfg.get("enabled", True) or "agent-meta-scout" not in roles):
        acc_local = acc_cfg.get("local_path", "external/awesome-claude-code")
        deinit_skill_repo(agent_meta_root, project_root, acc_local, log, dry_run, is_submodule=is_project_admin)

