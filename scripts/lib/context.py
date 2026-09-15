"""Context file management: CLAUDE.md managed block, provider context, gitignore, settings."""
from __future__ import annotations

import json
import re
from pathlib import Path

from .agents import build_agent_hints, build_knowledge_engine_hints
from .frontmatter import _strip_frontmatter
from .io import content_hash, is_absent_gitignored_target, load_json_file, safe_path
from .json_persistence import save_json_document
from .log import SyncLog
from .plugins import resolve_plugin_compact
from .rule_index import (
    bootstrap_previously_managed,
    cleanup_stale_managed_files,
    write_managed_index,
)
from .variables import (
    _orch_mode_flags,
    _resolve_orch_mode,
    repo_containment_variables,
    strip_inactive_conditional_blocks,
    substitute,
)
from .context_templates.builder import TemplateBuilder

SNIPPETS_DIR = "snippets"

# Sidecar store recording the hash of each generated static header, so a later
# sync can tell its own staleness apart from manual user edits.
_CONTEXT_HASHES_FILE = "context-hashes.json"
_CONTEXT_HASHES_DIR = ".meta-config"

# Marker that separates the static header from the managed block in context files.
_MANAGED_BLOCK_RE = re.compile(
    r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
    re.DOTALL,
)


def _has_duplicate_managed_block(text: str) -> bool:
    """Return True when *text* contains more than one managed-begin/end pair.

    ``_update_managed_html_block`` only ever replaces the first match
    (``count=1``). A second pair therefore stays behind untouched; surfacing it
    as a duplicate lets the caller warn instead of silently half-updating the
    file (AC-17 / OQ-6).
    """
    return len(_MANAGED_BLOCK_RE.findall(text)) > 1


def _context_hashes_path(project_root: Path) -> Path:
    return project_root / _CONTEXT_HASHES_DIR / _CONTEXT_HASHES_FILE


def _load_context_hashes(project_root: Path) -> dict:
    """Read .meta-config/context-hashes.json; return {} if absent or invalid.

    Canonical JSON loader (Issue #479), fail-soft: absent or malformed file
    yields {} — same contract as the former hand-rolled loader.
    """
    path = _context_hashes_path(project_root)
    data = load_json_file(path, on_error="default", default={})
    hashes = data.get("hashes") if isinstance(data, dict) else None
    return hashes if isinstance(hashes, dict) else {}


def _save_context_hashes(project_root: Path, hashes: dict, dry_run: bool) -> None:
    """Write the sidecar hash store (no-op in dry_run)."""
    if dry_run:
        return
    path = _context_hashes_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"version": 1, "hashes": hashes}
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _record_static_hash(
    project_root: Path, rel_label: str, header_text: str, dry_run: bool
) -> None:
    """Store hash(header_text) for rel_label in the sidecar store."""
    hashes = _load_context_hashes(project_root)
    hashes[rel_label] = content_hash(header_text)
    _save_context_hashes(project_root, hashes, dry_run)


def _split_context_file(text: str) -> tuple[str, str | None, str]:
    """Split a context file into (header, managed_block, footer).

    - header: everything above the managed-begin marker.
    - managed_block: the full begin..end block (None if the file has none).
    - footer: everything after the managed-end marker.

    Concatenating header + managed_block + footer reproduces the original text
    exactly, so it is safe to regenerate only the header and keep the rest.
    """
    match = _MANAGED_BLOCK_RE.search(text)
    if not match:
        return text, None, ""
    return text[:match.start()], match.group(0), text[match.end():]


def _split_injected_footer_tail(footer: str) -> tuple[str, str]:
    """Split a footer into (template_part, injected_tail).

    The injected tail is any trailing block appended below the template footer by
    a separate step or external tool — e.g. agent-meta's own bootstrap block
    (``<!-- agent-meta:bootstrap-begin -->``) or a third-party wrapper block. All
    of these are delimited by HTML comments, and the context template footers are
    plain markdown with no HTML comments below the managed block, so the first
    ``<!--`` in the footer reliably marks the boundary. Returning the tail
    separately lets us regenerate the template part of the footer while preserving
    every injected trailing block byte-for-byte, exactly like the managed block.
    """
    idx = footer.find("<!--")
    if idx == -1:
        return footer, ""
    return footer[:idx], footer[idx:]


def _normalize_static_sig(s: str) -> str:
    """Normalize a static-part signature: drop dates, collapse whitespace."""
    import re

    s = re.sub(r"\d{4}-\d{2}-\d{2}", "", s)
    return re.sub(r"\s+", " ", s).strip()


USER_NOTES_HEADING = "## Eigene Notizen"


def _user_notes_span(header: str) -> tuple[int, int] | None:
    """Locate the user-owned notes section inside a context-file header.

    The section starts at the ``## Eigene Notizen`` heading and ends at the next
    top-level boundary (``## `` heading or a ``---`` rule). Returns character
    offsets into ``header``, or None when the header has no such section.
    """
    lines = header.splitlines(keepends=True)
    start_line = next(
        (i for i, line in enumerate(lines) if line.strip() == USER_NOTES_HEADING), None
    )
    if start_line is None:
        return None
    end_line = len(lines)
    for j in range(start_line + 1, len(lines)):
        stripped = lines[j].strip()
        if stripped.startswith("## ") or stripped == "---":
            end_line = j
            break
    start = sum(len(x) for x in lines[:start_line])
    end = start + sum(len(x) for x in lines[start_line:end_line])
    return start, end


def _strip_user_notes(header: str) -> str:
    """Return the header without its user-owned notes section."""
    span = _user_notes_span(header)
    if span is None:
        return header
    return header[: span[0]] + header[span[1] :]


def _preserve_user_notes(new_header: str, existing_header: str) -> str:
    """Splice the project's own notes section into a freshly rendered header.

    The header is regenerated from the template on every sync, which used to
    delete everything a user had written under ``## Eigene Notizen`` — the one
    section the template explicitly promises never to overwrite (issue #515).
    """
    new_span = _user_notes_span(new_header)
    old_span = _user_notes_span(existing_header)
    if new_span is None or old_span is None:
        return new_header
    return (
        new_header[: new_span[0]]
        + existing_header[old_span[0] : old_span[1]]
        + new_header[new_span[1] :]
    )


def _backup_context_file(
    target_path: Path, existing_content: str, rel_label: str, log: SyncLog, dry_run: bool
) -> None:
    """Write a timestamped backup before overwriting a user-modified static part."""
    from datetime import datetime

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")  # noqa: DTZ005
    backup = target_path.with_name(f"{target_path.name}.sync-backup-{ts}")
    log.warning(
        f"{rel_label}: static part differs from the last generated version "
        f"(manual edit or first-time migration). Backup written to {backup.name} — "
        f"review and merge any wanted changes."
    )
    print(f"  !  {rel_label}: static part changed -> backup {backup.name}")
    if not dry_run:
        backup.write_text(existing_content, encoding="utf-8")


def _regenerate_static_context(
    project_root: Path,
    target_path: Path,
    template_path: Path | None,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    rel_label: str,
    source_label: str,
    rebuild_footer: bool = False,
) -> None:
    """Regenerate the static part of an existing managed context file.

    Distinguishes agent-meta's own staleness (hash matches the last generated
    static part → silent overwrite) from manual user edits (hash mismatch or no
    record → timestamped backup, then overwrite; drift is worse than a
    recoverable overwrite). The managed block is always preserved verbatim.

    The footer (everything below the managed block) is preserved verbatim by
    default (CLAUDE.md behaviour). When ``rebuild_footer`` is set — the AGENTS.md
    family, whose footer holds the dynamic ``## Agents`` provider list — the
    footer template part is regenerated from the template too, while any
    agent-injected trailing block (e.g. the bootstrap block) is preserved
    verbatim, exactly like the managed block. The static signature used for
    drift detection then covers header + template footer instead of header only.
    """

    if not target_path.exists():
        return
    if not template_path or not template_path.exists():
        log.note(rel_label, "no static template — skipping static regeneration")
        return

    fallback_partials = template_path.parent.parent / "context" / "partials"
    builder = TemplateBuilder(template_path.parent, fallback_partials_dir=fallback_partials)
    rendered = builder.build(template_path.stem, variables)
    new_header, _tmpl_managed, new_footer = _split_context_file(rendered)

    existing = target_path.read_text(encoding="utf-8")
    existing_header, existing_managed, existing_footer = _split_context_file(existing)
    if existing_managed is None:
        # File exists but has no managed block yet (e.g. a third-party tool
        # created it first without the agent-meta marker). Header/footer
        # regeneration needs a marker to split around, so it is deferred here;
        # the managed-block step later in this same sync run inserts the
        # marker (preserving this content verbatim), and the next sync will
        # then regenerate the static header/footer normally.
        log.note(rel_label, "no managed block yet — static regeneration deferred until marker exists")
        return

    # The notes section is user-owned: carry it over verbatim and keep it out of
    # the drift signature, so editing it neither loses content nor triggers a
    # spurious "static part differs" backup.
    new_header = _preserve_user_notes(new_header, existing_header)
    new_static, existing_static = _strip_user_notes(new_header), _strip_user_notes(existing_header)

    if rebuild_footer:
        existing_footer_tmpl, injected_tail = _split_injected_footer_tail(existing_footer)
        if injected_tail:
            # Re-attach the agent-injected tail below the fresh template footer,
            # reproducing the exact spacing the agents step uses when appending.
            target_footer = new_footer.rstrip("\n") + "\n\n" + injected_tail
        else:
            target_footer = new_footer
        # Signature covers header + template footer (ignoring the injected tail,
        # which is owned by the agents step and changes independently).
        new_sig = new_static + "\x00" + new_footer.rstrip("\n")
        existing_sig = existing_static + "\x00" + existing_footer_tmpl.rstrip("\n")
    else:
        target_footer = existing_footer
        new_sig = new_static
        existing_sig = existing_static

    norm_new = _normalize_static_sig(new_sig)
    norm_existing = _normalize_static_sig(existing_sig)

    if norm_existing == norm_new:
        log.skip(rel_label, "static part unchanged")
        _record_static_hash(project_root, rel_label, norm_new, dry_run)
        return

    stored = _load_context_hashes(project_root).get(rel_label)
    user_modified = stored is None or content_hash(norm_existing) != stored
    if user_modified:
        _backup_context_file(target_path, existing, rel_label, log, dry_run)

    new_content = new_header + existing_managed + target_footer
    log.action("UPDATE", rel_label, "static part regenerated from template")
    if not dry_run:
        target_path.write_text(new_content, encoding="utf-8")
    _record_static_hash(project_root, rel_label, norm_new, dry_run)
