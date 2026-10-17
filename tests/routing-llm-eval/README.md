# routing-llm-eval — Agenten-Eval-Framework

LLM-basierte Tests für **generierte** agent-meta-Agenten in echten
Provider-Sessions. Zwei Klassen:

| Klasse | Kataloge | Grading | Zweck |
|--------|----------|---------|-------|
| Routing (B1) | `catalog.generated.yaml` + `catalog.manual.yaml` | exakter normalisierter Ein-Wort-Match auf `pipeline` | Intent-Routing-Tabelle des orchestrator |
| Behavioral (#535) | `catalog.behavior.yaml` | `contains_any` (Regex) / `contains_all` / `forbidden` | Delegation-Gates (B3), Rollen-Treue (B2), Output-Contract (B5), Interface-Wissen (B6), Prozess-Disziplin (B7) |

> **`expected_any`-Semantik:** `run_eval.sh` wertet die Liste als **Regex** aus
> (`grep -qiE`), promptfoo als **Literal-Substring** (`icontains-any`). Katalog-
> Einträge bleiben daher **einfache Literale** — ein Regex wie
> `'nicht (moeglich|erlaubt)'` ist unter promptfoo tot; Alternationen in
> separate Listen-Einträge aufteilen.

## Nutzung

```bash
REPEAT=1 ./run_eval.sh --provider claude     # schneller Smoke-Lauf
REPEAT=3 ./run_eval.sh --provider opencode   # Flakiness-Erkennung

# Strukturierter Sidecar (finding B1): JSON mit final_text,
# event_counts, tool_events, spawn_attempts neben dem Text-stdout:
EVAL_STRUCTURED_OUTPUT=/tmp/out.json ./provider-opencode.sh --agent developer "task"
```

Beide Provider-Wrapper nehmen `--agent <role>` (default: `orchestrator`)
und beenden sich mit **exit 2 bei unbekannter/fehlender Rollen-Datei**
(finding W6).

### Prompt-Quelle, Modell und Baseline (IC-13, IC-36)

- **System-Prompt:** immer die **gerenderte** Agent-Datei des aktiven Profils
  (`.claude/agents/<role>.md`, Frontmatter entfernt; Opencode: `.opencode/agents/<role>.md`).
  Für `orchestrator` ist das die gerenderte Orchestrator-Datei, nicht `.claude/rules/use-orchestrator.md`.
  Fehlt die Datei: exit 2 — zuerst `python3 scripts/sync.py` ausführen.
- **Modellklasse:** `CLAUDE_ROUTING_EVAL_MODEL` (Default `haiku`) bzw.
  `OPENCODE_ROUTING_EVAL_MODEL` (Default `opencode-go/deepseek-v4-flash`).
- **Baseline (Task 0f.3):** braucht mindestens 2 Modellklassen und mindestens 3 Läufe
  je Modell und läuft nur nach ausdrücklicher Nutzerfreigabe der Kostenschätzung (IC-36).
  Ohne Freigabe wird ein Skip-Record geschrieben.
- **Ausgabe-Contract:** `output-contract.md` wird vom Runner über
  `EVAL_OUTPUT_CONTRACT=<pfad>` gesetzt und von beiden Provider-Wrappern an den
  System-Prompt gehängt. Nur so erfüllt das Modell die promptfoo-Asserts
  (`contains-json` auf `{target[, tier_escalation]}`); ohne die Env-Variable
  bleiben die behavioralen Kataloge beim normalen Prosa-Antwortverhalten.
- **Runner:** `scripts/run_role_routing_eval.py` lädt den Korpus, schätzt die
  Kosten aus `measure_artifacts`, zeigt sie an und startet erst nach `yes`/`ja`
  (IC-36). `--estimate-only` ist immer offline. Modellklassen sind explizit
  (`--model-class NAME=PROVIDER/MODEL`, wiederholbar); eine einzelne Klasse ist
  erlaubt, wird aber im Baseline-Metadatenfeld `evidence.status` als
  `not-evidenced` ausgewiesen (AC-02 verlangt ≥ 2 Klassen).

```bash
# Kostenlose Vorschau (kein LLM-Call, kein Netz):
python3 scripts/run_role_routing_eval.py --estimate-only \
  --provider opencode \
  --model-class deepseek=opencode/opencode-go/deepseek-v4-flash \
  --date 2026-10-17

# Bezahlter Deepseek-only-Lauf (3 Läufe, nur nach Freigabe; niemals automatisch):
python3 scripts/run_role_routing_eval.py \
  --provider opencode \
  --model-class deepseek=opencode/opencode-go/deepseek-v4-flash \
  --repeat 3 --approval yes --date 2026-10-17
```

Ergebnis: `roles/baseline/<date>-<model>-<profile>.json`; eine Ablehnung schreibt
`roles/runs/<date>-qg1-<model>.json` mit `status: SKIPPED-BY-USER`, Kostenschätzung
und Begründung. Promptfoo kann denselben Contract nutzen:

```bash
EVAL_OUTPUT_CONTRACT=tests/routing-llm-eval/output-contract.md \
  npx promptfoo eval -c tests/routing-llm-eval/roles/promptfooconfig.generated.yaml
```

## Single Source of Truth

**Handgepflegt (nur diese beiden):**
- `catalog.manual.yaml` — Disambiguierungs-, Negativ- und Ambiguous-Fälle.
- `catalog.behavior.yaml` — behaviorale Asserts (Rollen-Treue, Gates, Output-Contract,
  Prozess-Disziplin B7).

**Generiert — niemals von Hand editieren:**
- `catalog.generated.yaml` ← `scripts/gen_routing_llm_eval_catalog.py`
  (aus `config/role-defaults.yaml` → `quality_pipelines[*].signal_keywords`).
- `promptfooconfig.generated.yaml` ← `scripts/gen_promptfoo_config.py`
  (aus den drei Katalogen; Header „GENERATED … do not edit by hand“).

Der Bash-Runner (`run_eval.sh` + `list_cases.py`) konsumiert die Kataloge direkt;
die promptfoo-Config ist nur ein abgeleitetes Artefakt, kein zweiter Pflegepunkt.

**Freshness-Gates (CI über `python -m pytest tests/`):**
- `promptfooconfig.generated.yaml`: `scripts/gen_promptfoo_config.py --check`
  (Test `test_generated_promptfoo_config_is_fresh_and_valid`).
- `catalog.generated.yaml`: Byte-Vergleich einer Regenerierung via `--out <tmp>`
  (Test `test_generated_routing_catalog_is_fresh`).

Provider-Kommandos enthalten bewusst **kein** `{{prompt}}` (finding W4):
promptfoo hängt den Prompt als letztes Argument an.

## Judge spec — OFFEN (finding W1)

`llm-rubric`-Asserts sind absichtlich noch nicht im Katalog. Vor der
Implementierung zu entscheiden:

- Judge-Modell (Vorschlag: billigstes Claude-Haiku; Kostenziel < $0.01 je
  Case bei repeat=1)
- Judge-Prompt-Vorlage + Temperatur 0
- Retry-/Fehlerverhalten und Parsing (JSON-Output-Schema)
- Kalibrierungs-Budget: 2–3 Iterationsschleifen gegen False-Pass/Fail
  einplanen (finding W5)

## CI-Status

Existierende Workflows: `.github/workflows/validate.yml` (push/PR/Cron:
`sync.py --validate` + Frontmatter-Lint) und `orchestration-test.yml`.
Ein dedizierter `agent-eval.yml` (Kosten-Budget, paths-filter, Secrets)
ist Phase 3 — Korrektur zur ursprünglichen Planannahme „kein workflows/
Verzeichnis" (finding W7).
