from pathlib import Path

HTML = (Path(__file__).resolve().parent.parent / "docs" / "ui" / "admin-ui.html").read_text(encoding="utf-8")


def _helper():
    start = HTML.index("async function postTierPresetsConfirmingLoss(")
    return HTML[start:HTML.index("\n}\n", start)]


def test_helper_detects_refusal_confirms_and_retries_with_flag():
    h = _helper()
    assert "refusing lossy YAML save" in h
    assert "confirm(" in h
    assert "__allow_lossy__: true" in h
    assert "return false" in h  # declined -> nothing saved


def test_both_tier_preset_saves_use_helper():
    # only the helper itself (first try + retry) posts directly
    assert HTML.count('api.post("/api/tier-presets/update"') == 2
    assert HTML.count("postTierPresetsConfirmingLoss(") >= 3  # def + add + save
