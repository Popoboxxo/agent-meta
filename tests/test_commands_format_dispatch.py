"""MB-5 / REQ-PROV-01: commands format dispatch is a data-driven table lookup.

``sync_commands_for_provider`` must not branch on ``commands_format`` with an
if/elif chain. The declared ``commands_format`` value from
config/ai-providers.yaml is looked up in ``COMMAND_FORMAT_TRANSFORMS`` — the
key is a config value, never a provider name. This module pins:

1. the table is the complete supported key set,
2. every format declared in the provider registry has a transform,
3. an unknown key fails loudly with the list of valid keys (and before any
   file is written),
4. the output per format is byte-identical to the documented contract
   (markdown = unchanged, continue = ``invokable: true``, toml = converted),
5. the same key produces identical bytes for different provider names,
6. no if/elif format chain is left in the dispatch function.
"""
from __future__ import annotations

import ast
import inspect
import shutil
from pathlib import Path

import pytest
import yaml

from scripts.lib.commands import (
    COMMAND_FORMAT_TRANSFORMS,
    _command_transform,
    sync_commands_for_provider,
)
from scripts.lib.io import SyncError
from scripts.lib.log import SyncLog

_REPO_ROOT = Path(__file__).resolve().parent.parent
_COMMANDS_MODULE = _REPO_ROOT / "scripts" / "lib" / "commands.py"

#: Synthetic command source without placeholders or ``requires_roles`` so the
#: expected output is a pure function of the format transform.
_SOURCE = (
    "---\n"
    "description: Demo command\n"
    'allowed-tools: ["Agent"]\n'
    "---\n"
    "\n"
    "# Demo\n"
    "\n"
    "Do $ARGUMENTS now.\n"
)

#: ``commands_format: continue`` — ``invokable: true`` injected into frontmatter.
_CONTINUE_EXPECTED = (
    "---\n"
    "description: Demo command\n"
    'allowed-tools: ["Agent"]\n'
    "invokable: true\n"
    "---\n"
    "\n"
    "# Demo\n"
    "\n"
    "Do $ARGUMENTS now.\n"
)

#: ``commands_format: toml`` — description + prompt block, ``{{args}}`` syntax.
_TOML_EXPECTED = (
    'description = "Demo command"\n'
    'prompt = """\n'
    "# Demo\n"
    "\n"
    "Do {{args}} now.\n"
    '"""\n'
)

#: format key -> (output extension, expected file content).
_FORMATS = {
    "markdown": (".md", _SOURCE),
    "continue": (".md", _CONTINUE_EXPECTED),
    "toml": (".toml", _TOML_EXPECTED),
}


def _fake_root(tmp_path: Path) -> Path:
    """An agent-meta root carrying one synthetic command source + the config."""
    root = tmp_path / "agent-meta"
    shutil.copytree(_REPO_ROOT / "config", root / "config")
    generic = root / "commands" / "1-generic"
    generic.mkdir(parents=True)
    (generic / "demo-cmd.md").write_text(_SOURCE, encoding="utf-8")
    return root


def _sync(root: Path, project: Path, provider: str, fmt: str, ext: str) -> Path:
    """Sync the synthetic command for ``provider`` with the given format key."""
    sync_commands_for_provider(
        root, project, {}, SyncLog(), False, provider,
        provider_config={
            provider: {"commands_dir": "out", "commands_ext": ext, "commands_format": fmt},
        },
        variables={},
    )
    return project / "out"


# --- 1/2: the table is the dispatch surface --------------------------------


def test_dispatch_table_is_the_supported_format_set():
    assert set(COMMAND_FORMAT_TRANSFORMS) == {"markdown", "continue", "toml"}
    assert all(callable(transform) for transform in COMMAND_FORMAT_TRANSFORMS.values())


