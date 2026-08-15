# Konzept: Multi-Provider-Test-Suite für Orchestrator-Intent-Routing

> Status: **Konzept-Entwurf v1.1** | 2026-08-15
> Ziel: Die kanonische Intent-Routing-Tabelle (generiert aus `config/role-defaults.yaml` → `quality_pipelines[*].signal_keywords`) über echte LLM-Sessions gegen Claude, Opencode und (bedingt) Antigravity/Gemini testen — nicht nur gegen Claude wie bisher.

---

## 1. Kontext & Motivation

Mit PR #497 (`.experiments/promptfoo-routing-eval/`, gemerged) existiert ein funktionierender Proof-of-Concept: 17 Testfälle, die eine echte `claude -p`-Session mit dem tatsächlich generierten `.claude/rules/use-orchestrator.md` als System-Prompt konfrontieren und prüfen, ob die richtige Pipeline (`bugfix`, `quick-fix`, `feature-lifecycle`, `concept-development`, `refactor`, `docs-update`, `none`) erkannt wird. Weil die `promptfoo`-CLI im Sandbox nicht installierbar war, existiert zusätzlich ein Bash-Fallback-Runner (`run_eval.sh`) mit identischer Testfall-Menge, `repeat=3` zur Flakiness-Erkennung und exakten Ein-Wort-Match-Assertions.

**Der Beweis, dass die Methode funktioniert, liegt bereits vor:** Issue #498 wurde durch genau dieses PoC real gefunden — ein Recherche-Keyword führte zu einer Falschklassifikation von Erklärfragen. Das ist kein hypothetischer Nutzen, sondern ein bereits eingetretener.

**Die Lücke:** Der PoC deckt ausschließlich Claude ab. Die kanonische Routing-Tabelle wird aber in vier Provider-Dateien identisch eingebettet (`.claude/rules/use-orchestrator.md`, `.opencode/agents/orchestrator.md`, `.gemini/agents/orchestrator.md`, `.mammouth/agents/orchestrator.md`) — mit fundamental unterschiedlichem Einbettungs- und Aktivierungskontext pro Provider (siehe Abschnitt 4.2). Ein Test, der nur bei Claude läuft, sagt nichts darüber aus, ob dieselbe Tabelle bei Opencode oder Antigravity genauso zuverlässig funktioniert.

## 2. Abgrenzung zu bestehenden Tests

Es gibt bereits `tests/orchestration/` mit einer deterministischen `OrchestratorDryRun`-Engine (`tests/orchestration/dry_run/engine.py`) plus Provider-Syntax-Fixtures (`tests/orchestration/fixtures/providers/*.yaml`). Diese Suite ist wichtig, deckt aber eine andere Fehlerklasse ab:

