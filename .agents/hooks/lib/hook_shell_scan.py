#!/usr/bin/env python3
"""Shell statement scanning and fork-bomb detection for hooks.

Issue #1238a: importable logic plus a byte-identical source emitter.
This module is stdlib-only.
"""
import sys
from pathlib import Path

# agent-meta:emit-start
_IDENT_CHARS = frozenset(
    'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_:'
)
_WS = ' \t'
_MAX_FUNC_BODY = 512
_MAX_SUBST_DEPTH = 32


def _skip_quoted(text, j, q):
    # j is just past the opening quote q; return the index past its closer
    # (len(text) when unclosed). A backslash escapes inside "..." only.
    n = len(text)
    while j < n:
        c = text[j]
        if c == '\\' and q == '"':
            j += 2
            continue
        if c == q:
            return j + 1
        j += 1
    return n


def command_substitutions(text):
    # Bodies of the top-level $(...) / `...` substitutions in one statement,
    # found outside single quotes and ANSI-C strings (so also inside "...",
    # #1151 F6-03). An unclosed substitution yields the rest of the text:
    # over-scan, never under-scan. '$((...))' yields '(...)', which is harmless.
    out = []
    i, n = 0, len(text)
    dq = False
    while i < n:
        c = text[i]
        if c == '\\':
            i += 2
            continue
        if c == '"':
            dq = not dq
            i += 1
            continue
        if not dq and c == "'":
            i = _skip_quoted(text, i + 1, "'")
            continue
        if not dq and c == '$' and text[i + 1:i + 2] == "'":
            j = i + 2
            while j < n and text[j] != "'":
                j += 2 if text[j] == '\\' else 1
            i = j + 1
            continue
        if c == '`':
            j = i + 1
            while j < n and text[j] != '`':
                j += 2 if text[j] == '\\' else 1
            out.append(text[i + 1:j])
            i = j + 1
            continue
        if c == '$' and text[i + 1:i + 2] == '(':
            depth = 1
            j = i + 2
            while j < n:
                ch = text[j]
                if ch == '\\':
                    j += 2
                    continue
                if ch in ("'", '"'):
                    j = _skip_quoted(text, j + 1, ch)
                    continue
                if ch == '(':
                    depth += 1
                elif ch == ')':
                    depth -= 1
                    if depth == 0:
                        break
                j += 1
            out.append(text[i + 2:j])
            i = j + 1
            continue
        i += 1
    return out


def split_shell_statements_and_clean(command):
    """Return (statements, code_without_heredoc_bodies).

    The second value keeps the original operators/quotes but drops heredoc
    body lines and trailing comments (the same comment rule the statement
    stream uses -- review finding F4), so a fork-bomb-shaped STRING in a
    heredoc or a comment is not misclassified while ':(){ :|:& };:' (split
    into statements by the operators) is still seen as one line by the
    fork-bomb scanner.
    """
    statements, bodies, _ops, code = _split_shell_core(command, 0)
    return list(zip(statements, bodies)), code


def split_shell_statements_with_ops(command):
    statements, bodies, ops, _code = _split_shell_core(command, 0)
    return list(zip(statements, bodies, ops))


