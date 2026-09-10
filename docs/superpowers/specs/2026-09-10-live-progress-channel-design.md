# Live-Progress-Kanal für Orchestrator + Planungspipeline — Design-Spec

> Status: Entwurf, brainstormed mit Nutzer 2026-09-10. Noch nicht implementiert.

## Problem

Der `orchestrator` (und generell jeder langlaufende Background-Subagent-Dispatch) soll dem Main
Chat/User regelmäßig Zwischenstände zeigen — Pflicht-Status-Table seit Issue #678/#682. Das
funktioniert aber nur, wenn der Orchestrator selbst synchron im Main-Chat-Turn läuft. Sobald er
als Background-Subagent dispatcht wird (das übliche Muster), landet sein Status-Table-Output nur
in seinem eigenen Transkript — der Main Chat sieht während der Laufzeit nichts, erst das finale
Task-Result. Es gibt keinen Backkanal während der Laufzeit.

**Abgrenzung zu Issue #681:** #681 behandelt hängengebliebene oder tote Subagenten (Stall-/Hang-
Erkennung). Dieses Dokument behandelt den davon getrennten Fall eines **gesunden, aber
unsichtbaren** Laufs — der Orchestrator arbeitet korrekt und produziert Status-Updates, nur kommen
diese nirgendwo an. Keine der beiden Baustellen löst die andere.

Zusätzlich, unabhängig davon gefunden: der bestehende Progress-Datei-Mechanismus aus #678 hat
einen Provider-Bug. `CheckpointStore.save_checkpoint()` ruft nach jedem Checkpoint
`_write_progress_file()` auf, die hartcodiert nach `.claude/progress/current.md` schreibt
(Modul-Konstante `_PROGRESS_DIR = ".claude/progress"`, `scripts/lib/checkpoint.py:32`) — und zwar
per `write_atomic()`, also überschreibend, nicht anhängend (`checkpoint.py:235-239`). Das passiert
unabhängig vom aktiven Provider. Für jedes Nicht-Claude-Projekt landet die Datei an einem
Claude-spezifischen Pfad, den der jeweilige Provider gar nicht kennt.

Der Nutzer will zusätzlich, dass die "Planungspipeline" (in `config/role-defaults.yaml` definierte
Pipelines: `concept-driven-dev` aus Issue #370, `feature-lifecycle` mit Planner-Gate,
`se-cascade`/SE-Kaskade) vom selben Mechanismus profitiert. Diese Pipelines haben aktuell kein
eigenes Status-/Progress-Konzept — verifiziert: keine Status-Felder in den Stage-Definitionen
(`role-defaults.yaml:2484-2510` für `concept-driven-dev`, `role-defaults.yaml:2566-2596` für
`se-cascade`). Das dort vorkommende `se_output` ist nur eine Output-Ordnerstruktur, kein
Progress-Feld.

## Ziel

Ein Progress-Signal, das während eines laufenden Background-Dispatches (Orchestrator oder
Planungspipeline) beim Nutzer ankommt — gestaffelt nach dem, was die jeweilige Provider-Plattform
tatsächlich hergibt, statt für alle Provider künstlich denselben Mechanismus zu erzwingen. Dazu ein
Root-Cause-Fix für den bestehenden providerblinden Pfad in `checkpoint.py`.

## Nicht-Ziele (v1)

- Kein Versuch, für Tier-B-Provider (siehe unten) künstlich einen Hook nachzubauen, z.B. über
  einen Polling-Daemon — Overengineering für Provider ohne native Unterstützung.
- Keine Stall-/Hang-Erkennung — das ist Issue #681, ein separates Thema (siehe Abgrenzung oben).
- Keine Änderung der bestehenden Status-Table-Textform selbst (`snippets/orchestrator/status-table.md`)
  — nur wie/wohin sie zusätzlich zum reinen Chat-Text auch landet.

## Recherchierte Fakten — Provider-Fähigkeitsmatrix

