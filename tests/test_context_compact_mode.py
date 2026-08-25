"""Regression tests for COMPACT_MODE derivation from context_file.mode.

Issue #540 Phase C1: build_variables() must derive the boolean flag
COMPACT_MODE from the new top-level config key context_file.mode. Safe-side
direction is mandatory: True ONLY for mode == "compact" — a missing key, an
invalid value or a non-mapping block must all resolve to False (full mode),
so context compression can never activate by accident.

Also verifies the B2 wiring contract: {{#if COMPACT_MODE}} blocks in context
templates are resolved against exactly this variables dict by
TemplateBuilder.resolve_conditionals().

Phase B adds end-to-end coverage for the compression itself:
  - full mode must stay BYTE-IDENTICAL to the committed generated files
    (the core safety contract of the whole feature)
  - compact mode must shrink AGENTS.md while every mandatory instruction
    anchor survives (CRITICAL GATE, Branch-Guard, Commit-Konventionen,
    Sprachregeln, MCP prohibition lists incl. honcho/playwright/reqogniloom
    core bans, short-form bootstrap, keywords directory table)
"""

import shutil
import subprocess
from pathlib import Path

import pytest

from scripts.lib.config import build_variables, load_config
from scripts.lib.context_templates.builder import TemplateBuilder

REPO_ROOT = Path(__file__).resolve().parents[1]


def _compact_mode(config: dict) -> str:
    """Run build_variables() and return the derived COMPACT_MODE flag."""
    repo_root = Path(__file__).resolve().parents[1]
    variables, _ = build_variables(config, repo_root)
    return variables["COMPACT_MODE"]


def test_compact_mode_true_when_mode_is_compact():
    assert _compact_mode({"context_file": {"mode": "compact"}}) == "true"


def test_compact_mode_false_when_mode_is_full():
    assert _compact_mode({"context_file": {"mode": "full"}}) == "false"


def test_compact_mode_false_when_key_missing():
    assert _compact_mode({}) == "false"


def test_compact_mode_false_when_value_invalid():
    # Any value other than "compact" (wrong casing, unknown word, wrong type)
    # must fall back to full mode — never enable compression by accident.
    for invalid in ("Compact", "COMPACT", "slim", "", None, True):
        assert _compact_mode({"context_file": {"mode": invalid}}) == "false", (
            f"mode={invalid!r} unexpectedly enabled compact mode"
        )


def test_compact_mode_false_when_context_file_not_a_mapping():
    # Defensive: a scalar context_file block (config typo) must not crash
    # and must not enable compact mode.
    assert _compact_mode({"context_file": "compact"}) == "false"


def test_compact_mode_overrides_stale_user_variable():
    # context_file.mode is the canonical source — a leftover
    # variables.COMPACT_MODE entry in project.yaml must not win.
    config = {
        "context_file": {"mode": "full"},
        "variables": {"COMPACT_MODE": "true"},
    }
    assert _compact_mode(config) == "false"


def test_if_conditional_resolves_against_derived_flag():
    # Wiring contract for B2: TemplateBuilder.resolve_conditionals() evaluates
    # {{#if COMPACT_MODE}} against the build_variables() output dict.
    template = "{{#if COMPACT_MODE}}compact{{else}}full{{/if}}"
    builder = TemplateBuilder(Path(__file__).resolve().parents[1] / "templates")
    compact_vars = {"COMPACT_MODE": "true"}
    full_vars = {"COMPACT_MODE": "false"}
    assert builder.resolve_conditionals(template, compact_vars).strip() == "compact"
    assert builder.resolve_conditionals(template, full_vars).strip() == "full"


# ---------------------------------------------------------------------------
# Phase B unit tests — generator-side keyword derivation (B1)
# ---------------------------------------------------------------------------

from scripts.lib.bootstrap import BootstrapEngine  # noqa: E402
from scripts.lib.delegation_table import derive_keywords  # noqa: E402


def test_derive_keywords_takes_first_comma_segments():
    desc = ("WCAG 2.1/2.2 Compliance-Audit, ARIA-Checks, Keyboard-Navigation, "
            "Screenreader...")
    assert derive_keywords(desc) == "WCAG 2.1/2.2 Compliance-Audit, ARIA-Checks, Keyboard-Navigation"


