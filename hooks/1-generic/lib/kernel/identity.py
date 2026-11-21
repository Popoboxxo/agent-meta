"""Identity resolution from the explicit ``NormEvent.identity_source``.

The old hooks inferred attribution from an empty ``agent_id`` and an
implicit sentinel. Concept D.4 requires the source to be explicit:
``harness`` (reliable payload agent_id), ``sentinel`` (self-declared role) or
``none``. A reliable harness id discards a self-declaration (guard F6-05).
"""
from __future__ import annotations

from .model import Identity, NormEvent


def resolve_identity(event: NormEvent) -> Identity:
    """Return the authoritative attribution for ``event``."""
    if event.identity_source == "harness":
        return Identity(
            source="harness", agent_id=event.agent_id or None, role=None
        )
    if event.identity_source == "sentinel":
        return Identity(
            source="sentinel", agent_id=None, role=event.declared_agent or None
        )
    return Identity(source="none", agent_id=None, role=None)
