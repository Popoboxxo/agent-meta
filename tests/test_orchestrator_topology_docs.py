"""Documentation contract for the orchestrator topology (AC-4, P4).

SPEC-orchestrator-topology-2026-11-03 (issue #1077), Task 17/18. The concept doc
``docs/concepts/active/orchestrator-topology.md`` is the single documented home
of the three positions, the provider support/degradation matrix, the ``mode`` x
``topology`` interaction and the P3-only multi-instance contract. The doc must
never over-promise: ``hybrid`` is granted nowhere in v1 and multi-instance is
marked ``P3, designed, not shipped``.

The link check mirrors the ``scripts/lib/consistency/docs.py`` pattern: Markdown
links are extracted with a regex and their targets are resolved against the
containing file's directory; a missing target is a defect, not a warning.

Run: python3 -m pytest tests/test_orchestrator_topology_docs.py -q
"""

from __future__ import annotations

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONCEPT = _REPO_ROOT / "docs" / "concepts" / "active" / "orchestrator-topology.md"
_SINGLETON = (
    _REPO_ROOT / "docs" / "concepts" / "active" / "singleton-orchestrator-architecture.md"
)
_A2A_RULE = _REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md"

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


def test_concept_doc_marks_multi_instance_as_p3_not_shipped():
    content = _text(_CONCEPT)
    lowered = _normalized(content)
    assert "P3, designed, not shipped" in content, (
        "orchestrator-topology.md must mark the multi-instance contract with "
        "the literal 'P3, designed, not shipped' (AC-4: no v1 promise)."
    )
    assert "kein v1-versprechen" in lowered or "nicht teil von v1" in lowered, (
        "orchestrator-topology.md must state that multi-instance is not part "
        "of the v1 contract."
    )
    assert "max-instances" in content, (
        "orchestrator-topology.md must name the P3-only `max-instances` key so "
        "the reader sees what is deliberately absent in v1."
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
