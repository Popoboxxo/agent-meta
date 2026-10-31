---
spec-id: SPEC-RELEASE-CHECKLIST-2026-10-31
title: Strukturierte Release-Checkliste (off|advisory|strict) mit Dry-Check
status: APPROVED
revision: 1.2
klasse: L (Bounded, mit Review-Loop) — zusätzlich Architectural-Kriterium F7 (neuer öffentlicher Config-Contract + Schema)
related-spec: SPEC-TEST-ENVIRONMENTS-2026-10-31
quellen: .tmp/recon-release.md (Datei:Zeile-Belege dort), .tmp/spec-builder-check.md (Builder-Check, eingearbeitet in rev 1.1); Belege gegen den Code stichprobenartig verifiziert, siehe §16
---

# Strukturierte Release-Checkliste — Spec

> Status: APPROVED (2026-10-31, Freigabe durch Nutzer). Der Approval-Marker `Status: APPROVED` wird
> ausschließlich vom Nutzer bzw. `concept-reviewer` gesetzt, nie vom Autor. Diese Datei enthält
> Interface-Contracts und Akzeptanzkriterien, keine Implementierung und keinen Plan.
> Trace-Anker: `spec-id: SPEC-RELEASE-CHECKLIST-2026-10-31`.
>
> Reihenfolge der beiden Specs: **1 = diese Spec (Release-Checkliste)**, 2 = Test-Umgebungen
> (`docs/specs/2026-10-31-test-environments-spec.md`). Spec 2 verweist nur dort auf diese Spec, wo es
> Berührungspunkte gibt (§13 dort).
>
> Markierung: **[Nutzer]** / **Entscheidung des Nutzers** = Entscheidung des Nutzers (unverändert bzw. aus dem Builder-Check übernommen).
> **[Call des Autors]** = Vorschlag des Autors, begründet, im Review zu bestätigen oder zu verwerfen (Sammelliste in §18/§21).
> **Call des Autors (Builder-Check)** = Minor-Entscheidung aus `.tmp/spec-builder-check.md` (Stapel b), vom Autor übernommen.

## Änderungshistorie

| Revision | Datum | Änderung |
|---|---|---|
| 1.0 | 2026-10-31 | Erstentwurf. |
| 1.1 | 2026-10-31 | Builder-Check eingearbeitet: Entscheidungen des Nutzers C-1 (Default-Items in Vorbedingung/Schritt, Feld `phase`), C-2 (Gates in jedem Modus hart), C-5 (Freigabeprotokoll `APPROVAL_REQUEST`/`APPROVED`); Minor-Calls b1-b11, b22; Korrekturen a1-a4, a7, a10, a11, a17; neuer Section-Guard im Admin-Server; Folge-Optionen und Aufwand aktualisiert. Status bleibt DRAFT. |
| 1.2 | 2026-10-31 | OF-7 entschieden (Entscheidung des Nutzers U10): In `strict` dürfen die Default-Punkte `dod-met` und `readme-current` mit einzeiliger Begründung `n/a` sein (`na-allowed-with-reason`); neues AC-REL-25; OF-7 entfernt, OF-8 als „für den Implementierer" gekennzeichnet. Status bleibt DRAFT. |
| 1.2 | 2026-10-31 | rev 1.2 — Status APPROVED (Freigabe durch Nutzer, 2026-10-31) |

## 1. Intent / Why

Die Release-Checkliste ist heute hartkodierte Prosa in `agents/1-generic/release.md` (Default-Items Z.58-64, Checklisten-Abschnitt ab Z.52).
Projekte können nur Textzeilen anhängen (`conventions.release.custom_checklist`, nur Prosa, vom Agenten bewertet). Es gibt:

- keinen Modus (Gate-Fehler blockieren immer, sobald der Hook läuft; ob er läuft, entscheidet der Agent),
- keine einheitliche Punktdefinition (Prosa-Tabelle, Custom-Zeilen und Gate-Skripte sind getrennte Welten),
- keinen mechanischen Punkt in `project.yaml` (Skript + Exit-Code) ohne Hook-Datei, Allowlist und Checksumme,
- kein Ergebnisformat für die Agenten-Bewertung,
- keine Unterscheidung zwischen Vorbedingungen (vor dem Release prüfbar) und Release-Schritten (erst nach Ausführung bestätigbar),
- keine Möglichkeit, die Release-Fähigkeit zu prüfen, ohne ein Release zu bauen.

Ziel: Projekte steuern pro Projekt, wie verbindlich die Checkliste ist, und können eigene Punkte
(agentenbewertet oder per Skript) deklarativ ergänzen; ein Dry-Check beantwortet „wäre ein Release jetzt möglich?"
ohne Tag, Push, Build oder Version-Bump.

## 2. Ziele

- Z1: Neuer optionaler Top-Level-Block `release-checklist` in `project.yaml` mit Modus `off|advisory|strict` **[Nutzer]**.
- Z2: Punkte sind wahlweise mechanisch (Skript, Exit-Code) oder agentenbewertet **[Nutzer]**.
- Z3: Dry-Check-Modus „Release-Fähigkeit prüfen ohne zu bauen" **[Nutzer]**.
- Z4: Einheitliches Ergebnisformat der Bewertung (Tabelle im Return des Release-Agenten), inkl. Phase (Vorbedingung/Schritt).
- Z5: `agent-meta-manager` kann Modus und Punkte einrichten **[Nutzer]**.
- Z6: Admin-UI bietet dieselben Settings (Parität mit CLI/Manager) **[Nutzer]**.
- Z7: Default `off` lässt alle generierten Templates **byte-identisch** (Migration-Invariante).
- Z8: Einheitliches Freigabeprotokoll (`APPROVAL_REQUEST`/`APPROVED`) vor der ersten Mutation **[Entscheidung des Nutzers, C-5]**.

## 3. Nicht-Ziele

- NZ1: Kein harter Hook/Gate-Skript-Block für `strict` im MVP **[Nutzer]**; als Folge-Option in §15 dokumentiert.
- NZ2: Kein neues Gate-Plugin-System (Allowlist/Checksummen von `pre-release-check.sh` bleiben unverändert).
- NZ3: Keine Änderung der Semantik von `release-gates:` **und keine Aufweichung der Gates durch den Modus**: Schritt 0 (`pre-release-check.sh`, Exit≠0 ⇒ `STATUS: failed`) bleibt in **jedem** Modus (off/advisory/strict) hart wie heute **[Entscheidung des Nutzers, C-2]**. Der Modus wirkt nur auf Checklistenpunkte.
- NZ4: Kein Release-Auslöser/CI-Integration, kein automatisches Release.
- NZ5: Kein `sync.py --release-check` im MVP (nur als spätere Option notiert).
- NZ6: Kein Schema↔UI-Coverage-Test für alle Schema-Keys (bekannte Lücke, eigenes Thema).
- NZ7: Keine Änderung an `auto-github-release.sh` / `conventions.release.github_release`.

## 4. Anti-Ziele (Misserfolg trotz Funktion)

