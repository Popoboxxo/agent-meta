"""Remove-only config patch applier (Task 22 / 2d.3).

Binding: ``docs/plans/2026-10-17-context-profiles-phase2-plan.md`` Task 22 (cases
(a)-(j)) and ``docs/specs/2026-10-11-context-profiles-spec.md`` IC-24 ("Applier",
"Vorschau und Anwendung") / IC-25.

The applier recomputes the candidates itself, reconciles the REDACTED hunks of
``proposal.json``, enforces remove-only, binds the application to a
``preview.json`` and replaces ``.meta-config/project.yaml`` atomically from a
scratch file below the tmp-sink. Covered acceptance criteria: AC-55 (application
part), AC-56 (comments/order), AC-75 (sink protocol + backup), AC-80 (a)-(d),
AC-89 (redaction/mode), AC-90 (preview binding, TOCTOU, ``approval_source``),
AC-91 (``version-mismatch``, ``rejected: not-applicable``) and AC-94 (no system
temp directory, no scratch remnant).

Every case drives a real render, so the suite is deliberately grouped to keep the
number of ``sync.py`` renders low; the applier itself proves the patch (three
renders per application) and therefore dominates the runtime.

Run: .venv-1/bin/python -m pytest tests/test_meta_optimizer_applier.py -q
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import meta_optimizer as mo  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.config import read_version  # noqa: E402

SINK_PARTS = ("scratch", "out")
SINK_SUBDIR = ("scratch", "out", "meta-optimizer")
RUN_TIMEOUT = 900
TOKEN = "adminuisecrettokenvalue1234567890"
TARGET_ID = "OPT-no-effect:variables.PROJECT_PREFIX"
HINT_ID = "OPT-dead-variable-content-loss:variables.UNUSED_BIG"

CONFIG_TEXT = (
    "# Applier fixture (Task 22 / 2d.3): comments, key order and a Markdown\n"
    "# block scalar must survive a remove-only patch except the removed lines.\n"
    'agent-meta-version: "' + read_version(REPO_ROOT) + '"\n'
    "ai-providers:\n"
    "- Claude\n"
    "dod-preset: rapid-prototyping\n"
    "admin-ui:\n"
    "  token: " + TOKEN + "\n"
    "repo_containment:\n"
    "  tmp-sink:\n"
    "    enabled: true\n"
    "    path: scratch/out\n"
    "variables:\n"
    "  PROJECT_NAME: applierfixturetoken\n"
    "  PROJECT_PREFIX: ap\n"
    "  UNKNOWN_FALLBACK_MAIN_CHAT: true\n"
    "  UNUSED_SMALL: deadsmall\n"
    "  # standalone comment stays in place (Q24)\n"
    "  UNUSED_COMMENTED: dead-commented  # inline comment on a removed line\n"
    "  UNUSED_SMALL_BLOCK: |\n"
    "    # markdown heading inside a small block scalar\n"
    "    short body text\n"
    "  UNUSED_BIG: |\n"
    "    Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod\n"
    "    tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam,\n"
    "    quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo\n"
    "    consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse.\n"
)


# --- helpers ---------------------------------------------------------------

def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--config", ".meta-config/project.yaml", *args],
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


def _sink_files(root: Path) -> list:
    base = root.joinpath(*SINK_SUBDIR)
    return sorted(p for p in base.rglob("*") if p.is_file()) if base.is_dir() else []


def _run_dirs(root: Path) -> list:
    base = root.joinpath(*SINK_SUBDIR)
    return sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []


def _scratch_dirs(root: Path) -> list:
    base = root.joinpath(*SINK_SUBDIR)
    if not base.is_dir():
        return []
    return sorted(
        p for p in base.rglob("*")
        if p.is_dir() and (p.name == "work" or p.name.endswith(("-before", "-after")))
    )


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_proposal(path: Path, *, config_text: str = CONFIG_TEXT, version: str | None = None,
                    candidates: list | None = None, hunks: dict | None = None,
                    ids: list | None = None) -> Path:
    """Write a minimal ``proposal.json`` (only the fields the applier reads)."""
    payload = {
        "project_yaml_sha256": _sha256(config_text),
        "agent_meta_version": read_version(REPO_ROOT) if version is None else version,
        "generator_options": {
            "include_semantic": False, "content_loss_threshold_bytes": 200},
        "candidates": candidates if candidates is not None else [
            {"id": cid, "hunks": list((hunks or {}).get(cid, []))} for cid in (ids or [])],
        "fan_out": [],
        "diff": "",
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def _preview_payload(path: Path) -> dict:
    return _load(path)


def _seal_preview(payload: dict) -> dict:
    """Recompute ``preview_sha256`` so a tampered preview still has a valid digest."""
    payload["preview_sha256"] = mo._binding_digest(payload)
    return payload


# --- fixtures --------------------------------------------------------------

@pytest.fixture(scope="module")
def proposed(tmp_path_factory):
    """One real proposal run; every other case reuses its artifacts."""
    root = tmp_path_factory.mktemp("mo-applier")
    cfg = _init_project(root, CONFIG_TEXT)
    before = _snapshot(root, SINK_PARTS)
    result = _run(root, "--optimize-config", "--json")
    assert result.returncode == 0, result.stderr[-2500:]
    run_dirs = _run_dirs(root)
    assert run_dirs, result.stderr[-2500:]
    proposal_path = run_dirs[-1] / "proposal.json"
    proposal = _load(proposal_path)
    deterministic = [c["id"] for c in proposal["candidates"] if c["deterministic"]]
    assert TARGET_ID in deterministic, sorted(deterministic)
    assert HINT_ID in [c["id"] for c in proposal["candidates"]]
    return {
        "root": root,
        "cfg": cfg,
        "before": before,
        "proposal": proposal,
        "proposal_path": proposal_path,
        "deterministic_ids": deterministic,
    }


@pytest.fixture(scope="module")
def preview(proposed):
    """One real ``--dry-run`` preview (AC-90); never touches ``project.yaml``."""
    root = proposed["root"]
    result = _run(
        root, "--apply-config-patch", str(proposed["proposal_path"]),
        "--accept", *proposed["deterministic_ids"], "--dry-run", "--json")
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-2500:]
    report = json.loads(result.stdout)
    assert report["applied_ids"] == proposed["deterministic_ids"]
    assert report["rejected"] == []
    assert report["dry_run"] is True
    assert report["exit_code"] == 0
    previews = sorted(root.joinpath(*SINK_SUBDIR).glob("*/preview.json"))
    assert previews, sorted(p.name for p in _sink_files(root))
    path = previews[-1]
    return {"root": root, "path": path, "payload": _load(path), "report": report}


# --- (a) usage -------------------------------------------------------------

def test_missing_accept_exits_2_without_writing(proposed):
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    sink_before = _sink_files(root)
    result = _run(root, "--apply-config-patch", str(proposed["proposal_path"]))
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "--accept" in result.stderr
    assert _snapshot(root, SINK_PARTS) == before
    assert _sink_files(root) == sink_before


def test_preview_or_dry_run_is_mandatory(proposed):
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    result = _run(root, "--apply-config-patch", str(proposed["proposal_path"]),
                  "--accept", TARGET_ID)
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "--dry-run" in result.stderr and "--preview" in result.stderr
    assert _snapshot(root, SINK_PARTS) == before


def test_accept_flags_need_apply_config_patch(proposed):
    result = _run(proposed["root"], "--optimize-config", "--accept", TARGET_ID)
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "--accept" in result.stderr


def test_fill_defaults_conflicts_with_apply_config_patch(proposed):
    """`--fill-defaults` in the same invocation is the documented lossy-flag Exit 2."""
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    result = _run(root, "--apply-config-patch", str(proposed["proposal_path"]),
                  "--accept", TARGET_ID, "--dry-run", "--fill-defaults")
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "meta-optimizer.lossy-flag" in result.stderr
    assert _snapshot(root, SINK_PARTS) == before


# --- (h) AC-91: version-mismatch -------------------------------------------

def test_version_mismatch_writes_nothing(proposed, tmp_path):
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    sink_before = _sink_files(root)
    stale = _write_proposal(tmp_path / "proposal.json", version="1.0.0",
                            ids=proposed["deterministic_ids"])
    result = _run(root, "--apply-config-patch", str(stale),
                  "--accept", *proposed["deterministic_ids"], "--dry-run")
    assert result.returncode == 1, result.stdout[-800:] + result.stderr[-800:]
    assert "meta-optimizer.version-mismatch" in result.stderr
    assert _snapshot(root, SINK_PARTS) == before
    assert _sink_files(root) == sink_before  # not even a preview


# --- (b) AC-80 (b): manipulated proposal.json -------------------------------

def _tampered_proposal(tmp_path: Path, proposed, mutate) -> Path:
    payload = json.loads(proposed["proposal_path"].read_text(encoding="utf-8"))
    mutate(payload)
    path = tmp_path / "proposal.json"
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return path


def test_manipulated_hunk_that_inserts_a_line_is_not_remove_only(proposed, tmp_path):
    def mutate(payload):
        for candidate in payload["candidates"]:
            if candidate["id"] == TARGET_ID:
                lines = candidate["hunks"][0].splitlines()
                lines.insert(3, "+  INJECTED_BY_MALLORY: 1")
                candidate["hunks"] = ["\n".join(lines) + "\n"]

    path = _tampered_proposal(tmp_path, proposed, mutate)
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    sink_before = _sink_files(root)
    result = _run(root, "--apply-config-patch", str(path),
                  "--accept", TARGET_ID, "--dry-run")
    assert result.returncode == 1, result.stdout[-800:] + result.stderr[-800:]
    assert "meta-optimizer.not-remove-only" in result.stderr
    assert _snapshot(root, SINK_PARTS) == before
    assert _sink_files(root) == sink_before


def test_manipulated_remove_only_hunk_is_hunk_mismatch(proposed, tmp_path):
    def mutate(payload):
        for candidate in payload["candidates"]:
            if candidate["id"] == TARGET_ID:
                # still remove-only (a line is dropped, none inserted) but no
                # longer the recomputed hunk -> the hunk reconciliation fails.
                lines = candidate["hunks"][0].splitlines()
                candidate["hunks"] = ["\n".join(lines[:-1]) + "\n"]

    path = _tampered_proposal(tmp_path, proposed, mutate)
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    result = _run(root, "--apply-config-patch", str(path),
                  "--accept", TARGET_ID, "--dry-run")
    assert result.returncode == 1, result.stdout[-800:] + result.stderr[-800:]
    assert "hunk-mismatch" in result.stderr
    assert _snapshot(root, SINK_PARTS) == before


# --- (c) AC-80 (c): not-reproducible ---------------------------------------

def test_non_reproducible_id_is_rejected(tmp_path, proposed):
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    empty = _write_proposal(tmp_path / "proposal.json", ids=[])
    bogus = "OPT-no-effect:variables.DOES_NOT_EXIST"
    result = _run(root, "--apply-config-patch", str(empty), "--accept", bogus, "--dry-run")
    assert result.returncode == 1, result.stdout[-800:] + result.stderr[-800:]
    assert "not-reproducible" in result.stderr
    assert _snapshot(root, SINK_PARTS) == before


# --- (i) AC-91/AC-57: a hint ID is not applicable ---------------------------

def test_hint_id_is_rejected_as_not_applicable(proposed):
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    result = _run(root, "--apply-config-patch", str(proposed["proposal_path"]),
                  "--accept", HINT_ID, "--dry-run")
    assert result.returncode == 1, result.stdout[-800:] + result.stderr[-800:]
    assert "not-applicable" in result.stderr
    assert _snapshot(root, SINK_PARTS) == before


# --- AC-90: preview ---------------------------------------------------------

def test_preview_writes_only_preview_json(preview, proposed):
    payload = preview["payload"]
    assert payload["accept_ids"] == proposed["deterministic_ids"]
    assert payload["accept_runtime_ids"] == []
    assert payload["project_yaml_sha256"] == _sha256(CONFIG_TEXT)
    assert payload["agent_meta_version"] == read_version(REPO_ROOT)
    assert payload["generator_options"]["include_semantic"] is False
    assert payload["rejected"] == []
    entries = {entry["id"]: entry for entry in payload["candidates"]}
    for candidate_id in proposed["deterministic_ids"]:
        entry = entries[candidate_id]
        assert entry["hunks"], entry
        assert entry["kind"] == "no-effect"
        assert entry["marks"] == []
        assert entry["warnings"] == []
    assert payload["preview_sha256"]
    run_dir = preview["path"].parent
    assert sorted(p.name for p in run_dir.iterdir()) == ["preview.json"]
    assert (preview["path"].stat().st_mode & 0o777) == 0o600
    # project.yaml is untouched by a preview
    assert (preview["root"] / ".meta-config" / "project.yaml").read_text(
        encoding="utf-8") == CONFIG_TEXT
    assert _snapshot(preview["root"], SINK_PARTS) == proposed["before"]


# --- (d)(f)(g)(j) AC-80 (d), AC-56, AC-89, AC-90, AC-94 ---------------------

@pytest.fixture(scope="module")
def applied(proposed, preview, tmp_path_factory):
    """One real application plus the two preview-tamper probes (AC-90).

    Uses an explicit ``pytest.MonkeyPatch`` for the system-temp *creation* guard,
    records every observation and restores the shared ``project.yaml`` before
    returning, so the module's cases stay order-independent.
    """
    root = proposed["root"]
    ids = list(proposed["deterministic_ids"])
    cfg = root / ".meta-config" / "project.yaml"
    probe = _snapshot(root, SINK_PARTS)
    monkey = pytest.MonkeyPatch()

    def boom(*_args, **_kwargs):
        raise AssertionError("system temp must not be used")

    # Creation APIs only: ``tempfile.gettempdir()`` is a pure read that the
    # central resolver queries for the "sink not in system temp" check
    # (``tmp_sink_location_error``, spec §IC-01) and for the sanctioned
    # pytest-basetemp precedence (IC-04/ADR-01) -- it never creates an entry.
    # Same deviation as ``tests/test_context_report.py`` (Task 10).
    for name in ("mkdtemp", "mkstemp", "NamedTemporaryFile", "TemporaryDirectory"):
        monkey.setattr(tempfile, name, boom)
    try:
        # (d) a preview with a flipped hash is rejected before any recomputation
        flipped = _seal_preview({
            **_preview_payload(preview["path"]), "project_yaml_sha256": "0" * 64})
        flipped_path = tmp_path_factory.mktemp("flipped") / "preview.json"
        flipped_path.write_text(json.dumps(flipped), encoding="utf-8")
        hash_report = mo.apply_config_patch(
            root, REPO_ROOT, proposed["proposal_path"], ids,
            preview_path=flipped_path, dry_run=False)
        hash_unchanged = _snapshot(root, SINK_PARTS) == probe

        # (d) a preview whose recomputed hunk was swapped (valid digest) is rejected
        swapped = _preview_payload(preview["path"])
        for entry in swapped["candidates"]:
            if entry["id"] == TARGET_ID:
                entry["hunks"] = [entry["hunks"][0] + "+  INJECTED: 1\n"]
        swapped_path = tmp_path_factory.mktemp("swapped") / "preview.json"
        swapped_path.write_text(json.dumps(_seal_preview(swapped)), encoding="utf-8")
        hunk_report = mo.apply_config_patch(
            root, REPO_ROOT, proposed["proposal_path"], ids,
            preview_path=swapped_path, dry_run=False)
        hunk_unchanged = _snapshot(root, SINK_PARTS) == probe

        # the application itself (in-process, so the system-temp monkeypatch applies)
        report = mo.apply_config_patch(
            root, REPO_ROOT, proposed["proposal_path"], ids,
            preview_path=preview["path"], dry_run=False)
        assert report.exit_code == 0, report
        after_text = cfg.read_text(encoding="utf-8")
        result = {
            "root": root,
            "report": report,
            "protocol": _load(Path(report.log_path)),
            "after_text": after_text,
            "hash_report": hash_report,
            "hash_unchanged": hash_unchanged,
            "hunk_report": hunk_report,
            "hunk_unchanged": hunk_unchanged,
        }
    finally:
        monkey.undo()
        cfg.write_text(CONFIG_TEXT, encoding="utf-8")  # keep later cases pristine
    return result


@pytest.fixture
def pristine_config(proposed):
    """Restore the shared config after a mutating case (order-independent)."""
    cfg = proposed["cfg"]
    yield cfg
    cfg.write_text(CONFIG_TEXT, encoding="utf-8")


def test_tampered_previews_are_rejected(applied):
    assert applied["hash_report"].exit_code == 1
    assert applied["hash_report"].code == mo.PREVIEW_MISMATCH_CODE
    assert applied["hash_unchanged"] is True
    assert applied["hunk_report"].exit_code == 1
    assert applied["hunk_report"].code == mo.PREVIEW_MISMATCH_CODE
    assert applied["hunk_unchanged"] is True


@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_apply_writes_protocol_backup_and_hardened_sink(applied, proposed):
    """(f) + (j) AC-80 (d), AC-75: relayed approval, redacted backup, 0600."""
    report = applied["report"]
    protocol = applied["protocol"]
    assert list(report.applied_ids) == list(proposed["deterministic_ids"])
    assert report.rejected == ()
    assert protocol["approval_source"] == "relayed"
    assert protocol["approval_source"] not in ("user", "permission-prompt")
    assert protocol["accept_ids"] == list(proposed["deterministic_ids"])
    assert protocol["accept_runtime_ids"] == []
    assert protocol["rejected"] == []
    assert protocol["backup_redacted_keys"] == ["token"]
    assert TOKEN not in json.dumps(protocol)
    assert protocol["agent_meta_version"] == read_version(REPO_ROOT)
    assert protocol["generator_options"]["include_semantic"] is False
    assert protocol["timestamp"]

    run_dir = Path(report.log_path).parent
    assert run_dir.parent == applied["root"].joinpath(*SINK_SUBDIR)
    assert sorted(p.name for p in run_dir.iterdir()) == ["applied.json", "project.yaml.bak"]
    backup = run_dir / "project.yaml.bak"
    backup_text = backup.read_text(encoding="utf-8")
    assert TOKEN not in backup_text
    assert "redacted credential" in backup_text
    for path in (Path(report.log_path), backup):
        assert (path.stat().st_mode & 0o777) == 0o600, path


def test_apply_keeps_no_credential_and_no_scratch(applied):
    """AC-89 + review N2: no credential byte and no render scratch under the sink."""
    root = applied["root"]
    files = _sink_files(root)
    assert files
    for path in files:
        assert TOKEN.encode() not in path.read_bytes(), path
    assert _scratch_dirs(root) == []
    assert not list(root.joinpath(*SINK_SUBDIR).glob("*/project.yaml.new"))
    assert not list(root.joinpath(*SINK_SUBDIR).glob("*/work"))


def test_apply_preserves_comments_and_order(applied):
    """(g) AC-56: only the comments on the removed lines are lost (Q24)."""
    before, after = CONFIG_TEXT, applied["after_text"]
    roundtrip = mo.analyze_roundtrip(before, after)
    assert roundtrip.order_changed is False
    expected = mo._count_comments("".join(mo._removed_lines(before, after)))
    assert expected > 0  # the inline comment and the block-scalar heading count
    assert roundtrip.lost_comments == expected
    assert "# standalone comment stays in place (Q24)" in after
    for removed in ("PROJECT_PREFIX", "UNKNOWN_FALLBACK_MAIN_CHAT", "UNUSED_SMALL",
                    "UNUSED_COMMENTED", "UNUSED_SMALL_BLOCK"):
        assert removed not in after
    assert "UNUSED_BIG" in after  # a hint is never applied
    assert yaml.safe_load(after)["variables"]["PROJECT_NAME"] == "applierfixturetoken"


def test_applied_hashes_bind_to_the_preview(applied, preview):
    report = applied["report"]
    protocol = applied["protocol"]
    after_hash = _sha256(applied["after_text"])
    assert report.project_yaml_sha256_before == _sha256(CONFIG_TEXT)
    assert report.project_yaml_sha256_after == after_hash
    assert report.preview_sha256 == preview["payload"]["preview_sha256"]
    assert protocol["project_yaml_sha256_before"] == _sha256(CONFIG_TEXT)
    assert protocol["project_yaml_sha256_after"] == after_hash
    assert protocol["preview_sha256"] == preview["payload"]["preview_sha256"]


# --- (e) AC-90: TOCTOU ------------------------------------------------------

def test_toc_tou_hook_yields_stale_proposal(proposed, preview, monkeypatch, pristine_config):
    root = proposed["root"]
    ids = proposed["deterministic_ids"]
    changed = CONFIG_TEXT + "  INJECTED_AFTER_RECOMPUTE: 1\n"

    def hook():
        pristine_config.write_text(changed, encoding="utf-8")

    monkeypatch.setattr(mo, "_TOCTOU_TEST_HOOK", hook)
    before_sink = set(str(p) for p in _sink_files(root))
    report = mo.apply_config_patch(
        root, REPO_ROOT, proposed["proposal_path"], ids,
        preview_path=preview["path"], dry_run=False)
    assert report.exit_code == 1 and report.code == mo.STALE_PROPOSAL_CODE, report
    # nothing written: the config keeps the injected change, no protocol/backup,
    # not even an empty run dir (the transient scratch file was discarded)
    assert pristine_config.read_text(encoding="utf-8") == changed
    new_files = set(str(p) for p in _sink_files(root)) - before_sink
    assert new_files == set(), sorted(new_files)
    assert report.log_path is None and report.run_dir is None


# --- AC-94: cross-device sink ----------------------------------------------

def test_cross_device_sink_aborts_before_writing(proposed, preview, monkeypatch):
    root = proposed["root"]
    before = _snapshot(root, SINK_PARTS)
    sink_before = set(str(p) for p in _sink_files(root))
    monkeypatch.setattr(mo, "_same_device", lambda _a, _b: False)
    report = mo.apply_config_patch(
        root, REPO_ROOT, proposed["proposal_path"], proposed["deterministic_ids"],
        preview_path=preview["path"], dry_run=False)
    assert report.exit_code == 1 and report.code == mo.CROSS_DEVICE_CODE, report
    assert _snapshot(root, SINK_PARTS) == before
    assert set(str(p) for p in _sink_files(root)) == sink_before


# --- review N2: collect_candidates owns its scratch -------------------------

def test_collect_candidates_removes_its_own_scratch(tmp_path, monkeypatch):
    """N2 (blocking, security): no credential scratch survives collect_candidates."""
    cfg = _init_project(tmp_path, CONFIG_TEXT)
    config = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])
    calls = []

    def fake_render(_agent_meta_root, _config_text, work_dir, _paths=None):
        work_dir = Path(work_dir)
        calls.append(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / ".meta-config").mkdir(parents=True, exist_ok=True)
        (work_dir / ".meta-config" / "project.yaml").write_text(
            _config_text, encoding="utf-8")

    monkeypatch.setattr(mo, "_render_into", fake_render)
    proposal = mo.collect_candidates(tmp_path, REPO_ROOT, config, CONFIG_TEXT, active)
    assert proposal.candidates
    assert len(calls) == 1, calls
    assert not any(path.exists() for path in calls)
    assert _scratch_dirs(tmp_path) == []
    # no leftover run dir at all: the scratch owner removes its own run dir
    assert _run_dirs(tmp_path) == []


# --- review N1: artifact write failures map to the documented exit code ------

def test_artifact_write_failure_is_out_write_failed(tmp_path, monkeypatch):
    """N1: an OSError while writing the artifacts is Exit 2, never a traceback."""
    cfg = _init_project(tmp_path, CONFIG_TEXT)
    config = yaml.safe_load(cfg.read_text(encoding="utf-8"))
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])

    def fake_render(_agent_meta_root, _config_text, work_dir, _paths=None):
        work_dir = Path(work_dir)
        work_dir.mkdir(parents=True, exist_ok=True)
        (work_dir / "CLAUDE.md").write_text("x\n", encoding="utf-8")
        for rel in mo.L0_COMPARISON_FILES:
            target = work_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("{}\n", encoding="utf-8")

    def failing_write(_path, _payload):
        raise OSError("disk full")

    monkeypatch.setattr(mo, "_render_into", fake_render)
    monkeypatch.setattr(mo, "_write_json", failing_write)
    code = mo.run_optimize_config(
        project_root=tmp_path, agent_meta_root=REPO_ROOT, config_path=cfg,
        config=config, active=active)
    assert code == 2, code
