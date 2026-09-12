# Konzept — Repo-Containment („Gefängnis-Modus") & `.tmp`-Scratch-Sink

- **Status:** Accepted (Implementierung freigegeben; Umsetzung in diesem Lauf, §10/Q10)
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
- **Keine Änderung an `orchestrator-guard.sh` / `branch-guard`** in dieser Iteration; die beiden
  PreToolUse-Hooks koexistieren unabhängig (§10/Q7, entschieden).
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
`orchestrator`). Der Root-Eintrag besitzt kein
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

**Master-Switch-Klarstellung:** `repo_containment.enabled` ist der **einzige** Master-Switch.
Es existiert **kein** separater `hooks.repo-containment.enabled`-Eintrag. Die Hook-Registrierung
erfolgt rein capability-getrieben über den Hook-Header `enabled_by_default: true` plus
`provider_hooks_supported` (§4.2); den effektiven An/Aus-Zustand liest der Hook zur Laufzeit
direkt aus `.meta-config/project.yaml` (nicht aus einem `hooks`-Block).

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
`orchestrator.mode` (siehe
[`../../scripts/lib/consistency/orchestrator_strict.py`](../../scripts/lib/consistency/orchestrator_strict.py)).
Alle Verschachtelungszugriffe erfolgen defensiv (`config.get(...)` + `isinstance(..., dict)`-Guards),
der Resolver ist **nicht-exitierend**; der einzige Hard-Exit liegt im Sync-Validator (§4.3).

**YAML-1.1-Falle (F4 — eine Regel, konsistent referenziert aus §4.1 und §4.3):** Unquoted
`enabled: off|no|false|on|yes|true` wird als `bool` geparst — das ist gültig und wird direkt
interpretiert. Ein **nicht-boolescher** `enabled`-Wert (z. B. String oder Number) ist hingegen
ein harter Fehler: Der Sync-Time-Validator `_validate_repo_containment` bricht mit klarer
Fehlermeldung ab (§4.3). Zur Laufzeit gilt für den Hook eine defensive Safe-Side-Regel: Bei
fehlender, unlesbarer oder unparsebarer Config fällt er auf ENABLED zurück und öffnet **nie**
stillschweigend (§4.1). Es gibt keine dritte, widersprechende Fallback-Regel.

---

## 3. Admin-UI-Sektion „Repo Containment"

Die neue Sektion folgt dem Muster bestehender Projekt-Instanz-Sektionen (z. B.
`project_instance-general`, `project_instance-orchestrator`).

