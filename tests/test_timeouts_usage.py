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


def test_smoke_module_init_is_split_per_group_with_explicit_skip():
    src = SMOKE.read_text(encoding="utf-8")
    assert len(re.findall(r"^def project_\w+\(", src, re.M)) >= 3
    assert len(re.findall(r'"--init"', src)) == 1  # single factory, not a shared fixture
    assert "pytest.skip" in src and "TimeoutExpired" in src
