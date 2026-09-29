---
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
title: agent-meta-Ausnahme im Doku-INDEX-Gate — Design
status: draft
revision: 0.1
related:
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/plans/2026-09-25-docs-consolidation-oq1.md
---

# agent-meta-Ausnahme im Doku-INDEX-Gate — Design

> spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
> Rolle: concept-architect · Datum: 2026-09-29 · Klassifikation: S (gegrenzter Schnitt)
> Scope: **nur Design.** Keine Code-Datei wurde angefasst; einzige geschriebene Datei
> ist dieses Dokument.
> Vorgänger: Spec Rev. 0.7 (`status: APPROVED`, `approved: 2026-09-26`), Plan Rev. 0.7,
> Branch `feat/repository-documentation-consolidation-main`, PR #839 (Draft).
> **Vorentscheidung des Nutzers (nicht neu bewertet):** explizite agent-meta-Ausnahme;
> die Knowledge Engine bleibt für Consumer-Projekte autoritativ.

---

## 0. Kurzfassung

W3-6 scheitert an **einer** Codezeile: `scripts/lib/doc_renderer.py:702`. Der
KE-Vorrang-Zweig von `_index_mode_block_reason()` blockiert in agent-meta jeden
`docs/INDEX.md`-Schreibvorgang, weil `resolve_index_mode()` dort `"knowledge-engine"`
auflöst. Der Entwurf führt dafür **einen** neuen, fail-off Config-Key
`docs-consolidation.index-owner` ein (zweiwertiges Enum, Default `auto`), der
ausschließlich den **Auslöser** dieses einen Gates verengt — nicht die Liste der
blockierenden Eigentümer erweitert, nicht `resolve_index_mode()` ändert, nicht die
Besitzregel, `is_file_index_skeleton`, die B2-Doppel-Writer-Invariante oder den
`dry_run`-Vertrag anfasst. **Der Code enthält keine agent-meta-Kenntnis:** „die
agent-meta-Ausnahme" entsteht dadurch, dass *nur* agent-meta den Key setzt.

Fünf Punkte sind **inhaltliche Pflichtänderungen** der APPROVED-Spec und brauchen vor
Umsetzung eine User-Freigabe (Kapitel 6). Fünf Entscheidungsvorlagen **E-9 … E-13**
liegen offen bei; **keine** davon ist hier entschieden.

---

## 1. Diagnose — exakter Fehlschlagpunkt von W3-6

### 1.1 Der Pfad, den W3-6 nimmt

W3-6 (Plan `:4918-4944`) führt `python3 scripts/sync.py` im Repo **agent-meta** aus und
erwartet, dass dabei `docs/INDEX.md` entsteht (Plan `:4932`, `:4940-4941`).

| Schritt | Ort | Ergebnis in agent-meta |
|---|---|---|
| 1 | `sync_pipeline.py:966` `_sync_stage_knowledge_and_isolation` | Stage läuft |
| 2 | `sync_pipeline.py:974` → `knowledge.py` | KE schreibt `knowledge/**` — **erfolgreich, unberührt** |
| 3 | `sync_pipeline.py:980` → `spec_plan_scaffold.py:115-116` | `resolve_index_mode()` = `"knowledge-engine"` ⇒ **kein** Skeleton geschrieben |
| 4 | `sync_pipeline.py:985` → `sync_pipeline.py:958` → `doc_renderer.py:714` | Writerschicht |
| 5 | `doc_renderer.py:801-803` Gate `enabled` | `docs-consolidation.enabled: true` (`.meta-config/project.yaml:399`) ⇒ **passiert** |
| 6 | `doc_renderer.py:805-808` Gate `has_docs_tree` | `docs/` existiert ⇒ **passiert** |
| 7 | `doc_renderer.py:810-814` Mode-Gate | **⇒ Abbruch mit `skipped`** |
| 8 | `doc_renderer.py:821-824` `compute_doc_facts` + `render_docs_index` | **nie erreicht** |
| 9 | `doc_renderer.py:861` `write_checked` | **nie erreicht** |

### 1.2 Die exakte Fehlerstelle (Zitat)

`scripts/lib/doc_renderer.py:702-703`:

```python
    if resolve_index_mode(config)[0] == "knowledge-engine":
        return KE_AUTHORITATIVE_REASON
```

`scripts/lib/doc_renderer.py:277`:

```python
KE_AUTHORITATIVE_REASON: str = "knowledge-engine index is authoritative"
```

`scripts/lib/doc_renderer.py:810-814`:

```python
    mode_reason = _index_mode_block_reason(config)
    if mode_reason is not None:
        plan["skipped"].append(index_rel)
        log.note(LOG_TARGET, f"{index_rel}: {mode_reason}")
        return plan
```

### 1.3 Warum `resolve_index_mode()` in agent-meta `"knowledge-engine"` liefert

`scripts/lib/spec_plan_scaffold.py:87-97` (Auszug):

```python
    index = sp.get("index") or {}
    override = sp.get("external-system-override") or {}
    ke = config.get("knowledge-engine") or {}
    mode = index.get("mode", "knowledge-engine")
    ...
    if mode == "knowledge-engine" and (
        override.get("enabled", False) or not ke.get("enabled", False)
    ):
        mode = "file-index"
    return mode, fallback
```

Gemessen an `.meta-config/project.yaml`:

| Eingang | Wert | Datei:Zeile |
|---|---|---|
| `spec-plan-workflow.index.mode` | `knowledge-engine` | `.meta-config/project.yaml:69` |
| `spec-plan-workflow.external-system-override.enabled` | `false` | `.meta-config/project.yaml:77` |
| `knowledge-engine.enabled` | `true` | `.meta-config/project.yaml:15` |

`false or not true` ⇒ `False` ⇒ **kein** Absenken auf `file-index` ⇒ Rückgabe
`("knowledge-engine", "docs/INDEX.md")`. Das Gate feuert.

### 1.4 Gemessener Ist-Stand

- `docs/INDEX.md` **existiert nicht** (Glob `docs/INDEX.md` → keine Treffer). Damit ist
  W3-6s Kernlieferung gegenwärtig unmöglich.
- Folge: V2 (`scripts/lib/consistency/docs_index.py:180-211`) meldet **jede** Seite unter
  `docs/` als `Severity.ERROR` — genau der V-Check, den W3-6 auf 0 bringen soll
  (Plan `:4926`, `:4937`).
- W3-6s eigener Abnahme-Test `tests/test_doc_renderer.py:3258`
  (`test_skeleton_replaced_once`, AC-20) **umgeht** das Gate heute künstlich:
  `_e2e_config()` (`:3209-3238`) erzwingt `knowledge-engine: {"enabled": False}`
  (`:3237`), und der Docstring `:3213-3223` hält ausdrücklich fest, dass die
  agent-meta-Konfiguration **nicht** von diesem Test abgedeckt ist. Es existiert heute
  **kein** Test, der beweist, dass der Index in agent-metas eigener Konfiguration
  geschrieben werden kann.

### 1.5 Was ausdrücklich **nicht** die Fehlerursache ist

