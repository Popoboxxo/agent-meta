---
status: geplant
spec-id: SPEC-FLEET-SERVER-2026-10-23
pipeline_stages:
  implement: 3
---

# Fleet-Server F1 (Phase 1+2: Read-Only-Dashboard + Config-Ansicht) Implementation Plan

> Status: geplant

> **Freigabe-Gate:** Dieser Plan ist erst ausführbar, wenn die Spec `docs/specs/2026-10-23-fleet-server-spec.md` (Rev. 1.4) vom Nutzer auf `Status: APPROVED` gesetzt wurde (Entry-Kriterium E1). Bis dahin meldet `python3 scripts/sync.py --validate-spec-plan` für diesen Plan den erwarteten ERROR `spec_plan_approval_marker` (Spec R-14); das ist kein Planfehler.
>
> **Hinweis zu den Test-Tasks (Nutzerentscheidung D8, DoD `rapid-prototyping`):** Test-Tasks (Tasks 21 bis 27) sind separate, klar markierte Tasks pro Komponente und **kein Merge-Gate**. Die als **empfohlen (Security)** markierten Test-Tasks decken die sicherheitskritischen Pfade ab (fail closed ohne TLS, Pinning, Token-Auth/Widerruf/Rotation, Redaction, Audit/Secret-Dateien, Verbindungslimits). Ihre Umsetzung wird **dringend empfohlen**, auch wenn sie formal übersprungen werden dürfen (Spec R-8).

