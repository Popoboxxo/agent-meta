"""Task 8 (platform-project-defaults feature): sharkord's
{{platform.sharkord.host_lan_ip}} template placeholder migrated to the
generic, platform-cascaded {{HOST_LAN_IP}} (design spec Architektur §1 --
sharkord SERVICE_NAME/HOST_LAN_IP duplication cleanup).

Verified real call sites before writing this test (grep, see plan Task 8
notes): agents/2-platform/sharkord-docker.md lines 139 and 157 were the
ONLY two real usages of {{platform.sharkord.host_lan_ip}} in the whole
repo; {{platform.sharkord.service_name}} had ZERO real usages (only the
design spec's own illustrative comment) -- so only host_lan_ip needed a
template edit; service_name's now-redundant defaults key is removed outright.
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md

W2-8: the test no longer runs ``sync.py --validate``; that step measured the
host repo's global consistency exit code, not this fixture. The generated-tree
assertion below is the fixture's own scope.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

# The guard uses the PRODUCER's own pattern instead of a re-typed copy. Which
# placeholders the sync tries to resolve -- and may leave standing -- is defined
# exactly once, in ``lib.platform``. A hand-written ``[A-Za-z0-9_.-]+`` variant is
# strictly NARROWER than that definition, and therefore blind to gaps the sync
# really can leave behind: whitespace or punctuation inside the braces still
# match ``_PLATFORM_VAR_RE``, and ``_substitute_platform_vars`` then fails to
# resolve them and keeps the text (it only warns). Importing the single source
# makes "whatever production recognises, the guard recognises too" structural:
# there is no second spelling left to drift. Generic framework placeholders
# (``{{PRIMARY_PORT}}`` and friends) carry no ``platform.`` namespace and are
# filled by the consumer project, so they are correctly not matched.
from lib.platform import _PLATFORM_VAR_RE  # noqa: E402  (needs the sys.path insert above)

_PROJECT_YAML = """
agent-meta-version: 0.101.0
ai-providers: [Claude]
platforms: [sharkord]
roles: [orchestrator, docker, git]
project:
  name: sharkord-migration-test
  prefix: smt
  short: sharkord-migration-test
"""


def test_generated_docker_agent_has_no_leftover_platform_namespace_placeholder(tmp_path):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(_PROJECT_YAML, encoding="utf-8")

    sync_result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert sync_result.returncode == 0, sync_result.stdout + sync_result.stderr

    docker_agent = tmp_path / ".claude" / "agents" / "docker.md"
    assert docker_agent.is_file()
    content = docker_agent.read_text(encoding="utf-8")
    assert "{{platform.sharkord.service_name}}" not in content
    assert "{{platform.sharkord.host_lan_ip}}" not in content
    assert "127.0.0.1" in content  # HOST_LAN_IP resolved via the platform cascade (Task 3)

    # W2-8 decoupling: the `sync.py --validate` step that used to sit here
    # asserted the *host* repo's global consistency exit code. Even with
    # ``cwd=tmp_path`` it is a foreign measure: ``_handle_validate`` runs the
    # runner over ``agent_meta_root`` (``cli_commands.py:975``), and the runner
    # passes ``_AGENT_META_ROOT`` unconditionally to the three old checks
    # (``consistency-check.py:196`` and ``:199-201``, including
    # ``check_readme_docs_index``) -- ``--root`` is only honoured from
    # ``:257`` onwards. Measured on this fixture: ``consistency-check.py --json
    # --root <fixture>`` exits 1 with 3 ERRORs, all of them foreign (host
    # ``README.md`` plus two ``config/`` files the fixture does not have) and
    # none of them scoped to the generated ``.claude/agents/docker.md`` this
    # test owns. So the scope-filtered ``--json`` variant (mechanism iii) would
    # have been a no-op guard here, and the assertion below is the fixture's
    # own scope instead: no platform-namespace placeholder may survive ANYWHERE
    # in the generated agent tree. Non-vacuous -- ``agents/2-platform/
    # sharkord-docker.md`` still carries ``{{platform.sharkord.image_tag}}`` at
    # the template layer, so a regression that stops resolving the namespace
    # reappears in the generated output and is caught.
    survivors = {}
    for path in sorted((tmp_path / ".claude" / "agents").glob("*.md")):
        found = sorted(set(_PLATFORM_VAR_RE.findall(
            path.read_text(encoding="utf-8", errors="replace"))))
        if found:
            survivors[path.relative_to(tmp_path).as_posix()] = found
    assert not survivors, f"unresolved platform-namespace placeholders in generated agents: {survivors}"
