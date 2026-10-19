"""Config-optimizer runner + CLI (Task 21 / 2d.2).

Binding: ``docs/plans/2026-10-17-context-profiles-phase2-plan.md`` Task 21 and
``docs/specs/2026-10-11-context-profiles-spec.md`` IC-24/IC-25:
AC-54 (sink-only, self-hosted no-effect / dead-variable candidates),
AC-55 (L0 proof incl. comparison set), AC-57 (semantic hints, ``--include-semantic``),
AC-75/94/98 (sink discipline, no system temp, disabled sink), AC-89 (credential
exclusion), AC-91 (proposal fields / ``generator_options``).

Run: .venv-1/bin/python -m pytest tests/test_meta_optimizer_runner.py -q
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync.py"
MODULE = REPO_ROOT / "scripts" / "lib" / "meta_optimizer.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "meta-optimizer"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import meta_optimizer as mo  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402

SINK_PARTS = ("scratch", "out")
SINK_SUBDIR = ("scratch", "out", "meta-optimizer")
SEMANTIC_KINDS = {"duplicate-value", "relocate-to-ext", "relocate-to-doc", "semantic-merge"}
RUN_TIMEOUT = 900


# --- helpers ---------------------------------------------------------------

def _run(root: Path, cfg: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--config", str(cfg), *args],
        cwd=str(root), capture_output=True, text=True, timeout=RUN_TIMEOUT,
    )


def _snapshot(root: Path, skip: tuple) -> dict:
    out = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if path.is_file() and ".git" not in rel.parts and rel.parts[:len(skip)] != skip:
            out[rel.as_posix()] = path.read_bytes()
    return out


def _init_project(root: Path, text: str) -> Path:
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    cfg = root / ".meta-config" / "project.yaml"
    cfg.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    return cfg


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def _self_hosted_text() -> str:
    """The repo's own ``.meta-config/project.yaml``, sink redirected into the fixture."""
    data = yaml.safe_load((REPO_ROOT / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
    data["repo_containment"]["tmp-sink"]["path"] = "scratch/out"
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True)


def _run_dirs(root: Path) -> list:
    base = root.joinpath(*SINK_SUBDIR)
    return sorted(base.glob("*")) if base.is_dir() else []


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _sink_files(root: Path) -> list:
    """Every file below <sink>/meta-optimizer/ (the whole tree, review F1)."""
    base = root.joinpath(*SINK_SUBDIR)
    return sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []


# --- AC-94: guard -----------------------------------------------------------

def test_module_has_no_systemtemp_or_dot_tmp_literal():
    """AC-75/AC-94 grep guard over the new module (also bans a bare .tmp literal)."""
    text = MODULE.read_text(encoding="utf-8")
    assert not re.search(r"tempfile|gettempdir|/tmp|%TEMP%|TMPDIR|mkdtemp|\.tmp\b", text)


def test_advance_l0_and_semantic_kind_contract():
    """IC-25/AC-57: level progression and the hint-only kind set are stable."""
    assert [mo.advance_l0(level) for level in ("none", "L0", "L1", "L2", "L3")] == [
        "L0", "L1", "L2", "L3", "L3"]
    assert mo.advance_l0("bogus") == "L0"
    assert set(mo.SEMANTIC_KINDS) == SEMANTIC_KINDS
    assert mo.CONTENT_LOSS_THRESHOLD_BYTES == 200


# --- AC-54/55/75/94/98: self-hosted run -------------------------------------

@pytest.fixture(scope="module")
def optimized(tmp_path_factory):
    root = tmp_path_factory.mktemp("mo-self")
    cfg = _init_project(root, _self_hosted_text())
    before = _snapshot(root, SINK_PARTS)
    result = _run(root, cfg, "--optimize-config", "--json")
    runs = _run_dirs(root)
    assert runs, (result.stdout[-1500:], result.stderr[-2500:])
    run_dir = runs[-1]
    return {
        "root": root,
        "before": before,
        "result": result,
        "run_dir": run_dir,
        "proposal": _load(run_dir / "proposal.json"),
        "proof": _load(run_dir / "proof.json"),
    }


def test_cli_exit_zero_and_stdout_proposal(optimized):
    assert optimized["result"].returncode == 0, optimized["result"].stderr[-2500:]
    payload = json.loads(optimized["result"].stdout)
    assert payload["candidates"] == optimized["proposal"]["candidates"]
    assert "diff" not in payload  # the full diff lives in proposal.diff only


def test_only_sink_written_and_artifacts_present(optimized):
    """AC-54/AC-75: the runner writes exclusively below <sink>/meta-optimizer/<ts>/.

    Review F1 option (a): the render scratch is removed, so only the three
    artifacts remain.
    """
    root, run_dir = optimized["root"], optimized["run_dir"]
    assert _snapshot(root, SINK_PARTS) == optimized["before"]
    files = sorted(p.relative_to(run_dir).as_posix() for p in run_dir.rglob("*") if p.is_file())
    assert files == ["proof.json", "proposal.diff", "proposal.json"], files
    assert not (run_dir / "work").exists()
    assert not (run_dir / "proof").exists()


def test_self_hosted_no_effect_and_dead_variable_candidates(optimized):
    """AC-54: exactly the spec's candidates on the self-hosted config."""
    by_path = {c["yaml_path"]: c for c in optimized["proposal"]["candidates"]}
    for path in (
        "variables.ORCHESTRATOR_STRICT",
        "variables.UNKNOWN_FALLBACK_META_FEEDBACK",
        "variables.UNKNOWN_FALLBACK_MAIN_CHAT",
        "variables.UNKNOWN_FALLBACK_ASK_USER",
        "variables.SE_BASE_DIR",
    ):
        assert path in by_path, sorted(by_path)
        assert by_path[path]["kind"] == "no-effect", by_path[path]
        assert by_path[path]["deterministic"] is True, by_path[path]
    cqr = by_path["variables.CODE_QUALITY_RULES"]
    assert cqr["kind"] == "dead-variable-content-loss"
    assert cqr["applicable"] is False and list(cqr["hunks"]) == []


def test_proposal_candidate_fields(optimized):
    """AC-91/IC-24: full field set plus generator_options/agent_meta_version."""
    proposal = optimized["proposal"]
    assert set(proposal) >= {
        "project_yaml_sha256", "agent_meta_version", "generator_options",
        "candidates", "fan_out", "diff",
    }
    assert proposal["generator_options"]["include_semantic"] is False
    assert proposal["generator_options"]["content_loss_threshold_bytes"] == 200
    assert proposal["agent_meta_version"]
    candidate = next(c for c in proposal["candidates"] if c["deterministic"])
    assert set(candidate) == {
        "id", "kind", "yaml_path", "scope", "marks", "approval_level", "warnings",
        "deterministic", "applicable", "proof_level_required", "yaml_bytes_saved",
        "injected_bytes_saved_est", "rationale", "hunks",
    }
    assert candidate["scope"] == "variables"
    assert candidate["approval_level"] == "confirm"
    assert candidate["proof_level_required"] == "L0"
    assert candidate["applicable"] is True


def test_proof_is_l0_and_comparison_files_listed(optimized):
    """AC-55 Rev. 3: the L0 comparison set includes the three .meta-config sidecars."""
    proof = optimized["proof"]
    report = proof["report"]
    assert report["level_reached"] == "L0"
    assert report["ok"] is True
    assert report["files_compared"] >= report["byte_equal_files"]
    compared = {entry["path"]: entry for entry in proof["comparison_files"]}
    for rel in (".meta-config/auto-commit-allowlist.json",
                ".meta-config/generated-file-hashes.json",
                ".meta-config/context-hashes.json"):
        assert rel in compared, sorted(compared)
        assert compared[rel]["equal"] is True
        assert compared[rel]["before_sha256"] == compared[rel]["after_sha256"]
    # at least one comparison file exists in both renders -> it really was compared
    assert any(e["before_sha256"] for e in compared.values())
    assert report["scope_note"]


def test_lossy_flag_aborts_exit_2(tmp_path):
    """`--fill-defaults` in the same invocation aborts with meta-optimizer.lossy-flag."""
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml"))
    before = _snapshot(tmp_path, SINK_PARTS)
    result = _run(tmp_path, cfg, "--optimize-config", "--fill-defaults")
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "meta-optimizer.lossy-flag" in result.stderr
    assert _snapshot(tmp_path, SINK_PARTS) == before


def test_disabled_sink_exits_2_and_writes_nothing(tmp_path):
    """AC-98: a disabled tmp-sink aborts with tmp-sink.disabled, no fallback."""
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml").replace(
        "    enabled: true\n", "    enabled: false\n"))
    before = _snapshot(tmp_path, SINK_PARTS)
    result = _run(tmp_path, cfg, "--optimize-config")
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "tmp-sink.disabled" in result.stderr
    assert _snapshot(tmp_path, SINK_PARTS) == before
    assert not (tmp_path / "scratch").exists()


