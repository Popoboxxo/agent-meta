"""Rule delivery channels of a provider (SPEC-CONTEXT-PROFILES-2026-10-11, IC-07/IC-09, §4.3).

Which channel a rule reaches a provider through is data, not code:
``config/provider-capabilities.yaml: rules_read_channels`` lists the channels
the provider actually reads (``embedded`` | ``native-rules-dir`` | ``skills`` |
``path-scoped``). The writers (managed block, rules, MCP/tool sections) and the
reachability checks decide on these helpers, never on a provider name and no
longer on ``has_rules`` alone (``has_rules`` only says that a rules directory
is *written*, not that it is *read*).

Fallback for provider entries without ``rules_read_channels`` (e.g. custom
providers of a consumer project): the legacy key semantics -- ``has_rules``
means a read native rules directory, a ``skills_dir`` on a provider without
native rules is its lazy skills channel.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping, Optional

CHANNEL_NATIVE = "native-rules-dir"
CHANNEL_PATH_SCOPED = "path-scoped"
CHANNEL_SKILLS = "skills"
NATIVE_RULE_CHANNELS = (CHANNEL_NATIVE, CHANNEL_PATH_SCOPED)


def _channels(caps: Mapping) -> Optional[list]:
    value = caps.get("rules_read_channels")
    return list(value) if isinstance(value, (list, tuple)) else None


def reads_native_rules(caps: Mapping) -> bool:
    """True when the provider reads its generated rules directory."""
    channels = _channels(caps)
    if channels is None:
        return bool(caps.get("has_rules"))
    return any(c in channels for c in NATIVE_RULE_CHANNELS)


def reads_rule_skills(caps: Mapping) -> bool:
    """True when rules can reach the provider as ``<skills_dir>/<rule>/SKILL.md``."""
    if not caps.get("skills_dir"):
        return False
    channels = _channels(caps)
    if channels is None:
        return not caps.get("has_rules")
    return CHANNEL_SKILLS in channels


def lazy_skill_channel(caps: Mapping) -> bool:
    """Embedding provider whose lazy (non-embedded) rules are written as skills.

    IC-33 / IC-15 Nr. 2: no native rules channel, but a skills channel.
    """
    return not reads_native_rules(caps) and reads_rule_skills(caps)


def merged_caps(provider: str, provider_config: Mapping, capabilities: Mapping) -> dict:
    """ai-providers entry of *provider* merged with its capability-matrix entry."""
    merged = dict(provider_config.get(provider) or {})
    merged.update(capabilities.get(provider) or {})
    return merged


def provider_channel_caps(
    agent_meta_root: Path, provider_config: Mapping, providers: Iterable[str],
    capabilities: Optional[Mapping] = None,
) -> dict:
    """``{provider: merged caps}`` for *providers* (capability matrix loaded once)."""
    if capabilities is None:
        from .providers import load_provider_capabilities
        capabilities = load_provider_capabilities(agent_meta_root)
    return {p: merged_caps(p, provider_config, capabilities) for p in providers}
