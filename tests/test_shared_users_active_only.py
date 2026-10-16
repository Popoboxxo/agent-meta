"""IC-15 Nr. 1 (F-05): a shared context file lists only the paths of ACTIVE sharers.

Several providers render into the same physical context file (the AGENTS.md
group). The managed block used to join the per-provider path fields
(``agents_dir``, ``skills_dir``, ``pending_tasks_file``, ...) of every provider
in the catalog that declares this context file -- a single-provider project
named the directories of five providers it never uses. The sharer set is now
limited to the providers the project activates.

Provider-agnostic: the sharer group and the path values are read from
``config/ai-providers.yaml``; no provider name appears below except through
that data.

Run: python3 -m pytest tests/test_shared_users_active_only.py -q
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest
import yaml

from tests.active_set_render import default_config, preset_config, synced_project

REPO_ROOT = Path(__file__).resolve().parent.parent
_PROVIDERS = yaml.safe_load(
    (REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
# Path fields the managed block joins across the sharers of one context file.
_PATH_KEYS = ("agents_dir", "skills_dir", "pending_tasks_file", "extension_dir", "snippets_dir")
_BEGIN, _END = "<!-- agent-meta:managed-begin -->", "<!-- agent-meta:managed-end -->"


def _shared_group() -> tuple:
    """(context_file, sharers) of the largest catalog group sharing one context file."""
    counts = Counter(cfg.get("context_file") for cfg in _PROVIDERS.values())
    context_file, _n = counts.most_common(1)[0]
    sharers = sorted(p for p, cfg in _PROVIDERS.items() if cfg.get("context_file") == context_file)
    return context_file, sharers


CONTEXT_FILE, SHARERS = _shared_group()
# One sharer with and one without a native rules dir, plus the pair of both.
_WITH_RULES = next(p for p in SHARERS if _PROVIDERS[p].get("has_rules"))
_WITHOUT_RULES = next(p for p in SHARERS if not _PROVIDERS[p].get("has_rules"))


def _managed_block(project: Path) -> str:
    text = (project / CONTEXT_FILE).read_text(encoding="utf-8")
    return text[text.index(_BEGIN):text.index(_END)]


def _path_values(provider: str) -> set:
    values = (_PROVIDERS[provider].get(key) for key in _PATH_KEYS)
    return {v for v in values if isinstance(v, str) and v}


def test_catalog_has_a_shared_group_with_both_rule_kinds():
    assert len(SHARERS) >= 3, SHARERS
    assert _WITH_RULES != _WITHOUT_RULES


@pytest.mark.parametrize("provider", [_WITH_RULES, _WITHOUT_RULES])
def test_single_provider_block_names_no_inactive_sharer_path(tmp_path_factory, provider):
    project = synced_project(tmp_path_factory, preset_config(provider))
    block = _managed_block(project)
    own = _path_values(provider)
    foreign = set().union(*(_path_values(p) for p in SHARERS if p != provider)) - own
    leaked = sorted(v for v in foreign if v in block)
    assert not leaked, f"{provider}: managed block names paths of inactive sharers: {leaked}"
    assert _PROVIDERS[provider]["agents_dir"] in block


def test_two_active_sharers_list_both_paths(tmp_path_factory):
    pair = [_WITH_RULES, _WITHOUT_RULES]
    project = synced_project(tmp_path_factory, default_config(), pair)
    block = _managed_block(project)
    for provider in pair:
        assert _PROVIDERS[provider]["agents_dir"] in block, provider
    inactive = set().union(*(_path_values(p) for p in SHARERS if p not in pair))
    inactive -= _path_values(_WITH_RULES) | _path_values(_WITHOUT_RULES)
    assert not sorted(v for v in inactive if v in block)
