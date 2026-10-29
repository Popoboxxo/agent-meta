"""Hook regression tests for hooks/1-generic/repo-containment.sh.

Repo-Containment ("prison mode", spec
``docs/concepts/repo-containment-prison-mode.md`` §7) confines agent WRITE
access to the project root, with an optional ``.tmp`` scratch sink as the only
sanctioned exception. The enforcement lives in a bash hook outside the Python
test suite, so these tests invoke it as a real subprocess with synthetic
PreToolUse JSON payloads and assert on the exit code (0 = allow, 2 = block),
mirroring ``tests/test_orchestrator_guard_hook.py``.

Payload shape follows ``hooks/1-generic/lib/hook_common.sh``: the hook reads
``tool_name``, ``tool_input.file_path`` / ``tool_input.command`` and ``cwd``.
The repo root is the nearest ancestor of ``cwd`` containing ``.meta-config/``,
so each test builds a ``tmp_path`` project root with a
``.meta-config/project.yaml``.

Run: python -m pytest tests/test_repo_containment_hook.py -v
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment.sh"
_IMPL_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment-impl.sh"

sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.tmp_paths import resolve_tmp_paths  # noqa: E402

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _write_config(root: Path, block: str) -> Path:
    """Materialize ``<root>/.meta-config/project.yaml`` with *block*."""
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    config_path = meta / "project.yaml"
    config_path.write_text(block, encoding="utf-8")
    return config_path


def _project(tmp_path: Path, block: str | None = None) -> Path:
    """Create a project root with (optionally) a repo_containment block."""
    root = tmp_path / "project"
    root.mkdir(parents=True)
    _write_config(
        root,
        block
        if block is not None
        else (
            'repo_containment:\n'
            '  enabled: true\n'
            '  tmp-sink:\n'
            '    enabled: true\n'
            '    path: ".tmp"\n'
        ),
    )
    return root


def _config_at(path: Path, block: str | None = None) -> Path:
    """Create ``.meta-config/project.yaml`` directly in *path* (which becomes
    the project root itself, unlike ``_project`` which appends ``project/``)."""
    (path / ".meta-config").mkdir(parents=True, exist_ok=True)
    (path / ".meta-config" / "project.yaml").write_text(
        block
        if block is not None
        else (
            'repo_containment:\n'
            '  enabled: true\n'
            '  tmp-sink:\n'
            '    enabled: true\n'
            '    path: ".tmp"\n'
        ),
        encoding="utf-8",
    )
    return path


def _run_hook(
    payload: dict | str, process_cwd: Path | str | None = None
) -> subprocess.CompletedProcess:
    """Run the hook as a subprocess.

    ``process_cwd`` is the guard process' own working directory (the thing the
    hook must never adopt as a repo root). It defaults to the agent-meta repo
    root, which *does* carry ``.meta-config/`` — so any test that still passes
    with that default proves the verdict came from the payload, never ``$PWD``.
    """
    raw = payload if isinstance(payload, str) else json.dumps(payload)
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=raw,
        capture_output=True,
        text=True,
        cwd=str(process_cwd if process_cwd is not None else _REPO_ROOT),
        env=_clean_env(),
    )


def _write_payload(
    path: Path | str, cwd: Path | str | None = None, tool: str = "Write"
) -> dict:
    """Build a PreToolUse payload for a Write/Edit target.

    ``cwd=None`` omits the ``cwd`` key entirely (the AC-04 payload shape);
    ``cwd=""`` sends the key with an empty value (the AC-28/29/37 shape).
    """
    payload: dict = {"tool_name": tool, "tool_input": {"file_path": str(path)}}
    if cwd is not None:
        payload["cwd"] = str(cwd)
    return payload


def _bash_payload(command: str, cwd: Path) -> dict:
    return {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(cwd),
    }


def _external_fixture() -> Path:
    """Create a directory outside every project root (AC-03/AC-05/AC-07).

    ``tmp_path`` is unsuitable here: its location depends on the configured
    pytest basetemp, which may itself sit inside a project root. The spec
    therefore requires ``tempfile.mkdtemp(dir=tempfile.gettempdir())`` plus an
    assertion that no ancestor carries ``.meta-config/``.
    """
    fixture = Path(tempfile.mkdtemp(dir=tempfile.gettempdir(), prefix="am-hook-ext-"))
    for ancestor in (fixture, *fixture.parents):
        assert not (ancestor / ".meta-config").is_dir(), (
            f"external fixture {fixture} is not isolated: {ancestor} has .meta-config/"
        )
    return fixture


@pytest.fixture()
def external_fixture():
    fixture = _external_fixture()
    try:
        yield fixture
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


# --- Write/Edit: path containment --------------------------------------


def test_write_inside_root_is_allowed(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_write_payload(root / "pkg" / "module.py", root))
    assert result.returncode == 0, result.stderr


def test_write_outside_root_is_blocked(tmp_path):
    root = _project(tmp_path)
    outside = root.parent / "outside.py"
    result = _run_hook(_write_payload(outside, root))
    assert result.returncode == 2
    assert "outside the repository root" in result.stderr


def test_write_into_tmp_sink_with_active_sink_is_allowed(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_write_payload(root / ".tmp" / "scratch.txt", root))
    assert result.returncode == 0, result.stderr


def test_write_into_tmp_sink_without_sink_is_blocked(tmp_path):
    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: false\n'
        '    path: ".tmp"\n',
    )
    result = _run_hook(_write_payload(root / ".tmp" / "scratch.txt", root))
    assert result.returncode == 2
    assert "DISABLED tmp-sink" in result.stderr


def test_edit_missing_file_path_fails_closed(tmp_path):
    root = _project(tmp_path)
    payload = {"tool_name": "Edit", "tool_input": {}, "cwd": str(root)}
    result = _run_hook(payload)
    assert result.returncode == 2
    assert "no tool_input.file_path" in result.stderr


def test_read_tool_is_not_intercepted(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_write_payload(Path("/etc/passwd"), root, tool="Read"))
    assert result.returncode == 0, result.stderr


# --- enabled: false is a global opt-out --------------------------------


def test_disabled_mode_allows_even_an_outside_write(tmp_path):
    root = _project(tmp_path, "repo_containment:\n  enabled: false\n")
    result = _run_hook(_write_payload(root.parent / "outside.py", root))
    assert result.returncode == 0, result.stderr


def test_opt_out_does_not_unlock_a_foreign_cwd(tmp_path, external_fixture):
    """AC-08: `enabled: false` stays project-local (root resolution comes first).

    The same foreign project with the opt-out allows a write *inside itself*
    (exit 0) but cannot unlock a write from a `cwd` that resolves to no project
    at all (exit 2, ``repo-containment.no-root``).
    """
    foreign = _project(tmp_path, "repo_containment:\n  enabled: false\n")

    inside = _run_hook(_write_payload(foreign / "note.md", foreign))
    assert inside.returncode == 0, inside.stderr

    outside = _run_hook(_write_payload(external_fixture / "x.py", external_fixture))
    assert outside.returncode == 2, outside.stderr
    assert "repo-containment.no-root" in outside.stderr


# --- Bash: best-effort write detection ---------------------------------


def test_bash_write_pattern_outside_root_is_blocked(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(
        _bash_payload(f"touch {root.parent}/evil.txt", root)
    )
    assert result.returncode == 2
    assert "outside the repository root" in result.stderr


def test_bash_redirection_outside_root_is_blocked(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(
        _bash_payload(f"echo pwned > {root.parent}/evil.txt", root)
    )
    assert result.returncode == 2


def test_bash_write_inside_root_is_allowed(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_bash_payload("touch scratch.txt", root))
    assert result.returncode == 0, result.stderr


def test_bash_read_only_command_is_allowed(tmp_path):
    root = _project(tmp_path)
    result = _run_hook(_bash_payload("ls -la", root))
    assert result.returncode == 0, result.stderr


# --- Symlink escape (realpath check) -----------------------------------


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_symlink_escape_is_blocked(tmp_path):
    root = _project(tmp_path)
    os.symlink(root.parent, root / "escape")
    result = _run_hook(_write_payload(root / "escape" / "outside.py", root))
    assert result.returncode == 2


# --- Safe-side: empty / broken payloads never open the jail ------------


def test_empty_payload_fails_closed():
    result = _run_hook("")
    assert result.returncode == 2


def test_broken_json_payload_fails_closed():
    result = _run_hook("{not valid json")
    assert result.returncode == 2


def test_missing_config_fails_closed(external_fixture):
    """AC-03: without any `.meta-config/` ancestor the hook fails closed.

    The fixture has no ``.meta-config/`` ancestor (asserted by
    ``_external_fixture``) and the target lies *inside* the fixture, so the
    verdict can only come from the missing project root — not from a target
    outside some promoted directory.

    Deliberate inversion (Task 9, spec §"Bewusste Test-Änderung"): the old
    ``test_missing_config_defaults_to_containment_on`` asserted exit 2 for a
    target *outside* a promoted fixture root, i.e. the fail-open case
    (``cwd=/tmp``, target ``/tmp/x``) was never covered — it returned 0.

        # bewusst invertiert (Fail-open-Fall cwd=/tmp, Ziel /tmp/x)
        # root = tmp_path / "bare"
        # result = _run_hook(_write_payload(root.parent / "outside.py", root))
        # assert result.returncode == 2      # passed only via the escaped target

    The reversed test below keeps the old expectation (exit 2) but names the
    code and points the target inside the fixture, which fails on the
    pre-Task-8 hook (exit 0).
    """
    result = _run_hook(_write_payload(external_fixture / "notes.md", external_fixture))
    assert result.returncode == 2, result.stderr
    assert "repo-containment.no-root" in result.stderr
    anchor = os.path.realpath(external_fixture)
    assert f"no project root found above {anchor}" in result.stderr


def test_relative_target_without_cwd_fails_closed(external_fixture):
    """AC-04: a relative target and no `cwd` cannot be anchored -> exit 2.

    ``$PWD`` must not stand in for the payload field: the same payload is run
    once with the (project carrying) agent-meta repo as process cwd and once
    from the isolated external fixture. Both stay blocked, so the guard never
    resolves a relative target against its own working directory.
    """
    payload = _write_payload("notes.md")  # no `cwd` key at all
    assert "cwd" not in payload

    from_outside = _run_hook(payload, process_cwd=external_fixture)
    assert from_outside.returncode == 2, from_outside.stderr
    assert "repo-containment.no-root" in from_outside.stderr
    assert "relative target without `cwd`" in from_outside.stderr
    assert "target:    notes.md" in from_outside.stderr

    from_project_pwd = _run_hook(payload)  # process cwd = _REPO_ROOT
    assert from_project_pwd.returncode == 2, from_project_pwd.stderr
    assert "relative target without `cwd`" in from_project_pwd.stderr


# --- Fail-closed anchor rule (Task 8) ----------------------------------


def test_cwd_outside_project_cannot_be_adopted(external_fixture):
    """AC-05: a `cwd` outside any project must never be promoted to a root.

    The regression the hook carried until Task 8: with ``cwd=/tmp`` and target
    ``/tmp/x.py`` it adopted ``$PWD``/``cwd`` as the repo root and allowed the
    write (exit 0) because the target was "inside" that fake root.
    """
    target = external_fixture / "x.py"
    result = _run_hook(_write_payload(target, external_fixture))
    assert result.returncode == 2, result.stderr
    assert "repo-containment.no-root" in result.stderr
    anchor = os.path.realpath(external_fixture)
    assert f"no project root found above {anchor}" in result.stderr
    assert f"anchor:    {anchor}" in result.stderr


def test_relative_target_is_judged_at_its_real_location(tmp_path):
    """AC-33: a relative target is resolved against `cwd`, not the repo root."""
    root = _project(tmp_path)
    deep = root / "a" / "b"
    deep.mkdir(parents=True)

    inside = _run_hook(_write_payload(Path("../../x"), deep))
    assert inside.returncode == 0, inside.stderr

    outside = _run_hook(_write_payload(Path("../../../../etc/passwd"), deep))
    assert outside.returncode == 2, outside.stderr
    assert "outside the repository root" in outside.stderr


def test_relative_target_resolves_against_cwd(tmp_path):
    """AC-06: relative targets are judged where the tool would write them.

    ``cwd=<root>/.tmp/sub`` plus ``file_path="notes.md"`` is evaluated as
    ``<root>/.tmp/sub/notes.md`` (inside the enabled sink) -> exit 0. From the
    same `cwd` a relative target climbing out of the project is blocked, which
    only holds when the base really is the workdir and not the repo root.
    """
    root = _project(tmp_path)
    workdir = root / ".tmp" / "sub"
    workdir.mkdir(parents=True)

    inside = _run_hook(_write_payload("notes.md", workdir))
    assert inside.returncode == 0, inside.stderr

    climbing = _run_hook(_write_payload("../../../../etc/passwd", workdir))
    assert climbing.returncode == 2, climbing.stderr
    assert "outside the repository root" in climbing.stderr


@pytest.mark.skipif(os.name == "nt", reason="symlink semantics differ on Windows")
def test_symlinked_cwd_uses_realpath(external_fixture):
    """AC-07: a symlinked `cwd` is realpath-resolved before the root search.

    A link pointing outside every project must exit 2 with the *resolved* path
    named in stderr (the link must never become an anchor on its own). The
    control case — a link into a project — must allow, which only works when
    the realpath is searched rather than the link's own ancestors.
    """
    real_outside = external_fixture / "real-outside"
    real_outside.mkdir()
    link_outside = external_fixture / "link-outside"
    os.symlink(real_outside, link_outside)
    resolved_outside = os.path.realpath(real_outside)

    blocked = _run_hook(_write_payload(real_outside / "x.py", link_outside))
    assert blocked.returncode == 2, blocked.stderr
    assert "repo-containment.no-root" in blocked.stderr
    assert f"no project root found above {resolved_outside}" in blocked.stderr
    assert (
        f"resolved:  payload `cwd` {link_outside} -> {resolved_outside}"
        in blocked.stderr
    )

    project = external_fixture / "project"
    project.mkdir()
    _write_config(project, "repo_containment:\n  enabled: true\n")
    link_inside = external_fixture / "link-inside"
    os.symlink(project, link_inside)

    allowed = _run_hook(_write_payload(project / "notes.md", link_inside))
    assert allowed.returncode == 0, allowed.stderr


def test_empty_cwd_anchors_on_absolute_target(tmp_path):
    """AC-28: `cwd=""` anchors on the target's directory, never on `$PWD`.

    The fixture lives outside the agent-meta repo, so an implementation falling
    back to the guard process' working directory (the repo root) would call the
    target "outside" and exit 2. Exit 0 is only reachable through the
    target-derived anchor.
    """
    root = _project(tmp_path)
    result = _run_hook(_write_payload(root / "notes.md", ""))
    assert result.returncode == 0, result.stderr


def test_empty_cwd_does_not_allow_system_temp(external_fixture):
    """AC-29: `cwd=""` plus a system-temp target still fails closed."""
    result = _run_hook(_write_payload(external_fixture / "x.py", ""))
    assert result.returncode == 2, result.stderr
    assert "repo-containment.no-root" in result.stderr
    anchor = os.path.realpath(external_fixture)
    assert f"no project root found above {anchor}" in result.stderr
    assert "the target's own directory when `cwd` is missing" in result.stderr


def test_empty_cwd_uses_project_of_absolute_target(external_fixture):
    """AC-37: documented assumption (ADR-08) — the target's own project wins.

    With ``cwd=""`` an absolute target inside a *foreign* tree that carries
    ``.meta-config/`` becomes the root and the write is allowed. This pins the
    residual trust assumption (a foreign project is trusted exactly like a
    `cwd`) so it cannot change unnoticed; it is deliberately not a security
    claim. A sibling without ``.meta-config/`` stays blocked.
    """
    foreign = external_fixture / "foreign"
    foreign.mkdir()
    _write_config(foreign, "repo_containment:\n  enabled: true\n")

    allowed = _run_hook(_write_payload(foreign / "notes.md", ""))
    assert allowed.returncode == 0, allowed.stderr

    blocked = _run_hook(_write_payload(external_fixture / "other.py", ""))
    assert blocked.returncode == 2, blocked.stderr
    assert "repo-containment.no-root" in blocked.stderr


def test_hook_sink_matches_tmp_paths(tmp_path):
    """Shared contract: the hook's effective sink equals TmpPaths.absolute."""
    import yaml

    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: true\n'
        '    path: "scratch/x"\n',
    )
    config = yaml.safe_load(
        (root / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
    )
    paths = resolve_tmp_paths(root, config)
    assert paths.absolute is not None

    stderr = _outside_block_stderr(root)
    allowed = next(line for line in stderr.splitlines() if "allowed:" in line)
    assert allowed.strip().endswith(f"and under {paths.absolute}")
    assert str(paths.absolute) == os.path.realpath(root / "scratch" / "x")


# --- Safe-side: invalid tmp-sink paths fall back to ".tmp" -------------
# The inline config reader mirrors scripts/lib/repo_containment.py::
# tmp_sink_path_error — a Windows drive-letter prefix or a path that
# normalizes to the repo root itself must not become the effective sink. On a
# blocked OUTSIDE write, block_write() prints the effective sink path in
# stderr, which makes the ".tmp" fallback observable without extra plumbing.


def _outside_block_stderr(root: Path) -> str:
    result = _run_hook(_write_payload(root.parent / "outside.py", root))
    assert result.returncode == 2, result.stderr
    return result.stderr


def test_block_message_uses_absolute_sink(tmp_path):
    """AC-18: a blocked write names the absolute root and the absolute sink.

    No ``<root>/<relative-sink>`` concatenation artifact and no bare ``.tmp``:
    both paths are realpaths, as computed by ``resolve_tmp_paths().absolute``.
    """
    root = _project(tmp_path)
    stderr = _outside_block_stderr(root)

    real_root = os.path.realpath(root)
    real_sink = os.path.realpath(root / ".tmp")
    assert real_sink == f"{real_root}/.tmp"

    assert f"  repo root: {real_root}" in stderr
    assert f"allowed:   paths under {real_root} and under {real_sink}" in stderr
    # The relative sink never appears as a standalone allowed location.
    assert " under .tmp" not in stderr
    # Fixed message skeleton (spec §Fehlermeldungen).
    assert f"  anchor:    {real_root}" in stderr
    assert "  repair:    write inside " in stderr
    assert (
        f"  opt-out:   repo_containment.enabled: false in {real_root}/.meta-config/project.yaml"
        in stderr
    )


def test_valid_custom_sink_path_is_reflected_in_stderr(tmp_path):
    """Control: a valid custom sink path IS used (proves the reader works)."""
    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: true\n'
        '    path: "scratch/x"\n',
    )
    assert f"under {root}/scratch/x" in _outside_block_stderr(root)


