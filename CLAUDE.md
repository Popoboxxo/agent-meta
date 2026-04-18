# agent-meta — Meta-Repository für Agenten-Standards

## Zweck

Dieses Repository ist das **zentrale Meta-Repository** für die Standardisierung und
Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

---

## Kernprinzipien

**1. `CLAUDE.md` des Projekts ist die einzige Wahrheit.**
Sie beschreibt das Projekt vollständig (Ziel, Tech-Stack, Architektur, Konventionen).
Agenten lesen sie beim Start — sie enthalten keinen eigenen Kontext-Block.

**2. `.claude/agents/` ist generierter Output — nie manuell bearbeiten.**
Dateien werden von `sync.py` erzeugt und bei jedem Sync überschrieben.
Änderungen gehören in `.meta-config/project.yaml` (Variablen) oder die Agent-Quelldateien.

**3. Agenten haben generische Namen — kein Prefix.**
Ein Projekt pro Workspace. Die Agenten heißen `developer.md`, `tester.md` etc.
Kein `vwf-developer.md` oder `hi-tester.md` mehr.

**4. Projektspezifische Erweiterungen gehören in `.claude/3-project/`.**
Nicht in die generierten Agenten, nicht als Config-Variable.
Der generierte Agent liest die Erweiterungsdatei selbst zur Laufzeit.

---

## Schichten-Modell

```
0-external/   Externe Skill-Agenten aus Drittrepos (via Git Submodule).
              Höchste Priorität. Konfiguriert in config/skills-registry.yaml.
              approved: true/false — Meta-Maintainer Quality Gate.
              Projekte aktivieren Skills via "external-skills" in .meta-config/project.yaml.

1-generic/    Universell. Gilt für jedes Projekt. Wird immer generiert,
              solange kein Override in 2-platform oder 3-project existiert.

2-platform/   Plattformspezifisch. Überschreibt den Generic-Agent für alle
              Projekte auf dieser Plattform (z.B. alle Sharkord-Plugins).
              Zwei Modi:
              - Full-replacement (kein extends: im Frontmatter): Datei wird 1:1 verwendet
              - Composition (extends: + patches: im Frontmatter): sync.py komponiert
                aus Base + Patches. Sections können ergänzt, ersetzt oder gelöscht werden.

3-project/    Projektspezifisch. Zwei Arten:
              - <rolle>.md      → Override: ersetzt den generierten Agenten komplett
                                  Unterstützt ebenfalls extends:/patches: (Composition)
              - <rolle>-ext.md  → Extension: wird vom generierten Agenten additiv geladen
```

**Override-Reihenfolge (für generierte Agenten):**
```
1-generic  →  2-platform  →  3-project/<rolle>.md  →  0-external (eigenständige Rollen)
```

**Composition (2-platform und 3-project Overrides):**
```
extends: "1-generic/<rolle>.md"   ← Base-Template
patches:                          ← Operationen auf Markdown-Sections
  - op: append-after              ← nach Section einfügen
    anchor: "## Section Name"
    content: |
      ## Neuer Abschnitt ...
  - op: replace                   ← Section vollständig ersetzen
    anchor: "## Section Name"
    content: |
      ## Section Name (neu) ...
  - op: delete                    ← Section entfernen
    anchor: "## Section Name"
  - op: append                    ← ans Dateiende anhängen
    content: |
      ## Anhang ...
```
Composition wird von sync.py zur Build-Zeit aufgelöst — das generierte `.claude/agents/<rolle>.md`
enthält das vollständige, fertig zusammengesetzte Dokument. Kein `extends:` im Output.

**Extension (additiv, kein Override):**
```
generierter Agent  +  .claude/3-project/<rolle>-ext.md  =  voller Agent-Kontext
```
Extension-Dateien leben **ausschließlich im Zielprojekt** — sie werden von sync.py
nie berührt. Erstellen, bearbeiten und versionieren liegt vollständig beim Projekt.

---

## Verzeichnisstruktur

```
agent-meta/
  agents/
    1-generic/          ← universell, plattformunabhängig
      orchestrator.md
      developer.md
      tester.md
      validator.md
      requirements.md
      documenter.md
      release.md
      docker.md
      git.md

    2-platform/         ← plattformspezifisch (überschreibt 1-generic)
      sharkord-docker.md
      sharkord-release.md

    3-project/          ← projektspezifisch (im Meta-Repo als Vorlage, selten)
      developer-ext.md  ← Beispiel: Extension-Vorlage für developer
                           Overrides: <rolle>.md (ersetzt komplett)
                           Extensions: <rolle>-ext.md (additiv geladen)

    0-external/         ← Wrapper-Template für externe Skill-Agenten
      _skill-wrapper.md ← generisches Template (einmalig, nie manuell bearbeiten)

  external/             ← Git Submodule (externe Skill-Repos, via --add-skill)
    <repo-name>/        ← gepinnter Commit, enthält SKILL.md + Referenzdokumente

  .meta-config/
    project.yaml               ← Projekt-Config für dieses Repo (Self-Hosting) — wie jedes Zielprojekt

  config/                      ← Framework-Defaults (nie manuell bearbeiten)
    project.yaml               ← HINWEIS-STUB — kein Fallback mehr (Projekt-Config → .meta-config/)
    role-defaults.yaml         ← Rollen-Defaults: model, memory, permissionMode, tier
                                  Projekte überschreiben via *-overrides in .meta-config/project.yaml
    dod-presets.yaml           ← DoD-Qualitätsprofile (full, standard, rapid-prototyping)
    ai-providers.yaml          ← Provider-Konfiguration (Claude, Gemini, Continue)
                                  Neuen Provider hinzufügen ohne Python-Code-Änderung
    skills-registry.yaml       ← Zentrale Skill-Registry (Modell A)
                                  repos: Repo-Definitionen mit pinned_commit (1:n zu skills)
                                  skills: Skill-Einträge mit approved:true/false
    project-config.schema.json ← JSON Schema für .meta-config/project.yaml (IDE-Validierung)

  howto/
    first-steps.md               ← Geführte Ersteinrichtung via AI-Assistent (vor erstem Sync)
    instantiate-project.md       ← Schritt-für-Schritt Einrichtung
    external-skills.md           ← External Skills: vollständige Anleitung (Lifecycle, Troubleshooting)
    agent-composition.md         ← Composition-System: extends/patches, Patch-Ops, Beispiele
    upgrade-guide.md              ← Upgrade auf neue agent-meta Version
    CLAUDE.project-template.md    ← Template für CLAUDE.md im Zielprojekt
    CLAUDE.personal-template.md   ← Template für CLAUDE.personal.md (gitignored, persönlich)
    rules.md                          ← Rules-System: Schichten, Sync, create-rule
    hooks.md                          ← Hooks-System: Schichten, Sync, create-hook, dod-push-check
    agent-isolation.md                ← isolation: worktree — Konfiguration, Fallstricke, Feature-Agent
    agent-delegation-map.md           ← Delegations-Matrix: wer delegiert an wen, parallelisierbare Schritte
    platform-config.md                ← Platform Config Instantiation: {{platform.*}}-Platzhalter, Defaults, Overrides
    sync-concept.md
    template-gap-analysis.md

  rules/
    0-external/         ← Rules aus externen Skill-Repos
    1-generic/          ← universelle Regeln, gelten für alle Projekte
    2-platform/         ← plattformspezifisch (überschreibt 1-generic bei gleichem Namen)
                          Naming: <platform>-<thema>.md → <thema>.md im Output

  hooks/
    0-external/         ← Hooks aus externen Skill-Repos
    1-generic/          ← universelle Hooks, gelten für alle Projekte
    2-platform/         ← plattformspezifisch (überschreibt 1-generic bei gleichem Namen)
                          Naming: <platform>-<thema>.sh → <thema>.sh im Output

  snippets/
    tester/
      bun-typescript.md    ← Sprachspezifische Test-Snippets für TypeScript/Bun
      pytest-python.md     ← Sprachspezifische Test-Snippets für Python/pytest
    developer/
      bun-typescript.md    ← Code-Patterns & Best Practices für TypeScript/Bun
      pytest-python.md     ← Code-Patterns & Best Practices für Python

  speech/
    full.md              ← Placeholder (kein Output — Default-Verhalten)
    short.md             ← Fakten-Stil: kein Filler, nur Ergebnisse
    childish.md          ← Kindgerechter Stil: spielerisch, Tier-/Spielzeug-Analogien
    caveman.md           ← Höhlenmensch-Stil: kurz, direkt, abgehakt
    asozial.md           ← New-Kids-Stil: fachlich korrekt, aber mit Verachtung und Beleidigungen

  platform-configs/
    homeassistant.defaults.yaml  ← Default-Werte für {{platform.homeassistant.*}}-Platzhalter
                                    Leerer String = Pflichtfeld (User muss überschreiben)
                                    Nicht-leerer Wert = sinnvoller Default

  scripts/
    sync.py              ← CLI-Entrypoint (nur argparse + main)
    lib/                 ← Logik-Module (je ≤600 Zeilen, LLM-lesbar)
      agents.py          ← Frontmatter, Composition, sync_agents
      config.py          ← load_config, build_variables, fill_defaults
      context.py         ← init_claude_md, sync_context, gitignore
      dod.py             ← load_dod_presets, resolve_dod
      extensions.py      ← create_extension, update_extensions
      hooks.py           ← sync_hooks, create_hook
      io.py              ← YAML/JSON-Loader
      log.py             ← SyncLog
      platform.py        ← load_platform_config, substitute_platform
      providers.py       ← load_providers_config, resolve_providers
      roles.py           ← load_roles_config, build_role_map, Resolver
      rules.py           ← sync_rules, sync_speech_mode, create_rule
      skills.py          ← External Skills: load, sync, add

  templates/
    managed-block.md              ← Extension-managed-block Template
    managed-block-project-stub.md ← Projektbereich-Stub für neue Extensions
    claude-md-managed.md          ← CLAUDE.md managed-block Template

```

