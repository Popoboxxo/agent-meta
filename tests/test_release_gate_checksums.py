"""Regression tests for release-gate SHA-256 checksum verification (issue #603).

Covers both ends of the integrity chain:

- scripts/lib/hook_plugins.py::sync_release_gates() (re)generates
  release-gates/.sha256-checksums for built-in gates (hash of the deployed,
  placeholder-substituted content), preserves project-owned checksum lines
  verbatim and drops stale entries for removed built-ins — so legitimate
  gate changes refresh the manifest on every sync.
- hooks/1-generic/pre-release-check.sh refuses (fail-closed) to execute an
  allowlisted gate whose checksum manifest is missing, whose entry is
  missing, or whose checksum does not match — with a remediation hint.

The allowlist flow itself (issue #598) is covered by
tests/test_pre_release_check_hook.py.

Run: python -m pytest tests/test_release_gate_checksums.py -v
"""

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hook_plugins import sync_release_gates  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_DISPATCHER_PATH = _REPO_ROOT / "hooks" / "1-generic" / "pre-release-check.sh"
_CHECKSUM_MANIFEST = ".sha256-checksums"

_BASH = shutil.which("bash") or "bash"

_dispatcher_test = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)

_SHA256SUM_AVAILABLE = shutil.which("sha256sum") is not None


