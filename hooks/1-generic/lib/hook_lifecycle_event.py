#!/usr/bin/env python3
"""Lifecycle-event detection for the deployed lifecycle-check hook.

MB-2 of docs/plans/systemaudit-umsetzungsplan-2026-11-25.md: the hook decided
"was this a git push / commit / merge?" with ``grep -qE`` over the raw Bash
command string. A raw-text match cannot tell a command word from an argument,
so ``echo "git push"``, ``grep git push README`` or a tag name passed to an
unrelated program raised lifecycle events, while a hidden (quoted, wrapped)
real command could be missed. This module classifies each shell statement with
the shared tokenizer instead:

* ``hook_shell_scan.split_shell_statements`` -- statement split on control
  operators outside quotes, comments dropped, heredoc bodies removed and
  ``$(...)``/backtick bodies emitted as statements of their own;
* ``hook_shell_resolver.command_start`` -- the real command word after shell
  keywords, grouping, assignments, function headers and command wrappers
  (``sudo``, ``env``, ``timeout``, ``xargs``, ...);
* ``hook_push_arg_parser.walk_push_args`` -- the shared push option/positional
  walk, so ``-o --tags`` stays a push option value and not the ``--tags`` flag.

Output contract (one line on stdout, consumed by lifecycle-check.sh):
``none`` | ``on-release`` | ``on-version-bump-patch`` |
``on-version-bump-minor`` | ``on-version-bump-major`` | ``on-merge``.

Semantics carried over from the former shell version:

* ``on-release``: a real ``git push`` statement that carries ``--tags``/
  ``--tag`` or a ``vX.Y.Z`` tag ref (``git push origin v1.2.3``,
  ``git push origin refs/tags/v1.2.3``);
* ``on-version-bump-*``: a real ``git commit`` statement whose ``-m``/
  ``--message`` text matches the former bump heuristic
  (``bump.*version`` / ``version.*bump`` / ``chore.*bump``, case-insensitive)
  and names a ``X.Y.Z`` version. The bump kind is the former shell
  comparison against ``git describe --tags --abbrev=0 HEAD~1``: a different
  major is *major*, a different minor is *minor*, everything else -- and a
  missing previous tag -- is *patch*;
* ``on-merge``: a real ``git merge`` statement, or ``gh pr merge``;
* precedence stays release > version bump > merge, the former ``elif`` order.

Deliberately unchanged: a plain ``git commit`` never yields an event. The old
``on-commit`` arm sat behind the earlier ``git commit`` arm and was therefore
unreachable; keeping it unreachable preserves the observable behaviour (a
follow-up can make ``on-commit`` fire if that is wanted).

Known limit (shared with the other hooks): an opaque command string such as
``bash -c "git push origin v1.2.3"`` or ``eval ...`` is not executed or parsed
(see the hook_shell_scan docstring); an unparseable statement (unbalanced
quote) is skipped. Both mean "no event", i.e. fail open -- this hook is
informational automation, not a security boundary.
"""
from __future__ import annotations

import os
import re
import shlex
import subprocess
import sys

from hook_push_arg_parser import walk_push_args
from hook_shell_resolver import command_start
from hook_shell_scan import split_shell_statements

NO_EVENT = "none"
RELEASE = "on-release"
MERGE = "on-merge"
BUMP_PATCH = "on-version-bump-patch"
BUMP_MINOR = "on-version-bump-minor"
BUMP_MAJOR = "on-version-bump-major"

# git global options that consume a separate value token, so
# `git -C <path> push` still resolves its subcommand. Mirrors
# GLOBAL_OPTS_WITH_VALUE in hook_dod_push_classify.py (the push guard's
# authoritative copy) -- kept local because this module must stay importable
# without the push classifier.
GIT_OPTS_WITH_VALUE = {
    "-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path",
    "--super-prefix", "--config-env", "--attr-source", "--config",
}
# push options the shared walk must consume a value for; only the resulting
# positionals matter here.
PUSH_OPTS_WITH_VALUE = {"--push-option", "--repo", "--receive-pack", "--exec",
                        "--recurse-submodules"}
# `--tag` is a git-recognised synonym of `--tags`; both mark a tag push.
TAG_FLAGS = {"--tags", "--tag"}
# Tag refs the former shell matched anywhere in the command (`v1.2.3`).
TAG_REF = re.compile(r"v\d+\.\d+\.\d+")
VERSION = re.compile(r"\d+\.\d+\.\d+")
# Former `grep -qiE 'bump.*version|version.*bump|chore.*bump'`: line-based,
# so no DOTALL -- `.` must not cross a newline inside a message.
BUMP_TEXT = re.compile(r"bump.*version|version.*bump|chore.*bump", re.I)
GIT_WORDS = ("git", "git-push")


