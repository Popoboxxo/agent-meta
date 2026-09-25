"""B3 snippet copy contract + inlining-path transform.

Spec: ``docs/specs/2026-09-19-dynamic-routing-template-slimming.md`` §1.7 / §3.7
and AC **B3**. The manifest that documents the B2b normalizations lives in
``docs/plans/2026-09-19-dynamic-routing-template-slimming-diff-manifest.md``.

Two *independent* snippet mechanisms are pinned here, both against the real
production functions (never against duplicated literals):

1. **Inlining path** (``*_BLOCK``): ``scripts/lib/config.py``
   ``_build_snippet_variables`` loads ``snippets/agents/*.md`` through
   ``_load_block_snippet``. The canonical transform (SPEC §3.7 / O-D) strips a
   leading YAML frontmatter block, normalises line endings to ``\\n`` and
   reduces the result with ``strip("\\n")``.
2. **Copy path** (``*_SNIPPETS_PATH``): ``scripts/lib/context.py``
   ``sync_snippets_for_provider`` copies exactly the referenced snippet files
   as UTF-8 text into the target project (``context.py:2183-2250``). Its
   ``read_text()`` call applies universal-newline decoding (CRLF/CR → ``\\n``)
   before ``write_text()``; frontmatter is retained. This is a text contract,
   not a raw-byte preservation guarantee.

The copy path is synthesised with explicit references because this repository's
own config references no ``*_SNIPPETS_PATH`` snippet (both values are empty in
``.meta-config/project.yaml``); one test also verifies that derivation against
the real config.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.config import (
    _build_snippet_variables,
    _load_block_snippet,
    load_config,
)
from scripts.lib.context import sync_snippets_for_provider
from scripts.lib.log import SyncLog
from scripts.lib.providers import load_providers_config

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BLOCK_SNIPPETS_DIR = _REPO_ROOT / "snippets" / "agents"
_PROVIDER = "Claude"
_PROJECT_CONFIG = _REPO_ROOT / ".meta-config" / "project.yaml"

#: Inlining-path block variables → their real ``snippets/agents/`` source file.
_BLOCK_SNIPPET_FILES = {
    "OUTPUT_GUARD_BLOCK": "output-guard.md",
    "BACKGROUND_PROCESS_GUARD_BLOCK": "background-process-guard.md",
    "PARSE_INPUT_BLOCK": "parse-input.md",
}

#: The two copy-path snippets the synthetic fixture references, keyed by the
#: config variable that carries them. ``_SNIPPETS_PATH`` is the contract key.
_REFERENCED = {
    "TESTER_SNIPPETS_PATH": "tester/sample-tester.md",
    "DEVELOPER_SNIPPETS_PATH": "developer/sample-developer.md",
}
_EXPECTED_COPIED = frozenset(_REFERENCED.values())

_PROVIDER_CONFIG = {"Claude": {"snippets_dir": ".claude/snippets"}}


def _write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _synth_agent_meta_root(root: Path) -> Path:
    """Minimal agent-meta root with referenced and unreferenced snippets."""
    _write(
        root,
        "snippets/tester/sample-tester.md",
        '---\nsnippet: sample-tester\nversion: "1.0.0"\n---\n\ntester body\n',
    )
    _write(
        root,
        "snippets/developer/sample-developer.md",
        '---\nsnippet: sample-developer\nversion: "1.0.0"\n---\n\ndeveloper body\n',
    )
    # A block-snippet file (inlining path) and a stray copy-path snippet: both
    # are unreferenced here and must never be copied.
    _write(
        root,
        "snippets/agents/parse-input.md",
        '---\nsnippet: parse-input\nversion: "1.0.0"\n---\n\n## 1. Parse input\nA2A body\n',
    )
    _write(root, "snippets/orchestrator/stray.md", "stray\n")
    return root


def _copy_config() -> dict:
    """Config whose ``*_SNIPPETS_PATH`` keys select exactly ``_REFERENCED``."""
    variables = {"SNIPPETS_DIR": "snippets"}
    variables.update(_REFERENCED)
    # An empty ``*_SNIPPETS_PATH`` value and a key that merely *contains* the
    # marker must both be ignored by the copy-path selector.
    variables["LEGACY_SNIPPETS_PATH"] = ""
    variables["COPY_SNIPPETS_SOURCE"] = "orchestrator/stray.md"
    return {"variables": variables}


def _copied(root: Path) -> dict[str, str]:
    """Repo-relative path → content for every copied snippet under *root*."""
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*.md"))
    }


def _run_copy(agent_meta_root: Path, project_root: Path, config: dict, dry_run: bool = False):
    sync_snippets_for_provider(
        agent_meta_root,
        project_root,
        config,
        SyncLog(),
        dry_run,
        _PROVIDER,
        _PROVIDER_CONFIG,
    )
    return project_root / ".claude" / "snippets"


# ---------------------------------------------------------------------------
# (a) exactly the referenced snippets are copied
# ---------------------------------------------------------------------------


def test_copy_path_copies_exactly_referenced_snippets(tmp_path):
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    target_root = _run_copy(am_root, tmp_path / "project", _copy_config())

    assert set(_copied(target_root)) == _EXPECTED_COPIED
    # The unreferenced block snippet and the stray snippet are absent.
    assert "agents/parse-input.md" not in _copied(target_root)
    assert "orchestrator/stray.md" not in _copied(target_root)


def test_copy_path_ignores_empty_and_non_marker_variables(tmp_path):
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    config = _copy_config()
    assert config["variables"]["LEGACY_SNIPPETS_PATH"] == ""
    assert config["variables"]["COPY_SNIPPETS_SOURCE"] == "orchestrator/stray.md"

    target_root = _run_copy(am_root, tmp_path / "project", config)
    # Only the two truthy ``*_SNIPPETS_PATH`` values were copied.
    assert set(_copied(target_root)) == _EXPECTED_COPIED


def test_copy_path_preserves_utf8_text_and_frontmatter(tmp_path):
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    target_root = _run_copy(am_root, tmp_path / "project", _copy_config())

    for rel in _EXPECTED_COPIED:
        source = (am_root / "snippets" / rel).read_text(encoding="utf-8")
        copied = (target_root / rel).read_text(encoding="utf-8")
        assert copied == source, rel
        # Copy-path snippets keep their YAML frontmatter (SPEC §3.7 rule).
        assert copied.startswith("---")
        assert "snippet:" in copied


def test_copy_path_normalizes_crlf_to_lf(tmp_path):
    """The copy path applies universal-newline decoding before writing."""
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    source = am_root / "snippets/tester/sample-tester.md"
    source.write_bytes(
        b'---\r\nsnippet: sample-tester\r\nversion: "1.0.0"\r\n---\r\n\r\ntester body\r\n'
    )

    target_root = _run_copy(am_root, tmp_path / "project", _copy_config())
    copied_path = target_root / "tester/sample-tester.md"
    copied = copied_path.read_text(encoding="utf-8")
    copied_bytes = copied_path.read_bytes()

    assert copied == source.read_text(encoding="utf-8")
    assert copied.startswith("---\n")
    assert "snippet:" in copied
    assert "\r" not in copied
    assert b"\r" not in copied_bytes


def test_copy_path_removes_stale_target_snippets(tmp_path):
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    project_root = tmp_path / "project"
    target_root = project_root / ".claude" / "snippets"
    _write(target_root, "tester/obsolete.md", "old\n")
    _write(target_root, "orchestrator/stray.md", "old\n")

    _run_copy(am_root, project_root, _copy_config())

    assert not (target_root / "tester" / "obsolete.md").exists()
    assert not (target_root / "orchestrator" / "stray.md").exists()
    assert set(_copied(target_root)) == _EXPECTED_COPIED


def test_copy_path_dry_run_writes_nothing(tmp_path):
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    project_root = tmp_path / "project"
    _run_copy(am_root, project_root, _copy_config(), dry_run=True)

    assert not (project_root / ".claude" / "snippets").exists()


def test_copy_path_is_deterministic(tmp_path):
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    first = _run_copy(am_root, tmp_path / "project-a", _copy_config())
    second = _run_copy(am_root, tmp_path / "project-b", _copy_config())

    assert _copied(first) == _copied(second)
    assert set(_copied(first)) == _EXPECTED_COPIED


def test_copy_path_derives_references_from_real_project_config(tmp_path):
    """The production selector matches the configured ``*_SNIPPETS_PATH`` values."""
    config = load_config(_PROJECT_CONFIG)
    referenced = {
        value
        for key, value in config.get("variables", {}).items()
        if key.endswith("_SNIPPETS_PATH") and value
    }

    project_root = tmp_path / "project"
    target_root = _run_copy(_REPO_ROOT, project_root, config, dry_run=False)

    assert set(_copied(target_root)) == referenced


# ---------------------------------------------------------------------------
# (b) real block inputs remain non-vacuous; transform details live in the shared test
# ---------------------------------------------------------------------------


def test_real_block_snippets_are_non_vacuous_inlining_inputs():
    """Real block files remain frontmatter-bearing inputs to the inlining path."""
    for filename in _BLOCK_SNIPPET_FILES.values():
        raw = (_BLOCK_SNIPPETS_DIR / filename).read_text(encoding="utf-8")
        assert raw.startswith("---"), filename
        assert _load_block_snippet(_BLOCK_SNIPPETS_DIR / filename), filename


def test_copy_path_does_not_apply_the_inlining_transform(tmp_path):
    """A block-snippet file keeps UTF-8 text/frontmatter on the copy path."""
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    config = {"variables": {"REF_SNIPPETS_PATH": "agents/parse-input.md"}}

    target_root = _run_copy(am_root, tmp_path / "project", config)

    copied = (target_root / "agents" / "parse-input.md").read_text(encoding="utf-8")
    source = (am_root / "snippets" / "agents" / "parse-input.md").read_text(encoding="utf-8")
    assert copied == source
    assert copied.startswith("---")
    # ... while the inlining path strips that very frontmatter.
    assert not _load_block_snippet(am_root / "snippets" / "agents" / "parse-input.md").startswith("---")


def test_copy_path_and_inlining_path_are_independent(tmp_path):
    """Copying a block file leaves populated inlining variables unchanged."""
    am_root = _synth_agent_meta_root(tmp_path / "agent-meta")
    before: dict = {}
    _build_snippet_variables(before, _REPO_ROOT)
    for var, filename in _BLOCK_SNIPPET_FILES.items():
        assert before[var] == _load_block_snippet(_BLOCK_SNIPPETS_DIR / filename), var
        assert before[var] == before[var].strip("\n"), var
        assert "snippet:" not in before[var], var

    _run_copy(
        am_root,
        tmp_path / "project",
        {"variables": {"REF_SNIPPETS_PATH": "agents/parse-input.md"}},
    )

    after: dict = {}
    _build_snippet_variables(after, _REPO_ROOT)
    assert before == after
