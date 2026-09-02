---
name: wave9-agent-definitions-consistency
description: Wave-9/#564,#567,#570,#575 batch — DONE, all 4 issues implemented on branch chore/agent-definitions-consistency-batch, full suite green (884 passed/2 skipped, x2 runs), sync.py --validate clean, NOT committed
metadata:
  type: project
---

All 4 Wave-9 issues from `docs/plans/audit-2026-08-refactoring-roadmap.md` implemented on branch
`chore/agent-definitions-consistency-batch` (based on main@50e82aa2 + `6dd46782`). **Not
committed/pushed** — left for the main agent's `git` delegate. Full suite green (ran twice: once
mid-batch after #567's Python changes, once again after ALL edits including #575's Python changes,
to avoid the collection-time staleness trap noted in the Wave-8 memory). `sync.py --validate`
unchanged from baseline (only the 2 pre-existing orchestrator-strict warnings, no new errors/warnings
from our changes on THIS repo's own project.yaml — the new lint rules did fire correctly when tested
against a deliberately broken temp file, see below).

**Order followed:** #564 → #567 → #575 → #570, per the task's explicit instruction (ascending effort,
#570 last as the biggest chunk).

**Issue-by-issue:**

- **#564** (3-tier → 4-tier doc): `agents/1-generic/{junior-developer,developer,senior-developer,
  orchestrator}.md` updated to "4-tier system (junior → developer → senior → principal)".
  `senior-developer.md` gained a new workflow step 7 "Escalation to principal-developer (last resort)"
  (2+ verified failures → `STATUS: escalate` + `RECOMMENDED_TIER: principal-developer` + task summary +
  failure log), a matching `<output_contract>` escalate block, and a constraints line. `orchestrator.md`
  §4 tier table gained a `principal-developer` row (trigger: senior-developer failed 2+ times,
  `orchestrator_only`). Runtime config (`config/role-defaults.yaml` `principal-developer` role,
  `reflection_pairs[0].on_blocked: escalate_to_principal-developer`, `blocked-review-v1` handoff
  contract) already existed from an earlier wave — this was pure doc/template catch-up, no config
  changes needed. Versions bumped (junior 1.2.1→1.2.2 patch, developer 4.0.1→4.0.2 patch, senior-dev
  1.3.0→1.4.0 minor, orchestrator 7.10.0→7.11.0 minor). 4 full-replacement `2-platform/*-developer.md`
  overrides (`agent-meta-developer`, `sharkord-developer`, `hacs-developer`, `homeassistant-developer`)
  had their `based-on: "1-generic/developer.md@4.0.1"` pin bumped to `@4.0.2` + their own version
  patch-bumped, to avoid tripping the `stale_platform_overrides` audit check.

- **#567** (orphaned `</output>` tags): found via a paired-tag scan (NOT a plain substring grep — see
  false-positive note below) — **42 files** in `agents/1-generic/` had a trailing `</output>` line with
  no matching `<output>` anywhere (0 opens, 1 close each, always the literal last line of the file).
  None of `agents/2-platform/*.md` were affected. All 42 fixed by stripping exactly that trailing line.
  New lint rule added to `scripts/lib/config_audit.py`: `_find_unpaired_closing_tags()` +
  `_STANDALONE_TAG_RE` — **critically, this only matches lines that are *exactly* a tag** (stripped
  line == `<tag>` or `</tag>`, nothing else), NOT a substring scan. A naive substring/line-count
  approach produces real false positives in this codebase: prose mentions like `` `<context>` `` inline
  mid-sentence (developer.md: "see `<context>`") and tag-shaped placeholder examples inside fenced
  output blocks (bug-feature-analyzer.md has a literal `<list>` as example content under "### Affected
  components", never closed — that's a legitimate unclosed *opening* tag placeholder, not a bug; the
  rule is deliberately one-directional, only flags closes > opens, never opens > closes). New category
  `unpaired_closing_tags` (severity error) wired into `audit_config()`, `format_report()`,
  `report_to_dict()`, and into `sync.py`'s `_handle_validate()` (adds to `consistency_errors`, so it
  actually fails `--validate` with exit 1 — verified by temporarily re-appending `</output>` to
  `git.md` and confirming EXIT=1 + the warning message, then reverting). 4 new tests in
  `tests/test_config_audit.py` (detection, balanced-tags no-op, prose/placeholder false-positive guard,
  2-platform scanning).

- **#575 Problem 1** (tool-least-privilege): **Decision: Option B** (keep `Bash` on
  `validator`/`code-reviewer`, justify explicitly, add a WARN-only lint — not Option A/C). Rationale
  found by reading both templates' workflows: `validator` genuinely needs Bash for "test runner, git,
  sync validation" (process-conformance checks: are tests green, correct commit format, does
  `sync.py --validate` pass) and `code-reviewer` for `git diff` + running existing tests as review
  input — both are verification-only uses, never code edits (both already had "Never make code
  corrections"/"Never write code" constraints). Stripping Bash (Option A) would break real
  functionality. A new tool tier (Option C) was unnecessary ceremony for 2 roles. **What was actually
  inconsistent and got fixed:** the codebase already has an established convention across ~8 other
  roles (`dependency-auditor`, `security-auditor`, `bug-feature-analyzer`, `prompt-engineer`,
  `devops-engineer`, `ui-ux-designer`, `incident-responder`) of annotating the `<tools>` Bash bullet
  with an explicit `(read-only)`/verification-only qualifier — `validator.md`'s Bash bullet lacked this
  annotation (had it, just less explicit); both `validator.md` and `code-reviewer.md` bullets were
  tightened to match the convention explicitly + cross-reference `<constraints>`. New WARN-only lint:
  `_find_tool_privilege_mismatch()` in `config_audit.py` — scoped to the `<persona>` block content only
  (regex extracts `<persona>...</persona>`, then searches *within* that substring for "read-only"
  case-insensitive) to avoid false positives from templates that mention "read-only" describing
  something else entirely (`mammouth-expert.md` has no `<persona>` tag at all and mentions "Read-only"
  only as a description of an external CLI flag — correctly produces zero matches since the persona
  regex finds nothing). Currently 0 violations repo-wide (preventive lint, not fixing an existing
  breach) — verified against all `1-generic` templates whose persona says "read-only"
  (`backend-reviewer`, `database-reviewer`, `explorer`, `frontend-reviewer`, `ui-reviewer` — all
  correctly Read/Glob/Grep/TodoWrite only, no Write/Edit). New category `tool_privilege_mismatch`
  (severity warning) wired the same way as #567's category, EXCEPT in `sync.py` it only logs a warning
  and does NOT add to `consistency_errors` (does not block `--validate`), per the issue's own explicit
  steer ("WARNT, nicht blockiert").

- **#575 Problem 2** (agent-meta-manager.md length): **No action taken — investigated and found the
  premise doesn't hold against the current file state.** Current file is 283 lines (CLAUDE.md's own
  guideline: "200–500 Zeilen optimal"), squarely in the optimal band, and already under both the hard
  500-line ceiling AND the issue's suggested 300–400 target. The issue's "1493 words" framing measures
  a different metric (word count, not line count) and conflates it with the CLAUDE.md line-count
  guideline — likely written against an earlier/different version of the file, or just a
  metric-confusion in the original issue text. `git log --oneline -- agents/1-generic/
  agent-meta-manager.md` shows no recent trimming by another wave that would explain a discrepancy, so
  this isn't stale-issue-vs-already-fixed; the numbers in the issue just don't match reality. Did NOT
  force an unrequested extraction-to-howto-doc to manufacture a fix for a problem that doesn't exist
  (ponytail: "does this need to exist at all?" — no). If a future session disagrees, re-measure with
  `wc -l` first before doing the extraction work.

- **#570** (domain-reviewer standardization, the big one): `backend-reviewer.md`, `database-reviewer.md`,
  `frontend-reviewer.md`, `ui-reviewer.md` each gained a new `<tools>` section (per-tool rationale,
  domain-flavored) and a new `<constraints>` section (read-only enforcement line, P4 finding-schema
  requirement, P2 adversary-pass requirement, P3 rule_id requirement, a delegation matrix mirrored from
  each template's existing `<context>` Boundaries list, `**User proxy:**`, and a `**Language:** review
  reports → English.` line) — all 4 bumped 1.0.0→1.1.0 (minor, new optional sections). **Deliberate
  interpretation call:** the issue's acceptance criterion "alle vier enthalten `<language>`-Regel-
  Sektion" was read as "an explicit language rule must be present", NOT "invent a literal standalone
  `<language>` XML tag" — grepped the entire `agents/1-generic/` corpus and confirmed ZERO templates
  (out of 76) use a standalone `<language>` tag anywhere; the established, universal convention across
  all other roles (including `code-reviewer.md`, which these 4 templates were explicitly asked to align
  with) is a `**Language:**` prose line inside `<constraints>`. Inventing a one-off tag used by only 4
  files would have been a NEW inconsistency, contradicting the standardization goal. The existing
  P1–P5 rules-index/two-pass-protocol/output-contract sections were left completely untouched (kept,
  per the issue's explicit instruction to preserve that style) — only new sections were added, nothing
  renamed (`<output-contract>` stays hyphenated, was NOT merged/renamed to match the classic
  `<output_contract>` naming used elsewhere, to minimize diff/risk; if a future session wants full tag-
  name unification across styles, that's a separate, larger decision). `code-reviewer.md`'s Delegation
  section gained a new bidirectional routing table (4 rows, one per domain reviewer, tier "specialist",
  condition "after code-reviewer pass, only when domain depth needed") — bumped 1.2.2→1.2.3 (patch, for
  the #575 tools-bullet wording change) →1.3.0 (minor, for this table addition). `docs/architecture/
  03-agent-roles.md` (the file `ARCHITECTURE.md` actually points to for role docs — the issue said
  `docs/ARCHITECTURE.md`, which doesn't exist at that path; the real file is `./ARCHITECTURE.md` at
  repo root, which references `docs/architecture/03-agent-roles.md` as the "Agent Roles" deep-dive)
  gained 5 new table rows (`code-reviewer` + 4 domain reviewers, previously entirely absent from that
  doc despite being real active roles) and a new "Review-Pipeline" prose section documenting `developer
  → code-reviewer → (Domain-Reviewer, falls nötig) → senior-developer` plus the bidirectional-routing +
  read-only-tools facts.

**Sync/validate verification:** `python3 scripts/sync.py --dry-run` and `--validate` run after each
issue (#564, #567) and once more after all 4 (#570 last) — zero new warnings/errors beyond the 2
pre-existing `orchestrator-strict.no-hook-support` ones (Opencode/Gemini, unrelated, pre-existing on
main). Full real `sync.py` run at the end regenerated 192 files (`.claude/`, `.gemini/`, `.mammouth/`,
`.opencode/` agent copies + `CLAUDE.md`/`MAMMOUTH.md` for the tier-table/hint changes). The 4 domain-
reviewer templates and `backend-reviewer`/etc. produce NO generated output in `.claude/agents/` etc. in
THIS repo specifically — they're not in this repo's own `.meta-config/project.yaml` `roles:` list (this
repo doesn't dogfood those 4 roles for itself), so their template edits only show up as
`agents/1-generic/*.md` diffs, not generated-copy diffs. That's expected, not a bug — verified by
`grep` on `.meta-config/project.yaml` before concluding.

**New/changed lint infra (both in `scripts/lib/config_audit.py`, both wired into `sync.py
_handle_validate()`):**
1. `unpaired_closing_tags` (error, blocks `--validate`) — #567.
2. `tool_privilege_mismatch` (warning, does NOT block `--validate`) — #575.
Both scan `agents/1-generic/*.md` + `agents/2-platform/*.md` via a new shared helper
`_collect_template_files()`.

**Full-suite timing:** ~6:20–6:25 per run with `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` (this env's globally
installed `pytest_homeassistant_custom_component` plugin auto-loads via setuptools entry point and
crashes on import — unrelated `pyOpenSSL`/`acme` version mismatch in this machine's site-packages, NOT
a repo problem; `-p no:pytest_homeassistant_custom_component` does NOT suppress it since it's loaded
before plugin-name filtering applies at the entry-point-loading stage — only the env var works).
884 passed, 2 skipped, both full runs (mid-batch and final) — matches the Wave-8 memory's noted
baseline count/timing almost exactly.

**Not done / explicitly out of scope this session:** no git commit/push (per task instructions — left
for the main agent's `git` delegate). No `<output-contract>` → `<output_contract>` tag renaming
(deliberate scope-minimization call, see #570 note above).
