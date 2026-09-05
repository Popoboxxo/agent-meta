"""Codex agent document builder (frontmatter-mechanism: codex-toml).

Codex agents are TOML files in ``.codex/agents/<name>.toml`` that the
harness auto-loads. This module renders the neutral, already-transformed
agent inputs (name/description/model/extra-fields + Markdown body) into
that native document format. It contains no provider-name references —
it is simply the implementation behind the ``codex-toml`` mechanism key
in a provider's ``agent-transform:`` block (config/ai-providers.yaml).

Document shape (deterministic):

    # agent-meta generated file — do not edit manually.
    # generated-from: 1-generic/orchestrator.md@1.0.0   (only when provided)
    # version: 1.0.0                                    (only when provided)

    name = "orchestrator"
    description = "..."
    model = "..."            (only when non-empty)
    <extra_fields, keys sorted>

    developer_instructions = \"\"\"
    <markdown body>
    \"\"\"

``developer_instructions`` (the required body field per the verified Codex
agent schema) is always emitted last. ``version``/``generated-from`` are
preserved as header comments because the Codex frontmatter has no
bookkeeping fields. Round-trip guarantee:
``tomllib.loads(build_agent_toml_document(...))`` yields a dict with
exactly the emitted fields (comments excluded by TOML semantics).
"""
from __future__ import annotations

from .toml_writer import format_key, format_string, format_value

__all__ = ["build_agent_toml_document"]

_HEADER_COMMENT = "# agent-meta generated file — do not edit manually."


def _comment_safe(value: str) -> str:
    """Flatten newlines so a provenance comment always stays one line."""
    return value.replace("\r", " ").replace("\n", " ").strip()


def build_agent_toml_document(
    name: str,
    description: str,
    model: str,
    extra_fields: dict,
    body: str,
    version: str | None = None,
    generated_from: str | None = None,
) -> str:
    """Build a complete Codex agent TOML document as a string.

    Args:
        name: Agent name (the file stem of ``.codex/agents/<name>.toml``).
        description: Agent description (scalar, escaped via toml_writer).
        model: Resolved model ID; the ``model`` field is omitted entirely
            when empty (empty resolution must not inject a literal "").
        extra_fields: Literal extra document fields from the transform spec
            (e.g. sandbox_mode); emitted after model, keys sorted.
        body: Markdown body — emitted verbatim as the multi-line
            ``developer_instructions`` string (always last).
        version: Template version, preserved as a ``# version:`` comment.
        generated_from: Provenance label, preserved as a
            ``# generated-from:`` comment.

    Returns:
        The TOML document string (ends with a single trailing newline).
    """
    lines: list[str] = [_HEADER_COMMENT]
    if generated_from:
        lines.append(f"# generated-from: {_comment_safe(generated_from)}")
    if version:
        lines.append(f"# version: {_comment_safe(version)}")
    lines.append("")

    lines.append(f"name = {format_string(name)}")
    lines.append(f"description = {format_string(description)}")
    if model:
        lines.append(f"model = {format_string(model)}")
    for key in sorted(extra_fields or {}):
        lines.append(f"{format_key(key)} = {format_value(extra_fields[key])}")

    lines.append("")
    lines.append(f"developer_instructions = {format_string(body)}")
    return "\n".join(lines) + "\n"
