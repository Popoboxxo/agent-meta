---
pipeline_stages:
  implement: 1
status: geplant
date: 2026-11-23
spec: docs/specs/2026-11-23-decision-1335-payload-attribution-spec.md
spec-id: SPEC-1335-PAYLOAD-ATTRIBUTION
spec-status: APPROVED
issue: "#1335"
branch: fix/decision-points-bundle-20261123
klasse: L
---

# Payload-Attribution (#1210) als Allow-Matching-Quelle für die git-Rolle (#1335) — Implementation Plan

> Status: geplant. Plan erst nach `Status: APPROVED` der Spec (gegeben) ausführbar.
**Goal:** Auf Providern mit `hook-agent-id` + `hook-role-field` kommt die Rolle aus dem Harness-Payload; der `git`-Agent braucht dort keine Sentinel-Zeile, der Guard bleibt fail-closed. **Architecture:** Bestehendes `_ROLE_ATTRIBUTION` (`:444-468`) wird konsumiert → `EFFECTIVE_ROLE` → vier Rollenflags → Gates; Render-Seite capability-abgeleitete Platzhalter. **Tech Stack:** Python 3.9 Stdlib, Bash 3.2, pytest, Markdown-Templates.
**Spec:** `docs/specs/2026-11-23-decision-1335-payload-attribution-spec.md` — `spec-id: SPEC-1335-PAYLOAD-ATTRIBUTION`, Status: APPROVED (User, 2026-11-23).
**Estimated effort:** laut `effort-estimator` (Textreferenz, keine eigene Schätzung) — Klasse L: drei Subsysteme (Guard-Laufzeit, Sync-Rendering, Template), sicherheitsrelevante Fail-closed-Semantik, eine gedeckte Golden-Rebaseline.

## Rollout- und Closure-Gates (OQ-1 / OQ-3 / OQ-4)

