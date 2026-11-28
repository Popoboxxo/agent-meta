# agent-meta — Admin-Server / Admin-UI Betriebswissen

Betriebswissen für `scripts/admin-server.py` — den zero-dependency HTTP-Server
(Python stdlib + PyYAML), der die visuelle Konfigurations-Oberfläche von
agent-meta (`docs/ui/admin-ui.html`) ausliefert und REST/SSE-Endpunkte über die
YAML/JSON-Configs des Frameworks bereitstellt.

## Zwei Modi

- `super_admin` — Server läuft im agent-meta-Repo selbst (`agents/1-generic/`
  existiert); alle Super-Admin-Configs sind editierbar.
- `project_admin` — Server läuft in einem Ziel-Repo mit agent-meta als
  Submodul; nur `.meta-config/project.yaml` ist exponiert.

## Setup-Modus (REQ-ADM-01..03)

- **Zustand:** `GET /api/mode` liefert `setup_required: true`, solange
  `<root>/.meta-config/project.yaml` fehlt (berechnet, nicht persistiert). Der
  Server startet trotzdem (kein Abbruch).
- **Endpunkte** (token-gated, sofern ein Token konfiguriert ist, Mutationen origin-geprüft):
  - `GET /api/setup/options` — Provider, Git-Plattformen, DoD-Presets, Defaults.
  - `POST /api/setup/config` — legt `project.yaml` an, nur create-only: 400 mit
    `detail`-Liste bei ungültigen Antworten, 409 `already_configured`, wenn die
    Datei existiert. Fester Zielpfad, Modus 0600, create-only (Link, Fallback O_EXCL-Kopie).
  - `POST /api/setup/init-sync` — führt `sync.py --config … --init` aus
    (Subprozess-Timeout 300 s). Ohne Config: 409 `setup_required`.
- **Guard:** `SyncExecutor` (`run`, `dry_run`, `cleanup_preview`) startet ohne
  `project.yaml` keinen Subprozess und meldet `project.yaml missing`. So hängt
  kein interaktiver CLI-Wizard.
- **Auth:** Im Setup-Modus existiert keine `project.yaml` und damit kein
  `admin-ui.token`. Non-loopback (`--host`/`--mode network`) startet nur mit
  Token aus `--admin-token`, Env `ADMIN_UI_TOKEN` oder dem Netzwerk-Modus
  (Zufalls-Token); sonst fail-closed.
- **Wizard-Ablauf** (`docs/ui/admin-ui.html`, `init()`): bei `setup_required`
  nur der Wizard, keine Navigation. Schritte: Identity → Provider → Git →
  DoD-Preset (optional) → Review → „Anlegen“ (`POST /api/setup/config`) →
  „Erst-Sync starten“ (`POST /api/setup/init-sync`, Ausgabe in der UI) →
  Reload in den Normalbetrieb.
- **Fehleranzeige (REQ-ADM-03):** Schreibversuch auf eine nicht-schreibbare
  Section → 400 (`section not allowed: …`), keine Datei-Änderung. Die UI zeigt
  den fehlgeschlagenen Save als Toast plus Inline-Meldung.

## Server-Lifecycle

```bash
python3 scripts/admin-server.py start     # detached Hintergrund-Start, kehrt sofort zurück
python3 scripts/admin-server.py stop      # stoppt Admin UI + Viz + MCP
python3 scripts/admin-server.py status    # zeigt Laufzustand (Admin UI / Viz / MCP)
python3 scripts/admin-server.py restart   # stop dann start
python3 scripts/admin-server.py           # ohne Subcommand: Vordergrund bis Ctrl+C
```

`start` bringt alle drei Dienste gemeinsam hoch (Admin UI + Viz-Dashboard +
MCP-SSE-Server, sofern nicht `--no-viz`); `stop` reißt alle drei gemeinsam ab.

## Flags

