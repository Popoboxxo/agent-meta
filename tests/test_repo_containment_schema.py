"""Schema tests for the ``repo_containment`` block (spec §2.1).

The block is purely additive: a config without it stays valid and the block
itself carries the framework defaults (enabled true, protected paths
``external/`` + ``.agent-meta/``, tmp-sink enabled + path ``.tmp`` + gitignore
true + cleanup ``manual``). The only closed value set is ``tmp-sink.cleanup``
(``manual`` | ``on-sync``).

Run: python -m pytest tests/test_repo_containment_schema.py -v
"""

from __future__ import annotations

import ast
import contextlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment.sh"
_HOOK_LIB_DIR = _REPO_ROOT / "hooks" / "1-generic" / "lib"
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib import repo_containment  # noqa: E402


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _base_config(repo_containment: dict | None = None) -> dict:
    config = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
        "roles": ["orchestrator", "developer", "git"],
    }
    if repo_containment is not None:
        config["repo_containment"] = repo_containment
    return config


def _rc_schema() -> dict:
    return _schema()["properties"]["repo_containment"]


# --- Additive / structural ---------------------------------------------


def test_block_is_additive_config_without_it_is_valid():
    jsonschema.validate(_base_config(), _schema())


def test_minimal_block_is_valid():
    jsonschema.validate(
        _base_config({"enabled": True}), _schema()
    )


def test_full_block_is_valid():
    jsonschema.validate(
        _base_config(
            {
                "enabled": True,
                "provider-overrides": {"Claude": {"enabled": False}},
                "tmp-sink": {
                    "enabled": True,
                    "path": ".tmp",
                    "gitignore": True,
                    "cleanup": "manual",
                },
            }
        ),
        _schema(),
    )


def test_block_additional_properties_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"enabled": True, "bogus": 1}), _schema()
        )


# --- Type traps --------------------------------------------------------


def test_non_boolean_enabled_rejected():
    for bogus in ("yes", "true", 1, None):
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(_base_config({"enabled": bogus}), _schema())


def test_non_boolean_tmp_sink_enabled_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"tmp-sink": {"enabled": "on"}}), _schema()
        )


def test_tmp_sink_additional_properties_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"tmp-sink": {"path": ".tmp", "bogus": True}}),
            _schema(),
        )


def test_provider_override_values_must_be_objects():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"provider-overrides": {"Claude": False}}),
            _schema(),
        )


def test_provider_override_entry_additional_properties_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config(
                {"provider-overrides": {"Claude": {"enabled": True, "mode": "x"}}}
            ),
            _schema(),
        )


# --- cleanup enum ------------------------------------------------------


@pytest.mark.parametrize("cleanup", ["manual", "on-sync"])
def test_cleanup_enum_accepts_both_modes(cleanup):
    jsonschema.validate(
        _base_config({"tmp-sink": {"cleanup": cleanup}}), _schema()
    )


@pytest.mark.parametrize("cleanup", ["sometimes", "", "auto", "Manual"])
def test_cleanup_enum_rejects_everything_else(cleanup):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"tmp-sink": {"cleanup": cleanup}}), _schema()
        )


# --- Defaults (must match the framework resolver) ----------------------


def test_schema_defaults_match_spec():
    rc = _rc_schema()
    assert rc["properties"]["enabled"]["default"] is True
    sink = rc["properties"]["tmp-sink"]["properties"]
    assert sink["enabled"]["default"] is True
    assert sink["path"]["default"] == ".tmp"
    assert sink["gitignore"]["default"] is True
    assert sink["cleanup"]["default"] == "manual"
    assert set(sink["cleanup"]["enum"]) == {"manual", "on-sync"}


def test_block_is_closed_at_top_level():
    assert _rc_schema().get("additionalProperties") is False


# --- system-temp-exception --------------------------------------------


def _exception_schema() -> dict:
    return _rc_schema()["properties"]["tmp-sink"]["properties"][
        "system-temp-exception"
    ]


def test_system_temp_exception_block_is_valid():
    jsonschema.validate(
        _base_config(
            {
                "tmp-sink": {
                    "system-temp-exception": {
                        "enabled": True,
                        "reason": "pytest basetemp must stay outside the repo",
                        "pytest-basetemp": True,
                        "toolchain-caches": False,
                    }
                }
            }
        ),
        _schema(),
    )


def test_system_temp_exception_defaults_match_spec():
    props = _exception_schema()["properties"]
    assert props["enabled"]["default"] is True
    assert props["pytest-basetemp"]["default"] is True
    assert props["toolchain-caches"]["default"] is False
    assert _exception_schema().get("additionalProperties") is False


def test_system_temp_exception_must_be_an_object():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"tmp-sink": {"system-temp-exception": "on"}}),
            _schema(),
        )


@pytest.mark.parametrize("key", ["enabled", "pytest-basetemp", "toolchain-caches"])
def test_system_temp_exception_booleans_only(key):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config({"tmp-sink": {"system-temp-exception": {key: "yes"}}}),
            _schema(),
        )


