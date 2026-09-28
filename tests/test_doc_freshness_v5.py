"""AC-11 (IC-05, spec §5.1.1) — V5 ``check_role_generation_parity``, gate-aware.

V5 belongs to the family *dokumentierter Rollenbestand vs. erzeugte Rollen*
(Spec §4.1): it asks whether the roles the project config **declares** are the
roles the generator actually **produces**. That is the same question as V1 (a
hand-written number against a computed one) and V6 (a rendered block against a
computed fact), which is why Spec §4.1 assigns V5 to the freshness family — and
**E-7 / Rev. 0.7** gave it a module of its own,
``scripts/lib/consistency/docs_freshness_v5.py``, because
``docs_freshness.py`` reached its 592-line budget and the alternative would have
been either a shared helper (hidden coupling to V6's ``check`` id and severity
map) or a re-interpretation of a Sollwert. Neither is done.

**The comparison set is ``compute_active_roles()``, never ``len(config["roles"])``**
(IC-04). This is the whole reason V5 is not a one-liner: ``se-component-requirements``
is listed in ``roles:`` and is **never** generated, because
``systems-engineering.enabled: false`` closes the ``se`` activation group
(``config/role-defaults.yaml::activation_groups``). An implementation that
assumed the whitelist is the generated inventory would either report a permanent
false alarm (the F21 class this check exists to end) or — worse — silently
suppress the finding by comparing the list against itself. ``test_v5_comparison_
set_is_the_computed_active_set`` pins the difference set against
``compute_active_roles`` directly and against the **generator's own** resolver in
``test_v5_comparison_set_parity_with_the_generator``, which is the consumer
obligation ``doc_facts`` records for this task (module docstring, :174-185): a
clone of ``compute_active_roles`` cannot contradict it, so the oracle is
``roles.resolve_active_roles(..., require_template=True)``.

**Both severity branches are asserted in one function body.** ``test_v5_severity_
depends_on_se_gate`` is the acceptance test (AC-11) and it is deliberately
non-vacuum: the WARNING half reads the real tree, the ERROR half opens the gate
on a copy of that same tree and adds a ``roles:`` entry that has no template. A
test that only ever observed ``WARNING`` would pass against a check that can
never report an ERROR at all.

**Silence is a decision, not a fallback.** ``compute_active_roles`` raises
``FactUnavailable`` when a source it needs is missing or unreadable and never
returns a partially-intersected set. V5 can degrade — it is a comparison, and
without one side there is nothing to compare — so it degrades to ``[]``, the
same reading V6 applies in ``docs_freshness.py`` (``_v6_computed_facts``:426):
an absent Sollwert is an **absence, not a drift**. Collapsing that ``None`` into
an empty *set* instead would report all 59 declared roles as ungenerated — the
fabricated-drift failure mode, inverted. ``test_v5_unavailable_facts_are_silence_
not_fabricated_drift`` pins the ``[]`` half and, in the same body, the non-empty
half on the intact tree, because a check that always returns ``[]`` would
otherwise satisfy it.

**V5 is not registered yet** (W2-7 owns the ``docs.py`` ``__all__`` increment,
W3 the runner call). That is asserted **by measurement in the task ledger, not by
a test**: a permanent ``not in __all__`` assertion would be a tripwire a later
task must delete, which is the state-assertion defect the W2-5 review recorded.
Nothing here imports the facade, so this file never becomes a dependency of the
task that owns it (K20/K46).
"""

from __future__ import annotations

import copy
import inspect
import shutil
from pathlib import Path

import pytest
import yaml

from scripts.lib import doc_facts
from scripts.lib import roles as roles_lib
from scripts.lib.consistency import docs_freshness_v5 as v5_lib
from scripts.lib.doc_facts import AGENTS_CAPABILITY, compute_active_roles
from scripts.lib.io import SyncError

REPO_ROOT = Path(__file__).resolve().parent.parent

PROJECT_CONFIG_RELPATH = ".meta-config/project.yaml"

GATED_SE_ROLE = "se-component-requirements"
"""The F13 role: declared in ``roles:``, closed by the ``se`` gate, never generated."""

