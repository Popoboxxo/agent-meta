# Spike-Ergebnis — Orchestrator-Topologie P0-Probes (Issue #1077)

- **Datum:** 2026-11-04
- **Branch/HEAD bei Erstellung:** `feat/orchestrator-topology-v1` @ `6f8c9a9b`
- **Issue:** #1077 (P0-Gate, OQ-1 = B)
- **Spec:** `docs/specs/2026-11-04-orchestrator-topology-spec.md` (P0-Gate)
- **Design:** `docs/specs/2026-11-03-orchestrator-topology-design.md` §16 Nr. 2–6, §7 (Upgrade-Prozedur), §3.1
- **Plan:** `docs/plans/2026-11-04-orchestrator-topology-v1-plan.md` Task 3
- **Harness:** `scripts/topology-probe.py` (read-only, je Provider ein Lauf, Timeout 20 s)
- **Rohdaten:** `.tmp/topology-probe.json` (gitignored, nicht committet — die Zitate unten sind die Transkription)
- **Kurzstand:** Fünf Probes ausgeführt. **0 `evidence` / 2 `not run` / 3 `inconclusive`.** Keine Matrix-Zelle erfüllt die drei Gate-Bedingungen → **N = 0, keine Zell-Upgrades**, `config/provider-capabilities.yaml` bleibt unverändert (25 datenabgeleitet / 15 `UNVERIFIED ⇒ no`).

## Ausführungslage

| Provider | CLI-Pfad | Version | Probe |
|---|---|---|---|
| Opencode | `/usr/local/bin/opencode` | `1.19.5` | P0-1 |
| Claude | `/usr/local/bin/claude` | `2.1.318 (Claude Code)` | P0-2 |
| Codex | `/home/hermes/.npm-global/bin/codex` | `codex-cli 0.163.0` | P0-3 |
| Mammouth | — (nicht auf `PATH`) | — | P0-4 |
| KimiCode | — (nicht auf `PATH`) | — | P0-5 |

Alle Läufe erfolgten am 2026-11-04 auf demselben Host, nicht-interaktiv, ohne Netzwerkzugriff außer dem, den das jeweilige CLI-Kommando selbst auslöst. Der Harness startet ausschließlich `--version` / `--help` / `agent list`; er öffnet keine Session und schreibt nur die `--out`-Datei.

## Marker und Zählweise

- **`evidence`** — die Frage ist durch die aufgezeichnete, nicht-interaktive Ausgabe beantwortet (explizites Evidenzmuster im Output).
- **`inconclusive`** — das CLI lief, aber die Frage ist durch dieses Kommando nicht entscheidbar; der Grund steht im Verdikt.
- **`not run — CLI unavailable`** — das Binary fehlt auf `PATH`; das ist ein **gültiges** Ergebnis (Spec P0-Gate, R11) und lässt die Zelle `no`.
- Je Provider genau eine Probe. Ein `inconclusive`/`not run` ist **kein** Zell-Upgrade; die Zelle bleibt `no` und degradiert mit genau einer WARNING pro Provider und Lauf (AC-16).

## Probe-Protokoll (alle ausgeführten Kommandos)

| # | Kommando | Exit | Zweck |
|---|---|---|---|
| 1 | `python3 scripts/topology-probe.py --list` | 0 | fünf Records bestätigt (P0-1…P0-5) |
| 2 | `python3 scripts/topology-probe.py --out .tmp/topology-probe.json` | 0 | realer Lauf aller fünf Probes |
| 3 | `opencode --version` | 0 | Provider-Version P0-1 |
| 4 | `/usr/local/bin/opencode agent list` | 0 | P0-1 |
| 5 | `/usr/local/bin/claude --version` | 0 | Provider-Version P0-2 |
| 6 | `/usr/local/bin/claude --help` | 0 | P0-2 |
| 7 | `/home/hermes/.npm-global/bin/codex --version` | 0 | Provider-Version P0-3 |
| 8 | `/home/hermes/.npm-global/bin/codex --help` | 0 | P0-3 |
| 9 | `command -v mammouth` | 1 | P0-4 (nicht gefunden) |
| 10 | `command -v kimi` | 1 | P0-5 (nicht gefunden) |

## P0-1

**Frage (Design §16 Nr. 2):** Ist eine `mode: primary`-Rolle zusätzlich per `task(subagent_type: "orchestrator")` aufrufbar?

- **Befehl:** `/usr/local/bin/opencode agent list`
- **Datum:** 2026-11-04T18:46:50Z
- **Provider-Version:** `1.19.5`
- **Beobachtetes Ergebnis:** Exit 0. Die Ausgabe listet 65 Agenten-Zeilen, darunter `orchestrator (primary)` und `build (primary)`. Das belegt die **Registrierung** der Rolle als `primary` — nicht, ob diese Rolle zusätzlich per `task` spawnbar ist. Der Harness protokolliert dazu: `task(subagent_type) spawnability cannot be observed by a non-interactive agent listing; CLI output: build (primary)`.
- **Verdikt:** `inconclusive` — Grund: Spawnbarkeit per `task(subagent_type)` ist durch ein nicht-interaktives Agent-Listing nicht beobachtbar; die Frage braucht eine interaktive Session mit einem echten `task`-Aufruf.