def test_cli_reference_documents_optimize_config():
    text = (REPO_ROOT / "docs" / "api" / "cli-reference.md").read_text(encoding="utf-8")
    assert "--optimize-config" in text
    assert "--include-semantic" in text


# --- review F11: sink artifacts are owner-only (0600) -----------------------

@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_sink_artifacts_are_owner_only(optimized):
    run_dir = optimized["run_dir"]
    for name in ("proposal.json", "proposal.diff", "proof.json"):
        mode = (run_dir / name).stat().st_mode & 0o777
        assert mode == 0o600, (name, oct(mode))


# --- review F9/F10: --out handling ------------------------------------------

def test_out_outside_sink_exits_2_with_prefixed_code(tmp_path):
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml"))
    before = _snapshot(tmp_path, SINK_PARTS)
    result = _run(tmp_path, cfg, "--optimize-config", "--out", "../outside")
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "optimize-config.out-outside-tmp-sink" in result.stderr
    assert _snapshot(tmp_path, SINK_PARTS) == before


def test_out_inside_sink_selects_the_artifact_dir(tmp_path):
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml"))
    rel = "scratch/out/meta-optimizer/myrun"
    result = _run(tmp_path, cfg, "--optimize-config", "--out", rel)
    assert result.returncode == 0, result.stderr[-2000:]
    run_dir = tmp_path / rel
    assert sorted(p.name for p in run_dir.iterdir()) == [
        "proof.json", "proposal.diff", "proposal.json"]
    # the scratch dirs are gone as well, and no sibling run dir survives
    assert sorted(p.name for p in (tmp_path / "scratch/out/meta-optimizer").iterdir()) == ["myrun"]


