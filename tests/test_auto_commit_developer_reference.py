"""developer.md must reference the auto_commit block, appended at end of
file (matches the issue #506 output-guard append precedent) -- proof of
concept before the bulk rollout in Task 5."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEVELOPER = _REPO_ROOT / "agents" / "1-generic" / "developer.md"


def test_developer_references_auto_commit_block():
    content = _DEVELOPER.read_text(encoding="utf-8")
    assert "{{#if AUTO_COMMIT_ENABLED}}" in content
    assert "{{AUTO_COMMIT_BLOCK}}" in content
    assert "{{/if}}" in content
    # Appended at/near the end of the file, after the existing
    # <output-guard> block (issue #506 precedent) -- not spliced into the
    # middle of <workflow>/<persona>.
    assert content.rindex("{{#if AUTO_COMMIT_ENABLED}}") > content.rindex("<output-guard>")
