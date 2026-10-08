---
status: APPROVED
approved-by: user
approved-at: 2026-10-08
approval-note: "freigegeben durch Nutzer 2026-10-08 — explizite Freigabe aller bestätigten Findings des System-Reviews in dieser Session (vom Orchestrator als echte Nutzer-Autorität verifiziert); NICHT der unbeaufsichtigte Default"
plan-id: PLAN-BUGFIX-BATCH-2-2026-10-07
source: docs/reviews/2026-10-07-system-review.md
pipeline_stages:
  implement: 3
---

# Bugfix-Batch 2 — Umsetzung System-Review 2026-10-07 — Implementation Plan

> Status: APPROVED — freigegeben durch Nutzer 2026-10-08
> Datum: 2026-10-08 (Plan), Review-Stand `main` @ `9190965f`
> Trace-Anker: `plan-id: PLAN-BUGFIX-BATCH-2-2026-10-07`

**Spec:** `docs/reviews/2026-10-07-system-review.md` (konsolidierter Review-Report, 138 gültige Findings, IDs `SR-A/B/C/D/E-##`; im Review-PR, noch nicht auf `main`). Detailbelege + Verifier-Pässe je Dimension: `.tmp/review-dim-a.md` … `.tmp/review-dim-e.md`.

**Goal:** Alle bestätigten Findings des System-Reviews umsetzen — Security zuerst (Welle 1), danach MEDIUM (Welle 2) und LOW/INFO (Welle 3) als Cluster-PRs je Datei/Modul.
**Architecture:** Keine neue Komponente. Fixes an Ort und Stelle: HTTP-Handler (`scripts/admin-server.py`), Hooks (`hooks/1-generic/`), Templates (`agents/`, `snippets/`, `rules/`), Syncer-Libs (`scripts/lib/`), UI (`docs/ui/admin-ui.html`), CI/Tests.
**Tech Stack:** Python 3 stdlib, Bash-Hooks, Markdown-Templates, Vanilla-JS, pytest, Playwright (lokal, `tests/browser/`).

---

## 0. Grundlagen

### 0.1 Zählung

| Dimension | Findings | davon gültig | Welle 1 | Welle 2 | Welle 3 |
|---|---|---|---|---|---|
| A — scripts/lib + sync.py | 41 | 41 | 0 | 11 | 30 |
| B — Hooks & Guards | 33 | 33 | 2 | 10 | 21 |
| C — Templates/Rules/Skills | 18 | 18 | 2 (+C-07 Teil) | 8 | 8 |
| D — admin-server + admin-ui | 23 | 22 (A9 = FALSE_POSITIVE) | 3 | 11 | 8 |
| E — config/tests/CI | 24 | 24 | 0 | 8 | 16 |
| **Σ** | **139** | **138** | **7** | **48** | **83** |

Welle 1 = 6 Tasks · Welle 2 = 17 Cluster · Welle 3 = 21 Cluster.

### 0.2 ID-Mapping (Annahme, vor Start prüfen)

Der konsolidierte Report liegt nur auf Branch `docs/system-review-2026-10-07` (nicht im Arbeitsbaum). Mapping hier abgeleitet aus den Dim-Dateien:
- `SR-A-NN` = `A-NN`, `SR-B-NN` = `B-NN`, `SR-C-NN` = `C-NN`.
- `SR-D-01..06` = N1..N6, `SR-D-07/08` = X1/X2, `SR-D-09..23` = A1..A15 (bestätigt durch Vorgabe: SR-D-01 = N1, SR-D-09 = A1, SR-D-15 = A7).
- `SR-E-01..06` = E-CI-1..6, `SR-E-07..11` = E-CFG-1..5, `SR-E-12..24` = E-T-1..13 (**nicht** gegen Report geprüft).

Im Plan steht immer die Original-ID; für D/E zusätzlich die SR-ID. Abweichung im Report → nur Mapping korrigieren, Zuordnung zu Clustern bleibt.

### 0.3 Abgrenzung zum parallelen Plan #897/#896

`docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md` (Status DRAFT) deckt D1–D6, U1/U2 und N4 (Lowercase-Normalisierung) ab. Dieser Plan wiederholt nichts davon, berührt aber dieselben Dateien (`scripts/admin-server.py`, `docs/ui/admin-ui.html`, `tests/test_admin_server.py`) → Koordination siehe §6.

---

## Global Constraints

Gelten für alle Tasks und Cluster aller Wellen (einmal hier, nicht pro Task wiederholt):

- **Commits:** mindestens ein Commit pro Finding bzw. logischem Schritt — auch innerhalb eines Cluster-PRs. Conventional Commits, Englisch, ≤72 Zeichen, Finding-ID im Body (`Refs: SR-B-01`).
- **Review:** jeder PR bekommt ein unabhängiges Review (`code-reviewer`, bzw. Spezialist: `accessibility-specialist` für A11y). Implementierer ≠ Reviewer.
- **Security-Review:** Alles, was Hooks/Guards (B-*) oder `scripts/admin-server.py` / `scripts/lib/backup.py` (N*) berührt → **ZWINGEND separates Security-Review** (eigener Review-Durchlauf mit Security-Checkliste, zusätzlich zum normalen Code-Review). Keine Schwächung bestehender Schutzmechanismen; Convention- vs. Security-Boundary-Unterscheidung aus `.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary` respektieren — kein Fix darf einen Guard von „fail-closed" auf „fail-open" drehen.
- **Overlap-Check:** vor jedem Parallel-Dispatch innerhalb einer Welle `Files:` der Kandidaten vergleichen; Überlappung → sequenziell. Gemeinsame Dateien (`CHANGELOG.md`, Golden-Fixtures `tests/fixtures/slimming-golden/`) erzwingen sequenzielles Mergen (Rebase vor Merge).
- **TDD wo sinnvoll:** Test zuerst (fail), dann Fix (pass). Ausnahmen (reine Doku/Prosa) im PR benennen.
- **Template-Änderungen:** Minor-Bump im Frontmatter `version:` jeder geänderten Template-Datei; geänderte gerenderte Ausgabe → Golden-Rebaseline als eigener Commit (`test: rebaseline … golden fixture`).
- **Hooks:** Quelle ist `hooks/1-generic/`; deployte Kopien in `.claude/hooks/` sind gitignored und werden per `python3 scripts/sync.py` neu erzeugt — nie direkt editieren.
- **Branches:** frischer Branch von `main` pro PR (`fix/sr-<id>-…`). Kein Push/Merge durch Implementierer — Rolle `git`.
- **Regression:** `python3 scripts/sync.py --validate` und `python3 -m pytest -q` grün vor jedem PR.

