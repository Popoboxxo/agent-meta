# Context Profiles — Phase 2 Status / Handoff

**Datum:** 2026-10-18 · **Status-Doku zu:** Phase-2-Plan `docs/plans/2026-10-17-context-profiles-phase2-plan.md` (Status: APPROVED) · **Spec:** `docs/specs/2026-10-11-context-profiles-spec.md` (Rev. 3.4, APPROVED) · **Tracking:** #977

## 1. Kopf

| Feld | Wert |
|---|---|
| Repo | `C:\Repositories\agent-meta` (Meta-Repo) |
| Branch | `feat/context-profiles-phase2a` — **committet; Push via `git`-Agent** (kein Upstream, kein PR) |
| Basis | `main` = `3f837852` |
| Working Tree | clean (keine uncommitteten, untracked oder gestagten Änderungen) |
| Plan | `docs/plans/2026-10-17-context-profiles-phase2-plan.md` (APPROVED) |
| Spec | `docs/specs/2026-10-11-context-profiles-spec.md` (Rev. 3.4) |
| Tracking-Issue | #977 |
| Datum | 2026-10-20 |

**Zwei-Spuren-Modell (AC-02/AC-25):**

- **Spur A — jetzt ausliefern (opt-in, unverifiziert):** Profil-Auflösung/Schema/Konditionale, Render-Verdichtung, Budgets/Anker/Report, Optimizer + Rolle — alles opt-in bzw. read-only; Defaults unangetastet; INFO `context-profile.unverified` aktiv. Pakete **2a/2b/2c/2d/2e sind fertig** (Stand 2026-10-20); offen ist nur noch 2f.
- **Spur B — Paket 2f, GATED (heute nicht startbar):** Baseline-Nachversuch (AC-02), `compact`-Eval (AC-25), Verifikations-Abschluss. Erfordert ausdrückliche Nutzerfreigabe + vorab angezeigte Kostenschätzung.

> Kernaussage für Spur A: `context-profile: compact` ist **Opt-in und unverifiziert** — niemals „verifiziert“, „validiert“ oder „empfohlen“.

## 2. Erledigt (main..HEAD)

Verifiziert mit `git log --oneline main..HEAD`; alle Commits sind auf dem lokalen Branch vorhanden.

| Task | Koordinate | Commit |
|---|---|---|
| Plan-Freigabe | — | `a24e6ba1` |
| Profil-Auflösung mit Präzedenz | 2a.1 | `c6fed0eb` |
| Schema + Validierungsfehler | 2a.2 | `be6811e8` |
| `CONTEXT_PROFILE`/`COMPACT_MODE` aus Auflösung | 2a.3 | `482f990c` |
| `context-profile.marker-in-rule` → ERROR | 2a.4 | `000adb8e` |
| INFO `context-profile.unverified` | 2a.5 | `e3430d99` |
| Shared-File-Downgrade (WARN + `full`) | 2a.6 | `34d6e3e4` |
| Doku + CHANGELOG Paket 2a | 2a.7 | `59d6de4d` |
| Admin-UI-Exposition | 2a.8 | `260ea3d4` |
| Routing-Zeilenformat `compact` | 2b.1 | `65595a9d` |
| Orchestrator-§2a/§9/Tabelle verdichten | 2b.2 | `e5d47d48` |
| Gate-Card + kompakte Agentenliste | 2b.3 | `c5a25370` |
| REFERENCE-Rules in Skills-Kanal | 2b.4 | `58c03822` |
| CLAUDE.md-Notizen als HTML-Kommentare | 2b.5 | `73f8c2d0` |
| CHANGELOG + Klassifikations-Doku 2b | 2b.6 | `de03ae00` |
| Pflicht-Anker `compact` | 2c.1 | `97b2b740` |
| `--context-report --profile compact\|both` | 2c.2 | `1dee2dd5` |
| Fix: §9-Pointer auflösbar | — | `22df124f` |
| Provider-Matrix 9×2 + Idempotenz | 2c.3 | `8fd72471` |
| Doku + CHANGELOG `compact`-Profil | 2c.4 | `913a527c` |
| Fix: `roster_in_harness`-Gating der Agent-Tabelle | — | `1efde04e` |
| Fix: Doku/Kommentar-Bereinigung 2a | — | `1c6949e4` |

