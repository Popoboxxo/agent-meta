---
spec-id: SPEC-FLEET-SERVER-2026-10-23
title: Fleet-Server (Phasen 1-4) — Read-Only-Dashboard, Config-Ansicht, Remote-Sync-Trigger, Remote-Config-Edit
status: Entwurf
revision: 1.3
supersedes: docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md
issues: "#682 §7 (Primärquelle, IDEA); abgegrenzt: #877, #977, #528-#531"
---

# Fleet-Server (Phasen 1-4) — Spec

> Status: Entwurf
> Trace-Anker: `spec-id: SPEC-FLEET-SERVER-2026-10-23`
>
> Supersedes `docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md` (Legacy-Pfad; die Datei bleibt erhalten und bekommt in Plan F1 einen Hinweis-Header auf diese Spec).
>
> Primärquelle: GitHub-Issue #682 §7 („Agent-Meta Fleet-Server", Stufe IDEA). Ursprung des Bedarfs: `docs/concepts/planned/admin-ui-concept.md:885` (§12, Risiko „Multi-Repo-Szenario … **Noch offen.**"). Die Alt-Spec zitiert dafür fälschlich `docs/superpowers/specs/admin-ui-concept.md` — diese Datei existiert nicht.
>
> Freigabe ausschließlich durch den Nutzer (kein Self-Approve). Code-Stand der Verifikation: Branch `docs/fleet-server-spec-plans`, Commit `c0e6e8ff`, `scripts/admin-server.py` mit 5946 Zeilen. Zeilennummern sind Orientierung, **Symbole sind maßgeblich**.
>
> Evidenzmarker: **VERIFIED** = im Repo geprüft (Datei:Symbol bzw. Grep). **NEU** = existiert heute nicht, wird durch diese Spec definiert.

---

## Problem

`scripts/admin-server.py` läuft pro Repository und kennt keine anderen Instanzen. Wer mehrere agent-meta-instrumentierte Repos betreibt (z. B. ReqogniLoom, ha-health-o-mat, ha-go-gauge, agent-meta selbst), hat keinen zentralen Ort, der zeigt, welche Instanz auf welcher agent-meta-Version läuft, wann sie zuletzt synchronisiert hat, ob der Sync gesund ist und welche Provider aktiv sind. Heute muss jede Admin-UI einzeln geöffnet werden. Das Admin-UI-Konzept hat dieses Multi-Repo-Szenario als Risiko „Hoch / noch offen" markiert (`docs/concepts/planned/admin-ui-concept.md:885`).

