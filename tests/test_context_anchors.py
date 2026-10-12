"""QG-3 / AC-06: anchor registry (config/context-anchors.yaml) is satisfied by the
`full` render of every provider (IC-12).

Renders reuse the provider-matrix harness of tests/test_ac01_render_identity.py.
Run: python -m pytest tests/test_context_anchors.py -q
"""

import sys
from pathlib import Path
from typing import Dict, List

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_ac01_render_identity as matrix  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY = _REPO_ROOT / "config" / "context-anchors.yaml"
_KINDS = ("entry-file", "claude-md", "orchestrator", "rules-native", "gate-card")
_REQUIRED_RULE_ANCHORS = (
    "CRITICAL GATE", "Anti-Recursion", "MCP Hard Prohibitions",
    "Branch-Guard", "Sprachregeln", "Commit-Konventionen",
)
_SKIP = ("/.git/", "/.meta-config/", "/sync.log", "/.tmp/")


def _load_registry() -> dict:
    return yaml.safe_load(_REGISTRY.read_text(encoding="utf-8"))


def _read_all(project: Path, names: List[str]) -> str:
    return "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for n in names for p in sorted(project.glob(n)) if p.is_file()
    )


def _corpora(project: Path) -> Dict[str, str]:
    """Artifact-kind corpora of one rendered provider project (by file layout)."""
    files = [p.relative_to(project).as_posix() for p in project.rglob("*") if p.is_file()]
    files = [f for f in files if not any(s in "/" + f for s in _SKIP)]
    rules = [f for f in files if "/rules/" in "/" + f and f.endswith(".md")
             and not f.endswith("project-context.md")]
    rules += [f for f in files if f.startswith(".github/instructions/")]
    orch = [f for f in files if "/agents/orchestrator." in "/" + f or f.startswith("agents/orchestrator.")]
    entry = [f for f in files if f in ("AGENTS.md", ".github/copilot-instructions.md")
             or f.endswith("rules/project-context.md")]
    return {
        "entry-file": _read_all(project, entry),
        "claude-md": _read_all(project, ["CLAUDE.md"]),
        "orchestrator": _read_all(project, orch),
        "rules-native": _read_all(project, rules),
        "gate-card": "",
    }


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    root = tmp_path_factory.mktemp("anchors")
    return {p: _corpora(matrix._make_project(root, p)) for p in matrix._PROVIDERS}


def test_registry_schema():
    reg = _load_registry()
    assert set(reg["anchors"]) == set(_KINDS)
    for kind in _KINDS:
        assert set(reg["anchors"][kind]) == {"all-profiles", "compact-only"}
        for key in ("all-profiles", "compact-only"):
            assert isinstance(reg["anchors"][kind][key], list)
    for key in ("gate_card_sections", "intentional_unread", "intentional_empty"):
        assert isinstance(reg[key], list)
    assert all("#" in s for s in reg["gate_card_sections"])


def test_mandatory_anchors_registered():
    joined = "\n".join(_load_registry()["anchors"]["rules-native"]["all-profiles"])
    orch = "\n".join(_load_registry()["anchors"]["orchestrator"]["all-profiles"])
    for needle in _REQUIRED_RULE_ANCHORS:
        assert needle in joined, f"mandatory anchor missing: {needle}"
    for needle in ("Singleton", "STATUS", "RESULT", "ARTIFACTS"):
        assert needle in orch, f"mandatory orchestrator anchor missing: {needle}"


@pytest.mark.parametrize("provider", matrix._PROVIDERS)
def test_full_render_contains_all_anchors(rendered, provider):
    reg = _load_registry()["anchors"]
    corpora = rendered[provider]
    # Providers without a native rules dir inline the rules into the entry file.
    fallback = corpora["entry-file"]
    missing = []
    for kind in _KINDS:
        for anchor in reg[kind]["all-profiles"]:
            haystack = corpora[kind]
            if kind == "rules-native" and not haystack.strip():
                haystack = fallback
            elif kind == "rules-native":
                haystack = haystack + "\n" + fallback
            if kind == "claude-md" and not corpora["claude-md"].strip():
                continue  # provider has no CLAUDE.md
            if anchor not in haystack:
                missing.append(f"{kind}: {anchor!r}")
    assert not missing, f"{provider}: anchors missing in full render:\n" + "\n".join(missing)


def test_claude_md_rendered_for_claude(rendered):
    assert rendered["Claude"]["claude-md"].strip(), "Claude must render CLAUDE.md"
