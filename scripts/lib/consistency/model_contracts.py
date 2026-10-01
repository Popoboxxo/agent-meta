"""Generated-model-ID consistency check (registry/catalog-driven).

Plan Task 2 (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30), AC-2 + AC-12
(consistency side).

For every provider in ``config/ai-providers.yaml`` the check reads the
generated agent artifacts and validates each emitted ``model`` value against
the provider's declared ``model-format`` template and optional
``model-catalog``:

* ``model-format`` — the literal part before ``{model}`` is the required
  prefix (e.g. ``kimi-code/{model}`` → every ID starts with ``kimi-code/``).
  A missing prefix and a **doubled** prefix (``model-format`` applied twice:
  ``kimi-code/kimi-code/*``) are both ERROR findings.
* ``model-catalog`` — when declared (non-empty), every emitted ID must be in
  the catalog; an ID outside it is fail-loud. An absent catalog disables the
  containment check (conservative; spec §2.1 / DECISION-5).

Provider-agnostic by construction: the check iterates the registry and the
catalog; no provider-name literal appears in the code.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator

from ..frontmatter import parse_frontmatter_text
from ..providers import load_providers_config
from .report import Finding, Severity

try:  # Python 3.11+
    import tomllib as _toml
except ModuleNotFoundError:  # pragma: no cover - Python 3.9/3.10 fallback
    import tomli as _toml  # type: ignore[no-redef]

CHECK = "model-contract"
_PLACEHOLDER = "{model}"
_TOML_MECHANISMS = frozenset({"codex-toml"})
_TOML_MODEL_RE = re.compile(r'^\s*model\s*=\s*"([^"]*)"', re.MULTILINE)


def _finding(path: str, message: str, suggestion: str = "") -> Finding:
    return Finding(Severity.ERROR, CHECK, path, message, suggestion)


def _iter_artifacts(directory: Path, ext: str) -> Iterator[Path]:
    if not directory.is_dir():
        return
    for path in sorted(directory.iterdir()):
        if path.is_file() and path.name.endswith(ext):
            yield path


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _format_prefix(model_format: str) -> str:
    """Literal prefix before ``{model}`` (``""`` when the template is bare)."""
    index = model_format.find(_PLACEHOLDER)
    if index == -1:
        return ""
    return model_format[:index]


def _extract_models(text: str, mechanism: str) -> list[str]:
    """Return the emitted ``model`` value(s) from a generated artifact."""
    if mechanism in _TOML_MECHANISMS:
        try:
            doc = _toml.loads(text)
        except _toml.TOMLDecodeError:  # malformed TOML is reported by the artifact check
            return []
        model = doc.get("model") if isinstance(doc, dict) else None
        return [model] if isinstance(model, str) and model else []

    data = parse_frontmatter_text(text)
    model = data.get("model") if isinstance(data, dict) else None
    return [model] if isinstance(model, str) and model else []


def check_model_contracts(agent_meta_root: Path) -> list[Finding]:
    """Validate emitted model IDs against ``model-format`` / ``model-catalog``."""
    findings: list[Finding] = []
    providers = load_providers_config(agent_meta_root)
    if not isinstance(providers, dict):
        return findings

    for cfg in providers.values():
        if not isinstance(cfg, dict):
            continue
        agents_dir = cfg.get("agents_dir")
        if not agents_dir:
            continue

        model_format = str(cfg.get("model-format", _PLACEHOLDER))
        prefix = _format_prefix(model_format)
        catalog = cfg.get("model-catalog")
        catalog_set = set(catalog) if isinstance(catalog, list) and catalog else None

        transform = cfg.get("agent-transform")
        transform = transform if isinstance(transform, dict) else {}
        mechanism = str(transform.get("frontmatter-mechanism", "provider-md"))

        ext = str(cfg.get("agent_ext", ".md"))
        for path in _iter_artifacts(agent_meta_root / str(agents_dir), ext):
            text = _read(path)
            if text is None:
                continue
            rel = _rel(path, agent_meta_root)
            for model in _extract_models(text, mechanism):
                findings += _check_model(model, rel, model_format, prefix, catalog_set)

    return findings


def _check_model(
    model: str,
    path: str,
    model_format: str,
    prefix: str,
    catalog_set: set[str] | None,
) -> list[Finding]:
    findings: list[Finding] = []

    if prefix:
        if model.startswith(prefix + prefix):
            findings.append(
                _finding(
                    path,
                    f"model '{model}' has a doubled prefix — model-format "
                    f"'{model_format}' was applied twice.",
                    "Apply model-format exactly once at emission.",
                )
            )
        elif not model.startswith(prefix):
            findings.append(
                _finding(
                    path,
                    f"model '{model}' does not match model-format "
                    f"'{model_format}' (expected prefix '{prefix}').",
                    f"Emit the model as '{prefix}{model}'.",
                )
            )

    if catalog_set is not None and model not in catalog_set:
        findings.append(
            _finding(
                path,
                f"model '{model}' is not in the configured model-catalog.",
                "Use a runtime-verified model ID, or extend model-catalog from "
                "the provider's own catalog output.",
            )
        )

    return findings
