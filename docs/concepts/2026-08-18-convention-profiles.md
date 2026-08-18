# Konzept: Konfigurierbare Namens-/Versionierungs-Konventionen ("Convention Profiles")

> Status: Draft für Review-Stufe. Kein REQ-ID vergeben — Ideation-Phase.

## 1. Problem / Motivation

- **Issue #518:** Release-Versionierung und -Naming ist hartkodiert in `agents/1-generic/release.md` (SemVer-Tabelle, Tag-Format `vX.Y.Z`, CHANGELOG-Format mit `REQ-xxx:`-Präfix, 5-Schritte-Workflow). Projekte, die z.B. `YYYY.MM.PATCH`-Versionierung, ein anderes Tag-Format oder ein anderes Changelog-Schema wollen, müssten das Template selbst patchen.
- **Issue #452:** Der Release-**Prozess** (Build-Artefakt, GitHub-Release, npm/PyPI-Publish, ...) ist ebenfalls hartkodiert und variiert real zwischen Projekttypen (Library vs. CLI vs. Web-App).
- **Scope-Erweiterung (Nutzer-Vorgabe):** Beide Issues sind Symptome eines generischeren Problems — agent-meta hat aktuell **kein Fundament für konfigurierbare Namens-/Nomenklatur-Konventionen**, weder rollen-gebunden (Release-Naming) noch projektweit-aber-nicht-rollen-spezifisch (Commit-/Branch-Naming via `commit-conventions.md`/`branch-guard.md`). Dieses Konzept soll dieses Fundament legen — mit Release-Naming als erstem konkretem Anwendungsfall und Issue-Naming (injiziert in den `git`-Agenten) als zweitem, absichtlich andersartigen Anwendungsfall, der beweist, dass das Fundament wirklich wiederverwendbar ist und nicht nur für Release maßgeschneidert wurde.

## 2. Ist-Zustand (verifiziert)

- **Rollen-Allowlist:** `project.yaml` hat ein optionales `roles:`-Array. Prüfmuster in `scripts/lib/delegation_table.py:16-17`:
  ```python
  roles_list = config.get("roles")
  active_roles = set(roles_list) if roles_list is not None else None
  ```
  `None` = alle Rollen aktiv (kein Allowlist-Filter), sonst harte Schnittmenge. Dieses Muster ist der etablierte Weg, um Rollen-Verfügbarkeit zu prüfen, und wird von diesem Konzept wiederverwendet.
- **Rules sind projektweit, nicht rollen-gebunden:** `scripts/lib/rules.py` (`resolve_rules`, `sync_rules`) kennt `alwaysApply` (nur Continue-Frontmatter), `gemini: skip`, `embed: false`, `channel: skill`. Kein Rollen-Filter. Jede Regel aus `rules/{0-external,1-generic,2-platform}/*.md` landet in **`.claude/rules/<name>.md` — einer einzigen, geteilten Datei je Regel, die von Claude Code für JEDEN Agenten-Kontext (main-chat und jeden Subagenten) vollständig geladen wird**, unabhängig von `alwaysApply`. Beleg dafür direkt im Code-Kommentar (`rules.py:26-32`): `alwaysApply: false` hat auf Claude Code nachweislich **keinen** Effekt — das ist eine Cursor/Continue-Konvention. Der einzige echte Lazy-Load-Kanal auf Claude Code ist `channel: skill` (Rule wandert nach `.claude/skills/<name>/SKILL.md`, nur `name`+`description` im System-Prompt, Body erst on-demand per `Read`) — aber auch das ist **nicht rollenspezifisch**, sondern nur "on-demand für wen auch immer den Skill liest".
  → **Konsequenz für dieses Konzept:** Die Rules-Pipeline ist architektonisch die falsche Injektionsstelle für rollen-gebundene Inhalte auf Claude Code, weil ihre Ausgabe (`.claude/rules/*.md`) plattformseitig immer an alle Kontexte geht. Echte Rollen-Scopierung existiert heute nur über den Inhalt der **eigenen** generierten Agenten-Datei einer Rolle (`.claude/agents/<rolle>.md`), die nur geladen wird, wenn genau diese Rolle aufgerufen wird.