| Flag | Default | Bedeutung |
|------|---------|-----------|
| `--mode local\|network` | `local` (Verhalten) | Startmodus (Issue #896): `local` = Loopback, kein Token; `network` = `0.0.0.0`, Zufalls-Token (nicht persistiert), erreichbare URLs + Firewall-Hinweis |
| `--port PORT` | `7420` | Admin-UI-Port |
| `--host HOST` | `127.0.0.1` | Bind-Adresse; non-loopback erzwingt Token |
| `--admin-token TOKEN` | — | Auth-Token für Remote-Zugriff (Pflicht bei non-loopback) |
| `--allowed-hosts HOST…` | `127.0.0.1 localhost ::1` | zusätzliche erlaubte Origin-Hosts (erweitert, ersetzt nicht) |
| `--root PATH` | `.` | Projekt-Root |
| `--watch` | aus | Filesystem-Watcher (pollt Config-Dateien alle 2s) |
| `--no-viz` | aus | Viz-Dashboard + MCP-Server nicht mitstarten |

## Port-Matrix

| Dienst | Default-Port | Bind (Ist-Stand Code) | Netzweit konfigurierbar? |
|--------|--------------|------------------------|---------------------------|
| Admin UI | `7420` | `--host` (Default `127.0.0.1`) | ja — `--mode network` / `--host 0.0.0.0` + Token |
| Viz-Dashboard (`viz-report.py --serve`) | `8765` | hart `127.0.0.1` (`viz-report.py:912`) | nein (siehe Entscheidung 31) |
| MCP-SSE-Server (`viz-logger.py --http`) | `9090` | hart `127.0.0.1` (`viz-logger.py:580`) | nein (siehe Entscheidung 31) |

## Startmodus `local` / `network` (Issue #896)

- `local` (Default, verhaltensidentisch zu früher): bindet `127.0.0.1`, **kein Token**. Ein
  explizites `--host` mit non-loopback wird im local-Modus mit `ValueError` abgewiesen —
  `local` kann den Server nie netzweit exponieren.
- `network`: bindet `0.0.0.0` (bzw. ein explizites non-loopback `--host` / konfiguriertes
  `admin-ui.bind-host`). Das Token wird vor der Fail-closed-Prüfung erzeugt, **nur in der
  Startausgabe** ausgegeben und **nicht persistiert** (keine Token-Datei, kein Config-/Env-Write).
  Rotation = Neustart. Ausgabe: erreichbare URLs (`http://<ip>:7420/?token=<T>`), `Token: <T>`,
  Firewall-Hinweis und Sicherheitswarnung. `--allowed-hosts` für Writes von anderen Maschinen.
- Token-Transport zum Child-Prozess ausschließlich über Env `ADMIN_UI_TOKEN` — **nie** in argv
  (`ps`) und **nie** in `.meta-viz/admin-server.log`.
- **Firewall:** Allow inbound TCP `7420` only from trusted networks (Host-Firewall / Security
  Group). Port `7420` nicht öffentlich freigeben.
- **Sicherheitswarnung (network):** netzweiter Zugriff — Token wie ein Passwort behandeln,
  TLS / Reverse-Proxy verwenden, Exposure über `--allowed-hosts` begrenzen. Alternative: im
  local-Modus bleiben und per SSH-Tunnel (`ssh -L 7420:127.0.0.1:7420 user@host`) zugreifen.

## Bindeverhalten 8765/9090 bei `--host 0.0.0.0` — Entscheidung 31

- **Ist-Stand (code-verifiziert):** Viz-Dashboard `8765` bindet hart `127.0.0.1`
  (`scripts/viz-report.py:912`); MCP-SSE `9090` bindet hart `127.0.0.1`
  (`scripts/viz-logger.py:580`, `--http` ohne Host-Option). Beide bleiben auch bei
  `--host 0.0.0.0` des Admin-UI lokal.
- **Verbindliche Roadmap-Entscheidung 31 (N12):** beide Dienste netzweit konfigurierbar, je
  eigene Option mit sicherem Default. Die heutige Härtung auf Loopback ist die sichere
  Default-Variante; die netzweite Konfigurierbarkeit ist eine **offene Umsetzungslücke**
  (eigene Spec), keine neue Entscheidung dieses Starts. Keine `scripts/viz-*.py` ändern.

## Host-Bindung + Token-Regeln

- **Default: Loopback** (`127.0.0.1`) → kein Token nötig.
- **Non-loopback** (`--host 0.0.0.0`) → Token **erzwungen** (fail-closed: der
  Server verweigert den Start ohne Token).
- Token-Auflösung (Priorität): `--admin-token` > Env `ADMIN_UI_TOKEN` >
  `admin-ui.token` in `project.yaml` > `admin-ui.token-file`.

## Token-Distribution

- `Authorization: Bearer <token>` Header — für alle `/api/*`-Requests.
- `?token=<token>` Query-Parameter — Bequemlichkeit für den Browser: die UI
  übernimmt das Token nach `sessionStorage` und entfernt es aus der URL (kein
  `localStorage`, kein Verbleib in der History).
- Die UI-Shell (`/`, `/favicon.png`) ist public; jeder `/api/*`-Endpoint ist
  token-gated, Mutationen zusätzlich origin-geprüft (CSRF/DNS-Rebinding).

## Token-Persistenz

`admin-ui.token` in `.meta-config/project.yaml`:

```yaml
admin-ui:
  token: "..."
```

## Diagnose-Folge

1. Lauschende Ports prüfen:

   ```bash
   ss -tlnp
   ```

2. Server-Log lesen:

   ```bash
   cat .meta-viz/admin-server.log
   ```

3. Smoke-Test gegen den Health-Endpoint:

   ```bash
   curl -H "Authorization: Bearer <T>" http://127.0.0.1:<port>/api/health
   ```

## Known Issues

- **PID-Management erkennt fremde nohup-Instanzen nicht:** `status`/`stop`
  verlassen sich auf die PID-Datei `.meta-viz/.admin-server-pid`, die nur beim
  `start`-Subcommand geschrieben wird. Ein manuell per `nohup … &` gestarteter
  Server hinterlässt keine PID-Datei und wird von `status`/`stop` nicht erkannt.
- **`python` vs `python3` auf Linux-Hosts:** der detached Start re-invoked sich
  selbst über `sys.executable`; die Doku nutzt `python3`. Hosts ohne
  `python3`-Alias müssen ggf. `python` verwenden.

## Troubleshooting

- **ERR_CONNECTION_REFUSED** → Server bindet loopback-only (`127.0.0.1`).
  Remote-/Container-Zugriff braucht `--mode network` (setzt `0.0.0.0` + Token
  und gibt die erreichbare URL aus) oder manuell `--host 0.0.0.0` (+ Token).
- **HTTP 401** → Token fehlt oder ungültig (`Authorization: Bearer <T>` bzw.
  `?token=<T>` setzen).
- **Port-Kollision** → Port ist belegt; der detached Start schlägt fehl
  (crash-loop, siehe `admin-server.log`). Freien Port via `--port` wählen.
