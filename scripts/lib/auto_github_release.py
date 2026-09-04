"""Decision logic for the auto-github-release PostToolUse hook (issues #518/#622).

The shell wrapper hooks/1-generic/auto-github-release.sh pipes the Claude-Code
PostToolUse JSON payload to this module after a Bash tool call. If that command
was a `git push <remote> <tag>` whose tag matches the project's configured
`versioning.tag_format`, AND the project opted in via
`conventions.release.github_release.enabled: true`, the hook creates the
matching GitHub release with `gh release create` — unless one already exists
for that tag (idempotent no-op).

This is a pure automation side-effect after an already-completed push, never a
gate: main() always exits 0, and every unexpected condition (missing config,
broken conventions, gh failure) fails open (no release, no error surfaced to
the tool call). All the parsing/decision helpers here are side-effect-free and
unit-tested directly; only main() shells out to `gh`.
"""
from __future__ import annotations

import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

# Version segment placeholder in a tag_format (e.g. {major}, {year}). Real tags
# may append a pre-release/build tail (-beta.1, -rc.2, +build.5) that the
# tag_format core does not spell out, so the compiled matcher allows it.
_PRERELEASE_TAIL = r"(?:[-+][0-9A-Za-z.]+)?"
_SEGMENT = r"[0-9A-Za-z]+"


def tag_format_to_regex(tag_format: str) -> re.Pattern:
    """Compile a conventions tag_format into an anchored tag matcher.

    Literal characters are escaped; each ``{placeholder}`` becomes one version
    segment; an optional pre-release/build tail is always permitted so
    `v{major}.{minor}.{patch}` matches both `v1.2.3` and `v1.2.3-beta.1`.
    """
    parts = re.split(r"\{[^}]*\}", tag_format)
    regex = _SEGMENT.join(re.escape(p) for p in parts)
    return re.compile(rf"^{regex}{_PRERELEASE_TAIL}$")


def tag_format_prefix(tag_format: str) -> str:
    """Literal characters before the first ``{`` placeholder (e.g. 'v' or '')."""
    idx = tag_format.find("{")
    return tag_format if idx == -1 else tag_format[:idx]


def tag_version(tag: str, prefix: str) -> str:
    """Tag with its format prefix stripped ('v1.2.3' + 'v' -> '1.2.3')."""
    if prefix and tag.startswith(prefix):
        return tag[len(prefix):]
    return tag


def is_prerelease(tag: str, suffixes: list[str]) -> bool:
    """True if the tag carries a pre-release identifier from ``suffixes``.

    Matches a `-<suffix>` segment (case-insensitive), e.g. tag 'v1.2.3-beta.1'
    with suffixes ['alpha','beta','rc'] -> True; 'v1.2.3' -> False.
    """
    for s in suffixes:
        if s and re.search(rf"-{re.escape(s)}\b", tag, re.IGNORECASE):
            return True
    return False


def extract_push_refs(command: str) -> list[str]:
    """Return candidate ref tokens from every `git push` statement in a command.

    Reuses the orchestrator-guard tokenizer style (split on shell control
    operators, shlex each statement). For each `git push`, collects positional
    args after the remote and normalises them to bare tag names: strips a
    leading '+' (force refspec), a 'refs/tags/' prefix, and a 'src:dst' colon
    form (keeping the destination ref's tag name). `git push --tags` pushes all
    tags with no single named tag, so it yields nothing here (see hook docs).
    """
    refs: list[str] = []
    for stmt in re.split(r"&&|\|\||;|\||\n", command):
        try:
            toks = shlex.split(stmt)
        except ValueError:
            toks = stmt.split()
        if not toks:
            continue
        # The statement's leading token must itself be `git` — a fire-action
        # automation must not treat `git` appearing as an argument to another
        # command (e.g. `echo git push ...`) as a real push. A leading `sudo`/
        # env-prefix simply yields no auto-release (safe false-negative).
        if toks[0] != "git" and not toks[0].endswith("/git"):
            continue
        rest = toks[1:]
        j = 0  # skip global options before the subcommand
        while j < len(rest) and rest[j].startswith("-"):
            j += 1
        if j >= len(rest) or rest[j] != "push":
            continue
        positionals = [a for a in rest[j + 1:] if not a.startswith("-")]
        # first positional is the remote; the rest are refspecs
        for ref in positionals[1:]:
            refs.append(_normalise_ref(ref))
    return [r for r in refs if r]


def _normalise_ref(ref: str) -> str:
    ref = ref.lstrip("+")
    if ":" in ref:  # src:dst refspec -> take the destination
        ref = ref.split(":", 1)[1]
    if ref.startswith("refs/tags/"):
        ref = ref[len("refs/tags/"):]
    return ref


