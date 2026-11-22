"""Effective commit authority with an opt-in grant (issue #1181).

Spec: docs/specs/2026-11-09-commit-authority-grant-spec.md §3.2.
AC-1: a config key makes an Edit-only role eligible without touching agents/.

Both functions under test expect the NORMALIZED map ``{role: "direct"}``
(T2/K-8), not the config-object form. The grant only ever escalates
(``delegate``/``notify`` -> ``direct``, D17); it never downgrades.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.auto_commit import (  # noqa: E402
    AUTHORITY_DIRECT,
    is_role_eligible,
    role_commit_authority,
)

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
