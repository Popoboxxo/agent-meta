---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: Repository-weite Doku-Konsolidierung agent-meta — Implementation Plan
status: APPROVED
revision: 0.1
pipeline_stages:
  implement: 3
related:
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/plans/README.md
---

# Repository-weite Doku-Konsolidierung agent-meta — Implementation Plan

> Status: **APPROVED (2026-09-26)** — der Plan ist **genehmigt**; die Ausführung ist
> freigegeben. Grundlage: die Spec `SPEC-DOCS-CONSOLIDATION-2026-09-25` trägt seit 2026-09-26
> `status: APPROVED` (`docs/specs/2026-09-25-repository-documentation-consolidation.md:4`,
> Freigabevermerk im Spec-Kopf). Das Wertepaket des Plan-Templates
> (`geplant | IN PROGRESS | complete`) kennt kein `Entwurf`; hier gilt die Gate-Sprache der
> Spec. **Kein** `APPROVED` wird erfunden — es liegt eine dokumentierte User-Freigabe vor.
>
> **Genehmigungsumfang:** Die Freigabe umfasst die **Ausführung dieses Plans** (W0–W8, 47
> Tasks) inklusive der im Plan mit Owner und Entscheidungsweg versehenen Entscheidungs-Points
> W0-1/W0-3/W0-6 (davon **OQ2/OQ6/OQ8 bereits entschieden** — Ergebnis-Records) und der noch
> offenen Entscheidungs-Tasks W0-7/W5-1/W8-1. Die **Checkboxen sind bewusst nicht abgehakt** — das
> Plan-Ledger bleibt offen, die Genehmigung betrifft den Plan, nicht den Fortschritt. Die
> Task-Checkboxen werden erst während der Ausführung gesetzt.
>
> **Offene Entscheidungen aus der Spec** (bleiben offen, Entscheidung liegt bei den
> jeweiligen Ownern): **OQ1, OQ3, OQ4, OQ9** (Spec §11.1). Durch den Nutzer am
> 2026-09-26 entschieden und damit geschlossen: **OQ2** (`llms.txt` = **Hybrid**),
> **OQ6** (`docs/INDEX.md` = **tracked**) und **OQ8** (Regenerierung deterministisch über
> **Sync/Validator**, kein Commit-Hook) — Spec §11.2. **Konsequenz für diesen Plan:** die auf
> OQ2/OQ6/OQ8 bezogenen Punkte (u. a. `docs/plans/2026-09-25-docs-consolidation-oq2.md` /
> `-oq6.md` / `-oq8.md`) sind **keine offenen Entscheidungs-Tasks mehr**; sie werden als
> **Ergebnis-Dokumentation** der getroffenen Entscheidung geführt, nicht als offene Frage.
> Die betroffenen Task-Beschreibungen (W0-1, W0-3, W0-6, W1-6, W3-6, W3-7) sind gegen diese
> Entscheidung **korrigiert** und bei Ausführungsbeginn nochmals abzugleichen.
>
> **Ablage:** aktiv in `docs/plans/`, nicht `archive/` — `docs/plans/README.md:3-7`. Archivierung
> erst nach `STATUS: done` (Merge manuell bestätigt, Skill `plan-ledger`).
>
> **System-Design (verbindliche Eingangsgrundlage):**
> `docs/specs/2026-09-25-repository-documentation-consolidation-design.md`
> (concept-architect, 2026-09-25, 397 Zeilen; Trace-Anker
> `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25`).

**Goal:** Die 11 nachweislich falschen Handzahlen der Einstiegs-Doku (F1–F4, F14 ×3, F22 ×2,
`ARCHITECTURE.md:3`) durch berechnete `DOCS_*`-Fakten ersetzen, den bereits spezifizierten,
unerfüllten `docs/INDEX.md`-Vertrag aus `scripts/lib/spec_plan_scaffold.py:23` erfüllen, die
mehrfach geführten Spec/Plan- und Guide-Bäume konsolidieren und die Wiki-Staleness maschinell
machen — ohne Inhalts-Rewrite bestehender Doku.

**Architecture:** Vier abgeschlossene Module (Spec §4): M1 `doc_facts.py` (stdlib-Blatt, reine
Faktenberechnung) → M2 `doc_renderer.py` / `doc_index.py` / Snippet-Bridge / Pipeline-Stage
(Writer) → M3 reine Migration (`git mv`, keine neue Code-Datei) → M4
`knowledge.py::sync_wiki_index` (Schwester-Modul zu M2, importiert M1 **nicht**).
Schichtungs-Invariante `scripts/lib/variables.py:9-17` — keine Zyklen. Absenz-Defaults sind
**fail-off** für Writer **und** Checks (Präzedenz `scripts/lib/knowledge.py:127`).

**Tech Stack:** Python 3, **nur Stdlib** (NFA-07) + `scripts/lib`-Module, pytest, Markdown/YAML/JSON,
`scripts/sync.py`, `scripts/consistency-check.py`, Bash (`tests/scenarios/run.sh`).

**Spec:** `docs/specs/2026-09-25-repository-documentation-consolidation.md`
(`spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25`, Rev. 0.3, `status: APPROVED` (2026-09-26),
2015 Zeilen im Rev.-0.3-Stand).
Klassifikation **XL / Architectural** (Spec:62-66).

## Global Constraints

- **Ausführung freigegeben (2026-09-26).** Das Gate ist erfüllt: die Spec trägt
  `Status: APPROVED` (Freigabe 2026-09-26), dieser Plan trägt `Status: APPROVED (2026-09-26)`.
  Kein Task startet **vor** der Bestätigung, dass **W0-4** (Track-A-Merge-Status) grün ist —
  **W0-4 ist das Track-A-Gate** und sperrt W1 und W2; W0-2 ist der Design-Freeze und **kein**
  Gate. Dieser Plan ist ab der Freigabe ein **Startsignal**; die
  Task-Checkboxen sind zum Freigabezeitpunkt **bewusst alle offen** (Ledger-Start).
- **Datei-Ownership:** Jede Datei wird in genau **einer** Task geschrieben. `Files:` ist der Input
  für `check_plan_file_overlap` (`scripts/lib/orchestration.py`) und die Barrieren-Gruppen.
  **Lesen ist kein Ownership** — W2 liest `README.md`, ohne es zu besitzen.
- **Ein Branch pro Welle** (Spec §9.2 W0, R16): `chore/docs-consolidation-w<N>`, gestapelte PRs
  W0→W8, **ein Commit pro Datei**, Rebase gegen den Track-A-Branch vor jedem Merge.
- **Track-A-Kollision (R3, R15, Spec §2.3):** W1 und W2 starten **erst** nach dem Track-A-Merge
  (`tests/fixtures/slimming-golden/`); Gate = Task W0-4. W1/W2 laufen **sequenziell zu** Track A
  und **nicht** parallel zu Änderungen an `scripts/lib/config.py` und `scripts/lib/consistency/*`.
  Die V1-Fixture `tests/fixtures/docs_v1_fixtures.md` entsteht erst danach.
- **Provider-Agnostik (NFA-03):** kein `if provider == "Name"` in M1–M4; kein Config-Key enthält
  einen Providernamen. Guard `tests/test_provider_agnostic_dispatch.py`.
- **Fail-off für alle sechs Config-Keys** (IC-22): `docs-consolidation.enabled` ist bei Abwesenheit
  `false`; agent-meta selbst setzt ihn **explizit** `true` (NG-9). Gleiches gilt für V1–V9.
- **Kein neues `sync.py`-CLI-Flag** (NG-4) — jedes Flag wäre in `docs/api/cli-reference.md` zu
  dokumentieren (`scripts/lib/consistency/docs.py:9-44`, `Severity.ERROR`).
- **Keine inhaltliche Neuschreibung** bestehender Guides/Architektur/Wiki-Seiten (NG-1).
  Migrationen sind `git mv` + Marker-Regionen + additive Frontmatter-Zeilen.
- **Keine Mutation an `knowledge/sources/`** (NG-2); **kein** Eingriff in generierte Kontextdateien
  außer M-12 (NG-5); **kein** Rollen-Paritäts-Fix (NG-8); **kein** Platzhalter-Marker in
  Provider-Dateien (NG-11).
- **NG-10 / AC-38:** kein Assert-Skript und keine Fixture-Config der Szenarien 50/51/52/54/55/56
  wird angefasst. Szenario `64-docs-facts-drift` bleibt **Track A** (Spec §2.3), nur koordiniert.
- **NFA-10:** keine Secrets, keine Env-Werte in generierten Dateien.
- **Konventionen:** Conventional Commits (Englisch, ≤72 Zeichen, imperativ), PEP 8, snake_case,
  `from __future__ import annotations` in neuen Modulen (Muster
  `scripts/lib/spec_plan_scaffold.py:12`). Commit/Push **nur** über den `git`-Agenten und **nur**
  mit expliziten Pfaden (`git add <pfad>`; verboten: `git add -A`, `git add .`, `git commit -a`).
- **Kein Worktree**, Repo-Containment, ein frischer Subagent pro Task (Skill `plan-ledger`).
- **Keine Platzhalter** (`TODO`/`TBD`/`…`) in diesem Plan. Offene Punkte sind ausschließlich die
  Entscheidungs-Tasks W0-7/W5-1/W8-1 (OQ1/OQ9/OQ4) mit Owner und Entscheidungsweg sowie die
  Ergebnis-Records W0-1/W0-3/W0-6 zu den bereits entschiedenen OQ6/OQ2/OQ8 (Spec §11.2).

## File Structure

### Neu anzulegen (Code)

- Create: `scripts/lib/doc_facts.py` — IC-01…IC-04, IC-23. Stdlib-Blatt, 23 `DOCS_*`-Fakten.
- Create: `scripts/lib/doc_renderer.py` — IC-07, IC-10, IC-13, IC-14.
- Create: `scripts/lib/doc_index.py` — IC-09, einzige Komponente mit Doku-FS-Semantik.
- Create: `snippets/docs/repo-facts.md`, `agent-roster.md`, `pipelines.md`, `hooks.md`,
  `providers.md`, `tier-presets.md` — IC-11, 6 `*_BLOCK`-Snippet-Dateien.
- Create: `config/doc-facts-expected.yaml` — IC-23, **elf** handgepflegte Sollwerte; einziger Ort
  mit Sollzahlen im Repo-Baum (R14, NFA-11).
- Create: `docs/INDEX.md` — W3-6, 100 % generiert (§3.1), tracked (OQ6).
- Create: `docs/architecture/INDEX.md` — W4-3, Teil-Vorschau auf denselben Baum (IC-10(d)).

### Neu anzulegen (Tests)

- Create: `tests/test_doc_facts.py` — AC-01…AC-06, AC-11, AC-12, AC-25, V9-Test (W8-4).
- Create: `tests/test_doc_facts_expected.py` — AC-36.
- Create: `tests/test_doc_renderer.py` — AC-14…AC-18, AC-20…AC-24, AC-26, AC-27.
- Create: `tests/test_generated_file_drift_docs.py` — AC-19, AC-37.
- Create: `tests/test_docs_consolidation_migration.py` — AC-28, AC-29, AC-30, AC-32, AC-39, AC-40.
- Create: `tests/test_knowledge_index_gen.py` — AC-33, AC-34, AC-35, AC-41.
- Create: `tests/fixtures/docs_v1_fixtures.md` — V1a+V1b Positiv-Fixture (AC-07/AC-08), **erst
  nach Track-A-Merge** (Spec §2.3).
- Create: `docs/plans/2026-09-25-docs-consolidation-oq1.md`, `-oq2.md`, `-oq4.md`, `-oq6.md`,
  `-oq8.md`, `-oq9.md`, `-wave0-freeze.md`, `-track-a-gate.md` — W0-x / W5-1 / W8-1.

### Geändert (Code)

- Modify: `scripts/lib/consistency/docs.py` — IC-05, Checks V1…V9 (bestehende 3 unverändert).
- Modify: `scripts/lib/consistency/placeholders.py` — IC-06, `^DOCS_` in `_DYNAMIC_PREFIXES`.
- Modify: `scripts/consistency-check.py` — Registrierung der neun Checks + Common-Gate (AC-13).
- Modify: `scripts/lib/config.py` — IC-11, Snippet-Verzeichnis `snippets/docs/`; `_load_block_snippet`
  (`config.py:1842-1858`) bleibt **unverändert**.
- Modify: `scripts/lib/sync_pipeline.py` — IC-12, Stage **nach** `scaffold_spec_plan_dirs` (`:935`),
  **vor** Hash-Capture (`:1090-1099`).
- Modify: `scripts/lib/spec_plan_scaffold.py` — IC-15, `is_file_index_skeleton()` + Marker.
- Modify: `scripts/lib/generated_file_drift.py` — IC-16, Doku-Pfade symmetrisch in Scan **und**
  Capture; Allowlist gegen Basis-Pfad.
- Modify: `scripts/lib/knowledge.py` — IC-19, IC-20, IC-24 (nur W7).
- Modify: `config/project-config.schema.json` — M-11, IC-22, geschlossener Block
  `docs-consolidation` mit **sechs** Properties.

### Geändert (Config / Doku / Agent)

- Modify: `.meta-config/project.yaml` — W1-10 fünf additive Keys; W3-4 `checks.strict: true`;
  W6-2 `legacy:` +2 Zeilen (`:61-63`); W7-2/W7-5 `okf.index-mode`; W8-4 `PROJECT_STRUCTURE`
  (`:205-221`).
- **Unverändert:** `.gitignore` — OQ6 ist entschieden (2026-09-26): `docs/INDEX.md` ist
  **tracked**, also gibt es **keinen** `.gitignore`-Eintrag für `docs/INDEX.md`; die Datei
  `.gitignore` selbst wird von **keinem** Task geschrieben oder verändert. **W3-6 legt
  `docs/INDEX.md` an und committet sie (tracked)** — W3-6 schreibt **nicht** in `.gitignore`.
  Verifiziert wird stattdessen `git check-ignore -q docs/INDEX.md` → Exit **1**.
- Modify: `README.md` — W3-7 Marker-Regionen, W8-2 Totverweise (`:721-724`), W8-3 Providerzahl.
- Modify: `llms.txt` — W3-7 `:5`/`:24`, W8-3 Providerzahl.
- Modify: `ARCHITECTURE.md` — W3-7 `:3` als Region, W4-2 Stub.
- Modify: `knowledge/schema.md` — W7-1, Absatz „`index.md` is generated“ (`:41-42`), mit
  **User-Sign-off** (`:44-46`).
- Modify: `agents/1-generic/knowledge-indexer.md` — W7-4, IC-21 (einzige `agents/`-Berührung, NFA-08).
- Modify: `knowledge/wiki/**/*.md` — W5-3, additive `derived-from`/`derived-at`; W7-5 generiert
  `index.md` und hängt eine Zeile an `log.md`.
- Modify: `docs/REQUIREMENTS.md` — W8-1, deklarativer ID-Abschnitt (keine Umbenennung, NG-6).

### Verschoben / Stub / Archiviert / Gelöscht (M3)

