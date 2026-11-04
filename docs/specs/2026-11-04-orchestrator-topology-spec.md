# Orchestrator-Topologie konfigurierbar — Spec

> Status: Entwurf
> Revision: 1
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
- Degradierung ist laut: genau eine WARNING pro Provider und Lauf, nie stilles
  Absenken (AC-3, AC-7, AC-16).
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
| **D5** | Der Issue-Kommentar fordert eine von der Enum unabhängige Multiplizitäts-Achse mit hartem Konflikt statt stiller Präzedenz. | `orchestrator.max-instances` integer 1..**8** (**OQ-3 = A**, **P3-only**), kanonischer Wert. `orchestrator.singleton` presence-only Alias (`enum: [true]`, **kein Schema-`default`**, P3). Same-Scope-Konflikte (`singleton` present + N>1; `primary` + N>1) = harter ERROR; `singleton: false` = ERROR mit Hint „use max-instances". N>1 nur, wenn Capability `orchestrator_instances.multiple == true` und Zelle nicht `UNVERIFIED`. | Default 1 = heutiges Verhalten; kein stiller Vorrang. `max-instances` existiert **vor P3 nicht** — kein Zwischenschritt mit `maximum: 1`. |
| **D6** | Checkpoints sind eine Datei pro Session, Fortschritt ist eine Datei, Event-Log ist eine Datei; bei N>1 kollidieren sie. | Instanz-Identität ist ein State-Namespace, kein Rollenname: `orchestrator_id` = `[a-z0-9][a-z0-9._-]{0,39}`, Default `None` bei N=1. Session-ID = `<base>__<id>`. Fortschritt: `progress-<id>.md` **nur menschlich lesbar**; `current.md` bleibt maschinell gelesen. Event-Log bleibt eine Datei mit Feldern `orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at`. N=1 byte-identisch, kein Backfill. | N>1 ohne neue Verzeichnisstruktur und ohne Konsumenten-Bruch; `recovery.py` liest weiterhin nur Checkpoints. **P3-only.** |
| **D7** | Die Singleton-Regel ist heute über „es gibt genau einen" begründet; bei N>1 ist das falsch. | Drei mechanisch prüfbare Klauseln: **G1** Worker → orchestrator = HARD REJECT (immer); **G2** nur `main_chat` spawnt Orchestratoren, höchstens `max-instances`, eindeutige ID, disjunkter Scope, doppelte ID/Scope-Überlappung = HARD ERROR beim Spawn; **G3** orchestrator → orchestrator = HARD REJECT. | Anti-Recursion bleibt aus dem Envelope beweisbar (Spawner of record + fehlende Kante). Kein neues State-Artefakt; Scope-Registry ist P5, nicht v1. |
| **D8** | Der Guard arbeitet mit einem selbstdeklarierten Sentinel; Rollen-Identität ist von keinem Provider verifizierbar (#516). | Convention-Boundary bleibt. Sentinel darf optional `id=<id>` tragen; der Guard **parst** sie, nutzt sie **nie** für Allow/Deny und schreibt sie ins Audit-Log (**OQ-2 = A**, **P3-only**). „Bekannte Grenzen" wird um den Audit-Satz ergänzt. | Ehrlich: keine neue Sicherheitszusage, aber Nachvollziehbarkeit. Hook-Change + Test liegen in P3, nicht P4. |
| **D9** | Kein Projekt darf durch das Upgrade sein Verhalten ändern; gleichzeitig muss `topology: subagent` den Main Chat als Default behalten. | Key ungesetzt ⇒ exakt heutige Ableitung (`primary-role` + ActiveSet ⇒ `primary`, sonst `subagent`; `hybrid` nie abgeleitet). Key gesetzt (`subagent`) ⇒ `apply_settings_surface_shape` schreibt **kein** `default_agent`, `_opencode_entry_point` liefert `None`, Runtime-Gate wird laut suspendiert. Die Ableitung erscheint **nur** als Sync-Summary-Zeile (**OQ-4 = A**, **kein** `--check`-INFO). | `sync --check` bleibt byte-identisch; kein neues Rendering in bestehenden Templates, solange `ORCH_TOPOLOGY_EXPLICIT != "true"`. Nutzereigener `default_agent` wird nicht gelöscht, nur gewarnt. |
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
    effective: str             # "primary" | "subagent" | "hybrid"
    source: str                # "provider-override" | "project" | "derived"
    derived_from: str | None   # z.B. "providers.Opencode.primary-role"
    degraded_from: str | None
    degradation_reason: str | None
    verification_state: str    # Zelle aus topology_verified_state

def resolve_topology(
    config: dict,
    provider: str,
    *,
    provider_config: dict,
    capabilities: dict,
    mode: str,                 # bereits durch _resolve_orch_mode aufgelöst
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

**Vertrag:** Präzedenz `provider-overrides.<P>.topology > orchestrator.topology >
Ableitung aus providers.<P>.primary-role`. Ist die Zielzelle
`topology_verified_state == UNVERIFIED`, liefert der Resolver **nie** den
deklarierten Wert, sondern den konservativen Fallback aus `topology_degrade`
mit `degraded_from` + `degradation_reason = "capability cell UNVERIFIED"`.
`mode` kommt als Parameter herein; das Modul importiert `variables.py` **nicht**
(kein zweiter Mode-Resolver). `validate=False` liefert den normalisierten String
ohne zu werfen (Konsistenz-Checker).

**Fehlerpfade:** `SyncError` bei unbekanntem Enum-Wert;
`resolve_orchestrator_instances` wirft `SyncError` bei `singleton`-Widerspruch
oder `topology: primary` mit N>1 im selben Scope (D5);
`compose_instance_session_id` wirft `ValueError`, wenn die Komposition
`validate_session_id()` verletzt.

### IC-3 `scripts/lib/active_set.py::role_emitted_for_provider` (neu, P1)

```python
def role_emitted_for_provider(
    role: str,
    provider: str,
    config: dict,
    *,
    active_set: "ActiveSet | None" = None,
    provider_config: dict | None = None,
    capabilities: dict | None = None,
    mode: str | None = None,
) -> bool: ...
```

Einzige Quelle für „wird diese Rolle für diesen Provider erzeugt?". Drei
boolesche Konjunkte: (1) Rolle im ActiveSet, (2) Provider aktiv, (3)
`not _role_suppressed_by_mode(role, mode)` — `True` nur bei
`mode == "main-chat" AND role == "orchestrator"`. `main-chat` ist **kein**
Topologie-Wert. P1 landet **nur** Funktion + Unit-Test; die Call-Sites
(`agent_sync._should_skip_role`, `isolation._opencode_entry_point`) werden in P2
umgestellt.

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

### IC-5 `scripts/lib/consistency/topology.py` (neu, P2)

```python
def check_orchestrator_topology(
    agent_meta_root: Path, project_config: dict
) -> list[Finding]: ...
```

| Check-ID | Severity | Bedingung |
|---|---|---|
| `orchestrator-topology.degraded` | WARNING | `resolution.degraded_from is not None` (Provider kann den deklarierten Wert nicht ausdrücken **oder** Zelle ist `UNVERIFIED`) |
| `orchestrator-topology.hybrid-unverified` | WARNING | Deklaration `hybrid` und `topology_verified_state.hybrid == "UNVERIFIED"` |
| `orchestrator-topology.main-chat-supersedes` | WARNING | Cross-Scope: Provider-Override `mode: main-chat` bei übergeordnet gesetzter Topologie |
| `orchestrator-topology.instances-clamped` | WARNING | N>1, aber `orchestrator_instances.multiple == false` **oder** Cross-Scope `primary` + globales N>1 |
| `orchestrator-topology.unresolved-global-flags` | WARNING | Ein `ORCH_TOPOLOGY_*`-Platzhalter wurde provider-los gerendert |
| ~~`orchestrator-topology.derived`~~ | **entfällt** | **OQ-4 = A:** kein INFO-Finding; Ableitung nur als Sync-Summary-Zeile |

**Vertrag:** kein Schreiben, kein Exit, nur `Finding`s. Genau **eine** WARNING
pro Provider und Lauf (dedupliziert); `--check` bleibt rc 0.

### IC-6 `scripts/lib/provider_transform.py::_apply_agent_transform` (P2)

Die Ableitung wird von `explicit_primary_role(...)` auf
`resolve_topology(...).effective` umgestellt:

| effektive Topologie | opencode-native v1 | opencode-native v2 |
|---|---|---|
| `primary` (Rolle == entry role) | `mode: primary` | `mode: primary` |
| `subagent` | `mode` **nicht** geschrieben (heutiges v1-Verhalten) | `mode: subagent` |
| `hybrid` | wie `primary` (v1 nie gewährt → WARNING + Fallback) | wie `primary` |

Template-Fallbacks (`mode or template_fm["mode"]`) und der Write-Scope-Lock
(„primary ⇒ edit-deny") bleiben an `mode == 'primary'` gebunden — **keine**
zweite Bedingung.

**Ein Lesezugriff (A4):** In P1 entsteht
`scripts/lib/providers.py::primary_role(provider_config, provider, *, default: str | None = None)`
als **einziger** Lesezugriff. Beide Aufrufer werden migriert:
`context.py::apply_settings_surface_shape` → `default=None`;
`provider_transform.py::_apply_agent_transform` → `default="orchestrator"`
(heutige Allowlist-Bytes bleiben erhalten).

### IC-7 `scripts/lib/isolation.py` + `scripts/lib/context.py` (P2)

`_opencode_entry_point` liefert `None`, sobald die effektive Topologie
`subagent` ist; der ActiveSet-Konjunkt bleibt unverändert (A5):

```python
role = providers.primary_role(provider_config, provider, default=None)
if role is None:
    return None
if active_set is not None and role not in active_set.roles:
    return None
if resolve_topology(..., mode=mode).effective != "primary":
    return None
return role
```

Damit greift die bestehende D1a-Invariante: kein `default_agent` ⇒ kein Deny,
Gate wird laut suspendiert.

**Zweiter Schreiber (B2):**

```python
def apply_settings_surface_shape(
    content: str,
    pc: dict,
    capabilities: dict | None = None,
    *,
    topology_effective: str | None = None,
) -> str: ...
```

`topology_effective` ist die **aufgelöste effektive** Topologie (nicht
`variables["ORCH_TOPOLOGY"]`!). `None` = Legacy-Aufrufer, heutiges Verhalten
(byte-identisch). Ist `topology_effective != "primary"`:
`document.pop("default_agent", None)` und **kein** Schreiben. Ist
`topology_effective == "primary"`: heutiges Verhalten. Der Aufrufer
`_init_provider_settings_json` reicht `topology.effective` aus dem
Per-Provider-Loop durch.

**Migrationsregel:**

| Fall | Verhalten |
|---|---|
| Frisches v2-Projekt, effektive Topologie ≠ `primary` | Datei ohne `default_agent`; **kein** WARNING (AC-14) |
| Bestehender Wert verwaltet (`default-agent`-State-Record) | `_merge_default_agent` rollt beim Wechsel `primary → subagent` zurück (vorhanden) |
| Bestehender Wert nutzereigen (kein State-Record), Topologie ≠ `primary` | WARN `orchestrator-topology.default-agent-conflict` mit Handlungssatz; **kein** Auto-Delete |
| `topology: primary` | heutiges Verhalten unverändert |

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
UNVERIFIED` (AC-15). **Zählregel:** 25 Basis-Zellen + N belegte Upgrades (AC-16).
**Loudness:** jede `degraded→`/`no→`/`UNVERIFIED`-Zelle erzeugt beim Sync genau
eine WARNING pro Provider und Lauf.

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
| **P0 — Capability-Daten, Verified-State & Probe-Ausführung** | **M (5)** | `config/provider-capabilities.yaml`, `docs/spikes/2026-11-03-issue-1077-topology-probe.md` (**Evidenz-Dokument**), `scripts/topology-probe.py` (read-only Probe-Harness), `tests/test_topology_capability_invariant.py`, `tests/test_topology_probe_evidence.py` | Vier Capability-Strukturen je Provider + Invariante; **die fünf Provider-Probes (§16 Nr. 2–6 des Designs) werden jetzt ausgeführt** und im Spike-Doc aufgezeichnet (OQ-1 = B). Nur belegte Zellen → `yes`; unbelegte bleiben `no` mit genau einer WARNING. |
| **P1 — Config-Fläche, Auflöser, Validator, Flags** | **L (11–12)** | `config/project-config.schema.json`, `scripts/lib/topology.py` (neu), `scripts/lib/config.py` ((a)–(c), globale Flags), `scripts/lib/variables.py`, `scripts/lib/standalone.py`, `scripts/lib/consistency/placeholders.py`, `scripts/lib/providers.py` (`primary_role`), `scripts/lib/active_set.py` (Funktion + Unit-Test), drei neue Tests, Doku-Beispiele | Enum + Defaults, hartes Same-Scope-Validieren (a)–(c), Auflösekette, flache Topologie-Flags, fail-closed Conditional-Registrierung. `role_emitted_for_provider` landet **ohne** Call-Site. |
| **P2 — Emission, laute Degradierung, Builder-Default** | **L (10–11)** | `provider_transform.py`, `isolation.py`, `context.py`, `agent_sync.py`, `consistency/topology.py` (neu), `consistency-check.py`, drei Tests, `tests/fixtures/topology-golden/*`, `config/ai-providers.yaml` (Kommentar) | `subagent` auf Opencode funktioniert real; kein `default_agent` bei Topologie ≠ `primary`; `agent_sync.py` nutzt das Prädikat an der zweiten Stelle; WARNING + Sync-Summary-Zeile (**kein** `--check`-INFO). |
| **P3 — Multi-Instanz, Zustands-Namespaces & Guard-Audit** | **L (12–14)** | `project-config.schema.json` (`max-instances` max 8, `singleton`), `config.py` ((d)/(e)), `variables.py` (`_instance_flags`), `topology.py`, `a2a-delegation-gates.md`, `orchestrator-guard-impl.sh` (**OQ-2 = A**), `tests/test_orchestrator_guard_hook.py`, `checkpoint.py`, `schemas/a2a-handoff.schema.json`, `delegation_syntax.py`, Viz-Emitter, zwei Tests | N>1 sicher: presence-only `singleton`, ID, Session-ID-Komposition, Event-Tagging, Gate-Wortlaut mit `max {{ORCH_MAX_INSTANCES}}`, Guard-Audit-ID. **OQ-2/OQ-3 sind P3-only.** |
| **P4 — Regel- und Doku-Amendment** | **S–M (5–7)** | `rules/1-generic/a2a-delegation-gates.md`, `agents/1-generic/orchestrator.md`, `agents/1-generic/_reference-agent.md`, `docs/concepts/active/orchestrator-topology.md` (neu), `docs/concepts/active/singleton-orchestrator-architecture.md`, `CHANGELOG.md` | Neue Gate-Formulierung (conditional, else wortgleich, ohne Instanz-Platzhalter), Concept-Doc + Cross-Links. |

**Summe:** 43–50 Datei-Berührungen (mit Doppelzählungen von
`project-config.schema.json`, `config.py`, `topology.py`), **XL** (öffentliche
Config-Contracts + Schema + mehr als eine Subsystemgrenze).

**v1 = P0–P2 + P4.** P0 ist v1-Bestandteil, aber **keine Spec-Vorbedingung**:
die Spec hängt an der Upgrade-**Regel**, nicht an einem bereits gemessenen N.

---

## Acceptance Criteria

> **v1-DoD (OQ-5 = A):** AC-1…AC-7, AC-13…AC-16, AC-18 sowie die **P1-Zeilen**
> von AC-17 und das **P0-Gate**. AC-8…AC-12 und die **P3-Zeilen** von AC-17 sind
> **P3-only** und nicht Teil der v1-DoD.

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
darauf. *Contract:* IC-1. *Test:* Doku-Existenz + Link-Check
(`consistency/docs.py`-Muster).

### AC-5 — Testabdeckung der Kernflächen

**Given** die Testsuite, **when** sie läuft, **then** existieren Tests für Enum,
`mode`×`topology`-Matrix, `main-chat`-Konflikt und abgeleiteten Default.
*Contracts:* IC-1, IC-2, IC-8. *Test:* vier Testmodule aus P1/P2.

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
+ N>1 ist ein harter Validator-ERROR; `--validate` ist grün.
*Contracts:* IC-1, IC-8. *Test:* Schema-Test (beide Richtungen) + Validator-Test.

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
Datei; `viz-report` konsumiert unverändert; das Guard-Audit-Log trägt die ID.
**Given** ein Sentinel mit `id=`, **when** der Guard entscheidet, **then** wird
die ID **nie** für Allow/Deny benutzt (**OQ-2 = A**).
*Contracts:* IC-9, IC-10. *Test:* Event-Fixture + Reader-Test + Hook-Test.

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
Orchestrator-Rolle; **given** ein verwalteter Wert, **when** `primary →
subagent` wechselt, **then** wird er zurückgerollt; **given** ein nutzereigener
Wert, **then** entsteht `default-agent-conflict` (WARN, kein Auto-Delete) und
der ActiveSet-Konjunkt bleibt wirksam.
*Contracts:* IC-7. *Test:* `tests/test_ac01_render_identity.py` +
Isolation-Test.

### AC-15 — Invariante: kein `yes` ohne State

**Given** eine Provider-Zelle mit `topology_support.* == true`, **when** der
Invariantentest läuft, **then** ist `topology_verified_state.* != UNVERIFIED`;
**given** eine `UNVERIFIED`-Zelle, **when** aufgelöst wird, **then** liefert der
Resolver **nie** den deklarierten Wert. Eine `yes`-Zelle existiert nur mit
aufgezeichneter Probe-Evidenz. *Contract:* IC-2. *Test:*
Provider-Invariantentest + Resolver-Test.

### AC-16 — Matrix-Zählung als gemessene Regel

**Given** die Matrix aus §7 des Designs, **when** der Zähl-Test läuft, **then**
gilt: 40 Zellen = **`25 + N` datenabgeleitet** / **`15 − N` `UNVERIFIED ⇒ no`**,
wobei **N aus der Evidenzliste des Spike-Docs gemessen** wird (`0 ≤ N ≤ 15`;
die fünf Probes sind die Evidenzquellen, eine Probe kann mehrere Zellen
stützen) und **0 spekulative `yes`** existieren; jede Degradierung erzeugt genau eine WARNING
pro Provider und Lauf. Der Test pinnt **keine** konkrete Endzahl.
*Contracts:* IC-2, IC-5. *Test:* Matrix-Zähl-Test + Konsistenz-Test.

### AC-17 — Harte Validator-Teilstrings

**Given** eine widersprüchliche Config, **when** `sync` oder `--validate` läuft,
**then** bricht der stdlib-Validator mit rc≠0 ab (ohne `jsonschema`) und die
Meldung enthält den in IC-8 gepinnten Teilstring: **(P1)** Same-Scope
`main-chat` × Topologie (auch Same-Object), `enabled: false` × Topologie;
**(P3-only)** `singleton: false`, `singleton` present × N>1, `primary` × N>1 im
selben Scope. *Contract:* IC-8. *Test:*
`tests/test_orchestrator_topology_validator.py` (P1) + P3-Erweiterung.

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

### P0-Gate — Probe-Abnahme (v1-Bestandteil)

P0 ist abgeschlossen, wenn **jede** der fünf Probes (§16 Nr. 2–6 des Designs)
im Evidenz-Dokument `docs/spikes/2026-11-03-issue-1077-topology-probe.md` ein
**aufgezeichnetes Ergebnis** hat:

- **P0-1 … P0-5:** je Probe entweder (a) **Evidenz** — Befehl, Datum,
  Provider-Version, beobachtetes Ergebnis inkl. Fehlerfall — oder (b) die
  wörtliche Zeile **„not run — CLI unavailable"** mit Grund.
- **Upgrade-Regel:** Eine Matrix-Zelle wechselt nur dann auf `yes`, wenn
  `docs/spikes/…-topology-probe.md` die zugehörige Evidenz enthält **und**
  `topology_verified_state` auf `DOCUMENTED`/`VERIFIED-RUNTIME` steht; ein
  `yes` ohne Evidenzzeile ist ein Testfehler (AC-16).
- **Kein „unverifiziert für immer":** „not run" ist ein gültiges Ergebnis,
  lässt die Zelle aber `no` und erzeugt genau eine WARNING — es ist **kein**
  Grund, die Probe zu wiederholen, bevor eine CLI verfügbar ist.
- **N wird gemessen:** Die Endzahl der Upgrades steht erst nach P0 fest; die
  Spec/AC-16 assertet die Bilanz, nicht eine geratene Zahl.

---

## Risiken (Top 5)

| # | Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| **R1** | **Zweite Skip-Stelle** (`main-chat`-Skip in `agent_sync.py` + neue Topologie-Logik) | Orchestrator verschwindet still oder wird doppelt gepruned | Ein Prädikat `role_emitted_for_provider` (IC-3); P1 landet nur Funktion + Test, P2 stellt beide Call-Sites um; AST-/Grep-Assertion „genau eine Funktion entscheidet". |
| **R2** | **`default_agent` ↔ Gate-Deny-Kopplung + zweiter Schreiber** | Nutzer verliert Builder-Default oder Main-Chat-Schreibblockade | `_opencode_entry_point` bleibt einzige Quelle; `apply_settings_surface_shape` erhält `topology_effective` (IC-7/AC-14); D1a-Invariante unverändert; zusätzlicher WARNING „gate inactive because topology removed the entry point". |
| **R4** | **Byte-Identität bricht** durch unbedingte Textänderung oder `{{else}}` auf eigener Zeile | Jedes Consumer-Projekt meldet Drift nach Upgrade | Conditional-Rendering mit **inline** platzierten Markern und wortgleichem else-Zweig; AC-6 + AC-18; Golden-Fixtures „Rolle inaktiv/aktiv + Key unset". |
| **R8** | **N>1 ohne Zustands-Isolation** (P3) | Stiller Resume-Datenverlust | Harte Kopplung: `max-instances` existiert vor P3 nicht und wird gemeinsam mit `maximum: 8` und der Isolation eingeführt; kein Zwischenschritt mit `maximum: 1`. |
| **R10** | **Matrix-Zellen werden als Freigabe gelesen, obwohl `UNVERIFIED`** / Probe belegt nichts | Spec verspricht `hybrid`/N>1 ohne Evidenz | Upgrade-Prozedur (P0-Gate): `yes` nur mit Evidenzzeile + State-Wechsel + grünem Invariantentest; AC-15/AC-16; unbelegte Zellen bleiben `no` mit genauer einer WARNING. |

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
  Rev. 4 vom 2026-11-04 — §4 (Contracts), §7 (Matrix + Upgrade-Prozedur),
  §9 (Multi-Instanz, P3), §11 (Phasen), §12 (ACs), §15 (entschiedene OQ).
- **Phasen → AC:** P0 → P0-Gate, AC-13…AC-16; P1 → AC-1, AC-2, AC-5, AC-17
  (P1-Zeilen), AC-18; P2 → AC-3, AC-6, AC-7, AC-14; P4 → AC-4; P3 →
  AC-8…AC-12, AC-17 (P3-Zeilen).
- **Governance-Hinweis (A9/R12):** Dieses Dokument trägt die literalen
  Spec-Überschriften (`## Problem`, `## Ziel`, `## Nicht-Ziele`,
  `## Interface Contracts`, `## Datenfluss`, `## Acceptance Criteria`,
  `## Offene Fragen`, `## Trace-Anker`). `consistency/spec_plan.py::_classify`
  ordnet derzeit `*-design.md` als `spec` ein; `*-spec.md` fällt in die
  Plan-Rolle. Die Überschriften sind deshalb bewusst zusätzlich vorhanden —
  verbindlich bleibt die Design-Referenz, nicht der Dateiname.
