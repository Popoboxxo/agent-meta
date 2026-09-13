"""Guard/ratchet tests for the declarative Plan-Modus grouping (design §C).

The framework config ``config/spec-plan-groups.yaml`` is the single seed for
every Plan-Modus aspect. These tests lock in three guarantees:

1. Schema: the YAML is parseable, complete, uses the closed ``mechanism`` enum
   and only the allowed ``enabled-when`` operands; every declared
   ``config-path`` is textually referenced by its consumer.
2. Seed consistency: for a config matrix the resolver returns the expected
   aspect bools, seed-equal aspects all equal ``enabled`` and ``seed=False``
   implies no aspect is ``True``.
3. Consumer ratchet: the real consumer of each aspect is observed and must
   match the resolved aspect bool -- no aspect can drift independently.
"""

import importlib
import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.config import _build_dod_variables  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402
from lib.consistency.spec_plan import check_spec_plan_workflow  # noqa: E402
from lib.dod import (
    SPEC_PLAN_WHEN_OPERANDS,
    resolve_dod,
    resolve_spec_plan_bundle,
)  # noqa: E402
from lib.io import _load_yaml_or_json  # noqa: E402
from lib.knowledge import sync_knowledge_engine  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.pipelines import inject_pipeline_blocks  # noqa: E402
from lib.rules import collect_rule_sources  # noqa: E402
from lib.spec_plan_scaffold import scaffold_spec_plan_dirs  # noqa: E402

GROUPS_PATH = REPO_ROOT / "config" / "spec-plan-groups.yaml"
GROUP_ID = "plan-mode"

REQUIRED_FIELDS = ("id", "mechanism", "config-path", "enabled-when", "consumer")

MECHANISM_ENUM = {
    "rule-gate",
    "pipeline-stage-condition",
    "sync-scaffold",
    "template-conditional",
    "validator-noop",
    "knowledge-engine-auto-write",
    "dod-flag",
}

# Derived from the resolver's closed operand set so a new operand cannot be
# added on one side only (drift guard).
ALLOWED_OPERANDS = set(SPEC_PLAN_WHEN_OPERANDS)

# Seed-equal: on whenever the seed is on.
SEED_EQUAL_ASPECTS = (
    "rules-channel",
    "pipeline-gating",
    "scaffold",
    "template-conditional",
    "consistency-noop",
)
# Neither seed-equal nor KE-coupled: depends on an additional resolved DoD flag.
DOD_ASPECTS = ("dod-traceability",)
KE_ASPECTS = ("ke-auto-index", "ke-auto-log")
ALL_ASPECTS = SEED_EQUAL_ASPECTS + DOD_ASPECTS + KE_ASPECTS

_WHEN_TOKENS = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*|'[^']*'|==|.")


# --------------------------------------------------------------------------- #
# fixtures / helpers
# --------------------------------------------------------------------------- #

def _group() -> dict:
    data, path = _load_yaml_or_json(GROUPS_PATH)
    assert path == GROUPS_PATH, "spec-plan-groups.yaml not loaded from the repo"
    return data["groups"][GROUP_ID]


def _meta_root(tmp_path: Path, required: bool) -> Path:
    """Minimal agent-meta root (dod-presets only; no spec-plan-groups.yaml).

    The missing grouping config exercises the resolver's fail-safe fallback,
    which mirrors the framework YAML (see test_fallback_group_matches_yaml).
    """
    root = tmp_path / "agent-meta"
    config_dir = root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "dod-presets.yaml").write_text(
        "presets:\n"
        "  full:\n"
        f"    spec-plan-required: {str(required).lower()}\n"
        "    spec-plan-traceability: false\n"
        '    se-required: "false"\n',
        encoding="utf-8",
    )
    return root