| Op | Aktion | Welle | Quelle → Ziel |
|---|---|---|---|
| M-1 | `git mv` | W4 | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` |
| M-2 | Stub schreiben | W4 | `ARCHITECTURE.md` (84 Z) → generierter Stub (IC-18) |
| M-7 | additiv | W4 | Stale-Deklaration wandert in die Langfassung |
| M-5 | `git mv` | W5 | `howto/configs/project.yaml.example` (340 Z) → `docs/guides/configs/project.yaml.example` |
| M-6 | `git mv` | W5 | `docs/howto/admin-ui-remote-access.md` → `docs/guides/admin-ui-remote-access.md`; danach `docs/howto/` entfernt |
| M-9/M-10 | additiv | W5 | `derived-from`/`derived-at`; Architektur-Redirects |
| M-3 | `git mv` | W6 | `docs/superpowers/specs/` → `docs/specs/archive/superpowers/` |
| M-4 | `git mv` | W6 | `docs/superpowers/plans/` → `docs/plans/archive/superpowers/`; danach `docs/superpowers/` entfernt |
| M-8 | Modify | W8 | `README.md:721-724` Totverweise |
| M-11 | Modify | W1 | Schema-Block |
| M-12 | Modify (Config) | W8 | `PROJECT_STRUCTURE` |
| M-13 | Modify | W6 | `legacy:` additiv |

### Bewusst **nicht** angefasst (mit Grund)

- `docs/CODEBASE_OVERVIEW.md` — NG-3 (gehört `documenter`) **und kein AC** in der Spec ⇒ nicht
  geplant; FI-2 bleibt Folge-Issue.
- `knowledge/sources/**` — NG-2, append-only.
- `tests/scenarios/asserts/5{0,1,2,4,5,6}*.sh`, `tests/scenarios/configs/*` — NG-10 / AC-38.
- `AGENTS.md`-Bootstrap-Block — NG-5 / OQ3, eigene REQ nach W8.
- `docs/README.md` — NG-7, wird nicht eingeführt (T-3).

---

## Wellen-Übersicht, Reihenfolge und Entscheidungs-Vorlauf

```
W0 (6 Tasks, kein Code)
 |- W0-1 REC-OQ6 -----> Ergebnis-Record, entschieden 2026-09-26: tracked, kein .gitignore-Eintrag
 |- W0-3 REC-OQ2 -----> Ergebnis-Record, entschieden 2026-09-26: Hybrid (2 Blöcke, Rest Handtext)
 |- W0-4 Track-A-Gate -> blockiert W1 und W2
 |- W0-6 REC-OQ8 -----> Ergebnis-Record, entschieden 2026-09-26: Sync/Validator, kein Hook
 |- W0-7 DEC-OQ1 -----> blockiert Abschluss W5 (offen)
 `- W0-2 Freeze -------> blockiert alle W0-Folge-Tasks (W0-1, W0-3, W0-4, W0-6, W0-7)
        v
PG-1 (3 Ketten parallel, max 3 Agents)
 |- W1-A: W1-1 -> W1-2 -> W1-3 -> W1-4 -> W1-5 -> W1-6   (doc_facts + Config-Bridge)
 |- W1-B: W1-7 -> W1-8 -> W1-10                        (doc_renderer + doc_index + Config-Keys)
 `- W1-C: W1-9                                        (Schema-Block M-11)
        v
PG-2 (2 Ketten parallel, max 2 Agents)
 |- W2: W2-1 -> W2-2 -> W2-3 -> W2-4 -> W2-5 -> W2-6 -> W2-7   (consistency/docs.py)
 `- W3: W3-1 -> W3-2 -> W3-3 -> W3-4 -> W3-5 -> W3-6 -> W3-7   (Renderer/Stage/Drift/Index)
        v
PG-3 (BEWUSST SERIELL, 1 Agent)  W4-1 -> W4-2 -> W4-3 -> W5-1 -> W5-2 -> W5-3 -> W6-1 -> W6-2
        v
PG-4 (isoliert, 1 Agent)         W7-1 -> W7-2 -> W7-3 -> W7-4 -> W7-5
        v
PG-5 (1 Agent)                    W8-1 -> W8-2 -> W8-3 -> W8-4
```

| Welle | Tasks | AC-Menge (Spec §9.2) | Abhängig von | Parallel | Rückrollpunkt |
|---|---|---|---|---|---|
| W0 | 6 | Anker (W0 trägt laut Spec §9.2 kein eigenes AC) | — | — | Dateien löschen, kein Code berührt |
| W1 | 10 | AC-01…AC-06, AC-23…AC-25, AC-39 | W0 | PG-1: W1-A ‖ W1-B ‖ W1-C | `docs-consolidation.enabled: false`; kein Datei-Diff |
| W2 | 7 | AC-07…AC-11, AC-13, AC-36 | W1-A, W0-4 | PG-2: W2 ‖ W3 | `checks.strict: false` bzw. `enabled: false` |
| W3 | 7 | AC-12, AC-14…AC-22, AC-26, AC-27, AC-37, AC-38 | W1-B, W0-1, W0-6 | PG-2 | `git rm docs/INDEX.md`; Marker entfernen; `enabled: false` |
| W4 | 3 | AC-28 (Teil), AC-29 | W3 | PG-3 seriell | `git mv` zurück + Stub `git checkout` |
| W5 | 3 | AC-28 (Teil), AC-31 | W1, W0-7 | PG-3 seriell | `git mv` zurück; Annotationen additiv revertierbar |
| W6 | 2 | AC-28 (Teil), AC-32 | W3 | PG-3 seriell | Config-Key additiv → Zeile entfernen |
| W7 | 5 | AC-33…AC-35, AC-41 | W5, W3, Rollenpflege-Branch gemergt | **isoliert** | `index-mode: llm` → Generator stumm; `restore_wiki_index()` |
| W8 | 4 | AC-30, AC-40 | W2, W3, **nach** W7 | PG-5 | additiv revertierbar |

### Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht

- **W2 ‖ W3:** Write-Sets disjunkt. W2 besitzt `scripts/lib/consistency/docs.py`,
  `tests/test_doc_facts.py`, `tests/test_doc_facts_expected.py`, `tests/fixtures/docs_v1_fixtures.md`,
  `scripts/consistency-check.py`. W3 besitzt `scripts/lib/doc_renderer.py`, `scripts/lib/doc_index.py`,
  `scripts/lib/sync_pipeline.py`, `scripts/lib/spec_plan_scaffold.py`,
  `scripts/lib/generated_file_drift.py`, `tests/test_doc_renderer.py`,
  `tests/test_generated_file_drift_docs.py`, `docs/INDEX.md`, `README.md`, `llms.txt`,
  `ARCHITECTURE.md`, `.meta-config/project.yaml`. Überschneidung: keine (`.gitignore` bleibt
  unberührt, OQ6 entschieden). Spec §9.2
  bestätigt diese Parallelität.
- **W4/W5/W6 seriell (bewusste Abweichung von Spec §9.2 „Parallel mit“):** die Spec bindet die
  Testdateinamen (§7-Einleitung). AC-28, AC-29, AC-31 und AC-32 verweisen **alle** per `::` auf
  `tests/test_docs_consolidation_migration.py`. Tasks, die dieselbe Datei anlegen oder erweitern,
  sind nicht ownership-disjunkt; `check_plan_file_overlap` würde den Parallelstart als Fehler
  melden. Zusätzlich erzeugt jede `git mv`-Welle R+A-Diffs auf denselben Stammpfaden.
  **Entscheidung: PG-3 läuft mit einem Agenten sequenziell W4 → W5 → W6.** Das verlängert die
  Laufzeit, verletzt aber weder Ownership noch `plan-ledger`.
- **W7 isoliert** (NFA-06, R2, R19): einziger Policy-Bruch (`scripts/lib/knowledge.py:112-114`),
  einziges Datenverlust-Potenzial, einzige `agents/`-Berührung.
- **W8 nach W7**, obwohl Spec §9.2 nur W2/W3 nennt: W7 aktiviert den Generator und verschiebt den
  Diff-Bezugsrahmen; W8s M-12 wirkt auf **alle** generierten Kontextdateien. Die Sequenzierung
  hält NFA-06 („Rollback je Welle invalidiert keine andere Welle“) aufrecht.
- **Maximal 3 gleichzeitig laufende Agents** — unter der Grenze von 4. Eine wellen-interne
  Barrieren-Spaltung über 4 hinaus ist damit **nicht** erforderlich.
- **`.meta-config/project.yaml` wird von W1-10, W3-4, W6-2, W7-2/5 und W8-4 geschrieben** — alle
  liegen in **verschiedenen, sequenziell geordneten** Wellen, daher keine Parallelitätskollision.

### Step-Agent-Map (plan-driven `implement`, Stufe 3)

| Task | Agent | Task | Agent | Task | Agent |
|---|---|---|---|---|---|
| W0-1, W0-4, W0-6, W0-7 | orchestrator | W1-1…W1-5, W1-7, W1-8 | senior-developer | W3-1…W3-4 | senior-developer |
| W0-2 | git | W1-6, W1-9, W1-10 | developer | W3-5…W3-7 | developer |
| W0-3 | agent-meta-manager | W2-1…W2-7 | developer | W4-1, W4-2, W5-2, W6-1 | developer |
| W4-3, W5-3, W6-2, W8-4 | tester | W5-1 | technical-writer | W7-1, W7-5 | knowledge-curator |
| W7-2, W7-3 | senior-developer | W7-4 | prompt-engineer | W8-1 | requirements |
| W8-2, W8-3 | developer | | | | |

> `pipeline_stages.implement = 3` = Stufe `implement` (frischer Subagent pro Task, zweistufiges
> Review `review-req` → `review-quality`, Ledger = Checkboxen dieser Datei, Skill `plan-ledger`).

---

## W0 — Definition, Entscheidungen, Freeze (kein Code)

**Verifikation W0 (erwartete Exit-Codes):** `git branch --list 'chore/docs-consolidation-w*'` → **0**;
`git log --oneline -20 -- scripts/lib/` → **0** (nur lesend). **Kein** `sync.py`-Lauf mit
Schreibwirkung, kein Commit von Fremdänderungen.
**Review W0:** `concept-reviewer` (Spec-Treue der Entscheidungs-Records) → `orchestrator`.
**Gate bei CHANGES_REQUESTED:** W0-1/W0-3/W0-6/W0-7 kehren in die Welle zurück; W0-2/W0-4 sperren
alle Folgewellen bis zur Auflösung.
**Rollback W0:** `git rm docs/plans/2026-09-25-docs-consolidation-*.md`, Branches löschen; kein
Code berührt, keine andere Welle invalidiert.

### W0-1: REC-OQ6 — `docs/INDEX.md` tracked (Ergebnis-Record, entschieden 2026-09-26)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq6.md`
**Interfaces:** Produces: **Ergebnis-Record** der Tracking-Entscheidung (**tracked**) +
Begründung + Folge für `.gitignore`. Consumes: Spec §11.2 **OQ6** (entschieden 2026-09-26),
`scripts/lib/spec_plan_scaffold.py:23`, `.meta-config/project.yaml:70`.
**Agent:** orchestrator · **Depends on:** W0-2 · **parallel_group:** — (sequenziell, OQ6-Ergebnis-Record; das Track-A-Gate ist **W0-4**)
**Ziel-AK (AC):** AC-20, AC-21 (Index-Writer-Vertrag), AC-12 (Index im Repo).
**Akzeptanz:** Record nennt die **bereits getroffene** Entscheidung (**tracked**), Entscheider,
Datum 2026-09-26 und die exakte `.gitignore`-Folge: **kein** `.gitignore`-Eintrag,
`.gitignore` bleibt unverändert. **Diese Task trifft die Entscheidung nicht**, sie dokumentiert
sie (Spec §11.2).
**Verifikation:** `git check-ignore -q docs/INDEX.md; echo $?` → **1** (nicht ignoriert). Die
gesicherte Entscheidung ist `tracked`, also ist **1 der Sollwert**; **0** (ignoriert) wäre ein
**Widerspruch zur Entscheidung** und ist im Record als solcher zu melden. **Kein**
entscheidungsabhängiger Offenstand mehr.
**Steps:**
- [ ] 1: Die getroffene Entscheidung aus Spec §11.2 OQ6 übernehmen: **tracked**; Traces aus
      `scripts/lib/spec_plan_scaffold.py:23` und `project.yaml:70` im Record belegen.
- [ ] 2: `.gitignore`-Folge festschreiben (**kein** Eintrag) und die verworfene Alternative
      (`untracked` wie `.claude/`) benennen.
- [ ] 3: Record schreiben inkl. „Folge für W3-6“ und des gewählten `index-mode`-Werts.
- [ ] 4: commit via `git`-Agent: `docs: record OQ6 index tracking decision`.

### W0-2: Design-Freeze, Contract-Liste, Branch-Scaffold

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md`
**Interfaces:** Produces: eingefrorene IC-Liste IC-01…IC-24, NFA-01…NFA-11, Startwelle je
V-Check, Branches `chore/docs-consolidation-w0`…`-w8`, Commit-Reihenfolge. Consumes: Spec §5, §8,
§9.2, §15.
**Agent:** git · **Depends on:** — · **parallel_group:** —
**Ziel-AK (AC):** Querschnittsanker AC-01…AC-41 (W0 trägt laut Spec §9.2 kein eigenes AC).
**Akzeptanz:** Record listet alle 24 IC mit Zielmodul und Welle, die 9 V-Checks mit Startwelle und
die 8 Wellen-Branches; `git branch --list 'chore/docs-consolidation-w*'` zeigt mindestens `w0`.
**Verifikation:** `git branch --list 'chore/docs-consolidation-w*'` → **0**;
`grep -c '^#### IC-' docs/specs/2026-09-25-repository-documentation-consolidation.md` → **24**.
**Steps:**
- [ ] 1: IC-/NFA-/V-/Wellen-Liste aus der Spec extrahieren und im Record spiegeln.
- [ ] 2: Branches `chore/docs-consolidation-w0`…`-w8` anlegen (ein Branch pro Welle, R16).
- [ ] 3: Commit-Reihenfolge und Merge-Regel („`git mv`-Wellen zuerst mergen“) festschreiben.
- [ ] 4: commit via `git`-Agent: `docs: freeze docs-consolidation contracts and wave branches`.

### W0-3: REC-OQ2 — `llms.txt` Hybrid (Ergebnis-Record, entschieden 2026-09-26)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq2.md`
**Interfaces:** Produces: **Ergebnis-Record** der Modusentscheidung + Eintrag in IC-22
`docs-consolidation.sources`. Consumes: Spec §11.2 **OQ2** (entschieden 2026-09-26), IC-08,
IC-22, `llms.txt:3-12`.
**Agent:** agent-meta-manager · **Depends on:** W0-2 · **parallel_group:** W0-PG-B
**Ziel-AK (AC):** AC-25, AC-40.
**Akzeptanz:** Record hält die **bereits getroffene** Entscheidung fest — `llms.txt` bleibt
**handgepflegt** (Handtext-Einleitung und Linkliste unverändert), generiert werden
**ausschließlich** `{{DOCS_PROVIDERS_BLOCK}}` und `{{DOCS_REPO_FACTS_BLOCK}}`; ein
**Vollgenerieren** der Datei ist **nicht** entschieden. `llms.txt` ist ein Wert von
`docs-consolidation.sources`; Prosa-Ton `llms.txt:3-12` bleibt erhalten. **Diese Task trifft
die Entscheidung nicht** — sie dokumentiert sie (Spec §11.2).
**Verifikation:** `grep -n 'llms.txt' docs/plans/2026-09-25-docs-consolidation-oq2.md` → **0**
(mindestens ein Treffer).
**Steps:**
- [ ] 1: Die getroffene Entscheidung aus Spec §11.2 OQ2 übernehmen: **Hybrid** — Handtext
      bleibt, generiert werden nur `{{DOCS_PROVIDERS_BLOCK}}` + `{{DOCS_REPO_FACTS_BLOCK}}`.
      Die verworfene Vollgenerierung **benennen, nicht wählen**.
- [ ] 2: Folge für `docs-consolidation.sources` (IC-22) festschreiben und den Folge-Edit in
      **W1-6** (Snippet-Bridge) und **W3-7** (Marker-Regionen, `llms.txt:5`) benennen.
- [ ] 3: Record schreiben (Entscheidung, Entscheider, Datum 2026-09-26, Gewähltes/Verworfenes).
- [ ] 4: commit via `git`-Agent: `docs: record OQ2 llms.txt hybrid decision`.

### W0-4: Track-A-Kollisionsgate (R3, R15)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-track-a-gate.md`
**Interfaces:** Produces: go/no-go-Freigabe für W1 und W2 + Liste der zuletzt von Track A
berührten `scripts/lib/`-Dateien. Consumes: Spec §2.3, §9.2 (R3), Git-Historie **von
`origin/main`** (nicht des Feature-Branches).
**Agent:** orchestrator · **Depends on:** W0-2 · **parallel_group:** W0-PG-B
**Ziel-AK (AC):** AC-07, AC-08 (Fixture-Kollision), AC-39 (Schema-Datei).
**Akzeptanz:** Der Record belegt den Track-A-Merge-Status **gegen `origin/main`** — nicht gegen
einen Feature-Branch: (a) `git ls-tree -d origin/main -- tests/fixtures/slimming-golden/` ergibt
einen Treffer (Verzeichnis in `main` vorhanden), (b) `git ls-tree origin/main --
tests/fixtures/docs_v1_fixtures.md` ist **leer**, (c) `tests/fixtures/docs_v1_fixtures.md`
existiert auch im Arbeitsbaum nicht. **Erst dieser Nachweis gegen `origin/main`** gilt als
Track-A-Merge; ohne ihn bleiben W1 und W2 gesperrt. Branch und `origin/main` müssen dabei
synchron sein (`git rev-list --left-right --count origin/main...HEAD` → `0 0`), damit der
Gate-Record nicht über einen veralteten Stand entscheidet. Inhaltlich unverändert geprüft wird
dieselbe Aussage wie bisher: Fixture-Verzeichnis in `main` vorhanden, V1-Fixture
`docs_v1_fixtures.md` nicht vorhanden.
**Verifikation:** `git fetch origin` → **0**; `git ls-tree -r --name-only origin/main --
tests/fixtures/slimming-golden/` → **nicht leer**; `git ls-tree origin/main --
tests/fixtures/docs_v1_fixtures.md` → **leer**; `ls tests/fixtures/docs_v1_fixtures.md` → **1**
(nicht vorhanden); `git rev-list --left-right --count origin/main...HEAD` → `0 0`.
**Ausdrücklich kein Merge-Nachweis:** `git log --oneline -20 --
tests/fixtures/slimming-golden/` (und `git log --oneline -20 -- scripts/lib/`) führen nur die
zuletzt von Track A berührten Dateien auf — sie sind **kein** Nachweis des Merges nach `main`.
Der Merge-Nachweis ist ausschließlich der `git ls-tree`-Befehl gegen `origin/main` oben.
**Steps:**
- [ ] 1: `git fetch origin`; dann `git ls-tree -d origin/main -- tests/fixtures/slimming-golden/`
      und `git ls-tree origin/main -- tests/fixtures/docs_v1_fixtures.md` auswerten (Nachweis
      **gegen `origin/main`**, nicht gegen den Feature-Branch) und `git rev-list --left-right
      --count origin/main...HEAD` → `0 0` (Stand-Synchronität) prüfen.
- [ ] 2: Track-A-Merge-Status **gegen `origin/main`** feststellen; bei offen **stoppen** und an
      `main_chat` eskalieren.
- [ ] 3: Record mit go/no-go und Rebase-Pflicht vor jedem Merge schreiben.
- [ ] 4: commit via `git`-Agent: `docs: record track-a collision gate for docs consolidation`.

### W0-6: REC-OQ8 — wer re-generiert `docs/INDEX.md` bei neuer Doku-Datei (Ergebnis-Record)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq8.md`
**Interfaces:** Produces: **Ergebnis-Record** des Workflow-Vertrags — **gewählt:**
deterministischer **Sync-/Validator-Lauf** (`sync.py` im Default-Sync, `--validate` als
`TEST_COMMAND`, `.meta-config/project.yaml:193`); **verworfen:** `pre-commit`-Hook,
CONTRIBUTING-Regel, Severity-Downgrade; **gewählter Umsetzungsschritt:** W3-6 (W3-7 braucht
keinen, da keine neue Doku-Datei entsteht).
Consumes: Spec §10, §11.2 **OQ8** (entschieden 2026-09-26), IC-05 (V2), IC-22.
**Agent:** orchestrator · **Depends on:** W0-2 · **parallel_group:** W0-PG-B
**Ziel-AK (AC):** AC-12, AC-38.
**Akzeptanz:** Der Record hält die **bereits getroffene** Entscheidung fest: Auslöser ist der
Sync-/Validator-Lauf, **kein** `pre-commit`-Hook und **keine** CONTRIBUTING-Regel. **V2 bleibt
ERROR** (Spec-Empfehlung), damit die Vertragsverletzung sichtbar bleibt; **kein** neues
`sync.py`-CLI-Flag (NG-4) und **kein** neuer Hook — der vorhandene Sync-Pfad genügt. **Diese Task
trifft die Entscheidung nicht**, sie dokumentiert sie (Spec §11.2).
**Verifikation:** `grep -n 'pre-commit\|CONTRIBUTING' docs/plans/2026-09-25-docs-consolidation-oq8.md`
→ **0** (mindestens ein Treffer). **Scharfung der Erwartung:** `pre-commit` und `CONTRIBUTING`
müssen im Record als **verworfene** Alternative erscheinen (die Spec-Empfehlung war der
`pre-commit`-Hook); der **Sync-/Validator-Lauf** muss als **gewählter** Weg erscheinen. Der
Treffer belegt also die Entscheidungsdokumentation, **nicht** eine Hook-Implementierung.
**Abgrenzung:** `index-mode` (IC-22, `docs-consolidation.index-mode`) ist **kein** Mechanismus
von OQ8 und gehört **nicht** in die Verifikationserwartung. Es ist der **IC-22-Rollback-Schalter**
(für W7, `index-mode: llm`); im OQ8-Record darf er allenfalls als dieser IC-22-Verweis genannt
werden, **nicht** als der gewählte Weg dieser Entscheidung.
**Steps:**
- [ ] 1: Die getroffene Entscheidung aus Spec §11.2 OQ8 übernehmen: Sync-/Validator-Lauf;
      die **verworfene** Spec-Empfehlung (`pre-commit`-Hook → `sync.py --dry-run`) und die
      Alternative CONTRIBUTING-Regel als **verworfen** benennen.
- [ ] 2: Entscheidung als Workflow-Vertrag festschreiben (Owner, Auslöser, Kosten).
- [ ] 3: Umsetzungsschritt in W3-6 referenzieren. **W3-7 braucht keinen Doku-Schritt** für
      OQ8: gewählt ist der Sync-/Validator-Lauf, also entsteht **kein** Hook, **keine**
      CONTRIBUTING-Regel und **keine** neue Doku-Datei (Spec §11.2) — der Vertrag lebt im
      W0-6-Record und in Spec §10.
- [ ] 4: commit via `git`-Agent: `docs: record OQ8 index regeneration contract`.

### W0-7: DEC-OQ1 — Wiki-Topics vs. `docs/guides/` (Produktentscheidung)

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq1.md`
**Interfaces:** Produces: Scope-Grenze für W5-3 (Annotation statt Inhaltsmigration) + Titel der
Folge-REQ. Consumes: Spec §11.1 OQ1, §3.3, FI-4.
**Agent:** orchestrator (Eskalation an `main_chat`) · **Depends on:** W0-2 · **parallel_group:** W0-PG-B
**Ziel-AK (AC):** AC-31.
**Akzeptanz:** Entscheidung **vor Abschluss von W5**; Inhaltsmigration ausgeschlossen (NG-1) und
als FI-4 Folge-REQ geführt.
**Verifikation:** `grep -n 'OQ1\|FI-4' docs/plans/2026-09-25-docs-consolidation-oq1.md` → **0**.
**Steps:**
- [ ] 1: Produktfrage an `main_chat` eskalieren (Spec-Owner für OQ1).
- [ ] 2: Antwort als Scope-Grenze festhalten: W5-3 annotiert **additiv**, migriert **nichts**.
- [ ] 3: Record schreiben inkl. Folge-REQ-Referenz FI-4.
- [ ] 4: commit via `git`-Agent: `docs: decide OQ1 wiki topics scope`.

---

## W1 — DocFacts, Renderer, Snippet-Bridge, Schema (rein additiv)

**Verifikation W1 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_doc_facts.py tests/test_doc_facts_expected.py tests/test_doc_renderer.py tests/test_docs_consolidation_migration.py -q` → **0**
- `python3 scripts/sync.py --dry-run` → **0**
- `python3 scripts/sync.py --validate` (= `TEST_COMMAND`, `.meta-config/project.yaml:193`) → **0**
- `python3 scripts/consistency-check.py` → **0** (V1–V9 existieren erst ab W2)
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (6/6 grün, AC-38)
- `git status --porcelain` zeigt **keine** Änderung an `README.md`, `llms.txt`, `ARCHITECTURE.md`
  (W1 ist additiv; der erste echte Datei-Diff entsteht in W3).
**Review W1:** Stufe 1 `validator` (AC-Treue) → Stufe 2 `code-reviewer` (Blast-Radius; Prüfpunkt:
kein Diff in `agents/`, `hooks/`, `commands/`, `config/*.yaml`).
**Gate bei CHANGES_REQUESTED:** Task zurück in dieselbe Kette; bei Befund an
`scripts/lib/config.py` oder `scripts/lib/consistency/*` zusätzlich Rebase gegen Track A.
**Rollback W1:** `docs-consolidation.enabled: false` (additiv-revert), Schema-Block entfernen,
Config-Keys entfernen, `git rm` der neuen `scripts/lib/doc_*.py`, `snippets/docs/`,
`config/doc-facts-expected.yaml` und der Testdateien. Kein Datei-Diff, keine andere Welle
invalidiert.

### W1-1: `doc_facts.py` Grundgerüst und `compute_doc_facts` (Key-Set)

**Files:** Create `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `compute_doc_facts(agent_meta_root, config, *, provider_config=None,
log=None) -> dict[str, str]` mit **exakt** 23 Schlüsseln; `HOOK_EXCLUDED_DIRS`,
`HOOK_EXCLUDED_SUFFIXES = ("-impl.sh",)`, `AGENT_HELPER_PREFIX`. Consumes:
`scripts/lib/roles.py:129` (`resolve_activation_gates`), `scripts/lib/config.py:1060-1064`
(`read_version`).
**Agent:** senior-developer · **Depends on:** W0-1, W0-4 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-01** (IC-01, IC-02) · **V-Check:** — (Key-Set-Invariant, Unit-Test)
**Akzeptanz:** `test_fact_key_set_exact` grün; alle Werte `str`; keine Exceptions; Verzeichnis-Hash
von `agent_meta_root` vor/nach identisch (kein Schreibzugriff).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py::test_fact_key_set_exact -q` → **0**.
**Steps:**
- [ ] 1: Test zuerst schreiben (fail, ImportError).
- [ ] 2: `doc_facts.py` mit den 23 IC-02-Schlüsseln implementieren. Die Suffix-Regel muss
      **Bindestrich** haben (Spec NF-12: `"_impl.sh"` hätte nichts gematcht und
      `DOCS_HOOKS_COUNT` wäre 13 statt 11 gelaufen).
- [ ] 3: Test laufen lassen (pass), Hash-Gleichheit des Baums beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add doc_facts module with exact fact key set`.

### W1-2: Skalarformeln und volatile-Markierung

**Files:** Modify `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: 13 Formel-Assertions; `volatile: true` ausschließlich für
`DOCS_SCENARIO_COUNT`; sechs `*_BLOCK`-Fakten. Consumes: W1-1.
**Agent:** senior-developer · **Depends on:** W1-1 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-02** (IC-02), **AC-03** (IC-02) · **V-Check:** — (Unit-Test)
**Akzeptanz:** `test_scalar_fact_formulas` (parametrisiert, **13** Assertions) und
`test_volatile_fact_absent_from_hybrid_files` grün. **Kein** Wert wird gegen eine im Test
hinterlegte Konstante geprüft (Spec NEW-8: der `xfail`-Snapshot ist entfernt; Sollzahlen stehen
ausschließlich in `config/doc-facts-expected.yaml`).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**.
**Steps:**
- [ ] 1: Formel-Tests schreiben (fail).
- [ ] 2: Formeln aus IC-02 implementieren; `DOCS_AGENTS_ACTIVE_COUNT` über `compute_active_roles`
      (IC-04), **nicht** `len(roles)` (F13/F21).
- [ ] 3: Volatile-Unterdrückung implementieren; Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: implement doc fact formulas and volatile marking`.

### W1-3: Fehlertoleranz und aktive Rollenmenge

**Files:** Modify `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `compute_active_roles(agent_meta_root, config, provider_config=None) -> set[str]`;
Fehlerpfad „Quelle fehlt → `\"\"` + `log.debug`, kein `SyncError`“. Consumes: W1-2,
`scripts/lib/agent_sync.py:548`.
**Agent:** senior-developer · **Depends on:** W1-2 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-04** (IC-01), **AC-05** (IC-04) · **V-Check:** **V5**
**Akzeptanz:** `test_missing_source_is_fail_soft` und
`test_se_role_excluded_by_gate_not_by_roles_list` grün; `se-component-requirements` ist **nicht**
im Ergebnis, weil `systems-engineering.enabled: false` (`.meta-config/project.yaml:12-13`).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`grep -n 'systems-engineering' .meta-config/project.yaml` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `compute_active_roles` = `roles:` ∩ Templates ∩ `resolve_activation_gates()` implementieren.
- [ ] 3: Fail-soft-Pfade implementieren; Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add fail-soft fact paths and gate-aware active roles`.

### W1-4: Staleness-Resolver

**Files:** Modify `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `compute_wiki_staleness(wiki_root, project_root) -> dict[str, str]` mit
`""` / `"missing-derived-from"` / `"stale-source"` / `"age-<n>d"`. Consumes: W1-3;
`knowledge/wiki/index.md:24` (Quelle wandert nach W4 mit → `docs/architecture/00-overview-full.md`, M-7).
**Agent:** senior-developer · **Depends on:** W1-3 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-10** (IC-03, Prüfung in W2-3), **AC-29(c)** · **V-Check:** **V7**
**Akzeptanz:** Resolver liefert die vier Werte; `status:stale-upstream` wird **maschinell**
extrahiert und nicht mehr manuell gepflegt; Quelle ist die **Langfassung**, nicht der
`ARCHITECTURE.md`-Stub (Spec A12: die Stub-Quelle verschwindet nach W4).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: Resolver implementieren (`mtime(derived-from) > derived-at` → `stale-source`).
- [ ] 3: Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add wiki staleness resolver`.

### W1-5: Unabhängige Sollwert-Quelle (R14)

**Files:** Create `config/doc-facts-expected.yaml`, `tests/test_doc_facts_expected.py`;
Modify `scripts/lib/doc_facts.py`
**Interfaces:** Produces: `load_expected_doc_facts(agent_meta_root, log=None) -> dict[str, str]`,
`compare_expected_doc_facts(computed, expected) -> list[dict[str, str]]` (sortiert nach `fact`,
`kind ∈ {mismatch, missing-in-expected}`). Consumes: W1-2.
**Agent:** senior-developer · **Depends on:** W1-2 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-36** (IC-23), **NFA-11** · **V-Check:** **V6** (`expected-mismatch`)
**Akzeptanz:** YAML enthält **elf** Einträge (Spec:1105); `test_expected_values_match` grün;
`test_mismatch_is_reported` liefert bei manipuliertem Wert **genau einen**
`kind == "expected-mismatch"` mit beiden Werten; `compute_doc_facts()` nimmt **keinen**
Sollwert-Parameter (keine Kopplung, kein Zirkel).
**Verifikation:** `python3 -m pytest tests/test_doc_facts_expected.py -q` → **0**;
`grep -c '^[A-Z_]*:' config/doc-facts-expected.yaml` → **11**.
**Steps:**
- [ ] 1: Tests schreiben (fail); manipulierter Sollwert als Negativ-Fixture im Test.
- [ ] 2: `config/doc-facts-expected.yaml` anlegen (11 Keys, `verified-at`, `verified-by: human`).
- [ ] 3: `load_/compare_` implementieren; Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add independent expected doc facts source`.

### W1-6: Snippet-Bridge und `DOCS_`-Platzhalter-Namespace

**Files:** Modify `scripts/lib/config.py`, `scripts/lib/consistency/placeholders.py`,
`tests/test_doc_facts.py`; Create `snippets/docs/repo-facts.md`, `agent-roster.md`,
`pipelines.md`, `hooks.md`, `providers.md`, `tier-presets.md`
**Interfaces:** Produces: `variables["DOCS_*_BLOCK"]` aus `snippets/docs/*.md` über den
**unveränderten** `_load_block_snippet` (`config.py:1842-1858`); `^DOCS_` in `_DYNAMIC_PREFIXES`
(`placeholders.py:128-131`). Consumes: W1-4, OQ2-Entscheidung (**Hybrid**, Spec §11.2; Record
W0-3).
**Agent:** developer · **Depends on:** W1-4, W0-3 · **parallel_group:** PG-1 / W1-A
**Ziel-AK (AC):** **AC-25** (IC-11), **AC-06** (IC-06) · **V-Check:** — (Unit-Test)
**Akzeptanz:** `test_docs_snippet_inlining_contract` und
`test_docs_prefix_registered_in_placeholders` grün; `QUALITY_PIPELINES_BLOCK` bleibt vorhanden
(`config.py:1882`); Ergänzung **nach** dem `snippets/security/`-Block (`:1923-1924`);
`DOCS_LANGUAGE`/`INTERNAL_DOCS_LANGUAGE` (`.meta-config/project.yaml:183-184`) bleiben unberührt
(R12); Snippets sind **frontmatter-behaftet**, Inlining-Output ist frontmatter-frei.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`ls snippets/docs/*.md | wc -l` → **6**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: Sechs Snippets mit eigenem Frontmatter anlegen; `config.py` additiv erweitern; `^DOCS_` registrieren.
- [ ] 3: Tests grün beobachten; `QUALITY_PIPELINES_BLOCK`-Regression gegenprüfen.
- [ ] 4: commit via `git`-Agent: `feat: add docs snippet bridge and DOCS_ placeholder namespace`.

### W1-7: `doc_renderer.py` — Marker-API

**Files:** Create `scripts/lib/doc_renderer.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `DOCS_BLOCK_RE`, `render_doc_fact_block(region, facts) -> str`,
`apply_fact_blocks(text, facts, log=None) -> str`. Consumes: W1-1 (Fakten), Muster
`scripts/lib/context.py:36-50` (Regionspaar, `count=1`).
**Agent:** senior-developer · **Depends on:** W1-1 · **parallel_group:** PG-1 / W1-B
**Ziel-AK (AC):** **AC-14**, **AC-15**, **AC-16**, **AC-27** (IC-07, IC-08) · **V-Check:** **V6**
**Akzeptanz:** `test_apply_fact_block_single_region`, `test_unbalanced_marker_is_noop_with_warning`,
`test_duplicate_region_first_only`, `test_output_independent_of_dict_order` grün; unbalancierte
Region → Rückgabe **byte-identisch** plus **genau ein** `log.warning`; erlaubte Regionsnamen
`facts|roster|pipelines|hooks|providers|version`; leerer Wert → `<!-- agent-meta:docs-empty: … -->`;
`docs-*` ist eigener Namespace neben `agent-meta:managed-*` (keine Kollision, IC-08).
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `DOCS_BLOCK_RE` + die drei Funktionen implementieren.
- [ ] 3: Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add doc renderer marker API`.

### W1-8: `doc_index.py` — Doku-Baum-Modell

**Files:** Create `scripts/lib/doc_index.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `build_index_model(project_root) -> dict` mit
`{'root', 'entries': [{'path','title','description','kind','depth'}]}`,
`EXCLUDED_DIR_SEGMENTS = {'archive','_archive','local-Inputs'}`, `DESCRIPTION_MAX_CHARS = 120`.
Consumes: W1-7.
**Agent:** senior-developer · **Depends on:** W1-7 · **parallel_group:** PG-1 / W1-B
**Ziel-AK (AC):** **AC-17** (IC-09, Modell-Anteil), **NFA-01** · **V-Check:** **V2** (ab W2-6)
**Akzeptanz:** zweimaliger Aufruf auf demselben Baum ⇒ **byte-identisches** Ergebnis; `archive/`
ausgeschlossen; Frontmatter-lose Datei → Dateiname als `title`, `—` als description; **keine**
erfundene Beschreibung; Sortierung `kind` dann `path` (NFA-02).
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: `build_index_model` implementieren — **einzige** Komponente mit Doku-FS-Semantik
      (kein Pfadlogik-Duplikat in `doc_facts.py`).
- [ ] 3: Determinismus beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add docs tree index model`.

### W1-9: Schema-Block `docs-consolidation` (M-11)

**Files:** Modify `config/project-config.schema.json`; Create `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: geschlossener Top-Level-Block `docs-consolidation` mit
`additionalProperties: false` und **sechs** Properties aus IC-22. Consumes: IC-22;
`config/project-config.schema.json:2058, :2073` (Selbstauskunft „geschlossene Unterobjekte als
Tippfehler-Wächter“), `:2425` (Wurzel permissiv).
**Agent:** developer · **Depends on:** W0-4 · **parallel_group:** PG-1 / W1-C
**Ziel-AK (AC):** **AC-39** (IC-17 M-11) · **V-Check:** — (Schema-Operation, Unit-Test)
**Akzeptanz:** `test_schema_block_present_and_closed` grün; **kein** Property-Name ist ein
Providername; `project.yaml` mit `docs-consolidation.enabled: true` validiert grün. M-11 ist
Konventions- und Autocomplete-Pflicht, **keine** Fehlerbehebung.
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`python3 -c "import json;json.load(open('config/project-config.schema.json'))"` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Block mit sechs Properties ergänzen.
- [ ] 3: Test grün beobachten; Validierung mit aktiviertem Key prüfen.
- [ ] 4: commit via `git`-Agent: `feat: declare docs-consolidation config block in schema`.

### W1-10: Additive Config-Keys und Absenz-Default

**Files:** Modify `.meta-config/project.yaml`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `docs-consolidation.{enabled,index-mode,checks.strict,sources,volatile-facts}`
in `.meta-config/project.yaml`; `enabled: true` **explizit** in agent-meta (NG-9).
`knowledge-engine.okf.index-mode` folgt erst in W7-2. Consumes: W1-8, IC-22, W0-3.
**Agent:** developer · **Depends on:** W1-8 · **parallel_group:** PG-1 / W1-B
**Ziel-AK (AC):** **AC-24** (IC-13, IC-22) · **V-Check:** alle (Common-Gate)
**Akzeptanz:** `test_disabled_flag_is_noop` und `test_absent_block_is_noop` grün; bei Abwesenheit
`false` (Präzedenz `scripts/lib/knowledge.py:127`); in Consumer-Projekten kein Schreibzugriff;
`checks.strict` bleibt in W1 **nicht** `true` (erst W3-4).
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**;
`grep -n 'docs-consolidation' .meta-config/project.yaml` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: Fünf additive Keys anlegen.
- [ ] 3: Tests grün beobachten; **kein** Sync-Lauf mit Schreibwirkung.
- [ ] 4: commit via `git`-Agent: `feat: add additive docs-consolidation config keys`.

---

## W2 — Checks V1–V7 (V1 startet WARNING)

**Verifikation W2 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_doc_facts.py tests/test_doc_facts_expected.py -q` → **0**
- `python3 scripts/consistency-check.py` → **0** (V1 erscheint als **WARNING**)
- `python3 scripts/consistency-check.py --strict` → **1, planmäßig** — die **einzigen** Findings
  sind `docs.no_manual_counts`-V1-WARNINGS. Begründung Spec A11 (V1 startet WARNING) und
  `scripts/consistency-check.py:23-26` („warnings allowed unless `--strict`“). Dieser Exit-Code 1
  ist in W2 **erwartet** und wird im Review-Protokoll als *by design* markiert; der Gate-Nachweis
  `--strict == 0` erfolgt in W3.
- `python3 scripts/sync.py --validate` → **0** (`checks.strict` fehlt ⇒ Default `false` ⇒ keine Errors)
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (6/6)
**Review W2:** `tester` (Fixture-Treue) → `code-reviewer` → `validator` (AC-07…AC-13, AC-36).
**Gate bei CHANGES_REQUESTED:** jeder Fehlalarm in der Positiv-Fixture ⇒ `concept-reviewer`; jeder
nicht spezifizierte Treffer ⇒ R4-Eskalation an `main_chat`, Startseverity bleibt WARNING.
**Rollback W2:** `docs-consolidation.checks.strict: false`; da die Checks an
`docs-consolidation.enabled` gebunden sind, ist der vollständige Rollback `enabled: false`
(Fail-off ⇒ V1–V7 No-op). `git rm tests/fixtures/docs_v1_fixtures.md`;
`scripts/lib/consistency/docs.py` und `scripts/consistency-check.py` via `git checkout`.

### W2-1: V1a/V1b `check_no_manual_counts` + Positiv-Fixture

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`;
Create `tests/fixtures/docs_v1_fixtures.md`
**Interfaces:** Produces: `check_no_manual_counts(root, config=None) -> list[Finding]` mit zwei
disjunkten Branches und `branch`-Attribut `V1a`/`V1b`; Suppressionsregeln 1–4 (§5.1.1).
Consumes: W1-4, W0-4 (Track-A-Merge als Vorbedingung für die Fixture).
**Agent:** developer · **Depends on:** W1-6, W0-4 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-07**, **AC-08** (IC-05, §5.1.1) · **V-Check:** **V1a**, **V1b**
**Akzeptanz:** Fixture mit **genau vier** wörtlichen Zitatzeilen (Zeilen 1–4: `## Agent Roster — 74
Generic Agents`, `## Hooks (7 hooks, propagated to all providers)`,
`  ai-providers.yaml          # 6 provider configs (Claude, Gemini, Opencode, Continue, Copilot,
Mammouth)`, `VERSION                      # Current version (v1.0.0)`). Ergebnis = **genau 4**
Findings, `severity=WARNING`, `check="docs.no_manual_counts"`, `line` 1/2/3 = `V1a`, `line` 4 =
`V1b`. Die drei Suppressionsfälle (Marker-Region, `docs-exempt`, Fenced-Code) erzeugen **kein**
Finding; die Gegenprobe `| Agents | 74 |` außerhalb jeder Region erzeugt **genau eines**. Nach
`checks.strict: true` sind dieselben vier Befunde `Severity.ERROR`.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`wc -l < tests/fixtures/docs_v1_fixtures.md` → **4**.
**Steps:**
- [ ] 1: Fixture (Positiv + Exempt + Gegenprobe) anlegen; Tests schreiben (fail).
- [ ] 2: V1a (Zahl-Token ohne `\d+\.\d+` + Nomen auf derselben Zeile) und V1b (Versions-Literal)
      implementieren. Die Rev.-0.1-Regex wird **nicht** verwendet (sie matchte keine Fundstelle).
- [ ] 3: Suppressionen implementieren; Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add V1 manual count detection with fixtures`.

### W2-2: V3 `check_internal_links`

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_internal_links(root, config=None) -> list[Finding]`; prüft nur
relative repo-interne Pfade. Consumes: W2-1.
**Agent:** developer · **Depends on:** W2-1 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-09** (IC-05) · **V-Check:** **V3**
**Akzeptanz:** `test_v3_flags_dead_howto_links` grün: `README.md:721-723` (Links auf
`howto/setup/`, `howto/features/`) liefert ≥ 1 `Finding(severity=ERROR,
check="docs.internal_links", file="README.md")`. `http(s)://`, `mailto:` und `#anchor` werden
**nicht** geprüft (R6). Die Behebung erfolgt in W8-2.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`python3 scripts/consistency-check.py --strict` → **1, planmäßig** (V1-WARNINGS **plus**
V3-ERROR auf `README.md:721-723`, das erst W8-2 behebt — im Review als erwartet markieren).
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: V3 implementieren; Scope `docs/**` + `README.md` + `llms.txt`.
- [ ] 3: Test grün beobachten; Fehlalarm-Probe auf `http(s)://` und Anker.
- [ ] 4: commit via `git`-Agent: `feat: add V3 internal link check`.

### W2-3: V7 `check_wiki_staleness`

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_wiki_staleness(root, config=None) -> list[Finding]`, Severity
**WARNING**. Consumes: W1-4 (`compute_wiki_staleness`).
**Agent:** developer · **Depends on:** W2-2 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-10** (IC-05) · **V-Check:** **V7**
**Akzeptanz:** `test_v7_missing_and_stale_derived_from` grün: `type: Architecture` **ohne**
`derived-from` ⇒ Finding; `derived-from` mit `mtime(Quelle) > derived-at` ⇒ Finding nennt
`stale-source`. Die Behebung (Annotation) erfolgt in W5-3.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`python3 scripts/consistency-check.py` → **0** (nur WARNINGs).
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: V7 als dünne Adapter-Schicht auf W1-4 implementieren.
- [ ] 3: Test grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add V7 wiki staleness check`.

### W2-4: V5 `check_role_generation_parity` (gate-bewusst)

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_role_generation_parity(root, config=None) -> list[Finding]`;
Severity **ERROR**, sobald `systems-engineering.enabled: true`, sonst **WARNING**. Consumes: W1-3.
**Agent:** developer · **Depends on:** W2-3 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-11** (IC-05) · **V-Check:** **V5**
**Akzeptanz:** `test_v5_severity_depends_on_se_gate` grün; Vergleichsmenge ist
`compute_active_roles()` (IC-04), **nicht** der `roles:`-Listeninhalt (F21-Dauerfehlalarm, NG-8).
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: V5 mit Gate-Auswertung implementieren.
- [ ] 3: Test grün beobachten; Ist-Zustand (F13) muss **WARNING** sein.
- [ ] 4: commit via `git`-Agent: `feat: add V5 gate-aware role parity check`.

### W2-5: V6 `check_docs_facts_fresh` inkl. Sollwert-Vergleich

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts_expected.py`
**Interfaces:** Produces: `check_docs_facts_fresh(root, config=None) -> list[Finding]` mit
`kind ∈ {handedit, expected-mismatch, missing-in-expected}`; `missing-in-expected` = **WARNING**,
die anderen **ERROR**. Consumes: W1-5, W2-4.
**Agent:** developer · **Depends on:** W2-4 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-36** (IC-23, R14) · **V-Check:** **V6**
**Akzeptanz:** `test_mismatch_is_reported` grün: manipulierter Sollwert ⇒ **genau ein** Finding
`severity=ERROR, kind="expected-mismatch"` **obwohl** der gerenderte Block exakt
`compute_doc_facts()` entspricht — der Nachweis, dass der Kreis `doc_facts → Renderer → V6`
gebrochen ist (R14).
**Verifikation:** `python3 -m pytest tests/test_doc_facts_expected.py -q` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: V6 mit beiden Vergleichsachsen implementieren.
- [ ] 3: Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add V6 freshness check with expected-value axis`.

### W2-6: V2 `check_docs_index_completeness` und V4-Erweiterung

**Files:** Modify `scripts/lib/consistency/docs.py`, `tests/test_doc_facts.py`
**Interfaces:** Produces: `check_docs_index_completeness(root, config=None) -> list[Finding]`;
`check_readme_docs_index` generalisiert von `docs/api/*.md` (`:111`) auf den gesamten `docs/`-Baum
bei **unveränderter** Signatur und Severity. Consumes: W2-5, W1-8.
**Agent:** developer · **Depends on:** W2-5 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-12** (IC-05) · **V-Check:** **V2**, **V4**
**Akzeptanz:** `test_v2_missing_page` grün: eine getrackte `docs/**/*.md` außerhalb `archive/`, die
in `docs/INDEX.md` fehlt ⇒ **ERROR**; `docs/INDEX.md` selbst und `archive/`-Pfade ⇒ **kein**
Finding. Die bisherige Teilmenge `docs/api/*.md` bleibt eine echte Teilmenge der neuen Prüfung.
**Spec-Treue:** §9.1 führt AC-12 auf W3; die **Implementierung** liegt hier (Fixture-Ebene, damit
`scripts/lib/consistency/docs.py` nicht von zwei parallelen Ketten geschrieben wird), der
**E2E-Nachweis gegen das reale `docs/INDEX.md`** in W3-6.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: V2 implementieren; V4 generalisieren.
- [ ] 3: Tests grün beobachten; Szenario-Asserts 50–56 **nicht** anfassen (NG-10).
- [ ] 4: commit via `git`-Agent: `feat: add V2 index completeness and generalize V4`.

### W2-7: Registrierung, Common-Gate und Exit-Codes

**Files:** Modify `scripts/lib/consistency/docs.py`, `scripts/consistency-check.py`,
`tests/test_doc_facts.py`
**Interfaces:** Produces: Registrierung V1…V9 mit `check="docs.<name>"`; Common-Gate (No-op, wenn
`docs-consolidation.enabled != true`); unveränderter Exit-Code-Vertrag. Consumes: W2-6, W1-10.
**Agent:** developer · **Depends on:** W2-6 · **parallel_group:** PG-2 / W2
**Ziel-AK (AC):** **AC-13** (IC-05), **AC-24** · **V-Check:** alle
**Akzeptanz:** `test_exit_codes_unchanged_with_new_checks` grün: 0 Errors → Exit **0**, genau 1
Error → Exit **1**, Skriptfehler → Exit **2**; bestehende Exit-Code-Doku
(`scripts/consistency-check.py:23-26`) bleibt gültig; in allen Szenario-Fixtures sind V1–V9
**vollständig No-op** (AC-38). Die bestehenden drei Checks
(`check_sync_cli_docs` `:9`, `check_ui_help_mappings` `:47`, `check_readme_docs_index` `:100`)
bleiben in Signatur und Severity unverändert.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`python3 scripts/consistency-check.py` → **0**;
`bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Checks registrieren; Common-Gate als erste Bedingung in jeden Check einziehen.
- [ ] 3: Tests grün beobachten; Szenario-Lauf beobachten.
- [ ] 4: commit via `git`-Agent: `feat: register docs checks behind fail-off common gate`.

---

## W3 — Generator, Stage, Drift-Store, Index-Erzeugung

**Verifikation W3 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_doc_renderer.py tests/test_generated_file_drift_docs.py -q` → **0**
- `python3 scripts/sync.py --dry-run` → **0**, `written` nur als `would-update`
- `python3 scripts/sync.py --check` → **planmäßig 1** im Intervall W3-4…W3-6 (V1/V2/V6 noch rot;
  Spec §6(b): `--check`/`--validate` *dürfen* ab W3 bei V1/V2/V3/V6 nicht grün sein), **0** ab W3-7
- `python3 scripts/consistency-check.py --strict` → **0 ab W3-7** (Pflicht ab W3, Spec §10)
- `python3 scripts/sync.py --validate` (= `TEST_COMMAND`) → **0 nach W3-7**
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (6/6, AC-38: `54:26-27` findet Datei
  **und** `File-based index fallback`; `55:24-25` dito; `56:31` findet Datei; `50:32` findet Datei;
  `51:32` und `52:44` finden **keine** `docs/INDEX.md`)
- `grep -c 'Repo version:' ARCHITECTURE.md` → **0** nach W3-7 (F4, zweite Fundstelle)
**Review W3:** `code-reviewer` (Stage-Reihenfolge, Doppel-Writer-Risiko B2) → `validator`
(AC-20…AC-22, AC-38) → `concept-reviewer` (Besitzregel IC-13).
**Gate bei CHANGES_REQUESTED:** bricht der Scaffold-Guard ein Szenario, geht W3-3 zurück; eine
Umkehr der Stage-Reihenfolge (IC-12) ist ein **Stopp** mit Eskalation an `main_chat` (Spec A4).
**Rollback W3:** `git rm docs/INDEX.md`; `docs-consolidation.enabled: false`; `checks.strict`
zurück auf `false`; Marker-Regionen aus `README.md`/`llms.txt`/`ARCHITECTURE.md` entfernen;
`doc_renderer.py`, `doc_index.py`, `sync_pipeline.py`, `spec_plan_scaffold.py`,
`generated_file_drift.py` via `git checkout`. `docs/architecture/INDEX.md` entsteht erst in W4-3
und ist vom W3-Rollback **nicht** betroffen.

### W3-1: Schreib-, Idempotenz- und `dry_run`-Vertrag

**Files:** Modify `scripts/lib/doc_renderer.py`, `scripts/lib/doc_index.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `sync_docs_consolidation(agent_meta_root, project_root, config,
provider_config, log, dry_run) -> {'written','unchanged','skipped'}` inkl. Besitzregel (IC-13).
Consumes: W1-7, W1-8, W1-10.
**Agent:** senior-developer · **Depends on:** W1-10 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-23**, **AC-26** (IC-13) · **V-Check:** **V6**
**Akzeptanz:** `test_dry_run_no_writes` grün (null Dateisystem-Schreibvorgänge, `written` listet
Kandidaten, `knowledge/wiki/log.md` unverändert); `test_no_docs_dir_is_skipped_not_created` grün
(kein `mkdir` in Fremdprojekten); Zielinhalt == Istinhalt ⇒ `unchanged` **ohne** `write_checked`;
`enabled != true` ⇒ `log.skip("docs-consolidation", "disabled in project.yaml")` ohne jeden
Schreibzugriff. Besitzregel: der Generator überschreibt **nie** eine Datei, die ein anderer Writer
legitim geschrieben hat.
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `sync_docs_consolidation` mit Besitzregel und `dry_run`-Pfad implementieren.
- [ ] 3: Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add docs consolidation writer contract`.

### W3-2: `docs/INDEX.md`-Volltext, Fact-Hash-Footer, Volatile-Sektion

**Files:** Modify `scripts/lib/doc_renderer.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `render_docs_index(index_model, facts) -> str` nach IC-10; Footer
`facts-hash: <16 hex>` + `generator: doc-indexer/1` (IC-14). Consumes: W3-1, W1-8.
**Agent:** senior-developer · **Depends on:** W3-1 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-17**, **AC-18**, **AC-03** (IC-10, IC-14) · **V-Check:** **V2**, **V6**
**Akzeptanz:** `test_index_deterministic_and_archive_excluded` und
`test_footer_has_no_timestamp` grün; Regex `\d{4}-\d{2}-\d{2}` auf dem generierten Footer-Bereich
findet **keinen** Treffer; `docs-volatile` steht als **letzte** Sektion **vor** dem Footer; zwei
Renderings, die sich **nur** in `DOCS_SCENARIO_COUNT` unterscheiden ⇒ **identischer** `facts-hash`;
jeder `docs/**/*.md`-Pfad (ohne `archive/`, `_archive/`) genau einmal, `docs/INDEX.md` nie.
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `render_docs_index` + Hash-Algorithmus implementieren (SHA-256 über sortierte
      **nicht-volatile** Fakten, 16 Hex-Zeichen, kein Zeitstempel, kein absoluter Pfad).
- [ ] 3: Tests grün beobachten; Diff-Minimalität stichprobenartig prüfen.
- [ ] 4: commit via `git`-Agent: `feat: render full docs index with stable fact hash`.

### W3-3: Scaffold-Guard und Besitzregel

**Files:** Modify `scripts/lib/spec_plan_scaffold.py`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `is_file_index_skeleton(text) -> bool`,
`_FILE_INDEX_SKELETON_MARKER = "File-based index fallback"` (F20); `DEFAULT_FALLBACK_INDEX` bleibt
identisch (`:23`), `_FILE_INDEX_SKELETON` (`:24`) bleibt identisch. Consumes: W3-2, IC-15.
**Agent:** senior-developer · **Depends on:** W3-2 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-21** (IC-15, IC-13) · **V-Check:** **V4**
**Akzeptanz:** `test_skeleton_mode_preserves_scaffold` und
`test_ke_authoritative_writes_no_index` grün; bei `index-mode: skeleton` bleibt das Skeleton
**immer** unangetastet; bei `resolve_index_mode() == "knowledge-engine"` (Szenario 52) wird **kein**
`docs/INDEX.md` geschrieben, Eintrag in `skipped` + `log.note` mit Grund. Der Generator schreibt
**nie** einen Skeleton.
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**;
`bash tests/scenarios/run.sh 52 54 55 56` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `is_file_index_skeleton` implementieren; Generator ruft es **vor** dem Schreiben.
- [ ] 3: Tests grün beobachten; vier Szenarien beobachten.
- [ ] 4: commit via `git`-Agent: `feat: guard scaffold skeleton against docs index writer`.

### W3-4: Stage-Reihenfolge und `checks.strict`

**Files:** Modify `scripts/lib/sync_pipeline.py`, `.meta-config/project.yaml`, `tests/test_doc_renderer.py`
**Interfaces:** Produces: `_sync_stage_docs_consolidation(...)` (IC-12); Reihenfolge
Drift-Scan (`:587-620`) → Knowledge/Scaffold (`:922-945`, `:929`, `:935`) → **Docs** →
Hash-Capture (`:1090-1099`) → Auto-Commit-Allowlist (`:1102`); `docs-consolidation.checks.strict: true`.
Consumes: W3-3.
**Agent:** senior-developer · **Depends on:** W3-3 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-22** (IC-12) · **V-Check:** **V1** (Severity-Wechsel WARNING → ERROR)
**Akzeptanz:** `test_stage_order_after_scaffold` und `test_ke_index_stays_authoritative` grün;
`checks.strict: true` gesetzt; V1 wechselt von WARNING auf ERROR. **Keine** Interaktion mit
`_sync_stage_auto_commit_allowlist` (`sync_pipeline.py:1102-1117` liest den Drift-Store nicht —
R18 analysiert und nicht zutreffend).
**Verifikation:** `python3 -m pytest tests/test_doc_renderer.py -q` → **0**;
`grep -n 'checks.strict' .meta-config/project.yaml` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Stage-Funktion unmittelbar nach `scaffold_spec_plan_dirs` einhängen; `checks.strict: true`.
- [ ] 3: Tests grün beobachten; `--validate` im Intervall als erwartet rot markieren.
- [ ] 4: commit via `git`-Agent: `feat: wire docs stage after scaffold and enable strict checks`.

### W3-5: Drift-Store für Doku-Dateien

**Files:** Modify `scripts/lib/generated_file_drift.py`, `tests/test_generated_file_drift_docs.py`
**Interfaces:** Produces: `DOCS_GENERATED_RELS = ("docs/INDEX.md","docs/architecture/INDEX.md")`,
`DOCS_FACT_BLOCK_HOSTS = ("README.md","llms.txt","ARCHITECTURE.md")`, `DOCS_MARKER_KEY_SUFFIX =
"#docs:"`; Store-Key `<rel>#docs:<region>`; Allowlist-Match gegen den **Basis-Pfad**.
Consumes: W3-4, IC-16.
**Agent:** developer · **Depends on:** W3-4 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-19**, **AC-37** (IC-16) · **V-Check:** — (Drift-Store, Unit-Test)
**Akzeptanz:** `test_marker_body_only`, `test_no_backup_for_hash_key` und
`test_allowlist_matches_base_path` grün: Handprosa erzeugt **kein** Finding; ein Finding mit
`provider == "docs-consolidation"` und Pfad `README.md#docs:facts` erscheint; `apply_fact_blocks()`
überschreibt die editierte Region **nicht** (NFA-05); **keine** Datei namens `README.md#docs:facts`
entsteht; `allow-edits: ["README.md"]` unterdrückt den Marker-Body-Drift. Scan **und** Capture
werden symmetrisch ergänzt. Kein Eintritt in `_iter_managed_files` (`:240-310`).
**Verifikation:** `python3 -m pytest tests/test_generated_file_drift_docs.py tests/test_generated_file_drift.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: Doku-Pfade in Scan **und** Capture ergänzen; `is_allowlisted` (`:82-84`) gegen den
      Basis-Pfad matchen.
- [ ] 3: Tests grün beobachten; bestehende Drift-Tests mitlaufen lassen.
- [ ] 4: commit via `git`-Agent: `feat: track docs files in generated file drift store`.

### W3-6: `docs/INDEX.md` tracked, Erstgenerierung, OQ6/OQ8-Umsetzung

**Files:** Create `docs/INDEX.md`; Modify `.meta-config/project.yaml`, `README.md`,
`tests/test_doc_renderer.py` — **kein** `.gitignore`-Eintrag (OQ6 entschieden: `tracked`)
**Interfaces:** Produces: getrackte, 100 % generierte `docs/INDEX.md`; OQ6-Folge: `.gitignore`
bleibt **unverändert**; OQ8-Workflow-Vertrag (**Sync-/Validator-Lauf**, kein Hook) gemäß W0-6.
Consumes: W3-5, W0-1, W0-6, W2-6.
**Agent:** senior-developer · **Depends on:** W3-5, W0-1, W0-6 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-20**, **AC-12** (E2E), **AC-38** · **V-Check:** **V2**, **V4**
**Akzeptanz:** `test_skeleton_replaced_once` grün: Skeleton wird **einmalig** ersetzt
(`log.action("UPDATE","docs/INDEX.md",…)` genau einmal), zweiter Lauf meldet `unchanged` mit
**null** Schreibvorgängen; `git check-ignore -q docs/INDEX.md` → **1** (entschieden: `tracked`);
V2 und V4
sind gegen das reale `docs/INDEX.md` grün; `docs/architecture/INDEX.md` wird in W3 **nicht**
erzeugt (W4-3), die Datei erscheint daher noch nicht im Index.
**Verifikation:** `python3 scripts/sync.py --check` → **0**;
`git check-ignore -q docs/INDEX.md; echo $?` → **1**;
`bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**.
**Steps:**
- [ ] 1: E2E-Test schreiben (fail).
- [ ] 2: Sync mit `enabled: true` ⇒ `docs/INDEX.md` erzeugen; OQ6-Folge anwenden (kein
      `.gitignore`-Eintrag); OQ8-Vertrag umsetzen — der Sync-/Validator-Lauf ist der Auslöser,
      **kein** Hook und keine Doku-Regel.
