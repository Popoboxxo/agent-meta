"""``fill_defaults`` interplay as ``info-only`` hints (Task 23 / 2d.4, AC-82).

Binding: ``docs/plans/2026-10-17-context-profiles-phase2-plan.md`` Task 23 and
``docs/specs/2026-10-11-context-profiles-spec.md`` AC-82 / IC-24
("``fill_defaults``-Wechselwirkung (B-2)", spec line 1419 ff.) plus the Mark
definition ("``refilled-by-defaults``", spec line 504 ff.).

``refill_keys`` is derived from the *same* helpers that ``fill_defaults`` calls
(``config_field_defaults``, the schema top-level defaults, the special blocks
``repo_containment``/``project.short``/``dod.*``). Keys in that set never get a
removal hunk: the production guard turns them into an ``info-only`` candidate
with the Mark ``refilled-by-defaults`` and the mandatory warning text. Applying
every applicable candidate and running a regular sync afterwards must leave
``.meta-config/project.yaml`` byte-identical (AC-82).

Run: .venv-1/bin/python -m pytest tests/test_meta_optimizer_refill.py -q
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SYNC = REPO_ROOT / "scripts" / "sync.py"
SINK_SUBDIR = ("scratch", "out", "meta-optimizer")
RUN_TIMEOUT = 900

sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import meta_optimizer as mo  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.config import config_field_defaults  # noqa: E402

CASCADE_KEYS = {"dod-preset", "conventions-preset"}
REFILL_MARK = "refilled-by-defaults"


# --- helpers ---------------------------------------------------------------

def _run(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SYNC), "--config", ".meta-config/project.yaml", *args],
        cwd=str(root), capture_output=True, text=True, timeout=RUN_TIMEOUT,
    )


def _init_project(root: Path, text: str) -> Path:
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    cfg = root / ".meta-config" / "project.yaml"
    cfg.write_text(text, encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=str(root), check=True)
    return cfg


def _run_dirs(root: Path) -> list:
    base = root.joinpath(*SINK_SUBDIR)
    return sorted(p for p in base.iterdir() if p.is_dir()) if base.is_dir() else []


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


CASE_C_TEXT = (
    'agent-meta-version: "2.0.0-beta.1"\n'
    "ai-providers:\n"
    "- Claude\n"
    "dod-preset: rapid-prototyping\n"
    "repo_containment:\n"
    "  tmp-sink:\n"
    "    enabled: true\n"
    "    path: scratch/out\n"
    "variables:\n"
    "  PROJECT_NAME: refillcasetoken\n"
    "  UNUSED_SMALL: deadsmall\n"
)


def _case_d_text() -> str:
    version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    return (
        "# Case D fixture: AC-82 byte equality after apply + regular sync.\n"
        'agent-meta-version: "' + version + '"\n'
        "ai-providers:\n"
        "- Claude\n"
        "dod-preset: rapid-prototyping\n"
        "project:\n"
        "  name: refillfixture\n"
        "  prefix: rf\n"
        "  short: refillfixture\n"
        "repo_containment:\n"
        "  tmp-sink:\n"
        "    enabled: true\n"
        "    path: scratch/out\n"
        "variables:\n"
        "  PROJECT_NAME: refillfixturetoken\n"
        "  PROJECT_PREFIX: rf\n"
        "  UNUSED_SMALL: deadsmall\n"
    )


# --- Case A: refill_keys composition ---------------------------------------

def test_refill_keys_comes_from_fill_defaults_sources():
    """AC-82/IC-24: same sources as ``fill_defaults``, no copied default tables."""
    keys = mo.refill_keys(REPO_ROOT, {"dod-preset": "rapid-prototyping"})

    expected_fields = set(config_field_defaults(REPO_ROOT)) - CASCADE_KEYS
    assert expected_fields <= keys, expected_fields - keys

    assert "repo_containment" in keys
    assert "debug-mode" in keys               # schema top-level default
    assert "agent-meta-version" in keys       # derived from VERSION

    assert "dod.req-traceability" not in keys
    full_keys = mo.refill_keys(REPO_ROOT, {"dod-preset": "full"})
    assert "dod.req-traceability" in full_keys

    assert "project.short" not in keys
    with_project = mo.refill_keys(
        REPO_ROOT, {"project": {"name": "x", "prefix": "xx"}})
    assert "project.short" in with_project

    # Nested schema defaults are not filled by the first (top-level) loop.
    assert "admin-ui.port" not in keys
    assert "knowledge-engine.domain" not in keys

    assert "dod-preset" not in keys
    assert "conventions-preset" not in keys


# --- Case B: the guard neuters a removal candidate -------------------------

def test_refill_guard_turns_removal_into_info_only():
    """AC-82: no hunk, not applicable, Mark + mandatory warning text."""
    text = (
        'agent-meta-version: "2.0.0-beta.1"\n'
        "repo_containment:\n"
        "  enabled: true\n"
        "variables:\n"
        "  UNUSED_SMALL: deadsmall\n"
    )
    raw = mo._removable_candidate(
        text, "repo_containment", "no-effect", rationale="x",
        runtime_reader=False, credential_lines={})
    assert raw.hunks
    assert raw.applicable is True

    guarded = mo._refill_guard(
        raw, mo.refill_keys(REPO_ROOT, yaml.safe_load(text)))
    assert guarded.kind == "info-only"
    assert guarded.id == "OPT-info-only:repo_containment"
    assert guarded.yaml_path == "repo_containment"
    assert guarded.scope == "repo_containment"
    assert guarded.applicable is False
    assert guarded.deterministic is False
    assert guarded.hunks == ()
    assert guarded.proof_level_required == "none"
    assert guarded.yaml_bytes_saved == 0
    assert guarded.injected_bytes_saved_est == 0
    assert REFILL_MARK in guarded.marks
    assert mo._REFILL_WARNING in guarded.warnings
    assert "Entfernen wäre wirkungslos" in " ".join(guarded.warnings)

    # structural-simplify is a hint by construction: never carries a hunk.
    simplify = mo._hint_candidate("structural-simplify", "hooks")
    assert simplify.hunks == ()
    assert simplify.applicable is False


# --- Case C: production wiring ---------------------------------------------

def test_collect_candidates_uses_the_refill_guard(tmp_path, monkeypatch):
    """The guard is wired into ``collect_candidates``, not only into tests."""
    cfg = _init_project(tmp_path, CASE_C_TEXT)
    text = cfg.read_text(encoding="utf-8")
    config = yaml.safe_load(text)
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])

    monkeypatch.setattr(
        mo, "refill_keys", lambda agent_meta_root, cfg_dict: {"variables.UNUSED_SMALL"})

    proposal = mo.collect_candidates(tmp_path, REPO_ROOT, config, text, active)
    candidate = next(
        c for c in proposal.candidates if c.yaml_path == "variables.UNUSED_SMALL")
    assert candidate.kind == "info-only"
    assert candidate.id == "OPT-info-only:variables.UNUSED_SMALL"
    assert candidate.applicable is False
    assert candidate.deterministic is False
    assert candidate.hunks == ()
    assert candidate.proof_level_required == "none"
    assert REFILL_MARK in candidate.marks


# --- Case D: end-to-end AC-82 byte equality --------------------------------

def test_apply_then_regular_sync_is_byte_identical(tmp_path):
    """AC-82: refilled keys are never removed; apply + sync keeps the bytes."""
    root = tmp_path
    cfg = _init_project(root, _case_d_text())

    # 1) Regular sync materializes every fill_defaults key (baseline).
    first = _run(root)
    assert first.returncode == 0, first.stderr[-2000:]

    # 2) Optimizer proposal.
    optimized = _run(root, "--optimize-config", "--json")
    assert optimized.returncode == 0, optimized.stderr[-2000:]
    proposal_path = _run_dirs(root)[-1] / "proposal.json"
    proposal = _load(proposal_path)
    ids = [c["id"] for c in proposal["candidates"] if c["applicable"]]
    assert ids, proposal["candidates"]

    # Every key that fill_defaults would re-materialize must be a hint.
    config_text = cfg.read_text(encoding="utf-8")
    refill = mo.refill_keys(REPO_ROOT, yaml.safe_load(config_text))
    for candidate in proposal["candidates"]:
        if candidate["yaml_path"] in refill:
            assert candidate["applicable"] is False, candidate
            assert list(candidate["hunks"]) == [], candidate

    # 3) Preview (dry run) and locate its preview.json below the sink.
    preview_run = _run(
        root, "--apply-config-patch", str(proposal_path),
        "--accept", *ids, "--dry-run", "--json")
    assert preview_run.returncode == 0, preview_run.stdout[-1500:] + preview_run.stderr[-2000:]
    previews = sorted(root.joinpath(*SINK_SUBDIR).glob("*/preview.json"))
    assert previews, sorted(p.name for p in _run_dirs(root))
    preview_path = previews[-1]

    # 4) Apply, bound to the shown preview.
    applied = _run(
        root, "--apply-config-patch", str(proposal_path),
        "--accept", *ids, "--preview", str(preview_path), "--json")
    assert applied.returncode == 0, applied.stdout[-1500:] + applied.stderr[-2000:]
    after_apply = cfg.read_bytes()
    assert b"UNUSED_SMALL" not in after_apply
    assert b"repo_containment:" in after_apply

    # 5) AC-82: a regular sync afterwards does not rewrite the file.
    second = _run(root)
    assert second.returncode == 0, second.stderr[-2000:]
    assert cfg.read_bytes() == after_apply
