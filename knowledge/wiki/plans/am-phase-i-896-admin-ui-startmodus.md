---
type: Plan
title: "Phase-I #896 — Admin-UI Startmodus local/network"
source: "GitHub Issue #896; APPROVED-Konzept docs/specs/2026-11-20-phase-i-896-concept.md"
spec: "docs/specs/2026-11-20-phase-i-896-concept.md"
spec-id: "CONCEPT-PHASE-I-896-2026-11-20"
status: "geplant"
branch: "feat/wave7-phase-i-bundle"
created: "2026-11-21"
tags: [plan, admin-ui, phase-i, issue-896]
---

# Admin-UI Startmodus `local`/`network` (#896) Implementation Plan

> Status: geplant
> Bundle: W7 Phase-I-Bundle, Plan 1 von 2. Die Umsetzung erfolgt gemeinsam mit #681 in **einem** PR (vom Nutzer freigegebene Abweichung von Roadmap §3.9 „je Issue eigener Plan + PR" — im PR-Body zu vermerken). Die **Pläne bleiben getrennt**, die Ownership ist disjunkt.
> Keine neuen Decisions: ausschließlich APPROVED-Konzept + Roadmap-Entscheidung 31 (N12).

**Goal:** Der Admin-UI-Start-Skill (im Repo: `/admin`-Command, `commands/1-generic/admin.md`) bietet einen expliziten Modus `local` (Default, `127.0.0.1`, kein Token) und `network` (`0.0.0.0`, erzwungenes Zufalls-Token, **nicht persistiert**, nur ausgegeben, optionale `--allowed-hosts`, Ausgabe der erreichbaren URL inkl. Token). Die Skill-Doku enthält Port-Matrix, Firewall-Hinweise, Sicherheitswarnung und das gemäß Entscheidung 31 geklärte Bindeverhalten von 8765/9090.
**Architecture:** Modus-, Token- und Banner-Logik bleibt vollständig in `scripts/admin-server.py` (Modul-Helfer + `AdminServer` + `main()`); keine neue Komponente, keine externe Abhängigkeit, stdlib-only. Doku-Quellen sind `commands/1-generic/admin.md`, `rules/2-platform/agent-meta-admin-ui.md`, `docs/howto/admin-ui-remote-access.md`, `docs/api/admin-ui-reference.md`; generierte Artefakte ausschließlich via `scripts/sync.py`.
**Tech Stack:** Python 3 stdlib (`argparse`, `secrets`, `hmac`, `socket`), pytest/unittest, Markdown, Vanilla-JS (nur Verifikation).
**Spec:** `docs/specs/2026-11-20-phase-i-896-concept.md` (spec-id: `CONCEPT-PHASE-I-896-2026-11-20`, status: APPROVED, Nutzergo 20.11. / E-31)

## Global Constraints

- Token im network-Modus: `secrets.token_urlsafe(32)`, **keine Persistenz**, keine Token-Datei, kein Config-Write, kein Env-Write durch den Helfer. Der DRAFT-Plan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md` sieht in Q4 eine Token-Datei (`.meta-viz/admin-token`, 0600) vor — das ist durch das APPROVED-Konzept („nicht persistiert, nur ausgegeben") **überstimmt**; der DRAFT dient nur als Code-Kontext, nicht als Entscheidungsquelle.
- `local` bleibt verhaltensidentisch (Loopback, kein Token) — bestehende `TestBindHostEnforcement`-Tests bleiben unverändert grün.
- Fail-closed greift weiter: `--host <non-loopback>` ohne Token bricht ab; das network-Modus-Token wird vor dieser Prüfung erzeugt.
- Kein Wildcard-Origin, kein Abschalten der Origin-/Host-Prüfung, keine neuen Platzhalter, keine Provider-Literale.
- `#456` nur referenzieren, **keine Closing-Keywords** (`Closes`/`Fixes`/`Resolves`) in Commit- oder PR-Texten; kein Issue-/PR-Status-Wechsel.
- Keine Rebaseline (reine Doku + eine Code-Datei, keine Template-/Rule-Änderung im Sinne von Golden-Fixtures); `sync.py --validate` muss grün bleiben.
- Plan/Artefakte deutsch; die geänderten Admin-Doku-Dateien bleiben gemäß Sprachmatrix in ihrer bestehenden Sprache (Englisch).
- **Verbotene Bundle-1-Pfade nicht berühren:** `agents/1-generic/*.md`, `.meta-config/*`, `config/role-defaults.yaml`, `hooks/1-generic/lib/kernel/*`, `snippets/agents/closing-summary.md`, `standalone/**`, `tests/fixtures/**` sowie die Bundle-1-Testdateien. Ownership dieses Plans: `scripts/admin-server.py`, `docs/ui/admin-ui.html` (nur Verifikation), Admin-Doku, neuer Test `tests/test_admin_start_mode_896.py`.