---

## Agenten im Zielprojekt

### Generierte Agenten (Self-Hosting)

<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

Generiert von agent-meta v0.27.0 — `2026-04-18`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false

> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben.

| Agent | Zuständigkeit |
|-------|--------------|
| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projektspezifische Agenten anlegen |
| `agent-meta-scout` | Claude-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns für agent-meta entdecken |
| `developer` | Feature-Implementierung und Bugfixes im agent-meta Framework (Python, Markdown, YAML) |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README, Erkenntnisse |
| `feature` | Neues Feature end-to-end durchführen: Branch → REQ → TDD → Dev → Validate → PR |
| `git` | Commits, Branches, Tags, Push/Pull und alle Git-Operationen |
| `ideation` | Neue Ideen explorieren, Vision schärfen, Übergabe an requirements |
| `meta-feedback` | Verbesserungsvorschläge für agent-meta als GitHub Issues einreichen |
| `orchestrator` | Einstiegspunkt für alle Entwicklungsaufgaben — koordiniert alle anderen Agenten |
| `release` | Versioning, Changelog, Build-Artifact, GitHub Release erstellen |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben, REQUIREMENTS.md pflegen |
<!-- agent-meta:managed-end -->

### Update-Verhalten bei sync

| Datei | Sync-Verhalten | Committed? |
|-------|---------------|------------|
| `.meta-config/project.yaml` | ❌ Nie von sync.py berührt — Projekt schreibt selbst | Ja |
| `.claude/agents/*.md` (generiert) | ✅ Immer überschrieben; veraltete Dateien werden gelöscht | Ja |
| `CLAUDE.md` — managed block | ✅ Immer aktualisiert | Ja |
| `CLAUDE.md` — Rest | ❌ Einmalig angelegt, dann manuell | Ja |
| `CLAUDE.personal.md` | ❌ Einmalig angelegt aus Template | Nein (gitignored) |
| `.claude/settings.json` (Skeleton) | ❌ Einmalig angelegt; danach manuell verwaltet | Ja |
| `.claude/settings.json` — `hooks`-Section | ✅ Bei jedem sync gemergt (aktivierte Hooks) | Ja |
| `.claude/settings.local.json` | ❌ Einmalig via `--init` angelegt | Nein (gitignored) |
| `.gitignore` | ✅ Fehlende Einträge werden ergänzt | Ja |
| `.claude/3-project/*-ext.md` (Extension) | ❌ Einmalig via `--create-ext` | Ja |
| `.claude/3-project/*.md` (Override) | ❌ Nicht von sync.py berührt | Ja |
| `.claude/rules/*.md` (Rules, agent-meta-verwaltet) | ✅ Immer überschrieben; Stale-Rules werden gelöscht | Ja |
| `.claude/rules/*.md` (Projekt-eigene Rules) | ❌ Nie angefasst (nicht in `.agent-meta-managed`) | Ja |
| `.claude/hooks/*.sh` (Hooks, agent-meta-verwaltet) | ✅ Immer überschrieben; Stale-Hooks werden gelöscht | Ja |
| `.claude/hooks/*.sh` (Projekt-eigene Hooks) | ❌ Nie angefasst (nicht in `.agent-meta-managed`) | Ja |

**CLAUDE.md managed block** — eingeleitet durch `<!-- agent-meta:managed-begin -->`:
- Wird von `sync.py` bei **jedem normalen sync** automatisch aktualisiert
- Enthält: Agenten-Hints-Tabelle (`AGENT_HINTS`) mit Orchestrator-Einstiegspunkt + agent-meta Version + Datum
- Manuelle Änderungen innerhalb des Blocks werden überschrieben
- Kein managed block in `CLAUDE.md` → sync gibt `[WARN]` aus mit Hinweis zum manuellen Einfügen
- `--init` erstellt `CLAUDE.md` aus Template inkl. managed block (nur wenn nicht vorhanden)

---

## Projektspezifische Anpassungen

### Entscheidungsbaum

```
Was brauche ich?
│
├─ Einfacher Wert (Kommando, kurzer Text, Liste)?
│   → Variable in .meta-config/project.yaml
│   → Wird per {{PLATZHALTER}} in den Agenten injiziert
│   → Beispiele: BUILD_COMMAND, CODE_CONVENTIONS, REQ_CATEGORIES
│
├─ Strukturiertes Zusatzwissen (SDK-Patterns, E2E-Workflow, Plattform-Regeln)?
│  Gilt es für ALLE Projekte auf einer Plattform?
│   → Ja → 2-platform/<plattform>-<rolle>.md
│           - Additive Sections / Section-Ersatz: extends: + patches:  ← COMPOSITION
│           - Komplett anderer Aufbau: kein extends: (Full-replacement)
│   → Nein (nur dieses Projekt) → .claude/3-project/<rolle>-ext.md  ← EXTENSION
│
└─ Fundamentaler Unterschied — anderer Workflow, andere Struktur, anderes Tooling?
    → .claude/3-project/<rolle>.md  ← OVERRIDE
       Tipp: Auch hier ist extends: + patches: möglich statt Vollkopie!
```

### Extension: `.claude/3-project/<rolle>-ext.md`

