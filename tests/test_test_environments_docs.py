"""Documentation contract for the test-environments feature (Task 14).

Locks the German feature guide (AC-ENV-17), the AC-ENV-19 sentence in
``docs/RELEASE_GATES.md``, the commented example block in
``howto/configs/project.yaml.example`` and the CHANGELOG entry for the feature.

Run: ``python3 -m pytest tests/test_test_environments_docs.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.test_environments import collect_test_environment_errors  # noqa: E402


def test_chapter_documents_distinction_protocol_and_limits():  # AC-ENV-17
    t = (REPO_ROOT / "docs/guides/features/test-environments.md").read_text(
        encoding="utf-8"
    )
    for s in (
        "`environments:`",
        "`test-environments:`",
        "token-env",
        "secret: true",
        "APPROVAL_REQUEST",
        "APPROVED",
        "Convention boundary",
        "F6",
        "permissions",
        "dev_instance_url",
        "ha_url",
    ):
        assert s in t, s
    # Issue #1082: documentation examples must be escaped, never raw placeholders.
    assert "{{TEST_ENVIRONMENT" not in t.replace("{{%TEST_ENVIRONMENT_BLOCK%}}", "")


def test_release_gates_sentence():  # AC-ENV-19
    t = (REPO_ROOT / "docs/RELEASE_GATES.md").read_text(encoding="utf-8")
    assert "Dry-Check" in t and "access: read" in t and "test-environments" in t


def test_example_config_block_is_valid():
    raw = (REPO_ROOT / "howto/configs/project.yaml.example").read_text(encoding="utf-8")
    start, end = "# --- test-environments (example) ---", "# --- end test-environments ---"
    body = raw.split(start, 1)[1].split(end, 1)[0]
    cfg = yaml.safe_load(
        "\n".join(
            l[2:] if l.startswith("# ") else l.lstrip("#")
            for l in body.strip().splitlines()
        )
    )
    assert "environments" in cfg and "test-environments" in cfg
    assert collect_test_environment_errors(cfg) == []


def test_changelog_unreleased_mentions_feature():
    t = (REPO_ROOT / "CHANGELOG.md").read_text(encoding="utf-8").split(
        "## [2.0.0-beta.5]", 1
    )[0]
    assert "test-environments" in t
