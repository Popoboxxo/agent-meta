"""B2 equivalence gate for the template-slimming migration.

Spec: ``docs/specs/2026-09-19-dynamic-routing-template-slimming.md`` §3.7 and
AC **B2** (B2a byte-identical / B2b normalized). The frozen pre-slimming
generated output lives in ``tests/fixtures/slimming-golden/`` (58 active roles,
Claude provider) and must never be regenerated or edited.

This module is the single B2 gate. It is written once (Task 12) and consumed by
the later migration tasks (13 knowledge, 14/15 generic + platform). Every
migration task extends the two module-level registries below — that is the
agreed, documented shared-gate convention:

* ``_MIGRATED`` — template paths that had their inline ``## Anti-Recursion
  Guard`` prose replaced by ``{{ANTI_RECURSION_BLOCK}}``.
* ``_OUTPUT_GUARD_MIGRATED`` — template paths that had an inline canonical
  ``<output-guard>`` region replaced by ``{{OUTPUT_GUARD_BLOCK}}``.
* ``_NORMALIZATIONS`` — the declarative classification table (block kind →
  inline variants → expected post-migration text). A migration that produces a
  difference not attributable to exactly one declared entry fails the gate; a
  declared entry that is used nowhere fails too (no dead table entries).

What the gate checks
--------------------
1. **Golden comparison.** Each active role is re-rendered through the *real*
   per-role sync path (``_compose_role_content`` → ``_apply_content_pipeline``
   → ``_finalize_agent_content``). Roles whose template is not migrated must
   still be byte-identical to the golden. Migrated roles must match the golden
   after applying the declared normalizations.
2. **Normalization marking.** Every detected region of a declared kind is
   attributed to exactly one declared variant; the attribution
   (``role → block kind → variant id``) is printed on mismatch.
3. **Inverse.** No declared normalization is dead.
4. **Pflichtsätze.** Input-Parsing / Output-Guard / Handoff-Format /
   Anti-Recursion markers present in the golden must survive into the render.
5. **Structural check for migrated-but-inactive templates** (the ``se-*`` set is
   inactive in this repo and has no golden): no inline variant region remains,
   the rendered template carries the canonical block text and the mandatory
   markers.

The gate is network-free, writes nothing into the repository (the render target
is a pytest ``tmp_path``) and renders the corpus once per module (~5s).
"""
from __future__ import annotations

import difflib
import re
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from scripts.lib.agent_sync import (
    _apply_content_pipeline,
    _build_provider_vars,
    _compose_role_content,
    _finalize_agent_content,
    _resolve_sync_targets,
    _should_skip_role,
)
from scripts.lib.config import build_variables, load_config
from scripts.lib.log import SyncLog
from scripts.lib.providers import load_providers_config
from scripts.lib.roles import resolve_activation_gates
from scripts.lib.variables import strip_inactive_conditional_blocks, substitute

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GOLDEN_DIR = _REPO_ROOT / "tests" / "fixtures" / "slimming-golden"
_PROVIDER = "Claude"

# ---------------------------------------------------------------------------
# Shared-gate registries (extended by Tasks 13/14/15)
# ---------------------------------------------------------------------------

#: Templates whose inline ``## Anti-Recursion Guard`` prose was replaced by
#: ``{{ANTI_RECURSION_BLOCK}}`` (Task 12: the 14 ``se-*`` templates; Task 13:
#: the 7 ``knowledge-*`` templates — the ``AR-K1`` … ``AR-K7`` variants).
_MIGRATED = frozenset(
    {
        "agents/1-generic/se-architect.md",
        "agents/1-generic/se-component-requirements.md",
        "agents/1-generic/se-critic.md",
        "agents/1-generic/se-developer.md",
        "agents/1-generic/se-integration-and-test-manager.md",
        "agents/1-generic/se-interface-mgr.md",
        "agents/1-generic/se-junior-developer.md",
        "agents/1-generic/se-requirements.md",
        "agents/1-generic/se-senior-developer.md",
        "agents/1-generic/se-termination.md",
        "agents/1-generic/se-test-engineer.md",
        "agents/1-generic/se-testreviewer.md",
        "agents/1-generic/se-validator.md",
        "agents/1-generic/se-verifier.md",
        "agents/1-generic/knowledge-curator.md",
        "agents/1-generic/knowledge-gardener.md",
        "agents/1-generic/knowledge-indexer.md",
        "agents/1-generic/knowledge-ingestor.md",
        "agents/1-generic/knowledge-linter.md",
        "agents/1-generic/knowledge-migrator.md",
        "agents/1-generic/knowledge-querier.md",
    }
)

