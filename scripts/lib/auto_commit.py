"""Opt-in tiered commit authority for write-capable agents (issue #694).

Role authority is derived from each role's OWN generic template frontmatter
`tools:` list -- never a hand-maintained allowlist and never a provider-name
branch, so it stays correct as new roles are added.

Issue #767 refines the coarse "can write" boolean into four capability classes
that mirror what a role can actually do with the files it changes:

    direct   -- Bash AND {Edit,Write}: commits itself (`git add`/`commit`)
    delegate -- {Edit,Write}, no Bash, spawn-capable (Agent/Task): delegates
                the commit to the `git` agent
    notify   -- {Edit,Write}, no Bash, not spawn-capable: never runs git;
                reports changed files + a ready-to-use message upstream
    none     -- otherwise (read-only role): empty block

`eligible_roles` (the guard-hook allowlist) stays DIRECT-ONLY: only roles that
can run Bash themselves may ever hold the hook sentinel.
"""

from __future__ import annotations

import re
from pathlib import Path

from .frontmatter import parse_frontmatter_file

_ELIGIBLE_TOOLS = {"Edit", "Write"}
_SPAWN_TOOLS = {"Agent", "Task"}

ALLOWLIST_VERSION = 1

# Authority literal values (mirrors the capability table in the module docstring).
AUTHORITY_DIRECT = "direct"
AUTHORITY_DELEGATE = "delegate"
AUTHORITY_NOTIFY = "notify"
AUTHORITY_NONE = "none"

_SENTINEL_PREFIX_LINE = (
    "Prefix the Bash command with `#agent-meta:agent=<your-role-name>` as its "
    "first line before `git add`/`git commit` -- required for the guard hook "
    "to authorize the commit on hook-capable providers, harmless elsewhere."
)

_BOM_LINE = (
    "Ensure the commit message has no leading UTF-8 BOM — the subject must "
    "start at byte 0 with the Conventional-Commit type (issue #842); the "
    "guard hook rejects a BOM-prefixed commit."
)

_PUSH_BOUNDARY_LINE = (
    "This commit authority never extends to pushing, tagging, or branch "
    "management -- those remain exclusively the `git` role's job."
)

_CONFIG_ERROR_LINE = (
    "Commit authority is misconfigured: `mode: custom` requires "
    "`custom_script` to be set, but none is configured. Report this as a "
    "config error instead of committing."
)


def _template_path(role: str, agent_meta_root: Path, platform: str | None = None) -> Path | None:
    """Resolve a role's own generic template path.

    Platform overrides (agents/2-platform/<platform>-<role>.md) are not
    consulted here on purpose: authority must reflect the role's BASE tools
    contract, which platforms compose onto (extend), never replace the tools
    list of. If a future platform ever does replace `tools:`, revisit this --
    out of scope for issue #694/#767.
    """
    candidate = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
    return candidate if candidate.is_file() else None


def _normalize_tools(tools) -> set[str]:
    """Normalize a frontmatter `tools:` value to a set of tool names.

    Accepts the raw frontmatter forms a YAML list, a comma/space-separated
    string, or `*` (wildcard). Anything else yields an empty set.
    """
    if tools is None:
        return set()
    if isinstance(tools, str):
        if tools.strip() == "*":
            return {"*"}
        items = re.split(r"[,\s]+", tools)
    elif isinstance(tools, (list, tuple)):
        items = tools
    else:
        return set()
    return {str(i).strip() for i in items if str(i).strip()}


def _role_tools(role: str, agent_meta_root: Path, platform: str | None = None) -> set[str]:
    """Return the role's base 1-generic `tools:` set, or an empty set."""
    path = _template_path(role, agent_meta_root, platform)
    if path is None:
        return set()
    frontmatter = parse_frontmatter_file(path)
    return _normalize_tools(frontmatter.get("tools"))


