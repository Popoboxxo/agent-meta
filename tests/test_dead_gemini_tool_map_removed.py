import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))
NAME = "_map_claude_tools_to_gemini_tools"


def test_function_is_gone():
    from lib import provider_transform
    assert not hasattr(provider_transform, NAME)


def test_no_reference_in_code_or_config():
    for base in ("scripts", "config"):
        for p in (REPO_ROOT / base).rglob("*"):
            if p.suffix in (".py", ".yaml", ".yml"):
                assert NAME not in p.read_text(encoding="utf-8"), str(p)