**Goal:** Opt-in-Instanzen melden sich per Push/Phone-Home bei einem selbst gehosteten `scripts/fleet-server.py`, senden Status-Heartbeats, liefern redigierte Log-Auszüge (Phase 1) und die allowlist-redigierte `project.yaml` (Phase 2); ein statisches Dashboard `docs/ui/fleet-ui.html` zeigt alle Instanzen mit Liveness `online|stale|offline|never`. Ohne `fleet.enabled: true` entsteht keine Netzverbindung, kein Thread, keine Datei.
**Architecture:** Drei neue lib-Module (`fleet_protocol.py` Wire-Vertrag + Sicherheitsprimitive + Audit, `redaction.py` allgemeine Redaction, `fleet_client.py` Instanz-Client) plus der Server-Prozess `scripts/fleet-server.py` (Registry, Kommando-Vermittlung, Enrollment-CLI, TLS, Limits). Der Client wird nur über einen Hook von höchstens 25 Zeilen in `AdminServer.__init__`/`AdminServer.start` gestartet. Transport ausschließlich HTTP-Long-Poll (A3), TLS mit Fingerprint-Pinning (A8), Token als SHA-256-Hash in der Registry (A5). F1 enthält strukturell keinen Write-Handler (Kommandos `trigger-sync`/`put-config` → `unknown_command`).
**Tech Stack:** Python 3.9/3.11/3.12 (nur Stdlib; PyYAML nur indirekt über `lib.config.load_config` im Client), `http.server.ThreadingHTTPServer`, `http.client`, `ssl`, `hmac`, `secrets`, Vanilla-HTML/JS/CSS, pytest, Bash-Szenarien (`tests/scenarios/run.sh`).
**Spec:** docs/specs/2026-10-23-fleet-server-spec.md
**Spec-ID:** `spec-id: SPEC-FLEET-SERVER-2026-10-23` (Rev. 1.4, Entwurf; Primärquelle GitHub-Issue #682 §7)
**Branch:** `feat/fleet-server-f1` (kein Worktree, siehe `.claude/rules/no-worktree-isolation.md`)
**Estimated effort:** Gesamtaufwand und Gruppenaufwand schätzt `effort-estimator` (Textverweis, keine eigene Zahl in diesem Plan).
**Assumptions:** (A-1) Spec Rev. 1.4 wird unverändert freigegeben; ändert sich ein IC, sind die betroffenen Tasks neu zu planen. (A-2) O-F1 (nur Long-Poll; SSE ist die einzige verworfene Alternative) und O-F9 (Token-Kette nur Env > Token-Datei) sind vom Nutzer am 2026-10-28 bestätigt und geschlossen; die Defaults aus O-F7 und O-F8 gelten, falls unbeantwortet (siehe Entry-Kriterien). (A-3) `openssl` ist auf dem Testhost vorhanden (sonst werden TLS-Tests per `pytest.skip` übersprungen). (A-4) Das Szenario mit der Nummer 79 ist beim Start von Task 1 frei (siehe Risiko im Abschnitt „Merge-Reihenfolge“). (A-5) Doku-Tasks 18 bis 20 laufen über die Rolle `documenter` (existiert unter `.claude/agents`). (A-6) In Spec Rev. 1.4 übernommen (IC-4/IC-5): `load_fleet_settings(root, env_token_present: bool = False)` (Task 6, Task 14).
**Re-planning:** Nach jeder Task-Gruppe (Abschnitt „Task-Gruppen“) Annahmen prüfen: Sind IC-Signaturen unverändert, ist die Reihenfolge noch richtig, kollidiert ein inzwischen gemergter Plan (Netzplan, Opencode-v2) mit `scripts/admin-server.py` oder der Szenario-Nummer 79? Plan aktualisieren, nicht einfrieren.

## Task-Gruppen und Phasen

| Gruppe | Phase | Tasks | Inhalt |
|---|---|---|---|
| F1-A | 1 | 1, 6 | Schema-Property `fleet`, Szenario 79, `FleetSettings`/`load_fleet_settings` |
| F1-B | 1 | 3, 4, 5 | `fleet_protocol.py` (Token, Fingerprint, Secret-Dateien, `validate_payload`, `AuditLog`) |
| F1-C | 1 | 2, 11 | `redaction.py`; Python-3.9-Check-Erweiterung `_SCAN_FILES` (C7) |
| F1-D | 1 | 7, 8 | `fleet-server.py` Registry, Enrollment/Rotation/Widerruf, CLI |
| F1-E | 1 | 9, 10 | `fleet-server.py` HTTP-Endpunkte, Kommando-Vermittlung, TLS, Limits |
| F1-F | 1 | 12, 13, 14 | `fleet_client.py` (Verbindung/Pinning, Heartbeat, Poll, `get-logs`, Status) + Admin-Hook |
| F1-G | 1 | 16 | `fleet-ui.html` (Instanztabelle, Detail, Logs) |
| F1-H | 1 | 18, 19, 20 | Doku (Howto, API-Referenz, Querverweis, Alt-Spec-Header) |
| F1-I | 2 | 15, 17 | `get-config` Handler und Config-Ansicht im Dashboard |
| F1-T | 1+2 | 21 bis 27 | Tests je Komponente (optional, D8; Security-Tests empfohlen) |
| F1-V | 1+2 | 28, 29 | End-to-End-Verifikation und Abschluss-Validierung (Exit-Kriterien) |

## Task-Übersicht (Schritt → Agent)

| Schritt | Titel | Agent |
|---|---|---|
| 1 | Schema-Property `fleet` und Szenario 79 | developer |
| 2 | `redaction.py` | senior-developer |
| 3 | `fleet_protocol.py` Kern | senior-developer |
| 4 | `validate_payload` und Wire-Schemas | developer |
| 5 | `AuditLog` | senior-developer |
| 6 | `FleetSettings` und `load_fleet_settings` | senior-developer |
| 7 | Registry und Enrollment-Zustandsmaschine | senior-developer |
| 8 | Server-CLI | developer |
| 9 | Kommando-Broker und HTTP-Endpunkte | senior-developer |
| 10 | Transport: TLS, Verbindungslimits, `serve` | senior-developer |
| 11 | Python-3.9-Check deckt `fleet-server.py` ab | developer |
| 12 | `FleetClient` Kern | senior-developer |
| 13 | Lese-Handler `get-logs`, Status, `read_last_sync` | senior-developer |
| 14 | Admin-Hook und Env-Token-Entfernung | senior-developer |
| 15 | Lese-Handler `get-config` (Phase 2) | senior-developer |
| 16 | Dashboard `fleet-ui.html` | developer |
| 17 | Config-Ansicht im Dashboard (Phase 2) | developer |
| 18 | Howto `fleet-server.md` | documenter |
| 19 | API-Referenz `fleet-api-reference.md` | documenter |
| 20 | Querverweis und Hinweis-Header der Alt-Spec | documenter |
| 21 | Tests `fleet_protocol` | tester |
| 22 | Tests `redaction` | tester |
| 23 | Tests `fleet_client` Teil 1 | tester |
| 24 | Tests `fleet_client` Teil 2 | tester |
| 25 | Tests Admin-Hook | tester |
| 26 | Tests Server Teil 1 | tester |
| 27 | Tests Server Teil 2 | tester |
| 28 | End-to-End-Lauf | tester |
| 29 | Abschluss-Validierung | tester |

## Abhängigkeitsgraph

```
1 ─────────────┐ (g1)
2 ──────┐      │
3 ──┬───┼──┐   │
    │   │  │   │
    4 ──┴─ 5 ──┼──────────────┐
    │          │              │
    6 (g2)     7 (g2) ─ 8 ─ 9 ─ 10 ─ 11
    │                          │
    12 ─ 13 ─ 14               16 ─ 17
         └─ 15 ────────────────────┘
18,19 (g4) nach 10/14 · 20 (g4) ohne Abhängigkeit
Tests: 21←5, 22←2, 23←12,9, 24←15,23, 25←14,24, 26←8, 27←10,16,26 · 28←14,17,18,20 · 29←1,11,19,28 (keine Test-Tasks, D8)
```

Parallel-Gruppen (nur dateidisjunkte Tasks, per `Files:` belegt):
- `parallel_group: f1-g1` — Tasks 1, 2, 3 (Schema/Szenario ∥ `redaction.py` ∥ `fleet_protocol.py`).
- `parallel_group: f1-g2` — Tasks 6, 7 (`fleet_client.py` ∥ `fleet-server.py`).
- `parallel_group: f1-g4` — Tasks 18, 19, 20 (drei disjunkte Doku-Dateien).
- Alle übrigen Tasks sequenziell (gemeinsame Dateien `fleet_protocol.py`, `fleet-server.py`, `fleet_client.py`, `fleet-ui.html`, `tests/test_fleet_*.py`).

## Entry-Kriterien (alle vor Start von Task 1 belegen)

- **E1** Spec `docs/specs/2026-10-23-fleet-server-spec.md` trägt `Status: APPROVED` (Freigabe durch den Nutzer, kein Self-Approve). Nachweis: `grep -n "Status: APPROVED" docs/specs/2026-10-23-fleet-server-spec.md` liefert eine Zeile.
- **E2** (erledigt) O-F1 (nur Long-Poll, SSE verworfen) und O-F9 (Token-Kette nur Env > Token-Datei) sind geschlossen, vom Nutzer bestätigt am 2026-10-28; kein offener Entscheidungspunkt.
- **E3** O-F7 (keine help-id in `docs/api/admin-ui-reference.md`) und O-F8 (Windows: nur Warnung) beim Review dieses Plans entschieden. Begründung zu O-F7: Die Admin-UI rendert den `fleet`-Block nicht (Spec Nicht-Ziel); Schema-`description` und Howto ersetzen die help-id.
- **E4** Arbeitsbranch `feat/fleet-server-f1` von `main` (Konvention `.claude/rules/branch-guard.md`).
- **E5** Szenario-Nummer 79 frei: `ls tests/scenarios/configs/ | grep '^79-'` liefert nur dann eine Datei, wenn sie `79-fleet-config-opt-in` heißt. Der Entwurf `docs/plans/2026-10-22-opencode-v2-support-plan.md` reserviert ebenfalls `79-opencode-v2-full-surface` (Spec O-F10, Entscheidung bei Freigabe; Default: first-to-merge behält 79); bei Kollision wird die nächste freie Nummer verwendet und die Spec (AC-31, IC-1, Trace-Anker) per Revision nachgezogen, bevor Task 1 startet.

## Global Constraints

- **Nur Stdlib** (Konvention CLAUDE.md); keine neuen Abhängigkeiten. `fleet_client.py` darf zusätzlich bestehende `lib`-Module (`lib.config.load_config`) nutzen; Server und `fleet_protocol.py` benötigen kein PyYAML.
- **Python 3.9-kompatibel** für alle neuen Module **einschließlich `scripts/fleet-server.py`**: `from __future__ import annotations` als erste Anweisung, kein `match`, kein `X | Y` zur Laufzeit außerhalb von Annotationen; Check `scripts/lib/consistency/python_compat.py` (Task 11) grün.
- **Provider-agnostisch** (Skill `provider-agnostic`): Provider ausschließlich über die Liste `ai-providers` aus `project.yaml` durchreichen; kein `if provider == "Name"`, kein Vergleich gegen Provider-Namensliterale (AC-15).
- **Modulgrößen:** `fleet_client.py` ≤ 600 Zeilen, `fleet_protocol.py` ≤ 350, `redaction.py` ≤ 250, `fleet-server.py` ≤ 900 (Spec Architektur). `scripts/admin-server.py` wächst um höchstens 25 Zeilen; `main()`, `_admin_start_detached`, `AuthService`, Routing-Tabellen bleiben **unverändert** (AC-29).
- **Secrets:** Kein Token in argv, URL oder stdout; Token nur in `Authorization: Bearer`; Vergleiche nur per `hmac.compare_digest`; Secret-Dateien nur über `create_private_file` (`O_CREAT|O_EXCL|O_WRONLY`, 0600 ab Erzeugung, kein nachträgliches `os.chmod`); Temp-Dateien über `private_temp_path`; keine privaten Schlüssel im Repo (Test-Zertifikate zur Laufzeit per `openssl req -x509` in `tmp_path`).
- **Repo-Containment (R-10):** Server-State standardmäßig `~/.agent-meta-fleet`; alle Agent- und Testläufe verwenden `--state-dir .tmp/fleet-<name>` bzw. pytest-`tmp_path`; Server binden in Tests nur `127.0.0.1` auf freien Ports.
- **Keine Änderung** an `GET /api/config/<key>` der Admin-UI, an `docs/api/admin-ui-reference.md` (O-F7) und kein Split von `scripts/admin-server.py`.
- **Tests (D8):** Test-Tasks sind eigene Tasks, kein Merge-Gate. Impl-Tasks enden mit einem Smoke-Kommando (kleinster Beobachtungsnachweis), nicht mit einer Testsuite.
- **Commits:** Conventional Commits, Englisch, ≤ 72 Zeichen in Zeile 1, Imperativ. Die per `auto_commit` freigeschaltete Rolle meldet Dateien + Message je Task-Grenze; Push/Tag/Branch nur `git`-Rolle. Vor jedem Commit läuft der Secret-Scan über die gemeldeten Dateien.
- **Sprachen:** Doku Deutsch, Code/Kommentare/Commits Englisch.

## File Structure

**Neu:**
- Create: `scripts/lib/fleet_protocol.py` — Wire-Konstanten, Token-Hashing, Fingerprint, `resolve_secret`, private Dateien, `validate_payload`, `AuditLog` (C2)
- Create: `scripts/lib/redaction.py` — `redact_text`, `redact_config`, `contains_redaction_marker` (C3)
- Create: `scripts/lib/fleet_client.py` — `FleetSettings`, `load_fleet_settings`, `FleetClient`, `read_last_sync`, `tail_log` (C4)
- Create: `scripts/fleet-server.py` — Registry, Broker, HTTP(S)-Server, CLI (C1)
- Create: `docs/ui/fleet-ui.html` — Dashboard (C6)
- Create: `docs/howto/fleet-server.md` — Betrieb (C8)
- Create: `docs/api/fleet-api-reference.md` — Endpunkte, Schemas, Fehlercodes, Limits (C8)
- Create: `tests/scenarios/configs/79-fleet-config-opt-in.project.yaml`, `tests/scenarios/asserts/79-fleet-config-opt-in.sh` — Szenario 79 (`chmod +x`)
- Create (Tests, D8): `tests/test_fleet_protocol.py`, `tests/test_redaction.py`, `tests/test_fleet_client.py`, `tests/test_fleet_server.py`

**Geändert:**
- Modify: `config/project-config.schema.json` — Top-Level-Property `fleet` (draft-07, analog `admin-ui`)
- Modify: `tests/scenarios/registry.md` — Katalogzeile `79-fleet-config-opt-in`
- Modify: `scripts/lib/consistency/python_compat.py` — `_SCAN_FILES`, `_iter_py_files`
- Modify: `scripts/admin-server.py` — `_maybe_create_fleet_client`, `AdminServer.__init__`, `AdminServer.start` (≤ 25 Zeilen)
- Modify: `docs/howto/admin-ui-remote-access.md` — Abschnitt „Mehrere Repos zentral überwachen“ + Link
- Modify: `docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md` — Hinweis-Header (Datei bleibt erhalten)

**Nicht angefasst (bewusst):** `scripts/lib/cli_commands.py`, `scripts/sync.py` (konsumiert `fleet.*` nicht), `docs/api/admin-ui-reference.md` (O-F7), `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md`, `docs/plans/admin-server-split-backlog.md`.

---

## Phase 1 — Fundament (Gruppen F1-A bis F1-H)

### Task 1: F1-A — Schema-Property `fleet` und Szenario 79
**Agent:** developer
**Depends on:** —
**parallel_group:** f1-g1
**ACs:** AC-31 · **Spec:** IC-1
**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `tests/scenarios/registry.md`
- Create: `tests/scenarios/configs/79-fleet-config-opt-in.project.yaml`
- Create: `tests/scenarios/asserts/79-fleet-config-opt-in.sh`
**Interfaces:** Produces Schema-Property `fleet` (Keys `enabled`, `url`, `token-file`, `cert-fingerprint`, `allow-remote-write`, `heartbeat-interval`, `additionalProperties: false`, JSON exakt wie in IC-1); Szenario `79-fleet-config-opt-in`. Consumes Schema-Vorlage `admin-ui` in `config/project-config.schema.json`; Szenario-Konvention `tests/scenarios/run.sh` (Config + optionaler ausführbarer Assert unter `asserts/<name>.sh`, cwd = Temp-Projekt, `$1` = `REPO_ROOT`).
- [ ] Step 1: E5 prüfen (`ls tests/scenarios/configs/ | grep '^79-'`); Szenario-Config anlegen: Kopie einer bestehenden Claude-Szenario-Config (z. B. `tests/scenarios/configs/44-speech-mode-childish.project.yaml`) ergänzt um `fleet: {enabled: true, url: "http://127.0.0.1:7430", token-file: ".tmp/fleet-79.token", allow-remote-write: false, heartbeat-interval: 30}`. Dieser Zustand ist der Rot-Zustand: `python3 -c "import json,jsonschema"` ist nicht nötig; stattdessen beobachten, dass der Assert (Step 2) ohne Schema-Property fehlschlägt: `grep -c '"fleet"' config/project-config.schema.json` → `0`.
- [ ] Step 2: `asserts/79-fleet-config-opt-in.sh` (Bash, `set -eu`, `chmod +x`): (a) im Temp-Projekt `test -f .meta-config/project.yaml` und `grep -q '^fleet:' .meta-config/project.yaml`; (b) `! find . -path ./.meta-config -prune -o -iname '*fleet*' -print | grep -q .` (der generierte Baum enthält keine Fleet-Datei; sync.py konsumiert `fleet.*` nicht); (c) `python3 -c "import json,sys; s=json.load(open(sys.argv[1]+'/config/project-config.schema.json')); p=s['properties']['fleet']; assert p['additionalProperties'] is False and set(p['properties'])=={'enabled','url','token-file','cert-fingerprint','allow-remote-write','heartbeat-interval'}" "$1"`.
- [ ] Step 3: Property `fleet` unmittelbar nach der Property `admin-ui` in `config/project-config.schema.json` einfügen (JSON-Block exakt aus IC-1); Katalogzeile in `tests/scenarios/registry.md` nach Zeile `78-meta-optimizer-role`: `| \`79-fleet-config-opt-in\` | Claude | strict (default) | Opt-in \`fleet\`-Block (SPEC-FLEET-SERVER-2026-10-23, AC-31): Schema akzeptiert alle Keys, sync/dry-run/--validate laufen fehlerfrei, generierter Baum enthält keine Fleet-Datei |`.
- [ ] Step 4: Verifikation: `python3 -c "import json; json.load(open('config/project-config.schema.json'))"` → Exit 0; `tests/scenarios/run.sh 79` → `PASS  79-fleet-config-opt-in`, `Scenarios: 1  Passed: 1  Failed: 0`; `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 5: commit `feat: add fleet config schema property and scenario 79`

### Task 2: F1-C — `redaction.py` (Allowlist-Config-Redaction, Pattern-Text-Redaction)
**Agent:** senior-developer
**Depends on:** —
**parallel_group:** f1-g1
**ACs:** AC-20, AC-34 (Quelle), AC-30 (3.9) · **Spec:** IC-3, D7, R-3
**Files:**
- Create: `scripts/lib/redaction.py`
**Interfaces:** Produces `REDACTED: str = "[REDACTED]"`, `CONFIG_VIEW_ALLOWLIST: tuple[str, ...]` (26 Einträge exakt wie IC-3), `SECRET_KEY_RE`, `TEXT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...]`, `redact_text(text: str) -> str`, `redact_config(data: Mapping[str, Any], allowlist: Sequence[str] = CONFIG_VIEW_ALLOWLIST) -> dict[str, Any]`, `contains_redaction_marker(value: Any) -> bool`. Consumes: Muster aus `hooks/1-generic/lib/hook_common.sh::hook_redact_secrets` (1:1-Port der acht Muster in gleicher Reihenfolge: Bearer vor key=value) plus `amf_`-Muster und PEM-Private-Key-Block; keine Fleet-Abhängigkeit (A7).
- [ ] Step 1: Rot-Zustand: `PYTHONPATH=scripts python3 -c "from lib import redaction"` → `ModuleNotFoundError: No module named 'lib.redaction'`.
- [ ] Step 2: Muster aus `hook_redact_secrets` in `hooks/1-generic/lib/hook_common.sh` lesen und nach `TEXT_PATTERNS` portieren (URL-Basic-Auth, `Authorization: Bearer`, `bearer <token>`, `key=value`/`key: value` für token/api_key/secret/password/auth, `--token`/`--password <v>`, `ghp_/gho_/ghs_/ghu_/ghr_/github_pat_`, `xox[baprs]-`, `AKIA…`); ergänzen: `\bamf_[A-Za-z0-9_\-]{20,}` → `amf_***`, PEM-Block → `[REDACTED PRIVATE KEY]`. `redact_text` wendet sie in Tupel-Reihenfolge an.
- [ ] Step 3: `redact_config` nach den Regeln 1 bis 6 aus IC-3 implementieren: Pfade punktgetrennt; Teilbaum ohne Allowlist-Treffer als Ganzes `REDACTED` (Key bleibt sichtbar); tiefer Allowlist-Eintrag (z. B. `admin-ui.port`) lässt den Eltern-Key als Mapping, nicht gelistete Geschwister werden `REDACTED`; Backstop in sichtbaren Teilbäumen: Keys mit `SECRET_KEY_RE` → `REDACTED`, String-Werte durch `redact_text`; Listen elementweise wie der Eltern-Pfad; Deep-Copy, Nicht-Mapping-Eingabe → `{}`; kein Zugriff auf `.meta-config/secrets.local.yaml`. `contains_redaction_marker` rekursiv (`REDACTED` oder `***` aus `TEXT_PATTERNS`).
- [ ] Step 4: Smoke: `PYTHONPATH=scripts python3 -c "from lib import redaction as r; print(r.redact_text('curl -H \"Authorization: Bearer abc123def456ghi789\" ghp_0123456789abcdefghijklmnopqrstuvwxyz12'))"` → Ausgabe enthält weder `abc123def456ghi789` noch `ghp_0123`; `PYTHONPATH=scripts python3 -c "from lib import redaction as r; d={'variables':{'a':'b'},'admin-ui':{'port':7420,'token':'x'}}; print(r.redact_config(d))"` → `{'variables': '[REDACTED]', 'admin-ui': {'port': 7420, 'token': '[REDACTED]'}}`; `wc -l scripts/lib/redaction.py` ≤ 250.
- [ ] Step 5: commit `feat: add redaction module for fleet config and log views`

### Task 3: F1-B — `fleet_protocol.py` Kern (Token, Fingerprint, Secret-Dateien)
**Agent:** senior-developer
**Depends on:** —
**parallel_group:** f1-g1
**ACs:** AC-4 (Quelle), AC-11, AC-29, AC-49, AC-30 · **Spec:** IC-2, A4, A5, A8, O-F8
**Files:**
- Create: `scripts/lib/fleet_protocol.py`
**Interfaces:** Produces Konstanten (`PROTOCOL_VERSION`, `TOKEN_PREFIX`, `DEFAULT_PORT = 7430`, `ENV_INSTANCE_TOKEN`, `ENV_ADMIN_TOKEN`, `LOOPBACK_HOSTS`, `READ_COMMANDS`, `WRITE_COMMANDS`), `class FleetProtocolError(ValueError)` mit Attribut `code: str`, `new_token() -> str`, `hash_token(token: str) -> str`, `token_matches(token: str, token_hash: str) -> bool`, `normalize_fingerprint(value: str) -> str`, `cert_fingerprint(der: bytes) -> str`, `is_loopback(host: str) -> bool`, `resolve_secret(env_var: str, token_file: Path | None) -> str | None`, `create_private_file(path: Path) -> int`, `private_temp_path(target: Path) -> Path`, `cleanup_private_temps(directory: Path, names: Sequence[str]) -> int`, `utc_now_iso() -> str`. Consumes: nur Stdlib (`hashlib`, `hmac`, `secrets`, `os`, `re`, `datetime`).
- [ ] Step 1: Rot-Zustand: `PYTHONPATH=scripts python3 -c "from lib import fleet_protocol"` → `ModuleNotFoundError`.
- [ ] Step 2: Modul mit `from __future__ import annotations` anlegen; Konstanten und Funktionen nach IC-2. `token_matches`: leere Werte → `False`, sonst `hmac.compare_digest(hash_token(token), token_hash)`. `normalize_fingerprint`: `:`-Trenner entfernen, `sha256:`-Präfix case-insensitive, exakt 64 Hex, sonst `FleetProtocolError("invalid_fingerprint")`. `is_loopback`: Mitgliedschaft in `LOOPBACK_HOSTS`.
- [ ] Step 3: `resolve_secret`: Env zuerst; Datei: `fd = os.open(path, os.O_RDONLY)`, `os.fstat(fd)` auf demselben fd; POSIX (`os.name != "nt"`) Group-/Other-Bits → `FleetProtocolError("insecure_token_file")`; unter `nt` nur Warnung auf stderr (O-F8-Default); Lesen über denselben fd, `strip()`; kein `os.stat` vor dem `open` (TOCTOU, AC-49).
- [ ] Step 4: `create_private_file`: `os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)`; `private_temp_path`: `target.parent / f".{target.name}.{secrets.token_hex(8)}.tmp"`; `cleanup_private_temps`: entfernt nur Dateien mit exaktem Regex `^\.<escaped name>\.[0-9a-f]{16}\.tmp$` für die übergebenen Namen, liefert die Anzahl. `utc_now_iso`: `YYYY-MM-DDTHH:MM:SSZ`.
- [ ] Step 5: Smoke (Erwartung `True True`, `sha256:`-Länge 71): `PYTHONPATH=scripts python3 -c "from lib import fleet_protocol as p; t=p.new_token(); h=p.hash_token(t); print(t.startswith('amf_'), p.token_matches(t,h), len(h))"` → `True True 71`; Grep-Prüfung AC-11/AC-49: `grep -nE "token *==|hash *==|os\.chmod|os\.stat\(" scripts/lib/fleet_protocol.py` → keine Treffer (Exit 1).
- [ ] Step 6: commit `feat: add fleet protocol primitives for tokens and private files`

### Task 4: F1-B — `validate_payload` und Wire-Schemas
**Agent:** developer
**Depends on:** 3
**ACs:** AC-15 (Voraussetzung), AC-24 (Typprüfung) · **Spec:** IC-2, IC-7
**Files:**
- Modify: `scripts/lib/fleet_protocol.py`
**Interfaces:** Produces `SCHEMAS: dict[str, dict]` mit den Schemas `fleet-enroll-v1`, `fleet-status-v1`, `fleet-command-v1`, `fleet-ack-v1`, `fleet-instances-v1` (Inhalt wörtlich aus IC-7) und `validate_payload(schema: str, obj: object) -> list[str]` (leere Liste = gültig; Fehlerstrings nennen den Feldpfad). Consumes Schemas aus IC-7. Unterstützte Teilmenge: `type` (auch Liste von Typen inkl. `null`), `required`, `properties`, `enum`, `maxLength`, `maxItems`, `minimum`, `maximum`, `pattern`, `items`.
- [ ] Step 1: Rot-Zustand: `PYTHONPATH=scripts python3 -c "from lib.fleet_protocol import validate_payload"` → `ImportError: cannot import name 'validate_payload'`.
- [ ] Step 2: `SCHEMAS` und rekursiven Validator implementieren; unbekanntes Schema → `FleetProtocolError("schema_invalid")`; `bool` ist kein `integer`; unbekannte Zusatz-Properties sind erlaubt, nur dokumentierte werden geprüft.
- [ ] Step 3: Smoke: `PYTHONPATH=scripts python3 -c "from lib.fleet_protocol import validate_payload as v; print(v('fleet-ack-v1', {'command_id':'c','status':'ok'}), v('fleet-ack-v1', {'status':'bogus'}))"` → `[] ['…']` (zweite Liste nicht leer, nennt `command_id` und `status`); `wc -l scripts/lib/fleet_protocol.py` ≤ 350 nach Task 5.
- [ ] Step 4: commit `feat: add fleet wire schemas and payload validator`

### Task 5: F1-B — `AuditLog` (JSONL, Rotation, Aggregation)
**Agent:** senior-developer
**Depends on:** 2, 4
**ACs:** AC-26, AC-48, AC-49 · **Spec:** IC-2, IC-9
**Files:**
- Modify: `scripts/lib/fleet_protocol.py`
**Interfaces:** Produces `class AuditLog` mit `__init__(self, path: Path, side: str) -> None` (`side` ∈ {`server`, `instance`}), `append(self, event: str, *, outcome: str, instance_id: str | None = None, command_id: str | None = None, command: str | None = None, actor: str | None = None, detail: str = "") -> None`, `aggregate(self, event: str, source_ip: str) -> None`, Konstante `AUDIT_EVENTS: frozenset[str]` (18 Ereignisse aus IC-9). Consumes `scripts/lib/redaction.py::redact_text` (Task 2), `create_private_file`, `private_temp_path` (Task 3).
- [ ] Step 1: Rot-Zustand: `PYTHONPATH=scripts python3 -c "from lib.fleet_protocol import AuditLog"` → `ImportError`.
- [ ] Step 2: `append`: JSONL-Zeile mit den Feldern `ts, side, event, outcome, instance_id, command_id, command, actor, detail` (`detail` ≤ 200 Zeichen, durch `redact_text`); Öffnen mit `os.open(path, os.O_CREAT | os.O_APPEND | os.O_WRONLY, 0o600)` und `os.fchmod(fd, 0o600)` auf demselben fd; wirft nie (Fehler → einmalige stderr-Warnung); unbekannter Event-Name wird trotzdem geschrieben.
- [ ] Step 3: Rotation: nach dem Schreiben bei > 2000 Zeilen auf die neuesten 1000 kürzen, atomar über `create_private_file(private_temp_path(path))` + `os.fsync` + `os.replace`; bei Fehler Temp-Datei per `os.unlink` entfernen (best effort).
- [ ] Step 4: `aggregate(event, source_ip)`: zählt je Ereignistyp (`auth_failed`, `tls_refused`) unter `threading.Lock`; schreibt höchstens eine Zeile pro Minute mit `detail = "count=<N> ips=<bis zu 5 Quell-IPs, häufigste zuerst>"` (Zeitfenster per injizierbarer `time.monotonic`-Quelle als Konstruktor-Argument `clock`).
- [ ] Step 5: Smoke: `PYTHONPATH=scripts python3 -c "import tempfile,pathlib,json; from lib.fleet_protocol import AuditLog; d=pathlib.Path(tempfile.mkdtemp(dir='.tmp')) if pathlib.Path('.tmp').is_dir() else pathlib.Path(tempfile.mkdtemp()); a=AuditLog(d/'a.log','server'); [a.aggregate('auth_failed','10.0.0.%d'%(i%3)) for i in range(1000)]; a.append('issue',outcome='ok',detail='token=abc12345678901234567'); print(len((d/'a.log').read_text().splitlines()), oct((d/'a.log').stat().st_mode&0o777))"` → `2 0o600` (eine aggregierte Zeile, eine `issue`-Zeile; `detail` des Letzteren redigiert); `wc -l scripts/lib/fleet_protocol.py` ≤ 350.
- [ ] Step 6: commit `feat: add fleet audit log with rotation and aggregation`

### Task 6: F1-A — `FleetSettings` und `load_fleet_settings`
**Agent:** senior-developer
**Depends on:** 3
**parallel_group:** f1-g2
**ACs:** AC-2, AC-3, AC-4, AC-1 (Teil: `None` bei Opt-out), AC-47 (Env-only-Betrieb) · **Spec:** IC-1, IC-4, IC-5, A4
**Files:**
- Create: `scripts/lib/fleet_client.py`
**Interfaces:** Produces `@dataclass(frozen=True) class FleetSettings` (`url, host, port, use_tls, token_file, fingerprints, allow_remote_write, heartbeat_interval`), `class FleetConfigError(ValueError)` mit Attribut `code` ∈ {`tls_required`, `fingerprint_required`, `invalid_url`, `invalid_interval`, `token_missing`, `insecure_token_file`, `invalid_fingerprint`}, `load_fleet_settings(root: Path, env_token_present: bool = False) -> FleetSettings | None` (`env_token_present=True` bedeutet: Env-Token wurde vom Hook bereits entfernt und an `FleetClient(env_token=...)` übergeben; Spec IC-4/IC-5 Rev. 1.4, siehe A-6), Konstanten `STATE_FILE = ".meta-viz/fleet-state.json"`, `AUDIT_FILE = ".meta-viz/fleet-audit.log"`, `LOG_SOURCES = {"sync": "sync.log", "admin-server": ".meta-viz/admin-server.log"}`. Consumes `lib.config.load_config(config_path: Path)`, `fleet_protocol.normalize_fingerprint`, `is_loopback`, `resolve_secret`, `ENV_INSTANCE_TOKEN`.
- [ ] Step 1: Rot-Zustand: `PYTHONPATH=scripts python3 -c "from lib import fleet_client"` → `ModuleNotFoundError`.
- [ ] Step 2: `load_fleet_settings`: Config laden (`root / ".meta-config" / "project.yaml"`, fehlende Datei → `None`); Block fehlt oder `enabled` nicht `True` → `None`; URL per `urllib.parse.urlsplit` (nur `http`/`https`, kein Pfad/Query/Fragment, sonst `invalid_url`); `http` + Nicht-Loopback → `tls_required`; `https` ohne Fingerprint → `fingerprint_required`; Fingerprints (String oder Liste ≤ 2) über `normalize_fingerprint` (→ `invalid_fingerprint`); Intervall 10 bis 300 (→ `invalid_interval`); Token-Datei relativ zum Root oder absolut, `~` expandiert; weder `env_token_present` (reine Präsenzprüfung des Parameters, kein Lesen/Pop der Env-Variable) noch `token-file` → `token_missing`; unbekannte Keys unter `fleet` → stderr-Warnung. Die Modusprüfung der Token-Datei (`insecure_token_file`) erfolgt über `resolve_secret` beim Laden (Datei vorhanden → prüfen und `FleetProtocolError` in `FleetConfigError("insecure_token_file")` übersetzen).
- [ ] Step 3: Der Env-Token wird hier **nicht** gelesen (IC-4/IC-5: Entfernung per `os.environ.pop` in Task 14); `token_missing` entfällt, wenn `env_token_present=True` (Hook übergibt `env_token is not None`) oder `token-file` gesetzt ist. Plan-Abweichung/Klarstellung: Der Parameter `env_token_present` ergänzt die Signatur `load_fleet_settings(root)` aus Spec IC-4, damit Env-only-Betrieb (AC-47 Satz 2) nach dem Pop nicht an `token_missing` scheitert; in Spec Rev. 1.4 übernommen (IC-4/IC-5).
- [ ] Step 4: Smoke (je Fall in einem Temp-Projekt unter `.tmp/`): `fleet: {enabled: true, url: "http://10.0.0.5:7430", token-file: t}` → `FleetConfigError` mit `code == "tls_required"`; `https://…` ohne Fingerprint → `fingerprint_required`; Block fehlt → `None`; Env-only (Block ohne `token-file`): `load_fleet_settings(root, env_token_present=True)` → Settings, ohne den Parameter → `token_missing`. Befehl: `PYTHONPATH=scripts python3 -c "from pathlib import Path; from lib.fleet_client import load_fleet_settings; print(load_fleet_settings(Path('.')))"` im Repo-Root → `None` (agent-meta hat keinen `fleet`-Block).
- [ ] Step 5: commit `feat: add fleet client settings loader with fail-closed validation`

