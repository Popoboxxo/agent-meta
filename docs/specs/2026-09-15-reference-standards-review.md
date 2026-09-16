# Reference Standards — Spec Review (independent critic)

> Reviewer: `concept-reviewer` · Date: 2026-09-15 · Branch: `feat/reference-standards-support`
> Target: `docs/specs/2026-09-15-reference-standards-design.md` (`SPEC-REFERENCE-STANDARDS-2026-09-15`)
> Support: `.opencode/skills/spec-plan-workflow/SKILL.md`; implementation surfaces
> `scripts/lib/frontmatter.py`, `scripts/lib/providers.py`, `scripts/lib/provider_transform.py`,
> `scripts/lib/agent_toml.py`, `scripts/lib/consistency/*`, `scripts/consistency-check.py`,
> `config/project-config.schema.json`, `config/ai-providers.yaml`,
> `tests/test_agent_eval_framework.py`, `.github/workflows/orchestration-test.yml`.
> **`status: APPROVED` was set (user pre-approved the direction/policy on 2026-09-15).**

## Verdict: APPROVED

Structurally complete, provider-agnostic by construction, and the IC-04 quiet-strip
contract is both correct and necessary. One factual **MAJOR** (Opencode mechanism
classification / leak-surface count) was found and corrected editorially; no
BLOCKER/MAJOR remains open. Remaining findings are MINOR/INFO.

## Scope reviewed

7 review dimensions + spec-plan §7.1 (Pflichtsektionen, Trace-Anker, Approval-Marker,
No-Placeholder) + the 7 task checks (template completeness, provider-agnostic strip
policy, IC-04 provenance no-leak, whitelist rebuilders, byte-identity ACs, Auftrag 2,
blocker scan). All line references verified against the working tree.

Template completeness: **PASS** — frontmatter (`spec-id:
SPEC-REFERENCE-STANDARDS-2026-09-15`, title, `status`), Problem/Ziel/Nicht-Ziele,
Interface Contracts (IC-01…IC-06, each `Datei::Symbol` + signature + error paths),
Datenfluss (a/b/c), numbered ACs (AC-01…AC-18), Offene Fragen (OQ-1…OQ-11) + Risiken
(R1…R9), Trace-Anker. No `TODO`/`TBD`/`<platzhalter>`/standalone `...`/empty
`Interfaces:` remain (`spec_plan.py:73-82`).

## IC-04 provenance analysis — CONFIRMED NECESSARY AND CORRECT

`build_frontmatter` (`frontmatter.py:230-238`) and
`_transform_frontmatter_for_opencode` (`provider_transform.py:554-561`) both build the
`<!-- agent-meta-provenance: key=value -->` comment from the **stripped** keys'
pre-strip values. A naive "add `reference_standards` to `strip_fields`" would therefore
write the field token into **every** generated file — for the 8 patch surfaces as a
comment after the frontmatter, and for `Codex` through the body: `build_frontmatter`
inserts the comment before `_strip_frontmatter(content)` re-derives the body
(`frontmatter.py:629-636`), and `build_agent_toml_document` embeds that body verbatim as
`developer_instructions` (`agent_toml.py:88`). IC-04's quiet contract (AC-07/AC-08) is
the correct and minimal mitigation; AC-01/AC-08 are necessary, not redundant.

## Whitelist rebuilders

- `Codex` (`codex-toml`): true rebuild — unknown fields are dropped
  (`provider_transform.py:266-281` → `agent_toml.py:46-89`). AC-02's regression pin is
  meaningful.
- `Opencode` (`opencode-native`): **not** a whitelist rebuild. It is a patch through
  `_update_frontmatter_dict` with a fixed `removes` list plus `strip_fields`
  (`provider_transform.py:517-631`, `:603-619`; `frontmatter.py:105-114`). It passes
  unknown keys (incl. `reference_standards`) through today. Corrected (F-01).

## Findings