| Verdacht | Beleg | Befund |
|---|---|---|
| Doppel-Writer B2 | `spec_plan_scaffold.py:116` | **nicht** die Ursache: im `knowledge-engine`-Modus schreibt der Scaffold **gar nichts**, es gibt in agent-meta also keinen Doppel-Writer. |
| `index-mode: skeleton` | `.meta-config/project.yaml:398-401` (Key fehlt ⇒ Default `full`, `doc_renderer.py:274`) | feuert **nicht** (`doc_renderer.py:706-708`). |
| `docs-consolidation.enabled` | `.meta-config/project.yaml:399` = `true` | passiert. |
| OQ1 (Wiki-Topics ↔ `docs/guides/`) | `docs/plans/2026-09-25-docs-consolidation-oq1.md:94` | **ohne Wirkung** auf dieses Gate; OQ1 ist eine Inhaltsfrage über `knowledge/wiki/**`, die dieser Entwurf nicht berührt. Blockiert W5, nicht W3-6. |

---

## 2. Entwurf

### 2.1 Komponentenkarte

| ID | Komponente | Änderung | Verantwortung (genau eine) |
|---|---|---|---|
| **C1** | `scripts/lib/doc_renderer.py::_index_mode_block_reason` (`:663-711`) | **geändert** | Entscheidet allein, *ob* ein Schreiben verboten ist — jetzt mit einer dritten, deklarativen Eingabe |
| **C2** | `.meta-config/project.yaml` → `docs-consolidation.index-owner` | **neu** (Datenwert) | Deklariert den Eigentümer des Pfades `docs/INDEX.md`; einziger Ort, an dem „agent-meta" faktisch auftaucht — und zwar als Konfigurationswert, nicht als Code |
| **C3** | `config/project-config.schema.json` → `docs-consolidation.properties.index-owner` (`:2424-2469`) | **neu** | Enum + Default + `additionalProperties: false` (`:2470`) ⇒ Tippfehler werden vom Wächter gefangen |
| **C4** | `tests/test_doc_renderer.py` | **ergänzt** (5 neue Tests) + **eine** Docstring-Korrektur (`:3209-3223`) | Pinnt Absenz-Semantik, Override, Fail-closed, Skeleton-Umkehrschutz, `dry_run` |
| **C5** | `tests/test_docs_consolidation_migration.py` | **ergänzt** (Enum-Test) + **eine** Zählkommentar-Korrektur (`:42`) | Pinnt das Schema |
| **C6** | `docs/specs/2026-09-25-repository-documentation-consolidation.md` | **Pflichtänderung, freizugeben** (Kapitel 6) | IC-13, IC-15, IC-22, AC-21, R7 |

**Unverändert — bewusst, nicht zufällig:** `scripts/lib/spec_plan_scaffold.py`
(kein Eingriff in `resolve_index_mode`, `is_file_index_skeleton`, `_FILE_INDEX_SKELETON_MARKER`),
`scripts/lib/knowledge.py`, `scripts/lib/doc_index.py`,
`scripts/lib/generated_file_drift.py`, `scripts/lib/sync_pipeline.py` (Stage-Reihenfolge
= B2-Invariante), `scripts/consistency-check.py`, alle Szenario-Fixtures und -Asserts.

### 2.2 Warum genau **ein** Gate angefasst wird

`_index_mode_block_reason()` (`:663-711`) besitzt laut eigenem Docstring eine
**geschlossene** Liste blockierender Eigentümer (`:682-694`):

> „The two owners above are the complete list of what forbids a write, so `off` is
> **not** one of them… Treating `off` as fail-closed would be a different contract, and
> a behaviour change — not a docstring fix.“

Der Entwurf fügt **keinen dritten Eigentümer** hinzu. Er verengt nur die **Bedingung**,
unter der der *erste* Eigentümer greift. Damit bleibt die geschlossene Liste bei zwei,
und die Aussage `:685-686` bleibt wortwörtlich wahr. Das ist der kleinstmögliche
Eingriff, der W3-6 freigibt.

### 2.3 Interface-Verträge (neue ICs)

> **Nummerierung:** Die Aufgabenstellung nannte „neue ICs ab IC-16". **IC-16 ist jedoch
> bereits belegt** — IC-16 ist der Hash-Baseline-Vertrag
> (`…consolidation.md:1374`, Code `scripts/lib/generated_file_drift.py:75-91`). IC-17 bis
> IC-24 sind ebenfalls vergeben (IC-22 Config-Tabelle `:1531`; IC-23 Sollwert-Datei
> `:1567`; IC-24 Restore-Pfad, R2 `:2493`). Der nächste freie IC ist daher **IC-25**.
> Bestehende ICs werden **nicht** umnummeriert.

#### IC-25 — `docs-consolidation.index-owner`: Eigentümerdeklaration für `docs/INDEX.md`

```python
# scripts/lib/doc_renderer.py (neu, neben :270-275)

FULL_INDEX_MODE: str = "full"
SKELETON_INDEX_MODE: str = "skeleton"

INDEX_OWNER_AUTO: str = "auto"
"""Abwesenheits-Default von ``index-owner``: die Modus-Aufloesung entscheidet —
wortwoertlich IC-13, Zeile 2."""

INDEX_OWNER_GENERATOR: str = "docs-consolidation"
"""Dieser Generator erklaert sich zum Eigentuemer von ``docs/INDEX.md``."""

KE_OVERRIDE_REASON: str = (
    "index-owner: docs-consolidation — the docs generator owns docs/INDEX.md in "
    "this project"
)
"""Grund, warum der KE-Vorrang-Zweig in dieser Ausnahme nicht greift."""

UNKNOWN_INDEX_OWNER_REASON: str = (
    "index-owner is neither 'auto' nor 'docs-consolidation' — not written "
    "(fail-closed, IC-22)"
)
"""Grund fuer einen unbekannten Wert: eigener Grund, weil die Liste der blockierenden
Eigentuemer geschlossen bleibt (siehe ``UNKNOWN_INDEX_MODE_REASON``:284-299 als
Muster — ein Modus, der nichts bedeutet, darf keinen wahren Satz loggen)."""
```

Geänderte Entscheidungsfolge in `_index_mode_block_reason()` (**jeder** Schritt kann nur
konservativer werden; die Reihenfolge ist der Vertrag, `:729-731`):

```python
def _index_mode_block_reason(config: dict) -> str | None:
    block = config.get("docs-consolidation")
    block = block if isinstance(block, dict) else {}
    owner = block.get("index-owner", INDEX_OWNER_AUTO)
    if owner not in (INDEX_OWNER_AUTO, INDEX_OWNER_GENERATOR):
        return UNKNOWN_INDEX_OWNER_REASON          # (1) fail-closed, VOR der KE-Pruefung
    if (
        owner == INDEX_OWNER_AUTO
        and resolve_index_mode(config)[0] == "knowledge-engine"
    ):
        return KE_AUTHORITATIVE_REASON              # (2) unveraendert, nur bedingt
    mode = block.get("index-mode", DEFAULT_INDEX_MODE)
    if mode == SKELETON_INDEX_MODE:
        return SKELETON_MODE_REASON                 # (3) unveraendert
    if mode != FULL_INDEX_MODE:
        return UNKNOWN_INDEX_MODE_REASON            # (4) unveraendert
    return None
```