| Provider | has_hooks | hook_protocol | Live-Signal-Fähigkeit |
|---|---|---|---|
| Claude | true | claude-code-json | Echtes Hook-System (PreToolUse/PostToolUse etc., `.claude/settings.json:12`) + bestätigtes `SendMessage(to:"main")` aus einem Background-Subagenten heraus (harness-eigene Fähigkeit dieser Session, kein agent-meta-Artefakt) |
| Gemini/Antigravity | true | antigravity-hooks-json | 10 verifizierte+gespiegelte Events (`docs/providers/gemini-cli.md:123-131`, `config/provider-capabilities.yaml:65,81`); `send_message`-Tool im Dispatch-Surface vorhanden, aber nur als Delegations-Tool dokumentiert (`docs/concepts/active/singleton-orchestrator-architecture.md:354`), nicht als bestätigter Push-zum-Parent-Kanal — offene Verifikationsfrage, siehe unten |
| Opencode | false | — | Vollständig geprüft (kompletter Provider-Doc + beide Capability-Blöcke): kein Hook-System, kein Plugin/Event-Bus/Notification/Watch-Modus dokumentiert. `native-batch`/`barrier_collect: true` bedeutet nur gesammeltes Ergebnis am Turn-Ende, kein Zwischenkanal |
| Continue | false | — | keine Doku-Datei vorhanden, `hooks: false` |
| Copilot | false | — | keine Doku-Datei vorhanden, `hooks: false` |
| Mammouth | true (nur `hooks_dir` reserviert) | kein `hook_protocol` gesetzt | technisch nicht funktional — sync.py spiegelt ohne verifizierten Protocol keine Skripte (Analogon zu #630, `config/provider-capabilities.yaml:125-148`) |
| Codex | true (`hooks_dir` gesetzt) | kein `hook_protocol` gesetzt | Contract technisch vorhanden (12 Events, stdin JSON blocking, `docs/providers/codex.md:129-141`), aber nicht gemirrort wegen Payload-Deviations + Trust-Review-Gate (`codex.md:143-153`, `config/provider-capabilities.yaml:158-180`) |
| ZCode | false (Projekt-Hooks werden vom Harness ignoriert) | — | `run_in_background`/`autoBackgroundMs` nativ vorhanden, aber kein dokumentierter Notify-/Result-Collection-Kanal dazu |
| KimiCode | false (nur User-Level-Hooks, keine Projekt-Generierung) | — | `AgentSwarm`/`run_in_background` nativ vorhanden, kein Notify-Kanal dokumentiert |

## Architektur

### 1. Gestaffeltes Modell — kein Gleichheitszwang zwischen Providern

**Tier A (Claude, Gemini) — echter Zwischen-Push:**

Ein Hook feuert bei jedem relevanten Tool-Event (mindestens `PostToolUse`/`AfterTool`) während
eines laufenden Orchestrator-Dispatches. Der Hook schreibt den Status in die providerkorrekte
Progress-Datei (siehe Abschnitt 2) und pusht zusätzlich, wo bestätigt verfügbar, direkt in den
Main Chat:

- **Claude:** `SendMessage(to:"main")` aus dem Orchestrator-Agenten heraus, nach jedem
  Batch-Mitglied/BARRIER — nicht bei jedem einzelnen Tool-Call. Frequenz an die bestehende
  Status-Table-Kadenz aus §7 der Orchestrator-Regeln (Issue #678) koppeln, nicht öfter.
- **Gemini:** gleiche Kadenz, aber der Push-Mechanismus (`send_message` an den Parent) muss vor
  Implementierung technisch verifiziert werden — siehe offene Punkte unten. Bis zur Verifikation
  gilt für Gemini nur die Datei-Seite (Abschnitt 2) als gesichert, der Chat-Push als
  Implementierungsziel, nicht als gegebene Fähigkeit.

**Tier B (alle anderen sieben Provider: Opencode, Continue, Copilot, Mammouth, Codex, ZCode,
KimiCode) — passive, aber live mitlesbare Datei:**

Kein Hook verfügbar, also kein aktiver Push möglich. Stattdessen wird die Progress-Datei
**anhängend statt überschreibend** geschrieben — jeder Status-Table-Update-Zeitpunkt hängt einen
neuen Eintrag an, statt die Datei zu überschreiben (vom Nutzer explizit bestätigt: "anhängen wäre
das okay für mich"). Dadurch ist die Datei mit `tail -f` durch den Nutzer aktiv mitlesbar, auch
ohne dass agent-meta selbst pusht. Das ist ein Verhaltenswechsel gegenüber dem heutigen Stand: der
bestehende Mechanismus in `checkpoint.py:235-239` überschreibt die Datei bei jedem Checkpoint
komplett (`write_atomic`) — dieses Überschreib-Verhalten bleibt für Tier-A-Provider unverändert
sinnvoll (dort kommt der Live-Stand primär über den Chat-Push an, die Datei ist Sekundärkanal),
wird aber für Tier-B-Provider auf Append umgestellt, weil die Datei dort der einzige Kanal ist.

Rotation/Truncation ist Teil des Designs, weil eine unbegrenzt anhängende Datei nicht tragbar ist:
die Datei wird bei Sync-Start (bzw. beim Start einer neuen Orchestrator-Session) rotiert/geleert,
während der laufenden Session wird nur angehängt. Die exakte Rotationsgrenze (Zeilen-/Byte-Limit
zusätzlich zum Session-Start-Reset) ist ein offener Implementierungspunkt, siehe unten.

### 2. Root-Cause-Fix: providerkorrekter Pfad statt hartcodiertem `.claude/progress`

Unabhängig von den Tiers braucht `_PROGRESS_DIR` in `checkpoint.py` einen providerkorrekten statt
hartcodierten Wert. Zwei Optionen standen zur Wahl:

**Option (a): neuer optionaler Config-Key `progress_dir` pro Provider in
`config/ai-providers.yaml`, mit Fallback für Provider ohne eigenes Ökosystem-Verzeichnis.**

- Vorteil: jeder Provider kann sein natives Konventions-Verzeichnis nutzen (analog zu
  `hooks_dir`), Konsistenz mit dem bestehenden Muster, dass Provider-Ökosystem-Pfade in
  `ai-providers.yaml` deklariert werden.
- Nachteil: neuer Config-Key, neuer Pfad-Typ, der für sieben von neun Providern sowieso nur auf
  einen Fallback zeigen würde (die meisten Provider haben kein eigenes "progress"-Konzept in ihrem
  Ökosystem) — Konfigurationsaufwand ohne echten Mehrwert für die Mehrheit der Provider.

**Option (b): einheitlicher provider-neutraler Ort `.meta-viz/progress/` für alle Provider (Tier A
und Tier B gleich).**

- Vorteil: `checkpoint.py` schreibt die Checkpoint-JSON bereits provider-neutral nach
  `.meta-viz/checkpoints` (Modul-Konstante `CHECKPOINT_DIR = ".meta-viz/checkpoints"`,
  `checkpoint.py:28`). Ein `.meta-viz/progress/`-Verzeichnis im selben Ökosystem ist konsistent mit
  einem bereits etablierten Pattern, statt einen neuen provider-spezifischen Pfad-Typ einzuführen.
  Kein neuer Config-Key nötig, keine Fallback-Logik für Provider ohne eigenes
  Progress-Verzeichnis-Konzept.
- Nachteil: für Provider, deren natives Ökosystem eine eigene Konvention für "aktueller Status"
  hätte (aktuell keiner bekannt), wäre der Pfad nicht das erste, wo ein Nutzer nachschaut.

**Entscheidung: Option (b).** `.meta-viz/` ist bereits die etablierte provider-neutrale
Ablage für Checkpoint-Daten in diesem Repo — dieselbe Datei-Familie (Fortschritt einer laufenden
Orchestrierung) an einen zweiten, provider-spezifischen Ort zu legen würde eine Inkonsistenz
schaffen, die Option (a) gerade vermeiden sollte. Kein Provider in der Fähigkeitsmatrix hat ein
dokumentiertes natives "Progress-Verzeichnis"-Konzept, das einen provider-eigenen Pfad
rechtfertigen würde — der Fallback aus Option (a) wäre also faktisch für alle neun Provider aktiv
und die Optionalität des Config-Keys reine Illusion. `_PROGRESS_DIR` wird entsprechend zu
`.meta-viz/progress` geändert, die Datei bleibt `current.md`, der Zielpfad ist
`.meta-viz/progress/current.md` für alle Provider gleich.

### 3. Planungspipeline-Anbindung

`concept-driven-dev`, `feature-lifecycle` und `se-cascade` bekommen **keinen separaten
Mechanismus** — sie nutzen denselben Tier-A/B-Kanal, weil ihre Stage-Übergänge (Generator/
Critic-Loops wie in `role-defaults.yaml:2495-2503` für `concept-driven-dev/review` oder
`role-defaults.yaml:2574-2597` für die L0/L1-Stufen von `se-cascade`, Concept-Review-Iterationen)
ebenfalls über orchestrator-artige Batch/BARRIER-Dispatches laufen.

Die Statustabelle bzw. Progress-Datei bekommt pro Eintrag ein zusätzliches Feld, das die aktive
Pipeline benennt, z.B. `Pipeline: se-cascade / Stage: l1-requirements`. Das ermöglicht einem
Nutzer, bei mehreren parallel laufenden Kaskaden (z.B. zwei `se-cascade`-Läufe für unterschiedliche
Subsysteme, oder ein `feature-lifecycle` neben einem `se-cascade`) zu unterscheiden, welcher
Eintrag in der (bei Tier-B anhängenden) Progress-Datei zu welcher Pipeline gehört. Das Feld wird
aus dem laufenden `stage.id` bzw. dem Pipeline-Namen aus `role-defaults.yaml` befüllt — keine neue
Datenquelle, nur ein zusätzliches Ausgabefeld beim Rendern des Progress-Eintrags.

## Betroffene Dateien/Komponenten

- `scripts/lib/checkpoint.py` — `_PROGRESS_DIR`-Konstante, `_write_progress_file()`
  (Append- statt Overwrite-Logik für Tier-B, Pfadänderung nach `.meta-viz/progress`),
  `_render_progress_markdown()` (neues Pipeline/Stage-Feld).
- `agents/1-generic/orchestrator.md` — Trigger-Punkte für den Chat-Push bei Tier-A-Providern
  (Batch-Mitglied/BARRIER-Kopplung).
- `snippets/orchestrator/status-table.md` — bleibt inhaltlich unverändert (siehe Nicht-Ziele),
  ist aber die Quelle des Inhalts, der neu auch gepusht/angehängt wird.
- Hook-Konfiguration für Claude (`.claude/settings.json`) und Gemini (Antigravity
  `hooks.json`-Contract, `docs/providers/gemini-cli.md:123-131`) — neuer/erweiterter
  `PostToolUse`/`AfterTool`-Hook, der den Progress-Schreib-/Push-Vorgang auslöst.
- `config/role-defaults.yaml` — keine strukturelle Änderung an den Pipeline-Definitionen selbst
  nötig, da die Anbindung rein über den bestehenden Stage-Dispatch-Mechanismus läuft; das
  Pipeline/Stage-Feld wird aus den vorhandenen `id`-Werten der Stages abgeleitet.

## Rollout/Migration

Bestehende Nutzer der alten `.claude/progress/current.md` dürfen nicht ohne Übergang brechen:

- Beim ersten Sync nach der Umstellung wird `.claude/progress/current.md` (falls vorhanden) nicht
  gelöscht, sondern bleibt als Altlast liegen; neue Schreibvorgänge gehen ausschließlich nach
  `.meta-viz/progress/current.md`.
- `.gitignore`-Einträge für `.claude/progress/` bleiben bestehen (kein Aufräum-Zwang), ein neuer
  Eintrag für `.meta-viz/progress/` wird ergänzt, analog zum bestehenden `.meta-viz/checkpoints/`-
  Eintrag.
- Kein automatisches Migrationsskript, das alte Einträge nach `.meta-viz/progress/` kopiert — die
  Datei ist eine reine Momentaufnahme (bei Tier A überschreibend), ein Transfer historischer
  Zwischenstände hat keinen Nutzwert.

## Risiken

- **Chat-Push-Frequenz zu hoch:** wird die Kopplung an Batch/BARRIER nicht sauber eingehalten
  (z.B. versehentlicher Push pro Tool-Call statt pro Batch), flutet der Orchestrator den Main Chat
  mit Zwischenständen — Kadenz-Test (siehe Tests-Abschnitt) soll das vor Rollout abfangen.
- **Gemini-Push erweist sich als nicht verfügbar:** wird `send_message` bei der Verifikation als
  reines Delegations-Tool ohne Parent-Push-Fähigkeit bestätigt, fällt Gemini faktisch auf
  Tier-B-Verhalten zurück (nur Datei, kein Chat-Push) — das Design toleriert das, weil Tier A und
  Tier B klar getrennt und jeweils in sich konsistent sind, aber die Einstufung "Tier A" für Gemini
  müsste dann im Dokument und in der Provider-Matrix zurückgestuft werden.
- **Unbegrenztes Wachstum der Tier-B-Datei bei sehr langen Sessions:** ohne eine zusätzlich zur
  Session-Start-Rotation greifende Größen-/Zeilen-Grenze könnte `current.md` bei extrem langen
  Läufen (viele Batches, viele Pipeline-Stages) unhandlich groß werden — muss bei der
  Implementierung der Rotationsstrategie (offener Punkt 3) mit entschieden werden.
- **Pipeline-Feld verwaist bei parallelen Läufen ohne eindeutige Session-Zuordnung:** falls zwei
  Pipelines gleichzeitig in dieselbe (Tier-B-)Datei anhängen, muss das Pipeline/Stage-Feld
  ausreichen, um Einträge klar zuzuordnen — kein zusätzlicher Session-Identifier im
  Dateinamen/-pfad vorgesehen; sollte sich das in der Praxis als unzureichend erweisen, ist ein
  Session-Suffix im Dateinamen die naheliegende Erweiterung (nicht Teil von v1).

## Offene Implementierungs-Punkte (nicht blockierend fürs Design)

1. Gemini `send_message`-Push-zum-Parent muss vor Implementierung technisch verifiziert werden —
   echter Push-Kanal zum Main Chat oder nur ein Delegations-Tool für Subagent-Dispatch? Aktuell nur
   als Delegations-Tool dokumentiert (`singleton-orchestrator-architecture.md:354`).
2. Claude `SendMessage(to:"main")`-Kadenz: nach jedem Batch-Mitglied/BARRIER koppeln, nicht öfter —
   die exakten Trigger-Punkte im Orchestrator-Template (`agents/1-generic/orchestrator.md`) müssen
   bei der Implementierung identifiziert werden (wo endet aktuell ein Batch/BARRIER-Zyklus im
   Template-Flow).
3. Rotation/Truncation-Strategie für die appendierende Tier-B-Datei ist konkret auszuarbeiten:
   Session-Start-Reset steht fest, eine zusätzliche Größen-/Zeilen-Obergrenze innerhalb einer
   Session ist noch offen.
4. Provider-neutraler vs. provider-spezifischer Pfad für die Progress-Datei — im Grunddesign oben
   bereits zugunsten von Option (b), `.meta-viz/progress/`, entschieden; offen bleibt nur die
   konkrete Umbenennung/Migration der `_PROGRESS_DIR`-Konstante und ihrer Nutzer als
   Implementierungsschritt.

## Tests

Analog zum bestehenden Testmuster für den Progress-Datei-Mechanismus (`tests/test_progress_file.py`)
und die Status-Table-Pflicht (`tests/test_status_table_block.py`,
`tests/test_status_table_orchestrator_reference.py`, `tests/test_status_table_rule_reference.py`)
sollten folgende Aspekte bei der Implementierung verifiziert werden:

- **Pfadauflösung:** Unit-Test, der `_write_progress_file()` mit unterschiedlichen aktiven
  Providern aufruft und prüft, dass die Datei ausschließlich unter `.meta-viz/progress/current.md`
  landet — nie mehr unter `.claude/progress/`, unabhängig vom Provider.
- **Append- vs. Overwrite-Verhalten:** Test, der zwei aufeinanderfolgende `save_checkpoint()`-Aufrufe
  simuliert und prüft, dass für Tier-B-Konfiguration beide Einträge in der Datei erhalten bleiben
  (Append), während für Tier-A-Konfiguration (Claude/Gemini) weiterhin nur der aktuelle Stand
  sichtbar ist (Overwrite), sofern das Overwrite-Verhalten für Tier A wie oben beschrieben erhalten
  bleibt.
- **Rotation:** Test, der einen neuen Session-Start simuliert und prüft, dass die Tier-B-Datei dabei
  geleert/rotiert wird, sowie einen Test für das Verhalten beim Erreichen der noch festzulegenden
  Größen-/Zeilen-Obergrenze (Punkt 3 der offenen Implementierungs-Punkte).
- **Kadenz des Chat-Pushs (Tier A):** Test/Szenario, das einen mehrstufigen Batch-Dispatch simuliert
  und zählt, wie oft `SendMessage(to:"main")` ausgelöst wird — muss der Anzahl der
  Batch-Mitglieder/BARRIER-Zyklen entsprechen, nicht der Anzahl einzelner Tool-Calls.
- **Pipeline/Stage-Feld:** neues Szenario in `tests/scenarios/` (Infrastruktur aus PR #705
  wiederverwenden), das einen `se-cascade`-Lauf gegen einen `concept-driven-dev`-Lauf gleichzeitig
  simuliert und prüft, dass die resultierenden Progress-Einträge korrekt nach Pipeline/Stage
  unterscheidbar sind.
- **Migration/Rollout:** Test, der eine vorhandene Alt-Datei unter `.claude/progress/current.md`
  anlegt und prüft, dass ein Sync-Lauf sie unangetastet lässt (kein Löschen, kein Überschreiben)
  und ausschließlich nach `.meta-viz/progress/current.md` schreibt.
