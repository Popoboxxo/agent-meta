"""Gate at the single choke-point collect_rule_sources: gated rules leave
EVERY preset when the master switch is off, and None config is fail-closed."""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.rules import collect_rule_sources  # noqa: E402


def _meta_root(tmp_path: Path) -> Path:
    root = tmp_path / "agent-meta"
    rules_dir = root / "rules" / "1-generic"
    rules_dir.mkdir(parents=True)
    (rules_dir / "spec-plan-workflow.md").write_text("# spec-plan-workflow\n", encoding="utf-8")
    (rules_dir / "branch-guard.md").write_text("# branch-guard\n", encoding="utf-8")
    (rules_dir / "unknown-gate-rule.md").write_text(
        "# unknown-gate-rule\n", encoding="utf-8")
    cfg_dir = root / "config"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "rules-presets.yaml").write_text(
        "presets:\n"
        "  default: {}\n"
        "  minimal: {}\n"
        "  silent: {}\n"
        "  lazy: {}\n"
        "rule-gates:\n"
        "  spec-plan-workflow:\n"
        "    requires: spec-plan-workflow.enabled\n"
        "  unknown-gate-rule:\n"
        "    requires: unknown.flag\n",
        encoding="utf-8",
    )
    return root


def _names(root, config):
    return {name for _, name in collect_rule_sources(root, [], config=config)}


def test_gate_delivers_rule_when_enabled(tmp_path):
    root = _meta_root(tmp_path)
    config = {"spec-plan-workflow": {"enabled": True}}
    names = _names(root, config)
    assert "spec-plan-workflow.md" in names
    assert "branch-guard.md" in names


@pytest.mark.parametrize("preset", ["default", "minimal", "silent", "lazy"])
def test_gate_removes_rule_when_disabled_in_every_preset(tmp_path, preset):
    root = _meta_root(tmp_path)
    config = {"spec-plan-workflow": {"enabled": False}, "rules-preset": preset}
    names = _names(root, config)
    assert "spec-plan-workflow.md" not in names
    assert "branch-guard.md" in names


def test_none_config_is_fail_closed(tmp_path):
    root = _meta_root(tmp_path)
    assert "spec-plan-workflow.md" not in _names(root, None)


def test_missing_config_kwarg_is_type_error(tmp_path):
    root = _meta_root(tmp_path)
    with pytest.raises(TypeError):
        collect_rule_sources(root, [])


def test_unknown_requires_never_activates_rule(tmp_path):
    """Unknown `requires` values are fail-closed: no config key can unlock them."""
    root = _meta_root(tmp_path)
    config = {"spec-plan-workflow": {"enabled": True}}
    names = _names(root, config)
    assert "unknown-gate-rule.md" not in names
    # sanity: the known gate is still delivered when its switch is on
    assert "spec-plan-workflow.md" in names


_NEW_STEMS = (
    "spec-plan-workflow",
    "brainstorming-gate",
    "writing-plans",
    "plan-ledger",
)


def test_new_rule_files_exist():
    for stem in _NEW_STEMS:
        assert (REPO_ROOT / "rules" / "1-generic" / f"{stem}.md").is_file()


def test_lazy_preset_routes_new_rules_to_skill_channel():
    from lib.io import _load_yaml_or_json
    data, _ = _load_yaml_or_json(REPO_ROOT / "config" / "rules-presets.yaml")
    lazy = data["presets"]["lazy"]
    for stem in _NEW_STEMS:
        assert lazy[stem]["channel"] == "skill"
        assert lazy[stem]["skill-description"].strip()


def test_rule_gates_section_declares_all_new_stems():
    from lib.io import _load_yaml_or_json
    data, _ = _load_yaml_or_json(REPO_ROOT / "config" / "rules-presets.yaml")
    gates = data["rule-gates"]
    for stem in _NEW_STEMS:
        assert gates[stem]["requires"] == "spec-plan-workflow.enabled"
