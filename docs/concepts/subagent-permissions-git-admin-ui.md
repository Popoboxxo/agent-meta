# Technische Spezifikation — Subagent-Permission-Policy & Admin-UI-Sektion „Git"

- **Status:** Draft v2 (Review-CHANGES_REQUESTED B1/B2/M1-M5/m1-m8/n1-n3 eingearbeitet)
- **Betroffener Branch:** `feat/subagent-permissions-git-admin-ui`
- **Umfang:** 2 Features, 1 Admin-UI-Erweiterung, 1 Infrastruktur-Wartbarkeit
- **Nicht in dieser Spec:** Implementierung, Push/Tag/Release, Änderungen an `.agent-meta/`-Submodulen
- **Revision:** v2 ersetzt v1 vollständig; die Änderungen je Review-Finding sind in §13 dokumentiert.

---

## 1. Scope & Kontext

### 1.1 Feature A — Subagent-Permission-Policy (`subagent_permissions`)

Neuer, global aktivierbarer Modus, der Subagenten-Dispatches über eine deklarative
allow/deny-Anforderung absichert und das strukturierte Rückgabeformat
(`STATUS` / `RESULT` / `ARTIFACTS`) verbindlich macht.

- **Was gebaut wird:** Config-Key `subagent_permissions` mit `mode` ∈ `{strict, warn, off}`
  (Framework-Default `off`) und per-Provider-Override-Map `provider-overrides`; ein
  deterministisches Precedence-Resolve; Prompt-Rendering (provider-agnostisch); ein harter
  Sync-Time-Validator; ein Consistency-Check.
- **Was explizit NICHT gebaut wird:** Ein Runtime-Dispatch-Gate im Agenten-Harness. Das ist
  provider-agnostisch nicht umsetzbar (siehe §8, §10). Die Policy ist auf **allen** Providern
  prompt-basiert plus Sync-Time-Validierung.
- **Betroffene Subsysteme:** `scripts/lib/variables.py`, `scripts/lib/subagent_permissions.py`
  (neu), `scripts/lib/config.py`, `scripts/lib/sync_pipeline.py`, `scripts/lib/rules.py`,
  `scripts/lib/standalone.py`, `scripts/lib/consistency/`, `scripts/consistency-check.py`,
  `scripts/lib/cli_commands.py`, `rules/1-generic/`, `agents/1-generic/orchestrator.md`,
  `config/project-config.schema.json`, `docs/ui/admin-ui.html`.

**Capability-Quelle (B1-entscheidend):** Es gibt zwei getrennte Registries:

| Frage | Registry | Zugriff |
|---|---|---|
| Wird Subagenten-Dispatch überhaupt unterstützt? | `config/provider-capabilities.yaml` | `load_provider_capabilities(root).get(provider, {})` → **Top-Level-Boolean** `subagent_dispatch` |
| Sind PreToolUse-Hooks dieses Providers tatsächlich gespiegelt? | `config/ai-providers.yaml` | `providers.provider_hooks_supported(pc)` (`has_hooks` + verifiziertes `hook_protocol`) |

`provider_has_capability(pc, "subagent_dispatch")` / `("hooks")` ist **falsch**: `pc` ist der
`ai-providers.yaml`-Eintrag mit einer Liste `capabilities: [...]`; `subagent_dispatch`/`hooks`
sind dort keine Listeneinträge. Der Consistency-Check muss `load_provider_capabilities` bzw.
`provider_hooks_supported` nutzen (analog `check_orchestrator_strict_hook_support`).

### 1.2 Feature B — Admin-UI-Sektion „Git" & Auto-Commit-Exposition

- **Was gebaut wird:** Neue Top-Level-Sektion `git` in `.meta-config/project.yaml` für
  Repo-Settings (`platform`, `remote-url`, `main-branch`, `branch-prefixes`); diese Werte
  sind die kanonische Quelle der generierten `GIT_*`-Variablen (explizite
  `variables.GIT_*`-Einträge gewinnen weiterhin). Zusätzlich wird der bestehende
  `auto_commit`-Block über die Admin-UI editierbar gemacht.
- **Was explizit NICHT gebaut wird:** Kein Freigeben der `variables`-Sektion für die
  Admin-UI; keine Schema-Änderung an `auto_commit` (`project-config.schema.json:1193-1311`);
  **keine Branch-Prefix-Enforcement-Anbindung** an `orchestrator-guard-impl.sh`/`branch-guard`
  in dieser Iteration (Q3, §10).
- `git.branch-prefixes` ist in dieser Iteration **Daten/UI-only**: speichern und anzeigen,
  aber (noch) nicht konsumieren — `rules/1-generic/branch-guard.md` bleibt unverändert
  (siehe §3.2, §10 Folge-Issue).

### 1.3 Infrastruktur-Wartbarkeit (nicht-funktional)

- Keine neuen externen Python-Dependencies: nur Stdlib + PyYAML (`jsonschema` bleibt
  optional wie heute).
- Provider-Agnostik über Capability-Flags — **niemals** `if provider == "Name"`. Abgesichert
  durch `tests/test_provider_agnostic_dispatch.py` (um die neuen Module erweitert, §7/m1).
- PEP8, Type Hints, Docstrings.

### 1.4 Vom Orchestrator entschiedene Scope-Punkte (bindend)

- **Q1 — Retry-Zahl:** Genau **1** Retry bei strict-Formatverstoß, **nicht konfigurierbar** in
  dieser Iteration (kein neuer Config-Key). Dokumentiert als Nicht-Ziel + Folge-Issue (§10).