### Task 7: F1-D — Registry und Enrollment-Zustandsmaschine
**Agent:** senior-developer
**Depends on:** 5
**parallel_group:** f1-g2
**ACs:** AC-8 (Quelle), AC-9, AC-10, AC-14, AC-17, AC-25, AC-27, AC-49, AC-50 · **Spec:** IC-8, IC-10, D5, A5, A6
**Files:**
- Create: `scripts/fleet-server.py`
**Interfaces:** Produces in `scripts/fleet-server.py`: `MAX_INSTANCES = 256`, `RESERVED_SLOTS = 32`, `class RegistryError(Exception)` mit `code`, `class Registry` mit `__init__(self, state_dir: Path, audit: AuditLog, clock: Callable[[], float] = time.time) -> None`, `ensure_state_dir(path: Path) -> None` (`os.mkdir(path, 0o700)`; existierend mit Group-/Other-Bits → Exit 2), `issue(self, name: str, enroll_hours: int = 24) -> tuple[str, str, str]` (Token, Instance-ID, Deadline), `authenticate(self, token: str) -> tuple[str, dict]` (Hash-Vergleich per `token_matches` über alle Einträge; Promotion von `pending_token_hash`, Ablauf von `pending_until`; Fehler `invalid_token`/`instance_revoked`/`enroll_expired`), `enroll(self, instance_id: str, body: Mapping[str, Any]) -> dict`, `heartbeat(self, instance_id: str, status: Mapping[str, Any]) -> None`, `rotate(self, instance_id: str, grace_hours: int, immediate: bool) -> str`, `revoke(self, instance_id: str, by: str) -> None`, `save(self, force: bool = False) -> None` (atomar, Heartbeat-Sammelschreiben ≤ alle 60 s), `liveness(entry: Mapping[str, Any], now: float) -> str`, `instances_view(self) -> dict` (Schema `fleet-instances-v1`, `name_mismatch` abgeleitet aus `name` ≠ `status.name`). Consumes `fleet_protocol` (Token, `AuditLog`, `create_private_file`, `private_temp_path`, `cleanup_private_temps`, `hash_token`, `token_matches`), Registry-Format `fleet-registry-v1` aus IC-8.
- [ ] Step 1: Rot-Zustand: `python3 -c "import importlib.util as u; s=u.spec_from_file_location('fs','scripts/fleet-server.py'); m=u.module_from_spec(s); s.loader.exec_module(m)"` → `FileNotFoundError`.
- [ ] Step 2: Datei mit `from __future__ import annotations`, `sys.path`-Einfügung von `scripts/` und `from lib import fleet_protocol` anlegen; `Registry` nach IC-8 und IC-10: `instance_id = "inst_" + secrets.token_hex(8)`, eindeutiger `name` (Duplikat → `RegistryError("name_conflict")`), Obergrenze 256 (`RegistryError("registry_full")`), Zustände `issued|active|revoked|expired`, Tombstones ohne `token_hash`, In-Memory-Daten unter `threading.Lock`.
- [ ] Step 3: Enrollment: Treffer + `state == issued` + `now <= enroll_deadline` → `active` (`enrolled_at`, Audit `enroll`); danach idempotent (nur `prefix`/`agent_meta_version` aktualisieren, `name` nie; Abweichung nur im Audit-`detail`); Deadline überschritten → `expired` + `enroll_expired`; `revoked` → `instance_revoked`.
- [ ] Step 4: Rotation nach IC-10: `pending_token_hash`/`pending_until`; erste Nutzung des neuen Tokens ersetzt `token_hash` (Audit `rotate_complete`), Ablauf der Grace ohne Nutzung → alter Hash verworfen (`actor: server`); `immediate` ersetzt sofort; `instance_id` bleibt gleich.
- [ ] Step 5: Persistenz: `save` schreibt über `create_private_file(private_temp_path(registry.json))`, `os.fsync`, `os.replace`; `cleanup_private_temps(state_dir, ("registry.json", "audit.log"))` beim Laden; geladene Datei mit `schema != "fleet-registry-v1"` → Exit 1. `liveness`: `online` ≤ 2,5 × Intervall, `stale` ≤ 10 × Intervall, sonst `offline`, ohne Heartbeat `never`.
- [ ] Step 6: Smoke: Python-Einzeiler lädt das Modul per `importlib`, legt `Registry(Path('.tmp/fleet-t7'), AuditLog(Path('.tmp/fleet-t7/audit.log'),'server'))` an, ruft `issue('a')`, dann `authenticate(token)` → Treffer; `stat -c %a .tmp/fleet-t7 .tmp/fleet-t7/registry.json` → `700` und `600`; `grep -c amf_ .tmp/fleet-t7/registry.json` → `0`.
- [ ] Step 7: commit `feat: add fleet server registry with enrollment state machine`