def test_every_declared_commands_format_has_a_transform():
    """A format value in the provider registry without a table entry would fail
    the sync at runtime — the table must cover the registry."""
    providers = yaml.safe_load(
        (_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
    )["providers"]
    declared = {
        pc.get("commands_format") for pc in providers.values() if pc.get("commands_format")
    }
    assert declared, "no commands_format declared in config/ai-providers.yaml"
    assert declared <= set(COMMAND_FORMAT_TRANSFORMS), declared - set(COMMAND_FORMAT_TRANSFORMS)


# --- 3: unknown key fails loudly, before any write -------------------------


def test_unknown_format_raises_with_valid_key_list():
    with pytest.raises(SyncError) as excinfo:
        _command_transform("bogus", "SomeProvider")
    message = str(excinfo.value)
    assert "'bogus'" in message
    for key in COMMAND_FORMAT_TRANSFORMS:
        assert key in message, (key, message)


def test_unknown_format_fails_before_writing_anything(tmp_path):
    root = _fake_root(tmp_path)
    project = tmp_path / "project"
    with pytest.raises(SyncError) as excinfo:
        _sync(root, project, "Claude", "bogus", ".md")
    assert "commands_format" in str(excinfo.value)
    assert not (project / "out").exists(), "unknown format must fail before mkdir/write"


# --- 4: byte-identical output per format ----------------------------------


@pytest.mark.parametrize("fmt", sorted(_FORMATS))
def test_output_is_byte_identical_to_the_format_contract(fmt, tmp_path):
    ext, expected = _FORMATS[fmt]
    root = _fake_root(tmp_path)
    out_dir = _sync(root, tmp_path / "project", "Claude", fmt, ext)
    written = out_dir / f"demo-cmd{ext}"
    assert written.read_bytes() == expected.encode("utf-8")


def test_markdown_transform_is_identity():
    assert COMMAND_FORMAT_TRANSFORMS["markdown"](_SOURCE, "demo-cmd") == _SOURCE


def test_continue_transform_is_idempotent():
    """An already invokable command must not gain a second ``invokable`` line."""
    transform = COMMAND_FORMAT_TRANSFORMS["continue"]
    once = transform(_SOURCE, "demo-cmd")
    assert once == _CONTINUE_EXPECTED
    assert transform(once, "demo-cmd") == once


# --- 5: the key alone selects the output, never the provider name ---------


def test_same_format_key_yields_identical_bytes_for_different_providers(tmp_path):
    root = _fake_root(tmp_path)
    first = _sync(root, tmp_path / "a", "Claude", "toml", ".toml") / "demo-cmd.toml"
    second = _sync(root, tmp_path / "b", "Copilot", "toml", ".toml") / "demo-cmd.toml"
    assert first.read_bytes() == second.read_bytes() == _TOML_EXPECTED.encode("utf-8")


# --- 6: no if/elif format chain left -------------------------------------


def _dispatch_function() -> ast.FunctionDef:
    tree = ast.parse(_COMMANDS_MODULE.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "sync_commands_for_provider":
            return node
    raise AssertionError("sync_commands_for_provider not found in commands.py")


def test_no_if_elif_commands_format_chain_in_dispatch():
    """The dispatch function must not compare against any format key literal —
    the format is selected by table lookup only (REQ-PROV-01)."""
    keys = set(COMMAND_FORMAT_TRANSFORMS)
    offenders: list[str] = []
    for node in ast.walk(_dispatch_function()):
        if not isinstance(node, ast.Compare):
            continue
        operands = [node.left, *node.comparators]
        matched = {
            operand.value
            for operand in operands
            if isinstance(operand, ast.Constant) and operand.value in keys
        }
        if matched:
            offenders.append(f"line {node.lineno}: {sorted(matched)}")
    assert not offenders, (
        "if/elif format chain reintroduced in sync_commands_for_provider — "
        "dispatch via COMMAND_FORMAT_TRANSFORMS:\n" + "\n".join(offenders)
    )


def test_dispatch_goes_through_the_table():
    """The dispatch function resolves its transform via ``_command_transform``
    (the table lookup) instead of rebuilding format logic inline."""
    calls = {
        node.func.id
        for node in ast.walk(_dispatch_function())
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_command_transform" in calls
    assert "COMMAND_FORMAT_TRANSFORMS[" in inspect.getsource(_command_transform)
