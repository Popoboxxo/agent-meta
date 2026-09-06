"""Knowledge Engine Phase A — bundle scaffolding.

Rendering helpers (pure) plus the I/O-owning sync entry point
``sync_knowledge_engine`` (moved from scripts/sync.py by issue #481). The
sync function owns all filesystem writes and idempotency decisions.
"""

from pathlib import Path

from .io import SyncError, safe_path, write_checked
from .log import SyncLog

DOMAIN_CONCEPT_TYPES: dict[str, list[str]] = {
    "research": ["paper", "finding", "method", "dataset"],
    "personal": ["person", "event", "place", "memory"],
    "business": ["customer", "deal", "product", "decision"],
    "book": ["character", "location", "theme", "chapter"],
    "internal-docs": ["concept", "architecture", "guide", "reference"],
    "technical": ["architecture", "component", "interface", "protocol"],
    "custom": ["concept"],
}

_TEMPLATE_REL_PATH = ("templates", "knowledge-schema.template.md")


def generate_schema(domain: str, bundle_path: str, agent_meta_root: Path) -> str:
    """Render knowledge-schema.template.md for the given domain.

    Raises ValueError when domain is not a key of DOMAIN_CONCEPT_TYPES —
    callers must treat this as a hard sync error (SyncError), not a silent
    fallback, per the Phase A error-handling contract.
    """
    if domain not in DOMAIN_CONCEPT_TYPES:
        raise ValueError(
            f"Unknown knowledge-engine domain '{domain}' — must be one of: "
            + ", ".join(sorted(DOMAIN_CONCEPT_TYPES))
        )
    template_path = agent_meta_root.joinpath(*_TEMPLATE_REL_PATH)
    template = template_path.read_text(encoding="utf-8")
    concept_list = "\n".join(f"- {c}" for c in DOMAIN_CONCEPT_TYPES[domain])
    return (
        template
        .replace("{{KNOWLEDGE_DOMAIN}}", domain)
        .replace("{{KNOWLEDGE_CONCEPT_TYPES}}", concept_list)
        .replace("{{KNOWLEDGE_BUNDLE_PATH}}", bundle_path)
    )


def generate_initial_index() -> str:
    """Render the empty index.md skeleton for a freshly scaffolded bundle."""
    return (
        "# Knowledge Index\n\n"
        "> Auto-maintained entry point into the knowledge bundle. Lists all "
        "concepts, entities and topics as they are added.\n\n"
        "## Concepts\n\n"
        "(none yet)\n\n"
        "## Entities\n\n"
        "(none yet)\n\n"
        "## Topics\n\n"
        "(none yet)\n"
    )


def generate_initial_log() -> str:
    """Render the empty log.md skeleton with header + format documentation."""
    return (
        "# Knowledge Log\n\n"
        "> Append-only change log for the knowledge bundle. One entry per "
        "ingest/update/query operation.\n\n"
        "## Format\n\n"
        "```\n"
        "YYYY-MM-DD HH:MM — <operation> — <summary>\n"
        "```\n\n"
        "## Entries\n\n"
        "(none yet)\n"
    )


# ---------------------------------------------------------------------------
# Sync entry point (moved verbatim from scripts/sync.py, issue #481)
# ---------------------------------------------------------------------------

_KNOWLEDGE_GITKEEP_SUBDIRS = [
    Path("sources", "assets"),
    Path("wiki", "concepts"),
    Path("wiki", "entities"),
    Path("wiki", "topics"),
    Path("wiki", "sources"),
    Path("wiki", "queries"),
]


def sync_knowledge_engine(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Phase 2.5 — scaffold the knowledge/ bundle when knowledge-engine.enabled is true.

    No-op (zero-overhead) when disabled or absent. Idempotent: never
    overwrites existing schema.md/wiki/index.md/wiki/log.md, only fills in
    missing .gitkeep markers in empty subdirectories on subsequent runs.
    """
    ke_config = config.get("knowledge-engine") or {}
    if not ke_config.get("enabled", False):
        log.skip("knowledge-engine", "disabled in project.yaml")
        return

    domain = ke_config.get("domain", "research")
    bundle_rel = ke_config.get("bundle-path", "knowledge")
    bundle_dir = safe_path(project_root, bundle_rel)

    if bundle_dir.exists() and not bundle_dir.is_dir():
        raise SyncError(
            f"knowledge-engine.bundle-path '{bundle_rel}' points to an existing "
            f"file, not a directory: {bundle_dir}"
        )

    bundle_exists = bundle_dir.is_dir()

    if not bundle_exists:
        try:
            schema_content = generate_schema(domain, bundle_rel, agent_meta_root)
        except ValueError as exc:
            raise SyncError(f"knowledge-engine: {exc}") from exc

        if not dry_run:
            (bundle_dir / "wiki").mkdir(parents=True, exist_ok=True)

        schema_path = bundle_dir / "schema.md"
        rel_schema = f"{bundle_rel}/schema.md"
        if write_checked(schema_path, schema_content, log, rel_schema, dry_run=dry_run):
            log.action("CREATE", rel_schema, "knowledge-engine scaffolding")

        index_path = bundle_dir / "wiki" / "index.md"
        rel_index = f"{bundle_rel}/wiki/index.md"
        if write_checked(index_path, generate_initial_index(), log, rel_index, dry_run=dry_run):
            log.action("CREATE", rel_index, "knowledge-engine scaffolding")

        log_path = bundle_dir / "wiki" / "log.md"
        rel_log = f"{bundle_rel}/wiki/log.md"
        if write_checked(log_path, generate_initial_log(), log, rel_log, dry_run=dry_run):
            log.action("CREATE", rel_log, "knowledge-engine scaffolding")
    else:
        log.note(
            "knowledge-engine",
            f"{bundle_rel}/ already exists — schema.md/index.md/log.md not "
            "regenerated. If domain changed, verify schema.md manually "
            "(not auto-migrated in Phase A)."
        )

    for rel_subdir in _KNOWLEDGE_GITKEEP_SUBDIRS:
        target_dir = bundle_dir / rel_subdir
        gitkeep_path = target_dir / ".gitkeep"
        rel_gitkeep = f"{bundle_rel}/{rel_subdir.as_posix()}/.gitkeep"
        if not dry_run:
            target_dir.mkdir(parents=True, exist_ok=True)
        if write_checked(gitkeep_path, "", log, rel_gitkeep, dry_run=dry_run):
            log.action("CREATE", rel_gitkeep, "knowledge-engine scaffolding")