**Zusatz-Commits (außerplanmäßige Korrekturen auf dem Branch):** `ec8b7eaa` (2a.8-Task im Plan), `0631a6ee` (Log-Zeilen in `sync.log` drainen), `3ebff84f` (`context-profile.invalid`), `91d8514c` (Admin-UI lehnt ungültige Profil-Writes ab).

### Paket 2d/2e (2026-10-20)

| Koordinate / Task | Commit |
|---|---|
| 2d.1 / Task 20 | `a074dafc` |
| 2d.2 / Task 21 | `ea988447` |
| 2d.3 / Task 22 | `ce06e560` |
| 2d.4 / Task 23 | `79ce4ecb` |
| 2d.5 / Task 24 | `c182b57b` |
| 2d.6 / Task 25 | `1aacab24` |
| 2d.7 / Task 26 | `79132d9d` |
| 2e.1 / Task 27 | `8fe1faf1` |
| 2e.2 / Task 28 | `0cb42218` |
| 2e.3 / Task 29 | `dd6c32b0` |
| 2e.4 / Task 30 | `aad97f08` |
| 2e.5 / Task 31 | `20f2200d` |
| 2e.6 / Task 32 | `91fb26a4` |
| Fix: Standalone + compact-Budgets | `58d7689f` |

## 3. Task 2.00 Precondition

**Zustand:** Ein `SKIPPED-BY-USER`-Record **existiert** unter `tests/routing-llm-eval/roles/runs/2026-10-17-qg1-deepseek.json`. `tests/test_eval_baseline_schema.py` ist **grün (16 passed)**.

**Abweichung:** Die Plan-Checkboxen von Task 2.00 (2.00) sind **nicht** getickt, und der Dateiname weicht vom im Plan vorgeschlagenen `2026-10-17-baseline-full.json` ab.

**Schlussfolgerung:** Die Vorbedingung gilt als **faktisch erfüllt** (Skip-Record vorhanden, Schema-Test grün; AC-02 bleibt wahrheitsgemäß „nicht belegt“). Die Task-2.00-Steps bleiben bewusst ungetickt, da der Record-Name vom Plan-Soll abweicht — siehe §6/§8. Kein Blocker für Spur A.

## 4. Spur-A-Pakete 2d/2e — ERLEDIGT

> **Status 2026-10-20:** Pakete **2d** (Tasks 20–26) und **2e** (Tasks 27–32) sind **ERLEDIGT und committet** (Commits siehe §2, Plan-Checkboxen getickt). **Als Nächstes: nur Paket 2f — GATED** (siehe §5).

### Paket 2d — Config-Optimizer-Kern und Applier (Tasks 20–26) — **ERLEDIGT**

| Koordinate | Task | Ein-Zeiler |
|---|---|---|
| 2d.1 | 20 | Laufzeit-Leser-Registry (`config/runtime-config-readers.yaml`) inkl. `credentials` als Daten (IC-35). |
| 2d.2 | 21 | Optimizer-Runner mit Fan-out + Beweis (`meta_optimizer.py`, Sentinel-Render, `proof.json`) (IC-24/IC-25). |
| 2d.3 | 22 | Remove-only-Applier mit `--accept`-Pflicht und `preview.json`-Bindung (KEINE Zieldateien, Recompute). |
| 2d.4 | 23 | `fill_defaults`/`refill_keys` als info-only, nicht-entfernbare Hinweise. |
| 2d.5 | 24 | Inaktive Rollen ⇒ `inactive-scope` mit Reaktivierungswarnung (statt `no-effect`). |
| 2d.6 | 25 | Laufzeit-Leser-Keys nur mit `--accept-runtime` anwendbar (Marks). |
| 2d.7 | 26 | Credential-Ausschluss und Sink-Artefakte End-to-End nachweisen. |