def test_out_pointing_at_a_file_exits_2(tmp_path):
    """Review F9: an OSError from the artifact directory must not traceback."""
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml"))
    blocker = tmp_path / "scratch" / "out" / "blocker"
    blocker.parent.mkdir(parents=True, exist_ok=True)
    blocker.write_text("not a directory\n", encoding="utf-8")
    result = _run(tmp_path, cfg, "--optimize-config", "--out", "scratch/out/blocker")
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "meta-optimizer.out-write-failed" in result.stderr


# --- review F2: every render work dir goes through resolve_work_dir ---------

def test_render_work_dirs_use_resolve_work_dir_and_are_removed(tmp_path, monkeypatch):
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml"))
    config = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])
    calls = []

    def fake_render(_agent_meta_root, _config_text, work_dir):
        work_dir = Path(work_dir)
        calls.append(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "CLAUDE.md").write_text("x\n", encoding="utf-8")
        for rel in mo.L0_COMPARISON_FILES:
            target = work_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("{}\n", encoding="utf-8")

    monkeypatch.setattr(mo, "_render_into", fake_render)
    code = mo.run_optimize_config(
        project_root=tmp_path, agent_meta_root=REPO_ROOT, config_path=cfg,
        config=config, active=active)
    assert code == 0
    assert len(calls) == 3, calls
    run_ids = [path.parent.name for path in calls]
    assert len(set(run_ids)) == 3
    assert all(path.name == "work" for path in calls)
    for path in calls:
        assert path.parent.parent == tmp_path / "scratch" / "out" / "meta-optimizer"
    assert sum(run_id.endswith("-before") for run_id in run_ids) == 1
    assert sum(run_id.endswith("-after") for run_id in run_ids) == 1
    assert not any(path.exists() for path in calls)  # scratch removed (F1 option a)
    remaining = sorted(p.name for p in (tmp_path / "scratch/out/meta-optimizer").iterdir())
    assert len(remaining) == 1, remaining


# --- review F8: a vanished comparison sidecar cannot pass -------------------

def test_missing_comparison_file_fails_the_proof(tmp_path):
    before = tmp_path / "before"
    after = tmp_path / "after"
    for root in (before, after):
        (root / ".claude").mkdir(parents=True)
        (root / ".claude" / "a.md").write_text("same\n", encoding="utf-8")
    yaml_text = "variables:\n  A: b\n"
    report = mo.prove(before, after, yaml_text, yaml_text, "L0")
    assert report.ok is False
    assert any("comparison file missing" in reason for reason in report.reasons)
    assert (before / ".meta-config/context-hashes.json").exists() is False
    # byte_equal_files must not count the absent sidecars
    assert report.files_compared == 1


