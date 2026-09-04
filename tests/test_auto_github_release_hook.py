"""Tests for the auto-github-release hook (issues #518/#622).

Two layers:
  * Pure decision helpers in scripts/lib/auto_github_release.py (imported and
    called directly) — tag detection, tag_format matching, pre-release
    detection, title rendering, changelog extraction.
  * The bash wrapper hooks/1-generic/auto-github-release.sh run as a real
    subprocess with a synthetic PostToolUse payload and a FAKE `gh` on PATH
    (never touches the network). Asserts opt-in gating, idempotency, and the
    --prerelease flag.

Run: python -m pytest tests/test_auto_github_release_hook.py -v
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "auto-github-release.sh"
_BASH = shutil.which("bash") or "bash"

sys.path.insert(0, str(_REPO_ROOT / "scripts"))
from lib.auto_github_release import (  # noqa: E402
    decide,
    extract_changelog_notes,
    extract_push_refs,
    is_prerelease,
    tag_format_prefix,
    tag_format_to_regex,
    tag_version,
)

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)

_SPEC = {
    "versioning": {"tag_format": "v{major}.{minor}.{patch}"},
    "github_release": {
        "enabled": True,
        "title_pattern": "{tag}",
        "pre_release_suffixes": ["alpha", "beta", "rc"],
    },
}


# --- Pure decision helpers ------------------------------------------------

@pytest.mark.parametrize("command,expected", [
    ("git push origin v1.2.3", ["v1.2.3"]),
    ("git push origin refs/tags/v1.2.3-beta.4", ["v1.2.3-beta.4"]),
    ("git push origin +v1.2.3", ["v1.2.3"]),
    ("git push origin main v2.0.0", ["main", "v2.0.0"]),
    ("git push origin --tags", []),          # no single named tag
    ("echo git push origin v1.2.3", []),     # not a real git invocation
    ("git status", []),
])
def test_extract_push_refs(command, expected):
    assert extract_push_refs(command) == expected


def test_tag_format_matching():
    rx = tag_format_to_regex("v{major}.{minor}.{patch}")
    assert rx.match("v1.2.3")
    assert rx.match("v1.2.3-beta.1")
    assert not rx.match("1.2.3")        # missing prefix
    assert not rx.match("random-branch")


def test_tag_format_prefix_and_version():
    assert tag_format_prefix("v{major}.{minor}.{patch}") == "v"
    assert tag_format_prefix("{year}.{month}.{patch}") == ""
    assert tag_version("v1.2.3", "v") == "1.2.3"
    assert tag_version("2026.09.0", "") == "2026.09.0"


def test_is_prerelease():
    sfx = ["alpha", "beta", "rc"]
    assert is_prerelease("v1.2.3-beta.4", sfx)
    assert is_prerelease("v1.2.3-rc.1", sfx)
    assert not is_prerelease("v1.2.3", sfx)


def test_decide_stable_and_prerelease():
    assert decide("git push origin v1.2.3", _SPEC) == {
        "tag": "v1.2.3", "title": "v1.2.3", "prerelease": False,
    }
    assert decide("git push origin v1.2.3-beta.4", _SPEC) == {
        "tag": "v1.2.3-beta.4", "title": "v1.2.3-beta.4", "prerelease": True,
    }


def test_decide_disabled_returns_none():
    spec = json.loads(json.dumps(_SPEC))
    spec["github_release"]["enabled"] = False
    assert decide("git push origin v1.2.3", spec) is None


def test_decide_nonmatching_tag_returns_none():
    assert decide("git push origin some-branch", _SPEC) is None


def test_decide_title_pattern_version():
    spec = json.loads(json.dumps(_SPEC))
    spec["github_release"]["title_pattern"] = "MyApp {version}"
    assert decide("git push origin v1.2.3", spec)["title"] == "MyApp 1.2.3"


def test_extract_changelog_notes():
    cl = (
        "# Changelog\n\n"
        "## [1.2.3] — 2026-09-04\n\n"
        "### Added\n- thing\n\n"
        "## [1.2.2] — 2026-08-01\n- old\n"
    )
    assert extract_changelog_notes(cl, "1.2.3") == "### Added\n- thing"
    assert extract_changelog_notes(cl, "9.9.9") is None


# --- Integration: bash wrapper + fake gh ----------------------------------

_FAKE_GH = """#!/bin/bash
# Fake gh: logs argv, simulates `release view` via GH_FAKE_VIEW_EXIT.
printf '%s\\n' "$*" >> "$GH_FAKE_LOG"
if [ "$1" = "release" ] && [ "$2" = "view" ]; then
  exit "${GH_FAKE_VIEW_EXIT:-1}"
