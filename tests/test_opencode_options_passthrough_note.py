"""Opencode allow-list must document the provider-request evidence gap (#1175).

Harness-side passthrough of the emitted frontmatter keys is VERIFIED (runtime
evidence docs/analysis/evidence/2026-09-30-runtime-opencode-v{1,2}.md), but the
provider-side forwarding of those keys as request options is still UNVERIFIED.
The allow-list comment records that gap and links the probe runbook. This test
pins both the note and the three keys it comments on, so the documentation
cannot silently drift and the keys are not dropped while adding the note.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.providers import load_providers_config  # noqa: E402


def _provider_section(text: str, provider: str) -> str:
    """Return one provider's YAML block, up to the next sibling provider key."""
    lines = text.splitlines(keepends=True)
    start = next(
        (
            i
            for i, line in enumerate(lines)
            if re.match(rf"^  {re.escape(provider)}:\s*$", line)
        ),
        None,
    )
    assert start is not None, f"provider section {provider!r} not found"
    end = next(
        (i for i in range(start + 1, len(lines)) if re.match(r"^  \S", lines[i])),
        len(lines),
    )
    return "".join(lines[start:end])


def test_opencode_allowlist_documents_provider_request_gap():
    text = (_ROOT / "config/ai-providers.yaml").read_text(encoding="utf-8")
    opencode = _provider_section(text, "Opencode")
    assert "#1175" in opencode
    assert "opencode-request-options-probe" in opencode


def test_opencode_allowlist_keeps_three_keys():
    fields = load_providers_config(_ROOT)["Opencode"]["agent-transform"]["allowed-fields"]
    assert {"version", "prompt_mode", "generated-from"} <= set(fields)