- Handgeschriebene Markdown-Datei im Zielprojekt
- Wird vom generierten Agenten **beim Start automatisch gelesen** (Extension-Hook)
- Liegt im Zielprojekt unter `.claude/3-project/<prefix>-<rolle>-ext.md`
- Wird via `--create-ext <rolle>` (oder `--create-ext all`) erstellt
- Enthält einen **managed block** (`<!-- agent-meta:managed-begin/end -->`) mit auto-generiertem Kontext aus config-Variablen — aktualisierbar via `--update-ext`
- Darunter: handgeschriebener Projektbereich — von sync.py **nie angefasst**
- Das Meta-Repo stellt **keine** Extension-Vorlagen bereit — alles Projektdomäne

**Extension-Hook** (in jedem generierten Agenten):
```markdown
Falls die Datei `.claude/3-project/<prefix>-<rolle>-ext.md` existiert:
Lies sie jetzt sofort mit dem Read-Tool und wende alle Regeln vollständig an.
```

**sync.py Extension-Kommandos:**
```bash
# Extension erstmalig anlegen (managed block + leerer Projektbereich)
py .agent-meta/scripts/sync.py --create-ext developer
py .agent-meta/scripts/sync.py --create-ext all

# Managed block in allen bestehenden Extensions aktualisieren
py .agent-meta/scripts/sync.py --update-ext
```

### Override: `.claude/3-project/<rolle>.md`

- Liegt direkt im Zielprojekt (nicht von sync.py berührt)
- Wenn vorhanden im Meta-Repo unter `3-project/<rolle>.md`: wird wie 1-generic/2-platform behandelt, aber mit höchster Priorität
- Bekommt **keine automatischen Updates** — manuelle Pflege nötig
- Nur wenn Extension nicht reicht

---

## Config-Felder

### `ai-provider` — AI Provider (optional, empfohlen)

```json
"ai-provider": "Claude"
```

Steuert provider-spezifisches Verhalten von `sync.py`:

| Wert | Verhalten |
|------|-----------|
| `"Claude"` | `CLAUDE.md` wird automatisch erstellt (wenn nicht vorhanden) + managed block bei jedem sync aktualisiert |
| Anderer Wert / fehlt | Kein `CLAUDE.md`-Handling — weder Erstellen noch Update |

Verfügbare Werte: `Claude`, `GitHub` (weitere folgen bei Bedarf)

---

### `roles` — Agenten-Whitelist (optional)

```json
"roles": ["orchestrator", "developer", "tester", ...]
```

Fehlt der Key → alle Rollen aus `1-generic/` + aktiven `2-platform/`-Overrides werden generiert (Rückwärtskompatibel).
Ist der Key vorhanden → nur die gelisteten Rollen werden generiert. Alle anderen werden mit `[SKIP]` im Log übersprungen.

**Rollen-Klassifizierung (Empfehlung — gesteuert via `tier` in `config/role-defaults.yaml`):**

| Stufe | Rollen | Bedeutung |
|-------|--------|-----------|
| **Pflicht** | `orchestrator`, `developer`, `git` | Ohne diese funktioniert kein Workflow |
| **Empfohlen** | `tester`, `validator`, `documenter`, `requirements`, `feature` | Standard-Qualitäts-Workflow |
| **Optional** | `ideation`, `release`, `docker`, `security-auditor`, `meta-feedback`, `agent-meta-manager`, `agent-meta-scout`, `openscad-developer` | Bei Bedarf aktivieren |

Die Klassifizierung ist eine **Empfehlung** — per Default werden alle Rollen generiert.
Der User steuert über `roles` welche tatsächlich angelegt werden.

---

### `model-overrides` — Modell-Zuweisung pro Rolle (optional)

```json
"model-overrides": {
  "git":       "haiku",
  "developer": "opus"
}
```

Überschreibt das von agent-meta empfohlene Modell für einzelne Rollen.
`sync.py` injiziert das `model:`-Feld beim Generieren der Agenten-Datei.

**Precedence (höchste zuerst):**
1. Projekt-Override (`model-overrides` in `.meta-config/project.yaml`)
2. Meta-Default (`config/role-defaults.yaml` im agent-meta Root — vom Meta-Maintainer gepflegt)
3. Kein Eintrag → kein `model:`-Feld → Agent erbt das Modell vom Parent-Kontext

**Meta-Defaults (Stand v0.16.2):**

| Rolle | Default | Begründung |
|-------|---------|------------|
| `orchestrator` | *(leer)* | Volle Kapazität — Routing braucht Kontext |
| `developer` | *(leer)* | Volle Kapazität — komplexe Implementierung |
| `requirements` | *(leer)* | Volle Kapazität — nuancierte Anforderungsanalyse |
| `ideation` | *(leer)* | Volle Kapazität — kreative Exploration |
| `feature` | *(leer)* | Volle Kapazität — End-to-End-Workflow |
| `tester` | `sonnet` | Test-Schreiben braucht Präzision |
| `validator` | `sonnet` | Traceability-Audit braucht sorgfältiges Reasoning |
| `documenter` | `sonnet` | Dokumentationsqualität |
| `security-auditor` | `sonnet` | Sicherheitsanalyse braucht Sorgfalt |
| `agent-meta-scout` | `sonnet` | Web-Research + Evaluation |
| `agent-meta-manager` | `sonnet` | Framework-Management |
| `release` | `sonnet` | Changelog + Versioning |
| `git` | `haiku` | Shell-Operationen, kein Deep-Reasoning |
| `meta-feedback` | `haiku` | Issue-Formatierung, leichtgewichtig |
| `docker` | `haiku` | Docker-Kommandos, straightforward |
| `openscad-developer` | `sonnet` | 3D-Modellierung braucht Präzision + Render-Feedback |

Gültige Werte: `"haiku"`, `"sonnet"`, `"opus"` (oder vollständige Modell-IDs).

---

### `memory-overrides` — Persistentes Gedächtnis pro Rolle (optional)

```json
"memory-overrides": {
  "validator": "local",
  "developer": "project"
}
```

Überschreibt den von agent-meta empfohlenen Memory-Scope für einzelne Rollen.
`sync.py` injiziert das `memory:`-Feld beim Generieren der Agenten-Datei.

**Precedence (höchste zuerst):**
1. Projekt-Override (`memory-overrides` in `.meta-config/project.yaml`)
2. Meta-Default (`config/role-defaults.yaml` — vom Meta-Maintainer gepflegt)
3. Kein Eintrag → kein `memory:`-Feld → Agent hat kein persistentes Gedächtnis

**Memory-Scopes:**

| Scope | Speicherort | In Git? | Wann nutzen |
|-------|------------|---------|-------------|
| `project` | `.claude/agent-memory/<name>/` | ✅ ja | Projekt-Wissen mit Team teilen |
| `local` | `.claude/agent-memory-local/<name>/` | ❌ gitignored | Projekt-Wissen, nicht committen |
| `user` | `~/.claude/agent-memory/<name>/` | ❌ lokal | Projektübergreifendes Wissen |

**Meta-Defaults (Stand v0.16.4):**

| Rolle | Memory | Was akkumuliert wird |
|-------|--------|---------------------|
| `validator` | `project` | REQ-Muster, bekannte Traceability-Lücken |
| `documenter` | `project` | Architektur-Entscheidungen, Doku-Konventionen |
| `requirements` | `project` | REQ-Kategorien, bekannte Anforderungs-Muster |
| `security-auditor` | `project` | Findings aus vorherigen Audits |
| `agent-meta-scout` | `local` | Bewertete Repos, entdeckte Skills (nicht in git) |
| `openscad-developer` | `local` | Gelernte Toleranzen, Drucker-Profile, bewährte Patterns |
| alle anderen | *(leer)* | Kein persistentes Gedächtnis |

Siehe [howto/features/agent-memory.md](howto/features/agent-memory.md) für vollständige Dokumentation.

---

### `permission-mode-overrides` — Berechtigungsmodus pro Rolle (optional)

```json
"permission-mode-overrides": {
  "validator": "plan",
  "developer": "acceptEdits"
}
```

