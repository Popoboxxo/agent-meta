# A2A Best-Practice-Analyse — Update 2026-08-07

> Baut auf: [a2a-handoff-protocol.md](a2a-handoff-protocol.md), [a2a-best-practice-analysis.md](a2a-best-practice-analysis.md) (2026-06-07)
> Fokus dieses Updates: (1) was sich extern seit Juni geändert hat, (2) verifizierter Ist-Zustand (Code, nicht Doku), (3) Handlungsempfehlungen.
> Methode: Code-Audit (`grep`/`Read` gegen `scripts/lib/`, `config/`, `agents/`, `.meta-config/project.yaml`) + externe Recherche (WebSearch, Stand 2026-08-07).

---

## 1. Kernaussage

Das Juni-Konzept ist inhaltlich **weiterhin state-of-the-art** — TaskSpec-Kern-Schema, 4 Extensions, Supersession-Tracking und Provider-Agnostizismus sind laut aktueller externer Recherche eher voraus als hinterher (siehe §2). Das eigentliche Risiko liegt nicht in der Spezifikation, sondern in einer **Lücke zwischen Deklaration und Durchsetzung**: mehrere Config-Flags behaupten ein Verhalten, das im Code nicht existiert (§3). Das ist gefährlicher als eine fehlende Optimierung, weil es einen falschen Sicherheitseindruck erzeugt.

**Kurzantwort auf "ist das noch gut genug?"**: Das *Protokoll* ja. Die *Durchsetzung* nein — dort liegt der Hebel.

---

## 2. Was sich extern seit Juni geändert hat

### 2.1 Googles echtes "A2A" (Agent2Agent) Protokoll — nicht zu verwechseln mit agent-meta's interner Namensgebung

Namenskollision: Google/Linux Foundation betreiben seit April 2025 ein eigenes, gleichnamiges "A2A"-Protokoll (jetzt v1.0, >150 Organisationen, Production-Einsatz bei Google/Microsoft/AWS). agent-meta's A2A ist unabhängig entstanden und verfolgt ein anderes Ziel (interne Rollen-Delegation in einem Repo, nicht Cross-Vendor-Agent-Interop).

**Relevante v1.0-Neuerungen, keine davon ist für agent-meta direkt anwendbar:**
- Signed Agent Cards (Domain-Ownership-Verifikation) — löst ein Problem (fremde, nicht vertrauenswürdige Agenten), das agent-meta nicht hat (alle Rollen sind im selben Repo definiert).
- Multi-Tenancy (ein Endpoint, mehrere Agenten) — irrelevant, agent-meta hat keine Netzwerk-Endpoints.
- Client-Remote-Modell mit Opaque Agents (kein Einblick in fremde interne Logik) — agent-meta braucht das Gegenteil (alle Rollen sind Klartext-Markdown im selben Repo).

**Fazit:** Namensgleichheit ist rein zufällig, keine Handlungsrelevanz. Falls das je verwirrt (z.B. bei Doku für Externe), lohnt eine Umbenennung von "A2A" auf einen repo-eigenen Namen (z.B. "AMHP" — agent-meta Handoff Protocol) — kein Bug, aber ein Klarheits-Punkt.

### 2.2 Anthropic: "Effective context engineering for AI agents" (2026)

Kernaussage: *"find the smallest set of high-signal tokens that maximize the likelihood of your desired outcome"* — nicht die meisten Tokens, die richtigen. Subagenten sollen intern beliebig viel explorieren (zehntausende Tokens), aber nur eine **komprimierte Zusammenfassung von 1.000–2.000 Tokens** zurückgeben.

Abgleich mit agent-meta: `.claude/rules/a2a-delegation-gates.md` Punkt 5 ("Execution-Trace-Isolation: Worker-Output muss strukturiert sein... keine rohen Logs propagieren") und `orchestrator.md`'s Artifact-Pattern (">200 Zeilen → Referenz statt Inhalt") treffen genau diese Empfehlung. **Bereits umgesetzt, keine Änderung nötig.**