def test_sink_path_dot_slash_dot_falls_back_to_default(tmp_path):
    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: true\n'
        '    path: "./."\n',
    )
    stderr = _outside_block_stderr(root)
    assert f"under {root}/.tmp" in stderr
    assert "./." not in stderr


def test_sink_path_drive_letter_falls_back_to_default(tmp_path):
    root = _project(
        tmp_path,
        'repo_containment:\n'
        '  enabled: true\n'
        '  tmp-sink:\n'
        '    enabled: true\n'
        '    path: "C:\\\\x"\n',
    )
    stderr = _outside_block_stderr(root)
    assert f"under {root}/.tmp" in stderr
    assert "C:\\x" not in stderr


# --- Hook source health ------------------------------------------------

def test_hook_wrapper_and_impl_are_valid_bash():
    for script in (_HOOK_PATH, _IMPL_PATH):
        result = subprocess.run(
            [_BASH, "-n", str(script)], capture_output=True, text=True
        )
        assert result.returncode == 0, (script, result.stderr)


# --- issue #630: self-health wrapper carve-out ----------------------------
# repo-containment.sh (thin wrapper) syntax-checks repo-containment-impl.sh
# with `bash -n` before running it. If impl.sh is broken, the wrapper allows
# Write/Edit on EXACTLY the impl script (and the wrapper itself, mirroring
# orchestrator-guard.sh's own-directory carve-out) while every other path —
# including siblings under the same hooks directory — still fails CLOSED. The
# carve-out was narrowed from "any file under $SCRIPT_DIR" after review.


