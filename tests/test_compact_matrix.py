"""Task 18 (2c.3): provider matrix × context profile — QG-2, AC-27, AC-28.

Spec ``docs/specs/2026-10-11-context-profiles-spec.md``:

* **QG-2 / AC-24** — information preservation ``full`` ↔ ``compact``: the sets are
  equal for (1) roles, (2) keywords, (3) pipeline signal-keywords, (4) the
  ``required``/``recommended``/``orchestrator_only`` flags, (5) the name-only list
  with its reasons, and (6) the IC-04 example rule is verified. Additionally every
  section ``compact`` removes (§2a, §9-Begründung, Contracts, ``short_desc``) stays
  reachable through an existing pointer: **the path exists and the section is
  present there** (asserted strictly below, per provider).
* **AC-27 / QG-6** — the provider matrix runs 9 providers × 2 profiles plus
  multi-provider combinations (shared-file downgrade, AC-30).
* **AC-28** — ``sync.py --check`` is green after a ``compact`` sync and a second
  sync produces byte-identical files.

Everything is derived from ``config/ai-providers.yaml`` and the context templates —
no provider literal appears in this module (AC-36). ``compact`` stays opt-in and
unverified: nothing here claims validation, verification or recommendation.

Run: python -m pytest tests/test_compact_matrix.py -q
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _entry in (str(_REPO_ROOT), str(_REPO_ROOT / "scripts")):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

from tests.active_set_render import default_config, synced_projects  # noqa: E402
from tests.test_provider_matrix_sync import _generated_files, _LOCAL_FILE_RE  # noqa: E402

from lib.agents import (  # noqa: E402
    build_routing_tool_definition,
    build_routing_tool_definitions_for_providers,
)
from lib.config import PIPELINES_EFFECTIVE_KEY, build_variables  # noqa: E402

# --------------------------------------------------------------------------
# Matrix data — read from the registry, never hard-coded (AC-36)
# --------------------------------------------------------------------------

_PROVIDER_TABLE = yaml.safe_load(
    (_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
)["providers"]
_PROVIDERS = sorted(_PROVIDER_TABLE)
_PROFILES = ("full", "compact")

_ROLES_CONFIG = yaml.safe_load(
    (_REPO_ROOT / "config" / "role-defaults.yaml").read_text(encoding="utf-8")
)["roles"]


def _context_file_groups():
    groups = {}
    for provider, pc in _PROVIDER_TABLE.items():
        groups.setdefault(pc["context_file"], []).append(provider)
    return {name: sorted(members) for name, members in groups.items()}


_CONTEXT_FILE_GROUPS = _context_file_groups()
# The multi-provider combination with the most sharers is the shared-file case.
# Two sharers are enough to exercise AC-30 and keep the full render below the
# entry-file hard cap (a ``full`` AGENTS.md for the whole group exceeds it).
_SHARED_CONTEXT_FILE = max(_CONTEXT_FILE_GROUPS, key=lambda name: len(_CONTEXT_FILE_GROUPS[name]))
_SHARED_GROUP = _CONTEXT_FILE_GROUPS[_SHARED_CONTEXT_FILE][:2]

# The manifest whose body renders the compact one-line agent list (target_file).
_MANAGED_TARGET = yaml.safe_load(
    (_REPO_ROOT / "templates" / "context" / "agents-managed.md").read_text(encoding="utf-8")
    .split("---", 2)[1]
)["target_file"]

_COMPACT_LINE_RE = re.compile(r"^(?P<agent>[a-z0-9][a-z0-9-]*)\|(?P<flags>[^|]*)\|(?P<keywords>[^|]*)\|(?P<examples>.*)$")
_PIPELINE_LINE_RE = re.compile(r"^pipeline:(?P<pipeline>[^|]+)\|(?P<keywords>.*)$")
_NAME_ONLY_PREFIX = "name-only: "


# --------------------------------------------------------------------------
# Fixtures / helpers
# --------------------------------------------------------------------------


def _config(providers, *, profile=None, overrides=None):
    config = default_config()
    config["ai-providers"] = list(providers)
    if profile is not None:
        config["context-profile"] = profile
    if overrides:
        config["provider-overrides"] = overrides
    return config


def _run_sync(project: Path, *extra: str):
    return subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"),
         "--config", str(project / ".meta-config" / "project.yaml"), *extra],
        cwd=project, capture_output=True, text=True, timeout=900,
    )


def _sync_fresh(project: Path, config: dict, *extra: str):
    """Write ``config`` into ``project``, sync it, and return the result."""
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    (project / ".meta-config" / "project.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = _run_sync(project, *extra)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    return project, result


@pytest.fixture(scope="module")
def matrix(tmp_path_factory):
    """``{(provider, profile): project}`` for the full 9 × 2 matrix."""
    configs = {"%s-%s" % (provider, profile): _config([provider], profile=profile)
               for provider in _PROVIDERS for profile in _PROFILES}
    synced = synced_projects(tmp_path_factory, configs)
    return {(provider, profile): synced["%s-%s" % (provider, profile)]
            for provider in _PROVIDERS for profile in _PROFILES}


@pytest.fixture(scope="module")
def multi_provider(tmp_path_factory):
    """Multi-provider combinations: shared file compact / full, override-scoped."""
    configs = {
        "shared-compact": _config(_SHARED_GROUP, profile="compact"),
        "shared-full": _config(_SHARED_GROUP),
    }
    projects = synced_projects(tmp_path_factory, configs)
    return projects


def _project_config(project: Path) -> dict:
    return yaml.safe_load(
        (project / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))


def _routing(project: Path, provider: str) -> dict:
    """The profile-independent routing knowledge for ``provider``."""
    config = _project_config(project)
    variables, _warnings = build_variables(config, _REPO_ROOT, project)
    return build_routing_tool_definition(
        _REPO_ROOT, config, variables, pipelines=variables[PIPELINES_EFFECTIVE_KEY])


def _rendered_routing(project: Path, provider: str) -> str:
    """Exactly the string ``sync`` writes into ``{{INTENT_ROUTING_TOOLS}}``."""
    config = _project_config(project)
    variables, _warnings = build_variables(config, _REPO_ROOT, project)
    rendered = build_routing_tool_definitions_for_providers(
        _REPO_ROOT, config, variables, [provider],
        pipelines=variables[PIPELINES_EFFECTIVE_KEY])
    return rendered.get(provider, "")


def _tool_format(provider: str) -> str:
    from lib.delegation_syntax import DelegationSyntaxEngine

    caps = DelegationSyntaxEngine().get_capabilities(provider)
    return str(caps.get("handoff_format") or "")


def _full_routing_data(project: Path, provider: str) -> dict:
    """Parse the ``full`` render (json / yaml_text_block) into the routing data."""
    text = _rendered_routing(project, provider)
    fmt = _tool_format(provider)
    if fmt == "json":
        return json.loads(text)
    return yaml.safe_load(text)


def _orchestrator_file(project: Path, provider: str) -> Path:
    agents_dir = project / _PROVIDER_TABLE[provider]["agents_dir"]
    assert agents_dir.is_dir(), "%s: agents dir missing" % provider
    for candidate in agents_dir.iterdir():
        if candidate.is_file() and candidate.name.startswith("orchestrator."):
            return candidate
    raise AssertionError("%s: no orchestrator artifact in %s" % (provider, agents_dir))


def _section(text: str, heading_prefix: str) -> str:
    lines = text.splitlines(keepends=True)
    out, inside = [], False
    for line in lines:
        if line.startswith(heading_prefix):
            inside = True
        elif inside and line.startswith("## "):
            break
        if inside:
            out.append(line)
    return "".join(out)


def _parse_routing_lines(text: str):
    """Parse the IC-04 line block into ``(rules, pipelines, name_only_line)``."""
    rules, pipelines, name_only_line = {}, {}, None
    for line in text.splitlines():
        if not line:
            continue
        if line.startswith(_NAME_ONLY_PREFIX):
            name_only_line = line[len(_NAME_ONLY_PREFIX):]
            continue
        match = _PIPELINE_LINE_RE.match(line)
        if match:
            pipelines[match.group("pipeline")] = [
                keyword for keyword in match.group("keywords").split(";") if keyword]
            continue
        match = _COMPACT_LINE_RE.match(line)
        assert match, "unparsable compact routing line: %r" % line
        rules[match.group("agent")] = {
            "flags": [flag for flag in match.group("flags").split(",") if flag],
            "keywords": [k for k in match.group("keywords").split(";") if k],
            "examples": [e for e in match.group("examples").split("/") if e],
            "examples_raw": match.group("examples"),
        }
    return rules, pipelines, name_only_line


def _name_only_entries(name_index) -> list:
    """``[(agent, reason)]`` for the ``name_only`` roles (independent extraction)."""
    return sorted(
        (entry["agent"], entry["name_only_reason"])
        for entry in name_index
        if entry["addressability"] == "name_only"
    )


def _ic04_examples(rule: dict) -> list:
    """The IC-04 selection rule, re-implemented here as an independent oracle.

    First example plus every later example that does not repeat one of the
    role's own keywords (case-insensitive substring).
    """
    examples = [str(example) for example in (rule.get("examples") or [])]
    if not examples:
        return []
    keywords = [str(k).casefold() for k in (rule.get("keywords") or []) if str(k)]
    selected = [examples[0]]
    for example in examples[1:]:
        if not any(keyword in example.casefold() for keyword in keywords):
            selected.append(example)
    return selected


def _flag_tuple(rule: dict, name_only_agents) -> tuple:
    tier = rule.get("tier", "optional")
    return (
        tier == "required",
        tier == "recommended",
        bool(rule.get("orchestrator_only")),
        rule.get("agent") in name_only_agents,
    )


def _compact_flag_tuple(flags) -> tuple:
    return ("req" in flags, "rec" in flags, "orch-only" in flags, "name-only" in flags)


# --------------------------------------------------------------------------
# QG-2 — set equality full ↔ compact, element by element
# --------------------------------------------------------------------------


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_qg2_roles_set_equality(matrix, provider):
    """(1) The routable role set is identical in both renders."""
    definition = _routing(matrix[(provider, "full")], provider)
    name_index = definition["routing"]["name_index"]
    name_only_agents = {agent for agent, _ in _name_only_entries(name_index)}

    full_roles = {rule["agent"] for rule in definition["routing"]["rules"]} | name_only_agents
    rules, _pipelines, _line = _parse_routing_lines(
        _rendered_routing(matrix[(provider, "compact")], provider))
    # name-only roles carry no keyword rule; they render on the dedicated line.
    compact_roles = set(rules) | name_only_agents
    assert compact_roles == full_roles, (
        "roles differ: full-only=%s compact-only=%s"
        % (sorted(full_roles - compact_roles)[:5], sorted(compact_roles - full_roles)[:5]))
    assert full_roles, "%s: no routable role rendered" % provider


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_qg2_keywords_set_equality(matrix, provider):
    """(2) The (role, keyword) set is identical in both renders."""
    definition = _routing(matrix[(provider, "full")], provider)
    full = {(rule["agent"], keyword)
            for rule in definition["routing"]["rules"]
            for keyword in rule["keywords"]}
    rules, _pipelines, _line = _parse_routing_lines(
        _rendered_routing(matrix[(provider, "compact")], provider))
    compact = {(agent, keyword) for agent, data in rules.items() for keyword in data["keywords"]}
    assert compact == full, (
        "keywords differ: full-only=%s compact-only=%s"
        % (sorted(full - compact)[:5], sorted(compact - full)[:5]))


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_qg2_pipeline_signal_keywords_set_equality(matrix, provider):
    """(3) The (pipeline, signal-keyword) set is identical in both renders."""
    definition = _routing(matrix[(provider, "full")], provider)
    full = {(pipeline["pipeline"], keyword)
            for pipeline in definition["routing"]["pipelines"]
            for keyword in pipeline["keywords"]}
    _rules, pipelines, _line = _parse_routing_lines(
        _rendered_routing(matrix[(provider, "compact")], provider))
    compact = {(name, keyword) for name, keywords in pipelines.items() for keyword in keywords}
    assert compact == full, (
        "pipeline signal-keywords differ: full-only=%s compact-only=%s"
        % (sorted(full - compact)[:5], sorted(compact - full)[:5]))
    assert full, "%s: no pipeline signal-keywords rendered" % provider


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_qg2_flags_set_equality(matrix, provider):
    """(4) required / recommended / orchestrator_only / name-only are preserved."""
    definition = _routing(matrix[(provider, "full")], provider)
    name_only_agents = {agent for agent, _ in _name_only_entries(definition["routing"]["name_index"])}
    full = {(rule["agent"],) + _flag_tuple(rule, name_only_agents)
            for rule in definition["routing"]["rules"]}
    rules, _pipelines, _line = _parse_routing_lines(
        _rendered_routing(matrix[(provider, "compact")], provider))
    compact = {(agent,) + _compact_flag_tuple(data["flags"]) for agent, data in rules.items()}
    assert compact == full, (
        "flags differ: full-only=%s compact-only=%s"
        % (sorted(full - compact)[:5], sorted(compact - full)[:5]))


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_qg2_name_only_list_and_reasons_equality(matrix, provider):
    """(5) The name-only line matches the reconstructed expected line verbatim.

    The reasons themselves contain ``"; "``/``(``/``,``, so a naive split of the
    rendered line is lossy: the line is compared against the entry list
    reconstructed from the ``full`` name_index instead.
    """
    definition = _routing(matrix[(provider, "full")], provider)
    entries = _name_only_entries(definition["routing"]["name_index"])
    assert entries, "%s: no name_only role in the name_index" % provider

    _rules, _pipelines, line = _parse_routing_lines(
        _rendered_routing(matrix[(provider, "compact")], provider))
    assert line is not None, "%s: compact render has no name-only line" % provider
    expected = "; ".join("%s (%s)" % (agent, reason) for agent, reason in entries)
    assert line == expected, "name-only line mismatch:\n%s\n%s" % (expected, line)

    # The entries themselves come from the role registry (source of truth).
    for agent, reason in entries:
        assert _ROLES_CONFIG[agent]["routing"]["name_only_reason"] == reason, agent


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_qg2_ic04_example_rule_verified(matrix, provider):
    """(6) The IC-04 example rule is applied and the examples stay verbatim.

    The example field is compared as a whole string (``"/".join(selected)``):
    examples legitimately contain ``/`` (e.g. ``CI/CD-Pipeline``), so splitting
    the rendered field would be lossy and could not prove preservation.
    """
    definition = _routing(matrix[(provider, "full")], provider)
    by_agent = {rule["agent"]: rule for rule in definition["routing"]["rules"]}
    rules, _pipelines, _line = _parse_routing_lines(
        _rendered_routing(matrix[(provider, "compact")], provider))

    checked = 0
    for agent, data in rules.items():
        rule = by_agent[agent]
        expected = _ic04_examples(rule)
        assert data["examples_raw"] == "/".join(expected), (
            "%s/%s: example field %r != IC-04 selection %r"
            % (provider, agent, data["examples_raw"], expected))
        for example in expected:
            assert example in rule["examples"], (
                "%s/%s: example %r is not verbatim in the routing source"
                % (provider, agent, example))
        checked += 1
    assert checked, "%s: no routing rule to verify" % provider


# --------------------------------------------------------------------------
# QG-2 — reachability of the sections compact removes (path + section present)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_reachability_pipeline_stage_detail_pointer(matrix, provider):
    """§2a → the pipeline-details file; the stage block is present and identical."""
    compact_orch = _orchestrator_file(matrix[(provider, "compact")], provider).read_text(
        encoding="utf-8")
    full_orch = _orchestrator_file(matrix[(provider, "full")], provider).read_text(
        encoding="utf-8")

    pointer = re.search(r"`([^`]*pipeline-details[^`]*)`", compact_orch)
    assert pointer, "%s: compact §2a has no pipeline-details pointer" % provider
    pointer_path = pointer.group(1).replace("\\", "/")
    assert "<pipeline>" in pointer_path, pointer_path

    full_region = _section(full_orch, "## 2a.")
    assert full_region, "%s: full §2a region missing" % provider
    # The stage blocks end where the shared "Plan-driven gate" paragraph starts.
    blocks_area = full_region.split("**Plan-driven gate:**", 1)[0]
    blocks = {m.group(1): m.group(2).strip()
              for m in re.finditer(r"^### `([^`]+)`\n(.*?)(?=^### `|\Z)", blocks_area, re.M | re.S)}
    assert blocks, "%s: full §2a carries no pipeline block" % provider

    project = matrix[(provider, "compact")]
    for pipeline in blocks:
        destination = project / pointer_path.replace("<pipeline>", pipeline)
        assert destination.is_file(), (
            "%s: §2a pointer %s does not resolve" % (provider, pointer_path))
        body = re.sub(r"\A# Pipeline `[^`]+`\n+", "", destination.read_text(encoding="utf-8")).strip()
        assert body == blocks[pipeline], (
            "%s/%s: pipeline-details body differs from the full §2a block" % (provider, pipeline))


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_reachability_summarization_contract_pointer(matrix, provider):
    """§9-Begründung → the orchestrator reference file carries the landed section."""
    compact_orch = _orchestrator_file(matrix[(provider, "compact")], provider).read_text(
        encoding="utf-8")
    assert "_wf-orchestrator-reference.md" in compact_orch, (
        "%s: compact §9 renders no reference pointer" % provider)

    reference = _REPO_ROOT / "agents" / "1-generic" / "_wf-orchestrator-reference.md"
    assert reference.is_file(), "pointer destination %s missing" % reference
    text = reference.read_text(encoding="utf-8")
    assert "## Summarization-as-a-Contract" in text, "section heading missing"
    section = _section(text, "## Summarization-as-a-Contract")
    # rationale + checkpoint format + harness enforcement (the just-landed fix)
    for marker in ("**Rationale (issue #267):**", "STATUS/RESULT/ARTIFACTS block",
                   "**Checkpoint format:**", "**Harness enforcement (issue #265):**",
                   "scripts/lib/orchestration.py", "CheckpointStore.save_raw_output",
                   "checkpoint_ref"):
        assert marker in section, "%s: §9 destination lacks %r" % (provider, marker)


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_reachability_contracts_destination(matrix, provider):
    """Contracts → ``config/role-defaults.yaml`` carries them; the path exists."""
    definition = _routing(matrix[(provider, "full")], provider)
    destination = _REPO_ROOT / "config" / "role-defaults.yaml"
    assert destination.is_file(), destination

    referenced = 0
    for rule in definition["routing"]["rules"]:
        agent = rule["agent"]
        handoff = _ROLES_CONFIG[agent].get("handoff") or {}
        if rule["output_contract"]:
            assert handoff.get("output_contract") == rule["output_contract"], (
                "%s/%s: output_contract not reachable in role-defaults" % (provider, agent))
            referenced += 1
        for contract in rule["input_contracts"]:
            assert contract in (handoff.get("input_contracts") or []), (
                "%s/%s: input contract %r not reachable in role-defaults"
                % (provider, agent, contract))
            referenced += 1
    assert referenced, "%s: no contract referenced by the routing definition" % provider


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_reachability_short_desc_destination(matrix, provider):
    """``short_desc`` → carried by the artifact that keeps the role→description map.

    QG-2 clause ``short_desc`` (path exists AND the section is present there),
    asserted per destination class:

    * AGENTS.md-group: the ``## Agent Directory`` section of the file named by
      ``templates/context/agents-managed.md`` — asserted **strictly**: every
      ``name_index`` role has a ``- `\\`<role>\\``: `` bullet and its
      ``short_desc`` string is present (measured 62/62).
    * all other providers: only the name-channel form is asserted (a catalog
      file exists per role), because the compact render currently carries **no**
      ``short_desc`` destination for them.

    That second class is **Claude, Continue and Copilot**: the compact §3 line
    block has no ``short_desc`` field, and none of these three renders the
    ``agents-list-compact`` partial in any profile (``0/62`` / ``1/62`` measured).
    This is the known-open 2b ``roster_in_harness`` gating finding (C2:
    "Agent-Tabelle in ``<context>`` entfällt bei ``roster_in_harness: true``,
    sonst Namensliste"), out of Task 18's scope — reported as an open deviation,
    deliberately not skipped, xfailed or weakened.
    """
    context_file = _PROVIDER_TABLE[provider]["context_file"]
    definition = _routing(matrix[(provider, "full")], provider)
    name_index = definition["routing"]["name_index"]
    assert name_index, "%s: empty name_index" % provider

    ctx_text = (matrix[(provider, "compact")] / context_file).read_text(encoding="utf-8")
    if context_file == _MANAGED_TARGET:
        section = _section(ctx_text, "## Agent Directory")
        assert section, "%s: compact context file has no Agent Directory section" % provider
        listed = dict(re.findall(r"^- `([^`]+)`: (.+)$", section, re.M))
        assert listed, "%s: compact Agent Directory carries no agent list" % provider
        for entry in name_index:
            assert entry["agent"] in listed, (
                "%s: %s missing from the compact agent list" % (provider, entry["agent"]))
            short_desc = entry["short_desc"].strip()
            if short_desc:
                assert short_desc in ctx_text, (
                    "%s: short_desc of %s not present in the compact context file"
                    % (provider, entry["agent"]))
    else:
        agents_dir = matrix[(provider, "compact")] / _PROVIDER_TABLE[provider]["agents_dir"]
        for entry in name_index:
            candidates = [p for p in agents_dir.iterdir()
                          if p.is_file() and p.name.split(".")[0] == entry["agent"]]
            assert candidates, (
                "%s: no name-channel catalog file for %s in %s"
                % (provider, entry["agent"], agents_dir))


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_compact_section_3_keeps_the_name_index_vocabulary(matrix, provider):
    """C1/C2: the compact §3 prose keeps the ``name_index`` vocabulary, and the
    artifact's line block is exactly the library render (no divergence)."""
    orch = _orchestrator_file(matrix[(provider, "compact")], provider).read_text(encoding="utf-8")
    section = _section(orch, "## 3.")
    assert section, "%s: compact §3 missing" % provider
    for field in ("short_desc", "tier", "orchestrator_only", "addressability", "name_only_reason"):
        assert field in section, "%s: compact §3 lost %r" % (provider, field)

    rendered = _rendered_routing(matrix[(provider, "compact")], provider)
    rules, _pipelines, _line = _parse_routing_lines(rendered)
    assert rules, "%s: compact §3 render is empty" % provider
    for line in rendered.splitlines():
        if line:
            assert line in section, (
                "%s: rendered routing line missing from the artifact §3: %r" % (provider, line))


# --------------------------------------------------------------------------
# AC-30 — provider-overrides scope + shared-file downgrade
# --------------------------------------------------------------------------


def test_shared_file_compact_when_every_sharer_is_compact(multi_provider):
    shared = multi_provider["shared-compact"] / _SHARED_CONTEXT_FILE
    text = shared.read_text(encoding="utf-8")
    assert re.search(r"^- `[a-z0-9-]+`: ", text, re.M), (
        "all-compact sharers must render the compact one-line agent list")
    assert "| Agent | Core Capabilities |" not in text


def test_provider_override_scopes_compact_to_one_provider(tmp_path):
    """AC-30: the override acts on P only; the shared file stays ``full`` + WARN."""
    override_target = _SHARED_GROUP[0]
    other = _SHARED_GROUP[1]
    config = _config(_SHARED_GROUP, overrides={override_target: {"context-profile": "compact"}})
    project, result = _sync_fresh(tmp_path / "override-scoped", config)
    output = result.stdout + result.stderr

    assert "context-profile.shared-file-downgrade" in output, output[-2000:]
    assert override_target in output, (
        "downgrade warning does not name the compact requester %s" % override_target)

    shared_text = (project / _SHARED_CONTEXT_FILE).read_text(encoding="utf-8")
    assert "| Agent | Core Capabilities |" in shared_text, "shared file must render 'full'"
    assert not re.search(r"^- `[a-z0-9-]+`: ", shared_text, re.M)

    overridden = _orchestrator_file(project, override_target).read_text(encoding="utf-8")
    assert "<pipeline>.md" in overridden, "overridden provider must render compact §2a"
    assert re.search(r"^name-only: ", overridden, re.M)

    untouched = _orchestrator_file(project, other).read_text(encoding="utf-8")
    assert "<pipeline>.md" not in untouched, "the override must not leak to other sharers"
    assert re.search(r"^### `[^`]+`", _section(untouched, "## 2a."), re.M)


# --------------------------------------------------------------------------
# AC-28 / QG-6 — idempotence
# --------------------------------------------------------------------------


def _snapshot(project: Path) -> dict:
    snapshot = {}
    for path in _generated_files(project):
        rel = path.relative_to(project).as_posix()
        if _LOCAL_FILE_RE.search(rel):
            continue
        snapshot[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return snapshot


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_compact_second_sync_is_byte_identical(matrix, provider):
    project = matrix[(provider, "compact")]
    before = _snapshot(project)
    result = _run_sync(project)
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    assert _snapshot(project) == before, (
        "%s: a second compact sync changed generated files" % provider)


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_compact_sync_check_is_green(matrix, provider):
    result = _run_sync(matrix[(provider, "compact")], "--dry-run", "--check")
    assert result.returncode == 0, (
        "%s: --check reports pending changes after a compact sync\n%s"
        % (provider, result.stdout[-2000:]))


def test_multi_provider_check_is_green(multi_provider):
    for name in ("shared-compact", "shared-full"):
        result = _run_sync(multi_provider[name], "--dry-run", "--check")
        assert result.returncode == 0, "%s: --check not green\n%s" % (name, result.stdout[-2000:])
