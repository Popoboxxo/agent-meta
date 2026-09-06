"""Curation helpers for the model registry.

The curation file ``config/model-curation.yaml`` is the single source of truth
for model visibility:

* ``blacklist`` — hard exclusion, filtered during discovery, never appears in
  the generated registry.
* ``disabled`` — soft exclusion, stays in the registry but is hidden from tier
  dropdowns and pickers in the admin UI.

Both lists default to empty when the file is missing or malformed, so callers
can rely on ``load_curation()`` returning a usable dict in all environments.
"""

import os
import tempfile
from pathlib import Path
from typing import Any

from .frontmatter import _YAML_AVAILABLE
from .io import load_yaml_file

try:
    import yaml as _yaml  # only used by save_curation's YAML dump
except ImportError:  # pragma: no cover - exercised in environments without PyYAML
    _yaml = None

CURATION_FILE = os.path.join("config", "model-curation.yaml")

_DEFAULT: dict[str, list[str]] = {"blacklist": [], "disabled": []}


def _default() -> dict[str, list[str]]:
    """Return a fresh copy of the default curation document."""
    return {"blacklist": [], "disabled": []}


def _normalize(data: Any) -> dict[str, list[str]]:
    """Coerce a parsed YAML document into the canonical curation shape."""
    if not isinstance(data, dict):
        return _default()
    result = _default()
    for key in ("blacklist", "disabled"):
        value = data.get(key, [])
        if isinstance(value, list):
            result[key] = [str(item) for item in value]
    return result


def load_curation(root: str) -> dict[str, list[str]]:
    """Load ``config/model-curation.yaml`` from ``root``.

    Args:
        root: Absolute path to the project root.

    Returns:
        Curation dict with ``blacklist`` and ``disabled`` keys. Returns the
        default (both empty lists) if the file is missing, unreadable, or
        PyYAML is unavailable.

    Loads via the canonical single-file loader (Issue #479, fail-soft with
    the curation default as fallback) — identical failure semantics to the
    former hand-rolled loader.
    """
    path = os.path.join(root, CURATION_FILE)
    raw = load_yaml_file(Path(path), on_error="default", default=_default())
    return _normalize(raw)


def save_curation(root: str, data: dict[str, list[str]]) -> None:
    """Write ``data`` to ``config/model-curation.yaml`` atomically.

    The file is first written to a sibling temp file in the same directory and
    then renamed into place, so an interrupted write cannot leave a partial
    YAML document behind.

    Args:
        root: Absolute path to the project root.
        data: Curation dict; only the ``blacklist`` and ``disabled`` keys are
            persisted, both coerced to lists of strings.

    Raises:
        RuntimeError: If PyYAML is not available in the runtime.
    """
    if not _YAML_AVAILABLE:
        raise RuntimeError("PyYAML is required to write model-curation.yaml")
    payload = _normalize(data)
    path = os.path.join(root, CURATION_FILE)
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        prefix=".model-curation.", suffix=".yaml.tmp",
        dir=os.path.dirname(path),
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            _yaml.safe_dump(payload, fh, default_flow_style=False, sort_keys=False)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise
