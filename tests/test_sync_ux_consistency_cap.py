"""#1086 (e)/(f): hard-cap message names shared context file; legacy personal file pin."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.consistency.context_budget import check_over_hard_cap, check_over_soft_cap  # noqa: E402
from lib.context import CLAUDE_LOCAL_FILE, CLAUDE_PERSONAL_LEGACY_FILE, init_claude_personal  # noqa: E402

CAPS = {
    "a": {"context_file": "AGENTS.md", "context_soft_cap_bytes": 10},
    "b": {"context_file": "AGENTS.md"},
    "c": {"context_file": "OTHER.md"},
}
REPORT = {
    "a": {"entry-file": {"bytes": 50, "cap": 20, "cap_kind": "hard-bytes"}},
    "c": {"entry-file": {"bytes": 50, "cap": 20, "cap_kind": "hard-bytes"}},
}


def test_hard_cap_names_shared_provider():
    f = check_over_hard_cap(Path("."), ["a", "b", "c"], CAPS, None, report=REPORT)
    by = {x.message.split(":")[0]: x.message for x in f}
    assert "(shared with: b)" in by["a"]
    assert "shared with" not in by["c"]


def test_soft_cap_variant_unchanged():
    rep = {"a": {"entry-file": {"bytes": 50, "lines": 1, "cap_kind": None}}}
    f = check_over_soft_cap(Path("."), ["a", "b"], CAPS, None, report=rep)
    assert any("(shared with: b)" in x.message for x in f)


class _Log:
    def __init__(self):
        self.warnings, self.skips = [], []

    def warning(self, m): self.warnings.append(m)
    def skip(self, *a): self.skips.append(a)
    def action(self, *a): pass


def test_legacy_personal_file_kept_and_hint_emitted(tmp_path):
    (tmp_path / CLAUDE_PERSONAL_LEGACY_FILE).write_text("notes\n", encoding="utf-8")
    log = _Log()
    init_claude_personal(REPO_ROOT, tmp_path, log, dry_run=False)
    assert (tmp_path / CLAUDE_PERSONAL_LEGACY_FILE).read_text(encoding="utf-8") == "notes\n"
    assert not (tmp_path / CLAUDE_LOCAL_FILE).exists()
    assert log.warnings and CLAUDE_LOCAL_FILE in log.warnings[0]
