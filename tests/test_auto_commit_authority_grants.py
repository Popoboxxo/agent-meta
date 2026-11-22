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