def _isolated_wrapper_with_broken_impl(tmp_path) -> Path:
    """Deploy an isolated wrapper + broken impl pair under <tmp>/.claude/hooks/.

    Mirrors the real deployment layout so "the impl script" vs. "any sibling
    under the same directory" is a meaningful distinction.
    """
    hooks_dir = tmp_path / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    isolated_hook = hooks_dir / "repo-containment.sh"
    isolated_hook.write_text(_HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    broken_impl = hooks_dir / "repo-containment-impl.sh"
    # Unclosed `if` -> `bash -n` must fail (the exact trigger for the carve-out).
    broken_impl.write_text("if true; then\n", encoding="utf-8")
    return isolated_hook


def _run_isolated(hook: Path, payload: dict, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=_clean_env(),
    )


def test_broken_impl_blocks_bash_calls(tmp_path):
    hook = _isolated_wrapper_with_broken_impl(tmp_path)
    result = _run_isolated(hook, _bash_payload("ls -la", tmp_path), tmp_path)
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "syntax error" in result.stderr.lower()


def test_broken_impl_allows_edit_of_impl_script_only(tmp_path):
    hook = _isolated_wrapper_with_broken_impl(tmp_path)
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(hook.parent / "repo-containment-impl.sh")},
        "cwd": str(tmp_path),
    }
    result = _run_isolated(hook, payload, tmp_path)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_broken_impl_blocks_edit_of_sibling_under_hooks_dir(tmp_path):
    hook = _isolated_wrapper_with_broken_impl(tmp_path)
    sibling = hook.parent / "lib" / "hook_common.sh"
    sibling.parent.mkdir(parents=True, exist_ok=True)
    sibling.write_text("# sibling\n", encoding="utf-8")
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(sibling)},
        "cwd": str(tmp_path),
    }
    result = _run_isolated(hook, payload, tmp_path)
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"