- [ ] 3: Tests grün beobachten; zweiten Lauf auf `unchanged` beobachten.
- [ ] 4: commit via `git`-Agent: `feat: generate and track docs index`.

### W3-7: Marker-Regionen in `README.md`, `llms.txt`, `ARCHITECTURE.md`

**Files:** Modify `README.md`, `llms.txt`, `ARCHITECTURE.md`
**Interfaces:** Produces: 11 Handzahlen (F1, F2, F3 ×2, F4 ×2, F14 ×3, F22 ×2) durch
`agent-meta:docs-*-Regionen` ersetzt — `README.md:381-390` (Überschrift **und** Preset-Tabelle,
`concept-driven` ergänzen), `README.md:479-489` (8 Pipelines, `concept-driven-dev` ergänzen,
`se-cascade` als deaktiviert kennzeichnen), `README.md:501` (`DOCS_HOOKS_COUNT`),
`README.md:688-696` (`DOCS_DOD_PRESET_COUNT`, `DOCS_TIER_PRESET_COUNT`, `DOCS_HOOKS_1GENERIC_COUNT`),
`README.md:734` (`DOCS_VERSION`), `ARCHITECTURE.md:3` (Stale-Deklaration wandert in W4-1 mit),
`llms.txt:5` (Proverbenamen-Liste). **Hybrid-Scope (OQ2, Spec §11.2):** in `llms.txt` werden
**ausschließlich** `{{DOCS_PROVIDERS_BLOCK}}` und `{{DOCS_REPO_FACTS_BLOCK}}` generiert —
Handtext-Einleitung und Linkliste bleiben handgepflegt, **kein** Vollgenerieren. Consumes:
W3-6, W1-6 (Snippets), W0-3 (OQ2-Record, **Hybrid**).
**Agent:** developer · **Depends on:** W3-6 · **parallel_group:** PG-2 / W3
**Ziel-AK (AC):** **AC-40** (Teil: `README.md:690`, `llms.txt:5`), **AC-07** (Wirkung: V1 wird grün)
· **V-Check:** **V1a**, **V1b**, **V6**
**Akzeptanz:** `python3 scripts/consistency-check.py --strict` → **0** (kein `docs.*`-Finding);
`python3 scripts/sync.py --check` → **0**; `grep -c 'Repo version:' ARCHITECTURE.md` → **0**;
zweimaliger Sync ⇒ `unchanged` für alle drei Dateien (kein Diff-Churn, R1). Kreuz-Rendering ist
verboten: `DOCS_HOOKS_COUNT` **nur** in `:501`, `DOCS_HOOKS_1GENERIC_COUNT` **nur** in `:696`
mit dem verpflichtenden Klammerzuschlag `(+2 *-impl.sh helpers)`.
**Verifikation:** siehe Akzeptanz; zusätzlich `python3 -m pytest tests/test_doc_facts.py -q` → **0**
(V1-Fixture-Zeilen bleiben als Positiv-Fixture bestehen).
**Steps:**
- [ ] 1: Regionen `roster|pipelines|hooks|providers|version|facts` einführen (IC-08-Namensraum,
        getrennt von `agent-meta:managed-*`).
