---
status: APPROVED
approved: 2026-11-09
---

# Orchestrator `mode` × `topology` — Entscheidungs- und Design-Spec

> Status: **APPROVED** — Approved: 2026-11-09 (User-Freigabe via main_chat)
> Revision: 4
> Datum: 2026-11-09
> Rev. 4 (2026-11-09): **drei User-Entscheidungen eingearbeitet** — `DECIDED 2026-11-09`:
> D-OQ1 (Default dieses Repos = `strict × subagent`, beide Opencode-Positionen first-class),
> D-OQ2 (`strict × subagent` bleibt erlaubt und empfohlen, Gate-Tier je Surface), D-OQ3
> (`advisory × subagent` erst nach #1182). Neu: §3.8 Positionsmodell mit Mapping
> `mode × topology → Position`, AC-32…AC-37, angepasste D-Q1/D-Q3/D-Q4, Matrix mit
> Positions-Spalte. Nichts davon hebt D-Q1…D-Q5 auf. Die Spec ist seit **2026-11-09** freigegeben
> (`Status: APPROVED`, User-Freigabe via main_chat); die frühere Formulierung „die Freigabe steht
> weiter aus" ist damit überholt.
> Rev. 3.1 (2026-11-09): Pflicht-Überschriften validatorkonform benannt (`## Problem`, `## Ziel`,
> `## Interface Contracts`, `## Datenfluss`, `## Acceptance Criteria`, `## Offene Fragen`,
> `## Trace-Anker`); Inhalte nur verdichtet bzw. umbenannt, keine Entscheidung geändert.
> Review: `docs/reviews/2026-11-09-orchestrator-mode-topology-review.md` (Review 1, vor Revision 2) —
> alle Befunde RVW-1190-01…-20, B1–B3 und W1–W6 sind eingearbeitet.
> Re-Review: `docs/reviews/2026-11-09-orchestrator-mode-topology-rereview.md` (Re-Review 1, vor
> Revision 3) — alle Befunde RVW2-1190-01…-13 sind in dieser Revision eingearbeitet, Nachweis in §14.
> spec-id: SPEC-orchestrator-mode-topology-2026-11-09
> Issue: #1190 (`design(orchestrator): which mode×topology combination for OpenCode v1/v2?`)
> Vorläufer (nicht neu aufgerollt): `docs/specs/2026-11-04-orchestrator-topology-spec.md`
> (`SPEC-orchestrator-topology-2026-11-03`, D1–D10, AC-1…AC-20 — **bleibt normativ**)
> Design-Input: `docs/specs/2026-11-03-orchestrator-topology-design.md` (Rev. 4)
> Klasse: **XL / Architectural**
> Begründung der Klasse: Die Entscheidung berührt öffentliche Config-Contracts
> (`orchestrator.mode`, `orchestrator.topology`, gerenderte Bedingungen) und mehr als eine
> Subsystemgrenze (Resolver, Emission, Rendering, Consistency, Doku). Nach
> `rules/1-generic/spec-plan-workflow.md:32` ist das `XL → Architectural` mit
> vorgelagertem Systemdesign.
> Verifikations-Legende: **VERIFIED** = in dieser Runde im Repo gelesen (`datei:zeile`);
> **ISSUE** = aus dem Issue-Body #1190 übernommen, nicht neu gelesen;
> **ESTIMATE** = Schätzung mit genannter Messmethode, nicht gemessen.

---

## Problem (§1)

**Motivation.** Eine Regel, die in einer realen Session-Form nicht befolgt werden *kann*, wird als
Regel ausgegeben — das trainiert Regel-Ignorieren. Die drei folgenden Abschnitte belegen den Fall,
sein Auftreten in diesem Repo und seine Kosten.

### 1.1 Der unausführbare Gate-Fall

Die gerenderte Master-Rule sagt im Strict-Modus:

> „MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`. Keine Ausnahmen."
> (`rules/1-generic/use-orchestrator.md:4`)

Gleichzeitig ist in diesem Repo (Provider **OpenCode**) der Orchestrator **Session-Einstieg**
(`.opencode/agents/orchestrator.md:8` `mode: primary`), und ein Einstiegs-Agent ist dort **nicht per
`task()` spawnbar** (Provider-Zelle `topology_support.hybrid: false` mit Begründung „`mode: primary`
ist nicht per `task` spawnbar", `docs/specs/2026-11-04-orchestrator-topology-spec.md:600`). Eine
Session, die im Main Chat läuft, hat damit **in OpenCode keinen legalen Kanal**: sie darf nicht
selbst arbeiten (Gate) und kann den einzigen erlaubten Agenten nicht starten. Der Fehler kommt als
opake Provider-Meldung (Zitat `Agent orchestrator cannot run as a subagent` — **ISSUE**: aus dem
Issue-Body #1190 übernommen, im Repo nicht belegt), nicht als Konfigurations- oder Hinweis-Fehler.

Die Aussage ist **positions- und capability-gebunden**, nicht provider-agnostisch: auf Claude ist
`topology_support.primary: true` und `main_agent_selectable: true`
(`config/provider-capabilities.yaml:144`, `:148`), dort **kann** der Main Chat spawnen, und der
`hook`-Tier erzwingt die Delegation — siehe §12.4. „Kein Spawn-Kanal" gilt nur dort, wo die
`primary`-Rolle mit `mode: primary` emittiert wird (OpenCode) und deshalb selbst nicht spawnbar ist.

### 1.2 Warum der Fall real auftritt — und zwar in diesem Repo

- `orchestrator.mode: strict` und `enabled: true`, **kein** `topology`-Key:
  `.meta-config/project.yaml:308-323` (VERIFIED).
- Der Resolver **leitet** daraus `primary` ab, weil `config/ai-providers.yaml:268`
  `primary-role: orchestrator` deklariert und die Rolle im ActiveSet liegt
  (`scripts/lib/topology.py:135-140`, VERIFIED).
- `opencode.json:37` `"default_agent": "orchestrator"` (VERIFIED; das Issue nennt `:47` für
  `d12d4218`, HEAD ist `aaed14c2`) — die Installation bootet also regelhaft in den Orchestrator.
- Genau deshalb ist der **Main Chat hier der Ausnahmefall**: jede Review-, Handoff- oder
  Recovery-Session, die im Main Chat startet, läuft in den unausführbaren Fall.
- Weil `ORCH_TOPOLOGY_*` in `rules/1-generic/use-orchestrator.md:1-24` **überhaupt nicht**
  vorkommt, wird der Gate-Text von der Topologie nicht informiert — er ist in beiden Fällen
  wörtlich identisch.

### 1.3 Kosten des Status quo

1. **Strukturell**: eine Regel, die in einer realen Session-Form nicht befolgt werden *kann*,
   wird als Regel ausgegeben. Das ist stärker als „unschön": es trainiert Regel-Ignorieren.
2. **Diagnostisch**: kein Validator, kein Check, keine Warnung nennt den Zustand
   (`scripts/lib/config.py:538-563` prüft nur *deklarierte* Topologie; VERIFIED).
3. **Semantisch**: `mode` und `topology` werden an mehreren Stellen unterschiedlich behandelt
   (Emission nutzt `effective`, Rendering `declared`) — dieselbe Config erzeugt widersprüchliche
   Artefakte (§3, Lücke 2).
4. **Dokumentarisch**: elf Doku-Stellen widersprechen der Topologie-Semantik oder einander
   (§9.1); die häufigste Form ist die absolute Behauptung „nur `main_chat` spawnt".

---

## Ziel (§2)

Diese Spec **entscheidet** Q1–Q5 aus #1190 und leitet daraus das Soll-Verhalten für neun
verifizierte Lücken ab (G1–G9). Sie liefert **keinen** Implementierungscode und **keine**
Config-Änderung; sie ist der Spec-Input für einen Folgeplan.

Sie rollt **nicht** neu auf: das `topology`-Enum, die `hybrid`-Degradierung, die Multi-Instanz-Achse
(#1077 / D1–D10) und die V2-Surface-Matrix (#1007).

**Rev. 4 (`DECIDED 2026-11-09`):** Die Spec entscheidet zusätzlich das **Positionsmodell** (§3.8) —
drei Session-Formen (`POS-1` Main-Chat-als-Orchestrator, `POS-2` Delegierter Orchestrator, `POS-3`
Session-Einstieg), Default dieses Repos `strict × subagent` **explizit deklariert**, beide
Opencode-Positionen first-class, und `advisory × subagent` erst nach #1182. Die Deklaration selbst
ist **kein** Teil dieser Spec, sondern Plan-Task T20.

---

## 3. Ist-Zustand (mit Belegen)

### 3.1 Config und Ableitung

| Fakt | Beleg |
|---|---|
| `enabled: true`, `strict: true`, `direct-dispatch-enabled: true`, `mode: strict`, `handoff.protocol: a2a-v1`, `checkpointing: true`, **kein `topology`** | `.meta-config/project.yaml:308-323` (VERIFIED) |
| `provider-overrides` fehlen in diesem Repo | `.meta-config/project.yaml:308-323` (VERIFIED) |
| Ableitung: `primary` nur bei deklariertem `primary-role` **und** Rolle im ActiveSet, sonst `subagent`; `hybrid` nie abgeleitet | `scripts/lib/topology.py:135-140` (VERIFIED) |
| Fallback bei `support == false` oder Zelle `UNVERIFIED` → `topology_degrade` bzw. Fail-safe `subagent` | `scripts/lib/topology.py:147-183` (VERIFIED) |
| `effektiv ∈ VALID_TOPOLOGIES` als Invariante | `scripts/lib/topology.py:72-77` (VERIFIED) |
| `mode` wird an den Resolver **übergeben, aber nicht benutzt** („the mode does not change the position resolution in v1") | `scripts/lib/topology.py:196-206` (VERIFIED) |
| Opencode: `primary-role: orchestrator`, `has_hooks: false` | `config/ai-providers.yaml:268`, `:274` (VERIFIED) |
| Opencode-Zellen: `topology_support {primary: true, subagent: true, hybrid: false}`, `topology_verified_state {primary: DOCUMENTED, subagent: DOCUMENTED, hybrid: UNVERIFIED}` | `config/provider-capabilities.yaml:206-209` (VERIFIED) |
| Claude: **kein** `primary-role` → Ableitung ist immer `subagent`; `topology_support.primary: true` | `config/ai-providers.yaml:2-26` + `config/provider-capabilities.yaml:148-151` (VERIFIED) |
| Gemini: `topology_support.primary: false`, `topology_degrade.primary: subagent` | `config/provider-capabilities.yaml:263-266` (VERIFIED) |
| `direct-dispatch-enabled` default `true` | `scripts/lib/config.py:2003` (VERIFIED) |

### 3.2 Emission vs. Rendering

| Fakt | Beleg |
|---|---|
| Emission nutzt `effective`: `mode: primary` nur bei `topology.effective == 'primary'` **und** Rolle == `primary-role`; sonst auf v2 `mode: subagent` | `scripts/lib/provider_transform.py:488-499` (VERIFIED) |
| Write-Scope-Lock hängt an `mode == 'primary'` | `scripts/lib/provider_transform.py:529-531` (VERIFIED) |
| Rendering (Context) nutzt den **deklarierten** Wert: `_topology_flags(resolution.declared or "", …)` | `scripts/lib/context.py:2575-2586` (VERIFIED) |
| Rendering (Rules) nutzt ebenfalls **declared** | `scripts/lib/rules.py:281-293` (VERIFIED) |
| Agent-Templates bekommen **nur** `ORCH_MODE_*` provider-skopiert überschrieben | `scripts/lib/sync_pipeline.py:1405-1424` (VERIFIED) |
| `agent_sync._build_provider_vars` rechnet Topologie **nicht** provider-spezifisch neu (Rules/Context schon) | `scripts/lib/agent_sync.py:510-554` vs. `rules.py:281-293` (VERIFIED) |
| Folge: unter abgeleitetem `primary` gilt `ORCH_TOPOLOGY_EXPLICIT == "false"` → `agents/1-generic/orchestrator.md:19` rendert den else-Zweig „Only `main_chat` may create you" | `agents/1-generic/orchestrator.md:19` (VERIFIED) |
| Folge: `rules/1-generic/a2a-delegation-gates.md:17-19` rendert denselben else-Zweig („NUR `main_chat` darf den `orchestrator` spawnen") | `rules/1-generic/a2a-delegation-gates.md:6-19` (VERIFIED) |
| Flags: `ORCH_TOPOLOGY`, `_EXPLICIT`, `_PRIMARY`, `_SUBAGENT`, `_HYBRID`, `_SOURCE` — **kein** `effective`-Flag | `scripts/lib/variables.py:330-356` (VERIFIED) |

### 3.3 Statische Texte, die die Position behaupten

| Fakt | Beleg |
|---|---|
| Singleton-Block behauptet hart „der vom `main_chat` gespawnte" und „NIEMALS `task(subagent_type="orchestrator")`" — ohne Topologie | `scripts/lib/agent_sync.py:974-986` (VERIFIED) |
| Einstiegshinweis rendert „Starte mit dem `orchestrator`-Agenten" unabhängig von der Topologie | `scripts/lib/agents.py:171-179` (VERIFIED) |
| Gate-Text kennt nur `ORCH_MODE_*` + `GATE_*`; `ORCH_TOPOLOGY_*` kommt in der Datei nicht vor | `rules/1-generic/use-orchestrator.md:1-24` (VERIFIED) |
| Gerenderte Fassung in diesem Repo: unqualifiziertes „Keine Ausnahmen" | `AGENTS.md:140-141` (VERIFIED) |
| Gerenderte Claude-Fassung: Zeile 1 `# CRITICAL GATE` **ohne** Tier-Suffix, Zeile 2 der unqualifizierte Satz „… Keine Ausnahmen.", Zeilen 3-4 der PARTIAL-Absatz — zwei Gate-Varianten im **selben** Render | `.claude/rules/use-orchestrator.md:1-4` (VERIFIED) |

### 3.4 Validierung und Consistency

| Fakt | Beleg |
|---|---|
| Harte Fehler nur bei **deklarierter** Topologie × `main-chat` (same scope) | `scripts/lib/config.py:538-563` (VERIFIED) |
| Normative 3×3-Matrix als Daten, `main-chat` = `error`/`inert` | `scripts/lib/config.py:435-463` (VERIFIED) |
| `_user_owned_default_agent` gibt bei `effective == "primary"` **sofort `None`** zurück → der einzige Check, der „Entry Point zeigt auf nicht spawbbare Rolle" melden könnte, ist genau im Problemfall abgeschaltet | `scripts/lib/consistency/topology.py:118-128`, Aufruf `:384-386` (VERIFIED) |
| `gate-inactive` / `default-agent-conflict` nur bei `effective != "primary"` | `scripts/lib/consistency/topology.py:365-399` (VERIFIED) |
| **Kein** Finding für „`main-chat` + abgeleitetes `primary`" | `scripts/lib/consistency/topology.py:1-40` (Check-Liste) (VERIFIED) |
| `direct-dispatch-enabled` **wirkt** unter `strict`: der Key gated die Sektion „Task decomposition & delegation" des Orchestrator-Agenten; `DIRECT_DISPATCH_SECTION` wird modusunabhängig gebaut | `agents/1-generic/orchestrator.md:203-205`, `scripts/lib/config.py:2090-2101` (VERIFIED) |
| Wirkungslos ist der Key nur unter `mode: main-chat`: die Rolle wird nicht emittiert und der `advisory`-Zweig der Regel entfällt | `scripts/lib/provider_transform.py:488-499`, `rules/1-generic/use-orchestrator.md:25-31`, `scripts/lib/config.py:2003` (VERIFIED) |
| **Kein** Finding für wirkungsloses `direct-dispatch-enabled` unter `mode: main-chat` | `scripts/lib/consistency/orchestrator_strict.py:36-39` (bestehende Check-Liste) (VERIFIED) |

### 3.5 v2-Reconcile

| Fakt | Beleg |
|---|---|
| Spec-A-Pfad übergibt `topology=` korrekt — innerhalb von `_sync_opencode_runtime_gate` (def `:725`) | `scripts/lib/isolation.py:846-856`, `:866-872` (VERIFIED) |
| Die Defektstellen liegen **nicht** dort, sondern in `reconcile_opencode_surface_gate` (def `:1751`), das **kein** `TopologyResolution` besitzt, und in `_opencode_v2_gate_permissions` (def `:1408`), das aus dem Reconcile aufgerufen wird | `scripts/lib/isolation.py:1457`, `:1826-1830`, `:1840-1843` (VERIFIED) |
| Aufrufer von `reconcile_opencode_surface_gate`: Produktions-Stage und `--test-generated`-Pfad; beide übergeben heute nur `active_set` | `scripts/lib/sync_pipeline.py:1598-1602`, `scripts/lib/cli_commands.py:344-348` (VERIFIED) |
| Folge: unter `topology: subagent` + `strict` liefert der topology-blinde Aufruf `orchestrator`, der D1a-Guard hält den Entry Point für gültig und die Tripel für schreibbar; erst `_v2_entry_point_will_be_valid` (`document` ohne `default_agent`, `merge_writes == false` auf Tier `plugin`) kippt sie | `scripts/lib/isolation.py:1351-1375`, `:1856-1875` (VERIFIED) |
| Der dabei gerenderte Remediation-Text verlangt „Set `default_agent` to 'orchestrator'" — also genau die Rücknahme der Topologie-Entscheidung | `scripts/lib/isolation.py:1396-1404` (VERIFIED) |
| Zeile-6-Warnung behauptet „no explicit and generated primary-role", obwohl die Rolle explizit und generiert ist | `scripts/lib/isolation.py:1881-1889` (VERIFIED) |

### 3.6 Gate-Tiers

| Fakt | Beleg |
|---|---|
| Tier-Präzedenz `hook` → `plugin` → `permission` → `advisory` | `docs/concepts/runtime-gate-tiers.md:64-69` (VERIFIED) |
| v1 = `permission` (PARTIAL, keine Delegations-Provenienz) | `docs/concepts/runtime-gate-tiers.md:38`, `:48-55` (VERIFIED) |
| v2 = `plugin`, Artefakt ausschließlich `observe`; tragende Schicht ist der `permissions[]`-Deny | `docs/concepts/runtime-gate-tiers.md:37`, `:50-53`, `:155-167` (VERIFIED) |
| v2-Aktivierung rein datengetrieben | `config/ai-providers.yaml:314-325` (VERIFIED) |

### 3.7 Tests

| Fakt | Beleg |
|---|---|
| Emission nur für Opencode getestet | `tests/test_provider_transform_topology.py:59-184` (VERIFIED) |
| Entry-Point/Gate-Kopplung ist getestet — aber nur im **v1-Mapping-Pfad**: `PC` trägt keine `surface-version`, geprüft wird `permission.edit.**` | `tests/test_orchestrator_topology_entrypoint.py:38`, `:62-69`, `:133` (VERIFIED) |
| Kein Test für den **v2-`permissions[]`-Pfad** unter `subagent` (genau der Pfad aus G7) | `tests/test_orchestrator_topology_entrypoint.py:44-50` (`_init_pc` ist v2, wird aber von `_run_gate` nicht benutzt) (VERIFIED) |
| Kein Test für abgeleitetes `primary` vs. `ORCH_TOPOLOGY_*` (`ORCH_TOPOLOGY_EXPLICIT == "false"` bei `effective == "primary"`) | `tests/test_orchestrator_topology_flags.py:42-80` prüft nur `_topology_flags` direkt (VERIFIED) |
| Kein Test für `use-orchestrator`-Rendering unter `primary`/`subagent` | keine Treffer in der Testsuite für `use-orchestrator` + Topologie (VERIFIED) |
| Kein Test für den Singleton-Block | `scripts/lib/agent_sync.py:974-986` ohne Test-Referenz (VERIFIED) |
| Kein Test für `ROLE_ORCHESTRATOR_ACTIVE` unter `main-chat` | `tests/test_orchestrator_active_set_prose.py` deckt den Fall nicht (VERIFIED) |
| 19 Dateien matchen `tests/*topology*.py` — davon 5 für `context_file.topology` (Dateilayout, **andere** Achse) | `tests/*topology*.py` per Glob (VERIFIED) |

---

## Positionsmodell (§3.8)

**`DECIDED 2026-11-09` (D-OQ1).** Eine **Position** ist die tatsächliche Session-Form, in der die
Orchestrator-Rolle arbeitet. `mode` und `topology` sind die Config-Achsen, aus denen sie folgt — sie
sind **nicht** dasselbe wie die Position: die Session-Form ist zur Sync-Zeit nicht entscheidbar
(D-Q2). Dieses Repo fährt künftig **POS-2** und **deklariert** sie explizit
(`orchestrator.topology: subagent`, Umsetzung als Plan-Task T20, **nach** dem Code-Fix).

### 3.8.1 Die drei Positionen

| ID | Position | Wer startet | Wer spawnt | Rolle emittiert? | `default_agent` | Gate-Tier / Wirkung | A2A / Checkpointing | Hops |
|---|---|---|---|---|---|---|---|---|
| **POS-1** | **Main-Chat-als-Orchestrator** (`mode: main-chat`) | Nutzer im Main Chat | niemand — kein Subagent, kein zusätzlicher Hop | **nein**; `role_emitted_for_provider` liefert `False` (`scripts/lib/active_set.py:206-217`) | **keiner**: der Sync schreibt keinen; ein nutzereigener Wert bleibt und wird gewarnt (`scripts/lib/isolation.py:910-924`) | **kein Runtime-Gate**: die Rolle existiert nicht, die Gate-Regel ist inert (D-Q5) | kein Orchestrator-State; Checkpoints im Main-Chat-Scope | **0** |
| **POS-2** | **Delegierter Orchestrator** (`topology: subagent` mit `mode: strict` oder `advisory`) | Main Chat | Main Chat spawnt den Orchestrator als Subagent | **ja**, Frontmatter `mode: subagent` (`scripts/lib/provider_transform.py:1052`, `:1298`) | **keiner** — bewusst, damit kein Entry-Point auf eine nicht startbare Rolle zeigt | so stark wie das Tier: `hook` = erzwungen (Claude), `plugin` = `observe` + `permissions[]`-Deny, `permission` = PARTIAL, ohne Hooks = Prompt-Konvention; wo der Deny bewusst nicht geschrieben wird, ist `orchestrator-topology.gate-inactive` Pflicht (§6.4) | voll (`a2a-v1` + Checkpoints) | **1** |
| **POS-3** | **Session-Einstieg** (`topology: primary`) | Nutzer startet im Orchestrator | niemand — er **ist** der Einstieg | **ja**, Frontmatter `mode: primary` (`scripts/lib/provider_transform.py:496-497`) | `orchestrator` (Managed-Merge mit Rollback, #1006) | Tier wie POS-2, zusätzlich Write-Scope-Lock (`scripts/lib/provider_transform.py:529-531`) und Deny an den Einstieg gekoppelt (`scripts/lib/isolation.py:926-932`) | voll | **0** (nur wenn die Session tatsächlich dort startet) |

POS-3 ist die **dritte, optionale** Position: nicht jeder Provider unterstützt sie (Gemini degradiert,
`config/provider-capabilities.yaml:263-266`), und sie verlangt eine Nutzerentscheidung beim
Session-Start, die der Sync nicht erzwingen kann (D-Q2). POS-1 und POS-2 sind auf OpenCode **beide**
first-class (D-OQ2); keine von beiden wird abgewertet.

### 3.8.2 Mapping `mode` × `topology` → Position

`topology` ist je Zeile entweder **ungesetzt** (Ableitung durch `resolve_topology`) oder
**deklariert**. Die Ableitung liefert `primary` nur, wenn `providers.<P>.primary-role` die Rolle nennt
**und** sie im ActiveSet liegt (`scripts/lib/topology.py:135-140`), sonst `subagent`.

| `mode` | `topology` | aufgelöste Position (`effective`) | Positions-ID | Rolle emittiert? | `default_agent` | Gate-Tier / Wirkung | A2A / Checkpointing | Hops |
|---|---|---|---|---|---|---|---|---|
| `strict` | ungesetzt, `primary-role` im ActiveSet | `primary` | POS-3 | ja, `mode: primary` | `orchestrator` | Tier erzwingt (`hook`/`plugin`-Deny) bzw. PARTIAL (`permission`) | voll | 0 |
| `strict` | ungesetzt, keine `primary-role` im ActiveSet | `subagent` | POS-2 | ja, `mode: subagent` | keiner | `gate-inactive` (ehrlich), prompt-basiert | voll | 1 |
| `strict` | `primary` | `primary` | POS-3 | ja, `mode: primary` | `orchestrator` | Tier + Write-Scope-Lock + Deny | voll | 0 |
| `strict` | `subagent` | `subagent` | POS-2 | ja, `mode: subagent` | keiner | `gate-inactive`, prompt-basiert (D-Q2-Tabelle) | voll | 1 |
| `advisory` | ungesetzt | abgeleitet (`primary` oder `subagent`) | POS-3 bzw. POS-2 | ja | abhängig von der Ableitung | Tier + Advisory-Zusage | voll | 0 bzw. 1 |
| `advisory` | `primary` | `primary` | POS-3 | ja, `mode: primary` | `orchestrator` | Tier + Advisory-Zusage | voll | 0 |
| `advisory` | `subagent` | `subagent` | POS-2 | ja, `mode: subagent` | keiner | `gate-inactive`; **Empfehlung erst nach #1182** (D-OQ3) | voll | 1 |
| `main-chat` | ungesetzt (die Ableitung wäre `primary`) | Ableitung ist **inert** | POS-1 | **nein** | keiner; WARN `orchestrator-topology.main-chat-derived-primary` (D-Q1) | kein Gate | kein Orchestrator-State | 0 |
| `main-chat` | `primary` (gleicher Scope) | **Validierungs-ERROR** | keine Position — die Config ist ungültig | nein | keiner | harter Validator (`scripts/lib/config.py:557-563`), rc ≠ 0 | entfällt mit der Config | entfällt mit der Config |
| `main-chat` | `subagent` (provider-override oder cross-scope) | `subagent`, aber inert | POS-1 | **nein** | keiner | kein Gate; `orchestrator-topology.main-chat-supersedes` | kein Orchestrator-State | 0 |

### 3.8.3 Zusagen je Position (`DECIDED 2026-11-09`, D-OQ2)

Beide Opencode-Positionen sind **first-class**: sie werden je einzeln generiert und getestet, und
keine von beiden trägt eine „nicht empfohlen"-Markierung. Verbindlich ist:

1. **POS-1 erzeugt keinen dangling `default_agent`.** Der Sync schreibt den Key nicht; ein von ihm
   verwalteter Wert wird per State-Rollback zurückgenommen; ein nutzereigener Wert bleibt unangetastet
   und wird genau einmal als `opencode.default-agent.dangling` gewarnt
   (`scripts/lib/isolation.py:910-924`).
2. **POS-2 erzeugt kein `mode: primary` und keinen `default_agent`** und meldet die
   Gate-Suspendierung **ehrlich** — v1 über `orchestrator-topology.gate-inactive`, v2 über den
   ursachenbewussten Log-Text aus G7 (§6.4).
3. **POS-3 ist die einzige Position** mit `mode: primary`, `default_agent: orchestrator` und
   Write-Scope-Lock.
4. Die Unterschiede entstehen ausschließlich über **Capability-Flags und Config-Keys**
   (`config/provider-capabilities.yaml`, `config/ai-providers.yaml`); ein `if provider == "…"` ist
   unzulässig (Provider-Agnostik). Eine „Einheitslogik" über alle Provider gibt es nicht.

---

## 4. Entscheidungen (D-Q1 … D-Q5, D-OQ1 … D-OQ3)

Format je Entscheidung: Kontext → Entscheidung → Alternativen → Konsequenzen.

### D-Q1 — `mode: main-chat` + **abgeleitetes** `primary`: WARNING mit neuer Check-ID

**Kontext.** `mode: main-chat` bei *deklarierter* Topologie ist ein harter ERROR
(`config.py:557-563`). Bei **abgeleiteter** Topologie passiert nichts: der Resolver leitet
`primary` ab (denn `mode` beeinflusst ihn nie, `topology.py:196-206`), die Rolle wird nicht
emittiert, die Position ist gegenstandslos — und `_user_owned_default_agent` schweigt, weil
`effective == "primary"` (`consistency/topology.py:127-128`).

**Entscheidung.** **WARNING**, neue Check-ID
**`orchestrator-topology.main-chat-derived-primary`** (Severity `WARNING`, rc bleibt 0, auch in
`--check`). Exakter Text (gepinnt als Teilstring, `<P>` = Provider-Name):

```
orchestrator-topology.main-chat-derived-primary: orchestrator.mode is 'main-chat'
for provider '<P>', but the unset orchestrator.topology derives 'primary'
(providers.<P>.primary-role names the role and it is in the active set). In main-chat the
role is not emitted, so the derived position is inert. Remedy: declare
orchestrator.provider-overrides.<P>.topology: subagent (legal next to mode: main-chat), or
remove the derivation source. Declaring orchestrator.topology at project scope next to
mode: main-chat is an ERROR, not a remedy.
```

**`DECIDED 2026-11-09` (D-OQ1 / D-OQ2) — Kontext des Befunds geschärft.** In `mode: main-chat`
**ist** der Main Chat der Orchestrator (POS-1, §3.8.1): die Rolle wird per Design nicht emittiert,
deshalb ist die abgeleitete Position gegenstandslos. Der Befund beschreibt damit einen
**dangling**-Zustand (die Config deutet auf eine Rolle, die der Sync nicht schreibt), **keine**
verbotene Kombination — es gibt in `main-chat` keine unausführbare Pflicht, weil keine Regel an eine
nicht existierende Rolle adressiert. Die Remediation bleibt unverändert gültig: Override
`orchestrator.provider-overrides.<P>.topology: subagent` (dann ist die Rolle emittiert und POS-2
aktiv) oder Ableitungsquelle entfernen. Sobald dieses Repo `orchestrator.topology: subagent`
**explizit** deklariert (Plan-Task T20), ist der Befund hier gegenstandslos.

**Alternativen.**
- *Harter ERROR*: verworfen. Die Config ist **nicht** widersprüchlich — der Widerspruch entsteht
  erst in der Ableitung, die der Nutzer nie geschrieben hat. Ein rc≠0 auf einer gültigen Config
  bricht D9/AC-6 (`docs/specs/2026-11-04-orchestrator-topology-spec.md:128`, `:805-810`) und
  jede Bestandsinstallation, die `mode: main-chat` ohne `topology` fährt.
- *Dokumentierte Präzedenz („`main-chat` schluckt die Ableitung, fertig")*: verworfen. Sie ist
  heute schon implementiert — genau sie erzeugt das stille Verhalten. Der Fall muss laut sein,
  weil ein nutzereigenes `default_agent: orchestrator` dabei auf eine nicht generierte Rolle
  zeigt (#1090-Klasse, `isolation.py:910-924` deckt nur den `entry is None`-Zweig ab).

**Konsequenzen.**
- Die Ableitung wird sichtbar, ohne Bestandsprojekte zu brechen (`degraded_from`-Semantik
  unberührt: keine Degradierung, `topology.py:258-261`).
- Same-Scope-**deklariert** bleibt ERROR (`config.py:557-563`) — AC-2 pinnt das unverändert.
- Der Renderpfad braucht zusätzlich ein Inert-Signal, sonst rendert `main-chat` weiter
  `ORCH_TOPOLOGY=primary` (§5, G2).

### D-Q2 — `strict` × `primary` in einer Main-Chat-Session: **Nutzungsfehler** (c), statisch prüfbarer Teil als (a)

**Kontext.** Der Zustand „`strict` + effektiv `primary` + Session startet im Main Chat" ist zur
Sync-Zeit **nicht** entscheidbar: der Sync sieht Dateien, nicht die Session-Form. Es gibt aber
einen *Teil*, der statisch entscheidbar ist: ob die Datei, die die Session steuert
(`default_agent`), überhaupt auf den Einstieg zeigt.

**Entscheidung.**
1. **Primär (c):** Es ist ein **Nutzungsfehler**, kein Config-Fehler. Die Regel wird als
   dokumentierte Betriebsregel geführt und **im gerenderten Gate-Text** ausgesprochen
   (§5, G1) — inklusive des Auswegs (`orchestrator.mode: main-chat` oder
   `orchestrator.topology: subagent`).
2. **Sekundär (a), nur der entscheidbare Teil:** neue Check-ID
   **`orchestrator-topology.strict-primary-entry-mismatch`** (WARNING). Bedingung: `mode == strict`
   **und** `effective == "primary"` **und** der Provider besitzt eine schreibbare
   `default_agent`-Fläche (`owns_gate_surface`) **und** der committete `default_agent` fehlt oder
   nennt eine andere Rolle. Text (gepinnt):

```
orchestrator-topology.strict-primary-entry-mismatch: orchestrator.mode is 'strict' and the
effective orchestrator topology for provider '<P>' is 'primary', but default_agent is
'<absent|value>' — the session does not start in the role that the strict gate requires.
Set default_agent to 'orchestrator', or run with orchestrator.mode: main-chat, or set
orchestrator.topology: subagent for this provider.
```

   Das ist die **einzige** Stelle, an der `mode` in eine Prüfung eingeht — der Resolver bleibt
   mode-agnostisch (§5, G6).
3. **(b) bleibt zulässig — mit qualifizierter Zusage (`DECIDED 2026-11-09`, D-OQ2).** „Main Chat
   spawnt den Orchestrator" unter `strict` ist die Zelle `strict` × `subagent` (POS-2, §3.8.2). Sie
   ist **erlaubt und empfohlen**; der Preis ist bekannt und wird nicht versteckt: unter `subagent`
   wird bewusst **kein** `default_agent` geschrieben und **kein** Deny emittiert
   (`isolation.py:866-872`, `:932-962`; AC-20 der Vorgänger-Spec,
   `docs/specs/2026-11-04-orchestrator-topology-spec.md:956-964`), und genau das meldet
   `orchestrator-topology.gate-inactive` (§6.4). Die Rev.-1-Formulierung, diese Zelle sei „ein
   Widerspruch in der Zusage, kein Betriebsmodus", ist damit **zurückgenommen**: die Zelle bleibt,
   aber die Zusage wird auf den **tatsächlich** greifenden Tier heruntergebrochen (§6.5) statt
   `strict` als Erzwingung zu verkaufen.

**Konsequenzen für Write-Scope-Lock und Runtime-Gate.**

| Topologie | Write-Scope-Lock (Agent-Ebene) | Runtime-Gate | Zusage |
|---|---|---|---|
| `primary` (POS-3) | aktiv, gekoppelt an `mode == 'primary'` (`provider_transform.py:529-531`) | Deny geschrieben (`isolation.py:932`, D1a) | so stark wie das Tier: `hook` voll, `permission` PARTIAL, `plugin` = observe + Deny |
| `subagent` (POS-2) | **nicht** aktiv (kein `mode: primary`) | Deny bewusst nicht geschrieben, `orchestrator-topology.gate-inactive` WARN | prompt-basiert: `strict` bleibt die Absicht, der Tier sagt, was davon trägt (`hook` erzwungen, `permission`/`plugin` nicht) |

**Warum das die richtige Wahl ist.** (c) beschreibt die Realität ehrlich (die Session-Form ist
eine Nutzerentscheidung), (a) fängt den einzigen maschinell erkennbaren Teil davon ab, und (b) ist
als POS-2 zulässig, **weil** die Suspendierung sichtbar gemeldet wird — nicht, weil `strict` dort
erzwungen würde.

### D-Q3 — Beste Kombination je Surface

**`DECIDED 2026-11-09` (D-OQ1 / D-OQ2 / D-OQ3).** Empfehlung je Surface — genau **eine**
`RECOMMENDED`-Zelle pro Surface, volle 24-Zellen-Matrix mit Positions-Spalte in §12:

| Surface | Empfohlen (`RECOMMENDED`) | Position | Begründung in einem Satz |
|---|---|---|---|
| OpenCode v1 | `strict` × `subagent` | POS-2 | Der Orchestrator bleibt eine echte Governance-Instanz im Subagenten und der Main Chat der Kontext-Owner; der Gate-Tier ist auf v1 `permission` (PARTIAL) und wird bei `subagent` **ehrlich** als suspendiert gemeldet (`gate-inactive`) statt als erzwungen verkauft. |
| OpenCode v2 | `strict` × `subagent` | POS-2 | Dasselbe Argument; das `observe`-Plugin trägt nicht, `permission_deny_required` würde die `permissions[]`-Tripel nur mit Entry-Point aktiv halten (`runtime-gate-tiers.md:50-53`) — die Begründung der Empfehlung ist Session-Ownership, **nicht** Enforcement (H3 **bestätigt**). |
| Claude | `strict` × `subagent` | POS-2 | `hook`-Tier ist der einzige voll erzwungene Tier (`runtime-gate-tiers.md:36`); Claude hat **kein** `primary-role`, also ist `subagent` die natürliche Ableitung und der Main Chat der dauerhafte Kontext-Owner. |
| Gemini | `strict` × `subagent` | POS-2 | `topology_support.primary: false` — `primary` ist dort keine Zelle, sondern eine Degradierung mit WARN (`provider-capabilities.yaml:263-266`, `topology.py:147-183`). |

**`strict` × `primary` (POS-3) bleibt als dritte, optionale Position `ALLOWED`** — ohne Abwertung und
ohne „nicht empfohlen"-Markierung: sie liefert 0 Hop und auf v1/v2 einen echten Deny, verlangt aber,
dass die Session tatsächlich im Orchestrator startet (Nutzerentscheidung, D-Q2). Beide
Opencode-Positionen sind first-class (D-OQ2, §3.8.3).

**Empfehlung für agent-meta selbst:** **`strict` × `subagent`, explizit deklariert**
(`orchestrator.topology: subagent` in `.meta-config/project.yaml`). Grund: heute ist die Position
abgeleitet, deshalb rendert `ORCH_TOPOLOGY_EXPLICIT=false` und die Templates fallen in den
else-Zweig (Lücke 2/4/5); zusätzlich ist „derived vs. declared" hier die Ursache der Divergenz.
Die explizite Deklaration ist die billigste Reparatur von vier der neun Lücken und macht D-Q1 in
diesem Repo gegenstandslos. Sie ist **nicht** Teil dieser Spec (§7), sondern der letzte
Umsetzungsschritt des Plans (T20, **nach** dem Code-Fix, mit Rollback).

**Empfehlung für Zielprojekte:**

- *Single-User-Harness*: `strict` × `subagent` (Default, POS-2) — dieselbe Governance wie `primary`,
  aber ohne die Anforderung, dass die Session im Orchestrator startet. Wer 0 Hop will, wählt bewusst
  `strict` × `primary` (POS-3) und akzeptiert die Session-Start-Abhängigkeit; Scratch-/Review-Sessions
  laufen mit `orchestrator.mode: main-chat` (POS-1).
- *Team / Multi-Workstream*: `advisory` × `subagent` — **`DECIDED 2026-11-09` (D-OQ3): erst nach dem
  Fix von #1182** (`context-profile: compact` bricht für `advisory` ab) flächig tragfähig. Bis dahin
  ist **`strict` × `subagent`** die belastbare Team-Empfehlung; `advisory` × `subagent` wird in der
  Matrix als `ALLOWED (Team-Empfehlung, setzt #1182 voraus)` geführt und ist **keine** freigegebene
  Zusage.

`hybrid` erscheint in der Matrix ausschließlich als **„degraded to `subagent`"**
(`topology_verified_state.hybrid: UNVERIFIED`, `provider-capabilities.yaml:209`; D2 bleibt
unangetastet).

### D-Q4 — Kosten/Nutzen des zusätzlichen Hops

**Definition.** Der „Hop" ist **keine** Eigenschaft von `strict`, sondern der **Position** (§3.8):

- **POS-3 (`primary`)**: Session → Orchestrator (identisch, **0 Hop**). Die Governance (Classify,
  Spec/Plan-Gate, A2A, Checkpointing, Review-Loop) kostet **keinen** zusätzlichen Modellaufruf.
- **POS-2 (`subagent`)**: Session → Orchestrator → Worker (**1 Hop** pro Arbeitseinheit) — ein
  zusätzlicher Modellaufruf mit eigenem System-Prompt, ein zusätzliches Kontextfenster und ein
  zusätzlicher Fehlermodus (der Orchestrator kann „nichts tun" und trotzdem erfolgreich aussehen).
- **POS-1 (`main-chat`)**: Session → Main Chat als Router/Worker (**0 Hop**, aber auch **kein**
  Orchestrator-State: Classify-Route, Review-Loop und A2A-Handoff entfallen mit der Rolle).

**Kosten (ESTIMATE, Messmethode in Klammern):**
- Prompt-Overhead pro Hop: **4–8k Tokens** Orchestrator-System-Prompt
  (`wc -c .opencode/agents/orchestrator.md` / 4 — **nicht gemessen**).
- Latenz: **1 zusätzlicher Modell-Roundtrip** vor der ersten Worker-Aktion.
- Buchhaltung: ein zusätzlicher A2A-Envelope (`payload.t` ≤ 300 Zeichen, Default
  `orchestrator.handoff.t-size-limit`) und ein zusätzlicher Checkpoint-Scope.

**Nutzen (nur ab M):** Classify-Route, Spec/Plan-Gate (`Status: APPROVED`), Review-Loop-Governance,
Kontext-Isolation, A2A-Handoff, Checkpointing. Für S-Aufgaben fällt **kein** Nutzen an: die
Classify-Route überspringt den Workflow (`rules/1-generic/spec-plan-workflow.md:29`).

**Schwellwert.** **S (≤2 Dateien, kein Architektur-Impact) → direkter Dispatch ist besser.**
Ab **M (3–8 Dateien)** amortisiert der Hop seine Kosten, weil er Artefakte erzeugt, die der
direkte Pfad nicht hat (`spec-plan-workflow.md:30-32`).

**Empfehlung für Single-User-Harness (`DECIDED 2026-11-09`, D-OQ1).** **`strict` × `subagent` ist der
Default** (POS-2): 1 Hop, dafür eine echte Governance-Instanz und ein Provider-unabhängiger Start.
**`strict` × `primary` bleibt gleichwertig wählbar** (POS-3): dieselbe Governance **ohne** den Hop,
aber mit der Abhängigkeit, dass die Session tatsächlich im Orchestrator startet. Wer POS-3 wählt,
akzeptiert diese Session-Start-Bindung; wer POS-2 wählt, akzeptiert den Hop und — auf v1/v2 — den
ausfallenden Runtime-Gate-Deny (D-Q2-Tabelle). POS-1 ist die dritte Option für Sessions, die bewusst
ohne Rolle laufen sollen.

### D-Q5 — `direct-dispatch-enabled` unter `mode: main-chat`: als wirkungslos dokumentieren + INFO

**Kontext.** Der Key ist **nicht** generell modusabhängig. `{{#if DIRECT_DISPATCH_ENABLED}}` gated
die Sektion „Task decomposition & delegation" des **Orchestrator-Agenten**
(`agents/1-generic/orchestrator.md:203-205`), und `DIRECT_DISPATCH_SECTION` wird unabhängig vom
Modus gebaut (`scripts/lib/config.py:2090-2101`). Unter `strict` und unter `advisory` ist der Key
damit **wirksam**: in diesem Repo (`strict`, Key explizit gesetzt, `.meta-config/project.yaml:311`)
rendert die Sektion. Wirkungslos ist er ausschließlich unter `mode: main-chat` — dort wird die
Orchestrator-Rolle nicht emittiert (`scripts/lib/provider_transform.py:488-499`) und der
`advisory`-Zweig der Regel entfällt (`rules/1-generic/use-orchestrator.md:25-31`), sodass **kein**
Konsument des Keys mehr existiert. Ein `direct-dispatch-inert`-Finding unter `strict` wäre daher
falsch und würde zur Beschneidung einer funktionierenden Agent-Ausgabe raten.

**Entscheidung.** **Dokumentieren + INFO**, kein Validator-Fehler, keine Warnung:

- Neue Check-ID **`orchestrator-strict.direct-dispatch-inert`** (Severity **INFO**, Ablage
  `scripts/lib/consistency/orchestrator_strict.py` in Nachbarschaft von
  `orchestrator-strict.no-hook-support`, `:36`; Namespace-Konvention
  `docs/concepts/runtime-gate-tiers.md:135-145`).
- Bedingung: `mode == "main-chat"` **und** `"direct-dispatch-enabled" in orchestrator`
  (**Präsenz**, nicht Truthiness). Unter `strict`/`advisory` entsteht **kein** Finding; fehlt der
  Key, entsteht ebenfalls keins (Default `true`, `scripts/lib/config.py:2003`).
- Text (gepinnt, **ohne** Entfernungs-Rat für den wirksamen Fall):

```
orchestrator-strict.direct-dispatch-inert: orchestrator.direct-dispatch-enabled is set but
orchestrator.mode is 'main-chat' — in main-chat the orchestrator role is not emitted, so the
key has no consumer. If main-chat is intended: remove the key. If direct dispatch is
intended: run with mode: strict or mode: advisory — there the key is effective and renders
the 'Task decomposition & delegation' section of the orchestrator agent.
```

**Alternativen.**
- *Validieren (ERROR)*: verworfen — der Key ist nicht falsch, nur wirkungslos; ein Fehler auf einer
  gültigen, abwärtskompatiblen Config ist unverhältnismäßig.
- *Als tot dokumentieren ohne Finding*: verworfen, weil die Präsenz ein Absichts-Signal ist
  („ich will direkten Dispatch") und stille Ignoranz genau das Muster ist, das #1190 anprangert.
- *Finding auch unter `strict` (Rev. 1)*: verworfen — sachlich falsch (Review-Befund RVW-1190-01);
  der Key rendert dort die Delegations-Sektion.

**Konsequenzen.** Kein Schema-Change, kein rc-Einfluss. Der Check wird ausschließlich aus
`_handle_validate` gerufen (`scripts/lib/cli_commands.py:1457-1464`); der
Consistency-Check-Runner (`scripts/consistency-check.py`) ruft
`check_orchestrator_strict_hook_support` **nicht** auf — der Kanal ist damit **`--validate`-only**.
Die Bedingung ist provider-unabhängig (Modus + Key-Präsenz auf Projekt-Ebene), die Prüfung steht
deshalb **einmal pro Lauf vor dem Provider-Loop** und erzeugt **genau ein** INFO pro Lauf
(Rev. 3 / RVW2-1190-05). In diesem Repo (`mode: strict`, Key gesetzt) entsteht **kein** `[INF]`
mit der ID `orchestrator-strict.direct-dispatch-inert`; der bestehende INFO
`orchestrator-strict.no-hook-support` (`scripts/lib/consistency/orchestrator_strict.py:234-245`)
bleibt davon unberührt (Rev. 3 / RVW2-1190-06).

**`DECIDED 2026-11-09` (D-OQ1) — Einordnung.** `mode: main-chat` **ist** POS-1 (§3.8.1): der Main Chat
ist der Orchestrator, es gibt keinen Konsumenten des Keys, und die Gate-Regel ist inert. Der INFO ist
damit die **Positions-Aussage** zur Abwesenheit der Rolle, keine Warnung über eine Fehlkonfiguration —
deshalb bleibt es bei Severity `INFO` und rc 0.

---

## 5. Design-Änderungen (G1 … G9)

Jede Änderung nennt Soll-Verhalten, Ort und den Contract, den sie berührt.

### G1 — Gate-Text mit Topologie-Vorbedingung (Lücke 1)

**Ort:** `rules/1-generic/use-orchestrator.md:1-24`.
**Soll:** Die **Sektion `# CRITICAL GATE` bleibt in allen Varianten unverändert im Namen**
(sonst bricht der Compact-Pfad, der die Sektion `CRITICAL GATE` verlangt — siehe #1182 und §11).
Innerhalb der Sektion wird der Impressiv-Satz topologieabhängig, gesteuert von
`ORCH_TOPOLOGY_EFFECTIVE_PRIMARY` (G2):

- **`primary`** → der Satz „MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`.
  Keine Ausnahmen." wird ersetzt durch:

```
Der `orchestrator` ist in diesem Projekt der Session-Einstieg (`strict` verlangt das).
Eine Session im Main Chat erfüllt dieses Gate nur, wenn sie jede Entwicklungsaufgabe an
den `orchestrator` delegiert — vorausgesetzt, der Provider lässt diesen Start aus dem
Main Chat zu — oder wenn der Nutzer `orchestrator.mode: main-chat` setzt (dann ist der
Main Chat Router + Worker).
```

Der zweite Satz ist **capability-/positionsbasiert** (Rev. 3 / RVW2-1190-04): er nennt beide
legalen Wege und qualifiziert den Delegations-Weg mit der Provider-Voraussetzung, statt für jede
effektive `primary`-Position zu behaupten, eine Main-Chat-Session könne das Gate nicht erfüllen.
Auf Claude (`topology_support.primary: true`, `main_agent_selectable: true`,
`config/provider-capabilities.yaml:144`, `:148`; §12.4) bleibt der Delegations-Weg offen, auf
OpenCode greift der `mode: main-chat`-Ausweg bzw. der Start im Orchestrator. Der Text enthält
**keinen** Provider-Namen und **keine** absolute Spawnbarkeits-Behauptung.

- **`subagent`** → der heutige Wortlaut (`… ALLES -> orchestrator. Keine Ausnahmen.` bzw. die
  `GATE_PARTIAL`/`GATE_ADVISORY`-Varianten) **wortgleich** — AC-6-Identität bleibt.

Der tier-spezifische Provenienz-Absatz (`GATE_PARTIAL`/`GATE_ADVISORY`) bleibt in **beiden**
Varianten erhalten: die Topologie ändert die Ausführbarkeit, nicht die Stärke der Zusage.
Das `Keine Ausnahmen` bleibt damit erhalten, wo es ausführbar ist, und verschwindet, wo es das
nicht ist. Kein Provider-Name im Code, keine neue Bedingung außerhalb der Topologie-Flags.

**Bewusst nicht aufgenommen:** die Rev.-1-Formulierung „es gibt keinen Spawn-Kanal" / „cannot run
as a subagent". Sie ist auf Claude falsch (`topology_support.primary: true`, `hook`-Tier, der Main
Chat spawnt legal — §12.4) und hängt nicht an `EFFECTIVE_PRIMARY`, sondern an der Emission von
`mode: primary`. Wenn sie später gewünscht ist, muss sie datengetrieben an eine Capability
(`topology_support.hybrid`/`mode: primary` emittiert) gebunden werden, nie an
`ORCH_TOPOLOGY_EFFECTIVE_PRIMARY` allein. Rev. 2/3 lässt sie ersatzlos weg — der Gate-Text nennt
stattdessen die Position, den qualifizierten Delegations-Weg und den Ausweg.

### G2 — Render-Flags auf **effective** Topologie (Lücke 2)

**Ort:** `scripts/lib/variables.py:330-356` (Builder), plus die drei provider-skopierten
Re-Resolution-Stellen `rules.py:281-293`, `context.py:2575-2586`, `agent_sync.py:510-554` (G3).

**Neue Flags (additiv, `declared` bleibt):**

| Flag | Wert | Bedeutung |
|---|---|---|
| `ORCH_TOPOLOGY` | `""` \| `primary` \| `subagent` \| `hybrid` | **unverändert**: deklarierter Wert, sonst leer |
| `ORCH_TOPOLOGY_EXPLICIT` | `true`\|`false` | **unverändert**: projekt-skopierte Deklaration (Audit-Aussage „hat der Nutzer es geschrieben?") |
| `ORCH_TOPOLOGY_EFFECTIVE` | `primary`\|`subagent`\|`hybrid` | neu: `resolution.effective` (immer in `VALID_TOPOLOGIES`) |
| `ORCH_TOPOLOGY_EFFECTIVE_SOURCE` | `provider-override`\|`project`\|`derived` | neu: `resolution.source` — **Audit-/Doku-Flag**, kein Conditional |
| `ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT` | `true`\|`false` | neu: `resolution.source != "derived"` — „die Position ist nicht die naive Ableitung" |
| `ORCH_TOPOLOGY_EFFECTIVE_PRIMARY` / `_SUBAGENT` / `_HYBRID` | genau eines `true` | neu: Verzweigung in Templates |
| `ORCH_TOPOLOGY_INERT` | `true`\|`false` | neu: `true` iff `mode == "main-chat"` (Rev. 3 / RVW2-1190-12: die Rev.-2-Zusatzbedingung „eine Positionsaussage existiert" ist gestrichen — `effective` ist per Invariante nie leer, sie war wirkungslos); Konsument ist `_singleton_constraint_block(..., inert=…)` (G4) |

**Formel-Korrektur (Rev. 2, K-1 aus Review 1):** Die Rev.-1-Formel
`effective != declared or source != "derived"` ist bei `declared is None` **immer `true`**
(`"primary" != None`) und würde in jedem Default-Consumer den `{{#if}}`-Zweig öffnen — Verstoß
gegen AC-16. Verbindlich ist deshalb `source != "derived"`.

**Registrierung (fail-closed):** Die **fünf Bool-Flags** (`_EFFECTIVE_EXPLICIT`,
`_EFFECTIVE_PRIMARY`, `_EFFECTIVE_SUBAGENT`, `_EFFECTIVE_HYBRID`, `_INERT`) stehen in allen vier
Registrierungen: `strip_inactive_conditional_blocks`-Whitelist, `_FALSE_DEFAULT_CONDITIONALS`,
`standalone._CONDITIONAL_FALSE_FLAGS`, `consistency/placeholders._BUILTIN_VARS`
(vgl. `docs/specs/2026-11-04-orchestrator-topology-spec.md:316-339`). Die **zwei String-Flags**
(`_EFFECTIVE`, `_EFFECTIVE_SOURCE`) sind keine Conditionals und werden nur in
`_BUILTIN_VARS` geführt (Doku-/Audit-Namen) — sie dürfen in **keiner** Bool-Registrierung stehen.
**Invariante:** `ORCH_TOPOLOGY_EFFECTIVE` ist **nie** `"none"` — der „inert"-Fall wird
ausschließlich über `ORCH_TOPOLOGY_INERT` ausgedrückt, damit die Resolver-Invariante
(`topology.py:72-77`) unangetastet bleibt.

**Ein ActiveSet pro Provider und Lauf (Rev. 3, R-07 + RVW2-1190-03):** `_provider_topology_flags`
erhält `active_set` als **Pflicht-Keyword** (dokumentiert „same set as emission") und löst den
`ActiveSet` **nie** selbst auf (kein `compute_active_set` im Helfer); die Position selbst bildet
sie über `resolve_topology` — genau einmal pro Aufruf. Durchgereicht wird der per-Sync-`ActiveSet` an alle vier Seams: Emission
(`provider_transform.py:480-493`, `agent_sync.py:1427-1430`), Rules
(`rules.sync_rules`/`sync_embedded_rule_files`), Context
(`sync_context_for_provider`/`_build_managed_block`) und den Topologie-Helfer selbst. Der
**Context-Seam liegt in Stage 4**, nicht in Stage 6: Aufrufstelle ist
`sync_pipeline._sync_stage_contexts` (`scripts/lib/sync_pipeline.py:732-737`), die
`sync_context_for_provider` bei `:788-790` aufruft. `_sync_stage_contexts` erhält `active_set`
als **Pflicht-Keyword** (kein Default — ein Default `None` würde AC-30 aushebeln) und wird von
`scripts/lib/cli_commands.py:1543` mit `ctx.active_set` (gesetzt in `:964`) aufgerufen.
`_sync_stage_per_provider` (`:1335-1446`) reicht denselben Set an Emission, Rules und den
Reconcile (G7). Ohne diese Bindung fällt `_derive` (`topology.py:135-140`) auf die leere Menge
zurück und liefert immer `subagent` (`rules.py:281-288`, `context.py:2575-2581`).

**Die provider-lose Basis ist nicht autoritativ (Rev. 3 / RVW2-1190-09).**
`config._build_orch_variables` (`scripts/lib/config.py:2013-2037`) füllt die neuen Flags einmal
provider-los; dieser Wert ist **nur** der Ausgangspunkt und darf von **keinem** Render-Seam
konsumiert werden, ohne dass `_provider_topology_flags` ihn überschreibt. Konkret steht in
diesem Repo (kein Key, abgeleitetes `primary`) in der Basis `ORCH_TOPOLOGY_EFFECTIVE ==
"subagent"` — das ist bewusst **keine** Positionsaussage. Ein Ratchet-Test (AC-30) schlägt fehl,
sobald ein Render-Seam die `ORCH_TOPOLOGY_EFFECTIVE*`-Werte der globalen Basis ohne
Provider-Override liest.

**Verwendung:** `agents/1-generic/orchestrator.md:19`, `agents/1-generic/_reference-agent.md:24` und
`rules/1-generic/a2a-delegation-gates.md:6-19` verzweigen künftig dreiwertig: zuerst
`ORCH_TOPOLOGY_EFFECTIVE_PRIMARY` (Einstiegs-Wortlaut), dann `ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT`
(heutiger expliziter Zweig), sonst der heutige else-Zweig. `ORCH_TOPOLOGY_EXPLICIT` bleibt als
Aussage „hat der Nutzer es geschrieben?" erhalten (Doku/Audit), steuert aber **nicht** mehr die
Semantik.

### G3 — Agent-Templates mit provider-skopierter Topologie (Lücke 3)

**Ort:** `scripts/lib/agent_sync.py:510-554` (`_build_provider_vars`).
**Soll:** Parität mit `rules.py`/`context.py`: Topologie (effective) pro Provider neu auflösen und
in `provider_vars` überschreiben. Zusätzlich in `sync_pipeline.py:1405-1424` den
Override-Zweig um dieselben Flags erweitern (dort werden heute nur `ORCH_MODE_*` und die
Subagent-Permissions neu gesetzt). **Kein** neuer Resolver — dieselbe Funktion
`resolve_topology(...)` wie an den beiden anderen Seams.

### G4 — Singleton-Block topologieabhängig (Lücke 4)

**Ort:** `scripts/lib/agent_sync.py:974-986`.
**Soll:** Drei Varianten, gesteuert von `ORCH_TOPOLOGY_EFFECTIVE` **und** `ORCH_TOPOLOGY_INERT`.
Die Signatur der extrahierten Funktion ist verbindlich
`_singleton_constraint_block(effective: str, *, inert: bool) -> str` — aus `effective` allein ist
die Inert-Variante nicht ableitbar, weil `ORCH_TOPOLOGY_EFFECTIVE` per Invariante nie leer/`none` ist:

- `primary` (und `not inert`): „Es existiert genau **EIN Orchestrator** pro Session — er **ist** der
  Session-Einstieg. Ein `task(subagent_type="orchestrator")`-Aufruf ist immer ein HARD REJECT
  (G1/G3)."
- `subagent` (und `not inert`): heutiger Wortlaut („der vom `main_chat` gespawnte") **wortgleich**.
- `inert == True` (`mode: main-chat`): neutraler Satz ohne Spawner-Behauptung; die Inert-Quelle ist
  `ORCH_TOPOLOGY_INERT`, nicht der Modus-Literal im Funktionsrumpf.

Die Zeile „NIEMALS `task(subagent_type="orchestrator", ...)`" bleibt in **allen** Varianten —
sie ist die kardinalitätsfreie G1/G3-Regel (`docs/concepts/active/orchestrator-topology.md:115-119`).
Der Verweis „Gate #5" (`agent_sync.py:981`) ist ein **bewusst konservierter toter Verweis**: die
a2a-Gates haben nur 1–3. Er bleibt im `subagent`-Zweig byte-identisch erhalten (AC-16) und wird
**nicht** als neuer Fehler behandelt — im Plan ist er als bewusste Übernahme markiert.

**Injektionsbedingung (unverändert):** `role != "orchestrator" and not role.endswith("-iteration")
and can_spawn` (`agent_sync.py:985`).

### G5 — Einstiegshinweis topologieabhängig (Lücke 5)

**Ort:** `scripts/lib/agents.py:171-179` (Textbausteine) und `scripts/lib/context.py:848-852`
(Entscheidung, siehe unten).
**Soll (provider-eigene, nicht geteilte Kontextdatei):**

| `effective` | Gerenderter Hinweis |
|---|---|
| `primary` | „**Einstiegspunkt:** Diese Session startet im `orchestrator`-Agenten. Ein Start im Main Chat erfüllt das Gate nur bei Delegation an den `orchestrator` — siehe `use-orchestrator.md`." |
| `subagent` | **unverändert** (Rev. 3 / RVW2-1190-01): „**Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«." (`agents.py:174`) |
| `main-chat` | unverändert (`:177-179`) |

**Entscheidung zur `subagent`-Zeile (Rev. 3 / RVW2-1190-01):** Der heutige `subagent`-Hinweis wird
**nicht** geändert. Die Rev.-2-Formulierung („Delegiere jede Entwicklungsaufgabe an den
`orchestrator`-Subagenten") ist damit zurückgenommen — sie war die zweite, unabhängige
Verletzung der Byte-Identitätszusage (`agents.py:174`). Damit bleibt der Default-Render
(`ungesetzt ∧ effective == "subagent"`) für **alle** Kontextdateien byte-identisch (AC-16).

**Geteilte Kontextdatei (verbindlich, Rev. 3 / R-05 + RVW2-1190-02).** Eine Datei, die mehrere
Provider lesen, wird nacheinander von jedem Sharer geschrieben und muss deshalb **identisch**
rendern (Kommentar `context.py:721-722`, Oszillationsschutz `_shared_context_users`
`context.py:2246`). Sie darf **keine** positionsspezifische Falschaussage tragen — in diesem Repo
leitet Opencode `primary`, Gemini `subagent` ab (`config/provider-capabilities.yaml:206-209`,
`:263-266`). Regel:

- Rendern **alle** aktiven Sharer dieselbe Position, wird **genau dieser** Text gerendert
  (Byte-Identität für den reinen `subagent`-Fall, AC-16).
- Unterscheiden sich die Positionen, rendert **immer** der neutrale Text:

```
**Einstiegspunkt:** Entwicklungsaufgaben laufen über den `orchestrator`-Agenten. Ob er der
Session-Einstieg ist oder ein Subagent, hängt von `orchestrator.topology` ab — siehe
`use-orchestrator.md`.
```

**Ort der Entscheidung (Rev. 3 / RVW2-1190-02).** Die Entscheidung fällt **nicht** in
`build_agent_hints` — die Funktion kennt weder Provider noch Zieldatei (`agents.py:132-140`) und
wird provider-los aus dem globalen Variablen-Bau gerufen (`config.py:1686-1688`, `:1950-1953`).
Sie fällt in `context.py`, wo Provider, Ziel und Sharer bekannt sind: neuer Helfer
`_position_aware_agent_hints(...)`, aufgerufen aus `_sync_managed_block_context` (`:848-852`,
kennt `provider`, `target_name`, `provider_config`, `active_set` und
`_shared_context_users`). `build_agent_hints` bekommt nur noch den expliziten
`position`-Parameter (Default `"neutral"`). Die globalen Aufrufer behalten den neutralen Text —
er ist für jeden Leser wahr. **Konsumenten des Hinweises heute:**
`templates/context/claude-managed.md:12` (CLAUDE.md), `templates/configs/CLAUDE.project-template.md:37`,
`templates/configs/CONTINUE.project-template.md:20`, `templates/configs/COPILOT.project-template.md:14`.
`templates/context/agents-managed.md` rendert **keinen** `AGENT_HINTS` — die geteilte `AGENTS.md`
trägt den Hinweis derzeit nicht; die Safe-Side-Regel bleibt trotzdem verbindlich, weil der
Platzhalter in Projekt-Templates frei verwendbar ist.

**Safe-Side-Regel:** Kein Render darf mehr behaupten, als für **alle** Leser desselben physischen
Files gilt. Bei gemischten Sharern gewinnt der neutrale Text; die positionsspezifischen Sätze
erscheinen nur in provider-eigenen, nicht geteilten Dateien. Deterministisch bleibt es in beiden
Fällen (kein Oszillieren, unabhängig von der Provider-Reihenfolge). Die Shared-Detektion löst die
Position der Sharer mit **derselben** Funktion (`resolve_topology`) und **denselben** Eingaben
(`config`, `active_set`) auf — kein zweiter Resolver, keine abweichende Semantik.

### G6 — Validierung des unausführbaren Falls (Lücke 6)

**Ort (geteilt, Rev. 2 / R-04):** zwei neue Findings in
`scripts/lib/consistency/topology.py`; **ein** neues Finding in
`scripts/lib/consistency/orchestrator_strict.py` (Namespace
`orchestrator-strict.direct-dispatch-inert`, dort bereits `_CHECK_ID` und die Tier-Logik, `:36-39`,
`:182-250`). **Kein** Finding im Resolver.
**Soll:**

- `orchestrator-topology.main-chat-derived-primary` (D-Q1) → `consistency/topology.py`.
- `orchestrator-topology.strict-primary-entry-mismatch` (D-Q2-2) → `consistency/topology.py`.
- `orchestrator-strict.direct-dispatch-inert` (D-Q5, INFO) → `consistency/orchestrator_strict.py`,
  **einmal pro Lauf vor dem Provider-Loop** (`:226`) — die Bedingung ist provider-unabhängig, und
  hinter dem Strict-Gate (`:227-228`) würde sie im einzigen Zielmodus (`main-chat`) nie feuern
  (Rev. 3 / RVW2-1190-05).
- **Negativ-Invariante (Test):** `resolve_topology(...)` liefert für `mode ∈ {strict, advisory,
  main-chat}` **denselben** `effective`-Wert — `mode` bleibt ohne Einfluss
  (`topology.py:196-206` bleibt wahr).
- `_user_owned_default_agent` (`consistency/topology.py:127-128`) bleibt unverändert; der neue
  Mismatch-Check ist ein **eigener** Check und kein Umbau der bestehenden Früh-Rückkehr.

### G7 — v2-Reconcile übergibt `topology` (Lücke 7)

**Ort (Rev. 2 / R-03):** `scripts/lib/isolation.py` — `reconcile_opencode_surface_gate`
(def `:1751`) und `_opencode_v2_gate_permissions` (def `:1408`), **nicht**
`_sync_opencode_runtime_gate` (def `:725`). Der Spec-A-Pfad übergibt `topology=` heute schon
(`:846-856`, `:866-872`); die Defektstellen sind die beiden anderen.

**Soll:**

1. **Signaturerweiterung:** `reconcile_opencode_surface_gate(..., *, active_set, topology=None)`.
   Die Funktion löst die Topologie **nicht** selbst auf (sonst dritter Auflösungspunkt pro Provider
   und Lauf — Widerspruch zu R-3/Global Constraint „Auflösung je Provider genau einmal").
2. **Durchreichung statt Neuresolution:** derselbe `TopologyResolution`-Wert fließt an
   `_opencode_entry_point(..., topology=topology)` (`:1826-1830`) **und** an
   `_opencode_v2_gate_permissions(..., topology=topology)` (`:1840-1843`); dort wird der Wert an
   `_opencode_entry_point(...)` weitergereicht (`:1457`). Beide Stellen sind heute topology-blind.
3. **Aufrufer:** `sync_pipeline._sync_stage_per_provider` (`:1598-1602`) und der
   `--test-generated`-Pfad (`cli_commands.py:344-348`) übergeben `topology=`. Beide Stellen
   besitzen `config` + `active_set`; die Auflösung erfolgt einmal pro Provider im Pipeline-Loop
   (dieselbe Resolution, die G2/G3 für die Render-Seams nutzt) bzw. im Test-Repo-Pfad.
4. Die Zeile-6-Warnung (`:1881-1889`) wird ursachenbewusst. Neuer Text (gepinnt als Teilstring):
   `opencode-v2 gate (permissions deny) NOT written for provider '<P>': the effective
   orchestrator topology is '<effective>' — no entry point is written and the deny would lock
   every agent; see orchestrator-topology.gate-inactive.` Der alte Wortlaut („no explicit and
   generated primary-role — declare primary-role …") bleibt **nur** für den Fall
   `entry is None` **ohne** Topologie-Ursache (dann ist die `primary-role`-Diagnose korrekt).
5. Der Remediation-Text (`:1396-1404`) darf `default_agent` **nicht** mehr empfehlen, wenn die
   effektive Topologie ≠ `primary` ist.

**Wirkung:** Auf v2 + `strict` + `subagent` entsteht **kein** `permissions[]`-Deny (D1a bleibt
erfüllt) und **genau eine Log-Warnung** im Sync-Kanal statt einer irreführenden
„SUSPENDED/default_agent missing"-Meldung mit gegenläufiger Handlungsanweisung. Ein
Consistency-Finding entsteht auf v2 **nicht** — `_gate_wanted` ist Tier-`permission`-gebunden
(`consistency/topology.py:94-105`), v2 ist Tier `plugin` (siehe AC-22).

**Abgrenzung zur bestehenden Auflösung:** Die Resolution in `_sync_opencode_runtime_gate`
(`:846-856`) bleibt unverändert — sie gehört zum Spec-A-Pfad und wird von der Pipeline-Resolution
nicht ersetzt. Entscheidend ist allein, dass `reconcile_opencode_surface_gate` **keine eigene**
Resolution hinzufügt (das wäre der dritte Punkt pro Provider und Lauf).

### G8 — Tests (Lücke 8)

Neue/erweiterte Module: `tests/test_orchestrator_mode_topology_matrix.py` (24 Zellen),
`tests/test_provider_transform_topology_generic.py` (Claude/Gemini-Emission),
`tests/test_isolation_v2_topology_reconcile.py`, `tests/test_orchestrator_topology_effective_flags.py`,
`tests/test_orchestrator_topology_render_parity.py` (inkl. Zwei-Sharer-Fall, R-05/R-07),
`tests/test_use_orchestrator_topology_rendering.py`, `tests/test_singleton_block_topology.py`,
`tests/test_orchestrator_topology_checks.py` (neue Check-IDs), `tests/test_entry_hint_topology.py`.
Details in AC-24 und AC-30.

### G9 — Doku-Angleichung (Lücke 9)

Elf Befunde (§9.1) werden **einzeln** adressiert: absolute Singleton-Aussagen werden
topologie-qualifiziert, der Widerspruch „P3 shipped" vs. „designed, not shipped" wird **einmalig
zugunsten von „shipped"** aufgelöst (der Vertrag ist implementiert und validiert; AC-8…AC-12 der
Vorgänger-Spec sind umgesetzt, `docs/concepts/active/orchestrator-topology.md:91-96`), und der
**widersprüchliche Render innerhalb einer Datei** (`.claude/rules/use-orchestrator.md`:
unqualifizierter Satz + PARTIAL-Absatz unter einem suffixlosen `# CRITICAL GATE`, B-9) wird auf
**eine** konsistente Gate-Variante gebracht (Tier-Text bleibt). Die P3-Zeile der Vorgänger-Spec
(`docs/specs/2026-11-04-orchestrator-topology-spec.md:791-792`) wird **nicht** editiert, sondern
in B-7 als **überholt** ausgewiesen (ohne D1–D10 neu aufzurollen, Rev. 3 / RVW2-1190-08).

---

## Interface Contracts (§6)

### 6.1 Config-Keys

**Keine neuen Keys.** Verwendet werden ausschließlich bestehende:
`orchestrator.mode`, `orchestrator.topology`, `orchestrator.provider-overrides.<P>.{mode,topology}`,
`orchestrator.direct-dispatch-enabled`, `orchestrator.enabled`, `orchestrator.strict`.
Damit bleibt `config/project-config.schema.json` **strukturell** unverändert (nur
`description`-Texte dürfen die neue Empfehlung nennen) — relevant für #1186/#1188 (§11).

**Position ist kein Key (`DECIDED 2026-11-09`, D-OQ1).** Es gibt keinen `position`-Key: die Position
wird aus `mode` + `effective` abgeleitet (§3.8.2). Die für dieses Repo beschlossene Deklaration
`orchestrator.topology: subagent` ist ein **bestehender** Key, der bisher nur ungesetzt war; sie
ändert kein Schema und ist Plan-Task T20.

### 6.2 Check-IDs

| ID | Severity | Bedingung | Ort | Phase |
|---|---|---|---|---|
| `orchestrator-topology.main-chat-derived-primary` | WARNING | `mode == "main-chat"` **und** `topology` ungesetzt **und** abgeleitetes `effective == "primary"` | `consistency/topology.py` | neu |
| `orchestrator-topology.strict-primary-entry-mismatch` | WARNING | `mode == "strict"` **und** `effective == "primary"` **und** Provider besitzt `default_agent`-Fläche **und** `default_agent` fehlt/fremd | `consistency/topology.py` | neu |
| `orchestrator-strict.direct-dispatch-inert` | INFO | `mode == "main-chat"` **und** Key `direct-dispatch-enabled` **präsent**; genau **ein** INFO pro Lauf, Kanal `--validate` | `consistency/orchestrator_strict.py` | neu |
| `orchestrator-topology.degraded` / `.hybrid-unverified` / `.main-chat-supersedes` / `.gate-inactive` / `.default-agent-conflict` / `.instances-clamped` | wie Spec 2026-11-04 | unverändert | `consistency/topology.py` | bestehend |
| `orchestrator-strict.no-hook-support` | tier-abhängig | unverändert | `consistency/orchestrator_strict.py` | bestehend |

Alle neuen IDs sind WARNING/INFO — **keine** davon ändert den Exit-Code (AC-6-Kontinuität).
Unter `strict` entsteht **kein** `orchestrator-strict.direct-dispatch-inert`: der Key ist dort
wirksam (D-Q5).

### 6.3 Flag-Namen

Neu: `ORCH_TOPOLOGY_EFFECTIVE`, `ORCH_TOPOLOGY_EFFECTIVE_SOURCE`,
`ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT`, `ORCH_TOPOLOGY_EFFECTIVE_PRIMARY`,
`ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT`, `ORCH_TOPOLOGY_EFFECTIVE_HYBRID`, `ORCH_TOPOLOGY_INERT`.
Unverändert: `ORCH_TOPOLOGY`, `ORCH_TOPOLOGY_EXPLICIT`, `ORCH_TOPOLOGY_PRIMARY`,
`ORCH_TOPOLOGY_SUBAGENT`, `ORCH_TOPOLOGY_HYBRID`, `ORCH_TOPOLOGY_SOURCE`, `ORCH_MODE_*`,
`GATE_ENFORCED|GATE_PARTIAL|GATE_ADVISORY|GATE_NEUTRAL`, `ENFORCEMENT_TIER`.

**Condition-Flag vs. Audit-Flag (Rev. 2):** Condition-Flags sind ausschließlich
`ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT`, `_EFFECTIVE_PRIMARY`, `_EFFECTIVE_SUBAGENT`,
`_EFFECTIVE_HYBRID`, `ORCH_TOPOLOGY_INERT` (fünf). `ORCH_TOPOLOGY_EFFECTIVE` und
`ORCH_TOPOLOGY_EFFECTIVE_SOURCE` sind **String-/Audit-Flags**: sie werden gerendert und
dokumentiert, aber nie in `{{#if}}` verwendet (Muster-Warnung `variables.py:95-97`).

### 6.4 Fehlertexte (gepinnt)

Die drei Texte aus D-Q1, D-Q2 und D-Q5 sind **wörtlich** als Teilstring-Assertion zu pinnen.
Der bestehende harte Validator-Text bleibt unverändert:
`orchestrator.topology conflicts with orchestrator.mode: main-chat`
(`config.py:557-563`).

**Kanal-Regel (Rev. 2 / R-10):**

| Kanal | Fall | Gepinnter Teilstring |
|---|---|---|
| Sync-Log, v2, Tier `plugin` | `strict` + `effective == "subagent"` | `opencode-v2 gate (permissions deny) NOT written for provider` **und** `effective orchestrator topology is 'subagent'` (neuer, ursachenbewusster Text aus G7 Nr. 4) |
| Sync-Log, v1 | `strict` + Rolle emittiert + `effective != "primary"` | `orchestrator-topology.gate-inactive: runtime gate` (`isolation.py:955-962`) |
| Consistency-Finding, v1 | derselbe Zustand | `runtime gate is wanted for provider` (`consistency/topology.py:370-382`, Tier `permission`) |

**Zählregel:** v1 erzeugt **zwei Meldungen in zwei Kanälen** (eine Log-Warnung, ein Finding) —
gezählt wird **je Kanal**, nicht über Kanäle hinweg. v2 erzeugt **genau eine** Meldung (Sync-Log);
auf v2 existiert **kein** Consistency-Finding, weil `_gate_wanted` Tier-`permission`-gebunden ist
(`consistency/topology.py:103-105`) und v2 Tier `plugin` ist. Eine Dedup über Kanäle wird
**nicht** eingeführt (die Kanäle haben verschiedene Sichtbarkeit).

### 6.5 Provider-Matrix (Soll-Empfehlung, nicht Capability-Änderung)

| Provider | `primary` (POS-3) | `subagent` (POS-2) | Empfehlung | Gate-Tier, der bei der Empfehlung **tatsächlich** greift |
|---|---|---|---|---|
| OpenCode v1 | ja (`permission`) | ja (`mode: subagent`, kein Deny) | `strict × subagent` | `permission` — bei `subagent` **suspendiert** (`gate-inactive`), nur Prompt-Konvention |
| OpenCode v2 | ja (`plugin` observe + Deny) | ja (`mode: subagent`, kein Deny) | `strict × subagent` | `plugin`/`observe` + `permissions[]`-Deny — bei `subagent` **kein** Deny (`gate-inactive`) |
| Claude | ja (explizit, `hook`) | ja (Ableitung) | `strict × subagent` | `hook` — **erzwungen** |
| Gemini | **nein** (degradiert) | ja (`hook`) | `strict × subagent` | `hook` — **erzwungen** |

**`DECIDED 2026-11-09` (D-OQ2).** Die Matrix weist pro Surface aus, welcher Tier **bei der gewählten
Position** greift; `strict × subagent` ist auf OpenCode erlaubt und empfohlen, aber der Deny entfällt —
das steht als `gate-inactive` in der Zeile und wird nicht als Erzwingung verkauft. `strict × primary`
bleibt `ALLOWED` (0 Hop, echter Deny, dafür Session-Start-Bindung). Keine Position wird als „nicht
empfohlen" markiert.

**Positions-Caveat (Rev. 2 / R-02):** Die Spalte `primary` bedeutet **nicht** überall „kein
Spawn-Kanal". Auf OpenCode wird die Rolle mit `mode: primary` emittiert und ist dann selbst nicht
per `task` spawnbar; auf Claude gibt es kein `mode: primary`-Konzept und der Main Chat **kann**
spawnen (`hook`-Tier, `main_agent_selectable: true`, `provider-capabilities.yaml:144`).
„Kein Spawn-Kanal" ist deshalb eine OpenCode-Aussage, keine provider-agnostische.

Die Capability-Zellen selbst werden **nicht** verändert (§7).

---

## Datenfluss (§6.6)

Die effektive Topologie entsteht **einmal je Provider und Lauf** und fließt von dort in alle
Render-Seams (§5-G2/G3/G7). Die Kette besteht aus fünf Stufen:

1. **Config** — `orchestrator.mode`, `orchestrator.topology` und
   `orchestrator.provider-overrides.<P>.{mode,topology}` werden gelesen; es gibt **keine** neuen
   Keys (§6.1).
2. **Resolver** — `resolve_topology(...)` (`scripts/lib/topology.py:186`) liefert eine
   `TopologyResolution` mit `declared`, `effective`, `source` und `degraded_from`; `mode` wird
   übergeben, beeinflusst die Position aber nicht (`:196-206`).
3. **Flag-Bau** — `_effective_topology_flags(resolution, *, mode)` erzeugt die fünf Bool- und zwei
   String-Flags; `_provider_topology_flags(config, provider, *, active_set, …)` bindet sie an den
   per-Sync-`ActiveSet` und reicht sie weiter (kein vierter Resolver, Auflösung genau einmal).
4. **Render** — Emission (`provider_transform.py:488-499`), Rules (`rules.py`), Context
   (`context.py`), Agent-Templates (`agent_sync.py`), Singleton-Block (G4) und Einstiegshinweis (G5)
   lesen ausschließlich die provider-skopierten Effektiv-Flags. Die provider-lose Basis aus
   `config._build_orch_variables` ist **nicht** autoritativ (RVW2-1190-09).
5. **Diagnose** — `--validate`/`consistency-check` prüfen den Zustand additiv (WARNING/INFO, rc 0,
   G6); der v2-Reconcile erhält dieselbe `TopologyResolution` durchgereicht (G7).

**Position (`DECIDED 2026-11-09`, D-OQ1).** Aus `mode` und `effective` folgt die Position (§3.8.2):
`effective == "primary"` ⇒ **POS-3**, `effective == "subagent"` ⇒ **POS-2**, `mode == "main-chat"` ⇒
**POS-1** (die Rolle wird nicht emittiert). Die Position ist eine Emission-/Render-Ableitung aus
Daten, keine eigene Config-Achse — es gibt keinen `position`-Key (§6.1).

---

## Nicht-Ziele (§7)

- **Kein** Neu-Verhandeln des `topology`-Enums oder der `hybrid`-Semantik (#1077 / D1/D2).
- **Keine** Änderung der `hybrid`-Degradierung, der Multi-Instanz-Achse (`max-instances`,
  `singleton`) oder der `topology_verified_state`-Zellen.
- **Keine** Lösung der OpenCode-v2-Surface-Lücken (#1007), insbesondere nicht der Plugin-
  `enforce`-Freigabe (P6).
- **Keine** Implementierung, kein Plan, kein Code, keine Config-Änderung in `.meta-config/` **durch
  diese Spec**. Die Deklaration `orchestrator.topology: subagent` für dieses Repo (D-OQ1) ist
  ausdrücklich **kein** Bestandteil dieser Spec, sondern Plan-Task T20 — sie läuft **nach** dem
  Code-Fix und ist dort mit Rollback beschrieben.
- **Keine** Änderung an `resolve_topology(...)`-Semantik (insbesondere: `mode` bleibt dort
  unbenutzt).
- **Keine** Änderung an `#1182` (compact × `advisory`); es bleibt ein externer Blocker.
- **Keine** neue Severity-Stufe, kein rc≠0 für abgeleitete Zustände.

---

## Acceptance Criteria (§8)

> Jedes AC ist prüfbar und referenziert mindestens einen Contract aus §6 oder eine Lücke aus §5.

### Q1

- [ ] **AC-1** — **Given** `mode: main-chat`, `topology` ungesetzt, `primary-role` gesetzt und Rolle
      im ActiveSet, **when** `python3 scripts/sync.py --validate` bzw. `python3 scripts/consistency-check.py`
      läuft (Kanal-Korrektur Rev. 2: `--check` führt **keine** Consistency-Checks aus, einziger
      Aufrufer ist `scripts/consistency-check.py:264-267`), **then** entsteht genau **eine** WARNING
      `orchestrator-topology.main-chat-derived-primary` pro Provider und Lauf, die den in §4-D-Q1
      gepinnten Teilstring enthält, und **rc == 0**.
- [ ] **AC-2** — **Given** `mode: main-chat` **und** deklariertes `topology` im selben Scope,
      **when** `sync` oder `--validate` läuft, **then** bleibt es bei rc ≠ 0 mit dem gepinnten
      Teilstring `orchestrator.topology conflicts with orchestrator.mode: main-chat`
      (unverändert, `config.py:557-563`).

### Q2

- [ ] **AC-3** — **Given** der gerenderte `strict`-Regeltext, **when** die effektive Topologie
      `primary` ist, **then** enthält er die positionsbasierte Vorbedingung
      (`orchestrator` ist der Session-Einstieg, `strict` verlangt das), den **qualifizierten**
      Delegations-Weg („vorausgesetzt, der Provider lässt diesen Start aus dem Main Chat zu")
      **und** den Ausweg (`orchestrator.mode: main-chat`) und **nicht** den unqualifizierten Satz
      „ALLES -> `orchestrator`. Keine Ausnahmen."; **when** die effektive Topologie `subagent`
      ist, **then** ist der Text byte-identisch zu heute. **Nicht** gepinnt wird die Aussage
      „kein Spawn-Kanal" (auf Claude falsch, §6.5-Caveat); der Test stellt zusätzlich sicher, dass
      der `primary`-Text **keinen** Provider-Namen und **keine absolute**
      Spawnbarkeits-Behauptung enthält (nicht „kein Spawn-Kanal", nicht „cannot run as a
      subagent", nicht „erfüllt dieses Gate nicht"). **Given** die `primary`-Position auf einem
      Provider, dessen Zelle `main_agent_selectable: true` trägt (`provider-capabilities.yaml:144`),
      **then** enthält der Text den Delegations-Weg als zulässigen Pfad (Claude-Negativ-Assertion,
      Rev. 3 / RVW2-1190-04).
- [ ] **AC-4** — **Given** `strict` + `effective == primary` + `default_agent` fehlt oder nennt
      eine andere Rolle, **when** der Consistency-Check läuft, **then** entsteht genau eine
      WARNING `orchestrator-topology.strict-primary-entry-mismatch` mit dem gepinnten Text;
      **given** `default_agent == orchestrator` **oder** `effective != primary`, **then** entsteht
      kein Finding.
- [ ] **AC-5** — **Given** `topology: primary`, **when** `orchestrator.md` emittiert wird,
      **then** trägt es den Write-Scope-Lock; **given** `topology: subagent` + `strict`, **then**
      ist der Lock **nicht** gesetzt und genau eine `orchestrator-topology.gate-inactive`-Meldung
      existiert im v1-Sync-Log (Kanal/Zählregel §6.4; AC-20 der Vorgänger-Spec bleibt gültig).

### Q3

- [ ] **AC-6** — **Given** die Entscheidungsmatrix in §12, **when** der Doku-Test läuft,
      **then** existieren genau 4 Surfaces × 6 `mode`×`topology`-Kombinationen = 24 Zeilen, jede
      mit Urteil (`RECOMMENDED`/`ALLOWED`/`DEGRADED`/`FORBIDDEN`); `dito`-Zellen sind innerhalb
      ihrer Tabelle auf eine Zelle mit eigener `datei:zeile`-Referenz auflösbar, und jede
      Surface-Tabelle hat mindestens einen Eintrag im Evidenz-Index (§12.6).
- [ ] **AC-7** — **Given** die Matrix, **when** der Test die Empfehlungen zählt, **then** hat jede
      Surface genau **eine** `RECOMMENDED`-Zelle, und die Menge ist exakt
      `{(v1, strict, subagent), (v2, strict, subagent), (Claude, strict, subagent),
      (Gemini, strict, subagent)}` (`DECIDED 2026-11-09`, D-OQ1); `strict × primary` ist auf v1/v2
      `ALLOWED` (optionale Session-Einstiegs-Position POS-3) und **nicht** als „nicht empfohlen"
      markiert.
- [ ] **AC-8** — **Given** die v2-Surface-Tabelle, **when** der Doku-Test die Begründungen prüft,
      **then** nennt die `RECOMMENDED`-Zeile (`strict × subagent`) Session-Ownership **und** die
      ehrliche Gate-Suspendierung (`gate-inactive`, kein `permissions[]`-Deny), und die
      `ALLOWED`-Zeile (`strict × primary`) nennt `observe` **und** `permissions`-Deny als tragende
      Schicht (H3 bestätigt) und **nicht** das Plugin als Erzwingungsinstanz.
- [ ] **AC-9** — **Given** die Gemini-Zeile, **when** `topology: primary` deklariert wird,
      **then** weist der Resolver `effective == "subagent"` aus und genau eine
      `orchestrator-topology.degraded`-WARN entsteht (vorhandenes Verhalten, hier als
      Regressionsschutz gepinnt).

### Q4

- [ ] **AC-10** — **Given** der Kostenabschnitt, **when** der Doku-Test läuft, **then** enthält er
      (a) die Definition „Hop ∈ `subagent`, 0 Hop unter `primary`", (b) den Schwellwert
      „S (≤2 Dateien) → direkter Dispatch", (c) eine als **ESTIMATE** markierte Zahl **mit**
      Messmethode und **ohne** Messbehauptung.
- [ ] **AC-11** — **Given** die Empfehlung für Single-User-Harness, **when** sie geprüft wird,
      **then** ist sie `strict × subagent` (POS-2, Default) **und** nennt `strict × primary` (POS-3)
      als gleichwertige Option mit „gleiche Governance, kein Hop, dafür Session-Start-Bindung"
      (`DECIDED 2026-11-09`, D-OQ1).

### Q5

- [ ] **AC-12** — **Given** `mode: main-chat` **und** der Key `direct-dispatch-enabled` ist
      **präsent**, **when** `--validate` läuft, **then** entsteht genau **ein** INFO
      `orchestrator-strict.direct-dispatch-inert` **pro Lauf** (nicht pro Provider) mit dem
      gepinnten Text, rc == 0; der Consistency-Check-Runner ruft den Check nicht auf (Kanal
      `--validate`-only, Rev. 3 / RVW2-1190-06). **Given** dieses Repo (`mode: strict`, Key
      gesetzt), **then** entsteht **kein** `[INF]` mit der ID
      `orchestrator-strict.direct-dispatch-inert` — der bestehende
      `orchestrator-strict.no-hook-support` bleibt davon unberührt (Rev. 3 / RVW2-1190-06).
- [ ] **AC-13** — **Given** `mode: main-chat` **ohne** den Key (Default `true`), **when** der Check
      läuft, **then** entsteht **kein** Finding; **given** `mode: strict` **oder** `mode: advisory`
      mit präsentem Key, **then** ebenfalls kein Finding (der Key ist dort wirksam); **given**
      `direct-dispatch-enabled: false` unter `main-chat` mit Präsenz, **then** entsteht ein Finding
      (Präsenz-, nicht Truthiness-Semantik).

### Lücken G1–G9

- [ ] **AC-14 (G1)** — Der `strict`-Gate-Text verzweigt ausschließlich über
      `ORCH_TOPOLOGY_EFFECTIVE_PRIMARY`; ein Grep-Test stellt sicher, dass
      `rules/1-generic/use-orchestrator.md` für die Verzweigung **keine** Provider-Name-Bedingung
      und **kein** `ORCH_TOPOLOGY_EXPLICIT` mehr verwendet.
- [ ] **AC-15 (G2)** — Die **fünf Bool-Flags** (`ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT`,
      `_EFFECTIVE_PRIMARY`, `_EFFECTIVE_SUBAGENT`, `_EFFECTIVE_HYBRID`, `ORCH_TOPOLOGY_INERT`)
      existieren und sind in **allen vier** fail-closed-Registrierungen eingetragen
      (`strip_inactive_conditional_blocks`, `_FALSE_DEFAULT_CONDITIONALS`,
      `standalone._CONDITIONAL_FALSE_FLAGS`, `consistency/placeholders._BUILTIN_VARS`); ein Test,
      der ein Bool-Flag aus einer Registrierung entfernt, schlägt fehl. Die **zwei String-Flags**
      (`ORCH_TOPOLOGY_EFFECTIVE`, `_EFFECTIVE_SOURCE`) stehen nur in `_BUILTIN_VARS` (Audit-/Doku-Namen)
      und in **keiner** Bool-Registrierung; ein Test prüft beides.
- [ ] **AC-16 (G2)** — **Given** `topology`-Key ungesetzt **und** `effective == "subagent"` für
      **alle** aktiven Renderer, **when** ein Consumer rendert, **then** ist die Ausgabe
      byte-identisch zu heute (Golden-Fixture); `ORCH_TOPOLOGY_EFFECTIVE` ist `"primary"` **oder**
      `"subagent"` — **nie** `"none"`. **Nicht** von der Zusage erfasst ist **abgeleitetes**
      `primary` (Key ungesetzt, `effective == "primary"`): das ist die **beabsichtigte** Änderung
      aus AC-17 (Rev. 3 / RVW2-1190-01).
- [ ] **AC-17 (G2/G1)** — **Given** abgeleitetes `primary` (Key ungesetzt,
      `ORCH_TOPOLOGY_EFFECTIVE_PRIMARY == "true"`), **when** `agents/1-generic/orchestrator.md`
      rendert, **then** enthält das Ergebnis **nicht** den Satz „Only `main_chat` may create you"
      und **nicht** „NUR `main_chat` darf den `orchestrator` spawnen"
      (`a2a-delegation-gates.md:17-19`). Das ist ausdrücklich eine **beabsichtigte** Änderung mit
      eigener Golden-Fixture — keine Byte-Identitäts-Zusage (Rev. 3 / RVW2-1190-01).
- [ ] **AC-18 (G3)** — **Given** `orchestrator.provider-overrides.<P>.topology: subagent` bei
      globalem `primary`, **when** Agent-Dateien für `<P>` und für einen zweiten Provider
      gerendert werden, **then** tragen die Agent-Templates von `<P>` `_SUBAGENT == "true"` und
      die des anderen Providers `_PRIMARY == "true"` (Parität mit Rules/Context).
- [ ] **AC-19 (G4)** — **Given** `effective == primary`, **when** ein spawn-fähiger Worker-Agent
      gerendert wird, **then** enthält der Singleton-Block **nicht** „der vom `main_chat`
      gespawnte", sondern die Einstiegs-Formulierung, und die Zeile
      „NIEMALS `task(subagent_type=\"orchestrator\")`" bleibt vorhanden.
- [ ] **AC-20 (G5)** — **Given** eine provider-eigene, nicht geteilte Kontextdatei, **when** der
      Einstiegshinweis gerendert wird, **then** lautet er bei `primary` „startet im
      `orchestrator`", bei `subagent` **unverändert** „Starte mit dem `orchestrator`-Agenten …"
      (`agents.py:174`), bei `main-chat` unverändert. **Given** eine **geteilte** Datei mit
      **unterschiedlicher** Effektivposition der Sharer (z. B. Opencode `primary` + Gemini
      `subagent`), **then** rendert sie den neutralen Text aus §5-G5 und **keine**
      positionsspezifische Aussage; Assertion auf den tatsächlich gerenderten Text, nicht auf die
      Flag-Werte; zwei Läufe mit vertauschter Provider-Reihenfolge sind identisch (Rev. 3 /
      RVW2-1190-02). **Given** eine geteilte Datei, deren Sharer **alle** dieselbe Position haben,
      **then** rendert genau dieser Positions-Text (kein Positionsverlust).
- [ ] **AC-21 (G6)** — Ein Test belegt: `resolve_topology(config, p, mode="strict"|"advisory"|
      "main-chat", …)` liefert dreimal denselben `effective`-Wert. Ablage der neuen Checks
      (Rev. 2 / R-04): **zwei** in `consistency/topology.py`
      (`main-chat-derived-primary`, `strict-primary-entry-mismatch`), **einer** in
      `consistency/orchestrator_strict.py` (`direct-dispatch-inert`); ein Test schlägt fehl, wenn
      eine ID in der jeweils anderen Datei liegt.
- [ ] **AC-22 (G7)** — **Given** v2 + `strict` + `topology: subagent`, **when** der Reconcile
      läuft, **then** enthält `opencode.json` **keine** `permissions[]`-Tripel und es entsteht
      **genau eine Log-Warnung** im Sync-Kanal mit den in §6.4 gepinnten Teilstrings
      (`opencode-v2 gate (permissions deny) NOT written for provider` **und** `effective
      orchestrator topology is 'subagent'`); **kein** Consistency-Finding (v2 ist Tier `plugin`,
      `_gate_wanted` ist `permission`-gebunden), **weder** der Text „default_agent is missing"
      **noch** die Handlungsanweisung „Set `default_agent` to 'orchestrator'". **Given** v1 +
      derselbe Zustand, **then** gilt die Zählregel aus §6.4: eine Log-Warnung **und** ein Finding,
      je Kanal genau eine.
- [ ] **AC-23 (G7)** — Alle **drei** Aufrufstellen von `_opencode_entry_point` in
      `scripts/lib/isolation.py` (`:869`, `:1457`, `:1827`) übergeben `topology=`; an `:869` darf
      der Wert `None` sein, wenn `rollback_only` gilt oder `config is None` ist. Zusätzlich
      übergeben beide Aufrufer von `reconcile_opencode_surface_gate`
      (`sync_pipeline.py:1598-1602`, `cli_commands.py:344-348`) das Keyword `topology=`
      (Durchreichung, keine Neuresolution). Prüfmethode (Rev. 3 / RVW2-1190-13): (a) AST-Test mit
      **erwarteter Trefferzahl** — genau **3** `Call`-Knoten von `_opencode_entry_point` tragen
      das Keyword `topology`, genau **2** `Call`-Knoten von `reconcile_opencode_surface_gate`
      tragen es; (b) Fixture-Test mit Monkeypatch-Zähler: ein Reconcile-Lauf ruft
      `_opencode_entry_point` genau einmal und `_opencode_v2_gate_permissions` genau einmal auf,
      und beide Aufrufe tragen `topology` mit demselben Objekt (Identität, nicht nur Gleichheit).
- [ ] **AC-24 (G8)** — Die Testliste aus G8 existiert und deckt: Nicht-Opencode-Emission
      (Claude/Gemini), v2-Reconcile unter `subagent`, abgeleitetes `primary` vs.
      `ORCH_TOPOLOGY_*`, `use-orchestrator`-Rendering unter `primary`/`subagent`, Singleton-Block,
      `ROLE_ORCHESTRATOR_ACTIVE` unter `main-chat` (Test namentlich in T10,
      `test_role_orchestrator_active_under_main_chat_prose` in
      `tests/test_entry_hint_topology.py`), alle drei neuen Check-IDs und den Zwei-Sharer-Fall
      (AC-20). Konkrete Assertion für den Prosa-Test (Rev. 3 / RVW2-1190-13): bei
      `mode: main-chat` ist `variables["ROLE_ORCHESTRATOR_ACTIVE"] == "false"`, und die gerenderte
      `a2a-delegation-gates`-Zeile lautet `Worker → HARD REJECT` (Golden-Fixture
      `tests/fixtures/topology-golden/a2a-delegation-gates.role-inactive.md`) — **nicht** die
      Variante mit ``Worker`` → `orchestrator` → HARD REJECT.
- [ ] **AC-25 (G9)** — Die elf Doku-Befunde aus §9.1 sind einzeln abgearbeitet; ein Doku-Test
      schlägt fehl, solange eine absolute Aussage außerhalb eines topologie-qualifizierten
      Kontexts steht. Scope und Prüfmethode (Rev. 3 / RVW2-1190-13): geprüft werden **genau** die
      elf Belegstellen aus §9.1 (B-1…B-11, je `datei`), **nicht** die Spec, das Review oder dieser
      Plan. Verboten sind die Literale „nur der `main_chat` spawnt", „NUR `main_chat` darf",
      „Only `main_chat` may create you", „der vom `main_chat` gespawnte" und „one per session,
      spawned by the main chat"; Ausnahme: steht `topology`, `subagent` oder `primary` im **selben
      Absatz**, gilt die Stelle als qualifiziert. Zulässige, ausdrücklich erlaubte Fundstellen
      außerhalb des Scopes: `docs/specs/2026-11-09-orchestrator-mode-topology-design.md` (§6.5,
      §12.4 — Negativbeispiel), `docs/reviews/*` (historisches Protokoll).

### Querschnitt

- [ ] **AC-26** — `config/project-config.schema.json` enthält **keine** neuen Properties
      (Diff-Assertion gegen den Stand vor der Umsetzung); nur `description`-Texte dürfen sich
      ändern.
- [ ] **AC-27** — `sync --check` bleibt auf einem Consumer byte-identisch, dessen `topology`-Key
      ungesetzt ist **und** dessen aktive Provider **alle** `effective == "subagent"` auflösen
      (Fortschreibung von AC-6 der Vorgänger-Spec); `--validate` bleibt rc 0. Zwei Fälle ändern
      sich **beabsichtigt** und erhalten je eine eigene Golden-Fixture statt einer
      Byte-Identitäts-Zusage: (a) **abgeleitetes** `primary` (Key ungesetzt, AC-17) und (b)
      **deklariertes** `topology: primary` (`EFFECTIVE_PRIMARY`-Zweig ersetzt den expliziten
      Zweig) (Rev. 3 / RVW2-1190-01).
- [ ] **AC-28** — Die bindenden Entscheidungen D-Q1…D-Q5 **und** D-OQ1…D-OQ3 liegen als ADR vor
      (MADR-minimal, `se-cascade-adr-standard`-Format) und
      `docs/concepts/active/orchestrator-topology.md` enthält die 24-Zellen-Matrix plus Empfehlung.
- [ ] **AC-29 (G8/T17)** — Die Szenarien sind auf das Positionsmodell ausgerichtet
      (`DECIDED 2026-11-09`, D-OQ1): `100` = `strict × subagent` (neuer Default, POS-2, Opencode v2),
      `101` = `strict × primary` (POS-3, Opencode v2), `102` = `main-chat` (POS-1),
      `104` = Claude `strict × subagent`. Diese vier liegen unter dem `10*`-Match von
      `tests/scenarios/run.sh` und liefern je `PASS`. Szenario `103` = `advisory × subagent` ist
      wegen #1182 **nicht** ausführbar, wird unter einem Namen **außerhalb** `10*` geführt
      (`blocked-103-advisory-subagent.project.yaml`) und im Katalog als `BLOCKED (#1182)`
      ausgewiesen. `run.sh` kennt **kein** `SKIP` (`run.sh:231`), eine Skip-Konvention wird nicht
      eingeführt.
- [ ] **AC-30 (G3/R-07)** — Emission und alle drei Render-Seams (Rules, Context,
      Agent-Templates) benutzen **denselben** per-Sync-`ActiveSet`: `_provider_topology_flags`
      hat `active_set` als Pflicht-Keyword; `sync_context_for_provider` und
      `_sync_stage_contexts` erhalten ihn ebenfalls als Pflicht-Keyword (kein Default), Aufrufer
      ist `cli_commands.py:1543` mit `ctx.active_set` (`:964`). Ein Test mit zwei Providern und
      einer Rolle **nicht** im `ActiveSet` liefert an allen vier Seams `effective == "subagent"`
      (kein Seam fällt auf die leere Menge zurück). **Zusatz-Ratchet (Rev. 3 / RVW2-1190-09):**
      kein Render-Seam konsumiert die **provider-lose** Basis — ein AST-/Grep-Test schlägt fehl,
      sobald `ORCH_TOPOLOGY_EFFECTIVE*` außerhalb der Provider-Variablen (d. h. außerhalb der
      Rückgabe von `_provider_topology_flags` und des als nicht autoritativ markierten
      `_build_orch_variables`-Blocks) gelesen wird.
- [ ] **AC-31 (R-06)** — Nach jeder emissionsrelevanten Task-Gruppe (T4–T10, T14, T19, T20) wird
      `python3 scripts/sync.py` ausgeführt, das Diff der regenerierten Artefakte geprüft und
      committet; `python3 scripts/sync.py --check` ist danach rc 0. Die `--check`-Gates von
      M1/M3/M10 und T21 sind erst nach dieser Regeneration einfahrbar.

### Positionsmodell (`DECIDED 2026-11-09`)

- [ ] **AC-32 (D-OQ1, POS-Doku)** — Diese Spec enthält in §3.8 **drei** Positionen (`POS-1`,
      `POS-2`, `POS-3`) mit je **sieben** Feldern (wer startet, wer spawnt, Rolle emittiert,
      `default_agent`, Gate-Tier/Wirkung, A2A/Checkpointing, Hops) **und** die Mapping-Tabelle
      `mode` × `topology` → Position mit **zehn** Zeilen.
      `docs/concepts/active/orchestrator-topology.md` trägt dieselben zwei Tabellen; ein Doku-Test
      parst **dort** beide: jede Zeile hat eine Positionsangabe aus
      `{POS-1, POS-2, POS-3, keine Position}`, keine Zelle ist leer, und jede verwendete
      Positions-ID ist in der Concept-Doc **vor** der Matrix definiert. `README.md` und
      `docs/CODEBASE_OVERVIEW.md` erklären die **zwei** Opencode-Positionen (POS-1 und POS-2)
      ausdrücklich.
- [ ] **AC-33 (D-OQ2, POS-Parität)** — **Given** die beiden first-class Opencode-Positionen, **when**
      `tests/test_opencode_positions.py` läuft, **then** existiert **je ein** Test pro Position —
      `test_opencode_main_chat_position_generates_clean` (POS-1) und
      `test_opencode_subagent_position_generates_clean` (POS-2) — plus der Regressionstest
      `test_opencode_primary_position_generates_clean` (POS-3). Kein Test darf beide Positionen in
      einem Fall zusammenfassen; jede Position wird für `surface-version: v1` **und** `v2` geprüft.
- [ ] **AC-34 (D-OQ2, POS-1)** — **Given** `mode: main-chat` auf OpenCode, **when** der Sync läuft,
      **then** enthält `opencode.json` **keinen** von der Sync geschriebenen `default_agent`, es
      existiert **keine** generierte `orchestrator`-Agent-Datei, es werden **keine**
      `permissions[]`-Tripel geschrieben, ein **verwalteter** Alt-Wert wird per State-Rollback
      zurückgenommen, und ein **nutzereigener** Wert bleibt unangetastet mit **genau einer**
      `opencode.default-agent.dangling`-Warnung (`scripts/lib/isolation.py:910-924`).
- [ ] **AC-35 (D-OQ2, POS-2)** — **Given** `topology: subagent` auf OpenCode, **when** der Sync läuft,
      **then** trägt die generierte `orchestrator`-Datei `mode: subagent` und **nicht**
      `mode: primary`, `opencode.json` trägt **keinen** `default_agent`, und die Gate-Suspendierung
      wird **ehrlich** gemeldet: v1 genau eine `orchestrator-topology.gate-inactive`-Meldung
      (Log + Finding je Kanal genau eine, §6.4), v2 genau die ursachenbewusste Log-Warnung aus G7 und
      **kein** `permissions[]`-Deny.
- [ ] **AC-36 (D-OQ1, declared = deterministisch)** — **Given** ein explizit deklariertes
      `orchestrator.topology: subagent` (`mode: strict`), **when** derselbe Provider zweimal gerendert
      wird, **then** sind die Artefakte byte-identisch (kein Oszillieren, unabhängig von der
      Provider-Reihenfolge), es gilt `ORCH_TOPOLOGY == "subagent"`,
      `ORCH_TOPOLOGY_EFFECTIVE_SOURCE == "project"`, `ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT == "true"`, und
      die Ausgabe unterscheidet sich von `ungesetzt ∧ abgeleitetem subagent`
      (`ORCH_TOPOLOGY == ""`, `_EFFECTIVE_EXPLICIT == "false"`) **genau** im expliziten Zweig der
      Templates — belegt durch zwei Golden-Fixtures (declared/derived).
- [ ] **AC-37 (D-OQ3, #1182-Bedingung)** — **Given** die Matrixzeile `advisory × subagent`, **when**
      der Doku-Test läuft, **then** trägt sie die Bedingung „setzt #1182 voraus (compact-Profil)"
      wörtlich, im Szenario-Katalog steht `103` als `BLOCKED (#1182)`, und `README.md` sowie
      `docs/concepts/active/orchestrator-topology.md` nennen die Bedingung an derselben Stelle wie die
      Empfehlung. **Keine** Dokustelle empfiehlt `advisory × subagent` ohne diesen Zusatz.

---

## 9. Befunde und Risiken

### 9.1 Die elf Doku-Befunde (Lücke 9, einzeln)

| # | Befund | Beleg | Auflösung |
|---|---|---|---|
| B-1 | Singleton absolut: „der vom `main_chat` gespawnte" | `CLAUDE.md:102` | topologie-qualifizieren (G4-Text) |
| B-2 | Mermaid: „orchestrator: one per session, spawned by the main chat" für `strict or advisory` | `README.md:415` | zwei Knoten (`primary` = entry, `subagent` = spawned) |
| B-3 | Key-Tabelle nennt nur `orchestrator.mode`, kein `orchestrator.topology` | `README.md:210` | Zeile ergänzen (Auffindbarkeit) |
| B-4 | „NUR der `main_chat` darf den `orchestrator` spawnen" | `docs/CODEBASE_OVERVIEW.md:1726` | Qualifizierung + Verweis |
| B-5 | else-Zweig „Only `main_chat` may create you" bei abgeleitetem `primary` | `agents/1-generic/orchestrator.md:19` | G2/G3: auf `EFFECTIVE` umstellen |
| B-6 | else-Zweig „NUR `main_chat` darf … spawnen" bei abgeleitetem `primary` | `rules/1-generic/a2a-delegation-gates.md:17-19` | G2: auf `EFFECTIVE` umstellen |
| B-7 | Widerspruch „P3, shipped" vs. „P3, designed, not shipped" | `docs/concepts/active/orchestrator-topology.md:91` vs. `docs/specs/2026-11-04-orchestrator-topology-spec.md:791-792` | **Entschieden (Rev. 3 / RVW2-1190-08): „shipped" gilt** — der Vertrag ist implementiert und validiert (AC-8…AC-12), der Doku-Test (`test_p3_status_is_single_valued`, T16) pinnt die eine Aussage. Die Vorgänger-Spec-Zeile `:791-792` ist damit **überholt** und wird hier als solche ausgewiesen, nicht editiert (D1–D10 bleiben unangetastet) |
| B-8 | Gegenläufiger Marker in der Singleton-Concept | `docs/concepts/active/singleton-orchestrator-architecture.md:13` | auf denselben Stand wie B-7 |
| B-9 | Widersprüchlicher Render **innerhalb einer Datei**: Zeile 1 `# CRITICAL GATE` ohne Tier-Suffix, Zeile 2 der unqualifizierte Satz, Zeilen 3-4 der PARTIAL-Absatz — zwei Gate-Varianten, kein gemeinsamer Tier-Text | `.claude/rules/use-orchestrator.md:1-4` | auf **eine** Gate-Variante zurückführen (Tier-Text bleibt); Ursache ist ein doppelter `GATE_*`-Treffer im Render, kein zweiter Wortlaut-Vertrag |
| B-10 | „Singleton-Guard-Hook entfällt oder wird deaktiviert, da es keinen Orchestrator gibt" vs. Statuszeile „Hook-Deaktivierung bleibt offenes Follow-up" | `docs/concepts/active/main-chat-orchestrator-mode.md:109` vs. `:178` | offenen Punkt explizit als offen markieren |
| B-11 | Die Interaktionsmatrix deckt nur **deklarierte** Topologie; der abgeleitete Fall fehlt | `docs/concepts/active/orchestrator-topology.md:75-79` | Derived-Zeile ergänzen (D-Q1) |

### 9.2 Risiken

| # | Risiko | Wirkung | Gegenmaßnahme |
|---|---|---|---|
| R-1 | **Warnungs-Flut**: neue WARNINGs auf jedem Bestandsprojekt | Nutzer ignoriert Checks | Jede neue Bedingung ist an eine *Präsenz* oder einen *Widerspruch* gebunden (D-Q1 nur bei abgeleitetem `primary` + `main-chat`; D-Q5 nur bei `mode: main-chat` **und** präsentem Key); Dedup je Check-ID und Lauf. |
| R-2 | **Byte-Identität bricht** durch neue Conditional-Flags | `sync --check`-Drift auf allen Consumern | Fail-closed-Registrierung in vier Stellen + Golden-Fixtures (AC-15/AC-16); der Default-Render (`ungesetzt ∧ effective == "subagent"`) muss der heutige sein, abgeleitetes `primary` ist beabsichtigt (AC-17). |
| R-3 | **Vierter Resolver**: Topologie wird an einer vierten Stelle neu gerechnet (G3) und driftet | Emission und Rendering widersprechen sich erneut | Kein neuer Resolver: ausschließlich `resolve_topology(...)` wiederverwenden, Auflösung je Provider genau einmal pro Lauf (Muster `isolation.py:821-856`). |
| R-4 | **Cross-Issue-Kollision** (§11) | Merge-Konflikte, halb gefixte Zustände | Serialisierung der Berührungsflächen (§11-Tabelle). |
| R-5 | **Matrix wird als Capability-Freigabe gelesen** | jemand erklärt Gemini-`primary` für unterstützt | Matrix ist Empfehlung; Capability-Zellen bleiben `UNVERIFIED ⇒ no` (AC-9 pinnt die Degradierung). |
| R-6 | **Der Fix ist unsichtbar, solange dieses Repo die Position nur ableitet** | Lücken 2/4/5 bleiben im Alltag sichtbar; „derived vs. declared" bleibt die Divergenzursache | **`DECIDED 2026-11-09` (D-OQ1):** explizite Deklaration `orchestrator.topology: subagent` — Plan-Task T20, **nach** dem Code-Fix, mit Rollback (nicht Teil dieser Spec). |
| R-7 | **`strict` + `subagent` wird als „auch strict" missverstanden** | Zusage wird überschätzt | D-Q2-Tabelle + `gate-inactive`-WARN bleiben Pflicht; Doku sagt „prompt-basiert". Die Matrix nennt je Surface den **tatsächlich** greifenden Tier (§6.5, D-OQ2). |
| R-8 | **Positions-Doku driftet auseinander**: Matrix, §3.8-Mapping und Doku nennen unterschiedliche Positionen | Nutzer wählt eine Position, die die Doku anders beschreibt | Ein Doku-Test pinnt beide Tabellen (AC-32); Doku-Folgen in README/CODEBASE_OVERVIEW/Concept sind ein eigener Plan-Task (T18). |
| R-9 | **`advisory × subagent` wird als freigegeben gelesen** | Team stellt auf eine Kombination um, die an #1182 bricht | Bedingung steht an jeder Empfehlungsstelle (AC-37); Szenario `103` bleibt `BLOCKED`. |

---

## Offene Fragen (§9.3)

> **`DECIDED 2026-11-09`:** Die drei User-Entscheidungen (D-OQ1, D-OQ2, D-OQ3) beantworten OQ-1, OQ-2
> und OQ-4. Offen bleibt allein die externe Terminierung von #1182 (kein Entscheid, den dieses
> Vorhaben treffen kann).

| # | Frage | Warum offen | Vorschlag | Status |
|---|---|---|---|---|
| OQ-1 | Soll dieses Repo `orchestrator.topology` **explizit** deklarieren — und mit welchem Wert? | Config-Änderung ist per #1190 §6 ausgeschlossen; es ist eine Projektentscheidung | **Ja, `subagent`** — löst B-5/B-6/B-11, beseitigt die derived-vs-declared-Divergenz und macht D-Q1 hier gegenstandslos | **`DECIDED 2026-11-09` (D-OQ1)** — Umsetzung Plan-Task T20, **nach** dem Code-Fix |
| OQ-2 | Soll `strict × subagent` eine dokumentierte Zelle bleiben (oder als „nicht empfohlen, Gate suspendiert" markiert)? | Zusage-Frage, keine Mechanik-Frage | Als `ALLOWED`/`RECOMMENDED` führen, nicht verbieten | **`DECIDED 2026-11-09` (D-OQ2)** — bleibt erlaubt **und** empfohlen; je Surface wird der tatsächlich greifende Tier ausgewiesen |
| OQ-3 | Sollen die neuen Check-IDs den `orchestrator-topology.`-Namespace teilen oder einen eigenen (`orchestrator-mode.`) bekommen? | Namensraum-Konsistenz vs. Auffindbarkeit | `orchestrator-topology.` für Positionsbefunde, `orchestrator-strict.` für Gate-Befunde (wie D-Q5) | entschieden (§6.2), unverändert gültig |
| OQ-4 | Wird #1182 vor der Team-Empfehlung (`advisory × subagent`) gefixt? | Externer Blocker | Empfehlung mit Blocker-Hinweis ausliefern | **`DECIDED 2026-11-09` (D-OQ3)** — Empfehlung erst **nach** #1182; bis dahin `strict × subagent` |
| OQ-5 | Soll die Matrix auch in `README.md` (extern, Englisch) erscheinen? | Sprache: interne Doku Deutsch, externe Englisch | Ja, Kurzfassung; volle Matrix im Concept-Doc | Ja — Kurzfassung inkl. **beider** Opencode-Positionen (Plan-Task T18) |

---

## 10. Backlog- und Issue-Bezug

| Issue | Status | Bezug |
|---|---|---|
| **#1190** | offen (dieses Dokument) | Haupt-Issue: Q1–Q5, Matrix, Empfehlungen |
| **#1077** | closed | Mechanismus (`orchestrator.topology`, D1–D10). **Nicht** neu aufgerollt; die Spec von 2026-11-04 bleibt normativ. |
| **#1182** | offen | Blockiert `advisory` + `context-profile: compact` → blockiert die Team-Empfehlung (§4-D-Q3). |
| **#1007** | offen | V2-Surface-Matrix; unsere v2-Empfehlung stützt sich auf `runtime-gate-tiers.md`, nicht auf #1007-Ergebnisse. |
| **#1090** | closed | Dangling `default_agent` in `main-chat`; liefert das Prädikat `role_emitted_for_provider`. Unsere D-Q1-Diagnose ist die **Rückrichtung** davon. |
| **#794** | closed | Main-Chat-Mutationen ohne Gate auf OpenCode (kein Runtime-Gate) — Motiv für die ehrliche Tier-Zusage in D-Q3. |
| **#683** | closed | `strict` blockierte delegierte Implementer; Motiv für „Nutzungsfehler statt Config-Fehler" (D-Q2) und für die Topologie-Vorbedingung im Gate. |
| **#1210** | offen | Guard kann einen Sentinel keiner Rolle zuordnen — begrenzt, wie stark D-Q2 (c) überhaupt erzwungen werden kann; keine Abhängigkeit, aber derselbe Ehrlichkeits-Maßstab. |
| **#1187** | offen | Projekt-Kontext-Injektion; berührt `agents/1-generic/*.md` und `variables.py` (§11). |
| **#1006** | closed | Entry-Point-Invariante (`primary-role` ⇒ `mode: primary` + `default_agent`); G7 ist die Topologie-Erweiterung dieser Invariante. |
| **#885** | — | Framework-Conformity-Audit (Kontext für die Doku-Befunde). |

---

## 11. Cross-Vorhaben-Konfliktflächen

| Datei | Dieses Vorhaben | Kollidiert mit | Serialisierung |
|---|---|---|---|
| `config/project-config.schema.json` | keine neuen Properties, ggf. `description` (AC-26) | **#1186** (artifact-locations), **#1188** (issue-label-taxonomy) — beide legen neue Schema-Blöcke an | Dieses Vorhaben **zuletzt** und **text-only**; Schema-Diff muss leer sein |
| `scripts/lib/config.py` | keine Validator-Änderung geplant; ggf. nur Verweis | **#1186** (Validierung neuer Blöcke) | Nicht parallel schneiden; dieses Vorhaben fügt dort nichts hinzu |
| `scripts/lib/variables.py` | sieben neue `ORCH_TOPOLOGY_EFFECTIVE*`/`_INERT`-Flags (G2) | **#1209** (Artifact-Mode-Gating), **#1187** (Context-Injection-Scope) — beide fassen `_build_variables` an | Reihenfolge: #1187/#1209 zuerst, dann G2 (Flag-Registrierung ist additiv, aber die Datei ist heiß) |
| `scripts/lib/agent_sync.py` | G3 (provider-scoped Topologie), G4 (Singleton-Block) | **#1181** (Commit-Authority für Edit-only-Rollen; Body nennt nur `agents/1-generic/documenter.md`, der Commit-Authority-Seam liegt aber plausibel hier — **im Body nicht belegt**) | Getrennte Commits; G3/G4 berühren `_build_provider_vars`/`_finalize_agent_content`, #1181 eher den Commit-Block |
| `agents/1-generic/orchestrator.md` | G2-Verzweigung (`EFFECTIVE_EXPLICIT`) | **#1187** (Projekt-Kontext in 70 Templates), **#1209** (Output-Pfad-Gating) | `orchestrator.md` ist in allen drei Vorhaben betroffen → **eine** Datei, drei Themen: Serialisierung Pflicht |
| `rules/1-generic/use-orchestrator.md` | G1 (Gate-Vorbedingung) | **#1182** (compact/Gate-Card-Sektionen: `CRITICAL GATE` muss als Sektion erhalten bleiben) | G1 darf die Sektion `CRITICAL GATE` **nicht** umbenennen, sonst bricht der Compact-Pfad zusätzlich |
| `scripts/lib/isolation.py` | G7: Signatur `reconcile_opencode_surface_gate(..., topology=None)` + zwei Durchreichungen; **plus** die zwei Aufrufer `sync_pipeline.py:1598-1602`, `cli_commands.py:344-348` | **#1007** (v2-Surface) | G7 ist klein und lokal; vor #1007-Änderungen an denselben Funktionen landen |
| `scripts/lib/sync_pipeline.py` | G7-Aufrufer (`topology=` an den Reconcile), G3-Override-Zweig (`:1405-1431`), per-Provider-`ActiveSet`-Durchreichung | **#1181**, **#1209** | Getrennte Commits; Reconcile-Aufruf und Render-Seams im selben Commit wie die Signatur |
| `scripts/lib/cli_commands.py` | G7-Aufrufer im `--test-generated`-Pfad | — | folgt `sync_pipeline.py` im selben Commit |
| `scripts/lib/consistency/topology.py` | drei neue Check-IDs | — | unkritisch, aber Check-ID-Registry (`consistency-check`) mitpflegen |

---

## 12. Herleitung der Matrix (Q3)

### 12.1 Lesart

- **Urteil:** `RECOMMENDED` (eine pro Surface) · `ALLOWED` (funktioniert, mit benannten Kosten) ·
  `DEGRADED` (deklariert, aber effektiv `subagent`) · `FORBIDDEN` (Validator-ERROR oder
  strukturell unausführbar).
- **Spalte `Position`:** die Session-Form aus §3.8.2 — `POS-1` (Main-Chat-als-Orchestrator),
  `POS-2` (Delegierter Orchestrator), `POS-3` (Session-Einstieg). `main-chat` ist immer `POS-1`.
- **Spalte `topology`:** deklariert → effektiv. `hybrid` ist in allen Zellen `UNVERIFIED ⇒
  subagent` (`config/provider-capabilities.yaml:209`, `docs/concepts/active/orchestrator-topology.md:30-34`)
  und wird deshalb nicht als eigene Zeile geführt (kein Neuaufrollen von #1077).
- **Hop:** `POS-1` = 0, `POS-2` = 1, `POS-3` = 0 (§4-D-Q4).
- Jede Begründung nennt die tragende Code-Stelle; Capability-Zellen sind Daten, keine Meinung.

### 12.2 OpenCode v1 (`surface-version: v1`, Tier `permission` PARTIAL)

| mode | topology (decl→eff) | Position | Urteil | Gate-Tier | Write-Scope-Lock | Recursion | Hop | A2A / Checkpoint |
|---|---|---|---|---|---|---|---|---|
| `strict` | `primary`→`primary` | POS-3 | ALLOWED (optional, 0 Hop) | `permission` (PARTIAL, `runtime-gate-tiers.md:38`) | aktiv (`provider_transform.py:529-531`) | `subagent_depth` nur bei `inject-subagent-depth`; Plattform-Limit | 0 | `a2a-v1` + `.meta-viz` Checkpoints aktiv |
| `strict` | `subagent`→`subagent` | POS-2 | **RECOMMENDED** (Default, D-OQ1) | Gate suspendiert, `gate-inactive`-WARN (`isolation.py:932-962`) | **nicht** gesetzt | dito, +1 Ebene | 1 | dito |
| `advisory` | `primary`→`primary` | POS-3 | ALLOWED | `permission` | aktiv | dito | 0 | dito |
| `advisory` | `subagent`→`subagent` | POS-2 | ALLOWED (Team-Empfehlung, **setzt #1182 voraus**) | Gate suspendiert | nicht gesetzt | dito | 1 | dito |
| `main-chat` | `primary`→`primary` | POS-1 (keine Rolle) | **FORBIDDEN** (declared) / WARN (derived, D-Q1) | keiner (Rolle fehlt) | entfällt | entfällt | 0 | kein Orchestrator-State |
| `main-chat` | `subagent`→`subagent` | POS-1 | ALLOWED nur **cross-scope** (inert + `main-chat-supersedes`, `topology.py`-Spec AC-7) | keiner | entfällt | entfällt | 0 | dito |

### 12.3 OpenCode v2 (`surface-version: v2`, Tier `plugin` observe + `permissions[]`-Deny)

| mode | topology (decl→eff) | Position | Urteil | Gate-Tier | Write-Scope-Lock | Recursion | Hop | A2A / Checkpoint |
|---|---|---|---|---|---|---|---|---|
| `strict` | `primary`→`primary` | POS-3 | ALLOWED (optional) | `plugin` observe, Deny tragend (`runtime-gate-tiers.md:50-53`) | aktiv | `subagent_depth` (Capability `required_depth: 2`, `provider-capabilities.yaml:211`) | 0 | dito |
| `strict` | `subagent`→`subagent` | POS-2 | **RECOMMENDED** (Default, D-OQ1) — **erst nach G7** | Gate suspendiert (`gate-inactive`), kein Deny | nicht gesetzt | dito | 1 | dito |
| `advisory` | `primary`→`primary` | POS-3 | ALLOWED | `plugin` + Deny | aktiv | dito | 0 | dito |
| `advisory` | `subagent`→`subagent` | POS-2 | ALLOWED (Team-Empfehlung, **setzt #1182 voraus**) | Gate suspendiert | nicht gesetzt | dito | 1 | dito |
| `main-chat` | `primary`→`primary` | POS-1 (keine Rolle) | **FORBIDDEN**/WARN (D-Q1) | keiner | entfällt | entfällt | 0 | kein Orchestrator-State |
| `main-chat` | `subagent`→`subagent` | POS-1 | ALLOWED nur cross-scope (inert + WARN) | keiner | entfällt | entfällt | 0 | dito |

> **v2-Pin:** Nicht-`primary`-Rollen werden hart auf `mode: subagent` gesetzt
> (`provider_transform.py:498-499`). Genau deshalb ist `subagent` auf v2 **technisch** sauber —
> und genau deshalb ist der topology-blinde Reconcile (G7) der einzige verbleibende Defekt.

> **Bedingung (`DECIDED 2026-11-09`, D-OQ3).** `advisory × subagent` ist die Team-Empfehlung, aber
> **erst nach dem Fix von #1182** (`context-profile: compact` bricht für `advisory` ab). Bis dahin ist
> `strict × subagent` die belastbare Team-Empfehlung; Szenario `103` bleibt `BLOCKED (#1182)`.

### 12.4 Claude (Tier `hook`, kein `primary-role`)

| mode | topology (decl→eff) | Position | Urteil | Gate-Tier | Write-Scope-Lock | Recursion | Hop | A2A / Checkpoint |
|---|---|---|---|---|---|---|---|---|
| `strict` | ungesetzt→`subagent` | POS-2 | **RECOMMENDED** | `hook` (voll, `runtime-gate-tiers.md:36`) | entfällt (kein `mode: primary`-Konzept) | Subagent-Nesting-Limit der Plattform (`a2a-delegation-gates.md:30-32`) | 1 | `a2a-v1`/Checkpoints provider-gestützt |
| `strict` | `primary`→`primary` | POS-3 | ALLOWED (nur explizit deklariert) | `hook` | Guard-Hook statt Agent-Frontmatter-Deny | dito | 0 | dito |
| `advisory` | `primary`→`primary` | POS-3 | ALLOWED | `hook` | Guard-Hook | dito | 0 | dito |
| `advisory` | `subagent`→`subagent` | POS-2 | ALLOWED (Team-Empfehlung, **setzt #1182 voraus**) | `hook` | entfällt | dito | 1 | dito |
| `main-chat` | `primary`→`primary` | POS-1 (keine Rolle) | **FORBIDDEN** (declared) / WARN (derived, D-Q1) | keiner (Rolle fehlt) | entfällt | entfällt | 0 | kein Orchestrator-State |
| `main-chat` | `subagent`→`subagent` | POS-1 | ALLOWED nur cross-scope (inert + WARN) | keiner | entfällt | entfällt | 0 | dito |

> **Caveat `strict × primary` (Rev. 2 / R-02):** „Hop 0" gilt **nur**, wenn die Session tatsächlich
> im `orchestrator` startet. Claude hat kein `mode: primary`-Konzept und
> `main_agent_selectable: true` (`provider-capabilities.yaml:144`): eine Main-Chat-Session **darf**
> den Orchestrator spawnen (das ist der legale Kanal, `hook`-Tier), kostet dann aber 1 Hop. Die
> Regel „kein Spawn-Kanal" aus Rev. 1 ist hier deshalb **falsch** und in G1 ersatzlos gestrichen.

### 12.5 Gemini / Antigravity (Tier `hook`, `primary` nicht unterstützt)

| mode | topology (decl→eff) | Position | Urteil | Gate-Tier | Write-Scope-Lock | Recursion | Hop | A2A / Checkpoint |
|---|---|---|---|---|---|---|---|---|
| `strict` | `primary`→**`subagent`** | POS-2 (degradiert) | DEGRADED (+ `orchestrator-topology.degraded`) | `hook` | nicht gesetzt | Roster / Plattform-Limit | 1 | dito |
| `strict` | `subagent`→`subagent` | POS-2 | **RECOMMENDED** | `hook` | nicht gesetzt | dito | 1 | dito |
| `advisory` | `primary`→`subagent` | POS-2 (degradiert) | DEGRADED (WARN) | `hook` | nicht gesetzt | dito | 1 | dito |
| `advisory` | `subagent`→`subagent` | POS-2 | ALLOWED (Team-Empfehlung, **setzt #1182 voraus**) | `hook` | nicht gesetzt | dito | 1 | dito |
| `main-chat` | `primary`→`subagent` | POS-1 (keine Rolle) | **FORBIDDEN** (declared) / WARN (derived) | keiner (Rolle fehlt) | entfällt | entfällt | 0 | kein Orchestrator-State |
| `main-chat` | `subagent`→`subagent` | POS-1 | ALLOWED nur cross-scope (inert + WARN) | keiner | entfällt | entfällt | 0 | dito |

### 12.6 Evidenz-Index

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

---

## Trace-Anker (§13)

- **spec-id:** `SPEC-orchestrator-mode-topology-2026-11-09` (vom Plan unverändert zu übernehmen).
- **Issue:** #1190.
- **Normative Vorgänger:** `SPEC-orchestrator-topology-2026-11-03`
  (`docs/specs/2026-11-04-orchestrator-topology-spec.md`, D1–D10, AC-1…AC-20).
- **Design-Quelle:** `docs/specs/2026-11-03-orchestrator-topology-design.md` (Rev. 4).
- **Lücken → G:** L1→G1, L2→G2, L3→G3, L4→G4, L5→G5, L6→G6, L7→G7, L8→G8, L9→G9.
- **Q → AC:** Q1→AC-1, AC-2 · Q2→AC-3, AC-4, AC-5 · Q3→AC-6…AC-9 · Q4→AC-10, AC-11 ·
  Q5→AC-12, AC-13 · G1–G9→AC-14…AC-25 · Querschnitt→AC-26…AC-28 · Szenarien→AC-29 ·
  ActiveSet-Parität→AC-30 · Regeneration→AC-31 · Positionsmodell (`DECIDED 2026-11-09`)→AC-32…AC-37.
- **D-OQ → AC (`DECIDED 2026-11-09`):** D-OQ1 (Default `strict × subagent`, beide
  Opencode-Positionen first-class, explizite Deklaration) → **AC-7, AC-11, AC-32, AC-36** ·
  D-OQ2 (`strict × subagent` erlaubt und empfohlen, Gate-Tier je Surface, saubere Generierung je
  Position) → **AC-8, AC-33, AC-34, AC-35** · D-OQ3 (`advisory × subagent` erst nach #1182) →
  **AC-29, AC-37**. D-Q1/D-Q3/D-Q4 sind entsprechend nachgeführt (§4).
- **H-Map (Rev. 2 / R-19):** Der Issue-Body #1190 lag in Review 1 nicht vor; H1–H3 sind deshalb nur
  gegen diese Spec prüfbar (§12-Einschränkung). Zuordnung:

  | Hypothese | Beantwortet durch | Urteil |
  |---|---|---|
  | H1 („`mode` und `topology` werden an den Render-Seams widersprüchlich aufgelöst") | §3.2, §4-D-Q1, G2/G3, AC-16/AC-17/AC-18/AC-30 | **bestätigt** (Ist-Zustand belegt: Emission `effective`, Rendering `declared`) |
  | H2 („`main-chat` + `primary` ist der unausführbare Zustand") | §4-D-Q2, D-Q1, G1, AC-1/AC-3/AC-4 | **teilweise bestätigt** — unausführbar nur für die Session-Form, nicht für die Config; deshalb WARNING + Nutzungsfehler statt ERROR |
  | H3 („v2 trägt nur über den `permissions[]`-Deny, nicht über das Plugin") | §4-D-Q3, D-Q2-Tabelle, AC-8 | **bestätigt** (`runtime-gate-tiers.md:50-53`) |

  H1 und H2 werden also durch D-Q1/D-Q2/D-Q4 beantwortet, H3 durch D-Q3. Offen bleibt allein die
  Frage, ob der Issue-Body weitere Hypothesen enthielt (Review-Einschränkung, nicht auflösbar ohne Body).
- **Governance-Hinweis (Rev. 2, erweitert):** `consistency/spec_plan.py::_classify` (`:318-323`)
  behandelt `*-design.md` als `spec` und **alles andere** (auch `*-spec.md`) als `plan`. Folgen für
  dieses Paar:
  1. Diese Datei matcht `_DESIGN_RE` (`:50`) und wird deshalb als `spec` gegen die
     **Spec**-Sektionen geprüft (`REQUIRED_SPEC_SECTIONS`, `:351`). Die acht Pflicht-Überschriften
     — `## Problem`, `## Ziel`, `## Nicht-Ziele`, `## Interface Contracts`, `## Datenfluss`,
     `## Acceptance Criteria`, `## Offene Fragen`, `## Trace-Anker` — stehen aus diesem Grund
     **literal** in der Datei (Rev. 3.1); fehlte eine, wäre es wegen `spec-plan-required: false`
     eine WARNING, kein Fehler.
  2. Der `spec-id`-Anker wird gegen den Plantext geprüft (`:425-439`); der Plan nennt
     `SPEC-orchestrator-mode-topology-2026-11-09` im Kopf (`**spec-id:**`) und in der
     Frontmatter-`trace`-Liste ⇒ kein Finding.
  3. Der Plan hingegen wird als `plan` erkannt und erreicht `_check_approval_markers` (`:479-507`),
     **sobald** er `**Spec:**` wörtlich nennt. Solange diese Spec `DRAFT` war, entstand dort der
     beabsichtigte ERROR `spec_plan_approval_marker` — das war das gewünschte Verhalten, kein
     Planfehler. Mit der User-Freigabe am 2026-11-09 trägt diese Spec `Status: APPROVED`
     (sichtbarer Marker `> Status: APPROVED`), sodass `_check_approval_markers` **keinen** Befund
     mehr erzeugt: der Gate ist erfüllt und die Plan-Ausführung autorisiert.

---

## 14. Review-Auflösung (2026-11-09)

Gegenstand: `docs/reviews/2026-11-09-orchestrator-mode-topology-review.md` (Review 1, vor Revision 2).
Status dieser Tabelle = Stand Rev. 4. Zum Zeitpunkt der Einarbeitung stand diese Spec auf `DRAFT`;
seit der User-Freigabe am 2026-11-09 ist sie `Status: APPROVED`. Die Tabelle belegt weiterhin nur,
**wo** der Befund eingearbeitet wurde — die Freigabe ersetzt kein „erledigt" im Sinne von „umgesetzt".

| Befund-ID | Änderung | Stelle |
|---|---|---|
| RVW-1190-01 (BLOCKER) | D-Q5 vollständig neu: `direct-dispatch-enabled` wirkt unter `strict` (`orchestrator.md:203-205`, `config.py:2090-2101`); Bedingung auf `mode == "main-chat"` ∧ Key präsent; INFO-Text ohne falschen Entfernungs-Rat; kein `[INF]` in diesem Repo | §1.3, §3.4, §4-D-Q5, §6.2, §6.4, AC-12, AC-13 |
| RVW-1190-02 (BLOCKER) | „kein Spawn-Kanal" ersatzlos gestrichen und durch positions-/capability-basierte Formulierung ersetzt; `EFFECTIVE_PRIMARY` bleibt alleinige Verzweigung; Claude-Caveat präzisiert | §1.1, §5-G1, §6.5, §12.4, AC-3, AC-14 |
| RVW-1190-03 (BLOCKER) | G7 adressiert jetzt `reconcile_opencode_surface_gate` (`:1751`) + `_opencode_v2_gate_permissions` (`:1408`); `topology=None` als Signaturerweiterung; beide Aufrufer in §11 und AC-23; Durchreichung statt Neuresolution | §3.5, §5-G7, §11, AC-22, AC-23 |
| RVW-1190-04 (MAJOR) | Check-Ablage geteilt: zwei in `consistency/topology.py`, einer in `consistency/orchestrator_strict.py`; §6.2 hat eine Ort-Spalte | §5-G6, §6.2, AC-21 |
| RVW-1190-05 (MAJOR) | Geteilte Kontextdatei darf keine positionsspezifische Aussage tragen: neutraler Text + Safe-Side-Regel; Test auf tatsächlich gerenderten Text mit zwei Sharern | §5-G5, AC-20, AC-24 |
| RVW-1190-06 (MAJOR) | Regenerationsschritt `python3 scripts/sync.py` + Diff-Prüfung + Commit je emissionsrelevantem Task; `--check`-Gates erst danach; M1/M3/M8/T21 entzerrt | AC-31, §8 |
| RVW-1190-07 (MAJOR) | `active_set` als **Pflicht-Keyword** in `_provider_topology_flags`; Durchreichung an alle vier Seams; Paritäts-AC ergänzt | §5-G2, AC-30 |
| RVW-1190-08 (MAJOR) | Revision 2: §5-G2-Formel auf `source != "derived"` korrigiert; AC-1-Kanal auf `--validate`/`consistency-check`; K-1/K-2 im Plan degradiert | §5-G2, AC-1, §5-G2 (Formel-Korrektur) |
| RVW-1190-09 (MAJOR) | Plan erhält die Pflichtsektionen (`**Goal:**`, `**Architecture:**`, `**Tech Stack:**`, `**Spec:**`, `## Global Constraints`, `## File Structure`, `pipeline_stages`); `_classify`-Folgen ausführlich dokumentiert | §13, Plan-Kopf, Plan „Global Constraints" / „File Structure" |
| RVW-1190-10 (MAJOR) | AC-22 nennt jetzt den Kanal (Sync-Log, Tier `plugin`), pinnt den neuen Warntext und schließt ein Finding aus; v1-Zählregel (Log + Finding, je Kanal eine) verbindlich | §5-G7, §6.4, AC-22 |
| RVW-1190-11 (MAJOR) | Alle `.tmp/`-Zitate entfernt; M0 erzeugt die Baseline selbst (EXIT-Codes/Hashes im Plan dokumentiert) | Plan „Voraussetzungen", „Meilensteine" (M0), T13, Plan „Teststrategie" |
| RVW-1190-12 (MAJOR) | `_singleton_constraint_block(effective, *, inert)`; `ORCH_TOPOLOGY_INERT` dort verdrahtet; `_EFFECTIVE_SOURCE` als Audit-Flag deklariert | §5-G2, §5-G4, §6.3, AC-15 |
| RVW-1190-13 (MINOR) | Szenario 103 aus dem `10*`-Match genommen, im Katalog `BLOCKED (#1182)`; keine Skip-Konvention; M8 auf 4 PASS | AC-29, Plan T17, M8 |
| RVW-1190-14 (MINOR) | `ROLE_ORCHESTRATOR_ACTIVE`-Test unter `main-chat` namentlich T10 zugeordnet und in AC→Task-Tabelle geführt | AC-24, Plan T10, Plan §10 |
| RVW-1190-15 (MINOR) | B-9 auf den echten Unterschied umgestellt (widersprüchlicher Render in **einer** Datei); Elf-Liste bleibt | §3.3, §9.1 B-9, §5-G9 |
| RVW-1190-16 (MINOR) | AC-23 auf die drei realen Aufrufstellen (`:869`, `:1457`, `:1827`) bezogen; `None`-Ausnahme nur an `:869` | AC-23 |
| RVW-1190-17 (MINOR) | AC-27: Byte-Identität nur noch für `ungesetzt ∧ effective == "subagent"` (Rev. 3 geschärft); abgeleitetes **und** deklariertes `primary` = beabsichtigte Änderung mit eigener Golden-Fixture | AC-16, AC-17, AC-27, Plan „Migration & Rollback", T8, T21 |
| RVW-1190-18 (MINOR) | D-Q1-Remediation nennt `orchestrator.provider-overrides.<P>.topology: subagent`; Projekt-Scope + `main-chat` ist ERROR | §4-D-Q1 |
| RVW-1190-19 (NIT) | H-Map H1/H2/H3 → D-Q/AC mit Urteil `bestätigt`/`teilweise bestätigt` ergänzt | §13 |
| RVW-1190-20 (NIT) | Sieben neue Flags (fünf Bool, zwei String); Injektionsbedingung mit `not role.endswith("-iteration")`; „Gate #5" als bewusst konservierter toter Verweis markiert; „cannot run as a subagent" als `ISSUE` markiert | §6.3, §5-G4, §1.1, Plan T2/T9 |
| B1 (Formalblocker) | Plansumme korrigiert auf 9×S / 8×M / 1×L | Plan Kopf |
| B2 (Formalblocker) | durch RVW-1190-04 gelöst (AC-21 ↔ T13-Ablage konsistent) | AC-21, Plan T13 |
| B3 (Formalblocker) | AC-15 auf die fünf **Bool**-Flags präzisiert; zwei String-Flags separat als Audit-/Doku-Flags | AC-15, §6.3 |
| W1 | AC-1-Kanal korrigiert (`--validate`/`consistency-check` statt `sync --check`) | AC-1 |
| W2 | T17 hatte kein AC ⇒ AC-29 für Szenarien 100–104 ergänzt | AC-29 |
| W3 | Plan-Anker `…-spec.md:2` → `:3` | Plan Voraussetzungen |
| W4 | „94–99 reserviert" mit Quelle (Config-Welle, PR #1212) versehen; `100`–`104` bleibt kollisionsfrei | Plan „Teststrategie" |
| W5 | Allowlist bestätigt real: #1209, #1006, #885 sind bestehende Issues, keine Erfindung | §10, Plan §11 |
| W6 | Plan-Kopf trägt `Revision: 3` | Plan Kopf |

### Re-Review 1 (vor Revision 3) — RVW2-1190-01…-13

| Befund-ID | Änderung | Stelle |
|---|---|---|
| RVW2-1190-01 (BLOCKER) | Identitätszusage auf `ungesetzt ∧ effective == "subagent"` geschärft; abgeleitetes `primary` ist beabsichtigte Änderung mit eigener Golden-Fixture; `subagent`-Einstiegshinweis **nicht** geändert (Rev.-2-Formulierung zurückgenommen) | AC-16, AC-17, AC-27, §5-G5, Plan „Global Constraints", T7, T8, T10, T21, Plan „Migration & Rollback" |
| RVW2-1190-02 (MAJOR) | Entscheidung aus `build_agent_hints` in `context._position_aware_agent_hints` (`_sync_managed_block_context`, `:848-852`) verlegt; `position`-Parameter; geteilte Datei = neutral, gleichpositionierte Sharer = Positions-Text; ∃-Regel bleibt verworfen (K-4) | §5-G5, AC-20, Plan T5, T10, K-4 |
| RVW2-1190-03 (MAJOR) | Context-Seam auf `_sync_stage_contexts` (Stage 4, `sync_pipeline.py:732-737`, Aufruf `:788-790`) korrigiert; `active_set` als Pflicht-Keyword bis `sync_context_for_provider`; Aufrufer `cli_commands.py:1543` (`ctx.active_set`, `:964`) in File-Map und T5; Default-`None` ausgeschlossen | §5-G2, Plan „Global Constraints", T5, File-Map, AC-30 |
| RVW2-1190-04 (MAJOR) | G1-Text capability-/positionsbasiert geöffnet (Delegations-Weg mit Provider-Voraussetzung); absolute Negativ-Aussage nur noch verboten, nicht behauptet; Claude-Negativ-Assertion in AC-3 | §5-G1, AC-3, §6.5, §12.4 |
| RVW2-1190-05 (MINOR) | INFO-Prüfung **einmal pro Lauf vor dem Provider-Loop** (`orchestrator_strict.py:226`), Begründung gegen die Lage hinter `_resolve_effective_strict` (`:227-228`) | §5-G6, AC-12, Plan T13 |
| RVW2-1190-06 (MINOR) | Kanal auf `--validate`-only präzisiert (`cli_commands.py:1457-1464`); Assertion auf die **Check-ID** statt „kein `[INF]`"; bestehendes `no-hook-support` ausdrücklich ausgenommen | §4-D-Q5, AC-12, §6.2 |
| RVW2-1190-07 (MINOR) | Plan-Selbstaussage so umformuliert, dass der Platzhalter-Checker (`consistency/spec_plan.py:88-97`, `:366-384`) nicht mehr auslöst | Plan „Self-Review" |
| RVW2-1190-08 (MINOR) | P3-Status einmalig auf **„shipped"** festgelegt; die Vorgänger-Spec-Zeile `:791-792` ist als überholt ausgewiesen, nicht editiert | §5-G9, §9.1 B-7/B-8, Plan T16 |
| RVW2-1190-09 (MINOR) | Provider-lose Basis ausdrücklich **nicht autoritativ**; Ratchet-Test „kein Render-Seam konsumiert die Basis" | §5-G2, AC-30, Plan T3 |
| RVW2-1190-10 (NIT) | Plan „Teststrategie": zehn neue Testdateien; „24 Zellen × 4 Assertions = 96" korrigiert | Plan „Teststrategie" |
| RVW2-1190-11 (NIT) | Branch-Übergang `docs/…` → `feat/…` in Plan „Branch-Guard" explizit benannt | Plan „Branch-Guard" |
| RVW2-1190-12 (NIT) | `_opencode_v2_gate_permissions` überall `:1408` (RVW-1190-03-Zeile korrigiert); `ORCH_TOPOLOGY_INERT` einheitlich `mode == "main-chat"` | §14 (RVW-1190-03), §5-G2, §6.3, Plan T1, K-3 |
| RVW2-1190-13 (MINOR) | AC-24 (konkrete Prosa-Assertion), AC-23 (Trefferzahlen + Monkeypatch-Zähler), AC-25 (Datei-Scope + Ausnahmen) präzisiert | AC-23, AC-24, AC-25, Plan T10, T14, T16 |

**Nicht aufgelöst (bewusst):** Der Issue-Body #1190 lag auch in dieser Runde nicht vor; H1–H3 sind
deshalb weiterhin nur gegen diese Spec prüfbar (§13). Diese Spec stand bis zur User-Freigabe am
2026-11-09 auf `DRAFT`; seither ist sie `Status: APPROVED` — die Freigabe betrifft den Entwurf, nicht
die noch offene H-Map-Frage.

### User-Entscheidungen (2026-11-09) — D-OQ1…D-OQ3

| ID | Entscheidung (`DECIDED 2026-11-09`) | Änderung in dieser Revision | Stelle |
|---|---|---|---|
| **D-OQ1** | Default dieses Repos = **`strict × subagent`**, **explizit deklariert**; beide Opencode-Positionen (`main-chat`, `subagent`) first-class, `primary` die dritte, optionale Position | Neues Positionsmodell mit drei Positionen und Mapping-Tabelle `mode × topology → Position`; D-Q3-Empfehlungen je Surface umgestellt; AC-7-Menge und AC-11 angepasst; AC-32 (Positions-Doku) und AC-36 (declared deterministisch) ergänzt; D-Q1-Kontext, D-Q4-Definition und R-6 nachgeführt; die Config-Deklaration bleibt ausdrücklich Plan-Task T20 (nach dem Code-Fix) | §3.8 (3.8.1–3.8.3), §4-D-Q1, §4-D-Q3, §4-D-Q4, §6.5, §9.2 R-6, §9.3 OQ-1, §12, AC-7, AC-11, AC-32, AC-36 |
| **D-OQ2** | Zelle `strict × subagent` bleibt **erlaubt und empfohlen**; kein Verbot, keine „nicht empfohlen"-Markierung; pro Surface wird der **tatsächlich** greifende Gate-Tier ausgewiesen; Opencode generiert **je Position** sauber (POS-1 ohne dangling `default_agent`, POS-2 ohne `mode: primary` mit ehrlichem `gate-inactive`, POS-3 als Session-Einstieg) | §3.8.3 als verbindliche Zusagen; §6.5 mit Spalte „Gate-Tier, der tatsächlich greift"; Matrixzeilen je Position; AC-8 neu gefasst; AC-33 (je ein Test pro Position), AC-34 (POS-1), AC-35 (POS-2) ergänzt; Provider-Agnostik als Zusage 4 | §3.8.3, §6.5, §12.2–§12.5, AC-8, AC-33, AC-34, AC-35 |
| **D-OQ3** | `advisory × subagent` wird **erst nach dem Fix von #1182** empfohlen; bis dahin ist `strict × subagent` die belastbare Team-Empfehlung; Szenario `103` bleibt `BLOCKED (#1182)` | Bedingung in jeder `advisory × subagent`-Zeile (v1/v2/Claude/Gemini) und in D-Q3; AC-29 auf die neue Szenario-Zuordnung umgestellt; AC-37 (Bedingung an jeder Empfehlungsstelle) ergänzt; R-9 als Risiko | §4-D-Q3, §12.2–§12.5, §9.2 R-9, §9.3 OQ-4, AC-29, AC-37 |