fi
exit 0
"""


def _make_project(tmp_path: Path, *, enabled: bool) -> Path:
    proj = tmp_path / "proj"
    (proj / ".meta-config").mkdir(parents=True)
    flag = "true" if enabled else "false"
    (proj / ".meta-config" / "project.yaml").write_text(
        "conventions:\n"
        "  release:\n"
        "    github_release:\n"
        f"      enabled: {flag}\n",
        encoding="utf-8",
    )
    return proj


def _run_hook(proj: Path, command: str, gh_log: Path, view_exit: int) -> subprocess.CompletedProcess:
    bindir = proj / "bin"
    bindir.mkdir(exist_ok=True)
    gh = bindir / "gh"
    gh.write_text(_FAKE_GH, encoding="utf-8")
    gh.chmod(0o755)

    env = dict(os.environ)
    env["PATH"] = f"{bindir}{os.pathsep}{env['PATH']}"
    env["AGR_AGENT_META_ROOT"] = str(_REPO_ROOT)
    env["GH_FAKE_LOG"] = str(gh_log)
    env["GH_FAKE_VIEW_EXIT"] = str(view_exit)

    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(proj)}
    return subprocess.run(
        [_BASH, str(_HOOK_PATH)],
        input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(proj), env=env,
    )


def _gh_calls(gh_log: Path) -> list[str]:
    return gh_log.read_text(encoding="utf-8").splitlines() if gh_log.exists() else []


def test_hook_disabled_makes_no_gh_call(tmp_path):
    proj = _make_project(tmp_path, enabled=False)
    gh_log = tmp_path / "gh.log"
    r = _run_hook(proj, "git push origin v1.2.3", gh_log, view_exit=1)
    assert r.returncode == 0
    assert _gh_calls(gh_log) == []


def test_hook_enabled_creates_release(tmp_path):
    proj = _make_project(tmp_path, enabled=True)
    gh_log = tmp_path / "gh.log"
    r = _run_hook(proj, "git push origin v1.2.3", gh_log, view_exit=1)  # release absent
    assert r.returncode == 0
    calls = _gh_calls(gh_log)
    assert any(c.startswith("release view v1.2.3") for c in calls)
    create = [c for c in calls if c.startswith("release create v1.2.3")]
    assert create and "--prerelease" not in create[0]


def test_hook_idempotent_when_release_exists(tmp_path):
    proj = _make_project(tmp_path, enabled=True)
    gh_log = tmp_path / "gh.log"
    r = _run_hook(proj, "git push origin v1.2.3", gh_log, view_exit=0)  # release exists
    assert r.returncode == 0
    calls = _gh_calls(gh_log)
    assert any(c.startswith("release view v1.2.3") for c in calls)
    assert not any(c.startswith("release create") for c in calls)


def test_hook_nonmatching_tag_no_call(tmp_path):
    proj = _make_project(tmp_path, enabled=True)
    gh_log = tmp_path / "gh.log"
    r = _run_hook(proj, "git push origin feature-branch", gh_log, view_exit=1)
    assert r.returncode == 0
    assert _gh_calls(gh_log) == []


def test_hook_prerelease_flag_for_beta_tag(tmp_path):
    proj = _make_project(tmp_path, enabled=True)
    gh_log = tmp_path / "gh.log"
    r = _run_hook(proj, "git push origin v1.2.3-beta.4", gh_log, view_exit=1)
    assert r.returncode == 0
    create = [c for c in _gh_calls(gh_log) if c.startswith("release create v1.2.3-beta.4")]
    assert create and "--prerelease" in create[0]