## File Structure

- Modify: `scripts/admin-server.py` — `--mode`, Bind-Auflösung, Zufalls-Token, Token-Transport, Start-Banner (Z. 88, 561, 1143, 6340, 6432, 6486/6533, 6654).
- Create: `tests/test_admin_start_mode_896.py` — TDD-Tests `TestResolveBindMode`, `TestNetworkToken`, `TestDetachedTokenTransport`, `TestNetworkBanner`, `TestAdminModeDocs`. Neuer Dateiname verhindert Overlap mit Bundle-1-Tests.
- Modify: `commands/1-generic/admin.md` — `/admin start --mode local|network`, Argument-Hint.
- Modify: `rules/2-platform/agent-meta-admin-ui.md` — Quelle für generiertes `admin-ui`-Skill: Modi, Port-Matrix, Firewall, Sicherheitswarnung, 8765/9090.
- Modify: `docs/howto/admin-ui-remote-access.md` — Quick-start network, Token nur in Startausgabe, Firewall, Bindeverhalten 8765/9090.
- Modify: `docs/api/admin-ui-reference.md` — Modus-/Port-Tabelle konsistent zur Rule.
- Verify (keine Änderung erwartet): `docs/ui/admin-ui.html` — `?token=`-Ingest (Z. 874–882) und Bearer-Wrapper (ab Z. 953) müssen die ausgegebene Deep-Link-URL akzeptieren; Ownership nur gegen Bundle-1-Overlap beansprucht.
- via `python scripts/sync.py` (nicht von Hand): `.claude/commands/admin.md`, `.claude/skills/admin-ui/SKILL.md`.
---
pipeline_stages:
  implement: 1   # Task 1 ist der Einstieg in die Implementierung; jeder Task ist eine TDD-Einheit
---

### Task 896-1: `--mode local|network` und Bind-Auflösung

**Agent:** `developer` · **Depends on:** —
**Files:** Modify `scripts/admin-server.py` (`main()` ~Z. 6654, neuer Helfer); Test `tests/test_admin_start_mode_896.py::TestResolveBindMode` (Create)
**Interfaces:**
- Produces: CLI `--mode {local,network}` (Default `None`) in `main()`; `--host`/`--port`/`--allowed-hosts` bleiben unverändert.
- Produces: `def _resolve_bind_mode(*, mode: str | None, cli_host: str | None, cfg_bind_host: str) -> str` — `local` → `"127.0.0.1"`; `ValueError`, falls `cli_host` gesetzt und nicht in `LOOPBACK_HOSTS`; `network` → `cli_host` falls nicht-loopback, sonst `cfg_bind_host` falls nicht-loopback, sonst `"0.0.0.0"`; `None` → `cli_host or cfg_bind_host`.
- Consumes: `_load_admin_ui_config(root)["bind_host"]` (`scripts/admin-server.py:561`), `LOOPBACK_HOSTS` (bestehende Konstante).

