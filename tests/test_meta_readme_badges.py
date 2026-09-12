"""Static assertions on the agent-meta repo's own README badge block.

The meta repository's README is hand-maintained (there is no `readme:` block
in `.meta-config/project.yaml`), so the badge row is asserted statically here
-- no network access, no renderer. See
docs/concepts/agent-meta-version-badge.md §6/§6.1.
"""

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_README = _REPO_ROOT / "README.md"
_VERSION_FILE = _REPO_ROOT / "VERSION"


def _readme_lines() -> list[str]:
    return _README.read_text(encoding="utf-8").splitlines()


def _repo_version() -> str:
    """Read the repo's own version from the root `VERSION` file at runtime.

    Hard-coding `v1.1.0` here would silently rot on the next version bump and
    would assert the test author's copy rather than the released artifact, so
    the version is always taken from the actual `VERSION` file. If the file is
    absent the badge contracts cannot be checked meaningfully -> skip cleanly.
    """
    if not _VERSION_FILE.is_file():
        pytest.skip(f"VERSION file not found at {_VERSION_FILE}")
    return _VERSION_FILE.read_text(encoding="utf-8").strip()


def test_badge_block_sits_between_h1_and_first_callout():
    """The badge row must sit directly below `# agent-meta` and before the
    first `> [!...]` callout; the first badge is the agent-meta badge."""
    lines = _readme_lines()
    h1_index = lines.index("# agent-meta")
    first_callout = next(i for i, line in enumerate(lines) if line.startswith("> [!"))
    badge_indices = [i for i, line in enumerate(lines) if line.startswith("[![")]

    assert badge_indices, "README must contain at least one badge line"
    assert min(badge_indices) == h1_index + 2, (
        "badge block must start directly after the H1 (one blank line)"
    )
    assert max(badge_indices) < first_callout, (
        "badge block must come before the first [!...] callout"
    )
    assert lines[h1_index + 2].startswith("[![agent-meta "), (
        "the first badge in the block must be the agent-meta badge"
    )


def test_readme_contains_repowise_code_health_badge_and_link():
    content = _README.read_text(encoding="utf-8")
    assert "https://api.repowise.dev/badge/health/popoboxxo/agent-meta.svg" in content
    assert "https://repowise.dev/repo/popoboxxo/agent-meta" in content


def test_readme_contains_agent_meta_badge_with_tag_link():
    version = _repo_version()
    content = _README.read_text(encoding="utf-8")
    agent_meta_badge = (
        f"[![agent-meta v{version}]"
        f"(https://img.shields.io/badge/agent--meta-v{version}-blue.svg)]"
        f"(https://github.com/Popoboxxo/agent-meta/releases/tag/v{version})"
    )
    assert "https://github.com/Popoboxxo/agent-meta/releases/tag/v" in content
    assert agent_meta_badge in content


def test_readme_agent_meta_badge_never_double_escapes_label():
    """The label must be escaped exactly once: the image URL is
    `badge/agent--meta-v<version>-blue.svg`, never `badge/agent----meta`
    (M1/F4/F5)."""
    version = _repo_version()
    content = _README.read_text(encoding="utf-8")
    assert "badge/agent----meta" not in content
    assert f"badge/agent--meta-v{version}-blue.svg" in content


def test_readme_generic_version_badge_fresh_and_no_stale_version():
    """Both the generic version badge and the agent-meta badge must show the
    real `VERSION` (read at runtime, not hard-coded); the old stale
    pre-release value must be gone entirely (D4/Q5)."""
    version = _repo_version()
    content = _README.read_text(encoding="utf-8")
    assert f"version-{version}" in content
    assert f"agent--meta-v{version}" in content
    assert "0.101.0-beta.6" not in content
    assert "0.101.0--beta.6" not in content
