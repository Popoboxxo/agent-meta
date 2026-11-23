"""Issue #1329 (Stage-2 review F1) — external-skill render path must not fail open.

The skills.py wrapper path calls ``transform_agent_content_for_provider()``
for every provider that declares a ``skills_dir`` (e.g. Mammouth). It MUST pass
the resolved provider-capability registry so the opencode-native permission
mappers see the declared ``subagent-shell`` grant. A non-grant provider
(Mammouth: false / UNVERIFIED) must render the wrapper's template ``Bash`` as
``bash: deny`` (never ``allow``) and emit a WARNING — never a silent fail-open.

Run: python3 -m pytest tests/test_external_skill_shell_gate.py -q
"""
from __future__ import annotations

import shutil
from pathlib import Path

from scripts.lib.frontmatter import _parse_frontmatter_yaml
from scripts.lib.log import SyncLog
from scripts.lib.providers import load_providers_config
from scripts.lib.skills import sync_external_skills_for_provider

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVIDER = "Mammouth"


class _FakeActiveSet:
    """Minimal active set: no scout role, so no implicit awesome-claude-code."""

    raw_roles: tuple = ()

    def has(self, role: str) -> bool:
        return False


def _setup(root: Path) -> None:
    (root / "agents" / "0-external").mkdir(parents=True, exist_ok=True)
    shutil.copy(
        REPO_ROOT / "agents" / "0-external" / "_skill-wrapper.md",
        root / "agents" / "0-external" / "_skill-wrapper.md",
    )
    (root / "external" / "testrepo").mkdir(parents=True, exist_ok=True)
    (root / "external" / "testrepo" / "SKILL.md").write_text(
        "---\nname: shell-skill\ndescription: test\n---\n\nSkill body.\n",
        encoding="utf-8",
    )
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "skills-registry.yaml").write_text(
        "\n".join(
            [
                "repos: {}",
                "skills:",
                "  shell-skill:",
                "    approved: true",
                "    source: testrepo",
                "    entry: SKILL.md",
                "    role: shell-skill",
                "    name: Shell Skill",
                "    description: wrapper declares template Bash",
                "    enabled-by-default: true",
                "",
            ]
        ),
        encoding="utf-8",
    )
    # Real framework registry: Mammouth declares subagent-shell: false / UNVERIFIED.
    shutil.copy(
        REPO_ROOT / "config" / "provider-capabilities.yaml",
        root / "config" / "provider-capabilities.yaml",
    )


def test_external_skill_wrapper_non_grant_provider_denies_bash_with_warning(tmp_path):
    """Regression F1: skills.py must resolve capabilities and gate Bash.

    Rendering the real external-skill wrapper for a non-grant provider through
    the skills.py path must yield ``bash: deny`` (never ``allow``) AND a
    fail-safe WARNING (AC-2). Before the fix the call omitted
    ``provider_capabilities``, so the UNSET sentinel allowed Bash silently.
    """
    root = tmp_path
    _setup(root)

    pc = load_providers_config(REPO_ROOT)
    provider_config = {PROVIDER: pc[PROVIDER]}
    variables = {
        "PROJECT_NAME": "demo",
        "COMMUNICATION_LANGUAGE": "English",
        "USER_INPUT_LANGUAGE": "English",
    }
    log = SyncLog()

    sync_external_skills_for_provider(
        agent_meta_root=root,
        project_root=root,
        config={},
        variables=variables,
        log=log,
        dry_run=False,
        provider=PROVIDER,
        provider_config=provider_config,
        active_set=_FakeActiveSet(),
    )

    generated = root / ".mammouth" / "agents" / "shell-skill.md"
    assert generated.exists(), "external-skill wrapper agent was not generated"
    fm = _parse_frontmatter_yaml(generated.read_text(encoding="utf-8"))
    perm = fm.get("permission") or {}

    assert perm.get("bash") != "allow", (
        f"non-grant {PROVIDER} must not get bash allow; got permission={perm!r}"
    )
    assert [w for w in log.warnings if "subagent shell" in w.lower()], (
        "non-grant render must emit a fail-safe WARNING (AC-2), never fail open silently"
    )