- [ ] Step 1: Test schreiben (fail): `("local", None, "10.0.0.2")` → `"127.0.0.1"`; `("network", None, "127.0.0.1")` → `"0.0.0.0"`; `("network", "10.0.0.2", "127.0.0.1")` → `"10.0.0.2"`; `(None, None, "10.0.0.2")` → `"10.0.0.2"`; `("local", "0.0.0.0", "127.0.0.1")` → `ValueError`.
- [ ] Step 2: Helfer + argparse-Flag implementieren; `main()` nutzt den Helfer für den Bind.
- [ ] Step 3: `rtk pytest tests/test_admin_start_mode_896.py -k ResolveBindMode -q` grün; `rtk grep "add_argument.*--mode" scripts/admin-server.py` liefert genau einen Treffer.
- [ ] Step 4: Commit `feat(admin): add explicit local/network start mode`

**Acceptance criteria (messbar):** Fünf Testfälle grün; `--mode` genau einmal in `main()` registriert; `python scripts/admin-server.py --mode local` bindet `127.0.0.1`.

### Task 896-2: Zufalls-Token im network-Modus (nicht persistiert)

**Agent:** `developer` · **Depends on:** 896-1
**Files:** Modify `scripts/admin-server.py` (Token-Erzeugung vor Fail-closed); Test `tests/test_admin_start_mode_896.py::TestNetworkToken`
**Interfaces:**
- Produces: `def _ensure_network_token(resolved: str | None) -> tuple[str, bool]` — `(resolved, False)` bei bereits aufgelöstem Token, sonst `(secrets.token_urlsafe(32), True)`. Schreibt **keine** Datei, keine Config, kein `os.environ`.
- Produces: Aufruf ausschließlich bei `mode == "network"`, vor der Fail-closed-Prüfung in `AdminServer.__init__` (~Z. 6364); bei `local` kein Aufruf.
- Consumes: `_resolve_admin_token(...)` (`scripts/admin-server.py:1143`), `mode` aus 896-1.
- Error path: kein `ADMIN_TOKEN_FILE`, keine 0600-Datei, keine Rotation über Datei (APPROVED-Konzept).

- [ ] Step 1: Test schreiben (fail): `resolved="x"` → `("x", False)`, keine Datei; `resolved=None` → Länge ≥ 32, URL-safe, `generated=True`, zwei Aufrufe liefern verschiedene Tokens, `tmp_path` bleibt leer; `local`-Pfadruft den Helfer nicht (Mock-Zähler 0).
- [ ] Step 2: `import secrets` ergänzen und Helfer + Aufrufbedingung implementieren.
- [ ] Step 3: `rtk pytest tests/test_admin_start_mode_896.py -k NetworkToken -q` grün.
- [ ] Step 4: Commit `feat(admin): generate ephemeral network token without persistence`

**Acceptance criteria (messbar):** Kein Datei-/Config-/Env-Write durch den Helfer; `network` erzeugt Token, `local` nicht; Token-Länge ≥ 32 und url-safe.

### Task 896-3: Token nie über argv oder Log

**Agent:** `senior-developer` · **Depends on:** 896-2
**Files:** Modify `scripts/admin-server.py` (`_admin_start_detached`, Z. 6486/6533); Test `tests/test_admin_start_mode_896.py::TestDetachedTokenTransport`
**Interfaces:**
- Modifies: `_admin_start_detached(args)` — ersetzt `cmd += ["--admin-token", args.admin_token]` (Z. 6533) durch `env={**os.environ, "ADMIN_UI_TOKEN": token}` an `subprocess.Popen`.
- Consumes: 896-2 Token; bestehender `ADMIN_UI_TOKEN`-Pfad in `_resolve_admin_token`.
- Error path: Token-Wert nicht in `cmd`, nicht in `args`, nicht in `.meta-viz/admin-server.log`.

