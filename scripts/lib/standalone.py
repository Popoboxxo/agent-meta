"""Render 1-generic agent templates as self-contained standalone personas.

Produces plain-English, fully-resolved copies of every generic agent
template under ``standalone/agents/`` — no ``{{PLACEHOLDER}}`` left over,
no Python/sync.py required to use them. Intended to be pasted directly as
a system prompt / custom instructions into any chat AI.

This is deliberately NOT the same pipeline as ``sync_agents_for_provider()``
in ``agents.py``: that pipeline assumes a real ``project.yaml`` (providers,
active roles, DoD config, composition). Standalone rendering has no such
config to draw on, so it substitutes a small, hand-picked set of English
fallback values instead — instructions to the LLM ("ask the user...")
rather than invented facts.
"""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from .frontmatter import _YAML_AVAILABLE, _parse_frontmatter_yaml, is_deprecated_template
from .config import (
    _orch_mode_flags,
    _resolve_orch_mode,
    read_version,
    strip_inactive_conditional_blocks,
    substitute,
)
from .log import SyncLog
from .roles import load_roles_config

REPO_URL = "https://github.com/Popoboxxo/agent-meta"


def discover_standalone_roles(agent_meta_root: Path) -> tuple[str, ...]:
    """Every 1-generic role eligible for standalone rendering — by default, all
    of them. Mirrors the same skip rules as the main sync pipeline (see
    ``agents.py::resolve_agent_overrides``): files starting with ``_`` are
    reserved resources/templates, not roles; templates marked
    ``deprecated: true`` are excluded."""
    generic_dir = agent_meta_root / "agents" / "1-generic"
    roles = []
    for f in sorted(generic_dir.glob("*.md")):
        if f.name.startswith("_"):
            continue
        if is_deprecated_template(f.read_text(encoding="utf-8")):
            continue
        roles.append(f.stem)
    return tuple(roles)

# Identity/config placeholders that need real project.yaml data to resolve
# meaningfully. Fallback values read as instructions to the LLM, not
# invented facts about a project that doesn't exist for this render.
_IDENTITY_FALLBACKS: dict[str, str] = {
    "PROJECT_NAME": "your project",
    "PROJECT_SHORT": "your project",
    "PREFIX": "proj",
    "PROJECT_CONTEXT": "(not provided — ask the user for a short project description if you need it)",
    "PROJECT_GOAL": "(not provided — ask the user what they're trying to achieve)",
    "PROJECT_LANGUAGES": "(not provided — ask the user, or infer from the code you're shown)",
    "ARCHITECTURE": "(not provided — ask the user, or infer from the code you're shown)",
    "CODE_CONVENTIONS": "(not provided — follow the conventions already visible in the code you're shown)",
    "DEV_COMMANDS": "(not provided — ask the user how to build/run/test this project)",
    "TEST_COMMANDS": "(not provided — ask the user how to run tests)",
    "REQ_CATEGORIES": "(not provided — ask the user how they categorize requirements, or propose your own)",
    "CODE_LANGUAGE": "ask the user, default to English if unspecified",
    "COMMUNICATION_LANGUAGE": "the language the user writes in",
    "DOCS_LANGUAGE": "the language the user writes in, default to English if unspecified",
    "INTERNAL_DOCS_LANGUAGE": "the language the user writes in, default to English if unspecified",
    "EXTRA_DONTS": "",
}

# Multi-agent / orchestration blocks: no delegation infrastructure exists
# outside a full agent-meta install, so these render empty — matching how
# they already behave in a real project with A2A/DoD disabled.
_ORCHESTRATION_FALLBACKS: dict[str, str] = {
    "A2A_HANDOFF_BLOCK": "",
    "ANTI_RECURSION_BLOCK": "",
    "DOD_REQ_BLOCK": "",
    "DOD_TESTS_BLOCK": "",
}

