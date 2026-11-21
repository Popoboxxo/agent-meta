"""Git command classification for the kernel shell gate.

Grounded in the fail-closed classifier of
``hooks/1-generic/orchestrator-guard-impl.sh`` (the same MUTATING set, wrapper
grammar, global-option walk, RCE config keys and destructive spellings). This
module is a first extraction: it classifies a single command string and is
importable/testable without a subprocess. The shell guards are not rewired to
it yet -- that is migration step 1/3 and stays outside this bundle.
"""
from __future__ import annotations

import os
import shlex
from dataclasses import dataclass
from typing import List, Optional, Tuple

MUTATING = {
    "commit", "push", "add", "rm", "merge", "rebase", "reset", "restore",
    "tag", "pull", "switch", "cherry-pick", "revert", "am", "update-ref",
    "mv", "apply", "notes", "replace", "update-index", "fast-import", "init",
    "gc",
}
NARROW_SUBCMDS = {"add", "commit"}
STASH_READ_ONLY = {"list", "show"}
SUBMODULE_READ_ONLY = {None, "status", "summary"}
CONFIG_WRITE_OPTS = {
    "--unset", "--unset-all", "--add", "--replace-all", "--rename-section",
    "--remove-section", "-e", "--edit",
}
CONFIG_WRITE_SUBCMDS = {"set", "unset", "rename-section", "remove-section", "edit"}
CONFIG_OPTS_WITH_VALUE = {
    "-f", "--file", "--blob", "--type", "--default", "--comment", "--value",
}
STASH_OPTS_WITH_VALUE = {"-m", "--message", "--pathspec-from-file"}
GLOBAL_OPTS_WITH_VALUE = {
    "-C", "--git-dir", "--work-tree", "--namespace", "--exec-path",
    "--super-prefix", "--config-env", "--attr-source",
}
RCE_CONFIG_KEYS = {
    "core.pager", "core.editor", "core.sshcommand", "core.fsmonitor",
    "core.hookspath", "sequence.editor", "credential.helper",
}
GC_EXPIRY_KEYS = {"gc.reflogexpire", "gc.reflogexpiredrop", "gc.pruneexpire"}
REFLOG_DESTRUCTIVE = {"expire", "delete"}
WHOLE_TREE_PATHSPECS = {".", "./", "*", ":/"}
LEADING_KEYWORDS = {
    "!", "(", ")", "{", "}", "if", "then", "else", "elif", "while", "until",
    "do", "done", "fi", "esac", "in",
}
WRAPPERS = {
    "sudo": ({"-u", "-g", "-p", "-C", "-T", "-r", "-t", "--user", "--group",
              "--prompt", "--chdir"}, 0),
    "doas": ({"-u", "-C"}, 0),
    "env": ({"-u", "--unset", "-C", "--chdir", "-S", "--split-string"}, 0),
    "command": (set(), 0),
    "builtin": (set(), 0),
    "nohup": (set(), 0),
    "exec": ({"-a"}, 0),
    "time": ({"-f", "-o", "--format", "--output"}, 0),
    "nice": ({"-n", "--adjustment"}, 0),
    "ionice": ({"-c", "-n", "-p", "-P", "-u", "--class", "--classdata",
                "--pid", "--pgid", "--uid"}, 0),
    "stdbuf": ({"-i", "-o", "-e", "--input", "--output", "--error"}, 0),
    "xargs": ({"-I", "-n", "-P", "-d", "-L", "-s", "-a", "-E", "-e"}, 0),
    "timeout": ({"-s", "--signal", "-k", "--kill-after"}, 1),
    "flock": ({"-w", "--timeout", "-E", "--conflict-exit-code"}, 1),
    "setsid": (set(), 0),
    "watch": ({"-n", "--interval", "-q", "--equexit"}, 0),
    "strace": ({"-o", "--output", "-p", "--attach", "-e", "--trace",
                "-s", "--string-limit", "-u", "--user", "-a", "--columns",
                "-b", "-I", "-O", "-S", "-X", "-E", "-P"}, 0),
    "chroot": ({"-u", "--userspec", "-g", "--groups"}, 1),
    "busybox": (set(), 0),
}
BRANCH_LIST_FLAGS = {
    "--list", "-l", "--contains", "--no-contains", "--merged", "--no-merged",
    "--points-at", "-a", "--all", "-r", "--remotes", "--show-current",
}


@dataclass(frozen=True)
class GitClass:
    """Classification result: ``category`` and ``scope`` mirror the guard."""

    category: str  # none | mutation | destructive
    scope: str     # narrow | broad
    subcommand: Optional[str] = None


_NONE = GitClass("none", "narrow")


def tokens_of(stmt: str) -> List[str]:
    """Punctuation-aware shell tokens; fall back to a plain split."""
    try:
        lex = shlex.shlex(stmt, posix=True, punctuation_chars="()")
        lex.whitespace_split = True
        lex.commenters = ""
        return list(lex)
    except Exception:
        return stmt.split()


def command_start(toks: List[str]) -> int:
    """Index of the real command word, skipping keywords and wrappers."""
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        if t in LEADING_KEYWORDS:
            i += 1
            continue
        if "=" in t and not t.startswith("-") and t.split("=", 1)[0].isidentifier():
            i += 1
            continue
        base = os.path.basename(t)
        if base in WRAPPERS:
            value_opts, skip_args = WRAPPERS[base]
            i += 1
            while i < n and toks[i].startswith("-") and toks[i] != "-":
                opt = toks[i]
                i += 1
                if opt in value_opts and i < n:
                    i += 1
            while skip_args > 0 and i < n:
                i += 1
                skip_args -= 1
            continue
        return i
    return n


def config_pair(raw: str) -> Tuple[str, Optional[str]]:
    if "=" in raw:
        key, value = raw.split("=", 1)
        return key, value
    return raw, None


def parse_git(rest: List[str]):
    """Consume leading global options; return (subcmd, args, config_values)."""
    config_values = []
    j, n = 0, len(rest)
    while j < n:
        t = rest[j]
        if t in ("-c", "--config"):
            if j + 1 < n:
                config_values.append(config_pair(rest[j + 1]))
                j += 2
            else:
                j += 1
            continue
        if t.startswith("--config="):
            config_values.append(config_pair(t[len("--config="):]))
            j += 1
            continue
        if t == "--config-env":
            if j + 1 < n:
                config_values.append((rest[j + 1].split("=", 1)[0], None))
                j += 2
            else:
                j += 1
            continue
        if t.startswith("--config-env="):
            config_values.append(
                (t[len("--config-env="):].split("=", 1)[0], None)
            )
            j += 1
            continue
        if t in GLOBAL_OPTS_WITH_VALUE:
            j += 2
            continue
        if t.startswith("-"):
            j += 1
            continue
        break
    if j >= n:
        return None, [], config_values
    return rest[j], rest[j + 1:], config_values


def first_word(args: List[str], opts_with_value=()) -> Optional[str]:
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a == "--":
            return None
        if a in opts_with_value:
            skip = True
            continue
        if a.startswith("-"):
            continue
        return a
    return None


def has_short_flag(args: List[str], ch: str, value_opts=()) -> bool:
    for a in args:
        if not (a.startswith("-") and not a.startswith("--") and a != "-"):
            continue
        for c in a[1:]:
            if c == ch:
                return True
            if c in value_opts:
                break
    return False


def is_whole_tree_pathspec(path: str) -> bool:
    return path in WHOLE_TREE_PATHSPECS or path.startswith(":/")


def is_destructive(subcmd, args, config_values) -> bool:
    for key, value in config_values:
        lower = key.lower()
        if lower in RCE_CONFIG_KEYS or lower.startswith("alias."):
            return True
        if lower in GC_EXPIRY_KEYS and (
            value is None or value.strip().lower() == "now"
        ):
            return True
    if subcmd is None:
        return False
    positionals = [a for a in args if not a.startswith("-")]
    if subcmd == "push":
        if any(a in ("-f", "--force") or a.startswith("--force-with-lease")
               for a in args):
            return True
        if has_short_flag(args, "f", {"o"}):
            return True
        if ("--mirror" in args or "--delete" in args or "--prune" in args
                or has_short_flag(args, "d", {"o"})):
            return True
        if any(p.startswith(":") and len(p) > 1 for p in positionals):
            return True
        return any(p.startswith("+") for p in positionals)
    if subcmd == "reset":
        return "--hard" in args
    if subcmd == "clean":
        return "--force" in args or has_short_flag(args, "f")
    if subcmd == "stash":
        return first_word(args, STASH_OPTS_WITH_VALUE) in ("drop", "clear")
    if subcmd in ("filter-branch", "filter-repo"):
        return True
    if subcmd == "branch":
        value_opts = {"u", "c", "C", "m", "M"}
        return ("--force" in args or has_short_flag(args, "f", value_opts)
                or has_short_flag(args, "D", value_opts))
    if subcmd in ("checkout", "switch"):
        k = args.index("--") if "--" in args else len(args)
        opts, paths = args[:k], args[k + 1:]
        value_opts = {"b", "B"} if subcmd == "checkout" else {"c", "C"}
        if "--force" in opts or "--discard-changes" in opts:
            return True
        if has_short_flag(opts, "f", value_opts):
            return True
        create_flag = "B" if subcmd == "checkout" else "C"
        if has_short_flag(opts, create_flag, value_opts):
            return True
        return any(is_whole_tree_pathspec(p) for p in paths)
    if subcmd == "reflog":
        return first_word(args) in REFLOG_DESTRUCTIVE
    return False


def is_mutation(subcmd, args) -> bool:
    if subcmd in MUTATING:
        return True
    if subcmd == "stash":
        return first_word(args, STASH_OPTS_WITH_VALUE) not in STASH_READ_ONLY
    if subcmd == "submodule":
        return first_word(args) not in SUBMODULE_READ_ONLY
    if subcmd == "config":
        if any(a in CONFIG_WRITE_OPTS or a.startswith("--unset=")
               or a.startswith("--add=") for a in args):
            return True
        return first_word(args, CONFIG_OPTS_WITH_VALUE) in {
            "set", "unset", "rename-section", "remove-section", "edit",
        }
    if subcmd == "branch":
        if any(a in BRANCH_LIST_FLAGS or a.startswith("--contains=")
               or a.startswith("--points-at=") for a in args):
            return False
        return bool([a for a in args if not a.startswith("-")])
    return False


def classify_git(command: Optional[str]) -> GitClass:
    """Classify a shell command string as none/mutation/destructive."""
    if not command or not isinstance(command, str):
        return _NONE
    toks = tokens_of(command)
    start = command_start(toks)
    if start >= len(toks) or os.path.basename(toks[start]) != "git":
        return _NONE
    subcmd, args, config_values = parse_git(toks[start + 1:])
    if is_destructive(subcmd, args, config_values):
        return GitClass("destructive", "broad", subcmd)
    if subcmd is None:
        return _NONE
    if is_mutation(subcmd, args):
        narrow = subcmd in NARROW_SUBCMDS and not (
            subcmd == "commit" and "--amend" in args
        )
        return GitClass("mutation", "narrow" if narrow else "broad", subcmd)
    return GitClass("none", "narrow", subcmd)