def test_broken_impl_allows_edit_of_wrapper_itself(tmp_path):
    """The wrapper is exempted too, mirroring orchestrator-guard.sh."""
    hook = _isolated_wrapper_with_broken_impl(tmp_path)
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": str(hook)},
        "cwd": str(tmp_path),
    }
    result = _run_isolated(hook, payload, tmp_path)
    assert result.returncode == 0, f"stdout={result.stdout!r} stderr={result.stderr!r}"


@pytest.mark.parametrize(
    "yaml_path",
    ['"\\\\\\\\server\\\\share\\\\x"', '"CON"', '".GIT"', '".Codex/out"', '"a:b"', '"x."'],
)
def test_unsafe_sink_path_falls_back_to_default(tmp_path, yaml_path):
    """IC-15 Nr. 27 f: the hook mirrors the hardened rules (UNC, reserved, protected)."""
    root = _project(
        tmp_path,
        'repo_containment:\n  enabled: true\n  tmp-sink:\n    enabled: true\n'
        f'    path: {yaml_path}\n',
    )
    assert f"under {root}/.tmp" in _outside_block_stderr(root)


def test_sink_path_backslash_is_canonicalized(tmp_path):
    root = _project(
        tmp_path,
        'repo_containment:\n  enabled: true\n  tmp-sink:\n    enabled: true\n'
        '    path: "scratch\\\\out"\n',
    )
    assert f"under {root}/scratch/out" in _outside_block_stderr(root)