def test_system_temp_exception_additional_properties_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _base_config(
                {"tmp-sink": {"system-temp-exception": {"bogus": True}}}
            ),
            _schema(),
        )


# --- protected_paths (T28 / #1275b) -------------------------------------


def _protected_schema() -> dict:
    return _rc_schema()["properties"]["protected_paths"]


def test_protected_paths_schema_accepts_string_list():
    jsonschema.validate(
        _base_config({"protected_paths": ["external/", "vendor/lib"]}),
        _schema(),
    )


@pytest.mark.parametrize("bogus", ["external/", 1, None, {}])
def test_protected_paths_schema_rejects_non_list(bogus):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_config({"protected_paths": bogus}), _schema())


@pytest.mark.parametrize("bogus", [[1], [True], [None], [""]])
def test_protected_paths_schema_rejects_invalid_items(bogus):
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_base_config({"protected_paths": bogus}), _schema())


def test_protected_paths_schema_defaults_are_explicit():
    assert _protected_schema()["default"] == ["external/", ".agent-meta/"]
    block = repo_containment.default_repo_containment_block()
    assert block["protected_paths"] == ["external/", ".agent-meta/"]
    block["protected_paths"].append("mutated")
    assert repo_containment.default_repo_containment_block()["protected_paths"] == [
        "external/",
        ".agent-meta/",
    ]


def _project(tmp_path: Path, config: dict, gitmodules: str | None = None) -> Path:
    root = tmp_path / "project"
    meta = root / ".meta-config"
    meta.mkdir(parents=True)
    (meta / "project.yaml").write_text(
        "repo_containment:\n"
        "  protected_paths: " + json.dumps(config["protected_paths"]) + "\n",
        encoding="utf-8",
    )
    if gitmodules is not None:
        (root / ".gitmodules").write_text(gitmodules, encoding="utf-8")
    return root