#: Templates whose inline canonical ``<output-guard>`` region was replaced by
#: ``{{OUTPUT_GUARD_BLOCK}}`` (Task 12: 10 of the 14 ``se-*`` templates;
#: Task 13: ``knowledge-migrator`` — the only knowledge role with the block).
_OUTPUT_GUARD_MIGRATED = frozenset(
    {
        "agents/1-generic/se-architect.md",
        "agents/1-generic/se-component-requirements.md",
        "agents/1-generic/se-critic.md",
        "agents/1-generic/se-developer.md",
        "agents/1-generic/se-junior-developer.md",
        "agents/1-generic/se-requirements.md",
        "agents/1-generic/se-senior-developer.md",
        "agents/1-generic/se-test-engineer.md",
        "agents/1-generic/se-validator.md",
        "agents/1-generic/se-verifier.md",
        "agents/1-generic/knowledge-migrator.md",
    }
)

# ---------------------------------------------------------------------------
# Declarative classification table: block kinds
# ---------------------------------------------------------------------------

_KIND_CANONICAL_VAR = {
    "ANTI_RECURSION": "ANTI_RECURSION_BLOCK",
    "OUTPUT_GUARD": "OUTPUT_GUARD_BLOCK",
    "BACKGROUND_PROCESS_GUARD": "BACKGROUND_PROCESS_GUARD_BLOCK",
    "PARSE_INPUT": "PARSE_INPUT_BLOCK",
}

#: A region ends at the next line that starts a new top-level construct: a
#: markdown heading, an XML element or a template conditional. Tolerant to any
#: leading indentation (the region text itself is dedented for matching).
_SECTION_STOP_RE = re.compile(r"^(?:[ \t]*#{1,6}\s|[ \t]*<[a-z]|[ \t]*\{\{#)", re.M)
_AR_HEADING_RE = re.compile(r"^[ \t]*##\s+Anti-Recursion Guard\s*$", re.M)
_BGP_HEADING_RE = re.compile(
    r"^[ \t]*##\s+Background-Process Guard \(issue #506\)\s*$", re.M
)
_PARSE_INPUT_HEADING_RE = re.compile(r"^[ \t]*##\s+1\.\s+Parse input\s*$", re.M)
_OUTPUT_GUARD_TAG_RE = re.compile(r"^[ \t]*<output-guard>.*?</output-guard>", re.M | re.S)


@dataclass(frozen=True)
class Region:
    start: int
    end: int
    text: str


def _dedent(text: str) -> str:
    """Normalize a region for comparison: strip common indentation + fillers."""
    return textwrap.dedent(text).strip("\n")


def _heading_regions(text: str, heading_re: re.Pattern[str]) -> list[Region]:
    regions: list[Region] = []
    for match in heading_re.finditer(text):
        rest = text[match.end():]
        stop = _SECTION_STOP_RE.search(rest)
        end = match.end() + stop.start() if stop else len(text)
        raw = text[match.start():end].rstrip("\n")
        regions.append(Region(match.start(), match.start() + len(raw), raw))
    return regions


def _output_guard_regions(text: str) -> list[Region]:
    return [
        Region(m.start(), m.end(), m.group(0))
        for m in _OUTPUT_GUARD_TAG_RE.finditer(text)
    ]


def _background_process_guard_regions(text: str) -> list[Region]:
    """Standalone ``## Background-Process Guard`` regions.

    The same heading commonly appears *inside* an ``<output-guard>`` tag; those
    occurrences belong to the OUTPUT_GUARD kind and are excluded here so the two
    kinds never normalize the same bytes twice.
    """
    tag_spans = [(r.start, r.end) for r in _output_guard_regions(text)]
    standalone: list[Region] = []
    for region in _heading_regions(text, _BGP_HEADING_RE):
        if any(region.start >= s and region.end <= e for s, e in tag_spans):
            continue
        standalone.append(region)
    return standalone


def _parse_input_regions(text: str) -> list[Region]:
    return _heading_regions(text, _PARSE_INPUT_HEADING_RE)


