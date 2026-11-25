#!/usr/bin/env python3
"""Git, destructive-command and commit-BOM classifier for the guard hook.

Issue #1238b2: importable replacement for the former inline Python heredoc.
The shared shell scanner is imported from the same deployed flat lib/ directory.
"""
from __future__ import annotations

import os
import re
import shlex
import sys

sys.dont_write_bytecode = True

from hook_shell_scan import (  # noqa: E402
    is_fork_bomb,
    split_shell_statements_and_clean,
    strip_quoted,
)


MUTATING = {
    'commit', 'push', 'add', 'rm', 'merge', 'rebase', 'reset', 'restore',
    'tag',
    # SR-B-13: history/ref/working-tree changing subcommands that used to
    # slip through ('switch' is checkout's modern alias).
    'pull', 'switch', 'cherry-pick', 'revert', 'am', 'update-ref',
    # #1151 F6-04: index/tree/ref/object-store writers that slipped through.
    'mv', 'apply', 'notes', 'replace', 'update-index', 'fast-import', 'init',
    'gc',
}
# 'git stash' subcommands that only read; a bare 'git stash' is 'stash push'
# and every other form (push/save/apply/pop/drop/clear/store/branch/...)
# changes the stash or the working tree (#1151 F6-04).
STASH_READ_ONLY = {'list', 'show'}
# 'git submodule' forms that only read; a bare 'git submodule' is 'status'.
SUBMODULE_READ_ONLY = {None, 'status', 'summary'}
# 'git config' write spellings (#1151 F6-04): option forms and the git >= 2.46
# subcommand forms. Options that consume a value are skipped when counting the
# key/value positionals (key alone = read, key + value = write).
CONFIG_WRITE_OPTS = {'--unset', '--unset-all', '--add', '--replace-all',
                     '--rename-section', '--remove-section', '-e', '--edit'}
CONFIG_READ_OPTS = {'--get', '--get-all', '--get-regexp', '--get-urlmatch',
                    '--get-color', '--get-colorbool', '-l', '--list'}
CONFIG_WRITE_SUBCMDS = {'set', 'unset', 'rename-section', 'remove-section', 'edit'}
CONFIG_READ_SUBCMDS = {'get', 'list'}
CONFIG_OPTS_WITH_VALUE = {'-f', '--file', '--blob', '--type', '--default',
                          '--comment', '--value'}
# Options of 'git stash' (push form) that consume a value token, so the
# value is not misread as the stash subcommand ('git stash -m drop').
STASH_OPTS_WITH_VALUE = {'-m', '--message', '--pathspec-from-file'}
# 'git reflog' subcommands that delete reflog entries (SR-B-12/13); plain
# 'git reflog' / 'git reflog show' are read-only.
REFLOG_DESTRUCTIVE = {'expire', 'delete'}

# Global git options (before the subcommand) that consume a following value
# token; if not skipped WITH their value, the value is misread as the
# subcommand (issue #591, e.g. 'git -C path push' would see 'path').
GLOBAL_OPTS_WITH_VALUE = {
    '-C', '--git-dir', '--work-tree', '--namespace', '--exec-path',
    '--super-prefix',
    # Same subcommand-hiding class as '-c' (issue #551): both take a separate
    # value token in space-form and would otherwise mask the real subcommand
    # (e.g. 'git --config-env x=Y push --force' / 'git --attr-source t push
    # --force' hid 'push').
    '--config-env', '--attr-source',
}
# Config keys whose value git hands to the shell -> arbitrary command
# execution / RCE (issue #591). Flagged destructive regardless of the
# subcommand, so 'git -c core.pager=<cmd> status' is still blocked. Keys are
# compared case-insensitively (git config section/name are case-insensitive),
# so every entry here must be lowercase. 'alias.*' is handled by prefix below.
RCE_CONFIG_KEYS = {
    'core.pager', 'core.editor', 'core.sshcommand', 'core.fsmonitor',
    'core.hookspath', 'sequence.editor', 'credential.helper',
}


def tokens_of(stmt):
    # Punctuation-aware so a grouping token does not glue to the command word
    # (issue #943 (b): shlex.split('(git push)') gave the token '(git', which
    # is never 'git'). Parentheses become their own tokens; the command-word
    # scan below skips them.
    try:
        lex = shlex.shlex(stmt, posix=True, punctuation_chars='()')
        lex.whitespace_split = True
        lex.commenters = ''
        return list(lex)
    except Exception:
        return stmt.split()


