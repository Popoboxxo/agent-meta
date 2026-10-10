#!/bin/bash
# hook: dod-push-check
# version: 2.1.0
# event: PreToolUse
# matcher: Bash
# provider: Claude
# description: Blocks git push on/to main/master (Branch-Guard) and until tests are green (DoD enforcement)
# enabled_by_default: false
# changelog: v2.1.0: push detection by command word incl. global options/wrappers, no false positives on quoted/echoed text (SR-B-03/04), Branch-Guard checks destination refs and blocks --all/--mirror/detached pushes (SR-B-02), no SIGPIPE fail-open on large commands (SR-B-21), scoped boundary wording (SR-B-07); v2.0.3: per-statement tag-only push detection with flag allowlist, --no-tags, redirects, line continuations, fail-closed parsing (SR-B-01); v2.0.2: fix pipefail propagation in TEST_CMD subshell (#753)

set -uo pipefail

# Claude Code passes hook context as JSON on stdin.
# Exit 0 = allow, exit 2 = block. On exit 2 only *stderr* is fed back to the
# model as the block reason (see orchestrator-guard.sh header note, issue
# #396) — every message on a blocking path in this script goes to stderr
# (issue #593). stdout is used only for non-blocking progress/status text.

# --- Shared helper lib + fail-closed python check (issue #595) ---------
# For THIS check (dependency availability) the hook acts as a security
# boundary — see .claude/rules/branch-guard.md#guard-terminologie for the
# convention-vs-security-boundary distinction: it must not silently allow a
# push through just because python3 or the helper lib went missing (which
# could be as simple as a broken PATH, or as deliberate as an attacker trying
# to disable the gate). Fail CLOSED instead. Otherwise (Branch-Guard command
# classification, test gate, result cache) the hook is a convention
# boundary: a best-effort token scan, not a shell interpreter — indirection
# such as eval/$(...)-in-quotes/aliases (#592) or a hand-written cache file
# can still get a push past it. Classification doubt fails closed.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! source "$SCRIPT_DIR/lib/hook_common.sh" 2>/dev/null; then
  echo "DoD-Check: required helper $SCRIPT_DIR/lib/hook_common.sh is missing or unreadable." >&2
  echo "Failing closed (issue #595) — re-run sync.py to redeploy the hooks/lib/ directory." >&2
  exit 2
fi

# This script (read_config_var, tag-only-push detection below) hardcodes
# the "python3" binary name throughout, unlike hook_common.sh's generic
# python3/python fallback — checked explicitly here rather than via
# hook_have_python so a "python-but-no-python3" system doesn't pass this
# check and then silently fail every later python3 invocation.
if ! command -v python3 >/dev/null 2>&1; then
  echo "DoD-Check: python3 not found on PATH." >&2
  echo "Failing closed (issue #595) — Branch-Guard/test gate cannot be evaluated without it." >&2
  echo "Install python3 or restore PATH to unblock this guard." >&2
  exit 2
fi

INPUT=$(cat)
TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")
COMMAND=$(hook_json_get "$INPUT" "tool_input.command")

# Only intercept Bash tool calls
[ "$TOOL_NAME" = "Bash" ] || exit 0

# Cheap pre-filter: a push needs the word 'push' somewhere (quotes/backslashes
# between the letters tolerated, e.g. pu''sh). The precise per-statement
# classification below decides; this only skips the python startup for the
# common case. Here-string, NOT `printf | grep -q`: under pipefail a writer
# killed by SIGPIPE after grep's early exit made the pipeline fail and
# `|| exit 0` allowed large multi-line pushes through (SR-B-21).
_Q="[\"'\\\\]*"
# Only rc 1 (no match) skips; a grep error (rc 2) falls through (fail closed).
grep -qE "p${_Q}u${_Q}s${_Q}h" <<<"$COMMAND"
[ $? -eq 1 ] && exit 0

