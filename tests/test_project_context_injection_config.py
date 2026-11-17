"""Tests for the project-context-injection config surface (issue #1187).

Shared across T1-T3 and T14. Test groups are kept clearly separated by
section comments so later tasks can append their own tests without touching
the schema tests below.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "config" / "project-config.schema.json"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.config import (  # noqa: E402  (path setup must precede local imports)
    PROJECT_CONTEXT_MODES,
    _PROJECT_CONTEXT_POINTER_TEXTS,
    build_variables,
    format_project_context_pointer,
    resolve_project_context_scope,
)
from lib.io import SyncError  # noqa: E402


def _schema():
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _base_config(**extra):
    cfg = {
        "project": {"name": "test", "prefix": "tst", "short": "test"},
        "platforms": [],
    }
    cfg.update(extra)
    return cfg


def _validator():
    jsonschema = pytest.importorskip("jsonschema")
    return jsonschema.Draft7Validator(_schema())


# ---------------------------------------------------------------------------
# T1 — schema section `project-context-injection`
# ---------------------------------------------------------------------------


def test_schema_section_accepts_all_four_modes():
    validator = _validator()
    for mode in ("all", "core+orchestrator", "core+whitelist", "core"):
        config = _base_config(**{
            "project-context-injection": {"mode": mode},
        })
        assert validator.is_valid(config), f"mode {mode!r} should be valid"


def test_schema_section_rejects_unknown_key():
    validator = _validator()
    config = _base_config(**{
        "project-context-injection": {"enabled": True},
    })
    assert not validator.is_valid(config)


def test_schema_section_rejects_duplicate_and_nonstring_whitelist():
    validator = _validator()
    for whitelist in (["developer", "developer"], [1]):
        config = _base_config(**{
            "project-context-injection": {"whitelist": whitelist},
        })
        assert not validator.is_valid(config), f"whitelist {whitelist!r} should be invalid"


def test_schema_defaults_are_mode_whitelist_orchestrator_pointer_language():
    props = _schema()["properties"]["project-context-injection"]["properties"]
    assert props["mode"]["default"] == "all"
    assert props["whitelist"]["default"] == []
    assert props["orchestrator"]["default"] == "inherit"
    assert props["pointer-language"]["default"] == "en"


def test_schema_orchestrator_roles_and_pointer_text_have_no_default():
    props = _schema()["properties"]["project-context-injection"]["properties"]
    assert "default" not in props["orchestrator-roles"]
    assert "default" not in props["pointer-text"]


def test_schema_section_accepts_orchestrator_roles_and_pointer_settings():
    validator = _validator()
    valid = _base_config(**{
        "project-context-injection": {
            "orchestrator-roles": ["orchestrator", "senior-developer"],
            "pointer-language": "de",
            "pointer-text": "Projektkontext: lies `{context_file}`.",
        },
    })
    assert validator.is_valid(valid)
    for roles in (["senior-developer", "senior-developer"], [1]):
        invalid = _base_config(**{
            "project-context-injection": {"orchestrator-roles": roles},
        })
        assert not validator.is_valid(invalid), f"roles {roles!r} should be invalid"


def test_schema_rejects_unknown_pointer_language_and_empty_pointer_text():
    validator = _validator()
    for section in (
        {"pointer-language": "fr"},
        {"pointer-text": ""},
    ):
        config = _base_config(**{"project-context-injection": section})
        assert not validator.is_valid(config), f"section {section!r} should be invalid"


# ---------------------------------------------------------------------------
# T2 — resolver (`resolve_project_context_scope`, `format_project_context_pointer`)
# ---------------------------------------------------------------------------

# Char-exact copies of spec §3.2/§3.2.1 — independent of the production dict so
# a silent edit to the default texts breaks a test instead of drifting through.
_EN_POINTER_TEXT = (
    "Project context: read `{context_file}` first — it is the single source for "
    "project-specific facts (embedded here only when "
    "`project-context-injection.mode` includes this role)."
)
_DE_POINTER_TEXT = (
    "Projektkontext: lies zuerst `{context_file}` — sie ist die einzige Quelle für "
    "projektspezifische Fakten (hier nur eingebettet, wenn "
    "`project-context-injection.mode` diese Rolle einschließt)."
)


def test_scope_absent_config_defaults_to_all():
    # Must not raise: derive_builder_vars calls build_variables({}, ...).
    scope = resolve_project_context_scope({}, REPO_ROOT)
    assert scope["mode"] == "all"
    assert scope["whitelist"] == []
    assert scope["orchestrator"] == "inherit"
    assert scope["orchestrator_roles"] == ("orchestrator",)
    assert scope["pointer_language"] == "en"
    assert scope["pointer_text"] == _EN_POINTER_TEXT
    assert scope["pointer_text"] == _PROJECT_CONTEXT_POINTER_TEXTS["en"]
    assert scope["present"] is False


def test_scope_null_section_is_all():
    scope = resolve_project_context_scope(
        {"project-context-injection": None}, REPO_ROOT)
    assert scope["mode"] == "all"
    assert scope["present"] is False


def test_scope_unknown_mode_raises_sync_error():
    for mode in PROJECT_CONTEXT_MODES:
        scope = resolve_project_context_scope(
            {"project-context-injection": {"mode": mode}}, REPO_ROOT)
        assert scope["mode"] == mode
    with pytest.raises(SyncError, match="mode-unknown") as exc_info:
        resolve_project_context_scope(
            {"project-context-injection": {"mode": "slim"}}, REPO_ROOT)
    assert "slim" in str(exc_info.value)


def test_scope_unknown_orchestrator_value_raises():
    with pytest.raises(SyncError, match="orchestrator-unknown") as exc_info:
        resolve_project_context_scope(
            {"project-context-injection": {"orchestrator": "sometimes"}}, REPO_ROOT)
    assert "sometimes" in str(exc_info.value)


def test_scope_whitelist_unknown_role_lists_all_names():
    with pytest.raises(SyncError) as exc_info:
        resolve_project_context_scope(
            {"project-context-injection": {
                "whitelist": ["developer", "nope", "nada"]}}, REPO_ROOT)
    message = str(exc_info.value)
    assert "whitelist-unknown-role" in message
    assert "nope" in message and "nada" in message
    assert message.index("nada") < message.index("nope")  # sorted alphabetically


def test_scope_whitelist_known_roles_accepted():
    warnings: list[str] = []
    scope = resolve_project_context_scope(
        {"project-context-injection": {"whitelist": ["developer", "planner"]}},
        REPO_ROOT, warn_sink=warnings)
    assert scope["whitelist"] == ["developer", "planner"]
    assert warnings == []


@pytest.mark.parametrize("registry, ai_providers, expected", [
    ({"Claude": {}}, None, ("orchestrator",)),
    ({"Claude": {}, "Lead": {"primary-role": "lead"}},
     ["Claude", "Lead"], ("lead", "orchestrator")),
    ({"Alpha": {}, "Beta": {"primary-role": "orchestrator"}},
     ["Alpha", "Beta"], ("orchestrator",)),
])
def test_scope_orchestrator_roles_default_per_provider_set(
        registry, ai_providers, expected):
    config = {}
    if ai_providers is not None:
        config["ai-providers"] = ai_providers
    scope = resolve_project_context_scope(
        config, REPO_ROOT, provider_config=registry)
    assert scope["orchestrator_roles"] == expected


def test_scope_orchestrator_roles_override_replaces_default():
    scope = resolve_project_context_scope(
        {"project-context-injection": {"orchestrator-roles": ["senior-developer"]}},
        REPO_ROOT)
    assert scope["orchestrator_roles"] == ("senior-developer",)
    assert "orchestrator" not in scope["orchestrator_roles"]


def test_scope_empty_orchestrator_roles_allowed():
    scope = resolve_project_context_scope(
        {"project-context-injection": {"orchestrator-roles": []}}, REPO_ROOT)
    assert scope["orchestrator_roles"] == ()


def test_scope_orchestrator_roles_unknown_lists_all_names():
    with pytest.raises(SyncError) as exc_info:
        resolve_project_context_scope(
            {"project-context-injection": {
                "orchestrator-roles": ["senior-developer", "nope", "nada"]}},
            REPO_ROOT)
    message = str(exc_info.value)
    assert "orchestrator-roles-unknown" in message
    assert "nope" in message and "nada" in message
    assert "whitelist" not in message  # distinct error code, no cross-talk


def test_scope_all_plus_exclude_warns_not_raises():
    warnings: list[str] = []
    resolve_project_context_scope(
        {"project-context-injection": {"mode": "all", "orchestrator": "exclude"}},
        REPO_ROOT, warn_sink=warnings)
    assert warnings == [
        "project-context-injection.exclude-overrides-mode: mode=all + "
        "orchestrator=exclude — orchestrator roles (orchestrator) excluded; "
        "exclude wins"
    ]


def test_scope_core_orchestrator_plus_exclude_warns_and_degrades():
    warnings: list[str] = []
    resolve_project_context_scope(
        {"project-context-injection": {
            "mode": "core+orchestrator", "orchestrator": "exclude"}},
        REPO_ROOT, warn_sink=warnings)
    assert warnings == [
        "project-context-injection.exclude-overrides-mode: "
        "mode=core+orchestrator + orchestrator=exclude — "
        "orchestrator roles (orchestrator) excluded; exclude wins"
    ]


def test_scope_core_plus_exclude_stays_silent():
    warnings: list[str] = []
    resolve_project_context_scope(
        {"project-context-injection": {"mode": "core", "orchestrator": "exclude"}},
        REPO_ROOT, warn_sink=warnings)
    assert warnings == []


def test_scope_empty_set_with_core_orchestrator_warns():
    warnings: list[str] = []
    resolve_project_context_scope(
        {"project-context-injection": {
            "mode": "core+orchestrator", "orchestrator": "inherit",
            "orchestrator-roles": []}},
        REPO_ROOT, warn_sink=warnings)
    assert warnings == [
        "project-context-injection.empty-orchestrator-set: "
        "mode=core+orchestrator + orchestrator-roles=[] — "
        "no role receives the block (mode degenerates to core)"
    ]


def test_exclude_and_empty_set_warn_once():
    warnings: list[str] = []
    resolve_project_context_scope(
        {"project-context-injection": {
            "mode": "core+orchestrator", "orchestrator": "exclude",
            "orchestrator-roles": []}},
        REPO_ROOT, warn_sink=warnings)
    assert len(warnings) == 1  # exclude-overrides-mode wins over empty-orchestrator-set
    assert warnings[0].startswith("project-context-injection.exclude-overrides-mode:")
    assert "orchestrator roles (none) excluded" in warnings[0]


def test_pointer_language_defaults_to_en():
    scope = resolve_project_context_scope({}, REPO_ROOT)
    assert scope["pointer_language"] == "en"
    assert scope["pointer_text"] == _EN_POINTER_TEXT
    assert "{context_file}" in scope["pointer_text"]
    assert "\n" not in scope["pointer_text"]


def test_pointer_language_de_selects_german_default():
    scope = resolve_project_context_scope(
        {"project-context-injection": {"pointer-language": "de"}}, REPO_ROOT)
    assert scope["pointer_language"] == "de"
    assert scope["pointer_text"] == _DE_POINTER_TEXT
    assert scope["pointer_text"].count("{context_file}") == 1


@pytest.mark.parametrize("language, expected", [
    ("Deutsch", "de"), ("de", "de"), ("German", "de"),
    ("  gErMaN ", "de"),
    ("English", "en"), ("en", "en"), (" ENglisch ", "en"),
])
def test_pointer_language_project_derives_from_communication_language(
        language, expected):
    scope = resolve_project_context_scope(
        {"project-context-injection": {"pointer-language": "project"}},
        REPO_ROOT, communication_language=language)
    assert scope["pointer_language"] == expected
    assert scope["pointer_text"] == _PROJECT_CONTEXT_POINTER_TEXTS[expected]


def test_pointer_language_project_unknown_falls_back_with_warn():
    warnings: list[str] = []
    scope = resolve_project_context_scope(
        {"project-context-injection": {"pointer-language": "project"}},
        REPO_ROOT, communication_language="Klingonisch", warn_sink=warnings)
    assert scope["pointer_language"] == "en"
    assert scope["pointer_text"] == _EN_POINTER_TEXT
    assert warnings == [
        "project-context-injection.pointer-language-fallback: "
        "COMMUNICATION_LANGUAGE='Klingonisch' has no pointer text — "
        "falling back to 'en'"
    ]


def test_pointer_text_override_wins_over_language():
    override = "See `{context_file}`."
    scope = resolve_project_context_scope(
        {"project-context-injection": {
            "pointer-language": "de", "pointer-text": override}}, REPO_ROOT)
    assert scope["pointer_text"] == override
    assert scope["pointer_text"] != _DE_POINTER_TEXT


def test_pointer_text_unknown_token_raises():
    with pytest.raises(SyncError) as exc_info:
        resolve_project_context_scope(
            {"project-context-injection": {
                "pointer-text": "Read {context_file} and {mode}."}}, REPO_ROOT)
    message = str(exc_info.value)
    assert "pointer-text-unknown-token" in message
    assert "{mode}" in message


@pytest.mark.parametrize("text", [
    "Read the project file.",
    "{context_file} / {context_file}",
])
def test_pointer_text_requires_exactly_one_context_file_token(text):
    with pytest.raises(SyncError, match="pointer-text-context-file-count"):
        resolve_project_context_scope(
            {"project-context-injection": {"pointer-text": text}}, REPO_ROOT)


def test_pointer_text_multiline_raises():
    with pytest.raises(SyncError, match="pointer-text-multiline"):
        resolve_project_context_scope(
            {"project-context-injection": {
                "pointer-text": "Read {context_file}\nfirst."}}, REPO_ROOT)


def test_format_project_context_pointer_substitutes_token():
    assert format_project_context_pointer(
        "Read `{context_file}`.", "AGENTS.md") == "Read `AGENTS.md`."


def test_build_variables_exposes_mode():
    variables, _ = build_variables(
        {"project-context-injection": {"mode": "core"}}, REPO_ROOT)
    assert variables["PROJECT_CONTEXT_MODE"] == "core"
    scope = variables["_PROJECT_CONTEXT_SCOPE"]
    assert scope["mode"] == "core"
    assert "pointer_text" in scope
    assert "orchestrator_roles" in scope


# ---------------------------------------------------------------------------
# T3 — diagnose variables (D-5) + conditional whitelist
# ---------------------------------------------------------------------------


def test_builtin_vars_contain_project_context_flags():
    from lib.consistency.placeholders import _BUILTIN_VARS

    assert "PROJECT_CONTEXT_INJECTED" in _BUILTIN_VARS
    assert "PROJECT_CONTEXT_MODE" in _BUILTIN_VARS


def test_builtin_known_set_has_no_project_context_findings():
    from lib.consistency.placeholders import check_builder_known_set

    assert [
        f for f in check_builder_known_set(REPO_ROOT) if "PROJECT_CONTEXT" in f.message
    ] == []


def test_conditional_strip_removes_inactive_project_context_branch():
    from lib.variables import strip_inactive_conditional_blocks as strip

    template = "A{{#if PROJECT_CONTEXT_INJECTED}}X{{else}}Y{{/if}}B"
    # Inactive: only the {{else}} branch survives.
    assert strip(template, {"PROJECT_CONTEXT_INJECTED": "false"}) == "AYB"
    # Active: only the {{#if}} branch survives.
    assert strip(template, {"PROJECT_CONTEXT_INJECTED": "true"}) == "AXB"


def test_standalone_flags_default_to_all():
    from lib.standalone import _CONDITIONAL_FALSE_FLAGS

    assert _CONDITIONAL_FALSE_FLAGS["PROJECT_CONTEXT_INJECTED"] == "true"
    assert _CONDITIONAL_FALSE_FLAGS["PROJECT_CONTEXT_MODE"] == "all"
