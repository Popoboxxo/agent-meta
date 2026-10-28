---
status: geplant
spec-id: SPEC-FLEET-SERVER-2026-10-23
issues: "#682 §7 (Primärquelle); abgegrenzt: #877, #977, #528-#531"
pipeline_stages:
  implement: 3
---

# Fleet-Server F2 (Schreibpfad, Phase 3+4) — Implementation Plan

> Status: geplant
>
> **Freigabevermerk:** offen. Der Plan ist erst ausführbar, wenn die Spec den Approval-Marker (`Status: APPROVED`) trägt; der Marker wird nur vom Nutzer gesetzt, nie vom Planer. Bis dahin meldet `python3 scripts/sync.py --validate-spec-plan` für diesen Plan ein ERROR `spec_plan_approval_marker` (Spec R-14); das ist erwartet.

> **Hinweis Tests (D8):** Die Test-Tasks `F2-T1` bis `F2-T5` (Task 9, 10, 11, 18, 19) sind **separate Tasks und kein Merge-Gate** (DoD `rapid-prototyping`); kein Verifikations-Task (F2-V1, F2-V2) hängt per `Depends on:` von ihnen ab. Die als **„empfohlen (Security)"** markierten Tests (Write-Gate `allow-remote-write`, Bestätigungs-Nonce, Lösch-/Pfad-Prüfung, Busy-Gate, Token-/Widerrufs-Zusammenspiel) sollten trotz D8 umgesetzt werden, bevor Phase 3 produktiv geschaltet wird. AC-54 ist gestrichen (User, 2026-10-28, D11): es gibt keinen `SyncExecutor`-Test. Task 11 (F2-T3) prüft das Fleet-eigene Busy-Gate `FLEET_WRITE_GATE` auf Unit-Ebene (AC-52) und ist deshalb ebenfalls „empfohlen (Security)" (AC-52 steht in der Security-Liste der Spec).

> **Task-Nummern und Labels:** Task-Header tragen eine rein numerische ID (maschinenlesbar) plus das Label `F2-<Gruppe><n>` im Titel. `Depends on:` verwendet ausschließlich die Nummern. Im Fließtext stehen Labels; die Zuordnung Label ↔ Nummer steht in der Tabelle unter „Ausführungsmodell".

**Goal:** Das Fleet-Dashboard kann auf einer Instanz mit `fleet.allow-remote-write: true` nach expliziter Bestätigung einen Sync auslösen (Phase 3) und allowlist-begrenzte Schlüssel der `.meta-config/project.yaml` ändern (Phase 4) — mit Bestätigungs-Nonce, optionalem Write-Token, instanzseitig autoritativem Gate, Busy-Gate, Dedupe, optimistischer Hash-Prüfung, Admin-UI-Validierungsparität, Abbruch bei Kommentarverlust (`error/comments_lost`, D12) und beidseitigem Audit.
**Architecture:** F2 ergänzt F1 additiv. Server (`scripts/fleet-server.py`): Write-Gate-Kette (Admin-Token → Write-Token → `write_disabled` → Offline → Nonce) vor dem bestehenden Enqueue. Client (`scripts/lib/fleet_client.py`): Write-Pfad im Poll-Thread (Gate, Dedupe, Arg-Prüfung, danach nicht-blockierendes modulweites Fleet-Busy-Gate `FLEET_WRITE_GATE`) plus genau ein Worker-Thread `fleet-write`; reine Funktionen `validate_write_args` und `apply_config_ops`. Admin-Server (`scripts/admin-server.py`): Extract-Method `AdminRequestHandler._validate_project_document`, neuer keyword-only Parameter `roundtrip_guard: bool = False` in `ConfigManager.write`, injizierte Write-Handler `trigger-sync` und `put-config`. `SyncExecutor`, `_run`, `_record_run` und alle Admin-Routen bleiben unverändert (D11). Dashboard (`docs/ui/fleet-ui.html`): Bestätigungsdialog und Config-Edit-Dialog.
**Tech Stack:** Python 3.9/3.11/3.12 (nur Stdlib; PyYAML nur über bestehendes `lib.config`/`ConfigManager`), unittest/pytest (`python3 -m pytest`), Vanilla-JS/HTML, Markdown.
**Spec:** docs/specs/2026-10-23-fleet-server-spec.md
**Spec-ID:** `spec-id: SPEC-FLEET-SERVER-2026-10-23` (Rev. 1.4, Entwurf). Plan F1 (Fundament, Phase 1+2): `docs/plans/2026-10-23-fleet-server-f1-plan.md` (Task-Gruppen F1-A bis F1-I, F1-T laut Spec-Trace-Anker). **Abhängigkeit: F2 startet erst nach Merge von F1.**

## Entry-/Exit-Kriterien

**Entry (alle erfüllt, bevor Task 1 (F2-S1) startet):**
1. Plan F1 ist gemergt und seine Exit-Kriterien (Spec Abschnitt Phasen: AC-1 bis AC-32, AC-47 bis AC-51, `python3 scripts/sync.py --validate` grün, manueller End-to-End-Lauf dokumentiert) sind erfüllt. Prüfung: `scripts/fleet-server.py`, `scripts/lib/fleet_client.py`, `scripts/lib/fleet_protocol.py`, `scripts/lib/redaction.py`, `docs/ui/fleet-ui.html` existieren auf dem Arbeitsbranch. `allow_remote_write` wird aus dem F1-Status (F1 Task 13, `build_status`) konsumiert, nicht in F2 neu erzeugt.
2. Der Nutzer hat die Spec freigegeben (`Status: APPROVED`).
3. Einziger offener Eintrittspunkt: O-F3 (Inhalt `REMOTE_WRITE_ALLOWLIST`) ist entschieden oder der Default ist vom Nutzer ausdrücklich akzeptiert; der Plan setzt die Liste aus IC-15 um. O-F1, O-F2 und O-F9 sind geschlossen (D9, D12, D10); O-F2 = Abbruch bei Kommentarverlust (`error/comments_lost`, Datei unverändert, kein Backup).
4. Phase 1+2 laufen mindestens auf einer realen Instanz (Entry Phase 3) und der Threat-Model-Abschnitt der Spec ist für den Schreibpfad durch `concept-reviewer` erneut gereviewt (Wirksamkeitsprüfung laut Threat Model, Frage 4).
5. Arbeitsbranch laut `.claude/rules/branch-guard.md`: Phase 3 auf `feat/fleet-server-f2` (angelegt durch den `git`-Agenten von aktuellem `main`); Phase 4 auf `feat/fleet-server-f2-phase4` (von `main` nach dem Merge von Phase 3). Keine Tasks auf `main`.

**Exit Phase 3 (vor PR-Hand-off Phase 3; Tasks 1 bis 8 (F2-S1 bis F2-D1), 9 bis 11 (F2-T1 bis F2-T3), 12 (F2-V1)):**
1. AC-37, AC-38, AC-39, AC-40, AC-46, AC-52 sind erfüllt (AC-54 ist gestrichen, nicht erforderlich, D11) (Nachweis: Test-Tasks 9 bis 11 (F2-T1 bis F2-T3) grün, soweit umgesetzt; sonst Code-Inspektion/Grep laut Task 12 (F2-V1)).
2. `python3 scripts/sync.py --validate` Exit 0 (Task 12 (F2-V1)).
3. Manueller End-to-End-Lauf (Loopback, `--state-dir .tmp/…`) dokumentiert (Task 12 (F2-V1)).
4. Abschnitt „Schreibpfad (Phase 3)" in `docs/howto/fleet-server.md` und Write-Teil in `docs/api/fleet-api-reference.md` vorhanden (Task 8 (F2-D1)).

**Exit Phase 4 (vor PR-Hand-off Phase 4; Tasks 13 bis 15 (F2-B4 bis F2-B6), 16 (F2-C2), 17 (F2-D2), 18 und 19 (F2-T4, F2-T5), 20 (F2-V2)):**
1. AC-41, AC-42, AC-43, AC-44, AC-45, AC-53 sind erfüllt (Tasks 18/19 (F2-T4/F2-T5) soweit umgesetzt bzw. Grep-Nachweise in Task 20 (F2-V2)).
2. Das Admin-UI-Verhalten von `PUT /api/config/project` ist unverändert (bestehende Tests in `tests/test_admin_server.py` vor und nach der Extraktion identisch grün).
3. `python3 scripts/sync.py --validate` Exit 0; manueller `put-config`-Lauf inkl. Backup-Wiederherstellung dokumentiert (Task 20 (F2-V2)).

## Rollback je Phase

| Phase | Sofortmaßnahme (ohne Code) | Code-Rollback |
|---|---|---|
| 3 | `fleet.allow-remote-write: false` in `.meta-config/project.yaml` (wirkt ohne Neustart nach ≤ 1 Intervall, AC-46) | Revert des Phase-3-PR (durch `git`-Agent). Ohne Write-Handler antwortet die Instanz `unknown_command` (F1-Verhalten), der Server lehnt Write-Typen wieder als `unknown_command` ab. Das Fleet-eigene Gate `FLEET_WRITE_GATE` (F2-B1) ist Teil des Reverts; die Admin-UI ist nie betroffen, weil `SyncExecutor` unverändert bleibt (D11). |
| 4 | wie Phase 3; zusätzlich Wiederherstellung der Datei aus dem im Ack gemeldeten Backup (`backup`-Feld, von `ConfigManager.write` angelegt) | Revert des Phase-4-PR. Die Extraktion `_validate_project_document` und der Parameter `roundtrip_guard` (Default `False`) sind für die Admin-UI verhaltensneutral und dürfen im Revert enthalten sein. Bei `error/comments_lost` ist keine Wiederherstellung nötig (Datei unverändert, kein Backup). |

## Reihenfolge und Merge