# --- Resolve project config file ---
# Config layout since agent-meta v0.26+: .meta-config/project.yaml (YAML).
# Legacy fallback: agent-meta.config.json at the project root (pre-0.26).
# Walk up the directory tree until a config is found.
CONFIG_FILE=""
DIR="$PWD"
for _ in 1 2 3 4 5 6; do
  if [ -f "$DIR/.meta-config/project.yaml" ]; then
    CONFIG_FILE="$DIR/.meta-config/project.yaml"
    break
  fi
  if [ -f "$DIR/agent-meta.config.json" ]; then
    CONFIG_FILE="$DIR/agent-meta.config.json"
    break
  fi
  [ "$DIR" = "/" ] && break
  DIR="$(dirname "$DIR")"
done

# read_config_var <config_file> <variable_name>
# Reads variables.<name> from a project config. Supports YAML (project.yaml)
# and legacy JSON (agent-meta.config.json). Prefers PyYAML, falls back to a
# stdlib-only scan of the top-level `variables:` block so the hook never needs
# a third-party dependency in the target project.
read_config_var() {
  python3 - "$1" "$2" <<'PYEOF' 2>/dev/null
import sys
path, key = sys.argv[1], sys.argv[2]
val = ""
try:
    if path.endswith(".json"):
        import json
        with open(path, encoding="utf-8") as f:
            data = json.load(f) or {}
        val = str(data.get("variables", {}).get(key, ""))
    else:
        try:
            import yaml
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            val = str(data.get("variables", {}).get(key, ""))
        except Exception:
            # stdlib-only fallback: scan the top-level `variables:` block
            in_vars = False
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.rstrip("\n")
                    if line.startswith("variables:"):
                        in_vars = True
                        continue
                    if in_vars:
                        if line and not line[0].isspace():
                            break
                        s = line.strip()
                        if s.startswith(key + ":"):
                            v = s[len(key) + 1:].strip()
                            if len(v) >= 2 and v[0] in "\"'" and v[-1] == v[0]:
                                v = v[1:-1]
                            val = v
                            break
except Exception:
    val = ""
print(val)
PYEOF
}

# --- Tag-only push detection ---
# A tag push (`git push origin v1.2.3`, `git push origin --tags`,
# `git push origin tag v1.2.3`, `git push origin refs/tags/v1.2.3`) does not
# touch any branch ref — it cannot add commits to main/master, which is the
# entire premise the Branch-Guard below exists to prevent. Without this
# check, cutting a release while sitting on main (the normal place to be
# right after a release PR merges) was blocked identically to an actual
# direct push of main's commit history, even though the two are unrelated
# in risk. Not a full shell parser (matches this repo's other hooks'
# documented approach) — covers the realistic `git push <remote> <ref>` /
# `--tags` / `tag <name>` forms; anything else (bare `git push`, `git push
# origin`, an explicit branch ref) still falls through to the branch check.
#
# SR-B-01: classification is per `git push` STATEMENT (split on shell control
# operators, same splitter as orchestrator-guard-impl.sh `statements()`), and
# every ref of every push statement must be a tag ref. The whole command is
# tag-only only if it has >=1 push statement and ALL of them are tag-only —
# `git push origin main --tags` or `git push --tags && git push origin main`
# must still hit the Branch-Guard. Any parse doubt -> not tag-only.
#
# SR-B-03/SR-B-04: a statement is a push only if its COMMAND WORD resolves to
# git with subcommand `push` after git's global options (`git -C . push`,
# `/usr/bin/git push`, `(git push ...)`, `VAR=1 git push`), or if an
# exec-capable wrapper/unknown command carries a `git [opts] push` in its args
# (`sudo git push`, `env X=1 git push`, `timeout 60 git push` — fail closed).
# Commands that never execute their arguments (`echo`, `grep`, `gh`, ...) are
# not pushes even if their text contains "git push".
#
# SR-B-02: the Branch-Guard also checks every DESTINATION ref of each non-tag
# push statement (`HEAD:main`, `feat:main`, `+feat:refs/heads/main`, `:main`,
# `--delete main`, `origin/main`, `--force-with-lease=main`). Bulk/ambiguous
# pushes (`--all`, `--branches`, `--mirror`, wildcard or `:` refspecs,
# unknown/abbreviated push options) and refspec-less pushes from a detached
# HEAD are blocked because the destination cannot be determined safely.
#
# Classifier output (one line): none | tag | push | block <reason>.
# Anything else (python crash, empty output) blocks (fail closed). The
# command is passed on fd 3 (here-string): argv/env cap a single string at
# 128 KB (E2BIG) and a pipe writer can die from SIGPIPE (SR-B-21).

