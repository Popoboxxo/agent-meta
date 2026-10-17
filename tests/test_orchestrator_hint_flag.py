"""Orchestrator hint must use the real Claude CLI flag (IC-15 Nr. 13, F-17).

The Claude provider's ``orchestrator_hint`` documented ``claude -a orchestrator``
— there is no ``-a`` flag; the correct invocation is ``claude --agent``. The
value is pinned through the provider-config loader (``scripts/lib/providers.py``)
rather than by reading the YAML directly, so a regression is caught at the
registry level the renderers actually consume. Provider-agnostic: the generic
guard sweeps every provider's hint and never branches on a provider name.
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.providers import load_providers_config  # noqa: E402

#: The invalid short flag as previously documented (`claude -a orchestrator`).
_INVALID_SHORT_FLAG = "claude -a"
#: The correct long flag.
_VALID_LONG_FLAG = "claude --agent"


def _orchestrator_hints() -> dict:
    config = load_providers_config(_REPO_ROOT)
    return {
        provider: entry["orchestrator_hint"]
        for provider, entry in config.items()
        if isinstance(entry, dict) and entry.get("orchestrator_hint")
    }


def test_claude_orchestrator_hint_uses_long_agent_flag():
    hints = _orchestrator_hints()
    hint = hints.get("Claude", "")
    assert hint, "Claude provider must carry an orchestrator_hint"
    assert _VALID_LONG_FLAG in hint, (
        "Claude orchestrator_hint must invoke `%s orchestrator`; got: %r"
        % (_VALID_LONG_FLAG, hint)
    )


def test_no_orchestrator_hint_documents_the_invalid_short_flag():
    offenders = {
        provider: hint
        for provider, hint in _orchestrator_hints().items()
        if _INVALID_SHORT_FLAG in hint
    }
    assert not offenders, (
        "orchestrator_hint still documents the invalid `%s` short flag (use "
        "`%s`): %s" % (_INVALID_SHORT_FLAG, _VALID_LONG_FLAG, offenders)
    )