### Task 8: F1-D — Server-CLI (`issue-token`, `rotate-token`, `revoke`, `list`)
**Agent:** developer
**Depends on:** 7
**ACs:** AC-8, AC-14, AC-27, AC-29, AC-49, AC-50 (list-Maskierung) · **Spec:** IC-6, IC-8 (PID-Guard), IC-10
**Files:**
- Modify: `scripts/fleet-server.py`
**Interfaces:** Produces `main(argv: Sequence[str] | None = None) -> int` (argparse-Subkommandos `serve`, `issue-token`, `rotate-token`, `revoke`, `list` mit den Flags aus IC-6; **kein** Flag nimmt einen Token-Wert), `cmd_issue_token(args) -> int`, `cmd_rotate_token(args) -> int`, `cmd_revoke(args) -> int`, `cmd_list(args) -> int`, `mask_control(value: str) -> str` (jedes Zeichen der Unicode-Kategorie `Cc` als `\xNN`/`\uNNNN`), `ensure_no_serve_running(state_dir: Path) -> None` (`<state-dir>/serve.pid` + Prozess-Check, sonst Exit 1 mit Hinweis), Exit-Codes 0 ok / 1 Bedien-/Zustandsfehler / 2 Sicherheits-Refusal. Consumes `Registry` (Task 7), `fleet_protocol.create_private_file`, `cert_fingerprint`.
- [ ] Step 1: Rot-Zustand: `python3 scripts/fleet-server.py issue-token --name a --out .tmp/fleet-t8/a.token --state-dir .tmp/fleet-t8; echo $?` → Nicht-Null (kein CLI).
- [ ] Step 2: `issue-token`: Token nur per `create_private_file(Path(--out))` (existierende Datei → Exit 1), nie auf stdout/stderr; Ausgabe: Instance-ID, Deadline (`issued_at` + `--enroll-hours`), mit `--tls-cert` zusätzlich Fingerprint (aus der Zertifikatsdatei, DER aus PEM via `ssl.PEM_cert_to_DER_cert`) und Pfad der Token-Datei. `rotate-token`: `--grace-hours` (Default 24) oder `--immediate`, schreibt den neuen Token in `--out`. `revoke`: `Registry.revoke(id, "server")`.
- [ ] Step 3: `list`: Tabelle (Name, Zustand, Liveness, Version, Provider, Health) bzw. `--json` mit `json.dumps(ensure_ascii=True)`; alle instanzgelieferten Strings durch `mask_control`; Markierung `[name mismatch]`.
- [ ] Step 4: Admin-Token-Datei: `ensure_admin_token(state_dir, cli_file) -> str` (Kette Env `AGENT_META_FLEET_ADMIN_TOKEN` > `--admin-token-file` > `<state-dir>/admin.token` über `resolve_secret`; fehlt alles, wird `admin.token` per `create_private_file` erzeugt und nur der Pfad ausgegeben).
- [ ] Step 5: Smoke: `python3 scripts/fleet-server.py issue-token --name a --out .tmp/fleet-t8/a.token --state-dir .tmp/fleet-t8` → Exit 0, Ausgabe enthält `inst_`, enthält **nicht** den Dateiinhalt (`! grep -F "$(cat .tmp/fleet-t8/a.token)"` auf die Ausgabe); zweiter Aufruf mit gleichem `--out` → Exit 1; `stat -c %a .tmp/fleet-t8/a.token` → `600`; `python3 scripts/fleet-server.py list --state-dir .tmp/fleet-t8 --json` → JSON mit `"state": "issued"`; `python3 scripts/fleet-server.py issue-token --help | grep -ci "token-value\|--token "` → `0`.
- [ ] Step 6: commit `feat: add fleet server enrollment CLI`

### Task 9: F1-E — Kommando-Broker und HTTP-Endpunkte
**Agent:** senior-developer
**Depends on:** 8
**ACs:** AC-9, AC-10, AC-11, AC-12, AC-13, AC-17, AC-18, AC-22, AC-23, AC-24, AC-50 · **Spec:** IC-7, IC-11 (Queue, Ablauf, Long-Poll), IC-13 (Header)
**Files:**
- Modify: `scripts/fleet-server.py`
**Interfaces:** Produces `class CommandBroker` (`enqueue(instance_id, type, args) -> dict`, `next_for(instance_id, wait: float, poll_slot_holder) -> list[dict]`, `ack(instance_id, body) -> None` mit der Übergangstabelle `delivered → accepted|ok|error|rejected`, `accepted → ok|error`, sonst `schema_invalid`, `state(command_id) -> dict | None`, `sweep(now)` für `queued` 60 s → `expired`, `delivered` 60 s → `expired`, `accepted` 330 s → `error/command_timeout`, Retention 10 min / 1000 Einträge, Queue je Instanz 16 → `queue_full`), `class FleetHandler(BaseHTTPRequestHandler)` mit Routen `POST /v1/enroll`, `POST /v1/heartbeat`, `GET /v1/poll`, `POST /v1/ack`, `POST /v1/deregister`, `GET /`, `GET /api/instances`, `GET /api/instances/<id>`, `POST /api/instances/<id>/commands`, `GET /api/commands/<command_id>`; Fehlerform `{"error": {"code", "message"}}`; Standard-Header `X-Content-Type-Options: nosniff`, `Cache-Control: no-store`; `GET /` liefert `docs/ui/fleet-ui.html` (Pfad relativ zu `fleet-server.py`: `../docs/ui/fleet-ui.html`) mit der CSP aus IC-13, `Referrer-Policy: no-referrer`. Consumes `Registry`, `fleet_protocol.validate_payload`, `READ_COMMANDS`, `WRITE_COMMANDS`.
- [ ] Step 1: Rot-Zustand: Handler/Klassen fehlen: `python3 -c "import importlib.util as u; s=u.spec_from_file_location('fs','scripts/fleet-server.py'); m=u.module_from_spec(s); s.loader.exec_module(m); m.CommandBroker"` → `AttributeError`.
- [ ] Step 2: Authentisierung: Bearer-Header; Instanz-Token nur `/v1/*` (über `Registry.authenticate`), Fleet-Admin-Token nur `/api/*` (`hmac.compare_digest`); `GET /` öffentlich; kein Query-Token; 401 mit `WWW-Authenticate: Bearer`; `revoked` → 403 `instance_revoked`; Heartbeat/Poll im Zustand `issued` → 409 `not_enrolled`.
- [ ] Step 3: Heartbeat validiert `fleet-status-v1`, aktualisiert `status`/`last_heartbeat` (Server-Empfangszeit); Poll: `threading.Condition` je Instanz, `wait` 0 bis 25 s, höchstens 4 Kommandos je Antwort, 204 ohne Kommandos, ein neuer Poll derselben Instanz beendet den alten sofort mit 204; Ack validiert `fleet-ack-v1`; `deregister` → `revoked` (`revoked_by: "instance"`, Audit `deregister`).
- [ ] Step 4: `POST /api/instances/<id>/commands`: Typ ∉ `READ_COMMANDS` → 400 `unknown_command` (in F1 auch `WRITE_COMMANDS`; keine Write-Pfade); Instanz `offline`/`never` → 409 `instance_offline`; wartet bis 20 s auf Terminalzustand → 200 Kommandozustand, sonst 504 `command_timeout`; Audit `command_enqueued`, `command_delivered`, `command_ack`; Results landen nur im RAM (nie in Registry/Audit).
- [ ] Step 5: Body-Limits: Instanz-POST 1 MiB, Dashboard-POST 64 KiB (Prüfung des `Content-Length` vor dem Lesen → 413 `payload_too_large`, Body wird nicht gelesen). `fleet-instances-v1` liefert Registry-Namen; Enroll/Heartbeat ändern ihn nie.
- [ ] Step 6: Smoke (Loopback, Plain-HTTP): Hilfsfunktion `make_server(state_dir, port=0)` startet einen `ThreadingHTTPServer` in einem Thread; mit `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:<port>/api/instances` → `401`; mit gültigem Admin-Token → `200`; `curl … /v1/poll` mit Admin-Token → `401`. `wc -l scripts/fleet-server.py` ≤ 900 (nach Task 10 erneut prüfen).
- [ ] Step 7: commit `feat: add fleet server endpoints and command broker`

### Task 10: F1-E — Transport: TLS, Verbindungslimits, Deadlines, `serve`
**Agent:** senior-developer
**Depends on:** 9
**ACs:** AC-5, AC-6, AC-21, AC-22, AC-24, AC-48, AC-51, AC-30 · **Spec:** IC-6 (`serve`), IC-11, IC-12, R-4
**Files:**
- Modify: `scripts/fleet-server.py`
**Interfaces:** Produces `class FleetHTTPServer(ThreadingHTTPServer)` (`daemon_threads = True`, `request_queue_size = 32`, `connection_slots = BoundedSemaphore(MAX_INSTANCES + RESERVED_SLOTS)` = 288 im überschriebenen `process_request` mit nicht-blockierendem `acquire`, `release` im `finally` von `process_request_thread`; `poll_slots = BoundedSemaphore(MAX_INSTANCES)` mit Slot-Übergabe beim Ersatz-Poll unter dem Instanz-Lock; Pre-Auth-Zähler je Quell-IP (8, Loopback ausgenommen); Gesamt-Deadline 10 s ab `accept()` für Request-Zeile + Header + Body mit `sock.settimeout(max(0.1, deadline - now))` vor jedem `recv`; Handler-Timeout 35 s; TLS-Handshake im Worker-Thread bei `do_handshake_on_connect=False`), `build_ssl_context(cert: Path, key: Path) -> ssl.SSLContext` (`PROTOCOL_TLS_SERVER`, `minimum_version = TLSv1_2`, Ladefehler → Exit 2), `cmd_serve(args) -> int` (Exit 2 mit `refusing to bind on non-loopback host without TLS (--tls-cert/--tls-key)` **vor** `bind`; Startbanner mit Fingerprint; schreibt `serve.pid`; `cleanup_private_temps`; Registry-Flush alle 60 s und beim Beenden). Consumes `AuditLog.aggregate` für `auth_failed` und `tls_refused`.
- [ ] Step 1: Rot-Zustand: `python3 scripts/fleet-server.py serve --host 0.0.0.0 --state-dir .tmp/fleet-t10; echo $?` → Server startet ohne TLS oder meldet fehlendes Subkommando (erwartet nach Umsetzung: Exit 2).
- [ ] Step 2: Fail closed: `not is_loopback(host)` ohne `--tls-cert` und `--tls-key` → Meldung auf stderr, Exit 2, **kein** Socket (Aufruf vor `FleetHTTPServer(...)`); TLS-Kontext nur über `build_ssl_context`.
- [ ] Step 3: Limits wie in IC-11: Hauptthread schreibt nie auf einen TLS-Socket (über Limit: `shutdown_request` ohne Antwort; Plain-HTTP: fester 503-`busy`-Body per nicht-blockierendem `send`); authentisierter Poll ohne freien `poll_slot` (und ohne eigenen offenen Poll) → 503 `busy` aus dem Handler-Thread; `auth_failed` und `tls_refused` ausschließlich über `AuditLog.aggregate`.
- [ ] Step 4: Smoke: `python3 scripts/fleet-server.py serve --host 0.0.0.0 --state-dir .tmp/fleet-t10; echo $?` → Meldung `refusing to bind on non-loopback host without TLS (--tls-cert/--tls-key)`, Exit `2`; `python3 scripts/fleet-server.py serve --port 0 --state-dir .tmp/fleet-t10 &` bindet Loopback, `curl -s http://127.0.0.1:<port>/ | head -c 15` liefert `<!DOCTYPE html>` sobald Task 16 existiert (bis dahin 404 `unknown_route`/Fehlerform); Slowloris-Probe: `python3 -c "import socket,time; s=socket.create_connection(('127.0.0.1',<port>)); s.send(b'GET / HTTP/1.1\r\n'); time.sleep(11); print(s.recv(10))"` → leere Antwort (`b''`) nach ≤ 10 s; `wc -l scripts/fleet-server.py` ≤ 900; Prozess beenden (`kill %1`).
- [ ] Step 5: commit `feat: add fleet server TLS transport and connection limits`