- **Q2 — Validator-Scope:** Rollen werden über die echte Override-Kette aufgelöst
  (`collect_sources`/`role_map`, „2-platform-Override gewinnt"); Scope = **alle Rollen, die
  der Provider-Sync tatsächlich als Dateien erzeugt** (§4.2).
- **Q3 — Branch-Prefix-Konventionen:** Doku/Config-only. `git` speichert `branch-prefixes`
  und exponiert sie in der UI; Enforcement-Anbindung an Branch-Guard ist Folge-Issue, da der
  Guard Git-Mutationen und keine Branch-Namen prüft.

---

## 2. Interface Contracts

### 2.1 Feature A — Schema `subagent_permissions`

**Landepunkt:** `config/project-config.schema.json`, neues Top-Level-Property nach
`orchestrator` (Reihenfolge egal, Stil wie `auto_commit`).

**Entscheidung Key-Name Provider-Map: `provider-overrides`** (nicht `providers`), spiegelt
`orchestrator.provider-overrides` (`project-config.schema.json:1919-1938`).

```json
"subagent_permissions": {
  "type": "object",
  "description": "Subagent permission policy. Default: mode 'off' -- zero behavior change. 'warn' reports dispatch/return-format violations in the delegating agent's own report but never blocks. 'strict' instructs the orchestrator to reject subagent dispatches for roles without an explicit allow/deny declaration (a non-empty `tools:` list in the role template) and to require the structured STATUS/RESULT/ARTIFACTS return format; sync-time validation additionally aborts when an active role template declares no explicit tools list.",
  "properties": {
    "mode": {
      "type": "string",
      "enum": ["strict", "warn", "off"],
      "default": "off",
      "description": "off = today's behavior (subagent dispatch is unconstrained). warn = violations are reported in the delegating agent's report, dispatch continues. strict = subagents without an explicit allow/deny declaration (`tools:` frontmatter) are not dispatched, and every subagent result MUST follow the structured STATUS/RESULT/ARTIFACTS format."
    },
    "provider-overrides": {
      "type": "object",
      "description": "Override subagent_permissions.mode per provider. Keys are provider names (Claude, Codex, Gemini, Opencode, ...). Providers without an entry (or without 'mode' set) inherit the global subagent_permissions.mode. Resolution: provider override > project value > framework default 'off'.",
      "additionalProperties": {
        "type": "object",
        "description": "Per-provider subagent permission overrides.",
        "properties": {
          "mode": {
            "type": "string",
            "enum": ["strict", "warn", "off"],
            "description": "Subagent permission mode for this provider only. Same semantics as subagent_permissions.mode. When unset, inherits the global mode."
          }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

### 2.2 Feature B — Schema `git` (Repo-Settings)

**Landepunkt:** `config/project-config.schema.json`, neues Top-Level-Property.

**Key-Stil:** kebab-case (`main-branch`, `remote-url`, `branch-prefixes`). Der Root-Schema-Eintrag
hat `additionalProperties: true` (`project-config.schema.json:1963`), das neue Property ist
rein additiv.

```json
"git": {
  "type": "object",
  "description": "Repository and branch conventions surfaced in the Admin UI 'Git' section. Values are the canonical source for the generated {{GIT_PLATFORM}}/{{GIT_REMOTE_URL}}/{{GIT_MAIN_BRANCH}} variables. Backward compatible: an explicit variables.GIT_* entry in project.yaml still wins over this section. branch-prefixes are stored/displayed but not yet consumed (follow-up: branch-guard wiring, see design doc).",
  "properties": {
    "platform": {
      "type": "string",
      "enum": ["GitHub", "GitLab", "Gitea", "Codeberg"],
      "default": "GitHub",
      "description": "Git hosting platform. Mirrors variables.GIT_PLATFORM."
    },
    "remote-url": {
      "type": "string",
      "default": "",
      "description": "Canonical remote URL (e.g. https://github.com/owner/repo). Mirrors variables.GIT_REMOTE_URL."
    },
    "main-branch": {
      "type": "string",
      "default": "main",
      "description": "Default/main branch name. Mirrors variables.GIT_MAIN_BRANCH."
    },
    "branch-prefixes": {
      "type": "object",
      "description": "Branch prefix conventions (data/UI only in this iteration — not yet consumed by branch-guard). Defaults reproduce the historic feat/ fix/ chore/ prefixes.",
      "properties": {
        "feat": { "type": "string", "default": "feat/", "description": "Prefix for feature branches." },
        "fix": { "type": "string", "default": "fix/", "description": "Prefix for bugfix branches." },
        "chore": { "type": "string", "default": "chore/", "description": "Prefix for maintenance branches." }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 2.3 Feature B — `auto_commit` Exposition

Keine Schema-Änderung. Der Block `auto_commit` ist schema-komplett (`mode off|suggest|auto|custom`,
`triggers`, `file_count_threshold`, `custom_script`, `secret_scan`, `allOf`-Bedingungen). Geändert
wird nur die Admin-UI-Bindung (§5) und die Whitelist `PROJECT_WRITABLE_SECTIONS` (§5.5).

### 2.4 Neue/geänderte Modul-Funktionen (Interface-Signaturen)

**`scripts/lib/variables.py`** (neutraler Low-Level-Layer, stdlib-only, keine Zyklen):

```python
_VALID_SUBAGENT_PERMISSION_MODES: frozenset[str] = frozenset({"strict", "warn", "off"})
_BOOLEAN_SUBAGENT_PERMISSION_FLAGS: frozenset[str] = frozenset({
    "SUBAGENT_PERMISSIONS_STRICT",
    "SUBAGENT_PERMISSIONS_WARN",
    "SUBAGENT_PERMISSIONS_OFF",
    "SUBAGENT_PERMISSIONS_ENABLED",
})

def normalize_subagent_permission_mode(value: object) -> str | None:
    """Pure, non-exiting: canonical mode string ('strict'|'warn'|'off') or None
    when value is missing/not one of the three. Lowercases+strips strings;
    bools normalize to None (safe-side: never opt-in from a YAML boolean)."""

def _resolve_subagent_permissions_mode(
    cfg: dict,
    provider_override: dict | None = None,
) -> str:
    """Effective mode for cfg + optional override. NEVER calls sys.exit —
    invalid/absent resolves to 'off' (safe-side). All nested access via .get()."""

def _subagent_permission_flags(mode: str) -> dict: ...
```

`_subagent_permission_flags(mode)` (exakt ein Bool-Flag `"true"`, `MODE` ist der String):

```python
{
  "SUBAGENT_PERMISSIONS_MODE": mode,          # "strict" | "warn" | "off"
  "SUBAGENT_PERMISSIONS_STRICT": "true" if mode == "strict" else "false",
  "SUBAGENT_PERMISSIONS_WARN":   "true" if mode == "warn"   else "false",
  "SUBAGENT_PERMISSIONS_OFF":    "true" if mode == "off"    else "false",
  "SUBAGENT_PERMISSIONS_ENABLED": "false" if mode == "off" else "true",
}
```

**`scripts/lib/subagent_permissions.py`** (neu; Stdlib + `.frontmatter`; `compose_agent` lazy):

```python
def render_subagent_permission_block(mode: str) -> str: ...
    # "" bei "off", sonst die Prosa-Anweisung (§4.1)

def resolve_effective_subagent_permission_mode(
    config: dict, provider: str | None = None
) -> str:
    """Read+normalize only — NEVER raises/exits; invalid/absent -> "off".
    Built on _resolve_subagent_permissions_mode / normalize_subagent_permission_mode."""

def resolve_subagent_permission_provider_vars(config: dict, provider: str) -> dict:
    """Full per-provider variable bundle: the boolean flags from
    _subagent_permission_flags(mode) PLUS SUBAGENT_PERMISSIONS_BLOCK =
    render_subagent_permission_block(mode). Defensive .get() chain; invalid ->
    "off". Single source of truth for the M2 (flags+block) consistency."""

def invalid_subagent_permission_entries(config: dict) -> list[str]:
    """Human-readable paths of invalid mode values (global + per override) for
    a consistency Finding. Pure read, never exits."""

def role_declares_tools(
    role: str, agent_meta_root: Path, platforms: list[str]
) -> bool:
    """True when the role's *resolved* template declares a non-empty `tools:`
    (after the real override chain + `extends:` composition)."""

def missing_tools_roles(
    active_roles: list[str], agent_meta_root: Path, platforms: list[str]
) -> list[str]: ...
```

**`scripts/lib/consistency/subagent_permissions.py`** (neu):

```python
def check_subagent_permission_support(
    project_root: Path, agent_meta_root: Path, config: dict, provider_config: dict
) -> list[Finding]:
    """WARNING-only. `subagent_dispatch` from load_provider_capabilities(agent_meta_root)
    (top-level boolean); hooks via providers.provider_hooks_supported(pc).
    Uses the non-exiting resolve_effective_subagent_permission_mode()."""

def check_subagent_permission_templates(
    agent_meta_root: Path, config: dict
) -> list[Finding]:
    """ERROR-only framework-source drift: per-file template checks (M5) +
    flag-not-strippable boolean-flag check (m2)."""
```

---

## 3. Datenfluss

### 3.1 Feature A — Resolve & Precedence

**Effektiver Modus = Provider-Override (falls gesetzt) > Projekt-Wert (`subagent_permissions.mode`) > Framework-Default `"off"`.**

```
.project.yaml
  subagent_permissions:
    mode: warn                      # Ebene 2 (Projekt)
    provider-overrides:
      Opencode: { mode: strict }    # Ebene 1 (Provider), nur Opencode
      Gemini:   {}                  # kein mode -> erbt "warn"
```

- **Alle Verschachtelungszugriffe defensiv (M1):** ausschließlich
  `config.get("subagent_permissions", {})` → `sl.get("provider-overrides", {})` →
  `overrides.get(provider, {})`, jeweils mit `isinstance(..., dict)`-Guard. Kein direkter
  Dict-Index im Default-Fall — auch nicht in `rules._merged_rule_vars` (§3.3).
- **Ebene 3 (Default):** Schema-`default: "off"` wird zur Laufzeit **nicht** materialisiert
  (`fill_defaults()` füllt nur Top-Level + `dod.*`). Der Resolver liefert `"off"`, wenn weder
  Projekt- noch Provider-Wert gesetzt ist.
- **Normalisierung (YAML-1.1):** Unquoted `mode: off|no|false|on|yes|true` parst als
  `bool`. `normalize_subagent_permission_mode()` kanonisiert **jeden bool auf `None`** →
  der Resolver fällt auf `"off"` (Safe-Side: Policy muss explizit per gequotetem Enum-Namen
  opt-in, niemals aus einem YAML-Boolean abgeleitet). Gilt für Top-Level-`mode` **und** jeden
  `provider-overrides.<P>.mode`.
- **Fail-Soft-Semantik (M3):** Resolver/Consistency/UI rufen **nur** die nicht-exitierende
  Lese-/Normalisierungsfunktion. Bei ungültigem Wert → `"off"` + Finding
  (`subagent-permissions.invalid-mode`, WARNING), **kein** `try/except SystemExit`.
  Der harte `sys.exit(1)` existiert **ausschließlich** im Sync-Validator
  `_validate_subagent_permissions` (§4.2), der in `load_config` **vor** `build_variables()`
  läuft.

**Aufrufkette (global → per-Provider):**

1. `load_config()` (`config.py:254-257`): `_normalize_null_blocks` → **neu**
   `_normalize_subagent_permissions_mode(config)` → `_validate_config` (darin **neu**
   `_validate_subagent_permissions`).
2. `build_variables()` (`config.py:1553-1602`): nach `_build_orch_variables(...)` **neu**
   `_build_subagent_permission_variables(variables, config)`.
   Setzt global: `SUBAGENT_PERMISSIONS_MODE`, `_STRICT`, `_WARN`, `_OFF`, `_ENABLED` **und**
   `SUBAGENT_PERMISSIONS_BLOCK = render_subagent_permission_block(mode)`.
3. `sync_pipeline._sync_stage_per_provider()` (`sync_pipeline.py:515-528`): Erweiterung des
   bestehenden Orchestrator-Override-Blocks. **Ein** Shallow-Copy-Punkt bleibt erhalten:

   ```python
   provider_variables = dict(variables) if (orch_override or subagent_override) else variables
   if orch_override:      provider_variables.update(_orch_mode_flags(_resolve_orch_mode(...)))
   if subagent_override:  provider_variables.update(resolve_subagent_permission_provider_vars(config, provider))
   ```
   `subagent_override` liegt vor, wenn `config.get("subagent_permissions", {})` ein dict ist
   und `... .get("provider-overrides", {}).get(provider, {})` ein dict mit gesetztem `mode`.
   **Der Provider-Bundle enthält Flags UND `SUBAGENT_PERMISSIONS_BLOCK`** (M2).
4. Konsumenten: `sync_agents_for_provider` via `_build_provider_vars`, `sync_rules` /
   `sync_embedded_rule_files` via `_merged_rule_vars` — beide sehen den provider-korrekten
   Modus. `_merged_rule_vars` (`rules.py:160-201`) liest den Override **defensiv** und
   aktualisiert `provider_vars` mit `resolve_subagent_permission_provider_vars(config, provider)`
   (idempotent, wenn `variables` die Werte schon trägt; deckt aber direkte Aufrufer ab).

**Conditional-Stripper-Allowlist (Pflicht!):** `strip_inactive_conditional_blocks`
(`variables.py:106-110`) erkennt Variablen nur über eine fest verdrahtete Allowlist:

```python
conditional_vars.update({k for k in variables if k.startswith("SUBAGENT_PERMISSIONS_")})
```

### 3.2 Feature B — `git`-Sektion → `GIT_*`-Variablen

In `_build_core_variables()` (nach dem User-`variables:`-Loop, vor
`_build_provider_variables`) gilt für `GIT_PLATFORM` / `GIT_REMOTE_URL` / `GIT_MAIN_BRANCH`:

```
explizites variables.GIT_X  >  git.<entsprechendes Feld>  >  Default
                              (platform=GitHub, remote-url="", main-branch="main")
```

Implementierung via `variables.setdefault(...)` nach dem Laden der User-Variablen: ein
expliziter Projekt-Wert gewinnt (Backward Compatibility), sonst wird aus `config.get("git", {})`
abgeleitet, sonst der Default gesetzt.

**Branch-Prefixe (Q3):** `git.branch-prefixes` wird **nicht** in `BRANCH_PREFIX_*`-Variablen
übersetzt und `rules/1-generic/branch-guard.md` wird **nicht** angefasst. Schema + Admin-UI
speichern/anzeigen die Werte; die Konsum-Anbindung (branch-guard/Guard) ist ein Folge-Issue.

### 3.3 M2-Entscheidung: Per-Provider-Override führt `SUBAGENT_PERMISSIONS_BLOCK` konsistent mit

**Gewählte Variante A (dokumentiert):** Der Provider-Bundle aus
`resolve_subagent_permission_provider_vars()` setzt **sowohl** die booleschen Flags **als auch**
`SUBAGENT_PERMISSIONS_BLOCK = render_subagent_permission_block(mode)`. Damit bleibt das
Orchestrator-Template `{{SUBAGENT_PERMISSIONS_BLOCK}}` per-provider korrekt, ohne dass
Flags und Block auseinanderlaufen können. Variante B (Orchestrator nur mit
`{{#if SUBAGENT_PERMISSIONS_*}}`-Conditionals, Block-Placeholder entfällt) wird **nicht**
gewählt, weil M4 den Block als Standalone-Fallback fordert.

Das Orchestrator-Template umschließt den Block zusätzlich mit dem Flag, damit der `off`-Fall
keine Leerzeile hinterlässt (§3.4):

```markdown
{{#if SUBAGENT_PERMISSIONS_ENABLED}}
{{SUBAGENT_PERMISSIONS_BLOCK}}
{{/if}}
```

### 3.4 M8 — `off` hinterlässt keine Leerzeile

- `render_subagent_permission_block("off") == ""` und `SUBAGENT_PERMISSIONS_ENABLED == "false"`.
- Die Einbettung erfolgt **innerhalb** eines `{{#if SUBAGENT_PERMISSIONS_ENABLED}}`-Blocks
  (Inline-Conditional). Bei `off` entfernt `strip_inactive_conditional_blocks` Marker **und**
  umgebende Leerzeilen; es bleibt keine leere Zeile zurück.
- Kein Trailing-Strip-Nachbau nötig (der Agent-Pipeline fehlt eine generische
  Whitespace-Normalisierung — deshalb ist die Conditional-Variante verbindlich).

---

## 4. Enforcement-Orte (Feature A)

Es gibt **drei** Ebenen. Keine ist ein Runtime-Gate (siehe §8/§10).

### 4.1 Prompt-Rendering (primär, provider-agnostisch)

**Artefakt 1 — `rules/1-generic/a2a-delegation-gates.md`** (Generic-Rule-Scan `rules.py`, dann
über `_merged_rule_vars` pro Provider substituiert): neue Sektion mit bedingten Blöcken.

```markdown
{{#if SUBAGENT_PERMISSIONS_STRICT}}
## Subagent Permission Policy (strict)

- Dispatche NUR Subagenten, deren Rollen-Template eine explizite allow/deny-Deklaration
  besitzt (nicht-leere `tools:`-Liste in der Frontmatter). Fehlt sie → NICHT dispatchen,
  an `main_chat` eskalieren.
- Jedes Subagenten-Ergebnis MUSS dem Format `STATUS` / `RESULT` / `ARTIFACTS` folgen.
  Ein Ergebnis ohne alle drei Felder wird verworfen; der Subagent wird genau EINMAL mit
  Format-Hinweis erneut dispatcht. Zweiter Verstoß → Eskalation an `main_chat`.
{{/if}}
{{#if SUBAGENT_PERMISSIONS_WARN}}
## Subagent Permission Policy (warn)

- Prüfe jedes Dispatch auf explizite allow/deny-Deklaration und jedes Ergebnis auf
  `STATUS` / `RESULT` / `ARTIFACTS` — blockiere aber NICHT.
- Protokolliere Verstöße als Zeile `SUBAGENT_PERMISSION_WARNING: <role> — <reason>` im
  eigenen Abschluss-Report und fahre fort.
{{/if}}
```

- **`off`:** Beide `{{#if}}`-Blöcke entfernt → kein Text.
- **`warn`:** nur Warn-Block. **`strict`:** nur Strict-Block.

**Artefakt 2 — `agents/1-generic/orchestrator.md`:** `{{SUBAGENT_PERMISSIONS_BLOCK}}` im
Delegations-Gate-Bereich (direkt nach §5 „Pre-delegation self-validation gate"),
eingebettet per `{{#if SUBAGENT_PERMISSIONS_ENABLED}}` (§3.3/§3.4). Bei `off` Leerstring +
entfernter Conditional. Dadurch sieht auch der Orchestrator (nicht nur der Regel-Kontext) die
Policy.

**Artefakt 3 — `rules/1-generic/use-orchestrator.md`:** **unverändert**.

**Provider-Agnostik:** Die Regel-/Agent-Dateien sind Quellen; die per-Provider-Auflösung
erfolgt ausschließlich über Variablen-Flags. Kein Provider-Name im Rendering.

### 4.2 Harter Config-Validator — `_validate_subagent_permissions` (config.py)

Aufgerufen aus `_validate_config` (`config.py:275-335`), Signatur
`(config: dict, config_path: Path) -> None`, Muster `_validate_providers` (`:338-388`):
Meldung auf `stderr`, dann `sys.exit(1)`. **Einziger** Ort mit Hard-Exit für die Policy.

**Geprüft wird:**

1. **Struktur/Enum (immer):** `mode` (falls gesetzt) muss
   `normalize_subagent_permission_mode()` bestehen; `provider-overrides` ist ein Mapping;
   **jeder Key** ist ein registrierter Provider (`registered_provider_names(_framework_root())`);
   jeder Eintrag ist ein Mapping; dessen `mode` (falls gesetzt) ∈ Enum.
   Ungültig → `sys.exit(1)` mit Pfad/Provider-Name.
2. **Strict-Pflicht (nur wenn effektiver Modus `strict` für mindestens einen aktiven
   Provider):** Die Rollen werden über die **echte Override-Kette** aufgelöst (B2, Q2):
   - `platforms = config.get("platforms", [])`
   - `overrides, _ = collect_sources(_framework_root(), platforms)` (`frontmatter.py:550-627`;
     2-platform gewinnt über 1-generic, 3-project über beide)
   - `role_map = build_role_map(_framework_root())` (`roles.py:62-69`) — nur Rollen mit
     Ausgabedatei werden erzeugt
   - aktiv = `role_map`-Schnitt ∩ (`config["roles"]` falls gesetzt) ∩ `_is_role_enabled(role, config)`
   - `orchestrator` entfällt, wenn `_resolve_orch_mode(config.get("orchestrator", {})) == "main-chat"`
     (`agent_sync._should_skip_role:509`).
   Für jede aktive Rolle muss das **aufgelöste** Template (nach `extends:`-Composition, via
   lazy `agent_sync.compose_agent`) eine nicht-leere `tools:`-Deklaration tragen. Fehlende
   Rollen → Hard-Fail; die Meldung nennt die aufgelöste Quelldatei (z. B.
   `agents/2-platform/agent-meta-claude-expert.md`), nicht den hardkodierten
   `agents/1-generic/<role>.md`-Pfad.
   - **Nicht** geprüft wird das Rückgabeformat: `STATUS/RESULT/ARTIFACTS` ist zur Config-Zeit
     nicht verifizierbar (Prompt-Rendering + Consistency, §8).

**Nutzer-sichtbare Fehlermeldung (strict, fehlende Tools):**

```
ERROR: .meta-config/project.yaml: subagent_permissions.mode='strict' requires an explicit
  allow/deny declaration (a non-empty `tools:` list) for every active role.
  Missing tools:
    developer      -> agents/2-platform/hacs-developer.md
    claude-expert  -> agents/2-platform/agent-meta-claude-expert.md
  Fix: add a `tools:` list to the resolved template path above, or set
  subagent_permissions.mode to 'warn' or 'off'.
```

**Nutzer-sichtbare Fehlermeldung (unbekannter Provider-Key / ungültiger Enum):** analog
`_validate_providers`, inkl. Liste der registrierten Provider.

**`sync.py --validate`:** Der Hard-Validator läuft bereits beim `load_config()` — ein
ungültiger strict-Zustand bricht damit **jeden** Sync und `--validate` mit Exit 1 ab, bevor
etwas geschrieben wird.

### 4.3 Consistency-Check — `scripts/lib/consistency/subagent_permissions.py`

**A) Projekt-bewusst (in `_handle_validate`, `cli_commands.py:984-1003`):**

```python
check_subagent_permission_support(project_root, agent_meta_root, config, provider_config)
```

- `caps = load_provider_capabilities(agent_meta_root)` (Top-Level-Booleans; **nicht**
  `provider_has_capability` — B1).
- Für jeden aktiven Provider (`providers.resolve_providers`) effektiven Modus über die
  **nicht-exitierende** `resolve_effective_subagent_permission_mode(config, provider)`.
- Bei ungültigen Werten: **WARNING** `subagent-permissions.invalid-mode`
  (`invalid_subagent_permission_entries`) — kein `try/except SystemExit`.
- `strict` + `caps.get(provider, {}).get("subagent_dispatch") is not True` →
  **WARNING** `subagent-permissions.no-dispatch-surface` (kein Dispatch-Surface; auch der
  konservative Continue/Copilot-Fall).
- `strict` + `not provider_hooks_supported(provider_config.get(provider, {}))` →
  **WARNING** `subagent-permissions.no-hook-support`. Ehrliches Wording (m3): die Policy ist
  auf **allen** Providern prompt-basiert; hier fehlt zusätzlich die optionale PreToolUse-Hook-
  Sekundärstufe (`has_hooks` + verifiziertes `hook_protocol`, issue #630). Deckt u. a.
  Opencode (`hooks: false`) ab.
- Aufruf zusätzlich zu `check_orchestrator_strict_hook_support` in `_handle_validate`;
  Findings werden in `_strict_findings` gemerged. **`print_report` liefert Exit 1 nur bei
  ERROR** — WARNINGs hier eskalieren in `sync.py --validate` **nicht** (n2).

**B) Quell-Template-Drift (in `run_checks`, `consistency-check.py:180-205`):**

```python
check_subagent_permission_templates(agent_meta_root, config)
```

- **ERROR** `subagent-permissions.template-missing` — **getrennt pro Datei (M5), kein `or`
  über zwei Dateien:**
  1. `rules/1-generic/a2a-delegation-gates.md` fehlt **oder** enthält weder
     `{{#if SUBAGENT_PERMISSIONS_STRICT}}` noch `{{#if SUBAGENT_PERMISSIONS_WARN}}`.
  2. `agents/1-generic/orchestrator.md` fehlt **oder** enthält nicht
     `{{SUBAGENT_PERMISSIONS_BLOCK}}`.
  Nur ausgelöst, wenn `load_provider_capabilities(agent_meta_root)` mindestens einen Provider
  mit `subagent_dispatch: true` führt (Framework-Drift → Policy wird nie ausgeliefert).
- **ERROR** `subagent-permissions.flag-not-strippable` — **nur für boolesche Flags (m2):**
  Jedes in den beiden Templates verwendete `{{#if SUBAGENT_PERMISSIONS_*}}` muss in
  `_BOOLEAN_SUBAGENT_PERMISSION_FLAGS` (`SUBAGENT_PERMISSIONS_STRICT/WARN/OFF/ENABLED`) liegen.
  `SUBAGENT_PERMISSIONS_MODE` ist **ausgeschlossen** (Wert ist der Modus-String;
  `strip_inactive_conditional_blocks` behandelt nur `"false"`).
- **Pfad-Semantik (n2):**
  - `sync.py --validate` ruft `run_checks` über `_run_consistency_checks`
    (`cli_commands.py:149-173`) und zählt **nur ERROR** → Exit 1. WARNINGs eskalieren dort
    nicht.
  - `consistency-check.py --strict` (`consistency-check.py:262-263`) stuft WARNINGs zu
    Exit 1 hoch — das ist ein **separater** Aufrufpfad und darf nicht mit `sync.py --validate`
    vermischt werden.

### 4.4 Zusammenfassung der Modus-Semantik

| Modus | Generierte Prompt-Anweisung | Harter Validator | Consistency |
|---|---|---|---|
| `off` | keine (Conditional entfernt, `SUBAGENT_PERMISSIONS_BLOCK=""`) | nur Struktur/Enum | keine Findings |
| `warn` | Report-only-Block, `SUBAGENT_PERMISSION_WARNING` | nur Struktur/Enum | Warnung bei fehlendem Dispatch-Surface / Hook-Wiring |
| `strict` | Blockade + Rückgabeformat-Pflicht + 1 Retry, dann Eskalation | Hard-Fail, wenn aktive Rolle ohne nicht-leere `tools:` (auflösungskorrekt); Hard-Fail bei ungültigem Enum/Provider-Key | Warnung bei fehlendem Dispatch-Surface / Hook-Wiring |

---

## 5. Admin-UI-Bindung (Feature B + A-Konfiguration)

### 5.1 Navigation (`docs/ui/admin-ui.html`, `buildSidebar()`)

Gruppe **„Project instance"**, nach `Hooks` einfügen:

```js
{ route: "/project/subagent-permissions", label: "Subagent Permissions", icon: "🛡" },
{ route: "/project/git",                  label: "Git",                  icon: "⑂" },
{ route: "/project/auto-commit",          label: "Auto-Commit",          icon: "⏱" },
```

Kein `superOnly` — Projekt-Instanz-Settings, sichtbar/schreibbar in beiden Modi.

### 5.2 Router (`init()` `docs/ui/admin-ui.html:9978-10056`)

```js
router.register("/project/subagent-permissions", viewProjectSubagentPermissions);
router.register("/project/git",                  viewProjectGit);
router.register("/project/auto-commit",          viewProjectAutoCommit);
```

### 5.3 Help-ID-Mapping (m7, neu)

Die drei neuen Routen müssen im Help-System-`routeMap`
(`admin-ui.html:10117-10155`) eingetragen werden; `check_ui_help_mappings`
(`scripts/lib/consistency/docs.py:47-97`) verlangt für jeden routeMap-Wert einen
`<!-- help-id: ... -->`-Block in `docs/api/admin-ui-reference.md`.

```js
"project/subagent-permissions": "project_instance-subagent_permissions",
"project/git":                  "project_instance-git",
"project/auto-commit":          "project_instance-auto_commit",
```

In `docs/api/admin-ui-reference.md` (Abschnitt „2. Project instance") die drei
`<!-- help-id: ... -->`-Blöcke ergänzen. Ohne Schritt 5.3 schlägt
`check_ui_help_mappings` mit ERROR fehl.

### 5.4 Neue View-Funktionen

**`viewProjectSubagentPermissions()`** — Muster `viewProjectOrchestrator`
(`admin-ui.html:6796-6963`):

- `loadProject()` → `data.subagent_permissions` klonen.
- Mode-Select via `selectField(["strict", "warn", "off"], section.mode || "off", ...)`
  (`admin-ui.html:1928-1937`), Hilfetext mit Precedence-Erklärung.
- Provider-Override-Tabelle: exakt der Loop aus `:6897-6932` über `data["ai-providers"]`;
  Optionen `["", "strict", "warn", "off"]`, leere Auswahl entfernt den Provider-Key.
- Save: `saveProjectSection("subagent_permissions", section, status)`.
- Client-seitig leer lassen, wenn `mode` `off` und Overrides leer (kein leeres Objekt
  schreiben).

**`viewProjectGit()`** — Formular-View:

- `platform`: Select `["GitHub","GitLab","Gitea","Codeberg"]`.
- `remote-url`: Text-Input (Platzhalter `https://github.com/owner/repo`).
- `main-branch`: Text-Input (Platzhalter `main`).
- `branch-prefixes`: drei Text-Inputs (`feat/`, `fix/`, `chore/`) — Daten-only (Q3).
- Hinweis: „Explizite `variables.GIT_*`-Einträge haben weiterhin Vorrang."
- Save: `saveProjectSection("git", section, status)`.

**`viewProjectAutoCommit()`** — Muster Orchestrator-Panels:

- `mode`: Select `["off","suggest","auto","custom"]`.
- `triggers`: Tag-Editor (`tagEditorField`, Muster Native-Extensions-Whitelist `:6829-6834`)
  mit `task-boundary`, `per-edit`, `context-pressure`, `file-count-threshold`, `custom`.
- `file_count_threshold`: Number-Input (min 1, Default 5).
- `custom_script`: Text-Input (nur sinnvoll bei `custom` bzw. Trigger `custom`).
- `secret_scan`: Checkbox (Default true).
- Client-Gate: `mode === "custom"` ohne `custom_script` → Toast/Inline-Fehler, kein Save.
- Save: `saveProjectSection("auto_commit", section, status)`.

Alle Views nutzen `saveProjectSection` (`:5714-5724`) und `a11yField` (`:5746-5755`) mit
`aria-live`-Status.

### 5.5 Genutzte Endpunkte

- **Lesen:** `GET /api/config/project`; optional `GET /api/schema/project`.
- **Schreiben:** `PUT /api/config/project/section`, Body `{"section": "<key>", "data": <value>}`
  → `_write_project_section`.
- **Kein neuer HTTP-Endpunkt nötig.**

### 5.6 Whitelist-Erweiterung (`scripts/admin-server.py:230-245`)

```python
PROJECT_WRITABLE_SECTIONS: frozenset[str] = frozenset({
    ...,
    # Feature: subagent permissions + git repo settings + auto-commit (Admin UI)
    "subagent_permissions", "git", "auto_commit",
})
```

Ohne diese Erweiterung liefert `_assert_project_sections_writable` HTTP 400
`section not allowed: git`. `variables` bleibt bewusst draußen.

### 5.7 Rollen-/Mode-Verhalten & bekannte Grenze (n3)

- `PROJECT_WRITABLE_SECTIONS` ist modusunabhängig; `ConfigManager.write` beschränkt nur
  `SUPER_ADMIN_FILES`. → Beide Modi dürfen die drei Sektionen schreiben.
- **Bekannte Grenze (n3):** `ConfigManager.write` validiert **nicht** gegen das JSON-Schema
  und es gibt **keine Server-Validierung** der `auto_commit`-`allOf`-Bedingung. Das
  `custom`-ohne-`custom_script`-Gate ist rein client-seitig (Selects/Client-Gates); erst der
  harte Config-Validator beim nächsten `load_config()`/Sync greift. Das ist konsistent mit der
  bestehenden WP3-UI und wird nicht durch einen neuen Endpunkt geschlossen. Abdeckung:
  optionaler Playwright-Test (§7.9), kein Muss.

---

## 6. Geplante Datei-Änderungsliste

### Neu

| Datei | Inhalt |
|---|---|
| `scripts/lib/subagent_permissions.py` | `render_subagent_permission_block`, `resolve_effective_subagent_permission_mode`, `resolve_subagent_permission_provider_vars`, `invalid_subagent_permission_entries`, `role_declares_tools`, `missing_tools_roles` |
| `scripts/lib/consistency/subagent_permissions.py` | `check_subagent_permission_support`, `check_subagent_permission_templates` |
| `tests/test_subagent_permissions_schema.py` | jsonschema-Tests |
| `tests/test_subagent_permissions_resolve.py` | Precedence + Normalisierung + Flags |
| `tests/test_subagent_permissions_render.py` | Rendering + Conditional-Strip |
| `tests/test_subagent_permissions_validate.py` | Hard-Validator (inkl. B2-Plattformrollen) |
| `tests/test_subagent_permissions_consistency.py` | Consistency-Findings (B1) |
| `tests/test_subagent_permissions_provider_override.py` | M2-Regression: Per-Provider-BLOCK in `orchestrator.md` |
| `tests/test_standalone_subagent_permissions.py` | M4-Standalone-Drift |
| `tests/test_git_section_variables.py` | `git`-Sektion → `GIT_*` |
| `tests/test_admin_ui_git_section.py` | statische HTML-Asserts (inkl. routeMap) |
| `tests/browser/test_git_admin_sections.py` | optionaler Playwright-Test |

### Geändert

| Datei | Art der Änderung |
|---|---|
| `config/project-config.schema.json` | neue Top-Level-Properties `subagent_permissions` (§2.1) und `git` (§2.2) |
| `scripts/lib/config.py` | `_normalize_subagent_permissions_mode()` + Aufruf in `load_config`; `_validate_subagent_permissions()` + Aufruf in `_validate_config` (Rollen via `collect_sources`/`build_role_map`); `_build_subagent_permission_variables()` + Aufruf in `build_variables`; `GIT_*`-Ableitung aus `git` in `_build_core_variables` |
| `scripts/lib/variables.py` | `_VALID_SUBAGENT_PERMISSION_MODES`, `_BOOLEAN_SUBAGENT_PERMISSION_FLAGS`, `normalize_subagent_permission_mode`, `_resolve_subagent_permissions_mode` (nicht-exitierend), `_subagent_permission_flags`; Allowlist-Erweiterung in `strip_inactive_conditional_blocks` |
| `scripts/lib/rules.py` | `_merged_rule_vars`: defensiver Per-Provider-Bundle (`resolve_subagent_permission_provider_vars`) analog `_orch_mode` (`:183-187`) |
| `scripts/lib/sync_pipeline.py` | Provider-Override-Block in `_sync_stage_per_provider` (`:515-528`): Flags **und** `SUBAGENT_PERMISSIONS_BLOCK` |
| `scripts/lib/standalone.py` | `SUBAGENT_PERMISSIONS_BLOCK: ""` in `_ORCHESTRATION_FALLBACKS`; `SUBAGENT_PERMISSIONS_STRICT/WARN/OFF/ENABLED` in `_CONDITIONAL_FALSE_FLAGS` (M4) |
| `scripts/consistency-check.py` | Import + Aufruf `check_subagent_permission_templates(agent_meta_root, config)` im Global-Block (`:180-205`) |
| `scripts/lib/cli_commands.py` | `check_subagent_permission_support(project_root, agent_meta_root, config, provider_config)` in `_handle_validate` (`:984-1003`) |
| `scripts/admin-server.py` | `PROJECT_WRITABLE_SECTIONS` um `subagent_permissions`, `git`, `auto_commit` erweitern |
| `docs/ui/admin-ui.html` | Nav, Router, 3 Views, routeMap-Help-IDs |
| `docs/api/admin-ui-reference.md` | drei neue `<!-- help-id: ... -->`-Blöcke |
| `rules/1-generic/a2a-delegation-gates.md` | Subagent-Permission-Sektion mit `{{#if SUBAGENT_PERMISSIONS_STRICT}}` / `{{#if SUBAGENT_PERMISSIONS_WARN}}` |
| `agents/1-generic/orchestrator.md` | `{{SUBAGENT_PERMISSIONS_BLOCK}}` in `{{#if SUBAGENT_PERMISSIONS_ENABLED}}` nach §5 |
| `tests/test_provider_agnostic_dispatch.py` | `_TOUCHED_MODULES` um `subagent_permissions`, `consistency/subagent_permissions` erweitern (m1) |
| `templates/configs/project.yaml.example` | kommentierte Beispiele `subagent_permissions` + `git` |
| `CHANGELOG.md` | `## [Unreleased]` → `### Added` (Feature A, Feature B) |
| `README.md` / `docs/` | Config-Key-Doku + Doku-Index-Eintrag (documenter) |

**Bewusst NICHT geändert:**

- `rules/1-generic/branch-guard.md` und `hooks/1-generic/orchestrator-guard*` — Q3: keine
  Branch-Prefix-Enforcement-Anbindung in dieser Iteration (Folge-Issue).
- `config/provider-capabilities.yaml` und `config/ai-providers.yaml` — nutzen die bereits
  vorhandenen Flags (`subagent_dispatch`/`hooks` bzw. `has_hooks`/`hook_protocol`).
- `auto_commit`-Schema.

---

## 7. Test-Plan

Kommandos (CI): `pip install -r tests/requirements.txt`;
`python -m pytest tests/ -q`; `python scripts/sync.py --validate`;
`python3 scripts/sync.py --check`; `python scripts/sync.py --render-standalone --check`;
`bash tests/scenarios/run.sh`.

### 7.1 `tests/test_subagent_permissions_schema.py`

- `{mode: "off"|"warn"|"strict"}` valide; unbekannter Modus → `ValidationError`.
- `provider-overrides: {Claude: {mode: "warn"}}` valide; ungültiger Sub-Modus → Fehler.
- Zusätzliche Property im Block / im Provider-Eintrag → Fehler (`additionalProperties: false`).
- `git`-Sektion: Defaults nicht erforderlich; ungültige `platform` → Fehler; unbekannte
  Property → Fehler.

### 7.2 `tests/test_subagent_permissions_resolve.py`

- unset → `"off"`; Projekt `warn` → `warn`; Provider-Override `strict` schlägt Projekt
  `warn`; Provider-Eintrag `{}` erbt Projekt-Modus; zwei Provider unabhängig.
- `_subagent_permission_flags`: genau ein `*_STRICT/WARN/OFF`-Flag `"true"`;
  `SUBAGENT_PERMISSIONS_ENABLED == "false"` nur bei `off`; `SUBAGENT_PERMISSIONS_MODE`
  enthält den String.
- **Defensive `.get()`-Kette (M1):** `subagent_permissions: {}`, `provider-overrides: {}`,
  `provider-overrides: {Gemini: {}}` und fehlende Keys führen zu keiner Exception.
- Normalisierung über `load_config` (Temp-YAML): `mode: off` (bool) → `"off"`,
  `mode: on` (bool True) → `"off"`, Provider-Eintrag-bool → `"off"`.
- ungültiger Modus → **kein** `SystemExit` im Resolver (`normalize_...` liefert `None`,
  effektiv `"off"`).

### 7.3 `tests/test_subagent_permissions_render.py`

- `render_subagent_permission_block("off") == ""`.
- `"warn"` enthält `SUBAGENT_PERMISSION_WARNING`, kein „do NOT dispatch".
- `"strict"` enthält Blockade + `STATUS`/`RESULT`/`ARTIFACTS` + Eskalation.
- `strip_inactive_conditional_blocks` auf der A2A-Rule: `strict` entfernt den Warn-Block und
  lässt keinen `{{#if SUBAGENT_PERMISSIONS_`-Marker übrig; `off` entfernt beide.
- **M8:** `off` in `agents/1-generic/orchestrator.md` hinterlässt keine Leerzeile
  (Assertion auf den umgebenden Textblock).

### 7.4 `tests/test_subagent_permissions_validate.py`

- unbekannter Provider-Key in `provider-overrides` → `SystemExit(1)` mit
  „unknown provider"-Meldung.
- ungültiger Enum → `SystemExit(1)`.
- `strict` + aktive Rolle ohne `tools:` → `SystemExit(1)`, Rolle + aufgelöste Quelldatei
  benannt; bei `warn` kein Exit.
- **B2-Plattformrollen (Regression):** Repo-Fixture mit `platforms: [agent-meta]` und Rolle
  `claude-expert`, die **nur** als `agents/2-platform/agent-meta-claude-expert.md` existiert
  (kein `agents/1-generic/claude-expert.md`) → Validator löst über `collect_sources` auf und
  meldet **nicht** fehlend. Analog `gemini-expert`/`opencode-expert`/`continue-expert`/
  `copilot-expert`.
- 2-platform-Override ohne `tools:` (aber generische Basis mit `tools:` via `extends:`) →
  nach Composition nicht fehlend; 2-platform-Override **ohne** `extends:`/`tools:` → fehlend.
- `subagent_permissions: null` (YAML) → `_normalize_null_blocks` → `{}` → kein Exit.

### 7.5 `tests/test_subagent_permissions_consistency.py`

- **B1:** Provider mit `provider-capabilities.yaml subagent_dispatch: false` (Continue) +
  `strict` → WARNING `no-dispatch-surface`.
- **B1:** Provider mit `subagent_dispatch: true` und `provider_hooks_supported == false`
  (Opencode, `hooks: false`) + `strict` → WARNING `no-hook-support`.
- **B1:** Claude/Gemini (verifiziertes `hook_protocol`) + `strict` → **keine**
  `no-dispatch-surface`-Warnung, obwohl ihre `ai-providers.yaml`-`capabilities`-Liste kein
  `subagent_dispatch` enthält (schützt vor dem v1-Fehler).
- **M5:** fehlender Strict/Warn-Conditional nur in `a2a-delegation-gates.md` → ERROR für die
  Rule; fehlender BLOCK nur in `orchestrator.md` → ERROR für das Agent-Template (zwei getrennte
  Assertions; kein `or`).
- **m2/n1:** `{{#if SUBAGENT_PERMISSIONS_UNKNOWN}}` → ERROR `flag-not-strippable`;
  `{{#if SUBAGENT_PERMISSIONS_MODE}}` → **kein** Finding; Nicht-Boolean-Wert in
  `_subagent_permission_flags` wird nicht als strippbar fehlklassifiziert.
- ungültiger Modus-Wert (direkter Aufruf) → WARNING `invalid-mode`, **kein** `SystemExit`.
- `off` → keine Findings.

### 7.6 `tests/test_subagent_permissions_provider_override.py` (M2)

- Global `off`, Provider `Opencode: {mode: strict}`: generierte
  `.opencode/agents/orchestrator.md` (Fixture) enthält den Strict-Text; Claude (ohne Override)
  enthält ihn nicht.
- Der Provider-Bundle enthält `SUBAGENT_PERMISSIONS_BLOCK == render_subagent_permission_block(mode)`
  **und** die vier booleschen Flags konsistent; kein Flag/Block-Mismatch.
- `sync_rules`-Pfad: `a2a-delegation-gates.md` rendert für den Override-Provider die
  Strict-/Warn-Sektion, für die anderen `off` (kein Block).

### 7.7 `tests/test_standalone_subagent_permissions.py` (M4)

- `_ORCHESTRATION_FALLBACKS["SUBAGENT_PERMISSIONS_BLOCK"] == ""` und die vier Flags in
  `_CONDITIONAL_FALSE_FLAGS`.
- `render_standalone_agent("orchestrator", root)` enthält keinen `SUBAGENT_PERMISSIONS`-Marker
  und keinen `[SUBAGENT_PERMISSIONS_BLOCK …]`-Leak.
- `check_standalone_drift(root) == []` nach eingechecktem Re-Render.

### 7.8 `tests/test_git_section_variables.py`

- `git.main-branch: develop` → `GIT_MAIN_BRANCH == "develop"`.
- `variables.GIT_MAIN_BRANCH: trunk` + `git.main-branch: develop` → `"trunk"`.
- weder noch → `"main"`; `remote-url` → `GIT_REMOTE_URL`; `platform` → `GIT_PLATFORM`.
- `branch-prefixes` erzeugt **keine** `BRANCH_PREFIX_*`-Variable (Q3) und
  `rules/1-generic/branch-guard.md` bleibt byte-identisch.

### 7.9 Admin-Server / Admin-UI

`tests/test_admin_server.py` (erweitern):

- Round-Trip `subagent_permissions`, `git`, `auto_commit` via `_write_project_section`.
- `variables` bleibt nicht-schreibbar (HTTP-400, kein Teil-Write).

`tests/test_admin_ui_git_section.py` (statisch):

- `viewProjectSubagentPermissions(`, `viewProjectGit(`, `viewProjectAutoCommit(` definiert,
  je ≥ 2× im HTML.
- `'section: "git"'` / `"subagent_permissions"` / `"auto_commit"` vorhanden.
- **m7:** die drei neuen `routeMap`-Keys vorhanden; jeder Help-ID-Wert existiert als
  `<!-- help-id: ... -->` in `docs/api/admin-ui-reference.md` (kann zusätzlich über
  `check_ui_help_mappings` abgesichert werden).

Optional `tests/browser/test_git_admin_sections.py` (Playwright, Port 7421):

- Mode-Select + Provider-Override setzen, speichern, neu laden → persistiert.
- `auto_commit mode: custom` ohne `custom_script` → Client-Fehler, kein Save (n3; optional).

### 7.10 Regressions-/Provider-Agnostik

- `tests/test_provider_agnostic_dispatch.py` bleibt grün; `_TOUCHED_MODULES` enthält
  `"subagent_permissions"` und `"consistency/subagent_permissions"` (m1).
- `tests/test_config_null_blocks.py`, `tests/test_import_acyclicity.py`,
  `tests/test_build_variables_decomposition.py`, `tests/test_auto_commit_*` bleiben grün.

---

## 8. Akzeptanzkriterien

Jede Referenz `[C-n]` verweist auf einen Interface-Contract in §2/§3.

1. **AC-A1** — Das Schema akzeptiert `subagent_permissions.mode` ∈ `{strict, warn, off}`
   und `provider-overrides.<Provider>.mode` ∈ derselben Menge; jeder andere Wert und jede
   unbekannte Property wird von jsonschema abgelehnt. `[C-2.1]`
2. **AC-A2** — `_resolve_subagent_permissions_mode` liefert deterministisch
   Provider-Override > Projekt-Wert > `"off"`; alle Zugriffe defensiv per `.get()`. `[§3.1]`
3. **AC-A3** — YAML-1.1-Booleans unter `subagent_permissions.mode` und jedem
   `provider-overrides.<P>.mode` werden auf `"off"` normalisiert; kein bool erreicht den
   Resolver. `[§3.1]`
4. **AC-A4** — Bei `off` ist `SUBAGENT_PERMISSIONS_BLOCK == ""` und nach
   `strip_inactive_conditional_blocks` bleibt weder ein `SUBAGENT_PERMISSIONS_*`-Marker noch
   eine Leerzeile zurück. `[§3.4, §4.1]`
5. **AC-A5** — Bei `warn`/`strict` wird genau ein `SUBAGENT_PERMISSIONS_*`-Block gerendert;
   `strict` enthält Blockade + Rückgabeformat-Pflicht, `warn` nur Report. `[§4.1]`
6. **AC-A6** — `load_config()` bricht mit `SystemExit(1)` und benannter Fehlermeldung ab,
   wenn effektiv `strict` gilt und eine **über die echte Override-Kette aufgelöste** aktive
   Rolle keine nicht-leere `tools:`-Deklaration hat; bei `warn`/`off` nicht. `[§4.2]`
7. **AC-A7** — Ein unbekannter Provider-Key in `provider-overrides` führt zu `SystemExit(1)`
   inkl. Liste der registrierten Provider. `[§4.2]`
8. **AC-A8 (B1-korrekt)** — Der Consistency-Check bestimmt `subagent_dispatch` aus
   `load_provider_capabilities(agent_meta_root)` (Top-Level-Boolean) und spiegelt für die
   Hook-Frage `provider_hooks_supported(pc)`; Claude/Gemini erzeugen bei `strict` **keine**
   `no-dispatch-surface`-Warnung, Continue erzeugt `no-dispatch-surface`, Opencode erzeugt
   `no-hook-support` — alles WARNING, nie ERROR. `[§4.3]`
9. **AC-A9 (B2)** — Der Strict-Validator löst Rollen ausschließlich über
   `collect_sources`/`build_role_map` (2-platform gewinnt) auf und deckt die Repo-eigenen
   Plattform-Rollen (`claude-expert`, `gemini-expert`, `opencode-expert`, `continue-expert`,
   `copilot-expert`) ab; der hardkodierte Pfad `agents/1-generic/<role>.md` wird nicht
   verwendet. `[§4.2]`
10. **AC-A10 (M5/m2)** — `template-missing` prüft Rule und Orchestrator-Template getrennt
    (kein `or` über zwei Dateien); `flag-not-strippable` prüft nur die vier booleschen Flags
    und schließt `SUBAGENT_PERMISSIONS_MODE` aus. `[§4.3]`
11. **AC-A11 (n2)** — `sync.py --validate` eskaliert WARNINGs nicht (Exit 1 nur bei ERROR);
    `consistency-check.py --strict` (WARNING→ERROR) ist ein separater Pfad. `[§4.3]`
12. **AC-B1** — Die `git`-Sektion ist im Schema mit `platform`/`remote-url`/`main-branch`/
    `branch-prefixes` definiert; `additionalProperties: false`; Defaults dokumentiert. `[§2.2]`
13. **AC-B2** — `build_variables()` leitet `GIT_*` aus `git` ab; ein expliziter
    `variables.GIT_*`-Eintrag gewinnt; fehlen beide, gilt der Default. `branch-prefixes`
    erzeugt keine Variable (Q3). `[§3.2]`
14. **AC-B3** — `PUT /api/config/project/section` persistiert `git`, `auto_commit`,
    `subagent_permissions`; eine nicht-gelistete Sektion liefert HTTP 400 ohne Teil-Write. `[§5.5-5.6]`
15. **AC-B4** — Nav, Router und die drei Views existieren; gespeichert wird über
    `/api/config/project/section`; die drei neuen Routen sind in `routeMap` + Help-Referenz
    verdrahtet (m7). `[§5.1-5.4]`
16. **AC-C1** — Keine neuen externen Dependencies (nur Stdlib + PyYAML; `jsonschema` optional).
17. **AC-C2** — `pytest`, `sync.py --validate`, `sync.py --check`,
    `sync.py --render-standalone --check`, `tests/scenarios/run.sh` sind grün.

---

## 9. Edge Cases

| # | Fall | Erwartetes Verhalten |
|---|---|---|
| E1 | `provider-overrides` mit unbekanntem Provider-Key (`Claud`) | Hard-Fail via `_validate_subagent_permissions` (§4.2) |
| E2 | `provider-overrides: {}` (leer) | gültig → alle Provider erben Projekt-Modus |
| E3 | `subagent_permissions: null` (YAML) | `_normalize_null_blocks` → `{}` → effektiv `off` |
| E4 | unquoted `mode: off` (bool `False`) | Normalisierung → `"off"` |
| E5 | `mode: on`/`yes`/`true` (bool `True`) | Normalisierung → `"off"` (Safe-Side) |
| E6 | Provider-Eintrag `{}` (kein `mode`) | erbt Projekt-Modus |
| E7 | Provider-Eintrag mit bool-`mode` | Normalisierung → `"off"` für diesen Provider |
| E8 | `mode: strict`, aktive Rolle ohne `tools:` | Hard-Fail, aufgelöste Quelldatei(en) benannt (§4.2) |
| E9 | `auto_commit.mode: custom` ohne `custom_script` | Schema-`allOf` lehnt ab; Admin-UI blockt Save client-seitig; **keine** Server-Validierung (n3) |
| E10 | `git`-Sektion nur teilweise gesetzt | fehlende Felder fallen auf `variables.GIT_*` bzw. Default zurück (§3.2) |
| E11 | Provider-Eintrag mit ungültigem `mode` (nur Consistency/UI) | `"off"` + WARNING `invalid-mode`, kein `SystemExit` (M3) |
| E12 | 2-platform-Rolle nur als `agent-meta-*-expert.md` | über `collect_sources` aufgelöst, nicht als fehlend gemeldet (B2) |
| E13 | `strict` mit Orchestrator in `main-chat`-Mode | `orchestrator` aus dem Validator-Scope ausgeschlossen (§4.2) |

---

## 10. Risiken & Nicht-Ziele

### Risiken

- **Kein Runtime-Dispatch-Gate (m3, ehrlich formuliert).** Die Policy ist auf **allen**
  Providern prompt-basiert plus Sync-Time-Validierung; es gibt auf keinem Provider ein
  Runtime-Gate. `validate_envelope()` ist dormant
  (`scripts/lib/delegation_syntax.py:210-222`). Ein Modell kann die Prompt-Anweisung
  ignorieren — identische, bereits akzeptierte Grenze wie bei `orchestrator.mode: strict`
  (`docs/concepts/a2a-handoff-protocol.md`). Muss in der generierten Rule ehrlich benannt
  werden.
- **`no-hook-support`-WARNING für hook-lose Provider** kann bei `strict`-Nutzern Rauschen
  erzeugen — deshalb Severity WARNING, nie ERROR, und ehrliches Wording (#630).
- **Doppelte Permission-Map vermeiden (m5).** Template-Frontmatter `tools:` ist eine
  **Allow-Liste**; ein **Deny** entsteht nur aus der globalen `opencode_deny_critical`-Liste
  in `config/provider-tools.yaml` (`provider_transform.py:504-515`; angewandt beim Aufbau des
  `permission:`-Blocks `:582-591`). Diese Spec erzeugt **keine** zweite Permission-Map; sie
  liest `tools:` nur als allow/deny-**Deklaration**.
- **Admin-UI schreibt ohne Schema-Validierung** (`ConfigManager.write`) und ohne
  Server-Validierung der `auto_commit`-Bedingung (n3). Enum-Fehler werden erst beim nächsten
  Sync hart erkannt; Client-Selects mildern das.
- **Validator-Scope** ist die Menge der tatsächlich generierten Rollen (§4.2, Q2); die
  Orchestrator-`main-chat`-Ausnahme ist explizit modelliert (E13).

### Nicht-Ziele

- **Q1:** Keine konfigurierbare Retry-Zahl (`subagent_permissions.max_format_retries`) in
  dieser Iteration — fix `1` Retry, Folge-Issue.
- **Q3:** Keine Branch-Prefix-Enforcement-Anbindung an `orchestrator-guard-impl.sh`/
  `branch-guard`; `branch-prefixes` sind Daten/UI-only, `branch-guard.md` bleibt unverändert.
- Kein Push/Tag/Release (exklusiv `git`-Rolle).
- Kein Aktivieren der `variables`-Sektion in der Admin-UI.
- Keine Änderung bestehender `unique_id`s/Entity-Generationen oder des `auto_commit`-Schemas.
- Keine neuen Python-Dependencies, keine Provider-Namensverzweigungen.
- Keine Runtime-Hook-Erweiterung (`PreToolUse`) in dieser Iteration.

---

## 11. Migrations- & Rückwärtskompatibilität

- **Default `off`:** Ohne `subagent_permissions`-Block wird keine Anweisung generiert, kein
  Strict-Validator-Zweig aktiv, kein Consistency-Finding erzeugt → **Zero Behavior Change**.
- **Additive Schema-Keys:** Root-`additionalProperties: true`
  (`project-config.schema.json:1963`); bestehende Configs bleiben unverändert gültig.
- **`git` vs. `variables.GIT_*` (m6, präzisiert):** Byte-Identität der Provider-Outputs ist
  garantiert, **sofern** das Projekt explizite `variables.GIT_*`-Einträge hat — der
  User-Wert gewinnt per `setdefault`, und Templates, die `{{GIT_*}}` referenzieren, rendern
  exakt wie zuvor. Projekte **ohne** explizite `variables.GIT_*`, deren Templates `{{GIT_*}}`
  referenzieren, erhalten erstmals einen konkreten Wert (Default/Git-Sektion) statt eines
  unaufgelösten Platzhalters — das ist die beabsichtigte additive Verbesserung, **keine**
  Byte-Identität.
- **Branch-Prefixe:** unverändert (Q3) — `branch-guard.md` behält die hartkodierten
  `feat/`, `fix/`, `chore/`.
- **Admin-UI:** Rein additive Nav/Routen/Views/Help-IDs; bestehende Sektionen unberührt.
- **CHANGELOG:** Eintrag unter `## [Unreleased]` / `### Added`; keine Versionserhöhung in
  dieser Spec.

---

## 12. Offene Fragen

1. ~~Retry-Zahl konfigurierbar?~~ → **entschieden (Q1):** nein, fix 1, Folge-Issue.
2. ~~Validator-Scope?~~ → **entschieden (Q2):** echte Override-Kette, generierte Rollen.
3. ~~Branch-Prefix-Variablen umsetzen?~~ → **entschieden (Q3):** Daten/UI-only, Folge-Issue.
4. Verbleibend: **Format der Folge-Issues.** Sollen Q1 (Retry-Config) und Q3
   (Branch-Prefix-Enforcement) als zwei separate GitHub Issues angelegt werden (Empfehlung:
   ja, unterschiedliche Subsysteme)? — Klärung durch `main_chat`, kein Blocker.

---

## 13. Revision History (v1 → v2)

| Finding | Severity | Eingearbeitet |
|---|---|---|
| B1 | BLOCKER | §1.1 Capability-Tabelle, §2.4 Signatur mit `agent_meta_root`, §4.3 nutzt `load_provider_capabilities` + `provider_hooks_supported`; AC-A8 + Test 7.5 (Claude/Gemini vs. Continue/Opencode) |
| B2 | BLOCKER | §4.2 Rollenauflösung via `collect_sources`/`build_role_map` inkl. `extends`-Composition; AC-A9 + Test 7.4 (Repo-Plattformrollen) |
| M1 | MAJOR | §3.1/§3.3: durchgängige `.get()`-Kette + `isinstance`-Guards, auch in `rules._merged_rule_vars`; Test 7.2 |
| M2 | MAJOR | §3.3 Entscheidung Variante A: Provider-Bundle führt Flags **und** `SUBAGENT_PERMISSIONS_BLOCK` mit; Test 7.6 |
| M3 | MAJOR | §3.1/§4.3: Hard-Exit nur im Validator; nicht-exitierende Lese-/Normalisierungsfunktion, kein `try/except SystemExit`; Test 7.5 |
| M4 | MAJOR | §6 Standalone-Zeile; `SUBAGENT_PERMISSIONS_BLOCK`-Fallback + Flags in `_CONDITIONAL_FALSE_FLAGS`; Test 7.7 |
| M5 | MAJOR | §4.3 `template-missing` pro Datei getrennt (Rule ≠ Orchestrator, kein `or`); AC-A10 + Test 7.5 |
| m1 | MINOR | §6/§7.10: `_TOUCHED_MODULES` um beide neuen Module erweitert |
| m2 | MINOR | §4.3 `flag-not-strippable` nur boolesche Flags; `SUBAGENT_PERMISSIONS_MODE` ausgeschlossen; Test 7.5 |
| m3 | MINOR | §4.3/§10 ehrliches Wording: prompt-basiert auf allen Providern, kein Runtime-Gate |
| m4 | MINOR | §1.4/§3.2 Q3: Branch-Prefix-Scope = Daten/UI-only, kein branch-guard |
| m5 | MINOR | §10: `tools:` = Allow-Liste; Deny aus `opencode_deny_critical` (`provider_transform.py:504-515`) |
| m6 | MINOR | §11: Byte-Identität nur bei explizitem `variables.GIT_*` |
| m7 | MINOR | §5.3 routeMap + Help-IDs; §6/§7.9 Testabdeckung |
| m8 | MINOR | §3.4/§4.1: `{{#if SUBAGENT_PERMISSIONS_ENABLED}}`-Wrapper, keine Leerzeile bei `off`; AC-A4 + Test 7.3 |
| n1 | MINOR | §7.5 Test für `flag-not-strippable` + Nicht-Boolean-Wert |
| n2 | MINOR | §4.3 Trennung `consistency-check.py --strict` vs. `sync.py --validate`; AC-A11 |
| n3 | MINOR | §5.7 bekannte Grenze ohne Server-Validierung; optionaler Playwright-Test |
