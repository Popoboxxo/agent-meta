"""AC-38 / QG-10 (SPEC-CONTEXT-PROFILES-2026-10-11, Task 0d.5): doctor seed fixtures.

Every registry seed (``config/known-issues.yaml``) owns a fixture directory
``tests/fixtures/doctor/<seed-id>/{positive,negative}/``:

* ``positive`` => at least one finding with ``check == doctor.<seed-id>``;
* ``negative`` => no finding with that check.

A fixture directory is a tiny project tree whose ``.meta-config/project.yaml`` is
the doctor config. A seed with several cases (``tmp-sink-not-gitignored`` a, a',
b-e; ``tmp-sink-outside-repo-or-system-temp`` AC-96) keeps one sub-directory per
case below ``positive/`` or ``negative/``. The doctor runs in-process
(``run_doctor``; the CLI is covered by ``test_doctor_cli.py``); the active set,
registry load and ``subprocess`` are the only things stubbed, see ``_run_case``.

Coverage matrix (30 seeds): all seeds are fixturable. Seeds that need a stub
because the real environment cannot be put into a small tree are marked
``STUBBED`` below with the reason; ``NOT_FIXTURABLE`` is empty on purpose and
exists so that a future gap must be named with a reason instead of silently
dropped (the meta test fails for any seed that has neither fixtures nor an entry).
"""

import copy
import hashlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib import doctor, doctor_detectors  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402

FIXTURE_ROOT = _ROOT / "tests" / "fixtures" / "doctor"
PROJECT_CONFIG = Path(".meta-config") / "project.yaml"
_REGISTRY = yaml.safe_load((_ROOT / "config" / "known-issues.yaml").read_text(encoding="utf-8"))
SEED_IDS = [e["id"] for e in _REGISTRY["issues"]]

# Seed id -> reason. A seed listed here needs no fixture directory.
NOT_FIXTURABLE = {}

# Seeds whose detector cannot be driven by a small tree alone (stub in _run_case).
STUBBED = {
    "sync-pending": "detector kind `command`: `sync.py --check` takes ~25 s on the "
                    "self-hosting tree; subprocess.run is stubbed (exit 1 / exit 0)",
    "schema-validation-skipped": "depends on whether `jsonschema` is installed; "
                                 "importlib.util.find_spec is stubbed per case",
    "surface-unverified": "every shipped provider has UNVERIFIED surfaces with a target key, "
                          "so the negative needs a capability matrix with verified surfaces",
    "rule-unreachable": "IC-15 Nr. 8 retired the unread rules dirs, so no shipped provider "
                        "writes a rules dir it does not read any more; the positive case "
                        "reconstructs the retired Gemini `.gemini/rules` shape via "
                        "STUB_CAPABILITIES",
    "unread-channel": "same retirement as `rule-unreachable`; the positive case reconstructs "
                      "the retired Gemini `.gemini/rules` shape via STUB_CAPABILITIES",
}

# Per-seed provider-capability stubs for fixtures whose defect no longer exists in a
# shipped provider (IC-15 Nr. 8: Gemini/Mammouth/Codex retired their unread rules
# dirs). The checks stay as they are; only the fixture's provider shape is restored
# so a positive case still produces a finding and a negative case still exercises the
# reachable/clean path.
STUB_CAPABILITIES = {
    "rule-unreachable": {
        "Gemini": {"has_rules": True, "rules_dir": ".gemini/rules"},
    },
    "unread-channel": {
        "Gemini": {"has_rules": True, "rules_dir": ".gemini/rules"},
    },
}

# finding-ref seeds: referenced check id that a positive must carry in `ref_check`.
EXPECTED_REF = {
    "dangling-pointer": "context.dangling-pointer",
    "rule-unreachable": "context.rule-unreachable",
    "unread-channel": "context.unread-channel",
    "dangling-role-dispatch": "active-set.dangling-dispatch",
    "gate-dropped-allowlist-role": "active-set.gate-dropped",
    "unresolved-placeholder-in-output": "active-set.unresolved-placeholder",
    "hooks-not-registered": "hooks.enabled-but-not-registered",
    "schema-validation-skipped": "doctor.environment",
    "declared-surface-empty": "context.declared-surface-empty",
    "legacy-artifact-present": "context.legacy-artifact-present",
    "routing-examples-language-fallback": "routing.examples-language-fallback",
    "routing-keyword-overlap-active": "routing.keyword-overlap",
    "tmp-sink-outside-repo-or-system-temp": "doctor.tmp-sink-location",
}