def _split_shell_core(command, depth):
    statements = []
    bodies = []
    ops = []
    pending = []  # (delimiter, strip_leading_tabs, statement_index)
    kept_lines = []
    buf = []
    quote = None
    subst = 0
    backtick = False
    word_start = True
    lines = command.split('\n')
    li = 0

    def flush(op):
        text = ''.join(buf).strip()
        del buf[:]
        if text:
            statements.append(text)
            bodies.append([])
            ops.append(op)
            for inner in command_substitutions(text):
                if depth >= _MAX_SUBST_DEPTH:
                    raise ValueError('command substitution nested too deeply')
                inner_stmts, inner_bodies, _o, _c = _split_shell_core(inner, depth + 1)
                statements.extend(inner_stmts)
                bodies.extend(inner_bodies)
                ops.extend(['subst'] * len(inner_stmts))

    while li < len(lines):
        line = lines[li]
        li += 1
        i = 0
        continued = False
        # Index where a trailing comment starts (len(line) = no comment). The
        # cleaned code keeps only line[:comment_at], matching the statement
        # stream, which drops the comment text as well (review finding F4).
        comment_at = len(line)
        while i < len(line):
            c = line[i]
            if quote == "'":
                buf.append(c)
                i += 1
                if c == "'":
                    quote = None
                continue
            if quote == 'ansi':
                # $'...' (ANSI-C quoting): a backslash escapes the next
                # character, so \' does not terminate the string (review
                # finding F1). This is the one shell mode whose escaping
                # differs from a plain single-quoted string.
                if c == '\\':
                    if i + 1 < len(line):
                        buf.append(line[i:i + 2])
                        i += 2
                    else:
                        continued = True
                        i += 1
                    continue
                buf.append(c)
                i += 1
                if c == "'":
                    quote = None
                continue
            if quote == '"' or quote == 'locale':
                # Plain double quotes and $"..." (locale translation) share
                # the same delimiter rules. The scanner treats a backslash as
                # escaping ANY next character (bash only special-cases $, `,
                # ", \ and newline) -- a superset that keeps the closing quote
                # correct without changing where the region ends.
                if c == '\\':
                    if i + 1 < len(line):
                        buf.append(line[i:i + 2])
                        i += 2
                    else:
                        continued = True
                        i += 1
                    continue
                buf.append(c)
                i += 1
                if c == '"':
                    quote = None
                continue
            # unquoted context
            if c == '\\':
                if i + 1 < len(line):
                    buf.append(line[i:i + 2])
                    i += 2
                else:
                    continued = True
                    i += 1
                word_start = False
                continue
            if backtick:
                buf.append(c)
                i += 1
                if c == '`':
                    backtick = False
                continue
            if c == '`':
                backtick = True
                buf.append(c)
                i += 1
                word_start = False
                continue
            if c == '$' and i + 1 < len(line) and line[i + 1] == '(':
                subst += 1
                buf.append('$(')
                i += 2
                word_start = False
                continue
            if c == '$' and i + 1 < len(line) and line[i + 1] in ("'", '"'):
                # $'...' / $"...": the '$' prefixes the quoting mode instead
                # of being ordinary text. Without this the single quote inside
                # $'it\'s' was read as a plain quote and closed on the \' .
                quote = 'ansi' if line[i + 1] == "'" else 'locale'
                buf.append(line[i:i + 2])
                i += 2
                word_start = False
                continue
            if subst > 0:
                if c == '(':
                    subst += 1
                elif c == ')':
                    subst -= 1
                buf.append(c)
                i += 1
                word_start = False
                continue
            if c == "'" or c == '"':
                quote = c
                buf.append(c)
                i += 1
                word_start = False
                continue
            if c == '#' and word_start:
                comment_at = i  # comment runs to end of line
                i = len(line)
                break
            if c in _WS:
                buf.append(c)
                i += 1
                word_start = True
                continue
            if c in (';', '|', '&'):
                if line[i:i + 2] in ('&&', '||'):
                    op = line[i:i + 2]
                    i += 2
                else:
                    op = c
                    i += 1
                flush(op)
                word_start = True
                continue
            if c == '<' and i + 1 < len(line) and line[i + 1] == '<':
                j = i + 2
                strip_tabs = False
                if j < len(line) and line[j] == '-':
                    strip_tabs = True
                    j += 1
                while j < len(line) and line[j] in _WS:
                    j += 1
                delim = ''
                if j < len(line) and line[j] in ("'", '"'):
                    q = line[j]
                    j += 1
                    start = j
                    while j < len(line) and line[j] != q:
                        j += 1
                    delim = line[start:j]
                    if j < len(line):
                        j += 1
                else:
                    if j < len(line) and line[j] == '\\':
                        j += 1  # <<\EOF: the backslash escapes the delimiter
                    start = j
                    while j < len(line) and line[j] not in ' \t;&|<>()':
                        j += 1
                    delim = line[start:j]
                if delim and '$' not in delim and '`' not in delim:
                    pending.append((delim, strip_tabs, len(statements)))
                buf.append(line[i:j])
                i = j
                word_start = False
                continue
            buf.append(c)
            i += 1
            word_start = False

        # Keep only the code part of the physical line (a trailing comment is
        # NOT code). This is appended before heredoc bodies are consumed below,
        # so an opening line is kept while its body is dropped.
        kept_lines.append(line[:comment_at])
        # End of physical line. A still-open quote / substitution / backtick
        # keeps accumulating (a newline inside it is literal); a trailing
        # backslash joins the NEXT line without inserting a newline.
        if quote is not None or subst > 0 or backtick:
            buf.append('\n')
            continue
        if continued:
            continue
        flush('\n')
        for delim, strip_tabs, idx in pending:
            body_lines = []
            while li < len(lines):
                raw = lines[li]
                li += 1
                check = raw.lstrip('\t') if strip_tabs else raw
                if check.rstrip('\r').rstrip() == delim:
                    kept_lines.append(raw)  # keep the terminator, drop the body
                    break
                body_lines.append(raw)
            if idx < len(bodies):
                bodies[idx].append('\n'.join(body_lines))
        pending = []
        word_start = True

    if quote is not None or subst > 0 or backtick:
        buf.append('\n')
    flush('')
    return statements, bodies, ops, '\n'.join(kept_lines)