GATE_OPEN_ROLE = "se-role-without-template"
"""A role that has no template anywhere — generated with the gate open *or* closed.

Premise for the ERROR half: opening the ``se`` gate cannot admit a role the
template universe does not contain, so the parity gap survives the gate change
and only the severity is under test.
"""

COPY_PATHS: tuple[str, ...] = (
    "VERSION",
    ".meta-config",
    "agents/1-generic",
    "agents/2-platform",
    "config",
    "commands/1-generic",
)

CORRUPT_ROLE_DEFAULTS = "roles: [unclosed\n  bad: : :\n\t- tab-indented\n"
"""Structurally invalid YAML for the role registry.

Tab indentation plus an unclosed flow sequence, so the failure is a *parse*
error (``io.py``:78 raises ``SyncError``) rather than a missing file. The
sibling test deletes the file instead; the two branches must degrade alike.
"""


def _yaml(relpath: str) -> dict:
    return yaml.safe_load((REPO_ROOT / relpath).read_text(encoding="utf-8")) or {}


def _copy_tree(root: Path) -> Path:
    """Copy every source V5 reads into ``root``; return ``root``.

    A copy of the *real* tree, not a synthetic fixture: the check's whole subject
    is the gate/template interplay of the shipped ``role-defaults.yaml``, and a
    hand-built fixture would prove nothing about it (the precedent is
    ``tests/test_doc_facts.py::_copy_fact_tree``).
    """
    for rel in COPY_PATHS:
        source = REPO_ROOT / rel
        target = root / rel
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    return root


@pytest.fixture(scope="module")
def repo_config() -> dict:
    return _yaml(PROJECT_CONFIG_RELPATH)


def _roles(findings: list) -> list[str]:
    """The declared role each finding names, in report order."""
    return [finding.message.split("'")[1] for finding in findings]


def test_v5_severity_depends_on_se_gate(tmp_path, repo_config):
    """AC-11: the ``se`` gate decides WARNING vs. ERROR — both halves, one body.

    Half **A** (WARNING) is the real tree: ``systems-engineering.enabled`` is
    ``false``, so the one declared-but-ungenerated role is a *deliberate* gating
    decision and must not fail a build. Half **B** (ERROR) is the same tree with
    the gate opened **and** a role added that has no template: with the gate
    closed a gap is expected, with it open the gap is a defect.

    Both halves live in one function body on purpose (K33, the W2-6 lesson): a
    check hard-wired to one severity satisfies either half alone.
    """
    # --- half A: gate closed -> WARNING -------------------------------------
    assert repo_config["systems-engineering"]["enabled"] is False, (
        "premise: this repository is in the F13 state the spec names"
    )
    warnings = v5_lib.check_role_generation_parity(REPO_ROOT, repo_config)
    assert warnings, "half A premise: the F13 state must produce a finding"
    assert all(f.severity is v5_lib.Severity.WARNING for f in warnings)
    assert _roles(warnings) == [GATED_SE_ROLE]
    assert {f.check for f in warnings} == {v5_lib.V5_CHECK_ID}
    assert {f.file for f in warnings} == {PROJECT_CONFIG_RELPATH}
    assert all(f.suggestion for f in warnings)

    # --- half B: gate open + a role without a template -> ERROR -------------
    root = _copy_tree(tmp_path)
    opened = copy.deepcopy(repo_config)
    opened["systems-engineering"]["enabled"] = True
    opened["roles"] = list(opened["roles"]) + [GATE_OPEN_ROLE]
    errors = v5_lib.check_role_generation_parity(root, opened)
    assert errors, "half B premise: the ungeneratable role must be reported"
    assert _roles(errors) == [GATE_OPEN_ROLE], (
        "opening the gate must admit the real SE role too — the premise is that "
        "only the template-less role stays ungenerated"
    )
    assert all(f.severity is v5_lib.Severity.ERROR for f in errors), (
        "systems-engineering.enabled: true makes every declared-but-ungenerated "
        "role an ERROR"
    )
    assert {f.check for f in errors} == {v5_lib.V5_CHECK_ID}