| | `tests/orchestration/` (bestehend) | Diese Test-Suite (Konzept) |
|---|---|---|
| Mechanismus | Hartcodierter Python-`INTENT_MAP` (Keyword→Agent), simuliert Entscheidungen | Echter LLM-Call gegen die tatsächlich generierte Datei |
| Liest reale Templates? | Nein — eigene, vereinfachte Keyword-Liste, unabhängig von `role-defaults.yaml` | Ja — genau die Datei, die `sync.py` tatsächlich ausrollt |
| Kosten/Determinismus | Kostenlos, deterministisch, läuft in jedem `pytest`-Lauf | Kostet LLM-Calls, nicht-deterministisch (daher `repeat=3`) |
| Erkennt | Logikfehler in der Simulation selbst, Syntax-Regeln (FANOUT/PARALLEL_GROUP) | Ob der reale Modell-Prompt-Text die reale Zielentscheidung auslöst — inkl. Drift zwischen `role-defaults.yaml` und Rendering (siehe Issue #498) |
| Pipeline-Ebene | Nein (nur einzelne Agenten wie `developer`, `tester`) | Ja — genau die Pipelines, die tatsächlich in `.claude/rules/use-orchestrator.md` gerendert werden (aktuell 6, siehe Filterkriterium in Abschnitt 4.1) |

**Empfehlung:** Beide Suiten bewusst getrennt halten (unterschiedliche Kostenklasse, unterschiedlicher Zweck), nicht zusammenführen. Diese Entscheidung sollte der Projekt-Owner bestätigen (siehe Abschnitt 7).

## 3. Ziel & Nicht-Ziele

### Ziel

- Testfall-Katalog für die Intent-Routing-Tabelle, der die tatsächlich in `.claude/rules/use-orchestrator.md` gerenderten Pipelines abdeckt — aktuell 6 (`bugfix`, `quick-fix`, `feature-lifecycle`, `concept-development`, `refactor`, `docs-update`), ermittelt über den in Abschnitt 4.1 beschriebenen Filter (nicht "alle `quality_pipelines`-Einträge mit `signal_keywords`" — das wären 7, siehe dort) — plus Negativ-/Ambiguitäts-Fälle.
- Katalog teilweise automatisch aus `config/role-defaults.yaml` ableitbar (Basis-Keyword-Abdeckung, nie vergessbar bei Tabellenänderung), teilweise manuell gepflegt (harte Fälle).
- Provider-Wrapper für Claude (Baseline, bereits vorhanden) und Opencode (neu).
- Für Antigravity/Gemini: ein **expliziter Verifikationsschritt**, ob und wie ein headless-Testpfad überhaupt existiert — vor jeglicher Wrapper-Implementierung.
- Ein Testfall-Typ speziell für das **Doppel-Tabellen-Drift-Risiko** bei Opencode/Gemini (siehe Abschnitt 4.3).

### Nicht-Ziele (bewusst außerhalb dieses Konzepts)

- **Volle Antigravity-Integration ist NICHT garantiert** — falls der Aktivierungspfad-Blocker sich bestätigt (kein CLI-Zugriff auf die generierte Datei außerhalb der IDE), wird das als dokumentierte Lücke akzeptiert, nicht erzwungen.
- **Mammouth** — strukturell analog zu Opencode/Gemini (Doppel-Tabelle), aber nicht Teil des ursprünglichen Auftrags. Kann später per Analogie ergänzt werden, hier nicht geplant.
- **promptfoo-CLI-Installation** — bleibt ungelöst (Sandbox-Limitierung). Der Bash-Fallback-Runner ist die dauerhafte Lösung, nicht nur ein Übergangs-Workaround.
- **Auflösung des Doppel-Tabellen-Problems selbst** (Zusammenführen von §2 „Pipeline match check" und §3 „Intent routing" in `orchestrator.md`) — dieses Konzept deckt nur die *Erkennung* per Test ab, nicht den Architektur-Fix. Falls der Drift-Test tatsächlich fehlschlägt, wird das als eigener Findings-Kandidat/Issue vorgeschlagen (Abschnitt 7).
- **Vereinheitlichung mit `tests/orchestration/`** — bewusst getrennte Suite (siehe Abschnitt 2).
- **`se-cascade`-Pipeline** — hat ebenfalls `signal_keywords` in `role-defaults.yaml`, wird aber unter der Standardkonfiguration von agent-meta (`se-focus: false`, siehe Abschnitt 4.1) nicht in der Intent-Routing-Tabelle gerendert und ist daher nicht Teil dieses Katalogs. Falls `se-focus: true` gesetzt wird, müsste der Katalog das separat berücksichtigen — hier nicht geplant.

## 4. Architektur-Vorschlag

### 4.1 Testfall-Katalog: Hybrid aus generiert + manuell

**Filterkriterium — welche Pipelines landen überhaupt in der Tabelle?**

`config/role-defaults.yaml` → `quality_pipelines:` enthält **7** Einträge mit `signal_keywords` (`feature-lifecycle`, `quick-fix`, `bugfix`, `concept-development`, `refactor`, `docs-update`, `se-cascade` — verifiziert `config/role-defaults.yaml:1413-1704`). Die gerenderte Tabelle in `.claude/rules/use-orchestrator.md` hat aber nur **6** Zeilen — `se-cascade` fehlt. Das ist kein Zufall, sondern ein expliziter Filter in `scripts/lib/config.py:783-787`:

```python
se_focus = bool(config.get("se-focus", False))
if not se_focus:
    effective = {k: v for k, v in effective.items()
                 if not k.startswith("se-")}
```

Jede Pipeline, deren Name mit `se-` beginnt, wird aus `effective` entfernt, außer das Projekt setzt `se-focus: true` in `.meta-config/project.yaml`. agent-metas eigene Konfiguration hat `se-focus: false` (`.meta-config/project.yaml:331`) — daher fehlt `se-cascade`. Das gefilterte `effective`-Dict wird danach an `get_intent_routing_table()` (`scripts/lib/delegation_table.py:51-108`) übergeben, die pro verbleibender Pipeline mit nicht-leeren `signal_keywords` genau eine Tabellenzeile rendert.

**Der geplante Katalog-Generator MUSS diesen Filter replizieren:** `quality_pipelines` laden → Projekt-Overrides anwenden (`apply_overrides`) → alle `se-`-präfigierten Pipelines entfernen, sofern nicht `se-focus: true` → nur Pipelines mit nicht-leeren `signal_keywords` behalten. Nur so bleibt der generierte Katalog deckungsgleich mit der real gerenderten Tabelle statt mit der YAML-Rohliste. Wo in diesem Dokument von "6 Pipelines" die Rede ist, ist damit **nicht** eine feste Zahl gemeint, sondern das Ergebnis dieses Filters zum jeweiligen Zeitpunkt — aktuell 6, kann sich ändern (z. B. bei `se-focus: true` oder neuen `quality_pipelines`-Einträgen).

**Kollisionsregel — geteilte `signal_keywords` zwischen Pipelines:**

`Bug fixen` und `Bug beheben` sind `signal_keywords` sowohl bei `bugfix` (`config/role-defaults.yaml:1491-1494`) als auch bei `quick-fix` (`config/role-defaults.yaml:1472-1477`) — sichtbar an den zwei fast identischen Tabellenzeilen in `.claude/rules/use-orchestrator.md:11` und `:15`. Ein Generator, der "1 Fall pro `signal_keyword`" ableitet, würde für diese zwei Keywords widersprüchliche Einzel-Wahrheiten erzeugen (`Bug fixen → bugfix` UND `Bug fixen → quick-fix`, wobei mindestens eine der beiden Erwartungen beim realen LLM-Aufruf zwangsläufig als "falsch" gewertet würde).

**Entscheidung: Kollidierende Keywords werden von der Auto-Generierung ausgeschlossen** (statt sie als Mehrfach-Akzeptanzliste zu generieren) — der PoC-Autor hat genau das bereits bewusst so gehandhabt: Statt eines literalen `Bug fixen`/`Bug beheben`-Falls testet der bestehende Katalog `quick-fix` ausschließlich über disambiguierende Kontext-Keywords (`Hotfix`, `Triage`, jeweils mit Dringlichkeits-Framing) und `bugfix` über einen expliziten "kein Dringlichkeits-Signal"-Fall (`Fehler beheben`-Framing ohne Eile). Eine Mehrfach-Akzeptanzliste (`expected: [bugfix, quick-fix]`) würde genau dieses Test-Signal verwässern, da sie keine echte Unterscheidung mehr prüft. Der Generator MUSS daher:

1. Eine Keyword→Pipelines-Map über alle gefilterten Pipelines bilden.
2. Für jedes Keyword, das nur in genau einer Pipeline vorkommt: einen Literal-Testfall generieren (`expected: [pipeline]`).
3. Für jedes Keyword, das in mehr als einer Pipeline vorkommt (aktuell nur `Bug fixen`, `Bug beheben`): **von der Auto-Generierung ausschließen** und stattdessen in einer Logzeile/Kommentar auf den manuell gepflegten Katalog verweisen, der die Disambiguierung bereits über Kontext-Keywords abdeckt.

Mit den aktuellen 6 Pipelines ergibt das 27 `signal_keyword`-Einträge insgesamt (7 feature-lifecycle + 5 quick-fix + 3 bugfix + 4 concept-development + 4 refactor + 4 docs-update), davon 25 eindeutige Keyword-Strings (`Bug fixen`/`Bug beheben` je doppelt gezählt), davon 2 kollidierend und ausgeschlossen → **23 automatisch generierbare Literal-Fälle**. Generalisierungs-, Negativ- und Disambiguierungsfälle sind ohnehin NICHT aus der YAML ableitbar (brauchen Vokabular jenseits der Keywords) — dafür bleibt ein manuell gepflegter Katalog nötig.

Vorschlag für zwei Katalog-Dateien, zur Laufzeit gemergt:

```yaml
# tests/routing-llm-eval/catalog.generated.yaml
# AUTO-GENERIERT von scripts/gen_routing_llm_eval_catalog.py — nicht von Hand editieren.
# Quelle: config/role-defaults.yaml → quality_pipelines[*].signal_keywords,
# gefiltert nach dem in Abschnitt 4.1 beschriebenen se-focus/se-Präfix-Kriterium.
cases:
  - id: kw-bugfix-01
    pipeline: bugfix
    category: keyword
    task: "Bitte Bug fixen: ..."       # aus signal_keyword literal konstruiert
    expected: [bugfix]
    source_keyword: "Bug fixen"
  # ... 1 Fall pro nicht-kollidierendem signal_keyword-Eintrag über alle
  # gefilterten Pipelines (aktuell 6, siehe Filterkriterium in 4.1).
  # Kollidierende Keywords ('Bug fixen', 'Bug beheben' — geteilt zwischen
  # bugfix/quick-fix) werden NICHT auto-generiert, siehe catalog.manual.yaml.
```

```yaml
# tests/routing-llm-eval/catalog.manual.yaml
# Handgepflegt: Generalisierung, Negativ-Fälle, Ambiguität, Keyword-Kollisionen,
# Doppel-Tabellen-Drift.
cases:
  - id: gen-bugfix-01
    pipeline: bugfix
    category: generalization
    task: "Der Sortier-Algorithmus liefert bei negativen Zahlen ein falsches Ergebnis, das muss korrigiert werden."
    expected: [bugfix]
  - id: neg-01
    pipeline: null
    category: negative
    task: "Wie ist das Wetter heute in Berlin?"
    expected: [none]
  - id: amb-01
    pipeline: null
    category: ambiguous
    task: "Es gibt einen Bug, den wir dringend fixen und deployen müssen, aber der Code drumherum sollte dabei auch gleich aufgeräumt werden."
    expected: [bugfix, quick-fix, refactor]
  # ... plus die 5 Drift-Fälle aus Abschnitt 4.3, plus die bestehenden
  # Kollisions-Disambiguierungsfälle für 'Bug fixen'/'Bug beheben'
  # (Hotfix/Triage für quick-fix, Framing-ohne-Dringlichkeit für bugfix)
```

Die bestehenden 17 Fälle aus `run_eval.sh`/`promptfooconfig.yaml` wandern 1:1 als Basis in `catalog.manual.yaml`. Exakt nachgezählt (`.experiments/promptfoo-routing-eval/promptfooconfig.yaml`): **6× keyword** (je 1 literaler Fall für `feature-lifecycle`, `docs-update`, `refactor`, `concept-development` sowie 2 für `bugfix` — der literale Fall plus der Fall mit dem für `bugfix` eindeutigen Keyword `Fehler beheben`), **5× generalization** (je 1 pro Pipeline mit literalem Fall), **2× disambiguation** (`quick-fix` über `Hotfix`/`schneller Fix` bzw. `Triage`), **3× negative**, **1× ambiguous** — Summe 6+5+2+3+1 = **17**, konsistent mit der tatsächlichen Testfall-Anzahl. Die neu vorgeschlagenen Keyword-Fälle wandern in `catalog.generated.yaml` und werden dort nicht dupliziert. `scripts/gen_routing_llm_eval_catalog.py` sollte idempotent laufen und in CI als Freshness-Check nutzbar sein (`git diff --exit-code` nach Regenerierung → erkennt, wenn jemand `signal_keywords` ändert, ohne den Katalog zu regenerieren).

### 4.2 Provider-Wrapper: Isolationsstrategien

Jeder Provider braucht eine eigene Isolationsstrategie, weil die Aktivierungs- und Einbettungspfade fundamental unterschiedlich sind:

| Provider | System-Prompt-Quelle | Isolationsstrategie | Aktivierungsrealität | Status |
|---|---|---|---|---|
| **Claude** | `.claude/rules/use-orchestrator.md` | `mktemp -d` außerhalb des Repos, `claude -p --system-prompt-file <pfad> --model haiku "<prompt>"` (bestehend, `provider.sh`) | main_chat IST der Orchestrator direkt (keine Subagent-Registrierung nötig) | **Fertig** — nur zu generalisieren (Katalog statt Hardcoded-Array) |
| **Opencode** | `.opencode/agents/orchestrator.md` | Kein `--system-prompt-file`-Äquivalent. `--agent <name>` muss auf eine Datei in `.opencode/agents/` matchen → ephemeres Verzeichnis mit nur `agents/orchestrator.md` (Kopie der realen Datei) bauen, `opencode run "<prompt>" --agent orchestrator --model <günstiges-Tier> --format json` darin ausführen, JSON-Feld parsen | Realitätsnah, aber nicht 1:1 wie Claude: Kopie simuliert die Registrierung, testet aber nicht das volle Repo-Setup (z. B. `.opencode/3-project/`-Extensions) | **Zu bauen** (Phase 2) — JSON-Output-Struktur muss vorab per Spike geklärt werden |
| **Antigravity/Gemini** | `.gemini/agents/orchestrator.md` | **Ungeklärt.** Kein lokales `agy`/`gemini`-Binary verifizierbar gewesen; laut (unsicherer, nur sekundärer) Recherche evtl. `agy -p "prompt" --agent <name> --output-format json`, Auth nur über OAuth-Cache. Ob das die Repo-Datei lädt oder nur der IDE-interne `define_subagent`-Bootstrap funktioniert, ist der zentrale offene Blocker. | **Nicht verifiziert** — Datei ist laut Kommentar im Repo explizit NICHT automatisch aktiv, sondern wird zur Laufzeit über einen `AGENTS.md`-Bootstrap-Block registriert | **Blockiert** — Verifikationsschritt VOR jeder Implementierung (Phase 3) |

Alle drei Wrapper folgen demselben Interface: `provider-<name>.sh "<prompt>"` → stdout = rohe Modellantwort (ein Wort, ggf. mit Rauschen). Der Runner normalisiert (trim + lowercase) und vergleicht exakt gegen `expected`.

### 4.3 Doppel-Tabellen-Drift als eigener Testfall-Typ

Opencode und Gemini/Antigravity enthalten in ihrer `orchestrator.md` **zwei** Tabellen: §2 „Pipeline match check" (verkürzte Signalwörter) und §3 „Intent routing" (volle kanonische Tabelle, identisch zu `signal_keywords`). Verifiziert im Repo: §2 nennt für `feature-lifecycle` nur „Feature implementieren / Feature bauen / neues Feature", §3 zusätzlich „Funktion bauen, Feature Lifecycle, komplexes Feature, Feature Pipeline". Unklar, welche Tabelle das Modell bei Konflikt tatsächlich befolgt — das ist selbst ein Drift-Risiko.

Konkreter Vorschlag für 5 gezielte Testfälle (Vokabular, das NUR in §3 steht, NICHT in §2 — bei Claude irrelevant, da dort nur eine Tabelle existiert, daher provider-spezifisch nur für Opencode/Gemini relevant):

| Pipeline | Nur-§3-Vokabular | Beispiel-Task |
|---|---|---|
| `feature-lifecycle` | „Funktion bauen" | "Wir müssen eine neue Funktion bauen, die den Export als CSV ermöglicht." |
| `quick-fix` | „Hotfix" (isoliert, ohne „Triage"/„Bug fixen") | "Wir brauchen einen Hotfix, sofort." |
| `refactor` | „Code verbessern" | "Bitte den Code in diesem Modul verbessern." |
| `docs-update` | „Doku" (isoliert, ohne „Dokumentation"/„README"/„Docs") | "Die Doku ist veraltet, bitte aktualisieren." |
| `concept-development` | „Trade-offs" (isoliert, ohne „Konzept"/„Design-Doc"/„Recherche") | "Wäge bitte die Trade-offs zwischen den beiden Ansätzen ab." |