def _consumer_root(tmp_path: Path, required: bool) -> Path:
    """Root with the gate-rule + rule-gates fixture from test_rules_activation_gate."""
    root = _meta_root(tmp_path, required)
    rules_dir = root / "rules" / "1-generic"
    rules_dir.mkdir(parents=True, exist_ok=True)
    (rules_dir / "spec-plan-workflow.md").write_text("# Spec/Plan rule\n", encoding="utf-8")
    (root / "config" / "rules-presets.yaml").write_text(
        "presets:\n"
        "  default: {}\n"
        "rule-gates:\n"
        "  spec-plan-workflow:\n"
        "    requires: spec-plan-workflow.enabled\n",
        encoding="utf-8",
    )
    return root


def _config(extra: dict) -> dict:
    config = {"platforms": []}
    config.update(extra)
    return config


# Explicit `enabled=True` wins; absent key falls back to the resolved DoD
# `spec-plan-required`; explicit `False` beats the DoD override.
_MATRIX = [
    ("explicit-true", {"spec-plan-workflow": {"enabled": True}}, False, True),
    ("explicit-false-over-preset-true",
     {"spec-plan-workflow": {"enabled": False}}, True, False),
    ("absent-preset-true", {}, True, True),
    ("absent-preset-false", {}, False, False),
    ("dod-override-true", {"dod": {"spec-plan-required": True}}, False, True),
    ("explicit-false-beats-dod-override",
     {"spec-plan-workflow": {"enabled": False},
      "dod": {"spec-plan-required": True}}, False, False),
    ("ke-on-seed-on",
     {"spec-plan-workflow": {"enabled": True, "index": {"mode": "knowledge-engine"}},
      "knowledge-engine": {"enabled": True}}, False, True),
    ("ke-off-seed-on",
     {"spec-plan-workflow": {"enabled": True, "index": {"mode": "knowledge-engine"}},
      "knowledge-engine": {"enabled": False}}, False, True),
]


def _expected_ke(config: dict, seed: bool) -> bool:
    ke_enabled = bool((config.get("knowledge-engine") or {}).get("enabled", False))
    index_mode = ((config.get("spec-plan-workflow") or {}).get("index") or {}).get(
        "mode", "knowledge-engine",
    )
    return seed and ke_enabled and index_mode == "knowledge-engine"


def _expected_dod_traceability(config: dict, seed: bool) -> bool:
    """The fixture preset ``full`` declares ``spec-plan-traceability: false``.

    A project ``dod`` override wins (same precedence as ``resolve_dod``); the
    effective aspect is the seed AND the resolved flag.
    """
    override = (config.get("dod") or {}).get("spec-plan-traceability")
    flag = False if override is None else bool(override)
    return seed and flag


# --------------------------------------------------------------------------- #
# 1. schema validation
# --------------------------------------------------------------------------- #

def test_groups_file_parses_and_contains_plan_mode():
    data, path = _load_yaml_or_json(GROUPS_PATH)
    assert path == GROUPS_PATH
    assert GROUP_ID in data.get("groups", {})


def test_aspects_have_required_fields_and_unique_ids():
    aspects = _group()["aspects"]
    ids = [aspect["id"] for aspect in aspects]
    assert len(ids) == len(set(ids)), "aspect ids must be unique"
    for aspect in aspects:
        for field in REQUIRED_FIELDS:
            assert aspect.get(field), f"{aspect.get('id')!r}: missing {field!r}"


def test_expected_aspect_ids_present():
    ids = {aspect["id"] for aspect in _group()["aspects"]}
    assert set(ALL_ASPECTS) <= ids


def test_mechanism_uses_closed_enum():
    for aspect in _group()["aspects"]:
        assert aspect["mechanism"] in MECHANISM_ENUM, (
            f"unknown mechanism {aspect['mechanism']!r}"
        )


def test_seed_sources_and_default_declared():
    seed = _group()["seed"]
    kinds = [source["kind"] for source in seed["sources"]]
    assert kinds == ["explicit", "dod"], (
        "seed precedence must be explicit spec-plan-workflow.enabled > dod.spec-plan-required"
    )
    assert seed["default"] is False


