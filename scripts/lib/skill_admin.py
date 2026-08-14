"""External-skill admin operations (`sync.py --add-skill`).

Split out of ``scripts/lib/skills.py`` (module size limit — see CLAUDE.md
"Python (scripts/lib/)" conventions, <= 600 lines per module) to keep the
CLI-only skill-registration flow separate from the sync-time skill pipeline
in that module.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .io import _write_yaml
from .log import SyncLog
from .skills import (
    _EXTERNAL_SKILLS_CONFIG_JSON,
    _EXTERNAL_SKILLS_CONFIG_LEGACY,
    EXTERNAL_SKILLS_CONFIG,
    get_skill_commit,
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
    # Derive submodule name from repo URL (last path segment without .git)
    submodule_name = repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
    local_path = f"external/{submodule_name}"

    # Run git clone (skip if already exists)
    submodule_target = agent_meta_root / local_path
    if submodule_target.exists():
        print(f"  i  Repo clone already exists: {local_path}")
    else:
        print(f"  >  git clone {repo_url} {local_path}")
        if not dry_run:
            result = subprocess.run(  # noqa: PLW1510
                ["git", "clone", repo_url, local_path],
                cwd=str(agent_meta_root),
                capture_output=False,
            )
            if result.returncode != 0:
                print("  !  git clone failed", file=sys.stderr)
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
        print(f"  i  To activate: set enabled: true in .meta-config/project.yaml (or approved: true in registry)")
