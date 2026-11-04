# Orchestrator-Topologie konfigurierbar — Spec

> Status: **APPROVED (2026-11-04)**
> Freigabe durch den User am 2026-11-04 („Freigabe!") nach Beantwortung von OQ-1…OQ-5 (OQ-1 = B, OQ-2 = A, OQ-3 = A, OQ-4 = A, OQ-5 = A) — der Marker wird nie vom Planer gesetzt.
> Revision: 3
> Datum: 2026-11-04
> spec-id: SPEC-orchestrator-topology-2026-11-03
> Issue: #1077
> Design-Input: `docs/specs/2026-11-03-orchestrator-topology-design.md` (Rev. 4,
> 2026-11-04)
> Verifikations-Legende: **VERIFIED** = im Repo gelesen (`datei:symbol`);
> **BRIEF** = aus Design/Auftrag übernommen, in dieser Runde nicht neu geprüft.

Diese Spec ist die implementierbare Ableitung des Designs Rev. 4. Sie enthält
Interface-Contracts, Datenfluss und testbare Abnahmekriterien — **keinen
Implementierungscode**. Alle fünf offenen Fragen sind entschieden; die
Entscheidungen sind als Fakten eingefaltet (D1–D10, §15 des Designs).

## Revision

| Rev | Datum | Autor | Änderung |
|---|---|---|---|
| 1 | 2026-11-04 | concept-specifier | Erste implementierbare Ableitung des Designs Rev. 4. |
| 2 | 2026-11-04 | concept-specifier | Review-Fix-Pass (**Status bleibt Entwurf**): **B1** Ist-Zustand rebased — #1090 hat `active_set.role_emitted_for_provider`, `emit_default_agent` und die direkten `primary-role`-Lesezugriffe bereits gelandet; IC-3/IC-6/IC-7, P1/P2-Dateilisten und Call-Site-Zählung darauf neu aufgesetzt, kein zweiter Steuerparameter. **B2** Resolver-Regel vervollständigt: `support == false` **oder** `UNVERIFIED` ⇒ Fallback; `effective ∈ VALID_TOPOLOGIES` garantiert, Mechanismus-Wort wandert nach `degradation_reason`; AC-15 erweitert. **B3** Evidenz-Gate auf alle drei Design-Bedingungen (§7 inkl. §3.1-Zeile + Invariantentest) erweitert; §3.1 im Trace-Anker. **B4** Sync-Summary-Zeile, `default-agent-conflict` und Gate-Inactive-WARNUNG als IC + AC nachgezogen; v1-DoD aktualisiert. **B5** Governance-Hinweis auf das reale `_classify`-Verhalten korrigiert (akzeptierte WARNING-only, kein Grün). Advisories 1–5, 7–9 eingearbeitet (AC-17-Teilstring, P0→AC-Liste, normative Matrix-Kopie, `degraded_from`-Bedingung, `mode`-Quelle, P3-Registrierungen, AC-4-P3-Marker, 3×3-Matrix). Zusätzlich D5-Klausel (redundantes `singleton`-INFO) und AC-11-Reduktionssatz. |
| 3 | 2026-11-04 | concept-specifier | Wording-Fix-Pass (**Status bleibt Entwurf**): **NC-1** Resolver-Invariante auf „nie unvalidiert durchgereicht" umgestellt; Koinzidenz-Fall (Continue: declared `subagent`, Fail-safe `subagent`) explizit als **keine** Degradierung benannt — `degraded_from = None`, keine WARNING (IC-2, Provider-Matrix, AC-15). **NC-2** WARNING-Dedup in IC-5 auf „genau eine pro Check-ID" präzisiert; mehrere IDs (`degraded`, `gate-inactive`, `default-agent-conflict`) dürfen im selben Lauf feuern. **NC-3** `hybrid`-Spalte der 3×3-Matrix mit Degradations-Fußnote (`→ subagent` in v1) versehen. **NC-4** ungenutzten `mode`-Parameter aus `_opencode_entry_point` entfernt; Aufrufer der einmaligen `TopologyResolution`-Auflösung benannt. **NC-5 (Deviation):** Diese Spec **supersediert** Design Rev. 4 in zwei Punkten — `topology_effective` (ersetzt durch das in den bestehenden `emit_default_agent`-Bool gefaltete Konjunkt, IC-7) und `providers.primary_role` (nicht eingeführt; `explicit_primary_role` bleibt, B1/#1090). Die entsprechenden Design-Passagen sind überholt. |
| 3.1 | 2026-11-04 | user | Rev. 3.1 (2026-11-04) — user approval recorded (Status APPROVED). |

---

## Problem

Die Position des Orchestrators ist heute **kein Nutzerentscheid**, sondern ein
Nebeneffekt genau eines Daten-Keys: `providers.<P>.primary-role` in
`config/ai-providers.yaml` (VERIFIED, nur `Opencode` setzt ihn). Daraus folgen
drei Probleme (Issue #1077 §1.2):

1. **Strukturell unterschiedliches Verhalten je Provider** ohne
   Konfigurationsmöglichkeit — die Antwort steckt in der Provider-Registry.
2. **Nicht auffindbar:** `orchestrator.mode` (`strict|advisory|main-chat`) klingt,
   als steuere er die Position, tut es aber nicht. `strict`/`advisory` ändern nur
   die Gate-Stärke; `main-chat` entfernt die Rolle ganz
   (VERIFIED `scripts/lib/variables.py:_resolve_orch_mode`,
   `scripts/lib/agent_sync.py:_should_skip_role`).
3. **Kein Multi-Orchestrator**, obwohl scope-disjunkte Parallel-Stränge je ihren
   eigenen Delegations-Wurzel-Agenten bräuchten — die Singleton-Regel verbietet
   `subagent_type: orchestrator` pauschal für Worker (VERIFIED
   `rules/1-generic/a2a-delegation-gates.md`).

Zusätzlich ist der **angestrebte Nutzerzustand** heute nicht erreichbar: Mit
`topology: subagent` muss in einem frischen Opencode-v2-Projekt der Main-Chat-
Default der **Builder** (Main Chat) sein, nicht der Orchestrator. Ein
`default_agent: orchestrator` auf eine `mode: subagent`-Datei ist der zu
vermeidende Zustand (Design §1, §4.6 / AC-14).

**Betroffene Subsysteme:** Schema (`config/project-config.schema.json`),
Config-Validierung (`scripts/lib/config.py`), Variablen/Rendering
(`scripts/lib/variables.py`), Auflöser (neu `scripts/lib/topology.py`),
Emission (`provider_transform.py`, `isolation.py`, `context.py`, `agent_sync.py`),
Konsistenz (`consistency/topology.py`), Multi-Instanz-Zustand
(`checkpoint.py`, `delegation_syntax.py`, Viz-Events) und Guard
(`hooks/1-generic/orchestrator-guard-impl.sh`).

---

## Ziel

Eine explizite, dokumentierte Projekt-Einstellung `orchestrator.topology` mit
`primary | subagent | hybrid`, ein dazu **orthogonaler** Multi-Instanz-Vertrag,
harte Lautstärke bei Degradierung und **exakte Rückwärtskompatibilität** bei
ungesetztem Key.

**v1-Umfang (OQ-5 = A):** P0–P2 + P4. v1 liefert den Builder-Default und **genau
einen** spawnbaren Orchestrator; Multi-Instanz (P3) ist der unmittelbar nächste
Schritt und **nicht** Teil der v1-DoD.

**Messbare Ziele:**

- `sync --check` auf unveränderten Consumer-Projekten bleibt byte-identisch
  (AC-6).
- Degradierung ist laut: genau eine WARNING **pro Check-ID** (d. h. pro
  Provider und Lauf je Check) — mehrere verschiedene Check-IDs dürfen im selben
  Lauf feuern —, nie stilles Absenken (AC-3, AC-7, AC-16).
- Keine Matrix-Zelle behauptet eine Fähigkeit ohne aufgezeichnete Evidenz
  (AC-15, AC-16, P0-Gate).
- `topology: subagent` erzeugt in einem frischen Opencode-v2-Projekt **kein**
  `default_agent` auf der Orchestrator-Rolle (AC-14).

---

## Nicht-Ziele

- **Keine** Parallel-Workstream-Isolation selbst (Worktrees/Checkouts) —
  Issue #547, ausdrücklich out of scope.
- **Keine** Reparatur des OpenCode-v1/v2-Surface-Bugs (#1006). Die
  `primary`-Emission nutzt den bestehenden Pfad; #1006 ändert die *Form*, nicht
  die Topologie-Semantik.
- **Kein** neuer Provider, keine Änderung der Provider-Registry.
- **Keine** SE-Kaskade (kein `systems-engineering`-Auto-Start).
- **Kein** Admin-UI-Editor für Topologie (nur Schema/Doku).
- **Keine** Per-Instanz-Kosten-/Token-Abrechnung.
- **Keine** Scope-Registry und **kein** Orchestrator→Orchestrator-Spawn in v1
  (D7).
- **Keine** Änderung an `max-parallel-agents` (Semantik, Default, Grenzen).
- **Kein** Runtime-Enforcement von N oder von Instanz-Scopes (D8). Die
  Instanz-ID im Guard ist **audit-only**.
- **Kein ungebundenes Zell-Upgrade:** Matrix-Zellen wechseln nur über die
  P0-Upgrade-Prozedur mit aufgezeichneter Evidenz; unbelegte Zellen bleiben
  `UNVERIFIED ⇒ no`.

---

## Entscheidungen (D1–D10, OQ-Ergebnisse eingefaltet)

Format je Entscheidung: Kontext → Entscheidung → Konsequenz (ADR-Kurzform).
Alle fünf OQ sind am **2026-11-04** durch den Nutzer entschieden; die
Konsequenz ist jeweils eingefaltet.

| ID | Kontext | Entscheidung | Konsequenz |
|---|---|---|---|
| **D1** | Eine Konfigurationsfläche für „wo lebt der Orchestrator" existiert nicht; `context_file.topology` ist bereits belegt (Dateilayout). | Key `orchestrator.topology`, Enum `primary \| subagent \| hybrid`. `primary` = Rolle ist Session-Einstieg, ein Orchestrator, kein Spawn-Kanal; `subagent` = Rolle ist nie Einstieg, Main Chat spawnt 1..N; `hybrid` = positions-agnostisch. | Ein Schlüssel, ein Enum, direkt in Doku/Rule/Fehlermeldung zitierbar. Schema-`description` von `context_file.topology` sagt „Dateilayout, nicht Agent-Topologie". |
| **D2** | #1077 §2 beschreibt `hybrid` als „primary **und** zusätzlich spawnbar". | **Deviation:** `hybrid` = **entweder/oder** (eine positions-agnostische Rolle), nicht zwei gleichzeitige Positionen. Anzahl ist ausschließlich `max-instances` (D5). | Ein Identitätsmodell für alle Topologien; `hybrid` ist in v1 akzeptiert, aber degradiert, solange keine Evidenz vorliegt. Deviationssatz muss in Concept-Doc und Doku-Tabelle stehen. |
| **D3** | `mode: main-chat` entfernt die Rolle; eine gesetzte Topologie wäre gegenstandslos. Widerspruch kann im selben Scope oder cross-scope auftreten. | **Same-Scope = harter ERROR** (`_validate_orchestrator_topology`, stdlib, rc≠0 in `sync` **und** `--validate`), inkl. Same-Object `{mode: main-chat, topology: primary}`. **Cross-Scope = WARNING** (`main-chat-supersedes`); `primary` × globales N>1 cross-scope = WARNING `instances-clamped`, effektiv N=1. Schema-`if/then` bleibt Editor-Hilfe, kein Fehlerkanal. | Tippfehler-Paar bricht früh mit Pfadangabe; der legitime Mischfall (Claude main-chat, Opencode strict) bleibt möglich und laut. |
| **D4** | `mode` (Gate-Stärke/Existenz) und `topology` (Position) sind verschiedene Achsen. | Zwei orthogonale Achsen; genau **eine** Dominanzzelle (`main-chat` macht Topologie inert). Topologie ist per Provider überschreibbar: `orchestrator.provider-overrides.<P>.topology`; Präzedenz `provider-override > project > derived`. | Symmetrie zu `mode`; Degradierung ist pro Provider auflösbar. `provider-overrides` wird von „nur `mode`" auf zwei Properties erweitert. |
| **D5** | Der Issue-Kommentar fordert eine von der Enum unabhängige Multiplizitäts-Achse mit hartem Konflikt statt stiller Präzedenz. | `orchestrator.max-instances` integer 1..**8** (**OQ-3 = A**, **P3-only**), kanonischer Wert. `orchestrator.singleton` presence-only Alias (`enum: [true]`, **kein Schema-`default`**, P3). Same-Scope-Konflikte (`singleton` present + N>1; `primary` + N>1) = harter ERROR; `singleton: false` = ERROR mit Hint „use max-instances". **`singleton` present + N=1 ist kein Konflikt, sondern ein redundanter Sync-INFO** (`orchestrator-topology.singleton-redundant`, P3-only). N>1 nur, wenn Capability `orchestrator_instances.multiple == true` und Zelle nicht `UNVERIFIED`. | Default 1 = heutiges Verhalten; kein stiller Vorrang. `max-instances` existiert **vor P3 nicht** — kein Zwischenschritt mit `maximum: 1`. Das redundante INFO macht den Alias sichtbar, ohne zu blockieren. |
| **D6** | Checkpoints sind eine Datei pro Session, Fortschritt ist eine Datei, Event-Log ist eine Datei; bei N>1 kollidieren sie. | Instanz-Identität ist ein State-Namespace, kein Rollenname: `orchestrator_id` = `[a-z0-9][a-z0-9._-]{0,39}`, Default `None` bei N=1. Session-ID = `<base>__<id>`. Fortschritt: `progress-<id>.md` **nur menschlich lesbar**; `current.md` bleibt maschinell gelesen. Event-Log bleibt eine Datei mit Feldern `orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at`. N=1 byte-identisch, kein Backfill. | N>1 ohne neue Verzeichnisstruktur und ohne Konsumenten-Bruch; `recovery.py` liest weiterhin nur Checkpoints. **P3-only.** |
| **D7** | Die Singleton-Regel ist heute über „es gibt genau einen" begründet; bei N>1 ist das falsch. | Drei mechanisch prüfbare Klauseln: **G1** Worker → orchestrator = HARD REJECT (immer); **G2** nur `main_chat` spawnt Orchestratoren, höchstens `max-instances`, eindeutige ID, disjunkter Scope, doppelte ID/Scope-Überlappung = HARD ERROR beim Spawn; **G3** orchestrator → orchestrator = HARD REJECT. | Anti-Recursion bleibt aus dem Envelope beweisbar (Spawner of record + fehlende Kante). Kein neues State-Artefakt; Scope-Registry ist P5, nicht v1. |
| **D8** | Der Guard arbeitet mit einem selbstdeklarierten Sentinel; Rollen-Identität ist von keinem Provider verifizierbar (#516). | Convention-Boundary bleibt. Sentinel darf optional `id=<id>` tragen; der Guard **parst** sie, nutzt sie **nie** für Allow/Deny und schreibt sie ins Audit-Log (**OQ-2 = A**, **P3-only**). „Bekannte Grenzen" wird um den Audit-Satz ergänzt. | Ehrlich: keine neue Sicherheitszusage, aber Nachvollziehbarkeit. Hook-Change + Test liegen in P3, nicht P4. |
| **D9** | Kein Projekt darf durch das Upgrade sein Verhalten ändern; gleichzeitig muss `topology: subagent` den Main Chat als Default behalten. | Key ungesetzt ⇒ exakt heutige Ableitung (`primary-role` + ActiveSet ⇒ `primary`, sonst `subagent`; `hybrid` nie abgeleitet). Key gesetzt (`subagent`) ⇒ `apply_settings_surface_shape` schreibt **kein** `default_agent`, `_opencode_entry_point` liefert `None`, Runtime-Gate wird laut suspendiert. Die Ableitung erscheint **nur** als Sync-Summary-Zeile (IC-11/AC-19; **OQ-4 = A**, **kein** `--check`-INFO). | `sync --check` bleibt byte-identisch; kein neues Rendering in bestehenden Templates, solange `ORCH_TOPOLOGY_EXPLICIT != "true"`. Nutzereigener `default_agent` wird nicht gelöscht, nur gewarnt. |
| **D10** | Das Issue macht die Provider-Matrix zur Freigabe-Vorbedingung: nicht versprechen, was nicht belegbar ist. | Matrix aus **vorhandenen** Capability-Keys ableiten (`main_agent_selectable`, `subagent_dispatch`, `parallel_execution`); neue Strukturen `topology_support`, `topology_degrade`, `orchestrator_instances`, `topology_verified_state`. Regel `UNVERIFIED ⇒ no`; `hybrid`-Degradierung fail-safe auf `"subagent"`. **OQ-1 = B:** die fünf Provider-Probes (§16 Nr. 2–6 des Designs) werden **jetzt in P0** ausgeführt; nur belegte Zellen dürfen `yes` werden. | Keine Zelle ist eine Behauptung; 25 Basis-Zellen + N **gemessene** Upgrades; 0 spekulative `yes`. Neue Provider sind fail-safe eingeordnet. |

---

## Interface Contracts

Alle Pfade relativ zum Framework-Root. Fehlerpfad-Konvention: `SyncError`
(→ CLI rc 1) im Auflöser; harte Config-Checks folgen `_validate_providers`
(stderr + `sys.exit(1)`), weil sie vor dem Sync und in `--validate` laufen.

### IC-1 `config/project-config.schema.json`

| Key | Typ | Phase | Contract |
|---|---|---|---|
| `orchestrator.topology` | enum `primary \| subagent \| hybrid` | P1 | Optional; Default = heutige Ableitung (kein Schema-Default, der die Ableitung überschreibt). `description` grenzt gegen `context_file.topology` ab. |
| `orchestrator.provider-overrides.<P>.topology` | enum, wie oben | P1 | `additionalProperties: false` bleibt; das Objekt erhält neben `mode` genau dieses Property. |
| `orchestrator.max-instances` | integer, min 1, max **8** | **P3** | Existiert vor P3 **nicht**. `description` grenzt gegen `max-parallel-agents` ab. |
| `orchestrator.singleton` | enum `[true]` | **P3** | Presence-only Alias, **kein** Schema-`default`; Abwesenheit = aus `max-instances` abgeleitet. |
| `orchestrator.provider-overrides.<P>.mode` | bestehend | — | Unverändert. |

Fehlerpfad: Schema-`if/then` ist **nur** Dokumentations-/Editor-Hilfe (S22) und
erzeugt weder rc≠0 noch Sync-Abbruch. Durchsetzung ausschließlich IC-9.

### IC-2 `scripts/lib/topology.py` (neu, Blattmodul)

```python
VALID_TOPOLOGIES: frozenset[str] = frozenset({"primary", "subagent", "hybrid"})
DEFAULT_MAX_INSTANCES: int = 1
VERIFIED_STATES: frozenset[str] = frozenset(
    {"VERIFIED-RUNTIME", "DOCUMENTED", "UNVERIFIED"}
)

@dataclass(frozen=True)
class TopologyResolution:
    declared: str | None       # Roh-Wert oder None (Key ungesetzt)
    effective: str             # IMMER in VALID_TOPOLOGIES (nie ein Mechanismus-Wort)
    source: str                # "provider-override" | "project" | "derived"
    derived_from: str | None   # z.B. "providers.Opencode.primary-role"
    degraded_from: str | None  # declared, wenn declared != effective; sonst None
    degradation_reason: str | None  # Grund + ggf. Mechanismus-Wort
    verification_state: str    # Zelle aus topology_verified_state

def resolve_topology(
    config: dict,
    provider: str,
    *,
    provider_config: dict,
    capabilities: dict,
    mode: str,                 # bereits durch _resolve_orch_mode aufgelöst
    active_set: "ActiveSet | None" = None,  # D9-Ableitung: Rolle im ActiveSet?
    validate: bool = True,
) -> TopologyResolution: ...

def topology_explicit(config: dict, provider: str | None = None) -> bool: ...

def resolve_orchestrator_instances(   # P3
    config: dict, provider: str, topology: TopologyResolution, *,
    capabilities: dict, validate: bool = True,
) -> tuple[int, str | None]: ...

def compose_instance_session_id(      # P3
    base_session_id: str, instance_id: str | None
) -> str: ...
```

**Vertrag (Rev. 2):**

1. **Präzedenz:** `provider-overrides.<P>.topology > orchestrator.topology >
   Ableitung aus providers.<P>.primary-role`. Key ungesetzt ⇒ Ableitung
   (`primary`, wenn `primary-role` gesetzt und die Rolle im ActiveSet liegt,
   sonst `subagent`; `hybrid` wird nie abgeleitet), `degraded_from is None`,
   keine WARNING (D9).
2. **Fallback-Regel (B2):** Ist `topology_support.<achse> == false` **oder**
   `topology_verified_state.<achse> == "UNVERIFIED"`, wird der deklarierte Wert
   **nie unvalidiert durchgereicht**: `effective` wird `topology_degrade.<achse>`,
   sofern dieser Wert in `VALID_TOPOLOGIES` liegt; andernfalls Fail-safe
   `"subagent"`. **Koinzidenz-Fall (kein Degradationsfall):** Fällt der
   Fail-safe auf denselben String wie die Deklaration — z. B. Continue: declared
   `subagent`, `topology_support.subagent == false`,
   `topology_degrade.subagent = "sequential-text"` (nicht in
   `VALID_TOPOLOGIES`) ⇒ Fail-safe `"subagent"` —, dann gilt `degraded_from =
   None` und es entsteht **keine** WARNING; der Support-Mangel ist dann nur in
   der Zelle (`no`/`degraded`) dokumentiert, nicht als Laufzeit-Degradierung.
   `degraded_from = declared` gilt ausschließlich, wenn `declared != effective`
   wirklich degradiert wurde; `degradation_reason` trägt den Grund **und** das
   Mechanismus-Wort, z. B.
   `"capability cell UNVERIFIED"`, `"support=false"` oder
   `"support=false (degrade mechanism: sequential-text; clamped to subagent)"`.
   ```python
   VALID_TOPOLOGIES = frozenset({"primary", "subagent", "hybrid"})
   # topology_support.<axis> == false or verified_state == UNVERIFIED
   raw = (cfg.get("topology_degrade") or {}).get(axis)
   effective = raw if raw in VALID_TOPOLOGIES else "subagent"   # Fail-safe
   assert effective in VALID_TOPOLOGIES                         # Invariante
   ```
   Ein Mechanismus-Wort (`"sequential-text"`, Continue) ist **nie** ein
   gültiger `effective`-Wert; es lebt ausschließlich in `degradation_reason`.
3. **Parameter `mode`:** kommt aufgelöst herein. Einzige Quelle ist
   `variables._resolve_orch_mode(orch, provider_override, validate=False)`,
   **einmal** pro Provider im Aufrufer gerufen; `topology.py` importiert
   `variables.py` **nicht** (kein zweiter Mode-Resolver).
4. `validate=False` liefert den normalisierten String ohne zu werfen
   (Konsistenz-Checker); die `effective ∈ VALID_TOPOLOGIES`-Invariante gilt
   auch dort.

**Fehlerpfade:** `SyncError` bei unbekanntem Enum-Wert;
`resolve_orchestrator_instances` wirft `SyncError` bei `singleton`-Widerspruch
oder `topology: primary` mit N>1 im selben Scope (D5);
`compose_instance_session_id` wirft `ValueError`, wenn die Komposition
`validate_session_id()` verletzt.

### IC-3 `scripts/lib/active_set.py::role_emitted_for_provider` (bestehend; P2 Call-Site-Angleichung)

> **Ist-Zustand (Rev. 2, B1):** Die Funktion existiert bereits
> (`scripts/lib/active_set.py::role_emitted_for_provider`) und ist verdrahtet in
> `context.py::_init_provider_settings_json` (Aufruf) sowie in
> `isolation.py::_opencode_entry_point`, `isolation.py::_sync_opencode_runtime_gate`
> (Dangling-Warnung und Gate-Suspendierung). Sie ist **keine** P1-Neuentwicklung.

```python
def role_emitted_for_provider(
    role: str,
    active_set: Optional[ActiveSet],
    config: Optional[Mapping],
    provider: str,
) -> bool: ...
```

Signatur bleibt **unverändert**. Vertrag: (1) `active_set is None` ⇒
fail-open (historisch); sonst muss `role in active_set.roles` gelten. (2) Nicht-
Orchestrator-Rollen sind danach `True`. (3) Für `role == "orchestrator"` ist
das Ergebnis `_resolve_orch_mode(orch_cfg, provider_override, validate=False)
!= "main-chat"` — Provider-Override zuerst, dann global. Die Funktion bleibt
provider-agnostisch: einzige Provider-Eingabe ist der Daten-Key
`orchestrator.provider-overrides.<provider>`.

**Topologie ist kein zweiter „emitted"-Begriff.** `topology: subagent` erzeugt
`orchestrator.md` weiterhin (als Subagent); die Rolle ist also *emittiert*. Die
Topologie steuert ausschließlich den **Entry-Point**
(`default_agent`/`_opencode_entry_point`) und wird dort als zusätzliche
Konjunktion ausgewertet (IC-6/IC-7) — **kein** neuer Parameter in
`apply_settings_surface_shape`, **kein** `topology_effective`-Flag.

**P2-Call-Site (B1 — die tatsächlichen Stellen, nicht „die zweite"):**

| Site | Heute | P2-Änderung |
|---|---|---|
| `scripts/lib/agent_sync.py::_should_skip_role` | liest `variables["ORCH_MODE_MAIN_CHAT"]` | ruft `role_emitted_for_provider(role, active_set, config, provider)`; der Variablen-Read entfällt |
| `scripts/lib/context.py::_init_provider_settings_json` | ruft das Prädikat bereits | zusätzlich `and topology.effective == "primary"` für `emit_default_agent` |
| `scripts/lib/isolation.py::_opencode_entry_point` | ruft das Prädikat bereits | zusätzlich `topology.effective == "primary"` |
| `scripts/lib/isolation.py::_sync_opencode_runtime_gate` (Dangling-Warnung) | ruft das Prädikat bereits | zusätzlich Topologie-Konjunktion für `orchestrator-topology.default-agent-conflict` |
| `scripts/lib/isolation.py::_sync_opencode_runtime_gate` (Gate-Suspendierung) | nutzt das Prädikat + `explicit_primary_role` | zusätzlich Topologie-Konjunktion für `orchestrator-topology.gate-inactive` |

Genau **eine** Funktion entscheidet weiterhin über Datei-Emission; nirgends
wird `main-chat` als Topologie-Wert behandelt.

### IC-4 `scripts/lib/variables.py` (P1; P3-Erweiterung)

```python
def _topology_flags(topology: str, *, explicit: bool, source: str) -> dict[str, str]:
    # ORCH_TOPOLOGY_PRIMARY / _SUBAGENT / _HYBRID : "true"|"false"  (genau eines true)
    # ORCH_TOPOLOGY                               : "primary"|"subagent"|"hybrid"
    # ORCH_TOPOLOGY_EXPLICIT                      : "true"|"false"
    # ORCH_TOPOLOGY_SOURCE                        : "provider-override"|"project"|"derived"

def _instance_flags(max_instances: int, *, singleton_declared: bool) -> dict[str, str]:  # P3
    # ORCH_MAX_INSTANCES       : "1".."8"
    # ORCH_SINGLETON_DECLARED  : "true"|"false"   (presence-only Key)
```

**Provider-loser Global-Vertrag (`config.py::_build_variables`):**

| Flag | provider-loser Wert | Phase |
|---|---|---|
| `ORCH_TOPOLOGY` | Projekt-Scope-Wert, sonst `""` (nie ein abgeleiteter Provider-Wert) | P1 |
| `ORCH_TOPOLOGY_EXPLICIT` | `"true"` **nur** wenn `orchestrator.topology` im Projekt-Scope steht; Provider-Override zählt **nicht** | P1 |
| `ORCH_TOPOLOGY_PRIMARY/_SUBAGENT/_HYBRID` | genau eines `"true"`, sonst alle `"false"` (wenn `ORCH_TOPOLOGY == ""`) | P1 |
| `ORCH_MAX_INSTANCES` | existiert vor P3 **nicht**; ab P3 Projekt-Scope-Wert, Default `"1"` | P3 |
| `ORCH_SINGLETON_DECLARED` | existiert vor P3 **nicht**; ab P3 `"true"` nur bei presence-only Key | P3 |

Jede provider-skopierte Rendering-Stelle (`context.py::_build_context_vars`,
`rules.py::_merged_rule_vars`, `provider_transform.py`) muss mit
`provider=...` re-resolven und die globalen Werte überschreiben — exakt wie
`REPO_CONTAINMENT_*`. `rules.py::_merged_rule_vars` unterstützt
`variables=None` und baut die Flags selbst (S23); der Topologie-Zweig muss dort
genauso stehen wie `_orch_mode_flags`.

**Conditional-Registrierung (P1-Pflicht, B4):** Vier getrennte Registrierungen;
fehlt eine, rendert der heutige Mechanismus **beide** Zweige bzw. den falschen:

1. `scripts/lib/variables.py::strip_inactive_conditional_blocks` — Präfix
   `ORCH_TOPOLOGY_` in das intern gebaute `conditional_vars`-Set (Z. 431–451).
2. `scripts/lib/variables.py::_FALSE_DEFAULT_CONDITIONALS` (Z. 52) —
   `ORCH_TOPOLOGY_EXPLICIT`, `ORCH_TOPOLOGY_PRIMARY`, `ORCH_TOPOLOGY_SUBAGENT`,
   `ORCH_TOPOLOGY_HYBRID` eintragen; sonst liest `_conditional_active` eine
   abwesende Variable als `"true"` und rendert den **neuen** Zweig.
3. `scripts/lib/standalone.py::_CONDITIONAL_FALSE_FLAGS` — literale
   `"false"`-Einträge für dieselben vier Flags; zusätzlich Fallback
   `ORCH_TOPOLOGY: ""`. (`ORCH_MAX_INSTANCES`/`ORCH_SINGLETON_DECLARED` folgen
   erst in P3.)
4. `scripts/lib/consistency/placeholders.py::_BUILTIN_VARS` — alle neuen
   Builder-Variablen registrieren (Ratchet ist shrink-only).

**P3-Nachzug (Advisory 7):** `ORCH_MAX_INSTANCES` und
`ORCH_SINGLETON_DECLARED` werden in P3 in **allen vier** Registrierungen
nachgezogen — Präfix-Whitelist in `strip_inactive_conditional_blocks`
(`ORCH_MAX_INSTANCES`/`ORCH_SINGLETON_DECLARED` explizit, nicht nur
`ORCH_TOPOLOGY_`), `variables.py::_FALSE_DEFAULT_CONDITIONALS`,
`standalone.py::_CONDITIONAL_FALSE_FLAGS` und
`consistency/placeholders.py::_BUILTIN_VARS`. Fehlt eine, rendert der
Conditional-Mechanismus den falschen Zweig (fail-open).

### IC-5 `scripts/lib/consistency/topology.py` (neu, P2)

```python
def check_orchestrator_topology(
    agent_meta_root: Path, project_config: dict
) -> list[Finding]: ...
```

| Check-ID | Severity | Phase | Bedingung |
|---|---|---|---|
| `orchestrator-topology.degraded` | WARNING | P2 | `resolution.degraded_from is not None` (`support == false` **oder** Zelle `UNVERIFIED`; declared ≠ effective) |
| `orchestrator-topology.hybrid-unverified` | WARNING | P2 | Deklaration `hybrid` und `topology_verified_state.hybrid == "UNVERIFIED"` |
| `orchestrator-topology.main-chat-supersedes` | WARNING | P2 | Cross-Scope: Provider-Override `mode: main-chat` bei übergeordnet gesetzter Topologie |
| `orchestrator-topology.instances-clamped` | WARNING | P2/P3 | N>1, aber `orchestrator_instances.multiple == false` **oder** Cross-Scope `primary` + globales N>1 |
| `orchestrator-topology.unresolved-global-flags` | WARNING | P2 | Ein `ORCH_TOPOLOGY_*`-Platzhalter wurde provider-los gerendert |
| `orchestrator-topology.default-agent-conflict` | WARNING | P2 | Nutzereigener `default_agent` (kein State-Record) auf der Orchestrator-Rolle bei effektiver Topologie ≠ `primary`; Text nennt die Handlung, **kein** Auto-Delete |
| `orchestrator-topology.gate-inactive` | WARNING | P2 | Das Runtime-Gate wäre gewollt, aber `_opencode_entry_point` ist `None`, weil die Topologie ≠ `primary`; der Deny wird bewusst **nicht** geschrieben |
| `orchestrator-topology.singleton-redundant` | **INFO** | **P3** | `singleton` present **und** `max-instances == 1` (kein Konflikt, kein Fehler; nur Hinweis „redundant, `max-instances` ist bei 1 der Default") |
| ~~`orchestrator-topology.derived`~~ | **entfällt** | — | **OQ-4 = A:** kein INFO-Finding; Ableitung nur als Sync-Summary-Zeile (IC-11/AC-19) |

**Vertrag:** kein Schreiben, kein Exit, nur `Finding`s. Genau **eine** WARNING
**pro Check-ID** und Provider und Lauf (dedupliziert **je Check-ID**);
verschiedene Check-IDs können im selben Lauf für denselben Provider feuern —
z. B. `degraded` + `gate-inactive` auf Opencode bei deklariertem `hybrid`, mit
nutzereigenem `default_agent` zusätzlich `default-agent-conflict`; `--check`
bleibt rc 0. Das `singleton-redundant`-INFO ist P3-only und zählt nicht als
Degradierungs-WARNUNG (AC-16).

### IC-6 `scripts/lib/provider_transform.py::_apply_agent_transform` (P2)

Heute entscheidet `explicit_primary_role(...)` allein (`mode: primary` nur bei
explizitem `primary-role`; sonst v2 `subagent`). P2 ergänzt die
Topologie-Konjunktion — die Ableitung bleibt sonst unverändert:

| effektive Topologie | opencode-native v1 | opencode-native v2 |
|---|---|---|
| `primary` (Rolle == entry role) | `mode: primary` | `mode: primary` |
| `subagent` | `mode` **nicht** geschrieben (heutiges v1-Verhalten) | `mode: subagent` |
| `hybrid` | wie `primary` (v1 nie gewährt → WARNING + Fallback) | wie `primary` |

Konkret: `mode = 'primary'` nur wenn `role == explicit_primary_role(...)`
**und** `resolve_topology(...).effective == "primary"`; sonst v2 `subagent`,
v1 kein `mode`. `effective` ist durch IC-2 garantiert in `VALID_TOPOLOGIES`;
der Fallback passiert im Resolver, nicht hier.

Template-Fallbacks (`mode or template_fm["mode"]`) und der Write-Scope-Lock
(„primary ⇒ edit-deny") bleiben an `mode == 'primary'` gebunden — **keine**
zweite Bedingung.

**Bestehende `primary-role`-Lesezugriffe (B1 — bleiben, kein neuer Accessor):**
`primary-role` ist ein Daten-Key, kein Steuerparameter. Die direkten Reads
liegen in `provider_transform.py::_apply_agent_transform`
(`explicit_primary_role` + der Allowlist-Read), in
`context.py::apply_settings_surface_shape`, in
`context.py::_init_provider_settings_json` und in
`context.py::init_settings_json` (Entry-Point-Vorprüfung). P1 führt **keinen**
neuen `providers.primary_role(...)`-Accessor ein (die frühere A4-Annahme ist
durch #1090 überholt); `providers.explicit_primary_role` bleibt der
Registry-Read, die Topologie-Achse liest `primary-role` nur als
Ableitungsquelle (D9).

### IC-7 `scripts/lib/isolation.py` + `scripts/lib/context.py` (P2)

`_opencode_entry_point` bleibt die **einzige** Entry-Point-Quelle und wird um
die Topologie-Konjunktion erweitert; der ActiveSet-Konjunkt bleibt unverändert
(A5). **Aufrufer und Auflösungs-Ort:** `isolation.py::_sync_opencode_runtime_gate`
löst pro Provider genau **einmal** `resolve_topology(config, provider, …,
mode=<aus _resolve_orch_mode>, …)` auf und reicht das `TopologyResolution`-Objekt
als `topology=` an `_opencode_entry_point(...)` weiter; dasselbe Objekt verwendet
`context.py::_init_provider_settings_json` (und die Entry-Point-Vorprüfung in
`init_settings_json`) für den `emit_default_agent`-Bool. Das Prädikat hat
**keinen** eigenen `mode`-Parameter; `role_emitted_for_provider` löst `mode` wie
heute intern über `_resolve_orch_mode(..., validate=False)` auf, wenn es keinen
Kontext bekommt.

```python
def _opencode_entry_point(
    provider: str,
    provider_config: dict,
    active_set,
    config: dict | None = None,
    *,
    topology: "TopologyResolution | None" = None,  # einmal im Aufrufer aufgelöst
) -> str | None:
    role = providers.explicit_primary_role(provider_config, provider)
    if role is None:
        return None
    if config is not None and not role_emitted_for_provider(
        role, active_set, config, provider,
    ):
        return None
    if active_set is not None and role not in active_set.roles:
        return None
    if topology is not None and topology.effective != "primary":
        return None
    return role
```

Damit greift die bestehende D1a-Invariante: kein `default_agent` ⇒ kein Deny,
Gate wird laut suspendiert (`orchestrator-topology.gate-inactive`, IC-5/AC-20).

**Zweiter Schreiber — in den bestehenden `emit_default_agent`-Pfad gefaltet
(B1):** `context.py::apply_settings_surface_shape` behält **exakt** seine
bestehende Signatur; es kommt **kein** `topology_effective`-Parameter hinzu:

```python
def apply_settings_surface_shape(
    content: str,
    pc: dict,
    capabilities: dict | None = None,
    *,
    emit_default_agent: bool = True,   # #1090/D16 — unverändert
) -> str: ...
```

Der Aufrufer `context.py::_init_provider_settings_json` berechnet den bereits
vorhandenen Bool als Konjunktion:

```python
emit_default_agent = role_emitted_for_provider(primary_role, active_set, config, provider) \
    and topology.effective == "primary"
```

Begründung (B1): `emit_default_agent` ist bereits der einzige Steuerparameter
für „schreibe `default_agent`"; ein zweiter Parameter wäre eine parallele
Wahrheit. Topologie und ActiveSet/Mode sind zwei Gründe für **denselben** Bool.
`apply_settings_surface_shape` läuft nur bei der **Erst-Erzeugung** der
Settings-Datei (Datei fehlt); es löscht keinen Nutzerwert. Bestehende Dateien
gehen ausschließlich über `_sync_opencode_runtime_gate` /
`_merge_default_agent`.

**Migrationsregel:**

| Fall | Verhalten |
|---|---|
| Frisches v2-Projekt, effektive Topologie ≠ `primary` | Datei ohne `default_agent`; **kein** `default-agent-conflict` (der gilt nur für nutzereigene Werte); die `gate-inactive`-WARNUNG bleibt laut (AC-20) |
| Bestehender Wert verwaltet (`default-agent`-State-Record) | `_merge_default_agent` rollt beim Wechsel `primary → subagent` zurück (vorhanden) |
| Bestehender Wert nutzereigen (kein State-Record), Topologie ≠ `primary` | WARN `orchestrator-topology.default-agent-conflict` mit Handlungssatz; **kein** Auto-Delete |
| Gate wäre gewollt, aber Topologie ≠ `primary` | Gate-Deny wird nicht geschrieben; WARN `orchestrator-topology.gate-inactive` (IC-5/AC-20) |
| `topology: primary` | heutiges Verhalten unverändert |

Der Check-ID-Name `orchestrator-topology.default-agent-conflict` ersetzt die
frühere Formulierung „WARN default-agent-conflict" und ist in IC-5 registriert;
der bestehende Laufzeit-Text `opencode.default-agent.dangling` bleibt als
Emitter-Detail erhalten, die stabile ID ist die des Konsistenz-Checks.

### IC-8 `scripts/lib/config.py::_validate_orchestrator_topology` (neu, P1; P3-Erweiterung)

```python
def _validate_orchestrator_topology(config: dict, config_path: Path) -> None: ...
```

Aufgerufen aus `_validate_config` **nach** `_validate_providers`. stdlib-only,
kein `jsonschema`; stderr `ERROR: <config-path>: …`, dann `sys.exit(1)`; läuft
in `sync` **und** `--validate`.

| Regel | stabiler Teilstring | Phase |
|---|---|---|
| (a) unbekanntes Enum | `ERROR: <path>: unknown orchestrator.topology` | P1 |
| (b) `topology` explizit × `mode: main-chat` | `orchestrator.topology conflicts with orchestrator.mode: main-chat` | P1 |
| (b) `topology` explizit × `enabled: false` | `orchestrator.topology conflicts with orchestrator.enabled: false` | P1 |
| (c) Override (auch Same-Object) | `provider-overrides.<P>.topology conflicts with provider-overrides.<P>.mode: main-chat` | P1 |
| (d) `singleton` × N>1 | `orchestrator.singleton conflicts with orchestrator.max-instances` | **P3** |
| (d) `singleton: false` | `orchestrator.singleton: false is not supported (use max-instances)` | **P3** |
| (e) `primary` × N>1 (selber Scope) | `orchestrator.topology: primary conflicts with orchestrator.max-instances` | **P3** |

`<P>` wird durch den tatsächlichen Provider-Namen ersetzt. AC-17 assertet die
**Teilstrings**, nicht die Satzform. Cross-Scope wird hier bewusst **nicht**
abgelehnt (das ist die WARNING-Regel aus D3/IC-5).

### IC-9 `hooks/1-generic/orchestrator-guard-impl.sh` (P3-only, OQ-2 = A)

- Sentinel-Grammatik:
  `^#agent-meta:agent=([A-Za-z0-9_-]+)(?:\s+id=([A-Za-z0-9._-]+))?$`.
- Die ID wird **nur** via `hook_audit_log_append` ins Audit-Log geschrieben,
  **niemals** in einer Allow/Deny-Entscheidung benutzt (audit-only).
- Bestehender Audit-Log-Redaction-/Rechte-Pfad bleibt unverändert.

### IC-10 Weitere P3-Contracts

- `schemas/a2a-handoff.schema.json`: optionales Feld `orchestrator_id`
  (`[a-z0-9][a-z0-9._-]{0,39}`) plus `metadata.scope_id`; der Dispatch-Zielname
  bleibt `orchestrator` (keine `#`-Suffixe).
- `scripts/lib/checkpoint.py`: kein neues Verzeichnis; Session-ID-Komposition
  ausschließlich über IC-2.
- Viz-Events: eine Datei, Felder `orchestrator_id`, `scope_id`, `spawned_by`,
  `spawned_at` — kein Datei-Sharding.

### IC-11 `scripts/lib/sync_pipeline.py::emit_topology_summary` (neu, P2)

OQ-4 = A braucht einen **Produzenten**, nicht nur eine Satzform. Ein neuer
Summary-Schritt läuft in `sync_pipeline` **nach** der Provider-Schleife und
**vor** `log.finish`:

```python
def emit_topology_summary(
    config: dict,
    provider_config: dict,
    providers: Sequence[str],
    log: SyncLog,
    *,
    mode: str,                         # "sync" | "check" | "validate"
    capabilities: dict | None = None,
) -> None: ...
```

**Vertrag:**

| Aspekt | Regel |
|---|---|
| Bedingung | Nur für Provider, deren `TopologyResolution.source == "derived"` ist (Projekt-Key ungesetzt **und** kein Provider-Override). Bei expliziter Deklaration entsteht **keine** Zeile. |
| Modus | Nur `mode == "sync"`. In `--check` und `--validate` wird die Funktion **nicht aufgerufen** ⇒ keine Byte-/Ausgabe-Drift (AC-6). |
| Text (exakt, `derived_from` gesetzt) | `topology: <effective> (derived from providers.<P>.primary-role)` — `<P>` ist der Provider aus `derived_from`. |
| Text (exakt, kein `primary-role`) | `topology: subagent (derived: active-set default)` |
| Kanal | `log.note("topology", <line>)` — INFO-Zeile in der Sync-Zusammenfassung; keine Datei, kein Finding, kein Exit-Code-Einfluss. |
| Dedup | Höchstens eine Zeile pro Provider und Lauf. |

`emit_topology_summary` schreibt nichts und ändert keine gerenderten Bytes; es
ist die **einzige** Stelle, an der die Ableitung sichtbar wird (kein INFO-Finding
in IC-5).

---

## mode × topology-Interaktionsmatrix (normativ für AC-5)

Lesart: **Zeile = effektiver `mode`** (nach `variables._resolve_orch_mode`),
**Spalte = deklarierte Topologie**. Die Matrix ist die Testgrundlage für AC-5
und die Ableitungsregel für IC-8 (b)/(c).

| `mode` \ `topology` | `primary` | `subagent` | `hybrid` |
|---|---|---|---|
| `strict` | Einstieg, strikte Gates, 1 Instanz | Main Chat spawnt 1..N, strikte Gates | positions-agnostisch, strikte Gates¹ |
| `advisory` | Einstieg, advisory Gates | Main Chat spawnt 1..N, advisory Gates | positions-agnostisch, advisory Gates¹ |
| `main-chat` | **ERROR** (gleicher Scope, inkl. Same-Object) / **inert + WARNING** (Cross-Scope) | **ERROR** (gleicher Scope) / **inert + WARNING** (Cross-Scope) | **ERROR** (gleicher Scope) / **inert + WARNING** (Cross-Scope) |

¹ **`hybrid`-Degradations-Fußnote:** „positions-agnostisch" beschreibt die
*deklarierte* Semantik (D1/D2), **nicht** das v1-Verhalten. Weil
`topology_verified_state.hybrid == "UNVERIFIED"` ist, degradiert in v1 **jede**
`hybrid`-Zelle auf `subagent` (Fail-safe, IC-2); AC-5 testet die Spalte daher als
`hybrid → subagent`-Degradierung, nicht als dritte Position.

**Ableitungsregel:** `topology` ändert nie die Gate-Stärke; `mode` ändert nie
die Position. `main-chat` ist die einzige Dominanzzelle (Rolle existiert nicht
⇒ Topologie inert). Cross-Scope `primary` + globales N>1 ⇒ WARNING
`instances-clamped`, effektiv N=1. Bei `mode != main-chat` und effektiver
Topologie `subagent` entfällt der Entry-Point samt Gate-Deny
(`gate-inactive`-WARNING, nicht still).

## Provider-Matrix (Stand vor P0)

Ableitung ausschließlich aus vorhandenen Capability-Keys
(`main_agent_selectable`, `subagent_dispatch`, `parallel_execution`); Zellen
ohne Datenbasis sind `UNVERIFIED ⇒ no`. Die Tabelle zeigt den Stand **vor P0**
(N = 0). Nach P0 gilt die Upgrade-Prozedur: `25 + N` datenabgeleitet /
`15 − N` `UNVERIFIED ⇒ no`, **N gemessen** aus der Evidenzliste.

| Provider | `primary` | `subagent` | `hybrid` | N>1 |
|---|---|---|---|---|
| **Claude** | **yes** — `main_agent_selectable: true` | **yes** — `subagent_dispatch: true` | **no→subagent** — `UNVERIFIED` | **yes** — `parallel_execution: true` |
| **Opencode** | **yes** — `mode: primary` + `default_agent` (VERIFIED-RUNTIME) | **yes** — `subagent_dispatch: true`; neu: `mode: subagent` bzw. kein `mode` (v1) und kein `default_agent` | **no→subagent** — `UNVERIFIED`; `mode: primary` ist nicht per `task` spawnbar (#1006, Design §16 Nr. 2) | **yes** — `parallel_execution: true` |
| **Gemini / Antigravity** | **no→subagent** — `main_agent_selectable: false` | **yes** — generierter Roster | **no→subagent** — `UNVERIFIED` | **yes** — `parallel_execution: true` (`native-batch`) |
| **Continue** | **yes** — `main_agent_selectable: true` (`cn --agent`) | **degraded→sequential-text** — `subagent_dispatch: false` (nur Text-Mention) | **no→subagent** — `UNVERIFIED` | **no** — `parallel_execution: false` |
| **Copilot** | **no→subagent** — `main_agent_selectable: false` | **yes** — `agents:`-Allow-List + `agent`-Tool (#855) | **no→subagent** — `UNVERIFIED` | **no** — `parallel_execution: false` |
| **Mammouth** | **no→subagent** — Quell-Key UNVERIFIED (Design §16 Nr. 5) | **yes** — natives `task` | **no→subagent** — `UNVERIFIED` | **no** — `parallel_execution: false` |
| **Codex** | **no→subagent** — Quell-Key UNVERIFIED (Design §16 Nr. 4) | **yes** — `spawn_agent`/`wait_agent` | **no→subagent** — `UNVERIFIED` | **yes** — `parallel_execution: true` |
| **ZCode** | **no→subagent** — `main_agent_selectable: false` | **yes** — `Agent`-Toolcall + Bootstrap-Roster | **no→subagent** — `UNVERIFIED` | **no** — `parallel_execution: false` |
| **KimiCode** | **yes** — `main_agent_selectable: true` (Design §16 Nr. 6) | **yes** — `Agent` + `AgentSwarm` | **no→subagent** — `UNVERIFIED` | **yes** — `parallel_execution: true` |
| *(custom / nicht im Registry)* | **no** — `UNVERIFIED`, kein Registry-Datum | **no** — `UNVERIFIED`, kein Registry-Datum | **no→subagent** — Fail-safe-Ziel, keine Capability-Zusage | **no** — keine Capability-Daten |

**Invariante:** `topology_support.* == true` ⇒ `topology_verified_state.* !=
UNVERIFIED` (AC-15); äquivalent dazu wird bei `topology_support.* == false`
**oder** `UNVERIFIED` **nie** ein unvalidierter Wert durchgereicht — `effective`
entstammt ausschließlich `topology_degrade` oder dem Fail-safe `subagent` (IC-2,
Fallback-Regel). Fällt der Fail-safe dabei auf den deklarierten String
(Continue: declared `subagent`), ist das **keine** Degradierung: `degraded_from =
None`, keine WARNING; die Zelle bleibt `no`/`degraded`.
**Zählregel:** 25 Basis-Zellen + N belegte Upgrades (AC-16). **Normative Kopie
für AC-16 ist genau diese Tabelle** (die Design-Matrix §7 ist Referenz, nicht
zweite Wahrheit). **Loudness:** jede **tatsächliche Degradierung**
(`degraded_from is not None`, d. h. declared ≠ effective) erzeugt beim Sync genau
eine `orchestrator-topology.degraded`-WARNING pro Provider und Lauf — nicht jede
`no`-Zelle eines unveränderten Projekts (sonst warnt jeder Sync, vgl. D9/R5).

---

## Datenfluss

```
project.yaml                      ai-providers.yaml          provider-capabilities.yaml
orchestrator.topology  ---------+ providers.<P>.primary-role   topology_support
orchestrator.provider-  |        |                             topology_degrade
  overrides.<P>.topology|        |                             orchestrator_instances
orchestrator.max-       |        |                             topology_verified_state
  instances (P3)        |        |                                        |
                         v        v                                        v
                   [topology.resolve_topology(mode=...)]  <----------------+
                         |
      +------------------+-------------------+--------------------+
      v                  v                   v                    v
 ORCH_TOPOLOGY_*   provider_transform    isolation           Konsistenz
 (+ EXPLICIT)      (mode: primary|sub)   (_opencode_entry)   (WARNING)
      |                  |                   |                    |
      v                  v                   v                    v
  Templates (nur   .opencode/agents/    opencode.json        sync-Report
  bei EXPLICIT)    orchestrator.md      default_agent        + Sync-Summary-Zeile
      |                                                      (kein --check-INFO)
      v
 [_validate_orchestrator_topology]  (vor jedem Schreiben; hart)
```

**Eigentum:** `topology.py` besitzt nur die Auflösung; es schreibt nichts, kennt
keinen Pfad und keinen Provider-Namen. `provider_transform`/`isolation`/
`context` setzen ausschließlich den aufgelösten Wert. `consistency/topology.py`
schreibt nie. `config.py` bricht hart ab, bevor geschrieben wird.

**Zustands-Eigentum bei N>1 (P3-only):**

| Artefakt | Eigentümer | Namespace / Konsument |
|---|---|---|
| `<checkpoint-dir>/<session>.json` | je Instanz | Session-ID = `<base>__<orchestrator-id>`; Konsument: `recovery.py`/`CheckpointStore` |
| `<progress-dir>/current.md` | **nur** Wurzel-Session | unverändert; einziger maschinell gelesener Fortschritt |
| `<progress-dir>/progress-<orchestrator-id>.md` | je Instanz | **rein menschlich lesbar**; kein Code-Konsument |
| `.meta-viz/events.jsonl` | gemeinsam (append) | Felder `orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at`; **keine** Datei-Shards |
| Delegations-Tracker | je Instanz | nur im Kontext — kollidiert nicht |
| `.opencode/agents/orchestrator.md` | Framework (eine Datei) | Instanz-Identität ist **kein** Dateiname |

---

## Multi-Instanz-Vertrag (P3-only)

> **Phasengeltung:** Dieser gesamte Abschnitt ist **P3-only** und **nicht** Teil
> der v1-DoD (OQ-5 = A). v1 referenziert weder `max-instances` noch
> `orchestrator_id`.

### Identität

- **Form:** `orchestrator_id` = `[a-z0-9][a-z0-9._-]{0,39}`.
- **Quelle:** Der Main Chat vergibt sie beim Spawn, deterministisch aus dem
  Scope-Schlüssel (Plan-ID/Task-Ref, Branch-Name oder PR-Nummer), normalisiert
  nach `_sanitize_component`-Regeln.
- **Default:** `None` bei `max-instances == 1` → keine sichtbare Änderung an
  Rollennamen, Dateinamen, Session-IDs.
- **Adressierung:** Dispatch-Ziel bleibt `orchestrator`; die Identität reist im
  Envelope (`orchestrator_id`, `metadata.scope_id`).
- **Audit-Datensatz:** `{orchestrator_id, scope_id, spawned_by, spawned_at}`.
  `spawned_by` ist der Spawner of record (`main_chat`); `spawned_at` der
  Spawn-Zeitpunkt. Vollständig im Viz-Event, reduziert auf die ID im
  Guard-Audit-Log.
- **Fehlende ID (N>1):** HARD REJECT durch den Main Chat (Prompt-Vertrag) und
  WARNING im Guard-Audit (`id=unset`).
- **Doppelte ID / Scope-Überlappung:** HARD ERROR **beim Spawn**, beide
  Eigentümer im Text. Kein Laufzeit-Race; die Prüfung liegt vor dem ersten
  Dispatch.

### Scope-Regel

Ein Scope ist eine Menge von Dateien/PRs/Branches. Zwei Instanzen mit
überlappendem Scope dürfen nicht koexistieren. Die Prüfung ist
**Main-Chat-Pflicht** (Prompt + A2A-Gate G2), nicht Framework-Runtime — es gibt
keinen Interception-Punkt (dieselbe akzeptierte Grenze wie
`validate_envelope`).

### Zustands-Namespaces

| Artefakt | N=1 (Default) | N>1 |
|---|---|---|
| Checkpoint | `<checkpoint-dir>/<base>.json` | `<checkpoint-dir>/<base>__<id>.json` |
| Fortschritt | `<progress-dir>/current.md` | `progress-<id>.md` (Instanz, nur menschlich) + `current.md` (nur Wurzel, maschinell) |
| Event-Log | `.meta-viz/events.jsonl` | gleich, Felder `orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at` |
| Tracker | im Kontext | im Kontext (je Instanz) |

Eine Identität, zwei Dateinamen: `<base>__<id>` (Checkpoint) und
`progress-<id>.md` (Mensch) leiten sich aus **derselben** normalisierten
`orchestrator_id` ab.

### Teardown / Aggregation

Nur der Main Chat sieht alle Instanzen; er aggregiert Ergebnisse und schreibt
den Gesamt-Fortschritt. Keine Orchestrator→Orchestrator-Koordination (G3).
Instanz-Teardown = Kontextende; kein „Abmelden"-Artefakt.

### Gate-Wortlaut (P3-Amendment)

Mit `max-instances` ersetzt G2 „**genau einen**" durch „**höchstens
{{ORCH_MAX_INSTANCES}}**"; v1 rendert keinen `ORCH_MAX_INSTANCES`-Platzhalter.

---

## Phasenzerlegung

Jede Phase ist eigenständig mergebar (grün, rückrollbar) und lässt
`sync --check` auf unveränderten Consumer-Projekten byte-identisch. Größen nach
`spec-plan-workflow` (S/M/L/XL).

| Phase | Größe | Dateien (Kern) | Was sie landet |
|---|---|---|---|
| **P0 — Capability-Daten, Verified-State & Probe-Ausführung** | **M (5)** | `config/provider-capabilities.yaml`, `docs/spikes/2026-11-03-issue-1077-topology-probe.md` (**Evidenz-Dokument**), `scripts/topology-probe.py` (read-only Probe-Harness), `tests/test_topology_capability_invariant.py`, `tests/test_topology_probe_evidence.py` | Vier Capability-Strukturen je Provider + Invariante; **die fünf Provider-Probes (§16 Nr. 2–6 des Designs) werden jetzt ausgeführt** und im Spike-Doc aufgezeichnet (OQ-1 = B). Nur belegte Zellen → `yes`; unbelegte bleiben `no` (eine WARNING entsteht nur bei tatsächlicher Degradierung, `degraded_from is not None`; AC-16). |
| **P1 — Config-Fläche, Auflöser, Validator, Flags** | **L (9–11)** | `config/project-config.schema.json`, `scripts/lib/topology.py` (neu), `scripts/lib/config.py` ((a)–(c), globale Flags), `scripts/lib/variables.py`, `scripts/lib/standalone.py`, `scripts/lib/consistency/placeholders.py`, drei neue Tests, Doku-Beispiele | Enum + Defaults, hartes Same-Scope-Validieren (a)–(c), Auflösekette inkl. `support == false`-Fallback und `effective ∈ VALID_TOPOLOGIES`, flache Topologie-Flags, fail-closed Conditional-Registrierung. **Kein** Eingriff in `active_set.py`/`providers.py`: das Prädikat existiert seit #1090, ein neuer `primary_role`-Accessor entfällt (B1). |
| **P2 — Emission, laute Degradierung, Builder-Default** | **L (11–12)** | `provider_transform.py`, `isolation.py`, `context.py`, `agent_sync.py`, `sync_pipeline.py` (IC-11), `consistency/topology.py` (neu), `consistency-check.py`, vier Tests, `tests/fixtures/topology-golden/*`, `config/ai-providers.yaml` (Kommentar) | `subagent` auf Opencode funktioniert real; kein `default_agent` bei Topologie ≠ `primary` (in den bestehenden `emit_default_agent`-Bool gefaltet); `agent_sync.py::_should_skip_role` ruft das **bestehende** Prädikat statt des `ORCH_MODE_MAIN_CHAT`-Reads; WARN `degraded`/`default-agent-conflict`/`gate-inactive` + Sync-Summary-Zeile (**kein** `--check`-INFO). |
| **P3 — Multi-Instanz, Zustands-Namespaces & Guard-Audit** | **L (14–16)** | `project-config.schema.json` (`max-instances` max 8, `singleton`), `config.py` ((d)/(e)), `variables.py` (`_instance_flags` **plus** Registrierung von `ORCH_MAX_INSTANCES`/`ORCH_SINGLETON_DECLARED` in der `strip_inactive_conditional_blocks`-Whitelist, `_FALSE_DEFAULT_CONDITIONALS` und — via `standalone.py` — `_CONDITIONAL_FALSE_FLAGS` **sowie** `consistency/placeholders.py::_BUILTIN_VARS`), `topology.py`, `consistency/topology.py` (`singleton-redundant`-INFO), `a2a-delegation-gates.md`, `orchestrator-guard-impl.sh` (**OQ-2 = A**), `tests/test_orchestrator_guard_hook.py`, `checkpoint.py`, `schemas/a2a-handoff.schema.json`, `delegation_syntax.py`, Viz-Emitter, zwei Tests | N>1 sicher: presence-only `singleton` (mit redundantem INFO bei N=1), ID, Session-ID-Komposition, Event-Tagging, Gate-Wortlaut mit `max {{ORCH_MAX_INSTANCES}}`, Guard-Audit-ID. **OQ-2/OQ-3 sind P3-only.** |
| **P4 — Regel- und Doku-Amendment** | **S–M (5–7)** | `rules/1-generic/a2a-delegation-gates.md`, `agents/1-generic/orchestrator.md`, `agents/1-generic/_reference-agent.md`, `docs/concepts/active/orchestrator-topology.md` (neu), `docs/concepts/active/singleton-orchestrator-architecture.md`, `CHANGELOG.md` | Neue Gate-Formulierung (conditional, else wortgleich, ohne Instanz-Platzhalter), Concept-Doc + Cross-Links. |

**Summe:** 44–51 Datei-Berührungen (mit Doppelzählungen von
`project-config.schema.json`, `config.py`, `topology.py`, `consistency/topology.py`),
**XL** (öffentliche Config-Contracts + Schema + mehr als eine Subsystemgrenze).

**v1 = P0–P2 + P4.** P0 ist v1-Bestandteil, aber **keine Spec-Vorbedingung**:
die Spec hängt an der Upgrade-**Regel**, nicht an einem bereits gemessenen N.

---

## Acceptance Criteria

> **v1-DoD (OQ-5 = A):** AC-1…AC-7, AC-13…AC-16, AC-18, AC-19, AC-20 sowie die
> **P1-Zeilen** von AC-17 und das **P0-Gate**. AC-8…AC-12 und die **P3-Zeilen**
> von AC-17 sind **P3-only** und nicht Teil der v1-DoD.

Jedes Kriterium ist nummeriert, testbar und in Given/When/Then-Form formuliert.
Jedes AC referenziert mindestens einen Interface-Contract.

### AC-1 — Schema deklariert die Fläche, der Validator erzwingt

**Given** ein Projekt mit `orchestrator.topology: subagent`, **when**
`config/project-config.schema.json` validiert wird, **then** ist das Enum
akzeptiert und die `mode`-Interaktion dokumentiert; **when** zusätzlich im
selben Scope `mode: main-chat` steht, **then** lehnt
`_validate_orchestrator_topology` mit rc≠0 ab (nicht das Schema).
*Contracts:* IC-1, IC-8. *Test:* Schema-Test + Validator-Test.

### AC-2 — Auflöser meldet unbekannte Enum-Werte handlungsfähig

**Given** ein unbekannter `topology`-Wert, **when** `resolve_topology(...)`
läuft, **then** wirft es `SyncError` mit Hint; der Same-Scope-`main-chat`-
Konflikt kommt ausschließlich aus dem stdlib-Validator (kein `jsonschema`).
*Contracts:* IC-2, IC-8. *Test:* Fehlertext-Assertion + Validator-Test.

### AC-3 — Emission folgt der Auflösung, Degradierung ist laut

**Given** eine effektive Topologie, **when** emittiert wird, **then** setzt
`provider_transform` `mode` gemäß IC-6 und der Per-Provider-Fall ist im Code
kommentiert; **when** eine Zelle degradiert, **then** existiert genau eine
`orchestrator-topology.degraded`-WARNING pro Provider und Lauf.
*Contracts:* IC-2, IC-5, IC-6. *Test:* Transform-Test + Konsistenz-Test.

### AC-4 — Concept-Doc vollständig und verlinkt

**Given** das Repo, **when** die Doku geprüft wird, **then** erklärt
`docs/concepts/active/orchestrator-topology.md` die drei Topologien, die
Support-/Degradierungsmatrix, die Multi-Instanz-Adressierung **und** den
`hybrid`-Deviationssatz (D2); die Singleton-Concept und die A2A-Rule verlinken
darauf. Die Multi-Instanz-Passage ist ausdrücklich als **„P3, designed, not
shipped"** markiert (kein v1-Versprechen). *Contract:* IC-1. *Test:*
Doku-Existenz + Link-Check (`consistency/docs.py`-Muster) + Text-Assertion auf
den P3-Marker.

### AC-5 — Testabdeckung der Kernflächen

**Given** die Testsuite, **when** sie läuft, **then** existieren Tests für Enum,
die **3×3-Matrix aus „mode × topology-Interaktionsmatrix"** (alle neun Zellen
inkl. der `main-chat`-ERROR-/inert-Regel), `main-chat`-Konflikt und abgeleiteten
Default. *Contracts:* IC-1, IC-2, IC-8. *Test:* vier Testmodule aus P1/P2.

### AC-6 — Kein Verhaltenswechsel ohne Key

**Given** ein unverändertes Consumer-Projekt ohne `orchestrator.topology`,
**when** `sync --check` läuft, **then** ist die Ausgabe byte-identisch; die
Golden-Fixtures „Rolle inaktiv + Key unset" und „Rolle aktiv + Key unset"
rendern exakt die heutigen Bytes.
*Contracts:* IC-4, IC-6. *Test:* `tests/test_ac01_render_identity.py` +
`tests/fixtures/topology-golden/*`.

### AC-7 — Cross-Scope ist genau eine WARNING

**Given** global gesetzte Topologie und `provider-overrides.<P>.mode:
main-chat`, **when** der Sync läuft, **then** existiert genau eine
`orchestrator-topology.main-chat-supersedes`-WARNING und kein Fehler (rc 0).
*Contracts:* IC-5, IC-8. *Test:* Konsistenz-Test.

### AC-8 — (P3-only) `max-instances`/`singleton`-Schema

**Given** eine konsistente Config, **when** validiert wird, **then** akzeptiert
das Schema `max-instances` (min 1, **max 8**, Default 1; der Key existiert vor
P3 nicht) und `singleton` (nur `true`, **kein** `default`); `singleton` present
+ N>1 ist ein harter Validator-ERROR; `singleton` present + N=1 ist **kein**
Fehler, sondern das INFO `orchestrator-topology.singleton-redundant` (rc bleibt
0); `--validate` ist grün.
*Contracts:* IC-1, IC-5, IC-8. *Test:* Schema-Test (beide Richtungen) +
Validator-Test + Konsistenz-Test (INFO).

### AC-9 — (P3-only) `primary` × N im selben Scope

**Given** `topology: primary` und `max-instances > 1` im selben Scope, **when**
validiert wird, **then** ist das ein harter ERROR; **given** Provider-Override
`primary` bei globalem N>1, **then** ist es eine WARNING und effektiv N=1.
*Contracts:* IC-2, IC-5, IC-8. *Test:* Validator-Test + Konsistenz-Test.

### AC-10 — (P3-only) Zustands-Pfade

**Given** N=1, **when** ein Checkpoint geschrieben wird, **then** entsteht exakt
der heutige Pfad; **given** N=2, **then** entstehen `<base>__<id>`-Dateien und
`validate_session_id` akzeptiert die Komposition.
*Contract:* IC-2 (`compose_instance_session_id`). *Test:*
`tests/test_checkpoint_paths.py`-Erweiterung.

### AC-11 — (P3-only) Audit-Datensatz vollständig, audit-only

**Given** N>1, **when** Events geschrieben werden, **then** tragen sie
`orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at`; das Log bleibt eine
Datei; `viz-report` konsumiert unverändert; das Guard-Audit-Log trägt die ID,
**und die Reduktion des Audit-Datensatzes auf `orchestrator_id` ist im
Guard-Audit dokumentiert** (Feldname + Reduktionssatz, nicht nur implizit).
**Given** ein Sentinel mit `id=`, **when** der Guard entscheidet, **then** wird
die ID **nie** für Allow/Deny benutzt (**OQ-2 = A**).
*Contracts:* IC-9, IC-10. *Test:* Event-Fixture + Reader-Test + Hook-Test +
Audit-Text-Assertion.

### AC-12 — (P3-only) Abgrenzung der beiden Limits

**Given** die Schema-`description`s, **when** sie geprüft werden, **then** sind
`max-instances` (Anzahl Orchestratoren) und `max-parallel-agents` (Parallelität
innerhalb eines Orchestrators) gegeneinander abgegrenzt (Text-Assertion).
*Contract:* IC-1. *Test:* Schema-Text-Test.

### AC-13 — Capability-Strukturen vollständig

**Given** die Provider-Registry, **when** der Invariantentest läuft, **then**
trägt jeder registrierte Provider `topology_support`, `topology_degrade`,
`orchestrator_instances` **und** `topology_verified_state`.
*Contract:* IC-2 (Capability-Struktur). *Test:* Provider-Invariantentest
(Muster `test_provider_three_file_invariant.py`).

### AC-14 — Builder-Default

**Given** ein frisches Opencode-v2-Projekt mit `topology: subagent`, **when**
der Sync läuft, **then** enthält die Config **kein** `default_agent` auf der
Orchestrator-Rolle (der bestehende `emit_default_agent`-Bool ist `False`);
**given** ein verwalteter Wert, **when** `primary → subagent` wechselt, **then**
wird er zurückgerollt; **given** ein nutzereigener Wert, **then** entsteht die
WARN `orchestrator-topology.default-agent-conflict` (kein Auto-Delete) und der
ActiveSet-Konjunkt bleibt wirksam.
*Contracts:* IC-5, IC-7. *Test:* `tests/test_ac01_render_identity.py` +
Isolation-Test + Konsistenz-Test.

### AC-15 — Invariante: kein `yes` ohne State, kein Durchreichen ohne Support

**Given** eine Provider-Zelle mit `topology_support.* == true`, **when** der
Invariantentest läuft, **then** ist `topology_verified_state.* != UNVERIFIED`;
**given** eine `UNVERIFIED`-Zelle **oder** eine Zelle mit
`topology_support.* == false`, **when** aufgelöst wird, **then** wird der
deklarierte Wert **nie unvalidiert durchgereicht**: `effective` entstammt
ausschließlich `topology_degrade` (bzw. dem Fail-safe `subagent`) und liegt immer
in `VALID_TOPOLOGIES`; **given** der Fail-safe fällt auf denselben String wie die
Deklaration (Continue: declared `subagent`), **then** gilt `degraded_from = None`
und es entsteht keine WARNING (Koinzidenz, keine Degradierung). Eine
`yes`-Zelle existiert nur mit aufgezeichneter Probe-Evidenz **und** erfüllter
§3.1-Bedingung (P0-Gate, alle drei Bedingungen; Design §3.1 im Trace-Anker).
*Contracts:* IC-2, IC-5. *Test:* Provider-Invariantentest + Resolver-Test
(Support-false- und UNVERIFIED-Zweig) mit den Assertions `effective in
VALID_TOPOLOGIES` und `degraded_from == (declared if declared != effective else
None)`.

### AC-16 — Matrix-Zählung als gemessene Regel

**Given** die **normative Matrix dieser Spec** („Provider-Matrix (Stand vor
P0)"; Design §7 ist Referenz), **when** der Zähl-Test läuft, **then** gilt:
40 Zellen = **`25 + N` datenabgeleitet** / **`15 − N` `UNVERIFIED ⇒ no`**, wobei
**N aus der Evidenzliste des Spike-Docs gemessen** wird (`0 ≤ N ≤ 15`; die fünf
Probes sind die Evidenzquellen, eine Probe kann mehrere Zellen stützen) und
**0 spekulative `yes`** existieren. Jedes Zell-Upgrade erfüllt **alle drei**
P0-Gate-Bedingungen (Evidenz, State-Wechsel, §3.1-Zeile + Invariantentest).
**WARNING-Bedingung:** genau eine `orchestrator-topology.degraded`-WARNING pro
Provider und Lauf **nur wenn `degraded_from is not None`** (declared ≠
effective); eine unveränderte `no`-Zelle ohne Deklaration warnt **nicht**
(D9/R5). Der Test pinnt **keine** konkrete Endzahl.
*Contracts:* IC-2, IC-5. *Test:* Matrix-Zähl-Test + Konsistenz-Test
(Degradierungs-Zähler).

### AC-17 — Harte Validator-Teilstrings

**Given** eine widersprüchliche Config, **when** `sync` oder `--validate` läuft,
**then** bricht der stdlib-Validator mit rc≠0 ab (ohne `jsonschema`) und die
Meldung enthält den in IC-8 gepinnten Teilstring: **(P1)** unbekanntes Enum
(`unknown orchestrator.topology`), Same-Scope `main-chat` × Topologie (auch
Same-Object), `enabled: false` × Topologie; **(P3-only)** `singleton: false`,
`singleton` present × N>1, `primary` × N>1 im selben Scope. Jeder dieser
Teilstrings wird **assertet**, nicht nur dokumentiert. *Contract:* IC-8. *Test:*
`tests/test_orchestrator_topology_validator.py` (P1: alle vier P1-Teilstrings)
+ P3-Erweiterung.

### AC-18 — Fail-closed Conditional-Registrierung

**Given** ein ungesetzter Key, **when** ein Template mit
`{{#if ORCH_TOPOLOGY_EXPLICIT}}` rendert, **then** rendert exakt der heutige
else-Zweig (inkl. verschachteltem `ROLE_ORCHESTRATOR_ACTIVE`), kein Zweig
rendert doppelt; `ORCH_TOPOLOGY_*` steht in der Whitelist von
`strip_inactive_conditional_blocks`, `ORCH_TOPOLOGY_EXPLICIT`/`_PRIMARY`/
`_SUBAGENT`/`_HYBRID` in `_FALSE_DEFAULT_CONDITIONALS` (abwesend ⇒ inaktiv);
`_CONDITIONAL_FALSE_FLAGS` und `_BUILTIN_VARS` tragen dieselben Flags.
*Contract:* IC-4. *Test:* Golden-Fixtures + `check_builder_known_set` +
Conditional-Test.

### AC-19 — Sync-Summary-Zeile der Ableitung (v1)

**Given** ein Projekt ohne `orchestrator.topology` (und ohne Provider-Override),
**when** `sync` läuft, **then** gibt `emit_topology_summary` genau eine
INFO-Zeile pro abgeleitetem Provider aus, wörtlich
`topology: <effective> (derived from providers.<P>.primary-role)` (bzw.
`topology: subagent (derived: active-set default)`, wenn kein `primary-role`
existiert); **given** derselbe Zustand mit `--check` oder `--validate`,
**then** wird die Funktion nicht aufgerufen und die Ausgabe ist byte-identisch
zu heute; **given** ein explizit gesetzter Key, **then** existiert keine
Summary-Zeile. *Contract:* IC-11. *Test:*
`tests/test_topology_summary_line.py` (Text-Assertion + Mode-Negativtest) +
AC-6-Golden.

### AC-20 — Gate-Inactive ist laut (v1)

**Given** `mode != main-chat` und effektive Topologie ≠ `primary` (z. B.
`subagent`) auf Opencode, **when** der Sync das Gate aufbauen will, **then**
wird **kein** Deny geschrieben und genau eine WARN
`orchestrator-topology.gate-inactive` entsteht (Text nennt Provider, Topologie
und die Handlung); **given** effektive Topologie `primary`, **then** entsteht
diese WARN nicht. Kein rc≠0, kein stilles Absenken.
*Contracts:* IC-5, IC-7. *Test:* Isolation-Test + Konsistenz-Test.

### P0-Gate — Probe-Abnahme (v1-Bestandteil)

P0 ist abgeschlossen, wenn **jede** der fünf Probes (§16 Nr. 2–6 des Designs)
im Evidenz-Dokument `docs/spikes/2026-11-03-issue-1077-topology-probe.md` ein
**aufgezeichnetes Ergebnis** hat:

- **P0-1 … P0-5:** je Probe entweder (a) **Evidenz** — Befehl, Datum,
  Provider-Version, beobachtetes Ergebnis inkl. Fehlerfall — oder (b) die
  wörtliche Zeile **„not run — CLI unavailable"** mit Grund.
- **Upgrade-Regel (B3 — alle drei Design-§7-Bedingungen, nicht zwei):** Eine
  Matrix-Zelle wechselt nur dann auf `yes`, wenn **alle drei** gemeinsam
  erfüllt sind:
  1. **Evidenz aufgezeichnet:** `docs/spikes/…-topology-probe.md` enthält die
     zugehörige Probe mit Befehl, Datum, Provider-Version und beobachtetem
     Ergebnis (inkl. Fehlerfall).
  2. **State-Wechsel:** `topology_verified_state.<achse>` steht danach auf
     `DOCUMENTED` oder `VERIFIED-RUNTIME` (nie `UNVERIFIED`).
  3. **Invariante grün:** Die **§3.1-Zeile** (Design §3.1,
     Invocation-/Main-Loop-Checkliste) für die Position hat keine offenen
     `unverified`-Felder mehr — Ausnahme ausschließlich `prompt-caching` und
     `progress` — **und** der Invariantentest (AC-15/AC-16) deckt die Änderung
     ab.

  Ein `yes` ohne eine dieser drei Bedingungen ist ein Testfehler (AC-16), kein
  Datenpunkt.
- **Kein „unverifiziert für immer":** „not run" ist ein gültiges Ergebnis,
  lässt die Zelle `no` und ist **kein** Grund, die Probe zu wiederholen, bevor
  eine CLI verfügbar ist; eine WARNING entsteht nur bei tatsächlicher
  Degradierung (AC-16).
- **N wird gemessen:** Die Endzahl der Upgrades steht erst nach P0 fest; die
  Spec/AC-16 assertet die Bilanz, nicht eine geratene Zahl.

---

## Risiken (Top 5)

| # | Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| **R1** | **Zweite Skip-Stelle** (`main-chat`-Skip in `agent_sync.py` + neue Topologie-Logik) | Orchestrator verschwindet still oder wird doppelt gepruned | Das **bestehende** Prädikat `role_emitted_for_provider` (IC-3) bleibt einzige Datei-Emissions-Quelle; P2 stellt `agent_sync.py::_should_skip_role` auf das Prädikat um (der `ORCH_MODE_MAIN_CHAT`-Read entfällt); AST-/Grep-Assertion „genau eine Funktion entscheidet". |
| **R2** | **`default_agent` ↔ Gate-Deny-Kopplung + zweiter Schreiber** | Nutzer verliert Builder-Default oder Main-Chat-Schreibblockade | `_opencode_entry_point` bleibt einzige Quelle; `apply_settings_surface_shape` behält seinen bestehenden `emit_default_agent`-Bool (kein `topology_effective`; IC-7/AC-14); D1a-Invariante unverändert; WARN `orchestrator-topology.gate-inactive` (AC-20). |
| **R4** | **Byte-Identität bricht** durch unbedingte Textänderung oder `{{else}}` auf eigener Zeile | Jedes Consumer-Projekt meldet Drift nach Upgrade | Conditional-Rendering mit **inline** platzierten Markern und wortgleichem else-Zweig; AC-6 + AC-18; Golden-Fixtures „Rolle inaktiv/aktiv + Key unset". |
| **R8** | **N>1 ohne Zustands-Isolation** (P3) | Stiller Resume-Datenverlust | Harte Kopplung: `max-instances` existiert vor P3 nicht und wird gemeinsam mit `maximum: 8` und der Isolation eingeführt; kein Zwischenschritt mit `maximum: 1`. |
| **R10** | **Matrix-Zellen werden als Freigabe gelesen, obwohl `UNVERIFIED`** / Probe belegt nichts | Spec verspricht `hybrid`/N>1 ohne Evidenz | Upgrade-Prozedur (P0-Gate): `yes` nur mit **allen drei** Bedingungen — Evidenzzeile, State-Wechsel, §3.1-Zeile ohne offene `unverified`-Felder + grüner Invariantentest; AC-15/AC-16; unbelegte Zellen bleiben `no` und warnen nur bei tatsächlicher Degradierung. |

---

## Offene Fragen

**Keine — OQ-1…OQ-5 sind am 2026-11-04 entschieden** (Design §15; OQ-1 = B,
OQ-2 = A, OQ-3 = A, OQ-4 = A, OQ-5 = A). Es gibt in dieser Spec keinen
OQ-Block und keinen `DECISION-NEEDED`-Marker. Die Entscheidungen sind als
Fakten in D1–D10 eingefaltet; ein späterer Widerspruch ist ein
Änderungsbedarf (neue Revision), keine offene Frage.

---

## Trace-Anker

- **spec-id:** `SPEC-orchestrator-topology-2026-11-03` (unverändert aus dem
  Design übernommen; der Plan referenziert genau diesen Wert).
- **Issue:** #1077 (Body + Kommentar vom 2026-11-02).
- **Kontext-Issues:** #1007, #1006, #547 (Nicht-Ziel), #516 (Guard),
  #369 (Delegationstiefe).
- **Design-Quelle:** `docs/specs/2026-11-03-orchestrator-topology-design.md`,
  Rev. 4 vom 2026-11-04 — **§3.1** (Invocation-/Main-Loop-Checkliste, dritte
  Upgrade-Bedingung), §4 (Contracts), §7 (Matrix + Upgrade-Prozedur),
  §9 (Multi-Instanz, P3), §11 (Phasen), §12 (ACs), §15 (entschiedene OQ).
- **Phasen → AC:** P0 → P0-Gate, **AC-13, AC-15, AC-16** (AC-14 ist P2, nicht
  P0); P1 → AC-1, AC-2, AC-5, AC-17 (P1-Zeilen), AC-18; P2 → AC-3, AC-6, AC-7,
  AC-14, AC-19, AC-20; P4 → AC-4; P3 → AC-8…AC-12, AC-17 (P3-Zeilen).
- **Governance-Hinweis (A9/R12, Rev. 2/B5 — korrigiert):** Dieses Dokument
  trägt die acht literalen Spec-Überschriften (`## Problem`, `## Ziel`,
  `## Nicht-Ziele`, `## Interface Contracts`, `## Datenfluss`,
  `## Acceptance Criteria`, `## Offene Fragen`, `## Trace-Anker`) **zusätzlich**
  zur Design-Referenz. Das ist **kein** Grün-Machen: `consistency/spec_plan.py`
  klassifiziert über `_classify(name)` — `*-spike.md` → `spike`,
  `*-design.md` → `spec`, **alles andere (also auch `*-spec.md`) → `plan`**.
  Für diese Datei prüft `--validate-spec-plan` daher `REQUIRED_PLAN_SECTIONS`:
  **7 fehlende Plan-Abschnitte + 1 Traceability-Finding = 8 WARNINGs**
  (`spec-plan-required: false` ⇒ WARNING, nicht ERROR; `dod-traceability` aus ⇒
  Traceability-WARNING). Der Zustand ist — wie Design R12 — **bewusst
  akzeptiert** (WARNING-only, kein Fehler); die Überschriften bleiben trotzdem
  als menschenlesbare Spec-Struktur erhalten. Eine `_classify`-Korrektur ist
  **nicht** Teil dieser Spec.