def test_derive_keywords_splits_on_und():
    assert derive_keywords("Feature-Implementierung und Bugfixes") == \
        "Feature-Implementierung, Bugfixes"


def test_derive_keywords_strips_egg_marker_and_caps_at_three():
    out = derive_keywords("[EASTER EGG / GAG] Der übereifrige Praktikant")
    assert "EASTER" not in out
    assert out == "Der übereifrige Praktikant"


def test_derive_keywords_first_sentence_only_and_empty_safe():
    assert derive_keywords("Erster Satz. Zweiter Satz.") == "Erster Satz"
    assert derive_keywords("") == ""
    assert derive_keywords(None) == ""


# ---------------------------------------------------------------------------
# Phase B unit tests — agents-table partial (B1)
# ---------------------------------------------------------------------------


def _agents_table_body() -> str:
    raw = (REPO_ROOT / "templates/context/partials/agents-table.md").read_text(encoding="utf-8")
    return raw.split("---", 2)[2].lstrip()


_SAMPLE_AGENTS = [
    {"name": "alpha", "short_desc": "Erstes Tool, zweites Feature, drittes Ding, viertes",
     "keywords": "Erstes Tool, zweites Feature, drittes Ding"},
    {"name": "beta", "short_desc": "Zweites Agent kurz", "keywords": "Zweites Agent"},
]


def test_agents_table_full_render_keeps_legacy_layout_byte_for_byte():
    # Legacy layout: blank line between rows, full description column.
    legacy = ("| Agent | Core Capabilities |\n"
              "|-------|-------------------|\n"
              "\n| `alpha` | Erstes Tool, zweites Feature, drittes Ding, viertes |\n"
              "\n| `beta` | Zweites Agent kurz |\n\n")
    builder = TemplateBuilder(REPO_ROOT / "templates" / "context")
    body = _agents_table_body()
    rendered = builder.resolve_conditionals(
        builder.resolve_loops(body, {"active_agents": _SAMPLE_AGENTS}),
        {"COMPACT_MODE": "false"},
    )
    assert rendered == legacy


def test_agents_table_compact_render_is_dense_with_keywords():
    builder = TemplateBuilder(REPO_ROOT / "templates" / "context")
    body = _agents_table_body()
    rendered = builder.resolve_conditionals(
        builder.resolve_loops(body, {"active_agents": _SAMPLE_AGENTS}),
        {"COMPACT_MODE": "true"},
    )
    lines = [line for line in rendered.splitlines() if line.strip()]
    # Header pair + one dense row per agent, no blank-line separators.
    assert len(lines) == 4
    assert rendered.count("\n\n") <= 1  # at most the single trailing blank line
    assert "| `alpha` | Erstes Tool, zweites Feature, drittes Ding |" in lines
    assert "kurz" not in rendered  # full description must not leak into compact


# ---------------------------------------------------------------------------
# Phase B unit tests — MCP / external-tool / knowledge sections (B3, B8)
# ---------------------------------------------------------------------------

from scripts.lib.agents import build_knowledge_engine_hints  # noqa: E402
from scripts.lib.external_tools import (  # noqa: E402
    EXTERNAL_HOOKS_DIR,
    _generate_tool_rule_content,
)
from scripts.lib.mcp import _generate_rule_content  # noqa: E402

_SERVER_DEF = {
    "description": "Demo server",
    "tools": {
        "allowed": ["a_tool"],
        "blocked": ["b_delete"],
    },
    "agent-hint": "Use a_tool wisely.",
    "connection": {"type": "sse", "url": "{{DEMO_URL}}"},
}


def test_mcp_full_content_keeps_hints_and_footer():
    content = _generate_rule_content("demo", _SERVER_DEF)
    assert "## Agent-Hinweise" in content
    assert "## Verbindungstyp" in content
    assert "- URL:" in content
    assert "Generiert von agent-meta aus `config/mcp-registry.yaml`" in content


