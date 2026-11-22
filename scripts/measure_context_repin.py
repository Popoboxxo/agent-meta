"""Dev helper: print an insert-ready re-pin block for context budgets (#1115).

Measures the same rendered projects and artifacts as the ``measured`` fixture
in ``tests/test_context_budgets.py``; no provider is called and nothing is
written to the repository. Every deviation from the pin is reported (verification
stays human); an artifact above its tolerance ceiling is flagged explicitly.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Mapping, Optional, Sequence

_REPO_ROOT = Path(__file__).resolve().parents[1]
for _entry in (str(_REPO_ROOT / "scripts"), str(_REPO_ROOT)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)


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


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Measure the rendered artifacts; print a block on deviation (exit 1)."""
    import tempfile

    import yaml  # noqa: F401  (PyYAML is the documented runtime exception)

    from lib import context_report as cr
    from lib.providers import load_provider_capabilities, load_providers_config
    from tests.test_ac01_render_identity import _make_project
    from tests.test_context_budgets import _IST_FULL, _PROVIDERS

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        mappings = cr.merge_provider_mappings(
            load_providers_config(_REPO_ROOT, {}),
            load_provider_capabilities(_REPO_ROOT),
        )
        projects = {provider: _make_project(root, provider) for provider in _PROVIDERS}
        report: dict = {}
        for provider, project in projects.items():
            report.update(cr.measure_artifacts(project, [provider], mappings))
    block = format_repin_block(report, _IST_FULL, "full")
    if block:
        print(block)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
