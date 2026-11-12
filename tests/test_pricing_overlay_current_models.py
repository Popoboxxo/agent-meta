from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def test_overlay_prices_every_current_claude_tier_and_alias_id():
    providers = yaml.safe_load((ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
    claude = providers["Claude"]
    ids = set(claude["model-tiers"].values()) | set(claude["model-aliases"].values())
    prices = yaml.safe_load((ROOT / "config" / "pricing-overlay.yaml").read_text(encoding="utf-8"))["prices"]["anthropic"]
    assert not [i for i in ids if i not in prices], sorted(ids - set(prices))