# --- SR-B-17: wrapper maps impl exit status to {0, 2} -----------------------
# Same gap as SR-B-08 on orchestrator-guard.sh: the harness only blocks on
# exit 2, so a crashed impl (rc 1 / 137 / 141) passed straight through and
# the tool call proceeded. Only {0, 2} may be propagated.

def _wrapper_with_stub_impl(tmp_path, impl_body: str) -> Path:
    hooks_dir = tmp_path / "hooks"
    hooks_dir.mkdir()
    wrapper = hooks_dir / "repo-containment.sh"
    wrapper.write_text(_HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (hooks_dir / "repo-containment-impl.sh").write_text(
        "#!/bin/bash\ncat >/dev/null\n" + impl_body + "\n", encoding="utf-8",
    )
    return wrapper


@pytest.mark.parametrize("impl_body,crash_rc", [
    ("set -u\necho \"$UNBOUND_VAR_SR_B_17\"", 1),
    ("kill -KILL $$", 137),
    ("kill -PIPE $$", 141),
    ("exit 3", 3),
])
def test_wrapper_fails_closed_on_impl_crash(tmp_path, impl_body, crash_rc):
    wrapper = _wrapper_with_stub_impl(tmp_path, impl_body)
    result = subprocess.run(
        [_BASH, str(wrapper)],
        input=json.dumps(_bash_payload("echo hi", tmp_path)),
        capture_output=True, text=True, cwd=str(tmp_path), env=_clean_env(),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert f"impl crashed rc={crash_rc}" in result.stderr
    assert "failing closed" in result.stderr


@pytest.mark.parametrize("impl_rc", [0, 2])
def test_wrapper_passes_through_allow_and_block(tmp_path, impl_rc):
    wrapper = _wrapper_with_stub_impl(tmp_path, f"exit {impl_rc}")
    result = subprocess.run(
        [_BASH, str(wrapper)],
        input=json.dumps(_bash_payload("echo hi", tmp_path)),
        capture_output=True, text=True, cwd=str(tmp_path), env=_clean_env(),
    )
    assert result.returncode == impl_rc, f"stderr={result.stderr!r}"
    assert "impl crashed" not in result.stderr


# --- review finding M2: payload/tool_name fail-closed ----------------------

def _garbage_python_env(tmp_path) -> dict:
    """Environment whose `python3` EXITS 0 printing junk (the M2 trigger);
    the rest of PATH stays intact so the hook's shell utilities still work."""
    shim_dir = tmp_path / "garbage-python"
    shim_dir.mkdir()
    shim = shim_dir / "python3"
    shim.write_text("#!/bin/sh\necho garbage\n", encoding="utf-8")
    shim.chmod(0o755)
    env = _clean_env()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


def test_garbage_python_interpreter_fails_closed(tmp_path):
    """M2: junk from a broken python3 shim used to become tool_name and hit
    `*) exit 0` -- an outside write was allowed. hook_json_usable() blocks."""
    root = _project(tmp_path)
    outside = root.parent / "outside.py"
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(_write_payload(outside, root)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT),
        env=_garbage_python_env(tmp_path),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "does not behave like a Python interpreter" in result.stderr


@pytest.mark.parametrize("tool", ["Frobnicate", "bash", "run_command"])
def test_unknown_tool_name_fails_closed(tmp_path, tool):
    """M2: an unrecognized tool_name used to hit `*) exit 0` (allow)."""
    root = _project(tmp_path)
    result = _run_hook({"tool_name": tool, "tool_input": {}, "cwd": str(root)})
    assert result.returncode == 2, result.stderr
    assert f"unknown tool_name '{tool}'" in result.stderr


@pytest.mark.parametrize("payload", [
    {"tool_input": {}},                       # no tool_name at all
    {"tool_name": None, "tool_input": {}},    # null
    {"tool_name": ["Write"], "tool_input": {}},   # array
    {"tool_name": {"name": "Write"}, "tool_input": {}},  # object
])
def test_missing_or_non_scalar_tool_name_fails_closed(payload):
    result = _run_hook(payload)
    assert result.returncode == 2, result.stderr
    assert "empty or unparseable PreToolUse payload" in result.stderr


@pytest.mark.parametrize("tool", [
    "Read", "Glob", "Grep", "WebFetch", "TodoWrite", "Task",
    "mcp__playwright__browser_navigate",
])
def test_known_non_mutating_tools_stay_allowed(tmp_path, tool):
    """M2 must not over-block: known non-writing tools keep their pass-through
    even when the target path would be blocked for Write/Edit."""
    root = _project(tmp_path)
    result = _run_hook({"tool_name": tool, "tool_input": {"file_path": "/etc/passwd"},
                        "cwd": str(root)})
    assert result.returncode == 0, result.stderr


def test_outdated_helper_lib_fails_closed(tmp_path):
    """A deployed lib/hook_common.sh without hook_known_tool_name must block
    with a clear message instead of failing obscurely."""
    root = _project(tmp_path)
    hooks_dir = tmp_path / "hooks"
    (hooks_dir / "lib").mkdir(parents=True)
    (hooks_dir / "repo-containment.sh").write_text(
        _HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (hooks_dir / "repo-containment-impl.sh").write_text(
        _IMPL_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (hooks_dir / "lib" / "hook_common.sh").write_text(
        "#!/bin/bash\n"
        "hook_have_python() { command -v python3 >/dev/null 2>&1; }\n"
        "hook_python_bin() { printf '%s' python3; }\n"
        "hook_json_get() { printf '%s' \"${3:-}\"; }\n"
        "hook_json_usable() { return 0; }\n",
        encoding="utf-8",
    )
    result = subprocess.run(
        [_BASH, str(hooks_dir / "repo-containment.sh")],
        input=json.dumps(_write_payload(root / "ok.py", root)),
        capture_output=True, text=True, cwd=str(root), env=_clean_env(),
    )
    assert result.returncode == 2, f"stdout={result.stdout!r} stderr={result.stderr!r}"
    assert "outdated" in result.stderr


# --- issue #944: repo-containment hardening (W2-B3) -----------------------
# SR-B-16 heredoc false positives, SR-B-17 wrapper exit mapping (already
# covered above), the detector's fail-open `|| true`, SR-B-18 fixed jail root,
# SR-B-19 missed in-place/destination spellings, SR-B-20 silent PyYAML opt-out.


def _clean_env() -> dict:
    """Never inherit $CLAUDE_PROJECT_DIR: the fixed jail root (SR-B-18) prefers
    it, so a value from the surrounding Claude session would retarget the
    tests. Tests that need it set it explicitly."""
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    return env


@pytest.mark.parametrize("command", [
    "cat >> notes.md <<'EOF'\ntext with `2>/dev/null` and > /etc/x\nEOF",
    "cat > notes.md <<EOF\nblockquote: > /etc/passwd\nEOF",
    "python - <<'PY'\nprint('> /etc/x')\nPY",
])
def test_heredoc_body_is_not_scanned_as_commands(tmp_path, command):
    """SR-B-16: prose/markdown inside a heredoc produced false-positive
    blocks. The body is skipped; the write to notes.md itself is inside the
    root (and not part of WRITE_ALL), so the command is allowed."""
    root = _project(tmp_path)
    result = _run_hook(_bash_payload(command, root))
    assert result.returncode == 0, result.stderr


def test_command_after_heredoc_terminator_is_still_scanned(tmp_path):
    """SR-B-16: skipping the body must not skip the rest of the command."""
    root = _project(tmp_path)
    result = _run_hook(
        _bash_payload("cat <<'EOF'\nprose\nEOF\ntouch /etc/after-heredoc", root)
    )
    assert result.returncode == 2, result.stderr
    assert "outside the repository root" in result.stderr


# --- v1.5.0: wrapper / `--` / case blind spot (guard v1.9.2 parity) -------


@pytest.mark.parametrize("template", [
    # Wrapper with a positional prefix, `--` directly before the command.
    "timeout 5 -- touch {target}",
    "flock -w 5 {lock} -- touch {target}",
    "chroot /x -- touch {target}",
    # Wrapper options on either side of the marker.
    "timeout --signal=KILL 5 -- touch {target}",
    "env -u HOME -- touch {target}",
    # `case … in` arm, one-line and split across statements.
    "case x in x) touch {target} ;; esac",
    "case x\nin x) touch {target}\nesac",
    "case x in\n  x) touch {target}\n  ;;\nesac",
    # Inline function body, subshell, group, if, for, while.
    "f() {{ touch {target}; }}",
    "function f {{ touch {target}; }}",
    "( touch {target} )",
    "{{ touch {target}; }}",
    "if true; then touch {target}; fi",
    "for f in a; do touch {target}; done",
    "while true; do touch {target}; break; done",
])
def test_wrapper_and_compound_shapes_outside_root_are_blocked(tmp_path, template):
    """The containment detector used its own wrapper-name-only skip loop and
    knew neither `--` transparency nor `case`/function/grouping, so every one
    of these resolved to NO command and was allowed (rc 0). The shared
    resolver (hook_shell_resolver_py) fixes all of them; the orchestrator
    guard got the same shapes in v1.9.2."""
    root = _project(tmp_path)
    target = root.parent / "outside-target.txt"
    command = template.format(target=target, lock=root.parent / "outside.lock")
    result = _run_hook(_bash_payload(command, root))
    assert result.returncode == 2, result.stderr
    assert "outside the repository root" in result.stderr


@pytest.mark.parametrize("template", [
    "timeout 5 -- touch {target}",
    "flock -w 5 {lock} -- touch {target}",
    "chroot /x -- touch {target}",
    "case x in x) touch {target} ;; esac",
    "case x\nin x) touch {target}\nesac",
    "f() {{ touch {target}; }}",
    "( touch {target} )",
    "if true; then touch {target}; fi",
    "for f in a; do touch {target}; done",
    "touch .tmp/{name}",
    "sed -i s/a/b/ {target}",
    "cp {source} -t .",
    "timeout 5 -- sed -i s/a/b/ {target}",
])
def test_wrapper_and_compound_shapes_inside_root_stay_allowed(tmp_path, template):
    """Counter-check for the same shapes: writes inside the root (and into
    the `.tmp/` sink) remain allowed, so the resolver must not over-block."""
    root = _project(tmp_path)
    (root / "inroot.txt").write_text("x", encoding="utf-8")
    (root / "source.txt").write_text("x", encoding="utf-8")
    command = template.format(
        target=root / "inroot.txt",
        name="scratch.txt",
        lock=root / "lock",
        source=root / "source.txt",
    )
    result = _run_hook(_bash_payload(command, root))
    assert result.returncode == 0, result.stderr


def test_detector_crash_fails_closed(tmp_path):
    """Verifier note: the detector ended in `|| true`, so a Python crash
    ALLOWED the command. A crash must block."""
    root = _project(tmp_path)
    shim_dir = tmp_path / "detector-shim"
    shim_dir.mkdir()
    real = shutil.which("python3") or "python3"
    shim = shim_dir / "python3"
    shim.write_text(
        "#!/bin/sh\n"
        'case "${2:-}" in\n'
        '  *WRITE_ALL*) exit 1 ;;\n'
        "esac\n"
        'exec "' + real + '" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    env = _clean_env()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(_bash_payload("echo hi", root)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT), env=env,
    )
    assert result.returncode == 2, result.stderr
    assert "detector exited rc=1" in result.stderr


@pytest.mark.parametrize("command", [
    "perl -pi -e 's/a/b/' /etc/target",
    "sed -Ei 's/a/b/' /etc/target",
    "sed -ni 's/a/b/p' /etc/target",
    "sed -i 's/a/b/' /etc/target",
    "ruby -pi -e 'x' /etc/target",
    "cp -t /etc source",
    "cp --target-directory=/etc source",
    "cp -t/etc source",
    "cp source /etc/target -v",
    "cp source /etc/target --verbose",
])
def test_inplace_and_destination_spellings_are_detected(tmp_path, command):
    """SR-B-19: perl/sed in-place clusters, `cp -t DIR` and trailing flags
    were not recognised as writes."""
    root = _project(tmp_path)
    result = _run_hook(_bash_payload(command, root))
    assert result.returncode == 2, result.stderr
    assert "outside the repository root" in result.stderr


@pytest.mark.parametrize("command", [
    "perl -pi -e 's/a/b/' notes.md",
    "sed -Ei 's/a/b/' notes.md",
    "sed -ni 's/a/b/p' notes.md",
    "cp -t . source",
    "cp source notes.md -v",
    "perl -e 'print 1' notes.md",  # -e only: no in-place edit
    "sed -n 's/a/b/p' notes.md",   # -n only: no in-place edit
])
def test_inplace_detection_does_not_over_block_inside_the_root(tmp_path, command):
    """SR-B-19 counter-check: the same spellings writing INSIDE the root stay
    allowed (and -e/-n without -i are not in-place edits)."""
    root = _project(tmp_path)
    for name in ("notes.md", "source"):
        (root / name).write_text("x", encoding="utf-8")
    result = _run_hook(_bash_payload(command, root))
    assert result.returncode == 0, result.stderr


def _deployed_hook(project: Path, provider_dir: str = ".claude") -> Path:
    """Deploy wrapper+impl+lib into <project>/<provider_dir>/hooks/ (SR-B-18
    anchor). The layout is provider-neutral (Claude, Gemini, ...)."""
    hooks = project / provider_dir / "hooks"
    (hooks / "lib").mkdir(parents=True)
    (hooks / "repo-containment.sh").write_text(
        _HOOK_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (hooks / "repo-containment-impl.sh").write_text(
        _IMPL_PATH.read_text(encoding="utf-8"), encoding="utf-8")
    (hooks / "lib" / "hook_common.sh").write_text(
        (_REPO_ROOT / "hooks" / "1-generic" / "lib" / "hook_common.sh").read_text(
            encoding="utf-8"),
        encoding="utf-8",
    )
    return hooks / "repo-containment.sh"


def test_payload_cwd_cannot_redefine_the_deployed_jail_root(tmp_path):
    """SR-B-18: with the hook deployed under project A, a payload cwd in a
    different project B must not make B the jail root. A write inside B is
    therefore outside A and blocked."""
    project_a = _config_at(tmp_path / "a")
    project_b = _config_at(tmp_path / "b")
    hook = _deployed_hook(project_a)
    result = subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(_write_payload(project_b / "x.py", project_b)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT), env=_clean_env(),
    )
    assert result.returncode == 2, result.stderr
    assert f"repo root: {os.path.realpath(project_a)}" in result.stderr


def test_claude_project_dir_is_a_fixed_anchor_from_the_source_tree(tmp_path):
    """SR-B-18: even when run from the source tree, $CLAUDE_PROJECT_DIR wins
    over the payload cwd."""
    project_a = _config_at(tmp_path / "a")
    project_b = _config_at(tmp_path / "b")
    env = _clean_env()
    env["CLAUDE_PROJECT_DIR"] = str(project_a)
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(_write_payload(project_b / "x.py", project_b)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT), env=env,
    )
    assert result.returncode == 2, result.stderr
    assert f"repo root: {os.path.realpath(project_a)}" in result.stderr


@pytest.mark.parametrize("provider_dir", [".claude", ".agents", ".gemini"])
def test_fixed_anchor_is_provider_neutral(tmp_path, provider_dir):
    """SR-B-18: the deployment-layout anchor does not depend on the Claude
    directory name."""
    project = _config_at(tmp_path / "a")
    other = _config_at(tmp_path / "b")
    hook = _deployed_hook(project, provider_dir)
    result = subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(_write_payload(other / "x.py", other)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT), env=_clean_env(),
    )
    assert result.returncode == 2, result.stderr
    assert f"repo root: {os.path.realpath(project)}" in result.stderr


def test_write_inside_the_fixed_anchor_is_allowed(tmp_path):
    """SR-B-18 counter-check: the fixed anchor must not block legitimate
    writes inside itself."""
    project = _config_at(tmp_path / "a")
    hook = _deployed_hook(project)
    result = subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(_write_payload(project / "pkg" / "x.py", project)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT), env=_clean_env(),
    )
    assert result.returncode == 0, result.stderr


# --- review findings F1/F2/F5: the shared splitter and the fixed root ----


def test_f1_ansi_c_quoting_does_not_hide_an_outside_copy(tmp_path):
    """F1: the ANSI-C quote desync swallowed the rest of the command, so an
    outside-root copy after `echo $'it\\'s'` was invisible to this guard too
    (both guards share hook_shell_scan_py)."""
    root = _project(tmp_path)
    outside = root.parent / "outside.txt"
    result = _run_hook(
        _bash_payload(f"echo $'it\\'s'; cp notes.md {outside}", root)
    )
    assert result.returncode == 2, result.stderr
    assert "outside the repository root" in result.stderr


@pytest.mark.parametrize("command", [
    "cat <<$X\nX\ntouch {target}",
    'cat <<"$X"\nX\ntouch {target}',
])
def test_f2_dynamic_heredoc_delimiter_does_not_hide_a_write(tmp_path, command):
    """F2: an unresolvable heredoc delimiter no longer suppresses the body,
    so a write target after it is still seen (fail closed)."""
    root = _project(tmp_path)
    target = root.parent / "outside-heredoc.txt"
    result = _run_hook(_bash_payload(command.format(target=target), root))
    assert result.returncode == 2, result.stderr
    assert "outside the repository root" in result.stderr


def _realpath_failing_env(tmp_path, path_to_fail: Path) -> dict:
    """PATH whose python3 delegates to the real interpreter EXCEPT when it is
    asked to realpath *path_to_fail* (then it exits 1, like a broken
    interpreter would)."""
    shim_dir = tmp_path / "realpath-shim"
    shim_dir.mkdir()
    real = shutil.which("python3") or "python3"
    shim = shim_dir / "python3"
    shim.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        f'  *os.path.realpath*"{path_to_fail}"*) exit 1 ;;\n'
        "esac\n"
        f'exec "{real}" "$@"\n',
        encoding="utf-8",
    )
    shim.chmod(0o755)
    env = _clean_env()
    env["PATH"] = f"{shim_dir}{os.pathsep}{env.get('PATH', '')}"
    return env


