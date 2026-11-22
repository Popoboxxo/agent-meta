"""scripts/lib/auto_commit.py: role commit-authority classification,
eligibility derivation and allowlist shape (issue #694, #767).

Authority is derived from each role's OWN template frontmatter tools: list --
never a hand-maintained list."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.auto_commit import (
    is_role_eligible,
    resolve_auto_commit_config,
    role_commit_authority,
)
from lib.config import load_config

_REPO_ROOT = Path(__file__).resolve().parent.parent


# --- issue #767: authority classification (AC2) -------------------------

def test_direct_authority_roles():
    for role in ("developer", "tester", "se-developer"):
        assert role_commit_authority(role, _REPO_ROOT) == "direct", role


def test_orchestrator_is_delegate():
    assert role_commit_authority("orchestrator", _REPO_ROOT) == "delegate"


def test_notify_authority_roles():
    for role in (
        "documenter",
        "copyeditor",
        "technical-writer",
        "concept-architect",
        "concept-specifier",
    ):
        assert role_commit_authority(role, _REPO_ROOT) == "notify", role


def test_none_authority_roles():
    for role in ("explorer", "git"):
        assert role_commit_authority(role, _REPO_ROOT) == "none", role


def test_authority_accepts_platform_none():
    assert role_commit_authority("developer", _REPO_ROOT, platform=None) == "direct"


# --- is_role_eligible is direct-only (AC1) ------------------------------

def test_developer_is_eligible():
    assert is_role_eligible("developer", _REPO_ROOT) is True


def test_tester_is_eligible():
    assert is_role_eligible("tester", _REPO_ROOT) is True


def test_git_is_not_eligible():
    # Bash but no Edit/Write -> "none", even though it has full commit authority.
    assert is_role_eligible("git", _REPO_ROOT) is False


def test_explorer_is_not_eligible():
    assert is_role_eligible("explorer", _REPO_ROOT) is False


def test_write_without_bash_is_not_eligible():
    # Previously eligible under the coarse Edit/Write check; must no longer be.
    for role in (
        "orchestrator",
        "documenter",
        "copyeditor",
        "technical-writer",
        "concept-architect",
    ):
        assert is_role_eligible(role, _REPO_ROOT) is False, role


def test_resolve_config_mode_off_still_computes_eligible_roles():
    result = resolve_auto_commit_config(
        config={"auto_commit": {"mode": "off"}},
        active_roles=["orchestrator", "developer", "git"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["mode"] == "off"
    assert result["eligible_roles"] == ["developer"]
    assert "git" not in result["eligible_roles"]
    assert "orchestrator" not in result["eligible_roles"]


def test_resolve_config_auto_mode_lists_only_eligible_active_roles():
    result = resolve_auto_commit_config(
        config={"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}},
        active_roles=["orchestrator", "developer", "git", "tester"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["mode"] == "auto"
    assert result["eligible_roles"] == ["developer", "tester"]
    assert result["triggers"] == ["task-boundary"]


def test_resolve_config_defaults_secret_scan_true():
    result = resolve_auto_commit_config(
        config={"auto_commit": {"mode": "auto", "triggers": ["per-edit"]}},
        active_roles=["developer"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["secret_scan"] is True


def test_resolve_config_suggest_mode_still_computes_eligible_roles():
    result = resolve_auto_commit_config(
        config={"auto_commit": {"mode": "suggest"}},
        active_roles=["orchestrator", "developer", "git", "tester"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["mode"] == "suggest"
    # AC3: direct-only in every mode -- orchestrator (delegate) is excluded.
    assert result["eligible_roles"] == ["developer", "tester"]


def test_resolve_config_custom_mode_lists_eligible_roles():
    result = resolve_auto_commit_config(
        config={"auto_commit": {"mode": "custom", "custom_script": "x.sh"}},
        active_roles=["orchestrator", "developer", "git"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["eligible_roles"] == ["developer"]


def test_resolve_config_missing_auto_commit_key_defaults_to_off():
    result = resolve_auto_commit_config(
        config={},
        active_roles=["orchestrator", "developer", "git"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["mode"] == "off"
    assert result["eligible_roles"] == ["developer"]
    assert "git" not in result["eligible_roles"]


def test_load_config_normalizes_unquoted_off_bool(tmp_path):
    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "project:\n  name: t\n  prefix: t\n  short: t\n"
        "auto_commit:\n  mode: off\n"
    )
    config = load_config(config_path)
    assert config["auto_commit"]["mode"] == "off"

    result = resolve_auto_commit_config(
        config=config,
        active_roles=["orchestrator", "developer", "git"],
        agent_meta_root=_REPO_ROOT,
    )
    assert result["mode"] == "off"
    assert result["eligible_roles"] == ["developer"]
    assert "git" not in result["eligible_roles"]


# --- issue #1181 (T4): grants carried into the allowlist artifact ----------


def _grant(role):
    return {role: {"authority": "direct", "acknowledge_full_shell": True}}


def _grant_config(*roles, mode="auto"):
    ac = {"mode": mode}
    if mode == "auto":
        ac["triggers"] = ["task-boundary"]
    overrides = {}
    for role in roles:
        overrides.update(_grant(role))
    ac["authority_overrides"] = overrides
    return {"auto_commit": ac}


def test_granted_notify_role_becomes_eligible():
    out = resolve_auto_commit_config(
        config=_grant_config("documenter"),
        active_roles=["documenter", "developer"],
        agent_meta_root=_REPO_ROOT,
    )
    assert out["eligible_roles"] == ["developer", "documenter"]


def test_grant_is_mode_independent():
    for mode in ("off", "suggest", "auto"):
        out = resolve_auto_commit_config(
            config=_grant_config("documenter", mode=mode),
            active_roles=["documenter", "developer"],
            agent_meta_root=_REPO_ROOT,
        )
        # D20: capability is mode-independent; only rendering is skipped.
        assert out["eligible_roles"] == ["developer", "documenter"], mode


def test_artifact_carries_only_active_grants():
    out = resolve_auto_commit_config(
        config=_grant_config("documenter", "planner"),
        active_roles=["documenter"],
        agent_meta_root=_REPO_ROOT,
    )
    assert out["authority_overrides"] == {"documenter": "direct"}


def test_artifact_version_is_two():
    out = resolve_auto_commit_config(
        config=_grant_config("documenter"),
        active_roles=["documenter"],
        agent_meta_root=_REPO_ROOT,
    )
    assert out["version"] == 2


def test_grant_without_roles_key_has_no_effect():
    out = resolve_auto_commit_config(
        config=_grant_config("documenter"),
        active_roles=[],
        agent_meta_root=_REPO_ROOT,
    )
    assert out["eligible_roles"] == []
    assert out["authority_overrides"] == {}


def test_grant_without_ack_triggers_fail_safe():
    cfg = {"auto_commit": {
        "mode": "auto", "triggers": ["task-boundary"],
        "authority_overrides": {"documenter": {"authority": "direct"}},
    }}
    out = resolve_auto_commit_config(
        config=cfg,
        active_roles=["documenter", "developer"],
        agent_meta_root=_REPO_ROOT,
    )
    assert out["mode"] == "off"
    assert out["eligible_roles"] == []
    assert out["authority_overrides"] == {}


def test_invalid_grant_triggers_fail_safe():
    out = resolve_auto_commit_config(
        config=_grant_config("explorer"),
        active_roles=["explorer", "developer"],
        agent_meta_root=_REPO_ROOT,
    )
    assert out["mode"] == "off"
    assert out["eligible_roles"] == []
    assert out["authority_overrides"] == {}


def test_fail_safe_artifact_shape_includes_grant_map():
    # Schema-invalid block (triggers with mode: off) -> fail-safe artifact.
    cfg = {"auto_commit": {"mode": "off", "triggers": ["task-boundary"]}}
    out = resolve_auto_commit_config(
        config=cfg,
        active_roles=["developer"],
        agent_meta_root=_REPO_ROOT,
    )
    assert "authority_overrides" in out
    assert out["authority_overrides"] == {}