# Conditional flags gating {{#if VAR}}/{{#unless VAR}} blocks tied to
# extension/snippet mechanisms, DoD gates, and other project-specific
# infrastructure — all inert in standalone mode. Every flag referenced by a
# {{#if}} in agents/1-generic/*.md must have an entry here (regardless of
# true/false): strip_inactive_conditional_blocks() only recognizes a
# variable as conditional if it's a literal key in the variables dict — an
# omitted flag falls through to that function's orphaned-marker cleanup,
# which keeps the block unconditionally. For mutually exclusive flag groups
# (ORCH_MODE_*, DOD_SE_*) omitting even one member means every branch
# renders at once (e.g. "Mode: strictadvisorydisabled.") instead of picking
# the single intended branch — see git history for the concrete case that
# prompted this comment.
_CONDITIONAL_FALSE_FLAGS: dict[str, str] = {
    "DOD_REQ_TRACEABILITY": "false",
    "DOD_TESTS_REQUIRED": "false",
    "DOD_CODEBASE_OVERVIEW": "false",
    "DOD_SECURITY_AUDIT": "false",
    "WEB_PROJECT_ENABLED": "false",
    "DEVELOPER_SNIPPETS_PATH_SET": "false",
    "TESTER_SNIPPETS_PATH_SET": "false",
    "DEV_STACK_START_SET": "false",
    # No A2A infrastructure or knowledge-engine bundle exists standalone —
    # matches the scope note in the rendered header ("no A2A protocol, no
    # project-specific config").
    "A2A_PROTOCOL_ENABLED": "false",
    "KNOWLEDGE_ENGINE_ENABLED": "false",
    # DIRECT_DISPATCH_SECTION is a large partial loaded from
    # templates/direct-dispatch-section.md — unavailable standalone, so
    # disable the flag rather than leak a "[...not available...]" note
    # mid-document.
    "DIRECT_DISPATCH_ENABLED": "false",
    # SE-cascade requirement level: standalone has no SE infrastructure to
    # enforce, so it's "optional" (the only one of the three that's true)
    # rather than "recommended"/"strict".
    "DOD_SE_OPTIONAL": "true",
    "DOD_SE_RECOMMENDED": "false",
    "DOD_SE_STRICT": "false",
}
# Orchestrator mode flags (mutually exclusive) — reuse the real resolver so
# standalone matches the schema's own default (orchestrator.enabled=true,
# strict=true → "strict") instead of hand-duplicating it.
_CONDITIONAL_FALSE_FLAGS.update(_orch_mode_flags(_resolve_orch_mode({})))

_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
# The boilerplate pointer line every 1-generic template opens with — always
# its own full line, safe to delete outright.
_EXTENSION_BOILERPLATE_RE = re.compile(r"^> \*\*Extension:\*\*.*\n?", re.MULTILINE)
# The extension-file-path token wherever else it's referenced (numbered
# workflow steps, inline prose). Replaced in place rather than deleting the
# whole line, so surrounding sentence/step content survives.
_EXTENSION_PATH_RE = re.compile(r"`\{\{EXTENSION_DIR\}\}/\{\{PREFIX\}\}-[a-z0-9-]+-ext\.md`")
_EXTENSION_PATH_FALLBACK = "a project-specific extension file (not available in standalone mode)"
_LEFTOVER_PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
_EMPTY_BULLET_RE = re.compile(r"^- *\n", re.MULTILINE)
_EXCESS_BLANK_LINES_RE = re.compile(r"\n{3,}")


def _standalone_variables(agent_meta_root: Path) -> dict:
    variables: dict = {}
    variables.update(_IDENTITY_FALLBACKS)
    variables.update(_ORCHESTRATION_FALLBACKS)
    variables.update(_CONDITIONAL_FALSE_FLAGS)
    variables["AGENT_META_VERSION"] = read_version(agent_meta_root)
    variables["AGENT_META_DATE"] = datetime.now().strftime("%Y-%m-%d")  # noqa: DTZ005
    # Convention blocks: render the 'default' preset so a standalone release/git
    # persona keeps its versioning table / issue-naming block instead of degrading
    # to a "not available" safety-net note. active_roles=None => all roles active.
    from .conventions import render_convention_block, resolve_conventions
    _conv_log = SyncLog()
    _resolved = resolve_conventions({}, agent_meta_root)
    for _domain in ("release", "issues"):
        _spec = _resolved.get(_domain)
        if isinstance(_spec, dict):
            _blocks = render_convention_block(_domain, _spec, None, _conv_log)
            if _blocks:
                variables.update(_blocks)
    return variables


def _role_title(role: str) -> str:
    return role.replace("-", " ").title()