def resolve_release_spec(config: dict, agent_meta_root: Path) -> dict:
    """Effective 'release' conventions domain (preset + project overrides).

    Fails open to {} on any resolution error (broken conventions config must
    never make this automation raise — the caller just does nothing).
    """
    try:
        from .conventions import resolve_conventions
        resolved = resolve_conventions(config, agent_meta_root)
        spec = resolved.get("release")
        return spec if isinstance(spec, dict) else {}
    except Exception:
        return {}


def decide(command: str, release_spec: dict) -> dict | None:
    """Decide whether/what GitHub release to create for a push command.

    Returns {tag, title, prerelease} for the first matching, opted-in tag, or
    None when the feature is disabled, the command is not a matching tag push,
    or no configured tag_format is present.
    """
    gh = release_spec.get("github_release") or {}
    if not gh.get("enabled", False):
        return None
    tag_format = (release_spec.get("versioning") or {}).get("tag_format")
    if not tag_format:
        return None

    matcher = tag_format_to_regex(tag_format)
    prefix = tag_format_prefix(tag_format)
    suffixes = gh.get("pre_release_suffixes") or []
    title_pattern = gh.get("title_pattern", "{tag}")

    for tag in extract_push_refs(command):
        if not matcher.match(tag):
            continue
        version = tag_version(tag, prefix)
        title = title_pattern.replace("{tag}", tag).replace("{version}", version)
        return {"tag": tag, "title": title, "prerelease": is_prerelease(tag, suffixes)}
    return None


def extract_changelog_notes(changelog_text: str, version: str) -> str | None:
    """Extract the CHANGELOG section body for ``version``, or None if absent.

    Matches a keep-a-changelog/angular header line that references the version
    (e.g. '## [1.2.3] — 2026-09-04' or '## [1.2.3] (2026-09-04)') and returns
    everything up to the next '## ' header, trimmed.
    """
    lines = changelog_text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("## ") and re.search(rf"\[?{re.escape(version)}\]?", line):
            start = i + 1
            break
    if start is None:
        return None
    body: list[str] = []
    for line in lines[start:]:
        if line.startswith("## "):
            break
        body.append(line)
    text = "\n".join(body).strip()
    return text or None


def _release_exists(tag: str, cwd: str) -> bool:
    try:
        r = subprocess.run(
            ["gh", "release", "view", tag],
            cwd=cwd, capture_output=True, text=True,
        )
        return r.returncode == 0
    except FileNotFoundError:
        # gh not installed -> cannot verify, treat as "exists" to stay safe
        # (never risk a duplicate/partial create when we cannot check).
        return True


def _load_config(project_root: Path) -> dict:
    cfg_path = project_root / ".meta-config" / "project.yaml"
    if not cfg_path.exists():
        return {}
    try:
        from .io import _load_yaml_or_json
        data, _ = _load_yaml_or_json(cfg_path)
        return data or {}
    except Exception:
        return {}


def _notes_for(project_root: Path, tag: str, version: str) -> str:
    changelog = project_root / "CHANGELOG.md"
    if changelog.exists():
        try:
            notes = extract_changelog_notes(changelog.read_text(encoding="utf-8"), version)
            if notes:
                return notes
        except Exception:
            pass
    return f"Release {tag}"


def main() -> int:
    """Read a PostToolUse payload from stdin, create a GitHub release if due.

    Always returns 0 — PostToolUse hooks must never block the (already
    completed) tool call, and this is pure automation.
    """
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0

    if payload.get("tool_name") != "Bash":
        return 0
    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        return 0

    project_root = Path(
        os.environ.get("AGR_PROJECT_ROOT") or payload.get("cwd") or os.getcwd()
    )
    agent_meta_root = Path(
        os.environ.get("AGR_AGENT_META_ROOT") or (project_root / ".agent-meta")
    )
    if not (agent_meta_root / "config" / "conventions-presets.yaml").exists():
        # agent-meta sources not locatable -> cannot resolve conventions.
        return 0

    config = _load_config(project_root)
    release_spec = resolve_release_spec(config, agent_meta_root)
    decision = decide(command, release_spec)
    if not decision:
        return 0

    tag = decision["tag"]
    if _release_exists(tag, str(project_root)):
        print(f"auto-github-release: GitHub release for {tag} already exists — skipping.",
              file=sys.stderr)
        return 0

    prefix = tag_format_prefix((release_spec.get("versioning") or {}).get("tag_format", ""))
    version = tag_version(tag, prefix)
    argv = [
        "gh", "release", "create", tag,
        "--title", decision["title"],
        "--notes", _notes_for(project_root, tag, version),
    ]
    if decision["prerelease"]:
        argv.append("--prerelease")

    try:
        r = subprocess.run(argv, cwd=str(project_root), capture_output=True, text=True)
        if r.returncode == 0:
            print(f"auto-github-release: created GitHub release {tag}.", file=sys.stderr)
        else:
            print(f"auto-github-release: `gh release create {tag}` failed "
                  f"(exit {r.returncode}): {r.stderr.strip()}", file=sys.stderr)
    except FileNotFoundError:
        print("auto-github-release: `gh` CLI not found on PATH — skipping.", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