GITIGNORE_BLOCK_BEGIN = "# --- agent-meta managed (do not edit) ---"
GITIGNORE_BLOCK_END   = "# --- end agent-meta managed ---"

# sync_claude_md_managed was removed because it is dead code.


def _has_capability(pc: dict, capability: str) -> bool:
    """Return True if provider config lists the given capability."""
    return capability in pc.get("capabilities", [])


def _shared_rules_file_channel(
    pc: dict, provider_config: dict | None, shared_users: list[str]
) -> bool:
    """True when every provider sharing this context_file can load rules from
    separate files (progressive-disclosure file channel, issue #192 Phase 2).

    Expressed purely via config keys: a provider participates when a
    ``skills_dir`` is configured — the channel that receives non-embedded
    rules as ``<skills_dir>/<rule-stem>/SKILL.md`` (rendered on demand via
    Read). Deliberately NOT keyed on provider names (provider-agnostic
    policy): a future provider joining the shared file converges
    automatically. When any sharer lacks the channel, the caller embeds the
    rule instead of dropping it — a rules-preset opt-out must never delete
    content a provider cannot load from anywhere else.
    """
    if provider_config and shared_users:
        pcs = [provider_config.get(p, {}) for p in shared_users]
    else:
        pcs = [pc]
    return all(bool(p.get("skills_dir")) for p in pcs)


def _ensure_context_file(
    project_root: Path,
    agent_meta_root: Path,
    target_path: Path,
    template_path: Path | None,
    variables: dict,
    config: dict,
    log: SyncLog,
    dry_run: bool,
    fallback_agent_dir: str,
) -> None:
    """Create a provider context file from template or minimal fallback."""

    if target_path.exists():
        return

    if template_path and template_path.exists():
        fallback_partials = template_path.parent.parent / "context" / "partials"
        builder = TemplateBuilder(template_path.parent, fallback_partials_dir=fallback_partials)
        content = builder.build(template_path.stem, variables)
        source_label = str(template_path.relative_to(agent_meta_root))
    else:
        project_name = config["project"]["name"]
        content = (
            f"# {project_name}\n\n"
            "<!-- agent-meta:managed-begin -->\n"
            "<!-- agent-meta:managed-end -->\n\n"
            f"## Agents\n\n"
            f"Agent files are in {fallback_agent_dir} (invoke by name).\n"
        )
        source_label = f"minimal fallback ({template_path.name if template_path else 'no template'})"
    log.action("INIT", str(target_path.relative_to(project_root)), source_label)
    if not dry_run:
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")


def _core_context_filename(config: dict) -> str:
    """Resolve the canonical core context file (``context_file.core_file``).

    Config-driven with the spec default ``AGENTS.md``; a missing/non-mapping
    ``context_file`` block or a blank/non-string value degrades to the default
    without raising (IC-09).
    """
    block = config.get("context_file") if isinstance(config, dict) else None
    if isinstance(block, dict):
        core = block.get("core_file")
        if isinstance(core, str) and core.strip():
            return core
    return "AGENTS.md"


def _adapter_reference_line(config: dict, pc: dict) -> str | None:
    """Return the provider-native core reference line for an adapter file.

    Returns ``None`` when the provider is not adapter-capable. An explicit
    ``context_adapter_import_supported: true`` with a non-blank
    ``context_adapter_import`` renders that syntax with ``{core}`` substituted
    by ``context_file.core_file`` (e.g. ``@AGENTS.md``); any other combination
    (unsupported, absent, blank) falls back to a pointer line. Purely
    key-driven — no provider-name literal.
    """
    if pc.get("context_adapter") is not True:
        return None
    core_file = _core_context_filename(config)
    syntax = pc.get("context_adapter_import")
    if (
        pc.get("context_adapter_import_supported") is True
        and isinstance(syntax, str)
        and syntax.strip()
    ):
        line = syntax.replace("{core}", core_file).strip()
        if line:
            return line
    return f"Read `{core_file}` for the shared project context."


def _inject_adapter_line(managed_block: str, adapter_line: str) -> str:
    """Insert the provider-native core reference line into a managed block.

    Placed directly after the managed-begin marker — i.e. inside the
    regenerated block, never the static header — so the static-part hash stays
    stable across syncs (no backup oscillation) and the render is idempotent.
    A block without the marker is returned unchanged.
    """
    marker = "<!-- agent-meta:managed-begin -->"
    line = adapter_line.strip()
    if not line or marker not in managed_block:
        return managed_block
    return managed_block.replace(marker, f"{marker}\n{line}", 1)


def _update_managed_html_block(
    target_path: Path,
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    agent_meta_root: Path,
    provider: str = "Claude",
    pc: dict | None = None,
    adapter_line: str | None = None,
) -> None:
    """Update the HTML-style managed block in a context file.

    For Claude, the per-agent table is dropped from the managed block:
    Claude Code injects agent descriptions natively, so the table would be a
    duplication. Other providers keep the full table via {{AGENT_HINTS}}.

    If the file already exists but has no agent-meta marker at all — e.g. a
    third-party tool (Headroom/RTK and similar wrapper proxies) created it
    first without ever running sync.py — the foreign content is never
    discarded. The managed block is inserted above it instead, so agent-meta
    initializes itself alongside the pre-existing content rather than never
    initializing at all.
    """

    existing = target_path.read_text(encoding="utf-8")
    managed_pattern = re.compile(
        r"<!--\s*agent-meta:managed-begin\s*-->"
        r".*?<!--\s*agent-meta:managed-end\s*-->",
        re.DOTALL,
    )
    rel = str(target_path.relative_to(project_root))
    if _has_duplicate_managed_block(existing):
        log.warning(
            f"{rel}: contains more than one agent-meta managed block — only the "
            "first block is replaced; remove the duplicate marker pair to keep "
            "the file consistent."
        )
    render_vars = variables
    _has_dedicated = (pc or {}).get("has_dedicated_context_file", False)
    if _has_dedicated and "AGENT_HINTS_CLAUDE" in variables:
        render_vars = {**variables, "AGENT_HINTS": variables["AGENT_HINTS_CLAUDE"]}

    builder = TemplateBuilder(agent_meta_root / "templates" / "context")
    try:
        new_managed = builder.build("claude-managed", render_vars)
    except FileNotFoundError:
        log.warning(f"claude-managed template missing — using minimal inline fallback for {rel}.")
        new_managed = (
            "<!-- agent-meta:managed-begin -->\n"
            "<!-- Dieser Block wird von sync.py bei jedem sync automatisch aktualisiert. -->\n"
            "{{PROVIDER_ROUTING}}\n"
            "Generiert von agent-meta v{{AGENT_META_VERSION}} — `{{AGENT_META_DATE}}`\n"
            "{{AGENT_HINTS}}\n"
            "<!-- agent-meta:managed-end -->"
        )
        new_managed = substitute(new_managed, render_vars, "inline fallback", log)

    # For AGENTS.md, also inject dynamic content into the managed block:
    # 1. Provider agent locations (stays in sync with deactivations)
    # 2. Rules pointer (all providers share AGENTS.md, so all must produce
    #    the same managed block content to avoid ping-pong updates).
    if target_path.name == "AGENTS.md":
        agent_locations = variables.get("AGENT_LOCATIONS", "")
        if agent_locations:
            new_managed = new_managed.replace(
                '<!-- agent-meta:managed-end -->',
                f'\n## Agents\n\n{agent_locations}\n\n<!-- agent-meta:managed-end -->',
            )
        new_managed = new_managed.replace(
            '<!-- agent-meta:managed-end -->',
            '\n## Regeln\n\n> **Regeln:** Alle Regeln werden nativ über den Provider-Rules-Mechanismus geladen.\n\n<!-- agent-meta:managed-end -->',
        )

    if adapter_line:
        new_managed = _inject_adapter_line(new_managed, adapter_line)

    if not managed_pattern.search(existing):
        if not new_managed.strip():
            log.warning(
                f"{rel}: exists but has no agent-meta marker, and the managed "
                "block could not be rendered — leaving the file untouched. "
                "Add the following block manually at the desired location:\n"
                "  <!-- agent-meta:managed-begin -->\n"
                "  <!-- agent-meta:managed-end -->"
            )
            return
        new_content = _insert_managed_block_above_foreign_content(existing, new_managed)
        log.action(
            "INIT", rel,
            "managed block inserted — file existed without an agent-meta "
            "marker (foreign content preserved below)",
        )
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")
        return

    # Function replacement: new_managed is rendered template content and
    # must be inserted verbatim (#674 escape-safety).
    new_content = managed_pattern.sub(lambda _m: new_managed, existing, count=1)
    if new_content != existing:
        log.action("UPDATE", rel, "managed block")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")
    else:
        log.skip(rel, "managed block unchanged")