_LOCATORS = {
    "ANTI_RECURSION": lambda t: _heading_regions(t, _AR_HEADING_RE),
    "OUTPUT_GUARD": _output_guard_regions,
    "BACKGROUND_PROCESS_GUARD": _background_process_guard_regions,
    "PARSE_INPUT": _parse_input_regions,
}

# ---------------------------------------------------------------------------
# Declarative classification table: inline variants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Variant:
    """One declared inline variant of a block kind.

    ``inline`` is the normalized pre-migration region text. ``retained`` holds
    role-specific clauses that the migration keeps *after* the canonical block
    (semantic-loss rule); ``expected`` is derived from the canonical variable at
    comparison time. ``paths`` names the templates that carry the variant — used
    by the inverse ("no dead entry") check and for documentation.
    """

    id: str
    kind: str
    inline: str
    classification: str  # "B2a" (byte-identical) | "B2b" (normalized)
    retained: tuple[str, ...] = ()
    paths: tuple[str, ...] = field(default=())


_NORMALIZATIONS: tuple[Variant, ...] = (
    Variant(
        id="AR-1",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "Worker-Agent. Niemals Scope-Aufgaben an `orchestrator` oder andere "
            "Worker zurückdelegieren."
        ),
        paths=(
            "agents/1-generic/se-architect.md",
            "agents/1-generic/se-component-requirements.md",
            "agents/1-generic/se-critic.md",
            "agents/1-generic/se-requirements.md",
        ),
    ),
    Variant(
        id="AR-2",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "Worker-Agent. Niemals Scope-Aufgaben an `orchestrator` oder andere "
            "Worker zurückdelegieren. `status: escalate` ist kein Delegation, "
            "sondern reguläres Ergebnis.\n"
            "\n"
            "Erlaubte Eskalationen: Interface-Change → `se-interface-mgr`/"
            "`se-architect` | Boundary → `se-architect` | Unklare/contradictory "
            "specs | Critic loop exhausted → `blocked`"
        ),
        retained=(
            "`status: escalate` ist kein Delegation, sondern reguläres Ergebnis.",
            "Erlaubte Eskalationen: Interface-Change → `se-interface-mgr`/"
            "`se-architect` | Boundary → `se-architect` | Unklare/contradictory "
            "specs | Critic loop exhausted → `blocked`",
        ),
        paths=("agents/1-generic/se-senior-developer.md",),
    ),
    Variant(
        id="AR-3",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "You are a worker agent. You implement, analyze, and verify yourself. "
            "NEVER delegate scope tasks back to the orchestrator or to other "
            "workers without an explicit escalation.\n"
            "\n"
            "| Forbidden | Reason |\n"
            "|-----------|--------|\n"
            "| `@orchestrator` in output | You are a worker, not a router |\n"
            "| Task() calls to orchestrator | Only the main chat / orchestrator "
            "delegates |\n"
            "| Forwarding own scope tasks | You are the endpoint within your tier |\n"
            "\n"
            "**Exception:** The escalation card (`status: escalate`) is NOT a "
            "delegation — it is the regular result the orchestrator routes onward.\n"
            "\n"
            "Permitted escalations:\n"
            "- Interface change required → `se-interface-mgr` / `se-architect`\n"
            "- Scope exceeds your tier → `se-senior-developer` with "
            "`recommended_tier`\n"
            "- Unclear requirement / contradictory interface specs → with rationale"
        ),
        retained=(
            "**Exception:** The escalation card (`status: escalate`) is NOT a "
            "delegation — it is the regular result the orchestrator routes onward.",
        ),
        paths=("agents/1-generic/se-developer.md",),
    ),
    Variant(
        id="AR-4",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "You are a worker agent. You do NOT delegate back to the orchestrator "
            "or to other agents without an explicit escalation.\n"
            "\n"
            "| Forbidden | Reason |\n"
            "|-----------|--------|\n"
            "| `@orchestrator` in output | You are a worker, not a router |\n"
            "| Task() calls to orchestrator | Only the main chat / orchestrator "
            "delegates |\n"
            "| Forwarding own scope tasks | You are the endpoint within your tier |\n"
            "\n"
            "**Exception:** The escalation card (`status: escalate`) is NOT a "
            "delegation — it is the regular result the orchestrator routes onward.\n"
            "\n"
            "Permitted escalations (OUTPUT `status: escalate`):\n"
            "- Interface change required → escalate to `se-interface-mgr` / "
            "`se-architect`\n"
            "- Scope exceeds your tier → escalate with `recommended_tier`\n"
            "- Unclear requirement / contradictory interface specs → escalate with "
            "rationale"
        ),
        retained=(
            "**Exception:** The escalation card (`status: escalate`) is NOT a "
            "delegation — it is the regular result the orchestrator routes onward.",
        ),
        paths=("agents/1-generic/se-junior-developer.md",),
    ),
    Variant(
        id="AR-5",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Du bist Worker-Agent.** Implementiere/analysiere/prüfe selbst. "
            "Delegiere NIEMALS Aufgaben aus deinem Scope an `orchestrator` oder "
            "andere Worker zurück.\n"
            "\n"
            "Verboten: `@orchestrator` im Output, Task()-Calls an orchestrator, "
            '"Delegiere an orchestrator: ...", eigene Scope-Aufgaben weiterreichen.\n'
            "\n"
            "**Ausnahme:** Andere Worker-Rolle nötig → im Text verweisen, nicht "
            "per Tool-Call delegieren. Der orchestrator koordiniert die Reihenfolge."
        ),
        retained=(
            "**Ausnahme:** Andere Worker-Rolle nötig → im Text verweisen, nicht "
            "per Tool-Call delegieren. Der orchestrator koordiniert die Reihenfolge.",
        ),
        paths=(
            "agents/1-generic/se-integration-and-test-manager.md",
            "agents/1-generic/se-interface-mgr.md",
            "agents/1-generic/se-termination.md",
            "agents/1-generic/se-test-engineer.md",
            "agents/1-generic/se-testreviewer.md",
        ),
    ),
    Variant(
        id="AR-6",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Worker-Agent.** Implementierst/analysierst/prüfst selbst. NIEMALS "
            "Scope-Aufgaben an `orchestrator` oder andere Worker zurückdelegieren "
            '(kein `@orchestrator`, keine Task-Calls, kein "Delegiere an…"). '
            "**Ausnahme:** Andere Worker-Rolle nötig → im Text verweisen, nicht via "
            "Tool-Call delegieren."
        ),
        retained=(
            "**Ausnahme:** Andere Worker-Rolle nötig → im Text verweisen, nicht via "
            "Tool-Call delegieren.",
        ),
        paths=(
            "agents/1-generic/se-validator.md",
            "agents/1-generic/se-verifier.md",
        ),
    ),
    Variant(
        id="AR-K1",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Du bist ein Worker-Agent.** Delegiere NIEMALS Aufgaben in deinem "
            "Scope an den `orchestrator` oder andere Worker-Agenten zurück.\n"
            "\n"
            "Verboten: `@orchestrator` im Output, Task()-Calls an orchestrator, "
            "eigene Scope-Aufgaben weiterreichen.\n"
            "\n"
            "**Ausnahme:** Andere Worker-Rolle nötig (`knowledge-ingestor`, "
            "`knowledge-linter`, `knowledge-gardener`) → im Text verweisen bzw. per "
            'Tool-Call delegieren, wie in "Deine Rolle" beschrieben.'
        ),
        paths=("agents/1-generic/knowledge-curator.md",),
    ),
    Variant(
        id="AR-K2",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Du bist ein Worker-Agent.** Delegiere NIEMALS Aufgaben in deinem "
            "Scope an den `orchestrator` zurück.\n"
            "\n"
            "**Ausnahme:** Inhaltliche Findings an `knowledge-ingestor` "
            "weiterreichen, statt sie selbst zu beheben."
        ),
        paths=("agents/1-generic/knowledge-gardener.md",),
    ),
    Variant(
        id="AR-K3",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Du bist ein Worker-Agent.** Delegiere NIEMALS Aufgaben in deinem "
            "Scope an den `orchestrator` zurück."
        ),
        paths=("agents/1-generic/knowledge-indexer.md",),
    ),
    Variant(
        id="AR-K4",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Du bist ein Worker-Agent.** Delegiere NIEMALS Aufgaben in deinem "
            "Scope an den `orchestrator` zurück.\n"
            "\n"
            "**Ausnahme:** `knowledge-indexer` nach jedem Ingest delegieren — das "
            "ist Teil deines Workflows, keine Rückdelegation."
        ),
        paths=("agents/1-generic/knowledge-ingestor.md",),
    ),
    Variant(
        id="AR-K5",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Du bist ein Worker-Agent.** Delegiere NIEMALS Aufgaben in deinem "
            "Scope an den `orchestrator` zurück.\n"
            "\n"
            "**Ausnahme:** Findings an `knowledge-gardener`/`knowledge-ingestor`/"
            "`knowledge-indexer` weiterreichen — das ist dein Kernauftrag."
        ),
        paths=("agents/1-generic/knowledge-linter.md",),
    ),
    Variant(
        id="AR-K6",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Du bist ein Worker-Agent.** Delegiere NIEMALS Aufgaben in deinem "
            "Scope an den `orchestrator` zurück.\n"
            "\n"
            "**Ausnahme:** `knowledge-linter`/`knowledge-indexer` in Phase 3 "
            "delegieren — das ist Teil deines Workflows."
        ),
        paths=("agents/1-generic/knowledge-migrator.md",),
    ),
    Variant(
        id="AR-K7",
        kind="ANTI_RECURSION",
        classification="B2b",
        inline=(
            "## Anti-Recursion Guard\n"
            "\n"
            "**Du bist ein Worker-Agent.** Delegiere NIEMALS Aufgaben in deinem "
            "Scope an den `orchestrator` zurück.\n"
            "\n"
            "**Ausnahme:** `knowledge-indexer` bei File-Back delegieren."
        ),
        paths=("agents/1-generic/knowledge-querier.md",),
    ),
    # --- byte-identical (B2a) occurrences of the new block snippets ---------
    # Their inline text equals the canonical block, so canonicalizing them is an
    # identity transform and the golden comparison stays byte-identical.
    Variant(
        id="OG-CANON",
        kind="OUTPUT_GUARD",
        classification="B2a",
        inline="__CANONICAL__",
    ),
    Variant(
        id="PI-CANON",
        kind="PARSE_INPUT",
        classification="B2a",
        inline="__CANONICAL__",
    ),
)