Wenn diese Fälle bei Opencode/Gemini systematisch scheitern (Modell folgt der verkürzten §2-Tabelle), ist das ein belastbarer Befund für einen eigenen Folge-Vorschlag: die beiden Tabellen in der Template-Generierung zusammenführen. Das ist explizit **nicht** Teil dieses Konzepts (siehe Nicht-Ziele), nur die Erkennung.

### 4.4 Gemeinsames Assertion-/Grading-Format

Beibehaltung des bewährten PoC-Ansatzes: exakter, normalisierter Ein-Wort-Match (trim + lowercase) statt `icontains` — verhindert, dass ein Modell mit Fließtext-Antwort fälschlich als „bestanden" gilt. Für Ambiguitäts-Fälle: `expected` als Liste, jede der genannten Antworten zählt als Pass. `repeat=3` als Default (Flakiness-Erkennung), override via `REPEAT=1` für schnelle Smoke-Runs.

### 4.5 Verzeichnisstruktur-Vorschlag

> Bewusst **nicht** `tests/orchestration-eval/` genannt — zu ähnlich zum bestehenden `tests/orchestration/` (deterministische Engine, Abschnitt 2), Verwechslungsgefahr beim schnellen Lesen von Pfaden/CI-Logs.

```
tests/routing-llm-eval/                    # neu — bewusst anders benannt als tests/orchestration/
  catalog.generated.yaml                   # auto-generiert
  catalog.manual.yaml                      # handgepflegt
  provider-claude.sh                       # generalisiert aus .experiments/.../provider.sh
  provider-opencode.sh                     # neu (Phase 2)
  provider-antigravity.sh                  # neu, gated (Phase 3, nur falls verifiziert)
  run_eval.sh                              # generalisierter Runner, --provider Flag, liest Katalog
scripts/
  gen_routing_llm_eval_catalog.py          # neu — leitet catalog.generated.yaml aus role-defaults.yaml ab
```

