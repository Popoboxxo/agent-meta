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

## Positions-Matrix je Surface

> Datenquelle: Design §12.2–§12.6
> ([`2026-11-09-orchestrator-mode-topology-design.md`](../../specs/2026-11-09-orchestrator-mode-topology-design.md)).
> Die Tabellen sind **Daten**, keine Meinung: jede Begründung nennt die tragende
> Code-Stelle, jede Verdict-Zelle beginnt mit genau einem Wort aus dem
> geschlossenen Vokabular.

**Positions-Legende** (Spec §3.8.1):

- **POS-1** — Main-Chat-als-Orchestrator (`mode: main-chat`): die Rolle wird nicht
  emittiert, kein Orchestrator-State, **0 Hop**.
- **POS-2** — Delegierter Orchestrator (`topology: subagent`): der Main Chat spawnt
  die Rolle, **1 Hop**.
- **POS-3** — Session-Einstieg (`topology: primary`): der Nutzer startet in der
  Rolle, **0 Hop** — aber nur, wenn die Session tatsächlich dort startet.

**Urteil-Vokabular:** `RECOMMENDED` (genau eine pro Surface) · `ALLOWED`
(funktioniert, mit benannten Kosten) · `DEGRADED` (deklariert, effektiv aber
`subagent`) · `FORBIDDEN` (Validator-ERROR oder strukturell unausführbar).