def render_standalone_agent(role: str, agent_meta_root: Path) -> str:
    """Render one ``agents/1-generic/<role>.md`` template as a fully-resolved,
    English-only standalone persona. Raises FileNotFoundError if the source
    template doesn't exist."""
    source_path = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
    content = source_path.read_text(encoding="utf-8")

    # Drop the YAML frontmatter — its `tools:` list names Claude-Code-specific
    # tools that don't map onto arbitrary chat AIs, and prompt_mode/name are
    # meaningless outside the generation pipeline.
    content = _FRONTMATTER_RE.sub("", content, count=1)

    # Drop the boilerplate extension-pointer line entirely, then replace any
    # remaining extension-file-path references in place (preserving the
    # surrounding step/sentence) rather than deleting whole lines — some of
    # those lines carry real content beyond the path reference.
    content = _EXTENSION_BOILERPLATE_RE.sub("", content)
    content = _EXTENSION_PATH_RE.sub(_EXTENSION_PATH_FALLBACK, content)

    variables = _standalone_variables(agent_meta_root)
    log = SyncLog()
    content = substitute(content, variables, f"1-generic/{role}.md (standalone)", log)
    content = strip_inactive_conditional_blocks(content, variables)

    # Safety net: any placeholder this pilot batch's fallback dicts didn't
    # anticipate becomes an explicit, honest note instead of a raw,
    # confusing {{TOKEN}} leaking into the persona.
    content = _LEFTOVER_PLACEHOLDER_RE.sub(
        lambda m: f"[{m.group(1)} — not available outside a full agent-meta install]",
        content,
    )

    # Cosmetic cleanup: dangling empty bullets (e.g. "- {{EXTRA_DONTS}}" with
    # EXTRA_DONTS resolved to "") and blank-line buildup left behind by the
    # removals above.
    content = _EMPTY_BULLET_RE.sub("", content)
    content = _EXCESS_BLANK_LINES_RE.sub("\n\n", content)

    header = (
        f"# {_role_title(role)} — Standalone Persona\n\n"
        f"> Generated from [agent-meta]({REPO_URL}) v{variables['AGENT_META_VERSION']} "
        f"(role: `{role}`) for use without a Python install — paste this whole file "
        "as your system prompt / custom instructions in any chat AI.\n"
        ">\n"
        "> **Scope note:** this is a solo snapshot of the persona. No multi-agent "
        "delegation, no DoD gate, no A2A protocol, no project-specific config or "
        f"extensions — for the full pipeline, see [{REPO_URL}]({REPO_URL}).\n\n"
    )
    return header + content.strip() + "\n"


def render_all(agent_meta_root: Path, roles: tuple[str, ...] | None = None) -> dict[str, str]:
    """Return {role: rendered_content} for every discovered standalone role."""
    if roles is None:
        roles = discover_standalone_roles(agent_meta_root)
    return {role: render_standalone_agent(role, agent_meta_root) for role in roles}


def _role_summary(role: str, agent_meta_root: Path) -> str:
    """One-line description pulled from the source template's frontmatter.

    Uses the real YAML frontmatter parser (agents.py::_parse_frontmatter_yaml)
    rather than a hand-rolled regex — several SE-cascade templates fold their
    `description:` across multiple lines (quoted or not), which a single-line
    regex silently truncates or misses.
    """
    source_path = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
    content = source_path.read_text(encoding="utf-8")
    if _YAML_AVAILABLE:
        desc = _parse_frontmatter_yaml(content).get("description", "")
    else:
        match = re.search(r'^description:\s*"(.+?)"\s*$', content, re.MULTILINE)
        desc = match.group(1) if match else ""
    if not desc:
        return ""
    # First sentence only — the index is a scan list, not the full description.
    return desc.split(". ")[0].rstrip(".") + "."


# German descriptions for 1-generic roles that role-defaults.yaml doesn't
# cover — currently just `provider-expert`, whose role-defaults.yaml entries
# only exist as concrete 2-platform variants (claude-expert, gemini-expert,
# ...), not the abstract generic base this standalone render targets.
_ROLE_SUMMARY_DE_FALLBACKS: dict[str, str] = {
    "provider-expert": "Absoluter Analyse-Experte für eine KI-Plattform: Funktionsweise, "
    "Konfiguration, Best Practices zur optimalen Anpassung von agent-meta.",
}


def _role_summary_de(role: str, roles_cfg: dict) -> str:
    """German one-line description, sourced from config/role-defaults.yaml
    (already German-language for internal routing tables like
    use-orchestrator.md) rather than the frontmatter `description:` field,
    which is inconsistently English/German across templates."""
    desc = roles_cfg.get(role, {}).get("description") or _ROLE_SUMMARY_DE_FALLBACKS.get(role, "")
    if not desc:
        return ""
    return desc.split(". ")[0].rstrip(".") + "."


