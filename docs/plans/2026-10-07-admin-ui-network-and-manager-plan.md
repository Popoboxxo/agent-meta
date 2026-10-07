---
status: DRAFT
spec-id: SPEC-897-896-ADMIN-UI-NETWORK-2026-10-07
issues: [897, 896, 899, 855]
pipeline_stages:
  implement: 3
---

# Admin-UI Network-Mode (#897, #896) + Status #899/#855 — Spec + Implementation Plan

> Status: Entwurf (DRAFT — wartet auf Nutzer-Freigabe; NICHT self-approved)
> Datum: 2026-10-07
> Scope: #897 (bug/security), #896 (feature) — spezifiziert. #899 (PR #913), #855 (PR #905) — nur Status-Tracking, keine spezifizierten Features.
> Quelle: GitHub-Issues #896, #897, #899, #855; Code-Stand `79d6db95` (#912), Code-Claims in §2/§3 am 2026-10-07 gegen `scripts/admin-server.py` re-verifiziert (`check_origin` Z. 903-937, `AdminServer.__init__` Z. 5564-5573, `DEFAULT_ALLOWED_HOSTS`/`LOOPBACK_HOSTS` Z. 197-198, Detached-argv Z. 5694, Routen `/api/sync/dry-run` Z. 3572, `/api/backups/create` Z. 3593).
> Trace-Anker: `spec-id: SPEC-897-896-ADMIN-UI-NETWORK-2026-10-07`
> Entwurfs-Herkunft: `.tmp/2026-10-07-admin-ui-network-and-manager-plan-draft.md` (Trail, kann aufgeräumt werden)