Überschreibt den von agent-meta empfohlenen Berechtigungsmodus für einzelne Rollen.
`sync.py` injiziert das `permissionMode:`-Feld beim Generieren der Agenten-Datei.

**Precedence (höchste zuerst):**
1. Projekt-Override (`permission-mode-overrides` in `.meta-config/project.yaml`)
2. Meta-Default (`config/role-defaults.yaml` — vom Meta-Maintainer gepflegt)
3. Kein Eintrag → kein `permissionMode:`-Feld → Agent erbt den Modus vom Parent-Kontext

**Gültige Werte:**

| Wert | Verhalten |
|------|-----------|
| `plan` | Read-only — Agent kann keine Dateien schreiben oder Befehle ausführen |
| `acceptEdits` | Datei-Edits automatisch akzeptieren, Ausführung manuell bestätigen |
| `bypassPermissions` | Alle Berechtigungen automatisch akzeptiert (nur für vertrauenswürdige Umgebungen) |
| `default` | Normales interaktives Verhalten |

**Meta-Defaults:**

| Rolle | permissionMode | Grund |
|-------|---------------|-------|
| `validator` | `plan` | Reiner Auditor — darf niemals Dateien ändern |
| `security-auditor` | `plan` | Statische Analyse — kein Write-Zugriff nötig |
| alle anderen | *(leer)* | Standard-Verhalten |

---

### `max-parallel-agents` — Maximale parallele Agenten (optional)

```json
"max-parallel-agents": 2
```

Steuert wie viele Agenten ein Koordinator (orchestrator, feature) gleichzeitig
via `run_in_background: true` starten darf.

| Wert | Verhalten |
|------|-----------|
| `1` | Sequentiell — keine Parallelisierung (sicherstes Default) |
| `2` | **Default** — ein Agent im Vordergrund, einer im Hintergrund |
| `3`–`5` | Mehrere Background-Agenten — nur für leistungsstarke Setups |

`sync.py` injiziert den Wert als `{{MAX_PARALLEL_AGENTS}}` in die Orchestrator- und Feature-Templates.
Dort steuert er welche Workflow-Schritte (markiert mit `∥`) parallel ausgeführt werden.

**Modell-Kosten beachten:** Zwei `opus`-Agenten parallel = doppelter Token-Verbrauch.
Bei knappem Budget `1` setzen oder teure Rollen via `model-overrides` auf `sonnet` herabstufen.

Siehe [howto/features/agent-delegation-map.md](howto/features/agent-delegation-map.md) für die vollständige
Delegations-Matrix und parallelisierbare Workflow-Schritte.

---

### `speech-mode` — Kommunikationsstil aller Agenten (optional)

```json
"speech-mode": "short"
```

Steuert den Kommunikationsstil aller Agenten. `sync.py` kopiert `speech/<mode>.md` nach
`.claude/rules/speech-mode.md` — Claude Code lädt diese Rule automatisch in jeden Agenten-Kontext.

| Wert | Verhalten |
|------|-----------|
| `"full"` | **Default** — Normales Verhalten, keine Rule wird generiert |
| `"short"` | Nur Fakten, keine Floskeln, keine Begrüßung/Zusammenfassung, Erklärungen nur auf Nachfrage |
| `"childish"` | Kindgerecht, spielerisch, Beispiele aus Tierwelt/Spielzeug, Emojis erlaubt |
| `"caveman"` | Höhlenmensch-Stil: kurz, direkt, abgehakt, keine Konjunktionen |
| `"asozial"` | New-Kids-Stil: fachlich korrekt, vulgär, hält den User für beschränkt |

**Technisch:**
- `"full"` → keine Rule-Datei (Verhalten unverändert); vorhandene `speech-mode.md` wird entfernt
- Alle anderen → `speech/<mode>.md` → `.claude/rules/speech-mode.md`
- Die Rule überschreibt alle anderen Stil-Anweisungen in den Agenten-Templates
- Gilt automatisch für **alle** Agenten und den Hauptchat — keine Template-Änderungen nötig

**Neue Modi hinzufügen:** Neue Datei `speech/<name>.md` anlegen → Enum in `agent-meta.schema.json` ergänzen.

---

### `dod-preset` — DoD-Qualitätsprofil (optional)

```json
"dod-preset": "rapid-prototyping"
```

Wählt ein vordefiniertes Qualitätsprofil. Einzelne Kriterien können via `dod` überschrieben werden.
Presets sind in `dod-presets.config.yaml` definiert (im agent-meta Root).

| Preset | req-traceability | tests-required | codebase-overview | security-audit |
|--------|:---------------:|:--------------:|:-----------------:|:--------------:|
| `full` (Default) | true | true | true | false |
| `standard` | false | true | false | false |
| `rapid-prototyping` | false | false | false | false |

**Precedence:** `dod` (Projekt-Override) > `dod-preset` > `full` (impliziter Default).

**Neue Presets hinzufügen:** Neuen Eintrag in `dod-presets.config.yaml` unter `presets` anlegen +
Enum in `agent-meta.schema.json` erweitern.

**Neue DoD-Spalten hinzufügen:**
1. Feld in `dod-presets.config.yaml` (in jedem Preset + `full`-Preset als Fallback) definieren
2. In `scripts/lib/dod.py` als `DOD_<NAME>` auto-injizieren
3. In Agent-Templates via `{{DOD_<NAME>}}` referenzieren
4. Schema in `agent-meta.schema.json` im `dod`-Block erweitern

---

### `dod` — Definition of Done Overrides (optional)

```json
"dod-preset": "standard",
"dod": {
  "security-audit": true
}
```

Überschreibt einzelne Kriterien des gewählten Presets. Fehlt `dod-preset` → Basis ist `full`.

| Feature | Default (`full`) | Steuert |
|---------|:----------------:|---------|
| `req-traceability` | `true` | REQ-IDs, REQUIREMENTS.md, REQ-ID in Commits, Traceability-Audit |
| `tests-required` | `true` | Tests als DoD-Kriterium, TDD-Workflow-Schritte |
| `codebase-overview` | `true` | CODEBASE_OVERVIEW.md als DoD-Kriterium |
| `security-audit` | `false` | Security-Audit vor Release |

`sync.py` injiziert die aufgelösten Werte als `{{DOD_REQ_TRACEABILITY}}`, `{{DOD_TESTS_REQUIRED}}`,
`{{DOD_CODEBASE_OVERVIEW}}`, `{{DOD_SECURITY_AUDIT}}`, `{{DOD_PRESET}}` (`"true"`/`"false"` bzw. Preset-Name).
Die aufgelösten Werte erscheinen auch im **CLAUDE.md managed block** des Zielprojekts.

**Auswirkung auf Agenten und Workflows:**

| Wenn deaktiviert | Orchestrator | Developer | Validator | Git |
|-----------------|-------------|-----------|-----------|-----|
| `req-traceability: false` | `requirements`-Schritte übersprungen | Keine REQ-ID-Pflicht | Kein Traceability-Audit | Commit ohne REQ-ID |
| `tests-required: false` | `tester`-Schritte übersprungen | Kein "Code ohne Tests"-Verbot | Test-Kriterium entfällt | — |
| `codebase-overview: false` | `documenter`-Schritte übersprungen | — | Doku-Kriterium entfällt | — |

**Beispiel: Rapid-Prototyping mit Tests:**
```json
"dod-preset": "rapid-prototyping",
"dod": {
  "tests-required": true
}
```
→ Kein REQ-System, kein CODEBASE_OVERVIEW, aber Tests bleiben Pflicht.

---

### `hooks` — Hook-Aktivierung pro Projekt (optional)

```json
"hooks": {
  "dod-push-check": { "enabled": true }
}
```