def test_enabled_when_only_uses_allowed_operands():
    for aspect in _group()["aspects"]:
        expr = aspect["enabled-when"]
        for match in _WHEN_TOKENS.finditer(expr):
            token = match.group(0)
            if token.isspace():
                continue
            if token == "==" or (token.startswith("'") and token.endswith("'")):
                continue
            if token in ("and", "or"):
                continue
            assert token in ALLOWED_OPERANDS, (
                f"{aspect['id']!r}: illegal operand {token!r} in {expr!r}"
            )


def test_eval_enabled_when_is_closed_no_eval(tmp_path):
    """The `enabled-when` interpreter rejects anything outside its grammar."""
    from lib.dod import _evaluate_enabled_when
    from lib.io import SyncConfigError

    context = {"seed": True, "ke.enabled": True, "index.mode": "knowledge-engine"}
    assert _evaluate_enabled_when("seed", context) is True
    assert _evaluate_enabled_when(
        "seed and ke.enabled and index.mode=='knowledge-engine'", context,
    ) is True
    assert _evaluate_enabled_when(
        "seed and dod.spec-plan-traceability",
        {**context, "dod.spec-plan-traceability": True},
    ) is True
    assert _evaluate_enabled_when("seed", {"seed": False, "ke.enabled": True,
                                           "index.mode": "off"}) is False
    for expression in ("__import__('os')", "seed == " , "seed and unknown.flag"):
        with pytest.raises(SyncConfigError):
            _evaluate_enabled_when(expression, context)


def _config_path_tokens(config_path: str) -> set[str]:
    tokens = {part for part in re.split(r"[.#/\s]+", config_path) if part}
    return tokens


def test_config_path_is_referenced_by_consumer():
    """Static text check: the consumer must mention a token of its config-path."""
    for aspect in _group()["aspects"]:
        consumer = aspect["consumer"]
        consumer_file = REPO_ROOT / consumer.split("::", 1)[0]
        assert consumer_file.is_file(), f"consumer {consumer!r} does not exist"
        text = consumer_file.read_text(encoding="utf-8")
        tokens = _config_path_tokens(aspect["config-path"])
        assert any(token in text for token in tokens), (
            f"{aspect['id']!r}: config-path {aspect['config-path']!r} is not "
            f"referenced by consumer {consumer!r}"
        )


def test_consumer_symbol_exists_in_module():
    """Ratchet: a ``module.py::symbol`` consumer must name a real symbol.

    The static config-path check above only proves the file exists and mentions
    a token; it would accept a phantom symbol. Import the referenced module and
    assert the symbol is actually defined so a phantom consumer fails here.
    """
    for aspect in _group()["aspects"]:
        consumer = aspect["consumer"]
        if "::" not in consumer:
            continue
        file_part, symbol = consumer.split("::", 1)
        if not file_part.endswith(".py"):
            continue
        module_name = file_part[:-3].replace("/", ".")
        if module_name.startswith("scripts."):
            module_name = module_name[len("scripts."):]
        module = importlib.import_module(module_name)
        assert hasattr(module, symbol), (
            f"{aspect['id']!r}: consumer {consumer!r} names a symbol that does "
            f"not exist in {module_name!r}"
        )


def test_fallback_group_matches_yaml():
    """The in-code fail-safe fallback must not drift from the framework YAML."""
    from lib.dod import (
        _SPEC_PLAN_FALLBACK_ASPECTS,
        _SPEC_PLAN_FALLBACK_SEED_SOURCES,
    )

    yaml_sources = [
        (source["config-path"], source["kind"]) for source in _group()["seed"]["sources"]
    ]
    assert yaml_sources == list(_SPEC_PLAN_FALLBACK_SEED_SOURCES)
    yaml_aspects = [
        (aspect["id"], aspect["enabled-when"]) for aspect in _group()["aspects"]
    ]
    assert yaml_aspects == list(_SPEC_PLAN_FALLBACK_ASPECTS)