def test_mcp_compact_content_is_listen_only_with_mandatory_blocks():
    content = _generate_rule_content("demo", _SERVER_DEF, compact=True)
    # Mandatory anchors: both tool lists survive verbatim.
    assert "## Erlaubte Tools" in content and "- `a_tool`" in content
    assert "## Verbotene Tools (ABSOLUT — keine Ausnahmen)" in content
    assert "- `b_delete`" in content
    # Connection collapses to a single pointer line; prose/footer vanish.
    assert "**Verbindungstyp:** `sse` — Details: `config/mcp-registry.yaml`." in content
    assert "## Agent-Hinweise" not in content
    assert "Use a_tool wisely." not in content
    assert "- URL:" not in content
    assert "Generiert von agent-meta aus" not in content


def test_external_tool_full_content_keeps_rule_body():
    tool_def = {"description": "demo tool", "rule-content": "Nutzungsregel Eins.",
                "hooks": ["guard-a"], "permitted-injections": []}
    content = _generate_tool_rule_content("demo", tool_def, {}, REPO_ROOT)
    assert "Nutzungsregel Eins." in content
    assert "## Hook-Wrapper" in content


def test_external_tool_compact_content_is_pointer(tmp_path):
    tool_def = {"description": "demo tool", "rule-content": "Nutzungsregel Eins.",
                "hooks": ["guard-a"], "permitted-injections": []}
    content = _generate_tool_rule_content("demo", tool_def, {}, tmp_path, compact=True)
    assert "> demo tool" in content
    assert f"`{EXTERNAL_HOOKS_DIR}/guard-a.sh`" in content
    assert "Details/Registrierung: `config/external-tools-registry.yaml`." in content
    assert "Nutzungsregel Eins." not in content


def test_knowledge_engine_hints_full_vs_compact():
    config = {"knowledge-engine": {"enabled": True, "domain": "personal", "bundle-path": "knowledge"}}
    full = build_knowledge_engine_hints(config)
    compact = build_knowledge_engine_hints(config, compact=True)
    assert "### Knowledge-Agenten" in full and "### Knowledge-Workflows" in full
    assert len(compact.splitlines()) < len(full.splitlines()) / 2
    assert "`knowledge/wiki/index.md`" in compact
    assert "`knowledge/schema.md`" in compact
    assert "modifiziert NIEMALS" in compact  # immutability rule is instruction


def test_agent_delegation_table_resolves_conditionals_both_modes():
    # AGENT_DELEGATION_TABLE is rendered in build_variables() via
    # resolve_partials + resolve_loops and injected into agent templates where
    # strip_inactive_conditional_blocks' final cleanup deletes leftover
    # {{#if}}/{{else}} markers VERBATIM — an unresolved conditional here would
    # concatenate both table variants into the orchestrator agents.
    from scripts.lib.config import load_config

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")

    variables, _ = build_variables(config, REPO_ROOT)
    full_table = variables["AGENT_DELEGATION_TABLE"]
    assert "{{#if" not in full_table and "{{else}}" not in full_table
    assert "\n\n| `" in full_table  # legacy blank-line-separated layout

    compact_config = dict(config)
    compact_config["context_file"] = {"mode": "compact"}
    compact_vars, _ = build_variables(compact_config, REPO_ROOT)
    compact_table = compact_vars["AGENT_DELEGATION_TABLE"]
    assert "{{#if" not in compact_table and "{{else}}" not in compact_table
    assert "\n\n| `" not in compact_table  # dense keyword rows
    assert "| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben |" in compact_table


def test_bootstrap_full_contains_enumerations(tmp_path):
    (tmp_path / "a.md").write_text("---\ndescription: A\n---\nbody", encoding="utf-8")
    (tmp_path / "b.md").write_text("---\ndescription: B\n---\nbody", encoding="utf-8")
    engine = BootstrapEngine()
    text = engine.generate_gemini_bootstrap_instructions(tmp_path)
    assert 'define_subagent(name="a", ...)' in text
    assert "- `a.md` → registriere als `a`" in text


