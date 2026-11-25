#!/usr/bin/env python3
"""Bash write-target detection for the deployed repo-containment hook.

Issue #1238b1: importable replacement for the inline Python detector.
The shared shell scanner and resolver are imported from the same deployed lib/.
"""
import sys

sys.dont_write_bytecode = True

from hook_shell_scan import _skip_quoted, split_shell_statements_with_ops
from hook_shell_resolver import command_start


def main(argv: list[str], stdin: str) -> int:
    """Print candidate write targets, one per line."""
    import os
    import re
    import shlex
    import sys

    # Bytes-in (surrogateescape): invalid UTF-8 / a lone surrogate in the command
    # must not crash the detector (the crash used to be a silent allow).
    command = stdin

    # Commands whose operands are created / modified / removed outright.
    WRITE_ALL = {
        "touch", "mkdir", "rmdir", "rm", "truncate", "mkfifo", "mknod", "tee",
    }
    # Commands whose LAST non-flag operand (or -t/--target-directory value) is
    # the destination write target.
    WRITE_DEST = {"cp", "install", "rsync", "scp", "ln"}
    # In-place editors: only the operands are written when -i/--in-place is set.
    INPLACE = {"sed", "perl", "ruby"}
    # Short options of the INPLACE editors that consume a value: the rest of a
    # cluster after them is a script/program, not a flag (so '-e' does not hide a
    # later 'i' in a script argument, and '-e' alone is not an in-place edit).
    INPLACE_VALUE_OPTS = {"e", "f"}


    def tokenize(chunk):
        if not chunk.strip():
            return []
        try:
            lex = shlex.shlex(chunk, posix=True, punctuation_chars="();<>|&")
            lex.whitespace_split = True
            lex.commenters = ""
            return list(lex)
        except Exception:
            return chunk.split()


    def is_flag(token):
        return token.startswith("-") and token != "-"


    def is_dev_target(target):
        return (
            target in ("/dev/null", "/dev/stdout", "/dev/stderr", "/dev/tty", "/dev/zero")
            or target.startswith("/dev/fd/")
            or target.startswith("/proc/self/fd/")
        )


    HOME = os.environ.get("HOME") or os.path.expanduser("~")
    # Variables whose value the hook knows; an unset one stays a '$' word.
    KNOWN_VARS = {"HOME": HOME, "AM_PROJECT_DIR": os.environ.get("AM_PROJECT_DIR")}


    def expand_home(target):
        # '~', '~/x', '~user/x', '$HOME/x' and '${HOME}/x' name a real place
        # outside the repo (#1151 F6-06: they used to be skipped as literal text
        # or as a '$' variable); $AM_PROJECT_DIR is expanded from the hook
        # environment the same way. Any other '$VAR' stays unresolved (known gap).
        if target.startswith("~"):
            return os.path.expanduser(target)
        for name, value in KNOWN_VARS.items():
            if not value:
                continue
            for prefix in ("$" + name, "${" + name + "}"):
                if target == prefix or target.startswith(prefix + "/"):
                    return value + target[len(prefix):]
        return target


    def is_skippable(target):
        target = expand_home(target)
        return (
            not target
            or target == "-"
            or target.startswith("&")
            or target.startswith("$")
            or is_dev_target(target)
        )


    # Options whose value is a write destination (#1151 F6-06). A short option
    # may also carry its value glued ('-o/x') or end a cluster ('-sSLo /x').
    OUTPUT_OPTS = {
        "curl": ({"-o", "--output", "--output-dir"}, "o"),
        "wget": ({"-O", "--output-document", "-o", "--output-file", "-a",
                  "--append-output", "-P", "--directory-prefix"}, "OoaP"),
        "unzip": ({"-d"}, "d"),
    }


    def option_values(args, long_short, cluster_chars):
        values = []
        i = 0
        while i < len(args):
            a = args[i]
            i += 1
            if a.startswith("--"):
                name, eq, val = a.partition("=")
                if name in long_short:
                    if eq:
                        values.append(val)
                    elif i < len(args):
                        values.append(args[i])
                        i += 1
                continue
            if a.startswith("-") and a != "-":
                for k, ch in enumerate(a[1:], start=1):
                    if ch in cluster_chars and "-" + ch in long_short:
                        if k + 1 < len(a):
                            values.append(a[k + 1:])
                        elif i < len(args):
                            values.append(args[i])
                            i += 1
                        break
        return values


    # Old-style tar letters that take the next words as values, in order.
    TAR_OLD_VALUE_LETTERS = "fCbTXLNgKVHI"


    def tar_targets(args):
        # Extraction writes into -C/--directory; creation writes the -f archive.
        # An old-style first word ('cf', 'xzfC') is a cluster whose value letters
        # consume the following words in order ('tar cf /etc/x.tar .').
        old = {}
        rest = args
        flags = ""
        if args and not args[0].startswith("-"):
            flags = args[0]
            rest = args[1:]
            for ch in flags:
                if ch in TAR_OLD_VALUE_LETTERS and rest:
                    old.setdefault(ch, rest[0])
                    rest = rest[1:]
        flags +="".join(a.lstrip("-") for a in rest if a.startswith("-") and not a.startswith("--"))
        longs = {a.split("=", 1)[0] for a in rest if a.startswith("--")}
        extract = "x" in flags or longs & {"--extract", "--get"}
        create = any(c in flags for c in "cruA") or longs & {"--create", "--append", "--update", "--concatenate"}
        targets = []
        if extract:
            targets += ([old["C"]] if "C" in old else []) + option_values(rest, {"-C", "--directory"}, "C")
        if create:
            targets += ([old["f"]] if "f" in old else []) + option_values(rest, {"-f", "--file"}, "f")
        return targets


    GIT_GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace",
                                  "--config-env", "--exec-path", "--super-prefix"}
    CLONE_OPTS_WITH_VALUE = {"-b", "--branch", "-o", "--origin", "-u", "--upload-pack",
                             "--depth", "--reference", "--reference-if-able",
                             "--separate-git-dir", "--template", "-c", "--config",
                             "-j", "--jobs", "--filter", "--shallow-since",
                             "--shallow-exclude", "--server-option", "--bundle-uri"}


    def git_clone_targets(args):
        # 'git [-C DIR] clone [opts] <repo> [<dir>]' writes <dir> (default: the
        # repo's basename) under DIR or the cwd.
        base = ""
        i = 0
        while i < len(args) and args[i].startswith("-"):
            if args[i] == "-C" and i + 1 < len(args):
                base = os.path.join(base, args[i + 1])
            i += 2 if args[i] in GIT_GLOBAL_OPTS_WITH_VALUE else 1
        if i >= len(args) or args[i] != "clone":
            return []
        positionals = []
        rest = args[i + 1:]
        j = 0
        while j < len(rest):
            a = rest[j]
            j += 1
            if a == "--":
                positionals += rest[j:]
                break
            if a in CLONE_OPTS_WITH_VALUE:
                j += 1
                continue
            if a.startswith("-"):
                continue
            positionals.append(a)
        if not positionals:
            return []
        if len(positionals) >= 2:
            dest = positionals[1]
        else:
            dest = os.path.basename(positionals[0].rstrip("/"))
            if dest.endswith(".git"):
                dest = dest[:-4]
        return [os.path.join(base, expand_home(dest)) if base else dest]


    def split_flags(args):
        """Return (positionals, target_dir) with flags and -t values removed.

        Trailing flags must not be mistaken for the destination: `cp a /etc/b -v`
        used to append '-v' (inside the repo) as the "destination" and allow the
        command (issue #944 SR-B-19).
        """
        positionals = []
        target_dir = None
        i = 0
        while i < len(args):
            a = args[i]
            if a == "--":
                i += 1
                continue
            if a in ("-t", "--target-directory"):
                if i + 1 < len(args):
                    target_dir = args[i + 1]
                    i += 2
                else:
                    i += 1
                continue
            if a.startswith("--target-directory="):
                target_dir = a.split("=", 1)[1]
                i += 1
                continue
            if a.startswith("-t") and len(a) > 2:
                target_dir = a[2:]
                i += 1
                continue
            if is_flag(a):
                i += 1
                continue
            if not is_skippable(a):
                positionals.append(a)
            i += 1
        return positionals, target_dir


    def inplace_requested(args):
        for a in args:
            if a == "--in-place" or a.startswith("--in-place="):
                return True
            if a == "-i" or a.startswith("-i."):
                return True
            if a.startswith("-") and not a.startswith("--") and a != "-":
                for c in a[1:]:
                    if c == "i":
                        return True
                    if c in INPLACE_VALUE_OPTS:
                        break
        return False


    def inplace_operands(args):
        """Operands that the editor writes: script values are not targets."""
        operands = []
        used_e = False
        skip_next = False
        for a in args:
            if skip_next:
                skip_next = False
                continue
            if a in ("-e", "--expression"):
                used_e = True
                skip_next = True
                continue
            if a.startswith("-e") and len(a) > 2 and not a.startswith("--"):
                used_e = True
                continue
            if a in ("-f", "--file"):
                skip_next = True
                continue
            if a.startswith("-f") and len(a) > 2 and not a.startswith("--"):
                continue
            if is_flag(a):
                continue
            if not is_skippable(a):
                operands.append(a)
        if not used_e and operands:
            # sed/perl/ruby: the first non-option operand is the script itself.
            operands = operands[1:]
        return operands


    UNRESOLVED_CWD = "\x01"  # marks a relative target under an unknown directory


    def cd_destination(args, cwds):
        # Directories a cd/pushd/popd may land in; None = cannot be resolved.
        positionals = [a for a in args if not (a.startswith("-") and a != "-")]
        if not positionals:
            return {expand_home("~")}
        dest = expand_home(positionals[0])
        for prefix in ("$PWD", "${PWD}"):
            # $PWD is whichever directory the command is in: relative to each cwd.
            if dest == prefix or dest.startswith(prefix + "/"):
                dest = "." + dest[len(prefix):]
        if dest == "-" or any(ch in dest for ch in "$`*?[{"):
            return {None}
        if os.path.isabs(dest):
            return {dest}
        return {os.path.join(c, dest) if c is not None else None for c in cwds}


    CASE_WORD = re.compile(r"(?<![\w-])(case|esac)(?![\w-])")


    def subshell_parens(statement):
        """('(' count, closing ')' positions, masked text, unquoted text).

        The masked text is the statement with every unquoted $(...) replaced by
        '$_': its body is scanned as separate 'subst' statements, and a 'cd' in
        'X=$(cd ...)' must not be read as the outer command. Only parens outside
        quotes, backticks and $(...) count; the ')' of an empty '()' pair
        (function definition) does not. Positions refer to the masked text.
        """
        n = len(statement)
        opens = 0
        closes = []
        masked = []
        unquoted = []
        last = ""  # last non-blank unquoted character
        i = 0
        while i < n:
            c = statement[i]
            if c == "\\":
                masked.append(statement[i:i + 2])
                i += 2
                continue
            if c in ("'", '"', "`"):
                j = _skip_quoted(statement, i + 1, c)
                masked.append(statement[i:j])
                i = j
                continue
            if c == "$" and statement[i + 1:i + 2] == "(":
                depth, i = 1, i + 2
                while i < n and depth:
                    ch = statement[i]
                    if ch in ("'", '"'):
                        i = _skip_quoted(statement, i + 1, ch)
                        continue
                    depth += (ch == "(") - (ch == ")")
                    i += 2 if ch == "\\" else 1
                masked.append("$_")
                continue
            if c == "(" and not statement[i + 1:].lstrip().startswith(")"):
                opens += 1
            if c == ")" and last != "(":
                closes.append(sum(map(len, masked)))
            masked.append(c)
            unquoted.append(c)
            if not c.isspace():
                last = c
            i += 1
        return opens, closes, "".join(masked), "".join(unquoted)


    def detect(tokens):
        """Return (write targets, command word, its arguments) for one statement."""
        found = []

        # Redirection operators `>`, `>>`, `>|` (and `&>` once the `&` split above
        # has peeled it); the following token is the write target. shlex emits the
        # punctuation as single-character tokens, so collapse a run of '>'/'|'
        # before taking the target ('>> file' must not target '>').
        i = 0
        while i < len(tokens):
            if tokens[i] in (">", ">>", ">|"):
                j = i + 1
                while j < len(tokens) and tokens[j] in (">", "|", ">>", ">|"):
                    j += 1
                if j < len(tokens) and not is_skippable(tokens[j]):
                    found.append(tokens[j])
                i = j + 1
                continue
            i += 1

        # Locate the command with the SHARED resolver (hook_common.sh
        # hook_shell_resolver_py): keywords, `case … in` arms, function bodies,
        # grouping, KEY=VALUE assignments, wrappers (with their positional
        # arity) and a transparent `--` are all handled there, not here. See the
        # header note for the shapes this closed in v1.5.0.
        idx = command_start(tokens)
        cmd = os.path.basename(tokens[idx]) if idx < len(tokens) else ""
        args = tokens[idx + 1:]

        if cmd in WRITE_ALL:
            positionals, _target_dir = split_flags(args)
            found.extend(positionals)
        elif cmd in WRITE_DEST:
            positionals, target_dir = split_flags(args)
            if target_dir is not None:
                if not is_skippable(target_dir):
                    found.append(target_dir)
            elif positionals:
                found.append(positionals[-1])
        elif cmd == "mv":
            positionals, _target_dir = split_flags(args)
            found.extend(positionals)
        elif cmd == "dd":
            for arg in args:
                if arg.startswith("of=") and not is_skippable(arg[3:]):
                    found.append(arg[3:])
        elif cmd in INPLACE:
            if inplace_requested(args):
                found.extend(inplace_operands(args))
        elif cmd in OUTPUT_OPTS:
            found.extend(v for v in option_values(args, *OUTPUT_OPTS[cmd]) if not is_skippable(v))
        elif cmd == "tar":
            found.extend(v for v in tar_targets(args) if not is_skippable(v))
        elif cmd == "git":
            found.extend(v for v in git_clone_targets(args) if not is_skippable(v))
        return found, cmd, args


    def judge(found, cwds):
        for target in found:
            target = expand_home(target)
            if os.path.isabs(target):
                targets.append(target)
                continue
            for cwd in cwds:
                targets.append(UNRESOLVED_CWD + target if cwd is None
                               else os.path.join(cwd, target))


    workdir = argv[0] if argv else ""
    # Every directory the command may be in at this point (#1151 F6-07). A cd
    # joined by '&&' moves the command (it ran only when cd succeeded); after
    # any other separator, a failed cd leaves the old directory in place, so the
    # set is widened instead of replaced. A relative target is judged against
    # every member; an unresolvable member blocks it.
    # A cd inside $(...) or a '( ... )' subshell does not move the outer command:
    # the set is restored once the substitution / subshell ends. Inside, it is
    # tracked as usual (a substitution starts from the directories before AND
    # after its parent statement, and its inner separators count as ';').
    cwds = {workdir}
    before_parent = cwds
    dirstack = []
    subshells = []    # cwds saved at each open '(' subshell
    in_subst = None   # (cwds, len(subshells)) to restore after a substitution run
    case_depth = 0
    targets = []

    for statement, _heredocs, op in split_shell_statements_with_ops(command):
        if op == "subst":
            if in_subst is None:
                in_subst = (cwds, len(subshells))
                cwds = cwds | before_parent
        else:
            if in_subst is not None:
                cwds, depth = in_subst
                del subshells[depth:]
                in_subst = None
            before_parent = cwds
        tokens = tokenize(statement)
        if not tokens:
            continue

        opens, closes, statement, unquoted = subshell_parens(statement)
        words = CASE_WORD.findall(unquoted)
        if case_depth or words:
            # shortcut: a case arm's ')' looks like a subshell close; inside a
            # case no subshell is scoped, so a cd there stays in play (over-block).
            opens, closes = 0, []
        case_depth = max(0, case_depth + words.count("case") - words.count("esac"))
        subshells.extend([cwds] * opens)

        # Text after the last closing ')' (e.g. '> log' in '(cd x && make) > log')
        # runs in the directory restored by that close.
        head, tail = statement, ""
        if closes:
            head, tail = statement[:closes[-1]], statement[closes[-1] + 1:]
        found, cmd, args = detect(tokenize(head))
        judge(found, cwds)

        if cmd in ("cd", "pushd", "popd"):
            if cmd == "popd":
                dest = dirstack.pop() if dirstack else {None}
            elif cmd == "pushd" and not [a for a in args if not a.startswith("-")]:
                dest = {None}  # bare pushd swaps the top two stack entries
            else:
                dest = cd_destination(args, cwds)
            if cmd == "pushd":
                dirstack.append(set(cwds))
            cwds = dest if op == "&&" else (cwds | dest)

        for _ in closes:
            if subshells:
                cwds = subshells.pop()
        if tail.strip():
            judge(detect(tokenize(tail))[0], cwds)

    for target in targets:
        print(target)
    return 0


if __name__ == "__main__":
    command = sys.stdin.buffer.read().decode('utf-8', 'surrogateescape')
    sys.exit(main(sys.argv[1:], command))
