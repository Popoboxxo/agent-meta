# Dynamic Routing + Template Slimming — Spec

> Status: APPROVED (2026-09-19)
> Klasse: XL / Architectural
> Vorgelagertes Systemdesign: Kernentscheidungen liegen vor (Concept-Architect)
> Revision: 5 (Amendment zum Code-Review Runde 2 — RVW-22-Norm in §3.7 und AK B2a
> geändert, siehe §8.4; vorher: Revision 4 nach finalem Re-Review
> `2026-09-19-dynamic-routing-template-slimming-final-rereview.md`)

## Trace-Anker

```
spec-id: SPEC-dynamic-routing-template-slimming
```

Diese Spec beschreibt **zwei zusammenhängende Änderungen** im agent-meta-Framework:

- **Block A — Dynamisches, konfigurationsabhängiges Routing:** jede aktive Rolle wird
  adressierbar; Routing-Ziele werden deterministisch aus `config/role-defaults.yaml`
  abgeleitet; die Aktivierungslogik bekommt eine Single Source.
- **Block B — Slimming der Agenten-Templates:** wiederkehrende Blöcke werden über den
  vorhandenen Snippet-/Variablen-Mechanismus zentralisiert, ohne Semantikverlust und ohne
  den Route-Guard zu verletzen.

---

## 1. Problem / Ziel / Nicht-Ziele

### 1.0 Problem

Routing-Ziele und Agenten-Tabellen werden heute aus **zwei unterschiedlichen
Aktivierungslogiken** gebildet (§1.5) und können still auseinanderlaufen. Vier Rollen sind
nicht keyword-/example-adressierbar (§1.1), obwohl nur `orchestrator` aus
Anti-Recursion-Gründen ausgeschlossen sein darf. Der nicht-callable Fallback-Pfad des
Orchestrators kann Name→Rolle mangels strukturiertem `name_index` nicht deterministisch
auflösen. Parallel tragen die Templates erhebliche Redundanz (§1.7), deren Deduplikation
den Route-Guard nicht unterlaufen darf.

### 1.1 Ist-Analyse: Routing-Datenlage

`config/role-defaults.yaml` ist die einzige Routing-Quelle (Route-Guard,
`tests/test_no_role_routes_in_templates.py`). Sie enthält 84 Rollen:

| Merkmal | Anzahl |
|---|---|
| Rollen gesamt | 84 |
| mit `routing.intent_keywords` + `routing_patterns` | 80 |
| mit `handoff.output_contract` | 48 |
| mit `handoff.target_roles` | 29 |
| `routing.orchestrator_only: true` | 3 (`principal-developer`, `bug-feature-analyzer`, `knowledge-indexer`) |

**Nicht keyword-/example-adressierbar (4 Rollen):**

| Rolle | Grund | Ort der Fixierung |
|---|---|---|
| `orchestrator` | Anti-Recursion: Self-Dispatch HARD REJECT | `delegation_table.py:119-120`, `agents.py:273` |
| `intern-developer` | Easter Egg, kein Routing | `tests/test_routing_tool_definitions.py:67-73` |
| `principal-developer` | Eskalations-Rolle, nur `orchestrator_only` | ebd. |
| `openscad-developer` | **Datenfehler** — als nicht keyword-routbar dokumentiert | `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md:270` |

Ziel-Adressierbarkeit nach dieser Spec (84 Rollen):

| `addressability` | Erwartung | Begründung |
|---|---|---|
| `keyword` | **81** | 80 Bestands-Patterns + `openscad-developer` (Datenfehler-Fix) |
| `name_only` | **2** | `intern-developer`, `principal-developer` |
| `excluded` | **1** | `orchestrator` (Anti-Recursion) |

### 1.2 Bestehende Nuance beim Routing-Ziel-Enum

`route_intent.target_agents`-Enum umfasst alle aktiven Nicht-Orchestrator-Rollen
(`delegation_table.py:116-138`); Regeln (`rules[]`) entstehen nur für Rollen mit
nicht-leeren `keywords`/`examples` (`:147-156`). „Rolle im Enum, aber ohne Keyword-Regel"
existiert also bereits — ohne `name_index` ist dieser Pfad zur Laufzeit nicht sauber
auflösbar, wenn das native Tool nicht callable ist.

### 1.3 `route_intent` ist in keiner Runtime callable

- `config/provider-capabilities.yaml`: `route_intent_tool: false` für **alle 9 Provider**
  (Zeilen 69, 89, 109, 135, 158, 188, 222, 253, 284 — verifiziert).
- Tests: `tests/test_provider_agnostic_dispatch.py:176-191`,
  `tests/test_routing_tool_definitions.py:399-418`.
- Orchestrator nutzt den Fallback `{{#if ROUTE_INTENT_CALLABLE}}`
  (`agents/1-generic/orchestrator.md:92-98`). `{{INTENT_ROUTING_TOOLS}}` wird **außerhalb**
  des Conditionals (Zeile 98) eingebettet — `name_index` wäre im Prompt verfügbar.

### 1.4 Datenfluss (verifiziert)

```
config/role-defaults.yaml
  → scripts/lib/roles.py         load_roles_config:44, build_role_map:62
  → scripts/lib/delegation_table.py
        _active_role_names:34, get_active_agents_data:70,
        get_routing_rules:97, get_intent_routing_table:189
  → scripts/lib/agents.py
        ROUTING_TOOL_NAME:34, build_agent_hints:105, build_agent_table:178,
        build_routing_tool_definition:224,
        build_routing_tool_definitions_for_providers:339
  → scripts/lib/config.py
        PIPELINE_MATCH_TABLE:1801, INTENT_ROUTING_TABLE:1962,
        _INTENT_ROUTING_TOOL_DEFS:1977
  → scripts/lib/agent_sync.py     ROUTE_INTENT_CALLABLE:469
```

### 1.5 DIVERGENZ-RISIKO: zwei Aktiv-Mengen mit unterschiedlicher Logik

| Builder | Filter | Ort |
|---|---|---|
| `_active_role_names` (Routing/Ziele) | direkte Variablen `SE_ENABLED`/`VALIDATOR_ENABLED`/`KNOWLEDGE_ENGINE_ENABLED`/`DEVELOPER_TIERS_ENABLED` + Projekt-Whitelist — **ohne** `_is_role_enabled` | `delegation_table.py:34-67` |
| `build_agent_hints` / `build_agent_table` (Hints/Tabelle) | Projekt-Whitelist **UND** `_is_role_enabled` | `agents.py:121-197`, `frontmatter.py:467-475` |

Widersprüchliche Defaults:

| Default | Wert | Ort |
|---|---|---|
| SE-Default in `_is_role_enabled` | `True` | `frontmatter.py:471` |
| SE-Default in Aktivierungs-Variablen | `False` (`se_config.get("enabled", False)`) | `config.py:1580` |

Folge: Routing-Ziele und Agenten-Tabelle können **auseinanderlaufen** — Rollen werden
still aus dem einen, nicht aber aus dem anderen Artefakt gedroppt.

### 1.6 Templates ohne `role-defaults`-Eintrag (korrigiert)

**Widerlegte Vorannahme:** Entgegen der Erstfassung haben die `*-reviewer`-Templates sehr
wohl Einträge mit `routing_patterns` — verifiziert:
`code-reviewer` (`role-defaults.yaml:1189`), `concept-reviewer` (`:1219`),
`frontend-reviewer` (`:2221`), `backend-reviewer` (`:2242`),
`database-reviewer` (`:2263`), `ui-reviewer` (`:2284`).

**Einziger scheinbarer Sonderfall:** `agents/1-generic/provider-expert.md` hat keinen
Eintrag — **by design**: es ist in `WRAPPER_TEMPLATES` (`frontmatter.py:55`) gelistet,
wird von `collect_sources` explizit ausgeschlossen (`frontmatter.py:637`) und ist eine
`based-on`-Basis-Vorlage, keine selektierbare Rolle (`CHANGELOG` #736/WP5;
`config_audit.py:71-90`; `docs/plans/audit-2026-09-detailed-system-audit.md:54`).

**Konsequenz:** Es gibt keinen echten „Template-ohne-Eintrag"-Orphan. §5.2 liefert dennoch
eine Warnung für „generierbare Rolle ohne role-defaults-Eintrag" als Regressionsnetz; die
`WRAPPER_TEMPLATES`-Menge ist davon ausgenommen.

### 1.7 Template-Größen und Redundanz

101 Template-Dateien / 14.890 Zeilen:

| Layer | Dateien | Zeilen |
|---|---|---|
| `agents/1-generic` | 83 | 13.106 |
| `agents/2-platform` | 18 | 1.784 |

Wiederkehrende Blöcke:

