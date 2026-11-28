"""Phase 3 (admin setup mode) T1: pure config builders extracted from the
CLI setup wizard. AC-5 (golden parity wizard vs. build_setup_config) and the
unit part of AC-6 (validate_setup_answers)."""
from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import setup as setup_mod  # noqa: E402
from lib.setup import run_setup_wizard  # noqa: E402

_VERSION = (_REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
_SECRETS = [".env*", "*.pem", "*.key", "credentials*.json", "secret*.y*ml"]
_ROLES = ["orchestrator", "agent-meta-manager", "developer", "documenter",
          "meta-feedback", "log-analyzer", "git"]


def _run_wizard(tmp_path, inputs):
    with patch("lib.setup._QUESTIONARY_AVAILABLE", False), \
         patch("sys.stdin.isatty", return_value=True), \
         patch("builtins.input", side_effect=inputs):
        return run_setup_wizard(
            agent_meta_root=_REPO_ROOT,
            project_root=tmp_path,
            target_config=tmp_path / "project.yaml",
            dry_run=True,
        )


# name, prefix, short, providers, git platform, remote, branch, secrets, optional
_MINIMAL_INPUTS = ["my-proj", "mp", "", "", "", "", "", "", "no"]

_GOLDEN_MINIMAL = {
    "agent-meta-version": _VERSION,
    "ai-providers": ["Claude"],
    "roles": _ROLES,
    "gitignore": {"custom_entries": _SECRETS},
    "dod-preset": "standard",
    "project": {"name": "my-proj", "prefix": "mp", "short": "my-proj"},
    "variables": {
        "PROJECT_CONTEXT": "my-proj — short description.",
        "PROJECT_GOAL": "Primary goal of my-proj.",
        "PROJECT_LANGUAGES": "TypeScript",
        "COMMUNICATION_LANGUAGE": "English",
        "USER_INPUT_LANGUAGE": "English",
        "DOCS_LANGUAGE": "English",
        "INTERNAL_DOCS_LANGUAGE": "English",
        "CODE_LANGUAGE": "English",
        "AGENT_META_REPO": "Popoboxxo/agent-meta",
        "GIT_PLATFORM": "GitHub",
        "GIT_REMOTE_URL": "",
        "GIT_MAIN_BRANCH": "main",
        "DEV_COMMANDS": "bun run build",
        "TEST_COMMANDS": "bun test",
        "BUILD_COMMANDS": "bun run build",
        "CODE_CONVENTIONS": "- TypeScript ES6+, no `any`, no `var`",
        "ARCHITECTURE": "src/\\n  index.ts  # Entry-Point",
        "REQ_CATEGORIES": "- Core features\\n- Non-functional requirements",
    },
}


def test_golden_wizard_minimal(tmp_path):
    assert _run_wizard(tmp_path, _MINIMAL_INPUTS) == _GOLDEN_MINIMAL


def test_build_matches_wizard_minimal(tmp_path):
    answers = {"name": "my-proj", "prefix": "mp", "providers": ["Claude"],
               "git_platform": "GitHub"}
    assert setup_mod.build_setup_config(answers, _REPO_ROOT) == _GOLDEN_MINIMAL


def test_build_matches_wizard_full(tmp_path):
    inputs = [
        "demo", "dm", "Demo App",            # identity
        "1, 2",                              # providers
        "GitLab", "https://x.example/o/r", "develop",
        "no",                                # secrets
        "yes",                               # optional
        "hacs",                              # platforms
        "full",                              # dod preset
        "German", "German", "English", "German", "English",
        "o/r", "Ctx", "Python", "make", "pytest",
    ]
    wizard_cfg = _run_wizard(tmp_path, inputs)
    providers = wizard_cfg["ai-providers"]
    assert len(providers) == 2
    answers = {
        "name": "demo", "prefix": "dm", "short": "Demo App",
        "providers": providers, "git_platform": "GitLab",
        "git_remote": "https://x.example/o/r", "git_branch": "develop",
        "ignore_secrets": False, "platforms": ["hacs"], "dod_preset": "full",
        "communication_language": "German", "user_input_language": "German",
        "docs_language": "English", "internal_docs_language": "German",
        "code_language": "English", "agent_meta_repo": "o/r",
        "project_context": "Ctx", "project_languages": "Python",
        "dev_commands": "make", "test_commands": "pytest",
    }
    assert setup_mod.build_setup_config(answers, _REPO_ROOT) == wizard_cfg
    assert "gitignore" not in wizard_cfg


def test_build_has_no_io(tmp_path, capsys):
    setup_mod.build_setup_config(
        {"name": "a", "prefix": "a", "providers": ["Claude"], "git_platform": "GitHub"},
        _REPO_ROOT)
    assert capsys.readouterr().out == ""


def _valid():
    return {"name": "my-proj", "prefix": "mp", "providers": ["Claude"],
            "git_platform": "GitHub"}


def test_validate_ok():
    assert setup_mod.validate_setup_answers(_valid(), _REPO_ROOT) == []


def test_validate_bad_prefix():
    for bad in ("", "toolongprefix", "a b", "a/b"):
        a = _valid(); a["prefix"] = bad
        assert setup_mod.validate_setup_answers(a, _REPO_ROOT)


def test_validate_unknown_provider_and_empty():
    a = _valid(); a["providers"] = ["NoSuchProvider"]
    assert setup_mod.validate_setup_answers(a, _REPO_ROOT)
    a["providers"] = []
    assert setup_mod.validate_setup_answers(a, _REPO_ROOT)


def test_validate_missing_name_and_git_platform():
    a = _valid(); a["name"] = ""
    assert setup_mod.validate_setup_answers(a, _REPO_ROOT)
    a = _valid(); a["git_platform"] = "Nope"
    assert setup_mod.validate_setup_answers(a, _REPO_ROOT)
    assert setup_mod.validate_setup_answers({}, _REPO_ROOT)


def _errs(**over):
    a = _valid(); a.update(over)
    return setup_mod.validate_setup_answers(a, _REPO_ROOT)


def _names(errors, field):
    return any(e.startswith(f"{field}:") for e in errors)


def test_validate_errors_name_the_field():
    assert _names(_errs(prefix=""), "prefix")
    assert _names(_errs(name=""), "name")
    assert _names(_errs(providers=["NoSuchProvider"]), "providers")
    assert _names(_errs(git_platform="Nope"), "git_platform")


def test_validate_invalid_and_none_dod_preset():
    assert _names(_errs(dod_preset="bogus"), "dod_preset")
    assert _names(_errs(dod_preset=None), "dod_preset")
    assert _errs(dod_preset="full") == []


def test_validate_non_list_providers():
    assert _names(_errs(providers="Claude"), "providers")
    assert _names(_errs(providers=[1]), "providers")


def test_validate_wrong_type_optional_fields():
    assert _names(_errs(ignore_secrets="yes"), "ignore_secrets")
    assert _names(_errs(platforms="hacs"), "platforms")
    assert _names(_errs(platforms=[1]), "platforms")
    assert _names(_errs(dev_commands=5), "dev_commands")
    assert _names(_errs(short=None), "short")


def test_validate_length_cap():
    assert _names(_errs(project_context="x" * 501), "project_context")
    assert _names(_errs(name="x" * 501), "name")
    assert _errs(project_context="x" * 500) == []
