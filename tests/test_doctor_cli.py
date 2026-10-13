"""Task 0d.3 (IC-22): ``sync.py --doctor`` CLI -- write boundary, exit codes, JSON.

Covers AC-39 (SHA-256 snapshot, exit-code matrix), AC-42 (Codex hard cap),
AC-75 / AC-95 / AC-98 (sink-bound output, ``doctor.out-outside-tmp-sink``,
``doctor.tmp-sink.disabled``) and the ``--strict`` rule for
``doctor.registry-invalid``.

Runtime note: the registry seed ``sync-pending`` runs ``sync.py --check
--dry-run`` as a subprocess (about 25 s on the real repository). Only the two
snapshot tests (project install and self-hosting) execute the real command; all
other tests run ``main()`` in-process and replace that single subprocess call.
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

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_ROOT / "scripts"))

import sync  # noqa: E402
from lib import doctor, doctor_detectors  # noqa: E402
from lib.consistency.report import Severity  # noqa: E402
from lib.doctor import DoctorFinding, DoctorReport  # noqa: E402

_SYNC_PY = _ROOT / "scripts" / "sync.py"
_SINK = "scratch/out"

# Top-level entries a self-contained agent-meta copy needs to run the doctor.
_AGENT_META_PARTS = (
    "agents", "commands", "config", "hooks", "rules", "schemas", "scripts",
    "snippets", "speech", "templates", "platform-configs", "VERSION",
)


# ------------------------------------------------------------------ helpers

def _project_yaml(providers="[Claude]", sink=_SINK, enabled=True) -> str:
    return (
        f"ai-providers: {providers}\n"
        "dod-preset: rapid-prototyping\n"
        "roles: [developer]\n"
        "project: {name: doctor-cli, prefix: dc, short: doctor-cli}\n"
        "variables: {PROJECT_NAME: doctor-cli}\n"
        "repo_containment:\n"
        "  tmp-sink:\n"
        f"    enabled: {'true' if enabled else 'false'}\n"
        f"    path: {sink}\n"
    )


def _make_project(root: Path, **kwargs) -> Path:
    config = root / ".meta-config" / "project.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(_project_yaml(**kwargs), encoding="utf-8")
    return config


def _copy_agent_meta(dst: Path) -> Path:
    dst.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for part in _AGENT_META_PARTS:
        src = _ROOT / part
        if src.is_dir():
            shutil.copytree(src, dst / part, ignore=ignore)
        else:
            shutil.copy2(src, dst / part)
    return dst


def _snapshot(*roots: Path, exclude: tuple = ()) -> dict:
    """SHA-256 of every file below *roots*; *exclude* = absolute sink directories."""
    result = {}
    for root in roots:
        for path in sorted(root.rglob("*")):
            if not path.is_file() or any(path.is_relative_to(e) for e in exclude):
                continue
            result[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def _cli(project: Path, *args: str, env=None) -> subprocess.CompletedProcess:
    config = project / ".meta-config" / "project.yaml"
    return subprocess.run(
        [sys.executable, str(project_script(project)), "--config", str(config), *args],
        capture_output=True, text=True, cwd=str(project), encoding="utf-8",
        env=env, timeout=300)


def project_script(project: Path) -> Path:
    local = project / "scripts" / "sync.py"
    return local if local.is_file() else _SYNC_PY


class _Proc:
    def __init__(self, code):
        self.returncode, self.stdout, self.stderr = code, "", ""


@pytest.fixture
def fake_command(monkeypatch):
    """Replace only the ``sync.py ...`` subprocess of the ``command`` detector."""
    real_run = subprocess.run
    calls = []

    def run(cmd, *a, **kw):
        if isinstance(cmd, list) and len(cmd) > 2 and str(cmd[1]).endswith("sync.py"):
            calls.append(cmd)
            return _Proc(0)
        return real_run(cmd, *a, **kw)

    monkeypatch.setattr(doctor_detectors.subprocess, "run", run)
    return calls


def _main(monkeypatch, capsys, project: Path, *args: str):
    """Run ``sync.main()`` in-process; returns (exit code, stdout, stderr)."""
    config = project / ".meta-config" / "project.yaml"
    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "argv", ["sync.py", "--config", str(config), "--doctor", *args])
    with pytest.raises(SystemExit) as exc:
        sync.main()
    captured = capsys.readouterr()
    return exc.value.code, captured.out, captured.err


def _finding(severity, check="doctor.x", issue_id="x", registry=None) -> DoctorFinding:
    return DoctorFinding(
        severity, check, "f.md", "message", "suggestion", issue_id=issue_id,
        verified_state="VERIFIED-SOURCE", fix_owner="project-config",
        evidence="source: t (2026-10-11)",
        severity_registry=(registry or severity).value)


def _report(*findings) -> DoctorReport:
    return DoctorReport(tuple(findings), (), 1, "9.9.9")


@pytest.fixture
def project(tmp_path):
    root = tmp_path / "project"
    _make_project(root)
    return root


# ------------------------------------------------- AC-39 / AC-95: write boundary

def test_doctor_writes_only_report_into_sink_project_install(tmp_path):
    """Real ``command`` detector; agent-meta is a separate copy (submodule layout)."""
    meta = _copy_agent_meta(tmp_path / "agent-meta")
    project = tmp_path / "project"
    _make_project(project)
    sink = project / _SINK
    before = _snapshot(project, meta, exclude=(sink,))
    # --doctor itself must suppress bytecode: do not inherit the suppression
    env = {k: v for k, v in os.environ.items() if k != "PYTHONDONTWRITEBYTECODE"}
    out_rel = f"{_SINK}/doctor/report.json"

    result = subprocess.run(
        [sys.executable, str(meta / "scripts" / "sync.py"), "--config",
         str(project / ".meta-config" / "project.yaml"), "--doctor", "--json",
         "--out", out_rel],
        capture_output=True, text=True, cwd=str(project), encoding="utf-8",
        env=env, timeout=300)

    assert result.returncode == 0, result.stderr
    assert _snapshot(project, meta, exclude=(sink,)) == before
    assert not list(meta.rglob("*.pyc")) and not list(project.rglob("*.pyc"))
    written = sorted(p.relative_to(sink).as_posix() for p in sink.rglob("*") if p.is_file())
    assert written == ["doctor/report.json"]                       # AC-95: exactly one file
    stdout_json = json.loads(result.stdout)
    assert json.loads((sink / "doctor" / "report.json").read_text(encoding="utf-8")) == stdout_json
    assert any(f["issue_id"] == "sync-pending" for f in stdout_json["findings"])  # command ran


def test_doctor_without_out_writes_nothing_self_hosting(tmp_path):
    """Self-hosting: project root == agent-meta root (enum update must not run)."""
    meta = _copy_agent_meta(tmp_path / "self-hosting")
    _make_project(meta)
    before = _snapshot(meta)
    result = _cli(meta, "--doctor", "--json")
    assert result.returncode == 0, result.stderr
    assert _snapshot(meta) == before                                # no sync.log, env, schema, pyc
    assert json.loads(result.stdout)["summary"]["registry_version"] == 1
    assert not (meta / _SINK).exists()


# ------------------------------------------------------ exit-code matrix (AC-39)

_E, _W, _I = Severity.ERROR, Severity.WARNING, Severity.INFO


@pytest.mark.parametrize("findings,strict,expected", [
    ((), False, 0),
    ((_finding(_I),), False, 0),
    ((_finding(_W),), False, 0),
    ((_finding(_E),), False, 1),
    ((), True, 0),
    ((_finding(_I),), True, 0),
    ((_finding(_W),), True, 1),
    ((_finding(_E),), True, 1),
    ((_finding(_W, "doctor.registry-invalid", "", _E),), False, 0),   # WARNING without --strict
    ((_finding(_W, "doctor.registry-invalid", "", _E),), True, 2),    # ERROR / exit 2 with --strict
    ((_finding(_E), _finding(_W, "doctor.registry-invalid", "", _E)), True, 2),
])
def test_exit_code_matrix(monkeypatch, capsys, project, findings, strict, expected):
    monkeypatch.setattr(doctor, "run_doctor", lambda *a, **k: _report(*findings))
    args = ("--json", "--strict") if strict else ("--json",)
    code, out, _err = _main(monkeypatch, capsys, project, *args)
    assert code == expected
    data = json.loads(out)
    assert data["summary"]["total"] == len(findings)
    if strict and expected == 2:
        invalid = [f for f in data["findings"] if f["check"] == "doctor.registry-invalid"]
        assert invalid[0]["severity"] == "ERROR" and invalid[0]["severity_registry"] == "ERROR"


def test_exit_code_runtime_error_is_two(monkeypatch, capsys, project):
    def boom(*a, **k):
        raise RuntimeError("internal")
    monkeypatch.setattr(doctor, "run_doctor", boom)
    code, out, err = _main(monkeypatch, capsys, project, "--json")
    assert code == 2 and out == ""
    assert "doctor.internal-error" in err and "RuntimeError" in err


def test_registry_invalid_real_registry_strict(monkeypatch, capsys, project, fake_command):
    """Broken registry file: WARNING / exit 0 normally, exit 2 with --strict."""
    meta = project.parent / "agent-meta"
    (meta / "config").mkdir(parents=True)
    (meta / "config" / "known-issues.yaml").write_text("registry-version: 2\n", encoding="utf-8")
    real_load = doctor.load_known_issues
    monkeypatch.setattr(doctor, "load_known_issues", lambda root: real_load(meta))
    code, out, _ = _main(monkeypatch, capsys, project, "--json")
    assert code == 0
    assert [f["check"] for f in json.loads(out)["findings"]] == ["doctor.registry-invalid"]
    assert json.loads(out)["findings"][0]["severity"] == "WARNING"
    code, out, _ = _main(monkeypatch, capsys, project, "--json", "--strict")
    assert code == 2


# ------------------------------------------------------------- AC-42: Codex cap

def test_codex_instruction_file_at_hard_cap_exits_one(monkeypatch, capsys, tmp_path, fake_command):
    root = tmp_path / "codex"
    _make_project(root, providers="[Codex]")
    (root / "AGENTS.md").write_bytes(b"x" * 32768)
    code, out, _ = _main(monkeypatch, capsys, root, "--json")
    assert code == 1
    hits = [f for f in json.loads(out)["findings"] if f["issue_id"] == "context-hard-cap-truncation"]
    assert [(f["severity"], f["provider"], f["file"]) for f in hits] == [("ERROR", "Codex", "AGENTS.md")]


def test_codex_below_hard_cap_is_clean(monkeypatch, capsys, tmp_path, fake_command):
    root = tmp_path / "codex"
    _make_project(root, providers="[Codex]")
    (root / "AGENTS.md").write_bytes(b"x" * 32767)
    code, out, _ = _main(monkeypatch, capsys, root, "--json")
    assert code == 0
    assert not [f for f in json.loads(out)["findings"] if f["issue_id"] == "context-hard-cap-truncation"]


# ------------------------------------------- AC-75 / AC-98: --out and the tmp-sink

@pytest.mark.parametrize("target", [
    "report.json",                       # project root
    ".tmp/doctor/r.json",                # not the configured sink
    "../escape.json",                    # traversal
    f"{_SINK}/report.json",              # inside the sink, outside doctor/
    f"{_SINK}/doctor/../report.json",
    f"{_SINK}/doctor",                   # the directory itself
])
def test_out_outside_tmp_sink_exits_two_and_writes_nothing(
        monkeypatch, capsys, project, fake_command, target):
    before = _snapshot(project.parent)
    code, out, err = _main(monkeypatch, capsys, project, "--json", "--out", target)
    assert code == 2 and out == ""
    assert "doctor.out-outside-tmp-sink" in err
    assert _snapshot(project.parent) == before
    assert fake_command == []                      # rejected before the slow run


def test_out_absolute_path_outside_sink_is_rejected(monkeypatch, capsys, project, fake_command, tmp_path):
    code, _out, err = _main(monkeypatch, capsys, project, "--out", str(tmp_path / "x.json"))
    assert code == 2 and "doctor.out-outside-tmp-sink" in err


def test_out_symlink_escape_is_rejected(monkeypatch, capsys, project, fake_command, tmp_path):
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    (project / _SINK).mkdir(parents=True)
    try:
        (project / _SINK / "doctor").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    code, _out, err = _main(monkeypatch, capsys, project, "--out", f"{_SINK}/doctor/r.json")
    assert code == 2 and "doctor." in err
    assert not list(outside.iterdir())


def test_out_inside_sink_writes_exactly_one_file(monkeypatch, capsys, project, fake_command):
    before = _snapshot(project, exclude=(project / _SINK,))
    code, out, _ = _main(monkeypatch, capsys, project, "--json", "--out",
                         f"{_SINK}/doctor/20261011-120000.json")
    assert code == 0
    files = [p for p in (project / _SINK).rglob("*") if p.is_file()]
    assert [p.name for p in files] == ["20261011-120000.json"]
    assert json.loads(files[0].read_text(encoding="utf-8")) == json.loads(out)
    assert _snapshot(project, exclude=(project / _SINK,)) == before


def test_out_without_json_flag_still_writes_json(monkeypatch, capsys, project, fake_command):
    code, out, _ = _main(monkeypatch, capsys, project, "--out", f"{_SINK}/doctor/r.json")
    assert code == 0 and out.startswith("Doctor:")                    # text on stdout
    data = json.loads((project / _SINK / "doctor" / "r.json").read_text(encoding="utf-8"))
    assert "findings" in data and "summary" in data


def test_tmp_sink_disabled_out_exits_two_with_precedence(
        monkeypatch, capsys, tmp_path, fake_command):
    root = tmp_path / "off"
    _make_project(root, enabled=False)
    before = _snapshot(root)
    for target in ("report.json", f"{_SINK}/doctor/r.json"):          # outside AND inside path
        code, out, err = _main(monkeypatch, capsys, root, "--json", "--out", target)
        assert code == 2 and out == ""
        assert "doctor.tmp-sink.disabled" in err
        assert "out-outside" not in err
    assert _snapshot(root) == before and fake_command == []


def test_tmp_sink_disabled_without_out_runs(monkeypatch, capsys, tmp_path, fake_command):
    root = tmp_path / "off"
    _make_project(root, enabled=False)
    before = _snapshot(root)
    code, out, _ = _main(monkeypatch, capsys, root, "--json")
    assert code == 0
    data = json.loads(out)
    assert data["summary"]["registry_version"] == 1
    skipped = {(s["issue_id"], s["reason"]) for s in data["summary"]["skipped"]}
    assert ("tmp-sink-outside-repo-or-system-temp", "predicate") in skipped    # AC-98 (d)
    assert _snapshot(root) == before
    assert fake_command and fake_command[0][2:] == ["--check", "--dry-run"]   # stdout-only command runs


# ------------------------------------------------------------- --json / output

def test_json_is_valid_deterministic_and_stdout_clean(monkeypatch, capsys, project, fake_command):
    first = _main(monkeypatch, capsys, project, "--json")
    second = _main(monkeypatch, capsys, project, "--json")
    assert first[0] == second[0] == 0
    assert first[1] == second[1]                                       # byte-identical
    data = json.loads(first[1])                                        # stdout is only the JSON object
    assert set(data) == {"findings", "summary"}
    assert {"total", "errors", "warnings", "infos", "registry_version",
            "agent_meta_version", "skipped", "severity"} <= set(data["summary"])
    assert data["summary"]["total"] == len(data["findings"])
    keys = [(f["severity"], f["issue_id"], f["provider"], f["file"]) for f in data["findings"]]
    rank = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    assert [rank[k[0]] for k in keys] == sorted(rank[k[0]] for k in keys)
    assert "DRY-RUN" in first[2] or "DRY-RUN" not in first[1]          # banner never on stdout


def test_text_output_lists_findings(monkeypatch, capsys, project, fake_command):
    code, out, _ = _main(monkeypatch, capsys, project)
    assert code == 0 and out.startswith("Doctor: ")
    assert "doctor.sync-pending" not in out                           # command exit 0 -> no finding


def test_provider_filter_reports_ignored_names(monkeypatch, capsys, project, fake_command):
    code, out, _ = _main(monkeypatch, capsys, project, "--json", "--provider", "Claude", "Nope")
    assert code == 0
    infos = [f for f in json.loads(out)["findings"] if f["check"] == "doctor.provider-filter"]
    assert [f["provider"] for f in infos] == ["Nope"]


def test_doctor_sets_read_only_and_skips_common_tail(monkeypatch, capsys, project, fake_command):
    monkeypatch.setattr(sync, "_run_common_tail",
                        lambda ctx: pytest.fail("common tail must not run for --doctor"))
    code, _out, _err = _main(monkeypatch, capsys, project, "--json")
    assert code == 0
    assert not (project / "sync.log").exists()
    assert not list((project / ".meta-config").glob("env.*"))


# ------------------------------------------------------------------- wiring

def test_doctor_is_registered_and_documented_in_help(capsys, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["sync.py", "--help"])
    with pytest.raises(SystemExit):
        sync.main()
    help_text = capsys.readouterr().out
    for flag in ("--doctor", "--strict", "--provider", "--out"):
        assert flag in help_text
    assert any("doctor" in getattr(h, "__name__", "") for _p, h in sync._MODE_HANDLERS)


def test_doctor_modules_do_not_branch_on_provider_identity():
    text = (_ROOT / "scripts" / "lib" / "cli_commands.py").read_text(encoding="utf-8")
    start = text.index("_DOCTOR_SUBDIR")
    block = text[start:text.index("def _handle_validate(")]
    for name in ("Claude", "Codex", "Gemini", "OpenCode"):
        assert f'== "{name}"' not in block and f"== '{name}'" not in block