# Shell keywords / grouping tokens that may precede the real command word.
# `in` is a bash reserved word, never a command: it is the separator a `case`
# list carries when the splitter cuts `case WORD` and `in PATTERN)` onto
# different statements (review finding F-NEW-2). Without it the command word
# of the next statement was the literal `in`, so the arm's command list was
# never classified.
LEADING_KEYWORDS = {
    '!', '(', ')', '{', '}', 'if', 'then', 'else', 'elif', 'while', 'until',
    'do', 'done', 'fi', 'esac', 'in',
}
# Command wrappers whose option-before-command form must not hide the real
# command word (issue #943 (i): 'man git pull' must NOT be read as git, while
# 'sudo git push' and 'env X=1 git push' must still be). Maps a wrapper to
# (its short/long options that consume a value token, its count of leading
# non-option arguments before the wrapped command word). The second element is
# grammar, not guesswork: 'timeout DURATION cmd', 'flock FILE cmd' and
# 'chroot NEWROOT cmd' each own exactly one positional prefix (review finding
# F3 -- these used to hide the wrapped command word entirely).
WRAPPERS = {
    'sudo': ({'-u', '-g', '-p', '-C', '-T', '-r', '-t', '--user', '--group',
              '--prompt', '--chdir'}, 0),
    'doas': ({'-u', '-C'}, 0),
    'env': ({'-u', '--unset', '-C', '--chdir', '-S', '--split-string'}, 0),
    'command': (set(), 0),
    'builtin': (set(), 0),
    'nohup': (set(), 0),
    'exec': ({'-a'}, 0),
    'time': ({'-f', '-o', '--format', '--output'}, 0),
    'nice': ({'-n', '--adjustment'}, 0),
    'ionice': ({'-c', '-n', '-p', '-P', '-u', '--class', '--classdata',
                '--pid', '--pgid', '--uid'}, 0),
    'stdbuf': ({'-i', '-o', '-e', '--input', '--output', '--error'}, 0),
    'xargs': ({'-I', '-n', '-P', '-d', '-L', '-s', '-a', '-E', '-e'}, 0),
    'timeout': ({'-s', '--signal', '-k', '--kill-after'}, 1),
    'flock': ({'-w', '--timeout', '-E', '--conflict-exit-code'}, 1),
    # setsid has NO option that consumes a value (-c/-f/-w are all flags);
    # listing them as value-taking swallowed the wrapped command word
    # (`setsid --wait git push` was never classified).
    'setsid': (set(), 0),
    'watch': ({'-n', '--interval', '-q', '--equexit'}, 0),
    'strace': ({'-o', '--output', '-p', '--attach', '-e', '--trace',
                '-s', '--string-limit', '-u', '--user', '-a', '--columns',
                '-b', '-I', '-O', '-S', '-X', '-E', '-P'}, 0),
    'chroot': ({'-u', '--userspec', '-g', '--groups'}, 1),
    'busybox': (set(), 0),
}


def _empty_parens(toks, i):
    # shlex with punctuation_chars='()' returns ADJACENT punctuation as one
    # token, so 'f()' yields the pair '()' while '( git' yields '('. Return
    # how many tokens the empty pair occupies at i (0 = none).
    if i < len(toks) and toks[i] == '()':
        return 1
    if i + 1 < len(toks) and toks[i] == '(' and toks[i + 1] == ')':
        return 2
    return 0


def _close_paren_run(tok):
    # A case-pattern terminator. shlex with punctuation_chars='()' groups
    # ADJACENT punctuation into one token, so the ')' closing a pattern can
    # arrive as ')' or -- for an extglob pattern such as `@(a|b))` -- as
    # ')). Treat any token consisting only of closing parentheses as the
    # terminator (review finding F-NEW-2 follow-up: the exact-')' test let
    # the extglob arm hide its command list).
    return bool(tok) and tok.strip(')') == ''