Die Alt-Spec (2026-09-07) beschreibt einen Fleet-Server für Phase 1+2, enthält aber mehrere Annahmen, die der reale Code widerlegt (Abschnitt „Drift-/Korrekturtabelle"), deckt Phase 3+4 nicht ab, liegt im Legacy-Pfad und erfüllt das Spec-Template nicht (kein Frontmatter, kein `Status:`, kein `spec-id:`, fehlende Pflichtsektionen laut `scripts/lib/consistency/spec_plan.py::REQUIRED_SPEC_SECTIONS`, VERIFIED).

Sicherheitsrelevante Ausgangslage (VERIFIED):

1. Im gesamten Repo existiert kein TLS-Code (`grep -E "import ssl|SSLContext|wrap_socket" scripts/` → 0 Treffer). Die Admin-UI spricht Plain-HTTP; TLS wird laut `docs/howto/admin-ui-remote-access.md` (Abschnitt TLS, ~Z. 336) per Reverse-Proxy davor terminiert; der Netzplan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md` erklärt HTTPS zum Nicht-Ziel (Q9).
2. Es gibt keine öffentliche Python-Funktion zur Redaktion von `project.yaml` (Inventar siehe IC-3). `GET /api/config/<key>` (`AdminRequestHandler._route_get_config` → `ConfigManager.read`) liefert die Config **unredigiert**, inklusive `admin-ui.token` im Klartext.
3. Es gibt keinen Log-Lese-Endpunkt (`/api/logs` o. ä. existiert nicht).
4. Es gibt keinen provider-neutralen Audit-Log. `class AuditService` (`scripts/admin-server.py`) ist Consistency-/Config-Audit, kein Ereignisprotokoll; der einzige Audit-Mechanismus ist `.claude/hooks/.guard-audit.log` (Hook-/Claude-spezifischer Pfad, geschrieben über `hooks/1-generic/lib/hook_common.sh::hook_audit_log_append`).

## Ziel

1. **Phase 1 — Read-Only-Dashboard:** Opt-in-Instanzen melden sich ausgehend (Push/Phone-Home) bei einem selbst gehosteten `scripts/fleet-server.py`, senden alle 30 s einen Status-Heartbeat (Version, letzter Sync, Health, aktive Provider) und liefern auf Anfrage redigierte Log-Auszüge. Ein statisches Dashboard `docs/ui/fleet-ui.html` zeigt alle Instanzen mit Liveness `online|stale|offline|never`.
2. **Phase 2 — Config-Ansicht:** Das Dashboard zeigt die `project.yaml` einer Instanz, instanzseitig per Allowlist redigiert, bevor sie übertragen wird.
3. **Phase 3 — Remote-Sync-Trigger:** Das Dashboard kann auf einer Instanz einen Sync auslösen — nur wenn die Instanz `fleet.allow-remote-write: true` gesetzt hat und der Bediener im Dashboard explizit bestätigt.
4. **Phase 4 — Remote-Config-Edit:** Das Dashboard kann allowlist-begrenzte Schlüssel der `project.yaml` ändern — gleiche Gates wie Phase 3, zusätzlich optimistische Nebenläufigkeitsprüfung und optionale Re-Authentisierung.
5. Sicherheitsmodell (Enrollment, Token, TLS, Pinning, Audit, Redaction) ist für alle vier Phasen einmal und vollständig spezifiziert.
6. Standardzustand jeder Instanz ist unverändert: ohne `fleet.enabled: true` entsteht keine Netzverbindung, kein Thread, keine Datei.
7. Nur Python-Stdlib (Konvention CLAUDE.md), Python-3.9-kompatibel (CI-Matrix 3.9/3.11/3.12, `scripts/lib/consistency/python_compat.py`), provider-agnostisch (Skill `provider-agnostic`).

### Strukturentscheidung

**Eine Spec, zwei Pläne.**

- **Eine Spec für Phase 1-4**, weil Enrollment, Token-Modell, TLS/Pinning, Threat-Model, Registry und Audit für alle Phasen identisch sind. Getrennte Specs würden diese Teile duplizieren, auseinanderdriften lassen und doppelte Reviews erzeugen. Die Phasen sind als eigene Abschnitte mit eigenen Entry-/Exit-Kriterien und Rollback getrennt (Abschnitt „Phasen").
- **Plan F1 (Fundament, Phase 1+2):** `scripts/fleet-server.py`, `scripts/lib/fleet_protocol.py`, `scripts/lib/fleet_client.py`, `scripts/lib/redaction.py`, Enrollment-CLI, Audit, Registry, Schema-Property, Szenario, minimaler Hook in `scripts/admin-server.py`, `docs/ui/fleet-ui.html`, Doku.
- **Plan F2 (Schreibpfad, Phase 3+4):** Write-Gates, Bestätigungs-Nonce, optionale Re-Auth, Write-Handler, UI-Bestätigungsdialog. Eigene Entry-/Exit-Gates; **hängt vom Merge von F1 ab**. F1 enthält strukturell keinen Write-Handler (Kommandos `trigger-sync`/`put-config` sind in F1 unbekannt → `unknown_command`).
- Abgelehnt: (a) vier Pläne — zu viel Koordinationsaufwand für geteilte Dateien; (b) ein Plan — mischt das risikoarme Lese-Fundament mit dem risikoreichen Schreibpfad und verhindert, dass Phase 1+2 unabhängig in Betrieb geht.

## Nicht-Ziele

- **Kein Bezug zu #877** (Subplattform-/Familien-Schicht, `docs/specs/2026-10-11-context-profiles-spec.md`). Komplementär: der Fleet-Server zeigt Instanz-Metadaten, ändert keine Plattform-Schicht.
- **Keine Doctor-/Context-Report-Daten (#977).** `meta-doctor`- bzw. Context-Report-Daten werden erst nach #977 Phase 0 verfügbar und sind hier ausschließlich Erweiterungspunkt (künftiges Payload-Schema `fleet-status-v2`, siehe O-F5).
- **Nicht die Review-Agent-Fleet (#528-#531)** (`docs/CODEBASE_OVERVIEW.md` §15, `tests/test_review_fleet.py`) und **nicht Claude-Codes „FleetView"**. „Fleet" meint hier ausschließlich die Menge der agent-meta-Instanzen.
- Keine Autodiscovery (mDNS, Netz-Scan); nur explizites Opt-in pro Instanz.
- Keine Benutzer-/Rollenverwaltung; ein Fleet-Admin-Token (aus Alt-Spec Q4 übernommen).
- Keine Registrierung ephemerer CI-Runner (aus Alt-Spec Q2 übernommen).
- Keine Registry-Verschlüsselung at rest; die Registry enthält keine Geheimnisse (D5).
- Keine History/Zeitreihen; `sqlite3` erst in einer späteren Ausbaustufe (D5).
- Kein Admin-UI-Formular und kein Admin-UI-Hinweis für den `fleet`-Block (Admin-UI-Integration ist Nicht-Ziel; Folge für die help-id-Konvention siehe O-F7).
- Keine Zertifikatserzeugung im Code (Stdlib kann keine Zertifikate erzeugen); die Howto dokumentiert `openssl`-Befehle.
- Kein eigenständiger Client-Daemon ohne Admin-Server (O-F4).
- Keine Änderung an `GET /api/config/<key>` der Admin-UI (bleibt unredigiert; die neue Redaction ist dafür wiederverwendbar, die Umstellung ist ein eigenes Issue).
- Kein Split von `scripts/admin-server.py` (Backlog `docs/plans/admin-server-split-backlog.md`, STATUS: open); F1 fügt dort nur einen Hook von ≤ 25 Zeilen ein.
- Keine neuen Abhängigkeiten.

## Entscheidungsregister

Bindende Nutzerentscheidungen (nicht überstimmbar):

| Nr. | Entscheidung | Konsequenz in dieser Spec |
|---|---|---|
| D1 | Scope: alle 4 Phasen, zwei Pläne F1/F2. | Strukturentscheidung; Phasen-Abschnitt; Trace-Anker gruppiert nach F1/F2. |
| D2 | Alt-Spec revidieren, nicht neu erfinden; Drift-Tabelle Alt-Spec → realer Code. | Abschnitt „Drift-/Korrekturtabelle"; übernommene Antworten Q1, Q2, Q4, Q6a bleiben gültig. Alt-Spec Q6 (Z. 32) wird geteilt: **Q6a** „Registry als Klartext-JSON ohne Secrets" übernommen; **Q6b** „Token-Kette `--fleet-token` > env > `project.yaml` > file" ist eine Nutzerantwort und wird durch A4/K1 ersetzt — Bestätigung des Overrides offen (O-F9). |
| D3 | Push/Phone-Home (Instanz verbindet ausgehend); TLS Pflicht für Nicht-Localhost, fail closed. | IC-11, IC-12; AC-2, AC-3, AC-5. |
| D4 | Enrollment: Server stellt pro Instanz Token via `fleet-server.py issue-token` aus; Zertifikats-Fingerprint wird beim Enrollment übergeben (Pinning); Widerruf server- UND instanzseitig; Token rotierbar. | IC-10 (vollständiger Ablauf + Zustandsmaschine); AC-7 bis AC-14. |
| D5 | Registry = JSON-Datei (Metadaten, `token_hash`, `last_heartbeat`; kein Config-/Log-Inhalt, keine Klartext-Token); `sqlite3` erst später für History. | IC-8; AC-25. |
| D6 | Status-Payload: Version, letzter Sync, Health, Liste aktiver Provider aus `ai-providers` (config-key-getrieben, kein `if provider == "Name"`); Doctor-/Context-Report-Daten nicht jetzt. | IC-7 `fleet-status-v1`; AC-15, AC-16; Nicht-Ziel #977. |
| D7 | Redaction: Allowlist für Config, Pattern-Redaction für Logs, beides instanzseitig vor der Übertragung; neue Funktion/neues Modul. | IC-3 `scripts/lib/redaction.py`; AC-19, AC-20, AC-33 bis AC-35. |
| D8 | Tests optional (DoD `rapid-prototyping`): Tests sind separate, klar markierte Tasks pro Komponente, kein Merge-Gate. Security-Pfad-Tests sind „empfohlen (Security)". | Abschnitt „Tests"; Risiko R-8. |

Architekturentscheidungen dieser Spec (Format gemäß Konzept-Architekt-Vorgabe; ADR-Ablage folgt der bestehenden ADR-Konvention, Skill `se-cascade-adr-standard`, nicht einem Parallelformat):

```
DECISION A1 — Ort des Instanz-Clients
context: Der Client braucht Lesezugriff auf Repo-Dateien und (F2) SyncExecutor/ConfigManager aus admin-server.py.
choice: Neues lib-Modul scripts/lib/fleet_client.py; admin-server.py startet es nur (Hook in AdminServer.__init__/start), F2-Write-Handler werden als Callables injiziert.
alternatives: Code in admin-server.py (5946 Z., Split-Backlog, Konflikt mit Netzplan) abgelehnt; eigener Client-Daemon abgelehnt (zweiter Prozess, PID-/Lifecycle-Verwaltung, O-F4).
consequences: lib-Modul ist ohne admin-server.py testbar; admin-server.py wächst um ≤ 25 Zeilen; Fleet ist nur aktiv, solange der Admin-Server läuft.
```

```
DECISION A2 — Instanzseitiges Lesen direkt statt Relay über /api/*
context: Die Alt-Spec wollte Kommandos an bestehende /api/*-Handler dispatchen; für Logs existiert keiner, Config-GET ist unredigiert.
choice: fleet_client liest Status/Config/Logs direkt (lib.config.load_config, .meta-viz/sync-status.json, Log-Dateien) und redigiert vor dem Senden.
alternatives: Loopback-HTTP-Aufruf der eigenen Admin-API abgelehnt (bräuchte Admin-Token im Client, liefert unredigierte Daten, kein Log-Endpunkt).
consequences: Kein neuer Admin-Endpunkt; Redaction an genau einer Stelle; Lese-Code ist klein und lokal.
```

```
DECISION A3 — Transport: Long-Poll statt SSE (siehe O-F1)
context: Alt-Spec Q5 wählte „SSE + HTTP-Long-Poll"; im Repo gibt es keinen SSE-Client-Code, nur Server->Browser-SSE (/api/events).
choice: Ausschließlich HTTP-Long-Poll (GET /v1/poll, Haltezeit 25 s) plus separate Heartbeat-POSTs; Dashboard pollt /api/instances alle 5 s.
alternatives: SSE zur Instanz abgelehnt (eigener Stream-Parser + Reconnect-Logik im Client, offener Stream ohne natürliches Ende erschwert Timeouts, Proxy-Puffering/Idle-Timeouts brechen Streams); WebSocket abgelehnt (kein Stdlib-Support). Thread-Bindung ist kein Unterscheidungsmerkmal: auch ein Long-Poll belegt je Instanz dauerhaft einen Handler-Thread (Kapazität siehe IC-11).
consequences: Jede Anfrage ist eine abgeschlossene HTTP-Transaktion (einfache Timeouts, Proxy-freundlich); Latenz eines Kommandos ≤ 25 s Haltezeit, typischerweise sofort.
```

```
DECISION A4 — Token-Auflösung im Client
context: _resolve_admin_token in admin-server.py ist parametrisierbar, aber aus lib/ nicht importierbar (Dateiname mit Bindestrich).
choice: Eigene kleine Funktion fleet_protocol.resolve_secret(env_var, token_file) (Env > Datei); kein Inline-Token-Key, kein CLI-Token-Flag.
alternatives: _resolve_admin_token nach lib/ verschieben abgelehnt (zusätzliche Änderungen in admin-server.py, Überlappung mit Netzplan); Inline-Key fleet.token abgelehnt (Klartext-Secret in versionierter Config).
consequences: Token gelangt nie in argv oder project.yaml; zwei ähnliche Resolver existieren nebeneinander (Konsolidierung beim admin-server-Split). Ein Env-Token wird beim Start des Admin-Servers bedingungslos (auch ohne aktiven Fleet-Block) einmal gelesen und aus os.environ entfernt, damit Kindprozesse des Admin-Servers (SyncExecutor -> sync.py) ihn nicht erben (IC-4, AC-47); empfohlen bleibt die Token-Datei.
```

```
DECISION A5 — Token-Speicherung und -Vergleich
context: Registry darf keine Klartext-Token enthalten (D5); Vergleich muss constant-time sein.
choice: Token = "amf_" + secrets.token_urlsafe(32); Registry speichert "sha256:" + sha256(token).hexdigest(); Vergleich der Hash-Strings per hmac.compare_digest über alle Einträge.
alternatives: Salted KDF (pbkdf2) abgelehnt — 256-Bit-Zufallstoken machen Wörterbuchangriffe gegenstandslos, KDF kostet pro Request CPU; Klartext-Vergleich abgelehnt (D5).
consequences: Präfix amf_ ist für Secret-Scanner und Log-Redaction erkennbar; Registry-Leak gibt keine nutzbaren Token preis.
```

```
DECISION A6 — Registry-Ort außerhalb des Repos
context: Server-State unter ~/.agent-meta-fleet/ vs. Repo-Containment (Schreiben nur Repo-Root + .tmp/).
choice: Default --state-dir ~/.agent-meta-fleet (Verzeichnis 0700, Dateien 0600); Flag --state-dir für Tests und Agent-Läufe (.tmp/fleet-*).
alternatives: State im Repo abgelehnt (Fleet-Server ist repo-übergreifend und läuft ggf. auf einem Host ohne agent-meta-Projekt); XDG-Pfad abgelehnt (kein Präzedenzfall im Repo).
consequences: Repo-Containment (.claude/hooks/repo-containment-impl.sh) prüft nur Agent-Tool-Calls Write/Edit/Bash, nicht Schreibzugriffe eines vom Nutzer gestarteten Serverprozesses; Agenten starten den Server nur mit --state-dir .tmp/... .
```

```
DECISION A7 — Gesonderte Modulgrenzen fleet_protocol / redaction
context: Server und Client teilen Wire-Schemas, Token-Hashing, Audit; Redaction ist fachlich allgemein.
choice: scripts/lib/fleet_protocol.py (Wire-Vertrag + geteilte Sicherheitsprimitive + Audit-Writer), scripts/lib/redaction.py (allgemein, ohne Fleet-Bezug).
alternatives: Alles in fleet_client.py abgelehnt (Server müsste Client-Modul importieren, > 600 Z.); separates fleet_audit.py abgelehnt (≤ 60 Z., gleicher Konsument-Kreis wie protocol).
consequences: redaction.py ist später für die Admin-UI-Config-Ansicht wiederverwendbar; Server importiert nur protocol (kein PyYAML nötig).
```

```
DECISION A8 — Fingerprint-Pinning statt CA-Vertrauen
context: Fleet-Server laufen typischerweise mit selbstsignierten Zertifikaten; Alt-Spec fordert Mutual Identity Check.
choice: Client prüft nach jedem connect() den SHA-256-Fingerprint des DER-Leaf-Zertifikats gegen fleet.cert-fingerprint (String oder Liste mit ≤ 2 Einträgen für Zertifikatswechsel); CA-Kette wird nicht ausgewertet.
alternatives: System-CA-Store abgelehnt (selbstsigniert scheitert; CA-signiert schützt nicht gegen falsch ausgestellte Zertifikate); Pinning nur beim Enrollment abgelehnt (MITM nach Enrollment).
consequences: Zertifikatswechsel erfordert Fingerprint-Verteilung (zweiter Listeneintrag erlaubt überlappenden Wechsel); Reverse-Proxy-Terminierung ist möglich (Proxy-Fingerprint pinnen, fleet-server bindet dann loopback).
```

## Drift-/Korrekturtabelle (Alt-Spec → realer Code)

| # | Aussage der Alt-Spec | Realer Code (VERIFIED) | Korrektur in dieser Spec |
|---|---|---|---|
| K1 | Token-Kette „wie admin-server.py (`--fleet-token` > env > project.yaml > file)"; Admin-Flag implizit `--token` | Admin-Flag heißt `--admin-token` (`main()`), Kette in `_resolve_admin_token(cli_token, config_token, config_token_file, env_var_name="ADMIN_UI_TOKEN")`: CLI > env > config > file | Kein CLI-Token-Flag und kein Inline-Key für Fleet; nur Env > Token-Datei (A4; ersetzt Alt-Spec Q6b, Bestätigung O-F9). Token nie in argv (Netzplan Task 896-3: `_admin_start_detached` reicht `--admin-token` heute per argv weiter). |
| K2 | „reuse that existing redaction function" | `grep -inE 'redact\|mask\|sanitiz' scripts/admin-server.py` → 0 Treffer; Config-GET unredigiert | Neues Modul `scripts/lib/redaction.py` (IC-3, D7). |
| K3 | `get-logs` dispatcht auf existierende `/api/*`-Handler | Kein Log-Endpunkt; `sync.log` im Projekt-Root (`scripts/lib/cli_commands.py: LOGFILE = "sync.log"`), `.meta-viz/admin-server.log` (`ADMIN_LOG_FILE`, nur bei detached `start`) | Neuer Log-Tail-Code in `fleet_client` mit fester Quellen-Allowlist (IC-4). |
| K4 | Instanz-Audit über „`.claude/hooks/.guard-audit.log`'s sibling convention" | `.guard-audit.log` ist Hook-/Claude-spezifisch und loggt Git-Elevation von Agenten; `AuditService` ist kein Audit-Log | Provider-neutrale Audit-Logs `.meta-viz/fleet-audit.log` (Instanz) und `<state-dir>/audit.log` (Server), IC-9. |
| K5 | TLS „enforced at startup" (implizit vorhandene Technik) | Kein TLS-Code im Repo; Admin-UI plain HTTP, HTTPS im Netzplan Nicht-Ziel (Q9) | TLS + Pinning sind Neuland und vollständig spezifiziert (IC-12). |
| K6 | Registry analog zu `.claude/agent-meta-state.json` | Diese Datei ist Provider-Isolation-State (`scripts/lib/isolation.py`), kein Sync-Zeitstempel | Analogie gestrichen; Registry eigenständig (IC-8). |
| K7 | Last-Sync-Zeitstempel ohne Quelle | `SyncExecutor.STATUS_FILE = .meta-viz/sync-status.json` (`last_run_timestamp`, `last_run_exit_code`, `last_run_summary`); wird nur bei Admin-Server-Syncs geschrieben | Quelle `.meta-viz/sync-status.json`, Fallback `sync.log`-mtime (IC-4, R-6). |
| K8 | Versionsbeispiel `0.101.0` | `VERSION` = `2.0.0-beta.2`; `agent-meta-version` in `project.yaml` | Beispiele mit `2.0.0-beta.2`. |
| K9 | Transport „(c) SSE + HTTP long-poll" | SSE existiert nur Server→Browser für Config-Events (`/api/events`, `SSE_HEARTBEAT_SECONDS = 15`); kein SSE-Client-Code | Long-Poll only (A3, O-F1). |
| K10 | Endpunkte `/register`, `/events/<session_id>`, `/result/<session_id>`, `/heartbeat/<session_id>` | Existieren nicht (NEU) | Versionierte `/v1/*`-API; Identität ausschließlich aus dem Bearer-Token, keine Session-ID in der URL (IC-7). |
| K11 | Instanz erzeugt eigenes Token „oder" Admin stellt es aus | — | Server stellt aus (D4), `issue-token`. |
| K12 | Offline-TTL „z. B. 90 s" | — | Schwellen online/stale/offline relativ zum Heartbeat-Intervall (IC-11). |
| K13 | Fleet-Client als Erweiterung von `admin-server.py` mit Flags `--fleet-url`/`--fleet-token` | `admin-server.py` 5946 Z., Split-Backlog offen; Netzplan ändert `AdminServer.__init__`, `_admin_start_detached`, `main()` | Client in `scripts/lib/fleet_client.py`, Konfiguration nur über `fleet.*` in `project.yaml`, keine neuen Admin-CLI-Flags (A1). |
| K14 | Phase 3+4 komplett out of scope | Nutzerentscheidung D1 | Phase 3+4 hier spezifiziert, Umsetzung erst in F2. |
| K15 | Quelle `docs/superpowers/specs/admin-ui-concept.md` §12 | Datei existiert nicht; real `docs/concepts/planned/admin-ui-concept.md:885` | Korrigiert im Kopf. |
| K16 | Keine Abgrenzung zu #877/#977 | #877 = Subplattform-Schicht, #977 = Context-Profiles-Tracking | Nicht-Ziele. |
| K17 | Spec im Legacy-Pfad ohne Template | Aktive Pfade `docs/specs`, `docs/plans` (`project.yaml` → `spec-plan-workflow.paths`) | Diese Datei; Alt-Datei bleibt mit Hinweis-Header. |

Übernommen aus der Alt-Spec (weiter gültig): Q1 Hosting im agent-meta-Repo, Q2 keine CI-Runner, Q4 ein Fleet-Admin-Token, Q6a Registry als Klartext-JSON ohne Secrets, Dashboard als Zero-Dependency-Single-File, „Read-only ist strukturell" (F1 enthält keinen Write-Handler).

Nicht übernommen: Q5 (SSE + Long-Poll, ersetzt durch A3, O-F1) und Q6b (Token-Kette, ersetzt durch A4/K1, O-F9). Beide sind Nutzerantworten; der Override gilt erst nach Bestätigung bzw. mit akzeptiertem Default.

## Architektur (Komponentenkarte)

| ID | Komponente | Datei | Verantwortung (genau eine) | Status |
|---|---|---|---|---|
| C1 | Fleet-Server | `scripts/fleet-server.py` | HTTP(S)-Endpunkte, Registry, Kommando-Vermittlung, Enrollment-CLI | NEU |
| C2 | Protokoll | `scripts/lib/fleet_protocol.py` | Wire-Konstanten/-Schemas, Token-Hashing/-Vergleich, Secret-Auflösung, Audit-Writer | NEU |
| C3 | Redaction | `scripts/lib/redaction.py` | Allowlist-Redaction für Config, Pattern-Redaction für Text | NEU |
| C4 | Fleet-Client | `scripts/lib/fleet_client.py` | Settings laden/validieren, TLS-Pinning-Verbindung, Heartbeat, Poll, Lese-Handler, Ack | NEU |
| C5 | Admin-Hook | `scripts/admin-server.py` (`AdminServer.__init__`, `AdminServer.start`) | Client starten/stoppen; ab F2 Write-Handler injizieren | geändert (≤ 25 Z. in F1) |
| C6 | Dashboard | `docs/ui/fleet-ui.html` | Instanzliste, Detail, Log-/Config-Ansicht, ab F2 Bestätigungsdialog | NEU |
| C7 | Schema/Szenario/Checks | `config/project-config.schema.json`, `tests/scenarios/registry.md` + `tests/scenarios/configs/79-fleet-config-opt-in.project.yaml`, `scripts/lib/consistency/python_compat.py` (`_SCAN_FILES`) | Deklaration `fleet`-Block, Sync-Akzeptanz, 3.9-Check deckt `fleet-server.py` ab | geändert/NEU |
| C8 | Doku | `docs/howto/fleet-server.md`, `docs/api/fleet-api-reference.md`, `docs/howto/admin-ui-remote-access.md` (Querverweis), Hinweis-Header Alt-Spec | Betrieb, API-Referenz | NEU/geändert |

Begründung der Grenzen: Server (C1) und Client (C4) laufen auf verschiedenen Hosts und teilen nur den Vertrag (C2) — daher drei statt einer Datei. Redaction (C3) hat keinen Fleet-Bezug und wird separat gehalten, damit sie ohne Netzwerkcode testbar und später wiederverwendbar ist. Mehr Komponenten (eigener Audit-, Registry-, TLS-Modul) wurden abgelehnt: jedes wäre < 100 Zeilen mit genau einem Konsumenten.

Größen-Obergrenzen: `fleet_client.py` ≤ 600 Z. (lib-Konvention), `fleet_protocol.py` ≤ 350 Z., `redaction.py` ≤ 250 Z., `fleet-server.py` ≤ 900 Z.

## Interface Contracts

### IC-1 Config-Keys `fleet.*` (Instanz, `.meta-config/project.yaml`)

| Key | Typ | Default | Regel |
|---|---|---|---|
| `fleet.enabled` | bool | `false` | Opt-in. `false` oder Block fehlt → Client wird nicht erzeugt. |
| `fleet.url` | string | — (Pflicht bei `enabled`) | `https://host:port` oder `http://` nur bei Loopback-Host (`127.0.0.1`, `localhost`, `::1`). Pfad/Query/Fragment verboten. |
| `fleet.token-file` | string | — (Pflicht, sofern Env `AGENT_META_FLEET_TOKEN` fehlt) | Relativ zum Projekt-Root oder absolut, `~` wird expandiert. POSIX: Datei darf keine Group-/Other-Bits haben, sonst fail closed (Windows: O-F8). |
| `fleet.cert-fingerprint` | string oder Liste (1-2 Strings) | — (Pflicht bei `https`) | Format `sha256:` + 64 Hex; Groß-/Kleinschreibung und `:`-Trenner werden normalisiert (kompatibel zu `openssl x509 -noout -fingerprint -sha256`). |
| `fleet.allow-remote-write` | bool | `false` | Instanzseitiges, autoritatives Gate für Phase 3+4. |
| `fleet.heartbeat-interval` | int (Sekunden) | `30` | Bereich 10-300; außerhalb → Client startet nicht (Fehlermeldung). |

Kein Key `fleet.token` (A4). Unbekannte Keys unter `fleet` → Warnung auf stderr, kein Abbruch.

Schema-Ergänzung in `config/project-config.schema.json` (Top-Level-Property `fleet`, draft-07, analog `admin-ui`):

```json
"fleet": {
  "type": "object",
  "description": "Fleet client (opt-in). Connects this instance outbound to a self-hosted scripts/fleet-server.py. Read-only unless allow-remote-write is true.",
  "additionalProperties": false,
  "properties": {
    "enabled": {"type": "boolean", "default": false},
    "url": {"type": "string", "pattern": "^https?://[^/?#]+$"},
    "token-file": {"type": "string", "description": "Path to the per-instance token file issued by 'fleet-server.py issue-token'. Must be chmod 600. NEVER commit to version control."},
    "cert-fingerprint": {
      "oneOf": [
        {"type": "string", "pattern": "^[Ss][Hh][Aa]256:[0-9A-Fa-f:]{64,95}$"},
        {"type": "array", "minItems": 1, "maxItems": 2, "items": {"type": "string", "pattern": "^[Ss][Hh][Aa]256:[0-9A-Fa-f:]{64,95}$"}}
      ]
    },
    "allow-remote-write": {"type": "boolean", "default": false},
    "heartbeat-interval": {"type": "integer", "default": 30, "minimum": 10, "maximum": 300}
  }
}
```

Die normative Prüfung (exakt 64 Hex nach Entfernen der `:`) erfolgt im Client (`load_fleet_settings`); das Schema-`pattern` ist nur eine Grobprüfung.

Szenario `79-fleet-config-opt-in` in `tests/scenarios/registry.md` (Konvention „jede neue Config-Option bekommt ein Szenario"): Config mit vollständigem `fleet`-Block (`enabled: true`, Loopback-URL, Token-Datei-Pfad); Assertion: `sync.py`-Dry-Run, Sync und `--validate` laufen ohne Fehler, der generierte Baum enthält keine Fleet-spezifische Datei (sync.py konsumiert `fleet.*` nicht).

### IC-2 `scripts/lib/fleet_protocol.py`

```python
from __future__ import annotations

PROTOCOL_VERSION: str = "v1"
TOKEN_PREFIX: str = "amf_"
DEFAULT_PORT: int = 7430
ENV_INSTANCE_TOKEN: str = "AGENT_META_FLEET_TOKEN"
ENV_ADMIN_TOKEN: str = "AGENT_META_FLEET_ADMIN_TOKEN"
LOOPBACK_HOSTS: tuple[str, ...] = ("127.0.0.1", "localhost", "::1")
READ_COMMANDS: frozenset[str] = frozenset({"get-logs", "get-config"})
WRITE_COMMANDS: frozenset[str] = frozenset({"trigger-sync", "put-config"})

class FleetProtocolError(ValueError):
    code: str  # Fehlercode aus IC-7-Tabelle

def new_token() -> str: ...                      # TOKEN_PREFIX + secrets.token_urlsafe(32)
def hash_token(token: str) -> str: ...           # "sha256:" + hashlib.sha256(token.encode()).hexdigest()
def token_matches(token: str, token_hash: str) -> bool: ...  # hmac.compare_digest(hash_token(token), token_hash); leere Werte -> False
def normalize_fingerprint(value: str) -> str: ...  # -> "sha256:<64 lowercase hex>"; FleetProtocolError("invalid_fingerprint")
def cert_fingerprint(der: bytes) -> str: ...     # "sha256:" + sha256(der).hexdigest()
def is_loopback(host: str) -> bool: ...
def resolve_secret(env_var: str, token_file: Path | None) -> str | None: ...
    # Env > Datei; Datei: fd = os.open(path, os.O_RDONLY), os.fstat(fd) auf demselben fd
    # (POSIX-Modus-Prüfung: group/other -> FleetProtocolError("insecure_token_file")), dann
    # Lesen über denselben fd, strip(). Kein stat-then-open (TOCTOU).
def create_private_file(path: Path) -> int: ...
    # os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600) -> fd; Modus gilt ab Erzeugung,
    # kein chmod-Fenster. Genutzt für Registry-Temp-Datei, admin.token, --out-Token-Dateien,
    # Audit-Rotations-Temp-Datei und STATE_FILE-Temp-Datei.
def private_temp_path(target: Path) -> Path: ...
    # target.parent / f".{target.name}.{secrets.token_hex(8)}.tmp" — eindeutiger Temp-Name je
    # Schreibvorgang, damit O_EXCL nach einem Absturz (liegengebliebene Temp-Datei) nicht dauerhaft
    # fehlschlägt. Alle atomaren Schreibvorgänge: fd = create_private_file(private_temp_path(t)),
    # schreiben, os.fsync, os.replace(tmp, t); bei Fehler tmp per os.unlink entfernen (best effort).
def cleanup_private_temps(directory: Path, names: Sequence[str]) -> int: ...
    # Entfernt beim Start liegengebliebene Dateien ".<name>.<16 hex>.tmp" für die übergebenen
    # Zielnamen (Server: registry.json, audit.log; Instanz: fleet-state.json, fleet-audit.log);
    # nur exakter Regex-Treffer, keine Wildcards darüber hinaus; liefert die Anzahl.
def validate_payload(schema: str, obj: object) -> list[str]: ...
    # Stdlib-Typprüfer für die Schemas aus IC-7 (required, type, maxLength, enum, maxItems); leere Liste = gültig
def utc_now_iso() -> str: ...                    # "2026-10-23T12:00:00Z"

class AuditLog:
    def __init__(self, path: Path, side: str) -> None: ...   # side in {"server", "instance"}
    def append(self, event: str, *, outcome: str, instance_id: str | None = None,
               command_id: str | None = None, command: str | None = None,
               actor: str | None = None, detail: str = "") -> None: ...
```

`AuditLog` öffnet die Datei mit `os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)` (Modus bereits bei Erzeugung), danach `os.fchmod(fd, 0o600)` auf demselben fd für bereits existierende Dateien.

`AuditLog.aggregate(event: str, source_ip: str) -> None` (zusätzliche Methode): zählt `auth_failed`- und `tls_refused`-Ereignisse und schreibt je Ereignistyp höchstens eine Zeile pro Minute mit `detail = "count=<N> ips=<bis zu 5 Quell-IPs, häufigste zuerst>"` (IC-9).

Fehlerpfade: `AuditLog.append` wirft nie (Logging best effort, analog `hook_audit_log_append`); schlägt das Schreiben fehl, wird einmalig auf stderr gewarnt.

### IC-3 `scripts/lib/redaction.py`

Beweis „keine bestehende Funktion" (VERIFIED, `grep -rniE 'redact|mask|secret|sanitiz' scripts/`):

| Fundstelle | Warum nicht wiederverwendbar |
|---|---|
| `scripts/lib/secrets.py::scan_for_secrets(content, config=None)` | Nur Detektion (Warnliste), keine Maskierung. |
| `scripts/lib/env.py::_mask(value)` | Privat, maskiert einen Einzelwert (erste/letzte 4 Zeichen) — lässt Teile des Secrets stehen. |
| `scripts/lib/meta_optimizer.py::_redacted_config_text(config_text, config, credentials)`, `_redact_hunks` | Privat, Denylist an die Credentials-Liste des Optimizers gebunden. |
| `scripts/lib/mcp_provider_config.py::_contains_literal_secret(value, config)` | Prädikat, keine Redaction. |
| `hooks/1-generic/lib/hook_common.sh::hook_redact_secrets` | Shell mit Inline-Python, aus Python nur per Subprozess; Muster werden portiert. |

```python
from __future__ import annotations

REDACTED: str = "[REDACTED]"
CONFIG_VIEW_ALLOWLIST: tuple[str, ...] = (
    "agent-meta-version", "project.name", "project.prefix", "project.short",
    "ai-providers", "platforms", "roles", "dod-preset", "rules-preset",
    "conventions-preset", "tier-preset", "speech-mode", "provider-isolation",
    "max-parallel-agents", "spec-plan-workflow", "quality-pipelines", "auto_commit",
    "debug-mode", "admin-ui.enabled", "admin-ui.port", "admin-ui.bind-host",
    "fleet.enabled", "fleet.url", "fleet.cert-fingerprint",
    "fleet.allow-remote-write", "fleet.heartbeat-interval",
)
SECRET_KEY_RE: re.Pattern[str]   # (?i)(token|secret|password|passwd|pwd|api[_-]?key|apikey|credential|auth|private[_-]?key)
TEXT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...]
    # 1:1-Port der acht Muster aus hook_redact_secrets (URL-Basic-Auth, Authorization: Bearer,
    # bearer <token>, key=value, --token <v>, ghp_/gho_/ghs_/ghu_/ghr_/github_pat_, xox[baprs]-, AKIA…)
    # plus: r"\bamf_[A-Za-z0-9_\-]{20,}" -> "amf_***" und PEM-Blöcke
    # r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----" -> "[REDACTED PRIVATE KEY]"
    # Reihenfolge wie im Shell-Original (Bearer vor key=value).

def redact_text(text: str) -> str: ...
def redact_config(data: Mapping[str, Any],
                  allowlist: Sequence[str] = CONFIG_VIEW_ALLOWLIST) -> dict[str, Any]: ...
def contains_redaction_marker(value: Any) -> bool: ...   # rekursiv; True wenn REDACTED oder "***" aus TEXT_PATTERNS vorkommt
```

Regeln `redact_config` (Allowlist, D7):

1. Pfade sind punktgetrennte Mapping-Keys. Ein Wert bleibt sichtbar, wenn sein Pfad gleich einem Allowlist-Eintrag ist oder darunter liegt.
2. Ein Teilbaum ohne Allowlist-Treffer wird als Ganzes durch `REDACTED` ersetzt (Key sichtbar, keine Unter-Keys). Liegt ein Allowlist-Eintrag tiefer (z. B. `admin-ui.port`), bleibt der Eltern-Key ein Mapping, alle nicht gelisteten Geschwister werden `REDACTED`.
3. Backstop innerhalb sichtbarer Teilbäume: Keys, die `SECRET_KEY_RE` matchen, werden `REDACTED`; alle String-Werte laufen durch `redact_text`.
4. Listen werden elementweise wie ihr Eltern-Pfad behandelt.
5. Eingabe wird nicht verändert (Deep-Copy-Ergebnis). Nicht-Mapping-Eingabe → `{}`.
6. `.meta-config/secrets.local.yaml` wird von keinem Fleet-Pfad gelesen.

### IC-4 `scripts/lib/fleet_client.py`

```python
from __future__ import annotations

@dataclass(frozen=True)
class FleetSettings:
    url: str                       # normalisiert, ohne Slash am Ende
    host: str
    port: int
    use_tls: bool
    token_file: Path | None
    fingerprints: tuple[str, ...]  # normalisiert; leer nur bei Loopback-http
    allow_remote_write: bool
    heartbeat_interval: int

class FleetConfigError(ValueError): ...   # Code-Attribut: tls_required | fingerprint_required | invalid_url | invalid_interval | token_missing | insecure_token_file

def load_fleet_settings(root: Path) -> FleetSettings | None: ...
    # None wenn Block fehlt oder enabled != true; FleetConfigError bei ungültiger Config (fail closed)

WriteHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]

class FleetClient:
    def __init__(self, root: Path, settings: FleetSettings, *,
                 env_token: str | None = None,
                 write_handlers: Mapping[str, WriteHandler] | None = None,
                 audit: AuditLog | None = None) -> None: ...
        # env_token: bereits aus os.environ entfernter Wert (IC-5); der Client liest os.environ nie
    def start(self) -> None: ...       # startet Daemon-Threads "fleet-heartbeat", "fleet-poll" und (nur wenn write_handlers nicht leer, F2) "fleet-write"; idempotent
    def stop(self, *, deregister: bool = False) -> None: ...
    def build_status(self) -> dict[str, Any]: ...   # Payload fleet-status-v1 (IC-7)
    def handle_command(self, command: Mapping[str, Any]) -> dict[str, Any]: ...  # liefert Ack-Body

def read_last_sync(root: Path) -> dict[str, Any] | None: ...
def tail_log(root: Path, source: str, lines: int) -> list[str]: ...
def apply_config_ops(current: Mapping[str, Any], ops: Sequence[Mapping[str, Any]],
                     allowlist: Sequence[str]) -> dict[str, Any]: ...   # F2, rein funktional
LOG_SOURCES: Mapping[str, str] = {"sync": "sync.log", "admin-server": ".meta-viz/admin-server.log"}
REMOTE_WRITE_ALLOWLIST: tuple[str, ...]   # F2, Inhalt siehe IC-15 / O-F3
STATE_FILE: str = ".meta-viz/fleet-state.json"
AUDIT_FILE: str = ".meta-viz/fleet-audit.log"
```

Verhalten:

- **Verbindung:** `http.client.HTTPSConnection(host, port, context=ctx, timeout=35)` bzw. `HTTPConnection` bei Loopback-http. `ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)`, `ctx.minimum_version = ssl.TLSVersion.TLSv1_2`, `ctx.check_hostname = False`, `ctx.verify_mode = ssl.CERT_NONE` (Vertrauen ausschließlich über Pinning, A8). Nach `conn.connect()` und **vor** dem Senden jeglicher Request-Bytes: `cert_fingerprint(conn.sock.getpeercert(binary_form=True))` gegen `settings.fingerprints` per `hmac.compare_digest`; kein Treffer → Socket schließen, Audit `pin_mismatch`, Backoff. Eine Verbindung pro Request (kein Keep-Alive), damit jede Verbindung gepinnt wird.
- **Token:** Die Env-Variable wird **nicht** im Client gelesen, sondern bedingungslos in `_maybe_create_fleet_client` (IC-5) per `os.environ.pop("AGENT_META_FLEET_TOKEN", None)` entfernt — als erste Anweisung, vor Import, `load_fleet_settings` und jeder Validierung, also auch bei `fleet.enabled: false`, fehlendem Block, `FleetConfigError` oder ImportError. Der Wert wird als `env_token` an `FleetClient.__init__` übergeben und nur im Speicher gehalten. Damit erbt kein Kindprozess des Admin-Servers (u. a. `SyncExecutor._run` → `subprocess.run` ohne `env=`, VERIFIED) den Token (AC-47). Ohne Env-Token: vor jedem Request `resolve_secret(ENV_INSTANCE_TOKEN, token_file)`; die Datei wird bei geänderter mtime neu gelesen. Howto empfiehlt die Token-Datei. Token nur im Header `Authorization: Bearer <token>`, nie in URL/Query.
- **Heartbeat-Thread:** alle `heartbeat_interval` s: `project.yaml` neu laden (`lib.config.load_config`), `fleet.enabled`/`allow-remote-write` neu auswerten (Laufzeit-Rollback ohne Neustart), dann `POST /v1/heartbeat`. Erster Zyklus: `POST /v1/enroll`.
- **Poll-Thread:** Schleife `GET /v1/poll?wait=25`. Read-Kommandos (`READ_COMMANDS`, kurz und begrenzt) führt der Poll-Thread selbst über `handle_command` aus und beantwortet sie per `POST /v1/ack`. Write-Kommandos führt er **nie** selbst aus.
- **Write-Worker (F2):** genau ein Daemon-Thread `fleet-write` mit Busy-Gate `self._write_gate = threading.Semaphore(1)` und Übergabe-Queue `queue.Queue(maxsize=1)`. Eine Queue allein reicht nicht: sobald der Worker das Kommando per `get()` entnommen hat, ist der Slot wieder frei, obwohl der Write noch läuft. Ablauf: der Poll-Thread prüft das Gate (`allow_remote_write`, frisch geladen) und ruft `self._write_gate.acquire(blocking=False)`. `False` (ein Write läuft, z. B. `trigger-sync` bis 300 s, oder wartet auf sein Terminal-Ack) → sofort Ack `rejected/busy`, keine Einreihung. `True` → `put_nowait` (kann nicht voll sein, weil nur der Gate-Inhaber einreiht) und sofort Ack `accepted`. **Ack-Regel:** `rejected` gibt es nur vor `accepted` (Poll-Thread: Gate, Dedupe, Arg-Prüfungen); nach `accepted` sendet ausschließlich der Worker genau ein Terminal-Ack `ok|error` — jede im Handler erkannte Ablehnung (u. a. belegtes `SyncExecutor`-Gate → `error.code: busy`, IC-14; dateiabhängige `put-config`-Prüfungen, IC-15) wird zu `error` mit dem jeweiligen Code. Der Worker führt den Handler aus, sendet das Terminal-Ack `ok|error` und gibt das Gate **erst danach** im `finally` per `release()` frei (auch bei Exception im Handler oder Fehler beim Ack-Versand). Damit pollt die Instanz während eines laufenden Writes weiter, und ein zweites Write-Kommando erhält deterministisch `busy` (IC-14, AC-39, AC-52).
- **Zustellsemantik: at-most-once.** Der Server liefert jedes Kommando höchstens einmal aus (Zustand `delivered` beim Schreiben der Poll-Antwort, kein Redelivery; geht die Antwort verloren, endet das Kommando serverseitig: `delivered` ohne Ack nach 60 s → `expired`; `accepted` ohne Terminal-Ack nach 330 s → `error` mit `error.code = "command_timeout"`, IC-11). Instanzseitig: Write-Kommandos werden per `command_id` gegen eine begrenzte LRU (`collections.OrderedDict`, 256 Einträge, nur im Speicher) dedupliziert; Duplikat → `rejected/duplicate_command`, keine Ausführung. `expires_at` wertet ausschließlich der Server aus (er stellt abgelaufene Kommandos nicht mehr zu); die Instanz nutzt ihre lokale Uhr dafür nie (keine Ablehnung wegen Clock-Skew).
- **Lese-Handler:** `get-logs` (`args.source` ∈ `LOG_SOURCES`, `args.lines` 1-200, Default 100; liest höchstens die letzten 64 KiB per `seek`, Zeilen > 2000 Zeichen werden gekürzt, jede Zeile durch `redact_text`); `get-config` (`args.key == "project"` einziger zulässiger Wert; `redact_config(load_config(...))`).
- **Status:** `build_status()` liest `agent-meta-version` (Fallback `.agent-meta/VERSION`, dann `VERSION`, dann `"unknown"` — gleiche Reihenfolge wie `AdminServer._read_version`), `project.name`/`project.prefix`, `ai-providers` (Liste unverändert übernommen, keine Namensverzweigung), `read_last_sync`, Health (IC-7).
- **`read_last_sync`:** `.meta-viz/sync-status.json` → `{"timestamp": <last_run_timestamp normalisiert>, "exit_code": last_run_exit_code, "summary": redact_text(last_run_summary or "")[:200], "source": "sync-status"}`. `SyncExecutor._record_run` schreibt `last_run_summary` als `None`, wenn keine SUMMARY-Zeile gefunden wurde, und `last_run_timestamp` per `datetime.isoformat()` mit `+00:00` und Mikrosekunden (VERIFIED); `None` wird daher zu `""`, der Zeitstempel wird geparst (`datetime.fromisoformat`), nach UTC konvertiert und im Format von `utc_now_iso()` (`YYYY-MM-DDTHH:MM:SSZ`) ausgegeben; nicht parsebar → Behandlung wie fehlende Datei; fehlt die Datei: `sync.log`-mtime → `{"timestamp": <mtime ISO>, "exit_code": null, "summary": "", "source": "sync-log-mtime"}`; beides fehlt → `None`.
- **Write-Kommandos:** nur wenn in `write_handlers` registriert (F1: leer → `rejected/unknown_command`, kein `fleet-write`-Thread); vor dem Einreihen `allow_remote_write` aus der frisch geladenen Config prüfen, sonst `rejected/remote_write_disabled`. Der Write-Handler wird ausschließlich im Thread `fleet-write` aufgerufen.
- **Fehlerpfade (Client fail closed, Admin-Server läuft weiter):**

| Situation | Reaktion |
|---|---|
| `FleetConfigError` beim Start | Meldung auf stderr, Audit `config_invalid`, kein Thread. |
| Netzwerkfehler, 5xx, 429, 503 `busy` | Exponentielles Backoff 5 s → 300 s (Faktor 2, ±20 % Jitter). |
| Pin-Mismatch | Kein Request-Byte gesendet; Audit `pin_mismatch`; Backoff. |
| 401 `invalid_token` | Audit `auth_failed` (instanzseitig einmal je Pause); Pause bis sich die mtime der Token-Datei ändert (Prüfung je Heartbeat-Intervall). Bei Env-Token (Prozessumgebung zur Laufzeit unveränderlich): Pause bis zum Neustart des Admin-Servers. |
| 403 `instance_revoked` / `enroll_expired` | `STATE_FILE` = `{"state": "revoked", "since": <ISO>, "reason": <code>}`; Client stoppt; Neustart nur, wenn Token-Datei-mtime > `since`. |
| `fleet.enabled` wird zur Laufzeit `false` | `POST /v1/deregister`, Audit `deregistered`, Client stoppt (instanzseitiger Widerruf). |

### IC-5 Hook in `scripts/admin-server.py`

- `AdminServer.__init__`: nach dem bestehenden Setup `self.fleet_client = _maybe_create_fleet_client(self.root)`; die neue Modulfunktion entfernt als **erste Anweisung bedingungslos** `env_token = os.environ.pop("AGENT_META_FLEET_TOKEN", None)` (String-Literal, weil der Import von `fleet_client` danach noch scheitern kann; Wert gleich `fleet_protocol.ENV_INSTANCE_TOKEN`), ruft dann `fleet_client.load_fleet_settings`, fängt `FleetConfigError` (stderr-Meldung, `None`) und liefert `FleetClient(root, settings, env_token=env_token)` oder `None`. In jedem Pfad ist die Variable danach aus `os.environ` entfernt. F2 übergibt `write_handlers={"trigger-sync": ..., "put-config": ...}` (IC-14, IC-15).
- `AdminServer.start`: vor `serve_forever()` `if self.fleet_client: self.fleet_client.start()`; Banner-Zeile `Fleet: enabled (<url>)`; im `finally`: `self.fleet_client.stop()`.
- **Nicht geändert:** `main()`, `_admin_start_detached` (keine neuen Flags → kein Token in argv), `AuthService`, Routing-Tabellen.
- Import über den bestehenden Mechanismus `_ensure_scripts_on_path(root)` + `from lib import fleet_client`; ImportError (z. B. fehlendes PyYAML) → Fleet deaktiviert mit stderr-Hinweis.
- Ordnungsnotiz Netzplan (`SPEC-897-896-ADMIN-UI-NETWORK-2026-10-07`, DRAFT): Dieser ändert `AdminServer.__init__`, `_admin_start_detached`, `main()`, `AuthService.check_origin`. Überlappung mit F1 nur in `AdminServer.__init__`/`start` (additive Zeilen am Ende bzw. vor `serve_forever`). Regel: wer zuerst gemergt wird, gewinnt; der andere rebased. Keine semantische Abhängigkeit (R-2).

### IC-6 CLI `scripts/fleet-server.py`

```
python3 scripts/fleet-server.py serve [--host 127.0.0.1] [--port 7430]
        [--tls-cert PATH --tls-key PATH] [--state-dir PATH]
        [--admin-token-file PATH] [--write-token-file PATH]
python3 scripts/fleet-server.py issue-token --name NAME --out PATH [--state-dir PATH]
        [--enroll-hours 24] [--tls-cert PATH]
python3 scripts/fleet-server.py rotate-token --instance ID --out PATH [--state-dir PATH]
        [--grace-hours 24 | --immediate]
python3 scripts/fleet-server.py revoke --instance ID [--state-dir PATH]
python3 scripts/fleet-server.py list [--state-dir PATH] [--json]
```

- Kein Flag nimmt einen Token-Wert entgegen. Token werden ausschließlich in `--out` geschrieben (`create_private_file`: Modus 0600 ab Erzeugung, `O_CREAT|O_EXCL`: existierende Datei → Exit 1) und nie auf stdout ausgegeben.
- Fleet-Admin-Token: `AGENT_META_FLEET_ADMIN_TOKEN` > `--admin-token-file` > `<state-dir>/admin.token` (gelesen über `resolve_secret`, fstat auf dem geöffneten fd); fehlt alles, erzeugt `serve` beim ersten Start `<state-dir>/admin.token` per `create_private_file` (0600 ab Erzeugung, kein chmod-Fenster) und gibt nur den Pfad aus.
- `list` gibt alle instanzgelieferten Strings (Name aus Status, Version, Provider, Health-Reasons) mit maskierten Steuerzeichen aus: jedes Zeichen der Unicode-Kategorie `Cc` (C0/C1 inkl. ESC, ohne Ausnahme) wird als `\xNN` bzw. `\uNNNN` dargestellt (keine ANSI-Injection ins Terminal); `--json` nutzt `json.dumps(ensure_ascii=True)`.
- `--write-token-file` (optional, F2): aktiviert die Re-Auth für Write-Kommandos (IC-15).
- `serve` mit `not is_loopback(host)` und fehlendem `--tls-cert`/`--tls-key` → Exit 2 mit Meldung `refusing to bind on non-loopback host without TLS (--tls-cert/--tls-key)`, bevor ein Socket gebunden wird. Mit TLS: Startbanner gibt den Fingerprint aus.
- `issue-token` mit `--tls-cert` gibt Fingerprint, Instance-ID, Enroll-Deadline und den Pfad der Token-Datei aus. Im Reverse-Proxy-Betrieb wird `--tls-cert` auf die Zertifikatsdatei des Proxys auf dessen Host gesetzt (der Fingerprint wird aus der Datei berechnet, nie über das Netz abgerufen, IC-12).
- `--state-dir` Default `~/.agent-meta-fleet`; wird mit 0700 angelegt. Exit-Codes: 0 ok, 1 Bedien-/Zustandsfehler, 2 Sicherheits-Refusal.

### IC-7 Wire-API (`/v1/*` Instanz, `/api/*` Dashboard)

Alle Antworten `application/json; charset=utf-8` (außer `/`), Header `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`. Fehlerform: `{"error": {"code": "<code>", "message": "<text>"}}`. Zeitstempel ISO-8601 UTC mit `Z`.

Authentisierung: `Authorization: Bearer <token>`; Instanz-Token gilt nur für `/v1/*`, Fleet-Admin-Token nur für `/api/*`. Vergleich: Instanz per `token_matches` über alle Registry-Einträge, Admin per `hmac.compare_digest`. Kein Query-Token (anders als Admin-UI-SSE). Fehlender/ungültiger Token → 401 + `WWW-Authenticate: Bearer`.

| Methode + Pfad | Auth | Request | Response |
|---|---|---|---|
| `POST /v1/enroll` | Instanz | `fleet-enroll-v1` | 200 `{"instance_id", "server_time", "heartbeat_interval", "protocol": "v1"}` |
| `POST /v1/heartbeat` | Instanz | `fleet-status-v1` | 200 `{"server_time", "liveness"}` |
| `GET /v1/poll?wait=N` | Instanz | — (N 0-25, Default 25) | 200 `{"commands": [fleet-command-v1, …]}` (≤ 4 je Antwort) oder 204 |
| `POST /v1/ack` | Instanz | `fleet-ack-v1` | 200 `{"ok": true}` |
| `POST /v1/deregister` | Instanz | `{"reason": string ≤ 200}` | 200 `{"state": "revoked"}` |
| `GET /` | öffentlich | — | `docs/ui/fleet-ui.html` + CSP (IC-13) |
| `GET /api/instances` | Admin | — | 200 `fleet-instances-v1` |
| `GET /api/instances/<id>` | Admin | — | 200 Einzeleintrag aus `fleet-instances-v1` |
| `POST /api/instances/<id>/commands` | Admin (+ F2-Gates) | `{"type", "args", "confirm_nonce"?}` | 200 Kommandozustand (terminal), 202 (`accepted`, Phase 3), 428 (F2 Bestätigung), Fehler |
| `GET /api/commands/<command_id>` | Admin | — | 200 Kommandozustand |

Schemas (Notation: JSON-Schema-Teilmenge, normativ umgesetzt durch `validate_payload`):

```json
{"$id": "fleet-enroll-v1", "type": "object", "required": ["name", "prefix", "agent_meta_version"],
 "properties": {"name": {"type": "string", "maxLength": 100},
                "prefix": {"type": "string", "maxLength": 20},
                "agent_meta_version": {"type": "string", "maxLength": 40}}}

{"$id": "fleet-status-v1", "type": "object",
 "required": ["schema", "name", "prefix", "agent_meta_version", "last_sync", "health", "providers", "allow_remote_write", "heartbeat_interval"],
 "properties": {
   "schema": {"enum": ["fleet-status-v1"]},
   "name": {"type": "string", "maxLength": 100},
   "prefix": {"type": "string", "maxLength": 20},
   "agent_meta_version": {"type": "string", "maxLength": 40},
   "last_sync": {"type": ["object", "null"], "required": ["timestamp", "exit_code", "summary", "source"],
                 "properties": {"timestamp": {"type": "string"}, "exit_code": {"type": ["integer", "null"]},
                                "summary": {"type": "string", "maxLength": 200},
                                "source": {"enum": ["sync-status", "sync-log-mtime"]}}},
   "health": {"type": "object", "required": ["state", "reasons"],
              "properties": {"state": {"enum": ["ok", "degraded", "error"]},
                             "reasons": {"type": "array", "maxItems": 10, "items": {"type": "string", "maxLength": 200}}}},
   "providers": {"type": "array", "maxItems": 32, "items": {"type": "string", "maxLength": 64}},
   "allow_remote_write": {"type": "boolean"},
   "heartbeat_interval": {"type": "integer", "minimum": 10, "maximum": 300}}}

{"$id": "fleet-command-v1", "type": "object", "required": ["command_id", "type", "args", "issued_at", "expires_at"],
 "properties": {"command_id": {"type": "string", "pattern": "^cmd_[0-9a-f]{16}$"},
                "type": {"enum": ["get-logs", "get-config", "trigger-sync", "put-config"]},
                "args": {"type": "object"}, "issued_at": {"type": "string"}, "expires_at": {"type": "string"}}}

{"$id": "fleet-ack-v1", "type": "object", "required": ["command_id", "status"],
 "properties": {"command_id": {"type": "string"},
                "status": {"enum": ["accepted", "ok", "error", "rejected"]},
                "result": {"type": ["object", "null"]},
                "error": {"type": ["object", "null"], "required": ["code", "message"]}}}

{"$id": "fleet-instances-v1", "type": "object", "required": ["schema", "server_time", "instances"],
 "properties": {"schema": {"enum": ["fleet-instances-v1"]}, "server_time": {"type": "string"},
   "instances": {"type": "array", "maxItems": 256, "items": {"type": "object",
     "required": ["instance_id", "name", "name_mismatch", "state", "liveness", "last_heartbeat", "status"],
     "properties": {"instance_id": {"type": "string"}, "name": {"type": "string"},
                    "name_mismatch": {"type": "boolean"},
                    "state": {"enum": ["issued", "active", "revoked", "expired"]},
                    "liveness": {"enum": ["online", "stale", "offline", "never"]},
                    "last_heartbeat": {"type": ["string", "null"]},
                    "status": {"type": ["object", "null"]}}}}}}
```

Health-Regel (instanzseitig): `error`, wenn `project.yaml` nicht ladbar ist oder `last_sync.exit_code` ≠ 0 und nicht `null`; `degraded`, wenn `last_sync` `null` ist oder `exit_code` `null`; sonst `ok`. `reasons` enthält kurze, redigierte Begründungen.

Kommando-Args: `get-logs` `{"source": "sync"|"admin-server", "lines": 1..200}`; `get-config` `{"key": "project"}`; `trigger-sync` `{"mode": "validate"|"run"}` (F2); `put-config` siehe IC-15 (F2).

Ack-Results: `get-logs` `{"source", "lines": [string]}` (≤ 64 KiB); `get-config` `{"key": "project", "config": <redigiertes Mapping>, "sha256": <sha256 der Datei auf Platte>}` (≤ 512 KiB); `trigger-sync` `{"exit_code", "tail": [≤ 50 redigierte Zeilen]}`; `put-config` `{"backup": string|null, "comments_lost": int}`.

Kommandozustand (Server, nur im Speicher): `{"command_id", "instance_id", "type", "state": "queued|delivered|accepted|ok|error|rejected|expired", "result", "error", "created_at", "updated_at"}`; zulässige Ack-Übergänge: `delivered` → `accepted|ok|error|rejected`, `accepted` → `ok|error` (IC-4 Ack-Regel); jedes andere Ack (z. B. `rejected` für ein `accepted`-Kommando, Ack auf Terminalzustand) → 400 `schema_invalid`, Zustand unverändert; aufbewahrt 10 min nach Terminalzustand, höchstens 1000 Einträge (älteste zuerst verworfen). Results werden weder in Registry noch Audit geschrieben.

Fehlercodes:

| Code | HTTP | Bedeutung |
|---|---|---|
| `invalid_token` | 401 | Token fehlt/unbekannt |
| `write_reauth_required` | 401 | F2: Write-Token fehlt/falsch |
| `instance_revoked` | 403 | Instanz widerrufen |
| `enroll_expired` | 403 | Enroll-Deadline überschritten |
| `write_disabled` | 403 | F2: Instanz meldet `allow_remote_write: false` |
| `unknown_route` | 404 | Pfad unbekannt |
| `not_enrolled` | 409 | Heartbeat/Poll vor Enroll |
| `instance_offline` | 409 | Kommando an `offline`/`never`-Instanz |
| `payload_too_large` | 413 | Body über Limit (IC-11) |
| `schema_invalid` | 400 | `validate_payload` meldet Fehler |
| `unknown_command` | 400 | Typ nicht in `READ_COMMANDS ∪ WRITE_COMMANDS` bzw. in F1 nicht freigeschaltet |
| `confirmation_required` | 428 | F2: Nonce fehlt/ungültig; Body enthält neuen `confirm_nonce` |
| `busy` (Hauptthread) | 503 | Globales Verbindungslimit (288) erreicht: Antwort nur unter Plain-HTTP vom Hauptthread; unter TLS wird ohne Antwort geschlossen (IC-11) |
| `busy` (Worker) | 503 | Nach erfolgreicher Authentisierung kein freier `poll_slot` (alle `MAX_INSTANCES` Poll-Slots belegt); Antwort aus dem Handler-Thread nach abgeschlossenem Handshake, daher auch unter TLS (IC-11) |
| `queue_full` | 503 | Kommando-Queue der Instanz voll |
| `command_timeout` | 504 | kein Terminal-/`accepted`-Zustand innerhalb 20 s (Dashboard-Wartezeit; Kommando läuft weiter). Derselbe Code steht als `error.code` im Kommandozustand `error`, wenn ein `accepted`-Kommando 330 s ohne Terminal-Ack bleibt (IC-11) |

Instanzseitige Ack-Fehlercodes (`status: rejected` vor, `error` nach `accepted`, IC-4 Ack-Regel; `busy` kommt in beiden vor: Fleet-Write-Gate → `rejected`, `SyncExecutor`-Gate → `error`): `unknown_command`, `invalid_args`, `remote_write_disabled`, `busy`, `duplicate_command` (m4, IC-4), `path_not_writable`, `base_hash_mismatch`, `redacted_value`, `invalid_config` (F2, IC-15: Ergebnis-Mapping verletzt eine Admin-UI-Schreibvalidierung; `message` enthält den `ValueError`-Text, durch `redact_text`), `lossy_write`, `internal_error`.

Name-Autorität: `name` in `fleet-instances-v1` ist immer der Registry-Name aus `issue-token` (serverautoritativ). Enroll und Heartbeat aktualisieren ihn nie; weicht `fleet-enroll-v1.name` bzw. `status.name` davon ab, setzt der Server `name_mismatch: true` (Dashboard zeigt einen Warnhinweis neben dem Registry-Namen, `list` eine Markierung `[name mismatch]`). Der gemeldete Name bleibt nur innerhalb von `status` sichtbar. Da `name_mismatch` aus `name` ≠ `status.name` abgeleitet und nicht gespeichert wird (IC-8), ist es erst nach dem ersten Heartbeat aussagekräftig; vorher (`status: null`) ist es immer `false` — ein abweichender Name nur im Enroll-Body wird nur im Server-Audit (`enroll`, `detail`) vermerkt.

### IC-8 Registry `<state-dir>/registry.json`

```json
{
  "schema": "fleet-registry-v1",
  "instances": {
    "inst_3f9a1c2b4d5e6f70": {
      "name": "agent-meta",
      "state": "active",
      "token_hash": "sha256:9b1c...<64 hex>",
      "pending_token_hash": null,
      "pending_until": null,
      "issued_at": "2026-10-23T12:00:00Z",
      "enroll_deadline": "2026-10-24T12:00:00Z",
      "enrolled_at": "2026-10-23T12:05:00Z",
      "revoked_at": null,
      "revoked_by": null,
      "last_heartbeat": "2026-10-23T12:30:00Z",
      "heartbeat_interval": 30,
      "status": {"schema": "fleet-status-v1", "name": "agent-meta", "prefix": "am", "agent_meta_version": "2.0.0-beta.2", "last_sync": null, "health": {"state": "degraded", "reasons": ["no sync record"]}, "providers": ["Claude", "Opencode", "Gemini"], "allow_remote_write": false, "heartbeat_interval": 30}
    }
  }
}
```

(Das Beispiel kürzt den Hash; real stehen 64 Hex-Zeichen.)

- `instance_id` = `inst_` + `secrets.token_hex(8)`; `name` eindeutig (Duplikat bei `issue-token` → Exit 1).
- Inhalt: nur Metadaten, Hashes, Zeitstempel, letzter Status-Payload. Nie Klartext-Token, nie Config- oder Log-Inhalt (D5).
- In-Memory autoritativ, geschützt durch `threading.Lock`. Persistenz: sofort bei Zustandsübergängen (issue/enroll/rotate/revoke/expire); Heartbeat-Aktualisierungen gesammelt höchstens alle 60 s.
- Schreiben atomar: Temp-Datei im selben Verzeichnis mit eindeutigem Namen `private_temp_path` (`.registry.json.<token_hex(8)>.tmp`) per `create_private_file` (`O_CREAT|O_EXCL|O_WRONLY`, 0600 ab Erzeugung — kein umask-/chmod-Fenster), `os.fsync`, `os.replace`. `serve` ruft beim Start `cleanup_private_temps(state_dir, ("registry.json", "audit.log"))`, der `FleetClient.start` analog für `.meta-viz/` (`fleet-state.json`, `fleet-audit.log`); liegengebliebene Temp-Dateien eines Absturzes blockieren damit weder Schreiben noch Rotation. Verzeichnis per `os.mkdir(path, 0o700)` angelegt; existiert es mit Group-/Other-Bits → `serve`/CLI Exit 2.
- `name` ist serverautoritativ (gesetzt nur von `issue-token`); `name_mismatch` wird beim Ausliefern aus `name` ≠ `status.name` abgeleitet und nicht gespeichert (IC-7).
- Obergrenze 256 Instanzen (`issue-token` darüber → Exit 1). `revoked`/`expired` bleiben als Tombstone (ohne `token_hash`, auf `null` gesetzt) erhalten; Löschen ist Nicht-Ziel.
- CLI-Subkommandos und `serve` greifen nicht gleichzeitig zu: CLI-Kommandos verlangen, dass kein `serve` läuft (`<state-dir>/serve.pid` + Prozess-Check, sonst Exit 1 mit Hinweis); `serve` lädt die Registry beim Start. Live-Ausstellung ohne Neustart ist Nicht-Ziel dieser Version (siehe R-11).

### IC-9 Audit (beidseitig, provider-neutral)

- Pfade: Instanz `<root>/.meta-viz/fleet-audit.log`; Server `<state-dir>/audit.log`. Kein Pfad unter `.claude/` oder einem anderen Provider-Verzeichnis.
- Format: JSONL, eine Zeile pro Ereignis: `{"ts", "side": "server"|"instance", "event", "outcome": "ok"|"error"|"rejected"|"denied", "instance_id", "command_id", "command", "actor": "dashboard"|"cli"|"instance"|"server", "detail"}`; `detail` ≤ 200 Zeichen, durch `redact_text`.
- Ereignisse: `issue`, `enroll`, `rotate_start`, `rotate_complete`, `revoke`, `deregister`, `expire`, `auth_failed`, `pin_mismatch`, `tls_refused`, `config_invalid`, `command_enqueued`, `command_delivered`, `command_ack`, `command_rejected`, `write_gate_denied`, `confirm_issued`, `confirm_used`. Heartbeats und Polls werden nicht protokolliert.
- Datei 0600 ab Erzeugung (`os.open(..., O_CREAT|O_APPEND|O_WRONLY, 0o600)`, danach `os.fchmod` auf demselben fd), Rotation nach dem Muster `hook_audit_log_append`: > 2000 Zeilen → auf die neuesten 1000 kürzen (atomar über Temp-Datei aus `create_private_file` + `os.replace`).
- Aggregation (DoS-Schutz der Audit-Datei): serverseitige `auth_failed`- und `tls_refused`-Ereignisse entstehen vor jeder Authentisierung und werden über `AuditLog.aggregate` geschrieben — je Ereignistyp höchstens 1 Zeile pro Minute mit Zähler und bis zu 5 Quell-IPs im `detail`. Ein nicht authentisierter Angreifer kann damit höchstens 2 Zeilen/min erzeugen und die Rotation nicht in relevanter Zeit erzwingen (AC-48). Alle übrigen Ereignisse setzen einen gültigen Token voraus und werden einzeln geschrieben.

### IC-10 Enrollment, Rotation, Widerruf

Zustandsmaschine (Server, je Instanz):

```
            issue-token
   (none) ─────────────▶ issued ──enroll (Token gültig, vor Deadline)──▶ active
                           │                                              │  ▲
                           │ Deadline überschritten                       │  │ rotate_complete (neuer Token benutzt)
                           ▼                                              │  │
                        expired                       rotate-token ──▶ active+pending ──grace abgelaufen──▶ active (nur neuer Hash)
                                                                          │
              revoke (CLI) │ deregister (Instanz) │ revoke während pending
                           ▼
                        revoked  (terminal; Tombstone)
```

Ablauf Enrollment:

1. Admin auf dem Server-Host: `python3 scripts/fleet-server.py issue-token --name ha-go-gauge --out ./ha-go-gauge.token --tls-cert /etc/fleet/cert.pem` → Registry-Eintrag `issued`, Ausgabe: Instance-ID, Deadline, Fingerprint.
2. Übergabe out-of-band: Token-Datei per `scp`/Passwortmanager auf den Instanz-Host, Ablage außerhalb des Repos (empfohlen `~/.config/agent-meta/fleet/<name>.token`), `chmod 600`. Der Fingerprint ist nicht geheim und wird über denselben Kanal mitgeteilt.
3. Instanz-Config: `fleet.enabled: true`, `fleet.url`, `fleet.token-file`, `fleet.cert-fingerprint`.
4. Start des Admin-Servers → Client: Pin-Prüfung → `POST /v1/enroll`. Server: Token-Hash-Treffer, `state == issued`, `now ≤ enroll_deadline` → `active`, `enrolled_at`; Antwort mit `instance_id`. Erneutes Enroll im Zustand `active` ist idempotent (200, gleiche ID; aktualisiert werden nur `prefix`/`agent_meta_version`, **nie** `name` — Abweichung → `name_mismatch`, IC-7).
5. Danach Heartbeats und Polls.

Fehlerpfade Enrollment: unbekannter Token → 401 `invalid_token`; Deadline überschritten → Zustand `expired`, 403 `enroll_expired` (Admin stellt neu aus); Pin-Mismatch → Client sendet nichts; `revoked` → 403 `instance_revoked`; Name-Konflikt nur bei `issue-token` (Exit 1).

Rotation:

1. `rotate-token --instance <id> --out new.token [--grace-hours 24]` → `pending_token_hash`, `pending_until = now + grace`.
2. Während `pending`: alter und neuer Token gültig.
3. Erster Request mit neuem Token → `token_hash = pending_token_hash`, Pending-Felder `null`, Audit `rotate_complete`; alter Token ab sofort 401.
4. `pending_until` überschritten ohne Nutzung → alter Hash wird verworfen, neuer bleibt (`rotate_complete`, `actor: server`); Instanz ist bis zur Token-Übergabe nicht authentisiert.
5. `--immediate`: alter Hash sofort ersetzt (Kompromittierungsfall), Instanz behält ID.
6. Instanzseitig: Token-Datei überschreiben; der Client erkennt die mtime-Änderung beim nächsten Request.

Widerruf:

- **Serverseitig:** `revoke --instance <id>` → `revoked`, `revoked_by: "server"`, Hashes `null`. Nächster Request der Instanz → 403 `instance_revoked`; Client schreibt `STATE_FILE` und stoppt.
- **Instanzseitig:** `fleet.enabled: false` (wirkt spätestens nach einem Heartbeat-Intervall) → `POST /v1/deregister` → Server `revoked`, `revoked_by: "instance"`. Alternativ Token-Datei löschen → Client stoppt lokal (`token_missing`), Server sieht die Instanz als `offline`.
- Reaktivierung immer über neues `issue-token` (neue Instance-ID).

### IC-11 Transport- und Ressourcengrenzen (stdlib `ThreadingHTTPServer`)

| Parameter | Wert | Umsetzung |
|---|---|---|
| Max. gleichzeitige Verbindungen | `MAX_INSTANCES + RESERVED_SLOTS` = 256 + 32 = 288 | Gekoppelt an die Instanz-Obergrenze, weil jede aktive Instanz nahezu permanent einen Long-Poll hält (A3). `threading.BoundedSemaphore(288)`; nicht-blockierendes `acquire` in überschriebenem `process_request`; `release` im `finally` von `process_request_thread`. Thread-Obergrenze damit 288 Handler + Hauptthread. |
| Reserve für `/api/*`, Heartbeat, Ack, Enroll | 32 Slots | Polls ziehen nach erfolgreicher Authentisierung zusätzlich aus `poll_slots = threading.BoundedSemaphore(MAX_INSTANCES)` (1 Poll je Instanz erzwungen, Zeile „Poll-Haltezeit"); damit können Polls höchstens 256 der 288 Slots belegen, mindestens 32 bleiben für alle übrigen Requests. Kein freier `poll_slot` → 503 `busy` aus dem Worker (auch unter TLS, Handshake ist dann abgeschlossen). Ein Ersatz-Poll derselben Instanz zieht keinen zusätzlichen Slot: er beendet den alten Poll mit 204 und übernimmt dessen `poll_slot` (Zeile „Poll-Haltezeit"). |
| Verhalten über dem Limit | Plain-HTTP: 503; TLS: Schließen ohne Antwort | Der Hauptthread schreibt nie auf einen TLS-Socket (`do_handshake_on_connect=False`: jedes Write würde den Handshake im Hauptthread erzwingen, ein stummer Client blockierte `accept()`). Unter TLS über dem Limit: `shutdown_request` ohne Antwort; der Client behandelt den Verbindungsabbruch wie 503 (Backoff, IC-4). Plain-HTTP (nur Loopback): fester 503-`busy`-Body per nicht-blockierendem `send` (best effort), dann Schließen. |
| `daemon_threads` | `True` | wie `_DaemonThreadingHTTPServer` im Admin-Server |
| `request_queue_size` | 32 | Listen-Backlog |
| Deadline Request-Zeile + Header + Body | 10 s gesamt | Pro Verbindung absolute Deadline ab `accept()`; vor jedem `recv` `sock.settimeout(max(0.1, deadline - now))`; Überschreitung → Schließen ohne Antwort. Verhindert Slowloris über das per-`recv`-Timeout hinweg. |
| Socket-Timeout Handler (nach dem Lesen) | 35 s | `StreamRequestHandler.timeout = 35` gilt nur noch für das Schreiben der Antwort (> Poll-Haltezeit 25 s). |
| Pre-Auth-Verbindungen je Quell-IP | 8 | Zähler je Peer-IP für Verbindungen, deren Token noch nicht geprüft ist (Handshake + Header-Phase); die 9. wird geschlossen (TLS ohne Antwort, Plain 503). Nach erfolgreicher Authentisierung zählt die Verbindung nicht mehr (Instanzen hinter NAT bleiben möglich). Loopback-Peers sind ausgenommen (Reverse-Proxy-Topologie; Slowloris-Schutz liegt dann beim Proxy). |
| TLS-Handshake | im Handler-Thread, innerhalb der 10-s-Deadline | Listen-Socket mit `do_handshake_on_connect=False` gewrappt; `sock.settimeout(...)`, `sock.do_handshake()` im Worker; Fehler → Socket schließen, `AuditLog.aggregate("tls_refused", ip)` (≤ 1 Zeile/min). Verhindert, dass ein stummer Client `accept()` im Hauptthread blockiert. |
| Poll-Haltezeit | ≤ 25 s | `threading.Condition` je Instanz; höchstens 1 offener Poll je Instanz — ein neuer Poll derselben Instanz beendet den alten sofort mit 204 und übernimmt dessen `poll_slot` (Slot-Übergabe unter dem Instanz-Lock, kein `release`/`acquire`-Fenster); er wird daher nie wegen erschöpfter `poll_slots` mit `busy` abgewiesen. |
| Kommando-Queue je Instanz | 16 | voll → Dashboard `503 queue_full` (Backpressure) |
| Kommando-Ablauf | `queued` 60 s nach `issued_at` → `expired`; `delivered` ohne Ack 60 s nach Zustellung → `expired`; `accepted` ohne Terminalzustand 330 s nach `accepted` → `error` mit `command_timeout` | Slow-Consumer-Drop: pollt eine Instanz nicht, verfallen ihre Kommandos. Geht eine Poll-Antwort oder ein Ack verloren, erreicht jedes Kommando trotzdem einen Terminalzustand (at-most-once, IC-4). 330 s = `SyncExecutor`-Timeout 300 s + 30 s Reserve für Ack-Versand. |
| Dashboard-Wartezeit auf Ergebnis | 20 s | danach `504 command_timeout` (Kommando läuft weiter, abfragbar über `/api/commands/<id>`) |
| Body-Limit Instanz-POST | 1 MiB | `Content-Length` fehlt/zu groß → 413 |
| Body-Limit Dashboard-POST | 64 KiB | 413 |
| Heartbeat-Intervall | 30 s (10-300) | vom Client gemeldet |
| Liveness | `online` ≤ 2,5 × Intervall (75 s), `stale` ≤ 10 × Intervall (300 s), sonst `offline`; ohne Heartbeat `never` | nur Server-Empfangszeit, keine Client-Zeitstempel |
| Dashboard-Polling | 5 s | `fleet-ui.html` |
| Instanzen | ≤ 256 (`MAX_INSTANCES`) | IC-8; Änderung nur zusammen mit dem Verbindungslimit |

SSE wird nicht verwendet (A3); Heartbeat-Kommentare im SSE-Sinn entfallen, weil jede Long-Poll-Antwort spätestens nach 25 s zurückkommt und damit auch Proxy-Idle-Timeouts unterschreitet.

Python-3.9-Kompatibilität: alle neuen Module **einschließlich `scripts/fleet-server.py`** (Python-Untergrenze des Servers: 3.9, gleich wie Client) mit `from __future__ import annotations`, kein `match`, nur 3.9-verfügbare APIs (`ThreadingHTTPServer` ≥ 3.7, `ssl.TLSVersion` ≥ 3.7, `ssl.PROTOCOL_TLS_SERVER/CLIENT` ≥ 3.6). Da `scripts/lib/consistency/python_compat.py` heute nur `_SCAN_DIRS = (("scripts", "lib"), ("tests",))` prüft (VERIFIED), ergänzt F1 eine Konstante `_SCAN_FILES = (("scripts", "fleet-server.py"),)`, die `_iter_py_files` zusätzlich liefert (AC-30).

### IC-12 TLS und Pinning

- Server: `ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)`, `ctx.minimum_version = ssl.TLSVersion.TLSv1_2`, `ctx.load_cert_chain(certfile, keyfile)`; Ladefehler → Exit 2. Fingerprint = `cert_fingerprint` des ersten Zertifikats der Datei (DER), ausgegeben beim Start.
- Fail closed: Nicht-Loopback-Bind ohne Cert/Key → Exit 2 (IC-6). Loopback darf plain HTTP (lokaler Test, Reverse-Proxy-Betrieb).
- Reverse-Proxy-Topologie: `fleet-server.py` bindet `127.0.0.1`, der Proxy terminiert TLS; Instanzen pinnen den Proxy-Fingerprint. Die Howto beschreibt beide Topologien. Pflicht in der Howto: der Fingerprint wird **auf dem Proxy-Host aus der Zertifikatsdatei** berechnet (`openssl x509 -in <cert.pem> -noout -fingerprint -sha256` oder `issue-token --tls-cert <cert.pem>`) und out-of-band übergeben; ein Abruf über das Netz (`openssl s_client`) ist Trust-on-first-use und in der Howto ausdrücklich als unzulässig markiert.
- Automatische Erneuerung (z. B. Let's Encrypt): das Pin gilt dem Leaf-DER, jede Erneuerung bricht es (R-13). Howto-Empfehlung: für den Fleet-vHost ein eigenes, langlebiges selbstsigniertes Zertifikat ohne Auto-Renewal; wer Auto-Renewal nutzt, muss den Wechsel über die Zwei-Einträge-Liste fahren (neues Zertifikat vorab erzeugen, dessen Fingerprint als zweiten Eintrag verteilen, erst dann deployen).
- Client: siehe IC-4 (Pinning nach jedem `connect()`, vor dem ersten Request-Byte; `http://` nur bei Loopback-Host; `https://` ohne Fingerprint → `FleetConfigError("fingerprint_required")`).
- Zertifikatswechsel: neuen Fingerprint als zweiten Listeneintrag in `fleet.cert-fingerprint` verteilen, Server-Zertifikat tauschen, alten Eintrag entfernen.

### IC-13 Dashboard `docs/ui/fleet-ui.html`

- Single-File, Vanilla-JS/CSS, keine externen Ressourcen; ausgeliefert von `GET /` (Pfad relativ zu `fleet-server.py`: `../docs/ui/fleet-ui.html`).
- Response-Header: `Content-Security-Policy: default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'; frame-ancestors 'none'`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`.
- Token-Eingabe einmalig per Formularfeld, Ablage in `sessionStorage`, Versand nur als `Authorization`-Header.
- Darstellung ausschließlich über `document.createElement` + `textContent`; keine Zuweisung von Daten an `innerHTML`/`outerHTML`/`insertAdjacentHTML`, kein `eval`. Instanzgelieferte Strings laufen vor der Anzeige durch eine Funktion `displaySafe(s)`, die Steuerzeichen (`/[\u0000-\u001f\u007f-\u009f]/g`, außer `\n` in Log-/Config-`<pre>`) als `\uNNNN` sichtbar macht; Instanznamen werden immer aus dem Registry-Feld `name` angezeigt, bei `name_mismatch: true` mit Warnhinweis.
- Ansichten: Instanztabelle (Name, Prefix, Version, Liveness, Health, letzter Sync, Provider), Detail mit „Logs" (Quelle + Zeilenzahl) und „Config" (Phase 2, als formatiertes JSON in `<pre>` via `textContent`).
- F2: Buttons „Sync auslösen"/„Config ändern" nur sichtbar, wenn `status.allow_remote_write` true; Bestätigungsdialog zeigt Instanzname, Kommando, Args (bei `put-config` alle Ops) und — bei `put-config` — den Kommentarverlust-Hinweis (O-F2); erst danach zweiter POST mit `confirm_nonce`.

### IC-14 Phase 3 — `trigger-sync` (F2)

- Server: Write-Kommandos durchlaufen in dieser Reihenfolge: Admin-Token → optional Write-Token (`X-Fleet-Write-Token`, `hmac.compare_digest`, nur wenn `--write-token-file` gesetzt; sonst 401 `write_reauth_required`) → `status.allow_remote_write` der Instanz true (sonst 403 `write_disabled`, UX-Vorprüfung) → Bestätigungs-Nonce.
- Bestätigungs-Nonce: erster POST ohne gültige Nonce → 428 `confirmation_required` mit `{"confirm_nonce": secrets.token_urlsafe(16), "expires_in": 60}`; Nonce ist einmalig, 60 s gültig und gebunden an `(instance_id, type, sha256(kanonisches JSON der args))`. Wiederverwendung oder abweichende Args → erneut 428.
- Instanz (autoritativ): `allow_remote_write` aus frisch geladener Config; false → `rejected/remote_write_disabled`, Audit `write_gate_denied`, kein Subprozess.
- Handler (in `admin-server.py`, injiziert): `mode: "validate"` → `SyncExecutor.dry_run()` (führt laut Docstring `sync.py --validate` aus), `mode: "run"` → `SyncExecutor.run()`; ist das gemeinsame `SyncExecutor`-Ausführungs-Gate belegt (Admin-UI-Sync läuft, R-16), erkennt der Handler das am Ergebnis-Marker `"busy": true` (R-16) und sendet — da das Kommando bereits `accepted` ist — das Terminal-Ack `error` mit `error.code: busy` ohne Subprozess (IC-4 Ack-Regel, AC-54); `returncode: -1` allein (Timeout/Exception) wird weiterhin als normales `error` mit `exit_code` gemeldet. Ablauf (IC-4 Write-Worker): der Poll-Thread erwirbt das Busy-Gate nicht-blockierend, reiht das Kommando an den Worker `fleet-write` und sendet sofort Ack `accepted`; der Worker führt den Sync aus (bis 300 s, `SyncExecutor`-Timeout), sendet dann Ack `ok|error` mit `exit_code` und ≤ 50 redigierten Tail-Zeilen und gibt das Gate erst danach frei. Der Poll-Thread pollt währenddessen weiter; ein weiteres Write-Kommando (`trigger-sync` oder `put-config`), solange das Gate gehalten wird → sofort `rejected/busy`.
- Dashboard: POST liefert 202 bei `accepted`; UI pollt `/api/commands/<id>` alle 2 s.

### IC-15 Phase 4 — `put-config` (F2)

- Args: `{"key": "project", "base_sha256": "<64 hex>", "ops": [{"op": "set", "path": "dod-preset", "value": "standard"}, {"op": "delete", "path": "model-overrides.developer"}]}`; höchstens 20 Ops.
- Gates wie IC-14; zusätzlich instanzseitig. Ort (IC-4 Ack-Regel): die reinen Arg-Prüfungen 2-3 führt der Poll-Thread vor `accepted` aus (`rejected/<code>`); die dateiabhängigen Schritte 1, 4-6 laufen im Worker nach `accepted`, Ablehnungen dort → Terminal-Ack `error` mit `error.code: <code>`.
  1. `base_sha256` ≠ sha256 der aktuellen Datei → `error/base_hash_mismatch`.
  2. Jeder `path` muss gleich einem Eintrag aus `REMOTE_WRITE_ALLOWLIST` sein oder darunter liegen → sonst `rejected/path_not_writable`. Default-Inhalt (O-F3): `dod-preset`, `rules-preset`, `conventions-preset`, `tier-preset`, `speech-mode`, `max-parallel-agents`, `ai-providers`, `platforms`, `roles`, `model-overrides`. Nie schreibbar, unabhängig von der Liste: `fleet`, `admin-ui`, `hooks`, `repo_containment`, `variables`, `mcp-servers`, `mcp-registry`, `plugins`, `environments`, `allow-committed-secrets`, `provider-isolation`.
  3. `contains_redaction_marker(value)` → `rejected/redacted_value` (verhindert das Zurückschreiben redigierter Platzhalter).
  4. `apply_config_ops` erzeugt das neue Mapping.
  5. **Admin-UI-Schreibvalidierung (Parität):** Der Admin-UI-Pfad `AdminRequestHandler._route_put_config` validiert für `key == "project"` vor dem Schreiben mit `_assert_project_update_writable(body, existing)`, `_validate_project_provider_options(body.get("provider-options"))` und `_guard_context_profile_write` für `context-profile` und `provider-overrides` (VERIFIED). F2 extrahiert **exakt diese Sequenz** (Reihenfolge und Argumente wie heute im `if key == "project"`-Zweig von `_route_put_config`: `_assert_project_update_writable(body, existing)`; falls `body` ein `dict` ist: `_validate_project_provider_options(body.get("provider-options"))`, `_guard_context_profile_write("context-profile", body.get("context-profile"))`, `_guard_context_profile_write("provider-overrides", body.get("provider-overrides"))`) in eine Methode `AdminRequestHandler._validate_project_document(self, body: Any, existing: dict) -> None` (wirft `ValueError`), die `_route_put_config` an genau dieser Stelle aufruft — reines Extract-Method-Refactoring ohne Verhaltensänderung. **Nicht** aufgenommen wird `_guard_model_block_write`: der Guard läuft heute nur im Partial-Section-Pfad `_write_project_section`, nicht in `_route_put_config` (VERIFIED); ihn in die gemeinsame Methode zu ziehen, würde das Verhalten von `PUT /api/config/project` ändern, und für Fleet wäre er toter Code, weil `MODEL_EXCLUSIVE_BLOCKS` (`model-override-all`, `model-inherit-main-chat`) nicht in `REMOTE_WRITE_ALLOWLIST` stehen (Schritt 2 lehnt sie vorher mit `path_not_writable` ab). Wer diese Blöcke später in die Allowlist aufnimmt (O-F3), muss den Guard im Fleet-Handler zusätzlich aufrufen. **Nicht validiert** werden die Werte von `ai-providers` und `model-overrides` (sowie `platforms`, `roles`, `*-preset`, `speech-mode`): dafür gibt es im `project`-Schreibpfad der Admin-UI heute keine Wertprüfung — Fleet hat damit dieselbe Lücke wie die Admin-UI, nicht mehr und nicht weniger (R-15, O-F3). Der injizierte Fleet-Handler ruft genau diese Methode auf einem request-losen Exemplar `AdminRequestHandler.__new__(AdminRequestHandler)` auf (ohne `__init__`, also ohne Socket): die beteiligten Methoden nutzen ausschließlich Klassenzustand (`config_manager`, `root`, `_service_context()` über `_agent_meta_root`/`_ensure_lib_on_path`, VERIFIED für `_load_providers_registry`, `_ensure_lib_on_path`, `_agent_meta_root`). Der F2-Plan verifiziert dies für `_service_context`; greift eine Methode auf Request-Zustand zu, ist das ein Blocker des Plans, kein stilles Abweichen. **Argumente im Fleet-Pfad:** `body` = das vollständige neue Mapping aus Schritt 4 (nicht nur die geänderten Sektionen), `existing` = das unmittelbar vorher per `ConfigManager.read("project")` gelesene Mapping; unveränderte Read-only-Sektionen passieren damit wie beim Admin-UI-GET-then-PUT, aber auch unveränderte `provider-options`/`context-profile`/`provider-overrides` werden mitvalidiert (eine bereits ungültige Datei blockiert jeden Remote-Edit — gewollt fail closed). **Löschungen:** `_assert_project_update_writable` iteriert nur über die Keys in `updates` und sieht entfernte Top-Level-Keys nicht (VERIFIED; in der Admin-UI unkritisch, weil `_deep_merge` nicht löscht). Der Fleet-Handler ruft daher vor `_validate_project_document` zusätzlich `self._assert_project_sections_writable(set(existing) - set(body))` (bestehende Methode, VERIFIED) — jede entfernte Top-Level-Sektion außerhalb `PROJECT_WRITABLE_SECTIONS` → `ValueError("section not allowed: …")`. Dieser Aufruf liegt im Fleet-Handler, nicht in `_validate_project_document` (dort würde er den Admin-UI-Teilbody als Löschung fehlinterpretieren). `ValueError` → `error/invalid_config`, keine Schreiboperation. Wirksam schreib- und löschbar ist damit die Schnittmenge aus `REMOTE_WRITE_ALLOWLIST` und `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py`, VERIFIED); `max-parallel-agents` steht heute nicht in `PROJECT_WRITABLE_SECTIONS` und ist remote weder setz- noch löschbar (`set` → `_assert_project_update_writable`, `delete` → Lösch-Prüfung, jeweils `ValueError("section not allowed: max-parallel-agents")` → `error/invalid_config`, O-F3). `_validate_project_provider_options` und `_guard_context_profile_write` greifen für Fleet erst, wenn `provider-options`, `context-profile` bzw. `provider-overrides` in die `REMOTE_WRITE_ALLOWLIST` aufgenommen werden; mit der Default-Liste lehnt Schritt 2 sie vorher ab.
  6. Handler ruft `ConfigManager.write("project", data)` (atomar, Backup, chmod 600 — bestehendes Verhalten, VERIFIED).
- Kommentarverlust: `ConfigManager.write` prüft Round-Trip nur für `ai-providers` (VERIFIED); für `project` verliert ein YAML-Dump Kommentare. Default (O-F2): Admin-UI-Parität — Schreiben mit Backup, `comments_lost` (über `lib.yaml_roundtrip.analyze_roundtrip`) im Ack, Warnung im Bestätigungsdialog.
- Optionale Re-Auth: siehe IC-14 (`--write-token-file`).

## Datenfluss

```
Instanz-Host                                            Fleet-Server-Host
────────────                                            ─────────────────
.meta-config/project.yaml ─┐
.meta-viz/sync-status.json ┼─▶ fleet_client.build_status ──HTTPS(pinned)──▶ POST /v1/heartbeat ──▶ Registry (RAM, ≤60 s → registry.json)
sync.log / admin-server.log┘    (redact_text, redact_config)                                                │
                                                                                                             ▼
                                                                      fleet-ui.html ◀── GET /api/instances (5 s Polling)

Kommando (Pull durch die Instanz):
fleet-ui.html ──POST /api/instances/<id>/commands──▶ Server-Queue (≤16) ──▶ GET /v1/poll (≤25 s) ──▶ fleet_client.handle_command
                                                                                                          │ liest + redigiert lokal
fleet-ui.html ◀── 200/202 (≤20 s Warten) ◀── Kommandozustand (RAM, 10 min) ◀── POST /v1/ack ◀────────────┘

Audit:  Server ──▶ <state-dir>/audit.log        Instanz ──▶ .meta-viz/fleet-audit.log   (beide JSONL, 0600, redigiert)
```

Datenhoheit:

| Datum | Eigentümer | Persistiert | Wo |
|---|---|---|---|
| Config-Inhalt | Instanz | nein (Server) | nur redigiert im RAM des Servers, 10 min |
| Log-Inhalt | Instanz | nein (Server) | wie oben |
| Klartext-Instanz-Token | Instanz | ja | Token-Datei 0600 (oder Env) |
| Token-Hash | Server | ja | `registry.json` 0600 |
| Status-Payload | Instanz erzeugt, Server hält | ja | `registry.json` |
| Fleet-Admin-Token | Server | ja | `<state-dir>/admin.token` 0600 oder Env |
| Audit | beide | ja | siehe oben |

Der Server liest nie Instanz-Dateien; er vermittelt nur Kommandos und hält redigierte Ergebnisse kurzzeitig im Speicher.

## Phasen

| Phase | Plan | Entry-Kriterien | Exit-Kriterien | Rollback |
|---|---|---|---|---|
| 1 Read-Only-Dashboard | F1 | Spec vom Nutzer freigegeben; O-F1, O-F7, O-F8, O-F9 beantwortet oder Default akzeptiert | AC-1 bis AC-32 und AC-47 bis AC-51 erfüllt; `python3 scripts/sync.py --validate` grün; Howto + API-Referenz vorhanden; manueller End-to-End-Lauf (zwei Instanzen, ein Server, Loopback und TLS) dokumentiert | Instanz: `fleet.enabled: false` (wirkt ≤ 1 Heartbeat-Intervall, AC-13). Code: Revert der F1-Task-Gruppen; der Admin-Hook ist ohne `fleet`-Block wirkungslos (AC-1). Server: Prozess stoppen, `<state-dir>` löschen. |
| 2 Config-Ansicht | F1 | Phase-1-Komponenten gemergt (gleicher Plan, eigene Task-Gruppe) | AC-33 bis AC-36 erfüllt | Revert der Task-Gruppe F1-I „get-config + Config-Ansicht" (Kommando wird `unknown_command`); Instanz-Rollback wie Phase 1. |
| 3 Remote-Sync-Trigger | F2 | F1 gemergt; Phase 1+2 mindestens auf einer realen Instanz in Betrieb; Threat-Model-Abschnitt für Schreibpfad erneut gereviewt; O-F2/O-F3 beantwortet oder Default akzeptiert | AC-37 bis AC-40, AC-46, AC-52 und AC-54 erfüllt | `fleet.allow-remote-write: false` (Default; wirkt ohne Neustart ≤ 1 Intervall, AC-46); Revert der F2-Task-Gruppe; Server ohne Write-Handler lehnt nichts ab, Instanz antwortet `unknown_command`. |
| 4 Remote-Config-Edit | F2 | Phase 3 gemergt | AC-41 bis AC-45 und AC-53 erfüllt | wie Phase 3; inhaltlich: Wiederherstellung aus dem von `ConfigManager.write` angelegten Backup. |

## Threat Model (Skill `threat-model-4-questions`, CISO §7.5)

Das Feature ist intern (Self-Hosting durch den Nutzer), wird hier aber vollständig mit allen vier Fragen behandelt, weil es einen netzwerkerreichbaren Schreibpfad (Phase 3+4) einführt.

**1. Woran arbeiten wir / was bauen wir?** Ein zentraler Prozess (`fleet-server.py`) mit Registry (Metadaten + Token-Hashes), Bearer-Auth (Instanz-Token pro Instanz, ein Fleet-Admin-Token, optional Write-Token), TLS mit Fingerprint-Pinning; Instanzen verbinden sich ausgehend. Daten: Status-Metadaten persistent; redigierte Config/Logs flüchtig. Nutzer: ein Fleet-Admin, Browser im lokalen Netz/über Proxy.

**2. Was kann schiefgehen?** und **3. Was tun wir dagegen?**

| STRIDE | Bedrohung | Gegenmaßnahme | AC |
|---|---|---|---|
| Spoofing | Gefälschter Fleet-Server (DNS/ARP-Spoofing) erhält Token oder schickt Kommandos | Fingerprint-Pinning vor dem ersten Request-Byte; `http` nur Loopback | AC-3, AC-7 |
| Spoofing | Fremde Instanz gibt sich als andere aus | Token pro Instanz; Identität nur aus Token-Hash, keine ID in der URL | AC-9, AC-11 |
| Spoofing | Dashboard-Zugriff durch Dritte | Fleet-Admin-Token, Trennung Admin-/Instanz-Token | AC-18 |
| Tampering | MITM verändert Kommandos/Ergebnisse | TLS ≥ 1.2, Pinning | AC-5, AC-6, AC-7 |
| Tampering | Manipulation von `registry.json` | Verzeichnis 0700, Dateien 0600, atomares Schreiben | AC-25 |
| Tampering | Remote-Edit überschreibt Secrets mit `[REDACTED]` oder sicherheitsrelevante Keys | `redacted_value`-Reject, Write-Allowlist, Sperrliste | AC-41, AC-43 |
| Tampering | Lost Update durch parallele Edits | `base_sha256` | AC-42 |
| Repudiation | Unklar, wer ein Kommando ausgelöst hat | Beidseitiges Audit mit `command_id` | AC-26 |
| Information Disclosure | Secrets in Config/Logs verlassen die Instanz | Instanzseitige Allowlist (Config) + Patterns (Logs) | AC-19, AC-20, AC-33 bis AC-35 |
| Information Disclosure | Token in `ps`/argv, URL, Proxy-Logs, stdout | kein Token-Flag, nur Datei/Env, nur Header, `issue-token` schreibt Datei | AC-8, AC-29 |
| Information Disclosure | Registry-Leak | nur Hashes, keine Inhalte | AC-25 |
| Information Disclosure | XSS im Dashboard über Instanzdaten (Name, Logs) | `textContent`, CSP, `nosniff` | AC-28 |
| Denial of Service | Thread-Erschöpfung, Slowloris, TLS-Handshake-Hänger | Verbindungslimit `MAX_INSTANCES + 32` mit 32 reservierten Nicht-Poll-Slots, 10-s-Gesamt-Deadline für Request-Zeile/Header/Body, ≤ 8 Pre-Auth-Verbindungen je Quell-IP, Handshake im Worker, Hauptthread schreibt nie auf TLS-Sockets | AC-6, AC-21, AC-51 |
| Denial of Service | Audit-Flut durch nicht authentisierte Requests rotiert echte Ereignisse aus dem Log | `auth_failed`/`tls_refused` aggregiert (≤ 1 Zeile/min je Typ, Zähler + Quell-IPs) | AC-48 |
| Spoofing | Instanz meldet fremden Namen (Enroll/Heartbeat) oder injiziert Terminal-Steuersequenzen | Name serverautoritativ, `name_mismatch`-Markierung; Steuerzeichen-Escaping in `list` und Dashboard | AC-50 |
| Tampering | Doppelte Ausführung eines Write-Kommandos | at-most-once-Zustellung, instanzseitige `command_id`-Dedupe | AC-52 |
| Tampering | Remote-Edit erzeugt eine Config, die die Admin-UI-Validierung abgelehnt hätte | Gleiche Validierungsmethode wie `_route_put_config` plus Lösch-Prüfung für entfernte Top-Level-Sektionen, `error/invalid_config` | AC-53 |
| Information Disclosure | Env-Token wird an `sync.py`-Kindprozesse vererbt | Env-Variable nach dem Lesen aus `os.environ` entfernt | AC-47 |
| Tampering | TOCTOU-Fenster bei Erzeugung/Prüfung von Secret-Dateien | `O_CREAT`+`O_EXCL` mit Modus 0600 (`create_private_file`), `fstat` auf dem geöffneten fd | AC-49 |
| Denial of Service | Speicher durch große Bodies/Queues | Body-Limits, Queue 16, Kommando-Retention 1000 | AC-23, AC-24 |
| Elevation of Privilege | Kompromittierter Server löst Sync/Edit aus | Instanz-Gate `allow-remote-write` (Default false, autoritativ, frisch gelesen), Write-Allowlist, Sperrliste `fleet`/`admin-ui`/`hooks` (Gate kann nicht remote geöffnet werden) | AC-37, AC-41 |
| Elevation of Privilege | Gestohlenes Admin-Token löst Schreibkommandos aus | Bestätigungs-Nonce, optional Write-Token | AC-38, AC-40 |
| Elevation of Privilege | Gestohlenes Instanz-Token | Wirkt nur für diese Instanz; Widerruf/Rotation | AC-12, AC-14 |

Bewusst nicht adressiert: CSRF — Auth erfolgt per `Authorization`-Header, nicht per Cookie, daher kein automatisches Mitsenden durch den Browser; Brute Force auf 256-Bit-Token — rechnerisch aussichtslos, kein Rate-Limit (Audit-Flut wird durch Aggregation begrenzt, AC-48).

Restrisiko DoS: ein verteilter Angreifer mit vielen Quell-IPs kann die 288 Slots trotz Per-IP-Limit und 10-s-Deadline zyklisch belegen; Loopback-Peers (Reverse-Proxy) sind vom Per-IP-Limit ausgenommen, dort muss der Proxy Slowloris-Schutz und Verbindungslimits liefern (Howto). Folge ist Nichtverfügbarkeit des Dashboards, kein Datenabfluss; Instanzen fallen auf Backoff zurück.

**4. Was sind die Konsequenzen / haben wir gut gearbeitet?** Worst Case ohne Gegenmaßnahmen: Abfluss von MCP-/API-Credentials mehrerer Repos und fremdgesteuerte Syncs mit Schreibzugriff auf Agent-Konfigurationen in allen angebundenen Repos. Restrisiko mit Gegenmaßnahmen: pattern-basierte Log-Redaction ist best effort (R-3); kompromittierter Server plus Instanz mit `allow-remote-write: true` kann allowlistete Keys ändern. Wirksamkeitsprüfung: die mit „empfohlen (Security)" markierten Tests (Abschnitt „Tests") und ein `concept-reviewer`-Durchlauf dieses Abschnitts vor F2-Start (Entry-Kriterium Phase 3).

## Acceptance Criteria

Tag in Klammern = Phase. Jedes AC ist durch Test, Kommando oder Code-Inspektion (Grep) prüfbar.

- **AC-1 (P1):** Ohne `fleet`-Block oder mit `fleet.enabled: false` erzeugt `AdminServer` keinen `FleetClient`, startet keinen Thread mit Präfix `fleet-`, öffnet keine ausgehende Verbindung und legt keine `.meta-viz/fleet-*`-Datei an.
- **AC-2 (P1):** `fleet.enabled: true` mit `fleet.url: http://<Nicht-Loopback-Host>:7430` → `load_fleet_settings` wirft `FleetConfigError` mit Code `tls_required`; der Admin-Server startet trotzdem, ohne Fleet, mit stderr-Meldung.
- **AC-3 (P1):** `https://`-URL ohne `fleet.cert-fingerprint` → `FleetConfigError("fingerprint_required")`; ungültiges Fingerprint-Format → `invalid_fingerprint`.
- **AC-4 (P1):** Token-Datei mit Group- oder Other-Bits (POSIX) → `insecure_token_file`, kein Request.
- **AC-5 (P1):** `fleet-server.py serve --host 0.0.0.0` (bzw. jede Nicht-Loopback-Adresse) ohne `--tls-cert/--tls-key` endet mit Exit 2 und der Meldung aus IC-6, bevor ein Port gebunden wird.
- **AC-6 (P1):** Mit TLS akzeptiert der Server nur TLS ≥ 1.2; ein Client, der verbindet und nichts sendet, blockiert parallele Requests nicht und wird nach ≤ 10 s getrennt.
- **AC-7 (P1):** Bei Fingerprint-Mismatch schließt der Client die Verbindung, bevor ein Request-Byte (insbesondere der `Authorization`-Header) gesendet wurde; Audit `pin_mismatch` auf der Instanz.
- **AC-8 (P1):** `issue-token` schreibt den Token nur in `--out` (Modus 0600, verweigert existierende Datei), gibt ihn nicht auf stdout/stderr aus; `registry.json` enthält danach genau einen `token_hash` (`sha256:` + 64 Hex), Zustand `issued`, `enroll_deadline` = `issued_at` + 24 h.
- **AC-9 (P1):** Enroll mit gültigem Token vor Deadline → 200, Zustand `active`; wiederholtes Enroll → 200 mit derselben `instance_id`.
- **AC-10 (P1):** Enroll nach Deadline → 403 `enroll_expired`, Zustand `expired`.
- **AC-11 (P1):** Unbekannter Token → 401 `invalid_token` mit `WWW-Authenticate: Bearer`; Token- und Hash-Vergleiche in `fleet_protocol.py`/`fleet-server.py` nutzen `hmac.compare_digest` (Grep: kein `==` auf Token-/Hash-Variablen).
- **AC-12 (P1):** Nach `revoke` liefert der nächste Instanz-Request 403 `instance_revoked`; der Client schreibt `.meta-viz/fleet-state.json` mit `state: revoked`, stoppt und versucht keine Verbindung, bis die Token-Datei-mtime neuer als `since` ist.
- **AC-13 (P1):** Wird `fleet.enabled` zur Laufzeit auf `false` gesetzt, sendet der Client innerhalb eines Heartbeat-Intervalls `POST /v1/deregister`; der Server setzt `revoked`, `revoked_by: "instance"`; der Client stoppt.
- **AC-14 (P1):** Nach `rotate-token` sind alter und neuer Token gültig; die erste Nutzung des neuen Tokens macht den alten ungültig (401); nach `--grace-hours` ohne Nutzung ist der alte ungültig; `--immediate` macht ihn sofort ungültig; `instance_id` bleibt gleich.
- **AC-15 (P1):** Der Heartbeat-Body besteht `validate_payload("fleet-status-v1", …)`; `providers` ist exakt die `ai-providers`-Liste aus `project.yaml` in Originalreihenfolge; die neuen Dateien enthalten keinen Vergleich gegen Provider-Namensliterale (Grep auf `== "` mit Namen aus `config/ai-providers.yaml`).
- **AC-16 (P1):** `read_last_sync` liefert die Werte aus `.meta-viz/sync-status.json` (`source: sync-status`; `last_run_summary: null` → `summary: ""`, `last_run_timestamp` `2026-10-23T12:00:00.123456+00:00` → `2026-10-23T12:00:00Z`); fehlt sie, `sync.log`-mtime mit `exit_code: null` (`source: sync-log-mtime`); fehlt beides, `None`. Health folgt der Regel aus IC-7.
- **AC-17 (P1):** Liveness wird aus der Server-Empfangszeit berechnet: bei Intervall 30 s `online` ≤ 75 s, `stale` ≤ 300 s, darüber `offline`, ohne Heartbeat `never`.
- **AC-18 (P1):** `/api/*` ohne oder mit Instanz-Token → 401; `/v1/*` mit Fleet-Admin-Token → 401; `GET /` ist ohne Token erreichbar.
- **AC-19 (P1):** `get-logs` akzeptiert nur `source` ∈ {`sync`, `admin-server`} und `lines` 1-200 (sonst `rejected/invalid_args`); es gibt kein Pfad-Argument; das Result ist ≤ 64 KiB und jede Zeile durch `redact_text` gelaufen.
- **AC-20 (P1):** `redact_text` maskiert in einer Fixture alle Muster aus IC-3: URL-Basic-Auth, `Authorization: Bearer`, `bearer <token>`, `token=`/`password:`-Paare, `--token <v>`, `ghp_…`, `xoxb-…`, `AKIA…`, `amf_…`, PEM-Private-Key-Block; die Ausgabe enthält keinen der Original-Secret-Werte.
- **AC-21 (P1):** Das Verbindungslimit ist `MAX_INSTANCES + 32` (288). Bei 288 gehaltenen Verbindungen wird die 289. sofort abgewiesen: unter Plain-HTTP (Loopback) mit `503 busy`, unter TLS durch Schließen ohne Antwort, wobei der Hauptthread keinen Byte auf den TLS-Socket schreibt und `accept()` weiter bedient. Halten alle 256 Instanzen gleichzeitig einen Long-Poll, werden `/api/*`-Requests und Heartbeats weiterhin bedient (≥ 32 reservierte Slots); ein authentisierter Poll ohne freien `poll_slot` (und ohne eigenen offenen Poll) erhält `503 busy` aus dem Handler-Thread, auch unter TLS. Nach Freigabe werden neue Requests wieder bedient.
- **AC-22 (P1):** `GET /v1/poll?wait=25` ohne Kommandos antwortet nach 25 s (±1 s) mit 204; ein zweiter Poll derselben Instanz beendet den ersten sofort mit 204 und übernimmt dessen `poll_slot` — auch wenn alle `MAX_INSTANCES` Poll-Slots belegt sind, erhält er kein `busy`.
- **AC-23 (P1):** Das 17. unzugestellte Kommando an eine Instanz → `503 queue_full`; ein 60 s nicht abgeholtes Kommando hat Zustand `expired`; ein zugestelltes Kommando ohne Ack hat 60 s nach Zustellung Zustand `expired`; ein `accepted`-Kommando ohne Terminal-Ack hat 330 s nach `accepted` Zustand `error` mit `error.code: command_timeout`.
- **AC-24 (P1):** Instanz-POST > 1 MiB und Dashboard-POST > 64 KiB → 413 `payload_too_large`, ohne den Body vollständig zu lesen.
- **AC-25 (P1):** `registry.json` hat Modus 0600 in einem 0700-Verzeichnis, wird atomar ersetzt und enthält nur die Felder aus IC-8 (kein Klartext-Token, kein `config`-, `lines`- oder `result`-Feld).
- **AC-26 (P1):** Beide Audit-Logs sind JSONL mit den Feldern aus IC-9, Modus 0600, `detail` redigiert; Heartbeats/Polls erzeugen keine Zeile; bei > 2000 Zeilen wird auf 1000 gekürzt.
- **AC-27 (P1):** Alle Server-Dateien (`registry.json`, `audit.log`, `admin.token`, `serve.pid`) liegen unter `--state-dir`; Default `~/.agent-meta-fleet`.
- **AC-28 (P1):** `GET /` liefert `fleet-ui.html` mit den CSP-/`nosniff`-/`Referrer-Policy`-Headern aus IC-13; eine Instanz mit Name `<img src=x onerror=alert(1)>` wird als Text dargestellt; `fleet-ui.html` enthält keine Datenzuweisung an `innerHTML`/`outerHTML`/`insertAdjacentHTML` und kein `eval` (Grep).
- **AC-29 (P1):** Kein Subkommando von `fleet-server.py` akzeptiert einen Token-Wert als Argument; `_admin_start_detached` und `main()` in `admin-server.py` sind durch F1 unverändert; der Client sendet Token ausschließlich im `Authorization`-Header (keine Query-Parameter `token`).
- **AC-30 (P1):** Die neuen lib-Module **und `scripts/fleet-server.py`** bestehen den Python-3.9-Check (`scripts/lib/consistency/python_compat.py`, erweitert um `_SCAN_FILES` mit `scripts/fleet-server.py`, IC-11) und importieren nur Stdlib sowie bestehende `lib`-Module; Python-Untergrenze des Servers ist 3.9.
- **AC-31 (P1):** `config/project-config.schema.json` enthält die Property `fleet` mit den Keys und Defaults aus IC-1; Szenario `79-fleet-config-opt-in` ist in `tests/scenarios/registry.md` eingetragen und besteht `tests/scenarios/run.sh 79`.
- **AC-32 (P1):** `docs/howto/fleet-server.md` und `docs/api/fleet-api-reference.md` existieren; `docs/howto/admin-ui-remote-access.md` verlinkt auf die Howto; die Alt-Spec trägt einen Hinweis-Header auf diese Spec; `python3 scripts/sync.py --validate-spec-plan` meldet für Spec und Pläne keine Findings der Severity ERROR (geprüft nach Freigabe der Spec, siehe Entry-Kriterium Phase 1). Die bekannten WARNINGs, die aus der `_classify`-Grenze für `*-spec.md` folgen (Spec wird als Plan gelesen), sind zulässig und in R-14 dokumentiert.
- **AC-33 (P2):** `get-config` akzeptiert nur `key: "project"` (sonst `rejected/invalid_args`); kein Fleet-Codepfad öffnet `.meta-config/secrets.local.yaml` (Grep).
- **AC-34 (P2):** `redact_config` auf einer Fixture: nicht allowlistete Top-Level-Keys (`variables`, `mcp-servers`, `hooks`) haben den Wert `[REDACTED]` ohne Unter-Keys; `admin-ui.token`, `admin-ui.token-file`, `fleet.token-file` sind `[REDACTED]`, `admin-ui.port` bleibt sichtbar; ein allowlisteter Teilbaum mit Unter-Key `api-key` wird über `SECRET_KEY_RE` redigiert; ein String-Wert mit `ghp_…` wird pattern-redigiert; die Eingabe bleibt unverändert.
- **AC-35 (P2):** Redaction geschieht vor dem Senden: das Ack-Result enthält ausschließlich die Ausgabe von `redact_config`; Server-Registry und Server-Audit enthalten nach einem `get-config` keinen Config-Wert; der Kommandozustand wird 10 min nach Terminalzustand verworfen.
- **AC-36 (P2):** Das Dashboard zeigt das Config-Result als formatiertes JSON per `textContent`.
- **AC-37 (P3):** `trigger-sync` an eine Instanz mit `allow-remote-write: false` → Ack `rejected/remote_write_disabled`, beidseitig auditiert (`write_gate_denied`), kein `sync.py`-Subprozess gestartet — auch wenn der Server das Kommando ohne Vorprüfung zustellt.
- **AC-38 (P3):** Ein Write-Kommando ohne gültige Nonce → 428 mit `confirm_nonce`; mit Nonce → angenommen; dieselbe Nonce erneut, nach 60 s oder mit geänderten Args → 428.
- **AC-39 (P3):** Bei erlaubtem Write liefert `trigger-sync` erst `accepted` (Dashboard 202), dann `ok|error` mit `exit_code` und ≤ 50 redigierten Tail-Zeilen; ein zweites Write-Kommando (`trigger-sync` oder `put-config`), das eintrifft, nachdem der Worker das erste entnommen hat und bevor dessen Terminal-Ack gesendet ist → `rejected/busy` (Busy-Gate `threading.Semaphore(1)`, nicht der Queue-Füllstand; Grep: `acquire(blocking=False)` im Poll-Pfad, `release()` im `finally` des Workers nach dem Terminal-Ack).
- **AC-40 (P3):** Mit `--write-token-file` werden Write-Kommandos ohne gültigen `X-Fleet-Write-Token` mit 401 `write_reauth_required` abgelehnt; Read-Kommandos sind davon nicht betroffen.
- **AC-41 (P4):** `put-config` lehnt jeden Pfad außerhalb `REMOTE_WRITE_ALLOWLIST` und jeden Pfad unter `fleet`, `admin-ui`, `hooks`, `repo_containment`, `variables`, `mcp-servers`, `mcp-registry`, `plugins`, `environments`, `allow-committed-secrets`, `provider-isolation` mit `rejected/path_not_writable` ab; die Datei bleibt byte-identisch.
- **AC-42 (P4):** Abweichendes `base_sha256` → nach `accepted` Terminal-Ack `error/base_hash_mismatch`, keine Schreiboperation.
- **AC-43 (P4):** Ein Op-Wert, der `[REDACTED]` oder einen Redaction-Marker enthält → `rejected/redacted_value`.
- **AC-44 (P4):** Ein gültiges `put-config` schreibt über `ConfigManager.write("project", …)`: Backup angelegt, Datei 0600, Ack enthält `backup`; beidseitig auditiert.
- **AC-45 (P4):** Das Ack enthält `comments_lost` (Ganzzahl ≥ 0); der Bestätigungsdialog zeigt vor dem Absenden den Kommentarverlust-Hinweis (Verhalten gemäß Antwort auf O-F2).
- **AC-46 (P3):** Wird `fleet.allow-remote-write` zur Laufzeit auf `false` gesetzt, lehnt die Instanz das nächste Write-Kommando ohne Neustart des Admin-Servers ab.

Nachträge aus Review-Revision 1.1 (angehängt, um die Nummerierung stabil zu halten; Phase im Tag):

- **AC-47 (P1):** Ist `AGENT_META_FLEET_TOKEN` gesetzt, ist die Variable nach `_maybe_create_fleet_client` in **jedem** Pfad nicht mehr in `os.environ` — Fleet aktiv, `fleet.enabled: false`, Block fehlt, `FleetConfigError` oder ImportError; ein danach vom Admin-Server gestarteter `sync.py`-Subprozess (`SyncExecutor._run`) sieht sie nicht (Test: Kindprozess gibt `os.environ.get("AGENT_META_FLEET_TOKEN")` aus → `None`). Der Client authentisiert weiterhin mit dem im Speicher gehaltenen Wert.
- **AC-48 (P1):** 1000 Requests mit ungültigem Token bzw. 1000 fehlgeschlagene TLS-Handshakes innerhalb einer Minute erzeugen im Server-Audit je Ereignistyp höchstens eine Zeile mit `count=` und Quell-IP(s) im `detail`.
- **AC-49 (P1):** `registry.json`-Temp-Datei, `admin.token`, `--out`-Token-Dateien, `fleet-state.json`-Temp-Datei und die Audit-Rotations-Temp-Datei werden über `create_private_file` (`O_CREAT|O_EXCL|O_WRONLY`, 0600) erzeugt, Temp-Dateien mit eindeutigem Namen aus `private_temp_path` (`.<name>.<16 hex>.tmp`); eine liegengebliebene Temp-Datei eines früheren Laufs blockiert das nächste atomare Schreiben nicht und wird beim Start von `serve` bzw. `FleetClient.start` durch `cleanup_private_temps` entfernt; Audit-Logs mit `os.open(..., 0o600)` geöffnet; `resolve_secret` prüft den Modus per `os.fstat` auf dem fd, aus dem es liest (Grep: kein `os.chmod` direkt nach der Erzeugung dieser Dateien, kein `os.stat` vor `open` in `resolve_secret`).
- **AC-50 (P1):** Enroll/Heartbeat mit abweichendem `name` ändern den Registry-Namen nicht; ab dem ersten Heartbeat mit abweichendem `status.name` ist `name_mismatch: true` in `fleet-instances-v1` (vor dem ersten Heartbeat `false`); das Dashboard zeigt den Registry-Namen mit Warnhinweis. `fleet-server.py list` gibt einen Status-String mit `\x1b[31m` als `\x1b[31m`-Text (maskiert) aus, nicht als Steuersequenz; das Dashboard stellt Steuerzeichen sichtbar maskiert dar.
- **AC-51 (P1):** Ein Client, der die Header byteweise langsamer als die 10-s-Gesamt-Deadline sendet, wird nach ≤ 10 s getrennt, unabhängig vom per-`recv`-Timeout; die 9. gleichzeitige Pre-Auth-Verbindung einer Nicht-Loopback-Quell-IP wird abgewiesen; authentisierte Verbindungen zählen nicht gegen dieses Limit.
- **AC-52 (P3):** Während ein `trigger-sync` im Thread `fleet-write` läuft (also nach dessen Entnahme aus der Übergabe-Queue und bis zum Versand seines Terminal-Acks), pollt die Instanz weiter: ein zweites Write-Kommando erhält innerhalb einer Poll-Runde `rejected/busy`, ein Read-Kommando wird normal beantwortet; nach dem Terminal-Ack wird das nächste Write-Kommando wieder `accepted` (Gate freigegeben, auch wenn der Handler eine Exception wirft). Ein Write-Kommando mit bereits gesehener `command_id` → `rejected/duplicate_command` ohne Ausführung. Der Server stellt kein Kommando ein zweites Mal zu (at-most-once); die Instanz lehnt kein Kommando wegen `expires_at` ab (Grep: `fleet_client.py` wertet `expires_at` nicht aus).
- **AC-53 (P4):** `put-config` ruft vor `ConfigManager.write` dieselbe Validierungsmethode `AdminRequestHandler._validate_project_document` auf wie `_route_put_config` für `key == "project"`; `_validate_project_document` enthält genau die drei heutigen Aufrufe aus `_route_put_config` und keinen `_guard_model_block_write`-Aufruf (Grep). Prüffälle (Ergebnis jeweils Terminal-Ack `error` nach `accepted`): (a) `{"op": "set", "path": "max-parallel-agents", "value": 4}` mit Default-Allowlist (allowlistet, aber nicht in `PROJECT_WRITABLE_SECTIONS`) → `error/invalid_config`, `message` enthält `section not allowed`, Datei byte-identisch; (b) nur mit testweise um `context-profile` erweiterter `REMOTE_WRITE_ALLOWLIST`: `{"op": "set", "path": "context-profile", "value": "huge"}` → `error/invalid_config` mit `context-profile.invalid`, Datei byte-identisch; mit Default-Allowlist liefert derselbe Op vor `accepted` `rejected/path_not_writable`; (c) `{"op": "delete", "path": "max-parallel-agents"}` auf einer Datei, die `max-parallel-agents` enthält → `error/invalid_config`, `message` enthält `section not allowed: max-parallel-agents`, Datei byte-identisch; ein `delete` in bzw. von einer Sektion aus `PROJECT_WRITABLE_SECTIONS` ∩ Allowlist (z. B. `model-overrides.developer`) wird geschrieben. Die Lösch-Prüfung steht im Fleet-Handler, nicht in `_validate_project_document` (Grep). Das Admin-UI-Verhalten von `PUT /api/config/project` bleibt unverändert (gleiche Antworten für dieselben Bodies vor und nach der Extraktion).

Nachtrag aus Review-Revision 1.2:

- **AC-54 (P3):** Läuft ein über die Admin-UI gestarteter `sync.py`-Subprozess (jeder `SyncExecutor._run`-Aufruf), erhält ein Fleet-`trigger-sync` `accepted` und danach das Terminal-Ack `error` mit `error.code: busy` und startet keinen zweiten `sync.py`-Subprozess; umgekehrt startet keine Admin-UI-Route aus R-16 einen Subprozess, solange ein Fleet-`trigger-sync` läuft — sie liefert das Busy-Ergebnis `{"success": false, "busy": true, "returncode": -1, "output": "sync already running"}` mit dem in R-16 genannten HTTP-Status (neues, beabsichtigtes Admin-UI-Verhalten; bisher gab es keine Busy-Antwort). Im Busy-Fall bleibt `.meta-viz/sync-status.json` byte-identisch (`_record_run` nicht aufgerufen). Umsetzung über ein gemeinsames, nicht-blockierendes Ausführungs-Gate in `SyncExecutor._run` (R-16).

## Tests (optional, D8)

DoD-Preset `rapid-prototyping`: Tests sind **separate, klar markierte Tasks pro Komponente** in F1/F2 und **kein Merge-Gate**. Vorgesehene Testdateien: `tests/test_fleet_protocol.py`, `tests/test_redaction.py`, `tests/test_fleet_client.py`, `tests/test_fleet_server.py`, `tests/test_fleet_write.py` (F2), Szenario `79-fleet-config-opt-in`. Tests, die Server-State schreiben, nutzen `--state-dir` unter `.tmp/` bzw. pytest-`tmp_path`; Server-Prozesse binden `127.0.0.1` auf freien Ports; TLS-Tests erzeugen ein selbstsigniertes Wegwerf-Zertifikat zur Laufzeit per `openssl req -x509` in `tmp_path` und werden per `pytest.skip` übersprungen, wenn `openssl` fehlt (kein eingecheckter Private Key — der Secret-Scan vor Commits würde ihn blockieren).

**empfohlen (Security)** — diese Tests sollten trotz D8 umgesetzt werden: AC-2, AC-3, AC-5, AC-7 (fail closed ohne TLS, Pinning), AC-11, AC-12, AC-14, AC-18 (Token-Auth, Widerruf, Rotation, Token-Trennung), AC-37, AC-38, AC-41, AC-43 (Write-Gate `allow-remote-write`, Bestätigung, Write-Allowlist), AC-20, AC-34, AC-35 (Redaction), AC-21, AC-47 bis AC-53 (Verbindungslimit/TLS-Abweisung, Env-Token-Vererbung, Audit-Aggregation, Secret-Datei-Erzeugung, Name-Autorität/Escaping, Slowloris, Write-Worker/Dedupe, Config-Validierung). **Empfohlen (Integrität, nicht Security):** AC-54 (gemeinsames `SyncExecutor`-Gate, keine überlappenden `sync.py`-Läufe).

## Doku-Deliverables

| Datei | Inhalt | Plan |
|---|---|---|
| `docs/howto/fleet-server.md` (Deutsch) | Server starten (Loopback, TLS, Reverse-Proxy), `openssl`-Befehle für selbstsigniertes Zertifikat + Fingerprint, Enrollment Schritt für Schritt, Rotation, Widerruf, Troubleshooting nach Fehlercodes, Agent-/Testbetrieb mit `--state-dir .tmp/…`; Pflichtabschnitte: Fingerprint nur aus der Zertifikatsdatei auf dem (Proxy-)Host, `openssl s_client` als TOFU unzulässig, Zertifikatswechsel/Auto-Renewal (R-13), Token-Datei statt Env empfohlen, Proxy-seitiger Slowloris-Schutz bei Loopback-Bind | F1 |
| `docs/api/fleet-api-reference.md` (Deutsch) | Endpunkte, Schemas, Fehlercodes, Limits aus IC-7/IC-11 | F1 (Write-Teil F2) |
| `docs/howto/admin-ui-remote-access.md` | Kurzer Abschnitt „Mehrere Repos zentral überwachen → Fleet-Server" mit Link; klarstellen, dass Fleet eigene Tokens nutzt und `admin-ui.token` nicht weitergibt | F1 |
| `docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md` | Hinweis-Header „Superseded by docs/specs/2026-10-23-fleet-server-spec.md" | F1 |
| `docs/howto/fleet-server.md` Abschnitt Schreibpfad | `allow-remote-write`, Bestätigung, Write-Token, Write-Allowlist, Backup-Wiederherstellung | F2 |

## Offene Fragen

| ID | Frage | Default-Annahme (gilt, wenn unbeantwortet) | Entscheidungszeitpunkt |
|---|---|---|---|
| O-F1 | Darf die frühere Nutzerantwort Q5 („SSE + Long-Poll") durch „nur Long-Poll" ersetzt werden (A3)? | Ja, nur Long-Poll; SSE als spätere Erweiterung für Dashboard-Live-Updates. | Vor Freigabe dieser Spec. |
| O-F2 | Phase 4 verliert YAML-Kommentare in `project.yaml` (PyYAML-Dump). Akzeptieren, ablehnen oder kommentarerhaltendes Schreiben? | Admin-UI-Parität: Schreiben mit Backup, `comments_lost` im Ack, Warnung im Dialog. | Vor Start von Plan F2. |
| O-F3 | Inhalt der `REMOTE_WRITE_ALLOWLIST`. | Liste aus IC-15 (`dod-preset`, `rules-preset`, `conventions-preset`, `tier-preset`, `speech-mode`, `max-parallel-agents`, `ai-providers`, `platforms`, `roles`, `model-overrides`); wirksam (setzen und löschen) nur die Schnittmenge mit `PROJECT_WRITABLE_SECTIONS` (ohne `max-parallel-agents`, IC-15 Schritt 5). Hinweis: Werte von `ai-providers`/`model-overrides` werden wie in der Admin-UI nicht validiert (R-15); ob diese Keys remote schreibbar bleiben sollen, ist Teil der Entscheidung. Aufnahme von `model-override-all`/`model-inherit-main-chat` erfordert zusätzlich den `_guard_model_block_write`-Aufruf im Fleet-Handler. | Vor Start von Plan F2. |
| O-F4 | Wird ein eigenständiger Client ohne laufenden Admin-Server benötigt (Headless-Repos)? | Nein; Fleet ist nur aktiv, solange der Admin-Server läuft. | Nach vier Wochen Betrieb von Phase 1. |
| O-F5 | Welche Doctor-/Context-Report-Felder kommen nach #977 Phase 0 in den Status-Payload? | Keine in `fleet-status-v1`; Erweiterung als neues Schema `fleet-status-v2` mit eigener Spec-Revision. | Nach Merge von #977 Phase 0. |
| O-F6 | Issue-Nummer #682 wird in anderen Dokumenten auch für die Status-Table-Pflicht zitiert; ist §7 von #682 korrekt als Primärquelle? (Nicht live per `gh` geprüft.) | Ja, #682 §7. | Bei Freigabe dieser Spec durch den Nutzer. |
| O-F7 | Die Konvention verlangt für neue Config-Optionen eine help-id in `docs/api/admin-ui-reference.md`; die Admin-UI rendert den `fleet`-Block aber nicht (Nicht-Ziel). Help-id trotzdem anlegen? | Nein; Schema-`description` + Howto genügen, Begründung im F1-Plan. | Bei Review von Plan F1. |
| O-F8 | Windows: POSIX-Rechteprüfung der Token-Datei und `chmod 600` sind dort nicht aussagekräftig. Fail closed oder Warnung? | Unter `os.name == "nt"` nur Warnung auf stderr, kein Abbruch. | Bei Review von Plan F1. |
| O-F9 | Q6b-Override bestätigen? Die Alt-Spec-Nutzerantwort Q6 legte die Token-Kette `--fleet-token` > env > `project.yaml` > file fest; diese Spec ersetzt sie (A4/K1). | Nur Env > Token-Datei (kein CLI-Flag, kein Inline-Key); Q6a (Registry Klartext-JSON) bleibt. | Vor Freigabe dieser Spec. |

## Risiken

| ID | Risiko | Auswirkung | Mitigation |
|---|---|---|---|
| R-1 | TLS/Pinning ist Neuland im Repo (kein Bestandscode, Admin-UI plain HTTP) | Fehlkonfiguration, Nutzer weichen auf Loopback/Proxy aus | Fail closed, klare Fehlermeldungen mit Fingerprint-Ausgabe, Howto mit `openssl`-Befehlen; Security-Tests AC-5/AC-7. |
| R-2 | Datei-Überlappung `scripts/admin-server.py` mit Netzplan `SPEC-897-896-ADMIN-UI-NETWORK-2026-10-07` (DRAFT; `AdminServer.__init__`) | Merge-Konflikte | F1 ändert nur additiv `__init__`/`start`, nicht `_admin_start_detached`/`main()`; wer später mergt, rebased. |
| R-3 | Pattern-Redaction für Logs ist best effort | Unbekannte Secret-Formate in Logs könnten durchrutschen | Logs nur aus zwei festen Quellen, ≤ 200 Zeilen auf Anfrage, nicht persistiert; Config strikt per Allowlist; Muster erweiterbar in `TEXT_PATTERNS`. |
| R-4 | Thread-pro-Verbindung in `ThreadingHTTPServer` | Erschöpfung bei vielen Instanzen/Angriffen; jede Instanz hält nahezu permanent einen Long-Poll-Thread | Verbindungslimit an die Instanzzahl gekoppelt (`MAX_INSTANCES + 32` = 288 Threads), 32 Slots für Nicht-Poll-Requests reserviert, 10-s-Header-Deadline, Pre-Auth-Limit je IP, ≤ 256 Instanzen; bei Bedarf späterer Umbau auf `selectors`-basierten Long-Poll (eigene Spec). |
| R-5 | `.meta-viz/` ist in agent-meta gitignored (VERIFIED), in Consumer-Projekten nicht verifiziert | Instanz-Audit/State könnte versehentlich committet werden | Inhalte sind redigiert und tokenfrei; Howto weist auf `.gitignore` hin. |
| R-6 | `sync-status.json` wird nur bei Admin-Server-Syncs geschrieben | „Letzter Sync" zeigt CLI-Syncs nicht bzw. nur über die `sync.log`-mtime ohne Exit-Code | `source`-Feld macht die Herkunft sichtbar; Health `degraded` statt `ok` bei fehlendem Exit-Code. |
| R-7 | Schreibpfad (Phase 3+4) erweitert die Angriffsfläche erheblich | Fremdgesteuerte Syncs/Config-Änderungen | Default aus, instanzseitig autoritativ, Bestätigung, optional Write-Token, Allowlist, Sperrliste, Audit; eigenes Entry-Gate mit Threat-Model-Re-Review. |
| R-8 | Tests sind laut D8 optional | Sicherheitsregressionen bleiben unentdeckt | Security-Pfad-Tests sind **empfohlen (Security)** (Liste im Abschnitt „Tests": fail closed ohne TLS, Token-Auth/Widerruf, `allow-remote-write`-Gate, Redaction) und als eigene Tasks im Plan geführt. |
| R-9 | Client braucht PyYAML (`lib.config.load_config`) | Ohne PyYAML kein Fleet | Fleet wird mit stderr-Hinweis deaktiviert (IC-5); der Server selbst braucht kein YAML. |
| R-10 | Server-State außerhalb des Repos | Agent-gestartete Server/Tests schreiben nach `~` | `--state-dir .tmp/…` für Agent- und Testläufe verpflichtend in Howto und Plan; Repo-Containment greift nur für Agent-Tool-Calls. |
| R-11 | CLI-Subkommandos verlangen gestoppten `serve`-Prozess | Ausstellen/Widerrufen erfordert kurzen Server-Neustart | Bewusste Vereinfachung (keine Mehrprozess-Synchronisation der Registry); Upgrade-Pfad: Admin-Endpunkte für issue/revoke in einer späteren Revision. |
| R-12 | Namenskollision „Fleet" mit Review-Agent-Fleet (#528-#531) | Verwechslung in Doku/Tests | Testdateien `test_fleet_*.py` statt `test_review_fleet.py`-Nähe; Nicht-Ziel-Abgrenzung in Howto übernehmen. |
| R-13 | Leaf-DER-Pin bricht bei automatischer Zertifikatserneuerung (z. B. Let's Encrypt am Reverse-Proxy) | Alle Instanzen melden `pin_mismatch` und werden `offline`, bis der neue Fingerprint verteilt ist | Howto: eigenes langlebiges selbstsigniertes Zertifikat für den Fleet-vHost ohne Auto-Renewal; sonst Zwei-Einträge-Wechsel (`fleet.cert-fingerprint` als Liste mit altem + neuem Pin, neues Zertifikat vorab erzeugen und Pin verteilen, erst dann deployen); Fingerprint immer aus der Zertifikatsdatei auf dem Host, nie per Netzabruf (IC-12). |
| R-14 | `scripts/lib/consistency/spec_plan.py::_classify` erkennt Specs nur über `_DESIGN_RE` (`*-design.md`); `2026-10-23-fleet-server-spec.md` passt auf `_DATED_RE` und wird als **Plan** klassifiziert (VERIFIED). Tatsächliches Verhalten von `--validate-spec-plan`: für die Spec WARNINGs `spec_plan_required_sections` (Plan-Pflichtsektionen `**Goal:**`, `**Architecture:**`, `**Tech Stack:**`, `**Spec:**`, `## Global Constraints`, `## File Structure`, `pipeline_stages` fehlen; WARNING, weil `spec-plan-required` im Preset `rapid-prototyping` nicht `true` ist) und `spec_plan_traceability` „plan has no '**Spec:**' reference" (WARNING, weil `spec-plan-traceability` aus); die Spec-Prüfungen (`REQUIRED_SPEC_SECTIONS`, „spec-id not referenced by any plan") laufen für sie nicht. Für die Pläne F1/F2: `_check_approval_markers` erzeugt ein **ERROR** `spec_plan_approval_marker`, solange die referenzierte Spec kein `Status: APPROVED` trägt und der Plan Tasks/Checkboxen hat — unabhängig vom DoD-Preset. | Fehlklassifikation verdeckt Spec-Pflichtsektions-Prüfung; Pläne sind bis zur Spec-Freigabe ERROR-behaftet | Weder Umbenennung noch Validator-Fix in diesem Vorhaben (Nutzerentscheidung). AC-32 verlangt nur „keine ERROR-Findings" und wird nach der Spec-Freigabe geprüft; die genannten WARNINGs sind akzeptiert. Präzedenzfall mit derselben Lage: `docs/specs/2026-10-11-context-profiles-spec.md`. Follow-up-Empfehlung (eigenes Issue): `_SPEC_RE`/`_DESIGN_RE` in `spec_plan.py` um `-spec.md` erweitern (`_classify` → `spec`). |
| R-15 | Remote-Edit von `ai-providers`/`model-overrides` (und den übrigen Allowlist-Keys ohne Wertprüfung) kann eine Config erzeugen, die erst beim nächsten `sync.py`-Lauf scheitert | Instanz-Sync bricht ab, bis der Wert korrigiert ist | Paritätsentscheidung: Fleet validiert exakt wie `PUT /api/config/project` (IC-15 Schritt 5), keine zusätzliche Fleet-Validierung; Wiederherstellung über das `ConfigManager.write`-Backup; optional anschließendes `trigger-sync mode: validate` als Kontrolle; Einschränkung der Allowlist über O-F3. |
| R-16 | Kein Lock zwischen Admin-UI-Sync (`SyncExecutor.run`/`dry_run` über die Admin-API) und Fleet-`trigger-sync`: `SyncExecutor` hat keinen Ausführungs-Lock (VERIFIED), das Fleet-Busy-Gate (IC-4) gilt nur für Fleet-Writes | Zwei `sync.py`-Läufe können sich überlappen (konkurrierende Schreibzugriffe auf generierte Dateien, `sync-status.json` vom zuletzt endenden Lauf überschrieben) | Plan F2 (F2-B) führt ein gemeinsames, nicht-blockierendes Ausführungs-Gate im `SyncExecutor` ein (Klassen-`threading.Lock`, `acquire(blocking=False)` als erste Anweisung in `_run`, `release` im `finally`). Belegt → `_run` liefert ohne Subprozess und **ohne** `_record_run` (`sync-status.json` unberührt) `{"success": False, "busy": True, "returncode": -1, "output": "sync already running"}`; der Marker `busy` unterscheidet den Fall von Timeout/Exception (ebenfalls `returncode: -1`, aber ohne `busy`). Fleet → Terminal-Ack `error/busy` (IC-14). Beabsichtigte Admin-UI-Verhaltensänderung (heute existiert keine Busy-Antwort, VERIFIED), HTTP-Status unverändert je Route: `POST /api/sync/run`, `/api/sync/dry-run`, `/api/sync/render-standalone`, `/api/models/update` (Nicht-Override-Zweig `_run(["--update-models"])`) → 200 mit Busy-Dict; `/api/roles/cleanup/preview` → 500 `sync_preview_failed`; `/api/roles/cleanup/apply` → 500 `sync_preview_failed` (Recompute) bzw. 500 `sync_failed` (Apply-`run()`), jeweils mit `output: "sync already running"`. AC-54. Abgelehnte Alternative: nur Vorab-Prüfung „läuft ein Admin-UI-Sync?" — hat ein Check-then-act-Fenster. CLI-Syncs außerhalb des Admin-Servers bleiben ungeschützt (Howto-Hinweis). |

## Trace-Anker

`spec-id: SPEC-FLEET-SERVER-2026-10-23` — beide Pläne (F1, F2) müssen diesen Wert und `**Spec:** docs/specs/2026-10-23-fleet-server-spec.md` enthalten.

Task-Gruppen (Planner-Vorgabe, IDs stabil):

| Gruppe | Plan | Inhalt |
|---|---|---|
| F1-A | F1 | Config-Keys, `load_fleet_settings`, Schema-Property, Szenario 79 |
| F1-B | F1 | `fleet_protocol.py` (Token, Fingerprint, `validate_payload`, `AuditLog`) |
| F1-C | F1 | `redaction.py` |
| F1-D | F1 | `fleet-server.py` CLI + Registry + Enrollment/Rotation/Widerruf |
| F1-E | F1 | `fleet-server.py` HTTP-Endpunkte, TLS, Limits |
| F1-F | F1 | `fleet_client.py` (Verbindung/Pinning, Heartbeat, Poll, Lese-Handler `get-logs`, Env-Token-Entfernung) + Hook `admin-server.py` |
| F1-G | F1 | `fleet-ui.html` |
| F1-H | F1 | Doku (Howto, API-Referenz, Querverweis, Alt-Spec-Header) |
| F1-I | F1 | get-config + Config-Ansicht (Phase 2): Lese-Handler `get-config` in `fleet_client.py`, Config-Ansicht in `fleet-ui.html`; nutzt `redact_config` aus F1-C |
| F1-T | F1 | Tests (optional; Security-Tests empfohlen) |
| F2-A | F2 | Server-Write-Gates (Nonce, Write-Token, `write_disabled`) |
| F2-B | F2 | Instanz-Write-Worker `fleet-write`, `command_id`-Dedupe, Write-Handler `trigger-sync`, `put-config`, `apply_config_ops`, `REMOTE_WRITE_ALLOWLIST`, Extraktion `AdminRequestHandler._validate_project_document`, Lösch-Prüfung entfernter Top-Level-Sektionen im `put-config`-Handler (IC-15), gemeinsames Ausführungs-Gate in `SyncExecutor._run` mit Busy-Marker (R-16) |
| F2-C | F2 | Dashboard-Bestätigungsdialog |
| F2-D | F2 | Doku Schreibpfad |
| F2-T | F2 | Tests (optional; Security-Tests empfohlen) |

| AC | Komponente | Datei(en) | Gruppe |
|---|---|---|---|
| AC-1 | C4, C5 | `scripts/lib/fleet_client.py`, `scripts/admin-server.py` | F1-F |
| AC-2, AC-3, AC-4 | C4, C2 | `scripts/lib/fleet_client.py`, `scripts/lib/fleet_protocol.py` | F1-A, F1-B |
| AC-5, AC-6 | C1 | `scripts/fleet-server.py` | F1-E |
| AC-7 | C4, C2 | `scripts/lib/fleet_client.py`, `scripts/lib/fleet_protocol.py` | F1-F |
| AC-8 | C1, C2 | `scripts/fleet-server.py`, `scripts/lib/fleet_protocol.py` | F1-D |
| AC-9, AC-10, AC-11 | C1, C2 | `scripts/fleet-server.py`, `scripts/lib/fleet_protocol.py` | F1-D, F1-E |
| AC-12, AC-13 | C1, C4 | `scripts/fleet-server.py`, `scripts/lib/fleet_client.py` | F1-D, F1-F |
| AC-14 | C1 | `scripts/fleet-server.py` | F1-D |
| AC-15, AC-16 | C4, C2 | `scripts/lib/fleet_client.py`, `scripts/lib/fleet_protocol.py` | F1-F |
| AC-17, AC-18 | C1 | `scripts/fleet-server.py` | F1-E |
| AC-19 | C4 | `scripts/lib/fleet_client.py` | F1-F |
| AC-20 | C3 | `scripts/lib/redaction.py` | F1-C |
| AC-21, AC-22, AC-23, AC-24 | C1 | `scripts/fleet-server.py` | F1-E |
| AC-25, AC-27 | C1 | `scripts/fleet-server.py` | F1-D |
| AC-26 | C2, C1, C4 | `scripts/lib/fleet_protocol.py`, `scripts/fleet-server.py`, `scripts/lib/fleet_client.py` | F1-B |
| AC-28 | C6, C1 | `docs/ui/fleet-ui.html`, `scripts/fleet-server.py` | F1-G |
| AC-29 | C1, C4, C5 | `scripts/fleet-server.py`, `scripts/lib/fleet_client.py`, `scripts/admin-server.py` | F1-D, F1-F |
| AC-30 | C1, C2, C3, C4, C7 | `scripts/lib/fleet_protocol.py`, `scripts/lib/redaction.py`, `scripts/lib/fleet_client.py`, `scripts/fleet-server.py`, `scripts/lib/consistency/python_compat.py` | F1-B, F1-C, F1-E, F1-F |
| AC-31 | C7 | `config/project-config.schema.json`, `tests/scenarios/registry.md`, `tests/scenarios/configs/79-fleet-config-opt-in.project.yaml` | F1-A |
| AC-32 | C8 | `docs/howto/fleet-server.md`, `docs/api/fleet-api-reference.md`, `docs/howto/admin-ui-remote-access.md`, `docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md` | F1-H |
| AC-33, AC-35 | C4 | `scripts/lib/fleet_client.py` | F1-I |
| AC-34 | C3 | `scripts/lib/redaction.py` | F1-C |
| AC-36 | C6 | `docs/ui/fleet-ui.html` | F1-I |
| AC-37, AC-46 | C4, C5 | `scripts/lib/fleet_client.py`, `scripts/admin-server.py` | F2-B |
| AC-38, AC-40 | C1 | `scripts/fleet-server.py` | F2-A |
| AC-39 | C4, C5, C1 | `scripts/lib/fleet_client.py`, `scripts/admin-server.py`, `scripts/fleet-server.py` | F2-B, F2-A |
| AC-41, AC-42, AC-43, AC-44 | C4, C5, C3 | `scripts/lib/fleet_client.py`, `scripts/admin-server.py`, `scripts/lib/redaction.py` | F2-B |
| AC-45 | C4, C6 | `scripts/lib/fleet_client.py`, `docs/ui/fleet-ui.html` | F2-B, F2-C |
| AC-47 | C4, C5 | `scripts/lib/fleet_client.py`, `scripts/admin-server.py` | F1-F |
| AC-48 | C2, C1 | `scripts/lib/fleet_protocol.py`, `scripts/fleet-server.py` | F1-B, F1-E |
| AC-49 | C2, C1, C4 | `scripts/lib/fleet_protocol.py`, `scripts/fleet-server.py`, `scripts/lib/fleet_client.py` | F1-B, F1-D, F1-F |
| AC-50 | C1, C6 | `scripts/fleet-server.py`, `docs/ui/fleet-ui.html` | F1-D, F1-E, F1-G |
| AC-51 | C1 | `scripts/fleet-server.py` | F1-E |
| AC-52 | C4, C1 | `scripts/lib/fleet_client.py`, `scripts/fleet-server.py` | F2-B, F2-A |
| AC-53 | C5, C4 | `scripts/admin-server.py`, `scripts/lib/fleet_client.py` | F2-B |
| AC-54 | C5, C4 | `scripts/admin-server.py` (`SyncExecutor`), `scripts/lib/fleet_client.py` | F2-B |