# (seed, case dir name): negatives for which the predicate legitimately skips the seed.
NEGATIVE_PREDICATE_SKIP = {
    ("dead-variable-code-quality-rules", "negative"),   # variable absent => entry n/a (single case dir)
    ("tmp-sink-not-gitignored", "e-sink-disabled"),     # AC-76 (e): sink disabled
    ("repo-containment-block-missing", "negative"),     # block present => entry n/a
}


# --------------------------------------------------------------------- helpers

def _cases(seed, kind):
    """Case directories of ``<seed>/<kind>``: the dir itself or its case sub-dirs."""
    base = FIXTURE_ROOT / seed / kind
    if (base / PROJECT_CONFIG).is_file():
        return [base]
    if not base.is_dir():
        return []
    return sorted(p for p in base.iterdir() if (p / PROJECT_CONFIG).is_file())


def _param_list():
    params = []
    for seed in SEED_IDS:
        for kind in ("positive", "negative"):
            for case in _cases(seed, kind):
                label = kind if case == FIXTURE_ROOT / seed / kind else f"{kind}-{case.name}"
                params.append(pytest.param(seed, kind, case, id=f"AC-38-{seed}-{label}"))
    return params


def _tree_digest(root):
    digest = hashlib.sha256()
    for path in sorted(Path(root).rglob("*")):
        digest.update(path.relative_to(root).as_posix().encode())
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()


_CACHE = {}


_REAL = {
    "load_known_issues": doctor.load_known_issues,
    "compute_active_set": doctor.compute_active_set,
    "load_provider_capabilities": doctor.load_provider_capabilities,
    "find_spec": importlib.util.find_spec,
}


def _cached_active_set(config, agent_meta_root, project_root, **kwargs):
    key = repr(sorted((k, repr(v)) for k, v in config.items()))
    if key not in _CACHE:
        _CACHE[key] = _REAL["compute_active_set"](config, agent_meta_root, project_root, **kwargs)
    return _CACHE[key]


def _run_case(project, seed, kind, providers=None):
    """Run the doctor in-process on a fixture project; the fixture tree is never modified."""
    config = yaml.safe_load((project / PROJECT_CONFIG).read_text(encoding="utf-8")) or {}
    before = _tree_digest(project)
    positive = kind == "positive"

    def fake_run(cmd, **kwargs):                 # `command` detector: no real sync.py run
        assert "--dry-run" in cmd and shell_free(kwargs)
        return SimpleNamespace(returncode=1 if (positive and seed == "sync-pending") else 0,
                               stdout="", stderr="")

    def shell_free(kwargs):
        return kwargs.get("shell") is False

    def fake_find_spec(name, *args, **kwargs):
        if name == "jsonschema":
            return None if (positive and seed == "schema-validation-skipped") else object()
        return _REAL["find_spec"](name, *args, **kwargs)

    def fake_capabilities(agent_meta_root):      # all surfaces verified (surface-unverified negative)
        caps = copy.deepcopy(_REAL["load_provider_capabilities"](agent_meta_root))
        if seed == "surface-unverified" and not positive:
            for entry in caps.values():
                entry["surface_verified_state"] = {
                    k: "DOCUMENTED" for k in entry.get("surface_verified_state", {})}
        for provider, overrides in STUB_CAPABILITIES.get(seed, {}).items():
            caps.setdefault(provider, {}).update(overrides)
        return caps

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(doctor, "load_known_issues", _cached_registry)
        mp.setattr(doctor, "compute_active_set", _cached_active_set)
        mp.setattr(doctor, "load_provider_capabilities", fake_capabilities)
        mp.setattr(doctor_detectors.subprocess, "run", fake_run)
        mp.setattr(importlib.util, "find_spec", fake_find_spec)
        report = doctor.run_doctor(project, _ROOT, config, providers=providers)
    assert _tree_digest(project) == before, "the doctor must not write into the project tree"
    return report


def _cached_registry(root):
    if "registry" not in _CACHE:
        _CACHE["registry"] = _REAL["load_known_issues"](root)
    entries, invalid = _CACHE["registry"]
    return list(entries), list(invalid)       # the runner appends to the findings list


