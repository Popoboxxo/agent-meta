"""Fan-out report exactness (Task 21 / 2d.2, AC-58).

The sentinel render wraps every *text* value under ``variables:`` and counts the
substitutions per active provider artifact. ``fan_out`` must match an
independent sentinel count on the same fixture. Conditional variables are never
wrapped: they must still APPEAR in the fan-out report with ``occurrences: null``
and ``conditional: true`` (spec lines 1445-1449, plan Task 21 Falle, review
F3/F4), and must never produce a sentinel token.

Run: .venv-1/bin/python -m pytest tests/test_meta_optimizer_fanout.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync.py"
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "meta-optimizer"
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import meta_optimizer as mo  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.context_report import merge_provider_mappings  # noqa: E402
from lib.providers import (  # noqa: E402
    load_provider_capabilities,
    load_providers_config,
    resolve_providers,
)

RUN_TIMEOUT = 900
SENTINEL = "QZPROJECT_NAMEQZ"
VALUE = "fanoutfixturetoken"
CONDITIONAL_SENTINEL = "QZUNKNOWN_FALLBACK_MAIN_CHATQZ"

# The fixture renders exactly one provider (Claude); its registry-declared
# artifact tree is `.claude/` plus the context file. Hard-coded on purpose: the
# independent count must not reuse the module's provider-root resolution.
CLAUDE_ROOTS = (".claude", "CLAUDE.md")
EXCLUDED_FILES = {".meta-config/project.yaml", "sync.log"}


def _independent_sentinel_count(root: Path, token: str) -> tuple:
    """Raw walk + ``bytes.count`` over the whole render (own code path)."""
    total = 0
    files = 0
    attributed = 0
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel.startswith(".git/") or rel in EXCLUDED_FILES:
            continue
        hits = path.read_bytes().decode("utf-8", errors="replace").count(token)
        if not hits:
            continue
        total += hits
        files += 1
        if any(rel == root_rel or rel.startswith(root_rel + "/") for root_rel in CLAUDE_ROOTS):
            attributed += hits
    return total, files, attributed


def _make_project(root: Path) -> Path:
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    cfg = root / ".meta-config" / "project.yaml"
    cfg.write_text((FIXTURES / "claude-minimal.yaml").read_text(encoding="utf-8"),
                   encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    return cfg


def _independent_sentinel_render(root: Path, cfg: Path) -> Path:
    """Render an own sentinel copy (test-owned, no call into the module)."""
    work = root / "independent-sentinel-render"
    (work / ".meta-config").mkdir(parents=True)
    text = cfg.read_text(encoding="utf-8")
    for name, value in (("PROJECT_NAME", VALUE), ("PROJECT_GOAL", "fanoutgoaltoken")):
        wrapped = "QZ{}QZ{}ZQ{}ZQ".format(name, value, name)
        text = text.replace("  {}: {}\n".format(name, value),
                            "  {}: {}\n".format(name, wrapped))
    (work / ".meta-config" / "project.yaml").write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=str(work), check=True)
    result = subprocess.run(
        [sys.executable, str(SYNC), "--config",
         str(work / ".meta-config" / "project.yaml"), "--init"],
        cwd=str(work), capture_output=True, text=True, timeout=RUN_TIMEOUT)
    assert result.returncode == 0, result.stderr[-2000:]
    return work


@pytest.fixture(scope="module")
def fanout_run(tmp_path_factory):
    root = tmp_path_factory.mktemp("mo-fanout")
    cfg = _make_project(root)
    result = subprocess.run(
        [sys.executable, str(SYNC), "--config", str(cfg), "--optimize-config", "--json"],
        cwd=str(root), capture_output=True, text=True, timeout=RUN_TIMEOUT)
    assert result.returncode == 0, result.stderr[-2500:]
    runs = sorted((root / "scratch" / "out" / "meta-optimizer").glob("*/proposal.json"))
    assert runs, sorted((root / "scratch" / "out" / "meta-optimizer").iterdir())
    proposal = json.loads(runs[-1].read_text(encoding="utf-8"))
    return {
        "root": root,
        "cfg": cfg,
        "proposal": proposal,
        "render": _independent_sentinel_render(root, cfg),
    }


def test_fan_out_matches_independent_sentinel_count(fanout_run):
    entries = {e["variable"]: e for e in fanout_run["proposal"]["fan_out"]}
    entry = entries["variables.PROJECT_NAME"]
    total, files, attributed = _independent_sentinel_count(fanout_run["render"], SENTINEL)
    assert total > 0
    assert entry["occurrences"] == total
    assert entry["files"] == files
    assert entry["conditional"] is False
    assert entry["value_bytes"] == len(VALUE.encode("utf-8"))
    assert entry["injected_bytes"] == total * entry["value_bytes"]
    assert entry["per_provider"] == {"Claude": attributed * entry["value_bytes"]}


def test_fan_out_entry_field_set(fanout_run):
    entry = fanout_run["proposal"]["fan_out"][0]
    assert set(entry) == {
        "variable", "value_bytes", "occurrences", "files", "injected_bytes",
        "per_provider", "conditional",
    }


def test_zero_occurrence_variable_has_no_fan_out_entry(fanout_run):
    variables = {e["variable"] for e in fanout_run["proposal"]["fan_out"]}
    assert "variables.UNUSED_SMALL" not in variables
    assert "variables.UNUSED_BIG" not in variables
    kinds = {c["yaml_path"]: c["kind"] for c in fanout_run["proposal"]["candidates"]}
    assert kinds["variables.UNUSED_SMALL"] == "no-effect"
    assert kinds["variables.UNUSED_BIG"] == "dead-variable-content-loss"


def test_conditional_variable_appears_with_null_occurrences(fanout_run):
    """Spec 1445-1449 / review F3+F4: conditional entries are present, not wrapped."""
    entries = {e["variable"]: e for e in fanout_run["proposal"]["fan_out"]}
    entry = entries["variables.UNKNOWN_FALLBACK_MAIN_CHAT"]
    assert entry["conditional"] is True
    assert entry["occurrences"] is None
    assert entry["files"] is None
    assert entry["injected_bytes"] == 0
    assert entry["per_provider"] == {"Claude": 0}
    # not sentinel-wrapped: the module says so, and the value never got a token
    config = yaml.safe_load(fanout_run["cfg"].read_text(encoding="utf-8"))
    active = compute_active_set(config, REPO_ROOT, fanout_run["root"], warn_sink=[])
    wrapped = mo.sentinel_wrapped_names(config, REPO_ROOT, fanout_run["root"], active)
    assert "UNKNOWN_FALLBACK_MAIN_CHAT" not in wrapped
    assert "PROJECT_NAME" in wrapped
    assert CONDITIONAL_SENTINEL not in json.dumps(fanout_run["proposal"])


def test_static_conditional_detection_covers_if_usage():
    """F4(b): the static ``{{#if X}}`` scan complements the whitelist."""
    _referenced, conditionals = mo._framework_references(REPO_ROOT)
    assert "PROJECT_STRUCTURE" in conditionals  # templates/context/partials/project-metadata.md
    assert mo._is_conditional("PROJECT_STRUCTURE", {}, conditionals) is True
    assert mo._is_conditional("PROJECT_NAME", {}, conditionals) is False


def test_fan_out_counts_helper_matches_proposal(fanout_run):
    config = yaml.safe_load(fanout_run["cfg"].read_text(encoding="utf-8"))
    active = compute_active_set(config, REPO_ROOT, fanout_run["root"], warn_sink=[])
    provider_config = load_providers_config(REPO_ROOT, config)
    providers = resolve_providers(config, provider_config)
    mappings = merge_provider_mappings(
        provider_config, load_provider_capabilities(REPO_ROOT))
    scanned = {
        e["variable"]: e for e in mo.fan_out_counts(
            fanout_run["render"], config, REPO_ROOT, fanout_run["root"], active,
            providers=providers, mappings=mappings)
    }
    from_proposal = {e["variable"]: e for e in fanout_run["proposal"]["fan_out"]}
    # only the variables the test wrapped itself can be cross-checked
    for variable in ("variables.PROJECT_NAME", "variables.PROJECT_GOAL"):
        entry = from_proposal[variable]
        assert scanned[variable]["occurrences"] == entry["occurrences"]
        assert scanned[variable]["per_provider"] == entry["per_provider"]
        assert scanned[variable]["conditional"] == entry["conditional"]
    assert from_proposal["variables.UNKNOWN_FALLBACK_MAIN_CHAT"]["conditional"] is True