### Task 11: F1-C — Python-3.9-Check deckt `scripts/fleet-server.py` ab
**Agent:** developer
**Depends on:** 10
**ACs:** AC-30 · **Spec:** IC-11 (Python-3.9-Kompatibilität), C7
**Files:**
- Modify: `scripts/lib/consistency/python_compat.py`
**Interfaces:** Produces Konstante `_SCAN_FILES = (("scripts", "fleet-server.py"),)` und erweitertes `_iter_py_files(root: Path)`, das nach den Verzeichnissen aus `_SCAN_DIRS` zusätzlich existierende Dateien aus `_SCAN_FILES` liefert. Consumes `_SCAN_DIRS = (("scripts", "lib"), ("tests",))`; die Checks `check_py39_union_syntax` und `check_fstring_backslash_hazard` bleiben unverändert.
- [ ] Step 1: Rot-Zustand: `PYTHONPATH=scripts python3 -c "from pathlib import Path; from lib.consistency import python_compat as pc; print([p.name for p in pc._iter_py_files(Path('.')) if p.name=='fleet-server.py'])"` → `[]`.
- [ ] Step 2: `_SCAN_FILES` nach `_SCAN_DIRS` ergänzen (Kommentar: Hyphen-Dateinamen sind aus `scripts/lib` nicht erreichbar, daher explizit); in `_iter_py_files` nach der Verzeichnisschleife `for parts in _SCAN_FILES: path = root.joinpath(*parts); if path.is_file(): yield path`.
- [ ] Step 3: Verifikation: dieselbe Zeile wie in Step 1 → `['fleet-server.py']`; `PYTHONPATH=scripts python3 -c "from pathlib import Path; from lib.consistency import python_compat as pc; print(pc.check_py39_union_syntax(Path('.')), pc.check_fstring_backslash_hazard(Path('.')))"` → `[] []`; `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 4: commit `chore: scan fleet-server.py in the python 3.9 compat check`

### Task 12: F1-F — `FleetClient` Kern (Pinning, Enroll, Heartbeat, Poll, Backoff, Widerruf)
**Agent:** senior-developer
**Depends on:** 5, 6
**ACs:** AC-7, AC-12, AC-13, AC-26 (Instanz-Audit), AC-29, AC-30, AC-49 · **Spec:** IC-4, IC-9, IC-10, IC-12, A3, A8
**Files:**
- Modify: `scripts/lib/fleet_client.py`
**Interfaces:** Produces `class FleetClient` mit `__init__(self, root: Path, settings: FleetSettings, *, env_token: str | None = None, write_handlers: Mapping[str, WriteHandler] | None = None, audit: AuditLog | None = None) -> None`, `start(self) -> None` (idempotent; Daemon-Threads `fleet-heartbeat`, `fleet-poll`; Thread `fleet-write` nur wenn `write_handlers` nicht leer, in F1 nie), `stop(self, *, deregister: bool = False) -> None`, `_request(self, method: str, path: str, body: Mapping[str, Any] | None) -> tuple[int, dict | None]` (eine Verbindung pro Request, kein Keep-Alive), `_post_ack(self, command_id: str, body: Mapping[str, Any]) -> None` (`POST /v1/ack` über `_request`; F2 stubbt/ersetzt dieses Symbol, F1 ruft es nur aus dem Poll-Thread), `_backoff(attempt: int) -> float` (5 s bis 300 s, Faktor 2, ±20 % Jitter), vorläufige Stubs `build_status(self) -> dict[str, Any]` (minimaler `fleet-status-v1`-Body: Name, Prefix, Version, `providers`, `schema: "fleet-status-v1"`, `health: {"state": "degraded", "reasons": []}`, `last_sync: None`, `allow_remote_write` frisch aus der Config (Default `False`), `heartbeat_interval` aus `settings`) und `handle_command(self, command: Mapping[str, Any]) -> dict[str, Any]` (Ack `rejected/unknown_command`), die Task 13 vollständig ersetzt (hält den Abhängigkeitsgraph azyklisch), `WriteHandler = Callable[[Mapping[str, Any]], Mapping[str, Any]]`. Consumes `fleet_protocol` (`cert_fingerprint`, `resolve_secret`, `validate_payload`, `AuditLog`, `create_private_file`, `private_temp_path`, `cleanup_private_temps`, `utc_now_iso`), `FleetSettings` (Task 6).
- [ ] Step 1: Rot-Zustand: `PYTHONPATH=scripts python3 -c "from lib.fleet_client import FleetClient"` → `ImportError`.
- [ ] Step 2: `_request`: `ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)`, `minimum_version = TLSv1_2`, `check_hostname = False`, `verify_mode = CERT_NONE`; `http.client.HTTPSConnection(host, port, context=ctx, timeout=35)` bzw. `HTTPConnection` (Loopback-http); nach `conn.connect()` und **vor** jeglichem Request-Byte: `cert_fingerprint(conn.sock.getpeercert(binary_form=True))` gegen `settings.fingerprints` per `hmac.compare_digest`; kein Treffer → Socket schließen, Audit `pin_mismatch`, Backoff, **kein** `Authorization`-Header gesendet. Token nur im Header `Authorization: Bearer <token>`; Token-Quelle: `env_token` (im Speicher) sonst `resolve_secret(ENV_INSTANCE_TOKEN, settings.token_file)` mit Neulesen bei geänderter mtime.
- [ ] Step 3: Heartbeat-Thread: erster Zyklus `POST /v1/enroll` (`fleet-enroll-v1`), danach alle `heartbeat_interval` s `project.yaml` neu laden (`lib.config.load_config`), `fleet.enabled`/`allow-remote-write` frisch auswerten, `POST /v1/heartbeat` mit `build_status()` (Stub aus diesem Task, Vollimplementierung Task 13); Poll-Thread: Schleife `GET /v1/poll?wait=25`, Antwort 204 → erneut, Kommandos → `handle_command(...)` (Stub, Task 13 ersetzt) und `_post_ack(...)`; Write-Kommandos werden nie ausgeführt (F1: `rejected/unknown_command`).
- [ ] Step 4: Fehlerpfade nach der Tabelle in IC-4: 401 `invalid_token` → Audit `auth_failed` (einmal je Pause), Pause bis Token-Datei-mtime wechselt (Env-Token: bis Neustart); 403 `instance_revoked`/`enroll_expired` → `STATE_FILE` atomar schreiben (`{"state": "revoked", "since": <ISO>, "reason": <code>}` über `create_private_file(private_temp_path(...))`), Client stoppt, Neustart nur wenn Token-Datei-mtime > `since`; `fleet.enabled` zur Laufzeit `false` → `POST /v1/deregister`, Audit `deregistered`, Stopp. `start()` ruft `cleanup_private_temps(root / ".meta-viz", ("fleet-state.json", "fleet-audit.log"))`. Das Modul wertet `expires_at` **nicht** aus.
- [ ] Step 5: Smoke: `PYTHONPATH=scripts python3 -c "from lib.fleet_client import FleetClient; print([FleetClient._backoff(n) for n in (0,1,9)])"` → drei Zahlen, erste in [4.0, 6.0], letzte ≤ 360.0; `grep -nE "[?&]token=|\"token\"" scripts/lib/fleet_client.py` → keine Treffer (AC-29); `wc -l scripts/lib/fleet_client.py` ≤ 600 (nach Task 15 erneut).
- [ ] Step 6: commit `feat: add fleet client with pinned transport and heartbeat`

### Task 13: F1-F — Lese-Handler `get-logs`, Status, `read_last_sync`
**Agent:** senior-developer
**Depends on:** 2, 12
**ACs:** AC-15, AC-16, AC-19 · **Spec:** IC-4 (Lese-Handler, `read_last_sync`), IC-7 (Health-Regel, Ack-Results), A2
**Files:**
- Modify: `scripts/lib/fleet_client.py`
**Interfaces:** Produces `read_last_sync(root: Path) -> dict[str, Any] | None`, `tail_log(root: Path, source: str, lines: int) -> list[str]` (≤ letzte 64 KiB per `seek`, Zeilen > 2000 Zeichen gekürzt, jede Zeile durch `redact_text`), `FleetClient.build_status(self) -> dict[str, Any]` (ersetzt den Stub aus Task 12; Schema `fleet-status-v1`; Version aus `agent-meta-version`, Fallback `.agent-meta/VERSION`, dann `VERSION`, dann `"unknown"`; `providers` = `ai-providers` unverändert; `allow_remote_write` aus frisch geladener Config, `heartbeat_interval` aus `settings`; Health nach IC-7), `FleetClient.handle_command(self, command: Mapping[str, Any]) -> dict[str, Any]` (ersetzt den Stub aus Task 12; Ack-Body; `get-logs` in F1; `get-config`/`trigger-sync`/`put-config`/Unbekanntes → `rejected/unknown_command`; Dispatch über Wörterbuch `_READ_HANDLERS`, damit Task 15 genau einen Eintrag ergänzt). Consumes `redaction.redact_text`, `.meta-viz/sync-status.json` (`last_run_timestamp`, `last_run_exit_code`, `last_run_summary`), `sync.log`-mtime.
- [ ] Step 1: Rot-Zustand: `PYTHONPATH=scripts python3 -c "from lib.fleet_client import read_last_sync"` → `ImportError`.
- [ ] Step 2: `read_last_sync`: `.meta-viz/sync-status.json` → `{"timestamp": <fromisoformat → UTC → utc_now_iso-Format>, "exit_code", "summary": redact_text(last_run_summary or "")[:200], "source": "sync-status"}`; nicht parsebar wie fehlende Datei; Fallback `sync.log`-mtime → `{"timestamp", "exit_code": None, "summary": "", "source": "sync-log-mtime"}`; beides fehlt → `None`.
- [ ] Step 3: `handle_command` für `get-logs`: `args.source` ∈ `LOG_SOURCES`, `args.lines` 1 bis 200 (Default 100), sonst `rejected/invalid_args`; kein Pfad-Argument; Result `{"source", "lines": [...]}` ≤ 64 KiB.
- [ ] Step 4: Health: `error` bei nicht ladbarer `project.yaml` oder `exit_code` ≠ 0 und nicht `None`; `degraded` bei `last_sync` `None` oder `exit_code` `None`; sonst `ok`; `reasons` kurz und redigiert (≤ 10 Einträge).
- [ ] Step 5: Smoke (Temp-Projekt unter `.tmp/fleet-t13` mit `.meta-viz/sync-status.json` `{"last_run_timestamp": "2026-10-23T12:00:00.123456+00:00", "last_run_exit_code": 0, "last_run_summary": null}`): `PYTHONPATH=scripts python3 -c "from pathlib import Path; from lib.fleet_client import read_last_sync; print(read_last_sync(Path('.tmp/fleet-t13')))"` → `{'timestamp': '2026-10-23T12:00:00Z', 'exit_code': 0, 'summary': '', 'source': 'sync-status'}`; Grep AC-15: `grep -nE "== *\"(Claude|Opencode|Gemini|Mammouth|Codex|Copilot|KimiCode|Continue|ZCode)\"" scripts/lib/fleet_client.py scripts/fleet-server.py scripts/lib/fleet_protocol.py scripts/lib/redaction.py` → keine Treffer.
- [ ] Step 6: commit `feat: add fleet client status and log read handlers`

### Task 14: F1-F — Admin-Hook und Env-Token-Entfernung
**Agent:** senior-developer
**Depends on:** 13
**ACs:** AC-1, AC-2 (Admin-Server startet trotz `FleetConfigError`), AC-29, AC-47 · **Spec:** IC-5, A1, A4, R-2
**Files:**
- Modify: `scripts/admin-server.py`
**Interfaces:** Produces Modulfunktion `_maybe_create_fleet_client(root: Path) -> Any` (erste Anweisung bedingungslos `env_token = os.environ.pop("AGENT_META_FLEET_TOKEN", None)`; danach `_ensure_scripts_on_path(root)`, `from lib import fleet_client`, `fleet_client.load_fleet_settings(root, env_token_present=env_token is not None)` (Parameter aus Task 6, Spec IC-4/IC-5 Rev. 1.4, siehe A-6; Env-only-Betrieb bleibt so nach dem Pop erhalten); `FleetConfigError` → stderr-Meldung + `None`; `ImportError` → stderr-Hinweis + `None`; sonst `fleet_client.FleetClient(root, settings, env_token=env_token)`), Attribut `AdminServer.fleet_client`, Banner-Zeile `  i  Fleet:   enabled (<url>)`, `fleet_client.start()` vor `serve_forever()`, `fleet_client.stop()` im `finally`. Consumes `AdminServer.__init__` (setzt `self.httpd` als letzte Anweisung), `AdminServer.start`, `_ensure_scripts_on_path`, `load_fleet_settings` (Task 6). **Nicht geändert:** `main()`, `_admin_start_detached`, `AuthService`, Routing-Tabellen.
- [ ] Step 1: Rot-Zustand: `python3 -c "import importlib.util as u; s=u.spec_from_file_location('a','scripts/admin-server.py'); m=u.module_from_spec(s); s.loader.exec_module(m); m._maybe_create_fleet_client"` → `AttributeError`.
- [ ] Step 2: `_maybe_create_fleet_client` als Modulfunktion in `scripts/admin-server.py` unmittelbar vor `class AdminServer` einfügen; in `AdminServer.__init__` nach `self.httpd = _DaemonThreadingHTTPServer(...)` die Zeile `self.fleet_client = _maybe_create_fleet_client(self.root)` anfügen; in `start()` vor dem `try:` mit `serve_forever()` `if self.fleet_client: self.fleet_client.start()` und die Banner-Zeile; im `finally` nach `self.httpd.server_close()` `if self.fleet_client: self.fleet_client.stop()`. Gesamtzuwachs ≤ 25 Zeilen: `git diff --stat scripts/admin-server.py` zeigt ≤ 25 Einfügungen.
- [ ] Step 3: Verifikation: `git diff -U0 scripts/admin-server.py | grep -E "^[-+].*(def main|_admin_start_detached|AuthService)"` → keine Treffer; Env-Test: `AGENT_META_FLEET_TOKEN=x python3 -c "import importlib.util as u,os,pathlib; s=u.spec_from_file_location('a','scripts/admin-server.py'); m=u.module_from_spec(s); s.loader.exec_module(m); print(m._maybe_create_fleet_client(pathlib.Path('.')), 'AGENT_META_FLEET_TOKEN' in os.environ)"` → `None False` (agent-meta hat keinen `fleet`-Block, Variable trotzdem entfernt); Env-only-Test: Temp-Projekt unter `.tmp/fleet-t14` mit `fleet`-Block ohne `token-file` und `AGENT_META_FLEET_TOKEN=x` → `_maybe_create_fleet_client` liefert ein `FleetClient`-Objekt (kein `token_missing`); `python3 scripts/sync.py --validate` → Exit 0.
- [ ] Step 4: Hinweis Netzplan (R-2): Änderungen nur additiv in `AdminServer.__init__`/`start`; wer später mergt, rebased (siehe „Merge-Reihenfolge“).
- [ ] Step 5: commit `feat: start fleet client from the admin server hook`

## Phase 2 — Config-Ansicht (Task 15)

### Task 15: F1-I — Lese-Handler `get-config` (Phase 2)
**Agent:** senior-developer
**Depends on:** 13
**ACs:** AC-33, AC-35 · **Spec:** IC-3, IC-4 (Lese-Handler), IC-7 (Ack-Result `get-config`), D7
**Files:**
- Modify: `scripts/lib/fleet_client.py`
**Interfaces:** Produces `config_file_sha256(path: Path) -> str` (SHA-256 über die Rohbytes, in `fleet_client.py`; F2 nutzt es wieder), `FleetClient._handle_get_config(self, args: Mapping[str, Any]) -> dict[str, Any]` und genau einen Eintrag `"get-config": _handle_get_config` in `_READ_HANDLERS` (Rollback = Eintrag entfernen). Ack-Result `{"key": "project", "config": <redact_config(load_config(...))>, "sha256": <sha256 der Datei auf Platte>}` ≤ 512 KiB (größer → `error/internal_error`). `args.key` ≠ `"project"` → `rejected/invalid_args`. Consumes `redaction.redact_config`, `lib.config.load_config`.
- [ ] Step 1: Rot-Zustand: `get-config` liefert `rejected/unknown_command` (Task 13): Temp-Projekt `.tmp/fleet-t15` mit `.meta-config/project.yaml`; `PYTHONPATH=scripts python3 -c "…FleetClient(...).handle_command({'command_id':'cmd_0123456789abcdef','type':'get-config','args':{'key':'project'}})"` → Status `rejected`.
- [ ] Step 2: Handler implementieren: Datei `root / ".meta-config" / "project.yaml"` lesen, SHA-256 via `config_file_sha256(path)`, `load_config` für das Mapping, **nur** `redact_config(...)` geht ins Ack; `.meta-config/secrets.local.yaml` wird nirgends geöffnet.
- [ ] Step 3: Smoke: dieselbe Zeile wie Step 1 → Status `ok`, `result["config"]` enthält `variables` als `[REDACTED]` (sofern in der Test-Config vorhanden) und kein Klartext-Token; `grep -n "secrets.local" scripts/lib/fleet_client.py scripts/fleet-server.py` → keine Treffer (AC-33); `wc -l scripts/lib/fleet_client.py` ≤ 600.
- [ ] Step 4: commit `feat: add fleet get-config handler with allowlist redaction`

## Phase 1 — Dashboard (Task 16)

### Task 16: F1-G — Dashboard `fleet-ui.html` (Instanztabelle, Detail, Logs)
**Agent:** developer
**Depends on:** 10
**ACs:** AC-28, AC-50 (Dashboard-Teil) · **Spec:** IC-13, IC-7, IC-11 (Dashboard-Polling 5 s)
**Files:**
- Create: `docs/ui/fleet-ui.html`
**Interfaces:** Produces Single-File-Dashboard (Vanilla-JS/CSS, keine externen Ressourcen) mit Token-Eingabe (`sessionStorage`, Versand nur als `Authorization`-Header), Instanztabelle (Name, Prefix, Version, Liveness, Health, letzter Sync, Provider; Polling `GET /api/instances` alle 5 s), Detailansicht mit „Logs“ (Quelle `sync|admin-server`, Zeilenzahl 1 bis 200 → `POST /api/instances/<id>/commands` mit `{"type": "get-logs", "args": {...}}`), Funktion `displaySafe(s)` (Steuerzeichen `/[\u0000-\u001f\u007f-\u009f]/g` außer `\n` in `<pre>` als `\uNNNN` sichtbar), Warnhinweis bei `name_mismatch: true`. Consumes `fleet-instances-v1`, Kommandozustand (IC-7), CSP aus IC-13 (`script-src 'unsafe-inline'`, `connect-src 'self'`).
- [ ] Step 1: Rot-Zustand: `test -f docs/ui/fleet-ui.html && echo da || echo fehlt` → `fehlt`.
- [ ] Step 2: Seite bauen: Darstellung ausschließlich über `document.createElement` + `textContent`; die Wörter `innerHTML`, `outerHTML`, `insertAdjacentHTML` und `eval` kommen **auch nicht in Kommentaren** vor (Grep-Prüfung); Instanznamen immer aus dem Registry-Feld `name`; Fehlerzustände (401, 409 `instance_offline`, 504 `command_timeout`) als Text.
- [ ] Step 3: Verifikation: `grep -nE "innerHTML|outerHTML|insertAdjacentHTML|eval *\(" docs/ui/fleet-ui.html` → keine Treffer (Exit 1); `grep -c "http://\|https://" docs/ui/fleet-ui.html` → `0` (keine externen Ressourcen); Server-Auslieferung: `curl -sI http://127.0.0.1:<port>/` → Header `Content-Security-Policy: default-src 'none'; …`, `X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`.
- [ ] Step 4: commit `feat: add fleet dashboard single-file UI`

