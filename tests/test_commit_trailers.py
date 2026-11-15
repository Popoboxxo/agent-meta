"""commit.trailers contract (E-19): validator, renderer, schema, config, --validate."""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib.commit_trailers import (  # noqa: E402
    commit_violations,
    commit_warnings,
    render_commit_trailers,
)
from lib.config import _build_core_variables  # noqa: E402

GOOD = "Co-Authored-By: Some Bot <bot@example.com>"
_FIX = Path(__file__).resolve().parent / "fixtures" / "active-set" / "p10"
_SYNC = ROOT / "scripts" / "sync.py"


def _cfg(trailers):
    return {"commit": {"trailers": trailers}}


# --- C2 validator ------------------------------------------------------------

@pytest.mark.parametrize("cfg", [{}, {"commit": None}, _cfg([]), _cfg([GOOD])])
def test_violations_empty_for_valid(cfg):
    assert commit_violations(cfg) == []


@pytest.mark.parametrize("cfg,needle", [
    ({"commit": "x"}, "commit must be a mapping"),
    ({"commit": {"trailers": "x"}}, "commit.trailers must be a list"),
    (_cfg(["kein trailer"]), "commit.trailers[0] must match"),
    (_cfg([GOOD, 5]), "commit.trailers[1] must match"),
    (_cfg(["A: b\n"]), "commit.trailers[0] must match"),
    (_cfg([GOOD, GOOD]), "duplicate"),
    ({"commit": {"foo": 1}}, "commit has unknown key(s): foo"),
])
def test_violations_messages(cfg, needle):
    out = commit_violations(cfg)
    assert any(m.startswith("commit") and needle in m for m in out), out


def test_warnings_co_authored_by_without_email():
    assert commit_warnings(_cfg(["co-authored-by: Bot"])) == [
        "commit.trailers[0] Co-Authored-By should include an email address"]
    assert commit_warnings(_cfg([GOOD, "Signed-off-by: x"])) == []
    assert commit_warnings(_cfg(["Co-Authored-By:"])) == []  # format violation skipped
    assert commit_warnings({"commit": 3}) == []
    assert commit_warnings({}) == []


def test_render():
    assert render_commit_trailers(_cfg([GOOD, "X-Y: z"])) == GOOD + "\nX-Y: z"
    assert render_commit_trailers(_cfg([GOOD, GOOD, "bad", 7])) == GOOD
    for cfg in ({}, {"commit": None}, {"commit": "x"}, {"commit": {"trailers": "x"}}, _cfg([])):
        assert render_commit_trailers(cfg) == ""


# --- C1 schema (structural, no jsonschema) -----------------------------------

def test_schema_commit_property():
    schema = json.loads((ROOT / "config" / "project-config.schema.json").read_text(encoding="utf-8"))
    commit = schema["properties"]["commit"]
    assert commit["type"] == "object" and commit["additionalProperties"] is False
    assert list(commit["properties"]) == ["trailers"]
    trailers = commit["properties"]["trailers"]
    assert trailers["type"] == "array" and trailers["uniqueItems"] is True
    assert trailers["default"] == []
    assert trailers["items"] == {"type": "string", "pattern": "^[A-Za-z][A-Za-z0-9-]*: \\S.*$"}


# --- C3 config variables -----------------------------------------------------

def _core(extra=None, variables=None):
    config = {"project": {"prefix": "tp", "short": "T", "name": "T"}, "roles": ["developer"]}
    config.update(extra or {})
    variables = {} if variables is None else variables
    _build_core_variables(variables, config, ROOT, None)
    return variables


def test_core_variables_with_trailers():
    v = _core(_cfg([GOOD, "X-Y: z"]))
    assert v["COMMIT_TRAILERS"] == GOOD + "\nX-Y: z"
    assert v["_AUTO_COMMIT_RESOLVED"]["commit_trailers"] == [GOOD, "X-Y: z"]


def test_core_variables_without_key():
    v = _core()
    assert v["COMMIT_TRAILERS"] == ""
    assert v["_AUTO_COMMIT_RESOLVED"]["commit_trailers"] == []


def test_core_variables_invalid_commit_block_no_raise():
    v = _core(_cfg(["kein trailer", GOOD]))
    assert v["COMMIT_TRAILERS"] == ""
    assert v["_AUTO_COMMIT_RESOLVED"]["commit_trailers"] == []


def test_core_variables_invalid_auto_commit_branch_empty_list():
    v = _core({"auto_commit": {"mode": "bogus"}, **_cfg([GOOD])})
    assert v["_AUTO_COMMIT_RESOLVED"]["commit_trailers"] == []  # spec C3: invalid branch -> []


def test_explicit_variable_wins():
    v = _core(_cfg([GOOD]), variables={"COMMIT_TRAILERS": "Own: x"})
    assert v["COMMIT_TRAILERS"] == "Own: x"


# --- C4 --validate -----------------------------------------------------------

def _validate(tmp_path, block):
    project = tmp_path / "proj"
    (project / ".meta-config").mkdir(parents=True)
    cfg = project / ".meta-config" / "project.yaml"
    shutil.copy(_FIX / ".meta-config" / "project.yaml", cfg)
    with open(cfg, "a", encoding="utf-8") as fh:
        fh.write(block)
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    run = lambda *f: subprocess.run(  # noqa: E731
        [sys.executable, str(_SYNC), "--config", str(cfg), *f], cwd=project,
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=300)
    assert run("--init").returncode == 0
    res = run("--validate")
    return res.returncode, res.stdout + res.stderr


def test_validate_format_violation_is_error(tmp_path):
    rc, out = _validate(tmp_path, 'commit:\n  trailers: ["kein trailer"]\n')
    assert rc == 1 and "config-audit [ERROR] commit: commit.trailers[0]" in out


def test_validate_missing_email_is_warning_only(tmp_path):
    rc, out = _validate(tmp_path, 'commit:\n  trailers: ["Co-Authored-By: Bot"]\n')
    assert rc == 0 and "config-audit [WARN] commit:" in out


@pytest.mark.parametrize("block", [
    'commit:\n  trailers: ["A: b", "A: b"]\n',
    'commit:\n  foo: 1\n',
])
def test_validate_duplicates_and_unknown_key_fail(tmp_path, block):
    rc, out = _validate(tmp_path, block)
    assert rc == 1 and "config-audit [ERROR] commit:" in out
