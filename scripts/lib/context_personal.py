"""Personal and settings file initialization (created once, never overwritten)."""

from pathlib import Path

from .log import SyncLog


def init_claude_personal(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Copy CLAUDE.personal-template.md to CLAUDE.personal.md if not present yet."""
    template_path = agent_meta_root / "howto" / "configs" / "CLAUDE.personal-template.md"
    target_path = project_root / "CLAUDE.personal.md"

    if target_path.exists():
        log.skip("CLAUDE.personal.md", "already exists")
        return

    if not template_path.exists():
        log.warn("CLAUDE.personal-template.md not found — skipping CLAUDE.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "CLAUDE.personal.md", "howto/configs/CLAUDE.personal-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def init_opencode_personal(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Copy AGENTS.personal-template.md to AGENTS.personal.md if not present yet.

    Analogous to CLAUDE.personal.md — gitignored, never committed, loaded via
    the `instructions` field in opencode.json.
    """
    template_path = agent_meta_root / "howto" / "configs" / "AGENTS.personal-template.md"
    target_path = project_root / "AGENTS.personal.md"

    if target_path.exists():
        log.skip("AGENTS.personal.md", "already exists")
        return

    if not template_path.exists():
        log.warn("AGENTS.personal-template.md not found — skipping AGENTS.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "AGENTS.personal.md", "howto/configs/AGENTS.personal-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def init_settings_json(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Create .claude/settings.json if it does not exist yet.

    The file is created once as a skeleton for team-shared settings.
    The hooks section is managed separately by sync_hooks() on every sync.
    """
    target_path = project_root / ".claude" / "settings.json"
    if target_path.exists():
        log.skip(".claude/settings.json", "already exists")
        return

    content = '{\n  "permissions": {\n    "allow": [],\n    "deny": []\n  }\n}\n'
    log.action("INIT", ".claude/settings.json", "team permissions skeleton")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def init_settings_local_json(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Create .claude/settings.local.json skeleton if it does not exist yet.

    This file is gitignored and intended for personal / machine-local overrides
    (e.g. allow-listing commands during development, local hook overrides).
    Created once on --init or first Claude sync — never overwritten afterwards.
    """
    target_path = project_root / ".claude" / "settings.local.json"
    if target_path.exists():
        log.skip(".claude/settings.local.json", "already exists")
        return

    content = (
        '{\n'
        '  "permissions": {\n'
        '    "allow": [],\n'
        '    "deny": []\n'
        '  }\n'
        '}\n'
    )
    log.action("INIT", ".claude/settings.local.json", "personal/local settings skeleton (gitignored)")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