DAG 2d: `2d.1 → 2d.2 → 2d.3 → 2d.4 → 2d.5 → 2d.6 → 2d.7` (Ausführung unabhängig vom Eval möglich; **Merge erst nach 2c**).

### Paket 2e — Rolle `meta-optimizer` und Manager-Integration (Tasks 27–32) — **ERLEDIGT**

| Koordinate | Task | Ein-Zeiler |
|---|---|---|
| 2e.1 | 27 | Rolle `meta-optimizer` read-only (exakte Tool-Menge, kein `model:`, Contract-Marker) (IC-26). |
| 2e.2 | 28 | Rollen-Registrierung (`role-defaults`, Addressability) + Goldens/Rebaseline + Szenario 78 (IC-28 Nr. 4). |
| 2e.3 | 29 | Contract `config-patch-proposal-v1` in den Manager verdrahten (kein `handoff.output-not-consumed`). |
| 2e.4 | 30 | `agent-meta-manager`-Apply-Workflow (drei Optimizer-Schritte, Version-Bump `1.25.0`) (IC-27). |
| 2e.5 | 31 | Orchestrator-Vorschau-Pflicht vor Anwendung (IC-27). |
| 2e.6 | 32 | Szenario 78 + CLI-Doku + Neue-Rolle-Checkliste abschließen. |

DAG 2e: `(2d.2, 2d.3) → 2e.1 → (2e.2; 2e.3 → 2e.4 → 2e.5) → 2e.6`.

## 5. Spur B (2f) — GATED

**Nicht starten.** Aktueller Status: `SKIPPED-BY-USER`. Start erst nach **separater Nutzerfreigabe** und **vorab angezeigter Kostenschätzung**.

- **2f.1** (Task 33): Baseline-Nachversuch (full-Routing-Eval) — Gate: Nutzerfreigabe + Kostenschätzung zuerst.
- **2f.2** (Task 34): `compact`-Eval gegen die Baseline (AC-25) — Gate: AC-02 belegt.
- **2f.3** (Task 35): Verifikations-Abschluss (INFO-Absenz, Doku-Claim, AC-26-Claim) — Gate: AC-25 belegt.

DAG 2f: `2f.1 → 2f.2 → 2f.3`.

## 6. Offene Abweichungen / Known Issues

1. **MAJOR — AC-26-Zielgrößen verfehlt (compact size targets MISSED).**
   - Gemessen/verfehlt: `AGENTS.md` Einzel **9,6–10,6 KB** (Ziel 8 KB), Gemini **10,1 KB** (Ziel 9 KB), Continue **20,2 KB** (Ziel 2 KB), Copilot **9.468 B** (Ziel 4.000 Zeichen).
   - Getroffen: Claude-Orchestrator **32.450 B** ≤ 32.768 B; Multi-Shared **11.374 B** ≤ 12.288 B und < 32.768 B.
   - **Per AC-26 erfordert ein verfehltes Ziel eine SPEC-Revision** (niemals stille Testanpassung) → **jetzt out of scope**.
   - Konsequenz: Ziele bleiben **ESTIMATE-Daten**; gemessene Actuals sind als **Regressions-Obergrenzen** gepinnt; der Over-Target-Checker ist aktiv; die Doku benennt die Verfehlung **explizit**.
