"""Schema validation for the ``auto_commit`` block (issue #1091).

Two layers are covered:

* ``auto_commit_violations`` / ``resolve_auto_commit_config`` (unit): an
  invalid block yields explicit violation messages and the resolver falls
  back to the fail-safe allowlist (``mode: off``, ``eligible_roles: []``).
* ``sync.py`` / ``sync.py --validate`` (subprocess e2e): a schema-invalid
  block fails validation with rc=1 while a normal sync stays rc=0 and writes
  the fail-safe allowlist plus a WARN -- no time-based grace.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.auto_commit import (
    authority_override_notices,
    authority_override_violations,
    auto_commit_violations,
    resolve_auto_commit_config,
)


def _grant(role):
    return {role: {"authority": "direct", "acknowledge_full_shell": True}}


_HOOKLESS_PC = {"Opencode": {"has_hooks": False, "hook_protocol": None}}
_HOOKED_PC = {
    "Claude": {"has_hooks": True, "hook_protocol": "claude-code-json"},
    "Opencode": {"has_hooks": False, "hook_protocol": None},
}


# --------------------------------------------------------------------------- #
# Unit: violation detection + fail-safe resolver                              #
# --------------------------------------------------------------------------- #


def test_valid_and_absent_blocks_have_no_violations():
    assert auto_commit_violations({}) == []
    assert auto_commit_violations({"auto_commit": None}) == []
    assert auto_commit_violations(
        {"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}}) == []
    assert auto_commit_violations(
        {"auto_commit": {"mode": "custom", "custom_script": "x.sh"}}) == []


def test_authority_overrides_key_is_known():
    cfg = {
        "auto_commit": {
            "mode": "auto",
            "triggers": ["task-boundary"],
            "authority_overrides": {
                "documenter": {"authority": "direct", "acknowledge_full_shell": True}
            },
        }
    }
    assert auto_commit_violations(cfg) == []


def test_triggers_with_mode_off_is_violation():
    v = auto_commit_violations(
        {"auto_commit": {"mode": "off", "triggers": ["task-boundary"]}})
    assert v == ["auto_commit.triggers is only valid with mode: auto"]


def test_custom_without_script_is_violation():
    msg = "auto_commit.custom_script is required for mode: custom or trigger: custom"
    assert auto_commit_violations({"auto_commit": {"mode": "custom"}}) == [msg]
    assert auto_commit_violations(
        {"auto_commit": {"mode": "auto", "triggers": ["custom"],
                         "custom_script": " "}}) == [msg]


def test_unknown_values_and_keys():
    v = auto_commit_violations(
        {"auto_commit": {"mode": "loose", "triggers": ["nope"], "bogus": 1,
                         "file_count_threshold": 0}})
    assert any("auto_commit.mode" in m for m in v)
    assert any("unknown value" in m and "nope" in m for m in v)
    assert any("bogus" in m for m in v)
    assert any("file_count_threshold" in m for m in v)


def test_resolve_fail_safe_on_violation():
    cfg = {"auto_commit": {"mode": "off", "triggers": ["task-boundary"]}}
    out = resolve_auto_commit_config(cfg, ["developer"], REPO_ROOT)
    assert out["mode"] == "off" and out["eligible_roles"] == [] and out["triggers"] == []


# --------------------------------------------------------------------------- #
# Validator/schema parity (advisory findings on PR #1118)                     #
# --------------------------------------------------------------------------- #


def test_duplicate_triggers_is_violation():
    # schema: triggers.uniqueItems = true
    v = auto_commit_violations(
        {"auto_commit": {"mode": "auto", "triggers": ["per-edit", "per-edit"]}})
    assert any("duplicate" in m and "per-edit" in m for m in v)


def test_non_bool_secret_scan_is_violation():
    v = auto_commit_violations(
        {"auto_commit": {"mode": "auto", "triggers": ["task-boundary"],
                         "secret_scan": "yes"}})
    assert any("secret_scan" in m and "boolean" in m for m in v)


def test_non_string_custom_script_is_violation():
    v = auto_commit_violations(
        {"auto_commit": {"mode": "auto", "triggers": ["task-boundary"],
                         "custom_script": 5}})
    assert any("custom_script" in m and "string" in m for m in v)


def test_integral_float_threshold_accepted():
    # JSON Schema calls 5.0 an integer; the stdlib validator must agree.
    cfg = {"auto_commit": {"mode": "auto", "triggers": ["file-count-threshold"],
                           "file_count_threshold": 5.0}}
    assert auto_commit_violations(cfg) == []
    out = resolve_auto_commit_config(cfg, ["developer"], REPO_ROOT)
    assert out["file_count_threshold"] == 5
    assert isinstance(out["file_count_threshold"], int)


def test_non_integral_float_threshold_rejected():
    v = auto_commit_violations(
        {"auto_commit": {"mode": "auto", "triggers": ["file-count-threshold"],
                         "file_count_threshold": 5.5}})
    assert any("file_count_threshold" in m for m in v)


def test_enum_constants_match_schema():
    # advisory 3: a schema addition must not silently become a hard
    # --validate failure because the stdlib constants were not updated.
    import json

    from lib.auto_commit import _KEYS, _MODES, _TRIGGERS

    schema = json.loads(
        (REPO_ROOT / "config" / "project-config.schema.json").read_text(encoding="utf-8"))
    ac = schema["properties"]["auto_commit"]
    assert list(_MODES) == ac["properties"]["mode"]["enum"]
    assert list(_TRIGGERS) == ac["properties"]["triggers"]["items"]["enum"]
    assert set(_KEYS) == set(ac["properties"])


def test_valid_config_unchanged():
    cfg = {"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}}
    out = resolve_auto_commit_config(cfg, ["developer", "git"], REPO_ROOT)
    assert out["mode"] == "auto" and out["eligible_roles"] == ["developer"]


# --------------------------------------------------------------------------- #
# E2E: --validate rc=1, sync rc=0 + fail-safe allowlist                       #
# --------------------------------------------------------------------------- #


def _project(tmp_path, ac, provider="Claude"):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        f"project:\n  name: t\n  prefix: t\nai-providers: [{provider}]\n"
        "roles: [orchestrator, developer, git]\n" + ac, encoding="utf-8")
    return tmp_path


def _sync(project, *flags):
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py"), *flags],
        cwd=project, capture_output=True, text=True)


def test_validate_rc1_on_triggers_with_mode_off(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: 'off'\n  triggers: [task-boundary]\n")
    r = _sync(p, "--validate")
    assert r.returncode == 1 and "triggers is only valid with mode: auto" in (
        r.stdout + r.stderr)


def test_validate_rc1_on_custom_without_script(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: custom\n")
    assert _sync(p, "--validate").returncode == 1


def test_sync_rc0_but_allowlist_not_rewritten(tmp_path):
    # #1142: invalid block -> warning, no allowlist write (stale one stays).
    p = _project(tmp_path, "auto_commit:\n  mode: auto\n  triggers: [custom]\n")
    r = _sync(p)
    assert r.returncode == 0, r.stderr
    assert not (p / ".meta-config" / "auto-commit-allowlist.json").exists()
    assert "auto_commit is invalid" in r.stderr


def test_validate_rc0_on_valid_config(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n")
    assert _sync(p, "--validate").returncode == 0


# --------------------------------------------------------------------------- #
# Render path: the fail-safe must reach the generated prose (blocking finding) #
# --------------------------------------------------------------------------- #


def test_invalid_config_renders_disabled_commit_authority_on_hookless_provider(tmp_path):
    # Opencode has has_hooks: false, so orchestrator-guard-impl.sh never
    # enforces anything -- the rendered agent prose is the only place the
    # #1091 fail-safe can reach. It must say "off", not "mode: auto enabled".
    p = _project(
        tmp_path,
        "auto_commit:\n  mode: auto\n  triggers: [custom]\n",
        provider="Opencode",
    )
    r = _sync(p)
    assert r.returncode == 0, r.stderr
    rendered = (p / ".opencode" / "agents" / "developer.md").read_text(encoding="utf-8")
    assert "Commit authority (issue #694): off" in rendered
    assert "disabled (fail-safe)" in rendered
    assert "`auto_commit.mode: auto` enabled" not in rendered


def test_valid_config_still_renders_enabled_commit_authority(tmp_path):
    p = _project(
        tmp_path,
        "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n",
        provider="Opencode",
    )
    r = _sync(p)
    assert r.returncode == 0, r.stderr
    rendered = (p / ".opencode" / "agents" / "developer.md").read_text(encoding="utf-8")
    assert "`auto_commit.mode: auto` enabled" in rendered
    assert "Commit authority (issue #694): off" not in rendered


def _schema_keys():
    schema = json.loads((REPO_ROOT / "config" / "project-config.schema.json")
                        .read_text(encoding="utf-8"))
    return set(schema["properties"]["auto_commit"]["properties"])


def test_static_fallback_equals_schema_properties():
    from lib import auto_commit
    assert set(auto_commit._STATIC_KEYS) == _schema_keys()


def test_schema_only_key_is_accepted(tmp_path):
    # a key added only in the schema must not be reported as unknown
    from lib import auto_commit
    schema = json.loads((REPO_ROOT / "config" / "project-config.schema.json")
                        .read_text(encoding="utf-8"))
    schema["properties"]["auto_commit"]["properties"]["authority_overrides"] = {"type": "object"}
    path = tmp_path / "schema.json"
    path.write_text(json.dumps(schema), encoding="utf-8")
    assert "authority_overrides" in auto_commit._load_schema_keys(path)


def test_missing_schema_falls_back_to_static_keys(tmp_path):
    from lib import auto_commit
    assert auto_commit._load_schema_keys(tmp_path / "missing.json") == auto_commit._STATIC_KEYS


def test_unknown_key_message_names_key_and_source():
    v = auto_commit_violations({"auto_commit": {"mode": "off", "bogus": 1}})
    msg = [m for m in v if "bogus" in m][0]
    assert "config/project-config.schema.json" in msg and "allowed:" in msg


# --------------------------------------------------------------------------- #
# Issue #1181 (T2): semantic grant validation + inactive-role notices          #
# --------------------------------------------------------------------------- #


def test_authority_override_valid_grant_has_no_violation():
    cfg = {"auto_commit": {"mode": "auto", "triggers": ["task-boundary"],
                           "authority_overrides": _grant("documenter")}}
    assert authority_override_violations(cfg, REPO_ROOT) == []


def test_authority_override_missing_ack_rejected():
    cfg = {"auto_commit": {
        "authority_overrides": {"documenter": {"authority": "direct"}}}}
    v = authority_override_violations(cfg, REPO_ROOT)
    assert v == [
        "auto_commit.authority_overrides.documenter: missing acknowledge_full_shell: true "
        "(the grant is a full Bash grant, not a git-only grant)"
    ]


def test_authority_override_scalar_value_rejected():
    cfg = {"auto_commit": {"authority_overrides": {"documenter": "direct"}}}
    v = authority_override_violations(cfg, REPO_ROOT)
    assert v == [
        "auto_commit.authority_overrides.documenter: "
        "expected {authority: direct, acknowledge_full_shell: true}"
    ]


def test_authority_override_unknown_value_rejected():
    cfg = {"auto_commit": {"authority_overrides": {
        "documenter": {"authority": "notify", "acknowledge_full_shell": True}}}}
    v = authority_override_violations(cfg, REPO_ROOT)
    assert v == [
        "auto_commit.authority_overrides.documenter: "
        "expected {authority: direct, acknowledge_full_shell: true}"
    ]


def test_authority_override_read_only_role_rejected():
    v = authority_override_violations(
        {"auto_commit": {"authority_overrides": _grant("explorer")}}, REPO_ROOT)
    assert v == [
        "auto_commit.authority_overrides.explorer: "
        "role has no Edit/Write (derived authority is 'none')"
    ]


def test_authority_override_typo_role_rejected():
    v = authority_override_violations(
        {"auto_commit": {"authority_overrides": _grant("documenterr")}}, REPO_ROOT)
    assert v == [
        "auto_commit.authority_overrides.documenterr: "
        "role has no Edit/Write (derived authority is 'none')"
    ]


def test_authority_override_non_mapping_rejected():
    v = authority_override_violations(
        {"auto_commit": {"authority_overrides": ["documenter"]}}, REPO_ROOT)
    assert v == [
        "auto_commit.authority_overrides: expected an object of role -> grant object"
    ]


def test_grant_not_enforced_when_guard_disabled():
    cfg = {
        "hooks": {"orchestrator-guard": {"enabled": False}},
        "auto_commit": {"authority_overrides": _grant("documenter")},
    }
    v = authority_override_violations(cfg, REPO_ROOT)
    assert v == [
        "auto_commit.authority_overrides.documenter: grant not enforced "
        "(guard hook disabled: hooks.orchestrator-guard.enabled is not true)"
    ]


def test_grant_not_enforced_on_hookless_provider():
    cfg = {"ai-providers": ["Opencode"],
           "auto_commit": {"authority_overrides": _grant("documenter")}}
    v = authority_override_violations(cfg, REPO_ROOT, _HOOKLESS_PC)
    assert v == [
        "auto_commit.authority_overrides.documenter: grant not enforced "
        "(provider 'Opencode', reason has_hooks=false)"
    ]


def test_grant_enforced_on_mixed_provider_set_is_no_violation():
    cfg = {"ai-providers": ["Claude", "Opencode"],
           "auto_commit": {"authority_overrides": _grant("documenter")}}
    assert authority_override_violations(cfg, REPO_ROOT, _HOOKED_PC) == []


def test_authority_override_inactive_role_is_not_a_violation():
    cfg = {"auto_commit": {"authority_overrides": _grant("documenter")}}
    assert authority_override_violations(cfg, REPO_ROOT) == []
    notes = authority_override_notices(cfg, ["developer"])
    assert notes == [
        "auto_commit.authority_overrides.documenter: grant ignored — role is not active "
        "(not listed in `roles:` or dropped by the active set)"
    ]


def test_grant_notice_for_gate_dropped_role():
    # Role is in raw_roles but dropped by the active set, so the EFFECTIVE
    # active set passed to the notices helper excludes it (K-15/RVW2-1181-05).
    cfg = {"auto_commit": {"authority_overrides": _grant("documenter")}}
    raw_roles = {"documenter", "developer"}

    class _DroppingActiveSet:
        def has(self, role):
            return role == "developer"

    effective = {r for r in raw_roles if _DroppingActiveSet().has(r)}
    notes = authority_override_notices(cfg, effective)
    assert len(notes) == 1 and "grant ignored" in notes[0]
    assert "documenter" in notes[0]


def test_validate_rc1_on_read_only_grant(tmp_path):
    p = _project(tmp_path,
                 "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n"
                 "  authority_overrides:\n    explorer:\n      authority: direct\n"
                 "      acknowledge_full_shell: true\n")
    r = _sync(p, "--validate")
    out = r.stdout + r.stderr
    assert r.returncode == 1, out
    assert "config-audit [ERROR] auto_commit: auto_commit.authority_overrides.explorer" in out


def test_validate_rc0_on_inactive_role_grant(tmp_path):
    p = _project(tmp_path,
                 "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n"
                 "  authority_overrides:\n    documenter:\n      authority: direct\n"
                 "      acknowledge_full_shell: true\n")
    r = _sync(p, "--validate")
    out = r.stdout + r.stderr
    assert r.returncode == 0, out
    assert "config-audit [ERROR]" not in out
    assert ("config-audit [INFO] auto_commit: "
            "auto_commit.authority_overrides.documenter") in out


def test_validate_rc1_on_grant_without_active_guard(tmp_path):
    p = _project(tmp_path,
                 "hooks:\n  orchestrator-guard:\n    enabled: false\n"
                 "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n"
                 "  authority_overrides:\n    documenter:\n      authority: direct\n"
                 "      acknowledge_full_shell: true\n")
    r = _sync(p, "--validate")
    out = r.stdout + r.stderr
    assert r.returncode == 1, out
    assert ("config-audit [ERROR] auto_commit: auto_commit.authority_overrides.documenter: "
            "grant not enforced (guard hook disabled: "
            "hooks.orchestrator-guard.enabled is not true)") in out