Steuert welche agent-meta-verwalteten Hooks in `.claude/settings.json` registriert werden.

**Two-Gate-Prinzip:** Ein Hook wird nur registriert wenn:
1. Das Skript in `hooks/1-generic/` (oder `2-platform/`, `0-external/`) existiert
2. `enabled: true` in `.meta-config/project.yaml` des Projekts gesetzt ist

Fehlt der `hooks`-Block → kein Hook wird registriert (sicheres Default).
Skripte werden unabhängig von `enabled` immer nach `.claude/hooks/` kopiert.

**Verfügbare Hooks:**

| Hook | Event | Beschreibung |
|------|-------|-------------|
| `dod-push-check` | `PreToolUse` | Blockiert `git push` wenn Tests nicht grün sind |

Projekt-eigene Hooks anlegen: `--create-hook <name>` (nie von sync.py überschrieben).

Siehe [howto/features/hooks.md](howto/features/hooks.md) für vollständige Dokumentation.

---

## Variablen und Platzhalter

Alle `{{PLATZHALTER}}` werden via `.meta-config/project.yaml` befüllt.
Auto-injiziert (nicht in config nötig): `AGENT_META_VERSION`, `AGENT_META_DATE`, `AGENT_TABLE`, `AGENT_HINTS`, `AI_PROVIDER`, `MAX_PARALLEL_AGENTS`, `DOD_REQ_TRACEABILITY`, `DOD_TESTS_REQUIRED`, `DOD_CODEBASE_OVERVIEW`, `DOD_SECURITY_AUDIT`, `DOD_PRESET`.

**Platform-Config-Platzhalter** (`{{platform.*}}`) werden separat via `platform-configs/<platform>.defaults.yaml` + `.claude/platform-config.yaml` befüllt.
Siehe [howto/features/platform-config.md](howto/features/platform-config.md) für Details.

### Generische Variablen (alle Projekte)

| Platzhalter | Agent | Zweck |
|-------------|-------|-------|
| `{{PROJECT_CONTEXT}}` | alle | Projektbeschreibung |
| `{{PROJECT_GOAL}}` | alle | Primäres Ziel des Projekts (für wen, was wird gelöst) |
| `{{PROJECT_LANGUAGES}}` | alle | Verwendete Programmiersprachen |
| `{{COMMUNICATION_LANGUAGE}}` | alle | Sprache für Nutzer-Kommunikation — Agent-Output (z.B. `Englisch`) |
| `{{USER_INPUT_LANGUAGE}}` | alle | Sprache der Nutzer-Eingaben — Agent-Input (z.B. `Deutsch`) |
| `{{DOCS_LANGUAGE}}` | alle | Sprache für externe Doku: README, CHANGELOG, Release Notes, GitHub Issues |
| `{{INTERNAL_DOCS_LANGUAGE}}` | alle | Sprache für interne Doku: CODEBASE_OVERVIEW, ARCHITECTURE, REQUIREMENTS, conclusions |
| `{{CODE_LANGUAGE}}` | alle | Sprache für code-nahe Artefakte: Kommentare, Commit-Messages, Test-Beschreibungen |
| `{{AGENT_META_REPO}}` | meta-feedback | GitHub-Repo für Issues (z.B. `owner/agent-meta`) |
| `{{GIT_PLATFORM}}` | git | Plattform: `GitHub`, `GitLab` oder `Gitea` |
| `{{GIT_REMOTE_URL}}` | git | Remote-URL des Repositories |
| `{{GIT_MAIN_BRANCH}}` | git | Haupt-Branch (z.B. `main` oder `master`) |
| `{{CODE_CONVENTIONS}}` | developer | Sprachspezifische Regeln |
| `{{ARCHITECTURE}}` | developer | Verzeichnisstruktur, Entry-Points |
| `{{DEV_COMMANDS}}` | developer, orchestrator | Build/Run-Kommandos |
| `{{EXTRA_DONTS}}` | developer | Zusätzliche Verbote (kurze Liste) |
| `{{CODE_QUALITY_RULES}}` | validator | Linting-Regeln, Quality-Gates |
| `{{REQ_CATEGORIES}}` | requirements | Anforderungs-Kategorien |
| `{{TEST_COMMANDS}}` | tester | Test-Runner-Kommandos |
| `{{TESTER_SNIPPETS_PATH}}` | tester | Pfad zur Snippet-Datei (relativ zu `snippets/`) |
| `{{DEVELOPER_SNIPPETS_PATH}}` | developer | Pfad zur Snippet-Datei (relativ zu `snippets/`) |
| `{{BUILD_COMMANDS}}` | release | Build-Schritte |

### Infrastruktur-Variablen — generisch (Docker, Ports)

| Platzhalter | Zweck | Format |
|-------------|-------|--------|
| `{{SYSTEM_DEPENDENCIES}}` | Kern-Abhängigkeiten mit konkreten Versionen | Markdown-Liste |
| `{{SYSTEM_URLS}}` | Relevante System-URLs (Web-UI, APIs, Signaling) | Markdown-Liste |
| `{{PRIMARY_PORT}}` | Haupt-Port der Anwendung | Einzelwert |
| `{{EXTRA_PORTS}}` | Weitere benötigte Ports neben `PRIMARY_PORT` | Markdown-Liste |
| `{{SERVICE_NAME}}` | Compose-Service-Name | Einzelwert |
| `{{CONTAINER_NAME}}` | Docker-Container-Name | Einzelwert |

### Plattform-Variablen — nur bei `"platforms": ["sharkord"]`

| Platzhalter | Zweck | Format |
|-------------|-------|--------|
| `{{PRIMARY_IMAGE_TAG}}` | Docker-Image-Tag des Sharkord-Kernsystems | Einzelwert |
| `{{PLUGIN_DIR_NAME}}` | Plugin-Verzeichnisname = `package.json` `name` | Einzelwert |

### Projektspezifische Variablen — individuelle Werte pro Projekt

| Platzhalter | Zweck | Format |
|-------------|-------|--------|
| `{{BUILD_OUTPUT}}` | Beschreibung der Build-Artefakte | Text |
| `{{ARTIFACT_ZIP_CMD}}` | Befehl zum Erstellen des ZIP-Artifacts | Shell-Befehl |
| `{{ARTIFACT_TAR_CMD}}` | Befehl zum Erstellen des TAR-Artifacts | Shell-Befehl |
| `{{GH_ASSETS}}` | Pfade der GitHub-Release-Assets | Leerzeichen-getrennt |
| `{{BUILD_SYSTEM_NOTES}}` | Hinweise zum Build-System | Text |
| `{{VERSION_DIST_BEHAVIOUR}}` | Wie landet die Version im Dist? | Text |

---

## Snippets

Sprachspezifische Code-Beispiele, die Agenten zur Laufzeit lesen — sprachunabhängige Templates
können so plattformspezifische Syntax einbinden, ohne sie im Agent-Template hart zu kodieren.

### Konzept

```
agent-meta/snippets/<rolle>/<sprache-runtime>.md   ← versionierte Quelldateien
    ↓  sync.py COPY
.claude/snippets/<rolle>/<sprache-runtime>.md       ← im Zielprojekt (generiert)
    ↓  Read-Tool zur Laufzeit
Agent nutzt sprachspezifische Syntax
```

### Frontmatter

Jede Snippet-Datei enthält YAML-Frontmatter:

```yaml
---
snippet: <rolle>-syntax          # Eindeutiger Bezeichner
version: "1.0.0"                 # Semver — erhöhen bei inhaltlichen Änderungen
language: "TypeScript"           # Programmiersprache
runtime: "Bun"                   # Runtime / Test-Framework
---
```

### Verfügbare Snippets