### 2.3 Anthropic: "Effective harnesses for long-running agents" (2026)

Kernpunkte:
- Git-Commits + Progress-Files als Session-Übergabe-Mechanismus, nicht Context-Compaction allein.
- **JSON statt Markdown für State-Dateien** — Modelle verändern/überschreiben JSON seltener versehentlich als Markdown.
- Explizite "DO NOT edit" Guards für unveränderliche Zustandsteile (z.B. Test-Listen).

Abgleich: agent-meta nutzt für Session-Übergabe primär `.superpowers/sdd/progress-*.md` (Markdown) und Honcho-Memory, nicht JSON. Das ist ein echter, aber kleiner Diskrepanzpunkt — nicht A2A-Envelope-relevant (das betrifft Human↔Agent- bzw. Session↔Session-Übergabe, nicht Agent↔Agent-Delegation), daher hier nur als Randnotiz, kein Handlungsbedarf im A2A-Scope.

### 2.4 Industrie-Konsens 2026 (mehrere Quellen: LangChain, Beam, Medium-Produktionsberichte)

- **"Orchestrator + isolierte Subagenten mit Summary-Rückgabe"** hat sich branchenweit als Standardmuster durchgesetzt (Anthropic, Cognition, OpenAI, AutoGen, LangChain). **agent-meta folgt exakt diesem Muster** (Singleton-Orchestrator, kein Peer-to-Peer).
- **Multi-Agent verbrennt ~15× mehr Tokens als Chat** (Anthropic 2025) — Token-Spend erklärt ~80% der Performance-Varianz. Bestätigt die Juni-Analyse's Fokus auf Token-Effizienz als *richtige* Priorität, nicht Nice-to-have.
- **OpenAI Agents SDK (April 2026 Update):** verschachtelte Handoff-Historie ist jetzt standardmäßig **opt-in** statt opt-out — explizit um Cross-Agent-Context-Bleed zu reduzieren. Deckt sich 1:1 mit agent-meta's bereits vorhandenem `.claude/rules/conventions.md`-Konzept "Instruction Bleed" (arXiv:2606.26356, bereits zitiert) und den A2A-Gates. **Kein neuer Handlungsbedarf, nur Bestätigung des bestehenden Designs.**
- **"Keep an arbiter"**: jedes überlebende Multi-Agent-System 2026 hat Phase-Gates, geteilte Artefakte oder einen finalen Supervisor. agent-meta's Singleton-Orchestrator + BARRIER-Gates erfüllen das.

**Zusammenfassung §2:** Keine der 2026-Entwicklungen verlangt eine Kurskorrektur am *Design*. Die externe Literatur bestätigt drei zentrale Juni-Entscheidungen (Orchestrator-Singleton, komprimierte Rückgaben, Token-Fokus) und liefert keinen Grund, das Envelope-Format, Draft-07 oder die TaskSpec-Strategie zu ändern.

---

## 3. Verifizierter Ist-Zustand (Code-Audit, nicht Doku-Stand)

Der Juni-Report hat einen Maßnahmenkatalog (Phase 1–3) vorgeschlagen. Direkt im Code geprüft, was davon tatsächlich läuft:

