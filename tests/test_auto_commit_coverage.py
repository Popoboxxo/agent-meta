"""Every 1-generic template with a write capability (direct|delegate|notify,
issue #767) must reference {{AUTO_COMMIT_BLOCK}}. `git.md` is correctly
excluded: it has no Edit/Write in tools: (it already has full commit
authority via Bash + its own sentinel), and `_reference-agent` is explicitly a
didactic, non-deployable template (its own frontmatter description says "not
intended for production delegation", it has no entry in
config/role-defaults.yaml, and no project ever activates it as a role)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.auto_commit import (
    render_auto_commit_block,
    role_commit_authority,
)

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GENERIC_DIR = _REPO_ROOT / "agents" / "1-generic"
_EXCLUDED = {"_reference-agent"}
_WRITE_AUTHORITIES = {"direct", "delegate", "notify"}

_AUTO_CFG = {
    "mode": "auto",
    "triggers": ["task-boundary"],
    "file_count_threshold": 5,
    "secret_scan": True,
}


def _write_capable_template_files():
    for path in sorted(_GENERIC_DIR.glob("*.md")):
        role = path.stem
        if role in _EXCLUDED:
            continue
        authority = role_commit_authority(role, _REPO_ROOT)
        if authority in _WRITE_AUTHORITIES:
            yield role, path, authority


def test_every_write_capable_template_references_the_block():
    missing = [
        str(p.relative_to(_REPO_ROOT))
        for _role, p, _authority in _write_capable_template_files()
        if "{{AUTO_COMMIT_BLOCK}}" not in p.read_text(encoding="utf-8")
    ]
    assert missing == [], f"templates missing the auto_commit block: {missing}"


def test_delegate_and_notify_roles_still_render_when_mode_enabled():
    """AC11: narrowing eligibility to direct-only must not silently drop the
    block for delegate/notify roles when mode != off."""
    roles = list(_write_capable_template_files())
    # Both non-direct classes must actually be exercised by the corpus.
    classes = {authority for _role, _p, authority in roles}
    assert {"direct", "delegate", "notify"} <= classes
    for role, _path, authority in roles:
        block = render_auto_commit_block(_AUTO_CFG, authority)
        assert block, f"{role} ({authority}) rendered an empty block in auto mode"
        assert "Commit authority" in block


def test_git_template_is_not_touched():
    content = (_GENERIC_DIR / "git.md").read_text(encoding="utf-8")
    assert "AUTO_COMMIT_BLOCK" not in content
    assert role_commit_authority("git", _REPO_ROOT) == "none"


def test_reference_agent_is_excluded_but_documented_why():
    assert "not intended for production" in (
        _GENERIC_DIR / "_reference-agent.md"
    ).read_text(encoding="utf-8").lower() or "not intended for production" in (
        _GENERIC_DIR / "_reference-agent.md"
    ).read_text(encoding="utf-8")
