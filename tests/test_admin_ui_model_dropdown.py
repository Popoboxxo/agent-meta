"""Issue #898: role-model dropdown must offer every current Claude alias/tier."""
import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
HTML = (ROOT / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def _model_options():
    m = re.search(r"const modelOptions = \[(.*?)\];", HTML)
    assert m, "modelOptions not found"
    return re.findall(r'"([^"]*)"', m.group(1))


def test_role_model_dropdown_covers_current_claude_tiers_and_aliases():
    claude = yaml.safe_load((ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]["Claude"]
    expected = set(claude["model-tiers"]) | set(claude["model-aliases"])
    assert expected <= set(_model_options()), sorted(expected - set(_model_options()))


def test_ui_has_no_stale_claude_4_literals():
    assert not re.search(r"claude-(haiku|sonnet|opus)-4", HTML)