- [ ] 2: Snippets einbinden; `concept-driven-dev`-Zeile ergänzen; `se-cascade` als deaktiviert
        kennzeichnen; Prose außerhalb der Regionen unverändert lassen (NG-1).
- [ ] 3: `--check`/`--strict` beobachten; Idempotenz beobachten.
- [ ] 4: commit via `git`-Agent: `docs: replace manual counts with generated doc fact blocks`.

---

## W4 — Architektur-Konsolidierung (`git mv` + Stub)

**Verifikation W4 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**
- `python3 scripts/sync.py --validate` → **0**
- `python3 scripts/consistency-check.py --strict` → **0** (V3 grün)
- `test ! -e ARCHITECTURE.full.md` → **0**; `test -e docs/architecture/00-overview-full.md` → **0**
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**
**Review W4:** `code-reviewer` (Diff ist **ausschließlich** R+A) → `validator` (AC-28-Teil, AC-29).
**Gate bei CHANGES_REQUESTED:** jeder Inhalts-Diff in einer verschobenen Datei ⇒ **Stopp** (NG-1);
`git log -M --follow` muss reine Renames zeigen (AC-28).
**Rollback W4:** `git mv docs/architecture/00-overview-full.md ARCHITECTURE.full.md`;
`ARCHITECTURE.md` via `git checkout`; additive Stale-Zeile entfernen; `docs/architecture/INDEX.md`
entfernen; `docs/INDEX.md` neu generieren.