def _insert_managed_block_above_foreign_content(existing: str, new_managed: str) -> str:
    """Prepend a freshly rendered managed block above pre-existing foreign content.

    Used when a context file already exists but was never initialized by
    agent-meta (no ``agent-meta:managed-begin/-end`` marker) — e.g. created by
    a third-party tool such as Headroom/RTK. The foreign content is kept
    byte-for-byte as a trailing block, mirroring how ``_split_injected_footer_tail``
    already treats agent-injected trailing blocks below agent-meta's own
    managed block.
    """
    stripped = existing.strip()
    if not stripped:
        return new_managed.rstrip("\n") + "\n"
    return new_managed.rstrip("\n") + "\n\n" + existing


def _sync_managed_block_context(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
    target_name: str | None = None,
    adapter_line: str | None = None,
) -> None:
    """Strategy for providers with a context file using HTML managed blocks.

    ``target_name`` overrides the physical filename chosen by the
    ``per-provider`` dispatch (IC-09); ``adapter_line`` is the provider-native
    core reference injected into the managed block when the provider reads an
    adapter file. Both default to the legacy single-file behaviour.
    """

    pc = provider_config[provider]
    context_file = target_name or pc.get("context_file")
    if not context_file:
        return
    target_path = safe_path(project_root, context_file)
    template_name = pc.get("context_template")
    template_path = agent_meta_root / template_name if template_name else None

    # build_agent_hints is imported at module top level — the lazy import was
    # vestigial (agents does not import context; Issue #478 cleanup, guarded
    # by tests/test_import_acyclicity.py).
    orch_config = config.get("orchestrator", {})
    provider_override = orch_config.get("provider-overrides", {}).get(provider, {})
    _orch_mode = _resolve_orch_mode(orch_config, provider_override)
    
    local_config = config.copy()
    if "orchestrator" in local_config:
        local_orch = local_config["orchestrator"].copy()
        local_orch["mode"] = _orch_mode
        local_config["orchestrator"] = local_orch

    # Driven by the `has_dedicated_context_file` capability flag (issue #631)
    # instead of a literal `provider == "Claude"` check -- Claude is the only
    # provider with dedicated context-file handling today (own static-header
    # builder, own settings.json init path in sync.py), but a future provider
    # can opt into the same treatment via config/ai-providers.yaml alone.
    has_dedicated = pc.get("has_dedicated_context_file", False)

    variables = variables.copy()
    if has_dedicated:
        variables["AGENT_HINTS_CLAUDE"] = build_agent_hints(local_config, agent_meta_root, include_table=False)
    else:
        variables["AGENT_HINTS"] = build_agent_hints(local_config, agent_meta_root, include_table=True)

    # Claude's CLAUDE.md static part is handled by sync_claude_md_static() in the
    # main sync loop; this strategy only refreshes the managed block for Claude.
    # For every other managed-block provider we also regenerate the static header
    # here (same hash-drift detection), when a static template is configured.
    if not has_dedicated:
        _ensure_context_file(
            project_root, agent_meta_root, target_path, template_path, variables, config,
            log, dry_run,
            fallback_agent_dir=pc.get("agents_dir", f".{provider.lower()}/agents"),
        )
        if target_path.exists():
            _regenerate_static_context(
                project_root, target_path, template_path, variables, log, dry_run,
                rel_label=context_file, source_label=template_name or context_file,
                rebuild_footer=True,
            )
    if target_path.exists():
        _update_managed_html_block(
            target_path, project_root, variables, log, dry_run, agent_meta_root,
            provider, pc, adapter_line=adapter_line,
        )

    # Claude settings files are initialized by the dedicated helpers in sync.py.
    if not has_dedicated:
        _init_provider_settings_json(project_root, pc, agent_meta_root, variables, log, dry_run)


def _sync_opencode_context(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
    target_name: str | None = None,
) -> None:
    """Strategy for Opencode: rules embedded into AGENTS.md managed block.

    ``target_name`` overrides the physical filename chosen by the
    ``per-provider`` dispatch (IC-09); it defaults to the provider's
    ``context_file``.
    """

    pc = provider_config[provider]
    context_file = target_name or pc["context_file"]  # AGENTS.md
    target_path = safe_path(project_root, context_file)
    template_name = pc.get("context_template")
    template_path = agent_meta_root / template_name if template_name else None

    if not target_path.exists():
        if template_path and template_path.exists():
            fallback_partials = template_path.parent.parent / "context" / "partials"
            builder = TemplateBuilder(template_path.parent, fallback_partials_dir=fallback_partials)
            ocontent = builder.build(template_path.stem, variables)
        else:
            project_name = config["project"]["name"]
            ocontent = (
                f"# {project_name}\n\n"
                "<!-- agent-meta:managed-begin -->\n"
                "<!-- agent-meta:managed-end -->\n"
            )
        log.action("INIT", context_file, template_name or "minimal fallback")
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(ocontent, encoding="utf-8")

    # Refresh the static header AND footer from the template on every sync so the
    # dynamic `## Agents` provider list never freezes at INIT (same header+footer
    # regeneration the managed-block providers get). The managed block and any
    # agent-injected trailing block are preserved verbatim.
    if target_path.exists():
        _regenerate_static_context(
            project_root, target_path, template_path, variables, log, dry_run,
            rel_label=context_file, source_label=template_name or context_file,
            rebuild_footer=True,
        )

    managed_pattern = re.compile(
        r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
        re.DOTALL,
    )
    if dry_run and not target_path.exists():
        log.action("UPDATE", context_file, "managed block (agent hints + rules)")
    else:
        existing = target_path.read_text(encoding="utf-8")
        new_managed = _build_managed_block(
            agent_meta_root, config, variables, log,
            provider=provider, provider_config=provider_config, project_root=project_root,
            target_name=target_name,
        )
        # The "agents-managed" template ends with a trailing newline after its
        # own closing marker, but managed_pattern's match never consumes any
        # whitespace after "-->" (only \s* before it) — so the old matched
        # span always ends exactly at "-->". Replacing that span with text
        # that ends in "-->\n" inserts one extra newline into the untouched
        # footer every single sync run, compounding forever (#434). Strip it
        # so match and replacement share the same boundary.
        new_managed = new_managed.rstrip("\n")
        if managed_pattern.search(existing):
            # Function replacement keeps the rendered block verbatim (#674).
            new_content = managed_pattern.sub(lambda _m: new_managed, existing, count=1)
            if new_content != existing:
                log.action("UPDATE", context_file, "managed block (agent hints + rules)")
                if not dry_run:
                    target_path.write_text(new_content, encoding="utf-8")
            else:
                log.skip(context_file, "managed block unchanged")
        elif not new_managed.strip():
            log.warning(
                f"{context_file}: exists but has no agent-meta marker, and the "
                "managed block could not be rendered — leaving the file untouched. "
                "Add the following block manually at the desired location:\n"
                "  <!-- agent-meta:managed-begin -->\n"
                "  <!-- agent-meta:managed-end -->"
            )
        else:
            # File already existed but was never initialized by agent-meta —
            # e.g. created by a third-party tool (Headroom/RTK and similar
            # wrapper proxies) without our marker. Insert the managed block
            # above the foreign content instead of leaving it uninitialized
            # forever or discarding what is already there.
            new_content = _insert_managed_block_above_foreign_content(existing, new_managed)
            log.action(
                "INIT", context_file,
                "managed block inserted — file existed without an agent-meta "
                "marker (foreign content preserved below)",
            )
            if not dry_run:
                target_path.write_text(new_content, encoding="utf-8")

    # Bootstrap block cleanup: remove Gemini bootstrap if Gemini is not active.
    _cleanup_bootstrap_block(target_path, config, provider_config, log, dry_run,
                              project_root=project_root)

    init_opencode_personal(agent_meta_root, project_root, log, dry_run)
    _init_provider_settings_json(project_root, pc, agent_meta_root, variables, log, dry_run)


def _cleanup_bootstrap_block(
    target_path: Path,
    config: dict,
    provider_config: dict,
    log: SyncLog,
    dry_run: bool,
    project_root: Path | None = None,
) -> None:
    """Remove the Gemini bootstrap block from AGENTS.md if Gemini is not active.

    The bootstrap block (<!-- agent-meta:bootstrap-begin --> ... <!-- agent-meta:bootstrap-end -->)
    is Gemini-specific. When Gemini is deactivated, it should not appear in AGENTS.md
    because 1) it lists agents that won't work without Gemini, and 2) it wastes context.
    """
    from .providers import resolve_providers
    active = set(resolve_providers(config, provider_config))
    gemini_active = "Gemini" in active

    if not target_path.exists():
        return

    content = target_path.read_text(encoding="utf-8")
    bootstrap_pattern = re.compile(
        r"<!--\s*agent-meta:bootstrap-begin\s*-->.*?<!--\s*agent-meta:bootstrap-end\s*-->",
        re.DOTALL,
    )
    has_bootstrap = bootstrap_pattern.search(content)

    if gemini_active or not has_bootstrap:
        return

    new_content = bootstrap_pattern.sub("", content)
    new_content = re.sub(r"\n{3,}", "\n\n", new_content)
    if new_content != content:
        rel_label = (str(target_path.relative_to(project_root))
                     if project_root else target_path.name)
        log.action("CLEANUP", rel_label,
                   "removed Gemini bootstrap block (Gemini deactivated)")
        if not dry_run:
            target_path.write_text(new_content, encoding="utf-8")


