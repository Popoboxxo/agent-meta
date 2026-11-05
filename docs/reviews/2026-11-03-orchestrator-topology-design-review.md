# Review — Orchestrator-Topologie (SPEC-orchestrator-topology-2026-11-03)

> Reviewer: `concept-reviewer` · Datum: 2026-11-03 · Modus: Design-Review (Spec-Input)
> Gegenstand: `docs/specs/2026-11-03-orchestrator-topology-design.md` (989 Zeilen, `status: Entwurf`)
> Referenz: Issue #1077 (Body + Kommentar 2026-11-02, abgerufen), verifizierter Repo-Stand `main`.
> Ergebnis: **CHANGES_REQUESTED** — 5 blockierende, 10 beratende Findings.

## Scope

Geprüft: Vollständigkeit gegen #1077 §2/§2.1/§3/§4/§5 und Kommentar §1–§6;
Nutzer-Intent („Main-Chat-Default = Builder, mehrere Orchestrator-Subagenten");
Belastbarkeit von D1–D10; Provider-Matrix als Datenaussage; Byte-Identität bei
ungesetztem Key; Zustands-/Migrationsrisiko; Prüfbarkeit der Regel-Änderung;
Governance (Marker, OQs, Unverifiziertes, Platzhalter, `datei:symbol`).
Nicht Teil des Scopes: Implementierung, Spec-Formulierung, Issue-Kritik.

**Verifikationsbasis:** jede tragende Fundstelle wurde im Repo gelesen
(`datei:symbol`). Nicht geprüft: der genannte Commit `95756dfe` und der
Arbeitsbaum-Status (kein Shell-Zugriff im Review; §16 Nr. 1 bleibt offen).

## Findings — blockierend

### B1 · Dimension: Vollständigkeit / Logik — die Matrix ist Vorbedingung *der Spec*, nicht ihrer Umsetzung

**§3, §7, §11 P0, §16, D10.** #1077 §3 verlangt die Provider-Analyse **vor**
der Enum-Finalisierung („Before the enum is finalized … the enum must be
derived from what providers can really express"), weil #1077 §3 als
*blocking precondition for design* markiert ist. Das Design dreht die Reihenfolge:
Enum und Matrix stehen in der Spec, die Belegdaten entstehen erst in **P0**
danach — und P0 ist als „S (2 Dateien)" dimensioniert, obwohl es 11
unverifizierte Punkte (§16), 9 Provider × 3 Strukturen und drei entscheidende
`hybrid`-Zellen abdecken müsste. Die Matrix wird damit zu einer Behauptung, die
sich die Daten später selbst schreibt (die vorgeschlagenen Keys
`topology_support`/`topology_degrade`/`orchestrator_instances` existieren heute
nicht — `config/provider-capabilities.yaml` kennt nur `main_agent_selectable`,
`subagent_dispatch`, `parallel_execution`, `file_based_agents`,
`bootstrap_required`, `fanout_mechanism`).

**Fix:** Entweder P0 als **Pre-Approval-Gate** deklarieren (Design bleibt
`Entwurf`, bis der Spike mit Zell-für-Zell-Evidenz vorliegt), oder in v1
konservativ nach der Repo-Konvention verfahren („an UNVERIFIED … maps to
sequential-fallback/false, never to a speculative mechanism",
`provider-capabilities.yaml` Kopfkommentar): `hybrid` auf **allen** Providern
`no`/`degraded` und die drei `hybrid=yes|degraded`-Zellen erst nach Beleg
freigeben. Zusätzlich pro Provider eine `topology_verified_state`-Struktur
(Muster `surface_verified_state`), damit „Daten" nicht mit „Annahme" verwechselt
wird.

### B2 · Dimension: Vollständigkeit — der zweite `default_agent`-Schreiber macht das Nutzerziel unerreichbar

**§4.6, S3, D6, D9, R2, §12.** Der Nutzer-Intent ist „Main-Chat-Default ist der
Builder, Orchestrator läuft als Subagent". §4.6 beschreibt als einzige
Änderung `_opencode_entry_point` (`scripts/lib/isolation.py`) und behauptet
„**Kein neuer Zustand**, keine neue Warnung an dieser Stelle". Das ist falsch:
`scripts/lib/context.py:apply_settings_surface_shape` schreibt
`document["default_agent"] = primary_role` für `opencode-json-v2`
**ohne** Topologie- und ohne ActiveSet-Bezug; `_init_provider_settings_json`
schreibt die Datei beim Anlegen. Der Managed-Merge räumt diesen Wert nicht ab
(`_merge_default_agent`: `desired is None` + leeres `st` ⇒ `return {}`, Wert
bleibt stehen). Folge für ein frisches v2-Projekt mit `topology: subagent`:
`default_agent: orchestrator` bleibt dauerhaft stehen, obwohl die Rolle als
`mode: subagent` emittiert wird, und weil `_opencode_entry_point` `None`
liefert, wird gleichzeitig **kein** Gate-Deny geschrieben (S4 greift, aber
niemand warnt über den Widerspruch). Das ist genau der Zustand, den der Nutzer
nicht will, und der einzige, den die ACs nicht abdecken.

**Fix:** `apply_settings_surface_shape` in P2 explizit in den Contract
aufnehmen (kein `default_agent` bei effektiver Topologie ≠ `primary`), plus
AC „`topology: subagent` ⇒ in einem frischen v2-Projekt steht **kein**
`default_agent` auf der Orchestrator-Rolle" und eine Aussage zur Migration
(vom Nutzer gesetzter Wert ≠ verwalteter Wert: WARN + Handlungssatz, kein
Auto-Delete — konsistent zu D1c/D16).

### B3 · Dimension: Logik — D3s „Schema-ERROR ⇒ kein Sync" existiert in diesem Repo nicht

**D3 (1), §4.1, §4.4, §12 AC-1/AC-2.** D3 stützt die Lautstärke des
Same-Scope-Widerspruchs auf „JSON-Schema `if/then`, `--validate` schlägt fehl,
kein Sync". Verifiziert falsch: `scripts/lib/config.py:_validate_config` Schritt
4 validiert gegen `project-config.schema.json`, druckt Verstöße aber als
**Warnungen** („Schema violations are printed as warnings — never hard-fails",
Docstring `:394-397`), kappt bei 5 Meldungen und überspringt die Prüfung
komplett, wenn `jsonschema` nicht installiert ist — was ein unterstützter
Zustand ist (`:407-416`). Ein `if/then` im Schema erzeugt also weder rc≠0 noch
Sync-Abbruch. Der eigentliche Fehlerkanal wäre der `SyncError` aus
`resolve_topology` (§4.1) — der greift aber nur, wenn der Resolver auf dem
Sync-Pfad läuft, nicht in `--validate`.

**Fix:** Den Same-Scope-Konflikt als **hart-fehlenden, stdlib-only** Check in
`_validate_config` verankern (Muster `_validate_providers` /
`_validate_repo_containment`, die hart abbrechen) *oder* als
Consistency-`ERROR` (dann zählt `print_report` ihn in `--validate`), und D3
sowie AC-1 entsprechend umformulieren. Das Schema-`if/then` als
Dokumentationshilfe behalten, aber nicht als Enforcement behaupten.

### B4 · Dimension: Logik — das Conditional-Rendering aus §10 funktioniert mit dem heutigen Mechanismus nicht; der `{{else}}`-Zweig ist nicht wortgleich

**§10, §4.3, §12 AC-6, R4, S20.** Zwei Defekte in der einzigen Textänderung:

1. **Maschinerie:** `scripts/lib/variables.py:_expand_conditionals` behandelt nur
   eine Whitelist als Conditional (`DOD_*`, `ORCH_MODE_*`,
   `REPO_CONTAINMENT_*`, `SUBAGENT_PERMISSIONS_*`, `*_SET`, `ROLE_*_ACTIVE`, …,
   `:431-451`). `ORCH_TOPOLOGY_*` ist nicht enthalten; ein nicht erkanntes
   `{{#if}}` fällt in die „orphaned marker cleanup" und **behält den Block
   unbedingt** — beide Zweige rendern. Dasselbe gilt für
   `scripts/lib/standalone.py:_CONDITIONAL_FALSE_FLAGS` (Kommentar `:118-129`:
   „an omitted flag falls through … which keeps the block unconditionally"),
   das den Standalone-Export derselben Templates rendert. Beide Dateien fehlen
   in P1 **und** P4. Zusätzlich müssen die neuen Builder-Variablen in
   `scripts/lib/consistency/placeholders.py:_BUILTIN_VARS` registriert werden
   (Ratchet ist shrink-only, „New builder variables must be registered, not
   added here"), sonst meldet `check_builder_known_set` einen ERROR.
2. **Text:** der `{{else}}`-Zweig ist **nicht** wortgleich. Heute lautet
   `rules/1-generic/a2a-delegation-gates.md:6`
   `Worker{{#if ROLE_ORCHESTRATOR_ACTIVE}} → \`orchestrator\`{{/if}} → HARD REJECT`;
   das Design schreibt `Worker → \`orchestrator\` → HARD REJECT`. Für jedes
   Projekt ohne aktive Orchestrator-Rolle ändert sich damit der Byte-Output
   genau im BC-kritischen Fall (ORCH_TOPOLOGY_EXPLICIT = false).

**Fix:** `variables.py:_expand_conditionals` + `standalone.py` +
`placeholders.py:_BUILTIN_VARS` in den P1/P4-Dateilisten ergänzen, das
verschachtelte `{{#if ROLE_ORCHESTRATOR_ACTIVE}}` im else-Zweig unverändert
übernehmen und AC-6 um einen Golden-Fixture-Fall „Rolle inaktiv + Key unset"
erweitern.

### B5 · Dimension: Logik — `orchestrator.singleton` ist so nicht ausdrückbar

**D5, §12 AC-8/AC-9.** Der Kommentar fordert `singleton` mit **Default `true`**.
Das Design gibt `enum: [true]`, lehnt `singleton: false` ab und erklärt
`singleton: true` + `max-instances > 1` zum Schema-ERROR — nennt aber keinen
Default. Beide Auflösungen sind kaputt: (a) mit Default `true` (wie im Issue
gefordert) wäre **jedes** `max-instances: 2` per Default im Konflikt, und weil
`false` verboten ist, ist N>1 prinzipiell unkonfigurierbar; (b) ohne Default
hängt die Konfliktprüfung an „Key explizit gesetzt", was JSON-Schema nicht von
„Default" unterscheiden kann. Zweiter Punkt: `topology: primary` + N>1 ist laut
D5 ein ERROR — nur im *selben* Scope prüfbar. Ein Provider-Override
`topology: primary` bei global `max-instances: 3` landet nach D3 (2) im WARNING
und rendert dann in `orchestrator.md` „primary, max 3 Instanzen".

**Fix:** `singleton` als **presence-only** Alias ohne Schema-`default`
dokumentieren („abwesend = aus `max-instances` abgeleitet"), Konflikt im
stdlib-Validator prüfen (siehe B3), und die Cross-Scope-Kombination
`primary` × globales N>1 in die D3-Matrix aufnehmen (ERROR oder WARNING —
explizit, nicht implizit).

## Findings — beratend

- **A1 · D2:** `hybrid` wird gegenüber #1077 §2 („primary *and* can additionally
  be spawned") auf „positions-agnostisch (entweder/oder)" verengt. Die
  Einschränkung steht in den Konsequenzen, aber nicht in §1 Ziel und nicht im
  Concept-Doc-Text; Nutzer werden die Issue-Tabelle lesen. Deviationssatz
  ergänzen.
- **A2 · §4.1:** `resolve_topology` muss D3 (1) erkennen, also `mode` auflösen —
  der Resolver liegt aber in `variables.py`, das seinerseits `topology.py` nicht
  importieren darf, wenn `ORCH_TOPOLOGY_*` dort gebaut werden. „Blattmodul"
  (C2) und „kennt variables-API" widersprechen sich. Signatur erweitern
  (`mode: str` als Parameter) statt einen zweiten Mode-Resolver zu bauen.
- **A3 · §4.1/§4.3:** `provider` ist Pflichtparameter, die globalen
  `ORCH_TOPOLOGY_*`-Flags werden aber in `config.py:_build_variables`
  provider-**los** gebaut. Für den ungesetzten Fall ist der globale Wert
  undefiniert (Ableitung ist per Provider). Expliziten Global-Vertrag ergänzen.
- **A4 · S2:** „`primary-role` wird ausschließlich über
  `providers.explicit_primary_role()` gelesen" ist falsch —
  `context.py:1698` (`pc.get("primary-role")`) und
  `provider_transform.py:649` (`.get('primary-role', 'orchestrator')`, mit
  Code-Default) lesen direkt. Damit existiert heute eine zweite Wahrheit für
  „primary"; das ist der Kern von R1, nicht nur ein Nebeneffekt.
- **A5 · §4.6:** Das ActiveSet-Konjunkt aus `_opencode_entry_point`
  (`active_set is not None and role not in active_set.roles ⇒ None`, `:568-569`)
  darf beim Umbau nicht verloren gehen; §4.6 nennt nur „`subagent` ⇒ None".
  Sonst erhält ein Projekt mit deaktivierter Orchestrator-Rolle einen neuen
  `default_agent` (Verhaltensänderung bei ungesetztem Key).
- **A6 · §8/D3:** Die Vier-Feld-Kombination ist nicht vollständig: der
  Same-Object-Fall `provider-overrides.<P>.{mode: main-chat, topology: primary}`
  ist weder (1) noch (2) zugeordnet — und genau das ist der wahrscheinlichste
  Tippfehler.
- **A7 · §5/§9.3, Kommentar §4:** Der geforderte Audit-Datensatz lautet „id,
  scope, spawn time, spawned-by"; geliefert wird nur `orchestrator_id`
  (AC-11). `scope_id` steht nur als Envelope-Feld (§9.1), nicht im Event.
  Entweder Event-Contract erweitern oder die Reduktion explizit begründen.
- **A8 · §11/R1:** P1 enthält `agent_sync.py`/`active_set.py` (Skip-Prädikat),
  R1 sagt „P1 landet es, P2 nutzt es an beiden Stellen". P1 ist damit sehr wohl
  emissions-nah, obwohl die Phase als „noch nicht in die Emission verdrahtet"
  begründet wird. Phasen-Schnitt schärfen.
- **A9 · Governance:** `consistency/spec_plan.py:_classify` ordnet
  `*-design.md` als **spec** ein und verlangt die literalen Überschriften
  `## Problem`, `## Ziel`, `## Nicht-Ziele`, `## Interface Contracts`,
  `## Datenfluss`, `## Acceptance Criteria`, `## Offene Fragen`, `## Trace-Anker`.
  Das Dokument nutzt `## 1. Problem und Ziel`, `### 4. Schnittstellen-Contracts`
  usw. → ~8 Section-Findings unter `--validate-spec-plan` (aktuell WARNING, weil
  DoD `rapid-prototyping` `spec-plan-required: false`). Entweder Überschriften
  anpassen oder die Klassifikation für Design-Docs schärfen.
- **A10 · D6/§9.3:** Checkpoint-Namespace nutzt `<base>__<id>`, der
  Fortschritt `<progress-dir>/progress-<id>.md` (nur `<id>`) — zwei
  Ableitungsregeln für dieselbe Identität. Zudem liest `recovery.py` nur
  Checkpoints; wer `progress-<id>.md` konsumiert, steht nirgends. Konsument
  benennen oder die Dateien als rein menschlich lesbar deklarieren.
- **A11 · S9:** Zeilenangaben (`Zeile 61/1522/2113`) statt Symbol; laut
  Konvention `datei:symbol`. Driftet beim nächsten Plan-Edit.

## Positiv verifiziert (info)

- `isolation._merge_default_agent` (`:690-700`) rollt einen **verwalteten**
  `default_agent` beim Wechsel `primary → subagent` korrekt zurück — die
  Migration ist für diesen Fall bereits vorhanden und muss nur dokumentiert
  werden (siehe B2 für die beiden Restfälle).
- Die Wahl `<base>__<id>` statt `checkpoint-<id>.json` ist richtig: sie
  kollidiert nicht mit dem Legacy-Glob `.meta-viz/checkpoint-*.json`
  (`recovery._LEGACY_GLOB`) und besteht `validate_session_id`.
- D3 (2) und D8 sind inhaltlich korrekt und ehrlich (Convention boundary,
  keine Enforcement-Behauptung) — die Kritik in B3 betrifft nur den
  *Mechanismus*, nicht die Absicht.

## Votum

**CHANGES_REQUESTED.** Die Richtung ist tragfähig (orthogonale Achsen,
Provider-Daten statt Namens-Branches, ehrliche Grenzen), aber fünf Punkte sind
vor einer Freigabe zu reparieren: die Matrix als Vorbedingung (B1), der
Builder-Default (B2), der Fehlerkanal des Same-Scope-Konflikts (B3), die
Conditional-Maschinerie samt wortgleichem Default-Zweig (B4) und die
`singleton`-Semantik (B5). Ohne B1 und B2 würde eine `APPROVED`-Spec ein
Versprechen tragen, das der Nutzer-Intent nicht einlöst.

Kein `Status: APPROVED` gesetzt — dieses Dokument bleibt `Entwurf`.