def _can_spawn(tools: set[str]) -> bool:
    """Spawn capability: Agent/Task tool, or a `*` wildcard.

    Semantics mirror `agent_sync._tools_can_spawn`; duplicated here to avoid a
    load-time import cycle (auto_commit is imported by config/agent_sync).
    """
    return "*" in tools or bool(_SPAWN_TOOLS & tools)


def role_commit_authority(
    role: str, agent_meta_root: Path, platform: str | None = None
) -> str:
    """Classify a role's real commit authority from its 1-generic `tools:`.

    Returns one of "direct" | "delegate" | "notify" | "none" (see module
    docstring). `platform` is accepted for symmetry with `is_role_eligible`
    but not consulted (base contract only).
    """
    tools = _role_tools(role, agent_meta_root, platform)
    if not (_ELIGIBLE_TOOLS & tools):
        return AUTHORITY_NONE
    if "Bash" in tools:
        return AUTHORITY_DIRECT
    if _can_spawn(tools):
        return AUTHORITY_DELEGATE
    return AUTHORITY_NOTIFY


def is_role_eligible(role: str, agent_meta_root: Path, platform: str | None = None) -> bool:
    """True only if `role` can commit DIRECTLY (Bash AND Edit/Write).

    Direct-only on purpose: `eligible_roles` gates the guard-hook sentinel,
    which authorizes the role to run `git add`/`git commit` itself. Delegate/
    notify roles must never hold that sentinel.
    """
    return role_commit_authority(role, agent_meta_root, platform) == AUTHORITY_DIRECT


def resolve_auto_commit_config(
    config: dict,
    active_roles: list[str],
    agent_meta_root: Path,
    platform: str | None = None,
) -> dict:
    """Resolve project.yaml's auto_commit block into the allowlist shape
    written to .meta-config/auto-commit-allowlist.json by the sync
    pipeline (Task 6).

    `eligible_roles` lists only active roles with DIRECT commit capability
    (Bash + Edit/Write). It is deliberately mode-independent (capability, not
    a mode-gated grant); the guard hook keys the actual sentinel on `mode`.
    """
    ac_cfg = config.get("auto_commit", {}) or {}
    mode = ac_cfg.get("mode", "off")

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


def _describe_triggers(resolved: dict) -> str:
    """Render the configured trigger list as a single prose fragment."""
    triggers = resolved.get("triggers", [])
    threshold = resolved.get("file_count_threshold", 5)
    descriptions = [
        f"{t} ({_TRIGGER_PROSE[t].format(n=threshold)})"
        for t in triggers
        if t in _TRIGGER_PROSE
    ]
    return "; ".join(descriptions)


def render_auto_commit_block(resolved: dict, authority: str = AUTHORITY_DIRECT) -> str:
    """Render the `{{AUTO_COMMIT_BLOCK}}` prose for a role at `authority`.

    Mode dominates authority (see the mode x authority matrix in the #767
    spec): "off" renders nothing for everyone, "suggest" is authority-agnostic
    (propose-only), "auto"/"custom" select prose by authority. Never mentions
    push/tag/branch as something the role may do -- those remain the `git`
    role's exclusive job. An unknown/None `authority` fails CLOSED (rendered
    as "none", i.e. ""); only the explicit default parameter is "direct".
    """
    if authority not in (
        AUTHORITY_DIRECT,
        AUTHORITY_DELEGATE,
        AUTHORITY_NOTIFY,
        AUTHORITY_NONE,
    ):
        # Fail-CLOSED: an unknown/None authority is treated as "no authority"
        # rather than silently granting the strongest (direct) prose. The
        # ``authority="direct"`` default parameter is unaffected -- only
        # invalid explicit values are downgraded.
        authority = AUTHORITY_NONE

    mode = resolved.get("mode", "off")
    if mode == "off" or authority == AUTHORITY_NONE:
        return ""

    secret_scan = resolved.get("secret_scan", True)
    scan_line = (
        "Before committing, run the project's secret scan against your "
        "staged changes; a finding blocks the commit -- report it and ask "
        "for manual intervention instead of committing anyway."
        if secret_scan
        else "Secret scanning is disabled for this project (secret_scan: false)."
    )
    # F1 (issue #767): the `secret_scan` requirement must reach every
    # write-capable authority, not just `direct`. For `delegate` the party
    # performing the commit runs the scan; for `notify` the caller/orchestrator
    # does. When `secret_scan: false` the requirement is simply omitted.
    delegate_scan_line = (
        "Before delegating the commit, run the project's secret scan against "
        "the staged changes; a finding blocks the commit -- report it and ask "
        "for manual intervention instead of delegating anyway."
    )
    notify_scan_line = (
        "Before the reported message is committed, the caller/orchestrator "
        "must run the project's secret scan against the reported files; a "
        "finding blocks the commit -- report it and ask for manual "
        "intervention."
    )

    lines = [
        "**Commit authority (issue #694):** this project has "
        f"`auto_commit.mode: {mode}` enabled for your role.",
    ]

    if mode == "suggest":
        # Authority-agnostic by design: whoever you are, propose -- never commit.
        lines.append(
            "When a configured trigger condition is met, propose a "
            "ready-to-use commit message in your own final report -- do "
            "NOT run `git commit` yourself, and do not stop and wait for "
            "confirmation before continuing your work. The user or "
            "orchestrator decides when to act on your suggestion."
        )
    elif mode == "custom":
        script = resolved.get("custom_script")
        if not script:
            # Defense in depth: the schema already rejects this combination,
            # but never render the literal word "None" into agent prose.
            lines.append(_CONFIG_ERROR_LINE)
            return "\n".join(lines)
        if authority == AUTHORITY_DIRECT:
            lines.append(
                f"Commit directly whenever `{script}` exits 0 (the project's "
                "own commit-decision script has full control; no other "
                "trigger applies)."
            )
            lines.append(scan_line)
            lines.append(_SENTINEL_PREFIX_LINE)
        elif authority == AUTHORITY_DELEGATE:
            lines.append(
                f"Whenever `{script}` exits 0 (the project's own "
                "commit-decision script has full control), do NOT run `git` "
                "yourself; instead delegate the commit to the `git` agent, "
                "handing it the changed files and a ready-to-use "
                "Conventional-Commits message."
            )
            if secret_scan:
                lines.append(delegate_scan_line)
        else:  # notify
            lines.append(
                f"Whenever `{script}` exits 0 (the project's own "
                "commit-decision script has full control), include the "
                "changed files and a ready-to-use Conventional-Commits "
                "message in your result/report. Do NOT run `git` yourself; "
                "the caller/orchestrator applies the commit."
            )
            if secret_scan:
                lines.append(notify_scan_line)
    else:  # auto
        triggers = _describe_triggers(resolved)
        if authority == AUTHORITY_DIRECT:
            lines.append(
                "Commit directly as soon as ANY of the following is true: "
                + triggers + "."
            )
            lines.append(scan_line)
            lines.append(_SENTINEL_PREFIX_LINE)
        elif authority == AUTHORITY_DELEGATE:
            lines.append(
                "At each configured trigger boundary -- as soon as ANY of "
                "the following is true: " + triggers + " -- do NOT run "
                "`git` yourself. Instead delegate the commit to the `git` "
                "agent, handing it the changed files and a ready-to-use "
                "Conventional-Commits message."
            )
            if secret_scan:
                lines.append(delegate_scan_line)
        else:  # notify
            lines.append(
                "Include the changed files and a ready-to-use "
                "Conventional-Commits message in your result/report at each "
                "configured trigger boundary -- as soon as ANY of the "
                "following is true: " + triggers + ". Do NOT run `git` "
                "yourself; the caller/orchestrator applies the commit."
            )
            if secret_scan:
                lines.append(notify_scan_line)

    lines.append(_BOM_LINE)
    lines.append(_PUSH_BOUNDARY_LINE)
    return "\n".join(lines)