### W4-1: `git mv` Langfassung + wandernde Stale-Deklaration (M-1, M-7)

**Files:** Move `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` (via `git mv`)
**Interfaces:** Produces: Langfassung an kanonischem Ort; **additive** Stale-Deklaration
(`Repo version:` / `last substantively reviewed`) wandert mit. Consumes: M-1, M-7, IC-18.
**Agent:** developer · **Depends on:** W3-6 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-28** (Teil, M-1), **AC-29(b)** (M-7) · **V-Check:** **V3**
**Akzeptanz:** `git log -M --follow --name-status` zeigt **R100** ohne Inhalts-Diff; die
Stale-Deklaration steht in der Langfassung; `ARCHITECTURE.full.md` existiert **nicht** mehr.
**Verifikation:** `git log -M -1 --name-status` → **R100**;
`grep -c 'Repo version:' docs/architecture/00-overview-full.md` → **1**;
`test ! -e ARCHITECTURE.full.md` → **0**.
**Steps:**
- [ ] 1: `git mv` ausführen; Byte-Identität des Inhalts belegen.
- [ ] 2: Stale-Deklaration additiv in die Langfassung eintragen.
- [ ] 3: `git log -M` beobachten.
- [ ] 4: commit via `git`-Agent: `docs: move architecture longform into docs tree`.

### W4-2: `ARCHITECTURE.md` als generierter Stub (M-2, IC-18)

**Files:** Modify `ARCHITECTURE.md` (84 Z → Stub)
**Interfaces:** Produces: Titel, generierter Diagramm-Index (`docs/architecture/*.md` +
`docs/concepts/viz-logging-mcp.md` + `docs/concepts/a2a-handoff-protocol.md`, heute `:8-20`),
Pointer auf `docs/architecture/INDEX.md` und `docs/architecture/00-overview-full.md`, **keine**
eigene Architektur-Prose, **keine** `Repo version:`-Zeile. Consumes: W4-1.
**Agent:** developer · **Depends on:** W4-1 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-29(a)** (IC-18) · **V-Check:** **V3**
**Akzeptanz:** `llms.txt:24`-Link auf `ARCHITECTURE.md` bleibt gültig (T-4-B — „Löschen bricht
Deeplinks“); keine eigene Prosa im Stub.
**Verifikation:** `grep -c 'Repo version:' ARCHITECTURE.md` → **0**; `wc -l < ARCHITECTURE.md` → **< 84**;
`python3 scripts/consistency-check.py --strict` → **0**.
**Steps:**
- [ ] 1: Stub-Inhalt nach IC-18 entwerfen.
- [ ] 2: `ARCHITECTURE.md` ersetzen; Linkziele prüfen.
- [ ] 3: V3 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: reduce ARCHITECTURE.md to generated stub`.

### W4-3: `docs/architecture/INDEX.md` und AC-29-Nachweis

**Files:** Create `docs/architecture/INDEX.md`; Modify `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: Teil-Vorschau auf denselben Doku-Baum (IC-10(d));
`test_architecture_stub_shape`, `test_stale_declaration_moved_with_longform`. Consumes: W4-2, W1-4.
**Agent:** tester · **Depends on:** W4-2 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-29** (IC-18, IC-03, M-7), **AC-28** (Teil) · **V-Check:** **V3**, **V7**
**Akzeptanz:** AC-29 inkl. Teil (c): `compute_wiki_staleness()` liefert für
`knowledge/wiki/concepts/architecture.md` mit `derived-from: docs/architecture/00-overview-full.md`
einen **auswertbaren** Wert (kein `missing-derived-from`) — der Wert wird in **W5-3** gesetzt;
W4-3 stellt den Test so auf, dass er ab W5-3 grün ist und den Zwischenzustand als erwarteten
Befund dokumentiert.
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`python3 scripts/consistency-check.py --strict` → **0** (V3).
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `docs/architecture/INDEX.md` generieren lassen; Test auf W5-3 vorbereiten.
- [ ] 3: Tests bzw. erwarteten Zwischenbefund beobachten; `--validate` beobachten.
- [ ] 4: commit via `git`-Agent: `test: cover architecture stub shape after move`.

---

## W5 — Guides-Auflösung und Wiki-Annotation

**Verifikation W5 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**
- `python3 scripts/sync.py --validate` → **0**
- `python3 scripts/consistency-check.py --strict` → **0** (V7 grün nach der Annotation)
- `test ! -e howto` → **0**; `test ! -e docs/howto` → **0**
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**
**Review W5:** `code-reviewer` (Additiv-Garantie) → `knowledge-linter` (Frontmatter/OKF) →
`validator` (AC-28-Teil, AC-31).
**Gate bei CHANGES_REQUESTED:** jede **gelöschte** Zeile außer der Ersetzung eines bestehenden
`status:`-Werts ⇒ **Stopp** (AC-31-Additivität).
**Rollback W5:** beide `git mv` zurück; `docs/howto/` wiederherstellen; Annotationen additiv
revertieren (je annotierter Wiki-Seite `git checkout`, commitweise rückwärts).

