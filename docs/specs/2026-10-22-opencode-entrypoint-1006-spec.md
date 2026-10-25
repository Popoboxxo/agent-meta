---
spec-id: SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22
title: Opencode-Einstiegspunkt (#1006) — mode primary + default_agent auch auf v1, Gate-Kopplung, Managed-Merge
status: APPROVED
revision: 1.4
review: docs/reviews/2026-10-22-opencode-entrypoint-1006-spec-review.md
rereview: docs/reviews/2026-10-22-opencode-entrypoint-1006-spec-rereview.md
issue: "#1006"
builds-on: SPEC-OPENCODE-RUNTIME-GATE-2026-09-13, docs/specs/2026-09-30-provider-audit-opencode-v2.md (OQ-8)
amends: OQ-8 (Amendment siehe Abschnitt Entscheidungsregister)
---

# Opencode-Einstiegspunkt (#1006) — Spec

> Status: APPROVED (2026-10-22) — Nutzerfreigabe 2026-10-22 (Auftrag: beide Pläne vollständig abarbeiten).
>
> Rev. 1.4 — 2026-10-22: Doku-Korrekturen aus Verifikation (IC-3 `deny_edit`-Ausdruck, Zeilenreferenzen, Problem-2-Wortlaut, AC-03/AC-15-Präzisierung). Rev. 1.3 — 2026-10-22: Nutzerantworten eingearbeitet: OQ-3 entschieden (Variante B bestätigt), OQ-4 als bewusste Grenze mit verifizierter Evidenz dokumentiert (Folge-Issue). Rev. 1.2 — Rereview `CHANGES_REQUESTED` vom 2026-10-22 eingearbeitet: MAJOR-A, MINOR-A..C; Rev. 1.1: MAJOR-1..3, MINOR-1..6)
> Trace-Anker: `spec-id: SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22`
>
> Der Approval-Marker (`Status: APPROVED`) wird ausschließlich vom Nutzer bzw. `concept-reviewer`
> gesetzt, nie vom Autor. Diese Datei enthält Interface-Contracts und Akzeptanzkriterien, keine
> Implementierung. Provider-Unterschiede ausschließlich über Config-Keys/Capability-Flags, nie über
> `if provider == "Name"` (Skill `provider-agnostic`).
> Zeilenangaben beziehen sich auf den Stand von Branch `docs/opencode-v2-1006-plans`
> (2026-10-22) und können driften; maßgeblich sind die Symbole.

## Problem

Auf der Opencode-Surface v1 (Default) ist der Einstiegspunkt kaputt, sobald die Orchestrator-Pflicht
(`orchestrator.mode: strict`) über das Permission-Tier-Gate durchgesetzt wird:

1. **Kein primärer Agent.** `scripts/lib/provider_transform.py` setzt `mode: primary` nur im
   Zweig `mechanism == 'opencode-native-v2'` (`:408-411`). Auf v1 bleibt `mode` `None`, der
   Fallback in `_transform_frontmatter_for_opencode` (`:819`) liefert `subagent`. Der generierte
   `.opencode/agents/orchestrator.md` trägt `mode: subagent` (verifiziert im Repo).
2. **Kein `default_agent`.** `scripts/lib/context.py::apply_settings_surface_shape` (`:1644`) gibt
   `default_agent` nur für `mcp-config.format == "opencode-json-v2"` aus (`:1677-1679`) und für
   jedes andere Format den Inhalt byte-identisch zurück; zudem schreibt
   `_init_provider_settings_json` (`:1683`) die Datei nur beim ERSTELLEN (`log.skip` mit Grund „already exists — not overwritten“, `context.py:1698-1701`). Das eigene `opencode.json` des Repos enthält kein `default_agent`.
3. **Das Gate sperrt trotzdem den Main Chat.** `scripts/lib/isolation.py::_sync_opencode_runtime_gate`
   (`:413`) schreibt bei `strict` + Tier `permission` die Globs `permission.edit["**"]="deny"` und
   `permission.bash["**"]="deny"` (`:407-410`, `:454-466`) in `opencode.json`. Opencode startet ohne
   `default_agent` mit seinem eingebauten Standard-Agenten — der Nutzer landet in einer Session, die
   weder editieren noch Shell nutzen darf und den `orchestrator` (nur Subagent, `@orchestrator`)
   nicht als Einstieg hat.
4. **`edit: allow` im Orchestrator.** `_map_claude_tools_to_opencode_permissions`
   (`provider_transform.py:703-751`) mappt `Write`/`Edit` auf `edit: allow`. Das Template
   `agents/1-generic/orchestrator.md` hat im Frontmatter `tools: [TodoWrite, Agent, Read, Write]` und
   KEIN `edit: allow` — die Erlaubnis entsteht im Mapping (`Write -> edit`). Das generierte
   `.opencode/agents/orchestrator.md` trägt `edit: allow`, `bash: deny` (aus
   `opencode_deny_critical` in `config/provider-tools.yaml:56`). Wird der Orchestrator zum primären
   Agenten (= Main Chat), würde sein Agent-Level-`edit: allow` die globale Sperre für genau den
   Main Chat aufheben, den das Gate sperren soll. Rangfolge per Opencode-Doku belegt (OQ-1): "Agent
   permissions are merged with the global config, and agent rules take precedence"
   (opencode.ai/docs/permissions; letzter passender Match gewinnt).
5. **Bestehende Projekte bekommen den Fix nie.** `default_agent` lebt nur im Create-Pfad; ein
   bestehendes `opencode.json` wird nie angefasst. Der Managed-Merge
   (`_sync_opencode_runtime_gate`) ist der einzige Pfad, der auf bestehende Dateien wirkt.
6. **Mammouth-Falle.** Mammouth nutzt dieselbe Mechanismus-Branch (`frontmatter-mechanism:
   opencode-native`, `ai-providers.yaml:623`) und hat KEIN `primary-role`. Der Code-Default
   `.get('primary-role', 'orchestrator')` (`provider_transform.py:410`, `:525`) würde bei einem naiven
   Fix Mammouth ungewollt zu `mode: primary` machen.

**Root-Cause:** Der v1-Freeze (OQ-8) wurde auf den gesamten Opencode-Output angewandt, obwohl er nur das
Surface-FORMAT (MCP-Form, Frontmatter-Schlüssel) schützen sollte. Der Einstiegspunkt (primärer Agent +
`default_agent`) ist aber eine Voraussetzung dafür, dass das Gate überhaupt sinnvoll ist, und wurde mit
eingefroren.

## Ziel

1. Opencode v1 und v2 emittieren die `primary-role`-Rolle als `mode: primary` (jede andere Rolle
   bleibt wie bisher). Wirkt nur bei **explizit** gesetztem `primary-role`. **Gilt unabhängig von
   `orchestrator.mode` (strict oder nicht): auch nicht-strikte Opencode-Projekte bekommen einen
   primären Orchestrator und `default_agent: orchestrator` (Default-Agent wechselt von `build` auf
   `orchestrator`; der Aufruf per `@orchestrator` entfällt, Einstieg ist Default/Tab) — Verhaltensänderung
   für ALLE Opencode-Projekte, siehe R-8.** Grund: der Merge ist tier-, nicht strict-gesteuert
   (Opencode: Tier `permission`, `config/provider-capabilities.yaml:149`).