def test_resolver_defaults_without_gitmodules(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    effective = repo_containment.resolve_effective_repo_containment(
        {}, project_root=root
    )
    assert effective.protected_paths == ["external", ".agent-meta"]
    assert effective.findings == []


def test_resolver_custom_list_replaces_defaults_and_appends_gitmodules(tmp_path):
    paths = ["./vendor/", "vendor", "shared\\lib"]
    root = _project(
        tmp_path,
        {"protected_paths": paths},
        '[submodule "core"]\n  path = modules/core\n'
        '[submodule "overlap"]\n  path = vendor\n',
    )
    effective = repo_containment.resolve_effective_repo_containment(
        {"repo_containment": {"protected_paths": paths}}, project_root=root
    )
    assert effective.protected_paths == ["vendor", "shared/lib", "modules/core"]
    assert effective.findings == []


def test_resolver_explicit_empty_list_keeps_only_gitmodules_paths(tmp_path):
    root = _project(
        tmp_path,
        {"protected_paths": []},
        '[submodule "core"]\n  path = modules/core\n',
    )
    effective = repo_containment.resolve_effective_repo_containment(
        {"repo_containment": {"protected_paths": []}}, project_root=root
    )
    assert effective.protected_paths == ["modules/core"]
    assert effective.findings == []


def test_resolver_defaults_are_appended_with_gitmodules_when_key_missing(tmp_path):
    root = tmp_path / "project"
    root.mkdir()
    (root / ".gitmodules").write_text(
        '[submodule "core"]\n  path = modules/core\n', encoding="utf-8"
    )
    effective = repo_containment.resolve_effective_repo_containment(
        {"repo_containment": {"enabled": True}}, project_root=root
    )
    assert effective.protected_paths == ["external", ".agent-meta", "modules/core"]


@pytest.mark.parametrize(
    "bogus",
    [
        "external/",
        ["vendor", 7],
        ["../escape"],
        ["/absolute"],
        ["C:\\escape"],
        ["vendor\ninjected"],
    ],
)
def test_resolver_invalid_protected_paths_fail_safe_to_defaults(tmp_path, bogus):
    root = tmp_path / "project"
    root.mkdir()
    (root / ".gitmodules").write_text(
        '[submodule "core"]\n  path = modules/core\n', encoding="utf-8"
    )
    effective = repo_containment.resolve_effective_repo_containment(
        {"repo_containment": {"protected_paths": bogus}}, project_root=root
    )
    assert effective.protected_paths == ["external", ".agent-meta", "modules/core"]
    assert any(f.code == "repo-containment.protected-paths" for f in effective.findings)


def _load_hook_module(filename: str):
    path = _HOOK_LIB_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call_hook_module(module, argv):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = module.main(argv, "")
    return rc, stdout.getvalue(), stderr.getvalue()


def _hook_values(stdout: str) -> dict:
    return dict(line.split("=", 1) for line in stdout.splitlines() if "=" in line)


def test_hook_config_emits_same_effective_paths_as_resolver(tmp_path, monkeypatch):
    monkeypatch.delenv("ARTIFACT_SCRATCH_DIR", raising=False)
    paths = [
        "./vendor/",
        "vendor",
        "VENDOR",
        "shared\\lib",
        "space dir",
        'quote"dir',
    ]
    root = _project(
        tmp_path,
        {"protected_paths": paths},
        '[submodule "core"]\n  path = modules/core\n',
    )
    config_file = root / ".meta-config" / "project.yaml"
    module = _load_hook_module("hook_containment_config.py")
    rc, stdout, stderr = _call_hook_module(
        module, [str(config_file), "", "--include-protected-paths"]
    )
    assert rc == 0, stderr
    values = _hook_values(stdout)
    encoded = values["PROTECTED_PATHS_JSON"]
    assert "\n" not in encoded and "\r" not in encoded
    assert json.loads(encoded) == [
        "vendor",
        "shared/lib",
        "space dir",
        'quote"dir',
        "modules/core",
    ]
    effective = repo_containment.resolve_effective_repo_containment(
        {"repo_containment": {"protected_paths": paths}}, project_root=root
    )
    assert json.loads(encoded) == effective.protected_paths


@pytest.mark.parametrize("bogus", ["external/", ["vendor", 7], ["vendor\ninjected"]])
def test_hook_config_invalid_paths_warn_and_fail_safe(tmp_path, monkeypatch, bogus):
    monkeypatch.delenv("ARTIFACT_SCRATCH_DIR", raising=False)
    root = _project(
        tmp_path,
        {"protected_paths": bogus},
        '[submodule "core"]\n  path = modules/core\n',
    )
    module = _load_hook_module("hook_containment_config.py")
    rc, stdout, stderr = _call_hook_module(
        module,
        [str(root / ".meta-config" / "project.yaml"), "", "--include-protected-paths"],
    )
    assert rc == 0
    assert "protected_paths" in stderr
    assert json.loads(_hook_values(stdout)["PROTECTED_PATHS_JSON"]) == [
        "external",
        ".agent-meta",
        "modules/core",
    ]


def test_hook_config_unreadable_yaml_keeps_defaults_and_gitmodules(tmp_path, monkeypatch):
    monkeypatch.delenv("ARTIFACT_SCRATCH_DIR", raising=False)
    root = tmp_path / "project"
    meta = root / ".meta-config"
    meta.mkdir(parents=True)
    (meta / "project.yaml").write_text(": [broken", encoding="utf-8")
    (root / ".gitmodules").write_text(
        '[submodule "core"]\n  path = modules/core\n', encoding="utf-8"
    )
    module = _load_hook_module("hook_containment_config.py")
    rc, stdout, stderr = _call_hook_module(
        module, [str(meta / "project.yaml"), "", "--include-protected-paths"]
    )
    assert rc == 0
    assert "containment stays ENABLED" in stderr
    assert json.loads(_hook_values(stdout)["PROTECTED_PATHS_JSON"]) == [
        "external",
        ".agent-meta",
        "modules/core",
    ]


def _clean_hook_env() -> dict:
    env = dict(os.environ)
    for name in (
        "AM_PROJECT_DIR",
        "CLAUDE_PROJECT_DIR",
        "AM_ALLOW_PROTECTED_WRITE",
        "ARTIFACT_SCRATCH_DIR",
    ):
        env.pop(name, None)
    return env


def _run_write_hook(root: Path, target: str, env: dict | None = None):
    return subprocess.run(
        [shutil.which("bash") or "bash", str(_HOOK_PATH)],
        input=json.dumps(
            {"tool_name": "Write", "tool_input": {"file_path": target}, "cwd": str(root)}
        ),
        capture_output=True,
        text=True,
        cwd=str(root),
        env=_clean_hook_env() if env is None else env,
        timeout=30,
    )


def test_hook_routes_custom_and_gitmodules_paths_with_quotes(tmp_path):
    root = _project(
        tmp_path,
        {"protected_paths": ["vendor", "space dir", 'quote"dir']},
        '[submodule "core"]\n  path = modules/core\n',
    )
    targets = (
        "vendor/file",
        "space dir/file",
        'quote"dir/file',
        "modules/core/file",
    )
    for target in targets:
        result = _run_write_hook(root, target)
        assert result.returncode == 2, result.stderr
        assert "protected path" in result.stderr
    allowed = _run_write_hook(root, "docs/file")
    assert allowed.returncode == 0, allowed.stderr
    env = _clean_hook_env()
    env["AM_ALLOW_PROTECTED_WRITE"] = "1"
    override = _run_write_hook(root, "vendor/file", env)
    assert override.returncode == 0, override.stderr


def test_repo_containment_sources_parse_as_python39():
    for path in (
        _SCRIPTS_DIR / "lib" / "repo_containment.py",
        _HOOK_LIB_DIR / "hook_containment_config.py",
        _HOOK_LIB_DIR / "hook_containment_path.py",
    ):
        ast.parse(
            path.read_text(encoding="utf-8"),
            filename=str(path),
            feature_version=(3, 9),
        )
