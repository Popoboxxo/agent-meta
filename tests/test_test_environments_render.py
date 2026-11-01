"""Render baseline harness for the test-environments feature (SPEC-TEST-ENVIRONMENTS-2026-10-31).

Freezes the **unconfigured** render of the six base role templates across the
five platform variants, so every later template edit (Tasks 8/9) can be proven
byte-neutral while ``test-environments`` is absent (AC-ENV-1, C3).

Provenance of ``tests/fixtures/test-env-baseline/hashes.json``: the fixture is
never hand-written. It is produced from the *unchanged* templates through the
real sync path::

    python3 tests/test_test_environments_render.py --capture-baseline

which runs ``python3 scripts/sync.py --config <project>/.meta-config/project.yaml
--init`` (same invocation as ``tests/test_ac01_render_identity.py::_run_sync``)
for every entry of :data:`PLATFORM_MATRIX` and hashes the rendered
``.claude/agents/*.md`` of the six roles.

Run: ``python3 -m pytest tests/test_test_environments_render.py --basetemp="{{PYTEST_BASETEMP}}"``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional, Sequence

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
SYNC = REPO_ROOT / "scripts" / "sync.py"
BASELINE = Path(__file__).parent / "fixtures" / "test-env-baseline" / "hashes.json"

#: The six roles that receive the gated test-environment block (Tasks 8/9).
ROLES = (
    "developer",
    "tester",
    "e2e-tester",
    "docker",
    "devops-engineer",
    "test-executor",
)

#: Five variants: the unconfigured base plus one project per platform override.
PLATFORM_MATRIX = (
    ("base", ()),
    ("homeassistant", ("homeassistant",)),
    ("sharkord", ("sharkord",)),
    ("hacs", ("hacs",)),
    ("agent-meta", ("agent-meta",)),
)

#: Every platform override must actually reach the render (Task 1, Step 4).
OVERRIDE_COVERAGE = {
    "homeassistant": {"developer"},
    "sharkord": {"developer", "docker"},
    "hacs": {"developer", "tester", "devops-engineer"},
    "agent-meta": {"developer"},
}

#: Task 8: the minor version bump each base template receives with the gate.
BASE_VERSIONS = {
    "tester": "2.9.0",
    "e2e-tester": "1.7.0",
    "developer": "4.9.0",
    "docker": "1.10.0",
    "devops-engineer": "1.8.0",
    "test-executor": "1.3.0",
}

#: Static role line inside the gate, directly below {{TEST_ENVIRONMENT_BLOCK}}.
ROLE_LINES = {
    "tester": "Run tests locally before touching any remote environment.",
    "e2e-tester": "Run tests locally before touching any remote environment.",
    "developer": (
        "Develop and test locally first; touch a remote environment only as "
        "the rules above allow."
    ),
    "docker": (
        "Deploy to a remote environment only if its access is deploy and the "
        "approval protocol above is satisfied."
    ),
    "devops-engineer": (
        "Deploy to a remote environment only if its access is deploy and the "
        "approval protocol above is satisfied."
    ),
    "test-executor": (
        "Read-only: run existing suites against environments only as the rules "
        "above allow; never deploy."
    ),
}

#: Spec §9.1 example: one remote (both) target with a secret token plus one local.
CONFIG_YAML = """
environments:
  HA_DEV_TOKEN:
    description: "Long-lived access token of the HA dev server"
    secret: true
test-environments:
  ha-dev:
    kind: both
    url: "http://ha-dev.lan:8123"
    token-env: HA_DEV_TOKEN
    access: deploy
    remote-access: ask
    notes: "Integration erst nach lokalem Test auf den Dev-Server deployen."
  sharkord-local:
    kind: local
    notes: "Docker-Compose-Stack: docker compose run --rm test"
