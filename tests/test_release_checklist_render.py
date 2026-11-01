"""Render tests for the ``release-checklist`` template block.

Each test syncs a minimal project into a throw-away directory with the real
``scripts/sync.py`` and reads the generated ``.claude/agents/release.md``.
This observes the rendered artifact (placeholders substituted, conditional
stripped), not an internal intermediate.

Covers AC-REL-1 (``off`` renders byte-identical, no stray blank line),
AC-REL-6/7/8/11/12/21-25 (block text and ordering) and the template versions.
"""

import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]

# Copied from ``tests/test_release_checklist_lib.py`` (Task 2): the content
# contract of the rendered block.
REQUIRED_PHRASES = (
    "CHECKLIST_MODE",
    "CHECKLIST_SUMMARY",
    "not_run",
    "required_failed",
    "APPROVAL_REQUEST",
    "APPROVED:",
    "MODE: check-only",
    "n/a (nicht ausgeführt)",
    "Exit 0 = pass",
    "side-effect free",
    "Step 0",
    "STATUS: failed",
    "dod-met",
    "readme-current",
    "tests-green",
    "changelog-updated",
    "version-bumped",
    "build-created",
    "git-tag-push",
    "| phase |",
)

ITEM_A = {
    "id": "changelog-unreleased",
    "task": "CHANGELOG.md has an [Unreleased] section with this release's entries",
    "verification": "Read the top of CHANGELOG.md",
}
ITEM_B = {
    "id": "schema-valid",
    "task": "The project config validates",
    "verification": "python3 scripts/sync.py --validate",
    "check": "script",
    "script": "python3 scripts/sync.py --validate",
}


def _write_config(project: Path, block, platforms) -> None:
    config = {
        "agent-meta-version": "2.0.0-beta.6",
        "ai-providers": ["Claude"],
        "dod-preset": "rapid-prototyping",
        "platforms": list(platforms),
        "roles": ["orchestrator", "developer", "git", "release"],
        "project": {
            "name": f"release-checklist-{project.name}",
            "prefix": "rcl",
            "short": "release-checklist",
        },
        "variables": {
            "PROJECT_NAME": "release-checklist-fixture",
            "PROJECT_DESCRIPTION": "Render fixture for the release-checklist block.",
            "PROJECT_GOAL": "Observe the rendered release agent.",
            "PROJECT_LANGUAGES": "Python",
            "DOCS_LANGUAGE": "Englisch",
            "GIT_PLATFORM": "GitHub",
            "GIT_REMOTE_URL": "https://github.com/example/release-checklist",
            "GIT_MAIN_BRANCH": "main",
            "TEST_COMMAND": "python3 -m pytest",
            "BUILD_COMMANDS": "python3 scripts/sync.py",
        },
        "rules-preset": "default",
        "speech-mode": "full",
        "tier-preset": "Normal",
        "se-focus": False,
        "max-parallel-agents": 2,
        "conventions-preset": "default",
        "debug-mode": False,
        "allow-committed-secrets": False,
    }
    if block is not None:
        config["release-checklist"] = block
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    (project / ".meta-config" / "project.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _sync(project: Path, block, platforms) -> str:
    """Sync a minimal project and return the rendered ``release.md``."""
    _write_config(project, block, platforms)
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py")],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=900,
    )
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    return (project / ".claude" / "agents" / "release.md").read_text(
        encoding="utf-8"
    )


def test_off_absent_and_empty_are_byte_identical(tmp_path):
    """AC-REL-1: absent, ``mode: off`` and unquoted ``off`` render identically."""
    ref = _sync(tmp_path / "a", None, [])
    assert _sync(tmp_path / "b", {"mode": "off"}, []) == ref
    assert _sync(tmp_path / "c", {"mode": False}, []) == ref
    assert "CHECKLIST_MODE" not in ref
    assert "RELEASE_CHECKLIST" not in ref


def test_null_and_empty_block_render_identical(tmp_path):
    """R1: ``{}`` and ``items: []`` behave like an absent block."""
    ref = _sync(tmp_path / "a", None, [])
    assert _sync(tmp_path / "b", {}, []) == ref
    assert _sync(tmp_path / "c", {"items": []}, []) == ref


def test_advisory_text(tmp_path):
    """AC-REL-6, 11, 21-23: block text, item rows and placement."""
    text = _sync(tmp_path, {"mode": "advisory", "items": [ITEM_A, ITEM_B]}, [])
    for phrase in REQUIRED_PHRASES:
        assert phrase in text, phrase
    assert ITEM_A["id"] in text and ITEM_B["id"] in text
    assert (
        text.index("## 1. Pre-release checklist")
        < text.index("CHECKLIST_MODE")
        < text.index("## 2. Versioning")
    )
    assert "{{" not in text


def test_strict_text(tmp_path):
    """AC-REL-7, 8, 24, 25: strict semantics are prose, not a hook."""
    text = _sync(tmp_path, {"mode": "strict"}, [])
    assert "Prompt-/Konventions-Boundary" in text
    assert "required_failed" in text


def test_gates_step0_text_unchanged(tmp_path):
    """AC-REL-22: Step 0 stays hard in every mode, unchanged wording."""
    text = _sync(tmp_path, {"mode": "strict"}, [])
    assert "Exit code ≠ 0 → abort the release, `STATUS: failed`" in text


def test_hacs_override(tmp_path):
    """AC-REL-12: the hacs override extends the new generic version."""
    text = _sync(tmp_path, {"mode": "advisory"}, ["hacs"])
    assert "HACS Release-Regeln" in text
    assert "CHECKLIST_MODE" in text
    assert 'based-on: "1-generic/release.md@1.13.0"' in (
        REPO_ROOT / "agents/2-platform/hacs-release.md"
    ).read_text(encoding="utf-8")


def test_sharkord_override(tmp_path):
    """AC-REL-12: the sharkord override renders the block before its checklist."""
    adv = _sync(tmp_path / "a", {"mode": "advisory"}, ["sharkord"])
    assert "CHECKLIST_MODE" in adv
    assert adv.index("CHECKLIST_MODE") < adv.index("## Checkliste vor Release")
    assert "CHECKLIST_MODE" not in _sync(tmp_path / "b", {"mode": "off"}, ["sharkord"])
    assert _sync(tmp_path / "c", {"mode": "off"}, ["sharkord"]) == _sync(
        tmp_path / "d", None, ["sharkord"]
    )


def test_template_versions():
    """The three templates carry the planned versions."""

    def ver(path):
        return re.search(
            r'^version: "([^"]+)"',
            (REPO_ROOT / path).read_text(encoding="utf-8"),
            re.M,
        ).group(1)

    assert (
        ver("agents/1-generic/release.md"),
        ver("agents/2-platform/hacs-release.md"),
        ver("agents/2-platform/sharkord-release.md"),
    ) == ("1.13.0", "1.1.1", "1.3.3")
