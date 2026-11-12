"""Documentation contract for the orchestrator topology (AC-4, P4).

SPEC-orchestrator-topology-2026-11-03 (issue #1077), Task 17/18. The concept doc
``docs/concepts/active/orchestrator-topology.md`` is the single documented home
of the three positions, the provider support/degradation matrix, the ``mode`` x
``topology`` interaction and the P3-only multi-instance contract. The doc must
never over-promise: ``hybrid`` is granted nowhere in v1, while multi-instance
is shipped as P3 (``max-instances``/``singleton``), with the guard id
remaining audit-only.

The link check mirrors the ``scripts/lib/consistency/docs.py`` pattern: Markdown
links are extracted with a regex and their targets are resolved against the
containing file's directory; a missing target is a defect, not a warning.

Run: python3 -m pytest tests/test_orchestrator_topology_docs.py -q
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONCEPT = _REPO_ROOT / "docs" / "concepts" / "active" / "orchestrator-topology.md"
_SINGLETON = (
    _REPO_ROOT / "docs" / "concepts" / "active" / "singleton-orchestrator-architecture.md"
)
_A2A_RULE = _REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md"

sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.consistency.report import Severity  # noqa: E402
from lib.consistency.topology import check_orchestrator_topology  # noqa: E402
from lib.providers import load_provider_capabilities, runtime_gate_vars  # noqa: E402
from lib.topology import TopologyResolution, resolve_topology  # noqa: E402
from lib.variables import (  # noqa: E402
    _effective_topology_flags,
    _orch_mode_flags,
    _topology_flags,
    strip_inactive_conditional_blocks,
    substitute,
)

# Markdown inline link target, same shape the docs consistency checks use.
_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)\s]+)\)")
_EXTERNAL = ("http://", "https://", "mailto:", "#")


def _normalized(text: str) -> str:
    """Lower-case + drop emphasis markers + collapse whitespace.

    The docs use inline code and bold for key terms, so ``**`` and backticks
    are removed before matching a phrase split across wrapped Markdown lines.
    """
    return " ".join(text.replace("*", "").replace("`", "").split()).lower()


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _dead_links(path: Path) -> list[str]:
    """Links in *path* whose target file does not exist (docs.py pattern)."""
    dead = []
    for target in _LINK_RE.findall(_text(path)):
        if target.startswith(_EXTERNAL):
            continue
        target = target.split("#", 1)[0]
        if not target:
            continue
        candidate = path.parent / target
        if not candidate.is_file():
            dead.append(target)
    return dead


def test_concept_doc_exists():
    assert _CONCEPT.is_file(), (
        "docs/concepts/active/orchestrator-topology.md must exist (AC-4): the "
        "three positions and their degradation rules need a documented home."
    )


def test_concept_doc_names_the_three_topologies():
    lowered = _normalized(_text(_CONCEPT))
    for topology in ("primary", "subagent", "hybrid"):
        assert topology in lowered, (
            f"orchestrator-topology.md must name the '{topology}' position."
        )


def test_concept_doc_states_the_hybrid_deviation():
    """D2: hybrid is either/or, never two simultaneous positions."""
    lowered = _normalized(_text(_CONCEPT))
    assert "hybrid ist entweder/oder" in lowered, (
        "orchestrator-topology.md must carry the D2 deviation sentence: "
        "`hybrid` is either/or, not both at once."
    )
    assert "nicht zwei gleichzeitige positionen" in lowered, (
        "orchestrator-topology.md must reject the 'primary AND spawnable' "
        "reading of `hybrid` explicitly (D2)."
    )


def test_concept_doc_marks_multi_instance_as_p3_shipped():
    content = _text(_CONCEPT)
    lowered = _normalized(content)
    assert "P3, shipped" in content, (
        "orchestrator-topology.md must mark the multi-instance contract as "
        "shipped (P3 delivered, not a design-only promise)."
    )
    assert "n=1 ist byte-identisch" in lowered, (
        "orchestrator-topology.md must state that N=1 stays byte-identical."
    )
    assert "max-instances" in content and "singleton" in content, (
        "orchestrator-topology.md must name the shipped `max-instances` and "
        "`singleton` keys."
    )
    assert "audit-only" in lowered, (
        "orchestrator-topology.md must state that the guard id is audit-only."
    )


def test_concept_doc_carries_the_provider_matrix():
    content = _text(_CONCEPT)
    lowered = _normalized(content)
    for provider in (
        "Claude",
        "Opencode",
        "Gemini",
        "Continue",
        "Copilot",
        "Mammouth",
        "Codex",
        "ZCode",
        "KimiCode",
    ):
        assert provider in content, (
            f"orchestrator-topology.md must list '{provider}' in the support "
            "matrix (config/provider-capabilities.yaml)."
        )
    assert "UNVERIFIED ⇒ no" in content, (
        "orchestrator-topology.md must state the conservative matrix rule "
        "'UNVERIFIED ⇒ no'."
    )
    assert "25" in content and "15" in content, (
        "orchestrator-topology.md must give the measured split 25 data-derived "
        "/ 15 UNVERIFIED => no (40 cells)."
    )
    assert "fail-safe" in lowered and "subagent" in lowered, (
        "orchestrator-topology.md must name the fail-safe target `subagent`."
    )


def test_concept_doc_carries_the_mode_topology_matrix():
    content = _text(_CONCEPT)
    lowered = _normalized(content)
    for mode in ("strict", "advisory", "main-chat"):
        assert mode in lowered, (
            f"orchestrator-topology.md must cover the `{mode}` mode row of the "
            "mode x topology interaction matrix."
        )
    assert "inert" in lowered, (
        "orchestrator-topology.md must state that `main-chat` makes the "
        "topology inert (cross-scope) instead of silently winning."
    )
    assert "error" in lowered, (
        "orchestrator-topology.md must state that same-scope `main-chat` x "
        "topology is a hard ERROR."
    )


def test_concept_doc_links_resolve():
    dead = _dead_links(_CONCEPT)
    assert dead == [], (
        "orchestrator-topology.md has dead links (docs.py link-check pattern): "
        + ", ".join(sorted(dead))
    )


def test_concept_doc_links_spec_and_a2a_rule():
    targets = set(_LINK_RE.findall(_text(_CONCEPT)))
    assert any(t.endswith("2026-11-04-orchestrator-topology-spec.md") for t in targets), (
        "orchestrator-topology.md must link the normative spec."
    )
    assert any(t.endswith("a2a-delegation-gates.md") for t in targets), (
        "orchestrator-topology.md must link the A2A rule it amends."
    )


def test_a2a_rule_states_topology_inline():
    # #1180: the rule carries the core topology limits inline, no doc pointer.
    text = _text(_A2A_RULE)
    assert "docs/concepts" not in text, (
        "rules/1-generic/a2a-delegation-gates.md must not point at docs/concepts "
        "(#1180: core limits are inline)."
    )
    lowered = _normalized(text)
    for phrase in (
        "orchestrator-topologie",
        "g1 ein worker dispatcht nie einen orchestrator",
        "g3 ein orchestrator dispatcht nie einen orchestrator",
        "degradiert laut auf subagent",
    ):
        assert phrase in lowered, f"a2a rule must state inline: {phrase!r}"


def test_singleton_architecture_links_the_topology_doc():
    targets = set(_LINK_RE.findall(_text(_SINGLETON)))
    topology_links = [t for t in targets if t.split("#", 1)[0] == "orchestrator-topology.md"]
    assert topology_links, (
        "singleton-orchestrator-architecture.md must link "
        "orchestrator-topology.md (AC-4 cross-link)."
    )
    assert (_SINGLETON.parent / topology_links[0].split("#", 1)[0]).is_file(), (
        "the singleton concept's topology link must resolve."
    )
    lowered = _normalized(_text(_SINGLETON))
    assert "topologie" in lowered, (
        "singleton-orchestrator-architecture.md must carry a status note that "
        "the singleton statement is topology-conditioned in v1."
    )


# ---------------------------------------------------------------------------
# 24-cell position matrix (issue #1190, Task 15; AC-6/7/8/10/11)
#
# Binding data source: docs/specs/2026-11-09-orchestrator-mode-topology-design.md
# §12.2-§12.5 (four surface tables) and §12.6 (evidence index). The concept doc
# reproduces those tables; the constants below are the same judgments, so a
# silent verdict drift on either side is a test failure.
# ---------------------------------------------------------------------------

_MATRIX_SURFACES = ("v1", "v2", "Claude", "Gemini")
_MATRIX_MODES = ("strict", "advisory", "main-chat")
_MATRIX_TOPOLOGIES = ("primary", "subagent")
_VERDICTS = frozenset({"RECOMMENDED", "ALLOWED", "DEGRADED", "FORBIDDEN"})

# `(surface, mode, topology)` -> first token of the Urteil cell.
EXPECTED_MATRIX: dict[tuple[str, str, str], str] = {
    ("v1", "strict", "primary"): "ALLOWED",
    ("v1", "strict", "subagent"): "RECOMMENDED",
    ("v1", "advisory", "primary"): "ALLOWED",
    ("v1", "advisory", "subagent"): "ALLOWED",
    ("v1", "main-chat", "primary"): "FORBIDDEN",
    ("v1", "main-chat", "subagent"): "ALLOWED",
    ("v2", "strict", "primary"): "ALLOWED",
    ("v2", "strict", "subagent"): "RECOMMENDED",
    ("v2", "advisory", "primary"): "ALLOWED",
    ("v2", "advisory", "subagent"): "ALLOWED",
    ("v2", "main-chat", "primary"): "FORBIDDEN",
    ("v2", "main-chat", "subagent"): "ALLOWED",
    ("Claude", "strict", "primary"): "ALLOWED",
    ("Claude", "strict", "subagent"): "RECOMMENDED",
    ("Claude", "advisory", "primary"): "ALLOWED",
    ("Claude", "advisory", "subagent"): "ALLOWED",
    ("Claude", "main-chat", "primary"): "FORBIDDEN",
    ("Claude", "main-chat", "subagent"): "ALLOWED",
    ("Gemini", "strict", "primary"): "DEGRADED",
    ("Gemini", "strict", "subagent"): "RECOMMENDED",
    ("Gemini", "advisory", "primary"): "DEGRADED",
    ("Gemini", "advisory", "subagent"): "ALLOWED",
    ("Gemini", "main-chat", "primary"): "FORBIDDEN",
    ("Gemini", "main-chat", "subagent"): "ALLOWED",
}

# spec §3.8.2 (lines 228-246): the ten `mode` x `topology` -> position rows.
# The second key component is the documented `topology` cell: `primary`/
# `subagent`/`unset` keep their literal spelling, the two derived `strict` rows
# carry their derivation condition. `"keine Position"` = same-scope
# `main-chat` x `primary` is a validator ERROR; `"POS-3 bzw. POS-2"` = the
# `advisory` x unset cell resolves to either position depending on the
# derivation. Every value is a plain string (one documented position).
EXPECTED_POSITION_MAP: dict[tuple[str, str], str] = {
    ("strict", "ungesetzt (primary-role im ActiveSet)"): "POS-3",
    ("strict", "ungesetzt (keine primary-role)"): "POS-2",
    ("strict", "primary"): "POS-3",
    ("strict", "subagent"): "POS-2",
    ("advisory", "ungesetzt"): "POS-3 bzw. POS-2",
    ("advisory", "primary"): "POS-3",
    ("advisory", "subagent"): "POS-2",
    ("main-chat", "ungesetzt"): "POS-1",
    ("main-chat", "primary"): "keine Position",
    ("main-chat", "subagent"): "POS-1",
}

_SURFACE_HEADING_RE = re.compile(r"^####\s+Surface\s+`([^`]+)`", re.MULTILINE)
_NEXT_HEADING_RE = re.compile(r"^#{1,4}\s", re.MULTILINE)
_POSITION_RE = re.compile(r"POS-[123]")
_FILE_LINE_RE = re.compile(r"[\w./-]+\.(?:py|md|yaml|json|sh):\d+(?:-\d+)?")
_SEPARATOR_RE = re.compile(r":?-{2,}:?")


def _plain(cell: str) -> str:
    """Drop the Markdown emphasis a verdict/position cell may carry."""
    return cell.replace("*", "").replace("`", "").strip()


def _first_token(cell: str) -> str:
    plain = _plain(cell)
    return plain.split()[0] if plain.split() else ""


def _topology_key(cell: str) -> str:
    """Declared topology of a `decl→eff` cell (effective one when unset)."""
    plain = _plain(cell).replace("->", "→")
    declared, _, effective = plain.partition("→")
    declared = declared.strip().lower()
    effective = effective.strip().lower()
    if not declared or "ungesetzt" in declared:
        return effective.split()[0] if effective.split() else ""
    return declared


def _surface_tables() -> dict[str, list[list[str]]]:
    """The four surface tables (heading ``#### Surface <key>``) as raw cells."""
    content = _text(_CONCEPT)
    headings = list(_SURFACE_HEADING_RE.finditer(content))
    tables: dict[str, list[list[str]]] = {}
    for heading in headings:
        next_heading = _NEXT_HEADING_RE.search(content, heading.end())
        end = next_heading.start() if next_heading else len(content)
        rows: list[list[str]] = []
        for line in content[heading.end():end].splitlines():
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
            if all(_SEPARATOR_RE.fullmatch(cell) for cell in cells):
                continue
            if cells[0].lower() == "mode":
                continue
            rows.append(cells)
        tables[heading.group(1)] = rows
    return tables


def _verdict_cells() -> dict[tuple[str, str, str], str]:
    cells = {}
    for surface, rows in _surface_tables().items():
        for row in rows:
            cells[(surface, _plain(row[0]).lower(), _topology_key(row[1]))] = (
                _first_token(row[3])
            )
    return cells


def _resolve_dito(rows: list[list[str]], row_index: int, column: int) -> str | None:
    """Walk upwards to the first non-`dito` cell of the same column."""
    for earlier in range(row_index - 1, -1, -1):
        cell = rows[earlier][column]
        if "dito" not in cell.lower():
            return cell
    return None


def test_matrix_has_24_rows():
    tables = _surface_tables()
    assert set(tables) == set(_MATRIX_SURFACES), (
        "orchestrator-topology.md must carry one `#### Surface `<key>`` block per "
        f"surface {list(_MATRIX_SURFACES)}; found {sorted(tables)}."
    )

    actual: dict[tuple[str, str, str], str] = {}
    positions: dict[tuple[str, str, str], str] = {}
    for surface, rows in tables.items():
        assert len(rows) == 6, (
            f"surface {surface!r}: expected exactly 6 data rows "
            f"(strict/advisory/main-chat x primary/subagent), got {len(rows)}."
        )
        for row in rows:
            assert len(row) == 9, (
                f"surface {surface!r}: expected 9 columns "
                "(mode | topology | Position | Urteil | Gate-Tier | "
                f"Write-Scope-Lock | Recursion | Hop | A2A), got {len(row)}."
            )
            mode = _plain(row[0]).lower()
            topology = _topology_key(row[1])
            assert mode in _MATRIX_MODES, f"surface {surface!r}: bad mode {mode!r}."
            assert topology in _MATRIX_TOPOLOGIES, (
                f"surface {surface!r}: bad topology {topology!r} in {row[1]!r}."
            )
            assert _POSITION_RE.search(row[2]), (
                f"surface {surface!r}, {mode} x {topology}: no POS-1/2/3 in "
                f"the Position cell {row[2]!r}."
            )
            key = (surface, mode, topology)
            assert key not in actual, f"duplicate matrix row {key}."
            actual[key] = _first_token(row[3])
            positions[key] = row[2]

    assert len(actual) == 24, f"expected 24 cells, found {len(actual)}."
    assert actual == EXPECTED_MATRIX, (
        "the documented verdicts drifted from spec §12.2-§12.5; "
        f"diff: { {k: (actual.get(k), v) for k, v in EXPECTED_MATRIX.items() if actual.get(k) != v} }"
    )

    # §3.8.2 cross-check: every non-degraded cell keeps its documented position.
    for (surface, mode, topology), verdict in actual.items():
        if verdict == "DEGRADED":
            continue
        expected_position = EXPECTED_POSITION_MAP.get((mode, topology))
        if expected_position is None or not _POSITION_RE.search(expected_position):
            # `keine Position`: same-scope `main-chat` x `primary` is a validator
            # ERROR, so the cell has no position to compare against.
            continue
        assert expected_position in positions[(surface, mode, topology)], (
            f"{surface}, {mode} x {topology}: expected {expected_position}, "
            f"found {positions[(surface, mode, topology)]!r}."
        )


def test_verdict_vocabulary_is_closed():
    tables = _surface_tables()
    assert tables, "no `#### Surface `<key>`` tables found in the concept doc."
    for surface, rows in tables.items():
        for row_index, row in enumerate(rows):
            assert _first_token(row[3]) in _VERDICTS, (
                f"{surface} row {row_index}: verdict {row[3]!r} does not start "
                f"with one of {sorted(_VERDICTS)}."
            )
            assert _POSITION_RE.search(row[2]), (
                f"{surface} row {row_index}: no POS-1/2/3 in {row[2]!r}."
            )
            for column, cell in enumerate(row):
                if "dito" not in cell.lower():
                    continue
                resolved = _resolve_dito(rows, row_index, column)
                assert resolved is not None, (
                    f"{surface} row {row_index} column {column}: `dito` has no "
                    "earlier cell to resolve to."
                )
                assert _FILE_LINE_RE.search(resolved), (
                    f"{surface} row {row_index} column {column}: `dito` resolves "
                    f"to {resolved!r}, which carries no datei:zeile reference."
                )


def test_exactly_one_recommended_per_surface():
    cells = _verdict_cells()
    recommended = {key for key, verdict in cells.items() if verdict == "RECOMMENDED"}
    assert recommended == {(surface, "strict", "subagent") for surface in _MATRIX_SURFACES}, (
        "exactly one RECOMMENDED cell per surface is allowed (D-OQ1); "
        f"found {sorted(recommended)}."
    )
    for surface in ("v1", "v2"):
        assert cells[(surface, "strict", "primary")] == "ALLOWED", (
            f"{surface}: `strict` x `primary` must stay first-class ALLOWED "
            "(D-OQ2, not downgraded)."
        )
    lowered = _normalized(_text(_CONCEPT))
    assert "nicht empfohlen" not in lowered, (
        "no position may be marked 'nicht empfohlen' (D-OQ2: both Opencode "
        "positions are first-class)."
    )


def test_v2_rows_name_tier_facts_and_recommendation_basis():
    rows = _surface_tables()["v2"]
    by_key = {
        (_plain(row[0]).lower(), _topology_key(row[1])): row
        for row in rows
    }

    recommended = _normalized(" ".join(by_key[("strict", "subagent")]))
    assert "session-/context-ownership" in recommended, (
        "the v2 RECOMMENDED row must name the session/context ownership the "
        "main chat keeps."
    )
    assert "gate-inactive" in recommended and "kein deny" in recommended, (
        "the v2 RECOMMENDED row must state that the gate is inactive and no "
        "deny is written."
    )

    primary = _normalized(" ".join(by_key[("strict", "primary")]))
    assert "observe" in primary, (
        "v2 `strict` x `primary` must name the plugin mode `observe`."
    )
    assert "permissions" in primary and "deny" in primary, (
        "v2 `strict` x `primary` must name the `permissions[]`-deny as the "
        "enforcing instance."
    )
    assert "nicht das plugin" in primary, (
        "v2 `strict` x `primary` must not present the plugin as the enforcing "
        "instance."
    )


def test_cost_section_has_hop_definition_threshold_and_estimate():
    content = _text(_CONCEPT)
    lowered = _normalized(content)
    for expected in ("pos-3 = 0 hop", "pos-2 = 1 hop", "pos-1 = 0 hop"):
        assert expected in lowered, (
            f"the cost section must define `{expected}` (§4, D-Q4)."
        )
    assert "s ≤2 dateien → direkter dispatch" in lowered, (
        "the cost section must carry the S threshold `S ≤2 Dateien → direkter "
        "Dispatch`."
    )
    assert "ESTIMATE" in content, "the cost section must carry an `ESTIMATE`."
    assert re.search(r"\b\d+\s*[–-]\s*\d+k\b", content), (
        "the `ESTIMATE` must state a token range (e.g. `4–8k`)."
    )
    assert "wc -c" in content and "/ 4" in content, (
        "the `ESTIMATE` must name its measurement method (`wc -c … / 4`)."
    )
    assert "nicht gemessen" in lowered, (
        "the `ESTIMATE` must carry the explicit 'nicht gemessen' caveat."
    )


def test_single_user_recommendation_is_strict_subagent_with_primary_option():
    lowered = _normalized(_text(_CONCEPT))
    assert "strict × subagent" in lowered, (
        "the single-user default `strict` x `subagent` must be stated."
    )
    assert "strict × primary" in lowered, (
        "`strict` x `primary` must be documented as an option."
    )
    assert "gleiche governance, kein hop, dafür session-start-bindung" in lowered, (
        "the `strict` x `primary` option must be framed as equal governance "
        "without a hop, at the price of the session-start binding."
    )


def test_gemini_primary_degrades_with_one_warning():
    capabilities = load_provider_capabilities(_REPO_ROOT)
    assert "Gemini" in capabilities, (
        "config/provider-capabilities.yaml must carry the Gemini capability cell."
    )
    active_set = SimpleNamespace(
        roles=frozenset({"orchestrator"}),
        known_roles=frozenset({"orchestrator"}),
    )
    provider_config = {"Gemini": {"primary-role": "orchestrator"}}
    config = {"orchestrator": {"mode": "strict", "topology": "primary"}}

    resolution = resolve_topology(
        config,
        "Gemini",
        provider_config=provider_config,
        capabilities=capabilities["Gemini"],
        mode="strict",
        active_set=active_set,
    )
    assert resolution.effective == "subagent", (
        "Gemini must degrade a declared `primary` to `subagent` "
        f"(effective={resolution.effective!r})."
    )
    assert resolution.degraded_from == "primary"

    findings = check_orchestrator_topology(
        _REPO_ROOT,
        config,
        provider_config=provider_config,
        capabilities=capabilities,
        providers=["Gemini"],
        active_set=active_set,
    )
    degraded = [f for f in findings if f.check == "orchestrator-topology.degraded"]
    assert len(degraded) == 1, (
        "exactly one `orchestrator-topology.degraded` WARNING is expected, "
        f"got {len(degraded)}."
    )
    assert degraded[0].severity == Severity.WARNING


# ---------------------------------------------------------------------------
# Issue #1190, Task 16 (AC-25/AC-28): the eleven documentation findings B-1…B-11
#
# B-1 … B-11 (spec §9.1) are absolute singleton claims that must be
# topology-qualified, a contradictory P3 status, one rendered gate variant and
# two README gaps. B-9 is a render defect (checked against the rule source
# rendered in-process, not against prose); B-5/B-6 were already fixed in T8 and
# are pinned here so
# the template branches cannot regress.
#
# Spec/review/plan files are intentionally excluded: they quote the defect.
# ---------------------------------------------------------------------------

_README = _REPO_ROOT / "README.md"
_CLAUDE_MD = _REPO_ROOT / "CLAUDE.md"
_CODEBASE_OVERVIEW = _REPO_ROOT / "docs" / "CODEBASE_OVERVIEW.md"
_MAIN_CHAT_CONCEPT = (
    _REPO_ROOT / "docs" / "concepts" / "active" / "main-chat-orchestrator-mode.md"
)
_ORCHESTRATOR_TEMPLATE = _REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"
# The RULE SOURCE, not the generated `.claude/rules/` copy: that tree is
# gitignored, so a fresh CI checkout has no rendered rule at all. The test
# renders the source in-process instead (see ``_render_gate_rule``).
_GATE_RULE_SOURCE = _REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md"
_ADR_0002 = _REPO_ROOT / "docs" / "adr" / "0002-orchestrator-mode-topology.md"

#: Machine flags of an enforced (``hook``) provider — the only tier that
#: renders the suffixless ``# CRITICAL GATE`` heading.
_ENFORCED_PC = {"has_hooks": True, "hook_protocol": "claude-code-json"}


def _render_gate_rule() -> str:
    """Render ``rules/1-generic/use-orchestrator.md`` with this repo's flags.

    Mirrors the production substitute-then-strip order (``rules.py::sync_rules``)
    and builds the effective-topology axis from the real T1 seam, exactly like
    ``tests/test_use_orchestrator_topology_rendering.py``. Flags: ``strict``
    mode, an enforced (``hook``) provider tier and this repository's declared
    ``subagent`` position.
    """
    resolution = TopologyResolution(
        declared="subagent",
        effective="subagent",
        source="project",
        derived_from=None,
        degraded_from=None,
        degradation_reason=None,
        verification_state="DOCUMENTED",
    )
    flags = _orch_mode_flags("strict")
    flags.update(runtime_gate_vars(_ENFORCED_PC, {}, {}))
    flags.update(_topology_flags("subagent", explicit=True, source="project"))
    flags.update(_effective_topology_flags(resolution, mode="strict"))

    source = _text(_GATE_RULE_SOURCE)
    rendered = substitute(source, flags, _GATE_RULE_SOURCE.name, None)
    return strip_inactive_conditional_blocks(rendered, flags)

# Normalized (see ``_normalized``) forbidden literals: an absolute singleton
# claim. It is only allowed when a topology qualifier sits in the same block.
_SINGLETON_CLAIM_LITERALS = (
    "nur der main_chat spawnt",
    "nur main_chat darf",
    # B-4 variant: "NUR der `main_chat` darf …" (same absolute claim).
    "nur der main_chat darf",
    "only main_chat may create you",
    "der vom main_chat gespawnte",
    "one per session, spawned by the main chat",
)
# Word boundary on both sides: `subagent_type` is not a topology qualifier.
_SINGLETON_QUALIFIER_RE = re.compile(r"(?<![a-z_])(?:topology|subagent|primary)(?![a-z_])")

# ``(finding, path, anchor, extra required tokens)``. Eleven site entries for
# ten text-carrying findings: B-9 is the generated-render check below and B-10
# pins both the consequence line and the status row that contradicted it.
_B_SITES: tuple[tuple[str, Path, str, tuple[str, ...]], ...] = (
    ("B-1", _CLAUDE_MD, "Singleton-Regel", ("topology",)),
    ("B-2", _README, "flowchart TD", ("orchestrator (primary)", "orchestrator (subagent)")),
    ("B-3", _README, "| `orchestrator.mode` |", ("orchestrator.topology",)),
    ("B-4", _CODEBASE_OVERVIEW, "13.2 Singleton-Regel", ("pos-2", "pos-3")),
    ("B-5", _ORCHESTRATOR_TEMPLATE, "**Singleton", ()),
    ("B-6", _A2A_RULE, "G2 Unter", ()),
    ("B-7", _CONCEPT, "Der Vertrag ist implementiert und validiert", ()),
    ("B-8", _SINGLETON, "Status-Hinweis (2026-11-04)", ("p3, shipped",)),
    ("B-10", _MAIN_CHAT_CONCEPT, "Singleton-Guard-Hook", ("offenes follow-up", "pos-1")),
    (
        "B-10",
        _MAIN_CHAT_CONCEPT,
        "Hook-Deaktivierung bleibt offenes Follow-up",
        ("offenes follow-up",),
    ),
    ("B-11", _CONCEPT, "Main Chat spawnt, strikte Gates", ("topology",)),
)


def _block_at(path: Path, anchor: str) -> str:
    """The blank-line-delimited Markdown block containing *anchor*.

    A heading-only block is expanded to the following block, so an anchor on a
    heading also covers the paragraph/table/blockquote it introduces.
    """
    lines = _text(path).splitlines()
    for index, line in enumerate(lines):
        if anchor not in line:
            continue
        start = index
        while start > 0 and lines[start - 1].strip():
            start -= 1
        end = index
        while end + 1 < len(lines) and lines[end + 1].strip():
            end += 1
        if lines[start].lstrip().startswith("#") and start == end:
            cursor = end + 1
            while cursor < len(lines) and not lines[cursor].strip():
                cursor += 1
            end = cursor
            while end + 1 < len(lines) and lines[end + 1].strip():
                end += 1
            start = cursor
        return "\n".join(lines[start:end + 1])
    raise AssertionError(f"anchor {anchor!r} not found in {path}")


def _fenced_blocks(content: str, language: str) -> list[str]:
    return re.findall(
        rf"^```{language}\s*$(.*?)^```\s*$", content, re.MULTILINE | re.DOTALL
    )


def test_no_absolute_singleton_claim_without_topology_qualifier():
    """AC-25 / RVW2-1190-13: no absolute singleton claim survives.

    The eleven B sites of spec §9.1 are pinned; a forbidden literal may only
    appear when ``topology``/``subagent``/``primary`` is in the same block.
    """
    assert len(_B_SITES) == 11, "expected exactly the eleven B sites."
    violations = []
    for finding, path, anchor, _extra in _B_SITES:
        block = _normalized(_block_at(path, anchor))
        for literal in _SINGLETON_CLAIM_LITERALS:
            if literal in block and not _SINGLETON_QUALIFIER_RE.search(block):
                violations.append(f"{finding} {path.relative_to(_REPO_ROOT)}: {literal!r}")
    assert violations == [], (
        "absolute singleton claim without a topology qualifier in the same "
        "block (B-1…B-11): " + "; ".join(violations)
    )

    for finding, path, anchor, extra in _B_SITES:
        block = _normalized(_block_at(path, anchor))
        for token in extra:
            assert token in block, (
                f"{finding}: {path.relative_to(_REPO_ROOT)} block at {anchor!r} "
                f"must state {token!r}."
            )

    # B-11: the declared-only interaction matrix carries the derived case.
    concept = _normalized(_text(_CONCEPT))
    assert "orchestrator-topology.main-chat-derived-primary" in concept, (
        "B-11: the mode x topology matrix must name the derived-topology WARN "
        "`orchestrator-topology.main-chat-derived-primary`."
    )
    assert "primary-role" in concept, (
        "B-11: the derived row must name `providers.<P>.primary-role` as the "
        "derivation source."
    )


def test_p3_status_is_single_valued():
    """B-7/B-8: P3 has exactly one status — shipped."""
    for path in (_CONCEPT, _SINGLETON):
        content = _text(path)
        assert "P3, shipped" in content, (
            f"{path.relative_to(_REPO_ROOT)} must say `P3, shipped`."
        )
        assert "P3, designed, not shipped" not in content, (
            f"{path.relative_to(_REPO_ROOT)} still carries the superseded "
            "`P3, designed, not shipped` marker."
        )
    concept = _text(_CONCEPT)
    assert "überholt" in _normalized(concept), (
        "orchestrator-topology.md must mark the predecessor spec line as "
        "superseded (`überholt`) instead of editing it."
    )
    assert "2026-11-04-orchestrator-topology-spec.md" in concept and ":791-792" in concept, (
        "orchestrator-topology.md must cite the superseded predecessor spec "
        "line `docs/specs/2026-11-04-orchestrator-topology-spec.md:791-792`."
    )


_GATE_HEADER_RE = re.compile(r"^# CRITICAL GATE(?: \(([^)]+)\))?\s*$", re.MULTILINE)
_GATE_VARIANT_MARKERS = (
    "runtime-partially enforced",
    "ACHTUNG: Auf diesem Provider ist der Gate rein prompt-basiert",
    "Dieser geteilte Kontext wird von mehreren Providern gelesen",
)


def test_gate_render_is_single_variant_per_file():
    """B-9: a rendered rule carries exactly one gate variant.

    Rendered in-process from ``rules/1-generic/use-orchestrator.md`` — the
    generated ``.claude/rules/`` tree is gitignored and absent in CI.
    """
    content = _render_gate_rule()
    headers = _GATE_HEADER_RE.findall(content)
    assert len(headers) == 1, (
        "the rendered `rules/1-generic/use-orchestrator.md` must carry exactly "
        f"one `# CRITICAL GATE` header, found {len(headers)}: {headers!r}."
    )
    if headers[0] == "":
        for marker in _GATE_VARIANT_MARKERS:
            assert marker not in content, (
                "a suffixless `# CRITICAL GATE` must not be combined with a "
                f"tier-suffixed gate paragraph ({marker!r}) in the same file."
            )


def test_readme_lists_the_topology_key():
    """B-2/B-3: the key table and the Mermaid graph name the topology."""
    content = _text(_README)
    key_rows = [line for line in content.splitlines() if line.startswith("| `orchestrator.")]
    assert any("`orchestrator.mode`" in row for row in key_rows), (
        "README key table lost the `orchestrator.mode` row."
    )
    assert any("`orchestrator.topology`" in row for row in key_rows), (
        "README key table must name `orchestrator.topology` (B-3)."
    )

    mermaid = _normalized(
        "\n".join(
            block
            for block in _fenced_blocks(content, "mermaid")
            if "orchestrator.mode" in block
        )
    )
    assert "orchestrator (primary)" in mermaid and "entry" in mermaid, (
        "B-2: the Mermaid block needs an `orchestrator (primary)` node marked "
        "as the session entry point."
    )
    assert "orchestrator (subagent)" in mermaid and "spawned" in mermaid, (
        "B-2: the Mermaid block needs an `orchestrator (subagent)` node marked "
        "as spawned by the main chat."
    )
    assert "one per session, spawned by the main chat" not in mermaid, (
        "B-2: the absolute `one per session, spawned by the main chat` node "
        "must be gone."
    )


def _adr_decision_chunk(content: str, decision_id: str) -> str:
    """Text of one `### <decision_id>` section, up to the next heading."""
    heading = re.search(rf"^###\s+{re.escape(decision_id)}\b.*?$", content, re.MULTILINE)
    assert heading, f"ADR must carry a `### {decision_id}` decision section."
    rest = content[heading.end():]
    following = re.search(r"^#{2,3}\s", rest, re.MULTILINE)
    return rest[: following.start()] if following else rest


def test_adr_records_dq1_to_dq5():
    """AC-28: the five design decisions live in ADR 0002 with consequences."""
    assert _ADR_0002.is_file(), (
        "docs/adr/0002-orchestrator-mode-topology.md must exist (AC-28)."
    )
    content = _text(_ADR_0002)
    for expected in (
        "Status: Accepted",
        "2026-11-09",
        "#1190",
        "2026-11-09-orchestrator-mode-topology-design.md",
    ):
        assert expected in content, f"ADR 0002 must carry {expected!r}."
    for index in range(1, 6):
        chunk = _normalized(_adr_decision_chunk(content, f"D-Q{index}"))
        assert "konsequenz" in chunk, (
            f"ADR 0002: D-Q{index} needs an explicit consequence."
        )


def test_adr_records_doq1_to_doq3():
    """AC-28: the three user decisions carry the 2026-11-09 date + consequence."""
    content = _text(_ADR_0002)
    chunks = {}
    for index in (1, 2, 3):
        decision = f"D-OQ{index}"
        chunks[index] = _normalized(_adr_decision_chunk(content, decision))
        assert "2026-11-09" in chunks[index], (
            f"ADR 0002: {decision} must carry the decision date 2026-11-09."
        )
        assert "konsequenz" in chunks[index], (
            f"ADR 0002: {decision} needs an explicit consequence."
        )
    assert "strict × subagent" in chunks[1] and "first-class" in chunks[1], (
        "D-OQ1 must record the default `strict × subagent` and the first-class "
        "status of both Opencode positions."
    )
    assert "gate-tier" in chunks[2], (
        "D-OQ2 must record the gate tier per surface."
    )
    assert "#1182" in chunks[3], (
        "D-OQ3 must record the #1182 precondition for `advisory × subagent`."
    )


# ---------------------------------------------------------------------------
# Issue #1190, Task 18 (AC-32/AC-37): the three-position model and the
# `mode` x `topology` -> position mapping (spec §3.8.1/§3.8.2).
#
# The positions must be defined ONCE, before any matrix uses them: a surface
# table may only cite an ID whose definition the reader has already passed.
# ---------------------------------------------------------------------------

_POSITIONS_HEADING = "## Positionen"
_MAPPING_HEADING = "### Mapping `mode` × `topology` → Position"
_INTERACTION_MATRIX_HEADING = "## `mode` × `topology` — Interaktionsmatrix"
_SURFACE_MATRIX_HEADING = "## Positions-Matrix je Surface"

# The seven attribute fields of spec §3.8.1, in documented order.
_POSITION_ATTR_FIELDS = (
    "wer startet",
    "wer spawnt",
    "rolle emittiert?",
    "default_agent",
    "gate-tier / wirkung",
    "a2a / checkpointing",
    "hops",
)
_ALLOWED_POSITION_VALUES = frozenset(
    {"POS-1", "POS-2", "POS-3", "POS-3 bzw. POS-2", "keine Position"}
)


def _section_text(content: str, heading: str, *, stop_at: str | None = None) -> str:
    """Body of the `heading` section, up to `stop_at` or the next `##` heading."""
    start = content.find(heading)
    assert start >= 0, (
        f"orchestrator-topology.md must carry a `{heading}` section (AC-32)."
    )
    body_start = start + len(heading)
    if stop_at is not None:
        marker = content.find(stop_at, body_start)
        assert marker >= 0, (
            f"`{heading}` must be followed by `{stop_at}` (document order)."
        )
        return content[body_start:marker]
    following = re.search(r"^##\s", content[body_start:], re.MULTILINE)
    end = body_start + following.start() if following else len(content)
    return content[body_start:end]


def _table_rows(region: str) -> list[list[str]]:
    """Markdown table rows of *region* (separator rows dropped, header kept)."""
    rows: list[list[str]] = []
    for line in region.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(_SEPARATOR_RE.fullmatch(cell) for cell in cells):
            continue
        rows.append(cells)
    return rows


def test_position_model_has_three_positions():
    """AC-32: exactly POS-1/POS-2/POS-3 with the seven §3.8.1 attributes."""
    content = _text(_CONCEPT)
    rows = _table_rows(_section_text(content, _POSITIONS_HEADING, stop_at=_MAPPING_HEADING))
    assert rows, f"`{_POSITIONS_HEADING}` must carry the position definition table."
    header = [_normalized(cell) for cell in rows[0]]
    data = rows[1:]
    assert len(data) == 3, (
        "the position table must define exactly three positions "
        f"(POS-1/POS-2/POS-3), got {len(data)}."
    )
    assert len(header) == len(_POSITION_ATTR_FIELDS) + 2, (
        "the position table needs the seven §3.8.1 attribute fields plus the "
        f"`ID` and `Position` columns, got {len(header)}: {header}."
    )
    for field in _POSITION_ATTR_FIELDS:
        assert field in header, (
            f"the position table lost the attribute field {field!r} (§3.8.1)."
        )
    assert header[0] == "id" and header[1] == "position", (
        "the position table's first two columns must be `ID` and `Position`, "
        f"got {header[:2]}."
    )
    ids = [_plain(row[0]) for row in data]
    assert ids == ["POS-1", "POS-2", "POS-3"], (
        f"the position table must list POS-1, POS-2, POS-3 in order, got {ids}."
    )
    for row in data:
        assert len(row) == len(header), (
            f"position row {row[0]!r}: expected {len(header)} cells, got {len(row)}."
        )
        assert all(cell.strip() for cell in row), (
            f"position row {row[0]!r} has an empty cell."
        )
    assert "POS-4" not in content and "POS-0" not in content, (
        "there is no fourth position: only POS-1/POS-2/POS-3 exist (AC-32)."
    )


def test_position_mapping_has_ten_rows_without_empty_cells():
    """AC-32: ten `mode` x `topology` rows, every cell non-empty."""
    content = _text(_CONCEPT)
    rows = _table_rows(
        _section_text(content, _MAPPING_HEADING, stop_at=_INTERACTION_MATRIX_HEADING)
    )
    assert rows, f"`{_MAPPING_HEADING}` must carry the mapping table."
    header = rows[0]
    data = rows[1:]
    assert len(data) == 10, (
        "the mapping table must carry exactly ten `mode` x `topology` rows "
        f"(spec §3.8.2), got {len(data)}."
    )
    actual: dict[tuple[str, str], str] = {}
    for row in data:
        assert len(row) == len(header), (
            f"mapping row {row[:2]!r}: expected {len(header)} cells, got {len(row)}."
        )
        assert all(cell.strip() for cell in row), (
            f"mapping row {row[:2]!r} has an empty cell (AC-32)."
        )
        key = (_plain(row[0]).lower(), _plain(row[1]))
        assert key not in actual, f"duplicate mapping row {key}."
        position = _plain(row[3])
        assert position in _ALLOWED_POSITION_VALUES, (
            f"mapping row {key}: position cell {row[3]!r} must be one of "
            f"{sorted(_ALLOWED_POSITION_VALUES)}."
        )
        actual[key] = position
    assert actual == EXPECTED_POSITION_MAP, (
        "the documented mapping drifted from spec §3.8.2; diff: "
        f"{ {k: (actual.get(k), v) for k, v in EXPECTED_POSITION_MAP.items() if actual.get(k) != v} } "
        f"| missing={sorted(set(EXPECTED_POSITION_MAP) - set(actual))} "
        f"| extra={sorted(set(actual) - set(EXPECTED_POSITION_MAP))}"
    )


def test_positions_are_defined_before_they_are_used():
    """AC-32: no matrix cites a POS-ID before `## Positionen` defines it."""
    content = _text(_CONCEPT)
    positions_start = content.find(_POSITIONS_HEADING)
    assert positions_start >= 0, f"`{_POSITIONS_HEADING}` is missing (AC-32)."
    mapping_start = content.find(_MAPPING_HEADING, positions_start)
    assert mapping_start > positions_start, (
        f"`{_MAPPING_HEADING}` must follow `{_POSITIONS_HEADING}`."
    )
    surface_start = content.find(_SURFACE_MATRIX_HEADING, mapping_start)
    assert surface_start > mapping_start, (
        f"`{_SURFACE_MATRIX_HEADING}` must follow `{_MAPPING_HEADING}`."
    )

    early = _POSITION_RE.search(content[:positions_start])
    assert early is None, (
        "a POS-ID is used before `## Positionen` defines it: "
        f"{early.group(0)!r} at offset {early.start()}."
    )

    used: set[str] = set()
    for surface, rows in _surface_tables().items():
        for row in rows:
            used.update(_POSITION_RE.findall(row[2]))
    assert used, "the surface matrices must cite positions (T15)."
    for position in sorted(used):
        first = content.find(position)
        assert positions_start <= first < mapping_start, (
            f"{position} is used in the surface matrix but its first occurrence "
            f"is at offset {first}, outside the `{_POSITIONS_HEADING}` definition "
            f"block ({positions_start}..{mapping_start})."
        )


def test_readme_explains_both_opencode_positions():
    """AC-32: both OpenCode positions are equal, POS-3 is the optional third."""
    content = _text(_README)
    blocks = [_normalized(block) for block in re.split(r"\n\s*\n", content)]

    pos1 = [block for block in blocks if "mode: main-chat" in block and "pos-1" in block]
    assert pos1, (
        "README.md must name `mode: main-chat` as POS-1 (equal OpenCode "
        "position, not the only one)."
    )
    pos2 = [
        block for block in blocks if "topology: subagent" in block and "pos-2" in block
    ]
    assert pos2, (
        "README.md must name `topology: subagent` as POS-2 (equal OpenCode "
        "position, default/recommended)."
    )
    assert any("equal" in block for block in pos1), (
        "README.md must present POS-1 and POS-2 as equal choices, not ranked "
        "against each other (D-OQ2)."
    )
    pos3 = [block for block in blocks if "pos-3" in block and "optional" in block]
    assert pos3, (
        "README.md must present `topology: primary` as POS-3, the optional "
        "third position (0 hops, only when the session starts in the role)."
    )

    mermaid = "\n".join(_fenced_blocks(content, "mermaid"))
    assert "orchestrator (primary)" in mermaid, (
        "B-2: the Mermaid block needs the `orchestrator (primary)` node (POS-3)."
    )
    assert "orchestrator (subagent)" in mermaid, (
        "B-2: the Mermaid block needs the `orchestrator (subagent)` node (POS-2)."
    )


def test_codebase_overview_names_both_positions():
    """AC-32: §13.2 names POS-1 and POS-2 instead of one absolute claim."""
    block = _normalized(_block_at(_CODEBASE_OVERVIEW, "13.2 Singleton-Regel"))
    assert "pos-1" in block, (
        "CODEBASE_OVERVIEW.md §13.2 must name POS-1 (main-chat as orchestrator): "
        "that position emits no orchestrator role at all."
    )
    assert "pos-2" in block, (
        "CODEBASE_OVERVIEW.md §13.2 must name POS-2 (delegated orchestrator)."
    )
    assert "pos-3" in block and "optional" in block, (
        "CODEBASE_OVERVIEW.md §13.2 must name POS-3 as the optional "
        "session-entry position."
    )


def test_advisory_subagent_carries_1182_condition_everywhere():
    """AC-37: every `advisory` x `subagent` recommendation cites #1182."""
    concept = _text(_CONCEPT)
    rows_checked = 0
    for surface, rows in _surface_tables().items():
        for row in rows:
            if (
                _plain(row[0]).lower() != "advisory"
                or _topology_key(row[1]) != "subagent"
            ):
                continue
            rows_checked += 1
            assert "#1182" in " ".join(row), (
                f"{surface}: the `advisory` x `subagent` row recommends a "
                "position that is blocked until #1182 is fixed (D-OQ3)."
            )
    assert rows_checked == len(_MATRIX_SURFACES), (
        "expected one `advisory` x `subagent` recommendation per surface, "
        f"checked {rows_checked}."
    )

    team_blocks = [
        block
        for block in re.split(r"\n\s*\n", concept)
        if "empfehlung (team)" in _normalized(block)
    ]
    assert team_blocks, (
        "the concept doc must carry a team recommendation paragraph."
    )
    for block in team_blocks:
        assert "#1182" in block, (
            "the team recommendation (`advisory` x `subagent`) must name #1182 "
            "in the same paragraph (D-OQ3)."
        )

    readme_sites = [
        block
        for block in re.split(r"\n\s*\n", _text(_README))
        if "advisory" in _normalized(block)
        and "subagent" in _normalized(block)
        and "recommend" in _normalized(block)
    ]
    assert readme_sites, (
        "README.md must state the `advisory` x `subagent` recommendation "
        "(POS-2, team) so its #1182 precondition can be pinned."
    )
    for block in readme_sites:
        assert "#1182" in block, (
            "the README recommendation of `advisory` x `subagent` must name "
            "#1182 in the same paragraph (D-OQ3)."
        )


# --- Task 21: intentional topology goldens (AC-17/AC-26/AC-27/AC-36) ------

_TOPOLOGY_GOLDEN = _REPO_ROOT / "tests" / "fixtures" / "topology-golden"
_PROJECT_SCHEMA = _REPO_ROOT / "config" / "project-config.schema.json"
_SCHEMA_BASELINE_COMMIT = "a41745e"

sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_orchestrator_topology_effective_flags import (  # noqa: E402
    _UNSET,
    _split_frontmatter,
    render_orchestrator,
)

_PRIMARY_MARKER = "**Singleton (session entry):**"
_DECLARED_SUBAGENT_MARKER = "**Singleton (subagent):**"
_LEGACY_MARKER = "**Singleton:** Self-spawn (`subagent_type: orchestrator`)"


def _golden(name: str) -> str:
    path = _TOPOLOGY_GOLDEN / name
    assert path.is_file(), f"missing intentional golden fixture: {path.name}"
    return path.read_text(encoding="utf-8")


def _body_diff(expected: str, actual: str) -> list[str]:
    """Body lines that differ (frontmatter excluded)."""
    import difflib

    _, expected_body = _split_frontmatter(expected)
    _, actual_body = _split_frontmatter(actual)
    return [
        line
        for line in difflib.unified_diff(
            expected_body.splitlines(), actual_body.splitlines(),
            "golden", "render", lineterm="",
        )
        if line[:1] in "+-" and not line.startswith(("+++", "---"))
    ]


def test_derived_primary_render_matches_intentional_golden(tmp_path):
    """AC-17/Rev.3: an unset key + primary role is INTENTIONALLY different.

    Undeclared, the ``primary`` position renders the session-entry singleton
    (never the legacy text); the frozen golden is the AC-17 target state. The
    derived-subagent baseline shares everything except that one line.
    """
    rendered = render_orchestrator(
        "Opencode", tmp_path / "derived-primary",
        topology=_UNSET, active_set=frozenset({"orchestrator"}),
    )
    golden = _golden("orchestrator.derived-primary.opencode.md")
    assert rendered == golden, "\n".join(_body_diff(golden, rendered))

    _, body = _split_frontmatter(rendered)
    assert _PRIMARY_MARKER in body
    assert _LEGACY_MARKER not in body

    # The intentional deviation is exactly the singleton wording, nothing else.
    baseline = _golden("orchestrator.unset-derived-subagent.opencode.md")
    _, baseline_body = _split_frontmatter(baseline)
    assert _LEGACY_MARKER in baseline_body, "baseline lost the legacy branch"

    diff = _body_diff(baseline, rendered)
    assert len(diff) == 2, (
        "derived primary vs baseline must differ by exactly one changed line; "
        f"got: {diff!r}"
    )
    assert _LEGACY_MARKER in diff[0] and diff[0].startswith("-"), diff
    assert _PRIMARY_MARKER in diff[1] and diff[1].startswith("+"), diff


def test_declared_primary_render_matches_new_golden(tmp_path):
    """AC-27: a declared ``primary`` renders the session-entry singleton."""
    rendered = render_orchestrator(
        "Claude", tmp_path / "declared-primary", topology="primary",
    )
    golden = _golden("orchestrator.declared-primary.md")
    assert rendered == golden, "\n".join(_body_diff(golden, rendered))

    _, body = _split_frontmatter(rendered)
    assert _PRIMARY_MARKER in body
    assert _LEGACY_MARKER not in body


def test_declared_subagent_render_matches_new_golden(tmp_path):
    """AC-36: declared ``subagent`` differs from the derived (else) branch.

    Both renders resolve ``effective == subagent``; only the explicit branch
    wording separates them, so the difference is deterministic and exactly one
    line wide.
    """
    declared = render_orchestrator(
        "Claude", tmp_path / "declared-subagent", topology="subagent",
    )
    golden = _golden("orchestrator.declared-subagent.md")
    assert declared == golden, "\n".join(_body_diff(golden, declared))

    derived = render_orchestrator(
        "Claude", tmp_path / "derived-subagent",
        topology=_UNSET, active_set=frozenset(),
    )
    _, declared_body = _split_frontmatter(declared)
    _, derived_body = _split_frontmatter(derived)
    assert declared_body != derived_body, (
        "declared and derived `subagent` render identically — the "
        "ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT conditional is not wired (AC-36)"
    )
    assert _DECLARED_SUBAGENT_MARKER in declared_body
    assert _LEGACY_MARKER in derived_body

    diff = _body_diff(derived, declared)
    assert len(diff) == 2, (
        "declared vs derived `subagent` must differ by exactly one changed "
        f"line (removed + added); got: {diff!r}"
    )


def test_schema_has_no_new_properties():
    """AC-26: the topology gate adds no schema property.

    Property PATHS are frozen from the pre-implementation commit; titles,
    descriptions and enum values may change, the property tree may not.
    """
    import json

    fixture_path = _TOPOLOGY_GOLDEN / "schema-property-paths.json"
    assert fixture_path.is_file(), f"missing schema fixture: {fixture_path.name}"
    baseline = json.loads(fixture_path.read_text(encoding="utf-8"))
    assert baseline["commit"] == _SCHEMA_BASELINE_COMMIT

    def property_paths(node: dict, prefix: str = "") -> set[str]:
        found: set[str] = set()
        if not isinstance(node, dict):
            return found
        for name, child in (node.get("properties") or {}).items():
            path = f"{prefix}.{name}" if prefix else name
            found.add(path)
            found |= property_paths(child, path)
        if isinstance(node.get("items"), dict):
            found |= property_paths(node["items"], f"{prefix}[]")
        return found

    current = json.loads(_PROJECT_SCHEMA.read_text(encoding="utf-8"))
    current_paths = property_paths(current)
    frozen_paths = set(baseline["paths"])

    assert current_paths - frozen_paths == set(), (
        "the implementation added schema properties (AC-26): "
        f"{sorted(current_paths - frozen_paths)}"
    )
    assert frozen_paths - current_paths == set(), (
        "the implementation removed schema properties (AC-26): "
        f"{sorted(frozen_paths - current_paths)}"
    )
