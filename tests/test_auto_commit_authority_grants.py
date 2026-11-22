"""Effective commit authority with an opt-in grant (issue #1181).

Spec: docs/specs/2026-11-09-commit-authority-grant-spec.md §3.2.
AC-1: a config key makes an Edit-only role eligible without touching agents/.

Both functions under test expect the NORMALIZED map ``{role: "direct"}``
(T2/K-8), not the config-object form. The grant only ever escalates
(``delegate``/``notify`` -> ``direct``, D17); it never downgrades.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.auto_commit import (  # noqa: E402
    AUTHORITY_DIRECT,
    is_role_eligible,
    role_commit_authority,
)
from lib.frontmatter import _parse_frontmatter_yaml  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _effective(role: str, platform=None, authority_overrides=None) -> str:
    """Call the T3 function via a lazy import so the red phase is 8 failures
    (not one module-level collection error)."""
    from lib.auto_commit import effective_commit_authority  # noqa: E402

    return effective_commit_authority(role, _REPO_ROOT, platform, authority_overrides)


_GENERIC_DIR = _REPO_ROOT / "agents" / "1-generic"
_EXCLUDED = {"_README.md", "_reference-agent.md", "_wf-orchestrator-reference.md"}
_DEPLOYABLE = sorted(
    path.stem for path in _GENERIC_DIR.glob("*.md") if path.name not in _EXCLUDED
)


def test_notify_role_escalates_to_direct():
    assert _effective("documenter", None, {"documenter": "direct"}) == "direct"


def test_delegate_role_escalates_to_direct():
    assert _effective("orchestrator", None, {"orchestrator": "direct"}) == "direct"


def test_no_override_is_identity():
    assert len(_DEPLOYABLE) == 98
    for role in _DEPLOYABLE:
        derived = role_commit_authority(role, _REPO_ROOT)
        assert _effective(role) == derived, role
        assert _effective(role, None, None) == derived, role


def test_derived_direct_is_noop():
    assert _effective("developer", None, {"developer": "direct"}) == "direct"


def test_read_only_role_never_escalates():
    assert _effective("explorer", None, {"explorer": "direct"}) == "none"


def test_override_for_other_role_does_not_leak():
    assert _effective("documenter", None, {"planner": "direct"}) == "notify"


def test_non_mapping_or_unknown_value_never_raises():
    derived = role_commit_authority("documenter", _REPO_ROOT)
    for overrides in (["x"], {"documenter": "notify"}, {}):
        assert _effective("documenter", None, overrides) == derived


def test_is_role_eligible_matches_effective_authority():
    # role -> (eligible without grant, eligible with grant)
    expected = {
        "documenter": (False, True),    # notify -> direct
        "orchestrator": (False, True),  # delegate -> direct
        "developer": (True, True),      # direct stays direct (no-op)
        "explorer": (False, False),     # none never escalates
        "git": (False, False),          # none never escalates
    }
    for role, (without, with_grant) in expected.items():
        assert without == (_effective(role, None, None) == AUTHORITY_DIRECT), role
        granted = {role: "direct"}
        assert with_grant == (_effective(role, None, granted) == AUTHORITY_DIRECT), role
        assert is_role_eligible(role, _REPO_ROOT, None, None) == without, role
        assert is_role_eligible(role, _REPO_ROOT, None, granted) == with_grant, role


# --------------------------------------------------------------------------- #
# T6 (issue #1181): provider-hook / active-guard gated Bash render              #
# --------------------------------------------------------------------------- #

def _resolve(role: str, resolved: dict, pc, *, guard_enabled: bool = True) -> tuple[str, bool]:
    """Call T6 via a lazy import so the red phase is 10 failures (not one
    module-level collection error)."""
    from lib.auto_commit import resolve_commit_grant  # noqa: E402

    return resolve_commit_grant(
        role, resolved, pc, _REPO_ROOT, guard_enabled=guard_enabled
    )


def _granted(mode: str = "auto", role: str = "documenter") -> dict:
    """A resolved auto_commit block with a NORMALIZED direct grant (T2)."""
    return {"mode": mode, "authority_overrides": {role: "direct"}}


_HOOKED = {"has_hooks": True, "hook_protocol": "claude-code-json"}
_ANTIGRAVITY = {"has_hooks": True, "hook_protocol": "antigravity-hooks-json"}


def test_grant_on_hook_provider_renders_bash():
    assert _resolve("documenter", _granted(), _HOOKED) == ("direct", True)


def test_grant_on_antigravity_provider_renders_bash():
    assert _resolve("documenter", _granted(), _ANTIGRAVITY) == ("direct", True)


def test_grant_on_hookless_provider_does_not_render():
    # No verified hook ⇒ gate downgrades the grant to the derived authority (D21).
    assert _resolve("documenter", _granted(), {"has_hooks": False}) == ("notify", False)


def test_grant_on_provider_without_verified_protocol_does_not_render():
    # Mammouth (config/ai-providers.yaml:622) / Codex (:734) form: no protocol.
    pc = {"has_hooks": True, "hook_protocol": None}
    assert _resolve("documenter", _granted(), pc) == ("notify", False)


def test_grant_under_off_and_suggest_does_not_render():
    # D20: off/suggest always yield (derived, False).
    for mode in ("off", "suggest"):
        assert _resolve("documenter", _granted(mode), _HOOKED) == ("notify", False), mode


def test_grant_without_active_guard_does_not_render():
    # RVW-1181-01: guard disabled ⇒ fail closed even on a verified hook provider.
    resolved = _granted()
    assert _resolve("documenter", resolved, _HOOKED, guard_enabled=False) == ("notify", False)


def test_derived_direct_role_never_needs_bash_injection():
    # K-3: developer's DERIVED authority is already direct; no Bash injection.
    assert _resolve("developer", _granted(role="developer"), _HOOKED) == ("direct", False)


def test_none_capabilities_fail_closed():
    # No exception; no verified hook ⇒ (derived, False).
    assert _resolve("documenter", _granted(), None) == ("notify", False)


def test_grant_under_suggest_is_never_rendered():
    # D20: suggest is propose-only — never rendered, even with an active guard.
    assert _resolve("documenter", _granted("suggest"), _HOOKED) == ("notify", False)


def test_grant_in_mixed_provider_set_renders_on_hook_provider():
    # D21: resolution is per provider; the caller invokes once per provider.
    resolved = _granted()
    assert _resolve("documenter", resolved, _HOOKED) == ("direct", True)
    assert _resolve("documenter", resolved, {"has_hooks": False}) == ("notify", False)


# --------------------------------------------------------------------------- #
# T8 (issue #1181): provider gate + Bash injection before the provider         #
# transform + sync.log contracts. Real-subprocess syncs (pattern:              #
# tests/test_auto_commit_allowlist_pipeline.py:13-43).                         #
# --------------------------------------------------------------------------- #

_GRANT_YAML = (
    "  authority_overrides:\n"
    "    documenter:\n"
    "      authority: direct\n"
    "      acknowledge_full_shell: true\n"
)

_CLAUDE_INFO = (
    "auto-commit-grant: documenter=direct "
    "(source: auto_commit.authority_overrides; hook-enforced: yes)"
)
_HOOKLESS_WARN = (
    "auto-commit-grant: documenter=direct not enforced on provider 'Opencode' "
    "(has_hooks=false); rendered as notify (issue #1181)"
)
_GUARD_OFF_WARN = (
    "auto-commit-grant: documenter=direct not enforced "
    "(guard hook disabled: hooks.orchestrator-guard.enabled is not true); "
    "rendered as notify (issue #1181)"
)


def _write_project(project: Path, *, providers: str = "[Claude]",
                   roles: str = "[orchestrator, developer, documenter]",
                   grant: bool = True, mode: str = "auto",
                   guard_disabled: bool = False) -> None:
    """Write a minimal project.yaml for a real sync subprocess."""
    auto = f"auto_commit:\n  mode: {mode}\n  triggers: [task-boundary]\n"
    if grant:
        auto += _GRANT_YAML
    hooks = "hooks:\n  orchestrator-guard:\n    enabled: false\n" if guard_disabled else ""
    cfg = (
        "project:\n  name: t\n  prefix: t\n"
        f"ai-providers: {providers}\n"
        f"roles: {roles}\n"
        + hooks + auto
    )
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    (project / ".meta-config" / "project.yaml").write_text(cfg, encoding="utf-8")


def _run_sync(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py")],
        cwd=project, capture_output=True, text=True, timeout=180,
    )


def _sync_log(project: Path) -> str:
    return (project / "sync.log").read_text(encoding="utf-8")


def _frontmatter_tools(text: str) -> list:
    return list(_parse_frontmatter_yaml(text).get("tools") or [])


def _agent_text(project: Path, provider_dir: str, role: str = "documenter") -> str:
    path = project / provider_dir / "agents" / f"{role}.md"
    assert path.exists(), path
    return path.read_text(encoding="utf-8")


def test_claude_documenter_gains_bash_when_granted(tmp_path):
    _write_project(tmp_path)
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    doc = _agent_text(tmp_path, ".claude")
    assert "Bash" in _frontmatter_tools(doc)          # frontmatter `- Bash`
    assert "Granted by project config" in doc          # grant line in the body
    assert "issue #1181" in doc
    assert _CLAUDE_INFO in _sync_log(tmp_path)


def test_claude_documenter_without_grant_keeps_bash_deny(tmp_path):
    _write_project(tmp_path, grant=False)
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    doc = _agent_text(tmp_path, ".claude")
    assert "Bash" not in _frontmatter_tools(doc)
    assert "issue #1181" not in doc
    assert "auto-commit-grant:" not in _sync_log(tmp_path)


def test_claude_grant_with_disabled_guard_keeps_bash_deny(tmp_path):
    _write_project(tmp_path, guard_disabled=True)
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    doc = _agent_text(tmp_path, ".claude")
    assert "Bash" not in _frontmatter_tools(doc)
    assert "issue #1181" not in doc
    log = _sync_log(tmp_path)
    assert _GUARD_OFF_WARN in log
    assert _CLAUDE_INFO not in log  # N-1: no hook-enforced INFO anywhere


def test_opencode_v1_documenter_bash_deny_by_default(tmp_path):
    _write_project(tmp_path, providers="[Opencode]", grant=False)
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    doc = _agent_text(tmp_path, ".opencode")
    # The only real Opencode render case (K-12): shell stays denied.
    assert ("bash: deny" in doc) or ("action: shell" in doc and "effect: deny" in doc)
    assert "Bash" not in _frontmatter_tools(doc)


def test_render_bash_on_synthetic_hook_capable_fixture():
    from lib.agent_sync import _apply_role_auto_commit_overrides  # noqa: E402

    merged: dict = {}
    variables = {
        "_AUTO_COMMIT_RESOLVED": {
            "mode": "auto", "authority_overrides": {"documenter": "direct"},
        }
    }
    render_bash = _apply_role_auto_commit_overrides(
        merged, "documenter", _REPO_ROOT, variables,
        config={}, provider="Claude",
        provider_capabilities={"has_hooks": True, "hook_protocol": "claude-code-json"},
        log=None, guard_off_logged=set(),
    )
    assert render_bash is True
    assert "Granted by project config" in merged["AUTO_COMMIT_BLOCK"]
    assert "issue #1181" in merged["AUTO_COMMIT_BLOCK"]


def test_hookless_provider_renders_derived_and_warns(tmp_path):
    # A mixed set keeps the block valid (D21): the hookless provider renders the
    # DERIVED authority and gets its own WARN; Claude carries the INFO.
    _write_project(tmp_path, providers="[Claude, Opencode]")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    doc = _agent_text(tmp_path, ".opencode")
    assert ("bash: deny" in doc) or ("action: shell" in doc and "effect: deny" in doc)
    assert "Do NOT run `git` yourself" in doc          # derived notify prose
    assert "issue #1181" not in doc                    # no grant line
    log = _sync_log(tmp_path)
    assert _HOOKLESS_WARN in log
    assert "Granted by project config" not in doc


def test_grant_log_line_on_claude(tmp_path):
    _write_project(tmp_path)
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    assert _CLAUDE_INFO in _sync_log(tmp_path)


def test_mixed_provider_set_logs_info_and_warn(tmp_path):
    _write_project(tmp_path, providers="[Claude, Opencode]")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    log = _sync_log(tmp_path)
    assert log.count("hook-enforced: yes") == 1
    assert log.count("not enforced on provider 'Opencode'") == 1
    # D21: the hook-capable provider renders, the hookless one stays notify.
    assert "Bash" in _frontmatter_tools(_agent_text(tmp_path, ".claude"))
    assert "Bash" not in _frontmatter_tools(_agent_text(tmp_path, ".opencode"))


def test_suggest_renders_no_grant_line_and_no_bash(tmp_path):
    _write_project(tmp_path, mode="suggest")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    doc = _agent_text(tmp_path, ".claude")
    assert "Bash" not in _frontmatter_tools(doc)
    assert "issue #1181" not in doc
    log = _sync_log(tmp_path)
    assert "hook-enforced: yes" not in log
    assert "auto-commit-grant:" not in log             # D20: both lines silent


def test_grant_on_inactive_role_is_logged_as_info(tmp_path):
    # D22: the notice comes from authority_override_notices (§4.3) on --validate.
    _write_project(tmp_path, roles="[developer]", grant=False)
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "project:\n  name: t\n  prefix: t\n"
        "ai-providers: [Claude]\n"
        "roles: [developer]\n"
        "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n"
        "  authority_overrides:\n"
        "    planner:\n"
        "      authority: direct\n"
        "      acknowledge_full_shell: true\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--validate"],
        cwd=tmp_path, capture_output=True, text=True, timeout=180,
    )
    output = result.stdout + result.stderr
    assert "grant ignored — role is not active" in output


def test_gemini_grant_maps_to_run_command(tmp_path):
    _write_project(tmp_path, providers="[Gemini]")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    doc = _agent_text(tmp_path, ".gemini")
    assert "run_command" in doc
    assert "code_execution" not in doc


def test_ungranted_roles_render_byte_identical(tmp_path):
    with_grant = tmp_path / "with"
    without = tmp_path / "without"
    _write_project(with_grant, grant=True)
    _write_project(without, grant=False)
    r1 = _run_sync(with_grant)
    r2 = _run_sync(without)
    assert r1.returncode == 0, r1.stderr
    assert r2.returncode == 0, r2.stderr
    d1 = with_grant / ".claude" / "agents"
    d2 = without / ".claude" / "agents"
    names = {p.name for p in d1.glob("*.md")} - {"documenter.md"}
    assert names
    for name in sorted(names):
        assert (d1 / name).read_bytes() == (d2 / name).read_bytes(), name


def test_hookless_only_failsafe_logs_hookless_warn(tmp_path):
    # Review F3 (hookless seam): a single hookless provider + a well-formed
    # grant triggers the non-enforcement fail-safe. The recovered grant must
    # still emit the byte-exact §4.6 hookless WARN.
    _write_project(tmp_path, providers="[Opencode]")
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    log = _sync_log(tmp_path)
    assert _HOOKLESS_WARN in log
    assert "hook-enforced: yes" not in log
    # Fail-safe rendering is untouched: no grant line on the agent.
    assert "issue #1181" not in _agent_text(tmp_path, ".opencode")


def test_hooked_provider_structural_failsafe_has_no_false_hookless_warn(tmp_path):
    # Review F3 (hooked seam): a single HOOKED provider, an active guard and a
    # well-formed grant, but an unrelated structural violation forces the
    # fail-safe. A `has_hooks=false` WARN here would be a false positive (F2).
    _write_project(tmp_path, providers="[Claude]")
    cfg_path = tmp_path / ".meta-config" / "project.yaml"
    cfg_path.write_text(
        cfg_path.read_text(encoding="utf-8").replace(
            "  triggers: [task-boundary]\n",
            "  triggers: [task-boundary]\n  file_count_threshold: 0\n",
        ),
        encoding="utf-8",
    )
    result = _run_sync(tmp_path)
    assert result.returncode == 0, result.stderr
    log = _sync_log(tmp_path)
    assert "not enforced on provider" not in log
    assert "guard hook disabled" not in log
    assert "hook-enforced: yes" not in log
    assert "issue #1181" not in _agent_text(tmp_path, ".claude")
