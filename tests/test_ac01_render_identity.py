"""AC-01 harness: render output of every provider-matrix project is byte-identical.

For each provider registered in config/ai-providers.yaml a scratch project
(same single-provider config as tests/test_provider_matrix_sync.py) is synced,
and every generated file is hashed (SHA-256). The result is compared against
the committed manifest ``tests/fixtures/ac01-baseline/hashes.json``, which was
produced on the pre-feature ``main`` state.

Differences are only tolerated for paths matching ``AC01_EXCEPTIONS`` (the
AC-01 exception list (i)-(v) of SPEC-CONTEXT-PROFILES-2026-10-11, kept as data).

Regenerate the manifest (only for a justified rebaseline):
    python tests/test_ac01_render_identity.py --write

Run: python -m pytest tests/test_ac01_render_identity.py -q
"""

import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path
from typing import Dict, List

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC = _REPO_ROOT / "scripts" / "sync.py"
_MANIFEST = Path(__file__).resolve().parent / "fixtures" / "ac01-baseline" / "hashes.json"
_PROVIDERS = sorted(
    yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
)

# AC-01 exception list (i)-(v) as data: regexes over "<provider>/<relpath>".
# (i)/(ii) new meta-doctor / meta-optimizer role artifacts and their roster rows,
# (iv) IC-15 Nr. 26 root .gitignore entry of the tmp-sink (None path).
# (iii) golden rebaselines and (v) hard errors produce no render diff.
# Empty entries would hide drift, so every pattern must stay role/entry specific.
AC01_EXCEPTIONS = frozenset({
    r".*/meta-doctor\.[a-z]+$",
    r".*/meta-optimizer\.[a-z]+$",
    r".*/standalone/agents/meta-doctor\.md$",
})

# Volatile, non-render artifacts: never part of the manifest.
_SKIP_RE = re.compile(r"(^|/)(\.git)(/|$)|(^|/)sync\.log$|\.sync-backup-")


def _run_sync(project: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(project / ".meta-config" / "project.yaml"), *extra],
        cwd=project, capture_output=True, text=True, timeout=300,
    )


def _make_project(root: Path, provider: str) -> Path:
    project = root / provider
    (project / ".meta-config").mkdir(parents=True)
    (project / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        f"ai-providers:\n- {provider}\n"
        "dod-preset: rapid-prototyping\n"
        "variables:\n  PROJECT_NAME: matrix\n  PROJECT_PREFIX: mx\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = _run_sync(project, "--init")
    assert result.returncode == 0, f"{provider}: sync failed\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}"
    return project


def _hash_file(path: Path, root: Path) -> str:
    data = path.read_bytes()
    # Normalize run-specific values: scratch root path and today's date stamp.
    for needle, repl in ((str(root).encode(), b"<ROOT>"), (date.today().isoformat().encode(), b"<DATE>")):
        data = data.replace(needle, repl)
    return hashlib.sha256(data).hexdigest()


def render_matrix_hashes(fixture_root: Path) -> Dict[str, str]:
    """Sync every provider into ``fixture_root/<provider>`` and hash all files.

    Returns ``{"<provider>/<relpath>": sha256}``.
    """
    fixture_root = Path(fixture_root)
    hashes: Dict[str, str] = {}
    for provider in _PROVIDERS:
        project = _make_project(fixture_root, provider)
        for f in sorted(project.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(fixture_root).as_posix()
            if _SKIP_RE.search(rel):
                continue
            hashes[rel] = _hash_file(f, fixture_root)
    return hashes


def diff_against_manifest(current: Dict[str, str], baseline: Dict[str, str]) -> List[str]:
    """Return drift entries not covered by ``AC01_EXCEPTIONS``."""
    patterns = [re.compile(p) for p in AC01_EXCEPTIONS]
    drift = []
    for path in sorted(set(current) | set(baseline)):
        if current.get(path) == baseline.get(path):
            continue
        if any(p.match(path) for p in patterns):
            continue
        kind = "added" if path not in baseline else "removed" if path not in current else "changed"
        drift.append(f"{kind}: {path}")
    return drift


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    root = tmp_path_factory.mktemp("ac01")
    return root, render_matrix_hashes(root)


def test_ac01_render_identical_to_manifest(rendered):
    _root, current = rendered
    baseline = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    drift = diff_against_manifest(current, baseline)
    assert not drift, "AC-01 drift vs. main baseline:\n" + "\n".join(drift[:30])


def test_ac01_detects_drift(rendered):
    root, current = rendered
    baseline = json.loads(_MANIFEST.read_text(encoding="utf-8"))
    victim = next(p for p in sorted(current) if p.endswith(".md") and not any(
        re.match(e, p) for e in AC01_EXCEPTIONS))
    target = root / victim
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"\n<!-- drift -->\n")
        mutated = dict(current)
        mutated[victim] = _hash_file(target, root)
        assert diff_against_manifest(mutated, baseline) == [f"changed: {victim}"]
    finally:
        target.write_bytes(original)


def test_ac01_exception_list_allows_meta_doctor_artifacts():
    baseline = {"codex/.codex/agents/developer.toml": "a"}
    current = dict(baseline, **{"codex/.codex/agents/meta-doctor.toml": "b"})
    assert diff_against_manifest(current, baseline) == []


if __name__ == "__main__":
    if "--write" not in sys.argv:
        sys.exit("usage: python tests/test_ac01_render_identity.py --write")
    with tempfile.TemporaryDirectory() as td:
        manifest = render_matrix_hashes(Path(td))
    _MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    _MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest)} hashes to {_MANIFEST}")
