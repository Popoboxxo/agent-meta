# Agent Composition — extends & patches

> Dieses Dokument beschreibt das Composition-System für 2-platform (und 3-project Override) Agenten.
> Statt Vollkopien von 1-generic zu pflegen können Plattform-Agenten einen Base-Template **erweitern**
> und gezielt **Sections ersetzen, ergänzen oder löschen**.

---

## Das Problem: Vollkopien werden stale

Ohne Composition ist `2-platform/sharkord-developer.md` eine vollständige Kopie von
`1-generic/developer.md` — plus Sharkord-spezifische Sections. Das bedeutet:

- Jede Änderung am Generic-Template muss manuell in alle Plattform-Kopien übertragen werden.
- `based-on` im Frontmatter ist nur deklarativ — sync.py hat keine Möglichkeit zu prüfen, ob
  die Kopie noch aktuell ist.
- Bei mehreren Plattformen skaliert das nicht.

---

## Lösung: Composition-Modus

Ein Plattform-Agent (oder 3-project Override) kann statt eines Vollkörpers nur **Frontmatter mit
`extends:` und `patches:`** enthalten. sync.py erkennt `extends:` und führt die Komposition durch:

```
Base-Template (1-generic/developer.md)
     ↓  patches anwenden
Composiertes Dokument
     ↓  Variable-Substitution
.claude/agents/developer.md  (finales Ergebnis)
```

Das finale `.claude/agents/developer.md` im Zielprojekt **enthält kein `extends:`** — es ist ein
vollständiges, fertig zusammengesetztes Dokument.

---

## Zwei Modi für 2-platform

| Modus | Erkennungsmerkmal | Verhalten |
|-------|------------------|-----------|
| **Full-replacement** (bestehend) | kein `extends:` im Frontmatter | Datei wird 1:1 verwendet |
| **Composition** (neu) | `extends: "1-generic/developer.md"` vorhanden | Base + patches werden zusammengeführt |

Beide Modi koexistieren. Bestehende Platform-Agenten ohne `extends:` funktionieren unverändert.

---

## Frontmatter-Struktur

```yaml
---
name: sharkord-developer
version: "2.0.0"
based-on: "1-generic/developer.md@1.4.1"
description: "..."
hint: "..."
tools:
  - Bash
  - Read
  # ... weitere Tools
extends: "1-generic/developer.md"      # ← Composition-Trigger
patches:                                # ← Liste der Patch-Operationen
  - op: replace
    anchor: "## Development Environment"
    content: |
      ## Build & Commands
      ...
  - op: append-after
    anchor: "## Build & Commands"
    content: |
      ## Sharkord Plugin-SDK
      ...
  - op: delete
    anchor: "## Delegation"
  - op: append
    content: |
      ## Anhang
      ...
---
```

**Wichtig:** Kein Datei-Body außerhalb des Frontmatter-Blocks. Der gesamte Inhalt kommt
aus dem Base-Template plus den Patches.

---

## Patch-Operationen

### `append-after` — Section ergänzen

Fügt `content` **nach** der durch `anchor` identifizierten Section ein.

```yaml
- op: append-after
  anchor: "## Build & Commands"
  content: |
    ## Sharkord Plugin-SDK

    Hier steht der neue Inhalt...
```

**Verhalten:**
- Findet die Section `## Build & Commands` (inkl. ihrem gesamten Inhalt)
- Fügt `content` nach dem Ende dieser Section (vor der nächsten Section) ein
- Warnung im sync.log wenn `anchor` nicht gefunden

---

### `replace` — Section ersetzen

Ersetzt die gesamte durch `anchor` identifizierte Section (Heading + Inhalt bis zur nächsten
gleichwertigen oder übergeordneten Section).

```yaml
- op: replace
  anchor: "## Development Environment"
  content: |
    ## Build & Commands

    {{DEV_COMMANDS}}
```

**Typischer Use-Case:** Section umbenennen, Inhalt anpassen, Platzhalter behalten.

---

### `delete` — Section entfernen

Entfernt die gesamte durch `anchor` identifizierte Section.

```yaml
- op: delete
  anchor: "## Delegation"
```

**Hinweis:** Auch die vorangehende Leerzeile wird mit entfernt.

---

### `append` — ans Ende anhängen

Hängt `content` an das Ende des Dokuments an. Kein `anchor` erforderlich.

```yaml
- op: append
  content: |
    ## Plattform-spezifischer Anhang

    Zusatzinfos für alle Projekte auf dieser Plattform.
```

---

## Anchor-Syntax

Der `anchor`-Wert muss **exakt dem Heading-Text** im Base-Template entsprechen — inkl. `#`-Präfix.

```yaml
anchor: "## Development Environment"   # ✓ exakt wie in developer.md
anchor: "## development environment"   # ✗ Groß/Kleinschreibung zählt
anchor: "Development Environment"      # ✗ Fehlendes ##
```