def _sync_continue_context(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
) -> None:
    """Strategy for Continue: project-context.md + config.yaml comment block."""
    from .extensions import render_managed_block, update_managed_block

    pc = provider_config[provider]
    context_file = pc.get("context_file")
    if context_file:
        ctx_path = project_root / context_file
        template_path = agent_meta_root / pc["context_template"]
        rel_ctx = str(ctx_path.relative_to(project_root))
        if is_absent_gitignored_target(ctx_path, dry_run):
            log.skip(rel_ctx, "absent (target root gitignored)")
        elif not ctx_path.exists():
            if template_path.exists():
                fallback_partials = template_path.parent.parent / "context" / "partials"
                builder = TemplateBuilder(template_path.parent, fallback_partials_dir=fallback_partials)
                ccontent = builder.build(template_path.stem, variables)
                source_label = pc["context_template"]
            else:
                ccontent = (
                    f"# {variables.get('PROJECT_NAME', 'Project Context')}\n\n"
                    f"{variables.get('PROJECT_CONTEXT', '')}\n\n"
                    "<!-- agent-meta:managed-begin -->\n"
                    "<!-- agent-meta:managed-end -->\n\n"
                    "## Agent Rules\n\n"
                    "Agent context files are in `.continue/rules/`.\n"
                    "Continue loads all Markdown files in this directory automatically as context.\n"
                )
                source_label = "minimal fallback (CONTINUE.project-template.md not found)"
            log.action("INIT", rel_ctx, source_label)
            if not dry_run:
                ctx_path.parent.mkdir(parents=True, exist_ok=True)
                ctx_path.write_text(ccontent, encoding="utf-8")
        else:
            existing = ctx_path.read_text(encoding="utf-8")
            new_managed = render_managed_block(variables, context_file, log, agent_meta_root)
            updated = update_managed_block(existing, new_managed)
            if updated != existing:
                log.action("UPDATE", str(ctx_path.relative_to(project_root)),
                           "managed block refreshed")
                if not dry_run:
                    ctx_path.write_text(updated, encoding="utf-8")
            else:
                log.skip(str(ctx_path.relative_to(project_root)), "managed block unchanged")

    settings_file = pc.get("settings_file")
    if settings_file:
        settings_path = project_root / settings_file
        if settings_path.exists():
            _update_continue_config_managed_block(
                settings_path, variables, log, dry_run, project_root
            )
        else:
            rel_settings = str(settings_path.relative_to(project_root))
            if is_absent_gitignored_target(settings_path, dry_run):
                log.skip(rel_settings, "absent (target root gitignored)")
            else:
                settings_template_rel = pc.get("settings_template")
                settings_template_path = (
                    agent_meta_root / settings_template_rel if settings_template_rel else None
                )
                if settings_template_path and settings_template_path.exists():
                    yaml_content = settings_template_path.read_text(encoding="utf-8")
                    source_label = settings_template_rel
                else:
                    yaml_content = (
                        "# Continue configuration\n"
                        "# See https://docs.continue.dev for full documentation\n"
                        "\n"
                        "# Agents are in .continue/agents/ - managed by agent-meta\n"
                        "# Project rules are in .continue/rules/ - managed by agent-meta\n"
                    )
                    source_label = "minimal fallback"
                    if settings_template_rel:
                        log.warning(f"{settings_template_rel} not found — using minimal fallback for {settings_file}")
                log.action("INIT", rel_settings, source_label)
                if not dry_run:
                    settings_path.parent.mkdir(parents=True, exist_ok=True)
                    settings_path.write_text(yaml_content, encoding="utf-8")


def _shares_context_with_embedded_rules(
    provider: str, pc: dict, provider_config: dict
) -> bool:
    """True if this provider's context_file is also rendered by an embedded-rules provider.

    Multiple providers can point `context_file` at the same physical file (e.g.
    Opencode/Gemini/Codex/ZCode/KimiCode all share AGENTS.md). That file can hold
    only ONE managed block, so every sharer must render byte-identical content —
    otherwise a lone `--check` reports a permanent, unfixable false "out of sync"
    (issue #638). The embedded-rules strategy is a strict superset of the plain
    managed-block strategy (it additionally inlines the rule bodies), so when any
    sharer uses `context-embedded-rules`, ALL sharers must use it too. This keeps
    the choice generic: it depends on the shared-file capability set, not on any
    hardcoded provider name, so a future provider that joins the shared file
    converges automatically.
    """
    context_file = pc.get("context_file")
    if not context_file:
        return False
    return any(
        p != provider
        and cfg.get("context_file") == context_file
        and "context-embedded-rules" in cfg.get("capabilities", [])
        for p, cfg in provider_config.items()
    )


_ADAPTER_MANAGED_INDEX = ".agent-meta-context-adapters-managed"


def _adapter_index_path(project_root: Path) -> Path:
    """Path of the managed index that authorizes generated adapter files."""
    return project_root / _ADAPTER_MANAGED_INDEX


def _record_adapter_managed(
    project_root: Path, adapter_file: str, log: SyncLog, dry_run: bool
) -> None:
    """Register a generated adapter file in the adapter managed index.

    The index is the rollback authorization (Task 6): only files listed here
    may be removed when the topology switches back to ``unified``. Existing
    entries are preserved so a multi-adapter catalog does not lose siblings
    across the per-provider calls of one sync run.
    """
    index_path = _adapter_index_path(project_root)
    previously_managed = bootstrap_previously_managed(
        project_root, index_path, glob_pattern="*",
    )
    write_managed_index(index_path, previously_managed | {adapter_file}, dry_run)


def _record_adapter_hash(project_root: Path, adapter_file: str, dry_run: bool) -> None:
    """Record the adapter's static-part hash for static-drift detection.

    Mirrors ``sync_claude_md_static``'s hash key/signature so a manual edit to
    the adapter's static header is detected the same way as the core context
    file. A missing/unreadable adapter is a silent no-op (nothing to hash).
    """
    target_path = safe_path(project_root, adapter_file)
    if not target_path.exists():
        return
    header, _managed, _footer = _split_context_file(
        target_path.read_text(encoding="utf-8")
    )
    _record_static_hash(
        project_root, adapter_file,
        _normalize_static_sig(_strip_user_notes(header)), dry_run,
    )


def _expected_adapter_files(
    config: dict, provider_config: dict, active_providers: list
) -> set[str]:
    """Adapter files still expected because ``per-provider`` is active.

    Empty in ``unified`` mode (the rollback case). Only providers opting in
    via ``context_adapter: true`` whose resolved topology is ``per-provider``
    contribute; every lookup is key-driven and fail-safe.
    """
    from .providers import context_topology

    expected: set[str] = set()
    if not isinstance(provider_config, dict):
        return expected
    for provider in active_providers:
        pc = provider_config.get(provider)
        if not isinstance(pc, dict) or pc.get("context_adapter") is not True:
            continue
        if context_topology(config, provider) != "per-provider":
            continue
        adapter_file = pc.get("context_adapter_file")
        if isinstance(adapter_file, str) and adapter_file.strip():
            expected.add(adapter_file)
    return expected


def rollback_context_adapters(
    project_root: Path,
    config: dict,
    provider_config: dict,
    active_providers: list,
    log: SyncLog,
    dry_run: bool,
) -> list[str]:
    """Tear down adapter artifacts that are no longer expected.

    The adapter managed index (``.agent-meta-context-adapters-managed``) is the
    sole authorization: only project-relative paths listed in it are ever
    deleted — a foreign/user file without an index entry is never touched. The
    switch ``per-provider`` -> ``unified`` therefore converges idempotently:
    every indexed adapter is removed backup-first via
    ``cleanup_stale_managed_files`` (its file content is preserved in a
    ``.sync-backup-<ts>`` sibling), and the index is dropped once no adapter
    remains managed. Each adapter file is re-created by the unified render if
    the provider still owns it. Returns the written backup paths.
    """
    index_path = _adapter_index_path(project_root)
    expected = _expected_adapter_files(config, provider_config, active_providers)
    tracked = bootstrap_previously_managed(project_root, index_path, glob_pattern="*")

    backups: list[str] = []
    if tracked:
        backups = cleanup_stale_managed_files(
            project_root, project_root, tracked, expected, log, dry_run,
            reason="context adapter no longer expected (topology rollback)",
            backup=True,
        )

    if expected:
        if tracked != expected:
            write_managed_index(index_path, expected, dry_run)
    elif not dry_run and index_path.exists():
        # No adapter remains: drop the now-empty index entirely so `unified`
        # stays byte-identical to a project that never opted in.
        try:
            index_path.unlink()
        except OSError as exc:
            log.warning(
                f"context adapter index '{index_path.name}': could not remove: "
                f"{type(exc).__name__}: {exc} — file left in place"
            )
    return backups


def _dispatch_context_strategy(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
    target_name: str | None = None,
    adapter_line: str | None = None,
) -> None:
    """Capability-driven render dispatch shared by both topology modes."""
    pc = provider_config.get(provider, {})
    if _has_capability(pc, "context-embedded-rules") or _shares_context_with_embedded_rules(
        provider, pc, provider_config
    ):
        _sync_opencode_context(
            agent_meta_root, project_root, config, variables, log, dry_run,
            provider, provider_config, target_name=target_name,
        )
    elif _has_capability(pc, "context-config-comment"):
        _sync_continue_context(
            agent_meta_root, project_root, config, variables, log, dry_run,
            provider, provider_config,
        )
    elif _has_capability(pc, "context-managed-block"):
        _sync_managed_block_context(
            agent_meta_root, project_root, config, variables, log, dry_run,
            provider, provider_config, target_name=target_name,
            adapter_line=adapter_line,
        )