### W5-1: DEC-OQ9 — SSoT der beiden Beispiel-Configs

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq9.md`
**Interfaces:** Produces: SSoT-Entscheidung zwischen `docs/guides/project.yaml.example` (179 Z) und
`docs/guides/configs/project.yaml.example` (340 Z) + Folge-Edit in beiden Dateien.
Consumes: Spec §11.1 OQ9, F24, NG-1.
**Agent:** technical-writer · **Depends on:** W4-3, W0-7 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-28** (Teil, M-5-Ziel) · **V-Check:** **V2**
**Akzeptanz:** Entscheidung **vor** W5-2 (Spec §11.1 OQ9, Blockade W5); Ergebnis ist eine Zeile in
`docs/guides/INDEX.md` plus ein Pointer in **beiden** Dateien — **kein** Merge, **keine** Löschung
(NG-1: eine Löschung würde Beispielkonfiguration entfernen).
**Verifikation:** `wc -l docs/guides/project.yaml.example docs/guides/configs/project.yaml.example`
→ **179** / **340**.
**Steps:**
- [ ] 1: Reichweiten beider Dateien vergleichen (ohne Rewrite).
- [ ] 2: Entscheidung festhalten (Spec-Empfehlung: 340 Z = vollständige Referenz, 179 Z =
      Kurzfassung mit Pointer darauf).
- [ ] 3: Pointer-Edit für W5-2 vormerken.
- [ ] 4: commit via `git`-Agent: `docs: decide OQ9 example config single source`.

### W5-2: M-5 und M-6 (`git mv` der Guides)

**Files:** Move `howto/configs/project.yaml.example` → `docs/guides/configs/project.yaml.example`;
Move `docs/howto/admin-ui-remote-access.md` → `docs/guides/admin-ui-remote-access.md`;
entfernen: `docs/howto/` (leer) und `howto/` (Root)
**Interfaces:** Produces: **ein** Guide-Ort `docs/guides/`; Pointer-Zeile aus W5-1 in beiden
Beispiel-Configs. Consumes: W5-1.
**Agent:** developer · **Depends on:** W5-1 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-28** (Teil, M-5, M-6) · **V-Check:** **V2**, **V3**
**Akzeptanz:** `git log -M` zeigt R100 für beide Dateien; `docs/INDEX.md` erkennt die neuen Pfade
bei der nächsten Generierung; `howto/` und `docs/howto/` existieren **nicht** mehr (F6, F15, F23).
**Verifikation:** `test ! -e howto` → **0**; `test ! -e docs/howto` → **0**;
`python3 scripts/sync.py --check` → **0**.
**Steps:**
- [ ] 1: Beide `git mv` ausführen; `howto/` und `docs/howto/` entfernen.
- [ ] 2: Pointer aus W5-1 additiv eintragen.
- [ ] 3: `--check` und V2/V3 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: consolidate guide locations under docs/guides`.

### W5-3: M-9/M-10 — `derived-from`-Annotation und Architektur-Redirects

**Files:** Modify `knowledge/wiki/**/*.md` (additive Frontmatter-Zeilen),
`knowledge/wiki/concepts/architecture*.md` (Kurzform-Redirects);
Modify `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: `derived-from: <existierender Rel-Pfad>` + `derived-at: <ISO-8601>`;
`SSoT: docs/architecture/…`-Redirect für die Architektur-Wiki-Seiten. Consumes: W5-2, W0-7, W1-4.
**Agent:** tester · **Depends on:** W5-2, W0-7 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-31** (IC-17, IC-03), **AC-29(c)** · **V-Check:** **V7**
**Akzeptanz:** `test_wiki_annotation_is_additive` grün — der Diff ist **ausschließlich** additiv
(keine gelöschte Zeile außer der Ersetzung eines bestehenden `status:`-Werts); jede annotierte
Seite trägt `derived-from` **und** `derived-at`; `knowledge/sources/` ist **unberührt** (NG-2).
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`python3 scripts/consistency-check.py --strict` → **0** (V7);
`git diff --stat -- knowledge/sources/` → **0 Dateien**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Annotationen additiv setzen; Architektur-Seiten auf
      `docs/architecture/00-overview-full.md` umhängen (IC-03 liest **nicht** aus dem Stub).
- [ ] 3: Tests grün beobachten; V7 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: annotate wiki pages with derived-from provenance`.

---

## W6 — Spec/Plan-Legacy archivieren

**Verifikation W6 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**
- `test ! -e docs/superpowers` → **0**
- `python3 scripts/consistency-check.py --strict` → **0** (V8 grün)
- `python3 scripts/sync.py --validate` → **0**
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**
**Review W6:** `code-reviewer` (R+A) → `validator` (AC-28, AC-32) → `release` (B1: Release-Notes,
Minor-Bump für die Deprecation-WARNING).
**Gate bei CHANGES_REQUESTED:** Inhalts-Diff ⇒ **Stopp**; fehlende Release-Notes ⇒ Merge gesperrt
(B1/R8).
**Rollback W6:** beide `git mv` zurück, `docs/superpowers/` wiederherstellen, die zwei additiven
`legacy:`-Zeilen entfernen.

### W6-1: M-3 und M-4 (`git mv` nach `archive/superpowers/`)

**Files:** Move `docs/superpowers/specs/` → `docs/specs/archive/superpowers/`;
Move `docs/superpowers/plans/` → `docs/plans/archive/superpowers/`; entfernen: `docs/superpowers/`
**Interfaces:** Produces: zwei archivierte Legacy-Bäume; `docs/superpowers/` verschwindet (F7);
Archiv-Trennung gemäß `docs/plans/README.md`. Consumes: W5-3.
**Agent:** developer · **Depends on:** W5-3 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-28** (Teil, M-3, M-4) · **V-Check:** **V8**
**Akzeptanz:** `git log -M` zeigt R100; keine Inhalte umgeschrieben.
**Verifikation:** `test ! -e docs/superpowers` → **0**;
`ls docs/specs/archive/superpowers | wc -l` → **> 0**;
`ls docs/plans/archive/superpowers | wc -l` → **> 0**.
**Steps:**
- [ ] 1: `git mv` für beide Bäume ausführen; `docs/superpowers/` entfernen.
- [ ] 2: Prüfen, dass keine Inhalte umgeschrieben wurden.
- [ ] 3: `git log -M` und V8 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: archive superpowers spec and plan trees`.

### W6-2: M-13, `legacy:`-Erweiterung und AC-28-Abschlussnachweis

**Files:** Modify `.meta-config/project.yaml` (`:61-63`), `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: `legacy:` mit **vier** Einträgen (2 alte + 2 Archivpfade);
Deprecation-WARNING statt Fehler für die alten Pfade; `test_legacy_list_extended_additively`,
`test_moves_are_renames`. Consumes: W6-1, W5-2, W4-1.
**Agent:** tester · **Depends on:** W6-1 · **parallel_group:** PG-3 (seriell)
**Ziel-AK (AC):** **AC-32** (IC-17, IC-13, IC-22), **AC-28** (M-1, M-3, M-4, M-6) · **V-Check:** **V8**
**Akzeptanz:** `test_moves_are_renames` grün: `ARCHITECTURE.full.md`, `docs/superpowers/`, `howto/`
und `docs/howto/` existieren **nicht** mehr; `git log --diff-filter=R --name-only` zeigt je Datei
ein **R**ena-**+ A**dd-Paar. `test_legacy_list_extended_additively` grün (4 Einträge).
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`grep -c 'docs/superpowers' .meta-config/project.yaml` → **2** (bleiben toleriert, B1);
`python3 scripts/sync.py --validate` → **0** (mit Deprecation-WARNING; Exit bleibt 0).
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `legacy:` additiv um zwei Zeilen erweitern; Release-Notes-Eintrag vorbereiten.
- [ ] 3: Tests grün beobachten; `--validate` beobachten (Exit **0**, Warnung sichtbar).
- [ ] 4: commit via `git`-Agent: `feat: extend legacy path list for archived spec plan trees`.

---

## W7 — Knowledge-Index-Generierung (isoliert, einziger Policy-Bruch)

**Harte Voraussetzung vor W7:** Rollenpflege-/Track-A-Branch **gemergt**; `knowledge/schema.md` um
„`index.md` is generated“ ergänzt und **User-Sign-off** eingeholt (IC-19-Bedingung (a),
`knowledge/schema.md:44-46`).
**Verifikation W7 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_knowledge_index_gen.py -q` → **0**
- `python3 scripts/consistency-check.py --strict` → **0** (V7)
- `python3 scripts/sync.py --validate` → **0**
- `git diff --stat -- knowledge/wiki/log.md` → **genau 1 Zeile** (Format `knowledge/wiki/log.md:13-17`)
- `ls knowledge/wiki/index.md.sync-backup-* | wc -l` → **≥ 1**
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0** (KE-Write-Pfade in Szenario 54 unverändert)
**Review W7:** `code-reviewer` → `knowledge-curator` (Policy) → `validator` (AC-33…AC-35, AC-41) →
`knowledge-linter`. **Gate:** fehlende Erstsicherung oder Diff ohne vorheriges Review ⇒ **Stopp** (R2).
**Rollback W7:** `knowledge-engine.okf.index-mode: llm` (Generator stumm) **und**
`restore_wiki_index(project_root, log)` (IC-24); `agents/1-generic/knowledge-indexer.md` via
`git checkout`; `knowledge/schema.md`-Absatz via `git checkout`. W7 invalidiert keine andere Welle
(NFA-06).

### W7-1: Policy-Voraussetzung — `knowledge/schema.md`

**Files:** Modify `knowledge/schema.md` (Abschnitt „Usage“, `:41-42`)
**Interfaces:** Produces: Absatz „`index.md` is generated“ mit Verweis auf IC-19 und den
Rollback-Hebel `knowledge-engine.okf.index-mode`. Consumes: IC-19-Bedingung (a),
`knowledge/schema.md:44-46`.
**Agent:** knowledge-curator · **Depends on:** W6-2 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-35** (IC-19) · **V-Check:** — (Policy-Dokument)
**Akzeptanz:** **User-Sign-off liegt vor** (strukturelle Änderung nach
`knowledge/schema.md:44-46`); Text nennt Generator, Flag und Rückrollweg. Ohne Sign-off startet W7
**nicht** — das ist Bedingung (a) von IC-19.
**Verifikation:** `grep -n 'index.md' knowledge/schema.md` → **0** (Treffer vorhanden).
**Steps:**
- [ ] 1: Absatzentwurf nach IC-19 vorlegen.
- [ ] 2: **User-Sign-off einholen** (Gate).
- [ ] 3: Absatz einfügen.
- [ ] 4: commit via `git`-Agent: `docs: declare knowledge index as generated`.

### W7-2: `sync_wiki_index` und `log.md`-Append

**Files:** Modify `scripts/lib/knowledge.py` (`:103-205`), `.meta-config/project.yaml` (`:18-29`);
Create `tests/test_knowledge_index_gen.py`
**Interfaces:** Produces: `sync_wiki_index(agent_meta_root, project_root, config, log, dry_run) -> dict`
(No-op, wenn `knowledge-engine.okf.index-mode != "generated"`); `knowledge-engine.okf.index-mode`
**neben** dem bestehenden `auto-index: true` (`.meta-config/project.yaml:28`) in der Config.
Consumes: W7-1, Verzeichnisnamen-Muster `knowledge.py:_KNOWLEDGE_GITKEEP_SUBDIRS` (`:87-100`).
**Agent:** senior-developer · **Depends on:** W7-1 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-33** (IC-19, IC-22), **AC-34** (IC-20) · **V-Check:** **V7**
**Akzeptanz:** `test_index_mode_flag_and_determinism` grün (jede Wiki-Seite **genau einmal**,
alphabetisch ⇒ minimaler Diff); `test_log_append_only_on_change` grün (genau **eine** Zeile
`YYYY-MM-DD HH:MM — index/update — <summary>` bei Wiki-Änderung, **keine** sonst; Bestand
append-only, nie umsortiert). `index-mode: llm` ⇒ `index.md` byte-identisch.
**Verifikation:** `python3 -m pytest tests/test_knowledge_index_gen.py -q` → **0**;
`grep -n 'index-mode' .meta-config/project.yaml` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: `sync_wiki_index` + Append implementieren; `index-mode: llm` als Default.
- [ ] 3: Tests grün beobachten.
- [ ] 4: commit via `git`-Agent: `feat: add deterministic knowledge index generator`.

### W7-3: Erstsicherung und Restore-Pfad

**Files:** Modify `scripts/lib/knowledge.py`; Modify `tests/test_knowledge_index_gen.py`
**Interfaces:** Produces: Erstsicherung `index.md.sync-backup-<YYYYmmdd-HHMMSS>` vor dem ersten
Rewrite; `restore_wiki_index(project_root, log, *, dry_run=False) -> list[str]` (IC-24, Reihenfolge
Sibling-Backup → `git -C <project_root> checkout -- knowledge/wiki/index.md` → `log.error` +
**kein** Schreibzugriff). Consumes: W7-2, Muster `generated_file_drift.py:354-402, :388`.
**Agent:** senior-developer · **Depends on:** W7-2 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-35**, **AC-41** (IC-24) · **V-Check:** — (Restore-Ebene, Unit-Test)
**Akzeptanz:** `test_first_activation_is_backed_up`, `test_restore_from_backup_sibling`,
`test_restore_dry_run` und `test_restore_fails_closed_without_source` grün; Restore liefert
**exakt einen** Rel-Pfad und stellt den Alt-Inhalt byte-identisch wieder her (Vergleich über
`io.content_hash`); ohne Sicherung **und** ohne Git-Tracking: `log.error`, **kein** Write
(fail-closed, kein stiller Datenverlust). Aufruf **nur** als manueller Runbook-Schritt, **ohne**
neues CLI-Flag (NG-4).
**Verifikation:** `python3 -m pytest tests/test_knowledge_index_gen.py -q` → **0**.
**Steps:**
- [ ] 1: Tests schreiben (fail).
- [ ] 2: Sicherung + `restore_wiki_index` implementieren (Reihenfolge ist vertraglich: Sibling
      schlägt Git, weil es den exakten Vor-Rewrite-Zustand sichert).
- [ ] 3: Tests grün beobachten; Dry-Run-Substep des Runbooks dokumentieren.
- [ ] 4: commit via `git`-Agent: `feat: add wiki index backup and restore path`.

### W7-4: `knowledge-indexer`-Umschreibung (IC-21) — **letzter Commit der Welle**

**Files:** Modify `agents/1-generic/knowledge-indexer.md`
**Interfaces:** Produces: Rolle „prüfe Generator-Output, melde Drift“ statt „schreibe `index.md`“;
provider-agnostisch. Consumes: W7-3, Rollenpflege-Branch (muss gemergt sein — R19).
**Agent:** prompt-engineer · **Depends on:** W7-3 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-35** (IC-19, IC-24, IC-21) · **V-Check:** — (Agent-Rolle)
**Akzeptanz:** **einzige** von dieser Initiative berührte Datei unter `agents/` (NFA-08); kein
Claude-Literal, keine Provider-Verzweigung; IC-21 wird als **letzter** Commit von W7 committet,
damit ein Rebase der Rollenpflege nicht in einem `agents/1-generic/`-Template-Diff landet.
**Verifikation:** `python3 -m pytest tests/test_provider_agnostic_dispatch.py -q` → **0**;
`grep -rn 'Claude' agents/1-generic/knowledge-indexer.md` → **1** (kein Treffer erwartet).
**Steps:**
- [ ] 1: Rollenpflege-Branch-Status prüfen; bei offen **stoppen** (R19).
- [ ] 2: Rolle umschreiben.
- [ ] 3: Provider-Agnostik-Guard beobachten.
- [ ] 4: commit via `git`-Agent: `docs(agent): shift knowledge-indexer to drift reporting`.

### W7-5: Aktivierung `index-mode: generated` und W7-Abschluss

**Files:** Modify `.meta-config/project.yaml`, `knowledge/wiki/index.md` (generiert),
`knowledge/wiki/log.md` (Generator-Append)
**Interfaces:** Produces: `knowledge-engine.okf.index-mode: generated`; deterministisch gerenderte
`index.md`; genau **eine** Log-Zeile. Consumes: W7-4.
**Agent:** knowledge-curator · **Depends on:** W7-4 · **parallel_group:** PG-4 (isoliert)
**Ziel-AK (AC):** **AC-33**, **AC-34**, **AC-35** · **V-Check:** **V7**
**Akzeptanz:** `index-mode: llm` ⇒ `index.md` **byte-identisch**; `index-mode: generated` ⇒
deterministisch neu gerendert, jede Wiki-Seite genau einmal; `log.md` wächst um **eine** Zeile im
Format `knowledge/wiki/log.md:13-17` (`operation ∈ {index, index/update}`).
**Verifikation:** `python3 scripts/sync.py --validate` → **0**;
`python3 scripts/consistency-check.py --strict` → **0**;
`git diff --stat -- knowledge/wiki/log.md` → **1 Zeile**.
**Steps:**
- [ ] 1: Diff-Review von `knowledge/wiki/index.md` **vor** Aktivierung (R2).
- [ ] 2: `index-mode: generated` setzen; Sync; Log-Diff prüfen.
- [ ] 3: `--validate` und V7 beobachten.
- [ ] 4: commit via `git`-Agent: `feat: activate generated knowledge index`.

---

## W8 — Totverweise, V9, Config-Struktur, ID-Deklaration

**Verifikation W8 (erwartete Exit-Codes):**
- `python3 -m pytest tests/test_doc_facts.py tests/test_docs_consolidation_migration.py -q` → **0**
- `python3 scripts/sync.py --check` → **0**
- `python3 scripts/sync.py --validate` → **0**
- `python3 scripts/consistency-check.py --strict` → **0** (V1a **und** V3 ohne Befund; V9 meldet die
  179 Altlasten als **WARNING** — lokale Aufräumaktion FI-10, kein Fehler)
- `bash tests/scenarios/run.sh 50 51 52 54 55 56` → **0**
- `grep -c 'docs/INDEX.md' AGENTS.md` → **≥ 1** (M-12-Wirkung sichtbar)
**Review W8:** `code-reviewer` → `validator` (AC-30, AC-40) → `requirements` (OQ4) → `release`
(M-12 wirkt auf alle generierten Kontextdateien, B6/R13).
**Gate bei CHANGES_REQUESTED:** der Layout-Diff in `AGENTS.md`/`CLAUDE.md` muss im Review
**explizit quittiert** werden (B6); ohne Quittung kein Merge.
**Rollback W8:** additiv revertierbar — `git checkout README.md llms.txt docs/REQUIREMENTS.md`,
`git checkout .meta-config/project.yaml`, V9-Block aus `scripts/lib/consistency/docs.py` entfernen.
Kein `git mv` betroffen ⇒ keine andere Welle invalidiert.

### W8-1: DEC-OQ4 — ID-System-Deklaration

**Files:** Create `docs/plans/2026-09-25-docs-consolidation-oq4.md`; Modify `docs/REQUIREMENTS.md`
**Interfaces:** Produces: deklarativer Abschnitt „`SPEC-*` = Spec-Pipeline-Artefakt-ID, `REQ-*` =
Requirements-Master-ID, Einweg-Verweis“; **keine** Umbenennung (NG-6). Consumes: F16.
**Agent:** requirements · **Depends on:** W7-5 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-40** (IC-02, IC-22 — Deklaration F16 gehört in W8) · **V-Check:** **V8**
**Akzeptanz:** Entscheidung **vor** W8-3 (Spec §11.1 OQ4, Blockade W8); Deklarationsabschnitt **additiv** in
`docs/REQUIREMENTS.md` ergänzt; **keine** bestehende `SPEC-*`-ID umbenannt; Szenario
`53-spec-plan-traceability` bleibt grün.
**Verifikation:** `grep -n 'REQ-\|SPEC-' docs/REQUIREMENTS.md` → **0** (beide Muster vorhanden);
`bash tests/scenarios/run.sh 53` → **0**.
**Steps:**
- [ ] 1: Zwei-Ebenen-Modell mit `validator` abstimmen.
- [ ] 2: Deklarationsabschnitt additiv ergänzen.
- [ ] 3: Szenario 53 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: declare REQ and SPEC identifier layers`.