# --- review F5: the credential registry fails closed ------------------------

def test_registry_failure_is_hard_error(tmp_path, monkeypatch):
    monkeypatch.setattr(mo, "_REGISTRY_RELPATH", "config/does-not-exist.yaml")
    with pytest.raises(mo.RegistryError) as excinfo:
        mo.credential_paths({"variables": {"API_TOKEN": "x"}}, REPO_ROOT)
    assert excinfo.value.code == "meta-optimizer.credential-registry-invalid"


def test_registry_error_exits_2(tmp_path, monkeypatch):
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml"))
    config = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])
    monkeypatch.setattr(mo, "_REGISTRY_RELPATH", "config/does-not-exist.yaml")
    code = mo.run_optimize_config(
        project_root=tmp_path, agent_meta_root=REPO_ROOT, config_path=cfg,
        config=config, active=active)
    assert code == 2


def test_value_scan_is_honoured(tmp_path, monkeypatch):
    """F5: the value scan only runs when the registry declares ``value_scan: secrets``."""
    monkeypatch.setattr(mo, "_load_registry", lambda _root: {
        "readers": [], "credentials": {"name_patterns": [], "keys": [], "value_scan": "off"},
    })
    config = {"variables": {"API_TOKEN": "sk-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUV"}}
    assert mo.credential_paths(config, REPO_ROOT) == frozenset()


# --- review F6: semantic kinds are gated even without the CLI flag ----------

def test_forbid_semantic_kinds_is_enforced():
    hint = mo._hint_candidate("duplicate-value", "variables.X", rationale="dup")
    keep = mo.Candidate(id="OPT-no-effect:variables.Y", kind="no-effect",
                        yaml_path="variables.Y", scope="variables")
    filtered = mo._forbid_semantic_kinds([hint, keep])
    assert [candidate.kind for candidate in filtered] == ["no-effect"]
    assert hint.kind in mo.SEMANTIC_KINDS


# --- review F12: byte accounting -------------------------------------------

def test_yaml_bytes_saved_counts_utf8_bytes():
    text = (
        "variables:\n"
        "  UMLAUT: Werte für Größen\n"
        "  KEEP: other\n"
    )
    candidate = mo._removable_candidate(
        text, "variables.UMLAUT", "no-effect", rationale="", runtime_reader=False,
        credential_lines={})
    expected = len("  UMLAUT: Werte für Größen\n".encode("utf-8"))
    assert len("  UMLAUT: Werte für Größen\n") != expected  # non-ASCII on purpose
    assert candidate.yaml_bytes_saved == expected
    assert candidate.hunks


# --- AC-57: semantic hints --------------------------------------------------

def test_semantic_kinds_need_the_flag(tmp_path):
    cfg = _init_project(tmp_path, _fixture("claude-duplicates.yaml"))

    without = _run(tmp_path, cfg, "--optimize-config", "--json")
    assert without.returncode == 0, without.stderr[-1500:]
    plain = json.loads(without.stdout)
    assert not [c for c in plain["candidates"] if c["kind"] in SEMANTIC_KINDS]
    assert not [c for c in plain["candidates"] if c["deterministic"] is False]

    with_flag = _run(tmp_path, cfg, "--optimize-config", "--include-semantic", "--json")
    assert with_flag.returncode == 0, with_flag.stderr[-1500:]
    semantic = json.loads(with_flag.stdout)
    dupes = [c for c in semantic["candidates"] if c["kind"] == "duplicate-value"]
    assert dupes, semantic["candidates"]
    dupe = dupes[0]
    assert dupe["deterministic"] is False
    assert dupe["applicable"] is False
    assert dupe["proof_level_required"] == "none"
    assert list(dupe["hunks"]) == []
    assert semantic["generator_options"]["include_semantic"] is True


# --- AC-89: credential exclusion -------------------------------------------

def test_credential_paths_detected_and_negative_case():
    config = yaml.safe_load(_fixture("claude-credentials.yaml"))
    creds = mo.credential_paths(config, REPO_ROOT)
    assert "admin-ui.token" in creds
    assert "admin-ui.token-file" in creds
    assert "variables.API_TOKEN" in creds
    assert "max-tokens-overrides" not in creds
    assert not any(p.startswith("max-tokens-overrides") for p in creds)


