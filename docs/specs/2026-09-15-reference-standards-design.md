---
spec-id: SPEC-REFERENCE-STANDARDS-2026-09-15
title: Framework-Support für das Agent-Frontmatter-Feld `reference_standards`
status: APPROVED
source-analysis: docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md
related-issues: "#787, #788, #789, #790, #791, #793, #795"
related-spec: SPEC-CONTEXT-FILE-MODES-2026-09-13
---

# Framework-Support für `reference_standards` — Spec

> Status: **APPROVED (2026-09-15)** — approved by the user on **2026-09-15**,
> recorded by the `concept-reviewer` role; the recommended defaults were accepted
> unchanged (see the Revision table and the approval record below). This document
> is a specification only: it defines Interface Contracts and Acceptance Criteria
> and contains **no** implementation and no plan.
> The approval marker is set here and in the frontmatter `status:` field — never
> by the authoring role, only by `concept-reviewer` after review (Approval-Gate,
> Master-Rule `spec-plan-workflow`). Without `Status: APPROVED` neither a plan
> nor code may be produced.
> Trace-Anker: `spec-id: SPEC-REFERENCE-STANDARDS-2026-09-15`.
> Quelle (Analyse/Plan): `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md`,
> WP2/D2 — „`reference_standards` ist optional, parsebar und wird im
> Consistency-Lauf geprüft“ (Zeilen 338–343, 422–430).
> Benachbarte Spec (Konventionen, nicht Supersession): `SPEC-CONTEXT-FILE-MODES-2026-09-13`
> — dieselben Seams (Frontmatter-Render, Per-Provider-Transformation,
> Consistency-Registrierung) werden benutzt; deren Tier-/Topologie-Vokabular
> bleibt unangetastet.
>
> Provider-agnostisch ist Pflicht: alle Provider-Unterschiede werden über
> Config-Keys/Capability-Flags ausgedrückt (`config/ai-providers.yaml`,
> `.meta-config/project.yaml → provider-options`). Kein
> `if provider == "<Name>"`, kein Provider-Namens-Literal in neuem oder
> geändertem Code (Regel: `rules/2-platform/agent-meta-provider-agnostic.md`,
> Guard: `tests/test_provider_agnostic_dispatch.py`).

### Verifikations-Legende

| Marker | Bedeutung |
|---|---|
| **VERIFIED** | am Revision dieses Specs im Repo gelesen (Datei:Zeile unten genannt) |
| **VERIFIED-RESEARCH** | aus Repo-Doku/Issues belegt, nicht in diesem Lauf ausgeführt |
| **HYPOTHESIS** | Annahme, vor Implementierung zu prüfen |

### Klassifikation (Master-Rule `spec-plan-workflow`)

**M / Bounded** — geplanter Produktions-Footprint **6 Dateien**
(`scripts/lib/frontmatter.py` [modified], `scripts/lib/providers.py` [modified],
`scripts/lib/provider_transform.py` [modified], `scripts/lib/consistency/reference_standards.py`
[new], `scripts/consistency-check.py` [modified], `config/project-config.schema.json`
[modified]); dazu kommen Doku (2) und Tests (4) als Folgeartefakte, die nicht in
die Größenheuristik zählen. Begründung gegen **Architectural**: keine öffentliche
API/Contract-Grenze wird neu gezogen (der Strip-Policy-Kanal
`frontmatter-strip-fields` existiert bereits, VERIFIED), kein Datenmodell wird
migriert (die Schema-Ergänzung ist additiv/optional), und es wird keine
Subsystem-Grenze neu überschritten — genutzt werden zwei **bestehende** Seams
(Frontmatter-Render-Pipeline, Consistency-Registrierung). Die qualitative
Zusatzregel für Architectural greift damit nicht. Sollte der `concept-reviewer`
das anders bewerten, ist die Eskalation an `concept-architect` der dokumentierte
Fallback (R8).

### Revision — incorporated review findings

| Finding | Change |
|---|---|
| Erstfassung | Basisversion. Interface Contracts IC-01 … IC-06, Acceptance Criteria AC-01 … AC-18, Offene Fragen OQ-1 … OQ-11, Risiken R1 … R9. Weitere Zeilen werden auf `CHANGES_REQUESTED` iterationsweise ergänzt (max. 3). |
| APPROVED (2026-09-15) | **Approved by the user on 2026-09-15, recorded by the `concept-reviewer` role.** All recommended defaults accepted unchanged, incl. OQ-3 (quiet/silent strip: `reference_standards` appears neither as a YAML key nor in the `agent-meta-provenance` comment), consistent with the user's explicit policy *"strip `reference_standards` from every provider by default, per-provider configurable"* (opt-in keep via `frontmatter-keep-fields`). Frontmatter `status:` set to `APPROVED`. Factual review corrections (verified against code; no IC/AC semantics changed): **(a)** Opencode reclassified — `opencode-native` is a patch over `_update_frontmatter_dict` with a fixed `removes` list (`provider_transform.py:517-631`, `:603-619`; `frontmatter.py:105-114`), **not** a whitelist rebuild, so it passes `reference_standards` through today; only Codex drops unknown fields ⇒ leak surface is 8/9 providers (Problem 3, IC-03 "Reichweite", Datenfluss table, R1, AC-02 note corrected). **(b)** IC-03 now states explicitly that the two existing strip channels are combined by **union** (previously project `or` provider). **(c)** Check scope corrected to `agents/1-generic/*.md` + `agents/2-platform/*.md` (`collect_agent_files`, `consistency-check.py:107-120`). **(d)** standalone `...` elision in the IC-02 snippet replaced (avoids `spec_plan_no_placeholder`). **(e)** `_TOUCHED_MODULES` line reference `:34` → `:27`. |

---

## Problem

Das Feld `reference_standards` (Liste von Strings, Format
`"<STANDARD>[@<version>][#<section>]"`) wird von den offenen PRs #787/#788/#789/
#790/#791/#793/#795 in Agent-Templates eingeführt (HYPOTHESIS: PR-Inhalte wurden
nicht eingesehen; im Repo existiert der Feldname bislang **nur** in Plan-Doku,
VERIFIED via `grep reference_standards`). Das Framework kennt das Feld nicht:

1. **Kein Parser-/Recognition-Punkt.** Es gibt keine typisierte Zugriffsfläche
   für das Feld. `scripts/lib/frontmatter.py` parst Frontmatter generisch
   (beliebige Keys über `_parse_frontmatter_yaml`), es existiert **keine**
   Feld-Whitelist, die unbekannte Keys ablehnt (VERIFIED: keine
   „known fields“-Konstante in `frontmatter.py` bzw.
   `consistency/frontmatter.py`). „Erkennen“ heißt im Framework daher: explizite
   Konstante + Accessor + Dokumentation, nicht Parser-Umbau.
2. **Kein Consistency-Check.** `scripts/lib/consistency/frontmatter.py`
   validiert `tools`, `version`, `workflow_tier`, `based-on` usw., aber kein
   `reference_standards` (VERIFIED). Damit sind Strukturfehler (Skalar statt
   Liste, leere Einträge, falsche Token-Reihenfolge) im Repo unbemerkt — der Plan
   WP2/AC1 fordert „parsebar und im Consistency-Lauf geprüft“.