2. `default_agent` wird für Opencode (v1 und v2) im Managed-Merge in ein bestehendes `opencode.json`
   geschrieben — mit eigenem State-Key und exaktem Rollback. Vom Nutzer abweichend gesetzter
   `default_agent` wird nie überschrieben (nur Warnung).
3. Die Edit-/Bash-Sperre (Gate) wird an den Einstiegspunkt gekoppelt: der Deny wird nur geschrieben,
   wenn `primary-role` explizit gesetzt ist und diese Rolle generiert wird; sonst nur Warnung.
4. Der primäre Orchestrator hebelt das Gate nicht aus: solange das Gate aktiv ist, emittiert er statt
   `edit: allow` eine Sperre (Ausgestaltung: scoped allow-list `.tmp/**` + `.meta-viz/**`, ADR-5 —
   vom Nutzer bestätigt, 2026-10-22; Skalar `deny` bleibt per leerer Pfadliste schaltbar).
5. Das eigene `opencode.json` des Repos (Self-Sync) konvergiert beim nächsten Sync zu einem
   funktionierenden Einstiegspunkt.
6. Bugfix, kein Major: CHANGELOG-Eintrag unter „Fixed".

## Nicht-Ziele

- Das v1-Surface-FORMAT bleibt frozen: Frontmatter-Schlüsselmenge, MCP-Form (`opencode-json`),
  Settings-Template `templates/configs/OPENCODE.settings-template.json` (Bytes unverändert),
  `subagent_depth`-Handling.
- Mammouth (und jeder Provider ohne explizites `primary-role`) bleibt byte-identisch.
- Kein Schema-Eintrag `primary-role` in `config/project-config.schema.json` (bleibt reiner
  Registry-Key in `config/ai-providers.yaml`).
- Kein `mode: all` (primary + subagent) für den Orchestrator (verworfen, ADR-6).
- Kein v2-Opt-in-Schalter, keine Native-`permissions[]`, kein Plugin-Gate, kein `opencode.jsonc`-
  Cleanup, keine `docs/providers/opencode.md`-Überarbeitung — alles Plan B (separate Spec).
- Kein Create-Pfad-Umbau: `_init_provider_settings_json` und `apply_settings_surface_shape` bleiben
  unverändert (siehe ADR-3, v1-Template-Bytes bleiben frozen).
