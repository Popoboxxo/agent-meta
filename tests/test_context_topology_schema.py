"""Schema tests for the ``context_file`` topology keys.

SPEC-CONTEXT-FILE-MODES-2026-09-13 (AC-11):

- ``context_file.topology`` is a string enum (``unified``/``per-provider``)
  with default ``unified``; it is a sibling of the density ``mode`` key, not the
  same axis.
- ``context_file.core_file`` is a string with default ``AGENTS.md``.
- ``context_file.provider-overrides.<Provider>.topology`` is a nested enum.
- The ``context_file`` block stays closed (``additionalProperties: false``), so
  unknown sub-keys are rejected.
- Absence of the topology keys is valid and resolves to ``unified``.

Run: python -m pytest tests/test_context_topology_schema.py -v
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

jsonschema = pytest.importorskip("jsonschema")

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCHEMA_PATH = _REPO_ROOT / "config" / "project-config.schema.json"


def _schema() -> dict:
    with _SCHEMA_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _config(**extra) -> dict:
    base = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
    }
    base.update(extra)
    return base


def _context_file_schema() -> dict:
    return _schema()["properties"]["context_file"]


def test_topology_enum_accepted():
    jsonschema.validate(
        _config(context_file={
            "topology": "per-provider",
            "core_file": "AGENTS.md",
            "provider-overrides": {"Gemini": {"topology": "unified"}},
        }),
        _schema(),
    )


@pytest.mark.parametrize("value", ["unified", "per-provider"])
def test_topology_each_enum_value_accepted(value):
    jsonschema.validate(_config(context_file={"topology": value}), _schema())


def test_topology_out_of_enum_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(context_file={"topology": "garbage"}), _schema()
        )


def test_topology_non_string_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(context_file={"topology": 1}), _schema())


def test_topology_unknown_subkey_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(context_file={"topology": "unified", "bogus": 1}), _schema()
        )


def test_core_file_non_string_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(_config(context_file={"core_file": 1}), _schema())


def test_provider_overrides_unknown_subkey_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(context_file={
                "provider-overrides": {"Gemini": {"topology": "unified", "x": 1}}
            }),
            _schema(),
        )


def test_provider_overrides_out_of_enum_rejected():
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            _config(context_file={
                "provider-overrides": {"Gemini": {"topology": "garbage"}}
            }),
            _schema(),
        )


def test_absence_resolves_unified():
    jsonschema.validate(_config(context_file={}), _schema())
    props = _context_file_schema()["properties"]
    assert props["topology"]["enum"] == ["unified", "per-provider"]
    assert props["topology"]["default"] == "unified"
    assert props["core_file"]["default"] == "AGENTS.md"
    assert _context_file_schema()["additionalProperties"] is False


def _fill_defaults_roundtrip(tmp_path: Path, body: str) -> dict:
    import sys

    import yaml

    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from lib.config import fill_defaults
    from lib.log import SyncLog

    config_path = tmp_path / "project.yaml"
    config_path.write_text(body, encoding="utf-8")
    fill_defaults(config_path, _REPO_ROOT, SyncLog(), dry_run=False)
    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def test_fill_defaults_does_not_persist_topology_default(tmp_path: Path):
    """IC-12: a missing key stays absent — the safe-side ``unified`` default is
    virtual (schema ``default`` + ``context_topology()`` fail-safe), never
    materialised into user config. Existing projects stay byte-identical."""
    reloaded = _fill_defaults_roundtrip(
        tmp_path,
        "project:\n  name: t\n  prefix: t\n  short: t\n"
        "ai-providers:\n  - Claude\n",
    )
    assert "context_file" not in reloaded or "topology" not in reloaded.get(
        "context_file", {}
    ), "fill_defaults must not write context_file.topology"


def test_fill_defaults_keeps_explicit_topology(tmp_path: Path):
    """IC-12: an explicit value is never overwritten (the block is untouched)."""
    reloaded = _fill_defaults_roundtrip(
        tmp_path,
        "project:\n  name: t\n  prefix: t\n  short: t\n"
        "ai-providers:\n  - Claude\n"
        "context_file:\n  topology: per-provider\n",
    )
    assert reloaded["context_file"]["topology"] == "per-provider"
