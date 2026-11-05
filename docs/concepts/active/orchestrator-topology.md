# Orchestrator-Topologie (`primary | subagent | hybrid`)

> Status: **Aktiv (v1, P0–P4)** — implementiert am 2026-11-04; P3 (Multi-Instanz) nachgezogen am 2026-11-05.
> Spec: [Orchestrator-Topologie (normativ)](../../specs/2026-11-04-orchestrator-topology-spec.md)
> Design: [Design Rev. 4](../../specs/2026-11-03-orchestrator-topology-design.md)
> Rule: [`a2a-delegation-gates.md`](../../../rules/1-generic/a2a-delegation-gates.md)
> Verwandt: [Singleton-Orchestrator-Architektur](singleton-orchestrator-architecture.md)

`orchestrator.topology` macht die **Position** des Orchestrators zu einer
expliziten, validierten Projekt-Entscheidung. Der Key ist optional; bleibt er
ungesetzt, leitet der Builder die heutige Position ab und jedes gerenderte Byte
bleibt identisch (AC-6). Die Topologie ist **orthogonal** zu `mode`
(Gate-Stärke) und zur Multiplizität (`max-instances`, siehe unten).

## Die drei Topologien

| Wert | Bedeutung | Wer spawnt den Orchestrator? |
|---|---|---|
| `primary` | Die Rolle ist der **Session-Einstieg**. Genau ein Orchestrator, kein Spawn-Kanal. | niemand — der Nutzer startet direkt in der Rolle |
| `subagent` | Die Rolle ist **nie** Einstieg. Der Main Chat spawnt den Orchestrator. | ausschließlich `main_chat` |
| `hybrid` | **Positions-agnostisch**: die Rolle darf Einstieg *oder* gespawnt sein — aber nie beides gleichzeitig. | `main_chat`, wenn nicht als Einstieg gestartet |

**Deviation (D2):** `hybrid` ist **entweder/oder** — eine positions-agnostische
Rolle, **nicht zwei gleichzeitige Positionen**. Das Issue #1077 §2 las `hybrid`
ursprünglich als „primary **und** zusätzlich spawnbar"; diese Lesart ist
verworfen. Die Anzahl der Instanzen regelt ausschließlich `max-instances`
(siehe Multi-Instanz-Vertrag), nie die Enum. Ein Identitätsmodell gilt
für alle drei Werte.

**`hybrid` ist in v1 nirgends gewährt:** Für jeden Provider ist
`topology_support.hybrid == false` und `topology_verified_state.hybrid ==
UNVERIFIED`. Eine Deklaration `hybrid` wird akzeptiert, aber **laut** auf
`subagent` degradiert (eine WARNING `orchestrator-topology.hybrid-unverified`,
plus `orchestrator-topology.degraded`, solange deklariert ≠ effektiv).

## Provider-Unterstützung und Degradierung

Die Matrix wird **ausschließlich** aus vorhandenen Capability-Keys abgeleitet
(`main_agent_selectable`, `subagent_dispatch`, `parallel_execution`) und liegt
in [`config/provider-capabilities.yaml`](../../../config/provider-capabilities.yaml).
Zellen ohne Datenbasis sind **`UNVERIFIED ⇒ no`** — eine Zelle behauptet nie
eine Fähigkeit ohne aufgezeichnete Evidenz.

| Provider | `primary` | `subagent` | `hybrid` | N>1 |
|---|---|---|---|---|
| Claude | **yes** | **yes** | **no → subagent** | **yes** |
| Opencode | **yes** | **yes** | **no → subagent** | **yes** |
| Gemini / Antigravity | **no → subagent** | **yes** | **no → subagent** | **yes** |
| Continue | **yes** | **degraded → sequential-text** | **no → subagent** | **no** |
| Copilot | **no → subagent** | **yes** | **no → subagent** | **no** |
| Mammouth | **no → subagent** | **yes** | **no → subagent** | **no** |
| Codex | **no → subagent** | **yes** | **no → subagent** | **yes** |
| ZCode | **no → subagent** | **yes** | **no → subagent** | **no** |
| KimiCode | **yes** | **yes** | **no → subagent** | **yes** |
| *(custom / nicht registriert)* | **no** | **no** | **no → subagent** | **no** |

**Zählung:** 40 Zellen = **25 datenabgeleitet** / **15 `UNVERIFIED ⇒ no`**. Jedes
spätere Zell-Upgrade braucht alle drei P0-Gate-Bedingungen (Evidenz-Zeile,
State-Wechsel, Invariantentest); die Endzahl `N` wird gemessen, nie gepinnt.

**Degradierung ist laut, nie still:** Fällt `support == false` **oder** ist die
Zelle `UNVERIFIED`, entstammt `effective` ausschließlich `topology_degrade`
bzw. dem **Fail-safe `subagent`**. Jede tatsächliche Degradierung (deklariert ≠
effektiv) erzeugt genau eine WARNING `orchestrator-topology.degraded` pro
Provider und Lauf. Eine unveränderte `no`-Zelle ohne Deklaration warnt nicht.
Ein Mechanismus-Wort (`sequential-text`) wandert nach `degradation_reason` und
wird nie als Topologie-Wert durchgereicht.

## `mode` × `topology` — Interaktionsmatrix

Die Achsen sind orthogonal: `topology` ändert nie die Gate-Stärke, `mode`
ändert nie die Position. Genau **eine** Dominanzzelle existiert — `main-chat`
entfernt die Rolle, damit ist jede Topologie gegenstandslos.

