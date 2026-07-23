# Native Extensions Whitelist — Design

**Status:** Entwurf zur Freigabe
**Branch:** `feat/knowledge-engine-phase-b` (eigenständiges Feature, teilt sich den Branch mit Phase B — siehe „Branch-Hinweis" unten)
**Kontext:** Erweiterung des bereits existierenden `orchestrator.native-extensions`-Mechanismus (Policy-Statement „native Skills/Plugins sind erlaubt") um eine aktive Whitelist, die einschränkt, WELCHE Skills/Plugins konkret erlaubt sind.

## Ausgangslage — was existiert bereits

Vor dieser Spec existiert bereits:

- `config/project-config.schema.json:993-1004` — `orchestrator.native-extensions.enabled` (boolean, default `true`)
- `scripts/lib/config.py:466-471` — liest den Block, setzt Variable `NATIVE_EXTENSIONS_ENABLED`
- `rules/1-generic/use-orchestrator.md:79-88` — rendert je nach `NATIVE_EXTENSIONS_ENABLED` einen von zwei Textblöcken (\"erlaubt\" vs. \"deaktiviert\"), propagiert in alle Provider-Regelverzeichnisse

Das ist ein reiner **An/Aus-Schalter** (gilt für alle nativen Erweiterungen gleichermaßen). Es gibt aktuell **keine Möglichkeit**, einzelne Skills/Plugins namentlich zu erlauben oder zu sperren. Das ist die Lücke, die diese Spec schließt.

**Abgrenzung zu `config/skills-registry.yaml`:** Die Skills-Registry ist ein Meta-Maintainer-Gate für 0-external-Skills, die agent-meta selbst als Submodul-Skill-Wrapper anbietet (`approved: true/false`). Die hier beschriebene Whitelist ist orthogonal dazu — sie betrifft native Plattform-Skills/Plugins (z.B. Claude-Code-Skills, die der Endnutzer selbst installiert hat), nicht agent-metas eigene Skill-Distribution. Beide Mechanismen bleiben getrennt.

## Entscheidung: Whitelist nested unter `orchestrator.native-extensions`

Ursprünglich war ein neuer Top-Level-Block `native-extensions:` in `project.yaml` vorgesehen (Ansatz A). Bei der Umsetzung wurde festgestellt, dass `orchestrator.native-extensions.enabled` bereits existiert — ein neuer, gleichnamiger Top-Level-Block hätte zwei Konfigurationspfade mit identischem Namen aber unterschiedlicher Bedeutung erzeugt (`orchestrator.native-extensions.enabled` = Gate-Bypass, top-level `native-extensions.whitelist` = Berechtigungsliste). Auf Nutzerentscheidung wird die Whitelist stattdessen in den **bestehenden** `orchestrator.native-extensions`-Block eingefügt:

```yaml
orchestrator:
  native-extensions:
    enabled: true        # bestehend — Policy-Statement + Gate-Bypass
    whitelist: []         # NEU — leer = kein Filter; nicht-leer = Allow-Only
```

**Vorteil:** ein einziger Konfigurationspfad für „native Erweiterungen", keine Doppel-Benennung, keine Verwechslungsgefahr.

## Anpassbarkeit: Framework-Defaults UND Projekt-Settings

Beide Ebenen müssen greifen — wie beim bereits etablichten Preset-Muster (`config/dod-presets.yaml` + `dod-preset`/`dod` in `project.yaml`, Precedence `dod > dod-preset > full`):

| Ebene | Ort | Zweck |
|-------|-----|-------|
| **Framework-Default** | `config/project-config.schema.json` (`default: true` / `default: []`) | Gilt für jedes Projekt, das das Feld nicht setzt. |
| **Framework-Default (Beispiel)** | `howto/project.yaml.example` | Dokumentiert die empfohlene Ausgangskonfiguration für neue Projekte (Kommentar-Block, keine Pflicht-Werte). |
| **Projekt-Override** | `<projekt>/.meta-config/project.yaml` → `orchestrator.native-extensions.whitelist` | Jedes Projekt setzt seine eigene, konkrete Liste erlaubter Skills/Plugins. Fehlt der Schlüssel → Framework-Default (leere Liste = kein Filter) greift. |
| **Admin-UI** | `docs/ui/admin-ui.html`, Panel „Orchestrator" | Liest/schreibt denselben `orchestrator.native-extensions`-Block wie `project.yaml` — keine eigene Datenquelle, nur ein Editor darauf. |

Kein neues Presets-File nötig: Anders als bei DoD gibt es keine sinnvollen „Preset-Varianten" einer Skill-Whitelist (sie ist projektspezifisch, keine Stufen wie `rapid-prototyping`/`full`). Die zweistufige Anpassbarkeit ergibt sich bereits aus Schema-Default + Projekt-Override, exakt wie bei `checkpointing`, `strict` usw.

## Whitelist-Semantik (Option B — verbindlich, wortwörtlich)

> **Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement.**

Dieser Satz muss **wortwörtlich** in folgenden Stellen erscheinen:
1. `config/project-config.schema.json` → `description` von `orchestrator.native-extensions.whitelist`
2. `rules/1-generic/use-orchestrator.md` → gerenderter Regeltext, wenn die Whitelist nicht leer ist
3. Admin-UI → Hilfetext/Tooltip neben dem Whitelist-Editor-Feld

**Konkret:**
- `whitelist: []` (Default) → kein Filter, das bestehende `enabled`-Verhalten (An/Aus für alle nativen Erweiterungen) bleibt unverändert.
- `whitelist: ["superpowers", "code-simplifier"]` → nur diese zwei Skills/Plugins dürfen laufen; jedes andere native Skill/Plugin ist gesperrt, selbst wenn `enabled: true` gesetzt ist.
- `enabled: false` bleibt weiterhin der übergeordnete Schalter: ist er `false`, sind native Erweiterungen komplett deaktiviert — die Whitelist wird in diesem Fall gar nicht ausgewertet (kein Widerspruch möglich, da „aus" Vorrang vor jeder Positivliste hat).

## Config-Schema

Erweiterung des bestehenden `orchestrator.native-extensions`-Objekts in `config/project-config.schema.json:993-1004`:

```json
"native-extensions": {
  "type": "object",
  "description": "Exempt platform-native extension mechanisms (Skills, Plugins, Lifecycle-Hooks) from the STRICT-mode orchestrator gate. When enabled, platform-triggered flows are not treated as a delegation bypass. Default: true.",
  "properties": {
    "enabled": {
      "type": "boolean",
      "default": true,
      "description": "Allow native extension mechanisms to run without going through the orchestrator gate. Branch-guard, commit-conventions and DoD still apply to resulting code changes. Default: true."
    },
    "whitelist": {
      "type": "array",
      "items": { "type": "string" },
      "default": [],
      "uniqueItems": true,
      "description": "Whitelist of allowed native Skill/Plugin identifiers. Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement. Empty (default) = no filter."
    }
  },
  "additionalProperties": false
}
```

## Variablen-Injektion

Erweiterung von `scripts/lib/config.py:466-471` (direkt im Anschluss an die bestehende `NATIVE_EXTENSIONS_ENABLED`-Zeile):

```python
_native_ext_whitelist = _native_ext_cfg.get("whitelist", []) if isinstance(_native_ext_cfg, dict) else []
variables["NATIVE_EXTENSIONS_WHITELIST_ACTIVE"] = "true" if _native_ext_whitelist else "false"
variables["NATIVE_EXTENSIONS_WHITELIST_TABLE"] = (
    "\n".join(f"- `{s}`" for s in _native_ext_whitelist) if _native_ext_whitelist else ""
)
```

`NATIVE_EXTENSIONS_WHITELIST_ACTIVE` steuert einen weiteren `{{#if}}`-Block in `rules/1-generic/use-orchestrator.md`; `NATIVE_EXTENSIONS_WHITELIST_TABLE` liefert die gerenderte Liste (eine Markdown-Bullet-Zeile pro erlaubtem Skill/Plugin-Identifier).

Diese beiden neuen Variablen werden außerdem in die conditional-vars-Menge in `scripts/lib/config.py:695` aufgenommen (`NATIVE_EXTENSIONS_WHITELIST_ACTIVE` neben `NATIVE_EXTENSIONS_ENABLED`), damit sie in der generierten CLAUDE.md korrekt als struktureller (nicht neu zu diffender) Block behandelt werden.

## Regel-Template-Änderung

Erweiterung von `rules/1-generic/use-orchestrator.md` (im bestehenden `{{#if NATIVE_EXTENSIONS_ENABLED}}`-Block, Zeilen 79-83):

```
{{#if NATIVE_EXTENSIONS_ENABLED}}
## Native Provider-Erweiterungen

Native Erweiterungsmechanismen der Plattform — Skills, Plugins, Lifecycle-Hooks — werden von diesem Gate NICHT blockiert. Sie laufen im Rahmen des eigenen Invocation-Flows der Plattform (z.B. ein SessionStart-Hook, der eine Skill lädt) und zählen nicht als `task`-Call oder `edit`/`write`-Aktion im Sinne dieser Regel. Folge ihren Anweisungen gemäß Plattform-Konvention. Das hebt Branch-Guard, Commit-Konventionen und DoD-Criteria NICHT auf — die gelten weiterhin für jede daraus resultierende Code-Änderung.

{{#if NATIVE_EXTENSIONS_WHITELIST_ACTIVE}}
**Whitelist aktiv:** Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement.

Erlaubte Skills/Plugins:
{{NATIVE_EXTENSIONS_WHITELIST_TABLE}}
{{/if}}
{{/if}}
```

**Wichtig:** Die Durchsetzung erfolgt — wie beim gesamten Regel-Mechanismus dieses Repos — über den generierten Regeltext, den der Agent zur Laufzeit liest und befolgt (keine Code-Ebene, die eine Skill-Ausführung technisch blockieren könnte; native Skills/Plugins laufen im Invocation-Flow der jeweiligen Plattform, außerhalb von agent-metas Kontrolle). Diese Spec fügt eine verbindliche Verhaltensregel hinzu, kein technisches Sandboxing.

## Admin-UI

Erweiterung des bestehenden Orchestrator-Panels (`docs/ui/admin-ui.html`, Funktion um Zeile 4536-4557, Route `/project/orchestrator`):

- Bestehend: `checkboxField("checkpointing", ...)` neben weiteren Orchestrator-Feldern.
- **Neu:** innerhalb desselben Panels ein Unterabschnitt „Native Extensions":
  - Checkbox für `orchestrator.native-extensions.enabled` (analog zu `checkboxField`).
  - Array-Editor für `orchestrator.native-extensions.whitelist` — wiederverwendet das bestehende generische Array-Feld-Pattern (`docs/ui/admin-ui.html:1036`, `schema.type === "array"` bzw. die String-Array-Erkennung um Zeile 1812), keine neue UI-Komponente nötig.
  - Hilfetext direkt am Whitelist-Feld, wortwörtlich: „Ist die Whitelist nicht leer, sind ausschließlich die dort gelisteten Skills/Plugins erlaubt — alles andere wird automatisch gesperrt, unabhängig vom generellen Erlaubt-Statement."
- Speichern über den bestehenden `saveProjectSection("orchestrator", orch, status)`-Aufruf (Zeile 4755) — kein neuer REST-Endpoint nötig, da `native-extensions` bereits Teil des `orchestrator`-Objekts ist, das dieser Call komplett schreibt.

## Fehlerbehandlung

- Whitelist-Einträge sind reine Strings (Skill-/Plugin-Identifier laut Plattform-Konvention, z.B. `superpowers`, `code-simplifier`) — keine Validierung gegen eine bekannte Liste installierter Skills, da agent-meta zur Sync-Zeit nicht weiß, welche nativen Skills auf der Zielmaschine installiert sind. Tippfehler in der Whitelist führen dazu, dass ein eigentlich gewünschtes Skill fälschlich gesperrt wird — das ist eine Nutzerverantwortung, kein Sync-Fehler.
- `whitelist` als nicht-Array (z.B. String) → Schema-Validierung schlägt fehl (Phase 1 von `sync.py`), Sync stoppt vor Variablen-Injektion.
- `enabled: false` mit nicht-leerer `whitelist` → kein Konflikt, kein Fehler; die Whitelist wird schlicht nicht gerendert, da der äußere `{{#if NATIVE_EXTENSIONS_ENABLED}}`-Block sie umschließt.

## Testing

- Unit-Test: `build_variables()` mit `orchestrator.native-extensions.whitelist: []` (oder Block fehlt) → `NATIVE_EXTENSIONS_WHITELIST_ACTIVE == "false"`, `NATIVE_EXTENSIONS_WHITELIST_TABLE == ""`.
- Unit-Test: `build_variables()` mit `whitelist: ["superpowers", "code-simplifier"]` → `NATIVE_EXTENSIONS_WHITELIST_ACTIVE == "true"`, Tabelle enthält beide Einträge als `- \`superpowers\`` / `- \`code-simplifier\``.
- Regressionstest: bestehende `NATIVE_EXTENSIONS_ENABLED`-Tests bleiben unverändert grün (keine Verhaltensänderung, wenn `whitelist` fehlt).
- Schema-Test: `orchestrator.native-extensions.whitelist` als String statt Array → `sync.py --dry-run --validate` schlägt fehl.
- Integrationstest: `sync.py --dry-run` mit gesetzter Whitelist auf einem Testprojekt → generierte `use-orchestrator.md`-Regel enthält den Options-B-Satz wortwörtlich und die Skill-Liste.

## Out of Scope

- Technisches Sandboxing/Blockieren einzelner nativer Skills auf Plattform-Ebene — außerhalb der Kontrolle von agent-meta (Plattform-Invocation-Flow, siehe oben). Diese Spec liefert die Verhaltensregel, keine Erzwingung durch einen Hook.
- Presets/Vorlagen für typische Whitelist-Zusammenstellungen (z.B. „nur superpowers") — YAGNI, kann bei Bedarf als eigene Spec nachgezogen werden.
- Migration bestehender Projekte auf eine nicht-leere Default-Whitelist — Default bleibt `[]` (kein Filter), das ist die Zero-Overhead-Garantie für alle Projekte, die dieses Feature nicht aktiv nutzen.

## Branch-Hinweis

Diese Spec entsteht auf `feat/knowledge-engine-phase-b`, da der Branch zum Zeitpunkt der Spec-Erstellung bereits ausgecheckt war. Da dieses Feature inhaltlich unabhängig von Knowledge-Engine-Phase-B ist, wird vor Beginn der Implementierung ein eigener Branch (`feat/native-extensions-whitelist`, von `main` oder von `feat/knowledge-engine` abgezweigt) empfohlen, um die beiden Feature-Linien sauber zu trennen — analog zur bereits erfolgten Trennung von Phase A und Phase B.