- [ ] Step 1: Test schreiben (fail): `subprocess.Popen` gemockt → `"--admin-token"` nicht in `cmd`, `env["ADMIN_UI_TOKEN"] == token`; Logdatei nach Start enthält die Token-Zeichenkette nicht.
- [ ] Step 2: Implementieren.
- [ ] Step 3: `rtk pytest tests/test_admin_start_mode_896.py -k DetachedTokenTransport -q` grün; `tests/test_admin_server.py` unverändert grün.
- [ ] Step 4: Commit `fix(admin): pass network token via env, never argv or log`

**Acceptance criteria (messbar):** Gemockter `cmd` enthält keinen Token-Parameter; `env` enthält `ADMIN_UI_TOKEN`; Logfile enthält den Token-String nicht.

### Task 896-4: Erreichbare URLs, Firewall-Hinweis, Sicherheitswarnung

**Agent:** `developer` · **Depends on:** 896-2
**Files:** Modify `scripts/admin-server.py` (`AdminServer.start` Z. 6432, `_admin_start_detached`, neue Helfer); Test `tests/test_admin_start_mode_896.py::TestNetworkBanner`
**Interfaces:**
- Produces: `def _reachable_urls(bind_host: str, port: int, local_ips: tuple[str, ...]) -> list[str]` — Wildcard-Bind → eine URL je `local_ips` plus `http://127.0.0.1:<port>/`; konkrete Adresse → genau diese; im network-Modus je URL `?token=<T>`.
- Produces: `def _network_banner(urls: list[str], token: str, port: int) -> list[str]` — Zeilen: erreichbare URLs, `Token: <token>`, `Allow inbound TCP <port> only from trusted networks (host firewall / security group).`, Sicherheitswarnung (netzweiter Zugriff, Token wie Passwort, TLS/Reverse-Proxy empfohlen), SSH-Tunnel-Alternative.
- Modifies: `AdminServer.start()` druckt das Banner **ohne** Token (Child-stdout → Logdatei); `_admin_start_detached` (Parent) druckt es **mit** Token. Bestehende `http://0.0.0.0:…`-Ausgaben werden ersetzt.
- Consumes: 896-2 Token; `DEFAULT_PORT = 7420` (Z. 88).

- [ ] Step 1: Test schreiben (fail): `_reachable_urls("0.0.0.0", 7420, ("192.168.1.5",))` enthält `http://192.168.1.5:7420/?token=T`, kein `0.0.0.0`; `_network_banner(...)` enthält Firewall-Zeile, Sicherheitswarnung und `Token: T`; gemocktes `AdminServer.start` schreibt `T` nicht nach stdout.
- [ ] Step 2: Implementieren (IP-Ermittlung best-effort via stdlib, Fallback `127.0.0.1`).
- [ ] Step 3: `rtk pytest tests/test_admin_start_mode_896.py -k NetworkBanner -q` grün.
- [ ] Step 4: Commit `feat(admin): print reachable URLs, firewall and security guidance`

**Acceptance criteria (messbar):** Keine `0.0.0.0`-URL in der Ausgabe; jede URL trägt `?token=`; Firewall- und Sicherheitszeile vorhanden; Token nie im Server-stdout.

### Task 896-5: Skill-/Command-Doku, Port-Matrix, 8765/9090 gemäß Entscheidung 31