| Datei | Rolle | Sprache / Runtime | Version |
|-------|-------|-------------------|---------|
| `snippets/tester/bun-typescript.md` | tester | TypeScript / Bun | 1.0.0 |
| `snippets/tester/pytest-python.md` | tester | Python / pytest | 1.0.0 |
| `snippets/developer/bun-typescript.md` | developer | TypeScript / Bun | 1.0.0 |
| `snippets/developer/pytest-python.md` | developer | Python / pytest | 1.0.0 |

### Snippet hinzufügen

1. Neue Datei in `snippets/<rolle>/` anlegen (mit Frontmatter)
2. Variable `<ROLLE>_SNIPPETS_PATH` in `.meta-config/project.yaml` des Projekts setzen
3. `sync.py` kopiert die Datei automatisch nach `.claude/snippets/`
4. Agent-Template enthält Read-Instruktion: `Lies .claude/snippets/{{<ROLLE>_SNIPPETS_PATH}}`

### Versionierung

- Snippet-Version ist unabhängig von Agent- und Repo-Version
- `sync.py` loggt die Version beim COPY: `snippets/tester/bun-typescript.md@1.0.0`
- Bei inhaltlichen Änderungen: Patch oder Minor erhöhen

---

## Rules (`.claude/rules/` Layer)

Projekt-globale Regeln die **automatisch** in jeden Agenten-Kontext geladen werden —
kein Read-Tool nötig. Ideal für Security-Policies, Coding-Konventionen, Plattform-Constraints.

### Vier-Schichten-Modell

```
rules/
  0-external/     ← aus externen Skill-Repos
  1-generic/      ← universell, für alle Projekte
  2-platform/     ← plattformspezifisch (überschreibt 1-generic bei gleichem Dateinamen)
  ← 3-project: .claude/rules/ im Zielprojekt — nie von sync.py berührt
```

**Naming für 2-platform:** `<platform>-<thema>.md` → Output: `<thema>.md`

### Sync-Verhalten

`sync.py` kopiert Rules automatisch bei jedem normalen Sync. Stale-Tracking via
`.claude/rules/.agent-meta-managed` — nur dort gelistete Dateien werden entfernt,
wenn sie aus den agent-meta-Quellen verschwinden.

```bash
# Projekt-eigene Rule anlegen (nie überschrieben)
py .agent-meta/scripts/sync.py --create-rule security-policy
```

### Abgrenzung zu Extensions

| | Extensions (`.claude/3-project/*-ext.md`) | Rules (`.claude/rules/`) |
|---|---|---|
| Scope | Ein Agenten-Typ | **Alle Agenten** |
| Laden | Explizit per Read-Hook | **Automatisch** |
| Quelle | Projekt schreibt selbst | Alle 4 Schichten |

Siehe [howto/features/rules.md](howto/features/rules.md) für vollständige Dokumentation.

---

## Hooks (`.claude/hooks/` Layer)

Shell-Skripte die Claude Code automatisch vor/nach Tool-Aufrufen ausführt —
ideal für DoD-Enforcement, Pre-Push-Checks, Audit-Logging.

### Vier-Schichten-Modell

```
hooks/
  0-external/     ← Hooks aus externen Skill-Repos
  1-generic/      ← universell, für alle Projekte
  2-platform/     ← plattformspezifisch (überschreibt 1-generic bei gleichem Dateinamen)
  ← 3-project: .claude/hooks/ im Zielprojekt — Projekt-eigene Hooks (nie überschrieben)
```

**Naming für 2-platform:** `<platform>-<thema>.sh` → Output: `<thema>.sh`

### Sync-Verhalten

- Skripte werden **immer kopiert** (wie Rules) — unabhängig von `enabled`
- **Registrierung in `.claude/settings.json`** nur wenn Projekt den Hook aktiviert:

```json
"hooks": {
  "dod-push-check": { "enabled": true }
}
```

- Stale-Tracking via `.claude/hooks/.agent-meta-managed`

```bash
# Projekt-eigenen Hook anlegen (nie überschrieben)
py .agent-meta/scripts/sync.py --create-hook mein-hook
```

### Abgrenzung zu Rules

| | Rules (`.claude/rules/`) | Hooks (`.claude/hooks/`) |
|---|---|---|
| Format | Markdown | Shell-Skript |
| Laden | Automatisch in Agent-Kontext | Claude Code führt aus (settings.json) |
| Scope | Kontext für Agenten | Automatisierung / Enforcement |
| Aktivierung | Immer aktiv | Opt-in via `.meta-config/project.yaml` |

Siehe [howto/features/hooks.md](howto/features/hooks.md) für vollständige Dokumentation.

---

## External Skills (0-external Layer)

Domänenspezifische Agenten aus Drittrepos — hochspezialisiertes Wissen das nicht in generischen
Agenten gehört (z.B. 3D-Druck-Systeme, CAD-Workflows, spezifische Plattform-Expertise).

### Konzept

```
external/<repo>/path/to/SKILL.md    ← Quelldatei im Submodule (gepinnter Commit)
    ↓  sync.py substituiert SKILL_CONTENT in _skill-wrapper.md
.claude/agents/<role>.md            ← generierter Wrapper-Agent im Zielprojekt
.claude/skills/<skill-name>/        ← kopierte Skill-Dateien (für lazy Read-Zugriff)
```

### Konfiguration: `config/skills-registry.yaml`

Liegt **zentral in agent-meta** (Modell A) — ein Eintrag pro Skill:

```json
{
  "repos": {
    "my-skills-repo": {
      "repo": "https://github.com/owner/my-skills-repo",
      "local_path": "external/my-skills-repo",
      "pinned_commit": "abc1234"
    }
  },
  "skills": {
    "my-skill": {
      "approved": true,
      "repo": "my-skills-repo",
      "source": "path/within/repo",
      "entry": "SKILL.md",
      "role": "my-specialist",
      "name": "My Specialist",
      "description": "Kurzbeschreibung der Spezialisierung.",
      "additional_files": ["reference.md"]
    }
  }
}
```

- **`repos`** — Repo-Definitionen (1:n zu skills): URL, `local_path`, `pinned_commit`
- **`pinned_commit`** — Vollständiger Commit-Hash; sync.py warnt bei Abweichung des Submodul-Stands
- **`approved: true/false`** — Meta-Maintainer Quality Gate: Skill ist geprüft und für Projekte nutzbar
- **`repo`** — Referenz auf einen Eintrag in `repos` (statt `submodule`)
- **`entry`** — Abstraktion über die Einstiegsdatei (egal wie sie im Fremdrepo heißt)
- **`additional_files`** — weitere Dokumente, die der Agent lazy per Read-Tool laden kann

### Projektlokale Aktivierung: `.meta-config/project.yaml`

Projekte aktivieren freigegebene Skills über einen eigenen Block in `.meta-config/project.yaml`:

```json
{
  "external-skills": {
    "my-skill": { "enabled": true },
    "large-skill": { "enabled": true, "gitignore": true }
  }
}
```

**Two-Gate-Regel:** Ein Skill wird nur generiert wenn **beide** Bedingungen erfüllt sind:
1. `approved: true` in `config/skills-registry.yaml` (Meta-Maintainer-Freigabe)
2. `enabled: true` in `.meta-config/project.yaml` des Projekts (Projekt-Opt-in)

Fehlt der `external-skills`-Block komplett → kein externer Skill wird generiert (sicheres Default).
Referenziert ein Projekt einen unbekannten oder nicht-approved Skill → `[WARN]` im sync.log.

**`gitignore: true`** (optional): `sync.py` fügt `.claude/skills/<skill-name>/` automatisch zum
`.gitignore` managed block hinzu. Beim Deaktivieren wird der Eintrag wieder entfernt. Sinnvoll
wenn der Skill große oder generierte Dateien nach `.claude/skills/` kopiert.