def test_f5_unresolvable_fixed_root_fails_closed(tmp_path):
    """F5: a SELECTED fixed root whose realpath fails must not silently
    downgrade to the payload anchor. Before the fix FIXED_ROOT became "" and
    project_b's cwd was adopted, so a write inside B was allowed (rc 0)."""
    project_a = _config_at(tmp_path / "a")
    project_b = _config_at(tmp_path / "b")
    env = _realpath_failing_env(tmp_path, project_a)
    env["CLAUDE_PROJECT_DIR"] = str(project_a)
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(_write_payload(project_b / "x.py", project_b)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT), env=env,
    )
    assert result.returncode == 2, result.stderr
    assert "could not be resolved" in result.stderr
    assert "F5" in result.stderr


def test_f5_absent_fixed_root_still_uses_the_payload_anchor(tmp_path):
    """F5 counter-check: 'no fixed root applies' (rc 1, e.g. the source-tree
    run) is NOT a failure -- the documented payload-anchor fallback stays."""
    root = _project(tmp_path)
    result = _run_hook(_write_payload(root / "notes.md", root))
    assert result.returncode == 0, result.stderr


def test_submodule_meta_config_is_skipped_in_the_walk_up(tmp_path):
    """#943 (l): a nested .agent-meta checkout is not the jail root when an
    enclosing project exists (write inside the OUTER root is allowed)."""
    outer = _config_at(tmp_path / "outer")
    sub = _config_at(outer / ".agent-meta")
    deep = sub / "src"
    deep.mkdir(parents=True)
    result = _run_hook(_write_payload(outer / "notes.md", deep))
    assert result.returncode == 0, result.stderr