def command_start(toks):
    # Index of the real command word in a statement, skipping keywords,
    # grouping tokens, KEY=VALUE assignments, `case` arm syntax, inline
    # function-definition prefixes and wrapper prefixes. Returns len(toks)
    # when the statement has no command word. This is what keeps a mere
    # ARGUMENT named git ('man git pull', 'echo git push') from being
    # classified as a git invocation (issue #943 (i)).
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        base = os.path.basename(t)
        # A lone '--' at command position is an end-of-options marker, not a
        # command word. It can follow a wrapper's option parser, its
        # positional prefix (DURATION/FILE/ROOT) or appear directly before
        # the command word; in every case the wrapped command is what runs, so
        # skipping the marker is the transparent reading (review finding
        # F-NEW-1: `timeout 5 -- git push --force` used to stop here and was
        # never classified).
        if t == '--':
            i += 1
            continue
        if t in LEADING_KEYWORDS:
            i += 1
            continue
        # A bare run of grouping parentheses (shlex groups adjacent ones into
        # '((' / '))' / '()'). At command position it closes a subshell/case
        # arm, it is never the command word itself.
        if t and t.strip('()') == '':
            i += 1
            continue
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', t):
            i += 1
            continue
        # `case WORD in PATTERN) COMMAND ;; esac`: the command list after the
        # pattern terminator is what runs (review finding F3).
        if t == 'case':
            i += 1
            if i < n:                      # the case subject word
                i += 1
            if i < n and toks[i] == 'in':
                i += 1
            while i < n and not _close_paren_run(toks[i]):
                i += 1
            if i < n:
                i += 1                     # the pattern's closing ')' run
            continue
        # The splitter cuts at ';;', so a later case arm arrives as its own
        # statement ('PATTERN) command'). A bare word directly followed by a
        # ')' run is never a command outside `case`; skip the pattern prefix.
        # The ')' run may be several characters wide for an extglob pattern
        # (`@(a|b))`), which is why this is not an exact-')' comparison.
        if i + 1 < n and _close_paren_run(toks[i + 1]):
            i += 2
            continue
        # Inline function definition: 'NAME() { COMMAND; }' (review finding
        # F3). The body's first command follows the '{'.
        parens = _empty_parens(toks, i + 1)
        if parens and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', t):
            i += 1 + parens
            if i < n and toks[i] == '{':
                i += 1
            continue
        # 'function NAME { COMMAND; }' (optional empty parens).
        if t == 'function':
            i += 1
            if i < n:                      # the function name
                i += 1
            i += _empty_parens(toks, i)
            if i < n and toks[i] == '{':
                i += 1
            continue
        if base in WRAPPERS:
            value_opts, skip_args = WRAPPERS[base]
            i += 1
            while i < n:
                opt = toks[i]
                if opt == '--':
                    i += 1
                    break
                if opt.startswith('--'):
                    name = opt.split('=', 1)[0]
                    has_value = '=' in opt
                    i += 1
                    if not has_value and name in value_opts and i < n:
                        i += 1
                    continue
                if opt.startswith('-') and opt != '-':
                    i += 1
                    if opt in value_opts and i < n:
                        i += 1
                    continue
                break
            # Skip the wrapper's own positional prefix (DURATION, FILE, ROOT).
            while skip_args > 0 and i < n:
                i += 1
                skip_args -= 1
            continue
        break
    return i


def config_pair(raw):
    # A -c/--config value may be 'key' or 'key=value'. --config-env only names
    # the ENV VAR that holds the value, so its value is unknown at hook time;
    # represent that as None (conservative for the gc.* rules below).
    if '=' in raw:
        k, v = raw.split('=', 1)
        return (k, v)
    return (raw, None)


def parse_git(rest):
    # Consume leading global options (including '-c key=val' with its value,
    # issue #591) and return (subcmd or None, args, config_values).
    # config_values collects the (KEY, VALUE) of every -c/--config pair; the
    # VALUE is what distinguishes 'gc.reflogExpire=now' from '=never'.
    config_values = []
    j, n = 0, len(rest)
    while j < n:
        t = rest[j]
        if t in ('-c', '--config'):
            if j + 1 < n:
                config_values.append(config_pair(rest[j + 1]))
                j += 2
            else:
                j += 1
            continue
        if t.startswith('--config='):
            config_values.append(config_pair(t[len('--config='):]))
            j += 1
            continue
        # '--config-env <name>=<envvar>' (git >=2.31): the KEY is the <name>
        # part, same RCE surface as '-c' (issue #551). The VALUE lives in an
        # environment variable the hook cannot read, so record it as None
        # (unknown -> conservative for the gc.* rules).
        if t == '--config-env':
            if j + 1 < n:
                raw = rest[j + 1]
                config_values.append((raw.split('=', 1)[0], None))
                j += 2
            else:
                j += 1
            continue
        if t.startswith('--config-env='):
            raw = t[len('--config-env='):]
            config_values.append((raw.split('=', 1)[0], None))
            j += 1
            continue
        if t in GLOBAL_OPTS_WITH_VALUE:
            j += 2
            continue
        if t.startswith('-'):
            j += 1
            continue
        break
    if j >= n:
        return None, [], config_values
    return rest[j], rest[j + 1:], config_values


def first_word(args, opts_with_value=()):
    # First non-option token of a subcommand's args, i.e. its own
    # sub-subcommand (SR-B-12): options may precede it ('git stash -q drop'),
    # so 'args[0]' is not enough. Values of opts_with_value are skipped; a
    # '--' ends option parsing and everything after it is a pathspec.
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a == '--':
            return None
        if a in opts_with_value:
            skip = True
            continue
        if a.startswith('-'):
            continue
        return a
    return None


