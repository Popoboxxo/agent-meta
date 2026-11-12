"""Tests for scripts/check_plan_refs.py (git-ref based plan freshness check)."""
from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_plan_refs.py"
_spec = importlib.util.spec_from_file_location("check_plan_refs", _SCRIPT)
cpr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cpr)

_GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"]


def _git(repo: Path, *args: str) -> None:
    subprocess.run(_GIT + ["-C", str(repo)] + list(args), check=True, capture_output=True)


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    r = tmp_path / "repo"
    (r / "scripts" / "lib").mkdir(parents=True)
    (r / "docs").mkdir()
    (r / "scripts" / "lib" / "mod.py").write_text(
        "\n".join(["# l%d" % i for i in range(1, 20)] + ["def real_func():", "    pass", ""]),
        encoding="utf-8",
    )
    (r / "docs" / "a.md").write_text("hello\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(r)], check=True)
    _git(r, "add", "-A")
    _git(r, "commit", "-q", "-m", "init")
    return r


def _run(tmp_path, repo, plan_text, extra=(), runner=None, capsys=None):
    plan = tmp_path / "plan.md"
    plan.write_text(plan_text, encoding="utf-8")
    argv = ["--plans", str(plan), "--repo", str(repo), "--ref", "HEAD", "--json", *extra]
    rc = cpr.main(argv, issue_runner=runner)
    out = capsys.readouterr().out
    return rc, json.loads(out)


def _classes(data):
    return [f["cls"] for p in data["plans"] for f in p["findings"]]


def test_existing_file_no_finding(tmp_path, repo, capsys):
    rc, data = _run(tmp_path, repo, "see `docs/a.md` here\n", ["--no-issues"], capsys=capsys)
    assert rc == 0 and _classes(data) == []


def test_missing_file_is_error(tmp_path, repo, capsys):
    rc, data = _run(tmp_path, repo, "- Modify: `docs/nope.md`\n", ["--no-issues"], capsys=capsys)
    assert rc == 1 and _classes(data) == ["FILE_MISSING"]


def test_missing_file_in_prose_only_warns(tmp_path, repo, capsys):
    rc, data = _run(tmp_path, repo, "see `docs/nope.md`\n", ["--no-issues"], capsys=capsys)
    f = data["plans"][0]["findings"]
    assert rc == 0 and [(x["cls"], x["sev"]) for x in f] == [("FILE_MISSING", "WARN")]


def test_line_out_of_range(tmp_path, repo, capsys):
    rc, data = _run(tmp_path, repo, "see `docs/a.md:99`\n", ["--no-issues"], capsys=capsys)
    assert rc == 0 and _classes(data) == ["LINE_OUT_OF_RANGE"]


def test_symbol_missing_in_named_file(tmp_path, repo, capsys):
    plan = "## Frische-Check-Referenzen\n\n- `scripts/lib/mod.py` (`real_func`, `ghost_func`)\n"
    rc, data = _run(tmp_path, repo, plan, ["--no-issues"], capsys=capsys)
    assert rc == 1 and _classes(data) == ["SYMBOL_MISSING"]
    assert data["plans"][0]["findings"][0]["ref"] == "ghost_func"


def test_symbol_without_file_only_warns(tmp_path, repo, capsys):
    plan = "## Frische-Check-Referenzen\n\n- Symbole: `real_func`, `ghost_func`\n"
    rc, data = _run(tmp_path, repo, plan, ["--no-issues"], capsys=capsys)
    assert rc == 0
    f = data["plans"][0]["findings"]
    assert [(x["cls"], x["sev"], x["ref"]) for x in f] == [("SYMBOL_MISSING", "WARN", "ghost_func")]


def test_anchor_drift_reports_actual_line(tmp_path, repo, capsys):
    plan = "- `scripts/lib/mod.py:5` -> `real_func()`\n"
    rc, data = _run(tmp_path, repo, plan, ["--no-issues"], capsys=capsys)
    f = data["plans"][0]["findings"]
    assert [x["cls"] for x in f] == ["ANCHOR_DRIFT"]
    assert "20" in f[0]["hint"]


def test_anchor_within_tolerance_ok(tmp_path, repo, capsys):
    plan = "- `scripts/lib/mod.py:15` -> `real_func()`\n"
    rc, data = _run(tmp_path, repo, plan, ["--no-issues"], capsys=capsys)
    assert _classes(data) == []


def test_create_line_with_existing_file_warns(tmp_path, repo, capsys):
    plan = "## File Structure\n\n- Create: `docs/a.md` - new\n- Create: `docs/new.md`\n"
    rc, data = _run(tmp_path, repo, plan, ["--no-issues"], capsys=capsys)
    f = data["plans"][0]["findings"]
    assert rc == 0 and [(x["cls"], x["sev"], x["ref"]) for x in f] == [("CREATE_EXISTS", "WARN", "docs/a.md")]


def test_unknown_issue_is_error_and_closed_is_info(tmp_path, repo, capsys):
    states = {1: "OPEN", 2: "CLOSED", 3: None}
    plan = "## Frische-Check-Referenzen\n\n- Issues: #1, #2, #3, #1086i\n- `#2` done\n"
    rc, data = _run(tmp_path, repo, plan, runner=states.get, capsys=capsys)
    got = sorted((x["cls"], x["ref"]) for x in data["plans"][0]["findings"])
    assert rc == 1
    assert got == [("ISSUE_MISSING", "#3")]  # #2 line marks done


def test_issue_closed_info(tmp_path, repo, capsys):
    plan = "## Frische-Check-Referenzen\n\n- Issues: #2\n"
    rc, data = _run(tmp_path, repo, plan, runner={2: "CLOSED"}.get, capsys=capsys)
    f = data["plans"][0]["findings"]
    assert rc == 0 and [(x["cls"], x["sev"]) for x in f] == [("ISSUE_CLOSED", "INFO")]


def test_no_issues_never_calls_runner(tmp_path, repo, capsys):
    def boom(n):
        raise AssertionError("runner called")

    rc, data = _run(tmp_path, repo, "see `#12`\n", ["--no-issues"], runner=boom, capsys=capsys)
    assert rc == 0


def test_issue_runner_cached(tmp_path, repo, capsys):
    calls = []

    def runner(n):
        calls.append(n)
        return "OPEN"

    _run(tmp_path, repo, "`#5` and `#5` again\n", runner=runner, capsys=capsys)
    assert calls == [5]


def test_invalid_ref_exit_2(tmp_path, repo, capsys):
    plan = tmp_path / "p.md"
    plan.write_text("x\n", encoding="utf-8")
    rc = cpr.main(["--plans", str(plan), "--repo", str(repo), "--ref", "nope/nope", "--no-issues"])
    assert rc == 2
    assert "nope/nope" in capsys.readouterr().err


def test_no_plans_exit_2(tmp_path, repo, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    rc = cpr.main(["--plans", str(empty), "--repo", str(repo), "--ref", "HEAD", "--no-issues"])
    assert rc == 2


def test_plans_directory(tmp_path, repo, capsys):
    d = tmp_path / "plans"
    d.mkdir()
    (d / "a.md").write_text("`docs/a.md`\n", encoding="utf-8")
    (d / "b.md").write_text("- Modify: `docs/zzz.md`\n", encoding="utf-8")
    rc = cpr.main(["--plans", str(d), "--repo", str(repo), "--ref", "HEAD", "--no-issues", "--json"])
    data = json.loads(capsys.readouterr().out)
    assert rc == 1 and len(data["plans"]) == 2


def test_working_tree_independent(tmp_path, repo, capsys):
    (repo / "docs" / "a.md").unlink()
    (repo / "docs" / "untracked.md").write_text("x\n", encoding="utf-8")
    rc, data = _run(tmp_path, repo, "- Modify: `docs/a.md` `docs/untracked.md`\n", ["--no-issues"], capsys=capsys)
    assert [(x["cls"], x["ref"]) for x in data["plans"][0]["findings"]] == [("FILE_MISSING", "docs/untracked.md")]


def test_branch_ref(tmp_path, repo, capsys):
    _git(repo, "branch", "feature")
    (repo / "docs" / "b.md").write_text("b\n", encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "more")
    plan = tmp_path / "p.md"
    plan.write_text("- Modify: `docs/b.md`\n", encoding="utf-8")
    rc = cpr.main(["--plans", str(plan), "--repo", str(repo), "--ref", "feature", "--no-issues"])
    assert rc == 1


# --- parser fixtures from real plan excerpts -------------------------------

REAL_FRISCHE_BULLETS = """\
## Frische-Check-Referenzen

- file: scripts/lib/context.py
- scripts/lib/sync_pipeline.py: _sync_stage_auto_commit_allowlist, SYNC_BACKUP_MAX_PER_SOURCE
- scripts/hermes_export.py::export_skill_pack
- `scripts/lib/auto_commit.py` (`_KEYS`, `is_role_eligible`)
- Issues und PRs: #547, #857, #1086i
- `https://models.dev/catalog.json` (Live-Payload)
- `docs/specs/x.md` (existiert nicht)
"""


def test_parser_real_frische_formats():
    refs = cpr.extract_refs(REAL_FRISCHE_BULLETS)
    paths = {r["ref"] for r in refs if r["kind"] == "path"}
    assert paths == {
        "scripts/lib/context.py", "scripts/lib/sync_pipeline.py",
        "scripts/hermes_export.py", "scripts/lib/auto_commit.py",
    }
    syms = {r["ref"] for r in refs if r["kind"] == "symbol"}
    assert syms == {
        "_sync_stage_auto_commit_allowlist", "SYNC_BACKUP_MAX_PER_SOURCE",
        "export_skill_pack", "_KEYS", "is_role_eligible",
    }
    issues = {r["ref"] for r in refs if r["kind"] == "issue"}
    assert issues == {"#547", "#857"}


REAL_INLINE = """\
Roadmap-Verdikt `Phase-A` mit `developer` und `Class.method` in `code`.
- Modify: `scripts/lib/provider_transform.py` - `_map_claude_tools_to_gemini_tools()` entfernen (#1170)
**Files:** Modify scripts/sync.py:217, `docs/x.md`; Create `tests/test_new.py`
```
echo `#99` scripts/ghost.py
```
Siehe `scripts/admin-server.py:5065-5100` und `a/b` sowie `und/oder`.
"""


def test_parser_inline_tokens():
    refs = cpr.extract_refs(REAL_INLINE)
    by = {(r["kind"], r["ref"]) for r in refs}
    assert ("path", "scripts/lib/provider_transform.py") in by
    assert ("symbol", "_map_claude_tools_to_gemini_tools") in by
    assert ("issue", "#1170") in by
    assert ("path", "scripts/sync.py") in by
    assert ("path", "scripts/admin-server.py") in by
    assert ("path", "tests/test_new.py") in by
    assert not any(r["ref"] in ("Phase-A", "developer", "code", "scripts/ghost.py", "#99") for r in refs)
    assert not any(r["ref"] in ("a/b", "und/oder") for r in refs)
    anchors = {r["ref"]: r["lines"] for r in refs if r["kind"] == "path" and r.get("lines")}
    assert anchors["scripts/sync.py"] == (217, 217)
    assert anchors["scripts/admin-server.py"] == (5065, 5100)
    create = {r["ref"] for r in refs if r["kind"] == "path" and r.get("create")}
    assert create == {"tests/test_new.py"}