def _adapter_settings_activation(pc: dict) -> dict | None:
    """Resolve the provider-native settings activation for an adapter file.

    Capability/``settings_file``-gated (AC-26, F-10):

    * ``context_adapter_settings`` absent/``False`` (the default) → ``None``: no
      settings write; the adapter file is the provider's default context file.
    * ``context_adapter_settings: true`` additionally requires a native
      ``settings_file`` and the provider-native key name in
      ``context_adapter_settings_key`` (worked example: ``context.fileName`` in
      ``.gemini/settings.json``); a missing piece degrades to ``None`` instead of
      guessing (never writes an unspecified key).

    Purely key-driven — no provider-name literal in any branch.
    """
    if pc.get("context_adapter_settings") is not True:
        return None
    settings_file = pc.get("settings_file")
    settings_key = pc.get("context_adapter_settings_key")
    adapter_file = pc.get("context_adapter_file")
    if not (isinstance(settings_file, str) and settings_file.strip()):
        return None
    if not (isinstance(settings_key, str) and settings_key.strip()):
        return None
    if not (isinstance(adapter_file, str) and adapter_file.strip()):
        return None
    return {
        "settings_file": settings_file,
        "settings_key": settings_key.strip(),
        "adapter_file": adapter_file,
    }


def _write_adapter_settings_activation(
    project_root: Path, activation: dict, log: SyncLog, dry_run: bool
) -> None:
    """Merge the provider-native settings key that activates an adapter file.

    Only reached through ``_adapter_settings_activation`` (an explicit provider
    opt-in). The dotted native key is set on the existing settings document,
    preserving sibling keys. A missing or non-mapping settings file is a
    ``log.warning`` — never a silent no-op and never a create-and-guess.
    """
    settings_file = activation["settings_file"]
    settings_key = activation["settings_key"]
    adapter_file = activation["adapter_file"]
    settings_path = safe_path(project_root, settings_file)
    if not settings_path.exists():
        log.warning(
            f"context_adapter_settings for '{adapter_file}' requires '{settings_file}' "
            "— settings file missing, activation skipped"
        )
        return
    document = load_json_file(settings_path, on_error="warn", default=None, log=log)
    if not isinstance(document, dict):
        log.warning(f"{settings_file}: not a JSON object — adapter activation skipped")
        return
    cursor = document
    parts = [part for part in settings_key.split(".") if part]
    if not parts:
        log.warning(f"{settings_file}: invalid settings key '{settings_key}' — activation skipped")
        return
    for part in parts[:-1]:
        branch = cursor.get(part)
        if not isinstance(branch, dict):
            branch = {}
            cursor[part] = branch
        cursor = branch
    cursor[parts[-1]] = adapter_file
    if not dry_run:
        save_json_document(settings_path, document)
    log.action(
        "UPDATE", settings_file,
        f"context adapter activation: {settings_key}={adapter_file}",
    )


def sync_context_adapters_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
) -> None:
    """Write the adapter file of an adapter-capable provider (``per-provider``).

    The physical filename is selected here (IC-09, the render switch): an
    adapter-capable provider renders its ``context_adapter_file`` with the
    provider-native core reference line; a provider without the capability is
    never routed here. ``resolve_context_filename`` (IC-08) is not consulted —
    it feeds legacy cleanup only. A missing/blank adapter file is a
    ``log.warning`` + return (never silent); ``dry_run`` never writes.
    """
    pc = provider_config.get(provider, {})
    if pc.get("context_adapter") is not True:
        return
    adapter_file = pc.get("context_adapter_file")
    if not (isinstance(adapter_file, str) and adapter_file.strip()):
        log.warning(
            f"context_adapter enabled for provider '{provider}' but "
            "context_adapter_file is missing/empty — adapter render skipped"
        )
        return
    _dispatch_context_strategy(
        agent_meta_root, project_root, config, variables, log, dry_run,
        provider, provider_config,
        target_name=adapter_file,
        adapter_line=_adapter_reference_line(config, pc),
    )
    if safe_path(project_root, adapter_file).exists():
        _record_adapter_managed(project_root, adapter_file, log, dry_run)
        _record_adapter_hash(project_root, adapter_file, dry_run)
        activation = _adapter_settings_activation(pc)
        if activation is not None:
            _write_adapter_settings_activation(project_root, activation, log, dry_run)


def sync_context_for_provider(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider: str,
    provider_config: dict,
):
    """Create or update the context file for a given provider.

    Dispatch is capability-driven:
      - context-embedded-rules → Opencode strategy
      - shares a context_file with an embedded-rules provider → Opencode strategy
        (the shared physical file must converge to one managed block, #638)
      - context-config-comment → Continue strategy (managed block + config.yaml comment)
      - context-managed-block  → generic HTML managed-block strategy

    In ``context_file.topology: per-provider`` the render target is selected
    per provider (IC-09): adapter-capable providers render their
    ``context_adapter_file`` via ``sync_context_adapters_for_provider``, every
    other provider renders the canonical core (``context_file.core_file``).
    The default ``unified`` topology keeps the exact legacy path.
    """
    pc = provider_config.get(provider)
    if not pc:
        return

    from .providers import context_topology

    if context_topology(config, provider) == "per-provider":
        if pc.get("context_adapter") is True:
            sync_context_adapters_for_provider(
                agent_meta_root, project_root, config, variables, log, dry_run,
                provider, provider_config,
            )
        else:
            _dispatch_context_strategy(
                agent_meta_root, project_root, config, variables, log, dry_run,
                provider, provider_config,
                target_name=_core_context_filename(config),
            )
        return

    _dispatch_context_strategy(
        agent_meta_root, project_root, config, variables, log, dry_run,
        provider, provider_config,
    )


def _init_provider_settings_json(
    project_root: Path,
    pc: dict,
    agent_meta_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
) -> None:
    """Create provider settings skeleton once if it does not exist yet."""

    settings_file = pc.get("settings_file")
    if not settings_file:
        return
    settings_path = safe_path(project_root, settings_file)
    if settings_path.exists():
        log.skip(str(settings_path.relative_to(project_root)),
                 "already exists — not overwritten")
        return
    if is_absent_gitignored_target(settings_path, dry_run):
        log.skip(str(settings_path.relative_to(project_root)),
                 "absent (target root gitignored)")
        return

    settings_template_rel = pc.get("settings_template")
    settings_template_path = (
        agent_meta_root / settings_template_rel if settings_template_rel else None
    )
    if settings_template_path and settings_template_path.exists():
        content = substitute(
            settings_template_path.read_text(encoding="utf-8"),
            variables, settings_template_rel, log,
        )
        source_label = settings_template_rel
    else:
        # Minimal provider-agnostic JSON skeleton
        content = '{\n}\n'
        source_label = "minimal fallback"
        if settings_template_rel:
            log.warning(f"{settings_template_rel} not found — using minimal fallback for {settings_file}")
    log.action("INIT", str(settings_path.relative_to(project_root)), source_label)
    if not dry_run:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        settings_path.write_text(content, encoding="utf-8")


_CONTINUE_MANAGED_BEGIN = "# agent-meta:managed-begin"
_CONTINUE_MANAGED_END   = "# agent-meta:managed-end"


def _update_continue_config_managed_block(
    settings_path: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    project_root: Path,
) -> None:
    """Insert or update the agent-meta metadata comment block in config.yaml.

    The block is YAML comments so it never affects parsing. User model config
    and any other customisations are left completely untouched.
    """
    from datetime import date
    version = variables.get("AGENT_META_VERSION", "?")
    # Same reproducible source as the managed blocks (#752) — a raw date.today()
    # would make the committed managed comment block drift daily.
    today = variables.get("AGENT_META_DATE") or date.today().isoformat()  # noqa: DTZ011
    new_block = (
        f"{_CONTINUE_MANAGED_BEGIN}\n"
        f"# Managed by agent-meta v{version} — {today}\n"
        f"# Agents : .continue/agents/  (auto-discovered by Continue)\n"
        f"# Rules  : .continue/rules/   (auto-discovered by Continue)\n"
        f"{_CONTINUE_MANAGED_END}"
    )

    existing = settings_path.read_text(encoding="utf-8")
    rel = str(settings_path.relative_to(project_root))

    managed_re = re.compile(
        rf"^{re.escape(_CONTINUE_MANAGED_BEGIN)}.*?^{re.escape(_CONTINUE_MANAGED_END)}",
        re.MULTILINE | re.DOTALL,
    )
    if managed_re.search(existing):
        # Function replacement keeps the generated metadata block verbatim (#674).
        updated = managed_re.sub(lambda _m: new_block, existing, count=1)
        if updated != existing:
            log.action("UPDATE", rel, "managed comment block")
            if not dry_run:
                settings_path.write_text(updated, encoding="utf-8")
        else:
            log.skip(rel, "managed comment block unchanged")
    else:
        # Prepend block before first non-comment line
        updated = new_block + "\n" + existing
        log.action("UPDATE", rel, "inject managed comment block")
        if not dry_run:
            settings_path.write_text(updated, encoding="utf-8")


def _extract_rule_compact_from_content(content: str, output_name: str, rel_source: str,
                                        provider: str = "Claude", has_native_rules: bool = True) -> str:
    """Extract title + 1-sentence summary from already-substituted rule content.

    Reduces a 50-100 line rule to a single 3-line block:
      - Title
      - First non-empty paragraph (≤200 chars)
      - Pointer to full rule (provider-aware)
    """
    body = _strip_frontmatter(content).strip()
    if not body:
        return f"- **{output_name}** — siehe `{rel_source}`"

    lines = body.splitlines()
    title = output_name.replace('-', ' ').replace('.md', '').title()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('# '):
            title = stripped[2:].strip()
            break

    summary = ""
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith(('#', '```')):
            continue
        summary = stripped
        if len(summary) > 200:
            summary = summary[:197] + "..."
        break

    rule_stem = Path(output_name).stem
    if has_native_rules:
        details = f"Details: `rules/.../{rule_stem}.md`"
    else:
        details = f"Details: embedded in `{provider}` context (Regeln-Abschnitt)"
    return f"### {title}\n{summary}\n{details}"