def has_short_flag(args, ch, value_opts=()):
    # True if a short-option cluster (single dash, not '--') contains 'ch'
    # BEFORE any option that consumes the rest of the cluster as its value:
    # has_short_flag(['-fu'], 'f') -> True, has_short_flag(['-bfoo'], 'f',
    # ('b', 'B')) -> False because '-bfoo' is '-b foo' (issue #943 (i): the
    # old 'ch in a' test read the branch name 'foo' as the --force flag).
    # 'ch' wins over value_opts so '-f' itself and '-fu' still match.
    for a in args:
        if not (a.startswith('-') and not a.startswith('--') and a != '-'):
            continue
        for c in a[1:]:
            if c == ch:
                return True
            if c in value_opts:
                break
    return False


# git config keys that expire/delete unreachable objects or reflogs when set
# to 'now'. They are destructive-by-value (never by name alone) and are listed
# separately from RCE_CONFIG_KEYS, which are destructive by key (#943 (e)).
GC_EXPIRY_KEYS = {'gc.reflogexpire', 'gc.reflogexpiredrop', 'gc.pruneexpire'}

# Pathspecs that address the whole tree rather than one file (issue #943 (d)).
WHOLE_TREE_PATHSPECS = {'.', './', '*', ':/'}


def is_whole_tree_pathspec(p):
    return p in WHOLE_TREE_PATHSPECS or p.startswith(':/')


def is_ask_class(subcmd, args, config_values):
    """Narrow #1217 ask subclass: only PURE explicitly approved ref deletions.

    A statement is ask-eligible only when its destructive verdict comes from
    the delete operation alone -- any co-occurring hard indicator in the SAME
    statement (force / mirror / prune / leading '+' refspec for push, force
    for branch) makes it hard (strictest class wins WITHIN one statement).
    Default is 'hard' for everything else. A config-driven RCE vector, a
    fork bomb, a filesystem wipe or any other destructive verdict is NOT
    ask-class, so it keeps the hard exit 2. Multi-statement commands win the
    strictest class: one hard destructive statement disqualifies the whole
    command from ask (tracked by the caller's ask_eligible flag).
    """
    if config_values:
        return False
    if subcmd == 'branch':
        branch_value_opts = {'u', 'c', 'C', 'm', 'M'}
        # '-f'/'--force' moves the tip -> hard, even alongside '-D'.
        if '--force' in args or has_short_flag(args, 'f', branch_value_opts):
            return False
        # '-D' (forced delete); value opts must not be read as '-D'.
        return has_short_flag(args, 'D', branch_value_opts)
    if subcmd == 'push':
        positionals = [a for a in args if not a.startswith('-')]
        # Mirror/prune delete far more than the named ref; a leading '+' or
        # any force flag makes the push hard regardless of --delete/':ref'.
        if '--mirror' in args or '--prune' in args:
            return False
        if any(p.startswith('+') for p in positionals):
            return False
        for a in args:
            if a in ('-f', '--force') or a.startswith('--force-with-lease'):
                return False
        if has_short_flag(args, 'f', {'o'}):
            return False
        if '--delete' in args:
            return True
        # ':dst' empty-source refspec deletes the remote ref.
        return any(p.startswith(':') and len(p) > 1 for p in positionals)
    return False


