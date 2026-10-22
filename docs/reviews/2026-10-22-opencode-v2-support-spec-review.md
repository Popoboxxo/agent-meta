# Review: SPEC-OPENCODE-V2-SUPPORT-2026-10-22 (Rev. 1.0, Entwurf)

- **Gegenstand:** `docs/specs/2026-10-22-opencode-v2-support-spec.md` (444 Zeilen, vollständig gelesen)
- **Kontext:** `.tmp/opencode-v2-ctx.md` (bindende Entscheidungen 6-12); Abhängigkeit Spec A `docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md` (nur gelesen, IC-2..IC-7)
- **Reviewer:** concept-reviewer (Spec-Review-Modus), 2026-10-22
- **Verdikt:** **CHANGES_REQUESTED** — 2 BLOCKER, 7 MAJOR, 8 MINOR, 2 INFO
- **Nicht neu verhandelt:** Entscheidungen 6-12 als solche; Findings betreffen Ausgestaltung, Konsistenz mit Code und Spec A, Nachweisbarkeit.

## 1. Scope und Methode

- Formale Spec-Checks gegen `scripts/lib/consistency/spec_plan.py` (`REQUIRED_SPEC_SECTIONS` :31-35, `_PLACEHOLDER_PATTERNS` :88-97, `_APPROVED_RE` :85).
- Existenzprüfung aller referenzierten Pfade/Symbole im Code.
- Konsistenz mit Entscheidungen 6-12 und mit Spec A.
- Testbarkeit der ACs, Spike-Exit-Gate-Logik, Phasenabhängigkeiten, Querwirkung (AC-01/Goldens), Bedrohungsmodell.

### Formale Spec-Checks

| Check | Ergebnis |
|---|---|
| Pflichtsektionen (`## Problem`, `## Ziel`, `## Nicht-Ziele`, `## Interface Contracts`, `## Datenfluss`, `## Acceptance Criteria`, `## Offene Fragen`, `## Trace-Anker`) + `## Entscheidungsregister`, `## Risiken` | vorhanden |
| Trace-Anker `spec-id: SPEC-OPENCODE-V2-SUPPORT-2026-10-22` | vorhanden (Frontmatter, Kopf, Schluss); `requires-spec` auf Spec A gesetzt |
| Approval-Marker | `status: Entwurf` / `> Status: Entwurf` — konsistent; Schlusssatz (:443) matcht `_APPROVED_RE` nicht (Mid-Line), korrekt |
| No-Placeholder | keine Treffer für TODO/TBD/`<platzhalter>`/`...`; inhaltlich offen: Registry-Pfad in 3.5 (m-4), `{…}` in AC-B10/AC-D7 (m-5) |

### Verifizierte Symbole (existieren wie referenziert)

`providers._apply_project_surface_overrides` (:148), `_SURFACE_OVERRIDE_KEYS` (:139), `_apply_surface_format_selection` (:53), `_apply_surface_mechanism_selection` (:89), `load_providers_config` (:231), `provider_runtime_gate_tier` (:656); `mcp_provider_config._build_connection_entry` (:92, `enabled=True` :139-140), `_update_opencode_v2_json_config` (:309), `_write_json_config` (:235), `_write_provider_config` (:732); `runtime_gate.py` (Protokoll-Map :93-95, `_baked_plugin_mode` :123, `runtime_gate_plugin_relpath` :107); `templates/plugins/runtime-gate.opencode-plugin.js.tmpl`; `artifact_validate.validate_frontmatter` (:131), `_validate_opencode_v2` (:275), Kommentar IC-15 Nr. 16 (:48-49); `context.apply_settings_surface_shape` (:1644), `_init_provider_settings_json` (:1683); `isolation._read_json_safe`/`_read_state`/`_write_state` (:155/:179/:191); `consistency/artifact_contracts.check_artifact_contracts` (:64), `consistency/model_contracts.py`; Schema `provider-options.Opencode.surface-version` (:864); Scenario-69-Assert (:173); Szenario 79 frei (höchste Config 78).

Abweichungen von Symbolnamen/Pfaden: siehe m-2, m-3, m-4.

## 2. Findings

### BLOCKER