_NORMALIZATION_INDEX: dict[tuple[str, str], Variant] = {
    (v.kind, v.inline): v for v in _NORMALIZATIONS
}

# ---------------------------------------------------------------------------
# Render environment
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderEnv:
    variables: dict
    rendered: dict[str, str]  # role -> generated content
    source_paths: dict[str, str]  # role -> repo-relative template path


@pytest.fixture(scope="module")
def render_env(tmp_path_factory: pytest.TempPathFactory) -> RenderEnv:
    """Render every active role through the real per-role sync path.

    Mirrors ``sync_agents_for_provider`` for the Claude provider but without
    writing into the repository: the target root is a pytest temp directory.
    """
    tmp_root = tmp_path_factory.mktemp("slimming-equivalence")
    config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _warnings = build_variables(config, _REPO_ROOT, tmp_root)
    provider_config = load_providers_config(_REPO_ROOT)
    log = SyncLog()
    pc, role_map, overrides, target_dir = _resolve_sync_targets(
        _PROVIDER, provider_config, _REPO_ROOT, tmp_root, config, True, log
    )
    assert pc is not None, "Claude provider config missing"
    gates = resolve_activation_gates(_REPO_ROOT, config)
    allowed_roles = set(config["roles"]) if "roles" in config else None
    project_name = config.get("project", {}).get("name", "unknown")

    rendered: dict[str, str] = {}
    source_paths: dict[str, str] = {}
    for role, source_path in overrides.items():
        skip, filename = _should_skip_role(
            role, source_path, _PROVIDER, pc, role_map, allowed_roles, config,
            variables, tmp_root, target_dir, log, gates=gates,
        )
        if skip:
            continue
        target_path = target_dir / filename
        content, can_spawn, rel_source, source_version, description = _compose_role_content(
            source_path, _PROVIDER, project_name, _REPO_ROOT, tmp_root,
            target_path, log, pc=pc,
        )
        merged = _build_provider_vars(pc, _PROVIDER, variables, _REPO_ROOT, config=config)
        content = _apply_content_pipeline(
            content, config, _PROVIDER, merged, rel_source, None, _REPO_ROOT, log
        )
        content = _finalize_agent_content(
            content, role, filename, source_path, _PROVIDER, provider_config,
            source_version, description, can_spawn, config, _REPO_ROOT, tmp_root,
            target_path, variables, False, log,
        )
        rendered[role] = content
        source_paths[role] = str(source_path.relative_to(_REPO_ROOT))
    return RenderEnv(variables=variables, rendered=rendered, source_paths=source_paths)