**Agent:** `documenter` · **Depends on:** 896-1, 896-2, 896-3, 896-4
**Files:** Modify `commands/1-generic/admin.md`, `rules/2-platform/agent-meta-admin-ui.md`, `docs/howto/admin-ui-remote-access.md`, `docs/api/admin-ui-reference.md`; Test `tests/test_admin_start_mode_896.py::TestAdminModeDocs`; generierte Artefakte via `python scripts/sync.py`
**Interfaces:**
- Produces: `argument-hint: "[start | stop | status | restart] [--mode local|network] [--allowed-hosts HOST...] [--no-viz] [--port <port>]"` und Bullets für beide Modi in `commands/1-generic/admin.md`.
- Produces: Port-Matrix 7420/8765/9090 in Rule, Howto und Reference; Firewall-Hinweis; Sicherheitswarnung network; Quick-start network (Token nur Startausgabe, **kein** Persistenzweg, Rotation = Neustart).
- Produces: Abschnitt „Bindeverhalten 8765/9090 bei `--host 0.0.0.0`" mit (a) code-verifiziertem Ist-Stand (`scripts/viz-report.py:912` bindet hart `127.0.0.1`; `scripts/viz-logger.py --http` ohne Host-Option) und (b) der verbindlichen Roadmap-Entscheidung 31 (beide netzweit konfigurierbar, je eigene Option, sicherer Default). Abweichung Ist vs. Soll als offene Umsetzungslücke markieren — **keine** neue Option erfinden, keine `scripts/viz-*.py` anfassen (außerhalb Ownership).
- Consumes: 896-1..4; Konzept §2/§3/§5; DRAFT-Plan nur als Code-Kontext.

- [ ] Step 1: Test schreiben (fail): `test_admin_docs_cover_start_modes` prüft, dass `commands/1-generic/admin.md` `--mode` enthält und Rule + Howto `7420`, `8765`, `9090`, Firewall, Sicherheitswarnung und `Entscheidung 31` enthalten.
- [ ] Step 2: Doku ändern; `python scripts/sync.py` generiert `.claude/commands/admin.md` + `.claude/skills/admin-ui/SKILL.md` neu (nicht von Hand editieren).
- [ ] Step 3: `rtk pytest tests/test_admin_start_mode_896.py -k AdminModeDocs -q` und `rtk exec python3 scripts/sync.py --validate` grün; `rtk grep -rnE "Closes|Fixes|Resolves" <geänderte Dateien>` leer.
- [ ] Step 4: Commit `docs(admin): document local/network modes, port matrix and security`

**Acceptance criteria (messbar):** Alle fünf Doku-Tokens (`--mode`, `7420`, `8765`, `9090`, `Entscheidung 31`) in den drei Zieldateien nachweisbar; `sync.py --validate` grün; keine Closing-Keywords.

## Self-Review

| Check | Ergebnis |
|---|---|
| AK-896-1 (explizite Modus-Wahl, local = Default) | ✔ Task 896-1 (`--mode`, Default `None` → config/CLI-Verhalten, `local` → Loopback) |
| AK-896-2 (network erzwingt Token, URL inkl. Token) | ✔ Task 896-2 (Zufalls-Token) + 896-4 (`_network_banner`, `?token=`) |
| AK-896-3 (Port-Matrix, Firewall, Sicherheitswarnung) | ✔ Task 896-4 (Laufzeit-Banner) + 896-5 (Doku) |
| AK-896-4 (8765/9090 gemäß Entscheidung 31 geklärt) | ✔ Task 896-5 (Ist-Stand code-verifiziert + Entscheidung 31 dokumentiert) |
| Keine neuen Entscheidungen | ✔ Token-Nicht-Persistenz aus Konzept; DRAFT-Q4 explizit überstimmt; 8765/9090-Soll aus Entscheidung 31 |
| Jeder Task genau eine Rolle | ✔ developer / developer / senior-developer / developer / documenter |
| Jeder Task hat Test + Commit + messbare AK | ✔ 5 Tasks, je 4 TDD-Schritte |
| `pipeline_stages` vorhanden | ✔ `implement: 1` |
| Ownership disjunkt zu #681 | ✔ #681 berührt keine dieser Dateien |
| Bundle-1-Dateien unberührt | ✔ keine forbidden Pfade in `Files:` |
| Keine Placeholder | ✔ alle Pfade, Symbole, Signaturen, Commit-Messages benannt |