**Was passiert bei falschem Anchor?**
sync.py gibt eine `[WARN]`-Meldung im sync.log aus und lässt den Content unverändert.
Das generierte Dokument ist valide, aber der Patch wurde nicht angewendet.

**Anchors für `1-generic/developer.md`:**

| Anchor | Inhalt |
|--------|--------|
| `## Projektkontext` | PROJECT_CONTEXT, Ziel, Sprachen |
| `## Deine Zuständigkeiten` | Feature-Implementierung, Workflow, Qualität |
| `## Code-Konventionen` | CODE_CONVENTIONS, Best Practices, Fehlerbehandlung |
| `## Architektur & Verzeichnisstruktur` | ARCHITECTURE-Platzhalter |
| `## Commit-Konventionen` | Commit-Format-Tabelle |
| `## Development Environment` | DEV_COMMANDS-Platzhalter |
| `## Don'ts` | Verbote-Liste + EXTRA_DONTS |
| `## Delegation` | Verweise auf andere Agenten |
| `## Sprache` | Sprach-Einstellungen |

---

## Frontmatter-Merge-Regeln

Wenn `extends:` vorhanden, werden Frontmatter-Felder zusammengeführt:

| Feld | Quelle |
|------|--------|
| `name`, `version`, `description`, `hint`, `tools` | Override (Plattform-Datei) gewinnt |
| `based-on` | Override (Plattform-Datei) gewinnt |
| `extends`, `patches` | werden aus dem Output entfernt |
| alle anderen Felder | Override gewinnt über Base |

---

## Vollständiges Beispiel: sharkord-developer.md

```yaml
---
name: sharkord-developer
version: "2.0.0"
based-on: "1-generic/developer.md@1.4.1"
description: "Sharkord-spezifischer Developer-Agent mit Plugin-SDK Wissen."
hint: "Feature-Implementierung und Bugfixes nach REQ-IDs (Sharkord Plugin SDK)"
tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Agent
  - TodoWrite
extends: "1-generic/developer.md"
patches:
  - op: replace
    anchor: "## Development Environment"
    content: |
      ## Build & Commands

      {{DEV_COMMANDS}}

  - op: append-after
    anchor: "## Build & Commands"
    content: |
      ## Sharkord Plugin-SDK
      ... (SDK-Dokumentation)

  - op: replace
    anchor: "## Don'ts"
    content: |
      ## Don'ts
      ... (generische Don'ts + Sharkord-spezifische Don'ts)
---
```

Ergebnis: `developer.md` im Zielprojekt enthält alle Sections aus `1-generic/developer.md`,
mit Sharkord-Anpassungen bei `Development Environment` und `Don'ts`, plus dem neuen
`Sharkord Plugin-SDK`-Block.

---

## Debugging

### Composition prüfen

```bash
# dry-run zeigt was generiert wird (ohne zu schreiben)
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml --dry-run
cat sync.log  # INFO-Zeile: "composed from 1-generic/developer.md + sharkord-developer.md"
```

### Typische Fehler im sync.log

```
[WARN]   Composition patch 'append-after': anchor '## Build & Commands' not found in developer.md
```
→ Section existiert im Base nicht. Anchor-Text prüfen (Groß/Kleinschreibung, `#` Anzahl).

```
[WARN]   PyYAML not available — composition skipped. Install it with: pip install pyyaml
```
→ PyYAML ist nicht installiert. `pip install pyyaml` ausführen.

---

## Kompatibilität mit 3-project Overrides

Das `extends:/patches:` System funktioniert identisch für `.claude/3-project/<rolle>.md` Overrides:

```yaml
# .claude/3-project/myproject-developer.md (im Zielprojekt)
---
name: myproject-developer
extends: "1-generic/developer.md"
patches:
  - op: append-after
    anchor: "## Don'ts"
    content: |
      ### Projektspezifische Don'ts
      - Kein direkter DB-Zugriff außerhalb von `src/db/`
---
```

**Wichtig:** Wie bei 2-platform Composition-Dateien gilt auch hier — **kein Datei-Body
außerhalb des Frontmatter-Blocks.** Der gesamte Inhalt kommt aus dem Base-Template plus
den Patches. Text außerhalb des `---`-Blocks wird ignoriert.

**Hinweis:** Für rein additive Erweiterungen empfehlen wir weiterhin `-ext.md` Extensions
(kein sync.py-Involvement nötig). Overrides mit `extends:` eignen sich wenn Sections aus
dem Base-Template entfernt oder ersetzt werden sollen.

---

## Dependency Map

```
1-generic/developer.md
    └── extends → 2-platform/sharkord-developer.md
                      └── generiert → sk_plugin/.claude/agents/developer.md
                      └── generiert → sk_hero_introduce/.../.claude/agents/developer.md
```

Wenn `1-generic/developer.md` eine neue Section bekommt oder eine Section umbenennt:
1. `anchor`-Werte in `sharkord-developer.md` prüfen
2. Falls nötig: `patches` aktualisieren
3. Version in `sharkord-developer.md` erhöhen + `based-on` aktualisieren
4. Projekte neu syncen
