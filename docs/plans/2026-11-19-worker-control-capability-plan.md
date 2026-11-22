---
status: APPROVED
date: 2026-11-19
approval: "User-Freigabe 2026-11-19 (E-17 approved + Roadmap approved — volle Umsetzung 2.3)"
spec-id: SPEC-WORKER-CONTROL-CAPABILITY-2026-11-19
spec-status: APPROVED
klasse: M
branch: feat/worker-control-capability
base-head: 7dc9e88
pipeline_stages:
  execute: 1
  review-req: 6
  review-quality: 7
  rebaseline: 8
  pr: 9
  merge: 10
---

# Worker-Control-Capability (PR B / P12 / E-17) Implementation Plan

> Status: APPROVED — User-Freigabe 2026-11-19 („E17 ist nun Approved! Machen Masterplan roadmap auch! Approved Go! Volle Umsetzung!"). Spec `status: APPROVED`, Roadmap `docs/plans/2026-11-15-master-roadmap.md:3` APPROVED.
> Branch `feat/worker-control-capability` (HEAD `7dc9e88`). Dies ist ein Plan — keine Implementierung, kein Commit durch die Planungsrolle.

**Goal:** #1176 provider-übergreifend beheben — Worker-Control-Prosa wird über ein abgeleitetes Capability-Flag gegated statt „where granted"; pro Provider nur Tools nennen, die im Frontmatter stehen. Capability `worker_control_tools` ersetzt `primary-role-tools` (E-17); Continue `subagent` → WARNING; Claude/Kimi `primary` → „prose-only"; #1172 reine Doku (E-18); Trailer nur Verweis auf P37 (E-19).

**Architecture:** `config/provider-capabilities.yaml` (`capabilities.<Provider>.worker_control_tools`) → Resolver `scripts/lib/config.py::_build_core_variables` + `scripts/lib/agent_sync.py` (Provider-Override) → `WORKER_CONTROL_ENABLED` / `PROGRESS_CHAT_PUSH_ENABLED` (nicht an `hooks` gekoppelt) → Render `scripts/lib/provider_transform.py::_with_native_tools` (Whitelist-Validierung) → Prosa-Gate `agents/1-generic/orchestrator.md` → Check `scripts/lib/consistency/topology.py` → eine Rebaseline am Ende.

**Tech Stack:** Python 3.9, Stdlib + PyYAML, Markdown-Templates mit `{{#if}}`-Platzhaltern, unittest/pytest, provider-agnostisch (Capability-Keys/Config-Flags, nie `if provider == "Name"`).

**Spec:** docs/specs/2026-11-19-worker-control-capability-spec.md

**Estimated effort:** `effort-estimator` (Textverweis, keine eigene Schätzung) — Klasse M.

## Global Constraints

- Python 3.9; nur Stdlib + PyYAML, keine neuen Dependencies.
- Provider-agnostisch: **niemals** `if provider == "Name"` in geänderten Pfaden; alle Verzweigungen über Capability-Keys/Config-Flags (AC 10, `provider-agnostic`-Skill).
- Conservative default: fehlender/leerer `worker_control_tools`-Key ⇒ `[]` / Flag `false` (fail-safe, kein Wurf).
- Keine neuen Entscheidungen, keine neuen Dateien, keine Spec-Änderung — B1–B5 sind 1:1 aus der APPROVED-Spec übernommen.
- 0.4 (`config/role-defaults.yaml:11` plan→default + Test) ist mit Commit `c73319cb` bereits umgesetzt — nicht im Plan wiederholt.
- Branch `feat/worker-control-capability`; kein Direkt-Commit auf `main`, kein Force/Admin/Auto, kein Worktree-Isolation.
- Conventional Commits, Englisch, Imperativ, ≤ 72 Zeichen; Trailer genau 1× je Zeile: `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`.
- Ein Commit je Task B1–B5; Rebaseline = **ein** letzter Commit (AC/G/B/H), keine zweite; PR + MERGE durch Rolle `git`.
- Alle Shell-Kommandos mit `rtk`-Präfix (rtk passt durch, wenn kein Filter vorhanden).
- Kein Wall-Clock-/Netzwerk-Test; reine Render-/Config-/Check-Assertions; `python3 scripts/sync.py --validate` Exit 0 (Warnungen erlaubt).
- Jeder Testbeeld deckt eine AC 1–10 ab; keine AC ohne Test.
- Ledger/Checkpoints: `.tmp/orchestrator-checkpoints/20261119-worker-control-ledger.md` (nach jedem Task-Boundary fortschreiben).

## File Structure

- Modify: `config/provider-capabilities.yaml` — neuer Key `worker_control_tools` (B1)
- Modify: `config/provider-tools.yaml` — Whitelist-Kommentare `:19-20` (B1)
- Modify: `config/ai-providers.yaml` — Transform-Specs `primary-role-tools` → Capability (B1)
- Modify: `scripts/lib/provider_transform.py` — `:397-401`, `:743`, Whitelist `:745` (B1)
- Modify: `scripts/lib/config.py` — `:2607-2617` Resolver (B1)
- Modify: `scripts/lib/agent_sync.py` — `:568-572`, `:889` Provider-Override (B1)
- Modify: `scripts/lib/variables.py`, `scripts/lib/standalone.py`, `scripts/lib/consistency/placeholders.py` — Platzhalter-Registrierung/Fallbacks (B1)
- Create/Modify: `tests/test_topology_capability_invariant.py`, `tests/test_provider_agnostic_dispatch.py` (B1)
- Modify: `agents/1-generic/orchestrator.md` — `:240`, `:270-272`, `:280` (B2) **und** §7 `:258-276` (B4) — **strikt sequentiell**
- Modify: `tests/test_orchestrator_worker_report_contract.py` + Create Tool-Mention⊆FM-Test (B2)
- Modify: `scripts/lib/consistency/topology.py` — WARNING-Findings (B3)
- Modify/Create: Test für WARNING-Finding (Continue subagent, Claude/Kimi primary prose-only) (B3)
- Modify: `rules/1-generic/use-orchestrator.md` — `## Git Delegation` `:85-93` (B4)
- Modify: `agents/1-generic/git.md` — `## 4. Operation` `:52`, Commit-Format `:134-136` (B4); `:140` **unverändert** (B5/IC-6)
- Create: `tests/test_merge_pattern_docs.py` — `test_merge_pattern_in_three_templates` (B4)
- Modify: Prosa-Stellen mit Trailer-Thema — Verweis auf P37 / `#1168` / `#1247` (B5)
- Modify (Rebaseline, letzter Commit): `tests/fixtures/topology-golden/orchestrator*.md`, `tests/fixtures/compact-golden/orchestrator*.md`, `tests/fixtures/slimming-golden/orchestrator*.md` (G); `ac01-baseline/hashes.json`, `context-hashes.json`, `generated-file-hashes.json` (H/AC); `tests/test_context_budgets.py`-Ceilings (B)

## Tasks

### Task B1: Capability & Resolver

**Agent / Tier:** `developer` (Tier B1)
**Depends on:** —
**Stage:** execute (Schritt 1)
**Files:**
- Modify: `config/provider-capabilities.yaml`, `config/provider-tools.yaml`, `config/ai-providers.yaml` (Transform-Specs), `scripts/lib/provider_transform.py` (`:397-401`, `:743`), `scripts/lib/config.py` (`:2607-2617`), `scripts/lib/agent_sync.py` (`:568-572`, `:889`), `scripts/lib/variables.py`, `scripts/lib/standalone.py`, `scripts/lib/consistency/placeholders.py`
- Test: Create/Modify `tests/test_topology_capability_invariant.py`, `tests/test_provider_agnostic_dispatch.py` (AC-01)

**Interfaces:**
- Consumes: IC-1, IC-2
- Produces: `worker_control_tools` + `WORKER_CONTROL_ENABLED`; `primary-role-tools` ersetzt

**AC:** 1, 2, 3, 4, 10
**Review-Pflicht:** Stufe 1 `validator` (AC/DoD-Abgleich) → Stufe 2 `code-reviewer` (Blast-Radius, SOLID/DRY)

- [ ] Step 1 (rot): Invariantentest je Provider — Claude `["SendMessage","TaskStop"]`, Codex `["send_input","close_agent","wait_agent"]`, Gemini `["send_message"]`, übrige `[]`; fehlender Key → Leer-Default + Invarianten-Finding (Muster `tests/test_topology_capability_invariant.py:81`); `WORKER_CONTROL_ENABLED` true/false je Key; `PROGRESS_CHAT_PUSH_ENABLED` aus Messaging-Tool-Capability (ohne Hook-Support); Platzhalter in `variables.py`/`standalone.py`/`consistency/placeholders.py` registriert; kein `if provider ==`.
- [ ] Step 2 (grün): Capability-Block + Resolver in `config.py::_build_core_variables` / `agent_sync.py` (Provider-Override, Whitelist-Validierung `provider_transform.py:745`, WARNING statt Abbruch); Lesestelle `:743` auf `worker_control_tools` umstellen; `primary-role-tools` in `ai-providers.yaml` + `provider-tools.yaml:19-20` aktualisieren.
- [ ] Step 3 (pass): `rtk python3 -m pytest tests/test_topology_capability_invariant.py tests/test_provider_agnostic_dispatch.py -q` grün; `rtk python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 4 (commit): `feat: add worker_control_tools capability and render flag` + Trailer `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` (1×).

### Task B2: Prosa-Gate & Orchestrator-Template

**Agent / Tier:** `developer` (Tier B2)
**Depends on:** B1 (braucht `WORKER_CONTROL_ENABLED`)
**Stage:** execute (Schritt 2)
**Files:**
- Modify: `agents/1-generic/orchestrator.md` (`:240`, `:270-272`, `:280`)
- Test: Modify `tests/test_orchestrator_worker_report_contract.py` (Zeilen 90-99 prüfen heute schon `SendMessage`/`TaskStop`), Create Tool-Mention⊆FM-Test

**Interfaces:**
- Consumes: IC-3, IC-2-Flag (`WORKER_CONTROL_ENABLED`)
- Produces: gegatete, provider-agnostische Prosa ohne „where granted"

**AC:** 1, 2, 3
**Review-Pflicht:** Stufe 1 `validator` → Stufe 2 `code-reviewer`. **Ownership-Konflikt:** teilt `agents/1-generic/orchestrator.md` mit B4 → B2 vor B4, strikt sequentiell.

- [ ] Step 1 (rot): Tool-Mention⊆FM-Test — jeder genannte Tool-Name steht im FM des aktiven Providers; `test_orchestrator_worker_report_contract.py` für provider-spezifische Prosa; kein „(where granted)" nirgends; bei `WORKER_CONTROL_ENABLED=false` verschwinden Claude-Toolliterale vollständig aus dem Render.
- [ ] Step 2 (grün): Sätze `:240`/`:270-272`/`:280` in `{{#if WORKER_CONTROL_ENABLED}} … {{/if}}` klemmen; nur Tools aus `worker_control_tools` des aktiven Providers nennen; „(where granted)" entfernen; Version/Frontmatter gemäß `conventions`-Skill beibehalten.
- [ ] Step 3 (pass): `rtk python3 -m pytest tests/test_orchestrator_worker_report_contract.py -q` grün.
- [ ] Step 4 (commit): `feat: gate orchestrator worker prose on WORKER_CONTROL_ENABLED` + Trailer (1×).

### Task B3: Continue/primary Findings

**Agent / Tier:** `developer` (Tier B3)
**Depends on:** B1 (Capability-Kontext); file-disjunkt zu B2/B4
**Stage:** execute (Schritt 3)
**Files:**
- Modify: `scripts/lib/consistency/topology.py`
- Test: Modify/Create TestWARNING-Finding (Continue subagent, Claude/Kimi primary prose-only)

**Interfaces:**
- Consumes: IC-4, E-17/§5.5(3)/(4)
- Produces: WARNING-Check-Output (Exit 0 bei WARNING)

**AC:** 5, 6
**Review-Pflicht:** Stufe 1 `validator` → Stufe 2 `code-reviewer`.

- [ ] Step 1 (rot): Test — genau ein WARNING-Finding „subagent unsupported → sequential-text degradation" bei Continue-Fail-Safe (`subagent_dispatch: false`, `topology_degrade.subagent: sequential-text`); kein Clamp auf `primary`; Claude/Kimi `primary` → „prose-only"; `sync.py --validate` Exit 0 bei WARNING, Exit 1 nur bei ERROR mit `require-runtime-gate`.
- [ ] Step 2 (grün): WARNING-Finding in `topology.py` emittieren — identisch zu O5 (P10/PR A), kein zweites abweichendes Finding; kein Still-Degrade.
- [ ] Step 3 (pass): `rtk python3 -m pytest <TestWARNING-Finding> -q` grün; `rtk python3 scripts/sync.py --validate` Exit 0.
- [ ] Step 4 (commit): `fix: warn on subagent degrade, report primary prose-only` + Trailer (1×).

### Task B4: #1172-Doku (E-18, nur Doku)

**Agent / Tier:** `junior-developer` (Tier B4)
**Depends on:** B2 (Ownership-Konflikt: `agents/1-generic/orchestrator.md`)
**Stage:** execute (Schritt 4)
**Files:**
- Modify: `rules/1-generic/use-orchestrator.md` (`## Git Delegation`, `:85-93`), `agents/1-generic/orchestrator.md` (§7, `:258-276`), `agents/1-generic/git.md` (`## 4. Operation` `:52`, Commit-Format `:134-136`)
- Test: Create `tests/test_merge_pattern_docs.py` (`test_merge_pattern_in_three_templates`, Muster Phase-D-Plan `:187`)

**Interfaces:**
- Consumes: IC-5
- Produces: `#1172`/`#783` je genau 1× je Template; keine Permission-Regel

**AC:** 7
**Review-Pflicht:** Stufe 1 `validator` → Stufe 2 `code-reviewer`. **Ownership-Konflikt:** teilt `orchestrator.md` mit B2 → nach B2.

- [ ] Step 1 (rot): `test_merge_pattern_in_three_templates` — genau 1 Treffer `#1172` und 1 `#783` im Merge-Absatz je Template; `#1172` = ausschließlich Doku (kein Hook, kein Setting, keine Permission-Regel); Satz in `use-orchestrator.md` außerhalb der `AUTO_COMMIT_ENABLED`/`ROLE_GIT_ACTIVE`-Zweige einfügen (Phase-D-Plan `:189`).
- [ ] Step 2 (grün): Merge-Muster-Text in `use-orchestrator.md:85-93`, `orchestrator.md:258-276`, `git.md:52`/`:134-136`; Fallback #783 + Verweis auf den 2026-11-06 blockierten Pfad (Ursache außerhalb des Repos, nicht reproduziert).
- [ ] Step 3 (pass): `rtk python3 -m pytest tests/test_merge_pattern_docs.py -q` grün.
- [ ] Step 4 (commit): `docs: add orchestrator merge pattern reference (#1172)` + Trailer (1×).

### Task B5: P37-Verweis (letzter inhaltlicher Task)

**Agent / Tier:** `developer` (Tier B5)
**Depends on:** B1, B2, B3, B4 — **hängt an allen, letzter Task**
**Stage:** execute (Schritt 5)
**Files:**
- Modify: Prosa-Stellen mit Trailer-Thema (Verweis auf `docs/specs/2026-11-15-git-trailer-contract-spec.md`, `#1168`/`#1247`)
- **Keine** Änderung an `agents/1-generic/git.md:140` (P37-Implementierungsstelle, IC-6)
- Test: AC-8-Prüfung des P37-Verweises (kein Contract-Duplikat)

**Interfaces:**
- Consumes: IC-6, §5.4
- Produces: P37-Verweis ohne Contract-Duplikat (Rebaseline erfolgt als eigener letzter Commit, Schritt 8)

**AC:** 8
**Review-Pflicht:** Stufe 1 `validator` → Stufe 2 `code-reviewer`.

- [ ] Step 1 (rot): Test — 2.3-Prosa verweist auf P37 / `docs/specs/2026-11-15-git-trailer-contract-spec.md` und `#1168`/`#1247`, ohne `commit.trailers`-Rangfolge oder Trailer-Regeln zu duplizieren; `git.md:140` bleibt unverändert.
- [ ] Step 2 (grün): Prosa-Stellen mit Trailer-Thema um den Verweis ergänzen; kein Eingriff in `git.md:140`.
- [ ] Step 3 (pass): `rtk python3 -m pytest <AC-8-Test> -q` grün.
- [ ] Step 4 (commit): `docs: reference P37 trailer contract without duplication` + Trailer (1×).

### Task 6: Review Stufe 1 — Requirements (Stage `review-req`)

**Agent:** `validator`
**Depends on:** B1–B5
**Files:** keine (reine Prüfung)
**Interfaces:** Consumes: alle B-Tasks; Produces: Pass/Fail-Liste je AC.
**AC:** 1–10 (Abgleich)

- [ ] Step 1: AC 1–10 gegen Spec und Diff abgleichen; DoD, keine neuen Entscheidungen/Dateien, kein `if provider ==`, Trailer-Konvention, 0.4 nicht wiederholt.
- [ ] Step 2: Bei Rot → Befund an den verantwortlichen B-Task zurück, kein Merge. Kein Commit.

### Task 7: Review Stufe 2 — Quality (Stage `review-quality`)

**Agent:** `code-reviewer`
**Depends on:** 6
**Files:** keine (reine Prüfung)
**Interfaces:** Consumes: B1–B5 + Review 6; Produces: Blast-Radius/SOLID/DRY-Bericht.
**AC:** 9, 10 (Querschnitt)

- [ ] Step 1: Blast-Radius, SOLID/DRY, keine Provider-Literale, Whitelist-/Placeholder-Konsistenz prüfen; `rtk python3 scripts/sync.py --validate` Exit 0 bestätigen.
- [ ] Step 2: Bei Rot → zurück an B-Task; bei Grün → Rebaseline freigeben. Kein Commit.

### Task 8: Rebaseline — EIN letzter Commit (Stage `rebaseline`)

**Agent:** `developer`
**Depends on:** 7
**Files (Modify):**
- G: `tests/fixtures/topology-golden/orchestrator*.md`, `tests/fixtures/compact-golden/orchestrator*.md`, `tests/fixtures/slimming-golden/orchestrator*.md`
- H/AC: `ac01-baseline/hashes.json`, `context-hashes.json`, `generated-file-hashes.json`
- B: `tests/test_context_budgets.py`-Ceilings

**Interfaces:** Consumes: finale Templates/Quellen (B1–B5); Produces: konsistente Goldens/Hashes/Ceilings.
**AC:** 9
**Review-Pflicht:** Stufe 1 `validator` → Stufe 2 `code-reviewer` (identisch mit Review 6/7, hier final).

- [ ] Step 1: Sauberer Arbeitsbaum; roten Ausgangszustand der Golden-/Hash-Tests bestätigen.
- [ ] Step 2: G/H/AC/B einmalig aktualisieren — **kein** SA-, Rules- oder Allowlist-Anteil (E-15/E-12 andere PRs), **keine zweite Rebaseline**.
- [ ] Step 3: `rtk python3 scripts/sync.py --validate` Exit 0; betroffene Pin-Tests grün.
- [ ] Step 4 (commit): `chore: rebaseline orchestrator goldens, hashes and ceilings` + Trailer (1×).

### Task 9: Pull Request (Stage `pr`)

**Agent:** `git`
**Depends on:** 8
**Files:** keine
**Interfaces:** Consumes: Rebaseline-Commit; Produces: PR mit Spec-/AC-Referenz.

- [ ] Step 1: PR erstellen — nur `git`-Rolle; kein Force/Admin/Auto; Titel/Body verweisen auf Spec `SPEC-WORKER-CONTROL-CAPABILITY-2026-11-19` und AC 1–10.
- [ ] Step 2: Nur grüne CI + Status `MERGEABLE` als Voraussetzung für Task 10. Kein Merge hier.

### Task 10: MERGE (Stage `merge`)

**Agent:** `git`
**Depends on:** 9
**Files:** keine
**Interfaces:** Consumes: PR (Task 9); Produces: **MERGE-Commit**.

- [ ] Step 1: Merge ausschließlich durch `git`-Rolle, nur bei grüner CI + `MERGEABLE`; nur MERGE-Commit, kein Force/Admin/Auto; Push/Tag/Branch-Management bleibt bei `git`.
- [ ] Step 2: Nach Merge Ledger-Eintrag in `.tmp/orchestrator-checkpoints/20261119-worker-control-ledger.md` abschließen.

## Re-planning

Nach jedem Task-Boundary (besonders nach B1 Resolver, B2/B4 Ownership-Konflikt, Review 6/7 und dem einzigen Rebaseline-Commit) Annahmen neu prüfen: Capability-Mapping noch konsistent? `WORKER_CONTROL_ENABLED` fail-safe? B2/B4-Reihenfolge korrekt? AC ohne Test? Plan aktualisieren statt einfrieren.

## Self-Review

- Jeder Task mappt auf genau eine Rolle: B1/B2/B3/B5 `developer`, B4 `junior-developer`, Review 6 `validator`, Review 7 `code-reviewer`, Rebaseline 8 `developer`, PR/MERGE 9–10 `git`. Jedes Akzeptanzkriterium ist messbar (AC-Nummer + Testbefund/Exit-Code/Diff-Bedingung).
- `Files:`/`Interfaces:` vollständig; B2 und B4 teilen `agents/1-generic/orchestrator.md` → strikt sequentiell (B2 → B4); B5 hängt an allen → letzter inhaltlicher Task; Rebaseline = ein letzter Commit; keine Parallelgruppe mit Dateiüberlappung.
- `pipeline_stages` deckt alle sechs `plan-driven`-Stages ab: `execute: 1`, `review-req: 6`, `review-quality: 7`, `rebaseline: 8`, `pr: 9`, `merge: 10`.
- AC-Abdeckung: 1–3 (B1+B2), 4 (B1), 5–6 (B3), 7 (B4), 8 (B5), 9 (Task 8 + Reviews/Validate), 10 (B1 + Review 7). Keine AC ohne Test.
- Spec-Referenz + `spec-id: SPEC-WORKER-CONTROL-CAPABILITY-2026-11-19` im Frontmatter; `**Spec:**` auf die APPROVED-Spec; `status: APPROVED` + User-Freigabe 2026-11-19.
- Effort-Schätzung: `effort-estimator` (Textverweis, hier bewusst nicht berechnet).
