"""``measure_artifacts`` and ``sync.py --context-report`` (IC-11, AC-04, AC-75/94/98).

Run: python -m pytest tests/test_context_report.py -q
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync.py"
MODULE = REPO_ROOT / "scripts" / "lib" / "context_report.py"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402

_CAPS = {
    "Alpha": {
        "context_file": "ENTRY.md",
        "agents_dir": ".alpha/agents",
        "agent_ext": ".md",
        "has_rules": True,
        "rules_dir": ".alpha/rules",
        "roster_in_harness": True,
        "context_hard_cap_bytes": 100,
        "context_soft_cap_lines": 5,
    },
    "Beta": {"context_file": "AGENTS.md", "agents_dir": ".beta/agents"},
}


def _write(path: Path, text: str) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))
    return len(text.encode("utf-8"))


def test_measure_artifacts_bytes_match_independent_count(tmp_path):
    entry = _write(tmp_path / "ENTRY.md", "# Entry\nümlaut line\n" * 20)
    r1 = _write(tmp_path / ".alpha/rules/a.md", "rule a\n" * 7)
    r2 = _write(tmp_path / ".alpha/rules/b.md", "rule b\n" * 3)
    orch = _write(tmp_path / ".alpha/agents/orchestrator.md", "orch\n" * 11)
    dev = _write(tmp_path / ".alpha/agents/developer.md", "dev\n" * 5)
    report = cr.measure_artifacts(tmp_path, ["Alpha", "Beta"], _CAPS)
    alpha = report["Alpha"]
    for name, expected in (("entry-file", entry), ("rules", r1 + r2),
                           ("orchestrator", orch), ("harness-roster", orch + dev)):
        assert abs(alpha[name]["bytes"] - expected) <= expected * 0.01
    assert alpha["always-loaded"]["bytes"] == entry + r1 + r2 + orch + dev
    assert alpha["entry-file"]["tokens_est"] == entry // 4
    assert alpha["entry-file"]["cap"] == 100 and alpha["entry-file"]["cap_kind"] == "hard-bytes"
    assert "Beta" not in report  # nothing on disk -> omitted


def test_over_hard_cap_finding(tmp_path):
    _write(tmp_path / "ENTRY.md", "x" * 101)
    report = cr.measure_artifacts(tmp_path, ["Alpha"], _CAPS)
    findings = cr.find_over_hard_cap(report)
    assert len(findings) == 1 and "context.over-hard-cap" in findings[0]
    # boundary is inclusive: exactly at the cap already counts (IC-10)
    _write(tmp_path / "ENTRY.md", "x" * 100)
    assert len(cr.find_over_hard_cap(cr.measure_artifacts(tmp_path, ["Alpha"], _CAPS))) == 1
    _write(tmp_path / "ENTRY.md", "x" * 99)
    assert cr.find_over_hard_cap(cr.measure_artifacts(tmp_path, ["Alpha"], _CAPS)) == []


def test_module_has_no_systemtemp_or_dot_tmp_literal():
    """AC-75/AC-94 grep guard over the new module."""
    text = MODULE.read_text(encoding="utf-8")
    assert not re.search(r"tempfile|gettempdir|/tmp|%TEMP%|TMPDIR|mkdtemp|\.tmp\b", text)


def _project(root: Path, sink_enabled: bool = True) -> Path:
    (root / ".meta-config").mkdir(parents=True)
    cfg = root / ".meta-config" / "project.yaml"
    cfg.write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers: [Claude]\n"
        "dod-preset: rapid-prototyping\n"
        "repo_containment:\n"
        "  tmp-sink:\n"
        "    enabled: {}\n"
        "    path: scratch/out\n"
        "variables:\n  PROJECT_NAME: ctxrep\n  PROJECT_PREFIX: cr\n".format(
            "true" if sink_enabled else "false"),
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    return cfg


def _snapshot(root: Path, skip: str) -> dict:
    out = {}
    for p in sorted(root.rglob("*")):
        rel = p.relative_to(root)
        if p.is_file() and ".git" not in rel.parts and rel.parts[:2] != tuple(skip.split("/")):
            out[str(rel)] = p.read_bytes()
    return out


def _run(root: Path, cfg: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--config", str(cfg), *args],
        cwd=root, capture_output=True, text=True, timeout=600,
    )


@pytest.fixture(scope="module")
def reported(tmp_path_factory):
    root = tmp_path_factory.mktemp("ctxrep")
    cfg = _project(root)
    before = _snapshot(root, "scratch/out")
    result = _run(root, cfg, "--context-report", "--json")
    return root, before, result


def test_cli_json_report_and_independent_bytes(reported):
    root, _before, result = reported
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    report = json.loads(result.stdout)
    entry = report["Claude"]["entry-file"]
    assert {"bytes", "lines", "tokens_est", "cap", "cap_kind"} <= set(entry)
    works = list((root / "scratch" / "out" / "context-report").glob("*/work/CLAUDE.md"))
    assert len(works) == 1
    independent = len(works[0].read_bytes())
    assert independent > 0
    assert abs(entry["bytes"] - independent) <= independent * 0.01


def test_cli_writes_only_below_configured_sink(reported):
    root, before, _result = reported
    assert _snapshot(root, "scratch/out") == before
    assert list((root / "scratch" / "out" / "context-report").glob("*/report.json"))


def test_context_report_never_uses_tempfile(tmp_path, monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("system temp must not be used")

    for name in ("mkdtemp", "mkstemp", "gettempdir", "NamedTemporaryFile", "TemporaryDirectory"):
        monkeypatch.setattr(tempfile, name, boom)
    cfg = _project(tmp_path)
    mappings = {"Claude": {"context_file": "CLAUDE.md"}}
    code = cr.run_context_report(
        project_root=tmp_path, agent_meta_root=REPO_ROOT, config_path=cfg,
        config={"repo_containment": {"tmp-sink": {"enabled": True, "path": "scratch/out"}}},
        providers=["Claude"], mappings=mappings, as_json=True)
    assert code == 0
    assert (tmp_path / "scratch" / "out" / "context-report").is_dir()


def test_cli_disabled_sink_exits_2_and_writes_nothing(tmp_path):
    cfg = _project(tmp_path, sink_enabled=False)
    before = _snapshot(tmp_path, "scratch/out")
    result = _run(tmp_path, cfg, "--context-report")
    assert result.returncode == 2, result.stdout[-800:] + result.stderr[-800:]
    assert "tmp-sink.disabled" in result.stderr
    assert _snapshot(tmp_path, "scratch/out") == before
    assert not (tmp_path / "scratch").exists()


def test_cli_reference_documents_context_report():
    text = (REPO_ROOT / "docs" / "api" / "cli-reference.md").read_text(encoding="utf-8")
    assert "--context-report" in text


def _run_report(tmp_path, before_run=None, **kw):
    cfg = _project(tmp_path)
    if before_run is not None:
        before_run()
    args = dict(
        project_root=tmp_path, agent_meta_root=REPO_ROOT, config_path=cfg,
        config={"repo_containment": {"tmp-sink": {"enabled": True, "path": "scratch/out"}}},
        providers=["Claude"], mappings={"Claude": {"context_file": "CLAUDE.md"}},
        as_json=True)
    args.update(kw)
    return cr.run_context_report(**args)


def test_render_failure_exits_2_with_own_code(tmp_path, monkeypatch, capsys):
    def boom(*_a, **_k):
        raise FileNotFoundError("git")

    code = _run_report(tmp_path, lambda: monkeypatch.setattr(subprocess, "run", boom))
    assert code == 2
    assert "context-report.render-failed" in capsys.readouterr().err


def test_old_work_dirs_survive_failed_render(tmp_path, monkeypatch):
    old = tmp_path / "scratch" / "out" / "context-report" / "old-run" / "work"
    old.mkdir(parents=True)
    def boom(*_a, **_k):
        raise OSError("x")

    assert _run_report(tmp_path, lambda: monkeypatch.setattr(subprocess, "run", boom)) == 2
    assert old.is_dir()


def test_empty_report_warns_but_exits_0(tmp_path, capsys):
    assert _run_report(tmp_path, mappings={"Claude": {}}) == 0
    assert "empty report" in capsys.readouterr().err


def test_profile_both_note_names_requested_profile(tmp_path, capsys):
    assert _run_report(tmp_path, profile="both") == 0
    err = capsys.readouterr().err
    assert "'both'" in err and "'compact'" not in err


def test_rules_skipped_without_rules_dir(tmp_path):
    _write(tmp_path / ".claude/rules/a.md", "rule\n")
    caps = {"Claude": {"has_rules": True}}
    assert "rules" not in cr.measure_artifacts(tmp_path, ["Claude"], caps).get("Claude", {})
    merged = cr.merge_provider_mappings({"providers": {"Claude": {"has_rules": True}}}, {})
    assert merged["Claude"]["rules_dir"] == ".claude/rules"
    assert "rules" in cr.measure_artifacts(tmp_path, ["Claude"], merged)["Claude"]


def test_cli_reference_documents_exit_codes_and_limitation():
    text = (REPO_ROOT / "docs" / "api" / "cli-reference.md").read_text(encoding="utf-8")
    assert "context-report.render-failed" in text
    assert "3-project" in text
