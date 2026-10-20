"""Task 13 (2b.4): REFERENCE sections of generic rules reach the skills channel.

Spec ``docs/specs/2026-10-11-context-profiles-spec.md`` IC-07 (AC-24 C5, AC-32):
``_COMPACT_PLATFORM_RULES`` classifies the generic rules that carry a REFERENCE
portion next to their INSTRUCTION core — ``a2a-delegation-gates``,
``branch-guard``, ``submodule-protection``, ``security-paved-roads``, classified
after ``docs/guides/context-block-inventory.md``:

* the INSTRUCTION core stays embedded (the compact entry file carries it via the
  gate card, IC-06);
* the removed REFERENCE sections are written as
  ``<skills_dir>/<rule>/SKILL.md`` for a context file whose sharers all read
  rules as skills — through the existing Phase-1 writer (same ``SKILL.md``
  format, deliberately outside the lazy skills index);
* without such a channel the full text stays embedded (invariant §4.3) and a
  ``context.rule-reference-fallback`` WARN is logged;
* ``full`` (or no opt-in) stays byte-identical to the committed managed block.

``compact`` stays opt-in and unverified (IC-36): nothing here claims the profile
is verified, validated or recommended.

Run: python3 -m pytest tests/test_compact_rule_channels.py -q
"""
from __future__ import annotations

import difflib
import re
import shutil
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402
from lib.config import build_variables, load_config  # noqa: E402
from lib.consistency import context_budget as cb  # noqa: E402
from lib.context import (  # noqa: E402
    _COMPACT_PLATFORM_RULES,
    _build_managed_block,
    _split_compact_rule,
    compact_embedded_rule,
    sync_context_for_provider,
)
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_provider_capabilities, load_providers_config  # noqa: E402
from lib.rules import sync_embedded_rule_files  # noqa: E402

_PROVIDER = "Opencode"
_SKILLS_DIR = ".opencode/skills"
# IC-07: generic rules with a REFERENCE portion (classification:
# docs/guides/context-block-inventory.md §4a — the INSTRUCTION core stays, the
# "Bekannte Grenzen"/detail prose is reference).
_REFERENCE_RULES = (
    "a2a-delegation-gates",
    "branch-guard",
    "submodule-protection",
    "security-paved-roads",
)
_MANAGED_BLOCK_RE = re.compile(
    r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
    re.DOTALL,
)

# (rule, INSTRUCTION-core markers, REFERENCE markers) of the split.
_SPLIT_CASES = (
    (
        "a2a-delegation-gates",
        (
            "# A2A Anti-Re-Delegation Gates",
            "## Enforced Gates (aktiv prüfen — HARD REJECT)",
            "No Self-Handoff / No Re-Delegation",
        ),
        ("## Degradierte Checks", "## Bekannte Grenzen"),
    ),
    (
        "branch-guard",
        ("# Branch-Guard", "Keine Code-Änderungen direkt auf `main` oder `master`"),
        ("## Guard-Terminologie", "## Bekannte Grenzen"),
    ),
    (
        "security-paved-roads",
        ("# Security Paved Roads", "## Enforcement", "Vor jedem Commit"),
        ("## Block-Katalog", "| Block | Abdeckt | Eigentümer-Agent |"),
    ),
)
_CORE_MARKERS = {stem: core for stem, core, _ in _SPLIT_CASES}
_REFERENCE_MARKERS = {stem: reference for stem, _, reference in _SPLIT_CASES}


def _rule_text(stem: str) -> str:
    return (_REPO_ROOT / "rules" / "1-generic" / f"{stem}.md").read_text(encoding="utf-8")