3. **Kein definiertes Provider-Verhalten (der eigentliche Defekt).**
   `scripts/lib/provider_transform.py:385-388` entfernt nur Keys aus
   `provider-options.<provider>.frontmatter-strip-fields` (Projekt-Config) bzw.
   `config/ai-providers.yaml[provider]['frontmatter_strip_fields']`; **beide sind
   für alle Provider unset** (VERIFIED: kein `frontmatter_strip_fields` in
   `config/ai-providers.yaml`, kein Eintrag in `.meta-config/project.yaml`).
   Konsequenz: neun registrierte Provider (`Claude`, `Gemini`, `Opencode`,
   `Continue`, `Copilot`, `Mammouth`, `Codex`, `ZCode`, `KimiCode`; VERIFIED in
   `config/ai-providers.yaml`) verhalten sich unterschiedlich:
   - **8 Provider patchen** die Frontmatter (`Claude` `:92-97`, `Gemini`
     `:159-162`, `Opencode` `:235-255`, `Continue` `:305-315`, `Copilot`
     `:358-368`, `Mammouth` `:421-426`, `ZCode` `:533-536`, `KimiCode`
     `:583-586`) → unbekannte Felder werden **durchgereicht** (wie bisher
     `version`/`prompt_mode`/`hint`).
   - **1 Provider baut neu auf** (`Codex` `frontmatter-mechanism: codex-toml`
     `:487` → `scripts/lib/agent_toml.py::build_agent_toml_document`) →
     unbekannte Felder fallen weg (das TOML-Dokument wird ausschließlich aus
     `name`/`description`/`model`/`extra_fields` + Body neu gebaut).
   - **`Opencode` ist kein Whitelist-Rebuild** (Korrektur, VERIFIED):
     `frontmatter-mechanism: opencode-native` `:236` →
     `_transform_frontmatter_for_opencode` (`provider_transform.py:517-631`) ist
     ein **Patch** über `_update_frontmatter_dict` mit einer **festen**
     `removes`-Liste (`:603-617`) plus `strip_fields` (`:618-619`); Keys außerhalb
     dieser Listen bleiben erhalten (`frontmatter.py:105-114`).
     `reference_standards` wird dort heute also ebenfalls **durchgereicht**.
   Ohne Policy landet das Feld damit in **8** Provider-Surfaces (potenziell mit
   strikten Provider-Schemas kollidierend, Muster #505) und nur in `Codex`
   nicht — ein nicht-deterministisches Framework-Verhalten.

**Zusatzbefund (Provenance-Leak).** Das Strippen ist heute **nicht lautlos**:
`build_frontmatter` (`frontmatter.py:230-238`) und
`_transform_frontmatter_for_opencode` (`provider_transform.py:554-561`) schreiben
die Werte gestrippter Keys als `<!-- agent-meta-provenance: key=value -->` in die
generierte Datei. Ein naives „Feld in `strip_fields` aufnehmen“ würde den Feldnamen
(dann ohne YAML-Key, aber im Kommentar) in **jede** generierte Datei schreiben und
damit AC „kein `reference_standards` in generierten Agenten“ verfehlen.

**Auftrag 2 (separater, kleiner Befund).** Für das Eval-Framework existiert die
Regel „nur die YAML-Kataloge unter `tests/routing-llm-eval/` sind handgepflegt,
`promptfooconfig.generated.yaml` wird nur von `scripts/gen_promptfoo_config.py`
erzeugt“ (VERIFIED: `tests/routing-llm-eval/README.md:26-32`, Script-Header
`gen_promptfoo_config.py:2-19`). Offen war, ob ein Gate diese Regel schützt.

## Ziel

1. **Recognition:** `reference_standards` ist ein **legitimes, optionales**
   Template-Frontmatter-Feld — typisiert lesbar über eine zentrale Konstante +
   Accessor, ohne das neutrale Frontmatter-Layer um Feld-Policy zu belasten
   (IC-01).
2. **Struktur-Validierung:** ein neuer Consistency-Check validiert
   „Liste von Strings“ und das MVP-Format `"<STANDARD>[@<version>][#<section>]"`
   (Name nicht leer; Version/Section optional) und meldet **nur** bei
   Struktur-/Formatfehlern (IC-02).
3. **Deterministische Provider-Policy:** Das Feld wird per Default aus **jeder**
   generierten Provider-Agent-Frontmatter entfernt — über den **bestehenden**
   `strip_fields`-Kanal (IC-03), ohne `if provider ==` und ohne die
   `frontmatter-mechanism`-Pfade (`opencode-native`, `codex-toml`) zu duplizieren; die Policy ist
   **per Provider konfigurierbar** und erlaubt ein späteres Opt-in „keep“
   (IC-03/IC-05) — ohne Code-Änderung.
4. **Kein Leak:** Das gestrippte Feld darf weder als YAML-Key noch über den
   `agent-meta-provenance`-Kommentar in generierten Agenten auftauchen; das
   bestehende Provenance-Verhalten anderer Felder bleibt **byte-identisch**
   (IC-04).
5. **Auftrag 2:** Die Eval-Katalog-Regel ist dokumentiert und – soweit heute
   vorhanden – gegated; die verifizierte Lücke (`catalog.generated.yaml`) erhält
   einen minimalen, testbaren Freshness-Schutz (IC-06, AC-15 … AC-18).

## Nicht-Ziele

- **Keine Umsetzung der fachlichen Nutzung des Feldes.** Was eine Rolle mit ihren
  Referenzstandards tun *soll* (Prompt-Injektion, Review-Evidenz, Coverage-Reports)
  ist **nicht** Teil dieser Spec. Es wird nur Erkennung, Validierung und
  Provider-Transport-Policy spezifiziert.
- **Keine Änderung am Verhalten von `hint`, `version`, `prompt_mode`,
  `generated-from`, `based-on`.** Deren Strip-/Provenance-/Render-Semantik bleibt
  unangetastet (Insbesondere bleibt `provider-options.<P>.frontmatter-strip-fields`
  für diese Felder reines Opt-in, `docs/providers/multi-provider.md:586`).
- **Keine Eval-Case-Inhalte.** Auftrag 2 ändert **keine** Testfälle, keine
  Erwartungswerte, keine Katalogeinträge und keine Prompt-/Provider-Wrapper. Es
  geht ausschließlich um die Regel „hand-maintained vs. generiert“ und deren Gate.
- **Keine Namens-Registry-Validierung.** MVP prüft Struktur/Format, nicht, ob
  `"arc42"` ein „bekannter“ Standard ist (OQ-5).
- **Keine Änderung an `config/role-defaults.yaml`** (Plan WP2: neue Felder gehören
  in Template-Frontmatter, nicht in `role-defaults`).
- **Keine Migration bestehender Templates.** Der Backfill ist opportunistisch
  (Plan, Zeile 341) und liegt bei WP2/den Rollen-PRs, nicht in dieser Spec.
- **Kein neuer CI-Workflow.** Auftrag 2 nutzt die vorhandenen Gates
  (`orchestration-test.yml`, `validate.yml`) — OQ-10.
- **Keine Formatter-/Pre-Commit-Erweiterung**, kein Admin-UI-Feld (HYPOTHESIS:
  Admin-UI kennt Frontmatter-Felder nur anzeigend; nicht Teil des Scopes).

## Interface Contracts

Konvention wie in `docs/specs/2026-09-13-*`: `Datei::Symbol — Signatur`, danach
Fehlerpfade. Alle Zeilenangaben sind am Revision dieses Specs verifiziert.

### IC-01 — `scripts/lib/frontmatter.py` :: Recognition & Parse (neutral)

```python
REFERENCE_STANDARDS_FIELD: str = "reference_standards"

def parse_reference_standards(content: str) -> object | None:
    """Raw YAML value of the `reference_standards` field, or None when absent.

    No validation: structure/format checks live in
    `scripts/lib/consistency/reference_standards.py` (IC-02). Absent field →
    None. PyYAML unavailable → falls back to `extract_frontmatter_field`
    (string/dict repr) so the accessor never raises.
    """
```

- Verhalten: liest **nur** (`_parse_frontmatter_yaml(content).get(REFERENCE_STANDARDS_FIELD)`);
  verändert keinen Inhalt und trifft keine Policy-Entscheidung.
- Fehlerpfade: kein Frontmatter / kein PyYAML / YAML-Fehler → `None`
  (analog `_parse_frontmatter_yaml`-Fallback); niemals Exception.
- Das Feld wird **nicht** zu einer Whitelist hinzugefügt, weil es keine gibt
  (Problem 1); die „Legitimität“ wird über Konstante, Accessor und Doku
  (IC-05) hergestellt.
- Rückwärtskompatibilität: rein additiv; bestehende Parser-Signaturen unverändert.

### IC-02 — `scripts/lib/consistency/reference_standards.py` (neu) + Registrierung

```python
# scripts/lib/consistency/reference_standards.py
from .report import Finding, Severity

# MVP-Format: <STANDARD>[@<version>][#<section>]
#   STANDARD: nicht leer, kein führendes/abschließendes Whitespace,
#             keine '@'/'#'-Zeichen (Delimiter), interne Leerzeichen erlaubt
#             ("C4 model", "arc42", "IEEE 1012").
#   @version / #section: optional, jeweils nicht leer, ohne Whitespace,
#             ohne weitere Delimiter, Reihenfolge fix (@ vor #).
REFERENCE_STANDARDS_FORMAT_HINT: str = "<STANDARD>[@<version>][#<section>]"

def parse_reference_standards_entry(entry: str) -> tuple[str, str | None, str | None] | None:
    """('arc42', None, None) | ('ISTQB', '4.0', None) | ('IEEE 1012', '2016', '7')
    → None when the entry does not match the MVP grammar."""

def check_reference_standards(
    path: Path,
    content: str,
    agent_meta_root: Path,
    changed_files: set[str] | None,
) -> list[Finding]:
    """Findings for the `reference_standards` field of one agent template."""
```

Signatur bewusst identisch zu
`consistency/frontmatter.py::check_agent_frontmatter` (`:18-19`), inkl.
`changed_files` (heute ungenutzt, aber für zukünftige „changed-only“-Regeln und
für die identische Aufrufkonvention). `changed_files` darf `None` sein.

Findings-Matrix (Feld **optional**: abwesend → `[]`):

| Bedingung | Severity | `check`-ID | Vorschlagstext (suggestion) |
|---|---|---|---|
| Wert ist keine Liste (Skalar/Mapping) | `ERROR` | `reference-standards.not-list` | `Use a YAML list, e.g. ["Diátaxis", "C4 model"]` |
| Liste ist leer | `WARNING` | `reference-standards.empty` | Feld entfernen oder Einträge ergänzen |
| Eintrag kein String | `ERROR` | `reference-standards.entry-not-string` | `Quote the entry: "arc42@1.0"` |
| Eintrag `""` oder nur Whitespace | `ERROR` | `reference-standards.entry-empty` | `Remove the empty entry` |
| Eintrag verletzt die MVP-Grammatik | `ERROR` | `reference-standards.entry-format` | Format-Hint + betroffener Eintrag |
| Doppelter Eintrag (nach Trim, case-sensitiv) | `WARNING` | `reference-standards.duplicate` | `Remove the duplicate` |
| Unbekannter Standard-Name | — (kein Finding) | — | MVP prüft keine Registry (OQ-5) |

Registrierung (identisch zu allen bestehenden Modulen):

```python
# scripts/consistency-check.py
from lib.consistency.reference_standards import check_reference_standards   # bei :57
# ... (übrige Imports des Moduls unverändert)
    for path in agent_files:
        content = _read(path)
        if content is None:
            continue
        findings += check_agent_frontmatter(path, content, root, changed_files)
        findings += check_reference_standards(path, content, root, changed_files)   # bei :172
        findings += check_placeholders(path, content, root, project_vars)
```

- Fehlerpfade: fehlendes Frontmatter / YAML-Fehler → `[]` (der
  Frontmatter-Check meldet das bereits als `frontmatter.missing`); kein
  Doppel-ERROR. `path` wird wie bei `frontmatter.py` über `_rel(...)` relativiert.
- Exit-Code-Vertrag unverändert: `ERROR` → rc 1, nur `WARNING` → rc 0
  (bzw. rc 1 unter `--strict`), siehe `consistency/report.py::print_report`
  (`:44-75`).
- `scripts/lib/consistency/__init__.py` bleibt unverändert (exportiert nur
  `Finding`/`Severity`, `:1-5`).

### IC-03 — Provider-agnostische Strip-Policy (Resolver + Aufrufstelle)

**Entscheidung (Mechanismus):** Die Policy wird als **ein** Resolver mit
Kanal-Vereinigung realisiert. Globaler Default = strip, per-Provider
überschreibbar in beide Richtungen (strip ergänzen, keep erzwingen) — alles über
Config-Keys, kein Provider-Namens-Branch.

```python
# scripts/lib/providers.py  (Config-Resolver-Modul; schon im
# provider-agnostic AST-Guard, tests/test_provider_agnostic_dispatch.py:27)

FRONTMATTER_STRIP_DEFAULTS: tuple[str, ...] = ("reference_standards",)
# Bewusst ein Modul-Konstante, kein ai-providers-Top-Level-Key:
# load_providers_config() gibt `data.get("providers", data)` zurück
# (providers.py:119) — ein Top-Level-Key würde dort verworfen.

def resolve_frontmatter_strip_fields(
    provider: str,
    config: dict,
    provider_config: dict,
) -> list[str]:
    """Effective frontmatter strip set for `provider` (provider-agnostic).

    strip = FRONTMATTER_STRIP_DEFAULTS
          ∪ config["provider-options"][provider]["frontmatter-strip-fields"]
          ∪ provider_config[provider]["frontmatter_strip_fields"]
    keep  = config["provider-options"][provider]["frontmatter-keep-fields"]
          ∪ provider_config[provider]["frontmatter_keep_fields"]
    result = stable-ordered (strip \ keep)
    """
```

Aufrufstelle (ersetzt `provider_transform.py:385-388`):

```python
# scripts/lib/provider_transform.py::transform_agent_content_for_provider
_strip_fields = resolve_frontmatter_strip_fields(provider, config, provider_config)
```

- **Kanal-Kompatibilität:** `provider-options.<P>.frontmatter-strip-fields`
  (Projekt, kebab-case) und `frontmatter_strip_fields` (ai-providers.yaml,
  snake_case) behalten ihre bisherigen Namen und Payloads (VERIFIED
  `provider_transform.py:385-388`, Doku `docs/providers/multi-provider.md:576-586`).
  **Präzisierung der Kombinationssemantik:** heute gilt `project or provider`
  (eine gesetzte Projekt-Liste **ersetzt** die ai-providers-Liste, `:385-388`);
  der Resolver führt beide Kanäle mit den Defaults zu einer **Union** zusammen
  (siehe Code-Block oben: `∪`). Im Repo sind beide Kanäle unset, das
  Ist-Verhalten ändert sich daher nicht; für Projekte, die **beide** Kanäle
  setzen, gilt künftig Union statt Override (bewusste Vereinheitlichung).
- **Neue Keep-Kanäle** (heute überall unset, also reines Default-Strip):
  `provider-options.<P>.frontmatter-keep-fields` und
  `providers.<P>.frontmatter_keep_fields`. **keep schlägt strip.** Ein späteres
  Opt-in „Feld behalten“ ist damit eine reine Config-Änderung
  (`frontmatter-keep-fields: [reference_standards]`) — kein Code-Change.
- **Fehlerpfade (fail-safe = strip bleibt aktiv):** fehlender/`None`/Nicht-Dict
  `provider-options` oder Provider-Eintrag → diese Quelle trägt nichts bei (kein
  `KeyError`, Muster `provider_config.get(provider, {})` bzw.
  `resolve_provider_options`, `providers.py:519-532`); nicht-Listen-Werte
  (String/Skalar/Dict) in einem der vier Keys → als leer behandelt **plus genau
  eine `log.warning` je `(provider, key)`**, dedupliziert; unbekannte Keys in der
  Liste werden unverändert weitergereicht (`_remove_frontmatter_fields` ist
  ein No-op für nicht vorhandene Keys). Kein Abbruch, keine Exception.
- **Reichweite:** Der Resolver ersetzt die Inline-Expression für **alle** 9
  Provider. Bei `Codex` (`codex-toml`, echter Whitelist-Rebuild) ist der Effekt
  ohnehin „Feld fällt weg“; bei `Opencode` (`opencode-native`) wird das Feld
  heute durchgereicht und erst durch den Resolver-Wert in `strip_fields`
  wirksam (`removes.extend(strip_fields)`, `provider_transform.py:618-619`). Der
  Resolver macht den Effekt damit **explizit und testbar** statt zufällig
  (AC-02) und liefert den Mechanismus für den Keep-Fall (dann müsste der
  Feld-Whitelist-Builder es aktiv übernehmen — heute **Nicht-Ziel**, OQ-3-folgend).
- Bestehende Strip-Listen (z. B. `Copilot` `:359-367`, `Mammouth` `:426`,
  `KimiCode` `:586`, `ZCode` `:536`) bleiben wirksam; `strip-fields` im
  `agent-transform`-Block (`provider_transform.py:335-337`) ist und bleibt ein
  **anderer** Kanal (Runtime-Felder) und wird nicht angefasst.
- Provider-agnostisch: keine Provider-Namens-Literale; der Guard
  `tests/test_provider_agnostic_dispatch.py` wird um `provider_transform` und
  `consistency/reference_standards` erweitert (AC-09).

### IC-04 — No-Leak-Garantie in beiden Frontmatter-Buildern

```python
# scripts/lib/frontmatter.py
FRONTMATTER_QUIET_STRIP_FIELDS: frozenset[str] = frozenset({REFERENCE_STANDARDS_FIELD})

def build_frontmatter(
    content: str, name: str, description: str,
    generated_from: str | None = None,
    strip_fields: list[str] | None = None,
    quiet_fields: frozenset[str] | None = None,   # NEU, additiv
) -> str: ...
```

- Semantik: `quiet_fields` (Default `FRONTMATTER_QUIET_STRIP_FIELDS`) werden
  gestrippt, aber **nicht** in den `<!-- agent-meta-provenance: ... -->`-Kommentar
  aufgenommen (`frontmatter.py:230-238`). Begründung: die Werte bleiben in der
  Template-Quelle auffindbar; es gibt keinen Konsumenten in generierten Dateien
  (anders als `version`-Bump-Enforcement / `prompt_mode`), und die Policy-Absicht
  ist ein sauberes Provider-Frontmatter.
- Symmetrisch in `_transform_frontmatter_for_opencode`
  (`provider_transform.py:554-561`): dieselbe Quiet-Menge beim Aufbau des
  Provenance-Kommentars anwenden (`strip_fields` kann dort weiterhin
  `reference_standards` enthalten — `removes.extend(strip_fields)` `:618-619`).
- `Codex` (`agent_toml.py::build_agent_toml_document`) übernimmt nur
  `version`/`generated-from` als Header-Kommentare (`:66-77`) — es braucht keine
  Änderung, wird aber vom Regressionstest erfasst (AC-02).
- Fehlerpfade: `quiet_fields=None` → Default; unbekannte Namen in `quiet_fields`
  sind No-ops; Übergabe falschen Typs (z. B. Liste) wird als Menge interpretiert
  bzw. ignoriert — keine Exception (fail-safe: dann wird der reguläre
  Provenance-Pfad benutzt, AC-06 pinnt das).
- **Rückwärtskompatibilität (kritisch):** Ohne neuen Parameter ist das Verhalten
  von `build_frontmatter` und `_transform_frontmatter_for_opencode`
  **byte-identisch** zu heute; die bestehenden Tests
  `tests/test_agents_frontmatter.py:51-89,107-186` bleiben unverändert grün.

### IC-05 — Config-Oberfläche & Doku

```jsonc
// config/project-config.schema.json, Block "provider-options" (:731-...),
// bestehendes Muster: properties pro Provider + "additionalProperties": false
"frontmatter-keep-fields": {
  "type": "array",
  "items": { "type": "string" },
  "description": "Frontmatter keys that must NOT be stripped for this provider, even when they appear in the global defaults or in frontmatter-strip-fields. Wins over strip. Default: empty."
}
```

- **Pflicht**, weil jeder Provider-Eintrag `additionalProperties: false` hat und
  `Claude`/`Gemini` heute `"properties": {}` (VERIFIED `:735-746`) — ohne
  Schema-Ergänzung würde ein gültiger Keep-Key die Projekt-Config-Validierung
  brechen (R6). Rein additiv/optional.
- Gleicher Key in allen Provider-Sub-Blöcken, die `provider-options` heute
  modelliert (Provider-agnostisch, kein Provider-Sonderfall).
- Dokumentation: `docs/providers/multi-provider.md` (Abschnitt um `:572-586`)
  bekommt den neuen Absatz „`reference_standards` wird per Default gestrippt;
  Opt-in behalten via `frontmatter-keep-fields`; Provenance bleibt für
  `version`/`prompt_mode`/`generated-from` unverändert“ — die bestehende Aussage
  „Default … reines Opt-in“ (`:586`) wird auf den Geltungsbereich der
  Bookkeeping-Felder eingegrenzt.
- Template-Feld-Doku: `conventions`-Skill (`.claude/skills/conventions/SKILL.md`,
  VERIFIED vorhanden; dort `:43` listet die Frontmatter-Felder) um
  `reference_standards` + MVP-Format ergänzen. HYPOTHESIS: dass weitere
  Provider-Kopien des Skills existieren, die denselben Satz brauchen — beim
  Implementieren prüfen (OQ-8).

### IC-06 — Auftrag 2: Eval-Katalog-Regel + Freshness-Gate

```python
# scripts/gen_promptfoo_config.py (bestehend, VERIFIED)
def main(argv: list[str]) -> int:        # --check → rc 1 bei Drift (:86-102)
```

```python
# tests/test_agent_eval_framework.py (bestehend, VERIFIED)
def test_generated_promptfoo_config_is_fresh_and_valid() -> None:   # :113-125
    # ruft `gen_promptfoo_config.py --check` als Subprozess
    # + prüft Provider/Tests-Anzahl + W4 (kein {{prompt}})
```

- **Gate-Status VERIFIED:** `--check` existiert (`gen_promptfoo_config.py:87,93-99`)
  und wird von `tests/test_agent_eval_framework.py::test_generated_promptfoo_config_is_fresh_and_valid`
  als Subprozess ausgeführt; dieser Test läuft in CI über
  `.github/workflows/orchestration-test.yml:48` (`python -m pytest tests/ -q`),
  getriggert auf `pull_request` mit `paths: tests/**`, `scripts/**` u. a.
  (`:17-25`). Für `promptfooconfig.generated.yaml` ist die Regel also **bereits**
  gegated.
- **Verifizierte Lücke:** Für `tests/routing-llm-eval/catalog.generated.yaml`
  gibt es **keinen** Freshness-Test — kein Test im Repo ruft
  `scripts/gen_routing_llm_eval_catalog.py` auf (VERIFIED:
  `grep gen_routing_llm_eval_catalog tests/` → nur Doku-Treffer), obwohl der
  Script-Header den CI-Freshness-Check als Zweck nennt (`:18-21`). Das Script hat
  heute nur `--project-config`/`--out` (`:173-183`), kein `--check`.
- **Minimaler Schutz (Vorschlag, verbindlich als AC-17):** ein Freshness-Test im
  bestehenden Testmodul, der `gen_routing_llm_eval_catalog.py --out <tmp>` gegen
  die committete Datei byte-vergleicht (kein neues CI-File, keine
  Katalog-Inhaltsänderung). Alternative, gleichwertige Variante: `--check`-Flag
  am Generator analog `gen_promptfoo_config.py` — dann muss der Test beide Gates
  fahren (OQ-9 entscheidet die Variante, nicht das Ob).
- Die Regel „hand-maintained vs. generiert“ wird exakt formuliert
  (siehe Abschnitt *Auftrag 2*); der Regeltext selbst ist Doku, kein Code.

## Datenfluss

### (a) Template → generierter Agent (alle Provider, Default = strip)

```
agents/1-generic/<role>.md  (+ 2-platform / 3-project Overrides)
  frontmatter: frontmatter:
    name, version, description, tools, reference_standards: [...], ...
        │
        ▼  IC-01: parse_reference_standards()  → raw value (nur lesend, kein Schreiben)
        │
        ▼  provider_transform.transform_agent_content_for_provider(provider, ...)
        │      IC-03: _strip_fields = resolve_frontmatter_strip_fields(provider, config, provider_config)
        │               = FRONTMATTER_STRIP_DEFAULTS ∪ strip(project) ∪ strip(ai-providers)
        │                 \ keep(project) \ keep(ai-providers)
        │      IC-04: quiet_fields = FRONTMATTER_QUIET_STRIP_FIELDS
        │
        ├── Provider OHNE `frontmatter-mechanism` (7: Claude, Gemini, Continue,
        │   Copilot, Mammouth, ZCode, KimiCode)
        │     build_frontmatter(..., strip_fields=_strip_fields, quiet_fields=…)
        │       → YAML-Key entfernt; KEIN `reference_standards` im Provenance-Kommentar
        │     _apply_agent_transform(...)  (model/memory/permissionMode/tools/…)
        │
        └── Provider MIT `frontmatter-mechanism` (2: Opencode, Codex)
              Opencode: _transform_frontmatter_for_opencode(..., strip_fields=…)
                        → Patch + feste `removes`-Liste; `removes.extend(strip_fields)`;
                          Provenance-Kommentar ohne `reference_standards`
              Codex:    _apply_agent_transform → build_agent_toml_document(...)
                        → nur name/description(/model)/developer_instructions
                          (+ version/generated-from als Header-Kommentar)
        │
        ▼
<provider agents_dir>/<role>.<agent_ext>   ← Default: kein `reference_standards` (kein Token)
```

Pro-Provider-Ergebnis im Default (VERIFIED Konfigurationslage):

| Provider | Mechanismus | Ist-Zustand ohne Policy | Mit IC-03/IC-04 |
|---|---|---|---|
| Claude, Gemini, Continue, Copilot, Mammouth, ZCode, KimiCode | Patch (kein `frontmatter-mechanism`) | Feld wird durchgereicht | Feld + Provenance-Token entfernt |
| Opencode (`opencode-native`) | Patch + feste `removes`-Liste | Feld wird heute **durchgereicht** | explizit gestrippt (`strip_fields` → `removes.extend`), kein Token, Verhalten gepinnt |
| Codex (`codex-toml`) | TOML-Rebuild (Whitelist) | Feld fällt weg (heute implizit) | unverändert + Regression gepinnt |

Nebenpfade (kein Handlungsbedarf, VERIFIED): `standalone.py::render_standalone_agent`
entfernt die Frontmatter komplett (`_FRONTMATTER_RE.sub("", content, count=1)`,
`:216`) → keine Leak-Quelle. `admin-server`/Admin-UI rendern keine Agent-Frontmatter.

### (b) Consistency-Pfad (Template-Quelle, nicht generierte Datei)

```
scripts/consistency-check.py  (collect_agent_files → agents/1-generic/*.md + agents/2-platform/*.md)
  run_checks()
   ├─ check_agent_frontmatter(...)      (bestehend)
   ├─ check_reference_standards(...)    IC-02  → Findings (ERROR/WARNING)
   └─ check_placeholders(...)           (bestehend)
        ▼
  print_report(...)  →  rc 0 nur ohne ERROR (rc 1 bei ERROR; --strict: rc 1 auch bei WARNING)
```

Wichtig: geprüft werden **Templates**, nicht die generierten Provider-Dateien —
dort ist das Feld per Default ohnehin entfernt (Default-Strip) bzw. beim Keep-Opt-in
gewollt (OQ-7).

### (c) Auftrag-2-Fluss (Single Source of Truth)

```
config/role-defaults.yaml (quality_pipelines[*].signal_keywords)
        │  scripts/gen_routing_llm_eval_catalog.py
        ▼
tests/routing-llm-eval/catalog.generated.yaml   (generiert; kein Freshness-Test → Lücke, IC-06)
tests/routing-llm-eval/catalog.manual.yaml      ← handgepflegt
tests/routing-llm-eval/catalog.behavior.yaml    ← handgepflegt
        │  scripts/gen_promptfoo_config.py  (--check gegated via pytest → orchestration-test.yml)
        ▼
tests/routing-llm-eval/promptfooconfig.generated.yaml   (generiert, Header „do not edit by hand“)
        │
        ├── run_eval.sh / list_cases.py   (lokaler bash-Runner, liest Kataloge direkt)
        └── promptfoo (CI, Phase 3 — HYPOTHESIS: eigener Workflow existiert noch nicht)
```

## Auftrag 2 — Eval-Katalog-Regel (hand-maintained vs. generiert)

Regeltext (verbindlich, als Doku in `tests/routing-llm-eval/README.md`
„Single Source of Truth“-Abschnitt `:26-32` zu präzisieren):

1. **Handgepflegt (nur diese):** `tests/routing-llm-eval/catalog.manual.yaml`
   (Disambiguierungs-/Negativ-/Ambiguous-Fälle) und
   `tests/routing-llm-eval/catalog.behavior.yaml` (behaviorale Asserts).
2. **Generiert — niemals von Hand editieren:**
   - `tests/routing-llm-eval/catalog.generated.yaml` ← `scripts/gen_routing_llm_eval_catalog.py`
     (aus `config/role-defaults.yaml`; Header sagt das bereits, VERIFIED `:1-11`),
   - `tests/routing-llm-eval/promptfooconfig.generated.yaml` ← `scripts/gen_promptfoo_config.py`
     (aus den drei Katalogen; Header sagt das bereits, VERIFIED `:71-77`).
3. **Der Runner konsumiert die Kataloge direkt** (`run_eval.sh` + `list_cases.py`);
   die promptfoo-Config ist nur ein abgeleitetes Artefakt, kein zweiter
   Pflegepunkt.
4. **Gate-Anforderung:** jede generierte Datei hat einen Freshness-Check, der in
   CI läuft. Heute erfüllt für (2)-promptfoo, **Lücke** für (2)-catalog.generated
   (IC-06 → AC-17). Ein Gate, das nur „Datei existiert“ prüft, erfüllt die
   Anforderung nicht.

Präzisierung gegenüber der Ausgangsannahme: **nicht** „alle `catalog.*.yaml` sind
handgepflegt“ — `catalog.generated.yaml` liegt im selben Namensraum, ist aber
generiert. Genau diese Namensähnlichkeit ist die Drift-Falle, die AC-15/AC-17
adressieren.

## Acceptance Criteria

Jede AC ist nummeriert, testbar (Given/When/Then) und referenziert mindestens
einen Interface-Contract. Testdateien sind verbindlich: A/B aus
`tests/test_agents_frontmatter.py` (erweitern) + neu
`tests/test_reference_standards_strip.py` (Sync-Pfad, falls Abgrenzung gewünscht);
C aus neu `tests/test_consistency_reference_standards.py`; D aus
`tests/test_provider_agnostic_dispatch.py`; E aus `tests/test_agent_eval_framework.py`.

**A — Strip-Policy (Default = strip, alle Provider)**

- **AC-01** (IC-03, IC-04) Given ein Template mit
  `reference_standards: ["Diátaxis", "C4 model", "arc42"]` und einer Config ohne
  jeden Strip-/Keep-Key, when `transform_agent_content_for_provider` für **jeden**
  Provider ohne `frontmatter-mechanism` läuft (parameterisiert über alle
  Provider aus `load_providers_config()`, für die
  `agent-transform.frontmatter-mechanism` fehlt — heute 7), then enthält das
  Ergebnis **kein** Vorkommen des Tokens `reference_standards` (weder als
  YAML-Key noch im `agent-meta-provenance`-Kommentar) und **kein**
  `agent-meta-provenance`-Kommentar für dieses Feld.
- **AC-02** (IC-03, IC-04) Given dasselbe Template, when die Transformation für
  jeden Provider **mit** `frontmatter-mechanism` (`opencode-native`, `codex-toml`)
  läuft, then enthält das Ergebnis kein `reference_standards`-Token; für
  `codex-toml` gilt zusätzlich: das Dokument parst mit `tomllib` und enthält genau
  die Felder `name`, `description`, (`model`), `developer_instructions` (plus
  `version`/`generated-from` nur als Kommentar); für `opencode-native` parst die
  Frontmatter als YAML und enthält keinen `reference_standards`-Key. *Regression-Pin
  für `codex-toml` (heute implizit); für `opencode-native` bewusste
  Verhaltensänderung (heute Durchreichen → künftig Strip), ebenfalls durch AC-02 gepinnt.*
- **AC-03** (IC-03) Given `provider=None`-freie Default-Config (`{}`) und
  `provider_config={}`, when `resolve_frontmatter_strip_fields(provider, {}, {})`
  für jeden registrierten Provider (`registered_provider_names`) aufgerufen wird,
  then enthält das Ergebnis `"reference_standards"` — für **alle** Provider
  identisch (Provider-Agnostik des Defaults). *Test in
  `tests/test_provider_agnostic_dispatch.py` oder
  `tests/test_reference_standards_strip.py`.*
- **AC-04** (IC-03, IC-05) Given `provider-options.<P>.frontmatter-keep-fields:
  ["reference_standards"]`, when für `P` generiert wird, then bleibt
  `reference_standards` unverändert im Frontmatter (Wertliste byte-identisch zur
  Template-Quelle) und für alle **anderen** Provider bleibt es entfernt. Given
  `providers.<P>.frontmatter_keep_fields: ["reference_standards"]`
  (`ai-providers.yaml`), then gilt dasselbe. Given beide Kanäle mit
  widersprüchlichen Angaben, then gewinnt **keep** (genau ein Verhalten).
- **AC-05** (IC-03) Given die bestehenden Config-Kanäle unverändert
  (`provider-options.Opencode.frontmatter-strip-fields: [version, prompt_mode,
  generated-from]`), when generiert wird, then werden diese drei Felder weiterhin
  gestrippt und ihr Provenance-Kommentar bleibt **byte-identisch** zu heute
  (`tests/test_agents_frontmatter.py:152-173` bleibt grün) — der neue Default
  ändert bestehende Strip-Semantik nicht.
- **AC-06** (IC-03) Given fehlerhafte Config (Strip-/Keep-Key als String, `null`,
  Nicht-Dict-Provider-Eintrag, unbekannter Provider), when
  `resolve_frontmatter_strip_fields` läuft, then: keine Exception, `"reference_standards"`
  bleibt im Ergebnis (fail-safe = strip), bestehende gültige Einträge bleiben
  wirksam, und pro fehlerhaftem `(provider, key)` wird höchstens eine
  `log.warning` erzeugt.
- **AC-07** (IC-04) Given `build_frontmatter(..., strip_fields=["reference_standards",
  "version"], quiet_fields=FRONTMATTER_QUIET_STRIP_FIELDS)`, then enthält der
  Provenance-Kommentar `version=…` (wie heute) und **kein**
  `reference_standards=`; gegeben `quiet_fields=None`, then wird der Default
  (`FRONTMATTER_QUIET_STRIP_FIELDS`) verwendet (nicht „alles laut“); gegeben ein
  Nicht-Mengen-Typ, then wird der reguläre Provenance-Pfad benutzt, ohne
  Exception. *Dieselbe Matrix für `_transform_frontmatter_for_opencode`.*
- **AC-08** (IC-03, IC-04) Given zwei Templates, die sich **nur** durch
  `reference_standards` unterscheiden, when für jeden registrierten Provider
  generiert wird, then sind die beiden Ausgaben **byte-identisch**
  (Default-Strip ⇒ das Feld ist unsichtbar; gilt für Patch- und
  Rebuild-Provider gleichermaßen). *Stärkster Regressionsbeweis gegen
  unbeabsichtigte Feld-/Kommentaränderungen und für AC „existing provider output
  byte-identical except the intended strip“.*

**B — Consistency (Struktur/Format)**

- **AC-09** (IC-02) Given ein Agent-Template **ohne** `reference_standards`, when
  `check_reference_standards` läuft, then `[]` (Feld ist optional).
- **AC-10** (IC-02) Given gültige Werte `["Diátaxis", "C4 model", "arc42",
  "ISTQB@4.0", "IEEE 1012@2016#7", "ASVS@4.0.3"]`, when der Check läuft, then
  `[]`. Given ein unbekannter, aber strukturell gültiger Name
  (`"Some Unknown Standard"`), then ebenfalls `[]` (keine Registry, OQ-5).
- **AC-11** (IC-02) Given fehlerhafte Werte, when der Check läuft, then exakt die
  IC-02-Matrix-Findings: Skalar → ERROR `reference-standards.not-list`; `[]` →
  WARNING `reference-standards.empty`; `[42]` → ERROR
  `reference-standards.entry-not-string`; `[""]`/`["  "]` → ERROR
  `reference-standards.entry-empty`; `["arc42#1@2"]`, `["@1.0"]`, `["x@@"]`,
  `["y##"]`, `["x#"]` → ERROR `reference-standards.entry-format`;
  `["arc42", "arc42"]` → WARNING `reference-standards.duplicate`. *(Tabellengetriebener
  Test; jede Zeile genau ein Finding.)*
- **AC-12** (IC-02) Given ein Agent-Template mit ungültigem Feld, when
  `python3 scripts/consistency-check.py --file <template>` läuft, then erscheint
  das Finding im Report und der Exit-Code ist 1 (nur-WARNING-Fälle → rc 0; unter
  `--strict` → rc 1). Given ein Template ohne Feld, then rc-Verhalten unverändert
  zum Vorzustand.
- **AC-13** (IC-02) Given ein Template ohne Frontmatter (oder mit YAML-Fehler),
  when `check_reference_standards` läuft, then `[]` und **kein** zusätzliches
  Finding (der `frontmatter.missing`-Fehler kommt ausschließlich aus
  `check_agent_frontmatter`).

**C — Provider-Agnostik & Doku**

- **AC-14** (IC-03, alle ICs) Ein AST-Scan über die geänderten/neuen Module
  (`tests/test_provider_agnostic_dispatch.py::_TOUCHED_MODULES`,
  erweitert um `provider_transform` und `consistency/reference_standards`) findet
  keinen neuen `provider == "Name"`-Vergleich und keine Provider-Namens-Literale
  in neuem Code; die Policy-Verzweigung kommt ausschließlich aus
  Config-Keys/Resolver-Ergebnis.

**D — Auftrag 2**

- **AC-15** (IC-06) Given die Doku `tests/routing-llm-eval/README.md`, then
  benennt sie explizit `catalog.manual.yaml` + `catalog.behavior.yaml` als
  handgepflegt und `catalog.generated.yaml` **und**
  `promptfooconfig.generated.yaml` als generiert — inkl. Generator-Pfad und
  „nicht von Hand editieren“. *(Doku-AC; Nachweis per Review/grep, kein
  funktionaler Test.)*
- **AC-16** (IC-06) Given der Ist-Zustand, when
  `python3 scripts/gen_promptfoo_config.py --check` läuft, then rc 0 bei
  aktueller Datei und rc 1 bei manipulierter Datei; derselbe Check wird von
  `tests/test_agent_eval_framework.py::test_generated_promptfoo_config_is_fresh_and_valid`
  ausgeführt und läuft damit in CI (`orchestration-test.yml`). *(Bestehende
  Zusicherung wird durch den Test gepinnt; keine Code-Änderung erwartet.)*
- **AC-17** (IC-06 — Minimal-Schutz für die verifizierte Lücke) Given
  `config/role-defaults.yaml` mit geänderten `signal_keywords` **ohne**
  Regenerierung, when die Test-Suite läuft, then schlägt ein Freshness-Test für
  `tests/routing-llm-eval/catalog.generated.yaml` fehl (Regenerierung in ein
  Temp-Verzeichnis `--out <tmp>` und Byte-Vergleich gegen die committete Datei —
  oder `--check`-Flag am Generator mit identischem Ergebnis); bei unveränderter
  Quelle rc 0. Der Test liegt unter `tests/` (damit im CI-`paths`-Filter) und
  ändert **keinen** Kataloginhalt.
- **AC-18** (IC-06) Given `promptfooconfig.generated.yaml`, then enthält sie den
  bestehenden GENERATED-Header („do not edit by hand“) und die Test-Suite stellt
  sicher, dass die Datei nicht ohne Generatoränderung abweicht (AC-16). *(Header
  existiert bereits, VERIFIED `:71-77`; AC pinnt ihn.)*

## Offene Fragen + Risiken

Jede Frage mit **empfohlenem Default**. `[User approval]` markiert Punkte, die
eine bewusste Nutzerentscheidung brauchen (statt nur Reviewer-Freigabe).

- **OQ-1 — Träger des globalen Defaults.** Default: Modul-Konstante
  `FRONTMATTER_STRIP_DEFAULTS` in `providers.py` (nicht `ai-providers.yaml`
  Top-Level, weil `load_providers_config()` `data.get("providers", data)` liefert,
  `providers.py:119`; nicht pro Provider dupliziert). Alternative: neuer
  `global`-Block in `ai-providers.yaml` + Loader-Erweiterung — höherer
  Änderungsumfang, kein Mehrwert. *(GRUNDLAGE DER POLICY-ENTSCHEIDUNG.)*
- **OQ-2 — Namen der Keep-Kanäle.** Default: Projekt
  `provider-options.<P>.frontmatter-keep-fields` (kebab, konsistent mit
  `frontmatter-strip-fields`) und ai-providers
  `providers.<P>.frontmatter_keep_fields` (snake, konsistent mit
  `frontmatter_strip_fields`).
- **OQ-3 — Provenance-Leak (Policy-Entscheidung)** `[User approval]`. Default:
  `reference_standards` wird **lautlos** entfernt (`FRONTMATTER_QUIET_STRIP_FIELDS`),
  also kein Token in generierten Dateien (Akzeptanzkriterium ist strikt „kein
  `reference_standards` in generierten Provider-Agenten“). Alternative
  (abgelehnt als Default): wie `version` als Provenance-Kommentar erhalten —
  würde das Feld-Token in jede generierte Datei schreiben und AC-01/AC-08
  verletzen. Falls der User Traceability im generierten Artefakt braucht, ist das
  eine bewusste Umkehr dieses Defaults (dann AC-01/AC-08 anpassen).
- **OQ-4 — Severity-Feinheit.** Default: Struktur-Verstöße (`not-list`,
  `entry-*`) = `ERROR`; inhaltlich-schwache Befunde (`empty`, `duplicate`) =
  `WARNING` (Muster `frontmatter.tools-not-list` ERROR vs.
  `frontmatter.version-format` WARNING).
- **OQ-5 — Registry-Validierung.** Default MVP: **keine** Registry (jeder
  nicht-leere Name gültig). Später (eigene Spec): `config/reference-standards.yaml`
  mit Alias-/Versions-Normalisierung.
- **OQ-6 — Ort der Format-Grammatik.** Default: nur im Consistency-Modul
  (IC-02); `frontmatter.py` bleibt neutral (keine Feld-Policy im Bottom-Layer).
- **OQ-7 — Geltungsbereich der Prüfung.** Default: alle von
  `collect_agent_files` erfassten Templates (`agents/1-generic/*.md` +
  `agents/2-platform/*.md`, `consistency-check.py:107-120`; `3-project` wird
  nicht erfasst); generierte Provider-Dateien werden **nicht**
  geprüft.
- **OQ-8 — Doku-Surface des Feldes.** Default:
  `.claude/skills/conventions/SKILL.md` (VERIFIED vorhanden, `:43`) +
  `docs/providers/multi-provider.md`. HYPOTHESIS: weitere Provider-Skill-Kopien
  existieren — beim Implementieren prüfen und angleichen, sonst inkonsistente
  Feld-Doku.
- **OQ-9 — Form des Auftrag-2-Schutzes.** Default: Test im bestehenden
  `tests/test_agent_eval_framework.py`, Byte-Vergleich via `--out <tmp>` (kein
  Generator-Flag nötig). Alternative: `--check`-Flag am Generator + Test —
  gleichwertig, etwas mehr Produktionscode.
- **OQ-10 — Neues CI-Gate?** Default: **nein** — die bestehenden Gates
  (`orchestration-test.yml` → `pytest tests/`, `validate.yml` → `sync.py
  --check`, Frontmatter-Lint) genügen; AC-17 wird über `pytest` wirksam.
- **OQ-11 — Ist `reference_standards` auch außerhalb von `agents/**` zulässig**
  (z. B. `agents/0-external`-Wrapper, Commands)? Default: nur Agent-Templates;
  Wrapper/Commands unverändert.

Risiken:

- **R1 — Provenance-Leak bei naiver Implementierung** (hoch/hoch, mitigiert):
  Wer nur die Feldliste erweitert, schreibt das Token über den
  `agent-meta-provenance`-Kommentar in **jede** generierte Datei — bei den 8
  Patch-Surfaces als Kommentar nach dem Frontmatter, bei `Codex` über den Body
  (`developer_instructions`, da `build_frontmatter` den Kommentar vor dem
  TOML-Rebuild in den Body schreibt).
  Gegenmaßnahme: IC-04 + AC-01/AC-07/AC-08.
- **R2 — Ein Default-Strip ist verhaltensändernd für alle Provider** (mittel/mittel):
  Korrekt für dieses eine Feld, aber `FRONTMATTER_STRIP_DEFAULTS` ist der einzige
  Erweiterungspunkt — jede künftige Ergänzung ist eine Framework-weite
  Verhaltensänderung und braucht dieselbe Spec-/Review-Pflicht.
- **R3 — Merge-Reihenfolge zu #787-#795** (mittel/hoch): Landet das Feld in
  Templates, bevor IC-03 gemergt ist, entsteht ein Zeitfenster, in dem das Feld in
  8 Providern sichtbar ist (alle außer `Codex`). Empfehlung: dieses Framework-Change **zuerst** oder im
  selben Batch; kein Hard-Stop, nur ein Reihenfolgehinweis für den Orchestrator.
- **R4 — Selbst-Hosting-Drift-Gate ist blind für generierte Provider-Dirs**
  (mittel/niedrig): `validate.yml:35-41` dokumentiert, dass die generierten
  Verzeichnisse in agent-meta gitignored sind. Konsequenz: die
  Byte-Identitäts-/Kein-Leak-Zusicherung stützt sich auf **Unit-Tests** (AC-01,
  02, 08), nicht auf `sync.py --check`.
- **R5 — Consistency prüft Templates, nicht generierte Dateien** (niedrig/mittel):
  Ein durch Fehl-Konfiguration *generiertes* Feld mit falschem Format bliebe
  unentdeckt. Akzeptiert (OQ-7); Alternative wäre ein zweiter Check auf
  `agents_dir`-Inhalten — größerer Scope, eigene Spec.
- **R6 — `provider-options`-Schema ist `additionalProperties: false`** (mittel/hoch):
  ohne IC-05 bricht ein gültiger Keep-Key die Projekt-Config-Validierung
  (betrifft v. a. `Claude`/`Gemini` mit leerem `properties`). Gegenmaßnahme:
  Schema-Ergänzung **vor** der Key-Nutzung; beim Implementieren
  `config_audit`/`load_config`-Pfad gegenprüfen.
- **R7 — Silent Strip eines später „gebrauchten“ Feldes** (niedrig/mittel): Sollte
  ein Provider das Feld doch auswerten wollen, ist der Weg das Keep-Opt-in
  (IC-03/IC-05) — nicht ein zweiter Code-Pfad.
- **R8 — Klassifikations-Einspruch** (niedrig): Bewertet der Review die
  Schema-/Consistency-Berührung als Architectural, eskaliert der Orchestrator an
  `concept-architect`; Inhalt dieser Spec (Contracts/ACs) bleibt unabhängig davon
  wiederverwendbar.
- **R9 — Auftrag-2-Überdehnung** (niedrig): Der Schutz darf nicht in
  Katalog-Inhaltsänderungen abrutschen (Nicht-Ziel). AC-17 misst ausschließlich
  Frische, keine Semantik.

## Trace-Anker

- **spec-id: `SPEC-REFERENCE-STANDARDS-2026-09-15`** — dieses Dokument; der
  spätere Plan referenziert diesen Wert in seinem `**Spec:**`-Feld.
- Quelle/Analyse: `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md`
  (D2/WP2, Zeilen 338–343, 422–430, 547; Auftrag 2 ist ein Rahmen-Befund dieser
  Spec, kein WP des Plans).
- Benachbarte Spec (gleiche Seams, keine Supersession):
  `SPEC-CONTEXT-FILE-MODES-2026-09-13`
  (`docs/specs/2026-09-13-context-file-modes-design.md`).
- Externe/vorausgehende Referenzen: PRs #787/#788/#789/#790/#791/#793/#795
  (Feld-Einführung, HYPOTHESIS), Issue #505 (Frontmatter-Strip-Muster),
  `tests/routing-llm-eval/README.md` (Eval-Single-Source-of-Truth),
  `scripts/gen_promptfoo_config.py` (`--check`).

### Erwartete Berührung (Implementierung, nicht Teil dieser Spec)

| Datei | Art | IC | Zweck |
|---|---|---|---|
| `scripts/lib/frontmatter.py` | modify | IC-01, IC-04 | Feld-Konstante + Accessor; `quiet_fields` |
| `scripts/lib/providers.py` | modify | IC-03 | `FRONTMATTER_STRIP_DEFAULTS`, `resolve_frontmatter_strip_fields` |
| `scripts/lib/provider_transform.py` | modify | IC-03, IC-04 | Resolver-Aufruf statt Inline-Expression; Quiet-Menge im Opencode-Builder |
| `scripts/lib/consistency/reference_standards.py` | new | IC-02 | Struktur-/Format-Check |
| `scripts/consistency-check.py` | modify | IC-02 | Import + Aufruf im Agent-Loop |
| `config/project-config.schema.json` | modify | IC-05 | `frontmatter-keep-fields` (additiv) |
| `docs/providers/multi-provider.md` | modify | IC-05 | Default-Strip + Keep-Opt-in dokumentieren |
| `.claude/skills/conventions/SKILL.md` | modify | IC-05 | Feld + MVP-Format dokumentieren (OQ-8) |
| `tests/test_agents_frontmatter.py` | modify | AC-01…AC-08 | Strip-/Provenance-Matrix, Provider-Parameterisierung |
| `tests/test_consistency_reference_standards.py` | new | AC-09…AC-13 | Finding-Matrix + Registrierung |
| `tests/test_provider_agnostic_dispatch.py` | modify | AC-03, AC-14 | Default-Für-Alle-Provider + AST-Guard-Erweiterung |
| `tests/test_agent_eval_framework.py` | modify | AC-16…AC-18 | Freshness-Gates (promptfoo + catalog.generated) |
| `tests/routing-llm-eval/README.md` | modify | AC-15 | Regel präzisieren (hand-maintained vs. generiert) |

`config/ai-providers.yaml` und `config/role-defaults.yaml` sind mit dem gewählten
Mechanismus **nicht** zu ändern (per-Provider-Overrides nur als Zukunfts-Opt-in).
Standard-DoD (VERSION/CHANGELOG) folgt der Repo-Konvention und ist keine AC dieser
Spec.