| # | Maßnahme (Juni-Report) | Status | Beleg |
|---|---|---|---|
| 1 | TaskSpec-Kern-Schema | ✅ Umgesetzt | `schemas/handoffs/task-spec.schema.json` |
| 2 | Kurze Payload-Feldnamen (t/ctx/con/refs/pri/dep) | ✅ Umgesetzt | `use-orchestrator.md`, `a2a-delegation-gates.md` |
| 6 | 4 TaskSpec-Extensions (Ideation/Design/API/Review) | ✅ Umgesetzt | `schemas/handoffs/ext/*.schema.json` |
| 10 | A2A-Event-Typen in viz-logger | ✅ Umgesetzt | `scripts/lib/viz.py:801-818` |
| 3 | `orchestrator.handoff`-Config-Block | ✅ Vorhanden | `.meta-config/project.yaml:270-273` |
| 9 | `schema_ref` implizit ableiten (Token-Ersparnis) | ⚠️ Unklar | kein Code-Treffer für "implizite Ableitung"; vermutlich weiterhin explizit |
| — | `validate-before-delegate: true` (Config) | ❌ **Nicht durchgesetzt** | `validate_envelope()` in `scripts/lib/delegation_syntax.py:152` existiert, wird aber **nirgends aufgerufen** — 0 Treffer für `validate_envelope(` außerhalb der eigenen Definition |
| — | `compact-mode: true` (Config) | ❌ **Nicht durchgesetzt** | 0 Code-Treffer für `compact_mode`/`compact-mode` außerhalb `.meta-config/project.yaml` und dem JSON-Schema — das Flag wird nirgends gelesen |
| 8 | FANOUT/BARRIER/PIPELINE mit A2A-Envelopes (gemeinsame `trace_id`, Response-Envelopes) | ❌ **Nicht umgesetzt** | `orchestrator.md`'s tatsächliche FANOUT/BARRIER-Beschreibung (Zeilen 64–96) nutzt Klartext-Format `"[task] → [agent] (reason)"` / `"[agent]: [result]. Next: [...]"` — kein `trace_parent`, kein `handoff_id` in der operativen Kommunikation |
| 5 | Payload-Feldnamen-Checkliste in `howto/` | ❌ Nicht gefunden | kein Treffer für `*handoff*`/`*a2a*` unter `howto/` |
| 12 | Response-Envelopes (Worker→Orchestrator) | ❌ Nicht umgesetzt (war Phase 3, erwartbar) | kein Treffer für `response_handoff` |
| 1 (Gates) | `validate_envelope(max_depth=...)`-Tiefenlimit | ⚠️ Bekannt & dokumentiert als Lücke | `a2a-delegation-gates.md` selbst benennt das bereits ehrlich als "modellbasiert, keine technische Barriere" |

### 3.1 Der wichtigste Einzelfund: zwei parallele, nicht verzahnte Delegationsstile

`use-orchestrator.md` deklariert das A2A-IEnvelope/IPayload-Format als *das* Protokoll ("A2A-Envelopes verwenden..."). Die tatsächliche, im selben Template beschriebene FANOUT/BARRIER-Mechanik — also das, was der Orchestrator im Alltag wirklich tut — läuft über ein simples Klartext-Muster ohne jede Envelope-Struktur. Das ist nicht zwangsläufig ein Bug (das Klartext-Muster ist token-günstiger für den Normalfall, das JSON-Envelope eher für Fälle mit echtem Schema-Bedarf wie SE-Kaskade gedacht) — aber es ist **nirgends explizit dokumentiert, wann welches Format gilt**. Ein Agent, der `use-orchestrator.md` liest, bekommt zwei Beispiele, die sich nicht offensichtlich zueinander verhalten.

### 3.2 Konfiguration, die lügt

`validate-before-delegate: true` und `compact-mode: true` stehen seit mindestens dem 1. August in `.meta-config/project.yaml` (siehe `.bak`-Dateien). Beide Flags suggerieren aktives Verhalten, das der Code nicht liefert. Das ist strukturell derselbe Fehlerklasse wie die bereits gefixten Bugs #429/#432 dieser Session: **eine Erwartung, die durch Konfiguration erzeugt, aber vom Code nicht eingelöst wird.**

---

## 4. Priorisierte Empfehlungen