def _fixture_config(*, profile: str | None = "compact", preset: str | None = None) -> dict:
    """Repo config scoped to one provider; the profile decides the density.

    ``context_file.mode`` is dropped so the profile resolves the entry-file
    density (a stale explicit mode would otherwise win over the profile), and
    the project-level ``rules`` overrides are cleared so the preset alone
    decides which rule leaves the embed.
    """
    config = dict(load_config(_REPO_ROOT / ".meta-config" / "project.yaml"))
    config["ai-providers"] = [_PROVIDER]
    context_file = dict(config.get("context_file") or {})
    context_file.pop("mode", None)
    config["context_file"] = context_file
    config["rules"] = {}
    if preset is not None:
        config["rules-preset"] = preset
    if profile is not None:
        config["context-profile"] = profile
    return config


def _render(project_root: Path, config: dict, provider_config: dict) -> str:
    variables, _warnings = build_variables(config, _REPO_ROOT, project_root)
    return _build_managed_block(
        _REPO_ROOT, config, variables, SyncLog(), provider=_PROVIDER,
        provider_config=provider_config, project_root=project_root,
    )


def _sync_with_references(tmp_path: Path, config: dict, *, preset: str) -> tuple[Path, SyncLog]:
    """Sync the fixture project (entry file + reference skills) and return it."""
    project = tmp_path / f"compact-{preset}"
    project.mkdir()
    shutil.copy(_REPO_ROOT / "AGENTS.md", project / "AGENTS.md")
    provider_config = load_providers_config(_REPO_ROOT)
    variables, _warnings = build_variables(config, _REPO_ROOT, project)
    log = SyncLog()
    sync_context_for_provider(
        _REPO_ROOT, project, config, variables, log, dry_run=False,
        provider=_PROVIDER, provider_config=provider_config,
    )
    return project, log


def _diff(expected: str, actual: str, label: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            expected.splitlines(), actual.splitlines(),
            f"expected/{label}", f"actual/{label}", lineterm="",
        )
    )


# --- classification and split (unit) ---------------------------------------

@pytest.mark.parametrize("stem", _REFERENCE_RULES)
def test_ic07_reference_rules_are_classified(stem):
    """IC-07: the generic reference rules are in ``_COMPACT_PLATFORM_RULES``."""
    spec = _COMPACT_PLATFORM_RULES[stem]
    assert spec.get("reference_skill") is True, stem
    assert isinstance(spec["keep"], tuple), stem
    assert spec["pointer"].strip(), stem


def test_classification_stays_provider_agnostic():
    """No provider name in the classification (AC-61/AC-36)."""
    source = (_REPO_ROOT / "scripts" / "lib" / "context.py").read_text(encoding="utf-8")
    table = source.split("_COMPACT_PLATFORM_RULES = {", 1)[1].split("\n}\n", 1)[0]
    registered = load_providers_config(_REPO_ROOT)
    for provider in registered:
        assert provider not in table, provider


@pytest.mark.parametrize("stem,core_markers,reference_markers", _SPLIT_CASES)
def test_reference_split_keeps_the_instruction_core(stem, core_markers, reference_markers):
    """INSTRUCTION core and REFERENCE text are separated without losing a line."""
    text = _rule_text(stem)
    core, reference = _split_compact_rule(stem, text)

    for marker in core_markers:
        assert marker in core, f"{stem}: INSTRUCTION marker {marker!r} left the core"
    assert core.startswith(core_markers[0]), f"{stem}: core does not start at its title"
    for marker in reference_markers:
        assert marker in reference, f"{stem}: REFERENCE marker {marker!r} missing"
    for marker in reference_markers:
        assert marker not in core, f"{stem}: REFERENCE marker {marker!r} stayed embedded"

    kept_lines = [ln for ln in (core + "\n" + reference).splitlines() if ln.strip()]
    assert sorted(kept_lines) == sorted(ln for ln in text.splitlines() if ln.strip())


def test_submodule_protection_has_no_reference_portion():
    """Its whole body is the INSTRUCTION core — nothing is moved to a skill."""
    text = _rule_text("submodule-protection")
    core, reference = _split_compact_rule("submodule-protection", text)
    assert core == text.rstrip()
    assert reference == ""