## P0-2

**Frage (Design §16 Nr. 3):** Ist `claude --agent orchestrator` wirklich ein „Primary" im Sinne der Definition (gleicher Kontext wie der Main Chat, gleiche Hook-Payload-Semantik, Prompt-Caching)?

- **Befehl:** `/usr/local/bin/claude --help`
- **Datum:** 2026-11-04T18:46:50Z
- **Provider-Version:** `2.1.318 (Claude Code)`
- **Beobachtetes Ergebnis:** Exit 0. Die Hilfe enthält wörtlich:

  ```
    --agent <agent>                       Agent for the current session. Overrides
                                          the 'agent' setting.
  ```

  Das belegt die **Existenz und Semantik des Flags** (Session-Agent-Wahl überschreibt die `agent`-Einstellung). Es belegt **nicht** die Kontext-Identität zum Main Chat, die Hook-Payload-Semantik oder das Prompt-Caching. Harness-`observed`: `context identity and hook-payload semantics cannot be observed by a non-interactive command; CLI output: Usage: claude [options] [command] [prompt]`.
- **Verdikt:** `inconclusive` — Grund: Kontext-Identität und Hook-Payload-Semantik sind durch ein nicht-interaktives `--help` nicht beobachtbar; die Frage braucht eine gestartete Session mit Hook-Mitschnitt.

## P0-3

**Frage (Design §16 Nr. 4):** Ist `main_agent_selectable` wahr, und welcher Mechanismus wählt den Main-Agenten?

- **Befehl:** `/home/hermes/.npm-global/bin/codex --help`
- **Datum:** 2026-11-04T18:46:54Z
- **Provider-Version:** `codex-cli 0.163.0`
- **Beobachtetes Ergebnis:** Exit 0. Erste Zeile `Codex CLI`; die Hilfe nennt u. a. das Subkommando `agents  Browse all agent sessions on the shared local app-server daemon`. Ein `--agent`-/`default_agent`-/`main_agent`-Flag erscheint in `--help` **nicht**. Harness-`observed`: `the main-agent selection mechanism is not observable from a non-interactive help/version run; CLI output: Codex CLI`.
- **Verdikt:** `inconclusive` — Grund: Aus `--help` allein ist weder `main_agent_selectable` noch der Auswahlmechanismus (Config-Feld vs. Subkommando) ableitbar; dafür ist ein Lauf gegen die Codex-Config/den App-Server nötig.

## P0-4

**Frage (Design §16 Nr. 5):** Unterstützt Mammouth `mode: primary` / `default_agent` für einen Orchestrator-Einstiegspunkt?

- **Befehl:** `mammouth agent list` (geplant; nicht gestartet)
- **Datum:** 2026-11-04T18:46:54Z
- **Provider-Version:** — (keine; Binary fehlt)
- **Beobachtetes Ergebnis:** `mammouth not found on PATH` (`command -v mammouth` → rc 1).
- **Verdikt:** `not run — CLI unavailable` — Grund: Mammouth ist auf diesem Host nicht installiert; das ist ein gültiges Ergebnis und lässt die Zelle `no`.

## P0-5

**Frage (Design §16 Nr. 6):** Welcher Mechanismus wählt den Main-Agenten — ein CLI-Flag oder ein Config-Feld?

- **Befehl:** `kimi --help` (geplant; nicht gestartet)
- **Datum:** 2026-11-04T18:46:54Z
- **Provider-Version:** — (keine; Binary fehlt)
- **Beobachtetes Ergebnis:** `kimi not found on PATH` (`command -v kimi` → rc 1).
- **Verdikt:** `not run — CLI unavailable` — Grund: KimiCode ist auf diesem Host nicht installiert. P0-5 ist die einzige Probe mit einem expliziten Evidenzmuster im Harness (`--agent` in `--help`); ohne Binary kann sie es nicht einlösen.

## Ergebnis-Tabelle

| Probe | Provider | Ergebnis | Zelle(n), die die Probe stützen könnte |
|---|---|---|---|
| P0-1 | Opencode | `inconclusive` | Opencode `hybrid` (heute `false`/`UNVERIFIED`) |
| P0-2 | Claude | `inconclusive` | Claude `primary` (heute `true`/`DOCUMENTED`, State-Upgrade) |
| P0-3 | Codex | `inconclusive` | Codex `primary` (heute `false`/`UNVERIFIED`) |
| P0-4 | Mammouth | `not run — CLI unavailable` | Mammouth `primary` (heute `false`/`UNVERIFIED`) |
| P0-5 | KimiCode | `not run — CLI unavailable` | KimiCode `primary` (heute `true`/`DOCUMENTED`, State-Upgrade) |

**Bilanz: 0 `evidence` · 3 `inconclusive` · 2 `not run`.**

## Konsequenz für die Matrix

**Keine Zelle wird hochgestuft.** Ein Zell-Upgrade verlangt laut Design §7 / Spec-P0-Gate **alle drei** Bedingungen gemeinsam:

