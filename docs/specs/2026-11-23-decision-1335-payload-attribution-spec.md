---
spec-id: SPEC-1335-PAYLOAD-ATTRIBUTION
title: "Payload-Attribution (#1210) als Allow-Matching-Quelle für die git-Rolle (#1335)"
status: APPROVED
approval: "User, 2026-11-23, Einzelentscheidung"
issue: "#1335"
based-on: SPEC-GUARD-ROLE-ATTRIBUTION-2026-11-11
head: 278ba54f
---

# Payload-Attribution für Allow-Matching (#1335) — Spec

> Status: APPROVED (User, 2026-11-23, Einzelentscheidung)

Bindende Nutzerentscheidung vom 23.11.: Die vorhandene #1210-Payload-Attribution wird zur **autoritativen Rollenquelle** für das Allow-Matching des Guards. Es wird **kein** neues Attributionsverfahren eingeführt. Diese Spec enthält Contracts und Abnahmekriterien, keine Implementierung.

## Problem / Ziel / Nicht-Ziele

**Problem (#1335):** `agents/1-generic/git.md` verlangt bei jedem `git`-Bash-Call die Sentinel-Zeile `#agent-meta:agent=git` als erste Zeile. Auf Claude Code ist diese Kommentarzeile ein eigener Sub-Command; enge Allow-Rules wie `Bash(git status *)` können dadurch nicht matchen (Hypothese laut Issue, live nicht deterministisch verifiziert). Der Guard wiederum hat die Attribution bereits: `_P_AGENT_TYPE` (`agent_type`) wird gelesen, und #1210 prüft es gegen den Sentinel — aber `_ROLE_ATTRIBUTION` wird nirgends als Rollenquelle konsumiert (nur `:451`/`:457` gesetzt, kein weiterer Bezug). Die Rollenflags werden weiterhin aus `DECLARED_AGENT` (Sentinel) gebildet.

**Ziel:** Auf Providern mit vertrauenswürdiger Payload-Attribution kommt die Rolle aus dem Harness-Payload (`agent_id` + `agent_type`), nicht aus modellschreibbarem Kommandotext. Der `git`-Agent benötigt dort keine Sentinel-Zeile mehr; der Guard behält die Rollenunterscheidung und bleibt fail-closed. Provider ohne entsprechende Capabilities behalten das exakte bisherige Verhalten.

**Nicht-Ziele:** Kein neues Payload-Feld, keine neue Capability, kein Secret/Token, kein Eingriff in Destructive-Gate, Branch-Guard oder Strict-Mode-`agent_id`-Logik, keine Änderung an `auto_commit`-Allowlist-Semantik (#1181), keine Änderung an Nicht-Git-Rollen, keine Implementierung in diesem Schritt.

**Re-Messung am lokalen Checkout (Branch `fix/decision-points-bundle-20261123`, HEAD `278ba54fa6f43376b93aa025d3efedf7a73e6463` = task-genannte `278ba54f`):**

| Anker (verifiziert) | Befund |
|---|---|
| `hooks/1-generic/orchestrator-guard-impl.sh:3` | v1.14.1; Changelog nennt #1210 nur als „cross-checks the self-declared sentinel“ |
| `:239-250`, `:254-258` | Single parse liest `agent_type` → `_P_AGENT_TYPE`; `AGENT_ID` gesetzt |
| `:379-386` | `HOOK_AGENT_ID_RELIABLE="{{AGENT_META_HOOK_AGENT_ID}}"`, `HOOK_ROLE_FIELD_RELIABLE="{{AGENT_META_HOOK_ROLE_FIELD}}"` |
| `:388-392` | Sentinel-Verwurf auf Main-Thread bei `hook-agent-id=true` |
| `:444-468` | #1210-Block: `_ROLE_ATTRIBUTION = "sentinel" \| "payload-field"`; Mismatch → exit 2; **Variable ungenutzt** |
| `:479-537`, `:1738`, `:1758-1769`, `:1784-1789` | Rollenflags/Allowlist/Grant und alle Matching-Gates lesen `DECLARED_AGENT`/Sentinel-Flags |
| `scripts/lib/hooks.py:570-578` | Beide Flags werden via `provider_has_capability(pc, ...)` gebacken (kein Providername) |
| `config/ai-providers.yaml:64-75` | Claude hat `hook-agent-id` (`:69`) **und** `hook-role-field` (`:75`); keine neue Capability nötig |
| `scripts/lib/agent_sync.py:567-608` | `_git_sentinel_scope_vars(pc)` kennt nur 2 Varianten (mit/ohne `hook-agent-id`) |
| `agents/1-generic/git.md:26-35`, `:41-46`, `:97-101`, `:163` | Sentinel-Pflicht, drei Beispielblöcke mit Literal, `<tools>`-Zeile via `{{GIT_SENTINEL_BASH_RULE}}` |
| `tests/test_hook_single_parse.py:205-286` | #1210-Matrix; `:248-255` testet „role field leer → Sentinel-Fallback“ (wird hier geändert) |
| `tests/test_git_sentinel_gh_scope.py:195-198`, `:201-219` | 3 Literal-Sentinels im Render; Byte-Identität ohne Capability |
| `tests/fixtures/slimming-golden/git.md:32,36,44,100,163` | Golden für die `hook-agent-id`- Variante (gh-Ausnahme); bleibt unverändert |
| `docs/specs/2026-11-11-guard-role-attribution-spec.md:139`, `:102-104` | R1 „role field alone never GRANTS“ (OQ-3) ist durch diese Entscheidung ersetzt; Classifier-Abhängigkeit dort explizit unverifiziert |

## Interface Contracts

| ID | Datei:Symbol | Signatur / Typ | Rolle & Fehlerpfad |
|---|---|---|---|
| IC-1 | `hooks/1-generic/orchestrator-guard-impl.sh:_P_AGENT_TYPE` / `_ROLE_ATTRIBUTION` (`:239-250`, `:444-468`) | `_P_AGENT_TYPE: str` (normalisiert lowercase); `_ROLE_ATTRIBUTION: "sentinel" \| "payload-field"` | Bestehende #1210-Lese- und Cross-Check-Logik unverändert. Neu: `_ROLE_ATTRIBUTION == "payload-field"` wird zur Rollenquelle. Mismatch (Sentinel ≠ Payload-Rolle) bleibt exit 2 + Audit (fail closed). |
| IC-2 | `hooks/1-generic/orchestrator-guard-impl.sh` Rollenauflösung (`:479-537`, `:1738`, `:1758-1769`, `:1784-1789`) | `EFFECTIVE_ROLE: str` (lowercase) = Payload-Rolle bei IC-1 `payload-field`, sonst Sentinel-Rolle; `IS_GIT_SENTINEL`, `IS_ORCH_SENTINEL`, `IS_ALLOWLIST_SENTINEL`, `IS_GRANT_SENTINEL: 0\|1` | Die vier Flags und alle Gates lesen `EFFECTIVE_ROLE` statt `DECLARED_AGENT`. Namen bleiben aus Kompatibilitätsgründen, Bedeutung ist „effective role“. Bei `payload-field` ist `DECLARED_AGENT` **keine** Grant-Quelle. Unbekannte nicht-leere Rolle → exit 2 (fail closed). Capability true, `agent_id` nicht leer, `agent_type` leer → **kein** Sentinel-Fallback, kein Delegate-Grant, exit 2 an den Matching-Gates. Main-Thread (`agent_id` leer) und Capability false → exakt bisheriger Pfad. |
| IC-3 | `hooks/1-generic/lib/hook_common.sh:hook_audit_log_append` (Aufruf `:459-464`, `:559-578`) | `hook_audit_log_append(log_path: str, line: str) -> None` | Keine Signaturänderung. Audit-Zeile erhält `attribution=payload-field\|sentinel`; Reject-Zeile behält `decision=rejected class=role-mismatch`. Redaktion/600/Rotation unverändert. |
| IC-4 | `scripts/lib/hooks.py:570-578` | `source_content.replace("{{AGENT_META_HOOK_AGENT_ID}}", "true"\|"false")`, analog `{{AGENT_META_HOOK_ROLE_FIELD}}` | Unverändert; keine neue Capability. Unsyncte Quellkopie (literal placeholder) zählt als `false` → Sentinel-Pfad. |
| IC-5 | `scripts/lib/agent_sync.py:_git_sentinel_scope_vars(pc: dict) -> dict[str, str]` (`:567-608`, Verbrauch `:690`) | Reine Funktion, `provider_has_capability(pc, ...)`; Keys `GIT_SENTINEL_SCOPE_BLOCK`, `GIT_SENTINEL_BASH_RULE` unverändert | Drei statt zwei Varianten: **(A)** ohne `hook-agent-id`: beide Werte byte-identisch heute (`""` / „always prefixed …“). **(B)** `hook-agent-id` ja, `hook-role-field` nein: beide Werte byte-identisch #1307 (gh-Ausnahme, `git` behält Sentinel). **(C)** beide ja: exakte Strings im Block nach dieser Tabelle. |
| IC-6 | `scripts/lib/agent_sync.py:_build_provider_vars` + `scripts/lib/consistency/placeholders.py:162-165` | `GIT_PAYLOAD_ATTRIBUTION: "true"\|"false"` = `"true" if (provider_has_capability(pc, "hook-agent-id") and provider_has_capability(pc, "hook-role-field")) else "false"`; registriert als gültiger Platzhalter | Neue Template-Variable, keine neue Capability. Reine Ableitung aus `pc`, kein Providername. |
| IC-7 | `agents/1-generic/git.md:26-35`, `:41-46`, `:97-101`, `:163` | `{{#if GIT_PAYLOAD_ATTRIBUTION}}…{{else}}<bestehender Text>{{/if}}` | Variante C: Schritt 0, alle drei Beispielblöcke und `<tools>`-Zeile ohne `#agent-meta:agent=git`; kein Literal-Token im gerenderten Output. Variante A/B: Byte-Identität zum heutigen Render (Golden #1307 bleibt gültig). |
| IC-8 | `config/ai-providers.yaml:64-75` | Capability-Liste (unverändert) | `hook-agent-id` + `hook-role-field` bleiben die einzigen Schalter; keine Provider-Verzweigung. |
| IC-9 | `tests/test_orchestrator_guard_hook.py`, `tests/test_hook_single_parse.py:202-286`, `tests/test_git_sentinel_gh_scope.py`, `tests/fixtures/slimming-golden/git.md` | pytest, `-> None` | Matrix für A/B/C; `:248-255` wird von „Fallback“ auf „fail closed“ umgestellt; Golden B bleibt, Golden C neu. Golden-/Pin-Rebaselines sind von dieser Freigabe für genau diese Dateien gedeckt; andere Pins brauchen erneute Freigabe. |

Exakte Strings für Variante C (IC-5), Python-Literale — keine Escape-Zeichen im gerenderten Markdown nötig:

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

## Datenfluss

1. **Input (Sync-Zeit):** `config/ai-providers.yaml` → `provider_has_capability()` → gebackene Flags (IC-4) und Provider-Variablen (IC-5/IC-6) → generiertes `.claude/agents/git.md`.
2. **Input (Laufzeit):** PreToolUse-Payload (`tool_name`, `tool_input.command`, `cwd`, `agent_id`, `agent_type`) + `auto-commit-allowlist.json` + `project.yaml`.
3. **Transformation:** Single parse → lowercase → Capability-Gate → `_ROLE_ATTRIBUTION` → `EFFECTIVE_ROLE` → Rollenflags → Allowlist-/Grant-Lookup → Destructive-/Strict-/Mutation-/Grant-Gates. Sentinel wird bei `payload-field` nur noch gelesen (Mismatch-Erkennung/Audit), nie als Grant-Quelle.
4. **Output:** exit 0 (Call läuft) oder exit 2 + stderr-Begründung; Audit-Zeile mit `attribution=`; generierte Agent-Datei und Golden-Fixtures.
5. **Persistenz:** `.claude/hooks/.guard-audit.log` (bisher), `.claude/agents/git.md` (bisher), Golden-Fixtures im Repo. Keine neue Persistenz.

## Acceptance Criteria

1. **AC-01 — Payload grantet ohne Sentinel (IC-1, IC-2, IC-3):** Gegeben Flags `true/true`, `agent_id="subagent-1"`, `agent_type="git"`; wenn `Bash("git add -- f")` ohne Sentinel ausgeführt wird, dann exit 0 und die Audit-Zeile enthält `role=git attribution=payload-field`.
2. **AC-02 — Fälschung blockiert (IC-1, IC-3):** Gegeben `true/true`, `agent_type="developer"`; wenn der Call `#agent-meta:agent=git\ngit add -- f` sendet, dann exit 2 mit `role mismatch`, kein Grant, Audit `decision=rejected class=role-mismatch`.
3. **AC-03 — Keine Rechteausweitung (IC-2):** Gegeben `true/true`, `agent_type="developer"`; wenn `git add -- f` **ohne** Sentinel kommt, dann exit 2 durch das Mutations-Gate; Nicht-Git-Rollen bleiben unverändert.
4. **AC-04 — Fail closed bei leerem Rollenfeld (IC-2):** Gegeben `true/true`, nicht-leeres `agent_id`, `agent_type` leer/abwesend; wenn `git add -- f` **mit** Sentinel kommt, dann exit 2 ohne Sentinel-Grant (ersetzt `test_role_field_empty_falls_back_to_sentinel`).
5. **AC-05 — Hook-/Rollen Feld-freie Provider (IC-4, IC-5 A/B, IC-7, IC-9):** Gegeben `hook-role-field=false` oder literal placeholder; wenn derselbe sentinelbewehrte Call wie heute läuft, dann identisches Ergebnis (exit 0) und gerendertes `git.md` byte-identisch zum Golden (B bzw. A).
6. **AC-06 — Capability-B true bleibt stabil (IC-5 B, IC-9):** Gegeben `hook-agent-id=true`, `hook-role-field=false`; wenn `git.md` gerendert wird, dann gilt unverändert die #1307-Regel (gh-only ohne Sentinel, `git` mit Sentinel) und `tests/fixtures/slimming-golden/git.md` ist unverändert.
7. **AC-07 — Destructive/Strict unverändert (IC-2):** Gegeben `true/true`, `agent_type="git"`; wenn `git reset --hard` gesendet wird, dann exit 2 mit `user approval` (bestehender Test grün); die `agent_id`-basierte Strict-Entscheidung ist unverändert.
8. **AC-08 — Template/output & Suite (IC-5 C, IC-6, IC-7, IC-9):** Gegeben beide Capabilities true; wenn `git.md` gerendert wird, dann kommt `#agent-meta:agent=git` **0-mal** im Output vor und die `<tools>`-Zeile entspricht exakt IC-5 C; `python3 scripts/sync.py --validate` und die Testsuiten (A/B/C-Matrix) sind grün.

## Offene Fragen + Risiken

- **OQ-1 (Mapping):** Der exakte `agent_type`-Wert des `git`-Subagenten ist im Repo nicht festgehalten (Erwartung: `git`, analog `subagent_type`); die frontmatter `name: template-git` ist nicht automatisch der Payload-Wert. Eskalation: einen echten PreToolUse-Payload eines dispatched `git`-Subagenten erfassen. Bis dahin gilt: nicht-leere unbekannte Rolle → exit 2, **kein** Sentinel-Fallback.
- **OQ-2 (Provenienz):** Ob ein Subagent `agent_type` durch Kind-Spawn mit `subagent_type: git` beeinflussen kann, ist nicht verifiziert (`docs/analysis/2026-11-20-agent-id-evidence.md:57-59`). Die Entscheidung ist bindend; Cross-Check und Fail-closed bleiben daher zwingend. Eskalation: Security-Prüfung/live probe, kein Blockieren dieser Spec.
- **OQ-3 (Vollständigkeit):** Ob `agent_type` auf allen legitimen Spawn-Pfaden (custom agents, `--agent`) gesetzt ist, ist nicht verifiziert (`docs/analysis/2026-11-11-hook-api-ask-permission.md:81`). Falls nein, blockt AC-04 diese Pfade; Eskalation: explizite Harness-ID→Rolle-Zuordnung statt Sentinel-Fallback.
- **OQ-4 (Issue-Evidenz):** Issue #1335 markiert die Allow-Rule-Nicht-Match-Hypothese selbst als „NOT verified“. Die Spec stützt sich auf die Nutzerentscheidung, nicht auf den Beweis; vor Issue-Closure deterministic check (`/permissions` → „Recently blocked“) durchführen.
- **R-1:** Sentinel bleibt im Kommandotext lesbar (Anchor-Regex, kein Interpreter). Solange Variante A/B aktiv ist, bleibt er Convention boundary — bewusst kein Security-Boundary-Upgrade. Model-writable Texte dürfen nie Grants erzeugen; `eval`/Indirektion bleibt Convention boundary.
- **ADR (eingebettet, adr.github.io-Format; Separate ADR-Datei durch Single-File-Scope ausgeschlossen):** **Kontext** — #1210 liefert Harness-Rollenattribution, wurde aber nur als Cross-Check genutzt; #1335 verlangt Entfernung der Sentinel-Zeile. **Entscheidung** — Payload-Attribution wird autoritative Rollenquelle, Sentinel nur noch Widerspruchs-/Audit-Signal; Rückfall ausschließlich auf Providern ohne die Capabilities. **Konsequenzen** — enge Allow-Rules matchen ohne Kommentarzeile; fail-closed bei fehlender Attribution; Golden-Rebaseline in IC-9; OQ-1..3 bleiben Beobachtungspflicht.

**Coverage-Checkliste:** Pflichtabschnitte vorhanden ✓ · IC-1..IC-9 ohne Platzhalter, Typen und Fehlerpfade benannt ✓ · AC-01..AC-08 in Gegeben/Wenn/Dann, je mindestens einem IC zugeordnet ✓ · Trace-Anker gesetzt ✓.

## Trace-Anker: spec-id: SPEC-1335-PAYLOAD-ATTRIBUTION
