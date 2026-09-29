# Spike — F-RULESLOC: Trägt `.gemini/rules` den Gemini/Antigravity-Tier? (Kanal (a) vs. Fallback (c))

| | |
|---|---|
| **Spec / Plan** | `SPEC-CONTEXT-FILE-MODES-2026-09-13` · Plan `docs/plans/2026-09-13-context-file-modes.md` → Task 4 „F-RULESLOC-Verifikation (Gate für Kanal (a))" |
| **Status** | Verdict gesetzt — **Evidenz-/Doku-basiert**, kein Live-Real-Repo-Lauf (Protokoll: `tests/manual/f-rulesloc-gemini-rules-channel.md`) |
| **Datum** | 2026-09-14 |
| **Rolle** | explorer (Task 4) |
| **Verdict** | **channel (a) `.gemini/rules` CONTRADICTED as an Antigravity workspace-rules location** |
| **Kanalentscheidung** | **Fallback (c)** — geteilte `AGENTS.md` + native Hook-Erzwingung (Prompt-Text = Dokumentation) |
| **Bindung** | Verdict gilt für Task 5 (AC-13/AC-14) und Task 8; OQ-3/R8 |

---

## 1. Frage

`per-provider` soll Gemini/Antigravity (**ein** Provider) seinen Gate-Tier über einen
provider-nativen Kanal tragen lassen. Der Plan favorisiert **Kanal (a):** den bereits
existierenden `rules_dir`-Kanal `.gemini/rules` (Always-On-Regel) — gated auf FINDING
F-RULESLOC. Der Kanal ist nur dann tragfähig, wenn die **Antigravity-Runtime** den Ordner
`.gemini/rules` tatsächlich als Workspace-Rules liest.

**Leitfrage:** Liest Antigravity `.gemini/rules` als Workspace-Rules-Lokation? Falls nein,
ist Kanal (a) zur Laufzeit ein No-op und der Gate-Text läge in einer nicht geladenen Datei
→ **Fallback (c)**.

## 2. Repo-Evidenz

Erhoben im Repo (Arbeitsbaum `feat/spec-plan-workflow`, 2026-09-14):

| Punkt | Beleg | Befund |
|---|---|---|
| Gemini-Provider-Block | `config/ai-providers.yaml:98` ff. | — |
| Kontext-Datei | `config/ai-providers.yaml:101` (`context_file: AGENTS.md`) | geteilter Kern, kein dedizierter Gemini-Kontextfile |
| Rules-Kanal | `config/ai-providers.yaml:103` (`has_rules: true`), `:104` (`rules_dir: .gemini/rules`) | weicht von der Doku-Lokation `.agents/rules` ab |
| Hook-Kanal | `config/ai-providers.yaml:105-108` (`has_hooks`, `hook_protocol: antigravity-hooks-json`, `hooks_dir: .agents/hooks`, `hooks_config_file: .agents/hooks.json`) | **entspricht** der Antigravity-Konvention (`.agents/`), obwohl der Rules-Kanal abweicht |
| Settings | `config/ai-providers.yaml:126` (`settings_file: .gemini/settings.json`) | `.gemini/settings.json` hat **keinen** `context.fileName`-Key (Kandidat (b) unberührt) |
| Generierte Rules | `.gemini/rules/` — **39 Einträge** (35 `.md`-Rules inkl. `use-orchestrator.md`, 1 `.sync-backup-*`, 3 `.agent-meta-managed*`-Marker) | Verzeichnis existiert und ist bestückt |
| Tier im Rules-Kanal | `.gemini/rules/use-orchestrator.md:1` = `# CRITICAL GATE` | Der bestehende Seam rendert den Gemini-Tier (`hook` → `GATE_ENFORCED`) **heute schon** in diesen Kanal; das Verdict betrifft ausschließlich die **Lokation**, nicht die Verdrahtung |
| Gegenprobe | `.agents/` enthält **nur** `hooks.json` + `hooks/` | `.agents/rules/` existiert **nicht** — generierte Rules und Doku-Lokation divergieren |

### 2.1 Tier-Injection-Seam

Der Tier wird über den bestehenden per-Provider-Seam in die Rules-Dateien von
`has_rules`-Providern injiziert:

- `scripts/lib/sync_pipeline.py:748` — `provider_variables.update(runtime_gate_vars(pc, caps, config))`
  (HEAD-Nummerierung; im Phase-1-Arbeitsbaum `:762`).
- `scripts/lib/sync_pipeline.py:781-785` — `sync_rules(...)` konsumiert `provider_variables`
  (HEAD-Nummerierung; im Phase-1-Arbeitsbaum `:796-799`).

Konsumiert wird der Tier dann in `rules/1-generic/use-orchestrator.md:2-13`
(`{{#if GATE_ENFORCED}}` / `{{#if GATE_PARTIAL}}` / `{{#if GATE_ADVISORY}}`). Für Gemini
(`provider-capabilities.yaml:94` → `runtime_gate: hook`) rendert das den
`GATE_ENFORCED`-Zweig (`# CRITICAL GATE`). **Der Seam ist also vorhanden und würde (a)
ohne neue Keys bedienen.** Offen ist allein, ob `.gemini/rules` die von der Runtime
gelesene Lokation ist.