@pytest.mark.parametrize("stem", tuple(_CORE_MARKERS))
def test_compact_embedded_rule_keeps_full_text_without_a_skills_channel(stem):
    """Invariant §4.3: no read channel for the reference -> full text stays."""
    text = _rule_text(stem)
    assert compact_embedded_rule(
        stem, text, profile_compact=True, skills_channel=False
    ) == text


@pytest.mark.parametrize("stem", tuple(_CORE_MARKERS))
def test_compact_embedded_rule_drops_reference_with_a_skills_channel(stem):
    """With a channel the block keeps the core plus the reference pointer."""
    compacted = compact_embedded_rule(
        stem, _rule_text(stem), profile_compact=True, skills_channel=True
    )
    for marker in _CORE_MARKERS[stem]:
        assert marker in compacted, f"{stem}: lost INSTRUCTION marker {marker!r}"
    for marker in _REFERENCE_MARKERS[stem]:
        assert marker not in compacted, f"{stem}: kept REFERENCE marker {marker!r}"
    assert _COMPACT_PLATFORM_RULES[stem]["pointer"] in compacted


def test_compact_embedded_rule_is_a_noop_for_unclassified_rules():
    text = _rule_text("commit-conventions")
    assert compact_embedded_rule("commit-conventions", text) == text
    assert compact_embedded_rule("commits", text, profile_compact=True) == text


@pytest.mark.parametrize("stem", ("a2a-delegation-gates", "security-paved-roads"))
def test_reference_entries_are_profile_only(stem):
    """Opt-in only: without ``context-profile`` the #540 render keeps its bytes.

    The reference pointer names a skill that only the profile writer produces,
    so the sections must not leave the block in a plain COMPACT_MODE render.
    """
    assert _COMPACT_PLATFORM_RULES[stem].get("profile_only") is True
    text = _rule_text(stem)
    assert compact_embedded_rule(stem, text, profile_compact=False) == text


# --- byte stability without the opt-in -------------------------------------