def is_destructive(subcmd, args, config_values, stdin_bodies=None):
    # RCE via config applies regardless of the subcommand (issue #591). Keys
    # are matched case-insensitively; 'alias.<name>=<cmd>' is an RCE vector too
    # (git runs the alias body via the shell), matched by prefix. A gc.*
    # expiry key is destructive when it expires/reaps immediately (#943 (e)).
    for k, v in config_values:
        kl = k.lower()
        if kl in RCE_CONFIG_KEYS or kl.startswith('alias.'):
            return True
        if kl in GC_EXPIRY_KEYS and (v is None or v.strip().lower() == 'now'):
            return True
    if subcmd is None:
        return False
    positionals = [a for a in args if not a.startswith('-')]
    if subcmd == 'push':
        for a in args:
            if a in ('-f', '--force') or a.startswith('--force-with-lease'):
                return True
        # short-flag cluster containing 'f' (e.g. -fu); '-o' takes the rest of
        # the cluster as a value, so '-oforce' is a push-option, not --force.
        if has_short_flag(args, 'f', {'o'}):
            return True
        # '--mirror' / '--delete' / '-d' delete remote refs -> irreversible
        # ref loss, blocked even with a git sentinel (issue #551, cf. #590).
        # '--prune' deletes remote refs without a local counterpart (SR-B-12).
        if '--mirror' in args or '--delete' in args or '--prune' in args:
            return True
        if has_short_flag(args, 'd', {'o'}):
            return True
        # Empty-source refspec ':dst' (also '+:dst') deletes the remote ref
        # dst (SR-B-12). A bare ':' is the 'matching' refspec, not a delete.
        if any(p.startswith(':') and len(p) > 1 for p in positionals):
            return True
        # leading '+' on a refspec forces a non-fast-forward push (issue #590);
        # a plain 'HEAD:main' (no '+') is a normal fast-forward push.
        return any(p.startswith('+') for p in positionals)
    if subcmd == 'reset':
        return '--hard' in args
    if subcmd == 'clean':
        if '--force' in args:
            return True
        return has_short_flag(args, 'f')
    if subcmd == 'stash':
        return first_word(args, STASH_OPTS_WITH_VALUE) in ('drop', 'clear')
    if subcmd in ('filter-branch', 'filter-repo'):
        return True
    if subcmd == 'branch':
        # Issue #943 (h): '-f'/'--force' moves a branch to another tip and
        # '-D' deletes it even when unmerged -- both drop the old tip without
        # a reachable reflog promise. '-m'/'-M'/'-c'/'-C' take a value, so a
        # cluster like '-mold' must not be read as '-f'/'D' ('f'/'D' inside
        # the value). Plain '-d' stays a mutation.
        branch_value_opts = {'u', 'c', 'C', 'm', 'M'}
        if '--force' in args or has_short_flag(args, 'f', branch_value_opts):
            return True
        return has_short_flag(args, 'D', branch_value_opts)
    if subcmd in ('checkout', 'switch'):
        # SR-B-12: '-f'/'--force' (and switch's '--discard-changes') throw
        # away local changes; checkout of a whole-tree pathspec wipes the
        # working tree with or without '--'. A single-path restore stays a
        # mutation. Issue #943 (d): './', '*', ':/' and 'HEAD -- ./' are
        # whole-tree too; issue #943 (h): '-B'/'-C' (force-create) reset the
        # branch tip even when no pathspec is given.
        k = args.index('--') if '--' in args else len(args)
        opts, paths = args[:k], args[k + 1:]
        value_opts = {'b', 'B'} if subcmd == 'checkout' else {'c', 'C'}
        if '--force' in opts or '--discard-changes' in opts:
            return True
        if has_short_flag(opts, 'f', value_opts):
            return True
        create_ch = 'B' if subcmd == 'checkout' else 'C'
        if '--force-create' in opts or has_short_flag(opts, create_ch, value_opts):
            return True
        candidates = [a for a in opts if not a.startswith('-')] + paths
        return any(is_whole_tree_pathspec(a) for a in candidates)
    if subcmd == 'update-ref':
        if '-d' in args or '--delete' in args:
            return True
        if '--stdin' in args:
            # Issue #943 (f): 'update-ref --stdin' reads ref commands from
            # stdin. Only a heredoc body is visible to the hook; with no body
            # (a pipe) the input cannot be classified -> fail closed.
            if stdin_bodies is None:
                return True
            for body in stdin_bodies:
                for line in body.splitlines():
                    if re.match(r'^\s*delete(\s|' + chr(0) + r')', line):
                        return True
        return False
    if subcmd == 'reflog':
        return first_word(args) in REFLOG_DESTRUCTIVE
    if subcmd == 'restore':
        return any(is_whole_tree_pathspec(a) for a in positionals)
    if subcmd == 'gc':
        # Issue #943 (e): 'git gc --prune=now' deletes unreachable objects
        # immediately (the accompanying gc.reflogExpire=now is covered by
        # GC_EXPIRY_KEYS above).
        for idx, a in enumerate(args):
            if a == '--prune=now':
                return True
            if a == '--prune' and idx + 1 < len(args) and args[idx + 1] == 'now':
                return True
        return False
    if subcmd == 'worktree':
        # Issue #943 (g): 'worktree remove --force/-f' deletes a worktree
        # even with local modifications.
        w = first_word(args)
        if w == 'remove' and ('--force' in args or '-f' in args or has_short_flag(args, 'f')):
            return True
        return False
    return False


def is_config_write(args):
    if any(a.split('=', 1)[0] in CONFIG_WRITE_OPTS for a in args):
        return True
    if any(a in CONFIG_READ_OPTS for a in args):
        return False
    positionals = []
    skip = False
    for a in args:
        if skip:
            skip = False
            continue
        if a in CONFIG_OPTS_WITH_VALUE:
            skip = True
            continue
        if a.startswith('-'):
            continue
        positionals.append(a)
    if positionals and positionals[0] in CONFIG_WRITE_SUBCMDS:
        return True
    if positionals and positionals[0] in CONFIG_READ_SUBCMDS:
        return False
    return len(positionals) >= 2


