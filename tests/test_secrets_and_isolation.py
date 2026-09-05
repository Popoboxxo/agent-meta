"""Regression tests for Wave 8 #586: secrets false positives, isolation dead
code, gitignore verification on secrets writes, and mcp_provider_config
substitution DRY-extraction.
"""

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.io import write_checked  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.mcp_provider_config import _subst, _subst_opencode  # noqa: E402
from lib.secrets import scan_for_secrets  # noqa: E402


# ---------------------------------------------------------------------------
# #586 point 2 -- InfluxDB-style regex false positives
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("content", [
    "sha256hash: " + "a" * 90,  # long hex hash
    "minified_var_" + "x" * 85 + "==",  # minified-code-ish identifier
    "a" * 88 + "==",  # bare long base64-ish blob
])
def test_long_base64ish_strings_no_longer_flagged(content):
    assert scan_for_secrets(content) == []


def test_real_secret_patterns_still_detected():
    assert scan_for_secrets("api_key: 1234567890abcdef1234567890abcdef") != []
    assert scan_for_secrets("sk-" + "a" * 48) != []


# ---------------------------------------------------------------------------
# #586 point 3 -- dead code removed from isolation.py
# ---------------------------------------------------------------------------

def test_isolation_no_dead_expression_statement():
    text = (_REPO_ROOT / "scripts" / "lib" / "isolation.py").read_text(encoding="utf-8")
    assert 'pc.get("isolation-dirs", [])\n' not in text


def test_isolation_still_generates_deny_entries(tmp_path):
    from lib.isolation import sync_provider_isolation

    project_root = tmp_path
    providers = ["Claude", "Opencode"]
    provider_config = {
        "Claude": {"isolation-dirs": [".claude/"], "isolation-mechanism": "claude-settings-deny"},
        "Opencode": {"isolation-dirs": ["opencode.json"], "isolation-mechanism": "opencode-permissions"},
    }
    log = SyncLog()
    sync_provider_isolation(project_root, providers, provider_config, log, dry_run=False)

    settings = (project_root / ".claude" / "settings.json")
    assert settings.exists()
    assert "**/opencode.json" in settings.read_text(encoding="utf-8")


@pytest.mark.parametrize("provider,own_dirs", [
    ("KimiCode", [".kimi-code/", "AGENTS.md"]),
    ("Codex", [".codex/", "AGENTS.md"]),
    ("ZCode", [".zcode/", "AGENTS.md"]),
])
def test_isolation_provider_without_mechanism_is_skipped(tmp_path, provider, own_dirs):
    # Plan §10 P3: providers whose registry entry has isolation-dirs but NO
    # isolation-mechanism yet (KimiCode/Codex/ZCode) must be skipped
    # gracefully — no crash, no provider-side artifacts — while the OTHER
    # provider (Claude, via claude-settings-deny) still blocks their dirs.
    from lib.isolation import sync_provider_isolation

    project_root = tmp_path
    providers = ["Claude", provider]
    provider_config = {
        "Claude": {"isolation-dirs": [".claude/"], "isolation-mechanism": "claude-settings-deny"},
        provider: {"isolation-dirs": list(own_dirs)},  # no isolation-mechanism
    }
    log = SyncLog()
    sync_provider_isolation(project_root, providers, provider_config, log, dry_run=False)

    # Claude gained deny entries for the foreign (provider-owned) dirs,
    # using the same dir→glob mapping the existing deny-entry test asserts.
    settings = (project_root / ".claude" / "settings.json")
    assert settings.exists()
    settings_text = settings.read_text(encoding="utf-8")
    for d in own_dirs:
        expected_glob = d + "**" if d.endswith("/") else f"**/{d}"
        assert expected_glob in settings_text

    # The provider itself is skipped with the documented reason and no
    # provider-side isolation artifacts were written.
    assert any(
        "no isolation mechanism defined for this provider" in s for s in log.skipped
    ), log.skipped
    assert not (project_root / own_dirs[0]).exists()


# ---------------------------------------------------------------------------
# #586 point 1 -- gitignore verification for allow_secrets writes
# ---------------------------------------------------------------------------

def _has_git() -> bool:
    try:
        subprocess.run(["git", "--version"], capture_output=True, timeout=5, check=False)
        return True
    except OSError:
        return False


@pytest.mark.skipif(not _has_git(), reason="git not installed")
def test_write_checked_warns_when_secrets_file_not_gitignored(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    target = tmp_path / "secrets.local.yaml"
    log = SyncLog()

    write_checked(target, "KEY: value\n", log, "secrets.local.yaml", allow_secrets=True,
                  verify_gitignored=True)

    assert any("not covered by .gitignore" in w for w in log.warnings)


@pytest.mark.skipif(not _has_git(), reason="git not installed")
def test_write_checked_no_warning_when_actually_gitignored(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    (tmp_path / ".gitignore").write_text("secrets.local.yaml\n", encoding="utf-8")
    target = tmp_path / "secrets.local.yaml"
    log = SyncLog()

    write_checked(target, "KEY: value\n", log, "secrets.local.yaml", allow_secrets=True,
                  verify_gitignored=True)

    assert not any("not covered by .gitignore" in w for w in log.warnings)


def test_write_checked_gitignore_check_fails_safe_outside_git_repo(tmp_path):
    # No git repo at all -- must not raise, must not block the write.
    target = tmp_path / "no_git_here" / "secrets.local.yaml"
    log = SyncLog()

    written = write_checked(target, "KEY: value\n", log, "secrets.local.yaml", allow_secrets=True,
                             verify_gitignored=True)

    assert written is True
    assert target.read_text(encoding="utf-8") == "KEY: value\n"


def test_write_checked_gitignore_check_fails_safe_when_git_missing(tmp_path, monkeypatch):
    def _raise_missing_binary(*_a, **_kw):
        raise FileNotFoundError("git not found")

    monkeypatch.setattr("lib.io.subprocess.run", _raise_missing_binary)
    target = tmp_path / "secrets.local.yaml"
    log = SyncLog()

    written = write_checked(target, "KEY: value\n", log, "secrets.local.yaml", allow_secrets=True,
                             verify_gitignored=True)

    assert written is True
    assert target.exists()


@pytest.mark.skipif(not _has_git(), reason="git not installed")
def test_write_checked_does_not_warn_for_committed_secrets_override(tmp_path):
    """allow_secrets=True via `allow-committed-secrets: true` means a
    committed (non-gitignored) file with the secrets check bypassed -- NOT
    a local file. The gitignore check must stay opt-in (verify_gitignored)
    so this legitimate case never gets a bogus "not gitignored" warning."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    target = tmp_path / "committed-with-override.md"
    log = SyncLog()

    write_checked(target, "content\n", log, "committed-with-override.md", allow_secrets=True)

    assert not any("not covered by .gitignore" in w for w in log.warnings)


# ---------------------------------------------------------------------------
# #586 point 4 -- _subst / _subst_opencode share one implementation
# ---------------------------------------------------------------------------

def test_subst_and_subst_opencode_still_behave_as_documented():
    assert _subst("{{FOO}}", None) == "${FOO}"
    assert _subst("{{FOO}}", {"FOO": "bar"}) == "bar"
    assert _subst("{{FOO}}", {"FOO": ""}) == "${FOO}"

    assert _subst_opencode("{{FOO}}", None) == "{env:FOO}"
    assert _subst_opencode("{{FOO}}", {"FOO": "bar"}) == "bar"
    assert _subst_opencode("{{FOO}}", {"FOO": ""}) == "{env:FOO}"
