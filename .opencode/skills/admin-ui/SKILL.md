---
name: admin-ui
description: "Use when operating the admin-server/admin-ui in agent-meta — lifecycle, host binding, token auth, port matrix, troubleshooting."
---

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
| `--port PORT` | `7420` | Admin-UI-Port |
| `--host HOST` | `127.0.0.1` | Bind-Adresse; non-loopback erzwingt Token |
| `--admin-token TOKEN` | — | Auth-Token für Remote-Zugriff (Pflicht bei non-loopback) |
| `--allowed-hosts HOST…` | `127.0.0.1 localhost ::1` | zusätzliche erlaubte Origin-Hosts (erweitert, ersetzt nicht) |
| `--root PATH` | `.` | Projekt-Root |
| `--watch` | aus | Filesystem-Watcher (pollt Config-Dateien alle 2s) |
| `--no-viz` | aus | Viz-Dashboard + MCP-Server nicht mitstarten |

## Port-Matrix

| Dienst | Default-Port |
|--------|--------------|
| Admin UI | `7420` |
| Viz-Dashboard | `8765` |
| MCP-SSE-Server | `9090` |

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
  Remote-/Container-Zugriff braucht `--host 0.0.0.0` (+ Token).
- **HTTP 401** → Token fehlt oder ungültig (`Authorization: Bearer <T>` bzw.
  `?token=<T>` setzen).
- **Port-Kollision** → Port ist belegt; der detached Start schlägt fehl
  (crash-loop, siehe `admin-server.log`). Freien Port via `--port` wählen.