def test_bootstrap_compact_is_short_form_without_enumeration(tmp_path):
    (tmp_path / "a.md").write_text("---\ndescription: A\n---\nbody", encoding="utf-8")
    engine = BootstrapEngine()
    text = engine.generate_gemini_bootstrap_instructions(
        tmp_path, compact=True, agents_label=".gemini/agents")
    assert "registriere jeden Agenten unter seinem Dateinamen (ohne `.md`) via `define_subagent`" in text
    assert ".gemini/agents" in text
    assert "NICHT in der Runtime" in text  # warning anchor preserved
    assert "define_subagent(name=" not in text
    assert len(text.splitlines()) <= 10


def test_bootstrap_compact_skips_empty_dir(tmp_path):
    engine = BootstrapEngine()
    assert engine.generate_gemini_bootstrap_instructions(
        tmp_path, compact=True, agents_label=".gemini/agents") == ""


# ---------------------------------------------------------------------------
# Phase B integration — full pipeline against the real templates
# ---------------------------------------------------------------------------


def _render_context(mode: str, workdir: Path) -> str:
    """Run the real opencode strategy for this repo's config into workdir."""
    import sys

    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    from lib.context import sync_context_for_provider
    from lib.log import SyncLog
    from lib.providers import load_providers_config

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    if mode == "compact":
        config["context_file"] = {"mode": "compact"}
    variables, _ = build_variables(config, REPO_ROOT)
    provider_config = load_providers_config(REPO_ROOT)
    log = SyncLog()
    # Order mirrors how the committed AGENTS.md was produced: Gemini last
    # (its PENDING_TASKS_FILE/SKILLS_DIR flavor wins in the shared file).
    for provider in ("Opencode", "Gemini"):
        sync_context_for_provider(
            REPO_ROOT, workdir, config, variables, log,
            dry_run=False, provider=provider, provider_config=provider_config,
        )
    if mode == "compact":
        # The bootstrap block lives in the AGENTS.md injected footer and is
        # written by the agents step (B6 wiring) — run it like sync.py does.
        from lib.agents import sync_agents_for_provider

        gemini_vars = {**variables, "PIPELINE_DETAILS_DIR": ".gemini/pipeline-details"}
        sync_agents_for_provider(
            REPO_ROOT, workdir, config, gemini_vars, log,
            dry_run=False, provider="Gemini", provider_config=provider_config,
        )
    return (workdir / "AGENTS.md").read_text(encoding="utf-8")


@pytest.fixture
def seeded_project(tmp_path):
    """Temp copy of this repo's committed AGENTS.md as sync target."""
    shutil.copy(REPO_ROOT / "AGENTS.md", tmp_path / "AGENTS.md")
    return tmp_path


_MANDATORY_ANCHORS = (
    "CRITICAL GATE",
    "# Branch-Guard",
    "# Commit-Konventionen",         # commit conventions section survives
    "Conventional Commits (feat, fix, chore)",  # concrete convention statement
    "# Sprachregeln",
    "`delete_conclusion`",           # honcho prohibitions
    "`set_config`",                  # honcho prohibitions
    "`browser_run_code_unsafe`",     # playwright prohibitions
    "`browser_evaluate`",            # playwright prohibitions
    "`workspace.delete`",            # reqogniloom prohibitions
)


