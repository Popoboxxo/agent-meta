"""#1180: rules must not point at undelivered docs; dangling-doc-pointer check."""
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.consistency import context_budget as cb
from lib.consistency import doc_pointers as dp
from lib.consistency.report import Severity

_RE = re.compile(r"`(docs/[^`\s]+\.md)`")
CAPS = {"P": {"context_file": "AGENTS.md"}}


def test_no_unresolvable_relative_doc_pointers():
    hits = []
    for path in (REPO_ROOT / "rules" / "1-generic").rglob("*.md"):
        for doc in _RE.findall(path.read_text(encoding="utf-8")):
            if doc != "docs/REQUIREMENTS.md":
                hits.append((path.name, doc))
    assert hits == []


def test_branch_guard_keeps_section_and_809():
    text = (REPO_ROOT / "rules/1-generic/branch-guard.md").read_text(encoding="utf-8")
    assert "## Bekannte Grenzen" in text and "#809" in text


def test_dangling_doc_pointer_check(tmp_path):
    (tmp_path / "AGENTS.md").write_text("see `docs/nicht-vorhanden.md`\n", encoding="utf-8")
    found = dp.check_dangling_doc_pointer(tmp_path, ["P"], CAPS, None)
    assert len(found) == 1 and found[0].severity is Severity.WARNING
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs/nicht-vorhanden.md").write_text("x", encoding="utf-8")
    assert dp.check_dangling_doc_pointer(tmp_path, ["P"], CAPS, None) == []


def test_severity_registered_and_no_docs_url_variable():
    assert cb.SPEC_SEVERITY["context.dangling-doc-pointer"] is Severity.WARNING
    assert "DOCS_URL" not in (REPO_ROOT / "scripts/lib/variables.py").read_text(encoding="utf-8")


def test_repo_containment_has_no_provider_specific_pointer():
    text = (REPO_ROOT / "rules/1-generic/repo-containment.md").read_text(encoding="utf-8")
    assert ".claude/rules/" not in text


def test_lazy_table_lists_all_se_cascade_skills():
    text = (REPO_ROOT / "rules/1-generic/use-lazy-rules.md").read_text(encoding="utf-8")
    for stem in ("se-cascade-adr-standard", "se-cascade-artifact-taxonomy",
                 "se-cascade-review-lifecycle"):
        assert f"| {stem} |" in text


def test_generic_rules_have_no_provider_specific_pointers():
    # #1180: whole class; branch-guard.md itself is the anchor's home, so skip it.
    hits = []
    for path in (REPO_ROOT / "rules" / "1-generic").rglob("*.md"):
        text = path.read_text(encoding="utf-8")
        if path.name == "branch-guard.md":
            continue
        for pat in (r"\.claude/rules/", r"branch-guard\.md#"):
            if re.search(pat, text):
                hits.append((path.name, pat))
    assert hits == []
