"""Schema tests for the Opencode v2 project options (Task 4 / B.1).

Spec: ``docs/specs/2026-10-22-opencode-v2-support-spec.md`` §3.1
(``SPEC-OPENCODE-V2-SUPPORT-2026-10-22``), Amendment B1 (2026-10-23).
Plan: ``docs/plans/2026-10-22-opencode-v2-support-plan.md``, Task 4.

Covers the schema part of AC-D3: the new keys
``experimental-subagent-depth``, ``experimental-todo``, ``providers``,
``model-variants`` and ``cli`` are accepted under
``provider-options.Opencode`` and keep the block closed.

Amendment B1 removes ``small-model`` (``agents.title.model`` is UNVERIFIED),
therefore the block must reject it as an unknown key. Per the plan there is no
dedicated small-model test any more, so that guard lives in
``test_unknown_key_rejected``.

MCP connection keys (Task 14 / C2.1, AC-C8/AC-C9 schema part): both MCP
``connection`` objects — the deprecated ``mcp-registry`` shape and the inline
``plugin-catalog`` shape — must declare ``timeout`` (``catalog``/``execution``
plus the Amendment-B1 ``startup``), ``oauth`` (snake_case ``client_id``,
``client_secret``, ``scope``) and ``disabled``. ``timeout``/``oauth`` are
closed: the documented-but-unsupported v2 oauth keys
(``callback_port``, ``redirect_uri``, ``auth_server_metadata_url``) and
``oauth: false`` are rejected visibly instead of being silently dropped.
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


def _config(**provider_options) -> dict:
    """Minimal valid project config with the given Opencode provider options."""
    return {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Opencode"],
        "provider-options": {"Opencode": dict(provider_options)},
    }


def _validate(**provider_options) -> None:
    jsonschema.validate(_config(**provider_options), _schema())


def _opencode_properties() -> dict:
    props = _schema()["properties"]["provider-options"]["properties"]["Opencode"]
    return props


def test_valid_v2_configuration_accepted():
    """All five new keys, in their documented shape, validate."""
    _validate(
        **{
            "surface-version": "v2",
            "experimental-subagent-depth": 2,
            "experimental-todo": True,
            "providers": {
                "opencode-go": {
                    "name": "opencode-go",
                    "env": ["OC_API_KEY"],
                    "settings": {"baseURL": "https://example.invalid/v1"},
                }
            },
            "model-variants": {"developer": "high"},
            "cli": {"plugins": ["example-plugin"]},
        }
    )


def test_model_variant_with_space_rejected():
    """AC-D3: a variant is appended as ``#variant`` — blanks are not allowed."""
    with pytest.raises(jsonschema.ValidationError):
        _validate(**{"model-variants": {"developer": "hi gh"}})


def test_subagent_depth_zero_rejected():
    with pytest.raises(jsonschema.ValidationError):
        _validate(**{"experimental-subagent-depth": 0})


def test_provider_id_with_dot_rejected():
    """``providers`` is keyed by provider id; a dot is not a valid id."""
    with pytest.raises(jsonschema.ValidationError):
        _validate(**{"providers": {"a.b": {}}})


def test_unknown_key_rejected():
    """``additionalProperties: false`` stays — ``foo`` and the removed
    ``small-model`` (Amendment B1) are both unknown keys."""
    assert "small-model" not in _opencode_properties()["properties"]
    for key, value in (("foo", True), ("small-model", "deepseek")):
        with pytest.raises(jsonschema.ValidationError):
            _validate(**{key: value})


# --- MCP connection keys (Task 14 / C2.1) ------------------------------------
#
# Both MCP connection objects are open at the connection level by design
# (``additionalProperties`` is deliberately left unset there, so unrelated
# connection passthrough keys keep working). That means whole-config validation
# alone cannot prove that ``timeout``/``oauth``/``disabled`` are *declared* --
# an undeclared key would validate just as well. The acceptance test therefore
# asserts the declarations explicitly and the rejection tests exercise the
# declared sub-objects through the real top-level schema.