### W8-2: M-8 — Tote interne Verweise (AC-30)

**Files:** Modify `README.md`, `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: `README.md:721-723` auf existierende Ziele umgeschrieben bzw. entfernt;
`README.md:724` (`CLAUDE.md` als Template-Config) entfernt — die Datei existiert nicht (F15);
`test_no_dead_internal_links_after_migration`. Consumes: W4-2, W5-2, W6-1.
**Agent:** developer · **Depends on:** W8-1 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-30** (IC-17, M-8) · **V-Check:** **V3**
**Akzeptanz:** `README.md`, `llms.txt` und `docs/**` frei von Findings auf **relative interne**
Links; V3 liefert **keine** Findings mehr (`exit 0`); keine Umbenennung von Dateien.
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`python3 scripts/consistency-check.py --strict` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: Totverweise umschreiben/entfernen.
- [ ] 3: V3 beobachten (Exit **0**).
- [ ] 4: commit via `git`-Agent: `docs: fix dead internal links in README`.

### W8-3: Providerzahl generiert (AC-40)

**Files:** Modify `llms.txt`, `README.md`, `tests/test_docs_consolidation_migration.py`
**Interfaces:** Produces: Providerzahl in `llms.txt` und `README.md:690` **ausschließlich** aus
einem `agent-meta:docs-*-Block`; `docs/INDEX.md` führt `DOCS_PROVIDERS_BLOCK`;
`test_provider_count_is_generated_in_readme_llms_index`. Consumes: W8-2, W0-3 (OQ2-Record,
**Hybrid**, Spec §11.2).
**Agent:** developer · **Depends on:** W8-2 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-40** (IC-02, IC-22) · **V-Check:** **V1a**, **V6**
**Akzeptanz:** keine handgeschriebene Providerzahl mehr im Fließtext; Wert entspricht
`DOCS_PROVIDER_COUNT`; `llms.txt:5` führt alle 9 Providernamen oder verweist auf den Block
(`config/ai-providers.yaml:1` + 9 Blöcke).
**Verifikation:** `python3 -m pytest tests/test_docs_consolidation_migration.py -q` → **0**;
`python3 scripts/consistency-check.py --strict` → **0**; `python3 scripts/sync.py --check` → **0**.
**Steps:**
- [ ] 1: Test schreiben (fail).
- [ ] 2: `DOCS_PROVIDERS_BLOCK` in beide Dateien einbinden; Prosa drumherum erhalten
      (OQ2-Hybrid, NG-1).
- [ ] 3: Tests grün beobachten; V1a/V6 beobachten.
- [ ] 4: commit via `git`-Agent: `docs: generate provider count in README and llms.txt`.

### W8-4: V9, M-12 und Abschluss

**Files:** Modify `scripts/lib/consistency/docs.py`, `.meta-config/project.yaml` (`:205-221`),
`tests/test_doc_facts.py`
**Interfaces:** Produces: `check_stale_backups(root, config=None)` (**WARNING**,
`*.sync-backup-*` älter als N Tage, Muster `.gitignore:22`); `PROJECT_STRUCTURE` um `docs/INDEX.md`,
`docs/guides/configs/`, `docs/providers/`, `docs/se-cascade/`, `docs/concepts/` ergänzt (M-12).
Consumes: W8-3.
**Agent:** tester · **Depends on:** W8-3 · **parallel_group:** PG-5
**Ziel-AK (AC):** **AC-30** (V3-Nachweis), **AC-40** · **V-Check:** **V9**
**Spec-Lücke (ehrlich benannt, nicht kaschiert):** **V9 hat in der Spec kein AC** — §9.1 führt
V1–V8, V9 erscheint nur in IC-05 mit Start W8. Eine AC zu erfinden wäre eine Spec-Änderung und
unterbleibt. V9 wird in W8-4 implementiert und nachgewiesen über
`python3 scripts/consistency-check.py --strict` (Exit **0**, V9 meldet ausschließlich WARNING)
sowie FI-10 („Abbau der 179 Altlasten ist lokale Aufräumaktion, kein Spec-Gegenstand“).
**Akzeptanz:** M-12 wirkt sichtbar in `AGENTS.md`/`CLAUDE.md` (managed block,
`context.py:36-38`; Drift-Detection fängt Handpflege ab); die 179 Altlasten bleiben **unangetastet**.
**Verifikation:** `python3 -m pytest tests/test_doc_facts.py -q` → **0**;
`python3 scripts/consistency-check.py --strict` → **0**; `python3 scripts/sync.py --validate` → **0**;
`grep -c 'docs/INDEX.md' AGENTS.md` → **≥ 1**.
**Steps:**
- [ ] 1: V9 implementieren (Severity WARNING, Altersschwelle als Config-Key mit Default).
- [ ] 2: `PROJECT_STRUCTURE` additiv ergänzen; Sync ⇒ Layout-Diff.
- [ ] 3: Layout-Diff im Review quittieren lassen (B6/R13).
- [ ] 4: commit via `git`-Agent: `feat: add V9 stale backup check and project structure fix`.

---

## Reihenfolge-/Abhängigkeitsmatrix

| Task | Welle | Agent | Depends on | parallel_group | AC | V-Check | Datei-Ownership (Schreibmenge) |
|---|---|---|---|---|---|---|---|
| W0-1 | W0 | orchestrator | W0-2 | — (Gate) | AC-20/21/12 | — | `docs/plans/…-oq6.md` |
| W0-2 | W0 | git | — | — | AC-01…41 (Anker) | — | `docs/plans/…-wave0-freeze.md` + Branches |
| W0-3 | W0 | agent-meta-manager | W0-2 | W0-PG-B | AC-25/40 | — | `docs/plans/…-oq2.md` |
| W0-4 | W0 | orchestrator | W0-2 | W0-PG-B | AC-07/08/39 | — | `docs/plans/…-track-a-gate.md` |
| W0-6 | W0 | orchestrator | W0-2 | W0-PG-B | AC-12/38 | V2 | `docs/plans/…-oq8.md` |
| W0-7 | W0 | orchestrator | W0-2 | W0-PG-B | AC-31 | V7 | `docs/plans/…-oq1.md` |
| W1-1 | W1 | senior-developer | W0-1, W0-4 | PG-1/W1-A | AC-01 | — | `scripts/lib/doc_facts.py`, `tests/test_doc_facts.py` |
| W1-2 | W1 | senior-developer | W1-1 | PG-1/W1-A | AC-02, AC-03 | — | dieselben 2 |
| W1-3 | W1 | senior-developer | W1-2 | PG-1/W1-A | AC-04, AC-05 | V5 | dieselben 2 |
| W1-4 | W1 | senior-developer | W1-3 | PG-1/W1-A | AC-10, AC-29c | V7 | dieselben 2 |
| W1-5 | W1 | senior-developer | W1-2 | PG-1/W1-A | AC-36, NFA-11 | V6 | + `config/doc-facts-expected.yaml`, `tests/test_doc_facts_expected.py` |
| W1-6 | W1 | developer | W1-4, W0-3 | PG-1/W1-A | AC-25, AC-06 | — | + `scripts/lib/config.py`, `scripts/lib/consistency/placeholders.py`, `snippets/docs/*.md` (6) |
| W1-7 | W1 | senior-developer | W1-1 | PG-1/W1-B | AC-14/15/16/27 | V6 | `scripts/lib/doc_renderer.py`, `tests/test_doc_renderer.py` |
| W1-8 | W1 | senior-developer | W1-7 | PG-1/W1-B | AC-17 (Modell), NFA-01 | V2 | + `scripts/lib/doc_index.py` |
| W1-10 | W1 | developer | W1-8 | PG-1/W1-B | AC-24 | alle | + `.meta-config/project.yaml` |
| W1-9 | W1 | developer | W0-4 | PG-1/W1-C | AC-39 | — | `config/project-config.schema.json`, `tests/test_docs_consolidation_migration.py` |
| W2-1 | W2 | developer | W1-6, W0-4 | PG-2/W2 | AC-07, AC-08 | V1a, V1b | `scripts/lib/consistency/docs.py`, `tests/fixtures/docs_v1_fixtures.md`, `tests/test_doc_facts.py` |
| W2-2 | W2 | developer | W2-1 | PG-2/W2 | AC-09 | V3 | `docs.py`, `tests/test_doc_facts.py` |
| W2-3 | W2 | developer | W2-2 | PG-2/W2 | AC-10 | V7 | dieselben 2 |
| W2-4 | W2 | developer | W2-3 | PG-2/W2 | AC-11 | V5 | dieselben 2 |
| W2-5 | W2 | developer | W2-4 | PG-2/W2 | AC-36 | V6 | `docs.py`, `tests/test_doc_facts_expected.py` |
| W2-6 | W2 | developer | W2-5 | PG-2/W2 | AC-12 | V2, V4 | `docs.py`, `tests/test_doc_facts.py` |
| W2-7 | W2 | developer | W2-6 | PG-2/W2 | AC-13, AC-24 | alle | + `scripts/consistency-check.py` |
| W3-1 | W3 | senior-developer | W1-10 | PG-2/W3 | AC-23, AC-26 | V6 | `scripts/lib/doc_renderer.py`, `doc_index.py`, `tests/test_doc_renderer.py` |
| W3-2 | W3 | senior-developer | W3-1 | PG-2/W3 | AC-17, AC-18, AC-03 | V2, V6 | `doc_renderer.py`, `tests/test_doc_renderer.py` |
| W3-3 | W3 | senior-developer | W3-2 | PG-2/W3 | AC-21 | V4 | + `scripts/lib/spec_plan_scaffold.py` |
| W3-4 | W3 | senior-developer | W3-3 | PG-2/W3 | AC-22 | V1 | + `scripts/lib/sync_pipeline.py`, `.meta-config/project.yaml` |
| W3-5 | W3 | developer | W3-4 | PG-2/W3 | AC-19, AC-37 | — | + `scripts/lib/generated_file_drift.py`, `tests/test_generated_file_drift_docs.py` |
| W3-6 | W3 | senior-developer | W3-5, W0-1, W0-6 | PG-2/W3 | AC-20, AC-12, AC-38 | V2, V4 | + `docs/INDEX.md`, `README.md` (kein `.gitignore` — OQ6 entschieden) |
| W3-7 | W3 | developer | W3-6 | PG-2/W3 | AC-40 (Teil), AC-07 | V1a, V1b, V6 | + `llms.txt`, `ARCHITECTURE.md`, `README.md` |
| W4-1 | W4 | developer | W3-6 | PG-3 (seriell) | AC-28 (Teil), AC-29b | V3 | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` |
| W4-2 | W4 | developer | W4-1 | PG-3 | AC-29a | V3 | `ARCHITECTURE.md` |
| W4-3 | W4 | tester | W4-2 | PG-3 | AC-29, AC-28 (Teil) | V3, V7 | `docs/architecture/INDEX.md`, `tests/test_docs_consolidation_migration.py` |
| W5-1 | W5 | technical-writer | W4-3, W0-7 | PG-3 | AC-28 (Teil) | V2 | `docs/plans/…-oq9.md` |
| W5-2 | W5 | developer | W5-1 | PG-3 | AC-28 (Teil) | V2, V3 | `howto/configs/…` → `docs/guides/configs/…`, `docs/howto/…` → `docs/guides/…` |
| W5-3 | W5 | tester | W5-2, W0-7 | PG-3 | AC-31, AC-29c | V7 | `knowledge/wiki/**/*.md`, `tests/test_docs_consolidation_migration.py` |
| W6-1 | W6 | developer | W5-3 | PG-3 | AC-28 (Teil) | V8 | `docs/superpowers/**` → `docs/{specs,plans}/archive/superpowers/**` |
| W6-2 | W6 | tester | W6-1 | PG-3 | AC-32, AC-28 | V8 | `.meta-config/project.yaml`, `tests/test_docs_consolidation_migration.py` |
| W7-1 | W7 | knowledge-curator | W6-2 | PG-4 (isoliert) | AC-35 | — | `knowledge/schema.md` |
| W7-2 | W7 | senior-developer | W7-1 | PG-4 | AC-33, AC-34 | V7 | `scripts/lib/knowledge.py`, `.meta-config/project.yaml`, `tests/test_knowledge_index_gen.py` |
| W7-3 | W7 | senior-developer | W7-2 | PG-4 | AC-35, AC-41 | — | `scripts/lib/knowledge.py`, `tests/test_knowledge_index_gen.py` |
| W7-4 | W7 | prompt-engineer | W7-3 | PG-4 | AC-35 | — | `agents/1-generic/knowledge-indexer.md` |
| W7-5 | W7 | knowledge-curator | W7-4 | PG-4 | AC-33/34/35 | V7 | `.meta-config/project.yaml`, `knowledge/wiki/index.md`, `knowledge/wiki/log.md` |
| W8-1 | W8 | requirements | W7-5 | PG-5 | AC-40 | V8 | `docs/plans/…-oq4.md`, `docs/REQUIREMENTS.md` |
| W8-2 | W8 | developer | W8-1 | PG-5 | AC-30 | V3 | `README.md`, `tests/test_docs_consolidation_migration.py` |
| W8-3 | W8 | developer | W8-2 | PG-5 | AC-40 | V1a, V6 | `llms.txt`, `README.md`, `tests/test_docs_consolidation_migration.py` |
| W8-4 | W8 | tester | W8-3 | PG-5 | AC-30, AC-40 | V9 | `scripts/lib/consistency/docs.py`, `.meta-config/project.yaml`, `tests/test_doc_facts.py` |

**Zyklenprüfung:** Der Graph ist ein **DAG**. Jede Kante zeigt auf eine **niedrigere** Welle oder
auf einen früheren Task derselben Welle. Die einzigen Kanten innerhalb einer Welle sind
W0-2 → {W0-1, W0-3, W0-4, W0-6, W0-7}, W1-1→…→W1-10 (kettenintern), W2-1→…→W2-7, W3-1→…→W3-7,
W4→W5→W6 durchgehend, W7-1→…→W7-5 und W8-1→…→W8-4. **Keine Zyklen.**

## Entscheidungs-Tasks

| OQ | Task | Owner | Position | Folge, wenn nicht entschieden |
|---|---|---|---|---|
| **OQ6** — **ENTSCHIEDEN 2026-09-26** (`tracked`, kein `.gitignore`-Eintrag) | **W0-1** = Ergebnis-Record (vor W1-10 und W3-6) | `orchestrator` | W0, vor jedem Code-Task | **entfällt** — entschieden; W0-1 dokumentiert, W3-6 schreibt `docs/INDEX.md` tracked ohne `.gitignore`-Diff (Spec §11.2) |
| **OQ8** — **ENTSCHIEDEN 2026-09-26** (Sync/Validator, kein Hook) | **W0-6** = Ergebnis-Record (vor Abschluss W3) | `orchestrator` | W0, Umsetzung in W3-6 | **entfällt** — entschieden; V2 bleibt **ERROR**, Auslöser ist der Sync-/Validator-Lauf (Spec §11.2) |
| **OQ2** — **ENTSCHIEDEN 2026-09-26** (**Hybrid**: `{{DOCS_PROVIDERS_BLOCK}}` + `{{DOCS_REPO_FACTS_BLOCK}}`, Rest Handtext) | **W0-3** = Ergebnis-Record (vor Abschluss W1) | `agent-meta-manager` | W0 | **entfällt** — entschieden; `llms.txt` ist Wert von `docs-consolidation.sources` (IC-22), Prosa bleibt handgepflegt (Spec §11.2) |
| OQ1 (offen) | W0-7 (vor Abschluss W5) | `orchestrator` → `main_chat` | W0 | W5-3 annotiert ohne Scope-Grenze; FI-4 bliebe ungebunden |
| OQ9 (offen) | W5-1 (vor W5-2) | `technical-writer` + `documenter` | W5 | zwei SSoT-Kandidaten unter `docs/guides/` ohne Kennzeichnung (F24) |
| OQ4 (offen) | W8-1 (vor W8-3) | `requirements` + `validator` | W8 | F16 (zwei ID-Systeme) bleibt undokumentiert |
| OQ3 | — (nach W8) | `requirements` via `main_chat` | außerhalb dieses Plans | eigene REQ (Spec §11.1 OQ3, nach W8) |
| OQ5, OQ7 | — | — | geschlossen (Spec §11.2) | kein Task |

## Coverage-Matrix Task → AC → Welle → V-Check

| AC | Task(s) | Welle | V-Check |
|---|---|---|---|
| AC-01 | W1-1 | W1 | — |
| AC-02 | W1-2 | W1 | — |
| AC-03 | W1-2 (volatile) + W3-2 (Index-Sektion) | W1/W3 | V6 |
| AC-04 | W1-3 | W1 | — |
| AC-05 | W1-3 | W1 | V5 |
| AC-06 | W1-6 | W1 | — |
| AC-07 | W2-1 (Erkennung) + W3-7 (Wirkung: kein Befund mehr) | W2/W3 | V1a, V1b |
| AC-08 | W2-1 | W2 | V1a, V1b |
| AC-09 | W2-2 (Fund) + W8-2 (Behebung) | W2/W8 | V3 |
| AC-10 | W1-4 (Resolver) + W2-3 (Check) | W1/W2 | V7 |
| AC-11 | W2-4 | W2 | V5 |
| AC-12 | W2-6 (Implementierung) + W3-6 (E2E) | W2/W3 | V2 |
| AC-13 | W2-7 | W2 | alle |
| AC-14 | W1-7 (Implementierung) + W3-6 (Aktivierung) | W1/W3 | V6 |
| AC-15 | W1-7 | W1 | V6 |
| AC-16 | W1-7 | W1 | V6 |
| AC-17 | W1-8 (Modell) + W3-2 (Volltext) | W1/W3 | V2 |
| AC-18 | W3-2 | W3 | — (Determinismus) |
| AC-19 | W3-5 | W3 | — (Drift-Store) |
| AC-20 | W3-6 | W3 | V4 |
| AC-21 | W3-3 | W3 | V4 |
| AC-22 | W3-4 | W3 | — |
| AC-23 | W3-1 | W3 | — |
| AC-24 | W1-10 (+ W2-7 Common-Gate) | W1/W2 | alle |
| AC-25 | W1-6 | W1 | — |
| AC-26 | W3-1 | W3 | — |
| AC-27 | W1-7 | W1 | V6 |
| AC-28 | W4-1, W4-3, W5-1, W5-2, W6-1, W6-2 | W4/W5/W6 | V8 |
| AC-29 | W1-4, W4-2, W4-3, W5-3 | W1/W4/W5 | V3, V7 |
| AC-30 | W8-2 (+ W8-4 Nachweis) | W8 | V3 |
| AC-31 | W5-3 | W5 | V7 |
| AC-32 | W6-2 | W6 | V8 |
| AC-33 | W7-2, W7-5 | W7 | V7 |
| AC-34 | W7-2, W7-5 | W7 | — |
| AC-35 | W7-1, W7-3, W7-4, W7-5 | W7 | — |
| AC-36 | W1-5 (Quelle) + W2-5 (Prüfung) | W1/W2 | V6 |
| AC-37 | W3-5 | W3 | — (Allowlist) |
| AC-38 | W3-6 (Szenario-Nachweis); Szenario-Lauf in **jeder** Welle | W3 | — (bestehender Runner) |
| AC-39 | W1-9 | W1 | — |
| AC-40 | W3-7 (README/llms-Anteil), W8-1, W8-3 | W3/W8 | V1a, V6 |
| AC-41 | W7-3 | W7 | — (Restore) |

**Alle 41 AC sind durch mindestens einen Task abgedeckt. Keine AC wird gestrichen.**
18 AC haben bewusst **keinen** Consistency-Check (Spec §16, NEW-6) und werden per Unit-Test bzw.
bestehendem Runner abgesichert: AC-01, AC-02, AC-03, AC-04, AC-06, AC-18, AC-19, AC-22, AC-23,
AC-24, AC-25, AC-26, AC-34, AC-35, AC-37, AC-38, AC-39, AC-41.

**Nicht planbar / bewusst außerhalb (mit Begründung, nicht stillschweigend):**
- **V9 hat kein AC.** Die Spec führt V1–V8 in der AC-/V-Zuordnung, V9 nur in IC-05 (Start W8).
  V9 wird in W8-4 implementiert und über `--strict == 0` plus FI-10 nachgewiesen. Eine AC zu
  erfinden wäre eine Spec-Änderung.
- **`docs/CODEBASE_OVERVIEW.md`** (SSoT-Matrix §3.2) hat **kein AC** und ist über NG-3 der
  `documenter`-Ownership entzogen ⇒ kein Task; FI-2 bleibt Folge-Issue.
- **`knowledge/sources/docs/guides/`** (FI-7) — NG-2, kein Eingriff.
- **`AGENTS.md`-Bootstrap-Block** (OQ3/FI-5) — NG-5, eigene REQ nach W8.

## Risiken-Übernahme (R1–R20) und Restrisiko nach Planung

| # | W. | Planungsmaßnahme im Plan | Restrisiko nach Planung |
|---|---|---|---|
| R1 Doku-Diff-Churn | hoch | W1-2 volatile-Unterdrückung, W3-2 `docs-volatile` als letzte Sektion, Fact-Hash nur über nicht-volatile Fakten, Idempotenz-Tests in W3-1/3-2/3-7 | **niedrig** — Restdiff = genau eine Zeile pro Szenario, im Review begründet |
| R2 LLM-Handpflege-Kollision | hoch | W7-3 Erstsicherung **vor** Erst-Rewrite, IC-24-Restore, W7-5 Diff-Review vor Aktivierung, W7 isoliert und letzte Welle, `index-mode: llm` als Rollback | **niedrig** — Datenverlustpfad ist spezifiziert und getestet |
| R3 Track-A-Konflikt | hoch | W0-4 Gate-Task, W1/W2 sequenziell nach Track A, ein Commit pro Datei, Rebase vor jedem Merge, W7-4 erst nach Rollenpflege-Merge | **niedrig** |
| R4 V1-Fehlalarme | mittel | W2-1 Positiv- **und** Negativ-Fixture, `docs-exempt`-Marker, Start WARNING, `checks.strict` Default `false`; die zwei heute korrekten Handzahlen (`README.md:689`, `:695`) werden in W3-7 zu Regionen | **niedrig** — Restrisiko Fließtext („3 tests“) wird in W3-7-Wirkung sichtbar |
| R5 Rollen-Parität | niedrig | W2-4 V5 gate-bewusst und WARNING; Fix ist eigene REQ (NG-8) | **niedrig** |
| R6 Link-Check-Fehlalarme | mittel | W2-2 prüft nur relative repo-interne Pfade, ohne `http(s)://`, `mailto:`, `#anchor` | **niedrig** |
| R7 Doppel-Writer `docs/INDEX.md` | hoch | W3-3 `is_file_index_skeleton`, W3-4 verbindliche Stage-Reihenfolge, Besitzregel IC-13, `index-mode: skeleton`, Szenarien 50/51/52/54/55/56 in **jeder** Welle | **niedrig** |
| R8 Downstream-Bruch B1 | mittel | W6-2 `legacy:` additiv, ein Release Toleranz, Release-Pflicht + Minor-Bump über `release` im Review | **niedrig** |
| R9 Scope-Creep | mittel | Wellen sind additiv bzw. `git mv`-only, NG-1, OQ1/OQ9 als Entscheidungs-Tasks statt Inhaltsarbeit, NFA-08 | **niedrig** |
| R10 `AGENTS.md`-Bootstrap | niedrig | als OQ3/FI-5 bewusst außerhalb, kein Task | **niedrig** |
| R11 `CODEBASE_OVERVIEW.md` | mittel | kein Task (NG-3), FI-2 als Folge-Issue bei `documenter` | **niedrig** |
| R12 `DOCS_`-Namenskollision | mittel | W1-6 registriert nur `^DOCS_`; `DOCS_LANGUAGE`/`INTERNAL_DOCS_LANGUAGE` bleiben Built-ins; IC-02 verbietet ihre Belegung | **niedrig** |
| R13 `PROJECT_STRUCTURE`-Diff (B6) | niedrig | W8-4 additiver Config-Edit, managed block + Drift-Detection, Layout-Diff muss im Review quittiert werden | **niedrig** |
| R14 Falsche-Fakt-Kette | **hoch** | W1-5 `config/doc-facts-expected.yaml` (**elf** Werte) + `compare_expected_doc_facts`, W2-5 V6 mit `kind=expected-mismatch`; AC-02 prüft **Formeln**, nicht Zahlen | **mittel, bewusst akzeptiert** — jede gewollte Zahlenänderung macht V6 rot, bis die Datei im selben Commit mitgezogen wird (Review-Signalweg) |
| R15 Kollision über Track A hinaus | mittel | W0-4 Fixture-Gate, W1-9 Schema-Block in W1, W2-1 Fixtures nach Track-A-Merge; Szenario-Fixtures unverändert (NG-10) | **niedrig** |
| R16 PR-/Branch-Kollision | mittel | W0-2 ein Branch pro Welle, gestapelte PRs, `git mv`-Wellen zuerst mergen, ein Commit pro Datei | **niedrig** |
| R17 Downstream-Asymmetrie | mittel | Absenz-Default `false` (IC-22) für Writer **und** Checks; W2-7 Common-Gate in jedem Check; W3-1 Besitzregel | **niedrig** |
| R18 Auto-Commit-Interaktion | — | als **analysiert und nicht zutreffend** geführt (Spec:907, `sync_pipeline.py:1102-1117` liest den Drift-Store nicht); kein Plan-Task nötig | **keines** |
| R19 `knowledge-indexer`-Kollision | mittel | W7-4 als **letzter** Commit von W7, erst nach Rollenpflege-Merge; Rollback `git checkout` | **niedrig** |
| R20 V2-ERROR vs. menschliche Doku-Erstellung | mittel | **W0-6** entscheidet den Auslöser **vor** W3; W3-6 setzt ihn um; W3-7 dokumentiert den Vertrag | **niedrig** nach W0-6 |

## Definition of Done (Gesamtvorhaben)

1. **Alle 41 AC** sind durch je einen beobachtbaren Test oder Kommando **tatsächlich beobachtet**
   (nicht angenommen); die Coverage-Matrix ist ohne Lücke.
2. **Alle neun V-Checks** sind implementiert und liefern in agent-meta `exit 0` unter
   `python3 scripts/consistency-check.py --strict` (V9 ausschließlich WARNING).
3. **11 Handzahlen = 0**: `python3 scripts/consistency-check.py` meldet **keinen**
   `docs.no_manual_counts`-Befund; `grep -c 'Repo version:' ARCHITECTURE.md` → **0**.
4. **`docs/INDEX.md` existiert, ist getrackt und 100 % generiert**; zweimaliger Sync ⇒
   `unchanged`, null Schreibvorgänge (NFA-01).
5. **11 unabhängige Sollwerte** in `config/doc-facts-expected.yaml`; AC-36 grün; die Datei wird bei
   jeder gewollten Zahlenänderung **im selben Commit** mitgezogen (Review-Regel).
6. **Migration ohne Inhaltsverlust**: `git log --diff-filter=R` zeigt für alle 13 Operationen
   R+A-Paare; `test ! -e ARCHITECTURE.full.md && test ! -e docs/superpowers && test ! -e howto &&
   test ! -e docs/howto` → **0** (AC-28).
7. **Szenarien 50/51/52/54/55/56** bleiben nach **jeder** Welle grün; **kein** Assert-Skript und
   **keine** Fixture-Config wurde geändert (AC-38, NG-10).
8. **W7 isoliert**: Erstsicherung vorhanden, `restore_wiki_index` getestet (Backup, Dry-Run,
   fail-closed), User-Sign-off zu `knowledge/schema.md` liegt vor, `index-mode: llm` als Rollback
   dokumentiert.
9. **Alle sechs Entscheidungs-Records** (OQ1, OQ2, OQ4, OQ6, OQ8, OQ9) existieren mit Owner,
   Entscheidung und Datum. **OQ2/OQ6/OQ8** sind bereits **entschieden (2026-09-26, Nutzer)** — ihre
   Records dokumentieren die getroffene Entscheidung (Gewähltes **und** Verworfenes), nicht eine
   offene Wahl. OQ3 ist als Folge-REQ geführt.
10. **Provider-Agnostik**: `python3 -m pytest tests/test_provider_agnostic_dispatch.py -q` → **0**;
    kein `if provider == "Name"` in M1–M4; kein Config-Key mit Providernamen.
11. **NFA-07** eingehalten: M1, M2, M4 importieren nur Stdlib + `scripts/lib`.
12. **DoD-Standard**: Code komplett, Konventionen und Conventional Commits eingehalten, keine
    Regressionen; `python3 scripts/sync.py --validate` → **0**; `--check` → **0**.
13. **Traceability**: `validator`-Audit bestätigt AC-01…AC-41 → Task → Test; NFA-01…NFA-11 belegt.
14. **Ledger**: alle Checkboxen dieses Plans gesetzt (geschrieben durch den Ledger-Writer
    `scripts/lib/plan_ledger.py`); Merge der acht Wellen-Branches manuell bestätigt; danach
    Verschiebung nach `docs/plans/archive/` gemäß `docs/plans/README.md:4-7`.

## Self-Review (kein Platzhalter, Konsistenz gegen die Spec)

- **No-Placeholder:** kein `TODO`, kein `TBD`, kein `???`, kein leeres Feld. Offene Punkte sind
  ausschließlich die Entscheidungs-Tasks W0-7/W5-1/W8-1 (OQ1/OQ9/OQ4) mit Owner, Entscheidungsweg
  und Folge sowie die Ergebnis-Records W0-1/W0-3/W0-6 (OQ6/OQ2/OQ8, entschieden 2026-09-26).
  Jede
  Interface-Signature ist vollständig, jeder Task nennt exakte Pfade, Symbole und eine
  Commit-Message. `Interfaces:` ist in **jedem** Task gefüllt (Produces **und** Consumes).
- **AC-Vollständigkeit:** AC-01…AC-41 lückenlos, jede Zahl genau einmal in der Coverage-Matrix;
  W1=10, W2=7, W3=14, W4=2, W5=2, W6=2, W7=4, W8=2 — deckungsgleich mit Spec §9.2 (NEW-5).
- **Wellen-Konsistenz:** W0–W8 vollständig, Reihenfolge aus Spec §9.2 übernommen; die beiden
  Umordnungen (W4/W5/W6 seriell, W8 nach W7) sind **begründet** und markiert.
- **V-Checks:** V1–V9 implementiert; V9 ohne AC ist als Lücke **benannt**, nicht kaschiert.
- **Entscheidungen:** OQ6 (W0-1) und OQ8 (W0-6) sowie OQ2 (W0-3) sind **entschieden**
  (Nutzer, 2026-09-26, Spec §11.2) und als benannte Tasks **vor** der abhängigen Welle
  geführt, nicht als Fußnote: W0-1/W0-3/W0-6 sind **Ergebnis-Records** (Gewähltes **und**
  Verworfenes), W0-6 nennt den Sync-/Validator-Lauf und **ausdrücklich nicht** den
  `pre-commit`-Hook. OQ1/OQ9/OQ4 bleiben offen (W0-7/W5-1/W8-1); OQ3 außerhalb,
  OQ5/OQ7 geschlossen.
- **Ownership:** Jede Datei erscheint in höchstens einer Task-`Files:`-Liste **pro Parallelgruppe**.
  `.meta-config/project.yaml` wird von fünf Tasks geschrieben — diese liegen in fünf
  **sequenziell geordneten** Wellen, also nie gleichzeitig.
- **Parallelgruppen:** PG-1 (3 Ketten), PG-2 (2 Ketten), PG-3 (seriell), PG-4 (isoliert),
  PG-5 (1). Maximal 3 gleichzeitig laufende Agents — **unter** der Grenze 4, daher ist keine
  Barrieren-Spaltung über 4 hinaus nötig.
- **Track-A-Bedingung:** W1/W2 nicht parallel zu `scripts/lib/config.py`- und
  `scripts/lib/consistency/*`-Änderungen; als Gate-Task W0-4 verankert, plus Rebase-Pflicht.
- **Exit-Codes:** pro Welle konkret genannt, inklusive der **planmäßig nicht-null** Fälle
  (W2 `--strict` = 1 wegen V1-WARNING; W2/W3 Zwischenzustände), damit `--validate` als
  `TEST_COMMAND` nicht fälschlich als Regression gelesen wird.
- **Bekannte Abweichungen von der Spec (alle begründet, keine stillschweigend):**
  1. W4/W5/W6 seriell statt parallel (geteilter Testdatei-Besitz, §9.2).
  2. W8 nach W7 (NFA-06, B6).
  3. AC-12 Implementierung in W2-6, E2E-Nachweis in W3-6 (Datei-Ownership).
  4. AC-14/15/16/27 Implementierung in W1-7, Aktivierung in W3-6 (Spec §9.1 nennt W3).
  5. W0-Tasks verweisen als **Gate-Anker** auf ACs, obwohl W0 laut Spec §9.2 kein eigenes AC trägt.
- **Ehrliche Lücken:** V9 ohne AC; `docs/CODEBASE_OVERVIEW.md` ohne AC und NG-3; `llms.txt:5`
  Providernamen-Liste ist inhaltlich (AC-40), aber keine „manuell gepflegte Zahl“ (Spec Rev. 0.3,
  NF-9) und daher nicht Teil der 11.

