"""IC-15 Nr. 12 (F-16, AC-11 part, AC-21 part): context files without provider noise.

* The routing banner of a context file names only the providers the project
  activates (the AGENTS.md header listed hard-wired catalog providers, e.g.
  ``Opencode->AGENTS.md | Gemini->AGENTS.md`` in a Codex-only project).
* A lazy-skill table (``| Skill | Wann |``, rule ``use-lazy-rules``) lists only
  skills that exist after the sync for that provider; a table without any
  existing skill is not rendered at all (it named up to 15 agent-meta-internal
  skills in every consumer project).

Provider-agnostic: provider names come from config/ai-providers.yaml.

Run: python3 -m pytest tests/test_context_header_noise.py -q
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.consistency import context_budget as cb  # noqa: E402
from lib.providers import load_provider_capabilities, load_providers_config  # noqa: E402
from tests.active_set_render import default_config, preset_config, synced_projects  # noqa: E402

_PROVIDERS = sorted(load_providers_config(REPO_ROOT, {}))
_MAPPINGS = cr.merge_provider_mappings(
    load_providers_config(REPO_ROOT, {}), load_provider_capabilities(REPO_ROOT))
_BANNER_RE = re.compile(r"^> \*\*(AI )?ROUTING:\*\*(.*)$", re.MULTILINE)
_PRESETS = ("default", "lazy")


@pytest.fixture(scope="module")
def projects(tmp_path_factory):
    configs = {f"{preset}-{p}": preset_config(p, preset) for preset in _PRESETS for p in _PROVIDERS}
    every = default_config()
    every["ai-providers"] = list(_PROVIDERS)
    # The all-provider *full* render exceeds Codex' 32 KiB hard cap (AC-13) and
    # would abort the sync. Compact mode is the supported way to fit a large
    # context; it keeps every provider active (and therefore in the shared
    # AGENTS.md banner) while staying well below the cap.
    every["context_file"] = {"mode": "compact"}
    configs["all"] = every
    return synced_projects(tmp_path_factory, configs)


def _banners(project: Path, provider: str) -> list:
    text = (project / _MAPPINGS[provider]["context_file"]).read_text(encoding="utf-8")
    return [m.group(2) for m in _BANNER_RE.finditer(text)]


def _named(banner: str) -> set:
    return {p for p in _PROVIDERS if re.search(r"\b%s\b" % re.escape(p), banner)}


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_banner_names_only_active_providers(projects, provider):
    banners = _banners(projects[f"default-{provider}"], provider)
    for banner in banners:  # a context file without banner (Continue) has nothing to check
        assert _named(banner) == {provider}, f"{provider}: banner {banner!r}"


def test_banner_of_shared_file_names_every_active_provider(projects):
    sharers = {p for p in _PROVIDERS if _MAPPINGS[p]["context_file"] == "AGENTS.md"}
    banners = _banners(projects["all"], sorted(sharers)[0])
    assert banners
    for banner in banners:
        assert sharers <= _named(banner), banner


@pytest.mark.parametrize("preset", _PRESETS)
@pytest.mark.parametrize("provider", _PROVIDERS)
def test_lazy_table_lists_only_existing_skills(projects, preset, provider):
    project = projects[f"{preset}-{provider}"]
    active = compute_active_set(preset_config(provider, preset), REPO_ROOT, project)
    findings = cb.check_dangling_pointer(project, [provider], _MAPPINGS, active)
    assert not findings, [f"{f.file}: {f.message}" for f in findings][:5]


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_empty_lazy_table_is_not_rendered(projects, provider):
    """Default preset: no lazy skill exists, so no artifact carries the table."""
    project = projects[f"default-{provider}"]
    for artifact in cb._pointer_artifacts(project, _MAPPINGS[provider]):
        text = artifact.read_text(encoding="utf-8")
        assert not cb._lazy_table_skills(text), f"{provider}: {artifact.name} lists lazy skills"
        assert "# Lazy-Loaded Rules" not in text, f"{provider}: {artifact.name}"


def test_filter_skill_tables_unit():
    from lib.rules import filter_skill_tables, has_skill_table

    text = "# T\n\n| Skill | Wann |\n|---|---|\n| a | x |\n| b | y |\n\nfooter\n"
    assert has_skill_table(text) and not has_skill_table("# T\n| Agent | x |\n")
    assert filter_skill_tables("# no table\n", set()) == "# no table\n"
    assert filter_skill_tables(text, {"b"}) == "# T\n\n| Skill | Wann |\n|---|---|\n| b | y |\n\nfooter\n"
    assert filter_skill_tables(text, {"a", "b"}) == text
    assert filter_skill_tables(text, set()) is None