- **Namenskollision:** `target_roles` existiert bereits in `config/role-defaults.yaml` unter `handoff:` — dort bedeutet es "A2A-Handoff-Zielrolle". Für "Rolle, an deren Render-Gate dieser Konventions-Block gebunden ist" muss ein anderer Name gewählt werden.
- **Block-Injektions-Muster (Vorbild):** `BROWSER_VERIFICATION_BLOCK` / `LANGUAGE_BEST_PRACTICES_BLOCK` (`scripts/lib/config.py:886-894`, geladen aus `snippets/developer/*.md` in `build_variables()`) — ganze Markdown-Abschnitte werden einmal berechnet und als gewöhnliche `{{VARIABLE}}` in genau die Templates substituiert, die sie referenzieren. Kein Rollen-Filter nötig, weil jedes Template ohnehin nur für seine eigene Rolle generiert wird.
- **Konditionierungs-Muster:** `{{#if VAR}}...{{/if}}` (`strip_inactive_conditional_blocks`, `scripts/lib/config.py:899`), gespeist aus zentral in `build_variables()` berechneten `*_ENABLED`-Variablen. Aktuell nur aus Top-Level-Feature-Flags gespeist (z.B. `DOD_*`, `SE_ENABLED`, `PIPELINE_*_ENABLED`), nicht aus `roles:`-Mitgliedschaft — aber technisch trivial erweiterbar.
- **Bestehende Preset-Systeme:** `rules-preset` (`config/rules-presets.yaml`), `dod-preset` (`config/dod-presets.yaml`), `tier-preset` (`config/tier-presets.yaml`) — alle drei folgen demselben Muster: `<preset-name>` in `project.yaml` wählt einen benannten Preset, ein optionaler Override-Block (`rules:`, `dod:`) gewinnt additiv darüber. `default` ist bei allen drei kein leeres Schema, sondern ein voll ausgefüllter, sinnvoller Ausgangszustand.
- **`agents/1-generic/release.md`:** hartkodierte SemVer-Tabelle, Tag-Format `vX.Y.Z`, CHANGELOG-Format mit `### Added/Fixed/Changed/Removed` und `REQ-xxx:`-Präfix (unabhängig davon, ob `dod.req-traceability` für das Projekt überhaupt aktiv ist — im agent-meta-Projekt selbst z.B. `false`), 5-Schritte-Workflow. Keine Konditionierung nach Projekttyp.
- **`agents/1-generic/git.md`:** hartkodierte Branch-Konvention, Commit-Format, referenziert `commit-conventions.md` (projektweite Rule, s.o.). Kein Issue-Naming-Schema.
- **`.claude/skills/issue-lifecycle/SKILL.md`:** nur Prozess (Referenzieren, Closing-Keywords, Kommentar nach Fertigstellung) — keine Titel-/Label-Namenskonvention.

## 3. Prior Art (extern, knapp)

**Versionierung/Changelog:**

| Tool | Muster | Bewertung |
|---|---|---|
| semantic-release | Preset **oder** Config (additive Overrides + Preset sind XOR) | Negativbeispiel — Preset-Override-Footgun, den wir vermeiden wollen |
| release-please | Trennt Schema-Config von laufendem Release-Zustand | Gutes Vorbild für die Trennung Config/State |
| git-cliff | Sehr granular (Regex-Parser, Templates) | Kein Zero-Config-Fallback außerhalb Conventional Commits |
| Changesets | Manueller Zwischenschritt pro Change | Anderes Paradigma, nicht übertragbar (kein Sync-Zeit-Generator) |
| cocogitto | Versionierung + Changelog + Validierung + Hooks in einer Config | Am nächsten am heutigen `release.md`-Workflow |

**Gemeinsames Muster:** Preset-Name + additiver Override, nie ein leeres Schema, opinionated Zero-Config-Default (Conventional Commits + SemVer). Deckt sich exakt mit dem bereits in agent-meta etablierten `rules-preset`/`dod-preset`-Muster — kein neues Paradigma nötig, nur eine neue Preset-Achse.

**Issue-Naming:** Kein etablierter Standard analog zu Conventional Commits. Verbreitet sind Titel-Präfixe (`[BUG]:`) und Namespace-Labels (`type: bug`). Konsequenz: für den Default keinen fremden Standard importieren, sondern das im Projekt bereits etablierte Commit-Type-Vokabular (`commit-conventions.md`: `feat`/`fix`/`docs`/`chore`/...) wiederverwenden — ein Projekt, das seine Commit-Types kennt, kennt damit implizit auch sein Issue-Type-Vokabular.

## 4. Architektur-Entscheidung

### A) Wo lebt das Konventions-Profil?