def tokens(statement):
    """Tokenize one statement like the shell (quotes, escapes, punctuation).

    Raises ValueError on an unbalanced quote; the caller skips such a
    statement (fail open for this informational hook).
    """
    lex = shlex.shlex(statement, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    return list(lex)


def git_invocation(toks, i):
    """(subcommand, args after it) for the git word at toks[i], else None."""
    word = os.path.basename(toks[i])
    if word not in GIT_WORDS:
        return None
    if word == "git-push":
        return "push", toks[i + 1:]
    j, n = i + 1, len(toks)
    while j < n and toks[j].startswith("-"):
        opt = toks[j]
        name = opt.partition("=")[0]
        j += 1
        if "=" not in opt and name in GIT_OPTS_WITH_VALUE and j < n:
            j += 1
    if j >= n:
        return None
    return toks[j], toks[j + 1:]


def push_is_release(args):
    """True when this `git push` carries a tag flag or a vX.Y.Z ref."""
    pos, opts = walk_push_args(args, PUSH_OPTS_WITH_VALUE)
    for name, value, _raw in opts:
        if name in TAG_FLAGS and value is None:
            return True
        if value and TAG_REF.search(value):
            return True
    return any(TAG_REF.search(tok) for tok in pos)


def commit_message(args):
    """The message text of `-m`/`--message` options, in argument order."""
    parts = []
    i, n = 0, len(args)
    while i < n:
        tok = args[i]
        i += 1
        if tok == "--":
            break  # git parse-options: only paths follow the end-of-options mark
        if tok == "--message":
            if i < n:
                parts.append(args[i])
                i += 1
            continue
        if tok.startswith("--message="):
            parts.append(tok[len("--message="):])
            continue
        if tok.startswith("-") and not tok.startswith("--") and len(tok) > 1:
            # short cluster: the 'm' takes the rest of the cluster ('-mmsg')
            # or the next token ('-am "msg"').
            flags = tok[1:]
            at = flags.find("m")
            if at < 0:
                continue
            rest = flags[at + 1:]
            if rest:
                parts.append(rest)
            elif i < n:
                parts.append(args[i])
                i += 1
    return "\n".join(parts)


def bump_kind(version, previous):
    """The former shell comparison: major > minor > patch, no tag = patch."""
    major, minor = version.split(".")[:2]
    if not previous:
        return BUMP_PATCH
    prev_major, prev_minor = previous.split(".")[:2]
    if major != prev_major:
        return BUMP_MAJOR
    if minor != prev_minor:
        return BUMP_MINOR
    return BUMP_PATCH


def previous_version():
    """First X.Y.Z of `git describe --tags --abbrev=0 HEAD~1`, else ''."""
    try:
        out = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0", "HEAD~1"],
            capture_output=True, text=True, errors="surrogateescape",
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    if out.returncode != 0:
        return ""
    match = VERSION.search(out.stdout)
    return match.group(0) if match else ""


def bump_event(message):
    """`on-version-bump-*` for a bump message, else None."""
    if not BUMP_TEXT.search(message):
        return None
    match = VERSION.search(message)
    if not match:
        return None
    return bump_kind(match.group(0), previous_version())


def is_pr_merge(args):
    """True for `gh pr merge ...` (the two command words stay adjacent)."""
    return any(tok == "pr" and args[k + 1] == "merge"
               for k, tok in enumerate(args[:-1]))


def detect(command):
    """One lifecycle event name for the shell command that just ran."""
    release = False
    merge = False
    messages = []
    for statement, _heredoc_bodies in split_shell_statements(command):
        try:
            toks = tokens(statement)
        except ValueError:
            continue  # unbalanced quote: not executable as written
        word_at = command_start(toks)
        if word_at >= len(toks):
            continue  # no command word at all (comment / grouping only)
        call = git_invocation(toks, word_at)
        if call is None:
            if os.path.basename(toks[word_at]) == "gh" and is_pr_merge(
                    toks[word_at + 1:]):
                merge = True
            continue
        subcommand, args = call
        if subcommand == "push" and push_is_release(args):
            release = True
        elif subcommand == "commit":
            messages.append(commit_message(args))
        elif subcommand == "merge":
            merge = True
    # Former elif order: release, version bump, merge.
    if release:
        return RELEASE
    for message in messages:
        event = bump_event(message)
        if event:
            return event
    if merge:
        return MERGE
    return NO_EVENT


def main(argv: list[str], stdin: str) -> int:
    """Print the lifecycle event for the command read from stdin."""
    if argv:
        return 1
    print(detect(stdin))
    return 0


if __name__ == "__main__":
    sys.exit(main(
        sys.argv[1:],
        sys.stdin.buffer.read().decode("utf-8", "surrogateescape"),
    ))
