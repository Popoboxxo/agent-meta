"""Migration-invariant test for the Convention Profiles feature.

The 'default' conventions-preset MUST reproduce the text that was hardcoded in
release.md/git.md before this feature — byte-for-byte. This is a non-negotiable
migration invariant: no project without its own conventions-preset/conventions
config may get a different generated release.md/git.md than before.

Baseline strings below are copied verbatim from the pre-feature release.md
(section '## 2. Versioning' lines 44-49, section '## 3. CHANGELOG.md format'
lines 53-67).
"""

import copy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# --- Baselines: verbatim from the pre-feature release.md ---------------------

EXPECTED_VERSIONING_BLOCK = (
    "| Change | Bump | Example |\n"
    "|--------|------|---------|\n"
    "| Breaking change | MAJOR | Removed commands, incompatible config |\n"
    "| New feature | MINOR | New commands, new settings |\n"
    "| Bugfix / docs | PATCH | Bugfixes, performance, doc fixes |\n"
    "| Alpha/Beta | Suffix | `-alpha.x` / `-beta.x` |"
)

EXPECTED_CHANGELOG_BLOCK = (
    "```markdown\n"
    "## [x.y.z] — YYYY-MM-DD\n"
    "\n"
    "### Added\n"
    "- REQ-xxx: [feature description]\n"
    "\n"
    "### Fixed\n"
    "- REQ-xxx: [bugfix description]\n"
    "\n"
    "### Changed\n"
    "- REQ-xxx: [change]\n"
    "\n"
    "### Removed\n"
    "- [what was removed]\n"
    "```"
)


@pytest.fixture
def base_config():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.config import load_config

    return load_config(REPO_ROOT / ".meta-config" / "project.yaml")


def _build(config):
    from lib.config import build_variables

    variables, _ = build_variables(config, REPO_ROOT)
    return variables


def test_default_versioning_block_is_byte_identical(base_config):
    # agent-meta's own config sets no conventions-preset -> falls back to 'default'.
    config = copy.deepcopy(base_config)
    config.pop("conventions-preset", None)
    variables = _build(config)
    assert variables["RELEASE_VERSIONING_BLOCK"] == EXPECTED_VERSIONING_BLOCK


def test_default_changelog_block_is_byte_identical(base_config):
    config = copy.deepcopy(base_config)
    config.pop("conventions-preset", None)
    variables = _build(config)
    assert variables["RELEASE_CHANGELOG_BLOCK"] == EXPECTED_CHANGELOG_BLOCK


def test_issue_naming_block_absent_when_git_role_inactive(base_config):
    config = copy.deepcopy(base_config)
    config.pop("conventions-preset", None)
    # roles set and git NOT included -> block must not be computed at all.
    config["roles"] = ["release", "documenter"]
    variables = _build(config)
    assert "GIT_ISSUE_NAMING_BLOCK" not in variables
    # release still active -> its blocks are present.
    assert "RELEASE_VERSIONING_BLOCK" in variables


def test_calver_versioning_block_differs_from_default(base_config):
    config = copy.deepcopy(base_config)
    config["conventions-preset"] = "calver"
    variables = _build(config)
    assert variables["RELEASE_VERSIONING_BLOCK"] != EXPECTED_VERSIONING_BLOCK
