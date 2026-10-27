#!/bin/bash
# hook: dod-push-check
# version: 2.1.6
# event: PreToolUse
# matcher: Bash
# provider: Claude
# description: Blocks git push on/to main/master (Branch-Guard) and until tests are green (DoD enforcement)
# enabled_by_default: false
# changelog: v2.1.6: the protected-branch list in the push-block message is de-duplicated (a configured GIT_MAIN_BRANCH of main/master no longer appears twice) (#1033); v2.1.5: --recurse-submodules=on-demand|only in a repo with submodules (or another repo) fails closed because the submodules push to their own remotes/branches (#953); v2.1.4: a push in a command that changes directory (cd/pushd/popd) is judged as a push into another repository (refspec-less/HEAD pushes blocked, cwd branch and config no longer assumed) (#952); v2.1.3: heredoc bodies fed to a text-only consumer (cat/gh/tee/git commit) are no longer classified as commands (#947), an unquoted word-start # comment is cut before tokenizing while quoted/mid-word # stay literal (#948), xargs carrying a git push and the {} placeholder fail closed (#950), computed-refspec block message names the HEAD / literal-branch way out (#950); v2.1.2: command-running git subcommands carrying a push blocked again (submodule foreach/bisect run git push, rebase -x/filter-branch/difftool -x/config with 'git ... push', R2-1), -c/--config-env aliases resolved or blocked, exec config (core.pager/sshCommand/editor, sequence.editor, ...) on a push or carrying one blocked, rg --pre/ack --pager blocked (R2-5), unreadable Bash command in the payload blocked instead of skipped (R2-2), linear classifier (shlex token buffer, brace/nested scans) + 20 s budget that blocks on overrun (R2-3), backslash-newline inside 'push' and 'alias' reach the classifier (R2-4); v2.1.1: DWIM destinations (heads/main, remotes/<r>/main) protected (F1), pre-filter without here-string + SIGXFSZ ignored so a failed temp file fails closed (F2), quote-aware statements and fail-closed quote repair (QF1), man/less/more/ack no longer treated as text (QF5), one for-each-ref snapshot (A2), refspec-less pushes checked against push.default/branch.<n>.merge/remote.<r>.push and -c overrides (A3), -C/--git-dir/--work-tree/GIT_DIR refspec-less or HEAD pushes blocked (A4), $'..'/$".."/{a,b}/$(..) command words and git-push resolved or blocked (A5); v2.1.0: push detection by command word incl. global options/wrappers, no false positives on quoted/echoed text (SR-B-03/04), Branch-Guard checks destination refs and blocks --all/--mirror/detached pushes (SR-B-02), no SIGPIPE fail-open on large commands (SR-B-21), scoped boundary wording (SR-B-07); v2.0.3: per-statement tag-only push detection with flag allowlist, --no-tags, redirects, line continuations, fail-closed parsing (SR-B-01); v2.0.2: fix pipefail propagation in TEST_CMD subshell (#753)

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
# Known alias/config limits (R2-5): only aliases and exec config declared ON
# THE SAME command line are seen. An alias or core.pager/sshCommand/editor
# set in a config file (repo, global, GIT_CONFIG_GLOBAL=<file>,
# include.path) or exported in an earlier statement/call (`git config
# alias.p push` in one call — blocked only if its value names git+push —
# then `git p origin main` in the next) is invisible: the pre-filter never
# sees 'push'. Likewise a script run by `rebase -x`, `bisect run`,
# `submodule foreach`, hooks or a filter whose text does not contain
# 'git ... push' (e.g. `git rebase -x ./deploy.sh`).
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

# A here-string/here-doc temp file hitting `ulimit -f` must make the
# redirection fail (-> classifier output empty -> block), not kill the hook
# with SIGXFSZ (a non-2 exit status is not a block).
trap '' XFSZ

INPUT=$(cat)
TOOL_NAME=$(hook_json_get "$INPUT" "tool_name")
COMMAND=$(hook_json_get "$INPUT" "tool_input.command")