def _of(report, seed):
    return [f for f in report.findings if f.check == "doctor." + seed]


def _skip_reasons(report, seed):
    return {reason for issue, reason in report.skipped if issue == seed}


# ------------------------------------------------------------------ meta tests

def test_ac38_registry_loads_without_invalid_entries():
    entries, invalid = _REAL["load_known_issues"](_ROOT)
    assert invalid == []
    assert [e["id"] for e in entries] == SEED_IDS


def test_ac38_every_registry_seed_is_in_the_fixture_matrix():
    """A new seed without fixtures (or a named NOT_FIXTURABLE reason) turns this red."""
    missing = []
    for seed in SEED_IDS:
        if seed in NOT_FIXTURABLE:
            assert NOT_FIXTURABLE[seed].strip(), f"{seed}: NOT_FIXTURABLE needs a reason"
            continue
        for kind in ("positive", "negative"):
            if not _cases(seed, kind):
                missing.append(f"{seed}/{kind}")
    assert missing == [], f"seeds without fixtures: {missing}"


def test_ac38_fixture_directories_are_exactly_the_seed_ids():
    on_disk = sorted(p.name for p in FIXTURE_ROOT.iterdir() if p.is_dir())
    expected = sorted(s for s in SEED_IDS if s not in NOT_FIXTURABLE)
    assert on_disk == expected


def test_ac38_matrix_tables_reference_only_registry_seeds():
    for table in (NOT_FIXTURABLE, STUBBED, EXPECTED_REF):
        assert set(table) <= set(SEED_IDS)
    assert all(reason.strip() for reason in STUBBED.values())


# ------------------------------------------------------ positive / negative

@pytest.mark.parametrize("seed,kind,case", _param_list())
def test_ac38_seed_fixture_matches_expected_finding_count(seed, kind, case):
    report = _run_case(case, seed, kind)
    findings = _of(report, seed)
    skipped = _skip_reasons(report, seed)
    # a detector that could not run (or an invalid entry) must never pass as "0 findings"
    assert not skipped & {"detector-unavailable", "registry-invalid"}, skipped
    if kind == "positive":
        assert findings, f"{seed}: positive fixture {case.name} produced no finding"
        assert not skipped, f"{seed}: positive fixture skipped the seed: {skipped}"
        assert {f.issue_id for f in findings} == {seed}
        if seed in EXPECTED_REF:
            assert EXPECTED_REF[seed] in {f.ref_check for f in findings}
    else:
        assert findings == [], [(f.file, f.message) for f in findings]
        if (seed, case.name) not in NEGATIVE_PREDICATE_SKIP:
            assert "predicate" not in skipped, f"{seed}: negative skipped by predicate"


# ---------------------------------------------------- seed-specific assertions

def test_ac76_tmp_sink_not_gitignored_reports_warning_for_cases_a_and_b():
    for case in _cases("tmp-sink-not-gitignored", "positive"):
        (finding,) = _of(_run_case(case, "tmp-sink-not-gitignored", "positive"),
                         "tmp-sink-not-gitignored")
        assert finding.severity is Severity.WARNING, case.name
        assert finding.file == ".gitignore", case.name


def test_ac76_case_a_prime_has_sink_gitignore_and_only_the_info_block_missing_seed():
    case = FIXTURE_ROOT / "tmp-sink-not-gitignored" / "negative" / "a-prime-no-block-sink-gitignore"
    config = yaml.safe_load((case / PROJECT_CONFIG).read_text(encoding="utf-8"))
    assert "repo_containment" not in config and (case / ".tmp" / ".gitignore").is_file()
    report = _run_case(case, "tmp-sink-not-gitignored", "negative")
    assert _of(report, "tmp-sink-not-gitignored") == []
    (info,) = _of(report, "repo-containment-block-missing")
    assert info.severity is Severity.INFO


def test_ac76_sink_path_is_read_from_the_config_not_assumed_to_be_dot_tmp():
    # case b: root .gitignore ignores `.tmp/`, but the configured sink is `scratch/out`
    case = FIXTURE_ROOT / "tmp-sink-not-gitignored" / "positive" / "b-block-wrong-root-entry"
    assert (case / ".gitignore").read_text(encoding="utf-8").strip() == ".tmp/"
    assert _of(_run_case(case, "tmp-sink-not-gitignored", "positive"), "tmp-sink-not-gitignored")


