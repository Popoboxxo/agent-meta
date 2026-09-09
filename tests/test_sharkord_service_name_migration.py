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
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

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

    validate_result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--validate"],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60,
    )
    assert validate_result.returncode == 0, validate_result.stdout + validate_result.stderr

    docker_agent = tmp_path / ".claude" / "agents" / "docker.md"
    assert docker_agent.is_file()
    content = docker_agent.read_text(encoding="utf-8")
    assert "{{platform.sharkord.service_name}}" not in content
    assert "{{platform.sharkord.host_lan_ip}}" not in content
    assert "127.0.0.1" in content  # HOST_LAN_IP resolved via the platform cascade (Task 3)
