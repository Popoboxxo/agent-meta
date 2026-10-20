"""End-to-end proof for credential exclusion and sink hardening (Task 26 / 2d.7).

Binding: ``docs/plans/2026-10-17-context-profiles-phase2-plan.md`` Task 26 and
``docs/specs/2026-10-11-context-profiles-spec.md`` AC-89 (Rev. 3.1):

* ``admin-ui.token``, ``admin-ui.token-file``, ``variables.API_TOKEN`` (name
  pattern + value scan) and ``variables.RELEASE_NOTE`` (value scan only) never
  produce a candidate, a hint or a ``FanOutEntry``;
* no secret value appears as a byte sequence in *any* file below
  ``<tmp-sink>/meta-optimizer/`` (proposal, diff, proof, preview, applied,
  backup);
* the diff context around a removed variable next to ``API_TOKEN`` carries the
  redaction marker; ``project.yaml.bak`` carries the marker instead of the value
  and ``applied.json.backup_redacted_keys`` names the key names;
* all sink files are owner-only (``0600``, POSIX) and no render scratch
  (``work``, ``*-before``/``*-after``, ``project.yaml.new``) survives;
* ``max-tokens-overrides`` is *not* classified as a credential (negative case).

The whole flow runs through the real CLI: ``--optimize-config``, the applier
``--dry-run`` preview and the full ``--preview``-bound application.

Run: .venv-1/bin/python -m pytest tests/test_meta_optimizer_credentials.py -q
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync.py"
FIXTURE_ROOT = REPO_ROOT / "tests" / "fixtures" / "meta-optimizer" / "credentials"
CFG_RELPATH = ".meta-config/project.yaml"
SINK_RELPATH = "scratch/out/meta-optimizer"
PROPOSAL_DIR = "scratch/out/meta-optimizer/proposal"
RUN_TIMEOUT = 900

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import meta_optimizer as mo  # noqa: E402
from lib.secrets import scan_for_secrets  # noqa: E402

ADMIN_TOKEN = "adminuisecrettokenvalue1234567890"
API_TOKEN = "sk-abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUV"
RELEASE_TOKEN = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"
SECRET_VALUES = (ADMIN_TOKEN, API_TOKEN, RELEASE_TOKEN)

CREDENTIAL_PATHS = (
    "admin-ui.token",
    "admin-ui.token-file",
    "variables.API_TOKEN",
    "variables.RELEASE_NOTE",
)

UNUSED_NEIGHBOUR = "variables.UNUSED_NEIGHBOR"


# --- helpers ---------------------------------------------------------------

def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--config", CFG_RELPATH, *args],
        cwd=str(root), capture_output=True, text=True, timeout=RUN_TIMEOUT,
    )


def _fail_tail(result: subprocess.CompletedProcess) -> str:
    return (result.stdout or "")[-2000:] + (result.stderr or "")[-2000:]


def _run_dirs(root: Path) -> set:
    sink = root / SINK_RELPATH
    if not sink.is_dir():
        return set()
    return {entry.name for entry in sink.iterdir() if entry.is_dir()}


def _sink_files(root: Path) -> list:
    sink = root / SINK_RELPATH
    return sorted(path for path in sink.rglob("*") if path.is_file())


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_no_credential_path(entries) -> None:
    """No entry may point at a credential (exact dotted path or ``admin-ui.*``)."""
    blob = json.dumps(entries, ensure_ascii=False)
    for path in CREDENTIAL_PATHS:
        assert path not in blob, "credential path leaked: {}".format(path)
    assert "admin-ui." not in blob, "admin-ui path leaked"


# --- one module-scoped end-to-end run --------------------------------------

@pytest.fixture(scope="module")
def credentials_e2e(tmp_path_factory):
    """Fixture project through optimize -> dry-run preview -> bound application."""
    root = tmp_path_factory.mktemp("meta-optimizer-credentials")
    shutil.copytree(str(FIXTURE_ROOT), str(root), dirs_exist_ok=True)
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    cfg = root / CFG_RELPATH
    original_hash = _sha256(cfg)

    optimized = _run(root, "--optimize-config", "--json", "--out", PROPOSAL_DIR)
    assert optimized.returncode == 0, _fail_tail(optimized)
    proposal_dir = root / PROPOSAL_DIR
    proposal = json.loads((proposal_dir / "proposal.json").read_text(encoding="utf-8"))

    matched = [
        candidate for candidate in proposal.get("candidates") or []
        if candidate.get("yaml_path") == UNUSED_NEIGHBOUR
        and candidate.get("deterministic") is True
    ]
    assert len(matched) == 1, [
        (entry.get("id"), entry.get("yaml_path"), entry.get("deterministic"))
        for entry in proposal.get("candidates") or []
    ]
    candidate_id = matched[0]["id"]

    before_dry = _run_dirs(root)
    dry = _run(root, "--apply-config-patch", str(proposal_dir / "proposal.json"),
               "--accept", candidate_id, "--dry-run", "--json")
    assert dry.returncode == 0, _fail_tail(dry)
    new_dry_dirs = _run_dirs(root) - before_dry
    assert len(new_dry_dirs) == 1, sorted(new_dry_dirs)
    preview_dir = root / SINK_RELPATH / new_dry_dirs.pop()
    preview_path = preview_dir / "preview.json"
    assert preview_path.is_file()
    assert sorted(entry.name for entry in preview_dir.iterdir()) == ["preview.json"]
    # AC-90: the dry-run must not modify the source config.
    assert _sha256(cfg) == original_hash

    preview = json.loads(preview_path.read_text(encoding="utf-8"))

    before_apply = _run_dirs(root)
    applied = _run(root, "--apply-config-patch", str(proposal_dir / "proposal.json"),
                   "--accept", candidate_id, "--preview", str(preview_path),
                   "--json")
    assert applied.returncode == 0, _fail_tail(applied)
    new_apply_dirs = _run_dirs(root) - before_apply
    assert len(new_apply_dirs) == 1, sorted(new_apply_dirs)
    apply_dir = root / SINK_RELPATH / new_apply_dirs.pop()
    report = json.loads((apply_dir / "applied.json").read_text(encoding="utf-8"))

    return {
        "root": root,
        "cfg": cfg,
        "proposal": proposal,
        "proposal_dir": proposal_dir,
        "candidate_id": candidate_id,
        "preview": preview,
        "preview_dir": preview_dir,
        "apply_dir": apply_dir,
        "report": report,
        "original_hash": original_hash,
    }


# --- AC-89: registry classification ---------------------------------------

def test_credential_paths_and_negative_case():
    """AC-89: name patterns, explicit keys and the value scan; no token overrides."""
    config = yaml.safe_load((FIXTURE_ROOT / CFG_RELPATH).read_text(encoding="utf-8"))
    credentials = mo.credential_paths(config, REPO_ROOT)
    for path in CREDENTIAL_PATHS:
        assert path in credentials, (path, sorted(credentials))
    assert "max-tokens-overrides" not in credentials
    assert "max-tokens-overrides.developer" not in credentials
    assert not any(
        path == "max-tokens-overrides" or path.startswith("max-tokens-overrides.")
        for path in credentials
    )


def test_secret_values_are_detected_by_the_value_scan():
    """AC-89: both scanned fixture values are high-confidence findings."""
    assert scan_for_secrets(API_TOKEN)
    assert scan_for_secrets(RELEASE_TOKEN)


# --- AC-89: proposal artifacts ---------------------------------------------

def test_proposal_has_no_credential_entries(credentials_e2e):
    proposal = credentials_e2e["proposal"]
    candidates = proposal.get("candidates") or []
    fan_out = proposal.get("fan_out") or []
    preview_candidates = credentials_e2e["preview"].get("candidates") or []
    # Non-vacuity: the fixture *does* produce candidates/fan-out/preview entries.
    assert candidates
    assert fan_out
    assert preview_candidates
    _assert_no_credential_path(candidates)
    _assert_no_credential_path(fan_out)
    _assert_no_credential_path(preview_candidates)

    for entry in proposal.get("candidates") or []:
        assert entry["yaml_path"] not in CREDENTIAL_PATHS
    for entry in proposal.get("fan_out") or []:
        assert entry["variable"] not in CREDENTIAL_PATHS


def test_diff_redacts_the_credential_neighbour_context(credentials_e2e):
    """AC-89: the removed neighbour's diff context redacts the credential line."""
    diff = (credentials_e2e["proposal_dir"] / "proposal.diff").read_text(encoding="utf-8")
    assert UNUSED_NEIGHBOUR.split(".", 1)[1] in diff
    assert "redacted credential" in diff
    for value in SECRET_VALUES:
        assert value not in diff