def split_shell_statements(command):
    return split_shell_statements_and_clean(command)[0]


def strip_quoted(command):
    # Remove single/double-quoted spans so a fork-bomb-looking STRING literal
    # (e.g. an echo argument) is not misclassified (#602/#809). Best-effort:
    # backslash-escaped quotes are honoured, no full shell parse.
    out = []
    quote = None
    i = 0
    n = len(command)
    while i < n:
        c = command[i]
        if quote is not None:
            if c == '\\' and quote == '"' and i + 1 < n:
                i += 2
                continue
            if c == quote:
                quote = None
            i += 1
            continue
        if c == '"' or c == "'":
            quote = c
            i += 1
            continue
        if c == '\\' and i + 1 < n:
            out.append(command[i:i + 2])
            i += 2
            continue
        out.append(c)
        i += 1
    return ''.join(out)


def _body_calls_itself_piped(body, name):
    start = 0
    ln = len(body)
    nl = len(name)
    while True:
        k = body.find(name, start)
        if k < 0:
            return False
        start = k + 1
        if k > 0 and (body[k - 1].isalnum() or body[k - 1] in '_:'):
            continue
        j = k + nl
        while j < ln and body[j] in _WS:
            j += 1
        if j >= ln or body[j] != '|':
            continue
        j += 1
        while j < ln and body[j] in _WS:
            j += 1
        if body.startswith(name, j):
            end = j + nl
            if end >= ln or not (body[end].isalnum() or body[end] in '_:'):
                return True


def is_fork_bomb(command):
    # Linear scan for a function definition whose body pipes the function into
    # itself (':(){ :|:& };:' / 'bomb(){ bomb|bomb& }' / 'bomb ( ) { ... }').
    n = len(command)
    i = 0
    while True:
        p = command.find('(', i)
        if p < 0:
            return False
        i = p + 1
        q = p + 1
        while q < n and command[q] in _WS:
            q += 1
        if q >= n or command[q] != ')':
            continue
        e = p
        while e > 0 and command[e - 1] in _WS:
            e -= 1
        s = e
        while s > 0 and command[s - 1] in _IDENT_CHARS:
            s -= 1
        name = command[s:e]
        if not name:
            continue
        if not (name[0].isalpha() or name[0] in '_:'):
            continue
        j = q + 1
        while j < n and command[j] in _WS:
            j += 1
        if j >= n or command[j] != '{':
            continue
        # End the body at the DEPTH-MATCHING '}' inside the window: count the
        # braces (so '{ ...; }' and '${...}' before the self-call do not cut
        # the body short). One forward pass over at most _MAX_FUNC_BODY
        # characters per candidate keeps the scan linear (#1050).
        close = -1
        depth = 1
        end = j + 1 + _MAX_FUNC_BODY
        if end > n:
            end = n
        k = j + 1
        while k < end:
            c = command[k]
            if c == '{':
                depth += 1
            elif c == '}':
                depth -= 1
                if depth == 0:
                    close = k
                    break
            k += 1
        if close < 0:
            # No depth-matching '}' in the first _MAX_FUNC_BODY characters: the
            # body cannot be inspected, so fail closed (block) instead of
            # skipping the header -- a skip is an allow (issue #943).
            return True
        body = command[j + 1:close]
        if name in body and _body_calls_itself_piped(body, name):
            return True
        i = j + 1
    return False
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