def test_full_mode_output_is_byte_identical_to_committed_file(seeded_project):
    # THE safety contract of issue #540: with mode unset (= full) the
    # regenerated AGENTS.md must equal the committed generated artifact
    # byte-for-byte. Any template change that leaks into full mode fails here.
    assert _render_context("full", seeded_project) == (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")


def test_compact_mode_shrinks_and_preserves_mandatory_anchors(seeded_project):
    committed_lines = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8").splitlines()
    compact = _render_context("compact", seeded_project)
    lines = compact.splitlines()

    # Must shrink substantially (baseline 1082 lines; embedded rules stay by
    # design, so the realistic floor is well above the <400 plan stretch goal).
    assert len(lines) < len(committed_lines) * 0.75

    for anchor in _MANDATORY_ANCHORS:
        assert anchor in compact, f"mandatory anchor missing in compact render: {anchor}"

    # Overviews are gone (discoverable via ls/find).
    for overview in ("## Architektur", "## Tech-Stack", "## Build & Development"):
        assert overview not in compact, f"overview still present: {overview}"

    # MCP sections collapsed to listen-only.
    assert "## Agent-Hinweise" not in compact
    assert "**Verbindungstyp:** `sse` — Details: `config/mcp-registry.yaml`." in compact

    # Directory uses dense keyword rows instead of blank-line-separated prose.
    assert "\n\n| `" not in compact
    assert "| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben |" in compact

    # Knowledge hints reduced to the pointer form.
    assert "### Knowledge-Workflows" not in compact
    assert "`knowledge/wiki/index.md`" in compact

    # Bootstrap block uses the short form (B6): instruction core preserved,
    # per-agent enumeration gone.
    assert "registriere jeden Agenten unter seinem Dateinamen (ohne `.md`) via `define_subagent`" in compact
    assert "NICHT in der Runtime" in compact
    assert "define_subagent(name=" not in compact

    # graphify section reduced to title + pointer lines.
    assert "Beziehungsfragen. Bei Bedarf" not in compact
    assert "Details/Registrierung: `config/external-tools-registry.yaml`." in compact


def test_compact_mode_render_is_idempotent(seeded_project):
    first = _render_context("compact", seeded_project)
    second = _render_context("compact", seeded_project)
    assert first == second


# ---------------------------------------------------------------------------
# Phase D (D3b) — provider matrix: Compact×Claude and Compact×Opencode
# ---------------------------------------------------------------------------


def _compact_variables():
    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    config["context_file"] = {"mode": "compact"}
    variables, _ = build_variables(config, REPO_ROOT)
    return config, variables


def test_540_d3b_compact_claude_renders_managed_block_without_placeholders(tmp_path):
    # Compact×Claude leg of the provider matrix (issue #540 plan D3b): the
    # CLAUDE.md managed block must render cleanly in compact mode — no crash,
    # intact managed markers, zero unresolved {{PLACEHOLDER}} tokens.
    import sys

    scripts_dir = str(REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from lib.context import sync_context_for_provider
    from lib.log import SyncLog
    from lib.providers import load_providers_config

    shutil.copy(REPO_ROOT / "CLAUDE.md", tmp_path / "CLAUDE.md")

    config, variables = _compact_variables()
    provider_config = load_providers_config(REPO_ROOT)
    log = SyncLog()
    sync_context_for_provider(
        REPO_ROOT, tmp_path, config, variables, log,
        dry_run=False, provider="Claude", provider_config=provider_config,
    )
    claude_md = (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    assert "<!-- agent-meta:managed-begin -->" in claude_md
    assert "<!-- agent-meta:managed-end -->" in claude_md
    block = claude_md.split("<!-- agent-meta:managed-begin -->", 1)[1]
    block = block.split("<!-- agent-meta:managed-end -->", 1)[0]
    assert "{{" not in block and "}}" not in block


def test_540_d3b_opencode_compact_embeds_rules_inline_rather_than_separating(
        seeded_project):
    # Compact×Opencode leg of the provider matrix (issue #540 plan D3b).
    # Opencode declares has_rules:false — rules MUST stay embedded in
    # AGENTS.md (in compact form), never fall back to a native rules dir or
    # the pointer-only separation variant used by has_rules providers.
    compact = _render_context("compact", seeded_project)

    # Embedded rule bodies survive inline (instruction anchors are real
    # rule-file content, not pointers).
    assert "# Branch-Guard" in compact
    assert "Verwende Conventional Commits (feat, fix, chore)." in compact
    assert "## Regeln" in compact

    # The separation pointer (used when rules live natively per provider)
    # must NOT appear.
    assert "Alle Regeln werden nativ über den Provider-Rules-Mechanismus geladen." \
        not in compact

    # Embeds arrive in their COMPACT form, not the full variant.
    assert "**Verbindungstyp:** `sse` — Details: `config/mcp-registry.yaml`." in compact
    assert "## Agent-Hinweise" not in compact