## File Structure (Welle 1)

- Modify: `scripts/admin-server.py` — Bare-Filename-Validierung Backup-Handler (T1)
- Create: `tests/test_admin_backup_name_validation.py` — Regression N1 (T1; bewusst neue Datei, um Kollision mit Plan #897 in `tests/test_admin_server.py` zu vermeiden)
- Modify: `hooks/1-generic/dod-push-check.sh`, `tests/test_dod_push_check_hook.py` (T2)
- Modify: `hooks/1-generic/orchestrator-guard-impl.sh`, `tests/test_orchestrator_guard_hook.py` (T3)
- Modify: 8 Templates in `agents/1-generic/` (T4); Create: `tests/test_template_report_paths.py` (T4)
- Modify: `agents/1-generic/senior-developer.md`, `agents/1-generic/orchestrator.md`, `tests/fixtures/slimming-golden/{senior-developer,orchestrator}.md`; Create: `tests/test_escalate_card_contract.py` (T5)
- Modify: `docs/ui/admin-ui.html`; Create: `tests/browser/test_admin_ui_keyboard.py` (T6)

---

## 1. Welle 1 — HIGH / Security-first (6 Tasks)

### Task W1-T1: Path-Traversal / Arbitrary File Delete über Backup-API (SR-D-01 / N1)

**Rolle:** `senior-developer` · **Effort:** S · **Depends on:** — · **ZWINGEND separates Security-Review**
**Files:** Modify `scripts/admin-server.py` (`_handle_delete_backup` ~`:5492`, `_handle_restore_backup` ~`:5483`); Create `tests/test_admin_backup_name_validation.py`. **Nicht** anfassen: `scripts/lib/backup.py` (der `Path(archive_name)`-Fallback ist CLI-Backend, `cli_commands.py:948/:992`, und wird von `tests/test_backup_robustness.py:80/:96`, `tests/test_backup_round_trip_804.py:107` genutzt — Trust-Boundary ist der HTTP-Handler).
**Interfaces:** Consumes HTTP-Suffix bzw. JSON-Body `archive_name`. Produces HTTP 400 `{"error":"bad_request","detail":"invalid archive name"}` bei ungültigem Namen; gültige Namen unverändert an `delete_backup`/`restore_backup`.

- [ ] Step 1: Test schreiben (fail) — Handler-Tests mit Wegwerf-Dateien unter `tmp_path` (Vorlage: `.tmp/n1-repro/repro.py`): `DELETE /api/backups//<tmp>/victim.txt` → 400, Datei existiert weiter; `DELETE /api/backups/../../outside/victim.txt` → 400; Restore mit `archive_name="/abs/x.zip"` und `"../x.zip"` → 400; Positivfall `agent-meta-backup-<ts>.zip` → wie bisher.
- [ ] Step 2: Implementieren — in beiden Handlern `re.fullmatch(r"[\w.-]+\.zip", name)` und `name not in (".", "..")`, sonst 400. Eine Helper-Funktion `_is_bare_backup_name(name)` für beide Handler.
- [ ] Step 3: `python3 -m pytest tests/test_admin_backup_name_validation.py tests/test_admin_server.py tests/test_backup_robustness.py tests/test_backup_round_trip_804.py -q` grün.
- [ ] Step 4: Commit `fix(admin): reject non-bare backup names in delete/restore handlers`

**Akzeptanzkriterien:**
- AC-1: Beide Repro-Varianten aus dem Verifier-Pass (absolut, `../`) liefern 400; die Opfer-Datei existiert nach dem Request.
- AC-2: Restore-Handler mit absolutem/relativem Traversal-Namen liefert 400, `restore_backup` wird nicht aufgerufen.
- AC-3: Bestehende CLI-Backup-Tests unverändert grün (Fallback in `lib/backup.py` unangetastet).
- AC-4: UI-Pfad (sendet nur `a.name`, `admin-ui.html:8310/:8320`) funktioniert unverändert.

**Out of scope (→ W2-D1):** Defense-in-depth-Containment in `delete_backup`, manifestgesteuerte Schreib-/`rmtree`-Pfade in `restore_backup` (`extra_files[].relative`, `providers.*.directory`).

### Task W1-T2: `--tags`-Bypass des Branch-Guards (SR-B-01 / B-01)

**Rolle:** `senior-developer` · **Effort:** S · **Depends on:** — · **ZWINGEND separates Security-Review**
**Files:** Modify `hooks/1-generic/dod-push-check.sh` (Tag-only-Erkennung `:135-144`); Test `tests/test_dod_push_check_hook.py`.
**Interfaces:** Produces `IS_TAG_ONLY_PUSH=true` nur, wenn **jedes** `git push`-Statement im Befehl ausschließlich Tag-Refs pusht.

- [ ] Step 1: Tests (fail) — Driver-Muster aus `.tmp/verify-b/b01.py` (`AGENT_META_TEST_COMMAND=false`, damit ein übersprungener Branch-Guard als andere Meldung sichtbar wird). Bypass-Fälle müssen „Branch-Guard: Push blocked" liefern: `git push origin main --tags`, `git push origin tag v1 main`, `git push origin --tags ; git push origin main`, `git push --tags && git push origin main`. Nicht-Regression (bleiben tag-only): `git push origin --tags`, `git push origin tag v1`, `git push origin refs/tags/v1`.
- [ ] Step 2: Implementieren — Befehl an Shell-Separatoren (`;`, `&&`, `||`, `|`, Newline) in Statements splitten; pro Push-Statement tag-only gdw. (a) `--tags` und keine positionale Ref außer Remote, oder (b) `tag <name>` ohne weitere Refs, oder (c) alle positionalen Refs `refs/tags/*`. `--follow-tags` = **kein** tag-only (pusht Branch mit). Gesamtbefehl tag-only nur, wenn alle Push-Statements tag-only sind.
- [ ] Step 3: `python3 -m pytest tests/test_dod_push_check_hook.py -q` grün; `python3 scripts/sync.py` → deployte Kopie aktualisiert.
- [ ] Step 4: Commit `fix(hooks): restrict tag-only push detection to pure tag refs`

**Akzeptanzkriterien:**
- AC-1: Alle 4 Bypass-Fälle aus dem Verifier-Repro werden auf `main` vom Branch-Guard geblockt (exit 2, Branch-Guard-Meldung).
- AC-2: Die 3 reinen Tag-Pushes bleiben tag-only (Release-Flow der `git`-Rolle unverändert).
- AC-3: Kein bestehender Test in `tests/test_dod_push_check_hook.py` ändert sein erwartetes Ergebnis.

### Task W1-T3: Strict-Mode fail-open ohne PyYAML (SR-B-10 / B-10, verifiziert MEDIUM, Welle 1 per Nutzer-Vorgabe)

**Rolle:** `senior-developer` · **Effort:** S · **Depends on:** — · **ZWINGEND separates Security-Review**
**Files:** Modify `hooks/1-generic/orchestrator-guard-impl.sh` (Strict-Mode-Auslesung `:774-826`, v.a. `import sys, yaml` `:788`); Test `tests/test_orchestrator_guard_hook.py` (neue Testfälle mit `tmp_path`-Projekt, Muster `test_elevation_attempts_are_audited` l.470/704 — **nicht** gegen das echte Repo, vgl. E-T-2). `hooks/lib/hook_common.sh` wird in Welle 1 **nicht** angefasst (gemeinsamer Reader = B-20, Welle 3).
**Interfaces:** Consumes `.meta-config/project.yaml`. Produces `STRICT` — fail-closed: existiert die Config, ist aber nicht mit PyYAML parsebar (ImportError oder YAMLError), entscheidet ein stdlib-Zeilenscan; trifft er einen Strict-Indikator (`mode: strict`, `strict: true`) oder ist er mehrdeutig → `STRICT=true` + stderr-Warnung.

- [ ] Step 1: Tests (fail) — Muster `.tmp/verify-b/b10.py`: tmp-Projekt mit `orchestrator:\n  mode: strict\n`, Main-Thread-Write; mit `PYTHONPATH=<dir mit yaml.py: raise ImportError>` → erwartet rc 2 (heute rc 0). Kontrolle: Projekt ohne Strict-Indikator + geshadowtes yaml → rc 0 (kein False-Block). Kaputtes YAML mit Strict-Indikator → rc 2.
- [ ] Step 2: Implementieren — `import yaml` in `try`; `except ImportError`/`yaml.YAMLError` → Fallback-Zeilenscan statt `print('false')`. Allein `import` in den `try` zu ziehen ist **kein** Fix (Verifier-Pass: der `except` druckt heute ebenfalls `'false'`).
- [ ] Step 3: `python3 -m pytest tests/test_orchestrator_guard_hook.py -q` grün; `python3 scripts/sync.py`.
- [ ] Step 4: Commit `fix(hooks): fail closed on unreadable strict-mode config`

**Akzeptanzkriterien:**
- AC-1: Strict-Projekt ohne PyYAML im Hook-Interpreter → Main-Thread-Write rc 2 mit Strict-Meldung (Verifier-Repro invertiert).
- AC-2: Nicht-strict-Projekt ohne PyYAML → rc 0.
- AC-3: Mit PyYAML: Verhalten identisch zu heute (alle bestehenden Tests unverändert grün).
- AC-4: Fail-Richtung konsistent mit repo-containment F4 (safe default bei unlesbarer Config); dokumentiert im Hook-Header.

### Task W1-T4: `/tmp/opencode`-Long-Report-Pfad in 8 Reviewer-Templates (SR-C-01 / C-01)

**Rolle:** `developer` · **Effort:** S · **Depends on:** —
**Files:** Modify `agents/1-generic/{backend-reviewer,database-reviewer,ui-reviewer,frontend-reviewer,ai-security-guardian,app-lifecycle-governor,prompt-governor,security-auditor}.md`; Create `tests/test_template_report_paths.py`.
**Interfaces:** —

Zwei Fix-Varianten laut Verifier-Pass:
- **Read-only-Quartett** (backend-/database-/ui-/frontend-reviewer, Tools nur `Read, Glob, Grep, TodoWrite`): Zeile durch #514-Wortlaut aus `agents/1-generic/code-reviewer.md:203-212` ersetzen (kompakte Summary + `chunk k/n`, Persistierung durch schreibfähige Rolle via Orchestrator empfehlen).
- **Schreibfähige 4** (ai-security-guardian, app-lifecycle-governor, prompt-governor, security-auditor — haben Bash bzw. Write): nur Pfad ändern auf `.tmp/<role>-<topic>.md` (kein Providername, innerhalb Repo-Containment).

- [ ] Step 1: Test (fail) — (a) `grep "/tmp/opencode"` über `agents/` = 0 Treffer; (b) die 4 Read-only-Reviewer enthalten den #514-Marker (z. B. „write-capable role"); (c) die 4 schreibfähigen enthalten `.tmp/`.
- [ ] Step 2: 8 Templates anpassen, Minor-Bump je Datei.
- [ ] Step 3: `python3 -m pytest tests/test_template_report_paths.py tests/test_template_slimming_equivalence.py -q` grün; `python3 scripts/sync.py --validate`.
- [ ] Step 4: Commits je Variante: `fix(templates): use read-only long-report contract in reviewer quartet`, `fix(templates): move long-report path into repo .tmp/`

**Akzeptanzkriterien:**
- AC-1: `grep -rn "/tmp/opencode" agents/` → 0 Treffer.
- AC-2: Kein Read-only-Template enthält eine Anweisung, selbst eine Datei zu schreiben.
- AC-3: Alle 8 Dateien mit gebumpter Minor-Version.

### Task W1-T5: ESCALATE-Card-Contract-Drift senior → principal (SR-C-06 + SR-C-07 Teil)

**Rolle:** `developer` · **Effort:** S · **Depends on:** — (nach W1-T4 mergen, falls Golden-Fixtures kollidieren — hier nicht der Fall, s. §6)
**Files:** Modify `agents/1-generic/senior-developer.md` (Escalation-Block `:133-139`, Workflow `:81-82`, Constraint `:153`), `agents/1-generic/orchestrator.md` (`:117` Tier-Tabelle, `:133` Classify-Route, abgleichen mit `:140-144`); Rebaseline `tests/fixtures/slimming-golden/senior-developer.md`, `tests/fixtures/slimming-golden/orchestrator.md`; Create `tests/test_escalate_card_contract.py`.
**Interfaces:** Produces ESCALATE-Card des senior-developer mit kanonischen Feldern aus `developer.md:118-119`: `ESCALATE_REASON` (kategorial) + `ESCALATE_METRIC` (quantifizierbar), zusätzlich zu `RECOMMENDED_TIER`/`TASK_SUMMARY`/`FAILURE_LOG`.

Scope-Korrektur gegenüber Verifier-Hinweis: `se-developer.md:136-137` und `se-junior-developer.md:125-126` tragen **bereits** `reason`/`metric` (Kleinschreibung) — sie erfüllen die Intake-Regel und werden in Welle 1 nicht angefasst; nur die Feldnamen-Vereinheitlichung gehört zu C-07 (W2-C2).

- [ ] Step 1: Test (fail) — senior-Block enthält `ESCALATE_REASON:` und `ESCALATE_METRIC:`; orchestrator.md: jede Beschreibung des principal-Gates nennt reason + metric (keine Stelle mehr mit nur „task summary + failure log").
- [ ] Step 2: senior-developer.md ergänzen (typisch `repeated_failure` / `attempts: 2`), Workflow-Schritt 7 + Constraint `:153` nachziehen; orchestrator.md `:117`/`:133` auf „task summary + failure log + reason/metric" angleichen. Minor-Bump beider Templates.
- [ ] Step 3: Golden-Rebaseline (eigener Commit); `python3 -m pytest tests/test_escalate_card_contract.py tests/test_template_slimming_equivalence.py tests/orchestration -q` grün.
- [ ] Step 4: Commits `fix(templates): add reason/metric to senior-developer escalation card`, `fix(templates): reconcile principal gate requirements in orchestrator`, `test: rebaseline senior-developer and orchestrator golden fixtures`

**Akzeptanzkriterien:**
- AC-1: Eine contract-konforme senior-Eskalation erfüllt die Orchestrator-Intake-Regel `:140-142` ohne Nachreichungsrunde.
- AC-2: orchestrator.md enthält keine widersprüchlichen principal-Gate-Definitionen mehr (`grep -n "task summary + failure log"` → jede Fundstelle nennt auch reason/metric).
- AC-3: Feldnamen identisch mit `developer.md:118-119`.

**Entscheidung C-07-Snippet:** **nicht** in Welle 1, sondern W2-C2. Begründung: Welle 1 schließt den Contract-Bruch mit minimalem Diff (2 Dateien). Das Snippet `{{ESCALATE_CARD_BLOCK}}` passt technisch (Präzedenz: Tupel in `scripts/lib/config.py:1989-1996` + `snippets/agents/*.md`), zieht aber `scripts/lib/config.py` (Konflikt mit W2-A4/W2-E3), eine Schema-Änderung in `junior-developer.md` (JSON-artiges `ESCALATE: {…}`), die se-*-Templates und weitere Golden-Rebaselines nach sich — das ist eine Contract-Vereinheitlichung, kein Security-Fix.

### Task W1-T6: Tastaturbedienbarkeit Navigation + Kernbedienelemente (SR-D-09 / A1, SR-D-15 / A7)

**Rolle:** `developer` (Review: `accessibility-specialist`) · **Effort:** M · **Depends on:** — (A1 vor A7 im selben PR, da ohne Navigation kein Tastatur-Zugang zu den Views)
**Files:** Modify `docs/ui/admin-ui.html` (Sidebar `:1631-1640`, Router-Aktivzustand `:1140-1142`, Rollen-Karten `:2113`/`:2137-2142`, Template-Liste `:5074`, Environment-Tabelle `:8545`); Create `tests/browser/test_admin_ui_keyboard.py`.
**Interfaces:** —

Scope: A1 (Sidebar) + A7-Blocker-Teile (Rollen-Karten, Template-Liste, Env-Tabelle). **Rules-Matrix-Teil von A7** (`:6352-6363`, verifiziert blocker → minor, Tastatur-Ausweichweg über `/project/rules-overrides`) → W3-D1.

- [ ] Step 1: Playwright-Test (fail, lokal): Tab erreicht jeden Nav-Eintrag, Enter navigiert, aktiver Eintrag hat `aria-current="page"`; Rollen-Karte per Space/Enter umschaltbar mit `aria-pressed`; Template-Zeile per Enter lädt Editor; Env-Zeile über Button in erster Zelle öffnet Modal.
- [ ] Step 2: Implementieren — Nav als `<a href="#/route">` (Router ist hash-basiert), `aria-current="page"` im Router-Loop, `🔒` mit Text „(read-only)"; Rollen-Karte als `<button aria-pressed>` mit nicht-farbigem Aktiv-Indikator (Häkchen/Text, 1.4.1-Hinweis des Verifiers); Template-Zeile als `<button>`; Env-Tabelle mit Button in erster Zelle.
- [ ] Step 3: `python3 -m pytest tests/browser/test_admin_ui_keyboard.py -q` lokal grün (Playwright läuft nicht in CI, E-CI-6 → Ergebnis im PR dokumentieren); manueller Tastatur-Durchlauf + ein Screenreader (NVDA oder VoiceOver) dokumentiert.
- [ ] Step 4: Commits `fix(admin-ui): make sidebar navigation keyboard operable`, `fix(admin-ui): make role cards, template rows and env rows keyboard operable`

**Akzeptanzkriterien:**
- AC-1: Jede Ansicht ist ausschließlich per Tastatur erreichbar (WCAG 2.1.1).
- AC-2: Rollen-Aktivierung, Template-Laden und Env-Bearbeitung ohne Maus möglich; Zustand programmatisch (`aria-pressed`/`aria-current`) verfügbar (4.1.2).
- AC-3: Keine `div`/`tr` mit `onclick` als einziger Aktivierungsweg in den vier genannten Stellen.
- AC-4: Bestehende Browser-Tests (`tests/browser/`) lokal grün.

---

## 2. Welle 2 — MEDIUM (17 Cluster)

Leitregel: ein Cluster = ein PR, Commit pro Finding. Mit „(mit)" markierte IDs sind niedriger eingestuft, werden aber wegen identischer Datei/Ursache im selben Cluster erledigt.

### 2.A scripts/lib (Rolle `senior-developer`, Review `code-reviewer`)

| Cluster | Findings | Files | AC (Kurz) | Effort | Depends |
|---|---|---|---|---|---|
| W2-A1 Gitignore-/Personal-File-Lecks | SR-A-11, SR-A-12 (mit; inkl. `gitignore.py:213` Name-Gate), SR-A-31, SR-A-32 (mit), SR-A-33 (mit) | `scripts/lib/sync_pipeline.py`, `scripts/lib/gitignore.py`, `scripts/lib/context.py`, `config/ai-providers.yaml` | Opencode-/Gemini-/Codex-only-Projekt: `.meta-config/env.*`, Viz-, Skill-Einträge und Personal-File in `.gitignore`; Test pro Provider-Set | M | — |
| W2-A2 `write_atomic` Datei-Modus | SR-A-15 | `scripts/lib/io.py`, Test | bestehende Datei behält Modus (inkl. +x), neue Datei `0o666 & ~umask`; `project.yaml` 0600 als expliziter Opt-in (#864) | S | — |
| W2-A3 `--validate` gegen echte Pipeline | SR-A-24, SR-A-25, SR-E-24 / E-T-13 (mit) | `scripts/lib/cli_commands.py`, `scripts/lib/sync_pipeline.py` (nur Aufruf der `_sync_stage_*`), Test | Exit-Code basiert auf `log.errors` des aktuellen Laufs; Test-Repo-Sync nutzt Produktions-Stages; neuer Test für `validate_test_repo` | M | W2-A1 (`sync_pipeline.py`) |
| W2-A4 Provider-Literale + Guard-Erweiterung | SR-A-06, SR-A-13 (mit), SR-A-21 (mit; inkl. `roles.py:353/383`) | `scripts/lib/context.py`, `scripts/lib/config.py` (`:834-848`), `scripts/lib/rules.py`, `scripts/lib/roles.py`, `tests/test_provider_agnostic_dispatch.py` | erweiterter Guard flaggt Provider-Namen in Call-Args/`.get()`/Subscripts/Defaults; 0 Treffer nach Fix (A-13/A-21 mitgenommen, sonst bleibt der Guard rot) | M | W2-A1 (`context.py`) |

### 2.B Hooks & Guards (Rolle `senior-developer`, **ZWINGEND separates Security-Review** für alle B-Cluster)

| Cluster | Findings | Files | AC (Kurz) | Effort | Depends |
|---|---|---|---|---|---|
| W2-B1 dod-push-check | SR-B-02, SR-B-03, SR-B-04 (mit, gleicher Fix), SR-B-21 | `hooks/1-generic/dod-push-check.sh`, `tests/test_dod_push_check_hook.py` | `HEAD:main`/`feat:main`/detached → Guard prüft Ziel-Ref (oder Boundary-Label bewusst herabgestuft, s. §5 Q5); `git -C . push`, `/usr/bin/git push` erkannt; `grep -rn git push docs` kein Block; 300-KB-Multiline-Push rc 2 (here-string statt `printf \| grep -q`) | M | W1-T2 |
| W2-B2 orchestrator-guard | SR-B-08, SR-B-11, SR-B-12, SR-B-13 | `hooks/1-generic/orchestrator-guard.sh`, `hooks/1-generic/orchestrator-guard-impl.sh`, `tests/test_orchestrator_guard_hook.py` | Wrapper mappt rc ∉ {0,2} → 2; Strict-Mode aus Unterverzeichnis aktiv (`$CLAUDE_PROJECT_DIR` vor `cwd`); 7 Destruktiv-Fälle mit `git`-Sentinel rc 2; pull/switch/cherry-pick/revert/am rc 2 im Main-Thread | S | W1-T3 |
| W2-B3 repo-containment | SR-B-16, SR-B-17, Verifier-Zusatz (`repo-containment-impl.sh:492` Detector-Crash fail-open, keine SR-ID) | `hooks/1-generic/repo-containment.sh`, `hooks/1-generic/repo-containment-impl.sh`, `tests/test_repo_containment_hook.py` | Heredoc-Bodies nicht als Befehle gescannt (Doku mit `> /etc/x` erlaubt); Wrapper rc ∉ {0,2} → 2; Detector-Crash → Block | S | — |

### 2.C Templates / Rules (Rolle `developer`, Review `code-reviewer`)

| Cluster | Findings | Files | AC (Kurz) | Effort | Depends |
|---|---|---|---|---|---|
| W2-C1 Output-Guard-Drift | SR-C-02, SR-C-03 (mit) | `agents/1-generic/{llm-evaluator,rag-engineer,ai-observability-engineer,ai-governance-engineer,code-reviewer}.md`, ggf. `snippets/agents/background-process-guard.md`, neuer Lint-Test | 4× `{{OUTPUT_GUARD_BLOCK}}`; code-reviewer nutzt `{{BACKGROUND_PROCESS_GUARD_BLOCK}}` (oder Variable entfernt); Test verbietet wörtliche Snippet-Bodies in Templates | S | W1-T4 (code-reviewer ist #514-Referenz) |
| W2-C2 ESCALATE-Card-Snippet | SR-C-07 (Rest nach W1-T5) | Create `snippets/agents/escalate-card.md`; Modify `scripts/lib/config.py` (Tupel `:1989`), `agents/1-generic/{junior-developer,developer,senior-developer,se-developer,se-junior-developer}.md`, Golden-Fixtures | ein kanonisches Feldschema in allen Developer-Tiers; `grep -n ESCALATE` zeigt nur `{{ESCALATE_CARD_BLOCK}}` + rollen-spezifische Tier-Werte | S | W1-T5; W2-A4 (`config.py`) |
| W2-C3 Platform-Override-Drift | SR-C-09, SR-C-10 | `agents/2-platform/*.md` (16 STALE) | `based-on` = aktuelle Generic-Version für alle 18; `replace` → `append-after` wo möglich; sharkord-developer ohne EN/DE-Duplikate + ohne unkonditionale Test-Zeile | M | W2-C2 (developer.md-Basis) |
| W2-C4 `a2a-delegation-gates` entschlacken | SR-C-13, SR-C-14 (mit), SR-C-15 (mit, info) | `rules/1-generic/a2a-delegation-gates.md`, `docs/concepts/a2a-handoff-protocol.md` | gerenderte SKILL.md ≤ ~3.5 KB; Maintainer-Prosa nach docs/concepts; kein `{{…}}` in Meta-Prosa | S | — |

### 2.D admin-server / admin-ui

| Cluster | Findings | Files | AC (Kurz) | Effort | Rolle | Depends |
|---|---|---|---|---|---|---|
| W2-D1 Server-Härtung | SR-D-02 / N2, SR-D-03 / N3 (verifiziert low, per Vorgabe hier), SR-D-05 / N5 (nur Restore/Delete; Create nicht betroffen), N1-Follow-up (manifestgesteuerte Pfade in `restore_backup`, keine SR-ID) | `scripts/admin-server.py`, `scripts/lib/backup.py`, Create `tests/test_admin_server_hardening.py` | `grep -n 'rfile.read' scripts/admin-server.py` → nur `_read_body`; UI-Shell sendet `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `nosniff`, `no-referrer`; `success: false` → 4xx; `extra_files[].relative`/`providers.*.directory` gegen `project_root` containt | M | `senior-developer`, **ZWINGEND separates Security-Review** | W1-T1; Plan #897 (§6) |
| W2-D2 Dialoge + Ansagen | SR-D-10 / A2, SR-D-16 / A8, SR-D-23 / A15 | `docs/ui/admin-ui.html`, `tests/browser/` | Modal + Token-Prompt als `<dialog>` (Rolle, Escape, Fokus-Einschluss, Rückgabe); Toast-Container `role="status"`, Fehler `role="alert"` ohne Auto-Remove; Token-Fehler per `aria-describedby` | M | `developer`, Review `accessibility-specialist` | W1-T6; W2-D1 (N5-Fehlerpfad in UI) |
| W2-D3 Labels, Fokus, Kontrast, Reflow | SR-D-11 / A3, SR-D-12 / A4, SR-D-13 / A5, SR-D-18 / A10, SR-D-20 / A12 | `docs/ui/admin-ui.html`, `tests/browser/` | Icon-Buttons mit `aria-label`; alle Feld-Helfer nutzen `a11yField`-Muster (ID + `for`); `:focus-visible` auf Toggles; `--text-muted` ≥ 4.5:1 auf allen Hintergründen; einspaltiges Layout < 640 px, 400 %-Zoom manuell geprüft | M | `developer`, Review `accessibility-specialist` | W2-D2 (gleiche Datei) |

### 2.E config / tests / CI (Rolle `developer`, Review `code-reviewer`)

| Cluster | Findings | Files | AC (Kurz) | Effort | Depends |
|---|---|---|---|---|---|
| W2-E1 CI-Timeouts + echte Artefakt-Tests | SR-E-01 / E-CI-1, SR-E-14 / E-T-3 (mit), SR-E-12 / E-T-1 | `.github/workflows/{orchestration-test,validate}.yml`, `_run_hook`-Helper in ~6 Testdateien | jeder Job `timeout-minutes`; Hook-Subprozesse mit `timeout=30`; ein Matrix-Leg führt `python scripts/sync.py` vor pytest aus, Skip-Zahl sinkt um die Generated-Artifact-Skips | S | W2-B1, W2-B2, W2-B3 (gleiche Testdateien) |
| W2-E2 Guard-Tests isolieren | SR-E-13 / E-T-2 | `tests/test_orchestrator_guard_hook.py` | alle Hook-Tests laufen gegen `tmp_path`-Projekt; `.claude/hooks/.guard-audit.log` des Repos wächst bei Testlauf nicht | S | W2-B2 (gleiche Datei) |
| W2-E3 Schema + Tier-Presets | SR-E-07 / E-CFG-1, SR-E-08 / E-CFG-2 (mit), SR-E-10 / E-CFG-4 (`ultra`-Teilclaim gestrichen, Verifier) | `config/project-config.schema.json`, `scripts/lib/config.py` (`_KNOWN_NON_OBJECT_KEYS`), `scripts/lib/roles.py`, `config/tier-presets.yaml` | 9+ Top-Level-Keys im Schema deklariert; `rules-preset: null` wird gedroppt; Warnung, wenn aktives Preset keinen Eintrag für einen aktiven Provider hat | M | W2-A4, W2-C2 (`config.py`) |

---

## 3. Welle 3 — LOW / INFO (21 Cluster)

**Leitregel: Cluster-PRs statt Einzel-PRs** — gebündelt je Datei/Modul, Commit pro Finding. Rollen: `developer` (Hooks: `senior-developer` + **ZWINGEND separates Security-Review**; UI: Review `accessibility-specialist`). AC je Finding = die Verifikation aus der Review-Zeile, invertiert (z. B. Repro liefert jetzt das erwartete Ergebnis); TDD wo Verhalten betroffen.

| Cluster | Findings | Bereich / Files |
|---|---|---|
| W3-A1 | SR-A-01, -02, -03, -04, -26 | `scripts/sync.py`, `scripts/lib/cli_commands.py`, `scripts/lib/generated_file_drift.py` |
| W3-A2 | SR-A-05, -07, -08, -09, -10, -27, -28, -41 | `scripts/lib/providers.py`, `config.py`, `deactivation.py` (gemeinsamer `_as_dict`-Helper, Registry-Cache mit `deepcopy`) |
| W3-A3 | SR-A-18, -19, -20, -22, -23 | `scripts/lib/rules.py` |
| W3-A4 | SR-A-14, -29, -30, -34, -35 | `scripts/lib/sync_pipeline.py` (Rename `is_claude`), `config.py`, `context.py`, Guard-Test gegen rohe `.write_text` |
| W3-A5 | SR-A-36, -37, -38, -39, -40 | Dead Code (`provider_transform.py`, `context.py`, `reflection.py`, `pipelines.py`, `deactivation.py`, `config_audit.py`, `standalone.py`, `viz.py`) + Doku-Drift (`CHANGELOG`, `docs/guides/quality-pipelines.md`) |
| W3-A6 | SR-A-16, -17 | `scripts/lib/io.py` |
| W3-B1 | SR-B-05, -06, -07 | `hooks/1-generic/dod-push-check.sh` |
| W3-B2 | SR-B-09, -14, -15 | `hooks/1-generic/orchestrator-guard-impl.sh` |
| W3-B3 | SR-B-18, -19, -20 | `hooks/1-generic/repo-containment-impl.sh`, `hooks/lib/hook_common.sh` (gemeinsamer stdlib-YAML-Subset-Reader; danach W1-T3-Zeilenscan darauf umstellen) |
| W3-B4 | SR-B-23, -24, -25, -27, -28, -29 | `hooks/1-generic/pre-release-check.sh`, `hooks/1-generic/release-gates/*.sh`, `docs/RELEASE_GATES.md` |
| W3-B5 | SR-B-22, -26, -30, -31, -32, -33 | `lifecycle-check.sh` (inkl. toter Branch `:88`), `antigravity-json-adapter.sh`, `viz-log.sh`, `scripts/lib/hook_plugins.py`, Boundary-Tabelle in `.claude/rules/branch-guard.md`-Quelle |
| W3-C1 | SR-C-04, -11, -12 | `snippets/agents/{output-guard,background-process-guard}.md` (EN), `agents/1-generic/developer.md`, `scripts/lib/config.py` (`ANTI_RECURSION_BLOCK` EN), Golden-Fixtures |
| W3-C2 | SR-C-05, -08 | `/tmp/` → `.tmp/` in `code-reviewer.md`, `docker.md`, `devops-engineer.md`; `concept-reviewer.md:157`; W1-T4-Test auf `/tmp/` allgemein ausweiten |
| W3-C3 | SR-C-16, -17, -18 | `rules/2-platform/agent-meta-conventions.md`, `rules/1-generic/use-lazy-rules.md` (generiert statt handgepflegt), `rules/1-generic/issue-lifecycle.md` |
| W3-D1 | SR-D-14 / A6, SR-D-19 / A11, SR-D-21 / A13 (advisory), SR-D-22 / A14, A7-Rules-Matrix-Teil | `docs/ui/admin-ui.html` |
| W3-D2 | SR-D-07 / X1, SR-D-08 / X2 | `docs/ui/admin-ui.html` — mit Task 897-4 / #896 abstimmen (X2-Toast-Text gehört ggf. in 897-4) |
| W3-D3 | SR-D-04 / N4, SR-D-06 / N6 | N4: nur Abhaken nach Merge 897-1/897-2 (keine eigene Arbeit); N6: #730 reopen oder Folge-Issue (Prozess, Rolle `git`/Orchestrator) |
| W3-E1 | SR-E-02, -03, -04, -05, -06 | `.github/workflows/*.yml` (E-CI-5 = 3.9-Leg für Szenarien, E-CI-6 = opt-in/nightly Playwright-Job) |
| W3-E2 | SR-E-09 / E-CFG-3, SR-E-11 / E-CFG-5 | `templates/configs/*`, Schema-Test parametrisieren; `config/ai-providers.yaml`, `config/provider-capabilities.yaml` (`# doc-only`) |
| W3-E3 | SR-E-15 / E-T-4, SR-E-22 / E-T-11, SR-E-23 / E-T-12 (Scope 5/3 Dateien) | Test-Infrastruktur: ein Import-Root via `conftest.py`, `MappingProxyType`/deepcopy für gecachte Returns |
| W3-E4 | SR-E-16 / E-T-5, SR-E-17 / E-T-6, SR-E-18 / E-T-7, SR-E-19 / E-T-8, SR-E-20 / E-T-9, SR-E-21 / E-T-10 | Testqualität / Negativpfade (`test_artifact_freshness_hook.py`, `test_barrier_runtime.py`, `test_backup_robustness.py`, `test_exception_specificity.py`, `test_release_scaffold.py`, `test_gitignore_keep.py` + `gitignore.py`-Normalisierung, `test_recommended_skills_registry.py`, `test_routing_tool_definitions.py`) |

Nicht umgesetzt: SR-D-17 / A9 (FALSE_POSITIVE als WCAG-Befund) — nur als UX-Hinweis an `ui-ux-designer`, kein Task.

---

## 4. Design-Gates — nicht autonom

Explizit **aus allen drei Wellen ausgeschlossen**. Umsetzung erst nach Nutzer-Entscheidung; kein Agent startet diese autonom.

| Issue | Thema | Warum Design-Gate |
|---|---|---|
| #783 | Konfigurierbare Merge-Policy | Ändert die Durchsetzung im `orchestrator-guard` (wer darf mergen, unter welchen Bedingungen) — Policy-Entscheidung des Nutzers, per Nutzer-Anweisung nicht autonom. |
| #548 | RFC/Design-Platzhalter | Offener Design-Placeholder ohne beschlossene Richtung — braucht Nutzer-Entscheidung vor jeder Spec. |
| #547 | RFC/Design-Platzhalter | Offener Design-Placeholder ohne beschlossene Richtung — braucht Nutzer-Entscheidung vor jeder Spec. |
| #330 | RFC/Design-Platzhalter | Offener Design-Placeholder ohne beschlossene Richtung — braucht Nutzer-Entscheidung vor jeder Spec. |
| #329 | RFC/Design-Platzhalter | Offener Design-Placeholder ohne beschlossene Richtung — braucht Nutzer-Entscheidung vor jeder Spec. |

## 5. Verwandt, nicht Teil dieser Wellen

- **#897** (OPEN, bug/P2/security — Origin-Check im Network-Mode) und **#896** (OPEN, enhancement — Network-Mode-Start): eigener paralleler Plan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md` (DRAFT). Die D1–D6-Bestätigungen aus Dimension (d) sind dort verortet; dieser Plan wiederholt sie nicht. Koordination: §6.
- **#899, #855, #528** — alle drei **CLOSED** (per `gh` verifiziert). **Korrektur** zur früheren Annahme, es gebe hier „Rest"-Arbeit: kein Rest, nichts zu planen.
- **#778** (OPEN, design/templates/audit-2026-09 — 53-Template-Literatur-Audit): thematisch nah an SR-C, aber eigenständiger, größerer Audit → Backlog, nicht Teil dieser Wellen.
- **#779** (OPEN, Routing-Audit — Intent-Routing-Tabelle, 272 fehlende deutsche Keywords): eigenständiger Audit → Backlog.
- **#676** (OPEN, HACS-Best-Practice-Lücken): andere Domäne (Home-Assistant-Integration), vom Review nicht berührt → Out-of-scope-Backlog.

## 6. Abhängigkeiten

```
Welle 1 (alle 6 file-disjunkt → parallel dispatchbar; Merge sequenziell wegen CHANGELOG):
  W1-T1 (admin-server.py)        ─┐
  W1-T2 (dod-push-check.sh)      ─┤
  W1-T3 (orchestrator-guard-impl)─┤
  W1-T4 (8 Reviewer-Templates)   ─┤
  W1-T5 (senior-dev, orchestrator, Golden) ─┤
  W1-T6 (admin-ui.html)          ─┘
  Externe Kollision: W1-T1/W1-T6 vs. Plan #897 (admin-server.py, admin-ui.html) → W1-T1 vor 897-PRs mergen (N1 vor #896 schließen)

Welle 2:
  W1-T2 → W2-B1 ─┐
  W1-T3 → W2-B2 ─┼→ W2-E1
          W2-B3 ─┘
  W2-B2 → W2-E2
  W2-A1 → W2-A3
  W2-A1 → W2-A4 → W2-C2 → W2-E3        (context.py / config.py-Kette)
  W1-T5 → W2-C2 → W2-C3
  W1-T4 → W2-C1
  W2-A2, W2-C4: unabhängig
  W1-T1 → W2-D1 → W2-D2 → W2-D3        (admin-server.py, dann admin-ui.html sequenziell)
  W1-T6 → W2-D2

Welle 3: startet je Cluster, sobald der Welle-2-Cluster derselben Datei gemergt ist
  W2-A* → W3-A*;  W2-B1 → W3-B1;  W2-B2 → W3-B2;  W2-B3 → W3-B3 (+ W1-T3 für Reader-Umstellung)
  W2-C* → W3-C*;  W2-D3 → W3-D1 → W3-D2;  897-1/897-2 gemergt → W3-D3 (N4)
  W2-E1 → W3-E1;  W2-E3 → W3-E2;  W2-E2 → W3-E3/W3-E4
```

Parallel-Gruppen Welle 2 (file-disjunkt, gleichzeitig dispatchbar): {W2-A1, W2-A2, W2-B1, W2-B2, W2-B3, W2-C1, W2-C4, W2-D1}.

## 7. Offene Entscheidungsfragen

1. **C-07-Snippet-Timing:** Plan legt `{{ESCALATE_CARD_BLOCK}}` nach W2-C2 (Begründung bei W1-T5). Bestätigen oder in Welle 1 vorziehen?
2. **Security-Review-Rolle:** `security-auditor` ist in diesem Projekt nicht generiert (`.claude/agents/` enthält ihn nicht), DoD-Preset `rapid-prototyping` hat `security-audit: false`, `ai-security-review: false`, `prompt-governance: false`. Default des Plans: separater `code-reviewer`-Durchlauf mit Security-Checkliste. Soll stattdessen `security-auditor` aktiviert oder das DoD-Preset für diese Welle angehoben werden? `ai-security-review`/`ai-governance` sind für die admin-server-Fixes fachlich nicht einschlägig (keine LLM-Funktion) — bestätigen.
3. **B-10-Fail-closed-Semantik:** Plan wählt stdlib-Zeilenscan (Strict-Indikator gefunden/mehrdeutig → strict). Alternative: Hard-Block jedes Main-Thread-Writes, sobald `project.yaml` existiert und PyYAML fehlt (strenger, blockiert aber auch nicht-strikte Projekte). Welche Variante?
4. **B-01 `--follow-tags`:** Plan behandelt `--follow-tags` als Branch-Push (Guard greift). Bestätigen.
5. **B-02/B-07 Boundary-Label von dod-push-check:** Ziel-Ref-Parsing implementieren (M) oder „security boundary"-Claim auf „convention boundary mit einer fail-closed-Eigenschaft" herabstufen und auf Remote-Branch-Protection verweisen?
6. **Reihenfolge zu Plan #897:** #897-Plan ist DRAFT. W1-T1 vor den 897-PRs mergen (Plan-Default) — und soll A8 (Live-Region) in Task 897-4 wandern, damit AC-897-7 für AT-Nutzer erfüllt ist, statt in W2-D2?
7. **N6 / #730:** Reopen von #730 oder neues Folge-Issue für die offenen A11y-Punkte?
8. **E-T-2 Audit-Log-Bereinigung:** 246 Testzeilen in der lokalen, ungetrackten `.claude/hooks/.guard-audit.log` — bereinigen (`grep -v 'agent=orchestrator echo test'`) oder bis W2-E2 belassen? Nutzer-Entscheidung, da Audit-Trail.
9. **ID-Mapping SR-D/SR-E:** aus Dim-Dateien abgeleitet (§0.2), da der konsolidierte Report nicht auf `main` liegt — nach Merge des Review-PRs gegenprüfen.
10. **Playwright in CI:** W1-T6/W2-D2/W2-D3 können Tastatur-AC nur lokal belegen (E-CI-6). Reicht lokaler Nachweis + manueller Test im PR, oder E-CI-6 (opt-in-Job) aus Welle 3 vorziehen?

## Self-Review

- Jeder Wave-1-Task mappt auf genau eine Rolle; jedes AC ist beobachtbar (rc, HTTP-Status, grep-Zählung, Tastatur-Durchlauf).
- `Files:`/`Interfaces:` für Welle 1 vollständig; Welle 1 ist file-disjunkt; Welle-2-Überlappungen als Kanten in §6.
- Alle 138 gültigen Findings genau einem Cluster/Task zugeordnet (7 + 48 + 83); A9 begründet ausgeschlossen; Verifier-Zusatzbefunde ohne SR-ID (N1-Follow-up, `repo-containment-impl.sh:492`) explizit verortet.
- `pipeline_stages` deckt die `plan-driven`-Stage `implement` ab.