# --- AC-89: no secret byte below the sink ----------------------------------

def test_no_secret_value_in_any_sink_file(credentials_e2e):
    root = credentials_e2e["root"]
    files = _sink_files(root)
    names = {path.name for path in files}
    assert {"proposal.json", "proposal.diff", "proof.json", "preview.json",
            "applied.json", "project.yaml.bak"} <= names
    for path in files:
        data = path.read_bytes()
        for value in SECRET_VALUES:
            assert value.encode("utf-8") not in data, (path, value)


# --- AC-89: redacted backup + protocol key names ---------------------------

def test_backup_is_redacted_and_protocol_names_the_keys(credentials_e2e):
    apply_dir = credentials_e2e["apply_dir"]
    backup_text = (apply_dir / "project.yaml.bak").read_text(encoding="utf-8")
    assert "redacted credential" in backup_text
    for value in SECRET_VALUES:
        assert value not in backup_text
    assert credentials_e2e["report"]["backup_redacted_keys"] == [
        "API_TOKEN", "RELEASE_NOTE", "token", "token-file"]


# --- AC-89: sink hardening + no scratch ------------------------------------

@pytest.mark.skipif(os.name == "nt", reason="POSIX mode bits only")
def test_every_sink_file_is_owner_only(credentials_e2e):
    for path in _sink_files(credentials_e2e["root"]):
        mode = path.stat().st_mode & 0o777
        assert mode == 0o600, (path, oct(mode))