**B-1 (Logik/Risiken): Gate-Plugin C3 schwächt im GO-Fall das Gate und bricht den v1-Freeze**
- Fundstelle: 3.6 Task C3, AC-C12, AC-C13; Code `providers.py:653` (`provider_runtime_gate_supported`), `:611` (`SUPPORTED_PLUGIN_PROTOCOLS = {"opencode-plugin-js"}`), `sync_pipeline.py:1308`, `isolation.py:400` (Tier-Check in `_opencode_runtime_gate_entries`), `runtime_gate.py:123` (nur `observe`).
- Begründung:
  1. Sobald `provider_runtime_gate_tier` `plugin` liefert, ruft `sync_pipeline.py:1308` den Permission-Writer nicht mehr auf, und `_opencode_runtime_gate_entries` liefert `[]`. Das Plugin ist laut Spec und Code nur `MODE=observe` (blockiert nie). Ergebnis: Der GO-Fall ersetzt ein wirksames Deny (C1) durch ein nicht blockierendes Plugin — Netto-Verlust an Durchsetzung.
  2. `has_plugins` ist ein statischer Registry-Key, kein Surface-Key. `has_plugins: true` schaltet auch v1-Projekte auf Tier `plugin` (Protokoll `opencode-plugin-js` ist in `SUPPORTED_PLUGIN_PROTOCOLS`). AC-C12 („v1-Projekt erzeugt keine v2-Plugin-Datei") verschweigt, dass v1 dann die v1-Plugin-Datei und Tier `plugin` bekommt — Bruch von Ziel 1/Entscheidung 8.
  3. `SUPPORTED_PLUGIN_PROTOCOLS` muss für `opencode-plugin-v2-js` erweitert werden; die Spec nennt das nicht (sonst bleibt der Tier auch bei GO `permission`, AC-C12 schlägt fehl).
- Korrektur: (a) Surface-abhängige Capability (`surface-has-plugins: {v2: true}`) in `_apply_surface_aux_selection` auflösen; statisches `has_plugins` bleibt `false`. (b) Solange `_baked_plugin_mode` nur `observe` liefert, bleibt das C1-Deny aktiv (Plugin additiv; entweder Aufrufbedingung von `_sync_opencode_v2_gate_permissions` vom Tier `permission` entkoppeln oder Tier-Wechsel erst bei Enforce-Freigabe). (c) Erweiterung von `SUPPORTED_PLUGIN_PROTOCOLS` als expliziten Vertrag in 3.6 aufnehmen. (d) AC-C12 um „v1-Projekt: Tier bleibt `permission`, keine Plugin-Datei" und „v2: Deny-Tripel bleiben bei Tier `plugin`+`observe` erhalten" ergänzen.

**B-2 (Konsistenz mit Spec A / Entscheidungen 2-4): v2-Zweig umgeht die Spec-A-Verträge**
- Fundstelle: 3.4 („dünner Zweig am Funktionsanfang"), 3.7 Signatur `_transform_frontmatter_for_opencode_v2`; Spec A IC-3, IC-4, IC-6 Schritte 2-3.
- Begründung:
  1. `_opencode_v2_gate_permissions` übernimmt nur „Tier + strict + v2_active", nicht die Einstiegspunkt-Kopplung aus Spec A IC-6 Schritt 2 (Deny nur bei explizitem und generiertem `primary-role`, Entscheidung 2). Auf v2 ohne generierte Primary-Rolle würde das Gate alle Agenten sperren.
  2. Der Early-Branch „`if v2_active(...)` → v2-Schreiber" lässt offen, ob Spec A Schritt 3 (`default_agent`-Managed-Merge mit State `default-agent`, Entscheidung 3) auf v2 noch läuft. Bei wörtlicher Umsetzung entfällt er auf v2.
  3. Die v2-Frontmatter-Funktion hat kein `deny_edit` (Spec A IC-3, Entscheidung 4). Mit der Default-Annahme OQ-B5 „Agent-Ebene übersteuert global" neutralisiert das `edit: allow` des Orchestrators das globale Deny — genau der #1006-Fehler, jetzt auf v2.
- Korrektur: In 3.4 normativ festlegen: v2-Zweig ersetzt nur Spec-A-Schritt 4 (`permission`-Merge); Schritte 1-3 und 5 laufen unverändert; Einträge = effektive Entries nach Spec-A-Kopplung. In 3.7 Parameter `deny_edit: bool = False` mit identischer Semantik aufnehmen (Primary-Rolle → `{action: edit, effect: deny}`). ACs ergänzen: v2 strict ohne Primary-Rolle → kein Tripel + WARNING; v2 `default_agent`-Merge wie Spec AC-06…09; v2-Orchestrator-Artefakt trägt `edit deny` bei aktivem Gate.

### MAJOR

**M-1 (Konsistenz, Entscheidung 6): Abweichung von bindender Entscheidung als Offene Frage mit Default getarnt**
- Fundstelle: 3.1 „Schalter (bestehend, wiederverwendet)", Entscheidungsregister Nr. 6, OQ-B1.
- Begründung: Entscheidung 6 verlangt einen *neuen* Projekt-Level-Schalter. Die Spec verwendet den bestehenden `provider-options.Opencode.surface-version` (Schema :864, Resolver :148, Scenario 69). Inhaltlich ist das tragfähig: Der Schalter ist projektlevel, im Schema und in `project.yaml`, opt-in, Default v1; ein zweiter Schalter würde zwei Wahrheiten erzeugen. Formal verletzt die Spec den Wortlaut aber. Laut Kopf von „Offene Fragen" folgt die Umsetzung dem Default, bis der Nutzer widerspricht. Damit überstimmt eine Default-Annahme eine bindende Nutzerentscheidung.
- Korrektur: Im Entscheidungsregister als **„Abweichung A-6 (Nutzerbestätigung erforderlich)"** führen, mit Begründung und Evidenz. OQ-B1 als **Freigabe-Gate** markieren: Ohne Nutzerbestätigung kein `Status: APPROVED`. Kein Default-Fortschritt. Alternative für den Fall „Nein": Alias-Key definieren, der auf `surface-version` normalisiert (eine Wahrheit).

**M-2 (Annahmen/Risiken): Phase-B-Keys sind weder dokumentiert noch im Spike enthalten**
- Fundstelle: 3.2/3.3, AC-B1, B3, B9, B10, D7; `docs/analysis/2026-09-30-provider-audit-docs-part1.md` §4.1 (:243-244), `…runtime-consolidation.md:106`.
- Begründung: Die DOKU-Quelle der Spec listet als v2-Config-Keys nur `agents`, `permissions`, `default_agent`, `mcp.servers`, `commands`, `skills`, `instructions`, `experimental.policies`. Nicht belegt sind `experimental.subagent_depth`, `experimental.todo`, `providers`, `agents.title.model` und `cli.json`. Die Analyse empfiehlt für `subagent_depth` „replace with `subagent` permission gating", nicht `experimental.subagent_depth`. Phase B entfernt das Top-Level-`subagent_depth` und schreibt unverifizierte Keys. v2 verwirft unbekannte Keys still (N6), d. h. die Regression wäre unsichtbar. Zudem kehrt die Spec die frühere Festlegung IC-15 Nr. 16 um, ohne formales Amendment an der `builds-on`-Spec.
- Korrektur: Spike-Frage Q6 „Phase-B-Keys" (je Key: `opencode debug config`-Auflösung auf v2, Marker VERIFIED/DOKU) aufnehmen und **C0 vor B** ziehen, oder einen Evidenz-Task als ersten B-Task anlegen. Bei negativem Ergebnis für einen Key: Key entfällt per Amendment B1. Für `subagent_depth` die Ersatzstrategie (Key vs. `subagent`-Permission) explizit entscheiden. IC-15-Nr.-16-Umkehr als Amendment-Querverweis in `docs/specs/2026-09-30-provider-audit-opencode-v2*.md` aufnehmen.

**M-3 (Logik, Entscheidung 7): MCP ist kein Managed-Merge; Rückwechsel und User-Einträge sind ungedeckt**
- Fundstelle: 3.2 Regel 5 und 8, 3.5, AC-B4, AC-B7, AC-C7, R-5; Code `mcp_provider_config.py:280` (`existing[mcp_key] = mcp_entries`), `:330` (`existing["mcp"] = {"servers": …}`), `:617-619` (früher Return ohne aktive Server).
- Begründung:
  1. Beide Opencode-MCP-Writer ersetzen `mcp` vollständig. User-MCP-Einträge („`mcp`-Fremdeintrag", AC-B4, Entscheidung 7) gehen bei jedem Sync verloren. AC-B4 ist nur grün, wenn man den MCP-Writer ausklammert.
  2. Regel 8 verlässt sich darauf, dass der v1-Writer `mcp` flach neu schreibt. Ohne aktive Server kehrt `_write_provider_config` früh zurück (:618-619): `mcp.servers` bleibt nach v2→v1 stehen. Das ist genau R-5, das damit nicht gemindert ist.
  3. „Ein von agent-meta geschriebenes `mcp.servers`" ist nicht feststellbar, weil für MCP kein State existiert.
  4. AC-C7 „deaktivierter Server trägt `disabled: true`": Es werden nur aktive Server emittiert (`resolve_active_mcp_servers`). Für „deaktiviert" gibt es keine Quelle, die AC-Hälfte ist nicht testbar.
- Korrektur: Managed-Pfade je Server `mcp.servers.<name>` bzw. `mcp.<name>` mit State im Managed-Namespace. Rückwechsel und Bereinigung unabhängig von aktiven Servern in `opencode_v2_config` ausführen. Fremdeinträge erhalten. `disabled`: Quelle definieren (z. B. Plugin-Katalog `enabled: false` bei aktivem Projekt-Eintrag) oder streichen. AC für „v2→v1 ohne aktive Server" ergänzen.

**M-4 (Logik/Feasibility): Spike-Exit-Gate deckt nur C3 ab; Phasenabhängigkeit C0 ist falsch begründet**
- Fundstelle: 3.0 (C0 „hängt ab von B: Datei-Konflikte isolation.py"), 3.6 Exit-Gate, 3.5 (C0 → C2), 3.7 (Q5 → D1).
- Begründung: GO/NO-GO bewertet nur Q1-Q3. Q5 gated jedoch C2 und D1 (und nach M-2 auch B), ohne Entscheidungsregel (was gilt bei „Q5 unbeantwortet"?). Der Spike schreibt nur `docs/spikes/…`. Ein Datei-Konflikt mit `isolation.py` existiert nicht, die Abhängigkeit C0 → B ist unbegründet und verzögert die Evidenz, die B/C2/D1 brauchen. Die Zeitbox „4 Stunden Arbeitszeit" ist für einen Agenten-Task nicht messbar.
- Korrektur: C0 als erste Phase nach A (parallel zu A zulässig). Ergebnis-Tabelle je Frage mit Folge: Q1-Q3 → `VERDICT-C3: GO|NO-GO`; Q5/Q6 → `VERDICT-FIELDS: CONFIRMED|AMEND` (AMEND = Amendment B1 vor C2/D1/B). Zeitbox als messbares Kriterium (z. B. max. N Probe-Läufe/Quellen oder ein Plan-Task ohne Re-Dispatch). AC-C1 auf beide Verdict-Zeilen anpassen.

**M-5 (Risiken/Bedrohungsmodell): v2-Agent-Permissions sind open-world; Rechteausweitung möglich**
- Fundstelle: 3.7 `map_tools_to_opencode_v2_permissions`, AC-D1; Code `provider_transform.py:703-751`, `:840` (`opencode_deny_critical`).
- Begründung: Der Builder lässt Tools ohne Mapping aus und emittiert für nicht gewährte Aktionen nur Einträge aus `deny_list` „analog v1". Der v2-Default-Effekt für nicht gelistete Aktionen ist UNVERIFIED. Ist er `allow`, erhalten Read-only-Rollen (z. B. `code-reviewer` ohne `Write`) `edit`/`shell`/`subagent`. Zudem nutzt das Agent-Ressourcenmuster `"*"`, das globale Gate `"**"` — die Matching-Semantik ist ungeklärt (OQ-B5) und kann Override-Verhalten verändern.
- Korrektur: Closed-world-Vertrag: Für jede Aktion in `{edit, shell, subagent}` genau ein Eintrag (`allow` bei Mapping, sonst `deny`), unabhängig von `opencode_deny_critical`. Ressourcenmuster vereinheitlichen oder per Spike Q3 begründen. AC-D1 um „Rolle ohne `Write`/`Edit` hat `{action: edit, effect: deny}`" ergänzen.

**M-6 (Logik): Aufrufbedingung der neuen Writer übernimmt das Tier-Gate**
- Fundstelle: 3.2 (`sync_opencode_v2_managed_keys` „direkt nach `_sync_opencode_runtime_gate`, gleiche Aufrufer"), 3.8; Code `sync_pipeline.py:1308-1312`, `cli_commands.py:283-287`.
- Begründung: Der Aufruf des Runtime-Gates steht in `if provider_runtime_gate_tier(pc, caps) == "permission"`. An dieser Stelle laufen `experimental.*`, `providers`, `agents.title.model`, `cli.json` und deren Rollback nur bei Tier `permission`. Das fachfremde Kopplung; bei Tier `plugin` (C3) oder `advisory` fehlen Keys bzw. bleibt der Rückbau aus. Für Regel 4 (v1-Rückbau) muss der Writer auch auf v1-Projekten laufen.
- Korrektur: Eigener, tier-unabhängiger Aufruf je aktivem Provider. Die Funktion ist ein No-op ohne `v2_active` und ohne State. Bedingung provider-agnostisch (kein Providername) im Vertrag festschreiben.

**M-7 (Logik): State-Namespace `opencode-v2-managed` ist mit dem bestehenden State-API nicht nutzbar und wird von drei Writern geteilt**
- Fundstelle: 3.2 (`MANAGED_STATE_KEY`), 3.4 (Unterbaum `permissions`), 3.8 (Unterbaum `cli.json`), B-D2; Code `isolation.py:179-188` (`_read_state`: `dict` nur für `runtime-gate-deny`, sonst `list`), `:191-203` (`_write_state` ersetzt den ganzen Key).
- Begründung: `_read_state(…, "opencode-v2-managed")` liefert `[]`, weil der Namespace kein dict-Key ist (Spec A erweitert die dict-Liste nur um `default-agent`). Folge: Der State ist immer leer, Regel 2/4 greifen nie, jeder Wert gilt ab dem zweiten Lauf als User-Wert (Regel 3), Rückbau ist unmöglich. Drei Writer (`isolation._sync_opencode_v2_gate_permissions`, `sync_opencode_v2_managed_keys`, `sync_opencode_cli_file`) schreiben zudem per Read-modify-write denselben Namespace. Der letzte Writer überschreibt die Teilbäume der anderen. Das widerspricht B-D2/IC-09 („ein Namespace je Writer").
- Korrektur: Drei Namespaces (`opencode-v2-keys`, `opencode-v2-permissions`, `opencode-v2-cli`) oder ein Writer-Modul mit einem Schreibzugriff pro Sync. `_read_state` um die neuen dict-Keys erweitern (Spec-A-Muster). AC „Namespaces clobbern sich nicht" analog Spec A ergänzen.

### MINOR

- **m-1 (Logik) Merge-Regel 3 unvollständig/mehrdeutig:** Fall `C == T` ohne State (User-Wert gleich Zielwert) ist ungeregelt → Warnung in jedem Lauf; Formulierung „`C != S[P]` und `P in S` oder `P not in S` mit `C` vorhanden" ist klammerlos mehrdeutig. Fix: Spec-A-Muster (`{value, prior}`) übernehmen: `C == T` ohne State → State `{value: T, prior: T}`, Rückbau stellt `prior` wieder her; Regeln als Entscheidungstabelle.
- **m-2 (Konsistenz) Symbol- und Dateinamen:** `_PLUGIN_TEMPLATES` existiert nicht (Ist: `PLUGIN_TEMPLATE_BY_PROTOCOL`, `runtime_gate.py:93`). AC-C12 nennt `.opencode/plugins/runtime-gate.js`; `runtime_gate_plugin_relpath` liefert `agent-meta-runtime-gate.js` (`PLUGIN_STEM`, :97). Fix: Namen korrigieren.
- **m-3 (Testbarkeit) AC-C11 referenziert nicht existierende Tests** `tests/test_mcp_provider_config*.py`. Ist: `tests/test_mcp_config.py`. Fix: Pfad korrigieren, plus expliziter Byte-Vergleichstest für v1.
- **m-4 (Vollständigkeit) Registry-Pfad in 3.5 offen gelassen** („im Plan zu bestätigen"). Ist bekannt: `config/plugin-catalog.yaml` via `registry_query.load_mcp_registry` (:119). Fix: Pfad und Schema-Stelle für `timeout`/`oauth` konkret benennen.
- **m-5 (Testbarkeit) AC-Zählung und Präzision:** Die Spec enthält **44** ACs (B1-B15, C1-C13, D1-D10, T1-T6), nicht 47. AC-C2 („Plan enthält keinen offenen C3-Task") ist ein Prozess-, kein Testkriterium. `{…}` in AC-B10/AC-D7 durch konkrete Fixture-Werte ersetzen.
- **m-6 (Querwirkung) Baseline von AC-T4 unklar:** `tests/test_ac01_render_identity.py` enthält Opencode-Artefakte (:194). Spec A ändert diese bei v1 (mode/deny_edit). Fix: „Baseline = Fixture-Stand nach Spec-A-Merge; Spec B ändert keine Fixture" explizit; Lab-Diff (AC-T2) gegen v1 nach Spec A.
- **m-7 (Risiken) Secret-Gate-Lücken:** `write_checked` überspringt im `dry_run` den Secret-Scan (`io.py:479-483`), AC-B10/AC-C9 greifen dort nicht. Musterbasierter Scan erkennt Klartext in `providers.<id>.options.apiKey` ggf. nicht. Fix: Zusatzregel „Werte unter Schlüsseln `*key*|*secret*|*token*` in `providers`/`oauth` müssen `{env:VAR}` sein, sonst Fehler", auch im dry-run als Finding.
- **m-8 (Konsistenz) 3.9 Duplikat-Check widersprüchlich formuliert:** „aufgelöste Opencode-`settings_file`" vs. „über `settings_file` aller Provider". Fix: provider-agnostische Variante (alle aktiven Provider) festschreiben; AC-D9 entsprechend.

### INFO

- **i-1:** Schema-Erweiterung des Opencode-Blocks (`additionalProperties: false`) berührt die Admin-UI-Provider-Options (Amendment 2026-10-03). Im Plan prüfen, ob der Admin-Server Keys allow-listet. Nicht-Ziel ist ausreichend, wenn ein Test „unbekannte Keys werden durchgereicht" existiert.
- **i-2:** Mammouth-Isolation (AC-D6, B-D5) ist durch den Mechanismus-Dispatch (`provider_transform.py:384`, neuer v2-Zweig nur bei `opencode-native-v2`) schlüssig. Mammouth hat keine `surface-mechanisms`, der Resolver lässt es auf `opencode-native`.

## 3. Bedrohungsmodell (internes Dev-Tool, verkürzt)

1. **Was wird gebaut?** Ein Writer, der die committete `opencode.json`/`cli.json` und Agent-Permissions erzeugt; die Permissions sind eine Convention Boundary (Gate gegen akzidentelle Edits des Main Chats).
2. **Was kann schiefgehen?** Gate wirkungslos (B-1, B-2, M-5), Read-only-Rollen erhalten Schreib-/Shell-Rechte (M-5), Secrets im Klartext in committeter Config (m-7), User-Config geht verloren (M-3), Prompt-Injection über Spike-Quellen (R-11, abgedeckt).
3. **Gegenmaßnahmen:** Siehe Korrekturen. Die Spec deckt Secrets und Injection teilweise ab, Rechteausweitung gar nicht.
4. **Folgen:** Stilles Versagen des Gates (v2 verwirft unbekannte Keys ohne Fehler, N6). Sicherheitswirkung niedrig bis mittel (Convention Boundary), Datenverlust bei User-MCP-Einträgen real.

## 4. Verdikt und Begründung

**CHANGES_REQUESTED.** Die Spec ist formal vollständig, gut evidenzmarkiert und überwiegend code-genau. Die Phasen- und Spike-Struktur setzt Entscheidung 9 korrekt um. Nicht tragfähig in der jetzigen Form:

- B-1: Der GO-Pfad von C3 schwächt das Gate und bricht den v1-Freeze.
- B-2: Der v2-Zweig umgeht die bindenden Spec-A-Verträge (Entscheidungen 2-4).
- M-3, M-6, M-7: Der Managed-Merge ist für MCP, Aufrufbedingung und State-Namespace mit dem bestehenden Code nicht umsetzbar wie beschrieben.
- M-1: Entscheidung 6 wird per Default-Annahme statt Nutzerbestätigung übersteuert.

Kein BLOCKED: Alle Punkte sind innerhalb der Spec korrigierbar, ohne die Entscheidungen 6-12 neu zu verhandeln.

**Re-Review-Fokus:** B-1, B-2, M-1 (Nutzerbestätigung dokumentiert), M-2/M-4 (Spike-Umfang und -Reihenfolge), M-3, M-7.