def is_mutation(subcmd, args):
    if subcmd is None:
        return False
    if subcmd == 'branch':
        positional = [a for a in args if not a.startswith('-')]
        mutating_flags = {'-d', '-D', '-m', '-M', '--delete', '--move', '--copy', '-c', '-C'}
        if set(args) & mutating_flags:
            return True
        # Issue #1258: list-mode flags take a positional (commit/pattern), not a new branch.
        # -v/--format/--sort/--color/--column are NOT list-mode implicators: stay fail-closed.
        list_flags = {'--list', '-l', '--contains', '--no-contains', '--merged', '--no-merged',
                      '--points-at', '-a', '--all', '-r', '--remotes', '--show-current'}
        if {a.split('=', 1)[0] for a in args} & list_flags:
            return False
        return bool(positional)
    if subcmd == 'checkout':
        return bool(args) and not all(a.startswith('-') for a in args)
    if subcmd == 'stash':
        return first_word(args, STASH_OPTS_WITH_VALUE) not in STASH_READ_ONLY
    if subcmd == 'submodule':
        return first_word(args) not in SUBMODULE_READ_ONLY
    if subcmd == 'config':
        return is_config_write(args)
    if subcmd == 'reflog':
        return first_word(args) in REFLOG_DESTRUCTIVE
    if subcmd == 'worktree':
        # Every worktree subcommand except 'list' changes worktree state.
        w = first_word(args)
        return w is not None and w != 'list'
    if subcmd == 'am':
        # Issue #943 (i): '--show-current-patch' only prints the patch; it
        # neither applies nor aborts anything.
        return not any(a == '--show-current-patch' or a.startswith('--show-current-patch=')
                       for a in args)
    if subcmd in ('cherry-pick', 'revert'):
        # Issue #943 (i): '--abort'/'--quit' roll a stopped sequence back; they
        # do not rewrite history.
        return not any(a in ('--abort', '--quit') for a in args)
    return subcmd in MUTATING


# Issue #694: the allowlist sentinel authorizes staging+committing only, so
# the scan reports whether every mutation found stays inside that set.
ADDCOMMIT_ONLY = {'add', 'commit'}


def is_addcommit_scope(subcmd, args):
    if subcmd not in ADDCOMMIT_ONLY:
        return False
    # 'commit --amend' REWRITES the previous commit rather than creating a
    # new one -- it can silently destroy work an earlier commit (possibly
    # the git role's) already recorded. Not part of the add/commit
    # authority granted to auto-committing roles.
    if subcmd == 'commit' and '--amend' in args:
        return False
    return True

def ansi_c_decode(s):
    # Decode a shell ANSI-C (dollar-single-quote) quoted value. shlex strips
    # the surrounding single quotes, so the token arrives as a leading dollar
    # sign followed by the raw escape text (backslash-u-F-E-F-F then the
    # message, or backslash-x-E-F...). bytes(...).decode('unicode_escape')
    # turns the backslash escapes into real characters.
    try:
        return s.encode('latin-1', 'backslashreplace').decode('unicode_escape')
    except Exception:
        return s


DOLLAR = chr(36)


def message_starts_with_bom(msg):
    # A leading UTF-8 BOM decodes to U+FEFF at the very start of the string
    # (issue #842). Only the START matters -- a BOM used as a zero-width
    # space inside the subject/body must not false-positive.
    if not msg:
        return False
    if msg[0] == '\ufeff':
        return True
    # ANSI-C quoting bypass (issue #842, G1): an ANSI-C quoted message with a
    # leading BOM reaches the hook as a leading dollar sign then the escape
    # text, because shlex strips the quotes. A NORMAL message starting with a
    # literal dollar sign must still pass, so only treat the leading dollar
    # sign as ANSI-C when the shell would: the next character must be a
    # backslash (an escape). A plain dollar amount has no backslash -> allowed.
    if msg[0] == DOLLAR and len(msg) > 1 and msg[1] == '\\':
        decoded = ansi_c_decode(msg[1:])
        if decoded[:1] == '\ufeff' or decoded[:3] == '\xef\xbb\xbf':
            return True
    return False


def file_starts_with_bom(path, root):
    # Read the first three bytes and compare to the raw UTF-8 BOM. A BOM
    # embedded anywhere later in the file is irrelevant (only the subject at
    # byte 0 matters). Missing/unreadable file -> no signal (allow; git
    # itself will report the missing file).
    if not os.path.isabs(path):
        path = os.path.join(root, path)
    try:
        with open(path, 'rb') as f:
            return f.read(3) == b'\xef\xbb\xbf'
    except OSError:
        return False


