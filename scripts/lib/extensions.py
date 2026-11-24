"""Extension file management: create, update managed block."""
from __future__ import annotations

from pathlib import Path

from .io import safe_path
from .log import SyncLog
from .managed_block import (
    ManagedBlockError, has_block, has_drift, replace_block, stamp_block,
)

CLAUDE_EXT_DIR = ".claude/3-project"
EXT_SUFFIX = "-ext"

# Paths to template files (relative to agent-meta root)
_MANAGED_BLOCK_TEMPLATE_PATH = "templates/managed-block.md"
_PROJECT_STUB_TEMPLATE_PATH = "templates/managed-block-project-stub.md"


def _load_managed_block_template(agent_meta_root: Path) -> str:
    """Load managed-block template from templates/managed-block.md."""
    template_path = agent_meta_root / _MANAGED_BLOCK_TEMPLATE_PATH
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Inline fallback if template file is missing
    return (
        "<!-- agent-meta:managed-begin -->\n"
        "<!-- This block is automatically updated by sync.py on --update-ext. -->\n"
        "<!-- Project-specific additions belong in the section BELOW this marker. -->\n"
        "\n"
        "**Projekt:** {{PROJECT_NAME}} | **Plattform:** {{PLATFORM}}\n"
        "**Runtime:** {{RUNTIME}}\n"
        "**Build:** `{{BUILD_COMMAND}}`\n"
        "**Test:** `{{TEST_COMMAND}}`\n"
        "<!-- agent-meta:managed-end -->"
    )


def _load_project_stub_template(agent_meta_root: Path) -> str:
    """Load project section stub from templates/managed-block-project-stub.md."""
    template_path = agent_meta_root / _PROJECT_STUB_TEMPLATE_PATH
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    # Inline fallback
    return (
        "\n\n---\n\n"
        "## Projektspezifische Erweiterungen\n\n"
        "<!-- This section is NEVER modified by sync.py. -->\n"
        "<!-- Add project-specific knowledge, rules, and patterns here. -->\n"
    )


def render_managed_block(
    variables: dict,
    source_label: str,
    log: SyncLog,
    agent_meta_root: Path | None = None,
) -> str:
    """Render the managed block content from config variables."""
    from .config import substitute

    if agent_meta_root is not None:
        template = _load_managed_block_template(agent_meta_root)
    else:
        # Fallback: try to find agent-meta root from this file's location
        template = _load_managed_block_template(Path(__file__).resolve().parent.parent.parent)

    content = substitute(template, variables, source_label, log)
    return content


def _render_extension_managed_block(
    variables: dict,
    source_label: str,
    log: SyncLog,
    agent_meta_root: Path | None = None,
) -> str:
    """Render the managed block for an extension and drop unresolved lines.

    IC-15 Nr. 19: an extension (``--create-ext``/``--update-ext``) must never
    contain a literal ``{{VAR}}``; a line whose variable is not set is omitted
    entirely (the shared ``context.omit_unresolved_placeholder_lines`` rule).
    """
    from .context import omit_unresolved_placeholder_lines

    return stamp_block(omit_unresolved_placeholder_lines(
        render_managed_block(variables, source_label, log, agent_meta_root),
        log, source_label,
    ))


def update_managed_block(existing: str, new_managed: str) -> str:
    """Replace the managed block in an existing extension file."""
    return replace_block(existing, new_managed)


def create_extension(
    project_root: Path,
    config: dict,
    variables: dict,
    role: str,
    log: SyncLog,
    dry_run: bool,
    agent_meta_root: Path | None = None,
):
    """Create .claude/3-project/<prefix>-<role>-ext.md if it does not exist yet."""
    from .frontmatter import ext_target_filename
    from .roles import build_role_map

    if agent_meta_root is None:
        agent_meta_root = Path(__file__).resolve().parent.parent.parent

    role_map = build_role_map(agent_meta_root)
    if role not in role_map:
        import sys
        print(f"  !  Unknown role '{role}'. Valid roles: {', '.join(role_map)}", file=sys.stderr)
        return

    prefix = (config.get("project") or {}).get("prefix", "")
    filename = ext_target_filename(role, prefix)
    target_path = safe_path(project_root, CLAUDE_EXT_DIR, filename)

    if target_path.exists():
        log.skip(str(target_path.relative_to(project_root)), "extension already exists — use --update-ext to update")
        return

    managed = _render_extension_managed_block(
        variables, f"--create-ext {role}", log, agent_meta_root
    )
    project_stub = _load_project_stub_template(agent_meta_root)
    content = managed + project_stub

    log.action("CREATE", str(target_path.relative_to(project_root)), f"generated for role '{role}'")
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def update_extensions(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    agent_meta_root: Path | None = None,
    force: bool = False,
    role: str | None = None,
) -> list:
    """Update the managed block in all existing extension files.

    Files with a missing marker or a hand-edited block (hash drift) are warned
    about and skipped unless *force*. *role* limits the run to one extension. Returns the drifted/skipped file names.
    """
    from .roles import build_role_map

    drifted: list = []
    matched = 0
    ext_dir = project_root / CLAUDE_EXT_DIR
    if not ext_dir.exists():
        log.skip(CLAUDE_EXT_DIR, "directory not found — no extensions to update")
        return drifted

    roles = list(build_role_map(agent_meta_root or Path(__file__).resolve().parent.parent.parent))

    for ext_file in sorted(ext_dir.glob(f"*{EXT_SUFFIX}.md")):
        existing = ext_file.read_text(encoding="utf-8")
        rel = ext_file.relative_to(project_root)
        stem = ext_file.name[: -len(EXT_SUFFIX + ".md")]
        # longest role wins, so "am-senior-developer" is not the "developer" extension
        owner = max((r for r in roles if stem == r or stem.endswith("-" + r)),
                    key=len, default=None)
        if role and owner != role:
            continue
        matched += 1
        if owner is None:
            log.warn(f"{rel}: no template role for this extension (orphan)")
        new_managed = _render_extension_managed_block(
            variables, str(ext_file.name), log, agent_meta_root
        )
        try:
            if not has_block(existing):
                log.warn(f"{rel}: managed-begin marker missing — skipped")
                drifted.append(ext_file.name)
                continue
            if has_drift(existing) and not force:
                log.warn(f"{rel}: managed block edited manually (hash drift) — skipped, use --force")
                drifted.append(ext_file.name)
                continue
            new_content = update_managed_block(existing, new_managed)
        except ManagedBlockError as exc:
            log.warn(f"{rel}: {exc} — skipped")
            continue

        if new_content == existing:
            log.note_unchanged(str(ext_file.relative_to(project_root)))
        else:
            log.action("UPDATE", str(ext_file.relative_to(project_root)), "managed block")
            if not dry_run:
                ext_file.write_text(new_content, encoding="utf-8")
    if role and not matched:
        log.warn(f"--role {role}: no extension file matches")
    return drifted
