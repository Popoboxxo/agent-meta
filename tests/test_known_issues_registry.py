"""IC-21 (SPEC-CONTEXT-PROFILES-2026-10-11, Task 0d.1, AC-37/AC-78/AC-85):
config/known-issues.yaml is a well-formed, provider-agnostic registry.

The validator (scripts/lib/doctor_registry.py) is the registry contract: form, unique ids, enums,
predicate / detector grammar (incl. the Rev.-3 extensions value_key,
pattern_from_config, active_role_where, map wildcard, source: doctor,
verified-state-by-capability, any_of), the `command` allowlist and the
bindings to config/provider-capabilities.yaml (+ config/ai-providers.yaml).
Negative tests prove the validator rejects broken entries.
"""

import copy
import re
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.doctor_registry import (  # noqa: E402
    FORBIDDEN_ARGV as _FORBIDDEN_ARGV,
    load_validation_context,
    validate_entry,
    validate_registry,
)

_REGISTRY_PATH = _ROOT / "config" / "known-issues.yaml"

# finding-ref check ids whose producer does not exist yet. Remove each id from
# this set when the producer lands (0d.4: IC-10 checks). The reverse test turns
# a stale entry red. The runner-owned doctor.* ids (doctor.environment,
# doctor.tmp-sink-location) are defined as literals in scripts/lib/doctor_detectors.py.
_PENDING_0D4 = {"context.declared-surface-empty", "context.legacy-artifact-present"}


# Mandatory seeds: IC-21 table + Rev. 2.2 + Rev. 3/3.1/3.4 additions.
REQUIRED_SEEDS = {
    "context-hard-cap-truncation", "context-soft-cap-bytes",
    "instruction-soft-cap-chars", "context-soft-cap-lines", "dangling-pointer",
    "rule-unreachable", "unread-channel", "rules-file-wrong-suffix",
    "orchestrator-missing-subagent-allowlist", "agent-name-suffix",
    "agent-frontmatter-strict-schema", "dispatch-depth-missing",
    "dangling-role-dispatch", "gate-dropped-allowlist-role",
    "unresolved-placeholder-in-output", "dead-variable-code-quality-rules",
    "project-role-not-generated", "hooks-not-registered", "sync-pending",
    "read-only-not-enforced", "schema-validation-skipped",
    "declared-surface-empty", "surface-unverified", "legacy-artifact-present",
    "routing-examples-language-fallback", "routing-keyword-overlap-active",
    "variable-unreferenced", "tmp-sink-not-gitignored",
    "repo-containment-block-missing", "tmp-sink-outside-repo-or-system-temp",
}


def _load_registry():
    return yaml.safe_load(_REGISTRY_PATH.read_text(encoding="utf-8"))


def _load_context():
    return load_validation_context(_ROOT)


# ---------------------------------------------------------------------- tests

@pytest.fixture(scope="module")
def ctx():
    return _load_context()


@pytest.fixture(scope="module")
def registry():
    assert _REGISTRY_PATH.is_file(), "config/known-issues.yaml missing"
    return _load_registry()


def _by_id(registry):
    return {e["id"]: e for e in registry["issues"]}


def test_registry_is_valid(registry, ctx):
    assert validate_registry(registry, ctx) == []