# Resolve GIT_MAIN_BRANCH: env var > project config > default "main"
MAIN_BRANCH="${AGENT_META_MAIN_BRANCH:-}"
if [ -z "$MAIN_BRANCH" ] && [ -n "$CONFIG_FILE" ]; then
  MAIN_BRANCH=$(read_config_var "$CONFIG_FILE" "GIT_MAIN_BRANCH")
fi
MAIN_BRANCH="${MAIN_BRANCH:-main}"

# Full ref (not --abbrev-ref, which shortens to 'heads/main' when a tag of
# the same name exists); empty = detached HEAD or not inside a repo.
CURRENT_REF=$(git symbolic-ref -q HEAD 2>/dev/null)
CURRENT_BRANCH="${CURRENT_REF#refs/heads/}"

PUSH_CLASS=$(python3 - "$MAIN_BRANCH" "$CURRENT_BRANCH" 3<<<"$COMMAND" <<'PYEOF' 2>/dev/null
import os, re, shlex, subprocess, sys

# git global options that take a separate value token. KEEP IN SYNC with
# GLOBAL_OPTS_WITH_VALUE in hooks/1-generic/orchestrator-guard-impl.sh (the
# authoritative copy, issue #551) — duplicated only because the two hooks
# share no Python lib. '-c'/'--config' are handled separately there.
GLOBAL_OPTS_WITH_VALUE = {
    "-C", "--git-dir", "--work-tree", "--namespace", "--exec-path",
    "--super-prefix", "--config-env", "--attr-source",
}
GIT_OPTS_WITH_VALUE = GLOBAL_OPTS_WITH_VALUE | {"-c", "--config"}

# `git push` flags allowed in a tag-only push (allowlist). Anything else —
# --all/--branches/--mirror/--follow-tags/--recurse-submodules/--prune,
# abbreviations, unknown flags — makes the statement NOT tag-only.
PUSH_FLAGS_SAFE = {
    "--dry-run", "--verbose", "--quiet", "--progress", "--no-progress",
    "--porcelain", "--force", "--atomic", "--no-atomic", "--verify",
    "--no-verify", "--thin", "--no-thin", "--ipv4", "--ipv6", "--delete",
    "--set-upstream", "--force-if-includes", "--no-force-if-includes",
    "--signed", "--no-signed", "--force-with-lease", "--no-force-with-lease",
}
# push long options taking a value ('--opt=v' or '--opt v'); short form: -o
PUSH_OPTS_WITH_VALUE = {"--push-option", "--repo", "--receive-pack", "--exec"}
PUSH_SHORT_SAFE = set("vqnfud46")
# --tags and its unique abbreviations; the last --tags/--no-tags wins (git
# parse-options applies flags left to right). '--t'/'--no-t' are ambiguous
# with --thin and fall through to "unknown" (fail closed).
TAGS_FLAGS = {"--tags", "--tag", "--ta"}
NO_TAGS_FLAGS = {"--no-tags", "--no-tag", "--no-ta"}
# Statement looks like a git push but cannot be resolved -> fail closed.
UNRESOLVED = object()
# Shell redirections incl. their target ('2>&1', '>/dev/null', '> f',
# '&>f', '>|f'), stripped before statement splitting so '2>&1' is neither
# split on '&' nor misread as a ref. A digit prefix counts only as a whole
# word (bash: 'v1>log' is ref 'v1' redirected to 'log').
REDIRECT = re.compile(
    r"(?:(?<![^\s;&|])\d+)?&?(?:>>?|<)(?:&(?:\d+|-)|\|?\s*[^\s;&|<>()]+)")


def ref_exists(ref):
    return subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref],
                          capture_output=True).returncode == 0


def is_tag_ref(ref):
    ref = ref.lstrip("+")
    if ":" in ref:
        # refspec <src>:<dst> — only the destination decides what is updated
        return ref.split(":", 1)[1].startswith("refs/tags/")
    if ref.startswith("refs/tags/"):
        return True
    return ref_exists(f"refs/tags/{ref}") and not ref_exists(f"refs/heads/{ref}")


