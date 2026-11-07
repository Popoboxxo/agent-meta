"""Guard: every ``subprocess.*(text=True)`` call in scripts/ pins its codec (#1155 F10).

Without ``encoding=`` text mode decodes with the locale codec (cp1252 on
Windows, ASCII under ``LANG=C``) and a non-ASCII byte in git/gh output
raises ``UnicodeDecodeError``. The convention is
``encoding="utf-8", errors="replace"``.
"""
from __future__ import annotations

import ast
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _offenders() -> list[str]:
    found = []
    for path in sorted(_SCRIPTS.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "subprocess"):
                continue
            kw = {k.arg: k.value for k in node.keywords if k.arg}
            text = kw.get("text") or kw.get("universal_newlines")
            if isinstance(text, ast.Constant) and text.value is True and "encoding" not in kw:
                found.append(f"{path.relative_to(_SCRIPTS.parent)}:{node.lineno}")
    return found


def test_subprocess_text_mode_sets_encoding() -> None:
    assert _offenders() == []
