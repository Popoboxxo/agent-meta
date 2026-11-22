---
status: APPROVED
date: 2026-11-19
approval: "User-Freigabe 2026-11-19 (E-17 approved + Roadmap approved — volle Umsetzung 2.3)"
---

# Worker-Control-Capability (PR B / P12 / E-17) — Spec

> Status: APPROVED (User-Freigabe 2026-11-19 — „E17 ist nun Approved! Machen Masterplan roadmap auch! Approved Go! Volle Umsetzung!" inkl. Rebaseline, PR, MERGE; wortgleich: User-Freigabe 2026-11-19 (E-17 approved + Roadmap approved — volle Umsetzung 2.3))
> Datum: 2026-11-19 | Entscheidung: E-17 (§5.5 Empfehlung 2/3/4) | Roadmap: `docs/plans/2026-11-15-master-roadmap.md` P12 / PR 2.3, `:3`, `:43`, `:181`, `:285` | Issues: #1176 (erweitert), O1, O4, O11-Teil | Klasse: **M**
> Branch: `feat/worker-control-capability` (HEAD `7dc9e88`) | Quellen (verifiziert): `docs/analysis/2026-11-15-fable-orchestration-rollout-audit.md` §5.3 `:195`, §5.4 `:202`, §5.5 `:208-210`; `docs/superpowers/plans/2026-11-11-phase-d-guards-hooks.md` (DRAFT) `:60-62`, `:187-190`; `docs/specs/2026-11-15-git-trailer-contract-spec.md:93`

Diese Spec setzt ausschließlich freigegebene Quellen um. Es werden keine neuen Entscheidungen getroffen, keine REQ-IDs erfunden und keine offenen Fragen erzeugt.

## Problem / Ziel / Nicht-Ziele

**Problem**

- #1176 („Orchestrator endet vor Hintergrund-Agenten"): Gegenmaßnahme ist heute reine Prosa plus Claude-Tools. Für Opencode/Gemini/Codex/Kimi fehlt das Tool-Äquivalent bzw. Mapping; der Zusatz „(where granted)" kaschiert die Lücke, statt sie zu gaten (Audit `:135`, `orchestrator.md:280`).
- Worker-Control-Test existiert nur für Claude; es gibt keinen Test „Prosa nennt nur Tools, die im FM stehen" (Audit `:156`).
- Provider-Literale (`SendMessage`, `TaskStop`, `run_in_background`) stehen im generischen `orchestrator.md` und gelangen in Opencode/Gemini; `strip-claude-lines` entfernt nur Zeilen mit „Claude" (Audit `:152`).
- Capability-Drift: `primary-role-tools` nur Claude, `primary-role` nur Opencode — zwei Provider-Keys für dieselbe Rolle (Audit `:150`; Readseite `scripts/lib/provider_transform.py:743`, Whitelist-Kommentare `config/provider-tools.yaml:19-20`).
- `PROGRESS_CHAT_PUSH_ENABLED` ist an `hooks` gekoppelt statt an ein Messaging-Tool; Gemini erhält dadurch `SendMessage`-Prosa (O4, Audit `:169`; `scripts/lib/config.py:2615-2617`, `scripts/lib/agent_sync.py:572`).
- Continue degradiert unter `subagent` still (ohne Finding) (Audit `:154`); `primary` ist für Claude/Kimi nur Prosa ohne Entry-Mechanismus (Audit `:171`).

**Ziel**

- Neue Capability `worker_control_tools` in `config/provider-capabilities.yaml`, als Ersatz für `primary-role-tools` (E-17, §5.3, §5.5 Empfehlung 2).
- #1176 provider-übergreifend beheben: Prosa wird über ein abgeleitetes Flag gegated statt „where granted"; pro Provider nur die Tools nennen, die im Frontmatter stehen.
- Continue unter `subagent`: WARNING-Finding, **kein** Clamp auf `primary` (E-17, §5.5 Empfehlung 3).
- `primary` für Claude/Kimi: mechanischer Rollout erst nach Runtime-Evidenz; bis dahin im Check als „prose-only" melden (E-17, §5.5 Empfehlung 4).
- #1172 in 2.3 als **reine Doku** (E-18); der Trailer-Contract bleibt bei P37, die 2.3-Prosa verweist darauf statt ihn zu duplizieren (E-19).

**Nicht-Ziele**

- Kein mechanisches Ausrollen von `primary` für Claude/Kimi (kein Claude-`agent`-Setting), keine Runtime-Probe in diesem PR.
- Keine Permission-Regel für #1172 (E-18: erst W4 bei positiver Machbarkeit); #1172/PR 0.9 betrifft hier ausschließlich Doku.
- Keine Implementierung des Trailer-Contracts, keine Config-Key-Einführung `commit.trailers`, kein Git-Agent-PR — das gehört P37 / PR 0.9 (E-19, `docs/specs/2026-11-15-git-trailer-contract-spec.md:93`); dieser PR verweist nur darauf.
- Kein Gemini-Dispatch (O2 / PR C / P13) und kein Opencode-Gate (O3/O13 in #1249/#1256/#1257-Kette).
- Kein erneutes Spezifizieren/Implementieren von 0.4 (`config/role-defaults.yaml:11` plan→default + Test ist mit Commit `c73319cb` bereits umgesetzt).
- Keine Produktionsdatei, kein Template, kein Hook, keine Config, keine Golden-Änderung durch diese Spec selbst — Spec only.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

**Technische Randbedingungen (alle ICs):** Python 3.9, nur Stdlib + PyYAML. Provider-agnostisch: **niemals** `if provider == "Name"` im Syncer — alle Verzweigungen laufen über Capability-Keys/Config-Flags (AGENTS.md, `provider-agnostic`-Skill). Neue Keys sind datengetrieben und folgen der Conservative-default-Regel (unverifiziert ⇒ leer/false, nie spekulativ yes).

**IC-1 — Capability-Schlüssel und Provider-Mapping** — `config/provider-capabilities.yaml`, Block `capabilities:`, neuer Key `worker_control_tools: [name, ...]`. Mapping exakt wie freigegeben (§5.3 `:195`):

| Provider | `worker_control_tools` |
|---|---|
| Claude | `["SendMessage", "TaskStop"]` |
| Codex | `["send_input", "close_agent", "wait_agent"]` |
| Gemini | `["send_message"]` |
| alle übrigen registrierten Provider | `[]` (konservativer Default; kein neues Tool-Wissen) |

- Signatur/Form: Liste von Tool-Namen, analog `native_agent_tools` (`:125`, `:241`, `:510`). Jeder registrierte Provider muss den Key explizit tragen; Fehlt er, greift der konservative Leer-Default und der Invariantentest meldet den Fehler (Muster `tests/test_topology_capability_invariant.py:81`).
- Ersetzung: `worker_control_tools` ersetzt `primary-role-tools` als Quelle der Primary-Role-Extra-Tools. Bestehende Lesestelle `scripts/lib/provider_transform.py:743` (`_with_native_tools(_tools, spec.get('primary-role-tools'))`) und Dokumentation `:397-401` werden auf den neuen Capability-Key umgestellt; `primary-role-tools` in `config/ai-providers.yaml`-Transform-Specs und die Kommentare in `config/provider-tools.yaml:19-20` werden entsprechend aktualisiert/entfernt. Tool-Namen bleiben über `_validate_tools_against_whitelist` (`provider_transform.py:745`) gegen die bestehende Whitelist validiert — davon abweichende Namen werden als WARNING geloggt und verworfen (kein harter Abbruch).

**IC-2 — Resolver / abgeleitetes Render-Flag** — `scripts/lib/config.py` `_build_core_variables` (neben `PROGRESS_CHAT_PUSH_ENABLED`, `:2607-2617`) und `scripts/lib/agent_sync.py` (Provider-Override-Block `:568-572`, `:889`).
- Aus `worker_control_tools` je aktivem Provider wird ein boolesches Render-Flag abgeleitet (Benennung nach `<VAR>_ENABLED`-Konvention, z. B. `WORKER_CONTROL_ENABLED`): `true` genau dann, wenn der aktive Provider mindestens ein Worker-Control-Tool deklariert; sonst `false`.
- Prosa-Gate ist **nicht** mehr an `hooks` gekoppelt (O4): `PROGRESS_CHAT_PUSH_ENABLED` bleibt vom Messaging-Tool-Capability-Key abgeleitet, nicht von `provider_hooks_supported`. Kein Provider-Name im Pfad, nur Capability-Lookup.
- Fehlerpfade: kein Wurf; fehlender/leerer Key ⇒ Flag `false` ⇒ Prosa wird nicht gerendert (fail-safe). Placeholder-Registrierung in `scripts/lib/variables.py`, Fallback-Dict `scripts/lib/standalone.py` und Whitelist `scripts/lib/consistency/placeholders.py` nachziehen, sonst Unknown-Placeholder-Fehler (Muster `config.py`-Spec `docs/specs/2026-11-15-git-trailer-contract-spec.md:83`).

**IC-3 — Prosa im Orchestrator-Template** — `agents/1-generic/orchestrator.md`.
- `:240` (Sync-Call-Vertrag, `SendMessage`/`TaskStop`), `:270-272` (`{{#if PROGRESS_CHAT_PUSH_ENABLED}}`-Block, `SendMessage(to:"main")`) und `:280` („Hard interrupt / Wait strategy (#1176)", `TaskStop … (where granted)`): Worker-Control-Sätze werden in `{{#if WORKER_CONTROL_ENABLED}} … {{/if}}` geklemmt und nennen ausschließlich die Tools aus `worker_control_tools` des aktiven Providers.
- „(where granted)" entfällt; stattdessen gilt das Flag als Gate. Claude-Toolliterale dürfen im generischen Template nur noch innerhalb dieses Gats stehen und müssen bei deaktiviertem Flag vollständig aus dem Render verschwinden (O11-Teil).
- Fehlerpfad: ungültiges/ unbekanntes Tool ⇒WARNING via Whitelist-Validierung (IC-1), kein Render-Abbruch. Versions-/Frontmatter-Konvention des Templates gemäß `conventions`-Skill beibehalten.

**IC-4 — Continue-WARNING-Finding** — `scripts/lib/consistency/topology.py` (Check-Output, Quick-Win O5) und `agents/1-generic/orchestrator.md` (gerenderte Prosa).
- Landet der Fail-Safe für Continue auf `subagent` (`subagent_dispatch: false`, `topology_support.subagent: false`, `topology_degrade.subagent: sequential-text`), ist ein **WARNING**-Finding zu emitsieren: „subagent unsupported → sequential-text degradation". Kein Clamp auf `primary` (E-17, §5.5 Empfehlung 3); `primary` wäre für Continue ebenfalls nur Prosa.
- Für Claude/Kimi: `primary`-Zelle im Check als „prose-only" melden, solange keine Runtime-Evidenz vorliegt (E-17, §5.5 Empfehlung 4). Kein Setting wird gesetzt.
- Fehlerpfad: Check-Output ausschließlich über WARNING; `sync.py --validate` bleibt bei WARNING Exit 0, ERROR (mit `require-runtime-gate`) Exit 1. Kein Still-Degrade ohne Finding.

**IC-5 — #1172-Doku (nur Doku, E-18)** — `rules/1-generic/use-orchestrator.md` Abschnitt `## Git Delegation` (`:85-93`), `agents/1-generic/orchestrator.md` §7 BARRIER (`:258-276`), `agents/1-generic/git.md` (`## 4. Operation` `:52`, Commit-Format `:134-136`).
- Merge-Muster-Text: Merges freigegebener PRs werden vom Main Chat direkt an `git` dispatched; Pfad orchestrator → git wurde 2026-11-06 vom Claude-Code-Auto-Mode-Classifier als „Merge Without Review" blockiert (Ursache außerhalb des Repos, nicht reproduziert); Pfad bleibt Fallback, Verweis auf #783. `#1172` und `#783` stehen je genau einmal je Template (Muster Phase-D-Plan `:187-190`). Für `use-orchestrator.md` außerhalb der `AUTO_COMMIT_ENABLED`/`ROLE_GIT_ACTIVE`-Zweige einfügen (Phase-D-Plan `:189`), sonst fehlt der Satz im gerenderten Output.
- Keine Permission-Regel, kein Hook, kein Setting in diesem PR.

**IC-6 — P37-Verweis statt Duplikat** — `agents/1-generic/git.md:140` („Commit trailers (issue #1168)") bleibt die Implementierungsstelle von P37 (`docs/specs/2026-11-15-git-trailer-contract-spec.md:93`). Die 2.3-Prosa nennt den Contract nur als Verweis auf P37/`docs/specs/2026-11-15-git-trailer-contract-spec.md` und `#1168`/`#1247`; sie dupliziert weder `commit.trailers`-Regeln noch Rangfolge-Text. Kein Eingriff in `git.md:140` selbst durch diesen PR (außer IC-5 Doku-Satz).

## Datenfluss

```
config/provider-capabilities.yaml (capabilities.<Provider>.worker_control_tools)
  + config/provider-tools.yaml (Whitelist: Tool-Namen gültig)
        │
        ▼
Resolver: scripts/lib/config.py::_build_core_variables
          → WORKER_CONTROL_ENABLED = any(worker_control_tools[aktive Provider])
          → PROGRESS_CHAT_PUSH_ENABLED ← Messaging-Tool-Capability (NICHT hooks)
        │  (scripts/lib/agent_sync.py: Provider-Override, Variablen-Fallbacks,
        │   scripts/lib/variables.py / standalone.py / consistency/placeholders.py)
        ▼
Render: scripts/lib/provider_transform.py::_with_native_tools
        → Primary-Role-FM: Tools aus worker_control_tools (statt primary-role-tools)
        → Whitelist-Validierung (WARNING bei unbekanntem Tool)
        ▼
Prosa-Gate: agents/1-generic/orchestrator.md {{#if WORKER_CONTROL_ENABLED}} … {{/if}}
        → gerenderte .claude/agents/orchestrator.md (bzw. je Provider-Ziel)
        → {{#if ROLE_GIT_ACTIVE}} Merge-Satz (#1172, nur Doku, IC-5)
        → P37-Verweis in git.md-Prosa (IC-6, kein Duplikat)
        ▼
Check/Output: scripts/lib/consistency/topology.py
        → WARNING: Continue subagent-Degrade, Claude/Kimi primary „prose-only"
        → sync.py --validate: WARNING Exit 0 / ERROR Exit 1
        ▼
Persistenz: keine DB. Artefakte = gerenderte Agent-Dateien + Rebaseline-Artefakte
            (Goldens, ac01-baseline/hashes.json, context-hashes.json,
             generated-file-hashes.json, tests/test_context_budgets.py-Ceilings)
```

## Acceptance Criteria

1. **Gegeben** ein aktivier Provider mit `worker_control_tools`, **wenn** `python3 scripts/sync.py` läuft, **dann** enthält das gerenderte `orchestrator.md` genau die Tool-Namen aus `capabilities.<Provider>.worker_control_tools` und keine anderen Worker-Control-Tool-Namen (Abgleich gegen `tests/test_orchestrator_worker_report_contract.py`, erweitert um den Tool-Mention⊆FM-Check). *Deckt IC-1, IC-3.*
2. **Gegeben** Claude, **wenn** gerendert wird, **dann** stehen `SendMessage` und `TaskStop` im FM und in der gegateten Prosa; **gegeben** Codex ⇒ `send_input`, `close_agent`, `wait_agent`; **gegeben** Gemini ⇒ `send_message`. *Deckt IC-1, IC-3.*
3. **Gegeben** ein Provider ohne `worker_control_tools` (z. B. Opencode/Continue/Copilot/Mammouth/ZCode/Kimi), **wenn** gerendert wird, **dann** enthält die Prosa keinen `SendMessage`/`TaskStop`-Hinweis und das Flag ist `false`; der Satz „(where granted)" kommt nirgends mehr vor. *Deckt IC-2, IC-3.*
4. **Gegeben** `PROGRESS_CHAT_PUSH_ENABLED`, **wann** immer der aktive Provider ein Messaging-Tool deklariert, **dann** ist das Flag `true` — auch ohne Hook-Support; ein rein an `hooks` gekoppelter Wert existiert nicht mehr. *Deckt IC-2 (O4).*
5. **Gegeben** Continue mit Fail-Safe auf `subagent`, **wenn** der Konsistenz-Check läuft, **dann** erscheint genau ein WARNING-Finding „subagent unsupported → sequential-text degradation"; es gibt keinen Clamp auf `primary` und kein Still-Degrade ohne Finding. *Deckt IC-4.*
6. **Gegeben** Claude oder Kimi als `primary`, **wenn** der Check läuft, **dann** wird die `primary`-Zelle als „prose-only" gemeldet; es wird kein `primary`-Setting mechanisch gesetzt. *Deckt IC-4.*
7. **Gegeben** die drei Doku-Zieldateien, **wenn** gerendert wird, **dann** enthält jede genau einen Treffer für `#1172` und einen für `#783` im Merge-Absatz; `#1172` betrifft ausschließlich Doku — kein Hook, kein Setting, keine Permission-Regel in 2.3. *Deckt IC-5 (E-18).*
8. **Gegeben** die 2.3-Prosa mit Trailer-Thema, **wenn** `git.md` geprüft wird, **dann** verweist sie auf P37 / `docs/specs/2026-11-15-git-trailer-contract-spec.md` und `#1168`/`#1247`, ohne `commit.trailers`-Rangfolge oder Trailer-Regeln zu duplizieren; `git.md:140` bleibt unverändert. *Deckt IC-6 (E-19).*
9. **Gegeben** alle Änderungen dieses PRs, **wenn** `python3 scripts/sync.py --validate` läuft, **dann** Exit 0 (Warnungen erlaubt), und es gibt **eine** Rebaseline (AC, G, H, B) als letzten Commit — keine zweite. *Deckt IC-1…IC-6, Rebaseline-Abschnitt.*
10. **Gegeben** der Syncer-Quellcode nach diesem PR, **wenn** er auf Provider-Namen geprüft wird, **dann** gibt es kein `if provider == "Name"` in den geänderten Pfaden; alle Verzweigungen sind Capability-Key-basiert. *Deckt IC-1, IC-2.*

## Offene Fragen + Risiken

**Offene Fragen: keine.** Alle relevanten Entscheidungen sind vom Nutzer am 2026-11-19 freigegeben: E-17 (Capability, Continue-WARNING, Claude/Kimi prose-only), E-18 (#1172 nur Doku), E-19 (Trailer konfigurierbar, P37, Git-Agent-PR zuerst) sowie §5.5 Empfehlungen 2–4 („ENTSCHIEDEN wie Empfehlung", Roadmap `:285-287`). 0.4 ist mit `c73319cb` bereits umgesetzt und nicht Teil dieser Spec.

**Risiken (mit bereits festgelegter Handhabung):**

- Rebaseline-Drift bei Goldens (`topology`/`compact`/`slimming`) und Hash-Dateien — Handhabung: eine einzige Rebaseline am PR-Ende (siehe Abschnitt Rebaseline).
- Consumer-Projekte sehen beim nächsten `update-meta` einen Orchestrator-Diff — Handhabung: CHANGELOG-Eintrag im selben PR (Audit `:202`).
- Tool-Whitelist: nicht gelistete Tool-Namen werden nur als WARNING verworfen — Handhabung:testseitig prüfen, dass Mapping-Namen in `config/provider-tools.yaml` stehen (AC 1/2).
- Continue-WARNING hängt mit O5 (P10/PR A) zusammen — Handhabung: identisches Finding, E-17-konform; keine zweite, abweichende Meldung erzeugen.
- Runtime-Verifikation von `primary` für Claude/Kimi steht aus — Handhabung: prose-only im Check bis Probe (E-17/§5.5 Empfehlung 4), keine spekulative Aktivierung.

## Nachgelagerte Tasks (File-Ownership)

Die Blöcke sind an den `planner` gerichtete Ownership-Vorschläge, keine Implementierung in dieser Spec.

**Task B1 — Capability & Resolver.**
`Files:` Modify `config/provider-capabilities.yaml`, `config/provider-tools.yaml`, `config/ai-providers.yaml` (Transform-Specs), `scripts/lib/provider_transform.py` (`:397-401`, `:743`), `scripts/lib/config.py` (`:2607-2617`), `scripts/lib/agent_sync.py` (`:568-572`, `:889`), `scripts/lib/variables.py`, `scripts/lib/standalone.py`, `scripts/lib/consistency/placeholders.py`. Test: Create/Modify `tests/test_topology_capability_invariant.py`, `tests/test_provider_agnostic_dispatch.py` (AC-01).
`Interfaces:` Consumes IC-1, IC-2. Produces `worker_control_tools` + `WORKER_CONTROL_ENABLED`, `primary-role-tools` ersetzt.

**Task B2 — Prosa-Gate & Orchestrator-Template.**
`Files:` Modify `agents/1-generic/orchestrator.md` (`:240`, `:270-272`, `:280`). Test: Modify `tests/test_orchestrator_worker_report_contract.py` (Zeilen 90-99 prüfen heute schon `SendMessage`/`TaskStop`), Create Tool-Mention⊆FM-Test.
`Interfaces:` Consumes IC-3, IC-2-Flag. Produces gegatete, provider-agnostische Prosa ohne „where granted".

**Task B3 — Continue/primary Findings.**
`Files:` Modify `scripts/lib/consistency/topology.py`. Test: Modify/Create TestWARNING-Finding (Continue subagent, Claude/Kimi primary prose-only).
`Interfaces:` Consumes IC-4, E-17/§5.5(3)/(4). Produces WARNING-Check-Output (Exit 0 bei WARNING).

**Task B4 — #1172-Doku (E-18, nur Doku).**
`Files:` Modify `rules/1-generic/use-orchestrator.md` (`## Git Delegation`, `:85-93`), `agents/1-generic/orchestrator.md` (§7, `:258-276`), `agents/1-generic/git.md` (`## 4. Operation` `:52`, Commit-Format `:134-136`). Test: Create `tests/test_merge_pattern_docs.py` (`test_merge_pattern_in_three_templates`, Muster Phase-D-Plan `:187`).
`Interfaces:` Consumes IC-5. Produces `#1172`/`#783` je genau 1× je Template; keine Permission-Regel.

**Task B5 — P37-Verweis + Rebaseline.**
`Files:` Modify Prosa-Stellen mit Trailer-Thema (Verweis auf `docs/specs/2026-11-15-git-trailer-contract-spec.md`, `#1168`/`#1247`); **keine** Änderung an `agents/1-generic/git.md:140` (P37-Implementierungsstelle). Rebaseline aller unten genannten Artefakte als letzter Commit.
`Interfaces:` Consumes IC-6, §5.4. Produces P37-Verweis ohne Contract-Duplikat + eine Rebaseline.

## TDD-Hinweise

- Reihenfolge: zuerst Tests (rot) — invariant für `worker_control_tools`, Tool-Mention⊆FM, Continue-WARNING, Merge-Pattern-Doku — dann Implementierung (grün), dann `python3 scripts/sync.py --validate` (Exit 0).
- Bestehende Hilfsmittel wiederverwenden: `tests/test_orchestrator_worker_report_contract.py` (Render-Hilfsmittel, `:90-99`), `tests/test_merge_pattern_docs.py` (Muster Phase-D-Plan `:187`), `tests/test_topology_capability_invariant.py` (Capability-Invarianten-Muster `:81`), `tests/test_context_budgets.py` (B-Ceilings).
- Kein Wall-Clock-/Netzwerk-Test; reine Render-/Config-/Check-Assertions.
- Jeder Testbeeld muss eine der AC 1–10 abdecken; keine AC ohne Test.

## Rebaseline (einmal, am Ende)

Eine einzige Rebaseline als letzter Commit des PRs (Roadmap `:181`, `:43`: AC, G, H, B):

- **G** — `tests/fixtures/topology-golden/orchestrator*.md`, `tests/fixtures/compact-golden/orchestrator*.md`, `tests/fixtures/slimming-golden/orchestrator*.md` (Audit `:202`).
- **H** — `ac01-baseline/hashes.json`, `context-hashes.json`, `generated-file-hashes.json`.
- **AC** — AC-01-Hashes (mit H).
- **B** — `tests/test_context_budgets.py`-Ceilings.
- Kein SA-, Rules- oder Allowlist-Anteil (E-15/E-12 betreffen andere PRs); keine zweite Rebaseline.

## Commit-/Trailer-Konvention

- Conventional Commits, Englisch, ≤72 Zeichen, Imperativ (AGENTS.md). Branch-Guard: Feature-Branch `feat/worker-control-capability`, kein Direkt-Commit auf `main`.
- Trailer (wörtlich, genau 1× je Zeile): `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`
- Vollständiger Trailer-Contract (Rangfolge Brief > Config > Harness, kein Raten aus Session-Kontext) liegt bei **P37**: `docs/specs/2026-11-15-git-trailer-contract-spec.md`, Implementierungsstelle `agents/1-generic/git.md:140`. Diese Spec übernimmt den Contract per Verweis, dupliziert ihn nicht (E-19, AC 8).
- Rebaseline ist der letzte Commit; vorherige Commits tragen je einen logischen Task (B1–B5).

## Trace-Anker: spec-id: SPEC-WORKER-CONTROL-CAPABILITY-2026-11-19