**Warum die Reihenfolge so ist (und nicht anders):** Der Fail-closed-Zweig (1) steht
**vor** der KE-Pruefung, damit ein Tippfehler nie als „KE ist autoritativ" fehlgedeutet
wird — dasselbe Argument, mit dem der Bestand die KE-Pruefung vor den
`index-mode`-Zweig legt (`:682-694`). Die Bedingung in (2) ist eine **Verengung**
(`auto and KE`), keine Erweiterung: `index-owner: docs-consolidation` kann keinen
Eigentuemer entfernen, nur den einen Ausloeser stilllegen.

| Wert | `resolve_index_mode()` | `index-mode` | Ergebnis |
|---|---|---|---|
| Key **fehlt** (Default `auto`) | `knowledge-engine` | beliebig | `KE_AUTHORITATIVE_REASON` — **identisch zum heutigen Verhalten** |
| Key **fehlt** | `file-index` / `off` | `full` | `None` — **identisch zum heutigen Verhalten** |
| Key **fehlt** | beliebig | `skeleton` | `SKELETON_MODE_REASON` — **identisch** |
| `docs-consolidation` | `knowledge-engine` | `full` | **`None`** ⇒ Schreiben erlaubt (die Ausnahme) |
| `docs-consolidation` | `knowledge-engine` | `skeleton` | `SKELETON_MODE_REASON` — **Gegenprobe, die Ausnahme hebt (3) nicht auf** |
| beliebiger/unbekannter Wert | beliebig | beliebig | `UNKNOWN_INDEX_OWNER_REASON`, **kein** Schreiben |

#### IC-26 — Begrenztheitsvertrag der Ausnahme

1. **Wirkung ausschliesslich auf `docs/INDEX.md`.** `index-owner` wird an genau einer
   Stelle gelesen (`_index_mode_block_reason`). Diese Funktion ist ausschliesslich fuer
   den Index-Writer zustaendig; die Hybrid-Regionen von W3-7 laufen ueber
   `apply_fact_blocks()` (`doc_renderer.py:183`) und werden **nicht** von diesem Gate
   beruehrt (siehe Kapitel 5, E-10).
2. **`resolve_index_mode()` bleibt unveraendert** (`spec_plan_scaffold.py:80-97`).
   Folge in agent-meta: der Scaffold schreibt **weiterhin kein** Skeleton
   (`spec_plan_scaffold.py:116` bleibt `False`). Die B2-Invariante „Scaffold zuerst,
   Generator ersetzt das Skeleton **einmalig**" (Spec `:1292-1304`, R7 `:2498`) ist damit
   **nicht** gebrochen, sondern fuer agent-meta **sachlich gegenstandslos**: es gibt
   nur einen Writer und einen Erstschreibvorgang (`CREATE`, `doc_renderer.py:830`).
   Sobald die Datei existiert, greift der Besitzzweig ueber
   `_carries_generator_id()` (`:644-655`, ID `doc-indexer/1` `:310`) — der zweite Lauf
   meldet `unchanged` (`:845-848`).
3. **Besitzregel unveraendert** (IC-13, Spec `:1331-1338`): eine fremde Datei ohne Marker
   und ohne Generator-ID wird auch mit `index-owner: docs-consolidation` **nicht**
   ueberschrieben (`:855-858`).
4. **`is_file_index_skeleton()` unveraendert** (`spec_plan_scaffold.py:41-77`), inkl.
   der dokumentierten permissiven Marker-Suchrichtung (`:52-68`).
5. **`dry_run`-Vertrag unveraendert** (IC-13, AC-23, Spec `:1325`): genau ein
   `write_checked` (`:861`), im Dry-Run nur Aenderungserkennung, Action getaggt
   `WOULD-CREATE`/`WOULD-UPDATE` (`:867`).
6. **Consumer unberuehrt.** Kein Szenario-Fixture enthaelt einen `docs-consolidation`-Key
   (Spec `:1553-1557`; `run.sh:46-52` spielt sie 1:1 ein) ⇒ `enabled` fail-off ⇒ die
   Ausnahme ist fuer die Szenarien **per Konstruktion unerreichbar**. Szenarien
   50/51/52/54/55/56 (Registry `:97-103`) bleiben ohne Aenderung gruen (AC-38).
7. **KE-Modi der Consumer unveraendert.** `knowledge.py:185-196` liest
   `resolve_index_mode()` unveraendert; `knowledge/wiki/index.md` bleibt Eigentum der KE.
8. **Kein Provider-Name, kein Projektname im Code.** Bestaetigt durch den bestehenden
   Guard `tests/test_provider_agnostic_dispatch.py` und die Policy
   `.opencode/skills/provider-agnostic/SKILL.md:12-18` (Capability-Flags/Config-Keys statt
   `if provider == "Name"`); dasselbe Prinzip gilt fuer die Projekt-Achse, vgl.
   `AGENTS.md:240`.

### 2.4 Config-Keys mit Defaults

| Key | Ort | Default bei Abwesenheit | agent-meta (explizit) | Consumer | Wirkung |
|---|---|---|---|---|---|
| `docs-consolidation.index-owner` | `.meta-config/project.yaml` (neu) | **`auto`** | **`docs-consolidation`** | **`auto`** (Key nicht gesetzt) | Verengt **ausschliesslich** den KE-Vorrang-Zweig in `_index_mode_block_reason` auf `docs/INDEX.md` |

**Schema-Eintrag** (C3), Muster nach `config/project-config.schema.json:2430-2438`:

```json
"index-owner": {
  "type": "string",
  "enum": ["auto", "docs-consolidation"],
  "default": "auto",
  "description": "auto = the resolved index mode decides (IC-13). docs-consolidation = this project declares the docs generator the owner of docs/INDEX.md, so a knowledge-engine mode does not block the write. Fail-off: absent means auto."
}
```

`additionalProperties: false` (`:2470`) bleibt ⇒ ein Tippfehler wie `index-owner: agent-meta`
oder `docs` ist ein **Schema-Fehler**, kein stiller No-op.