def _golden_roles() -> list[str]:
    return sorted(
        p.stem for p in _GOLDEN_DIR.glob("*.md") if p.name != "README.md"
    )


def _canonical(variables: dict, kind: str) -> str:
    return variables[_KIND_CANONICAL_VAR[kind]]


def _expected_text(variant: Variant, variables: dict) -> str:
    if variant.inline == "__CANONICAL__":
        return _canonical(variables, variant.kind)
    expected = _canonical(variables, variant.kind)
    if variant.retained:
        expected = expected + "\n\n" + "\n".join(variant.retained)
    return expected


def _lookup_variant(kind: str, region_text: str, variables: dict) -> Variant | None:
    normalized = _dedent(region_text)
    key = (kind, normalized)
    if key in _NORMALIZATION_INDEX:
        return _NORMALIZATION_INDEX[key]
    canonical = _canonical(variables, kind)
    if normalized == canonical:
        return _NORMALIZATION_INDEX[(kind, "__CANONICAL__")]
    return None


@dataclass(frozen=True)
class Attribution:
    kind: str
    variant_id: str
    classification: str


def _normalize(
    text: str, variables: dict
) -> tuple[str, list[Attribution]]:
    """Apply all declared normalizations to *text*.

    Returns the normalized text plus the attribution list (B2a/B2b marking).
    Raises ``AssertionError`` if a region of a declared kind matches no declared
    variant (a normalization that is detected but not declared).
    """
    attributions: list[Attribution] = []
    for kind in _LOCATORS:
        regions = _LOCATORS[kind](text)
        for region in sorted(regions, key=lambda r: r.start, reverse=True):
            variant = _lookup_variant(kind, region.text, variables)
            assert variant is not None, (
                f"{kind}: undeclared inline variant detected:\n{region.text[:400]}"
            )
            expected = _expected_text(variant, variables)
            if expected != region.text:
                text = text[: region.start] + expected + text[region.end:]
            attributions.append(
                Attribution(kind=kind, variant_id=variant.id,
                            classification=variant.classification)
            )
    return text, attributions


