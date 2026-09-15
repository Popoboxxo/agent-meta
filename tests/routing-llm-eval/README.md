# routing-llm-eval — Agenten-Eval-Framework

LLM-basierte Tests für **generierte** agent-meta-Agenten in echten
Provider-Sessions. Zwei Klassen:

| Klasse | Kataloge | Grading | Zweck |
|--------|----------|---------|-------|
| Routing (B1) | `catalog.generated.yaml` + `catalog.manual.yaml` | exakter normalisierter Ein-Wort-Match auf `pipeline` | Intent-Routing-Tabelle des orchestrator |
| Behavioral (#535) | `catalog.behavior.yaml` | `contains_any` (Regex) / `contains_all` / `forbidden` | Delegation-Gates (B3), Rollen-Treue (B2), Output-Contract (B5), Interface-Wissen (B6) |

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

## Single Source of Truth

**Handgepflegt (nur diese beiden):**
- `catalog.manual.yaml` — Disambiguierungs-, Negativ- und Ambiguous-Fälle.
- `catalog.behavior.yaml` — behaviorale Asserts (Rollen-Treue, Gates, Output-Contract).

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
