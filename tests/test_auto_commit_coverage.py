"""Every 1-generic template with Edit/Write in tools: must reference
{{AUTO_COMMIT_BLOCK}} (issue #694) -- except _reference-agent.md, which is
explicitly a didactic, non-deployable template (its own frontmatter
description says "not intended for production delegation", it has no
entry in config/role-defaults.yaml, and no project ever activates it as a
role). git.md is correctly excluded too: it has no Edit/Write in tools:
(it already has full commit authority via Bash + its own sentinel)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.auto_commit import is_role_eligible  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[1]
_GENERIC_DIR = _REPO_ROOT / "agents" / "1-generic"
_EXCLUDED = {"_reference-agent"}


def _eligible_template_files():
    for path in sorted(_GENERIC_DIR.glob("*.md")):
        role = path.stem
        if role in _EXCLUDED:
            continue
        if is_role_eligible(role, _REPO_ROOT):
            yield path


def test_every_eligible_template_references_the_block():
    missing = [
        str(p.relative_to(_REPO_ROOT))
        for p in _eligible_template_files()
        if "{{AUTO_COMMIT_BLOCK}}" not in p.read_text(encoding="utf-8")
    ]
    assert missing == [], f"templates missing the auto_commit block: {missing}"


def test_git_template_is_not_touched():
    content = (_GENERIC_DIR / "git.md").read_text(encoding="utf-8")
    assert "AUTO_COMMIT_BLOCK" not in content


def test_reference_agent_is_excluded_but_documented_why():
    # Confirms the exclusion is deliberate (see docstring), not an
    # oversight -- if this ever starts failing because _reference-agent.md
    # gained a role-defaults.yaml entry, re-evaluate the exclusion.
    assert "not intended for production" in (
        _GENERIC_DIR / "_reference-agent.md"
    ).read_text(encoding="utf-8").lower() or "not intended for production" in (
        _GENERIC_DIR / "_reference-agent.md"
    ).read_text(encoding="utf-8")
