"""Role-routing eval corpus (IC-13, AC-03, AC-62 corpus part).

Pure offline checks: no LLM call, no network. The corpus is generated from
``config/role-defaults.yaml`` by ``scripts/gen_role_routing_eval_catalog.py``;
curated extras live in ``tests/routing-llm-eval/roles/catalog.manual.yaml``.
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pytest
import yaml

from scripts import gen_role_routing_eval_catalog as gen
from scripts.lib.roles import load_roles_config

REPO_ROOT = Path(__file__).resolve().parents[1]
ROLES_DIR = REPO_ROOT / "tests" / "routing-llm-eval" / "roles"
GENERATED = ROLES_DIR / "catalog.generated.yaml"
MANUAL = ROLES_DIR / "catalog.manual.yaml"
PROMPTFOO = ROLES_DIR / "promptfooconfig.generated.yaml"


def _known_overlaps() -> dict:
    """Read KNOWN_KEYWORD_OVERLAPS from tests/test_routing_overlap.py (no duplicate)."""
    path = REPO_ROOT / "tests" / "test_routing_overlap.py"
    spec = importlib.util.spec_from_file_location("_routing_overlap_ref", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.KNOWN_KEYWORD_OVERLAPS


def _norm(token: object) -> str:
    return str(token).strip().casefold()


@pytest.fixture(scope="module")
def roles() -> dict:
    return load_roles_config(REPO_ROOT)["roles"]


@pytest.fixture(scope="module")
def generated_cases() -> list:
    return yaml.safe_load(GENERATED.read_text(encoding="utf-8"))["cases"]


@pytest.fixture(scope="module")
def manual_cases() -> list:
    return yaml.safe_load(MANUAL.read_text(encoding="utf-8"))["cases"]


@pytest.fixture(scope="module")
def all_cases(generated_cases, manual_cases) -> list:
    return generated_cases + manual_cases


def test_ac03_case_schema_target_and_tier_escalation(all_cases):
    """[AC-03] every case carries expected {target, tier_escalation}."""
    ids = [c["id"] for c in all_cases]
    assert len(ids) == len(set(ids)), "duplicate case ids"
    for case in all_cases:
        exp = case["expected"]
        assert set(exp) == {"target", "tier_escalation"}, case["id"]
        assert isinstance(exp["target"], str) and exp["target"], case["id"]
        assert isinstance(exp["tier_escalation"], bool), case["id"]
        assert case["lang"] in {"de", "en", "mixed"}, case["id"]
        assert case["task"].strip(), case["id"]


def test_ac62_every_keyword_and_example_is_covered(roles, all_cases):
    """[AC-62] each keyword/example in role-defaults is covered by >=1 case."""
    kw_cov = {(c["role"], c["source_keyword"]) for c in all_cases if "source_keyword" in c}
    ex_cov = {(c["role"], c["source_example"]) for c in all_cases if "source_example" in c}
    missing = []
    for name, info in roles.items():
        if (info.get("routing") or {}).get("addressability") in ("name_only", "excluded"):
            continue  # name_only roles are addressed by name only (Q9)
        patterns = info.get("routing_patterns") or {}
        missing += [(name, "kw", k) for k in patterns.get("keywords") or [] if (name, k) not in kw_cov]
        missing += [(name, "ex", e) for e in patterns.get("examples") or [] if (name, e) not in ex_cov]
    assert not missing, missing[:10]


def test_ac62_at_least_20_roles_have_de_and_en_paraphrases(all_cases):
    """[AC-62] curated paraphrases: >=20 roles with both DE and EN cases."""
    langs = defaultdict(set)
    for case in all_cases:
        if case["category"] == "paraphrase":
            langs[case["role"]].add(case["lang"])  # mixed never counts as en
    both = sorted(r for r, ls in langs.items() if {"de", "en"} <= ls)
    assert len(both) >= 20, both


def test_ac62_language_pairs_share_target_and_are_balanced(all_cases):
    """[AC-62] language delta only on pair_id pairs: same target, DE == EN count."""
    pairs = gen.language_pairs({"cases": all_cases})
    assert len(pairs) >= 20
    for de, en in pairs:
        assert de["pair_id"] == en["pair_id"]
        assert de["expected"] == en["expected"], de["pair_id"]
        assert (de["lang"], en["lang"]) == ("de", "en")
    manual_paired = [c for c in all_cases if c["id"].startswith("m-")]
    assert Counter(c["lang"] for c in manual_paired) == {"de": len(manual_paired) // 2, "en": len(manual_paired) // 2}
    # every pair_id has exactly one DE and one EN case
    by_pair = Counter(c["pair_id"] for c in all_cases if "pair_id" in c)
    assert set(by_pair.values()) == {2}


def test_ac62_mixed_cases_have_no_pair_id(all_cases):
    """[AC-62] English-framed DE-keyword cases are 'mixed' and never paired."""
    mixed = [c for c in all_cases if c["lang"] == "mixed"]
    assert mixed
    assert not [c["id"] for c in mixed if "pair_id" in c]


def test_ac62_all_pattern_roles_have_de_and_en_cases(roles, all_cases):
    """[AC-62] every keyword-routable pattern role has DE and EN-framed (en/mixed) cases."""
    langs = defaultdict(set)
    for case in all_cases:
        langs[case["role"]].add(case["lang"])
    gaps = [
        n for n, i in roles.items()
        if (i.get("routing_patterns") or {}).get("keywords")
        and (i.get("routing") or {}).get("addressability") == "keyword"
        and not ("de" in langs[n] and langs[n] & {"en", "mixed"})
    ]
    assert not gaps, gaps


def test_ac62_each_overlap_token_has_at_least_two_cases(all_cases):
    """[AC-62] >=2 cases per KNOWN_KEYWORD_OVERLAPS token (IC-29)."""
    counts = Counter(c["overlap_token"] for c in all_cases if "overlap_token" in c)
    overlaps = _known_overlaps()
    assert overlaps
    short = {t: counts.get(_norm(t), 0) for t in overlaps if counts.get(_norm(t), 0) < 2}
    assert not short, short


def test_ac62_overlap_cases_cover_each_owner_role(all_cases):
    """[AC-62] every owner role of an overlap token is a target of a case for it."""
    targets = defaultdict(set)
    for case in all_cases:
        if "overlap_token" in case:
            targets[case["overlap_token"]].add(case["expected"]["target"])
    for token, owners in _known_overlaps().items():
        assert set(owners) <= targets[_norm(token)], token


def test_ac62_name_only_roles_have_direct_addressing_cases(roles, all_cases):
    """[AC-62] name_only roles: direct-address cases in DE and EN."""
    name_only = [n for n, i in roles.items() if (i.get("routing") or {}).get("addressability") == "name_only"]
    assert name_only
    for name in name_only:
        mine = [c for c in all_cases if c["category"] == "name_only" and c["expected"]["target"] == name]
        assert {c["lang"] for c in mine} == {"de", "en"}, name
        assert all(name in c["task"] for c in mine), name
        positives = [c["id"] for c in all_cases
                     if c["role"] == name and ("source_keyword" in c or "source_example" in c)]
        assert not positives, positives  # direct addressing only (Q9)


def test_ac62_excluded_roles_are_never_targets(roles, all_cases):
    """[AC-62] orchestrator (excluded) is never an expected target."""
    excluded = {n for n, i in roles.items() if (i.get("routing") or {}).get("addressability") == "excluded"}
    assert excluded
    assert not [c["id"] for c in all_cases if c["expected"]["target"] in excluded]


def test_ac62_tier_escalation_matches_orchestrator_only(roles, generated_cases):
    """[AC-62] generated tier_escalation == routing.orchestrator_only of the target role."""
    for case in generated_cases:
        target = case["expected"]["target"]
        if target in roles:
            want = bool((roles[target].get("routing") or {}).get("orchestrator_only"))
            assert case["expected"]["tier_escalation"] is want, case["id"]


def test_ac62_targets_are_known_roles_pipelines_or_ask(roles, all_cases):
    """[AC-62] target is a role, ``pipeline:<name>`` or ASK."""
    for case in all_cases:
        target = case["expected"]["target"]
        assert target in roles or target == "ASK" or target.startswith("pipeline:"), case["id"]


def test_ac62_manual_catalog_is_short_and_justified(manual_cases):
    """[AC-62] manual cases are hand-written extras, each with a reason."""
    assert 0 < len(manual_cases) <= 120
    for case in manual_cases:
        assert case.get("reason", "").strip(), case["id"]
        assert case["id"].startswith("m-"), case["id"]
        assert "source_keyword" not in case and "source_example" not in case, case["id"]


def test_ac62_generated_files_are_deterministic_and_drift_free(tmp_path):
    """[AC-62] regenerating yields byte-identical files (drift test)."""
    out = tmp_path / "roles"
    for _ in range(2):
        assert gen.main(["--out-dir", str(out)]) == 0
    for name in ("catalog.generated.yaml", "promptfooconfig.generated.yaml"):
        assert (out / name).read_bytes() == (ROLES_DIR / name).read_bytes(), name


def test_ac62_check_mode_passes_on_committed_files():
    """[AC-62] --check exits 0 when committed files are fresh."""
    assert gen.main(["--check"]) == 0


def test_ac62_generate_catalog_is_pure_and_matches_file(generated_cases):
    """[AC-62] generate_catalog() is stable and equals the committed corpus."""
    first = gen.generate_catalog(REPO_ROOT)
    assert first == gen.generate_catalog(REPO_ROOT)
    assert first["cases"] == generated_cases


def test_ac62_manual_catalog_is_merged_unchanged_into_promptfoo():
    """[AC-62] promptfoo config references every manual case verbatim."""
    manual = yaml.safe_load(MANUAL.read_text(encoding="utf-8"))["cases"]
    config = yaml.safe_load(PROMPTFOO.read_text(encoding="utf-8"))
    by_desc = {t["description"]: t for t in config["tests"]}
    for case in manual:
        test = by_desc[f"{case['id']} [{case['role']}]"]
        assert test["vars"]["prompt"] == case["task"]
    generated = yaml.safe_load(GENERATED.read_text(encoding="utf-8"))["cases"]
    assert len(config["tests"]) == len(generated) + len(manual)


def test_ac62_corpus_hash_covers_generated_and_manual(capsys, tmp_path):
    """[AC-62] corpus hash = sha256 over generated+manual; manual change alters it."""
    expected = gen.corpus_hash(ROLES_DIR)
    assert len(expected) == 64
    assert gen.main(["--print-hash"]) == 0
    assert capsys.readouterr().out.strip() == expected
    copy = tmp_path / "roles"
    copy.mkdir()
    for name in ("catalog.generated.yaml", "catalog.manual.yaml"):
        (copy / name).write_bytes((ROLES_DIR / name).read_bytes())
    assert gen.corpus_hash(copy) == expected
    manual = (copy / "catalog.manual.yaml")
    manual.write_text(manual.read_text(encoding="utf-8").replace("Make it better.", "Improve it."),
                      encoding="utf-8")
    assert gen.corpus_hash(copy) != expected


def test_ac62_excluded_and_name_only_roles_own_no_overlap_token(roles):
    """[AC-62] excluded/name_only roles are never overlap owners."""
    owners = set().union(*gen._overlap_index(roles).values())
    skipped = {n for n, i in roles.items()
               if (i.get("routing") or {}).get("addressability") in ("excluded", "name_only")}
    assert not owners & skipped


def test_ac62_promptfoo_providers_use_exec_id_form():
    """[bug #977] promptfoo needs ``id: exec:<script>`` and no ``command`` field.

    The provider script path is resolved relative to the config file's
    directory (``ROLES_DIR``), hence the ``../`` prefix in the generated id.
    """
    config = yaml.safe_load(PROMPTFOO.read_text(encoding="utf-8"))
    assert config["providers"], "no providers in generated config"
    for provider in config["providers"]:
        assert "command" not in provider, (
            f"provider {provider!r} must not carry a command array (bug #977)"
        )
        assert provider["id"].startswith("exec:"), (
            f"provider id {provider['id']!r} must be 'exec:<script>' (bug #977)"
        )
        script = ROLES_DIR / provider["id"].split(":", 1)[1]
        assert script.exists(), f"provider script missing: {script}"


def test_ac62_generated_header_marks_file_as_generated():
    """[AC-62] generated files carry a DO-NOT-EDIT header."""
    for path in (GENERATED, PROMPTFOO):
        assert "GENERATED" in path.read_text(encoding="utf-8").splitlines()[0]


def test_ac62_generator_cli_runs_without_network(tmp_path):
    """[AC-62] CLI entry point works standalone (no LLM, no network)."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "gen_role_routing_eval_catalog.py"),
         "--out-dir", str(tmp_path / "o")],
        capture_output=True, text=True, check=False,
    )
    assert result.returncode == 0, result.stderr