- Serielle Merge-Reihenfolge: **F1 → F2 Phase 3 → F2 Phase 4**. Zwei PRs (je Phase eigene Entry-/Exit-Kriterien und Rollback), `git`-Agent für Push/PR/Merge.
- Datei-Überlappung mit dem Netzplan (`SPEC-897-896-ADMIN-UI-NETWORK-2026-10-07`, Spec R-2): F2 ändert in `scripts/admin-server.py` ausschließlich `ConfigManager.write` (neuer keyword-only Parameter `roundtrip_guard`, Default verhaltensneutral), `AdminRequestHandler._route_put_config` (Extract-Method), neue Modulfunktionen und `_maybe_create_fleet_client` (Argument `write_handlers`); `SyncExecutor`, `_run`, `_record_run` und die Routen bleiben unberührt (D11). Wer später merged, rebased.
- Commit-Grenzen: ein Commit je Task (Schritt „commit" im Task), Conventional Commits, Englisch, ≤ 72 Zeichen, Imperativ; Commit durch die per `auto_commit` freigeschaltete Rolle bzw. den Orchestrator (vorher Secret-Scan über die gemeldeten Dateien); Push/Branch/PR nur `git`.

## Global Constraints

- **Task-Format (maschinenlesbar):** `### Task <Nr>: F2-<Gruppe><n> — <Titel>` mit rein numerischer `<Nr>`; zeilenverankerte Felder `**Agent:**`, `**Depends on:**` (nur Task-Nummern dieses Plans, kommagetrennt, `—` für keine), `**Files:**` mit je einer Zeile `- Create:`/`- Modify:` mit Pfad in Backticks; `**Interfaces:**` mit Inhalt **auf derselben Zeile** (`Produces: …; Consumes: …`, Trenner `;`, keine Unterlisten direkt unter dem Feld).
- Nur Python-Stdlib, Python-3.9-kompatibel (`from __future__ import annotations`, kein `match`, kein `X | Y` zur Laufzeit außerhalb von Annotationen); `scripts/lib/consistency/python_compat.py` deckt die Dateien aus F1 bereits ab (`tests/test_python_compat_consistency.py` bleibt grün).
- Provider-agnostisch (Skill `provider-agnostic`): kein `if provider == "Name"`.
- Security-Invarianten (Spec IC-4, IC-14, IC-15): Gate `allow-remote-write` instanzseitig autoritativ und bei jedem Write-Kommando frisch aus der Config geladen (fail closed bei Lesefehler); `expires_at` wird instanzseitig nie ausgewertet; Token nur im Header, nie in Logs/Audit; Vergleich von Tokens/Nonces ausschließlich per `hmac.compare_digest` (kein `==`); Audit-`detail` immer durch `redact_text`.
- **Ack-Regel (IC-4):** `rejected` nur vor `accepted` (Poll-Thread); nach `accepted` sendet ausschließlich der Worker genau ein Terminal-Ack `ok|error`. Jede Ablehnung im Handler (im Handler erkannter Fleet-Busy-Zustand, dateiabhängige `put-config`-Prüfungen, `apply_config_ops`-Fehler → `invalid_args`, `YamlRoundTripLoss` → `comments_lost`) wird `error` mit Code. `busy` stammt ausschließlich aus dem Fleet-Gate `FLEET_WRITE_GATE`, nie aus `SyncExecutor`.
- **Busy-Gate-Reihenfolge (Review-Minor 2, Spec IC-4):** `remote_write`-Prüfung, Dedupe und reine Arg-Prüfungen laufen im Poll-Thread **vor** `FLEET_WRITE_GATE.acquire(blocking=False)`; zusätzlich gibt jeder Pfad nach dem `acquire`, der nicht zum Worker-Übergabe-Erfolg führt, das Gate wieder frei (`try/except` um Einreihung). Eine `rejected`-Antwort (`path_not_writable` u. a.) darf nie zu `busy` beim nächsten Write führen.
- **Modulweites Fleet-Gate (D11):** Das Busy-Gate ist `FLEET_WRITE_GATE = threading.Semaphore(1)` auf Modulebene von `scripts/lib/fleet_client.py` (keine Instanzvariable; überlebt einen `FleetClient`-Neustart im selben Prozess). Es serialisiert nur fleet-ausgelöste Writes untereinander.
- **Keine Änderung an `SyncExecutor`/Admin-Routen (D11, AC-54 gestrichen):** Kein gemeinsames Lock, kein Busy-Marker in `_run`, `_record_run` unverändert, keine neuen Busy-Antworten an `POST /api/sync/*`, `/api/models/update`, `/api/roles/cleanup/*`. Paralleler Sync aus Admin-UI und Fleet ist akzeptiertes Risiko (R-16, PA-8).
- Tests: unittest-Klassen (bestehende Konvention in `tests/test_admin_server.py`), lauffähig mit `python3 -m pytest`; Server-State nur unter `--state-dir`/`tempfile`; TLS-Tests (falls nötig) erzeugen Wegwerf-Zertifikate zur Laufzeit per `openssl req -x509` und werden bei fehlendem `openssl` per `skip` übersprungen; kein eingecheckter Private Key.
- Agenten starten Server-Prozesse nur mit `--state-dir .tmp/…` (Repo-Containment, Spec A6/R-10).
- Sprachregeln: Dokumente Deutsch, Code-Kommentare/Logmeldungen/Commit-Messages Englisch.
- Ausführung nach Skill `plan-ledger`: frischer Subagent je Task, zweistufiges Review (req → quality), **kein** `isolation: "worktree"`.
- Zeilenangaben sind Orientierung (Stand Branch `docs/fleet-server-spec-plans`, Commit `c0e6e8ff`, `scripts/admin-server.py` 5946 Zeilen); maßgeblich sind die Symbole. F1-Symbole in `fleet-server.py`/`fleet_client.py`/`fleet-ui.html` waren bei Planerstellung noch nicht vorhanden und werden in Task F2-S1 inventarisiert.
- Aufwand: Schätzung über `effort-estimator` (Textreferenz, nicht von diesem Plan berechnet).

## Ausführungsmodell

- DAG Phase 3: Task 1 (`F2-S1`) zuerst; danach `F2-A1 ∥ F2-B1` (Tasks 3, 2; `parallel_group: g1`, ownership-disjunkt: `scripts/fleet-server.py` vs. `scripts/lib/fleet_client.py`); `F2-B2` (Task 4) folgt auf `F2-B1` (gleiche Datei `scripts/lib/fleet_client.py`, daher nicht in `g1`); danach `F2-A1, F2-S1 → F2-A2` (3, 1 → 5); `(F2-B1, F2-B2) → F2-B3` (2, 4 → 6); `F2-A2 → F2-C1` (5 → 7); `(F2-B3, F2-C1) → F2-D1` (6, 7 → 8); Tests `F2-T1` (nach A2: 5 → 9), `F2-T2` (nach B3: 6 → 10), `F2-T3` (nach B1: 2 → 11) — je eigene Testdatei, parallel möglich, kein Merge-Gate; `F2-D1 → F2-V1` (8 → 12; die Implementierungs-Tasks sind transitiv enthalten).
- DAG Phase 4 (nach Merge von Phase 3): `F2-B4` (nach `F2-S1` und `F2-B3`: 1, 6 → 13); `F2-B5` (nach `F2-B2`: 4 → 14); `(F2-B3, F2-B4, F2-B5) → F2-B6` (6, 13, 14 → 15); `(F2-C1, F2-B5) → F2-C2` (7, 14 → 16); `(F2-B6, F2-C2, F2-D1) → F2-D2` (15, 16, 8 → 17); `F2-T4` (nach B5: 14 → 18), `F2-T5` (nach B6: 15 → 19); `F2-D2 → F2-V2` (17 → 20).
- Gemeinsame Dateien erzwingen Sequenz: `scripts/admin-server.py` (F2-B3 → F2-B4 → F2-B6), `scripts/lib/fleet_client.py` (F2-B1 → F2-B2 → F2-B5), `scripts/fleet-server.py` (F2-A1 → F2-A2), `docs/ui/fleet-ui.html` (F2-C1 → F2-C2), `docs/howto/fleet-server.md` und `docs/api/fleet-api-reference.md` (F2-D1 → F2-D2).
- V1/V2 konsumieren die Ergebnisse der Test-Tasks „soweit umgesetzt" (D8), ohne von ihnen abzuhängen.

| Nr | Label | Task | Agent | Depends on |
|---|---|---|---|---|
| 1 | F2-S1 | Blocker-Spike und F1-Symbolinventar | senior-developer | — |
| 2 | F2-B1 | Fleet-eigenes Busy-Gate `FLEET_WRITE_GATE` (modulweit) | developer | 1 |
| 3 | F2-A1 | Nonce-Store, Write-Token, `--write-token-file` | developer | 1 |
| 4 | F2-B2 | Write-Worker, Dedupe, Busy-Gate im Client | senior-developer | 1, 2 |
| 5 | F2-A2 | Write-Gate-Kette im Kommando-Endpunkt | developer | 3, 1 |
| 6 | F2-B3 | Handler `trigger-sync` und Injektion | developer | 2, 4 |
| 7 | F2-C1 | Dashboard: Sync-Button und Bestätigungsdialog | developer | 5 |
| 8 | F2-D1 | Doku Schreibpfad Phase 3 | documenter | 6, 7 |
| 9 | F2-T1 | Tests Server-Write-Gates | tester | 5 |
| 10 | F2-T2 | Tests Client-Write-Worker und `trigger-sync` | tester | 6 |
| 11 | F2-T3 | Tests Fleet-eigenes Busy-Gate | tester | 2 |
| 12 | F2-V1 | Verifikation Phase 3 | tester | 8 |
| 13 | F2-B4 | Extraktion `_validate_project_document` | developer | 1, 6 |
| 14 | F2-B5 | `put-config`-Logik im Client | developer | 4 |
| 15 | F2-B6 | `roundtrip_guard` in `ConfigManager.write`, Handler `put-config` und Injektion | senior-developer | 6, 13, 14 |
| 16 | F2-C2 | Dashboard: Config-Edit-Dialog | developer | 7, 14, 15 |
| 17 | F2-D2 | Doku Schreibpfad Phase 4 | documenter | 8, 15, 16 |
| 18 | F2-T4 | Tests `put-config`-Logik | tester | 14 |
| 19 | F2-T5 | Tests `put-config`-Handler und Validierung | tester | 15 |
| 20 | F2-V2 | Verifikation Phase 4 | tester | 17 |

## Plan-Annahmen (Assumptions)

- **PA-1:** `--write-token-file` verweist auf eine vom Betreiber angelegte Datei (Modus 0600, z. B. `umask 077; openssl rand -base64 32 > write.token`); fehlt sie, endet `serve` mit Exit 1, hat sie Group-/Other-Bits, mit Exit 2. Die Spec lässt die Erzeugung offen; keine Auto-Erzeugung (anders als `admin.token`). Gilt nicht, falls der Nutzer Auto-Erzeugung wünscht — dann ändert sich nur F2-A1 Schritt 4.
- **PA-2:** Ein `trigger-sync` mit Exit-Code ≠ 0 wird als Terminal-Ack `error` mit `error.code: internal_error` und gefülltem `result` (`exit_code`, `tail`) gemeldet, weil die Spec keinen eigenen Code für „sync.py fehlgeschlagen" vorsieht.
- **PA-3:** Reihenfolge Poll-Thread → Worker: Das Kommando wird per `put_nowait` an den Worker übergeben und das Ack `accepted` sofort gesendet; der Worker wartet vor dem Handler-Aufruf auf ein `threading.Event` (`accepted_sent`, Timeout **25 s**), damit das Terminal-Ack nie vor dem `accepted`-Ack beim Server ankommt (sonst wäre der Übergang `ok` → `accepted` serverseitig ein `schema_invalid`). Zeitbudget: 25 s Wartefenster + 300 s `sync.py`-Timeout = 325 s < 330 s (Margin 5 s). Der `ack`-POST mit 35 s Client-Timeout kann die 5 s Reserve überschreiten; dann meldet der Server `error/command_timeout`, ohne Doppel-Schreibvorgang. Wird das Wartefenster oder das Sync-Timeout geändert, muss die Summe unter 330 s bleiben.
- **PA-4:** Die Write-Handler werden immer injiziert (auch bei `allow-remote-write: false` zum Startzeitpunkt), weil das Gate zur Laufzeit frisch geprüft wird; der Thread `fleet-write` existiert damit bei jedem aktiven Client. AC-1 (kein Thread bei deaktiviertem Fleet) bleibt unberührt.
- **PA-5:** Zwischen Hash-Prüfung (`base_sha256`) und `ConfigManager.write` gibt es kein Dateisperr-Fenster (kein Lock in `ConfigManager`). Das Restfenster ist klein, durch Backup abgedeckt und wird in der Howto als Hinweis dokumentiert (Spec-Design: optimistische Prüfung, kein Locking).
- **PA-6:** Der Server prüft vor dem Enqueue nur Typ und `args`-Objektform; die inhaltliche Arg-Prüfung ist instanzseitig autoritativ (IC-15 Schritte 2-3 im Poll-Thread).
- **PA-7 (entschieden):** Spec IC-7 legt für Terminalzustände HTTP 200 fest, und `rejected` ist ein Terminalzustand. Der Server antwortet daher bei instanzseitig `rejected`-Kommandos mit **HTTP 200** und dem Kommandozustand im Body; es gibt keine Abhängigkeit vom F1-Mapping oder vom Spike.
- **PA-8 (akzeptiertes Risiko, R-16, D11, User 2026-10-28):** Ein Admin-UI-Sync und ein Fleet-`trigger-sync` (oder ein CLI-Sync) können sich überlappen: konkurrierende Schreibzugriffe auf generierte Dateien, `sync-status.json` stammt vom zuletzt endenden Lauf. Keine Code-Mitigation; `FLEET_WRITE_GATE` serialisiert nur fleet-ausgelöste Writes. Dokumentiert in Howto (Task 8) und API-Referenz; Hinweis: Remote-Sync nicht auslösen, während lokal ein Sync läuft.
- **Re-Planning:** Nach jedem Meilenstein (F2-S1-Verdikt, Merge Phase 3, Merge Phase 4) prüfen: Gelten die Annahmen noch (insbesondere PA-3 und die F1-Symbolnamen)? Sind Tasks richtig geordnet? Plan aktualisieren, nicht als eingefroren behandeln.

## File Structure

**Create:**
- Create: `docs/spikes/2026-10-23-fleet-f2-spike.md` — Verdikt zur request-losen Validierung, F1-Symbolinventar (Task F2-S1)
- Create: `tests/test_fleet_write_server.py` — Tests Server-Write-Gates (Task F2-T1)
- Create: `tests/test_fleet_write.py` — Tests Client-Write-Worker, `trigger-sync` (F2-T2)
- Create: `tests/test_fleet_put_config_handler.py` — Tests `put-config`-Handler und Validierungsparität (F2-T5)
- Create: `tests/test_fleet_write_gate.py` — Tests Fleet-eigenes Busy-Gate `FLEET_WRITE_GATE` (Task F2-T3)
- Create: `tests/test_fleet_put_config.py` — Tests `put-config`-Logik (Task F2-T4)

**Modify (Code):**
- Modify: `scripts/admin-server.py` — Write-Handler `trigger-sync` + Injektion in `_maybe_create_fleet_client` (F2-B3); `AdminRequestHandler._validate_project_document` (F2-B4); `ConfigManager.write(..., roundtrip_guard)` + Handler `put-config` (F2-B6)
- Modify: `scripts/fleet-server.py` — `NonceStore`, Write-Token-Laden, Flag `--write-token-file` (F2-A1); Write-Gate-Kette im Kommando-Endpunkt (F2-A2)
- Modify: `scripts/lib/fleet_client.py` — modulweites `FLEET_WRITE_GATE` (F2-B1); Write-Worker, Dedupe, `validate_write_args`, Busy-Gate (F2-B2); `REMOTE_WRITE_ALLOWLIST`, `REMOTE_NEVER_WRITABLE`, `apply_config_ops`, `validate_put_config_args` (F2-B5)
- Modify: `docs/ui/fleet-ui.html` — Sync-Button, Bestätigungsdialog, Write-Token-Feld (F2-C1); Config-Edit-Dialog (F2-C2)

**Modify (Doku):**
- Modify: `docs/howto/fleet-server.md` — Abschnitt Schreibpfad (F2-D1, F2-D2)
- Modify: `docs/api/fleet-api-reference.md` — Write-Teil: Gates, Nonce, Fehlercodes, Ack-Codes (F2-D1, F2-D2)

Nicht geändert: `config/project-config.schema.json` und `tests/scenarios/*` (der `fleet`-Block inkl. `allow-remote-write` ist seit F1-A deklariert; F2 führt keine neue Config-Option ein), `main()`, `_admin_start_detached`, `AuthService`, Routing-Tabellen des Admin-Servers sowie `SyncExecutor`, `_run`, `_record_run` und alle Admin-Routen (D11).

## Phase 3 — Remote-Sync-Trigger

### Task 1: F2-S1 — Blocker-Spike, request-lose Validierung und F1-Symbolinventar
**Agent:** senior-developer
**Depends on:** —
**Files:**
- Create: `docs/spikes/2026-10-23-fleet-f2-spike.md`
- Create: `.tmp/f2-spike/requestless_validate.py` (Wegwerf-Skript, gitignored, nicht committen)
**Interfaces:** Produces: Verdikt-Zeile `Verdikt: REQUESTLESS_OK | REQUEST_STATE_ACCESS` (Gate für F2-B4/B6, also Phase 4; bei `REQUEST_STATE_ACCESS` ist das ein **Blocker des Plans**, kein stilles Abweichen — an den Orchestrator eskalieren, Tasks 13 bis 15 (F2-B4 bis F2-B6) nicht starten); Tabelle „F1-Symbole" (Datei, Symbol, Zeile) für die in F2-A2, F2-B2, F2-C1 genutzten Einhängepunkte; Consumes: `scripts/admin-server.py` (`AdminRequestHandler._service_context`, `_agent_meta_root`, `_ensure_lib_on_path`, `_load_providers_registry`, `_assert_project_update_writable`, `_assert_project_sections_writable`, `_validate_project_provider_options`, `_guard_context_profile_write`), gemergte F1-Dateien.
**Vorab-Befund der Planung (statische Lektüre, im Spike dynamisch zu bestätigen):** `_service_context()` baut `ServiceContext(self.__class__, self)`; `ServiceContext.root`/`config_manager`/`agent_meta_root()` lesen ausschließlich Klassen-Attribute; `_ensure_lib_on_path`, `_agent_meta_root`, `_load_providers_registry`, `_guard_context_profile_write` (über `_ensure_scripts_on_path(self.__class__.root)`) greifen weder auf `self.headers` noch `self.rfile` noch `self.path` zu.
- [ ] Step 1: Entry prüfen: `ls scripts/fleet-server.py scripts/lib/fleet_client.py scripts/lib/fleet_protocol.py scripts/lib/redaction.py docs/ui/fleet-ui.html` → alle fünf Pfade ausgegeben, kein „No such file". Fehlt einer: F1 nicht gemergt, STOP und melden.
- [ ] Step 2: Skript `.tmp/f2-spike/requestless_validate.py` schreiben (Ausführung aus dem Repo-Root):
  ```python
  import importlib.util, sys
  from pathlib import Path

  root = Path.cwd()
  sys.path.insert(0, str(root / "scripts"))
  spec = importlib.util.spec_from_file_location("admin_server", root / "scripts" / "admin-server.py")
  mod = importlib.util.module_from_spec(spec)
  sys.modules["admin_server"] = mod
  spec.loader.exec_module(mod)
  H = mod.AdminRequestHandler
  H.root = root
  H.config_manager = mod.ConfigManager(root, mod.detect_mode(root))
  h = H.__new__(H)
  assert not hasattr(h, "headers") and not hasattr(h, "rfile")
  existing = H.config_manager.read("project")
  h._assert_project_update_writable(dict(existing), existing)
  print("OK assert_project_update_writable")
  try:
      h._validate_project_provider_options({"NoSuchProvider": {"surface-version": "v1"}})
  except ValueError as exc:
      print("OK provider_options (ValueError is request-less):", exc)
  else:
      print("OK provider_options")
  for section in ("context-profile", "provider-overrides"):
      h._guard_context_profile_write(section, existing.get(section))
  print("OK guard_context_profile_write (existing values)")
  try:
      h._guard_context_profile_write("context-profile", "huge")
  except ValueError as exc:
      assert "context-profile.invalid" in str(exc)
      print("OK invalid context-profile rejected")
  else:
      raise SystemExit("FAIL: no ValueError for context-profile=huge")
  try:
      h._assert_project_sections_writable({"max-parallel-agents"})
  except ValueError as exc:
      assert "section not allowed: max-parallel-agents" in str(exc)
      print("OK deletion check rejects max-parallel-agents")
  else:
      raise SystemExit("FAIL: max-parallel-agents unexpectedly writable")
  print("agent_meta_root:", h._agent_meta_root())
  print("VERDICT REQUESTLESS_OK")
  ```
- [ ] Step 3: Ausführen: `python3 .tmp/f2-spike/requestless_validate.py` → Ausgabe endet mit `VERDICT REQUESTLESS_OK`, Exit 0. Ein `AttributeError`/`KeyError` auf `headers`/`rfile`/`path`/`client_address` = `REQUEST_STATE_ACCESS` (Traceback in das Dokument kopieren).
- [ ] Step 4: F1-Symbolinventar per Grep erstellen und als Tabelle ins Dokument eintragen (jeweils Datei:Symbol:Zeile; nicht auffindbar = „fehlt" und an den Orchestrator melden):
  - `scripts/fleet-server.py`: Grep `WRITE_COMMANDS|unknown_command` (Stelle, an der F1 Write-Typen ablehnt = Einhängepunkt F2-A2); Handler von `POST /api/instances/<id>/commands`; Warte-Logik (20 s) und Statusabbildung der Kommandozustände; Audit-Aufruf-Muster (`AuditLog.append(...)`); Instanzzugriff (Registry-Eintrag, `status`-Feld, Liveness); Nonce-/Header-Zugriff existiert noch nicht.
  - `scripts/lib/fleet_client.py`: Grep `def handle_command|def _post_ack|def _poll|def stop|def start|sha256|allow_remote_write`; Poll-Schleife und Stelle, die das von `handle_command` gelieferte Ack sendet (Einhängepunkt F2-B2 `_ack_posted`); Funktion, die `.meta-config/project.yaml` frisch lädt; die `get-config`-Berechnung von `sha256`.
  - `scripts/lib/fleet_protocol.py`: Signatur und Verhalten von `resolve_secret` bei leerem `env_var`-Namen; ob `AuditLog.append` Ereignisnamen validiert (Liste aus IC-9 muss `write_gate_denied`, `confirm_issued`, `confirm_used`, `command_rejected`, `command_ack` enthalten).
  - `docs/ui/fleet-ui.html`: Grep `function |createElement|fetch(|sessionStorage|displaySafe` (Einhängepunkte F2-C1/F2-C2).
- [ ] Step 5: Dokument `docs/spikes/2026-10-23-fleet-f2-spike.md` schreiben (Deutsch): Abschnitte `## Experiment`, `## Ergebnis` mit genau einer Zeile `Verdikt: REQUESTLESS_OK` (oder `Verdikt: REQUEST_STATE_ACCESS`), `## F1-Symbole` (Tabelle). Prüfen: Grep nach `^Verdikt: (REQUESTLESS_OK|REQUEST_STATE_ACCESS)$` in der Datei liefert genau 1 Treffer.
- [ ] Step 6: commit `docs: record fleet f2 request-less validation spike`

### Task 2: F2-B1 — Fleet-eigenes Busy-Gate `FLEET_WRITE_GATE` (D11, AC-39, AC-52)
**Agent:** developer
**Depends on:** 1
**parallel_group:** g1
**Files:**
- Modify: `scripts/lib/fleet_client.py`
**Interfaces:** Produces: modulweites `FLEET_WRITE_GATE: threading.Semaphore = threading.Semaphore(1)` in `scripts/lib/fleet_client.py` (eigenes Fleet-Busy-Gate, serialisiert nur fleet-ausgelöste Writes; Task 4 nutzt es im Poll-Pfad per `acquire(blocking=False)` und im Worker-`finally` per `release()`); **keine** Änderung an `SyncExecutor`, `_run`, `_record_run` oder einer Admin-Route (D11, AC-54 gestrichen); Consumes: `threading` (Import in `fleet_client.py`, soweit nicht vorhanden).
- [ ] Step 1: Unberührtheits-Baseline: Grep `_RUN_GATE|FLEET_WRITE_GATE|sync already running` in `scripts/` → 0 Treffer vor der Änderung; `git diff --stat` zeigt am Ende dieses Tasks ausschließlich `scripts/lib/fleet_client.py`.
- [ ] Step 2: Test schreiben (fail): Ad-hoc `.tmp/f2-b1-check.py` (nicht committen; der dauerhafte Test ist F2-T3; Ausführung aus dem Repo-Root, `sys.path.insert(0, "scripts")`): `from lib import fleet_client`; `fleet_client.FLEET_WRITE_GATE` → vor der Änderung `AttributeError`.
- [ ] Step 3: Implementieren: direkt unter den Imports/Konstanten von `scripts/lib/fleet_client.py` `FLEET_WRITE_GATE = threading.Semaphore(1)`; Kommentar (Englisch): module-wide on purpose, one fleet-triggered write at a time across all `FleetClient` instances in this process; admin-UI syncs do not take this gate (accepted risk R-16).
- [ ] Step 4: Test (pass): Ad-hoc-Prüfung: erstes `acquire(blocking=False)` → `True`, zweites → `False`, nach `release()` wieder `True` (danach `release()`); Grep `FLEET_WRITE_GATE` in `scripts/lib/fleet_client.py` → genau 1 Definition auf Modulebene (Spalte 0); Grep `_RUN_GATE|sync already running` in `scripts/admin-server.py` → 0 Treffer.
- [ ] Step 5: commit `feat(fleet): add module-wide fleet write busy gate`

### Task 3: F2-A1 — Nonce-Store, Write-Token und Flag `--write-token-file` (Server)
**Agent:** developer
**Depends on:** 1
**parallel_group:** g1
**Files:**
- Modify: `scripts/fleet-server.py`
**Interfaces:** Produces: `class NonceStore` mit `__init__(self, ttl: int = 60, max_entries: int = 1024, clock: Callable[[], float] = time.monotonic) -> None`, `issue(self, instance_id: str, command_type: str, args: Mapping[str, Any]) -> str` (liefert `secrets.token_urlsafe(16)`), `consume(self, nonce: str, instance_id: str, command_type: str, args: Mapping[str, Any]) -> bool`; Hilfsfunktion `canonical_args_digest(args: Mapping[str, Any]) -> str` (`hashlib.sha256(json.dumps(args, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()`); Funktion `write_token_matches(provided: str | None, expected: str | None) -> bool` (`hmac.compare_digest` auf UTF-8-Bytes; leer/`None` → `False`); CLI-Flag `serve --write-token-file PATH` (IC-6) und Server-Attribut `write_token: str | None` (beim Start gelesen); Consumes: `fleet_protocol.resolve_secret(env_var: str, token_file: Path | None) -> str | None`, `fleet_protocol.FleetProtocolError`.
**Semantik NonceStore:** Bindung an `(instance_id, command_type, canonical_args_digest(args))`; einmalig (Eintrag wird bei jedem `consume`-Treffer entfernt, auch bei Bindungs-Mismatch = Nonce verbrannt); Gültigkeit 60 s ab `issue`; abgelaufene Einträge werden bei `issue`/`consume` entfernt; über `max_entries` wird der älteste verworfen; `threading.Lock`; Nonce-Vergleich per `hmac.compare_digest` über den Schlüssel-Lookup (Schlüssel = Nonce-String, Treffer via Dict-Zugriff, danach `compare_digest` auf Bindungs-Digest).
- [ ] Step 1: Test schreiben (fail): Ad-hoc `.tmp/f2-a1-check.py` mit Uhr-Stub: (a) `issue` → `consume` mit gleicher Bindung `True`, zweites `consume` `False`; (b) `consume` mit geänderten Args `False`, danach auch mit korrekten Args `False` (verbrannt); (c) Uhr +61 s → `False`; (d) fremde `instance_id` → `False`. Vor Implementierung: `ImportError`/`AttributeError` (Klasse fehlt).
- [ ] Step 2: Implementieren: `NonceStore`, `canonical_args_digest`, `write_token_matches` am Modulende vor `main`-Einstieg (Fundstelle laut F2-S1-Inventar). Kein `==` auf Token-/Nonce-Variablen (AC-11-Grep bleibt sauber).
- [ ] Step 3: Argparse: im Subparser `serve` Option `--write-token-file` (`type=Path`, Default `None`, Help-Text Englisch „enable write re-auth: write commands require a matching X-Fleet-Write-Token header"). Beim Start (vor Socket-Bindung, nach TLS-Refusal-Prüfung): `if args.write_token_file is not None:` Datei muss existieren (sonst Meldung `write token file not found: PATH` auf stderr, Exit 1), Token lesen per `resolve_secret("", args.write_token_file)` (fstat-Modusprüfung; `FleetProtocolError("insecure_token_file")` → Meldung, Exit 2); leeres Token → Exit 1. Falls `resolve_secret` einen leeren `env_var`-Namen nicht akzeptiert (Inventar F2-S1 Step 4), stattdessen dieselbe fd-basierte Leselogik lokal kapseln (`os.open`, `os.fstat`, Modusbits prüfen, `os.read`) — kein stat-then-open (AC-49).
- [ ] Step 4: Test (pass): Ad-hoc-Prüfung grün (Step 1); `python3 scripts/fleet-server.py serve --state-dir .tmp/f2-a1 --write-token-file .tmp/f2-a1/missing.token` → Exit 1 und stderr enthält `write token file not found`; Datei mit `chmod 644` → Exit 2 und stderr enthält `insecure_token_file`. Grep `write_token` in `scripts/fleet-server.py`: kein `==`/`!=` auf Token-Variablen.
- [ ] Step 5: commit `feat(fleet): add nonce store and write-token flag to server`

### Task 4: F2-B2 — Write-Worker, Dedupe und Busy-Gate im Client (AC-37, AC-39, AC-46, AC-52)
**Agent:** senior-developer
**Depends on:** 1, 2
**Files:**
- Modify: `scripts/lib/fleet_client.py`
**Interfaces:** Produces: `WriteHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]` (bereits aus F1; F2 definiert den Rückgabevertrag: Handler erhält `args` und liefert `{"status": "ok" | "error", "result": dict | None, "error": {"code": str, "message": str} | None}`; ungültige Rückgabeform → Terminal-Ack `error/internal_error`); `validate_write_args(command_type: str, args: Any) -> tuple[str, str] | None` (reine Funktion, `None` = gültig, sonst `(code, message)`; Phase 3: `trigger-sync` verlangt ein Objekt mit genau dem Key `mode` ∈ {`"validate"`, `"run"`}, sonst `("invalid_args", …)`; jeder andere Typ `("unknown_command", …)`, `put-config` wird in F2-B5 ergänzt); `FleetClient._load_write_allowed(self) -> bool` (lädt `.meta-config/project.yaml` frisch mit dem Lader laut F2-S1-Inventar, liefert `fleet.enabled is True and fleet.allow-remote-write is True`, jede Exception → `False`, fail closed); `FleetClient._register_command_id(self, command_id: str) -> bool` (`True` wenn neu; LRU `collections.OrderedDict`, 256 Einträge, `threading.Lock`, nur im Speicher); `FleetClient._handle_write_command(self, command: Mapping[str, Any]) -> dict` (liefert den sofortigen Ack-Body `rejected` oder `accepted`; `handle_command` delegiert für `command["type"] in WRITE_COMMANDS` hierhin); `FleetClient._ack_posted(self, ack: Mapping[str, Any]) -> None` (vom Poll-Thread nach dem Senden jedes Acks aufgerufen, setzt bei `status == "accepted"` das Event `accepted_sent` des zugehörigen Jobs); `class _WriteJob` (dataclass: `command_id: str`, `type: str`, `args: Mapping[str, Any]`, `accepted_sent: threading.Event`); Worker-Thread `fleet-write` (nur wenn `write_handlers` nicht leer) mit dem modulweiten Gate `FLEET_WRITE_GATE` (aus F2-B1, keine Instanzvariable) und `self._write_queue = queue.Queue(maxsize=1)`; Consumes: `FLEET_WRITE_GATE` (F2-B1), `fleet_protocol.WRITE_COMMANDS`, `AuditLog.append`, `redaction.redact_text`, F1-`handle_command`, F1-Poll-Schleife und Ack-Versand (Fundstellen laut F2-S1-Inventar), `self._write_handlers`.
**Reihenfolge in `_handle_write_command` (bindend, Review-Minor 2, Spec IC-4: `remote_write`-Prüfung, Dedupe, Arg-Prüfungen **vor** dem Acquire; jede Ablehnung vor `accepted` ist `status: "rejected"` und erzeugt Audit `command_rejected`):**
1. `command["type"]` nicht in `self._write_handlers` → `rejected/unknown_command`.
2. `_load_write_allowed()` ist `False` → `rejected/remote_write_disabled` und zusätzlich Audit `write_gate_denied` (outcome `denied`); **kein** Gate-Zugriff, **kein** Subprozess.
3. `_register_command_id` ist `False` → `rejected/duplicate_command`.
4. `validate_write_args(...)` liefert Fehler → `rejected/<code>`.
5. `if not FLEET_WRITE_GATE.acquire(blocking=False)` → `rejected/busy` (einzige Busy-Quelle, D11).
6. `try: self._write_queue.put_nowait(job)` / `except BaseException: FLEET_WRITE_GATE.release(); raise` — Rückgabe `accepted` (schlägt zwischen Acquire und `accepted` etwas fehl, wird das Gate sofort freigegeben). Das Gate wird **nur** vom Worker im `finally` (oder im Fehlerpfad dieser Zeile) freigegeben. Die Tests teilen sich das modulweite Gate: nach jedem Fall muss `FLEET_WRITE_GATE.acquire(blocking=False)` wieder `True` liefern (danach sofort `release()`).

**Worker-Ablauf:** `job = self._write_queue.get(timeout=1)` in Schleife bis `stop()`; `try:` `job.accepted_sent.wait(timeout=25)` (PA-3); Handler aufrufen; Ergebnis normalisieren; Terminal-Ack senden (`ok|error`, bei Exception im Handler `error/internal_error` mit gekürzter, durch `redact_text` gelaufener Meldung); Audit `command_ack`; `finally: FLEET_WRITE_GATE.release()` — auch bei Fehler im Ack-Versand.
**expires_at:** wird nirgends ausgewertet (Grep `expires_at` in `fleet_client.py` → kein Treffer in Vergleichs-/Zeitlogik).
- [ ] Step 1: Test schreiben (fail): Ad-hoc `.tmp/f2-b2-check.py` mit gestubbtem `_post_ack` und temporärem Projekt-Root (`.meta-config/project.yaml` mit `fleet: {enabled: true, allow-remote-write: true, …}`) und einem Blocker-Handler (wartet auf `Event`): (a) erstes `trigger-sync` → `accepted`; (b) zweites Write-Kommando → `rejected/busy`; (c) `get-logs` währenddessen normal; (d) nach Handler-Ende und Terminal-Ack → nächstes Write `accepted`. Vor der Änderung: `rejected/unknown_command`.
- [ ] Step 2: `validate_write_args`, `_WriteJob`, `_load_write_allowed`, `_register_command_id` implementieren; `import collections, queue, threading` ergänzen, soweit nicht vorhanden.
- [ ] Step 3: `_handle_write_command` und `handle_command`-Delegation implementieren (Reihenfolge 1-6 oben); `start()` startet `fleet-write` nur bei nicht leerem `write_handlers` (idempotent); `stop()` setzt ein Stop-Flag, legt kein Kommando mehr an und `join(timeout=1)`.
- [ ] Step 4: Poll-Thread-Einhängung: an der F1-Stelle, die das von `handle_command` gelieferte Ack sendet, unmittelbar nach dem Versand (auch bei Versandfehler im `finally`) `self._ack_posted(ack)` aufrufen. Ohne diesen Aufruf wartet der Worker 25 s (Fallback, PA-3) — im Code kommentieren (Englisch).
- [ ] Step 5: Test (pass): Ad-hoc-Prüfung grün. Zusätzlich im selben Skript: (e) `remote_write_disabled`: Config mit `allow-remote-write: false` → `rejected/remote_write_disabled`, Audit-Zeile `write_gate_denied` in `.meta-viz/fleet-audit.log`, Handler nie aufgerufen; (f) **Gate-Leckfreiheit:** `rejected/invalid_args` und `rejected/duplicate_command` gefolgt von einem gültigen Write → `accepted` (nicht `busy`); der `path_not_writable`-Fall existiert erst ab F2-B5 und wird in Task 14 (F2-B5) Step 3 sowie in Task 19 (F2-T5, `test_ac41_path_not_writable_before_accepted`) geprüft; (g) Handler wirft Exception → Terminal-Ack `error/internal_error`, nächstes Write wieder `accepted`; (h) Terminal-Ack wird nie vor dem `accepted`-Ack gesendet (Reihenfolge der `_post_ack`-Aufrufe). Grep `acquire(blocking=False)` in `fleet_client.py` → genau 1 Treffer im Poll-Pfad (`_handle_write_command`); Grep `release()` → Treffer im Worker-`finally` und im Einreihungs-Fehlerpfad.
- [ ] Step 6: commit `feat(fleet): add write worker with dedupe and busy gate`

### Task 5: F2-A2 — Write-Gate-Kette im Kommando-Endpunkt (Server; AC-38, AC-39, AC-40)
**Agent:** developer
**Depends on:** 3, 1
**Files:**
- Modify: `scripts/fleet-server.py`
**Interfaces:** Produces: im Handler von `POST /api/instances/<id>/commands` (Fundstelle laut F2-S1-Inventar) die Funktion `check_write_gates(server, instance, command_type: str, args: Mapping[str, Any], headers: Mapping[str, str], confirm_nonce: str | None) -> None` (wirft die serverseitigen Fehler als vorhandene Fehlerform); Gate-Reihenfolge, Typ-Prüfung und Antwort-Mapping siehe unten; Consumes: `NonceStore` (F2-A1), `write_token_matches`, `WRITE_COMMANDS`, F1-Audit-Helfer, F1-Warte-/Statuslogik.
**Gate-Reihenfolge (bindend, IC-14, ergänzt um den F1-Offline-Check):**
1. Admin-Token (bereits durch F1 vor dem Handler geprüft).
2. Write-Token: nur wenn `server.write_token` gesetzt: Header `X-Fleet-Write-Token` per `write_token_matches` → sonst 401 `write_reauth_required` (+ `WWW-Authenticate: Bearer`), Audit `write_gate_denied` (outcome `denied`, actor `dashboard`, detail `write_reauth_required`).
3. `instance.status.allow_remote_write is True` → sonst 403 `write_disabled`, Audit `write_gate_denied`.
4. F1-Offline-Check (`offline`/`never` → 409 `instance_offline`), unverändert wiederverwendet — vor dem Nonce, damit eine Nonce nicht an einer Offline-Instanz verbraucht wird.
5. Nonce: `confirm_nonce` fehlt oder `NonceStore.consume(...)` ist `False` → 428 `confirmation_required` mit Body `{"error": {"code": "confirmation_required", "message": "..."}, "confirm_nonce": <neu>, "expires_in": 60}`, Audit `confirm_issued`; bei Treffer Audit `confirm_used`.
6. Danach der unveränderte F1-Enqueue-Pfad (`queue_full` 503, Audit `command_enqueued`).

**Typ-Prüfung:** `command_type in READ_COMMANDS ∪ WRITE_COMMANDS`, sonst `unknown_command`; `args` muss ein Objekt sein (`schema_invalid`). Read-Kommandos durchlaufen die Gate-Kette **nicht** (AC-40: Read unberührt).
**Antwort-Mapping für Write (PA-7, entschieden):** Warten bis Zustand ∈ {`accepted`, `ok`, `error`, `rejected`} (max. 20 s, F1-Wartelogik): `accepted` → HTTP 202 mit Kommandozustand; `ok|error|rejected` → HTTP 200 (IC-7: Terminalzustände 200, `rejected` ist terminal) mit Kommandozustand im Body; Timeout → 504 `command_timeout`.
- [ ] Step 1: Test schreiben (fail): Ad-hoc `.tmp/f2-a2-check.py` (Subprozess `serve --host 127.0.0.1 --port <frei> --state-dir .tmp/f2-a2 --write-token-file .tmp/f2-a2/write.token`; Instanz per `issue-token` vor dem Start, `POST /v1/enroll` + `POST /v1/heartbeat` mit `allow_remote_write: true`): `POST /api/instances/<id>/commands` mit `{"type": "trigger-sync", "args": {"mode": "validate"}}` liefert vor der Änderung 400 `unknown_command`.
- [ ] Step 2: `check_write_gates` implementieren und an der F1-Stelle einhängen, die `WRITE_COMMANDS` heute mit `unknown_command` ablehnt; `NonceStore` wird einmal pro Server angelegt (`server.nonces`).
- [ ] Step 3: Test (pass) manuell: (a) ohne `X-Fleet-Write-Token` → 401 `write_reauth_required`; (b) mit Token, ohne Nonce → 428 und Body enthält `confirm_nonce`; (c) mit Nonce → ohne laufende Instanz Poll nach 20 s 504 `command_timeout` bzw. 202 sobald ein Fake-Poller `accepted` ackt; Fake-Poller mit `rejected` → HTTP 200 mit Zustand `rejected`; (d) dieselbe Nonce erneut → 428; (e) Instanz mit `allow_remote_write: false` → 403 `write_disabled`; (f) `get-logs` ohne Write-Token → keine Gate-Antwort (normaler Read-Pfad).
- [ ] Step 4: Audit prüfen: `<state-dir>/audit.log` enthält je einen JSONL-Eintrag `write_gate_denied`, `confirm_issued`, `confirm_used`; kein Eintrag enthält das Token oder die Nonce im Klartext (Grep auf die verwendeten Werte → 0 Treffer).
- [ ] Step 5: commit `feat(fleet): enforce write gates in server command endpoint`

### Task 6: F2-B3 — Handler `trigger-sync` und Injektion (AC-37, AC-39)
**Agent:** developer
**Depends on:** 2, 4
**Files:**
- Modify: `scripts/admin-server.py`
**Interfaces:** Produces: Modulfunktion `_fleet_trigger_sync_handler(args: Mapping[str, Any]) -> dict` und `_fleet_write_handlers() -> dict[str, Callable[[Mapping[str, Any]], Mapping[str, Any]]]` (Phase 3: `{"trigger-sync": _fleet_trigger_sync_handler}`); `_maybe_create_fleet_client` (F1) übergibt `write_handlers=_fleet_write_handlers()` an `FleetClient` (PA-4); Consumes: `SyncExecutor` (bestehend, unverändert, D11), `FLEET_WRITE_GATE`-Semantik (F2-B1/F2-B2: das Gate hält bereits der Worker), `lib.redaction.redact_text` (Import innerhalb der Funktion nach `_ensure_scripts_on_path(AdminRequestHandler.root)`), `FleetClient`-Handler-Vertrag (F2-B2).
**Handler-Verhalten:** `executor = AdminRequestHandler.sync_executor`; `args["mode"] == "validate"` → `executor.dry_run()`, sonst `executor.run()`, jeweils unverändert aufgerufen (kein Busy-Marker, kein gemeinsames Lock, D11); ein parallel laufender Admin-UI-Sync wird weder erkannt noch abgewiesen (R-16, PA-8); der Handler enthält keinen `SyncExecutor`-Busy-Zweig, `error/busy` kommt nur vom Fleet-Gate; `tail = [redact_text(line)[:2000] for line in output.splitlines()[-50:]]`, `exit_code = result["returncode"]`; `returncode == 0` → `{"status": "ok", "result": {"exit_code": 0, "tail": tail}, "error": None}`, sonst `{"status": "error", "result": {"exit_code": rc, "tail": tail}, "error": {"code": "internal_error", "message": "sync.py exited with code N"}}` (PA-2; `returncode: -1` ohne `busy` = Timeout/Exception, ebenfalls normales `error`).
- [ ] Step 1: Test schreiben (fail): Ad-hoc `.tmp/f2-b3-check.py` mit `AdminRequestHandler.sync_executor` = Executor mit gepatchtem `subprocess.run` (Ausgabe 60 Zeilen, Returncode 0): `_fleet_trigger_sync_handler({"mode": "validate"})` → `AttributeError`/`NameError` (Funktion fehlt).
- [ ] Step 2: Implementieren: beide Funktionen direkt neben `_maybe_create_fleet_client` (Fundstelle laut F2-S1-Inventar); Aufruf in `_maybe_create_fleet_client` ergänzen. Die erste Anweisung `os.environ.pop("AGENT_META_FLEET_TOKEN", None)` und alle F1-Pfade bleiben unverändert (AC-47).
- [ ] Step 3: Test (pass): Ad-hoc-Prüfung: Ergebnis `status == "ok"`, `len(tail) == 50`, Tail-Zeile mit `ghp_`+36 Zeichen ist maskiert; `executor.dry_run()` bzw. `run()` wird je Handler-Aufruf genau einmal aufgerufen, das Ergebnis enthält keinen `busy`-Key; `git diff scripts/admin-server.py` enthält keine Änderung an `SyncExecutor`/`_run`/`_record_run`; `python3 -m pytest tests/test_admin_server.py -q` weiterhin 0 failed.
- [ ] Step 4: commit `feat(admin): inject trigger-sync write handler into fleet client`

### Task 7: F2-C1 — Dashboard: Sync-Button, Bestätigungsdialog, Write-Token-Feld
**Agent:** developer
**Depends on:** 5
**Files:**
- Modify: `docs/ui/fleet-ui.html`
**Interfaces:** Produces: Funktionen im Single-File-Skript (Namen verbindlich) `postCommand(instanceId, type, args, nonce) -> Promise<{status, body}>` (Header `Authorization: Bearer …`, bei gesetztem Write-Token zusätzlich `X-Fleet-Write-Token`; Body `{type, args, confirm_nonce?}`), `showConfirmDialog(opts) -> Promise<boolean>` mit `opts = {instanceName, commandType, args, warning}`, `runWriteCommand(instance, type, args, warning)` (Ablauf: 1. POST ohne Nonce → 428 → Dialog → bei Bestätigung 2. POST mit `confirm_nonce` → 202 → `pollCommand(commandId)` alle 2 s gegen `GET /api/commands/<id>` bis Terminalzustand → Ergebnis per `textContent`), Eingabefeld „Write-Token (optional)" in `sessionStorage` (`fleetWriteToken`), nie in URL; Consumes: bestehende Hilfsfunktionen aus F1-G (`displaySafe`, Token-Zugriff, Instanzliste; Fundstellen laut F2-S1-Inventar), Server-Verhalten aus F2-A2.
**Sichtbarkeit:** Button „Sync auslösen" nur, wenn `instance.status && instance.status.allow_remote_write === true`; Args: Auswahl `validate`/`run` (Default `validate`); Dialog zeigt Instanzname (Registry-Name, mit `displaySafe`), Kommando, Args als `JSON.stringify(args, null, 2)` in einem `pre`-Element via `textContent`; Fehlermeldungen (401 `write_reauth_required`, 403 `write_disabled`, 409 `instance_offline`, 503 `queue_full`, 504 `command_timeout`) als sichtbarer Text.
- [ ] Step 1: Statische Prüfung vorab (fail erwartet nicht möglich): Grep `innerHTML|outerHTML|insertAdjacentHTML|eval\(` in `docs/ui/fleet-ui.html` → Baseline 0 Datenzuweisungen (AC-28).
- [ ] Step 2: Funktionen und Button implementieren; Dialog als `div`-Overlay per `document.createElement`; Bestätigen/Abbrechen-Buttons per `addEventListener`, keine Inline-Handler (CSP erlaubt `script-src 'unsafe-inline'`, aber keine externen Ressourcen).
- [ ] Step 3: Prüfen: Grep wie Step 1 → weiterhin 0 Treffer; Grep `fetch(` zeigt nur relative Pfade (`/api/…`), keine externen URLs.
- [ ] Step 4: Manuell (Loopback, `--state-dir .tmp/f2-c1`): Instanz mit `allow_remote_write: true` zeigt den Button, Instanz mit `false` nicht; Klick → Dialog mit Name, `trigger-sync`, Args; „Abbrechen" sendet keinen zweiten POST (Netzwerk-Log des Servers: nur 1 POST mit 428); „Bestätigen" sendet den zweiten POST mit `confirm_nonce`.
- [ ] Step 5: commit `feat(fleet-ui): add sync trigger confirmation dialog`

### Task 8: F2-D1 — Doku Schreibpfad Phase 3
**Agent:** documenter
**Depends on:** 6, 7
**Files:**
- Modify: `docs/howto/fleet-server.md`
- Modify: `docs/api/fleet-api-reference.md`
**Interfaces:** Produces: Howto-Abschnitt `## Schreibpfad (Phase 3: Remote-Sync)` (`fleet.allow-remote-write` mit Default `false` und Wirkung ≤ 1 Heartbeat-Intervall ohne Neustart; Bestätigungsdialog und Nonce, einmalig, 60 s; Write-Token mit `--write-token-file`, Erzeugung per `umask 077; openssl rand -base64 32 > write.token`, PA-1; Busy-Verhalten: ein Fleet-Write gleichzeitig (Fleet-eigenes Gate); Admin-UI-Sync, CLI-Sync und Fleet-Sync blockieren sich **nicht** gegenseitig und können sich überlappen (akzeptiertes Risiko R-16, PA-8; Hinweis „Remote-Sync nicht auslösen, während lokal ein Sync läuft"; bei Verdacht erneut `trigger-sync mode: validate`); Rollback `allow-remote-write: false`; Hinweis `trigger-sync mode: validate` als Kontrolle) und API-Referenz (Fehlercodes `write_reauth_required`, `write_disabled`, `confirmation_required` mit 428 und Nonce-Body, HTTP 202 für `accepted`, HTTP 200 für Terminalzustände inkl. `rejected`, Header `X-Fleet-Write-Token`, `trigger-sync`-Args/Ack-Result, instanzseitige Ack-Codes `remote_write_disabled`, `busy`, `duplicate_command`, `invalid_args`, keine Admin-UI-Nebenwirkung, `SyncExecutor` und Admin-Routen bleiben unverändert, D11); Consumes: Spec IC-7, IC-14, R-16; implementierte Task-Ergebnisse.
- [ ] Step 1: Bestehende Struktur der beiden Dateien lesen (F1-H) und Einhängepunkt für den Schreibpfad-Abschnitt festlegen.
- [ ] Step 2: Abschnitte schreiben (Deutsch; Befehle, Header- und Feldnamen Englisch). Alle Beispiele nutzen `--state-dir .tmp/fleet-demo` bzw. `~/.agent-meta-fleet`.
- [ ] Step 3: Prüfen: Grep `X-Fleet-Write-Token|confirmation_required|write_disabled|write_reauth_required|remote_write_disabled` in beiden Dateien → je mindestens 1 Treffer; kein Token-/Nonce-Beispielwert mit `amf_`-Präfix in der Doku (Secret-Scan-sauber).
- [ ] Step 4: commit `docs: document fleet remote sync write path`

### Task 9: F2-T1 — Tests: Server-Write-Gates (empfohlen (Security))
**Agent:** tester
**Depends on:** 5
**Files:**
- Create: `tests/test_fleet_write_server.py`
**Interfaces:** Produces: unittest-Klassen `TestServerWriteGates` und `TestNonceStore` (Testnamen enthalten die Task-/AC-Kennung für Traceability, z. B. `test_ac38_...`); Consumes: `scripts/fleet-server.py` (via `importlib` für `NonceStore`/`write_token_matches`; Subprozess `serve` auf `127.0.0.1` mit freiem Port und `--state-dir` in `tempfile.TemporaryDirectory()`), `issue-token`-CLI, F1-Enroll/Heartbeat-Endpunkte.
- [ ] Step 1: Fixture schreiben: freien Port via `socket.bind(("127.0.0.1", 0))`, `issue-token --name t1 --out <tmp>/t1.token`, `serve … --write-token-file <tmp>/write.token`, Warten bis `GET /` 200, Admin-Token aus `<state-dir>/admin.token`, `POST /v1/enroll` + `POST /v1/heartbeat` (Status mit `allow_remote_write` konfigurierbar). `tearDown` beendet den Prozess.
- [ ] Step 2: Tests (jeder zunächst gegen den Soll-Wert geschrieben): `test_ac38_missing_nonce_returns_428_with_nonce`; `test_ac38_nonce_single_use` (zweite Nutzung 428); `test_ac38_nonce_expires_after_60s` (über `NonceStore`-Uhr-Stub, keine echte Wartezeit); `test_ac38_nonce_bound_to_args` (andere Args → 428 und Nonce verbrannt); `test_ac40_write_token_required` (ohne Header 401 `write_reauth_required`, falscher Header 401, richtiger Header weiter); `test_ac40_read_command_not_gated` (`get-logs` ohne Write-Token kein 401 `write_reauth_required`); `test_write_disabled_instance_403`; `test_write_gate_order` (Write-Token vor `write_disabled` vor Nonce); `test_rejected_ack_maps_to_http_200` (PA-7); `test_audit_events_no_secrets` (Audit enthält `write_gate_denied`, `confirm_issued`, `confirm_used`, nie Token/Nonce); `test_admin_token_still_required` (Instanz-Token auf `/api/…/commands` → 401, Token-Trennung); `test_revoked_instance_command_rejected` (nach `revoke` und Neustart der Serverinstanz: Kommando an widerrufene Instanz scheitert mit `instance_offline`/`instance_revoked` laut F1-Verhalten).
- [ ] Step 3: Ausführen: `python3 -m pytest tests/test_fleet_write_server.py -q` → alle Tests `passed`, 0 failed. Schlägt einer fehl, ist das ein Fund für F2-A1/F2-A2 (Bericht an den Orchestrator, Test nicht abschwächen).
- [ ] Step 4: commit `test(fleet): cover server write gates and nonce store`

### Task 10: F2-T2 — Tests: Client-Write-Worker und `trigger-sync` (empfohlen (Security))
**Agent:** tester
**Depends on:** 6
**Files:**
- Create: `tests/test_fleet_write.py`
**Interfaces:** Produces: unittest-Klasse `TestWriteWorker` (Phase 3); Consumes: `lib.fleet_client.FleetClient`, `validate_write_args`; `admin-server.py` per `importlib` für `_fleet_trigger_sync_handler`; temporärer Projekt-Root mit `.meta-config/project.yaml` (PyYAML `safe_dump`); `_post_ack` per `unittest.mock.patch.object` gestubbt.
- [ ] Step 1: Helfer `_make_client(root, allow_write, handlers)` und `_command(command_id, type, args)` (`command_id` im Format `cmd_` + 16 Hex).
- [ ] Step 2: Tests: `test_ac37_remote_write_disabled_rejects_without_subprocess` (Config `allow-remote-write: false`, Handler-Mock nie aufgerufen, Audit-Datei enthält `write_gate_denied`); `test_ac37_server_precheck_bypassed` (Kommando wird direkt an `handle_command` gegeben, ohne Server — Instanz entscheidet autoritativ); `test_ac46_flag_flip_without_restart` (Config von `true` auf `false` umschreiben, nächstes Write `rejected/remote_write_disabled`; Gegenprobe `false` → `true`); `test_ac39_accepted_then_terminal_ack` (Reihenfolge der `_post_ack`-Aufrufe: erst `accepted`, dann `ok`; Ergebnis enthält `exit_code` und ≤ 50 Tail-Zeilen); `test_ac39_second_write_busy_while_running` (Blocker-Handler per `Event`); `test_ac52_read_answered_while_write_runs`; `test_ac52_gate_released_after_terminal_ack`; `test_ac52_gate_released_when_handler_raises` (Terminal-Ack `error/internal_error`, nächstes Write `accepted`); `test_ac52_duplicate_command_id_rejected` (zweite Auslieferung derselben `command_id` → `rejected/duplicate_command`, Handler einmal aufgerufen); `test_rejected_does_not_leak_gate` (`invalid_args` und `duplicate_command` gefolgt von einem gültigen Write → `accepted`, nie `busy`; Review-Minor 2; der `path_not_writable`-Fall wird in F2-T5 `test_ac41_path_not_writable_before_accepted` geprüft, weil `validate_put_config_args` erst ab F2-B5 existiert); `test_ac52_expires_at_ignored` (Kommando mit `expires_at` in der Vergangenheit wird trotzdem `accepted`); `test_ac52_no_expires_at_logic` (Quelltext von `fleet_client.py` enthält `expires_at` nur in Schema-/Kommentar-/Feldzugriffs-Kontext, nicht in einem Vergleich: Regex `expires_at\s*[<>]`/`datetime` im selben Ausdruck → keine Treffer); `test_ac39_acquire_nonblocking_release_in_finally` (Quelltext-Grep: `FLEET_WRITE_GATE.acquire(blocking=False)` genau einmal, `release()` im Worker); `test_ac39_acquire_after_dedupe_and_arg_checks` (IC-4-Reihenfolge: bei `duplicate_command`/`invalid_args` wird `FLEET_WRITE_GATE` nie erworben); `test_trigger_sync_handler_no_busy_branch` (Admin-Handler aus `admin-server.py`: `SyncExecutor` gepatcht, Aufruf genau einmal, kein `busy`-Key im Ergebnis; ein parallel laufender Executor-Lauf wird nicht abgewiesen, R-16); `test_trigger_sync_nonzero_exit_is_error_with_tail` (PA-2); `test_trigger_sync_tail_is_redacted`.
- [ ] Step 3: Ausführen: `python3 -m pytest tests/test_fleet_write.py -q` → alle Tests `passed`, 0 failed.
- [ ] Step 4: commit `test(fleet): cover write worker, dedupe and trigger-sync handler`

### Task 11: F2-T3 — Tests: Fleet-eigenes Busy-Gate (empfohlen (Security), AC-52)
**Agent:** tester
**Depends on:** 2
**Files:**
- Create: `tests/test_fleet_write_gate.py`
**Interfaces:** Produces: unittest-Klasse `TestFleetWriteGate` (Unit-Ebene, unabhängig von F2-T2); Consumes: `lib.fleet_client.FLEET_WRITE_GATE` (Import mit `sys.path`-Ergänzung `scripts/`), Quelltext von `scripts/lib/fleet_client.py` und `scripts/admin-server.py` (nur Lesen, für die Nicht-Änderungs-Prüfung).
- [ ] Step 1: Helfer: Gate-Zustand vor/nach jedem Test prüfen (`setUp`/`tearDown`: `acquire(blocking=False)` muss `True` liefern und wird sofort wieder freigegeben, sonst Test-Fehler „gate leaked").
- [ ] Step 2: Tests: `test_gate_is_module_level_semaphore_one` (`"FLEET_WRITE_GATE" in vars(fleet_client)`, Anfangswert 1: erstes `acquire(blocking=False)` `True`, zweites `False`, nach `release()` wieder `True`); `test_ac52_gate_not_instance_attribute` (Quelltext-Grep: `Semaphore(1)` kommt in `fleet_client.py` genau einmal vor, kein `self._write_gate`); `test_ac52_release_in_finally_even_on_exception` (simulierter Worker-Block `try: … raise RuntimeError … finally: release()` mit dem echten Gate-Objekt; nächstes `acquire(blocking=False)` `True`); `test_gate_shared_across_threads` (Thread A hält das Gate, Thread B erhält `False`, nach `release()` durch A erhält B `True`); `test_syncexecutor_untouched_by_fleet_gate` (Quelltext `scripts/admin-server.py`: `_RUN_GATE` und `sync already running` kommen nicht vor, `FLEET_WRITE_GATE` kommt nicht vor; D11, AC-54 gestrichen).
- [ ] Step 3: Ausführen: `python3 -m pytest tests/test_fleet_write_gate.py -q` → alle Tests `passed`, 0 failed; Regression: `python3 -m pytest tests/test_admin_server.py tests/test_admin_cleanup_endpoint.py -q` → 0 failed.
- [ ] Step 4: commit `test(fleet): cover module-wide fleet write busy gate`

### Task 12: F2-V1 — Verifikation Phase 3
**Agent:** tester
**Depends on:** 8
**Files:**
- Modify: `docs/howto/fleet-server.md`
**Interfaces:** Produces: dokumentierter manueller End-to-End-Lauf (Abschnitt `### Beispiel: Remote-Sync-Lauf` im Howto-Schreibpfad-Abschnitt) und Exit-Nachweis Phase 3; Consumes: alle Phase-3-Implementierungs-Tasks (Tasks 1 bis 8) sowie die Ergebnisse der Test-Tasks 9 bis 11 (F2-T1 bis F2-T3), soweit umgesetzt (D8, kein Merge-Gate).
- [ ] Step 1: Tests (soweit umgesetzt): `python3 -m pytest tests/test_fleet_write_server.py tests/test_fleet_write.py tests/test_fleet_write_gate.py tests/test_python_compat_consistency.py -q` → 0 failed. Nicht umgesetzte Test-Tasks (D8) im Bericht listen; die „empfohlen (Security)"-Tests T1/T2 besonders markieren.
- [ ] Step 2: Grep-Nachweise: `acquire(blocking=False)` in `scripts/lib/fleet_client.py` (Poll-Pfad) und `release()` im Worker-`finally`; kein `expires_at`-Vergleich in `fleet_client.py`; `FLEET_WRITE_GATE` genau einmal modulweit definiert; `_RUN_GATE` und `sync already running` in `scripts/admin-server.py` → 0 Treffer (D11); kein `==` auf Token-Variablen in `scripts/fleet-server.py` und `scripts/lib/fleet_protocol.py`; `innerHTML`-Datenzuweisung in `docs/ui/fleet-ui.html` → 0 Treffer.
- [ ] Step 3: Manueller Lauf (Loopback, nur `.tmp/`-State): `python3 scripts/fleet-server.py issue-token --name e2e --out .tmp/fleet-e2e/inst.token --state-dir .tmp/fleet-e2e`; `umask 077; openssl rand -base64 32 > .tmp/fleet-e2e/write.token`; `python3 scripts/fleet-server.py serve --state-dir .tmp/fleet-e2e --port 7430 --write-token-file .tmp/fleet-e2e/write.token`; in einem Wegwerf-Projekt (`.tmp/fleet-e2e-project`, `fleet`-Block mit `allow-remote-write: true`, `AGENT_META_FLEET_TOKEN` nicht gesetzt, `token-file` zeigt auf `.tmp/fleet-e2e/inst.token`) den Admin-Server starten; im Dashboard Instanz wählen, „Sync auslösen" (`validate`) → Dialog → Bestätigen → Ergebnis `exit_code: 0`. Beobachtungen (Zeitstempel, Audit-Zeilen beider Seiten) ins Howto übernehmen.
- [ ] Step 4: `python3 scripts/sync.py --validate` → Exit 0. `python3 scripts/sync.py --validate-spec-plan` → keine Findings der Severity ERROR für Spec und Plan, sofern die Spec freigegeben ist.
- [ ] Step 5: commit `docs: record fleet f2 phase 3 end-to-end run`

## Phase 4 — Remote-Config-Edit (nach Merge von Phase 3)

### Task 13: F2-B4 — Extraktion `AdminRequestHandler._validate_project_document` (AC-53)
**Agent:** developer
**Depends on:** 1, 6
**Files:**
- Modify: `scripts/admin-server.py`
**Interfaces:** Produces: `AdminRequestHandler._validate_project_document(self, body: Any, existing: dict) -> None` (wirft `ValueError`; Rumpf **genau** die heutige Sequenz aus dem `if key == "project":`-Zweig von `_route_put_config`, in dieser Reihenfolge: `self._assert_project_update_writable(body, existing)`; `if isinstance(body, dict):` `self._validate_project_provider_options(body.get("provider-options"))`, `self._guard_context_profile_write("context-profile", body.get("context-profile"))`, `self._guard_context_profile_write("provider-overrides", body.get("provider-overrides"))`; **kein** `_guard_model_block_write`, **keine** Lösch-Prüfung in dieser Methode); Consumes: Verdikt `REQUESTLESS_OK` aus F2-S1 (bei `REQUEST_STATE_ACCESS` darf dieser Task nicht starten); Datei-Reihenfolge nach Task 6 (F2-B3), da beide `scripts/admin-server.py` ändern.
- [ ] Step 1: Voraussetzung prüfen: Grep `^Verdikt: REQUESTLESS_OK$` in `docs/spikes/2026-10-23-fleet-f2-spike.md` → 1 Treffer, sonst STOP und an den Orchestrator melden.
- [ ] Step 2: Baseline (Charakterisierung): `python3 -m pytest tests/test_admin_server.py -q` und `python3 -m pytest tests -q -k "config and project"` → Passed-Anzahlen notieren.
- [ ] Step 3: Refactoring: Methode direkt hinter `_assert_project_update_writable` einfügen; in `_route_put_config` ersetzt der Aufruf `self._validate_project_document(body, existing)` die vier bisherigen Anweisungen an derselben Stelle (vor `config_manager.write`, nach `existing`-Normalisierung). Dokumentationsstring (Englisch) benennt, dass Admin-UI und Fleet `put-config` sie gemeinsam nutzen.
- [ ] Step 4: Test (pass): dieselben Kommandos wie Step 2 → identische Passed-Anzahlen, 0 failed. Grep `_guard_model_block_write` im Rumpf der neuen Methode → 0 Treffer; Grep `_validate_project_document` → genau 2 Treffer im Quelltext (Definition und Aufruf in `_route_put_config`; der Fleet-Handler kommt in F2-B6 hinzu).
- [ ] Step 5: commit `refactor(admin): extract project document validation method`

### Task 14: F2-B5 — `put-config`-Logik im Client (AC-41, AC-43)
**Agent:** developer
**Depends on:** 4
**Files:**
- Modify: `scripts/lib/fleet_client.py`
**Interfaces:** Produces: `REMOTE_WRITE_ALLOWLIST: tuple[str, ...] = ("dod-preset", "rules-preset", "conventions-preset", "tier-preset", "speech-mode", "max-parallel-agents", "ai-providers", "platforms", "roles", "model-overrides")` (O-F3-Default); `REMOTE_NEVER_WRITABLE: tuple[str, ...] = ("fleet", "admin-ui", "hooks", "repo_containment", "variables", "mcp-servers", "mcp-registry", "plugins", "environments", "allow-committed-secrets", "provider-isolation")` (unabhängig von der Allowlist, AC-41); `MAX_CONFIG_OPS: int = 20`; `validate_put_config_args(args: Any, allowlist: Sequence[str] = REMOTE_WRITE_ALLOWLIST) -> tuple[str, str] | None` (Poll-Thread-Prüfung, IC-15 Schritte 2-3 plus Formprüfung: `args` ist ein Objekt mit genau den Keys `key`, `base_sha256`, `ops`; `key == "project"`; `base_sha256` passt auf `^[0-9a-f]{64}$`; `ops` ist eine Liste mit 1 bis 20 Einträgen; jeder Eintrag ein Objekt mit `op` ∈ {`"set"`, `"delete"`}, `path` (String, Regex `^[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)*$`), `set` mit Key `value`, `delete` ohne `value` → sonst `("invalid_args", …)`; Pfadprüfung: Pfad (oder sein erstes Segment) in `REMOTE_NEVER_WRITABLE` oder außerhalb der Allowlist (gleich einem Eintrag oder `startswith(eintrag + ".")`) → `("path_not_writable", …)`; `redaction.contains_redaction_marker(op["value"])` → `("redacted_value", …)`; Reihenfolge Form → alle Pfade → alle Werte); `apply_config_ops(current: Mapping[str, Any], ops: Sequence[Mapping[str, Any]], allowlist: Sequence[str]) -> dict[str, Any]` (rein funktional, Eingabe unverändert per `copy.deepcopy`, Ops sequenziell; `set` legt fehlende Zwischen-Mappings an; ein Zwischenknoten, der kein Mapping ist, ein `delete` auf einen nicht vorhandenen Pfad oder ein Pfad außerhalb Allowlist/in der Sperrliste → `ValueError` mit kurzer englischer Meldung, der Handler bildet das auf `error/invalid_args` ab, Review-Minor 3; keine Listen-Traversierung, Pfade sind nur Mapping-Keys); Erweiterung von `validate_write_args` (Typ `put-config` delegiert an `validate_put_config_args`); `config_file_sha256(path: Path) -> str` (wird nicht neu angelegt: F1 Task 15 definiert sie in `fleet_client.py`; F2 nutzt sie wieder und verifiziert, dass `get-config` sie verwendet, damit `get-config` und der `put-config`-Handler dieselbe Funktion teilen); Consumes: `lib.redaction.contains_redaction_marker`, F2-B2 (`validate_write_args`).
- [ ] Step 1: Test schreiben (fail): Ad-hoc `.tmp/f2-b5-check.py`: `validate_put_config_args({"key": "project", "base_sha256": "a"*64, "ops": [{"op": "set", "path": "fleet.enabled", "value": False}]})` muss `("path_not_writable", …)` liefern — vor der Änderung `ImportError`.
- [ ] Step 2: Konstanten, `validate_put_config_args`, `apply_config_ops` implementieren (`config_file_sha256` aus F1 wiederverwenden, Grep: `get-config` nutzt sie); `validate_write_args` erweitern. Für den Gate-Leckfreiheits-Test (Step 1/3) wird ein gestubbter `put-config`-Handler benötigt, sonst liefert `handle_command` `unknown_command`.
- [ ] Step 3: Test (pass), Prüffälle: Sperrliste (`admin-ui.port`, `hooks`, `variables.x`, `mcp-servers`) → `path_not_writable` auch bei testweise um den Key erweiterter Allowlist; `provider-options` und `context-profile` mit Default-Allowlist → `path_not_writable` (AC-53 b, Teil „vor accepted"); `[REDACTED]` als Wert und verschachtelt `{"a": ["[REDACTED]"]}` → `redacted_value`; 21 Ops → `invalid_args`; `apply_config_ops({"dod-preset": "a"}, [{"op": "set", "path": "model-overrides.developer", "value": "x"}], REMOTE_WRITE_ALLOWLIST)` → `{"dod-preset": "a", "model-overrides": {"developer": "x"}}` bei unverändertem Eingabe-Mapping; `delete` auf nicht vorhandenen Pfad → `ValueError`; Gate-Leckfreiheit mit `path_not_writable`: `FleetClient._handle_write_command` mit einem `put-config`-Kommando auf `fleet.enabled` → `rejected/path_not_writable`, danach ein gültiges Write → `accepted` (nicht `busy`).
- [ ] Step 4: commit `feat(fleet): add put-config validation and ops application`

### Task 15: F2-B6 — `roundtrip_guard` in `ConfigManager.write`, Handler `put-config` und Injektion (AC-42, AC-44, AC-45, AC-53)
**Agent:** senior-developer
**Depends on:** 6, 13, 14
**Files:**
- Modify: `scripts/admin-server.py`
**Interfaces:** Produces: `ConfigManager.write(self, key: str, data: Any, *, allow_lossy: bool = False, roundtrip_guard: bool = False) -> dict` (neuer keyword-only Parameter, D12/A9; der Round-Trip-Guard läuft, wenn `key == "ai-providers" or roundtrip_guard` und die Datei existiert, jeweils **vor** Backup und `os.replace`; Admin-UI-Aufrufer übergeben ihn nicht, ihr Verhalten bleibt unverändert); Modulfunktion `_fleet_put_config_handler(args: Mapping[str, Any]) -> dict` und erweitertes `_fleet_write_handlers()` (liefert zusätzlich `"put-config": _fleet_put_config_handler`); Ok-Result von `put-config` ausschließlich `{"backup": <str|None>}`; Consumes: F2-B4 (`_validate_project_document`), F2-B5 (`apply_config_ops`, `REMOTE_WRITE_ALLOWLIST`), F1 (`config_file_sha256`, gemeinsamer Hash-Helper für `get-config` und `put-config`), `lib.redaction.redact_text`, `lib.yaml_roundtrip` (`assert_roundtrip_preserved`, `YamlRoundTripLoss`), `ConfigManager.read/write/resolve_path`.
**Ablauf im Handler (läuft im Worker nach `accepted`; jede Ablehnung ist `{"status": "error", "result": None, "error": {"code": …, "message": …}}`, `message` durch `redact_text`, ≤ 200 Zeichen):**
1. `config_manager = AdminRequestHandler.config_manager`; `path = config_manager.resolve_path("project")`; `config_file_sha256(path) != args["base_sha256"]` (Vergleich per `hmac.compare_digest`) → `base_hash_mismatch`, **keine** Schreiboperation.
2. `existing = config_manager.read("project")` (kein Mapping → `{}`); `new = apply_config_ops(existing, args["ops"], REMOTE_WRITE_ALLOWLIST)`; `ValueError` → `invalid_args`.
3. `h = AdminRequestHandler.__new__(AdminRequestHandler)`; **zuerst** `h._assert_project_sections_writable(set(existing) - set(new))` (Lösch-Prüfung entfernter Top-Level-Sektionen; steht **im Fleet-Handler, nicht** in `_validate_project_document`), **danach** `h._validate_project_document(new, existing)`; `ValueError` → `invalid_config` (Nachricht = `str(exc)`, z. B. `section not allowed: max-parallel-agents` oder `context-profile.invalid: …`), keine Schreiboperation.
4. `res = config_manager.write("project", new, roundtrip_guard=True)` (`allow_lossy` wird nie übergeben und ist nicht über Args steuerbar; atomar, Backup, chmod 600 — bestehendes Verhalten). `YamlRoundTripLoss` wird **vor** dem allgemeinen `ValueError` gefangen → `comments_lost` (Datei byte-identisch, kein Backup, keine `.tmp`-Datei; D12); sonstige Exception → `internal_error` (Details nur ins Server-Log). Kein eigener `analyze_roundtrip`-Dump im Handler (A9: keine zweite Serialisierung).
5. Ergebnis `{"status": "ok", "result": {"backup": res["backup"]}, "error": None}` (kein Feld `comments_lost` im Ok-Result).

- [ ] Step 1: Symbole per Grep verifizieren (Fundstellen im Task-Bericht): `def write\(self, key: str, data: Any, \*, allow_lossy` in `scripts/admin-server.py` (`ConfigManager.write`, bisher ohne `roundtrip_guard`); die Bedingung `key == "ai-providers" and path.exists()` und `assert_roundtrip_preserved(` darin; `class YamlRoundTripLoss(ValueError)`, `def assert_roundtrip_preserved`, `def analyze_roundtrip` in `scripts/lib/yaml_roundtrip.py`; Rückgabedict von `write` enthält den Key `backup`; alle Aufrufer `config_manager.write(` in `scripts/admin-server.py` (mehrere Stellen, alle ohne `roundtrip_guard`) — sie bleiben unverändert. Fehlt ein Symbol: STOP und melden.
- [ ] Step 2: Test schreiben (fail): Ad-hoc `.tmp/f2-b6-guard-check.py` mit Wegwerf-Root (kommentierte `.meta-config/project.yaml` mit `dod-preset`): `config_manager.write("project", data, roundtrip_guard=True)` → vor der Änderung `TypeError: write() got an unexpected keyword argument 'roundtrip_guard'`.
- [ ] Step 3: `roundtrip_guard` implementieren: Signatur `write(self, key, data, *, allow_lossy=False, roundtrip_guard=False)`; Guard-Bedingung `if (key == "ai-providers" or roundtrip_guard) and path.exists():` (Rest des Blocks, `allow_lossy`-Durchreichung und Reihenfolge Guard → Backup → `.tmp` → `os.replace` unverändert); Docstring (Englisch) ergänzen: `roundtrip_guard` extends the abort-on-lossy-save guard to any key (used by the fleet `put-config` handler, never set by the admin UI).
- [ ] Step 4: Test (pass), Guard separat: (a) kommentierte Datei + `roundtrip_guard=True` → `YamlRoundTripLoss`, Datei-Bytes identisch, Backup-Verzeichnis unverändert (kein neues Backup), keine `.tmp`-Datei neben der Datei; (b) kommentarfreie Datei + `roundtrip_guard=True` → schreibt, Backup angelegt, Modus 0600; (c) kommentierte Datei + Default (`write("project", data)`) → schreibt wie bisher (Admin-UI unverändert); (d) `ai-providers` verhält sich unverändert (Guard ohne den Parameter). Dauerhafter Test: Task 19 (F2-T5).
- [ ] Step 5: Handler implementieren und in `_fleet_write_handlers()` registrieren (Imports innerhalb der Funktion nach `_ensure_scripts_on_path(AdminRequestHandler.root)`); Ad-hoc `.tmp/f2-b6-check.py` zuerst fail: `_fleet_put_config_handler` fehlt → `NameError`. Fixtures: kommentarfreie und kommentierte Variante der `.meta-config/project.yaml` (`dod-preset`, `model-overrides`, `max-parallel-agents: 2`).
- [ ] Step 6: Test (pass), Prüffälle aus AC-53/AC-44/AC-45 (jeweils Datei-Bytes vor/nach vergleichen, kommentarfreie Fixture, sofern nicht anders genannt): (a) `set max-parallel-agents = 4` → `error/invalid_config`, Meldung enthält `section not allowed`, Datei byte-identisch; (b) mit testweise `REMOTE_WRITE_ALLOWLIST + ("context-profile",)` (Monkeypatch des Modulattributs im Ad-hoc-Skript) `set context-profile = "huge"` → `error/invalid_config` mit `context-profile.invalid`; (c) `delete max-parallel-agents` → `error/invalid_config` mit `section not allowed: max-parallel-agents`, Datei byte-identisch; `delete model-overrides.developer` → `ok`, Backup vorhanden; (d) falsches `base_sha256` → `error/base_hash_mismatch`, Datei byte-identisch; (e) AC-44: gültiges `set dod-preset = "standard"` → `ok`, `result` hat genau den Key `backup` (String), Datei hat Modus 0600 (`stat`); (f) AC-45: dasselbe Kommando auf der **kommentierten** Fixture → `error/comments_lost`, `config_file_sha256` vor/nach identisch, kein neues Backup, keine `.tmp`-Datei.
- [ ] Step 7: Grep-Nachweise: `_validate_project_document` kommt in `scripts/admin-server.py` genau 3-mal vor (Definition, `_route_put_config`, Fleet-Handler); `_assert_project_sections_writable(set(existing) - set(new))` steht im Fleet-Handler und nicht im Rumpf von `_validate_project_document`; `_guard_model_block_write` wird im Fleet-Handler nicht aufgerufen (O-F3: nur nötig, wenn `model-override-all`/`model-inherit-main-chat` in die Allowlist aufgenommen werden); `roundtrip_guard=True` kommt genau einmal als Aufruf vor (Fleet-Handler), `allow_lossy` weder im Fleet-Handler noch in `scripts/lib/fleet_client.py`.
- [ ] Step 8: Regression: `python3 -m pytest tests/test_admin_server.py -q` → 0 failed.
- [ ] Step 9: commit `feat(admin): add roundtrip_guard and put-config fleet handler`

### Task 16: F2-C2 — Dashboard: Config-Edit-Dialog
**Agent:** developer
**Depends on:** 7, 14, 15
**Files:**
- Modify: `docs/ui/fleet-ui.html`
**Interfaces:** Produces: Funktion `openConfigEditor(instance)` (Ablauf: `get-config` ausführen, bestehender Phase-2-Pfad F1-I, und aus dem Result `sha256` als `base_sha256` übernehmen; Formular mit bis zu 20 Op-Zeilen mit Auswahl `set`/`delete`, Pfad-Feld und Wert-Feld als JSON-Text nur bei `set`; clientseitige UX-Vorprüfung mit Pfad-Regex wie `validate_put_config_args`, Wert muss gültiges JSON sein, kein `[REDACTED]`-Wert, **nicht** autoritativ; danach `runWriteCommand(instance, "put-config", args, warning)` mit `warning` = Hinweis (Deutsch) „Enthält die project.yaml YAML-Kommentare, bricht die Instanz ab (comments_lost); die Datei bleibt unverändert und muss vor Ort bearbeitet werden." (D12); der Bestätigungsdialog zeigt **alle** Ops (Op, Pfad, Wert) und den Hinweis, bietet aber **keine** Option, verlustbehaftetes Schreiben zu bestätigen; nach dem Terminal-Ack werden bei `ok` das `backup` und bei `error/comments_lost` die `message` per `textContent` angezeigt); Button „Config ändern" nur bei `status.allow_remote_write === true`; Consumes: `runWriteCommand`, `showConfirmDialog`, `displaySafe` (F2-C1/F1-G), Ack-Result von `get-config` (`sha256`), Ack-Result von `put-config` (`backup`) und Terminal-Ack `error/comments_lost` (`message`).
- [ ] Step 1: Statische Baseline: Grep `innerHTML|outerHTML|insertAdjacentHTML|eval\(` → 0 Datenzuweisungen.
- [ ] Step 2: Editor, Op-Zeilen-Verwaltung und Dialog-Warnung implementieren (nur `createElement`/`textContent`).
- [ ] Step 3: Prüfen: Grep wie Step 1 → weiterhin 0 Treffer; Grep `Kommentare` in `docs/ui/fleet-ui.html` → mindestens 1 Treffer (Hinweistext im Dialog-Aufruf).
- [ ] Step 4: Manuell (Loopback, `.tmp/`-State): Dialog zeigt vor dem Absenden den Kommentarverlust-Hinweis und keine Option zum Bestätigen verlustbehafteten Schreibens (AC-45); ein Op mit Wert `"[REDACTED]"` wird clientseitig blockiert und instanzseitig als `redacted_value` abgelehnt (Gegenprobe über direkten `curl`-POST); Ergebnisanzeige enthält bei `ok` das `backup`, bei kommentierter Datei die `message` zu `error/comments_lost`.
- [ ] Step 5: commit `feat(fleet-ui): add remote config edit dialog`

### Task 17: F2-D2 — Doku Schreibpfad Phase 4
**Agent:** documenter
**Depends on:** 8, 15, 16
**Files:**
- Modify: `docs/howto/fleet-server.md`
- Modify: `docs/api/fleet-api-reference.md`
**Interfaces:** Produces: Howto-Abschnitt `## Schreibpfad (Phase 4: Remote-Config-Edit)` (Ablauf `get-config` → `base_sha256` → Ops → Bestätigung; `REMOTE_WRITE_ALLOWLIST` als Default-Liste; Sperrliste mit 11 Schlüsseln; Hinweis auf die wirksame Schnittmenge mit `PROJECT_WRITABLE_SECTIONS`, `max-parallel-agents` ist remote weder setz- noch löschbar, O-F3; Werte von `ai-providers`/`model-overrides` werden wie in der Admin-UI nicht inhaltlich validiert, R-15; Abbruch bei Kommentarverlust (D12, R-17): eine kommentierte `project.yaml` ist remote nicht editierbar, `error/comments_lost`, Datei unverändert, kein Backup, kein Remote-Opt-in; Abhilfe: Datei vor Ort manuell bearbeiten oder Kommentare bewusst entfernen; Backup-Wiederherstellung nach erfolgreichem Schreiben Schritt für Schritt: Backup-Datei aus dem Ack neben `.meta-config/project.yaml` auffinden, Datei zurückkopieren, `chmod 600`; Hinweis auf akzeptiertes Risiko paralleler Sync (R-16); Restfenster ohne Dateisperre, PA-5; Rollback) und API-Referenz (`put-config`-Args `key`, `base_sha256`, `ops`; Ok-Result ausschließlich `backup`; instanzseitige Codes `path_not_writable`, `redacted_value`, `base_hash_mismatch`, `invalid_args` (auch `apply_config_ops`-Fehler nach `accepted`), `invalid_config`, `comments_lost`, `internal_error` mit Zuordnung `rejected` vor `accepted` bzw. `error` nach `accepted`); Consumes: Spec IC-7, IC-15, D12, O-F3, R-15, R-17; Task-Ergebnisse F2-B5/F2-B6.
- [ ] Step 1: Abschnitte schreiben (Deutsch; Schlüssel, Header, Codes Englisch).
- [ ] Step 2: Prüfen: Grep `base_sha256|path_not_writable|redacted_value|invalid_config|comments_lost` in beiden Dateien → je mindestens 1 Treffer; die Default-Allowlist in der Doku stimmt Eintrag für Eintrag mit `REMOTE_WRITE_ALLOWLIST` in `scripts/lib/fleet_client.py` überein (manueller Abgleich im Task-Bericht).
- [ ] Step 3: commit `docs: document fleet remote config edit path`

### Task 18: F2-T4 — Tests: `put-config`-Logik (empfohlen (Security))
**Agent:** tester
**Depends on:** 14
**Files:**
- Create: `tests/test_fleet_put_config.py`
**Interfaces:** Produces: unittest-Klassen `TestValidatePutConfigArgs`, `TestApplyConfigOps`; Consumes: `lib.fleet_client` (`validate_put_config_args`, `apply_config_ops`, `REMOTE_WRITE_ALLOWLIST`, `REMOTE_NEVER_WRITABLE`), `lib.redaction.REDACTED`.
- [ ] Step 1: Tests `TestValidatePutConfigArgs`: `test_ac41_allowlist_boundary` (jeder Default-Allowlist-Eintrag und ein Unterpfad → `None`; ein nicht gelisteter Top-Level-Key → `path_not_writable`); `test_ac41_never_writable_even_if_allowlisted` (für jeden der 11 Sperrlisten-Schlüssel: Pfad `K` und `K.child`, mit um `K` erweiterter Allowlist → weiterhin `path_not_writable`); `test_ac43_redaction_marker_rejected` (`"[REDACTED]"`, verschachtelt in Dict/Liste, `amf_***`-Muster → `redacted_value`); `test_ops_limit_20` (21 → `invalid_args`, 20 → `None`); `test_bad_shape_invalid_args` (fehlende Keys, `key != "project"`, `base_sha256` kein 64-Hex, `delete` mit `value`, Pfad mit `..`/leerem Segment); `test_check_order_paths_before_values` (ungültiger Pfad und `[REDACTED]`-Wert in einer Anfrage → `path_not_writable`).
- [ ] Step 2: Tests `TestApplyConfigOps`: `test_set_creates_intermediate_mappings`, `test_delete_existing_path`, `test_delete_missing_path_raises_value_error`, `test_traverse_non_mapping_raises_value_error`, `test_input_not_mutated` (Deep-Copy: `current` vor/nach gleich), `test_ops_applied_sequentially`, `test_path_outside_allowlist_raises_value_error` (Verteidigung in der Tiefe), `test_failure_is_atomic` (zweiter Op scheitert → kein Teilergebnis, `ValueError`).
- [ ] Step 3: Ausführen: `python3 -m pytest tests/test_fleet_put_config.py -q` → alle Tests `passed`, 0 failed.
- [ ] Step 4: commit `test(fleet): cover put-config validation and ops application`

### Task 19: F2-T5 — Tests: `put-config`-Handler und Validierungsparität (empfohlen (Security))
**Agent:** tester
**Depends on:** 15
**Files:**
- Create: `tests/test_fleet_put_config_handler.py`
**Interfaces:** Produces: unittest-Klassen `TestPutConfigHandler`, `TestAdminUiParity`, `TestConfigManagerRoundtripGuard` (eigene Datei, unabhängig von F2-T2); Consumes: `admin-server.py` per `importlib` (`_fleet_put_config_handler`, `AdminRequestHandler`, `ConfigManager`), `FleetClient` (für den End-to-End-Pfad Poll-Thread → Worker), temporärer Root mit kommentierter `.meta-config/project.yaml`.
- [ ] Step 1: Fixture: zwei Wegwerf-Roots, kommentarfrei (Standard) und kommentiert (AC-45), jeweils mit `.meta-config/project.yaml` (`dod-preset`, `model-overrides: {developer: x}`, `max-parallel-agents: 2`, `fleet`-Block, `admin-ui.token`), `AdminRequestHandler.root`/`config_manager` gesetzt, Helfer `_sha(path)`.
- [ ] Step 2: Tests `TestPutConfigHandler`: `test_ac42_base_hash_mismatch_no_write` (nach `accepted` Terminal-Ack `error/base_hash_mismatch`, Bytes identisch); `test_ac44_valid_write_backup_mode_audit` (kommentarfreie Datei; Datei 0600, Ok-Result hat genau den Key `backup` (String, Backup-Datei existiert), kein Feld `comments_lost`, Instanz-Audit enthält `command_ack`, Server-Audit-Pendant per F2-T1-Fixture oder Hinweis im Bericht); `test_ac44_fleet_never_passes_allow_lossy` (Quelltext-Grep: `allow_lossy` weder in `fleet_client.py` noch im Fleet-Handler); `test_ac45_commented_file_aborts_comments_lost` (kommentierte Datei: nach `accepted` Terminal-Ack `error/comments_lost`, `config_file_sha256` vor/nach identisch, kein neues Backup, keine `.tmp`-Datei); `test_ac41_path_not_writable_before_accepted` (Ack `rejected/path_not_writable`, Datei byte-identisch, **nächstes gültiges Write → `accepted`, nicht `busy`**; Review-Minor 2; hier liegt die Gate-Leck-Prüfung für `path_not_writable`); `test_ac43_redacted_value_before_accepted`; `test_apply_failure_is_error_invalid_args_after_accepted` (`delete` auf nicht vorhandenen Pfad: erst `accepted`, dann Terminal-Ack `error/invalid_args`, Datei byte-identisch; Review-Minor 3); `test_fleet_block_never_writable` (`set fleet.allow-remote-write` → `rejected/path_not_writable`, Gate kann nicht remote geöffnet werden); `test_admin_ui_token_never_returned_or_written` (`set admin-ui.token` → `rejected/path_not_writable`).
- [ ] Step 3: Tests `TestAdminUiParity` (AC-53): `test_ac53_validate_project_document_called_by_both_paths` (Quelltext-Grep: `_route_put_config` und `_fleet_put_config_handler` rufen `_validate_project_document` auf; die Methode enthält genau die drei Aufrufe `_validate_project_provider_options`, `_guard_context_profile_write` (2×) plus `_assert_project_update_writable` und **kein** `_guard_model_block_write`); `test_ac53_case_a_max_parallel_agents_set`; `test_ac53_case_b_context_profile_with_extended_allowlist` (Allowlist per `unittest.mock.patch.object` erweitern; ohne Erweiterung `rejected/path_not_writable`); `test_ac53_case_c_delete_max_parallel_agents` und `test_ac53_delete_allowed_section_is_written` (`model-overrides.developer`); `test_ac53_deletion_check_lives_in_fleet_handler` (Quelltext: `_assert_project_sections_writable(set(existing) - set(new))` im Fleet-Handler, nicht in `_validate_project_document`); `test_admin_ui_put_project_unchanged` (`_route_put_config("project")` per Handler-Instanz und gepatchtem `_read_body`/`_send_json`: gleiche Antworten/Fehler für denselben Body vor und nach der Extraktion — Referenzwerte aus dem Stand vor F2-B4 (`git`-freie Abbildung: die Erwartungen entsprechen den bestehenden Admin-UI-Tests, die in F2-B4 Step 2 als Baseline gemessen wurden)).
- [ ] Step 3b: Tests `TestConfigManagerRoundtripGuard` (AC-44/AC-45, getrennt vom Handler, Admin-UI-Verhalten): `test_roundtrip_guard_aborts_commented_file` (`write("project", data, roundtrip_guard=True)` → `YamlRoundTripLoss`, Bytes identisch, Backup-Verzeichnis unverändert, keine `.tmp`-Datei); `test_roundtrip_guard_allows_comment_free_file` (schreibt, Backup, Modus 0600); `test_default_write_unchanged_for_commented_project` (ohne `roundtrip_guard` schreibt `write("project", data)` wie bisher, Admin-UI-Verhalten unverändert); `test_ai_providers_guard_unchanged` (Guard für `ai-providers` ohne den Parameter, `allow_lossy=True` weiterhin Opt-out); `test_roundtrip_guard_is_keyword_only` (`write("project", data, False, True)` → `TypeError`).
- [ ] Step 4: Ausführen: `python3 -m pytest tests/test_fleet_put_config_handler.py -q` → alle Tests `passed`, 0 failed.
- [ ] Step 5: commit `test(fleet): cover put-config handler and admin-ui validation parity`

### Task 20: F2-V2 — Verifikation Phase 4
**Agent:** tester
**Depends on:** 17
**Files:**
- Modify: `docs/howto/fleet-server.md`
**Interfaces:** Produces: dokumentierter manueller `put-config`-Lauf inkl. Backup-Wiederherstellung (Abschnitt `### Beispiel: Remote-Config-Edit`) und Exit-Nachweis Phase 4; Consumes: alle Phase-4-Implementierungs-Tasks (13 bis 17) sowie die Ergebnisse der Test-Tasks 18 und 19 (F2-T4, F2-T5), soweit umgesetzt (D8, kein Merge-Gate).
- [ ] Step 1: Tests (soweit umgesetzt): `python3 -m pytest tests/test_fleet_put_config.py tests/test_fleet_put_config_handler.py tests/test_fleet_write.py tests/test_fleet_write_server.py tests/test_fleet_write_gate.py tests/test_admin_server.py tests/test_python_compat_consistency.py -q` → 0 failed. Nicht umgesetzte Test-Tasks (D8) im Bericht listen.
- [ ] Step 2: Grep-Nachweise (AC-53): `_validate_project_document` 3 Treffer in `scripts/admin-server.py`; `_guard_model_block_write` nicht im Rumpf der Methode und nicht im Fleet-Handler; `REMOTE_NEVER_WRITABLE` enthält genau die 11 Schlüssel aus IC-15; `roundtrip_guard=True` genau einmal als Aufruf (Fleet-Handler), `allow_lossy` weder im Fleet-Handler noch in `fleet_client.py`.
- [ ] Step 3: Manueller Lauf auf dem Wegwerf-Projekt aus F2-V1 (`allow-remote-write: true`): im Dashboard „Config ändern": `set dod-preset` auf einen anderen gültigen Wert → Dialog mit Kommentarverlust-Hinweis → Bestätigen → Ergebnis mit `backup` (kommentarfreie `project.yaml`); `.meta-config/project.yaml` hat Modus 0600; danach Wiederherstellung aus dem Backup und Gegenprobe `set fleet.enabled` → abgelehnt (`path_not_writable`). Zweiter Lauf mit einer kommentierten `project.yaml`: Ergebnis `error/comments_lost`, `config_file_sha256` vor/nach identisch, kein neues Backup (AC-45). Beobachtungen ins Howto übernehmen.
- [ ] Step 4: `python3 scripts/sync.py --validate` → Exit 0; `python3 scripts/sync.py --validate-spec-plan` → keine ERROR-Findings (Spec freigegeben vorausgesetzt).
- [ ] Step 5: commit `docs: record fleet f2 phase 4 end-to-end run`

## Fehlercode-Abdeckung (instanzseitige Ack-Codes, Spec IC-7)

| Code | Vor/Nach `accepted` | Erzeugt in (Label, Task-Nr.) |
|---|---|---|
| `unknown_command` | vor (`rejected`) | F2-B2 (4) |
| `remote_write_disabled` | vor (`rejected`) | F2-B2 (4) |
| `duplicate_command` | vor (`rejected`) | F2-B2 (4) |
| `invalid_args` | vor (`rejected`, Poll-Thread) bzw. nach (`error`, `apply_config_ops`-`ValueError`) | F2-B2 (4), F2-B5 (14), F2-B6 (15) |
| `path_not_writable` | vor (`rejected`) | F2-B5 (14) |
| `redacted_value` | vor (`rejected`) | F2-B5 (14) |
| `busy` | vor (`rejected`, Fleet-Gate `FLEET_WRITE_GATE`) bzw. nach (`error`, nur falls im Handler ein Fleet-Busy-Zustand erkannt wird; nie aus `SyncExecutor`, D11) | F2-B1 (2), F2-B2 (4) |
| `base_hash_mismatch` | nach (`error`) | F2-B6 (15) |
| `invalid_config` | nach (`error`) | F2-B6 (15) |
| `comments_lost` | nach (`error`, `YamlRoundTripLoss` aus `ConfigManager.write(..., roundtrip_guard=True)`, D12) | F2-B6 (15) |
| `internal_error` | nach (`error`) | F2-B2 (4), F2-B3 (6), F2-B6 (15) |

## Offene Punkte

- **Geschlossen (Spec Rev. 1.4):** O-F1 (Long-Poll, D9), O-F2 (Abbruch bei Kommentarverlust, D12), O-F9 (Token-Kette Env > Datei, D10). Einziger offener Eintrittspunkt für Phase 3: O-F3.
- **O-F10** (Szenario-ID 79 kollidiert mit dem Opencode-v2-Plan): betrifft F1 (Szenario `79-fleet-config-opt-in`), nicht F2; wird bei Freigabe der Spec geklärt, hier nicht umnummeriert.
- **O-F3** (Allowlist-Inhalt): Plan setzt die Default-Liste um. Aufnahme von `model-override-all`/`model-inherit-main-chat` erfordert zusätzlich `_guard_model_block_write` im Fleet-Handler (F2-B6).
- **PA-1 bis PA-7** (Plan-Annahmen, oben): PA-1 (Write-Token-Datei manuell anlegen) und PA-2 (Exit ≠ 0 → `error/internal_error`) sind Nutzer-/Review-Rückfragen, falls abweichend gewünscht; PA-7 (`rejected` → HTTP 200) ist entschieden (IC-7).
- Ungeprüft bei Planerstellung (F1 nicht gemergt): alle Symbolnamen in `scripts/fleet-server.py`, `scripts/lib/fleet_client.py`, `scripts/lib/fleet_protocol.py`, `docs/ui/fleet-ui.html` — werden in Task F2-S1 Step 4 inventarisiert.

## Self-Review

- **AC-Abdeckung:** Jedes Phase-3/4-AC (AC-37 bis AC-46, AC-52, AC-53; AC-54 gestrichen, nicht abgebildet) ist mindestens einem Implementierungs-Task und einem Test-/Verifikations-Task zugeordnet (Traceability-Tabelle unten).
- **Eine Rolle je Task:** jeder Task hat genau ein `Agent:`-Feld (senior-developer, developer, tester, documenter).
- **Files/Interfaces:** vollständig; jeder Task hat `**Interfaces:**` mit Inhalt auf derselben Zeile (keine leeren Interfaces). Datei-Disjunktheit der Parallelgruppe `g1` (`F2-A1`: `scripts/fleet-server.py`, `F2-B1`: `scripts/lib/fleet_client.py`; `F2-B2` hängt wegen derselben Datei von `F2-B1` ab und steht nicht in `g1`) und der Test-Tasks (je eigene Datei, auch F2-T2 und F2-T5) nach `check_plan_file_overlap` (`scripts/lib/orchestration.py`) prüfbar. Gemeinsame Dateien sind über `Depends on:` serialisiert (siehe Ausführungsmodell).
- **Task-IDs:** alle Header rein numerisch (1 bis 20), `Depends on:` nur Nummern; Label ↔ Nummer in der Tabelle unter „Ausführungsmodell". V1/V2 hängen nicht von Test-Tasks ab (D8).
- **Review-Minors eingearbeitet:** (1) entfällt mit AC-54 (keine Admin-Routen-Änderung, D11); (2) `remote_write`-Prüfung/Dedupe/Arg-Prüfung vor Gate-Acquire, Gate-Freigabe im Fehlerpfad, `path_not_writable` führt nicht zu `busy` (F2-B2, F2-B5, F2-T2, F2-T5); (3) `apply_config_ops`-Fehler → `error/invalid_args` (F2-B5, F2-B6, Fehlercode-Tabelle, F2-T5); (4) Blocker-Spike zuerst (F2-S1, Gate für F2-B4/B6); (5) modulweites `FLEET_WRITE_GATE` statt Klassen-Attribut (F2-B1, F2-T3).
- **Spec-Rev. 1.4 umgesetzt:** D9 (Long-Poll, kein SSE-Anteil im Plan), D10 (Token-Kette Env > Datei, kein Plan-Eingriff), D11/R-16 (eigenes Gate, `SyncExecutor` unverändert, PA-8), D12/A9 (`roundtrip_guard`, `comments_lost`, R-17), `config_file_sha256` als gemeinsamer Helper, O-F10 vermerkt.
- **Messbarkeit:** jede Akzeptanz ist ein Kommando mit erwartetem Ergebnis (Exit-Code, `passed`-Zeile, Grep-Trefferzahl, HTTP-Status/Fehlercode, Datei-Bytes).
- **Placeholder-Freiheit:** keine Platzhalter-Wörter, keine einzelnen Auslassungspunkte-Zeilen, keine leeren `Interfaces:`.
- **`pipeline_stages`:** Frontmatter am Dateianfang (`implement: 3`); Task 3 (F2-A1) ist ein `developer`-Task.

### Traceability Spec ↔ Task ↔ Test

| AC | Implementierung (Task-Nr.) | Test / Nachweis (Task-Nr.) |
|---|---|---|
| AC-37 | F2-B2 (4), F2-B3 (6) | F2-T2 (10) `test_ac37_*` |
| AC-38 | F2-A1 (3), F2-A2 (5) | F2-T1 (9) `test_ac38_*` |
| AC-39 | F2-A2 (5), F2-B1 (2), F2-B2 (4), F2-B3 (6) | F2-T2 (10) `test_ac39_*`, F2-V1 (12) Step 2 (Grep) |
| AC-40 | F2-A1 (3), F2-A2 (5) | F2-T1 (9) `test_ac40_*` |
| AC-41 | F2-B5 (14) | F2-T4 (18) `test_ac41_*`, F2-T5 (19) `test_ac41_*` |
| AC-42 | F2-B6 (15) | F2-T5 (19) `test_ac42_*` |
| AC-43 | F2-B5 (14) | F2-T4 (18) `test_ac43_*`, F2-T5 (19) `test_ac43_*` |
| AC-44 | F2-B6 (15) | F2-T5 (19) `test_ac44_*`, `TestConfigManagerRoundtripGuard`, F2-V2 (20) Step 2 (Grep) |
| AC-45 | F2-B6 (15), F2-C2 (16) | F2-T5 (19) `test_ac45_*`, `TestConfigManagerRoundtripGuard`, F2-C2 (16) Step 3-4, F2-V2 (20) Step 3 |
| AC-46 | F2-B2 (4) | F2-T2 (10) `test_ac46_*` |
| AC-52 | F2-B1 (2), F2-B2 (4) | F2-T2 (10) `test_ac52_*`, F2-T3 (11) `test_ac52_*` |
| AC-53 | F2-B4 (13), F2-B6 (15) | F2-T5 (19) `test_ac53_*`, F2-V2 (20) Step 2 (Grep) |
| AC-54 | gestrichen (User, 2026-10-28; D11) | nicht abgebildet, nicht erforderlich; Nummer bleibt reserviert. Akzeptiertes Risiko „paralleler Sync aus Admin-UI und Fleet" (R-16): PA-8, Howto Task 8 |