def short_cluster_value(args, tok):
    # G2 (issue #842): a short-option cluster like '-am' or '-aF' may end in a
    # value-taking short option. git's own grammar: 'm' takes a message (next
    # token when it is the cluster's last char), 'F' takes a file. If the value
    # is glued to the cluster ('-amMSG' / '-aFfile'), the remainder is the
    # value. Return (kind, value) or (None, None) when the cluster holds no
    # m/F. Only single-dash clusters (not '--long') are considered.
    if not tok.startswith('-') or tok.startswith('--') or tok == '-':
        return None, None
    body = tok[1:]
    for pos, ch in enumerate(body):
        if ch == 'm':
            rest = body[pos + 1:]
            if rest:
                return 'message', rest
            if len(args) > 1:
                return 'message', args[1]
            return None, None
        if ch == 'F':
            rest = body[pos + 1:]
            if rest:
                return 'file', rest
            if len(args) > 1:
                return 'file', args[1]
            return None, None
    return None, None


def commit_message_bom(args, root):
    # 'message' when a -m/--message value starts with a BOM, 'file' when a
    # -F/--file file whose first three bytes are the UTF-8 BOM, else 'none'.
    # Recognized spellings: '-m VALUE', '--message VALUE', '--message=VALUE',
    # '-mGLUED', and short-option clusters containing m/F ('-am VALUE',
    # '-aFfile VALUE' -- the value is the next token only when m/F is the
    # cluster's last character, matching git's short-option grammar; anything
    # glued after m/F is that option's value). -m/-F may repeat; any
    # BOM-bearing source counts.
    for idx, tok in enumerate(args):
        value = None
        kind = None
        for flag, fkind in (('-m', 'message'), ('--message', 'message'),
                            ('-F', 'file'), ('--file', 'file')):
            if tok == flag:
                if idx + 1 < len(args):
                    value, kind = args[idx + 1], fkind
                break
            if tok.startswith(flag + '='):
                value, kind = tok[len(flag) + 1:], fkind
                break
        if value is None and (tok.startswith('-') and not tok.startswith('--')):
            kind, value = short_cluster_value(args[idx:], tok)
        if value is None:
            continue
        if kind == 'message':
            if message_starts_with_bom(value):
                return 'message'
        elif file_starts_with_bom(value, root):
            return 'file'
    return 'none'


# --- issue #809: non-git filesystem destruction + fork bomb -------------
# The git classifier above only inspects 'git <subcommand>' invocations.
# The destructive gate must also cover the canonical shell-level
# catastrophes: recursive removal of a dangerous filesystem root and a
# recursive fork bomb. Same best-effort token scan / convention-boundary
# trade-off as the git gates (issue #592) -- no shell interpreter, and the
# command is never executed. wrapper prefixes (sudo/env/nice/...) are skipped
# by command_start(), shared with the git classifier.
# Top-level roots whose recursive removal is treated as destructive.
# '/tmp' is deliberately absent: build/CI scratch under /tmp is routine.
DANGEROUS_ROOTS = {
    '/', '/etc', '/usr', '/var', '/bin', '/sbin', '/lib', '/lib64',
    '/boot', '/dev', '/proc', '/sys', '/opt', '/root', '/home', '/srv',
    '/mnt', '/media', '/run',
}
# Known scratch subtrees that stay allowed even though their first component
# is a system root (e.g. '/var'): routine build/CI cleanup lives here.
SCRATCH_SUBPATHS = ('/tmp/', '/var/tmp/', '/private/tmp/', '/var/folders/')
def is_recursive_rm(args):
    for a in args:
        if a == '--recursive':
            return True
        if a.startswith('-') and not a.startswith('--') and a != '-':
            if 'r' in a[1:] or 'R' in a[1:]:
                return True
    return False


def normalize_rm_target(target):
    # Drop a trailing glob and trailing slashes so '/etc/*' and '/etc/'
    # both normalize to '/etc' (bare '/' stays '/').
    t = target.strip()
    if t.endswith('*'):
        t = t[:-1]
    if t.endswith('/') and t != '/':
        t = t.rstrip('/')
    return t


def is_dangerous_rm_target(target):
    raw = target.strip()
    # Bare current/parent dir or unqualified glob wipes the working tree.
    # Checked on the RAW token; normalize_rm_target turns '*' into ''.
    if raw in ('.', '..', '*'):
        return True
    # Known scratch subtrees stay allowed; '..' is excluded so a traversal
    # like '/var/tmp/../etc' is not laundered into the exception.
    if raw.startswith(SCRATCH_SUBPATHS) and '..' not in raw:
        return False
    t = normalize_rm_target(target)
    if not t:
        return False
    if t in ('.', '..'):
        return True
    home = DOLLAR + 'HOME'
    home_braced = DOLLAR + '{HOME}'
    # HOME itself (or a glob directly under it), not a normal subdirectory.
    if t in ('~', home, home_braced):
        return True
    # Absolute path: danger is the top-level component, minus scratch.
    if t.startswith('/'):
        if t.startswith(SCRATCH_SUBPATHS):
            return False
        first = '/' + t.lstrip('/').split('/', 1)[0]
        return first in DANGEROUS_ROOTS
    return False