def test_ac77_variable_unreferenced_reports_key_and_length_but_never_the_value():
    case = FIXTURE_ROOT / "variable-unreferenced" / "positive"
    (finding,) = _of(_run_case(case, "variable-unreferenced", "positive"), "variable-unreferenced")
    value = "Ship early and often"
    assert "variables.TEAM_MOTTO" in finding.message
    assert f"length {len(value)}" in finding.message
    assert value not in finding.message and value not in finding.quoted
    assert finding.severity is Severity.WARNING


def test_ac77_code_quality_rules_yields_exactly_one_finding_from_its_own_seed():
    case = FIXTURE_ROOT / "dead-variable-code-quality-rules" / "positive"
    report = _run_case(case, "dead-variable-code-quality-rules", "positive")
    assert len(_of(report, "dead-variable-code-quality-rules")) == 1
    assert _of(report, "variable-unreferenced") == []     # dedupe: no second finding


def test_ac96_tmp_sink_outside_repo_is_an_error_naming_the_location_check():
    base = FIXTURE_ROOT / "tmp-sink-outside-repo-or-system-temp" / "positive"
    names = {c.name for c in _cases("tmp-sink-outside-repo-or-system-temp", "positive")}
    assert names == {"parent-traversal", "posix-absolute", "windows-drive", "unc-path",
                     "reserved-device-name"}
    for name in sorted(names):
        report = _run_case(base / name, "tmp-sink-outside-repo-or-system-temp", "positive")
        (finding,) = _of(report, "tmp-sink-outside-repo-or-system-temp")
        assert finding.severity is Severity.ERROR, name
        assert finding.ref_check == "doctor.tmp-sink-location", name
        assert finding.check == "doctor.tmp-sink-outside-repo-or-system-temp", name


def test_ac96_default_and_scratch_out_sinks_are_accepted():
    names = {c.name for c in _cases("tmp-sink-outside-repo-or-system-temp", "negative")}
    assert names == {"default-without-block", "scratch-out"}


@pytest.fixture()
def dynamic_project():
    """A project dir inside the repo sink (`.tmp`), i.e. NOT under the system temp dir."""
    sink = _ROOT / ".tmp"
    sink.mkdir(exist_ok=True)
    project = Path(tempfile.mkdtemp(prefix="doctor-fixture-", dir=str(sink)))
    yield project
    shutil.rmtree(project, ignore_errors=True)


def _symlink_sink(project, target):
    try:
        os.symlink(target, project / "sinklink", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are not available")
    (project / ".meta-config").mkdir()
    (project / PROJECT_CONFIG).write_text(
        "ai-providers: [Claude]\nrepo_containment:\n  enabled: true\n  tmp-sink:\n"
        "    enabled: true\n    path: sinklink\n    gitignore: true\n    cleanup: false\n",
        encoding="utf-8")


def test_ac96_symlink_sink_pointing_outside_the_root_is_an_error(dynamic_project):
    outside = _ROOT.parent                       # outside the repo, not the system temp dir
    if os.path.realpath(tempfile.gettempdir()) in os.path.realpath(str(outside)) + os.sep:
        pytest.skip("repo parent lives under the system temp dir")
    _symlink_sink(dynamic_project, outside)
    report = _run_case(dynamic_project, "tmp-sink-outside-repo-or-system-temp", "positive")
    (finding,) = _of(report, "tmp-sink-outside-repo-or-system-temp")
    assert finding.severity is Severity.ERROR


def test_ac96_symlink_sink_resolving_into_system_temp_is_an_error(dynamic_project):
    temp_real = os.path.realpath(tempfile.gettempdir())
    if os.path.realpath(str(_ROOT)).startswith(temp_real + os.sep):
        pytest.skip("repo itself lives under the system temp dir")
    target = tempfile.mkdtemp(prefix="doctor-sink-target-")
    try:
        _symlink_sink(dynamic_project, target)
        report = _run_case(dynamic_project, "tmp-sink-outside-repo-or-system-temp", "positive")
        (finding,) = _of(report, "tmp-sink-outside-repo-or-system-temp")
        assert finding.severity is Severity.ERROR
        assert finding.ref_check == "doctor.tmp-sink-location"
    finally:
        shutil.rmtree(target, ignore_errors=True)