| # | Empfehlung | Aufwand | Begründung |
|---|---|---|---|
| 1 | **`validate_envelope()` real in den Delegationspfad einhängen** — oder wenn technisch (noch) nicht möglich: `validate-before-delegate` aus `project.yaml` entfernen bzw. auf `false` setzen und die Doku entsprechend korrigieren. | Mittel (Hook-Integration) / Gering (Doku-Fix als Sofortmaßnahme) | Config-Lüge schließen — höchste Priorität, da sie einen falschen Sicherheitseindruck erzeugt |
| 2 | **`compact-mode` entweder implementieren (Payload-Feldnamen wirklich kürzen) oder aus der Config entfernen.** | Gering | Gleiche Fehlerklasse wie #1, kleinerer Impact (nur Tokens, keine Sicherheit) |
| 3 | **Explizit dokumentieren, wann Klartext-FANOUT/BARRIER gilt vs. wann ein echtes A2A-Envelope nötig ist** (z.B. ein Satz in `use-orchestrator.md`: "Envelopes nur bei SE-Kaskade / schema-pflichtigen Routen, sonst Klartext-Kurzform"). | Gering (Doku) | Beseitigt die in §3.1 gefundene Zweideutigkeit ohne Codeänderung |
| 4 | **Namenskonflikt mit Googles echtem A2A-Protokoll vermerken** (ein Satz in `a2a-handoff-protocol.md`: "kein Bezug zu Google/Linux Foundation A2A v1.0"). | Trivial | Vermeidet zukünftige Verwechslung bei Onboarding/Doku-Suche |
| 5 | **Response-Envelopes (Worker→Orchestrator) bleiben bewusst zurückgestellt** (Phase 3, wie im Juni-Report). | — | Kein Handlungsbedarf jetzt — externe Recherche bestätigt keinen Zeitdruck hierfür |

**Nicht empfohlen:** Envelope-Format, Draft-07, TaskSpec-Struktur oder Supersession-Mechanik ändern — all das ist durch die 2026-Außensicht bestätigt, nicht widerlegt.

---

## 5. Umsetzung (2026-08-07)

Bei der Umsetzung der Empfehlungen 1–4 stellte sich heraus, dass die Config-Lüge größer war als zunächst gefunden: von 8 Feldern im `orchestrator.handoff:`-Block in `.meta-config/project.yaml` hatte **nur `protocol` einen echten Konsumenten** — 5 der 8 waren nicht mal im JSON-Schema (`config/project-config.schema.json`) deklariert, sondern liefen unbemerkt über `additionalProperties: true` durch. Auf Nutzerwunsch ("wenn wir das Konzept verkomplexiert haben bitte melden und kürzen") wurde entsprechend breiter gekürzt statt nur die 2 ursprünglich gefundenen Flags zu fixen:

| Empfehlung | Entscheidung | Details |
|---|---|---|
| 1. `validate_envelope()` einhängen | **Nicht eingehängt, Config entfernt.** | Kein technischer Interception-Punkt vorhanden: der Orchestrator dispatcht Subagenten über den `Agent`-Tool-Call, nicht über einen Python-Layer. `orchestrator-guard.sh` (der einzige PreToolUse-Hook, der auf *alle* Tools läuft) prüft laut eigenem Code-Kommentar nur `Write`/`Edit`/`Bash` — für `Agent`-Calls gibt es keine Payload-Identität, an der ein Hook ansetzen könnte. `validate_envelope()` bleibt als getestetes, manuell aufrufbares Utility erhalten (10 neue Tests in `tests/test_delegation_syntax.py`). |
| 2. `compact-mode` | **Entfernt** (Config + Schema + Doku). | TaskSpec-Felder sind immer kurz, es gab nie einen zweiten Zustand zum Umschalten. |
| 3. Klartext-vs-Envelope verzahnen | **Umgesetzt.** | `snippets/orchestrator/a2a-protocol.md` behauptete zuvor "Jede Delegation MUSS als strukturiertes A2A-Envelope erfolgen" — im Widerspruch zur tatsächlichen FANOUT/BARRIER-Praxis in `orchestrator.md` (Klartext `"[task] → [agent] (reason)"`). Neue Regel: Envelope ist nur Pflicht, wenn `role-defaults.yaml`'s `handoff.input_schema`/`output_schema` auf eine echte Schema-Datei zeigt (TaskSpec + 4 Extensions + SE-Schemas); sonst gilt das normale Klartext-Format. Gleiche Klarstellung in `A2A_HANDOFF_BLOCK` (`scripts/lib/config.py`). |
| 4. Google-Namenskollision vermerken | **Umgesetzt.** | Hinweis im Kopf von `a2a-handoff-protocol.md`. |

