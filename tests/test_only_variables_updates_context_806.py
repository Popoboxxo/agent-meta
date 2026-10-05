"""Regression: ``--only-variables`` must propagate a changed variable (issue #806).

The generated context files (CLAUDE.md, AGENTS.md, …) do **not** keep the
``{{VARIABLE}}`` placeholders around — a full sync already substituted every
variable to its literal value. The historic ``only_variables`` implementation
substituted *open* placeholders only, so changing a variable in
``.meta-config/project.yaml`` and running ``--only-variables`` was a no-op: the
old value stayed, the new value appeared nowhere (issue #806).

Contract after the fix:

* the static part (header + template footer) is re-rendered from the provider's
  ``context_template`` with the current variables — so the new value lands and
  the old value is gone;
* the ``agent-meta:managed-begin … managed-end`` block is preserved verbatim
  (refreshing it stays a full-sync job, S3 / AC-18);
* agents are **not** regenerated (0 diffs under ``.claude/agents``);
* the operation is idempotent (a second run reports no actions).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.context import (
    _MANAGED_BLOCK_RE,
    _split_context_file,
    only_variables,
)
from lib.log import SyncLog

_OLD_DESC = "OLDVALUE_DESCRIPTION_806"
_NEW_DESC = "NEWVALUE_DESCRIPTION_806"

_MANAGED_BLOCK = (
    "<!-- agent-meta:managed-begin -->\n"
    "role hints for this project\n"
    "<!-- agent-meta:managed-end -->"
)

_MANAGED_BLOCK_HEADER = "<!-- agent-meta:managed-begin -->"


def _repo_fixtures(description: str):
    """Load this repo's real config/variables with a swappable description."""
    from lib.config import build_variables, load_config
    from lib.providers import load_providers_config

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, REPO_ROOT)
    variables = {**variables, "PROJECT_DESCRIPTION": description}
    provider_config = load_providers_config(REPO_ROOT)
    return config, variables, provider_config


def _seed_context_files(project_root: Path, description: str) -> None:
    """Write realistic generated CLAUDE.md / AGENTS.md with the OLD value.

    The static header is rendered from the real templates (so it contains the
    already-substituted ``description``); a synthetic managed block is appended
    to prove it survives ``--only-variables`` verbatim.
    """
    config, variables, provider_config = _repo_fixtures(description)

    # Render the static header/footer for the two physical context files this
    # repo uses (CLAUDE.md for Claude, AGENTS.md shared by Gemini/Opencode) from
    # the same templates a full sync uses. We do not run a full sync (it would
    # regenerate agents); a template render + crafted managed block is a faithful
    # stand-in for a generated file.
    from lib.context_templates.builder import TemplateBuilder

    _TARGETS = {"Claude": "CLAUDE.md", "Gemini": "AGENTS.md", "Opencode": "AGENTS.md"}
    rendered: dict[str, str] = {}
    for provider, context_file in _TARGETS.items():
        if context_file in rendered:
            continue
        template_name = provider_config.get(provider, {}).get("context_template")
        template_path = REPO_ROOT / template_name if template_name else None
        if template_path is None or not template_path.exists():
            continue
        builder = TemplateBuilder(
            template_path.parent,
            fallback_partials_dir=template_path.parent.parent / "context" / "partials",
        )
        produced = builder.build(template_path.stem, variables)
        header, managed, footer = _split_context_file(produced)
        if managed is None:
            # No managed block in the template render — synthesize header + block.
            rendered[context_file] = header + _MANAGED_BLOCK + "\n" + footer
        else:
            rendered[context_file] = produced

    for context_file, content in rendered.items():
        target = project_root / context_file
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


@pytest.fixture
def seeded_project(tmp_path):
    _seed_context_files(tmp_path, _OLD_DESC)
    return tmp_path