**`hybrid` ist keine eigene Zeile:** jede `hybrid`-Zelle ist `UNVERIFIED ⇒
subagent` und erscheint deshalb unter `subagent` (kein Neuaufrollen von #1077).

#### Surface `v1` — OpenCode v1 (`surface-version: v1`, Tier `permission` PARTIAL)

| mode | topology (decl→eff) | Position | Urteil | Gate-Tier | Write-Scope-Lock | Recursion | Hop | A2A / Checkpoint |
|---|---|---|---|---|---|---|---|---|
| `strict` | `primary`→`primary` | POS-3 | ALLOWED (optional, 0 Hop) | `permission` (PARTIAL, `runtime-gate-tiers.md:38`) | aktiv (`provider_transform.py:529-531`) | `subagent_depth` nur bei `inject-subagent-depth` (`provider-capabilities.yaml:211`); Plattform-Limit | 0 | `a2a-v1` + `.meta-viz`-Checkpoints aktiv (`plan-ledger.md:30-32`) |
| `strict` | `subagent`→`subagent` | POS-2 | **RECOMMENDED** (Default, D-OQ1) | Gate suspendiert, `gate-inactive`-WARN (`isolation.py:932-962`) | **nicht** gesetzt | dito, +1 Ebene | 1 | dito |
| `advisory` | `primary`→`primary` | POS-3 | ALLOWED | `permission` | aktiv | dito | 0 | dito |
| `advisory` | `subagent`→`subagent` | POS-2 | ALLOWED (Team-Empfehlung, **setzt #1182 voraus**) | Gate suspendiert | nicht gesetzt | dito | 1 | dito |
| `main-chat` | `primary`→`primary` | POS-1 (keine Rolle) | **FORBIDDEN** (declared) / WARN (derived, D-Q1) | keiner (Rolle fehlt) | entfällt | entfällt | 0 | kein Orchestrator-State |
| `main-chat` | `subagent`→`subagent` | POS-1 | ALLOWED nur **cross-scope** (inert + `main-chat-supersedes`) | keiner | entfällt | entfällt | 0 | kein Orchestrator-State |

#### Surface `v2` — OpenCode v2 (`surface-version: v2`, Tier `plugin` observe + `permissions[]`-Deny)

| mode | topology (decl→eff) | Position | Urteil | Gate-Tier | Write-Scope-Lock | Recursion | Hop | A2A / Checkpoint |
|---|---|---|---|---|---|---|---|---|
| `strict` | `primary`→`primary` | POS-3 | ALLOWED (optional) | `plugin` = **observe**; Deny tragend ist der `permissions[]`-Deny (**nicht** das Plugin) (`runtime-gate-tiers.md:50-53`) | aktiv | `subagent_depth` (Capability `required_depth: 2`, `provider-capabilities.yaml:211`) | 0 | `a2a-v1` + `.meta-viz`-Checkpoints aktiv (`plan-ledger.md:30-32`) |
| `strict` | `subagent`→`subagent` | POS-2 | **RECOMMENDED** (Default, D-OQ1) — **erst nach G7** | Gate suspendiert (`gate-inactive`), **kein Deny**; Session-/Context-Ownership bleibt beim Main Chat | **nicht** gesetzt | dito | 1 | dito |
| `advisory` | `primary`→`primary` | POS-3 | ALLOWED | `plugin` + `permissions[]`-Deny | aktiv | dito | 0 | dito |
| `advisory` | `subagent`→`subagent` | POS-2 | ALLOWED (Team-Empfehlung, **setzt #1182 voraus**) | Gate suspendiert | nicht gesetzt | dito | 1 | dito |
| `main-chat` | `primary`→`primary` | POS-1 (keine Rolle) | **FORBIDDEN** (declared) / WARN (derived, D-Q1) | keiner | entfällt | entfällt | 0 | kein Orchestrator-State |
| `main-chat` | `subagent`→`subagent` | POS-1 | ALLOWED nur cross-scope (inert + WARN) | keiner | entfällt | entfällt | 0 | kein Orchestrator-State |

> **v2-Pin:** Nicht-`primary`-Rollen werden hart auf `mode: subagent` gesetzt
> (`provider_transform.py:498-499`). Genau deshalb ist `subagent` auf v2
> **technisch** sauber — und genau deshalb ist der topology-blinde Reconcile
> (G7) der einzige verbleibende Defekt.

> **Bedingung (`DECIDED 2026-11-09`, D-OQ3):** `advisory × subagent` ist die
> Team-Empfehlung, aber **erst nach dem Fix von #1182** (`context-profile:
> compact` bricht für `advisory` ab). Bis dahin ist `strict × subagent` die
> belastbare Team-Empfehlung; Szenario `103` bleibt `BLOCKED (#1182)`.

#### Surface `Claude` — Tier `hook`, kein `primary-role`

| mode | topology (decl→eff) | Position | Urteil | Gate-Tier | Write-Scope-Lock | Recursion | Hop | A2A / Checkpoint |
|---|---|---|---|---|---|---|---|---|
| `strict` | ungesetzt→`subagent` | POS-2 | **RECOMMENDED** | `hook` (voll, `runtime-gate-tiers.md:36`) | entfällt (kein `mode: primary`-Konzept) | Subagent-Nesting-Limit der Plattform (`a2a-delegation-gates.md:30-32`) | 1 | `a2a-v1`/Checkpoints provider-gestützt (`plan-ledger.md:30-32`) |
| `strict` | `primary`→`primary` | POS-3 | ALLOWED (nur explizit deklariert) | `hook` | Guard-Hook statt Agent-Frontmatter-Deny | dito | 0 | dito |
| `advisory` | `primary`→`primary` | POS-3 | ALLOWED | `hook` | Guard-Hook | dito | 0 | dito |
| `advisory` | `subagent`→`subagent` | POS-2 | ALLOWED (Team-Empfehlung, **setzt #1182 voraus**) | `hook` | entfällt | dito | 1 | dito |
| `main-chat` | `primary`→`primary` | POS-1 (keine Rolle) | **FORBIDDEN** (declared) / WARN (derived, D-Q1) | keiner (Rolle fehlt) | entfällt | entfällt | 0 | kein Orchestrator-State |
| `main-chat` | `subagent`→`subagent` | POS-1 | ALLOWED nur cross-scope (inert + WARN) | keiner | entfällt | entfällt | 0 | kein Orchestrator-State |

> **Caveat `strict × primary` (Rev. 2 / R-02):** „Hop 0" gilt **nur**, wenn die
> Session tatsächlich im `orchestrator` startet. Claude hat kein
> `mode: primary`-Konzept und `main_agent_selectable: true`
> (`provider-capabilities.yaml:144`): eine Main-Chat-Session **darf** den
> Orchestrator spawnen (der legale `hook`-Kanal), kostet dann aber 1 Hop. Die
> Rev.-1-Regel „kein Spawn-Kanal" ist deshalb **falsch** und in G1 ersatzlos
> gestrichen.

#### Surface `Gemini` — Gemini / Antigravity (Tier `hook`, `primary` nicht unterstützt)

| mode | topology (decl→eff) | Position | Urteil | Gate-Tier | Write-Scope-Lock | Recursion | Hop | A2A / Checkpoint |
|---|---|---|---|---|---|---|---|---|
| `strict` | `primary`→**`subagent`** | POS-2 (degradiert) | DEGRADED (+ `orchestrator-topology.degraded`) | `hook` (`runtime-gate-tiers.md:36`) | nicht gesetzt | Roster (`provider-capabilities.yaml:256`) / Plattform-Limit | 1 | `a2a-v1`/Checkpoints provider-gestützt (`plan-ledger.md:30-32`) |
| `strict` | `subagent`→`subagent` | POS-2 | **RECOMMENDED** | `hook` | nicht gesetzt | dito | 1 | dito |
| `advisory` | `primary`→`subagent` | POS-2 (degradiert) | DEGRADED (WARN) | `hook` | nicht gesetzt | dito | 1 | dito |
| `advisory` | `subagent`→`subagent` | POS-2 | ALLOWED (Team-Empfehlung, **setzt #1182 voraus**) | `hook` | nicht gesetzt | dito | 1 | dito |
| `main-chat` | `primary`→`subagent` | POS-1 (keine Rolle) | **FORBIDDEN** (declared) / WARN (derived) | keiner (Rolle fehlt) | entfällt | entfällt | 0 | kein Orchestrator-State |
| `main-chat` | `subagent`→`subagent` | POS-1 | ALLOWED nur cross-scope (inert + WARN) | keiner | entfällt | entfällt | 0 | kein Orchestrator-State |

## Kosten und Empfehlung

**Hop-Definition** (Spec §4, D-Q4): **POS-3 = 0 Hop**, **POS-2 = 1 Hop**,
**POS-1 = 0 Hop**. Ein Hop ist genau ein Spawn des Orchestrators durch den Main
Chat; ein Hop ist Kontext- und Latenz-Kosten, nie ein Governance-Gewinn.

**Schwelle:** **S ≤2 Dateien → direkter Dispatch** (kein Orchestrator-Hop);
M/L/XL laufen über den Orchestrator (`spec-plan-workflow.md:29-32`).

**ESTIMATE:** 4–8k Tokens pro Session-Start für den Orchestrator-Einstieg.
Messmethode: `wc -c <datei> / 4` über die drei Einstiegsdateien (Agent-Prompt,
eingebettete Rules, Projekt-Kontext). Der Wert ist **nicht gemessen**, sondern
geschätzt — er ist keine Messbehauptung.

**Empfehlung (Einzelnutzer):** Default ist **`strict × subagent`** (POS-2,
1 Hop). **`strict × primary`** (POS-3) ist eine **gleichwertige** Option:
gleiche Governance, kein Hop, dafür Session-Start-Bindung — der Sync kann den
Start in der Rolle nicht erzwingen.

**Empfehlung (Team):** `advisory × subagent` — **erst nach #1182**
(`context-profile: compact` bricht für `advisory` ab). Bis dahin gilt auch im
Team `strict × subagent`.

## Evidenz-Index (Matrix)

| Aussage | Quelle |
|---|---|
| Ableitung/`effective`-Invariante | `scripts/lib/topology.py:135-140`, `:72-77` |
| Fallback/Degradierung | `scripts/lib/topology.py:147-183`, `config/provider-capabilities.yaml:263-266` |
| `mode` beeinflusst Position nicht | `scripts/lib/topology.py:196-206` |
| Same-Scope-ERROR, Cross-Scope-WARN | `scripts/lib/config.py:435-463`, `:538-563` |
| v1/v2-Emission + Pin | `scripts/lib/provider_transform.py:488-499` |
| Write-Scope-Lock | `scripts/lib/provider_transform.py:529-531` |
| Tier-Präzedenz und Zusagen | `docs/concepts/runtime-gate-tiers.md:36-55`, `:64-69` |
| v2-Deny-Invariante (D1a) | `scripts/lib/isolation.py:1351-1404`, `:1856-1889` |
| Auto-Commit/Dispatch-Defaults | `scripts/lib/config.py:2003` |
| S/M/L/XL-Schwellen | `rules/1-generic/spec-plan-workflow.md:29-32` |
| Capability-Zellen | `config/provider-capabilities.yaml:148-151`, `:206-209`, `:263-266` |
| Registry-Keys Opencode | `config/ai-providers.yaml:260-274`, `:314-325` |
| Position POS-1: Rolle nicht emittiert | `scripts/lib/active_set.py:206-217` |
| Position POS-1: dangling `default_agent` nur gewarnt | `scripts/lib/isolation.py:910-924` |
| Position POS-2/POS-3: Frontmatter-`mode` | `scripts/lib/provider_transform.py:494-499`, `:1052`, `:1298` |

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
