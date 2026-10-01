"""Role-generation parity — is the declared role inventory the generated one?

Family of the file-check cut of Spec §4.1 (U-1/K18): V5 owns exactly one
question — *"Is the documented role inventory the generated one?"* — and E-7 /
Rev. 0.7 gave it this module, because ``docs_freshness.py`` stands at its
592-line budget. Both alternatives are rejected, not quietly skipped: reusing V6's
``_v6_computed_facts`` / ``_v6_finding`` is hidden coupling (``V6_CHECK_ID`` and
``V6_SEVERITY_BY_KIND`` are wired to V6; V5 needs ERROR **iff** the ``se`` gate is
open), and compressing the V1 prose buys a hard bound with readability. The
``docs.py`` re-export stays W2-7's write-set (K20/K46) and the runner call is
W3's — V5 is not registered yet and contributes 0 findings.

**The comparison set is ``compute_active_roles()`` (IC-04), never
``len(config["roles"])``.** That is why V5 is not a one-liner:
``se-component-requirements`` is listed in ``roles:`` and is *never* generated,
because ``systems-engineering.enabled: false`` closes the ``se`` activation
group. Treating the whitelist as the generated inventory yields either a permanent
false alarm (F21) or — worse — no finding at all, by comparing the list with
itself. The direction is one-way because ``roles:`` bounds the intent from above,
not the generation from below: without the key the generated set is *by design*
larger.

**Unavailable is not drift.** ``compute_active_roles`` raises
``FactUnavailable`` for a missing or unreadable source and never returns a
partially-intersected set. V5 *can* degrade — a comparison needs two sides — so
it degrades to silence, the reading V6 applies in ``docs_freshness.py``
(``_v6_project_config``:410, ``_v6_computed_facts``:426): an absent Sollwert is
an **absence, not a drift**. The sentinel is ``None``, never ``set()``: an empty
computed set against a 59-role declaration would fabricate a finding per role —
the F21 class, inverted. Staying silent is also what keeps V5 *inside* the
report: ``consistency-check.py`` has no per-check guard (``run_checks`` and
``main`` hold no ``try`` at all — measured by AST), so a check that lets an
exception escape takes the whole run with it and no JSON report is written.
Degrading is a contract here, not a convenience: the runner offers no per-check
blast radius to degrade into.

**Severity is the gate, read through the gate table.** The ``se`` group declares
``config_predicate: {kind: config_flag, path: systems-engineering.enabled}``, so
the state is resolved via ``roles.resolve_activation_gates`` instead of reading
that path here: no gate path is hard-coded, and the severity follows the table if
the predicate is re-pointed. Closed ⇒ the exclusion is a decision (WARNING); open
⇒ it is a defect (ERROR); an unknown group resolves closed, the fail-soft way.

The provider dimension of IC-04 is **skipped, not evaluated**: the generator has
no provider-capability notion, and a registry that resolves the set to ``{}``
would turn every declared role into a finding.
"""

from __future__ import annotations

from pathlib import Path

from ..doc_facts import FactUnavailable, compute_active_roles
from ..io import SyncError, load_yaml_file
from ..roles import resolve_activation_gates
from .report import Finding, Severity

V5_CHECK_ID = "docs.role_generation_parity"

V5_PROJECT_CONFIG_RELPATH = ".meta-config/project.yaml"

V5_GATE_GROUP = "se"

V5_SUGGESTION_BY_SEVERITY: dict[Severity, str] = {
    Severity.ERROR: (
        f"The `{V5_GATE_GROUP}` gate is open, so a declared role must be "
        "generated: give it a template under `agents/` or drop it from "
        f"`{V5_PROJECT_CONFIG_RELPATH}`."
    ),
    Severity.WARNING: (
        "A closed gate excludes the role by decision, so this is a note, not a "
        "defect: give it a template, or record why the gate stays closed."
    ),
}


def _v5_project_config(root: Path, config: dict | None) -> dict:
    """The config the declaration and the gate are read from (see :410)."""
    if config:
        return config
    data = load_yaml_file(
        Path(root) / V5_PROJECT_CONFIG_RELPATH, on_error="default", default=None
    )
    return data if isinstance(data, dict) else {}


def _v5_generated_roles(root: Path, config: dict) -> set[str] | None:
    """The generated role set, or ``None`` when no source allows computing it.

    Two exception types are caught, and the second one is deliberate.
    :class:`FactUnavailable` is ``doc_facts``' own "a source is missing or
    unreadable" signal. :class:`SyncError` is ``io._load_yaml_or_json`` raising
    on **malformed** YAML (``io.py``:78) for the very same source
    ``config/role-defaults.yaml`` — a corrupt registry is the *same* category,
    only reported by the layer below: ``doc_facts`` documents that only
    ``OSError``/``ValueError`` are mapped to ``FactUnavailable`` and that "any
    other exception type propagates unchanged" (``_template_role_names``,
    ``:608-611``), and its own fail-soft contract (``:768-772``) states that a
    missing or unreadable source is unavailable, never a wrong answer.

    Catching only ``FactUnavailable`` would therefore make V5 the **one** check
    of the family that escapes a corrupt registry and takes the runner with it
    (``consistency-check.py`` wraps no check in ``try``), which is precisely the
    outcome the module docstring gives for degrading. The wider catch is scoped
    to this one call and changes nothing in the intact case.
    """
    try:
        return compute_active_roles(root, config)
    except (FactUnavailable, SyncError):
        return None


def _v5_severity(root: Path, config: dict) -> Severity:
    """``ERROR`` once the ``se`` group is enabled, ``WARNING`` while it is closed."""
    group = resolve_activation_gates(root, config).get(V5_GATE_GROUP) or {}
    return Severity.ERROR if group.get("enabled") else Severity.WARNING


def check_role_generation_parity(
    root: Path, config: dict | None = None
) -> list[Finding]:
    """One finding per role declared in ``roles:`` that is never generated (AC-11).

    One finding per role, not per file: the reader repairs a single declaration,
    and a summary of all of them would hide which one to remove.
    """
    project_config = _v5_project_config(root, config)
    generated = _v5_generated_roles(root, project_config) if project_config else None
    if generated is None:
        return []
    severity = _v5_severity(root, project_config)
    declared = {
        role for role in (project_config.get("roles") or []) if isinstance(role, str)
    }
    return [
        Finding(
            severity=severity,
            check=V5_CHECK_ID,
            file=V5_PROJECT_CONFIG_RELPATH,
            message=f"role '{role}' is declared but never generated",
            suggestion=V5_SUGGESTION_BY_SEVERITY[severity],
        )
        for role in sorted(declared - generated)
    ]