def is_fs_destructive(cmd, args):
    if cmd != 'rm':
        return False
    if not is_recursive_rm(args):
        return False
    return any(
        is_dangerous_rm_target(a)
        for a in args
        if not (a.startswith('-') and a != '-')
    )


# Fork-bomb detection comes from the shared lib (hook_shell_scan_py):
# linear-time and quote-aware. It runs on the command with heredoc bodies and
# comments removed (a fork-bomb-shaped STRING in prose must not trip the
# gate, #602/#809/#943 (j)), but with operators intact -- ':(){ :|:& };:' is
# split into statements by those operators and would otherwise be invisible.
# The comment rule lives in the scanner itself (one implementation for the
# statement stream and this cleaned code, review finding F4): a trailing
# '# :(){ :|:& };:' is cut here exactly as it is in the statements.


def classify(command: str, root: str) -> str:
    _statement_stream, _scan_code = split_shell_statements_and_clean(command)
    fork_bomb = is_fork_bomb(strip_quoted(_scan_code))
    destructive = fork_bomb
    mutation = False
    mutation_scope_broad = False
    bom = 'none'
    # Issue #1181: 1 only when EVERY statement's command word is `git`. The grant
    # gate uses this to reject a mixed git+non-git list (e.g. `git add && curl`)
    # even when the git mutations themselves stay within the narrow add/commit
    # scope. Comments (incl. the sentinel line) are absent from this stream.
    all_git = True
    # #1217: ask subclass is opt-in and only for the two approved delete ops.
    # One hard-destructive statement disqualifies the whole command (strictest
    # class wins); a fork bomb or fs wipe is never ask-class.
    ask_eligible = True
    has_ask = False
    if fork_bomb:
        ask_eligible = False
    # Quote/heredoc-aware statements from the shared lib (issue #943 (c)/(j),
    # #944 SR-B-16). Heredoc bodies are attached to the statement that opened
    # them; they are prose for command classification, except that
    # `update-ref --stdin` delete lines are inspected.
    for stmt, heredoc_bodies in _statement_stream:
        # #1217 (review fix): only stop early once a HARD destructive verdict is
        # known (strictest class already reached). While merely an ask-class
        # delete was found, keep scanning -- a later hard statement such as
        # `git reset --hard` must win and force exit 2 (AC-08 / strictest wins).
        if destructive and not ask_eligible:
            break
        toks = tokens_of(stmt)
        idx = command_start(toks)
        if idx >= len(toks):
            continue
        cmd = os.path.basename(toks[idx])
        args = toks[idx + 1:]
        if is_fs_destructive(cmd, args):
            destructive = True
            ask_eligible = False
            break
        if cmd != 'git':
            all_git = False
            continue
        subcmd, git_args, config_values = parse_git(args)
        # An empty heredoc list means the stdin was not visible (a pipe), which is
        # unclassifiable for update-ref --stdin -> fail closed there.
        if is_destructive(subcmd, git_args, config_values,
                          heredoc_bodies if heredoc_bodies else None):
            destructive = True
            if is_ask_class(subcmd, git_args, config_values):
                has_ask = True
            else:
                ask_eligible = False
        if is_mutation(subcmd, git_args):
            mutation = True
            if not is_addcommit_scope(subcmd, git_args):
                mutation_scope_broad = True
        if subcmd == 'commit' and bom == 'none':
            bom = commit_message_bom(git_args, root)
        # No break here: #1217 must keep scanning after an ask-class delete so a
        # later hard statement can revoke ask eligibility (the top-of-loop guard
        # stops only once a hard verdict makes the strictest class final).

    category = 'destructive' if destructive else ('mutation' if mutation else 'none')
    # #1151 F6-08: a fork-bomb verdict reports scope 'forkbomb' so the block
    # message names the fork-bomb scan only when it fired (scope is otherwise
    # irrelevant for 'destructive').
    scope = 'forkbomb' if fork_bomb else ('broad' if mutation_scope_broad else 'narrow')
    ask_class = 1 if (destructive and has_ask and ask_eligible) else 0
    return f'{category} {scope} {bom} {1 if all_git else 0} {ask_class}'


def main(argv: list[str], stdin: str) -> int:
    """Print '<category> <scope> <bom> <all_git> <ask_class>'."""
    if len(argv) != 1:
        return 1
    print(classify(stdin, argv[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], sys.stdin.buffer.read().decode('utf-8', 'surrogateescape')))