**Warum `auto` und nicht `knowledge-engine` als Default:** `auto` ist wortwoertlich das
heutige Verhalten („die Modus-Aufloesung entscheidet") und haelt damit die
Absenz-Semantik der Spec wortgleich; ein Default `knowledge-engine` wuerde eine Aussage
treffen, die es ohne Key gar nicht gibt. Ein dritter Wert `knowledge-engine` als
*explizite* Deklaration wird **bewusst nicht eingefuehrt** (Begruendung in DECISION-2).

### 2.5 Datenfluss

```
sync.py
  └─ _sync_stage_knowledge_and_isolation()            sync_pipeline.py:966
       ├─ sync_knowledge_engine()                     :974   → knowledge/wiki/**   [unveraendert]
       ├─ scaffold_spec_plan_dirs()                   :980   → KE-Modus ⇒ KEIN Skeleton :116  [unveraendert]
       │                                                     (B2: Scaffold zuerst, Reihenfolge unveraendert)
       └─ _sync_stage_docs_consolidation()            :985
            └─ sync_docs_consolidation()              doc_renderer.py:714
                 ├─ Gate 1  enabled is True            :801   [unveraendert]
                 ├─ Gate 2  has_docs_tree()            :805   [unveraendert]
                 ├─ Gate 3  _index_mode_block_reason   :810   ► EINZIGE AENDERUNG (:702-710)
                 │            ├─ UNKNOWN owner  → fail-closed          (neu, IC-25)
                 │            ├─ auto + KE     → KE_AUTHORITATIVE     (unveraendert)
                 │            ├─ skeleton      → SKELETON_MODE         (unveraendert)
                 │            └─ docs-consolidation + full → None  ⇒ WEITER
                 ├─ compute_doc_facts()                :821   [unveraendert]
                 ├─ render_docs_index()                :824   [unveraendert]
                 ├─ Besitzpruefung                     :826-859
                 │    Lauf 1: FileNotFoundError → tag = "CREATE"  :829-830
                 │    Lauf 2: _carries_generator_id  → "unchanged"/"UPDATE" :845-859
                 └─ write_checked(...)                 :861   [unveraendert, dry_run :867]
```

**Zustands- und Datenverantwortung:** Ab dem ersten erfolgreichen Lauf gehört
`docs/INDEX.md` dem `doc_renderer` (Besitzregel IC-13). `knowledge/wiki/index.md`
bleibt Eigentum der Knowledge Engine (`knowledge.py:163-169`). Kein Component
uebernimmt Daten des anderen — die beiden Index-Baeume bleiben getrennt, und genau das
ist der gewuenschte Endzustand: **in agent-meta zwei Indizes mit klar getrennten
Eigentuemern, in Consumer-Projekten unveraendert genau ein Index (KE)**.

### 2.6 Nachweis der Begrenztheit (drei Maschinen, keine Behauptung)

| Maschine | Wirkung |
|---|---|
| `resolve_index_mode()` | **unveraendert** (`spec_plan_scaffold.py:80-97`) ⇒ Default-Modus nicht umgedreht, KE-Modi der Consumer unveraendert |
| `_index_mode_block_reason()` | **eine** Bedingung wird um eine Konjunktion verklammert (`:702`) ⇒ **kein** dritter Eigentuemer, Liste bleibt geschlossen (`:685-686`) |
| Schema `additionalProperties: false` (`:2470`) | Jede Ausweitung des Schluesselsels wird zum Validierungsfehler statt zu stillem Verhalten |

---

## 3. Trade-off-Analyse der Anbindungsachsen

### 3.1 Die Kandidaten

| Achse | Variante | Was der Code sehen wuerde |
|---|---|---|
| **A** | Deklarativer Config-Key im `docs-consolidation`-Block | „dieses Projekt **erklaert** den Doku-Generator zum Eigentuemer" |
| **B-1** | Eigenheit per Namen | `project.name == "agent-meta"` bzw. `platforms == ["agent-meta"]` |
| **B-2** | Eigenheit per Struktur | „dieses Repo *ist* das Framework-Repo" (Marker-Datei, `scripts/sync.py` + `agents/1-generic/` vorhanden) |
| **C** | Capabilities-Key im `knowledge-engine`-Block | `knowledge-engine.index-scope: bundle` (die KE verzichtet auf den Pfad) |
| **D** | Nicht ablehnen | `resolve_index_mode()`-Default umdrehen bzw. `index.mode: file-index` in agent-meta setzen |

### 3.2 Entscheidungen

**DECISION-1 — Anbindungsachse: deklarativer Config-Key (A)**

```
DECISION
context:    Das KE-Vorrang-Gate blockiert in agent-meta jeden docs/INDEX.md-Schreibvorgang,
            und die Loesung darf "agent-meta" nirgends im Code kodieren.
choice:     A — zweiwertiges Enum docs-consolidation.index-owner (Default auto), gelesen
            von genau einer Funktion (_index_mode_block_reason), in agent-meta explizit
            auf "docs-consolidation" gesetzt.
alternatives:
  - B-1 (project.name / platforms-Vergleich): verstoesst direkt gegen die Aufgaben-
    Constraint und gegen AGENTS.md:240; zaehlt eine Projekt**identitaet**, die eine
    Variable ist, keine Faehigkeit.
  - B-2 (Struktur-/Marker-Erkennung): von der APPROVED-Spec bereits entschieden —
    Spec R17:2513 "Ein 'agent-meta-Eigenerkennung'-Heuristik-Gate wird **nicht** gebaut
    (es wuerde in Fremd-Repos Doku-Claims aufstellen, die niemand gepflegt hat)".
    Ein Heuristik-Gate, das in einem Fork feuert, erzeugt Doku ohne Owner.
  - C (knowledge-engine.index-scope): der KE-Block wird von knowledge.py, config.py,
    consistency-check.py, dem Schema und der Admin-UI gelesen
    (tests/test_knowledge_engine.py:165,175,385,422,467,488); ihm Jurisdiktion ueber den
    *Doku*-Index zu geben, koppelt zwei Features, die IC-13 bewusst entkoppelt hält
    (das Gate entscheidet aus docs-consolidation + resolve_index_mode).
  - D (Default umdrehen / index.mode: file-index in agent-meta): dreht die KE-Praezedenz
    um und macht den Scaffold zum Mit-Schreiber — bricht genau die B2-Invariante, die
    W3-6 nicht aufweichen darf; zusaetzlich globale Umstellung (Constraint).
consequences:
  leichter  — Die Ausnahme ist ein **Datenfakt**, sichtbar im Config-Diff, reviewbar,
              und kann in einem Projekt, das nicht danach fragt, nie feuern.
              Ein **neues** Projekt kann dieselbe Achse mit dokumentierter Begruendung
              nutzen — der Code transportiert eine **Policy-Achse**, keinen Sonderfall.
              Unit-Tests decken alle Enum-Zweige ab, ohne eine Projektidentitaet zu
              simulieren.
  schwerer  — Ein neuer Key, eine neue Schema-Property, ein Enum; die IC-22-Tabelle
              waechst um eine Zeile; und die Abwesenheits-Semantik muss in **jedem**
              Review neu bestaetigt werden (dafuer zwei neue Tests).
```

Das tragende Argument ist die **Richtung der Deklaration**: Ausgenommen wird nicht die
KE, sondern der *Anspruch des Doku-Generators auf einen Pfad*. Genau diesen Anspruch
kodiert bereits der Nachbar-Key `docs-consolidation.index-mode` — „Abwesenheits-Default
von `index-mode` (IC-22) — der Voll-Index ersetzt das Skeleton" (`doc_renderer.py:274-275`).
`index-owner` ist damit **Geschwister**, nicht Nachfolger: gleicher Block, gleiche
Fail-off-Logik, gleiche Garantie „**Kein** Key enthaelt einen Provider-Namen"
(Spec `:1563`). Achse C verlangt dagegen, dass die KE einen Pfad **verwirft**, den sie
zu Recht haelt — und macht die Praezedenzregel davon abhaengig, *welchen* Block man
anschreibt.

Aus **Dekompositionssicht** (Kopplung / Failure-Isolation / Deployability / Data-Ownership):
Die Grenze zwischen „KE-Jurisdiktion" und „Doku-Jurisdiktion" bleibt **eine** Grenze und
wird **nicht** mit einer zweiten, gegenlaeufigen truth source verdoppelt. Deployability
bleibt additiv: Consumer-Projekte erhalten beim Sync **kein** neues Feld, keine
Schema-Aenderung an ihrem Config und **null** Verhaltensaenderung.

**DECISION-2 — Kein expliziter Wert `knowledge-engine` im Enum**

```
DECISION
context:    Ein Enum mit drei Werten (auto | knowledge-engine | docs-consolidation) waere
            symmetrischer, wuerde aber einen **dritten blockierenden Eigentuem** in die
            Liste aufnehmen, die doc_renderer.py:685-686 ausdruecklich als geschlossen
            fuehrt ("The two owners above are the complete list of what forbids a
            write").
choice:     Nur zwei Werte. Der Key kann einen Eigentuem **nicht** hinzufuegen, sondern
            nur den einen Ausloeser stilllegen.
alternatives:
  - Wert "knowledge-engine": wuerde in einem file-index-Projekt einen Pfad blockieren,
    den heute der Generator schreibt — eine **neue** Foermlichkeit, die IC-13 nicht
    kennt, und eine Verhaltensaenderung fuer jedes file-index-Projekt, das den Key
    setzt. Ausserdem: eine Eigentuemerklaerung, die die Modus-Aufloesung uebersteuert,
    macht "resolve_index_mode entscheidet" (IC-13, Zeile 2) zur Halfte der Wahrheit.
consequences:
  leichter  — Die Liste blockierender Eigentuemer bleibt geschlossen und nachprüfbar;
              fail-closed greift nur fuer echte Tippfehler.
  schwerer  — Eine denkbare, aber nicht umgesetzte Feinsteuerung bleibt zukünftigen
              Vorlagen ueberlassen (E-9).
```

**DECISION-3 — Kein Eingriff in `resolve_index_mode()`**

```
DECISION
context:    Der naechstliegende Kurzschluss waere, die KE-Praezedenz in
            resolve_index_mode() selbst zu relativieren.
choice:     Kein Eingriff. Die Ausnahme lebt im *Doku*-Gate, das die Funktion nur
            aufruft, nie in der Funktion, die auch der Scaffold liest.
alternatives:
  - Optionaler dritter Parameter resolve_index_mode(config, *, owner_override=False):
    breitete die Ausnahme in die Scaffold-Entscheidung aus (spec_plan_scaffold.py:115)
    und in knowledge.py:185 — also genau in die Pfade, die unveraendert bleiben
    muessen. Auch: eine Aenderung der **Signatur** eines Schnittstellenpunktes, den
    W1-1 bis W3-5 als stabil behandeln.
consequences:
  leichter  — Drei Aufrufer (spec_plan_scaffold, doc_renderer, knowledge) sehen
              unveraenderte Semantik; Szenario 52 ist strukturell unberuehrt.
  schwerer  — Die Ausnahme ist an **eine** Funktion gebunden; eine zweite
              Doku-Ausnahme (etwa fuer docs/architecture/INDEX.md) braeuchte eine
              eigene, neu zu bewertende Achse.
```

**DECISION-4 — W3-7 wird von dieser Ausnahme ausdruecklich nicht miterfasst**

```
DECISION
context:    Die Aufgabe begrenzt die Ausnahme auf docs/INDEX.md und stellt W3-7 daneben.
choice:     Der Key wirkt ausschliesslich auf _index_mode_block_reason, also auf den
            Index-Writer. Die Hybrid-Regionen (apply_fact_blocks, doc_renderer.py:183)
            bleiben unberuehrt.
alternatives:
  - Den Key als "der Doku-Generator besitzt alle generierten Doku-Artefakte" lesen und
    sources mitskalieren: waere eine Umbenennung des Keys (Scheinkonsistenz, wenn der
    Name nur einen Pfad meint) und wuerde W3-7 in den Scope ziehen, ohne dass ein Gate
    es blockiert.
consequences:
  leichter  — W3-7 braucht **keine** Ausnahme (es ist durch das KE-Gate nicht
              blockiert), sondern nur sources in .meta-config/project.yaml; der
              Aufgaben-Scope bleibt eingehalten.
  schwerer  — Wer spaeter eine Ausnahme fuer die Regionen braucht, muss den Key
              umbenennen — als Breaking Change mit Migrationsfolge (offen als E-10).
```

---

## 4. Blast-Radius

### 4.1 Kandidatenliste der angefassten Dateien

| # | Datei | Art | Umfang |
|---|---|---|---|
| 1 | `scripts/lib/doc_renderer.py` | **Modify** | 3 neue Modulkonstanten; `_index_mode_block_reason` (`:663-711`); Docstring `:669-672` |
| 2 | `.meta-config/project.yaml` | **Modify** | eine Zeile in `docs-consolidation` (`:398-401`) |
| 3 | `config/project-config.schema.json` | **Modify** | eine Property in `:2424-2469` |
| 4 | `tests/test_doc_renderer.py` | **Modify** | 5 neue Tests; 1 Docstring-Korrektur (`:3209-3223`) |
| 5 | `tests/test_docs_consolidation_migration.py` | **Modify** | 1 Enum-Test; Zählkommentar `:42` |
| 6 | `docs/specs/2026-09-25-repository-documentation-consolidation.md` | **Modify (freizugeben)** | IC-13, IC-15, IC-22-Tabelle, AC-21, R7 (Kapitel 6) |
| 7 | `docs/plans/2026-09-25-repository-documentation-consolidation.md` | **Modify** | W3-6 Files/Verifikation, W3-6 „V2 ist mit dem Sync auf 0" (`:4937`) |
| 8 | `agent-meta.config.example.yaml` | **Modify** | Beispielzeile (Spec-Konvention „neue Platzhalter dokumentiert", `AGENTS.md:247`) |
| 9 | `docs/specs/2026-09-25-repository-documentation-consolidation-design-agent-meta-exception.md` | **Create** | dieses Dokument |

**Summe:** 1 Code-Datei, 2 Config-/Schema-Dateien, 2 Test-Dateien, 3 Doku-Dateien.
Kein neuer Writer, keine neue Stage, keine neue Datei unter `scripts/`.

### 4.2 Tests, die sich **nicht** ändern (Sollwerte bleiben)

| Test / Assert | Warum unveraendert |
|---|---|
| `tests/scenarios/asserts/50:32`, `51:32`, `52:44`, `54:26-27`, `55:24-25`, `56:31` | Die Fixtures `tests/scenarios/configs/*.project.yaml` enthalten **keinen** `docs-consolidation`-Block (Spec `:1553-1557`, `run.sh:46-52`) ⇒ `enabled` fail-off ⇒ Code-Pfad nie erreicht. **AC-38 bleibt wörtlich gültig, NG-10 gewahrt.** |
| `test_ke_authoritative_writes_no_index` (`:2614`) | Fixture `_KE_AUTHORITATIVE_CONFIG` (`:2481-2484`) hat **keinen** `index-owner`-Key ⇒ `auto` ⇒ Gate feuert unveraendert |
| `test_ke_authoritative_writes_no_index_even_when_absent` (`:2650`) | dito |
| `test_ke_index_stays_authoritative` (`:3100`) | Fixture `:3118-3123` ohne `index-owner` ⇒ bleibt gruen |
| `test_index_mode_off_permits_the_full_index` (`:2740`) | `off` + kein `index-owner` ⇒ unveraendert; der Test pinnt ausdruecklich, dass `off` kein blockierender Eigentuem ist |
| `test_skeleton_mode_preserves_scaffold` (`:2559`), `test_skeleton_mode_creates_no_index_at_all` (`:2590`) | `index-mode: skeleton` wird von der Ausnahme **nicht** aufgehoben (IC-26/2) |
| `test_skeleton_replaced_once` (`:3258`) | Siehe 4.3 — bleibt gruen, wird **nicht** umdefiniert |
| `test_scaffold_guard_recognises_only_the_skeleton` (`:2529`) | `is_file_index_skeleton` unberuehrt |

### 4.3 `test_skeleton_replaced_once` — Sollwert-Stabilitaet als Design-Anforderung

`_e2e_config()` (`:3229-3238`) kopiert den **Live**-Block inklusive des neuen Keys und
setzt zusaetzlich `knowledge-engine: {"enabled": False}`. Damit laeuft der Test in einer
`file-index`-Konfiguration, in der `index-owner` per Konstruktion ein **No-op** ist (der
KE-Zweig greift ohnehin nicht). Der Test bleibt also gruen, **ohne** dass sein Sollwert
angefasst wird.

Das ist Absicht und muss im Review so verteidigt werden: der Test beweist die
**Skeleton-Uebernahme** (AC-20), nicht die **Eigentuemer-Deklaration**. Fuer die zweite
Aussage kommt der neue Test aus 4.4 Nr. 1 daneben — derselbe Live-Block, aber mit
`knowledge-engine: {enabled: true}`.

**Ausdruecklich benannte Sollwert-Aenderung:** der Docstring von `_e2e_config`
(`:3209-3223`) behauptet, IC-13/IC-15 machten „the knowledge engine the authoritative
owner of `docs/INDEX.md`" fuer agent-metas Konfiguration. Nach C2 ist diese Aussage fuer
agent-meta **falsch** (der Key verengt genau diesen Zweig). Das ist eine **Korrektur eines
Docstrings**, keine Aenderung eines Verhaltens- oder Sollwerts. Die ergaenzende
Formulierung muss ausdruecklich benennen, dass `_e2e_config()` eine **abweichende**
Konfiguration benutzt und warum.

### 4.4 Neue Tests (Sollwerte, ausdruecklich benannt)

| # | Test | Sollwert |
|---|---|---|
| 1 | `test_index_owner_override_writes_in_a_ke_authoritative_project` | Live-Block + `index-owner: docs-consolidation` + `knowledge-engine.enabled: true` + `index.mode: knowledge-engine` ⇒ `plan == {"written": ["docs/INDEX.md"], "unchanged": [], "skipped": []}`; genau **eine** Action; **kein** `KE_AUTHORITATIVE_REASON` im Log; das geschriebene Dokument traegt `doc-indexer/1` **und** den `docs-facts`-Block (Beweis, dass `compute_doc_facts` betreten wurde — die entscheidende Unterscheidung zu einem „leeren" Lauf) |
| 2 | `test_index_owner_absent_keeps_the_ke_authoritative_block` | Dieselbe Config **ohne** den Key ⇒ `skipped` + `KE_AUTHORITATIVE_REASON`, Tree-Snapshot identisch. Pinnt die Absenz-Semantik |
| 3 | `test_unknown_index_owner_is_fail_closed` | `index-owner: "docs"` ⇒ `skipped` + `UNKNOWN_INDEX_OWNER_REASON`, **kein** Schreiben. Muster: `test_unknown_index_mode_is_fail_closed` (`:2720`) |
| 4 | `test_index_owner_override_does_not_relax_skeleton_or_ownership` | (a) Override + `index-mode: skeleton` ⇒ weiter `skipped` + `SKELETON_MODE_REASON`; (b) Override + `index-mode: full` + **fremde** Datei (kein Marker, keine Generator-ID) ⇒ weiter `skipped` + `OWNERSHIP_REASON`. **Das ist der Nachweis, dass die Ausnahme das Gate verengt, nicht die Besitzregel aufweicht.** |
| 5 | `test_index_owner_override_keeps_dry_run_free_of_writes` | `dry_run=True` ⇒ `written` enthaelt den Pfad, Action `WOULD-CREATE`, Tree-Snapshot identisch (IC-13/AC-23, Spec `:1325`) |
| 6 | `tests/test_docs_consolidation_migration.py`: Enum-Test | `["auto", "docs-consolidation"]` valide; alles andere inkl. `"knowledge-engine"`, `"agent-meta"`, `true` invalide |

### 4.4.1 Reihenfolge- und Konsistenzvertrag bleibt messbar

`test_stage_order_after_scaffold` (`:3013`) und `test_ke_index_stays_authoritative`
(`:3100`) fahren die **verdrahtete** Stage (`sync_pipeline.py:985`). Sie bleiben
unveraendert gruen, weil ihre Fixtures den Key nicht setzen. Ein **neuer** Test an der
verdrahteten Stage ist deshalb **nicht** zwingend, aber **empfohlen** (Billigvariante:
`test_ke_index_stays_authoritative` um eine zweite Fixture-Variante mit gesetztem Key
erweitern) — Entscheidung als **E-12** vorgelegt, nicht hier getroffen.

### 4.5 Nachweisformen

| Nachweis | Kommando | Soll |
|---|---|---|
| W3-6 Kernlieferung | `python3 scripts/sync.py --dry-run` (einmal), danach `python3 scripts/sync.py` | 1. Lauf `CREATE docs/INDEX.md`; 2. Lauf `unchanged`, **null** Actions |
| Drift-Baseline | `python3 scripts/sync.py --check` | **0** — sobald die Datei existiert, greift `DOCS_GENERATED_RELS` (`generated_file_drift.py:82`, Verdrahtung `:204-207`). Der Docstring dort (`:201`) sagt bereits voraus: „``docs/INDEX.md`` only arrives in W3-6" |
| Szenario-Regression | `bash tests/scenarios/run.sh 50 51 52 54 55 56` | **0** (bestehender Runner, keine neuen Dateien — AC-38, NG-10) |
| V2-Nachweis | `python3 scripts/sync.py --validate` | V2 **0**; `--validate` bleibt planmaessig **rot** ueber V3 (Plan `:4936-4937`) |
| tracked (OQ6) | `git check-ignore -q docs/INDEX.md; echo $?` | **1** (Plan `:4929`, `:4935`) |
| Schema | `tests/test_docs_consolidation_migration.py` (bestehender Test-Runner) | gruen inkl. neuem Enum-Test |
| Einheiten | `tests/test_doc_renderer.py` | gruen inkl. der 5 neuen Tests |

### 4.6 Geprueft und ausdruecklich **unveraendert**

| Artefakt | Pruefergebnis |
|---|---|
| `scripts/lib/consistency/docs_index.py:67-70` `V2_SUGGESTION` | bleibt richtig: nach der Ausnahme erzeugt der Generator die Datei tatsaechlich. **Keine Aenderung.** |
| `scripts/lib/knowledge.py:185-196` | liest `resolve_index_mode` unveraendert; KE schreibt weiter `knowledge/wiki/index.md` |
| `scripts/lib/generated_file_drift.py` | `docs/INDEX.md` ist bereits Baseline-Mitglied (`:82`, Schleife `:204-207`) — **keine Aenderung** |
| `scripts/lib/sync_pipeline.py:930-987` | Stage-Reihenfolge (B2) unveraendert |
| `tests/scenarios/configs/*.project.yaml` | **keine** Fixture wird angefasst (NG-10) |
| `config/agent-meta.config.example.yaml` | Zeile ergaenzt, kein Verhalten |

---

## 5. Offene Entscheidungsvorlagen

> **Nicht** entschieden. E-5 … E-8 sind laut Spec `:149` **ENTSCHIEDEN (Rev. 0.7, §17.11)**
> und werden hier **nicht** neu aufgerollt. E-1 … E-4 sind offen (Spec `:56`, `:149`) und
> betreffen andere Themen. Neue Vorlagen beginnen daher bei **E-9**. E-1 … E-4 werden
> **nicht** neu nummeriert oder verdraengt.

### E-9 — Wert des Keys: zweiwertiges Enum oder boolescher Override?

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-9a (Empfehlung)** | Enum `["auto", "docs-consolidation"]`, Default `auto` | Schema-Waechter greift; Tippfehler werden zu Validierungsfehlern; self-documenting |
| E-9b | Boolean `index-override: true`, Default `false` | kuerzer, aber ein **Negativname**; Tippfehler (`overide: true`) stiller No-op ⇒ der Wächter verliert seinen Zweck; spaeterer dritter Wert = breaking rename |
| E-9c | Enum `["auto", "knowledge-engine", "docs-consolidation"]` | symmetrisch, fuegt aber einen dritten blockierenden Eigentuem ein und widerspricht `:685-686` ⇒ **verworfen** (DECISION-2) |

**Empfehlung: E-9a.** **Wirkung auf W3-6/W3-7/W4:** bei E-9a **keine** Sollwert-Aenderung;
bei E-9b waeren die Tests 2–3 aus 4.4 auf einen Boolean umzuschreiben; W4 unberuehrt.

### E-10 — Reichweite: nur `docs/INDEX.md` oder auch die W3-7-Marker-Regionen?

**Sachstand (gemessen):** `apply_fact_blocks()` (`doc_renderer.py:183`) wird vom
KE-Gate **nicht** beruehrt. Ihre Gates sind `docs-consolidation.enabled`
(Common-Gate, `scripts/consistency-check.py:138`) und `docs-consolidation.sources`
(`IC-22`, Spec `:1538`), das in `.meta-config/project.yaml:398-401` **fehlt** (Default
`[]` = kein Rendering, NG-9). **W3-7 ist also durch dieses Gate nicht blockiert** — es
fehlt `sources`, nicht die Ausnahme.

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-10a (Empfehlung)** | `index-owner` gilt **ausschliesslich** fuer `docs/INDEX.md` | haelt den Aufgaben-Scope; W3-7 bleibt eigenstaendig |
| E-10b | Key = „der Doku-Generator besitzt alle generierten Doku-Artefakte" | erfordert Umbenennung (Key-Name waere falsch), skaliert `sources` mit, zieht W3-7 in den Scope |

**Empfehlung: E-10a.** **Wirkung:** W3-6 laeuft mit E-10a; W3-7 braucht in jedem Fall
`docs-consolidation.sources: [README.md, llms.txt, ARCHITECTURE.md]` — das ist eine
**eigene** Config-Zeile und **keine** Folge dieser Ausnahme. W4 unberuehrt.

### E-11 — Reicht der Key fuer `docs/architecture/INDEX.md` (W4-3)?

**Sachstand:** `docs/architecture/INDEX.md` steht in `DOCS_GENERATED_RELS`
(`generated_file_drift.py:82`), unterliegt aber **keinem** Mode-Gate — es gibt nur EINEN
Aufrufer von `_index_mode_block_reason`, den Index-Writer. W3-6 erzeugt die Datei
ausdruecklich nicht (Plan `:4931-4932`, Test `:3319-3320`).

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-11a (Empfehlung)** | Nichts aendern; in W4-3 **verifizieren**, nicht vorab entscheiden | W4-3 bleibt wie geplant |
| E-11b | W4-3 verlangt vorab eine Scope-Erweiterung des Keys | wuerde E-10 faktisch vorwegnehmen ⇒ **nicht** ohne E-10-Entscheidung |

**Empfehlung: E-11a.** **Wirkung:** W4-1 (von W3-6 abhaengig) und W4-3 unberuehrt.

### E-12 — Reicht eine Docstring-Korrektur, oder zwei Fixtures im AC-20-Test?

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-12a (Empfehlung)** | Docstring korrigieren **und** den neuen Test aus 4.4 Nr. 1 als zweites Fixture danebenstellen; `_e2e_config()` nicht umbauen | Test bleibt bei seiner Aussage; neue Aussage kommt additiv dazu |
| E-12b | `_e2e_config()` umbauen, sodass es beide Modi durchlaeuft | ein Test mit zwei Verhaltensweisen ⇒ schwerer zu diagnostizieren, und der Skeleton-Fall verliert seinen eigenen Namen |
| E-12c | zusaetzlich ein Test an der **verdrahteten** Stage (`sync_pipeline.py:985`) | staerkerer Nachweis (Stellenwert: `test_ke_index_stays_authoritative` `:3100` argumentiert genau damit); Kosten: ein weiterer Test |

**Empfehlung: E-12a**, mit E-12c als moeglicher Erweiterung. **Wirkung:** W3-6 Testaufwand
unveraendert; W4 unberuehrt.

### E-13 — Dokumentationspflicht: wer traegt Schema-/Beispiel-/Admin-UI-Eintrag?

| Option | Beschreibung | Auswirkung |
|---|---|---|
| **E-13a (Empfehlung)** | W3-6: `project.yaml`-Zeile + `agent-meta.config.example.yaml`; W8-4: Schema-Abschluss und Doku | verteilt die Pflicht auf die Wellen, die ohnehin `.meta-config/project.yaml` bzw. den Schema-Stand besitzen |
| E-13b | alles in W3-6 | W3-6 waere groesser als geplant; beruehrt `admin-ui`-Belange (fremde Welle) |

**Empfehlung: E-13a.** **Wirkung:** W3-6 +1 Beispielzeile; W4 unberuehrt; W8-4 ggf. ein
zusaetzlicher Punkt in dessen Files-Liste (Plan-Änderung, keine Spec-Änderung).

### Ausdruecklich **keine** offene Frage

| Thema | Feststellung |
|---|---|
| `facts-hash`-Churn durch den neuen Key | Der Key fliesst **nicht** in `compute_doc_facts()` ein ⇒ **kein** Churn, **kein** AC. Festgehalten, damit es nicht erneut aufgerollt wird. |
| OQ1 (Wiki-Topics ↔ `docs/guides/`) | Bleibt **offen**, Owner `main_chat` (`…-oq1.md:94`). Dieser Entwurf beruehrt `knowledge/wiki/**` nicht; die Ausnahme hat **keinen** Einfluss auf OQ1 und hebt dessen W5-Blockade **nicht** auf. |
| OQ8 | **ENTSCHIEDEN** (Sync/Validator-Lauf, kein Hook, Spec `:2516`) — von W3-6 Schritt 2 umzusetzen, hier nicht neu bewertet. |
| OQ6 | **ENTSCHIEDEN** (`tracked`, kein `.gitignore`-Eintrag, Spec/Plan) — W3-6, hier nicht neu bewertet. |

---

## 6. Verdictschnitt

### 6.1 Inhaltliche Pflichtaenderung der APPROVED-Spec → **User-Freigabe erforderlich**

| ID | Stelle | Warum eine Pflichtaenderung |
|---|---|---|
| **P-1** | **IC-13**, Spec `:1319` | Die Tabellenzeile lautet woertlich absolut: „`resolve_index_mode(config)[0] == "knowledge-engine"` ⇒ **kein** `docs/INDEX.md` schreiben". Der Entwurf fuegt eine bedingte Ausnahme ein und aendert damit das Verhalten bei `enabled: true` + KE an. **Kein** Formulierungsfehler — ein neuer Vertrag. |
| **P-2** | **IC-15**, Spec `:1363-1367` | IC-15 nennt als Bedingungen der Skeleton-Uebernahme u. a. „`resolve_index_mode() == "file-index"`". In agent-meta entsteht der Index **ohne** Skeleton (Neuanlage). IC-15 regelt nur den Skeleton-Fall und wird dadurch nicht falsch, aber **unvollstaendig**. |
| **P-3** | **IC-22** Config-Tabelle, Spec `:1533-1540`, `:1550` | Die Tabelle enumeriert sechs Keys und der Absatz spricht von „**allen sechs** Keys". Ein siebter Key (`index-owner`) kommt hinzu; ebenso der Zaehlkommentar `tests/test_docs_consolidation_migration.py:42` („IC-22 enumerates six rows; five of them are `docs-consolidation.*`"). |
| **P-4** | **AC-21**, Spec `:1904-1910` | Der zweite Given/When/Then-Block macht die KE-Autoritaet zur **ungefuehrten** Vorbedingung. Mit der Ausnahme ist er **bedingt**, also braucht es ein **zusaetzliches AC** fuer den Override-Pfad (sonst widerspricht der Test der Spez). |
| **P-5** | **R7** (B2-Doppel-Writer), Spec `:2498` | Die Mitigation listet zwei Hebel (`is_file_index_skeleton`, Stage-Reihenfolge) plus Besitzregel und `index-mode: skeleton`. Ein **dritter** Hebel kommt hinzu. Die Risikozeile bleibt in Substanz richtig (das Risiko selbst sinkt in agent-meta), aber die normative Mitigation-Tabelle aendert sich. |

**Was P-1 bis P-5 gemeinsam ist:** Sie betreffen ausschliesslich **normative** Stellen
(IC-Vertrag, Config-Tabelle, Akzeptanzkriterium, Risikotabelle). Keine davon ist eine
Korrektur eines versehentlichen Fehlers. Sie gehoeren in eine **Spec-Revision mit
Bump** (Rev. 0.8), nicht in eine stille Korrekturrunde.

### 6.2 Korrektur bestehender Formulierung → **keine Freigabe**, aber zu benennen

| ID | Stelle | Art |
|---|---|---|
| **K-1** | `doc_renderer.py:669-672` (Docstring) | „Scenario 52 asserts no `docs/INDEX.md` is written there … so the generator has nothing to do **in that project**" — gilt fuer agent-meta ab C2 nicht mehr. Reiner Text, **kein** Verhalten. |
| **K-2** | `tests/test_doc_renderer.py:3209-3223` (`_e2e_config`-Docstring) | Siehe 4.3. Reiner Text; der Test-Sollwert bleibt (4.2). |
| **K-3** | `tests/test_docs_consolidation_migration.py:42` | Zaehlkommentar „six rows / five of them" → sieben / sechs. Reiner Kommentar. |
| **K-4** | Spec `:1302-1304` (Zeilenanker `spec_plan_scaffold.py:62-68`) und Spec `:1319`, `:1915` (`:40-44`) | **Veraltete Zeilenanker**, unabhaengig von dieser Aenderung: real sind `spec_plan_scaffold.py:115-121` bzw. `:80-97`. Nachweis: `scaffold_spec_plan_dirs` beginnt bei `:100` und der Modus-Zweig bei `:115-116`; `resolve_index_mode` beginnt bei `:80`. |
| **K-5** | `doc_renderer.py:685-686` („the complete list of what forbids a write") | **Bleibt wortwoertlich stehen** — DECISION-2 haelt die Liste geschlossen. Ausdruecklich als *nicht* zu aendern vermerkt, damit der Guard nicht als Widerspruch missverstanden wird. |

### 6.3 Kein Eingriff (bleibt bewusst unangetastet)

`resolve_index_mode()` · `is_file_index_skeleton()` · `_FILE_INDEX_SKELETON*` ·
`knowledge.py` · `doc_index.py` · `generated_file_drift.py` · `sync_pipeline.py` ·
`consistency/docs_index.py` (V2-Text) · alle Szenario-Fixtures und -Asserts ·
`providers`-/`platforms`-Konfiguration · `config/ai-providers.yaml` ·
`config/provider-capabilities.yaml`.

---

## 7. Zusammenfassung der Nachweise

| Aussage dieses Dokuments | Nachweisform |
|---|---|
| W3-6 scheitert an `doc_renderer.py:702` | Zitat 1.2 + Aufloesungskette 1.3 (`:69`, `:77`, `:15`) |
| `docs/INDEX.md` existiert nicht | Glob ohne Treffer |
| Die Ausnahme enthaelt keinen agent-meta-Bezug im Code | Diff-Grenze 4.1: eine Code-Datei, eine Bedingung, ein Config-Wert |
| Consumer bleiben unberuehrt | Fehlender `docs-consolidation`-Key in allen Fixtures (Spec `:1553-1557`) + 6 Sollwert-Tests aus 4.2 |
| Die B2-Invariante bricht nicht | `spec_plan_scaffold.py:115-116` schreibt im KE-Modus nichts; Stage-Reihenfolge `sync_pipeline.py:980 → :985` unveraendert |
| Die KE-Autoritaet fuer Consumer bleibt | `knowledge.py:185-196` unveraendert; Szenario 52 (`asserts/52:44`) unveraendert |

---

**Offener Stand:** Die Ausnahme ist **fachlich entworfen**, aber **noch nicht
freigegeben**. Vor der Umsetzung von W3-6 sind P-1 bis P-5 (Kapitel 6.1) mit dem
Nutzer zu klaeren; E-9 bis E-13 (Kapitel 5) sind Entscheidungsvorlagen mit Empfehlung,
**keine** Festlegungen.