"""

#: Drift-only frontmatter/provenance lines: they carry the template version, not
#: rendered body content, so a minor template bump must not move the baseline
#: (Task 8 keeps ``test_unset_render_matches_baseline`` green).
_VOLATILE_LINE_RE = re.compile(
    r"^(?:version|based-on|model):.*\n?", re.MULTILINE
)
#: ``generated-from:`` keeps its source path (render identity) but not the
#: template version suffix — the same drift rule as ``based-on:``.
_GENERATED_FROM_VERSION_RE = re.compile(
    r"^(generated-from:[^\n@]*)@[^\n]*$", re.MULTILINE
)


def _project_yaml(platforms: Sequence[str], extra_yaml: str) -> str:
    """Build the throw-away ``project.yaml`` for one matrix variant."""
    lines = [
        'agent-meta-version: "2.0.0-beta.5"',
        "ai-providers: [Claude]",
        "dod-preset: rapid-prototyping",
    ]
    if platforms:
        lines.append("platforms:")
        lines.extend("- %s" % p for p in platforms)
    lines.append("roles:")
    lines.extend("- %s" % r for r in ROLES)
    lines.append("project: {name: te, prefix: te, short: te}")
    lines.append("variables: {PROJECT_NAME: te, AGENT_META_REPO: example/agent-meta}")
    text = "\n".join(lines) + "\n"
    if extra_yaml:
        text += extra_yaml if extra_yaml.endswith("\n") else extra_yaml + "\n"
    return text


def _sync_project(
    root: Path,
    platforms: Sequence[str] = (),
    extra_yaml: str = "",
    extra_env: Optional[Dict[str, str]] = None,
) -> Path:
    """Create a minimal project, run the real sync (``--init``) and return it."""
    project = Path(root)
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    config_path = project / ".meta-config" / "project.yaml"
    config_path.write_text(
        _project_yaml(platforms, extra_yaml), encoding="utf-8"
    )
    subprocess.run(
        ["git", "init", "-q"], cwd=str(project), check=True, capture_output=True
    )
    env = dict(os.environ)
    if extra_env:
        env.update(extra_env)
    result = subprocess.run(
        [
            sys.executable,
            str(SYNC),
            "--config",
            str(config_path),
            "--init",
        ],
        cwd=str(project),
        capture_output=True,
        text=True,
        timeout=300,
        env=env,
    )
    assert result.returncode == 0, (
        "sync failed for %s (platforms=%r)\nstdout:\n%s\nstderr:\n%s"
        % (project, tuple(platforms), result.stdout[-3000:], result.stderr[-3000:])
    )
    return project


def _role_of(stem: str) -> Optional[str]:
    """Map an agent stem to one of the six roles (longest suffix wins)."""
    for role in sorted(ROLES, key=len, reverse=True):
        if stem == role or stem.endswith("-" + role):
            return role
    return None


def _role_texts(project: Path) -> Dict[str, str]:
    """Return ``{stem: text}`` for every rendered agent of the six roles."""
    texts: Dict[str, str] = {}
    agents_dir = Path(project) / ".claude" / "agents"
    if not agents_dir.is_dir():
        return texts
    for path in sorted(agents_dir.glob("*.md")):
        if _role_of(path.stem) is not None:
            texts[path.stem] = path.read_text(encoding="utf-8")
    return texts


def _normalized_hash(text: str) -> str:
    """Hash the body contract: LF, no version/provenance lines, sha256."""
    normalized = text.replace("\r\n", "\n")
    normalized = _VOLATILE_LINE_RE.sub("", normalized)
    normalized = _GENERATED_FROM_VERSION_RE.sub(r"\1", normalized)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _root_normalized(text: str, *roots: Path) -> str:
    """Replace scratch paths with ``<ROOT>`` so runs on any host compare equal."""
    variants = set()
    for root in roots:
        raw = str(root)
        variants.add(raw)
        variants.add(Path(raw).as_posix())
        variants.add(raw.replace("\\", "\\\\"))
    for needle in sorted(variants, key=len, reverse=True):
        if needle:
            text = text.replace(needle, "<ROOT>")
    return text


def _matrix_hashes(root: Path) -> Dict[str, str]:
    """Sync every entry of :data:`PLATFORM_MATRIX` and hash its six role agents."""
    root = Path(root)
    hashes: Dict[str, str] = {}
    for label, platforms in PLATFORM_MATRIX:
        project = _sync_project(root / label, platforms)
        for stem, text in _role_texts(project).items():
            hashes["%s/%s" % (label, stem)] = _normalized_hash(
                _root_normalized(text, project, root)
            )
    return hashes


def _scratch_root() -> Path:
    """A fresh scratch directory below the resolved ``{{PYTEST_BASETEMP}}``."""
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib import tmp_paths  # noqa: PLC0415 - CLI-only import

    config = yaml.safe_load(
        (REPO_ROOT / ".meta-config" / "project.yaml").read_text(encoding="utf-8")
    )
    paths = tmp_paths.resolve_tmp_paths(REPO_ROOT, config)
    base = Path(tmp_paths.resolve_pytest_basetemp(REPO_ROOT, paths))
    base.mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix="te-baseline-", dir=str(base)))


def capture_baseline() -> Path:
    """Capture the unset-render baseline from the current (unchanged) templates."""
    hashes = _matrix_hashes(_scratch_root())
    BASELINE.parent.mkdir(parents=True, exist_ok=True)
    BASELINE.write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return BASELINE


def test_unset_render_matches_baseline(tmp_path_factory):
    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    assert _matrix_hashes(tmp_path_factory.mktemp("teb")) == baseline


def test_matrix_exercises_every_override(tmp_path_factory):
    current = _matrix_hashes(tmp_path_factory.mktemp("teo"))
    for label, roles in OVERRIDE_COVERAGE.items():
        for role in roles:
            stems = [
                k.split("/", 1)[1]
                for k in current
                if k.startswith(label + "/") and _role_of(k.split("/", 1)[1]) == role
            ]
            assert stems, (label, role)
            assert any(
                current["%s/%s" % (label, s)] != current.get("base/%s" % s)
                for s in stems
            ), (label, role)


# ---------------------------------------------------------------------------
# Task 8: gate block in the six base templates + configured render
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("role", sorted(BASE_VERSIONS))
def test_template_has_gated_block_directly_after_constraints(role):
    src = (REPO_ROOT / "agents" / "1-generic" / f"{role}.md").read_text(encoding="utf-8")
    gate = (
        "{{#if TEST_ENVIRONMENTS_SET}}\n{{TEST_ENVIRONMENT_BLOCK}}\n"
        + ROLE_LINES[role]
        + "\n{{/if}}\n"
    )
    assert f'version: "{BASE_VERSIONS[role]}"' in src and src.count(gate) == 1
    end = src.index("</constraints>") + len("</constraints>")
    assert src[end:src.index(gate)].strip() == ""
    if "{{OUTPUT_GUARD_BLOCK}}" in src:
        assert src.index(gate) < src.index("{{OUTPUT_GUARD_BLOCK}}")


@pytest.fixture(scope="module")
def configured(tmp_path_factory):
    return _role_texts(_sync_project(tmp_path_factory.mktemp("cfg"), extra_yaml=CONFIG_YAML))


def test_configured_render_has_block_table_and_role_line(configured):  # AC-ENV-7
    assert {_role_of(s) for s in configured} == set(BASE_VERSIONS)
    for stem, text in configured.items():
        assert "## Test environments" in text
        assert "| ha-dev | both | http://ha-dev.lan:8123 | deploy | ask |" in text
        assert ROLE_LINES[_role_of(stem)] in text
        assert text.index("</constraints>") < text.index("## Test environments")


def test_approval_protocol_in_all_six_roles(configured):  # AC-ENV-8, AC-ENV-20
    for text in configured.values():
        assert "APPROVAL_REQUEST: env=<name>; action=<read|deploy: action>" in text
        assert "APPROVED: env=<name>; action=<action>" in text
        assert "convention boundary" in text
        block = text.split("## Test environments", 1)[1].split("\n## ", 1)[0]
        assert "{{" not in block


def test_settings_json_identical_and_no_secrets_file(tmp_path_factory):  # AC-ENV-11, AC-ENV-1
    unset = _sync_project(tmp_path_factory.mktemp("u"))
    cfg = _sync_project(tmp_path_factory.mktemp("c"), extra_yaml=CONFIG_YAML)
    assert (unset / ".claude/settings.json").read_bytes() == (
        cfg / ".claude/settings.json"
    ).read_bytes()
    assert not (unset / ".meta-config/secrets.local.yaml").exists()
    assert not (cfg / ".meta-config/secrets.local.yaml").exists()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--capture-baseline",
        action="store_true",
        help="re-render the unset matrix and overwrite the baseline fixture",
    )
    args = parser.parse_args(argv)
    if not args.capture_baseline:
        parser.error("nothing to do: pass --capture-baseline")
    path = capture_baseline()
    count = len(json.loads(path.read_text(encoding="utf-8")))
    print("wrote %s (%d hashes)" % (path, count))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
