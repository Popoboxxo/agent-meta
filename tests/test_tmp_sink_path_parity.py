"""Parity of the tmp-sink path rules across all implementations (AC-97).

The shared corpus ``tests/fixtures/tmp-sink-path-corpus.json`` is evaluated by
``tmp_sink_path_error`` (Python), the shared config reader
``hooks/1-generic/lib/hook_containment_config.py`` (run as subprocess) and
``progress_path_error``. All three must take the same accept/reject
decision and agree on the canonical form (hook: rejected => fallback ``.tmp``).

Run: python -m pytest tests/test_tmp_sink_path_parity.py -q
"""

from __future__ import annotations

import importlib.util
import json
import ntpath
import posixpath
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import repo_containment as rc  # noqa: E402
from lib.consistency.hook_drift import check_stale_deployed_hooks  # noqa: E402
from lib.progress_paths import progress_path_error  # noqa: E402

HOOK_IMPL = REPO_ROOT / "hooks" / "1-generic" / "repo-containment-impl.sh"
CONFIG_READER = REPO_ROOT / "hooks" / "1-generic" / "lib" / "hook_containment_config.py"
CORPUS = json.loads(
    (REPO_ROOT / "tests" / "fixtures" / "tmp-sink-path-corpus.json").read_text(encoding="utf-8")
)["cases"]
IDS = [repr(c["path"]) for c in CORPUS]
FALLBACK = ".tmp"


def _hook_decision(tmp_path: Path, path: str) -> tuple:
    """Run the shared config reader; return (rejected, effective sink path)."""
    config = tmp_path / "project.yaml"
    config.write_text(
        "repo_containment:\n  tmp-sink:\n    path: %s\n" % json.dumps(path), encoding="utf-8"
    )
    result = subprocess.run(
        [sys.executable, str(CONFIG_READER), str(config), ""],
        capture_output=True, text=True, check=True,
    )
    values = dict(line.split("=", 1) for line in result.stdout.splitlines())
    return values["SINK_REJECTED"] == "1", values["SINK_PATH"]


@pytest.mark.parametrize("case", CORPUS, ids=IDS)
def test_python_progress_and_hook_agree(case, tmp_path):
    path = case["path"]
    py_error = rc.tmp_sink_path_error(path)
    pg_error = progress_path_error(path)
    rejected, effective = _hook_decision(tmp_path, path)

    assert bool(py_error) == case["reject"]
    assert bool(pg_error) == case["reject"]
    assert rejected == case["reject"]
    if case["reject"]:
        assert effective == FALLBACK
    else:
        assert effective == case["canonical"] == rc.canonical_tmp_sink_path(path)


@pytest.mark.parametrize("pathmod", [posixpath, ntpath], ids=["posix", "nt"])
@pytest.mark.parametrize("case", CORPUS, ids=IDS)
def test_progress_path_error_pathmod(case, pathmod):
    assert bool(progress_path_error(case["path"], pathmod=pathmod)) == case["reject"]


def test_progress_path_error_resolves_links(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    try:
        (root / "lnk").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    assert progress_path_error("lnk/x", root)
    assert progress_path_error("ok/x", root) is None


def _hook_protected_prefixes() -> set:
    spec = importlib.util.spec_from_file_location(
        "hook_containment_config", CONFIG_READER
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {tuple(seg.lower() for seg in entry) for entry in module._PROTECTED}


def _expected_protected_prefixes() -> set:
    """Fallback list plus provider_root_dirs, derived independently of the hook."""
    import yaml

    entries = {".git", ".claude", ".meta-config"}
    data = yaml.safe_load((REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    providers = data.get("providers", data)
    for cfg in providers.values():
        entries.update(e for e in (cfg.get("provider_root_dirs") or ()) if isinstance(e, str))
    return {
        tuple(seg.lower() for seg in e.replace("\\", "/").split("/") if seg not in ("", "."))
        for e in entries
    }


def test_hook_protected_list_equals_python_and_registry():
    hook = _hook_protected_prefixes()
    python = {tuple(p) for p in rc._protected_prefixes()}
    expected = _expected_protected_prefixes()
    for name, actual in (("python", python), ("hook", hook)):
        assert actual == expected, (
            f"{name} protected list differs from fallback + provider_root_dirs: "
            f"missing in {name}={sorted(expected - actual)}, "
            f"extra in {name}={sorted(actual - expected)}"
        )


def test_hook_protects_every_python_protected_prefix(tmp_path):
    for prefix in rc._protected_prefixes():
        rejected, _ = _hook_decision(tmp_path, "/".join(prefix) + "/out")
        assert rejected, f"hook accepts protected prefix {prefix!r}"


def test_hook_version_bumped_and_old_version_is_drift(tmp_path):
    # The impl's self-documented rule requires a version bump whenever its
    # logic changes: 1.1.0 -> 1.2.0 (Task 8, fail-closed anchor rule),
    # 1.2.0 -> 1.3.0 (review finding M2, tool_name/payload fail-closed),
    # 1.3.0 -> 1.4.0 (#944: heredoc scanning, detector fail-closed, fixed jail
    # root, in-place/destination flags, PyYAML warning),
    # 1.4.0 -> 1.4.1 (review finding F5: an unresolvable fixed jail root
    # fails closed instead of degrading to the payload anchor),
    # 1.4.1 -> 1.5.0 (shared command-word resolver: wrapper `--`, case arms,
    # function bodies, grouping and if/for bodies no longer hide a write),
    # 1.5.0 -> 1.6.0 (#1151: NotebookEdit/MultiEdit/PowerShell, home and
    # download/unpack targets, cd tracking, substitution bodies).
    # 1.6.0 -> 1.6.1 (#1161 Pkt5: all payload fields read in ONE
    # hook_json_get_many parse; fail-closed probes unchanged).
    # 1.6.1 -> 1.10.0 (#1238b1/#1275b: the inline config reader moved into the
    # shared hooks/1-generic/lib/hook_containment_config.py module, which also
    # emits the structured protected-path list).
    source = HOOK_IMPL.read_text(encoding="utf-8")
    version_lines = [ln for ln in source.splitlines() if ln.startswith("# version: ")]
    assert version_lines == ["# version: 1.10.0"]
    meta = tmp_path / "meta"
    (meta / "hooks" / "1-generic").mkdir(parents=True)
    name = HOOK_IMPL.name
    (meta / "hooks" / "1-generic" / name).write_text(source, encoding="utf-8")
    project = tmp_path / "project"
    hooks = project / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    old = source.replace("# version: 1.10.0", "# version: 1.0.0", 1)
    (hooks / name).write_text(old, encoding="utf-8")
    (hooks / ".agent-meta-managed").write_text(name + "\n", encoding="utf-8")
    findings = check_stale_deployed_hooks(
        project, meta, {"platforms": []}, {"claude": {"hooks_dir": ".claude/hooks"}}
    )
    assert [f.check for f in findings] == ["hooks.stale-deployed-version"]