### Skill hinzufügen

```bash
# Einmalig: Submodule registrieren + Config-Eintrag anlegen
python .agent-meta/scripts/sync.py \
  --add-skill https://github.com/owner/skill-repo \
  --skill-name my-skill \
  --source path/within/repo \
  --role my-specialist

# Danach normaler Sync generiert den Wrapper-Agenten
python .agent-meta/scripts/sync.py
```

### Wrapper-Agent

`_skill-wrapper.md` ist das **einzige Template** für alle External Skills:
- Header + Scope-Hinweis werden von agent-meta beigesteuert
- `{{SKILL_CONTENT}}` wird mit dem vollständigen Inhalt der `entry`-Datei substituiert
  (Frontmatter des Skill-Dokuments wird dabei entfernt)
- `additional_files` bleiben als `.claude/skills/<skill>/` für lazy Read-Zugriff

### Versionierung

`sync.py` loggt beim Generieren den Submodule-Commit-Hash:
`0-external/my-skill@a3f9c12`

Um einen Skill auf einen neuen Stand zu bringen:
```bash
cd external/my-skills-repo && git pull
cd ../.. && git add external/my-skills-repo
git commit -m "chore: update my-skills-repo submodule"
python .agent-meta/scripts/sync.py --config .meta-config/project.yaml
```

---

## Standard-Entwicklungsworkflows

Definiert in `1-generic/orchestrator.md`, gelten projektübergreifend.
Schritte mit `∥` können parallel laufen (gesteuert via `max-parallel-agents`).
Siehe [howto/features/agent-delegation-map.md](howto/features/agent-delegation-map.md) für die vollständige Delegations-Matrix.

### Branch-Guard (Schritt 0 für Workflows A, B, E, L)
```
0.   git           → Branch prüfen. Auf main/master? → Feature-Branch anlegen.
                      Bereits auf Feature-Branch? → Weiter.
```

### Workflow A: Neues Feature
```
0.   git           → Branch-Guard (→ feat/<thema>)
1.   requirements  → Anforderung formulieren, REQ-ID vergeben
2.   tester        → Tests ZUERST schreiben (TDD Red Phase)
3.   developer     → Implementierung (TDD Green Phase)
4.   tester        → Tests ausführen, Regressions prüfen
5∥6. validator     → Code gegen REQ validieren, DoD-Check
 ∥   documenter    → CODEBASE_OVERVIEW + Erkenntnisse updaten
7.   git           → Commit + Push
```

### Workflow B: Bugfix
```
0.   git           → Branch-Guard (→ fix/<thema>)
1.   requirements  → Bestehende REQ-ID identifizieren
2.   tester        → Reproduzierenden Test schreiben
3.   developer     → Fix implementieren
4.   tester        → Tests ausführen
5∥6. validator     → Quick-Check
 ∥   documenter    → Ggf. Doku updaten
7.   git           → Commit + Push
```

### Workflow C: Validierung / Audit
```
1. validator     → Traceability-Audit (REQ → Code → Test)
2. validator     → Code-Qualitäts-Scan
3. validator     → Vollständiger Bericht
```

### Workflow D: Erkenntnisse speichern
```
1. documenter    → Tages-Erkenntnisse in docs/conclusions/ speichern
```

### Workflow E: Refactoring
```
0.   git           → Branch-Guard (→ refactor/<thema>)
1.   requirements  → Betroffene REQ-IDs identifizieren
2.   developer     → Refactoring durchführen
3.   tester        → Alle betroffenen Tests ausführen
4∥5. validator     → Sicherstellen, dass kein Verhalten sich ändert
 ∥   documenter    → Signaturen/Flows in CODEBASE_OVERVIEW updaten
6.   git           → Commit + Push
```

### Workflow F: Testsystem starten
```
1. docker        → Dev-Stack bauen + starten, Startup-Display ausgeben
```

### Workflow G: Neue Docker-Konfiguration
```
1. docker        → Anforderungen klären, Dockerfile + Compose erstellen
2. tester        → Test-Stack validieren
```

### Workflow H: Neue Idee / Vision erkunden
```
1. ideation      → Idee explorieren, Fragen stellen, Scope schärfen
2. ideation      → Übergabe an requirements (wenn Idee reif)
3. requirements  → Anforderungen formal aufnehmen, REQ-IDs vergeben
```

---

## Standard-Qualitätskriterien

### Definition of Done (DoD)

Konfigurativ steuerbar über `dod` in `.meta-config/project.yaml`.
Fehlende Einträge verwenden die Defaults.

**Immer aktiv (Pflicht):**
- [ ] **Code** implementiert die Aufgabe vollständig
- [ ] **Code-Konventionen** eingehalten (s. CLAUDE.md des Projekts)
- [ ] **Commit-Message** im korrekten Conventional-Commits-Format

**Wenn `req-traceability: true` (Default):**
- [ ] **REQ-ID** existiert in `docs/REQUIREMENTS.md`
- [ ] **REQUIREMENTS.md** konsistent

**Wenn `tests-required: true` (Default):**
- [ ] **Test** vorhanden
- [ ] **Tests grün**

**Wenn `codebase-overview: true` (Default):**
- [ ] **CODEBASE_OVERVIEW.md** aktualisiert

**Wenn `security-audit: true` (Default: false):**
- [ ] **Security-Audit** vor Release durchgeführt

### Commit-Format (Conventional Commits)

Immer aktiv — unabhängig von DoD-Konfiguration.

```
<type>(REQ-xxx): <beschreibung>    ← mit req-traceability
<type>: <beschreibung>             ← ohne req-traceability
```

| Type | Bedeutung | REQ-ID |
|------|-----------|--------|
| `feat` | Neues Feature | Wenn `req-traceability` aktiv |
| `fix` | Bugfix | Wenn `req-traceability` aktiv |
| `test` | Tests hinzufügen/ändern | Wenn `req-traceability` aktiv |
| `refactor` | Refactoring ohne Verhaltensänderung | Wenn `req-traceability` aktiv |
| `chore` | Wartung: Dependencies, Config, Versions-Bumps | **Nie** |
| `docs` | Dokumentation | **Nie** |
| `ci` | CI/CD-Änderungen | **Nie** |

### Sprachregeln
- `README.md` → **Englisch**
- Alle anderen Dokumente → **Deutsch**
- Code-Kommentare, Commit-Messages → **Englisch**
- Kommunikation mit dem Nutzer → **Deutsch**

---

## Unterstützte Projekte

| Repository | Plattform | CLAUDE.md |
|-----------|-----------|-----------|
| `sk_plugin` (sharkord-vid-with-friends) | Sharkord | `sk_plugin/CLAUDE.md` |
| `sk_hero_introduce` (sharkord-hero-introducer) | Sharkord | `sk_hero_introduce/sharkord-hero-introducer/CLAUDE.md` |

---

## Abhängigkeits-Karte — PFLICHTLEKTÜRE bei Änderungen

```
1-generic/docker.md
    └── 2-platform/sharkord-docker.md
            ├── sk_plugin/.claude/agents/docker.md
            └── sk_hero_introduce/.../.claude/agents/docker.md

1-generic/release.md
    └── 2-platform/sharkord-release.md
            ├── sk_plugin/.claude/agents/release.md
            └── sk_hero_introduce/.../.claude/agents/release.md

1-generic/orchestrator.md  → sk_plugin/.claude/agents/orchestrator.md
                           → sk_hero_introduce/.../.claude/agents/orchestrator.md

1-generic/developer.md     → sk_plugin/.claude/agents/developer.md
                           → sk_hero_introduce/.../.claude/agents/developer.md

(analog für tester, validator, requirements, ideation, documenter, meta-feedback, git, agent-meta-manager, feature, agent-meta-scout, security-auditor, openscad-developer)

1-generic/agent-meta-scout.md  → .claude/agents/agent-meta-scout.md (generiert)
    └── liest zur Laufzeit:
        .agent-meta/external/awesome-claude-code/.claude/commands/evaluate-repository.md

0-external/_skill-wrapper.md
    └── config/skills-registry.yaml (enabled skills)
            └── .claude/agents/<role>.md (generiert)
            └── .claude/skills/<skill-name>/ (kopiert)

CLAUDE.md ← diese Datei
    └── referenziert: agents/**, howto/**, alle unterstützten Projekte

ARCHITECTURE.md ← grafische Übersicht (Mermaid)
    └── wird bei jedem Major Release aktualisiert
```

