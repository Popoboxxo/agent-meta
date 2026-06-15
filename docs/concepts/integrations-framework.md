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
| MCP-Server | manuell | mcp-registry.yaml | bestehend |
| Integrations | pip/uv-Paket | integrations-registry.yaml | NEU |

Integrations sind die einzige Kategorie mit System-Side-Effects (Paketinstallation) → strikte Trennung deklarativ/imperativ.

---

## 2.5. Verworfene Alternativen

Folgende Ansätze wurden evaluiert und verworfen:

| Alternative | Verworfen weil |
|---|---|
| **semble als 0-external/Skill via Git-Submodul** | Paket-Lifecycle nicht abbildbar, Submodul-Struktur passt nicht zu pip-Installation; Skills sind für Code-Templates gedacht, nicht für verwaltete Binaries |
| **Rein manuell in mcp-registry.yaml ohne Lifecycle-Management** | Init- und Index-Schritte nicht dokumentierbar; kein Two-Gate; keine reproduzierbare, automatisierbare Einrichtung |
| **Install-Hook direkt in sync.py mit Opt-In** | Bricht Stdlib-only und side-effect-freies Design von sync.py (siehe Issue #255); würde sync für Anfänger zu komplex machen |
| **mcp-registry.yaml um `lifecycle:`-Block erweitern** | Semantischer Mismatch: mcp-registry ist deklarativ (Bestands-Verwaltung existierender Server), während Integrations-Lifecycle imperativ ist (Build- und Init-Schritte mit Seiteneffekten). Dadurch andere Approval-Policy nötig, Schema-Explosion (MCP 5 Felder vs. Integrations 10+), unnötige Komplexität für MCP-Maintainer |
| **Nichts tun / semble nur per README manuell** | Nicht skalierbar für >1 Integration; Reproduzierbarkeit leidet; Agent-Awareness nicht automatisierbar; jedes Projekt müsste manuell init-Schritte dokumentieren |

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
        maps_to:
          kind: arg
          target: "--content"
      top_k:
        type: integer
        default: 5
        maps_to:
          kind: arg
          target: "--top-k"
    capabilities: [code-search, semantic-retrieval]
    description: "Hybrid semantic + lexical code search (Model2Vec + BM25)"
    docs_url: "https://github.com/MinishLab/semble"
```

Wichtige Designentscheidungen zu diesem YAML:
- `options` + `maps_to` ist der Generalisierungs-Kern. Jede Integration deklariert Optionen + Ziel-Mapping selbst. Neue Tools = nur YAML, kein Python.
- `installer`-Feld ist PRO Integration (Designentscheidung), kein globaler Default.
- Two-Gate-Muster: `approved` im Meta-Repo (wie Skills) + `enabled` im Projekt.
- **`maps_to`-Schema v1 — erweitert für arg/env/config:** Aktuell wird `maps_to_arg` verwendet (vereinfachte Syntax für CLI-Argumente). Das volle v1-Schema unterstützt aber bereits drei Zieltypen:
  ```yaml
  maps_to:
    kind: arg|env|config      # arg: CLI-Argument | env: Umgebungsvariable | config: JSON-Konfiguration
    target: "--content"|"FOO_CONTENT"|"config.section"
  ```
  Begründung für direkte Schema-Erweiterung statt spätere Migration zu v2: Survey gegen realistische Kandidaten (ripgrep-mcp, llm-cli, sourcegraph-mcp) zeigt dass nicht alle Tools CLI-Args nutzen. Der Config-Support ist notwendig um eine breite Palette zukünftiger Tools zu unterstützen, ohne später ein Breaking Change durchzuführen. Die v1-Spezifikation deckt alle drei Fälle ab.

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
- `validate_options(integration_name, user_options, registry_options_schema)` — dynamische Validierung gegen Registry-Schema (Optionen werden über `maps_to` auf CLI/Env/Config gemappt)
- `build_mcp_entries(enabled_integrations)` — gibt MCP-Einträge zurück zum Merge durch mcp.py
- `build_tool_awareness(enabled_integrations)` — generiert Inhalte für rules/integrations.md
- `write_pending_marker(target_path, pending_integrations)` — schreibt Marker wenn Init noch aussteht; `init-integrations.py` löscht den Marker nach Completion (Symmetrie)

Rahmenbedingungen:
- Keine externen Dependencies außer Stdlib — AUSNAHME: **Integrations-Framework setzt PyYAML voraus.** Die `integrations-registry.yaml` nutzt verschachtelte Strukturen (z.B. `mcp.tools[]`, `options.*.items[]`) die ohne PyYAML nicht labar sind. 
- **PyYAML-Fallback (Issue #255):** Ohne PyYAML wird der `integrations:`-Block komplett übersprungen, bestehende MCP-Einträge in settings.json bleiben unverändert, und eine Warnung wird in sync.log geschrieben. Agent-Awareness wird deaktiviert.
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
4. Index-Command ausführen (Optionen über `maps_to` aufgelöst)
5. MCP-Healthcheck
6. Pending-Marker löschen

State wird in `.meta-config/.integrations-state.json` gespeichert. Dieser State-Marker hält `current_version` pro Integration, um Drift bei Versionsupgrades zu erkennen (siehe §10 „Upgrade-Pfad").

Funktioniert identisch in Meta- und Ziel-Repo. Aufruf aus Ziel-Repo: `python .agent-meta/scripts/init-integrations.py`

**Multi-Repo/Submodul-Pfade (bei Ziel-Repo als agent-meta-Submodul):**

| Datei | Ort bei Meta-Repo | Ort bei Ziel-Repo (als Submodul) |
|---|---|---|
| `integrations-registry.yaml` | `config/` | gelesen aus `.agent-meta/config/` (Submodul-Pfad) |
| `.integrations-state.json` | `.meta-config/` (falls Meta-Self-Test) | `.meta-config/` (Ziel-Repo) |
| Pending-Marker | `.meta-config/.integrations-pending.json` (provider-agnostisch) | `.meta-config/.integrations-pending.json` (Ziel-Repo) |

---

## 9. Agent-Awareness (provider-agnostisch)

- sync.py generiert `rules/integrations.md` (analog zur MCP-Rule) — listet aktive Tools + Hints
- **Erzeugungsmechanismus:** Integrations-Rule wird **programmatisch per Codegen** in `scripts/lib/integrations.py` (`build_tool_awareness()`) erzeugt, NICHT aus Template-Datei (Unterschied zu Skills).
- sync.py rendert diese generierte Rule für jeden in `platforms:` konfigurierten Provider (z.B. `.claude/rules/integrations.md`, `.gemini/rules/integrations.md`, etc.)
- Generischer Inhalt nennt nie Tool-Namen oder Provider — nur abstrakte Muster wie „Nutze verfügbare Integrations-Tools vor manuellen Fallbacks"
- Beispiel-Injektion in die generierte Rule: „Wenn semantic-search-Tool verfügbar: semantische Suche vor grep für Konzept-Lookups"

---

## 10. End-to-End-Flow (Ziel-Repo, semble.enabled: true)

1. **sync.py ausführen** → schreibt MCP-Eintrag (mit `disabled: true` da Pending-Marker existiert) in settings.json + generiert rules/integrations.md + setzt pending-marker (`.meta-config/.integrations-pending.json`)
2. **Hinweis-Ausgabe:** „1 Integration ausstehend: `python .agent-meta/scripts/init-integrations.py`"
3. **init-integrations.py ausführen:**
   - Paket installieren (via konfiguriertem Installer, z.B. `uv tool install semble==0.3.4`)
   - Init-Command einmalig ausführen: `semble install`
   - Index-Command ausführen: `semble index .`
   - MCP-Healthcheck durchführen
   - MCP-Eintrag auf `disabled: false` setzen (oder entfernen) + State aktualisieren
   - Pending-Marker löschen
4. **Agent-Session starten** → `mcp__semble__search` verfügbar, vollumfänglich funktional

**State-Drift-Handling:** Solange Pending-Marker existiert, ist der MCP-Eintrag in settings.json mit `disabled: true` markiert — das ist der Gate, nicht nur Information. Nur `init-integrations.py` darf nach erfolgreicher Provisioning auf `disabled: false` setzen (oder das Feld entfernen). Dies löst das Race-Condition-Problem zwischen sync.py (schreibt MCP-Eintrag) und init-integrations.py (installiert Paket).

---

## 10b. Disable-Pfad (Integration entfernen)

Zwei Szenarien unterscheiden sich:

**Szenario 1: Hard-Remove (User deaktiviert Integration via `enabled: false`)**

Wenn `enabled: true → false` in `.meta-config/project.yaml`:

1. **sync.py ausführen** → **entfernt MCP-Eintrag komplett aus settings.json** + entfernt generierte Sections aus rules/integrations.md
2. **Optional: init-integrations.py --remove <name>** → führt optionalen `uv tool uninstall semble` / `pip uninstall semble` aus (mit Bestätigung) + räumt `.meta-config/.integrations-state.json` auf
3. **Hinweis:** Globale MCP-Registrierung (falls `semble install` ausgeführt worden ist) wird NICHT automatisch rückgängig gemacht. User muss manuell `semble uninstall` aufrufen falls nötig (ist Integration-spezifisch).

**Szenario 2: Soft-Disable (Pending-Zustand, Installation noch nicht abgeschlossen)**

Solange Pending-Marker (`.meta-config/.integrations-pending.json`) existiert: MCP-Eintrag in settings.json mit `disabled: true` geschrieben → das ist der Gate, der verhindert dass der MCP-Server geladen wird bevor init-integrations.py erfolgreich läuft.

---

## 10c. Upgrade-Pfad (Versionsbump)

Wenn `package: "semble==0.3.4" → "0.4.0"` in `config/integrations-registry.yaml`:

1. **Healthcheck** (in init-integrations.py oder bei sync.py-Validierung): Vergleicht installierte Version (via `semble --version`) mit Registry-Version
2. **Bei Drift** (installiert: 0.3.4, Registry: 0.4.0): Force-Reinstall triggern (analog zu `npm audit fix`)
3. **Re-Index-Bedarf:** Tools deklarieren selbst wann ein Re-Index nötig ist via `lifecycle.reindex_on`-Feld in der Registry:
   ```yaml
   lifecycle:
     reindex_on: [major, schema_change]
   ```
   NICHT jeder Version-Bump erzwingt einen Re-Index — das wird von der Integration selbst spezifiziert. Bei Major-Bump oder Schema-Change wird `semble index` automatisch erneut ausgeführt
4. **Mechanik:** `init-integrations.py --check` oder `--reindex` erkennt Version-Drift und bietet Upgrade-Workflow an

---

## 11. Neu vs. Wiederverwendet

| Artefakt | Status | Anmerkung |
|----------|--------|-----------|
| `config/integrations-registry.yaml` | NEU | Neue Meta-Registry |
| `scripts/lib/integrations.py` | NEU | Neues Modul mit `build_tool_awareness()` Codegen |
| `scripts/init-integrations.py` | NEU | Neuer Entry-Point mit Healthcheck + Upgrade-Erkennung |
| Integrations-Rule (Codegen) | NEU | **Programmatisch erzeugt in `integrations.py`, NICHT aus Template** |
| Schema-Block in `project-config.schema.json` | NEU | Erweiterung des bestehenden Schemas |
| Two-Gate-Muster (approved + enabled) | WIEDERVERWENDET | Wie bei Skills |
| `generate_mcp_artifacts()` aus mcp.py | WIEDERVERWENDET | MCP-Einträge werden gemergt |
| `build_variables()` Toggle-Mechanik | WIEDERVERWENDET | Analog ANALYSIS_ENABLED |
| settings.json-Writer | WIEDERVERWENDET | Bestehende Infrastruktur |
| PyYAML-Fallback (Issue #255) | WIEDERVERWENDET | Graceful degradation (nur für flache Struktur; verschachtelte Registry setzt PyYAML voraus) |
| gitignore-Management | WIEDERVERWENDET | `.integrations-state.json` + `.integrations-pending.json` hinzufügen |

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
- Multi-IDE-Support (Claude Code, Gemini, VS Code Extensions)
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

## 14. Implementierungsreihenfolge

Umsetzung folgt in separater Session (User-Entscheidung).

1. `config/integrations-registry.yaml` + Schema-Block anlegen
2. `scripts/lib/integrations.py` implementieren (mit `build_tool_awareness()` Codegen)
3. `mcp.py`-Merge integrieren
4. `scripts/init-integrations.py` implementieren (mit Healthcheck + Upgrade-Erkennung)
5. Generierte Integrations-Rule registrieren (sync.py, Codegen-Output)
6. semble als erste Instanz testen: erst in Meta-Repo, dann in Ziel-Repo

---

## 15. Offene Punkte

**ENTSCHIEDEN (nicht mehr offen):**
- ✅ uv vs. pip Fallback: Automatischer Fallback auf pip bei fehlender uv (Warnung + Log)
- ✅ maps_to-Schema: v1 unterstützt bereits arg|env|config in direkter Syntax (§4)
- ✅ Validierungs-Zeitpunkt: Beide (sync.py validiert Registry, init-integrations.py validiert User-Optionen gegen Schema)
- ✅ uv-Modus: `uv tool install` (globales Tool, isoliert zwischen Repos via venv, PATH-clean)
- ✅ Pending-Marker: `.meta-config/.integrations-pending.json` (provider-agnostisch, §8)
- ✅ State-Drift sync↔init: MCP-Eintrag mit `disabled: true` bis init erfolgreich (§10)
- ✅ Disable-Pfad: `enabled: true → false` in project.yaml triggert Entfernung (§10b)
- ✅ Upgrade-Pfad: Healthcheck + Force-Reinstall bei Version-Drift, Re-Index bei Major-Bump (§10c)

**NOCH OFFEN:**
- **approved-Flag-Policy für Forks:** Wer ist zuständiger Meta-Maintainer wenn agent-meta geforkt wird? Wie wird approval delegiert?
