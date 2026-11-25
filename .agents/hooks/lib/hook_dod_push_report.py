#!/usr/bin/env python3
"""Reporter for the deployed dod-push-check hook.

Issue #1238c1 (MB-1): every user-visible Branch-Guard/DoD-Check message and
the hook action it implies live here; the decisions themselves are in
``hook_dod_push_policy.py`` and the shell keeps only orchestration.  A scene
writes its message to the stream the hook has always used (stderr on every
blocking path, issue #593) and returns the hook action as its exit status —
an internal protocol with the shell, never surfaced as the hook's own status.

Scenes:
  ``branch <class_rc> <budget> <main_branch> <protected_display>``
      classifier verdict on stdin.  0 = continue to the test gate (tag/push),
      3 = allow, not a push, 2 = blocked (reason on stderr).
  ``gate <config_file> <test_cmd> <cache_file> <head_sha> <timeout> <has_timeout>``
      0 = run the tests now (the "Running ..." line is already printed),
      3 = allow, no config, 4 = allow, no TEST_COMMAND, 5 = allow, cached pass.
  ``result <test_rc> <timeout> <has_timeout> <test_cmd>``
      0 = passed, 2 = failed or timed out (reason on stderr).

This module is stdlib-only.
"""
from __future__ import annotations

import sys

from hook_dod_push_policy import (
    branch_verdict,
    cache_matches,
    test_gate_state,
    test_result_verdict,
)

# Exit statuses (internal protocol with the shell, see the module docstring).
# Each scene numbers its own outcomes, so equal values carry different
# meanings across scenes.
CONTINUE = 0
BLOCK = 2
NOT_A_PUSH = 3
NO_CONFIG = 3
NO_COMMAND = 4
CACHED = 5

_BLOCK_PREFIX = "Branch-Guard: Push blocked — "
_DISABLE_HINT = (
    "If this is intentional (release, hotfix), disable the hook temporarily:",
    "  Remove dod-push-check from hooks in .meta-config/project.yaml, "
    "re-sync, push, re-enable.",
)


def _write(stream, lines) -> None:
    """Write one message line per entry, exactly like the former ``echo``."""
    for line in lines:
        stream.write(line + "\n")


def _branch(args: list[str], stdin: str) -> int:
    if len(args) != 4:
        return 1
    class_rc, budget, main_branch, protected_display = args
    try:
        class_rc = int(class_rc)
    except ValueError:
        return 1
    # The shell passes the verdict as a here-string, which appends exactly one
    # newline to the command-substitution value; remove it again so the token
    # comparison stays byte-exact.
    verdict = stdin[:-1] if stdin.endswith("\n") else stdin
    action, value = branch_verdict(verdict, class_rc, budget)
    if action == "none":
        return NOT_A_PUSH
    if action in ("tag", "push"):
        return CONTINUE
    if action == "onbranch":
        _write(sys.stderr, (
            _BLOCK_PREFIX + "you are on '" + value + "'.",
            "Create a feature branch first: git checkout -b feat/<topic>",
            "Direct pushes to " + main_branch
            + " are not allowed by DoD policy.",
            "",
            *_DISABLE_HINT,
        ))
        return BLOCK
    _write(sys.stderr, (
        _BLOCK_PREFIX + value + ".",
        "Protected branches: " + protected_display
        + ". Push a feature branch and open a PR instead.",
        "",
        *_DISABLE_HINT,
    ))
    return BLOCK


def _read_cache(path: str) -> str | None:
    if not path:
        return None
    try:
        with open(path, encoding="utf-8", errors="surrogateescape") as handle:
            return handle.read()
    except OSError:
        return None


def _gate(args: list[str], stdin: str) -> int:
    del stdin
    if len(args) != 6:
        return 1
    config_file, test_cmd, cache_file, head_sha, timeout, has_timeout = args
    state = test_gate_state(config_file, test_cmd)
    if state == "no-config":
        _write(sys.stdout, (
            "DoD-Check: no project config found (.meta-config/project.yaml).",
            "The test gate could not be evaluated. Either run from within the project,",
            "or export AGENT_META_TEST_COMMAND='<your-test-command>' to enable it.",
            "Push allowed (Branch-Guard passed, but test gate was NOT enforced).",
        ))
        return NO_CONFIG
    if state == "no-command":
        _write(sys.stdout, (
            "DoD-Check: TEST_COMMAND not configured — skipping test gate.",
            "Set variables.TEST_COMMAND in .meta-config/project.yaml or",
            "export AGENT_META_TEST_COMMAND='<your-test-command>' to enable.",
            "Push allowed (Branch-Guard passed, no test gate configured).",
        ))
        return NO_COMMAND
    if cache_matches(_read_cache(cache_file), head_sha, test_cmd):
        _write(sys.stdout, (
            "DoD-Check: tests already passed for commit " + head_sha[:12]
            + " with this TEST_COMMAND (cached) — skipping re-run.",
            "Delete " + cache_file + " to force a re-run.",
        ))
        return CACHED
    _write(sys.stdout, (
        "DoD-Check: Running '" + test_cmd + "' (timeout: " + timeout + "s)...",
    ))
    if has_timeout == "0":
        _write(sys.stderr, (
            "DoD-Check: 'timeout' command not available on this system — "
            "running the test gate without a hard time limit.",
        ))
    return CONTINUE


def _result(args: list[str], stdin: str) -> int:
    del stdin
    if len(args) != 4:
        return 1
    test_rc, timeout, has_timeout, test_cmd = args
    try:
        test_rc = int(test_rc)
    except ValueError:
        return 1
    verdict = test_result_verdict(test_rc, has_timeout != "0")
    if verdict == "pass":
        _write(sys.stdout, ("DoD-Check passed.",))
        return CONTINUE
    if verdict == "timeout":
        _write(sys.stderr, (
            "",
            "DoD-Check TIMED OUT after " + timeout + "s: '" + test_cmd + "'.",
            "Raise the limit via variables.TEST_TIMEOUT in .meta-config/project.yaml "
            "(or AGENT_META_TEST_TIMEOUT), or fix a hanging test.",
            "Fix failing tests and retry, or disable the hook temporarily.",
        ))
        return BLOCK
    _write(sys.stderr, (
        "",
        "DoD-Check FAILED: Tests must pass before pushing.",
        "Fix failing tests and retry, or disable the hook temporarily.",
    ))
    return BLOCK


_SCENES = {
    "branch": _branch,
    "gate": _gate,
    "result": _result,
}


def main(argv: list[str], stdin: str) -> int:
    """Run one reporting scene and return the hook action as exit status."""
    if not argv:
        return 1
    scene = _SCENES.get(argv[0])
    if scene is None:
        return 1
    return scene(argv[1:], stdin)


if __name__ == "__main__":
    sys.exit(main(
        sys.argv[1:],
        sys.stdin.buffer.read().decode("utf-8", "surrogateescape"),
    ))