def _connection_schemas() -> list[dict]:
    """The two MCP ``connection`` schemas: project (mcp-registry) and inline."""
    schema = _schema()
    project_conn = (
        schema["properties"]["mcp-registry"]["patternProperties"]
        ["^[a-zA-Z0-9_-]+$"]["properties"]["connection"]
    )
    inline_conn = (
        schema["properties"]["plugin-catalog"]["properties"]["plugins"]
        ["patternProperties"]["^[a-zA-Z0-9_-]+$"]["properties"]["connection"]
    )
    return [project_conn, inline_conn]


def _config_with_connection(connection: dict) -> dict:
    """Config that uses the connection in both supported placements at once."""
    return {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Opencode"],
        "mcp-registry": {"srv": {"connection": dict(connection)}},
        "plugin-catalog": {
            "plugins": {"srv": {"kind": "mcp-server", "connection": dict(connection)}}
        },
    }


def test_connection_timeout_oauth_disabled_accepted():
    """AC-C8/AC-C9: the documented combination validates in both placements and
    the three keys are actually declared (not merely tolerated as unknown)."""
    connection = {
        "type": "http",
        "url": "https://example.invalid/mcp",
        "timeout": {"startup": 1000, "catalog": 5000, "execution": 60000},
        "oauth": {"client_id": "id", "client_secret": "{env:MCP_SECRET}", "scope": "read"},
        "disabled": True,
    }
    jsonschema.validate(_config_with_connection(connection), _schema())

    for conn in _connection_schemas():
        props = conn["properties"]
        for key in ("timeout", "oauth", "disabled"):
            assert key in props, f"connection.{key} is not declared"
        timeout = props["timeout"]
        assert timeout["type"] == "object"
        assert timeout["additionalProperties"] is False
        for key in ("startup", "catalog", "execution"):
            assert timeout["properties"][key]["type"] == "integer"
            assert timeout["properties"][key]["minimum"] == 1
        oauth = props["oauth"]
        assert oauth["type"] == "object"
        assert oauth["additionalProperties"] is False
        for key in ("client_id", "client_secret", "scope"):
            assert oauth["properties"][key]["type"] == "string"
        assert props["disabled"]["type"] == "boolean"


def test_connection_timeout_non_integer_rejected():
    """``timeout.catalog`` is milliseconds — a string must not validate."""
    with pytest.raises(jsonschema.ValidationError) as excinfo:
        jsonschema.validate(
            _config_with_connection({"timeout": {"catalog": "5"}}), _schema()
        )
    assert "catalog" in str(excinfo.value)


def test_connection_oauth_camel_case_rejected():
    """``oauth`` is snake_case only; documented-but-unsupported keys and
    ``oauth: false`` fail visibly instead of being silently dropped."""
    for oauth in (
        {"clientId": "x"},
        {"clientSecret": "x"},
        {"redirect_uri": "https://example.invalid/cb"},
        {"callback_port": 4711},
        {"auth_server_metadata_url": "https://example.invalid/.well-known"},
        False,
    ):
        with pytest.raises(jsonschema.ValidationError) as excinfo:
            jsonschema.validate(_config_with_connection({"oauth": oauth}), _schema())
        message = str(excinfo.value)
        assert len(message) > 20, message  # readable, not a bare assertion
        if isinstance(oauth, dict):
            assert next(iter(oauth)) in message


def test_connection_without_new_keys_still_valid():
    """The new keys stay optional — existing connections validate unchanged."""
    jsonschema.validate(
        _config_with_connection({"type": "stdio", "command": "npx", "args": ["-y", "x"]}),
        _schema(),
    )
    for conn in _connection_schemas():
        required = set(conn.get("required", []))
        assert not required & {"timeout", "oauth", "disabled"}
