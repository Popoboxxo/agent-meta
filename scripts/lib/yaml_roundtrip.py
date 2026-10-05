"""Save-time round-trip guard: refuse to silently drop YAML comments / reorder keys.

PyYAML has no round-trip support: any :func:`yaml.dump` re-serialisation of a
hand-authored file discards every ``#`` comment, and a caller that supplies a
freshly-built mapping can also reorder mapping keys. agent-meta is stdlib-only
(``ruamel.yaml`` is not allowed), so a full comment-preserving writer is out of
scope; instead this module provides a **diff guard** that inspects the existing
on-disk text and the text about to be written and reports the loss.

Both Admin-UI write paths for ``config/ai-providers.yaml`` (issue #847) call
:func:`assert_roundtrip_preserved` before the atomic write:

* ``ConfigManager.write`` (``PUT /api/config/ai-providers``)
* ``_handle_post_ai_providers_update`` (``POST /api/ai-providers/update``)

The default is to **abort** (raise :class:`YamlRoundTripLoss`, mapped to HTTP
400) so nothing is silently destroyed. A caller that deliberately wants a lossy
write can opt in with ``allow_lossy=True``; the loss is then logged as a warning
(``warn + abort`` by default, ``warn + proceed`` on explicit opt-in).

Design constraints:
* stdlib only (no external dependency);
* provider-agnostic — no provider-name branch here;
* generic over any YAML document, not coupled to ``ai-providers.yaml``.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

import yaml

logger = logging.getLogger("agent_meta.yaml_roundtrip")

#: Body/query flag understood by the Admin-UI write handlers to explicitly
#: accept a lossy (comment/order dropping) save. Kept as a dunder so it can
#: never collide with a real config key.
ALLOW_LOSSY_KEY = "__allow_lossy__"


class YamlRoundTripLoss(ValueError):
    """A write would drop YAML comments or reorder mapping keys.

    Subclasses :class:`ValueError` so the Admin-UI dispatcher maps it to HTTP
    400 (``do_PUT`` / ``do_POST``) without any extra handling.
    """


@dataclass(frozen=True)
class RoundTripReport:
    """Comparison of the on-disk YAML text with the would-be-written text."""

    comments_before: int
    comments_after: int
    order_changed: bool
    order_before: tuple[str, ...]
    order_after: tuple[str, ...]

    @property
    def lost_comments(self) -> int:
        """Number of comment lines present before but absent after."""
        return max(0, self.comments_before - self.comments_after)

    @property
    def lossy(self) -> bool:
        """True when the write would lose comments or reorder common keys."""
        return self.lost_comments > 0 or self.order_changed

    def describe(self, context: str = "") -> str:
        prefix = f"{context}: " if context else ""
        parts = [
            (
                f"{self.lost_comments} YAML comment line(s) would be dropped "
                f"({self.comments_before} -> {self.comments_after})"
            )
        ]
        if self.order_changed:
            parts.append(
                "mapping key order would change "
                f"({list(self.order_before)} -> {list(self.order_after)})"
            )
        return prefix + "; ".join(parts)


def _count_comments(text: str) -> int:
    """Count lines carrying a YAML comment (``#`` outside quotes).

    A ``#`` only starts a comment when it is at the start of a line or preceded
    by whitespace, so fragments like ``https://x#y`` do not count. Quoted
    strings are skipped so a literal ``"# not a comment"`` value does not count
    either. The scanner is intentionally simple (per line, no cross-line state):
    it needs to be *consistent* between the old and new text, not a full YAML
    tokenizer.
    """
    count = 0
    for line in text.splitlines():
        in_single = in_double = False
        i = 0
        length = len(line)
        while i < length:
            ch = line[i]
            if ch == "'" and not in_double:
                # A doubled single quote is an escaped quote inside a scalar.
                if in_single and i + 1 < length and line[i + 1] == "'":
                    i += 2
                    continue
                in_single = not in_single
            elif ch == '"' and not in_single:
                if not (in_double and i > 0 and line[i - 1] == "\\"):
                    in_double = not in_double
            elif ch == "#" and not in_single and not in_double:
                if i == 0 or line[i - 1] in " \t":
                    count += 1
                    break
            i += 1
    return count


def _flatten_keys(node, prefix: str = "") -> list[str]:
    """Return every mapping key path of *node* in document order.

    List items are traversed but do not contribute an index path: sequence
    order is a legitimate, semantic edit (``yaml.dump`` does not reorder
    sequences), so only **mapping** key order is tracked here.
    """
    out: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            out.append(path)
            out.extend(_flatten_keys(value, path))
    elif isinstance(node, list):
        for value in node:
            out.extend(_flatten_keys(value, prefix))
    return out


def _first_seen_order(keys: list[str]) -> list[str]:
    """Deduplicate *keys* keeping only the first occurrence, order-preserving."""
    seen: set[str] = set()
    out: list[str] = []
    for key in keys:
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def _ordered_common_keys(before: list[str], after: list[str]) -> tuple[list[str], list[str]]:
    """Filter both key sequences down to the keys they share, preserving order.

    Only *relative* order of keys that exist on both sides is compared: a key
    legitimately added or removed is a semantic edit, not a serialisation
    artefact, and must not trip the order check. First-occurrence dedup keeps a
    key that appears under several list items from producing spurious diffs.
    """
    common = set(before) & set(after)
    return (
        _first_seen_order([key for key in before if key in common]),
        _first_seen_order([key for key in after if key in common]),
    )


def analyze_roundtrip(original_text: str, new_text: str) -> RoundTripReport:
    """Compare *original_text* (on disk) with *new_text* (about to be written)."""
    comments_before = _count_comments(original_text)
    comments_after = _count_comments(new_text)
    try:
        before_doc = yaml.safe_load(original_text)
        after_doc = yaml.safe_load(new_text)
    except yaml.YAMLError:  # pragma: no cover - callers pass valid YAML
        before_doc = after_doc = None
    order_before, order_after = _ordered_common_keys(
        _flatten_keys(before_doc), _flatten_keys(after_doc))
    return RoundTripReport(
        comments_before=comments_before,
        comments_after=comments_after,
        order_changed=order_before != order_after,
        order_before=tuple(order_before),
        order_after=tuple(order_after),
    )


def assert_roundtrip_preserved(
    original_text: str,
    new_text: str,
    *,
    context: str = "",
    allow_lossy: bool = False,
) -> RoundTripReport:
    """Abort unless the write preserves comments and key order.

    Args:
        original_text: The current file contents.
        new_text: The serialised contents about to replace it.
        context: Optional path/label used in the error/warning text.
        allow_lossy: When ``True``, log a warning and return instead of raising.
            This is the explicit escape hatch (``__allow_lossy__``) for callers
            that knowingly accept the loss.

    Returns:
        The :class:`RoundTripReport` (so callers can inspect/log the outcome).

    Raises:
        YamlRoundTripLoss: If the write would lose comments/order and
            *allow_lossy* is ``False``.
    """
    report = analyze_roundtrip(original_text, new_text)
    if not report.lossy:
        return report
    message = report.describe(context)
    if allow_lossy:
        logger.warning(
            "%s — proceeding because allow_lossy was explicitly requested "
            "(set %s to false to abort).", message, ALLOW_LOSSY_KEY)
        return report
    raise YamlRoundTripLoss(
        f"refusing lossy YAML save ({message}). Resend with "
        f"\"{ALLOW_LOSSY_KEY}\": true to accept comment/order loss, or edit the "
        f"file directly to keep comments."
    )