Die Promotion aus `.experiments/promptfoo-routing-eval/` in diesen permanenten Ort ist Teil von Phase 1 — als Empfehlung, keine bereits getroffene Entscheidung (siehe Abschnitt 7).

## 5. Phasenplan

**Phase 1 — Katalog-Fundament + Claude-Coverage vervollständigen**

*Design-Vorbedingungen (vor Implementierung von Schritt 1 zu klären, siehe Abschnitt 4.1):*
- Pipeline-Filter festlegen/bestätigen: Generator repliziert den `se-focus`/`se-`-Präfix-Filter aus `scripts/lib/config.py:783-787` exakt, statt naiv alle `quality_pipelines`-Einträge zu lesen.
- Kollisionsregel festlegen/bestätigen: geteilte `signal_keywords` (aktuell `Bug fixen`, `Bug beheben` zwischen `bugfix`/`quick-fix`) werden von der Auto-Generierung ausgeschlossen, nicht als Mehrfach-Akzeptanzliste generiert.

1. `scripts/gen_routing_llm_eval_catalog.py` bauen: liest `quality_pipelines[*].signal_keywords`, wendet Pipeline-Filter und Kollisionsregel an, generiert `catalog.generated.yaml` (1 Fall pro nicht-kollidierendem `signal_keyword`).
2. `.experiments/promptfoo-routing-eval/` nach `tests/routing-llm-eval/` promoten, bestehende 17 Fälle in `catalog.manual.yaml` überführen (Kategorien beibehalten: 6× keyword, 5× generalization, 2× disambiguation, 3× negative, 1× ambiguous).
3. Die 5 Doppel-Tabellen-Drift-Fälle aus Abschnitt 4.3 zu `catalog.manual.yaml` hinzufügen (auch wenn bei Claude irrelevant — der Katalog ist provider-agnostisch, Wrapper/Runner entscheiden, welche Fälle je Provider laufen).
4. `run_eval.sh` generalisieren: `--provider claude` Flag, Katalog statt hartcodiertem `TASKS`-Array, Wrapper-Script-Auswahl parametrisiert.
5. Vollen Claude-Lauf durchführen, Baseline-Zahlen dokumentieren.