def test_only_variables_updates_value_and_preserves_managed_block(seeded_project):
    """Core #806 contract: new value present, old gone, managed block verbatim."""
    config_new, variables_new, provider_config = _repo_fixtures(_NEW_DESC)
    log = SyncLog()

    before = (seeded_project / "CLAUDE.md").read_text(encoding="utf-8")
    assert _OLD_DESC in before, "fixture must start with the old value"
    managed_before = _MANAGED_BLOCK_RE.search(before).group(0)

    only_variables(
        seeded_project, variables_new, log, dry_run=False,
        providers=["Claude", "Gemini", "Opencode"],
        provider_config=provider_config,
        config=config_new, agent_meta_root=REPO_ROOT,
    )

    for context_file in ("CLAUDE.md", "AGENTS.md"):
        content = (seeded_project / context_file).read_text(encoding="utf-8")
        assert _NEW_DESC in content, f"{context_file}: new value missing"
        assert _OLD_DESC not in content, f"{context_file}: old value still present"
        assert _MANAGED_BLOCK_RE.search(content), f"{context_file}: managed block lost"
    after = (seeded_project / "CLAUDE.md").read_text(encoding="utf-8")
    managed_after = _MANAGED_BLOCK_RE.search(after).group(0)
    assert managed_after == managed_before, "managed block must be preserved verbatim"
    assert _MANAGED_BLOCK_HEADER in after  # first marker survived


def test_only_variables_is_idempotent(seeded_project):
    """A repeated run must not report further variable actions."""
    config_new, variables_new, provider_config = _repo_fixtures(_NEW_DESC)

    log1 = SyncLog()
    only_variables(
        seeded_project, variables_new, log1, dry_run=False,
        providers=["Claude", "Gemini", "Opencode"],
        provider_config=provider_config,
        config=config_new, agent_meta_root=REPO_ROOT,
    )
    log2 = SyncLog()
    only_variables(
        seeded_project, variables_new, log2, dry_run=False,
        providers=["Claude", "Gemini", "Opencode"],
        provider_config=provider_config,
        config=config_new, agent_meta_root=REPO_ROOT,
    )
    writes = [a for a in log2.actions if "variable" in a.lower()]
    assert writes == [], f"second run must be a no-op, got: {writes}"


def test_only_variables_does_not_touch_agents(seeded_project):
    """Acceptance: agent files must not be regenerated (0 agent diffs)."""
    agents_dir = seeded_project / ".claude" / "agents"
    agents_dir.mkdir(parents=True)
    sentinel = agents_dir / "developer.md"
    sentinel.write_text("hand-authored sentinel\n", encoding="utf-8")

    config_new, variables_new, provider_config = _repo_fixtures(_NEW_DESC)
    only_variables(
        seeded_project, variables_new, SyncLog(), dry_run=False,
        providers=["Claude", "Gemini", "Opencode"],
        provider_config=provider_config,
        config=config_new, agent_meta_root=REPO_ROOT,
    )

    assert sentinel.read_text(encoding="utf-8") == "hand-authored sentinel\n"
    assert sorted(p.name for p in agents_dir.iterdir()) == ["developer.md"]


def test_only_variables_cli_end_to_end(tmp_path):
    """The real CLI: change a variable, run ``--only-variables``, observe it."""
    config_dir = tmp_path / ".meta-config"
    config_dir.mkdir(parents=True)
    config_path = config_dir / "project.yaml"

    config_src = (REPO_ROOT / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
    assert _OLD_DESC_ANCHOR in config_src
    config_path.write_text(
        config_src.replace(_OLD_DESC_ANCHOR, _NEW_DESC), encoding="utf-8"
    )

    # Seed the two context files with the OLD value via a template render.
    _seed_context_files(tmp_path, _OLD_DESC)

    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py"),
         "--config", str(config_path), "--only-variables"],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    for context_file in ("CLAUDE.md", "AGENTS.md"):
        content = (tmp_path / context_file).read_text(encoding="utf-8")
        assert _NEW_DESC in content, f"{context_file}: CLI did not write new value"
        assert _OLD_DESC not in content, f"{context_file}: CLI left old value"


# The real config stores PROJECT_DESCRIPTION as a folded scalar; anchor on its
# literal first line to avoid a YAML-formatting dependency.
_OLD_DESC_ANCHOR = (
    "Zentrales Meta-Repository für die Standardisierung und Wiederverwendung"
)
