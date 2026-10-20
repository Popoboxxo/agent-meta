"""AC-01 harness: render output of every provider-matrix project is byte-identical.

For each provider registered in config/ai-providers.yaml a scratch project
(same single-provider config as tests/test_provider_matrix_sync.py) is synced,
and every generated file is hashed (SHA-256). The result is compared against
the committed manifest ``tests/fixtures/ac01-baseline/hashes.json``, which was
produced on the pre-feature ``main`` state.

Differences are only tolerated for paths matching ``AC01_EXCEPTIONS`` (the
AC-01 exception list (i)-(v) of SPEC-CONTEXT-PROFILES-2026-10-11, kept as data).

Regenerate the manifest (only for a justified rebaseline; ``--write`` is only
allowed on a clean, unmodified ``main`` state, rebaseline only with a documented
reason, Spec AC-01):
    python tests/test_ac01_render_identity.py --write

Rebaseline log (manifest is plain JSON, so reasons are kept here):
- Task 0e.2 (IC-28, AC-01 exception list ii/iii): new role ``meta-doctor`` (all provider
  artifacts, roster/enum/name_index rows in orchestrator, AGENTS.md, copilot-instructions,
  managed-file lists and generated-file-hashes) plus the ``agent-meta-manager`` 1.24.0
  ``doctor-findings-v1`` consumer section and ``handoff.input_contracts`` row in the
  orchestrator routing data. No other render changes.
- Review of package 0e (fix commit): meta-doctor allowlist reduced to the exact IC-23/AC-88 forms, wording
  without "read-only", manager ``input_contracts`` reduced to ``doctor-findings-v1`` (no ``task-spec-v1``).
  Affects only the meta-doctor artifacts, the orchestrator routing data and managed-file hashes.
- Task 1.35 (Q9, IC-15 Nr. 14): ``template-auditor`` loses its ``routing_patterns`` (name_only role
  without keyword rule). Rebaselined only the per-provider orchestrator artifact (its keyword
  routing data / intent rows) and the matching managed-file hashes; no other artifact changed.
- Task 1.05 (IC-18 no. 18, user decision): meta-doctor (new in 0e, unreleased): the NEXT
  conditional ``ROLE_META_FEEDBACK_ACTIVE`` is true in the default (meta-feedback is in the
  ActiveSet) now that ``active_set_variables`` reaches ``build_variables``. Only the
  meta-doctor artifacts of all providers and the dependent generated-file-hashes change; the
  exception regex now also covers two-suffix names (``meta-doctor.agent.md``).
- Task 1.07 (IC-31 EN/DE twin PR, AC-72 exception): the German "Pflicht-Abschluss-Summary" twin of the
  closing summary in 19 templates is unified on the English ``{{CLOSING_SUMMARY_BLOCK}}`` text (patch
  version bump each; ``agent-meta-mammouth-expert`` 1.2.3 re-pinned to ``mammouth-expert@1.6.2``). Of the
  19 roles only ``mammouth-expert`` is active in the provider matrix, so only its per-provider artifact
  (8 providers + ``.agent`` file) and the matching managed-file hashes (9 x ``generated-file-hashes.json``)
  changed - 18 of 1102 hashes. The other 18 roles (knowledge-*, se-*) are not rendered in the matrix.
- Task 1.10 (IC-18 no. 2, user decision ADR-10/Q18: the pipeline drop applies in the DEFAULT too): in the
  default project the ``validator`` and ``developer_tiers`` gates are off, so ``concept-driven-dev`` and
  ``feature-lifecycle`` (``validator``) and ``refactor`` (``senior-developer``) are no longer rendered. Changed
  only: the per-provider orchestrator artifact (9; match table, section 2a detail blocks, ``routing.pipelines``),
  the 3 ``pipeline-details/*.md`` files plus the ``.agent-meta-managed`` index per provider, and the matching
  ``generated-file-hashes.json`` (27 + 9 + 9 + 9 = 54 of 1102 entries; 1075 remain, 27 files vanished). No other
  hash changed.
- Task 1.13 (IC-18 no. 5, AC-48: the default has ``developer_tiers`` off): orchestrator section 3/4 and the
  task-size table name ``developer`` instead of the junior/senior/principal chain, developer's
  ``RECOMMENDED_TIER`` line and the planner step mapping drop ``senior-developer``; minor version bumps
  (orchestrator 8.5.0, developer 4.8.0, planner 1.6.0). Changed: orchestrator, developer, planner per provider
  and generated-file-hashes (4 x 9 = 36 of 1075 entries).
- Task 1.14 (IC-18 no. 6): ``ANTI_RECURSION_BLOCK`` names only reference roles of
  ``role-defaults.yaml: anti_recursion.reference_roles`` that are in the ActiveSet; the default drops
  ``/validator`` (gate off). Changed: orchestrator, developer per provider and generated-file-hashes
  (3 x 9 = 27 of 1075 entries). No template version bump (template source unchanged).
- Task 1.16 (IC-18 no. 8): orchestrator persona/section 11 follow ``ROLE_META_FEEDBACK_ACTIVE`` and the
  AI review roles, SE-mode prose needs ``SE_ENABLED`` (off in the default), ``se-critic`` and
  ``effort-estimator`` only when active, and the static prose names only rendered pipelines (the default
  drops ``concept-driven-dev``/``feature-lifecycle`` mentions, closing the PR C interim). Changed:
  orchestrator per provider + generated-file-hashes (2 x 9 = 18 of 1075 entries).
- Task 1.19 (IC-18 no. 11 / IC-30 triage, AC-71): dispatch/NEXT lines in worker templates are gated on
  their target role (``ROLE_*_ACTIVE``); patch bumps of the triaged templates. In the default only the
  inactive targets disappear (documenter KE route, bug-feature-analyzer ``se-critic``/``se-interface-mgr``
  rows, concept-reviewer ``se-critic`` and developer ``validator`` arrows); the rest is the version bump.
  Changed: 29 agent artifacts per provider (accessibility-specialist ... test-executor, see CHANGELOG) +
  generated-file-hashes (30 x 9 = 270 of 1075 entries).
- Task 1.21 (IC-15 no. 1, F-05): the shared AGENTS.md block is derived from the ACTIVE sharers only.
  Single-provider projects no longer join the path fields of all six catalog sharers with "bzw."
  (agents dir, pending-tasks file, skills dir) and the header banner no longer names inactive sharers.
  Changed: AGENTS.md of the six AGENTS.md providers (6 of 1075 entries). No other hash changed.
- Task 1.22 (IC-15 no. 2, AC-14 path part): Copilot's ``skills_dir`` moves from the never-read
  ``.github/copilot/skills`` to ``.github/skills``. In the default preset no rule is lazy, so only the
  rendered ``SKILLS_DIR`` path changes: Copilot ``agent-meta-manager``, ``mcp-guardrails``,
  ``use-lazy-rules`` and its ``generated-file-hashes.json`` (4 of 1075 entries).
- Task 1.23 (IC-15 no. 9, AC-19): Codex and Mammouth no longer write their unread rules directories
  (project-root ``rules/``, ``.mammouth/rules/``; rules stay embedded in AGENTS.md); Claude gets
  ``CLAUDE.local.md`` (read by Claude Code) instead of ``CLAUDE.personal.md``. Removed: 2 x 22 rules-dir
  files (19 rules + 3 managed indexes) and ``Claude/CLAUDE.personal.md``; added ``Claude/CLAUDE.local.md``;
  changed: Claude ``.gitignore`` (``CLAUDE.local.md`` entry) and the Codex/Mammouth
  ``generated-file-hashes.json`` (49 entries; 1075 -> 1031). AGENTS.md is unchanged.
- Task 1.33 (IC-15 no. 12, F-16): the AGENTS.md header banner lists the active providers by context file
  (``> **AI ROUTING:** Codex -> AGENTS.md``) instead of the hard-wired ``Opencode->AGENTS.md | Gemini->
  AGENTS.md``; lazy-skill tables list only skills the sync writes for the provider - the default preset has
  none, so ``use-lazy-rules`` is no longer rendered. Changed: 6 x AGENTS.md (banner, embedded table gone),
  removed 4 x ``use-lazy-rules.md`` (Claude, Continue, Gemini, Copilot rules dirs), changed their 4
  ``.agent-meta-managed`` indexes and 4 ``generated-file-hashes.json`` (18 entries; 1031 -> 1027).
- Task 1.25 (IC-15 no. 4, F-04/F-09): Codex gets a ``.codex/config.toml`` with a managed
  ``[agents] max_depth`` table (new artifact) and its ``spawn_agent`` delegation syntax uses the real
  ``agent_type``/``message`` parameters instead of ``agent``/``task`` (config/delegation-syntax.yaml).
  Changed: ``Codex/.codex/config.toml`` (added), ``Codex/.codex/agents/orchestrator.toml``, the 4
  ``Codex/.codex/pipeline-details/*.md`` and ``Codex/.meta-config/generated-file-hashes.json``
  (7 of 1028 entries). No other provider's render changed.
- Task 1.26 (IC-15 no. 5, F-10): the KimiCode ``agent-transform`` maps ``TodoWrite``->``TodoList`` and
  renames ``hint``->``whenToUse`` on every Kimi agent, and the orchestrator gains the Kimi ``subagents:``
  allow-list (``ActiveSet.routable``) plus the ``native_agent_tools`` fan-out tool ``AgentSwarm``.
  Changed: all 62 ``KimiCode/.kimi-code/agents/*.md`` and the KimiCode
  ``.meta-config/generated-file-hashes.json`` (63 of 1028 hashes). No other provider's render changed.
- Task 1.27 (IC-15 no. 6, F-11): the Mammouth ``agent-transform`` switches to ``frontmatter-mechanism:
  opencode-native`` (Mammouth is an OpenCode fork), so every Mammouth agent emits a lowercase
  ``permission`` map (incl. ``task``/``todowrite``) and a set ``mode`` instead of the inert Claude-cased
  ``tools:`` object, plus a ``subagent_depth`` from the ``required_depth`` capability (``inject-subagent-depth``).
  Changed: all 62 ``Mammouth/.mammouth/agents/*.md`` and the Mammouth
  ``.meta-config/generated-file-hashes.json`` (63 of 1028 hashes). No other provider's render changed.
- Task 1.28 (IC-15 Nr. 8, F-08/F-07): Gemini no longer writes its unread ``.gemini/rules`` directory
  (rules stay embedded in AGENTS.md) and ``.gemini/settings.json`` gains ``context.fileName=AGENTS.md``
  so Gemini CLI actually reads the shared core. Removed: the 21 ``Gemini/.gemini/rules`` files
  (18 rules + 3 managed indexes); changed: ``Gemini/.gemini/settings.json`` and the Gemini
  ``.meta-config/generated-file-hashes.json`` (23 of 1028 entries; 1028 -> 1007). AGENTS.md and no
  other provider's render changed.
- Task 1.29 (IC-15 Nr. 3, AC-14 / F-13): Copilot rule files gain the mandatory ``.instructions.md``
  suffix plus ``applyTo``/``description`` frontmatter, and every Copilot agent frontmatter ``name:``
  drops the leaked extension (``orchestrator.agent`` -> ``orchestrator``). Changed/reassigned: 18
  ``Copilot/.github/instructions/*.md`` removed + 18 ``*.instructions.md`` added, all 63
  ``Copilot/.github/agents/*.agent.md`` names, the ``.github/instructions/.agent-meta-managed`` index
  and the Copilot ``.meta-config/generated-file-hashes.json`` (101 of 1007 entries; Copilot-only,
  0 non-Copilot drift; ``meta-doctor.agent.md`` is covered by the existing AC-01 exception). No other
  provider's render changed.
- Task 1.31 (IC-15 Nr. 10, AC-10 / F-14): Continue rule files gain
  ``alwaysApply: false`` + ``description`` frontmatter (driven by the
  ``rules-always-apply`` capability; before, the frontmatter was only emitted
  when the rules-preset opted in, so the default preset shipped 18,591 B of
  rules always active - 28 % of the local template window, study §3.8) and
  ``.continue/rules/project-context.md`` no longer ships unresolved
  ``{{PLATFORM}}``/``{{BUILD_COMMAND}}``/``{{RUNTIME}}``/``{{TEST_COMMAND}}``
  lines. Changed: 19 ``Continue/.continue/rules/*.md`` plus
  ``project-context.md`` and the Continue ``.meta-config/generated-file-hashes.json``
  (20 of 1007 entries; Continue-only, 0 non-Continue drift).
- Task 1.32 (IC-15 Nr. 11, AC-20 / F-15): the Agent Directory / ``AGENT_DELEGATION_TABLE``
  is now one valid Markdown table - the ``agents-table`` partial no longer emits blank
  lines between rows (full mode) and the orchestrator no longer repeats a second header
  above the partial-provided ``| Agent | Core Capabilities |`` header (orchestrator
  8.5.0 -> 8.5.1). Changed: the orchestrator artifact of all 9 providers, the 6
  ``AGENTS.md`` files (Agent Directory rows lose the blank-line separation) and the 9
  ``generated-file-hashes.json`` (24 of 1007 entries). No other artifact changed.
- Task 1.38 (IC-15 Nr. 17, AC-51): the reflection overrides now come from the CONSUMER
  config instead of agent-meta's own tracked ``.meta-config/project.yaml``, so the three
  active ``{{MAX_ITERATIONS}}`` roles (``control-framework-assessor``,
  ``fraud-risk-assessor``, ``risk-based-audit-planner``) render the framework value ``3``
  instead of agent-meta's leaked override ``5``. Changed: those 3 artifacts per provider
  (9 providers) plus the 9 ``generated-file-hashes.json`` (36 of 1007 entries; 0 unrelated drift).
- Task 1.40 (IC-15 Nr. 21, AC-10 / F-32): a provider declaring
  ``read_only_enforcement: sandbox`` (Codex) plus the ``read-only-extra-fields`` override
  map now emits ``sandbox_mode: read-only`` for roles whose template tool list carries
  neither ``Write`` nor ``Edit`` (previously the pauschale ``workspace-write``). Changed: the
  21 read-only ``Codex/.codex/agents/*.toml`` roles plus the Codex
  ``.meta-config/generated-file-hashes.json`` (22 of 1007 entries; Codex-only, 0 non-Codex
  drift; ``meta-doctor.toml`` is covered by the existing AC-01 exception).
- Task 1.42 (IC-15 Nr. 23, AC-73): provider literals are removed from the generic
  templates. ``agent-meta-manager``/``agent-meta-scout``/``prompt-governor`` use the
  ``{{CONTEXT_FILE}}`` placeholder, ``agent-meta-manager``/``release`` wrap their
  provider-specific snippets in ``> **Example (provider-specific):**`` blocks, and
  ``mammouth-expert`` is split into a provider-neutral ``1-generic`` base plus a
  standalone ``2-platform/agent-meta-mammouth-expert.md`` (based on
  ``provider-expert``, both 2.0.0). Changed: 5 agent artifacts per provider (9
  providers = 45), 9 ``generated-file-hashes.json`` and 1
  ``Copilot/.github/copilot-instructions.md`` — 55 of 1007 hashes; 0 added/removed.
  ``knowledge-migrator`` is not rendered in the matrix. No other artifact changed.
- Task 11 (2b.2, IC-05, AC-23): the orchestrator template §2a, §9 and the ``<context>``
  agent table are wrapped in ``{{#if CONTEXT_PROFILE_COMPACT}}…{{else}}…{{/if}}`` (minor
  bump 8.5.1 -> 8.6.0). The ``{{else}}`` branch is the unchanged text, so without the
  ``context-profile`` opt-in every render only differs by the version bump in the
  orchestrator artifact. Changed: the 9 per-provider orchestrator artifacts
  (``orchestrator.md``/``.toml``/``.agent.md``) plus the 9
  ``generated-file-hashes.json`` (18 of 1003 hashes; 0 added/removed). No other
  artifact changed.
- C2/C3/IC-05 roster gating (SPEC-CONTEXT-PROFILES-2026-10-11): the compact agent roster in
  both emitters (orchestrator ``<context>`` names line and the shared-file ``agents-list-compact``)
  is gated on the per-provider ``roster_in_harness`` capability (IC-09). The orchestrator template
  is bumped 8.6.0 -> 8.7.0; the ``{{else}}`` (full) branch is unchanged, so without the
  ``context-profile`` opt-in every render only differs by that version bump. Changed: the 9
  per-provider orchestrator artifacts (``orchestrator.md``/``.toml``/``.agent.md``) plus the 9
  ``generated-file-hashes.json`` (18 hashes; 0 added/removed). No other artifact changed.
- Task 28 (2e.2, IC-28/AC-23/AC-59): new role ``meta-optimizer`` registration: per-provider role
  artifacts, roster/name_index/enum rows in the orchestrator, AGENTS.md/context-file rows,
  managed-file lists and ``generated-file-hashes.json``. The exception regex is extended to
  ``.*/meta-optimizer\\.(md|toml|agent\\.md)$`` so the Copilot two-suffix form
  (``meta-optimizer.agent.md``) is covered. No other render changed.
- Task 29 (2e.3, IC-27/AC-59): ``agent-meta-manager`` gains ``handoff.input_contracts +=
  config-patch-proposal-v1`` -> one additional ``input_contracts`` routing row in the orchestrator
  routing data. Changed: the 9 per-provider orchestrator artifacts plus the 9
  ``generated-file-hashes.json`` (18 of 1012 hashes; 0 added/removed). No other render changed.
- Task 30 (2e.4, IC-27/AC-59/AC-90/AC-91): the ``agent-meta-manager`` template gains the new
  section ``## 10c. Optimizer-Vorschläge anwenden (Advisory Mode)`` (the three steps
  Analyse/Vorschau/Anwendung of IC-27 Rev. 3.1) and a minor version bump ``1.24.1 -> 1.25.0``
  (new optional section, convention: minor). The section is prose plus three bash invocations,
  so it only changes the rendered ``agent-meta-manager`` artifact of each provider and the
  managed-file hash of that file. Changed: the 9 per-provider ``agent-meta-manager`` artifacts
  (``Claude/.claude/agents/agent-meta-manager.md``, ``Codex/.codex/agents/agent-meta-manager.toml``,
  ``Continue/.continue/agents/agent-meta-manager.md``,
  ``Copilot/.github/agents/agent-meta-manager.agent.md``,
  ``Gemini/.gemini/agents/agent-meta-manager.md``,
  ``KimiCode/.kimi-code/agents/agent-meta-manager.md``,
  ``Mammouth/.mammouth/agents/agent-meta-manager.md``,
  ``Opencode/.opencode/agents/agent-meta-manager.md``,
  ``ZCode/.zcode/agents/agent-meta-manager.md``) plus the 9
  ``generated-file-hashes.json`` (18 of 1012 hashes; 0 added/removed). No other render changed;
  ``AC01_EXCEPTIONS`` is NOT extended — the exception list stays limited to the new role
  artifacts ``meta-doctor``/``meta-optimizer`` (Spec AC-01 iv/v).
- Task 30 fix round (2e.4, review findings): three *text* corrections inside the new
  ``## 10c.`` section of the ``agent-meta-manager`` template (the scoped "no manual edit"
  rule, the release/approval wording, the ``preview.json`` payload sentence). The rendered
  section keeps its line count (36 lines) and the template version pin stays ``1.25.0``
  (the section was not yet released), so the *set* of affected paths is unchanged: again
  exactly the 9 per-provider ``agent-meta-manager`` artifacts plus the 9
  ``generated-file-hashes.json`` (18 of 1012 hashes; 0 added/removed).
- Task 30 polish round (2e.4, review findings): one further *text* correction inside the
  same §10c section -- the "no manual edit" rule now names §13 as well
  ("§3/§5/§8" -> "§3/§5/§8/§13 (confirmation, schema check, re-sync, SE cascade)"), because
  §13 (SE cascade) is a documented ``project.yaml`` change path next to §3/§5/§8. The
  rendered section keeps its line count (36 lines) and the template version pin stays
  ``1.25.0`` (the section was not yet released), so the *set* of affected paths is
  unchanged: again exactly the 9 per-provider ``agent-meta-manager`` artifacts plus the 9
  ``generated-file-hashes.json`` (18 of 1012 hashes; 0 added/removed).
- Task 31 (2e.5, IC-27 Rev. 3.1 step 4 / AC-90 / AC-23): the orchestrator template gains the
  common-body section ``## 3a. Optimizer proposals — mandatory preview gate`` (show
  ``preview.json`` to the user via ``main_chat``, obtain the explicit confirmation, only then
  instruct ``agent-meta-manager`` with ``--preview``; verbatim relayed-ID rule; no Bash for
  orchestrator/``meta-optimizer``) and a minor version bump ``8.7.0 -> 8.8.0``. The section
  is outside every ``CONTEXT_PROFILE_COMPACT`` conditional, so both profiles carry it; the
  default (``full``) render therefore differs only by that section plus the version pin.
  Changed: the 9 per-provider orchestrator artifacts (``orchestrator.md``/``.toml``/
  ``.agent.md``) plus the 9 ``generated-file-hashes.json`` (18 of 1012 hashes; 0
  added/removed). No other render changed; ``AC01_EXCEPTIONS`` is NOT extended. Incidental
  rebaseline: ``tests/fixtures/compact-golden/orchestrator.md`` (owner of the compact
  render, unchanged by this task's scope) is updated because the compact golden also
  carries the template version and the common-body section.
- Task 32 (CI fix, AC-49): §3a is wrapped in ``ROLE_AGENT_META_MANAGER_ACTIVE`` +
  ``ROLE_META_OPTIMIZER_ACTIVE`` (template ``8.8.0 -> 8.8.1``). The AC-01 matrix keeps
  every role active, so the section stays and the render differs only by the version pin.
  Changed: the 9 per-provider orchestrator artifacts plus the 9 ``generated-file-hashes.json``
  (18 of 1012 hashes; 0 added/removed). No other render changed; ``AC01_EXCEPTIONS`` is NOT
  extended. The default (repo) render drops the section because the repo whitelist has no
  ``meta-optimizer``; that fixture is the slimming/compact golden, rebaselined with the same
  reason in ``tests/test_template_slimming_equivalence.py``.

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
from typing import Dict, List, Sequence

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
# (iv)/(v) produce no render diff in a regular sync, so there is no pattern (Spec AC-01 iv/v);
# (ii)/(iii) (meta-doctor roster rows in existing files, golden rebaseline) are done
# via rebaseline in package 0e, not via a path pattern.
# Empty entries would hide drift, so every pattern must stay role/entry specific.
AC01_EXCEPTIONS = frozenset({
    r".*/meta-doctor\.(md|toml|agent\.md)$",
    r".*/meta-optimizer\.(md|toml|agent\.md)$",
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


def _hash_file(path: Path, root: Path, dates: Sequence[str]) -> str:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    # Normalize run-specific values: scratch root path (native, posix, JSON-escaped)
    # and the date stamp(s) captured once per run (before/after the sync).
    root_variants = {str(root), root.as_posix(), str(root).replace("\\", "\\\\")}
    for needle in sorted(root_variants, key=len, reverse=True):
        data = data.replace(needle.encode(), b"<ROOT>")
    for d in dates:
        data = data.replace(d.encode(), b"<DATE>")
    return hashlib.sha256(data).hexdigest()


def render_matrix_hashes(fixture_root: Path) -> Dict[str, str]:
    """Sync every provider into ``fixture_root/<provider>`` and hash all files.

    Returns ``{"<provider>/<relpath>": sha256}``.
    """
    fixture_root = Path(fixture_root)
    hashes: Dict[str, str] = {}
    date_before = date.today().isoformat()
    projects: List[tuple] = []
    for provider in _PROVIDERS:
        project = _make_project(fixture_root, provider)
        for f in sorted(project.rglob("*")):
            if not f.is_file():
                continue
            rel = f.relative_to(fixture_root).as_posix()
            if _SKIP_RE.search(rel):
                continue
            projects.append((rel, f))
    # Date captured once before and once after all syncs; both are normalized.
    dates = {date_before, date.today().isoformat()}
    for rel, f in projects:
        hashes[rel] = _hash_file(f, fixture_root, sorted(dates))
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
        mutated[victim] = _hash_file(target, root, [date.today().isoformat()])
        assert diff_against_manifest(mutated, baseline) == [f"changed: {victim}"]
    finally:
        target.write_bytes(original)


def test_ac01_exception_list_allows_meta_doctor_artifacts():
    baseline = {"codex/.codex/agents/developer.toml": "a"}
    current = dict(baseline, **{"codex/.codex/agents/meta-doctor.toml": "b"})
    assert diff_against_manifest(current, baseline) == []


def test_ac01_exception_list_allows_meta_optimizer_artifacts():
    baseline = {"codex/.codex/agents/developer.toml": "a"}
    current = dict(baseline, **{
        "Claude/.claude/agents/meta-optimizer.md": "b",
        "Codex/.codex/agents/meta-optimizer.toml": "c",
        # Copilot uses the two-suffix form; the old `[a-z]+$` pattern misses
        # it because of the dot in `.agent.md`.
        "Copilot/.github/agents/meta-optimizer.agent.md": "d",
    })
    assert diff_against_manifest(current, baseline) == []


if __name__ == "__main__":
    if "--write" not in sys.argv:
        sys.exit("usage: python tests/test_ac01_render_identity.py --write")
    with tempfile.TemporaryDirectory() as td:
        manifest = render_matrix_hashes(Path(td))
    _MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    _MANIFEST.write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {len(manifest)} hashes to {_MANIFEST}")
