# Plan-Schreiben (writing-plans)

Verbindliches Vorgehen, um eine approvte Spec in einen ausführbaren,
taskweisen Plan zu übersetzen. Diese Rule greift nach dem Approval-Gate und vor
der Ausführung (`plan-ledger`). Normativ nur bei aktiviertem Spec/Plan-Workflow.

## Plan-Header (Pflicht)

```markdown
# <Topic> Implementation Plan
> Status: geplant | IN PROGRESS | complete
**Goal:** …            **Architecture:** …      **Tech Stack:** …
**Spec:** <Pfad zur Spec>       # verpflichtend
## Global Constraints
## File Structure
- Modify/Create: <Pfad> — Zweck
---
pipeline_stages:                # PFLICHT, sonst fällt der Plan in den fallback_agent
  implement: 3
---
### Task <id>: <Titel>
**Files:** Modify/Create + Test          # Ownership (Barrieren-Input)
**Interfaces:** Produces/Consumes
- [ ] Step 1: Test schreiben (fail)
- [ ] Step 2: implementieren
- [ ] Step 3: Test (pass)
- [ ] Step 4: commit
```

- Das `pipeline_stages`-Frontmatter ist **Pflicht** — ohne es fällt ein
  templatekonformer Plan zur Laufzeit in den `fallback_agent`.
- Die `Spec:`-Referenz ist Pflicht und verweist auf den Trace-Anker
  `spec-id: SPEC-<slug>` der Spec.

## File-Structure-Map

- Vor den Tasks steht eine vollständige **File-Structure-Map**.
- Jede Datei wird als `Modify` oder `Create` markiert und mit ihrem Zweck benannt.
- Die Map ist die Grundlage für Ownership und Barrieren der Ausführung.

## Bite-sized TDD-Tasks

- Jeder Task ist **bite-sized**: in einem Durchgang umsetzbar, mit klarer Grenze.
- Jeder Task folgt dem TDD-Zyklus: Test schreiben (fail) → implementieren →
  Test (pass) → commit.
- Ein Task ist erst „done“, wenn der Test tatsächlich beobachtet wurde (nicht nur
  grüne Unit-Tests angenommen).

## Files / Interfaces (Pflicht pro Task)

- **`Files:`** — jede betroffene Datei wird explizit benannt (`Modify`/`Create` +
  Test). Diese Ownership ist der Input für `check_plan_file_overlap` und die
  Barrieren-Gruppen.
- **`Interfaces:`** — `Produces` (was der Task bereitstellt) und `Consumes` (was er
  voraussetzt). Leere Interfaces sind unzulässig; Schnittstellen werden mit Datei,
  Symbol und Signatur präzisiert.
- Abhängigkeiten zwischen Tasks werden explizit gemacht, damit der Graph-Validator
  Zyklen und Overlaps im `parallel_group` erkennen kann.

## No-Placeholder

- Kein `TODO`, kein `TBD`, kein `...`, kein `<Platzhalter>`, keine leeren
  `Interfaces:`.
- Jeder Task benennt exakte Pfade, Symbole, Signaturen und Commit-Messages.

## Self-Review

- Vor der Freigabe des Plans wird der Plan gegen die Spec geprüft: Deckt jeder
  Acceptance-Criterion mindestens einen Task ab? Hat jeder Task einen Test? Ist die
  Traceability (`Spec` ↔ Task-ID ↔ Test) vollständig?
- Das Ergebnis der Self-Review wird im Plan festgehalten, nicht nur gedacht.