- **PRE-ROLLOUT-GATE (Task 5, OQ-1 + OQ-3):** Exakter `agent_type`-Wert des `git`-Subagenten und Vollständigkeit des Feldes auf allen Spawn-Pfaden müssen durch echte Payload-Erfassung belegt sein. **Blockiert ausschließlich den Rollout**, nicht die Implementierung: Task 1–3 laufen mit synthetischen Payload-Tests weiter.
- **CLOSURE-GATE (Task 6, OQ-4):** Der deterministische Check (`/permissions` → „Recently blocked") vor Schließen von #1335. **Kein Implementierungs-Gate.**
- Beide Gates sind explizit benannt und haben eigene Tasks mit messbarem Bericht.

## Global Constraints

- Kein neues Attributionsfeld, keine neue Capability, kein neuer Grant, kein Secret/Token. `GIT_PAYLOAD_ATTRIBUTION` ist ausschließlich capability-abgeleitete Render-Variable (IC-6), keine Rollenquelle.
- Rollenquelle ist allein die bereits gesetzte #1210-Attribution `_ROLE_ATTRIBUTION` (`:451`/`:457`); **kein** neues Attributionsverfahren. Sentinel ist bei `payload-field` nur Mismatch-/Audit-Signal.
- **FAIL-CLOSED-GATE IC-1 (explizit):** Capability `true`, `agent_id` nicht leer, `agent_type` leer/unbekannt → `exit 2`, niemals `permissionDecision: allow`, kein Sentinel-Fallback, kein Delegate-Grant. Unknown/empty never grants.
- Rückfall ausschließlich auf Providern ohne die Capabilities (Variante A/B): exakt bisheriger Pfad, byte-identischer Render.
- **Provider-agnostisch:** Capability-Flags (`provider_has_capability`), nie `if provider == "Name"`. `config/ai-providers.yaml:64-75` und `scripts/lib/hooks.py:570-578` bleiben unverändert (IC-4/IC-8).
- Kein Eingriff in Destructive-Gate, Branch-Guard, Strict-Mode-`agent_id`-Logik, `auto_commit`-Allowlist-Semantik (#1181) oder Nicht-Git-Rollen.
- Modellschreibbarer Kommandotext darf nie Grants erzeugen; Sentinel bleibt Convention boundary, `eval`/Indirektion bleibt Convention boundary (R-1).
- Golden-/Pin-Rebaseline nur für die in IC-9 gedeckten Dateien; jeder andere Bruch → STOP, keine Selbst-Rebaseline.
- Keine Closing-Keywords in Plan oder Commit-Messages; Issue-Bezug rein als `(#1335)`.
- Branch `fix/decision-points-bundle-20261123`; kein Push/Tag/Branch-Management (Rolle `git`). Commit-Betreff Englisch, Imperativ, ≤ 72 Zeichen, ohne UTF-8-BOM.

## Review-Findings (bindend)

1. **ADR-Konsequenz als Hypothese:** Die Aussage „enge Allow-Rules matchen ohne Kommentarzeile" ist laut Issue #1335 **nicht verifiziert** (OQ-4). Sie darf in Spec-/Doku-Folgetexten nur als Hypothese geführt werden, nie als Fakt. Keine Änderung am Beantragungstext der APPROVED-Spec in diesem Plan.
2. **OQ-1/OQ-3:** Payload-Capture als PRE-ROLLOUT-GATE (Task 5), nicht als Implementierungs-Blocker.
3. **IC-1:** Fail-closed-Gate explizit benannt und mit eigenem Test versehen (Task 2).
4. **OQ-4:** Deterministischer Check vor #1335-Closure (Task 6).

## Exakte Strings — Variante C (IC-5, Python-Literale, unverändert aus der Spec)

```python
_GIT_SENTINEL_SCOPE_WITH_BOTH_CAPS = (
    " On providers whose hook payload carries a harness-set agent identity, the `git` role "
    "is taken from that payload — do NOT add a sentinel comment to any Bash call: a "
    "comment-only first line is a separate sub-command and can prevent narrow allow rules "
    "such as `Bash(git status *)` from matching. Destructive-operation, branch and "
    "auto-commit-scope checks still apply."
)
_GIT_SENTINEL_BASH_RULE_WITH_BOTH_CAPS = (
    "`git` and `gh` calls without a sentinel line "
    "(role comes from the hook payload; see workflow step 0)"
)
```

## File Structure

- Modify: `scripts/lib/agent_sync.py` — 3. Scope-Variante + `GIT_PAYLOAD_ATTRIBUTION` in `_build_provider_vars` (IC-5/IC-6)
- Modify: `scripts/lib/consistency/placeholders.py` — `GIT_PAYLOAD_ATTRIBUTION` registrieren (`:162-165`, IC-6)
- Create: `tests/test_git_payload_attribution.py` — A/B/C-Matrix der Provider-Variablen
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh` — `_ROLE_ATTRIBUTION` → `EFFECTIVE_ROLE`, Flags, Fail-closed, Audit (IC-1/IC-2/IC-3)
- Modify: `tests/test_hook_single_parse.py` — #1210-Matrix auf Fail-closed umstellen (`:248-255`), Payload-Grants/Audit (IC-9)
- Modify: `tests/test_orchestrator_guard_hook.py` — Destructive/Strict unverändert mit Payload-Rolle (IC-2, AC-07)
- Modify: `agents/1-generic/git.md` — konditionale Blöcke `:26-35`, `:41-46`, `:97-101`, `:163` (IC-7)
- Modify: `tests/test_git_sentinel_gh_scope.py` — Variante-C-Render, 0 Literal-Token
- Modify: `tests/test_git_template_sentinel_doc.py` — Assertion auf gerenderten Output
- Create: `tests/fixtures/slimming-golden/git-payload-attribution.md` — Golden C (Golden B bleibt unverändert)
- Create: `docs/analysis/2026-11-23-1335-payload-capture.md` — OQ-1/OQ-3-Beweisführung
- Modify: `CHANGELOG.md` — Eintrag (Englisch), Allow-Rule-Hypothese als Hypothese

---
pipeline_stages:
  implement: 1
---

### Task 1: Provider-Rendering — `GIT_PAYLOAD_ATTRIBUTION` und dritte Scope-Variante
**Agent:** developer
**Depends on:** —
**Files:** Modify `scripts/lib/agent_sync.py`; Modify `scripts/lib/consistency/placeholders.py`; Create `tests/test_git_payload_attribution.py`
**Interfaces:** Produces `provider_vars["GIT_PAYLOAD_ATTRIBUTION"]: "true"|"false"`, `provider_vars["GIT_SENTINEL_SCOPE_BLOCK"]`/`["GIT_SENTINEL_BASH_RULE"]` (3 Varianten, exakte Strings oben); Consumes `provider_has_capability(pc, "hook-agent-id"|"hook-role-field")`, `pc: dict`.
- [ ] Step 1: Test schreiben (fail): Variante A (beide false) byte-identisch zu `_GIT_SENTINEL_SCOPE_WITHOUT_HOOK_AGENT_ID`/`_GIT_SENTINEL_BASH_RULE_WITHOUT_HOOK_AGENT_ID`; B (nur `hook-agent-id`) byte-identisch zu `_GIT_SENTINEL_SCOPE_WITH_HOOK_AGENT_ID` und `_GIT_SENTINEL_BASH_RULE_WITH_HOOK_AGENT_ID` (#1307); C exakt die beiden Spec-Literale; `GIT_PAYLOAD_ATTRIBUTION == "true"` nur bei beiden Capabilities.
- [ ] Step 2: Implementieren: Modul-Konstanten `_GIT_SENTINEL_SCOPE_WITH_BOTH_CAPS` / `_GIT_SENTINEL_BASH_RULE_WITH_BOTH_CAPS`; `_git_sentinel_scope_vars(pc)` (`:593-608`) 3. Zweig; `GIT_PAYLOAD_ATTRIBUTION` in `_build_provider_vars` (`:690`) aus `pc` ableiten; Namen in `placeholders.py:162-165` registrieren. `scripts/lib/hooks.py:570-578` unverändert.
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_git_payload_attribution.py` und `python3 scripts/sync.py --validate` — kein unbekannter/unbenutzter Platzhalter.
- [ ] Step 4: Commit-Vorschlag `feat: derive payload-attribution render flags from capabilities`

**Akzeptanz:** AC-05 (A/B-Basis), AC-06, AC-08 (Registrierung); kein Providername im Diff; `hooks.py` unverändert.

### Task 2: Guard-Laufzeit — `EFFECTIVE_ROLE`, Fail-closed, Audit
**Agent:** developer
**Depends on:** —
**Files:** Modify `hooks/1-generic/orchestrator-guard-impl.sh`; Modify `tests/test_hook_single_parse.py`; Modify `tests/test_orchestrator_guard_hook.py`
**Interfaces:** Produces `EFFECTIVE_ROLE: str` (lowercase), `IS_GIT_SENTINEL`/`IS_ORCH_SENTINEL`/`IS_ALLOWLIST_SENTINEL`/`IS_GRANT_SENTINEL: 0|1`, Audit `attribution=payload-field|sentinel`; Consumes `_P_AGENT_TYPE` (`:246`, normiert `:454`), `_ROLE_ATTRIBUTION` (`:451`/`:457`), `HOOK_AGENT_ID_RELIABLE`/`HOOK_ROLE_FIELD_RELIABLE` (`:379`/`:386`), `hook_audit_log_append` (`hook_common.sh`, Aufruf `:459-464`/`:559-578`), `DECLARED_AGENT` (nur noch Mismatch-Quelle).
- [ ] Step 1: Test schreiben (fail): `test_role_field_empty_falls_back_to_sentinel` (`:248-255`) → `test_fail_closed_empty_role_field_no_sentinel_grant` (exit 2, kein Grant, Audit `decision=rejected`); neu `test_payload_grants_without_sentinel` (AC-01), `test_unknown_payload_role_fails_closed` (AC-03/04), `test_payload_role_audit_attribution` (Audit-Feld); in `test_orchestrator_guard_hook.py` `test_destructive_ops_blocked_even_with_git_sentinel` und `test_strict_mode_sentinel_exemption` um Payload-Rolle ergänzen (AC-07).
- [ ] Step 2: Implementieren: nach `:468` `EFFECTIVE_ROLE` aus `_ROLE_ATTRIBUTION` setzen (`payload-field` → normiertes `_P_AGENT_TYPE`, sonst Sentinel-Rolle); `:479-537` und Matching-Gates `:1738`, `:1758-1769`, `:1784-1789` auf `EFFECTIVE_ROLE` umstellen (Namen aus Kompatibilitätsgründen behalten); **FAIL-CLOSED-GATE IC-1** umsetzen: leere/unbekannte Rolle bei `payload-field` → exit 2, nie `permissionDecision: allow`, kein Sentinel-/Delegate-/Grant-Fallback; Mismatch (`:458-465`) bleibt exit 2 + `class=role-mismatch`; Audit-Zeilen um `attribution=` ergänzen. Kein neues Payload-Feld, kein Grant erfunden.
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_hook_single_parse.py tests/test_orchestrator_guard_hook.py` — alle grün, Capability-false-Pfade unverändert.
- [ ] Step 4: Commit-Vorschlag `fix: use payload role attribution for guard allow matching`

**Akzeptanz:** AC-01, AC-02, AC-03, AC-04, AC-07; `_ROLE_ATTRIBUTION` wird konsumiert (nicht nur gesetzt); `git add -- f` ohne Sentinel bei `agent_type=git` → exit 0 + `role=git attribution=payload-field`; `agent_type=developer` + Sentinel → exit 2 `role mismatch`; leere/unbekannte Rolle → exit 2; `git reset --hard` → unverändert exit 2 `user approval`.

### Task 3: Template `git.md` — Sentinel nur bei Variante A/B
**Agent:** developer
**Depends on:** 1
**Files:** Modify `agents/1-generic/git.md`; Modify `tests/test_git_sentinel_gh_scope.py`; Modify `tests/test_git_template_sentinel_doc.py`; Create `tests/fixtures/slimming-golden/git-payload-attribution.md`
**Interfaces:** Produces gerendertes `git.md` Variante C ohne Literal-Token, Golden C; Consumes `GIT_PAYLOAD_ATTRIBUTION`, `GIT_SENTINEL_SCOPE_BLOCK`, `GIT_SENTINEL_BASH_RULE` aus Task 1.
- [ ] Step 1: Test schreiben (fail): Render bei beiden Capabilities — `#agent-meta:agent=git` kommt 0-mal vor, Schritt-0-Absatz exakt `_GIT_SENTINEL_SCOPE_WITH_BOTH_CAPS`, `<tools>`-Zeile exakt ``- **Bash** — all git/gh commands, `_GIT_SENTINEL_BASH_RULE_WITH_BOTH_CAPS` ``; Golden B und `<tools>`-Zeile ohne Capability byte-identisch zum Bestand (AC-05/06).
- [ ] Step 2: Implementieren: `:26-35`, `:41-46`, `:97-101`, `:163` in einen `{{#if GIT_PAYLOAD_ATTRIBUTION}}`-Block mit `{{else}}`-Zweig und abschließendem `{{/if}}` fassen: If-Zweig = Variante-C-Text aus den exakten Strings oben, Else-Zweig = wörtlich alter Text inkl. `{{GIT_SENTINEL_SCOPE_BLOCK}}`/`{{GIT_SENTINEL_BASH_RULE}}` (Variante B). Kein Literal-Sentinel im `if`-Zweig. Golden C anlegen, Golden B nicht ändern; `config/ai-providers.yaml:64-75` unverändert.
- [ ] Step 3: Test (pass): `python3 -m pytest tests/test_git_sentinel_gh_scope.py tests/test_git_template_sentinel_doc.py` grün; `python3 scripts/sync.py --validate` und `--check` ohne Findings.
- [ ] Step 4: Commit-Vorschlag `fix: drop git sentinel on payload-attributed providers`

**Akzeptanz:** AC-05, AC-06, AC-08; Golden B byte-identisch, Golden C vorhanden; kein Literal-Token im C-Render.

### Task 4: A/B/C-Matrix, AC-Nachweis und gedeckter Pin-Pass
**Agent:** tester
**Depends on:** 1, 2, 3
**Files:** Create (keine) — Bericht; Modify nur die in IC-9 gedeckten Golden/Pin-Dateien
**Interfaces:** Consumes Artefakte aus Task 1–3, IC-9, AC-01..08.
- [ ] Step 1: Gesamtsuite `python3 -m pytest tests/test_hook_single_parse.py tests/test_orchestrator_guard_hook.py tests/test_git_payload_attribution.py tests/test_git_sentinel_gh_scope.py tests/test_git_template_sentinel_doc.py` ausführen; AC-01..08 je mit testbarem Testnamen belegen.
- [ ] Step 2: Pin-Pass: Brüche auflisten; nur IC-9-gedeckte Dateien (Golden C, gedeckte Pins) dürfen wandern; jeder andere Bruch → STOP, Ursache klären, kein Rebaseline.
- [ ] Step 3: Bericht mit AC-Matrix und Pin-Ergebnis; `python3 scripts/sync.py --validate` grün.
- [ ] Step 4: Commit-Vorschlag nur bei gedeckter Pin-Änderung `test: rebaseline payload-attribution goldens`

**Akzeptanz:** AC-01..08 vollständig mit Testnamen belegt; keine ungedeckte Pin-Änderung; FAIL-CLOSED-GATE IC-1 durch `test_fail_closed_empty_role_field_no_sentinel_grant` nachgewiesen.

### Task 5: PRE-ROLLOUT-GATE — Payload-Capture (OQ-1 / OQ-3)
**Agent:** tester
**Depends on:** — (kein Implementierungs-Blocker; blockt nur den Rollout)
**Files:** Create `docs/analysis/2026-11-23-1335-payload-capture.md`
**Interfaces:** Consumes echter PreToolUse-Payload eines dispatched `git`-Subagenten (`agent_id`, `agent_type`) sowie alle legitimen Spawn-Pfade (custom agents, `--agent`).
- [ ] Step 1: Echten PreToolUse-Payload eines dispatched `git`-Subagenten erfassen; exakten `agent_type`-Wert festhalten (OQ-1; Erwartung `git`, nicht frontmatter `template-git`).
- [ ] Step 2: Vollständigkeit von `agent_type` auf allen legitimen Spawn-Pfaden prüfen (OQ-3): custom agents und `--agent`.
- [ ] Step 3: Bericht: weicht der Wert ab oder fehlt das Feld auf einem Pfad → Rollout-Gate ROT; Fail-closed-Regel (unbekannte Rolle → exit 2) bleibt aktiv, kein Sentinel-Fallback einführen.
- [ ] Step 4: Commit-Vorschlag `docs: record #1335 payload capture evidence`

**Akzeptanz:** OQ-1 und OQ-3 namentlich beantwortet; bei negativem Befund Rollout explizit blockiert. Implementierung Task 1–3 lief unabhängig mit synthetischen Payloads weiter.

### Task 6: CLOSURE-GATE — OQ-4-Deterministik und DoD/Traceability
**Agent:** validator
**Depends on:** 4, 5
**Files:** Create (keine) — Bericht
**Interfaces:** Consumes Task-4-AC-Matrix, Task-5-Payload-Evidenz, AC-01..08 und Spec `SPEC-1335-PAYLOAD-ATTRIBUTION`.
- [ ] Step 1: DoD-/Traceability-Check Spec ↔ Task-ID ↔ Testname; FAIL-CLOSED-GATE IC-1 und Review-Finding 1 (ADR-Hypothese) als erfüllt verifizieren.
- [ ] Step 2: OQ-4 deterministischen Check auf echtem Claude-Lauf durchführen (`/permissions` → „Recently blocked" mit/ohne Sentinel); Ergebnis wörtlich festhalten.
- [ ] Step 3: Bericht: erst bei grünem OQ-4 ist #1335 closure-fähig; Allow-Rule-Match bleibt bis dahin Hypothese; keine Closing-Keywords verwenden.

**Akzeptanz:** OQ-4 deterministisch geprüft und dokumentiert; ADR-Konsequenz nicht als Fakt ausgegeben; kein Closing-Keyword im Bericht.

### Task 7: CHANGELOG und Review-Finding-Doku
**Agent:** documenter
**Depends on:** 3, 6
**Files:** Modify `CHANGELOG.md`
**Interfaces:** Consumes Spec-ADR und Task-6-Bericht.
- [ ] Step 1: CHANGELOG-Eintrag (Englisch): payload attribution is authoritative for guard role matching; sentinel reduced to mismatch/audit signal; hook-less providers unchanged.
- [ ] Step 2: Konsequenz der engen Allow-Rules ausdrücklich als Hypothese (pending OQ-4) formulieren, nicht als Fakt (Review-Finding 1).
- [ ] Step 3: Commit-Vorschlag `docs: changelog for payload-attribution guard matching`

**Akzeptanz:** Eintrag vorhanden; keine Fakt-Behauptung zur Allow-Rule-Hypothese; kein Closing-Keyword.

## AC-Coverage

| AC | Erfüllt durch Task | Messbarer Nachweis |
|---|---|---|
| AC-01 Payload grantet ohne Sentinel | 2 | `test_payload_grants_without_sentinel`: exit 0 + Audit `role=git attribution=payload-field` |
| AC-02 Fälschung blockiert | 2 | `test_role_mismatch_is_rejected`: exit 2 `role mismatch`, Audit `class=role-mismatch` |
| AC-03 Keine Rechteausweitung | 2, 4 | `test_unknown_payload_role_fails_closed`: exit 2 am Mutations-Gate |
| AC-04 Fail closed bei leerem Rollenfeld | 2 | `test_fail_closed_empty_role_field_no_sentinel_grant`: exit 2, kein Sentinel-Grant |
| AC-05 Hook-/Rollen Feld-freie Provider | 1, 3 | Byte-Identität A/B gegen Golden, Render ohne Capability |
| AC-06 Capability-B stabil | 1, 3 | #1307-Regel; `tests/fixtures/slimming-golden/git.md` unverändert |
| AC-07 Destructive/Strict unverändert | 2, 4 | `test_destructive_ops_blocked_even_with_git_sentinel`, Strict-Exemption grün |
| AC-08 Template/Suite | 1, 3, 4 | 0 Literal-Token, `<tools>` exakt IC-5 C, `--validate` + A/B/C-Suite grün |

## Self-Review

- Jeder Task mappt auf genau eine Rolle: developer (1–3), tester (4, 5), validator (6), documenter (7); jedes AC ist mind. einem Task zugeordnet (Tabelle oben), jeder Task hat Test oder messbaren Bericht.
- `Files:`/`Interfaces:` vollständig mit Datei, Symbol, Signatur; keine Dateiüberlappung innerhalb einer Parallelgruppe: Task 1 ∥ 2 disjunkt; 3 ← 1; 4 ← 1,2,3; 5 unabhängig; 6 ← 4,5; 7 ← 3,6.
- `pipeline_stages` deckt die einzige `plan-driven`-Stage ab (`implement`, `config/role-defaults.yaml:2719-2724`) und zeigt auf Task 1.
- Keine Platzhalter (`TODO`, `TBD`, Auslassungspunkte), keine leeren Interfaces; alle neun ICs und acht ACs aus der Spec ohne Platzhalter übernommen.
- Kein neues Attributionsfeld/Grant erfunden; `GIT_PAYLOAD_ATTRIBUTION` nur Render-Ableitung; FAIL-CLOSED-GATE IC-1, OQ-1/OQ-3-PRE-ROLLOUT-GATE und OQ-4-CLOSURE-GATE explizit benannt; ADR-Hypothese als Hypothese geführt.

**Re-planning:** Nach Task 1 (Render-Varianten), Task 2 (Fail-closed), Task 4 (Pin-Pass), Task 5 (Payload-Capture) und Task 6 (OQ-4) Annahmen neu prüfen und Plan aktualisieren statt einfrieren. Anker wurden laut Spec bei `278ba54f` verifiziert, Task nennt `52bb8d9`; Anker vor Task 1 am aktuellen HEAD neu verifizieren. Fällt OQ-1/OQ-3 negativ aus → Re-Planung mit expliziter Harness-ID→Rolle-Zuordnung, kein Sentinel-Fallback.
