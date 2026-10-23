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


def test_opencode_orchestrator_hint_names_default_agent_not_mention():
    """#1006: the Opencode entry point is the default agent, not an @-mention.

    v1 and v2 both emit the explicit primary role as ``mode: primary`` and the
    managed merge writes it as ``default_agent``, so the hint must point at the
    default agent and must not offer an ``@orchestrator`` mention as the way to
    invoke it (OQ-8 amendment A2). The wording refers to the retired mention
    only as "eine @-Erwähnung ist nicht mehr nötig", which keeps the literal
    ``@orchestrator`` out of the hint.
    """
    hint = _orchestrator_hints()["Opencode"]
    assert "Default" in hint, (
        "Opencode orchestrator_hint must name the default agent; got: %r" % (hint,)
    )
    assert "@orchestrator" not in hint, (
        "Opencode orchestrator_hint must not advertise an @orchestrator mention "
        "as the way to invoke the agent; got: %r" % (hint,)
    )
    assert "nicht mehr nötig" in hint, (
        "Opencode orchestrator_hint must retire the @-mention explicitly; "
        "got: %r" % (hint,)
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