**Phase 2 — Opencode-Wrapper**
1. Spike: `opencode run --format json`-Output-Struktur klären (welches Feld enthält die Antwort).
2. `provider-opencode.sh` bauen (ephemeres `.opencode/agents/`-Verzeichnis, siehe 4.2).
3. Vollen Katalog gegen Opencode laufen lassen, insbesondere die 5 Drift-Fälle auswerten.
4. Bei bestätigtem Drift-Befund: separaten Findings-Eintrag/Issue vorschlagen (nicht in diesem Konzept lösen).

**Phase 3 — Antigravity (gated hinter Verifikation)**
1. **Verifikations-Spike zuerst, zeitlich begrenzt** (z. B. ≤0,5 Personentage): Existiert eine headless-CLI (`agy` o. ä.) lokal/in CI überhaupt? Lädt `--agent orchestrator` (oder Äquivalent) tatsächlich `.gemini/agents/orchestrator.md`, oder funktioniert nur der IDE-interne `define_subagent`-Bootstrap? Ergebnis wird als kurze schriftliche Verifikationsnotiz festgehalten (bestanden/nicht bestanden + Belege) — nicht angenommen.
2. **Nur falls positiv verifiziert:** `provider-antigravity.sh` analog zu Opencode bauen, vollen Katalog laufen lassen.
3. **Falls Verifikation scheitert oder CLI nicht verfügbar:** als akzeptierte Lücke dokumentieren (siehe Nicht-Ziele), keine Annäherungs-Lösung bauen, die etwas anderes testet als den echten Aktivierungspfad (würde falsches Vertrauen erzeugen).