def test_submodule_meta_config_is_the_fallback_when_nothing_encloses_it(tmp_path):
    """#943 (l): a session opened only inside the submodule still resolves."""
    base = Path(tempfile.mkdtemp(dir=tempfile.gettempdir(), prefix="am-submod-"))
    try:
        sub = _config_at(base / ".agent-meta")
        result = _run_hook(_write_payload(sub / "notes.md", sub))
        assert result.returncode == 0, result.stderr
    finally:
        shutil.rmtree(base, ignore_errors=True)


def _hide_pyyaml(tmp_path) -> dict:
    shadow = tmp_path / "no-yaml"
    shadow.mkdir()
    (shadow / "yaml.py").write_text(
        "raise ImportError('PyYAML hidden by test')\n", encoding="utf-8")
    env = _clean_env()
    env["PYTHONPATH"] = str(shadow)
    return env


def test_missing_pyyaml_with_enabled_false_is_reported_not_silent(tmp_path):
    """SR-B-20: without PyYAML the guard cannot honour the opt-out. It must
    stay fail-closed AND say so on stderr instead of ignoring it silently."""
    root = _project(tmp_path, "repo_containment:\n  enabled: false\n")
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(_write_payload(root.parent / "outside.py", root)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT), env=_hide_pyyaml(tmp_path),
    )
    assert result.returncode == 2, result.stderr
    assert "PyYAML" in result.stderr
    assert "enabled: false is NOT honoured" in result.stderr
    assert "outside the repository root" in result.stderr


def test_missing_pyyaml_with_enabled_true_stays_fail_closed(tmp_path):
    """SR-B-20 control: the safe-side default is unchanged."""
    root = _project(tmp_path)  # enabled: true
    result = subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(_write_payload(root.parent / "outside.py", root)),
        capture_output=True, text=True, cwd=str(_REPO_ROOT), env=_hide_pyyaml(tmp_path),
    )
    assert result.returncode == 2, result.stderr
    assert "PyYAML" in result.stderr
