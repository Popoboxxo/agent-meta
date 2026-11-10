"""Per-position Opencode generation (issue #1190, Task 19; AC-33/AC-34/AC-35/AC-36).

SPEC-orchestrator-mode-topology-2026-11-09, §3.8.3 (POS-1/POS-2/POS-3), §12.3,
AC-33…AC-36, D-OQ2.

The three Opencode positions are FIRST-CLASS: each one is generated and tested
on its own, for ``surface-version: v1`` **and** ``v2``. AC-33 forbids folding
two positions into one case, so this module carries exactly one test per
position plus one determinism test and the meta-grep that enforces the split
(§3.8.3 "je ein Test pro Position").

Position map (compressed from §3.8.2 — the full table lives in
``docs/concepts/active/orchestrator-topology.md``):

===========  ========================  ==========================================
Position     Config                    Contract pinned here
===========  ========================  ==========================================
POS-1        ``mode: main-chat``       no role emitted, no ``default_agent``,
                                       no gate triples; a *managed* value is
                                       rolled back, a *user* value survives with
                                       exactly one dangling warning (AC-34)
POS-2        ``topology: subagent``    ``mode: subagent`` (never ``primary``), no
                                       ``default_agent``/triples, honest
                                       gate-inactive reporting per surface (AC-35)
POS-3        ``topology: primary``     ``mode: primary``, ``default_agent``,
                                       write-scope lock AND the surface deny (AC-33)
===========  ========================  ==========================================

Every test runs the real ``scripts/sync.py`` in a throw-away project, never a
unit stub: the positions are a property of the generated artifacts.

Scope discipline: the project-level gate document (``opencode.json``) is what
the tests assert on. The ``permissions[]``/``permission`` block inside a
generated *agent* file is the role-level write-scope lock
(``tests/test_opencode_primary_edit_lock.py``) and is deliberately expected
even under POS-2 — the lock follows the ROLE, not the position.

Run: python3 -m pytest tests/test_opencode_positions.py -q
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

#: The AC-01 harness owns the "sync one scratch project through the real CLI"
#: and "normalise a rule render" helpers; reusing them keeps one generation
#: discipline instead of a second renderer.
import test_ac01_render_identity as render_harness  # noqa: E402

from lib.config import build_variables, load_config  # noqa: E402
from lib.consistency.topology import check_orchestrator_topology  # noqa: E402
from lib.providers import (  # noqa: E402
    load_provider_capabilities,
    load_providers_config,
)
from lib.roles import load_roles_config  # noqa: E402
from lib.topology import resolve_topology  # noqa: E402
from lib.variables import (  # noqa: E402
    _effective_topology_flags,
    _topology_flags,
    strip_inactive_conditional_blocks,
    substitute,
)
from tests.timeouts import SYNC_TIMEOUT  # noqa: E402

_SYNC = _REPO_ROOT / "scripts" / "sync.py"
_SURFACES = ("v1", "v2")
_PROVIDER = "Opencode"

_AGENT_FILE = Path(".opencode") / "agents" / "orchestrator.md"
_SETTINGS_FILE = Path("opencode.json")
_STATE_FILE = Path(".opencode") / "agent-meta-state.json"

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "topology-golden"
_GOLDEN_DECLARED = "a2a-delegation-gates.declared-subagent.md"
_GOLDEN_DERIVED = "a2a-delegation-gates.derived-subagent.md"
_GOLDEN_ROLE_ACTIVE = "a2a-delegation-gates.role-active.md"

_DANGLING = "opencode.default-agent.dangling"
_V1_GATE_LOG = "orchestrator-topology.gate-inactive: runtime gate"
_V2_GATE_LOG = "opencode-v2 gate (permissions deny) NOT written for provider"
_V2_GATE_CAUSE = "effective orchestrator topology is 'subagent'"
_GATE_FINDING = "orchestrator-topology.gate-inactive"


# ---------------------------------------------------------------------------
# Scratch projects — the real CLI, one project per (position, surface, seed)
# ---------------------------------------------------------------------------


def _project_config(*, mode: str, topology: str | None, surface: str) -> dict:
    """Minimal single-provider project config for one position.

    ``roles`` keeps the project to two agents so the scratch sync stays cheap;
    an unset ``topology`` is the AC-6 derivation case, never a synonym for
    ``subagent``.
    """
    config: dict = {
        "agent-meta-version": "2.0.0-beta.1",
        "ai-providers": [_PROVIDER],
        "dod-preset": "rapid-prototyping",
        "roles": ["orchestrator", "developer"],
        "orchestrator": {"mode": mode},
        "variables": {
            "PROJECT_NAME": "positions",
            "PROJECT_PREFIX": "pos",
            # Issue #1037: a derived remote would make the render depend on the
            # cloning remote, so the scratch projects pin a neutral slug.
            "AGENT_META_REPO": "example/agent-meta",
        },
    }
    if topology is not None:
        config["orchestrator"]["topology"] = topology
    if surface == "v2":
        config["provider-options"] = {_PROVIDER: {"surface-version": "v2"}}
    return config


def _scratch(
    root: Path,
    *,
    mode: str,
    topology: str | None = None,
    surface: str = "v1",
    seed_settings: dict | None = None,
    seed_state: dict | None = None,
) -> tuple[Path, dict]:
    """Create a throw-away project and return ``(root, parsed project config)``.

    ``seed_settings``/``seed_state`` pre-populate the committed document and the
    shared ``.opencode/agent-meta-state.json`` BEFORE the first sync — that is
    how POS-1's managed-legacy and user-owned cases are expressed without
    relying on a second sync's semantics.
    """
    project = Path(root)
    (project / ".meta-config").mkdir(parents=True)
    config = _project_config(mode=mode, topology=topology, surface=surface)
    (project / ".meta-config" / "project.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )
    if seed_settings is not None:
        (project / _SETTINGS_FILE).write_text(
            json.dumps(seed_settings, indent=2) + "\n", encoding="utf-8"
        )
    if seed_state is not None:
        state_path = project / _STATE_FILE
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(
            json.dumps(seed_state, indent=2) + "\n", encoding="utf-8"
        )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    return project, config


def _sync(project: Path) -> subprocess.CompletedProcess:
    """Run the real sync CLI once against a scratch project."""
    result = subprocess.run(
        [
            sys.executable,
            str(_SYNC),
            "--config",
            str(project / ".meta-config" / "project.yaml"),
            "--init",
        ],
        cwd=project,
        capture_output=True,
        text=True,
        timeout=SYNC_TIMEOUT,
    )
    assert result.returncode == 0, (
        f"sync failed for {project}\n{result.stdout[-1500:]}\n{result.stderr[-2500:]}"
    )
    return result


def _json(path: Path) -> dict:
    assert path.is_file(), f"{path} was not generated"
    return json.loads(path.read_text(encoding="utf-8"))


def _state(project: Path) -> dict:
    path = project / _STATE_FILE
    return _json(path) if path.exists() else {}


def _frontmatter(path: Path) -> dict:
    assert path.is_file(), f"{path} was not generated"
    text = path.read_text(encoding="utf-8")
    block = text.split("---", 2)[1]
    parsed = yaml.safe_load(block)
    assert isinstance(parsed, dict), parsed
    return parsed


def _count(text: str, needle: str) -> int:
    """Occurrences of *needle* in the sync output, one per output line."""
    return sum(1 for line in text.splitlines() if needle in line)


def _findings(project: Path, config: dict) -> list:
    """The consistency channel (read-only) for the scratch project.

    Uses the same inputs the sync uses (resolved registry, capability cells and
    a roles-only active set), so the findings are comparable to the log channel
    without re-running the whole active-set resolution.
    """
    known = frozenset(load_roles_config(_REPO_ROOT).get("roles", {}))
    active_set = SimpleNamespace(
        roles=frozenset(config.get("roles") or ()),
        known_roles=known,
    )
    return check_orchestrator_topology(
        project,
        config,
        provider_config=load_providers_config(_REPO_ROOT, config),
        capabilities=load_provider_capabilities(_REPO_ROOT),
        providers=[_PROVIDER],
        active_set=active_set,
    )


def _assert_no_surface_gate(document: dict) -> None:
    """No project-level deny on either surface form, and no entry point."""
    assert "default_agent" not in document, document
    # v2 form: the ``permissions[]`` triples.
    assert not document.get("permissions"), document
    # v1 form: the ``permission`` map (empty containers count as "no gate").
    assert not document.get("permission"), document


# ---------------------------------------------------------------------------
# POS-1 — ``orchestrator.mode: main-chat`` (AC-34)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("surface", _SURFACES)
def test_opencode_main_chat_position_generates_clean(tmp_path, surface):
    """POS-1: the main chat IS the orchestrator, so the sync emits no role.

    Three states, one per sub-case: a fresh project (nothing is written), a
    managed legacy value (rolled back via the shared state namespace) and a
    user-owned value (kept, warned exactly once). All three are asserted
    against the real sync run, for v1 and v2 alike (AC-33/AC-34).
    """
    # -- fresh: no role file, no entry point, no gate ----------------------
    fresh, _ = _scratch(tmp_path / "fresh", mode="main-chat", surface=surface)
    _sync(fresh)

    assert not (fresh / _AGENT_FILE).exists(), (
        "main-chat must not emit the orchestrator role"
    )
    _assert_no_surface_gate(_json(fresh / _SETTINGS_FILE))

    # -- managed legacy value: taken back by the state rollback ------------
    managed, _ = _scratch(
        tmp_path / "managed",
        mode="main-chat",
        surface=surface,
        seed_settings={"default_agent": "orchestrator"},
        seed_state={"default-agent": {"value": "orchestrator", "prior": None}},
    )
    _sync(managed)

    managed_document = _json(managed / _SETTINGS_FILE)
    assert "default_agent" not in managed_document, (
        "a still-managed default_agent must be rolled back by the sync"
    )
    assert not managed_document.get("permissions"), managed_document
    assert "default-agent" not in _state(managed), (
        "the emptied default-agent namespace must not survive the rollback"
    )
    assert not (managed / _AGENT_FILE).exists()

    # -- user-owned value: kept, warned exactly once -----------------------
    user_owned, _ = _scratch(
        tmp_path / "user-owned",
        mode="main-chat",
        surface=surface,
        seed_settings={"default_agent": "orchestrator"},
    )
    result = _sync(user_owned)

    assert _json(user_owned / _SETTINGS_FILE)["default_agent"] == "orchestrator", (
        "a user-owned value always wins (D16) — never auto-deleted"
    )
    assert "default-agent" not in _state(user_owned), (
        "an untracked user value must not become managed"
    )
    assert _count(result.stderr, _DANGLING) == 1, (
        f"exactly one {_DANGLING} warning expected (one per channel), got: "
        f"{[line for line in result.stderr.splitlines() if _DANGLING in line]}"
    )


# ---------------------------------------------------------------------------
# POS-2 — ``orchestrator.topology: subagent`` (AC-35)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("surface", _SURFACES)
def test_opencode_subagent_position_generates_clean(tmp_path, surface):
    """POS-2: the role is emitted as a subagent and the gate says so honestly.

    The position is legal and recommended (§12.2/§12.3, D-OQ2) — it must neither
    claim the session entry (``mode: primary``/``default_agent``) nor pretend
    the runtime gate is active. The suspension is reported per channel: v1 emits
    one log warning AND one finding (§6.4 counting rule), v2 only the
    cause-aware log warning because its tier is ``plugin``.
    """
    project, config = _scratch(
        tmp_path / "project", mode="strict", topology="subagent", surface=surface
    )
    result = _sync(project)

    agent_path = project / _AGENT_FILE
    frontmatter = _frontmatter(agent_path)
    assert frontmatter["mode"] == "subagent"
    assert "mode: primary" not in agent_path.read_text(encoding="utf-8")

    _assert_no_surface_gate(_json(project / _SETTINGS_FILE))

    findings = _findings(project, config)
    gate_findings = [f for f in findings if f.check == _GATE_FINDING]

    if surface == "v1":
        assert _count(result.stderr, _V1_GATE_LOG) == 1, result.stderr[-2000:]
        assert len(gate_findings) == 1, [f.check for f in findings]
        # One finding per channel — no other check may fire for this state.
        assert len(findings) == 1, [f.check for f in findings]
    else:
        assert _count(result.stderr, _V2_GATE_LOG) == 1, result.stderr[-2000:]
        assert _count(result.stderr, _V2_GATE_CAUSE) == 1, result.stderr[-2000:]
        assert gate_findings == [], (
            "v2 resolves to tier plugin: the tier-permission-bound finding must "
            "not fire (the log channel carries the message)"
        )
        assert findings == [], [f.check for f in findings]


# ---------------------------------------------------------------------------
# POS-3 — ``orchestrator.topology: primary`` (AC-33, regression)
# ---------------------------------------------------------------------------


def test_opencode_primary_position_generates_clean(tmp_path):
    """POS-3: the ONLY position with an entry point and a full deny.

    One test, two surface sub-cases (AC-33). Both must carry ``mode: primary``,
    ``default_agent``, the role-level write-scope lock AND the surface's deny
    form (v1 ``permission`` map, v2 ``permissions[]`` triples).
    """
    for surface in _SURFACES:
        project, _ = _scratch(
            tmp_path / surface,
            mode="strict",
            topology="primary",
            surface=surface,
        )
        _sync(project)

        agent_path = project / _AGENT_FILE
        frontmatter = _frontmatter(agent_path)
        assert frontmatter["mode"] == "primary", surface
        assert "mode: subagent" not in agent_path.read_text(encoding="utf-8"), surface

        document = _json(project / _SETTINGS_FILE)
        assert document["default_agent"] == "orchestrator", surface

        if surface == "v1":
            # The gate deny and the role lock are both a ``permission`` map.
            assert document["permission"]["edit"]["**"] == "deny", document
            assert document["permission"]["bash"]["**"] == "deny", document
            assert "permissions" not in document, document
            edit = frontmatter["permission"]["edit"]
            assert edit["*"] == "deny", edit
            assert edit[".tmp/**"] == "allow", edit
        else:
            triples = {
                (entry["action"], entry["resource"], entry["effect"])
                for entry in document["permissions"]
            }
            assert triples == {("edit", "**", "deny"), ("shell", "**", "deny")}, (
                document["permissions"]
            )
            assert "permission" not in document, (
                "a v2 document must not carry the v1 permission map"
            )
            agent_triples = {
                (entry["action"], entry["resource"], entry["effect"])
                for entry in frontmatter["permissions"]
            }
            assert ("edit", "*", "deny") in agent_triples, agent_triples
            assert ("edit", ".tmp/**", "allow") in agent_triples, agent_triples
            assert ("edit", "*", "allow") not in agent_triples, agent_triples


# ---------------------------------------------------------------------------
# Declared == deterministic (AC-36)
# ---------------------------------------------------------------------------


def _render_gate_rule(*, topology: str | None, root: Path) -> str:
    """Render the real ``a2a-delegation-gates`` rule for one topology state.

    Goes through the AC-01 harness helpers (``_topology_project_config``,
    ``_normalize_topology_golden``): Claude provider, orchestrator role active,
    normalised bytes — the same discipline as the frozen goldens, only with the
    ``orchestrator.topology`` key declared.
    """
    name = "declared" if topology else "derived"
    project = Path(root) / name
    (project / ".meta-config").mkdir(parents=True)
    config_text = render_harness._topology_project_config(True)
    if topology is not None:
        config_text += f"orchestrator:\n  mode: strict\n  topology: {topology}\n"
    (project / ".meta-config" / "project.yaml").write_text(
        config_text, encoding="utf-8"
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = render_harness._run_sync(project, "--init")
    assert result.returncode == 0, (
        f"rule render failed (topology={topology})\n"
        f"{result.stdout[-1500:]}\n{result.stderr[-1500:]}"
    )
    rendered = (project / render_harness._TOPOLOGY_RULE_REL).read_text(encoding="utf-8")
    return render_harness._normalize_topology_golden(rendered, project)


def _gate_branch(text: str) -> tuple[str, str, str]:
    """Split a rendered gate rule into ``(before, branch, after)``.

    The topology conditional sits between gate 1 and gate 3, so the two outer
    slices must be byte-identical across states while the branch is exactly what
    the resolution changes (AC-36 "die Textdifferenz liegt nur im expliziten
    Zweig").
    """
    head, after = text.split("\n3. **Execution-Trace-Isolation:**", 1)
    before, branch = head.split("2. **", 1)
    return before, branch, after


def test_explicit_subagent_topology_changes_output_deterministically(tmp_path):
    """AC-36: a declared position is stable and differs only in its own branch.

    Four facts, one test (they are facets of the same contract):

    1. the rendered flags differ between declared and derived ``subagent``
       exactly as the IC-4 flag contract says;
    2. two renders of the same declared position are byte-identical, also when
       the provider ORDER is swapped (no oscillation, §AC-36);
    3. the frozen goldens (declared/derived) reproduce from the real sync;
    4. the text difference between the two states lies ONLY in the explicit
       template branch.
    """
    capabilities = load_provider_capabilities(_REPO_ROOT)
    known = frozenset(load_roles_config(_REPO_ROOT).get("roles", {}))
    active_set = SimpleNamespace(
        roles=frozenset({"orchestrator", "developer"}),
        known_roles=known,
    )

    declared_config = {"orchestrator": {"mode": "strict", "topology": "subagent"}}
    derived_config = {"orchestrator": {"mode": "strict"}}
    claude = "Claude"

    def _flags(config: dict) -> dict:
        resolution = resolve_topology(
            config,
            claude,
            provider_config=load_providers_config(_REPO_ROOT, config),
            capabilities=capabilities[claude],
            mode="strict",
            active_set=active_set,
        )
        declared, source = (
            resolution.declared or "",
            resolution.source,
        )
        return {
            **_topology_flags(
                declared,
                explicit=declared != "",
                source=source,
            ),
            **_effective_topology_flags(resolution, mode="strict"),
        }

    declared_flags = _flags(declared_config)
    derived_flags = _flags(derived_config)

    assert declared_flags["ORCH_TOPOLOGY"] == "subagent"
    assert declared_flags["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "project"
    assert declared_flags["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "true"
    assert declared_flags["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"

    assert derived_flags["ORCH_TOPOLOGY"] == ""
    assert derived_flags["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert derived_flags["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "derived"
    assert derived_flags["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "false"

    # -- provider order must not matter (byte identity) --------------------
    def _emit(name: str, providers: list[str]) -> tuple[bytes, bytes]:
        project = Path(tmp_path) / name
        (project / ".meta-config").mkdir(parents=True)
        config = _project_config(mode="strict", topology="subagent", surface="v1")
        config["ai-providers"] = providers
        (project / ".meta-config" / "project.yaml").write_text(
            yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
        )
        subprocess.run(["git", "init", "-q"], cwd=project, check=True)
        _sync(project)
        return (
            (project / _AGENT_FILE).read_bytes(),
            (project / _SETTINGS_FILE).read_bytes(),
        )

    first = _emit("order-a", ["Opencode", "Claude"])
    second = _emit("order-b", ["Claude", "Opencode"])
    assert first == second, (
        "the declared subagent render must be byte-identical for swapped "
        "provider order"
    )

    # -- the two frozen goldens, generated through the real sync ----------
    declared_render = _render_gate_rule(topology="subagent", root=tmp_path / "golden")
    derived_render = _render_gate_rule(topology=None, root=tmp_path / "golden")

    assert declared_render == (_FIXTURE_DIR / _GOLDEN_DECLARED).read_text(
        encoding="utf-8"
    )
    assert derived_render == (_FIXTURE_DIR / _GOLDEN_DERIVED).read_text(
        encoding="utf-8"
    )
    # The derived golden is the same bytes as the unset-key role-active fixture:
    # declaring nothing must not move the rendered rule (AC-6).
    assert derived_render == (_FIXTURE_DIR / _GOLDEN_ROLE_ACTIVE).read_text(
        encoding="utf-8"
    )

    declared_before, declared_branch, declared_after = _gate_branch(declared_render)
    derived_before, derived_branch, derived_after = _gate_branch(derived_render)

    assert declared_before == derived_before
    assert declared_after == derived_after
    assert declared_branch != derived_branch
    assert "Orchestrator-Topologie (subagent)" in declared_branch
    assert "Orchestrator-Singleton" in derived_branch
    assert "{{" not in declared_render and "{{" not in derived_render


# ---------------------------------------------------------------------------
# AC-33 meta-guard — one test per position, never a combined case
# ---------------------------------------------------------------------------


def test_no_position_is_tested_in_a_combined_case():
    """AC-33: the per-position split is a source-level contract.

    Guards against the tempting shortcut of one parametrized "all positions"
    test: no test name may carry two position IDs, and the three
    ``*_position_generates_clean`` tests (POS-1/POS-2 parametrized over both
    surfaces) must exist.
    """
    source = Path(__file__).read_text(encoding="utf-8")
    names = re.findall(r"^def (test_\w+)", source, re.M)

    # No test may name two positions in one case — "main-chat"/"main_chat" is
    # one position, so the two spellings collapse before counting.
    position_words = ("main-chat", "main_chat", "subagent", "primary")
    for name in names:
        mentioned = {
            "main-chat" if word.startswith("main") else word
            for word in position_words
            if word in name
        }
        assert len(mentioned) <= 1, (
            f"{name} names two positions ({sorted(mentioned)}) — AC-33 forbids "
            "a combined-position case"
        )
        assert len(set(re.findall(r"POS-[123]", name))) <= 1, name

    assert {
        "test_opencode_main_chat_position_generates_clean",
        "test_opencode_subagent_position_generates_clean",
        "test_opencode_primary_position_generates_clean",
    } <= set(names)

    # POS-1 and POS-2 must be checked on both surfaces (AC-33); the grep keeps
    # a removed parameter from silently shrinking the matrix.
    decorators = re.findall(
        r'^@pytest\.mark\.parametrize\("surface", _SURFACES\)$', source, re.M
    )
    assert len(decorators) == 2, decorators
    assert _SURFACES == ("v1", "v2")


# ---------------------------------------------------------------------------
# This repository declares POS-2 (T20; AC-36/AC-31, D-OQ1)
# ---------------------------------------------------------------------------
#
# The repo is no longer in the derived ``subagent`` fallback: it says so in
# ``.meta-config/project.yaml``, the render picks the explicit branch, and no
# derived-position warning may fire. The tests read the real repo config, never
# a scratch project — that is the point of the task.

_REPO_CONFIG = _REPO_ROOT / ".meta-config" / "project.yaml"
_ORCHESTRATOR_TEMPLATE = _REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"
_AGENTS_MD = _REPO_ROOT / "AGENTS.md"

#: The explicit-branch singleton paragraph of the orchestrator template.
_EXPLICIT_SINGLETON = "**Singleton (subagent):**"
_EXPLICIT_SPAWN_CLAIM = "Only `main_chat` spawns the orchestrator"
_DERIVED_SPAWN_CLAIM = "Only `main_chat` may create you"

#: Tracked generated artifacts whose bytes must not move on a repeat sync.
_TRACKED_GENERATED = (
    "AGENTS.md",
    "CLAUDE.md",
    "opencode.json",
    ".meta-config/generated-file-hashes.json",
)


def _render_orchestrator_from_repo() -> tuple[str, dict]:
    """Render ``orchestrator.md`` with this repo's own variables."""
    config = load_config(_REPO_CONFIG)
    variables, unmapped = build_variables(config, _REPO_ROOT, _REPO_ROOT)
    assert unmapped == [], unmapped
    source = _ORCHESTRATOR_TEMPLATE.read_text(encoding="utf-8")
    rendered = strip_inactive_conditional_blocks(
        substitute(source, variables, _ORCHESTRATOR_TEMPLATE.name, None),
        variables,
    )
    return rendered, variables


def test_repo_declares_subagent_explicitly():
    """The declaration is one line in the orchestrator block — nothing else.

    AC-36: the position comes from ``orchestrator.topology`` alone. No
    ``provider-overrides`` entry may be needed (or present) for it, and the key
    must not be declared twice.
    """
    data = yaml.safe_load(_REPO_CONFIG.read_text(encoding="utf-8"))

    assert data["orchestrator"]["topology"] == "subagent"
    assert "topology" not in data.get("provider-overrides", {})

    orchestrator_block = _REPO_CONFIG.read_text(encoding="utf-8").split(
        "\norchestrator:\n", 1
    )[1].split("\nviz:\n", 1)[0]
    assert orchestrator_block.count("\n  topology:") == 1, orchestrator_block


def test_repo_render_is_the_explicit_branch():
    """The real config selects ``ORCH_TOPOLOGY_EXPLICIT``, not the ``else``.

    Renders the template through the production order (substitute → strip) with
    the variables the sync builds from this repo's ``project.yaml``. The
    committed ``AGENTS.md`` is the second witness: it is a tracked artifact and
    must carry the *subagent* gate wording, never the ``primary`` entry wording.
    """
    rendered, variables = _render_orchestrator_from_repo()

    assert variables["ORCH_TOPOLOGY"] == "subagent"
    assert variables["ORCH_TOPOLOGY_EXPLICIT"] == "true"
    assert variables["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "project"
    assert variables["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "false"

    assert _EXPLICIT_SINGLETON in rendered
    assert _EXPLICIT_SPAWN_CLAIM in rendered
    assert _DERIVED_SPAWN_CLAIM not in rendered

    agents_md = _AGENTS_MD.read_text(encoding="utf-8")
    # The tracked context file renders the subagent gate branch …
    assert "MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`." in agents_md
    # … and never the primary entry-point claim.
    assert "ist in diesem Projekt der Session-Einstieg" not in agents_md


def test_repo_has_no_derived_position_warnings():
    """``--validate`` stays silent on the derived-position checks (AC-36)."""
    result = subprocess.run(
        [sys.executable, str(_SYNC), "--validate"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=SYNC_TIMEOUT,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 0, output[-2500:]
    assert "orchestrator-topology.main-chat-derived-primary" not in output, output[-2500:]
    assert "orchestrator-topology.strict-primary-entry-mismatch" not in output, (
        output[-2500:]
    )


def _tracked_hashes() -> dict[str, str]:
    return {
        name: hashlib.sha256((_REPO_ROOT / name).read_bytes()).hexdigest()
        for name in _TRACKED_GENERATED
        if (_REPO_ROOT / name).is_file()
    }


def _tracked_diff() -> str:
    result = subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=no"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def test_declaration_is_deterministic():
    """Two consecutive sync runs leave every tracked artifact byte-identical.

    ``--check`` is the second half of AC-31: after a real sync the drift check
    must be clean, otherwise the declaration is not a fixed point.
    """
    before_hashes = _tracked_hashes()
    before_diff = _tracked_diff()

    sync = subprocess.run(
        [sys.executable, str(_SYNC)],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=SYNC_TIMEOUT,
    )
    assert sync.returncode == 0, (sync.stdout + sync.stderr)[-2500:]

    assert _tracked_hashes() == before_hashes, (
        "a repeat sync rewrote a tracked generated artifact:\n"
        + _tracked_diff()
    )
    assert _tracked_diff() == before_diff, _tracked_diff()

    check = subprocess.run(
        [sys.executable, str(_SYNC), "--check"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=SYNC_TIMEOUT,
    )
    assert check.returncode == 0, (check.stdout + check.stderr)[-2500:]
