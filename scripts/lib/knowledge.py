"""Knowledge Engine Phase A — bundle scaffolding helpers.

Pure rendering functions only. No filesystem writes happen here — callers
(sync_knowledge_engine() in scripts/sync.py) own all I/O and idempotency
decisions.
"""

from pathlib import Path

DOMAIN_CONCEPT_TYPES: dict[str, list[str]] = {
    "research": ["paper", "finding", "method", "dataset"],
    "personal": ["person", "event", "place", "memory"],
    "business": ["customer", "deal", "product", "decision"],
    "book": ["character", "location", "theme", "chapter"],
    "internal-docs": ["concept", "architecture", "guide", "reference"],
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
