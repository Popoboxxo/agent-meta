"""Issue #694: opt-in tiered commit authority for write-capable agents.

Role eligibility is derived from each role's OWN generic template
frontmatter `tools:` list (Edit or Write present) -- never a
hand-maintained allowlist, so it stays correct as new roles are added.
"""

from __future__ import annotations

from pathlib import Path

from .frontmatter import parse_frontmatter_file

_ELIGIBLE_TOOLS = {"Edit", "Write"}

ALLOWLIST_VERSION = 1


def _template_path(role: str, agent_meta_root: Path, platform: str | None = None) -> Path | None:
    """Resolve a role's own generic template path.

    Platform overrides (agents/2-platform/<platform>-<role>.md) are not
    consulted here on purpose: eligibility must reflect the role's BASE
    tools contract, which platforms compose onto (extend), never replace
    the tools list of. If a future platform ever does replace `tools:`,
    revisit this -- out of scope for issue #694.
    """
    candidate = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
    return candidate if candidate.is_file() else None


def is_role_eligible(role: str, agent_meta_root: Path, platform: str | None = None) -> bool:
    """True if `role`'s own template declares Edit or Write in tools:."""
    path = _template_path(role, agent_meta_root, platform)
    if path is None:
        return False
    frontmatter = parse_frontmatter_file(path)
    tools = frontmatter.get("tools") or []
    return bool(_ELIGIBLE_TOOLS.intersection(tools))


def resolve_auto_commit_config(
    config: dict,
    active_roles: list[str],
    agent_meta_root: Path,
    platform: str | None = None,
) -> dict:
    """Resolve project.yaml's auto_commit block into the allowlist shape
    written to .meta-config/auto-commit-allowlist.json by the sync
    pipeline (Task 6)."""
    ac_cfg = config.get("auto_commit", {}) or {}
    mode = ac_cfg.get("mode", "off")

    eligible_roles: list[str] = []
    if mode != "off":
        eligible_roles = sorted(
            role
            for role in active_roles
            if is_role_eligible(role, agent_meta_root, platform)
        )

    return {
        "version": ALLOWLIST_VERSION,
        "mode": mode,
        "eligible_roles": eligible_roles,
        "triggers": list(ac_cfg.get("triggers", [])),
        "file_count_threshold": ac_cfg.get("file_count_threshold", 5),
        "custom_script": ac_cfg.get("custom_script"),
        "secret_scan": ac_cfg.get("secret_scan", True),
    }