def _sha256_of(path: Path) -> str:
    """Return the hex SHA-256 digest of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest_entries(gates_dir: Path) -> dict[str, str]:
    """Parse .sha256-checksums into {filename: hash} (comments/blank lines ignored)."""
    entries: dict[str, str] = {}
    manifest = gates_dir / _CHECKSUM_MANIFEST
    if not manifest.exists():
        return entries
    for line in manifest.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        hash_value, filename = stripped.split()
        entries[filename] = hash_value
    return entries


# --------------------------------------------------------------------------
# sync_release_gates(): manifest generation / regeneration
# --------------------------------------------------------------------------


@pytest.fixture
def agent_meta_root(tmp_path):
    """Minimal agent-meta source tree with one built-in release gate."""
    root = tmp_path / "agent-meta"
    gates_dir = root / "hooks" / "1-generic" / "release-gates"
    gates_dir.mkdir(parents=True)
    (gates_dir / "demo-gate.sh").write_text(
        "#!/bin/bash\n"
        "# hook: demo-gate\n"
        "# version: 1.0.0\n"
        "# event: Manual\n"
        "# description: demo gate\n"
        "# enabled_by_default: false\n"
        'echo "[INFO] demo-gate: ran"\n',
        encoding="utf-8",
    )
    return root


@pytest.fixture
def project_root(tmp_path):
    p = tmp_path / "project"
    p.mkdir()
    return p


def _sync(agent_meta_root: Path, project_root: Path, dry_run: bool = False) -> SyncLog:
    log = SyncLog()
    sync_release_gates(
        agent_meta_root, project_root, {"platforms": []}, log, dry_run=dry_run
    )
    return log


def test_sync_writes_checksum_manifest_matching_deployed_content(
    agent_meta_root, project_root
):
    _sync(agent_meta_root, project_root)
    gates_dir = project_root / ".claude" / "hooks" / "release-gates"
    deployed = gates_dir / "demo-gate.sh"
    assert deployed.exists()
    entries = _manifest_entries(gates_dir)
    assert entries == {"demo-gate.sh": _sha256_of(deployed)}


def test_checksum_manifest_is_sha256sum_compatible(agent_meta_root, project_root):
    """The manifest must verify with standard `sha256sum -c` (no custom tooling)."""
    if not _SHA256SUM_AVAILABLE:
        pytest.skip("sha256sum not available")
    _sync(agent_meta_root, project_root)
    gates_dir = project_root / ".claude" / "hooks" / "release-gates"
    result = subprocess.run(
        [_BASH, "-c", "sha256sum --check --quiet .sha256-checksums"],
        cwd=str(gates_dir),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_sync_preserves_project_owned_checksum_lines(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root)
    gates_dir = project_root / ".claude" / "hooks" / "release-gates"
    # Project registers its own gate (issue #598 + #603 flow): .sh file plus
    # checksum line appended to the manifest.
    project_gate = gates_dir / "my-check.sh"
    project_gate.write_text("#!/bin/bash\necho mine\n", encoding="utf-8")
    with (gates_dir / _CHECKSUM_MANIFEST).open("a", encoding="utf-8") as fh:
        fh.write(f"# my own gate\n{_sha256_of(project_gate)}  my-check.sh\n")

    _sync(agent_meta_root, project_root)

    entries = _manifest_entries(gates_dir)
    assert entries["my-check.sh"] == _sha256_of(project_gate)
    assert entries["demo-gate.sh"] == _sha256_of(gates_dir / "demo-gate.sh")
    manifest_text = (gates_dir / _CHECKSUM_MANIFEST).read_text(encoding="utf-8")
    assert "# my own gate" in manifest_text  # comments preserved verbatim


def test_sync_drops_stale_checksum_entries_for_removed_builtins(
    agent_meta_root, project_root
):
    _sync(agent_meta_root, project_root)
    gates_dir = project_root / ".claude" / "hooks" / "release-gates"
    # Simulate a previously-shipped built-in that no longer exists upstream.
    stale_hash = "a" * 64
    with (gates_dir / _CHECKSUM_MANIFEST).open("a", encoding="utf-8") as fh:
        fh.write(f"{stale_hash}  old-gate.sh\n")
    (gates_dir / ".agent-meta-managed").write_text(
        "demo-gate.sh\nold-gate.sh\n", encoding="utf-8"
    )

    _sync(agent_meta_root, project_root)

    entries = _manifest_entries(gates_dir)
    assert "old-gate.sh" not in entries
    assert "demo-gate.sh" in entries


def test_sync_refreshes_checksum_after_legitimate_gate_change(
    agent_meta_root, project_root
):
    _sync(agent_meta_root, project_root)
    gates_dir = project_root / ".claude" / "hooks" / "release-gates"
    source_gate = agent_meta_root / "hooks" / "1-generic" / "release-gates" / "demo-gate.sh"

    # Legitimate upstream change: flip the gate default (sync re-bakes the
    # {{RELEASE_GATE_ENABLED_DEFAULT}} placeholder, so deployed bytes change).
    source_gate.write_text(
        source_gate.read_text(encoding="utf-8").replace(
            "# enabled_by_default: false", "# enabled_by_default: true"
        ),
        encoding="utf-8",
    )
    _sync(agent_meta_root, project_root)

    entries = _manifest_entries(gates_dir)
    assert entries["demo-gate.sh"] == _sha256_of(gates_dir / "demo-gate.sh")


def test_sync_dry_run_does_not_write_checksum_manifest(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root, dry_run=True)
    gates_dir = project_root / ".claude" / "hooks" / "release-gates"
    assert not gates_dir.exists() or not (gates_dir / _CHECKSUM_MANIFEST).exists()


def test_failed_deploy_gets_no_checksum_entry(agent_meta_root, project_root):
    """A gate whose deploy failed must not be checksummed (fail-closed direction)."""
    gates_dir = project_root / ".claude" / "hooks" / "release-gates"
    gates_dir.mkdir(parents=True)
    (gates_dir / "demo-gate.sh").mkdir()  # directory blocks write_atomic

    log = _sync(agent_meta_root, project_root)

    assert log.warnings, "deploy failure should be logged as a warning"
    assert _manifest_entries(gates_dir) == {}


# --------------------------------------------------------------------------
# pre-release-check.sh: fail-closed pre-execution verification
# --------------------------------------------------------------------------


@pytest.fixture
def dispatcher_root(tmp_path):
    """Synthetic project with the real dispatcher template deployed."""
    root = tmp_path / "project"
    hooks_dir = root / "hooks"
    (hooks_dir / "release-gates").mkdir(parents=True)
    shutil.copy(_DISPATCHER_PATH, hooks_dir / "pre-release-check.sh")
    return root


def _run_dispatcher(project_root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_BASH, str(project_root / "hooks" / "pre-release-check.sh")],
        capture_output=True,
        text=True,
        env={"PROJECT_ROOT": str(project_root), "PATH": "/usr/bin:/bin:/usr/local/bin"},
    )


def _register_checksum(gates_dir: Path, name: str) -> None:
    with (gates_dir / _CHECKSUM_MANIFEST).open("a", encoding="utf-8") as fh:
        fh.write(f"{_sha256_of(gates_dir / name)}  {name}\n")


@_dispatcher_test
def test_allowlisted_gate_with_valid_checksum_runs(dispatcher_root):
    gates_dir = dispatcher_root / "hooks" / "release-gates"
    (gates_dir / "ok.sh").write_text('#!/bin/bash\necho "[INFO] ok: ran"\n', encoding="utf-8")
    (gates_dir / ".agent-meta-managed").write_text("ok.sh\n", encoding="utf-8")
    _register_checksum(gates_dir, "ok.sh")

    result = _run_dispatcher(dispatcher_root)

    assert "ok: ran" in result.stdout
    assert result.returncode == 0


@_dispatcher_test
def test_checksum_manifest_supports_comments_and_blank_lines(dispatcher_root):
    gates_dir = dispatcher_root / "hooks" / "release-gates"
    (gates_dir / "ok.sh").write_text('#!/bin/bash\necho "[INFO] ok: ran"\n', encoding="utf-8")
    (gates_dir / ".agent-meta-managed").write_text("ok.sh\n", encoding="utf-8")
    with (gates_dir / _CHECKSUM_MANIFEST).open("w", encoding="utf-8") as fh:
        fh.write("# header comment\n\n")
        fh.write(f"{_sha256_of(gates_dir / 'ok.sh')}  ok.sh\n")

    result = _run_dispatcher(dispatcher_root)

    assert "ok: ran" in result.stdout
    assert result.returncode == 0


@_dispatcher_test
def test_tampered_builtin_gate_is_refused_and_not_run(dispatcher_root):
    gates_dir = dispatcher_root / "hooks" / "release-gates"
    (gates_dir / "evil.sh").write_text(
        '#!/bin/bash\necho "[INFO] evil: ran"\n', encoding="utf-8"
    )
    (gates_dir / ".agent-meta-managed").write_text("evil.sh\n", encoding="utf-8")
    _register_checksum(gates_dir, "evil.sh")
    # Tamper AFTER checksum registration — the classic drive-by modification.
    (gates_dir / "evil.sh").write_text(
        '#!/bin/bash\necho "[INFO] evil: TAMPERED"\n', encoding="utf-8"
    )

    result = _run_dispatcher(dispatcher_root)

    assert "evil: ran" not in result.stdout  # never executed
    assert "SHA-256 checksum mismatch" in result.stdout
    # Built-in gate → remediation points at sync.py, not at hand-editing.
    assert "re-run sync.py" in result.stdout
    assert result.returncode == 1


@_dispatcher_test
def test_tampered_project_gate_remediation_mentions_sha256sum(dispatcher_root):
    gates_dir = dispatcher_root / "hooks" / "release-gates"
    (gates_dir / "mine.sh").write_text(
        '#!/bin/bash\necho "[INFO] mine: ran"\n', encoding="utf-8"
    )
    (gates_dir / ".allowed-gates").write_text("mine.sh\n", encoding="utf-8")
    _register_checksum(gates_dir, "mine.sh")
    (gates_dir / "mine.sh").write_text(
        '#!/bin/bash\necho "[INFO] mine: TAMPERED"\n', encoding="utf-8"
    )

    result = _run_dispatcher(dispatcher_root)

    assert "SHA-256 checksum mismatch" in result.stdout
    assert "sha256sum" in result.stdout  # project-gate escape hatch
    assert result.returncode == 1


@_dispatcher_test
def test_missing_checksum_manifest_fails_closed(dispatcher_root):
    gates_dir = dispatcher_root / "hooks" / "release-gates"
    (gates_dir / "ok.sh").write_text('#!/bin/bash\necho "[INFO] ok: ran"\n', encoding="utf-8")
    (gates_dir / ".agent-meta-managed").write_text("ok.sh\n", encoding="utf-8")
    # No .sha256-checksums at all — e.g. sync.py not yet run with v3.1.0.

    result = _run_dispatcher(dispatcher_root)

    assert "ok: ran" not in result.stdout
    assert "missing" in result.stdout
    assert "fail-closed" in result.stdout
    assert result.returncode == 1


@_dispatcher_test
def test_missing_checksum_entry_fails_closed(dispatcher_root):
    gates_dir = dispatcher_root / "hooks" / "release-gates"
    (gates_dir / "ok.sh").write_text('#!/bin/bash\necho "[INFO] ok: ran"\n', encoding="utf-8")
    (gates_dir / ".agent-meta-managed").write_text("ok.sh\n", encoding="utf-8")
    (gates_dir / _CHECKSUM_MANIFEST).write_text(
        "# header only, no entries\n", encoding="utf-8"
    )

    result = _run_dispatcher(dispatcher_root)

    assert "ok: ran" not in result.stdout
    assert "no checksum entry" in result.stdout
    assert result.returncode == 1


@_dispatcher_test
def test_no_allowlisted_gates_does_not_require_checksum_manifest(dispatcher_root):
    """Fail-closed applies only to gates about to run — zero-config stays green."""
    gates_dir = dispatcher_root / "hooks" / "release-gates"
    (gates_dir / "stray.sh").write_text("#!/bin/bash\necho ran\n", encoding="utf-8")
    # No allowlist manifests, no checksum manifest.

    result = _run_dispatcher(dispatcher_root)

    assert "not on the release-gates allowlist" in result.stdout
    assert result.returncode == 0
