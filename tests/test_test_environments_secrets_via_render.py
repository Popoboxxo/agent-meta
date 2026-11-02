"""Secret handling through the configured render (Task 8, AC-ENV-6, AZ2).

A ``token-env`` reference must never leak the token value into any generated
file: the block only names the env var, the value stays in the shell. The
canary is injected through the process environment of the real sync run.

Run: ``python3 -m pytest tests/test_test_environments_secrets_via_render.py``
"""

from __future__ import annotations

from tests.test_test_environments_render import (
    CONFIG_YAML,
    _role_texts,
    _sync_project,
)

CANARY = "canary-secret-8f3a91"


def test_no_token_value_in_any_generated_file(tmp_path):  # AC-ENV-6, AZ2
    project = _sync_project(
        tmp_path, extra_yaml=CONFIG_YAML, extra_env={"HA_DEV_TOKEN": CANARY}
    )
    for f in project.rglob("*"):
        if f.is_file() and ".git" not in f.parts:
            assert CANARY.encode() not in f.read_bytes(), f
    assert any("${HA_DEV_TOKEN}" in t for t in _role_texts(project).values())
    env_sh = (project / ".meta-config" / "env.sh").read_text(encoding="utf-8")
    assert "HA_DEV_TOKEN" in env_sh
    assert "[SECRET]" in env_sh
    assert CANARY not in env_sh