| Ort | Änderung |
|---|---|
| `docs/ui/admin-ui.html` → `buildSidebar()` (:1548, Gruppe „Project instance") | Sidebar-Eintrag `{ route: "/project/repo-containment", label: "Repo Containment", icon: "🔒" }` |
| `docs/ui/admin-ui.html` → `init()` → `router.register(...)` (:10001–10052) | **Neue View-Registrierung** `router.register("/project/repo-containment", viewProjectRepoContainment)` — fehlt im aktuellen Bestand und ist zwingend, sonst Blank-Page |
| `docs/ui/admin-ui.html` → Help-`routeMap` im zweiten `<script>`-Block (:10117) — **nicht** in `init()` | `"project/repo-containment": "project_instance-repo_containment"` |
| `docs/api/admin-ui-reference.md` | `<!-- help-id: project_instance-repo_containment -->` ergänzen (sonst schlägt `check_ui_help_mappings` fehl) |
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
bereits akzeptierte Grenze wie im Admin-UI-Konzept, in dem das Schema ebenfalls nur über
`sync.py` validiert wird und Fehler erst beim Sync sichtbar werden
([`planned/admin-ui-concept.md`](planned/admin-ui-concept.md)).

---

## 4. Enforcement-Design

Es gibt **drei** Ebenen: (1) PreToolUse-Hook (Runtime, nur hook-fähige Provider), (2)
Sync-Time-Validator (harte Struktur-/Pfad-Prüfung), (3) Consistency-Check (Drift + Support-Lücke).
Keine davon ist eine vollständige Security Boundary (§6).

### 4.1 Hook-basiert (primär)

**Neuer Hook:** `hooks/1-generic/repo-containment.sh` (Wrapper) + `hooks/1-generic/repo-containment-impl.sh`
(Logik). Der Wrapper-/Impl-Split übernimmt das etablierte Muster aus
[`../../hooks/1-generic/orchestrator-guard.sh`](../../hooks/1-generic/orchestrator-guard.sh)
inkl. `bash -n`-Selbstcheck (Issue #630). **Fail-Mode (Q6, entschieden): narrow carve-out.**
Ist `repo-containment-impl.sh` syntaktisch kaputt, **failt der Guard CLOSED** für `Write`/`Edit`
(er blockt die Tool-Aufrufe), öffnet also nicht stillschweigend — bietet aber einen
**dokumentierten Reparatur-Kanal**, damit sich der Guard nicht selbst aussperrt. Der Reparatur-
Kanal ist im Hook dokumentiert (analog #630); Details siehe §9.1.

**Fail-safe bei unklarem `enabled` (F4):** Fehlt die Config, ist sie unlesbar oder unparsebar,
fällt der Hook defensive safe-side auf **ENABLED** zurück und öffnet **nie** stillschweigend.
Ein explizit nicht-boolescher `enabled`-Wert ist bereits auf Sync-Ebene ein Hard-Exit (§4.3);
dieselbe Regel wird hier nicht widersprüchlich dupliziert.

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
verifiziertes `hook_protocol`) zutrifft. Die Funktion ist in
[`../../scripts/lib/providers.py`](../../scripts/lib/providers.py) definiert und wird von
[`../../scripts/lib/hooks.py`](../../scripts/lib/hooks.py) bei der Registrierung aufgerufen.
Die Registrierung läuft über `pc.get("hook_protocol")` und die datengetriebene Zuordnung
`_HOOK_REGISTRATION_WRITERS` (`scripts/lib/hooks.py` :375–378): Claude (`claude-code-json`)
→ `_update_settings_hooks`; Gemini (`antigravity-hooks-json`) → Writer
`_update_antigravity_hooks_json` (`scripts/lib/hooks.py` :255), der als registrierten
Command-String den Adapter `antigravity-json-adapter.sh` einträgt (erzeugt von
`_antigravity_adapter_command`, `scripts/lib/hooks.py` :235–252) — der Adapter ist also nur der
Command-String, nicht der Writer. **Kein `if provider == "Name"`** — ein neuer Provider wird ohne
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
| Unterstützt der Provider Hooks **und** sind sie gespiegelt? | `config/ai-providers.yaml` | `provider_hooks_supported(pc)` — definiert in `scripts/lib/providers.py`, aufgerufen bei der Hook-Registrierung in `scripts/lib/hooks.py` (`has_hooks` + verifiziertes `hook_protocol`) |
| Wird der neue Hook per Config an-/ausgeschaltet? | `config/project-config.schema.json` | **`repo_containment.enabled` ist der einzige Master-Switch.** Es gibt **keinen** separaten `hooks.repo-containment.enabled`-Eintrag. Die Registrierung erfolgt ausschließlich über den Hook-Header `enabled_by_default: true` plus Capability (`providers.provider_hooks_supported`); der Hook liest den An/Aus-Zustand zur Laufzeit direkt aus `.meta-config/project.yaml` |
| Ist Subagent-Dispatch vorhanden? (nur Kontext) | `config/provider-capabilities.yaml` | Capability-Wert im Dict von `load_provider_capabilities(...)` (`scripts/lib/providers.py` :120) — der Loader liefert das Capabilities-Dict, der Boolean ist der jeweilige Wert darin (kein Top-Level-Boolean) |

`provider_has_capability(pc, "hooks")` ist **falsch** für diese Frage: `pc` ist der
`ai-providers.yaml`-Eintrag, dessen `capabilities: [...]`-Liste `hooks` als Listeneintrag führt,
während die Spiegelung über `has_hooks` + `hook_protocol` entschieden wird (analog
[`../../scripts/lib/consistency/orchestrator_strict.py`](../../scripts/lib/consistency/orchestrator_strict.py)).

### 4.3 Sync-Time-Validator

**`_validate_repo_containment(config, config_path)`** in `scripts/lib/config.py`, aufgerufen aus
`_validate_config` (dort schon `_validate_providers`). Muster:
Meldung auf `stderr`, dann `sys.exit(1)`. **Einziger Hard-Exit im Sync-Prozess** für
Containment — der PreToolUse-Hook kann per `exit 2` ebenfalls hart blocken, ist aber kein
Sync-Exit.

Geprüft wird:

1. `repo_containment` ist ein Mapping (falls gesetzt).
2. `enabled` ist boolean (falls gesetzt). **F4:** Ein nicht-boolescher `enabled`-Wert (String/
   Number) → **Hard-Exit** `sys.exit(1)` mit klarer Fehlermeldung, die den erwarteten Typ nennt.
   Dieselbe Regel wird aus §2.3 und §4.1 referenziert; die Runtime-Safe-Side-Fallback-Logik des
   Hooks (fehlende/unlesbare/unparsebare Config → ENABLED) gilt hier nicht, weil der Validator
   bei vorliegender, aber falsch typisierter Config hart abbricht.
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
`orchestrator_strict.py`:

- **`check_repo_containment_support(project_root, config, provider_config)`** — WARNING-only.
  Meldet, wenn Containment für einen aktiven Provider effektiv aktiv ist, dieser aber keinen
  gespiegelten Hook hat (`provider_hooks_supported == false`): Dort ist Containment ein stiller
  No-Op als Runtime-Gate und wirkt nur als Prompt-Konvention. Registrierung in
  `_handle_validate` ([`../../scripts/lib/cli_commands.py`](../../scripts/lib/cli_commands.py)) neben
  `check_orchestrator_strict_hook_support`.
- **`check_repo_containment_templates(agent_meta_root)`** — ERROR-only Framework-Drift. Prüft,
  dass Hook und Prompt-Template die erwarteten Marker/Variablen tragen. Ein **markerbasierter
  Hook↔Rule-Template-Drift-Check existiert bisher nicht** und ist damit **neu**; die bereits
  bestehenden Deployment-Drift-Checks (`check_stale_deployed_hooks`,
  `check_hook_enablement_consistency` in
  [`../../scripts/lib/consistency/hook_drift.py`](../../scripts/lib/consistency/hook_drift.py),
  aufgerufen in [`../../scripts/lib/cli_commands.py`](../../scripts/lib/cli_commands.py)
  (`_handle_validate`, dort :984–1000)) werden dabei **nicht dupliziert** — jene prüfen
  deployte Hook-Dateien und deren Enablement, nicht den Template-Marker-Abgleich. Als
  Registrierungsstelle dient der modulweite Framework-Aufrufblock in
  [`../../scripts/consistency-check.py`](../../scripts/consistency-check.py) (:181–203, nur
  wenn kein `specific_file`; dort z. B.
  [`check_role_defaults_coverage`](../../scripts/lib/consistency/crossrefs.py)).

### 4.5 Prompt-/Template-Ebene (Convention)

- Neue Rule-Sektion in `rules/1-generic/` (z. B. `repo-containment.md`) mit bedingten
  `{{#if REPO_CONTAINMENT_ENABLED}}`-Blöcken.
- Neue Variablen: `REPO_CONTAINMENT_ENABLED`, `REPO_CONTAINMENT_BLOCK`,
  `REPO_CONTAINMENT_TMP_SINK_ENABLED`, `REPO_CONTAINMENT_TMP_PATH`.
- **Pflicht:** Der `REPO_CONTAINMENT_`-Präfix muss in die fest verdrahtete
  Conditional-Allowlist von `strip_inactive_conditional_blocks` (`scripts/lib/variables.py`)
  aufgenommen werden, sonst werden die Blöcke nie gestrippt.
- **Pflicht:** Neue Platzhalter müssen in der `_BUILTIN_VARS`-Allowlist in
  [`../../scripts/lib/consistency/placeholders.py`](../../scripts/lib/consistency/placeholders.py)
  (:11–106) registriert werden. Der Sync bricht bei unbekannten Platzhaltern **nicht** ab; sie
  erzeugen lediglich ein `placeholders.unknown`-WARNING (:159–164).

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
  innerhalb des Projekt-Roots und sind daher ohnehin erlaubt. Diese Definition ist bestätigt
  (§10/Q8).

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
  verlässlichem Session-Start-Hook; Q3 entschieden: nur `manual`/`on-sync`, §10/Q3).
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
   Ziel außerhalb an und schreibt durch ihn. Der **entschiedene** `realpath`-Check mildert das
   (Q5), hat aber ein TOCTOU-Fenster (Ziel ändert sich zwischen Check und Write); dieses
   Restrisiko wird dokumentiert, Symlinks werden nicht pauschal gesperrt (§10/Q5).
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

### 6.4 Konsequenzen

Die Kombination aus Default AN und bewusst begrenzter Durchsetzung hat direkte Folgen, die das
Design in Kauf nimmt und die vor der Implementierung sichtbar sein müssen (Threat-Model-Frage 4):

- **Worst Case: Default AN blockiert legitime Writes.** Ein falsch positiver Treffer trifft
  nicht einen Angreifer, sondern den normalen Arbeitsfluss: Ein Agent kann eine beabsichtigte,
  legitime Schreiboperation außerhalb des Repo-Roots nicht mehr ausführen und erhält einen
  harten Deny. Das ist der bewusste Preis des fail-closed-Defaults.
- **Destruktiver `on-sync`-Cleanup.** Wird der Cleanup-Modus auf `on-sync` gestellt, kann jeder
  Sync-Lauf Artefakte aus `.tmp/` unwiederbringlich entfernen. Der Default bleibt deshalb
  `manual` (§5.4); `on-sync` ist ein bewusster, destruktiver Opt-in.
- **Vertrauensverlust durch „Default AN ohne Runtime-Gate" auf hook-losen Providern.** Provider
  ohne gespiegelten Hook (§6.2 Punkt 6) erhalten Containment nur als Prompt-Konvention. Wird der
  Modus dort als „aktiv" kommuniziert, ohne technisch erzwungen zu werden, entsteht eine
  trügerische Sicherheitserwartung — der WARNING-Check (§4.4) und die ehrliche Einordnung (§4.6)
  machen das sichtbar, beseitigen die Lücke aber nicht.

Diese Konsequenzen sind bewusst dokumentiert, nicht behoben: Eine Abschwächung des Defaults wäre
eine Design-Umkehr und ist nicht Teil dieses Konzepts.

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
| Sync-Time-Validator-Muster (Hard-Exit) | [`../../scripts/lib/config.py`](../../scripts/lib/config.py) (`_validate_config`, `_validate_providers`) |
| Capability-getriebene Hook-Registrierung | [`../../scripts/lib/hooks.py`](../../scripts/lib/hooks.py), [`../../scripts/lib/providers.py`](../../scripts/lib/providers.py), [`../../config/ai-providers.yaml`](../../config/ai-providers.yaml) |
| Provider-Agnostik-Policy | [`../../.opencode/skills/provider-agnostic/SKILL.md`](../../.opencode/skills/provider-agnostic/SKILL.md) |
| 0/1/2/3-Schichten-Modell | [`../../.opencode/skills/architecture/SKILL.md`](../../.opencode/skills/architecture/SKILL.md) |
| Sync-CLI/`--check`/Drift | [`../../.opencode/skills/sync-interface/SKILL.md`](../../.opencode/skills/sync-interface/SKILL.md) |
| `.gitignore`-Handling | [`../../scripts/lib/gitignore.py`](../../scripts/lib/gitignore.py) |
| Hooks-Doku (Provider-Payload) | [`../guides/features/hooks.md`](../guides/features/hooks.md) |
| Etabliertes Precedence-/Validator-Muster für `orchestrator.mode` | [`../../scripts/lib/consistency/orchestrator_strict.py`](../../scripts/lib/consistency/orchestrator_strict.py), [`active/main-chat-orchestrator-mode.md`](active/main-chat-orchestrator-mode.md), [`active/singleton-orchestrator-architecture.md`](active/singleton-orchestrator-architecture.md) |
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
  Tool-Aufrufe blockiert werden (Reparatur unmöglich). **Entschieden (Q6):** narrow carve-out wie
  #630 — `bash -n`-Selbstcheck; bei kaputtem `repo-containment-impl.sh` failt der Guard CLOSED
  für `Write`/`Edit`, bietet aber einen dokumentierten Reparatur-Kanal (§4.1, §10/Q6).
- **`on-sync`-Cleanup** ist destruktiv; Default bleibt `manual`.

### 9.2 Nicht-Ziele

- Kein OS-Sandboxing, kein Runtime-Gate auf hook-losen Providern.
- Kein Zusammenlegen/Refactoring von `orchestrator-guard` in dieser Iteration.
- Keine Änderung an `branch-guard.md` oder `rules/1-generic/branch-guard.md`.
- Keine automatische `.tmp`-Löschung per Default.
- Keine neuen Python-Dependencies, kein Provider-Namens-Branching.

### 9.3 Migrations- & Rückwärtskompatibilität

- **Additives Schema:** Bestehende Configs bleiben gültig; ohne Block greift der Default.
- **Materialisierung bei Bestandsprojekten (Q1, entschieden):** Beim Sync wird für
  Bestandsprojekte ein **expliziter** `repo_containment`-Block (Default `enabled: true` plus
  tmp-sink-Defaults) in `.meta-config/project.yaml` materialisiert. Das ist **idempotent** und
  geschieht **nur, wenn der Block fehlt**. Dadurch ist der Verhaltenswechsel sichtbar und der
  Opt-out direkt auffindbar (statt eines reinen unsichtbaren Schema-Defaults).
- **Default AN:** Verhaltensänderung (siehe 9.1) — bewusst, mit sichtbarem Opt-out.
- **`.gitignore`:** `.tmp/` kommt additiv in den Managed-Block; auf Claude-losen Projekten nur
  über den self-ignoring Fallback (§5.3), da der exakte Managed-Block Claude-gated ist.
- **Admin-UI:** Rein additive Nav/Route/View/Help-ID; bestehende Sektionen unberührt.
- **CHANGELOG-Note** unter `## [Unreleased]`; keine Versionserhöhung in diesem Konzept. Inhalt:
  (a) Verhaltenswechsel — Bestandsprojekte erhalten erstmals einen blockierenden Hook,
  (b) sichtbarer Opt-out `repo_containment.enabled: false` (bzw. Provider-Override),
  (c) einmalige Materialisierung des `repo_containment`-Blocks in `.meta-config/project.yaml`.

**Abnahmekriterien (DoD für die Implementierung):**

1. `python scripts/sync.py --validate` läuft grün (inkl. neuem `_validate_repo_containment`).
2. Die neue Hook-Test-Suite (§7) läuft grün; `python scripts/consistency-check.py` bleibt grün
   (inkl. `check_ui_help_mappings` für die neue Route).
3. Der Opt-out ist dokumentiert: `repo_containment.enabled: false` (bzw. ein Provider-Override)
   deaktiviert Containment nach einem Sync nachweislich.
4. CHANGELOG-Eintrag unter `## [Unreleased]` beschreibt den Verhaltenswechsel ehrlich.

**Rollback-Pfad:** `repo_containment.enabled: false` in `.meta-config/project.yaml` setzen und
`sync.py` erneut ausführen. Der Hook wird deregistriert und die Schreibbeschränkung entfällt;
`.tmp/`-Inhalte bleiben unberührt (Cleanup-Default `manual`), es entsteht kein Datenverlust.

---

## 10. Entschiedene Fragen (ehemals offene Fragen)

Alle vormals offenen Fragen sind entschieden; das Dokument ist damit **Accepted**.

1. **Default-AN-Migration. [entschieden]** Bestandsprojekte erhalten beim Sync einen
   **expliziten** `repo_containment`-Block in `.meta-config/project.yaml` materialisiert
   (Default `enabled: true` plus tmp-sink-Defaults), **idempotent** und nur wenn der Block fehlt.
   Der Verhaltenswechsel und der sichtbare Opt-out werden im CHANGELOG benannt (§9.3).
2. **Provider-Override-Semantik bei hook-losen Providern. [entschieden]** `enabled: true`
   bleibt dort als **Prompt-Konvention** bestehen und wird **nicht** automatisch auf `false`
   gesetzt; der Consistency-Check (§4.4) meldet die Support-Lücke als **WARNING**.
3. **Cleanup-Trigger. [entschieden]** Nur `manual` (Default) und `on-sync` (Opt-in, explizit als
   destruktiv markiert); kein Session-Start-Cleanup (§5.4).
4. **Bash-Umfang. [entschieden]** Schreibende Bash-Erkennung bleibt **best-effort** und wird
   bewusst als solche dokumentiert (analog #592, §6.2).
5. **Symlink-Politik. [entschieden]** `realpath`-Check wird angewendet; das verbleibende
   **TOCTOU-Restrisiko** wird dokumentiert (§6.2 Punkt 3), Symlinks werden nicht pauschal
   gesperrt.
6. **Hook-Selbstheilung. [entschieden]** **Narrow carve-out** (analog #630): `bash -n`-Selbstcheck
   im Wrapper; bei kaputtem `repo-containment-impl.sh` failt der Guard CLOSED für `Write`/`Edit`,
   aber mit dokumentiertem Reparatur-Kanal, damit er sich nicht selbst aussperrt (§4.1, §9.1).
7. **Hook-Interaktion. [entschieden]** `orchestrator-guard.sh` und `repo-containment.sh`
   koexistieren **unabhängig** (getrennte Registrierung, keine gemeinsame Wrapper-Logik in dieser
   Iteration).
8. **`repo root`-Definition im Submodul-Layout. [entschieden]** `repo root` ist immer das
   Verzeichnis, das `.meta-config/` enthält — auch im Submodul-Layout (agent-meta unter
   `.agent-meta/`), nicht das Git-Toplevel (§5.2).
9. **MCP-/Nicht-Tool-Schreibpfade. [entschieden]** Bleiben eine dokumentierte Grenze (§6.2
   Punkt 4) und werden in dieser Iteration **nicht** implementiert; eine separate
   MCP-Allowlist ist ein **Folge-Issue**.
10. **Issue-Aufteilung. [entschieden]** **Ein** Implementierungs-Task mit **5 Sub-Tasks**:
    (1) Config+Validator, (2) Hook, (3) `.tmp`-Sink/Gitignore, (4) Consistency, (5) Admin-UI —
    umgesetzt in diesem Lauf.