# Compact-mode section filter for the three agent-meta platform rules whose
# OVERVIEW-classified sections (layer model, composition syntax, changelog-style
# feature docs, reference checklists) are discoverable elsewhere. This pulls the
# #192-Phase-2 territory into #540's density work on an explicit user decision:
# only OVERVIEW density is reduced, INSTRUCTION sections stay embedded verbatim
# in BOTH modes (#540 non-goal: density only, no semantic change). Keyed by the
# *output* stem (2-platform prefix stripped by collect_rule_sources), because the
# embedded loop reads the raw source file (agent-meta-<name>.md) but preset/keep
# logic is expressed against the output name (<name>.md).
_COMPACT_PLATFORM_RULES = {
    "sync-interface": {
        "keep": ("## Branch-Guard-Erweiterung für agent-meta", "## Warum"),
        "pointer": (
            "Details (Smart Context Regeneration, `--check`, `context-hashes.json`, "
            "Provider-Context-Lifecycle): `.claude/skills/sync-interface/SKILL.md`."
        ),
    },
    "architecture": {
        "keep": ("## Abhängigkeitsprinzip",),
        "pointer": (
            "Details (Schichten-Modell, Composition-Syntax, Platzhalter-Escape): "
            "`docs/architecture/01-layer-model.md`."
        ),
    },
    "conventions": {
        "keep": ("## Hard Invariants",),
        "pointer": (
            "Details (Naming-Konvention, Instruction-Bleed-Checkliste, "
            "Adding-New-Role/Placeholder, Change-Checklist): "
            "`.claude/skills/conventions/SKILL.md`."
        ),
    },
    "admin-ui": {
        "keep": ("## Host-Bindung + Token-Regeln", "## Token-Distribution"),
        "pointer": (
            "Details (Zwei Modi, Server-Lifecycle, Flags, Port-Matrix, "
            "Token-Persistenz, Diagnose-Folge, Known Issues, Troubleshooting): "
            "`.claude/skills/admin-ui/SKILL.md`."
        ),
    },
}


def compact_embedded_rule(output_stem: str, content: str) -> str:
    """Collapse OVERVIEW sections of a known platform rule to a pointer (compact mode).

    The preamble (content before the first ``## `` heading, including the rule's
    ``# `` title) and every H2 section named in the rule's ``keep`` list survive
    verbatim — these are the INSTRUCTION parts that must stay identical in both
    modes (issue #540 non-goal: density only, no semantic change). All other H2
    sections are dropped and replaced by a single pointer line to the full
    reference. Rules not in the table pass through unchanged, so full mode (which
    never calls this) and every other embedded rule are unaffected.
    """
    spec = _COMPACT_PLATFORM_RULES.get(output_stem)
    if not spec:
        return content
    keep_set = set(spec["keep"])
    kept: list[str] = []
    keep_current = True  # preamble before the first H2 is always instruction/title
    for line in content.splitlines():
        if line.startswith("## "):
            keep_current = line.strip() in keep_set
        if keep_current:
            kept.append(line)
    body = "\n".join(kept).rstrip()
    return f"{body}\n\n{spec['pointer']}"