| Block | Vorkommen |
|---|---|
| `<output-guard>` | 51× |
| `## Background-Process Guard (issue #506)` | 49× |
| `## 1. Parse input` | 43× |
| `## Anti-Recursion Guard` (inline, literal) | **21×** (verifiziert: `knowledge-*` + `se-*`) |
| `{{ANTI_RECURSION_BLOCK}}` (bereits referenziert) | **5×** (verifiziert: `developer.md:138`, `orchestrator.md:298`, `_reference-agent.md:160`, `sharkord-developer.md:85`, `agent-meta-developer.md:157`) |
| `A2A_HANDOFF_BLOCK` | 15× |

**Widerlegte Vorannahme RVW-03:** `ANTI_RECURSION_BLOCK` war **nicht** 0× referenziert,
sondern 5×. Der Slimming-Hebel ist die **21× wörtlich duplizierte** Inline-Prosa
(`## Anti-Recursion Guard`), nicht die Block-Variable selbst.

Vorhandene Zentralisierungsbausteine:

| Variable | Definition | Referenzen |
|---|---|---|
| `ANTI_RECURSION_BLOCK` | `config.py:1536-1539` | 5× (aktiv) |
| `QUALITY_PIPELINES_BLOCK` | `config.py:1834` | 0× |
| `A2A_HANDOFF_BLOCK` | `config.py:1529-1535` | 15× |

Snippet-Mechanismen — **zwei unterschiedliche Pfade, nicht verwechseln:**
1. `*_BLOCK`-Variablen werden beim Rendern via `_build_snippet_variables`
   (`config.py:1815-1879`) **inlined** (String-Substitution).
2. `*_SNIPPETS_PATH`-Variablen kopieren Dateien in das Zielprojekt
   (`scripts/lib/context.py:2214-2230`, verifiziert) — **kein** Inlining.

### 1.8 Fehlende Absicherung