def is_git(tok):
    return tok == "git" or tok.endswith("/git")


def git_subcommand(toks):
    # toks[0] is git: skip global options (with their values) and return
    # (subcommand or None, args after it).
    j = 1
    while j < len(toks) and toks[j].startswith("-"):
        j += 2 if toks[j] in GIT_OPTS_WITH_VALUE else 1
    if j < len(toks):
        return toks[j], toks[j + 1:]
    return None, []


def push_args(toks):
    # Return the args after 'push' for a `git [global-opts] push ...` token
    # list, None if this statement is not a git push, or UNRESOLVED if it
    # mentions git and push but the first git token does not resolve to
    # 'push' (e.g. 'sudo -u git git push ...') — never silently dropped.
    for i, tok in enumerate(toks):
        if not is_git(tok):
            continue
        sub, args = git_subcommand(toks[i:])
        if sub == "push":
            return args
        break
    if "push" in toks and any(is_git(t) for t in toks):
        return UNRESOLVED
    return None


def stmt_is_tag_only(args):
    tags = False
    pos = []
    i = 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            pos += args[i:]
            break
        if not a.startswith("-") or a == "-":
            pos.append(a)
            continue
        name = a.split("=", 1)[0]
        if a.startswith("--"):
            if name in TAGS_FLAGS or name in NO_TAGS_FLAGS:
                if "=" in a:
                    return False
                tags = name in TAGS_FLAGS
            elif name in PUSH_OPTS_WITH_VALUE:
                if "=" not in a:
                    i += 1  # value is the next token, even if it is '--tags'
            elif name not in PUSH_FLAGS_SAFE:
                return False
            continue
        # short cluster: '-fv', '-o<val>', '-fo <val>'
        for k, ch in enumerate(a[1:], 1):
            if ch == "o":
                if k == len(a) - 1:
                    i += 1
                break
            if ch not in PUSH_SHORT_SAFE:
                return False
    refs = pos[1:]  # pos[0] is the remote
    if tags:
        return not refs
    if not refs:
        return False  # bare push / push <remote> pushes the current branch
    k = 0
    while k < len(refs):
        if refs[k] == "tag":
            if k + 1 >= len(refs):
                return False
            k += 2
            continue
        if not is_tag_ref(refs[k]):
            return False
        k += 1
    return True


MAIN_BRANCH, CURRENT = sys.argv[1], sys.argv[2]  # CURRENT "" = detached
PROTECTED = {"main", "master", MAIN_BRANCH} - {""}

# Shell reserved words / prefixes that precede the real command word.
RESERVED = {"!", "{", "}", "if", "then", "elif", "else", "while", "until",
            "do", "time", "coproc"}
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
# Command words that never execute their arguments: "git push" in their args
# is text, not a push (SR-B-04). Every other non-git command word is treated
# as a possible wrapper (sudo/env/timeout/xargs/...): fail closed.
NON_EXEC = {"echo", "printf", "grep", "egrep", "fgrep", "rg", "ag", "ack",
            "gh", "cat", "head", "tail", "less", "more", "wc", "ls", "man"}
PUNCT = set("();<>|&")
# stands in for a $(...)/<(...) group inside its parent command
COMPUTED = "$(...)"

# push long options the destination check understands; anything else
# (incl. unique abbreviations such as '--mirr' = --mirror) is ambiguous.
PUSH_LONG_KNOWN = (PUSH_FLAGS_SAFE | PUSH_OPTS_WITH_VALUE | TAGS_FLAGS
                   | NO_TAGS_FLAGS | {"--follow-tags", "--no-follow-tags",
                                      "--prune", "--no-prune",
                                      "--recurse-submodules",
                                      "--no-recurse-submodules"})
PUSH_BULK = {"--all", "--branches", "--mirror"}
_remotes = None