## Phase 2 — Config-Ansicht im Dashboard (Task 17)

### Task 17: F1-I — Config-Ansicht im Dashboard (Phase 2)
**Agent:** developer
**Depends on:** 15, 16
**ACs:** AC-36 · **Spec:** IC-13 (Ansichten), IC-7 (`get-config` Args/Result)
**Files:**
- Modify: `docs/ui/fleet-ui.html`
**Interfaces:** Produces Schaltfläche „Config“ in der Detailansicht → `POST /api/instances/<id>/commands` mit `{"type": "get-config", "args": {"key": "project"}}`; Darstellung des Result-Felds `config` als `JSON.stringify(config, null, 2)` in einem `<pre>` ausschließlich per `textContent` (über `displaySafe`). Consumes Task 15 (`get-config` Result), Task 16 (Detailansicht).
- [ ] Step 1: Rot-Zustand: `grep -c "get-config" docs/ui/fleet-ui.html` → `0`.
- [ ] Step 2: Button und Renderer ergänzen; kein Schreib-Button (F2); Hinweis im Dialog „Redigierte Ansicht (Allowlist)“.
- [ ] Step 3: Verifikation: `grep -c "get-config" docs/ui/fleet-ui.html` → ≥ `1`; `grep -nE "innerHTML|outerHTML|insertAdjacentHTML|eval *\(" docs/ui/fleet-ui.html` → keine Treffer.
- [ ] Step 4: commit `feat: show redacted instance config in the fleet dashboard`

## Phase 1 — Dokumentation (Tasks 18 bis 20)

