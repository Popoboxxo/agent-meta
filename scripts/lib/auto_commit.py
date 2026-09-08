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


_TRIGGER_PROSE = {
    "task-boundary": "a subtask is complete AND its tests are green",
    "per-edit": "after every Write/Edit tool call",
    "context-pressure": "just before a checkpoint or context-compaction event",
    "file-count-threshold": "after {n} files have changed since the last commit",
    "custom": "the project's custom_script (see below) also votes to commit",
}


def render_auto_commit_block(resolved: dict) -> str:
    """Render the {{AUTO_COMMIT_BLOCK}} prose for the resolved auto_commit
    config. Empty string when mode is 'off' (nothing to render). Never
    mentions push/tag/branch -- those remain the git role's exclusive job
    (issue #694 scope)."""
    mode = resolved.get("mode", "off")
    if mode == "off":
        return ""

    secret_scan = resolved.get("secret_scan", True)
    scan_line = (
        "Before committing, run the project's secret scan against your "
        "staged changes; a finding blocks the commit -- report it and ask "
        "for manual intervention instead of committing anyway."
        if secret_scan
        else "Secret scanning is disabled for this project (secret_scan: false)."
    )

    lines = [
        "**Commit authority (issue #694):** this project has "
        f"`auto_commit.mode: {mode}` enabled for your role.",
    ]

    if mode == "suggest":
        lines.append(
            "When a configured trigger condition is met, propose a "
            "ready-to-use commit message in your own final report -- do "
            "NOT run `git commit` yourself, and do not stop and wait for "
            "confirmation before continuing your work. The user or "
            "orchestrator decides when to act on your suggestion."
        )
    elif mode == "custom":
        script = resolved.get("custom_script")
        lines.append(
            f"Commit directly whenever `{script}` exits 0 (the project's "
            "own commit-decision script has full control; no other "
            "trigger applies)."
        )
        lines.append(scan_line)
        lines.append(
            "Prefix the Bash command with `#agent-meta:agent=<your-role-"
            "name>` as its first line before `git add`/`git commit` -- "
            "required for the guard hook to authorize the commit on "
            "hook-capable providers, harmless elsewhere."
        )
    else:  # auto
        triggers = resolved.get("triggers", [])
        threshold = resolved.get("file_count_threshold", 5)
        trigger_descriptions = [
            f"{t} ({_TRIGGER_PROSE[t].format(n=threshold)})"
            for t in triggers
            if t in _TRIGGER_PROSE
        ]
        lines.append(
            "Commit directly as soon as ANY of the following is true: "
            + "; ".join(trigger_descriptions) + "."
        )
        lines.append(scan_line)
        lines.append(
            "Prefix the Bash command with `#agent-meta:agent=<your-role-"
            "name>` as its first line before `git add`/`git commit` -- "
            "required for the guard hook to authorize the commit on "
            "hook-capable providers, harmless elsewhere."
        )

    lines.append(
        "This commit authority never extends to pushing, tagging, or "
        "branch management -- those remain exclusively the `git` role's "
        "job."
    )
    return "\n".join(lines)
