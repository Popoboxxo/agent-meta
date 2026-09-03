# Admin-UI Remote-Token Fix — Report (#514)

## STATUS

**done** — alle 3 Aufgaben umgesetzt, 583 Tests grün, committet auf Feature-Branch.

## RESULT

Remote-Zugriff auf die Admin-UI (`--host 0.0.0.0 --admin-token X`) liefert keine
`invalid or missing admin token`-Fehler mehr. Ursache: Der JS-Client in
`docs/ui/admin-ui.html` transportierte den Token nie — HTML-Load via `?token=`
gab 200, aber alle `fetch("/api/...")`-Calls liefen ohne Auth-Header → 401.

### Client-Fix (`docs/ui/admin-ui.html`, +165/−7)

- **Token-Ingest:** `?token=` beim Seitenload → `sessionStorage` → URL-Param via
  `history.replaceState` aus History/Verlauf entfernt (kein Token-Leak in Logs).
- **Zentraler `authFetch()`-Wrapper:** alle `api.get/post/put/delete/getText`
  laufen über eine einzige Funktion, die `Authorization: Bearer <token>` nur bei
  vorhandenem Token injiziert (Loopback ohne Token bleibt ohne Header).
- **401 → Login-Overlay:** dedupliziertes, Promise-basiertes Mini-Login; gültiger
  Token → `sessionStorage` → Retry desselben Requests; invalider Token → Fehlermeldung
  + neuer Versuch; Cancel → `APIError(401)`.
- **EventSource/SSE:** kann keine Header setzen → Token als `?token=`-Query-Param.
- **Help-Script:** läuft vor dem Modul → liest Token direkt aus URL/sessionStorage.

### Server-Fix (`scripts/admin-server.py`, +14/−1)

`_check_token()` galt auch für die HTML-Shell `/` — dadurch wäre das Login-Overlay
beim Erstaufruf nie erreichbar gewesen (HTML selbst 401, JS lädt gar nicht). Neu:
`_is_public_get_path()` serviert nur `/` + `/favicon.png` ohne Auth; alle `/api/*`
bleiben token-gated, Mutationen zusätzlich origin-geprüft. Die Bearer-Validierung
war bereits korrekt (`_check_token`, `Authorization: Bearer`).

### Doku (`docs/howto/admin-ui-remote-access.md`, 329 Zeilen, EN)

Lifecycle, Flags (`--port/--host/--admin-token/--allowed-hosts/--no-viz/--watch/--root`),
Port-Matrix (7420/8765/9090), Bind-Verhalten (default loopback, non-loopback erzwingt
Token), Token-Distribution + Persistenz, Troubleshooting + SSE-Log-Sicherheitshinweis.
Flags/Ports quelltext-verifiziert; im Repo-`README.md` (Documentation Index) registriert.

### Skill (`admin-ui`, intern)

- Quelle: `rules/2-platform/agent-meta-admin-ui.md` (111 Zeilen, DE) — Lifecycle,
  Flags, Port-Matrix, Host-Bindung+Token-Regeln, Diagnose-Folge, Known Issues,
  Troubleshooting.
- Registrierung: `config/rules-presets.yaml` (`lazy`-Preset, `channel: skill`) +
  `rules/1-generic/use-lazy-rules.md` (Lazy-Load-Tabelle, statische Source-Rule).
- Generiert: `.claude/skills/admin-ui/SKILL.md` (+ sync-generierte Provider-Dateien).
- **NICHT** in `config/skills-registry.yaml` (nur für externe Repo-Skills).

### Compact-Registrierung (`scripts/lib/context.py`, +8)

Die neue Rule wurde in `_COMPACT_PLATFORM_RULES` aufgenommen (`keep`: Host-Bindung+
Token-Regeln, Token-Distribution; Pointer auf `.claude/skills/admin-ui/SKILL.md`),
da sie sonst im #540-Compact-Embed ungefaltet 111 Zeilen in AGENTS.md eingebettet
hätte und die Ratio-Tests (1.6×/0.6×) gesprengt hätte. Test-Ergänzung in
`tests/test_context_compact_mode.py` (+4). **Keine Test-Schwellen verändert**
(Ziel-Retrofit widerspricht `docs/plans/issue-540-baseline.md`).