### Task 18: F1-H — Howto `fleet-server.md`
**Agent:** documenter
**Depends on:** 10, 14
**parallel_group:** f1-g4
**ACs:** AC-32 · **Spec:** Doku-Deliverables, IC-6, IC-10, IC-12, R-10, R-12, R-13
**Files:**
- Create: `docs/howto/fleet-server.md`
**Interfaces:** Produces deutschsprachige Howto mit den Pflichtabschnitten: Server starten (Loopback, TLS, Reverse-Proxy) mit `openssl`-Befehlen für ein selbstsigniertes Zertifikat und die Fingerprint-Berechnung **aus der Zertifikatsdatei auf dem (Proxy-)Host**; `openssl s_client` ausdrücklich als Trust-on-first-use unzulässig; Enrollment Schritt für Schritt (`issue-token`, Token-Datei out-of-band, `fleet`-Block mit Keys aus IC-1); Rotation; Widerruf (server- und instanzseitig); Zertifikatswechsel/Auto-Renewal (R-13, Zwei-Einträge-Liste, eigenes langlebiges selbstsigniertes Zertifikat); Token-Datei statt Env empfohlen; Proxy-seitiger Slowloris-Schutz bei Loopback-Bind; Troubleshooting nach Fehlercodes; Agent-/Testbetrieb mit `--state-dir .tmp/…`; `.gitignore`-Hinweis für `.meta-viz/` (R-5); Abgrenzung zur Review-Agent-Fleet (#528-#531, R-12); Hinweis, dass CLI-Syncs außerhalb des Admin-Servers nicht in `sync-status.json` erscheinen (R-6). Consumes CLI aus Tasks 8 und 10, Hook aus Task 14.
- [ ] Step 1: Rot-Zustand: `test -f docs/howto/fleet-server.md && echo da || echo fehlt` → `fehlt`.
- [ ] Step 2: Howto schreiben; jeder Befehl im Dokument muss gegen die reale CLI ausgeführt werden können (`python3 scripts/fleet-server.py --help`, `… serve --help`, `… issue-token --help` zur Abstimmung der Flag-Namen).
- [ ] Step 3: Verifikation: `grep -c "s_client" docs/howto/fleet-server.md` → ≥ `1` (mit Warnung); `grep -c "state-dir" docs/howto/fleet-server.md` → ≥ `3`; kein Token-Wert und kein privater Schlüssel im Dokument (Secret-Scan über die Datei).
- [ ] Step 4: commit `docs: add fleet server howto`

### Task 19: F1-H — API-Referenz `fleet-api-reference.md`
**Agent:** documenter
**Depends on:** 10
**parallel_group:** f1-g4
**ACs:** AC-32 · **Spec:** Doku-Deliverables, IC-7, IC-8, IC-11
**Files:**
- Create: `docs/api/fleet-api-reference.md`
**Interfaces:** Produces deutschsprachige Referenz: Endpunkttabelle (IC-7), Authentisierung (Instanz-Token nur `/v1/*`, Admin-Token nur `/api/*`), Schemas `fleet-enroll-v1`, `fleet-status-v1`, `fleet-command-v1`, `fleet-ack-v1`, `fleet-instances-v1`, Kommandozustand und Übergänge, Fehlercodetabelle (IC-7, in F1 gültige Codes; F2-Codes mit Kennzeichnung „ab F2“), Limits (IC-11), Registry-Format (IC-8), Audit-Format (IC-9). Consumes `SCHEMAS` aus `fleet_protocol.py` (Task 4).
- [ ] Step 1: Rot-Zustand: `test -f docs/api/fleet-api-reference.md && echo da || echo fehlt` → `fehlt`.
- [ ] Step 2: Referenz schreiben; Schemas aus `PYTHONPATH=scripts python3 -c "import json; from lib.fleet_protocol import SCHEMAS; print(json.dumps(SCHEMAS['fleet-status-v1'], indent=2))"` übernehmen, damit Doku und Code nicht auseinanderlaufen.
- [ ] Step 3: Verifikation: `grep -c "fleet-status-v1" docs/api/fleet-api-reference.md` → ≥ `2`; `grep -c "queue_full" docs/api/fleet-api-reference.md` → ≥ `1`.
- [ ] Step 4: commit `docs: add fleet api reference`

### Task 20: F1-H — Querverweis in `admin-ui-remote-access.md` und Hinweis-Header der Alt-Spec
**Agent:** documenter
**Depends on:** —
**parallel_group:** f1-g4
**ACs:** AC-32 · **Spec:** Doku-Deliverables, K15/K17
**Files:**
- Modify: `docs/howto/admin-ui-remote-access.md`
- Modify: `docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md`
**Interfaces:** Produces (a) in `docs/howto/admin-ui-remote-access.md` einen kurzen Abschnitt „Mehrere Repos zentral überwachen → Fleet-Server“ mit relativem Link auf `fleet-server.md` und der Klarstellung, dass Fleet eigene Tokens nutzt und `admin-ui.token` nicht weitergibt (Abschnitt vor `## Related`, zusätzlicher Eintrag in der Liste `## Related`); (b) in der Alt-Spec als erste Zeilen den Header `> **Hinweis:** Superseded by \`docs/specs/2026-10-23-fleet-server-spec.md\` (SPEC-FLEET-SERVER-2026-10-23). Diese Datei bleibt aus Historiengründen erhalten und wird nicht mehr gepflegt.` gefolgt von einer Leerzeile; der übrige Inhalt bleibt unverändert, die Datei wird **nicht** gelöscht oder verschoben. Consumes Task 18 (Link-Ziel; Link bleibt gültig, weil der Pfad fest ist).
- [ ] Step 1: Rot-Zustand: `grep -c "fleet-server" docs/howto/admin-ui-remote-access.md` → `0`; `head -1 docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md` → `# Fleet-Server (Phase 1+2: …`.
- [ ] Step 2: Beide Änderungen einarbeiten.
- [ ] Step 3: Verifikation: `grep -c "fleet-server.md" docs/howto/admin-ui-remote-access.md` → ≥ `1`; `head -1 docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md` beginnt mit `> **Hinweis:** Superseded by`; `git diff --stat docs/superpowers/specs/2026-09-07-fleet-server-phase1-2-design.md` zeigt nur Einfügungen (keine Löschungen).
- [ ] Step 4: commit `docs: link fleet server howto and mark the old fleet spec superseded`

## Tests (F1-T, optional nach D8 — kein Merge-Gate)

> Test-Tasks laufen nach ihrer Komponente. Tests, die Server-State schreiben, nutzen pytest-`tmp_path` oder `--state-dir .tmp/…`; Server binden `127.0.0.1` auf Port 0; TLS-Tests erzeugen das Wegwerf-Zertifikat zur Laufzeit per `openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem -days 1 -subj /CN=localhost` in `tmp_path` und überspringen bei fehlendem `openssl` (`pytest.skip`). Der Server wird per `importlib.util.spec_from_file_location` geladen (Hyphen-Dateiname, Muster `tests/test_admin_server.py`).

### Task 21: F1-T — Tests `fleet_protocol` (empfohlen (Security))
**Agent:** tester
**Depends on:** 5
**ACs:** AC-11, AC-26, AC-48, AC-49 (empfohlen (Security): Token-Vergleich, Secret-Dateien, Audit-Aggregation)
**Files:**
- Create: `tests/test_fleet_protocol.py`
**Interfaces:** Produces Tests `test_token_roundtrip_and_prefix`, `test_token_matches_rejects_empty_and_wrong`, `test_normalize_fingerprint_variants_and_invalid`, `test_resolve_secret_env_beats_file`, `test_resolve_secret_rejects_group_readable_file`, `test_create_private_file_mode_and_excl`, `test_cleanup_private_temps_exact_regex_only`, `test_validate_payload_status_ok_and_errors`, `test_audit_fields_mode_0600_and_redacted_detail`, `test_audit_rotation_truncates_to_1000`, `test_audit_aggregate_one_line_per_minute`, `test_no_equality_comparison_on_tokens` (Grep gegen `scripts/lib/fleet_protocol.py`). Consumes `scripts/lib/fleet_protocol.py`.
- [ ] Step 1: Tests schreiben (Quelle der Erwartungen: AC-11, AC-26, AC-48, AC-49).
- [ ] Step 2: `python3 -m pytest tests/test_fleet_protocol.py -q` → Exit 0, alle Tests `passed`; ein Negativversuch (z. B. temporär `os.chmod` in `create_private_file`) lässt `test_no_equality_comparison_on_tokens`/Modustest scheitern und wird zurückgenommen.
- [ ] Step 3: commit `test: add fleet protocol security tests`

### Task 22: F1-T — Tests `redaction` (empfohlen (Security))
**Agent:** tester
**Depends on:** 2
**ACs:** AC-20, AC-34 (empfohlen (Security): Redaction)
**Files:**
- Create: `tests/test_redaction.py`
**Interfaces:** Produces Tests `test_redact_text_masks_all_patterns` (Fixture mit URL-Basic-Auth, `Authorization: Bearer`, `bearer <token>`, `token=`/`password:`, `--token <v>`, `ghp_…`, `xoxb-…`, `AKIA…`, `amf_…`, PEM-Block; Ausgabe enthält keinen Original-Secret-Wert), `test_redact_config_allowlist_subtrees`, `test_redact_config_nested_allowlist_keeps_siblings_redacted`, `test_redact_config_secret_key_backstop`, `test_redact_config_pattern_in_string_values`, `test_redact_config_does_not_mutate_input`, `test_redact_config_non_mapping_returns_empty`, `test_contains_redaction_marker_recursive`. Consumes `scripts/lib/redaction.py`; Fake-Secrets sind offensichtlich synthetisch (`EXAMPLE_NOT_A_KEY`-Muster, keine realen Formate mit gültiger Prüfsumme).
- [ ] Step 1: Tests schreiben (Fixture-Erwartungen aus AC-20 und AC-34: `admin-ui.token`, `admin-ui.token-file`, `fleet.token-file` → `[REDACTED]`, `admin-ui.port` sichtbar).
- [ ] Step 2: `python3 -m pytest tests/test_redaction.py -q` → Exit 0.
- [ ] Step 3: commit `test: add redaction tests for fleet views`

### Task 23: F1-T — Tests `fleet_client` Teil 1: Settings, Pinning, Widerruf (empfohlen (Security))
**Agent:** tester
**Depends on:** 12, 9
**ACs:** AC-2, AC-3, AC-4, AC-7, AC-12, AC-13, AC-29 (empfohlen (Security): fail closed, Pinning, Widerruf)
**Files:**
- Create: `tests/test_fleet_client.py`
**Interfaces:** Produces Tests `test_http_non_loopback_raises_tls_required`, `test_https_without_fingerprint_raises`, `test_invalid_fingerprint_code`, `test_group_readable_token_file_raises`, `test_disabled_or_missing_block_returns_none`, `test_pin_mismatch_sends_no_request_bytes` (TLS-Wegwerfserver auf Loopback, der jedes empfangene Byte zählt; erwartet `0` Bytes und Audit `pin_mismatch`), `test_pin_match_allows_request`, `test_two_fingerprints_rotation`, `test_revoked_writes_state_file_and_stops`, `test_restart_blocked_until_token_mtime_newer`, `test_runtime_disable_sends_deregister`, `test_token_only_in_authorization_header`. Consumes `scripts/lib/fleet_client.py`, `fleet-server.py` (für den End-to-End-Teil `deregister`/`revoked`).
- [ ] Step 1: Tests schreiben.
- [ ] Step 2: `python3 -m pytest tests/test_fleet_client.py -q` → Exit 0 (TLS-Tests bei fehlendem `openssl` `skipped`).
- [ ] Step 3: commit `test: add fleet client security tests`

### Task 24: F1-T — Tests `fleet_client` Teil 2: Lese-Handler und `get-config`
**Agent:** tester
**Depends on:** 15, 23
**ACs:** AC-15, AC-16, AC-19, AC-33, AC-35 (empfohlen (Security): `get-config`-Redaction)
**Files:**
- Modify: `tests/test_fleet_client.py`
**Interfaces:** Produces Tests `test_build_status_validates_and_keeps_provider_order`, `test_read_last_sync_sync_status_normalizes_timestamp_and_summary`, `test_read_last_sync_falls_back_to_log_mtime`, `test_read_last_sync_none_when_both_missing`, `test_health_rules`, `test_get_logs_only_allowed_sources_and_lines_range`, `test_get_logs_redacts_every_line_and_caps_size`, `test_get_config_only_key_project`, `test_get_config_result_is_redacted_and_has_sha256`, `test_no_secrets_local_access` (Grep gegen `scripts/lib/fleet_client.py`), `test_unknown_and_write_commands_rejected_in_f1`. Consumes `FleetClient.handle_command`, `build_status`, `read_last_sync`, `tail_log`.
- [ ] Step 1: Tests schreiben.
- [ ] Step 2: `python3 -m pytest tests/test_fleet_client.py -q` → Exit 0.
- [ ] Step 3: commit `test: add fleet client read handler tests`

### Task 25: F1-T — Tests Admin-Hook (empfohlen (Security))
**Agent:** tester
**Depends on:** 14, 24
**ACs:** AC-1, AC-2, AC-47 (empfohlen (Security): Env-Token-Vererbung)
**Files:**
- Modify: `tests/test_fleet_client.py`
**Interfaces:** Produces Tests `test_hook_returns_none_without_block_and_starts_no_fleet_thread` (Thread-Namen mit Präfix `fleet-` fehlen, keine `.meta-viz/fleet-*`-Datei), `test_hook_survives_fleet_config_error` (stderr-Meldung, `None`), `test_env_token_removed_in_every_path` (Fleet aktiv, `enabled: false`, Block fehlt, `FleetConfigError`, ImportError per Monkeypatch), `test_env_only_operation_creates_client` (Block ohne `token-file`, Env-Token gesetzt → `FleetClient` statt `token_missing`), `test_child_process_does_not_inherit_env_token` (nach dem Hook startet `subprocess.run([sys.executable, "-c", "import os;print(os.environ.get('AGENT_META_FLEET_TOKEN'))"])` und gibt `None` aus), `test_diff_does_not_touch_main_or_detached_start` (liest `scripts/admin-server.py` und prüft, dass `_admin_start_detached` keinen Fleet-Bezug enthält). Consumes `scripts/admin-server.py::_maybe_create_fleet_client` (Laden per `importlib`, Muster `tests/test_admin_server.py`).
- [ ] Step 1: Tests schreiben.
- [ ] Step 2: `python3 -m pytest tests/test_fleet_client.py -q -k hook or env_token` → Exit 0; `python3 -m pytest tests/test_admin_server.py -q` → Exit 0 (keine Regression).
- [ ] Step 3: commit `test: add admin hook and env token inheritance tests`

### Task 26: F1-T — Tests Server Teil 1: Registry und CLI (empfohlen (Security))
**Agent:** tester
**Depends on:** 8
**ACs:** AC-8, AC-9, AC-10, AC-14, AC-25, AC-27, AC-29, AC-49, AC-50 (empfohlen (Security): Token-Ausgabe, Rotation, Dateimodi, Steuerzeichen)
**Files:**
- Create: `tests/test_fleet_server.py`
**Interfaces:** Produces Tests `test_issue_token_writes_only_to_out_mode_0600_and_refuses_existing`, `test_issue_token_registry_has_single_hash_and_24h_deadline`, `test_registry_mode_0600_dir_0700_no_plaintext_token`, `test_enroll_idempotent_same_instance_id`, `test_enroll_after_deadline_expired`, `test_rotation_old_and_new_valid_until_first_use`, `test_rotation_grace_expiry_and_immediate`, `test_state_dir_contains_all_server_files`, `test_no_cli_flag_accepts_token_value`, `test_list_masks_control_characters` (Status-String mit `\x1b[31m`), `test_list_json_is_ascii`, `test_stale_temp_file_does_not_block_write`. Consumes `scripts/fleet-server.py` (`Registry`, `main`, `mask_control`).
- [ ] Step 1: Tests schreiben (Uhr injizierbar über `Registry(..., clock=...)`).
- [ ] Step 2: `python3 -m pytest tests/test_fleet_server.py -q` → Exit 0.
- [ ] Step 3: commit `test: add fleet registry and cli security tests`

### Task 27: F1-T — Tests Server Teil 2: HTTP, TLS, Limits, Dashboard (empfohlen (Security))
**Agent:** tester
**Depends on:** 10, 16, 26
**ACs:** AC-5, AC-6, AC-11, AC-12, AC-13, AC-17, AC-18, AC-21, AC-22, AC-23, AC-24, AC-28, AC-48, AC-50, AC-51 (empfohlen (Security): fail closed ohne TLS, Token-Trennung, Verbindungslimit, Slowloris, Audit-Flut)
**Files:**
- Modify: `tests/test_fleet_server.py`
**Interfaces:** Produces Tests `test_serve_non_loopback_without_tls_exits_2_before_bind`, `test_tls_min_version_1_2`, `test_silent_client_does_not_block_and_is_dropped_within_10s`, `test_invalid_token_401_with_www_authenticate`, `test_admin_token_on_v1_and_instance_token_on_api_rejected`, `test_root_is_public_with_csp_nosniff_referrer_headers`, `test_revoked_instance_gets_403`, `test_liveness_thresholds_online_stale_offline_never`, `test_connection_limit_288_plain_http_503_and_tls_close_without_bytes`, `test_reserved_slots_keep_api_available_with_256_polls`, `test_poll_returns_204_after_wait` (mit `wait=1`, Haltezeit 25 s per Konstante geprüft), `test_second_poll_takes_over_slot_without_busy`, `test_queue_full_503_on_17th_command`, `test_queued_and_delivered_commands_expire_after_60s`, `test_accepted_without_terminal_ack_becomes_command_timeout_after_330s` (Uhr injiziert), `test_body_limits_413_without_reading_body`, `test_auth_failed_and_tls_refused_are_aggregated_to_one_line_each`, `test_name_is_registry_authoritative_and_name_mismatch_flag`, `test_slow_header_client_dropped_after_10s_total_deadline`, `test_ninth_pre_auth_connection_per_ip_rejected`, `test_fleet_ui_has_no_dom_html_injection_or_eval` (Grep gegen `docs/ui/fleet-ui.html`), `test_write_commands_unknown_command_in_f1`. Consumes `scripts/fleet-server.py` (`FleetHTTPServer`, `make_server`, `FleetHandler`), `docs/ui/fleet-ui.html`.
- [ ] Step 1: Tests schreiben; lange Zeitspannen (60 s, 330 s) über injizierte Uhr, echte Wartezeiten nur ≤ 12 s (Slowloris/Deadline).
- [ ] Step 2: `python3 -m pytest tests/test_fleet_server.py -q` → Exit 0 (TLS-Tests bei fehlendem `openssl` `skipped`).
- [ ] Step 3: commit `test: add fleet server transport and limit security tests`

## Verifikation (F1-V)

### Task 28: F1-V — End-to-End-Lauf (zwei Instanzen, ein Server, Loopback und TLS)
**Agent:** tester
**Depends on:** 14, 17, 18, 20
**ACs:** Exit-Kriterium Phase 1 (manueller End-to-End-Lauf dokumentiert), AC-9, AC-12, AC-13, AC-16, AC-28, AC-36
**Files:**
- Modify: `docs/howto/fleet-server.md`
**Interfaces:** Produces Howto-Abschnitt „Verifikationslauf (F1)“ mit den real ausgeführten Befehlen und beobachteten Ergebnissen (Instanzen, Liveness, Log-Auszug, Config-Ansicht, Widerruf). Consumes alle Server-, Client-, Hook- und UI-Komponenten.
- [ ] Step 1: Zwei Temp-Instanzen unter `.tmp/fleet-e2e/inst-a` und `.tmp/fleet-e2e/inst-b` mit je `.meta-config/project.yaml` (`fleet`-Block, Loopback-URL, eigene Token-Dateien 0600) und synthetischem `sync.log`/`.meta-viz/sync-status.json` anlegen; Server mit `--state-dir .tmp/fleet-e2e/state` starten, zwei Tokens per `issue-token` erzeugen.
- [ ] Step 2: Admin-Server je Instanz starten (`python3 scripts/admin-server.py --root .tmp/fleet-e2e/inst-a --port <frei> --no-viz`), im Dashboard bzw. per `curl -H "Authorization: Bearer $(cat .tmp/fleet-e2e/state/admin.token)" http://127.0.0.1:<port>/api/instances` prüfen: beide Instanzen `online`; `get-logs` und `get-config` liefern redigierte Daten; `revoke` einer Instanz → nach ≤ einem Heartbeat `403`-Folge, `.meta-viz/fleet-state.json` mit `state: revoked`.
- [ ] Step 3: Wiederholung der Kernschritte mit TLS (`openssl req -x509 …` in `.tmp/fleet-e2e/tls`, `serve --tls-cert/--tls-key`, `fleet.cert-fingerprint` aus `issue-token --tls-cert`); falscher Fingerprint → Instanz bleibt `never`/`offline`, Audit `pin_mismatch`. Ergebnisse in das Howto eintragen, Temp-Verzeichnis `.tmp/fleet-e2e` danach löschen, Prozesse beenden.
- [ ] Step 4: commit `docs: record fleet server F1 end-to-end verification`

### Task 29: F1-V — Abschluss-Validierung (Exit-Kriterien Phase 1 und 2)
**Agent:** tester
**Depends on:** 1, 11, 19, 28
**ACs:** AC-30, AC-31, AC-32 und Gesamtprüfung Phase 1 (AC-1 bis AC-32, AC-47 bis AC-51) und Phase 2 (AC-33 bis AC-36)
**Files:**
- Modify: `docs/plans/2026-10-23-fleet-server-f1-plan.md`
**Interfaces:** Produces abgehakte Checkboxen und `> Status: complete` im Plan nach erfüllten Exit-Kriterien; Consumes alle Vor-Tasks.
- [ ] Step 1: `python3 scripts/sync.py --validate` → Exit 0; `tests/scenarios/run.sh 79` → `PASS  79-fleet-config-opt-in`; `python3 scripts/sync.py --check` → Exit 0; `python3 scripts/consistency-check.py` → Exit 0.
- [ ] Step 2: `python3 scripts/sync.py --validate-spec-plan` → keine Finding der Severity ERROR für Spec und Plan (setzt E1 voraus); die bekannten WARNINGs aus R-14 sind zulässig.
- [ ] Step 3: Falls die Test-Tasks umgesetzt wurden: `python3 -m pytest tests/test_fleet_protocol.py tests/test_redaction.py tests/test_fleet_client.py tests/test_fleet_server.py tests/test_admin_server.py -q` → Exit 0; sonst Vermerk „Tests übersprungen (D8)“ in der PR-Beschreibung samt Liste der nicht abgedeckten empfohlenen Security-ACs.
- [ ] Step 4: Plan-Ledger aktualisieren (Checkboxen, `> Status: complete`); commit `chore: close fleet server F1 plan`

## Exit-Kriterien

**Phase 1 (Read-Only-Dashboard):** AC-1 bis AC-32 und AC-47 bis AC-51 erfüllt (Traceability unten); `python3 scripts/sync.py --validate` grün; `tests/scenarios/run.sh 79` grün; Howto und API-Referenz vorhanden; manueller End-to-End-Lauf (zwei Instanzen, ein Server, Loopback und TLS) in der Howto dokumentiert (Task 28); `--validate-spec-plan` ohne ERROR (Task 29).
**Phase 2 (Config-Ansicht):** AC-33 bis AC-36 erfüllt (Tasks 2, 15, 17; Tests 22, 24).

## Rollback je Phase

- **Phase 1:** Instanz: `fleet.enabled: false` (wirkt spätestens nach einem Heartbeat-Intervall, AC-13). Code: Revert der Commits der Tasks 1 bis 20 in umgekehrter Reihenfolge; der Admin-Hook (Task 14) ist ohne `fleet`-Block wirkungslos (AC-1) und kann als einzelner Commit zuerst zurückgenommen werden. Server: Prozess stoppen, `<state-dir>` löschen. Schema-Property und Szenario 79 (Task 1) sind separat revertierbar.
- **Phase 2:** Revert der Commits der Tasks 15 und 17 (Gruppe F1-I): Der Eintrag `"get-config"` in `_READ_HANDLERS` entfällt, das Kommando liefert `rejected/unknown_command`; Instanz-Rollback wie Phase 1.

## Merge-Reihenfolge und Konflikte

- **Seriell:** Plan F1 (dieser Plan) wird vollständig gemergt, bevor Plan F2 (Phase 3+4) startet (F2 hängt vom Merge von F1 ab; Dateien `fleet_client.py`, `fleet-server.py`, `fleet-ui.html`, `admin-server.py` werden von beiden geändert). Empfohlene PR-Aufteilung auf `feat/fleet-server-f1`: PR 1 Tasks 1 bis 5 (Fundament), PR 2 Tasks 6 bis 11 (Server + Client-Settings), PR 3 Tasks 12 bis 17 (Client, Hook, UI, Phase 2), PR 4 Tasks 18 bis 20 und 28/29 (Doku, Verifikation; Tasks 18 und 20 mergen zusammen, Task 28 setzt beide voraus); Test-Tasks 21 bis 27 jeweils im PR ihrer Komponente (optional). Jeder PR trägt ein eigenes Conventional-Commits-Squash-Subject.
- **Netzplan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md` (DRAFT, `SPEC-897-896-ADMIN-UI-NETWORK-2026-10-07`):** ändert ebenfalls `AdminServer.__init__`, `_admin_start_detached`, `main()` und `AuthService.check_origin`. Überlappung mit F1 nur in `AdminServer.__init__`/`start` (additive Zeilen, Task 14). Regel (Spec R-2): wer zuerst gemergt wird, gewinnt; der zweite rebased. Keine semantische Abhängigkeit.
- **`docs/plans/admin-server-split-backlog.md` (STATUS: open):** Ein Split von `scripts/admin-server.py` vor oder während F1 würde Task 14 (Hook-Position) verschieben; F1 führt bewusst keinen Split durch. Wird der Split vorgezogen, ist Task 14 vor dem Split zu mergen oder die Hook-Zeilen sind in die neue Modulstruktur zu übernehmen (Re-Planning).
- **Opencode-v2-Plan (`docs/plans/2026-10-22-opencode-v2-support-plan.md`):** reserviert ebenfalls Szenario `79-opencode-v2-full-surface`. Wer zuerst gemergt wird, behält die Nummer 79 (Spec O-F10, Entscheidung bei Freigabe); der andere Plan nimmt die nächste freie Nummer und zieht seine Spec nach (Entry-Kriterium E5).
- **Unverifiziert:** Die genaue Einfügeposition der Schema-Property `fleet` (nach `admin-ui`) wird in Task 1 gegen die reale Datei bestimmt.

## Commit-Grenzen

Ein Commit je Task (Conventional Commits, Englisch, ≤ 72 Zeichen, Imperativ), Reihenfolge wie die Task-Nummern. Die Rolle meldet nach jedem abgeschlossenen Task (Test grün bzw. Smoke bestanden) die geänderten Dateien plus Commit-Message und spätestens nach 5 geänderten Dateien; die Anwendung des Commits sowie Secret-Scan vor dem Commit übernimmt Caller/Orchestrator. Push, Tag und Branch-Management bleiben der `git`-Rolle vorbehalten.

## Self-Review

- **Rollenzuordnung:** Jeder Task nennt genau eine Rolle (`developer`, `senior-developer`, `documenter`, `tester`); Sicherheits- und Protokollcode liegt bei `senior-developer`, Doku bei `documenter`, Tests bei `tester`.
- **Messbarkeit:** Jeder Task endet mit einem Kommando und erwarteter Ausgabe (Smoke bzw. pytest-Exit 0), keine Kriterien der Form „funktioniert korrekt“.
- **Files/Interfaces:** Alle Tasks tragen `Files:` (Create/Modify) und nicht leere `Interfaces:`; Dateiüberlappung innerhalb der Parallel-Gruppen ausgeschlossen: `f1-g1` (Tasks 1, 2, 3: Schema/Szenario, `redaction.py`, `fleet_protocol.py`), `f1-g2` (Tasks 6, 7: `fleet_client.py`, `fleet-server.py`), `f1-g4` (Tasks 18, 19, 20: drei verschiedene Doku-Dateien).
- **`pipeline_stages`:** Das Frontmatter am Dateianfang enthält `implement: 3`; die Tabelle „Task-Übersicht“ liefert die Schritt-zu-Agent-Zuordnung.
- **Platzhalter:** Keine offenen Markierungen im Plan; offene Fragen sind ausschließlich Verweise auf O-F7, O-F8, O-F10 (Entry-Kriterien E3, E5); O-F1, O-F2 und O-F9 sind geschlossen.
- **Spec-Treue:** F1 enthält keinen Write-Handler, keinen `fleet-write`-Thread und keine F2-Fehlercodes im Verhalten (Tasks 9, 12, 13). `main()` und `_admin_start_detached` bleiben unverändert (Task 14, Test 25). Keine Abweichung von der Spec: `env_token_present` ist in Rev. 1.4 übernommen (A-6).

## Traceability AC → Task

Impl = Implementierungs-Task, Test = Test-Task (D8, optional; Security-Tests empfohlen).

| AC | Impl-Task(s) | Test-Task(s) |
|---|---|---|
| AC-1 | 6, 14 | 25 |
| AC-2 | 6, 14 | 23, 25 |
| AC-3 | 6 | 23 |
| AC-4 | 3, 6 | 21, 23 |
| AC-5 | 10 | 27 |
| AC-6 | 10 | 27 |
| AC-7 | 12 | 23 |
| AC-8 | 7, 8 | 26 |
| AC-9 | 7, 9 | 26, 27 |
| AC-10 | 7, 9 | 26 |
| AC-11 | 3, 9 | 21, 27 |
| AC-12 | 9, 12 | 23, 27 |
| AC-13 | 9, 12 | 23, 27 |
| AC-14 | 7, 8 | 26 |
| AC-15 | 4, 13 | 24 |
| AC-16 | 13 | 24 |
| AC-17 | 7, 9 | 27 |
| AC-18 | 9 | 27 |
| AC-19 | 13 | 24 |
| AC-20 | 2 | 22 |
| AC-21 | 10 | 27 |
| AC-22 | 9, 10 | 27 |
| AC-23 | 9 | 27 |
| AC-24 | 9, 10 | 27 |
| AC-25 | 7 | 26 |
| AC-26 | 5, 12 | 21, 23 |
| AC-27 | 7, 8 | 26 |
| AC-28 | 16 | 27 |
| AC-29 | 8, 12, 14 | 23, 25, 26 |
| AC-30 | 2, 3, 10, 11, 12 | 29 (Kommandos) |
| AC-31 | 1 | 1 (Szenario 79), 29 |
| AC-32 | 18, 19, 20 | 29 (`--validate-spec-plan`) |
| AC-33 | 15 | 24 |
| AC-34 | 2 | 22 |
| AC-35 | 15 | 24 (empfohlen (Security)) |
| AC-36 | 17 | 28 (manuell) |
| AC-47 | 6, 14 | 25 |
| AC-48 | 5, 10 | 21, 27 |
| AC-49 | 3, 5, 7, 12 | 21, 26 |
| AC-50 | 8, 9, 16 | 26, 27 |
| AC-51 | 10 | 27 |

Phase 1 deckt AC-1 bis AC-32 und AC-47 bis AC-51 ab, Phase 2 deckt AC-33 bis AC-36 ab. AC-37 bis AC-46, AC-52 und AC-53 gehören zu Plan F2 (AC-54 entfällt in Rev. 1.4).
