# Orchestrator-Topologie (`primary | subagent | hybrid`)

> Status: **Aktiv (v1, P0–P2 + P4)** — implementiert am 2026-11-04.
> Spec: [Orchestrator-Topologie (normativ)](../../specs/2026-11-04-orchestrator-topology-spec.md)
> Design: [Design Rev. 4](../../specs/2026-11-03-orchestrator-topology-design.md)
> Rule: [`a2a-delegation-gates.md`](../../../rules/1-generic/a2a-delegation-gates.md)
> Verwandt: [Singleton-Orchestrator-Architektur](singleton-orchestrator-architecture.md)

`orchestrator.topology` macht die **Position** des Orchestrators zu einer
expliziten, validierten Projekt-Entscheidung. Der Key ist optional; bleibt er
ungesetzt, leitet der Builder die heutige Position ab und jedes gerenderte Byte
bleibt identisch (AC-6). Die Topologie ist **orthogonal** zu `mode`
(Gate-Stärke) und zur Multiplizität (P3).

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
(P3), nie die Enum. Ein Identitätsmodell gilt für alle drei Werte.

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

## Multi-Instanz-Vertrag — **P3, designed, not shipped**

> **P3, designed, not shipped.** Der folgende Vertrag ist entworfen und
> akzeptiert, aber **kein v1-Versprechen** — er ist **nicht Teil von v1** und
> wird erst mit P3 implementiert.

- `orchestrator.max-instances` (integer 1..8, Default 1) ist der kanonische
  Multiplizitäts-Key; `orchestrator.singleton` ist ein presence-only Alias
  (`true`), kein Schema-Default.
- Same-Scope-Konflikte sind harte ERRORs: `singleton` present × N>1,
  `primary` × N>1, `singleton: false`. `singleton` present × N=1 ist **kein**
  Fehler, sondern das redundante INFO `orchestrator-topology.singleton-redundant`.
- Die Singleton-Regel wird kardinalitätsfrei: **G1** Worker → Orchestrator =
  HARD REJECT (immer); **G2** nur `main_chat` spawnt Orchestratoren, höchstens
  `max-instances`, mit eindeutiger `orchestrator_id` und disjunktem Scope;
  **G3** Orchestrator → Orchestrator = HARD REJECT.
- Zustands-Namespaces (`<base>__<id>`, `progress-<id>.md`) und das
  Guard-Audit der Instanz-ID sind P3-only.

In v1 existiert keiner dieser Keys. Der v1-Vertrag ist: **genau ein spawnbarer
Orchestrator**, und `max-instances`/`singleton`/`orchestrator_id` werden vom
Validator nicht akzeptiert, weil sie noch nicht existieren.

## Cross-Links

- Normative Spec: [Orchestrator-Topologie](../../specs/2026-11-04-orchestrator-topology-spec.md)
- Design (Rev. 4): [Design](../../specs/2026-11-03-orchestrator-topology-design.md)
- Bedingte Gate-Regel: [`a2a-delegation-gates.md`](../../../rules/1-generic/a2a-delegation-gates.md)
- Singleton-Historie: [Singleton-Orchestrator-Architektur](singleton-orchestrator-architecture.md)
- Capability-Daten: [`config/provider-capabilities.yaml`](../../../config/provider-capabilities.yaml)
