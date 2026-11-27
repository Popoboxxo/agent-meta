"""Dev helper: print an insert-ready re-pin block for context budgets (#1115).

Measures the same rendered projects and artifacts as the budget fixtures in
``tests/test_context_budgets.py`` — ``full`` like the ``measured`` fixture,
``compact`` like the ``measured_compact`` fixture (through
``render_into_work_dir(..., profile="compact")`` + ``measure_artifacts``); no
provider is called and nothing is written to the repository. Every deviation
from the pin is reported (verification stays human); an artifact above its
tolerance ceiling is flagged explicitly.

Usage::

    python3 scripts/measure_context_repin.py                  # `full` pins
    python3 scripts/measure_context_repin.py --profile compact # `compact` pins

Exit 0 when every artifact matches its pin (second run after adopting the
block), exit 1 when a block is printed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Mapping, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _entry in (str(_REPO_ROOT / "scripts"), str(_REPO_ROOT)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

#: Budget profiles a re-pin block can be produced for.
PROFILES = ("full", "compact")


def _ceiling(ist: int) -> int:
    from tests.test_context_budgets import (
        TOLERANCE_MAX_BYTES,
        TOLERANCE_MIN_BYTES,
        TOLERANCE_RATIO,
    )

    return ist + min(
        TOLERANCE_MAX_BYTES,
        max(TOLERANCE_MIN_BYTES, int(ist * TOLERANCE_RATIO)),
    )


def format_repin_block(
    report: Mapping[str, Mapping],
    pins: Mapping[str, Mapping[str, int]],
    name: str,
) -> str:
    """Return an insert-ready re-pin block for every ``bytes != pin`` entry.

    ``report`` is ``{provider: {artifact: {"bytes": int, ...}}}`` and ``pins``
    is ``{provider: {artifact: int}}``. Returns an empty string when nothing
    deviates. Ceiling breaches are annotated but never hide a deviation.
    """
    lines: list[str] = []
    deltas: list[str] = []
    for provider in sorted(report):
        artifacts = report[provider]
        pin_provider = pins.get(provider) or {}
        entries: list[tuple[str, int]] = []
        for artifact, stat in sorted(artifacts.items()):
            if not isinstance(stat, Mapping) or "bytes" not in stat:
                continue
            value = stat["bytes"]
            pin = pin_provider.get(artifact)
            if pin is None or value == pin:
                continue
            delta = value - pin
            sign = "+" if delta > 0 else ""
            suffix = " (EXCEEDS_TOLERANCE)" if value > _ceiling(pin) else ""
            deltas.append(f"{provider}/{artifact}: {pin} -> {value} ({sign}{delta}){suffix}")
            entries.append((artifact, value))
        if entries:
            lines.append(f'    "{provider}": {{')
            for artifact, value in entries:
                lines.append(f'        "{artifact}": {value},')
            lines.append("    },")
    if not deltas:
        return ""
    return "\n".join(
        [f"# Re-pin {name} (verification is human):", *lines, "", "# Deltas:", *deltas]
    ) + "\n"


def _measure_full(root: Path) -> dict:
    """Measure the ``full`` matrix exactly like the ``measured`` budget fixture."""
    from lib import context_report as cr
    from lib.providers import load_provider_capabilities, load_providers_config
    from tests.test_ac01_render_identity import _make_project
    from tests.test_context_budgets import _PROVIDERS

    mappings = cr.merge_provider_mappings(
        load_providers_config(_REPO_ROOT, {}),
        load_provider_capabilities(_REPO_ROOT),
    )
    report: dict = {}
    for provider in _PROVIDERS:
        report.update(cr.measure_artifacts(_make_project(root, provider), [provider], mappings))
    return report


def _measure_compact(root: Path) -> dict:
    """Measure the ``compact`` matrix exactly like the ``measured_compact`` fixture.

    Reuses the budget module's own ``_matrix_config``/``_matrix_mappings``
    helpers instead of duplicating the matrix setup, so the helper cannot drift
    away from the fixture it is meant to reproduce.
    """
    from lib import context_report as cr
    from lib.tmp_paths import resolve_tmp_paths
    from tests.test_context_budgets import _PROVIDERS, _matrix_config, _matrix_mappings

    mappings = _matrix_mappings()
    report: dict = {}
    for provider in _PROVIDERS:
        config = _matrix_config(root, provider, [provider])
        work = root / (provider + "-work")
        paths = resolve_tmp_paths(root / provider, {})
        cr.render_into_work_dir(_REPO_ROOT, config, work, profile="compact", paths=paths)
        report.update(cr.measure_artifacts(work, [provider], mappings))
    return report


def _measure_report(profile: str, root: Path) -> dict:
    """Dispatch on *profile* (``full``/``compact``); sole seam the tests patch."""
    if profile == "compact":
        return _measure_compact(root)
    return _measure_full(root)


def _parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="measure_context_repin.py",
        description="Print an insert-ready context-budget re-pin block (#1115).",
    )
    parser.add_argument(
        "--profile",
        choices=PROFILES,
        default="full",
        help="budget profile to measure (default: full)",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Measure the rendered artifacts; print a block on deviation (exit 1)."""
    args = _parse_args(argv)

    import tempfile

    import yaml  # noqa: F401  (PyYAML is the documented runtime exception)

    from tests.test_context_budgets import _IST_COMPACT, _IST_FULL

    pins = _IST_COMPACT if args.profile == "compact" else _IST_FULL
    with tempfile.TemporaryDirectory() as tmp:
        report = _measure_report(args.profile, Path(tmp))
    block = format_repin_block(report, pins, args.profile)
    if block:
        print(block)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