- **Bewusste Grenze (OQ-4, vom Nutzer bestätigt 2026-10-22): keine Rollback-Garantie bei Tier-Wechsel
  weg von `permission` und bei Provider-Entfernung.** Die Lücke ist NICHT Teil dieses Fixes; sie wird
  als Folge-Issue geführt (Plan A, letzter Task). Verifizierte Evidenz (Stand Branch
  `docs/opencode-v2-1006-plans`, 2026-10-22):
  - (a) *Tier-Wechsel weg von `permission` (z. B. `advisory`):* `_sync_opencode_runtime_gate` wird nur bei
    `provider_runtime_gate_tier(pc, caps) == "permission"` aufgerufen (`scripts/lib/sync_pipeline.py:1308`,
    `scripts/lib/cli_commands.py:283`). Der Rollback-Zweig (`scripts/lib/isolation.py:467-479`) läuft dann
    nie; `permission.edit["**"]`/`permission.bash["**"]` = `"deny"` (`isolation.py:408-410`, `:464`) und
    der State-Namespace `runtime-gate-deny` (`.opencode/agent-meta-state.json`; `isolation.py:41`, `:441`,
    `:494-499`) bleiben stale. Der Wechsel `strict` -> nicht-strict bei Tier `permission` rollt dagegen
    korrekt zurück.
  - (b) *Provider aus `project.yaml` entfernt:* `_sync_stage_legacy_cleanup`
    (`sync_pipeline.py:836-886`) löscht nur `agents_dir`, `AGENTS.md` und das leere Provider-Root;
    `opencode.json` wird nicht angefasst, die State-Datei hält `.opencode/` am Leben -> verwaltete Denies
    und Isolation-Denies (`isolation.py:310-361`) bleiben stale. Der Deaktivierungspfad
    (`scripts/lib/deactivation.py`, `remove_provider_dir`) wurde nur aus der Signatur abgeleitet, nicht
    per Lauf geprüft (Restunsicherheit). Ein Gegenmechanismus existiert nicht
    (`rule_index.cleanup_stale_managed_files` und `agent_sync._cleanup_stale_agents` behandeln nur Dateien).
  - Ergebnis: Lücke bestätigt. Konsequenz für Nutzer: nach Tier-Wechsel/Provider-Entfernung `opencode.json`
    und State-Namespaces manuell bereinigen, bis das Folge-Issue umgesetzt ist (CHANGELOG-Hinweis
    nicht nötig; bestehendes Verhalten, kein Rückschritt durch #1006). Folge-Issue: #1020.
- Keine Änderung der Kimi-Allowlist-Logik (`provider_transform.py:525`); deren Default bleibt.

## Interface Contracts

Alle Pfade relativ zu `/home/hermes/repos/agent-meta`.

### IC-1 `scripts/lib/providers.py` — expliziter Primary-Role-Helper

Ablage in `providers.py` (beide Module `provider_transform.py` und `isolation.py` importieren es
bereits) — vermeidet Kreuz-Lazy-Imports zwischen Transform und Isolation.

```python
def explicit_primary_role(provider_config: dict, provider: str) -> str | None:
    """Declared ``primary-role`` of *provider* or ``None``.

    Returns the value only when ``provider_config[provider]['primary-role']`` is a
    non-empty ``str``. NO code default (unlike the Kimi allow-list default at the
    ``subagents-allowlist`` step). Never raises: missing provider / non-dict entry /
    non-str / empty value -> ``None``.
    """
```

Fehlerpfade: alles Nicht-Gültige → `None` (kein Exception). Wiederverwendung in IC-2 und IC-4.

### IC-2 `scripts/lib/provider_transform.py` — Mode-Ableitung (Zweig `opencode-native`/`-v2`, ersetzt `:408-411`)

Verhalten (Pseudo-Spezifikation, keine Implementierung):

| Mechanismus | `primary-role` explizit & `role == primary-role` | sonst |
|---|---|---|
| `opencode-native` (v1) | `mode='primary'` | `mode=None` (bisher: Template-`mode` oder `subagent`) |
| `opencode-native-v2` | `mode='primary'` | `mode='subagent'` |

Änderung ggü. Ist: (a) v1 emittiert für die Primary-Rolle `primary`; (b) der Code-Default
`'orchestrator'` entfällt für die Mode-Ableitung — ohne explizites `primary-role` wird nie
`primary` emittiert, auch nicht auf v2 (Opencode hat den Key; kein bestehender Provider ist auf v2
ohne Key betroffen, siehe Risiko R-4). Der Branch bleibt mechanism-keyed (kein Provider-Literal).

### IC-3 `scripts/lib/provider_transform.py` — Edit-Sperre für die Primary-Rolle (Ausgestaltung: ADR-5)

```python
def _transform_frontmatter_for_opencode(
    content: str, name: str, description: str, model: str, steps: str,
    generated_from: str, agent_meta_root: Path, temperature: str = "",
    strip_fields: list[str] | None = None,
    quiet_fields: frozenset[str] | None = None,
    mode: str | None = None, subagent_depth: int | None = None,
    deny_edit: bool = False,          # NEU
    edit_allow_paths: tuple[str, ...] = (),   # NEU (ADR-5)
) -> str:
```

Vertrag: `deny_edit=True` ersetzt im berechneten Permission-Block `perms["edit"]` **nur falls
`perms.get("edit") == "allow"`** (d.h. Rolle hat `Write`/`Edit`; Schlüsselreihenfolge unverändert).
Achtung: `edit` steht dank `opencode_deny_critical: [Bash, Write, Edit]` IMMER im Mapping —
`_map_claude_tools_to_opencode_permissions` (`:746-749`) setzt `edit: "deny"` für jede Rolle ohne
`Write`/`Edit`. Ein vorhandenes `perms["edit"] == "deny"` bleibt unverändert (sonst würde ein
Sperr-Mechanismus Rechte erweitern); `deny_edit` wirkt dann nicht. Bei `perms["edit"] == "allow"`:
- `edit_allow_paths == ()` → `perms["edit"] = "deny"` (Skalar).
- sonst → `perms["edit"] = {"*": "deny", <p1>: "allow", <p2>: "allow", …}` (Reihenfolge: `"*"`
  zuerst, da letzter Match gewinnt).

`deny_edit=False` (Default) → Output byte-identisch zu heute. Der Rückgabetyp von
`_map_claude_tools_to_opencode_permissions` (`dict[str, str]`, `:706`) wird für den `edit`-Schlüssel
auf `str | dict[str, str]` erweitert; der Frontmatter-Serializer (`updates["permission"]`, `:845`)
muss verschachtelte Mappings ausgeben können — Plan-Task: Serializer prüfen, ggf. minimal
erweitern (AC-11 testet das gerenderte YAML).

Quelle der Pfade: neuer Schlüssel `opencode_primary_edit_allow: [".tmp/**", ".meta-viz/**"]` in
`config/provider-tools.yaml` (neben `opencode_deny_critical`, `:56`); leere Liste = Skalar `deny`
(Rückfall auf Option A aus ADR-5, ohne Codeänderung).

Aufruf im Zweig aus IC-2: `deny_edit = mode == 'primary' and opencode_runtime_gate_wanted(config, provider,
agent_meta_root, provider_config)` (`mode` aus IC-2). Der Import von `lib.isolation`
(IC-4) erfolgt lazy innerhalb der Funktion (einziger Lazy-Import; `isolation.py` importiert
`provider_transform` nicht, `explicit_primary_role` liegt in `providers.py`, IC-1).

### IC-4 `scripts/lib/isolation.py` — Gate-Wunsch + Einstiegspunkt

```python
def opencode_runtime_gate_wanted(config: dict, provider: str,
                                 agent_meta_root: Path, provider_config: dict) -> bool:
    """True iff the tier-`permission` gate is requested: ``bool(_opencode_runtime_gate_entries(...))``."""

def _opencode_entry_point(provider: str, provider_config: dict,
                          active_set) -> str | None:
    """Primary-role of *provider* if explicit AND generated, else ``None``.

    Explicit: ``providers.explicit_primary_role`` (IC-1, direct import, no lazy import
    needed). Generated: ``active_set is None`` or
    ``role in active_set.roles`` (``scripts/lib/active_set.py::ActiveSet.roles``).
    """
```

`_opencode_runtime_gate_entries` (`:368`) bleibt UNVERÄNDERT (reine Strict/Tier-Entscheidung); die
Kopplung passiert in `_sync_opencode_runtime_gate`. Bestehende Tests der Entries-Funktion bleiben
gültig.

### IC-5 `scripts/lib/isolation.py` — State-Namespace `default-agent`

```python
_STATE_DEFAULT_AGENT_KEY = "default-agent"
# state value: {"value": "<role>", "prior": <str | None>}
```

- `_read_state(state_path, key)` (`:179`): für `key in (_STATE_RUNTIME_GATE_KEY,
  _STATE_DEFAULT_AGENT_KEY)` liefert ein `dict` (leeres `{}` bei fehlend/ungültig), sonst `list`.
- `_write_state` (`:191`) bleibt unverändert (leerer Wert entfernt den Namespace;
  Geschwister-Namespaces bleiben erhalten, Sentinel `_agent-meta` wird gesetzt).
- Bedeutung: `value` = vom Merge geschriebener `default_agent`; `prior` = vorheriger Nutzerwert
  (`None` = Key war nicht vorhanden).

### IC-6 `scripts/lib/isolation.py::_sync_opencode_runtime_gate` — erweiterte Signatur und Logik

```python
def _sync_opencode_runtime_gate(
    project_root: Path, config: dict, provider: str, provider_config: dict,
    agent_meta_root: Path, log: SyncLog, dry_run: bool,
    active_set=None,                      # NEU, optional (rückwärtskompatibel)
) -> None:
```

Logik (normativ):

1. `entry = _opencode_entry_point(provider, provider_config, active_set)`.
2. **Gate-Kopplung:** `wanted = bool(_opencode_runtime_gate_entries(...))`. Effektive Entries =
   Entries nur wenn `entry is not None`. Ist `wanted and entry is None`: **kein** Deny schreiben (ein
   bereits verwalteter Deny wird über den vorhandenen Rollback-Zweig `:467-479` zurückgenommen) und
   `log.warning(...)` mit Text, der `primary-role` und die Konsequenz nennt (Gate würde sonst jeden
   Agenten sperren).
3. **default_agent** (`desired = entry`), `current = existing.get("default_agent")`,
   `st = _read_state(state_path, _STATE_DEFAULT_AGENT_KEY)`:
   - `desired` und kein `st`:
     - `current is None` → schreiben, `st = {"value": desired, "prior": None}`.
     - `current == desired` → nichts schreiben, `st = {"value": desired, "prior": desired}`.
     - sonst (abweichender Nutzerwert) → NICHT überschreiben, `log.warning(...)` (nennt Nutzerwert,
       gewünschte Rolle und — wenn das Gate effektiv geschrieben wird — die Konsequenz „Gate aktiv,
       `<user-agent>` ist gesperrt; `default_agent` auf `<role>` setzen oder Strict für Opencode via
       `provider-overrides` deaktivieren"), kein State. Der Gate-Deny (Schritt 4) wird trotzdem
       geschrieben (Entscheidung 2: Bedingung ist nur `primary-role` + generiert; R-9).
   - `desired` und `st`:
     - `current == st["value"]` → bei `desired != st["value"]` auf `desired` nachziehen und
       `st["value"]` aktualisieren; sonst idempotent.
     - `current != st["value"]` (Nutzer hat nachträglich geändert oder Key gelöscht) → nichts
       schreiben, Warnung (gleicher Text wie oben), State bleibt.
   - `desired is None` und `st`: bei `current == st["value"]` Rollback (`prior is None` → Key
     entfernen, sonst `prior` zurückschreiben); bei `current != st["value"]` Nutzerwert belassen;
     State-Namespace in beiden Fällen entfernen.
   - `desired is None` und kein `st` → nichts.
4. `permission`-Merge (Familien `edit`, `bash`) wie bisher (`:454-479`), mit den effektiven Entries
   aus Schritt 2.
5. Schreiben via `write_checked`; State via `_write_state` pro Namespace nur bei Änderung
   (`runtime-gate-deny` unverändert, `default-agent` NEU). `dry_run` schreibt nie. Parse-Fehler in
   `opencode.json` → früher Return wie bisher (`:437-438`), kein Datenverlust.
6. Log-Zeile `log.action("WRITE", …)` nennt zusätzlich `default_agent`, wenn geändert.

Fehlerpfade: unlesbares `provider-capabilities.yaml` → Tier ≠ permission → `wanted=False`
(unverändert); `active_set is None` (z.B. Unit-Tests) → Einstiegspunkt gilt als generiert.

### IC-7 Aufrufer

- `scripts/lib/sync_pipeline.py:1308-1312` und `scripts/lib/cli_commands.py:283-287`: zusätzlich
  `active_set=active_set` an `_sync_opencode_runtime_gate` übergeben (`active_set` ist in beiden
  Funktionen im Scope: `sync_pipeline.py:1317`, `cli_commands.py:221`). Die Bedingung
  `provider_runtime_gate_tier(pc, caps) == "permission"` bleibt (Tier-Wechsel: OQ-4).

### IC-8 Konfiguration

- `config/ai-providers.yaml`: Opencode behält `primary-role: orchestrator` (`:243`); **Mammouth
  bekommt bewusst KEIN `primary-role`** (Guard). Kommentar am Opencode-Key ergänzen: „v1 und v2
  emittieren die Rolle als `mode: primary`; ohne diesen Key wird nie `primary` emittiert."
  Mammouth: `runtime_gate: advisory` (`config/provider-capabilities.yaml:377`) → der Merge
  (`_sync_opencode_runtime_gate`) läuft für Mammouth strukturell nie (Aufrufer-Guard Tier
  `permission`); der Mammouth-Guard wirkt ausschließlich transform-seitig über IC-1/IC-2.
- `config/ai-providers.yaml:309` `orchestrator_hint` (`@orchestrator`) wird nicht mehr korrekt;
  derzeit in keinem Template gerendert → Hinweistext auf „Default-Agent/Tab" korrigieren
  (Einzeiler im Plan; Doku-Überarbeitung bleibt Plan B).
- `config/provider-tools.yaml`: neuer Schlüssel `opencode_primary_edit_allow` (IC-3).
- `config/project-config.schema.json`, `templates/configs/OPENCODE.settings-template.json`:
  keine Änderung.

## Datenfluss

```
config/ai-providers.yaml (Opencode.primary-role)
      │                                  │
      ▼                                  ▼
provider_transform (pro Rolle)      sync_pipeline / cli_commands (pro Provider)
  providers.explicit_primary_role        active_set (ActiveSet.roles)
  mode primary|subagent                  │
  deny_edit ◄── opencode_runtime_gate_wanted (strict + Tier permission)
      │                                  ▼
      ▼                       _sync_opencode_runtime_gate
.opencode/agents/<role>.md      1. entry = _opencode_entry_point
(mode, permission.edit)         2. Gate-Entries nur bei entry
                                3. default_agent mergen (State: default-agent)
                                4. permission.edit/bash mergen (State: runtime-gate-deny)
                                      │
                                      ▼
                  opencode.json  +  .opencode/agent-meta-state.json
                  (default_agent,    (isolation-deny | runtime-gate-deny |
                   permission)        default-agent — read-modify-write je Namespace)
```

Rollback-Pfad: Sync mit `strict` aus → Entries leer → vorhandener Rollback-Zweig entfernt/restauriert
`**` je Familie. Sync ohne Primary-Rolle (Key entfernt oder Rolle nicht generiert) →
`desired is None` → `default_agent` wird gemäß State restauriert/entfernt, Gate-Deny zurückgenommen.
Der Create-Pfad (`_init_provider_settings_json`) läuft unverändert vor dem Merge; auf einem frischen
v1-Projekt entsteht `opencode.json` aus dem (kommentierten) Template, und der Merge fügt
`default_agent` + ggf. Gate hinzu (dabei werden JSONC-Kommentare verworfen — das tut der Merge heute
schon für Strict-Projekte; siehe R-3).

## Acceptance Criteria

Testdateien sind Vorschläge; der Plan konkretisiert. Alle Tests: `python3 -m pytest <datei> -q`.

- **AC-01 (Goldens-Rebaseline, regressionsfrei):** Given der Baseline-Render-Test
  `tests/test_ac01_render_identity.py` gegen `tests/fixtures/ac01-baseline/hashes.json` (Matrixprojekt
  ist NICHT strikt, d.h. im Orchestrator wird KEIN `edit`-Deny erwartet; `_sync_opencode_runtime_gate`
  läuft trotzdem, weil Opencode Tier `permission` hat), When der Fix umgesetzt ist, Then gilt
  `diff_against_manifest`: **2 geändert** — `Opencode/.opencode/agents/orchestrator.md` (nur
  `mode: subagent` → `primary`) und `Opencode/opencode.json` (nur neuer Key `default_agent`) — und
  **1 hinzugefügt** — `Opencode/.opencode/agent-meta-state.json` (nur Namespace `default-agent` +
  Sentinel `_agent-meta`); alle übrigen Einträge — insbesondere `Mammouth/.mammouth/agents/orchestrator.md`,
  `Mammouth/mammouth.json` und alle anderen Provider — bleiben unverändert. Rebaseline per
  Diff-Review (nicht blind). `tests/fixtures/slimming-golden/` und `tests/fixtures/compact-golden/`
  (nur Claude-Artefakte) bleiben vollständig unverändert. (Verifiziert IC-2, IC-3, IC-6, IC-8.)
- **AC-02 (v1 Primary-Mode):** Given Opencode v1 mit `primary-role: orchestrator`, When Rolle
  `orchestrator` transformiert wird, Then Frontmatter `mode == "primary"`; Rolle `developer` →
  `mode == "subagent"`. (IC-1, IC-2; Test: `tests/test_transform_contracts.py`, bestehender
  `test_opencode_native_v1_stays_subagent` (`:367`) wird zu „v1 primary role emits primary, others
  stay subagent" umgeschrieben.)
- **AC-03 (Mammouth-Guard):** Given Mammouth-Provider-Config ohne `primary-role`, When die Rolle
  `orchestrator` transformiert wird, Then `mode == subagent` für Mammouth; Byte-Identität wird indirekt über die AC-01-Hashes (Plan Task 11) verifiziert; Given dieselbe Config MIT `primary-role: orchestrator` Then `mode == "primary"`.
  (IC-1, IC-2, IC-8.)
- **AC-04 (kein Code-Default):** Given Opencode v2 ohne `primary-role` in der Provider-Config, When
  `orchestrator` transformiert wird, Then `mode == "subagent"` (kein implizites `primary`). (IC-1,
  IC-2; Test: `tests/test_opencode_v2_surface.py`/`tests/test_transform_contracts.py`.)
- **AC-05 (Create-Pfad frozen):** Given v1-Settings-Template, When `apply_settings_surface_shape`
  aufgerufen wird, Then Rückgabe byte-identisch zum Template (`test_v1_settings_template_is_byte_identical`,
  `tests/test_opencode_v2_surface.py:204`, und `tests/test_settings_depth_and_deny.py:85` bleiben
  unverändert grün); v2 emittiert weiterhin `default_agent` aus `primary-role`. (Nicht-Ziel: Create-Pfad.)
- **AC-06 (default_agent schreiben):** Given bestehendes `opencode.json` ohne `default_agent`,
  Opencode mit `primary-role: orchestrator`, Rolle in `active_set.roles`, When
  `_sync_opencode_runtime_gate` läuft, Then enthält `opencode.json` `"default_agent": "orchestrator"` und
  `agent-meta-state.json` den Namespace `default-agent` = `{"value": "orchestrator", "prior": null}`;
  ein zweiter Lauf ist byte-identisch (idempotent). (IC-5, IC-6; Test:
  `tests/test_opencode_runtime_gate.py`.)
- **AC-07 (abweichender Nutzerwert):** Given `opencode.json` mit `"default_agent": "build"`, When der
  Merge läuft, Then bleibt `"build"` unverändert, es wird kein `default-agent`-State geschrieben und
  genau eine `log.warning`, die `build` und `orchestrator` nennt UND die Konsequenz: "Gate aktiv,
  `build` ist gesperrt; `default_agent` auf `orchestrator` setzen oder Strict für Opencode via
  `provider-overrides` deaktivieren" (nur wenn das Gate effektiv geschrieben wird; ohne Strict entfällt
  der Konsequenz-Teil). Der Gate-Deny wird unabhängig davon geschrieben (Entscheidung 2, R-9). (IC-6.)
- **AC-08 (Gleicher Nutzerwert):** Given `"default_agent": "orchestrator"` (vom Nutzer), When der
  Merge läuft, Then keine Dateiänderung; State `prior == "orchestrator"`; ein späterer Rollback
  (AC-09) lässt den Wert stehen. Dasselbe gilt für den v2-Create-Pfad (schreibt `default_agent`
  selbst; erster Merge sieht `current == desired` → `prior = desired`): Wert bleibt nach Entfall von
  `primary-role` stehen (bewusste Grenze, ADR-3). (IC-6.)
- **AC-09 (Rollback default_agent):** Given verwalteter `default_agent` (State vorhanden), When der
  nächste Sync die Rolle nicht mehr generiert bzw. `primary-role` nicht mehr gesetzt ist, Then wird
  `default_agent` entfernt (`prior=null`) bzw. auf `prior` zurückgesetzt, der Namespace aus dem State
  entfernt, Geschwister-Namespaces und Nutzer-Keys bleiben unberührt; hat der Nutzer den Wert
  zwischenzeitlich geändert, bleibt dessen Wert stehen (State trotzdem entfernt). (IC-5, IC-6.)
- **AC-10 (Gate-Kopplung):** Given `strict` + Tier `permission` und Opencode OHNE explizites
  `primary-role` (oder Rolle nicht in `active_set.roles`), When der Merge läuft, Then enthält
  `opencode.json` KEINEN neuen `permission.edit["**"]`/`permission.bash["**"]`-Deny, ein bereits
  verwalteter Deny wird zurückgenommen (Prior wiederhergestellt) und es gibt eine `log.warning`, die
  `primary-role` nennt. Given `primary-role` gesetzt und generiert → Deny wie bisher (bestehende
  Gate-Tests `tests/test_opencode_runtime_gate.py` bleiben mit Fixture-Anpassung
  `primary-role: orchestrator` bzw. angepasster Assertion grün, Liste in AC-15). Pipeline-Ebene
  (neuer Test in `tests/test_runtime_gate_wiring.py`): strict + Tier `permission` ohne `primary-role`
  → kein Deny in `opencode.json` + Warning. (IC-4, IC-6.)
- **AC-11 (edit-Sperre am Orchestrator, ADR-5):** Given `strict` + Tier `permission` + `primary-role`
  und `opencode_primary_edit_allow: [".tmp/**", ".meta-viz/**"]` (Default-Empfehlung), When der
  Orchestrator (Template `tools` enthält `Write`) für Opencode transformiert wird, Then
  `permission.edit == {"*": "deny", ".tmp/**": "allow", ".meta-viz/**": "allow"}` (Schlüsselreihenfolge
  `"*"` zuerst, im gerenderten YAML geprüft); Given `opencode_primary_edit_allow: []`, Then
  `permission.edit == "deny"` (Skalar). Given `strict` aus ODER Tier ≠ permission ODER Rolle ≠
  Primary-Rolle, Then `permission.edit == "allow"` wie bisher (`developer` unverändert). Given eine
  Primary-Rolle OHNE `Write`/`Edit` im Template (Mapping liefert `edit: "deny"` aus
  `opencode_deny_critical`) und aktives Gate, Then bleibt `permission.edit == "deny"` (Skalar)
  unverändert — kein Mapping, keine Rechte-Erweiterung, unabhängig von `opencode_primary_edit_allow`.
  `bash: deny`, `task`, `read`, `todowrite` unverändert. (IC-3, IC-4.)
- **AC-12 (Self-Sync):** Given das eigene Repo (`.meta-config/project.yaml`: `orchestrator.strict:
  true`), When `python3 scripts/sync.py` läuft, Then (a) `.opencode/agents/orchestrator.md` hat
  `mode: primary` und `permission.edit` gemäß AC-11 (Variante B, vom Nutzer bestätigt (OQ-3):
  `{"*": deny, ".tmp/**": allow, ".meta-viz/**": allow}`), (b) `opencode.json` enthält zusätzlich
  `"default_agent": "orchestrator"` bei erhaltenen Keys (`subagent_depth`, `plugin`, `mcp`,
  `permission.edit/bash["**"]="deny"`), (c) `.opencode/agent-meta-state.json` enthält die
  Namespaces `runtime-gate-deny` (unverändert) und `default-agent`, (d) ein zweiter Sync ist
  idempotent, (e) `python3 scripts/sync.py --validate` ist grün.
- **AC-13 (Namespace-Koexistenz):** Given alle drei Namespaces (`isolation-deny`, `runtime-gate-deny`,
  `default-agent`) im State, When ein Writer seinen Namespace schreibt/entfernt, Then bleiben die
  anderen unverändert (`_read_state` liefert dict für beide dict-Keys, list für `isolation-deny`).
  (IC-5; Test: `tests/test_opencode_runtime_gate.py` ergänzt um `default-agent`.)
- **AC-14 (Parse-Fehler/Dry-Run):** Given nicht parsebares `opencode.json`, When der Merge läuft,
  Then bleibt die Datei unverändert und es wird eine Warnung geloggt; Given `dry_run=True`, Then
  weder `opencode.json` noch State werden geschrieben. (IC-6.)
- **AC-15 (Bestehende Tests):** (a) unveränderte Tests bleiben grün: `tests/test_surface_version_selection.py`,
  `tests/test_provider_config_contracts.py` (`:178`), `tests/test_settings_depth_and_deny.py`,
  `tests/test_opencode_v2_surface.py` (inkl. `:204`), `tests/test_agents_frontmatter.py:142`
  (Rolle `code-reviewer`, ohne `primary-role` → `mode: subagent`), `tests/test_artifact_contracts.py`
  und `tests/test_surface_version_consistency.py:241` (Fixtures setzen `default_agent` selbst);
  `python3 scripts/sync.py --validate` und die Szenario-Suite bleiben grün (nach Rebaseline AC-01).
  (b) **Anzupassende Tests mit Soll-Assertion** (vollständige Liste; der Plan greppt vor Umsetzung
  nach `default_agent`, `mode: subagent`, `primary-role`, `edit.*allow` erneut nach Nachzüglern):
  1. `tests/scenarios/asserts/69-opencode-v2-surface.sh:141` — `assert "default_agent" not in doc`
     entfällt; Teil 1b prüft künftig auf v1 `doc["default_agent"] == "orchestrator"` und
     `orchestrator.md` `mode: primary`; das v1/unset-`cmp` der übrigen Artefakte bleibt. Kopfkommentar
     `:20-23` („v1 … byte-identical … no `default_agent`") und Registry-Zeile
     `tests/scenarios/registry.md:116` entsprechend umformulieren.
  2. `tests/test_transform_contracts.py:367` `test_opencode_native_v1_stays_subagent` → „v1 primary
     role emits primary, others stay subagent" (AC-02); zusätzlich Mammouth-/Kein-Default-Fälle
     (AC-03/AC-04).
  3. `tests/test_runtime_gate_wiring.py:182-208` (`test_strict_sync_writes_mapping_deny`,
     `test_single_provider_strict_writes_deny`): `_provider_config()` bekommt `primary-role:
     orchestrator`, sonst schreibt IC-6 Schritt 2 keinen Deny mehr; Soll: Deny `edit["**"]`/`bash["**"]`
     wie bisher + `default_agent == "orchestrator"`. Neuer Test siehe AC-10.
  4. `tests/test_opencode_runtime_gate.py:333` (`test_absent_config_is_created_with_managed_block`, Assert ≈ `:352`):
     exakter Vergleich `data == {"permission": …}` → erwartet zusätzlich `"default_agent":
     "orchestrator"`; übrige Gate-Fixtures dieser Datei bekommen `primary-role: orchestrator`;
     Ergänzung Namespace `default-agent` (AC-13).
  5. `tests/test_ac01_render_identity.py` + `tests/fixtures/ac01-baseline/hashes.json`: Rebaseline
     (AC-01).
- **AC-16 (CHANGELOG):** `CHANGELOG.md` enthält unter `## [Unreleased]` einen Abschnitt `### Fixed`
  mit dem Eintrag aus „CHANGELOG-Eintrag".

## Entscheidungsregister

Verbindliche Nutzerentscheidungen 1–5 sowie die Bestätigungen zu OQ-3/OQ-4 vom 2026-10-22 (ADR-Kurzform: Kontext → Entscheidung → Konsequenz).

| # | Entscheidung | Konsequenz |
|---|---|---|
| 1 | v1-Freeze für den Einstiegspunkt aufbrechen: `mode: primary` + `default_agent` auch auf v1, als **Bugfix** deklariert (OQ-8-Amendment unten). Mammouth wird nur bei explizit gesetztem `primary-role` primary. | IC-1/IC-2/IC-6/IC-8; Rebaseline AC-01 (nur Opencode-Orchestrator). Code-Default `'orchestrator'` für die Mode-Ableitung entfällt (R-4). |
| 2 | Shell-/Edit-Sperre an Einstiegspunkt koppeln: Deny nur bei gesetztem `primary-role` und generierter Rolle, sonst nur Warnung. | IC-4/IC-6 Schritt 2; AC-10. Eine Strict-Konfiguration kann das Gate nicht mehr „leer“ schalten, ohne dass ein Einstieg existiert. |
| 3 | `default_agent` im Managed-Merge (`_sync_opencode_runtime_gate`) mit eigenem State-Key und Rollback; Nutzer-abweichender Wert wird nicht überschrieben, nur gewarnt. | IC-5/IC-6; AC-06…AC-09. |
| 4 | `edit: allow` im Orchestrator im selben Fix lösen — **Korrektur:** das Template hat kein `edit: allow`, es entsteht im Mapping (`Write → edit`); Ansatzpunkt ist `provider_transform` (IC-3), nicht das Template. Rangfolge per Doku belegt (OQ-1). Ausgestaltung Skalar vs. scoped allow-list: ADR-5. | IC-3/IC-4; AC-11. |
| 5 | Kein Major; CHANGELOG „Fixed“. | AC-16. |
| OQ-3 | Edit-Sperre des Primär-Orchestrators: scoped allow-list (Variante B: `.tmp/**` + `.meta-viz/**`) statt Skalar `deny`. **Vom Nutzer bestätigt, 2026-10-22; bleibt Default, OQ-3 geschlossen.** | ADR-5, IC-3, AC-11/AC-12; Rückfall auf A weiterhin per `opencode_primary_edit_allow: []` ohne Codeänderung. |
| OQ-4 | Rollback-Lücke bei Tier-Wechsel/Provider-Entfernung ist NICHT Teil von Fix A. **Vom Nutzer bestätigt, 2026-10-22.** | Bewusste Grenze unter Nicht-Ziele (verifizierte Evidenz dort); Folge-Issue als letzter Plan-Task (Plan A, Task 16), angelegt als #1020. |

Zusätzliche Spec-Entscheidungen:

- **ADR-1 (explizit statt Default):** `providers.explicit_primary_role` ersetzt den Code-Default für die Mode-
  Ableitung. Alternative „Mammouth-Sonderfall per Provider-Literal" verworfen (Verstoß
  `provider-agnostic`). Alternative „`primary-role` ins Projekt-Schema" verworfen (zusätzliche Surface
  ohne Bedarf; Registry-Key genügt). Ablage in `providers.py` statt `provider_transform.py`/
  `isolation.py`, um Kreuz-Lazy-Imports zu vermeiden.
- **ADR-2 (Merge statt Create-Pfad):** `default_agent` wird ausschließlich im Managed-Merge
  geschrieben, weil nur dieser auf bestehende Dateien wirkt und State/Rollback hat. Alternative
  „Template erweitern" verworfen (bricht v1-Byte-Freeze, hartkodierte Rolle). Evidenz, dass
  `default_agent` den v1-Freeze nicht schema-seitig bricht: Opencode 1.18.31 dokumentiert/akzeptiert
  den Key (`docs/analysis/2026-09-30-provider-audit-runtime-consolidation.md:103`); Doku
  (opencode.ai/docs/config): "The default agent must be a primary agent … will fall back to "build"
  with a warning" — begründet die Kopplung `mode: primary` ↔ `default_agent`.
- **ADR-3 (Create-Pfad unverändert):** Daher bleibt `apply_settings_surface_shape` v1-byte-identisch;
  v2 behält seinen Create-Time-`default_agent`. Beide Pfade konvergieren, weil der Merge
  `current == desired` idempotent behandelt (AC-08). **Bewusste Grenze (v2-Rollback):** auf v2
  schreibt der Create-Pfad `default_agent`; der erste Merge sieht `current == desired` ohne State →
  `prior = desired`. Entfällt später `primary-role`, „restauriert" der Rollback denselben Wert — der
  ursprünglich von agent-meta erzeugte Key bleibt dauerhaft stehen. Akzeptiert (Datei ist
  maschinenverwaltet, Fall selten); auf v1 neu erzeugte Dateien sind nicht betroffen.
- **ADR-4 (Entries-Funktion unverändert):** Die Kopplung liegt im Sync, nicht in
  `_opencode_runtime_gate_entries`, damit dessen Vertrag (Strict/Tier) und seine Tests stabil bleiben.
- **ADR-5 (Edit-Sperre des primären Orchestrators: Skalar `deny` vs. scoped allow-list):**
  *Kontext:* Unter Strict sperrt das Gate global `edit`/`bash`; der primäre Orchestrator hätte per
  Agent-Level-`edit: allow` Vorrang (OQ-1) und müsste daher selbst gesperrt werden (Entscheidung 4).
  Der Orchestrator hat `bash: deny` (`opencode_deny_critical`) und verliert bei Skalar-`deny` jeden
  Schreibpfad. Das Template führt `Write` aber für „checkpoints/artifacts"
  (`agents/1-generic/orchestrator.md:344`, §9 Context guard & checkpointing, Ledger/Checkpoint-
  Recovery `:60`); das eigene Repo hat `checkpointing: true`; Checkpoints liegen unter
  `.meta-viz/` (`scripts/lib/orchestration.py:130`, `providers.py:299`), Zwischenartefakte unter `.tmp/`.
  *Optionen:* **A** Skalar `edit: deny` — maximal konsistent mit „Router, nicht Worker", einfach;
  verliert Checkpoint-/Artefakt-/Tier-B-Progress-Schreibpfad (Funktionsverlust unter Strict+Opencode).
  **B** scoped allow-list `edit: {"*": "deny", ".tmp/**": "allow", ".meta-viz/**": "allow"}` (Agent-
  Regeln haben Vorrang, letzter Match gewinnt) — Quell-/Repo-Dateien bleiben gesperrt (Entscheidung 2
  erfüllt), Orchestrator-Infrastruktur bleibt funktionsfähig; etwas mehr Surface (Pfadliste,
  verschachteltes YAML im Frontmatter, Pfade müssen zu Checkpoint-Konfiguration passen).
  *Entscheidung (vom Nutzer bestätigt, 2026-10-22; OQ-3 geschlossen):* **B**; die Pfadliste liegt in
  `config/provider-tools.yaml: opencode_primary_edit_allow`, leere Liste = A ohne Codeänderung.
  *Konsequenz:* IC-3/AC-11 beschreiben beide Varianten; Entscheidung 2 (Sperre) bleibt bindend,
  B ist nur Ausgestaltung. Risiko: Pfade driften von `checkpoint_dir`-Konfiguration (R-2).
- **ADR-6 (`mode: primary` statt `mode: all`):** `all` (primary + subagent) würde `@orchestrator`
  weiter erlauben (Rückwärtskompatibilität für nicht-strikte Projekte), macht aber den Orchestrator
  auch für andere Agenten per Task-Tool aufrufbar (Router-Rekursion, widerspricht der Singleton-Regel)
  und weicht von der v2-Semantik (`primary`, Entscheidung 1) ab. Verworfen; Verhaltensänderung in R-8.

### OQ-8-Amendment (Text für `docs/specs/2026-09-30-provider-audit-opencode-v2.md`, Abschnitt OQ-8 und Tabellenzeile `:26`/`:410`)

> **Amendment A2 (2026-10-22, Issue #1006):** Der v1-Freeze aus OQ-8 gilt für das Surface-**Format**
> (Frontmatter-Schlüsselmenge, MCP-Form, Settings-Template-Bytes), nicht für den **Einstiegspunkt**.
> `mode: primary` für die in `config/ai-providers.yaml` explizit deklarierte `primary-role` sowie
> `default_agent` in `opencode.json` werden auch auf Surface v1 ausgegeben (Bugfix: ohne Einstiegspunkt
> sperrt das Permission-Tier-Gate den Main Chat). Provider ohne explizites `primary-role` (z.B.
> Mammouth) bleiben unverändert. v2 bleibt opt-in; der Default-Flip bleibt dem nächsten Major
> vorbehalten. Referenz: `SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22`.

Gleichlautender Querverweis (eine Zeile) in `docs/specs/2026-09-30-provider-audit-opencode-v2-design.md:589`
und `docs/specs/2026-10-03-admin-ui-opencode-surface-amendment.md:42,:67` (Plan-Task, kein Inhalt
dieser Spec).

### CHANGELOG-Eintrag (unter `## [Unreleased]`)

```markdown
### Fixed
- **Opencode entry point (#1006)**: the orchestrator is now generated as `mode: primary` and
  `default_agent` is written to an existing `opencode.json` (managed merge with own state key and
  rollback) on surface v1 as well, so the strict permission-tier gate no longer locks the main chat
  out of every agent. The edit/bash deny is only written when an explicit `primary-role` is
  generated (otherwise a warning); the primary orchestrator no longer emits `edit: allow` while the
  gate is active (writes limited to `.tmp/**` and `.meta-viz/**`). A user-set, different
  `default_agent` is never overwritten (warning only; under strict the gate still applies, so set
  `default_agent` to `orchestrator`). Providers without an explicit `primary-role` (Mammouth) stay
  byte-identical.
  **Behavior change for all Opencode projects (strict or not):** the default agent is now
  `orchestrator` instead of `build`, and `@orchestrator` no longer invokes it (it is a primary agent;
  switch via Tab/default).
```

## Offene Fragen

| # | Frage | Default-Annahme (bis geklärt) | Verifikationsweg |
|---|---|---|---|
| OQ-1 | **Permission-Rangfolge in Opencode:** überschreibt ein Agent-Level-`permission.edit: allow` einen globalen `permission.edit: {"**": "deny"}`? **Per Doku belegt:** "Agent permissions are merged with the global config, and agent rules take precedence" (opencode.ai/docs/permissions, Abschnitt Agents; "last matching rule wins"). Damit ist IC-3 notwendig (sonst hebt der primäre Orchestrator das Gate auf); `developer` & Co. dürfen weiterhin editieren. | Beantwortet (siehe links). | Optional (Bestätigung, kein Blocker): Plan-Task, falls Binary vorhanden, Probe in Wegwerf-Verzeichnis unter `.tmp/`: globales edit-deny + Agent mit `edit: allow` bzw. scoped Mapping (ADR-5), Schreibversuch über `opencode run`; Ergebnis dokumentieren. Falls entgegen der Doku Global gewinnt: IC-3 wirkungslos, das Gate sperrt dann auch Subagents → Folge-Issue, Entscheidung 4 neu bewerten. |
| OQ-2 | Soll der primäre Orchestrator unter aktivem Gate `edit: deny` oder `edit` weggelassen emittieren? | `deny`/scoped Mapping (explizit, unabhängig von der Rangfolge lesbar; Weglassen verlöre die explizite Absicht, Entscheidung 4). | Durch ADR-5 abgedeckt; optionale OQ-1-Probe. |
| OQ-3 | ~~Skalar `edit: deny` (A) oder scoped allow-list (B)?~~ **ENTSCHIEDEN (vom Nutzer bestätigt, 2026-10-22): B** (`.tmp/**` + `.meta-viz/**`); geschlossen. | B: Orchestrator behält Checkpoint-/Artefakt-Schreibpfad (§9), Quell-/Repo-Dateien bleiben gesperrt. A = `opencode_primary_edit_allow: []`, ohne Codeänderung. | Erledigt (Register). |
| OQ-4 | **Tier-Wechsel-/Provider-Entfernungs-Rollback-Lücke:** `sync_pipeline.py:1308` und `cli_commands.py:283` rufen den Merge nur bei `provider_runtime_gate_tier(pc, caps) == "permission"`. Wechselt das Tier (oder wird Opencode aus der Provider-Liste entfernt), bleiben verwalteter Deny, `default_agent` und State stehen. **ENTSCHIEDEN (vom Nutzer bestätigt, 2026-10-22): bleibt NICHT Teil von Fix A; bewusste Grenze (siehe Nicht-Ziele, verifizierte Evidenz), Folge-Issue.** | Folge-Issue #1020 (nach Merge von Plan A, Task 16). Vorschlag dort: Rollback-Aufruf von der Tier-Bedingung entkoppeln, sobald ein State-Eintrag existiert; Rollback-Helper in `_sync_stage_legacy_cleanup` vor dem State-Löschen. Nicht aufgenommen, weil der Aufruf provider-agnostisch gated werden müsste, ohne `.opencode/…` fest zu verdrahten (Risiko von Fehlrollbacks für fremde Provider). | Geschlossen; Folge-Issue #1020 angelegt (2026-10-24). |
| OQ-5 | Fehlt `active_set` im Aufrufer (`None`), gilt die Primary-Rolle als generiert. Reicht das für `--test`-Repos und Unit-Tests? | Ja; beide produktiven Aufrufer übergeben `active_set` (IC-7). | Test in AC-10 mit und ohne `active_set`. |
| OQ-6 | `default_agent` und Gate nur unter Tier `permission`: Reicht das, falls ein zukünftiger Provider denselben Einstiegspunkt ohne Tier braucht? | Ja (YAGNI); der Aufrufer-Guard bleibt. | Beim ersten Bedarf neues Issue. |

## Risiken

- **R-1 Rangfolge (OQ-1):** per Doku belegt (Agent-Regeln haben Vorrang); Restrisiko Abweichung des
  Opencode-Runtime-Verhaltens von der Doku (Gate wirkungslos oder alle Agenten gesperrt). Mitigation:
  optionale Probe; IC-3 isoliert und per Flag (`deny_edit`) abschaltbar.
- **R-2 Orchestrator unter Strict+Opencode verliert Schreibrechte:** betroffen sind Checkpoints/
  Artefakt-Archiv (§9 Context guard & checkpointing, `.meta-viz/checkpoints/`), Tier-B-Progress-
  Dateien und `.tmp/`-Artefakte. Bei Option A (Skalar `deny`) fallen alle weg (Funktionsverlust,
  Checkpoint-Recovery nicht nutzbar); bei Option B (Default) bleiben sie über die scoped allow-list
  erhalten, Quell-/Repo-Dateien bleiben gesperrt. Restrisiko B: Pfadliste driftet von konfiguriertem
  `checkpoint_dir`/Artefaktpfad (`progress.checkpoint-dir` ist konfigurierbar) → Schreibfehler zur
  Laufzeit. Mitigation: Liste in `provider-tools.yaml`, AC-11 prüft Rendering; Hinweis im CHANGELOG;
  Nicht-Strict-Projekte unberührt.
  **Restrisiko Pfad-Semantik (unbelegt):** opencode.ai/docs/permissions definiert `*`/`?`, nicht `**`,
  und sagt nicht, ob `edit`-Patterns gegen relative oder absolute Pfade matchen (Beispiele mischen
  beides). Matcht Opencode absolut, greifen `.tmp/**`/`.meta-viz/**` nie → Option B degradiert
  stillschweigend zu A (fail-closed: es wird nie mehr erlaubt, nur weniger; kein Sicherheitsproblem,
  aber das ADR-5-Ziel wird verfehlt). Die Pfad-Semantik gilt als „nicht belegt", bis die optionale
  OQ-1-Probe sie belegt; der Plan führt sie als eigene Zeile im Evidenzdokument (Task 1, „nicht
  belegt" zulässig) und in Task 8 als markierte Unsicherheit.
  **Plan-Ledger-Fallback gesperrt:** die Checkbox-Pflege in `docs/plans/*.md`
  (`rules/1-generic/plan-ledger.md:36-38`: Writer-Skript braucht `bash` = `deny`, manueller Edit als
  Fallback) ist dem Opencode-Orchestrator unter Strict auch mit Option B verwehrt (`docs/plans/**` ist
  nicht in der allow-list und wird bewusst nicht aufgenommen: Repo-Dateien bleiben gesperrt). Akzeptiert:
  Plan-Ledger-Checkboxen werden nur via Subagent gepflegt; Folge-Issue, falls das praktisch stört.
- **R-3 JSONC-Kommentare:** Der Merge schreibt via `json.dumps`; auf einem frisch erzeugten v1-
  `opencode.json` gehen Template-Kommentare beim ersten Merge verloren (auch bisher bei Strict). Die
  Datei ist maschinenverwaltet; akzeptiert.
- **R-4 Verhaltensänderung v2 ohne Key:** v2 ohne `primary-role` emittierte bisher implizit
  `primary` für `orchestrator`. Nur Opencode nutzt v2 und hat den Key; Test AC-04 fixiert das neue
  Verhalten.
- **R-5 Goldens-Drift:** Rebaseline verdeckt versehentliche Änderungen. Mitigation: AC-01 verlangt
  Diff-Review und beschränkt die erlaubten Änderungen auf 2 geänderte + 1 hinzugefügtes Opencode-Artefakt.
- **R-6 Koordination mit Plan B:** `context.py`/`isolation.py` werden von Plan B/C ebenfalls
  angefasst; Merge serialisiert (A vor B/C).
- **R-7 Stale State im Self-Sync:** Das Repo-State-File hat noch keinen `_agent-meta`-Sentinel
  (älter als #802); `_write_state` setzt ihn beim ersten Schreiben — harmlos, aber Diff sichtbar.
- **R-8 Verhaltensänderung für alle Opencode-Projekte:** der Merge ist tier-, nicht strict-gesteuert →
  auch nicht-strikte Projekte bekommen `default_agent: orchestrator` und einen primären Orchestrator
  (`edit: allow`); Default-Agent wechselt von `build` auf `orchestrator`, `@orchestrator` entfällt.
  Mitigation: CHANGELOG-Hinweis (Bugfix-Eintrag), `mode: all` als verworfene Alternative (ADR-6),
  Nutzer kann `default_agent` selbst setzen (wird nie überschrieben, AC-07).
- **R-9 Lockout bei abweichendem Nutzer-`default_agent` unter Strict:** setzt der Nutzer `default_agent`
  auf z.B. `build` (oder löscht den Key nachträglich), wird der Gate-Deny trotzdem geschrieben
  (Entscheidung 2: Bedingung nur `primary-role` + generiert) → Main Chat landet im gesperrten Agenten,
  das Symptom aus #1006. Korrekt gemäß Entscheidung, aber unbenannt gewesen; Mitigation: Warnung mit
  Konsequenz und Abhilfe (AC-07, IC-6). Guard bleibt Convention boundary
  (`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).

## Trace-Anker

spec-id: SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22