**Entscheidung:** Neue `config/conventions-presets.yaml` (Preset-Definitionen) + zwei neue optionale Top-Level-Keys in `project.yaml`: `conventions-preset: <name>` (Selektor, Default `"default"` wenn Key fehlt) und `conventions: {...}` (additiver Projekt-Override, exakt wie `rules:` heute).

**Begründung:**
- Folgt 1:1 dem bereits dreifach bewährten Preset+Override-Muster (`rules-preset`/`rules:`, `dod-preset`/`dod:`, `tier-preset`). Kein neues Paradigma, keine neue mentale Belastung für Nutzer, die die anderen Presets schon kennen.
- Deckt sich mit dem externen Prior-Art-Konsens (Preset + additiver Override, nie XOR wie bei semantic-release).
- **Option 3 (Rules-Mechanismus um Rollen-Scope erweitern) wird verworfen als Storage-Ort für die Konventions-*Daten*:** Konventionen sind strukturierte Daten (Versions-Schema, Tag-Format, Changelog-Sections, Issue-Types), die von einer Substitutions-Funktion in ein Template gerendert werden — keine frei formulierte Rule-Prosa, die an `.claude/rules/` verteilt wird. Der Rules-Mechanismus bleibt für sein eigentliches Einsatzgebiet (projektweite, nicht-rollen-gebundene Prosa-Regeln wie `commit-conventions.md`, `branch-guard.md`) unverändert.
- **Zur "Preset-Wucherung"-Sorge:** Eine vierte Preset-Achse ist kein Zufallswachstum, sondern schließt eine echte Lücke — die drei bestehenden Achsen (Rules-Sichtbarkeit, DoD-Strenge, Workflow-Tiefe) haben keine Überlappung mit "wie heißen/versionieren wir Dinge". Mitigation: Dokumentation bekommt eine kurze "Preset-Systeme-Übersicht"-Tabelle (alle vier Achsen an einer Stelle), damit Nutzer nicht vier isolierte Konzepte lernen müssen.
- Namenskollision vermieden: das neue Feld heißt **`applies_to_roles`**, nicht `target_roles` (das bereits unter `handoff:` in `role-defaults.yaml` mit anderer Bedeutung existiert).
- **Klarstellung Semantik `applies_to_roles`:** Das Feld ist NUR ein Render-Gate gegen `active_roles` — es beantwortet die Frage „wird dieser Block überhaupt berechnet, falls die referenzierte(n) Rolle(n) nicht aktiv sind?", nicht „wohin wird der Block injiziert?". Welche Rolle den Block tatsächlich erhält, entscheidet ausschließlich, welches Rollen-Template den Platzhalter referenziert (z.B. `{{RELEASE_VERSIONING_BLOCK}}` in genau `release.md`) — nicht `applies_to_roles`. Ein Preset-Autor könnte `applies_to_roles: [git]` deklarieren, den Platzhalter aber versehentlich in `release.md` referenzieren; nichts an diesem Feld verhindert das (siehe Risiken, Abschnitt 8).

### B) Wie kommt der Default in die Templates?

**Entscheidung:** Generalisierung des bestehenden Block-Platzhalter-Musters (`BROWSER_VERIFICATION_BLOCK`), **nicht** eine Erweiterung von `sync_rules()`.

**Begründung (siehe Ist-Zustand-Analyse oben):** Echte Rollen-Scopierung ist auf Claude Code nur über den Inhalt der eigenen Agenten-Datei einer Rolle möglich, nicht über die geteilte `.claude/rules/`-Pipeline — die lädt plattformseitig immer alles in jeden Kontext, unabhängig von jedem Frontmatter-Flag. Eine Erweiterung von `sync_rules()` um einen Rollen-Filter würde also entweder (a) wirkungslos bleiben (Rule landet trotzdem in der geteilten Datei, die jeder Agent lädt) oder (b) eine viel größere Strukturänderung erfordern (Rules müssten künftig in die einzelnen `.claude/agents/<rolle>.md`-Dateien eingebettet werden statt in `.claude/rules/` — das bricht das gesamte heutige Rules-Modell). Das ist eine potenziell sinnvolle spätere Erweiterung, aber kein Ziel dieses Konzepts (siehe Risiken, Abschnitt 8).

Stattdessen: neues, kleines Modul `scripts/lib/conventions.py`:

```python
def load_conventions_presets(agent_meta_root: Path) -> dict: ...
def resolve_conventions(config: dict, agent_meta_root: Path) -> dict:
    """Preset + project-override merge, exakt nach resolve_rules()-Muster."""
def render_convention_block(
    domain: str, resolved: dict, active_roles: set[str] | None, log: SyncLog
) -> dict[str, str]:
    """Generischer Teil: Rollen-Gating nach Muster C (log.skip statt Crash/toter
    Content, applies_to_roles ist hier NUR das Render-Gate), dann Dispatch an
    eine kleine, domain-spezifische Rendering-Funktion. Welches Template den
    resultierenden Block tatsächlich einbindet, entscheidet ausschließlich die
    Platzhalter-Referenz im Zieltemplate — nicht dieses Feld (siehe Abschnitt C)."""
    ...

def _render_release_versioning(spec: dict) -> str:
    """Domain-spezifisch: rendert versioning-Felder in die heutige
    SemVer-Tabellenform (Großschrift MAJOR/MINOR/PATCH, Backtick-Suffixe, ...)."""

def _render_git_issue_naming(spec: dict) -> str:
    """Domain-spezifisch: rendert issues-Felder in die heutige Markdown-Form."""
```

`build_variables()` ruft `render_convention_block()` einmal je Domain auf und ergänzt neue Variablen — `RELEASE_VERSIONING_BLOCK`, `RELEASE_CHANGELOG_BLOCK`, `GIT_ISSUE_NAMING_BLOCK` — nach exakt demselben Substitutions-Muster wie `BROWSER_VERIFICATION_BLOCK` heute. `release.md` und `git.md` referenzieren diese Platzhalter an der Stelle, wo heute die hartkodierte Tabelle/das hartkodierte Format steht.

Wiederverwendbar ist nur ein Teil des Mechanismus, nicht die Formatierung selbst: (a) ein generisches, domain-agnostisches Fundament — Preset-Resolution, Rollen-Gating nach Muster C, Variable-Substitutions-Mechanik — plus (b) pro Domain eine kleine, domain-spezifische Rendering-Funktion (`_render_release_versioning(spec) -> str`, `_render_git_issue_naming(spec) -> str`), die die YAML-Felder in die exakte heutige Markdown-Form bringt (Tabellen-Layout, Großschrift `MAJOR`/`MINOR`/`PATCH` aus `bump: major` usw., Backtick-Wrapping bei Suffix-Beispielen). Nur (a) ist über beliebig viele zukünftige Domains hinweg wiederverwendbar; (b) ist bewusst pro Domain individuell zu schreiben — genau wie bei `BROWSER_VERIFICATION_BLOCK` heute schon (Snippet-Datei pro Block, kein universeller Formatierer). Ein neuer Convention-Domain-Typ (Branch-Naming, PR-Title-Naming, Dateibenennung, ...) braucht also weiterhin drei Dinge: neuer YAML-Eintrag, neue Platzhalter-Referenz im Zieltemplate, und eine neue, kleine `_render_<domain>()`-Funktion — nicht nur die ersten zwei.

### C) Verhalten bei fehlender Zielrolle

Sync-Zeit-Check nach dem `active_roles`-Muster aus `delegation_table.py:16-17`, angewendet pro Konventions-Domain:

```python
active_roles = set(config.get("roles")) if config.get("roles") is not None else None  # None = alle Rollen aktiv

for domain, spec in resolved_conventions.items():
    declared_roles = spec.get("applies_to_roles", [])
    for role in declared_roles:
        if active_roles is not None and role not in active_roles:
            log.skip(
                f"conventions.{domain}",
                f"Rolle '{role}' nicht in project.yaml roles: — Konvention "
                f"'{domain}' wird nicht injiziert (kein Platzhalter berechnet)"
            )
            continue
        # render block for (domain, role) → variable name, z.B. RELEASE_VERSIONING_BLOCK
```

**Rückfallwert:** Für eine deklarierte-aber-inaktive Rolle wird **gar keine Variable berechnet** (nicht einmal ein Leerstring) — der Platzhalter im jeweiligen Rollen-Template ist irrelevant, weil diese Rollen-Datei ohnehin nicht generiert wird, sobald die Rolle nicht in `active_roles` ist (bestehendes Verhalten der Agenten-Generierungsschleife). Der `log.skip(...)`-Aufruf ist trotzdem sinnvoll für Transparenz beim `--dry-run`/`--check`, z.B. wenn ein Preset `applies_to_roles: [release]` deklariert, aber `release` nicht in `project.yaml roles:` enthalten ist — dann soll sichtbar sein, dass die Konvention bewusst übersprungen wurde, statt stillschweigend zu verschwinden. **v1-Einschränkung:** `applies_to_roles` unterstützt pro Domain nur genau eine Rolle — die Listen-Syntax ist reine Forward-Compat, siehe YAML-Kommentar in Abschnitt 5 und Risiken (Abschnitt 8).