**Goal:** Mutationen (Save/Backup/Sync) funktionieren im Network-Mode, ohne die Origin/Host-Prüfung aufzuweichen (#897); darauf aufbauend ein expliziter `local`/`network`-Startmodus mit Auto-Token und URL-/Firewall-Ausgabe (#896).
**Nicht-Ziele:** Wildcard-/Reflection-Allowlist; HTTPS/Reverse-Proxy-Origins (Q9 → eigenes Issue); Origin-Check für GET; Hostname-Auto-Allow; neue Abhängigkeiten.
**Architecture:** Alle Origin-/Host-Logik bleibt in `AuthService.check_origin` (`scripts/admin-server.py`); neue Helfer sind reine Modul-Funktionen daneben. Keine neue Komponente, keine neue Abhängigkeit.
**Tech Stack:** Python 3 stdlib (`socket`, `ipaddress`, `secrets`), Vanilla-JS in `docs/ui/admin-ui.html`, pytest/unittest, Playwright (`tests/browser/`).

---

## 0. Verifikationsstatus (zuerst lesen)

### 0.1 Live-GitHub-Daten

Weder der Entwurfs-Agent noch der Finalisierungs-Agent (concept-specifier, 2026-10-07) hatte ein Shell-Tool; `gh issue view` / `gh pr view` wurden **in diesem Dokument nicht live ausgeführt**. Merge-Status von PR #913 stammt aus der Aussage des Orchestrators (§1). Vor Freigabe ausführen:

```bash
/home/hermes/.local/bin/gh issue view 897 --json title,body,state,labels,comments
/home/hermes/.local/bin/gh issue view 896 --json title,body,state,labels,comments
/home/hermes/.local/bin/gh issue view 899 --json state,closedAt
/home/hermes/.local/bin/gh issue view 855 --json state,closedAt
/home/hermes/.local/bin/gh pr view 913 --json state,mergedAt,files
/home/hermes/.local/bin/gh pr view 905 --json state,mergedAt,files
```

Abweichungen zwischen Issue-Text und den in §2/§3 belegten Code-Defekten → Dokument anpassen, bevor es APPROVED wird.

### 0.2 Spec-Gate

Beide Implementierungs-Issues sind **M** (3–8 Dateien). Dieses Dokument ist die kombinierte Spec + Plan (Stage `specify` von `concept-driven-dev`, finalisiert durch `concept-specifier`). Ausführung erst nach Nutzer-Freigabe (`status: APPROVED` im Frontmatter + Header), Q1–Q12 (§10) beantwortet.

### 0.3 Arbeitsbaum

Stand 2026-10-07: aktueller Branch `fix/452-release-process-templates`; keine uncommitteten Änderungen an getrackten Dateien (nur untracked `.playwright-mcp/`, `issue838-*.yml`). Der im Entwurf genannte Konflikt mit `fix/746-gitignore-keep-reinclude` (`config/project-config.schema.json`) ist im aktuellen Baum nicht mehr sichtbar; vor Start von PR 1 trotzdem prüfen, ob #746 offene Schema-Änderungen hat. Implementierung immer auf frischem Branch von `main`.

---

## 1. Status #899 und #855 (keine neue Implementierungsarbeit)

### #899 — `--update-models`-Reminder / „Modelle nie von Hand pflegen"

- Lokale Evidenz (`.git/logs/refs/heads/fix/899-manager-update-models-reminder`): 2 Commits auf Basis `87e14db3` (#911):
  - `docs(agent-meta-manager): add --update-models reminder (#899)`
  - `test: rebaseline agent-meta-manager golden fixture for #899` (`67219d05`)
- Merge-Status: **laut Orchestrator gemergt (PR #913, nach Erstellung des Entwurfs)**. In dieser Finalisierung **nicht live verifiziert** (kein Shell-Tool, §0.1); lokales `origin/main` enthält den Merge noch nicht (kein Fetch seit `79d6db95`).
- Plan-Eintrag: **erledigt via PR #913 (gemergt — vorbehaltlich `gh pr view 913`-Bestätigung), nur Issue-Close, falls noch offen.** Kein Implementierungsbedarf für #899 in diesem Plan.
- Mögliche Restlücke **unbestätigt** (Q12): `docs/plans/2026-10-06-bugfix-wave-plan.md` (Wave 2a) nennt `config/ai-providers.yaml` + `docs/`; PR #913 berührt laut Commit-Messages nur `agents/1-generic/agent-meta-manager.md` + Golden-Fixture. Fordert der Issue-Body von #899 zusätzlich eine `docs/`-Stelle (z. B. `docs/guides/features/sync-concept.md`, Abschnitt „Was NIEMALS manuell editiert wird") → eigener S-Task (`documenter`); sonst komplett erledigt.

### #855 — Copilot Subagent-Dispatch-Capability

- Spec `docs/specs/2026-10-06-855-copilot-subagent-capability.md` (APPROVED) verlangt: `capabilities.Copilot.subagent_dispatch: true`, `native_agent_tools: ["agent"]`, ein zusätzliches `special_notes`-Bullet.
- Ist-Stand `config/provider-capabilities.yaml`: Z. 196 `subagent_dispatch: true`, Z. 204 `native_agent_tools: ["agent"]`, Z. 215 Bullet „Subagent-Dispatch (#855) …" — alle drei AC-relevanten Werte vorhanden.
- `docs/plans/2026-10-05-backlog-execution-status.md:74`: `#855 | merged/closed | PR #905 (copilot)`.
- Plan-Eintrag: **erledigt via PR #905 (gemergt laut Repo-Evidenz; `gh pr view 905` nicht live ausgeführt) — nur Issue-Close, falls noch offen.**
- Bewusst **keine** Restlücke: P-1-Pfad-Drift (`.github/copilot/agents/`) ist in der Spec als Nicht-Ziel ausgegliedert → eigenes Issue.

---

## 2. #897 — Root-Cause-Analyse

**Symptom:** Im Network-Mode lädt die UI (GET ist nicht origin-geprüft), aber jeder `PUT`/`POST`/`DELETE` liefert `403 {"error":"forbidden","detail":"origin not allowed: 'http://<lan-ip>:7420'"}`.

**Kontrollfluss:** `do_PUT/do_POST/do_DELETE` → `_check_token()` → `_check_origin()` → `AuthService.check_origin(origin, host, allowed_hosts, bind_host, bind_port)` (`scripts/admin-server.py:903-937`).

Belegte Defekte (alle im Code verifiziert):

| # | Defekt | Stelle | Auswirkung |
|---|---|---|---|
| D1 | **Origin/Host-Asymmetrie:** Der Host-Check fügt `bind_host:bind_port` immer hinzu (Z. 935), der Origin-Check nicht (Z. 929). | `AuthService.check_origin` | Bei `--host 192.168.1.5` passiert Host, aber Origin `http://192.168.1.5:7420` scheitert → exakt „origin not allowed". |
| D2 | **Wildcard-Bind ohne erreichbaren Host:** `--host 0.0.0.0` → Browser sendet die echte LAN-IP; die steht weder in `DEFAULT_ALLOWED_HOSTS` noch ist sie `bind_host`. | `AdminServer.__init__` Z. 5564 | Default-Network-Setup blockt **alle** Mutationen. |
| D3 | **„Extends"-Versprechen gebrochen:** `--help`, Schema (`project-config.schema.json`, `admin-ui.allowed-hosts`), Howto und Rule sagen „erweitert die Loopback-Defaults"; Code **ersetzt** sie (`tuple(allowed_hosts) if allowed_hosts else …`). | `AdminServer.__init__` Z. 5564 | Nach `--allowed-hosts myhost` scheitert lokaler Zugriff über `127.0.0.1`, wenn Bind ≠ 127.0.0.1. |
| D4 | **Format-Falle `host:port`:** Schema-Beschreibung sagt „List of host:port origins"; Code hängt `:<bind_port>` an → `192.168.1.5:7420:7420`. | Schema vs. `check_origin` Z. 929/933 | Nutzer, die der Doku folgen, bekommen weiter 403 — still. |
| D5 | **IPv6 nie matchbar:** `::1` erzeugt `http://::1:7420` / `::1:7420`; Browser senden `http://[::1]:7420` / `[::1]:7420`. | `check_origin` | Default-Eintrag `::1` ist toter Code. |
| D6 | **Kein Startup-Feedback:** Non-loopback-Bind ohne nicht-loopback Allowed-Host startet kommentarlos. | `AdminServer.__init__` | Fehler erst beim ersten Save sichtbar. |

**UI „hängt"/Overlay bleibt** (Code-belegte Kandidaten; gegen Issue-Text bestätigen, Q10):

- U1: Mehrere Mutations-Handler nutzen `try { … } finally { … }` **ohne `catch`** (z. B. `docs/ui/admin-ui.html` Z. 10104-10109, 10117-10122, 10128-10149). Ein `APIError(403)` wird zur unbehandelten Promise-Rejection → kein Toast. Kein globaler `unhandledrejection`-Handler vorhanden.
- U2: „Create Backup" (Z. 8333-8344) öffnet ein Modal ohne Close-Button, ruft im Fehlerfall blockierendes `alert()` und schließt das Modal erst danach.

**Fazit:** D1+D2 sind die Ursache des Blockers; D3–D5 verhindern, dass der dokumentierte Workaround (`--allowed-hosts`) greift; D6+U1/U2 machen den Fehler unsichtbar. Der Check ist nicht „zu streng", sondern **falsch implementiert** (asymmetrisch, falsch normalisiert, ohne Kenntnis der eigenen Adressen). Fix = Korrektheit herstellen, **nicht** lockern.

---

## 3. #896 — Ist-Analyse

- `--host`, `--admin-token`, `--allowed-hosts` existieren bereits (`main()`). `--allowed-hosts` ist **kein neues Flag** — #896 braucht nur die korrekte Wirkung aus #897 + Doku.
- `admin-ui.bind-host` und `admin-ui.port` aus `project.yaml` werden geladen (`_load_admin_ui_config` Z. 473-505), aber **nicht** für Bind verwendet (`--host`/`--port` haben harte CLI-Defaults).
- Startausgabe druckt `http://0.0.0.0:7420` — keine erreichbare URL.
- Detached-Start reicht das Token als **argv** an den Child (`cmd += ["--admin-token", args.admin_token]`, Z. 5694) → sichtbar in `ps`/`/proc/<pid>/cmdline`.
- Child-stdout geht nach `.meta-viz/admin-server.log` → ein vom Child gedrucktes Token landet im Log.
- Slash-Command heißt `/admin` (`commands/1-generic/admin.md`), nicht `/admin-ui`.

---

## 4. Abhängigkeit / Reihenfolge #897 ↔ #896

**Empfehlung: #897 zuerst als eigener PR, danach #896 auf dessen Basis. Nicht bündeln, nicht parallelisieren.**

1. **Funktionale Abhängigkeit:** Ein `network`-Modus, der eine LAN-URL druckt, auf der jedes Save mit 403 scheitert, wäre ein Feature mit eingebautem Defekt. AC-896-3 setzt AC-897-2 voraus.
2. **Gemeinsamer Helfer:** `_local_interface_addresses()` und `_url_host()` entstehen in #897 und werden von #896 (`_reachable_urls`) nur konsumiert.
3. **Datei-Overlap** (§5): `scripts/admin-server.py` (`AdminServer.__init__`, `main()`), `tests/test_admin_server.py`, Howto, Rule → parallel = garantierte Merge-Konflikte.
4. **Gegen Bündelung:** #897 ist `security`-gelabelt; eine Auth-Grenzen-Änderung soll isoliert reviewbar und revertierbar sein.
5. **Umgekehrt unabhängig:** #897 hat keine Abhängigkeit auf #896 und ist allein shipbar.

Sanity-Check (Finalisierung): Begründung hält — keine der #896-Tasks wird von #897 benötigt, aber 896-4 und AC-896-3 benötigen #897-Symbole/-Verhalten. Bei Q1 = „nein" wandert `_local_interface_addresses()` nach #896; die Reihenfolge bleibt #897 → #896 (Gründe 1, 3, 4 gelten unverändert).

---

## 5. File-Structure-Map

| Datei | Aktion | #897 | #896 | Zweck |
|---|---|---|---|---|
| `scripts/admin-server.py` | Modify | ✔ | ✔ | Origin-Check-Korrektur, Allowlist-Normalisierung (#897); `--mode`, Bind-/Token-Auflösung, Banner, Token via env (#896) |
| `tests/test_admin_server.py` | Modify | ✔ | ✔ | Unit-Tests je Task |
| `docs/ui/admin-ui.html` | Modify | ✔ | — | Fehler sichtbar machen (U1/U2) |
| `tests/browser/test_admin_ui_network_mode.py` | Create | ✔ | — | E2E: Mutation über Nicht-Loopback-Origin + 403-Sichtbarkeit |
| `tests/browser/README.md` | Modify | ✔ | — | Neue Testdatei in Layout-Tabelle |
| `config/project-config.schema.json` | Modify | ✔ | — | `allowed-hosts`-Beschreibung korrigieren |
| `docs/howto/admin-ui-remote-access.md` | Modify | ✔ | ✔ | Allowlist-Semantik (#897), Modi/Banner/Token-Datei (#896) |
| `rules/2-platform/agent-meta-admin-ui.md` | Modify | ✔ | ✔ | Quelle für generiertes `.claude/skills/admin-ui/SKILL.md` |
| `commands/1-generic/admin.md` | Modify | — | ✔ | `/admin`-Argument-Hint + Modi |
| generierte Artefakte (`.claude/commands/admin.md`, `.claude/skills/admin-ui/SKILL.md`) | via `python scripts/sync.py` | ✔ | ✔ | nicht von Hand editieren |

**Aufwand (S ≤2 / M 3–8 / L 9–20 Dateien, generierte Artefakte nicht gezählt):**

| Issue | Dateien | Klasse |
|---|---|---|
| #897 | 8 | **M** (obere Grenze; 6 falls 897-4 per Q10 entfällt) |
| #896 | 5 | **M** |
| #899 | 0 (Doku-Restlücke unbestätigt, Q12) | erledigt via PR #913 (Merge live zu bestätigen) |
| #855 | 0 | erledigt via PR #905 |

---

## 6. Global Constraints

- **Keine Wildcard-Allowlist** — verbindlich, siehe §9 Inv. 5.
- **Loopback-Definition einheitlich:** „loopback" = Mitgliedschaft in `LOOPBACK_HOSTS` (Z. 198), wie im bestehenden Fail-closed-Check (Z. 5566). Alle neuen Helfer (`_resolve_bind`, D6-Warnung, 896-2) verwenden genau diese Definition.
- Nur stdlib.
- `AuthService.check_origin`-Signatur bleibt unverändert.
- Provider-agnostisch: keine Provider-Literale im Code.
- Commits: Conventional Commits, Englisch, ≤72 Zeichen; Commit-Ausführung durch Orchestrator/git-Rolle.
- Tests: `python3 -m pytest tests/test_admin_server.py -q`; Browser: `pytest tests/browser/test_admin_ui_network_mode.py -v`; Gesamt-Gate: `python3 scripts/sync.py --validate`.

---

## 7. Tasks #897 (PR 1, Branch-Vorschlag `fix/897-admin-origin-check`)

### Task 897-1: Allowlist-Normalisierung (D4, D5, Wildcard-Verbot)

**Files:** Modify `scripts/admin-server.py`; Test `tests/test_admin_server.py` (neue Klasse `TestNormalizeAllowedHost`)
**Interfaces:**
- Produces: `WILDCARD_BIND_HOSTS: tuple[str, ...] = ("0.0.0.0", "::", "")`
- Produces: `def _url_host(host: str) -> str` — lowercase; IPv6-Literal → `[addr]`; bereits geklammerte Form unverändert.
- Produces: `def _normalize_allowed_host(entry: str, bind_port: int) -> str` — akzeptiert `name`, `name:<bind_port>`, `IPv4`, `IPv6`, `[IPv6]:<bind_port>`; liefert `_url_host`-Form ohne Port. `ValueError` bei: leer, `"*"` oder Glob-Zeichen (`*`, `?`, `[` außerhalb IPv6-Klammerform), Wildcard-Adresse (`WILDCARD_BIND_HOSTS`, auch `[::]`), Schema/Pfad (`://`, `/`), Port ≠ `bind_port`.
- Error path: `ValueError(f"invalid allowed-hosts entry {entry!r}: <reason>")`.

- [ ] Step 1: Tests (fail): `"192.168.1.5:7420"`→`"192.168.1.5"`; `"MyHost"`→`"myhost"`; `"::1"`→`"[::1]"`; `"[::1]:7420"`→`"[::1]"`; `"*"`, `"*.lan"`, `"0.0.0.0"`, `"::"`, `"[::]"`, `"http://x"`, `"x:9999"` (bind 7420), `""` → `ValueError`.
- [ ] Step 2: Implementieren (`ipaddress.ip_address` für IPv6-Erkennung).
- [ ] Step 3: `python3 -m pytest tests/test_admin_server.py -k NormalizeAllowedHost -q` grün.
- [ ] Step 4: Commit `fix(admin): normalize allowed-hosts entries and reject wildcards`

### Task 897-2: Symmetrischer Origin/Host-Check (D1, D5)

**Files:** Modify `scripts/admin-server.py` (`AuthService.check_origin`); Test `tests/test_admin_server.py` (`TestCheckOrigin` erweitern)
**Interfaces:**
- Consumes: `_url_host`, `WILDCARD_BIND_HOSTS` (897-1)
- Produces: `AuthService.check_origin(*, origin, host, allowed_hosts, bind_host, bind_port) -> None` (Signatur unverändert). Semantik: `hosts = {_url_host(h) for h in allowed_hosts} ∪ ({_url_host(bind_host)} wenn bind_host ∉ WILDCARD_BIND_HOSTS)`; daraus **identisch** `origins = {f"http://{h}:{bind_port}"}` und `host_values = {f"{h}:{bind_port}"}`. Exakter Mengenvergleich gegen `origin.lower()` / `host.lower()` (kein Präfix-/Suffix-/Regex-Match). Fehlertexte unverändert (`origin not allowed: …`, `host header not allowed: …`).
- **Bewusste Verhaltensänderung:** Bei Wildcard-Bind wird `0.0.0.0:<port>` nicht mehr als Host akzeptiert (heute via Z. 935). Kein Browser sendet diesen Host; betroffen wären nur CLI-Aufrufe gegen `http://0.0.0.0:<port>` → diese nutzen künftig `127.0.0.1`.

- [ ] Step 1: Tests (fail):
  - `bind_host="192.168.1.5"`, Origin `http://192.168.1.5:7420`, Host `192.168.1.5:7420`, Default-Allowlist → passt (Regressionstest D1).
  - Origin `http://[::1]:7420`, Host `[::1]:7420`, bind `127.0.0.1` → passt (D5).
  - `bind_host="0.0.0.0"`, Origin/Host `0.0.0.0:7420` → `SecurityError`.
  - Alle 7 bestehenden `TestCheckOrigin`-Tests unverändert grün (insb. DNS-Rebinding, leerer Origin, fehlender Host).
- [ ] Step 2: Implementieren.
- [ ] Step 3: `python3 -m pytest tests/test_admin_server.py -k CheckOrigin -q` grün.
- [ ] Step 4: Commit `fix(admin): apply bind host symmetrically to origin and host checks`

### Task 897-3: Effektive Allowlist = Defaults ∪ Config ∪ CLI ∪ eigene IPs (D2, D3, D6)

**Files:** Modify `scripts/admin-server.py` (`AdminServer.__init__`, neue Helfer); Test `tests/test_admin_server.py` (neue Klasse `TestEffectiveAllowedHosts`)
**Interfaces:**
- Produces: `def _local_interface_addresses() -> tuple[str, ...]` — eigene nicht-Loopback-, nicht-Link-Local-IP-Literale via `socket.getaddrinfo(socket.gethostname(), None)` + UDP-Route-Probe (`socket.socket(AF_INET, SOCK_DGRAM).connect(("192.0.2.1", 9))`, sendet kein Paket); best-effort, wirft nie, liefert `()` bei Fehler. **Nur IP-Literale (via `ipaddress` validiert), keine Hostnamen.**
- Produces: `def _effective_allowed_hosts(*, cli: Iterable[str] | None, config: Iterable[str], bind_host: str, bind_port: int) -> tuple[str, ...]` — normalisiert via `_normalize_allowed_host`; reihenfolgestabil dedupliziert; `DEFAULT_ALLOWED_HOSTS` immer enthalten; bei `bind_host ∈ WILDCARD_BIND_HOSTS` zusätzlich `_local_interface_addresses()`. `ValueError` propagiert → Startabbruch mit klarer Meldung (stderr + Exit ≠ 0).
- Modifies: `AdminServer.__init__` Z. 5564 → `effective_allowed_hosts = _effective_allowed_hosts(cli=allowed_hosts, config=admin_cfg["allowed_hosts"], bind_host=host, bind_port=port)`; danach: wenn `host ∉ LOOPBACK_HOSTS` und keine Nicht-Loopback-Entry in der Menge (konkreter Bind-Host zählt als Entry) → stderr-Warnung `"  !  No non-loopback allowed host — remote saves will be rejected (403). Pass --allowed-hosts <host>."`.
- Consumes: 897-1.

- [ ] Step 1: Tests (fail):
  - `cli=("myhost",)`, config default, bind `127.0.0.1` → enthält `127.0.0.1`, `localhost`, `[::1]`, `myhost` (D3).
  - bind `0.0.0.0`, `_local_interface_addresses` gemockt auf `("192.168.1.5",)` → enthält `192.168.1.5` (D2).
  - `config=["10.0.0.2:7420"]`, port 7420 → enthält `10.0.0.2` (D4 end-to-end).
  - `cli=("*",)` → `ValueError`.
  - `AdminServer(root, host="0.0.0.0", admin_token="t", port=0)` mit gemocktem `_DaemonThreadingHTTPServer` und `_local_interface_addresses → ()` → stderr enthält „No non-loopback allowed host" (D6).
  - `_local_interface_addresses()` mit `socket.getaddrinfo` → `OSError` gemockt liefert `()`.
- [ ] Step 2: Implementieren.
- [ ] Step 3: `python3 -m pytest tests/test_admin_server.py -q` komplett grün (inkl. `TestBindHostEnforcement`).
- [ ] Step 4: Commit `fix(admin): extend loopback allowlist and auto-allow own interface IPs`

### Task 897-4: Fehler in der UI sichtbar machen (U1, U2)

**Files:** Modify `docs/ui/admin-ui.html`; Test `tests/browser/test_admin_ui_network_mode.py` (Create, `test_forbidden_mutation_surfaces_error_and_clears_modal`)
**Interfaces:**
- Produces (JS): `window.addEventListener("unhandledrejection", (ev) => { if (ev.reason instanceof APIError) { toast(\`Request failed: ${ev.reason.message}\`, "error"); ev.preventDefault(); } })` — ein zentraler Punkt für alle `try/finally`-Handler ohne `catch`.
- Modifies (JS): „Create Backup"-Handler (Z. 8333-8344): `hideModal()` in `finally`, `alert(...)` → `toast(\`Backup failed: ${e.message}\`, "error")`. Gleiche Ersetzung in Restore/Delete (Z. 8311-8322).
- Consumes: bestehende `toast`, `APIError`, `hideModal`.

- [ ] Step 1: Browser-Test (fail): `page.route("**/api/backups/create", lambda r: r.fulfill(status=403, json={"error":"forbidden","detail":"origin not allowed: 'http://x:7420'"}))`; Dialog-Handler akzeptiert `prompt()`; Klick „Create Backup" → `#modal-overlay` hidden **und** `.toast-error` mit „origin not allowed" innerhalb 3 s.
- [ ] Step 2: Implementieren.
- [ ] Step 3: `pytest tests/browser/test_admin_ui_network_mode.py -k forbidden -v` grün.
- [ ] Step 4: Commit `fix(admin-ui): surface rejected mutations instead of hanging`

### Task 897-5: E2E-Regressionstest Nicht-Loopback-Origin

**Files:** Modify `tests/browser/test_admin_ui_network_mode.py`, `tests/browser/README.md`
**Interfaces:**
- Produces: modul-lokale Fixture `network_server` — startet `scripts/admin-server.py --host 127.0.0.2 --port 7422 --no-viz --root <REPO_ROOT>` mit `env ADMIN_UI_TOKEN=e2e-token` (nicht argv); `pytest.skip` wenn `sys.platform != "linux"`. `127.0.0.2 ∉ LOOPBACK_HOSTS` → reproduziert den Network-Pfad (Token-Pflicht + fremder Origin) ohne LAN.
- Produces: `test_mutation_from_bind_origin_is_accepted` — navigiert `http://127.0.0.2:7422/?token=e2e-token`, führt im Seitenkontext `fetch("/api/sync/dry-run", {method:"POST", headers:{Authorization:"Bearer e2e-token"}})` aus (Route existiert, Z. 3572; seiteneffektfrei, aber origin-geprüft) und erwartet Status ≠ 403.
- Consumes: 897-2, `tests/browser/conftest.py::_wait_for_server`.

- [ ] Step 1: Test schreiben; gegen Stand vor 897-2 → 403 „origin not allowed" (rot beobachten, DoD).
- [ ] Step 2: (Implementierung bereits durch 897-2/897-3.)
- [ ] Step 3: `pytest tests/browser/test_admin_ui_network_mode.py -v` grün; README-Layout-Tabelle ergänzt.
- [ ] Step 4: Commit `test(admin-ui): add network-origin e2e regression for #897`

### Task 897-6: Doku/Schema an korrigierte Semantik angleichen

**Files:** Modify `config/project-config.schema.json` (`admin-ui.allowed-hosts.description`), `docs/howto/admin-ui-remote-access.md`, `rules/2-platform/agent-meta-admin-ui.md` (+ Troubleshooting „HTTP 403 origin not allowed"), `--help`-Text von `--allowed-hosts` in `scripts/admin-server.py`
**Interfaces:**
- Produces: Schema-Beschreibung: „Hostnames or IP literals (optional `:<port>` equal to the admin port) additionally allowed as Origin/Host. Always extends the loopback defaults. Wildcards (`*`, `0.0.0.0`, `::`) are rejected. When bound to a wildcard address the server's own interface IPs are allowed automatically."
- Consumes: Verhalten aus 897-1..3.

- [ ] Step 1: Test (fail): `test_schema_allowed_hosts_description_matches_semantics` in `tests/test_admin_server.py` — Schema-Description enthält **nicht** mehr `host:port origins`, enthält `extends the loopback defaults`.
- [ ] Step 2: Doku/Schema ändern; `python scripts/sync.py` regeneriert `.claude/skills/admin-ui/SKILL.md`.
- [ ] Step 3: `python3 scripts/sync.py --validate` + Test grün.
- [ ] Step 4: Commit `docs(admin): document corrected allowed-hosts semantics`

---

## 8. Tasks #896 (PR 2, nach Merge von PR 1; Branch-Vorschlag `feat/896-admin-network-mode`)

### Task 896-1: `--mode local|network` + Bind-Auflösung (Config wird wirksam)

**Files:** Modify `scripts/admin-server.py` (`main()`, neuer Helfer); Test `tests/test_admin_server.py` (`TestResolveBind`)
**Interfaces:**
- Produces: CLI `--mode {local,network}` (Default `None`); `--host`/`--port` Default `None`.
- Produces: `def _resolve_bind(*, mode: str | None, cli_host: str | None, cfg_bind_host: str) -> str` — `local` → `"127.0.0.1"` (`ValueError`, falls `cli_host` gesetzt und `∉ LOOPBACK_HOSTS`); `network` → `cli_host` falls gesetzt und `∉ LOOPBACK_HOSTS`, sonst `cfg_bind_host` falls `∉ LOOPBACK_HOSTS`, sonst `"0.0.0.0"`; `None` → `cli_host or cfg_bind_host`.
- Modifies: `main()` nutzt `_resolve_bind` und `args.port or admin_cfg["port"]`; `_admin_start_detached`/`_admin_status` erhalten die aufgelösten Werte.
- Consumes: `_load_admin_ui_config`.

- [ ] Step 1: Tests (fail): `("local", None, "0.0.0.0")`→`"127.0.0.1"`; `("network", None, "127.0.0.1")`→`"0.0.0.0"`; `("network", "10.0.0.2", "127.0.0.1")`→`"10.0.0.2"`; `(None, None, "10.0.0.2")`→`"10.0.0.2"`; `("local", "0.0.0.0", "127.0.0.1")`→`ValueError`.
- [ ] Step 2: Implementieren.
- [ ] Step 3: `python3 -m pytest tests/test_admin_server.py -k ResolveBind -q` grün.
- [ ] Step 4: Commit `feat(admin): add --mode local|network and honor admin-ui bind config`

### Task 896-2: Auto-generiertes Token im Network-Mode

**Files:** Modify `scripts/admin-server.py`; Test `tests/test_admin_server.py` (`TestEnsureAdminToken`)
**Interfaces:**
- Produces: `ADMIN_TOKEN_FILE = ".meta-viz/admin-token"` (`.meta-viz/` gitignored).
- Produces: `def _ensure_admin_token(root: Path, resolved: str | None) -> tuple[str, bool]` — `(resolved, False)`, wenn bereits ein Token aufgelöst ist; sonst vorhandene Token-Datei lesen → `(token, False)`; sonst `secrets.token_urlsafe(32)` erzeugen, Datei mit `0o600` schreiben (best-effort chmod wie bestehendes Muster), `(token, True)`.
- Modifies: Aufruf **nur bei `mode == "network"`** (Q3-Empfehlung), **vor** der bestehenden Fail-closed-Prüfung (Z. 5566-5572). Die Prüfung bleibt unverändert und greift weiter für `--host <non-loopback>` ohne `--mode network` und ohne Token (`TestBindHostEnforcement` unverändert grün).
- Consumes: `_resolve_admin_token`.

- [ ] Step 1: Tests (fail): leere tmp-root → Datei entsteht, Mode `0o600` (POSIX), 2. Aufruf liefert dasselbe Token mit `generated=False`; `resolved="x"` → keine Datei.
- [ ] Step 2: Implementieren.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit `feat(admin): auto-generate persisted token for network mode`

### Task 896-3: Token nie über argv / Log

**Files:** Modify `scripts/admin-server.py` (`_admin_start_detached`); Test `tests/test_admin_server.py` (`TestDetachedStartTokenTransport`)
**Interfaces:**
- Modifies: `_admin_start_detached(args)` — entfernt `cmd += ["--admin-token", …]` (Z. 5694); übergibt Token per `env={**os.environ, "ADMIN_UI_TOKEN": token}` an `subprocess.Popen`.
- Consumes: 896-2.

- [ ] Step 1: Test (fail): `subprocess.Popen` gemockt; `--admin-token` nicht in `cmd`; `env["ADMIN_UI_TOKEN"] == token`.
- [ ] Step 2: Implementieren.
- [ ] Step 3: Test grün.
- [ ] Step 4: Commit `fix(admin): pass admin token to detached child via env, not argv`

### Task 896-4: Start-Banner mit erreichbaren URLs + Firewall-Hinweis

**Files:** Modify `scripts/admin-server.py` (`AdminServer.start`, `_admin_start_detached`, `_admin_status`); Test `tests/test_admin_server.py` (`TestNetworkBanner`)
**Interfaces:**
- Produces: `def _reachable_urls(bind_host: str, port: int) -> list[str]` — Wildcard-Bind → `http://<_url_host(ip)>:<port>/` je `_local_interface_addresses()` plus `http://127.0.0.1:<port>/`; konkreter Bind → genau `http://<_url_host(bind_host)>:<port>/`.
- Produces: `def _network_banner(urls: list[str], port: int, token: str | None) -> list[str]` — reine Funktion: URL-Zeilen; wenn `token` gesetzt: `Token: <token>` (+ Deep-Link je nach Q5); Firewall-Zeile `Allow inbound TCP <port> only from trusted networks (host firewall / security group).`; Tunnel-Alternative `ssh -L <port>:127.0.0.1:<port> <user>@<host>`.
- Modifies: `AdminServer.start()` druckt Banner **ohne Token** (Child-stdout = Logdatei); `_admin_start_detached` (Parent) druckt Banner **mit** Token nur, wenn in 896-2 neu erzeugt, sonst Pfad zur Token-Datei; ersetzt alle `http://0.0.0.0:…`-Ausgaben.
- Consumes: `_local_interface_addresses`, `_url_host` (#897).

- [ ] Step 1: Tests (fail): `_reachable_urls("0.0.0.0", 7420)` mit gemockten IPs enthält `http://192.168.1.5:7420/`, kein `0.0.0.0`; `_network_banner(..., token=None)` ohne `Token:`-Zeile, mit Firewall-Zeile; `AdminServer.start` (gemocktes `serve_forever`) schreibt das Token nicht nach stdout.
- [ ] Step 2: Implementieren.
- [ ] Step 3: Tests grün.
- [ ] Step 4: Commit `feat(admin): print reachable URLs and firewall guidance on start`

### Task 896-5: `/admin`-Command + Doku

**Files:** Modify `commands/1-generic/admin.md`, `rules/2-platform/agent-meta-admin-ui.md`, `docs/howto/admin-ui-remote-access.md`
**Interfaces:**
- Produces: `argument-hint: "[start | stop | status | restart] [--mode local|network] [--allowed-hosts HOST...] [--no-viz] [--port <port>]"`; Bullets für beide Modi; Flag-Tabelle der Rule um `--mode`; Howto-Abschnitt „Quick start: network mode" (Token-Datei, Banner, Firewall, Rotation durch Löschen von `.meta-viz/admin-token`).
- Produces (AC-896-7): Howto-/Rule-Abschnitt „Binding der Nebendienste bei `--host 0.0.0.0`" — für **Viz-Dashboard (Port 8765)** und **MCP (Port 9090)** getrennt: an welche Adresse gebunden, ob netzwerkweite Exposition beabsichtigt. Ist-Verhalten vorher im Code ermitteln, nicht annehmen.
- Consumes: 896-1..4.

- [ ] Step 1: Test (fail): `tests/test_admin_server.py::test_admin_command_documents_mode_flag` — `commands/1-generic/admin.md` enthält `--mode`.
- [ ] Step 2: Doku ändern; `python scripts/sync.py` regeneriert `.claude/commands/admin.md` + `.claude/skills/admin-ui/SKILL.md`.
- [ ] Step 3: `python3 scripts/sync.py --validate` + Test grün.
- [ ] Step 4: Commit `docs(admin): document local/network start modes`

---

## 9. Security-Design Origin-Check / Allowlist

**Invarianten (dürfen durch #897/#896 nicht fallen):**

1. Jede Mutation erfordert Token (Bind `∉ LOOPBACK_HOSTS`) **und** passenden Origin (falls gesendet) **und** passenden Host.
2. Die Allowlist enthält nur **konkret benannte** Hosts: Loopback-Defaults, explizite Config/CLI-Einträge, konkreter Bind-Host, eigene Interface-IP-Literale bei Wildcard-Bind.
3. DNS-Rebinding-Schutz bleibt: ein Angreifer-Hostname gelangt nie in die Menge (eigene IPs sind IP-Literale). `test_dns_rebinding_forged_host_rejected_even_with_matching_origin` bleibt unverändert grün.
4. Ein `Origin: http://<eigene-ip>:<port>` kann nur von einer Seite stammen, die von genau diesem IP:Port-Socket ausgeliefert wurde — also vom Admin-Server selbst. Auto-Allow eigener IP-Literale erweitert die Angriffsfläche nicht.
5. **Kein Wildcard-Origin — verbindlich und nicht konfigurierbar:**
   - Kein `"*"`, kein Glob-/Suffix-/Regex-/CIDR-Matching; Vergleich ausschließlich exakte Mengen-Gleichheit nach Normalisierung.
   - Wildcard-Bind-Adressen (`0.0.0.0`, `::`, `[::]`, `""`) werden **nie** Teil der Allowlist — weder als Eintrag (`ValueError` beim Start) noch implizit über `bind_host`.
   - Eingehender `Origin`/`Host` wird **nie** in die Allowlist gespiegelt — auch nicht bei gültigem Token.
   - Kein Modus, Flag oder Config-Key schaltet den Origin/Host-Check ab — auch nicht `--mode network`.
   - `*`/Wildcards in `allowed-hosts` führen zu **Startabbruch** (fail-closed), nicht zu stillem Ignorieren.

**Verworfene Optionen:**

| Option | Verworfen weil |
|---|---|
| Allowlist `"*"` / Origin-Check im Network-Mode abschalten | Im Loopback-Mode gibt es **kein Token** (`check_token` No-op) — der Origin/Host-Check ist dort die **einzige** CSRF-/Rebinding-Abwehr. Im Network-Mode bliebe nur das Token als Einzelschutz (SSE-Query-Token in Proxy-Logs, Howto §10). Vom Nutzer explizit ausgeschlossen. |
| Eingehenden `Host`/`Origin` übernehmen, wenn Token stimmt | Macht die Origin-Prüfung zur Token-Prüfung; entfernt Defense-in-Depth bei Token-Leak. |
| Eigenen Hostnamen (`socket.gethostname()`, `.local`) automatisch erlauben | Per DNS/mDNS im LAN fälschbar → Rebinding-Vektor. Nur explizit via `--allowed-hosts`. (Q2) |
| Origin-Check auf GET ausweiten | Out of scope; GET ist token-gated und seiteneffektfrei. |

---

## 10. Offene Entscheidungsfragen an den Nutzer (12)

1. **Q1 — Auto-Allowlist eigener IPs in #897?** Empfehlung: ja (behebt das Symptom ohne Nutzeraktion, sicher per §9 Inv. 4). Alternative: nur Startup-Warnung + explizites `--allowed-hosts`; Helfer wandert nach #896.
2. **Q2 — Eigenen Hostnamen automatisch erlauben?** Empfehlung: nein (§9). Bestätigen.
3. **Q3 — Auto-Token auch bei `--host <non-loopback>` ohne `--mode network`?** Empfehlung: nein — Auto-Token nur bei `--mode network`; bestehende Aufrufe bleiben fail-closed (`TestBindHostEnforcement` unverändert). 896-2 ist so spezifiziert.
4. **Q4 — Token-Persistenz/Rotation:** Vorschlag: persistiert in `.meta-viz/admin-token` (0600, gitignored), Rotation = Datei löschen. Alternative: ephemer pro Start. `--rotate-token`-Flag gewünscht? (Plan sieht es nicht vor.)
5. **Q5 — Token im Banner:** Vorschlag: nur beim Erzeugen, nur vom Parent (nie im Log), danach nur Dateipfad. Deep-Link `http://<ip>:<port>/?token=…` drucken?
6. **Q6 — `--allowed-hosts`-Syntax:** `name`, `name:<admin-port>`, IPv4, IPv6, `[IPv6]:<port>`; Leerzeichen-getrennt (bestehend). Kommaliste zusätzlich? CIDR? Empfehlung: kein CIDR (§9 Inv. 5).
7. **Q7 — Firewall-Hinweis:** generisch + SSH-Tunnel (Plan) oder plattformspezifische Befehle?
8. **Q8 — `admin-ui.mode` als Config-Key?** Plan: nein — `admin-ui.bind-host` ist das persistente Äquivalent.
9. **Q9 — Reverse-Proxy/HTTPS-Origins:** Empfehlung: eigenes Issue (Nicht-Ziel hier).
10. **Q10 — Issue-Text-Abgleich (§0.1):** Benennt #897 den UI-„Hänger" anders als U1/U2, oder fordert #896 mehr als §8?
11. **Q11 — Reihenfolge:** #897 → #896 als zwei PRs (§4). Einverstanden?
12. **Q12 — #899 Doku-Restlücke:** Fordert der Issue-Body von #899 eine `docs/`-Änderung über PR #913 hinaus? Ja → S-Task (`documenter`); nein → #899 komplett erledigt.

---

## 11. Acceptance Criteria

### #897
- **AC-897-1:** Given Server mit konkretem Nicht-Loopback-Bind (`--host 127.0.0.2` bzw. LAN-IP) + Token, When Mutation mit Origin/Host = Bind-Adresse, Then Status ≠ 403. (897-2, 897-5)
- **AC-897-2:** Given `--host 0.0.0.0` + Token, When Mutation mit Origin/Host = eigene Interface-IP, Then ≠ 403; When Origin/Host = fremder Name, Then 403 `origin not allowed`. (897-3, Q1)
- **AC-897-3:** Given `--allowed-hosts myhost`, Then effektive Allowlist enthält `myhost` **und** `127.0.0.1`, `localhost`, `[::1]`. (897-3)
- **AC-897-4:** Given `allowed-hosts`-Eintrag `host:<admin-port>`, `::1` oder `[::1]:7420`, When Browser-Origin dieses Hosts, Then Match. (897-1, 897-2)
- **AC-897-5:** Given `*`, `*.lan`, `0.0.0.0`, `::`, `host:<fremder-port>` oder `http://…` in `allowed-hosts` (CLI oder Config), When Start, Then Abbruch mit Exit ≠ 0 und Meldung `invalid allowed-hosts entry`. (897-1, 897-3)
- **AC-897-6:** Alle bestehenden `TestCheckOrigin`-Tests (CSRF, DNS-Rebinding, leerer Origin, fehlender Host) unverändert grün. (897-2)
- **AC-897-7:** Given Mutation wird mit 403 abgelehnt, Then sichtbarer `.toast-error` innerhalb 3 s und kein Modal-Overlay bleibt offen. (897-4)
- **AC-897-8:** Given Bind `∉ LOOPBACK_HOSTS` ohne Nicht-Loopback-Allowed-Host, When Start, Then stderr enthält „No non-loopback allowed host". (897-3)
- **AC-897-9:** Schema-Description enthält nicht mehr `host:port origins`; Howto/Rule/`--help` beschreiben dieselbe Semantik; `sync.py --validate` grün. (897-6)
- **AC-897-10:** Given Bind `0.0.0.0`, When Host/Origin `0.0.0.0:<port>`, Then 403 (Wildcard nie in Allowlist, §9 Inv. 5). (897-2)

### #896
- **AC-896-1:** `--mode local` bindet `127.0.0.1` ohne Token-Pflicht; `--mode local --host <non-loopback>` → Startabbruch; `--mode network` bindet `0.0.0.0` (oder konfigurierte Nicht-Loopback-Adresse). (896-1)
- **AC-896-2:** `admin-ui.bind-host`/`admin-ui.port` aus `project.yaml` wirken, wenn kein CLI-Wert gesetzt ist. (896-1)
- **AC-896-3:** `--mode network` ohne konfiguriertes Token erzeugt ein Token (0600-Datei, wiederverwendet); Mutationen funktionieren (setzt AC-897-2 voraus). (896-2)
- **AC-896-4:** Token erscheint weder in argv des Child-Prozesses noch in `.meta-viz/admin-server.log`. (896-3, 896-4)
- **AC-896-5:** Startausgabe listet erreichbare URLs (keine `0.0.0.0`-URL) und Firewall-/Tunnel-Hinweis. (896-4)
- **AC-896-6:** `--mode` und `--allowed-hosts` sind in `/admin`-Command und Doku beschrieben. (896-5)
- **AC-896-7:** Binding von Viz-Dashboard (8765) und MCP (9090) bei `--host 0.0.0.0` ist je Dienst dokumentiert (beabsichtigte Exposition ja/nein). (896-5)
- **AC-896-8:** `--host <non-loopback>` ohne `--mode network` und ohne Token bricht weiter ab (`TestBindHostEnforcement` unverändert grün; Q3). (896-2)

### #899 (Status-Tracking)
- **AC-899-1:** `gh pr view 913` → `MERGED`; `gh issue view 899` → `CLOSED` (sonst schließen). Restlücke nur bei Q12 = ja.

### #855 (Status-Tracking)
- **AC-855-1:** `gh pr view 905` → `MERGED`; `gh issue view 855` → `CLOSED` (sonst schließen).

---

## 12. Testplan

| Ebene | Datei | Abdeckung |
|---|---|---|
| Unit | `tests/test_admin_server.py` | `TestNormalizeAllowedHost`, `TestCheckOrigin` (erweitert), `TestEffectiveAllowedHosts`, Schema-Description-Check (#897); `TestResolveBind`, `TestEnsureAdminToken`, `TestDetachedStartTokenTransport`, `TestNetworkBanner`, Command-Doku-Check, `TestBindHostEnforcement` unverändert (#896) |
| Browser/E2E | `tests/browser/test_admin_ui_network_mode.py` (**neu**) | Echte Browser-Origin über `127.0.0.2:7422` (Linux), 403-Sichtbarkeit via `page.route` |
| Gate | `python3 scripts/sync.py --validate` | Schema/Doku/generierte Artefakte |
| Manuell (einmalig, vor Merge #896) | zweites Gerät im LAN | `--mode network` → Banner-URL öffnen → Save + Backup |

Hinweis: Der Browser-Test nutzt `fetch` im Seitenkontext eines pytest-Playwright-Tests; das MCP-Verbot für `browser_evaluate` (`mcp-guardrails.md`) betrifft nur das Playwright-**MCP**-Tool.

---

## 13. Self-Review (Finalisierung 2026-10-07, concept-specifier)

| Check | Ergebnis |
|---|---|
| Pflicht-Header (Status, Trace-Anker, Problem/Ziel/Nicht-Ziele) | ✔ Frontmatter `status: DRAFT`, `spec-id`; Nicht-Ziele ergänzt |
| Platzhalter (`TODO`/`TBD`) | ✔ keine; offene Punkte nur als Q1–Q12 |
| Interfaces vollständig typisiert | ✔ jede Task: Datei, Symbol, Signatur, Fehlerpfad, Testname, Commit |
| AC-Abdeckung | ✔ AC-897-1..10 → 897-1..6; AC-896-1..8 → 896-1..5; jede AC ≥1 Task, jeder Task ≥1 Test |
| Issue-Nummern-Konsistenz | ✔ #897 Bug/Origin, #896 Feature/Modi, #899 ↔ PR #913, #855 ↔ PR #905 |
| Wildcard-Verbot eindeutig | ✔ §9 Inv. 5 (verbindlich, nicht konfigurierbar, fail-closed) + AC-897-5/-10 |
| Reihenfolge #897 → #896 | ✔ Sanity-Check §4 |
| Code-Claims | ✔ re-verifiziert (Header-Zeilennummern) |

Korrekturen gegenüber Entwurf:
- #899: PENDING → erledigt via PR #913 (gemergt laut Orchestrator; Live-Bestätigung über AC-899-1 ausstehend).
- §0.2/§0.3 aktualisiert (Dokument ist jetzt die Spec; Arbeitsbaum-Konflikt nicht mehr sichtbar).
- Widerspruch 896-2 („Aufruf bei nicht-loopback Bind") vs. Q3-Empfehlung („nur `--mode network`") aufgelöst → nur `--mode network`; AC-896-8 ergänzt.
- „loopback" einheitlich als `LOOPBACK_HOSTS`-Mitgliedschaft definiert (§6).
- §9 Inv. 5 (Wildcard-Verbot) explizit; AC-897-10 und Verhaltensänderung `0.0.0.0:<port>`-Host (897-2) dokumentiert.
- ACs in Given/When/Then-Form geschärft; AC-897-5 um Exit-Code + Meldung, AC-896-1 um `--mode local --host <non-loopback>` ergänzt.
- 897-6 um `--help`-Text ergänzt (D3 nennt `--help` als betroffene Stelle).

Grenzen: Issue-Texte und PR-Status nicht live gelesen (§0.1).