**Zusätzlich gefunden und mitgekürzt** (gleiche Fehlerklasse: spezifiziert, aber nie konsumiert — weder in Code noch in Agent-Prompt-Text):
- Retry-Logik (`retry_count`, `max_retries`, `escalation`, `timeout_seconds`) — komplett aus `schemas/a2a-handoff.schema.json` entfernt, inkl. der beiden Doku-Abschnitte dazu in `a2a-handoff-protocol.md` (§10, §11 alt).
- `negotiated_format` (dynamisches Protocol-Routing) — Transport-Format wird tatsächlich statisch aus `config/provider-capabilities.yaml` gelesen, nie dynamisch verhandelt.
- 3 ungenutzte JSON-Schema-`definitions` (`handoffRoute`, `agentContract`, `handoffRegistry`) — nirgends per `$ref` referenziert.
- `config/project-config.schema.json`s `handoff`-Block hat jetzt `additionalProperties: false` statt `true` — verhindert, dass zukünftig wieder unbemerkt Config-Felder ohne Konsumenten einschleichen (genau das ist bei 5 der 8 jetzt entfernten Felder passiert).

**Bewusst NICHT entfernt** (haben echte Konsumenten, wenn auch nur auf Prompt-Ebene — konsistent mit dem restlichen, prompt-basiert durchgesetzten Framework, nicht mit Code-Enforcement zu verwechseln): `requires_human_approval` (Envelope-Feld, referenziert in `developer.md`/`orchestrator.md`/`_reference-agent.md`), `supersession`/`trace_parent`/`trace_context` (referenziert in den SE-Kaskade-Rollen), `batch` (FANOUT-Konzept).

**Ergebnis:** `docs/concepts/a2a-handoff-protocol.md` von 887 auf 812 Zeilen (2 volle Abschnitte entfernt, 15→13 Abschnitte); `schemas/a2a-handoff.schema.json` von 257 auf ~180 Zeilen; `.meta-config/project.yaml`s Handoff-Block von 14 auf 2 Zeilen.

---

## Quellen (externe Recherche, 2026-08-07)

- [A year of open collaboration: Celebrating the anniversary of A2A (Google Open Source Blog)](https://opensource.googleblog.com/2026/04/a-year-of-open-collaboration-celebrating-the-anniversary-of-a2a.html)
- [A2A Protocol Surpasses 150 Organizations (Linux Foundation)](https://www.linuxfoundation.org/press/a2a-protocol-surpasses-150-organizations-lands-in-major-cloud-platforms-and-sees-enterprise-production-use-in-first-year)
- [Effective context engineering for AI agents (Anthropic)](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Effective harnesses for long-running agents (Anthropic)](https://www.anthropic.com/engineering/effective-harnesses-for-long-running-agents)
- [How and when to build multi-agent systems (LangChain)](https://www.langchain.com/blog/how-and-when-to-build-multi-agent-systems)
- [6 Multi-Agent Orchestration Patterns for Production 2026 (Beam)](https://beam.ai/agentic-insights/multi-agent-orchestration-patterns-production)
- [Multi-Agent in Production in 2026: What Actually Survived (Medium)](https://medium.com/@Micheal-Lanham/multi-agent-in-production-in-2026-what-actually-survived-f86de8bb1cd1)
