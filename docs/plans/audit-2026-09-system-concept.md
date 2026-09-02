# Grobaudit: System-Konzept & Provider-Agnostik — 2026-09-02

## STATUS

**done** — Konzept-Audit, keine Umsetzung. Empfehlungen in §7 sind Vorschläge, keine Issues (noch nicht gefiled).

## Scope

**Geprüft:** Konzepte und Ideen des Systems, definierte Hooks, im Syncer verbaute Konzepte, das Provider-Agnostik-Credo und die reale Erweiterbarkeit um einen weiteren Provider.

**Explizit NICHT geprüft:** Agent-Template-Dateien (`agents/*`), die Systemdokumentation (`docs/*` außer als Fundstellen-Referenz), Admin-UI, Tests, Korrektheit/Security der Hooks im Detail (siehe Audit 2026-08, Waves 1–3).

**Methode:** Direkte Lektüre von `config/*.yaml`, `scripts/lib/*.py`, `scripts/sync.py`, `hooks/**`; Graphify-Graph aus `graphify-out/` (Stand `90af78e2`, 31.08. — **vor** Wave 4–10, also nicht mehr aktuell; das `graphify`-Binary ist auf dieser Maschine nicht im PATH, nur die vorgebaute Ausgabe nutzbar). **Project Atlas:** im Repo nicht vorhanden (einzige "atlas"-Treffer sind Atlassian-URLs in `docs/se-cascade/se-mcp-adapters.md`) — nicht nutzbar.

---

## 1. Gesamturteil (TL;DR)

- **Konzept-Kern ist stark:** Layer-Modell 0/1/2/3, datengetriebene Provider-Registry, Placeholder-Lifecycle mit Drift-Erkennung, Hook-Shared-Lib mit sauberer Fail-closed/Fail-open-Taxonomie, Release-Gates als Allowlist-Plugin-Architektur.
- **Provider-Agnostik ist ein Zwei-Klassen-System:** auf **Daten-Ebene** (YAML) sauber und deklarativ (6 Provider: Claude, Gemini, Opencode, Continue, Copilot, Mammouth). Auf **Code-Ebene** (Syncer) durchlöchert: **86 hardcodierte Provider-Namen in 19 Python-Dateien**, davon mehrere echte `if/elif`-Ketten und fünf "doppelte Wahrheiten" (Python-Maps, die YAML-Inhalte duplizieren).
- **Das Credo greift zu kurz:** Der `provider-agnostic`-Skill (2 Sätze) regelt nur Templates in `agents/1-generic/`. Er macht **keine** Aussage über den Syncer-Code — genau dort bricht die Agnostik. Es gibt keinen Maßstab, gegen den ein Review einen `if provider == "Gemini"` beanstanden könnte.
- **Neuen Provider einbauen:** realistisch Aufwand **M–L**, ~5 YAML- + ~7–9 Code-Touchpoints, ohne Checkliste, ohne Lint-Regel. Beleg, dass Touchpoints vergessen werden: `scripts/lifecycle_check.py:63–66` kennt **Copilot und Mammouth bis heute nicht**, obwohl beide längst in `ai-providers.yaml` stehen.
- **Erweiterbarkeits-Note: 3/5.** Datenmodell top, Code-Seite verlangt verstreutes Detailwissen ohne Guard-Rail.

---

## 2. Graphify-Befund

