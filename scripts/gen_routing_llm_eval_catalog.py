#!/usr/bin/env python3
"""Generate tests/routing-llm-eval/catalog.generated.yaml from quality_pipelines.

Reads `config/role-defaults.yaml` -> `quality_pipelines[*].signal_keywords`,
replicates the se-focus/se-prefix pipeline filter from
`scripts/lib/config.py` (only pipelines that actually render a row in the
generated intent-routing table, e.g. `.claude/rules/use-orchestrator.md`),
and emits one literal keyword->pipeline test case per non-colliding
`signal_keyword`.

Collision rule: a `signal_keyword` shared by more than one pipeline (currently
"Bug fixen" / "Bug beheben" between `bugfix` and `quick-fix`) is EXCLUDED from
auto-generation -- a single literal test case can't encode "either pipeline is
correct" without diluting the disambiguation signal. Those keywords are
instead covered by hand-written disambiguation cases in
`tests/routing-llm-eval/catalog.manual.yaml`.

The script is idempotent: running it twice against an unchanged
`role-defaults.yaml` produces byte-identical output. This is intended to be
used as a CI freshness check (regenerate, then `git diff --exit-code`) so the
catalog can never silently drift from the real routing table.

See `docs/concepts/planned/orchestrator-routing-test-suite.md` (section 4.1)
for the full design rationale.

Usage:
    python scripts/gen_routing_llm_eval_catalog.py
    python scripts/gen_routing_llm_eval_catalog.py --project-config .meta-config/project.yaml
    python scripts/gen_routing_llm_eval_catalog.py --out tests/routing-llm-eval/catalog.generated.yaml
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the repo root is on the Python path so `scripts.lib` is importable
# when this script is invoked directly (mirrors scripts/se-export.py).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import yaml  # type: ignore[import]
except ImportError:
    print(
        "PyYAML is required to run this script (pip install pyyaml).",
        file=sys.stderr,
    )
    sys.exit(1)

from scripts.lib.pipelines import apply_overrides, load_quality_pipelines

DEFAULT_OUT_PATH = _REPO_ROOT / "tests" / "routing-llm-eval" / "catalog.generated.yaml"
DEFAULT_PROJECT_CONFIG = _REPO_ROOT / ".meta-config" / "project.yaml"

HEADER = """\
# AUTO-GENERIERT von scripts/gen_routing_llm_eval_catalog.py -- nicht von Hand editieren.
# Quelle: config/role-defaults.yaml -> quality_pipelines[*].signal_keywords,
# gefiltert nach dem se-focus/se-Praefix-Kriterium aus scripts/lib/config.py
# (siehe docs/concepts/planned/orchestrator-routing-test-suite.md, Abschnitt 4.1).
#
# Ein Testfall pro nicht-kollidierendem signal_keyword ueber alle gefilterten
# Pipelines. Kollidierende Keywords (aktuell "Bug fixen", "Bug beheben" --
# geteilt zwischen bugfix/quick-fix) werden NICHT auto-generiert, siehe
# catalog.manual.yaml fuer ihre disambiguierenden Testfaelle.
#
# Regenerieren: python scripts/gen_routing_llm_eval_catalog.py
"""


def load_project_config(config_path: Path) -> dict:
    """Load .meta-config/project.yaml (or equivalent), returning {} if absent."""
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def filter_effective_pipelines(agent_meta_root: Path, project_config: dict) -> dict:
    """Replicate the pipeline filter from scripts/lib/config.py:783-787.

    Steps: load raw quality_pipelines -> apply project overrides -> drop
    `se-`-prefixed pipelines unless `se-focus: true` -> drop structurally
    malformed pipelines (mirrors config.py:802-805, audit #402/#403) -> keep
    only pipelines with non-empty signal_keywords (the same set that
    actually renders a row in the generated intent-routing table).
    """
    pipelines = load_quality_pipelines(str(agent_meta_root))
    overrides = project_config.get("quality-pipelines", {})
    effective = apply_overrides(pipelines, overrides)

    se_focus = bool(project_config.get("se-focus", False))
    if not se_focus:
        effective = {
            name: pl for name, pl in effective.items() if not name.startswith("se-")
        }

    effective = {
        name: pl for name, pl in effective.items()
        if isinstance(pl.get("stages", []), list)
    }

    return {
        name: pl for name, pl in effective.items() if pl.get("signal_keywords")
    }


def build_keyword_map(pipelines: dict) -> dict[str, list[str]]:
    """Build a signal_keyword -> [pipeline names] map across all filtered pipelines."""
    keyword_map: dict[str, list[str]] = {}
    for name, pipeline in pipelines.items():
        for keyword in pipeline.get("signal_keywords", []):
            keyword_map.setdefault(keyword, []).append(name)
    return keyword_map


def generate_cases(
    pipelines: dict, keyword_map: dict[str, list[str]]
) -> tuple[list[dict], list[str]]:
    """Generate one literal test case per non-colliding signal_keyword.

    Returns (cases, skipped_notes). `skipped_notes` documents excluded
    colliding keywords for log output.
    """
    cases: list[dict] = []
    skipped_notes: list[str] = []
    per_pipeline_counter: dict[str, int] = {}

    for name, pipeline in pipelines.items():
        for keyword in pipeline.get("signal_keywords", []):
            owners = keyword_map[keyword]
            if len(owners) > 1:
                note = (
                    f"skip auto-gen for collision keyword '{keyword}' "
                    f"(shared by: {', '.join(sorted(owners))}) -- "
                    f"see tests/routing-llm-eval/catalog.manual.yaml"
                )
                if note not in skipped_notes:
                    skipped_notes.append(note)
                continue

            per_pipeline_counter[name] = per_pipeline_counter.get(name, 0) + 1
            case_id = f"kw-{name}-{per_pipeline_counter[name]:02d}"
            cases.append(
                {
                    "id": case_id,
                    "pipeline": name,
                    "category": "keyword",
                    "task": f"Bitte {keyword}: kümmere dich darum.",
                    "expected": [name],
                    "source_keyword": keyword,
                }
            )
    return cases, skipped_notes


def render_catalog(cases: list[dict]) -> str:
    """Render the final catalog.generated.yaml content (header + YAML body)."""
    body = yaml.safe_dump(
        {"cases": cases},
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=100,
    )
    return HEADER + "\n" + body


def main(argv: list[str] | None = None) -> int:
    """Regenerate tests/routing-llm-eval/catalog.generated.yaml. Returns exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--project-config",
        default=str(DEFAULT_PROJECT_CONFIG),
        help="Path to .meta-config/project.yaml (for se-focus / quality-pipelines overrides).",
    )
    parser.add_argument(
        "--out",
        default=str(DEFAULT_OUT_PATH),
        help="Output path for catalog.generated.yaml.",
    )
    args = parser.parse_args(argv)

    project_config = load_project_config(Path(args.project_config))
    pipelines = filter_effective_pipelines(_REPO_ROOT, project_config)
    keyword_map = build_keyword_map(pipelines)
    cases, skipped_notes = generate_cases(pipelines, keyword_map)

    for note in skipped_notes:
        print(f"[gen-routing-catalog] {note}", file=sys.stderr)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(render_catalog(cases), encoding="utf-8")
    print(f"[gen-routing-catalog] wrote {len(cases)} cases to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