| ID | Severity | Location | Issue | Change |
|----|----------|----------|-------|--------|
| F-01 | MAJOR (resolved) | Problem 3 §§, Ziel 3, IC-03 "Reichweite", Datenfluss (a)+Tabelle, AC-02 note, R1, R3 | **Opencode was misclassified as a whitelist rebuilder.** VERIFIED: `_transform_frontmatter_for_opencode` patches via `_update_frontmatter_dict` + fixed `removes` list, so `reference_standards` is passed through today; only `Codex` drops unknown fields. Leak surface is **8/9**, not 7/9; AC-02 is a regression pin only for Codex (for Opencode it is a behaviour change). | Corrected editorially in all seven locations (Problem 3, Ziel 3, IC-03, Datenfluss flow + table, AC-02 note, R1, R3). Design/AC assertions unchanged — the resolver still strips for all 9. |
| F-02 | MINOR (corrected) | IC-03 "Kanal-Kompatibilität" | Claimed the two strip channels keep "exakt ihre bisherigen … Semantik", but the resolver changes the combination from `project or provider` (override, `provider_transform.py:385-388`) to **union**. | Prose now states the union explicitly; no IC/AC semantics changed. |
| F-03 | MINOR | IC-05 / R6 | IC-05 adds only `frontmatter-keep-fields`; the pre-existing documented `frontmatter-strip-fields` is **not** modelled in the schema anywhere, and Claude/Gemini/Opencode/Mammouth have `"properties": {}` + `additionalProperties: false` (`project-config.schema.json:735-778`). R6's "bricht die Projekt-Config-Validierung" overstates: `_validate_config` prints schema violations as **warnings**, never hard-fails (`config.py:337-383`). | Add `frontmatter-strip-fields` alongside `frontmatter-keep-fields` in the same 5 modelled provider blocks; soften R6 wording. Author-side. |
| F-04 | MINOR (corrected) | IC-02 Datenfluss (b), OQ-7 | Scope was described as `agents/**/*.md` incl. 3-project overrides; `collect_agent_files` collects only `agents/1-generic/*.md` + `agents/2-platform/*.md` (`consistency-check.py:107-120`); `agents/3-project/` does not exist. | Wording corrected in both places. |
| F-05 | MINOR | AC-14, IC-03 `:34` | AC-14 says the guard finds "keine Provider-Namens-Literale", but `test_no_literal_provider_equality_branches_in_touched_modules` flags only `==`/`!=` comparisons against provider literals (`test_provider_agnostic_dispatch.py:82-92`). `_TOUCHED_MODULES` is at `:27`, not `:34`. | `:34` → `:27` corrected. Extending the tuple with `provider_transform` is safe (verified: no provider-name equality comparisons in that module). AC-14 wording left to the author. |
| F-06 | MINOR (resolved) | IC-02 snippet | A standalone `...` elision line would trip `spec_plan_no_placeholder` (`spec_plan.py:73-82`) in `sync.py --validate-spec-plan`. | Replaced with an explicit comment. |
| F-07 | INFO | AC-17 | Byte-comparison relies on stable PyYAML output across the CI matrix (3.9/3.11/3.12) with unpinned `pyyaml>=6.0`. The existing promptfoo `--check` uses the identical technique and passes, so acceptable. | No action; consider pinning if flakiness appears. |
| F-08 | INFO | all ICs | Verified references: `provider_transform.py:385-388`, `:517-631`, `:554-561`, `:603-619`, `:335-337`; `frontmatter.py:211-238`; `providers.py:119`, `:162`, `:519-532`; `consistency/frontmatter.py:18-19`; `consistency-check.py:57`/`:172`; `report.py:44-75`; schema `:731-780`; `agent_toml.py:46-89`; `standalone.py:216`; `conventions/SKILL.md:43`; `multi-provider.md:576-586`; `gen_promptfoo_config.py:2-19`/`:86-102`; `test_agent_eval_framework.py:113-125`; `orchestration-test.yml:17-25`/`:48`; `gen_routing_llm_eval_catalog.py:18-21`/`:172-183`; `routing-llm-eval/README.md:26-32`; `catalog.generated.yaml:1-11`; 9 registered providers; only 2 `frontmatter-mechanism` entries (Opencode `:236`, Codex `:487`); no `frontmatter_strip_fields` in `config/ai-providers.yaml`; no strip entry in `.meta-config/project.yaml`. | None. |

## Auftrag 2 — verified

- `gen_promptfoo_config.py --check` exists (`:86-102`) and is gated by
  `test_generated_promptfoo_config_is_fresh_and_valid` (`:113-125`), which runs via
  `python -m pytest tests/ -q` in `.github/workflows/orchestration-test.yml:48`
  (PR paths include `tests/**`, `scripts/**`, `config/**`). **Claim confirmed.**
- `catalog.generated.yaml` has **no** freshness test: no file under `tests/` invokes
  `gen_routing_llm_eval_catalog.py` (only the generated header references it). The
  generator has no `--check` (`:170-183`). **Gap confirmed.**
- AC-17 (regenerate to tmp + byte-compare / `--check` flag) is minimal, testable, adds
  no catalog content and no new CI file. **Accepted.**

## Provider-agnosticism — PASS

The resolver lives in `providers.py` (already in the AST guard) and branches purely on
config keys; `keep` wins over `strip`; failures degrade fail-safe to strip with one
warning per `(provider, key)`. No `if provider ==` is introduced, and
`provider_transform.py` contains no provider-name equality comparison, so extending the
guard is safe. The keep-override is config-only (`frontmatter-keep-fields`), satisfying
the user's "per-provider configurable" policy.

## Direct edits made

Frontmatter `status:` → `APPROVED`; body status block; one Revision row; and the
factual corrections F-01/F-02/F-04/F-05/F-06 listed above. No IC/AC semantics were
changed — the corrected statements align the prose with code-verified behaviour and with
the already-normative IC-03 code block.

## OQs needing a user decision

**None.** OQ-3 was the only item flagged `[User approval]`; it is resolved by the user's
explicit policy ("strip `reference_standards` from every provider by default,
per-provider configurable"). OQ-8 (doc surfaces) and OQ-9 (form of the Auftrag-2
protection) are implementation-time defaults covered by "recommended defaults accepted".

## Confirmations

- `status: APPROVED` set with an approval record; no plan and no implementation produced.
- The spec's IC/AC content was not semantically altered.