- AZ1: Ein Projekt ohne `release-checklist`-Block erhält nach dem Sync auch nur ein geändertes Byte in generierten Agenten/Rules (Migration-Invariante verletzt).
- AZ2: `strict` wird als Sicherheitsgarantie missverstanden. Es ist **nur Prompt-/Konventions-Boundary** (Terminologie: `.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`); Doku und Agent-Prosa dürfen keine harte Durchsetzung suggerieren.
- AZ3: `advisory` blockiert unbemerkt, oder `strict` lässt einen Fail stillschweigend durch (Agent schreibt „done" trotz Nicht-Pass).
- AZ4: Der Dry-Check verändert Zustand (Tag, Push, Build, Version-Bump, CHANGELOG-Edit, Commit).
- AZ5: Skript-Punkte öffnen eine Befehlsinjektions-Fläche über `project.yaml` ohne jeden Hinweis (siehe R3).
- AZ6: Admin-UI und `project.yaml` driften auseinander (zwei Wahrheiten).
- AZ7: YAML-1.1-Falle: `mode: off` wird als Bool `False` geladen und der Modus „verschwindet" oder wirft.
- AZ8: `strict` scheitert systematisch an Release-Schritten (`version-bumped`, `build-created`), weil sie vor ihrer Ausführung bewertet würden (Logikbruch, behoben durch C-1).
- AZ9: Der Worker führt eine Mutation (Bump, CHANGELOG-Edit, Tag, Push) aus, bevor die Freigabe vorliegt, obwohl ein Nicht-Pass vorliegt.

## 5. Constraints

- C1: Python-Stdlib only; Python >= 3.9 (kein `X | Y`-Typsyntax zur Laufzeit ohne `from __future__ import annotations`, keine `match`).
- C2: Provider-Agnostik: Unterschiede nur über Config-Keys/Capability-Flags, nie `if provider == "Name"` (Skill `provider-agnostic`). Der Release-Agent-Text ist provider-neutral (kein hartkodierter Hook-Pfad außer dem bereits vorhandenen Beispiel).
- C3: Default `off` ⇒ generierte Templates byte-identisch (Test analog `tests/test_conventions_migration_invariant.py`).
- C4: **Neue** lib-Module <= 600 Zeilen. `scripts/lib/config.py` hat bereits 2466 Zeilen (`variables.py` 796, `standalone.py` 537): Logik gehört in das eigene Modul `scripts/lib/release_checklist.py`; bestehende Module bekommen nur Aufrufzeilen/Registrierungseinträge.
- C5: Neue Platzhalter nur mit Registrierung nach Regel `rules/2-platform/agent-meta-conventions.md:105-109` (config.py `build_variables()`-Pfad: `_SET`-Muster `config.py:1442`, Convention-Blöcke `_build_convention_variables` `config.py:2293`), Eintrag in `scripts/lib/consistency/placeholders.py` und Doku in `docs/guides/features/sync-concept.md` (Tabelle „Auto-injiziert", ~:280). Eine Variablentabelle in `CLAUDE.md` existiert nicht.
- C6: YAML-1.1 `off`/`on` → Bool: ein eigener Normalizer in `release_checklist.py` bildet **nur** `False`→`"off"` ab; `True` bleibt unverändert und der Validator meldet „quote the value". Vorbild nur strukturell: `_normalize_subagent_permissions_mode` (`config.py:346-364`) macht dagegen **jeden** Bool zu `"off"` — nicht 1:1 übernehmen. Resolver-Vorbild: `variables.py:366-400`. Admin-UI-Hinweis `docs/ui/admin-ui.html` ~:7467.
- C7: Lese-Resolver beenden nie den Prozess; harte Validierung nur im Config-Load und im Python-Validator (Muster `config.py:674`). Die JSON-Schema-Validierung warnt nur und läuft nur, wenn `jsonschema` installiert ist (`config.py:388-434`): **harte Fehler stehen ausschließlich im Python-Validator**, das Schema ist Zusatz (Autocomplete, Warnung).
- C8: Sprache: Spec/Doku Deutsch; Code, Identifier, Commit-Messages Englisch.
- C9: Kein Top-Level-`default` im Schema für `release-checklist` (würde von `--fill-defaults` in `project.yaml` geschrieben, `config.py:1060-1069`, Issue #1074); verschachtelte Defaults im Schema sind reine Dokumentation und werden nicht geschrieben.

## 6. Ansätze

### A (gewählt): Eigener Top-Level-Block `release-checklist` + Modus-Muster von `subagent_permissions`

Neuer Block mit `mode` und `items`; Default-Items bleiben im Template, `items` erweitern sie; Auswertung durch den
Release-Agenten per Prosa-Block (kein neuer Laufzeit-Code im Agenten); Resolver/Schema/UI folgen dem etablierten Muster.
Vorteil: schema-validierbar, UI-fähig, plattformunabhängig, geringe Code-Fläche, bekannter Muster-Pfad.

### B (verworfen): Konfiguration in `platform-config` (`.claude/platform-config.yaml`) / `conventions.release.custom_checklist` erweitern

Verworfen: `platform-config` hat **kein Schema** (nur Laufzeit-Warnungen) und ist plattformgebunden; Modus und Punktstruktur
wären weder validierbar noch in der Admin-UI schemagetrieben editierbar. `custom_checklist` kennt weder Modus noch
mechanische Punkte; eine Erweiterung würde ein Preset-Konstrukt (`config/conventions-presets.yaml`) mit Laufzeitsemantik überladen.

### C (verworfen): Durchsetzung per Hook/Gate-Skript (z. B. `dod-push-check.sh`-ähnlich)

Verworfen: widerspricht der **Nutzerentscheidung** „strict = nur Prompt-/Konventions-Boundary, kein harter Hook im MVP" **[Nutzer]**.
Zudem bliebe ein Hook ohnehin nur Convention boundary (umgehbar via `$(...)`/`eval`, `branch-guard.md` Lücke 4) und
bräuchte pro Provider Hook-Registrierung plus Allowlist/Checksummen-Pflege.

## 7. Entscheidungen

### 7.1 Entscheidungen des Nutzers (aus dem Auftrag)

| ID | Entscheidung |
|---|---|
| U1 | Drei Modi `off\|advisory\|strict`, Default `off`. |
| U2 | Zusätzlicher Modus „Release-Fähigkeit prüfen OHNE Release zu bauen" (Dry-Check). |
| U3 | Punkte können mechanisch (Skript/Exit-Code) oder vom Agenten bewertet sein. |
| U4 | `strict` = nur Prompt-/Konventions-Boundary, KEIN harter Hook im MVP; als Folge-Option dokumentieren. |
| U5 | `agent-meta-manager` muss es einrichten können. |
| U6 | Admin-UI bietet dieselben Settings. |

### 7.2 Entscheidungen des Nutzers (aus dem Builder-Check, rev 1.1)

| ID | Entscheidung des Nutzers | Auswirkung (Abschnitte/ACs) |
|---|---|---|
| U7 (C-1) | Default-Items in zwei Klassen: **Vorbedingungen** (`tests-green`, `dod-met`, `changelog-updated` im Sinne „[Unreleased] gefüllt", `readme-current`) werden VOR dem Release bewertet. **Schritte** (`version-bumped`, `build-created`, `git-tag-push`) werden NACH ihrer Ausführung bestätigt und sind im Dry-Check/`check-only` `n/a (nicht ausgeführt)`, ohne dass `strict` dadurch scheitert. | §9.1, §9.2, §9.3, §9.4, §10.1-10.4, IC-3/4, AC-REL-21, AC-REL-24 |
| U8 (C-2) | Gates (`pre-release-check.sh`, Schritt 0) bleiben in JEDEM Modus hart (Exit≠0 ⇒ `STATUS: failed` wie heute). Der Modus wirkt nur auf Checklistenpunkte. Kein Manager-Hinweis „Gates werden weicher" nötig. | NZ3, §10.2, §10.5, AC-REL-22 |
| U9 (C-5) | Einheitliches Freigabeprotokoll: Der Worker stoppt VOR der ersten Mutation (Bump, CHANGELOG-Edit, Tag, Push) und liefert `STATUS: partial` + `APPROVAL_REQUEST: <Aktion/IDs>`; der Orchestrator holt das Okay beim Nutzer (`main_chat`) und dispatcht neu mit `APPROVED: <Aktion/IDs>` im Auftrag; die Freigabe gilt nur für die genannte Aktion. | Z8, AZ9, §10.2 (Regeln R-S6..R-S8), §10.3 (Felder), AC-REL-23 |
| U10 (OF-7) | In `strict` dürfen genau die zwei Default-Punkte `dod-met` und `readme-current` `n/a` sein, aber nur mit einzeiliger Begründung im Ergebnis (Spalte `reason` ist bei `n/a` Pflicht). Alle anderen Punkte (inkl. `tests-green`, `changelog-updated`) bleiben in `strict` Pflicht; eigene `items` bleiben nur über `applies-when` `n/a`-fähig. Die zwei Default-Punkte tragen dafür die Eigenschaft `na-allowed-with-reason: true` (Konstante `RESERVED_DEFAULT_ITEMS`, kein Schema-Feld für Nutzer-Items). | §9.3, §10.1, §10.2, §10.3, R-S9, IC-3, AC-REL-8, AC-REL-21, AC-REL-25, §17, F5 |

## 8. Calls des Autors (begründet; siehe §18/§21)

### 8.1 Calls des Autors (Erstentwurf, ggf. angepasst)

| ID | Call | Begründung |
|---|---|---|
| CA1 | Blockform `release-checklist: {mode, items: [{id, task, verification, check: agent\|script, script?, required?, applies-when?, phase?}]}`. | Minimal und auf U3 zugeschnitten; `required`, `applies-when` und `phase` tragen die Semantik von `strict` (§10). `verification` ist bei Skript-Items redundant zu `script`, bleibt aber Pflicht (einheitliche Tabelle). |
| CA2 | Modus-Muster von `subagent_permissions` (Schema `config/project-config.schema.json:1617-1640`, Validierung `scripts/lib/config.py:674`, Resolver `scripts/lib/variables.py:366-400`) **mit Abweichung**: Normalizer nur `False`→`"off"` (siehe b1/C6). | Bewährtes Muster; Bool-Verhalten laut AC-REL-3 maßgeblich. |
| CA3 | Default-Items bleiben in `agents/1-generic/release.md:58-64`; `items` erweitern sie; Block-Platzierung laut b2. | Kein Bruch der Template-Struktur, byte-identisch bei `off` (b4/a7). |
| CA4 | `pre-release-check.sh` bleibt Schritt 0 und in jedem Modus hart (U8). | Keine Doppelmechanik; Gate-Vertrag unverändert, kein Rückschritt gegenüber heute. |
| CA5 | Semantik-Tabelle §10.2 und Ergebnisformat §10.3 inkl. Phasen (U7) und Freigabeprotokoll (U9). | Machbar ohne Laufzeit-Code, prüfbar am Prompt-Text. |
| CA6 | Dry-Check = Agent-Modus `check-only` + Command `/release-check` (`commands/1-generic/`); `sync.py --release-check` nur als spätere Option. | Recon-Empfehlung (a)+(b). |
| CA7 | Eigener Modul-Name `scripts/lib/release_checklist.py`; ein Platzhalter `{{RELEASE_CHECKLIST_BLOCK}}`. | Pflicht wegen Dateigrößen (C4). |
| CA8 | `check: script` führt der Agent per `Bash` aus; keine Allowlist, keine Pfadprüfung; Validierung nur Leerstring/Zeilenumbruch (b6). | Vertrauensstufe wie `TEST_COMMANDS`/`BUILD_COMMANDS`; R3 dokumentiert. |

### 8.2 Call des Autors (Builder-Check) — Minor-Entscheidungen

| ID | Call des Autors (Builder-Check) | Betrifft |
|---|---|---|
| b1 | Normalizer bildet nur `False`→`"off"` ab; `True` bleibt, der Validator meldet „quote the value". CA2 entsprechend korrigiert; Belegzeilen: Normalizer `config.py:346-364`, Resolver `variables.py:366-400`. | C6, §9.4, IC-2, AC-REL-3 |
| b2 | Der Block steht in `{{#if RELEASE_CHECKLIST_ENABLED}}` **nach** Z.65 (hinter der Checklisten-Tabelle und `{{RELEASE_CUSTOM_CHECKLIST_BLOCK}}`), vor `## 2.`; die Modus-Prosa verweist auf Schritt 0. IC-9 und §18.2 sind vereinheitlicht (Reihenfolge: Default-Zeilen → Custom-Zeilen → neuer Block). | IC-9, §18.2 |
| b3 | Ein einziger Platzhalter `{{RELEASE_CHECKLIST_BLOCK}}`; die Prosa ordnet an, die `CHECKLIST_*`-Zeilen dem Return voranzustellen. Kein `RELEASE_CHECKLIST_RESULT_BLOCK`. | IC-4, IC-9, OF-5 entschieden |
| b4 | Präfix `RELEASE_CHECKLIST_` in die Whitelist von `strip_inactive_conditional_blocks` (`variables.py:431-450`); `standalone.py` `_CONDITIONAL_FALSE_FLAGS` mit `"false"`, Fallback des Blocks `""`. | IC-5, IC-6b |
| b5 | AC-REL-19 gilt für **neue** Module (<= 600 Zeilen); bestehende Module wachsen nur um Aufrufzeilen. | AC-REL-19 |
| b6 | Keine Pfadprüfung für `script`; nur Zeilenumbruch/Leerstring werden geprüft. R3 dokumentiert das. | §9.4, R3 |
| b7 | Skript-Items MÜSSEN seiteneffektfrei sein (Doku und Schema-`description`). Sie werden im `check-only`-Lauf trotzdem ausgeführt. | §9.2, §10.4, §18.1 |
| b8 | Neuer Section-Guard in `_write_project_section` (`scripts/admin-server.py:5176-5200`); er nutzt den nicht-exitenden Validator aus `release_checklist.py`. AC-REL-13 stützt sich darauf (der Server validiert Section-Writes bisher nicht gegen das Schema). | IC-15b, §12, AC-REL-13 |
| b9 | `sharkord-release.md`: Block mit `{{#if RELEASE_CHECKLIST_ENABLED}}` vor „## Checkliste vor Release" (:226) einfügen, `based-on`/Version nachziehen. (Fallback-Variante: Validator-Warnung, falls ein Sharkord-Projekt mode≠off setzt und der Block fehlt.) | IC-11, OF-2 entschieden |
| b10 | Konstante der reservierten Default-IDs in `release_checklist.py` plus Test, der die Template-Zeilenzahl gegen die Konstante prüft. | IC-3, §17 |
| b11 | `/release-check` bei `off`: Der Agent kennt `check-only` nur aus dem Command-Text; hingenommen. Der Command-Text nennt die Verbote vollständig (AC-REL-10). | §10.4 |
| b22 | `agent-meta-manager` 1.25.0 → **1.26.0** (Spec 2 folgt mit 1.27.0; Reihenfolge Spec 1 → 2). | IC-14 |

## 9. Konfig-Schema

### 9.1 YAML-Beispiel (`.meta-config/project.yaml`)

```yaml
release-checklist:
  mode: advisory            # off | advisory | strict   (Default: off)
  items:
    - id: changelog-unreleased
      task: "CHANGELOG [Unreleased] hat Einträge"
      verification: "Abschnitt [Unreleased] nicht leer"
      check: agent          # agent | script   (Default: agent)
      phase: precondition   # precondition | step   (Default: precondition)
      required: true        # Default: true; nur strict wertet aus
    - id: schema-valid
      task: "Konfiguration validiert"
      verification: "python3 scripts/sync.py --validate"
      check: script
      script: "python3 scripts/sync.py --validate"   # nur bei check: script; Exit 0 = pass; MUSS seiteneffektfrei sein
      required: true
    - id: docker-image-pushed
      task: "Docker-Image gepusht"
      verification: "docker manifest inspect <image>:<version>"
      check: agent
      phase: step           # wird erst NACH Ausführung des Release-Schritts bestätigt
      required: false
      applies-when: "Projekt liefert ein Docker-Image aus"   # Freitext, vom Agenten ausgewertet
```

### 9.2 JSON-Schema-Skizze (Einfügen unter `properties` in `config/project-config.schema.json`)

Das Schema ist Zusatz (Autocomplete, Warnung bei `jsonschema`; C7). Harte Fehler im Python-Validator (§9.4). Kein Top-Level-`default` (C9).

```json
"release-checklist": {
  "type": "object",
  "description": "Structured release checklist. Absent block or mode 'off' = zero behavior change. Script items MUST be side-effect free (they also run in check-only mode). Not to be confused with 'release-gates'.",
  "properties": {
    "mode": { "type": "string", "enum": ["strict", "advisory", "off"], "description": "Quote the value: unquoted off/on are YAML booleans." },
    "items": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "task", "verification"],
        "properties": {
          "id": { "type": "string", "pattern": "^[a-z0-9][a-z0-9-]*$" },
          "task": { "type": "string", "minLength": 1 },
          "verification": { "type": "string", "minLength": 1 },
          "check": { "type": "string", "enum": ["agent", "script"] },
          "script": { "type": "string", "minLength": 1, "description": "Command line, exit 0 = pass. Must be side-effect free." },
          "phase": { "type": "string", "enum": ["precondition", "step"], "description": "precondition = evaluated before the release; step = confirmed after its execution." },
          "required": { "type": "boolean" },
          "applies-when": { "type": "string", "minLength": 1 }
        },
        "additionalProperties": false,
        "if": { "properties": { "check": { "const": "script" } }, "required": ["check"] },
        "then": { "required": ["script"] }
      }
    }
  },
  "additionalProperties": false
}
```

Hinweis zur YAML-Bool-Falle: Der Normalizer in `release_checklist.py` (aufgerufen aus `load_config` vor `_validate_config`) bildet ein geladenes Bool `False` auf `"off"` ab. `True` bleibt unverändert und wird vom Validator mit „quote the value" abgelehnt (b1).

### 9.3 Defaults (Resolver-Ebene, nicht in project.yaml geschrieben)

| Key | Default | Wirkung bei Default |
|---|---|---|
| `release-checklist` (Block fehlt) | = `{mode: off, items: []}` | `release.md` byte-identisch |
| `mode` | `off` | wie heute |
| `items` | `[]` | nur Default-Items aus dem Template |
| `item.check` | `agent` | Agent bewertet |
| `item.phase` | `precondition` | vor dem Release bewertet |
| `item.required` | `true` | in `strict` Pflicht |
| `item.script` | — | Pflicht nur bei `check: script` |
| `item.applies-when` | — | kein `n/a` in `strict` möglich (Ausnahmen: `n/a (nicht ausgeführt)` für `phase: step` im Dry-Check; Default-Punkte mit `na-allowed-with-reason`, siehe unten) |
| Default-Item `na-allowed-with-reason` | `false`; `true` nur für `dod-met`, `readme-current` | in `strict` `n/a` erlaubt, wenn die Begründung einzeilig und nicht leer ist (U10). Eigenschaft der reservierten Default-Items (Konstante `RESERVED_DEFAULT_ITEMS`), **kein** Feld in `project.yaml` oder im Schema für Nutzer-Items (`additionalProperties: false` bleibt) |

### 9.4 Validierungsregeln (Python-Validator im Config-Load, hart)

1. `mode` ∈ {off, advisory, strict} nach Normalisierung (`False`→`"off"`); `True` oder anderer Wert ⇒ Fehler mit Pfadangabe und „quote the value".
2. `id` eindeutig innerhalb `items`; kollidiert nicht mit den reservierten Default-IDs (Konstante, siehe §10.1).
3. `check: script` ⇒ `script` vorhanden, nicht leer; `script` darf keinen Zeilenumbruch enthalten. Keine Pfadprüfung (b6; Begründung: `script` ist eine Kommandozeile, siehe R3).
4. `check: agent` ⇒ `script` darf nicht gesetzt sein (Fehler, vermeidet tote Konfiguration).
5. Unbekannte Keys (Block, Item) ⇒ **Fehler im Validator** (nicht nur Schema-Warnung; einheitlich mit Spec 2).
6. `phase` ∈ {precondition, step}, sonst Fehler.

Der Validator hat zwei Einstiege: eine hart abbrechende Variante für den Config-Load und eine nicht-exitende Variante (Rückgabe: Liste von Fehlermeldungen), die der Admin-Server-Section-Guard wiederverwendet (IC-2, IC-15b).

## 10. Verhalten / Semantik

### 10.1 Default-Items (Template, unverändert im Text) und Klassen

Die sieben Zeilen aus `release.md:58-64` erhalten implizite IDs, die nur im Ergebnisformat erscheinen. Reserviert: Nutzer-Items dürfen diese IDs nicht verwenden. Die Liste ist als Konstante in `release_checklist.py` geführt und per Test gegen die Template-Zeilenzahl gesichert (b10).

| ID | Phase | `na-allowed-with-reason` | Bewertung |
|---|---|---|---|
| `tests-green` | precondition | false | vor dem Release |
| `dod-met` | precondition | **true** | vor dem Release; `n/a` mit Begründung z. B. bei inaktivem Validator |
| `changelog-updated` | precondition | false | im Sinne „`[Unreleased]` ist gefüllt" (der CHANGELOG-Edit selbst ist Mutation, siehe §10.2 Ablauf) |
| `readme-current` | precondition | **true** | vor dem Release; `n/a` mit Begründung z. B. bei deaktiviertem CODEBASE_OVERVIEW |
| `version-bumped` | step | false | nach dem Bump bestätigt |
| `build-created` | step | false | nach dem Build bestätigt |
| `git-tag-push` | step | false | nach Tag/Push bestätigt |

Im Dry-Check (`check-only`) sind alle `step`-Punkte (Default und Projekt) `n/a (nicht ausgeführt)`; sie zählen nicht gegen `strict`.

### 10.2 Zustandsregeln

| Aspekt | `off` | `advisory` | `strict` |
|---|---|---|---|
| Schritt 0 (Gates, `pre-release-check.sh`) | **hart wie heute**: Exit≠0 ⇒ `STATUS: failed`; fehlender Hook ⇒ Info | **hart wie `off`** (U8) | **hart wie `off`** (U8) |
| Vorbedingungen (Default + Projekt-Items mit `phase: precondition`) | wie heute | Agent bewertet jeden Punkt `pass\|fail\|n/a` + einzeilige Begründung | alle Pflichtpunkte müssen `pass` sein |
| Schritte (`phase: step`) | wie heute | nach Ausführung bestätigt (`pass\|fail`); im Dry-Check `n/a (nicht ausgeführt)` | wie advisory, zusätzlich verbindlich nach `required`; im Dry-Check `n/a (nicht ausgeführt)` ohne Wirkung auf `strict` |
| `items` des Projekts | nicht gerendert | bewertet (agent) bzw. ausgeführt (script) | wie advisory, zusätzlich verbindlich nach `required` |
| `n/a` | — | erlaubt mit konkreter Begründung | nur wenn Punkt `applies-when` besitzt und Bedingung nicht zutrifft, **oder** der Punkt `dod-met`/`readme-current` ist (`na-allowed-with-reason`, einzeilige Begründung Pflicht, U10); Ausnahme: `n/a (nicht ausgeführt)` für Schritte im Dry-Check. Alle übrigen Default-Punkte (u. a. `tests-green`, `changelog-updated`) sind in `strict` nie `n/a` |
| Fail einer Vorbedingung | — | berichtet; Release nur nach Freigabe (`APPROVAL_REQUEST`, R-S6) | Pflichtpunkt ⇒ `STATUS: failed`, **keine Mutation**, kein Tag/Push |
| Fail eines Schritts nach Ausführung | — | `STATUS: partial`, Tag/Push nur nach neuer Freigabe (R-S7) | Pflichtpunkt ⇒ `STATUS: failed`, **kein Tag/Push** |
| `required: false` | — | wie normaler Punkt | Fail wird berichtet und über `APPROVAL_REQUEST` zur Freigabe gestellt, blockiert nicht |
| Boundary-Art | — | Prompt-Konvention | Prompt-/Konventions-Boundary (Convention boundary), kein Hook |

Ablauf (Release-Workflow-Position, ersetzt R-S5 aus rev 1.0):

1. Schritt 0: Gates (hart, jeder Modus).
2. Vorbedingungen bewerten (Default-Vorbedingungen → Projekt-Vorbedingungen). Dies geschieht **vor** jeder Mutation.
3. Entscheidung: `strict` + Pflicht-Vorbedingung `fail` ⇒ `STATUS: failed` (Ende). Gibt es Nicht-Pass-Punkte, deren Freigabe nötig ist (advisory: jeder `fail`; strict: `fail` von `required: false`), ⇒ Stopp mit `STATUS: partial` + `APPROVAL_REQUEST` (R-S6), sofern keine passende `APPROVED:`-Zeile im Auftrag steht.
4. Mutationen und Schritte in dieser Reihenfolge: Version-Bump (→ `version-bumped` bestätigen), CHANGELOG-Edit, Build (→ `build-created` bestätigen), Projekt-Schritte (`phase: step`), danach Tag/Push über den `git`-Agenten (→ `git-tag-push` bestätigen). Schlägt ein Schritt fehl: siehe Tabelle (strict-Pflicht ⇒ `failed`, advisory ⇒ `partial`).
5. Ergebnistabelle (§10.3) und Entscheidung.

Regeln:

- R-S1: Ergebnis eines `check: script`-Punkts: Exit 0 ⇒ `pass`, ≠0 ⇒ `fail`; Skript fehlt/nicht ausführbar ⇒ `fail` (nie stilles `n/a`).
- R-S2: Skript-Output wird nicht in die Ergebnistabelle kopiert (nur Exit-Code + Einzeiler); Details in eine Datei unter `.tmp/` (tmp-sink) falls nötig.
- R-S3: In `advisory` wird `n/a` nur akzeptiert, wenn die Begründung konkret ist; leere Begründung ⇒ der Agent wertet `fail`.
- R-S4: Der Release-Agent darf in keinem Modus den Modus selbst ändern.
- R-S5: Reihenfolge laut Ablauf oben (Schritt 0 → Vorbedingungen → Entscheidung → Mutationen/Schritte → Ergebnistabelle).
- R-S6 (U9): **Freigabeprotokoll.** Muss der Worker trotz Nicht-Pass fortfahren (oder verlangt der Modus eine Freigabe), stoppt er VOR der ersten Mutation (Bump, CHANGELOG-Edit, Tag, Push) und liefert `STATUS: partial` + `APPROVAL_REQUEST: release <version>; actions=bump,changelog,build,tag,push; accept=<ids der Nicht-Pass-Punkte>`. Er mutiert nichts, bevor die Freigabe vorliegt.
- R-S7 (U9): Der Orchestrator holt das Okay beim Nutzer (`main_chat`) und dispatcht neu mit `APPROVED: <Aktion/IDs>` im Auftrag (gleiche Aktion/IDs wie angefragt). Die Freigabe gilt **nur** für die genannte Aktion und die genannten IDs; weitere Nicht-Pass-Punkte oder ein fehlschlagender Schritt erzeugen eine neue `APPROVAL_REQUEST` (Beispiel `APPROVAL_REQUEST: continue-after-step-fail <ids>` vor Tag/Push).
- R-S9 (U10): In `strict` ist `n/a` für `dod-met`/`readme-current` zulässig, wenn die Spalte `reason` eine einzeilige, nicht leere Begründung enthält; ein `n/a` ohne Begründung wird als `fail` gewertet (zählt in `fail` und, da Pflichtpunkt, in `required_failed`). Gilt für kein anderes Default-Item; eigene `items` sind nur über `applies-when` `n/a`-fähig.
- R-S8: Bei Re-Dispatch bewertet der Worker die Vorbedingungen erneut; weicht das Ergebnis von den freigegebenen IDs ab, gilt R-S6 erneut.

### 10.3 Ergebnisformat (Return-Erweiterung)

Bei `mode != off` stellt der Release-Agent dem Return die folgenden Zeilen voran (vor `STATUS`; Prosa im Block, kein zweiter Platzhalter, b3):

```
CHECKLIST_MODE: advisory|strict
CHECKLIST:
| id | phase | check | result | reason (1 line) |
|----|-------|-------|--------|-----------------|
| tests-green | precondition | script | pass | exit 0 |
| version-bumped | step | agent | n/a (nicht ausgeführt) | Dry-Check |
CHECKLIST_SUMMARY: pass=<n> fail=<n> n/a=<n> not_run=<n> required_failed=<n>
APPROVAL_REQUEST: <Aktion/IDs>   # nur bei STATUS: partial wegen Freigabe, sonst weglassen
```

`result` ∈ `pass | fail | n/a | n/a (nicht ausgeführt)`. Die Spalte `reason` ist bei `n/a` **Pflicht** (einzeilig, nicht leer); fehlt sie, wertet der Agent den Punkt als `fail` (R-S3, R-S9). `not_run` zählt `n/a (nicht ausgeführt)` und geht nie in `required_failed` ein.

`STATUS`: `strict` und `required_failed>0` ⇒ `failed`; `advisory` mit `fail>0` oder offener Freigabe ⇒ `partial` (+ `APPROVAL_REQUEST`), sonst `done`. Gate-Fehler (Schritt 0) ⇒ `failed` in jedem Modus.

### 10.4 Dry-Check (`check-only`)

- Aufruf-Parameter an den Release-Agenten: `MODE: check-only` im Auftrag (kein neues Frontmatter-Feld).
- Erlaubt: Schritt 0, alle **Vorbedingungen** lesen/ausführen (Skript-Items werden ausgeführt und MÜSSEN deshalb seiteneffektfrei sein, b7), Ergebnistabelle.
- `phase: step`-Punkte (Default `version-bumped`, `build-created`, `git-tag-push` und Projekt-Schritte): `n/a (nicht ausgeführt)`, ohne Wirkung auf `strict` (U7).
- Verboten (Prompt-Konvention, Convention boundary): Tag, Push, Build, Version-Bump, CHANGELOG-/Datei-Edit, Commit, `gh release`.
- Verhalten je Modus: `off` ⇒ Dry-Check läuft mit dem Default-Umfang (Gates + Default-Vorbedingungen, **kein** Projekt-Items-Block, da nicht gerendert) und meldet dies; `advisory`/`strict` ⇒ voller Umfang. Ergebnis: `STATUS: done` (release-fähig), `partial` (advisory mit Fail einer Vorbedingung), `failed` (Gate-Fehler oder strict mit Pflicht-Fail einer Vorbedingung). Ein Dry-Check erzeugt nie eine `APPROVAL_REQUEST` (keine Mutation).
- Der Block zur Dry-Check-Semantik wird **immer** gerendert, sobald `mode != off`; bei `off` entfällt er (byte-identisch). Der Command `/release-check` bleibt auch bei `off` nutzbar und weist den Agenten explizit an, `MODE: check-only` zu setzen (der Agent kennt die Regel aus dem Command-Text, nicht aus dem Template; b11).

### 10.5 Interaktion mit `release-gates:`

`release-gates:` (Schema `config/project-config.schema.json:675-698`, Resolver `scripts/lib/dod.py:380-413`, Sync `scripts/lib/hook_plugins.py:28`) steuert weiterhin **welche** Gates aktiv sind. Die Gate-Behandlung (Exit≠0 ⇒ `failed`) ist **modusunabhängig hart** (U8); `release-checklist.mode` wirkt ausschließlich auf Checklistenpunkte. Kein Schreibzugriff des neuen Moduls auf Gate-Dateien.

## 11. Interface Contracts

| # | Datei:Symbol | Signatur / Vertrag | Fehlerpfade |
|---|---|---|---|
| IC-1 | `config/project-config.schema.json` → `properties."release-checklist"` | Schema §9.2 (Zusatz; kein Top-Level-`default`) | Warnung (nur mit `jsonschema`) |
| IC-2 | `scripts/lib/release_checklist.py` → `normalize_release_checklist_mode(config: dict) -> None` (nur `False`→`"off"`, aufgerufen aus `load_config` vor `_validate_config`), `validate_release_checklist(config: dict, config_path: Path) -> None` (hart, Config-Load; Aufruf neben `_validate_subagent_permissions`, `config.py:396`) und `collect_release_checklist_errors(config: dict) -> list[str]` (nicht-exitend, Basis beider Validatoren) | Regeln §9.4 | `ConfigError`/`sys.exit` nur in `validate_release_checklist` (C7) |
| IC-3 | `scripts/lib/release_checklist.py` → `resolve_release_checklist(config: dict) -> dict`; Konstante `RESERVED_DEFAULT_ITEMS: tuple[tuple[str, str, bool], ...]` (`(id, phase, na_allowed_with_reason)`; `True` nur für `dod-met`, `readme-current`, U10) | Rückgabe `{"mode": str, "items": list[dict]}` mit gefüllten Defaults (`check`, `phase`, `required`); nie Exception, nie Exit (bei kaputter Struktur: `mode="off"`, `items=[]`, `log.warning`) | — |
| IC-4 | `scripts/lib/release_checklist.py` → `render_release_checklist_block(resolved: dict) -> str` | Leerer String bei `mode=="off"`; sonst Markdown-Block: Modus-Prosa (verweist auf Schritt 0), Phasen-Klassen, Items-Tabelle, Ablauf/Freigabeprotokoll (R-S6..R-S8), Ergebnis-Contract (§10.3, `CHECKLIST_*`-Zeilen dem Return voranstellen), `check-only`-Regel | — |
| IC-5 | `scripts/lib/config.py` → Aufruf-/Registrierungszeilen (kein neuer Logikblock): Variablen `RELEASE_CHECKLIST_MODE` (`off\|advisory\|strict`), `RELEASE_CHECKLIST_ENABLED` (`"true"`/`"false"`-String), `RELEASE_CHECKLIST_BLOCK` über `_build_convention_variables` (`config.py:2293`) bzw. das `_SET`-Muster (`config.py:1442`); `scripts/lib/variables.py` → Präfix `RELEASE_CHECKLIST_` in die Whitelist von `strip_inactive_conditional_blocks` (`variables.py:431-450`), Resolver-Aufrufstelle im Muster `:366-400` | Regel `agent-meta-conventions.md:105-109`; siehe IC-3 bei kaputter Struktur | — |
| IC-6 | `scripts/lib/consistency/placeholders.py` → bekannte Platzhalter ergänzen (`RELEASE_CHECKLIST_BLOCK`, `RELEASE_CHECKLIST_MODE`, `RELEASE_CHECKLIST_ENABLED`) | C5 | Consistency-Check schlägt sonst an |
| IC-6b | `scripts/lib/standalone.py` → `_CONDITIONAL_FALSE_FLAGS` (:122ff, Kommentar :110-121) | `RELEASE_CHECKLIST_ENABLED` mit `"false"`; Fallback von `RELEASE_CHECKLIST_BLOCK` = `""` (Standalone-Templates ohne Sync) | — |
| IC-8 | `docs/guides/features/sync-concept.md` (Tabelle „Auto-injiziert", ~:280) | Zeilen für `RELEASE_CHECKLIST_MODE`, `RELEASE_CHECKLIST_ENABLED`, `RELEASE_CHECKLIST_BLOCK` (korrigiert: eine CLAUDE.md-Variablentabelle gibt es nicht; Doku-Beispiele mit `{{RELEASE_CHECKLIST_BLOCK}}` escapen, Berührung Issue #1082) | — |
| IC-9 | `agents/1-generic/release.md` | (a) `{{#if RELEASE_CHECKLIST_ENABLED}}\n{{RELEASE_CHECKLIST_BLOCK}}\n{{/if}}\n` **nach** Z.65 (`{{RELEASE_CUSTOM_CHECKLIST_BLOCK}}`), vor `## 2.` (b2); inaktive Blöcke werden samt Zeilenumbruch entfernt (`variables.py:483`), die Leerzeile von Z.65 ist bereits Teil der Baseline (`tests/test_conventions_migration_invariant.py:99-105`) ⇒ bei `off` byte-identisch; (b) kein eigener Result-Platzhalter (b3); (c) Schritt-0-Text und Default-Items-Tabelle bleiben im Wortlaut; (d) `version: "1.12.2"` → `"1.13.0"` | — |
| IC-10 | `agents/2-platform/hacs-release.md` | `based-on` → `1-generic/release.md@1.13.0`, `version` 1.1.0 → 1.1.1. Einziger Patch-Anker ist `<persona>` (`append-after`), von IC-9 **nicht betroffen** | — |
| IC-11 | `agents/2-platform/sharkord-release.md` | Standalone mit `based-on`, kein `extends/patches`: Block `{{#if RELEASE_CHECKLIST_ENABLED}}…{{/if}}` vor „## Checkliste vor Release" (:226) einfügen (b9; kein Schritt 0/`<output_contract>` dort, Prosa-Verweis auf Schritt 0 entsprechend anpassen), `based-on` → `@1.13.0`, `version` 1.3.2 → 1.3.3 | — |
| IC-12 | `commands/1-generic/release-check.md` (neu) | Dünner Prompt: Auftrag an `release` mit `MODE: check-only`; Output = Ergebnistabelle; Verbote vollständig genannt | Release-Agent nicht aktiv ⇒ Hinweistext |
| IC-13 | `commands/1-generic/set-release-checklist.md` (optional, neu) | Vorlage `set-preset.md`: project.yaml lesen, Key ändern, Sync, `--validate` | — |
| IC-14 | `agents/1-generic/agent-meta-manager.md` | Rezeptabschnitt „Release-Checkliste" (Muster §14a-c / §16), `version` 1.25.0 → **1.26.0**; §3-Bestätigungstabelle: `strict` aktivieren = Behavior-Change. **Kein** Hinweis „Gates werden weicher" (U8) | — |
| IC-15 | `scripts/admin-server.py` → `PROJECT_WRITABLE_SECTIONS` (Z.233-252) | `"release-checklist"` ergänzen | nicht gelistet ⇒ HTTP 400 |
| IC-15b | `scripts/admin-server.py` → `_write_project_section` (:5176-5200), neuer Section-Guard analog `_validate_project_provider_options`/`_guard_model_block_write` | Ruft `collect_release_checklist_errors` (nicht-exitend) und lehnt ungültige Payloads mit HTTP 400 + Fehlerliste ab (b8; bisher kein Schema-Check bei Section-Writes, `_route_get_schema_project` :3741 liefert nur das Schema per GET) | Fehlerliste ⇒ 400 |
| IC-16 | `docs/ui/admin-ui.html` → `viewProjectReleaseChecklist()` + `routeMap` + Nav + Help-ID | siehe §12 | — |

## 12. Admin-UI

- Sektion **Release-Checkliste** (Nav-Eintrag nahe `auto_commit`/`subagent_permissions`), Muster `auto_commit` (`docs/ui/admin-ui.html` `viewProjectAutoCommit` ~:7637; Save ~:7759 via `saveProjectSection("release-checklist", payload, status)`).
- Felder: `mode` (Select off/advisory/strict, Hinweistext „strict = nur Prompt-Konvention, kein Hook; Gates bleiben in jedem Modus hart"), `items`-Tabelle mit Modal (id, task, verification, check, script [nur bei `script`; Hinweis „muss seiteneffektfrei sein"], phase, required, applies-when).
- Whitelist: `"release-checklist"` in `PROJECT_WRITABLE_SECTIONS` (`scripts/admin-server.py:233-252`).
- Server-Validierung: neuer Section-Guard (IC-15b, b8); PUT `/api/config/project/section` (:3622) lehnt ungültige Payloads mit HTTP 400 ab.
- JS-View: `viewProjectReleaseChecklist`; `router.register`; `routeMap`-Eintrag (`~:10961`); Help-ID + Eintrag in `docs/api/admin-ui-reference.md`; `check_ui_help_mappings` (`scripts/lib/consistency/docs.py:47`) muss grün bleiben.
- Parität: UI schreibt exakt dasselbe Feld `release-checklist` wie CLI/Manager. Paritäts-Test: gleiche Payload per UI-Endpoint und per Manager-Weg ergibt identisches `project.yaml`-Fragment.
- YAML-Bool-Hinweis: UI sendet `mode` immer als String und quotet beim Schreiben (`"off"`); Verhalten des YAML-Writers bei `"off"` ist im Test abzusichern (im Builder-Check nicht geprüft).
- Keine Skript-Ausführung aus der UI (nur Konfiguration).

## 13. agent-meta-manager

- Neuer Rezeptabschnitt „Release-Checkliste" in `agents/1-generic/agent-meta-manager.md` (Version 1.25.0 → 1.26.0): (1) aktuellen Block lesen; (2) Modus erfragen; (3) Items ergänzen (id/task/verification/check/phase); (4) `project.yaml` editieren (Modus **gequotet**); (5) `python scripts/sync.py` + `--validate`; (6) Hinweis „strict = Prompt-Konvention; Gates bleiben in jedem Modus hart".
- §3-Bestätigungstabelle: `strict` aktivieren = Behavior-Change ⇒ explizite Bestätigung. Kein Bestätigungshinweis „Gates werden weicher" (U8).
- Optional Command `set-release-checklist` (IC-13).
- Schema ist Autorität (§15 im Manager): Manager darf nur schema-konforme Werte schreiben.

## 14. Datenfluss

1. `project.yaml` → Config-Load → `normalize_release_checklist_mode` → `validate_release_checklist` (hart) → `resolve_release_checklist` (weich).
2. Resolver → Variablen `RELEASE_CHECKLIST_MODE/ENABLED` und `RELEASE_CHECKLIST_BLOCK` → Template-Substitution in `release.md` (+ Overrides); `{{#if RELEASE_CHECKLIST_ENABLED}}` entfernt den Block bei `off` samt Zeilenumbruch.
3. Generiertes `release.md` → Release-Agent liest Prosa-Block → Schritt 0 (hart) → Vorbedingungen (inkl. Skripte) → Entscheidung → ggf. Stopp mit `STATUS: partial` + `APPROVAL_REQUEST`.
4. Orchestrator holt Freigabe bei `main_chat`/Nutzer → Re-Dispatch mit `APPROVED: <Aktion/IDs>` → Worker mutiert (Bump/CHANGELOG/Build/Schritte) und bestätigt Schritte nach Ausführung → Tag/Push durch `git`-Agent → Ergebnistabelle im Return.
5. `main_chat`/Orchestrator wertet `STATUS` aus.
6. Persistenz: nur `project.yaml` (Konfig) und generierte Agenten-Dateien; kein Laufzeitzustand.

## 15. Folge-Optionen (nicht MVP)

- F1: **Harter Durchsetzungs-Hook für `strict`** (z. B. Erweiterung eines Push-Checks im Stil `dod-push-check.sh`, vgl. `branch-guard.md`): echte Blockade, aber nur Convention boundary und pro Provider zu registrieren. Entscheidung dem Nutzer vorbehalten **[Nutzer: U4]**.
- F2: **`sync.py --release-check`** (nur mechanischer Teil: Gates + Skript-Vorbedingungen; Hook-Pfad pro Provider auflösen).
- F3: Schema↔UI-Coverage-Test.
- F4: Skript-Punkte mit Allowlist/Checksumme analog Gates, falls Skript-Injection (R3) relevant wird.
- F5: Implizite, maschinell ausgewertete `applies-when`-Bedingungen für Default-Vorbedingungen (`dod-met`, `readme-current`) als Alternative zu `na-allowed-with-reason`; im MVP durch U10 ersetzt (kein Bedarf, solange die Begründung genügt).

## 16. Berührungspunkte (Dateien/Funktionen)

Belege aus `.tmp/recon-release.md` und `.tmp/spec-builder-check.md`; **verifiziert** (V) bzw. **nicht erneut geprüft** (N).

| Pfad | Symbol / Zeile | Art | Prüfstatus |
|---|---|---|---|
| `agents/1-generic/release.md` | :52-65 Checkliste (Default-Items :58-64), :31-50 Schritt 0, :86-92 Workflow, `version: "1.12.2"` | ändern | V |
| `agents/2-platform/hacs-release.md` | Patch-Anker nur `<persona>`, `based-on …@1.12.2` | based-on nachziehen | V |
| `agents/2-platform/sharkord-release.md` | `based-on …@1.12.2`, kein `patches`; „## Checkliste vor Release" :226 | Block einfügen, based-on nachziehen | V |
| `scripts/lib/conventions.py` | :124-130, :176-193 `_render_release_custom_checklist` | Vorbild (Leerzeilen-Verhalten) | V |
| `config/conventions-presets.yaml` | :49/87/119 `custom_checklist: []` | unverändert | N |
| `config/project-config.schema.json` | :675-698 `release-gates`; :1617-1640 `subagent_permissions`; neuer Key | ändern | V |
| `scripts/lib/config.py` (2466 Zeilen) | :326/:346-364 Normalizer-Vorbild, :388-434 Schema-Warnung, :396 Validator-Aufruf, :674 Validator-Vorbild, :1060-1069 fill_defaults, :1442 `_SET`-Muster, :2293 `_build_convention_variables` | nur Aufrufe/Registrierung | V |
| `scripts/lib/variables.py` (796 Zeilen) | :366-400 Resolver, :431-450 Whitelist, :483 Block-Entfernung | Whitelist-Eintrag | V |
| `scripts/lib/standalone.py` (537 Zeilen) | :110-121 Kommentar, :122ff `_CONDITIONAL_FALSE_FLAGS` | ändern | V |
| `scripts/lib/release_checklist.py` | — | neu (<= 600 Zeilen) | — |
| `scripts/lib/dod.py` | :380-413 `resolve_release_gates` | unverändert (Verweis) | N |
| `scripts/lib/hook_plugins.py` | :28 `sync_release_gates` | unverändert | N |
| `scripts/lib/consistency/placeholders.py` | bekannte Platzhalter | ändern | N |
| `hooks/1-generic/pre-release-check.sh` | Dispatcher, Allowlist, Manifest | unverändert | N |
| `scripts/admin-server.py` | :233-252 Whitelist, :3622 PUT, :3741 Schema-GET, :5176-5200 `_write_project_section` | ändern (Whitelist + Section-Guard) | V |
| `docs/ui/admin-ui.html` | `viewProjectAutoCommit` ~:7637, Save :7759, `routeMap` :10961 | ändern | V (Stichprobe) |
| `docs/api/admin-ui-reference.md`, `scripts/lib/consistency/docs.py:47` | Help-Mapping | ändern/prüfen | N |
| `docs/guides/features/sync-concept.md` | :280 Tabelle „Auto-injiziert" | ändern | V |
| `agents/1-generic/agent-meta-manager.md` | v1.25.0 | ändern | N |
| `commands/1-generic/` | `release-check.md`, `set-release-checklist.md` | neu | N |
| `docs/RELEASE_GATES.md`, `docs/RELEASE_PROCESS` (Scaffold `scripts/lib/release_scaffold.py`) | Doku (inkl. ein Satz zu Spec 2, AC-ENV-19) | ändern | N |
| `tests/test_conventions_migration_invariant.py` | :99-105 Baseline Leerzeile | beachten/Vorbild | V |
| `tests/scenarios/registry.md`, `configs/<id>.project.yaml`, `asserts/<id>.sh`, `run.sh` | Szenarien | neu | N |
| `.claude/skills/{conventions,sync-interface,architecture}` | Doku-Hinweise | ggf. | N |
| `CHANGELOG.md`, `howto/configs/project.yaml.example` | Doku | ändern | N |

Berührungen: Issue #1082 (Placeholder-Check meldet escaped Doku-Beispiele) betrifft neue Doku mit `{{RELEASE_CHECKLIST_BLOCK}}`; Issue #1074 (fill_defaults) ⇒ C9.

Change Checklist (`rules/2-platform/agent-meta-conventions.md:111-123`, verifiziert): `1-generic/<role>.md` ⇒ Version bumpen; `2-platform` ⇒ `version` und `based-on` aktuell; `config/project-config.schema.json` ⇒ Autocomplete/jsonschema testen; neue Option ⇒ Szenario in `tests/scenarios/` + Lauf von `tests/scenarios/run.sh`.

**Version-Bumps (Summe):** `release.md` 1.12.2→1.13.0 (minor, neuer Block); `hacs-release.md` 1.1.0→1.1.1; `sharkord-release.md` 1.3.2→1.3.3; `agent-meta-manager.md` 1.25.0→1.26.0 (Spec 2 danach →1.27.0).

## 17. Tests

| Bereich | Datei (neu) | Inhalt |
|---|---|---|
| Schema | `tests/test_release_checklist_schema.py` | Enum; `check: script` ⇒ `script`-Pflicht; `additionalProperties`; ID-Pattern; `phase`-Enum; kein Top-Level-`default` |
| Resolver/Lib | `tests/test_release_checklist_lib.py` | `resolve_release_checklist` (Defaults inkl. `phase`, Bool-`False`→`off`, `True`→Fehler „quote the value", kaputte Struktur), `render_release_checklist_block` (leer bei off; Ausgabe für advisory/strict), Konstante `RESERVED_DEFAULT_ITEMS` gegen Template-Zeilenzahl von `release.md` (b10) |
| Config-Validierung | in `test_release_checklist_lib.py` | doppelte IDs, reservierte IDs, Skript mit Zeilenumbruch/Leerstring, `agent` mit `script`, unbekannte Keys ⇒ hart, ungültige `phase`; nicht-exitende Variante liefert Fehlerliste |
| Render | `tests/test_release_checklist_render.py` | **byte-identisch bei off und bei fehlendem Block** (Muster `tests/test_conventions_migration_invariant.py`, Baseline-Leerzeile beachten); advisory/strict-Text enthält Ergebnistabelle, Phasen-Klassen, Gates-hart-Satz, `APPROVAL_REQUEST`/`APPROVED`-Texte (Template-Text-Asserts); strict-Block nennt `n/a` nur für `dod-met`/`readme-current` mit Begründung, `reason` bei `n/a` als Pflicht (AC-REL-25); `RESERVED_DEFAULT_ITEMS`-Flag `na_allowed_with_reason` nur für diese zwei IDs |
| Overrides | in Render-Test | `hacs-release` rendert mit neuem `based-on`; Patch-Anker `<persona>` greift; `sharkord-release` enthält Block bei advisory und ist byte-identisch bei off |
| Consistency | `tests/test_release_checklist_consistency.py` | Platzhalter in `placeholders.py` bekannt; kein ungelöster `{{RELEASE_CHECKLIST_*}}`; standalone-Fallback |
| Admin-UI | `tests/test_admin_ui_release_checklist_section.py` (Muster `tests/test_admin_ui_git_section.py`) | Whitelist, PUT/GET-Roundtrip, Section-Guard (ungültiger Modus/`True`/unbekannter Key ⇒ 400), Parität |
| Szenarien | `tests/scenarios/registry.md` + `configs/<id>.project.yaml` + `asserts/<id>.sh` | „release-checklist-advisory" und „-strict" (Assert: Block im generierten Agenten), „-off" (Assert: kein Unterschied) |

Alle Tests Python >= 3.9-kompatibel, stdlib + vorhandene Test-Abhängigkeiten.

## 18. Doku, Migration, Risiken, offene Fragen

### 18.1 Doku
`docs/RELEASE_GATES.md` (Abschnitt „Checklist-Modus"; Hinweis „Gates bleiben in jedem Modus hart"; Hinweis „Skript-Items müssen seiteneffektfrei sein"; **ein Satz**, dass ein Dry-Check gegen eine Test-Umgebung nur `access: read`-Aktionen ausführt — Anforderung aus Spec 2, AC-ENV-19), `docs/api/admin-ui-reference.md`, `CHANGELOG.md` (Added), `howto/configs/project.yaml.example`, ggf. `docs/RELEASE_PROCESS`-Scaffold-Hinweis, `docs/guides/features/sync-concept.md` (Platzhalter-Tabelle).

### 18.2 Migration / Kompatibilität
Opt-in. Ohne Block: keine Änderung (Invariante AC-REL-1). Bestehende `conventions.release.custom_checklist` bleibt gültig und wird unabhängig gerendert; Reihenfolge im Template (vereinheitlicht, b2): Default-Zeilen → Custom-Zeilen (`{{RELEASE_CUSTOM_CHECKLIST_BLOCK}}`, Z.65) → neuer Block (nach Z.65, vor `## 2.`). Keine Datenmigration.

### 18.3 Risiken
- R1: Template-Änderung propagiert in alle Projekte ⇒ Invariante AC-REL-1 als Pflichttest.
- R2: `strict` ist nur Prompt-Konvention (AZ2) ⇒ Doku/Manager/UI nennen das explizit.
- R3: `check: script` führt Befehle aus `project.yaml` aus ⇒ nur durch Agenten auf Projektrepo-Ebene, gleiche Vertrauensstufe wie `TEST_COMMANDS`/`BUILD_COMMANDS`; **keine Pfadprüfung** (b6, `script` ist eine Kommandozeile); Hinweis in Doku; Allowlist als Folge-Option F4. Skripte werden auch im Dry-Check ausgeführt und müssen seiteneffektfrei sein (b7); der Agent kann das nicht prüfen.
- R4: YAML-1.1-Bool-Falle ⇒ C6, AC-REL-3.
- R5: Admin-UI-Monolith (`admin-ui.html` ~11k Zeilen) ⇒ Scope-Creep; nur eine Sektion.
- R6: Standalone-Override `sharkord-release.md` erbt den Block nicht automatisch ⇒ IC-11 (b9).
- R7: Dateigrößen: `config.py` 2466, `variables.py` 796 Zeilen ⇒ Logik nur im neuen Modul (C4).
- R8: Der Worker kann mitten im Lauf nicht fragen ⇒ Freigabe nur über Stopp + Re-Dispatch (U9); Prompt-Konvention, kein technischer Zwang (AZ2).

### 18.4 Offene Fragen
- OF-1 (entschieden): Rendering im eigenen Modul `release_checklist.py` (CA7), Anschluss über `_build_convention_variables`.
- OF-2 (entschieden, b9): `sharkord-release.md` übernimmt den Block.
- OF-3 (entschieden, a3): Doku-Stelle `docs/guides/features/sync-concept.md:280`; keine CLAUDE.md-Variablentabelle.
- OF-4 (entschieden, a2): `config.py` liegt weit über 600 Zeilen; Logik im neuen Modul.
- OF-5 (entschieden, b3): ein Platzhalter.
- OF-6 (entschieden, a1): Registrierung `config.py:1442`/`:2293`.
- OF-7 (entschieden, Nutzer U10): `dod-met`/`readme-current` dürfen in `strict` mit einzeiliger Begründung `n/a` sein (§7.2, R-S9, AC-REL-25).
- OF-8 (offen, **für den Implementierer**, keine Nutzerfrage): Schreibt der YAML-Writer der Admin-UI `"off"` gequotet? Im Builder-Check nicht geprüft; Testfall im Admin-UI-Test, bei Abweichung Writer anpassen.

## 19. Acceptance Criteria

| ID | Kriterium (Given/When/Then) | Contract |
|---|---|---|
| AC-REL-1 | Given ein Projekt ohne `release-checklist`-Block (und mit `mode: off`), When Sync läuft, Then sind `release.md` und alle Overrides **byte-identisch** zum Stand vor der Änderung (abgesehen von Template-`version`/`based-on` im Frontmatter, sofern generiert); der `{{#if RELEASE_CHECKLIST_ENABLED}}`-Block hinterlässt keine zusätzliche Leerzeile. | IC-3,4,5,9 |
| AC-REL-2 | Given `mode` ∉ {off,advisory,strict}, When Config geladen wird, Then bricht der Sync im Python-Validator mit Fehlermeldung inkl. Schlüsselpfad ab (unabhängig davon, ob `jsonschema` installiert ist). | IC-2 |
| AC-REL-3 | Given `mode: off` ungequotet (YAML-Bool `False`), When Config geladen wird, Then wird er als `"off"` behandelt; Given `mode: on` (Bool `True`), Then Fehler mit Hinweis „quote the value". | IC-2 |
| AC-REL-4 | Given zwei Items mit gleicher `id` oder eine reservierte Default-ID, When Config geladen wird, Then Fehler. | IC-2,3 |
| AC-REL-5 | Given `check: script` ohne `script`, oder `check: agent` mit `script`, oder ein unbekannter Key im Block/Item, Then Fehler im Python-Validator. | IC-2 |
| AC-REL-6 | Given `mode: advisory` mit 2 Items, When Sync, Then enthält das generierte `release.md` die Modus-Prosa (Fail einer Vorbedingung ⇒ `APPROVAL_REQUEST`, Freigabe über `main_chat`), beide Items in der Tabelle und den Ergebnis-Contract (§10.3). | IC-4,9 |
| AC-REL-7 | Given `mode: strict`, When Sync, Then enthält `release.md` die Regel „Nicht-Pass eines Pflichtpunkts ⇒ STATUS failed, keine Mutation, kein Tag/Push" und nennt „Prompt-/Konventions-Boundary". | IC-4,9 |
| AC-REL-8 | Given `strict`, Then erlaubt der Block `n/a` nur für Items mit `applies-when`, für die Default-Punkte `dod-met`/`readme-current` (mit Begründung, AC-REL-25) und `n/a (nicht ausgeführt)` für Schritte im Dry-Check; für alle anderen Punkte nicht. | IC-4 |
| AC-REL-9 | Given `check: script`, Then beschreibt der Block „Exit 0 = pass, ≠0 = fail, fehlendes Skript = fail" und „Skripte müssen seiteneffektfrei sein". | IC-4 |
| AC-REL-10 | Given der Befehl `/release-check`, Then existiert `commands/1-generic/release-check.md` und weist `MODE: check-only` an; die Datei verbietet Tag, Push, Build, Version-Bump, Edit, Commit ausdrücklich. | IC-12 |
| AC-REL-11 | Given `mode != off`, Then beschreibt `release.md` den `check-only`-Ablauf (§10.4) und die Ergebnis-Statuszuordnung. | IC-4 |
| AC-REL-12 | Given `hacs-release` mit neuem Basis-Stand, When Sync, Then rendert er fehlerfrei; `based-on` verweist auf `@1.13.0`; Patch-Anker `<persona>` wird aufgelöst. | IC-10 |
| AC-REL-13 | Given `PROJECT_WRITABLE_SECTIONS`, Then enthält sie `"release-checklist"`; Given PUT auf `/api/config/project/section` mit gültiger Payload, Then wird `project.yaml` geschrieben; Given ungültigem Modus, `True`, unbekanntem Key oder doppelter `id`, Then liefert der neue Section-Guard (`_write_project_section`, Validator aus `release_checklist.py`) HTTP 400 und schreibt nichts. | IC-15,15b |
| AC-REL-14 | Given Admin-UI, Then existieren View, Nav-Eintrag, `routeMap`-Eintrag und Help-ID, und `check_ui_help_mappings` meldet keinen Fehler. | IC-16 |
| AC-REL-15 | Given gleiche Eingabe über Manager-Rezept und UI, Then ist das resultierende `release-checklist`-Fragment identisch (Parität). | IC-14,16 |
| AC-REL-16 | Given `agent-meta-manager.md`, Then enthält er den Rezeptabschnitt und die §3-Bestätigung für `strict` (ohne Hinweis „Gates werden weicher"). | IC-14 |
| AC-REL-17 | Given neue Platzhalter, Then sind sie über `config.py` (`_SET`-Muster/`_build_convention_variables`), `consistency/placeholders.py`, `standalone.py` (`_CONDITIONAL_FALSE_FLAGS`, Fallback `""`), die Whitelist in `variables.py` und `docs/guides/features/sync-concept.md` registriert und `python3 scripts/sync.py --validate` meldet keine ungelösten Platzhalter. | IC-5,6,6b,8 |
| AC-REL-18 | Given die Szenarien in `tests/scenarios/`, When `tests/scenarios/run.sh` läuft, Then bestehen `-off`, `-advisory`, `-strict`. | §17 |
| AC-REL-19 | Given alle **neuen** Module (`scripts/lib/release_checklist.py`), Then ist jedes <= 600 Zeilen und läuft unter Python 3.9 (nur stdlib); bestehende Module (`config.py`, `variables.py`, `standalone.py`, `admin-server.py`) wachsen nur um Aufruf-/Registrierungs-/Guard-Zeilen, keine neue Logik darin. | C1,C4 |
| AC-REL-20 | Given die Doku, Then nennen `docs/RELEASE_GATES.md` und `CHANGELOG.md` den Modus und die Boundary-Einschränkung; Folge-Optionen F1/F2 sind dokumentiert; `docs/RELEASE_GATES.md` enthält den Satz zum Dry-Check gegen Test-Umgebungen (nur `access: read`). | §15,18.1 |
| AC-REL-21 | Given `mode != off`, Then enthält `release.md` die Klassen **Vorbedingung** (`tests-green`, `dod-met`, `changelog-updated`, `readme-current`) und **Schritt** (`version-bumped`, `build-created`, `git-tag-push`), das Item-Feld `phase` (`precondition\|step`, Default `precondition`) ist im Schema und Validator definiert, und die Ergebnistabelle hat die Spalte `phase`. Ein Test prüft die Konstante `RESERVED_DEFAULT_ITEMS` gegen die Template-Zeilenzahl; das Flag `na_allowed_with_reason` ist genau für `dod-met` und `readme-current` `True`, sonst `False`. | IC-3,4 |
| AC-REL-22 | Given `mode` ∈ {off, advisory, strict} und Gate-Exit≠0 (Schritt 0), Then lautet die Vorgabe im Template in jedem Modus `STATUS: failed`; der Block für advisory/strict enthält keinen Satz, der Gate-Fehler „nicht blockierend" macht. | IC-4,9 |
| AC-REL-23 | Given `mode != off`, Then enthält der Block das Freigabeprotokoll: Stopp VOR der ersten Mutation (Bump, CHANGELOG-Edit, Tag, Push) mit `STATUS: partial` + `APPROVAL_REQUEST: <Aktion/IDs>`, Re-Dispatch mit `APPROVED: <Aktion/IDs>`, Freigabe gilt nur für die genannte Aktion; der Return-Contract nennt das Feld `APPROVAL_REQUEST` (Template-Text-Asserts). | IC-4,9 |
| AC-REL-24 | Given `mode: strict` und `MODE: check-only`, Then enthält der Block die Regel, dass `phase: step`-Punkte `n/a (nicht ausgeführt)` sind, nicht in `required_failed` eingehen und `STATUS` nicht auf `failed` setzen; `CHECKLIST_SUMMARY` führt `not_run`. | IC-4 |
| AC-REL-25 | Given `mode: strict` und ein Projekt mit inaktivem Validator bzw. deaktiviertem CODEBASE_OVERVIEW, When der Release-Agent `dod-met` bzw. `readme-current` als `n/a` mit einzeiliger Begründung ausweist, Then wird das akzeptiert (kein `required_failed`, `STATUS` nicht allein deshalb `failed`); Given `n/a` ohne Begründung, Then wird der Punkt als `fail` gewertet (`STATUS: failed`); Given `n/a` für `tests-green`, `changelog-updated` oder ein eigenes Item ohne `applies-when`, Then wird es als `fail` gewertet. Der Block enthält diese Regel und nennt die Spalte `reason` bei `n/a` als Pflicht (Template-Text-Asserts). | IC-3,4 |

## 20. Aufwandsschätzung und Task-Schnitt (nur Liste, kein Plan)

| Paket | Inhalt | Größe |
|---|---|---|
| WP1 | Schema + `release_checklist.py` Normalizer/Validator (IC-1,2) + Schema-/Validierungstests | S |
| WP2 | `release_checklist.py` Resolver + Renderer (Phasen, Freigabeprotokoll-Texte), Platzhalter-Registrierung (config.py-Aufrufe, Whitelist, placeholders.py, standalone.py, sync-concept.md; IC-3..8) + Lib-/Consistency-Tests | M |
| WP3 | Template `release.md` + Override-Nachzug inkl. Sharkord-Block (IC-9..11) + Render-/Byte-identisch-/Template-Text-Tests | M |
| WP4 | Command(s) `release-check` (+ optional `set-release-checklist`) | S |
| WP5 | `agent-meta-manager` Rezept (IC-14) | S |
| WP6 | Admin-UI Sektion + Whitelist + **neuer Section-Guard in `_write_project_section`** + Help + Tests (IC-15,15b,16) | M |
| WP7 | Szenarien + Doku (inkl. RELEASE_GATES-Satz) + CHANGELOG + Skills | S |

Entfallen/vereinfacht gegenüber rev 1.0: kein separater Result-Platzhalter, kein CLAUDE.md-Variablentabellen-Eintrag. Neu: Section-Guard (WP6), Phasen- und Freigabeprotokoll-Texte (WP2/WP3), Sharkord-Block (WP3).

Gesamt: **L** (ca. 22-27 Dateien). Vorschlag Task-Folge: WP1 → WP2 → WP3 → WP4 → WP5 → WP6 → WP7 (WP4/WP5 parallelisierbar nach WP3).

## 21. Review-Hinweise für den Nutzer (nur Calls des Autors)

- CA1: Blockform mit zusätzlichem Item-Feld `phase`; `verification` bleibt auch bei Skript-Items Pflicht.
- CA2: Modus-Muster von `subagent_permissions`, aber Normalizer nur `False`→`"off"` (b1).
- CA3: Default-Items bleiben im Template (`release.md:58-64`); `items` erweitern sie.
- CA4: Gates bleiben in jedem Modus hart (setzt Ihre Entscheidung C-2 um).
- CA5: Semantik-Tabelle §10.2/§10.3 inkl. Phasen, `not_run`-Zähler und Freigabeprotokoll als Template-Text.
- CA6: Dry-Check über `MODE: check-only` + `/release-check`; bei `off` Default-Umfang.
- CA7: Eigenes Modul `release_checklist.py` mit einem Platzhalter `{{RELEASE_CHECKLIST_BLOCK}}`.
- CA8: `check: script` ohne Allowlist und ohne Pfadprüfung (b6), Skripte müssen seiteneffektfrei sein (b7).
- b2: Block in `{{#if RELEASE_CHECKLIST_ENABLED}}` nach Z.65, vor `## 2.`.
- b4: Präfix `RELEASE_CHECKLIST_` in die Whitelist und `standalone.py`-Fallback.
- b8: Neuer Section-Guard im Admin-Server statt Schema-Annahme.
- b9: `sharkord-release` übernimmt den Block (vor „## Checkliste vor Release").
- b10: Konstante reservierter Default-IDs plus Template-Zeilenzahl-Test.
- b22: Manager-Version 1.26.0 (Spec 2 danach 1.27.0).
- Entschieden (Nutzer U10, kein Call): `dod-met`/`readme-current` in `strict` `n/a` mit einzeiliger Begründung; Eigenschaft `na-allowed-with-reason` nur in `RESERVED_DEFAULT_ITEMS`, nicht im Schema für Nutzer-Items.
- Für den Implementierer (keine Nutzerfrage): OF-8 (YAML-Writer-Quoting von `"off"`).

---
Trace-Anker: spec-id: SPEC-RELEASE-CHECKLIST-2026-10-31
