"""Render 1-generic agent templates as self-contained standalone personas.

Produces plain-English, fully-resolved copies of selected generic agent
templates under ``standalone/agents/`` — no ``{{PLACEHOLDER}}`` left over,
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

from .config import read_version, strip_inactive_conditional_blocks, substitute
from .log import SyncLog

# Pilot batch — validated by hand before expanding to the full 1-generic set.
STANDALONE_ROLES: tuple[str, ...] = (
    "developer",
    "senior-developer",
    "documenter",
    "technical-writer",
    "requirements",
    "tester",
    "proofreader",
    "copyeditor",
)

REPO_URL = "https://github.com/Popoboxxo/agent-meta"

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

# Conditional flags gating {{#if VAR}} blocks tied to extension/snippet
# mechanisms and DoD gates — all inert in standalone mode. Must be present
# (not merely absent) for strip_inactive_conditional_blocks() to treat them
# as known conditional variables at all — see its docstring.
_CONDITIONAL_FALSE_FLAGS: dict[str, str] = {
    "DOD_REQ_TRACEABILITY": "false",
    "DOD_TESTS_REQUIRED": "false",
    "WEB_PROJECT_ENABLED": "false",
    "DEVELOPER_SNIPPETS_PATH_SET": "false",
    "TESTER_SNIPPETS_PATH_SET": "false",
}

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


def render_all(agent_meta_root: Path) -> dict[str, str]:
    """Return {role: rendered_content} for every STANDALONE_ROLES entry."""
    return {role: render_standalone_agent(role, agent_meta_root) for role in STANDALONE_ROLES}


def _role_summary(role: str, agent_meta_root: Path) -> str:
    """One-line description pulled from the source template's frontmatter."""
    source_path = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
    content = source_path.read_text(encoding="utf-8")
    match = re.search(r'^description:\s*"(.+?)"\s*$', content, re.MULTILINE)
    if not match:
        return ""
    desc = match.group(1)
    # First sentence only — the index is a scan list, not the full description.
    return desc.split(". ")[0].rstrip(".") + "."


def render_index(agent_meta_root: Path) -> str:
    """Render standalone/README.md — the discovery index for chat AIs browsing the repo."""
    version = read_version(agent_meta_root)
    lines = [
        "# Standalone Agent Personas",
        "",
        f"Pre-rendered, fully self-contained copies of [agent-meta]({REPO_URL})'s "
        "generic agent personas — no Python, no `sync.py`, no repo clone required.",
        "",
        "## How to use",
        "",
        "1. Pick the role below that matches what you need help with.",
        "2. Open its file (or ask a browsing-capable chat AI to fetch it from this "
        "repo directly).",
        "3. Paste the whole file as your system prompt / custom instructions.",
        "",
        "**Scope note:** each persona is a solo snapshot. No multi-agent delegation, "
        "no DoD gate, no A2A protocol, no project-specific config — for the full "
        f"pipeline (multi-agent orchestration, project-aware context, quality gates), "
        f"see the [main repo]({REPO_URL}).",
        "",
        "## Available roles",
        "",
        "| Role | Description | File |",
        "|------|-------------|------|",
    ]
    for role in STANDALONE_ROLES:
        summary = _role_summary(role, agent_meta_root) or "—"
        lines.append(f"| `{role}` | {summary} | [`agents/{role}.md`](agents/{role}.md) |")
    lines += [
        "",
        f"---",
        f"Generated from agent-meta v{version}. Regenerate via "
        "`python scripts/sync.py --render-standalone` (or the Admin UI's Sync page).",
        "",
    ]
    return "\n".join(lines)


def write_standalone_files(agent_meta_root: Path, *, dry_run: bool = False) -> dict:
    """Render all STANDALONE_ROLES + the index, write them to standalone/agents/,
    return a summary dict of what changed. Does not write when dry_run=True."""
    out_dir = agent_meta_root / "standalone" / "agents"
    written: list[str] = []
    unchanged: list[str] = []

    rendered = render_all(agent_meta_root)
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

    index_content = render_index(agent_meta_root)
    index_target = agent_meta_root / "standalone" / "README.md"
    index_existing = index_target.read_text(encoding="utf-8") if index_target.exists() else None
    if index_existing != index_content:
        written.append(str(index_target.relative_to(agent_meta_root)))
        if not dry_run:
            index_target.write_text(index_content, encoding="utf-8")
    else:
        unchanged.append(str(index_target.relative_to(agent_meta_root)))

    return {"written": written, "unchanged": unchanged, "roles": list(rendered.keys())}


def check_standalone_drift(agent_meta_root: Path) -> list[str]:
    """Return the list of standalone files that would change on a real render
    (empty list = up to date). Used by `sync.py --render-standalone --check`."""
    result = write_standalone_files(agent_meta_root, dry_run=True)
    return result["written"]
