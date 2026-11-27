"""#1255: Extension-Hook stripping is driven by the `extension_hook_path` capability."""
from pathlib import Path

import yaml

from scripts.lib.provider_transform import (
    _strip_extension_hook_lines,
    should_strip_extension_hook,
)

ROOT = Path(__file__).resolve().parent.parent
LINE = "> **Extension:** Falls `.claude/3-project/x-ext.md` existiert -> lesen\n"
BODY = "intro\n" + LINE + "outro\n"


def _providers():
    return yaml.safe_load((ROOT / "config" / "ai-providers.yaml").read_text())["providers"]


def test_only_claude_has_capability():
    caps = {n: e.get("extension_hook_path") for n, e in _providers().items()}
    assert caps["Claude"] == ".claude/3-project/"
    assert [n for n, v in caps.items() if v] == ["Claude"]


def test_claude_keeps_line_others_lose_it():
    for name, entry in _providers().items():
        body = _strip_extension_hook_lines(BODY) if should_strip_extension_hook(entry) else BODY
        assert (LINE in body) == (name == "Claude"), name


def test_opencode_and_flag_provider_strip():
    p = _providers()
    for name in ("Opencode", "Gemini"):
        assert should_strip_extension_hook(p[name])
        assert LINE not in _strip_extension_hook_lines(BODY)


def test_empty_capability_equals_missing():
    assert should_strip_extension_hook({"extension_hook_path": ""})
    assert should_strip_extension_hook(None)


def test_flag_removed_from_config():
    assert "strip-claude-lines" not in (ROOT / "config" / "ai-providers.yaml").read_text()


def test_no_legacy_names_left():
    hits = [
        str(f) for d in ("scripts", "config") for f in (ROOT / d).rglob("*")
        if f.is_file() and f.suffix in (".py", ".yaml")
        and any(n in f.read_text() for n in ("strip-claude-lines", "_strip_claude_specific_lines"))
    ]
    assert hits == []


def test_every_strip_call_is_capability_guarded():
    """All call sites must sit under `if should_strip_extension_hook(...)` or `if strip_ext_hook`."""
    import ast
    for rel in ("scripts/lib/provider_transform.py", "scripts/lib/context.py"):
        tree = ast.parse((ROOT / rel).read_text())
        parents = {c: p for p in ast.walk(tree) for c in ast.iter_child_nodes(p)}
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", "") == "_strip_extension_hook_lines"]
        assert calls, rel
        for call in calls:
            node, guarded = call, False
            while node in parents:
                node = parents[node]
                if isinstance(node, ast.If):
                    src = ast.unparse(node.test)
                    guarded |= "should_strip_extension_hook" in src or src == "strip_ext_hook"
            assert guarded, f"{rel}:{call.lineno} unguarded strip call"
