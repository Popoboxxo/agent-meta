#!/usr/bin/env python3
"""Command-word resolution for shared hook shell scans.

Issue #1238a: importable logic plus a byte-identical source emitter.
This module is stdlib-only.
"""
import os
import re
import sys
from pathlib import Path

# agent-meta:emit-start
# Shell keywords / grouping tokens that may precede the real command word.
# `in` is a bash reserved word, never a command: it is the separator a `case`
# list carries when the splitter cuts `case WORD` and `in PATTERN)` onto
# different statements.
LEADING_KEYWORDS = {
    '!', '(', ')', '{', '}', 'if', 'then', 'else', 'elif', 'while', 'until',
    'do', 'done', 'fi', 'esac', 'in',
}
# Command wrappers whose option-before-command form must not hide the real
# command word. Maps a wrapper to (its short/long options that consume a
# value token, its count of leading non-option arguments before the wrapped
# command word).
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
    # listing them as value-taking would swallow the wrapped command word.
    'setsid': (set(), 0),
    'watch': ({'-n', '--interval', '-q', '--equexit'}, 0),
    'strace': ({'-o', '--output', '-p', '--attach', '-e', '--trace',
                '-s', '--string-limit', '-u', '--user', '-a', '--columns',
                '-b', '-I', '-O', '-S', '-X', '-E', '-P'}, 0),
    'chroot': ({'-u', '--userspec', '-g', '--groups'}, 1),
    'busybox': (set(), 0),
}


def _empty_parens(toks, i):
    # shlex with punctuation_chars groups ADJACENT punctuation as one token,
    # so 'f()' yields the pair '()' while '( git' yields '('.
    if i < len(toks) and toks[i] == '()':
        return 1
    if i + 1 < len(toks) and toks[i] == '(' and toks[i + 1] == ')':
        return 2
    return 0


def _close_paren_run(tok):
    # A case-pattern terminator. shlex groups ADJACENT punctuation into one
    # token, so the ')' closing a pattern can arrive as ')' or -- for an
    # extglob pattern such as `@(a|b))` -- as '))'.
    return bool(tok) and tok.strip(')') == ''


def command_start(toks):
    i, n = 0, len(toks)
    while i < n:
        t = toks[i]
        base = os.path.basename(t)
        if t == '--':
            i += 1
            continue
        if t in LEADING_KEYWORDS:
            i += 1
            continue
        if t and t.strip('()') == '':
            i += 1
            continue
        if re.match(r'^[A-Za-z_][A-Za-z0-9_]*=', t):
            i += 1
            continue
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
        # A later case arm arrives as its own statement
        # ('PATTERN) command'); a bare word directly followed by a ')' run
        # is never a command outside `case`.
        if i + 1 < n and _close_paren_run(toks[i + 1]):
            i += 2
            continue
        parens = _empty_parens(toks, i + 1)
        if parens and re.match(r'^[A-Za-z_][A-Za-z0-9_]*$', t):
            i += 1 + parens
            if i < n and toks[i] == '{':
                i += 1
            continue
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
# agent-meta:emit-end


_EMIT_START = "# agent-meta:emit-start\n"
_EMIT_END = "# agent-meta:emit-end\n"


def _emitted_source() -> str:
    source = Path(__file__).read_text(encoding="utf-8")
    start = source.index(_EMIT_START) + len(_EMIT_START)
    end = source.index(_EMIT_END, start)
    return source[start:end]


def main(argv: list[str], stdin: str) -> int:
    """Emit the source fragment consumed by composite hook calls."""
    del argv, stdin
    sys.stdout.write(_emitted_source())
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:], ""))
