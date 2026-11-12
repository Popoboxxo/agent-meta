import re
from pathlib import Path

SMOKE = Path(__file__).parent / "test_cli_smoke_multi_provider.py"


def test_smoke_module_uses_central_slow_timeout():
    src = SMOKE.read_text(encoding="utf-8")
    assert "from tests.timeouts import SLOW_TIMEOUT" in src
    assert "timeout=SLOW_TIMEOUT" in src


def test_smoke_module_has_no_hardcoded_timeout_literal():
    src = SMOKE.read_text(encoding="utf-8")
    assert re.search(r"timeout\s*=\s*\d+", src) is None
