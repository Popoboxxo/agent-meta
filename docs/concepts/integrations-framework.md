# Generalisiertes Integrations-Framework für agent-meta — paket-verwaltete MCP-Tools (Referenz-Implementierung: semble v0.3.4)

---

## 1. Problem & Ziel

- Semble (https://github.com/MinishLab/semble, v0.3.4) ist weder Git-Submodul-Skill noch rein manuell konfigurierter MCP-Server.
- Es ist ein paket-verwaltetes Tool mit Lifecycle: installieren → initialisieren → indexieren → als MCP-Server bereitstellen.
- Ziel: EINE generische Kategorie „Integrations" die beliebige pip/uv-verwaltete Tools im selben Stil aufnimmt. Semble = erste Instanz.

---

## 2. Drei-Kategorien-Modell

Als Tabelle:

| Kategorie | Verwaltung | Konfiguration | Status |
|-----------|-----------|---------------|--------|
| Skills | Git-Submodul / Datei-Kopie | skills-registry.yaml | bestehend |
| MCP-Server | manuell | plugin-catalog.yaml | bestehend |
| Integrations | pip/uv-Paket | integrations-registry.yaml | NEU |

Integrations sind die einzige Kategorie mit System-Side-Effects (Paketinstallation) → strikte Trennung deklarativ/imperativ.

---

## 2.5. Verworfene Alternativen

Folgende Ansätze wurden evaluiert und verworfen:

| Alternative | Verworfen weil |
|---|---|
| **semble als 0-external/Skill via Git-Submodul** | Paket-Lifecycle nicht abbildbar, Submodul-Struktur passt nicht zu pip-Installation; Skills sind für Code-Templates gedacht, nicht für verwaltete Binaries |
| **Rein manuell in plugin-catalog.yaml ohne Lifecycle-Management** | Init- und Index-Schritte nicht dokumentierbar; kein Two-Gate; keine reproduzierbare, automatisierbare Einrichtung |
| **Install-Hook direkt in sync.py mit Opt-In** | Bricht Stdlib-only und side-effect-freies Design von sync.py (siehe Issue #255); würde sync für Anfänger zu komplex machen |

---

## 3. Kern-Architekturentscheidung: Sync deklarativ, Init imperativ

Zwei klar getrennte Phasen:

**sync.py (side-effect-frei):**
- MCP-Config → settings.json
- Tool-Mapping → rules/integrations.md
- Agent-Awareness
- Pending-Marker setzen

**init-integrations.py (imperativ):**
- Paket installieren
- Init-Command ausführen
- Index-Command ausführen
- MCP-Healthcheck
- Pending-Marker löschen

Begründung:
- sync.py hat keinen Install-Hook (bestehender Befund)
- Stdlib-only-Philosophie
- Issue #255 graceful degradation
- Sync darf nie ungefragt Pakete installieren

**Präzisierung „side-effect-frei":**
sync.py ist side-effect-frei im Sinne von: keine Paketinstallation, keine lang laufenden Prozesse. Die Reindexierung (z.B. `semble index`) läuft ausschließlich über `init-integrations.py --reindex`, nie über `sync.py`.

---

## 4. Meta-Registry: config/integrations-registry.yaml (neu)

Vollständiges YAML-Beispiel (exakt übernehmen):

```yaml
version: 1
integrations:
  semble:
    approved: true
    package: "semble==0.3.4"
    installer: uv                     # PRO INTEGRATION frei wählbar (uv|pip), KEIN globaler Default
    min_python: "3.10"
    mcp:
      command: ["semble", "mcp"]
      transport: stdio
      tools:
        - name: search
          hint: "Semantische Code-Suche statt grep für Konzept-/Intent-Lookups"
        - name: find_related
          hint: "Ähnliche Snippets zu einer Fundstelle finden"
    lifecycle:
      init:  ["semble", "install"]
      index: ["semble", "index", "{{TARGET_ROOT}}"]
      reindex_on: [manual]
      healthcheck: ["semble", "--version"]
    options:
      content:
        type: array
        items: [code, docs, config]
        default: [code]
        maps_to_arg: "--content"
      top_k:
        type: integer
        default: 5
        maps_to_arg: "--top-k"
    capabilities: [code-search, semantic-retrieval]
    description: "Hybrid semantic + lexical code search (Model2Vec + BM25)"
    docs_url: "https://github.com/MinishLab/semble"
```

Wichtige Designentscheidungen zu diesem YAML:
- `options` + `maps_to_arg` ist der Generalisierungs-Kern. Jede Integration deklariert Optionen + CLI-Mapping selbst. Neue Tools = nur YAML, kein Python.
- `installer`-Feld ist PRO Integration (Designentscheidung), kein globaler Default.
- Two-Gate-Muster: `approved` im Meta-Repo (wie Skills) + `enabled` im Projekt.
- **Generalisierungs-Grenze von `maps_to_arg`:** Aktuell werden nur CLI-Argument-Mappings unterstützt (z.B. `maps_to_arg: "--content"`). Integrations die Umgebungsvariablen oder JSON-Config-Dateien erwarten, passen nicht ins aktuelle Schema und sind Future-Work (z.B. erweiterte Syntax: `maps_to: {kind: arg|env|config, target: ...}`).

---

## 5. Projekt-Toggle: .meta-config/project.yaml

YAML-Beispiel:

```yaml
integrations:
  semble:
    enabled: true
    content: [code, docs]
    top_k: 8
```

Optionen werden dynamisch gegen das `options`-Schema aus der Registry validiert, nicht hartcodiert.

---

## 6. Schema-Erweiterung: config/project-config.schema.json

Die bestehende Schema-Datei bekommt einen generischen `integrations`-Block mit `additionalProperties` und `enabled` als Pflichtfeld. Tiefere Optionen werden zur Laufzeit gegen die Registry validiert — kein integrationssspezifisches Hardcoding im Schema.

---

## 7. Neues Modul: scripts/lib/integrations.py

Funktionssignaturen:

- `load_integrations_registry(registry_path)` — lädt und validiert integrations-registry.yaml
- `resolve_enabled_integrations(registry, project_config)` — Two-Gate: approved AND enabled
- `validate_options(integration_name, user_options, registry_options_schema)` — dynamische Validierung gegen Registry-Schema
- `build_mcp_entries(enabled_integrations)` — gibt MCP-Einträge zurück zum Merge durch mcp.py
- `build_tool_awareness(enabled_integrations)` — generiert Inhalte für rules/integrations.md
- `write_pending_marker(target_path, pending_integrations)` — schreibt Marker wenn Init noch aussteht; `init-integrations.py` löscht den Marker nach Completion (Symmetrie)

Rahmenbedingungen:
- Keine externen Dependencies außer Stdlib
- PyYAML-Fallback wie in Issue #255 (graceful degradation). Workaround: Issue #255 etablierte einen minimalen YAML-Fallback-Parser für einfache Key-Value-Strukturen. Für komplexe Schema-Validierung (options.type, options.items) ist PyYAML de-facto benötigt; der Fallback deckt nur das Registry-Laden ab (flache Struktur), nicht die options-Validierung.
- Hängt in `build_variables()` ein → stellt `INTEGRATIONS_ENABLED` + `INTEGRATION_TOOLS_HINT` bereit (analog zu `ANALYSIS_ENABLED`/`FILE_AFFINITY_HINT`)

---

## 8. Init-Script: scripts/init-integrations.py (neuer Entry-Point)

**Flags:**
- (default, ohne Flag): Mit Bestätigung — zeigt was installiert wird und fragt einmal
- `--yes`: Bestätigung überspringen (für CI/Automation)
- `--reindex`: Nur Re-Indexierung, kein erneutes Install
- `--check`: Healthcheck ohne Seiteneffekte

**INSTALL-POLICY (Designentscheidung):** Bestätigung ist Default. Das Script zeigt package + installer und fragt einmal. `--yes` überspringt für CI.

**Ablauf (idempotent):**
1. Healthcheck → bereits installiert? Skip install
2. Paket installieren (via konfiguriertem Installer)
3. Init-Command einmalig ausführen (via State-Marker)
4. Index-Command ausführen (Optionen über `maps_to_arg` aufgelöst)
5. MCP-Healthcheck
6. Pending-Marker löschen

State wird in `.meta-config/.integrations-state.json` gespeichert.

Funktioniert identisch in Meta- und Ziel-Repo. Aufruf aus Ziel-Repo: `python .agent-meta/scripts/init-integrations.py`

**Multi-Repo/Submodul-Pfade (bei Ziel-Repo als agent-meta-Submodul):**

| Datei | Ort bei Meta-Repo | Ort bei Ziel-Repo (als Submodul) |
|---|---|---|
| `integrations-registry.yaml` | `config/` | gelesen aus `.agent-meta/config/` (Submodul-Pfad) |
| `.integrations-state.json` | `.meta-config/` (falls Meta-Self-Test) | `.meta-config/` (Ziel-Repo) |
| Pending-Marker | `.claude/` (Meta-Repo) | `.claude/` (Ziel-Repo) |

---

## 9. Agent-Awareness (provider-agnostisch)

- sync.py generiert `.claude/rules/integrations.md` (analog zur MCP-Rule) — listet aktive Tools + Hints
- Quelle: `rules/1-generic/integrations.md` Template → per Sync generiert nach `.claude/rules/integrations.md`, `.gemini/rules/integrations.md`, etc.
- Generische Templates (1-generic/) bleiben sauber und nennen nie „semble" (Provider-Agnostic-Rule)
- Beispiel-Injektion in die generierte Rule: „Wenn mcp__semble__search verfügbar: semantische Suche vor grep für Konzept-Lookups"
- Der Mechanismus ist identisch zum bestehenden MCP-Rule-Generierungsweg

---

## 10. End-to-End-Flow (Ziel-Repo, semble.enabled: true)

1. **sync.py ausführen** → schreibt MCP-Eintrag in settings.json + generiert rules/integrations.md + setzt pending-marker
2. **Hinweis-Ausgabe:** „1 Integration ausstehend: `python .agent-meta/scripts/init-integrations.py`"
3. **init-integrations.py ausführen** → `uv install semble==0.3.4` → `semble install` → `semble index .`
4. **Agent-Session starten** → `mcp__semble__search` verfügbar, vollumfänglich funktional

---

## 11. Neu vs. Wiederverwendet

| Artefakt | Status | Anmerkung |
|----------|--------|-----------|
| `config/integrations-registry.yaml` | NEU | Neue Meta-Registry |
| `scripts/lib/integrations.py` | NEU | Neues Modul |
| `scripts/init-integrations.py` | NEU | Neuer Entry-Point |
| `rules/1-generic/integrations.md` Template | NEU | Für Rule-Generierung |
| Schema-Block in `project-config.schema.json` | NEU | Erweiterung des bestehenden Schemas |
| Two-Gate-Muster (approved + enabled) | WIEDERVERWENDET | Wie bei Skills |
| `generate_mcp_artifacts()` aus mcp.py | WIEDERVERWENDET | MCP-Einträge werden gemergt |
| `build_variables()` Toggle-Mechanik | WIEDERVERWENDET | Analog ANALYSIS_ENABLED |
| settings.json-Writer | WIEDERVERWENDET | Bestehende Infrastruktur |
| PyYAML-Fallback (Issue #255) | WIEDERVERWENDET | Graceful degradation |
| gitignore-Management | WIEDERVERWENDET | `.integrations-state.json` hinzufügen |

---

## 12. Sicherheit & Risiken

Paketinstallation ist eine Supply-Chain-Aktion. Schutzmaßnahmen:

- **Two-Gate:** `approved: true` im Meta-Repo (Quality Gate durch Meta-Maintainer) UND `enabled: true` im Projekt. Das `approved`-Flag ist der Vertrauensanker des Meta-Repos; Forks müssen eigene Approval-Policy definieren.
- **Gepinnte Version:** `package: "semble==0.3.4"` — keine Range-Versionen
- **Expliziter Init-Schritt:** Nie automatisch während sync.py — immer separater Schritt
- **Bestätigung default:** init-integrations.py fragt vor Installation, `--yes` ist opt-out

**Identifizierte Risiken:**

| Risiko | Mitigation |
|---|---|
| **uv nicht verfügbar** | init-integrations.py prüft Verfügbarkeit; Fallback auf pip wenn `installer: uv` und uv fehlt → Warnung + automatischer Fallback |
| **Globaler semble-State** | `semble install` registriert MCP global. Bei Multi-Repo-Setup auf einer Maschine wird derselbe semble-MCP-Server geteilt — Index ist repo-lokal (via `semble index <TARGET_ROOT>`), MCP-Registrierung aber einmalig |
| **Reindex-Performance** | Große Repos können lange brauchen. Reindex läuft nur via `init-integrations.py --reindex` (nie automatisch während sync.py) |
| **Hash-Pinning** | `package: "semble==0.3.4"` pinnt Version, aber kein Hash. Für produktive Setups empfehlenswert: lockfile oder Hash-Pin |

---

## 13. semble v0.3.4 — Faktenbasis

**Technologie:**
- Hybrid-Search: Model2Vec (semantisch) + BM25 (lexikalisch) + RRF-Ranking
- tree-sitter für Code-Chunking
- ~98% Token-Einsparung gegenüber grep+read
- CPU-only, ~1.5ms/Query

**Voraussetzungen:**
- Python ≥ 3.10
- Dependencies: model2vec, vicinity, bm25s, tree-sitter, numpy, orjson u.a.

**Version v0.3.4 (12.06.2026):**
- Antigravity-Support (Antigravity ist der Google-Gemini-CLI-Client analog zu Claude Code)
- Command Code Support
- Concurrent-Write-Fix

**Installation:**
```bash
uv tool install semble
# oder
pip install semble==0.3.4

# Danach MCP-Integration aktivieren:
semble install
```

**MCP-Tools:** `search`, `find_related`

**Projektseite:** https://github.com/MinishLab/semble

---

## 14. Offene Punkte / Nächste Schritte

### Implementierungsreihenfolge

Umsetzung folgt in separater Session (User-Entscheidung).

1. `config/integrations-registry.yaml` + Schema-Block anlegen
2. `scripts/lib/integrations.py` implementieren
3. `mcp.py`-Merge integrieren
4. `scripts/init-integrations.py` implementieren
5. Agent-Awareness-Rule-Template (`rules/1-generic/integrations.md`) erstellen
6. semble als erste Instanz testen: erst in Meta-Repo, dann in Ziel-Repo

### Offene Designfragen

Die folgenden Punkte sind bewusst nicht entschieden und sollten vor/während der Implementierung geklärt werden:

- **uv vs. pip Fallback-Verhalten:** Bei fehlender uv-Installation: Warnung + automatischer Fallback auf pip, oder Abbruch mit Installationsanweisung?
- **maps_to_arg-Generalisierung:** Wie soll die Syntax erweitert werden um Env-Variablen und Config-Dateien zu unterstützen? Zeitpunkt der Generalisierung (vor oder nach semble-Rollout)?
- **Validierungs-Zeitpunkt:** Sollen Optionen bereits in sync.py validiert werden, oder erst in init-integrations.py bei der Indexierung?
- **approved-Flag-Policy für Forks:** Wer ist zuständiger Meta-Maintainer wenn agent-meta geforkt wird? Wie wird approval delegiert?
- **uv-Modus klären:** Soll `uv pip install semble==0.3.4` (Projekt-Env) oder `uv tool install semble` (globales Tool) verwendet werden? Beeinflusst PATH-Verfügbarkeit der `semble`-CLI und Isolation zwischen Repos.