def test_v5_ist_state_is_one_warning_for_the_gated_se_role(repo_config):
    """F13 measured on the real tree: exactly one finding, and it is a WARNING.

    AC-11's "Ist-Zustand" half. ``test_v5_severity_depends_on_se_gate`` reads the
    same tree, so this test exists to pin the *count* and the *identity* of the
    role: a check that reported the whole 59-role whitelist, or none of it, is
    wrong in the direction this check exists to end.
    """
    findings = v5_lib.check_role_generation_parity(REPO_ROOT, repo_config)
    assert len(findings) == 1
    assert _roles(findings) == [GATED_SE_ROLE]
    assert findings[0].severity is v5_lib.Severity.WARNING
    assert findings[0].message == (
        f"role '{GATED_SE_ROLE}' is declared but never generated"
    ), "the message must name the role and the defect, not just carry the role"
    active = doc_facts.compute_active_roles(REPO_ROOT, repo_config)
    assert len(active) == 58, "premise: the computed set is smaller than the list"
    assert len(repo_config["roles"]) == 59
    assert GATED_SE_ROLE not in active


def test_v5_comparison_set_is_the_computed_active_set_not_the_roles_list(repo_config):
    """IC-04: the gap is ``declared − compute_active_roles()``, nothing else.

    The F21 guard, in the form that can actually fail: the finding set equals the
    difference against the **computed** set, and it is *non-empty* only because
    the computed set is not the whitelist. An implementation that used
    ``len(config["roles"])`` as the generated inventory finds a difference of
    zero and reports nothing.
    """
    findings = v5_lib.check_role_generation_parity(REPO_ROOT, repo_config)
    generated = doc_facts.compute_active_roles(REPO_ROOT, repo_config)
    expected = sorted(set(repo_config["roles"]) - generated)
    assert _roles(findings) == expected
    assert expected, "premise broken: the difference set must be non-empty"
    assert set(repo_config["roles"]) - set(repo_config["roles"]) == set(), (
        "the negative control: the whitelist minus itself is empty, so a "
        "whitelist-as-generated implementation reports nothing"
    )

    opened = copy.deepcopy(repo_config)
    opened["systems-engineering"]["enabled"] = True
    assert v5_lib.check_role_generation_parity(REPO_ROOT, opened) == [], (
        "with the gate open the whitelist is fully generated — the finding is "
        "the gate's doing, not a structural mismatch"
    )
    assert GATED_SE_ROLE in doc_facts.compute_active_roles(REPO_ROOT, opened)


def test_v5_comparison_set_parity_with_the_generator(repo_config):
    """The consumer obligation ``doc_facts`` records for W2-4 (IC-04 vs. resolver).

    The expected side is re-derived through the **generator's** entry point,
    ``roles.resolve_active_roles(..., require_template=True)``, which shares no
    code with ``compute_active_roles``. A defect present in only one of the two
    derivations is caught; a restatement of the implementation would not.
    """
    resolved = set(
        roles_lib.resolve_active_roles(
            REPO_ROOT, repo_config, require_template=True, warn_sink=[]
        )
    )
    assert resolved == doc_facts.compute_active_roles(REPO_ROOT, repo_config)
    findings = v5_lib.check_role_generation_parity(REPO_ROOT, repo_config)
    assert _roles(findings) == sorted(set(repo_config["roles"]) - resolved)


def test_v5_unavailable_facts_are_silence_not_fabricated_drift(tmp_path, repo_config):
    """``FactUnavailable`` ⇒ ``[]``; the intact tree ⇒ non-empty. Same body.

    ``config/role-defaults.yaml`` is the load-bearing source: without it the
    intersection cannot run. Two implementations satisfy "returns a list" — one
    that reports ``[]`` and one that reports **all 59 declared roles** as
    ungenerated. Only the pair of asserts below tells them apart, and only
    because the second half runs on an intact copy of the same tree.
    """
    root = _copy_tree(tmp_path / "broken")
    (root / "config" / "role-defaults.yaml").unlink()
    with pytest.raises(doc_facts.FactUnavailable):
        doc_facts.compute_active_roles(root, repo_config)
    assert v5_lib.check_role_generation_parity(root, repo_config) == [], (
        "an unavailable source is an absence, not a drift — reporting it as one "
        "would fabricate a finding per declared role"
    )

    intact_root = _copy_tree(tmp_path / "intact")
    intact = v5_lib.check_role_generation_parity(intact_root, repo_config)
    assert _roles(intact) == [GATED_SE_ROLE], (
        "non-vacuum: the same call on the same sources is not silent"
    )