1. **Evidenz aufgezeichnet** — die zugehörige Probe steht mit Befehl, Datum, Provider-Version und beobachtetem Ergebnis in diesem Dokument,
2. **State-Wechsel** — `topology_verified_state.<achse>` steht danach auf `DOCUMENTED` oder `VERIFIED-RUNTIME`,
3. **Invariante grün** — die §3.1-Zeile hat keine offenen `unverified`-Felder mehr (Ausnahme nur `prompt-caching`/`progress`) **und** der Invariantentest deckt die Änderung ab.

Für alle fünf Probes scheitert bereits **Bedingung 1**: `inconclusive` und `not run` sind ausdrücklich **keine** Evidenz. Damit ist `N = 0`, die Zählung bleibt **25 datenabgeleitet / 15 `UNVERIFIED ⇒ no`** (40 Zellen), und `config/provider-capabilities.yaml` wurde in diesem Task **nicht** angefasst — kein `topology_support`-, `topology_verified_state`- oder `topology_degrade`-Wert ändert sich. Die konservative Degradierung (genau eine WARNING pro Provider und Lauf) bleibt für alle offenen Zellen bestehen.

Nicht von den fünf Probes adressiert und daher unverändert: alle übrigen `hybrid`-Zellen (Claude, Codex, Mammouth, KimiCode, Gemini, Continue, Copilot, ZCode, custom), alle `subagent`-Zellen und alle `multiple`-Zellen.

## Was ein Upgrade bräuchte

Je noch offener Zelle der konkrete nächste Schritt (Bedingung 1 → 2 → 3):

| Zelle | Stand vor P0 | Bedingung 1 — fehlende Evidenz | Bedingung 2 — State | Bedingung 3 — §3.1 / Invariante |
|---|---|---|---|---|
| **Opencode `hybrid`** | `false` / `UNVERIFIED` | Interaktive Session: eine `mode: primary`-Rolle (z. B. `orchestrator`) per `task(subagent_type: "orchestrator")` aufrufen und Ausgabe/Fehlerfall protokollieren | `hybrid` → `VERIFIED-RUNTIME` | §3.1 Opencode: `Resume/Checkpoint` ist offen (nicht exempt) → muss geschlossen werden; `tests/test_topology_capability_invariant.py` pinnt `hybrid` aktuell auf `false`/`UNVERIFIED` → Assertion mitziehen |
| **Claude `primary`** | `true` / `DOCUMENTED` (State-Upgrade) | Interaktive Session: `claude --agent orchestrator` starten, Kontext-Identität, Hook-Payload und Prompt-Caching gegen den Main Chat vergleichen | `primary` → `VERIFIED-RUNTIME` | §3.1 Claude: `Resume/Checkpoint` offen (nicht exempt) → muss geschlossen werden |
| **Codex `primary`** | `false` / `UNVERIFIED` | `codex agents` bzw. interaktiver Lauf gegen die Config: ist der Main-Agent wählbar, und über welchen Mechanismus (Config-Feld vs. Subkommando)? | `primary` → `DOCUMENTED` oder `VERIFIED-RUNTIME` | §3.1 Codex: nur `prompt-caching`/`progress` offen → erfüllbar. Dann `topology_support.primary = true`, `topology_degrade.primary = null`, Mirror-Assertion + AC-16-Snapshot (26/14) nachziehen |
| **Mammouth `primary`** | `false` / `UNVERIFIED` | CLI installieren, `mammouth agent list` + Config-Key (`mode: primary` / `default_agent`) prüfen | `primary` → `DOCUMENTED` oder `VERIFIED-RUNTIME` | §3.1 Mammouth: `Resume/Checkpoint` offen (nicht exempt) → muss geschlossen werden |
| **KimiCode `primary`** | `true` / `DOCUMENTED` (State-Upgrade) | `kimi --help` bzw. interaktiver Lauf: CLI-Flag oder Config-Feld? (Der Harness sucht `--agent` in `--help`) | `primary` → `VERIFIED-RUNTIME` | §3.1 KimiCode: nur `prompt-caching`/`progress` offen → erfüllbar |

Für jede dieser Zellen gilt: Ein Upgrade ohne Evidenzzeile ist ein Testfehler (AC-16), kein Datenpunkt. Die Bilanz `25 + N` / `15 − N` bleibt bis dahin bei N = 0.

## Reproduktion

```sh
python3 scripts/topology-probe.py --list
python3 scripts/topology-probe.py --out .tmp/topology-probe.json
python3 -c "import json;[print(r['probe_id'], r['result']) for r in json.load(open('.tmp/topology-probe.json'))]"
```

Erwartung auf einem Host ohne Mammouth/KimiCode: `P0-1 inconclusive`, `P0-2 inconclusive`, `P0-3 inconclusive`, `P0-4` und `P0-5` je `not run` (fehlende Binaries). Ein anderer Host kann abweichende Ergebnisse liefern; dann ist **dieses** Dokument die Evidenzquelle und muss mit dem neuen Lauf aktualisiert werden.