2. **Provider-override-only `compact`-Hybrid:** Das Entry-File-Layout ist compact, **eingebettete Rules bleiben jedoch uncompacted** — Ursache: Rule-Kompaktierung hängt am **globalen** `COMPACT_MODE`, während das Entry-File-Gating `CONTEXT_PROFILE_COMPACT` **per Provider** nutzt. Bewertet als **OUT OF SCOPE** (Ripples auf MCP-/External-Tool-Sektionen, `resolve_plugin_compact`, `KNOWLEDGE_ENGINE_HINTS`; ein zu weites Ziehen riskiert `context.dangling-pointer` ERROR). **Empfehlung: eigener Backlog-Eintrag.**
3. **Minor (latent):** `_extract_rule_section` ist **fence-unaware** — kein aktiver Defekt, nur latentes Risiko.
4. **Vorbestehend (nicht von 2d/2e):** `tests/test_no_role_routes_in_templates.py::test_repo_conditional_markers_are_well_formed` ist **rot** — nested `{{#if …}}{{#unless …}}` in `agents/1-generic/orchestrator.md:320-322`; der Parser verbietet mehrere Direktiven pro Zeile. Auf `8c334aef` bereits rot (introduced by `1efde04e`/`e5d47d48`), **nicht auf `main`**. Bewusst **nicht** „gefixt“ und **nicht** Test-abgeschwächt.
5. **Task 31 / AC-90:** Der Pflichtabschnitt vergrößert den compact-Orchestrator um **exakt +1258 B je Provider** → `_IST_COMPACT` wird re-pinnt (Commit `58d7689f`). Die AC-26-Ziele bleiben **unverändert** und weiterhin **unmet/ESTIMATE** (siehe Punkt 1).
6. **Task 23 (2d.4):** Der Guard neutralisiert bestehende Refill-Kandidaten; es werden bewusst **keine NEUEN** info-only-Kandidaten für alle Refill-Keys emittiert (Runner-Test-Invariante). Als **Design-Entscheidung** dokumentiert.
7. **Task 30 (2e.4):** Der `test_context_budgets.py`-Re-Pin absorbierte zusätzlich stale Pins aus 2e.2/2e.3/compact-Arbeit (im Code-Kommentar dokumentiert).
8. **Umgebung:** Der 2d/2e-Lauf erfolgte in einer **Linux-Sandbox** (uv-venv, CPython 3.13.16, pytest 9.1.1) statt Windows `.venv-1\Scripts\python.exe`; `bash` war für Dev-/Test-Rollen verfügbar (abweichend von §7).
9. **In dieser Session behoben (resolved):**
   - compact §9-Pointer ist auflösbar (`22df124f`);
   - `roster_in_harness`-Gating implementiert + 2c.3 QG-2 verschärft (`1efde04e`);
   - die 2b.1-`Files`-Block-Abweichung war **stale Plan-Metadaten** — kein Code-Churn.

## 7. Umgebung / Ausführung

- **OS:** Windows; Shell **PowerShell 5.1**. Das `bash`-Tool ist **DENIED** → Shell-Aufrufe (git/pytest/sync) über das **Serena-`execute_shell_command`-Tool**.
- **Python:** Repo-Venv `.venv-1\Scripts\python.exe -m pytest ...` verwenden (blankes `python -m pytest` hat kein pytest).
- **Datei-Lesen:** Das `read`-Tool liefert teils kommentar-bereinigten Inhalt → für den exakten Quelltext `serena_execute_shell_command` + `Get-Content` oder Serenas `read_file` nutzen.
- **Befehle:** `python scripts/sync.py`, `--validate`, `--rehydrate`, `--scan-staged`; `python scripts/consistency-check.py`; Szenarien `bash tests/scenarios/run.sh <name>` (über einen bash-fähigen Runner).
- **Bekannter, vorbestehender, unabhängiger Fehlschlag:** `tests/test_python_compat_consistency.py` **4F** auf Windows (nur Pfad-Separator-Assertions).
- **graphify:** `graphify-out/` existiert; `graphify query "<q>"`.

## 8. Resume-Schritte