def test_v5_corrupt_role_registry_degrades_instead_of_escaping(tmp_path, repo_config):
    """A **malformed** ``role-defaults.yaml`` degrades too, not just a missing one.

    The sibling test covers the ``FactUnavailable`` branch: the source is
    *absent*. This one covers the branch next to it, which is the same category
    reported one layer lower: ``io._load_yaml_or_json`` raises ``SyncError`` on
    invalid YAML (``io.py``:78), and ``doc_facts`` documents that it maps only
    ``OSError``/``ValueError`` to ``FactUnavailable`` — "any other exception type
    propagates unchanged" (``_template_role_names``, ``:608-611``).

    Catching only ``FactUnavailable`` made V5 the one check of the family that
    escapes a corrupt registry, and since ``consistency-check.py`` wraps no check
    in ``try``, that escape takes the whole run with it and no JSON report is
    written. The premise is asserted first, on ``compute_active_roles`` directly,
    so the test states *why* the exception is expected rather than swallowing
    anything: the two asserts below are what separate "degrades to silence" from
    "propagates", and the sibling test alone cannot tell the two apart.
    """
    root = _copy_tree(tmp_path)
    (root / "config" / "role-defaults.yaml").write_text(
        CORRUPT_ROLE_DEFAULTS, encoding="utf-8"
    )
    with pytest.raises(SyncError):
        doc_facts.compute_active_roles(root, repo_config), (
            "premise: a malformed registry raises SyncError, not FactUnavailable"
        )
    assert v5_lib.check_role_generation_parity(root, repo_config) == [], (
        "a corrupt registry is an unreadable source — an absence, not a drift, "
        "and not an exception that would abort the runner"
    )

    intact_root = _copy_tree(tmp_path / "intact")
    assert _roles(v5_lib.check_role_generation_parity(intact_root, repo_config)) == [
        GATED_SE_ROLE
    ], "non-vacuum: the same call on a readable registry is not silent"


def test_v5_absent_project_config_is_silence(tmp_path, repo_config):
    """No project config ⇒ no declared inventory ⇒ ``[]``; an empty config likewise.

    The mirror of the unavailable-facts rule on the *Ist* side: a check that
    needed a config but compared against an empty one would report the whole
    repository as drifted.
    """
    root = _copy_tree(tmp_path)
    (root / PROJECT_CONFIG_RELPATH).unlink()
    assert v5_lib.check_role_generation_parity(root) == []
    assert v5_lib.check_role_generation_parity(root, {}) == []
    assert v5_lib.check_role_generation_parity(REPO_ROOT, repo_config), (
        "non-vacuum: the check is not silent on the real tree"
    )


