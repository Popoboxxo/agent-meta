"""Sync-time validator tests for ``_validate_repo_containment`` (spec §4.3).

The validator is the single hard exit for containment: wrong types and unsafe
tmp-sink paths print to stderr and ``sys.exit(1)``. Structure/path checks run
even when ``enabled: false`` so a later opt-in never surfaces a dormant
misconfiguration.

Run: python -m pytest tests/test_repo_containment_validate.py -v
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import _validate_repo_containment
from lib.repo_containment import tmp_sink_path_error


def _config_path(tmp_path: Path) -> Path:
    path = tmp_path / ".meta-config" / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _validate(config: dict, tmp_path: Path):
    return _validate_repo_containment(config, _config_path(tmp_path))


# --- Happy path --------------------------------------------------------


def test_absent_block_is_valid(tmp_path):
    _validate({}, tmp_path)


def test_valid_full_block_is_accepted(tmp_path):
    _validate(
        {
            "repo_containment": {
                "enabled": True,
                "provider-overrides": {"Claude": {"enabled": False}},
                "tmp-sink": {
                    "enabled": True,
                    "path": "scratch/tmp",
                    "gitignore": True,
                    "cleanup": "on-sync",
                },
            }
        },
        tmp_path,
    )


# --- 1. block mapping --------------------------------------------------


def test_non_mapping_block_fails(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate({"repo_containment": "yes"}, tmp_path)
    assert exc.value.code == 1
    assert "expected a mapping" in capsys.readouterr().err


# --- 2. enabled type ---------------------------------------------------


@pytest.mark.parametrize("value", ["true", "false", 1, 0, None])
def test_non_boolean_enabled_is_rejected(tmp_path, capsys, value):
    with pytest.raises(SystemExit) as exc:
        _validate({"repo_containment": {"enabled": value}}, tmp_path)
    assert exc.value.code == 1
    assert "repo_containment.enabled" in capsys.readouterr().err


# --- 3. provider-overrides ---------------------------------------------


def test_non_mapping_provider_overrides_is_rejected(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"repo_containment": {"provider-overrides": ["Claude"]}}, tmp_path
        )
    assert exc.value.code == 1
    assert "provider-overrides" in capsys.readouterr().err


def test_unknown_provider_override_is_rejected(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {
                "repo_containment": {
                    "provider-overrides": {"Definitely-Not-A-Provider": {}}
                }
            },
            tmp_path,
        )
    assert exc.value.code == 1
    assert "unknown provider" in capsys.readouterr().err


def test_non_mapping_provider_override_entry_is_rejected(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"repo_containment": {"provider-overrides": {"Claude": "off"}}},
            tmp_path,
        )
    assert exc.value.code == 1
    assert "provider-overrides.Claude" in capsys.readouterr().err


def test_non_boolean_provider_override_enabled_is_rejected(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {
                "repo_containment": {
                    "provider-overrides": {"Claude": {"enabled": "yes"}}
                }
            },
            tmp_path,
        )
    assert exc.value.code == 1
    assert "provider-overrides.Claude.enabled" in capsys.readouterr().err


# --- 4. tmp-sink structure & path --------------------------------------


def test_non_mapping_tmp_sink_is_rejected(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate({"repo_containment": {"tmp-sink": ".tmp"}}, tmp_path)
    assert exc.value.code == 1
    assert "tmp-sink" in capsys.readouterr().err


@pytest.mark.parametrize("key", ["enabled", "gitignore"])
def test_non_boolean_tmp_sink_flags_are_rejected(tmp_path, capsys, key):
    with pytest.raises(SystemExit) as exc:
        _validate({"repo_containment": {"tmp-sink": {key: "on"}}}, tmp_path)
    assert exc.value.code == 1
    assert f"tmp-sink.{key}" in capsys.readouterr().err


def test_unknown_cleanup_mode_is_rejected(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"repo_containment": {"tmp-sink": {"cleanup": "later"}}}, tmp_path
        )
    assert exc.value.code == 1
    assert "cleanup" in capsys.readouterr().err


@pytest.mark.parametrize(
    "path",
    ["/absolute/tmp", "..", "../escape", "a/../../escape", "", "   ", "."],
)
def test_unsafe_tmp_sink_paths_are_rejected(tmp_path, capsys, path):
    with pytest.raises(SystemExit) as exc:
        _validate({"repo_containment": {"tmp-sink": {"path": path}}}, tmp_path)
    assert exc.value.code == 1
    assert "tmp-sink.path" in capsys.readouterr().err


# --- Structure checks always run (even when disabled) ------------------


def test_path_checks_still_run_when_disabled(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {
                "repo_containment": {
                    "enabled": False,
                    "tmp-sink": {"path": "/absolute/tmp"},
                }
            },
            tmp_path,
        )
    assert exc.value.code == 1
    assert "tmp-sink.path" in capsys.readouterr().err


def test_type_checks_still_run_when_disabled(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        _validate(
            {"repo_containment": {"enabled": False, "provider-overrides": "x"}},
            tmp_path,
        )
    assert exc.value.code == 1
    assert "provider-overrides" in capsys.readouterr().err


def test_disabled_with_valid_structure_is_accepted(tmp_path):
    _validate(
        {
            "repo_containment": {
                "enabled": False,
                "tmp-sink": {"enabled": False, "cleanup": "manual"},
            }
        },
        tmp_path,
    )


def test_relative_project_root_is_resolved_consistently(tmp_path, monkeypatch):
    """A relative ``project_root`` (e.g. ``"."``) must not be a false escape.

    ``os.path.commonpath([".", ".tmp"])`` returns ``""``, which the old check
    compared against ``"."`` and rejected. Both sides are now resolved with
    ``abspath`` first, so a valid relative root + relative sink passes.
    """
    monkeypatch.chdir(tmp_path)
    assert tmp_sink_path_error(".tmp", ".") is None
    assert tmp_sink_path_error("scratch/x", ".") is None
    assert tmp_sink_path_error(".tmp", Path(".")) is None


@pytest.mark.parametrize("path", ["../escape", "/absolute/tmp", "..", "."])
def test_relative_project_root_still_rejects_unsafe_paths(path):
    assert tmp_sink_path_error(path, ".") is not None


@pytest.mark.parametrize("path", ["C:\\Users\\x", "c:/tmp", "D:", "Z:/scratch"])
def test_windows_drive_letter_paths_are_rejected(path):
    """Drive-letter absolutes are invalid on POSIX too (matching the UI rule).

    ``os.path.isabs("C:\\x")`` is ``False`` on POSIX, so without an explicit
    ``^[A-Za-z]:`` check such a path slipped through as "relative".
    """
    assert tmp_sink_path_error(path) is not None
    assert "drive-letter" in tmp_sink_path_error(path)


def test_unreadable_registry_warns_but_does_not_fail(tmp_path, capsys, monkeypatch):
    """A degraded provider registry must be visible, not silently skipped.

    On OSError the registry becomes ``[]`` and ``if known and ...`` skips the
    unknown-provider check. The validator now prints a WARNING (stderr) while
    still accepting the block — the normal ``--validate`` path is unaffected.
    """
    import lib.config as config_module

    def _boom(_root):
        raise OSError("registry unavailable")

    monkeypatch.setattr(config_module, "registered_provider_names", _boom)

    # Must not raise SystemExit for a provider that might be a typo.
    _validate(
        {"repo_containment": {"provider-overrides": {"Typo-Provider": {}}}},
        tmp_path,
    )
    err = capsys.readouterr().err
    assert "WARNING" in err
    assert "provider registry could not be read" in err
