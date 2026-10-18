"""QG-3 / AC-06: anchor registry (config/context-anchors.yaml) is satisfied by the
`full` and `compact` render of every provider (IC-12).

Renders reuse the provider-matrix harness of tests/test_ac01_render_identity.py;
the `compact` renders use the first MCP-active fixture
(``tests/fixtures/mcp-active/.meta-config/project.yaml``) so the gate card
carries the MCP deny tokens (AC-24/QG-3). Anchors are literal substrings: a
deliberate wording change must break the test.

``compact`` is opt-in and unverified (IC-36): nothing here claims the profile is
verified, validated or recommended.
Run: python -m pytest tests/test_context_anchors.py -q
"""

import re
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import test_ac01_render_identity as matrix  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY = _REPO_ROOT / "config" / "context-anchors.yaml"
_MCP_ACTIVE_FIXTURE = (
    _REPO_ROOT / "tests" / "fixtures" / "mcp-active" / ".meta-config" / "project.yaml"
)
_KINDS = ("entry-file", "claude-md", "orchestrator", "rules-native", "gate-card")
_REQUIRED_RULE_ANCHORS = (
    "CRITICAL GATE", "Anti-Recursion", "MCP Hard Prohibitions",
    "Branch-Guard", "Sprachregeln", "Commit-Konventionen",
)
# Anchors the `compact` profile must pin per artifact kind (IC-12/QG-3): the
# gate card incl. the MCP deny tokens (IC-06), the one-line agent list in the
# shared AGENTS.md, the orchestrator's on-demand pointers and the Claude
# maintainer notes as an HTML comment (IC-08).
_REQUIRED_COMPACT_ANCHORS = {
    "gate-card": (
        "# CRITICAL GATE",
        "MAIN CHAT darf nicht selbst editieren",
        "## Git Delegation",
        "Anti-Recursion: Worker dürfen nicht an `orchestrator` zurück delegieren.",
        "# Branch-Guard",
        "Keine Code-Änderungen direkt auf `main` oder `master`",
        "# Commit-Konventionen",
        "Verwende Conventional Commits (feat, fix, chore).",
        "# Sprachregeln",
        "## Enforced Gates (aktiv prüfen — HARD REJECT)",
        "Orchestrator-Singleton:",
        "# MCP Hard Prohibitions",
        "`delete_conclusion`, `set_config`",
        "`browser_run_code_unsafe`",
        "`workspace.delete`",
    ),
    "entry-file": (
        "- `orchestrator`:",
        "- `developer`:",
    ),
    "orchestrator": (
        "_wf-orchestrator-reference.md",
        "<pipeline>.md",
    ),
    "claude-md": (
        "<!--\nGeneriert von agent-meta v",
    ),
}
_SKIP = ("/.git/", "/.meta-config/", "/sync.log", "/.tmp/")
_MANAGED_BLOCK_RE = re.compile(
    r"<!--\s*agent-meta:managed-begin\s*-->(.*?)<!--\s*agent-meta:managed-end\s*-->",
    re.DOTALL,
)


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


def _compact_corpora(project: Path) -> Dict[str, str]:
    """Compact-only corpora of one rendered provider project.

    The compact profile's new surface lives in the shared ``AGENTS.md`` managed
    block (IC-06: gate card + one-line agent list), so ``entry-file`` and
    ``gate-card`` are pinned to that block. A provider whose context file is not
    ``AGENTS.md`` renders neither; its corpus stays empty and the compact-only
    check skips it.
    """
    corpora = _corpora(project)
    managed = "\n".join(
        m.group(1)
        for m in _MANAGED_BLOCK_RE.finditer(_read_all(project, ["AGENTS.md"]))
    )
    corpora["entry-file"] = managed
    corpora["gate-card"] = managed
    return corpora


def _make_compact_project(root: Path, provider: str) -> Path:
    """Render one provider with ``context-profile: compact`` and active MCP servers.

    The config is the MCP-active fixture (IC-12/QG-3); the provider membership
    is the only per-provider input, so every provider is rendered on the same
    MCP-active base.
    """
    project = root / provider
    (project / ".meta-config").mkdir(parents=True)
    config = yaml.safe_load(_MCP_ACTIVE_FIXTURE.read_text(encoding="utf-8"))
    config["ai-providers"] = [provider]
    (project / ".meta-config" / "project.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = matrix._run_sync(project, "--init")
    assert result.returncode == 0, (
        f"{provider}: compact sync failed\n"
        f"{result.stdout[-1500:]}\n{result.stderr[-1500:]}"
    )
    return project


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    root = tmp_path_factory.mktemp("anchors")
    return {p: _corpora(matrix._make_project(root, p)) for p in matrix._PROVIDERS}


@pytest.fixture(scope="module")
def compact_rendered(tmp_path_factory) -> Dict[str, Tuple[Dict[str, str], Dict[str, str]]]:
    root = tmp_path_factory.mktemp("anchors-compact")
    out: Dict[str, Tuple[Dict[str, str], Dict[str, str]]] = {}
    for provider in matrix._PROVIDERS:
        project = _make_compact_project(root, provider)
        out[provider] = (_corpora(project), _compact_corpora(project))
    return out


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


def test_compact_only_anchors_registered():
    """The registry pins the mandatory compact-only anchors per kind (IC-12)."""
    reg = _load_registry()["anchors"]
    for kind, needles in _REQUIRED_COMPACT_ANCHORS.items():
        joined = "\n".join(reg[kind]["compact-only"])
        for needle in needles:
            assert needle in joined, f"{kind}: compact-only anchor not pinned: {needle!r}"


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
            if kind == "claude-md" and not corpora["claude-md"].strip():
                continue  # provider has no CLAUDE.md
            if anchor not in haystack:
                missing.append(f"{kind}: {anchor!r}")
    assert not missing, f"{provider}: anchors missing in full render:\n" + "\n".join(missing)


def test_claude_md_rendered_for_claude(rendered):
    assert rendered["Claude"]["claude-md"].strip(), "Claude must render CLAUDE.md"


@pytest.mark.parametrize("provider", matrix._PROVIDERS)
def test_compact_render_keeps_all_profile_anchors(compact_rendered, provider):
    """Every all-profiles anchor survives the compact profile too (IC-12)."""
    reg = _load_registry()["anchors"]
    corpora = compact_rendered[provider][0]
    fallback = corpora["entry-file"]
    missing = []
    for kind in _KINDS:
        haystack = corpora[kind]
        if kind == "rules-native" and not haystack.strip():
            haystack = fallback
        if kind == "claude-md" and not corpora["claude-md"].strip():
            continue  # provider has no CLAUDE.md
        for anchor in reg[kind]["all-profiles"]:
            if anchor not in haystack:
                missing.append(f"{kind}: {anchor!r}")
    assert not missing, f"{provider}: anchors missing in compact render:\n" + "\n".join(missing)


@pytest.mark.parametrize("provider", matrix._PROVIDERS)
def test_compact_render_contains_compact_only_anchors(compact_rendered, provider):
    """The compact-only anchors hold wherever the profile renders that surface."""
    reg = _load_registry()["anchors"]
    corpora = compact_rendered[provider][1]
    missing = []
    for kind in _KINDS:
        haystack = corpora[kind]
        if not haystack.strip():
            continue  # this provider renders no compact surface for the kind
        for anchor in reg[kind]["compact-only"]:
            if anchor not in haystack:
                missing.append(f"{kind}: {anchor!r}")
    assert not missing, f"{provider}: compact-only anchors missing:\n" + "\n".join(missing)