def _build_managed_block(
    agent_meta_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    provider: str,
    provider_config: dict | None = None,
    project_root: Path | None = None,
    target_name: str | None = None,
) -> str:
    from .delegation_table import get_active_agents_data
    from .rules import collect_rule_sources, resolve_rules, rule_opts_lazy_channel

    # build_knowledge_engine_hints is imported at module top level — the
    # lazy import was vestigial (agents does not import context; Issue #478
    # cleanup, guarded by tests/test_import_acyclicity.py).
    pc = (provider_config or {}).get(provider, {})
    has_native_rules = pc.get("has_rules", False)

    # Providers that render into the *same physical* context_file (currently
    # only Opencode + Gemini, both sharing AGENTS.md). Every value below that
    # is derived from a single provider's config (pc) must instead be derived
    # from the union of shared_users -- otherwise the rendered managed block
    # differs depending on which shared provider happens to sync last, and
    # each sync overwrites the other's version forever (issue #638: infinite
    # oscillation, permanent false "out of sync" on --check).
    shared_users = [provider]
    shared_name = target_name or pc.get("context_file")
    if provider_config and shared_name:
        shared_users = [
            p for p, cfg in provider_config.items()
            if cfg.get("context_file") == shared_name
        ]
        if not all(provider_config[p].get("has_rules", False) for p in shared_users):
            has_native_rules = False

    def _shared(dir_key: str, default_fmt: str) -> str:
        """Join a per-provider path field across all shared_users, deduped.

        Falls back to the single current-provider value when the context file
        is not shared (shared_users == [provider]) -- identical to the old
        per-provider-only behaviour in that case.
        """
        values = [
            # Null-valued keys (skills_dir: null in ai-providers.yaml) fall
            # back to the same default an absent key gets — a None would
            # crash the join below (found via the #192 weak-sharer test).
            provider_config[p].get(dir_key) or default_fmt.format(p.lower())
            for p in shared_users
        ] if provider_config else [
            pc.get(dir_key) or default_fmt.format(provider.lower())
        ]
        return " bzw. ".join(dict.fromkeys(values))

    local_vars = dict(variables)
    local_vars["AGENTS_DIR"] = _shared("agents_dir", ".{}/agents")

    # Shared-file gate tier (SPEC-CONTEXT-FILE-MODES-2026-09-13, IC-03): a
    # physical context_file shared by more than one ACTIVE provider must render
    # exactly one deterministic GATE_* bundle. Otherwise each active sharer
    # overwrites the other's managed block forever and --check never converges
    # (issue #794). Resolve the tier from the weakest active sharer once, so the
    # first write lands and every later sharer is a byte-identical no-op skip.
    # A single active sharer keeps the per-provider runtime_gate_vars injected
    # by sync_pipeline (IC-04). Only the GATE_* family is neutralised -- the
    # remaining rendered provider-scoped inputs (ORCH_MODE_*, REPO_CONTAINMENT_*)
    # stay per-provider by design (determinism scope AC-25 / R7).
    if provider_config:
        from .providers import (
            load_provider_capabilities,
            resolve_providers,
            shared_runtime_gate_vars,
        )

        active = set(resolve_providers(config, provider_config))
        active_shared_users = [p for p in shared_users if p in active]
        if len(active_shared_users) > 1:
            local_vars.update(
                shared_runtime_gate_vars(
                    active_shared_users,
                    provider_config,
                    load_provider_capabilities(agent_meta_root),
                    config,
                )
            )

    if len(shared_users) > 1:
        for p in shared_users:
            local_vars[f"PLATFORM_{p.upper()}"] = True

    from .providers import context_topology

    # ``per-provider``: the canonical core is read by several providers, so it
    # must not carry a provider-specific runtime promise. Render the neutral
    # ``GATE_NEUTRAL`` state instead — each provider states its own tier in its
    # dedicated channel (adapter file / native rules file, AC-23). ``unified``
    # keeps the shared weakest-tier bundle set above, byte-identical to the
    # legacy render. Keyed on the topology + the physical core target only,
    # never on a provider name.
    if (
        context_topology(config, provider) == "per-provider"
        and target_name == _core_context_filename(config)
    ):
        local_vars.update({
            "GATE_NEUTRAL": "true",
            "GATE_ENFORCED": "false",
            "GATE_PARTIAL": "false",
            "GATE_ADVISORY": "false",
        })

    local_vars["HAS_NATIVE_RULES"] = has_native_rules
    local_vars[f"PLATFORM_{provider.upper()}"] = True
    local_vars["PENDING_TASKS_FILE"] = _shared("pending_tasks_file", ".{}/pending-tasks.md")
    local_vars["EXTENSION_DIR"] = _shared("extension_dir", ".{}/3-project")
    local_vars["SNIPPETS_DIR"] = _shared("snippets_dir", ".{}/snippets")
    local_vars["SKILLS_DIR"] = _shared("skills_dir", ".{}/skills")
    local_vars["ORCHESTRATOR_INVOCATION_HINT"] = pc.get("orchestrator_hint", "")
    
    orch_config = config.get("orchestrator", {})
    provider_override = orch_config.get("provider-overrides", {}).get(provider, {})
    _orch_mode = _resolve_orch_mode(orch_config, provider_override)
    local_vars.update(_orch_mode_flags(_orch_mode))

    # Repo-containment ("prison mode") flags for THIS provider — same
    # provider-scoped wiring as the ORCH_MODE_* flags above (provider-override
    # > project > framework default, spec §2.3/§4.5).
    local_vars.update(repo_containment_variables(config, provider))

    local_vars["active_agents"] = get_active_agents_data(agent_meta_root, config, local_vars)
    
    embedded_rules: list[dict] = []
    # Non-embedded (lazy) rule counter — only populated in the embedded-rules
    # branch below (has_rules providers never embed, so there is nothing to
    # count); initialized here so the flag assignment after the branch is
    # always well-defined.
    lazy_rule_count = 0

    if not has_native_rules:
        rule_options = resolve_rules(config, agent_meta_root)
        platforms = config.get("platforms", [])
        rule_sources = collect_rule_sources(agent_meta_root, platforms, config=config)

        # Compact mode (issue #540): embedded MCP/external-tool sections and
        # knowledge hints render in the compressed, pointer-based variant.
        # Native rule artifacts (.claude/rules/*, skills) stay full — they are
        # lazy-loaded and not part of the always-on context footprint.
        _global_compact = local_vars.get("COMPACT_MODE") == "true"
        # shared_users is catalog-wide (every provider that declares this
        # context_file anywhere in config/ai-providers.yaml, active or not --
        # see _shares_context_with_embedded_rules), so it always contains
        # ZCode/KimiCode for an AGENTS.md-based provider even when this
        # project never activates them. Only a provider actually selected in
        # this project's config can ever render (and thus lose content into)
        # this physical file, so the lazy-channel check is scoped to the
        # subset of shared_users this project actually activates.
        if provider_config:
            from .providers import resolve_providers
            _active_providers = set(resolve_providers(config, provider_config))
            _compact_pcs = [
                provider_config[p] for p in shared_users if p in _active_providers
            ] or [pc]
        else:
            _compact_pcs = [pc]
        _compact = resolve_plugin_compact(_global_compact, _compact_pcs)

        # Loaded before the plain-rules loop (not with the per-server embedding
        # below) so MCP_GUARDRAILS_LIST is available for mcp-guardrails.md's
        # {{MCP_GUARDRAILS_LIST}} placeholder — mirrors sync_rules()'s
        # provider_vars wiring for providers with a native rules_dir.
        from .mcp import build_mcp_guardrails_list, load_mcp_registry, resolve_active_mcp_servers
        mcp_registry = load_mcp_registry(agent_meta_root, config, project_root)
        mcp_active = resolve_active_mcp_servers(config, agent_meta_root, project_root, registry=mcp_registry)
        local_vars["MCP_GUARDRAILS_LIST"] = build_mcp_guardrails_list(mcp_registry, mcp_active)

        def _opts_skip(opts: dict, p: str) -> bool:
            prov_opt = opts.get(p.lower())
            return prov_opt == "skip" or prov_opt is False

        # Issue #192 Phase 2 (selective rule embedding): a rule flagged
        # `embed: false` (or routed to `channel: skill`) leaves the managed
        # block when the whole shared-file group can load rules from separate
        # files (every sharer has a skills_dir — see
        # _shared_rules_file_channel). The block then renders a pointer to
        # <SKILLS_DIR>/<rule-stem>/SKILL.md instead of the rule body;
        # sync_rules()/sync_embedded_rule_files() write those files. Without
        # the file channel the rule EMBEDS (never drops): a preset opt-out
        # must not delete content for a provider with no way to load it.
        rules_file_channel = _shared_rules_file_channel(pc, provider_config, shared_users)

        for src_path, output_name in rule_sources:
            # Key options by the OUTPUT stem ("admin-ui"), not the raw source
            # stem ("agent-meta-admin-ui"): rules-presets.yaml keys are output
            # names (2-platform prefix stripped by collect_rule_sources), and
            # sync_rules()/compact_embedded_rule() already resolve against the
            # output stem. The embed loop previously used src_path.stem, which
            # silently dropped every preset option (channel: skill, embed,
            # per-provider skip) for 2-platform rules (#192 Phase 2 fix).
            rule_stem = Path(output_name).stem
            opts = rule_options.get(rule_stem, {})
            # For a shared context_file, a rule is dropped only when EVERY
            # shared user opts out -- one provider's per-provider "skip" must
            # not remove content another shared provider still needs from the
            # same physical file (issue #638: union, not current-provider-only).
            if all(_opts_skip(opts, p) for p in shared_users):
                continue
            if rules_file_channel and rule_opts_lazy_channel(opts):
                # Progressive disclosure (issues #192 Phase 2 + #540 Fix 1):
                # the rule lives as a separate file; the block gets a pointer
                # via the rules-lazy partial (HAS_LAZY_RULES below).
                lazy_rule_count += 1
                continue
            # No file channel for the group (or an always-embed rule): fall
            # through to the embed path — a preset opt-out must NEVER delete
            # content for a provider with no way to load it (issue #192 risk
            # note: weak providers keep embedding; the former behaviour of
            # dropping embed:false rules here was silent content loss).

            layer = src_path.parts[-2]
            rel_source = f"rules/{layer}/{src_path.name}"
            rule_content = src_path.read_text(encoding="utf-8")
            rule_content = substitute(rule_content, local_vars, rel_source, log)
            rule_content = strip_inactive_conditional_blocks(rule_content, local_vars)
            if _global_compact:
                # Density-only compaction of the agent-meta platform rules whose
                # OVERVIEW sections are discoverable elsewhere (#540 + #192 P2).
                # Deliberately on the global flag, not the provider-aware
                # `_compact` below -- this is agent-meta's own always-on rule
                # density, not the plugin lazy-channel-loss bug (#638-adjacent).
                rule_content = compact_embedded_rule(Path(output_name).stem, rule_content)
            embedded_rules.append({"content": rule_content})
        
        try:
            from .mcp import MCP_RULE_PREFIX, _generate_rule_content
            if mcp_registry:
                for server_name in mcp_active:
                    server_def = mcp_registry.get(server_name)
                    if not server_def:
                        continue
                    # Same selective-embedding contract as the rules loop
                    # above (issue #192 Phase 2 + #540 Fix 1): when the whole
                    # shared-file group can load rules from separate files,
                    # per-server MCP sections flagged channel: skill /
                    # embed: false (rules-presets.yaml) leave the block; the
                    # embedded mcp-guardrails rule keeps the hard-prohibition
                    # one-liners always-on. generate_mcp_artifacts() writes
                    # the full section as <skills_dir>/mcp-<server>/SKILL.md.
                    mcp_opts = rule_options.get(f"{MCP_RULE_PREFIX}{server_name}", {})
                    if all(_opts_skip(mcp_opts, p) for p in shared_users):
                        continue
                    if rules_file_channel and rule_opts_lazy_channel(mcp_opts):
                        lazy_rule_count += 1
                        continue
                    mcp_content = _generate_rule_content(
                        server_name, server_def, compact=_compact
                    )
                    embedded_rules.append({"content": mcp_content})
        except ImportError:
            pass

        try:
            from .external_tools import (
                TOOL_RULE_PREFIX,
                _generate_tool_rule_content,
                load_external_tools_registry,
                resolve_active_external_tools,
            )
            tool_registry = load_external_tools_registry(agent_meta_root, config, project_root)
            if tool_registry:
                active_tools = resolve_active_external_tools(
                    config, agent_meta_root, project_root, registry=tool_registry,
                )
                shared_pcs = (
                    [provider_config[p] for p in shared_users]
                    if provider_config and len(shared_users) > 1 else None
                )
                for tool_name in active_tools:
                    tool_def = tool_registry.get(tool_name)
                    skip_list = tool_def.get("provider-skip", []) if tool_def else []
                    # Same union rule as above: only drop the tool for a shared
                    # context_file when every shared user opts out of it.
                    if not (tool_def and not all(p in skip_list for p in shared_users)):
                        continue
                    # Selective embedding (issue #192 Phase 2): the tool
                    # section leaves the block on the file channel, exactly
                    # like MCP sections and rules sources; the file is
                    # written by generate_external_tool_artifacts().
                    tool_opts = rule_options.get(f"{TOOL_RULE_PREFIX}{tool_name}", {})
                    if rules_file_channel and rule_opts_lazy_channel(tool_opts):
                        lazy_rule_count += 1
                        continue
                    embedded_rules.append(
                        {"content": _generate_tool_rule_content(
                            tool_name, tool_def, pc, project_root, compact=_compact,
                            shared_pcs=shared_pcs,
                        )}
                    )
        except ImportError:
            pass

    local_vars["embedded_rules"] = embedded_rules
    # Composition flags for agents-managed.md: embedded core rules render via
    # the rules-embedded partial, non-embedded (lazy) rules via the one-line
    # rules-lazy pointer. Both flags are plain Python bools — truthiness is
    # resolved by TemplateBuilder.resolve_conditionals().
    local_vars["HAS_EMBEDDED_RULES"] = bool(embedded_rules)
    local_vars["HAS_LAZY_RULES"] = bool(lazy_rule_count)

    local_vars["KNOWLEDGE_ENGINE_HINTS"] = build_knowledge_engine_hints(
        config, compact=local_vars.get("COMPACT_MODE") == "true"
    )

    builder = TemplateBuilder(agent_meta_root / "templates" / "context")
    return builder.build("agents-managed", local_vars)

