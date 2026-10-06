---
spec-id: SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06
title: Compress Generated Root Context (AGENTS.md/CLAUDE.md) — Technical Specification
status: APPROVED
related-issue: "#844"
related-plan: docs/plans/issue-540-context-compression.md
---

# Compress Generated Root Context — Spec

> Status: APPROVED (2026-10-06)
> Trace-Anker: `spec-id: SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06`

## 0. Zentraler Befund (vor dem Lesen des Rests wichtig)

Issue #844 wurde mit der Annahme formuliert, fünf Kompressions-Mechanismen müssten
neu gebaut werden (L-Tier, 9–20 Dateien). Die Code-Recherche zu diesem Spec zeigt:
**vier der fünf Acceptance-Criteria-Buchstaben (a, b, d und der Großteil von c) sind
bereits in Issue #540 implementiert und gemergt** (sichtbar an `COMPACT_MODE`-Wiring
in `scripts/lib/config.py`, `scripts/lib/context.py`, `scripts/lib/bootstrap.py` und
an den grünen Tests `tests/test_context_compact_mode.py`,
`tests/test_context_size_guard.py`, `tests/test_project_metadata_full_mode_structure.py`).
Der einzige Grund, warum agent-metas eigenes `AGENTS.md`/`CLAUDE.md` trotzdem groß
sind: **`.meta-config/project.yaml` schaltet den existierenden `compact`-Modus für das
eigene Repo nie ein** (`context_file.mode: full`, zusätzlich mit
`oversize_acknowledged: true` quittiert) — und **eine generische Kernregel
(`branch-guard`) wurde nie in die bestehende Verdichtungs-Tabelle
`_COMPACT_PLATFORM_RULES` aufgenommen**.

Die reale Umsetzung dieses Specs ist daher **S/M-Tier** (2 Produktionsdateien + 1–2
neue Testdateien), nicht L-Tier. Abschnitt 6 benennt die korrigierte Dateiliste
explizit. Buchstabe (e) der Issue ("newline-squashing bug") ist auf dem aktuellen
`main` **nicht reproduzierbar** (Abschnitt 5, AC-6) und wird als offene Frage statt
als Code-Fix spezifiziert.

## 1. Problem / Ziel / Nicht-Ziele

**Problem:** `AGENTS.md` (575 Zeilen) und `CLAUDE.md` (149 Zeilen, zusammen 724) von
agent-metas eigenem Repo laden bei jeder Session fünf Content-Typen immer-an, obwohl
ein Großteil davon discoverable (via `ls`/`find`/`Read`) oder bereits anderswo als
Lazy-Pointer verfügbar ist: Agent-Directory-Tabelle mit Voll-Beschreibung und
Leerzeilen-Trennung (~127 Zeilen), Gemini-Bootstrap-Block mit expliziter
`define_subagent`-Aufzählung für alle ~62 Agenten (~134 Zeilen), eingebettete
Kernregel-Referenzdetails (Branch-Guard "Guard-Terminologie" + "Bekannte Grenzen",
~24 Zeilen), Verzeichnisbaum + mehrzeilige Build/Dev-Befehle (~30 Zeilen).

