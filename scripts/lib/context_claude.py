"""CLAUDE.md management: managed block, initialization, variable substitution."""

import re
from pathlib import Path

from .io import safe_path
from .log import SyncLog

# Path to the CLAUDE.md managed block template (relative to agent-meta root)
_CLAUDE_MD_MANAGED_TEMPLATE_PATH = "templates/claude-md-managed.md"


def _load_claude_md_managed_template(agent_meta_root: Path) -> str:
    """Load CLAUDE.md managed block template from templates/claude-md-managed.md."""
    template_path = agent_meta_root / _CLAUDE_MD_MANAGED_TEMPLATE_PATH
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Inline fallback if template file is missing
    return (
        "<!-- agent-meta:managed-begin -->\n"
        "<!-- This block is automatically updated by sync.py on every sync. -->\n"
        "<!-- Manual changes here will be overwritten. -->\n"
        "\n"
        "Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`\n"
        "DoD-Preset: **{{DOD_PRESET}}** | REQ-Traceability: {{DOD_REQ_TRACEABILITY}} | "
        "Tests: {{DOD_TESTS_REQUIRED}} | Codebase-Overview: {{DOD_CODEBASE_OVERVIEW}} | "
        "Security-Audit: {{DOD_SECURITY_AUDIT}}\n"
        "\n"
        "{{AGENT_HINTS}}\n"
        "<!-- agent-meta:managed-end -->"
    )


def sync_claude_md_managed(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    agent_meta_root: Path | None = None,
):
    """Update the managed block in CLAUDE.md if it exists and contains the marker."""
    from .config import substitute

    if agent_meta_root is None:
        agent_meta_root = Path(__file__).resolve().parent.parent.parent

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

    template = _load_claude_md_managed_template(agent_meta_root)
    new_managed = substitute(template, variables, "CLAUDE.md managed block", log)
    new_content = pattern.sub(new_managed, existing, count=1)

    if new_content == existing:
        log.skip("CLAUDE.md", "managed block unchanged")
    else:
        log.action("UPDATE", "CLAUDE.md", "managed block (AGENT_TABLE + version)")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


def init_claude_md(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Create CLAUDE.md from template if it does not exist."""
    from .config import substitute

    template_path = agent_meta_root / "howto" / "configs" / "CLAUDE.project-template.md"
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
    log.action("INIT", "CLAUDE.md", "howto/configs/CLAUDE.project-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def only_variables(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Substitute {{VARIABLE}} placeholders in existing CLAUDE.md."""
    import sys
    from .config import substitute

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
