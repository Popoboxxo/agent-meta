"""Task 1.25 (IC-15 Nr. 4): Codex dispatch depth and the context hard cap.

Two defects from the provider study (§3.2):

* Codex never gets a ``.codex/config.toml`` with ``[agents] max_depth``, so a
  spawned orchestrator child has no multi-agent tools. ``write_dispatch_depth_config``
  (``scripts/lib/dispatch_depth.py``) closes this, gated purely on the capability
  keys ``agent_config_format`` (``toml``) and ``required_depth``.
* A multi-provider ``AGENTS.md`` can grow past Codex's 32 KiB hard cap
  (``project_doc_max_bytes``, silently truncated by the runtime). The sync must
  abort with ``context.over-hard-cap`` instead of writing over the cap.

Run: python -m pytest tests/test_dispatch_depth_and_hard_cap.py -q
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

CODEX_HARD_CAP_BYTES = 32768
AGENTS_MD_PROVIDERS = ["Gemini", "Opencode", "Mammouth", "Codex", "ZCode", "KimiCode"]


def _make_project(root: Path, providers, description: str = "") -> Path:
    project = root / "project"
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    lines = [
        'agent-meta-version: "2.0.0-beta.1"',
        "ai-providers:",
    ]
    lines += [f"- {p}" for p in providers]
    lines += [
        "dod-preset: rapid-prototyping",
        "variables:",
        "  PROJECT_NAME: matrix",
        "  PROJECT_PREFIX: mx",
    ]
    if description:
        lines.append(f"  PROJECT_DESCRIPTION: {description}")
    (project / ".meta-config" / "project.yaml").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    return project


def _run(project: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--config",
         str(project / ".meta-config" / "project.yaml"), *extra],
        cwd=project, capture_output=True, text=True, timeout=600,
    )


def test_static_context_regeneration_over_cap_aborts(tmp_path):
    """B1 (red-first): ``_regenerate_static_context`` writes a reader-measured
    context file (the static header + preserved managed block) and must honour
    the reader hard cap. Previously only the managed-block write path was
    guarded, so an over-cap static regeneration slipped through unguarded.
    """
    from lib.context import _regenerate_static_context
    from lib.io import SyncError
    from lib.log import SyncLog

    template_dir = tmp_path / "templates" / "context"
    template_dir.mkdir(parents=True)
    template = template_dir / "AGENTS.md"
    template.write_text(
        "# Title\n\n" + "x" * 40_000 + "\n\n"
        "<!-- agent-meta:managed-begin -->\n<!-- agent-meta:managed-end -->\n",
        encoding="utf-8",
    )
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "# old\n\n<!-- agent-meta:managed-begin -->\n<!-- agent-meta:managed-end -->\n",
        encoding="utf-8",
    )

    with pytest.raises(SyncError, match="context.over-hard-cap"):
        _regenerate_static_context(
            tmp_path, target, template, {}, SyncLog(), dry_run=False,
            rel_label="AGENTS.md", source_label="AGENTS.md",
            config={"ai-providers": ["Codex"]},
            provider_config={"Codex": {"context_file": "AGENTS.md"}},
            agent_meta_root=REPO_ROOT,
        )


def test_codex_config_toml_gets_agents_max_depth(tmp_path):
    """Test 1: Codex writes ``.codex/config.toml`` with ``[agents] max_depth``."""
    project = _make_project(tmp_path, ["Codex"])
    result = _run(project, "--init")
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]

    config = project / ".codex" / "config.toml"
    assert config.exists(), "Codex .codex/config.toml was not generated"
    text = config.read_text(encoding="utf-8")
    match = re.search(r"^\s*max_depth\s*=\s*(\d+)\s*$", text, re.MULTILINE)
    assert match, f"[agents] max_depth missing:\n{text}"
    assert int(match.group(1)) >= 2, f"max_depth too low: {text}"
    assert "[agents]" in text


def test_multi_provider_agents_md_over_hard_cap_aborts(tmp_path):
    """Test 2: an over-cap multi-provider AGENTS.md is never written silently.

    The fixture forces the static part of AGENTS.md over Codex's 32 KiB cap, so
    the cap holds for the explicit *and* the compact bootstrap form (the
    fallback path must stay over cap too and therefore re-raise).
    """
    project = _make_project(tmp_path, AGENTS_MD_PROVIDERS, description="x" * 40_000)
    result = _run(project, "--init")
    combined = result.stdout + result.stderr
    assert result.returncode != 0, "sync silently accepted an over-cap AGENTS.md"
    assert "context.over-hard-cap" in combined, combined[-3000:]

    agents_md = project / "AGENTS.md"
    if agents_md.exists():
        assert agents_md.stat().st_size < CODEX_HARD_CAP_BYTES
