"""Snippet collection and syncing for providers."""

from pathlib import Path

from .log import SyncLog

SNIPPETS_DIR = "snippets"


def sync_snippets_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
):
    """Copy snippet files from agent-meta/snippets/ to the provider-specific snippets dir.

    Only copies snippets referenced via TESTER_SNIPPETS_PATH (or similar *_SNIPPETS_PATH
    variables) in the project config. Unknown snippet files are skipped.
    All referenced paths are resolved relative to agent-meta/snippets/.
    """
    from .agents import extract_frontmatter_field

    pc = provider_config.get(provider, {})
    snippets_dir_rel = pc.get('snippets_dir')
    if not snippets_dir_rel:
        log.info("snippets", f"skipped for {provider} — no snippets_dir configured")
        return

    variables = config.get("variables", {})
    snippets_root = agent_meta_root / SNIPPETS_DIR
    target_root = project_root / snippets_dir_rel

    if not snippets_root.exists():
        return

    # Collect all *_SNIPPETS_PATH values from config variables
    snippet_paths: list[str] = [
        v for k, v in variables.items()
        if k.endswith("_SNIPPETS_PATH") and v
    ]

    # Remove stale snippet files no longer referenced in config
    expected_rel_paths: set[str] = set(snippet_paths)
    if target_root.exists():
        for existing in target_root.rglob("*.md"):
            rel = existing.relative_to(target_root).as_posix()
            if rel not in expected_rel_paths:
                log.action("DELETE", str(existing.relative_to(project_root)), "stale snippet")
                if not dry_run:
                    existing.unlink()

    if not snippet_paths:
        return

    for rel_path in snippet_paths:
        source_path = snippets_root / rel_path
        if not source_path.exists():
            log.warn(f"Snippet not found: snippets/{rel_path}")
            continue

        target_path = target_root / rel_path
        source_content = source_path.read_text(encoding="utf-8")
        snippet_version = extract_frontmatter_field(source_content, "version")
        version_label = f"@{snippet_version}" if snippet_version else ""

        log.action(
            "COPY",
            str(target_path.relative_to(project_root)),
            f"snippets/{rel_path}{version_label}",
        )
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(source_content, encoding="utf-8")