def test_no_render_scratch_survives(credentials_e2e):
    root = credentials_e2e["root"]
    sink = root / SINK_RELPATH
    for path in sink.rglob("*"):
        assert path.name != "work", path
        assert not path.name.endswith("-before"), path
        assert not path.name.endswith("-after"), path
    assert not list(sink.rglob("project.yaml.new"))


# --- AC-89: the source config stays intact and authoritative ---------------

def test_source_config_keeps_credentials_and_loses_only_the_neighbour(
        credentials_e2e):
    config = yaml.safe_load(credentials_e2e["cfg"].read_text(encoding="utf-8"))
    assert config["admin-ui"]["token"] == ADMIN_TOKEN
    assert config["admin-ui"]["token-file"] == "/run/secrets/admin-token"
    assert config["variables"]["API_TOKEN"] == API_TOKEN
    assert config["variables"]["RELEASE_NOTE"] == RELEASE_TOKEN
    assert config["max-tokens-overrides"]["developer"] == 4096
    assert "UNUSED_NEIGHBOR" not in config["variables"]
    # The applied run is reflected in the report's before/after hashes.
    report = credentials_e2e["report"]
    assert report["project_yaml_sha256_before"] == credentials_e2e["original_hash"]
    assert report["project_yaml_sha256_after"] == _sha256(credentials_e2e["cfg"])
    assert report["approval_source"] == "relayed"
