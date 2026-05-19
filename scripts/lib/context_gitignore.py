""".gitignore management: managed block with additive or exact mode."""

import re
from pathlib import Path

from .log import SyncLog

GITIGNORE_BLOCK_BEGIN = "# --- agent-meta managed (do not edit) ---"
GITIGNORE_BLOCK_END   = "# --- end agent-meta managed ---"


def ensure_gitignore_entries(
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    gitignore_entries: list[str] | None = None,
    exact_entries: list[str] | None = None,
):
    """Ensure required entries exist in a managed block in .gitignore.

    Writes a clearly marked block so users know the entries are managed by
    agent-meta and should not be removed manually.

    gitignore_entries: entries to add (additive — never removes existing block entries).
    exact_entries: if provided, the managed block is set to exactly these entries
                   (entries no longer needed are removed from the block).
    """
    if exact_entries is not None:
        required = list(exact_entries)
    elif gitignore_entries is not None:
        required = list(gitignore_entries)
    else:
        # Default: Claude entries (backward compat)
        required = [
            ".claude/settings.local.json",
            ".claude/agent-memory-local/",
            "CLAUDE.personal.md",
            "sync.log",
        ]

    gitignore_path = project_root / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""

    # Extract current block content if present
    block_pattern = re.compile(
        re.escape(GITIGNORE_BLOCK_BEGIN) + r"(.*?)" + re.escape(GITIGNORE_BLOCK_END),
        re.DOTALL,
    )
    block_match = block_pattern.search(existing)
    block_entries: set[str] = set()
    if block_match:
        block_entries = {
            line.strip() for line in block_match.group(1).splitlines() if line.strip()
        }

    required_set = set(required)
    if exact_entries is not None:
        # Exact mode: block must contain exactly required_set
        new_block_entries = sorted(required_set)
        changed = block_entries != required_set
        added = sorted(required_set - block_entries)
        removed = sorted(block_entries - required_set)
    else:
        # Additive mode: add missing entries, never remove
        missing = [e for e in required if e not in block_entries]
        if not missing:
            log.skip(".gitignore", "all required entries already present")
            return
        new_block_entries = sorted(block_entries | required_set)
        changed = True
        added = missing
        removed = []

    if not changed:
        log.skip(".gitignore", "all required entries already present")
        return

    new_block = (
        GITIGNORE_BLOCK_BEGIN + "\n"
        + "\n".join(new_block_entries) + "\n"
        + GITIGNORE_BLOCK_END
    )

    if block_match:
        new_content = block_pattern.sub(new_block, existing)
    else:
        new_content = existing.rstrip("\n") + "\n\n" + new_block + "\n"

    parts = []
    if added:
        parts.append(f"added: {', '.join(added)}")
    if removed:
        parts.append(f"removed: {', '.join(removed)}")
    log.action("UPDATE", ".gitignore", f"managed block — {'; '.join(parts)}")
    if not dry_run:
        gitignore_path.write_text(new_content, encoding="utf-8")
