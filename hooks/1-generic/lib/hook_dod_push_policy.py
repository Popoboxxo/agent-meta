#!/usr/bin/env python3
"""Pure decision rules for the deployed dod-push-check hook.

Issue #1238c1 (MB-1): the Branch-Guard verdict mapping, the test-gate state
machine, the result-cache key and the test-result classification were the last
decision tables left in the hook's Bash body.  They live here as side-effect
free functions so they can be unit-tested without starting a hook process; the
reporter (``hook_dod_push_report.py``) renders the messages and the shell keeps
only orchestration.  This module is stdlib-only and never touches the
filesystem, so a verdict can never depend on ambient state.
"""
from __future__ import annotations

# The classifier's own error path already prints "block <reason>"; anything
# that is neither a known token nor a "block "/"onbranch " line is treated as
# a broken classifier and blocks with this reason.
FALLBACK_REASON = "push classification failed (fail closed)"


def branch_verdict(output: str, rc: int, budget: str) -> tuple[str, str]:
    """Map the classifier's one-line verdict to ``(action, value)``.

    ``output`` is the exact command-substitution value (no trailing newline).
    A plain ``none``/``tag``/``push`` line wins over ``rc`` — that is the order
    the former ``case`` statement applied.  An ``onbranch `` prefix carries the
    branch name in ``value``.  Everything else is a ``block`` whose reason is
    the ``block `` payload, or the fail-closed fallback when the first word is
    not ``block``.  A classifier killed by the time budget (rc 124) overrides
    every block reason with the budget message.
    """
    if output == "none":
        return "none", ""
    if output == "tag":
        return "tag", ""
    if output == "push":
        return "push", ""
    if output.startswith("onbranch "):
        return "onbranch", output[len("onbranch "):]
    if rc == 124:
        return "block", "push classification exceeded " + budget + "s (fail closed)"
    reason = output[len("block "):] if output.startswith("block ") else output
    if output.split(" ")[0] != "block":
        reason = FALLBACK_REASON
    return "block", reason


def test_gate_state(config_file: str, test_cmd: str) -> str:
    """Return ``run``, ``no-config`` or ``no-command`` for the test gate.

    A configured command always wins; without one, a missing config file is
    reported as its own state so the user learns the gate was not evaluated
    instead of seeing a silent skip.
    """
    if test_cmd:
        return "run"
    return "no-command" if config_file else "no-config"


def cache_matches(content: str | None, head_sha: str, test_cmd: str) -> bool:
    """Whether a cached pass belongs to this commit and test command.

    ``content`` is the cache file's text (``None`` when absent, unreadable or
    no cache path exists).  Trailing newlines are ignored on the file side,
    like the former ``$(cat)`` command substitution; the expected key itself is
    compared verbatim, so any change to the commit or the command invalidates
    the cache.
    """
    if content is None or not head_sha:
        return False
    return content.rstrip("\n") == head_sha + "\n" + test_cmd


def test_result_verdict(rc: int, timeout_available: bool) -> str:
    """Return ``pass``, ``timeout`` or ``fail`` for a finished test run.

    rc 124 only means "timed out" when a real ``timeout`` binary was used; a
    test suite that exits 124 on its own is reported as a plain failure.
    """
    if rc == 0:
        return "pass"
    if rc == 124 and timeout_available:
        return "timeout"
    return "fail"
