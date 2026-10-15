"""IC-15 Nr. 2 / IC-33 (F-06, #857, #858): lazy rules reach every provider with a skills channel.

A rule routed out of the always-on context (``embed: false`` / ``channel: skill``,
rules-presets ``lazy`` and ``silent``) must still reach the provider:

* a provider whose ``rules_read_channels`` has no native rules channel but
  ``skills`` gets the rule as ``<skills_dir>/<rule>/SKILL.md`` -- independent of
  ``has_rules`` (a written but unread rules directory does not count);
* a provider without native rules channel and without skills channel keeps the
  rule embedded in its context file (never content loss, spec §4.3);
* a provider with a native rules channel and the native skill channel gets
  ``channel: skill`` rules as skills.

Provider-agnostic: providers are classified through their channel data
(``scripts/lib/rule_channels.py``); no provider name below.

Run: python3 -m pytest tests/test_lazy_skills_channel.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.consistency import context_budget as cb  # noqa: E402
from lib.providers import load_provider_capabilities, load_providers_config  # noqa: E402
from lib.rule_channels import lazy_skill_channel, reads_native_rules  # noqa: E402
from lib.rules import collect_rule_sources, resolve_rules, rule_opts_lazy_channel  # noqa: E402
from lib.skill_channel import provider_supports_skill_channel  # noqa: E402
from tests.active_set_render import preset_config, synced_projects  # noqa: E402

_PROVIDERS = sorted(load_providers_config(REPO_ROOT, {}))
_MAPPINGS = cr.merge_provider_mappings(
    load_providers_config(REPO_ROOT, {}), load_provider_capabilities(REPO_ROOT))
_PRESETS = ("lazy", "silent")


@pytest.fixture(scope="module")
def projects(tmp_path_factory):
    configs = {f"{preset}-{p}": preset_config(p, preset) for preset in _PRESETS for p in _PROVIDERS}
    return synced_projects(tmp_path_factory, configs)


def _lazy_stems(config: dict, provider: str) -> set:
    """Rules of this sync that leave the embedded context (embed: false / channel: skill)."""
    options = resolve_rules(config, REPO_ROOT)
    stems = set()
    for _src, output_name in collect_rule_sources(REPO_ROOT, config.get("platforms", []), config=config):
        stem = Path(output_name).stem
        opts = options.get(stem, {})
        if opts.get(provider.lower()) in ("skip", False):
            continue
        if rule_opts_lazy_channel(opts):
            stems.add((stem, opts.get("channel") == "skill"))
    return stems


def _skill_exists(project: Path, caps: dict, stem: str) -> bool:
    return (project / caps["skills_dir"] / stem / "SKILL.md").is_file()


def test_every_skills_channel_provider_is_classified():
    lazy = [p for p in _PROVIDERS if lazy_skill_channel(_MAPPINGS[p])]
    # Codex/Mammouth (unread rules dir) and the embedded-only providers all have
    # a skills channel in the data; at least the four named in IC-15 Nr. 2 qualify.
    assert len(lazy) >= 4, lazy
    for p in lazy:
        assert _MAPPINGS[p].get("skills_dir"), p


@pytest.mark.parametrize("preset", _PRESETS)
@pytest.mark.parametrize("provider", _PROVIDERS)
def test_lazy_rules_exist_as_skills(projects, preset, provider):
    caps = _MAPPINGS[provider]
    project = projects[f"{preset}-{provider}"]
    config = preset_config(provider, preset)
    if lazy_skill_channel(caps):
        expected = {stem for stem, _ in _lazy_stems(config, provider)}
    elif reads_native_rules(caps) and provider_supports_skill_channel(provider, caps):
        expected = {stem for stem, is_skill in _lazy_stems(config, provider) if is_skill}
    else:
        pytest.skip("no skills channel: lazy rules stay embedded / in the native rules dir")
    missing = sorted(s for s in expected if not _skill_exists(project, caps, s))
    assert not missing, f"{provider}/{preset}: lazy rules without SKILL.md: {missing}"


@pytest.mark.parametrize("preset", _PRESETS)
@pytest.mark.parametrize("provider", _PROVIDERS)
def test_no_lazy_rule_is_lost(projects, preset, provider):
    """The lazy pointer has skills behind it and no lazy rule is unreachable (spec §4.3)."""
    caps = _MAPPINGS[provider]
    if reads_native_rules(caps):
        pytest.skip("native rules channel: lazy rules stay readable in the rules directory")
    project = projects[f"{preset}-{provider}"]
    config = preset_config(provider, preset)
    active = compute_active_set(config, REPO_ROOT, project)
    pointer = [f for f in cb.check_dangling_pointer(project, [provider], _MAPPINGS, active)
               if "lazy-load pointer" in f.message]
    assert not pointer, [f.message for f in pointer]
    lazy = {stem for stem, _ in _lazy_stems(config, provider)}
    lost = sorted(Path(f.file).stem for f in cb.check_rule_unreachable(project, [provider], _MAPPINGS, active)
                  if Path(f.file).stem in lazy)
    assert not lost, f"{provider}/{preset}: lazy rules reachable through no channel: {lost}"


def test_gemini_lazy_loss_is_closed_via_data():
    """The former 8-rule loss (rules preset lazy, rules dir unread) has a channel now."""
    lost = [p for p in _PROVIDERS
            if not reads_native_rules(_MAPPINGS[p]) and _MAPPINGS[p].get("has_rules")
            and _MAPPINGS[p].get("skills_dir")]
    for p in lost:
        assert lazy_skill_channel(_MAPPINGS[p]), f"{p}: unread rules dir and no lazy skills channel"


def test_classification_uses_channel_data_not_has_rules():
    caps = {"has_rules": True, "skills_dir": "s", "rules_read_channels": ["embedded", "skills"]}
    assert lazy_skill_channel(caps) and not reads_native_rules(caps)
    caps = {"has_rules": False, "skills_dir": "s", "rules_read_channels": ["embedded"]}
    assert not lazy_skill_channel(caps)
    # legacy entries without channel data keep the has_rules semantics
    assert lazy_skill_channel({"has_rules": False, "skills_dir": "s"})
    assert not lazy_skill_channel({"has_rules": True, "skills_dir": "s"})
    assert not lazy_skill_channel({"has_rules": False})


def test_module_reads_no_provider_names():
    source = (REPO_ROOT / "scripts" / "lib" / "rule_channels.py").read_text(encoding="utf-8")
    for name in yaml.safe_load((REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]:
        assert f'"{name}"' not in source and f"'{name}'" not in source, name