def segments(stmt):
    # Tokenize like the shell (quotes, escapes) and nest at unquoted '(' /
    # ')', so '(git push x)', '$(git push x)' and '<(...)' expose 'git' as a
    # command word and 'x)' does not leak into a ref. A closed group leaves
    # COMPUTED in its parent's place ('git push origin $(...)' has a ref the
    # hook cannot know). Returns a list of token lists.
    lex = shlex.shlex(stmt, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    done, stack = [], [[]]
    for tok in lex:  # ValueError on unbalanced quotes
        if not set(tok) <= PUNCT:
            stack[-1].append(tok)
            continue
        for ch in tok:
            if ch == "(":
                if stack[-1] and stack[-1][-1].endswith("$"):
                    stack[-1][-1] = stack[-1][-1][:-1]  # '$(' / 'x=$('
                    if not stack[-1][-1]:
                        stack[-1].pop()
                stack.append([])
            elif ch == ")" and len(stack) > 1:
                done.append(stack.pop())
                if stack[-1]:
                    stack[-1].append(COMPUTED)
    return [s for s in done + stack if s]


def segments_ok(stmt):
    try:
        segments(stmt)
        return True
    except ValueError:
        return False


def segment_push_args(toks):
    # args after 'push' / None / UNRESOLVED, decided by the command word.
    i = 0
    while i < len(toks) and (toks[i] in RESERVED or ASSIGNMENT.match(toks[i])):
        i += 1
    if i >= len(toks):
        return None
    word = toks[i]
    if is_git(word):
        sub, args = git_subcommand(toks[i:])
        return args if sub == "push" else None
    if os.path.basename(word) in NON_EXEC:
        return None
    return push_args(toks[i + 1:])


def remotes():
    global _remotes
    if _remotes is None:
        out = subprocess.run(["git", "remote"], capture_output=True, text=True)
        _remotes = set(out.stdout.split())
    return _remotes


def is_protected(dst):
    if dst.startswith("refs/heads/"):
        dst = dst[len("refs/heads/"):]
    elif dst.startswith("refs/remotes/"):
        dst = dst[len("refs/remotes/"):].partition("/")[2]
    elif "/" in dst and dst.split("/", 1)[0] in remotes():
        dst = dst.split("/", 1)[1]
    return dst in PROTECTED


def destination_block(args):
    # Reason string if this (non-tag-only) push statement may update a
    # protected branch or its destination cannot be determined; else None.
    pos = []
    i = 0
    while i < len(args):
        a = args[i]
        i += 1
        if a == "--":
            pos += args[i:]
            break
        if not a.startswith("-") or a == "-":
            pos.append(a)
            continue
        name, _, val = a.partition("=")
        if a.startswith("--"):
            if name in PUSH_BULK:
                return f"'{name}' pushes many refs, destination cannot be determined"
            if name not in PUSH_LONG_KNOWN:
                return f"unknown push option '{name}', destination cannot be determined"
            if name == "--force-with-lease" and val and is_protected(val.split(":", 1)[0]):
                return f"'{a}' targets protected branch"
            if name in PUSH_OPTS_WITH_VALUE and not val:
                i += 1
            continue
        for k, ch in enumerate(a[1:], 1):
            if ch == "o":
                if k == len(a) - 1:
                    i += 1
                break
            if ch not in PUSH_SHORT_SAFE:
                return f"unknown push option '-{ch}', destination cannot be determined"
    refs = pos[1:]  # pos[0] is the remote
    if not refs:
        if not CURRENT:
            return "no explicit refspec on a detached HEAD (or outside a repo), destination cannot be determined"
        return None  # pushes the current branch: checked by the caller
    k = 0
    while k < len(refs):
        ref = refs[k]
        k += 1
        if ref == "tag":
            k += 1  # 'tag <name>' only touches refs/tags/
            continue
        spec = ref.lstrip("+")
        if "$" in spec or "`" in spec:  # incl. COMPUTED
            return f"refspec '{ref}' is computed at run time, destination cannot be determined"
        if "*" in spec or spec == ":":
            return f"refspec '{ref}' pushes many refs, destination cannot be determined"
        src, colon, dst = spec.partition(":")
        if not colon or not dst:
            dst = src
        if dst in ("HEAD", "@"):
            if not CURRENT:
                return f"refspec '{ref}' from detached HEAD, destination cannot be determined"
            dst = CURRENT
        if is_protected(dst):
            return f"destination '{dst}' of refspec '{ref}' is a protected branch"
    return None


def classify(cmd):
    # bash drops backslash-newline before parsing: join continued lines first
    cmd = REDIRECT.sub(" ", cmd.replace("\\\n", ""))
    pushes = []
    stmts = re.split(r"&&|\|\||;|\||&|\n", cmd)
    for stmt in stmts:
        plain = re.sub(r"[\"'\\]", "", stmt)
        if "push" not in plain:
            continue
        segs = None
        # A quote opened here and closed on a later line (multi-line -m/--body
        # text) leaves the command word intact: re-parse with the quote
        # closed. Still unparseable and mentions git -> fail closed.
        for suffix in ("", '"', "'"):
            try:
                segs = list(segments(stmt + suffix))
                break
            except ValueError:
                pass
        if segs is None:
            if "git" in plain:
                return "block unparseable statement mentions git push"
            continue
        for toks in segs:
            args = segment_push_args(toks)
            if args is UNRESOLVED:
                return "block unresolvable git push statement"
            if args is not None:
                pushes.append(args)
    if not pushes:
        return "none"
    non_tag = [a for a in pushes if not stmt_is_tag_only(a)]
    # B-01: any unparseable statement (a quote may hide a push) -> not tag-only
    if not non_tag and all(segments_ok(s) for s in stmts):
        return "tag"
    for args in non_tag:
        reason = destination_block(args)
        if reason:
            return "block " + reason
    return "push"


try:
    with os.fdopen(3, encoding="utf-8", errors="surrogateescape") as fh:
        print(classify(fh.read()))
except Exception as exc:  # fail closed on any classifier bug
    print(f"block classifier error ({type(exc).__name__})")
PYEOF
)

