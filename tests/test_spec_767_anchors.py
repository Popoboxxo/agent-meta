import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC = REPO_ROOT / "docs" / "specs" / "767-auto-commit-permission-authority.md"


def test_no_code_line_anchors():
    text = SPEC.read_text(encoding="utf-8")
    assert re.findall(r"[\w/.-]+\.(?:py|sh):\d+", text) == []


def test_symbol_anchors_resolve():
    text = SPEC.read_text(encoding="utf-8")
    refs = re.findall(r"([\w/.-]+\.(?:py|sh))::(\w+)", text)
    assert refs, "spec must use datei::symbol anchors"
    for rel, sym in refs:
        f = REPO_ROOT / rel
        assert f.is_file(), rel
        assert sym in f.read_text(encoding="utf-8"), f"{rel}::{sym}"


def test_is_role_eligible_claim_is_anchored():
    text = SPEC.read_text(encoding="utf-8")
    assert "scripts/lib/auto_commit.py::is_role_eligible" in text
