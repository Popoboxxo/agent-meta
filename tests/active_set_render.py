"""Shared helper for IC-18 prose-gating tests (Tasks 1.13-1.20).

Syncs a versioned active-set fixture (``tests/fixtures/active-set/<name>``) or an
ad-hoc config into a scratch project and returns its root. Every sync runs the
real ``scripts/sync.py --init`` so the tests observe the rendered artifacts, not
an internal intermediate.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Optional

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = REPO_ROOT / "tests" / "fixtures" / "active-set"
FIXTURE_NAMES = ("p10", "p20", "pall", "ha")


def all_roles() -> list:
    """All ``role-defaults`` roles, sorted (allowlist that opens every roles gate)."""
    data = yaml.safe_load((REPO_ROOT / "config" / "role-defaults.yaml").read_text(encoding="utf-8"))
    return sorted(data["roles"])


def fixture_config(name: str) -> dict:
    path = FIXTURES / name / ".meta-config" / "project.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def sync_config(project: Path, config: dict, providers: Optional[list] = None) -> Path:
    """Write ``config`` (optionally overriding ``ai-providers``) and run the sync."""
    config = dict(config)
    if providers is not None:
        config["ai-providers"] = list(providers)
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    (project / ".meta-config" / "project.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    res = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py"), "--config",
         str(project / ".meta-config" / "project.yaml"), "--init"],
        cwd=project, capture_output=True, text=True, timeout=600)
    assert res.returncode == 0, res.stdout[-1500:] + res.stderr[-1500:]
    return project


def default_config() -> dict:
    """The AC-01 provider-matrix default project (no ``roles:`` key)."""
    return {
        "agent-meta-version": "2.0.0-beta.1",
        "ai-providers": ["Claude"],
        "dod-preset": "rapid-prototyping",
        "variables": {"PROJECT_NAME": "matrix", "PROJECT_PREFIX": "mx"},
    }


def tiers_on_config() -> dict:
    """Default project with every role in the allowlist (developer tiers active)."""
    config = default_config()
    config["roles"] = all_roles()
    return config


def section(text: str, start: str, end: str) -> str:
    """Lines from the heading ``start`` (inclusive) up to ``end`` (exclusive)."""
    lines = text.splitlines(keepends=True)
    out, inside = [], False
    for line in lines:
        if line.startswith(start):
            inside = True
        elif inside and line.startswith(end):
            break
        if inside:
            out.append(line)
    return "".join(out)