case "$PUSH_CLASS" in
  none) exit 0 ;;
  tag) IS_TAG_ONLY_PUSH=true ;;
  push) IS_TAG_ONLY_PUSH=false ;;
  *)
    _REASON="${PUSH_CLASS#block }"
    [ "${PUSH_CLASS%% *}" = "block" ] || _REASON="push classification failed (fail closed)"
    echo "Branch-Guard: Push blocked — $_REASON." >&2
    echo "Protected branches: $MAIN_BRANCH, main, master. Push a feature branch and open a PR instead." >&2
    echo "" >&2
    echo "If this is intentional (release, hotfix), disable the hook temporarily:" >&2
    echo "  Remove dod-push-check from hooks in .meta-config/project.yaml, re-sync, push, re-enable." >&2
    exit 2
    ;;
esac

# --- Branch-Guard: block push while on a protected branch ---
if [ "$IS_TAG_ONLY_PUSH" != "true" ] && { [ "$CURRENT_BRANCH" = "$MAIN_BRANCH" ] || [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; }; then
  echo "Branch-Guard: Push blocked — you are on '$CURRENT_BRANCH'." >&2
  echo "Create a feature branch first: git checkout -b feat/<topic>" >&2
  echo "Direct pushes to $MAIN_BRANCH are not allowed by DoD policy." >&2
  echo "" >&2
  echo "If this is intentional (release, hotfix), disable the hook temporarily:" >&2
  echo "  Remove dod-push-check from hooks in .meta-config/project.yaml, re-sync, push, re-enable." >&2
  exit 2
fi

# --- Test-Gate: block push if tests fail ---
# Resolve TEST_COMMAND: env var > project config
TEST_CMD="${AGENT_META_TEST_COMMAND:-}"

if [ -z "$TEST_CMD" ] && [ -n "$CONFIG_FILE" ]; then
  TEST_CMD=$(read_config_var "$CONFIG_FILE" "TEST_COMMAND")
fi

if [ -z "$TEST_CMD" ] && [ -z "$CONFIG_FILE" ]; then
  # No config file located at all — surface this instead of silently skipping.
  # Not a block (exit 0) so stdout is fine here (issue #593 only requires
  # stderr for messages on a *blocking* path).
  echo "DoD-Check: no project config found (.meta-config/project.yaml)."
  echo "The test gate could not be evaluated. Either run from within the project,"
  echo "or export AGENT_META_TEST_COMMAND='<your-test-command>' to enable it."
  echo "Push allowed (Branch-Guard passed, but test gate was NOT enforced)."
  exit 0
fi

if [ -z "$TEST_CMD" ]; then
  echo "DoD-Check: TEST_COMMAND not configured — skipping test gate."
  echo "Set variables.TEST_COMMAND in .meta-config/project.yaml or"
  echo "export AGENT_META_TEST_COMMAND='<your-test-command>' to enable."
  echo "Push allowed (Branch-Guard passed, no test gate configured)."
  exit 0
fi

# --- Result cache keyed by commit SHA (issue #594) ----------------------
# A full test suite run inline on every single `git push` can block for
# minutes with no cap, even when nothing test-relevant changed since the
# last push of the exact same tree (e.g. re-pushing after a rejected push,
# or pushing the same commit to a second remote). Cache the last PASSING
# (HEAD sha, TEST_CMD) pair per-repo under .git/ (never synced, never
# committed) and skip straight to "allow" on a cache hit. Any change to
# either the commit or the configured TEST_CMD invalidates the cache.
GIT_DIR=$(git rev-parse --git-dir 2>/dev/null || echo "")
HEAD_SHA=$(git rev-parse HEAD 2>/dev/null || echo "")
CACHE_FILE=""
if [ -n "$GIT_DIR" ] && [ -n "$HEAD_SHA" ]; then
  CACHE_FILE="$GIT_DIR/agent-meta-dod-push-check-cache"
  if [ -f "$CACHE_FILE" ] && [ "$(cat "$CACHE_FILE" 2>/dev/null)" = "$HEAD_SHA
$TEST_CMD" ]; then
    echo "DoD-Check: tests already passed for commit ${HEAD_SHA:0:12} with this TEST_COMMAND (cached) — skipping re-run."
    echo "Delete $CACHE_FILE to force a re-run."
    exit 0
  fi
fi

# --- Timeout (issue #594) ------------------------------------------------
# Resolve TEST_TIMEOUT (seconds): env var > project config > default 300s.
TEST_TIMEOUT="${AGENT_META_TEST_TIMEOUT:-}"
if [ -z "$TEST_TIMEOUT" ] && [ -n "$CONFIG_FILE" ]; then
  TEST_TIMEOUT=$(read_config_var "$CONFIG_FILE" "TEST_TIMEOUT")
fi
TEST_TIMEOUT="${TEST_TIMEOUT:-300}"

echo "DoD-Check: Running '$TEST_CMD' (timeout: ${TEST_TIMEOUT}s)..."
_TEST_RC=0
if command -v timeout >/dev/null 2>&1; then
  # Note: TEST_CMD executed via bash -c (no eval) — value from project.yaml
  # Issue #753: inject set -uo pipefail so pipeline exit codes are not masked
  timeout "${TEST_TIMEOUT}s" bash -c "set -uo pipefail; $TEST_CMD" 2>&1 || _TEST_RC=$?
else
  echo "DoD-Check: 'timeout' command not available on this system — running the test gate without a hard time limit." >&2
  bash -c "set -uo pipefail; $TEST_CMD" 2>&1 || _TEST_RC=$?
fi

if [ "$_TEST_RC" -ne 0 ]; then
  echo "" >&2
  if [ "$_TEST_RC" -eq 124 ] && command -v timeout >/dev/null 2>&1; then
    echo "DoD-Check TIMED OUT after ${TEST_TIMEOUT}s: '$TEST_CMD'." >&2
    echo "Raise the limit via variables.TEST_TIMEOUT in .meta-config/project.yaml (or AGENT_META_TEST_TIMEOUT), or fix a hanging test." >&2
  else
    echo "DoD-Check FAILED: Tests must pass before pushing." >&2
  fi
  echo "Fix failing tests and retry, or disable the hook temporarily." >&2
  exit 2
fi

if [ -n "$CACHE_FILE" ]; then
  mkdir -p "$(dirname "$CACHE_FILE")" 2>/dev/null || true
  printf '%s\n%s' "$HEAD_SHA" "$TEST_CMD" > "$CACHE_FILE" 2>/dev/null || true
fi

echo "DoD-Check passed."
exit 0