# ---------------------------------------------------------------------------
# 1 + 2 + 3 — golden comparison, normalization marking, inverse
# ---------------------------------------------------------------------------


def test_golden_equivalence_and_normalization_marking(render_env: RenderEnv):
    """Golden roles: unmigrated byte-identical, migrated attributed to B2b."""
    failures: list[str] = []
    b2b_marks: list[str] = []
    for role in _golden_roles():
        assert role in render_env.rendered, f"golden role not rendered: {role}"
        golden = (_GOLDEN_DIR / f"{role}.md").read_text(encoding="utf-8")
        current = render_env.rendered[role]
        template = render_env.source_paths[role]
        if template not in _MIGRATED:
            if golden != current:
                failures.append(
                    f"{role} ({template}): unexpected diff on an unmigrated role\n"
                    + "\n".join(
                        list(
                            difflib.unified_diff(
                                golden.splitlines(), current.splitlines(),
                                f"golden/{role}", f"now/{role}", lineterm="",
                            )
                        )[:40]
                    )
                )
            continue
        try:
            normalized, attributions = _normalize(golden, render_env.variables)
        except AssertionError as exc:
            failures.append(f"{role} ({template}): {exc}")
            continue
        for a in attributions:
            b2b_marks.append(f"{role} → {a.kind} → {a.variant_id} ({a.classification})")
        if normalized != current:
            failures.append(
                f"{role} ({template}): diff not attributable to declared "
                f"normalizations\nattributions: {b2b_marks}\n"
                + "\n".join(
                    list(
                        difflib.unified_diff(
                            normalized.splitlines(), current.splitlines(),
                            f"normalized/{role}", f"now/{role}", lineterm="",
                        )
                    )[:40]
                )
            )
    assert not failures, "\n\n".join(failures)