## 3. Offizielle Antigravity-Dokumentation

Quellen:

- <https://antigravity.google/docs/ide/rules>
- <https://antigravity.google/docs/rules-workflows>

Wörtliche Aussagen der Doku:

- **Workspace Rules:** „Workspace rules live in the `.agents/rules` folder of your workspace
  or git root."
- **Backwards compatibility:** „Antigravity now defaults to `.agents/rules`, but still
  maintains backward support for `.agent/rules`."
- **Global Rules:** „Global rules live in `~/.gemini/GEMINI.md` and are applied across all
  workspaces."
- **Aktivierung** je Regel: `Manual`, `Always On`, `Model Decision`, `Glob`.

`.gemini/rules` wird in der offiziellen Doku **nicht** als Workspace-Rules-Lokation genannt;
`.gemini/` erscheint dort nur als Teil des globalen Pfads `~/.gemini/GEMINI.md`.

## 4. Verdict

> **VERDICT: channel (a) `.gemini/rules` CONTRADICTED as an Antigravity workspace-rules location.**

Die konfigurierte `rules_dir: .gemini/rules` widerspricht der offiziell dokumentierten
Workspace-Rules-Lokation `.agents/rules` (rückwärtskompatibel `.agent/rules`). Da die
Antigravity-Doku `.gemini/rules` **nicht** als Workspace-Rules-Lokation führt, kann Kanal (a)
auf Evidenzbasis **nicht** beansprucht werden. Nach der Blocked-Regel des Plans gilt
konservativ **Fallback (c)**.

Abgrenzung zum Restrisiko: Das Verdict ist nicht „(a) ist bewiesen tot", sondern „(a) ist als
Antigravity-Workspace-Rules-Lokation **widerlegt**". Ein Live-Lauf könnte die Doku-Aussage
bestätigen oder (bei unvollständiger Doku) revidieren; bis dahin bleibt (c) die sichere Wahl.

**Konsequenz für Phase 1:** Der Gemini/Antigravity-Tier wird **nicht** über `.gemini/rules`
beansprucht. `rules_dir` bleibt unverändert (der generierte `.gemini/rules`-Output bleibt für
den Gemini-CLI-Kanal bestehen), aber `per-provider` verspricht den Tier nicht über diesen Kanal.

## 5. Empfehlung — Fallback (c)

- **Träger:** geteilte `AGENTS.md` (kanonischer Kern) + native Hook-Erzwingung.
- **Belege:** `hook_protocol: antigravity-hooks-json` (`config/ai-providers.yaml:106`),
  `runtime_gate: hook` (`config/provider-capabilities.yaml:94`).
- **Prompt-Text = Dokumentation:** die Regel benennt die Direktive, die Erzwingung bleibt nativ
  im Hook.
- **Kein Config-Bruch, kein Rollback nötig:** die Kanalentscheidung ist datengetrieben; es werden
  keine neuen Kontext-Keys vorausgesetzt.
- **Promotion-Pfad:** bestätigt ein späterer Real-Repo-Lauf (a), kann der Kanal ohne neue Keys
  beansprucht werden — der Seam injiziert den Tier bereits (§2.1).

## 6. Was das Verdict bestätigen/widerlegen würde

Reproduzierbares Real-Repo-Protokoll: `tests/manual/f-rulesloc-gemini-rules-channel.md`.

Kern: je eine Always-On-Probe-Regel mit unverwechselbarem Marker in `.gemini/rules/` **und**
`.agents/rules/` ablegen, eine echte Antigravity-Session starten und beobachten, welcher
Marker geladen wird. Auswertung:

| Beobachtung | Interpretation |
|---|---|
| nur `.agents/rules`-Marker | Contradiction **bestätigt** → Fallback (c) bleibt |
| nur `.gemini/rules`-Marker | Contradiction **widerlegt** → Kanal (a) nutzbar, Verdict auf PASS heben |
| beide Marker | beide Kanäle lesbar → (a) technisch nutzbar, `.agents/rules` bleibt Doku-Ziel |
| keiner | Aktivierungs-Metadaten/Format falsch → über die Antigravity-UI neu anlegen und wiederholen |

## 7. Minor line-number drift (dokumentiert)

- Spec/Plan zitieren `config/ai-providers.yaml:95` (`rules_dir`) und `:97-99`
  (`hook_protocol`/`hooks_dir`/`hooks_config_file`). **Aktuell:** `:104` und `:106-108`
  (Gemini-Block beginnt `:98`). Keine semantische Änderung, nur Zeilendrift.
- Spec zitiert `sync_pipeline.py:373-375` / `:747-748` / `:782`; **aktuelle HEAD-Nummern
  stimmen**, im Phase-1-Arbeitsbaum verschoben auf `:389` / `:762` / `:796-799`.

## 8. Referenzen

- Plan: `docs/plans/2026-09-13-context-file-modes.md` → Task 4.
- Spec: `docs/specs/2026-09-13-context-file-modes-design.md` → FINDING F-RULESLOC.
- System-Design: `docs/specs/2026-09-13-context-file-modes-system-design.md` → §F-RULESLOC.
- Real-Repo-Protokoll: `tests/manual/f-rulesloc-gemini-rules-channel.md`.