def test_v5_provider_dimension_is_skipped_not_evaluated(tmp_path, repo_config):
    """The findings do not depend on a registry that would collapse the set.

    ``compute_active_roles`` takes an optional provider registry whose only
    meaningful value collapses the set to ``{}`` when the declared providers
    declare no ``agents`` capability — for this check that would turn into a
    finding for every declared role. The generator has no provider-capability
    notion, so the dimension is *skipped*.

    **What this test enforces, stated exactly** (the wording of an earlier
    revision over-claimed): that V5's findings are unchanged when the
    provider dimension is unavailable **or** collapsing, and that the signature
    offers no ``provider_config`` handle. It does **not** prove that
    ``config/ai-providers.yaml`` is never read — deleting the file cannot prove
    that, because ``load_providers_config`` is fail-soft and its built-in
    fallback declares ``agents``. ``test_v5_does_not_read_the_provider_registry``
    is the test that enforces the no-read property; this one stays because it
    pins the collapsing-registry case, which that other test cannot reach
    without a fixture.

    The premise is asserted, not assumed: the collapsing registry really does
    empty ``compute_active_roles`` on this tree. Without that premise the first
    assert would hold for a registry that merely fails to intersect the
    declared provider names, and the test would pass against an implementation
    that *did* evaluate the dimension — a silent mutation this test exists to
    catch. **Do not deduplicate this premise away:** it is the sole pin for that
    mutant, and the sibling test's premise is what makes its fixture valid.
    """
    collapsed = {
        name: {"capabilities": []} for name in repo_config["ai-providers"]
    }
    assert compute_active_roles(REPO_ROOT, repo_config, collapsed) == set(), (
        "premise: a registry without 'agents' collapses the computed set"
    )
    assert compute_active_roles(REPO_ROOT, repo_config), (
        "premise: the skipped dimension leaves the set intact"
    )

    root = _copy_tree(tmp_path)
    (root / "config" / "ai-providers.yaml").unlink()
    assert _roles(v5_lib.check_role_generation_parity(root, repo_config)) == [
        GATED_SE_ROLE
    ]
    parameters = inspect.signature(v5_lib.check_role_generation_parity).parameters
    assert "provider_config" not in parameters


def test_v5_does_not_read_the_provider_registry(tmp_path, repo_config):
    """V5 never reads ``config/ai-providers.yaml`` — the claim, actually enforced.

    Deleting the file does **not** prove this. ``load_providers_config`` is
    fail-soft *and* ships a built-in fallback entry that declares ``agents``
    (measured: the fallback is ``Claude`` with ``agents`` among its
    capabilities), so a load-and-forward check computes the very same set on a
    tree without the file, and on the healthy tree, where every registered
    provider declares ``agents``. Both states are invisible to the sibling test.

    The one state that separates the two implementations is a registry that
    **exists and parses** while declaring no ``agents`` capability — so this
    fixture rewrites the copied file rather than removing it. Under that fixture
    a load-and-forward check computes the empty set and reports a finding for
    every declared role; V5 never looks at the file and still reports the one
    gated SE role.

    The premise is asserted in the same body: without it, a future change to the
    providers schema could make the fixture vacuous and the test would go quiet
    instead of red.
    """
    document = yaml.safe_load(
        (REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
    )
    without_agents = {
        name: {
            **entry,
            "capabilities": [
                capability
                for capability in (entry.get("capabilities") or [])
                if capability != AGENTS_CAPABILITY
            ],
        }
        for name, entry in document["providers"].items()
    }
    assert without_agents["Claude"]["capabilities"], (
        "premise: the fixture strips only 'agents', the rest survives — otherwise "
        "the rewrite would be a different registry than the one under test"
    )
    assert compute_active_roles(REPO_ROOT, repo_config, without_agents) == set(), (
        "premise: a parsed registry without 'agents' collapses the computed set"
    )

    root = _copy_tree(tmp_path)
    payload = dict(document)
    payload["providers"] = without_agents
    (root / "config" / "ai-providers.yaml").write_text(
        yaml.safe_dump(payload, sort_keys=False), encoding="utf-8"
    )

    findings = v5_lib.check_role_generation_parity(root, repo_config)
    assert _roles(findings) == [GATED_SE_ROLE], (
        "V5 must not read the provider registry: a load-and-forward "
        f"implementation reports all {len(repo_config['roles'])} declared roles "
        "under this fixture"
    )
    assert findings[0].severity is v5_lib.Severity.WARNING


def test_v5_signature_and_check_id_are_pinned():
    """IC-05's signature convention for the nine new V-checks, plus the check id.

    ``(root, config=None)`` — the two-argument form, unlike the one-argument
    ``check_readme_docs_index`` (K59). The id ``docs.role_generation_parity`` is
    the ``__all__``/runner contract that W2-7 and W3 will wire.
    """
    parameters = inspect.signature(v5_lib.check_role_generation_parity).parameters
    assert list(parameters) == ["root", "config"]
    assert parameters["config"].default is None
    assert v5_lib.V5_CHECK_ID == "docs.role_generation_parity"
    assert v5_lib.V5_PROJECT_CONFIG_RELPATH == PROJECT_CONFIG_RELPATH