# --------------------------------------------------------------------------- #
# 2. seed consistency matrix
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "case,extra,required,expected", _MATRIX, ids=[case for case, *_ in _MATRIX],
)
def test_seed_matrix(tmp_path, case, extra, required, expected):
    root = _meta_root(tmp_path, required)
    config = _config(extra)
    bundle = resolve_spec_plan_bundle(config, root)

    assert bundle["enabled"] is expected

    for aspect in SEED_EQUAL_ASPECTS:
        assert bundle[aspect] == bundle["enabled"], f"{aspect} drifted from the seed"
        assert bundle[aspect] is expected

    expected_dod = _expected_dod_traceability(config, expected)
    for aspect in DOD_ASPECTS:
        assert bundle[aspect] is expected_dod, f"{aspect} DoD coupling broken"

    expected_ke = _expected_ke(config, expected)
    for aspect in KE_ASPECTS:
        assert bundle[aspect] is expected_ke, f"{aspect} KE coupling broken"


@pytest.mark.parametrize(
    "case,extra,required,expected", _MATRIX, ids=[case for case, *_ in _MATRIX],
)
def test_seed_false_implies_no_aspect_true(tmp_path, case, extra, required, expected):
    root = _meta_root(tmp_path, required)
    bundle = resolve_spec_plan_bundle(_config(extra), root)
    if not bundle["enabled"]:
        assert not any(value for key, value in bundle.items() if key != "enabled"), (
            "seed=False must switch off every aspect"
        )


def test_bundle_exposes_exactly_seed_and_all_aspects(tmp_path):
    root = _meta_root(tmp_path, required=False)
    bundle = resolve_spec_plan_bundle(_config({}), root)
    assert set(bundle) == {"enabled", *ALL_ASPECTS}


# --------------------------------------------------------------------------- #
# 3. consumer ratchet
# --------------------------------------------------------------------------- #

def _observe_ke(root: Path, project_root: Path, config: dict) -> bool:
    """Observe the KE auto-write consumer (one observer for both KE aspects).

    ``sync_knowledge_engine`` is a no-op exactly when the KE enable-gate is off;
    a pre-created bundle keeps ``generate_schema`` (which needs a template under
    the agent-meta root) out of the way, so the observation is the gate the
    ``ke-auto-*`` aspects model.
    """
    (project_root / "knowledge").mkdir(parents=True, exist_ok=True)
    log = SyncLog()
    sync_knowledge_engine(root, project_root, config, log, dry_run=True)
    disabled = any(
        "knowledge-engine" in entry and "disabled" in entry for entry in log.skipped
    )
    return not disabled


def _observe_dod_traceability(root: Path, project_root: Path, config: dict) -> bool:
    """Observe strict traceability via the consistency consumer.

    A plan referencing an existing design spec but leaving the ``spec-id:`` anchor
    unreferenced yields a ``spec_plan_traceability`` finding whose severity is
    ERROR exactly when the resolved ``dod-traceability`` aspect is on.
    """
    spec = project_root / "docs" / "specs" / "2027-01-01-demo-design.md"
    plan = project_root / "docs" / "plans" / "2027-01-01-demo.md"
    spec.parent.mkdir(parents=True, exist_ok=True)
    plan.parent.mkdir(parents=True, exist_ok=True)
    spec.write_text("# Demo Design\n\nspec-id: SPEC-1\n", encoding="utf-8")
    plan.write_text(
        "# Demo Plan\n\n"
        "**Spec:** docs/specs/2027-01-01-demo-design.md\n\n"
        "> Status: APPROVED\n\n"
        "### Task 1 — implement demo\n"
        "Agent: developer\n"
        "Modify: src/demo.py\n",
        encoding="utf-8",
    )
    findings = check_spec_plan_workflow(project_root, config, agent_meta_root=root)
    return any(
        finding.check == "spec_plan_traceability"
        and finding.severity == Severity.ERROR
        for finding in findings
    )