## 5. Default-Konventionen (konkret)

`config/conventions-presets.yaml` (neu):

```yaml
# Conventions-Presets — steuern Namens-/Versionierungs-Konventionen je Domain.
# Projekte wählen via 'conventions-preset' in project.yaml.
# Einzelne Felder können via 'conventions:' Block überschrieben werden.
# Precedence: conventions (Projekt-Override) > conventions-preset > default.
#
# applies_to_roles: Render-Gate, KEIN Injektions-Mechanismus. Die tatsächliche
#   Ziel-Rolle ergibt sich ausschließlich daraus, welches Rollen-Template den
#   Platzhalter referenziert (z.B. {{RELEASE_VERSIONING_BLOCK}} in release.md),
#   nicht aus diesem Feld. applies_to_roles entscheidet nur, ob der Block
#   überhaupt berechnet wird: fehlt die hier genannte Rolle in project.yaml
#   roles:-Allowlist, wird der Block übersprungen (log.skip, kein Fehler).
#   Syntax ist eine Liste (Forward-Compat für später), v1 unterstützt aber nur
#   genau EINE Rolle pro Domain — mehr als ein Eintrag ist ein Konfigurations-
#   fehler, den der Resolver mit klarer Fehlermeldung ablehnt.

presets:

  # Entspricht 1:1 dem heutigen hartkodierten Verhalten von release.md/git.md.
  # Migrations-Invariante: 'default' MUSS den heutigen Status quo reproduzieren.
  default:
    release:
      applies_to_roles: [release]
      versioning:
        scheme: semver
        tag_format: "v{major}.{minor}.{patch}"
        bump_rules:
          - {trigger: "Breaking change", bump: major, example: "Removed commands, incompatible config"}
          - {trigger: "New feature", bump: minor, example: "New commands, new settings"}
          - {trigger: "Bugfix / docs", bump: patch, example: "Bugfixes, performance, doc fixes"}
          - {trigger: "Alpha/Beta", bump: suffix, example: "-alpha.x / -beta.x"}
      changelog:
        format: keep-a-changelog
        sections: [Added, Fixed, Changed, Removed]
        entry_prefix: "REQ-xxx: "   # bewusst unverändert ggü. heute (siehe Abschnitt 8)
    issues:
      applies_to_roles: [git]
      # Vokabular wird 1:1 von commit-conventions.md übernommen, nicht neu erfunden.
      title_format: "{type}: {description}"
      types: [feat, fix, docs, chore, refactor, test, perf]
      labels:
        namespace: "type: {type}"
      closing_keywords: [Fixes, Closes, Resolves]
```

Beispiel-Override in einem Zielprojekt (`project.yaml`):

```yaml
conventions-preset: default
conventions:
  release:
    versioning:
      scheme: calver
      tag_format: "{year}.{month}.{patch}"
```

Gerenderter `RELEASE_VERSIONING_BLOCK` (Auszug, Default-Preset — inhaltlich identisch zur heutigen Tabelle in `release.md`):

```markdown
| Change | Bump | Example |
|--------|------|---------|
| Breaking change | MAJOR | Removed commands, incompatible config |
| New feature | MINOR | New commands, new settings |
| Bugfix / docs | PATCH | Bugfixes, performance, doc fixes |
| Alpha/Beta | Suffix | `-alpha.x` / `-beta.x` |
```

Gerenderter `GIT_ISSUE_NAMING_BLOCK` (neu, es gibt heute kein Äquivalent in `git.md`):