- Kein Schema-Test für `role-defaults`.
- Kein Coverage-/Overlap-Test der Routing-Regeln (#779 IT-6/IT-7).
- Kein Äquivalenz-Gate für Template-Slimming.
- Der Route-Guard-Scope ist `("agents/1-generic/*.md", "rules/1-generic/*.md")`
  (`tests/test_no_role_routes_in_templates.py:54`) — **`snippets/` ist nicht abgedeckt**.
- **Snippet-Korpus nicht auf Guard-Verträglichkeit geprüft (RVW-20):** Vor der
  Scope-Erweiterung existieren 13 Bestands-Snippets. Vorab-Grep (diese Revision) findet
  Pfeil-Konstrukte in `snippets/orchestrator/se-mode.md` (`L0→L{{SE_MAX_DEPTH}}`,
  `continue → neuer System-Cell`, `L1 … ←→ Architecture … → Interface Registry`) und
  `snippets/orchestrator/a2a-protocol.md` (`[task] → [agent]`). Die beteiligten Tokens
  sind **keine** Rollen (`L0`, `continue`, `Requirements`, `Architecture`, `[agent]`),
  daher greift `D-NONROLE` erwartungsgemäß; `T-HANDOFF`/`T-ROUTE-COL`/`T-NEXT` liefern
  keine Treffer. **Pre-Flight-Gate:** Vor dem Aktivieren der Scope-Erweiterung wird der
  Guard einmal über `snippets/**/*.md` trockenlaufen gelassen; Treffer müssen entweder
  über die bestehende `D-NONROLE`-Regel belegt exempt sein oder durch **Snippet-
  Umschreibung** (nicht Detektoränderung) beseitigt werden. A6 verlangt 0 Verstöße.

### 1.9 Ziel

Siehe §2 (Block A/B) — dynamisches, config-abhängiges Routing mit Single Source und
name-basierter Fallback-Adressierung; Deduplikation der Templates ohne Semantikverlust.

### 1.10 Nicht-Ziele

- **`route_intent` callable machen:** ausdrücklich NICHT. `route_intent_tool` bleibt bei
  `false`; der Fallback bleibt Produktionspfad.
- **Neue Rollen anlegen:** keine.
- **Provider-Capabilities ändern:** keine neuen/geänderten Capability-Keys.
- **Provider-Name-Branches:** keine `if provider == "Name"`-Logik.
- **Worktree-Isolation:** keine.
- **Repo-Containment lockern:** keine Schreibzugriffe außerhalb der Projekt-Wurzel.
- **Detektor-Logik des Route-Guards abschwächen:** keine Entfernung/Aufweichung von
  `T-*`/`D-*`-Detektoren. Der **Scope** wird um `snippets/**/*.md` erweitert (RVW-04).
- **Inhaltliche Neufassung von Agenten-Prompts:** Slimming ist Deduplikation.
- **SE-Kaskade:** wird nicht gestartet.

---

## 2. Zielbild

### 2.1 Block A — Dynamisches Routing

1. **Single Source bleibt `config/role-defaults.yaml`.** Neuer Top-Level-Block
   `activation_groups:` mit genau einer expliziten Default-Tabelle.
2. **Kanonischer Aktiv-Resolver** in `scripts/lib/roles.py`:
   `resolve_activation_gates`, `is_role_enabled`, `resolve_active_roles`.
   `frontmatter._is_role_enabled` wird ein Re-Export mit Root-Parameter (§5.2).
3. **Eine gemeinsame Aktiv-Menge mit zwei expliziten Layern:**
   Layer 1 = Aktivierungs-Gates + Whitelist; Layer 2 (`require_template=True`) = Layer 1 ∩
   generierbare Rollen. Routing-Ziele, Hints und Tabelle nutzen Layer 2. Abweichungen
   erzeugen eine Warnung über einen definierten `warn_sink` statt eines stillen Drops.
4. **Adressierbarkeit explizit:** Rollen-Feld
   `routing.addressability: keyword | name_only | excluded`; `excluded` nur `orchestrator`;
   `keyword` erfordert nicht-leere `routing_patterns` (keywords **oder** examples).
   Fehlt das Feld → Ableitung + Warnung.
5. **Datenfehler beheben:** `openscad-developer` erhält echte `routing_patterns` (→
   `keyword`); `principal-developer` und `intern-developer` werden `name_only` mit
   `name_only_reason`.
6. **`get_routing_rules()` liefert zusätzlich `name_index`** (deterministisch) mit
   `agent`, `short_desc`, `tier`, `orchestrator_only`, `addressability`,
   `name_only_reason`.
7. **`name_index` wird im nicht-callable Fallback-Pfad verpflichtend konsumiert**
   (Prompt-Contract in `orchestrator.md`, §5.6) — sonst bleibt das Ziel „jede Rolle
   adressierbar" daten-, aber nicht verhaltensseitig abgesichert.
8. **`route_intent` bleibt nicht-callable.** Keine Capability-Änderung.

### 2.2 Block B — Template-Slimming

1. Wiederkehrende Blöcke werden über den **vorhandenen** `*_BLOCK`-Inlining-Mechanismus
   zentralisiert. Kandidaten: die 21× inline duplizierte Anti-Recursion-Prosa,
   Background-Process-Guard, `<output-guard>`, Parsing-Boilerplate.
2. Der Route-Guard wird **nicht** verletzt: Routing bleibt ausschließlich in
   `config/role-defaults.yaml`; Templates, Rules **und Snippets** enthalten keine
   Routen-Tabellen, `roleA→roleB`-Pfeile, imperativen Handoffs oder Rollen in `NEXT:`.
3. **Qualitätsmetrik = semantische Äquivalenz des generierten Outputs.** Byte-Identität
   wird nur für Vorkommen zugesichert, die vorab als byte-identisch klassifiziert wurden
   (§5.5); Near-Duplikate erfordern ein dokumentiertes Diff-Manifest und einen
   abschnittsweisen Äquivalenz-Nachweis.
4. Kein neuer Ad-hoc-Mechanismus: Extraktion ausschließlich über benannte
   `*_BLOCK`-Variablen + Snippet-Dateien und `_build_snippet_variables`.

---

## 3. Interface Contracts & Datenfluss

### 3.1 Schema: `activation_groups` in `config/role-defaults.yaml`

```yaml
activation_groups:
  se:
    default: false
    role_patterns: ["se-*"]
    mirror_variable: SE_ENABLED          # nur Anzeige-Mirror, keine Gate-Quelle
    config_predicate:
      kind: config_flag
      path: systems-engineering.enabled
  knowledge:
    default: false
    role_patterns: ["knowledge-*"]
    mirror_variable: KNOWLEDGE_ENGINE_ENABLED
    config_predicate:
      kind: config_flag
      path: knowledge-engine.enabled
  validator:
    default: false
    role_patterns: ["validator"]
    mirror_variable: VALIDATOR_ENABLED
    config_predicate:
      kind: roles_membership
      mode: any
      roles: ["validator"]
  developer_tiers:
    default: false
    role_patterns: ["junior-developer", "senior-developer", "principal-developer"]
    mirror_variable: DEVELOPER_TIERS_ENABLED
    config_predicate:
      kind: roles_membership
      mode: all
      roles: ["junior-developer", "senior-developer"]
```

**Präzise Semantik der Predikate (RVW-07):**

- `kind: config_flag` → `bool(resolve_dotted(config, path))`; fehlender Pfad → `default`.
- `kind: roles_membership`, `mode: any` → `any(r in config.get("roles", []) for r in roles)`.
- `kind: roles_membership`, `mode: all` → `all(r in config.get("roles", []) for r in roles)`.
- **Prezedenz (RVW-14):** `config` ist die **einzige** Gate-Quelle; explizit gesetzter
  Projektwert schlägt `default`. Die früheren `variables`-Gates (`SE_ENABLED` etc.) sind
  **keine** Gate-Quelle mehr, sondern aus den Gates abgeleitete Anzeige-Variablen
  (`mirror_variable`).
- **Behavior-Change (bewusst, dokumentiert):**
  - SE-Default wird auf `false` vereinheitlicht (`activation_groups.se.default: false`);
    der implizite `True`-Default in `frontmatter.py:471` entfällt. Für agent-meta
    selbst (`systems-engineering.enabled: false`) unverändert.
  - `developer_tiers` behält die heutige Konjunktion (`all` junior+senior,
    `config.py:1605-1607`) als **Gruppen-Enable-Prädikat** bei. `role_patterns` definiert
    die **Gruppen-Mitgliedschaft** (Gating): `principal-developer` ist — wie
    `junior-developer`/`senior-developer` — Mitglied von `developer_tiers` und damit vom
    Gruppen-Enable abhängig. `principal-developer` ist **nicht** Teil des
    `config_predicate` (dieses verlangt junior `all` senior). Bei `default: false` und
    ohne Whitelist ist die Gruppe inaktiv → alle drei Rollen fallen aus Layer 2; das
    entspricht `tests/test_routing_tool_definitions.py:88`

### 3.2 Neue/geänderte Funktionen in `scripts/lib/roles.py`

```python
def resolve_dotted(config: dict, path: str) -> object: ...

def resolve_activation_gates(agent_meta_root: Path, config: dict) -> dict:
    """-> {group_name: bool}. Einzige Default-Tabelle:
    role-defaults.yaml::activation_groups.<group>.default; Projekt-config schlägt Default.
    Deterministisch, keine Provider-Branch."""

def is_role_enabled(role: str, config: dict, gates: dict) -> bool:
    """True, wenn `role` über `role_patterns` zu einer per `gates` aktivierten Gruppe
    gehört, sonst True. gates[group] = config_predicate (schlägt default) ODER default."""

def resolve_template_roles(agent_meta_root: Path, config: dict) -> set[str]:
    """Generierbare Rollenmenge = collect_sources(agent_meta_root, platforms)
    \\ WRAPPER_TEMPLATES \\ {Rollen ohne ROLE_MAP-Eintrag}. Die dritte Menge entspricht
    dem target_filename(role, role_map)-Filter in agents.py:159/:199-204, damit
    target_agents und Hints/Tabelle deckungsgleich bleiben (RVW-27). Lazy import von
    frontmatter (kein Import-Zyklus), gecacht pro (agent_meta_root, platforms)."""

def resolve_active_roles(
    agent_meta_root: Path,
    config: dict,
    *,
    require_template: bool = False,
    template_roles: set[str] | None = None,
    warn_sink: list[str] | None = None,
) -> list[str]:
    """Layer 1: Aktivierungs-Gates + Projekt-Whitelist.
    require_template=True: zusätzlich Schnitt mit der generierbaren Menge (Layer 2).
    template_roles=None -> deterministisch via resolve_template_roles(agent_meta_root,
    config) aufgelöst (kein ValueError im Default-Pfad, RVW-18). `agent_meta_root` ist
    Pflichtparameter; es gibt keinen ValueError-Zweig (RVW-28).
    warn_sink: optionaler List-Sink; deterministisch sortierte, deduplizierte
    Warnstrings (siehe 3.3)."""
```

- **`variables` wird aus dem Resolver entfernt** (RVW-14): Gate-Quelle ist `config`;
  `variables` erzeugte genau die Doppelquelle, die Block A beseitigt.
- **`template_roles`-Injektion (RVW-01/O2/RVW-18):** Aufrufer mit Root-Zugriff übergeben
  bevorzugt die generierbare Rollenmenge aus
  `resolve_template_roles(agent_meta_root, config)` (`collect_sources` minus
  `WRAPPER_TEMPLATES` minus Rollen ohne ROLE_MAP-Eintrag, `frontmatter.py:55`,
  `agents.py:159/:199-204`). `template_roles=None` bei `require_template=True` ist
  **kein** Fehler, sondern wird lazy über `resolve_template_roles` aufgelöst
  (Default-Pfad bleibt funktionsfähig).
- **`frontmatter._is_role_enabled`** wird Re-Export **mit Root** (RVW-05):

```python
# scripts/lib/frontmatter.py
def _is_role_enabled(role: str, config: dict, agent_meta_root: Path) -> bool:
    from .roles import is_role_enabled, resolve_activation_gates
    gates = resolve_activation_gates(agent_meta_root, config)
    return is_role_enabled(role, config, gates)
```

  **Migrationsplan für Bestandsaufrufer** (alle haben Root-Zugriff):
  `definition frontmatter.py:467`; `import config.py:31`;
  Aufrufe `agent_sync.py:524`, `agents.py:157`, `agents.py:197`, `config.py:658`;
  Tests `tests/test_se_role_boundary.py:300`, `tests/test_knowledge_engine.py:80-108`.
  Alle Aufrufe werden auf die 3-Parameter-Signatur migriert (Tests übergeben
  `_AGENT_META_ROOT`). Es gibt **keine** versteckte Global-/Cache-Abhängigkeit.

### 3.3 Warn-Sink (RVW-06)

- Signatur: `warn_sink: list[str] | None`. Ist er `None`, wird **keine** Warnung
  verschluckt: `resolve_active_roles` schreibt zusätzlich via bestehenden `SyncLog`
  (stderr). Für Tests/Caller ist der List-Sink der kanonische Assertions-Kanal.
- Warnungs-Format (deterministisch, sortiert, dedupliziert):
  - `"active role without template: <role>"` (konfiguriert/gated, aber kein Template)
  - `"template without role-defaults entry: <role>"` (Ausnahme: `WRAPPER_TEMPLATES`)
- **Injektionspunkte (RVW-19):** `warn_sink` wird als Keyword-Parameter (Default `None`)
  in jede Builder-Signatur aufgenommen, deren Ausgabe A3 vergleicht:
  `delegation_table.get_routing_rules(..., template_roles=None, warn_sink=None)`,
  `delegation_table.get_active_agents_data(..., template_roles=None, warn_sink=None)`,
  `delegation_table.get_intent_routing_table(..., template_roles=None, warn_sink=None)`,
  `agents.build_agent_hints(..., warn_sink=None)`,
  `agents.build_agent_table(..., warn_sink=None)`,
  `agents.build_routing_tool_definition(..., template_roles=None, warn_sink=None)`.
  Caller binden den Sink an den bestehenden `unmapped`-Mechanismus
  (`config._build_platform_variables`, `config.build_variables` → `_INTENT_ROUTING_TOOL_DEFS`,
  `agents.build_agent_hints`/`build_agent_table`). Ohne Injektion bleibt der
  `SyncLog`-stderr-Pfad als Fallback.

### 3.4 Schema: `routing.addressability` (pro Rolle)

| Feld | Typ | Werte | Regel |
|---|---|---|---|
| `routing.addressability` | string | `keyword` \| `name_only` \| `excluded` | Pflicht (ggf. abgeleitet + Warnung) |
| `routing.name_only_reason` | string | frei | Pflicht bei `name_only`, sonst optional |

- `keyword`: erfordert **nicht-leere** `routing_patterns.keywords` **oder**
  `.examples` (§5.3; RVW-10 angeglichen).
- `name_only`: kein `rules[]`-Eintrag; bleibt in `target_agents`-Enum + `name_index`.
- `excluded`: kein `rules[]`-, kein `target_agents`-Eintrag; **nur** `orchestrator`.
- Fehlt `addressability`: Ableitung (Patterns vorhanden → `keyword`, sonst `name_only`)
  + Warnung `"missing addressability, derived: <role>=<value>"`. **`orchestrator` ist
  unabhängig von der Ableitung immer `excluded`** (RVW-21).
- `addressability` ist eine **statische Schema-Eigenschaft** (gilt für die Rolle, sobald
  sie aktiv ist) und **orthogonal zur Aktivierung**: ein `name_only`-Eintrag ohne aktive
  Gruppe ist gültig konfiguriert, erscheint dann aber nicht in `target_agents`/
  `name_index` (RVW-17). `addressability` sagt nur, **wie** eine aktive Rolle
  adressierbar wäre.

### 3.5 Änderung `get_routing_rules()` (`delegation_table.py`)

**Call-Site-Semantik (RVW-01/RVW-18, aufgelöst):** `get_routing_rules()` und
`get_active_agents_data()` rufen `resolve_active_roles(..., require_template=True)`
**direkt** auf — nicht über einen impliziten Wrapper-Default. `_active_role_names` behält
für **Rückwärtskompatibilität** den Default `require_template: bool = False` (Layer 1),
damit bestehende Aufrufe ohne Zusatzargument nicht brechen; die zwei internen Aufrufer
setzen explizit `require_template=True` + `template_roles`:

```python
def _active_role_names(
    agent_meta_root, config, variables, *,
    require_template: bool = False,          # back-compat Default = Layer 1, kein ValueError
    template_roles: set[str] | None = None,
    warn_sink: list[str] | None = None,
) -> list[str]:
    # `variables` wird aus Kompatibilität akzeptiert, ist aber KEINE Gate-Quelle (RVW-14).
    return resolve_active_roles(
        agent_meta_root, config,
        require_template=require_template,
        template_roles=template_roles,
        warn_sink=warn_sink,
    )
```

**Vollständige Call-Site-Liste + Migration (RVW-18):**

| # | Aufrufer | Heutiger Aufruf | Ziel |
|---|---|---|---|
| 1 | `delegation_table.py:81` `get_active_agents_data()` | `_active_role_names(root, config, variables)` | `resolve_active_roles(require_template=True, template_roles=..., warn_sink=...)` — Layer 2 (A3) |
| 2 | `delegation_table.py:136` `get_routing_rules()` | `_active_role_names(...)` | dito, Layer 2 |
| 3 | `get_intent_routing_table()` → `get_active_agents_data()` | indirekt | erbt Layer 2; reicht `template_roles`/`warn_sink` durch |
| 4 | `agents.build_routing_tool_definition()` (`:257-259`) | `get_routing_rules(...)` | `template_roles`/`warn_sink` durchreichen |
| 5 | `agents.build_routing_tool_definitions_for_providers()` (`:339`) | dito | dito |
| 6 | `agents.build_agent_hints()` (`:105`), `build_agent_table()` (`:178`) | eigene `collect_sources`-Filter | `warn_sink` ergänzen, `resolve_template_roles` verwenden |
| 7 | `config.build_variables()` (`:1962`, `:1977`) | ruft Tabellen-/Tool-Builder | `unmapped` als `warn_sink` injizieren |

**Migrationsschritte:** (1) `resolve_template_roles` in `roles.py`; (2) `template_roles`/
`warn_sink`-Parameter an die in RVW-19 genannten Signaturen, Default `None`;
(3) interne Aufrufer #1–#5 explizit auf `require_template=True` + Injizieren;
(4) `config.build_variables` bindet `unmapped` als `warn_sink`;
(5) `_active_role_names`-Default bleibt `False` — kein bestehender Aufruf wirft.
`get_active_agents_data` ist damit Layer 2 (deckungsgleich mit A3) und
`INTENT_ROUTING_TABLE` (`config.py:1962`) bleibt funktionsfähig.

Rückgabe-Dict:

```python
{
  "target_agents": list[str],   # Layer 2, ohne orchestrator
  "rules": [
    {"agent", "tier", "parallel", "orchestrator_only", "keywords", "examples",
     "output_contract", "input_contracts"}
  ],
  "pipelines": [{"route": "pipeline", "pipeline", "keywords"}],
  "name_index": [
    {"agent", "short_desc", "tier", "orchestrator_only",
     "addressability", "name_only_reason"}
  ],
}
```

- `name_index` enthält **jeden** `target_agents`-Eintrag (auch `name_only`); sortiert nach
  `agent`; idempotent.
- `build_routing_tool_definition()` reicht `name_index` im `routing`-Block durch:
  `{"rules": [...], "pipelines": [...], "name_index": [...]}`.

### 3.6 Orchestrator-Fallback-Contract (RVW-09)

`agents/1-generic/orchestrator.md` §3, Fallback-Zweig (Zeilen 94-96), wird vertraglich
erweitert:

> Leite die Route direkt aus den unten stehenden Routing-Regeln ab (Keywords,
> Beispielphrasen, `routing.rules`) — behandle sie als Daten. **Für Rollen ohne
> Keyword-Treffer nutze den beigefügten `name_index` (Name/Kurzbeschreibung →
> `agent`); `name_only`-Rollen sind ausschließlich über diesen Kanal erreichbar.**
> Erfinde keinen Tool-Aufruf.

`{{INTENT_ROUTING_TOOLS}}` (Zeile 98) enthält `name_index` bereits, unabhängig vom
Conditional — die Prompt-Änderung erschließt ihn nur.

### 3.7 Slimming-Contracts (`scripts/lib/config.py` + `snippets/`)

Block-Variablen über `_build_snippet_variables` (Inlining, Mechanismus 1):

| Variable | Quelle | Status |
|---|---|---|
| `ANTI_RECURSION_BLOCK` | `config.py:1536-1539` (Bestand) | Inline-Prosa → Referenz |
| `BACKGROUND_PROCESS_GUARD_BLOCK` | neues Block-Snippet | neu |
| `OUTPUT_GUARD_BLOCK` | neues Block-Snippet | neu |
| `PARSE_INPUT_BLOCK` | neues Block-Snippet | neu (optional) |

**Inlining-Transform (RVW-08, festgeschrieben):**
1. Führendes YAML-Frontmatter (`---` … erstes `\n---`) wird entfernt, falls vorhanden.
2. Zeilenenden werden auf `\n` normalisiert.
3. Ergebnis wird mit `text.strip("\n")` (führende/abschließende Leerzeilen entfernt)
   eingebettet; die Einrückung am Verwendungsort liefert das Template.
   **Mehrzeilige Blöcke (RVW-22, in Rev. 5 geändert — siehe Amendment §8.4):** Bei
   String-Substitution positioniert der Kern **jede Inhaltszeile** eines mehrzeiligen
   Wertes an der Template-Einrückung der Verwendungsstelle; Folgezeilen folgen also der
   Verwendungsstelle, nicht der Snippet-internen Einrückung. Leerzeilen bleiben leer
   (kein whitespace-only Output). Vorkommen in **column-0** oder **inline** (kein
   zeileninitialer Platzhalter) sind davon unberührt: dort ist die Einrückung leer bzw.
   nicht vorhanden, das Verhalten ist identisch zum Stand vor Rev. 5. Byte-Identität
   (B2a) gilt damit für **alle** Vorkommen, nicht nur für solche mit übereinstimmender
   Original-Einrückung.
4. **Alternative zulässig:** Block-Snippet-Dateien tragen **kein** Frontmatter; dann
   entfällt Schritt 1 (siehe offene Entscheidung O-D).

Regeln:
- Jede neue Block-Variable wird aus einer Snippet-Datei geladen.
- Templates referenzieren nur `{{..._BLOCK}}`; der gerenderte Output inlined den Text.
- Snippet-Dateien für den `*_SNIPPETS_PATH`-Kopierpfad (Mechanismus 2) behalten ihr
  YAML-Frontmatter; Block-Snippet-Dateien (Mechanismus 1) folgen der Transform-Regel.

### 3.8 Datenfluss Zielzustand

```
config/role-defaults.yaml (activation_groups + routing.addressability + patterns)
  → roles.resolve_activation_gates / is_role_enabled / resolve_active_roles
        └─ template_roles injiziert von agents.py (collect_sources, ohne WRAPPER_TEMPLATES)
  → delegation_table.get_routing_rules  (target_agents, rules, name_index)
  → agents.build_agent_hints / build_agent_table      (identische Layer-2-Menge)
  → agents.build_routing_tool_definition → config._INTENT_ROUTING_TOOL_DEFS
  → config.INTENT_ROUTING_TABLE
  → agent_sync.ROUTE_INTENT_CALLABLE (unverändert false)
        └─ orchestrator.md Fallback: Keyword→rules, Name→name_index
Slimming:  templates/{{*_BLOCK}} → config._build_snippet_variables (Inlining) → Output
```

---

## 4. Acceptance Criteria

Insgesamt **14** ACs: A1–A9 (Block A) + B1–B5 (Block B).

### Block A — Routing

**A1 — `addressability` vollständig und konsistent.**
Given `config/role-defaults.yaml` mit 84 Rollen, when der Schema-Test läuft, then hat jede
Rolle `routing.addressability` ∈ {`keyword`, `name_only`, `excluded`}; die Verteilung ist
`81 keyword / 2 name_only / 1 excluded`; `excluded` ist genau `orchestrator`; jede
`keyword`-Rolle hat nicht-leere `routing_patterns.keywords` **oder** `.examples`; jede
`name_only`-Rolle hat nicht-leeren `name_only_reason`.

**A2 — Single Source der Aktivierungs-Defaults.**
Given `activation_groups:`, when `resolve_activation_gates(agent_meta_root, config)` läuft,
then wird jedes
Gate (se/knowledge/validator/developer_tiers) aus genau einer expliziten Default-Tabelle
aufgelöst; `config_predicate` ist pro Gruppe präzise (`config_flag` bzw.
`roles_membership` mit `mode: any|all` + Rollenliste); es existiert kein zweiter
SE-Default (`frontmatter.py:471` vs. `config.py:1580` aufgelöst).

**A3 — Eine gemeinsame Aktiv-Menge, Layer 2, kein stiller Drop.**
Given eine gültige `config` (Gate-Quelle; optional eine `template_roles`-Fixture, sonst
lazy via `resolve_template_roles`), when
`get_routing_rules().target_agents`, `build_agent_hints(include_table=True)`-Zeilen und
`build_agent_table()`-Zeilen verglichen werden, then sind die Routing-Ziele exakt
`resolve_active_roles(require_template=True) \ {orchestrator}` und Hints/Tabelle nutzen
dieselbe Layer-2-Menge; jede Abweichung (Rolle aktiv ohne Template bzw. Template ohne
role-defaults-Eintrag, außer `WRAPPER_TEMPLATES`) erzeugt einen deterministischen Eintrag
im `warn_sink`, nie einen stillen Ausschluss.

**A4 — `name_index` vollständig und deterministisch.**
Given ein aktives Routing-Set, when `get_routing_rules()` aufgerufen wird, then enthält
`name_index` genau einen Eintrag pro `target_agents`-Rolle mit `agent`, `short_desc`,
`tier`, `orchestrator_only`, `addressability`, `name_only_reason`; sortiert nach `agent`;
zwei Aufrufe über unveränderter Config liefern gleiche Dicts.

**A5 — Rollen-Adressierbarkeit korrigiert (statisches Schema).**
Given `openscad-developer`, `principal-developer`, `intern-developer`, when die Config
geladen wird (Adressierbarkeit ist aktivierungsunabhängig, §3.4), then hat
`openscad-developer` nicht-leere `routing_patterns` und `addressability: keyword`;
`principal-developer` und `intern-developer` haben `addressability: name_only` +
`name_only_reason`; `orchestrator` ist `excluded`; der Test
`test_roles_without_routing_stay_patternless` ist auf die neue Semantik aktualisiert
(nicht ersatzlos gelöscht).

**A6 — Route-Guard grün, inkl. Snippet-Scope.**
Given `_SCOPE_GLOBS` ist um `snippets/**/*.md` erweitert (Detektor-Logik unverändert) und
der Snippet-Korpus wurde vorab trockengelaufen (RVW-20-Pre-Flight), when
`tests/test_no_role_routes_in_templates.py` läuft, then werden 0 Verstöße der Detektoren
`T-ROUTE-COL`, `T-ROLE-ARROW`, `T-HANDOFF`, `T-NEXT` in Templates, Rules **und Snippets**
gemeldet; Routing lebt ausschließlich in `config/role-defaults.yaml`.

**A7 — Keine Capability-Änderung.**
Given `config/provider-capabilities.yaml`, when der Diff geprüft wird, then ist
`route_intent_tool` für alle Provider unverändert `false`, gibt es keine neuen/entfernten
Capability-Keys, und der Fallback `{{#if ROUTE_INTENT_CALLABLE}}` bleibt bestehen.

**A8 — `name_only`/`excluded` erzeugen keine Keyword-Regel, bleiben aber (bei aktiver
Rolle) erreichbar.**
Given eine Rolle, deren Aktivierung greift — `intern-developer` (keine Gate-Gruppe),
`principal-developer` **bei aktivierter Gruppe `developer_tiers`**, `orchestrator`
unabhängig — when `build_routing_tool_definition()` erzeugt wird, then enthalten `rules[]`
keine Einträge dieser `name_only`-Rollen und keinerlei `orchestrator`-Eintrag;
`orchestrator` ist nie in `target_agents`; aktive `name_only`-Rollen sind in
`target_agents` und `name_index` enthalten. Bei **inaktiver** `developer_tiers`-Gruppe
(Default ohne Whitelist) bleibt `principal-developer` korrekt außerhalb von
`target_agents`/`name_index` — konsistent mit `tests/test_routing_tool_definitions.py:88`.

**A9 — `name_index` wird im Fallback-Pfad verpflichtend konsumiert.**
Given der generierte `orchestrator.md`-Fallback-Zweig, when er gerendert wird, then
enthält er die vertragliche Anweisung, Name-Dispatch über `name_index` zu betreiben, und
weist `name_only`-Rollen als ausschließlich über diesen Kanal erreichbar aus; der
`INTENT_ROUTING_TOOLS`-Payload enthält die `name_only`-Einträge (Test: Prompt-Text +
Payload-Assert).

### Block B — Slimming

**B1 — Wiederkehrende Blöcke zentralisiert, Inline-Duplikate entfernt.**
Given die 21× inline duplizierte `## Anti-Recursion Guard`-Prosa sowie Background-Process-
Guard/`<output-guard>`/Parsing-Boilerplate, when die Templates nach der Änderung geprüft
werden, then ist jede migrierte Inline-Prosa durch eine `{{*_BLOCK}}`-Referenz ersetzt;
kein Template enthält den migrierten Block mehr wörtlich (für Anti-Recursion: 21× inline →
0×; die 5 bestehenden Block-Referenzen bleiben).

**B2 — Äquivalenz-Gate (getrennt byte-identisch / normalisiert).**
Given ein Golden-Set, das **nach Block A und vor Block B** eingefroren wurde, when der
Sync nach der Slimming-Änderung läuft, then gilt:
- **B2a:** Jedes Vorkommen, das vorab als byte-identisch zum kanonischen Snippet-Text
  klassifiziert wurde, ist im generierten Output byte-identisch zur Baseline. Die
  Einrückungs-Einschränkung aus Rev. 4 entfällt: der Inlining-Transform setzt die
  Einrückung der Verwendungsstelle auch auf Folgezeilen (§3.7/RVW-22, Amendment §8.4),
  sodass column-0-, Inline- UND eingerückte Vorkommen B2a-Fälle sind.
- **B2b:** Jedes normalisierte Near-Duplikat ist in einem Diff-Manifest gelistet und
  abschnittsweise semantisch äquivalent (kein verlorener Pflichtsatz: Input-Parsing,
  Output-Guard, Handoff-Format, Anti-Recursion bleiben erhalten).
Der Inlining-Transform aus §3.7 ist die einzige zulässige Quelltransformation.

**B3 — Snippet-Kopiervertrag korrekt.**
Given neu eingeführte Snippets, when der Sync mit `*_SNIPPETS_PATH`-Referenz läuft, then
werden genau die referenzierten Snippets in das Zielprojekt kopiert
(`context.py:2214-2230`-Vertrag); nicht-referenzierte Snippets werden nicht kopiert;
Block-Snippet-Dateien (Inlining-Pfad) folgen der Transform-Regel aus §3.7.

**B4 — Kein Regressions- bzw. Funktionsverlust.**
Given die vollständige bestehende Test-Suite, when sie nach Block A + B läuft, then ist sie
grün und `python3 scripts/sync.py --validate --dry-run` fehlerfrei; die Templates bleiben
je Rolle vollständig (kein verlorener Pflicht-Abschnitt).

**B5 — Reduktionsreport (informativ, kein Hard-Gate).**
Given die Template-Zeilen (Ist: 14.890), when der Sync abgeschlossen ist, then wird die
Zeilen-/Byte-Reduktion als Metrik ausgewiesen; ein konkreter Schwellenwert ist **nicht**
akzeptanzrelevant (Qualität via B2 statt Zeilen).

---

## 5. Risiken + Threat-Model

### 5.1 Risiken

| # | Risiko | Severity | Mitigation |
|---|---|---|---|
| R1 | Aktiv-Mengen divergieren weiter (falsche `template_roles`-Injektion) | Hoch | A3-Test + `warn_sink`; einziger Resolver; lazy Auflösung via `resolve_template_roles` |
| R2 | Semantikverlust beim Slimming (Near-Duplikate verlieren Pflichtinhalt) | Hoch | B2a/B2b + Diff-Manifest + section-level Review |
| R3 | Route-Guard-Verstoß durch Snippet-Ablage | Mittel | A6: Scope um `snippets/**/*.md` erweitert, Detektor-Logik unverändert |
| R4 | `_is_role_enabled`-Migration bricht Bestandsaufrufer | Mittel | §3.2-Migrationsliste + Signatur-Freeze; Tests angepasst |
| R5 | `openscad-developer`-Patterns kollidieren (Overlap) | Mittel | neuer Overlap-Test (IT-7); bewusste Ausnahme dokumentieren |
| R6 | `developer_tiers.mode: all` ist bewusster Behavior-Change-Kandidat | Mittel | Entscheidung O-B; bei `all` kein Verhaltenswechsel |
| R7 | Falsche Byte-Identitäts-Annahme (Vorkommen sind normalisiert) | Mittel | Vorab-Klassifikation erzwungen; B2b + Manifest |
| R8 | Golden-Baseline veraltet/blockiert legitime Änderungen | Niedrig | Baseline versioniert + bewusstes Update nur mit Manifest |

### 5.2 Threat-Model (4 Fragen)

**F1 — Was bauen wir?**
Eine datengetriebene Adressierbarkeits-Schicht (Routing + Name-Index) und eine
Template-Deduplikation im agent-meta-Framework. Verarbeitete Daten: statische
Repo-Configs (`role-defaults.yaml`, `provider-capabilities.yaml`), Template-Markdown und
generierte Agenten-Dateien. Keine Laufzeit-Nutzereingaben, kein Netzwerk, kein
Secret-Handling.

**F2 — Was kann schiefgehen?**
- *Stiller Funktionsverlust:* Rollen verschwinden aus Routing/Tabelle ohne Warnung (R1).
- *Prompt-Injektion via Templates:* externe/Beispiel-Inhalte könnten als Instruktion
  verstanden werden; Slimming darf keine neuen Instruktionsflächen schaffen.
- *Guard-Bypass:* Zentrale Snippets könnten Routing-Inhalte enthalten und so den
  Route-Guard umgehen (R3).
- *Semantik-Drift:* Normalisierung entfernt Sicherheits-/DoD-Pflichtsätze (R2).
- *Supply-Chain:* keine neuen Dependencies (nur Stdlib) — gering.

**F3 — Mitigationen?**
- Warnung statt stillem Drop + Schema-/Coverage-Test (A1, A3).
- Äquivalenz-Gate + Diff-Manifest (B2) verhindert unbemerkten Semantikverlust.
- Route-Guard-Scope wird auf `snippets/**/*.md` erweitert (A6); Detektor-Logik und
  `D-*`-Ausnahmen bleiben unverändert.
- Keine Provider-Name-Branches; Format über Capability-Keys.
- Prompt-Injection-Defense-Snippet bleibt erhalten; Slimming entfernt keine
  Security-Blöcke.
- **Daten-/Instruktionsgrenze (RVW-16):** `name_index`-Felder (`agent`, `short_desc`,
  `name_only_reason`) sind repo-kontrollierte **Daten** und werden nie als
  Routing-/Instruktionsquelle interpretiert; `name_only_reason` ist Freitext und als
  reine Datenfläche zu behandeln.

**F4 — Konsequenzen, wenn es schiefgeht?**
Begrenzt auf agent-meta und dessen generierte Agenten (Entwickler-Tooling). Kein
Produktionsdatenverlust, kein Kundenzugriff. Schlimmster Fall: falsche
Routing-Vorschläge oder ein unvollständiger Prompt — durch Tests + Warnungen sichtbar,
nicht still.

---

## 6. Teststrategie

### 6.1 Bestehende Tests, die betroffen sind

| Test | Betroffen weil | Erwartung |
|---|---|---|
| `tests/test_routing_tool_definitions.py:67-73` | 4 patternlose Rollen ändern sich | Semantik aktualisieren (openscad=keyword, principal/intern=name_only, orchestrator=excluded) |
| `tests/test_routing_tool_definitions.py:399-418` | `route_intent` non-callable | unverändert grün |
| `tests/test_routing_tool_definitions.py:80-88` | `principal-developer`-Gate bei `DEVELOPER_TIERS_ENABLED=false` | **bleibt gültig** (RVW-17): bei inaktiver Gruppe weiterhin nicht im Enum; neuer Komplementär-Test bei aktiver Gruppe |
| `tests/test_routing_tool_definitions.py:89` | `assert "validator" in enum` bricht unter config-only-Gate (RVW-24): mit `config={}` ist `activation_groups.validator` (`roles_membership any ["validator"]`) `false`, `variables.VALIDATOR_ENABLED` ist **keine** Gate-Quelle mehr | **Migration erforderlich:** `config={"roles": ["validator"]}` als Fixture ODER Assertion an die neue Gate-Semantik anpassen; optional `test_validator_gate` als Komplement (§6.2) |
| `tests/test_provider_agnostic_dispatch.py:176-191` | Capability-Erwartung | unverändert grün |
| `tests/test_no_role_routes_in_templates.py` | Scope + Slimming | Scope um `snippets/**/*.md` erweitert, 0 Verstöße |
| `tests/test_se_role_boundary.py:300`, `tests/test_knowledge_engine.py:80-108` | `_is_role_enabled`-Signatur | auf 3-Parameter-Aufruf migriert |
| Agent-Table-/Hints-Tests | gemeinsame Layer-2-Menge | grün, ggf. neue Warn-Assertions |

### 6.2 Neue Tests

- **`test_role_activation_schema.py`** — `activation_groups`-Schema (genau eine
  Default-Tabelle, gültige `config_predicate`), Determinismus (AC A2).
- **`test_role_addressability_coverage.py`** (#779 IT-6) — jede Rolle hat
  `addressability`; `keyword` ⇒ Patterns (keywords **oder** examples); `name_only` ⇒
  Reason; `excluded` genau `orchestrator`; Verteilung 81/2/1 (AC A1, A5).
- **`test_routing_name_index.py`** — `name_index` vollständig, sortiert, idempotent; ein
  Eintrag pro `target_agents` (AC A4).
- **`test_routing_overlap.py`** (#779 IT-7) — Keyword-/Example-Overlap zwischen Rollen
  wird erkannt und mit Rollenliste gemeldet (AC A5, R5).
- **`test_developer_tiers_gate.py`** (RVW-17) — `principal-developer` ist bei **aktiver**
  `developer_tiers`-Gruppe (`all` junior+senior) in `target_agents`/`name_index` und ohne
  `rules[]`-Eintrag; bei **inaktiver** Gruppe fehlt er in beiden — deckungsgleich mit
  `test_routing_tool_definitions.py:88` (AC A5, A8).
- **`test_active_role_call_sites.py`** (RVW-18) — `get_active_agents_data()` und
  `get_routing_rules()` liefern ohne explizite `template_roles` (lazy via
  `resolve_template_roles`) kein `ValueError`; `get_intent_routing_table()` bleibt
  funktionsfähig (AC A3, A6).
- **`test_validator_gate.py`** (RVW-24, Komplement) — `validator` ist in
  `target_agents` bei `config={"roles": ["validator"]}` und fehlt bei `config={}`;
  `VALIDATOR_ENABLED` in `variables` beeinflusst das Gate nicht mehr (AC A2).
- **`test_unified_active_set.py`** — Routing-Ziele == Layer 2 == Hints/Tabelle-Set;
  Abweichung erzeugt deterministischen `warn_sink`-Eintrag, kein stiller Drop (AC A3,
  RVW-06).
- **`test_orchestrator_name_dispatch.py`** — generierter `orchestrator.md`-Fallback nennt
  `name_index`; Payload enthält `name_only`-Einträge (AC A9).
- **`test_route_guard_snippets.py`** — Snippets im neuen Scope enthalten keine
  Routing-Konstrukte (AC A6).
- **`test_template_slimming_equivalence.py`** — Golden-Baseline nach Block A, vor Block B;
  B2a byte-identisch, B2b Diff-Manifest + section-level Äquivalenz (AC B2).
- **`test_snippet_inlining_transform.py`** — Frontmatter-Strip/Whitespace/Normalisierung
  deterministisch; `test_snippet_copy_contract.py` für den `*_SNIPPETS_PATH`-Pfad
  (AC B3).

### 6.3 Testreihenfolge / Gate

1. Block A: Schema-, Coverage-, Name-Index-, Overlap-, Unified-Set-, Name-Dispatch-Tests.
2. **Golden-Baseline nach Block A, vor Block B einfrieren** (verpflichtend, RVW-11).
3. Block B: nach jeder Extraktion `test_template_slimming_equivalence.py` + A6-Guard.
4. Vollständige Suite + `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`.

---

## 7. Offene Entscheidungen (max. 5, priorisiert)

O1 (SE-Default) und O2 (Resolver-Injektion) sind geschlossen: O1 =
`activation_groups.se.default: false` (§3.1), O2 = expliziter `template_roles`-Parameter,
`None` lazy via `resolve_template_roles` aufgelöst (RVW-01/§3.2). Verbleibend:

1. **O-A — Snippet-Ablageort/Naming:** neues `snippets/agents/*.md` vs. bestehendes
   `snippets/orchestrator/`. Vorschlag: `snippets/agents/`.
2. **O-B — `developer_tiers`-Prädikat:** heutige Konjunktion `mode: all`
   (junior+senior) beibehalten vs. auf `mode: any` vereinfachen (bewusster
   Behavior-Change). Vorschlag: `all` beibehalten.
3. **O-C — `name_only` im `target_agents`-Enum:** belassen (Name-Dispatch) vs. nur im
   `name_index`. Vorschlag: belassen.
4. **O-D — Block-Snippet-Frontmatter:** Loader strippt Frontmatter vs. Block-Snippets
   tragen kein Frontmatter. Vorschlag: strippen (einheitlicher Loader).
5. **O-E — Golden-Baseline-Ablage:** committed Golden-Files vs. render-on-demand-Fixture.
   Vorschlag: committed Golden-Files (stabiler Diff in Reviews).

---

## 8. Self-Review

- **Pflichtsektionen vorhanden:** Problem/Ziel/Nicht-Ziele (§1.0/1.9/1.10), Interface
  Contracts (§3), Datenfluss (§1.4, §3.8), Acceptance Criteria (§4, nummeriert), Offene
  Fragen + Risiken (§5, §7), Trace-Anker (§Trace-Anker) ✓.
- **Kein `APPROVED`:** Status `Entwurf (DRAFT)` ✓.
- **Keine Platzhalter / kein `TBD`** ✓. **Nur Spec, kein Plan/Code** ✓.
- **Provider-agnostisch:** keine `if provider ==`; Dispatch über Capability-Keys ✓.
- **AC↔Contract-Mapping (vollständig, 14/14):**
  A1↔§3.4, A2↔§3.1/3.2, A3↔§3.2/3.3, A4↔§3.5, A5↔§3.4, A6↔§3.7/A6-Scope,
  A7↔§2.1.8, A8↔§3.4/3.5, A9↔§3.6; B1↔§3.7, B2↔§3.7, B3↔§1.7/3.7, B4↔§6.1,
  B5↔§4-B5.
- **Verifiziert per Read (Revision 2):** `*-reviewer`-Einträge (`role-defaults.yaml`
  1189/1219/2221/2242/2263/2284) — RVW-02; `provider-expert` in `WRAPPER_TEMPLATES`
  (`frontmatter.py:55,637`) und excluded — RVW-02; `ANTI_RECURSION_BLOCK` 5× Referenzen
  (`developer.md:138`, `orchestrator.md:298`, `_reference-agent.md:160`,
  `sharkord-developer.md:85`, `agent-meta-developer.md:157`) + 21× Inline-Guard — RVW-03;
  `_SCOPE_GLOBS` (`test_no_role_routes_in_templates.py:54`) — RVW-04;
  `_is_role_enabled`-Signatur/Caller (`frontmatter.py:467`, `agents.py:157/197`,
  `config.py:31/658`, `agent_sync.py:524`, Tests) — RVW-05; `route_intent_tool: false` in
  9 Providern — RVW-09/§1.3; `collect_sources`-Ausschluss `WRAPPER_TEMPLATES`
  (`frontmatter.py:637`); Snippet-Kopierlogik `context.py:2214-2230`.
- **Verifiziert per Read (Revision 3):** `_active_role_names`-Aufrufer
  (`delegation_table.py:81` `get_active_agents_data`, `:136` `get_routing_rules`) —
  RVW-18; `test_routing_tool_definitions.py:80-88` (principal-Gate) + `:89`
  (validator-Assertion, Migrationsfall) — RVW-17/RVW-24;
  Snippet-Korpus-Arrows (`snippets/orchestrator/se-mode.md:4,11,13,22,41`,
  `snippets/orchestrator/a2a-protocol.md:4`, 13 Snippet-Dateien gesamt) — RVW-20;
  `config.py:1601/1605-1607` (validator=`any`, developer_tiers=`all`) — RVW-07.
- **Übernommen (nicht neu breit verifiziert):** Template-Zeilenzahlen/Redundanzzählungen
  außer Anti-Recursion (Output-Guard 51×, Background-Process 49×, Parse input 43×),
  #779 IT-6/IT-7.

### 8.1 Revisions-Delta (v1 → v2)

| Finding | Status | Änderung |
|---|---|---|
| RVW-01 (BLOCKER) | **gefixt** | `require_template=True` für Routing/Tabelle; `_active_role_names` mit `require_template`-Parameter; `get_routing_rules` ruft direkt `resolve_active_roles(require_template=True)`; A3 konsistent |
| RVW-02 | **gefixt** | §1.6 korrigiert: alle `*-reviewer` haben Einträge; `provider-expert` = `WRAPPER_TEMPLATES`-Basis (by design); R7/O4 angepasst |
| RVW-03 | **gefixt** | `ANTI_RECURSION_BLOCK` 5× (nicht 0×); B1 auf die 21× Inline-Prosa umformuliert |
| RVW-04 | **gefixt** | `_SCOPE_GLOBS` um `snippets/**/*.md` erweitert; Nicht-Ziel präzisiert; A6 + neuer Guard-Test |
| RVW-05 | **gefixt** | `_is_role_enabled(role, config, agent_meta_root)` + Migrationsliste der Aufrufer |
| RVW-06 | **gefixt** | `warn_sink`-Contract (§3.3) + deterministisches Format + Test-Assert |
| RVW-07 | **gefixt** | `config_predicate` mit `kind`/`mode`/Rollen je Gruppe; Behavior-Change dokumentiert |
| RVW-08 | **gefixt** | Byte-Prämisse ersetzt; B2a/B2b getrennt; Inlining-Transform §3.7 |
| RVW-09 | **gefixt** | Orchestrator-Fallback-Contract §3.6 + AC A9 + Prompt-Test |
| RVW-10 | **gefixt** | A1 an §3.4 angeglichen (keywords **oder** examples) |
| RVW-11 | **gefixt** | B2: Baseline „nach Block A, vor Block B" |
| RVW-12 | **gefixt** | `Status: Entwurf (DRAFT)` + eigene `## Trace-Anker`-Sektion |
| RVW-13 (NIT) | **gefixt** | A6/B3 zusammengeführt; 14 ACs; vollständiges Mapping |
| RVW-14 | **gefixt** | `variables` als Gate-Quelle entfernt; `config` ist einzige Quelle; nur `mirror_variable` |
| RVW-15 | **gefixt / bestätigt** | §1.0 Problem eigenständig; Erwartungstabelle 81/2/1 — im Re-Review zugunsten des Autors entschieden |
| RVW-16 | **gefixt** | F3-Satz zur Daten-/Instruktionsgrenze des `name_index` |
| O1 (SE-Default) | **geschlossen** | `activation_groups.se.default: false`, Behavior-Change dokumentiert |
| O2 (Resolver-Injektion) | **geschlossen, in v3 entschärft** | expliziter `template_roles`-Parameter; `None` wird lazy via `resolve_template_roles` aufgelöst statt fail-closed (RVW-18) |

**Bewusst abgelehnt / abweichend:**
- RVW-15 (v1-Review) „80 keyword / 3 name_only / 1 excluded" war rechnerisch falsch;
  korrekt ist **81 keyword / 2 name_only / 1 excluded** (§1.1). Im Re-Review bestätigt.

### 8.2 Revisions-Delta 2 (v2 → v3, Re-Review)

| Finding | Status | Änderung |
|---|---|---|
| RVW-17 (MAJOR) | **gefixt** | §3.1 präzisiert: `role_patterns` = Gruppen-Mitgliedschaft (Gating), `config_predicate` = Enable-Prädikat; `principal-developer` ist Mitglied von `developer_tiers`, aber nicht Teil des Predikats. §3.4: `addressability` ist statisch + aktivierungsorthogonal. A8 mit Aktivierungs-Vorbedingung („bei aktivierter `developer_tiers`-Gruppe") und Negativ-Klausel inaktiver Gruppe; `test_routing_tool_definitions.py:88` bleibt gültig, Komplementär-Test bei aktiver Gruppe ergänzt |
| RVW-18 (MAJOR) | **gefixt** | `_active_role_names`-Default zurück auf `require_template=False` (back-compat, kein ValueError); interne Aufrufer setzen explizit `True`. Vollständige Call-Site-Tabelle + Migrationsschritte (§3.5). `template_roles=None` wird lazy via `resolve_template_roles` aufgelöst; `get_active_agents_data`/`INTENT_ROUTING_TABLE` bleiben funktionsfähig |
| RVW-19 (MINOR) | **gefixt** | §3.3 listet die `warn_sink`/`template_roles`-Injektionspunkte für alle sechs Builder-Signaturen auf |
| RVW-20 (MINOR) | **gefixt** | §1.8 dokumentiert Bestands-Snippet-Audit (se-mode.md/a2a-protocol.md), erwartete `D-NONROLE`-Exemption + verpflichtendes Pre-Flight-Gate; A6 verlangt 0 Verstöße |
| RVW-21 (MINOR) | **gefixt** | §3.4: `orchestrator` ist unabhängig von der Ableitung immer `excluded` |
| RVW-22 (NIT) | **gefixt** | §3.7 Schritt 3 + B2a: Byte-Identität nur bei übereinstimmender Original-Einrückung; sonst B2b — *diese Norm ist in Rev. 5 superseded, siehe Amendment §8.4* |
| RVW-23 (NIT) | **gefixt** | A3 von `config`/`variables` auf `config` (+ optionale `template_roles`-Fixture) reduziert |

**Rest-Lücken / bewusst offen:**
- RVW-20 ist als **Pre-Flight-Gate** formuliert, nicht als Vorab-Beweis: der Guard-Lauf
  über den Bestands-Snippet-Korpus erfolgt zu Implementierungsbeginn; erwartet 0 Treffer
  via `D-NONROLE`, sonst Snippet-Umschreibung (keine Detektoränderung).
- Der genaue Umfang der bewusst normalisierten Blöcke (Diff-Manifest) wird erst im Plan
  fixiert; B2b verlangt den Nachweis, nicht eine Vorab-Festlegung.
- Reduktionszahl ist bewusst informativ (kein Hard-Gate).

**Keine verbleibenden strittigen Punkte** aus Autorensicht: RVW-15 ist zugunsten der
Autorenfassung entschieden; alle übrigen Findings sind gefixt. Etwaige Re-Review-Restpunkte
können sich nur auf die gewählte RVW-17-Variante (a: Aktivierungs-Vorbedingung) oder das
RVW-20-Pre-Flight (Gate statt Vorab-Beweis) beziehen.

### 8.3 Revisions-Delta 3 (v3 → v4, finales Re-Review)

| Finding | Status | Änderung |
|---|---|---|
| RVW-24 (MAJOR) | **gefixt** | §6.1: Testspanne auf `:80-88` (bleibt gültig) eingegrenzt; `:89` (`assert "validator" in enum`) als expliziter Migrationsfall ergänzt (`config={"roles": ["validator"]}`-Fixture oder angepasste Assertion). §6.2: optionaler Komplementär-Test `test_validator_gate.py` |
| RVW-25 (NIT) | **gefixt** | A8: Whitelist-Erratum „(bzw. bei `principal-developer`-Whitelist)" gestrichen (Whitelist ist AND-Filter nach den Gates) |
| RVW-26 (NIT) | **gefixt** | A2: Signatur `resolve_activation_gates(agent_meta_root, config)` vollständig |
| RVW-27 (MINOR) | **gefixt** | §3.2 `resolve_template_roles`: „generierbar" = `collect_sources \ WRAPPER_TEMPLATES \ {Rollen ohne ROLE_MAP-Eintrag}` (`agents.py:159/:199-204`) |
| RVW-28 (NIT) | **gefixt** | §3.2 `resolve_active_roles`-Docstring: toter ValueError-Zweig entfernt, `agent_meta_root` als Pflichtparameter |

**RVW-24 gefixt per Review-Anweisung; nicht erneut review-verifiziert (Loop-Cap).**

**Finale AK-Anzahl bleibt 14** (A1–A9, B1–B5); keine AK geändert oder entfernt.

**Offene NITs, vor Plan/Merge adressieren:** keine — RVW-25/26/28 sind gefixt, RVW-27 ist
gefixt. Verbleibend nur die bewusst informativen Punkte (Reduktionsreport B5; Diff-Manifest
im Plan) sowie das RVW-20-Pre-Flight-Gate als Implementierungsschritt.

### 8.4 Amendment Rev. 5 (v4 → v5) — RVW-22-Norm an die Implementierung nachgezogen

**Auslöser:** Finding B1 aus Code-Review Runde 2 (Spec-/Implementierungs-Divergenz am
Abnahmekriterium). Betroffen sind genau zwei Stellen: §3.7 Schritt 3 (RVW-22) und AK B2a.
Alle übrigen Abschnitte, AKNummern und Revisions-Deltas bleiben unverändert.

| | Norm |
|---|---|
| **Alt (Rev. 4, abgeschafft)** | „Bei String-Substitution wird nur die **erste** Zeile an der Template-Einrückung positioniert; Folgezeilen übernehmen die Snippet-interne Einrückung." Byte-Identität (B2a) nur bei übereinstimmender Original-Einrückung, sonst B2b. |
| **Neu (Rev. 5)** | Jede **Inhaltszeile** eines mehrzeiligen Wertes wird an der Template-Einrückung der Verwendungsstelle positioniert; Folgezeilen folgen der Verwendungsstelle. Leerzeilen bleiben leer. Column-0- und Inline-Vorkommen unverändert (gleiches Verhalten wie Rev. 4). |

**Warum (b) — die Engine garantierte den Einrückungsvertrag nie über den Kern:** Rev. 4
hatte den Einrückungsvertrag implizit über die *Aufrufkonvention* des Inlining-Transforms
festgeschrieben (`text.strip("\n")` + „das Template liefert die Einrückung"), nicht über
eine Zusicherung in `substitute()`. Ein mehrzeiliger Wert an einer eingerückten
Verwendungsstelle war damit nicht abgesichert. Der Runde-1-Fix
(`_reindent_to_placeholder` in `scripts/lib/variables.py`, verdrahtet über den optionalen
`transform`-Parameter in `scripts/lib/substitution.py`) macht den Vertrag explizit — es
handelt sich um ein **Hardening, nicht um die Korrektur eines beobachteten Fehloutputs**:
für den agent-meta-eigenen Render gab es keinen fehlerhaften Output, die Golden-Baseline
ist unverändert. Die alte Norm war damit nicht „falsch beschrieben“, sondern eine
Zusicherung, die der Kern nicht trug; die Spec wird nachgezogen, statt die
Festlegung zurückzunehmen.

**Auswirkung auf den Produktionsrender (c) — unverändert:** Im Korpus `agents/` gibt es
32 Platzhalter-Vorkommen mit Einrückung (verifiziert per Scan der Muster
`^[ \t]+\{\{[A-Z0-9_]+\}\}`); alle rendern für agent-meta unverändert:
28 davon liegen in `extends:`-Dateien, wo der YAML-Decoder den Patch-Text vor der
Substitution auf column 0 dedentiert — der Transform ist dort No-op. Die restlichen 4
(`EXTRA_VOLUMES`, `EXTRA_ENV_VARS`, `EXTRA_VOLUME_DEFINITIONS` in
`agents/2-platform/sharkord-docker.md`, `GH_ASSETS` in `agents/2-platform/sharkord-release.md`)
liegen in `extends:`-losen Dateien im Body innerhalb eines Code-Fence und sind für
agent-meta leer (kein Output-Delta). Consumer-sichtbar ist die Änderung nur für ein echtes
sharkord-Projekt mit mehrzeiligen `variables:`-Werten — dort ist sie eine **Korrektur**
(docker-compose-Listenitems bzw. Shell-Continuations behalten ihre Einrückung). Der
`### Changed`-Eintrag im `CHANGELOG.md` benennt das explizit.

**Nachweise (d):**
- *Verifiziert den Transform:* `tests/test_block_inlining_indentation.py` —
  `test_multiline_value_is_reindented_to_the_placeholder_indent` und
  `test_reindenting_keeps_the_yaml_literal_block_parseable` (fehlschlagen ohne den Fix),
  ergänzt um `test_reindenting_does_not_indent_blank_lines` (Leerzeile + Trailing-Newline
  ohne whitespace-only Zeile), `test_column_zero_placeholder_is_untouched`,
  `test_single_line_value_at_indent_is_untouched`,
  `test_inline_placeholder_in_a_sentence_is_untouched`.
- *Belegt den No-op in Produktion (grün mit **und** ohne Fix):* dieselbe Datei,
  `test_platform_override_renders_block_at_column_zero` (parametrisiert über
  `sharkord`/`homeassistant`/`agent-meta`),
  `test_homeassistant_documenter_override_renders_same_block_structure` und
  `test_source_templates_reference_the_block_inside_a_yaml_literal`; dazu die
  Golden-Vergleiche in `tests/test_template_slimming_equivalence.py` gegen
  `tests/fixtures/slimming-golden/**`.
- *Leer-zeilen-Regression:* `test_reindenting_does_not_indent_blank_lines` (Blank-Line
  und Trailing-Newline) — schützt vor `git diff --check`/Trailing-Whitespace-Hooks in
  Zielprojekten.