@pytest.mark.parametrize(
    "case,extra,required,expected", _MATRIX, ids=[case for case, *_ in _MATRIX],
)
def test_consumer_ratchet(tmp_path, case, extra, required, expected):
    root = _consumer_root(tmp_path, required)
    config = _config(extra)
    bundle = resolve_spec_plan_bundle(config, root)

    # Rule gate: the gated rule must only be delivered when rules-channel is on.
    names = {name for _src, name in collect_rule_sources(root, [], config=config)}
    assert ("spec-plan-workflow.md" in names) == bundle["rules-channel"]

    # Pipeline gating: the conditional stage is only rendered when seed is on.
    pipelines = {
        "concept-driven-dev": {
            "enabled": True,
            "stages": [
                {
                    "id": "specify",
                    "agent": "concept-specifier",
                    "task": "Spec schreiben",
                    "mode": "conditional",
                    "condition": {"dod_flag": "spec-plan-enabled"},
                }
            ],
        }
    }
    rendered = inject_pipeline_blocks(
        "{{PIPELINE_DETAIL_BLOCKS}}", pipelines, "Claude", resolve_dod(config, root),
    )
    assert ("concept-specifier" in rendered) == bundle["pipeline-gating"]

    # Scaffold: dry-run logs a CREATE action only when the aspect is on.
    log = SyncLog()
    scaffold_spec_plan_dirs(root, tmp_path / "scaffold-proj", config, log, dry_run=True)
    observed_scaffold = any("spec-plan scaffolding" in action for action in log.actions)
    assert observed_scaffold == bundle["scaffold"]

    # Template conditional: SPEC_PLAN_WORKFLOW_ENABLED is the seed projection.
    variables: dict = {}
    _build_dod_variables(variables, config, root)
    assert (variables["SPEC_PLAN_WORKFLOW_ENABLED"] == "true") == bundle["template-conditional"]

    # Consistency validator: disabled -> early no-op even with broken artifacts.
    project_root = tmp_path / "consistency-proj"
    plans_dir = project_root / "docs" / "plans"
    plans_dir.mkdir(parents=True)
    (plans_dir / "2026-01-01-demo.md").write_text("TBD\n", encoding="utf-8")
    findings = check_spec_plan_workflow(
        project_root, config, agent_meta_root=root,
    )
    assert bool(findings) == bundle["consistency-noop"]

    # ke-auto-index / ke-auto-log (spec §C.4.3: every aspect).
    observed_ke = _observe_ke(root, tmp_path / "ke-proj", config)
    assert observed_ke == bundle["ke-auto-index"] == bundle["ke-auto-log"]

    # dod-traceability: enforcement severity follows the resolved aspect.
    observed_trace = _observe_dod_traceability(root, tmp_path / "trace-proj", config)
    assert observed_trace == bundle["dod-traceability"]


def test_dod_traceability_aspect_follows_resolved_flag(tmp_path):
    """The aspect tracks seed AND the resolved DoD flag (M3)."""
    root = _meta_root(tmp_path, required=True)
    on = _config({
        "spec-plan-workflow": {"enabled": True},
        "dod": {"spec-plan-traceability": True},
    })
    bundle_on = resolve_spec_plan_bundle(on, root)
    assert bundle_on["enabled"] is True
    assert bundle_on["dod-traceability"] is True

    # Explicit workflow off wins over the DoD flag -> aspect off.
    off = _config({
        "spec-plan-workflow": {"enabled": False},
        "dod": {"spec-plan-traceability": True},
    })
    bundle_off = resolve_spec_plan_bundle(off, root)
    assert bundle_off["enabled"] is False
    assert bundle_off["dod-traceability"] is False