```markdown
**Issue-Titel-Format:** `<type>: <description>` — Types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `perf` (identisch zum Commit-Type-Vokabular, siehe `commit-conventions.md`).
**Labels:** `type: <type>` (Namespace-Label je Issue-Type).
**Closing-Keywords:** `Fixes #123`, `Closes #123`, `Resolves #123` im PR/Commit.
```

## 6. Scope v1

### E) Release-Naming + Issue-Naming zusammen, in einem Zug

**Empfehlung:** Beide Anwendungsfälle in v1 umsetzen — nicht nur Release konkret bauen und Issue-Naming bloß als Architektur-Beispiel dokumentieren.

**Begründung:** Die Kernanforderung des Nutzers ist explizit, dass das Fundament *nachweislich* wiederverwendbar ist, nicht nur behauptet. Eine Abstraktion, die nur einen einzigen Konsumenten hat (Release), ist per Definition unbewiesen — man weiß nicht, ob `applies_to_roles`, die Preset-Struktur und `render_convention_block()` wirklich domain-agnostisch sind, bis ein zweiter, strukturell andersartiger Konsument (Issue-Naming: andere Rolle, andere Feldstruktur, kein Versionsschema) tatsächlich gebaut wurde. Der Mehraufwand für den zweiten Anwendungsfall ist gering (kein neues Versionsschema, nur `title_format` + `types` + `labels` + `closing_keywords`, alles bereits aus `commit-conventions.md`/`issue-lifecycle/SKILL.md` ableitbar) — der Erkenntnisgewinn (ist die Abstraktion tragfähig?) ist hoch. "Nur dokumentieren, nicht bauen" würde exakt das Risiko eingehen, das der Nutzer vermeiden wollte: eine Abstraktion, die am Reißbrett gut aussieht, aber beim ersten echten zweiten Fall bricht.

### F) Issue #452 (Prozess je Projekttyp)

**Empfehlung:** `{{#if PROJECT_TYPE_*}}`-konditionierte Workflow-Varianten in `release.md`, **kein** Plugin-/Step-System nach `release-please`-Vorbild — und **außerhalb des Scopes von v1** dieses Konzepts.

**Begründung:**
- Aufwand/Nutzen: Ein Plugin-Registry mit Per-Typ-Strategie-Modulen (wie `release-type` bei release-please) lohnt sich bei einer offenen, wachsenden Zahl von Release-Strategien mit potenziell externen Plugins. agent-meta hat aktuell eine Handvoll bekannter Projekttypen (Library/CLI/Web-App/Service) und keinen Plugin-Anspruch — der bereits vorhandene `{{#if}}`/`*_ENABLED`-Mechanismus (`strip_inactive_conditional_blocks`) deckt das ohne neue Infrastruktur ab.
- **Andere Achse als Naming/Versionierung:** #452 betrifft *Workflow-Schritte* (Build-Artefakt ja/nein, npm-Publish ja/nein, GitHub-Release ja/nein), nicht *wie Dinge heißen*. Es sauber innerhalb desselben `conventions-presets.yaml`-Schemas unterzubringen würde die Domain-Grenze verwischen, die Abschnitt A gerade bewusst gezogen hat.
- **Konkreter Vorschlag für später (nicht Teil dieses v1):** neue Top-Level-Variable `PROJECT_TYPE` (`library`/`cli`/`web-app`/`service`) in `project.yaml`, daraus abgeleitete `PROJECT_TYPE_LIBRARY_ENABLED` etc. (analog zu `SE_ENABLED`), `{{#if PROJECT_TYPE_LIBRARY_ENABLED}}...{{/if}}`-Blöcke um die npm/PyPI-Publish-Schritte in `release.md`. Trigger für eine Revision zum Plugin-System: wenn die Zahl der Projekttyp-Varianten signifikant wächst (>8–10) oder Kombinationen (Library *und* CLI) nötig werden.

**v1 baut also:** `config/conventions-presets.yaml` (Default-Preset für `release` + `issues`), `scripts/lib/conventions.py` (`resolve_conventions`, `render_convention_block`), neue Platzhalter (`RELEASE_VERSIONING_BLOCK`, `RELEASE_CHANGELOG_BLOCK`, `GIT_ISSUE_NAMING_BLOCK`), Umbau von `release.md`/`git.md` auf diese Platzhalter, Rollen-Degradierung nach Muster C.
**v1 baut NICHT:** Projekttyp-Prozessvarianten (#452 — separates, kleineres Folge-Ticket mit dem `{{#if PROJECT_TYPE_*}}`-Ansatz), Erweiterung von `sync_rules()` um Rollen-Scope für Prosa-Rules (siehe Risiken).

## 7. Migrationspfad für bestehende Projekte

**Invariante:** Kein Projekt ohne eigene `conventions-preset:`/`conventions:`-Konfiguration darf nach dieser Änderung einen anderen generierten `release.md`/`git.md`-Inhalt bekommen als vorher.

1. `default`-Preset in `config/conventions-presets.yaml` wird Feld für Feld aus dem heute hartkodierten Text in `release.md`/`git.md` abgeleitet (siehe Abschnitt 5) — nicht neu erfunden.
2. `render_convention_block()` erzeugt für `default` exakt den Markdown-Text, der heute an derselben Stelle steht (Byte-für-Byte-Diff-Test gegen die aktuelle Template-Ausgabe für ein Projekt ohne `roles:`-Einschränkung). Der Diff-Test läuft konkret gegen den Output der domain-spezifischen Rendering-Funktionen (`_render_release_versioning()`, `_render_git_issue_naming()`, siehe Abschnitt 4B) — die generische Preset-Resolution/Rollen-Gating-Schicht erzeugt selbst keinen Markdown-Text.
3. `conventions-preset` fehlt in `project.yaml` → Fallback `"default"` (wie bei `rules-preset`/`dod-preset` heute schon).
4. Rollout-Reihenfolge: (a) `conventions.py` + `conventions-presets.yaml` einführen, Platzhalter berechnen, aber Templates noch NICHT umstellen → Dry-Run-Vergleich (`sync.py --dry-run`) zeigt keine Diffs. (b) `release.md`/`git.md` auf Platzhalter umstellen, Version bumpen (Minor — neues optionales Verhalten, kein Breaking Change) nach `conventions`-Skill-Konvention. (c) Gegen das Test-Repo (`test-repo:` in `project.yaml`, `../agent-meta-test`) sync-diffen: erwartetes Ergebnis = keine inhaltliche Änderung für Projekte ohne eigene Convention-Config.
5. Test-Suite-Impact prüfen: bestehende Test-Suite (`tests/`) muss nach der Umstellung grün bleiben. Verifiziert: aktuell assertet kein Test die SemVer-Tabelle/das Changelog-Format literal (Tests nutzen synthetische Templates) — Risiko gering, aber als expliziter Migrationsschritt aufgenommen.
6. `CLAUDE.md`-Variablentabelle und `howto/configs/project.yaml.example` um die neuen Keys ergänzen (Pflicht laut `conventions`-Skill: "Adding a New Placeholder").
7. Bestehende Projekte, die bereits manuell von der heutigen `release.md`/`git.md`-Struktur abweichen (z.B. eigene `.claude/3-project/*-release-ext.md`-Extension), bleiben unberührt — Extensions werden weiterhin zur Laufzeit vom Agenten gelesen, unabhängig vom Preset-Mechanismus.

## 8. Offene Risiken/Fragen für die Review-Stufe

- **REQ-Präfix vs. `dod.req-traceability`:** Der Default behält `entry_prefix: "REQ-xxx: "` bewusst unverändert bei, auch für Projekte mit `req-traceability: false` (wie agent-meta selbst) — das ist heute schon so (latente Inkonsistenz, kein neues Problem). Sollte der Default künftig `entry_prefix` leeren, wenn `DOD_REQ_TRACEABILITY=false`? Das wäre eine inhaltliche Verbesserung, aber eine Verhaltensänderung für bestehende Projekte — bewusst NICHT in diesem v1, da es die Migrations-Invariante (Abschnitt 7) verletzen würde. Separate Entscheidung nötig.
- **Preset-Wucherung:** Vierte Preset-Achse neben `rules-preset`/`dod-preset`/`tier-preset`. Mitigation ist reine Doku (Übersichtstabelle); mittelfristig denkbar, alle vier unter einem gemeinsamen `presets:`-Namespace in `project.yaml` zu konsolidieren — größerer Schnitt, nicht Teil dieses Konzepts.
- **Skalierung der Block-Platzhalter:** Jede neue Convention-Domain braucht eine eigene `_BLOCK`-Variable. Bei 2–3 Domains (Release, Issues) unkritisch; ab ca. 5+ Domains könnte das den gleichen Namens-Wildwuchs reproduzieren, den das `{{#if}}`-System schon hat. Trigger für Revision: mehr als ~5 aktive Convention-Domains.
- **Rollen-Scope für Prosa-Rules bleibt ungelöst:** Dieses Konzept löst Rollen-Scoping nur für datengetriebene Konventions-Blöcke (via eigenes Agenten-Template), nicht für beliebige Prosa-Rule-Dateien in `.claude/rules/`. Falls künftig der Bedarf entsteht, eine bestehende Rule (z.B. eine neue Sicherheits-Policy) nur für eine einzelne Rolle sichtbar zu machen, braucht es eine strukturell größere Änderung (Rules würden in einzelne Agenten-Templates eingebettet statt geteilt) — separates Folgekonzept, kein Teil von v1.
- **Label-Erstellung als Seiteneffekt:** `issues.labels.namespace` impliziert, dass der `git`-Agent (oder `feedback`) GitHub-Labels ggf. anlegen muss (`gh label create`), falls sie im Ziel-Repo nicht existieren. Ungeklärt, ob das Teil des `git`-Agent-Workflows wird oder eine reine Doku-Konvention ohne automatisches Anlegen bleibt — Klärung in der Requirements-Stufe.
- **Doppelte Quelle für Issue-Konventionen:** `issue-lifecycle`-Skill (Prozess: Referenzieren, Closing-Keywords) und der neue `GIT_ISSUE_NAMING_BLOCK` (Naming: Titel-Format, Labels) überlappen sich beim Closing-Keyword-Feld. Sollte `issue-lifecycle/SKILL.md` künftig aus derselben `conventions-presets.yaml`-Quelle gerendert werden (Konsistenz) oder bleiben beide getrennt gepflegt (Redundanz-Risiko)? Klärung in der Requirements-Stufe.
- **Versionsbump-Umfang:** `release.md` und `git.md` ändern sich strukturell (neue Platzhalter statt hartkodierter Abschnitte) — nach `conventions`-Skill-Konvention mindestens Minor-Bump für beide, ggf. auch für andere Rollen, die `release.md`/`git.md` per `2-platform`-Override patchen (Instruction-Bleed-Check nötig, siehe `conventions`-Skill Abschnitt "Composition-Risiko").
- **Preset/Template-Referenz-Drift:** `applies_to_roles` ist nur ein Render-Gate (siehe Abschnitt 4A), keine erzwungene Bindung. Ein Preset-Autor könnte `applies_to_roles: [git]` deklarieren, den Platzhalter aber versehentlich in `release.md` referenzieren — es gibt in v1 keinen Sync-Zeit-Validator, der Preset-Deklaration und tatsächliche Platzhalter-Referenz im Template gegeneinander prüft. Bewusster Trade-off in v1 (Konvention statt Enforcement, analog zum bereits akzeptierten Trade-off beim Orchestrator-Guard-Sentinel, siehe `.claude/rules/branch-guard.md` „Bekannte Grenzen"). Sollte in der Requirements-Stufe als möglicher `--validate`-Check aufgenommen werden (z.B.: für jede Domain prüfen, ob der erzeugte `_BLOCK`-Platzhalter tatsächlich in genau der/den in `applies_to_roles` deklarierten Rolle(n)-Datei(en) referenziert wird).
- **Mehrfach-Rollen pro Domain nicht in v1:** `applies_to_roles` unterstützt in v1 nur genau eine Rolle pro Domain (siehe YAML-Kommentar Abschnitt 5) — es gibt aktuell kein Mapping-Schema für den Fall, dass zwei aktive Rollen mit unterschiedlichem Content für dieselbe Domain versorgt werden sollen (z.B. `release` und `docs` mit je eigenem Changelog-Format). Potenzielle spätere Erweiterung mit dediziertem (domain, role) → Variablenname-Mapping-Schema, kein Teil dieses Konzepts.
- **Extension-Content-Drift:** Eine `.claude/3-project/release-ext.md`/`git-ext.md`, die den heute hartkodierten Text zitiert statt ihn zu patchen (Content-Quoting statt Patch), kann bei einer Preset-Abweichung vom Default still driften, ohne dass das auffällt. Risiko gering (Extensions sind additiv und laufzeitgelesen, kein Sync-Zeit-Konflikt), aber erwähnenswert für die Requirements-Stufe.

## Handoff

Empfohlener nächster Schritt: `requirements` (Kern-Idee, Scope v1 und Architektur-Entscheidung sind klar; keine Blocker-Fragen offen, nur Detailfragen für die Review-/Requirements-Stufe in Abschnitt 8). Alternativ: `concept-reviewer` für eine Review-Schleife vor der Formalisierung, insbesondere wegen der zwei offenen Konsistenzfragen (REQ-Präfix-Verhalten, `issue-lifecycle`-Redundanz).
