# Project-Context-Injection Scope — Spec

> Status: **DRAFT**
> Revision: 2 (Review-Auflösung 2026-11-09)
> Revision: 3 (Szenario-Konflikte K1–K8, 2026-11-09) — K1 eingearbeitet (`unmanaged` statt
> `project-state`); K2–K8 geprüft und für dieses Dokument nicht betroffen (§12.1).
> Datum: 2026-11-09
> Klasse: **L** (cross-cutting in einem Subsystem: `sync`-Rendering; ~12 produktive Dateien + Tests; keine neue Subsystem-Grenze, kein Provider-Sonderpfad). **Kein XL**: es entsteht kein neues Modul mit eigenem Lifecycle, und die Änderung ist an genau zwei Konfigurations-/Render-Stellen entschieden (`config.py`, `agent_sync.py`).
> Issue: [#1187 — feat(config): project-context-injection scope (core | +orchestrator | +whitelist | all)](https://github.com/Popoboxxo/agent-meta/issues/1187)
> Autor: `concept-specifier` (Subagent, agent-meta)
> Bezug: Branch `docs/config-wave-plans-1181-1188`, HEAD `aaed14c2`, agent-meta `v2.0.0-beta.8`
> Baseline-Belege: `.tmp/issue-dump/baseline-validate.txt` (PASS, 1 Warnung), `.tmp/issue-dump/baseline-check.txt` (DRY-RUN, Sync-Warnungen)
> spec-id: SPEC-project-context-injection-scope-2026-11-09

Diese Spec beschreibt ausschließlich **was** gelten soll und **welche Verträge** einzuhalten sind. Sie enthält keinen Implementierungscode; die Task-Zerlegung gehört in den Plan.

---

## 1. Problem & Motivation

Aus dem Issue (#1187, Summary):

- `{{PROJECT_CONTEXT}}` wird in **viele** generische Rollen-Templates gerendert; in einem synchronisierten Consumer-Projekt erscheint derselbe Projektabsatz dadurch in fast jedem Agenten-Prompt.
- Die Kontextdatei selbst beansprucht, die **einzige Quelle** zu sein (Zitat im Issue: „Diese Datei ist die **einzige Quelle** für projektspezifischen Kontext — Agenten lesen sie, statt eigenen Kontext zu haben." `CLAUDE.md:3-5`). Beides zusammen ist ein unkontrolliertes Duplikat.
- Kein Config-Key steuert das heute. Jede Änderung der Projektbeschreibung rendert alle betroffenen Templates neu, und jede Delegation trägt eine Kopie eines Textes, der bereits in der Kontextdatei steht.
- Anforderung (Daniel, im Issue zitiert): **heutiges Verhalten bleibt Default**, aber der Scope wird konfigurierbar — nur Kernkontext · plus Orchestrator · plus Whitelist · oder überall.

Das ist **kein Bug** im engeren Sinne (jeder Subagent sieht den Absatz in *seinem* Prompt), sondern eine nicht steuerbare Fan-out-Entscheidung des Generators. #994 (geschlossen) hat dasselbe für Regel-Kanäle gemacht (nur ausliefern, was der Provider tatsächlich liest); #1187 macht es für Projektkontext.

---

## 2. Ist-Zustand (verifiziert am Code, HEAD `aaed14c2`)

### 2.1 Rollen-Templates und Vorkommen

| Prüfung | Ergebnis | Beleg |
|---|---|---|
| `.md`-Dateien in `agents/1-generic/` | **101** | `glob agents/1-generic/*.md` |
| davon Rollen-Templates | **98** (3 Nicht-Rollen: `_README.md`, `_reference-agent.md`, `_wf-orchestrator-reference.md`) | Dateiliste, Underscore-Präfix |
| Dateien mit `{{PROJECT_CONTEXT}}` | **84** (davon **83 Rollen-Templates** + `_reference-agent.md`) | `grep -l`-Ergebnis: 84 Datei-Blöcke |
| Vorkommen insgesamt | **89** (5 zusätzliche Vorkommen in 4 Dateien) | dito |
| Mehrfach-Vorkommen pro Datei | `ui-ux-designer.md` **3×** (Z. 72, 77, 105), `bug-feature-analyzer.md` **2×** (Z. 40, 76), `knowledge-curator.md` **2×** (Z. 22, 55), `knowledge-migrator.md` **2×** (Z. 26, 38) | Datei:Zeile |
| Rollen **ohne** Vorkommen | **15**: `se-architect`, `se-component-requirements`, `se-critic`, `se-developer`, `se-interface-mgr`, `se-junior-developer`, `se-requirements`, `se-senior-developer`, `se-termination`, `se-test-engineer`, `se-testreviewer`, `se-validator`, `se-verifier`, `intern-developer`, `mammouth-expert` | Differenz 98 − 83 |

**Abweichung zum Issue:** Das Issue nennt „70 of 98" (`Verified today`-Tabelle, Stand `v1.2.0-beta.2`, 2026-11-08). Heute sind es **83 von 98** Rollen-Templates (84 von 101 Dateien) — die Zahl ist mit dem Rollen-Wachstum gestiegen. Der Issue-Wert ist damit **veraltet**, die Aussage (unkontrollierter Fan-out) bleibt korrekt.

**Abweichung zum Issue (wichtiger):** Das Issue schreibt „each subagent sees the paragraph once". Das gilt **nicht** für alle Rollen: `ui-ux-designer` rendert den vollständigen Absatz **3×** in einem Prompt, drei weitere Rollen 2×. Das ist eine eigenständige Lücke (siehe §9, Finding F1) und wird durch AC2 (Byte-Identität bei `mode: all`) in diesem Issue **nicht** behoben.

### 2.2 Render-Pfad (wer setzt `{{PROJECT_CONTEXT}}` ein?)

| Glied | Beleg |
|---|---|
| Rollen-Rendering pro Provider | `scripts/lib/agent_sync.py:1409` `sync_agents_for_provider` |
| Schleife über Rollen (Rollenname verfügbar) | `scripts/lib/agent_sync.py:1444` (`for role, source_path in overrides.items()`) |
| Provider-Variablen inkl. `CONTEXT_FILE` | `scripts/lib/agent_sync.py:489-535`, konkret `'CONTEXT_FILE': pc.get('context_file', …)` in `:515` |
| eigentliche Platzhalter-Substitution | `scripts/lib/agent_sync.py:730` `content = substitute(content, merged_vars, rel_source, log)` |
| Conditonal-Strip | `scripts/lib/agent_sync.py:737` |
| Substitutions-Engine | `scripts/lib/variables.py:698` `substitute()`; unbekannte Platzhalter warnen bzw. werfen im `strict`-Pfad |

Das Issue nennt als Render-Stelle `agents/1-generic/_reference-agent.md:74` und als betroffene Datei `scripts/lib/agents.py`. Beides ist **unpräzise**: `_reference-agent.md` ist eine Referenz-Datei, **kein** Parent der 83 Rollen-Templates (jedes Template trägt sein eigenes Literal, z. B. `ui-ux-designer.md:72`, `developer.md:67`, `orchestrator.md:316`). `scripts/lib/agents.py` enthält nur Routing-Renderer (`:421-604`), keine Rollen-Substitution. **Konsequenz für das Design:** ein bedingtes Rendern muss im Renderer (`agent_sync.py`) oder über `{{#if}}`-Konditionale in den Templates passieren — nicht durch Ändern einer einzigen Referenzdatei.

### 2.3 Kontextdatei-Kanal (bleibt unberührt)

`{{PROJECT_CONTEXT}}` wird **auch** in die Provider-Kontextdatei selbst geschrieben; dieser Kanal ist von der Scope-Frage nicht betroffen:

| Stelle | Beleg |
|---|---|
| Continue-Fallback-Block der Kontextdatei | `scripts/lib/context.py:1174-1183`, `:1176` (`variables.get('PROJECT_CONTEXT','')`) |
| Standalone-Rendering (Skills/externe Agenten) | `scripts/lib/standalone.py:57-74`, `:61` (eigener Fallback-Text) |

### 2.4 Provider → Kontextdatei (Datenquelle für den Pointer)

Alle 9 Provider in `config/ai-providers.yaml` deklarieren `context_file`:

| Provider | `context_file` | Beleg |
|---|---|---|
| Claude | `CLAUDE.md` | `config/ai-providers.yaml:2`, `:13` |
| Gemini | `AGENTS.md` | `:135`, `:159` — gelesen wird sie über den von sync gesetzten Settings-Key `context.fileName` (`:164-174`), **nicht** `GEMINI.md` |
| Opencode | `AGENTS.md` | `:252`, `:269` |
| Continue | `.continue/rules/project-context.md` | `:429`, `:435` |
| Copilot | `.github/copilot-instructions.md` | `:515`, `:523` |
| Mammouth | `AGENTS.md` | `:593`, `:606` |
| Codex | `AGENTS.md` | `:712`, `:718` |
| ZCode | `AGENTS.md` | `:802`, `:808` |
| KimiCode | `AGENTS.md` | `:874`, `:890` |

**Abweichung zum Issue:** Der Issue-Text fordert „`GEMINI.md` where applicable". Für Gemini ist die reale Datei `AGENTS.md` (plus `context.fileName`); ein `GEMINI.md`-Pointer wäre ein neuer Dead-Link. Der Pointer muss deshalb **den aufgelösten `context_file`-Wert** nennen, nicht einen Provider-Namen.

### 2.5 Konfiguration heute: kein Key

| Prüfung | Ergebnis | Beleg |
|---|---|---|
| Top-Level-Sektion für den Scope | **existiert nicht** | `grep PROJECT_CONTEXT|project_context` in `config/project-config.schema.json` → nur `:212` (Beschreibung `project.description`) und `:226` (`variables.PROJECT_CONTEXT`) |
| Wurzel-Schema akzeptiert unbekannte Keys | **ja** (`additionalProperties: true`) | `config/project-config.schema.json:2854` (siehe #1141) |
| Content-Quelle | `variables.PROJECT_CONTEXT`, Fallback auf `PROJECT_DESCRIPTION` | `scripts/lib/config.py:1860-1861`; Schema `:226` |
| Schema-Defaults werden beim Sync materialisiert | ja, außer Key steht in `_SYNC_SKIPPED_DEFAULT_KEYS` | `scripts/lib/config.py:183-191`, `:1258-1290`, `:1352-1356` |

### 2.6 Admin-UI-Schreibbarkeit heute

| Prüfung | Ergebnis | Beleg |
|---|---|---|
| Schreib-Whitelist | handgepflegtes `frozenset`, **47** Einträge; `project-context-injection` fehlt naturgemäß | `scripts/admin-server.py:234-259` (Kommentar „Keep in sync …" `:231`) |
| Ablehnung nicht-gelisteter Sektionen | HTTP 400 `section not allowed: …` | `scripts/admin-server.py:5241-5255`, `:5269-5274` |
| Admin-UI schreibt Sektionen über | `PUT /api/config/project/section` | `docs/ui/admin-ui.html:5960-5962` (`saveProjectSection`) |
| Panes sind handgebaut | `context_file`-Pane `:6300-6643`, `auto_commit`-Pane `:7650-7761`; kein `spec-plan`-Pane | `docs/ui/admin-ui.html` |
| `spec-plan-workflow` schreibbar? | **nein** (weiterhin nicht in der Whitelist) — der im Issue genannte Drift besteht weiter | `scripts/admin-server.py:234-259` vs. Schema `:2223` |

### 2.7 Was die Issue-Tabelle sonst behauptet

| Issue-Aussage | Status | Beleg |
|---|---|---|
| „Duplicate lines inside one prompt: 0 — channel gate is exclusive (`sync_pipeline.py:797-811`)" | **nicht mehr zutreffend**: `sync_pipeline.py:797-811` enthält heute `converge_managed_block_context`; die Regel-Kanalwahl liegt in `scripts/lib/rule_channels.py:1-30` + `config/provider-capabilities.yaml` (`rules_read_channels`) | `scripts/lib/sync_pipeline.py:791-806`, `scripts/lib/rule_channels.py:4,28` |
| „bluepencil: 37 of 38 Agenten" | extern, in diesem Repo **nicht** verifizierbar → „laut Issue" | — |
| „Config key controlling this: none" | **bestätigt** | §2.5 |

### 2.8 Baseline (vor der Änderung)

- `python3 scripts/sync.py --validate` → `[PASS] All checks passed.` mit einer `active-set.gate-dropped`-Notiz (`.tmp/issue-dump/baseline-validate.txt:1,8,11`).
- `python3 scripts/sync.py --check` → DRY-RUN, nur bereits existierende Warnungen (`generated-file-drift`, `context.over-soft-cap AGENTS.md: … 16364 chars, soft cap 12000`) (`.tmp/issue-dump/baseline-check.txt:5-7`).

Diese beiden Artefakte sind der Vergleichspunkt für AC2 und AC7.

---

## 3. Soll-Verhalten

### 3.1 Konfigurationsfläche

Top-Level-Sektion `project-context-injection` in `.meta-config/project.yaml`:

```yaml
project-context-injection:
  mode: all                 # all | core+orchestrator | core+whitelist | core
  whitelist: []             # Rollennamen; nur bei mode: core+whitelist ausgewertet
  orchestrator: inherit     # inherit | include | exclude
```

Die vier Modi und ihre Wirkung (Spalte „Kontextdatei" = Kanal aus §2.3, **immer** unverändert):

| `mode` | Kontextdatei | Orchestrator-Rolle(n) | andere Rollen | Wirkung |
|---|---|---|---|---|
| `all` (**Default** = heute) | ja | ja | ja | keine Verhaltensänderung |
| `core+orchestrator` | ja | ja | nein | Orchestrator behält Routingwissen, Worker lesen die Datei |
| `core+whitelist` | ja | gemäß `orchestrator` | nur `whitelist` | gezielte Duplizierung für Rollen, die sie brauchen |
| `core` | ja | nein | nein | minimale Tokens; jede Rolle liest die Kontextdatei bei Bedarf |

**Orchestrator-Achse (`orchestrator`):**

| Wert | `core` | `core+whitelist` | `core+orchestrator` | `all` |
|---|---|---|---|---|
| `inherit` | exkludiert | exkludiert | inkludiert (Default-Verhalten des Modus) | inkludiert |
| `include` | **inkludiert** (wirkt wie `core+orchestrator`) | inkludiert | inkludiert | inkludiert |
| `exclude` | exkludiert | exkludiert | **Validierungsfehler** (Modus verlangt Orchestrator) | **Validierungsfehler** (Modus `all` heißt überall) |

**Lesart der Achse (verbindlich):** `inherit` bedeutet „Modus-Default", **nicht** „inkludieren". Für `core+whitelist` heißt das: `inherit` und `exclude` inkludieren **keine** Orchestrator-Rolle; nur `include` fügt die Orchestrator-Menge zur Whitelist hinzu. `core` + `include` wirkt wie `core+orchestrator`. Für `core+orchestrator`/`all` ist `exclude` ein Fehler (Tabelle oben). Diese Lesart ist die einzige, die mit den Tests in Plan-T5 (`core+whitelist` → Whitelist ∪ Orchestrator-Menge **nur** bei `include`) und mit AC5 übereinstimmt.

**Orchestrator-Rollenmenge:** Rollenname `orchestrator` **plus** jeder für einen aktiven Provider in `providers.<P>.primary-role` genannte Rollenname (dedupliziert). Begründung: `primary-role` ist der reale Einstiegspunkt eines Providers; das Schema beschreibt diese Ableitung selbst (`config/project-config.schema.json:2485`). Provider ohne `primary-role` tragen nur `orchestrator` bei. Die Menge wird **nicht** über Provider-Namen verzweigt.

### 3.2 Pointer-Zeile (Pflicht, damit `core` kein Kontextverlust ist)

Jede Rolle, die den Block **nicht** erhält, bekommt **genau eine** physische Zeile, die die reale Kontextdatei des Providers nennt. Wortlaut (eine Zeile, Englisch wie die Templates):

```
Project context: read `{context_file}` first — it is the single source for project-specific facts (embedded here only when `project-context-injection.mode` includes this role).
```

- `{context_file}` ist der aufgelöste Wert aus `pc["context_file"]` (`scripts/lib/agent_sync.py:515`, Datenquelle `config/ai-providers.yaml`, §2.4). **Kein** `{{CONTEXT_FILE}}` innerhalb des Werts — die Substitution ist einpassig (`scripts/lib/variables.py:698`), verschachtelte Platzhalter würden nicht expandiert.

**Eine** Mechanik (entschieden; ersetzt die frühere, widersprüchliche Formulierung „an der Stelle des Platzhalters"):

1. Der Renderer setzt den Variablenwert `PROJECT_CONTEXT` für die Rolle auf `""` (§5.3 Schritt 3).
2. Nach der Substitution entfernt er die dadurch leer gewordene Label-Zeile `**Project context:**` — nur wenn die Zeile ausschließlich aus diesem Label besteht. Das verhindert eine leere Überschrift in `core` (AC7) und ist **kein** eigenständiger Template-Umbau.
3. Er fügt die Pointer-Zeile als **eine** Zeile am Ende der `<context>`-Sektion ein (vor dem letzten `</context>`).

Fallbacks für Rollen **ohne** Block-Vorkommen (dann entfallen Schritte 1–2):

| Fall | Rollenmenge | Einfügeposition |
|---|---|---|
| `<context>`-Sektion vorhanden | unter den 15 Rollen ohne Platzhalter heute **keine** — Regel gilt für künftige Templates | vor dem letzten `</context>` |
| keine `<context>`, aber `</workflow>` | `intern-developer` | vor dem letzten `</workflow>` |
| weder `<context>` noch `</workflow>` | 13 `se-*`-Rollen (`se-architect`, `se-component-requirements`, `se-critic`, `se-developer`, `se-interface-mgr`, `se-junior-developer`, `se-requirements`, `se-senior-developer`, `se-termination`, `se-test-engineer`, `se-testreviewer`, `se-validator`, `se-verifier`) + `mammouth-expert` | Dateiende; Sync-Log `note` |

- Die **15 Rollen ohne Platzhalter** (§2.1) sind exakt diese Menge: 13 `se-*` + `intern-developer` + `mammouth-expert`. `se-integration-and-test-manager` trägt den Platzhalter (Z. 26) und ist **nicht** Teil der Menge.
- Für die 5 Prosa-Vorkommen gilt eine separate Mechanik (D-3): sie werden auf `{{#if PROJECT_CONTEXT_INJECTED}}…{{else}}{{CONTEXT_FILE}}{{/if}}` umgestellt, damit in `core` der Dateiname statt eines leeren bzw. grammatisch kaputten Satzes steht.
- Damit ist AC3 („exactly one pointer line per role") für **alle** 98 Rollen mechanisch erfüllbar: 83 mit Block-Vorkommen (Label-Cleanup + Append) und 15 ohne Block-Vorkommen (Fallback-Tabelle).

### 3.3 Whitelist-Validierung

| Regel | Verhalten |
|---|---|
| Bekannte Rollennamen | Whitelist-Einträge werden gegen die Rollen-Registry geprüft: `scripts/lib/roles.py:80` `build_role_map` (Quelle `config/role-defaults.yaml`, `ROLES_CONFIG` `:23`) |
| Unbekannter Name | **harter Sync-Fehler** (Exit ≠ 0) mit allen unbekannten Namen in der Meldung — nicht der Warn-Pfad von `role(s) without generic template` (`scripts/lib/sync_pipeline.py:1840-1849`) |
| Whitelist bei anderem Modus | `whitelist` wird bei `mode != core+whitelist` ignoriert, aber **nicht** als Fehler behandelt; Sync-Log `note` „whitelist ignored (mode=…)" |
| Eintrag ohne Platzhalter | Whitelist-Eintrag, dessen Template kein `{{PROJECT_CONTEXT}}` enthält, ist wirkungslos → Konsistenz-**Warnung** (nicht Fehler), siehe §5.4 |
| Duplikate / Nicht-String | Schema-Fehler (`uniqueItems`, `items.type: string`) |

### 3.4 Präzedenz

1. `project-context-injection` in `.meta-config/project.yaml` (Projekt)
2. Schema-Default `mode: all`, `whitelist: []`, `orchestrator: inherit`

Es gibt **bewusst keine** Preset-Ebene (anders als #1186/#1188): der Scope ist ein einzelner Enum plus Liste, ein Preset würde nur eine dritte Auflösungsstufe ohne Nutzen einführen. Ein `--explain`-Analogon ist deshalb nicht Teil dieser Spec.

`variables.PROJECT_CONTEXT` (Inhalt) bleibt die einzige Inhaltsquelle und wird durch diese Sektion **nicht** verändert (Non-Goal, §6).

### 3.5 Reporting / Delta (AC6)

Pro aktivem Provider eine Log-Zeile nach der Rollen-Schleife:

```
project-context-injection: mode=<mode> injected=<n>/<total> roles, pointer=<m>, chars saved=<k> (vs mode=all)
```

- `chars saved` = Summe `len(PROJECT_CONTEXT)` über alle exkludierten Rollen minus Summe `len(pointer_line)` über dieselben Rollen; bei `mode: all` exakt `0`.
- Ausgabe über `log.note("project-context-injection", …)` (bestehende SyncLog-API, vgl. `scripts/lib/sync_pipeline.py:770-776`).
- Zusätzlich `--check`-Ausgabe: dieselbe Zeile, damit die Entscheidung vor dem Schreiben sichtbar ist.

### 3.6 Design-Entscheidungen

```
DECISION D-1  (Render-Ort)
context: 83 Templates tragen den Platzhalter je selbst; es gibt keinen gemeinsamen Parent.
choice: Auflösung im Renderer pro Rolle (agent_sync.py:1444-1462) durch Setzen des Werts von PROJECT_CONTEXT; Template-Text bleibt unverändert.
alternatives: (a) {{#if}} in 83 Templates — 83 Dateien, identisches Ergebnis, hohes Konfliktrisiko mit #1186/#1188; (b) neue Referenzdatei als Parent — existiert nicht, würde die Kompositionslogik (extends) umbauen.
consequences: + ein Codepfad, byte-identische Templates; − die Entscheidung ist im gerenderten Artefakt nicht mehr auf den ersten Blick sichtbar (deshalb D-5-Flags + Log-Zeile).
```

```
DECISION D-2  (Pointer-Mechanik)
context: Ein Satz muss genau einmal pro Rolle erscheinen, ohne 83 Templates anzufassen.
choice: Renderer blankiert das Block-Vorkommen (PROJECT_CONTEXT = ""), entfernt die leer gewordene `**Project context:**`-Label-Zeile und fügt die Pointer-Zeile als eigene Zeile am Ende der <context>-Sektion ein; ohne <context> vor </workflow>, ohne beides am Dateiende + log.note (§3.2).
alternatives: (a) Pointer als Wert von PROJECT_CONTEXT — erzeugt bei ui-ux-designer 3 Pointer-Zeilen und grammatisch kaputte Prosa (Z. 77/105); (b) Pointer nur über {{CONTEXT_FILE}} in Templates — Templates nennen kein Ziel; (c) Pointer exakt an der Platzhalterstelle in der Template-Zeile — hinterlässt das `**Project context:**`-Label als toten Präfix bzw. erzeugt bei Prosa-Vorkommen 5 Pointer-Zeilen.
consequences: + AC3 (genau eine Zeile) ist mechanisch erfüllbar und für alle 15 Rollen ohne Vorkommen definiert; − der Renderer braucht Label-Cleanup + Sektions-Heuristik, die als Fallback dokumentiert und geloggt wird; AC2 bleibt unberührt, weil beide Schritte nur im Nicht-Injiziert-Zweig laufen.
```

```
DECISION D-3  (Prosa-Vorkommen)
context: 5 Vorkommen stehen mitten im Satz (ui-ux-designer.md:77,105; bug-feature-analyzer.md:40; knowledge-curator.md:55; knowledge-migrator.md:38).
choice: Diese 5 Stellen werden auf {{#if PROJECT_CONTEXT_INJECTED}}…{{else}}`{{CONTEXT_FILE}}`{{/if}} umgestellt; im all-Zweig bleibt der gerenderte Text identisch (AC2), im core-Zweig steht der Dateiname statt eines kaputten Satzes.
alternatives: (a) unverändert lassen — in core entstehen grammatisch falsche Sätze („No designs without a `Project context: read CLAUDE.md first …` reference"); (b) Vorkommen ersatzlos streichen — verletzt AC2.
consequences: + AC3 auch für Prosa-Rollen; − 4 Template-Dateien werden angefasst (Konfliktfläche mit #1188: bug-feature-analyzer.md).
```

```
DECISION D-4  (Duplikate nicht in diesem Issue)
context: 4 Rollen rendern den Block mehrfach (bis 3×); AC2 verlangt Byte-Identität bei mode: all.
choice: Duplikat-Bereinigung wird NICHT in #1187 gemacht; sie ist als Finding F1 (§9) erfasst.
alternatives: (a) jetzt bereinigen — bricht AC2 und macht den Golden-Test wertlos.
consequences: + AC2 bleibt scharf; − der Fan-out sinkt in mode: all nicht (nur der Scope wird steuerbar).
```

```
DECISION D-5  (Diagnose-Flags)
context: Tests und Templates müssen „wurde injiziert?" ohne Textvergleich entscheiden können.
choice: Zwei neue Built-in-Variablen PROJECT_CONTEXT_MODE und PROJECT_CONTEXT_INJECTED ("true"/"false"), registriert in scripts/lib/consistency/placeholders.py:12-45.
alternatives: (a) nur Textvergleich im Test — bricht, sobald der Projekttext sich ändert; (b) kein Flag — AC3/AC5 sind nicht sauber testbar.
consequences: + prüfbare Invarianten; − zwei weitere öffentliche Variablennamen (in der Allow-List zu pflegen).
```

---

## 4. Öffentliche Contracts

### 4.1 Schema-Sektion

Datei: `config/project-config.schema.json`, neue Top-Level-Property (Position: bei den übrigen Feature-Sektionen, z. B. neben `context_file`/`context-profile`).

```json
"project-context-injection": {
  "type": "object",
  "description": "Issue #1187: scope of {{PROJECT_CONTEXT}} injection into generated role prompts. 'all' (default) reproduces today's output byte-identically.",
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["all", "core+orchestrator", "core+whitelist", "core"],
      "default": "all"
    },
    "whitelist": {
      "type": "array",
      "items": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$"},
      "uniqueItems": true,
      "default": []
    },
    "orchestrator": {
      "type": "string",
      "enum": ["inherit", "include", "exclude"],
      "default": "inherit"
    }
  },
  "additionalProperties": false
}
```

- `additionalProperties: false` ist Pflicht (Fehler in der Sektion dürfen nicht still durchfallen). `whitelist`/`orchestrator` bleiben auch dann gültig, wenn sie im gewählten Modus wirkungslos sind (§3.3) — sie werden nicht modusabhängig validiert (Draft-07-Enum bleibt einfach prüfbar).
- **Materialisierung (entschärft):** Die Sektion hat **keinen** Default auf Top-Level-Ebene — die Defaults stehen in `properties.mode/whitelist/orchestrator.default` (§4.1), und der einzige Nested-Fill-Zweig behandelt ausschließlich `dod.*` (`scripts/lib/config.py:1379-1389`). Ein normaler `sync.py`-Lauf materialisiert sie deshalb **ohnehin nicht**. Der Eintrag in `_SYNC_SKIPPED_DEFAULT_KEYS` (`scripts/lib/config.py:183-191`) ist ein **reiner Regressionsschutz** für den Fall, dass die Nested-Materialisierung künftig verallgemeinert wird — kein heute wirksamer Fix. `--fill-defaults`/`--init` dürfen die Sektion materialisieren.

### 4.2 Config-Key-Namen (stabil)

| Key | Typ | Default | Bedeutung |
|---|---|---|---|
| `project-context-injection.mode` | enum, 4 Werte | `all` | Scope |
| `project-context-injection.whitelist` | `string[]` | `[]` | Rollennamen (nur `core+whitelist`) |
| `project-context-injection.orchestrator` | enum, 3 Werte | `inherit` | Orchestrator-Achse |

Es werden **keine** weiteren Keys eingeführt (kein `enabled`, kein `preset`, keine per-Rolle-Overrides).

### 4.3 Aufgelöste Variablen (öffentlich für Tests/Templates)

| Variable | Werte | Auflösungsort | Registrierung |
|---|---|---|---|
| `PROJECT_CONTEXT` | Projektabsatz **oder** `""` | `scripts/lib/agent_sync.py:1458-1462` (pro Rolle) | bereits in `placeholders.py:15` |
| `PROJECT_CONTEXT_MODE` | `all` \| `core+orchestrator` \| `core+whitelist` \| `core` | `scripts/lib/config.py` (`build_variables`) | **neu** in `placeholders.py:12-45` |
| `PROJECT_CONTEXT_INJECTED` | `"true"` \| `"false"` | pro Rolle, `agent_sync.py` | **neu** in `placeholders.py:12-45` |
| `CONTEXT_FILE` | Provider-Kontextdatei | bereits vorhanden, `agent_sync.py:515` | bereits in `placeholders.py:38` |

`PROJECT_CONTEXT` behält seinen Namen und seine Position in der Variablen-Map — Templates bleiben unverändert (D-1).

### 4.4 Admin-UI-Schreibbarkeit

| Vertrag | Umsetzung |
|---|---|
| Sektion schreibbar | `"project-context-injection"` in `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py:234-259`) aufnehmen; ohne das antwortet `PUT /api/config/project/section` mit HTTP 400 (`:5241-5255`) |
| Pane | neuer Editor in `docs/ui/admin-ui.html` (Muster: `auto_commit`-Pane `:7650-7761`, Speichern über `saveProjectSection` `:5960-5962`); Felder: Modus-Select, Whitelist (Mehrfachauswahl aus der Rollen-Registry), Orchestrator-Select, read-only Effekt-Vorschau „Rolle → injiziert ja/nein" |
| Round-Trip | GET→PUT der Sektion darf keine anderen Sektionen verändern (bestehender Guard `:5257-5274`) |
| Kein UI-Zwang | Ohne Admin-UI-Pane bleibt der Key in `project.yaml` voll funktionsfähig (AC1 verlangt beides) |

### 4.5 Unveränderte Contracts

| Contract | Zusicherung | Beleg/Absicherung |
|---|---|---|
| A2A-Delegation | `schemas/a2a-handoff.schema.json` wird **nicht** angefasst; der Kontextblock ist kein Bestandteil des Handoffs | Datei existiert; Issue-Requirement 4 |
| Kontextdatei-Inhalt | §2.3-Stellen unverändert; `mode` steuert nur Rollen-Prompts | `context.py:1176`, `standalone.py:61` |
| Template-Kompatibilität | Platzhalter-Name und -Position unverändert; `--validate`-Platzhalterprüfung bleibt grün | `placeholders.py:12-45` |
| Provider-Agnostik | keine `if provider == …`-Zweige; Auflösung ausschließlich über `provider_config[*].context_file` | `agent_sync.py:515` |

---

## 5. Konsistenz- und Fehlerpfade

### 5.1 Harter Sync-Fehler

- unbekannter Whitelist-Rollenname (§3.3) → Meldung enthält alle unbekannten Namen.
- `mode: core+orchestrator` + `orchestrator: exclude`.
- `mode: all` + `orchestrator: exclude`.
- unbekannter `mode`/`orchestrator`-Wert → Schema-Validierung (`scripts/lib/config.py:695` Draft7Validator), sofern `jsonschema` installiert ist; ohne `jsonschema` greift die zusätzliche stdlib-Prüfung im Resolver (gleiche Meldung, damit das Verhalten nicht von einer optionalen Dependency abhängt).

### 5.2 Warnungen (kein Abbruch)

- `whitelist` gesetzt, aber Modus ≠ `core+whitelist`.
- Whitelist-Eintrag ohne `{{PROJECT_CONTEXT}}`-Vorkommen (Wirkungslosigkeit).
- Rolle ohne `<context>`-Sektion, in die der Pointer eingefügt werden müsste (§3.2) → `note`; Rolle ohne `<context>` **und** ohne `</workflow>` (13 `se-*` + `mammouth-expert`) → Pointer am Dateiende plus `note`.

### 5.3 Renderer-Reihenfolge (Invariante)

1. Modus/Whitelist/Orchestrator auflösen (projektweit, einmal).
2. Pro Rolle `PROJECT_CONTEXT_INJECTED` bestimmen (Modus × Whitelist × Orchestrator-Menge).
3. `merged_vars["PROJECT_CONTEXT"]` = Absatz oder `""`.
4. `substitute(...)` (`agent_sync.py:730`) — Konditionale werden **danach** gestrippt (`:737`), deshalb muss der `{{#if PROJECT_CONTEXT_INJECTED}}`-Wert vorher gesetzt sein.
5. Label-Cleanup + Pointer-Zeile: nur wenn `PROJECT_CONTEXT_INJECTED == "false"`. Erst die leer gewordene `**Project context:**`-Zeile entfernen, dann die Pointer-Zeile einfügen (§3.2). Rollen ohne Block-Vorkommen erhalten nur den Pointer über die Fallback-Tabelle (§3.2).
6. Delta-Zähler fortschreiben (§3.5).

### 5.4 Konsistenz-Checks (neue IDs)

| Check-ID | Schwere | Prüfung |
|---|---|---|
| `project-context-injection.pointer-missing` | WARN | Rolle hat `PROJECT_CONTEXT_INJECTED=false`, aber keine Pointer-Zeile im gerenderten Artefakt |
| `project-context-injection.whitelist-no-effect` | WARN | Whitelist-Eintrag ohne Vorkommen, oder Modus ≠ `core+whitelist` |
| `project-context-injection.mode-unknown` | ERROR | unbekannter Modus (Redundanz zur Schema-Prüfung, damit `--validate` auch ohne `jsonschema` hart ist) |

Registrierung im Konsistenz-Lauf: `scripts/consistency-check.py` (Import-Block ab `:42`). Bestehende Checks, die **nicht** erweitert werden: `context.dangling-pointer` (`scripts/lib/consistency/context_budget.py:293-340`) prüft ausschließlich Skill-Pointer — der neue Datei-Pointer wird durch `pointer-missing` abgedeckt, nicht durch eine stille Erweiterung dieses Checks.

---

## 6. Nicht-Ziele

- **Kein** Inhalt: `variables.PROJECT_CONTEXT` und alle Fallbacks (`config.py:1860-1861`) bleiben unverändert.
- **Kein** Per-Rolle-Custom-Text (dafür existieren `agents/3-project/<role>-ext.md`).
- **Keine** rückwirkende Bereinigung bestehender Consumer-Projekte (Re-Sync schreibt neu, es werden keine Dateien umgeschrieben).
- **Kein** Eingriff in den Kontextdatei-Kanal (`context.py:1176`) oder in Standalone-Rendering (`standalone.py:61`).
- **Keine** Preset-Ebene, kein `--explain`, keine Modus-übergreifende Migration.
- **Keine** Duplikat-Bereinigung der 4 Mehrfach-Templates (AC2 blockiert das, siehe D-4/F1).
- **Keine** Änderung an A2A-Schemas, Handoff-Contracts oder Rollen-Tools-Listen.

---

## 7. Akzeptanzkriterien

Wortlaut unverändert aus [#1187](https://github.com/Popoboxxo/agent-meta/issues/1187) (die dortige Inline-Verlinkung auf #1186 ist als `#1186` wiedergegeben):

- [ ] 1. `project-context-injection` is declared in `config/project-config.schema.json` (enum mode, `whitelist[]`, `orchestrator`) and is writable through the Admin UI (add it to `PROJECT_WRITABLE_SECTIONS`, see #1186 for the pre-existing 29-section drift).
- [ ] 2. `mode: all` produces byte-identical output to today for a fixture project (golden test) — the default is a no-op.
- [ ] 3. `mode: core` renders **zero** `{{PROJECT_CONTEXT}}` blocks in role templates and exactly one pointer line per role, naming the provider's real context file.
- [ ] 4. `mode: core+whitelist` renders the block only in whitelisted roles; an unknown name fails the sync with the name in the message.
- [ ] 5. `mode: core+orchestrator` renders it in the orchestrator and nowhere else.
- [ ] 6. The sync log reports the measured token/character delta per mode.
- [ ] 7. A role with `mode: core` still passes the existing prompt-quality checks (no empty required sections).

---

## 8. Risiken & offene Fragen

### 8.1 Risiken

| Risiko | Gegenmaßnahme |
|---|---|
| `core`-Rollen erfinden Projektfakten | Pflicht-Pointer (§3.2) + `pointer-missing`-Check + Test: bei `core` enthält jedes gerenderte Rollen-Artefakt genau eine Pointer-Zeile |
| Prosa-Vorkommen brechen in `core` | D-3: 5 Stellen auf `{{#if}}`-Zweige umgestellt; Test pro betroffener Rolle |
| Golden-Test friert die heutige Doppel-/Dreifach-Renderung ein | bewusst (D-4); F1 adressiert es separat nach AC2-Freigabe |
| Neue Sektion wird beim Sync in `project.yaml` materialisiert | Sektion hat keinen Top-Level-Default; `_SYNC_SKIPPED_DEFAULT_KEYS` ist nur Regressionsschutz (§4.1). Test: `grep -c '^project-context-injection:' .meta-config/project.yaml` == 0 nach einem Plain-Sync — **nicht** Byte-Identität der ganzen Datei (strukturelle Auto-Fills ändern sie ohnehin). |
| 15 Rollen ohne Platzhalter erhalten keinen Pointer | Renderer-Postpass mit dreistufigem Fallback (§3.2): `intern-developer` → vor `</workflow>`, 13 `se-*` + `mammouth-expert` → Dateiende; `pointer-missing` prüft das Ergebnis |
| Konflikt mit der Config-Welle (#1187/#1186/#1188/#1181) auf denselben Dateien | §10 Serialisierung (kanonische Reihenfolge) |
| Admin-UI-Pane wird gebaut, aber Sektion fehlt in der Whitelist → 400 | AC1 koppelt beide; Test über `PUT /api/config/project/section` |

### 8.2 Offene Fragen

| # | Frage | Vorschlag / Eskalation |
|---|---|---|
| OQ-1 | AC3 verlangt „exactly one pointer line per role" — auch für die **15 Rollen ohne Platzhalter**. Soll der Renderer dort wirklich eine Zeile einfügen (Sektions-Heuristik), oder gilt AC3 nur für Rollen mit Block-Vorkommen? | **Aufgelöst (Review 2026-11-09):** AC3 gilt für alle 98 Rollen. §3.2 benennt die 15 Rollen exakt und definiert den dreistufigen Fallback; die frühere „Sektions-Heuristik"-Unschärfe ist damit beseitigt. Verbleibende Auslegung nur noch redaktionell (AC-Wortlaut im Issue nachtragen). |
| OQ-2 | Gehören `providers.<P>.primary-role`-Rollen zur Orchestrator-Achse oder nur die Rolle `orchestrator`? | **Vorschlag:** ja, aufnehmen (§3.1). Ohne das verliert ein Provider mit abweichender `primary-role` in `core` seinen Einstiegspunkt. |
| OQ-3 | Ist `all` + `orchestrator: exclude` ein Fehler oder eine stille Verengung auf „alle außer Orchestrator"? | **Vorschlag:** harter Fehler (§3.1) — ein widersprüchlicher Modus ist die gleiche Fußangel wie ein unbekannter Whitelist-Name. |
| OQ-4 | AC7 nennt „the existing prompt-quality checks (no empty required sections)". Ein Check mit diesem Namen existiert nicht; vorhanden sind Frontmatter-, Platzhalter- und `context.*`-Checks (`scripts/consistency-check.py:42-58`, `placeholders.py:12`, `context_budget.py:293/540`). | **Vorschlag:** AC7 als „`--validate` bleibt grün + `project-context-injection.pointer-missing` = 0" interpretieren. Präzisierung im Issue nachtragen. |
| OQ-5 | Soll der Pointer-Text Englisch sein (wie die Templates) oder Projektsprache? | **Vorschlag:** Englisch, konsistent mit dem restlichen `<context>`-Block; Lokalisierung ist ein separates Thema. |

---

## 9. Backlog-Bugs & Findings

### 9.1 Bestehende Issues

| Nr | Titel (gekürzt) | Einordnung | Begründung |
|---|---|---|---|
| [#1183](https://github.com/Popoboxxo/agent-meta/issues/1183) | `compact`-Profil ersetzt den eingebetteten Regelblock durch die Gate-Karte | nur abhängig | Gleiche Metrik (Kontext-/Token-Budget), aber anderer Kanal (Einstiegsdatei statt Rollen-Prompt) und andere Dateien (`rules/`, `context-anchors.yaml`); keine gemeinsame Änderungsfläche. |
| [#1182](https://github.com/Popoboxxo/agent-meta/issues/1182) | `compact` + `orchestrator.mode: advisory/main-chat` bricht mit `SyncError` ab | nur abhängig | Beide betreffen `orchestrator`-Semantik, aber #1182 ist ein Abbruch im Gate-Card-Builder (`context.py`), nicht im Rollen-Rendering; #1187 darf den Abbruch nicht verschärfen, löst ihn aber nicht. |
| [#1161](https://github.com/Popoboxxo/agent-meta/issues/1161) | Token-Reduktion (route_intent, Agent-Directory, branch-guard, Hook-Kosten) | teilweise | #1187 ist ein zusätzlicher Hebel auf dasselbe Ziel „weniger pro-Spawn-Tokens"; #1161 ändert aber andere Artefakte und enthält keine Scope-Konfiguration. Die Delta-Messung (AC6) sollte dieselbe Zählweise wie die dortigen Messungen verwenden. |
| [#1180](https://github.com/Popoboxxo/agent-meta/issues/1180) | Regeln verweisen auf `docs/concepts/*.md`, die sync nie ausliefert | teilweise | #1187 erzeugt einen **neuen** Datei-Pointer; diese Klasse von Pointer ist heute nicht geprüft (`check_dangling_pointer` nur Skills, `context_budget.py:299-308`). #1180 liefert die `docs/`-Auslieferung und die Pointer-Prüfung — #1187 muss dessen Mechanik wiederverwenden, nicht duplizieren. |
| [#1141](https://github.com/Popoboxxo/agent-meta/issues/1141) | Unbekannte Top-Level-Keys werden still akzeptiert (`additionalProperties: true`) | nur abhängig | Ein Tippfehler im **Sektionsnamen** (`project-context-injectio`) wird nur von #1141 erkannt; #1187 sichert nur die Sektion intern (`additionalProperties: false`) ab. |
| [#1186](https://github.com/Popoboxxo/agent-meta/issues/1186) | Artifact-Locations-Matrix (inkl. „Injection hygiene") | nur abhängig | Erzwingt für #1187 nur die Randbedingung „kein neuer always-on-Block" (dort AC16/AC20) und teilt die Konfliktflächen aus §10; fachlich disjunkt. |

### 9.2 Neue Findings (mit Issue-Zuordnung)

| Finding | Warum relevant | Vorschlag Issue-Titel | Labels | Body-Skizze (3 Bullets) |
|---|---|---|---|---|
| [#1197](https://github.com/Popoboxxo/agent-meta/issues/1197) — `{{PROJECT_CONTEXT}}` wird in 4 Rollen **mehrfach** gerendert (`ui-ux-designer.md:72,77,105`; `bug-feature-analyzer.md:40,76`; `knowledge-curator.md:22,55`; `knowledge-migrator.md:26,38`) — 3× bzw. 2× derselbe Absatz in **einem** Prompt, an 5 Stellen mitten im Satz | Das Issue geht von „einmal pro Prompt" aus; #1187 kann das wegen AC2 (Byte-Identität) nicht mitbeheben, und `mode: core` würde die Prosa-Stellen ohne eigenen Umbau grammatisch zerlegen | `bug(templates): {{PROJECT_CONTEXT}} 2–3× pro Rollen-Prompt (ui-ux-designer 3×)` | `bug`, `context-engineering`, `agents`, `P2` | • Ist: 89 Vorkommen in 84 Dateien, 4 Dateien mit Mehrfach-Vorkommen (Belege: `ui-ux-designer.md:72/77/105`, `bug-feature-analyzer.md:40/76`, `knowledge-curator.md:22/55`, `knowledge-migrator.md:26/38`).<br>• Wirkung: identischer Projektabsatz mehrfach im selben Prompt, Prosa-Sätze wie „No designs without a `…` reference" werden in `mode: core` ungrammatisch.<br>• Soll: genau ein Block-Vorkommen pro Rolle; Prosa-Stellen referenzieren `{{CONTEXT_FILE}}`; Regressionstest zählt Vorkommen pro gerendertem Rollen-Artefakt. |

**Keine weiteren Findings.** Geprüft und verworfen: (a) fehlende Konsistenzprüfung für Datei-Pointer → in #1187 als `pointer-missing` in-scope; (b) `PROJECT_WRITABLE_SECTIONS`-Drift → bereits #1186/#1141; (c) fehlende Token-Zählung → in #1187 AC6 in-scope; (d) veraltete Zeilennummern im Issue-Text → redaktionell, kein Issue.

---

## 10. Cross-Issue-Konfliktflächen

**Kanonische Ausführungsreihenfolge (verbindlich):**

```
#1187 → #1186 → #1188 → #1181 → #1141 (Wurzel-Striktheit) → Whitelist-Ableitung aus dem Schema (eigenes Follow-up)
```

Begründung: #1187 ist der kleinste Eingriff und setzt die Rollen-Schleife neu auf, auf der #1186/#1188/#1181 aufsetzen; #1186 baut die Datenstruktur (Artifact-Locations, `ARTIFACT_*`); #1188 bringt eigene Module und Panes; #1181 setzt die Render-Pipeline fort und teilt `agent_sync.py`/`admin-ui.html`; #1141 (`additionalProperties: false` an der Wurzel) kommt **nach** allen neuen Sektionen, sonst validiert keine davon; die Whitelist-Ableitung aus dem Schema setzt **alle** Sektionen voraus und ist deshalb das letzte Follow-up (nicht mehr Teil von #1186).

| Datei | #1187 | #1186 | #1188 | #1181 | Konfliktnatur | Serialisierungsbedarf |
|---|---|---|---|---|---|---|
| `config/project-config.schema.json` | neue Top-Level-Sektion + `additionalProperties: false` | neue Top-Level-Sektion `artifact-locations` + 9 SE-Klassen | neue Top-Level-Sektion `issue-conventions` | neuer Key **`auto_commit.authority_overrides`** (nested in `auto_commit.properties`, **nicht** Top-Level) | drei Top-Level-Einfügungen plus eine Nested-Erweiterung an derselben Datei; Zeilennummern aller Folgeänderungen verschieben sich | **hoch** — Reihenfolge #1187 → #1186 → #1188 → #1181; #1141 (Wurzel-`additionalProperties: false`) erst danach |
| `scripts/lib/config.py` | Resolver + `PROJECT_CONTEXT_MODE` + `_SYNC_SKIPPED_DEFAULT_KEYS` | Matrix-Resolver + `ARTIFACT_*` | Taxonomie-Resolver (neues Modul) | Rollen-Authority (`auto_commit.py`, `_build_core_variables` `:1792-1848`) | vier Änderungen im selben `build_variables`-Umfeld; Konflikt in Importen/Reihenfolge | mittel — #1187 zuerst (klein), dann die großen Resolver |
| `scripts/admin-server.py` | ein Eintrag in `PROJECT_WRITABLE_SECTIONS` | ein Eintrag + Endpoint | ein Eintrag + eigener Guard | kein UI-Anteil (`auto_commit` bereits gelistet, `:252`) | dieselbe handgepflegte `frozenset` (`:234-259`), drei Autoren | mittel — nacheinander; die Ableitung aus dem Schema ist ein **eigenes Follow-up nach #1141** |
| `docs/ui/admin-ui.html` | neues Pane | neues Pane „Artifacts" | neues Pane „Labels" | ändert `viewProjectAutoCommit` (`:7639-7766`) | vier Panes in einer handgebauten 1-Datei-UI; gemeinsame Helper (`saveProjectSection`, `:5960`) | **hoch** — Panes nacheinander: #1187 → #1186 → #1188 → #1181 |
| `scripts/lib/agent_sync.py` | pro-Rolle-Injektion + Pointer + Delta-Zähler | keine | `_apply_role_issue_convention_overrides()` (Aufruf neben `:1459`) | per-Role-`auto_commit`-Overlay (`:1459`) + `_finalize_agent_content` (`:935`) | **#1187, #1188 und #1181 ändern dieselbe Rollen-Schleife** (`:1444-1468`); die frühere Aussage „nur #1187 ändert die Rollen-Schleife" war falsch, und #1186 fasst die Datei nicht an | **hoch** — seriell über die kanonische Reihenfolge |
| `scripts/lib/sync_pipeline.py` | keine Task (kein Edit) | Scaffold-Aufruf (`:1699`) + neue Stage 14c „resolved.json" nach `:1615` | keine | Umbau Stage 14 (`:1893-1924`, T9) | #1186 hängt eine neue Stage direkt hinter die von #1181 umgebaute Stage 14; #1187 fasst die Datei nicht an | mittel — nur #1186/#1181; #1187 serialisiert hier nichts |
| `scripts/lib/variables.py` | `PROJECT_CONTEXT_INJECTED` in die Conditional-Whitelist (`:570-598`) | keine (nur Hotspot, kein Edit) | keine | keine | dieselbe `strip_inactive_conditional_blocks`-Sammelzeile | niedrig (additiv), aber gleiche Datei — seriell |
| `scripts/lib/standalone.py` | Fallback-Flags `PROJECT_CONTEXT_INJECTED`/`PROJECT_CONTEXT_MODE` (`:150-204`) | keine | keine | keine | dieselbe Fallback-Dict-Region | niedrig (additiv), aber gleiche Datei — seriell |
| `tests/scenarios/registry.md` | Szenarien `95`–`98` | Szenario `99` | keine | Szenario `94` reserviert | gemeinsame Nummerierung + `tests/scenarios/asserts/*` | **hoch** — IDs vorab vergeben: `94` = #1181, `95`–`98` = #1187, `99` = #1186 |
| `templates/configs/project.yaml.example` **und** `howto/configs/project.yaml.example` | `project-context-injection`-Block | `artifact-locations`-Block | `issue-conventions`-Block | `auto_commit.authority_overrides`-Block | **zwei existierende Beispiel-Dateien mit derselben Sektion**; eine Änderung ohne die andere lässt die Doku divergieren | mittel — beide Dateien je Welle parallel pflegen |
| `scripts/lib/consistency/placeholders.py` | 2 neue Variablen | neue `ARTIFACT_*` | neue `ISSUE_*` | keine | dieselbe Allow-List, drei Autoren | niedrig (additiv), aber gleiche Datei |
| `agents/1-generic/bug-feature-analyzer.md` | D-3: Zeile 40 auf `{{#if}}` | — | Label-Tabelle (§ „label schema", `:81`) | — | **echter Zeilenkonflikt** in derselben Datei | mittel — kanonisch #1187 vor #1188, nicht parallel |
| `agents/1-generic/*.md` (breit) | 4 Dateien | 18 Dateien | 4 Dateien | 0 | mehrere Template-Wellen; `feedback`/`meta-feedback` (#1188) überschneiden sich nicht mit #1187 | mittel — Wellen seriell in kanonischer Reihenfolge, jede mit eigenem Golden |
| `config/ai-providers.yaml` | **nur lesend** (`context_file`) | nur lesend | nur lesend | nur lesend | keine | keiner |
| `docs/issue-labels.md` | — | klassifiziert als `project-docs.files.issue-labels` (T1) | **erzeugt** (T25, generierte Doku) | — | neue generierte Datei, deren Pfad #1186 als Klassen-Ziel deklariert; #1187 hat keine Task | niedrig — #1186 deklariert den Pfad, #1188 erzeugt die Datei (Reihenfolge #1186 → #1188) |
| `.meta-config/issue-labels-state.json` | — | klassifiziert als **`unmanaged`** (Negativ-Deklaration, K1) | **erzeugt** (persistiertes Prune-Manifest, T17/T21) | — | persistierter Zustand; ohne Deklaration meldet der Managed-Tree-Hook ihn als unbekannt | niedrig — #1186 führt ihn in `unmanaged[]`, #1188 schreibt |
| `schemas/a2a-handoff.schema.json` | **nicht angefasst** | nicht angefasst | nicht angefasst | nicht angefasst | keine | keiner |

**Querschnittsnotiz (#1188 → #1186):** `docs/issue-labels.md` (generiert, T25) und `.meta-config/issue-labels-state.json` (persistiertes Prune-Manifest, T17/T21) entstehen in #1188. #1186 muss **beide** Pfade klassifizieren — `docs/issue-labels.md` als `project-docs.files.issue-labels`, das Manifest als **`unmanaged`** (Negativ-Deklaration, keine Klasse; K1: die frühere Kategorie `project-state` ist gestrichen) —, damit die Artifact-Locations-Matrix sie abdeckt. Das ist **keine Task in #1187** — hier nur als Schnittstellenanforderung an #1186 notiert, weil #1187 die Matrix in §7/§10 referenziert.

---

## 11. Traceability

| AC | Spec-Abschnitt | Absicherung |
|---|---|---|
| AC1 (Schema + Admin-UI-Schreibbarkeit) | §4.1, §4.2, §4.4 | Schema-Test (valide/invalide), `PUT /api/config/project/section`-Round-Trip, Assertion `"project-context-injection" in PROJECT_WRITABLE_SECTIONS` |
| AC2 (`all` byte-identisch) | §3.1, §3.6 D-1/D-4, §6 | Golden-Test Fixture-Projekt: Diff der gerenderten Agenten = leer; zusätzlich „Sektion wird nicht materialisiert" (`grep -c '^project-context-injection:' .meta-config/project.yaml` == 0, §4.1 — im Szenario **Lauf A**, nicht Lauf B; **nicht** Byte-Identität der ganzen Datei, weil strukturelle Auto-Fills sie ändern) |
| AC3 (`core`: 0 Blöcke, 1 Pointer, reale Datei) | §3.2, §5.3, §8.2 OQ-1 | Test pro Provider: Pointer enthält den `context_file`-Wert aus `ai-providers.yaml`; Zählung `PROJECT_CONTEXT_INJECTED=false` + genau eine Pointer-Zeile pro Rollen-Artefakt (83 mit Block, 15 über Fallback: `intern-developer` → `</workflow>`, 13 `se-*` + `mammouth-expert` → Dateiende); `pointer-missing` = 0 |
| AC4 (`core+whitelist`, unbekannter Name = Fehler) | §3.3, §5.1 | Unit-Test: unbekannter Name → Sync-Abbruch mit Namen in der Meldung; bekannter Name → Block nur dort |
| AC5 (`core+orchestrator`) | §3.1 (Orchestrator-Achse), §3.2 | Test: Block in `orchestrator` (+ `primary-role`-Rollen), in keiner anderen Rolle |
| AC6 (Delta im Sync-Log) | §3.5 | Test: Log-Zeile `project-context-injection: mode=… injected=n/total chars saved=k`; bei `all` ist `k == 0` |
| AC7 (Prompt-Qualität bei `core`) | §5.4, §8.2 OQ-4 | `sync.py --validate` bleibt grün; `pointer-missing` = 0; Frontmatter-/Platzhalter-Checks unverändert grün |
| Issue-Requirement „Default bleibt `all`" | §3.1, §4.1 | Schema-Default `all` + Golden-Test AC2 |
| Issue-Requirement „Delegation-Contract unverändert" | §4.5 | `schemas/a2a-handoff.schema.json` unverändert — Diff gegen den eingefrorenen Basis-Hash `git diff --name-only aaed14c2..HEAD -- schemas/a2a-handoff.schema.json` ist leer (nicht `HEAD`, sonst nach dem Commit vakuum-grün) |
| Issue-Requirement „Provider-aware Pointer" | §2.4, §3.2 | Test über alle 9 Provider in `config/ai-providers.yaml`; Gemini-Fall explizit (`AGENTS.md`, nicht `GEMINI.md`) |

---

## 12. Review-Auflösung (2026-11-09)

Alle Befunde aus dem Review vom 2026-11-09 sind eingearbeitet. Status bleibt `DRAFT`; Revision 2.

| Befund-ID | Änderung | Betroffene Stelle |
|---|---|---|
| **BLOCKER** (Validator, `plan:195`) | Matrix-Lesart verbindlich: `core+whitelist` + `inherit`/`exclude` inkludiert **keine** Orchestrator-Rolle; nur `include` fügt die Orchestrator-Menge hinzu. Plan-T5-Testbullet und T8-Erwartung entsprechend korrigiert. | Spec §3.1 (neuer Lesart-Absatz), §11 AC5; Plan T5, T8 |
| **RVW-1187-01** (MAJOR) | M1-Gate erwartete die erst in T7 (M2) implementierte Logzeile. Log-Assertion aus M1 entfernt und in M2 verschoben. | Plan §3 M1/M2-Gates |
| **RVW-1187-02** (MAJOR) | **Eine** Pointer-Mechanik festgelegt: Block blankieren → leere `**Project context:**`-Zeile entfernen → Pointer als **eine** Zeile vor dem letzten `</context>` einfügen (Fallbacks vor `</workflow>` bzw. Dateiende). Die widersprüchliche Formulierung „an der Stelle des Platzhalters" ist ersatzlos gestrichen. | Spec §3.2, §3.6 D-2, §5.3 Schritt 5, §5.2; Plan T6, §5.3 |
| **RVW-1187-03** (MAJOR) | AC3-Rollenmenge exakt benannt: 15 Rollen ohne Platzhalter = 13 `se-*` + `intern-developer` + `mammouth-expert` (`se-integration-and-test-manager` trägt den Platzhalter und gehört **nicht** dazu). Dreistufiger Fallback dokumentiert; `intern-developer` → `</workflow>`, 13 `se-*` + `mammouth-expert` → Dateiende. | Spec §3.2 (Tabelle), §5.2, §8.1, §11 AC3; Plan T6, OQ-7 |
| **RVW-1187-04** (MAJOR) | Negativ-Assertions über `git diff --name-only HEAD` (nach Commit vakuum-grün) ersetzt durch `git diff --name-only aaed14c2..HEAD -- <pfad>` (eingefrorener Basis-Hash). | Plan T10, T15, §9; Spec §11 (Delegation-Contract-Zeile) |
| **RVW-1187-05** (MINOR) | „`project.yaml` byte-identisch" ist mit Minimal-Fixture falsch (strukturelle Auto-Fills). Assertion auf `grep -c '^project-context-injection:' == 0` verengt (ursprünglich Plan T15 Schritt 8; mit RVW2-1187-02 nach Schritt 2 / Lauf A verschoben). | Plan T15, §7; Spec §4.1, §8.1, §11 AC2 |
| **RVW-1187-06** (MINOR) | `_SYNC_SKIPPED_DEFAULT_KEYS`-Begründung entschärft: Sektion hat keinen Top-Level-Default, Nested-Fill behandelt nur `dod.*`; Eintrag ist reiner Regressionsschutz, kein heute wirksamer Fix. | Spec §4.1; Plan T2 |
| **Validator-WARN** (`spec:433`) | Falscher #1181-Key korrigiert: `auto_commit.authority_overrides` (nested), nicht `commit-authority-overrides`/`tools-overrides`. | Spec §10 (Schema-Zeile) |
| **NIT** | T9 sprach von „5 Block-Vorkommen" und listete vier — auf „4 Block-Vorkommen" korrigiert. | Plan T9 |
| Querschnitt: Reihenfolge | Kanonische Reihenfolge `#1187 → #1186 → #1188 → #1181`, dann `#1141`, dann Whitelist-Ableitung (eigenes Follow-up) ersetzt die widersprüchliche #1141-Aussage. | Spec §10; Plan §8, §2 |
| Querschnitt: Konfliktmatrix | Falsche Aussage „nur #1187 ändert die Rollen-Schleife" entfernt; verbindliche Zielmatrix: `agent_sync.py` → #1187/#1188/#1181; `sync_pipeline.py` → #1186/#1181 (#1187 ohne Task); `variables.py`/`standalone.py` → nur #1187 (#1186 nur Hotspot, kein Edit); `tests/scenarios/registry.md` → #1181/#1187/#1186; beide `project.yaml.example` → alle vier; `docs/issue-labels.md` und `.meta-config/issue-labels-state.json` → #1188 erzeugt, #1186 klassifiziert. | Spec §10; Plan §2, §8 |
| Querschnitt: Szenario-IDs | `94` für #1181 reserviert, `95`–`98` für #1187, `99` für #1186. | Plan T15, §6 |
| Querschnitt: `docs/issue-labels.md` / `.meta-config/issue-labels-state.json` | Beide von #1188 erzeugt; in #1186 zu klassifizieren (`project-docs.files.issue-labels` bzw. **`unmanaged`**, K1 — `project-state` ist gestrichen) — Querschnittsnotiz, keine Task in #1187. | Spec §10 (Notiz) |
| Finding #1197 | Mehrfach-Rendering-Finding ist jetzt #1197 und wird dort zitiert (statt „Nummer wird nachgetragen"). | Spec §9.2; Plan §11 |
| **RVW2-1187-01** (MAJOR) | Plan-Lauf F prüfte `mode: core` + `orchestrator: exclude` als Fehler, obwohl §3.1 (`:151`) das erlaubt (exkludiert). Lauf F im Plan auf `core+orchestrator`/`all` + `exclude` umgestellt und an `test_scope_core_orchestrator_plus_exclude_is_error`/`test_scope_all_plus_exclude_is_error` gekoppelt; `core` + `exclude` ist gültig. | Spec §3.1 (bestätigt); Plan T15 Schritt 7 |
| **RVW2-1187-02** (MINOR) | Materialisierungs-Assertion im Plan von Lauf B auf Lauf A verschoben — Lauf B setzt die Sektion selbst. | Plan T15 Schritte 2/8; Spec §11 AC2 |
| **RVW2-X-01** (MAJOR) | Konfliktmatrix in §10 und Plan §2 auf die verbindliche Zielmatrix gezogen (siehe Zeile „Querschnitt: Konfliktmatrix"); neue Matrix-Zeilen für `sync_pipeline.py`, `docs/issue-labels.md` und `.meta-config/issue-labels-state.json`. | Spec §10; Plan §2 |

### 12.1 Szenario-Konflikte K1–K8 (2026-11-09)

Auflösung der acht Befunde aus `.tmp/scenario-config-wave/RESULT.md`, konsistent über alle vier
Wave-Specs/-Pläne. Status bleibt `DRAFT`.

| Befund | Änderung | Stelle |
|---|---|---|
| **K1** (BLOCKER) | `.meta-config/issue-labels-state.json` heißt **`unmanaged`** (Negativ-Deklaration), nicht `project-state`; `classes` bleibt 23 | §10 (Matrix-Zeile), §10 (Querschnittsnotiz), §12 (Querschnitt-Zeile) |
| **K2** | **Nicht betroffen**: #1187 deklariert keinen Label-Separator | geprüft: §4.2 |
| **K3** | **Nicht betroffen**: #1187 hat bewusst **keine** Preset-Ebene (§3.4); es gibt keine Stufenkollision | geprüft: §3.4 |
| **K4** | **Nicht betroffen**: keine `taxonomyAxis` | geprüft: §4.1 |
| **K5** | **Nicht betroffen**: keine Grant-Präzedenztabelle | geprüft: §3.4 |
| **K6** | **Nicht betroffen**: die Schema-Sektion nutzt keine `$defs` | geprüft: §4.1 |
| **K7** | **Nicht betroffen**: neue Top-Level-Sektion `project-context-injection` bleibt kebab-case; kein snake_case-Bestandsblock berührt | geprüft: §4.1 |
| **K8** | **Nicht betroffen**: kein `_KEYS`-Block | geprüft: §4.1 |
