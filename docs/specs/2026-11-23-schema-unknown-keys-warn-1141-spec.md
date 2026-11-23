---
spec-id: SPEC-schema-unknown-keys-warn-1141
status: APPROVED
approval: "User, 2026-11-23, generelle Freigabe (Bug-Welle)"
---

# Unknown top-level config keys → WARNING (#1141) — Spec
> Status: APPROVED (User, 2026-11-23, generelle Freigabe)

## Problem / Ziel / Nicht-Ziele

**Problem (Issue #1141, wörtliche Evidenz):**
> The project config schema (`config/project-config.schema.json`) has top-level `additionalProperties: true`. Unknown or misspelled top-level keys in `.meta-config/project.yaml` are accepted silently, and the default value applies without any warning.
> Example: a typo such as `dod-presett` or `orchestator` is ignored. `python3 scripts/sync.py --validate` and `--audit-config` both pass.

Vom Issue genannte, in `properties` fehlende Keys: `rules-preset`, `test-repo`, `backup`, `mcp` (Top-Level; `:2544` ist verschachtelt/nested), `_comment`. Motivation laut Issue: stille Annahme eines Tippfehlers ⇒ Config-Änderung wirkt nicht, niemand merkt es; gleiche Fehlerklasse wie #1091.

**Ziel:** `--validate` (und der gemeinsame Audit-Pfad) melden unbekannte **Top-Level**-Keys als `config.unknown-key`-**WARNING** inkl. „did you mean"-Vorschlag (Edit-Distanz zu bekannten Keys). Feynman muss im Output sichtbar, aber nicht fatal sein.

**Nicht-Ziele (decisive user constraint, 23.11):**
- **WARN-ONLY, KEIN harter Fehler.** Unbekannte Top-Level-Keys erzeugen ausschließlich eine Warnung. Kein `rc != 0`, kein `sys.exit`, kein Abbruch von `--validate` oder `--audit-config`. Kein Breaking Change für Consumer.
- **KEIN `additionalProperties: false`** auf Top-Level (Issue-Option 2 wird explizit NICHT gewählt). Das Schema bleibt `true`; die Warnung kommt aus dem Validierungscode, nicht aus JSON-Schema-Fail-Closed.
- Keine Änderung am #1091-Fail-safe (`auto_commit` bleibt eigenständig; kein „fail-safe"-Umbau, keine Verschärfung).
- Keine neue strikte/strict-Mode-Konfiguration, keine Provider-Verzweigung (`if provider == ...`), kein `#1199`- writable-sections-Verhalten (T22 schema-derived whitelist bleibt Follow-up).
- Keine Implementierung in diesem Schritt.

## Interface Contracts

Alle Anker gegen Referenz-Commit `e29381db` neu gemessen (lokaler Checkout `fix/bug-wave2-20261123`; Abweichungen als offene Frage Q2 flaggen).

| Datei:Symbol | Signatur / Typ | Rolle & Fehlerpfad |
|---|---|---|
| `config/project-config.schema.json:3089` | `"additionalProperties": true` (Top-Level, nach `required: ["project"]` bei `:3086`) | Bleibt **unverändert** — kein `false`. Einzige autoritative Liste bekannter Keys ist `properties` (`:7`). |
| `config/project-config.schema.json:7` (`properties`) | `object` | Um die vom Issue genannten, tatsächlich fehlenden Keys ergänzen (mit korrektem Typ): `rules-preset`, `test-repo`, `backup`, `mcp` (Top-Level; `:2544` ist verschachtelt/nested). `_comment` ist hier bereits vorhanden (`:12`) — nur verifizieren, nicht duplizieren. |
| `scripts/lib/cli_commands.py:1733` `_handle_validate_config_only()` | `-> None`; ruft `_handle_validate(ctx, source_checks=False)` (`:1735`) | Einziger Hook für `--validate-config-only`; unbekannt-Key-Warnung muss hier durchlaufen. Fehlerpfad: Warnung, rc bleibt 0. |
| `scripts/lib/cli_commands.py` `_handle_validate()` | `-> None` | Zentraler Validate-Pfad; ruft `audit_config(...)` (Aufruf bei `:1553`). Neue Kategorie hier als **WARN** einhängen, nicht als error. |
| `scripts/lib/cli_commands.py:810` `_handle_audit_config()` | `-> None`; `audit_config(agent_meta_root, config_path)` (`:823`) | `--audit-config` teilt denselben Audit-Pfad → Warnung erscheint auch dort, rc 0. |
| `scripts/lib/config_audit.py:239` `audit_config()` | `audit_config(agent_meta_root: Path, project_config_path: Path) -> AuditReport` | Neue Finding-Kategorie `unknown_keys` (Harmonisierung mit Issue-Vorschlag `config.unknown-key`), Severity `warning`, analog zu `deprecated_roles` (`:251`)..Config via `load_yaml_file(..., on_error="raise", default={})` (`:284`) — bekannte Keys = `schema.properties` (via `scripts/lib/schema.py:66/164` geladen). |
| `scripts/lib/config_audit.py` `AuditReport` / Kategorie-Tabelle (`:555`, `:587`) | finding: `category`, `severity: warning`, `message` | Warning-Format: `config.unknown-key: '<key>' — did you mean '<nearest>'?` Edit-Distanz gegen `schema.properties`-Keys; bei keinem Kandidaten Vorschlag weglassen. Fehlerpfad: ausschließlich Warnung, kein Exit. |
| `scripts/admin-server.py:239` `PROJECT_WRITABLE_SECTIONS` | `frozenset[str]` | Enthält `rules-preset`, `backup`, `mcp`-Umfeld bereits; wird als **zusätzliche** bekannte-Key-Quelle konsultiert (nicht als Ersatz für Schema-`properties`). Keine Änderung an dieser Menge (gehört #1186/T22 / #1199). |
| `tests/` (neue Regression) | `pytest`-Test | Fixture: `.meta-config/project.yaml` mit `dod-presett: full` → `audit_config`/`--validate` liefert genau 1 `unknown_keys`-Warnung mit `dod-preset`-Vorschlag, rc 0. Muster: bestehende `tests/test_config_audit*.py`. |

**Fehlerpfade konsolidiert:** unbekannter Key ⇒ `warning` + rc 0; Schema-Ladefehler ⇒ unveränderter bestehender Fehlerpfad; kein Kandidat für „did you mean" ⇒ Warnung ohne Vorschlag (nie `TBD`).

## Datenfluss

`.meta-config/project.yaml` (mit Tippfehler) → `load_yaml_file()` (`config_audit.py:284`) → bekannte Keys aus `config/project-config.schema.json:7 properties` (+ `admin-server.PROJECT_WRITABLE_SECTIONS`) → Differenz `set(config) - known` → Edit-Distanz-Vorschlag → `AuditReport`-Finding `config.unknown-key` severity `warning` → `--validate` / `--audit-config` geben Warnung auf stdout aus, **`rc = 0`** → keine Persistenz-Änderung, keine Generierungsänderung (Default-Verhalten bleibt wie bisher).

## Acceptance Criteria (nummeriert, testbar)

1. **AC-01 (Kern):** Given `.meta-config/project.yaml` mit `dod-presett: full`, When `python3 scripts/sync.py --validate` läuft, Then erscheint eine Warnung, die `dod-presett` als unbekannt markiert und `dod-preset` vorschlägt — und der Prozess endet mit **rc 0**. *(Karte: `config_audit.py:239`, `cli_commands.py:1733`.)*
2. **AC-02 (WARN-ONLY):** Given derselbe Tippfehler, When `--audit-config` läuft, Then wird dieselbe Warnung ausgegeben, es gibt **keinen** nonzero Exit-Code, keine Datei wird geändert und kein Consumer bricht ab. *(Karte: `cli_commands.py:810`.)*
3. **AC-03 (Schema unverändert):** Given `config/project-config.schema.json`, When geprüft wird, Then ist Top-Level `additionalProperties` weiterhin `true` (`:3089`) — kein `false`, kein Fail-Closed. *(Karte: `schema.json:3089`.)*
4. **AC-04 (Valide Keys):** Given das self-hostete `.meta-config/project.yaml` ohne Tippfehler, When `--validate`/`--audit-config` laufen, Then **keine** `config.unknown-key`-Warnung und rc 0 — die in `properties` ergänzten Keys `rules-preset`, `test-repo`, `backup`, `mcp` werden nicht mehr gemeldet. *(Karte: `schema.json:7`.)*
5. **AC-05 (Nested-Scope):** Given ein unbekannter Key **innerhalb** eines bekannten verschachtelten Objekts (z. B. `dod.typo`), When `--validate` läuft, Then wird **keine** `config.unknown-key`-Top-Level-Warnung erzeugt — der Spec ist bewusst auf Top-Level begrenzt (Issue-Caveat „nested not verified" bleibt offen, siehe Q1). *(Karte: `config_audit.py:239`.)*
6. **AC-06 (Regression):** Given der neue Test mit `orchestator`-Tippfehler, When `pytest` läuft, Then existiert genau 1 Finding mit severity `warning`, Vorschlag `orchestrator`, und der Test asserted rc 0 / keinen Error. *(Karte: `tests/`.)*
7. **AC-07 (Kein Breaking Change):** Given ein Producer, der heute einen unbekannten Top-Level-Key setzt und Default-Verhalten erhält, When nach dem Fix gesynct wird, Then bleibt das generierte Output unverändert; einzig neu ist die Warnung auf stdout. *(Karte: `cli_commands.py:1733`.)*

Jede AC mappt auf mindestens einen Interface-Contract (AC-01/02/07 → `config_audit.py:239`, `cli_commands.py:1733/810`; AC-03 → `schema.json:3089`; AC-04 → `schema.json:7`; AC-05 → `config_audit.py:239`; AC-06 → `tests/`).

## Offene Fragen + Risiken

- **Q1 (vom Issue selbst offen gelassen):** „Whether nested objects also use `additionalProperties: true` is not verified" und „further valid keys … not verified beyond the list above." Spec beschränkt sich auf Top-Level + die genannten Keys; eine vollständige Nested-Objekt-Prüfung ist bewusst **nicht** enthalten. Eskalation: separater Issue, falls gewünscht.
- **Q2 (Referenz-Drift):** Anker gegen `e29381db` gemessen; lokaler Branch ist `fix/bug-wave2-20261123`. Falls die Arbeitskopie von `e29381db` abweicht, sind Zeilennummern vor Implementierung erneut zu prüfen. `_comment` ist im lokalen Schema bereits vorhanden (`:12`), obwohl der Issue es als fehlend listet — kein Duplikat anlegen.
- **Q3 („did you mean"-Format):** Severity und Grundschema sind durch die User-Vorgabe (WARN) fixiert; die **exakte** Textform der Warnung (`config.unknown-key: ... did you mean ...?`) ist Implementierungsdetail und muss nicht mit #1091 identisch sein. Kein Strict-Mode einführen.
- **R1:** Warn-Müdigkeit — bei vielen Tippfehlern können viele Warnungen erscheinen; bewusst akzeptiert, da warn-only gefordert.
- **R2 (#1199-Überlappung):** `admin-server.PROJECT_WRITABLE_SECTIONS` (`:239`) ist handgepflegt; die schema-abgeleitete Whitelist ist T22/Follow-up. Dieser Fix darf daran **nichts** ändern.

## ADR (Entscheidungen dieses Specs)

- **ADR-1141-1 — Warn, never fail:** Kontext: Issue schlägt „warning or error" und alternativ `additionalProperties: false` vor; #1091 zeigt fail-safe-Präzedenz. Entscheidung: User-vorgabe warn-only — Warnung + rc 0, Schema bleibt `true`. Konsequenz: keinerlei Breaking Change; Tippfehler werden sichtbar, aber nicht blockiert.
- **ADR-1141-2 — Schema `properties` als Wahrheitsquelle:** Kontext: Admin-UI hat eigene Whitelist. Entscheidung: bekannte Keys primär aus `schema.json:7 properties`, admin-server-Whitelist ergänzend; keine Duplikat-Liste neu erfinden. Konsequenz: ein ergänzter Schema-Key wird automatisch als bekannt erkannt.

## Completeness Checklist

- [x] Pflicht-Sektionen vorhanden (Problem/Ziel/Nicht-Ziele, Interface Contracts, Datenfluss, AC, Offene Fragen+Risiken, Trace-Anker).
- [x] Jeder Interface fully typed (Signaturen + Fehlerpfade, keine `TBD`).
- [x] Jede AC testbar (Given/When/Then + Contract-Mapping).
- [x] Anker gegen `e29381db` neu gemessen (Q2 flaggt lokale Abweichung).
- [x] Provider-agnostisch (kein `if provider == ...`).
- [x] Warn-only constraint (kein `additionalProperties:false`, kein rc-Wechsel, kein Strict-Mode) in Ziel/Nicht-Ziel/AC/ADR verankert.

## Trace-Anker: spec-id: SPEC-schema-unknown-keys-warn-1141