def test_no_declared_normalization_is_dead(render_env: RenderEnv):
    """Inverse: every declared normalization is used by some template."""
    dead: list[str] = []
    for variant in _NORMALIZATIONS:
        alive = any(path in _MIGRATED for path in variant.paths)
        if not alive:
            for template in sorted((_REPO_ROOT / "agents").rglob("*.md")):
                text = template.read_text(encoding="utf-8")
                if any(
                    _dedent(r.text) == variant.inline
                    for r in _LOCATORS[variant.kind](text)
                ):
                    alive = True
                    break
        if not alive and variant.inline == "__CANONICAL__":
            canonical = _canonical(render_env.variables, variant.kind)
            alive = any(
                _dedent(r.text) == canonical
                for template in sorted((_REPO_ROOT / "agents").rglob("*.md"))
                for r in _LOCATORS[variant.kind](
                    template.read_text(encoding="utf-8")
                )
            )
        if not alive:
            dead.append(variant.id)
    assert not dead, (
        "declared normalizations without any matching template (dead table "
        f"entries): {dead}"
    )


# ---------------------------------------------------------------------------
# 4 — Pflichtsatz assertions
# ---------------------------------------------------------------------------

_PFLICHTSATZ_MARKERS = {
    "Input-Parsing": ("Parse input",),
    "Output-Guard": ("<output-guard>", "</output-guard>"),
    "Handoff-Format": ("Handoff",),
    "Anti-Recursion": ("Anti-Recursion",),
}


def test_pflichtsaetze_survive(render_env: RenderEnv):
    """Mandatory content areas present in the golden must survive the render."""
    missing: list[str] = []
    for role in _golden_roles():
        golden = (_GOLDEN_DIR / f"{role}.md").read_text(encoding="utf-8")
        current = render_env.rendered[role]
        for area, markers in _PFLICHTSATZ_MARKERS.items():
            for marker in markers:
                if marker in golden and marker not in current:
                    missing.append(f"{role}: {area} marker {marker!r} lost")
    assert not missing, "\n".join(missing)


# ---------------------------------------------------------------------------
# 5 — structural check for migrated-but-inactive templates
# ---------------------------------------------------------------------------


def _render_template(path: Path, variables: dict) -> str:
    log = SyncLog()
    rendered = substitute(path.read_text(encoding="utf-8"), variables, str(path), log)
    return strip_inactive_conditional_blocks(rendered, variables)


def test_migrated_templates_have_no_inline_variant_regions(render_env: RenderEnv):
    """(a) No inline variant region of any of the four block kinds remains."""
    leftovers: list[str] = []
    for rel in sorted(_MIGRATED):
        path = _REPO_ROOT / rel
        text = path.read_text(encoding="utf-8")
        for kind, locator in _LOCATORS.items():
            for region in locator(text):
                leftovers.append(
                    f"{rel}: {kind} inline region still present:\n{region.text[:200]}"
                )
    assert not leftovers, "\n\n".join(leftovers)


def test_migrated_templates_render_canonical_blocks(render_env: RenderEnv):
    """(b)+(c) Canonical block text and mandatory markers appear after render."""
    problems: list[str] = []
    for rel in sorted(_MIGRATED):
        path = _REPO_ROOT / rel
        rendered = _render_template(path, render_env.variables)
        ar_text = _canonical(render_env.variables, "ANTI_RECURSION")
        if ar_text not in rendered:
            problems.append(f"{rel}: canonical ANTI_RECURSION_BLOCK missing")
        if "{{ANTI_RECURSION_BLOCK}}" in rendered:
            problems.append(f"{rel}: ANTI_RECURSION placeholder left unsubstituted")
        if rel in _OUTPUT_GUARD_MIGRATED:
            og_text = _canonical(render_env.variables, "OUTPUT_GUARD")
            if og_text not in rendered:
                problems.append(f"{rel}: canonical OUTPUT_GUARD_BLOCK missing")
            if "{{OUTPUT_GUARD_BLOCK}}" in rendered:
                problems.append(f"{rel}: OUTPUT_GUARD placeholder left unsubstituted")
    assert not problems, "\n".join(problems)


def test_migration_registries_are_consistent():
    """Registry guardrails for the shared-gate convention."""
    assert _OUTPUT_GUARD_MIGRATED <= _MIGRATED, (
        "_OUTPUT_GUARD_MIGRATED must be a subset of _MIGRATED"
    )
    seeds = [v.id for v in _NORMALIZATIONS]
    assert len(seeds) == len(set(seeds)), "duplicate variant ids in the table"
    keys = [(v.kind, v.inline) for v in _NORMALIZATIONS]
    assert len(keys) == len(set(keys)), "duplicate (kind, inline) table entries"
    for variant in _NORMALIZATIONS:
        assert variant.kind in _KIND_CANONICAL_VAR, variant
        assert variant.classification in {"B2a", "B2b"}, variant