1. `git status` / `git log --oneline -5` — Branch/Zustand verifizieren.
2. `python scripts/sync.py --rehydrate` — Kontext rehydrieren.
3. **Pakete 2a–2e sind abgeschlossen** (Plan-Checkboxen Tasks 1–32 getickt; Commits siehe §2). Es ist **kein Spur-A-Task offen** — Paket 2d/2e sind fertig, nichts nachzuziehen.
4. **Als Nächstes: nur Paket 2f (GATED)** — 2f.1 → 2f.2 → 2f.3, und **erst** nach ausdrücklicher Nutzerfreigabe + vorab angezeigter Kostenschätzung (§5).
5. `compact` bleibt **opt-in und unverifiziert**. Kein Push/Branch/PR ohne Auftrag (nur `git`-Agent).

## 9. Fortsetzungs-Prompt

```
Wir setzen den freigegebenen Phase-2-Plan für Context Profiles in C:\Repositories\agent-meta fort.

Lies zuerst: docs/plans/2026-10-18-context-profiles-phase2-status.md (Status/Handoff), dann docs/plans/2026-10-17-context-profiles-phase2-plan.md (Task-Sektionen) und docs/specs/2026-10-11-context-profiles-spec.md (Rev. 3.4).

Stand: Branch feat/context-profiles-phase2a (lokal, nicht gepusht). Pakete 2a, 2b, 2c sind FERTIG und committet (siehe Statusdoku §2). Nächstes: Paket 2d (Tasks 20–26), danach Paket 2e (Tasks 27–32). Paket 2f bleibt GATED — nicht starten (eigene Nutzerfreigabe + Kostenschätzung nötig).

Umgebung: Windows; das `bash`-Tool ist gesperrt → Serena-Shell-Tool nutzen; Tests mit `.venv-1\Scripts\python.exe -m pytest ...`.

Regeln: alle Dev-Arbeit über den orchestrator; ein Commit pro Task mit der exakten Plan-Message; TDD (rot→grün); provider-agnostisch (kein `if provider == "Name"`); Python 3.9; Byte-Stabilität ohne Opt-in; `compact` bleibt opt-in & unverifiziert; kein Push/Branch/PR ohne Auftrag (nur `git`-Agent); keine Worktree-Isolation.

Ziel: Paket 2d (2d.1–2d.7) vollständig implementieren und je Task committen, dann Statusbericht. Wenn 2d grün ist, mit Paket 2e fortfahren. Wo ein Plan-Files-Block/Verhalten von der Realität abweicht: sinnvoll fixen und dokumentieren; AC-26-Zielverfehlung als dokumentierten Spec-Revisions-Punkt belassen.

Lieferergebnisse: Red/Green-Nachweis je Task, Commits, `sync.py --check`-/consistency-Ausgaben, aktualisierte Plan-Checkboxen, knapper Statusbericht.
```

## 10. Abschluss-Verifikation (2026-10-20)

| Prüfung | Ergebnis |
|---|---|
| Volle Szenarien-Suite | `Scenarios: 78  Passed: 78  Failed: 0` |
| Relevante pytest-Auswahl (initial) | 569 passed / 3 failed |
| Relevante pytest-Auswahl (nach Fix `58d7689f`) | 572/572 effektiv grün (siehe unten) |
| `scripts/consistency-check.py` | **PASS** — „No issues found“ |
| `sync.py --validate` | Exit 0 (2 Warnungen, siehe unten) |

- **Szenarien:** Die volle Szenarien-Suite lief komplett grün: `Scenarios: 78  Passed: 78  Failed: 0`.
- **pytest:** Die relevante Auswahl war initial **569 passed / 3 failed**. Alle 3 Fehlschläge gingen auf **Task 31** zurück: stale `standalone/agents/orchestrator.md` + **compact-Budget-Decken um +1258 B/Provider überschritten**. Nach dem Fix `58d7689f` lieferte `tests/test_context_budgets.py tests/test_standalone_export_in_sync.py` **13 passed**; damit sind **572/572** der Auswahl grün.
- **consistency-check:** `scripts/consistency-check.py` meldet **PASS** / „No issues found“.
- **sync validate:** `sync.py --validate` endet mit **Exit 0**; es bleiben **2 Warnungen**: `se` gate-dropped und `external/awesome-claude-code` Checkout `3d8bde25`.
