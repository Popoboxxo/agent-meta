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
    (rules_dir / "root-cause-gate.md").write_text(
        "# root-cause-gate\n", encoding="utf-8")
    (rules_dir / "session-recovery.md").write_text(
        "# session-recovery\n", encoding="utf-8")
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
        "    requires: unknown.flag\n"
        "  root-cause-gate:\n"
        "    requires: dod.root-cause-required\n"
        "  session-recovery:\n"
        "    requires: spec-plan-workflow.enabled\n",
        encoding="utf-8",
    )
    # Minimal DoD preset so resolve_dod exposes root-cause-required; the
    # project `dod` override in the tests wins over this default.
    (cfg_dir / "dod-presets.yaml").write_text(
        "presets:\n"
        "  full:\n"
        "    root-cause-required: false\n",
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
    "session-recovery",
    "root-cause-gate",
)

# Expected `rule-gates.<stem>.requires` per new stem: the spec/plan workflow
# rules gate on the workflow switch, root-cause-gate on the DoD flag.
_NEW_STEM_REQUIRES = {
    "spec-plan-workflow": "spec-plan-workflow.enabled",
    "brainstorming-gate": "spec-plan-workflow.enabled",
    "writing-plans": "spec-plan-workflow.enabled",
    "plan-ledger": "spec-plan-workflow.enabled",
    "session-recovery": "spec-plan-workflow.enabled",
    "root-cause-gate": "dod.root-cause-required",
}


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
    for stem, requires in _NEW_STEM_REQUIRES.items():
        assert gates[stem]["requires"] == requires


# --- Task 13 (IC-09): DoD flag + root-cause/session-recovery rule-gates ------


def test_root_cause_gate_flag_on_off(tmp_path):
    """AC-24: the root-cause-gate rule follows dod.root-cause-required."""
    root = _meta_root(tmp_path)
    on = _names(root, {"dod": {"root-cause-required": True}})
    off = _names(root, {"dod": {"root-cause-required": False}})
    assert "root-cause-gate.md" in on
    assert "root-cause-gate.md" not in off


def test_unknown_gate_requirement_fails_closed(tmp_path):
    """AC-24: an unknown requirement stays out even when other flags are on."""
    root = _meta_root(tmp_path)
    config = {
        "dod": {"root-cause-required": True},
        "spec-plan-workflow": {"enabled": True},
    }
    names = _names(root, config)
    assert "unknown-gate-rule.md" not in names
    # Known gates still activate, so the assertion is not vacuous.
    assert "root-cause-gate.md" in names
    assert "session-recovery.md" in names


def test_session_recovery_gate_follows_workflow(tmp_path):
    """AC-24: session-recovery is gated on spec-plan-workflow.enabled."""
    root = _meta_root(tmp_path)
    on = _names(root, {"spec-plan-workflow": {"enabled": True}})
    off = _names(root, {"spec-plan-workflow": {"enabled": False}})
    assert "session-recovery.md" in on
    assert "session-recovery.md" not in off


def test_resolve_dod_exposes_root_cause_required(tmp_path):
    """AC-25: resolve_dod returns the resolved root-cause-required flag."""
    from lib.dod import resolve_dod
    root = _meta_root(tmp_path)
    assert resolve_dod(
        {"dod": {"root-cause-required": True}}, root,
    )["root-cause-required"] is True
    assert resolve_dod(
        {"dod": {"root-cause-required": False}}, root,
    )["root-cause-required"] is False


def test_repo_dod_presets_declare_root_cause_required():
    """AC-25: every shipped preset declares the flag; the heavy ones enable it."""
    from lib.dod import load_dod_presets
    presets = load_dod_presets(REPO_ROOT)
    for name, values in presets.items():
        assert "root-cause-required" in values, name
    for name in ("spec-driven", "concept-driven", "spec-certified"):
        assert presets[name]["root-cause-required"] is True, name
    for name in ("full", "standard", "rapid-prototyping", "spec-optional"):
        assert presets[name]["root-cause-required"] is False, name


def test_repo_rule_gates_declare_root_cause_and_session_recovery():
    """AC-24: the shipped rule-gates section names both new gates."""
    from lib.io import _load_yaml_or_json
    data, _ = _load_yaml_or_json(REPO_ROOT / "config" / "rules-presets.yaml")
    gates = data["rule-gates"]
    assert gates["session-recovery"]["requires"] == "spec-plan-workflow.enabled"
    assert gates["root-cause-gate"]["requires"] == "dod.root-cause-required"