def init_claude_personal(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
):
    """Copy CLAUDE.personal-template.md to CLAUDE.personal.md if not present yet."""
    template_path = agent_meta_root / "templates" / "configs" / "CLAUDE.personal-template.md"
    target_path = project_root / "CLAUDE.personal.md"

    if target_path.exists():
        log.skip("CLAUDE.personal.md", "already exists")
        return
    if is_absent_gitignored_target(target_path, dry_run):
        log.skip("CLAUDE.personal.md", "absent (target root gitignored)")
        return

    if not template_path.exists():
        log.warning("CLAUDE.personal-template.md not found — skipping CLAUDE.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "CLAUDE.personal.md", "templates/configs/CLAUDE.personal-template.md")
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
    template_path = agent_meta_root / "templates" / "configs" / "AGENTS.personal-template.md"
    target_path = project_root / "AGENTS.personal.md"

    if target_path.exists():
        log.skip("AGENTS.personal.md", "already exists")
        return
    if is_absent_gitignored_target(target_path, dry_run):
        log.skip("AGENTS.personal.md", "absent (target root gitignored)")
        return

    if not template_path.exists():
        log.warning("AGENTS.personal-template.md not found — skipping AGENTS.personal.md creation")
        return

    content = template_path.read_text(encoding="utf-8")
    log.action("INIT", "AGENTS.personal.md", "templates/configs/AGENTS.personal-template.md")
    if not dry_run:
        target_path.write_text(content, encoding="utf-8")


def init_settings_json(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    providers: list[str] | None = None,
    provider_config: dict | None = None,
    variables: dict | None = None,
):
    """Create provider settings files if they do not exist yet.

    Iterates over all active providers (or every configured provider if no
    explicit list is given) and initializes the committed settings file once.
    The hooks section for Claude is managed separately by sync_hooks().
    """
    pc = provider_config or {}
    active = providers if providers is not None else list(pc.keys())
    for provider in active:
        _init_provider_settings_json(
            project_root,
            pc[provider],
            agent_meta_root,
            variables or {},
            log,
            dry_run,
        )


def init_settings_local_json(
    agent_meta_root: Path,
    project_root: Path,
    log: SyncLog,
    dry_run: bool,
    providers: list[str] | None = None,
    provider_config: dict | None = None,
    variables: dict | None = None,
) -> None:
    """Create provider-local settings files if they do not exist yet.

    These files are gitignored and intended for personal / machine-local
    overrides. Created once on --init or first sync — never overwritten.
    """

    pc = provider_config or {}
    active = providers if providers is not None else list(pc.keys())
    for provider in active:
        prov_cfg = pc[provider]
        local_file = prov_cfg.get("settings_local_file")
        if not local_file:
            continue
        target_path = safe_path(project_root, local_file)
        if target_path.exists():
            log.skip(str(target_path.relative_to(project_root)), "already exists")
            continue
        if is_absent_gitignored_target(target_path, dry_run):
            log.skip(str(target_path.relative_to(project_root)),
                     "absent (target root gitignored)")
            continue

        template_rel = prov_cfg.get("settings_local_template")
        template_path = agent_meta_root / template_rel if template_rel else None
        if template_path and template_path.exists():
            content = substitute(
                template_path.read_text(encoding="utf-8"),
                variables or {}, template_rel, log,
            )
            source_label = template_rel
        else:
            content = _settings_local_fallback(local_file)
            source_label = "personal/local skeleton (gitignored)"

        log.action("INIT", str(target_path.relative_to(project_root)), source_label)
        if not dry_run:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding="utf-8")


def _settings_local_fallback(local_file: str) -> str:
    """Return a minimal, extension-aware skeleton for a local settings file."""
    lower = local_file.lower()
    if lower.endswith((".yaml", ".yml")):
        return "# Local overrides — managed by agent-meta, never committed\n"
    return '{\n}\n'


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
        required = []

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
        # Function replacement keeps generated path entries verbatim (#674).
        new_content = block_pattern.sub(lambda _m: new_block, existing)
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


def sync_claude_md_static(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
):
    """Create or regenerate the STATIC part of CLAUDE.md (above the managed block).

    Supersedes the old write-once init_claude_md(): the static header (project
    name, tech stack, architecture — all derived from project.yaml) is now
    refreshed on every sync so it never drifts. The managed block itself stays
    owned by _update_managed_html_block() and is
    preserved verbatim here. User edits to the static part are detected via the
    sidecar hash store and backed up before overwrite.
    """


    template_path = agent_meta_root / "templates" / "configs" / "CLAUDE.project-template.md"
    target_path = project_root / "CLAUDE.md"
    rel = "CLAUDE.md"

    if not template_path.exists():
        log.warning(f"CLAUDE.project-template.md not found at {template_path}")
        return

    if not target_path.exists():
        fallback_partials = agent_meta_root / "templates" / "context" / "partials"
        builder = TemplateBuilder(template_path.parent, fallback_partials_dir=fallback_partials)
        rendered = builder.build(template_path.stem, variables)
        new_header, _managed, _footer = _split_context_file(rendered)
        log.action("INIT", rel, "templates/configs/CLAUDE.project-template.md")
        if not dry_run:
            target_path.write_text(rendered, encoding="utf-8")
        _record_static_hash(
            project_root, rel, _normalize_static_sig(_strip_user_notes(new_header)), dry_run
        )
        return

    _regenerate_static_context(
        project_root, target_path, template_path, variables, log, dry_run,
        rel_label=rel, source_label="CLAUDE.project-template.md",
    )


def only_variables(
    project_root: Path,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    providers: list[str] | None = None,
    provider_config: dict | None = None,
):
    """Substitute {{VARIABLE}} placeholders in existing provider context files."""

    pc = provider_config or {}
    active = providers if providers is not None else list(pc.keys())
    found_any = False
    for provider in active:
        context_file = pc[provider].get("context_file")
        if not context_file:
            continue
        target_path = safe_path(project_root, context_file)
        if not target_path.exists():
            continue
        found_any = True
        content = target_path.read_text(encoding="utf-8")
        if _MANAGED_BLOCK_RE.search(content):
            log.warning(
                f"{context_file}: --only-variables substitutes placeholders only — "
                "the agent-meta managed block is not re-rendered (S3); run a full "
                "sync to refresh it."
            )
        new_content = substitute(content, variables, context_file, log)

        if new_content == content:
            log.skip(context_file, "no open placeholders")
        else:
            log.action("WRITE", context_file, "variables from config")
            if not dry_run:
                target_path.write_text(new_content, encoding="utf-8")

    if not found_any:
        print("  !  No provider context file found — use --init to create one")
        import sys
        sys.exit(1)


def sync_prompts_for_continue(
    agent_meta_root: Path,
    project_root: Path,
    config: dict,
    variables: dict,
    log: SyncLog,
    dry_run: bool,
    provider_config: dict | None = None,
):
    """Generate .continue/prompts/<role>.md as invokable slash-commands.

    Controlled by provider-options.Continue:
        generate-prompts: true          # enable (default: false)
        prompt-mode: "full" | "slim"    # full = complete agent body (default)
                                        # slim = compact role + core rules only

    Works with any local LLM — no tool calling required.
    Slash-commands: /developer, /git, /orchestrator, ...
    """
    from .agent_sync import compose_agent
    from .frontmatter import (
        AGENTS_DIR,
        _strip_frontmatter,
        collect_sources,
        extract_frontmatter_field,
        target_filename,
    )
    from .provider_transform import _make_slim_body, _strip_claude_specific_lines
    from .providers import resolve_provider_options
    from .roles import build_role_map

    opts = resolve_provider_options(config, "Continue")
    if not opts.get("generate-prompts", False):
        return

    pc = (provider_config or {}).get("Continue", {})
    provider_vars = {
        'EXTENSION_DIR': pc.get('extension_dir', '.continue/3-project'),
        'SNIPPETS_DIR': pc.get('snippets_dir', '.continue/snippets'),
        'PENDING_TASKS_FILE': pc.get('pending_tasks_file', '.continue/pending-tasks.md'),
        'SKILLS_DIR': pc.get('skills_dir', '.continue/skills'),
    }
    merged_vars = {**variables, **provider_vars}

    role_map = build_role_map(agent_meta_root)
    prompt_mode = opts.get("prompt-mode", "full")
    platforms = config.get("platforms", [])
    overrides, _ = collect_sources(agent_meta_root, platforms)
    allowed_roles: set | None = set(config["roles"]) if "roles" in config else None

    prompts_dir = project_root / ".continue" / "prompts"
    if not dry_run:
        prompts_dir.mkdir(parents=True, exist_ok=True)

    expected: set[str] = set()

    for role, source_path in overrides.items():
        filename = target_filename(role, role_map)
        if not filename:
            continue
        if allowed_roles is not None and role not in allowed_roles:
            continue

        expected.add(filename)
        target_path = safe_path(prompts_dir, filename)
        content = source_path.read_text(encoding="utf-8")

        # Composition
        extends_base = extract_frontmatter_field(content, "extends")
        if extends_base:
            base_path = agent_meta_root / AGENTS_DIR / extends_base
            content = compose_agent(base_path, content, log)

        rel_source = str(source_path.relative_to(agent_meta_root))
        content = substitute(content, merged_vars, rel_source, log)
        content = strip_inactive_conditional_blocks(content, merged_vars)

        # Apply PAL delegation syntax for Continue prompts
        from .delegation_syntax import DelegationSyntaxEngine
        pal_engine = DelegationSyntaxEngine(config_dir=agent_meta_root / "config")
        content = pal_engine.apply(content, "Continue")

        template_description = extract_frontmatter_field(content, "description") or f"Agent for {role}."
        template_description = template_description.replace("{{PROJECT_NAME}}", config["project"]["name"])

        # Strip original frontmatter, optionally slim the body
        body = _strip_frontmatter(content)
        body = _strip_claude_specific_lines(body)
        if prompt_mode == "slim":
            body = _make_slim_body(body)

        # Build Continue prompt frontmatter
        fm = (
            f"---\n"
            f"name: {role}\n"
            f'description: "{template_description}"\n'
            f"invokable: true\n"
            f"---\n"
        )
        final = fm + body

        layer = source_path.parts[-2]
        log.action("WRITE", str(target_path.relative_to(project_root)),
                   f"{layer}/{source_path.name} [prompt/{prompt_mode}]")
        if not dry_run:
            target_path.write_text(final, encoding="utf-8")

    # Stale cleanup
    managed_index = prompts_dir / ".agent-meta-managed"
    # IC-08/OQ-9: prompt files carry no agent-meta provenance marker, so the
    # fail-closed bootstrap (no marker/predicate) adopts nothing when the
    # index is absent — an unmanaged prompt is never swept by a fail-open
    # "delete everything unexpected" fallback.
    previously_managed = bootstrap_previously_managed(
        prompts_dir, managed_index, "*.md"
    )

    cleanup_stale_managed_files(
        prompts_dir,
        project_root,
        previously_managed,
        expected,
        log,
        dry_run,
        "role removed from config",
    )

    write_managed_index(managed_index, expected, dry_run)


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
    from .frontmatter import extract_frontmatter_field

    pc = provider_config.get(provider, {})
    snippets_dir_rel = pc.get('snippets_dir')
    if not snippets_dir_rel:
        log.note("snippets", f"skipped for {provider} — no snippets_dir configured")
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
            log.warning(f"Snippet not found: snippets/{rel_path}")
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
