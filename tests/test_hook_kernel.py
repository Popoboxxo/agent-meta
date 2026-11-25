"""Contract tests for the provider-neutral hook kernel (issue #1257, step 1).

The kernel is a stdlib-only Python package under hooks/1-generic/lib/kernel/.
It defines the NormEvent/Decision contract from the approved concept
(docs/analysis/2026-11-14-fable-provider-hooks-audit.md section D.2) and the
first pure-Python gates. It is NOT yet wired into the shell hooks — that
rewiring is a later migration step and stays outside this bundle.

Run: python -m pytest tests/test_hook_kernel.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_LIB_DIR = Path(__file__).resolve().parent.parent / "hooks" / "1-generic" / "lib"
sys.path.insert(0, str(_LIB_DIR))

import kernel  # noqa: E402
from kernel import containment, git_gate, identity, model  # noqa: E402


# ---------------------------------------------------------------------------
# model — NormEvent / Decision contract
# ---------------------------------------------------------------------------
class TestModel:
    def test_project_dir_contract_is_adapter_owned(self):
        contract = f"{model.__doc__}\n{model.NormEvent.__doc__}"
        assert "AM_PROJECT_DIR" in contract
        assert "CLAUDE_PROJECT_DIR" not in contract

    def test_norm_event_defaults(self):
        ev = model.NormEvent(tool_kind="read")
        assert ev.tool_kind == "read"
        assert ev.path is None
        assert ev.command is None
        assert ev.cwd is None
        assert ev.project_dir is None
        assert ev.agent_id is None
        assert ev.declared_agent is None
        assert ev.identity_source == "none"
        assert ev.event == ""

    def test_invalid_tool_kind_is_rejected(self):
        with pytest.raises(ValueError):
            model.NormEvent(tool_kind="teleport")

    def test_invalid_identity_source_is_rejected(self):
        with pytest.raises(ValueError):
            model.NormEvent(tool_kind="read", identity_source="guess")

    def test_decision_outcomes(self):
        assert model.Decision.allow("ok").outcome == "allow"
        assert model.Decision.deny("blocked").outcome == "deny"
        asked = model.Decision.ask("needs confirmation")
        assert asked.outcome == "ask"
        assert asked.reason == "needs confirmation"

    def test_decision_audit_is_not_shared(self):
        one = model.Decision.allow("ok")
        two = model.Decision.allow("ok")
        one.audit["x"] = 1
        assert "x" not in two.audit


# ---------------------------------------------------------------------------
# identity — explicit identity_source (concept D.4)
# ---------------------------------------------------------------------------
class TestIdentity:
    def test_harness_agent_id_is_authoritative(self):
        ev = model.NormEvent(
            tool_kind="shell", agent_id="abc123", identity_source="harness"
        )
        ident = identity.resolve_identity(ev)
        assert ident.source == "harness"
        assert ident.agent_id == "abc123"
        assert ident.role is None

    def test_sentinel_is_self_declared_only(self):
        ev = model.NormEvent(
            tool_kind="shell", declared_agent="git", identity_source="sentinel"
        )
        ident = identity.resolve_identity(ev)
        assert ident.source == "sentinel"
        assert ident.role == "git"
        assert ident.agent_id is None

    def test_none_source_has_no_attribution(self):
        ev = model.NormEvent(tool_kind="shell", identity_source="none")
        ident = identity.resolve_identity(ev)
        assert ident.source == "none"
        assert ident.agent_id is None
        assert ident.role is None

    def test_harness_discards_sentinel(self):
        ev = model.NormEvent(
            tool_kind="shell",
            agent_id="abc123",
            declared_agent="git",
            identity_source="harness",
        )
        ident = identity.resolve_identity(ev)
        assert ident.role is None
        assert ident.agent_id == "abc123"


# ---------------------------------------------------------------------------
# containment — path containment against project_dir
# ---------------------------------------------------------------------------
class TestContainment:
    def test_contract_is_adapter_owned(self):
        assert "AM_PROJECT_DIR" in containment.__doc__
        assert "CLAUDE_PROJECT_DIR" not in containment.__doc__

    def test_write_inside_root_is_allowed(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        (root / "sub").mkdir()
        ev = model.NormEvent(
            tool_kind="write", path=str(root / "sub" / "f.txt"),
            project_dir=str(root),
        )
        dec = containment.check_containment(ev)
        assert dec is not None and dec.outcome == "allow"
        assert dec.audit["root"] == str(root.resolve())

    def test_write_outside_root_is_denied(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        ev = model.NormEvent(
            tool_kind="write", path=str(tmp_path / "outside.txt"),
            project_dir=str(root),
        )
        dec = containment.check_containment(ev)
        assert dec is not None and dec.outcome == "deny"
        assert dec.reason == "containment.outside-root"

    def test_relative_path_resolves_against_cwd(self, tmp_path):
        root = tmp_path / "project"
        (root / "sub").mkdir(parents=True)
        ev = model.NormEvent(
            tool_kind="write", path="sub/f.txt", cwd=str(root),
            project_dir=str(root),
        )
        dec = containment.check_containment(ev)
        assert dec is not None and dec.outcome == "allow"

    def test_parent_traversal_escape_is_denied(self, tmp_path):
        root = tmp_path / "project"
        (root / "sub").mkdir(parents=True)
        ev = model.NormEvent(
            tool_kind="write", path="../escape.txt", cwd=str(root),
            project_dir=str(root),
        )
        dec = containment.check_containment(ev)
        assert dec is not None and dec.outcome == "deny"

    def test_nested_meta_checkout_is_denied(self, tmp_path):
        root = tmp_path / "project"
        (root / ".agent-meta").mkdir(parents=True)
        ev = model.NormEvent(
            tool_kind="write", path=str(root / ".agent-meta" / "config.py"),
            project_dir=str(root),
        )
        dec = containment.check_containment(ev)
        assert dec is not None and dec.outcome == "deny"
        assert dec.reason == "containment.meta-submodule"

    def test_missing_project_dir_fails_closed(self, tmp_path):
        ev = model.NormEvent(tool_kind="write", path=str(tmp_path / "f.txt"))
        dec = containment.check_containment(ev)
        assert dec is not None and dec.outcome == "deny"
        assert dec.reason == "containment.no-project-dir"

    def test_non_write_event_defers(self, tmp_path):
        ev = model.NormEvent(tool_kind="read", path=str(tmp_path / "f.txt"))
        assert containment.check_containment(ev) is None

    def test_write_without_path_defers(self, tmp_path):
        ev = model.NormEvent(tool_kind="write", project_dir=str(tmp_path))
        assert containment.check_containment(ev) is None


# ---------------------------------------------------------------------------
# git_gate — git command classification (grounded in orchestrator-guard)
# ---------------------------------------------------------------------------
class TestGitGate:
    @pytest.mark.parametrize(
        "command,category,scope",
        [
            ("git status", "none", "narrow"),
            ("git push origin main", "mutation", "broad"),
            ("git push --force origin main", "destructive", "broad"),
            ("git commit -m hello", "mutation", "narrow"),
            ("git commit --amend -m x", "mutation", "broad"),
            ("git reset --hard", "destructive", "broad"),
            ("git stash list", "none", "narrow"),
            ("git stash drop", "destructive", "broad"),
            ("git config --get user.name", "none", "narrow"),
            ("git config --add x y", "mutation", "broad"),
            ("echo git push origin main", "none", "narrow"),
            ("sudo git push origin main", "mutation", "broad"),
            ("git -C /tmp push origin main", "mutation", "broad"),
            ("git -c core.pager=cat status", "destructive", "broad"),
            ("git -c gc.reflogExpire=now status", "destructive", "broad"),
        ],
    )
    def test_classify(self, command, category, scope):
        result = git_gate.classify_git(command)
        assert (result.category, result.scope) == (category, scope)

    def test_empty_command_is_none(self):
        assert git_gate.classify_git("").category == "none"
        assert git_gate.classify_git(None).category == "none"


# ---------------------------------------------------------------------------
# decide(NormEvent) -> Decision dispatcher
# ---------------------------------------------------------------------------
class TestDecide:
    def test_read_is_allowed(self):
        dec = kernel.decide(model.NormEvent(tool_kind="read", command="cat f"))
        assert dec.outcome == "allow"

    def test_write_outside_root_is_denied(self, tmp_path):
        root = tmp_path / "project"
        root.mkdir()
        ev = model.NormEvent(
            tool_kind="write", path=str(tmp_path / "f"), project_dir=str(root)
        )
        assert kernel.decide(ev).outcome == "deny"

    def test_shell_mutation_is_denied(self):
        ev = model.NormEvent(tool_kind="shell", command="git push origin main")
        dec = kernel.decide(ev)
        assert dec.outcome == "deny"
        assert dec.reason == "git.mutation"

    def test_shell_destructive_is_denied(self):
        ev = model.NormEvent(tool_kind="shell", command="git reset --hard")
        assert kernel.decide(ev).reason == "git.destructive"

    def test_shell_readonly_git_is_allowed(self):
        ev = model.NormEvent(tool_kind="shell", command="git status")
        assert kernel.decide(ev).outcome == "allow"

    def test_dispatch_worktree_is_denied(self):
        ev = model.NormEvent(
            tool_kind="dispatch", command='agent_task(isolation="worktree")'
        )
        assert kernel.decide(ev).outcome == "deny"

    def test_dispatch_orchestrator_respawn_is_denied(self):
        ev = model.NormEvent(
            tool_kind="dispatch", command="subagent -> orchestrator"
        )
        assert kernel.decide(ev).outcome == "deny"

    def test_dispatch_normal_is_allowed(self):
        ev = model.NormEvent(tool_kind="dispatch", command="agent_task(role=developer)")
        assert kernel.decide(ev).outcome == "allow"

    def test_unknown_tool_kind_is_denied(self):
        ev = model.Decision.deny("x")  # not a NormEvent -> fail closed
        with pytest.raises((TypeError, AttributeError, ValueError)):
            kernel.decide(ev)