def test_credentials_never_appear_in_candidates_or_sink(tmp_path):
    token = "adminuisecrettokenvalue1234567890"
    cfg = _init_project(tmp_path, _fixture("claude-credentials.yaml"))
    result = _run(tmp_path, cfg, "--optimize-config", "--json", "--include-semantic")
    assert result.returncode == 0, result.stderr[-2000:]
    run_dir = _run_dirs(tmp_path)[-1]
    proposal = _load(run_dir / "proposal.json")
    paths = {c["yaml_path"] for c in proposal["candidates"]}
    assert "admin-ui.token" not in paths and "admin-ui.token-file" not in paths
    assert "variables.API_TOKEN" not in paths
    assert not any(p.startswith("admin-ui.") for p in paths)
    fan_out = {e["variable"] for e in proposal["fan_out"]}
    assert "variables.API_TOKEN" not in fan_out
    assert not any(v.startswith("admin-ui.") for v in fan_out)
    # AC-89 (review F1): the credential value appears in NO file of the whole
    # <sink>/meta-optimizer/ tree -- artifacts and any render scratch alike.
    sink_files = _sink_files(tmp_path)
    assert sink_files, "no sink files found"
    for path in sink_files:
        assert token.encode() not in path.read_bytes(), path
    # the scratch really is gone: only the three artifacts survive
    assert sorted(p.relative_to(run_dir).as_posix() for p in sink_files) == [
        "proof.json", "proposal.diff", "proposal.json"]


def test_credential_neighbour_context_is_redacted(tmp_path):
    """AC-89: diff context around a removed variable redacts the credential line."""
    text = (
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers:\n- Claude\n"
        "dod-preset: rapid-prototyping\n"
        "repo_containment:\n  tmp-sink:\n    enabled: true\n    path: scratch/out\n"
        "variables:\n"
        "  API_TOKEN: sk-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUV\n"
        "  RUNTIME_ONLY_KEY: deadsmall\n"
        "  PROJECT_NAME: redactfixturetoken\n"
    )
    cfg = _init_project(tmp_path, text)
    result = _run(tmp_path, cfg, "--optimize-config", "--json")
    assert result.returncode == 0, result.stderr[-2000:]
    run_dir = _run_dirs(tmp_path)[-1]
    diff = (run_dir / "proposal.diff").read_text(encoding="utf-8")
    assert "adminuisecrettokenvalue1234567890" not in diff
    assert "redacted credential" in diff


# --- AC-55: proof failure ---------------------------------------------------

def test_proof_failed_on_effective_variable(tmp_path):
    """A candidate whose removal changes the render -> meta-optimizer.proof-failed."""
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml"))
    config = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])
    before = _snapshot(tmp_path, SINK_PARTS)
    effective = mo.Candidate(
        id="OPT-no-effect:variables.PROJECT_NAME",
        kind="no-effect",
        yaml_path="variables.PROJECT_NAME",
        scope="variables",
        deterministic=True,
        applicable=True,
        proof_level_required="L0",
        yaml_bytes_saved=40,
    )
    code = mo.run_optimize_config(
        project_root=tmp_path, agent_meta_root=REPO_ROOT, config_path=cfg,
        config=config, active=active, candidates=[effective])
    assert code == 1
    assert _snapshot(tmp_path, SINK_PARTS) == before  # nothing written outside the sink
    run_dirs = _run_dirs(tmp_path)
    assert run_dirs
    proof = _load(run_dirs[-1] / "proof.json")
    assert proof["report"]["ok"] is False
    assert proof["report"]["level_reached"] == "none"
    assert proof["report"]["reasons"]
    assert not (run_dirs[-1] / "proposal.json").exists()


# --- AC-94: no system temp --------------------------------------------------

def test_optimizer_never_uses_systemtemp(tmp_path, monkeypatch):
    """AC-94: the whole runner path survives a tempfile.* monkeypatch that raises."""
    def boom(*_a, **_k):
        raise AssertionError("system temp must not be used")

    for name in ("mkdtemp", "mkstemp", "gettempdir", "NamedTemporaryFile", "TemporaryDirectory"):
        monkeypatch.setattr(tempfile, name, boom)
    cfg = _init_project(tmp_path, _fixture("claude-minimal.yaml"))
    config = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])
    code = mo.run_optimize_config(
        project_root=tmp_path, agent_meta_root=REPO_ROOT, config_path=cfg,
        config=config, active=active)
    assert code == 0
    run_dirs = _run_dirs(tmp_path)
    assert run_dirs and (run_dirs[-1] / "proof.json").is_file()