def render_index(agent_meta_root: Path, roles: tuple[str, ...] | None = None) -> str:
    """Render standalone/README.md — the discovery index for chat AIs browsing the repo.

    Bilingual layout: every English block is immediately followed by its
    German translation (not two separate top/bottom sections), and the role
    table carries both an English and a German description column."""
    if roles is None:
        roles = discover_standalone_roles(agent_meta_root)
    version = read_version(agent_meta_root)
    roles_cfg = load_roles_config(agent_meta_root)["roles"]
    lines = [
        "# Standalone Agent Personas",
        "",
        f"Pre-rendered, fully self-contained copies of [agent-meta]({REPO_URL})'s "
        "generic agent personas — no Python, no `sync.py`, no repo clone required.",
        "",
        f"*Fertig gerenderte, vollständig eigenständige Kopien der generischen "
        f"Agenten-Personas von [agent-meta]({REPO_URL}) — kein Python, kein `sync.py`, "
        "kein Repo-Klon nötig.*",
        "",
        "## How to use / Verwendung",
        "",
        "1. Pick the role below that matches what you need help with.",
        "   *Passende Rolle in der Tabelle unten auswählen.*",
        "2. Open its file (or ask a browsing-capable chat AI to fetch it from this "
        "repo directly).",
        "   *Zugehörige Datei öffnen (oder eine browsing-fähige Chat-KI bitten, sie "
        "direkt aus diesem Repo zu holen).*",
        "3. Paste the whole file as your system prompt / custom instructions.",
        "   *Die gesamte Datei als System-Prompt / Custom Instructions einfügen.*",
        "",
        "**Scope note:** each persona is a solo snapshot. No multi-agent delegation, "
        "no DoD gate, no A2A protocol, no project-specific config — for the full "
        f"pipeline (multi-agent orchestration, project-aware context, quality gates), "
        f"see the [main repo]({REPO_URL}).",
        "",
        "**Hinweis zum Umfang:** Jede Persona ist eine isolierte Momentaufnahme — "
        "ohne Multi-Agenten-Delegation, ohne DoD-Gate, ohne A2A-Protokoll, ohne "
        "projektspezifische Konfiguration. Für die volle Pipeline (Multi-Agenten-"
        f"Orchestrierung, projektbewusster Kontext, Quality Gates) siehe das "
        f"[Haupt-Repo]({REPO_URL}).",
        "",
        "## Available roles / Verfügbare Rollen",
        "",
        "| Role | Description | Beschreibung (DE) | File |",
        "|------|-------------|--------------------|------|",
    ]
    for role in roles:
        summary_en = _role_summary(role, agent_meta_root) or "—"
        summary_de = _role_summary_de(role, roles_cfg) or "—"
        lines.append(
            f"| `{role}` | {summary_en} | {summary_de} | [`agents/{role}.md`](agents/{role}.md) |"
        )
    lines += [
        "",
        "---",
        f"Generated from agent-meta v{version}. Regenerate via "
        "`python scripts/sync.py --render-standalone` (or the Admin UI's Sync page).",
        "",
    ]
    return "\n".join(lines)


def write_standalone_files(agent_meta_root: Path, *, dry_run: bool = False) -> dict:
    """Render every discovered standalone role + the index, write them to
    standalone/agents/, return a summary dict of what changed. Removes
    previously-rendered files for roles no longer eligible (e.g. deprecated
    since the last render). Does not write when dry_run=True."""
    out_dir = agent_meta_root / "standalone" / "agents"
    written: list[str] = []
    unchanged: list[str] = []
    removed: list[str] = []

    roles = discover_standalone_roles(agent_meta_root)
    rendered = render_all(agent_meta_root, roles=roles)
    for role, content in rendered.items():
        target = out_dir / f"{role}.md"
        existing = target.read_text(encoding="utf-8") if target.exists() else None
        if existing == content:
            unchanged.append(str(target.relative_to(agent_meta_root)))
            continue
        written.append(str(target.relative_to(agent_meta_root)))
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

    if out_dir.exists():
        for stale in sorted(out_dir.glob("*.md")):
            if stale.stem not in rendered:
                removed.append(str(stale.relative_to(agent_meta_root)))
                if not dry_run:
                    stale.unlink()

    index_content = render_index(agent_meta_root, roles=roles)
    index_target = agent_meta_root / "standalone" / "README.md"
    index_existing = index_target.read_text(encoding="utf-8") if index_target.exists() else None
    if index_existing != index_content:
        written.append(str(index_target.relative_to(agent_meta_root)))
        if not dry_run:
            index_target.write_text(index_content, encoding="utf-8")
    else:
        unchanged.append(str(index_target.relative_to(agent_meta_root)))

    return {
        "written": written,
        "unchanged": unchanged,
        "removed": removed,
        "roles": list(rendered.keys()),
    }


def check_standalone_drift(agent_meta_root: Path) -> list[str]:
    """Return the list of standalone files that would change (written or
    removed) on a real render (empty list = up to date). Used by
    `sync.py --render-standalone --check`."""
    result = write_standalone_files(agent_meta_root, dry_run=True)
    return result["written"] + result["removed"]