# R2-2: an empty COMMAND must mean "no command", never "could not extract
# it" (unparseable payload, non-string command, a helper failure): a Bash
# (or unidentifiable) call whose payload holds a non-empty command that did
# not reach us is blocked. An empty command of a non-Bash tool stays allowed.
if [ -z "$COMMAND" ] && { [ -z "$TOOL_NAME" ] || [ "$TOOL_NAME" = "Bash" ]; }; then
  _PAYLOAD_STATE=$(printf '%s' "$INPUT" | python3 -c '
import json, sys
try:
    d = json.loads(sys.stdin.buffer.read().decode("utf-8", "surrogateescape"))
except Exception:
    d = None
ti = d.get("tool_input") if isinstance(d, dict) else None
cmd = ti.get("command") if isinstance(ti, dict) else None
tool = d.get("tool_name") if isinstance(d, dict) else None
if not isinstance(d, dict) or (cmd not in (None, "") and tool in (None, "", "Bash")):
    print("unreadable")
else:
    print("empty")
' 2>/dev/null)
  if [ "$_PAYLOAD_STATE" != "empty" ]; then
    echo "Branch-Guard: Push blocked — the Bash command could not be read from the hook payload (fail closed)." >&2
    echo "Re-issue the command; if it contains unusual bytes (lone surrogates, invalid UTF-8), remove them." >&2
    exit 2
  fi
fi

# Only intercept Bash tool calls (and calls whose tool is unidentifiable)
[ "$TOOL_NAME" = "Bash" ] || [ -z "$TOOL_NAME" ] || exit 0

# Cheap pre-filter: a push needs the word 'push' somewhere (quotes/backslashes/
# '$' and backslash-newline between the letters tolerated, e.g. pu''sh,
# pu$'s'h, pu\<newline>sh) or ANSI-C quoting ($'\x70ush' can spell
# anything) or a git alias declared on the command line ('-c alias.p=push p',
# '--config-env=alias.p=VAR p', any case). The precise per-statement
# classification below decides; this only skips the python startup for the
# common case. Pure bash: no fork, no pipe (SIGPIPE under pipefail,
# SR-B-21) and no here-string temp file (a failed redirection returned rc 1
# = "no match").
_Q="[\"'\\\\\$"$'\n'"]*"
_PUSH_RE="p${_Q}u${_Q}s${_Q}h|[\$]'|[Aa]${_Q}[Ll]${_Q}[Ii]${_Q}[Aa]${_Q}[Ss]"
# Only rc 1 (no match) skips; a regex error (rc 2) falls through (fail closed).
[[ $COMMAND =~ $_PUSH_RE ]]
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
# `--delete main`, `origin/main`, `heads/main` (git DWIM), `--force-with-lease=main`).
# Bulk/ambiguous pushes (`--all`, `--branches`, `--mirror`, wildcard or `:`
# refspecs, unknown/abbreviated push options) and refspec-less pushes from a
# detached HEAD or in another repository (`-C`, `--git-dir`, `GIT_DIR=`) are
# blocked because the destination cannot be determined safely. A refspec-less
# push (and a ref without destination) is also judged by the config that
# routes it: push.default=matching, branch.<n>.merge, remote.<r>.push, and
# `-c`/GIT_CONFIG* overrides of those on the command line.
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

# R2-3: hard time budget. The classifier is linear (~1.5 s per MB), but a
# hook that runs into the harness timeout is a non-blocking error (= allow):
# past CLASSIFY_BUDGET seconds it is killed, its output is empty -> block.
CLASSIFY_BUDGET=20
_BUDGET=()
command -v timeout >/dev/null 2>&1 && _BUDGET=(timeout -k 2 "$CLASSIFY_BUDGET")
PUSH_CLASS=$(${_BUDGET[@]+"${_BUDGET[@]}"} python3 - "$MAIN_BRANCH" "$CURRENT_BRANCH" 3<<<"$COMMAND" <<'PYEOF' 2>/dev/null
import collections, os, re, shlex, subprocess, sys

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


_refs = None


def ref_exists(ref):
    # One for-each-ref snapshot instead of a git process per ref: 10,000 refs
    # took ~22 s (hook timeout = not a block). Exact names only; anything
    # else (e.g. 'v1^{}') counts as missing, i.e. not tag-only (fail closed).
    global _refs
    if _refs is None:
        out = subprocess.run(["git", "for-each-ref", "--format=%(refname)",
                              "refs/heads", "refs/tags"],
                             capture_output=True, text=True)
        _refs = set(out.stdout.splitlines())
    return ref in _refs


def is_tag_ref(ref):
    ref = ref.lstrip("+")
    if ":" in ref:
        # refspec <src>:<dst> — only the destination decides what is updated
        return ref.split(":", 1)[1].startswith("refs/tags/")
    if ref.startswith("refs/tags/"):
        return True
    return ref_exists(f"refs/tags/{ref}") and not ref_exists(f"refs/heads/{ref}")


def is_git(tok):
    # 'git', '/usr/bin/git' and the dashed form 'git-push'
    # ('/usr/lib/git-core/git-push')
    return os.path.basename(tok) in ("git", "git-push")


# A push recognised in a statement: its args after 'push', whether it runs in
# another repository (-C/--git-dir/--work-tree/GIT_DIR: the cwd repo's HEAD
# and config say nothing about it) and whether push/remote/branch config is
# overridden on the command line (-c, --config-env, GIT_CONFIG*): the
# overriding keys, lower-case.
Push = collections.namedtuple("Push", "args foreign override")
REPO_OPTS = {"-C", "--git-dir", "--work-tree"}
CONFIG_OPTS = {"-c", "--config", "--config-env"}
CONFIG_KEYS = ("push.", "remote.", "branch.", "include")
ENV_FOREIGN = ("GIT_DIR=", "GIT_WORK_TREE=", "GIT_COMMON_DIR=")
ENV_OVERRIDE = ("GIT_CONFIG",)
# overrides that can remap an explicit destination-less ref
MAP_KEYS = ("remote.", "include", "git_config")
# a word the shell expands at run time: $'..', $"..", $VAR, `..`, $(...), {a,b}
# (brace groups found first, then checked: a single regex with a ',' between
# two [^{}]* runs backtracks quadratically on '{,,,,...', R2-3)
BRACE = re.compile(r"\{([^{}]*)\}")


def computed(tok):
    # '{}' is the xargs -I / find -exec placeholder: the real value is unknown
    return "$" in tok or "`" in tok or "{}" in tok or any(
        "," in g or ".." in g for g in BRACE.findall(tok))


# a command string inside one argument ('man -P "git push ..."', 'bash -c ...'):
# 'git' followed (anywhere later) by the word 'push'. Two linear searches
# instead of r"git\b.*\bpush\b" (quadratic on many 'git' words, R2-3).
GIT_WORD = re.compile(r"git\b")
PUSH_WORD = re.compile(r"\bpush\b")


def nested(tok):
    m = GIT_WORD.search(tok)
    return bool(m and PUSH_WORD.search(tok, m.end()))


# R2-1/R2-5: config whose value git runs as a command. Set on the command
# line of a push it can run anything around it -> fail closed.
EXEC_KEYS = ("core.pager", "pager.", "core.sshcommand", "core.editor",
             "sequence.editor", "core.askpass", "core.fsmonitor",
             "core.hookspath", "diff.external", "gpg.", "credential.",
             "uploadpack.", "include")
# Subcommands whose arguments are text (messages, patterns, paths) and never
# a command line; every other subcommand (rebase -x, bisect run, submodule
# foreach, filter-branch, difftool -x, config, fetch --upload-pack, ...) is
# treated as able to run one: a 'git ... push' string in its args blocks.
TEXT_SUBCOMMANDS = {"commit", "tag", "notes", "stash", "merge", "log", "show",
                    "shortlog", "status", "add", "rm", "mv", "branch",
                    "switch", "checkout", "restore", "reset", "describe",
                    "blame", "diff", "rev-parse", "reflog", "revert",
                    "cherry-pick", "format-patch"}
ALIAS_DEPTH = 16


def git_subcommand(toks):
    # toks[0] is git: skip global options (with their values) and return
    # (subcommand or None, args after it, foreign, override, config) where
    # config lists every (key lower-case, value) set by -c/--config-env
    # (value None: taken from the environment, unknown).
    j = 1
    foreign, override, config = False, (), []
    while j < len(toks) and toks[j].startswith("-"):
        opt = toks[j]
        name, _, val = opt.partition("=")
        if opt in GIT_OPTS_WITH_VALUE:
            val = toks[j + 1] if j + 1 < len(toks) else ""
        foreign |= name in REPO_OPTS
        if name in CONFIG_OPTS:
            if val.lower().startswith(CONFIG_KEYS):
                override += (val.lower(),)
            key, _, value = val.partition("=")
            config.append((key.lower(), None if name == "--config-env" else value))
        j += 2 if opt in GIT_OPTS_WITH_VALUE else 1
    if j < len(toks):
        return toks[j], toks[j + 1:], foreign, override, config
    return None, [], foreign, override, config


def runs_push(sub, args):
    # R2-1: a subcommand other than push that runs a command line from its
    # args ('submodule foreach git push ...', 'bisect run git push ...').
    # The unquoted scan (a git word followed by push) applies to every
    # subcommand; the quoted one ('rebase -x "git push ..."') not to text
    # subcommands, so 'git commit -m "... git push ..."' stays a commit.
    g = next((k for k, t in enumerate(args) if is_git(t)), None)
    if g is not None and any(PUSH_WORD.search(t) for t in args[g + 1:]):
        return True  # also 'foreach git -c alias.p=push p'
    if sub in TEXT_SUBCOMMANDS:
        return False
    if "push" in args and any(computed(t) for t in args[:args.index("push")]):
        return True
    return any(nested(t) for t in args)


def git_push(toks, prefix):
    # toks[0] is git or git-push, prefix = the tokens before it (assignments,
    # wrapper words). Push, None (other subcommand) or UNRESOLVED (computed
    # subcommand such as git $'push' / git {push,} / git $(echo push), a
    # command-running subcommand or config that carries a push, an alias
    # that cannot be resolved).
    if os.path.basename(toks[0]) == "git-push":
        sub, args, foreign, override, config = "push", toks[1:], False, (), []
    else:
        sub, args, foreign, override, config = git_subcommand(toks)
    env_config = [t for t in prefix if t.startswith(ENV_OVERRIDE)]
    if any("alias" in t.lower() or "push" in t or nested(t) for t in env_config):
        return UNRESOLVED  # GIT_CONFIG_KEY_0=alias.p GIT_CONFIG_VALUE_0=push ...
    # aliases declared on this command line ('-c alias.p=push p ...') are
    # expanded like git does: the value's words replace the alias word.
    for _ in range(ALIAS_DEPTH):
        if any(value is not None and nested(value) for _, value in config):
            return UNRESOLVED  # -c core.pager='git push ...', -c alias.x='!git push'
        if any(key.startswith("alias.") and value is None for key, value in config):
            return UNRESOLVED  # --config-env=alias.<n>=VAR: value unknown
        aliases = {key[len("alias."):]: value for key, value in config
                   if key.startswith("alias.")}
        if sub is None or sub.lower() not in aliases:
            break
        value = aliases[sub.lower()]
        if value.startswith("!"):
            # a shell alias runs anything; one that mentions push -> block
            return UNRESOLVED if "push" in re.sub(r"[\"'\\$]", "", value) else None
        try:
            words = shlex.split(value)
        except ValueError:
            return UNRESOLVED
        sub, more, f2, o2, c2 = git_subcommand([toks[0]] + words)
        args = more + args
        foreign, override, config = foreign or f2, override + o2, config + c2
    else:
        return UNRESOLVED  # alias loop
    if sub != "push":
        if sub is not None and (computed(sub) or runs_push(sub, args)):
            return UNRESOLVED
        return None
    if any(key.startswith(EXEC_KEYS) for key, _ in config):
        return UNRESOLVED  # git -c core.sshCommand=... push
    foreign |= any(t.startswith(ENV_FOREIGN) for t in prefix)
    override += tuple(t.lower() for t in env_config)
    return Push(args, foreign, override)


def push_args(toks, w):
    # toks[w] is a non-git command word that may execute its arguments
    # (sudo/env/timeout/xargs/unknown). Push, None if this is not a git push,
    # or UNRESOLVED if it mentions git and push but does not resolve to a
    # plain `git [opts] push` (e.g. 'sudo -u git git push', 'sudo $GIT push',
    # a computed command word, 'bash -c "git push ..."') — never dropped.
    if computed(toks[w]):
        return UNRESOLVED
    g = next((k for k in range(w + 1, len(toks)) if is_git(toks[k])), len(toks))
    if g < len(toks):
        res = git_push(toks[g:], toks[:g])
        if res is not None:
            if os.path.basename(toks[w]) == "xargs":
                return UNRESOLVED  # refs arrive on stdin: destination unknown (#950)
            return res
    if "push" in toks[w:]:
        before = toks[w:toks.index("push", w)]
        if g < len(toks) or any(computed(t) for t in before):
            return UNRESOLVED
    if any(nested(t) for t in toks[w + 1:g]):
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
# as a possible wrapper (sudo/env/timeout/xargs/...): fail closed. Pagers and
# man are NOT here (man -P '<cmd>', less with LESSOPEN, ack --pager run
# commands). Known limit: a user-defined `gh` alias with a '!' shell
# expansion (gh alias set --shell) can run a push; gh stays here because
# `gh pr create --body "..."` text must not count as a push. rg runs a
# command only with --pre (checked before this set, like ack --pager).
NON_EXEC = {"echo", "printf", "grep", "egrep", "fgrep", "rg", "ag",
            "gh", "cat", "head", "tail", "wc", "ls"}
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


class _Buf:
    # Token buffer for _Lexer: shlex grows its token with 'self.token +=
    # char' on an attribute, which CPython cannot do in place — one long
    # word cost O(n^2) (1 MB: ~30 s, a hook timeout is not a block, R2-3).
    # Appending to a list keeps shlex's own state machine (no second
    # tokenizer that could disagree with it) at linear cost.
    __slots__ = ("parts", "size")

    def __init__(self, text):
        self.parts, self.size = [text], len(text)

    def __iadd__(self, text):
        self.parts.append(text)
        self.size += len(text)
        return self

    def __bool__(self):
        return self.size > 0

    def __str__(self):
        return "".join(self.parts)

    def __eq__(self, other):
        return str(self) == other

    __hash__ = None


class _Lexer(shlex.shlex):
    # 'token += c' stores the same _Buf back; 'token = c' starts a new one
    token = property(lambda self: self._buf, lambda self, v: setattr(
        self, "_buf", v if isinstance(v, _Buf) else _Buf(v)))

    def read_token(self):
        tok = super().read_token()
        return str(tok) if isinstance(tok, _Buf) else tok


def segments(stmt):
    # Tokenize like the shell (quotes, escapes) and nest at unquoted '(' /
    # ')', so '(git push x)', '$(git push x)' and '<(...)' expose 'git' as a
    # command word and 'x)' does not leak into a ref. A closed group leaves
    # COMPUTED in its parent's place ('git push origin $(...)' has a ref the
    # hook cannot know). Returns a list of token lists.
    lex = _Lexer(stmt, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    lex.commenters = ""
    # kinds: per open group how its value lands in the parent — "" plain
    # subshell, "word" a standalone $(...) word, "attach" glued to the
    # previous token ('x=$(...)', 'refs/heads/$(...)').
    done, stack, kinds = [], [[]], []
    for tok in lex:  # ValueError on unbalanced quotes
        if not set(tok) <= PUNCT:
            stack[-1].append(tok)
            continue
        for ch in tok:
            if ch == "(":
                kind = ""
                if stack[-1] and stack[-1][-1].endswith("$"):
                    stack[-1][-1] = stack[-1][-1][:-1]  # '$(' / 'x=$('
                    kind = "attach"
                    if not stack[-1][-1]:
                        stack[-1].pop()
                        kind = "word"
                stack.append([])
                kinds.append(kind)
            elif ch == ")" and len(stack) > 1:
                done.append(stack.pop())
                kind = kinds.pop()
                if kind == "attach":
                    stack[-1][-1] += COMPUTED
                elif kind or stack[-1]:
                    # a $(...) command word ('$(which git) push') stays visible
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
        return git_push(toks[i:], toks[:i])
    if os.path.basename(word) in ("rg", "ack", "ack-grep") and any(
            t.startswith(("--pre", "--pager")) for t in toks[i + 1:]):
        return UNRESOLVED  # rg --pre / ack --pager run a command per file
    if os.path.basename(word) in NON_EXEC:
        return None
    if os.path.basename(word) == "man":
        # 'man git-push' reads a page; a pager/browser command (-P/--pager,
        # -H/--html, MANPAGER=/PAGER=/MANOPT=) can run anything -> fail closed
        runs = any(t.startswith(("--pager", "--html")) or (
            t.startswith("-") and not t.startswith("--") and ("P" in t or "H" in t))
            for t in toks[i + 1:])
        runs |= any(t.startswith(("MANPAGER=", "PAGER=", "MANOPT=")) for t in toks[:i])
        return UNRESOLVED if runs else None
    return push_args(toks, i)


def remotes():
    global _remotes
    if _remotes is None:
        out = subprocess.run(["git", "remote"], capture_output=True, text=True)
        _remotes = set(out.stdout.split())
    return _remotes


def is_remote_branch(name):
    # '<remote>/<protected>' (remote names may contain '/'); an unknown
    # remote prefix is judged by its first component (fail closed).
    return (name.partition("/")[2] in PROTECTED
            or any(name == f"{r}/{p}" for r in remotes() for p in PROTECTED))


def is_protected(dst):
    # git resolves a destination not starting with 'refs/' via DWIM
    # (refs/%s, refs/tags/%s, refs/heads/%s, refs/remotes/%s): 'heads/main'
    # is refs/heads/main (F1). Tags ('tags/main', 'refs/tags/main') are not
    # branches; remote-tracking spellings are kept protected (fail closed).
    full = dst.startswith("refs/")
    name = dst[len("refs/"):] if full else dst
    if name.startswith("heads/"):
        return name[len("heads/"):] in PROTECTED
    if name.startswith("remotes/"):
        return is_remote_branch(name[len("remotes/"):])
    if full:
        return False
    if name in PROTECTED:
        return True
    first, _, rest = name.partition("/")
    return ((first in remotes() and rest in PROTECTED)
            or any(name == f"{r}/{p}" for r in remotes() for p in PROTECTED))


_cfg = None


def git_config():
    # {key: [values]} of the effective config (one process; keys as printed
    # by git: section/name lower-case, subsection verbatim). Empty on error.
    global _cfg
    if _cfg is None:
        out = subprocess.run(["git", "config", "--list", "-z"],
                             capture_output=True, text=True, errors="surrogateescape")
        _cfg = {}
        for entry in out.stdout.split("\0"):
            key, _, val = entry.partition("\n")
            _cfg.setdefault(key, []).append(val)
    return _cfg


def push_config_block():
    # remote.<r>.push maps destination-less refs and refspec-less pushes
    # (builtin/push.c). Any configured spec that may land on a protected
    # branch (protected/empty dst, wildcard, ':' = matching) -> reason.
    for key, vals in git_config().items():
        if not (key.startswith("remote.") and key.endswith(".push")):
            continue
        for v in vals:
            src, _, dst = v.lstrip("+").partition(":")
            dst = dst or src
            if not dst or "*" in dst or is_protected(dst):
                return f"{key}={v} may push to a protected branch"
    return None


def refspec_less_block():
    # A3: where a refspec-less push from a non-protected branch goes is
    # decided by config. Only a RESOLVED protected target blocks; an unset
    # upstream is the normal case and never blocks.
    reason = push_config_block()
    if reason:
        return reason
    if [v.lower() for v in git_config().get("push.default", ["simple"])][-1] == "matching":
        return "push.default=matching pushes every matching branch"
    for merge in git_config().get(f"branch.{CURRENT}.merge", []):
        if is_protected(merge):
            return f"upstream of '{CURRENT}' is protected (branch.{CURRENT}.merge={merge})"
    return None


def has_submodules():
    # True when the cwd repository declares submodules (.gitmodules in its
    # top level); unknown top level -> assume yes (fail closed).
    try:
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return True
    return not top or os.path.exists(os.path.join(top, ".gitmodules"))


def destination_block(p):
    # Reason string if this (non-tag-only) push statement may update a
    # protected branch or its destination cannot be determined; else None.
    args = p.args
    current = "" if p.foreign else CURRENT
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
            if name == "--recurse-submodules" and val in ("on-demand", "only") \
                    and (p.foreign or has_submodules()):
                return (f"'{a}' also pushes submodule commits to the submodules' own "
                        "remotes and branches, destination cannot be determined")
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
    where = "in another repository (-C/--git-dir/--work-tree/GIT_DIR)" if p.foreign \
        else "on a detached HEAD (or outside a repo)"
    refs = pos[1:]  # pos[0] is the remote
    if not refs:
        if not current:
            return f"no explicit refspec {where}, destination cannot be determined"
        if p.override:
            return "push/remote/branch config overridden on the command line, destination cannot be determined"
        # pushes the current branch (checked by the caller) or what config says
        return refspec_less_block()
    k = 0
    while k < len(refs):
        ref = refs[k]
        k += 1
        if ref == "tag":
            k += 1  # 'tag <name>' only touches refs/tags/
            continue
        spec = ref.lstrip("+")
        # incl. COMPUTED, brace expansion and glob characters ('ma?n' matches
        # a file named main): the shell decides the real refspec
        if computed(spec) or "?" in spec or "[" in spec:
            return (f"refspec '{ref}' is computed at run time, destination cannot be "
                    "determined (use a literal branch name or HEAD instead)")
        if "*" in spec or spec == ":":
            return f"refspec '{ref}' pushes many refs, destination cannot be determined"
        src, colon, dst = spec.partition(":")
        if not colon or not dst:
            dst = src
            # a destination-less ref is mapped through remote.<r>.push
            if any(key.startswith(MAP_KEYS) for key in p.override):
                return f"refspec '{ref}' without destination while push config is overridden on the command line"
            reason = push_config_block()
            if reason:
                return f"refspec '{ref}' without destination: {reason}"
        if dst in ("HEAD", "@"):
            if not current:
                return f"refspec '{ref}' {where}, destination cannot be determined"
            dst = current
        if is_protected(dst):
            return f"destination '{dst}' of refspec '{ref}' is a protected branch"
    return None


def quoted_statements(cmd):
    # Split on control operators OUTSIDE quotes (bash quoting: '...' takes
    # everything literally, backslash escapes elsewhere). Linear scan.
    out, start, q = [], 0, ""
    for m in re.finditer(r"\\.|[\"';|&\n]", cmd, re.S):
        t = m.group()
        if q == "'":
            if t[-1] == "'":
                q = ""
        elif t[0] == "\\":
            continue
        elif q == '"':
            if t == '"':
                q = ""
        elif t in "'\"":
            q = t
        else:
            out.append(cmd[start:m.start()])
            start = m.end()
    out.append(cmd[start:])
    return out


CHDIR = re.compile(r"(?:^|[\s;&|(])(?:cd|pushd|popd)(?!\S*[\w-])(?:\s+(?!\.(?:/)?(?:\s|$|;|&|\|))|\s*$|\s*[;&|)])")

# --- comment + heredoc preprocessing (#947, #948) ---------------------------
def strip_comment(stmt):
    # Cut an unquoted, word-start '#' comment (bash: '#' only starts a comment
    # at the beginning of a word; 'a#b', '"#x"', '${#x}' and '$#' stay text).
    # Only whitespace/start counts as word start: anything unusual keeps the
    # text, which can only add blocks, never hide a push.
    q, i, n = "", 0, len(stmt)
    while i < n:
        c = stmt[i]
        if q == "'":
            if c == "'":
                q = ""
        elif c == "\\":
            i += 1
        elif q == '"':
            if c == '"':
                q = ""
        elif c in "'\"":
            q = c
        elif c == "#" and (i == 0 or stmt[i - 1] in " \t"):
            return stmt[:i]
        i += 1
    return stmt


HEREDOC = re.compile(r"(?<!<)<<(-?)[ \t]*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
HEREDOC_OWNERS = {"cat", "gh", "tee"}
HEREDOC_OUTER = {"echo", "printf", "gh", "cat", "tee"}
HEREDOC_GIT_TEXT = {"commit", "tag", "notes"}


def _command_words(text):
    words = re.findall(r"[^\s|&;()<>]+", text)
    while words and (words[0] in RESERVED or ASSIGNMENT.match(words[0])):
        words.pop(0)
    return words


def _text_command(words):
    # does this command only treat stdin / its arguments as text?
    if not words:
        return False
    first = os.path.basename(words[0])
    if first == "git":
        rest = [w for w in words[1:] if not w.startswith("-")]
        if "-C" in words:  # -C <path>: the path is not the subcommand
            rest = [w for w in rest if w != words[words.index("-C") + 1]]
        return bool(rest) and rest[0] in HEREDOC_GIT_TEXT
    return first in HEREDOC_OUTER


def _heredoc_operator(line):
    # The first '<<WORD' in command position (outside quotes; a double-quoted
    # '$(' re-enters command position), or None.
    stack = [""]
    i, n = 0, len(line)
    while i < n:
        c, top = line[i], stack[-1]
        if top == "'":
            if c == "'":
                stack.pop()
        elif c == "\\":
            i += 1
        elif c == "$" and line[i + 1:i + 2] == "(" and top in ("", '"'):
            stack.append("")
            i += 1
        elif top == "" and c == ")" and len(stack) > 1:
            stack.pop()
        elif top == '"':
            if c == '"':
                stack.pop()
        elif c in "'\"":
            stack.append(c)
        elif top == "" and c == "<":
            m = HEREDOC.match(line, i)
            if m:
                return m
        i += 1
    return None


def strip_heredoc_bodies(cmd):
    # Drop the body of a heredoc whose consumer only handles text: `cat`
    # (usually inside "$(...)" for gh --body / git commit -m), gh, tee, or a
    # text-only outer command. A body fed to a shell, interpreter, eval, xargs,
    # a pipe or anything unknown is KEPT, since it may be executed. An
    # unterminated heredoc keeps everything (fail closed).
    lines = cmd.split("\n")
    out, i = [], 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        i += 1
        m = _heredoc_operator(line)
        if not m or re.search(r"[|;&`]", line):
            continue
        pre = line[:m.start()]
        owner_seg = pre[pre.rfind("$(") + 2:] if "$(" in pre else pre
        owner = _command_words(owner_seg)
        owner_ok = bool(owner) and (
            os.path.basename(owner[0]) in HEREDOC_OWNERS or _text_command(owner))
        if not (owner_ok and _text_command(_command_words(pre))):
            continue
        delim, dash = m.group(3), bool(m.group(1))
        j = i
        while j < len(lines) and (lines[j].lstrip("\t") if dash else lines[j]) != delim:
            j += 1
        if j < len(lines):
            i = j  # skip the body; the terminator line is kept
    return "\n".join(out)


def classify(cmd):
    # bash drops backslash-newline before parsing: join continued lines first
    cmd = REDIRECT.sub(" ", strip_heredoc_bodies(cmd.replace("\\\n", "")))
    pushes = []
    # Fragments split on EVERY control operator (a quote may hide a push: a
    # multi-line quoted 'bash -c' body stays visible line by line) PLUS the
    # quote-aware statements: a quoted ';', '|', '&' or newline must not cut
    # off the refspec ('git push -o "a;b" origin HEAD:main', QF1). Both views
    # are classified; any block wins.
    stmts = list(dict.fromkeys(
        strip_comment(s).strip()
        for s in re.split(r"&&|\|\||;|\||&|\n", cmd) + quoted_statements(cmd)))
    parsed = {}  # stmt -> parses as-is (each statement is tokenized once)
    for stmt in stmts:
        plain = re.sub(r"[\"'\\$]", "", stmt)
        # 'alias': '-c alias.p=push p', '--config-env=alias.p=VAR p' (R2-5)
        if "push" not in plain and "$'" not in stmt and "alias" not in plain.lower():
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
        parsed[stmt] = segs is not None and not suffix
        if segs is None:
            if "git" in plain:
                return "block unparseable statement mentions git push"
            continue
        for toks in segs:
            args = segment_push_args(toks)
            if args is UNRESOLVED:
                return "block unresolvable git push statement"
            if args is None:
                continue
            # The push only parsed after a quote was closed artificially: the
            # rest of it (refspec) sits behind a quoted separator — fail closed.
            if suffix:
                return "block git push statement with a quote spanning a command separator"
            # ANSI-C quoting can hide separators/escapes ($'a\';b') that the
            # tokenizer reads differently from bash — fail closed.
            if "$'" in stmt:
                return "block git push statement with ANSI-C quoting ($'...')"
            pushes.append(args)
    if not pushes:
        return "none"
    # A cd/pushd/popd anywhere in the command may move the push into another
    # repository whose HEAD and config the hook cannot see (#952): judge it
    # like -C. 'cd .' is a no-op and does not count.
    if CHDIR.search(cmd):
        pushes = [p._replace(foreign=True) for p in pushes]
    non_tag = [p for p in pushes
               if p.foreign or p.override or not stmt_is_tag_only(p.args)]
    # B-01: any unparseable statement (a quote may hide a push) -> not tag-only;
    # A3: a remote.<r>.push mapping may land a tag ref on a branch
    if not non_tag and all(parsed[s] if s in parsed else segments_ok(s) for s in stmts) \
            and not push_config_block():
        return "tag"
    for p in pushes if push_config_block() else non_tag:
        reason = destination_block(p)
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
_CLASS_RC=$?

case "$PUSH_CLASS" in
  none) exit 0 ;;
  tag) IS_TAG_ONLY_PUSH=true ;;
  push) IS_TAG_ONLY_PUSH=false ;;
  *)
    _REASON="${PUSH_CLASS#block }"
    [ "${PUSH_CLASS%% *}" = "block" ] || _REASON="push classification failed (fail closed)"
    [ "$_CLASS_RC" -eq 124 ] && _REASON="push classification exceeded ${CLASSIFY_BUDGET}s (fail closed)"
    echo "Branch-Guard: Push blocked — $_REASON." >&2
    # #1033: PROTECTED is main + master + the configured main branch (see the
    # classifier above) — list that set de-duplicated instead of repeating it.
    _PROTECTED_BRANCHES="main, master"
    if [ "$MAIN_BRANCH" != "main" ] && [ "$MAIN_BRANCH" != "master" ]; then
      _PROTECTED_BRANCHES="$MAIN_BRANCH, $_PROTECTED_BRANCHES"
    fi
    echo "Protected branches: $_PROTECTED_BRANCHES. Push a feature branch and open a PR instead." >&2
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