- 16.980 Knoten · 19.782 Kanten · 1.806 Communities · **0 Import-Zyklen** (Stand 31.08.; seit Wave 6 + #613 ist die Zyklus-Freiheit auf `scripts/lib` sogar besser als im Graph abgebildet).
- **God Nodes:** `SyncLog` (212 Kanten), `Changelog` (151/121, Doku), `AdminRequestHandler` (123), `main()` (86), `build_variables()` (63). Die letzten drei wurden in Wave 5–7 bereits entschärft (Service-Split, Dispatch-Table, Dekomposition) — der Graph zeigt den **Vorher**-Zustand. `SyncLog` als #1 ist strukturell unproblematisch (Cross-Cutting-Logging), kein Handlungsbedarf.
- **Communities** werden von Doku-/Konzeptdateien dominiert (AVD-Konzept, SE-Kaskade, Gap-Analysen, Changelog) — der Doku-Anteil am Wissensgraph ist groß; außerhalb dieses Audit-Scopes, aber ein Hinweis darauf, dass Konzept-Doku und Code-Realität im Graph nebeneinander stehen, ohne dass der Graph Drift zwischen beiden sichtbar macht.
- **Empfehlung:** `graphify update .` nach Abschluss der Refactoring-Waves, um den Graph auf den aktuellen Stand zu heben (Binary aktuell nicht installiert/im PATH).

---

## 3. Hooks — Konzept-Bewertung

**Inventar:**
- `hooks/0-external/`: `graphify-read-guard.sh`, `graphify-search-guard.sh` (Wrapper um externes Tool)
- `hooks/1-generic/`: `orchestrator-guard.sh` (v3.0.0), `dod-push-check.sh` (v2.0.0), `lifecycle-check.sh`, `sync-on-config-change.sh`, `viz-log.sh`, `pre-release-check.sh` (v3.0.0, Dispatcher)
- `hooks/1-generic/release-gates/`: `artifact-freshness.sh`, `action-pin-validation.sh`, `docker-image-scan.sh` (Plugins)
- `hooks/1-generic/lib/hook_common.sh` (Shared-Lib, seit Wave 3)

### 3.1 Stärken

| Konzept | Bewertung |
|---|---|
| **Sicherheits-Taxonomie** (Wave 3): genau 2 Hooks als "security boundary" (`orchestrator-guard`, `dod-push-check`) → **fail-closed**; alle anderen informational → **fail-open**. In jedem Header dokumentiert. | Sauber, konsistent, nachvollziehbar. Best Practice. |
| **Shared-Lib** `hook_common.sh`: JSON-Parsing, Python-Resolution, Credential-Redaction, Audit-Log-Rotation, GRAPHIFY_BIN-Validierung dedupliziert. | Gut. Beendet Copy-Paste über 5 Hooks. |
| **Release-Gates als Plugin-Architektur** mit Allowlist (`.agent-meta-managed` ∪ `.allowed-gates`), Skip statt Fail für unbekannte Skripte. | Sauberes Supply-Chain-Design (#598). |
| **Metadata-Header-Kontrakt** (`hook/version/event/matcher/provider/enabled_by_default`) macht Hooks maschinell registrierbar (`scripts/lib/hooks.py`). | Gut — Hooks sind Daten, nicht nur Skripte. |
| **Stale-Cleanup** über `.agent-meta-managed`-Index pro Zielverzeichnis. | Konsistent mit dem Rest des Syncers. |

### 3.2 Konzept-Schwächen

1. **Hooks sind de facto Claude-Code-only.** Jeder Hook trägt `# provider: Claude` (`viz-log.sh` hat gar kein `provider`-Feld). Der Hook-Kontrakt ist fest an Claude Codes Event-Modell gebunden: JSON auf stdin mit `tool_name`/`tool_input`/`tool_result`, Exit-Code 2 = block, Events `PreToolUse`/`PostToolUse`, Registrierung in `settings.json`. Ein Provider mit anderem Hook-Modell hätte **kein Adapter-Konzept**, an das er andocken könnte.

2. **Mammouth-Hooks sind konzeptionell unbelegt.** `has_hooks: true` gibt es nur für Claude und Mammouth. Mammouth bekommt die Claude-Hooks **1:1 gespiegelt** (`.mammouth/hooks/`) plus ein `settings.json` im **Claude-Format**. Ob Mammouth dieses Protokoll versteht, ist nirgends belegt — `provider-capabilities.yaml` sagt selbst *"native orchestration surface undocumented"* und begründet `hooks: true` zirkulär mit *"evidence-based: ai-providers.yaml sets has_hooks: true"*. Die Evidenz ist die eigene Konfiguration. `tests/test_provider_hooks_config.py` testet nur, dass Mammouth **eigene Pfade** hat — nicht, dass die Hooks dort funktionieren.

3. **Begriffs-Inkonsistenz "security boundary" vs. "keine Sicherheitsgrenze".** `branch-guard.md` und der Guard-Header nennen den Guard explizit *"Konventions-Tool, keine harte Sicherheitsgrenze"* (#592, Command-Substitution-Lücke bewusst offen). Wave 3 klassifiziert denselben Guard als *"security boundary → fail-closed"*. Beides ist für sich richtig (Grenze gegen **Unfälle**, nicht gegen **Angreifer**), aber nirgends als ein Begriffspaar definiert. Wer nur eine der beiden Stellen liest, zieht die falsche Schlussfolgerung.

4. **Selbst-Lockout ohne Selbstheilung** (heute in dieser Session erlebt): Ist die Guard-Datei selbst syntaktisch kaputt (Merge-Konfliktmarker), blockiert der `PreToolUse`-Hook **jeden** Tool-Aufruf — auch `Read`/`Edit` auf genau die Datei, die man reparieren müsste. Es fehlt konzeptionell ein Hook-Health-Fallback (z.B. `bash -n` Self-Check → fail-open bei Syntaxfehler der **eigenen** Datei, oder eine Ausnahme für Read/Edit unter `<hooks_dir>/`). Ein Konventions-Tool, das das Repo unreparierbar macht, widerspricht seinem eigenen Zweck.

5. **Keine Versions-Drift-Erkennung für ausgerollte Hooks.** Für Platform-Overrides gibt es seit #560 eine Staleness-Warnung (`based-on@version`). Für Hooks in Consumer-Projekten gibt es nur den Managed-Index — kein Vergleich "generierte Kopie v2.4.1 vs. Template v2.6.0". Der heute erlebte False-Positive (`checkout --theirs -- .claude/...` matcht das `checkout -- .`-Muster) ist in v2.6.0 behoben, aber jedes Consumer-Projekt, das nicht synct, läuft mit der alten Regex weiter — unsichtbar.

---

## 4. Syncer — Konzept-Bewertung

### 4.1 Konzepte im Syncer (positiv)

- **Layer-Modell** `0-external / 1-generic / 2-platform / 3-project` mit `based-on` / `extends` / `patches`-Composition und Placeholder-Escaping.
- **Placeholder-Lifecycle:** Registry (`consistency/placeholders.py::_BUILTIN_VARS`), Substitution in `variables.py`, Drift-Erkennung über `context-hashes.json` + `--check` (CI-Mode). Unbekannte Platzhalter werden bei `--validate` gemeldet (heute bei `{{ISSUE_LANGUAGE}}` erlebt — funktioniert).
- **Deklaratives Provider-Datenmodell** über vier Registries: `ai-providers.yaml` (Identität, Pfade, Capabilities, Model-Tiers, MCP-Format, Gitignore, Isolation), `provider-capabilities.yaml` (Orchestrierungs-Fähigkeiten), `provider-bootstrap.yaml` (Post-Sync-Registrierung), `provider-tools.yaml` (Tool-Whitelist). **Model-Tier-Abstraktion** `nano/fast/balanced/powerful/max → Provider-Model-ID` ist konzeptionell die eleganteste Stelle des Systems.
- **Capability-Flags statt Provider-Namen** — das richtige Muster existiert bereits: `_has_capability(pc, "context-embedded-rules")` (`context.py:745`), `pc.get("commands_dir", ...)` (Gemini/Opencode in `commands.py`), `pc.get("hooks_dir", ...)` (`hooks.py`), `frontmatter_strip_fields` als YAML-Key (#505). Es wird nur **nicht konsequent** angewendet.
- **Managed-Index** (`.agent-meta-managed`) für Stale-Cleanup pro Artefakt-Typ (Agents, Rules, Commands, Hooks, Release-Gates, Hook-Lib).
- **Seit Wave 6/7:** `main()` als Dispatch-Table + `_SyncContext`, `build_variables` dekomponiert, `agents.py` in frontmatter/provider_transform/agent_sync gesplittet, `scripts/lib` azyklisch — die Kern-Struktur ist jetzt tragfähig für die Empfehlungen in §7.

### 4.2 Konzept-Schwächen

**(a) Doppelte Wahrheiten — Python-Maps duplizieren YAML-Inhalte.** Jede dieser Maps ist ein Ort, an dem ein neuer Provider stillschweigend fehlt:

| Stelle | Dupliziert | YAML-Quelle, die bereits existiert |
|---|---|---|
| `scripts/lib/context.py:983–989` `provider_dirs` (inkl. hartem `"Mammouth"`) | Agents-Verzeichnis | `ai-providers.yaml::agents_dir` |
| `scripts/lifecycle_check.py:63–66` (nur Claude/Opencode/Gemini/Continue!) | Pending-Tasks-Datei | `ai-providers.yaml::pending_tasks_file` |
| `scripts/lib/viz.py:689–694` | Bash-Tool-Name pro Provider | fehlt in YAML (neuer Key nötig) |
| `scripts/lib/setup.py:210` `valid_providers` | Provider-Liste | `ai-providers.yaml` Keys |
| `scripts/lib/isolation.py:75–81, 290–292` | Isolation-Verhalten | `ai-providers.yaml::isolation-dirs` (teilweise) |

**(b) Bootstrap-Abstraktion wird umgangen.** `BootstrapEngine` + `provider-bootstrap.yaml` existieren **genau** für provider-spezifische Post-Sync-Aktionen. Trotzdem ruft `agent_sync.py:661` für Gemini `_inject_gemini_bootstrap(...)` hardcodiert direkt auf; nur Continue (`:669`) geht über die Engine. Die Abstraktion ist halb verwirklicht — der Gemini-Pfad ist der Präzedenzfall, den ein nächster Provider kopieren würde.

**(c) Claude als privilegierter Default überall.** Claude ist nicht ein Provider unter sechs, sondern das implizite Referenzmodell, von dem alle anderen als **Abweichung** modelliert sind:
- `providers.py::resolve_providers` fällt auf `["Claude"]` zurück; `load_providers_config` hat einen Claude-only-Fallback-Block; `resolve_context_filename` kodiert *"CLAUDE.md → AGENTS.md außer für Claude"*.
- `context.py`: `if provider == "Claude"` → `AGENT_HINTS_CLAUDE` statt `AGENT_HINTS`; static header wird für Claude *woanders* (`sync_claude_md_static`) gebaut; `_init_provider_settings_json` für Claude übersprungen; `gemini_active`-Sonderlogik für den Bootstrap-Block.
- `sync.py:1239` `is_claude = "Claude" in providers`; `sync.py:1510` *"already in base_gitignore_entries"* nur für Claude; `sync.py:1358` `if prov == "Copilot": prov_dir_name = ".github/copilot"` (Pfad-Ausnahme, die `isolation-dirs` in YAML schon kennt).
- 10+ Funktionen mit `provider: str = "Claude"` als Default-Parameter (harmlos, aber Symptom).

**(d) Provider-Verhalten als Python-Konstanten statt YAML-Flags.** `rules.py:40 _ALWAYS_APPLY_PROVIDERS = {"Continue"}`; `commands.py` nutzt `CLAUDE_COMMANDS_DIR`/`CONTINUE_COMMANDS_DIR`-Konstanten, obwohl `commands_dir` in YAML existiert und von Gemini/Opencode **im selben `if/elif`** bereits genutzt wird — zwei Muster nebeneinander in einer Funktion.

**(e) Format-Dispatcher mit geschlossener Menge, fail-soft aber unsichtbar.** `mcp_provider_config._write_provider_config` kennt 4 Formate (`claude-settings`, `gemini-settings`, `opencode-json`, `continue-yaml`), unbekannt → Warnung + Skip. `commands.py:124–141` `if/elif` über 4 Provider mit `else: return` → ein 7. Provider bekommt **stillschweigend keine Commands**, ohne Log-Zeile. `provider_transform.py:167/224/256/305/341/358` ist eine **6-Wege-`elif`-Kette** (Continue/Claude/Gemini/Opencode/Copilot/Mammouth) — die größte Einzelstelle, an der Agnostik im Code bricht.

---

## 5. Provider-Agnostik — Credo vs. Realität

**Credo-Text** (`.claude/skills/provider-agnostic/SKILL.md`, vollständig):
> Generische Templates in `1-generic/` müssen provider-agnostisch sein. Keine spezifischen Prompts für Claude, Gemini etc., außer als Fallback/Feature-Flag.

**Befund:**
- Auf **Template-Ebene** wird das Credo weitgehend eingehalten: `provider_transform.py` zieht Provider-Unterschiede (Frontmatter-Felder, Tool-Namen, Model-ID-Format, XML-Wrapping) **aus** den Templates heraus in den Syncer. Das ist der richtige Schnitt.
- Aber das Credo **endet dort, wo der Syncer anfängt**. Es gibt keinen Satz wie *"Provider-Unterschiede werden über Config-Keys ausgedrückt, nie über `if provider == "Name"` im Python-Code"*. Ohne diesen Maßstab ist jeder der 86 Treffer für ein Review "vertretbar".
- **Zählung:** 86 Provider-Name-Literale in 19 Python-Dateien unter `scripts/`. Harmlos: ~10 Parameter-Defaults. Echte Branch-Logik: `provider_transform.py` (6-Wege), `commands.py` (4-Wege + `else: return`), `isolation.py` (4-Wege), `context.py` (≥6 Claude/Continue/Gemini-Sonderpfade), `agent_sync.py` (Gemini/Continue), `rules.py`, `sync.py` (Claude/Copilot/Continue), `viz.py`, `lifecycle_check.py`, `setup.py`.
- Das **funktionierende Gegenmuster** existiert im selben Code (Capability-Flags, `pc.get(...)`, `frontmatter_strip_fields`) — es fehlt nur die Regel, die es zur Pflicht macht.

---

## 6. Praxistest: "Provider #7 einbauen" — Touchpoint-Analyse

Annahme: neuer, unkomplizierter Provider **X** — file-based Agents (`.x/agents/*.md`), eigene Context-Datei, kein Hook-Support, MCP über JSON-Settings.

**Pflicht-YAML (erwartbar, gut abgegrenzt):**
1. `config/ai-providers.yaml` — Provider-Block
2. `config/provider-capabilities.yaml` — Capability-Eintrag
3. `config/provider-bootstrap.yaml` — Bootstrap-Eintrag (`mechanism: file-based, action: none`)
4. `config/provider-tools.yaml` — Tool-Whitelist
5. `templates/configs/X.project-template.md` (+ ggf. `X.settings-template.json`)

**Pflicht-CODE (das eigentliche Problem — jede Stelle wird bei Vergessen still übersprungen):**
6. `scripts/lib/provider_transform.py` — neuer `elif provider == 'X'`-Zweig (sonst unklar, was im Fallthrough mit Frontmatter/Tools passiert)
7. `scripts/lib/commands.py:124` — neuer `elif` (sonst `else: return` → **keine Commands, kein Log**)
8. `scripts/lib/context.py:983` — `provider_dirs`-Map ergänzen
9. `scripts/lifecycle_check.py:63` — `pending_tasks`-Map ergänzen (**Copilot/Mammouth fehlen dort heute schon**)
10. `scripts/lib/viz.py:689` — Bash-Tool-Map ergänzen
11. `scripts/lib/isolation.py:75` — Isolation-Branch
12. `scripts/lib/setup.py:210` — `valid_providers` (sonst im Setup-Wizard nicht wählbar)
13. `scripts/lib/mcp_provider_config.py:395` — nur falls neues Settings-Format (sonst Warnung + Skip)
14. Hook-Adapter — nur falls `has_hooks: true` mit anderem Event-Modell (**kein Konzept vorhanden**, siehe §3.2.1)

**Fazit:** ~5 YAML- + **7–9 Code-Touchpoints**. Der `/add-provider`-Command (`.claude/commands/add-provider.md`) deckt nur *"bekannten Provider aktivieren"* (Step 3) und *"Issue filen"* (Step 4) ab — für das tatsächliche **Einbauen** gibt es weder Checkliste noch Lint-Regel, die vergessene Stellen aufdeckt. Der `lifecycle_check.py`-Gap ist der Beweis, dass genau das bereits zweimal passiert ist (Copilot, Mammouth).

**Bewertung Erweiterbarkeit: 3/5.** Das Datenmodell trägt; die Code-Seite verlangt Wissen über ≥7 verstreute Stellen ohne Guard-Rail.

---

## 7. Empfehlungen (priorisiert, konzeptionell — nichts davon in diesem Audit umgesetzt)

| Prio | Empfehlung | Warum | Aufwand |
|---|---|---|---|
| **P1** | **Agnostik-Lint als Guard-Rail:** neue `config_audit`-Regel `provider_registry_completeness` — für jeden Provider in `ai-providers.yaml` prüfen, dass alle provider-keyed Python-Maps und `elif`-Ketten ihn kennen (oder besser: die Maps ganz eliminieren, siehe P2). Hätte den Copilot/Mammouth-Gap in `lifecycle_check.py` sofort gemeldet. | Billigster Hebel gegen "still vergessen". | S–M |
| **P1** | **Credo erweitern:** `provider-agnostic`-Skill um einen Syncer-Absatz: *"Provider-Unterschiede werden über Capability-Flags/Config-Keys in `ai-providers.yaml` ausgedrückt, nie über `if provider == "Name"` im Python-Code. Ein neuer Provider muss ohne Python-Änderung aktivierbar sein, sofern er kein neues Datei-Format braucht."* | Ohne Maßstab kein Review-Kriterium. | S |
| **P2** | **Doppelte Wahrheiten eliminieren:** die 5 Maps aus §4.2(a) durch `pc.get(...)`-Lookups ersetzen; für Viz-Bash-Tool-Name und Isolation-Verhalten neue YAML-Keys einführen. Regression: Sync-Output byte-identisch (Baseline-Diff-Harness aus #563 wiederverwenden). | Reines Refactoring, sehr gut testbar. | M |
| **P2** | **`provider_transform.py` datengetrieben machen:** die 6-Wege-`elif` nicht bloß in ein `dict`-of-callables umbauen (Kosmetik), sondern die Transformationsschritte (Frontmatter-Felder strippen/umbenennen, Tool-Mapping, Model-ID-Format) als **Daten** in `ai-providers.yaml` beschreiben — `frontmatter_strip_fields` (#505) ist das bereits existierende Vorbild. | Größter Einzel-Verstoß, größter Gewinn. | L |
| **P2** | **Bootstrap-Abstraktion konsequent nutzen:** Gemini auf `BootstrapEngine` umziehen, `_inject_gemini_bootstrap` entfernen. | Beseitigt den falschen Präzedenzfall. | S–M |
| **P3** | **Hook-Konzept ehrlich machen:** entweder `has_hooks: false` für Mammouth, bis das Protokoll belegt ist, oder neues Feld `hook_protocol: claude-code-json` in `ai-providers.yaml`, sodass Hooks nur für protokoll-kompatible Provider gespiegelt werden. Plus: Hook-Self-Health-Fallback gegen den Selbst-Lockout (§3.2.4). Plus: Versions-Drift-Warnung für ausgerollte Hooks analog #560. | Verhindert stille Fehlfunktion und den heute erlebten Lockout. | M |
| **P3** | **Claude entprivilegieren:** `default-provider` als expliziter Key statt hardcodiertem `["Claude"]`; `resolve_context_filename`-Regel als YAML-Attribut (`shares_generic_context: true`); `AGENT_HINTS_CLAUDE`-Sonderpfad über Capability-Flag. | Macht Claude zu einem Provider unter n. | M |
| **P3** | **`/add-provider` um Step 5 "Neuen Provider einbauen"** mit der Touchpoint-Checkliste aus §6 ergänzen. | Kurzfristig billigste Absicherung, bis P1/P2 greifen. | S |
| **P3** | **Begriffspaar definieren:** "Konventions-Grenze (fail-closed gegen Unfälle)" vs. "Sicherheitsgrenze (gegen Angreifer)" einmal zentral in `branch-guard.md` festhalten und in den Hook-Headern referenzieren. | Beendet die Doppeldeutigkeit aus §3.2.3. | S |

---

## 8. Nicht Gegenstand dieses Audits

Agent-Templates (`agents/*`), Systemdokumentation (`docs/*`), Admin-UI, Test-Suite, Korrektheits-/Security-Details der Hooks (Audit 2026-08, Waves 1–3), Performance. Graphify-Graph ist Stand 31.08. (vor Wave 4–10). Project Atlas nicht im Repo.

## ARTIFACTS

- Diese Datei: `docs/plans/audit-2026-09-system-concept.md`
- Bezug: `docs/plans/audit-2026-08-refactoring-roadmap.md` (abgeschlossen), `.claude/skills/provider-agnostic/SKILL.md`, `config/ai-providers.yaml`, `config/provider-capabilities.yaml`, `config/provider-bootstrap.yaml`, `scripts/lib/provider_transform.py`, `graphify-out/GRAPH_REPORT.md`