**Ziel:** Root-Context spürbar verdichten, ohne Instruktionsverlust — Overview/
Referenzdetail raus, der Betriebsanweisungs-Kern bleibt. Konkret für agent-metas
eigenes Repo:
1. Existierenden `context_file.mode: compact`-Mechanismus (Issue #540) aktivieren.
2. Die generische Kernregel `branch-guard` in die bestehende Verdichtungs-Tabelle
   `_COMPACT_PLATFORM_RULES` (`scripts/lib/context.py`) aufnehmen — bisher nur für
   die vier 2-platform-Regeln (`sync-interface`, `architecture`, `conventions`,
   `admin-ui`) aktiv, die für agent-metas eigene aktive Provider-Kombination
   (Opencode+Gemini, beide mit `skills_dir`) ohnehin nie embedden (siehe § 4, IC-1).
3. Regressionstests ergänzen, die den Vorher/Nachher-Zustand sperren.

**Nicht-Ziele:**
- Keine neue Config-Option, kein neues Template-Feature — `COMPACT_MODE` und
  `compact_embedded_rule()` existieren bereits vollständig (Issue #540).
- Kein Fix für Buchstabe (e), solange der Fehler nicht reproduzierbar ist (§ 5, AC-6).
- Keine generische Lösung für providerspezifische Pointer-Pfade (`.claude/...` /
  `rules/1-generic/...`) in anderen Konsumenten-Projekten — bekannte, bereits
  existierende Einschränkung der vier bestehenden Tabelleneinträge, nicht neu
  eingeführt durch diesen Spec (§ 7, OQ-2).
- Keine Änderung an `templates/configs/AGENTS.project-template.md`,
  `templates/configs/CLAUDE.project-template.md` oder
  `templates/context/partials/project-metadata.md` — Verifikation zeigt: diese
  Dateien benötigen für die ACs (a)–(d) keine Änderung (§ 6).

## 2. Beantwortung der drei Design-Fragen (mit Beleg)

### Frage 1 — Welche Provider brauchen den Bootstrap-Block wirklich?

Beleg: `config/provider-bootstrap.yaml` (vollständig gelesen). Jeder Provider trägt
ein `mechanism`-Feld:

| Provider | mechanism | action | Bootstrap-Block in Root-Context? |
|---|---|---|---|
| Claude | file-based | none | Nein |
| Opencode | file-based | none | Nein |
| Gemini | api-based | inject-bootstrap-instructions | Ja (generated, per-Agent-Roster) |
| Continue | config-based | update-config | Nein (eigener Mechanismus, kein AGENTS.md-Block) |
| Copilot | file-based | none | Nein |
| Mammouth | file-based | none | Nein |
| Codex | file-based | none | Nein |
| ZCode | api-based | inject-bootstrap-instructions | Ja (static, kurz) |
| KimiCode | file-based | none | Nein |

→ **Bootstrap ist bereits vollständig provider-konditional** (`BootstrapEngine.
run_bootstrap()`, `scripts/lib/bootstrap.py:103-115`: `mechanism == "none" or
action == "none"` → sofortiger No-op). Für agent-metas aktive Provider (Claude,
Opencode, Gemini) bekommt ausschließlich Gemini einen Bootstrap-Block, scoped per
`<!-- agent-meta:bootstrap-begin:Gemini -->` und von `_cleanup_bootstrap_block()`
automatisch entfernt, sobald Gemini inaktiv wird. AC (a) der Issue ist also bereits
erfüllt — der einzige verbleibende Hebel ist die **Dichte** des Gemini-Blocks selbst
(siehe Frage 1b).

**Frage 1b (Dichte):** `scripts/lib/bootstrap.py:285-314`
(`generate_gemini_bootstrap_instructions`) hat bereits einen `compact: bool`-Parameter
(Issue #540 B6): `compact=True` ersetzt die ~124-zeilige Pro-Agent-Aufzählung durch
eine generische 6-Zeilen-Instruktion, bei identischem Instruktionskern. Der
Aufrufer `scripts/lib/agent_sync.py:1316` übergibt bereits
`compact=variables.get("COMPACT_MODE") == "true"`. **Es fehlt nur die Aktivierung
von `COMPACT_MODE` für agent-metas eigenes Repo** (§ 4, IC-2).

### Frage 2 — Agent-Directory-Tabelle: 1 Zeile/Agent oder Pointer-Ersatz?

Beleg: `scripts/lib/agents.py` (`build_agent_hints`, `build_agent_table`) und
`scripts/lib/delegation_table.py` (`get_routing_rules`, `derive_keywords`). Die
gerenderte Markdown-Tabelle in AGENTS.md ist **write-only** — kein Code-Pfad liest
sie zurück:
- Das Orchestrator-Routing (`get_routing_rules()`) liest `routing_patterns` direkt
  aus `config/role-defaults.yaml`, nie die gerenderte Tabelle.
- Tests, die nach "Core Capabilities"/"Agent Directory" suchen
  (`tests/test_context_compact_mode.py`, `tests/fixtures/slimming-golden/
  orchestrator.md`), prüfen nur das *Rendering*, nicht ein Re-Parsing.

→ **1 Zeile/Agent ist die richtige Wahl** (nicht Komplett-Ersatz durch Pointer) —
und existiert bereits exakt so: `templates/context/partials/agents-table.md`
Zeile 7 (`{{#if COMPACT_MODE}}{{#each active_agents}}| `{{name}}` |
{{keywords}} |{{/each}}`), gefüttert von `derive_keywords()`
(`scripts/lib/delegation_table.py:16-31`, ≤3 Keywords, ≤100 Zeichen, erste
Satzsegmente). Die volle Beschreibung bleibt im jeweiligen Agent-Template einen
`Read` entfernt — kein Wissensverlust für Routing-Zwecke, nur für die
Root-Context-Darstellung. Fehlt nur: `COMPACT_MODE` für agent-meta aktivieren.

### Frage 3 — Welche Regel-Abschnitte sind Hard Gates vs. Referenzdetail?

Beleg: `config/rules-presets.yaml` (vollständig gelesen) und
`scripts/lib/context.py:1503-1569` (`_COMPACT_PLATFORM_RULES` +
`compact_embedded_rule()`). Die Taxonomie ist bereits etabliert:

- **Hard Gate, bleibt IMMER eingebettet** (nicht im `lazy`-Preset gelistet →
  `alwaysApply: true`/`embed: true` per Default): `branch-guard`,
  `commit-conventions`, `language` (Sprachregeln), `speech-mode`,
  `no-worktree-isolation`, `dod-criteria`, `use-orchestrator`, zusätzlich
  `mcp-guardrails` (eigene, nicht-preset-gesteuerte Regel). Diese acht sind laut
  Kommentar in `rules-presets.yaml:104-110` explizit die "Kernregeln".
- **Referenzdetail, bereits lazy** (`channel: skill` im `lazy`-Preset, Zeilen
  111–200): `sync-interface`, `admin-ui`, `architecture`, `conventions`,
  `submodule-protection`, `a2a-delegation-gates`, `issue-lifecycle`,
  `lifecycle-tasks`, `provider-agnostic`, alle `mcp-<server>`-Regeln,
  `tool-graphify`, die drei `se-cascade-*`-Regeln, die vier
  Spec/Plan-Workflow-Regeln. **A2A- und SE-Kaskade-Regeln, die die Issue explizit
  als Kompressionsziel nennt, sind damit bereits vollständig lazy** — in der
  aktuellen AGENTS.md nur als 1-Zeilen-Pointer sichtbar (bestätigt im gelesenen
  Live-AGENTS.md, "## Übrige Regeln (Lazy-Load)"-Tabelle).
- **Innerhalb eines Hard-Gate-Regelfiles: Instruktion vs. Referenzdetail.**
  `branch-guard.md` selbst mischt beides: Präambel (Titel + 2-Zeilen-Direktive,
  IMMER Instruktion) + zwei H2-Abschnitte ("Guard-Terminologie…", "Bekannte
  Grenzen") die reine Erklärung/Dokumentation für menschliche Leser sind, keine
  Handlungsanweisung an den Agenten. `_COMPACT_PLATFORM_RULES` kennt diese
  Unterscheidung bereits (`keep`-Tupel = Instruktion, alles andere wird zu einem
  Pointer) — nur eben bisher ausschließlich für vier 2-platform-Regeln, nicht für
  `branch-guard`. MCP-Prohibitions sind in `rules/1-generic/mcp-guardrails.md`
  bereits minimal (nur 3 Kurzbullets + Pointer auf die lazy `mcp-<server>`-Regeln)
  — kein weiterer Hebel nötig.

→ **Etablierte Konvention:** Hard-Gate-Direktive bleibt wortgleich eingebettet;
Erklärungs-/Limitations-Prosa innerhalb eines Hard-Gate-Files wird zum
1-Zeilen-Pointer, wenn sie als H2-Abschnitt isolierbar ist (exakt der
`_COMPACT_PLATFORM_RULES`-Mechanismus). Dieser Spec wendet die Konvention auf
`branch-guard` an statt eine neue Taxonomie zu erfinden.

## 3. Interface Contracts

### IC-1 — `scripts/lib/context.py::_COMPACT_PLATFORM_RULES` (Dict-Erweiterung, Zeile 1512)

Signatur unverändert (`compact_embedded_rule(output_stem: str, content: str) ->
str`, Zeile 1546); neuer Dict-Eintrag:

```python
_COMPACT_PLATFORM_RULES = {
    "sync-interface": {...},   # unverändert
    "architecture": {...},     # unverändert
    "conventions": {...},      # unverändert
    "admin-ui": {...},         # unverändert
    "branch-guard": {
        "keep": (),
        "pointer": (
            "Details (Guard-Terminologie: Convention vs. Security Boundary, "
            "bekannte technische Grenzen): `rules/1-generic/branch-guard.md`."
        ),
    },
}
```

`"keep": ()` ist korrekt und ausreichend: die Präambel (H1-Titel + Direktive vor
der ersten `## `-Überschrift) wird von `compact_embedded_rule()` *immer* behalten
(Zeile 1562: `keep_current = True` vor der ersten H2), unabhängig vom `keep`-Set.
Beide H2-Abschnitte von `branch-guard.md` ("## Guard-Terminologie…", "## Bekannte
Grenzen") sind in keinem `keep`-Set enthalten → werden entfernt, danach wird genau
die eine Pointer-Zeile angehängt.

**Fehlerpfad:** unbekannter `output_stem` → `compact_embedded_rule()` gibt
`content` unverändert zurück (Zeile 1557-1559, bereits vorhanden, kein neuer
Fehlerpfad nötig).

**Wirkradius:** Der neue Eintrag wirkt nur im Zweig `if not has_native_rules:`
(`scripts/lib/context.py:1710`), d.h. ausschließlich für Opencode/Gemini als
Renderer des gemeinsamen `AGENTS.md`. Claudes eigener Kanal
(`.claude/rules/branch-guard.md`, generiert von `sync_rules()`, `has_rules: true`)
bleibt **byte-identisch** zu heute, in beiden `COMPACT_MODE`-Zuständen — Claude
verliert nichts. Der kanonische Quelltext `rules/1-generic/branch-guard.md` selbst
wird **nicht verändert**.

Wichtige Abgrenzung zu den vier bestehenden Einträgen: `sync-interface`,
`architecture`, `conventions`, `admin-ui` sind zusätzlich `channel: skill` im
`lazy`-Preset (`config/rules-presets.yaml:111-123`) — für agent-metas aktive
Provider-Gruppe (Opencode+Gemini, beide mit `skills_dir`) greift
`rules_file_channel=True`, wodurch diese vier Regeln den Embed-Pfad (und damit
`compact_embedded_rule()`) **nie erreichen** (`scripts/lib/context.py:1778-1783`,
`rule_opts_lazy_channel`-Gate). Ihre Tabelleneinträge sind für das heutige
agent-meta-Repo faktisch inert — ein Sicherheitsnetz für Provider-Gruppen ohne
vollständigen `skills_dir`, nicht die aktiv wirksame Kompression. `branch-guard`
hat **kein** `rules-presets.yaml`-Opt-out (`alwaysApply: true`/`embed: true` per
Default) und durchläuft den Embed-Pfad immer — der neue Eintrag ist damit der
**einzige der fünf Tabelleneinträge, der für agent-metas reales AGENTS.md
tatsächlich Zeilen spart.**

### IC-2 — `.meta-config/project.yaml::context_file` (Config-Wert-Änderung)

Vorher:
```yaml
context_file:
  mode: full
  max_lines: 250
  oversize_acknowledged: true
  auto_generate: true
```

Nachher:
```yaml
context_file:
  mode: compact
  max_lines: 250
  auto_generate: true
```

`oversize_acknowledged` wird entfernt — nicht blind, sondern bedingt durch AC-5:
bleibt nur dann als bewusst re-kommentierter Eintrag erhalten, wenn die gemessene
Zeilenzahl nach der Umstellung `max_lines` tatsächlich noch überschreitet.

Kein Schema-Change nötig: `mode: compact` ist laut
`config/project-config.schema.json` bereits ein gültiger Enum-Wert.
`build_variables()` (`scripts/lib/config.py:1375-1388`) leitet `COMPACT_MODE`
bereits korrekt ab (`"true"` nur bei `mode: compact`; fehlender/ungültiger Key
→ `"false"`, safe-side).

**Fehlerpfad:** unbekannter `mode`-Wert → `COMPACT_MODE = "false"` (bestehender
Code, Zeile 1388, safe-side-Default, kein neuer Fehlerpfad).

### IC-3 — `scripts/lib/consistency/context_size.py::check_context_file_size` (unverändert, nur verifiziert)

Signatur/Verhalten unverändert. Bereits vollständig verdrahtet in
`scripts/consistency-check.py:44,215` → läuft bei jedem `sync.py --validate`.
Default `DEFAULT_MAX_LINES` liegt bei 250 (strenger als die in der Issue
genannten 300) und ist projektweit per `context_file.max_lines` überschreibbar;
`oversize_acknowledged: true` unterdrückt die Warnung vollständig. AC (d) der
Issue ist damit **bereits erfüllt** — dieser Spec ändert hier nichts, verifiziert
nur (AC-5), dass die Warnung nach IC-1/IC-2 weiterhin korrekt feuert bzw. korrekt
still bleibt.

### IC-4 — `scripts/lib/bootstrap.py::generate_gemini_bootstrap_instructions` (unverändert, nur verifiziert)

Signatur/Verhalten unverändert (`compact: bool = False` existiert bereits,
Zeile 285-314). AC-3 verifiziert nur, dass der bestehende Aufrufer-Pfad
(`scripts/lib/agent_sync.py:1316`) nach IC-2 tatsächlich `compact=True` liefert.

## 4. Datenfluss

```
.meta-config/project.yaml (context_file.mode)
  │
  ▼
scripts/lib/config.py::build_variables()
  → COMPACT_MODE = "true" | "false"  (safe-side default: "false")
  │
  ├─► scripts/lib/context.py::_build_managed_block()
  │     _global_compact = COMPACT_MODE == "true"
  │     ├─► templates/context/partials/agents-table.md   (AC-2: 1 Zeile/Agent)
  │     ├─► templates/context/partials/project-metadata.md
  │     │     ({{#unless COMPACT_MODE}} Baum / {{#if COMPACT_MODE}} 1-Zeiler)
  │     ├─► compact_embedded_rule(output_stem, content)   (AC-4: branch-guard)
  │     ├─► build_knowledge_engine_hints(config, compact=_global_compact)
  │     └─► _generate_rule_content(server, compact=_compact)   (MCP, unverändert)
  │
  ├─► scripts/lib/agent_sync.py (Bootstrap-Aufruf)
  │     compact=COMPACT_MODE == "true"
  │     └─► scripts/lib/bootstrap.py::generate_gemini_bootstrap_instructions()
  │           (AC-3: kurze Instruktion statt Pro-Agent-Roster)
  │
  ▼
AGENTS.md / CLAUDE.md (geschrieben von scripts/lib/context.py,
  _regenerate_static_context / _update_managed_html_block)
  │
  ▼
scripts/consistency-check.py::check_context_file_size()
  (gelesen von python scripts/sync.py --validate)
  → WARNING, wenn Zeilenzahl > context_file.max_lines und nicht acknowledged
```

Persistenz: `.meta-config/context-hashes.json` erkennt die anstehende
Framework-Änderung (Drift) beim ersten Sync nach der Umstellung als
"static part differs" und schreibt einmalig ein `.sync-backup-<ts>`-Sibling vor
dem Overwrite — erwartetes, dokumentiertes Verhalten (§ 5, Risiko 2), kein Defekt.

## 5. Acceptance Criteria

Mapping zu den Issue-Buchstaben: (a)→AC-1, (b)→AC-2, (a, Dichte)→AC-3,
(c)→AC-4, (d)→AC-5, (e)→AC-6.

**AC-1 (Bootstrap provider-konditional, IC-4, bereits erfüllt/Verifikation)**
Given `config/provider-bootstrap.yaml` mit `action: none` für Claude/Opencode und
`action: inject-bootstrap-instructions` nur für Gemini,
When `python scripts/sync.py` für agent-metas aktive Provider (Claude, Opencode,
Gemini) läuft,
Then enthält ausschließlich `AGENTS.md` einen
`<!-- agent-meta:bootstrap-begin:Gemini -->`-Block; `CLAUDE.md` enthält keinen
Bootstrap-Block. Deaktiviert man Gemini, verschwindet der Block beim nächsten Sync
(`_cleanup_bootstrap_block`). — Bereits grün über bestehende Tests; keine
Code-Änderung, nur Verifikationslauf.

**AC-2 (Agent Directory ≤1 Zeile/Agent, IC-2)**
Given `context_file.mode: compact` (IC-2),
When `AGENTS.md` neu generiert wird,
Then rendert "## Agent Directory" jede aktive Rolle als genau eine Tabellenzeile
`| `name`  | ≤3 Keywords |` ohne Leerzeilen-Trennung — verifiziert durch
`tests/test_project_metadata_full_mode_structure.py` (bereits vorhanden, deckt den
Compact-Zweig von `agents-table.md` ab) plus manuellen Zeilenzahl-Vergleich auf dem
realen `AGENTS.md` (vorher ≈127 Zeilen Tabellenblock, danach ≈64).

**AC-3 (Gemini-Bootstrap-Dichte, IC-4)**
Given `context_file.mode: compact`,
When der Gemini-Bootstrap-Block regeneriert wird,
Then enthält `AGENTS.md` NICHT mehr die Literal-Zeile
`define_subagent(name="orchestrator", ...)` (oder irgendeinen anderen Agenten),
sondern genau den 6-zeiligen generischen Text aus
`generate_gemini_bootstrap_instructions(compact=True)`
("Gemini/Antigravity benötigt eine einmalige Agent-Registrierung pro Session…").

**AC-4 (Branch-Guard-Pointer, IC-1 — einzige echte Code-Änderung)**
Given den neuen `_COMPACT_PLATFORM_RULES["branch-guard"]`-Eintrag,
When `AGENTS.md` mit `COMPACT_MODE=true` gerendert wird,
Then enthält der eingebettete Branch-Guard-Abschnitt den H1-Titel und die
Zwei-Zeilen-Direktive wortgleich, aber weder "## Guard-Terminologie…" noch
"## Bekannte Grenzen", sondern genau eine Pointer-Zeile auf
`rules/1-generic/branch-guard.md`.
When `.claude/rules/branch-guard.md` (Claudes natives Regelfile) oder `AGENTS.md`
mit `COMPACT_MODE=false` geprüft wird,
Then sind beide H2-Abschnitte byte-identisch zu heute vorhanden — kein
Wissensverlust für Claude oder den Full-Modus.

**AC-5 (Validator-Verifikation, IC-3 — bereits erfüllt, nur Nachweis)**
Given den unveränderten `check_context_file_size`,
When `python scripts/sync.py --validate` nach AC-2/AC-3/AC-4 läuft,
Then meldet der Check entweder keine Warnung mehr (Zeilenzahl ≤ `max_lines`) oder
weiterhin eine korrekte, nachvollziehbare Warnung mit der tatsächlichen
Zeilenzahl; im zweiten Fall MUSS `.meta-config/project.yaml` entweder
`oversize_acknowledged: true` mit einem Kommentar (gemessene Zeilenzahl + Datum)
behalten oder `max_lines` mit einer Ein-Zeilen-Begründung anheben — ein stilles
Entfernen von `oversize_acknowledged` ohne dass die Datei tatsächlich unter das
Limit fällt, ist ein Fail dieses Kriteriums (Fail-Richtung muss sichtbar bleiben).

**AC-6 (Newline-Squashing-Verdacht, IC-5 — Untersuchungs-Gate, kein Fix)**
Given den Issue-Vorwurf "Build & Development / Code-Konventionen bullet lists
collapse to a single line",
When `templates/context/partials/project-metadata.md` über
`TemplateBuilder.build()` mit agent-metas eigener aktiver Config gerendert wird
(beide `COMPACT_MODE`-Zustände),
Then bleiben `{{CODE_CONVENTIONS}}`/`{{KEY_PATTERNS}}` mehrzeilig mit einem
Bullet pro Zeile — verifiziert bereits manuell gegen das reale `CLAUDE.md`/
`AGENTS.md` (beide korrekt) und durch einen neuen Locking-Regressionstest
(`tests/test_project_metadata_bullet_rendering.py`, NEU). Der gemeldete Defekt
selbst gilt als **nicht reproduziert** und wird zur offenen Frage (§ 7, OQ-1)
degradiert — kein Produktionscode wird unter diesem AC geändert.

## 6. Datei-Liste (korrigiert gegenüber der Issue-Annahme)

| Datei | Änderung | Grund |
|---|---|---|
| `.meta-config/project.yaml` | MODIFY (1 Config-Wert) | IC-2 |
| `scripts/lib/context.py` | MODIFY (1 Dict-Eintrag, ~6 Zeilen) | IC-1 |
| `tests/test_context_compact_mode.py` | MODIFY (2 neue Testfunktionen) | AC-4 |
| `tests/test_project_metadata_bullet_rendering.py` | ADD (neu, klein) | AC-6 |
| `scripts/lib/bootstrap.py` | KEINE ÄNDERUNG (verifiziert) | AC-1, AC-3 bereits erfüllt |
| `config/provider-bootstrap.yaml` | KEINE ÄNDERUNG (verifiziert) | AC-1 bereits erfüllt |
| `scripts/lib/consistency/context_size.py` | KEINE ÄNDERUNG (verifiziert) | AC-5 bereits erfüllt |
| `scripts/consistency-check.py` | KEINE ÄNDERUNG (verifiziert) | AC-5 bereits erfüllt |
| `templates/configs/AGENTS.project-template.md` | KEINE ÄNDERUNG (verifiziert) | nutzt bereits `{{> project-metadata}}` korrekt |
| `templates/configs/CLAUDE.project-template.md` | KEINE ÄNDERUNG (verifiziert) | dito |
| `templates/context/partials/project-metadata.md` | KEINE ÄNDERUNG (verifiziert) | `COMPACT_MODE`-Zweige bereits korrekt |
| `templates/context/partials/agents-table.md` | KEINE ÄNDERUNG (verifiziert) | Compact-Zweig bereits korrekt |
| `scripts/lib/agent_sync.py` | KEINE ÄNDERUNG (verifiziert) | `compact=`-Wiring bereits korrekt |

**Größeneinschätzung:** S/M (2 Produktionsdateien geändert, 2 Testdateien
geändert/neu) — **keine L-Klassifikation** (9–20 Dateien trifft nicht zu). Die
Aufwandseinschätzung aus dem Task-Briefing war durch die Annahme fehlender
Infrastruktur verzerrt; die Infrastruktur existiert bereits aus Issue #540.

## 7. Offene Fragen + Risiken

**OQ-1 (Risiko, AC-6):** Ist der "newline-squashing"-Defekt überhaupt auf `main`
reproduzierbar, und wenn ja mit welcher exakten `project.yaml`/`platforms:`/
Provider-Kombination? Gefunden wurde ein *anderer*, bewusst so designter
Mechanismus (`CODE_CONVENTIONS+`-additiver Merge über mehrere
`platform-defaults.yaml`-Quellen, Join-Zeichen `"; "` statt Newline — siehe
`tests/test_platform_defaults_resolver.py:68-72`), der NUR greift, wenn ein
Projekt mehrere `platforms:`-Quellen mit `CODE_CONVENTIONS+` aktiviert. Das ist
kein Bug, sondern dokumentiertes additive-join-Verhalten für einen anderen
Anwendungsfall (Zusammenführen mehrerer Plattform-Defaults, nicht Rendering
eines einzelnen Bullet-Felds). Vor einem Code-Fix: Reproduktionsschritte vom
Issue-Melder einholen (konkretes `project.yaml`, aktive `platforms:`).

**OQ-2 (Risiko, vorbestehend, nicht neu):** Der Pointer-Pfad in
`_COMPACT_PLATFORM_RULES` ist hart codiert (`.claude/skills/...` für die vier
bestehenden Einträge; `rules/1-generic/branch-guard.md` für den neuen). Für
agent-metas eigenes Repo korrekt (Claude aktiv, Pfad existiert real). In einem
Konsumenten-Projekt, das agent-meta als Submodule an anderer Stelle mountet oder
ohne Claude betreibt, könnte der Pointer ins Leere zeigen — dieselbe
Einschränkung gilt bereits heute für die vier bestehenden Einträge. Kein Fix in
diesem Spec (Provider-aware Pointer-Resolution wäre ein eigenständiges,
architektonisches Follow-up).

**OQ-3 (geprüft, keine Aktion nötig):** Sollten weitere 1-generic-Kernregeln
(`no-worktree-isolation`, `repo-containment`, `commit-conventions`,
`dod-criteria`, `language`, `mcp-guardrails`, `use-orchestrator`) ebenfalls einen
`keep`/`pointer`-Split bekommen? Geprüft (§ 2, Frage 3): keine davon hat einen
isolierbaren OVERVIEW-H2-Abschnitt von vergleichbarer Länge wie
`branch-guard`s "Bekannte Grenzen" (alle ≤6 Zeilen Gesamtlänge). Kein Eintrag
hinzugefügt — Revisit nur, falls eine dieser Regeln künftig wächst.

**OQ-4 (Risiko, Messung nötig):** Die genaue Zeilenzahl von `AGENTS.md`/
`CLAUDE.md` nach AC-2/AC-3/AC-4 lässt sich ohne Ausführen von
`python scripts/sync.py` nicht exakt vorhersagen (grobe Schätzung: AGENTS.md
575 → ~300–330 Zeilen). Der Plan-Schritt MUSS `python scripts/sync.py && python
scripts/sync.py --validate` ausführen und die realen Vorher/Nachher-Zahlen als
Beleg für AC-2 und AC-5 festhalten (siehe auch `scripts/measure_context.py`,
bereits vorhanden aus Issue #540 Phase A2, ggf. wiederverwendbar für den
Vorher/Nachher-Report).

**Risiko (Migration):** Der erste Sync nach der `context_file.mode`-Umstellung
löst die bestehende Hash-Drift-Erkennung aus (`_regenerate_static_context`,
`scripts/lib/context.py:211-305`) und schreibt je ein `.sync-backup-<ts>`-Sibling
für `AGENTS.md`/`CLAUDE.md`, bevor der neue Inhalt geschrieben wird. Erwartetes,
bereits im Issue-540-Risiko-Register dokumentiertes Verhalten — kein Defekt,
aber im PR-Beschreibungstext erwähnen, damit es im Review nicht als
unerwarteter Diff überrascht.

**Risiko (Wissensverlust-Gegenprobe, bereits abgedeckt):** Die
Keyword-Verdichtung der Agent-Tabelle (`derive_keywords`, ≤3 Keywords) ist kein
neues Risiko dieses Specs — sie ist bereits in Issue #540 gebaut und getestet
(`tests/test_context_compact_mode.py`, `tests/test_build_variables_decomposition.py`).
Die volle Beschreibung bleibt im jeweiligen Agent-Template erreichbar; das
Routing selbst liest `role-defaults.yaml`, nie die gerenderte Tabelle (§ 2,
Frage 2). Für AC-4 gilt dieselbe Zusicherung: Claudes natives Regelfile und der
Full-Modus bleiben unverändert, nur der kompakte Opencode/Gemini-Pfad verliert
die Referenzprosa (nicht die Direktive).

## 8. Test-Plan

1. `python scripts/sync.py --validate` vor und nach der Änderung — Konsistenz-
   Check muss grün bleiben (bzw. die in AC-5 beschriebene begründete Warnung
   zeigen).
2. `pytest tests/test_context_compact_mode.py` — bestehende Suite muss grün
   bleiben; zwei neue Testfunktionen (analog zu
   `test_540_compact_opencode_separates_platform_rules_via_file_channel` und dem
   `_PLATFORM_RULE_FULL_MARKERS`-Muster) decken AC-4 ab: Compact-Render ohne
   "## Guard-Terminologie"/"## Bekannte Grenzen", Full-Render bzw. Claudes
   natives Rule-File weiterhin mit beiden Abschnitten.
3. `pytest tests/test_context_size_guard.py` — unverändert grün (AC-5,
   Regressionsschutz für den bereits bestehenden Mechanismus).
4. `pytest tests/test_project_metadata_bullet_rendering.py` (NEU) — sperrt den
   aktuellen, korrekten Mehrzeilen-Bullet-Render für `CODE_CONVENTIONS`/
   `KEY_PATTERNS` in beiden `COMPACT_MODE`-Zuständen (AC-6).
5. Manueller Vorher/Nachher-Report: `python scripts/sync.py` real ausführen,
   `wc -l AGENTS.md CLAUDE.md` vorher/nachher protokollieren (OQ-4) und im
   PR-Text dokumentieren.
6. `pytest tests/test_build_variables_decomposition.py` — unverändert grün
   (Regressionsschutz für `COMPACT_MODE`-Ableitung, nicht Teil dieser Änderung,
   aber durch IC-2 indirekt berührt).

## 9. Trace-Anker

`spec-id: SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06`