### Verifikation

| Metrik | Ergebnis |
|---|---|
| `python3 scripts/sync.py --validate` | Exit 0 |
| `pytest tests/ -q --ignore=tests/browser` (PYTEST_DISABLE_PLUGIN_AUTOLOAD=1) | **583 passed / 0 failed** |
| `tests/test_context_compact_mode.py` | 39 passed |
| Compact-Ratio | full 1084 / compact 598 Zeilen (1.81× / 0.55×) |
| curl remote `172.20.5.120:7420` (Bearer) | `/` 200 · `/api/health` 200 · ohne Header 401 |
| Live-Neustart | Server läuft: PID 165528, `--host 0.0.0.0`, Token aktiv, `--allowed-hosts 172.20.5.120` |

### Code-Review (code-reviewer)

VERDICT: APPROVED_WITH_RECOMMENDATIONS (keine Blocker). F3 (Token-Persistenz erst
nach erfolgreichem Retry) umgesetzt; F1 (SSE `?token=` in Access-Logs) in die Howto
aufgenommen; F2/F4 als vertretbar akzeptiert.

## ARTIFACTS

- **Branch:** `fix/admin-ui-remote-token` (Basis `2965e363`, unabhängig von `fix/issue-546-compact-lossless`)
- **Commit:** `ed0a301b8b69396fd188cc6a40fd246b9aabfa95` — `fix: transport admin-ui token to remote API calls`
- **Geänderte Dateien (34):**
  - `docs/ui/admin-ui.html` (+165/−7), `scripts/admin-server.py` (+14/−1)
  - `docs/howto/admin-ui-remote-access.md` (neu, 329), `README.md` (Index)
  - `rules/2-platform/agent-meta-admin-ui.md` (neu), `config/rules-presets.yaml` (+3),
    `rules/1-generic/use-lazy-rules.md` (+1)
  - `scripts/lib/context.py` (+8), `tests/test_context_compact_mode.py` (+4)
  - Generiert: `.claude/skills/admin-ui/SKILL.md`, `.gemini/rules/admin-ui.md`,
    `.mammouth/rules/admin-ui.md`, `AGENTS.md`/`CLAUDE.md`/`MAMMOUTH.md`, Provider-Agents
    (Version-Drift beta.2→beta.3 aufgelöst), `.meta-config/context-hashes.json`

## OFFEN / Notes

- **Kein automatisierter Browser-Test** ergänzt (`tests/browser/`): Token-Flow wurde
  manuell via Playwright-MCP live verifiziert (alle 4 Client-Verhalten + Retry). Ein
  Playwright-Pytest scheitert am global kaputten Plugin-Load (homeassistant/OpenSSL) —
  Aufwand > 30 Min. Wünschenswert als Follow-up.
- **Schema-Diskrepanz (pre-existing, nicht Teil dieses Fixes):** `config/project-config.schema.json`
  dokumentiert `admin-ui.bind-host`/`admin-ui.port`, aber `AdminServer` wendet nur
  `token`/`token-file`/`allowed-hosts` an — Bind-Host/Port kommen ausschließlich aus
  CLI-Flags. Im Howto als Hinweis dokumentiert; Nachverdrahtung wäre eigener Fix.
- **Token in Prozess-Args + `/tmp/opencode/admin-token.txt`** sowie SSE-`?token=` in
  Server-Access-Logs — vor Commit/Teilen ggf. rotieren; Log-Retention/Sanitization beachten.
- `docs/plans/issue-546-report.md` bleibt **ungetrackt** (VOR-Session, bewusst nicht committet).
- `rtk` CLI in dieser Umgebung nicht installiert — plain `git`/`python3` verwendet.
- Issue-Mapping: Task als „#514“ bezeichnet; AGENTS.md „Bekannte Grenzen“ referenziert
  `agent-meta #514` für ein anderes Thema (Truncation). Kein `Fixes #`-Keyword im Commit
  gesetzt — Mapping ggf. klären.
- Kein Push, kein PR, kein main-Commit (Branch bleibt lokal).