### Regeln für Änderungen

| Wenn du änderst … | dann prüfe auch … |
|---|---|
| `1-generic/docker.md` | `2-platform/sharkord-docker.md` |
| `1-generic/release.md` | `2-platform/sharkord-release.md` |
| `1-generic/orchestrator.md` | Workflows-Abschnitt in dieser `CLAUDE.md` |
| beliebigen `1-generic/` Agenten | Version in Template erhöhen + Projekte neu syncen |
| `2-platform/sharkord-*.md` | Version in Template erhöhen + `based-on` aktuell halten + Projekte neu syncen |
| `agents/0-external/_skill-wrapper.md` | Alle aktivierten Skills neu syncen |
| `config/skills-registry.yaml` | Projekte neu syncen |
| `config/role-defaults.yaml` (neue Rolle) | Rollen-Übersicht hier + `howto/setup/instantiate-project.md` |
| `hint:` Feld in einem Agenten-Template | Projekte neu syncen (AGENT_HINTS wird neu generiert) |
| `howto/CLAUDE.project-template.md` | `howto/setup/instantiate-project.md` (Checkliste) |

### Änderungs-Kategorien

**Einfaches Projektspezifikum (Kommando, Text, Liste):**
→ Variable in `.meta-config/project.yaml` → bestehender `{{PLATZHALTER}}`.

**Strukturiertes Projektwissen (nur dieses Projekt):**
→ `.claude/3-project/<rolle>-ext.md` im Zielprojekt schreiben.

**Plattformwissen verbessern (gilt für alle Projekte auf Plattform X):**
→ `2-platform/<plattform>-<rolle>.md` ändern → Projekte neu syncen.
→ Composition-Modus: `extends: "1-generic/<rolle>.md"` + `patches:` im Frontmatter nutzen statt Vollkopie.
→ Siehe [howto/features/agent-composition.md](howto/features/agent-composition.md) für Details.

**Neuen External Skill einbinden:**
→ `--add-skill` ausführen → `config/skills-registry.yaml` prüfen → Projekte neu syncen.

**Neue Agenten-Rolle hinzufügen:**
→ `1-generic/<rolle>.md` + Eintrag in `config/role-defaults.yaml` + Tabellen in dieser `CLAUDE.md` + `howto/setup/instantiate-project.md` + `howto/CLAUDE.project-template.md`.

---

## Agent-Versionierung

Jeder Agent-Template-Datei trägt eine eigene `version:` im Frontmatter.
Plattform-Agenten dokumentieren zusätzlich ihre Generic-Basis via `based-on:`.
Generierte Dateien erhalten automatisch `generated-from:` (gesetzt von `sync.py`).

### Frontmatter-Übersicht

| Feld | 1-generic | 2-platform | generiert in `.claude/agents/` |
|------|-----------|------------|-------------------------------|
| `version` | ✅ manuell pflegen | ✅ manuell pflegen | erhalten aus Template |
| `hint` | ✅ manuell pflegen | ✅ manuell pflegen | erhalten aus Template — erscheint in `AGENT_HINTS` in `CLAUDE.md` |
| `based-on` | — | ✅ `<generic>@<version>` | erhalten aus Template |
| `generated-from` | — | — | ✅ automatisch von sync.py |

### Wann Version erhöhen?

| Änderungstyp | Version |
|---|---|
| Umbenannte Variable, geändertes Verhalten, neue Pflichtsektion | **Major** (`X.0.0`) |
| Neue optionale Sektion, erweiterter Scope | **Minor** (`x.Y.0`) |
| Textverbesserung, Klarstellung | **Patch** (`x.y.Z`) |

Agenten-Versionen sind **unabhängig** von der Repository-Version in `VERSION`.
Nur geänderte Agenten bekommen eine neue Versionsnummer.

Wenn eine `1-generic`-Datei versioniert wird und ein `2-platform`-Agent darauf basiert:
→ `based-on` im Plattform-Agenten auf neue Generic-Version aktualisieren.

Siehe [howto/features/agent-versioning.md](howto/features/agent-versioning.md) für Details.

---

## Neue Projekte hinzufügen

Siehe [howto/setup/instantiate-project.md](howto/setup/instantiate-project.md).

## Upgrade auf neue Version

Siehe [howto/setup/upgrade-guide.md](howto/setup/upgrade-guide.md).

---

## Release-Prozess (agent-meta selbst)

Releases folgen [Semantic Versioning](https://semver.org/):
- **Patch** (`x.y.Z`) — Bugfixes, Doku, kleine Verbesserungen ohne Breaking Changes
- **Minor** (`x.Y.0`) — Neue Features, neue Agenten-Rollen, neue Platzhalter (rückwärtskompatibel)
- **Major** (`X.0.0`) — Breaking Changes (Umbenennungen, entfernte Variablen, geändertes Verhalten)

### Schritt-für-Schritt

```
1. Agenten-Versionen prüfen und erhöhen:
   - Welche Agent-Dateien wurden inhaltlich geändert?
   - Für jede geänderte Datei: version: im Frontmatter erhöhen (Patch/Minor/Major)
   - Bei 2-platform Agenten: based-on prüfen — zeigt es noch auf die richtige
     Generic-Version? Ggf. aktualisieren.
   - Bei Unsicherheit: Nutzer fragen welche Agenten-Version gesetzt werden soll

2. Änderungen committen (alle Agenten, Scripts, Doku)

3. CHANGELOG.md aktualisieren:
   - Neue Version [x.y.z] — <Datum> oben einfügen
   - Breaking Changes, Added, Changed, Removed dokumentieren
   - Geänderte Agenten-Versionen im "Changed"-Abschnitt nennen

4. VERSION aktualisieren:
   - Inhalt auf neue Versionsnummer setzen (z.B. 0.10.2)

5. README.md aktualisieren:
   - "Current version:" Badge/Zeile auf neue Version setzen
   - Quick-Start-Beispiel (`git checkout v<x.y.z>`) auf neue Version setzen

6. Bei MAJOR Release: ARCHITECTURE.md aktualisieren:
   - Version in der Überschrift anpassen
   - Neue Agenten-Rollen, Schichten oder Submodule in die Diagramme einpflegen
   - Bei Minor/Patch nur wenn sich Architektur strukturell ändert

7. Commit: git add VERSION CHANGELOG.md README.md [ARCHITECTURE.md]
           git commit -m "chore: bump version to x.y.z"

8. Tag setzen und pushen:
   git tag vx.y.z
   git push origin main
   git push origin vx.y.z
```

### Wichtig

- **Agenten-Versionen zuerst** — vor dem Release-Commit prüfen, ob alle geänderten
  Agent-Dateien eine aktualisierte `version:` im Frontmatter haben
- Bei Unsicherheit über Agenten-Version oder Release-Tag: **Nutzer fragen**
- README.md muss **vor dem Tag-Commit** die neue Version zeigen
- CHANGELOG.md muss vollständig sein **bevor** der Tag gesetzt wird
- Der Tag zeigt immer auf den Version-Bump-Commit — nie auf einen vorherigen Commit
