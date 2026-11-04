"""Read-only topology probe harness — isolation, classification, JSON shape.

SPEC-orchestrator-topology-2026-11-03, P0 (issue #1077), Task 2.

The harness at ``scripts/topology-probe.py`` answers one probe question per
provider and emits one structured record per probe. These tests inject both
``which`` and the subprocess ``runner``, so no real CLI is required and the
suite never starts an interactive session:

* absent CLI          -> exactly ``not run — CLI unavailable`` (valid result)
* present + exit 0    -> ``evidence`` when the descriptor's evidence pattern
  matches, otherwise ``inconclusive`` (never a guess)
* timeout             -> ``inconclusive``
* non-zero exit       -> ``inconclusive``
* JSON shape          -> one record per provider (P0-1 ... P0-5), exact keys
* CLI surface         -> ``--list`` (5 lines), ``--probe <id> --dry-run``
  (prints the argv, runs nothing), ``--out`` (writes only that path)
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

_REPO_ROOT = Path(__file__).resolve().parents[1]

_spec = importlib.util.spec_from_file_location(
    "topology_probe", _REPO_ROOT / "scripts" / "topology-probe.py"
)
probe = importlib.util.module_from_spec(_spec)
sys.modules["topology_probe"] = probe  # dataclasses resolve __module__ via sys.modules
_spec.loader.exec_module(probe)

_REQUIRED_KEYS = {
    "provider",
    "probe_id",
    "question",
    "cli_path",
    "command",
    "exit_code",
    "result",
    "observed",
    "timestamp",
    "provider_version",
}
_EXPECTED_PROVIDERS = {"Opencode", "Claude", "Codex", "Mammouth", "KimiCode"}
_EXPECTED_IDS = {"P0-1", "P0-2", "P0-3", "P0-4", "P0-5"}


def _descriptor(probe_id):
    matches = [p for p in probe.PROBES if p.probe_id == probe_id]
    assert len(matches) == 1, f"expected exactly one descriptor for {probe_id}"
    return matches[0]


def _which(path_map):
    """Fake ``shutil.which``: only names in *path_map* resolve."""

    def which(name):
        return path_map.get(name)

    return which


def _completed(returncode=0, stdout="", stderr=""):
    return SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)


def _runner(handler=None):
    """Fake subprocess runner recording every argv it is asked to start."""

    def runner(argv, **kwargs):
        runner.calls.append(list(argv))
        if handler is None:
            return _completed()
        return handler(argv, **kwargs)

    runner.calls = []
    return runner


def _forbid_runner():
    def runner(argv, **kwargs):
        raise AssertionError(f"runner must not be called: {argv!r}")

    return runner


def test_absent_cli_records_the_exact_not_run_result():
    record = probe.run_probe(
        _descriptor("P0-2"),
        which=_which({}),
        runner=_forbid_runner(),
        timeout=20,
        project_root=_REPO_ROOT,
    )

    assert record["result"] == "not run — CLI unavailable"
    assert record["exit_code"] is None
    assert record["cli_path"] is None
    assert record["provider_version"] == ""
    assert record["provider"] == "Claude"
    assert record["probe_id"] == "P0-2"
    assert record["command"] == ["claude", "--help"]
    assert "not found on PATH" in record["observed"]


def test_present_cli_with_matching_evidence_is_evidence():
    descriptor = _descriptor("P0-5")
    assert descriptor.answerable is True

    def handler(argv, **kwargs):
        if argv[-1] == "--version":
            return _completed(stdout="kimi 2.1.1\n")
        return _completed(stdout="  --agent <name>   Agent profile\n")

    record = probe.run_probe(
        descriptor,
        which=_which({"kimi": "/usr/local/bin/kimi"}),
        runner=_runner(handler),
        timeout=20,
        project_root=_REPO_ROOT,
    )

    assert record["result"] == "evidence"
    assert record["exit_code"] == 0
    assert record["cli_path"] == "/usr/local/bin/kimi"
    assert record["command"] == ["/usr/local/bin/kimi", "--help"]
    assert record["provider_version"] == "kimi 2.1.1"
    assert "--agent" in record["observed"]


def test_timeout_is_inconclusive_not_an_error():
    descriptor = _descriptor("P0-1")

    def handler(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs.get("timeout", 20))

    record = probe.run_probe(
        descriptor,
        which=_which({"opencode": "/usr/bin/opencode"}),
        runner=_runner(handler),
        timeout=20,
        project_root=_REPO_ROOT,
    )

    assert record["result"] == "inconclusive"
    assert "timeout" in record["observed"].lower()
    assert record["exit_code"] is None


def test_non_zero_exit_is_inconclusive():
    record = probe.run_probe(
        _descriptor("P0-2"),
        which=_which({"claude": "/usr/bin/claude"}),
        runner=_runner(lambda argv, **kwargs: _completed(returncode=2, stderr="boom\n")),
        timeout=20,
        project_root=_REPO_ROOT,
    )

    assert record["result"] == "inconclusive"
    assert record["exit_code"] == 2
    assert "boom" in record["observed"]


def test_unanswerable_probe_never_claims_evidence():
    """A present, healthy CLI does not turn an unprovable question into evidence."""
    record = probe.run_probe(
        _descriptor("P0-2"),
        which=_which({"claude": "/usr/bin/claude"}),
        runner=_runner(lambda argv, **kwargs: _completed(stdout="Usage: claude\n")),
        timeout=20,
        project_root=_REPO_ROOT,
    )

    assert record["result"] == "inconclusive"
    assert "cannot" in record["observed"].lower()


def test_all_five_records_have_the_exact_json_shape():
    records = probe.run_probes(
        list(probe.PROBES),
        which=_which({}),
        runner=_forbid_runner(),
        timeout=20,
        project_root=_REPO_ROOT,
    )

    assert len(records) == 5
    assert {r["probe_id"] for r in records} == _EXPECTED_IDS
    assert {r["provider"] for r in records} == _EXPECTED_PROVIDERS
    for record in records:
        assert set(record) == _REQUIRED_KEYS
        assert isinstance(record["command"], list) and record["command"]
        assert isinstance(record["question"], str) and record["question"]
        assert record["result"] in {
            "evidence",
            "not run — CLI unavailable",
            "inconclusive",
        }
        # JSON round-trip: the record itself must be serialisable.
        json.dumps(record)


def test_list_prints_five_lines_and_exits_zero():
    out = _StringSink()
    rc = probe.main(
        ["--list"],
        which=_which({}),
        runner=_forbid_runner(),
        project_root=_REPO_ROOT,
        stdout=out,
    )

    assert rc == 0
    lines = [line for line in out.getvalue().splitlines() if line.strip()]
    assert len(lines) == 5
    assert lines[0].startswith("P0-1")


def test_dry_run_prints_the_command_and_runs_nothing():
    out = _StringSink()
    rc = probe.main(
        ["--probe", "P0-2", "--dry-run"],
        which=_which({"claude": "/usr/bin/claude"}),
        runner=_forbid_runner(),
        project_root=_REPO_ROOT,
        stdout=out,
    )

    assert rc == 0
    assert "/usr/bin/claude --help" in out.getvalue()
    assert "P0-2" in out.getvalue()


def test_out_flag_writes_only_the_given_path(tmp_path):
    target = tmp_path / "records.json"
    out = _StringSink()
    rc = probe.main(
        ["--probe", "P0-1", "--out", str(target)],
        which=_which({}),
        runner=_forbid_runner(),
        project_root=_REPO_ROOT,
        stdout=out,
    )

    assert rc == 0
    assert out.getvalue() == ""
    records = json.loads(target.read_text(encoding="utf-8"))
    assert len(records) == 1
    assert records[0]["probe_id"] == "P0-1"
    assert set(records[0]) == _REQUIRED_KEYS


def test_unknown_probe_id_is_a_usage_error():
    try:
        probe.main(
            ["--probe", "P0-9"],
            which=_which({}),
            runner=_forbid_runner(),
            project_root=_REPO_ROOT,
            stdout=_StringSink(),
        )
    except SystemExit as exc:
        assert exc.code == 2
    else:  # pragma: no cover - defensive
        raise AssertionError("unknown probe id must exit 2")


class _StringSink:
    """Minimal ``print(file=...)`` sink, avoids importing io in every test."""

    def __init__(self):
        self._chunks = []

    def write(self, text):
        self._chunks.append(text)

    def flush(self):
        pass

    def getvalue(self):
        return "".join(self._chunks)