| `mode` \ `topology` | `primary` | `subagent` | `hybrid` |
|---|---|---|---|
| `strict` | Einstieg, strikte Gates, 1 Instanz | Main Chat spawnt, strikte Gates | positions-agnostisch, strikte Gates¹ |
| `advisory` | Einstieg, advisory Gates | Main Chat spawnt, advisory Gates | positions-agnostisch, advisory Gates¹ |
| `main-chat` | **ERROR** (gleicher Scope) / **inert + WARNING** (Cross-Scope) | **ERROR** (gleicher Scope) / **inert + WARNING** (Cross-Scope) | **ERROR** (gleicher Scope) / **inert + WARNING** (Cross-Scope) |

¹ Die `hybrid`-Spalte beschreibt die *deklarierte* Semantik, **nicht** das
v1-Verhalten: weil `topology_verified_state.hybrid == UNVERIFIED` ist,
degradiert jede `hybrid`-Zelle in v1 auf `subagent` (Fail-safe).

`mode: main-chat` im selben Scope wie eine Topologie (auch im selben Objekt)
ist ein **harter Validator-ERROR** (rc ≠ 0). Cross-Scope (Provider-Override
`mode: main-chat` bei global gesetzter Topologie) ist eine WARNING
`orchestrator-topology.main-chat-supersedes`; die Topologie ist dann **inert**,
nicht still übersteuert.

## Multi-Instanz-Vertrag — **P3, shipped**

> **P3, shipped.** Der Vertrag ist implementiert und validiert und damit Teil
> des ausgelieferten Vertrags — nicht mehr nur entworfen. Der Default bleibt
> N=1: **N=1 ist byte-identisch** zu vorher (keine Rollen-, Dateinamen-,
> Session-ID- oder Render-Änderung ohne gesetzten Key).

- `orchestrator.max-instances` (integer **1..8**, Default **1**) ist der
  kanonische Multiplizitäts-Key; `orchestrator.singleton` ist ein
  **presence-only** Alias (`enum: [true]`, **kein** Schema-Default) für genau
  eine Instanz. `singleton: false` ist ein harter ERROR mit Hinweis auf
  `max-instances`.
- Same-Scope-Konflikte sind harte ERRORs: `singleton` present × N>1,
  `primary` × N>1, `singleton: false`. `singleton` present × N=1 ist **kein**
  Fehler, sondern das redundante INFO `orchestrator-topology.singleton-redundant`.
  Ein Cross-Scope-`primary` bei globalem N>1 ist ebenfalls kein Fehler, sondern
  die WARNING `orchestrator-topology.instances-clamped` mit effektivem N=1.
- **Identitätsmodell:** `orchestrator#<scope-id>`. Der Main Chat leitet die
  `orchestrator_id` deterministisch aus dem Scope-Schlüssel ab (Plan-/Task-Ref,
  Branch, PR-Nummer) und normalisiert sie auf
  `[a-z0-9][a-z0-9._-]{0,39}` (1..40 Zeichen, kein `..`). Das Dispatch-Ziel
  bleibt der reine Rollenname `orchestrator`; die Identität reist **nur** in
  den Envelope-Feldern `orchestrator_id`/`scope_id` (bzw. `metadata.scope_id`),
  nie als `#`-Suffix in Dateinamen oder `subagent_type`.
- **Singleton-Regel, kardinalitätsfrei:** **G1** Worker → Orchestrator =
  HARD REJECT (immer); **G2** nur `main_chat` spawnt Orchestratoren, höchstens
  `max-instances`, mit eindeutiger `orchestrator_id` und disjunktem Scope;
  **G3** Orchestrator → Orchestrator = HARD REJECT. Fehlende oder doppelte ID
  bzw. Scope-Überlappung ist ein HARD ERROR **beim Spawn**; es gibt kein
  Runtime-Registry (dieselbe akzeptierte Prompt-Grenze wie
  `validate_envelope`).
- **Zustands-Namespaces:** Der Checkpoint einer Instanz liegt als
  `<checkpoint-dir>/<base>__<id>.json`; `current.md` bleibt der einzige
  maschinell gelesene Fortschritt und gehört der Wurzel-Session, jede Instanz
  schreibt zusätzlich das rein menschlich lesbare `progress-<id>.md`. Das
  gemeinsame `.meta-viz/events.jsonl` trägt die Audit-Felder
  **`orchestrator_id`, `scope_id`, `spawned_by`, `spawned_at`** — keine
  Datei-Shards.
- **Audit-Felder:** Der vollständige Datensatz
  `{orchestrator_id, scope_id, spawned_by, spawned_at}` steht im Viz-Event;
  das Guard-Audit-Log reduziert ihn auf `orchestrator_id=<id|unset>`. Die
  Guard-ID ist **audit-only**: sie wird geloggt und **nie** in einer
  Allow/Deny-Entscheidung gelesen (kein Runtime-Enforcement von N oder
  Scopes, OQ-2 = A).

Ohne gesetzte Keys gilt der v1-Vertrag weiter: **genau ein spawnbarer
Orchestrator**; `max-instances: 1` und das Fehlen von `singleton` sind der
Default. Rollennamen, Dateinamen und Session-IDs bleiben bei N=1
byte-identisch zu vorher.

## Cross-Links

- Normative Spec: [Orchestrator-Topologie](../../specs/2026-11-04-orchestrator-topology-spec.md)
- Design (Rev. 4): [Design](../../specs/2026-11-03-orchestrator-topology-design.md)
- Bedingte Gate-Regel: [`a2a-delegation-gates.md`](../../../rules/1-generic/a2a-delegation-gates.md)
- Singleton-Historie: [Singleton-Orchestrator-Architektur](singleton-orchestrator-architecture.md)
- Capability-Daten: [`config/provider-capabilities.yaml`](../../../config/provider-capabilities.yaml)