def test_ids_unique_and_kebab(registry):
    ids = [e["id"] for e in registry["issues"]]
    assert len(ids) == len(set(ids))
    assert all(re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", i) for i in ids)


def test_all_required_seeds_present(registry):
    assert REQUIRED_SEEDS <= set(_by_id(registry))


def test_no_command_argv_with_forbidden_flags(registry):
    for entry in registry["issues"]:
        det = entry["detector"]
        for d in det.get("any_of", [det]):
            if d.get("kind") == "command":
                assert not (_FORBIDDEN_ARGV & set(d["argv"])), entry["id"]


def test_sync_pending_is_check_command(registry):
    det = _by_id(registry)["sync-pending"]["detector"]
    assert det == {"kind": "command", "argv": ["--check"], "expect_exit": 0,
                   "timeout_s": 60}


def _all_detectors(entry):
    det = entry["detector"]
    return det["any_of"] if "any_of" in det else [det]


def test_grammar_extensions_are_exercised(registry):
    """AC-37: every Rev.-3 grammar extension is used by at least one entry."""
    issues = registry["issues"]
    used = set()
    for e in issues:
        for p in e["applies_to"]:
            if "active_role_where" in p:
                used.add("active_role_where")
            if "value_key" in p:
                used.add("value_key")
        if "any_of" in e["detector"]:
            used.add("any_of")
        for d in _all_detectors(e):
            if "value_key" in d:
                used.add("value_key")
            if "pattern_from_config" in d:
                used.add("pattern_from_config")
            if d.get("kind") == "finding-ref" and d.get("source") == "doctor":
                used.add("source-doctor")
            if "*" in str(d.get("key", "")).split("."):
                used.add("map-wildcard")
        if "verified-state-by-capability" in e:
            used.add("verified-state-by-capability")
    assert used >= {
        "active_role_where", "value_key", "any_of", "pattern_from_config",
        "source-doctor", "map-wildcard", "verified-state-by-capability",
    }


def test_seed_formalisations(registry):
    seeds = _by_id(registry)
    depth = seeds["dispatch-depth-missing"]
    assert {"capability": "agent_config_format", "op": "eq", "value": "toml"} in depth["applies_to"]
    assert depth["detector"]["kind"] == "toml-key"
    assert depth["detector"]["key"] == "agents.max_depth"
    assert depth["detector"]["op"] == "lt"
    assert depth["detector"]["value_key"] == "required_depth"

    ro = seeds["read-only-not-enforced"]
    assert {"capability": "read_only_enforcement", "op": "eq", "value": "none"} in ro["applies_to"]
    assert {"active_role_where": {"tools_without": ["Write", "Edit"]}} in ro["applies_to"]
    assert ro["severity"] == "INFO" and ro["verified-state"] == "UNVERIFIED"

    assert seeds["dead-variable-code-quality-rules"]["detector"] == {
        "kind": "variable-unreferenced", "key": "CODE_QUALITY_RULES",
        "universe": "all-roles-all-providers",
    }
    unref = seeds["variable-unreferenced"]
    assert unref["detector"]["key"] == "*" and unref["severity"] == "WARNING"
    assert unref["fix-owner"] == "project-config"

    hard = seeds["context-hard-cap-truncation"]
    assert hard["verified-state"] == "VERIFIED-SOURCE"
    assert hard["severity"] == "ERROR"
    assert hard["verified-state-by-capability"] == {
        "derive": "surface_verified_state.context_file"}
    assert seeds["unread-channel"]["verified-state"] == "SOURCE-DERIVED"
    assert seeds["unread-channel"]["verified-state-by-capability"] == {
        "derive": "surface_verified_state.rules"}
    soft = seeds["instruction-soft-cap-chars"]
    assert soft["verified-state"] == "UNVERIFIED"
    assert soft["verified-state-by-capability"] == {
        "context_soft_cap_chars": {4000: "DOCUMENTED", 12000: "UNVERIFIED"}}

    surf = seeds["surface-unverified"]
    assert surf["detector"]["key"] == "surface_verified_state.*"
    assert surf["detector"]["value"] == "UNVERIFIED"

    assert seeds["schema-validation-skipped"]["detector"]["source"] == "doctor"
    assert seeds["schema-validation-skipped"]["detector"]["check"] == "doctor.environment"
    assert seeds["routing-examples-language-fallback"]["detector"]["source"] == "sync-log"


def test_tmp_sink_seeds(registry):
    seeds = _by_id(registry)
    gi = seeds["tmp-sink-not-gitignored"]
    assert gi["severity"] == "WARNING" and gi["verified-state"] == "VERIFIED-SOURCE"
    pred = gi["applies_to"][0]
    assert (pred["config"], pred["op"], pred["value"], pred["default"]) == (
        "repo_containment.tmp-sink.enabled", "ne", False, True)
    subs = gi["detector"]["any_of"]
    assert len(subs) == 2 and all(s["kind"] == "regex" for s in subs)
    assert subs[0]["pattern_from_config"] == "repo_containment.tmp-sink.path"
    assert subs[1]["scope"] == "all"
    assert subs[0]["path"] == ".gitignore"
    assert subs[1]["path_template"] == "{tmp_sink}/.gitignore"
    # N-5: a missing block is NOT a finding of this seed.
    assert not any(p.get("op") == "absent" for p in gi["applies_to"])

    blk = seeds["repo-containment-block-missing"]
    assert blk["severity"] == "INFO"
    assert blk["detector"]["kind"] == "yaml-key"
    assert blk["detector"]["key"] == "repo_containment"
    assert blk["detector"]["op"] == "absent"
    assert blk["target"]["artifact"] == "project_config"

    loc = seeds["tmp-sink-outside-repo-or-system-temp"]
    assert loc["severity"] == "ERROR" and loc["verified-state"] == "VERIFIED-SOURCE"
    assert loc["detector"] == {
        "kind": "finding-ref", "check": "doctor.tmp-sink-location",
        "source": "doctor"}
    assert loc["applies_to"][0]["default"] is True
    assert "verified-state-by-capability" not in loc  # no UNVERIFIED cap


def test_project_role_seed_is_registered_binding_role(registry):
    det = _by_id(registry)["project-role-not-generated"]["detector"]
    assert det["bind"] == "role" and det["then"]["expect"] == "absent"


def test_tmp_sink_regex_ii_matches_gitignore_content(registry):
    """Sub-detector (ii) must accept TMP_SINK_GITIGNORE_CONTENT and reject
    a file that lacks either line."""
    sub = _by_id(registry)["tmp-sink-not-gitignored"]["detector"]["any_of"][1]
    pattern = re.compile(sub["pattern"], re.MULTILINE)
    assert pattern.search("*\n!.gitignore\n")
    assert not pattern.search("*\n")
    assert not pattern.search("!.gitignore\n")
    assert not pattern.search("foo\nbar\n")
    # CRLF checkout (core.autocrlf on Windows): the runner reads text unnormalised
    assert pattern.search("*\r\n!.gitignore\r\n")
    assert not pattern.search("*\r\n")


def test_agent_name_suffix_regex(registry):
    det = _by_id(registry)["agent-name-suffix"]["detector"]
    pattern = re.compile(det["pattern"], re.MULTILINE)
    assert pattern.search("name: template-orchestrator.agent")
    assert not pattern.search("name: template-orchestrator")


def _finding_refs(registry):
    for e in registry["issues"]:
        for d in _all_detectors(e):
            if d.get("kind") == "finding-ref":
                yield e["id"], d


def _lib_source():
    return {p: p.read_text(encoding="utf-8")
            for p in (_ROOT / "scripts" / "lib").rglob("*.py")}


def test_finding_ref_checks_exist(registry):
    """Every finding-ref check id is produced somewhere (literal in
    scripts/lib) or is explicitly pending / runner-owned."""
    sources = _lib_source()
    for eid, det in _finding_refs(registry):
        check = det["check"]
        if check in _PENDING_0D4:
            continue
        assert any(f'"{check}"' in text for text in sources.values()), (eid, check)


def test_pending_finding_ref_ids_are_not_in_code(registry):
    sources = _lib_source()
    referenced = {d["check"] for _, d in _finding_refs(registry)}
    assert _PENDING_0D4 <= referenced
    for check in _PENDING_0D4:
        assert not any(f'"{check}"' in text for text in sources.values()), (
            f"{check} now exists in code - remove it from the pending set")


def test_sync_log_check_literal_in_delegation_table(registry):
    det = _by_id(registry)["routing-examples-language-fallback"]["detector"]
    assert det["source"] == "sync-log"
    text = (_ROOT / "scripts" / "lib" / "delegation_table.py").read_text(encoding="utf-8")
    assert f'"{det["check"]}"' in text


def test_value_dispatch_keys_match_capability_values(registry, ctx):
    spec = _by_id(registry)["instruction-soft-cap-chars"]["verified-state-by-capability"]
    (cap_key, mapping), = spec.items()
    actual = {c[cap_key] for c in ctx["caps"].values() if c.get(cap_key) is not None}
    assert set(mapping) == actual


def test_variable_unreferenced_message_binds_length(registry):
    msg = _by_id(registry)["variable-unreferenced"]["message"]
    assert "{key}" in msg and "{length}" in msg and "`variables.{key}`" in msg


def test_evidence_dates_not_in_future(registry):
    for e in registry["issues"]:
        assert date.fromisoformat(str(e["evidence"]["date"])) <= date.today()


# ------------------------------------------------------ validator self-checks

def _sample(registry, eid="context-soft-cap-bytes"):
    return copy.deepcopy(_by_id(registry)[eid])


@pytest.mark.parametrize("mutate,needle", [
    (lambda e: e.pop("evidence"), "missing fields"),
    (lambda e: e.__setitem__("severity", "FATAL"), "bad severity"),
    (lambda e: e.__setitem__("verified-state", "MAYBE"), "bad verified-state"),
    (lambda e: e.__setitem__("fix-owner", "someone"), "bad fix-owner"),
    (lambda e: e.__setitem__("id", "Bad_Id"), "kebab-case"),
    (lambda e: e.__setitem__("bogus", 1), "unknown fields"),
    (lambda e: e["evidence"].__setitem__("date", "yesterday"), "YYYY-MM-DD"),
    (lambda e: e["evidence"].__setitem__("date", date(2026, 10, 11)), "YYYY-MM-DD"),
    (lambda e: e["evidence"].__setitem__("kind", "rumor"), "valid kind"),
    (lambda e: e.__setitem__("severity", "ERROR") or e.__setitem__("verified-state", "UNVERIFIED"),
     "ADR-11"),
    (lambda e: e["detector"].__setitem__("limit", 5), "exactly one of limit|limit_key"),
    (lambda e: e.__setitem__("detector", {"kind": "path-exists", "glob": "*.md",
                                           "bind": "role", "expect": "present"}),
     "bind requires then"),
    (lambda e: e.__setitem__("detector", {"any_of": [
        {"any_of": [{"kind": "path-exists", "path": "a", "expect": "present"},
                    {"kind": "path-exists", "path": "b", "expect": "present"}]},
        {"kind": "path-exists", "path": "c", "expect": "present"}]}),
     "must not be nested"),
    (lambda e: e.__setitem__("detector", {"kind": "finding-ref", "check": "x.y",
                                           "source": "doctor"}), "doctor.* check"),
    (lambda e: e["applies_to"].append({"surface_has_target": "agents"}), "must be the {key}"),
    (lambda e: e["applies_to"].append({"capability": "no_such_key", "op": "present"}),
     "not found"),
    (lambda e: e["applies_to"].append({"capability": "name", "op": "eq", "value": "x"}),
     "identity"),
    (lambda e: e["applies_to"].append(
        {"capability": "agent_config_format", "op": "eq", "value": "Codex"}),
     "identity"),
    (lambda e: e["applies_to"].append({"capability": "skills", "op": "weird"}), "bad op"),
    (lambda e: e["applies_to"].append({"capability": "skills", "op": "eq"}), "value"),
    (lambda e: e["applies_to"].append(
        {"capability": "required_depth", "op": "lt", "value_key": "nope"}), "value_key"),
    (lambda e: e["applies_to"].append({"config": "unknown_block.x", "op": "present"}),
     "schema"),
    (lambda e: e.__setitem__("detector", {"kind": "shell", "cmd": "ls"}), "unsupported detector"),
    (lambda e: e.__setitem__("detector", {"kind": "command", "argv": ["--check", "--dry-run"],
                                           "expect_exit": 0}), "forbidden flag"),
    (lambda e: e.__setitem__("detector", {"kind": "command", "argv": ["--deactivation-status"],
                                           "expect_exit": 0}), "forbidden flag"),
    (lambda e: e.__setitem__("detector", {"kind": "command", "argv": ["--sync"],
                                           "expect_exit": 0}), "allowlist"),
    (lambda e: e.__setitem__("detector", {"kind": "json-schema",
                                           "schema": {"type": "object", "pattern": "x"}}),
     "keyword"),
    (lambda e: e.__setitem__("detector", {"kind": "finding-ref", "check": "x.y",
                                           "source": "bogus"}), "finding-ref source"),
    (lambda e: e.__setitem__("detector", {"kind": "regex", "pattern": "(",
                                           "expect": "match"}), "invalid regex"),
    (lambda e: e.__setitem__("detector", {"any_of": [{"kind": "path-exists", "path": "x",
                                                       "expect": "present"}]}), "any_of"),
    (lambda e: e.__setitem__("message", "role {role} broke"), "unbound placeholder"),
    (lambda e: e["target"].__setitem__("artifact", "nonsense_dir"), "target.artifact"),
    (lambda e: e.__setitem__("verified-state-by-capability", {"derive": "bogus"}),
     "derive"),
    (lambda e: e.__setitem__("verified-state-by-capability",
                              {"context_soft_cap_bytes": "MAYBE"}), "bad verified-state"),
])
def test_validator_rejects_broken_entries(registry, ctx, mutate, needle):
    entry = _sample(registry)
    mutate(entry)
    errors = validate_entry(entry, ctx)
    assert errors, "validator accepted a broken entry"
    assert any(needle in err for err in errors), errors


def test_validator_accepts_bound_placeholders(registry, ctx):
    entry = _sample(registry, "read-only-not-enforced")
    entry["message"] = "role {role} is not read-only"
    assert validate_entry(entry, ctx) == []


def test_duplicate_ids_rejected(registry, ctx):
    doc = copy.deepcopy(registry)
    doc["issues"].append(copy.deepcopy(doc["issues"][0]))
    assert any("duplicate id" in e for e in validate_registry(doc, ctx))


def test_bad_registry_version_rejected(registry, ctx):
    doc = copy.deepcopy(registry)
    doc["registry-version"] = 2
    assert validate_registry(doc, ctx)
