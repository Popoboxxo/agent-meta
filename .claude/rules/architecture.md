# agent-meta — Schichten-Architektur

Dieses Repo ist das Meta-Repository für Agenten-Standards. Jede Änderung an Templates
wirkt sich auf alle Projekte aus die dieses Submodul einbinden.

## Schichten-Modell

```
0-external/   Externe Skill-Agenten aus Drittrepos (via Git Submodule).
              Höchste Priorität. Konfiguriert in config/skills-registry.yaml.
              approved: true/false — Meta-Maintainer Quality Gate.

1-generic/    Universell. Gilt für jedes Projekt. Wird immer generiert,
              solange kein Override in 2-platform oder 3-project existiert.

2-platform/   Plattformspezifisch. Überschreibt den Generic-Agent für alle
              Projekte auf dieser Plattform.
              Modi: Full-replacement (kein extends:) oder Composition (extends: + patches:)

3-project/    Projektspezifisch.
              - <rolle>.md      → Override: ersetzt generierten Agent komplett
              - <rolle>-ext.md  → Extension: additiv geladen vom generierten Agent
```

**Override-Reihenfolge:**
```
1-generic  →  2-platform  →  3-project/<rolle>.md  →  0-external (eigenständige Rollen)
```

## Composition-Syntax (2-platform und 3-project)

```yaml
extends: "1-generic/<rolle>.md"
patches:
  - op: append-after        # nach Section einfügen
    anchor: "## Section"
    content: |
      ## Neue Section ...
  - op: replace             # Section vollständig ersetzen
    anchor: "## Section"
    content: |
      ## Section ...
  - op: delete              # Section entfernen
    anchor: "## Section"
  - op: append              # ans Dateiende anhängen
    content: |
      ## Anhang ...
```

Composition wird zur Build-Zeit aufgelöst — das generierte `.claude/agents/<rolle>.md`
enthält das vollständige Dokument. Kein `extends:` im Output.

## Abhängigkeitsprinzip

Jede Änderung an einer Quelldatei propagiert in alle instanziierten Projekte
beim nächsten `sync.py`-Lauf. Daher:

- **1-generic geändert** → alle Projekte neu syncen
- **2-platform geändert** → alle Projekte auf dieser Plattform neu syncen
- **config/role-defaults.yaml geändert** → alle Projekte neu syncen
- **config/skills-registry.yaml geändert** → alle betroffenen Projekte neu syncen

## Platzhalter-Escape

Für Dokumentation in Templates: Ein Platzhalter kann escaped werden, indem sein
Variablenname zusätzlich in Prozentzeichen eingeschlossen wird, direkt innerhalb
der doppelten geschweiften Klammern (Reihenfolge: zwei öffnende geschweifte
Klammern, Prozentzeichen, VARIABLENNAME, Prozentzeichen, zwei schließende
geschweifte Klammern). `sync.py` erkennt diese Schreibweise, entfernt beim
Rendern die beiden Prozentzeichen wieder und lässt den reinen Platzhalter
unverändert und unsubstituiert im generierten Output stehen — so kann ein
Platzhalter-Beispiel literal in Doku-Templates erscheinen, ohne selbst ersetzt
zu werden. Exakte Implementierung: `scripts/lib/config.py::substitute()`.

**Hinweis für Doku-Autoren:** Der escapte Token selbst darf hier in dieser
Quelldatei nicht als roher, verarbeitbarer Text auftauchen — jedes Vorkommen
würde von `substitute()` beim nächsten Sync genauso entschärft wie ein echter
Platzhalter, wodurch die Doku ihr eigenes Beispiel unsichtbar macht.
