# Konzept — Repo-Containment („Gefängnis-Modus") & `.tmp`-Scratch-Sink

- **Status:** Draft v1 (Konzept, keine Implementierung)
- **Betroffener Bereich:** Sync-Config, Provider-Hooks, Consistency-Checks, `.gitignore`, Admin-UI
- **Umfang:** 1 neuer Config-Block `repo_containment`, 1 neuer PreToolUse-Hook, 1 Sync-Time-Validator,
  1 Consistency-Check, 1 Admin-UI-Sektion, `.tmp`-Bereitstellung
- **Nicht in diesem Dokument:** Implementierung, Code-Änderungen, Commits, `sync.py`-Läufe,
  Änderungen an `.agent-meta/`-Submodul oder `external/`
- **Terminologie:** „Convention boundary" / „security boundary" wird exakt so verwendet wie in
  [`../../.claude/rules/branch-guard.md`](../../.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary)
  definiert. Dieses Dokument verlinkt die zentrale Definition und wiederholt sie nicht.

---

## 1. Scope & Kontext

### 1.1 Scope

Ein neuer, standardmäßig **aktiver** Modus „Repo-Containment" („Gefängnis-Modus") beschränkt die
Datei-**Schreib**zugriffe eines Agenten auf die Projekt-Wurzel (`repo root`). Zusätzlich stellt der
Modus optional einen sanktionierten Scratch-Bereich `.tmp/` bereit: Ist der `.tmp`-Sink aktiv,
darf der Agent **nur** innerhalb `repo root` **plus** dem auto-provisionierten `.tmp/` schreiben
(der „Übergriff"-Ausnahmebereich).

Der Modus ist:

- **Default AN** (Framework-Default `enabled: true`),
- **schaltbar** (an/aus) über `.meta-config/project.yaml`,
- **projekt-überschreibbar** (Precedence: Provider-Override > Projekt > Framework-Default),
- **in der Admin-UI schaltbar** (neue Sektion „Repo Containment"),
- **provider-agnostisch** (Config-Keys/Capability-Flags, kein `if provider == "Name"`),
- **konsistent** mit dem 0/1/2/3-Schichten-Modell
  ([architecture-Skill](../../.opencode/skills/architecture/SKILL.md)) und dem bestehenden
  Hook-Enforcement-Muster (`orchestrator-guard.sh`) plus Sync-Time-Validator.

### 1.2 Nicht-Scope

- **Kein OS-Level-Sandbox.** Containment wird auf PreToolUse-Hook-Ebene plus Sync-Time-Validierung
  umgesetzt — **nicht** über Container, Mount-Namespaces, seccomp/Landlock, Filesystem-ACLs oder
  einen dedizierten OS-User. Es ist damit primär eine **Convention boundary** (Details §6).
- **Kein Runtime-Gate auf hook-losen Providern.** Provider ohne gespiegelte Hooks
  (`provider_hooks_supported(pc) == false`) erhalten Containment nur als Prompt-Konvention plus
  Sync-Time-Validierung (analog zur bereits akzeptierten Grenze in
  [`../../scripts/lib/consistency/orchestrator_strict.py`](../../scripts/lib/consistency/orchestrator_strict.py)).
- **Kein Abfangen von Lese-Zugriffen.** Containment beschränkt Schreibzugriffe (`Write`/`Edit`
  plus schreibende Bash-Kommandos). Read-Tools (`Read`, `Glob`, `Grep`) bleiben unberührt.
- **Keine automatische Löschung von `.tmp`-Inhalten per Default** (Datenverlust-Risiko, §5.4).
- **Keine Änderung an `orchestrator-guard.sh` / `branch-guard`** in dieser Iteration; ein
  Zusammenlegen der beiden PreToolUse-Hooks ist eine offene Frage (§10).
- Kein Push/Tag/Release, keine neue externe Python-Dependency (nur Stdlib + PyYAML).

### 1.3 Betroffene Subsysteme

| Subsystem | Rolle im Konzept |
|---|---|
| `config/project-config.schema.json` | Neues Top-Level-Property `repo_containment` (additiv, Root ist ohne restriktives `additionalProperties`) |
| `scripts/lib/repo_containment.py` (neu) | Nicht-exitierender Resolver `resolve_effective_repo_containment(config, provider)`, `ensure_tmp_sink(...)`, Pfad-Validierung |
| `scripts/lib/config.py` | Harter Sync-Time-Validator `_validate_repo_containment`, aufgerufen aus `_validate_config` |
| `scripts/lib/variables.py` | Neue Variablen `REPO_CONTAINMENT_*` + Conditional-Allowlist |
| `hooks/1-generic/repo-containment.sh` + `-impl.sh` (neu) | PreToolUse-Hook (Wrapper/Impl-Split wie `orchestrator-guard`) |
| `scripts/lib/hooks.py` | Registrierung über `hook_protocol`/`has_hooks` (bereits capability-getrieben, unverändert) |
| `scripts/lib/consistency/repo_containment.py` (neu) | Support-WARNING + Template-Drift-ERROR |
| `scripts/consistency-check.py` | Registrierung des Template-Drift-Checks |
| `scripts/lib/cli_commands.py` (`_handle_validate`) | Registrierung des projekt-bewussten Support-Checks (`sync.py --validate`) |
| `scripts/lib/gitignore.py` | `.tmp/` in den managed Block |
| `docs/ui/admin-ui.html`, `docs/api/admin-ui-reference.md`, `scripts/admin-server.py` | Neue Admin-UI-Sektion + Whitelist |

---

## 2. Config-Schema & Precedence

### 2.1 Schema-Vorschlag

**Landepunkt:** `config/project-config.schema.json`, neues Top-Level-Property (Stil analog
`orchestrator` bzw. `subagent_permissions`). Der Root-Eintrag besitzt kein
`additionalProperties: false`; das neue Property ist rein additiv.

```json
"repo_containment": {
  "type": "object",
  "description": "Repo-Containment ('Gefängnis-Modus'): confines agent WRITE access to the project root. Default enabled: true. The optional tmp-sink additionally sanctions a framework-provisioned scratch directory (default .tmp/) as the single exception outside an otherwise root-confined policy.",
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": true,
      "description": "Master switch. true = writes are confined to the repo root (plus the tmp-sink when enabled). false = today's unrestricted behavior."
    },
    "provider-overrides": {
      "type": "object",
      "description": "Override repo_containment.enabled per provider. Keys are registered provider names (Claude, Codex, Gemini, Opencode, ...). Providers without an entry inherit the project value. Resolution: provider override > project value > framework default true.",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "enabled": {
            "type": "boolean",
            "description": "Containment switch for this provider only. When unset, inherits the global repo_containment.enabled."
          }
        },
        "additionalProperties": false
      }
    },
    "tmp-sink": {
      "type": "object",
      "description": "Optional scratch sink. When enabled, sync.py provisions <project-root>/<path> and the containment hook permits writes inside it as the only exception outside the repo root. The directory is gitignored by the framework.",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": true,
          "description": "Provision the scratch directory and widen the containment exception to it. When false, containment stays strictly root-only."
        },
        "path": {
          "type": "string",
          "default": ".tmp",
          "description": "Relative path of the scratch directory, resolved against the project root. MUST be relative and MUST NOT contain '..' segments (enforced by the sync-time validator)."
        },
        "gitignore": {
          "type": "boolean",
          "default": true,
          "description": "Add the scratch directory to the agent-meta managed .gitignore block and to a self-ignoring <path>/.gitignore fallback."
        },
        "cleanup": {
          "type": "string",
          "enum": ["manual", "on-sync"],
          "default": "manual",
          "description": "manual = never delete contents automatically (safe default). on-sync = prune the directory on each sync run (opt-in, destructive)."
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

### 2.2 Beispiel in `.meta-config/project.yaml`

```yaml
repo_containment:
  enabled: true                 # Ebene 2: Projekt-Wert (überschreibt Framework-Default)
  tmp-sink:
    enabled: true
    path: ".tmp"
    gitignore: true
    cleanup: "manual"
  provider-overrides:
    Continue: { enabled: false } # Ebene 1: nur für Continue aus (kein Hook-Support, §6)
```

### 2.3 Precedence

**Effektiver Modus = Provider-Override (falls gesetzt) > Projekt-Wert (`repo_containment.enabled`) >
Framework-Default `true`.**

Diese dreistufige Kettenlogik spiegelt bewusst die bereits etablierte Auflösung für
`orchestrator.mode`/`subagent_permissions.mode` (siehe
[`../../scripts/lib/consistency/orchestrator_strict.py`](../../scripts/lib/consistency/orchestrator_strict.py)
und [`subagent-permissions-git-admin-ui.md`](subagent-permissions-git-admin-ui.md)). Alle
Verschachtelungszugriffe erfolgen defensiv (`config.get(...)` + `isinstance(..., dict)`-Guards),
der Resolver ist **nicht-exitierend**; der einzige Hard-Exit liegt im Sync-Validator (§4.3).

**YAML-1.1-Falle:** Unquoted `enabled: off|no|false|on|yes|true` wird als `bool` geparst. Der
Resolver interpretiert einen echten `bool` direkt; nur bei explizit nicht-booleschen,
nicht auflösbaren Werten fällt er safe-side auf `true` (Default AN) zurück und erzeugt ein
WARNING-Finding.

---

## 3. Admin-UI-Sektion „Repo Containment"

Die neue Sektion folgt dem Muster bestehender Projekt-Instanz-Sektionen (z. B.
`project_instance-git`, `project_instance-orchestrator`).

| Ort | Änderung |
|---|---|
| `docs/ui/admin-ui.html` → `buildSidebar()` (Gruppe „Project instance") | Eintrag `{ route: "/project/repo-containment", label: "Repo Containment", icon: "🔒" }` |
| `docs/ui/admin-ui.html` → `routeMap` (in `init()`) | `"project/repo-containment": "project_instance-repo_containment"` |
| `docs/api/admin-ui-reference.md` | `<!-- help-id: project_instance-repo_containment -->` (sonst schlägt `check_ui_help_mappings` fehl) |
| `scripts/admin-server.py` → `PROJECT_WRITABLE_SECTIONS` | `"repo_containment"` ergänzen |
| Neue View-Funktion | Master-Toggle, `.tmp`-Sink-Toggle, Pfad-Feld (validiert), Gitignore-Toggle, Cleanup-Select, Provider-Override-Tabelle |

**Semantik der Controls:**

- **Master-Toggle** (`repo_containment.enabled`): Default AN; Deaktivieren zeigt einen
  Hinweis, dass Containment damit auf diesem Projekt vollständig aus ist.
- **`.tmp`-Sink-Toggle** (`tmp-sink.enabled`): Default AN. Ohne Sink bleibt Containment strikt
  root-only.
- **Pfad-Feld** (`tmp-sink.path`): muss relativ und `..`-frei sein; Client-Validierung plus
  harter Sync-Time-Validator (§4.3).
- **Cleanup-Select**: Default `manual`; `on-sync` ist opt-in und wird als destruktiv markiert.

**Bekannte Grenze:** Die Admin-UI schreibt ohne Schema-Validierung (`ConfigManager.write`); ein
ungültiger Wert wird erst beim nächsten Sync hart erkannt. Client-Selects mildern das — dieselbe
bereits akzeptierte Grenze wie in
[`subagent-permissions-git-admin-ui.md`](subagent-permissions-git-admin-ui.md) §5.7.

---

## 4. Enforcement-Design

Es gibt **drei** Ebenen: (1) PreToolUse-Hook (Runtime, nur hook-fähige Provider), (2)
Sync-Time-Validator (harte Struktur-/Pfad-Prüfung), (3) Consistency-Check (Drift + Support-Lücke).
Keine davon ist eine vollständige Security Boundary (§6).

### 4.1 Hook-basiert (primär)

**Neuer Hook:** `hooks/1-generic/repo-containment.sh` (Wrapper) + `hooks/1-generic/repo-containment-impl.sh`
(Logik). Der Wrapper-/Impl-Split übernimmt das etablierte Muster aus
[`../../hooks/1-generic/orchestrator-guard.sh`](../../hooks/1-generic/orchestrator-guard.sh)
inkl. `bash -n`-Selbstcheck (Issue #630): Ist `repo-containment-impl.sh` syntaktisch kaputt, darf
der Wrapper den Guard nicht stillschweigend öffnen; der Fail-Mode ist eine offene Frage (§10, Q7).

**Hook-Header (Registrierung):**

```
# hook: repo-containment
# version: 1.0.0
# event: PreToolUse
# matcher: ""
# description: Confine Write/Edit/Bash file writes to repo root (+ optional .tmp sink).
# enabled_by_default: true
```

`scripts/lib/hooks.py` liest `enabled_by_default` und registriert den Hook **capability-getrieben**:
Ein Provider erhält den Hook nur, wenn `provider_hooks_supported(pc)` (`has_hooks: true` **und**
verifiziertes `hook_protocol`) zutrifft. Die Registrierung läuft über `pc.get("hook_protocol")`
(Claude: `claude-code-json` → `_update_settings_hooks`; Gemini: `antigravity-hooks-json` →
`antigravity-json-adapter.sh`). **Kein `if provider == "Name"`** — ein neuer Provider wird ohne
Python-Änderung unterstützt, sobald er `has_hooks` + `hook_protocol` deklariert.

**Was der Hook prüft:**

- Tool `Write`/`Edit`: Zielpfad aus `tool_input.file_path` gegen `repo root`.
- Tool `Bash`: tokenisierte Analyse des Kommandos auf schreibende Operationen (analog
  `parse_git`/Mutation-Gate in `orchestrator-guard-impl.sh`).
- Erlaubt: Ziele, die per aufgelöstem `realpath` innerhalb `repo root` liegen.
- Erlaubt zusätzlich **nur bei aktivem Sink**: Ziele innerhalb `<repo root>/<tmp-sink.path>`.

**Effektiver Modus im Hook:** Der Hook liest `.meta-config/project.yaml` (über das `cwd`-Feld des
PreToolUse-Payloads, wie `orchestrator-guard`) und wendet die Precedence aus §2.3 an. Bei
`enabled: false` exit `0` ohne Overhead.

### 4.2 Provider-Capabilities (kein Namens-Branching)

| Frage | Registry | Zugriff |
|---|---|---|
| Unterstützt der Provider Hooks **und** sind sie gespiegelt? | `config/ai-providers.yaml` | `providers.provider_hooks_supported(pc)` (`has_hooks` + verifiziertes `hook_protocol`) |
| Wird der neue Hook per Config an-/ausgeschaltet? | `config/project-config.schema.json` | `hooks.repo-containment.enabled` (bestehender `hooks`-Block) |
| Ist Subagent-Dispatch vorhanden? (nur Kontext) | `config/provider-capabilities.yaml` | Top-Level-Boolean `load_provider_capabilities(...)` |

`provider_has_capability(pc, "hooks")` ist **falsch** für diese Frage: `pc` ist der
`ai-providers.yaml`-Eintrag, dessen `capabilities: [...]`-Liste `hooks` als Listeneintrag führt,
während die Spiegelung über `has_hooks` + `hook_protocol` entschieden wird (analog
[`../../scripts/lib/consistency/subagent_permissions.py`](../../scripts/lib/consistency/subagent_permissions.py)).

### 4.3 Sync-Time-Validator

**`_validate_repo_containment(config, config_path)`** in `scripts/lib/config.py`, aufgerufen aus
`_validate_config` (dort schon `_validate_providers` + `_validate_subagent_permissions`). Muster:
Meldung auf `stderr`, dann `sys.exit(1)`. **Einziger** Ort mit Hard-Exit für Containment.

Geprüft wird:

1. `repo_containment` ist ein Mapping (falls gesetzt).
2. `enabled` ist boolean (falls gesetzt).
3. `provider-overrides` ist ein Mapping; jeder Key ist ein registrierter Provider
   (`registered_provider_names(...)`); jeder Eintrag ist ein Mapping; dessen `enabled` ist boolean.
4. `tmp-sink.path` ist ein **relativer**, nicht-leerer Pfad, kein `.`/Absolutpfad, kein
   `..`-Segment, und darf nach `os.path.normpath` nicht aus `repo root` herausführen.
   Verstoß → `sys.exit(1)` mit Pfadangabe.

Ein Hard-Exit bei inaktivem Modus (`enabled: false` plus `provider-overrides` alle false)
findet **nicht** statt — Struktur-/Pfadprüfungen sind immer aktiv, damit ein späteres Aktivieren
keine schlafende Fehlkonfiguration freilegt.

### 4.4 Consistency-Check

`scripts/lib/consistency/repo_containment.py` mit zwei Funktionen, analog
`orchestrator_strict.py` / `subagent_permissions.py`:

- **`check_repo_containment_support(project_root, config, provider_config)`** — WARNING-only.
  Meldet, wenn Containment für einen aktiven Provider effektiv aktiv ist, dieser aber keinen
  gespiegelten Hook hat (`provider_hooks_supported == false`): Dort ist Containment ein stiller
  No-Op als Runtime-Gate und wirkt nur als Prompt-Konvention. Registrierung in
  `_handle_validate` ([`../../scripts/lib/cli_commands.py`](../../scripts/lib/cli_commands.py)) neben
  `check_orchestrator_strict_hook_support`.
- **`check_repo_containment_templates(agent_meta_root)`** — ERROR-only Framework-Drift. Prüft,
  dass Hook und Prompt-Template die erwarteten Marker/Variablen tragen. Registrierung in
  [`../../scripts/consistency-check.py`](../../scripts/consistency-check.py) neben
  `check_subagent_permission_templates`.

### 4.5 Prompt-/Template-Ebene (Convention)

- Neue Rule-Sektion in `rules/1-generic/` (z. B. `repo-containment.md`) mit bedingten
  `{{#if REPO_CONTAINMENT_ENABLED}}`-Blöcken.
- Neue Variablen: `REPO_CONTAINMENT_ENABLED`, `REPO_CONTAINMENT_BLOCK`,
  `REPO_CONTAINMENT_TMP_SINK_ENABLED`, `REPO_CONTAINMENT_TMP_PATH`.
- **Pflicht:** Der `REPO_CONTAINMENT_`-Präfix muss in die fest verdrahtete
  Conditional-Allowlist von `strip_inactive_conditional_blocks` (`scripts/lib/variables.py`)
  aufgenommen werden, sonst werden die Blöcke nie gestrippt.
- **Pflicht:** Neue Platzhalter müssen in der CLAUDE.md-Variablen-Tabelle registriert werden
  (Framework-Konvention, sonst kein Sync).

### 4.6 Hart vs. Konvention — ehrliche Einordnung

| Ebene | Klasse | Begründung |
|---|---|---|
| `Write`/`Edit`-Zielpfad (realpath innerhalb root) | **technisch hart** (im Rahmen des Hooks) | Strukturiertes JSON-Feld, deterministisch prüfbar |
| Sync-Time-Validator (Struktur/Pfad) | **technisch hart** (fail-closed) | Bricht den Sync ab, bevor etwas generiert wird |
| `Bash`-Schreibziel-Erkennung | **Convention boundary** | Tokenizer, kein Shell-Parser — umgehbar (§6) |
| Hook-lose Provider | **Convention** | Kein Runtime-Gate, nur Prompt + Validierung |
| Hook-Deaktivierung durch Agenten (Write auf `settings.json`) | **keine Boundary** | Guard wird von genau dem Filesystem durchgesetzt, das der Agent beschreiben darf |

---

## 5. Automatische `.tmp`-Bereitstellung

### 5.1 Wer legt an

**`sync.py`** provisioniert das Verzeichnis deterministisch bei jedem Lauf, wenn
`repo_containment.tmp-sink.enabled == true`. Das ist die kanonische Quelle (idempotent,
planbar, im Sync-Log sichtbar). Der Hook legt es **nicht** an — er kennt nur den erlaubten
Präfix. Ein `makedirs(exist_ok=True)` in `scripts/lib/repo_containment.py::ensure_tmp_sink(...)`
genügt; dry-run meldet nur.

### 5.2 Pfad

- Default: `<project-root>/.tmp/`.
- Konfigurierbar über `tmp-sink.path` (relativ, `..`-frei, durch §4.3 hart validiert).
- `repo root` ist der Projekt-Instanz-Root (das Verzeichnis, in dem `.meta-config/` liegt),
  **nicht** das Git-Toplevel bei Submodul-Layout. `.agent-meta/`-Framework-Dateien liegen
  innerhalb des Projekt-Roots und sind daher ohnehin erlaubt.

### 5.3 Gitignore-Handling

Zwei Stufen, damit die Ignorierung auch auf provider-fremden Setups greift:

1. **Managed-Block:** `scripts/lib/gitignore.py::compute_base_gitignore_entries` ergänzt `.tmp/`,
   wenn Sink + `tmp-sink.gitignore` aktiv sind. **Wichtige bestehende Grenze:** Der exakte
   Managed-Block-Pfad ist Claude-gated (`if "Claude" not in providers: return []` in
   `compute_base_gitignore_entries`); auf reinen Nicht-Claude-Projekten ist der Block nur
   additiv.
2. **Self-Ignoring-Fallback:** Zusätzlich wird `<path>/.gitignore` mit `*` plus einer Ausnahme
   für diese Datei selbst angelegt. Das wirkt provider-agnostisch und unabhängig vom
   Claude-Gate. Der Managed-Block-Eintrag bleibt trotzdem sinnvoll (Sichtbarkeit/Konsistenz).

`.tmp/` wird **nicht** in die generierten `gitignore_entries`-Listen der Provider eingetragen
(dort stehen lokale Settings/Personal-Dateien), sondern als Projekt-Scratch über die
managed-Block-Logik geführt.

### 5.4 Cleanup / Lifecycle

- **Default `manual`:** Der Sync löscht **nie** Inhalte. Grund: `.tmp` ist Scratch des Agenten
  und kann Artefakte enthalten, deren Verlust einen Lauf zerstört. „Default AN" beim Modus darf
  **nicht** „Default destruktiv" beim Cleanup bedeuten.
- **Opt-in `on-sync`:** Vor jedem Lauf wird der Inhalt geleert. Im Sync-Log und in der Admin-UI
  explizit als destruktiv markiert.
- Kein Cleanup beim Session-Start in dieser Iteration (mangels provider-agnostischem,
  verlässlichem Session-Start-Hook; als offene Frage §10/Q3 notiert).
- Das Verzeichnis bleibt via Gitignore ungetrackt und ist damit nicht Teil des Repo-Zustands.

---

## 6. Threat Model & bekannte Grenzen

### 6.1 Bedrohungsmodell

Der Guard schützt gegen **akzidentiellen** Missbrauch: vergessene `cd`, versehentliche absolute
Pfade, naive Automatisierung, ein Modell, das die Konvention „nur im Repo arbeiten" überdehnt.
Er ist **nicht** darauf ausgelegt, einem gezielten Umgehungsversuch zu widerstehen — genau die
Definition einer **Convention boundary** in
[`../../.claude/rules/branch-guard.md`](../../.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary).

### 6.2 Bekannte Bypässe und Grenzen

1. **Command-Substitution/Indirektion (analog #592).** `eval "..."`, Backticks, `$(...)` und
   `xargs` können ein schreibendes Kommando am Bash-Tokenizer vorbeischleusen, weil der Hook die
   Shell weder ausführt noch vollständig parst. Ein echter Shell-Interpreter wäre für ein
   Konventions-Tool unverhältnismäßig — derselbe bewusste Trade-off wie in
   [`../../hooks/1-generic/orchestrator-guard-impl.sh`](../../hooks/1-generic/orchestrator-guard-impl.sh)
   (Issue #592).
2. **Redirections/Heredocs/`cd`-Ketten.** `cat > /etc/x`, `cd / && ...` oder mehrstufige
   Pipes können außerhalb eines strukturierten Zielpfads schreiben. Der Hook erkennt
   `Write`/`Edit` präzise, schreibende `Bash`-Muster nur best-effort.
3. **Symlink-/TOCTOU-Escape.** Ein Agent legt einen Symlink innerhalb des Repo-Roots auf ein
   Ziel außerhalb an und schreibt durch ihn. Ein `realpath`-Check mildert das, hat aber ein
   TOCTOU-Fenster (Ziel ändert sich zwischen Check und Write). Ob Symlinks ganz verboten werden,
   ist offene Frage §10/Q6.
4. **Direkte Nicht-Tool-Schreibpfade.** MCP-Filesystem-Server, Editor-Plugins oder externe CLIs
   laufen ggf. an PreToolUse vorbei. Der Hook sieht nur die Tool-Aufrufe des Providers.
5. **Guard-Deaktivierung durch den Agenten selbst.** Ein Agent mit Write-Zugriff auf
   `.claude/settings.json` oder das Hook-Skript kann den Guard ausschalten oder verändern — eine
   Grenze, die ein Dateisystem-Hook prinzipiell nicht schließen kann.
6. **Hook-lose Provider.** Opencode, Continue, Copilot, Mammouth, Codex (Stand der
   `ai-providers.yaml`-Registries) haben kein verifiziertes `hook_protocol`; dort wirkt
   Containment nur als Prompt-Konvention. Der Consistency-Check (§4.4) meldet das als WARNING.
7. **`orchestrator-guard`-Analogie.** Wie beim bestehenden Guard gilt: Der Hook ist ein
   Konventions-Tool mit einzelnen security-boundary-Eigenschaften (hier: hard fail beim
   Sync-Validator), kein vollständiger Schutz.

### 6.3 Was eine echte Security Boundary bräuchte

Für einen Schutz gegen **deliberate** Umgehung wäre OS-/Runtime-Isolierung nötig, nicht ein
Shell-Hook:

- OS-Sandbox: Container / `bubblewrap` / `firejail`, Mount-Namespaces mit Read-only-Bind-Mounts
  außerhalb des Repo-Roots, `seccomp`/Landlock.
- Provider-native Sandbox/Permission-Modes (falls der Provider das anbietet) als vorgelagerte
  Boundary.
- Filesystem-ACLs oder Ausführung der Agenten unter einem dedizierten OS-User ohne
  Schreibrechte außerhalb des Repo-Roots.

Das ist ausdrücklich **nicht** Scope dieses Konzepts (§1.2).

---

## 7. Teststrategie

Kein Test existiert bisher; die folgenden Tests sind im Implementierungs-Issue anzulegen. Der
Hook-Test folgt dem Vorbild
[`../../tests/test_orchestrator_guard_hook.py`](../../tests/test_orchestrator_guard_hook.py)
(echter Subprozess-Aufruf mit synthetischen PreToolUse-JSON-Payloads, Assertion auf Exit-Code).

| Test | Inhalt |
|---|---|
| `tests/test_repo_containment_hook.py` | `Write` innerhalb Root → 0; außerhalb → 2; `.tmp` mit aktivem Sink → 0; `.tmp` ohne Sink → 2; `enabled: false` → immer 0; `Bash`-Schreibmuster; Symlink-Escape; leerer/kaputter Payload |
| `tests/test_repo_containment_schema.py` | Schema-Validierung des neuen Blocks (additiv, Defaults, Enum `cleanup`) |
| `tests/test_repo_containment_resolve.py` | Precedence Provider > Projekt > Default; defensive `.get()`-Kette; YAML-Bool-Falle |
| `tests/test_repo_containment_validate.py` | Sync-Validator: Nicht-Mapping, falscher `enabled`-Typ, unbekannter Provider, absoluter `tmp-sink.path`, `..`-Escape, leerer Pfad |
| `tests/test_repo_containment_consistency.py` | `no-hook-support`-WARNING (Claude/Gemini vs. Continue/Opencode); Template-Drift-ERROR; Import in `consistency-check.py` |
| `tests/test_repo_containment_tmp_sink.py` | Provisionierung bei Sync; `enabled: false` legt nichts an; `.tmp` im Managed-Block + self-ignoring `.gitignore`; `cleanup: manual` löscht nicht; `on-sync` leert |
| `tests/test_provider_agnostic_dispatch.py` | `_TOUCHED_MODULES` um die neuen Module erweitern (kein Provider-Namens-Branch) |
| Admin-UI (optional, Playwright) | Sektion lädt, Toggles persistieren, Provider-Overrides-Tabelle; sonst manueller Check |

Zusätzlich: `python scripts/consistency-check.py` muss grün bleiben (inkl.
`check_ui_help_mappings` für die neue Route).

---

## 8. Bezug zu bestehender Doku

| Thema | Referenz |
|---|---|
| Zentraldefinition Convention vs. Security Boundary + bekannte Guard-Grenzen | [`../../.claude/rules/branch-guard.md`](../../.claude/rules/branch-guard.md) |
| Wrapper/Impl-Split + `bash -n`-Selbstheilung (#630) | [`../../hooks/1-generic/orchestrator-guard.sh`](../../hooks/1-generic/orchestrator-guard.sh), [`../../hooks/1-generic/orchestrator-guard-impl.sh`](../../hooks/1-generic/orchestrator-guard-impl.sh) |
| Hook-Test-Muster | [`../../tests/test_orchestrator_guard_hook.py`](../../tests/test_orchestrator_guard_hook.py) |
| Support-/Drift-Check-Muster für Guards | [`../../scripts/lib/consistency/orchestrator_strict.py`](../../scripts/lib/consistency/orchestrator_strict.py) |
| Sync-Time-Validator-Muster (Hard-Exit) | [`../../scripts/lib/config.py`](../../scripts/lib/config.py) (`_validate_config`, `_validate_subagent_permissions`) |
| Capability-getriebene Hook-Registrierung | [`../../scripts/lib/hooks.py`](../../scripts/lib/hooks.py), [`../../config/ai-providers.yaml`](../../config/ai-providers.yaml) |
| Provider-Agnostik-Policy | [`../../.opencode/skills/provider-agnostic/SKILL.md`](../../.opencode/skills/provider-agnostic/SKILL.md) |
| 0/1/2/3-Schichten-Modell | [`../../.opencode/skills/architecture/SKILL.md`](../../.opencode/skills/architecture/SKILL.md) |
| Sync-CLI/`--check`/Drift | [`../../.opencode/skills/sync-interface/SKILL.md`](../../.opencode/skills/sync-interface/SKILL.md) |
| `.gitignore`-Handling | [`../../scripts/lib/gitignore.py`](../../scripts/lib/gitignore.py) |
| Hooks-Doku (Provider-Payload) | [`../guides/features/hooks.md`](../guides/features/hooks.md) |
| Vorgänger-Konzept mit identischem Precedence-/Validator-Muster | [`subagent-permissions-git-admin-ui.md`](subagent-permissions-git-admin-ui.md) |
| Bestehende Provider-Isolation (`isolation-dirs`, `isolation-mechanism`) | [`../../config/ai-providers.yaml`](../../config/ai-providers.yaml) — **Abgrenzung:** Isolation beschreibt, welche Verzeichnisse ein Provider besitzt; Repo-Containment beschränkt zur Laufzeit Schreibziele auf den Repo-Root. Beide ergänzen sich, ersetzen sich nicht. |

---

## 9. Risiken, Nicht-Ziele & Migration

### 9.1 Risiken

- **Default AN ist ein Verhaltenswechsel.** Bestandsprojekte, die `repo_containment` nicht
  explizit setzen, erhalten beim nächsten Sync erstmals einen blockierenden Hook. Das ist
  gewollt (Binding-Requirement), muss aber im CHANGELOG und in der Migrations-Notiz ehrlich als
  Verhaltensänderung benannt werden. Opt-out: `repo_containment.enabled: false` oder
  `provider-overrides`.
- **Hook-lose Provider erzeugen eine falsche Erwartungshaltung.** „Default AN" heißt dort nur
  Prompt-Konvention; der WARNING-Check (§4.4) muss das sichtbar machen.
- **Bash-Erkennung ist best-effort** (§6.2) — nicht als Sicherheitsgarantie kommunizieren.
- **Guard-Selbstblockade.** Ein defekter Impl-Script darf nicht dazu führen, dass alle
  Tool-Aufrufe blockiert werden (Reparatur unmöglich) — deshalb Wrapper-Muster wie #630;
  Fail-Mode ist Q7.
- **`on-sync`-Cleanup** ist destruktiv; Default bleibt `manual`.

### 9.2 Nicht-Ziele

- Kein OS-Sandboxing, kein Runtime-Gate auf hook-losen Providern.
- Kein Zusammenlegen/Refactoring von `orchestrator-guard` in dieser Iteration.
- Keine Änderung an `branch-guard.md` oder `rules/1-generic/branch-guard.md`.
- Keine automatische `.tmp`-Löschung per Default.
- Keine neuen Python-Dependencies, kein Provider-Namens-Branching.

### 9.3 Migrations- & Rückwärtskompatibilität

- **Additives Schema:** Bestehende Configs bleiben gültig; ohne Block greift der Default.
- **Default AN:** Verhaltensänderung (siehe 9.1) — bewusst, mit Opt-out.
- **`.gitignore`:** `.tmp/` kommt additiv in den Managed-Block; auf Claude-losen Projekten nur
  über den self-ignoring Fallback (§5.3), da der exakte Managed-Block Claude-gated ist.
- **Admin-UI:** Rein additive Nav/Route/View/Help-ID; bestehende Sektionen unberührt.
- **CHANGELOG-Eintrag** unter `## [Unreleased]`; keine Versionserhöhung in diesem Konzept.

---

## 10. Offene Fragen

1. **Default-AN-Migration.** Sollen Bestandsprojekte den Hook automatisch erhalten (reiner
   Schema-Default, wie oben beschrieben) oder soll `sync.py` einmalig einen expliziten
   `repo_containment`-Block in `.meta-config/project.yaml` materialisieren, damit der
   Verhaltenswechsel sichtbar/überprüfbar ist?
2. **Provider-Override-Semantik bei hook-losen Providern.** Wird `enabled: true` dort
   trotzdem als Prompt-Konvention ausgespielt (Empfehlung: ja, plus WARNING), oder soll der
   Resolver auf hook-losen Providern automatisch auf `false` fallen?
3. **Cleanup-Trigger Session-Start.** Gibt es einen provider-agnostisch verlässlichen
   Session-Start-Hook, oder bleibt es bei `manual`/`on-sync`?
4. **Bash-Umfang.** Wird die schreibende Bash-Erkennung bewusst als best-effort (analog #592)
   dokumentiert, oder sollen Redirection-Häufungen wie `cat > /path` aktiv erkannt werden?
5. **Symlink-Politik.** `realpath`-Auflösung mit TOCTOU-Restrisiko, oder Symlinks innerhalb des
   Repo-Roots pauschal sperren?
6. **Hook-Selbstheilung.** Welcher Fail-Mode bei kaputtem `repo-containment-impl.sh`? Narrow
   Carve-out (analog #630) oder separater Reparatur-Kanal?
7. **Hook-Interaktion.** `orchestrator-guard.sh` und `repo-containment.sh` sind zwei
   PreToolUse-Hooks mit `matcher: ""`. Reicht Koexistenz (unabhängige Registrierung), oder soll
   ein gemeinsamer Wrapper die Reihenfolge/Short-Circuit-Logik garantieren?
8. **`repo root`-Definition im Submodul-Layout.** Ist die Wurzel immer der Projekt-Root
   (Verzeichnis mit `.meta-config/`) — auch wenn agent-meta unter `.agent-meta/` liegt? Diese
   Definition liegt dem Konzept zugrunde und ist zu bestätigen.
9. **MCP-/Nicht-Tool-Schreibpfade.** Sollen MCP-Filesystem-Server in die Bedrohungsanalyse
   aufgenommen und ggf. durch eine separate MCP-Allowlist eingeschränkt werden (Folge-Issue)?
10. **Issue-Aufteilung.** Empfehlung: ein Implementierungs-Issue mit den Teilen Config+Validator,
    Hook, `.tmp`-Sink/Gitignore, Consistency und Admin-UI — oder getrennte Issues pro Subsystem?
    Klärung durch `main_chat`, kein Blocker.
