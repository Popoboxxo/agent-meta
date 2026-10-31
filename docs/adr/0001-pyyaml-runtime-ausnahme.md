# ADR 0001: PyYAML als dokumentierte Runtime-Ausnahme

- Status: Accepted
- Datum: 2026-10-30
- Bezug: `docs/plans/ci-test-improvement-plan.md` (G15)

## Kontext

Die Konvention lautet „keine externen Python-Dependencies außer Stdlib“. Faktisch
importieren rund 33 Dateien in `scripts/` `yaml`; `requirements.txt` führt `pyyaml`.
Doku und Code waren inkonsistent.

## Entscheidung

- PyYAML ist die **einzige** dokumentierte Runtime-Ausnahme zu „Stdlib only“.
  Ein Stdlib-YAML-Parser wird nicht gebaut (Aufwand und Fehlerrisiko über den Nutzen).
- Dev-/CI-Tools (pytest, pytest-xdist, pytest-split, ruff, pip-audit, zizmor, …)
  stehen ausschließlich in `tests/requirements.txt` bzw. in CI-Schritten, nie in
  `requirements.txt`.
- Jede weitere Runtime-Dependency erfordert einen eigenen ADR.

## Konsequenzen

- `CLAUDE.md`/`AGENTS.md` (Quelle: `.meta-config/project.yaml`, `CODE_CONVENTIONS`)
  nennen die Ausnahme explizit.
- Kein Code-Change.