**Phase 4 — CI-Integration (optional, nach Stabilitätsnachweis)** — siehe Abschnitt 6.

## 6. CI-Integrationsvorschlag

`.github/workflows/orchestration-test.yml` ist aktuell rein deterministisch (pytest + `sync.py --validate`), ohne LLM-Calls und ohne API-Key-Secrets. Ein LLM-Eval-Job wäre ein neuer Kostentyp — Vorschlag für einen gestuften Rollout statt „sofort bei jedem PR":

| Trigger | Umfang | Provider | `repeat` | Blockierend? |
|---|---|---|---|---|
| Jeder PR (bei Änderungen an `config/role-defaults.yaml`, `agents/**/orchestrator*`, `.claude/rules/use-orchestrator.md` etc.) | Nur `catalog.generated.yaml` (Keyword-Smoke) | Claude (günstigstes verfügbares Modell) | 1 | Nein, zunächst Report-only |
| Nightly / Cron | Voller Katalog (generiert + manuell, inkl. Drift-Fälle) | Alle verifiziert lauffähigen Provider (Claude + Opencode, ggf. Antigravity) | 3 | Nein |
| Label-getriggert (`run-routing-eval`) | Voller Katalog | Wählbar | 3 | Nein |

**Bewusste Limitation, nicht verschwiegen:** Der PR-Smoke-Job deckt ausschließlich Claude ab. Die Opencode/Gemini-spezifische Doppel-Tabellen-Drift (Abschnitt 4.3) wird dadurch **nur im Nightly-Lauf erkannt**, nicht bei jedem PR — ein PR, der z. B. §2 „Pipeline match check" in `.opencode/agents/orchestrator.md` isoliert verändert, würde vom PR-Smoke-Job nicht erfasst und erst am nächsten Nightly-Lauf auffallen. Das ist ein bewusster Kosten/Geschwindigkeits-Trade-off (Opencode-Calls sind teurer/langsamer als der Claude-Smoke-Job), keine übersehene Lücke — sollte aber bei der Owner-Entscheidung zu Abschnitt 7, Punkt 3 (API-Key-Beschaffung) mitgedacht werden, falls der Trade-off später verschoben werden soll.