def test_no_opt_in_render_is_byte_identical_to_the_committed_block(tmp_path):
    """AC-01/AC-23: without ``context-profile`` the render does not change."""
    committed = (_REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    match = _MANAGED_BLOCK_RE.search(committed)
    assert match, "committed AGENTS.md has no managed block"

    provider_config = load_providers_config(_REPO_ROOT)
    repo_config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
    no_key = _render(tmp_path / "no-key", repo_config, provider_config)
    full = _render(
        tmp_path / "full", {**repo_config, "context-profile": "full"}, provider_config
    )

    assert no_key == full, _diff(no_key, full, "agents-managed(full)")
    assert no_key.rstrip("\n") == match.group(0).rstrip("\n"), _diff(
        match.group(0).rstrip("\n"), no_key.rstrip("\n"), "agents-managed(no-key)"
    )


# --- reference skills over the skills channel (integration) ----------------

def test_with_skills_channel_writes_reference_skills(tmp_path):
    """The removed REFERENCE sections land as ``<skills_dir>/<rule>/SKILL.md``."""
    config = _fixture_config(profile="compact", preset="default")
    project, log = _sync_with_references(tmp_path, config, preset="default")
    skills_dir = project / _SKILLS_DIR

    for stem in ("a2a-delegation-gates", "branch-guard", "security-paved-roads"):
        skill = skills_dir / stem / "SKILL.md"
        assert skill.is_file(), f"{stem}: reference skill missing ({skill})"
        text = skill.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{stem}: no Phase-1 skill frontmatter"
        for marker in _REFERENCE_MARKERS[stem]:
            assert marker in text, f"{stem}: reference marker {marker!r} missing"
        for marker in _CORE_MARKERS[stem]:
            assert marker not in text, f"{stem}: INSTRUCTION core leaked into the skill"

    # No empty skill for a rule without a reference portion.
    assert not (skills_dir / "submodule-protection" / "SKILL.md").exists()

    # INSTRUCTION cores stay embedded in the compact entry file, the reference
    # sections do not (the entry file carries the gate card, IC-06).
    entry = (project / "AGENTS.md").read_text(encoding="utf-8")
    for marker in (
        "# Branch-Guard",
        "## Enforced Gates (aktiv prüfen — HARD REJECT)",
        "Keine Code-Änderungen direkt auf `main` oder `master`",
    ):
        assert marker in entry, f"compact entry lost the INSTRUCTION core {marker!r}"
    for marker in ("## Guard-Terminologie", "## Bekannte Grenzen", "## Block-Katalog"):
        assert marker not in entry, f"compact entry kept the REFERENCE section {marker!r}"

    assert not [w for w in log.warnings if "rule-reference-fallback" in w]


def test_reference_rules_stay_reachable_for_the_provider(tmp_path):
    """§4.3: every reference rule is embedded or delivered through a skill."""
    preset = "lazy"
    config = _fixture_config(profile="compact", preset=preset)
    project, _log = _sync_with_references(tmp_path, config, preset=preset)

    # The lazy preset routes the reference rules outside branch-guard into the
    # Phase-1 file channel; running that writer mirrors a real sync.
    provider_config = load_providers_config(_REPO_ROOT)
    variables, _warnings = build_variables(config, _REPO_ROOT, project)
    sync_embedded_rule_files(
        _REPO_ROOT, project, config, SyncLog(), dry_run=False,
        variables=variables, provider=_PROVIDER, provider_config=provider_config,
    )

    # Rule files a native rules channel would carry (the check inspects them).
    rules_dir = project / "rules"
    rules_dir.mkdir()
    for stem in _REFERENCE_RULES:
        shutil.copy(_REPO_ROOT / "rules" / "1-generic" / f"{stem}.md", rules_dir / f"{stem}.md")

    mappings = cr.merge_provider_mappings(
        load_providers_config(_REPO_ROOT, {}), load_provider_capabilities(_REPO_ROOT)
    )
    caps = {_PROVIDER: {**mappings[_PROVIDER], "has_rules": True, "rules_dir": "rules"}}
    findings = cb.check_rule_unreachable(project, [_PROVIDER], caps, None)
    assert findings == [], [f.message for f in findings]

    # The lazy channel owns its stems; branch-guard's reference came from the
    # compact writer. Both artifacts exist, none is written twice — and the
    # Phase-1 stale cleanup above (universe: all rule stems) did not delete the
    # reference skill of the still-embedded branch-guard rule.
    skills_dir = project / _SKILLS_DIR
    assert (skills_dir / "branch-guard" / "SKILL.md").is_file()
    for stem in ("a2a-delegation-gates", "submodule-protection", "security-paved-roads"):
        assert (skills_dir / stem / "SKILL.md").is_file(), stem


def test_without_skills_channel_writes_no_skill_and_warns(tmp_path, monkeypatch):
    """Requirement 4: no reachable channel -> embed + WARN, no artifact."""
    import lib.providers as providers

    real = providers.load_provider_capabilities

    def _without_skills(root):
        caps = {name: dict(entry or {}) for name, entry in real(root).items()}
        caps[_PROVIDER]["rules_read_channels"] = ["embedded"]
        return caps

    monkeypatch.setattr(providers, "load_provider_capabilities", _without_skills)

    config = _fixture_config(profile="compact", preset="default")
    project, log = _sync_with_references(tmp_path, config, preset="no-skills")

    assert not (project / _SKILLS_DIR).exists(), "skills written without a channel"
    fallback = [w for w in log.warnings if "context.rule-reference-fallback" in w]
    assert fallback, log.warnings
    assert any(stem in fallback[0] for stem in _REFERENCE_RULES), fallback[0]
