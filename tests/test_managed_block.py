"""Tests for scripts/lib/managed_block.py (#1268)."""
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from lib.managed_block import ManagedBlockError, render_block, replace_block  # noqa: E402

B = "<!-- agent-meta:managed-begin -->"
E = "<!-- agent-meta:managed-end -->"


def _legacy(existing, new):
    pat = re.compile(r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->", re.DOTALL)
    if pat.search(existing):
        return pat.sub(lambda _m: new, existing, count=1)
    return new + "\n\n" + existing


@pytest.mark.parametrize("text", [
    f"head\n{B}\nold\n{E}\n\n## mine\n",
    f"<!--  agent-meta:managed-begin-->\nold\n<!--agent-meta:managed-end  -->tail",
    f"{B}\na\n{E}\nmid\n{B}\nb\n{E}\n",
    "no block here\n",
])
def test_byte_identical_to_legacy(text):
    new = render_block("agent-meta", "x\\1 \\g<0>")
    assert replace_block(text, new) == _legacy(text, new)


def test_render_block():
    assert render_block("agent-meta", "b") == f"{B}\nb\n{E}"


@pytest.mark.parametrize("text", [f"{B}\nno end\n", f"x\n{E}\n", f"{B}\na\n{E}\n{E}\n"])
def test_broken_marker_raises_and_text_unchanged(text):
    orig = text
    with pytest.raises(ManagedBlockError):
        replace_block(text, "new")
    assert text == orig


def test_no_legacy_block_regex_outside_module():
    root = Path(__file__).resolve().parent.parent / "scripts" / "lib"
    files = ["extensions.py", "context.py", "context_templates/builder.py", "cli_commands.py", "release_scaffold.py"]
    for f in files:
        assert "managed-begin\\s*-->" not in (root / f).read_text(encoding="utf-8"), f


def test_replace_line_block_continue_form():
    from lib.managed_block import replace_line_block
    t = "# b\n# old\n# e\nrest\n"
    assert replace_line_block(t, "# b", "# e", "NEW\\1") == "NEW\\1\nrest\n"
    assert replace_line_block("x\n", "# b", "# e", "N") is None


def test_update_extensions_skips_broken_file_and_continues(tmp_path):
    from lib.extensions import update_extensions
    from lib.log import SyncLog
    ext = tmp_path / ".claude" / "3-project"
    ext.mkdir(parents=True)
    broken = f"{B}\nno end marker\n"
    (ext / "a-ext.md").write_text(broken, encoding="utf-8")
    (ext / "b-ext.md").write_text(f"{B}\nold\n{E}\n", encoding="utf-8")
    update_extensions(tmp_path, {}, SyncLog(), False, Path(__file__).resolve().parent.parent)
    assert (ext / "a-ext.md").read_text(encoding="utf-8") == broken
    assert "old" not in (ext / "b-ext.md").read_text(encoding="utf-8")