Nach einer Stabilitätsphase (z. B. 2–4 Wochen Nightly-Läufe ohne spurious Flaky-Fails) kann der PR-Smoke-Job zu einem Required-Check hochgestuft werden.

**Wichtiger, ungelöster Punkt:** Das erfordert API-Keys als GitHub Secrets (Claude, Opencode-Provider, ggf. Antigravity) — im Widerspruch zur aktuellen rein-OAuth-lokalen Nutzung (kein `ANTHROPIC_API_KEY` lokal vorhanden im PoC). Diese Beschaffung/Kostenverantwortung ist eine Entscheidung außerhalb dieses Konzepts, siehe Abschnitt 7.

## 7. Offene Risiken & Entscheidungen (Projekt-Owner)

| # | Frage | Warum offen |
|---|---|---|
| 1 | **Antigravity-Aktivierungspfad** | Zentraler Blocker, nur aus Sekundärquellen recherchiert, keine Primärverifikation möglich gewesen. Muss vor Phase 3 geklärt werden. |
| 2 | **Lohnt sich Antigravity-Aufwand überhaupt**, falls sich der Blocker bestätigt (z. B. nur IDE-interner Bootstrap, keine automatisierbare CLI-Prüfung)? | Owner-Entscheidung, abhängig davon wie kritisch Antigravity als Plattform fürs Projekt ist. |
| 3 | **API-Key-Beschaffung für CI** (Secrets für Claude/Opencode/ggf. Antigravity) | Kosten- und Verantwortungsfrage, die dieses Konzept nicht selbst entscheiden kann. |
| 4 | **promptfoo-CLI bleibt nicht installierbar im Sandbox** | Bash-Runner als Dauerlösung akzeptieren, oder weiter versuchen, `promptfoo` produktiv nutzbar zu machen? |
| 5 | **Doppel-Tabellen-Architektur** (§2 vs. §3 bei Opencode/Gemini) | Falls Drift-Tests (Abschnitt 4.3) tatsächlich Fehlschläge zeigen: eigenes Konzept/Issue zum Zusammenführen der Tabellen? Nicht Teil dieses Konzepts. |
| 6 | **Trennung von `tests/orchestration/` (deterministisch) und `tests/routing-llm-eval/` (LLM, kostenpflichtig)** | Empfehlung: getrennt halten (Abschnitt 2) — sollte der Owner bestätigen, bevor der Ordnername/Aufbau final ist. |

## 8. Nächste Schritte

1. **Konkreter erster Schritt:** `scripts/gen_routing_llm_eval_catalog.py` bauen (Phase 1, Schritt 1) — die zwei Design-Vorbedingungen (Pipeline-Filter und Kollisionsregel, siehe Abschnitt 5) sind bereits in diesem Konzept festgelegt, daher unabhängig von den übrigen offenen Fragen (Abschnitt 7) sofort umsetzbar. Liefert direkten Mehrwert: automatische Erkennung, wenn `signal_keywords` sich ändert, ohne dass der Testkatalog nachzieht.
2. Katalog-Struktur (`catalog.generated.yaml`/`catalog.manual.yaml`) mit Review absichern, bevor der Opencode-Wrapper (Phase 2) angegangen wird.
3. Antigravity-Verifikations-Spike als eigenständige, zeitlich begrenzte Aufgabe VOR jeglicher Implementierung von Phase 3 einplanen — Ergebnis schriftlich festhalten, nicht annehmen.
